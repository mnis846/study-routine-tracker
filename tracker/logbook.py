"""Study activity logbook — per-user SQLite journal."""

import pandas as pd

from tracker.database import DatabaseError, db_connection, get_current_user_id

_UNSET = object()


def _date_str(value):
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def ensure_logbook_schema():
    """Create logbook tables if missing (safe on existing databases)."""
    with db_connection() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS study_activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                log_date DATE NOT NULL,
                subject TEXT DEFAULT '',
                activity TEXT NOT NULL,
                duration_hours REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )"""
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_activity_logs_user_date "
            "ON study_activity_logs(user_id, log_date)"
        )


def add_activity_log(log_date, activity, subject="", duration_hours=None):
    ensure_logbook_schema()
    uid = get_current_user_id()
    activity = (activity or "").strip()
    if not activity:
        raise DatabaseError("Activity description is required.")
    date_str = _date_str(log_date)
    duration = None
    if duration_hours is not None and duration_hours != "":
        duration = max(0.0, float(duration_hours))
    with db_connection() as conn:
        c = conn.cursor()
        c.execute(
            """INSERT INTO study_activity_logs
               (user_id, log_date, subject, activity, duration_hours)
               VALUES (?, ?, ?, ?, ?)""",
            (uid, date_str, (subject or "").strip(), activity, duration),
        )
        return c.lastrowid


def get_activity_logs(log_date=None, year=None, month=None, limit=200):
    ensure_logbook_schema()
    uid = get_current_user_id()
    clauses = ["user_id = ?"]
    params: list = [uid]
    if log_date is not None:
        clauses.append("log_date = ?")
        params.append(_date_str(log_date))
    if year is not None:
        clauses.append("strftime('%Y', log_date) = ?")
        params.append(str(int(year)))
    if month is not None:
        clauses.append("strftime('%m', log_date) = ?")
        params.append(f"{int(month):02d}")
    where = f"WHERE {' AND '.join(clauses)}"
    params.append(int(limit))
    with db_connection(commit=False) as conn:
        return pd.read_sql(
            f"""SELECT id, log_date, subject, activity, duration_hours,
                       created_at, updated_at
                FROM study_activity_logs
                {where}
                ORDER BY log_date DESC, created_at DESC
                LIMIT ?""",
            conn,
            params=tuple(params),
        )


def get_activity_log_stats(year=None):
    ensure_logbook_schema()
    uid = get_current_user_id()
    clauses = ["user_id = ?"]
    params: list = [uid]
    if year is not None:
        clauses.append("strftime('%Y', log_date) = ?")
        params.append(str(int(year)))
    where = f"WHERE {' AND '.join(clauses)}"
    with db_connection(commit=False) as conn:
        c = conn.cursor()
        c.execute(f"SELECT COUNT(*) FROM study_activity_logs {where}", params)
        total_entries = int(c.fetchone()[0])
        c.execute(
            f"SELECT COUNT(DISTINCT log_date) FROM study_activity_logs {where}",
            params,
        )
        days_logged = int(c.fetchone()[0])
    return {"total_entries": total_entries, "days_logged": days_logged}


def update_activity_log(
    entry_id,
    *,
    log_date=None,
    activity=None,
    subject=None,
    duration_hours=_UNSET,
):
    ensure_logbook_schema()
    uid = get_current_user_id()
    fields = []
    params = []
    if log_date is not None:
        fields.append("log_date = ?")
        params.append(_date_str(log_date))
    if activity is not None:
        activity = activity.strip()
        if not activity:
            raise DatabaseError("Activity description is required.")
        fields.append("activity = ?")
        params.append(activity)
    if subject is not None:
        fields.append("subject = ?")
        params.append(subject.strip())
    if duration_hours is not _UNSET:
        if duration_hours is None or duration_hours == "":
            fields.append("duration_hours = ?")
            params.append(None)
        else:
            fields.append("duration_hours = ?")
            params.append(max(0.0, float(duration_hours)))
    if not fields:
        return
    fields.append("updated_at = CURRENT_TIMESTAMP")
    params.extend([int(entry_id), uid])
    with db_connection() as conn:
        c = conn.cursor()
        c.execute(
            f"UPDATE study_activity_logs SET {', '.join(fields)} WHERE id = ? AND user_id = ?",
            params,
        )
        if c.rowcount == 0:
            raise DatabaseError("Activity log entry not found.")


def delete_activity_log(entry_id):
    ensure_logbook_schema()
    uid = get_current_user_id()
    with db_connection() as conn:
        c = conn.cursor()
        c.execute(
            "DELETE FROM study_activity_logs WHERE id = ? AND user_id = ?",
            (int(entry_id), uid),
        )
        if c.rowcount == 0:
            raise DatabaseError("Activity log entry not found.")


def get_activity_logs_export():
    ensure_logbook_schema()
    uid = get_current_user_id()
    with db_connection(commit=False) as conn:
        return pd.read_sql(
            """SELECT log_date, subject, activity, duration_hours, created_at, updated_at
               FROM study_activity_logs
               WHERE user_id = ?
               ORDER BY log_date, created_at""",
            conn,
            params=(uid,),
        )