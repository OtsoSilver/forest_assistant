"""Центр уведомлений — красивые всплывающие сообщения внутри интерфейса.

Реализует контракт :class:`core.context.NotificationService`. Все
сообщения приложения выводятся только в интерфейсе — ни ``print``,
ни консоль для взаимодействия с пользователем не используются.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum, auto

import flet as ft

from core.logging_config import get_logger
from core.theme import AppPalette, ThemeController

logger = get_logger(__name__)


class _NotificationKind(Enum):
    SUCCESS = auto()
    ERROR = auto()
    INFO = auto()


class NotificationCenter:
    """Показывает плавающие уведомления (snackbar) в фирменном стиле."""

    _DURATION_MS: int = 6000

    def __init__(self, page: ft.Page, theme: ThemeController) -> None:
        self._page = page
        self._theme = theme
        self._history: list[dict[str, str]] = []

    # ------------------------------------------------------------------
    # Контракт NotificationService
    # ------------------------------------------------------------------

    def show_success(self, title: str, message: str | None = None) -> None:
        """Уведомление об успешном завершении операции."""
        self._show(_NotificationKind.SUCCESS, title, message)

    def show_error(self, title: str, message: str | None = None) -> None:
        """Уведомление об ошибке."""
        self._show(_NotificationKind.ERROR, title, message)

    def show_info(self, title: str, message: str | None = None) -> None:
        """Информационное уведомление."""
        self._show(_NotificationKind.INFO, title, message)

    # ------------------------------------------------------------------
    # Построение
    # ------------------------------------------------------------------

    def _show(self, kind: _NotificationKind, title: str, message: str | None) -> None:
        palette = self._theme.palette
        background, foreground, border, icon = self._style_for(kind, palette)
        self._history.append(
            {
                "kind": kind.name,
                "title": title,
                "message": message or "",
                "time": datetime.now().strftime("%H:%M:%S"),
            }
        )

        texts: list[ft.Control] = [
            ft.Text(
                title,
                size=13.5,
                weight=ft.FontWeight.W_600,
                color=foreground,
            )
        ]
        if message:
            texts.append(
                ft.Text(
                    message,
                    size=12.5,
                    color=foreground,
                    selectable=True,
                    max_lines=4,
                    overflow=ft.TextOverflow.ELLIPSIS,
                )
            )

        snackbar = ft.SnackBar(
            content=ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(icon, size=22, color=foreground),
                    ft.Column(spacing=2, tight=True, expand=True, controls=texts),
                ],
            ),
            behavior=ft.SnackBarBehavior.FLOATING,
            bgcolor=background,
            shape=ft.RoundedRectangleBorder(
                radius=14,
                side=ft.BorderSide(1, border),
            ),
            margin=ft.Margin.all(18),
            padding=ft.Padding.symmetric(horizontal=18, vertical=14),
            width=460,
            elevation=8,
            show_close_icon=True,
            close_icon_color=foreground,
            duration=self._DURATION_MS,
        )
        try:
            self._page.show_snack_bar(snackbar)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Не удалось показать snackbar уведомления: %s", exc)
            try:
                self._page.snack_bar = snackbar
                self._page.update()
            except Exception as fallback_exc:  # noqa: BLE001
                logger.debug("Не удалось обновить snackbar: %s", fallback_exc)

    def show_history(self) -> None:
        """Показывает список всех уведомлений за текущую сессию."""
        palette = self._theme.palette
        if not self._history:
            entries = [
                ft.Text(
                    "Уведомлений ещё не было",
                    size=13,
                    color=palette.text_secondary,
                )
            ]
        else:
            entries = []
            for item in self._history:
                kind_value = item["kind"]
                icon_name = {
                    "SUCCESS": ft.Icons.CHECK_CIRCLE,
                    "ERROR": ft.Icons.ERROR_OUTLINE,
                    "INFO": ft.Icons.INFO_OUTLINE,
                }.get(kind_value, ft.Icons.NOTIFICATIONS)
                entries.append(
                    ft.Container(
                        width=460,
                        padding=ft.Padding.symmetric(vertical=6),
                        content=ft.Row(
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                            controls=[
                                ft.Icon(icon_name, color=palette.accent),
                                ft.Column(
                                    spacing=2,
                                    tight=True,
                                    expand=True,
                                    controls=[
                                        ft.Text(
                                            f"{item['time']} · {item['title']}",
                                            size=13,
                                            weight=ft.FontWeight.W_600,
                                            color=palette.text_primary,
                                        ),
                                        ft.Text(
                                            item["message"] or "—",
                                            size=12.5,
                                            color=palette.text_secondary,
                                            selectable=True,
                                            max_lines=4,
                                            overflow=ft.TextOverflow.ELLIPSIS,
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    )
                )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Уведомления за сессию", size=18, weight=ft.FontWeight.W_600),
            content=ft.Column(
                width=500,
                spacing=6,
                controls=[
                    ft.Container(
                        height=420,
                        content=ft.Column(
                            spacing=6,
                            scroll=ft.ScrollMode.AUTO,
                            controls=entries,
                        ),
                    )
                ],
            ),
            actions=[
                ft.TextButton("Закрыть", on_click=lambda _: self._close_dialog_safely()),
            ],
        )
        self._open_dialog(dialog)

    def _open_dialog(self, dialog: ft.AlertDialog) -> None:
        """Открывает диалог безопасно и без падений при повторном вызове."""
        try:
            self._close_dialog_safely()
            self._page.dialog = dialog
            dialog.open = True
            self._page.update()
        except Exception as exc:  # noqa: BLE001
            logger.debug("Не удалось открыть диалог уведомлений: %s", exc)
            try:
                self._page.dialog = dialog
                dialog.open = True
                self._page.update()
            except Exception as fallback_exc:  # noqa: BLE001
                logger.debug("Не удалось открыть диалог уведомлений после повторной попытки: %s", fallback_exc)

    def _close_dialog_safely(self) -> None:
        """Закрывает текущий диалог, если он открыт, не роняя интерфейс."""
        try:
            current_dialog = getattr(self._page, "dialog", None)
            if current_dialog is None:
                return
            if hasattr(current_dialog, "open"):
                current_dialog.open = False
            if hasattr(self._page, "close_dialog"):
                self._page.close_dialog()
            self._page.update()
        except Exception as exc:  # noqa: BLE001
            logger.debug("Не удалось закрыть диалог уведомлений: %s", exc)
            try:
                self._page.dialog = None
                self._page.update()
            except Exception as fallback_exc:  # noqa: BLE001
                logger.debug("Не удалось очистить состояние диалога: %s", fallback_exc)

    @staticmethod
    def _style_for(
        kind: _NotificationKind, palette: AppPalette
    ) -> tuple[str, str, str, str]:
        """Возвращает (фон, текст, граница, иконка) для вида уведомления."""
        match kind:
            case _NotificationKind.SUCCESS:
                return (
                    palette.success_bg,
                    palette.success_fg,
                    palette.success_border,
                    ft.Icons.CHECK_CIRCLE,
                )
            case _NotificationKind.ERROR:
                return (
                    palette.error_bg,
                    palette.error_fg,
                    palette.error_border,
                    ft.Icons.ERROR_OUTLINE,
                )
            case _:
                return (
                    palette.info_bg,
                    palette.info_fg,
                    palette.info_border,
                    ft.Icons.INFO_OUTLINE,
                )
