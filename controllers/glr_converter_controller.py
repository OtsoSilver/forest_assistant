"""Контроллер страницы «Конвертер выписок ГЛР → GPX».

Принимает события представления, управляет состоянием формы, вызывает
сервис конвертации в фоновом потоке (интерфейс не блокируется) и
отображает результат через контракт представления. Все ошибки
обрабатываются и показываются внутри интерфейса — консоль и print
не используются нигде.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Protocol

import flet as ft

from controllers.base_controller import BaseController
from core.context import AppContext
from models.conversion import ConversionError, ConversionRequest, ConversionResult
from services.conversion_service import ConversionService
from utils.system import reveal_in_file_manager
from utils.validators import OutputNameValidator, PathValidator, ValidationResult


class GlrConverterViewContract(Protocol):
    """Контракт представления, необходимый контроллеру.

    Реализуется страницей :class:`ui.pages.glr_converter_page.GlrConverterPage`.
    Протокол изолирует контроллер от конкретной реализации интерфейса.
    """

    def set_source_file(self, path: Path, size: int | None) -> None: ...
    def clear_source_file(self) -> None: ...
    def set_save_dir(self, path: Path | None) -> None: ...
    def get_output_parts_raw(self) -> tuple[str, str]: ...
    def show_name_validation(self, result: ValidationResult, *, show_empty_error: bool) -> None: ...
    def set_convert_enabled(self, enabled: bool) -> None: ...
    def set_busy(self, busy: bool) -> None: ...
    def show_progress_status(self, text: str) -> None: ...
    def show_success_status(self, result: ConversionResult) -> None: ...
    def show_error_status(self, title: str, message: str) -> None: ...
    def hide_status(self) -> None: ...


class GlrConverterController(BaseController[GlrConverterViewContract]):
    """Управляет сценарием конвертации: выбор файла → имя → папка → запуск."""

    def __init__(self, context: AppContext, service: ConversionService) -> None:
        super().__init__(context)
        self._service = service
        self._selected_zip: Path | None = None
        self._selected_zip_size: int | None = None
        self._save_dir: Path | None = None
        self._name_validation: ValidationResult = ValidationResult.fail("")
        self._is_converting: bool = False

    # ------------------------------------------------------------------
    # Инициализация состояния представления
    # ------------------------------------------------------------------

    def init_view_state(self) -> None:
        """Восстанавливает состояние формы из настроек при открытии страницы."""
        last_save_dir = self._context.settings.current.last_save_dir
        if last_save_dir:
            candidate = Path(last_save_dir)
            if candidate.is_dir():
                self._save_dir = candidate
                self.view.set_save_dir(candidate)
                self._logger.debug("Восстановлена папка сохранения: %s", candidate)
        self._refresh_convert_availability()

    # ------------------------------------------------------------------
    # Шаг 1. Выбор ZIP-файла
    # ------------------------------------------------------------------

    async def on_pick_file_clicked(self) -> None:
        """Открывает системный диалог выбора ZIP-архива."""
        try:
            files = await self._context.file_picker.pick_files(
                dialog_title="Выберите ZIP-файл с выпиской ГЛР",
                initial_directory=self._initial_open_dir(),
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["zip"],
                allow_multiple=False,
            )
        except Exception as exc:  # noqa: BLE001
            self._logger.exception("Ошибка диалога выбора файла")
            self._context.notifications.show_error(
                "Не удалось открыть диалог выбора файла", str(exc)
            )
            return

        if not files:
            return  # Пользователь отменил выбор — это не ошибка.

        picked = files[0]
        if picked.path is None:
            self._context.notifications.show_error(
                "Не удалось получить путь к выбранному файлу"
            )
            return

        path = Path(picked.path)
        size = picked.size if picked.size is not None else self._file_size(path)

        self._selected_zip = path
        self._selected_zip_size = size
        self._context.settings.update(
            lambda s: setattr(s, "last_open_dir", str(path.parent))
        )
        self.view.set_source_file(path, size)
        self.view.hide_status()
        self._refresh_convert_availability()
        self._logger.info("Выбран ZIP-файл: %s (%s байт)", path, size)

    def on_file_cleared(self) -> None:
        """Сбрасывает выбранный файл."""
        self._selected_zip = None
        self._selected_zip_size = None
        self.view.clear_source_file()
        self.view.hide_status()
        self._refresh_convert_availability()

    # ------------------------------------------------------------------
    # Шаг 2. Имя выходного файла
    # ------------------------------------------------------------------

    def on_output_parts_changed(self, quarter_raw: str, compartment_raw: str) -> None:
        """Живая валидация имени при каждом изменении полей ввода."""
        self._name_validation = OutputNameValidator.validate_parts(quarter_raw, compartment_raw)
        self.view.show_name_validation(self._name_validation, show_empty_error=False)
        if self._name_validation.is_valid:
            self.view.hide_status()
        self._refresh_convert_availability()

    # ------------------------------------------------------------------
    # Шаг 3. Папка сохранения
    # ------------------------------------------------------------------

    async def on_pick_save_dir_clicked(self) -> None:
        """Открывает системный диалог выбора папки сохранения."""
        try:
            directory = await self._context.file_picker.get_directory_path(
                dialog_title="Выберите папку для сохранения GPX-файла",
                initial_directory=self._initial_save_dir(),
            )
        except Exception as exc:  # noqa: BLE001
            self._logger.exception("Ошибка диалога выбора папки")
            self._context.notifications.show_error(
                "Не удалось открыть диалог выбора папки", str(exc)
            )
            return

        if not directory:
            return  # Отмена выбора — не ошибка.

        path = Path(directory)
        self._save_dir = path
        self._context.settings.update(
            lambda s: setattr(s, "last_save_dir", str(path))
        )
        self.view.set_save_dir(path)
        self.view.hide_status()
        self._refresh_convert_availability()
        self._logger.info("Выбрана папка сохранения: %s", path)

    # ------------------------------------------------------------------
    # Шаг 4. Конвертация
    # ------------------------------------------------------------------

    async def on_convert_clicked(self) -> None:
        """Запускает конвертацию в фоновом потоке, не блокируя интерфейс."""
        if self._is_converting:
            return

        request = self._build_request()
        if request is None:
            return  # Ошибки валидации уже отображены пользователю.

        self._is_converting = True
        self.view.set_busy(True)
        self._refresh_convert_availability()
        self.view.show_progress_status("Выполняется конвертация, пожалуйста, подождите…")
        self._logger.info("Старт конвертации: %s", request.zip_path)

        try:
            result = await asyncio.to_thread(self._service.convert, request)
        except ConversionError as exc:
            self._logger.warning(
                "Ошибка конвертации: %s (%s)", exc.user_message, exc.technical_details
            )
            self.view.show_error_status("Не удалось выполнить конвертацию", exc.user_message)
        except Exception as exc:  # noqa: BLE001 — последний рубеж обработки
            self._logger.exception("Непредвиденная ошибка при конвертации")
            self.view.show_error_status(
                "Произошла непредвиденная ошибка",
                f"{exc}\nПодробности записаны в журнал (папка logs/).",
            )
        else:
            self.view.show_success_status(result)
            self._context.notifications.show_success(
                "Конвертация успешно завершена",
                f"Файл сохранён в:\n{result.output_file}",
            )
        finally:
            self._is_converting = False
            self.view.set_busy(False)
            self._refresh_convert_availability()

    def on_reveal_output_clicked(self, path: Path) -> None:
        """Показывает созданный файл в файловом менеджере ОС."""
        if not reveal_in_file_manager(path):
            self._context.notifications.show_error(
                "Не удалось открыть расположение файла", str(path)
            )

    # ------------------------------------------------------------------
    # Внутренняя логика
    # ------------------------------------------------------------------

    def _build_request(self) -> ConversionRequest | None:
        """Собирает и валидирует запрос; при ошибке показывает её в интерфейсе."""
        zip_check = PathValidator.validate_zip_path(self._selected_zip)
        name_check = OutputNameValidator.validate_parts(*self._current_output_parts())
        dir_check = PathValidator.validate_output_dir(self._save_dir)

        self._name_validation = name_check
        self.view.show_name_validation(name_check, show_empty_error=True)

        first_error = next(
            (check.error for check in (zip_check, name_check, dir_check) if not check.is_valid),
            None,
        )
        if first_error is not None:
            self.view.show_error_status("Проверьте исходные данные", first_error)
            self._logger.info("Конвертация отклонена валидацией: %s", first_error)
            return None

        # Все три проверки пройдены — значения гарантированно присутствуют.
        assert self._selected_zip is not None
        assert self._save_dir is not None
        assert name_check.normalized is not None
        return ConversionRequest(
            zip_path=self._selected_zip,
            output_dir=self._save_dir,
            output_name=name_check.normalized,
        )

    def _current_output_parts(self) -> tuple[str, str]:
        """Читает текущие значения полей квартала и выдела из представления."""
        return self.view.get_output_parts_raw()

    def _refresh_convert_availability(self) -> None:
        """Пересчитывает доступность кнопки «Конвертировать»."""
        ready = (
            self._selected_zip is not None
            and self._save_dir is not None
            and self._name_validation.is_valid
            and not self._is_converting
        )
        self.view.set_convert_enabled(ready)

    def _initial_open_dir(self) -> str | None:
        """Стартовая директория диалога выбора файла."""
        if self._selected_zip is not None:
            return str(self._selected_zip.parent)
        return self._context.settings.current.last_open_dir

    def _initial_save_dir(self) -> str | None:
        """Стартовая директория диалога выбора папки сохранения."""
        if self._save_dir is not None:
            return str(self._save_dir)
        return self._context.settings.current.last_save_dir

    @staticmethod
    def _file_size(path: Path) -> int | None:
        try:
            return path.stat().st_size
        except OSError:
            return None
