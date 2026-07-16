"""Конвертер выписок ГЛР → GPX — ТОЧКА ИНТЕГРАЦИИ СУЩЕСТВУЮЩЕГО АЛГОРИТМА.

╔══════════════════════════════════════════════════════════════════════════╗
║  СЮДА ПОДКЛЮЧАЕТСЯ ВАШ СУЩЕСТВУЮЩИЙ АЛГОРИТМ КОНВЕРТАЦИИ.               ║
║  Сам алгоритм НЕ переписывается, НЕ изменяется и НЕ переносится в UI.   ║
╚══════════════════════════════════════════════════════════════════════════╝

Поддерживаются два способа интеграции — выберите один:

СПОСОБ А (рекомендуемый) — существующий модуль остаётся отдельным файлом:
  1. Скопируйте ваш существующий файл с алгоритмом в папку ``services/``
     под именем ``glr_legacy.py`` (файл НЕ редактируйте).
  2. Убедитесь, что в нём есть функция, принимающая путь к ZIP и путь к
     выходному GPX, например ``convert(zip_path, output_path)``.
     Поддерживаемые имена точки входа перечислены в ``ENTRY_POINT_NAMES``
     ниже (``convert``, ``convert_zip_to_gpx``, ``main``, ``run``, ``process``).
  3. Больше ничего делать не нужно: адаптер :class:`GlrToGpxAlgorithm`
     найдёт модуль и вызовет его автоматически.

СПОСОБ Б — код алгоритма вставляется прямо в этот файл:
  1. Вставьте ваш существующий код в самый низ файла, ВНИЗ по ходу файла,
     в область после маркера ``# ===== ВАШ СУЩЕСТВУЮЩИЙ КОД =====``.
  2. Оставьте (или добавьте) тонкую функцию-обёртку с сигнатурой::

         def legacy_convert(zip_path: str, output_path: str) -> str | None:
             ...

     Адаптер обнаружит её в этом модуле автоматически.

Контракт точки входа (для обоих способов):
  * аргумент 1 — путь к входному ZIP-архиву (строка);
  * аргумент 2 — полный путь к выходному GPX-файлу (строка);
  * возврат — путь к созданному файлу (строка) либо ``None``, если алгоритм
    сам записывает файл по переданному второму аргументу.

Если сигнатура вашего алгоритма другая — измените ТОЛЬКО метод
:meth:`GlrToGpxAlgorithm._call_entry_point`: это единственное место,
где допускается «клей» между приложением и алгоритмом.
"""

from __future__ import annotations

import importlib
import inspect
import time
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

from core.logging_config import get_logger
from models.conversion import AlgorithmExecutionError, AlgorithmNotIntegratedError

logger = get_logger(__name__)

#: Имя модуля в папке ``services/``, куда помещается существующий алгоритм
#: при интеграции способом А (см. документацию модуля выше).
LEGACY_MODULE_NAME: str = "services.glr_legacy"

#: Допустимые имена функции-точки входа в модуле алгоритма.
ENTRY_POINT_NAMES: tuple[str, ...] = (
    "convert",
    "convert_zip_to_gpx",
    "convert_glr_to_gpx",
    "main",
    "run",
    "process",
)

#: Имя функции-обёртки для интеграции способом Б (код вставлен в этот файл).
LOCAL_WRAPPER_NAME: str = "legacy_convert"

#: Инструкция, отображаемая пользователю, если алгоритм ещё не подключён.
_NOT_INTEGRATED_MESSAGE: str = (
    "Алгоритм конвертации ещё не подключён. Поместите существующий модуль "
    "в папку services/ под именем glr_legacy.py — см. инструкцию в начале "
    "файла services/glr_converter.py."
)


class GlrToGpxAlgorithm:
    """Адаптер единого вызова существующего алгоритма конвертации.

    Инкапсулирует обнаружение и вызов подключённого модуля, изолируя
    остальное приложение от деталей его внутреннего устройства.
    Объект без состояния — потокобезопасен при параллельных вызовах.
    """

    def convert(self, zip_path: Path, output_file: Path) -> Path:
        """Выполняет конвертацию ZIP-архива выписки ГЛР в GPX-файл.

        Args:
            zip_path: Путь к входному ZIP-архиву (существование проверено
                на уровне сервиса-оркестратора).
            output_file: Полный путь к выходному GPX-файлу.

        Returns:
            Путь к фактически созданному GPX-файлу.

        Raises:
            AlgorithmNotIntegratedError: Алгоритм не подключён.
            AlgorithmExecutionError: Алгоритм завершился с исключением
                или не создал выходной файл.
        """
        entry_point = self._resolve_entry_point()
        result = self._call_entry_point(entry_point, zip_path, output_file)
        return self._resolve_output_file(result, output_file)

    # ------------------------------------------------------------------
    # Обнаружение алгоритма
    # ------------------------------------------------------------------

    def _resolve_entry_point(self) -> Callable[..., object]:
        """Ищет подключённый алгоритм: сначала локально, затем модулем.

        Returns:
            Вызываемая точка входа алгоритма.

        Raises:
            AlgorithmNotIntegratedError: Алгоритм нигде не найден.
        """
        # Способ Б: функция-обёртка legacy_convert определена в ЭТОМ файле
        # (ниже маркера «ВАШ СУЩЕСТВУЮЩИЙ КОД»).
        local_wrapper = globals().get(LOCAL_WRAPPER_NAME)
        if callable(local_wrapper):
            logger.debug("Алгоритм найден: локальная функция %s()", LOCAL_WRAPPER_NAME)
            return local_wrapper

        # Способ А: отдельный модуль services/glr_legacy.py.
        module = self._try_import_legacy_module()
        if module is not None:
            for name in ENTRY_POINT_NAMES:
                candidate = getattr(module, name, None)
                if callable(candidate):
                    logger.debug("Алгоритм найден: %s.%s()", LEGACY_MODULE_NAME, name)
                    return candidate
            raise AlgorithmNotIntegratedError(
                user_message=(
                    f"Модуль {LEGACY_MODULE_NAME.split('.')[-1]}.py найден, но в нём нет "
                    f"ни одной из поддерживаемых функций: {', '.join(ENTRY_POINT_NAMES)}. "
                    "Добавьте функцию convert(zip_path, output_path) или поправьте "
                    "метод _call_entry_point в services/glr_converter.py."
                ),
                technical_details=f"В модуле {module.__file__} нет точек входа {ENTRY_POINT_NAMES}",
            )

        raise AlgorithmNotIntegratedError(
            user_message=_NOT_INTEGRATED_MESSAGE,
            technical_details="Ни локальная обёртка, ни модуль glr_legacy не обнаружены",
        )

    @staticmethod
    def _try_import_legacy_module() -> ModuleType | None:
        """Импортирует модуль существующего алгоритма, если он подключён."""
        try:
            return importlib.import_module(LEGACY_MODULE_NAME)
        except ModuleNotFoundError:
            return None

    # ------------------------------------------------------------------
    # Вызов алгоритма
    # ------------------------------------------------------------------

    def _call_entry_point(
        self,
        entry_point: Callable[..., object],
        zip_path: Path,
        output_file: Path,
    ) -> object:
        """Вызывает точку входа алгоритма и упаковывает любые сбои.

        ════════════════════════════════════════════════════════════════════
        ЕДИНСТВЕННОЕ МЕСТО, где допустимо адаптировать вызов под сигнатуру
        вашего существующего алгоритма (если она отличается от контракта
        ``entry_point(zip_path: str, output_path: str) -> str | None``).
        ════════════════════════════════════════════════════════════════════
        """
        logger.info("Запуск алгоритма конвертации: %s → %s", zip_path, output_file)
        start = time.monotonic()
        try:
            self._log_signature(entry_point)
            result = entry_point(str(zip_path), str(output_file))
        except AlgorithmExecutionError:
            raise
        except Exception as exc:  # noqa: BLE001 — любое исключение алгоритма упаковываем
            logger.exception("Исключение внутри алгоритма конвертации")
            raise AlgorithmExecutionError(
                user_message=f"Алгоритм конвертации завершился с ошибкой: {exc}",
                technical_details=f"{type(exc).__name__}: {exc}",
            ) from exc

        elapsed = time.monotonic() - start
        logger.info("Алгоритм конвертации завершил работу за %.2f с", elapsed)
        return result

    # ------------------------------------------------------------------
    # Результат
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_output_file(result: object, expected: Path) -> Path:
        """Определяет фактический путь результата и проверяет его наличие."""
        output_file = Path(result) if isinstance(result, (str, Path)) and str(result) else expected
        if not output_file.exists():
            raise AlgorithmExecutionError(
                user_message=(
                    "Алгоритм завершил работу, но выходной файл не был создан: "
                    f"{output_file}"
                ),
                technical_details=f"Ожидался файл {output_file}, вернулось значение {result!r}",
            )
        return output_file

    @staticmethod
    def _log_signature(entry_point: Callable[..., object]) -> None:
        """Фиксирует сигнатуру точки входа в журнале (помогает интеграции)."""
        try:
            signature = inspect.signature(entry_point)
        except (TypeError, ValueError):
            return
        logger.debug("Сигнатура точки входа алгоритма: %s%s", entry_point.__name__, signature)


# ============================================================================
# ===== ВАШ СУЩЕСТВУЮЩИЙ КОД (способ Б — вставляйте ниже этой строки) ========
# ============================================================================
#
# Пример обёртки (удалите комментарии и подставьте вызов вашего кода):
#
# def legacy_convert(zip_path: str, output_path: str) -> str | None:
#     """Тонкая обёртка над существующим алгоритмом."""
#     # ... ваш существующий код конвертации ...
#     return output_path
