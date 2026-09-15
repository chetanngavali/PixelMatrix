"""
Screen Sync Binary Protocol for PixelMatrix ESP8266
High-performance low-overhead packet format.
Header: "SYNC" (0x53, 0x59, 0x4E, 0x43)
"""

import struct

MAGIC = b"SYNC"
PROTOCOL_VERSION = 0x01

# Packet Types
PKT_TYPE_FRAME = 0x01
PKT_TYPE_TEST = 0x02
PKT_TYPE_HEARTBEAT = 0x03

def build_screen_sync_frame(frame_id: int, rgb_array: bytes, led_count: int) -> bytes:
    """
    Builds a binary Screen Sync packet for the ESP8266.
    
    Packet structure:
    Bytes 0..3:   Magic 'S' 'Y' 'N' 'C' (4 bytes)
    Byte 4:       Version 0x01 (1 byte)
    Byte 5:       Packet Type 0x01 (1 byte)
    Bytes 6..7:   Frame ID uint16 (2 bytes big-endian)
    Bytes 8..9:   LED Count N uint16 (2 bytes big-endian)
    Byte 10:      Flags / Reserved (1 byte)
    Byte 11:      Header Checksum (1 byte XOR of bytes 0..10)
    Bytes 12..12+3N-1: RGB Payload (N * 3 bytes)
    Byte 12+3N:   Payload Checksum (1 byte XOR of RGB payload)
    """
    if len(rgb_array) < led_count * 3:
        raise ValueError(f"RGB array length ({len(rgb_array)}) is smaller than led_count * 3 ({led_count * 3})")
    
    payload = rgb_array[:led_count * 3]
    
    # Pack header fields up to byte 10
    raw_header = struct.pack(">4sBBHHB", MAGIC, PROTOCOL_VERSION, PKT_TYPE_FRAME, frame_id & 0xFFFF, led_count, 0x00)
    
    # Calculate header checksum (XOR of bytes 0..10)
    hdr_checksum = 0
    for b in raw_header:
        hdr_checksum ^= b
        
    # Calculate payload checksum (XOR of all RGB bytes)
    payload_checksum = 0
    for b in payload:
        payload_checksum ^= b
        
    return raw_header + bytes([hdr_checksum]) + payload + bytes([payload_checksum])

def build_heartbeat_packet(frame_id: int = 0) -> bytes:
    """Builds a lightweight heartbeat packet to maintain connection."""
    raw_header = struct.pack(">4sBBHHB", MAGIC, PROTOCOL_VERSION, PKT_TYPE_HEARTBEAT, frame_id & 0xFFFF, 0, 0x00)
    hdr_checksum = 0
    for b in raw_header:
        hdr_checksum ^= b
    return raw_header + bytes([hdr_checksum, 0x00])
