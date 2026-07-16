"""Настройка системы логирования приложения.

Используется стандартный модуль :mod:`logging`. Журналы пишутся в папку
``logs/`` с ротацией файлов. Уровни: INFO, WARNING, ERROR
(отладочный уровень включается отдельно при необходимости).

Важно: пользовательские сообщения выводятся только в интерфейсе,
консоль и ``print`` для этого не используются. Логирование предназначено
для диагностики и аудита работы приложения.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from core.constants import LOG_BACKUP_COUNT, LOG_MAX_BYTES

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured: bool = False


def setup_logging(logs_dir: Path, level: int = logging.INFO) -> None:
    """Инициализирует корневой логгер приложения.

    Функция идемпотентна: повторные вызовы (например, при горячей
    перезагрузке во время разработки) не создают дублирующих обработчиков.

    Args:
        logs_dir: Каталог для файлов журнала.
        level: Минимальный уровень регистрируемых сообщений.
    """
    global _configured
    if _configured:
        return

    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "forest_assistant.log"

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    root_logger.addHandler(file_handler)

    _configured = True
    logging.getLogger(__name__).info(
        "Система логирования инициализирована. Файл журнала: %s", log_file
    )


def get_logger(name: str) -> logging.Logger:
    """Возвращает именованный логгер для модуля.

    Args:
        name: Имя логгера, обычно ``__name__`` вызывающего модуля.

    Returns:
        Настроенный экземпляр :class:`logging.Logger`.
    """
    return logging.getLogger(name)
