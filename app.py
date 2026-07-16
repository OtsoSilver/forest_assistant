"""Корень композиции приложения «Лесной помощник».

Здесь собираются все зависимости (пути → логирование → настройки →
тема → сервисы → реестр инструментов → маршрутизатор → макет) и
настраивается главное окно. Это единственное место, знающее обо всех
слоях сразу, — остальные модули связаны только через абстракции.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import flet as ft
import pystray
from PIL import Image as PilImage

from core.config import AppPaths
from core.constants import (
    APP_NAME,
    APP_VERSION,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
)
from core.context import AppContext
from core.logging_config import get_logger, setup_logging
from core.registry import ToolRegistry
from core.router import Router
from core.settings import SettingsService
from core.theme import ThemeController, ThemePreference
from ui.components.app_logo import AppLogo
from ui.dialogs.notifications import NotificationCenter
from ui.layouts.main_layout import MainLayout

logger = get_logger(__name__)


class ForestAssistantApp:
    """Собирает и запускает приложение (composition root)."""

    async def start(self, page: ft.Page) -> None:
        """Точка входа жизненного цикла приложения."""
        self._page = page
        self._tray_icon: Any | None = None

        # 1. Инфраструктура: пути и логирование — прежде всего остального.
        paths = AppPaths.default()
        setup_logging(paths.logs_dir)
        logger.info("=" * 60)
        logger.info("Запуск приложения «%s» v%s", APP_NAME, APP_VERSION)

        # 2. Настройки пользователя (автоматически восстанавливаются).
        settings = SettingsService(paths.settings_file)

        # 3. Тема оформления (светлая/тёмная/системная).
        theme = ThemeController()
        theme.attach(page, ThemePreference.from_string(settings.current.theme_mode))

        # 4. Главное окно и геометрия из настроек.
        self._configure_page(page, paths, settings)

        # 5. Сервисы и плагинная система.
        file_picker = ft.FilePicker()
        registry = ToolRegistry()
        registry.autodiscover("tools")
        router = Router(registry)
        notifications = NotificationCenter(page, theme)

        # 6. Контейнер внедрения зависимостей.
        context = AppContext(
            page=page,
            paths=paths,
            settings=settings,
            theme=theme,
            notifications=notifications,
            file_picker=file_picker,
            registry=registry,
            router=router,
        )

        # 7. Макет и стартовая страница.
        layout = MainLayout(context)
        self._shell = self._build_app_shell(page, layout, theme, notifications, paths)
        page.add(self._shell)
        page.services.append(file_picker)
        page.update()
        layout.start()
        theme.add_listener(lambda: self._refresh_shell(page, layout, theme, notifications, paths))

        logger.info("Приложение успешно инициализировано")

    # ------------------------------------------------------------------
    # Настройка страницы и окна
    # ------------------------------------------------------------------

    def _configure_page(
        self, page: ft.Page, paths: AppPaths, settings: SettingsService
    ) -> None:
        """Настраивает страницу и параметры главного окна."""
        page.title = APP_NAME
        page.padding = 0
        page.spacing = 0

        window = settings.current.window
        try:
            page.window.width = window.width
            page.window.height = window.height
            page.window.min_width = WINDOW_MIN_WIDTH
            page.window.min_height = WINDOW_MIN_HEIGHT
            if window.left is not None and window.top is not None:
                page.window.left = window.left
                page.window.top = window.top
            if paths.app_icon.exists():
                page.window.icon = str(paths.app_icon)
            page.window.maximized = window.maximized
            page.window.prevent_close = True
            page.window.title_bar_hidden = True
            page.window.title_bar_buttons_hidden = True
            page.window.frameless = True
            page.window.on_event = self._make_window_event_handler(page, settings)
        except Exception as exc:  # noqa: BLE001 — веб-режим и прочие платформы
            logger.debug("Часть параметров окна недоступна на этой платформе: %s", exc)

    def _build_app_shell(
        self,
        page: ft.Page,
        layout: MainLayout,
        theme: ThemeController,
        notifications,
        paths: AppPaths,
    ) -> ft.Control:
        """Возвращает корневой контейнер с кастомной верхней панелью окна."""
        palette = theme.palette

        def minimize_window(_event: ft.ControlEvent) -> None:
            self._minimize_to_tray(page, paths)

        def toggle_maximize(_event: ft.ControlEvent) -> None:
            try:
                page.window.maximized = not page.window.maximized
                page.update()
            except Exception as exc:  # noqa: BLE001
                logger.debug("Не удалось изменить размер окна: %s", exc)

        def close_window(_event: ft.ControlEvent) -> None:
            self._close_app(page)

        def open_notifications(_event: ft.ControlEvent) -> None:
            notifications.show_history()

        title_bar_content = ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        AppLogo(size=22, palette=palette),
                        ft.Column(
                            spacing=1,
                            tight=True,
                            controls=[
                                ft.Text(
                                    APP_NAME,
                                    size=13,
                                    weight=ft.FontWeight.W_600,
                                    color=palette.text_primary,
                                    no_wrap=True,
                                ),
                                ft.Text(
                                    APP_VERSION,
                                    size=10,
                                    color=palette.text_hint,
                                    no_wrap=True,
                                ),
                            ],
                        ),
                    ],
                ),
                ft.Container(expand=True),
                ft.Row(
                    spacing=4,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.NOTIFICATIONS_OUTLINED,
                            icon_color=palette.text_secondary,
                            icon_size=18,
                            tooltip="Все уведомления",
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=8),
                                overlay_color=palette.nav_item_hover_bg,
                            ),
                            on_click=open_notifications,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.REMOVE,
                            icon_color=palette.text_secondary,
                            icon_size=18,
                            tooltip="Свернуть в трей",
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=8),
                                overlay_color=palette.nav_item_hover_bg,
                            ),
                            on_click=minimize_window,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.SQUARE_OUTLINED,
                            icon_color=palette.text_secondary,
                            icon_size=18,
                            tooltip="Развернуть",
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=8),
                                overlay_color=palette.nav_item_hover_bg,
                            ),
                            on_click=toggle_maximize,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            icon_color=palette.text_secondary,
                            icon_size=18,
                            tooltip="Закрыть",
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=8),
                                overlay_color=palette.nav_item_hover_bg,
                            ),
                            on_click=close_window,
                        ),
                    ],
                ),
            ],
        )

        title_bar = ft.Container(
            height=48,
            padding=ft.Padding.only(left=12, right=10, top=6, bottom=6),
            bgcolor=palette.sidebar_bg,
            border=ft.Border.only(bottom=ft.BorderSide(1, palette.divider)),
            content=ft.WindowDragArea(expand=True, content=title_bar_content),
        )

        body = layout.build()
        if hasattr(body, "expand"):
            body.expand = True

        return ft.Container(
            expand=True,
            content=ft.Column(
                expand=True,
                spacing=0,
                controls=[title_bar, ft.Container(expand=True, content=body)],
            ),
        )

    def _refresh_shell(
        self,
        page: ft.Page,
        layout: MainLayout,
        theme: ThemeController,
        notifications,
        paths: AppPaths,
    ) -> None:
        """Перестраивает верхнюю панель при смене темы."""
        try:
            page.controls.clear()
            page.add(self._build_app_shell(page, layout, theme, notifications, paths))
            page.update()
        except Exception as exc:  # noqa: BLE001
            logger.debug("Не удалось перестроить верхнюю панель: %s", exc)

    def _minimize_to_tray(self, page: ft.Page, paths: AppPaths) -> None:
        """Сворачивает окно в системный трей."""
        page.run_task(self._minimize_to_tray_async, page, paths)

    async def _minimize_to_tray_async(self, page: ft.Page, paths: AppPaths) -> None:
        try:
            if self._tray_icon is None:
                self._tray_icon = self._build_tray_icon(page, paths)
            page.window.visible = False
            page.window.minimized = False
            page.update()
            self._tray_icon.run_detached()
        except Exception as exc:  # noqa: BLE001
            logger.debug("Не удалось свернуть окно в трей: %s", exc)

    def _restore_from_tray(self, page: ft.Page) -> None:
        """Возвращает окно из трея."""
        page.run_task(self._restore_from_tray_async, page)

    async def _restore_from_tray_async(self, page: ft.Page) -> None:
        try:
            page.window.visible = True
            page.window.minimized = False
            page.window.focused = True
            page.update()
            await page.window.to_front()
            await page.window.center()
            page.window.visible = True
            page.update()
        except Exception as exc:  # noqa: BLE001
            logger.debug("Не удалось восстановить окно из трея: %s", exc)

    def _close_app(self, page: ft.Page) -> None:
        """Закрывает приложение и останавливает иконку в трей, если она есть."""
        if self._tray_icon is not None:
            try:
                self._tray_icon.stop()
            except Exception as exc:  # noqa: BLE001
                logger.debug("Не удалось остановить иконку трея: %s", exc)

        async def _close() -> None:
            try:
                await page.window.destroy()
            except Exception as exc:  # noqa: BLE001
                logger.debug("Не удалось закрыть окно: %s", exc)

        page.run_task(_close)

    def _build_tray_icon(self, page: ft.Page, paths: AppPaths) -> Any:
        """Создаёт иконку системного трея с пунктом восстановления."""
        image_path = paths.app_icon if paths.app_icon.exists() else None
        if image_path is None or not image_path.exists():
            image_path = Path(__file__).resolve().parent / "assets" / "icons" / "app_icon.png"

        img = PilImage.open(image_path)
        def on_double_click(icon, item):
            self._restore_from_tray(page)

        tray_icon = pystray.Icon(
            "forest_assistant",
            img,
            APP_NAME,
            menu=pystray.Menu(
                pystray.MenuItem("Открыть", lambda icon, item: self._restore_from_tray(page)),
                pystray.MenuItem("Выход", lambda icon, item: self._close_app(page)),
            ),
        )
        tray_icon.title = APP_NAME
        tray_icon.on_double_click = on_double_click
        return tray_icon

    # ------------------------------------------------------------------
    # Отслеживание геометрии окна
    # ------------------------------------------------------------------

    def _make_window_event_handler(
        self, page: ft.Page, settings: SettingsService
    ):  # noqa: ANN202 — вложенная функция-обработчик
        """Создаёт обработчик событий окна: персистентность геометрии.

        Размер, положение и состояние окна сохраняются по завершении
        действий пользователя (RESIZED/MOVED — «конечные» события), а при
        закрытии — принудительно.
        """

        def handler(event: ft.WindowEvent) -> None:
            if event.type in (
                ft.WindowEventType.RESIZED,
                ft.WindowEventType.MOVED,
                ft.WindowEventType.MAXIMIZE,
                ft.WindowEventType.UNMAXIMIZE,
            ):
                self._save_window_geometry(page, settings)
            elif event.type is ft.WindowEventType.CLOSE:
                self._save_window_geometry(page, settings)
                settings.save()
                logger.info("Приложение завершает работу")

                async def close_window() -> None:
                    await page.window.destroy()

                page.run_task(close_window)

        return handler

    @staticmethod
    def _save_window_geometry(page: ft.Page, settings: SettingsService) -> None:
        """Считывает текущую геометрию окна и пишет её в настройки."""
        try:
            width = int(page.window.width or 0)
            height = int(page.window.height or 0)
            maximized = bool(page.window.maximized)
            left = page.window.left
            top = page.window.top
        except Exception as exc:  # noqa: BLE001
            logger.debug("Не удалось прочитать геометрию окна: %s", exc)
            return

        if width <= 0 or height <= 0:
            return

        def mutate(state) -> None:  # noqa: ANN001, ANN202 — AppSettings
            state.window.width = width
            state.window.height = height
            state.window.maximized = maximized
            if not maximized:
                state.window.left = int(left) if left is not None else None
                state.window.top = int(top) if top is not None else None

        settings.update(mutate)


async def main(page: ft.Page) -> None:
    """Асинхронная точка входа Flet-приложения."""
    await ForestAssistantApp().start(page)
