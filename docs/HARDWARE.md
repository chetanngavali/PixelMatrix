# Hardware Specification & Bill of Materials: ESP8266 PixelMatrix 200

This document specifies all hardware components, electrical ratings, wire sizing, and pin assignments for the **ESP8266 PixelMatrix 200** addressable lighting controller.

---

## 1. Complete Bill of Materials (BOM)

| Item # | Component | Specifications | Quantity | Purpose |
|---|---|---|---|---|
| **1** | **Microcontroller** | **ESP8266 12E NodeMCU V2/V3**, 160MHz 32-bit Tensilica L106, 80KB RAM, 4MB Flash | 1 | Firmware, FastLED engine, WebServer, WebSocket stream, Wi-Fi |
| **2** | **Addressable LEDs** | WS2812B individually addressable 5050 RGB LEDs, 5V DC, GRB color order | 200 pixels | Physical light matrix / strip |
| **3** | **Power Supply (PSU)** | Regulated 5.0V DC switching power supply, **20.0A (100W)** (Minimum 15.0A / 75W) | 1 | Dedicated LED array & system power |
| **4** | **Series Resistor** | 330Ω to 470Ω, 1/4W (0.25W) metal film or carbon film | 1 | Placed between NodeMCU Pin D1 and LED #1 DIN to dampen signal reflections |
| **5** | **Buffer Capacitor** | 1000µF to 2200µF, 16V or 25V Low-ESR Electrolytic | 1 | Placed across +5V and GND near LED #1 input to absorb inrush transients |
| **6** | **Main Power Bus Cable** | AWG 14 (or AWG 16) high-strand silicone wire (Red for +5V, Black for GND) | 2–3 meters | Low-resistance power distribution bus |
| **7** | **Power Injection Drops** | AWG 18 or AWG 20 flexible wire | 5 pairs | Connecting main power bus to LED strip injection points |
| **8** | **Data Signal Wire** | AWG 22 stranded hookup wire | < 15 cm | Low-capacitance direct logic line from Pin D1 to DIN |
| **9** | **Main Fuse Holder** | Inline blade fuse holder (ATO/ATC) with 15A or 20A automotive blade fuse | 1 | Overcurrent and short-circuit protection on PSU 5V positive output |
| **10** | **Terminal Blocks** | 5-position screw terminal distribution blocks or WAGO 221 lever nuts | 2 sets | Safe wire splicing for distributed injection |

---

## 2. Pinout & Interfacing

### ESP8266 NodeMCU Pin Allocation:
- **Pin D1 (GPIO 5):** WS2812B serial bit-stream transmission directly to LED #1 DIN via 330Ω–470Ω resistor. (Pin D1 is a safe boot pin on ESP8266 with no boot-mode pullup/pulldown conflicts).
- **GND:** Ground reference bonded directly to 5V PSU GND.
- **VIN (or Micro-USB):** Powers the NodeMCU logic from the 5V power supply.

```
                  NodeMCU 12E Pinout (Key Connections)
                  +-----------------------------------+
                  |              [ USB ]              |
                  | A0 (ADC0)                     D0  | (GPIO 16)
                  | G (GND)                       D1  +===> [ 330Ω Resistor ] ==> LED #1 DIN
                  | VV (NC)                       D2  | (GPIO 4)
                  | S3                            D3  | (GPIO 0 - Boot mode)
                  | S2                            D4  | (GPIO 2 - Boot mode)
                  | S1                            3V3 |
                  | SC                            GND +===> To 5V PSU GND & LED GND Bus
                  | S0                            D5  | (GPIO 14 - SCK)
                  | SK                            D6  | (GPIO 12 - MISO)
                  | G (GND)                       D7  | (GPIO 13 - MOSI)
                  | 3V3                           D8  | (GPIO 15 - Boot mode)
                  | EN                            RX  | (GPIO 3)
                  | RST                           TX  | (GPIO 1)
                  | G (GND)                       GND |
                  | VIN +=============================+===> To 5V PSU +5V
                  +-----------------------------------+
```

---

## 3. WS2812B Physical Interface

Each pixel contains an integrated logic controller and 3 discrete LED dies (Red, Green, Blue):
- **Operating Voltage:** 4.5V to 5.5V DC (Nominal 5.0V).
- **Data Signal High Voltage ($V_{IH}$):** Typically 0.7 × $V_{DD}$ (~3.5V nominal, accepted down to ~2.8V in practice at room temperature).
- **Protocol:** Non-return-to-zero (NRZ) 800 kHz single-wire serial transmission:
  - T0H: 0.4µs ±150ns, T0L: 0.85µs ±150ns
  - T1H: 0.8µs ±150ns, T1L: 0.45µs ±150ns
  - Reset code: > 50µs LOW.
- **Color Byte Order:** GRB (Green [8 bits], Red [8 bits], Blue [8 bits]).
- **Max Full-White Current:** ~55mA to 60mA per LED at 100% brightness ($200 \times 60\text{mA} = 12.0\text{A}$).
- **Quiescent Current (LED OFF):** ~1mA per pixel ($200 \times 1\text{mA} = 0.2\text{A}$ idle draw).

---

## 4. Wire Gauge & Resistance Specifications

Using undersized wire causes resistance heating and noticeable voltage drops. The following wire sizes are required:

| Function | Current Capacity | Required Gauge | Maximum Recommended Run Length |
|---|---|---|---|
| **PSU to Main Bus** | Up to 15A–20A | AWG 14 ($2.08\text{ mm}^2$) | Up to 2.5 meters |
| **Injection Drops (5x)** | ~2.5A–3.0A each | AWG 18 ($0.82\text{ mm}^2$) or AWG 20 | Up to 1 meter each |
| **Direct Data Signal** | Microamps (< 5mA) | AWG 22 ($0.33\text{ mm}^2$) | Keep under 15 cm (6 inches) |
| **Common Ground Bond** | Signal reference | AWG 20 ($0.52\text{ mm}^2$) | As short and direct as possible |
