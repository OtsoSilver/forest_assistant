"""Модель пользовательских настроек приложения.

Настройки сериализуются в JSON и автоматически восстанавливаются
при запуске. Модель устойчива к изменениям схемы: неизвестные поля
игнорируются, отсутствующие — заменяются значениями по умолчанию.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from core.constants import WINDOW_DEFAULT_HEIGHT, WINDOW_DEFAULT_WIDTH

SCHEMA_VERSION: int = 1


@dataclass(slots=True)
class WindowSettings:
    """Геометрия главного окна."""

    width: int = WINDOW_DEFAULT_WIDTH
    height: int = WINDOW_DEFAULT_HEIGHT
    left: int | None = None
    top: int | None = None
    maximized: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WindowSettings":
        """Восстанавливает настройки окна из словаря (толерантно к данным)."""
        return cls(
            width=_safe_int(data.get("width"), WINDOW_DEFAULT_WIDTH),
            height=_safe_int(data.get("height"), WINDOW_DEFAULT_HEIGHT),
            left=_safe_optional_int(data.get("left")),
            top=_safe_optional_int(data.get("top")),
            maximized=bool(data.get("maximized", False)),
        )


@dataclass(slots=True)
class SidebarSettings:
    """Состояние боковой панели."""

    collapsed: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SidebarSettings":
        return cls(collapsed=bool(data.get("collapsed", False)))


@dataclass(slots=True)
class AppSettings:
    """Корневая модель настроек приложения.

    Attributes:
        schema_version: Версия схемы для будущих миграций.
        theme_mode: Режим темы: ``"system"``, ``"light"`` или ``"dark"``.
        last_open_dir: Последняя директория, из которой выбирался файл.
        last_save_dir: Последняя директория сохранения результата.
        window: Геометрия окна.
        sidebar: Состояние боковой панели.
    """

    schema_version: int = SCHEMA_VERSION
    theme_mode: str = "system"
    last_open_dir: str | None = None
    last_save_dir: str | None = None
    window: WindowSettings = field(default_factory=WindowSettings)
    sidebar: SidebarSettings = field(default_factory=SidebarSettings)

    def to_dict(self) -> dict[str, Any]:
        """Сериализует настройки в словарь для записи в JSON."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppSettings":
        """Восстанавливает настройки из словаря.

        Неизвестные ключи игнорируются, повреждённые значения заменяются
        значениями по умолчанию — приложение всегда стартует корректно.
        """
        theme_mode = data.get("theme_mode", "system")
        if theme_mode not in ("system", "light", "dark"):
            theme_mode = "system"

        window_data = data.get("window")
        sidebar_data = data.get("sidebar")

        return cls(
            schema_version=_safe_int(data.get("schema_version"), SCHEMA_VERSION),
            theme_mode=theme_mode,
            last_open_dir=_safe_optional_str(data.get("last_open_dir")),
            last_save_dir=_safe_optional_str(data.get("last_save_dir")),
            window=WindowSettings.from_dict(window_data if isinstance(window_data, dict) else {}),
            sidebar=SidebarSettings.from_dict(sidebar_data if isinstance(sidebar_data, dict) else {}),
        )


def _safe_int(value: Any, default: int) -> int:
    """Приводит значение к ``int`` с откатом к ``default``."""
    try:
        result = int(value)
    except (TypeError, ValueError):
        return default
    return result if result > 0 else default


def _safe_optional_int(value: Any) -> int | None:
    """Приводит значение к ``int | None``."""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_optional_str(value: Any) -> str | None:
    """Приводит значение к ``str | None``; пустая строка трактуется как None."""
    if isinstance(value, str) and value.strip():
        return value
    return None
