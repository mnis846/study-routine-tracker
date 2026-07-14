"""Inspect the project SQLite file (read-only)."""
from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "study_routine_tracker.db"
print("DB:", DB, "exists=", DB.exists(), "size=", DB.stat().st_size if DB.exists() else 0)
if not DB.exists():
    raise SystemExit(0)

conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY 1")]
print("tables:", tables)
if "users" in tables:
    for row in conn.execute("SELECT id, username, email, first_name FROM users"):
        print(" user", dict(row))
for t in tables:
    try:
        n = conn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
        print(f"  {t}: {n}")
    except Exception as e:
        print(f"  {t}: ERR {e}")

# Per-user data split check
if "users" in tables and "daily_study_hours" in tables:
    print("hours by user:")
    for row in conn.execute(
        "SELECT user_id, COUNT(*) c, COALESCE(SUM(hours),0) h FROM daily_study_hours GROUP BY user_id"
    ):
        print(" ", dict(row))
if "users" in tables and "daily_plans" in tables:
    print("plans by user:")
    for row in conn.execute(
        "SELECT user_id, COUNT(*) c FROM daily_plans GROUP BY user_id"
    ):
        print(" ", dict(row))
if "app_settings" in tables:
    print("settings:")
    for row in conn.execute("SELECT user_id, key, value FROM app_settings ORDER BY user_id, key"):
        print(" ", dict(row))

ok = conn.execute("PRAGMA integrity_check").fetchone()[0]
print("integrity:", ok)
# journal mode
jm = conn.execute("PRAGMA journal_mode").fetchone()[0]
print("journal_mode:", jm)
conn.close()

# WAL sidecars
for suffix in ("", "-wal", "-shm"):
    p = Path(str(DB) + suffix) if suffix else DB
    if p.exists():
        print(f"file {p.name}: {p.stat().st_size} bytes")
