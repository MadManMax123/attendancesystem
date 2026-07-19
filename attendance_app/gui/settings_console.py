from __future__ import annotations

import platform
import socket
import threading

import psutil
import requests
import tkinter as tk
from ping3 import ping

from ..services.logger import log_action
from .theme_widgets import themed_label, themed_labelframe, style_dialog_window


def show_settings_console(root, state) -> None:
    config = state.config
    settings_win = tk.Toplevel(root)
    style_dialog_window(settings_win, config, "Settings Console", "560x620", (540, 600))

    try:
        from PIL import Image, ImageTk

        logo_img = Image.open(config.root_dir / config.logo_file).resize((60, 60))
        logo_photo = ImageTk.PhotoImage(logo_img)
        tk.Label(settings_win, image=logo_photo, bg=config.theme["BG"]).place(relx=0.97, y=10, anchor="ne")
        settings_win.logo_img = logo_photo
    except Exception:
        pass

    themed_label(settings_win, config, "STATS", fg=config.theme["ACCENT_2"], font=tuple(config.theme["TITLE_FONT"])).pack(pady=(18, 12))

    sys_frame = themed_labelframe(settings_win, config, "System Info")
    sys_frame.pack(fill="x", padx=14, pady=8)
    net_frame = themed_labelframe(settings_win, config, "Network Info")
    net_frame.pack(fill="x", padx=14, pady=8)
    perf_frame = themed_labelframe(settings_win, config, "Performance")
    perf_frame.pack(fill="x", padx=14, pady=8)

    sys_labels = {key: themed_label(sys_frame, config, "", bg=config.theme["PANEL_BG"]) for key in ["Python Ver", "Platform", "Hostname", "Local IP", "MAC", "External IP"]}
    net_labels = {key: themed_label(net_frame, config, "", bg=config.theme["PANEL_BG"]) for key in ["Upload", "Download", "Ping"]}
    perf_labels = {key: themed_label(perf_frame, config, "", bg=config.theme["PANEL_BG"]) for key in ["CPU Usage", "Memory Usage", "Disk Usage"]}

    for label in list(sys_labels.values()) + list(net_labels.values()) + list(perf_labels.values()):
        label.pack(anchor="w")

    def update() -> None:
        if not settings_win.winfo_exists():
            return
        sys_labels["Python Ver"].config(text=f"Python Version: {platform.python_version()}")
        sys_labels["Platform"].config(text=f"Platform: {platform.system()} {platform.release()}")
        sys_labels["Hostname"].config(text=f"Hostname: {socket.gethostname()}")
        try:
            sys_labels["Local IP"].config(text=f"Local IP: {socket.gethostbyname(socket.gethostname())}")
        except Exception:
            sys_labels["Local IP"].config(text="Local IP: N/A")

        mac_address = "N/A"
        for _iface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if getattr(psutil, "AF_LINK", None) == addr.family:
                    mac_address = addr.address
                    break
            if mac_address != "N/A":
                break
        sys_labels["MAC"].config(text=f"MAC: {mac_address}")

        try:
            external_ip = requests.get("https://api.ipify.org", timeout=2).text
        except Exception:
            external_ip = "N/A"
        sys_labels["External IP"].config(text=f"External IP: {external_ip}")

        net_io = psutil.net_io_counters()
        net_labels["Upload"].config(text=f"Upload: {net_io.bytes_sent / (1024 * 1024):.2f} MB")
        net_labels["Download"].config(text=f"Download: {net_io.bytes_recv / (1024 * 1024):.2f} MB")

        try:
            latency = ping("8.8.8.8", timeout=1)
            latency_ms = f"{round(latency * 1000, 2)} ms" if latency else "Timeout"
        except Exception:
            latency_ms = "Error"
        net_labels["Ping"].config(text=f"Ping (8.8.8.8): {latency_ms}")

        perf_labels["CPU Usage"].config(text=f"CPU Usage: {psutil.cpu_percent()}%")
        perf_labels["Memory Usage"].config(text=f"Memory Usage: {psutil.virtual_memory().percent}%")
        perf_labels["Disk Usage"].config(text=f"Disk Usage: {psutil.disk_usage('/').percent}%")
        settings_win.after(2000, update)

    update()
    threading.Thread(target=update, daemon=True).start()

    themed_label(settings_win, config, "Made by Satyaki Bandopadhyay", fg=config.theme["MUTED"], font=tuple(config.theme["MONO_FONT"])).pack(side="bottom", pady=12)
    log_action(state.log_path, "Settings console opened", sink=state.log_sink)
