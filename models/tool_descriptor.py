"""Дескриптор инструмента — единица плагинной системы.

Каждый инструмент приложения описывается дескриптором и регистрируется
в :class:`core.registry.ToolRegistry`. Боковая панель и маршрутизатор
строятся автоматически на основе зарегистрированных дескрипторов,
поэтому добавление нового инструмента не требует изменения оболочки.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from core.context import AppContext
    from ui.pages.base_page import BasePage

#: Фабрика страницы инструмента. Получает контекст приложения (DI) и
#: собственный дескриптор, возвращает готовую к отображению страницу.
PageFactory = Callable[["AppContext", "ToolDescriptor"], "BasePage"]


@dataclass(frozen=True, slots=True)
class ToolDescriptor:
    """Описание инструмента для реестра.

    Attributes:
        tool_id: Уникальный стабильный идентификатор (например, ``"glr_to_gpx"``).
        title: Полное название, отображается в заголовке страницы.
        menu_title: Краткое название для пункта меню боковой панели.
        subtitle: Подзаголовок-описание на странице инструмента.
        icon: Иконка пункта меню (значение из ``ft.Icons``).
        page_factory: Фабрика, создающая страницу инструмента.
        order: Порядок сортировки в меню (меньше — выше).
        keywords: Ключевые слова для будущего поиска по инструментам.
    """

    tool_id: str
    title: str
    menu_title: str
    subtitle: str
    icon: Any
    page_factory: PageFactory
    order: int = 100
    keywords: tuple[str, ...] = field(default_factory=tuple)
