"""Баннер состояния операции.

Отображает ход выполнения, успех, предупреждение или ошибку прямо
на странице инструмента. Появляется и исчезает с плавной анимацией.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum, auto

import flet as ft

from core.constants import ANIMATION_MEDIUM_MS
from core.theme import AppPalette


class BannerKind(Enum):
    """Вид баннера состояния."""

    PROGRESS = auto()
    SUCCESS = auto()
    ERROR = auto()
    WARNING = auto()
    INFO = auto()


class StatusBanner(ft.Container):
    """Анимированный баннер с иконкой, заголовком, текстом и действием.

    В скрытом состоянии не занимает места в макете.
    """

    def __init__(self, palette: AppPalette) -> None:
        super().__init__()
        self._palette = palette

        self._switcher = ft.AnimatedSwitcher(
            duration=ANIMATION_MEDIUM_MS,
            reverse_duration=ANIMATION_MEDIUM_MS,
            switch_in_curve=ft.AnimationCurve.EASE_OUT_CUBIC,
            switch_out_curve=ft.AnimationCurve.EASE_IN_CUBIC,
            transition=ft.AnimatedSwitcherTransition.FADE,
            content=ft.Container(height=0),
        )
        self.content = self._switcher

    # ------------------------------------------------------------------
    # Публичный API
    # ------------------------------------------------------------------

    def show(
        self,
        kind: BannerKind,
        title: str,
        message: str | None = None,
        *,
        action_label: str | None = None,
        on_action: Callable[[], None] | None = None,
    ) -> None:
        """Показывает баннер указанного вида.

        Args:
            kind: Вид баннера (прогресс, успех, ошибка и т.д.).
            title: Заголовок (жирная строка).
            message: Детальный текст (можно выделять мышью).
            action_label: Текст кнопки действия (необязательно).
            on_action: Обработчик нажатия кнопки действия.
        """
        background, foreground, border, icon = self._style_for(kind)

        leading: ft.Control
        if kind is BannerKind.PROGRESS:
            leading = ft.ProgressRing(
                width=20,
                height=20,
                stroke_width=2.5,
                color=foreground,
            )
        else:
            leading = ft.Icon(icon, size=22, color=foreground)

        texts: list[ft.Control] = [
            ft.Text(
                title,
                size=13.5,
                weight=ft.FontWeight.W_600,
                color=foreground,
            )
        ]
        if message:
            texts.append(
                ft.Text(
                    message,
                    size=12.5,
                    color=foreground,
                    selectable=True,
                )
            )

        controls: list[ft.Control] = [
            leading,
            ft.Column(spacing=3, tight=True, expand=True, controls=texts),
        ]

        if action_label and on_action is not None:
            controls.append(
                ft.TextButton(
                    content=ft.Text(action_label, size=12.5, weight=ft.FontWeight.W_600),
                    style=ft.ButtonStyle(
                        color=foreground,
                        padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                    on_click=lambda _event: on_action(),
                )
            )

        banner = ft.Container(
            bgcolor=background,
            border=ft.Border.all(1, border),
            border_radius=ft.BorderRadius.all(14),
            padding=ft.Padding.symmetric(horizontal=18, vertical=14),
            content=ft.Row(
                spacing=14,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=controls,
            ),
        )
        self._switcher.content = banner
        self.update()

    def hide(self) -> None:
        """Скрывает баннер с плавной анимацией."""
        self._switcher.content = ft.Container(height=0)
        self.update()

    # ------------------------------------------------------------------
    # Оформление
    # ------------------------------------------------------------------

    def _style_for(self, kind: BannerKind) -> tuple[str, str, str, str]:
        """Возвращает (фон, текст, граница, иконка) для вида баннера."""
        palette = self._palette
        match kind:
            case BannerKind.SUCCESS:
                return (
                    palette.success_bg,
                    palette.success_fg,
                    palette.success_border,
                    ft.Icons.CHECK_CIRCLE,
                )
            case BannerKind.ERROR:
                return (
                    palette.error_bg,
                    palette.error_fg,
                    palette.error_border,
                    ft.Icons.ERROR_OUTLINE,
                )
            case BannerKind.WARNING:
                return (
                    palette.warning_bg,
                    palette.warning_fg,
                    palette.warning_border,
                    ft.Icons.WARNING_AMBER,
                )
            case _:
                return (
                    palette.info_bg,
                    palette.info_fg,
                    palette.info_border,
                    ft.Icons.INFO_OUTLINE,
                )
