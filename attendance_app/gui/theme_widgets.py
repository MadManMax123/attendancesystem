from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..config import AppConfig


def configure_styles(root: tk.Misc, config: AppConfig) -> None:
    theme = config.theme
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    bg = theme["BG"]
    panel_bg = theme["PANEL_BG"]
    card_bg = theme["CARD_BG"]
    text = theme["TEXT"]
    muted = theme["MUTED"]
    accent_2 = theme["ACCENT_2"]
    button_bg = theme["BUTTON_BG"]
    button_active = theme["BUTTON_ACTIVE"]
    mono_font = tuple(theme["MONO_FONT"])
    title_font = tuple(theme["TITLE_FONT"])
    subtitle_font = tuple(theme["SUBTITLE_FONT"])

    style.configure("TFrame", background=bg)
    style.configure("Card.TFrame", background=card_bg)
    style.configure("TLabel", background=bg, foreground=text, font=subtitle_font)
    style.configure("Title.TLabel", background=bg, foreground=accent_2, font=title_font)
    style.configure("Muted.TLabel", background=bg, foreground=muted, font=subtitle_font)
    style.configure("TButton", font=mono_font, padding=(12, 8))
    style.map("TButton", background=[("active", button_active), ("!active", button_bg)], foreground=[("active", text), ("!active", text)])
    style.configure("Accent.TButton", background=button_bg, foreground=text)
    style.configure("Treeview", background=card_bg, fieldbackground=card_bg, foreground=text, rowheight=26)
    style.configure("Treeview.Heading", background=panel_bg, foreground=text, font=mono_font)
    style.configure("TCombobox", fieldbackground=card_bg, background=card_bg, foreground=text)


def style_dialog_window(win: tk.Toplevel, config: AppConfig, title: str, geometry: str, minsize: tuple[int, int] | None = None) -> None:
    win.title(title)
    win.geometry(geometry)
    if minsize:
        win.minsize(*minsize)
    win.configure(bg=config.theme["BG"])


def themed_label(parent: tk.Misc, config: AppConfig, text: str, *, fg: str | None = None, bg: str | None = None, font=None, **kwargs):
    theme = config.theme
    return tk.Label(
        parent,
        text=text,
        fg=fg or theme["TEXT"],
        bg=bg if bg is not None else parent.cget("bg"),
        font=font or tuple(theme["SUBTITLE_FONT"]),
        **kwargs,
    )


def themed_button(parent: tk.Misc, config: AppConfig, text: str, command, *, width=None, bg=None, fg=None, font=None, **kwargs):
    theme = config.theme
    options = {
        "text": text,
        "command": command,
        "font": font or tuple(theme["MONO_FONT"]),
        "bg": bg or theme["BUTTON_BG"],
        "fg": fg or theme["TEXT"],
        "activebackground": theme["BUTTON_ACTIVE"],
        "activeforeground": theme["TEXT"],
        "cursor": "hand2",
        "relief": "ridge",
        "bd": 2,
    }
    if width is not None:
        options["width"] = width
    options.update(kwargs)
    return tk.Button(parent, **options)


def themed_entry(parent: tk.Misc, config: AppConfig, *, width: int = 24, center: bool = False):
    theme = config.theme
    return tk.Entry(
        parent,
        width=width,
        font=tuple(theme["MONO_FONT"]),
        bg=theme["CARD_BG"],
        fg=theme["TEXT"],
        insertbackground=theme["TEXT"],
        relief="flat",
        highlightthickness=1,
        highlightbackground="#26304d",
        highlightcolor=theme["ACCENT"],
        justify="center" if center else "left",
    )


def themed_frame(parent: tk.Misc, config: AppConfig, *, bg: str | None = None, border: bool = False):
    theme = config.theme
    options = {"bg": bg if bg is not None else theme["PANEL_BG"]}
    if border:
        options.update({"bd": 0, "highlightthickness": 1, "highlightbackground": "#26304d"})
    return tk.Frame(parent, **options)


def themed_labelframe(parent: tk.Misc, config: AppConfig, text: str):
    theme = config.theme
    return tk.LabelFrame(
        parent,
        text=text,
        bg=theme["PANEL_BG"],
        fg=theme["TEXT"],
        font=tuple(theme["MONO_FONT"]),
        bd=1,
        relief="solid",
        labelanchor="n",
        highlightthickness=1,
        highlightbackground="#26304d",
    )


def build_session_header(parent: tk.Misc, config: AppConfig):
    theme = config.theme
    header = tk.Frame(parent, bg=theme["BG"])
    header.pack(fill="x", padx=18, pady=(14, 8))

    left = tk.Frame(header, bg=theme["BG"])
    left.pack(side="left", anchor="w")

    tk.Label(left, text=f"{config.club_name_title} Attendance System", font=tuple(theme["TITLE_FONT"]), fg=theme["ACCENT_2"], bg=theme["BG"]).pack(anchor="w")
    tk.Label(left, text="Session storage is created automatically for every run.", font=tuple(theme["SUBTITLE_FONT"]), fg=theme["MUTED"], bg=theme["BG"]).pack(anchor="w", pady=(4, 0))

    right = tk.Frame(header, bg=theme["BG"])
    right.pack(side="right", anchor="e")
    tk.Label(right, text=f"Session: {config.session_dir.name}", font=tuple(theme["MONO_FONT"]), fg=theme["ACCENT"], bg=theme["BG"]).pack(anchor="e")
    tk.Label(right, text=config.log_path.name, font=tuple(theme["MONO_FONT"]), fg=theme["MUTED"], bg=theme["BG"]).pack(anchor="e")

    return header
