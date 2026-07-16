"""Конфигурация путей приложения.

Инкапсулирует расположение всех рабочих директорий проекта:
ресурсов, логов и файла настроек. Реализует паттерн «значение-объект»
(value object) — пути вычисляются один раз при старте приложения.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from core.constants import LOG_FILE_NAME, SETTINGS_FILE_NAME


@dataclass(frozen=True, slots=True)
class AppPaths:
    """Неизменяемый набор путей приложения.

    Attributes:
        project_root: Корень проекта (каталог, содержащий ``main.py``).
        assets_dir: Каталог ресурсов (иконки, изображения, шрифты).
        logs_dir: Каталог файлов журнала.
        settings_file: Полный путь к файлу настроек пользователя.
    """

    project_root: Path
    assets_dir: Path
    logs_dir: Path
    settings_file: Path

    @property
    def log_file(self) -> Path:
        """Полный путь к активному файлу журнала."""
        return self.logs_dir / LOG_FILE_NAME

    @property
    def app_icon(self) -> Path:
        """Путь к иконке окна приложения."""
        if sys.platform == "win32":
            return self.assets_dir / "icons" / "app_icon.ico"
        return self.assets_dir / "icons" / "app_icon.png"

    @property
    def logo_image(self) -> Path:
        """Путь к логотипу приложения для отображения в интерфейсе."""
        return self.assets_dir / "images" / "logo.png"

    @classmethod
    def default(cls) -> "AppPaths":
        """Создаёт набор путей относительно корня проекта.

        При запуске из исходников корнем считается каталог проекта.
        Дополнительно гарантирует существование рабочих каталогов.
        """
        project_root = Path(__file__).resolve().parent.parent
        instance = cls(
            project_root=project_root,
            assets_dir=project_root / "assets",
            logs_dir=project_root / "logs",
            settings_file=project_root / SETTINGS_FILE_NAME,
        )
        instance.ensure_directories()
        return instance

    def ensure_directories(self) -> None:
        """Создаёт рабочие каталоги, если они отсутствуют."""
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.mkdir(parents=True, exist_ok=True)
