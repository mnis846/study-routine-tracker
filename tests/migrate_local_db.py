"""Apply ensure_local_user consolidation to the project SQLite file."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracker.database import get_data_status, get_garden_xp, get_local_display_name, init_db
from tracker.paths import get_db_path

print("DB:", get_db_path())
uid = init_db()
print("user_id:", uid)
print("status:", get_data_status())
print("display:", get_local_display_name())
print("garden_xp:", get_garden_xp())
