# REST API & WebSocket Protocol: ESP8266 PixelMatrix 200

The **ESP8266 PixelMatrix 200** exposes a REST JSON API on port 80 and a binary WebSocket preview stream on port 81.

---

## 1. WebSocket Preview Stream (Port 81)

- **URL:** `ws://<ESP8266_IP>:81/`
- **Protocol:** Binary stream
- **Rate:** 20 FPS (every 50 ms)
- **Frame Format (602 Bytes Total):**

| Byte Offset | Field | Value / Description |
|---|---|---|
| `0` | Header Byte 1 | `0xAA` |
| `1` | Header Byte 2 | `0x55` |
| `2, 3, 4` | LED #1 Color | Red, Green, Blue (0–255 each) |
| `5, 6, 7` | LED #2 Color | Red, Green, Blue (0–255 each) |
| `...` | ... | ... |
| `599, 600, 601` | LED #200 Color | Red, Green, Blue (0–255 each) |

---

## 2. REST Endpoints Overview

All REST requests support JSON payloads (`Content-Type: application/json`) as well as URL form-encoded arguments. All endpoints return standard CORS headers (`Access-Control-Allow-Origin: *`).

### Summary Table

| Method | Path | Description |
|---|---|---|
| **GET** | `/api/status` | Current system state, telemetry, power estimates, and Wi-Fi data |
| **GET** | `/api/config` | Static hardware parameters and firmware version |
| **GET** | `/api/effects` | Array of all 20 available FastLED physical animation effects |
| **GET** | `/api/presets` | List of all stored user presets in flash |
| **POST** | `/api/power` | Turn LED output ON or OFF |
| **POST** | `/api/brightness` | Set brightness (0–100%) subject to safe limit |
| **POST** | `/api/color` | Set Primary or Secondary color (HEX or RGB) |
| **POST** | `/api/effect` | Set active animation effect by ID or name |
| **POST** | `/api/speed` | Set animation speed modifier (1–100) |
| **POST** | `/api/intensity` | Set pattern intensity modifier (1–100) |
| **POST** | `/api/direction` | Set wave direction (`"forward"` or `"reverse"`) |
| **POST** | `/api/test` | Trigger one of the 11 hardware diagnostic modes |
| **POST** | `/api/preset/save` | Save current active scene to flash |
| **POST** | `/api/preset/load` | Load a saved preset from flash |
| **POST** | `/api/preset/rename` | Rename an existing preset |
| **DELETE** | `/api/preset` | Remove a saved preset from flash |
| **POST** | `/api/wifi` | Configure Station Wi-Fi SSID and password |
| **POST** | `/api/settings` | Modify max safe brightness or device name |
| **POST** | `/api/reboot` | Soft-reboot the ESP8266 microcontroller |

---

## 3. Detailed Endpoint Specifications

### `GET /api/status`
Returns complete real-time status.

**Sample Response:**
```json
{
  "power": true,
  "ledCount": 200,
  "brightness": 30,
  "maxSafeBrightness": 80,
  "effect": "Rainbow",
  "effectIndex": 1,
  "speed": 50,
  "intensity": 75,
  "direction": "forward",
  "primaryColor": { "r": 124, "g": 58, "b": 237, "hex": "#7c3aed" },
  "secondaryColor": { "r": 37, "g": 99, "b": 235, "hex": "#2563eb" },
  "testMode": 0,
  "testLedIndex": 0,
  "dataPin": 5,
  "wifi": true,
  "ip": "192.168.1.150",
  "ssid": "MyHomeNetwork",
  "rssi": -58,
  "deviceName": "PixelMatrix-200",
  "estCurrentA": "3.80",
  "estWattage": "19.0",
  "psuUtilization": "19.0",
  "freeHeap": 42100,
  "uptime": 240,
  "version": "1.0.0"
}
```

---

### `POST /api/power`
Toggle LED array power.

**Request:**
```json
{
  "power": true
}
```

---

### `POST /api/brightness`
Set global brightness.

**Request:**
```json
{
  "brightness": 45
}
```

---

### `POST /api/color`
Set primary or secondary palette color.

**Request (HEX or RGB):**
```json
{
  "primary": "#ff3366",
  "secondary": { "r": 0, "g": 200, "b": 255 }
}
```

---

### `POST /api/effect`
Select active animation effect.

**Request:**
```json
{
  "effect": 1
}
```
*(Or by name: `{ "effect": "Fire" }`)*

---

### `POST /api/test`
Activate one of the 11 hardware diagnostic modes:

```json
{
  "mode": "sequential_fwd"
}
```
*Valid modes: `none`, `first_1`, `first_10`, `first_50`, `all_200`, `solid_red`, `solid_green`, `solid_blue`, `solid_white`, `sequential_fwd`, `sequential_rev`, `individual` (requires `"index": 42`).*

---

### `POST /api/reboot`
Soft-reboots the ESP8266 controller.

**Response:**
```json
{
  "status": "success",
  "message": "Rebooting ESP..."
}
```
