@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo   PixelMatrix Screen Sync - Desktop App Launcher
echo   Developed by Chetan Gavali [@chetanngavali]
echo ============================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%.."
set "REQ_FILE=%ROOT_DIR%\desktop\requirements.txt"
set "MAIN_SCRIPT=%ROOT_DIR%\desktop\main.py"

:: ------------------------------------------------------------
:: 1. Verify Python Installation
:: ------------------------------------------------------------
echo [1/3] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in your system PATH.
    echo Please install Python 3.10 or higher from https://python.org
    echo and ensure "Add Python to PATH" is checked during setup.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do echo   - Found: %%i

:: ------------------------------------------------------------
:: 2. Auto-Install / Verify Requirements
:: ------------------------------------------------------------
echo.
echo [2/3] Checking and installing Python dependencies...
if not exist "%REQ_FILE%" (
    echo [ERROR] Cannot find requirements file: %REQ_FILE%
    pause
    exit /b 1
)

python -m pip install -r "%REQ_FILE%"
if errorlevel 1 (
    echo.
    echo [WARNING] pip install encountered an issue. Retrying with --user flag...
    python -m pip install --user -r "%REQ_FILE%"
    if errorlevel 1 (
        echo [ERROR] Failed to install required dependencies.
        pause
        exit /b 1
    )
)
echo   - All dependencies are installed and up to date.

:: ------------------------------------------------------------
:: 3. Launch Desktop Application
:: ------------------------------------------------------------
echo.
echo [3/3] Starting PixelMatrix Screen Sync Desktop App...
echo.
if not exist "%MAIN_SCRIPT%" (
    echo [ERROR] Cannot find main script: %MAIN_SCRIPT%
    pause
    exit /b 1
)

python "%MAIN_SCRIPT%"

if errorlevel 1 (
    echo.
    echo [!] Desktop application closed with an exit code.
    pause
)
