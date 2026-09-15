# Power System Engineering & Calculation: ESP8266 PixelMatrix 200

This document details electrical power calculations, PSU selection, voltage drop modeling, and software power estimation formulas for driving 200 WS2812B LEDs with the **ESP8266 PixelMatrix 200**.

---

## 1. Theoretical Maximum Power Consumption

Each WS2812B pixel contains three internal LED channels (Red, Green, Blue) driven by constant-current sinks:
- **Red channel:** ~20mA at full brightness
- **Green channel:** ~20mA at full brightness
- **Blue channel:** ~20mA at full brightness
- **Internal Logic IC quiescent:** ~1mA

$$\text{Max Current per LED} \approx 60\text{ mA} = 0.060\text{ A}$$

### For 200 LEDs at 100% Brightness (Full Solid White):
$$I_{\text{max}} = 200 \times 0.060\text{ A} = 12.0\text{ Amperes}$$
$$P_{\text{max}} = 5.0\text{ V} \times 12.0\text{ A} = 60.0\text{ Watts}$$

### Operating Current at Various Brightness Levels:

| Brightness % | FastLED Raw (0-255) | Estimated Current (A) | Estimated Wattage (W) | Typical Content / Effect |
|---|---|---|---|---|
| **0% (Off)** | 0 | **0.20 A** (quiescent) | **1.0 W** | System standby, logic active |
| **20%** | 51 | **2.60 A** | **13.0 W** | Subtle ambient glow |
| **30% (Default)** | 76 | **3.80 A** | **19.0 W** | Comfortable room lighting |
| **50%** | 128 | **6.20 A** | **31.0 W** | Vivid animations & colors |
| **80% (Max Safe)** | 204 | **9.80 A** | **49.0 W** | High-energy dynamic shows |
| **100% (Full White)**| 255 | **12.20 A** | **61.0 W** | Full solid white test |

> [!NOTE]
> In typical dynamic effects (Rainbow, Fire, Ocean, Scanner), not all three color channels are driven to 100% simultaneously. The real-world RMS current draw for dynamic animations usually averages **35% to 50% of the theoretical maximum**, or approximately **4.5A to 6.0A**.

---

## 2. Power Supply Selection & Headroom Rationale

- **Selected PSU Rating:** **5.0V DC / 20.0A (100W)**
- **Minimum Acceptable PSU:** **5.0V DC / 15.0A (75W)**

### Why a 20A PSU is Recommended:
1. **The 80% Continuous Load Rule:** Switched-mode power supplies (SMPS) should never be operated at 100% continuous rated capacity. Running at $\le 75\%\text{--}80\%$ capacity maximizes capacitor lifespan, keeps internal switching MOSFETs cool, and minimizes cooling fan noise.
2. **Dynamic Inrush & Surge Capacity:** Addressable LEDs draw sharp current steps when switching from dark scenes to bright strobes. A 20A supply easily absorbs transient loads without dropping below the 4.5V threshold that causes WS2812B ICs to reset.
3. **Headroom Buffer:** With a maximum load of 12A on a 20A supply, the system operates at **60% capacity**, leaving an 8A (40%) safety buffer.

---

## 3. Voltage Drop Analysis & Why 5-Point Injection is Essential

The flexible printed circuit (FPCB) strip uses thin copper foils (typically 1oz or 2oz copper, cross-section ~0.035 mm²).
- Copper track resistance is approximately **$0.2\Omega$ to $0.4\Omega$ per meter**.
- If 200 LEDs (approx. 3.3 meters at 60 LEDs/m) were powered from only one end:
  $$\Delta V = I \times R \approx 12\text{ A} \times 0.6\Omega = 7.2\text{ Volts (Theoretical Drop)}$$
- In reality, voltage collapses below 3.5V within the first 60 pixels. This produces:
  1. Severe color distortion: Blue and Green LEDs have higher forward voltages ($V_f \approx 3.0\text{V}$), so pixels near the end turn muddy pink or dim red ($V_f \approx 1.8\text{V}$).
  2. Logic failure: The internal WS2812B microcontrollers reset when voltage drops below ~3.6V, causing the tail of the strip to freeze or flicker randomly.

### The Solution: 5-Point Distributed Injection Bus
By injecting power at **LED #1, #50, #100, #150, and #200**, the maximum current flowing through any single segment of the thin strip trace is reduced to less than **2.4A**, and the maximum distance to an injection point is only 25 LEDs (~40 cm).

```
   [5V 20A PSU]
        |
   AWG 14 Bus (R < 0.02Ω)
   +------+-------+--------+--------+
   |      |       |        |        |
 LED #1 LED #50 LED #100 LED #150 LED #200
```
This guarantees uniform 5.0V (±0.15V) across all 200 pixels with zero color shift.

---

## 4. Software Power Estimation Formulas

The firmware includes real-time telemetry estimates calculated without requiring physical shunt sensors:

```cpp
float calculateEstimatedCurrentAmps(uint8_t brightnessPct, uint8_t activeLeds) {
    if (!gSettings.power || brightnessPct == 0) {
        return (activeLeds * 0.001f); // 1mA quiescent per LED
    }
    float scale = (float)brightnessPct / 100.0f;
    float currentPerLed = 0.001f + (60.0f / 1000.0f) * scale;
    return activeLeds * currentPerLed;
}

float calculateEstimatedWattage(float currentAmps, float voltage) {
    return currentAmps * voltage;
}

float calculatePsuUtilizationPct(float currentAmps, float psuRatingAmps) {
    return (currentAmps / psuRatingAmps) * 100.0f;
}
```

This telemetry is broadcast to the web dashboard and displayed live in the Studio header and Diagnostics tab.
