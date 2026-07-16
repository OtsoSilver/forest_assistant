"""Логотип приложения для боковой панели.

Отображает фирменный значок из ресурсов; при отсутствии файла —
градиентный значок с иконкой (устойчивый запасной вариант).
"""

from __future__ import annotations

import flet as ft

from core.theme import AppPalette


class AppLogo(ft.Container):
    """Скруглённый логотип приложения с мягкой тенью."""

    def __init__(self, size: int = 40, palette: AppPalette | None = None) -> None:
        super().__init__()
        palette = palette or AppPalette.light()

        self.width = size
        self.height = size
        self.border_radius = ft.BorderRadius.all(size * 0.28)
        self.clip_behavior = ft.ClipBehavior.ANTI_ALIAS
        self.shadow = ft.BoxShadow(
            blur_radius=size * 0.4,
            spread_radius=-size * 0.12,
            offset=ft.Offset(0, size * 0.12),
            color=palette.shadow,
        )
        self.content = ft.Image(
            src="images/logo.png",
            width=size,
            height=size,
            fit=ft.BoxFit.COVER,
            error_content=self._fallback_icon(size, palette),
        )

    @staticmethod
    def _fallback_icon(size: int, palette: AppPalette) -> ft.Control:
        """Градиентный значок на случай отсутствия файла логотипа."""
        return ft.Container(
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=[palette.accent, palette.accent_container_text],
            ),
            alignment=ft.Alignment.CENTER,
            content=ft.Icon(
                ft.Icons.FOREST,
                color=palette.on_accent,
                size=size * 0.62,
            ),
        )
