"""Project path helpers — single source of truth for roots and data dirs."""

from __future__ import annotations

import os
from pathlib import Path

# tracker/paths.py → project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]

ASSETS_DIR = PROJECT_ROOT / "assets"
GAMES_DIR = PROJECT_ROOT / "games"
STICKERS_DIR = ASSETS_DIR / "stickers"
DOCS_DIR = PROJECT_ROOT / "docs"


def resolve_data_dir() -> Path:
    """Writable directory for SQLite (Cloud repo mount is read-only)."""
    override = os.environ.get("TRACKER_DATA_DIR")
    if override:
        path = Path(override)
    elif Path("/mount/src").exists() or os.environ.get("STREAMLIT_RUNTIME_ENV") == "cloud":
        path = Path.home() / ".study_routine_tracker"
    else:
        path = PROJECT_ROOT
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_db_path() -> Path:
    return resolve_data_dir() / "study_routine_tracker.db"
