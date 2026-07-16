"""Сервис хранения пользовательских настроек.

Настройки хранятся в JSON-файле и автоматически восстанавливаются при
запуске приложения. Запись выполняется атомарно (временный файл +
``os.replace``), поэтому внезапное завершение не повреждает файл.
"""

from __future__ import annotations

import json
import os
import threading
from collections.abc import Callable
from pathlib import Path

from core.logging_config import get_logger
from models.app_settings import AppSettings

logger = get_logger(__name__)


class SettingsService:
    """Потокобезопасное хранилище настроек с автосохранением.

    Типичное использование::

        settings.update(lambda s: setattr(s, "theme_mode", "dark"))
        save_dir = settings.current.last_save_dir
    """

    def __init__(self, settings_file: Path) -> None:
        self._settings_file = settings_file
        self._lock = threading.RLock()
        self._settings: AppSettings = self._load()

    # ------------------------------------------------------------------
    # Публичный API
    # ------------------------------------------------------------------

    @property
    def current(self) -> AppSettings:
        """Актуальный снимок настроек (только чтение снаружи)."""
        with self._lock:
            return self._settings

    def update(self, mutator: Callable[[AppSettings], None]) -> None:
        """Применяет изменение к настройкам и сохраняет их на диск.

        Args:
            mutator: Функция, изменяющая объект настроек на месте.
        """
        with self._lock:
            mutator(self._settings)
            self._save_locked()

    def save(self) -> None:
        """Принудительно сохраняет текущие настройки на диск."""
        with self._lock:
            self._save_locked()

    # ------------------------------------------------------------------
    # Загрузка и сохранение
    # ------------------------------------------------------------------

    def _load(self) -> AppSettings:
        """Читает настройки с диска; при любой ошибке возвращает значения по умолчанию."""
        if not self._settings_file.exists():
            logger.info("Файл настроек не найден, используются значения по умолчанию: %s",
                        self._settings_file)
            return AppSettings()

        try:
            raw = self._settings_file.read_text(encoding="utf-8")
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError("корневой элемент настроек не является объектом")
            settings = AppSettings.from_dict(data)
            logger.info("Настройки успешно загружены из %s", self._settings_file)
            return settings
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            logger.warning(
                "Не удалось прочитать настройки (%s). Создана резервная копия, "
                "используются значения по умолчанию.", exc,
            )
            self._backup_corrupted_file()
            return AppSettings()

    def _save_locked(self) -> None:
        """Атомарно записывает настройки. Вызывается под ``self._lock``."""
        temp_file = self._settings_file.with_suffix(".tmp")
        try:
            payload = json.dumps(self._settings.to_dict(), ensure_ascii=False, indent=2)
            temp_file.write_text(payload, encoding="utf-8")
            os.replace(temp_file, self._settings_file)
            logger.debug("Настройки сохранены в %s", self._settings_file)
        except OSError as exc:
            logger.error("Ошибка записи файла настроек %s: %s", self._settings_file, exc)
            temp_file.unlink(missing_ok=True)

    def _backup_corrupted_file(self) -> None:
        """Сохраняет повреждённый файл настроек под именем ``*.broken``."""
        try:
            broken = self._settings_file.with_suffix(".broken")
            os.replace(self._settings_file, broken)
        except OSError as exc:
            logger.warning("Не удалось создать резервную копию повреждённых настроек: %s", exc)
