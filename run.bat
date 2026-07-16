@echo off
rem ==================================================================
rem  Лесной помощник — запуск приложения (Windows)
rem ==================================================================
chcp 65001 >nul
cd /d "%~dp0"

rem Приоритет — локальное виртуальное окружение проекта.
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py
) else (
    python main.py
)

if errorlevel 1 (
    echo.
    echo Приложение завершилось с ошибкой. Подробности — в папке logs.
    pause
)
