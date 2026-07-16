"""Сервис-оркестратор конвертации выписок ГЛР → GPX.

Связывает проверенный запрос (:class:`ConversionRequest`) с адаптером
алгоритма (:class:`GlrToGpxAlgorithm`): выполняет предварительную
валидацию входных данных, запускает алгоритм и формирует результат.

Сервис синхронный по своей природе (алгоритм — блокирующий), поэтому
вызывается из контроллера через ``asyncio.to_thread`` — интерфейс
никогда не блокируется.
"""

from __future__ import annotations

import time
import zipfile
from pathlib import Path

from core.logging_config import get_logger
from models.conversion import (
    ConversionRequest,
    ConversionResult,
    ValidationError,
    ZipReadError,
)
from services.glr_converter import GlrToGpxAlgorithm
from utils.validators import OutputNameValidator, PathValidator

logger = get_logger(__name__)


class ConversionService:
    """Оркестратор процесса конвертации (валидация → алгоритм → результат)."""

    def __init__(self, algorithm: GlrToGpxAlgorithm) -> None:
        self._algorithm = algorithm

    def convert(self, request: ConversionRequest) -> ConversionResult:
        """Выполняет полный цикл конвертации.

        Args:
            request: Проверенный представлением запрос на конвертацию.

        Returns:
            Результат с фактическим путём к GPX-файлу и длительностью.

        Raises:
            ValidationError: Входные данные не прошли проверку.
            ZipReadError: ZIP-архив повреждён или не читается.
            AlgorithmNotIntegratedError: Алгоритм не подключён.
            AlgorithmExecutionError: Сбой внутри алгоритма.
        """
        logger.info(
            "Получен запрос на конвертацию: архив=%s, выходной файл=%s",
            request.zip_path, request.output_file,
        )
        self._validate_request(request)
        self._ensure_readable_zip(request.zip_path)

        start = time.monotonic()
        output_file = self._algorithm.convert(request.zip_path, request.output_file)
        elapsed = time.monotonic() - start

        result = ConversionResult(
            output_file=output_file,
            source_zip=request.zip_path,
            elapsed_seconds=elapsed,
        )
        logger.info(
            "Конвертация успешно завершена за %.2f с. Файл сохранён: %s",
            elapsed, result.output_file,
        )
        return result

    # ------------------------------------------------------------------
    # Валидация
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_request(request: ConversionRequest) -> None:
        """Проверяет все компоненты запроса перед запуском алгоритма."""
        zip_check = PathValidator.validate_zip_path(request.zip_path)
        if not zip_check.is_valid:
            raise ValidationError(zip_check.error or "Некорректный ZIP-файл")

        name_check = OutputNameValidator.validate(request.output_name)
        if not name_check.is_valid:
            raise ValidationError(name_check.error or "Некорректное имя файла")

        dir_check = PathValidator.validate_output_dir(request.output_dir)
        if not dir_check.is_valid:
            raise ValidationError(dir_check.error or "Некорректная папка сохранения")

    @staticmethod
    def _ensure_readable_zip(zip_path: Path) -> None:
        """Убеждается, что архив читается как ZIP (структурно не повреждён)."""
        try:
            if not zipfile.is_zipfile(zip_path):
                raise ZipReadError(
                    user_message=(
                        "Выбранный файл не является корректным ZIP-архивом. "
                        "Проверьте, что архив не повреждён."
                    ),
                    technical_details=f"is_zipfile() вернул False для {zip_path}",
                )
        except OSError as exc:
            raise ZipReadError(
                user_message="Не удалось прочитать ZIP-архив. Проверьте доступность файла.",
                technical_details=f"{type(exc).__name__}: {exc}",
            ) from exc
