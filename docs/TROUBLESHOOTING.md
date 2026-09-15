# Comprehensive Troubleshooting Guide: ESP8266 PixelMatrix 200

This guide covers systematic diagnostic procedures for the 15 most common real-world failure modes encountered with addressable LED installations on the **ESP8266 12E NodeMCU**.

---

## 1. No LEDs Turn On
- **Symptom:** Strip remains completely dark upon startup; first-boot RGBW sequence does not appear.
- **Root Cause & Solution:**
  1. **Check 5V Power:** Use a digital multimeter (DMM) to measure voltage directly between the strip's +5V and GND injection points. If 0V, check your PSU mains switch, DC wiring, and the 15A/20A inline fuse.
  2. **Check DIN vs. DO Connection:** Ensure the NodeMCU data wire is soldered to **DIN** (Data In), not DO (Data Out). Data can only flow in the direction of the printed arrows on the strip.
  3. **Check First-LED Failure:** If LED #1's internal IC is dead, no data passes downstream. Use Hardware Test Mode #1 or probe LED #2 DIN directly.

---

## 2. First LED Works But Others Don't
- **Symptom:** LED #1 illuminates, but LEDs #2 through #200 remain dark or frozen.
- **Root Cause & Solution:**
  1. **Dead Data Output (DO) on LED #1:** The internal driver for the DO pad on pixel #1 may be damaged by electrostatic discharge (ESD) or an inrush spike.
  2. **Defective Solder Joint between LED #1 and #2:** Inspect the microscopic solder bridge or wire between **LED #1 DO** and **LED #2 DIN**. Resolder with fresh flux.
  3. **Cut/Bypass Test:** Temporarily bypass LED #1 by moving the NodeMCU Pin D1 signal wire directly to LED #2 DIN. If LEDs #2–200 immediately light up, replace LED #1.

---

## 3. Only Some LEDs Work (Chain Stops at LED #X)
- **Symptom:** Pixels 1 through $X$ operate normally; pixels from $X+1$ to 200 are dark or frozen.
- **Diagnostic Procedure for Chain Interruption:**
  1. Focus strictly on the junction between **LED #$X$** and **LED #$X+1$**.
  2. Inspect the copper trace from **LED #$X$ DO** $\rightarrow$ **LED #$X+1$ DIN**.
  3. Check for cracked FPCB traces caused by bending or mechanical stress.
  4. Measure 5V voltage at LED #$X+1$. If power dropped out due to a broken trace, restore power injection.
  5. If voltage is 5.0V, either LED #$X$ is failing to transmit DO, or LED #$X+1$ has a blown DIN receiver. Cut out and splice in a new pixel.

---

## 4. Wrong Colors Displayed
- **Symptom:** You select Red in the web dashboard, but Green illuminates; or Blue and Green are swapped.
- **Root Cause & Solution:**
  - **Color Order Mismatch:** While WS2812B natively uses **GRB** order, older WS2811 strips or newer clones may use **RGB**, **BRG**, or **RBG**.
  - **Fix:** In `firmware/src/config.h`, update `LED_COLOR_ORDER` from `GRB` to `RGB` (or matching order) and re-flash.

---

## 5. Flickering Pixels
- **Symptom:** Rapid, erratic blinking or jittering across some or all pixels during animations.
- **Root Cause & Solution:**
  1. **Missing or Loose Common Ground:** A high-resistance GND return creates floating signal levels. Tighten all ground terminal screws.
  2. **Excessive Signal Wire Length:** Direct 3.3V logic signals degrade over long wires. If the cable between NodeMCU Pin D1 and LED #1 DIN exceeds 20 cm, trim it down to under 15 cm.
  3. **Series Resistor Missing:** High-frequency 800 kHz edges reflect off the high-impedance DIN gate. Verify a **330Ω to 470Ω resistor** is placed right at NodeMCU Pin D1.

---

## 6. Random Colors & Glitched Data Packets
- **Symptom:** Pixels display chaotic static, random white flashes, or wrong patterns.
- **Root Cause & Solution:**
  1. **Electromagnetic Interference (EMI):** Route the data wire away from 110V/220V AC mains lines, high-frequency switching power supply bricks, and inductive motors.
  2. **Wrong Pin Selected:** On NodeMCU, Pin D1 corresponds to GPIO 5. Make sure the wire is connected to physical pin **`D1`**, not D5 or D0.

---

## 7. ESP8266 Resets & Watchdog Brownouts
- **Symptom:** Serial console prints `wdt reset` or `Soft WDT reset`; device continuously boots in a loop when brightness increases.
- **Root Cause & Solution:**
  1. **Shared Power Drop:** The ESP8266 is connected to the same sagging 5V line without decoupling. When 200 LEDs turn on, the sudden 10A surge pulls the 5V line down below 3.6V, resetting the microcontroller.
  2. **Fix:** Ensure the **1000µF capacitor** is installed at the power input, and power the NodeMCU logic independently through USB or via a clean regulated step-down.

---

## 8. LED Voltage Drops (Dimming Towards End of Strip)
- **Symptom:** The start of the strip is bright white, but pixels beyond #100 become progressively dimmer, yellowish, or dull orange/red.
- **Root Cause & Solution:**
  - **Insufficient Power Injection:** Copper traces cannot deliver 12A over 3+ meters.
  - **Fix:** Connect all 5 injection taps (LED #1, #50, #100, #150, #200) to the heavy-gauge AWG 14 main power bus.

---

## 9. Power Supply Overload or Tripping
- **Symptom:** The 5V PSU clicks, whines, shuts down, or cycles power when brightness exceeds 50%.
- **Root Cause & Solution:**
  1. **Undersized PSU:** Verify your PSU is rated for at least **15A–20A (75W–100W)**. A 5A or 10A supply will trip its overcurrent protection (OCP).
  2. **Safety Throttling:** In the web dashboard Settings tab, lower **Maximum Safe Brightness** to 60% until a suitable 20A PSU is connected.

---

## 10. Wi-Fi Unavailable / Credentials Changed
- **Symptom:** Router was swapped, SSID changed, or home Wi-Fi is down; controller cannot connect.
- **Automatic Fallback Behavior:**
  - The firmware attempts connection for 15 seconds. If connection fails, it automatically boots its standalone Access Point:
    - **AP SSID:** `PixelMatrix-Setup`
    - **AP Password:** `pixel1234`
    - **Setup IP:** `http://192.168.4.1`
  - Connect your phone or laptop directly to this AP network and browse to `192.168.4.1` to enter new Wi-Fi credentials. The device never locks you out.

---

## 11. Web Dashboard Unavailable (LittleFS Missing)
- **Symptom:** Browser reaches the ESP8266 IP, but displays a plain white emergency recovery page saying *"Please upload the LittleFS data image via PlatformIO"*.
- **Fix:** You only uploaded the firmware binary, not the web dashboard filesystem. Run:
  ```powershell
  pio run -e nodemcuv2 -t uploadfs
  ```

---

## 12. USB Serial Device Not Recognized (Windows / Mac / Linux)
- **Symptom:** Running `pio device list` does not show a COM port, or Windows Device Manager shows an unknown device.
- **Root Cause & Solution:**
  - Most NodeMCU boards use either a **CH340G** or **CP2102** USB-to-UART converter chip.
  - Install the corresponding USB driver:
    - [WCH CH340 / CH341 Driver](https://www.wch-ic.com/downloads/CH341SER_EXE.html)
    - [Silicon Labs CP210x Driver](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers)

---

## 13. mDNS Name Not Resolving
- **Symptom:** `http://pixelmatrix-200.local` doesn't load, but the numerical IP address works.
- **Root Cause & Solution:**
  - Windows networks without Bonjour / Apple mDNS services sometimes fail to resolve `.local` domains.
  - Check your router client list or serial console monitor for the assigned IP address (e.g. `http://192.168.1.150`).

---

## 14. Flash Upload Errors (`esptool.FatalError: Failed to connect`)
- **Symptom:** PlatformIO reports `Timed out waiting for packet header` during upload.
- **Fix:**
  1. Hold down the **FLASH** button on the NodeMCU board while clicking upload, then release when writing begins.
  2. Try a different USB cable (ensure it has data lines, not a charge-only cable).
  3. Close any open Serial Monitor programs that are holding open the COM port.

---

## 15. First-Boot Sequence Sanity Check
- **Symptom:** How to tell if the hardware is fundamentally sound?
- **Expected Behavior:** On every boot, the controller runs a safe, non-disturbing sanity check:
  - Solid Red (400ms) $\rightarrow$ Solid Green (400ms) $\rightarrow$ Solid Blue (400ms) $\rightarrow$ Solid White (400ms) $\rightarrow$ Clear.
  - If all colors illuminate in that exact order across all 200 LEDs at startup, your wiring, data line, level integrity, and power supply are 100% verified and operating correctly!
