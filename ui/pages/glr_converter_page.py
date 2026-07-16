"""Страница инструмента «Конвертер выписок ГЛР → GPX».

Современная карточная страница из четырёх шагов: выбор ZIP-архива,
ввод имени выходного файла с живой валидацией, выбор папки сохранения
и запуск конвертации. Вся логика вынесена в контроллер — страница
только отображает состояние и передаёт события.
"""

from __future__ import annotations

from pathlib import Path

import flet as ft

from controllers.glr_converter_controller import GlrConverterController
from core.constants import OUTPUT_NAME_HELPER, OUTPUT_NAME_HINT
from core.context import AppContext
from models.conversion import ConversionResult
from models.tool_descriptor import ToolDescriptor
from ui.components.card import SectionCard
from ui.components.directory_field import DirectoryField
from ui.components.drop_zone import DropZone
from ui.components.loading_button import LoadingButton
from ui.components.status_banner import BannerKind, StatusBanner
from ui.pages.base_page import BasePage
from utils.validators import ValidationResult


class GlrConverterPage(BasePage):
    """Рабочая страница конвертера выписок ГЛР → GPX.

    Реализует контракт :class:`GlrConverterViewContract` — набор методов,
    через которые контроллер обновляет состояние представления.
    """

    def __init__(
        self,
        context: AppContext,
        descriptor: ToolDescriptor,
        controller: GlrConverterController,
    ) -> None:
        super().__init__(context, descriptor)
        self._controller = controller
        self._controller.attach_view(self)

    # ------------------------------------------------------------------
    # Построение
    # ------------------------------------------------------------------

    def build_content(self) -> ft.Control:
        palette = self._context.theme.palette

        # Шаг 1 — выбор ZIP-файла.
        self._drop_zone = DropZone(
            palette=palette,
            on_pick_requested=self._request_file_pick,
            on_file_cleared=self._controller.on_file_cleared,
        )
        file_card = SectionCard(
            step=1,
            icon=ft.Icons.FOLDER_ZIP,
            title="Исходный файл",
            subtitle="ZIP-архив с выпиской государственного лесного реестра",
            content=self._drop_zone,
            palette=palette,
        )

        # Шаг 2 — имя выходного файла.
        self._quarter_field = ft.TextField(
            label="Квартал",
            hint_text="18",
            helper="Только цифры",
            helper_style=ft.TextStyle(size=12, color=palette.text_hint),
            label_style=ft.TextStyle(color=palette.text_secondary),
            prefix_icon=ft.Icons.TAG,
            border=ft.InputBorder.OUTLINE,
            border_radius=ft.BorderRadius.all(12),
            border_color=palette.card_border,
            focused_border_color=palette.accent,
            cursor_color=palette.accent,
            filled=True,
            fill_color=palette.field_fill,
            text_size=14.5,
            content_padding=ft.Padding.symmetric(horizontal=16, vertical=15),
            keyboard_type=ft.KeyboardType.NUMBER,
            max_length=4,
            on_change=self._handle_name_change,
        )
        self._compartment_field = ft.TextField(
            label="Выдел",
            hint_text="12",
            helper="Только цифры",
            helper_style=ft.TextStyle(size=12, color=palette.text_hint),
            label_style=ft.TextStyle(color=palette.text_secondary),
            prefix_icon=ft.Icons.LANDSCAPE,
            border=ft.InputBorder.OUTLINE,
            border_radius=ft.BorderRadius.all(12),
            border_color=palette.card_border,
            focused_border_color=palette.accent,
            cursor_color=palette.accent,
            filled=True,
            fill_color=palette.field_fill,
            text_size=14.5,
            content_padding=ft.Padding.symmetric(horizontal=16, vertical=15),
            keyboard_type=ft.KeyboardType.NUMBER,
            max_length=4,
            on_change=self._handle_name_change,
        )
        name_content = ft.Row(
            spacing=16,
            controls=[self._quarter_field, self._compartment_field],
        )
        name_card = SectionCard(
            step=2,
            icon=ft.Icons.EDIT_OUTLINED,
            title="Имя выходного файла",
            subtitle="Введите номер квартала и выдела в цифровом формате",
            content=name_content,
            palette=palette,
        )

        # Шаг 3 — папка сохранения.
        self._dir_field = DirectoryField(
            palette=palette,
            on_browse_requested=self._request_dir_pick,
        )
        dir_card = SectionCard(
            step=3,
            icon=ft.Icons.SAVE_AS,
            title="Папка сохранения",
            subtitle="Выбранная папка запоминается для следующих запусков",
            content=self._dir_field,
            palette=palette,
        )

        # Шаг 4 — запуск и состояние операции.
        self._convert_button = LoadingButton(
            label="Конвертировать",
            loading_label="Конвертация…",
            icon=ft.Icons.AUTORENEW,
            palette=palette,
            on_click=self._controller.on_convert_clicked,
        )
        self._status_banner = StatusBanner(palette)

        self._cards = (file_card, name_card, dir_card)

        return ft.Column(
            spacing=20,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                file_card,
                name_card,
                dir_card,
                ft.Container(height=2),
                ft.Row(controls=[self._convert_button]),
                self._status_banner,
            ],
        )

    # ------------------------------------------------------------------
    # Жизненный цикл
    # ------------------------------------------------------------------

    def on_mounted(self) -> None:
        """Вызывается макетом после добавления страницы на экран."""
        self._controller.init_view_state()

    def dispose(self) -> None:
        """Освобождает ресурсы при переключении на другую страницу."""
        self._controller.dispose()

    # ------------------------------------------------------------------
    # События элементов (мост к контроллеру)
    # ------------------------------------------------------------------

    def _request_file_pick(self) -> None:
        self._context.page.run_task(self._controller.on_pick_file_clicked)

    def _request_dir_pick(self) -> None:
        self._context.page.run_task(self._controller.on_pick_save_dir_clicked)

    def _handle_name_change(self, event: ft.ControlEvent) -> None:
        self._controller.on_output_parts_changed(
            self._quarter_field.value or "",
            self._compartment_field.value or "",
        )

    # ------------------------------------------------------------------
    # Контракт представления (вызывается контроллером)
    # ------------------------------------------------------------------

    def set_source_file(self, path: Path, size: int | None) -> None:
        self._drop_zone.set_file(path, size)

    def clear_source_file(self) -> None:
        self._drop_zone.clear()

    def set_save_dir(self, path: Path | None) -> None:
        self._dir_field.set_path(path)

    def get_output_parts_raw(self) -> tuple[str, str]:
        return self._quarter_field.value or "", self._compartment_field.value or ""

    def show_name_validation(self, result: ValidationResult, *, show_empty_error: bool) -> None:
        """Отображает результат проверки имени: ошибка либо зелёная галочка."""
        fields = (self._quarter_field, self._compartment_field)
        if result.is_valid:
            for field in fields:
                field.error = None
                field.suffix = ft.Icon(
                    ft.Icons.CHECK_CIRCLE,
                    size=20,
                    color=self._context.theme.palette.accent,
                )
        else:
            for field in fields:
                field.suffix = None
            should_show = result.error is not None and show_empty_error
            for field in fields:
                field.error = result.error if should_show else None
        for field in fields:
            field.update()

    def set_convert_enabled(self, enabled: bool) -> None:
        self._convert_button.set_enabled(enabled)

    def set_busy(self, busy: bool) -> None:
        """Блокирует элементы управления на время конвертации."""
        self._drop_zone.set_disabled(busy)
        self._dir_field.set_disabled(busy)
        for field in (self._quarter_field, self._compartment_field):
            field.disabled = busy
            field.update()
        for card in self._cards:
            card.set_disabled(busy)
        self._convert_button.set_loading(busy)

    def show_progress_status(self, text: str) -> None:
        self._status_banner.show(
            BannerKind.PROGRESS,
            "Идёт конвертация",
            text,
        )

    def show_success_status(self, result: ConversionResult) -> None:
        self._status_banner.show(
            BannerKind.SUCCESS,
            "Конвертация успешно завершена",
            f"Файл сохранён в:\n{result.output_file}",
            action_label="Показать в папке",
            on_action=lambda: self._controller.on_reveal_output_clicked(result.output_file),
        )

    def show_error_status(self, title: str, message: str) -> None:
        self._status_banner.show(BannerKind.ERROR, title, message)

    def hide_status(self) -> None:
        self._status_banner.hide()
