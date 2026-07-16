"""Главный макет приложения: боковая панель + рабочая область.

Макет слушает маршрутизатор и контроллер темы:
  * при навигации — плавно (fade) заменяет рабочую страницу;
  * при смене темы — перестраивает себя с новой палитрой (cross-fade),
    сохраняя активный инструмент.

Макет не знает о конкретных инструментах: страницы создаются фабриками
из дескрипторов реестра (принцип открытости/закрытости).
"""

from __future__ import annotations

import flet as ft

from core.constants import ANIMATION_MEDIUM_MS, ANIMATION_SLOW_MS
from core.context import AppContext
from core.logging_config import get_logger
from core.theme import ThemePreference
from models.tool_descriptor import ToolDescriptor
from ui.pages.base_page import BasePage
from ui.sidebar import Sidebar

logger = get_logger(__name__)


class MainLayout:
    """Корневой макет приложения с навигацией и переключением тем."""

    def __init__(self, context: AppContext) -> None:
        self._context = context
        self._sidebar: Sidebar | None = None
        self._current_page: BasePage | None = None

        self._page_switcher = ft.AnimatedSwitcher(
            duration=ANIMATION_SLOW_MS,
            reverse_duration=ANIMATION_MEDIUM_MS,
            switch_in_curve=ft.AnimationCurve.EASE_OUT_CUBIC,
            switch_out_curve=ft.AnimationCurve.EASE_IN_CUBIC,
            transition=ft.AnimatedSwitcherTransition.FADE,
            content=ft.Container(expand=True),
        )
        self._theme_switcher = ft.AnimatedSwitcher(
            duration=ANIMATION_SLOW_MS,
            reverse_duration=ANIMATION_MEDIUM_MS,
            switch_in_curve=ft.AnimationCurve.EASE_OUT,
            switch_out_curve=ft.AnimationCurve.EASE_IN,
            transition=ft.AnimatedSwitcherTransition.FADE,
            content=self._compose(),
        )
        self._page_switcher.expand = True
        self._theme_switcher.expand = True

        context.router.add_listener(self._handle_navigate)
        context.theme.add_listener(self._handle_theme_changed)

    # ------------------------------------------------------------------
    # Построение
    # ------------------------------------------------------------------

    def build(self) -> ft.Control:
        """Возвращает корневой элемент макета."""
        return ft.Container(expand=True, content=self._theme_switcher)

    def start(self) -> None:
        """Открывает стартовую страницу (первый инструмент реестра)."""
        self._context.router.navigate_to_first()

    def _compose(self) -> ft.Control:
        """Собирает строку «сайдбар + рабочая область» с актуальной палитрой."""
        palette = self._context.theme.palette
        collapsed = self._context.settings.current.sidebar.collapsed

        self._sidebar = Sidebar(
            context=self._context,
            collapsed=collapsed,
            on_collapse_changed=self._persist_collapse,
            on_theme_preference=self._apply_theme_preference,
        )

        content_area = ft.Container(
            expand=True,
            bgcolor=palette.content_bg,
            content=self._page_switcher,
        )

        return ft.Row(
            expand=True,
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[self._sidebar, content_area],
        )

    # ------------------------------------------------------------------
    # Навигация
    # ------------------------------------------------------------------

    def _handle_navigate(self, descriptor: ToolDescriptor) -> None:
        """Монтирует страницу выбранного инструмента с анимацией."""
        self._mount_page(descriptor)

    def _mount_page(self, descriptor: ToolDescriptor) -> None:
        if self._current_page is not None:
            self._current_page.dispose()
            self._current_page = None

        try:
            page = descriptor.page_factory(self._context, descriptor)
        except Exception:  # noqa: BLE001 — сбой плагина не должен рушить оболочку
            logger.exception("Не удалось построить страницу инструмента '%s'", descriptor.tool_id)
            self._context.notifications.show_error(
                "Не удалось открыть инструмент",
                f"Подробности записаны в журнал (папка logs/).",
            )
            return

        self._current_page = page
        self._page_switcher.content = page.build()
        if self._sidebar is not None:
            self._sidebar.update_selection(descriptor.tool_id)
        self._page_switcher.update()
        page.on_mounted()
        logger.debug("Страница инструмента '%s' смонтирована", descriptor.tool_id)

    # ------------------------------------------------------------------
    # Смена темы
    # ------------------------------------------------------------------

    def _handle_theme_changed(self) -> None:
        """Перестраивает макет с новой палитрой, сохраняя активную страницу."""
        current = self._context.router.current_tool
        self._theme_switcher.content = self._compose()
        self._theme_switcher.update()
        if current is not None:
            self._mount_page(current)

    def _apply_theme_preference(self, preference: ThemePreference) -> None:
        """Применяет выбранный режим темы и сохраняет его в настройках."""
        self._context.settings.update(
            lambda s: setattr(s, "theme_mode", preference.value)
        )
        self._context.theme.set_preference(preference)

    # ------------------------------------------------------------------
    # Состояние боковой панели
    # ------------------------------------------------------------------

    def _persist_collapse(self, collapsed: bool) -> None:
        """Сохраняет состояние панели (свёрнута/развёрнута) в настройках."""
        self._context.settings.update(
            lambda s: setattr(s.sidebar, "collapsed", collapsed)
        )
        logger.debug("Состояние боковой панели сохранено: collapsed=%s", collapsed)
