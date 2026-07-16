@echo off
setlocal
cd /d "%~dp0"

set PYTHON_CMD="%~dp0.venv\Scripts\python.exe"
if not exist "%~dp0.venv\Scripts\python.exe" (
    echo Python environment not found. Create it first: py -m venv .venv
    exit /b 1
)

echo Installing build dependencies...
%PYTHON_CMD% -m pip install --upgrade pip pyinstaller

echo Building executable...
%PYTHON_CMD% -m PyInstaller --noconfirm --clean --distpath "dist" --workpath "build" forest_assistant.spec

echo.
echo Build finished.
echo Output: %~dp0dist\forest_assistant\forest_assistant.exe
endlocal
