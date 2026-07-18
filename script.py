#231794889142224

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from datetime import datetime
import re
import time
import threading
import csv
import os
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from PIL import Image, ImageTk
import webbrowser
import urllib.parse
import platform
import getpass
import sys
import json
import random
import psutil
import socket
import psutil
import requests
import time
from ping3 import ping
import hashlib
from flask import Flask, jsonify, request, render_template_string, send_from_directory


APP_DIR = os.path.dirname(os.path.abspath(__file__))
# Prompt for a session name before the main UI appears
temp_root = tk.Tk()
temp_root.withdraw()
session_name = simpledialog.askstring("Session Name", "Enter session name (letters, numbers, - or _):", parent=temp_root)
if not session_name or not session_name.strip():
    messagebox.showerror("Missing Session Name", "Session name is required. Exiting.")
    temp_root.destroy()
    sys.exit(1)
session_name = session_name.strip()
# sanitize to safe filename
safe_name = re.sub(r'[^A-Za-z0-9_-]', '_', session_name)
SESSION_ID = safe_name
SESSION_DIR = os.path.join(APP_DIR, f"session_{SESSION_ID}")
if os.path.exists(SESSION_DIR):
    # avoid overwriting existing session directory
    SESSION_DIR = os.path.join(APP_DIR, f"session_{SESSION_ID}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
os.makedirs(SESSION_DIR, exist_ok=True)
temp_root.destroy()

MONO_FONT = ("Cascadia Code", 11)
TITLE_FONT = ("Cascadia Code", 24, "bold")
SUBTITLE_FONT = ("Cascadia Code", 11)

BG = "#0b1020"
PANEL_BG = "#11172b"
CARD_BG = "#151d33"
TEXT = "#f5f7ff"
MUTED = "#aab3d1"
ACCENT = "#4dd0e1"
ACCENT_2 = "#ff6b9b"
BUTTON_BG = "#2d6cdf"
BUTTON_ACTIVE = "#1f4fa3"
WARNING = "#ffb86b"
SUCCESS = "#43d17a"
ERROR = "#ff6b6b"

ROOT_DIR = APP_DIR


def asset_path(filename):
    return os.path.join(ROOT_DIR, filename)

# Load theme (colors, fonts) from theme.json with sensible defaults
def load_theme():
    theme_file = asset_path("theme.json")
    defaults = {
        "MONO_FONT": ["Cascadia Code", 11],
        "TITLE_FONT": ["Cascadia Code", 24, "bold"],
        "SUBTITLE_FONT": ["Cascadia Code", 11],

        "BG": "#0b1020",
        "PANEL_BG": "#11172b",
        "CARD_BG": "#151d33",
        "TEXT": "#f5f7ff",
        "MUTED": "#aab3d1",
        "ACCENT": "#4dd0e1",
        "ACCENT_2": "#ff6b9b",
        "BUTTON_BG": "#2d6cdf",
        "BUTTON_ACTIVE": "#1f4fa3",
        "WARNING": "#ffb86b",
        "SUCCESS": "#43d17a",
        "ERROR": "#ff6b6b",
    }
    try:
        with open(theme_file, "r", encoding="utf-8") as f:
            user_theme = json.load(f)
    except Exception:
        user_theme = {}

    theme = {}
    for k, v in defaults.items():
        theme[k] = user_theme.get(k, v)
    return theme

THEME = load_theme()

MONO_FONT = tuple(THEME.get("MONO_FONT"))
TITLE_FONT = tuple(THEME.get("TITLE_FONT"))
SUBTITLE_FONT = tuple(THEME.get("SUBTITLE_FONT"))

BG = THEME.get("BG")
PANEL_BG = THEME.get("PANEL_BG")
CARD_BG = THEME.get("CARD_BG")
TEXT = THEME.get("TEXT")
MUTED = THEME.get("MUTED")
ACCENT = THEME.get("ACCENT")
ACCENT_2 = THEME.get("ACCENT_2")
BUTTON_BG = THEME.get("BUTTON_BG")
BUTTON_ACTIVE = THEME.get("BUTTON_ACTIVE")
WARNING = THEME.get("WARNING")
SUCCESS = THEME.get("SUCCESS")
ERROR = THEME.get("ERROR")
CLUB_NAME = THEME.get("CLUB_NAME", "club")
CLUB_NAME_TITLE = CLUB_NAME.title()
CLUB_NAME_UPPER = CLUB_NAME.upper()
LOGO_FILE = THEME.get("LOGO_FILE", "Logo.png")
CREST_FILE = THEME.get("CREST_FILE", "school_logo.png")

# Constants
with open(asset_path("password.json"), "r") as config_file:
    config = json.load(config_file)
ADMIN_PASSWORD_HASH = config.get("admin_password", "")

CSV_FILENAME = os.path.join(SESSION_DIR, "attendance.csv")
LOG_FILENAME = os.path.join(SESSION_DIR, "activity.log")
# Load environment variables (creds filename, sheet keys) from envvars.json
ENV_FILE = asset_path("envvars.json")
with open(ENV_FILE, "r", encoding="utf-8") as _ef:
    env = json.load(_ef)

# Require these keys to be present in envvars.json; fail fast if missing
required_keys = ["creds_file", "member_sheet_key", "attendance_sheet_key"]
missing = [k for k in required_keys if k not in env or not env.get(k)]
if missing:
    raise RuntimeError(f"Missing required key(s) in {ENV_FILE}: {', '.join(missing)}")

CREDS_FILE = os.path.join(ROOT_DIR, env["creds_file"])
PROGRAM_START_TIME = time.time()
MEMBER_SHEET_KEY = env["member_sheet_key"]
ATTENDANCE_SHEET_KEY = env["attendance_sheet_key"]

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPE)
client = gspread.authorize(creds)

member_sheet = client.open_by_key(MEMBER_SHEET_KEY).sheet1
attendance_sheet = client.open_by_key(ATTENDANCE_SHEET_KEY)

def log_action(action):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {action}"

    print(entry)

    with open(LOG_FILENAME, "a") as f:
        f.write(entry + "\n")

    def _update_widget():
        if 'log_text' in globals():
            log_text.config(state="normal")
            log_text.insert("end", entry + "\n")
            log_text.see("end")
            log_text.config(state="disabled")

    # log_action can be called from the Flask web check-in thread as well as
    # the main Tkinter thread, so widget updates are marshalled onto the
    # main thread via root.after instead of touching the widget directly.
    if 'root' in globals():
        try:
            root.after(0, _update_widget)
        except Exception:
            pass
    else:
        _update_widget()


def configure_styles():
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure("TFrame", background=BG)
    style.configure("Card.TFrame", background=CARD_BG)
    style.configure("TLabel", background=BG, foreground=TEXT, font=SUBTITLE_FONT)
    style.configure("Title.TLabel", background=BG, foreground=ACCENT_2, font=TITLE_FONT)
    style.configure("Muted.TLabel", background=BG, foreground=MUTED, font=SUBTITLE_FONT)
    style.configure("TButton", font=MONO_FONT, padding=(12, 8))
    style.map("TButton",
              background=[("active", BUTTON_ACTIVE), ("!active", BUTTON_BG)],
              foreground=[("active", TEXT), ("!active", TEXT)])
    style.configure("Accent.TButton", background=BUTTON_BG, foreground=TEXT)
    style.configure("Treeview", background=CARD_BG, fieldbackground=CARD_BG, foreground=TEXT, rowheight=26)
    style.configure("Treeview.Heading", background=PANEL_BG, foreground=TEXT, font=MONO_FONT)
    style.configure("TCombobox", fieldbackground=CARD_BG, background=CARD_BG, foreground=TEXT)


def build_session_header(parent):
    header = tk.Frame(parent, bg=BG)
    header.pack(fill="x", padx=18, pady=(14, 8))

    left = tk.Frame(header, bg=BG)
    left.pack(side="left", anchor="w")

    tk.Label(left, text=f"{CLUB_NAME_TITLE} Attendance System", font=TITLE_FONT, fg=ACCENT_2, bg=BG).pack(anchor="w")
    tk.Label(left, text="Session storage is created automatically for every run.", font=SUBTITLE_FONT, fg=MUTED, bg=BG).pack(anchor="w", pady=(4, 0))

    right = tk.Frame(header, bg=BG)
    right.pack(side="right", anchor="e")
    tk.Label(right, text=f"Session: {os.path.basename(SESSION_DIR)}", font=MONO_FONT, fg=ACCENT, bg=BG).pack(anchor="e")
    tk.Label(right, text=os.path.basename(LOG_FILENAME), font=MONO_FONT, fg=MUTED, bg=BG).pack(anchor="e")


def style_dialog_window(win, title, geometry, minsize=None):
    win.title(title)
    win.geometry(geometry)
    if minsize:
        win.minsize(*minsize)
    win.configure(bg=BG)


def themed_label(parent, text, *, fg=TEXT, bg=None, font=None, **kwargs):
    return tk.Label(parent, text=text, fg=fg, bg=bg if bg is not None else parent.cget("bg"), font=font or SUBTITLE_FONT, **kwargs)


def themed_button(parent, text, command, *, width=None, bg=BUTTON_BG, fg=TEXT, font=None, **kwargs):
    options = {
        "text": text,
        "command": command,
        "font": font or MONO_FONT,
        "bg": bg,
        "fg": fg,
        "activebackground": BUTTON_ACTIVE,
        "activeforeground": TEXT,
        "cursor": "hand2",
        "relief": "ridge",
        "bd": 2,
    }
    if width is not None:
        options["width"] = width
    options.update(kwargs)
    return tk.Button(parent, **options)


def themed_entry(parent, *, width=24, center=False):
    entry = tk.Entry(
        parent,
        width=width,
        font=MONO_FONT,
        bg=CARD_BG,
        fg=TEXT,
        insertbackground=TEXT,
        relief="flat",
        highlightthickness=1,
        highlightbackground="#26304d",
        highlightcolor=ACCENT,
        justify="center" if center else "left",
    )
    return entry


def themed_frame(parent, *, bg=None, border=False):
    options = {"bg": bg if bg is not None else PANEL_BG}
    if border:
        options.update({"bd": 0, "highlightthickness": 1, "highlightbackground": "#26304d"})
    return tk.Frame(parent, **options)


def themed_labelframe(parent, text):
    return tk.LabelFrame(
        parent,
        text=text,
        bg=PANEL_BG,
        fg=TEXT,
        font=MONO_FONT,
        bd=1,
        relief="solid",
        labelanchor="n",
        highlightthickness=1,
        highlightbackground="#26304d",
    )

PROGRAM_START_TIME = time.time()
log_action("System initialized")

def verify_password(input_password):
    """Verify password using SHA-256"""
    input_hash = hashlib.sha256(input_password.encode()).hexdigest()
    return input_hash == ADMIN_PASSWORD_HASH

def show_settings_console():
    settings_win = tk.Toplevel()
    style_dialog_window(settings_win, "Settings Console", "560x620", (540, 600))

    try:
        logo_img = Image.open(asset_path(LOGO_FILE)).resize((60, 60))
        logo_img = ImageTk.PhotoImage(logo_img)
        tk.Label(settings_win, image=logo_img, bg=BG).place(relx=0.97, y=10, anchor="ne")
        settings_win.logo_img = logo_img
    except:
        pass

    themed_label(settings_win, "STATS", fg=ACCENT_2, font=TITLE_FONT).pack(pady=(18, 12))

    sys_frame = themed_labelframe(settings_win, "System Info")
    sys_frame.pack(fill="x", padx=14, pady=8)

    sys_labels = {
        "Python Ver": themed_label(sys_frame, "", bg=PANEL_BG),
        "Platform": themed_label(sys_frame, "", bg=PANEL_BG),
        "Hostname": themed_label(sys_frame, "", bg=PANEL_BG),
        "Local IP": themed_label(sys_frame, "", bg=PANEL_BG),
        "MAC": themed_label(sys_frame, "", bg=PANEL_BG),
        "External IP": themed_label(sys_frame, "", bg=PANEL_BG)
    }
    for lbl in sys_labels.values():
        lbl.pack(anchor="w")

    net_frame = themed_labelframe(settings_win, "Network Info")
    net_frame.pack(fill="x", padx=14, pady=8)

    net_labels = {
        "Upload": themed_label(net_frame, "", bg=PANEL_BG),
        "Download": themed_label(net_frame, "", bg=PANEL_BG),
        "Ping": themed_label(net_frame, "", bg=PANEL_BG)
    }
    for lbl in net_labels.values():
        lbl.pack(anchor="w")

    perf_frame = themed_labelframe(settings_win, "Performance")
    perf_frame.pack(fill="x", padx=14, pady=8)

    perf_labels = {
        "CPU Usage": themed_label(perf_frame, "", bg=PANEL_BG),
        "Memory Usage": themed_label(perf_frame, "", bg=PANEL_BG),
        "Disk Usage": themed_label(perf_frame, "", bg=PANEL_BG)
    }
    for lbl in perf_labels.values():
        lbl.pack(anchor="w")

    def update():
        sys_labels["Python Ver"].config(text=f"Python Version: {platform.python_version()}")
        sys_labels["Platform"].config(text=f"Platform: {platform.system()} {platform.release()}")
        sys_labels["Hostname"].config(text=f"Hostname: {socket.gethostname()}")
        sys_labels["Local IP"].config(text=f"Local IP: {socket.gethostbyname(socket.gethostname())}")

        mac_address = "N/A"
        for iface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == psutil.AF_LINK:
                    mac_address = addr.address
                    break
            if mac_address != "N/A":
                break
        sys_labels["MAC"].config(text=f"MAC: {mac_address}")

        try:
            external_ip = requests.get("https://api.ipify.org").text
        except:
            external_ip = "N/A"
        sys_labels["External IP"].config(text=f"External IP: {external_ip}")

        net_io = psutil.net_io_counters()
        upload_speed = net_io.bytes_sent / (1024 * 1024)
        download_speed = net_io.bytes_recv / (1024 * 1024)
        net_labels["Upload"].config(text=f"Upload: {upload_speed:.2f} MB")
        net_labels["Download"].config(text=f"Download: {download_speed:.2f} MB")

        try:
            latency = ping("8.8.8.8", timeout=1)
            latency_ms = f"{round(latency * 1000, 2)} ms" if latency else "Timeout"
        except:
            latency_ms = "Error"
        net_labels["Ping"].config(text=f"Ping (8.8.8.8): {latency_ms}")

        perf_labels["CPU Usage"].config(text=f"CPU Usage: {psutil.cpu_percent()}%")
        perf_labels["Memory Usage"].config(text=f"Memory Usage: {psutil.virtual_memory().percent}%")
        perf_labels["Disk Usage"].config(text=f"Disk Usage: {psutil.disk_usage('/').percent}%")

        settings_win.after(2000, update)

    update()

    threading.Thread(target=update, daemon=True).start()

    themed_label(settings_win, "Made by Satyaki Bandopadhyay", fg=MUTED, font=MONO_FONT).pack(side="bottom", pady=12)


def ask_for_member_lookup():
    log_action("A/N or R/N prompt window")
    choice_win = tk.Toplevel()
    style_dialog_window(choice_win, "Choose Identification Method", "380x220", (360, 210))
    choice_win.grab_set()

    card = themed_frame(choice_win, border=True)
    card.pack(fill="both", expand=True, padx=16, pady=16)

    themed_label(card, "Select identification method:", font=MONO_FONT, bg=PANEL_BG).pack(pady=(10, 12))

    id_method = tk.StringVar(value="registration number")
    tk.Radiobutton(card, text="Registration Number", variable=id_method, value="registration number", bg=PANEL_BG, fg=TEXT, activebackground=PANEL_BG, activeforeground=TEXT, selectcolor=CARD_BG).pack(anchor="w", padx=18, pady=3)
    tk.Radiobutton(card, text="Admission Number", variable=id_method, value="admission number", bg=PANEL_BG, fg=TEXT, activebackground=PANEL_BG, activeforeground=TEXT, selectcolor=CARD_BG).pack(anchor="w", padx=18, pady=3)

    result = {"field": None, "key": None}

    def submit_choice():
        field = id_method.get()
        key = simpledialog.askstring("Login", f"Enter {field.title()}:")
        if key:
            result["field"] = field
            result["key"] = key
        choice_win.destroy()

    themed_button(card, "Proceed", submit_choice, bg=ACCENT, fg=BG).pack(pady=(14, 8))

    choice_win.wait_window()

    if not result["key"]:
        return None

    df = get_members_df()
    row = df[df[result["field"]].astype(str).str.strip() == result["key"].strip()]
    if row.empty:
        messagebox.showerror("Not Found", f"Member not found with {result['field'].title()}: {result['key']}")
        return None
    return row.iloc[0]


def get_members_df():
    data = member_sheet.get_all_records()
    df = pd.DataFrame(data)
    df.columns = df.columns.str.strip().str.lower()
    df["registration number"] = df["registration number"].astype(str).str.strip()
    return df


# ------------------------------------------------------------------
# Web check-in UI
# A lightweight Flask server that opens in the browser on launch and
# lets members tap their own name in a list to mark their attendance.
# It shares the same session CSV / Google Sheet as the desktop app.
# ------------------------------------------------------------------

WEB_PORT = 5050
sheet_lock = threading.Lock()

web_app = Flask(__name__)


def read_marked_registrations():
    """Return {registration_number: status} for everyone already logged this session."""
    marked = {}
    if os.path.exists(CSV_FILENAME):
        with open(CSV_FILENAME, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                reg = str(row.get("Reg. No", "")).strip()
                if reg:
                    marked[reg] = row.get("Status", "Present")
    return marked


@web_app.route("/assets/<path:filename>")
def web_assets(filename):
    return send_from_directory(ROOT_DIR, filename)


@web_app.route("/favicon.ico")
def web_favicon():
    favicon_path = os.path.join(ROOT_DIR, LOGO_FILE)
    if os.path.exists(favicon_path):
        return send_from_directory(ROOT_DIR, LOGO_FILE, mimetype="image/png")
    return "", 404


@web_app.route("/api/members")
def web_api_members():
    try:
        df = get_members_df()
    except Exception as e:
        return jsonify({"error": f"Could not load members: {e}"}), 500

    marked = read_marked_registrations()

    try:
        total_meetings = max(len(attendance_sheet.worksheets()) - 1, 0)
    except Exception:
        total_meetings = 0

    members = []
    for _, row in df.iterrows():
        reg = str(row["registration number"]).strip()
        try:
            attendance_count = int(str(row.get("attendance", 0)).strip() or 0)
        except ValueError:
            attendance_count = 0
        members.append({
            "name": row["name"],
            "class": str(row["class"]),
            "section": str(row["section"]),
            "admission_number": str(row["admission number"]),
            "registration_number": reg,
            "attendance": attendance_count,
            "status": marked.get(reg),
        })

    members.sort(key=lambda m: m["name"].lower())
    return jsonify({"members": members, "total_meetings": total_meetings})


@web_app.route("/api/attendance", methods=["POST"])
def web_api_mark_attendance():
    data = request.get_json(force=True, silent=True) or {}
    reg = str(data.get("registration_number", "")).strip()
    status = data.get("status", "Present")
    activity = str(data.get("activity", "")).strip()

    if not reg:
        return jsonify({"error": "Missing registration number."}), 400
    # default activity to session name when not provided by web UI
    if not activity:
        activity = session_name
    if status not in ("Present", "Absent", "On Duty"):
        return jsonify({"error": "Invalid status."}), 400

    with sheet_lock:
        try:
            df = get_members_df()
        except Exception as e:
            return jsonify({"error": f"Could not load members: {e}"}), 500

        row = df[df["registration number"] == reg]
        if row.empty:
            return jsonify({"error": "Member not found."}), 404
        member = row.iloc[0]

        already = read_marked_registrations()
        if reg in already:
            return jsonify({"error": f"{member['name']} has already checked in as {already[reg]}."}), 409

        with open(CSV_FILENAME, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d"),
                member["registration number"],
                member["name"],
                member["class"],
                member["section"],
                str(member["admission number"]),
                member["email"],
                status,
                activity,
                ""
            ])
        log_action(f"[Web] Attendance marked for {member['name']}: {status}, Activity: {activity}")

        if status == "Present":
            try:
                members_file = client.open_by_key(MEMBER_SHEET_KEY)
                member_ws = members_file.worksheet("Members")
                all_members = member_ws.get_all_records()
                for idx, m in enumerate(all_members):
                    if str(m["registration number"]).strip() == reg:
                        current_val = int(m.get("attendance", 0))
                        col_num = list(m.keys()).index("attendance") + 1
                        member_ws.update_cell(idx + 2, col_num, current_val + 1)
                        break
            except Exception as e:
                log_action(f"[Web] Warning: could not update attendance count: {e}")

    return jsonify({"success": True, "name": member["name"], "status": status})


@web_app.route("/api/attendance", methods=["DELETE"])
def web_api_remove_attendance():
    data = request.get_json(force=True, silent=True) or {}
    reg = str(data.get("registration_number", "")).strip()
    if not reg:
        return jsonify({"error": "Missing registration number."}), 400

    with sheet_lock:
        if not os.path.exists(CSV_FILENAME):
            return jsonify({"error": "No attendance recorded yet."}), 404

        with open(CSV_FILENAME, newline="") as f:
            rows = list(csv.reader(f))
        if not rows:
            return jsonify({"error": "No attendance recorded yet."}), 404

        header, body = rows[0], rows[1:]
        removed_row = None
        new_body = []
        for r in body:
            if removed_row is None and len(r) > 1 and r[1].strip() == reg:
                removed_row = r
                continue
            new_body.append(r)

        if removed_row is None:
            return jsonify({"error": "No check-in found to remove."}), 404

        with open(CSV_FILENAME, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(new_body)

        name = removed_row[2] if len(removed_row) > 2 else reg
        status = removed_row[7] if len(removed_row) > 7 else "Present"
        log_action(f"[Web] Attendance entry removed for {name} (was {status})")

        if status == "Present":
            try:
                members_file = client.open_by_key(MEMBER_SHEET_KEY)
                member_ws = members_file.worksheet("Members")
                all_members = member_ws.get_all_records()
                for idx, m in enumerate(all_members):
                    if str(m["registration number"]).strip() == reg:
                        current_val = int(m.get("attendance", 0))
                        col_num = list(m.keys()).index("attendance") + 1
                        member_ws.update_cell(idx + 2, col_num, max(current_val - 1, 0))
                        break
            except Exception as e:
                log_action(f"[Web] Warning: could not revert attendance count: {e}")

    return jsonify({"success": True, "name": name})


WEB_UI_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ CLUB_NAME_TITLE }} Attendance</title>
    <link rel="icon" href="/favicon.ico">
<style>
  :root {
    --bg: {{ BG }};
    --panel: {{ PANEL_BG }};
    --card: {{ CARD_BG }};
    --text: {{ TEXT }};
    --muted: {{ MUTED }};
    --accent: {{ ACCENT }};
    --accent2: {{ ACCENT_2 }};
    --button: {{ BUTTON_BG }};
    --button-active: {{ BUTTON_ACTIVE }};
    --warning: {{ WARNING }};
    --success: {{ SUCCESS }};
    --error: {{ ERROR }};
    --border: #26304d;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    min-height: 100vh;
    background: var(--bg);
    color: var(--text);
    font-family: 'Cascadia Code', 'Consolas', monospace;
  }
  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 18px 28px;
    border-bottom: 1px solid var(--border);
    flex-wrap: wrap;
    gap: 12px;
  }
  .brand { display: flex; align-items: center; gap: 14px; }
  .brand img { width: 48px; height: 48px; border-radius: 10px; }
  .brand h1 { font-size: 20px; margin: 0; color: var(--accent2); letter-spacing: 0.5px; }
  .brand p { margin: 2px 0 0; color: var(--muted); font-size: 12px; }
  #clock { color: var(--accent); font-weight: bold; font-size: 13px; }

  .toolbar {
    display: flex;
    gap: 14px;
    align-items: center;
    padding: 18px 28px;
    flex-wrap: wrap;
  }
  .field {
    display: flex;
    align-items: center;
    gap: 8px;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 8px 12px;
  }
  .field input {
    background: transparent;
    border: none;
    outline: none;
    color: var(--text);
    font-family: inherit;
    font-size: 13px;
    min-width: 180px;
  }
  .field svg { flex-shrink: 0; color: var(--muted); }
  #activity-field { flex: 1; min-width: 220px; }
  #activity-field input { width: 100%; }
  #activity-field.needs-input { border-color: var(--warning); }

  .icon-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    background: var(--button);
    color: var(--text);
    border: none;
    border-radius: 8px;
    padding: 9px 14px;
    font-family: inherit;
    font-size: 12px;
    font-weight: bold;
    cursor: pointer;
  }
  .icon-btn:hover { background: var(--button-active); }

  #grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
    gap: 14px;
    padding: 6px 28px 40px;
  }
  .card {
    position: relative;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px;
    cursor: pointer;
    transition: transform 0.1s ease, border-color 0.15s ease;
  }
  .card:hover { border-color: var(--accent); transform: translateY(-2px); }
  .card.present { border-color: var(--success); }
  .card.absent { border-color: var(--error); }
  .card.onduty { border-color: var(--warning); }

  .avatar {
    width: 38px; height: 38px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: bold; font-size: 15px;
    background: var(--accent);
    color: var(--bg);
    margin-bottom: 10px;
  }
  .card:nth-child(odd) .avatar { background: var(--accent2); }

  .name { font-weight: bold; font-size: 14px; margin: 0 0 2px; }
  .meta { color: var(--muted); font-size: 11px; margin: 0 0 8px; }
  .stat { font-size: 11px; margin: 0; }
  .stat.good { color: var(--success); }
  .stat.avg { color: var(--warning); }
  .stat.poor { color: var(--error); }

  .badge {
    position: absolute;
    top: 10px; right: 10px;
    width: 22px; height: 22px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    background: var(--border);
    color: var(--muted);
  }
  .card.present .badge { background: var(--success); color: var(--bg); }
  .card.absent .badge { background: var(--error); color: var(--bg); }
  .card.onduty .badge { background: var(--warning); color: var(--bg); }

  .menu {
    display: none;
    position: absolute;
    top: 38px; right: 10px;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
    z-index: 5;
    min-width: 150px;
  }
  .menu.open { display: block; }
  .menu button {
    display: block; width: 100%;
    background: none; border: none;
    color: var(--text); text-align: left;
    padding: 9px 12px; font-family: inherit; font-size: 12px;
    cursor: pointer;
  }
  .menu button:hover { background: var(--card); }
  .menu button.danger { color: var(--error); }

  #toast {
    position: fixed;
    bottom: 24px; left: 50%;
    transform: translateX(-50%) translateY(140%);
    background: var(--panel);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 12px 20px;
    border-radius: 10px;
    font-size: 13px;
    display: flex; align-items: center; gap: 10px;
    transition: transform 0.25s ease;
    z-index: 50;
  }
  #toast.show { transform: translateX(-50%) translateY(0); }
  #toast.success { border-color: var(--success); }
  #toast.error { border-color: var(--error); }

  #empty {
    text-align: center;
    color: var(--muted);
    padding: 60px 20px;
    display: none;
  }
</style>
</head>
<body>

<header>
  <div class="brand">
        <img src="/assets/{{ LOGO_FILE }}" onerror="this.style.display='none'">
        <div>
            <h1>{{ CLUB_NAME_UPPER }} ATTENDANCE</h1>
      <p>Tap your name to check in</p>
    </div>
  </div>
  <div id="clock"></div>
</header>

<div class="toolbar">
  <div class="field" id="activity-field">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>
    <input id="activity" type="text" placeholder="Enter today's activity, then tap your name...">
  </div>
  <div class="field">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
    <input id="search" type="text" placeholder="Search name, class, section...">
  </div>
  <button class="icon-btn" onclick="loadMembers()">
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-2.6-6.4"/><path d="M21 3v6h-6"/></svg>
    Refresh
  </button>
</div>

<div id="grid"></div>
<div id="empty">No members match your search.</div>

<div id="toast"></div>

<script>
let MEMBERS = [];
let TOTAL_MEETINGS = 0;

const grid = document.getElementById("grid");
const emptyMsg = document.getElementById("empty");
const activityInput = document.getElementById("activity");
const activityField = document.getElementById("activity-field");
const searchInput = document.getElementById("search");

activityInput.value = localStorage.getItem("ic_activity") || "{{ SESSION_ACTIVITY }}";
activityInput.addEventListener("input", () => {
  localStorage.setItem("ic_activity", activityInput.value);
  activityField.classList.remove("needs-input");
});

function tickClock() {
  const now = new Date();
  document.getElementById("clock").textContent = "Current Time: " + now.toLocaleString();
}
setInterval(tickClock, 1000);
tickClock();

function showToast(message, kind) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.className = "show " + (kind || "");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => { toast.className = ""; }, 3200);
}

function statClass(pct) {
  if (pct < 50) return "poor";
  if (pct < 75) return "avg";
  return "good";
}

function statusClass(status) {
  if (status === "Present") return "present";
  if (status === "Absent") return "absent";
  if (status === "On Duty") return "onduty";
  return "";
}

const CHECK_ICON = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>';
const DOT_ICON = '<svg width="8" height="8" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="10"/></svg>';
const KEBAB_ICON = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="5" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="12" cy="19" r="1"/></svg>';

function render() {
  const q = searchInput.value.trim().toLowerCase();
  grid.innerHTML = "";
  const filtered = MEMBERS.filter(m =>
    !q ||
    m.name.toLowerCase().includes(q) ||
    String(m.class).toLowerCase().includes(q) ||
    String(m.section).toLowerCase().includes(q) ||
    String(m.admission_number).toLowerCase().includes(q)
  );
  emptyMsg.style.display = filtered.length ? "none" : "block";

  filtered.forEach(m => {
    const pct = TOTAL_MEETINGS > 0 ? Math.round((m.attendance / TOTAL_MEETINGS) * 100) : 0;
    const card = document.createElement("div");
    card.className = "card " + statusClass(m.status);
    card.innerHTML = `
      <div class="badge">${m.status ? CHECK_ICON : DOT_ICON}</div>
      <div class="avatar">${m.name.trim().charAt(0).toUpperCase()}</div>
      <p class="name">${m.name}</p>
      <p class="meta">Class ${m.class}-${m.section} &middot; Adm. ${m.admission_number}</p>
      <p class="stat ${statClass(pct)}">${m.attendance}/${TOTAL_MEETINGS} meetings &middot; ${pct}%</p>
      <div class="menu" data-reg="${m.registration_number}">
        <button onclick="mark('${m.registration_number}','Present',event)">Mark Present</button>
        <button onclick="mark('${m.registration_number}','Absent',event)">Mark Absent</button>
        <button onclick="mark('${m.registration_number}','On Duty',event)">Mark On Duty</button>
        ${m.status ? `<button class="danger" onclick="removeEntry('${m.registration_number}',event)">Remove Entry</button>` : ''}
      </div>
    `;
    card.onclick = (e) => {
      if (e.target.closest(".menu")) return;
      if (e.target.closest(".badge") && m.status) { toggleMenu(card, e); return; }
      if (m.status) { showToast(m.name + " already checked in as " + m.status, "error"); return; }
      mark(m.registration_number, "Present", e);
    };
    const badge = card.querySelector(".badge");
    badge.style.cursor = "pointer";
    badge.onclick = (e) => { e.stopPropagation(); toggleMenu(card, e); };
    grid.appendChild(card);
  });
}

function toggleMenu(card, e) {
  e.stopPropagation();
  document.querySelectorAll(".menu.open").forEach(m => { if (m !== card.querySelector(".menu")) m.classList.remove("open"); });
  card.querySelector(".menu").classList.toggle("open");
}
document.addEventListener("click", () => document.querySelectorAll(".menu.open").forEach(m => m.classList.remove("open")));

async function mark(reg, status, e) {
  if (e) e.stopPropagation();
  const activity = activityInput.value.trim();
  if (!activity) {
    activityField.classList.add("needs-input");
    activityInput.focus();
    showToast("Enter the session activity first", "error");
    return;
  }
  try {
    const res = await fetch("/api/attendance", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ registration_number: reg, status: status, activity: activity })
    });
    const data = await res.json();
    if (!res.ok) { showToast(data.error || "Something went wrong.", "error"); return; }
    showToast((status === "Present" ? "Checked in: " : "Marked " + status + ": ") + data.name, "success");
    loadMembers();
  } catch (err) {
    showToast("Network error - is the app still running?", "error");
  }
}

async function removeEntry(reg, e) {
  if (e) e.stopPropagation();
  if (!confirm("Remove this check-in entry?")) return;
  try {
    const res = await fetch("/api/attendance", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ registration_number: reg })
    });
    const data = await res.json();
    if (!res.ok) { showToast(data.error || "Could not remove entry.", "error"); return; }
    showToast("Removed check-in for " + data.name, "success");
    loadMembers();
  } catch (err) {
    showToast("Network error - is the app still running?", "error");
  }
}

async function loadMembers() {
  try {
    const res = await fetch("/api/members");
    const data = await res.json();
    if (!res.ok) { showToast(data.error || "Could not load members.", "error"); return; }
    MEMBERS = data.members;
    TOTAL_MEETINGS = data.total_meetings;
    render();
  } catch (err) {
    showToast("Could not reach the app server.", "error");
  }
}

searchInput.addEventListener("input", render);
loadMembers();
setInterval(loadMembers, 15000);
</script>
</body>
</html>
"""


@web_app.route("/")
def web_index():
    return render_template_string(
        WEB_UI_TEMPLATE,
        BG=BG, PANEL_BG=PANEL_BG, CARD_BG=CARD_BG, TEXT=TEXT, MUTED=MUTED,
        ACCENT=ACCENT, ACCENT_2=ACCENT_2, BUTTON_BG=BUTTON_BG,
        BUTTON_ACTIVE=BUTTON_ACTIVE, WARNING=WARNING, SUCCESS=SUCCESS, ERROR=ERROR,
        CLUB_NAME_TITLE=CLUB_NAME_TITLE, CLUB_NAME_UPPER=CLUB_NAME_UPPER, LOGO_FILE=LOGO_FILE,
        SESSION_ACTIVITY=session_name,
    )


def start_web_checkin_server():
    def run():
        try:
            web_app.run(host="0.0.0.0", port=WEB_PORT, debug=False, use_reloader=False)
        except Exception as e:
            log_action(f"[Web] Failed to start check-in server: {e}")

    threading.Thread(target=run, daemon=True).start()
    time.sleep(0.6)
    try:
        local_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        local_ip = "127.0.0.1"
    log_action(f"Web check-in UI running at http://127.0.0.1:{WEB_PORT} (LAN: http://{local_ip}:{WEB_PORT})")
    webbrowser.open(f"http://127.0.0.1:{WEB_PORT}")


with open(CSV_FILENAME, "w", newline="") as f:
    log_action("Attendance CSV file created")
    writer = csv.writer(f)
    writer.writerow([
    "Date", "Reg. No", "Name", "Class", "Section",
    "Admission No", "Email", "Status", "Activity", "Remarks"
])

start_web_checkin_server()


root = tk.Tk()
root.title(f"{CLUB_NAME_TITLE} Attendance System")
root.geometry("1360x800")
root.minsize(1260, 740)
root.configure(bg=BG)
configure_styles()
build_session_header(root)

# Quick Entry Panel (Left Side)
quick_entry_frame = themed_frame(root, border=True)
quick_entry_frame.place(relx=0.02, rely=0.12, anchor="nw", width=320, relheight=0.80)

quick_title = tk.Label(quick_entry_frame, text="Quick Entry", fg=ACCENT, bg=PANEL_BG, font=TITLE_FONT)
quick_title.pack(pady=(16, 8))

activity_label = tk.Label(quick_entry_frame, text="Activity:", fg=TEXT, bg=PANEL_BG, font=MONO_FONT)
activity_label.pack(pady=(10, 5))

activity_entry = themed_entry(quick_entry_frame, width=25)
activity_entry.pack(pady=5, padx=10)

adm_label = tk.Label(quick_entry_frame, text="Admission Number:", fg=TEXT, bg=PANEL_BG, font=MONO_FONT)
adm_label.pack(pady=(20, 5))

adm_entry = themed_entry(quick_entry_frame, width=25)
adm_entry.pack(pady=5, padx=10)

def quick_submit():
    activity = activity_entry.get().strip()
    adm_no = adm_entry.get().strip()
    # default activity to session name when not provided
    if not activity:
        activity = session_name
    
    if not adm_no:
        messagebox.showerror("Missing Data", "Please enter an admission number.")
        return
    
    df = get_members_df()
    member_row = df[df["admission number"].astype(str).str.strip() == adm_no]
    
    if member_row.empty:
        messagebox.showerror("Not Found", f"Member not found with Admission Number: {adm_no}")
        adm_entry.delete(0, tk.END)
        adm_entry.focus()
        return
    
    member = member_row.iloc[0]
    
    with open(CSV_FILENAME, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d"),
            member["registration number"],
            member["name"],
            member["class"],
            member["section"],
            str(member["admission number"]),
            member["email"],
            "Present",
            activity,
            ""
        ])
    
    log_action(f"Quick entry: {member['name']}, Adm: {adm_no}, Activity: {activity}")
    
    try:
        members_file = client.open_by_key(MEMBER_SHEET_KEY)
        member_ws = members_file.worksheet("Members")
        all_members = member_ws.get_all_records()
        
        for idx, m in enumerate(all_members):
            if str(m["admission number"]).strip() == adm_no:
                current_val = int(m.get("attendance", 0))
                col_num = list(m.keys()).index("attendance") + 1
                member_ws.update_cell(idx + 2, col_num, current_val + 1)
                break
    except Exception as e:
        log_action(f"Warning: Could not update attendance count: {e}")
    
    messagebox.showinfo("Success", f"Attendance marked for {member['name']}")
    adm_entry.delete(0, tk.END)
    adm_entry.focus()

quick_submit_btn = tk.Button(
    quick_entry_frame, 
    text="Submit", 
    command=quick_submit,
    font=MONO_FONT,
    bg=BUTTON_BG,
    fg=TEXT,
    cursor="hand2",
    width=15
)
quick_submit_btn.pack(pady=20)

adm_entry.bind('<Return>', lambda e: quick_submit())

instructions = tk.Label(
    quick_entry_frame,
    text="1. Enter activity once\n2. Scan/type admission numbers\n3. Press Enter or Submit",
    fg=MUTED,
    bg=PANEL_BG,
    font=MONO_FONT,
    justify="left"
)
instructions.pack(pady=(30, 10))

# Activity Log Panel (Right Side)
log_frame = themed_frame(root, border=True)
log_frame.place(relx=0.98, rely=0.12, anchor="ne", width=350, relheight=0.80)

log_title = tk.Label(log_frame, text="Activity Log", fg=ACCENT_2, bg=PANEL_BG, font=MONO_FONT)
log_title.pack(pady=(14, 6))
log_text = tk.Text(log_frame, wrap="word", bg=CARD_BG, fg=TEXT, font=MONO_FONT, state="disabled", relief="flat", padx=8, pady=8, highlightthickness=0)
log_text.pack(expand=True, fill="both", padx=10, pady=(6, 10))

def refresh_log_view():
    if os.path.exists(LOG_FILENAME):
        with open(LOG_FILENAME, "r") as f:
            lines = f.readlines()
        log_text.config(state="normal")
        log_text.delete("1.0", tk.END)
        for line in lines[-100:]:
            log_text.insert(tk.END, line)
        log_text.see(tk.END)
        log_text.config(state="disabled")

def auto_refresh_log():
    refresh_log_view()
    root.after(2000, auto_refresh_log)

auto_refresh_log()

# Center Content Frame
center_frame = themed_frame(root, bg=BG)
center_frame.place(relx=0.5, rely=0.55, anchor="center")

try:
    crest_img = Image.open(asset_path(CREST_FILE)).resize((80, 80))
    crest_photo = ImageTk.PhotoImage(crest_img)
    crest_label = tk.Label(center_frame, image=crest_photo, bg=BG)
    crest_label.image = crest_photo
    crest_label.pack(pady=(0, 10))
except Exception as e:
    print(f"Failed to load crest: {e}")

try:
    logo_img = Image.open(asset_path(LOGO_FILE)).resize((180, 180))
    logo = ImageTk.PhotoImage(logo_img)
    logo_canvas = tk.Canvas(center_frame, width=180, height=180, bg=BG, highlightthickness=0)
    logo_canvas.pack(pady=20)
    logo_canvas.create_image(90, 90, image=logo)
except Exception as e:
    print("Error loading logo:", e)

tk.Label(
    center_frame,
    text=f"{CLUB_NAME_UPPER}\nATTENDANCE SYSTEM",
    font=TITLE_FONT,
    fg=TEXT, bg=BG
).pack(pady=10)

time_label = tk.Label(
    center_frame,
    text="",
    font=SUBTITLE_FONT,
    fg=ACCENT,
    bg=BG
)
time_label.pack(pady=(0, 5))

def update_time():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    time_label.config(text=f"Current Time: {now}")
    root.after(1000, update_time)

update_time()

button_style = {
    "width": 20,
    "font": MONO_FONT,
    "bg": BUTTON_BG,
    "fg": TEXT,
    "activebackground": BUTTON_ACTIVE,
    "activeforeground": TEXT,
    "relief": "ridge",
    "bd": 3
}


def admin_console():
    
    pw = simpledialog.askstring("Admin Login", "Enter admin password:", show="*")
    if pw is None:
        messagebox.showerror("Error", "Please enter a proper password.")
        log_action("No password entered")
        return
    if not verify_password(pw):
        messagebox.showerror("Access Denied", "Incorrect password!")
        log_action("Incorrect password entered")
        return
    
    log_action(f"Admin console accessed")
    
    admin_win = tk.Toplevel(root)
    style_dialog_window(admin_win, "Admin Console", "560x560", (520, 520))

    logo_img = Image.open(asset_path(LOGO_FILE)).resize((80, 80))
    logo_tk = ImageTk.PhotoImage(logo_img)

    logo_label = tk.Label(admin_win, image=logo_tk, bg=BG)
    logo_label.image = logo_tk
    logo_label.place(relx=0.98, y=10, anchor='ne')

    header_frame = themed_frame(admin_win, bg=BG)
    header_frame.pack(pady=(12, 6), fill="x")

    themed_label(header_frame, text="ADMIN CONSOLE", font=TITLE_FONT, fg=ACCENT_2, bg=BG).pack()
    datetime_label = themed_label(header_frame, text="", font=MONO_FONT, fg=TEXT, bg=BG)
    datetime_label.pack()
    count_label = themed_label(header_frame, text="", font=MONO_FONT, fg=TEXT, bg=BG)
    count_label.pack()

    def update_datetime():
        if not admin_win.winfo_exists():
            return
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            count = len(get_members_df())
            datetime_label.config(text=f"Time: {now}")
            count_label.config(text=f"Total Members: {count}")
        except tk.TclError:
            return
        admin_win.after(1000, update_datetime)

    update_datetime()


    def add_member():
        def is_valid_email(email):
            return email.endswith("@dpsn.org.in") and "@" in email

        def is_valid_class(c):
            return c.isdigit() and 1 <= int(c) <= 12

        def is_valid_section(s):
            return len(s) == 1 and s.isalpha() and s.isupper()

        def is_valid_string(s):
            return len(s.strip()) > 0

        fields = {
            "name": lambda x: is_valid_string(x),
            "class": is_valid_class,
            "section": is_valid_section,
            "admission number": is_valid_string,
            "registration number": is_valid_string,
            "email": is_valid_email,
        }

        new_data = []

        for field, validator in fields.items():
            while True:
                value = simpledialog.askstring("Input", f"Enter {field.title()}:")
                if value is None:
                    messagebox.showinfo("Cancelled", "Member addition cancelled.")
                    return
                value = value.strip()
                if validator(value):
                    new_data.append(value)
                    break
                else:   
                    messagebox.showerror("Invalid Input", f"Please enter a valid {field}.\n"
                        + (f"- Email must end with @dpsn.org.in" if field == "email" else "")
                        + (f"- Class must be a number from 1 to 12" if field == "class" else "")
                        + (f"- Section must be one uppercase letter (A-Z)" if field == "section" else "")
                    )

        confirm = messagebox.askyesno("Confirm Member", 
            "Add the following member?\n\n" +
            "\n".join(f"{k.title()}: {v}" for k, v in zip(fields.keys(), new_data))
        )

        if confirm:
            try:
                new_reg = new_data[4].strip()
                new_adm = new_data[3].strip()
                members_file = client.open_by_key(MEMBER_SHEET_KEY)
                past_members_sheet = members_file.worksheet("Past members")
                past_rows = past_members_sheet.get_all_values()
                headers = past_rows[0] if past_rows else []

                for i, row in enumerate(past_rows[1:], start=2):
                    if len(row) < 5:
                        continue
                    reg = row[4].strip()
                    adm = row[3].strip()
                    if reg == new_reg or adm == new_adm:
                        past_members_sheet.delete_rows(i)
                        log_action(f"Old record removed from 'Past members'. Reg: {reg}, Adm: {adm}")
                        break
            except Exception as e:
                log_action(f"Failed to clean up 'Past members' during add: {e}")
            member_sheet.append_row(new_data)
            messagebox.showinfo("Success", "Member added successfully.")
            log_action(f"New member added. {new_data[0]}, {new_data[3]}")
        else:
            messagebox.showinfo("Cancelled", "Member addition cancelled.")


    def remove_member():
        member = ask_for_member_lookup()
        if member is None:
            return
        reg = member["registration number"]
        n = member["name"]
        a = member["admission number"]


        try:
            all_rows = member_sheet.get_all_values()
            headers = all_rows[0]

            for i, row in enumerate(all_rows[1:], start=2):
                if row[4].strip() == reg.strip():
                    member_info = "\n".join(f"{headers[j]}: {row[j]}" for j in range(len(headers)))
                    confirm = messagebox.askyesno("Confirm Removal", f"Are you sure you want to remove this member?\n\n{member_info}")
                    if confirm:
                        reason = simpledialog.askstring("Removal Reason", "Enter reason for removal:")
                        if not reason or not reason.strip():
                            messagebox.showwarning("Cancelled", "Member removal cancelled (no valid reason provided).")
                            log_action("Removal cancelled due to blank reason.")
                            return

                        date_removed = datetime.now().strftime("%Y-%m-%d")

                        members_file = client.open_by_key(MEMBER_SHEET_KEY)
                        past_members_sheet = members_file.worksheet("Past members")

                        existing_rows = past_members_sheet.get_all_values()
                        if existing_rows:
                            existing_headers = existing_rows[0]
                        else:
                            existing_headers = headers + ["Removal Reason", "Date of Removal"]
                            past_members_sheet.append_row(existing_headers)

                        if "Removal Reason" not in existing_headers:
                            existing_headers.append("Removal Reason")
                        if "Date of Removal" not in existing_headers:
                            existing_headers.append("Date of Removal")
                            past_members_sheet.update("A1", [existing_headers])

                        row_dict = {headers[i]: row[i] if i < len(row) else "" for i in range(len(headers))}
                        row_dict["Removal Reason"] = reason
                        row_dict["Date of Removal"] = date_removed

                        final_row = [row_dict.get(col, "") for col in existing_headers]
                        past_members_sheet.append_row(final_row)

                        member_sheet.delete_rows(i)
                        messagebox.showinfo("Removed", "Member removed and added to 'Past members'.")
                        log_action(f"Member removed. {n}, {a}, Reason: {reason}, Date: {date_removed}")

                        
                    else:
                        messagebox.showinfo("Cancelled", "Member removal cancelled.")
                        log_action(f"Member removal cancelled")
                    return

            messagebox.showerror("Not Found", f"Registration number {reg} not found.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")


    def view_member():
        member = ask_for_member_lookup()
        if member is None:
            return

        info = (
            f"Name: {member['name']}\n"
            f"Class: {member['class']}\n"
            f"Section: {member['section']}\n"
            f"Admission No: {member['admission number']}\n"
            f"Registration No: {member['registration number']}\n"
            f"Email: {member['email']}"
        )
        messagebox.showinfo("Member Details", info)
        log_action(f"View member: {member['name']}, {member['admission number']}")
        
    def list_members():
        df = get_members_df()
        top = tk.Toplevel(admin_win)
        style_dialog_window(top, "Member List", "820x520", (760, 460))
        tree = ttk.Treeview(top)
        tree["columns"] = list(df.columns)
        for col in df.columns:
            tree.heading(col, text=col.title())
            tree.column(col, width=100)
        for _, row in df.iterrows():
            tree.insert("", "end", values=list(row))
        tree.pack(expand=True, fill='both', padx=12, pady=12)
        log_action(f"Members list accessed")

    def end_session():
        df = get_members_df()
        scanned = pd.read_csv(CSV_FILENAME)["Reg. No"].astype(str).str.strip().tolist()
        for _, row in df.iterrows():
            if row["registration number"] not in scanned:
                with open(CSV_FILENAME, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        datetime.now().strftime("%Y-%m-%d"),
                        row["registration number"],
                        row["name"],
                        row["class"],
                        row["section"],
                        row["admission number"],
                        row["email"],
                        "Absent",
                        "",
                        ""
                    ])
        with open(CSV_FILENAME, "r") as file:
            content = list(csv.reader(file))
        sheet_title = f"{safe_name} {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        if len(sheet_title) > 50:
            sheet_title = sheet_title[:50]
        sheet = attendance_sheet.add_worksheet(
            title=sheet_title,
            rows=str(len(content)),
            cols=str(len(content[0]))
        )
        sheet.update("A1", content)
        messagebox.showinfo("Uploaded", "Session data uploaded to Google Sheets.")
        log_action(f"Records updated to sheets")
        exit()
        
    def edit_member_requests():
        try:
            members_file = client.open_by_key(MEMBER_SHEET_KEY)
            edit_sheet = members_file.worksheet("Edit requests")
            member_sheet = members_file.worksheet("Members")

            all_requests = edit_sheet.get_all_records()
            if not all_requests:
                messagebox.showinfo("No Requests", "There are no edit requests.")
                return
    
            pending_requests = [r for r in all_requests if r.get("Status", "Pending") == "Pending"]
            if not pending_requests:
                messagebox.showinfo("No Pending", "No pending edit requests.")
                return

            member_df = pd.DataFrame(member_sheet.get_all_records())

            win = tk.Toplevel(root)
            style_dialog_window(win, "Edit Requests", "860x560", (780, 500))

            tree = ttk.Treeview(win, columns=["Time", "Reg No", "Field", "Old", "New", "Status"], show="headings")
            for col in ["Time", "Reg No", "Field", "Old", "New", "Status"]:
                tree.heading(col, text=col)
                tree.column(col, width=100)
            for idx, r in enumerate(pending_requests):
                tree.insert("", "end", iid=idx, values=(r["Time"], r["registration number"], r["Field"], r["Old Value"], r["New Value"], "Pending"))
            tree.pack(expand=True, fill="both", padx=12, pady=12)

            def approve():
                selected = tree.selection()
                if not selected:
                    return
                for sel in selected:
                    idx = int(sel)
                    req = pending_requests[idx]
                    reg = req["registration number"]
                    field = req["Field"]
                    new_val = req["New Value"]

                    row_idx = member_df.index[member_df["registration number"] == reg].tolist()
                    if not row_idx:
                        messagebox.showerror("Error", f"Reg. No. {reg} not found.")
                        continue
                    row_num = row_idx[0] + 2
                    col_list = member_df.columns.tolist()
                    if field not in col_list:
                        messagebox.showerror("Error", f"Field {field} not found in Members sheet.")
                        continue
                    col_num = col_list.index(field) + 1
                    member_sheet.update_cell(row_num, col_num, new_val)

                    edit_sheet.update_cell(idx + 2, 6, "Approved")
                    tree.set(sel, column="Status", value="Approved")
                    log_action(f"Member details update approved. {field} to {new_val}")
                    
            def reject():
                selected = tree.selection()
                if not selected:
                    return
                for sel in selected:
                    idx = int(sel)
                    edit_sheet.update_cell(idx + 2, 6, "Rejected")
                    tree.set(sel, column="Status", value="Rejected")
                    log_action(f"Member details update rejected.")

            tk.Button(win, text="Approve Selected", command=approve, **button_style).pack(pady=5)
            tk.Button(win, text="Reject Selected", command=reject, **button_style).pack(pady=5)
            tk.Button(win, text="Close", command=win.destroy, **button_style).pack(pady=10)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load edit requests:\n{str(e)}")

    def change_admin_password():
        colors = [BG, ACCENT_2, ACCENT, TEXT, MUTED]

        def generate_random_password():
            return ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ', k=4))

        def update_password(new_pass):
            password_hash = hashlib.sha256(new_pass.encode()).hexdigest()
            with open(asset_path("password.json"), "w") as config_file:
                json.dump({"admin_password": password_hash}, config_file)
            log_action("Admin password updated")
            print(f"[LOG] Admin password hash updated")
            messagebox.showinfo("Success", "Admin password updated successfully!")

        def prompt_password_change():
            pw_window = tk.Toplevel()
            style_dialog_window(pw_window, "Change Admin Password", "620x430", (580, 400))

            warning = tk.Label(
                pw_window,
                text="Please note that your password must be exactly 4 letters.\nOnce you change this password, get the RFID admin tag updated as well for convenience.",
                bg=BG, fg=WARNING, font=MONO_FONT, justify="left", wraplength=500
            )
            warning.pack(padx=16, pady=(14, 8))

            entry_label = tk.Label(
                pw_window,
                text="Enter new 4-letter password:",
                bg=BG, fg=TEXT, font=MONO_FONT
            )
            entry_label.pack()

            pw_entry = themed_entry(pw_window, width=25, center=True)
            pw_entry.pack(pady=5)

            def save_manual():
                new_pw = pw_entry.get()
                if len(new_pw) != 4 or not new_pw.isalpha():
                    messagebox.showerror("Invalid", "Password must be exactly 4 letters.")
                    return
                update_password(new_pw)
                pw_window.destroy()

            def use_random():
                rand_pw = generate_random_password()

                preview_window = tk.Toplevel(pw_window)
                style_dialog_window(preview_window, "Generated Password", "360x220", (340, 200))

                msg = tk.Label(
                    preview_window,
                    text="Generated Password:",
                    bg=BG, fg=ACCENT,
                    font=MONO_FONT
                )
                msg.pack(pady=(10, 5))

                pw_display = tk.Label(
                    preview_window,
                    text=rand_pw,
                    bg=BG, fg=TEXT,
                    font=MONO_FONT
                )
                pw_display.pack(pady=(0, 10))

                def confirm_save():
                    update_password(rand_pw)
                    preview_window.destroy()
                    pw_window.destroy()

                def cancel_save():
                    preview_window.destroy()

                btn_frame = tk.Frame(preview_window, bg=BG)
                btn_frame.pack(pady=10)

                save_btn = themed_button(btn_frame, "Save Password", confirm_save, bg=ACCENT_2, fg=BG)
                save_btn.grid(row=0, column=0, padx=10)

                cancel_btn = themed_button(btn_frame, "Cancel", cancel_save, bg=ERROR, fg=TEXT)
                cancel_btn.grid(row=0, column=1, padx=10)

            manual_btn = themed_button(pw_window, "Save Entered Password", save_manual, bg=ACCENT, fg=BG)
            manual_btn.pack(pady=5)

            random_btn = themed_button(pw_window, "Generate 4-letter Password", use_random, bg=ACCENT_2, fg=BG)
            random_btn.pack(pady=5)

        prompt_password_change()



    tk.Button(admin_win, text="Add Member", command=add_member, **button_style, cursor="hand2").pack(pady=10)
    tk.Button(admin_win, text="Remove Member", command=remove_member, **button_style, cursor="hand2").pack(pady=10)
    tk.Button(admin_win, text="List Members", command=list_members, **button_style, cursor="hand2").pack(pady=10)
    tk.Button(admin_win, text="View Member", command=view_member, **button_style, cursor="hand2").pack(pady=10)
    tk.Button(admin_win, text="View Edit Requests", command=edit_member_requests, **button_style, cursor="hand2").pack(pady=10)
    tk.Button(admin_win, text="Change Admin Password", command=change_admin_password, **button_style, cursor="hand2").pack(pady=10)

    
    tk.Button(admin_win, text="End Session & Upload", command=end_session, **button_style, cursor="hand2").pack(pady=40)

def member_console():
    member = ask_for_member_lookup()
    if member is None:
        return

    member_win = tk.Toplevel(root)
    style_dialog_window(member_win, "Member Portal", "620x680", (560, 620))

    log_action(f"Member portal accessed. {member['name']}, {member['admission number']}")

    title_label = tk.Label(
        member_win,
        text="MEMBER PORTAL",
        font=TITLE_FONT,
        fg=ACCENT_2,
        bg=BG,
        justify="center"
    )
    title_label.pack(side="top", fill="x", pady=(18, 10))

    logo_img = Image.open(asset_path(LOGO_FILE)).resize((80, 80))
    logo_tk = ImageTk.PhotoImage(logo_img)
    logo_label = tk.Label(member_win, image=logo_tk, bg=BG)
    logo_label.image = logo_tk
    logo_label.place(relx=0.98, y=10, anchor='ne')

    info_frame = themed_frame(member_win, bg=BG)
    info_frame.pack(pady=10)
    info_text = (
        f"Name: {member['name']}\n"
        f"Class: {member['class']}\n"
        f"Section: {member['section']}\n"
        f"Admission No: {member['admission number']}\n"
        f"Registration No: {member['registration number']}\n"
        f"Email: {member['email']}"
    )
    tk.Label(info_frame, text=info_text, justify="left", font=MONO_FONT, fg=TEXT, bg=BG).pack()

    try:
        all_sheets = attendance_sheet.worksheets()
        total_meetings = (len(all_sheets) - 1)
        members_file = client.open_by_key(MEMBER_SHEET_KEY)
        member_ws = members_file.worksheet("Members")
        all_members = member_ws.get_all_records()
        member_attendance = 0
        for m in all_members:
            if str(m["registration number"]).strip() == str(member["registration number"]).strip():
                member_attendance = int(m.get("attendance", 0))
                break

        percent = (member_attendance / total_meetings * 100) if total_meetings > 0 else 0
        if percent < 50: color = ERROR; comment = "Poor attendance!"
        elif percent < 75: color = WARNING; comment = "Average attendance"
        else: color = SUCCESS; comment = "Good attendance!"

        attendance_frame = themed_frame(member_win, bg=BG)
        attendance_frame.pack(pady=15)

        tk.Label(attendance_frame,
               text=f"{member_attendance}/{total_meetings}",
               font=TITLE_FONT,
               fg=color, bg=BG).pack()
        tk.Label(attendance_frame,
               text=comment, font=MONO_FONT, fg=color, bg=BG).pack()
    except Exception as e:
        log_action(f"Failed to fetch attendance: {e}")

    status_frame = themed_labelframe(member_win, "Mark Attendance")
    status_frame.pack(pady=10, padx=20, fill="x")
    status = tk.StringVar(value="Present")
    for val in ["Present", "Absent", "On Duty"]:
        tk.Radiobutton(status_frame, text=val, variable=status, value=val, bg=PANEL_BG, fg=TEXT, activebackground=PANEL_BG, activeforeground=TEXT, selectcolor=CARD_BG).pack(side="left", padx=12, pady=6)

    edit_frame = themed_labelframe(member_win, "Correction (if any)")
    edit_frame.pack(pady=10, fill="x", padx=20)

    tk.Label(edit_frame, text="Field:", bg=PANEL_BG, fg=TEXT, font=MONO_FONT).grid(row=0, column=0, padx=5, pady=5)
    wrong_field = tk.StringVar(value="NONE")
    field_options = ["NONE", "name", "class", "section", "admission number", "registration number", "email"]
    field_dropdown = ttk.Combobox(edit_frame, textvariable=wrong_field, values=field_options, state="readonly", width=20)
    field_dropdown.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(edit_frame, text="Correct Value:", bg=PANEL_BG, fg=TEXT, font=MONO_FONT).grid(row=1, column=0, padx=5, pady=5)
    corrected_value_entry = themed_entry(edit_frame, width=25)
    corrected_value_entry.grid(row=1, column=1, padx=5, pady=5)

    def toggle_entry(*args):
        if wrong_field.get() == "NONE":
            corrected_value_entry.config(state="disabled")
        else:
            corrected_value_entry.config(state="normal")
    wrong_field.trace("w", toggle_entry)
    toggle_entry()

    def submit():
        activity = simpledialog.askstring("Activity", "Enter the activity you participated in:")
        if not activity:
            activity = session_name
        attendance_status = status.get()

        with open(CSV_FILENAME, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d"),
                member["registration number"],
                member["name"],
                member["class"],
                member["section"],
                str(member["admission number"]),
                member["email"],
                attendance_status,
                activity,
                ""
            ])
        log_action(f"Attendance marked for {member['name']}: {attendance_status}, Activity: {activity}")

        if attendance_status == "Present":
            try:
                for idx, m in enumerate(all_members):
                    if str(m["registration number"]).strip() == str(member["registration number"]).strip():
                        current_val = int(m.get("attendance", 0))
                        col_num = list(m.keys()).index("attendance") + 1
                        member_ws.update_cell(idx + 2, col_num, current_val + 1)
                        break
            except Exception as e:
                messagebox.showwarning("Warning", f"Could not update attendance count:\n{e}")

        if wrong_field.get() != "NONE":
            new_val = str(corrected_value_entry.get().strip())
            if new_val:
                try:
                    edit_sheet = members_file.worksheet("Edit requests")
                    headers = edit_sheet.row_values(1) if edit_sheet.row_count > 0 else ["Timestamp", "Registration Number", "Field", "Old Value", "New Value", "Status"]
                    if edit_sheet.row_count == 0: edit_sheet.append_row(headers)
                    old_value = member[wrong_field.get()]
                    if not isinstance(old_value, str):
                        old_value = str(old_value)

                    edit_sheet.append_row([
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        str(member["registration number"]),
                        wrong_field.get(),
                        old_value,
                        new_val,
                        "Pending"
                    ])
                    
                    log_action(f"Member edit requested: {wrong_field.get()} from '{member[wrong_field.get()]}' to '{new_val}'")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to submit edit request:\n{e}")

        messagebox.showinfo("Done", "Attendance marked successfully.")
        member_win.destroy()

    tk.Button(member_win, text="Submit", command=submit, **button_style, cursor="hand2").pack(pady=20)


def voting_console():

    member = ask_for_member_lookup()
    if member is None:
        return

    params = {
        "name": member["name"],
        "class": member["class"],
        "section": member["section"],
        "admission_number": member["admission number"]
    }

    base_url = "https://innovationclubvotingwebsite.netlify.app/vote.html"
    query_string = urllib.parse.urlencode(params)
    autofill_url = f"{base_url}?{query_string}"

    webbrowser.open(autofill_url)
    log_action(f"Voting website opened. {member['name']}, {member ['class']}")


tk.Button(center_frame, text="Admin", command=admin_console, **button_style, cursor="hand2").pack(pady=15)
tk.Button(center_frame, text="Members", command=member_console, **button_style, cursor="hand2").pack(pady=15)
tk.Button(center_frame, text="Voting", command=voting_console, **button_style, cursor="hand2").pack(pady=15)

settings_button = tk.Button(
    root, 
    text="Settings", 
    command=show_settings_console,
        font=MONO_FONT,
    bg=ACCENT_2,
    fg=TEXT,
    cursor="hand2",
    width=12,
    relief="ridge",
    bd=2
)

def place_settings_button():
    settings_button.place(relx=0.0, rely=1.0, x=340, y=-15, anchor="sw")

root.after(100, place_settings_button)

root.mainloop()