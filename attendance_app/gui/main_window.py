from __future__ import annotations

from datetime import datetime
from pathlib import Path
import csv
import os
import tkinter as tk
from tkinter import messagebox

from PIL import Image, ImageTk

from ..services.logger import log_action, read_recent
from ..services.attendance_store import ensure_store
from .theme_widgets import (
    build_session_header,
    configure_styles,
    themed_button,
    themed_entry,
    themed_frame,
)


def build_main_window(root: tk.Tk, state) -> None:
    config = state.config
    theme = config.theme
    configure_styles(root, config)
    build_session_header(root, config)

    ensure_store(state.csv_path)

    log_text: tk.Text | None = None

    def append_log(entry: str) -> None:
        if log_text is None or not log_text.winfo_exists():
            return
        log_text.config(state="normal")
        log_text.insert("end", entry + "\n")
        log_text.see("end")
        log_text.config(state="disabled")

    state.log_sink = append_log

    quick_entry_frame = themed_frame(root, config, border=True)
    quick_entry_frame.place(relx=0.02, rely=0.12, anchor="nw", width=320, relheight=0.80)

    tk.Label(quick_entry_frame, text="Quick Entry", fg=theme["ACCENT"], bg=theme["PANEL_BG"], font=tuple(theme["TITLE_FONT"])).pack(pady=(16, 8))

    tk.Label(quick_entry_frame, text="Activity:", fg=theme["TEXT"], bg=theme["PANEL_BG"], font=tuple(theme["MONO_FONT"])).pack(pady=(10, 5))
    activity_entry = themed_entry(quick_entry_frame, config, width=25)
    activity_entry.pack(pady=5, padx=10)

    tk.Label(quick_entry_frame, text="Admission Number:", fg=theme["TEXT"], bg=theme["PANEL_BG"], font=tuple(theme["MONO_FONT"])).pack(pady=(20, 5))
    adm_entry = themed_entry(quick_entry_frame, config, width=25)
    adm_entry.pack(pady=5, padx=10)

    def quick_submit() -> None:
        activity = activity_entry.get().strip() or config.session_name
        admission_number = adm_entry.get().strip()
        if not admission_number:
            messagebox.showerror("Missing Data", "Please enter an admission number.")
            return

        member = state.sheets_service.get_member_by_admission(admission_number)
        if member is None:
            messagebox.showerror("Not Found", f"Member not found with Admission Number: {admission_number}")
            adm_entry.delete(0, tk.END)
            adm_entry.focus()
            return

        state.sheets_service.mark_attendance(state.csv_path, member, "Present", activity)
        log_action(state.log_path, f"Quick entry: {member['name']}, Adm: {admission_number}, Activity: {activity}", sink=state.log_sink)
        messagebox.showinfo("Success", f"Attendance marked for {member['name']}")
        adm_entry.delete(0, tk.END)
        adm_entry.focus()

    themed_button(quick_entry_frame, config, "Submit", quick_submit, width=15).pack(pady=20)
    adm_entry.bind("<Return>", lambda _event: quick_submit())

    instructions = tk.Label(
        quick_entry_frame,
        text="1. Enter activity once\n2. Scan/type admission numbers\n3. Press Enter or Submit",
        fg=theme["MUTED"],
        bg=theme["PANEL_BG"],
        font=tuple(theme["MONO_FONT"]),
        justify="left",
    )
    instructions.pack(pady=(30, 10))

    log_frame = themed_frame(root, config, border=True)
    log_frame.place(relx=0.98, rely=0.12, anchor="ne", width=350, relheight=0.80)

    tk.Label(log_frame, text="Activity Log", fg=theme["ACCENT_2"], bg=theme["PANEL_BG"], font=tuple(theme["MONO_FONT"])).pack(pady=(14, 6))
    log_text = tk.Text(log_frame, wrap="word", bg=theme["CARD_BG"], fg=theme["TEXT"], font=tuple(theme["MONO_FONT"]), state="disabled", relief="flat", padx=8, pady=8, highlightthickness=0)
    log_text.pack(expand=True, fill="both", padx=10, pady=(6, 10))

    def refresh_log_view() -> None:
        if not os.path.exists(state.log_path):
            return
        log_text.config(state="normal")
        log_text.delete("1.0", tk.END)
        for line in read_recent(state.log_path, limit=100):
            log_text.insert(tk.END, line)
        log_text.see(tk.END)
        log_text.config(state="disabled")

    def auto_refresh_log() -> None:
        refresh_log_view()
        root.after(2000, auto_refresh_log)

    auto_refresh_log()

    center_frame = themed_frame(root, config, bg=theme["BG"])
    center_frame.place(relx=0.5, rely=0.55, anchor="center")

    crest_path = Path(config.root_dir) / config.crest_file
    logo_path = Path(config.root_dir) / config.logo_file

    try:
        crest_img = Image.open(crest_path).resize((80, 80))
        crest_photo = ImageTk.PhotoImage(crest_img)
        crest_label = tk.Label(center_frame, image=crest_photo, bg=theme["BG"])
        crest_label.image = crest_photo
        crest_label.pack(pady=(0, 10))
    except Exception as exc:
        log_action(state.log_path, f"Failed to load crest: {exc}", sink=state.log_sink)

    try:
        logo_img = Image.open(logo_path).resize((180, 180))
        logo_photo = ImageTk.PhotoImage(logo_img)
        logo_canvas = tk.Canvas(center_frame, width=180, height=180, bg=theme["BG"], highlightthickness=0)
        logo_canvas.pack(pady=20)
        logo_canvas.create_image(90, 90, image=logo_photo)
        logo_canvas.image = logo_photo
    except Exception as exc:
        log_action(state.log_path, f"Error loading logo: {exc}", sink=state.log_sink)

    tk.Label(center_frame, text=f"{config.club_name_upper}\nATTENDANCE SYSTEM", font=tuple(theme["TITLE_FONT"]), fg=theme["TEXT"], bg=theme["BG"]).pack(pady=10)

    time_label = tk.Label(center_frame, text="", font=tuple(theme["SUBTITLE_FONT"]), fg=theme["ACCENT"], bg=theme["BG"])
    time_label.pack(pady=(0, 5))

    def update_time() -> None:
        time_label.config(text=f"Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        root.after(1000, update_time)

    update_time()

    button_style = {
        "width": 20,
        "font": tuple(theme["MONO_FONT"]),
        "bg": theme["BUTTON_BG"],
        "fg": theme["TEXT"],
        "activebackground": theme["BUTTON_ACTIVE"],
        "activeforeground": theme["TEXT"],
        "relief": "ridge",
        "bd": 3,
    }

    def open_admin() -> None:
        from .admin_console import show_admin_console

        show_admin_console(root, state)

    def open_members() -> None:
        from .member_console import show_member_console

        show_member_console(root, state)

    def open_voting() -> None:
        from .voting_console import show_voting_console

        show_voting_console(root, state)

    themed_button(center_frame, config, "Admin", open_admin, width=20).pack(pady=15)
    themed_button(center_frame, config, "Members", open_members, width=20).pack(pady=15)
    themed_button(center_frame, config, "Voting", open_voting, width=20).pack(pady=15)

    settings_button = themed_button(root, config, "Settings", lambda: show_settings_console(root, state), width=12, bg=theme["ACCENT_2"], fg=theme["TEXT"])

    def place_settings_button() -> None:
        settings_button.place(relx=0.0, rely=1.0, x=340, y=-15, anchor="sw")

    root.after(100, place_settings_button)


def show_settings_console(root, state) -> None:
    from .settings_console import show_settings_console as _show

    _show(root, state)
