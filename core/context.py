"""Контекст приложения — контейнер внедрения зависимостей (DI).

Собирается один раз в точке входа (:mod:`app`) и передаётся фабрикам
страниц и контроллерам. Благодаря этому ни один компонент не создаёт
сервисы самостоятельно — зависимости подаются снаружи (композиция
вместо наследования, явные зависимости).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import flet as ft

from core.config import AppPaths
from core.registry import ToolRegistry
from core.router import Router
from core.settings import SettingsService
from core.theme import ThemeController


class NotificationService(Protocol):
    """Контракт сервиса уведомлений (реализуется в слое UI)."""

    def show_success(self, title: str, message: str | None = None) -> None:
        """Показывает уведомление об успешном завершении операции."""
        ...

    def show_error(self, title: str, message: str | None = None) -> None:
        """Показывает уведомление об ошибке."""
        ...

    def show_info(self, title: str, message: str | None = None) -> None:
        """Показывает информационное уведомление."""
        ...


@dataclass(slots=True)
class AppContext:
    """Агрегат всех сквозных зависимостей приложения.

    Attributes:
        page: Корневая страница Flet.
        paths: Пути приложения (ресурсы, логи, настройки).
        settings: Сервис пользовательских настроек.
        theme: Контроллер темы оформления.
        notifications: Сервис внутриинтерфейсных уведомлений.
        file_picker: Сервис системных диалогов выбора файлов.
        registry: Реестр инструментов (плагинная система).
        router: Маршрутизатор рабочих страниц.
    """

    page: ft.Page
    paths: AppPaths
    settings: SettingsService
    theme: ThemeController
    notifications: NotificationService
    file_picker: ft.FilePicker
    registry: ToolRegistry
    router: Router
