"""Модели предметной области конвертации выписок ГЛР → GPX.

Содержит объекты запроса и результата конвертации, а также иерархию
типизированных исключений. Исключения несут два сообщения: понятное
пользователю (отображается в интерфейсе) и техническое (пишется в журнал).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path

from core.constants import GPX_EXTENSION


class ConversionStatus(Enum):
    """Состояния процесса конвертации (модель состояния представления)."""

    IDLE = auto()
    RUNNING = auto()
    SUCCESS = auto()
    ERROR = auto()


@dataclass(frozen=True, slots=True)
class ConversionRequest:
    """Проверенный запрос на конвертацию.

    Attributes:
        zip_path: Путь к ZIP-архиву с выпиской ГЛР.
        output_dir: Директория сохранения результата.
        output_name: Нормализованное имя выходного файла без расширения
            (например, ``"КВ 18 В 12"``).
    """

    zip_path: Path
    output_dir: Path
    output_name: str

    @property
    def output_file(self) -> Path:
        """Полный путь к результирующему GPX-файлу."""
        return self.output_dir / f"{self.output_name}{GPX_EXTENSION}"


@dataclass(frozen=True, slots=True)
class ConversionResult:
    """Результат успешной конвертации.

    Attributes:
        output_file: Путь к созданному GPX-файлу.
        source_zip: Путь к исходному ZIP-архиву.
        elapsed_seconds: Длительность конвертации в секундах.
    """

    output_file: Path
    source_zip: Path
    elapsed_seconds: float


# ---------------------------------------------------------------------------
# Иерархия исключений конвертации
# ---------------------------------------------------------------------------


class ConversionError(Exception):
    """Базовое исключение процесса конвертации.

    Args:
        user_message: Сообщение, отображаемое пользователю в интерфейсе.
        technical_details: Технические детали для журнала (необязательно).
    """

    def __init__(self, user_message: str, technical_details: str | None = None) -> None:
        super().__init__(user_message)
        self.user_message: str = user_message
        self.technical_details: str | None = technical_details


class ValidationError(ConversionError):
    """Ошибка валидации входных данных (файл, имя, папка сохранения)."""


class ZipReadError(ConversionError):
    """ZIP-архив повреждён или не может быть прочитан."""


class AlgorithmNotIntegratedError(ConversionError):
    """Существующий алгоритм ещё не подключён к сервису.

    Возникает, когда модуль-адаптер ``services/glr_converter.py`` не нашёл
    подключённый алгоритм. Сообщение содержит инструкцию по интеграции.
    """


class AlgorithmExecutionError(ConversionError):
    """Исключение, возникшее внутри алгоритма конвертации.

    Оригинальное исключение сохраняется в ``__cause__`` и в
    ``technical_details`` для последующего анализа по журналу.
    """
