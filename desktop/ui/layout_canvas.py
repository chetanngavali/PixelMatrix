"""
Visual LED Layout Designer Canvas (Tkinter Canvas)
Features:
- Premium light-mode visual monitor representation
- Displays physical perimeter LEDs with accurate side distributions
- Renders LED index labels and live sampling zones
- Highlights test/selected LEDs during calibration
- Supports custom normalized coordinate point dragging and editing
"""

import tkinter as tk
from typing import List, Optional, Callable, Dict, Any
from desktop.mapping.layout_engine import SamplingZone, LayoutEngine

class LayoutCanvas(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#f8fafc", highlightthickness=1, highlightbackground="#e2e8f0", **kwargs)
        self.zones: List[SamplingZone] = []
        self.selected_led_index: Optional[int] = None
        self.on_led_clicked: Optional[Callable[[int], None]] = None
        self.live_colors: Optional[bytes] = None # Packed RGB bytes
        self.bind("<Configure>", self._on_resize)
        self.bind("<Button-1>", self._on_click)

    def set_zones(self, zones: List[SamplingZone]):
        self.zones = zones
        self.redraw()

    def set_selected_led(self, idx: Optional[int]):
        self.selected_led_index = idx
        self.redraw()

    def update_live_colors(self, rgb_bytes: bytes):
        self.live_colors = rgb_bytes
        self.after_idle(self.redraw)

    def _on_resize(self, event):
        self.redraw()

    def _on_click(self, event):
        # Hit test against LED dot coordinates
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 50 or h < 50 or not self.zones:
            return

        pad_x, pad_y = 60, 45
        screen_w = w - 2 * pad_x
        screen_h = h - 2 * pad_y

        click_x, click_y = event.x, event.y
        closest_idx = None
        min_dist_sq = 150 # 12px radius squared

        for zone in self.zones:
            px = pad_x + zone.norm_x * screen_w
            py = pad_y + zone.norm_y * screen_h
            dist_sq = (click_x - px) ** 2 + (click_y - py) ** 2
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                closest_idx = zone.led_index

        if closest_idx is not None and self.on_led_clicked:
            self.on_led_clicked(closest_idx)

    def redraw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 50 or h < 50:
            return

        pad_x, pad_y = 60, 45
        screen_w = w - 2 * pad_x
        screen_h = h - 2 * pad_y

        # 1. Draw Monitor Frame & Bezel (Light Theme)
        # Stand
        stand_w, stand_h = 70, 20
        self.create_rectangle(w//2 - stand_w//2, h - pad_y + 10, w//2 + stand_w//2, h - pad_y + 10 + stand_h, fill="#cbd5e1", outline="#94a3b8")
        self.create_oval(w//2 - 60, h - pad_y + 24, w//2 + 60, h - pad_y + 34, fill="#94a3b8", outline="#64748b")

        # Monitor Bezel Outer Shadow
        self.create_rectangle(pad_x - 12, pad_y - 12, pad_x + screen_w + 12, pad_y + screen_h + 12, fill="#f1f5f9", outline="#cbd5e1", width=2)
        
        # Display Screen Area (Soft Blue/Slate gradient feel)
        self.create_rectangle(pad_x, pad_y, pad_x + screen_w, pad_y + screen_h, fill="#0f172a", outline="#334155", width=1)
        
        # Monitor Label
        self.create_text(w // 2, h // 2, text="PC SCREEN DISPLAY", fill="#475569", font=("Segoe UI", 12, "bold"))
        self.create_text(w // 2, h // 2 + 20, text=f"{len(self.zones)} Physical LEDs Configured", fill="#64748b", font=("Segoe UI", 9))

        # 2. Draw Sampling Zones (subtle dashed rectangles)
        for zone in self.zones:
            cx = pad_x + zone.norm_x * screen_w
            cy = pad_y + zone.norm_y * screen_h
            zw = (zone.norm_w * screen_w) / 2
            zh = (zone.norm_h * screen_h) / 2
            
            # Subtle zone outline
            self.create_rectangle(cx - zw, cy - zh, cx + zw, cy + zh, outline="#38bdf8", width=1, dash=(2, 4))

        # 3. Draw Physical LED Dots
        dot_r = 6
        show_numbers = (len(self.zones) <= 120) # Only display numbers if clean to read

        for zone in self.zones:
            idx = zone.led_index
            cx = pad_x + zone.norm_x * screen_w
            cy = pad_y + zone.norm_y * screen_h

            # Determine LED Color (live or default purple)
            fill_color = "#7c3aed" # Default PixelMatrix purple
            if self.live_colors and len(self.live_colors) >= (idx + 1) * 3:
                r = self.live_colors[idx * 3]
                g = self.live_colors[idx * 3 + 1]
                b = self.live_colors[idx * 3 + 2]
                fill_color = f"#{r:02x}{g:02x}{b:02x}"

            outline_color = "#ffffff"
            width = 1.5

            # Highlight selected / test LED
            if self.selected_led_index is not None and self.selected_led_index == idx:
                outline_color = "#f59e0b" # Golden amber highlight
                width = 3
                dot_r_cur = dot_r + 3
            else:
                dot_r_cur = dot_r

            self.create_oval(cx - dot_r_cur, cy - dot_r_cur, cx + dot_r_cur, cy + dot_r_cur, fill=fill_color, outline=outline_color, width=width)

            # Draw small number label if appropriate
            if show_numbers:
                # Place label slightly offset towards the outside
                ox, oy = cx, cy
                if zone.side == 'top': oy -= 14
                elif zone.side == 'bottom': oy += 14
                elif zone.side == 'left': ox -= 16
                elif zone.side == 'right': ox += 16
                self.create_text(ox, oy, text=str(idx + 1), fill="#64748b", font=("Segoe UI", 7))
