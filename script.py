#231794889142224

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from datetime import datetime
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


APP_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
SESSION_DIR = os.path.join(APP_DIR, f"session_{SESSION_ID}")
os.makedirs(SESSION_DIR, exist_ok=True)

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

# Constants
with open(asset_path("password.json"), "r") as config_file:
    config = json.load(config_file)
ADMIN_PASSWORD_HASH = config.get("admin_password", "")

CSV_FILENAME = os.path.join(SESSION_DIR, "attendance.csv")
LOG_FILENAME = os.path.join(SESSION_DIR, "activity.log")
CREDS_FILE = os.path.join(ROOT_DIR, "attendance-system-462506-007af2102f9d.json")
PROGRAM_START_TIME = time.time()
MEMBER_SHEET_KEY = "1MExQ09sgUynZR36hQBeJuqSkPoDc4iR4iOkRASbLfZo"
ATTENDANCE_SHEET_KEY = "1urIRLaSK6Hi8usLoEg4FeAYfZRx-sXsVROlJVCMzyQc"

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
    
    if 'log_text' in globals():
        log_text.config(state="normal")
        log_text.insert("end", entry + "\n")
        log_text.see("end")
        log_text.config(state="disabled")


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
    style.configure("TButton", font=("Cascadia Code", 10, "bold"), padding=(12, 8))
    style.map("TButton",
              background=[("active", BUTTON_ACTIVE), ("!active", BUTTON_BG)],
              foreground=[("active", TEXT), ("!active", TEXT)])
    style.configure("Accent.TButton", background=BUTTON_BG, foreground=TEXT)
    style.configure("Treeview", background=CARD_BG, fieldbackground=CARD_BG, foreground=TEXT, rowheight=26)
    style.configure("Treeview.Heading", background=PANEL_BG, foreground=TEXT, font=("Cascadia Code", 10, "bold"))
    style.configure("TCombobox", fieldbackground=CARD_BG, background=CARD_BG, foreground=TEXT)


def build_session_header(parent):
    header = tk.Frame(parent, bg=BG)
    header.pack(fill="x", padx=18, pady=(14, 8))

    left = tk.Frame(header, bg=BG)
    left.pack(side="left", anchor="w")

    tk.Label(left, text="Innovation Club Attendance System", font=TITLE_FONT, fg=ACCENT_2, bg=BG).pack(anchor="w")
    tk.Label(left, text="Session storage is created automatically for every run.", font=SUBTITLE_FONT, fg=MUTED, bg=BG).pack(anchor="w", pady=(4, 0))

    right = tk.Frame(header, bg=BG)
    right.pack(side="right", anchor="e")
    tk.Label(right, text=f"Session: {os.path.basename(SESSION_DIR)}", font=("Cascadia Code", 10, "bold"), fg=ACCENT, bg=BG).pack(anchor="e")
    tk.Label(right, text=os.path.basename(LOG_FILENAME), font=("Cascadia Code", 9), fg=MUTED, bg=BG).pack(anchor="e")


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
        "font": font or ("Cascadia Code", 10, "bold"),
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
        font=("Cascadia Code", 11),
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
        font=("Cascadia Code", 11, "bold"),
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
        logo_img = Image.open(asset_path("Logo.png")).resize((60, 60))
        logo_img = ImageTk.PhotoImage(logo_img)
        tk.Label(settings_win, image=logo_img, bg=BG).place(relx=0.97, y=10, anchor="ne")
        settings_win.logo_img = logo_img
    except:
        pass

    themed_label(settings_win, "STATS", fg=ACCENT_2, font=("Cascadia Code", 24, "bold")).pack(pady=(18, 12))

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

    themed_label(settings_win, "Made by Satyaki Bandopadhyay", fg=MUTED, font=("Cascadia Code", 9)).pack(side="bottom", pady=12)


def ask_for_member_lookup():
    log_action("A/N or R/N prompt window")
    choice_win = tk.Toplevel()
    style_dialog_window(choice_win, "Choose Identification Method", "380x220", (360, 210))
    choice_win.grab_set()

    card = themed_frame(choice_win, border=True)
    card.pack(fill="both", expand=True, padx=16, pady=16)

    themed_label(card, "Select identification method:", font=("Cascadia Code", 13, "bold"), bg=PANEL_BG).pack(pady=(10, 12))

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

with open(CSV_FILENAME, "w", newline="") as f:
    log_action("Attendance CSV file created")
    writer = csv.writer(f)
    writer.writerow([
    "Date", "Reg. No", "Name", "Class", "Section",
    "Admission No", "Email", "Status", "Activity", "Remarks"
])


root = tk.Tk()
root.title("Innovation Club Attendance System")
root.geometry("1360x800")
root.minsize(1260, 740)
root.configure(bg=BG)
configure_styles()
build_session_header(root)

# Quick Entry Panel (Left Side)
quick_entry_frame = themed_frame(root, border=True)
quick_entry_frame.place(relx=0.02, rely=0.12, anchor="nw", width=320, relheight=0.80)

quick_title = tk.Label(quick_entry_frame, text="Quick Entry", fg=ACCENT, bg=PANEL_BG, font=("Cascadia Code", 16, "bold"))
quick_title.pack(pady=(16, 8))

activity_label = tk.Label(quick_entry_frame, text="Activity:", fg=TEXT, bg=PANEL_BG, font=("Cascadia Code", 11))
activity_label.pack(pady=(10, 5))

activity_entry = themed_entry(quick_entry_frame, width=25)
activity_entry.pack(pady=5, padx=10)

adm_label = tk.Label(quick_entry_frame, text="Admission Number:", fg=TEXT, bg=PANEL_BG, font=("Cascadia Code", 11))
adm_label.pack(pady=(20, 5))

adm_entry = themed_entry(quick_entry_frame, width=25)
adm_entry.pack(pady=5, padx=10)

def quick_submit():
    activity = activity_entry.get().strip()
    adm_no = adm_entry.get().strip()
    
    if not activity:
        messagebox.showerror("Missing Data", "Please enter an activity.")
        return
    
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
    font=("Cascadia Code", 11, "bold"),
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
    font=("Cascadia Code", 9),
    justify="left"
)
instructions.pack(pady=(30, 10))

# Activity Log Panel (Right Side)
log_frame = themed_frame(root, border=True)
log_frame.place(relx=0.98, rely=0.12, anchor="ne", width=350, relheight=0.80)

log_title = tk.Label(log_frame, text="Activity Log", fg=ACCENT_2, bg=PANEL_BG, font=("Cascadia Code", 15, "bold"))
log_title.pack(pady=(14, 6))

log_text = tk.Text(log_frame, wrap="word", bg=CARD_BG, fg=TEXT, font=("Cascadia Code", 10), state="disabled", relief="flat", padx=8, pady=8, highlightthickness=0)
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
    crest_img = Image.open(asset_path("school_logo.png")).resize((80, 80))
    crest_photo = ImageTk.PhotoImage(crest_img)
    crest_label = tk.Label(center_frame, image=crest_photo, bg=BG)
    crest_label.image = crest_photo
    crest_label.pack(pady=(0, 10))
except Exception as e:
    print(f"Failed to load crest: {e}")

try:
    logo_img = Image.open(asset_path("Logo.png")).resize((180, 180))
    logo = ImageTk.PhotoImage(logo_img)
    logo_canvas = tk.Canvas(center_frame, width=180, height=180, bg=BG, highlightthickness=0)
    logo_canvas.pack(pady=20)
    logo_canvas.create_image(90, 90, image=logo)
except Exception as e:
    print("Error loading logo:", e)

tk.Label(
    center_frame,
    text="INNOVATION CLUB\nATTENDANCE SYSTEM",
    font=("Cascadia Code", 26, "bold"),
    fg=TEXT, bg=BG
).pack(pady=10)

time_label = tk.Label(
    center_frame,
    text="",
    font=("Cascadia Code", 14, "bold"),
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
    "font": ("Cascadia Code", 11, "bold"),
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

    logo_img = Image.open(asset_path("Logo.png")).resize((80, 80))
    logo_tk = ImageTk.PhotoImage(logo_img)

    logo_label = tk.Label(admin_win, image=logo_tk, bg=BG)
    logo_label.image = logo_tk
    logo_label.place(relx=0.98, y=10, anchor='ne')

    header_frame = themed_frame(admin_win, bg=BG)
    header_frame.pack(pady=(12, 6), fill="x")

    themed_label(header_frame, text="ADMIN CONSOLE", font=("Cascadia Code", 20, "bold"), fg=ACCENT_2, bg=BG).pack()
    datetime_label = themed_label(header_frame, text="", font=("Cascadia Code", 11), fg=TEXT, bg=BG)
    datetime_label.pack()
    count_label = themed_label(header_frame, text="", font=("Cascadia Code", 11), fg=TEXT, bg=BG)
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
        sheet = attendance_sheet.add_worksheet(
            title=f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}",
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
                bg=BG, fg=WARNING, font=("Cascadia Code", 10), justify="left", wraplength=500
            )
            warning.pack(padx=16, pady=(14, 8))

            entry_label = tk.Label(
                pw_window,
                text="Enter new 4-letter password:",
                bg=BG, fg=TEXT, font=("Cascadia Code", 10, "bold")
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
                    font=("Cascadia Code", 11, "bold")
                )
                msg.pack(pady=(10, 5))

                pw_display = tk.Label(
                    preview_window,
                    text=rand_pw,
                    bg=BG, fg=TEXT,
                    font=("Cascadia Code", 16, "bold")
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
        font=("Cascadia Code", 26, "bold"),
        fg=ACCENT_2,
        bg=BG,
        justify="center"
    )
    title_label.pack(side="top", fill="x", pady=(18, 10))

    logo_img = Image.open(asset_path("Logo.png")).resize((80, 80))
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
    tk.Label(info_frame, text=info_text, justify="left", font=("Cascadia Code", 11), fg=TEXT, bg=BG).pack()

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
             font=("Cascadia Code", 28, "bold"),
             fg=color, bg=BG).pack()
        tk.Label(attendance_frame,
             text=comment, font=("Cascadia Code", 13), fg=color, bg=BG).pack()
    except Exception as e:
        log_action(f"Failed to fetch attendance: {e}")

    status_frame = themed_labelframe(member_win, "Mark Attendance")
    status_frame.pack(pady=10, padx=20, fill="x")
    status = tk.StringVar(value="Present")
    for val in ["Present", "Absent", "On Duty"]:
        tk.Radiobutton(status_frame, text=val, variable=status, value=val, bg=PANEL_BG, fg=TEXT, activebackground=PANEL_BG, activeforeground=TEXT, selectcolor=CARD_BG).pack(side="left", padx=12, pady=6)

    edit_frame = themed_labelframe(member_win, "Correction (if any)")
    edit_frame.pack(pady=10, fill="x", padx=20)

    tk.Label(edit_frame, text="Field:", bg=PANEL_BG, fg=TEXT, font=("Cascadia Code", 10)).grid(row=0, column=0, padx=5, pady=5)
    wrong_field = tk.StringVar(value="NONE")
    field_options = ["NONE", "name", "class", "section", "admission number", "registration number", "email"]
    field_dropdown = ttk.Combobox(edit_frame, textvariable=wrong_field, values=field_options, state="readonly", width=20)
    field_dropdown.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(edit_frame, text="Correct Value:", bg=PANEL_BG, fg=TEXT, font=("Cascadia Code", 10)).grid(row=1, column=0, padx=5, pady=5)
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
            messagebox.showerror("Missing Data", "Please enter an activity.")
            return
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
    font=("Cascadia Code", 9, "bold"),
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
