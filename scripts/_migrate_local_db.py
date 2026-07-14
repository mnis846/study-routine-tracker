"""Apply ensure_local_user consolidation to the project SQLite file."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import database as db

print("DB:", db.get_db_path())
uid = db.init_db()
print("user_id:", uid)
print("status:", db.get_data_status())
print("display:", db.get_local_display_name())
print("garden_xp:", db.get_garden_xp())
