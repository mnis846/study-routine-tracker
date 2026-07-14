"""Phone ↔ PC database sync — local SQLite backup and restore."""

import sqlite3
from datetime import datetime
from pathlib import Path

from tracker.database import DatabaseError, get_db_path

SYNC_FILE_PREFIX = "study_routine_tracker_sync"


def _sqlite_backup(src: Path, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(src)) as src_conn:
        with sqlite3.connect(str(dest)) as dest_conn:
            src_conn.backup(dest_conn)


def get_sync_metadata():
    path = Path(get_db_path())
    if not path.exists():
        return {
            "exists": False,
            "path": str(path),
            "size_kb": 0,
            "modified": None,
        }
    stat = path.stat()
    return {
        "exists": True,
        "path": str(path),
        "size_kb": round(stat.st_size / 1024, 1),
        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%d %b %Y, %I:%M %p"),
    }


def backup_database():
    path = Path(get_db_path())
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = path.with_name(f"{path.stem}_backup_{stamp}{path.suffix}")
    _sqlite_backup(path, backup_path)
    return str(backup_path)


def export_database(dest_path):
    src = Path(get_db_path())
    if not src.exists():
        raise DatabaseError("No database found to export.")
    dest = Path(dest_path)
    _sqlite_backup(src, dest)
    return str(dest.resolve())


def default_sync_filename():
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    return f"{SYNC_FILE_PREFIX}_{stamp}.db"


def import_database(src_path, *, backup_current=True):
    src = Path(src_path)
    if not src.exists():
        raise DatabaseError("Sync file not found.")
    if src.stat().st_size < 512:
        raise DatabaseError("Sync file looks empty or corrupt.")
    dest = Path(get_db_path())
    dest.parent.mkdir(parents=True, exist_ok=True)
    backup_path = None
    if backup_current and dest.exists():
        backup_path = backup_database()
    _sqlite_backup(src, dest)
    return {"imported_to": str(dest), "backup_path": backup_path}