"""Боковая панель приложения (Sidebar).

Содержит логотип и название приложения, список инструментов из реестра,
переключатель темы и кнопку сворачивания. Панель строится исключительно
на основе :class:`core.registry.ToolRegistry`, поэтому новые инструменты
появляются в меню автоматически, без изменений этого кода.
"""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

from core.constants import (
    ANIMATION_MEDIUM_MS,
    APP_NAME,
    APP_VERSION,
    SIDEBAR_COLLAPSED_WIDTH,
    SIDEBAR_WIDTH,
)
from core.context import AppContext
from core.theme import AppPalette, ThemePreference
from models.tool_descriptor import ToolDescriptor
from ui.components.app_logo import AppLogo


class _NavItem(ft.Container):
    """Пункт меню инструмента с анимированным выделением и hover-эффектом."""

    def __init__(
        self,
        *,
        descriptor: ToolDescriptor,
        selected: bool,
        collapsed: bool,
        palette: AppPalette,
        on_click: Callable[[str], None],
    ) -> None:
        super().__init__()
        self._descriptor = descriptor
        self._selected = selected
        self._collapsed = collapsed
        self._palette = palette
        self._on_click = on_click

        self._icon = ft.Icon(
            descriptor.icon,
            size=21,
            color=self._icon_color(),
        )
        self._label = ft.Text(
            descriptor.menu_title,
            size=13,
            weight=ft.FontWeight.W_600 if selected else ft.FontWeight.W_500,
            color=self._text_color(),
            no_wrap=True,
            overflow=ft.TextOverflow.ELLIPSIS,
            expand=True,
            animate_opacity=ft.Animation(120, ft.AnimationCurve.EASE_OUT),
        )

        self.height = 46
        self.margin = ft.Margin.symmetric(horizontal=12, vertical=1)
        self.padding = ft.Padding.symmetric(horizontal=13)
        self.border_radius = ft.BorderRadius.all(12)
        self.bgcolor = self._background()
        self.animate = ft.Animation(ANIMATION_MEDIUM_MS, ft.AnimationCurve.EASE_OUT_CUBIC)
        self.on_hover = self._handle_hover
        self.on_click = self._handle_click
        self.tooltip = descriptor.menu_title if collapsed else None

        self.content = ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER if collapsed else ft.MainAxisAlignment.START,
            controls=[self._icon] + ([] if collapsed else [self._label]),
        )

    # ------------------------------------------------------------------
    # Состояния
    # ------------------------------------------------------------------

    def set_selected(self, selected: bool) -> None:
        """Обновляет визуальное выделение пункта меню."""
        self._selected = selected
        self.bgcolor = self._background()
        self._icon.color = self._icon_color()
        self._label.color = self._text_color()
        self._label.weight = ft.FontWeight.W_600 if selected else ft.FontWeight.W_500
        self.update()

    # ------------------------------------------------------------------
    # Оформление
    # ------------------------------------------------------------------

    def _background(self) -> str | None:
        if self._selected:
            return self._palette.nav_item_selected_bg
        return None

    def _icon_color(self) -> str:
        if self._selected:
            return self._palette.nav_item_selected_text
        return self._palette.nav_item_text

    def _text_color(self) -> str:
        if self._selected:
            return self._palette.nav_item_selected_text
        return self._palette.nav_item_text

    # ------------------------------------------------------------------
    # События
    # ------------------------------------------------------------------

    def _handle_hover(self, event: ft.HoverEvent) -> None:
        hovered = str(event.data).lower() == "true"
        if self._selected:
            self.bgcolor = self._palette.nav_item_selected_bg
        else:
            self.bgcolor = self._palette.nav_item_hover_bg if hovered else None
        self.update()

    def _handle_click(self, _event: ft.ControlEvent) -> None:
        self._on_click(self._descriptor.tool_id)


class Sidebar(ft.Container):
    """Боковая панель: логотип, навигация по инструментам, настройки вида.

    Args:
        context: Контекст приложения (реестр, маршрутизатор, тема).
        collapsed: Начальное состояние — свёрнута ли панель.
        on_collapse_changed: Обратный вызов сохранения состояния панели.
        on_theme_preference: Обратный вызов смены режима темы.
    """

    def __init__(
        self,
        *,
        context: AppContext,
        collapsed: bool,
        on_collapse_changed: Callable[[bool], None],
        on_theme_preference: Callable[[ThemePreference], None],
    ) -> None:
        super().__init__()
        self._context = context
        self._collapsed = collapsed
        self._on_collapse_changed = on_collapse_changed
        self._on_theme_preference = on_theme_preference

        palette = context.theme.palette
        self._palette = palette

        # --- Шапка: логотип и название --------------------------------
        self._title_block = ft.Column(
            spacing=1,
            tight=True,
            controls=[
                ft.Text(
                    APP_NAME,
                    size=15,
                    weight=ft.FontWeight.W_700,
                    color=palette.text_primary,
                    no_wrap=True,
                ),
                ft.Text(
                    f"версия {APP_VERSION}",
                    size=11,
                    color=palette.text_hint,
                    no_wrap=True,
                ),
            ],
        )

        header = ft.Container(
            padding=ft.Padding.only(left=22, right=18, top=22, bottom=18),
            content=ft.Row(
                spacing=13,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER if collapsed else ft.MainAxisAlignment.CENTER,
                controls=[AppLogo(size=40, palette=palette)]
                + ([] if collapsed else [self._title_block]),
            ),
        )
        if collapsed:
            header.padding = ft.Padding.only(left=0, right=0, top=22, bottom=18)
            header.alignment = ft.Alignment.CENTER

        self._header = header

        # --- Навигация -------------------------------------------------
        self._nav_column = ft.Column(
            spacing=2,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=self._build_nav_items(),
        )

        # --- Подвал: тема и сворачивание --------------------------------
        self._theme_button = self._build_theme_button()
        self._collapse_button = self._build_collapse_button()
        self._footer = self._build_footer()

        # --- Сборка -----------------------------------------------------
        self.width = SIDEBAR_COLLAPSED_WIDTH if collapsed else SIDEBAR_WIDTH
        self.bgcolor = palette.sidebar_bg
        self.border = ft.Border.only(right=ft.BorderSide(1, palette.divider))
        self.animate = ft.Animation(ANIMATION_MEDIUM_MS, ft.AnimationCurve.EASE_OUT_CUBIC)
        self.clip_behavior = ft.ClipBehavior.HARD_EDGE

        self.content = ft.Column(
            spacing=0,
            expand=True,
            controls=[
                self._header,
                ft.Divider(height=1, thickness=1, color=palette.divider),
                ft.Container(height=10),
                self._nav_column,
                self._footer,
            ],
        )

        self._context.registry.add_listener(self._rebuild_nav)

    # ------------------------------------------------------------------
    # Навигация
    # ------------------------------------------------------------------

    def _build_nav_items(self) -> list[ft.Control]:
        """Строит пункты меню по текущему составу реестра инструментов."""
        current_id = self._context.router.current_tool_id
        items: list[ft.Control] = []
        for descriptor in self._context.registry.tools:
            items.append(
                _NavItem(
                    descriptor=descriptor,
                    selected=descriptor.tool_id == current_id,
                    collapsed=self._collapsed,
                    palette=self._palette,
                    on_click=self._handle_nav_click,
                )
            )
        if not items:
            items.append(
                ft.Container(
                    padding=ft.Padding.all(20),
                    content=ft.Text(
                        "Инструменты не найдены",
                        size=12.5,
                        color=self._palette.text_hint,
                    ),
                )
            )
        return items

    def _rebuild_nav(self) -> None:
        """Перестраивает меню при изменении состава реестра."""
        self._nav_column.controls = self._build_nav_items()
        self._nav_column.update()

    def update_selection(self, tool_id: str | None) -> None:
        """Обновляет выделение активного пункта меню."""
        for control in self._nav_column.controls:
            if isinstance(control, _NavItem):
                control.set_selected(
                    tool_id is not None and control._descriptor.tool_id == tool_id
                )

    def _handle_nav_click(self, tool_id: str) -> None:
        self._context.router.navigate(tool_id)

    # ------------------------------------------------------------------
    # Сворачивание
    # ------------------------------------------------------------------

    def _build_collapse_button(self) -> ft.IconButton:
        palette = self._palette
        return ft.IconButton(
            icon=ft.Icons.MENU_OPEN if not self._collapsed else ft.Icons.MENU,
            icon_color=palette.text_secondary,
            icon_size=20,
            tooltip="Свернуть панель" if not self._collapsed else "Развернуть панель",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                overlay_color=palette.nav_item_hover_bg,
            ),
            on_click=self._handle_collapse_toggle,
        )

    def _handle_collapse_toggle(self, _event: ft.ControlEvent) -> None:
        self.set_collapsed(not self._collapsed)
        self._on_collapse_changed(self._collapsed)

    def set_collapsed(self, collapsed: bool) -> None:
        """Переключает режим панели с плавной анимацией ширины."""
        self._collapsed = collapsed
        self.width = SIDEBAR_COLLAPSED_WIDTH if collapsed else SIDEBAR_WIDTH
        self._collapse_button.icon = ft.Icons.MENU if collapsed else ft.Icons.MENU_OPEN
        self._collapse_button.tooltip = "Развернуть панель" if collapsed else "Свернуть панель"
        # Пункты меню и шапка перестраиваются под новый режим.
        self._nav_column.controls = self._build_nav_items()
        self._rebuild_header(collapsed)
        self._rebuild_footer(collapsed)
        self.update()

    def _rebuild_header(self, collapsed: bool) -> None:
        controls = [AppLogo(size=40, palette=self._palette)]
        if not collapsed:
            controls.append(self._title_block)
        self._header.content = ft.Row(
            spacing=13,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER if collapsed else ft.MainAxisAlignment.START,
            controls=controls,
        )
        self._header.padding = (
            ft.Padding.only(left=0, right=0, top=22, bottom=18)
            if collapsed
            else ft.Padding.only(left=22, right=18, top=22, bottom=18)
        )

    # ------------------------------------------------------------------
    # Тема оформления
    # ------------------------------------------------------------------

    def _build_theme_button(self) -> ft.PopupMenuButton:
        palette = self._palette
        preference = self._context.theme.preference

        def theme_item(p: ThemePreference) -> ft.PopupMenuItem:
            return ft.PopupMenuItem(
                content=ft.Text(p.title, size=13),
                icon=self._icon_for_preference(p),
                checked=preference is p,
                on_click=lambda _event, pref=p: self._handle_theme_select(pref),
            )

        return ft.PopupMenuButton(
            icon=self._icon_for_preference(preference),
            icon_color=palette.text_secondary,
            icon_size=20,
            tooltip="Тема оформления",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                overlay_color=palette.nav_item_hover_bg,
            ),
            items=[theme_item(p) for p in ThemePreference],
        )

    def _handle_theme_select(self, preference: ThemePreference) -> None:
        self._theme_button.icon = self._icon_for_preference(preference)
        self._on_theme_preference(preference)

    @staticmethod
    def _icon_for_preference(preference: ThemePreference) -> str:
        return {
            ThemePreference.SYSTEM: ft.Icons.CONTRAST,
            ThemePreference.LIGHT: ft.Icons.LIGHT_MODE,
            ThemePreference.DARK: ft.Icons.DARK_MODE,
        }[preference]

    # ------------------------------------------------------------------
    # Подвал
    # ------------------------------------------------------------------

    def _build_footer(self) -> ft.Container:
        palette = self._palette
        return ft.Container(
            padding=ft.Padding.only(left=12, right=12, top=8, bottom=14),
            content=ft.Column(
                spacing=4,
                controls=[
                    ft.Divider(height=1, thickness=1, color=palette.divider),
                    ft.Container(height=4),
                    self._footer_buttons(),
                ],
            ),
        )

    def _footer_buttons(self) -> ft.Control:
        if self._collapsed:
            return ft.Column(
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[self._theme_button, self._collapse_button],
            )
        return ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[self._theme_button, self._collapse_button],
        )

    def _rebuild_footer(self, collapsed: bool) -> None:
        column = self._footer.content
        if isinstance(column, ft.Column):
            column.controls = [
                ft.Divider(height=1, thickness=1, color=self._palette.divider),
                ft.Container(height=4),
                self._footer_buttons(),
            ]
