"""Карточка-секция — базовый контейнер рабочих страниц.

Оформлена в стилистике Fluent/Material 3: большие скругления, тонкая
граница, мягкая тень, щедрые отступы и анимированная реакция на наведение.
"""

from __future__ import annotations

import flet as ft

from core.constants import ANIMATION_FAST_MS
from core.theme import AppPalette


class SectionCard(ft.Container):
    """Карточка с заголовком, иконкой и произвольным содержимым.

    Args:
        icon: Иконка секции (из ``ft.Icons``).
        title: Заголовок секции.
        subtitle: Поясняющий подзаголовок.
        content: Содержимое карточки.
        palette: Активная семантическая палитра.
        step: Необязательный номер шага сценария (1, 2, 3…).
    """

    def __init__(
        self,
        *,
        icon: str,
        title: str,
        subtitle: str,
        content: ft.Control,
        palette: AppPalette,
        step: int | None = None,
    ) -> None:
        super().__init__()
        self._palette = palette

        self._resting_shadow = ft.BoxShadow(
            blur_radius=24,
            spread_radius=-12,
            offset=ft.Offset(0, 10),
            color=palette.shadow,
        )
        self._hover_shadow = ft.BoxShadow(
            blur_radius=32,
            spread_radius=-10,
            offset=ft.Offset(0, 14),
            color=palette.shadow,
        )

        self.bgcolor = palette.card_bg
        self.border = ft.Border.all(1, palette.card_border)
        self.border_radius = ft.BorderRadius.all(18)
        self.padding = ft.Padding.all(24)
        self.shadow = self._resting_shadow
        self.animate = ft.Animation(ANIMATION_FAST_MS, ft.AnimationCurve.EASE_OUT)
        self.on_hover = self._handle_hover

        self.content = ft.Column(
            spacing=18,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                self._build_header(icon, title, subtitle, step),
                content,
            ],
        )

    # ------------------------------------------------------------------
    # Построение
    # ------------------------------------------------------------------

    def _build_header(
        self, icon: str, title: str, subtitle: str, step: int | None
    ) -> ft.Control:
        palette = self._palette

        badge_content: ft.Control
        if step is not None:
            badge_content = ft.Text(
                str(step),
                size=15,
                weight=ft.FontWeight.W_700,
                color=palette.accent_container_text,
            )
        else:
            badge_content = ft.Icon(icon, size=18, color=palette.accent_container_text)

        badge = ft.Container(
            width=36,
            height=36,
            alignment=ft.Alignment.CENTER,
            bgcolor=palette.accent_container,
            border_radius=ft.BorderRadius.all(10),
            content=badge_content,
        )

        return ft.Row(
            spacing=14,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                badge,
                ft.Column(
                    spacing=2,
                    tight=True,
                    controls=[
                        ft.Text(
                            title,
                            size=15.5,
                            weight=ft.FontWeight.W_600,
                            color=palette.text_primary,
                        ),
                        ft.Text(subtitle, size=12.5, color=palette.text_secondary),
                    ],
                ),
            ],
        )

    # ------------------------------------------------------------------
    # Состояния
    # ------------------------------------------------------------------

    def set_disabled(self, disabled: bool) -> None:
        """Переводит карточку в неактивное состояние (на время операции)."""
        self.disabled = disabled
        self.ignore_interactions = disabled
        self.opacity = 0.55 if disabled else 1.0
        self.animate_opacity = ft.Animation(ANIMATION_FAST_MS, ft.AnimationCurve.EASE_OUT)
        self.update()

    def _handle_hover(self, event: ft.HoverEvent) -> None:
        """Усиливает тень при наведении — карточка «приподнимается»."""
        hovered = str(event.data).lower() == "true"
        if self.disabled:
            return
        self.shadow = self._hover_shadow if hovered else self._resting_shadow
        self.update()
