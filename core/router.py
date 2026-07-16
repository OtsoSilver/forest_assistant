"""Маршрутизатор рабочих страниц приложения.

Хранит идентификатор активного инструмента и оповещает подписчиков
(главный макет) о навигации. Сам ничего не отрисовывает — только
управляет состоянием навигации.
"""

from __future__ import annotations

from collections.abc import Callable

from core.logging_config import get_logger
from core.registry import ToolRegistry
from models.tool_descriptor import ToolDescriptor

logger = get_logger(__name__)


class Router:
    """Управляет активной страницей и уведомляет о её смене."""

    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry
        self._current_tool_id: str | None = None
        self._listeners: list[Callable[[ToolDescriptor], None]] = []

    # ------------------------------------------------------------------
    # Состояние
    # ------------------------------------------------------------------

    @property
    def current_tool_id(self) -> str | None:
        """Идентификатор активного инструмента (или ``None``)."""
        return self._current_tool_id

    @property
    def current_tool(self) -> ToolDescriptor | None:
        """Дескриптор активного инструмента (или ``None``)."""
        if self._current_tool_id is None:
            return None
        return self._registry.get(self._current_tool_id)

    # ------------------------------------------------------------------
    # Навигация
    # ------------------------------------------------------------------

    def navigate(self, tool_id: str) -> None:
        """Переключает активную страницу на указанный инструмент.

        Повторная навигация к уже активной странице игнорируется.
        """
        if tool_id == self._current_tool_id:
            return
        descriptor = self._registry.get(tool_id)
        if descriptor is None:
            logger.warning("Попытка навигации к незарегистрированному инструменту: %s", tool_id)
            return

        self._current_tool_id = tool_id
        logger.info("Навигация к инструменту: %s", tool_id)
        for listener in list(self._listeners):
            try:
                listener(descriptor)
            except Exception:  # noqa: BLE001
                logger.exception("Ошибка в подписчике маршрутизатора")

    def navigate_to_first(self) -> None:
        """Открывает первый инструмент реестра (стартовая страница)."""
        tools = self._registry.tools
        if tools:
            self.navigate(tools[0].tool_id)
        else:
            logger.warning("Реестр инструментов пуст — нечего отображать")

    def add_listener(self, listener: Callable[[ToolDescriptor], None]) -> None:
        """Подписывает функцию на событие навигации."""
        if listener not in self._listeners:
            self._listeners.append(listener)
