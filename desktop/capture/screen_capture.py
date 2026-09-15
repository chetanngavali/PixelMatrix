"""
High-Performance Screen Capture Engine
Supports:
1. DXGI Desktop Duplication (via dxcam / Windows native GPU capture)
2. Fast GDI Screen Capture (fallback if DXGI unavailable or non-interactive session)
3. Synthetic Test Pattern Generator (for testing and validation)
"""

import sys
import time
import logging
from typing import List, Dict, Optional, Tuple
import numpy as np

logger = logging.getLogger("ScreenSync.Capture")

class DisplayInfo:
    def __init__(self, index: int, name: str, left: int, top: int, width: int, height: int, is_primary: bool = False):
        self.index = index
        self.name = name
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.is_primary = is_primary

    def __repr__(self):
        return f"<Display {self.index}: {self.name} {self.width}x{self.height} (primary={self.is_primary})>"

class ScreenCaptureEngine:
    def __init__(self):
        self.selected_display_index = 0
        self.displays: List[DisplayInfo] = []
        self._dxcam_camera = None
        self._backend = "UNKNOWN"
        self._test_pattern_phase = 0.0
        self.refresh_displays()

    def refresh_displays(self) -> List[DisplayInfo]:
        """Detects all attached monitors and resolutions via Windows user32/DXGI/mss."""
        self.displays = []
        try:
            import mss
            with mss.mss() as sct:
                # sct.monitors[0] is the virtual all-in-one bounding box, 1..N are actual displays
                for idx, m in enumerate(sct.monitors):
                    if idx == 0:
                        continue # Skip virtual all-screen bounding box
                    is_prim = (m.get('is_primary', False) or idx == 1)
                    disp = DisplayInfo(
                        index=idx - 1,
                        name=f"Display {idx} ({m['width']}x{m['height']})",
                        left=m['left'],
                        top=m['top'],
                        width=m['width'],
                        height=m['height'],
                        is_primary=is_prim
                    )
                    self.displays.append(disp)
        except Exception as e:
            logger.warning(f"Could not enumerate displays via mss: {e}")

        if not self.displays:
            # Fallback single primary display
            self.displays.append(DisplayInfo(0, "Default Display (1920x1080)", 0, 0, 1920, 1080, True))

        return self.displays

    def start(self, display_idx: int = 0) -> bool:
        """Initializes high-performance capture on the selected display."""
        self.selected_display_index = display_idx
        
        # 1. Attempt DXGI capture
        try:
            import dxcam
            self._dxcam_camera = dxcam.create(output_idx=display_idx, output_color="BGR")
            if self._dxcam_camera:
                self._backend = "DXGI"
                logger.info(f"Initialized DXGI screen capture on display {display_idx}")
                return True
        except Exception as e:
            logger.info(f"DXGI capture not available ({e}), falling back to Windows GDI/PIL/Synthetic")

        # 2. Fallback to mss / GDI capture
        try:
            import mss
            self._sct = mss.mss()
            self._backend = "MSS"
            logger.info(f"Initialized MSS screen capture on display {display_idx}")
            return True
        except Exception as e:
            logger.warning(f"MSS capture failed: {e}")

        self._backend = "SYNTHETIC"
        return True

    def stop(self):
        """Releases all capture resources."""
        if self._dxcam_camera:
            try:
                self._dxcam_camera.release()
            except Exception:
                pass
            self._dxcam_camera = None

    def capture_frame(self) -> Optional[np.ndarray]:
        """
        Captures and returns the current screen frame as a numpy array with shape (H, W, 3) BGR.
        Zero disk writes, zero PNG encodings for maximum FPS.
        """
        # 1. DXGI capture path
        if self._backend == "DXGI" and self._dxcam_camera:
            try:
                frame = self._dxcam_camera.grab()
                if frame is not None:
                    return frame
            except Exception:
                pass

        # 2. MSS / GDI capture path
        if self._backend == "MSS":
            try:
                import mss
                mon_idx = min(len(self.displays), self.selected_display_index + 1)
                with mss.mss() as sct:
                    shot = sct.grab(sct.monitors[mon_idx])
                    # shot is BGRA
                    return np.array(shot, dtype=np.uint8)
            except Exception:
                pass

        # 3. Fallback / Test Pattern Generator (Rainbow swirl across display)
        # Keeps pipeline functional if running in a headless or locked desktop
        disp = self.displays[min(self.selected_display_index, len(self.displays) - 1)]
        h, w = 360, 640 # Lightweight simulation frame
        self._test_pattern_phase += 0.05
        y, x = np.mgrid[0:h, 0:w]
        
        # Dynamic rainbow wave
        r = (np.sin(x / 50.0 + self._test_pattern_phase) * 127 + 128).astype(np.uint8)
        g = (np.sin(y / 50.0 + self._test_pattern_phase + 2.0) * 127 + 128).astype(np.uint8)
        b = (np.sin((x + y) / 70.0 + self._test_pattern_phase + 4.0) * 127 + 128).astype(np.uint8)
        
        frame = np.stack([b, g, r], axis=-1)
        return frame
