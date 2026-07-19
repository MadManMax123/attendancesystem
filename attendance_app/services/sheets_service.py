from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

from ..config import AppConfig, DEFAULT_SCOPE
from .attendance_store import append_row, read_rows, remove_row


@dataclass
class SheetsService:
    client: Any
    member_sheet_key: str
    attendance_sheet_key: str

    @classmethod
    def connect(cls, config: AppConfig) -> "SheetsService":
        creds = Credentials.from_service_account_file(str(config.creds_file), scopes=config.scope or DEFAULT_SCOPE)
        client = gspread.authorize(creds)
        return cls(client=client, member_sheet_key=config.member_sheet_key, attendance_sheet_key=config.attendance_sheet_key)

    @property
    def member_sheet(self):
        return self.client.open_by_key(self.member_sheet_key).sheet1

    @property
    def attendance_book(self):
        return self.client.open_by_key(self.attendance_sheet_key)

    def get_members_df(self) -> pd.DataFrame:
        data = self.member_sheet.get_all_records()
        df = pd.DataFrame(data)
        if not df.empty:
            df.columns = df.columns.str.strip().str.lower()
            if "registration number" in df.columns:
                df["registration number"] = df["registration number"].astype(str).str.strip()
        return df

    def get_member_by_registration(self, registration_number: str) -> dict[str, Any] | None:
        df = self.get_members_df()
        if df.empty or "registration number" not in df.columns:
            return None
        match = df[df["registration number"] == str(registration_number).strip()]
        if match.empty:
            return None
        return match.iloc[0].to_dict()

    def get_member_by_admission(self, admission_number: str) -> dict[str, Any] | None:
        df = self.get_members_df()
        if df.empty or "admission number" not in df.columns:
            return None
        match = df[df["admission number"].astype(str).str.strip() == str(admission_number).strip()]
        if match.empty:
            return None
        return match.iloc[0].to_dict()

    def total_meetings(self) -> int:
        try:
            return max(len(self.attendance_book.worksheets()) - 1, 0)
        except Exception:
            return 0

    def update_member_attendance(self, registration_number: str, delta: int) -> None:
        all_members = self.member_sheet.get_all_records()
        for index, member in enumerate(all_members):
            if str(member.get("registration number", "")).strip() == str(registration_number).strip():
                current_val = int(member.get("attendance", 0) or 0)
                column_index = list(member.keys()).index("attendance") + 1
                self.member_sheet.update_cell(index + 2, column_index, max(current_val + delta, 0))
                break

    def mark_attendance(self, csv_path, member: dict[str, Any], status: str, activity: str, date_text: str | None = None) -> None:
        append_row(
            csv_path,
            [
                date_text or datetime.now().strftime("%Y-%m-%d"),
                str(member.get("registration number", "")).strip(),
                str(member.get("name", "")),
                str(member.get("class", "")),
                str(member.get("section", "")),
                str(member.get("admission number", "")),
                str(member.get("email", "")),
                status,
                activity,
                "",
            ],
        )
        if status == "Present":
            self.update_member_attendance(str(member.get("registration number", "")).strip(), 1)

    def remove_attendance(self, csv_path, registration_number: str) -> dict[str, Any] | None:
        removed_row = remove_row(csv_path, registration_number)
        if removed_row is None:
            return None
        status = removed_row[7] if len(removed_row) > 7 else "Present"
        if status == "Present":
            self.update_member_attendance(registration_number, -1)
        return {
            "date": removed_row[0] if len(removed_row) > 0 else "",
            "registration_number": removed_row[1] if len(removed_row) > 1 else registration_number,
            "name": removed_row[2] if len(removed_row) > 2 else "",
            "status": status,
            "activity": removed_row[8] if len(removed_row) > 8 else "",
        }

    def append_member(self, row: list[str]) -> None:
        self.member_sheet.append_row(row)

    def remove_member_row(self, registration_number: str) -> list[str] | None:
        all_rows = self.member_sheet.get_all_values()
        if not all_rows:
            return None
        headers = all_rows[0]
        for index, row in enumerate(all_rows[1:], start=2):
            if len(row) > 4 and row[4].strip() == registration_number.strip():
                self.member_sheet.delete_rows(index)
                return row
        return None

    def read_attendance_rows(self, csv_path):
        return read_rows(csv_path)

    def append_attendance_sheet(self, title: str, rows: list[list[str]]):
        sheet = self.attendance_book.add_worksheet(
            title=title,
            rows=str(len(rows)),
            cols=str(len(rows[0]) if rows else 1),
        )
        sheet.update("A1", rows)
        return sheet

    def session_sheet_title(self, session_name: str) -> str:
        title = f"{session_name} {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        return title[:50]
