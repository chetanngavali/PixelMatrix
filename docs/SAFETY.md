# Safety Guide & Precautions: ESP8266 PixelMatrix 200

High-current low-voltage DC installations present distinct electrical and fire-damage hazards. Adhere strictly to the safety guidelines in this document.

---

## 1. Operating Voltage: Strictly 5.0V DC

> [!CAUTION]
> **WS2812B LEDs OPERATE AT 5V DC ONLY.**
> Connecting a 12V or 24V power supply to these LEDs will instantly destroy all 200 pixel controller ICs, permanently incinerating the strip.
> - Verify your power supply output with a digital multimeter (DMM) **before** connecting any LEDs or the ESP8266.
> - Ensure the multimeter reads between **4.90V and 5.20V DC**.

---

## 2. Power Isolation: Do Not Power LEDs from the NodeMCU Board

> [!WARNING]
> **NEVER attempt to power 200 LEDs from the NodeMCU development board's 3.3V or VIN pins.**
> - The USB port and linear voltage regulator on the NodeMCU board can only safely pass 400mA–500mA.
> - Drawing 12A through the microcontroller board will vaporize PCB traces, destroy the USB chip, and may damage your computer's USB port.
> - Power the LEDs directly and exclusively from the external 5V 20A power supply.

---

## 3. Inline Fuse Protection

Because a 20A power supply can deliver tremendous short-circuit current capable of melting wires and igniting plastics, install an **inline automotive blade fuse (ATO/ATC)** on the primary +5V positive line immediately after the PSU output terminal:

```
  5V PSU (+5V Terminal) ───>[ 15A or 20A Fuse ]───> Main Distribution Bus
```

- **Fuse Rating:** 15A (for moderate brightness) or 20A (for high brightness).
- **Type:** Fast-acting or standard blade fuse.
- **Placement:** Within 15 cm of the power supply terminal.

---

## 4. Electrolytic Capacitor Polarity

The 1000µF buffer capacitor is an **electrolytic capacitor**, which is strictly polarized:
- The **negative (-) lead** is marked by a prominent stripe with minus signs down the side of the casing.
- The **positive (+) lead** is typically longer on new components.
- Connect (+) strictly to +5V, and (-) strictly to GND.

> [!CAUTION]
> **Reversing capacitor polarity will cause rapid internal boiling of the electrolyte, resulting in case rupture, venting of caustic smoke, or explosive failure.** Double-check polarity with your eyes before applying mains power.

---

## 5. Thermal & Brightness Management

Addressable LED strips dissipate heat proportional to power:
- At 100% white brightness (60W across 3.3 meters), flexible PCB strips can reach temperatures exceeding **65°C to 75°C**, which degrades the silicon lifespan and discolors silicone waterproofing sleeves.
- **Mounting Recommendation:** Adhere high-density LED strips to an **aluminum extrusion profile** to act as a heat sink.
- **Software Safeguard:** The firmware implements a default brightness of **30%** and allows setting a hardware cap (`MAX_SAFE_BRIGHTNESS_PCT`, default 80%). The web dashboard actively blocks exceeding this threshold unless reconfigured by the user.

---

## 6. Common Ground Requirement

The 5V Power Supply GND and ESP8266 GND **must be electrically connected**:
- Never run the ESP8266 from an isolated USB charger without bonding its GND pin to the 5V PSU GND terminal.
- Floating grounds produce undefined voltage potentials on Pin D1 (GPIO 5) that can inject negative voltages into LED #1 DIN or latch up the ESP8266 GPIO drivers.

---

## 7. Short-Circuit Prevention & Wire Sizing

- Strip terminals have tiny solder pads placed less than 1.5mm apart. Inspect every solder joint under magnification to verify there are no stray copper wire strands bridging +5V and GND.
- Use heat-shrink tubing over all solder joints and power taps.
- Never use thin bell wire or breadboard jumper wires for the main power feed. Use **AWG 14 or AWG 16 stranded copper wire** to prevent resistive heating and fire hazards.
