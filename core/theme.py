"""Система тем оформления приложения.

Включает:
  * :class:`AppPalette` — семантическая палитра пользовательских цветов
    для компонентов, которых не касается Material ColorScheme;
  * фабрики светлой и тёмной тем Material 3 (Fluent-стилистика Windows 11);
  * :class:`ThemeController` — управление режимом темы (светлая/тёмная/
    системная), персистентность и уведомление подписчиков о смене темы.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

import flet as ft

from core.logging_config import get_logger

logger = get_logger(__name__)

#: Основной шрифт интерфейса (системный шрифт Windows 11 — Fluent Design).
FONT_FAMILY: str = "Segoe UI"


class ThemePreference(Enum):
    """Пользовательский выбор режима темы."""

    SYSTEM = "system"
    LIGHT = "light"
    DARK = "dark"

    @classmethod
    def from_string(cls, value: str) -> "ThemePreference":
        """Восстанавливает предпочтение из строки настроек."""
        return {
            "light": cls.LIGHT,
            "dark": cls.DARK,
        }.get(value, cls.SYSTEM)

    @property
    def title(self) -> str:
        """Человекочитаемое название режима."""
        return {
            ThemePreference.SYSTEM: "Системная",
            ThemePreference.LIGHT: "Светлая",
            ThemePreference.DARK: "Тёмная",
        }[self]


# ---------------------------------------------------------------------------
# Семантическая палитра
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AppPalette:
    """Набор семантических цветов для пользовательских компонентов."""

    # Фоны
    content_bg: str
    sidebar_bg: str
    card_bg: str
    field_fill: str

    # Границы и разделители
    card_border: str
    divider: str

    # Текст
    text_primary: str
    text_secondary: str
    text_hint: str

    # Акцент (фирменный «лесной» зелёный)
    accent: str
    accent_hover: str
    on_accent: str
    accent_container: str
    accent_container_text: str

    # Навигация боковой панели
    nav_item_text: str
    nav_item_hover_bg: str
    nav_item_selected_bg: str
    nav_item_selected_text: str

    # Область перетаскивания
    dropzone_border: str
    dropzone_bg: str
    dropzone_active_bg: str
    dropzone_active_border: str

    # Статусы
    success_bg: str
    success_fg: str
    success_border: str
    error_bg: str
    error_fg: str
    error_border: str
    warning_bg: str
    warning_fg: str
    warning_border: str
    info_bg: str
    info_fg: str
    info_border: str

    # Тень карточек
    shadow: str

    @classmethod
    def light(cls) -> "AppPalette":
        """Светлая палитра (стилистика Windows 11 / Fluent)."""
        return cls(
            content_bg="#F3F5F3",
            sidebar_bg="#FBFCFB",
            card_bg="#FFFFFF",
            field_fill="#F6F8F6",
            card_border="#E3E8E3",
            divider="#E5EAE5",
            text_primary="#1B211C",
            text_secondary="#55605A",
            text_hint="#8B958E",
            accent="#1E7A46",
            accent_hover="#1A6B3E",
            on_accent="#FFFFFF",
            accent_container="#E2F1E8",
            accent_container_text="#14532D",
            nav_item_text="#414B44",
            nav_item_hover_bg="#EDF2EE",
            nav_item_selected_bg="#E2F1E8",
            nav_item_selected_text="#14532D",
            dropzone_border="#C3D2C7",
            dropzone_bg="#F4F8F5",
            dropzone_active_bg="#E2F1E8",
            dropzone_active_border="#1E7A46",
            success_bg="#E6F4EA",
            success_fg="#137333",
            success_border="#A8DAB5",
            error_bg="#FCEBEA",
            error_fg="#C5221F",
            error_border="#F3B8B3",
            warning_bg="#FEF7E0",
            warning_fg="#B06000",
            warning_border="#F2DCA0",
            info_bg="#E2F1E8",
            info_fg="#14532D",
            info_border="#B7DCC6",
            shadow="#0F1A130F",
        )

    @classmethod
    def dark(cls) -> "AppPalette":
        """Тёмная палитра (мягкие природные тона, без чистого чёрного)."""
        return cls(
            content_bg="#121714",
            sidebar_bg="#161C18",
            card_bg="#1B221E",
            field_fill="#1F2622",
            card_border="#2A332D",
            divider="#28302A",
            text_primary="#E4EAE5",
            text_secondary="#9CA79F",
            text_hint="#6C7A70",
            accent="#7CC79B",
            accent_hover="#93D6AF",
            on_accent="#0B2E1B",
            accent_container="#1E3D2B",
            accent_container_text="#A9E5C3",
            nav_item_text="#B4BFB7",
            nav_item_hover_bg="#202824",
            nav_item_selected_bg="#1E3D2B",
            nav_item_selected_text="#A9E5C3",
            dropzone_border="#35443A",
            dropzone_bg="#19201C",
            dropzone_active_bg="#1E3D2B",
            dropzone_active_border="#7CC79B",
            success_bg="#16301F",
            success_fg="#8DDBA8",
            success_border="#2A5C3F",
            error_bg="#3A1C1A",
            error_fg="#F2B8B5",
            error_border="#6E3430",
            warning_bg="#33270F",
            warning_fg="#F0C674",
            warning_border="#6B531F",
            info_bg="#1E3D2B",
            info_fg="#A9E5C3",
            info_border="#2F5B40",
            shadow="#00000066",
        )


# ---------------------------------------------------------------------------
# Фабрики тем Material 3
# ---------------------------------------------------------------------------


def build_light_theme() -> ft.Theme:
    """Собирает светлую тему Material 3."""
    return ft.Theme(
        use_material3=True,
        font_family=FONT_FAMILY,
        color_scheme=ft.ColorScheme(
            primary="#1E7A46",
            on_primary="#FFFFFF",
            primary_container="#C9EBD6",
            on_primary_container="#0E3B21",
            secondary="#4E6355",
            on_secondary="#FFFFFF",
            secondary_container="#D0E8D8",
            on_secondary_container="#0C1F14",
            tertiary="#3A6472",
            on_tertiary="#FFFFFF",
            surface="#FFFFFF",
            on_surface="#1B211C",
            on_surface_variant="#4A554C",
            surface_container_lowest="#FFFFFF",
            surface_container_low="#F3F5F3",
            surface_container="#EDF1ED",
            surface_container_high="#E7EBE7",
            surface_container_highest="#E1E6E1",
            outline="#77857B",
            outline_variant="#D8E0D9",
            error="#BA1A1A",
            on_error="#FFFFFF",
            error_container="#FFDAD6",
            on_error_container="#410002",
            shadow="#000000",
            scrim="#000000",
        ),
    )


def build_dark_theme() -> ft.Theme:
    """Собирает тёмную тему Material 3."""
    return ft.Theme(
        use_material3=True,
        font_family=FONT_FAMILY,
        color_scheme=ft.ColorScheme(
            primary="#8CD5A9",
            on_primary="#0B3A20",
            primary_container="#14532D",
            on_primary_container="#C9EBD6",
            secondary="#A9C4B2",
            on_secondary="#1C3524",
            secondary_container="#2C4A38",
            on_secondary_container="#C5E0CE",
            tertiary="#A3CBD8",
            on_tertiary="#0E3440",
            surface="#121714",
            on_surface="#E0E5E1",
            on_surface_variant="#B9C4BC",
            surface_container_lowest="#0D110E",
            surface_container_low="#121714",
            surface_container="#161C18",
            surface_container_high="#1B221E",
            surface_container_highest="#202824",
            outline="#84928A",
            outline_variant="#3A453E",
            error="#F2B8B5",
            on_error="#601410",
            error_container="#8C1D18",
            on_error_container="#FFDAD6",
            shadow="#000000",
            scrim="#000000",
        ),
    )


# ---------------------------------------------------------------------------
# Контроллер темы
# ---------------------------------------------------------------------------


class ThemeController:
    """Управляет режимом темы и оповещает подписчиков о её смене.

    Реализует простой паттерн «наблюдатель»: компоненты с ручной
    раскраской подписываются через :meth:`add_listener` и перестраиваются
    при смене темы.
    """

    def __init__(self) -> None:
        self._preference: ThemePreference = ThemePreference.SYSTEM
        self._page: ft.Page | None = None
        self._listeners: list[Callable[[], None]] = []

    # ------------------------------------------------------------------
    # Инициализация
    # ------------------------------------------------------------------

    def attach(self, page: ft.Page, preference: ThemePreference) -> None:
        """Привязывает контроллер к странице и применяет тему."""
        self._page = page
        self._preference = preference
        page.theme = build_light_theme()
        page.dark_theme = build_dark_theme()
        page.theme_mode = self._to_theme_mode(preference)
        self._apply_window_theme()
        logger.info("Тема применена: %s", preference.value)

    # ------------------------------------------------------------------
    # Состояние
    # ------------------------------------------------------------------

    @property
    def preference(self) -> ThemePreference:
        """Текущее пользовательское предпочтение темы."""
        return self._preference

    @property
    def effective_brightness(self) -> ft.Brightness:
        """Фактическая яркость с учётом системной темы ОС."""
        if self._preference is ThemePreference.LIGHT:
            return ft.Brightness.LIGHT
        if self._preference is ThemePreference.DARK:
            return ft.Brightness.DARK
        if self._page is not None:
            platform_brightness = self._page.platform_brightness
            if platform_brightness is not None:
                return platform_brightness
        return ft.Brightness.LIGHT

    @property
    def palette(self) -> AppPalette:
        """Активная семантическая палитра."""
        if self.effective_brightness is ft.Brightness.DARK:
            return AppPalette.dark()
        return AppPalette.light()

    # ------------------------------------------------------------------
    # Управление
    # ------------------------------------------------------------------

    def set_preference(self, preference: ThemePreference) -> None:
        """Устанавливает режим темы и уведомляет подписчиков.

        Персистентность (запись в настройки) выполняет вызывающая
        сторона — как правило, обработчик в слое UI.
        """
        if preference is self._preference:
            return
        self._preference = preference
        if self._page is not None:
            self._page.theme_mode = self._to_theme_mode(preference)
            self._apply_window_theme()
            self._page.update()
        logger.info("Тема изменена на: %s", preference.value)
        self._notify()

    def add_listener(self, listener: Callable[[], None]) -> None:
        """Подписывает функцию на событие смены темы."""
        if listener not in self._listeners:
            self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[], None]) -> None:
        """Отписывает функцию от события смены темы."""
        if listener in self._listeners:
            self._listeners.remove(listener)

    # ------------------------------------------------------------------
    # Внутренние helpers
    # ------------------------------------------------------------------

    def _apply_window_theme(self) -> None:
        """Синхронизирует цвет окна с текущей темой приложения."""
        if self._page is None:
            return
        palette = self.palette
        try:
            self._page.window.bgcolor = palette.sidebar_bg
            self._page.bgcolor = palette.content_bg
        except Exception:  # noqa: BLE001 — некоторые платформы могут не поддерживать
            logger.debug("Не удалось применить цвет окна для текущей темы")

    def _notify(self) -> None:
        for listener in list(self._listeners):
            try:
                listener()
            except Exception:  # noqa: BLE001 — слушатель не должен рушить приложение
                logger.exception("Ошибка в подписчике смены темы")

    @staticmethod
    def _to_theme_mode(preference: ThemePreference) -> ft.ThemeMode:
        return {
            ThemePreference.SYSTEM: ft.ThemeMode.SYSTEM,
            ThemePreference.LIGHT: ft.ThemeMode.LIGHT,
            ThemePreference.DARK: ft.ThemeMode.DARK,
        }[preference]
