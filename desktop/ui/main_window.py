"""
PixelMatrix Screen Sync - Desktop Controller GUI
Modern, clean, light-themed desktop application with real-time screen capture,
dynamic 4-side perimeter LED layout editor, calibration suite, and diagnostics.
Developed by Chetan Gavali (@chetanngavali).
"""

import sys
import os
import time
import asyncio
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np

from desktop.capture.screen_capture import ScreenCaptureEngine
from desktop.mapping.layout_engine import LayoutEngine, SamplingZone
from desktop.color.color_processor import ColorProcessor
from desktop.network.ws_client import ScreenSyncWebSocketClient
from desktop.config.config_manager import ConfigManager
from desktop.ui.layout_canvas import LayoutCanvas
from desktop.network.discovery import discover_esp, get_esp_info

class ScreenSyncApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("PixelMatrix - Dynamic Screen Sync Ambilight")
        self.geometry("1180x820")
        self.minsize(980, 720)
        self.configure(bg="#f8fafc")

        # Core Engines
        self.config_mgr = ConfigManager()
        self.layout_engine = LayoutEngine()
        self.color_processor = ColorProcessor()
        self.capture_engine = ScreenCaptureEngine()
        self.ws_client: ScreenSyncWebSocketClient = None

        # Synchronization & State
        self.is_syncing = False
        self._loop_thread = None
        self._async_loop: asyncio.AbstractEventLoop = None
        self._stop_event = threading.Event()
        
        # Telemetry metrics
        self.fps_capture = 0.0
        self.fps_process = 0.0
        self.fps_network = 0.0
        self.latency_ms = 0.0

        # Load persisted config into engines
        self._apply_persisted_config()

        # Build UI Components
        self._setup_styles()
        self._create_header()
        self._create_main_content()

        # Update layout zones initially
        self._update_layout()

        # Start periodic UI diagnostics refresh
        self.after(500, self._periodic_ui_refresh)
        # Automatically detect and verify ESP8266 on home Wi-Fi router
        self.after(800, self._start_auto_discovery)

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TLabel", background="#f8fafc", foreground="#0f172a", font=("Segoe UI", 10))
        style.configure("Card.TFrame", background="#ffffff", relief="flat")
        style.configure("Title.TLabel", font=("Segoe UI", 13, "bold"), foreground="#1e293b")
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), background="#7c3aed", foreground="#ffffff")

    def _apply_persisted_config(self):
        cfg = self.config_mgr.config
        self.layout_engine.top_count = cfg.get("top_count", 60)
        self.layout_engine.right_count = cfg.get("right_count", 40)
        self.layout_engine.bottom_count = cfg.get("bottom_count", 60)
        self.layout_engine.left_count = cfg.get("left_count", 40)
        self.layout_engine.start_corner = cfg.get("start_corner", "top-left")
        self.layout_engine.direction = cfg.get("direction", "clockwise")
        self.layout_engine.reverse_top = cfg.get("reverse_top", False)
        self.layout_engine.reverse_right = cfg.get("reverse_right", False)
        self.layout_engine.reverse_bottom = cfg.get("reverse_bottom", False)
        self.layout_engine.reverse_left = cfg.get("reverse_left", False)

        self.color_processor.brightness = cfg.get("brightness", 80)
        self.color_processor.saturation = cfg.get("saturation", 120)
        self.color_processor.intensity = cfg.get("intensity", 100)
        self.color_processor.set_gamma(cfg.get("gamma", 2.2))
        self.color_processor.smoothing = cfg.get("smoothing", "LOW")

    def _create_header(self):
        header = tk.Frame(self, bg="#ffffff", height=70, bd=1, relief="solid")
        header.pack(side="top", fill="x")

        # App Brand & Author
        brand_frame = tk.Frame(header, bg="#ffffff")
        brand_frame.pack(side="left", padx=24, pady=12)

        title_lbl = tk.Label(brand_frame, text="PixelMatrix Screen Sync", font=("Segoe UI", 16, "bold"), bg="#ffffff", fg="#7c3aed")
        title_lbl.pack(anchor="w")
        sub_lbl = tk.Label(brand_frame, text="Real-Time Ambilight & LED Layout Designer • by Chetan Gavali (@chetanngavali)", font=("Segoe UI", 9), bg="#ffffff", fg="#64748b")
        sub_lbl.pack(anchor="w")

        # Master Sync Toggle Button
        ctrl_frame = tk.Frame(header, bg="#ffffff")
        ctrl_frame.pack(side="right", padx=24, pady=12)

        self.btn_toggle_sync = tk.Button(
            ctrl_frame, text="▶ START SCREEN SYNC", font=("Segoe UI", 11, "bold"),
            bg="#7c3aed", fg="#ffffff", activebackground="#6d28d9", activeforeground="#ffffff",
            padx=20, pady=8, bd=0, relief="flat", cursor="hand2", command=self.toggle_screen_sync
        )
        self.btn_toggle_sync.pack(side="right")

        self.lbl_ws_status = tk.Label(ctrl_frame, text="● Disconnected", font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#ef4444")
        self.lbl_ws_status.pack(side="right", padx=16)

    def _create_main_content(self):
        container = tk.Frame(self, bg="#f8fafc")
        container.pack(fill="both", expand=True, padx=20, pady=16)

        # Left Column: Visual Canvas & Live Preview (60% width)
        left_col = tk.Frame(container, bg="#ffffff", bd=1, relief="solid")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 12))

        # Canvas Header
        canvas_hdr = tk.Frame(left_col, bg="#ffffff")
        canvas_hdr.pack(fill="x", padx=16, pady=12)
        tk.Label(canvas_hdr, text="Visual Layout & Screen Mapping", font=("Segoe UI", 12, "bold"), bg="#ffffff", fg="#1e293b").pack(side="left")
        self.lbl_total_leds = tk.Label(canvas_hdr, text="Total: 200 LEDs", font=("Segoe UI", 11, "bold"), bg="#ede9fe", fg="#7c3aed", padx=8, pady=2)
        self.lbl_total_leds.pack(side="right")

        # The Layout Canvas
        self.canvas = LayoutCanvas(left_col)
        self.canvas.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        self.canvas.on_led_clicked = self._on_canvas_led_clicked

        # Diagnostics Mini Bar
        self._create_telemetry_bar(left_col)

        # Right Column: Controls & Configuration Cards (40% width)
        right_col = tk.Frame(container, bg="#f8fafc", width=420)
        right_col.pack(side="right", fill="y", padx=(0, 0))
        right_col.pack_propagate(False)

        # Notebook Tabs: [Layout Designer] [Color & Tuning] [Calibration] [Network]
        notebook = ttk.Notebook(right_col)
        notebook.pack(fill="both", expand=True)

        tab_layout = tk.Frame(notebook, bg="#ffffff", padx=14, pady=14)
        tab_color = tk.Frame(notebook, bg="#ffffff", padx=14, pady=14)
        tab_calibrate = tk.Frame(notebook, bg="#ffffff", padx=14, pady=14)
        tab_network = tk.Frame(notebook, bg="#ffffff", padx=14, pady=14)

        notebook.add(tab_layout, text="Layout")
        notebook.add(tab_color, text="Colors")
        notebook.add(tab_calibrate, text="Calibration")
        notebook.add(tab_network, text="ESP & Network")

        self._build_layout_tab(tab_layout)
        self._build_color_tab(tab_color)
        self._build_calibrate_tab(tab_calibrate)
        self._build_network_tab(tab_network)

    def _create_telemetry_bar(self, parent):
        bar = tk.Frame(parent, bg="#f1f5f9", height=45, bd=1, relief="solid")
        bar.pack(fill="x", side="bottom", padx=16, pady=(0, 12))

        def add_metric(label_text, var_attr):
            f = tk.Frame(bar, bg="#f1f5f9")
            f.pack(side="left", expand=True, pady=6)
            tk.Label(f, text=label_text, font=("Segoe UI", 8), bg="#f1f5f9", fg="#64748b").pack()
            lbl = tk.Label(f, text="--", font=("Segoe UI", 10, "bold"), bg="#f1f5f9", fg="#0f172a")
            lbl.pack()
            setattr(self, var_attr, lbl)

        add_metric("Capture FPS", "disp_cap_fps")
        add_metric("Processing FPS", "disp_proc_fps")
        add_metric("Network FPS", "disp_net_fps")
        add_metric("Latency", "disp_latency")

    def _build_layout_tab(self, parent):
        # 4-Sided LED Counts
        tk.Label(parent, text="Perimeter LED Counts", font=("Segoe UI", 11, "bold"), bg="#ffffff", fg="#1e293b").pack(anchor="w", pady=(0, 8))

        def create_count_row(label_str, initial_val, attr_name):
            row = tk.Frame(parent, bg="#ffffff")
            row.pack(fill="x", pady=4)
            tk.Label(row, text=label_str, width=12, anchor="w", bg="#ffffff").pack(side="left")
            var = tk.IntVar(value=initial_val)
            spin = tk.Spinbox(row, from_=0, to=250, textvariable=var, width=6, command=self._on_layout_param_changed)
            spin.pack(side="left", padx=6)
            spin.bind("<KeyRelease>", lambda e: self._on_layout_param_changed())
            setattr(self, attr_name, var)

            # Side Reverse Checkbox
            rev_var = tk.BooleanVar(value=getattr(self.layout_engine, f"reverse_{label_str.lower()}"))
            chk = tk.Checkbutton(row, text="Reverse", variable=rev_var, bg="#ffffff", command=self._on_layout_param_changed)
            chk.pack(side="right")
            setattr(self, f"var_rev_{label_str.lower()}", rev_var)

        create_count_row("Top", self.layout_engine.top_count, "var_top")
        create_count_row("Right", self.layout_engine.right_count, "var_right")
        create_count_row("Bottom", self.layout_engine.bottom_count, "var_bottom")
        create_count_row("Left", self.layout_engine.left_count, "var_left")

        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=12)

        # Corner & Direction
        tk.Label(parent, text="Wiring Configuration", font=("Segoe UI", 11, "bold"), bg="#ffffff", fg="#1e293b").pack(anchor="w", pady=(0, 6))
        
        row_corner = tk.Frame(parent, bg="#ffffff")
        row_corner.pack(fill="x", pady=4)
        tk.Label(row_corner, text="Start Corner:", width=14, anchor="w", bg="#ffffff").pack(side="left")
        self.var_corner = tk.StringVar(value=self.layout_engine.start_corner)
        c_combo = ttk.Combobox(row_corner, textvariable=self.var_corner, values=LayoutEngine.START_CORNERS, state="readonly", width=16)
        c_combo.pack(side="left")
        c_combo.bind("<<ComboboxSelected>>", lambda e: self._on_layout_param_changed())

        row_dir = tk.Frame(parent, bg="#ffffff")
        row_dir.pack(fill="x", pady=4)
        tk.Label(row_dir, text="Direction:", width=14, anchor="w", bg="#ffffff").pack(side="left")
        self.var_dir = tk.StringVar(value=self.layout_engine.direction)
        d_combo = ttk.Combobox(row_dir, textvariable=self.var_dir, values=LayoutEngine.DIRECTIONS, state="readonly", width=16)
        d_combo.pack(side="left")
        d_combo.bind("<<ComboboxSelected>>", lambda e: self._on_layout_param_changed())

        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=12)

        # Monitor Selector
        tk.Label(parent, text="Screen Capture Source", font=("Segoe UI", 11, "bold"), bg="#ffffff", fg="#1e293b").pack(anchor="w", pady=(0, 6))
        self.var_monitor = tk.StringVar()
        mon_names = [d.name for d in self.capture_engine.displays]
        self.combo_monitor = ttk.Combobox(parent, textvariable=self.var_monitor, values=mon_names, state="readonly")
        self.combo_monitor.pack(fill="x", pady=4)
        if mon_names:
            self.combo_monitor.current(min(self.config_mgr.get("monitor_index", 0), len(mon_names) - 1))
        self.combo_monitor.bind("<<ComboboxSelected>>", self._on_monitor_changed)

        btn_save = tk.Button(parent, text="💾 Save Layout Configuration", bg="#ede9fe", fg="#7c3aed", font=("Segoe UI", 9, "bold"), bd=0, pady=6, cursor="hand2", command=self._save_config)
        btn_save.pack(fill="x", side="bottom", pady=8)

    def _build_color_tab(self, parent):
        tk.Label(parent, text="Color Tuning & Post-Processing", font=("Segoe UI", 11, "bold"), bg="#ffffff", fg="#1e293b").pack(anchor="w", pady=(0, 10))

        def create_slider(label_str, from_v, to_v, initial_v, attr_name, format_str="%d%%"):
            f = tk.Frame(parent, bg="#ffffff")
            f.pack(fill="x", pady=6)
            hdr = tk.Frame(f, bg="#ffffff")
            hdr.pack(fill="x")
            tk.Label(hdr, text=label_str, bg="#ffffff", font=("Segoe UI", 9, "bold")).pack(side="left")
            val_lbl = tk.Label(hdr, text=format_str % initial_v, bg="#ffffff", fg="#7c3aed", font=("Segoe UI", 9, "bold"))
            val_lbl.pack(side="right")
            var = tk.DoubleVar(value=initial_v)
            scale = tk.Scale(f, from_=from_v, to=to_v, orient="horizontal", variable=var, showvalue=0, bg="#ede9fe", highlightthickness=0)
            scale.pack(fill="x", pady=2)
            
            def on_change(v):
                val_lbl.config(text=format_str % float(v))
                setattr(self.color_processor, attr_name, float(v) if "gamma" in attr_name else int(float(v)))
            scale.config(command=on_change)
            setattr(self, f"var_{attr_name}", var)

        create_slider("Master Brightness", 0, 100, self.color_processor.brightness, "brightness")
        create_slider("Saturation Boost", 0, 200, self.color_processor.saturation, "saturation")
        create_slider("Color Intensity", 0, 200, self.color_processor.intensity, "intensity")
        create_slider("Gamma Correction", 1.0, 3.0, self.color_processor.gamma, "gamma", format_str="%.1f")
        create_slider("Black Threshold", 0, 50, self.color_processor.black_threshold, "black_threshold", format_str="%d")

        # Smoothing Combo
        f_smooth = tk.Frame(parent, bg="#ffffff")
        f_smooth.pack(fill="x", pady=8)
        tk.Label(f_smooth, text="Temporal Smoothing:", bg="#ffffff", font=("Segoe UI", 9, "bold")).pack(side="left")
        self.var_smoothing = tk.StringVar(value=self.color_processor.smoothing)
        s_combo = ttk.Combobox(f_smooth, textvariable=self.var_smoothing, values=["OFF", "LOW", "MEDIUM", "HIGH"], state="readonly", width=10)
        s_combo.pack(side="right")
        s_combo.bind("<<ComboboxSelected>>", lambda e: setattr(self.color_processor, "smoothing", self.var_smoothing.get()))

    def _build_calibrate_tab(self, parent):
        tk.Label(parent, text="Physical LED Verification Suite", font=("Segoe UI", 11, "bold"), bg="#ffffff", fg="#1e293b").pack(anchor="w", pady=(0, 6))
        tk.Label(parent, text="Verify wiring order and physical color accuracy.", font=("Segoe UI", 9), bg="#ffffff", fg="#64748b").pack(anchor="w", pady=(0, 12))

        # Solid Test Colors
        tk.Label(parent, text="Full Screen Test Colors", font=("Segoe UI", 10, "bold"), bg="#ffffff").pack(anchor="w", pady=4)
        c_row = tk.Frame(parent, bg="#ffffff")
        c_row.pack(fill="x", pady=4)
        
        colors = [("Red", "#ef4444", b"\xFF\x00\x00"), ("Green", "#22c55e", b"\x00\xFF\x00"), ("Blue", "#3b82f6", b"\x00\x00\xFF"), ("White", "#f8fafc", b"\xFF\xFF\xFF")]
        for name, hex_code, rgb_bytes in colors:
            btn = tk.Button(c_row, text=name, bg=hex_code, fg="#000000" if name=="White" else "#ffffff",
                            font=("Segoe UI", 9, "bold"), padx=10, pady=4, bd=0, relief="flat", cursor="hand2",
                            command=lambda b=rgb_bytes: self._send_solid_test_frame(b))
            btn.pack(side="left", padx=4, expand=True, fill="x")

        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=14)

        # Individual LED Probe
        tk.Label(parent, text="Probe Single LED", font=("Segoe UI", 10, "bold"), bg="#ffffff").pack(anchor="w", pady=4)
        probe_row = tk.Frame(parent, bg="#ffffff")
        probe_row.pack(fill="x", pady=4)
        tk.Label(probe_row, text="LED # (1..N):", bg="#ffffff").pack(side="left")
        self.var_probe_idx = tk.IntVar(value=1)
        spin_probe = tk.Spinbox(probe_row, from_=1, to=500, textvariable=self.var_probe_idx, width=6)
        spin_probe.pack(side="left", padx=8)
        btn_probe = tk.Button(probe_row, text="Illuminate", bg="#7c3aed", fg="#ffffff", bd=0, padx=12, pady=4, cursor="hand2", command=self._probe_single_led)
        btn_probe.pack(side="left")

        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=14)

        # Automatic Chase Sequence Test
        tk.Label(parent, text="Chaser Sequence Test", font=("Segoe UI", 10, "bold"), bg="#ffffff").pack(anchor="w", pady=4)
        self.btn_seq_test = tk.Button(parent, text="▶ Run 1..N Sequential Test", bg="#ede9fe", fg="#7c3aed", font=("Segoe UI", 10, "bold"), bd=0, pady=8, cursor="hand2", command=self._toggle_chaser_test)
        self.btn_seq_test.pack(fill="x", pady=4)
        self._chaser_running = False

    def _build_network_tab(self, parent):
        # Scrollable Canvas for Network Tab
        canvas = tk.Canvas(parent, bg="#ffffff", highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scroll_content = tk.Frame(canvas, bg="#ffffff")

        scroll_content.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- Section 1: Screen Sync Connection ---
        tk.Label(scroll_content, text="1. ESP8266 Screen Sync Connection", font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#1e293b").pack(anchor="w", pady=(0, 4))

        row_ip = tk.Frame(scroll_content, bg="#ffffff")
        row_ip.pack(fill="x", pady=4)
        tk.Label(row_ip, text="ESP IP Address:", width=13, anchor="w", bg="#ffffff", font=("Segoe UI", 9)).pack(side="left")
        self.var_esp_ip = tk.StringVar(value=self.config_mgr.get("esp_ip", "192.168.1.31"))
        entry_ip = tk.Entry(row_ip, textvariable=self.var_esp_ip, width=15)
        entry_ip.pack(side="left", padx=4)
        btn_find = tk.Button(row_ip, text="🔍 Auto-Find", bg="#ede9fe", fg="#6d28d9", font=("Segoe UI", 8, "bold"), bd=1, relief="solid", padx=6, pady=1, cursor="hand2", command=self._start_auto_discovery)
        btn_find.pack(side="left", padx=2)

        row_port = tk.Frame(scroll_content, bg="#ffffff")
        row_port.pack(fill="x", pady=4)
        tk.Label(row_port, text="WS Port:", width=13, anchor="w", bg="#ffffff", font=("Segoe UI", 9)).pack(side="left")
        self.var_esp_port = tk.IntVar(value=self.config_mgr.get("esp_ws_port", 81))
        entry_port = tk.Entry(row_port, textvariable=self.var_esp_port, width=8)
        entry_port.pack(side="left", padx=4)

        btn_conn = tk.Button(scroll_content, text="🔌 Connect / Disconnect", bg="#f1f5f9", fg="#0f172a", font=("Segoe UI", 9, "bold"), bd=1, relief="solid", pady=4, cursor="hand2", command=self._toggle_manual_connection)
        btn_conn.pack(fill="x", pady=(4, 6))

        # Live Network Info Card
        self.net_card = tk.Frame(scroll_content, bg="#f8fafc", bd=1, relief="solid", padx=8, pady=6)
        self.net_card.pack(fill="x", pady=(0, 10))
        
        self.lbl_net_status = tk.Label(self.net_card, text="Status: Disconnected", font=("Segoe UI", 8, "bold"), bg="#f8fafc", fg="#64748b", anchor="w")
        self.lbl_net_status.pack(fill="x")
        
        self.lbl_net_gateway = tk.Label(self.net_card, text="Default Gateway: --", font=("Segoe UI", 8), bg="#f8fafc", fg="#64748b", anchor="w")
        self.lbl_net_gateway.pack(fill="x")

        self.lbl_net_mac = tk.Label(self.net_card, text="ESP MAC: --", font=("Segoe UI", 8), bg="#f8fafc", fg="#64748b", anchor="w")
        self.lbl_net_mac.pack(fill="x")

        ttk.Separator(scroll_content, orient="horizontal").pack(fill="x", pady=6)

        # --- Section 2: Wi-Fi Setup Guide & Network Layout ---
        tk.Label(scroll_content, text="2. Network Layout & Wi-Fi Connection Guide", font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#7c3aed").pack(anchor="w", pady=(0, 4))

        info_box = tk.Frame(scroll_content, bg="#f8fafc", bd=1, relief="solid", padx=10, pady=8)
        info_box.pack(fill="x", pady=4)

        guide_text = (
            "📌 STEP 1 (First-Time / New Wi-Fi Setup):\n"
            "  • If ESP has no saved Wi-Fi, it broadcasts hotspot:\n"
            "    SSID: PixelMatrix-Setup\n"
            "    Password: pixel1234\n"
            "  • Connect your PC or Phone Wi-Fi to 'PixelMatrix-Setup'.\n\n"
            "📌 STEP 2 (Save Home Wi-Fi into ESP Flash):\n"
            "  • Enter your Home Router SSID & Password below.\n"
            "  • Click '📡 Save to ESP' (stored in ESP hardware flash).\n\n"
            "📌 STEP 3 (Start Screen Sync on Home Wi-Fi):\n"
            "  • Reconnect PC to your Home Wi-Fi router.\n"
            "  • Click '🔍 Auto-Find', then '▶ START SCREEN SYNC'!"
        )
        tk.Label(info_box, text=guide_text, justify="left", font=("Segoe UI", 8), bg="#f8fafc", fg="#334155").pack(anchor="w")

        ttk.Separator(scroll_content, orient="horizontal").pack(fill="x", pady=6)

        # --- Section 3: Configure Wi-Fi on ESP Provisioner ---
        tk.Label(scroll_content, text="3. Configure Wi-Fi on ESP8266", font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#1e293b").pack(anchor="w", pady=(0, 4))

        row_prov_ip = tk.Frame(scroll_content, bg="#ffffff")
        row_prov_ip.pack(fill="x", pady=3)
        tk.Label(row_prov_ip, text="ESP Target IP:", width=13, anchor="w", bg="#ffffff", font=("Segoe UI", 9)).pack(side="left")
        self.var_prov_ip = tk.StringVar(value="192.168.4.1")
        tk.Entry(row_prov_ip, textvariable=self.var_prov_ip, width=15).pack(side="left", padx=4)
        tk.Label(row_prov_ip, text="(192.168.4.1 in AP mode)", font=("Segoe UI", 8), fg="#64748b", bg="#ffffff").pack(side="left")

        row_ssid = tk.Frame(scroll_content, bg="#ffffff")
        row_ssid.pack(fill="x", pady=3)
        tk.Label(row_ssid, text="Router SSID:", width=13, anchor="w", bg="#ffffff", font=("Segoe UI", 9)).pack(side="left")
        self.var_wifi_ssid = tk.StringVar()
        tk.Entry(row_ssid, textvariable=self.var_wifi_ssid, width=20).pack(side="left", padx=4)

        row_pass = tk.Frame(scroll_content, bg="#ffffff")
        row_pass.pack(fill="x", pady=3)
        tk.Label(row_pass, text="Wi-Fi Password:", width=13, anchor="w", bg="#ffffff", font=("Segoe UI", 9)).pack(side="left")
        self.var_wifi_pass = tk.StringVar()
        tk.Entry(row_pass, textvariable=self.var_wifi_pass, show="*", width=20).pack(side="left", padx=4)

        self.lbl_prov_status = tk.Label(scroll_content, text="", font=("Segoe UI", 8), bg="#ffffff", fg="#64748b", wraplength=340, justify="left")
        self.lbl_prov_status.pack(fill="x", pady=(2, 6))

        btn_save_wifi = tk.Button(scroll_content, text="📡 Save Wi-Fi to ESP8266 (Permanent Flash)", bg="#7c3aed", fg="#ffffff", font=("Segoe UI", 9, "bold"), bd=0, pady=6, cursor="hand2", command=self._send_wifi_to_esp)
        btn_save_wifi.pack(fill="x", pady=(0, 12))

    def _on_layout_param_changed(self):
        try:
            self.layout_engine.top_count = max(0, self.var_top.get())
            self.layout_engine.right_count = max(0, self.var_right.get())
            self.layout_engine.bottom_count = max(0, self.var_bottom.get())
            self.layout_engine.left_count = max(0, self.var_left.get())
            self.layout_engine.reverse_top = self.var_rev_top.get()
            self.layout_engine.reverse_right = self.var_rev_right.get()
            self.layout_engine.reverse_bottom = self.var_rev_bottom.get()
            self.layout_engine.reverse_left = self.var_rev_left.get()
            self.layout_engine.start_corner = self.var_corner.get()
            self.layout_engine.direction = self.var_dir.get()
            self._update_layout()
        except Exception:
            pass

    def _update_layout(self):
        total = self.layout_engine.total_leds
        self.lbl_total_leds.config(text=f"Total: {total} LEDs")
        zones = self.layout_engine.generate_zones(1920, 1080)
        self.canvas.set_zones(zones)

    def _on_monitor_changed(self, event):
        idx = self.combo_monitor.current()
        self.capture_engine.selected_display_index = idx
        self.config_mgr.set("monitor_index", idx)

    def _on_canvas_led_clicked(self, idx: int):
        self.canvas.set_selected_led(idx)
        self.var_probe_idx.set(idx + 1)
        self._probe_single_led()

    def _save_config(self):
        self.config_mgr.set("top_count", self.layout_engine.top_count)
        self.config_mgr.set("right_count", self.layout_engine.right_count)
        self.config_mgr.set("bottom_count", self.layout_engine.bottom_count)
        self.config_mgr.set("left_count", self.layout_engine.left_count)
        self.config_mgr.set("reverse_top", self.layout_engine.reverse_top)
        self.config_mgr.set("reverse_right", self.layout_engine.reverse_right)
        self.config_mgr.set("reverse_bottom", self.layout_engine.reverse_bottom)
        self.config_mgr.set("reverse_left", self.layout_engine.reverse_left)
        self.config_mgr.set("start_corner", self.layout_engine.start_corner)
        self.config_mgr.set("direction", self.layout_engine.direction)
        self.config_mgr.set("esp_ip", self.var_esp_ip.get())
        self.config_mgr.set("esp_ws_port", self.var_esp_port.get())
        self.config_mgr.set("brightness", self.color_processor.brightness)
        self.config_mgr.set("saturation", self.color_processor.saturation)
        self.config_mgr.set("intensity", self.color_processor.intensity)
        self.config_mgr.set("gamma", self.color_processor.gamma)
        self.config_mgr.set("smoothing", self.color_processor.smoothing)
        self.config_mgr.save()
        messagebox.showinfo("PixelMatrix", "Layout configuration saved successfully.")

    def _probe_single_led(self):
        idx = max(0, self.var_probe_idx.get() - 1)
        total = self.layout_engine.total_leds
        if total == 0:
            return
        
        # Build test frame where only LED idx is White, all others Black
        frame_bytes = bytearray(total * 3)
        if idx < total:
            frame_bytes[idx * 3] = 255
            frame_bytes[idx * 3 + 1] = 255
            frame_bytes[idx * 3 + 2] = 255
        self.canvas.set_selected_led(idx)
        self.canvas.update_live_colors(bytes(frame_bytes))
        if self.ws_client and self.ws_client.is_connected:
            self.ws_client.queue_frame(bytes(frame_bytes), total)

    def _send_solid_test_frame(self, rgb_3bytes: bytes):
        total = self.layout_engine.total_leds
        frame_bytes = rgb_3bytes * total
        self.canvas.update_live_colors(frame_bytes)
        if self.ws_client and self.ws_client.is_connected:
            self.ws_client.queue_frame(frame_bytes, total)

    def _toggle_chaser_test(self):
        if self._chaser_running:
            self._chaser_running = False
            self.btn_seq_test.config(text="▶ Run 1..N Sequential Test", bg="#ede9fe")
        else:
            self._chaser_running = True
            self.btn_seq_test.config(text="⏹ Stop Sequential Test", bg="#fee2e2")
            threading.Thread(target=self._chaser_worker, daemon=True).start()

    def _chaser_worker(self):
        total = self.layout_engine.total_leds
        current = 0
        while self._chaser_running and total > 0:
            frame_bytes = bytearray(total * 3)
            # Leading dot is white, trailing 3 are cyan
            for tail in range(4):
                pos = (current - tail) % total
                if tail == 0:
                    frame_bytes[pos * 3] = 255
                    frame_bytes[pos * 3 + 1] = 255
                    frame_bytes[pos * 3 + 2] = 255
                else:
                    frame_bytes[pos * 3 + 1] = 180
                    frame_bytes[pos * 3 + 2] = 220
            
            self.canvas.update_live_colors(bytes(frame_bytes))
            if self.ws_client and self.ws_client.is_connected:
                self.ws_client.queue_frame(bytes(frame_bytes), total)
            current = (current + 1) % total
            time.sleep(0.04)

    def _toggle_manual_connection(self):
        if self.ws_client and self.ws_client.is_connected:
            asyncio.run_coroutine_threadsafe(self.ws_client.disconnect(), self._async_loop)
        else:
            self._init_network_loop()

    def _init_network_loop(self):
        if self._async_loop is None:
            self._async_loop = asyncio.new_event_loop()
            t = threading.Thread(target=self._run_asyncio_loop, args=(self._async_loop,), daemon=True)
            t.start()

        host = self.var_esp_ip.get().strip()
        port = self.var_esp_port.get()
        if self.ws_client:
            try:
                asyncio.run_coroutine_threadsafe(self.ws_client.disconnect(), self._async_loop)
            except Exception:
                pass
        self.ws_client = ScreenSyncWebSocketClient(host=host, port=port)
        self.ws_client.on_connection_change = self._on_ws_status_change
        asyncio.run_coroutine_threadsafe(self.ws_client.connect(), self._async_loop)

    def _run_asyncio_loop(self, loop: asyncio.AbstractEventLoop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    def _on_ws_status_change(self, connected: bool, message: str):
        self.after(0, lambda: self._update_ws_ui(connected, message))

    def _update_ws_ui(self, connected: bool, message: str):
        if connected:
            self.lbl_ws_status.config(text="● Connected to ESP", fg="#22c55e")
        else:
            self.lbl_ws_status.config(text=f"● {message}", fg="#ef4444")

    def _start_auto_discovery(self):
        self.lbl_ws_status.config(text="● Searching for ESP on Wi-Fi...", fg="#f59e0b")
        def _worker():
            current_ip = self.var_esp_ip.get().strip()
            found_ip = discover_esp(fallback_ip=current_ip)
            if found_ip:
                self.after(0, lambda: self._on_esp_discovered(found_ip))
            else:
                self.after(0, lambda: self.lbl_ws_status.config(text="● ESP not found (Check Wi-Fi)", fg="#ef4444"))
        threading.Thread(target=_worker, daemon=True).start()

    def _on_esp_discovered(self, ip: str):
        self.var_esp_ip.set(ip)
        self.config_mgr.set("esp_ip", ip)
        self.lbl_ws_status.config(text=f"● Discovered ESP at {ip}", fg="#22c55e")
        def _fetch_info():
            info = get_esp_info(ip)
            if info:
                st = info.get("wifiStatus", "Connected")
                gw = info.get("gateway", "N/A")
                mac = info.get("mac", "N/A")
                self.after(0, lambda: self._update_net_card(st, gw, mac))
        threading.Thread(target=_fetch_info, daemon=True).start()

    def _update_net_card(self, status: str, gateway: str, mac: str):
        self.lbl_net_status.config(text=f"Status: {status}", fg="#16a34a" if "Connected" in status else "#f59e0b")
        self.lbl_net_gateway.config(text=f"Default Gateway: {gateway}")
        self.lbl_net_mac.config(text=f"ESP MAC: {mac}")

    def _send_wifi_to_esp(self):
        target_ip = self.var_prov_ip.get().strip()
        ssid = self.var_wifi_ssid.get().strip()
        pwd = self.var_wifi_pass.get()
        if not ssid:
            messagebox.showwarning("Missing SSID", "Please enter your Wi-Fi SSID / Network Name.")
            return

        self.lbl_prov_status.config(text=f"Sending credentials to http://{target_ip}/api/wifi...", fg="#f59e0b")

        def _worker():
            import urllib.request
            import json
            url = f"http://{target_ip}/api/wifi"
            payload = json.dumps({"ssid": ssid, "password": pwd}).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=5.0) as resp:
                    if resp.status == 200:
                        msg = f"✓ Saved! ESP is connecting to '{ssid}'.\nNow reconnect PC to '{ssid}' & click 'Auto-Find'!"
                        self.after(0, lambda: self.lbl_prov_status.config(text=msg, fg="#16a34a"))
                    else:
                        self.after(0, lambda: self.lbl_prov_status.config(text=f"Error: HTTP {resp.status}", fg="#dc2626"))
            except Exception as e:
                err_msg = f"Failed to reach ESP: {e}\nEnsure your PC Wi-Fi is connected to 'PixelMatrix-Setup'!"
                self.after(0, lambda: self.lbl_prov_status.config(text=err_msg, fg="#dc2626"))

        threading.Thread(target=_worker, daemon=True).start()

    def toggle_screen_sync(self):
        if self.is_syncing:
            self.stop_screen_sync()
        else:
            self.start_screen_sync()

    def start_screen_sync(self):
        if self.is_syncing:
            return
        self.is_syncing = True
        self._stop_event.clear()
        self.btn_toggle_sync.config(text="⏹ STOP SCREEN SYNC", bg="#dc2626")

        # Connect WebSocket if not yet connected
        if self.ws_client is None or not self.ws_client.is_connected:
            self._init_network_loop()

        # Start Screen Capture Engine
        mon_idx = self.combo_monitor.current()
        self.capture_engine.start(display_idx=mon_idx)

        # Launch High-Performance Capture & Processing Worker Thread
        self._loop_thread = threading.Thread(target=self._capture_worker, daemon=True)
        self._loop_thread.start()

    def stop_screen_sync(self):
        self.is_syncing = False
        self._stop_event.set()
        self.btn_toggle_sync.config(text="▶ START SCREEN SYNC", bg="#7c3aed")
        self.capture_engine.stop()

    def _capture_worker(self):
        """
        Ultra-low latency Screen Capture -> Mapping -> Color Extraction -> WS Pipeline
        Operates targeting 35 FPS for rock-solid stability and zero buffer bloat on ESP8266.
        """
        zones = self.canvas.zones
        target_fps = self.config_mgr.get("target_fps", 35)
        frame_time = 1.0 / target_fps
        
        frames_cap = 0
        frames_proc = 0
        last_metric_time = time.perf_counter()

        while not self._stop_event.is_set():
            t0 = time.perf_counter()

            try:
                # 1. Grab screen frame
                frame = self.capture_engine.capture_frame()
                if frame is None:
                    time.sleep(0.005)
                    continue
                frames_cap += 1

                # 2. Extract colors & process
                rgb_bytes = self.color_processor.extract_and_process(frame, zones)
                frames_proc += 1

                # 3. Stream to ESP8266
                if self.ws_client and self.ws_client.is_connected:
                    self.ws_client.queue_frame(rgb_bytes, len(zones))

                # 4. Update UI Canvas
                if frames_proc % 2 == 0:
                    self.canvas.update_live_colors(rgb_bytes)

            except Exception as err:
                time.sleep(0.01)
                continue

            # 4. Update UI Canvas (downsampled to 30 FPS to preserve GUI performance)
            if frames_proc % 2 == 0:
                self.canvas.update_live_colors(rgb_bytes)

            # 5. Measure Latency & FPS
            dt = time.perf_counter() - t0
            self.latency_ms = dt * 1000.0

            now = time.perf_counter()
            if now - last_metric_time >= 1.0:
                self.fps_capture = frames_cap / (now - last_metric_time)
                self.fps_process = frames_proc / (now - last_metric_time)
                self.fps_network = (self.ws_client.frames_sent if self.ws_client else 0) / (now - last_metric_time)
                if self.ws_client:
                    self.ws_client.frames_sent = 0
                frames_cap = 0
                frames_proc = 0
                last_metric_time = now

            # Sleep remainder of frame budget
            rem = frame_time - (time.perf_counter() - t0)
            if rem > 0:
                time.sleep(rem)

    def _periodic_ui_refresh(self):
        if self.is_syncing:
            self.disp_cap_fps.config(text=f"{self.fps_capture:.0f} FPS")
            self.disp_proc_fps.config(text=f"{self.fps_process:.0f} FPS")
            self.disp_net_fps.config(text=f"{self.fps_network:.0f} FPS")
            self.disp_latency.config(text=f"~{self.latency_ms:.1f} ms")
        self.after(500, self._periodic_ui_refresh)

if __name__ == "__main__":
    app = ScreenSyncApp()
    app.mainloop()
