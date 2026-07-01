import sqlite3
from contextlib import contextmanager
from datetime import date, timedelta

import pandas as pd

DB_PATH = "study_routine_tracker.db"
_UNSET = object()
DEFAULT_DAILY_GOAL_HOURS = 6.0


class DatabaseError(Exception):
    """Raised when a SQLite operation fails."""


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


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


def init_db():
    with db_connection() as conn:
        c = conn.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS daily_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_date DATE UNIQUE NOT NULL,
                evening_reflection TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        c.execute(
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
        c.execute(
            """CREATE TABLE IF NOT EXISTS daily_study_hours (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_date DATE UNIQUE NOT NULL,
                hours REAL NOT NULL DEFAULT 0,
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS scheduled_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_no INTEGER UNIQUE,
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS garden_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT NOT NULL,
                xp_amount INTEGER NOT NULL,
                message TEXT NOT NULL
            )"""
        )


MONSOON_TEST_COUNT = 32

MONSOON_TESTS = [
    (1, "Level-1", "Sectional", "Welfare policy & Act", "2026-06-29", "Paper-7/Part-I"),
    (2, "Level-1", "Sectional", "Organizations & sports", "2026-07-03", "Paper-7/Part-II"),
    (3, "Level-1", "Sectional", "Education & HRD", "2026-07-09", "Paper-7/Part-III"),
    (4, "Level-1", "FLT", "Paper-7 Complete", "2026-07-13", "Full Length Test"),
    (5, "Level-1", "Sectional", "Philosophy", "2026-07-18", "Paper-6/Part-I"),
    (6, "Level-1", "Sectional", "Sociology", "2026-07-21", "Paper-6/Part-II"),
    (7, "Level-1", "Sectional", "Social Aspect of C.G.", "2026-07-25", "Paper-6/Part-III"),
    (8, "Level-1", "FLT", "Paper-6 Complete", "2026-07-31", "Full Length Test"),
    (9, "Level-1", "Sectional", "Indian & C.G. Economy", "2026-08-04", "Paper-5/Part-I"),
    (10, "Level-1", "Sectional", "Indian Geography", "2026-08-07", "Paper-5/Part-II"),
    (11, "Level-1", "Sectional", "CG Geography", "2026-08-11", "Paper-5/Part-III"),
    (12, "Level-1", "FLT", "Paper-5 Complete", "2026-08-17", "Full Length Test"),
    (13, "Level-1", "Sectional", "General Science", "2026-08-21", "Paper-4/Part-I"),
    (14, "Level-1", "Sectional", "Maths & Reasoning", "2026-08-24", "Paper-4/Part-II"),
    (15, "Level-1", "Sectional", "Applied Science", "2026-09-01", "Paper-4/Part-III"),
    (16, "Level-1", "FLT", "Paper-4 Complete", "2026-09-06", "Full Length Test"),
    (17, "Level-1", "Sectional", "Hindi Language", "2026-09-09", "Paper-1/Part-I"),
    (18, "Level-1", "Sectional", "English Language", "2026-09-12", "Paper-1/Part-II"),
    (19, "Level-1", "Sectional", "Chhattisgarhi Language", "2026-09-15", "Paper-1/Part-III"),
    (20, "Level-1", "FLT", "Paper-1 Complete", "2026-09-21", "Full Length Test"),
    (21, "Level-1", "Sectional", "Indian History", "2026-09-25", "Paper-3/Part-I"),
    (22, "Level-1", "Sectional", "Constitution & Pub Admin", "2026-09-28", "Paper-3/Part-II"),
    (23, "Level-1", "Sectional", "CG History", "2026-10-02", "Paper-3/Part-III"),
    (24, "Level-1", "FLT", "Paper-3 Complete", "2026-10-08", "Full Length Test"),
    (25, "Level-1", "FLT", "Paper-2 Complete", "2026-10-15", "Full Length Test"),
    (26, "Level-2", "FLT", "Paper-01 Complete Syllabus", "2026-10-26", "FLT-08"),
    (27, "Level-2", "FLT", "Paper-02 Complete Syllabus", "2026-10-26", "FLT-09"),
    (28, "Level-2", "FLT", "Paper-03 Complete Syllabus", "2026-10-27", "FLT-10"),
    (29, "Level-2", "FLT", "Paper-04 Complete Syllabus", "2026-10-27", "FLT-11"),
    (30, "Level-2", "FLT", "Paper-05 Complete Syllabus", "2026-10-28", "FLT-12"),
    (31, "Level-2", "FLT", "Paper-06 Complete Syllabus", "2026-10-28", "FLT-13"),
    (32, "Level-2", "FLT", "Paper-07 Complete Syllabus", "2026-10-29", "FLT-14"),
]


def _insert_monsoon_tests(conn):
    conn.cursor().executemany(
        """INSERT INTO scheduled_tests
           (test_no, level, test_type, subject, scheduled_date, topic_focus)
           VALUES (?, ?, ?, ?, ?, ?)""",
        MONSOON_TESTS,
    )


def _needs_monsoon_migration(conn):
    if get_setting("monsoon_series_v1") == "1":
        return False
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM scheduled_tests")
    count = c.fetchone()[0]
    if count == 0:
        return False
    c.execute("SELECT subject FROM scheduled_tests WHERE test_no = 1")
    row = c.fetchone()
    if not row:
        return count < MONSOON_TEST_COUNT
    return row[0] == "General Studies — History" or count < MONSOON_TEST_COUNT


def seed_monsoon_tests():
    """Seed Delhi IAS Monsoon Mains Test Series 2026 (32 tests)."""
    with db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM scheduled_tests")
        if c.fetchone()[0] > 0:
            if _needs_monsoon_migration(conn):
                c.execute("DELETE FROM scheduled_tests")
                _insert_monsoon_tests(conn)
                set_setting("monsoon_series_v1", "1")
            return
        _insert_monsoon_tests(conn)
        set_setting("monsoon_series_v1", "1")


def seed_sample_tests():
    """Backward-compatible alias for Monsoon test series seeding."""
    seed_monsoon_tests()


def get_setting(key, default=None):
    with db_connection(commit=False) as conn:
        c = conn.cursor()
        c.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
        row = c.fetchone()
    return row[0] if row else default


def set_setting(key, value):
    with db_connection() as conn:
        c = conn.cursor()
        c.execute(
            """INSERT INTO app_settings (key, value) VALUES (?, ?)
               ON CONFLICT(key) DO UPDATE SET value = excluded.value""",
            (key, str(value)),
        )


def get_daily_study_goal():
    raw = get_setting("daily_study_goal_hours", str(DEFAULT_DAILY_GOAL_HOURS))
    try:
        return max(0.5, float(raw))
    except (TypeError, ValueError):
        return DEFAULT_DAILY_GOAL_HOURS


def set_daily_study_goal(hours):
    set_setting("daily_study_goal_hours", max(0.5, float(hours)))


def add_daily_study_hours(log_date, hours, notes=""):
    date_str = _date_str(log_date)
    with db_connection() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT id, hours, notes FROM daily_study_hours WHERE log_date = ?",
            (date_str,),
        )
        row = c.fetchone()
        if row:
            new_hours = float(row[1]) + float(hours)
            old_notes = (row[2] or "").strip()
            new_note = (notes or "").strip()
            if new_note and old_notes:
                merged_notes = f"{old_notes}; {new_note}"
            elif new_note:
                merged_notes = new_note
            else:
                merged_notes = old_notes
            c.execute(
                """UPDATE daily_study_hours
                   SET hours = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (new_hours, merged_notes, row[0]),
            )
        else:
            c.execute(
                "INSERT INTO daily_study_hours (log_date, hours, notes) VALUES (?, ?, ?)",
                (date_str, float(hours), notes or ""),
            )


def get_study_hours_for_date(log_date):
    date_str = _date_str(log_date)
    with db_connection(commit=False) as conn:
        c = conn.cursor()
        c.execute("SELECT hours FROM daily_study_hours WHERE log_date = ?", (date_str,))
        row = c.fetchone()
    return float(row[0]) if row else 0.0


def get_week_study_hours(anchor_date=None):
    if anchor_date is None:
        anchor_date = date.today()
    monday = anchor_date - timedelta(days=anchor_date.weekday())
    week_dates = [monday + timedelta(days=i) for i in range(7)]
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    with db_connection(commit=False) as conn:
        rows = []
        for d, name in zip(week_dates, day_names):
            date_str = d.isoformat()
            c = conn.cursor()
            c.execute(
                "SELECT hours, notes FROM daily_study_hours WHERE log_date = ?",
                (date_str,),
            )
            row = c.fetchone()
            rows.append(
                {
                    "day": name,
                    "log_date": d,
                    "hours": float(row[0]) if row else 0.0,
                    "notes": row[1] if row else "",
                    "is_today": d == date.today(),
                }
            )
    return pd.DataFrame(rows)


def get_recent_study_hours(limit=14):
    with db_connection(commit=False) as conn:
        return pd.read_sql(
            """SELECT log_date, hours, notes, updated_at
               FROM daily_study_hours
               ORDER BY log_date DESC
               LIMIT ?""",
            conn,
            params=(limit,),
        )


def get_study_streak():
    today = date.today()
    with db_connection(commit=False) as conn:
        df = pd.read_sql(
            "SELECT log_date, hours FROM daily_study_hours ORDER BY log_date DESC",
            conn,
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


def get_longest_streak():
    with db_connection(commit=False) as conn:
        df = pd.read_sql(
            "SELECT log_date, hours FROM daily_study_hours ORDER BY log_date ASC",
            conn,
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
    with db_connection(commit=False) as conn:
        hours = pd.read_sql(
            "SELECT log_date, hours, notes, updated_at FROM daily_study_hours ORDER BY log_date",
            conn,
        )
        tests = pd.read_sql("SELECT * FROM scheduled_tests ORDER BY test_no", conn)
        targets = pd.read_sql(
            """SELECT p.plan_date, t.description, t.status, t.planned_hours, t.actual_hours
               FROM daily_target_items t
               JOIN daily_plans p ON p.id = t.plan_id
               ORDER BY p.plan_date, t.order_index""",
            conn,
        )
    return {"study_hours": hours, "scheduled_tests": tests, "daily_targets": targets}


def _get_or_create_plan_id(plan_date, conn):
    c = conn.cursor()
    date_str = _date_str(plan_date)
    c.execute("SELECT id FROM daily_plans WHERE plan_date = ?", (date_str,))
    row = c.fetchone()
    if row:
        return row[0]
    c.execute("INSERT INTO daily_plans (plan_date) VALUES (?)", (date_str,))
    return c.lastrowid


def get_daily_plan(plan_date):
    date_str = _date_str(plan_date)
    with db_connection(commit=False) as conn:
        plan_df = pd.read_sql(
            "SELECT * FROM daily_plans WHERE plan_date = ?",
            conn,
            params=(date_str,),
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
    with db_connection() as conn:
        c = conn.cursor()
        plan_id = _get_or_create_plan_id(plan_date, conn)

        c.execute(
            """SELECT order_index, status, actual_hours, completion_notes
               FROM daily_target_items
               WHERE plan_id = ?
               ORDER BY order_index, id""",
            (plan_id,),
        )
        existing_by_index = {
            row[0]: {
                "status": row[1],
                "actual_hours": row[2],
                "completion_notes": row[3],
            }
            for row in c.fetchall()
        }

        c.execute("DELETE FROM daily_target_items WHERE plan_id = ?", (plan_id,))
        for idx, target in enumerate(targets):
            desc = (target.get("description") or "").strip()
            if not desc:
                continue
            prev = existing_by_index.get(idx, {})
            c.execute(
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
            c.execute(
                """UPDATE daily_plans
                   SET evening_reflection = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (evening_reflection, plan_id),
            )
        else:
            c.execute(
                "UPDATE daily_plans SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (plan_id,),
            )


def update_target_status(item_id, status):
    with db_connection() as conn:
        c = conn.cursor()
        c.execute(
            "UPDATE daily_target_items SET status = ? WHERE id = ?",
            (status, int(item_id)),
        )


def save_evening_reflection(plan_date, reflection):
    with db_connection() as conn:
        c = conn.cursor()
        plan_id = _get_or_create_plan_id(plan_date, conn)
        c.execute(
            """UPDATE daily_plans
               SET evening_reflection = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (reflection or "", plan_id),
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
    with db_connection(commit=False) as conn:
        return pd.read_sql("SELECT * FROM scheduled_tests ORDER BY test_no", conn)


def get_next_scheduled_test():
    today_str = date.today().isoformat()
    with db_connection(commit=False) as conn:
        df = pd.read_sql(
            """SELECT * FROM scheduled_tests
               WHERE (status != 'Attempted' OR status IS NULL)
                 AND scheduled_date >= ?
               ORDER BY scheduled_date ASC
               LIMIT 1""",
            conn,
            params=(today_str,),
        )
        if df.empty:
            df = pd.read_sql(
                """SELECT * FROM scheduled_tests
                   WHERE status != 'Attempted' OR status IS NULL
                   ORDER BY scheduled_date ASC
                   LIMIT 1""",
                conn,
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
    with db_connection() as conn:
        c = conn.cursor()
        c.execute(
            """INSERT INTO garden_events (event_type, xp_amount, message)
               VALUES (?, ?, ?)""",
            (event_type, int(xp_amount), message),
        )


def add_garden_xp(amount, event_type, message):
    if amount <= 0:
        return 0
    old_xp = get_garden_xp()
    new_xp = old_xp + amount
    _set_garden_xp(new_xp)
    _log_garden_event(event_type, amount, message)
    return amount


def get_garden_events(limit=12):
    with db_connection(commit=False) as conn:
        return pd.read_sql(
            """SELECT event_date, event_type, xp_amount, message
               FROM garden_events
               ORDER BY id DESC
               LIMIT ?""",
            conn,
            params=(limit,),
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


def get_garden_state(streak=0):
    from garden import get_stage_info

    xp = get_garden_xp()
    return {
        "xp": xp,
        "streak": streak,
        "stage_info": get_stage_info(xp),
        "events": get_garden_events(8),
    }


def update_scheduled_test(
    test_no, status=None, hours_studied=_UNSET, score=_UNSET, remarks=_UNSET
):
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
    if remarks is not _UNSET:
        updates.append("remarks = ?")
        params.append(remarks)
    if not updates:
        return

    params.append(test_no)
    with db_connection() as conn:
        c = conn.cursor()
        c.execute(
            f"UPDATE scheduled_tests SET {', '.join(updates)} WHERE test_no = ?",
            params,
        )