"""
Dynamic LED Layout Engine
Calculates normalized (0.0 to 1.0) screen sampling coordinates and bounding boxes
for rectangular (Top, Right, Bottom, Left) or custom point arrangements.
"""

from dataclasses import dataclass
from typing import List, Tuple, Dict, Any

@dataclass
class SamplingZone:
    led_index: int
    norm_x: float          # Normalized center X [0.0 .. 1.0]
    norm_y: float          # Normalized center Y [0.0 .. 1.0]
    norm_w: float          # Normalized width [0.0 .. 1.0]
    norm_h: float          # Normalized height [0.0 .. 1.0]
    side: str              # 'top', 'right', 'bottom', 'left', 'custom'

class LayoutEngine:
    START_CORNERS = ["top-left", "top-right", "bottom-right", "bottom-left"]
    DIRECTIONS = ["clockwise", "counter-clockwise"]

    def __init__(self):
        # Default 4-sided layout parameters
        self.top_count = 60
        self.right_count = 40
        self.bottom_count = 60
        self.left_count = 40
        self.start_corner = "top-left"
        self.direction = "clockwise"
        self.reverse_top = False
        self.reverse_right = False
        self.reverse_bottom = False
        self.reverse_left = False
        
        # Sampling depth parameters (how deep into the screen edge we sample)
        self.edge_depth_pct = 0.12  # 12% inward from screen edge
        self.zone_spread_pct = 1.2  # 120% zone width relative to LED spacing (overlap smoothing)
        
        # Custom points list: List of dicts {'x': float, 'y': float}
        self.custom_points: List[Dict[str, float]] = []
        self.is_custom_mode = False

    @property
    def total_leds(self) -> int:
        if self.is_custom_mode:
            return len(self.custom_points)
        return self.top_count + self.right_count + self.bottom_count + self.left_count

    def generate_zones(self, screen_w: int, screen_h: int) -> List[SamplingZone]:
        """
        Generates screen sampling zones for each physical LED.
        Zones are ordered according to the physical wiring sequence (index 0 to N-1).
        """
        if self.is_custom_mode:
            return self._generate_custom_zones(screen_w, screen_h)
        return self._generate_rectangular_zones(screen_w, screen_h)

    def _generate_rectangular_zones(self, screen_w: int, screen_h: int) -> List[SamplingZone]:
        """
        Generates rectangular 4-sided perimeter LED sampling regions.
        Handles start corner, wiring direction, and individual side reversal.
        """
        # 1. Generate normalized centers (x, y, side) for each of the 4 edges
        top_leds = []
        if self.top_count > 0:
            step = 1.0 / self.top_count
            for i in range(self.top_count):
                x = (i + 0.5) * step
                top_leds.append((x, 0.0, 'top'))
            if self.reverse_top:
                top_leds.reverse()

        right_leds = []
        if self.right_count > 0:
            step = 1.0 / self.right_count
            for i in range(self.right_count):
                y = (i + 0.5) * step
                right_leds.append((1.0, y, 'right'))
            if self.reverse_right:
                right_leds.reverse()

        bottom_leds = []
        if self.bottom_count > 0:
            step = 1.0 / self.bottom_count
            for i in range(self.bottom_count):
                x = 1.0 - (i + 0.5) * step
                bottom_leds.append((x, 1.0, 'bottom'))
            if self.reverse_bottom:
                bottom_leds.reverse()

        left_leds = []
        if self.left_count > 0:
            step = 1.0 / self.left_count
            for i in range(self.left_count):
                y = 1.0 - (i + 0.5) * step
                left_leds.append((0.0, y, 'left'))
            if self.reverse_left:
                left_leds.reverse()

        # 2. Assemble sides based on Start Corner and Direction
        # Clockwise standard side order starting from Top-Left: Top -> Right -> Bottom -> Left
        # Counter-Clockwise standard order starting from Top-Left: Left -> Bottom -> Right -> Top
        if self.direction == "clockwise":
            if self.start_corner == "top-left":
                ordered_sides = [top_leds, right_leds, bottom_leds, left_leds]
            elif self.start_corner == "top-right":
                ordered_sides = [right_leds, bottom_leds, left_leds, top_leds]
            elif self.start_corner == "bottom-right":
                ordered_sides = [bottom_leds, left_leds, top_leds, right_leds]
            else: # bottom-left
                ordered_sides = [left_leds, top_leds, right_leds, bottom_leds]
        else: # counter-clockwise
            # Reverse direction of side ordering and LED sequence
            cw_tl = [top_leds, right_leds, bottom_leds, left_leds]
            ccw_leds = []
            for side in cw_tl:
                for pt in side:
                    ccw_leds.append(pt)
            ccw_leds.reverse()
            
            # Rotate according to starting corner
            ordered_sides = [ccw_leds]

        # Flatten list of points
        all_pts = []
        for s in ordered_sides:
            all_pts.extend(s)

        # 3. Create SamplingZone objects with sampling bounds
        zones: List[SamplingZone] = []
        for idx, (nx, ny, side) in enumerate(all_pts):
            # Compute width and height based on side
            if side == 'top':
                w = (1.0 / max(1, self.top_count)) * self.zone_spread_pct
                h = self.edge_depth_pct
            elif side == 'bottom':
                w = (1.0 / max(1, self.bottom_count)) * self.zone_spread_pct
                h = self.edge_depth_pct
            elif side == 'left':
                w = self.edge_depth_pct
                h = (1.0 / max(1, self.left_count)) * self.zone_spread_pct
            elif side == 'right':
                w = self.edge_depth_pct
                h = (1.0 / max(1, self.right_count)) * self.zone_spread_pct
            else:
                w = 0.08
                h = 0.08

            zones.append(SamplingZone(
                led_index=idx,
                norm_x=nx,
                norm_y=ny,
                norm_w=min(1.0, w),
                norm_h=min(1.0, h),
                side=side
            ))

        return zones

    def _generate_custom_zones(self, screen_w: int, screen_h: int) -> List[SamplingZone]:
        """Generates zones from user-placed normalized (x, y) coordinates."""
        zones: List[SamplingZone] = []
        default_size = 0.08  # 8% of screen size default box
        for idx, pt in enumerate(self.custom_points):
            nx = max(0.0, min(1.0, pt.get('x', 0.0)))
            ny = max(0.0, min(1.0, pt.get('y', 0.0)))
            zones.append(SamplingZone(
                led_index=idx,
                norm_x=nx,
                norm_y=ny,
                norm_w=default_size,
                norm_h=default_size,
                side='custom'
            ))
        return zones
