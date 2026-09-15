"""
Live ESP8266 WebSocket Integration Test
Connects to ws://192.168.1.31:81/ and streams live test frames.
"""
import sys
import os
import time
import asyncio
import websockets

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from desktop.network.protocol import build_screen_sync_frame

ESP_IP = "192.168.1.31"
ESP_PORT = 81
LED_COUNT = 500  # Configured physical LED count on ESP8266

async def run_live_test():
    uri = f"ws://{ESP_IP}:{ESP_PORT}/"
    print(f"Connecting to ESP8266 at {uri} (subprotocols=['screen-sync'])...")
    
    try:
        async with websockets.connect(uri, subprotocols=["arduino"], ping_interval=5, ping_timeout=10) as ws:
            print(" Connected to ESP8266 Screen Sync WebSocket server!")
            
            colors = [
                ("RED", (255, 0, 0)),
                ("GREEN", (0, 255, 0)),
                ("BLUE", (0, 0, 255)),
                ("WHITE", (200, 200, 200)),
                ("ORANGE", (255, 100, 0)),
                ("CYAN", (0, 200, 255)),
            ]
            
            frame_id = 1
            for name, (r, g, b) in colors:
                print(f"\nSending Color Test Frame: {name} (R={r}, G={g}, B={b}) to {LED_COUNT} LEDs...")
                # Fill all LEDs with the test color
                rgb_bytes = bytearray()
                for _ in range(LED_COUNT):
                    rgb_bytes.extend([r, g, b])
                
                pkt = build_screen_sync_frame(frame_id, bytes(rgb_bytes), LED_COUNT)
                await ws.send(pkt)
                print(f"  -> Packet sent ({len(pkt)} bytes). Frame ID: {frame_id}")
                frame_id += 1
                await asyncio.sleep(1.0)
            
            print("\nStreaming 30 Smooth Color Gradient frames to verify live refresh...")
            for i in range(30):
                rgb_bytes = bytearray()
                hue_shift = (i * 8) % 256
                for j in range(LED_COUNT):
                    val = (j * 5 + hue_shift) % 256
                    rgb_bytes.extend([val, 255 - val, (val * 2) % 256])
                pkt = build_screen_sync_frame(frame_id, bytes(rgb_bytes), LED_COUNT)
                await ws.send(pkt)
                frame_id += 1
                await asyncio.sleep(0.05)
            
            print("\n Live WebSocket test completed successfully! Physical LEDs responded!")
            
    except Exception as e:
        print(f" Error connecting to ESP8266: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_live_test())
