"""Поле выбора директории с отображением полного пути.

Показывает выбранную папку (или подсказку-заполнитель) и кнопку
открытия системного диалога. Само диалог не открывает — делегирует
действие контроллеру через обратный вызов.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import flet as ft

from core.constants import ANIMATION_FAST_MS
from core.theme import AppPalette


class DirectoryField(ft.Container):
    """Строка выбора папки: иконка, путь и кнопка «Обзор…».

    Args:
        palette: Активная семантическая палитра.
        on_browse_requested: Вызывается при нажатии кнопки выбора папки.
    """

    def __init__(
        self,
        *,
        palette: AppPalette,
        on_browse_requested: Callable[[], None],
    ) -> None:
        super().__init__()
        self._palette = palette
        self._on_browse_requested = on_browse_requested

        self._path_text = ft.Text(
            "Папка не выбрана",
            size=13.5,
            color=palette.text_hint,
            no_wrap=True,
            overflow=ft.TextOverflow.ELLIPSIS,
            expand=True,
        )
        self._folder_icon = ft.Icon(
            ft.Icons.FOLDER_OUTLINED,
            size=20,
            color=palette.text_hint,
        )
        self._browse_button = ft.FilledTonalButton(
            content=ft.Text("Обзор…", size=13, weight=ft.FontWeight.W_600),
            icon=ft.Icons.FOLDER_OPEN,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.Padding.symmetric(horizontal=18, vertical=12),
            ),
            on_click=lambda _event: self._on_browse_requested(),
        )

        self.bgcolor = palette.field_fill
        self.border = ft.Border.all(1, palette.card_border)
        self.border_radius = ft.BorderRadius.all(12)
        self.padding = ft.Padding.only(left=16, top=8, right=8, bottom=8)
        self.animate = ft.Animation(ANIMATION_FAST_MS, ft.AnimationCurve.EASE_OUT)

        self.content = ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[self._folder_icon, self._path_text, self._browse_button],
        )

    # ------------------------------------------------------------------
    # Публичный API
    # ------------------------------------------------------------------

    def set_path(self, path: Path | None) -> None:
        """Отображает выбранный путь или возвращает заполнитель."""
        if path is None:
            self._path_text.value = "Папка не выбрана"
            self._path_text.color = self._palette.text_hint
            self._folder_icon.name = ft.Icons.FOLDER_OUTLINED
            self._folder_icon.color = self._palette.text_hint
        else:
            self._path_text.value = str(path)
            self._path_text.color = self._palette.text_primary
            self._folder_icon.name = ft.Icons.FOLDER_SPECIAL
            self._folder_icon.color = self._palette.accent_container_text
            self.tooltip = str(path)
        self.update()

    def set_disabled(self, disabled: bool) -> None:
        """Блокирует кнопку выбора на время выполнения операции."""
        self._browse_button.disabled = disabled
        self.opacity = 0.55 if disabled else 1.0
        self.animate_opacity = ft.Animation(ANIMATION_FAST_MS, ft.AnimationCurve.EASE_OUT)
        self.update()
