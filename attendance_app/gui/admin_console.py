from __future__ import annotations

from dataclasses import replace
from datetime import datetime
import csv
import hashlib
import json
import random
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

import pandas as pd

from ..services.logger import log_action
from ..services.attendance_store import read_rows
from .dialogs import ask_for_member_lookup, verify_password
from .theme_widgets import themed_button, themed_entry, themed_frame, themed_label, themed_labelframe, style_dialog_window


def show_admin_console(root, state) -> None:
    config = state.config

    pw = simpledialog.askstring("Admin Login", "Enter admin password:", show="*", parent=root)
    if pw is None:
        messagebox.showerror("Error", "Please enter a proper password.")
        log_action(state.log_path, "No password entered", sink=state.log_sink)
        return
    if not verify_password(state, pw):
        messagebox.showerror("Access Denied", "Incorrect password!")
        log_action(state.log_path, "Incorrect password entered", sink=state.log_sink)
        return

    log_action(state.log_path, "Admin console accessed", sink=state.log_sink)

    admin_win = tk.Toplevel(root)
    style_dialog_window(admin_win, config, "Admin Console", "560x560", (520, 520))

    header_frame = themed_frame(admin_win, config, bg=config.theme["BG"])
    header_frame.pack(pady=(12, 6), fill="x")

    themed_label(header_frame, config, "ADMIN CONSOLE", font=tuple(config.theme["TITLE_FONT"]), fg=config.theme["ACCENT_2"], bg=config.theme["BG"]).pack()
    datetime_label = themed_label(header_frame, config, "", font=tuple(config.theme["MONO_FONT"]), fg=config.theme["TEXT"], bg=config.theme["BG"])
    datetime_label.pack()
    count_label = themed_label(header_frame, config, "", font=tuple(config.theme["MONO_FONT"]), fg=config.theme["TEXT"], bg=config.theme["BG"])
    count_label.pack()

    def update_datetime() -> None:
        if not admin_win.winfo_exists():
            return
        datetime_label.config(text=f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        count_label.config(text=f"Total Members: {len(state.sheets_service.get_members_df())}")
        admin_win.after(1000, update_datetime)

    update_datetime()

    def add_member() -> None:
        def is_valid_email(email: str) -> bool:
            return email.endswith("@dpsn.org.in") and "@" in email

        def is_valid_class(value: str) -> bool:
            return value.isdigit() and 1 <= int(value) <= 12

        def is_valid_section(value: str) -> bool:
            return len(value) == 1 and value.isalpha() and value.isupper()

        def is_valid_string(value: str) -> bool:
            return len(value.strip()) > 0

        fields = {
            "name": is_valid_string,
            "class": is_valid_class,
            "section": is_valid_section,
            "admission number": is_valid_string,
            "registration number": is_valid_string,
            "email": is_valid_email,
        }

        new_data: list[str] = []
        for field, validator in fields.items():
            while True:
                value = simpledialog.askstring("Input", f"Enter {field.title()}:", parent=admin_win)
                if value is None:
                    messagebox.showinfo("Cancelled", "Member addition cancelled.")
                    return
                value = value.strip()
                if validator(value):
                    new_data.append(value)
                    break
                messagebox.showerror(
                    "Invalid Input",
                    "Please enter a valid value." + (
                        "\n- Email must end with @dpsn.org.in" if field == "email" else ""
                    ) + (
                        "\n- Class must be a number from 1 to 12" if field == "class" else ""
                    ) + (
                        "\n- Section must be one uppercase letter (A-Z)" if field == "section" else ""
                    ),
                )

        confirm = messagebox.askyesno(
            "Confirm Member",
            "Add the following member?\n\n" + "\n".join(f"{key.title()}: {value}" for key, value in zip(fields.keys(), new_data)),
            parent=admin_win,
        )
        if not confirm:
            messagebox.showinfo("Cancelled", "Member addition cancelled.")
            return

        try:
            past_sheet = state.client.open_by_key(config.member_sheet_key).worksheet("Past members")
            past_rows = past_sheet.get_all_values()
            for index, row in enumerate(past_rows[1:], start=2):
                if len(row) < 5:
                    continue
                if row[4].strip() == new_data[4].strip() or row[3].strip() == new_data[3].strip():
                    past_sheet.delete_rows(index)
                    log_action(state.log_path, f"Old record removed from 'Past members'. Reg: {row[4]}, Adm: {row[3]}", sink=state.log_sink)
                    break
        except Exception as exc:
            log_action(state.log_path, f"Failed to clean up 'Past members' during add: {exc}", sink=state.log_sink)

        state.sheets_service.append_member(new_data)
        messagebox.showinfo("Success", "Member added successfully.", parent=admin_win)
        log_action(state.log_path, f"New member added. {new_data[0]}, {new_data[3]}", sink=state.log_sink)

    def remove_member() -> None:
        member = ask_for_member_lookup(root, state)
        if member is None:
            return

        try:
            all_rows = state.member_sheet.get_all_values()
            headers = all_rows[0]
            for row_index, row in enumerate(all_rows[1:], start=2):
                if len(row) > 4 and row[4].strip() == str(member["registration number"]).strip():
                    member_info = "\n".join(f"{headers[column_index]}: {row[column_index]}" for column_index in range(len(headers)))
                    confirm = messagebox.askyesno("Confirm Removal", f"Are you sure you want to remove this member?\n\n{member_info}", parent=admin_win)
                    if not confirm:
                        messagebox.showinfo("Cancelled", "Member removal cancelled.")
                        log_action(state.log_path, "Member removal cancelled", sink=state.log_sink)
                        return

                    reason = simpledialog.askstring("Removal Reason", "Enter reason for removal:", parent=admin_win)
                    if not reason or not reason.strip():
                        messagebox.showwarning("Cancelled", "Member removal cancelled (no valid reason provided).", parent=admin_win)
                        log_action(state.log_path, "Removal cancelled due to blank reason.", sink=state.log_sink)
                        return

                    date_removed = datetime.now().strftime("%Y-%m-%d")
                    members_file = state.client.open_by_key(config.member_sheet_key)
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

                    row_dict = {headers[column_index]: row[column_index] if column_index < len(row) else "" for column_index in range(len(headers))}
                    row_dict["Removal Reason"] = reason
                    row_dict["Date of Removal"] = date_removed
                    final_row = [row_dict.get(col, "") for col in existing_headers]
                    past_members_sheet.append_row(final_row)

                    state.sheets_service.remove_member_row(str(member["registration number"]))
                    messagebox.showinfo("Removed", "Member removed and added to 'Past members'.", parent=admin_win)
                    log_action(state.log_path, f"Member removed. {member['name']}, {member['admission number']}, Reason: {reason}, Date: {date_removed}", sink=state.log_sink)
                    return
            messagebox.showerror("Not Found", f"Registration number {member['registration number']} not found.", parent=admin_win)
        except Exception as exc:
            messagebox.showerror("Error", f"An error occurred:\n{exc}", parent=admin_win)

    def view_member() -> None:
        member = ask_for_member_lookup(root, state)
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
        messagebox.showinfo("Member Details", info, parent=admin_win)
        log_action(state.log_path, f"View member: {member['name']}, {member['admission number']}", sink=state.log_sink)

    def list_members() -> None:
        df = state.sheets_service.get_members_df()
        top = tk.Toplevel(admin_win)
        style_dialog_window(top, config, "Member List", "820x520", (760, 460))
        tree = ttk.Treeview(top)
        tree["columns"] = list(df.columns)
        tree["show"] = "headings"
        for column in df.columns:
            tree.heading(column, text=str(column).title())
            tree.column(column, width=100)
        for _, row in df.iterrows():
            tree.insert("", "end", values=list(row))
        tree.pack(expand=True, fill="both", padx=12, pady=12)
        log_action(state.log_path, "Members list accessed", sink=state.log_sink)

    def end_session() -> None:
        df = state.sheets_service.get_members_df()
        attendance_rows = read_rows(state.csv_path)
        scanned = [str(row[1]).strip() for row in attendance_rows[1:] if len(row) > 1]
        for _, row in df.iterrows():
            if str(row["registration number"]).strip() not in scanned:
                state.sheets_service.mark_attendance(
                    state.csv_path,
                    row.to_dict(),
                    "Absent",
                    config.session_name,
                )

        content = read_rows(state.csv_path)
        if not content:
            messagebox.showwarning("Empty", "No attendance data to upload.", parent=admin_win)
            return

        sheet_title = state.sheets_service.session_sheet_title(config.session_id)
        state.sheets_service.append_attendance_sheet(sheet_title, content)
        messagebox.showinfo("Uploaded", "Session data uploaded to Google Sheets.", parent=admin_win)
        log_action(state.log_path, "Records updated to sheets", sink=state.log_sink)
        admin_win.destroy()

    def edit_member_requests() -> None:
        try:
            members_file = state.client.open_by_key(config.member_sheet_key)
            edit_sheet = members_file.worksheet("Edit requests")
            member_sheet = members_file.worksheet("Members")
            all_requests = edit_sheet.get_all_records()
            if not all_requests:
                messagebox.showinfo("No Requests", "There are no edit requests.", parent=admin_win)
                return

            pending_requests = [request for request in all_requests if request.get("Status", "Pending") == "Pending"]
            if not pending_requests:
                messagebox.showinfo("No Pending", "No pending edit requests.", parent=admin_win)
                return

            member_df = pd.DataFrame(member_sheet.get_all_records())
            win = tk.Toplevel(admin_win)
            style_dialog_window(win, config, "Edit Requests", "860x560", (780, 500))

            tree = ttk.Treeview(win, columns=["Time", "Reg No", "Field", "Old", "New", "Status"], show="headings")
            for col in ["Time", "Reg No", "Field", "Old", "New", "Status"]:
                tree.heading(col, text=col)
                tree.column(col, width=100)
            for index, request in enumerate(pending_requests):
                tree.insert("", "end", iid=index, values=(request["Time"], request["registration number"], request["Field"], request["Old Value"], request["New Value"], "Pending"))
            tree.pack(expand=True, fill="both", padx=12, pady=12)

            def approve() -> None:
                selected = tree.selection()
                for selected_id in selected:
                    idx = int(selected_id)
                    req = pending_requests[idx]
                    reg = req["registration number"]
                    field = req["Field"]
                    new_val = req["New Value"]

                    row_idx = member_df.index[member_df["registration number"] == reg].tolist()
                    if not row_idx:
                        messagebox.showerror("Error", f"Reg. No. {reg} not found.", parent=win)
                        continue
                    row_num = row_idx[0] + 2
                    col_list = member_df.columns.tolist()
                    if field not in col_list:
                        messagebox.showerror("Error", f"Field {field} not found in Members sheet.", parent=win)
                        continue
                    col_num = col_list.index(field) + 1
                    member_sheet.update_cell(row_num, col_num, new_val)
                    edit_sheet.update_cell(idx + 2, 6, "Approved")
                    tree.set(selected_id, column="Status", value="Approved")
                    log_action(state.log_path, f"Member details update approved. {field} to {new_val}", sink=state.log_sink)

            def reject() -> None:
                selected = tree.selection()
                for selected_id in selected:
                    idx = int(selected_id)
                    edit_sheet.update_cell(idx + 2, 6, "Rejected")
                    tree.set(selected_id, column="Status", value="Rejected")
                    log_action(state.log_path, "Member details update rejected.", sink=state.log_sink)

            themed_button(win, config, "Approve Selected", approve, width=20).pack(pady=5)
            themed_button(win, config, "Reject Selected", reject, width=20).pack(pady=5)
            themed_button(win, config, "Close", win.destroy, width=20).pack(pady=10)
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to load edit requests:\n{exc}", parent=admin_win)

    def change_admin_password() -> None:
        def generate_random_password() -> str:
            return "".join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", k=4))

        def update_password(new_password: str) -> None:
            password_hash = hashlib.sha256(new_password.encode()).hexdigest()
            with open(config.password_path, "w", encoding="utf-8") as file_handle:
                json.dump({"admin_password": password_hash}, file_handle)
            state.config = replace(state.config, admin_password_hash=password_hash)
            log_action(state.log_path, "Admin password updated", sink=state.log_sink)
            messagebox.showinfo("Success", "Admin password updated successfully!", parent=admin_win)

        pw_window = tk.Toplevel(admin_win)
        style_dialog_window(pw_window, config, "Change Admin Password", "620x430", (580, 400))

        warning = tk.Label(
            pw_window,
            text="Please note that your password must be exactly 4 letters.\nOnce you change this password, get the RFID admin tag updated as well for convenience.",
            bg=config.theme["BG"],
            fg=config.theme["WARNING"],
            font=tuple(config.theme["MONO_FONT"]),
            justify="left",
            wraplength=500,
        )
        warning.pack(padx=16, pady=(14, 8))

        tk.Label(pw_window, text="Enter new 4-letter password:", bg=config.theme["BG"], fg=config.theme["TEXT"], font=tuple(config.theme["MONO_FONT"])).pack()
        pw_entry = themed_entry(pw_window, config, width=25, center=True)
        pw_entry.pack(pady=5)

        def save_manual() -> None:
            new_password = pw_entry.get()
            if len(new_password) != 4 or not new_password.isalpha():
                messagebox.showerror("Invalid", "Password must be exactly 4 letters.", parent=pw_window)
                return
            update_password(new_password)
            pw_window.destroy()

        def use_random() -> None:
            random_password = generate_random_password()
            preview_window = tk.Toplevel(pw_window)
            style_dialog_window(preview_window, config, "Generated Password", "360x220", (340, 200))
            tk.Label(preview_window, text="Generated Password:", bg=config.theme["BG"], fg=config.theme["ACCENT"], font=tuple(config.theme["MONO_FONT"])).pack(pady=(10, 5))
            tk.Label(preview_window, text=random_password, bg=config.theme["BG"], fg=config.theme["TEXT"], font=tuple(config.theme["MONO_FONT"])).pack(pady=(0, 10))

            def confirm_save() -> None:
                update_password(random_password)
                preview_window.destroy()
                pw_window.destroy()

            btn_frame = tk.Frame(preview_window, bg=config.theme["BG"])
            btn_frame.pack(pady=10)
            themed_button(btn_frame, config, "Save Password", confirm_save, bg=config.theme["ACCENT_2"], fg=config.theme["BG"]).grid(row=0, column=0, padx=10)
            themed_button(btn_frame, config, "Cancel", preview_window.destroy, bg=config.theme["ERROR"], fg=config.theme["TEXT"]).grid(row=0, column=1, padx=10)

        themed_button(pw_window, config, "Save Entered Password", save_manual, bg=config.theme["ACCENT"], fg=config.theme["BG"]).pack(pady=5)
        themed_button(pw_window, config, "Generate 4-letter Password", use_random, bg=config.theme["ACCENT_2"], fg=config.theme["BG"]).pack(pady=5)

    button_style = {
        "width": 20,
        "font": tuple(config.theme["MONO_FONT"]),
        "bg": config.theme["BUTTON_BG"],
        "fg": config.theme["TEXT"],
        "activebackground": config.theme["BUTTON_ACTIVE"],
        "activeforeground": config.theme["TEXT"],
        "relief": "ridge",
        "bd": 3,
        "cursor": "hand2",
    }

    themed_button(admin_win, config, "Add Member", add_member, width=20).pack(pady=10)
    themed_button(admin_win, config, "Remove Member", remove_member, width=20).pack(pady=10)
    themed_button(admin_win, config, "List Members", list_members, width=20).pack(pady=10)
    themed_button(admin_win, config, "View Member", view_member, width=20).pack(pady=10)
    themed_button(admin_win, config, "View Edit Requests", edit_member_requests, width=20).pack(pady=10)
    themed_button(admin_win, config, "Change Admin Password", change_admin_password, width=20).pack(pady=10)
    themed_button(admin_win, config, "End Session & Upload", end_session, width=20).pack(pady=40)
