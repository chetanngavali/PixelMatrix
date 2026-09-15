"""
Configuration Persistence Manager for PixelMatrix Screen Sync
Saves and restores user layout, color settings, monitor selection, and IP in JSON format.
"""

import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger("ScreenSync.Config")

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screen_sync_config.json")

DEFAULT_CONFIG = {
    "esp_ip": "192.168.1.50",
    "esp_ws_port": 81,
    "monitor_index": 0,
    "target_fps": 60,
    
    # Layout settings
    "layout_mode": "rectangle",  # "rectangle" or "custom"
    "top_count": 60,
    "right_count": 40,
    "bottom_count": 60,
    "left_count": 40,
    "start_corner": "top-left",
    "direction": "clockwise",
    "reverse_top": False,
    "reverse_right": False,
    "reverse_bottom": False,
    "reverse_left": False,
    "custom_points": [],

    # Color & Processing
    "brightness": 80,
    "saturation": 120,
    "intensity": 100,
    "gamma": 2.2,
    "smoothing": "LOW",
    "black_threshold": 12,
    "edge_depth_pct": 0.12
}

class ConfigManager:
    def __init__(self, filepath: str = CONFIG_FILE):
        self.filepath = filepath
        self.config: Dict[str, Any] = DEFAULT_CONFIG.copy()
        self.load()

    def load(self) -> Dict[str, Any]:
        """Loads configuration from JSON file."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.config.update(data)
                logger.info(f"Loaded configuration from {self.filepath}")
            except Exception as e:
                logger.warning(f"Failed to load config: {e}. Using defaults.")
        return self.config

    def save(self) -> bool:
        """Saves active configuration to JSON file."""
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Saved configuration to {self.filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def set(self, key: str, val: Any):
        self.config[key] = val
