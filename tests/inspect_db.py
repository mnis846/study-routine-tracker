"""Inspect the project SQLite file (read-only)."""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracker.paths import get_db_path  # noqa: E402

DB = get_db_path()
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

ok = conn.execute("PRAGMA integrity_check").fetchone()[0]
print("integrity:", ok)
print("journal_mode:", conn.execute("PRAGMA journal_mode").fetchone()[0])
conn.close()
