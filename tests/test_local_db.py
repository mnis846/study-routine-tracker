"""Smoke-test local SQLite persistence. Run: python -m tests.test_local_db"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="tracker_db_test_"))
    os.environ["TRACKER_DATA_DIR"] = str(tmp)
    # Fresh import after env so path resolution is clean
    import importlib

    import tracker.database as db

    importlib.reload(db)
    import tracker.paths as paths

    importlib.reload(paths)
    importlib.reload(db)

    print("DATA_DIR:", db.resolve_data_dir())
    print("DB_PATH:", db.get_db_path())

    db.init_db()
    uid = db.get_current_user_id()
    print("user_id:", uid)

    today = date.today()
    yesterday = today - timedelta(days=1)

    db.set_local_display_name("Test Aspirant")
    assert db.get_local_display_name() == "Test Aspirant"
    db.set_daily_study_goal(7.5)
    assert db.get_daily_study_goal() == 7.5

    db.save_daily_targets(
        today,
        [
            {"description": "Polity — Fundamental Rights notes", "planned_hours": 2},
            {"description": "Essay practice 1 page", "planned_hours": 1},
        ],
    )
    plan = db.get_daily_plan(today)
    assert plan is not None, "plan missing after save"
    assert len(plan["items"]) == 2, plan["items"]
    item_id = int(plan["items"][0]["id"])
    db.update_target_status(item_id, "Done")
    plan2 = db.get_daily_plan(today)
    assert plan2["items"][0]["status"] == "Done"
    db.save_evening_reflection(today, "Solid focus after lunch.")
    plan3 = db.get_daily_plan(today)
    assert "Solid focus" in (plan3.get("evening_reflection") or "")

    db.add_daily_study_hours(today, 2.0, "morning")
    db.add_daily_study_hours(today, 1.5, "evening")
    assert abs(db.get_study_hours_for_date(today) - 3.5) < 1e-9
    db.add_daily_study_hours(yesterday, 4.0, "full day")
    assert abs(db.get_study_hours_for_date(yesterday) - 4.0) < 1e-9
    streak = db.get_study_streak()
    assert streak >= 2, f"expected streak>=2 got {streak}"

    from tracker.logbook import add_activity_log, delete_activity_log, get_activity_logs

    eid = add_activity_log(
        today, "Revised constitution articles", subject="GS II", duration_hours=1.0
    )
    logs = get_activity_logs(log_date=today)
    assert not logs.empty
    assert int(logs.iloc[0]["id"]) == eid
    delete_activity_log(eid)
    logs2 = get_activity_logs(log_date=today)
    assert logs2.empty

    path = Path(db.get_db_path())
    assert path.exists() and path.stat().st_size > 0

    with db.db_connection() as conn:
        try:
            conn.execute("PRAGMA wal_checkpoint(FULL)")
        except Exception as exc:
            print("checkpoint note:", exc)

    db._current_user_id.set(None)
    db.init_db()
    assert db.get_local_display_name() == "Test Aspirant"
    assert abs(db.get_study_hours_for_date(today) - 3.5) < 1e-9
    plan_again = db.get_daily_plan(today)
    assert plan_again and len(plan_again["items"]) == 2

    with db.db_connection(commit=False) as conn:
        ok = conn.execute("PRAGMA integrity_check").fetchone()[0]
    assert ok == "ok", ok

    print("ALL CHECKS PASSED")
    print("temp db:", path)
    shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("FAILED:", type(exc).__name__, exc)
        raise
