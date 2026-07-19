from __future__ import annotations

import hashlib
import tkinter as tk
from tkinter import messagebox, simpledialog

from .theme_widgets import themed_button, themed_frame, themed_label, themed_labelframe, style_dialog_window


def verify_password(state, input_password: str) -> bool:
    input_hash = hashlib.sha256(input_password.encode()).hexdigest()
    return input_hash == state.config.admin_password_hash


def ask_for_member_lookup(root, state):
    log_action = state.sheets_service is not None and state.log_sink is not None
    choice_win = tk.Toplevel(root)
    style_dialog_window(choice_win, state.config, "Choose Identification Method", "380x220", (360, 210))
    choice_win.grab_set()

    card = themed_frame(choice_win, state.config, border=True)
    card.pack(fill="both", expand=True, padx=16, pady=16)

    themed_label(card, state.config, "Select identification method:", font=tuple(state.config.theme["MONO_FONT"]), bg=state.config.theme["PANEL_BG"]).pack(pady=(10, 12))

    id_method = tk.StringVar(value="registration number")
    tk.Radiobutton(card, text="Registration Number", variable=id_method, value="registration number", bg=state.config.theme["PANEL_BG"], fg=state.config.theme["TEXT"], activebackground=state.config.theme["PANEL_BG"], activeforeground=state.config.theme["TEXT"], selectcolor=state.config.theme["CARD_BG"]).pack(anchor="w", padx=18, pady=3)
    tk.Radiobutton(card, text="Admission Number", variable=id_method, value="admission number", bg=state.config.theme["PANEL_BG"], fg=state.config.theme["TEXT"], activebackground=state.config.theme["PANEL_BG"], activeforeground=state.config.theme["TEXT"], selectcolor=state.config.theme["CARD_BG"]).pack(anchor="w", padx=18, pady=3)

    result = {"field": None, "key": None}

    def submit_choice():
        field = id_method.get()
        key = simpledialog.askstring("Login", f"Enter {field.title()}:", parent=choice_win)
        if key:
            result["field"] = field
            result["key"] = key
        choice_win.destroy()

    themed_button(card, state.config, "Proceed", submit_choice, bg=state.config.theme["ACCENT"], fg=state.config.theme["BG"]).pack(pady=(14, 8))

    choice_win.wait_window()

    if not result["key"]:
        return None

    member = None
    if result["field"] == "registration number":
        member = state.sheets_service.get_member_by_registration(result["key"])
    else:
        member = state.sheets_service.get_member_by_admission(result["key"])

    if not member:
        messagebox.showerror("Not Found", f"Member not found with {result['field'].title()}: {result['key']}")
        return None
    return member
