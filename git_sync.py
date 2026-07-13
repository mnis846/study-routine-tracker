"""Export tracker data to JSON and push to GitHub when online."""

from __future__ import annotations

import hashlib
import json
import socket
import sqlite3
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from database import DatabaseError, get_db_path

REPO_ROOT = Path(__file__).resolve().parent
EXPORT_DIR = REPO_ROOT / "data"
LOG_DIR = REPO_ROOT / "logs"
STATE_FILE = LOG_DIR / "git-sync-state.json"
LOG_FILE = LOG_DIR / "git-sync.log"

# Idle background check — only a safety net; real syncs happen when you save data.
BACKGROUND_POLL_SECONDS = 10 * 3600
SCHEDULED_SYNC_SECONDS = 10 * 3600

TABLE_QUERIES = {
    "daily_plans": "SELECT * FROM daily_plans ORDER BY plan_date",
    "daily_target_items": (
        "SELECT * FROM daily_target_items ORDER BY plan_id, order_index, id"
    ),
    "daily_study_hours": "SELECT * FROM daily_study_hours ORDER BY log_date",
    "scheduled_tests": "SELECT * FROM scheduled_tests ORDER BY test_no, id",
    "app_settings": "SELECT * FROM app_settings ORDER BY key",
    "garden_events": "SELECT * FROM garden_events ORDER BY event_date, id",
    "study_activity_logs": (
        "SELECT * FROM study_activity_logs ORDER BY log_date, created_at, id"
    ),
}

_lock = threading.Lock()
_worker_started = False
_data_changed = threading.Event()
_last_attempt_monotonic = 0.0
_status = {
    "state": "idle",
    "message": "Waiting for internet",
    "last_success": None,
    "last_attempt": None,
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _write_log(message: str) -> None:
    line = f"{_utc_now()} {message}"
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except OSError:
        pass


def _set_status(state: str, message: str) -> None:
    _status["state"] = state
    _status["message"] = message
    _status["last_attempt"] = _utc_now()


def _load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_state(payload: dict) -> None:
    try:
        STATE_FILE.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        _write_log(f"STATE save failed: {exc}")


def is_online(timeout: float = 3.0) -> bool:
    probes = (("github.com", 443), ("1.1.1.1", 53))
    for host, port in probes:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            continue
    return False


def _rows_to_records(rows) -> list[dict]:
    return [dict(row) for row in rows]


def export_data_json(export_dir: Path | None = None) -> dict:
    db_path = Path(get_db_path())
    if not db_path.exists():
        raise DatabaseError("No database found to export.")

    target = export_dir or EXPORT_DIR
    target.mkdir(parents=True, exist_ok=True)

    counts: dict[str, int] = {}
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        for name, query in TABLE_QUERIES.items():
            rows = _rows_to_records(conn.execute(query).fetchall())
            counts[name] = len(rows)
            out_path = target / f"{name}.json"
            out_path.write_text(
                json.dumps(rows, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

    manifest = {
        "exported_at": _utc_now(),
        "source_db": str(db_path),
        "source_db_bytes": db_path.stat().st_size,
        "source_db_mtime": datetime.fromtimestamp(
            db_path.stat().st_mtime, tz=timezone.utc
        ).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "table_counts": counts,
    }
    manifest_path = target / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return manifest


def compute_data_fingerprint() -> str:
    db_path = Path(get_db_path())
    if not db_path.exists():
        return ""
    digest = hashlib.sha256()
    digest.update(str(db_path.stat().st_size).encode())
    digest.update(str(int(db_path.stat().st_mtime)).encode())
    with sqlite3.connect(str(db_path)) as conn:
        for name in TABLE_QUERIES:
            digest.update(name.encode())
            row = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()
            digest.update(str(row[0]).encode())
    return digest.hexdigest()


def _run_git(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _current_branch() -> str:
    result = _run_git(["rev-parse", "--abbrev-ref", "HEAD"])
    if result.returncode != 0:
        return "main"
    return (result.stdout or "main").strip() or "main"


def sync_to_github(*, force: bool = False) -> dict:
    global _last_attempt_monotonic

    with _lock:
        _last_attempt_monotonic = time.monotonic()
        if not is_online():
            _set_status("offline", "No internet — will retry when online")
            return {"ok": False, "reason": "offline"}

        db_path = Path(get_db_path())
        if not db_path.exists():
            _set_status("idle", "No database yet")
            return {"ok": False, "reason": "no_database"}

        fingerprint = compute_data_fingerprint()
        state = _load_state()
        if not force and fingerprint and fingerprint == state.get("fingerprint"):
            _set_status("up_to_date", "Already synced to GitHub")
            return {"ok": True, "reason": "unchanged"}

        _set_status("syncing", "Exporting data and pushing to GitHub...")
        try:
            manifest = export_data_json(EXPORT_DIR)
        except DatabaseError as exc:
            _set_status("error", f"Export failed: {exc}")
            _write_log(f"EXPORT failed: {exc}")
            return {"ok": False, "reason": "export_failed", "error": str(exc)}

        _run_git(["add", "--", "data"])
        diff = _run_git(["diff", "--cached", "--quiet", "--", "data"])
        if diff.returncode == 0:
            state["fingerprint"] = fingerprint
            state["last_checked"] = _utc_now()
            _save_state(state)
            _set_status("up_to_date", "Already synced to GitHub")
            return {"ok": True, "reason": "unchanged"}

        stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        total_rows = sum(manifest.get("table_counts", {}).values())
        commit_msg = f"data: sync study logs ({total_rows} rows) · {stamp}"
        commit = _run_git(["commit", "-m", commit_msg, "--", "data"])
        if commit.returncode != 0:
            message = (commit.stderr or commit.stdout or "git commit failed").strip()
            _set_status("error", message)
            _write_log(f"COMMIT failed: {message}")
            return {"ok": False, "reason": "commit_failed", "error": message}

        branch = _current_branch()
        pull = _run_git(["pull", "--rebase", "--autostash", "origin", branch])
        if pull.returncode != 0:
            message = (pull.stderr or pull.stdout or "git pull failed").strip()
            _set_status("error", message)
            _write_log(f"PULL failed: {message}")
            return {"ok": False, "reason": "pull_failed", "error": message}

        push = _run_git(["push", "origin", branch])
        if push.returncode != 0:
            message = (push.stderr or push.stdout or "git push failed").strip()
            _set_status("error", message)
            _write_log(f"PUSH failed: {message}")
            return {"ok": False, "reason": "push_failed", "error": message}

        success_at = _utc_now()
        state.update(
            {
                "fingerprint": fingerprint,
                "last_success": success_at,
                "last_commit": commit_msg,
                "branch": branch,
            }
        )
        _save_state(state)
        _status["last_success"] = success_at
        _set_status("synced", f"Pushed to GitHub ({branch})")
        _write_log(f"OK {commit_msg}")
        return {"ok": True, "reason": "pushed", "commit": commit_msg, "branch": branch}


def notify_data_changed() -> None:
    _data_changed.set()


def get_sync_status() -> dict:
    state = _load_state()
    return {
        **_status,
        "online": is_online(timeout=1.5),
        "export_dir": str(EXPORT_DIR),
        "last_success": state.get("last_success") or _status.get("last_success"),
        "last_commit": state.get("last_commit"),
        "branch": state.get("branch") or _current_branch(),
    }


def _worker_loop() -> None:
    while True:
        triggered = _data_changed.wait(timeout=BACKGROUND_POLL_SECONDS)
        if triggered:
            _data_changed.clear()

        if not is_online():
            if _status["state"] not in {"offline", "syncing"}:
                _set_status("offline", "No internet — will retry when online")
            continue

        elapsed = time.monotonic() - _last_attempt_monotonic
        if triggered or elapsed >= SCHEDULED_SYNC_SECONDS:
            sync_to_github()


def start_background_sync() -> None:
    global _worker_started
    if _worker_started:
        return
    _worker_started = True
    thread = threading.Thread(target=_worker_loop, name="git-sync", daemon=True)
    thread.start()
    _write_log("Background git sync started")