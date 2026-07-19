from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json
import re
from typing import Any


DEFAULT_THEME = {
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
    "CLUB_NAME": "club",
    "LOGO_FILE": "Logo.png",
    "CREST_FILE": "school_logo.png",
}

DEFAULT_SCOPE = (
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
)


@dataclass(frozen=True)
class AppConfig:
    app_dir: Path
    root_dir: Path
    session_name: str
    session_id: str
    session_dir: Path
    csv_path: Path
    log_path: Path
    theme_path: Path
    env_path: Path
    password_path: Path
    creds_file: Path
    member_sheet_key: str
    attendance_sheet_key: str
    admin_password_hash: str
    theme: dict[str, Any]
    scope: tuple[str, ...] = DEFAULT_SCOPE

    @property
    def club_name(self) -> str:
        return str(self.theme.get("CLUB_NAME", DEFAULT_THEME["CLUB_NAME"]))

    @property
    def club_name_title(self) -> str:
        return self.club_name.title()

    @property
    def club_name_upper(self) -> str:
        return self.club_name.upper()

    @property
    def logo_file(self) -> str:
        return str(self.theme.get("LOGO_FILE", DEFAULT_THEME["LOGO_FILE"]))

    @property
    def crest_file(self) -> str:
        return str(self.theme.get("CREST_FILE", DEFAULT_THEME["CREST_FILE"]))


def sanitize_session_name(session_name: str) -> str:
    safe_name = re.sub(r"[^A-Za-z0-9_-]", "_", session_name.strip())
    return safe_name or "session"


def load_json_file(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as file_handle:
            data = json.load(file_handle)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def load_theme(theme_path: Path) -> dict[str, Any]:
    theme_data = DEFAULT_THEME.copy()
    theme_data.update(load_json_file(theme_path))
    return theme_data


def load_app_config(app_dir: str | Path, session_name: str) -> AppConfig:
    app_dir_path = Path(app_dir)
    root_dir = app_dir_path
    session_id = sanitize_session_name(session_name)
    session_dir = root_dir / f"session_{session_id}"
    if session_dir.exists():
        session_dir = root_dir / f"session_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    session_dir.mkdir(parents=True, exist_ok=True)

    theme_path = root_dir / "theme.json"
    env_path = root_dir / "envvars.json"
    password_path = root_dir / "password.json"
    theme = load_theme(theme_path)
    env = load_json_file(env_path)
    password_data = load_json_file(password_path)

    required_keys = ["creds_file", "member_sheet_key", "attendance_sheet_key"]
    missing = [key for key in required_keys if not env.get(key)]
    if missing:
        raise RuntimeError(f"Missing required key(s) in {env_path}: {', '.join(missing)}")

    creds_file = root_dir / str(env["creds_file"])

    return AppConfig(
        app_dir=app_dir_path,
        root_dir=root_dir,
        session_name=session_name.strip(),
        session_id=session_id,
        session_dir=session_dir,
        csv_path=session_dir / "attendance.csv",
        log_path=session_dir / "activity.log",
        theme_path=theme_path,
        env_path=env_path,
        password_path=password_path,
        creds_file=creds_file,
        member_sheet_key=str(env["member_sheet_key"]),
        attendance_sheet_key=str(env["attendance_sheet_key"]),
        admin_password_hash=str(password_data.get("admin_password", "")),
        theme=theme,
    )
