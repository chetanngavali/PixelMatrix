"""
Asynchronous Low-Latency WebSocket Client for PixelMatrix Screen Sync
Sends binary frames directly to ws://<ESP_IP>:81/
Optimized for ultra-low latency with stale frame dropping.
"""

import asyncio
import time
import logging
from typing import Optional, Callable
import websockets
from desktop.network.protocol import build_screen_sync_frame, build_heartbeat_packet

logger = logging.getLogger("ScreenSync.Network")

class ScreenSyncWebSocketClient:
    def __init__(self, host: str, port: int = 81):
        self.host = host
        self.port = port
        self.uri = f"ws://{host}:{port}/"
        self.websocket = None
        self.is_connected = False
        self.frame_seq = 0
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._send_queue: Optional[asyncio.Queue] = None
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self.on_connection_change: Optional[Callable[[bool, str], None]] = None
        self.frames_sent = 0
        self.last_sent_time = 0.0

    async def connect(self):
        """Connects to the ESP8266 WebSocket server."""
        self._running = True
        self._loop = asyncio.get_running_loop()
        self._send_queue = asyncio.Queue(maxsize=2) # Created on the active running loop
        try:
            logger.info(f"Connecting to ESP8266 at {self.uri}...")
            self.websocket = await websockets.connect(
                self.uri,
                open_timeout=4.0,   # Generous timeout for ESP8266 Wi-Fi handshake
                ping_interval=None, # Disable ping/pong overhead for raw 60 FPS performance
                close_timeout=1.5
            )
            self.is_connected = True
            logger.info("Connected to ESP8266 Screen Sync WebSocket")
            if self.on_connection_change:
                self.on_connection_change(True, "Connected")
            
            # Start background sender and heartbeat
            self._worker_task = asyncio.create_task(self._sender_loop())
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            return True
        except Exception as e:
            self.is_connected = False
            logger.warning(f"Connection failed to {self.uri}: {e}")
            if self.on_connection_change:
                self.on_connection_change(False, str(e))
            return False

    async def disconnect(self):
        """Disconnects cleanly from the ESP8266."""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception:
                pass
            self.websocket = None
        self.is_connected = False
        if self.on_connection_change:
            self.on_connection_change(False, "Disconnected")

    def queue_frame(self, rgb_data: bytes, led_count: int):
        """Queues an RGB frame thread-safely from the capture thread to the network event loop."""
        if not self.is_connected or self._send_queue is None or self._loop is None:
            return
        
        self.frame_seq = (self.frame_seq + 1) & 0xFFFF
        try:
            packet = build_screen_sync_frame(self.frame_seq, rgb_data, led_count)
            def _push():
                if self._send_queue.full():
                    try:
                        self._send_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                try:
                    self._send_queue.put_nowait(packet)
                except asyncio.QueueFull:
                    pass
            self._loop.call_soon_threadsafe(_push)
        except Exception as e:
            logger.error(f"Error packing frame: {e}")

    async def _sender_loop(self):
        """Asynchronous worker pulling newest frame from queue and transmitting over socket."""
        while self._running and self.is_connected:
            try:
                packet = await self._send_queue.get()
                if self.websocket and self.is_connected:
                    t0 = time.perf_counter()
                    await self.websocket.send(packet)
                    self.frames_sent += 1
                    self.last_sent_time = time.perf_counter() - t0
                self._send_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"WebSocket send error: {e}")
                self.is_connected = False
                if self.on_connection_change:
                    self.on_connection_change(False, f"Send error: {e}")
                break

    async def _heartbeat_loop(self):
        """Sends lightweight heartbeat every 1.5 seconds if no frames sent to prevent timeout."""
        while self._running and self.is_connected:
            try:
                await asyncio.sleep(1.5)
                if time.perf_counter() - self.last_sent_time > 1.0 and self.websocket:
                    hb = build_heartbeat_packet(self.frame_seq)
                    await self.websocket.send(hb)
            except asyncio.CancelledError:
                break
            except Exception:
                break
