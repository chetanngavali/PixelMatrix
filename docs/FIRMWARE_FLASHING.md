# Firmware Flashing Guide: Pre-Compiled Release Binaries

This guide explains how to flash the pre-compiled **ESP8266 PixelMatrix 200** binaries onto your **ESP8266 12E NodeMCU** without installing compiler toolchains, C++ libraries, or PlatformIO.

---

## 1. Release Files in [`bin/`](../bin/)

| File | Offset | Size | Description |
| :--- | :--- | :--- | :--- |
| **`merged_firmware_4mb.bin`** | **`0x00000`** | 4,194,304 B (4 MB) | **Recommended**: Complete all-in-one image containing both the FastLED firmware and the LittleFS web dashboard in a single file. |
| **`firmware.bin`** | **`0x00000`** | ~524 KB | Standalone firmware code (FastLED engine, Wi-Fi, REST API, WebSocket server). |
| **`littlefs.bin`** | **`0x300000`** | 1,024,000 B (1 MB) | Standalone filesystem image containing the web dashboard (`index.html`, `style.css`, `app.js`). |

---

## 2. Method 1: 1-Click Scripts (Easiest)

1. Connect your ESP8266 NodeMCU to your computer via USB.
2. Open the `bin/` directory.
3. Launch the script:
   - **Windows**: Double-click [`flash_windows.bat`](../bin/flash_windows.bat).
     - It will prompt you for your COM port (e.g. `COM6`), then automatically flash `merged_firmware_4mb.bin`.
   - **Linux / macOS**: Open terminal in `bin/` and run:
     ```bash
     chmod +x flash_linux_mac.sh
     ./flash_linux_mac.sh
     ```

---

## 3. Method 2: In-Browser Web Flasher (No Software Required)

You can flash directly from any Chromium-based web browser (Google Chrome, Microsoft Edge, Opera, Brave) using WebSerial:

1. Connect your NodeMCU to your computer with a micro-USB data cable.
2. Open [Adafruit WebSerial ESPTool](https://adafruit.github.io/Adafruit_WebSerial_ESPTool/) or [ESP Web Flasher](https://esp.rainmaker.espressif.com/).
3. Click **Connect** and select your USB serial device (`USB-SERIAL CH340` or `CP2102 USB to UART`).
4. Set Baud Rate to **460800**.
5. Under **Flash Files**:
   - **File 1**: Choose `bin/merged_firmware_4mb.bin`
   - **Offset**: `0x00000`
6. Click **Program / Write Flash**.
7. Once 100% complete, press the physical **RST** button on the NodeMCU.

---

## 4. Method 3: Command Line (`esptool.py`)

If you have Python installed, you can flash using the official Espressif `esptool`:

```bash
# Install esptool if not already installed
pip install esptool

# Flash the all-in-one 4MB bundle
esptool.py --chip esp8266 --port COM6 --baud 460800 write_flash 0x00000 bin/merged_firmware_4mb.bin
```

*(If flashing the two files separately instead of the merged binary:)*
```bash
esptool.py --chip esp8266 --port COM6 --baud 460800 write_flash 0x00000 bin/firmware.bin 0x300000 bin/littlefs.bin
```

---

## 5. Method 4: NodeMCU PyFlasher / ESP Flash Tool (GUI)

1. Download [NodeMCU PyFlasher](https://github.com/marcelstoer/nodemcu-pyflasher/releases).
2. Select your Serial Port.
3. Browse to `bin/merged_firmware_4mb.bin`.
4. Set Baud rate to **460800**.
5. Flash mode: **Dual Output (DIO)**.
6. Click **Flash NodeMCU**.

---

## 6. Verifying Operation After Flashing

1. Open any Serial Monitor program (PuTTY, Arduino Serial Monitor, or Termite) set to **115200 baud**.
2. Press the **RST** button on the NodeMCU.
3. You will see the boot banner:
   ```text
   ============================================================
         ESP8266 12E NodeMCU - PixelMatrix 200 Controller      
   ============================================================
   [INIT] Initializing FastLED Controller (Direct GPIO 5)...
   [BOOT] Running First-Boot Sanity Check (RGBW Sequence)...
   [INIT] Starting Web Server & REST API...
   [FS] LittleFS mounted successfully.
   [READY] ESP8266 PixelMatrix 200 is fully operational!
   ```
4. The 200 LEDs will execute the safe RGBW sanity check (Red $\rightarrow$ Green $\rightarrow$ Blue $\rightarrow$ White $\rightarrow$ Off).
5. If Wi-Fi is not yet configured, the board automatically launches access point:
   - **SSID:** `PixelMatrix-Setup`
   - **Password:** `pixel1234`
   - **Dashboard URL:** `http://192.168.4.1`
