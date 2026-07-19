from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_app_config
from .services.attendance_store import ensure_store
from .services.logger import log_action
from .services.sheets_service import SheetsService
from .state import AppState


def bootstrap(app_dir: str | Path, session_name: str) -> tuple[AppState, SheetsService]:
    config = load_app_config(app_dir, session_name)
    state = AppState(config=config)
    ensure_store(state.csv_path)
    sheets = SheetsService.connect(config)
    state.client = sheets.client
    state.member_sheet = sheets.member_sheet
    state.attendance_sheet = sheets.attendance_book
    log_action(state.log_path, f"Modular bootstrap initialized for session {config.session_id}")
    return state, sheets


def main() -> int:
    parser = argparse.ArgumentParser(description="Modular attendance app bootstrap")
    parser.add_argument("session_name", help="Session name used to create the session directory")
    parser.add_argument("--app-dir", default=Path(__file__).resolve().parents[1], type=Path)
    args = parser.parse_args()

    bootstrap(args.app_dir, args.session_name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
