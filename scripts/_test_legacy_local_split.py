"""Verify legacy profile is adopted (not split) and data survives."""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "study_routine_tracker.db"
sys.path.insert(0, str(ROOT))

tmp = Path(tempfile.mkdtemp(prefix="tracker_split_"))
shutil.copy2(SRC, tmp / "study_routine_tracker.db")
for s in ("-wal", "-shm"):
    p = Path(str(SRC) + s)
    if p.exists() and p.stat().st_size:
        shutil.copy2(p, tmp / f"study_routine_tracker.db{s}")

os.environ["TRACKER_DATA_DIR"] = str(tmp)

import database as db

print("Before:")
with db.db_connection(commit=False) as conn:
    for row in conn.execute("SELECT id, username FROM users"):
        print(" ", dict(row))
    xp = conn.execute(
        "SELECT user_id, value FROM app_settings WHERE key='garden_xp'"
    ).fetchall()
    print(" garden_xp", [dict(r) for r in xp])

db.init_db()
uid = db.get_current_user_id()
print("current user", uid)
print("display", db.get_local_display_name())
print("garden_xp", db.get_garden_xp())
assert db.get_garden_xp() == 150, "expected legacy garden XP retained"
status = db.get_data_status()
assert status["ok"], status
assert status["user_count"] == 1, status

with db.db_connection(commit=False) as conn:
    users = list(conn.execute("SELECT id, username FROM users"))
    print("users after", [dict(u) for u in users])
    assert len(users) == 1
    assert users[0]["username"] == "local"

db.add_daily_study_hours(date.today(), 2.5, "fix log")
assert abs(db.get_study_hours_for_date(date.today()) - 2.5) < 1e-9

# Second session
db._current_user_id.set(None)
db.init_db()
assert abs(db.get_study_hours_for_date(date.today()) - 2.5) < 1e-9
assert db.get_garden_xp() == 150

# Simulate bad split: create orphan then consolidate
with db.db_connection() as conn:
    conn.execute(
        """INSERT INTO users (username, email, first_name, last_name, password_hash)
           VALUES ('orphan', 'orphan@x', 'O', '', 'x')"""
    )
    orphan = int(
        conn.execute("SELECT id FROM users WHERE username='orphan'").fetchone()[0]
    )
    conn.execute(
        "INSERT INTO app_settings (user_id, key, value) VALUES (?, 'garden_xp', '20')",
        (orphan,),
    )
    conn.execute(
        "INSERT INTO daily_study_hours (user_id, log_date, hours, notes) VALUES (?, ?, ?, ?)",
        (orphan, "2026-07-01", 3.0, "orphan day"),
    )

db._current_user_id.set(None)
db.init_db()
assert db.get_data_status()["user_count"] == 1
# primary already had 150; orphan 20 should not overwrite
assert db.get_garden_xp() == 150
assert abs(db.get_study_hours_for_date(date.fromisoformat("2026-07-01")) - 3.0) < 1e-9

backup = db.read_database_backup_bytes()
assert len(backup) > 1000
print("ALL SPLIT / BACKUP CHECKS PASSED")
shutil.rmtree(tmp, ignore_errors=True)
