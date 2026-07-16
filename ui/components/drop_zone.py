"""Область выбора ZIP-файла (drop-зона).

Компонент реализует современный сценарий выбора файла: большая
акцентная зона с анимированными состояниями, выбор через клик,
отображение имени и размера выбранного файла.

Замечание о нативном Drag & Drop из ОС: на текущей версии Flet (0.86)
сброс файлов из Проводника Windows прямо в окно приложения не
поддерживается фреймворком. Компонент спроектирован с учётом этого:
метод :meth:`DropZone.accept_external_path` — готовая точка подключения
нативного сброса, когда он появится (обработчик уже не потребует
изменений: он общий с ручным выбором файла). Визуально зона ведёт себя
как полноценная drop-зона.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import flet as ft

from core.constants import ANIMATION_FAST_MS, ANIMATION_MEDIUM_MS
from core.theme import AppPalette
from utils.formatters import format_file_size


class DropZone(ft.Container):
    """Анимированная зона выбора файла с состояниями «пусто»/«файл выбран».

    Args:
        palette: Активная семантическая палитра.
        on_pick_requested: Вызывается при клике по зоне — открыть диалог.
        on_file_cleared: Вызывается при сбросе выбранного файла.
    """

    def __init__(
        self,
        *,
        palette: AppPalette,
        on_pick_requested: Callable[[], None],
        on_file_cleared: Callable[[], None],
    ) -> None:
        super().__init__()
        self._palette = palette
        self._on_pick_requested = on_pick_requested
        self._on_file_cleared = on_file_cleared
        self._disabled = False

        self._upload_icon = ft.Icon(
            ft.Icons.CLOUD_UPLOAD,
            size=30,
            color=palette.accent_container_text,
            animate_scale=ft.Animation(ANIMATION_FAST_MS, ft.AnimationCurve.EASE_OUT_BACK),
        )

        self._switcher = ft.AnimatedSwitcher(
            duration=ANIMATION_MEDIUM_MS,
            reverse_duration=ANIMATION_MEDIUM_MS,
            switch_in_curve=ft.AnimationCurve.EASE_OUT_CUBIC,
            switch_out_curve=ft.AnimationCurve.EASE_IN_CUBIC,
            transition=ft.AnimatedSwitcherTransition.FADE,
            content=self._build_empty_state(),
        )

        self.border_radius = ft.BorderRadius.all(16)
        self.border = ft.Border.all(1.5, palette.dropzone_border)
        self.bgcolor = palette.dropzone_bg
        self.padding = ft.Padding.symmetric(horizontal=24, vertical=26)
        self.animate = ft.Animation(ANIMATION_FAST_MS, ft.AnimationCurve.EASE_OUT)
        self.on_hover = self._handle_hover
        self.on_click = lambda _event: self._request_pick()

        # GestureDetector без on_tap: курсор-указатель над зоной,
        # само нажатие обрабатывает контейнер (on_click выше).
        self.content = ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.CLICK,
            content=self._switcher,
        )

    # ------------------------------------------------------------------
    # Публичный API
    # ------------------------------------------------------------------

    def set_file(self, path: Path, size: int | None) -> None:
        """Переводит зону в состояние «файл выбран»."""
        self._switcher.content = self._build_file_state(path, size)
        self.border = ft.Border.all(1.5, self._palette.dropzone_active_border)
        self.bgcolor = self._palette.dropzone_active_bg
        self.update()

    def clear(self) -> None:
        """Возвращает зону в исходное состояние."""
        self._switcher.content = self._build_empty_state()
        self.border = ft.Border.all(1.5, self._palette.dropzone_border)
        self.bgcolor = self._palette.dropzone_bg
        self.update()

    def set_disabled(self, disabled: bool) -> None:
        """Блокирует взаимодействие на время выполнения операции."""
        self._disabled = disabled
        self.disabled = disabled
        self.ignore_interactions = disabled
        self.opacity = 0.55 if disabled else 1.0
        self.animate_opacity = ft.Animation(ANIMATION_FAST_MS, ft.AnimationCurve.EASE_OUT)
        self.update()

    def accept_external_path(self, path: Path) -> None:
        """Точка подключения нативного Drag & Drop из ОС (будущее).

        Когда Flet получит поддержку сброса файлов из Проводника,
        обработчик события сброса должен просто вызвать этот метод —
        дальнейшая обработка идентична ручному выбору файла.
        """
        self._request_pick()

    # ------------------------------------------------------------------
    # Состояния
    # ------------------------------------------------------------------

    def _build_empty_state(self) -> ft.Control:
        palette = self._palette
        return ft.Column(
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=64,
                    height=64,
                    alignment=ft.Alignment.CENTER,
                    bgcolor=palette.accent_container,
                    shape=ft.BoxShape.CIRCLE,
                    content=self._upload_icon,
                ),
                ft.Text(
                    "Перетащите ZIP-файл сюда",
                    size=15,
                    weight=ft.FontWeight.W_600,
                    color=palette.text_primary,
                ),
                ft.Text(
                    "или выберите файл на компьютере",
                    size=12.5,
                    color=palette.text_secondary,
                ),
                ft.Container(height=2),
                ft.OutlinedButton(
                    content=ft.Text("Выбрать файл", size=13.5, weight=ft.FontWeight.W_600),
                    icon=ft.Icons.FILE_OPEN,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=10),
                        padding=ft.Padding.symmetric(horizontal=20, vertical=12),
                        side=ft.BorderSide(1.5, palette.dropzone_border),
                        color=palette.accent_container_text,
                    ),
                    on_click=lambda _event: self._request_pick(),
                ),
            ],
        )

    def _build_file_state(self, path: Path, size: int | None) -> ft.Control:
        palette = self._palette
        return ft.Row(
            spacing=14,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=48,
                    height=48,
                    alignment=ft.Alignment.CENTER,
                    bgcolor=palette.accent_container,
                    border_radius=ft.BorderRadius.all(12),
                    content=ft.Icon(
                        ft.Icons.FOLDER_ZIP,
                        size=24,
                        color=palette.accent_container_text,
                    ),
                ),
                ft.Column(
                    spacing=3,
                    tight=True,
                    expand=True,
                    controls=[
                        ft.Text(
                            path.name,
                            size=14,
                            weight=ft.FontWeight.W_600,
                            color=palette.text_primary,
                            no_wrap=True,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.Text(
                            f"{format_file_size(size)} · ZIP-архив",
                            size=12,
                            color=palette.text_secondary,
                        ),
                    ],
                ),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    icon_color=palette.text_secondary,
                    icon_size=18,
                    tooltip="Убрать файл",
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8),
                        overlay_color=palette.nav_item_hover_bg,
                    ),
                    on_click=self._handle_clear,
                ),
            ],
        )

    # ------------------------------------------------------------------
    # Обработчики
    # ------------------------------------------------------------------

    def _request_pick(self) -> None:
        if not self._disabled:
            self._on_pick_requested()

    def _handle_clear(self, _event: ft.ControlEvent) -> None:
        if not self._disabled:
            self._on_file_cleared()

    def _handle_hover(self, event: ft.HoverEvent) -> None:
        """Подсвечивает зону при наведении курсора."""
        if self._disabled:
            return
        hovered = str(event.data).lower() == "true"
        palette = self._palette
        is_empty = not isinstance(self._switcher.content, ft.Row)

        if hovered:
            self.border = ft.Border.all(1.5, palette.dropzone_active_border)
            self.bgcolor = palette.dropzone_active_bg
            self._upload_icon.scale = 1.12
        else:
            self.border = ft.Border.all(
                1.5,
                palette.dropzone_border if is_empty else palette.dropzone_active_border,
            )
            self.bgcolor = (
                palette.dropzone_bg if is_empty else palette.dropzone_active_bg
            )
            self._upload_icon.scale = 1.0
        self.update()
