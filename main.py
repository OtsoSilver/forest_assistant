"""Точка входа приложения «Лесной помощник».

Запуск на Windows (десктопное окно)::

    python main.py

Запуск в браузере (режим разработки интерфейса)::

    set FOREST_ASSISTANT_WEB=1 && python main.py        :: Windows
    FOREST_ASSISTANT_WEB=1 python main.py               # Linux/macOS
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Гарантирует импортируемость пакетов проекта при любом способе запуска.
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import flet as ft

from app import main as app_main
from core.constants import (
    APP_NAME,
    DEFAULT_WEB_PORT,
    ENV_WEB_MODE,
    ENV_WEB_PORT,
)


def run() -> None:
    """Запускает приложение: десктопное окно либо веб-режим разработки."""
    assets_dir = str(PROJECT_ROOT / "assets")

    if os.environ.get(ENV_WEB_MODE) == "1":
        port = int(os.environ.get(ENV_WEB_PORT, str(DEFAULT_WEB_PORT)))
        ft.run(
            app_main,
            # В веб-режиме имя становится частью URL — используем ASCII.
            name="app",
            assets_dir=assets_dir,
            view=ft.AppView.WEB_BROWSER,
            host="127.0.0.1",
            port=port,
        )
    else:
        ft.run(app_main, name=APP_NAME, assets_dir=assets_dir)


if __name__ == "__main__":
    run()
