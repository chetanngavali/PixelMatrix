@echo off
setlocal

echo ============================================================
echo   ESP8266 PixelMatrix 200 - Auto-Installer and Flasher
echo   Developed by Chetan Ngavali [@chetanngavali]
echo ============================================================
echo.

:: ------------------------------------------------------------
:: STEP 1: Verify Release Binaries
:: ------------------------------------------------------------
set "BIN_DIR=%~dp0"
set "MERGED_BIN=%BIN_DIR%merged_firmware_4mb.bin"
set "FW_BIN=%BIN_DIR%firmware.bin"
set "FS_BIN=%BIN_DIR%littlefs.bin"
set "DUAL_MODE=0"

if exist "%MERGED_BIN%" goto :bin_ok
if exist "%FW_BIN%" if exist "%FS_BIN%" (
    echo [*] Found firmware.bin and littlefs.bin. Using dual-file mode.
    set "DUAL_MODE=1"
    goto :bin_ok
)

echo [ERROR] Required binary files are missing from: %BIN_DIR%
echo Please ensure you have downloaded the release files.
echo.
pause
exit /b 1

:bin_ok

:: ------------------------------------------------------------
:: STEP 2: Check Python and esptool
:: ------------------------------------------------------------
echo [1/3] Checking Python 3 environment...
python --version >nul 2>&1
if errorlevel 1 goto :no_python
goto :check_esptool

:no_python
echo [!] Python is not installed or not in your system PATH.
echo.
echo Launching WebSerial in-browser flasher [Zero-Install alternative]...
start https://adafruit.github.io/Adafruit_WebSerial_ESPTool/
echo.
echo You can flash merged_firmware_4mb.bin directly in your web browser.
pause
exit /b 1

:check_esptool
echo [2/3] Checking esptool utility...
python -m esptool version >nul 2>&1
if errorlevel 1 goto :install_esptool
echo   - esptool is installed and ready.
goto :prompt_port

:install_esptool
echo [!] esptool not detected. Auto-installing now via pip...
python -m pip install --upgrade esptool
if errorlevel 1 (
    echo [ERROR] Failed to install esptool via pip.
    pause
    exit /b 1
)
echo   - esptool has been installed successfully.

:prompt_port
:: ------------------------------------------------------------
:: STEP 3: Prompt for COM Port
:: ------------------------------------------------------------
echo.
echo [3/3] Target Serial Port Configuration:
set /p PORT="Enter your ESP8266 COM Port [default: COM6]: "
if "%PORT%"=="" set PORT=COM6
echo   - Selected port: %PORT%
echo.

:: ------------------------------------------------------------
:: STEP 4: Flash Binaries to ESP8266
:: ------------------------------------------------------------
echo [FLASH] Writing to ESP8266 on %PORT% at 460800 baud...
echo.

if "%DUAL_MODE%"=="1" (
    python -m esptool --chip esp8266 --port %PORT% --baud 460800 write-flash 0x00000 "%FW_BIN%" 0x300000 "%FS_BIN%"
    if errorlevel 1 (
        echo.
        echo [WARNING] High-speed flash failed. Retrying at 115200 baud...
        python -m esptool --chip esp8266 --port %PORT% --baud 115200 write-flash 0x00000 "%FW_BIN%" 0x300000 "%FS_BIN%"
    )
) else (
    python -m esptool --chip esp8266 --port %PORT% --baud 460800 write-flash 0x00000 "%MERGED_BIN%"
    if errorlevel 1 (
        echo.
        echo [WARNING] High-speed flash failed. Retrying at 115200 baud...
        python -m esptool --chip esp8266 --port %PORT% --baud 115200 write-flash 0x00000 "%MERGED_BIN%"
    )
)

if errorlevel 1 goto :flash_fail

echo.
echo ============================================================
echo [SUCCESS] Flashing completed successfully!
echo Please press the physical RST button on your NodeMCU board.
echo Connect to Wi-Fi 'PixelMatrix-Setup' [Password: pixel1234]
echo and open http://192.168.4.1 in your browser.
echo ============================================================
goto :end

:flash_fail
echo.
echo ============================================================
echo [ERROR] Flashing failed!
echo 1. Check your micro-USB cable [must support data, not charge-only].
echo 2. Ensure no other application [PuTTY, Arduino IDE] is using %PORT%.
echo 3. Hold down the physical FLASH button on the board while starting.
echo ============================================================

:end
echo.
pause
