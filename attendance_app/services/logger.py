from __future__ import annotations

from pathlib import Path
from datetime import datetime
from typing import Callable


def log_action(log_path: str | Path, action: str, sink: Callable[[str], None] | None = None) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {action}"

    print(entry)

    log_file = Path(log_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("a", encoding="utf-8") as file_handle:
        file_handle.write(entry + "\n")

    if sink is not None:
        sink(entry)

    return entry


def read_recent(log_path: str | Path, limit: int = 100) -> list[str]:
    log_file = Path(log_path)
    if not log_file.exists():
        return []
    with log_file.open("r", encoding="utf-8") as file_handle:
        return file_handle.readlines()[-limit:]
