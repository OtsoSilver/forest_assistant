"""Реестр инструментов — ядро плагинной системы (Tool Registry).

Принцип открытости/закрытости: оболочка приложения (боковая панель,
маршрутизатор, главный макет) строится только на основе реестра и
ничего не знает о конкретных инструментах. Новый инструмент добавляется
созданием модуля в пакете ``tools/`` с функцией ``register(registry)`` —
без единой правки существующего кода оболочки.
"""

from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Callable
from types import ModuleType

from core.logging_config import get_logger
from models.tool_descriptor import ToolDescriptor

logger = get_logger(__name__)


class ToolRegistry:
    """Хранилище дескрипторов инструментов с автоподключением модулей."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDescriptor] = {}
        self._listeners: list[Callable[[], None]] = []

    # ------------------------------------------------------------------
    # Регистрация
    # ------------------------------------------------------------------

    def register(self, descriptor: ToolDescriptor) -> None:
        """Регистрирует инструмент в реестре.

        Args:
            descriptor: Описание инструмента.

        Raises:
            ValueError: Если инструмент с таким идентификатором уже есть.
        """
        if descriptor.tool_id in self._tools:
            raise ValueError(
                f"Инструмент с идентификатором '{descriptor.tool_id}' уже зарегистрирован"
            )
        self._tools[descriptor.tool_id] = descriptor
        logger.info("Зарегистрирован инструмент: %s (%s)", descriptor.title, descriptor.tool_id)
        self._notify()

    def unregister(self, tool_id: str) -> None:
        """Удаляет инструмент из реестра (если он зарегистрирован)."""
        if self._tools.pop(tool_id, None) is not None:
            logger.info("Инструмент удалён из реестра: %s", tool_id)
            self._notify()

    # ------------------------------------------------------------------
    # Доступ
    # ------------------------------------------------------------------

    def get(self, tool_id: str) -> ToolDescriptor | None:
        """Возвращает дескриптор по идентификатору или ``None``."""
        return self._tools.get(tool_id)

    @property
    def tools(self) -> list[ToolDescriptor]:
        """Все инструменты, отсортированные по порядку вывода в меню."""
        return sorted(self._tools.values(), key=lambda tool: (tool.order, tool.title))

    def __len__(self) -> int:
        return len(self._tools)

    # ------------------------------------------------------------------
    # Автоподключение плагинов
    # ------------------------------------------------------------------

    def autodiscover(self, package_name: str = "tools") -> None:
        """Импортирует все модули пакета ``tools/`` и вызывает их ``register()``.

        Каждый модуль-плагин обязан экспортировать функцию::

            def register(registry: ToolRegistry) -> None: ...

        Модуль без такой функции пропускается с предупреждением в журнале,
        модуль с ошибкой — с записью об ошибке; оболочка продолжает работу.
        """
        package = self._import_package(package_name)
        if package is None or not hasattr(package, "__path__"):
            return

        for module_info in pkgutil.iter_modules(package.__path__):
            module_name = f"{package_name}.{module_info.name}"
            try:
                module = importlib.import_module(module_name)
            except Exception:  # noqa: BLE001 — плагин не должен рушить оболочку
                logger.exception("Не удалось загрузить модуль инструмента: %s", module_name)
                continue

            register = getattr(module, "register", None)
            if not callable(register):
                logger.warning(
                    "Модуль %s пропущен: отсутствует функция register(registry)", module_name
                )
                continue

            try:
                register(self)
            except Exception:  # noqa: BLE001
                logger.exception("Ошибка регистрации инструмента из модуля %s", module_name)

    @staticmethod
    def _import_package(package_name: str) -> ModuleType | None:
        try:
            return importlib.import_module(package_name)
        except ModuleNotFoundError:
            logger.warning("Пакет инструментов '%s' не найден — реестр пуст", package_name)
            return None

    # ------------------------------------------------------------------
    # Наблюдатели
    # ------------------------------------------------------------------

    def add_listener(self, listener: Callable[[], None]) -> None:
        """Подписывает функцию на изменение состава реестра."""
        if listener not in self._listeners:
            self._listeners.append(listener)

    def _notify(self) -> None:
        for listener in list(self._listeners):
            try:
                listener()
            except Exception:  # noqa: BLE001
                logger.exception("Ошибка в подписчике реестра инструментов")
