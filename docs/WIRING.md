# Wiring Guide: ESP8266 PixelMatrix 200

This document describes the physical wiring topology for driving 200 WS2812B individually addressable RGB LEDs with an **ESP8266 12E NodeMCU** board **without any logic level shifter**.

---

## 1. Master System Schematic

```
                            +-----------------------------+
                            |     5V DC Power Supply      |
                            |       (5V / 20A Regulated)  |
                            +--------------+--------------+
                                           |
                    +5V Main Bus (AWG 14)  |  GND Main Bus (AWG 14)
       +-----------------------------------+-----------------------------------+
       |                                                                       |
       |  +--------------------+                                               |
       |  | 1000µF 16V Cap     |                                               |
       |  | (+)            (-) |                                               |
       +--+---[||]---------+---+                                               |
       |                   |                                                   |
       |                   +------------------------------------+              |
       |                                                        |              |
       |                                                  +-----+------+       |
       |                                                  | NodeMCU    |       |
       |                                                  |   GND      |       |
       |                                                  |            |       |
       |                                                  |   Pin D1   |       |
       |                                                  +-----+------+       |
       |                                                        |              |
       |                                                   [ 330Ω-470Ω ]       |
       |                                                  Resistor in-line     |
       |                                                        |              |
       |                                                        v              |
       |                                                   DIN (LED #1)        |
       |                                                        |              |
       +======> LED #1   +5V ----------------- LED #1   GND ====+              |
       |                                                                       |
       +======> LED #50  +5V ----------------- LED #50  GND ===================+
       |                                                                       |
       +======> LED #100 +5V ----------------- LED #100 GND ===================+
       |                                                                       |
       +======> LED #150 +5V ----------------- LED #150 GND ===================+
       |                                                                       |
       +======> LED #200 +5V ----------------- LED #200 GND ===================+
```

---

## 2. Mandatory Hardware Rule: Direct 3.3V Drive (No Level Shifter)

> [!IMPORTANT]
> **NO LEVEL SHIFTER IS USED IN THIS DESIGN.**
> Prohibited components:
> - 74AHCT125 / 74HCT125
> - 74AHCT245 / 74HCT245
> - TXS0108 / TXB0108 / BSS138 bi-directional level converters
> - Any transistor or MOSFET-based signal booster

### Why Direct 3.3V Drive Works Reliably on ESP8266:
1. **Output Level**: The ESP8266 GPIO output High level is approximately **3.3V**.
2. **Input Threshold**: In the WS2812B datasheet, $V_{IH}$ (High-level input voltage) is specified as $0.7 \times V_{DD}$. When $V_{DD} = 5.0\text{V}$, $0.7 \times 5.0\text{V} = 3.5\text{V}$ nominally. However, real-world WS2812B chips reliably trigger high at $\approx 2.7\text{V}\text{--}3.1\text{V}$.
3. **Signal Regeneration**: When the 3.3V signal reaches LED #1, the internal controller of LED #1 reconstructs and re-amplifies the signal to full **5.0V logic** before transmitting it via its `DO` (Data Out) pin to LED #2. 
4. Therefore, **only the link between NodeMCU Pin D1 and LED #1 operates at 3.3V**. All subsequent 199 LEDs receive full 5.0V square-wave signals.
5. **Key Prerequisites for Clean Signal Integrity**:
   - Keep the wire from Pin D1 to LED #1 short (< 15 cm / 6 inches).
   - Solder a **330Ω to 470Ω series resistor** directly in line at Pin D1 to absorb transmission-line ringing.
   - Establish a solid, low-resistance **common ground connection** between the ESP8266 GND and the 5V PSU ground.

---

## 3. Data Chain Direction (DIN → DO)

WS2812B LEDs are strictly **unidirectional**:

```
ESP8266 Pin D1 ──>[ 330Ω ]──> DIN [LED 1] DO ──> DIN [LED 2] DO ──> ... ──> DIN [LED 200]
```

- **DIN (Data In)**: Receives the serialized data packet.
- **DO (Data Out)**: Re-transmits the remaining pixel packet to the next LED.
- **Direction Arrows**: Look at the arrows printed on the LED strip surface ($\rightarrow$). The signal **MUST** enter at the arrow base and travel in the direction of the arrow.

---

## 4. 5-Point Power Injection Architecture

The internal copper traces inside flexible LED strips have an electrical resistance of $\approx 0.2\Omega\text{--}0.4\Omega$ per meter. Attempting to power all 200 LEDs from just one end causes extreme voltage drop, resulting in LEDs at the end turning yellowish-red and flickering.

To maintain a consistent 5.0V across all 200 pixels, power must be injected at 5 points:

| Tap | Physical Location | Wire from 5V Bus | Wire from GND Bus |
| :--- | :--- | :--- | :--- |
| **Tap 1** | LED #1 (Beginning) | +5V (AWG 18/20) | GND (AWG 18/20) |
| **Tap 2** | LED #50 | +5V (AWG 18/20) | GND (AWG 18/20) |
| **Tap 3** | LED #100 (Center) | +5V (AWG 18/20) | GND (AWG 18/20) |
| **Tap 4** | LED #150 | +5V (AWG 18/20) | GND (AWG 18/20) |
| **Tap 5** | LED #200 (End) | +5V (AWG 18/20) | GND (AWG 18/20) |

- **Main Bus Trunk**: Use heavy AWG 14 or AWG 16 silicone stranded wire running alongside the LED strip.
- **Injection Drops**: Solder short AWG 18 or AWG 20 wires from the main trunk to the +5V and GND copper pads on the strip.

---

## 5. Capacitive Filtering & Transient Suppression

- **Electrolytic Capacitor (1000µF, 16V or 25V)**:
  - Solder directly across the +5V and GND rails right at the power input of LED #1.
  - Pay strict attention to polarity: the negative strip marked with minus signs (`-`) goes to **GND**; the long lead goes to **+5V**.
  - This capacitor absorbs high inrush voltage spikes when the 5V power supply turns on, protecting the delicate internal CMOS circuitry of LED #1.
