"""Базовая страница инструмента.

Задаёт единый каркас рабочей страницы: заголовок с иконкой и подзаголовком,
прокручиваемая область содержимого с ограничением ширины (современная
компоновка в духе Notion/Linear) и единые отступы. Наследники реализуют
только :meth:`BasePage.build_content`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import flet as ft

from core.context import AppContext
from models.tool_descriptor import ToolDescriptor

#: Максимальная ширина содержимого страницы — текст и формы читаются
#: лучше, когда строки не растянуты на весь экран.
MAX_CONTENT_WIDTH: int = 920


class BasePage(ABC):
    """Каркас страницы инструмента (шаблонный метод).

    Args:
        context: Контекст приложения (DI-контейнер).
        descriptor: Дескриптор инструмента, которому принадлежит страница.
    """

    def __init__(self, context: AppContext, descriptor: ToolDescriptor) -> None:
        self._context = context
        self._descriptor = descriptor

    # ------------------------------------------------------------------
    # Свойства
    # ------------------------------------------------------------------

    @property
    def context(self) -> AppContext:
        """Контекст приложения."""
        return self._context

    @property
    def descriptor(self) -> ToolDescriptor:
        """Дескриптор инструмента страницы."""
        return self._descriptor

    # ------------------------------------------------------------------
    # Построение
    # ------------------------------------------------------------------

    def build(self) -> ft.Control:
        """Собирает корневой элемент страницы с заголовком и содержимым."""
        palette = self._context.theme.palette

        content_column = ft.Column(
            spacing=20,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[self.build_content()],
        )

        return ft.Container(
            expand=True,
            padding=ft.Padding.only(left=40, top=34, right=40, bottom=30),
            content=ft.Column(
                expand=True,
                spacing=26,
                scroll=ft.ScrollMode.AUTO,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=[
                    self._build_header(palette),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            ft.Container(width=MAX_CONTENT_WIDTH, content=content_column)
                        ],
                    ),
                ],
            ),
        )

    @abstractmethod
    def build_content(self) -> ft.Control:
        """Строит содержимое страницы (реализуется наследниками)."""

    def on_mounted(self) -> None:
        """Вызывается после добавления страницы на экран (переопределяется)."""

    def dispose(self) -> None:
        """Освобождает ресурсы страницы при переключении (переопределяется)."""

    # ------------------------------------------------------------------
    # Заголовок
    # ------------------------------------------------------------------

    def _build_header(self, palette) -> ft.Control:  # noqa: ANN001 — AppPalette
        descriptor = self._descriptor
        return ft.Row(
            spacing=16,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=52,
                    height=52,
                    alignment=ft.Alignment.CENTER,
                    bgcolor=palette.accent_container,
                    border_radius=ft.BorderRadius.all(14),
                    content=ft.Icon(
                        descriptor.icon,
                        size=26,
                        color=palette.accent_container_text,
                    ),
                ),
                ft.Column(
                    spacing=3,
                    tight=True,
                    controls=[
                        ft.Text(
                            descriptor.title,
                            size=23,
                            weight=ft.FontWeight.W_700,
                            color=palette.text_primary,
                        ),
                        ft.Text(
                            descriptor.subtitle,
                            size=13,
                            color=palette.text_secondary,
                        ),
                    ],
                ),
            ],
        )
