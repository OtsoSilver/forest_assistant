"""Основная кнопка действия с анимированным состоянием загрузки.

В обычном состоянии — акцентная кнопка с иконкой и подписью. Во время
выполнения операции подпись плавно заменяется индикатором ProgressRing
и текстом процесса, а сама кнопка блокируется от повторного нажатия.
"""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable

import flet as ft

from core.constants import ANIMATION_FAST_MS
from core.theme import AppPalette

#: Обработчик нажатия: синхронный или асинхронный (Flet поддерживает оба).
ClickHandler = Callable[[], None | Awaitable[None]]


class LoadingButton(ft.Container):
    """Кнопка «Конвертировать» с индикатором выполнения.

    Args:
        label: Подпись кнопки в обычном состоянии.
        loading_label: Подпись во время выполнения операции.
        icon: Иконка обычного состояния.
        palette: Активная семантическая палитра.
        on_click: Обработчик нажатия (может быть ``async``).
    """

    def __init__(
        self,
        *,
        label: str,
        loading_label: str,
        icon: str,
        palette: AppPalette,
        on_click: ClickHandler,
    ) -> None:
        super().__init__()
        self._palette = palette
        self._enabled = False
        self._loading = False

        self._idle_content = self._build_idle_content(label, icon)
        self._loading_content = self._build_loading_content(loading_label)

        self._switcher = ft.AnimatedSwitcher(
            duration=ANIMATION_FAST_MS,
            reverse_duration=ANIMATION_FAST_MS,
            switch_in_curve=ft.AnimationCurve.EASE_OUT,
            switch_out_curve=ft.AnimationCurve.EASE_IN,
            transition=ft.AnimatedSwitcherTransition.FADE,
            content=self._idle_content,
        )

        self._button = ft.FilledButton(
            content=self._switcher,
            disabled=True,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=13),
                padding=ft.Padding.symmetric(horizontal=28, vertical=18),
                text_style=ft.TextStyle(size=14.5, weight=ft.FontWeight.W_600),
                elevation=0,
            ),
            on_click=self._make_click_handler(on_click),
        )
        self.content = self._button

    @staticmethod
    def _make_click_handler(on_click: ClickHandler) -> Callable[[ft.ControlEvent], Awaitable[None]]:
        """Оборачивает обработчик: поддерживает и sync, и async вызовы."""

        async def handler(_event: ft.ControlEvent) -> None:
            result = on_click()
            if inspect.isawaitable(result):
                await result

        return handler

    # ------------------------------------------------------------------
    # Построение состояний
    # ------------------------------------------------------------------

    def _build_idle_content(self, label: str, icon: str) -> ft.Control:
        return ft.Row(
            spacing=10,
            tight=True,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(icon, size=18),
                ft.Text(label, size=14.5, weight=ft.FontWeight.W_600),
            ],
        )

    def _build_loading_content(self, loading_label: str) -> ft.Control:
        return ft.Row(
            spacing=12,
            tight=True,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.ProgressRing(
                    width=17,
                    height=17,
                    stroke_width=2.4,
                    color=self._palette.on_accent,
                ),
                ft.Text(loading_label, size=14.5, weight=ft.FontWeight.W_600),
            ],
        )

    # ------------------------------------------------------------------
    # Публичный API
    # ------------------------------------------------------------------

    def set_enabled(self, enabled: bool) -> None:
        """Включает или выключает кнопку (с учётом состояния загрузки)."""
        self._enabled = enabled
        self._button.disabled = not enabled or self._loading
        self.update()

    def set_loading(self, loading: bool) -> None:
        """Переключает состояние «выполняется» с плавной анимацией."""
        self._loading = loading
        self._switcher.content = self._loading_content if loading else self._idle_content
        self._button.disabled = loading or not self._enabled
        self.update()
