from __future__ import annotations

from dataclasses import dataclass, field
import threading
from pathlib import Path
from typing import Any, Callable

from .config import AppConfig


@dataclass
class AppState:
    config: AppConfig
    sheet_lock: threading.Lock = field(default_factory=threading.Lock)
    client: Any = None
    member_sheet: Any = None
    attendance_sheet: Any = None
    sheets_service: Any = None
    log_sink: Callable[[str], None] | None = None

    @property
    def session_dir(self) -> Path:
        return self.config.session_dir

    @property
    def csv_path(self) -> Path:
        return self.config.csv_path

    @property
    def log_path(self) -> Path:
        return self.config.log_path

