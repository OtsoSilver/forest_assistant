"""Валидация пользовательского ввода.

Валидаторы не знают об интерфейсе: возвращают результат в виде
неизменяемого объекта :class:`ValidationResult`, а представление
само решает, как его отобразить.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from core.constants import OUTPUT_NAME_PATTERN, ZIP_EXTENSION


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Результат проверки значения.

    Attributes:
        is_valid: Признак успешной проверки.
        normalized: Нормализованное (каноническое) значение, если валидно.
        error: Понятное пользователю сообщение об ошибке, если не валидно.
    """

    is_valid: bool
    normalized: str | None = None
    error: str | None = None

    @classmethod
    def ok(cls, normalized: str) -> "ValidationResult":
        return cls(is_valid=True, normalized=normalized)

    @classmethod
    def fail(cls, error: str) -> "ValidationResult":
        return cls(is_valid=False, error=error)


class OutputNameValidator:
    """Проверка имени выходного файла по формату «КВ XX В YY».

    Для нового интерфейса используется раздельный ввод квартала и выдела,
    однако старый формат строки остаётся совместимым.
    """

    EMPTY_ERROR: str = "Введите имя выходного файла"
    FORMAT_ERROR: str = "Неверный формат имени. Ожидается: «КВ XX В YY», например «КВ 18 В 12»"
    EMPTY_QUARTER_ERROR: str = "Введите номер квартала"
    EMPTY_COMPARTMENT_ERROR: str = "Введите номер выдела"
    DIGITS_ERROR: str = "Квартал и выдел должны быть указаны цифрами"

    @classmethod
    def validate(cls, raw_value: str | None) -> ValidationResult:
        """Проверяет и нормализует имя выходного файла из старой строки."""
        value = (raw_value or "").strip()
        if not value:
            return ValidationResult.fail(cls.EMPTY_ERROR)

        match: re.Match[str] | None = OUTPUT_NAME_PATTERN.match(value)
        if match is None:
            return ValidationResult.fail(cls.FORMAT_ERROR)

        quarter, compartment = match.group(1), match.group(2)
        normalized = f"КВ {quarter} В {compartment}"
        return ValidationResult.ok(normalized)

    @classmethod
    def validate_parts(cls, quarter_raw: str | None, compartment_raw: str | None) -> ValidationResult:
        """Проверяет и нормализует имя выходного файла из квартала и выдела."""
        quarter = (quarter_raw or "").strip()
        compartment = (compartment_raw or "").strip()

        if not quarter:
            return ValidationResult.fail(cls.EMPTY_QUARTER_ERROR)
        if not compartment:
            return ValidationResult.fail(cls.EMPTY_COMPARTMENT_ERROR)
        if not quarter.isdigit() or not compartment.isdigit():
            return ValidationResult.fail(cls.DIGITS_ERROR)

        normalized = f"КВ {quarter} В {compartment}"
        return ValidationResult.ok(normalized)


class PathValidator:
    """Проверка путей файловой системы, участвующих в конвертации."""

    @staticmethod
    def validate_zip_path(path: Path | None) -> ValidationResult:
        """Проверяет, что выбранный файл — существующий ZIP-архив."""
        if path is None:
            return ValidationResult.fail("Выберите ZIP-файл с выпиской ГЛР")
        if not path.exists():
            return ValidationResult.fail(f"Файл не найден: {path}")
        if not path.is_file():
            return ValidationResult.fail(f"Указанный путь не является файлом: {path}")
        if path.suffix.lower() != ZIP_EXTENSION:
            return ValidationResult.fail("Выбранный файл не является ZIP-архивом")
        return ValidationResult.ok(str(path))

    @staticmethod
    def validate_output_dir(path: Path | None) -> ValidationResult:
        """Проверяет, что выбрана существующая директория сохранения."""
        if path is None:
            return ValidationResult.fail("Выберите папку для сохранения результата")
        if not path.exists():
            return ValidationResult.fail(f"Папка не существует: {path}")
        if not path.is_dir():
            return ValidationResult.fail(f"Указанный путь не является папкой: {path}")
        return ValidationResult.ok(str(path))
