"""
High-Performance Color Extraction and Processing Engine
Features:
- Saturation-weighted RGB color extraction (prevents muddy grey desaturation)
- Brightness adjustment (0..100%)
- Saturation boost (0..200%)
- Color intensity scaling (0..200%)
- Gamma correction (configurable, default 2.2)
- Black threshold cut-off (turns LEDs cleanly off in dark scenes)
- Adaptive temporal smoothing (smooths subtle shifts, snaps immediately on scene cuts)
"""

import numpy as np
from typing import List, Tuple
from desktop.mapping.layout_engine import SamplingZone

class ColorProcessor:
    SMOOTHING_PRESETS = {
        "OFF": 0.0,
        "LOW": 0.3,
        "MEDIUM": 0.6,
        "HIGH": 0.85
    }

    def __init__(self):
        self.brightness = 80       # 0..100 %
        self.saturation = 120      # 0..200 %
        self.intensity = 100       # 0..200 %
        self.gamma = 2.2           # Gamma correction exponent
        self.black_threshold = 12  # Pixels below this average RGB value are clamped to black (0)
        self.smoothing = "LOW"     # OFF, LOW, MEDIUM, HIGH
        self.scene_cut_threshold = 75 # Jump threshold to bypass smoothing on major scene changes
        
        self._prev_frame: np.ndarray = None
        self._gamma_lut = self._build_gamma_lut(self.gamma)

    def set_gamma(self, gamma: float):
        self.gamma = max(1.0, min(3.0, gamma))
        self._gamma_lut = self._build_gamma_lut(self.gamma)

    def _build_gamma_lut(self, gamma: float) -> np.ndarray:
        """Precomputes an 8-bit gamma lookup table for instantaneous O(1) transform."""
        lut = np.zeros(256, dtype=np.uint8)
        for i in range(256):
            val = int(255.0 * ((i / 255.0) ** gamma) + 0.5)
            lut[i] = max(0, min(255, val))
        return lut

    def extract_and_process(self, frame_bgra: np.ndarray, zones: List[SamplingZone]) -> bytes:
        """
        Extracts representative RGB for each sampling zone from the frame,
        applies saturation-weighted averaging, color adjustments, smoothing, and gamma.
        Returns raw packed RGB bytes (N * 3 bytes).
        """
        if frame_bgra is None or len(zones) == 0:
            return b""

        frame_h, frame_w = frame_bgra.shape[:2]
        num_leds = len(zones)
        raw_rgb = np.zeros((num_leds, 3), dtype=np.float32)

        for i, zone in enumerate(zones):
            # Compute integer pixel slice for this zone
            # zone.norm_x, norm_y are normalized centers
            cx = int(zone.norm_x * frame_w)
            cy = int(zone.norm_y * frame_h)
            half_w = max(2, int((zone.norm_w * frame_w) / 2))
            half_h = max(2, int((zone.norm_h * frame_h) / 2))

            x0 = max(0, cx - half_w)
            x1 = min(frame_w, cx + half_w)
            y0 = max(0, cy - half_h)
            y1 = min(frame_h, cy + half_h)

            if x1 <= x0 or y1 <= y0:
                continue

            # Crop region of interest: shape is (H, W, 3 or 4)
            # frame_bgra has channels [B, G, R, A] or [B, G, R]
            roi = frame_bgra[y0:y1, x0:x1]
            b_ch = roi[:, :, 0].astype(np.float32)
            g_ch = roi[:, :, 1].astype(np.float32)
            r_ch = roi[:, :, 2].astype(np.float32)

            # Saturation-weighted color extraction:
            # S = max(R,G,B) - min(R,G,B)
            # Give higher weight to colorful pixels so vivid colors aren't washed out
            max_c = np.maximum(np.maximum(r_ch, g_ch), b_ch)
            min_c = np.minimum(np.minimum(r_ch, g_ch), b_ch)
            sat = (max_c - min_c) + 1.0  # +1 baseline weight to prevent div by zero
            sat_weight = sat ** 1.5      # Non-linear emphasis on vibrant pixels

            total_weight = np.sum(sat_weight)
            if total_weight > 0.001:
                r_avg = np.sum(r_ch * sat_weight) / total_weight
                g_avg = np.sum(g_ch * sat_weight) / total_weight
                b_avg = np.sum(b_ch * sat_weight) / total_weight
            else:
                r_avg = np.mean(r_ch)
                g_avg = np.mean(g_ch)
                b_avg = np.mean(b_ch)

            raw_rgb[i, 0] = r_avg
            raw_rgb[i, 1] = g_avg
            raw_rgb[i, 2] = b_avg

        # Apply Black Threshold: if brightness is below threshold, turn off cleanly
        brightness_val = np.mean(raw_rgb, axis=1)
        black_mask = brightness_val < self.black_threshold
        raw_rgb[black_mask] = 0.0

        # Apply Saturation Boost (0..200%)
        if self.saturation != 100:
            sat_factor = self.saturation / 100.0
            gray = 0.299 * raw_rgb[:, 0] + 0.587 * raw_rgb[:, 1] + 0.114 * raw_rgb[:, 2]
            gray = gray[:, np.newaxis]
            raw_rgb = gray + (raw_rgb - gray) * sat_factor
            raw_rgb = np.clip(raw_rgb, 0.0, 255.0)

        # Apply Color Intensity / Multiplier (0..200%)
        if self.intensity != 100:
            raw_rgb *= (self.intensity / 100.0)

        # Apply Master Brightness (0..100%)
        raw_rgb *= (self.brightness / 100.0)
        raw_rgb = np.clip(raw_rgb, 0.0, 255.0)

        # Adaptive Temporal Smoothing
        smooth_factor = self.SMOOTHING_PRESETS.get(self.smoothing.upper(), 0.3)
        if smooth_factor > 0.0 and self._prev_frame is not None and self._prev_frame.shape == raw_rgb.shape:
            # Measure difference between frames
            diff = np.abs(raw_rgb - self._prev_frame)
            max_diff = np.max(diff)
            if max_diff > self.scene_cut_threshold:
                # Scene cut detected! Snap immediately to fresh frame for zero latency
                processed_rgb = raw_rgb
            else:
                # Subtle shift - apply smooth exponential moving average
                processed_rgb = (1.0 - smooth_factor) * raw_rgb + smooth_factor * self._prev_frame
        else:
            processed_rgb = raw_rgb

        self._prev_frame = processed_rgb.copy()

        # Apply Gamma LUT
        processed_int = np.clip(processed_rgb, 0, 255).astype(np.uint8)
        final_rgb = self._gamma_lut[processed_int]

        return final_rgb.tobytes()
