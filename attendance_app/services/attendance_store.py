from __future__ import annotations

from csv import DictReader, reader, writer
from pathlib import Path
from typing import Iterable


ATTENDANCE_HEADER = [
    "Date",
    "Reg. No",
    "Name",
    "Class",
    "Section",
    "Admission No",
    "Email",
    "Status",
    "Activity",
    "Remarks",
]


def ensure_store(csv_path: str | Path) -> None:
    csv_file = Path(csv_path)
    if csv_file.exists():
        return
    csv_file.parent.mkdir(parents=True, exist_ok=True)
    with csv_file.open("w", newline="", encoding="utf-8") as file_handle:
        csv_writer = writer(file_handle)
        csv_writer.writerow(ATTENDANCE_HEADER)


def append_row(csv_path: str | Path, row: Iterable[str]) -> None:
    csv_file = Path(csv_path)
    csv_file.parent.mkdir(parents=True, exist_ok=True)
    with csv_file.open("a", newline="", encoding="utf-8") as file_handle:
        csv_writer = writer(file_handle)
        csv_writer.writerow(list(row))


def read_rows(csv_path: str | Path) -> list[list[str]]:
    csv_file = Path(csv_path)
    if not csv_file.exists():
        return []
    with csv_file.open(newline="", encoding="utf-8") as file_handle:
        return list(reader(file_handle))


def read_marked(csv_path: str | Path) -> dict[str, str]:
    marked: dict[str, str] = {}
    csv_file = Path(csv_path)
    if not csv_file.exists():
        return marked
    with csv_file.open(newline="", encoding="utf-8") as file_handle:
        for row in DictReader(file_handle):
            registration_number = str(row.get("Reg. No", "")).strip()
            if registration_number:
                marked[registration_number] = row.get("Status", "Present")
    return marked


def remove_row(csv_path: str | Path, registration_number: str) -> list[str] | None:
    csv_file = Path(csv_path)
    if not csv_file.exists():
        return None

    with csv_file.open(newline="", encoding="utf-8") as file_handle:
        rows = list(reader(file_handle))

    if not rows:
        return None

    header, body = rows[0], rows[1:]
    removed_row: list[str] | None = None
    remaining_rows: list[list[str]] = []
    for row in body:
        if removed_row is None and len(row) > 1 and row[1].strip() == registration_number.strip():
            removed_row = row
            continue
        remaining_rows.append(row)

    if removed_row is None:
        return None

    with csv_file.open("w", newline="", encoding="utf-8") as file_handle:
        csv_writer = writer(file_handle)
        csv_writer.writerow(header)
        csv_writer.writerows(remaining_rows)

    return removed_row
