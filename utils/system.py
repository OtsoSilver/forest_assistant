"""Кроссплатформенные операции с файловым менеджером ОС."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from core.logging_config import get_logger

logger = get_logger(__name__)


def reveal_in_file_manager(path: Path) -> bool:
    """Открывает файловый менеджер ОС и выделяет указанный файл.

    Поддерживаются Windows (Проводник), macOS (Finder) и Linux (xdg-open).
    Ошибка операции не прерывает работу приложения — она фиксируется
    в журнале, а вызывающая сторона показывает пользователю уведомление.

    Args:
        path: Путь к файлу или папке, которую нужно показать.

    Returns:
        ``True``, если файловый менеджер был запущен успешно.
    """
    try:
        if sys.platform == "win32":
            if path.is_file():
                # /select выделяет файл в уже знакомом пользователю Проводнике.
                subprocess.Popen(["explorer", "/select,", str(path)])
            else:
                os.startfile(str(path))  # noqa: S606 — целевая платформа Windows
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-R", str(path)])
        else:
            target = path if path.is_dir() else path.parent
            subprocess.Popen(["xdg-open", str(target)])
        logger.info("Открыт файловый менеджер для пути: %s", path)
        return True
    except (OSError, subprocess.SubprocessError) as exc:
        logger.warning("Не удалось открыть файловый менеджер для %s: %s", path, exc)
        return False
