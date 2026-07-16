"""Пакет плагинов — точка расширения приложения.

КАК ДОБАВИТЬ НОВЫЙ ИНСТРУМЕНТ (без изменения существующего кода):

1. Создайте в этом пакете модуль, например ``tools/my_tool.py``.
2. Опишите в нём функцию регистрации::

       import flet as ft

       from core.context import AppContext
       from core.registry import ToolRegistry
       from models.tool_descriptor import ToolDescriptor
       from ui.pages.base_page import BasePage


       def create_page(context: AppContext, descriptor: ToolDescriptor) -> BasePage:
           ...  # соберите сервисы, контроллер и страницу инструмента


       def register(registry: ToolRegistry) -> None:
           registry.register(
               ToolDescriptor(
                   tool_id="my_tool",
                   title="Мой инструмент",
                   menu_title="Мой инструмент",
                   subtitle="Краткое описание инструмента",
                   icon=ft.Icons.BUILD,
                   page_factory=create_page,
                   order=100,
               )
           )

3. Готово. При следующем запуске реестр автоматически обнаружит модуль
   (автодискавери через :meth:`ToolRegistry.autodiscover`), а пункт меню
   и страница появятся в интерфейсе без правок оболочки.
"""
