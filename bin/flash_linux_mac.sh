#!/usr/bin/env bash
set -e

echo "============================================================"
echo "   ESP8266 PixelMatrix 200 - Auto-Installer & Flasher (Linux/macOS)  "
echo "============================================================"
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
BIN_PATH="$SCRIPT_DIR/merged_firmware_4mb.bin"

# ------------------------------------------------------------
# STEP 1: Verify Binary Files Exist
# ------------------------------------------------------------
if [ ! -f "$BIN_PATH" ]; then
    echo "[!] merged_firmware_4mb.bin not found in $SCRIPT_DIR"
    if [ -f "$SCRIPT_DIR/firmware.bin" ] && [ -f "$SCRIPT_DIR/littlefs.bin" ]; then
        echo "[*] Found firmware.bin and littlefs.bin. Will flash dual-file mode."
        DUAL_MODE=1
    else
        echo "[ERROR] Release binaries are missing from the bin/ directory!"
        echo "Please ensure you cloned the full repository or downloaded the release files."
        exit 1
    fi
else
    DUAL_MODE=0
fi

# ------------------------------------------------------------
# STEP 2: Check & Install Python 3
# ------------------------------------------------------------
echo "[1/4] Checking Python 3 installation..."
if ! command -v python3 &> /dev/null; then
    echo "[!] Python 3 is not installed. Attempting auto-install..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y python3 python3-pip
    elif command -v pacman &> /dev/null; then
        sudo pacman -Sy --noconfirm python python-pip
    elif command -v brew &> /dev/null; then
        brew install python
    else
        echo "[ERROR] Could not auto-install Python 3. Please install Python 3 manually."
        exit 1
    fi
fi
echo "  -> Python 3 is ready: $(python3 --version)"

# ------------------------------------------------------------
# STEP 3: Check & Install esptool
# ------------------------------------------------------------
echo "[2/4] Checking esptool utility..."
ESPTOOL_CMD=""

if command -v esptool.py &> /dev/null; then
    ESPTOOL_CMD="esptool.py"
elif python3 -m esptool version &> /dev/null; then
    ESPTOOL_CMD="python3 -m esptool"
else
    echo "[!] esptool not found. Installing via pip..."
    # Attempt installation with or without --break-system-packages (for newer PEP 668 distros)
    python3 -m pip install --upgrade esptool --break-system-packages 2>/dev/null || \
    python3 -m pip install --user --upgrade esptool 2>/dev/null || \
    pip3 install --upgrade esptool 2>/dev/null || true

    if python3 -m esptool version &> /dev/null; then
        ESPTOOL_CMD="python3 -m esptool"
    elif command -v esptool.py &> /dev/null; then
        ESPTOOL_CMD="esptool.py"
    else
        echo "[ERROR] Failed to install esptool automatically."
        echo "Please run: pip install esptool"
        exit 1
    fi
fi
echo "  -> esptool is ready."

# ------------------------------------------------------------
# STEP 4: Auto-Detect Connected ESP8266 Serial Port
# ------------------------------------------------------------
echo "[3/4] Detecting connected ESP8266 serial ports..."
DETECTED_PORT=""

# Look for standard Linux USB-serial adapters (CH340, CP2102, FTDI)
for port in /dev/ttyUSB* /dev/ttyACM* /dev/cu.usbserial* /dev/cu.wchusbserial* /dev/cu.SLAB_USBtoUART*; do
    if [ -e "$port" ]; then
        DETECTED_PORT="$port"
        break
    fi
done

if [ -n "$DETECTED_PORT" ]; then
    echo "  -> Found device on: $DETECTED_PORT"
    read -p "Use port [$DETECTED_PORT] (Press Enter) or type another port: " USER_PORT
    PORT="${USER_PORT:-$DETECTED_PORT}"
else
    echo "  -> No port auto-detected. Defaulting to /dev/ttyUSB0."
    read -p "Enter ESP8266 serial port (e.g. /dev/ttyUSB0): " USER_PORT
    PORT="${USER_PORT:-/dev/ttyUSB0}"
fi

# Linux dialout permission check
if [[ "$OSTYPE" == "linux-gnu"* ]] && [ -e "$PORT" ] && [ ! -w "$PORT" ]; then
    echo "[!] You do not have write permissions for $PORT."
    echo "[*] Temporarily granting access with sudo chmod 666..."
    sudo chmod 666 "$PORT" || {
        echo "[TIP] To permanently fix permissions, run: sudo usermod -a -G dialout $USER"
    }
fi

# ------------------------------------------------------------
# STEP 5: Flash Binaries to ESP8266
# ------------------------------------------------------------
echo ""
echo "[4/4] Flashing ESP8266 on $PORT at 460800 baud..."

FLASH_SUCCESS=0

if [ "$DUAL_MODE" -eq 1 ]; then
    echo "Writing firmware (0x0) and LittleFS (0x300000)..."
    if $ESPTOOL_CMD --chip esp8266 --port "$PORT" --baud 460800 write-flash 0x00000 "$SCRIPT_DIR/firmware.bin" 0x300000 "$SCRIPT_DIR/littlefs.bin"; then
        FLASH_SUCCESS=1
    else
        echo "[!] High-speed flash failed. Retrying at 115200 baud..."
        if $ESPTOOL_CMD --chip esp8266 --port "$PORT" --baud 115200 write-flash 0x00000 "$SCRIPT_DIR/firmware.bin" 0x300000 "$SCRIPT_DIR/littlefs.bin"; then
            FLASH_SUCCESS=1
        fi
    fi
else
    echo "Writing merged_firmware_4mb.bin (0x0)..."
    if $ESPTOOL_CMD --chip esp8266 --port "$PORT" --baud 460800 write-flash 0x00000 "$BIN_PATH"; then
        FLASH_SUCCESS=1
    else
        echo "[!] High-speed flash failed. Retrying at 115200 baud..."
        if $ESPTOOL_CMD --chip esp8266 --port "$PORT" --baud 115200 write-flash 0x00000 "$BIN_PATH"; then
            FLASH_SUCCESS=1
        fi
    fi
fi

echo ""
if [ "$FLASH_SUCCESS" -eq 1 ]; then
    echo "============================================================"
    echo " [SUCCESS] Flashing complete!"
    echo " Please press the physical RST button on your NodeMCU board."
    echo " Connect to Wi-Fi 'PixelMatrix-Setup' (Password: pixel1234)"
    echo " and open http://192.168.4.1 in your browser."
    echo "============================================================"
else
    echo "============================================================"
    echo " [ERROR] Flashing failed!"
    echo " Please check your USB cable, hold down the FLASH button"
    echo " while starting the script, and try again."
    echo "============================================================"
    exit 1
fi
