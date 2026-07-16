"""Плагин инструмента «Конвертер выписок ГЛР → GPX».

Регистрирует инструмент в реестре: собирает цепочку
«алгоритм → сервис → контроллер → страница» (внедрение зависимостей)
и отдаёт оболочке готовый дескриптор. Оболочка приложения ничего
не знает об этом модуле — он подключается автодискавери.
"""

from __future__ import annotations

import flet as ft

from controllers.glr_converter_controller import GlrConverterController
from core.context import AppContext
from core.registry import ToolRegistry
from models.tool_descriptor import ToolDescriptor
from services.conversion_service import ConversionService
from services.glr_converter import GlrToGpxAlgorithm
from ui.pages.base_page import BasePage
from ui.pages.glr_converter_page import GlrConverterPage


def create_page(context: AppContext, descriptor: ToolDescriptor) -> BasePage:
    """Фабрика страницы: композиция зависимостей инструмента.

    Алгоритм конвертации подключается здесь как отдельный сервис —
    его код остаётся нетронутым и изолированным в ``services/``.
    """
    algorithm = GlrToGpxAlgorithm()
    service = ConversionService(algorithm)
    controller = GlrConverterController(context, service)
    return GlrConverterPage(context, descriptor, controller)


def register(registry: ToolRegistry) -> None:
    """Регистрирует инструмент в реестре (вызывается автодискавери)."""
    registry.register(
        ToolDescriptor(
            tool_id="glr_to_gpx",
            title="Конвертер выписок ГЛР → GPX",
            menu_title="Конвертер ГЛР → GPX",
            subtitle=(
                "Преобразование выписок государственного лесного реестра "
                "из ZIP-архива в файл GPX"
            ),
            icon=ft.Icons.ROUTE,
            page_factory=create_page,
            order=10,
            keywords=("глр", "gpx", "выписка", "лесной реестр", "конвертер"),
        )
    )
