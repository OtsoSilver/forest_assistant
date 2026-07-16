"""Базовый контроллер страницы инструмента.

Задаёт общий каркас: доступ к контексту приложения, логгер,
жизненный цикл привязки/отвязки представления.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from core.context import AppContext
from core.logging_config import get_logger

#: Тип представления, с которым работает контроллер (контракт страницы).
ViewT = TypeVar("ViewT")


class BaseController(Generic[ViewT]):
    """Каркас контроллера: контекст + привязанное представление."""

    def __init__(self, context: AppContext) -> None:
        self._context = context
        self._view: ViewT | None = None
        self._logger = get_logger(f"{__name__}.{type(self).__name__}")

    # ------------------------------------------------------------------
    # Зависимости (для наследников)
    # ------------------------------------------------------------------

    @property
    def context(self) -> AppContext:
        """Контекст приложения (настройки, уведомления, диалоги и т.д.)."""
        return self._context

    @property
    def view(self) -> ViewT:
        """Привязанное представление.

        Raises:
            RuntimeError: Если представление ещё не привязано.
        """
        if self._view is None:
            raise RuntimeError(
                f"Представление не привязано к контроллеру {type(self).__name__}"
            )
        return self._view

    # ------------------------------------------------------------------
    # Жизненный цикл
    # ------------------------------------------------------------------

    def attach_view(self, view: ViewT) -> None:
        """Привязывает представление к контроллеру."""
        self._view = view
        self._logger.debug("Представление привязано к %s", type(self).__name__)

    def detach_view(self) -> None:
        """Отвязывает представление (при уничтожении страницы)."""
        self._view = None

    def dispose(self) -> None:
        """Освобождает ресурсы контроллера при закрытии страницы."""
        self.detach_view()
