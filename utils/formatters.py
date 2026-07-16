"""Форматирование значений для отображения в интерфейсе."""

from __future__ import annotations

#: Единицы измерения размера файла (русская локаль).
_SIZE_UNITS: tuple[str, ...] = ("Б", "КБ", "МБ", "ГБ", "ТБ")


def format_file_size(num_bytes: int | None) -> str:
    """Преобразует размер в байтах в читаемую строку.

    Примеры::

        format_file_size(512)       -> "512 Б"
        format_file_size(2_400_000) -> "2,3 МБ"
        format_file_size(None)      -> "—"

    Args:
        num_bytes: Размер в байтах или ``None``, если размер неизвестен.

    Returns:
        Отформатированная строка с русской единицей измерения.
    """
    if num_bytes is None or num_bytes < 0:
        return "—"

    size = float(num_bytes)
    for unit in _SIZE_UNITS:
        if size < 1024.0 or unit == _SIZE_UNITS[-1]:
            if unit == "Б":
                return f"{int(size)} {unit}"
            formatted = f"{size:.1f}".rstrip("0").rstrip(".")
            # Десятичный разделитель в русской локали — запятая.
            return f"{formatted.replace('.', ',')} {unit}"
        size /= 1024.0
    return f"{num_bytes} Б"  # недостижимо, оставлено для полноты типов


def format_duration(seconds: float) -> str:
    """Форматирует длительность операции в читаемый вид.

    Примеры::

        format_duration(0.42)  -> "0,4 с"
        format_duration(75.0)  -> "1 мин 15 с"
    """
    if seconds < 60:
        return f"{seconds:.1f}".replace(".", ",") + " с"
    minutes, rest = divmod(int(round(seconds)), 60)
    return f"{minutes} мин {rest} с"
