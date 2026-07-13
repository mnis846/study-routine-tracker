import contextvars
import sqlite3
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

DB_PATH = str(Path(__file__).resolve().parent / "study_routine_tracker.db")


def get_db_path():
    return DB_PATH
_UNSET = object()
DEFAULT_DAILY_GOAL_HOURS = 6.0
LEGACY_USER_ID = 1

_current_user_id: contextvars.ContextVar[int | None] = contextvars.ContextVar(
    "user_id", default=None
)


class DatabaseError(Exception):
    """Raised when a SQLite operation fails."""


class AuthRequiredError(DatabaseError):
    """Raised when a data operation runs without a logged-in user."""


def set_current_user(user_id: int):
    _current_user_id.set(int(user_id))


def get_current_user_id() -> int:
    uid = _current_user_id.get()
    if uid is None:
        raise AuthRequiredError("No authenticated user in this session.")
    return uid


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 30000")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def _table_has_column(conn, table, column):
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row[1] == column for row in rows)


def _read_setting(conn, key, user_id, default=None):
    row = conn.execute(
        "SELECT value FROM app_settings WHERE user_id = ? AND key = ?",
        (user_id, key),
    ).fetchone()
    return row[0] if row else default


def _write_setting(conn, key, value, user_id):
    conn.execute(
        """INSERT INTO app_settings (user_id, key, value) VALUES (?, ?, ?)
           ON CONFLICT(user_id, key) DO UPDATE SET value = excluded.value""",
        (user_id, key, str(value)),
    )


@contextmanager
def db_connection(*, commit=True):
    conn = get_conn()
    try:
        yield conn
        if commit:
            conn.commit()
    except sqlite3.Error as exc:
        conn.rollback()
        raise DatabaseError(str(exc)) from exc
    finally:
        conn.close()


def _date_str(value):
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _create_users_table(conn):
    conn.execute(
        """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            first_name TEXT DEFAULT '',
            last_name TEXT DEFAULT '',
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""
    )


def _create_multi_user_tables(conn):
    conn.execute(
        """CREATE TABLE IF NOT EXISTS daily_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            plan_date DATE NOT NULL,
            evening_reflection TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, plan_date),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS daily_target_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            planned_hours REAL DEFAULT 0,
            order_index INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Pending',
            actual_hours REAL DEFAULT 0,
            completion_notes TEXT DEFAULT '',
            FOREIGN KEY (plan_id) REFERENCES daily_plans(id) ON DELETE CASCADE
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS daily_study_hours (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            log_date DATE NOT NULL,
            hours REAL NOT NULL DEFAULT 0,
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, log_date),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS scheduled_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            test_no INTEGER NOT NULL,
            level TEXT,
            test_type TEXT,
            subject TEXT,
            scheduled_date DATE,
            topic_focus TEXT,
            status TEXT DEFAULT 'Not Attempted',
            hours_studied REAL DEFAULT 0,
            score REAL,
            max_score REAL,
            remarks TEXT,
            attempt_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, test_no),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS app_settings (
            user_id INTEGER NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            PRIMARY KEY (user_id, key),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS garden_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            event_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            event_type TEXT NOT NULL,
            xp_amount INTEGER NOT NULL,
            message TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )"""
    )
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


def _migrate_legacy_schema(conn):
    if _table_has_column(conn, "daily_plans", "user_id"):
        return

    _create_users_table(conn)
    legacy_user = conn.execute(
        "SELECT id FROM users WHERE id = ?", (LEGACY_USER_ID,)
    ).fetchone()
    if not legacy_user:
        conn.execute(
            """INSERT INTO users
               (id, username, email, first_name, last_name, password_hash)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                LEGACY_USER_ID,
                "legacy",
                "legacy@local",
                "Legacy",
                "User",
                "$2b$12$legacyplaceholderhashnotforloginuse000000000",
            ),
        )

    conn.execute(
        """CREATE TABLE daily_plans_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 1,
            plan_date DATE NOT NULL,
            evening_reflection TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, plan_date)
        )"""
    )
    conn.execute(
        """INSERT INTO daily_plans_new
           (id, user_id, plan_date, evening_reflection, created_at, updated_at)
           SELECT id, ?, plan_date, evening_reflection, created_at, updated_at
           FROM daily_plans""",
        (LEGACY_USER_ID,),
    )
    conn.execute("DROP TABLE daily_plans")
    conn.execute("ALTER TABLE daily_plans_new RENAME TO daily_plans")

    conn.execute(
        """CREATE TABLE daily_study_hours_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 1,
            log_date DATE NOT NULL,
            hours REAL NOT NULL DEFAULT 0,
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, log_date)
        )"""
    )
    conn.execute(
        """INSERT INTO daily_study_hours_new
           (id, user_id, log_date, hours, notes, created_at, updated_at)
           SELECT id, ?, log_date, hours, notes, created_at, updated_at
           FROM daily_study_hours""",
        (LEGACY_USER_ID,),
    )
    conn.execute("DROP TABLE daily_study_hours")
    conn.execute("ALTER TABLE daily_study_hours_new RENAME TO daily_study_hours")

    conn.execute(
        """CREATE TABLE scheduled_tests_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 1,
            test_no INTEGER NOT NULL,
            level TEXT,
            test_type TEXT,
            subject TEXT,
            scheduled_date DATE,
            topic_focus TEXT,
            status TEXT DEFAULT 'Not Attempted',
            hours_studied REAL DEFAULT 0,
            score REAL,
            remarks TEXT,
            attempt_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, test_no)
        )"""
    )
    conn.execute(
        """INSERT INTO scheduled_tests_new
           (id, user_id, test_no, level, test_type, subject, scheduled_date,
            topic_focus, status, hours_studied, score, remarks, attempt_date, created_at)
           SELECT id, ?, test_no, level, test_type, subject, scheduled_date,
                  topic_focus, status, hours_studied, score, remarks, attempt_date, created_at
           FROM scheduled_tests""",
        (LEGACY_USER_ID,),
    )
    conn.execute("DROP TABLE scheduled_tests")
    conn.execute("ALTER TABLE scheduled_tests_new RENAME TO scheduled_tests")

    conn.execute(
        """CREATE TABLE app_settings_new (
            user_id INTEGER NOT NULL DEFAULT 1,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            PRIMARY KEY (user_id, key)
        )"""
    )
    conn.execute(
        """INSERT INTO app_settings_new (user_id, key, value)
           SELECT ?, key, value FROM app_settings""",
        (LEGACY_USER_ID,),
    )
    conn.execute("DROP TABLE app_settings")
    conn.execute("ALTER TABLE app_settings_new RENAME TO app_settings")

    if not _table_has_column(conn, "garden_events", "user_id"):
        conn.execute(
            """CREATE TABLE garden_events_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL DEFAULT 1,
                event_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT NOT NULL,
                xp_amount INTEGER NOT NULL,
                message TEXT NOT NULL
            )"""
        )
        conn.execute(
            """INSERT INTO garden_events_new
               (id, user_id, event_date, event_type, xp_amount, message)
               SELECT id, ?, event_date, event_type, xp_amount, message
               FROM garden_events""",
            (LEGACY_USER_ID,),
        )
        conn.execute("DROP TABLE garden_events")
        conn.execute("ALTER TABLE garden_events_new RENAME TO garden_events")


def init_db():
    with db_connection() as conn:
        _create_users_table(conn)
        if conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='daily_plans'"
        ).fetchone():
            _migrate_legacy_schema(conn)
        else:
            _create_multi_user_tables(conn)
        if conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='scheduled_tests'"
        ).fetchone():
            _ensure_scheduled_tests_max_score(conn)


EXAM_TEST_COUNT = 0
EXAM_TESTS = []
MONSOON_TEST_COUNT = 0
MONSOON_TESTS = []


def _insert_monsoon_tests(conn, user_id):
    rows = [(user_id, *test) for test in EXAM_TESTS]
    conn.executemany(
        """INSERT INTO scheduled_tests
           (user_id, test_no, level, test_type, subject, scheduled_date, topic_focus)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )


def _needs_monsoon_migration(conn, user_id):
    if _read_setting(conn, "exam_series_v1", user_id) == "1":
        return False
    count = conn.execute(
        "SELECT COUNT(*) FROM scheduled_tests WHERE user_id = ?", (user_id,)
    ).fetchone()[0]
    if count == 0:
        return False
    row = conn.execute(
        "SELECT subject FROM scheduled_tests WHERE user_id = ? AND test_no = 1",
        (user_id,),
    ).fetchone()
    if not row:
        return count < EXAM_TEST_COUNT
    return row[0] == "General Studies — History" or count < EXAM_TEST_COUNT


def seed_monsoon_tests_for_user(user_id):
    """No-op: mock schedules are not seeded."""
    return


def seed_sample_tests():
    """No-op: mock schedules are not seeded."""
    return


def provision_new_user(user_id):
    """Initialize per-user defaults after signup."""
    with db_connection() as conn:
        if _read_setting(conn, "daily_study_goal_hours", user_id) is None:
            _write_setting(
                conn, "daily_study_goal_hours", DEFAULT_DAILY_GOAL_HOURS, user_id
            )


def get_user_credentials_dict():
    with db_connection(commit=False) as conn:
        rows = conn.execute(
            """SELECT username, email, first_name, last_name, password_hash
               FROM users ORDER BY username"""
        ).fetchall()
    usernames = {}
    for row in rows:
        usernames[row["username"]] = {
            "email": row["email"],
            "first_name": row["first_name"] or row["username"],
            "last_name": row["last_name"] or "",
            "password": row["password_hash"],
        }
    return {"usernames": usernames}


def get_user_id_by_username(username):
    with db_connection(commit=False) as conn:
        row = conn.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
    if not row:
        raise DatabaseError(f"User '{username}' not found.")
    return int(row[0])


def save_registered_user(username, email, name, credentials):
    """Persist a newly registered user from streamlit-authenticator."""
    entry = credentials["usernames"].get(username)
    if not entry:
        raise DatabaseError("Registration data missing for new user.")
    parts = (name or username).split(maxsplit=1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else ""
    with db_connection() as conn:
        conn.execute(
            """INSERT INTO users (username, email, first_name, last_name, password_hash)
               VALUES (?, ?, ?, ?, ?)""",
            (username, email, first_name, last_name, entry["password"]),
        )
        user_id = conn.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()[0]
    provision_new_user(int(user_id))


def get_setting(key, default=None, user_id=None):
    uid = user_id if user_id is not None else get_current_user_id()
    with db_connection(commit=False) as conn:
        return _read_setting(conn, key, uid, default)


def set_setting(key, value, user_id=None):
    uid = user_id if user_id is not None else get_current_user_id()
    with db_connection() as conn:
        _write_setting(conn, key, uid, value)


def get_daily_study_goal():
    raw = get_setting("daily_study_goal_hours", str(DEFAULT_DAILY_GOAL_HOURS))
    try:
        return max(0.5, float(raw))
    except (TypeError, ValueError):
        return DEFAULT_DAILY_GOAL_HOURS


def set_daily_study_goal(hours):
    set_setting("daily_study_goal_hours", max(0.5, float(hours)))


def add_daily_study_hours(log_date, hours, notes=""):
    uid = get_current_user_id()
    date_str = _date_str(log_date)
    with db_connection() as conn:
        row = conn.execute(
            """SELECT id, hours, notes FROM daily_study_hours
               WHERE user_id = ? AND log_date = ?""",
            (uid, date_str),
        ).fetchone()
        if row:
            new_hours = float(row["hours"]) + float(hours)
            old_notes = (row["notes"] or "").strip()
            new_note = (notes or "").strip()
            if new_note and old_notes:
                merged_notes = f"{old_notes}; {new_note}"
            elif new_note:
                merged_notes = new_note
            else:
                merged_notes = old_notes
            conn.execute(
                """UPDATE daily_study_hours
                   SET hours = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (new_hours, merged_notes, row["id"]),
            )
        else:
            conn.execute(
                """INSERT INTO daily_study_hours (user_id, log_date, hours, notes)
                   VALUES (?, ?, ?, ?)""",
                (uid, date_str, float(hours), notes or ""),
            )


def get_study_hours_for_date(log_date):
    uid = get_current_user_id()
    date_str = _date_str(log_date)
    with db_connection(commit=False) as conn:
        row = conn.execute(
            "SELECT hours FROM daily_study_hours WHERE user_id = ? AND log_date = ?",
            (uid, date_str),
        ).fetchone()
    return float(row["hours"]) if row else 0.0


def get_week_study_hours(anchor_date=None):
    uid = get_current_user_id()
    if anchor_date is None:
        anchor_date = date.today()
    monday = anchor_date - timedelta(days=anchor_date.weekday())
    week_dates = [monday + timedelta(days=i) for i in range(7)]
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    with db_connection(commit=False) as conn:
        rows = []
        for d, name in zip(week_dates, day_names):
            date_str = d.isoformat()
            row = conn.execute(
                """SELECT hours, notes FROM daily_study_hours
                   WHERE user_id = ? AND log_date = ?""",
                (uid, date_str),
            ).fetchone()
            rows.append(
                {
                    "day": name,
                    "log_date": d,
                    "hours": float(row["hours"]) if row else 0.0,
                    "notes": row["notes"] if row else "",
                    "is_today": d == date.today(),
                }
            )
    return pd.DataFrame(rows)


def get_recent_study_hours(limit=14):
    uid = get_current_user_id()
    with db_connection(commit=False) as conn:
        return pd.read_sql(
            """SELECT log_date, hours, notes, updated_at
               FROM daily_study_hours
               WHERE user_id = ?
               ORDER BY log_date DESC
               LIMIT ?""",
            conn,
            params=(uid, limit),
        )


def get_study_streak():
    uid = get_current_user_id()
    today = date.today()
    with db_connection(commit=False) as conn:
        df = pd.read_sql(
            """SELECT log_date, hours FROM daily_study_hours
               WHERE user_id = ? ORDER BY log_date DESC""",
            conn,
            params=(uid,),
        )
    if df.empty:
        return 0

    hours_by_date = {
        pd.to_datetime(row["log_date"]).date(): float(row["hours"])
        for _, row in df.iterrows()
    }
    streak = 0
    cursor = today
    while hours_by_date.get(cursor, 0) > 0:
        streak += 1
        cursor -= timedelta(days=1)
    return streak



def _parse_log_date(value):
    if isinstance(value, date):
        return value
    if hasattr(value, "date"):
        try:
            return value.date()
        except TypeError:
            pass
    return date.fromisoformat(str(value)[:10])


def default_max_score(test_type):
    """Default total marks: full-length papers 200, sectionals 100."""
    kind = (test_type or "").strip().upper()
    if kind == "FLT":
        return 200.0
    return 100.0


def score_percentage(score, max_score):
    """Return marks as a 0-100 percentage, or None if either value is missing/invalid."""
    if score is None or max_score is None:
        return None
    try:
        if pd.isna(score) or pd.isna(max_score):
            return None
        max_val = float(max_score)
        if max_val <= 0:
            return None
        return round(float(score) / max_val * 100, 1)
    except (TypeError, ValueError):
        return None


def _ensure_scheduled_tests_max_score(conn):
    """Add max_score column on existing DBs and backfill defaults by test type."""
    if not _table_has_column(conn, "scheduled_tests", "max_score"):
        conn.execute("ALTER TABLE scheduled_tests ADD COLUMN max_score REAL")
    conn.execute(
        """UPDATE scheduled_tests
           SET max_score = CASE
               WHEN UPPER(COALESCE(test_type, '')) = 'FLT' THEN 200
               ELSE 100
           END
           WHERE max_score IS NULL OR max_score <= 0"""
    )


def get_study_hours_map(start_date, end_date=None):
    """Return {date: hours} for each day in the inclusive range (current user)."""
    if end_date is None:
        end_date = date.today()
    uid = get_current_user_id()
    start_str = _date_str(start_date)
    end_str = _date_str(end_date)
    with db_connection(commit=False) as conn:
        df = pd.read_sql(
            """SELECT log_date, hours FROM daily_study_hours
               WHERE user_id = ? AND log_date >= ? AND log_date <= ?""",
            conn,
            params=(uid, start_str, end_str),
        )
    result = {}
    for _, row in df.iterrows():
        result[_parse_log_date(row["log_date"])] = float(row["hours"])
    return result


def add_daily_target(plan_date, description, planned_hours=0):
    """Append a single target to an existing or new daily plan."""
    desc = (description or "").strip()
    if not desc:
        raise DatabaseError("Target description cannot be empty.")
    uid = get_current_user_id()
    with db_connection() as conn:
        c = conn.cursor()
        plan_id = _get_or_create_plan_id(plan_date, conn, uid)
        c.execute(
            "SELECT COALESCE(MAX(order_index), -1) FROM daily_target_items WHERE plan_id = ?",
            (plan_id,),
        )
        next_index = int(c.fetchone()[0]) + 1
        c.execute(
            """INSERT INTO daily_target_items
               (plan_id, description, planned_hours, order_index, status)
               VALUES (?, ?, ?, ?, 'Pending')""",
            (plan_id, desc, float(planned_hours or 0), next_index),
        )


def get_longest_streak():
    uid = get_current_user_id()
    with db_connection(commit=False) as conn:
        df = pd.read_sql(
            """SELECT log_date, hours FROM daily_study_hours
               WHERE user_id = ? ORDER BY log_date ASC""",
            conn,
            params=(uid,),
        )
    if df.empty:
        return 0

    study_dates = sorted(
        pd.to_datetime(row["log_date"]).date()
        for _, row in df.iterrows()
        if float(row["hours"]) > 0
    )
    if not study_dates:
        return 0

    longest = 1
    run = 1
    for i in range(1, len(study_dates)):
        if study_dates[i] - study_dates[i - 1] == timedelta(days=1):
            run += 1
            longest = max(longest, run)
        else:
            run = 1
    return longest


def get_export_dataframes():
    uid = get_current_user_id()
    with db_connection(commit=False) as conn:
        hours = pd.read_sql(
            """SELECT log_date, hours, notes, updated_at
               FROM daily_study_hours WHERE user_id = ? ORDER BY log_date""",
            conn,
            params=(uid,),
        )
        tests = pd.read_sql(
            "SELECT * FROM scheduled_tests WHERE user_id = ? ORDER BY test_no",
            conn,
            params=(uid,),
        )
        targets = pd.read_sql(
            """SELECT p.plan_date, t.description, t.status, t.planned_hours, t.actual_hours
               FROM daily_target_items t
               JOIN daily_plans p ON p.id = t.plan_id
               WHERE p.user_id = ?
               ORDER BY p.plan_date, t.order_index""",
            conn,
            params=(uid,),
        )
    from logbook import get_activity_logs_export

    activity_logs = get_activity_logs_export()
    return {
        "study_hours": hours,
        "scheduled_tests": tests,
        "daily_targets": targets,
        "activity_logs": activity_logs,
    }


def _get_or_create_plan_id(plan_date, conn, user_id):
    date_str = _date_str(plan_date)
    row = conn.execute(
        "SELECT id FROM daily_plans WHERE user_id = ? AND plan_date = ?",
        (user_id, date_str),
    ).fetchone()
    if row:
        return row["id"]
    conn.execute(
        "INSERT INTO daily_plans (user_id, plan_date) VALUES (?, ?)",
        (user_id, date_str),
    )
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def get_daily_plan(plan_date):
    uid = get_current_user_id()
    date_str = _date_str(plan_date)
    with db_connection(commit=False) as conn:
        plan_df = pd.read_sql(
            "SELECT * FROM daily_plans WHERE user_id = ? AND plan_date = ?",
            conn,
            params=(uid, date_str),
        )
        if plan_df.empty:
            return None
        plan = plan_df.iloc[0].to_dict()
        items_df = pd.read_sql(
            """SELECT * FROM daily_target_items
               WHERE plan_id = ?
               ORDER BY order_index, id""",
            conn,
            params=(int(plan["id"]),),
        )
    plan["items"] = items_df.to_dict("records") if not items_df.empty else []
    return plan


def save_daily_targets(plan_date, targets, evening_reflection=None):
    uid = get_current_user_id()
    with db_connection() as conn:
        plan_id = _get_or_create_plan_id(plan_date, conn, uid)
        existing = conn.execute(
            """SELECT order_index, status, actual_hours, completion_notes
               FROM daily_target_items
               WHERE plan_id = ?
               ORDER BY order_index, id""",
            (plan_id,),
        ).fetchall()
        existing_by_index = {
            row["order_index"]: {
                "status": row["status"],
                "actual_hours": row["actual_hours"],
                "completion_notes": row["completion_notes"],
            }
            for row in existing
        }

        conn.execute("DELETE FROM daily_target_items WHERE plan_id = ?", (plan_id,))
        for idx, target in enumerate(targets):
            desc = (target.get("description") or "").strip()
            if not desc:
                continue
            prev = existing_by_index.get(idx, {})
            conn.execute(
                """INSERT INTO daily_target_items
                   (plan_id, description, planned_hours, order_index, status,
                    actual_hours, completion_notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    plan_id,
                    desc,
                    float(target.get("planned_hours") or 0),
                    idx,
                    prev.get("status", "Pending"),
                    float(prev.get("actual_hours") or 0),
                    prev.get("completion_notes") or "",
                ),
            )

        if evening_reflection is not None:
            conn.execute(
                """UPDATE daily_plans
                   SET evening_reflection = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ? AND user_id = ?""",
                (evening_reflection, plan_id, uid),
            )
        else:
            conn.execute(
                """UPDATE daily_plans SET updated_at = CURRENT_TIMESTAMP
                   WHERE id = ? AND user_id = ?""",
                (plan_id, uid),
            )


def update_target_status(item_id, status):
    uid = get_current_user_id()
    with db_connection() as conn:
        conn.execute(
            """UPDATE daily_target_items SET status = ?
               WHERE id = ? AND plan_id IN (
                   SELECT id FROM daily_plans WHERE user_id = ?
               )""",
            (status, int(item_id), uid),
        )


def save_evening_reflection(plan_date, reflection):
    uid = get_current_user_id()
    with db_connection() as conn:
        plan_id = _get_or_create_plan_id(plan_date, conn, uid)
        conn.execute(
            """UPDATE daily_plans
               SET evening_reflection = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ? AND user_id = ?""",
            (reflection or "", plan_id, uid),
        )


def get_daily_plan_summary(plan_date):
    plan = get_daily_plan(plan_date)
    if not plan or not plan["items"]:
        return {
            "has_plan": False,
            "total_targets": 0,
            "done": 0,
            "partial": 0,
            "pending": 0,
            "skipped": 0,
            "planned_hours": 0,
            "actual_hours": 0,
            "completion_pct": 0,
            "resolved_pct": 0,
        }
    items = plan["items"]
    done = sum(1 for i in items if i["status"] == "Done")
    partial = sum(1 for i in items if i["status"] == "Partial")
    pending = sum(1 for i in items if i["status"] == "Pending")
    skipped = sum(1 for i in items if i["status"] == "Skipped")
    planned = sum(float(i.get("planned_hours") or 0) for i in items)
    actual = sum(float(i.get("actual_hours") or 0) for i in items)
    total = len(items)
    resolved = done + skipped
    return {
        "has_plan": True,
        "total_targets": total,
        "done": done,
        "partial": partial,
        "pending": pending,
        "skipped": skipped,
        "planned_hours": round(planned, 1),
        "actual_hours": round(actual, 1),
        "completion_pct": round((done / total) * 100) if total else 0,
        "resolved_pct": round((resolved / total) * 100) if total else 0,
    }


def get_scheduled_tests():
    uid = get_current_user_id()
    with db_connection(commit=False) as conn:
        return pd.read_sql(
            "SELECT * FROM scheduled_tests WHERE user_id = ? ORDER BY test_no",
            conn,
            params=(uid,),
        )


def get_next_scheduled_test():
    uid = get_current_user_id()
    today_str = date.today().isoformat()
    with db_connection(commit=False) as conn:
        df = pd.read_sql(
            """SELECT * FROM scheduled_tests
               WHERE user_id = ?
                 AND (status != 'Attempted' OR status IS NULL)
                 AND scheduled_date >= ?
               ORDER BY scheduled_date ASC
               LIMIT 1""",
            conn,
            params=(uid, today_str),
        )
        if df.empty:
            df = pd.read_sql(
                """SELECT * FROM scheduled_tests
                   WHERE user_id = ?
                     AND (status != 'Attempted' OR status IS NULL)
                   ORDER BY scheduled_date ASC
                   LIMIT 1""",
                conn,
                params=(uid,),
            )
    if df.empty:
        return None
    return df.iloc[0].to_dict()


def get_test_series_progress():
    df = get_scheduled_tests()
    attempted = df[df["status"] == "Attempted"]
    scores = attempted["score"].dropna()
    total_hours = round(float(df["hours_studied"].fillna(0).sum()), 1)
    return {
        "total": len(df),
        "attempted": len(attempted),
        "avg_score": round(scores.mean(), 1) if not scores.empty else None,
        "total_hours": total_hours,
        "scores": attempted[["test_no", "subject", "scheduled_date", "score"]].copy(),
    }


def get_garden_xp():
    raw = get_setting("garden_xp", "0")
    try:
        return max(0, int(raw))
    except (TypeError, ValueError):
        return 0


def _set_garden_xp(xp):
    set_setting("garden_xp", max(0, int(xp)))


def _log_garden_event(event_type, xp_amount, message):
    uid = get_current_user_id()
    with db_connection() as conn:
        conn.execute(
            """INSERT INTO garden_events (user_id, event_type, xp_amount, message)
               VALUES (?, ?, ?, ?)""",
            (uid, event_type, int(xp_amount), message),
        )


def add_garden_xp(amount, event_type, message):
    if amount <= 0:
        return 0
    new_xp = get_garden_xp() + amount
    _set_garden_xp(new_xp)
    _log_garden_event(event_type, amount, message)
    return amount


def get_garden_events(limit=12):
    uid = get_current_user_id()
    with db_connection(commit=False) as conn:
        return pd.read_sql(
            """SELECT event_date, event_type, xp_amount, message
               FROM garden_events
               WHERE user_id = ?
               ORDER BY id DESC
               LIMIT ?""",
            conn,
            params=(uid, limit),
        )


def _bonus_already_today(setting_key):
    return get_setting(setting_key) == date.today().isoformat()


def _mark_bonus_today(setting_key):
    set_setting(setting_key, date.today().isoformat())


def process_daily_checkin(streak=0):
    """Award daily open-app XP once per day. Returns list of reward dicts."""
    rewards = []
    if _bonus_already_today("last_garden_checkin"):
        return rewards

    from garden import XP_REWARDS

    xp = add_garden_xp(
        XP_REWARDS["daily_checkin"],
        "checkin",
        "Daily check-in — you showed up!",
    )
    rewards.append({"xp": xp, "message": "Daily check-in — you showed up! 🌱"})

    streak_bonus = min(streak * XP_REWARDS["streak_per_day"], XP_REWARDS["streak_cap"])
    if streak_bonus > 0:
        xp = add_garden_xp(
            streak_bonus,
            "streak",
            f"{streak}-day study streak bonus",
        )
        rewards.append({"xp": xp, "message": f"{streak}-day streak bonus 🔥"})

    _mark_bonus_today("last_garden_checkin")
    return rewards


def award_hours_garden_xp(hours):
    from garden import XP_REWARDS

    amount = int(float(hours) * XP_REWARDS["per_hour"])
    if amount <= 0:
        return None
    xp = add_garden_xp(amount, "hours", f"Logged {hours}h of study")
    return {"xp": xp, "message": f"Logged {hours}h of study 💪"}


def award_target_done_xp():
    from garden import XP_REWARDS

    xp = add_garden_xp(XP_REWARDS["target_done"], "target", "Target completed!")
    return {"xp": xp, "message": "Target crushed ✅"}


def sync_daily_garden_bonuses(today=None):
    """Award once-per-day bonuses for all-targets and daily-goal milestones."""
    if today is None:
        today = date.today()

    from garden import XP_REWARDS

    rewards = []
    summary = get_daily_plan_summary(today)
    items = summary.get("total_targets", 0)
    done = summary.get("done", 0)
    skipped = summary.get("skipped", 0)

    if items > 0 and (done + skipped) >= items:
        if not _bonus_already_today("last_garden_all_targets"):
            xp = add_garden_xp(
                XP_REWARDS["all_targets"],
                "all_targets",
                "All targets resolved today!",
            )
            rewards.append({"xp": xp, "message": "All targets done today! 🎉"})
            _mark_bonus_today("last_garden_all_targets")

    hours = get_study_hours_for_date(today)
    goal = get_daily_study_goal()
    if hours >= goal:
        if not _bonus_already_today("last_garden_daily_goal"):
            xp = add_garden_xp(
                XP_REWARDS["daily_goal"],
                "daily_goal",
                f"Hit your {goal:g}h daily goal!",
            )
            rewards.append({"xp": xp, "message": f"Daily goal hit ({goal:g}h)! 🎯"})
            _mark_bonus_today("last_garden_daily_goal")

    return rewards


def get_garden_state(streak=0, today=None):
    from garden import get_stage_info
    from garden_life import sync_garden_life

    if today is None:
        today = date.today()
    xp = get_garden_xp()
    life = sync_garden_life(today)
    return {
        "xp": xp,
        "streak": streak,
        "stage_info": get_stage_info(xp),
        "events": get_garden_events(8),
        "life": life,
        "vitality": life,
    }


def update_scheduled_test(
    test_no,
    status=None,
    hours_studied=_UNSET,
    score=_UNSET,
    max_score=_UNSET,
    remarks=_UNSET,
):
    uid = get_current_user_id()
    updates = []
    params = []
    if status:
        updates.append("status = ?")
        params.append(status)
    if hours_studied is not _UNSET:
        updates.append("hours_studied = ?")
        params.append(hours_studied)
    if score is not _UNSET:
        updates.append("score = ?")
        params.append(score)
    if max_score is not _UNSET:
        updates.append("max_score = ?")
        params.append(max_score)
    if remarks is not _UNSET:
        updates.append("remarks = ?")
        params.append(remarks)
    if not updates:
        return

    params.extend([test_no, uid])
    with db_connection() as conn:
        conn.execute(
            f"""UPDATE scheduled_tests SET {', '.join(updates)}
                WHERE test_no = ? AND user_id = ?""",
            params,
        )