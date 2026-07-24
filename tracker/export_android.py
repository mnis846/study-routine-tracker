"""Export Streamlit SQLite data to Android tablet-app JSON backup format."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import date, datetime
from pathlib import Path

from tracker.paths import PROJECT_ROOT, get_db_path


def _iso_date(value) -> str:
    if value is None:
        return date.today().isoformat()
    if isinstance(value, date) and not isinstance(value, datetime):
        return value.isoformat()
    text = str(value).strip()
    if " " in text:
        text = text.split(" ", 1)[0]
    if "T" in text:
        text = text.split("T", 1)[0]
    return text[:10]


def _uid(prefix: str, n: int) -> str:
    return f"{prefix}_{n}"


def export_sqlite_to_android_state(
    db_path: Path, user_id: int | None = None
) -> tuple[dict, dict]:
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    try:
        users = conn.execute(
            "SELECT id, first_name, username FROM users ORDER BY id"
        ).fetchall()
        if not users:
            raise RuntimeError("No users found in the database.")

        if user_id is None:
            best = None
            best_score = -1.0
            for u in users:
                uid = int(u["id"])
                hours_n = conn.execute(
                    "SELECT COUNT(*), COALESCE(SUM(hours),0) FROM daily_study_hours WHERE user_id = ?",
                    (uid,),
                ).fetchone()
                plans_n = conn.execute(
                    "SELECT COUNT(*) FROM daily_plans WHERE user_id = ?",
                    (uid,),
                ).fetchone()[0]
                score = (hours_n[0] or 0) * 10 + float(hours_n[1] or 0) + plans_n
                if score > best_score:
                    best_score = score
                    best = u
            user = best or users[0]
            user_id = int(user["id"])
        else:
            user = conn.execute(
                "SELECT id, first_name, username FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
            if not user:
                raise RuntimeError(f"User id {user_id} not found.")

        def setting(key: str, default: str = "") -> str:
            row = conn.execute(
                "SELECT value FROM app_settings WHERE user_id = ? AND key = ?",
                (user_id, key),
            ).fetchone()
            return str(row["value"]) if row and row["value"] is not None else default

        name = (
            setting("display_name")
            or (user["first_name"] or "").strip()
            or (user["username"] or "Student")
        )
        try:
            daily_goal = float(setting("daily_study_goal_hours", "6") or 6)
        except ValueError:
            daily_goal = 6.0
        daily_goal = max(0.5, min(16.0, daily_goal))

        hours: dict[str, dict] = {}
        for row in conn.execute(
            """SELECT log_date, hours, notes FROM daily_study_hours
               WHERE user_id = ? ORDER BY log_date""",
            (user_id,),
        ):
            d = _iso_date(row["log_date"])
            hours[d] = {
                "hours": round(float(row["hours"] or 0), 2),
                "notes": (row["notes"] or "").strip(),
            }

        plans: dict[str, dict] = {}
        for plan in conn.execute(
            """SELECT id, plan_date, evening_reflection FROM daily_plans
               WHERE user_id = ? ORDER BY plan_date""",
            (user_id,),
        ):
            d = _iso_date(plan["plan_date"])
            items = []
            for item in conn.execute(
                """SELECT id, description, status, order_index
                   FROM daily_target_items
                   WHERE plan_id = ?
                   ORDER BY order_index, id""",
                (int(plan["id"]),),
            ):
                status = (item["status"] or "Pending").strip()
                if status not in ("Pending", "Done", "Skipped"):
                    status = "Pending"
                text = (item["description"] or "").strip()
                if not text:
                    continue
                items.append(
                    {
                        "id": _uid("t", int(item["id"])),
                        "text": text,
                        "status": status,
                    }
                )
            reflection = (plan["evening_reflection"] or "").strip()
            if items or reflection:
                entry: dict = {"items": items}
                if reflection:
                    entry["evening_reflection"] = reflection
                plans[d] = entry

        notes = []
        for row in conn.execute(
            """SELECT id, log_date, subject, activity FROM study_activity_logs
               WHERE user_id = ? ORDER BY log_date DESC, id DESC""",
            (user_id,),
        ):
            text = (row["activity"] or "").strip()
            if not text:
                continue
            notes.append(
                {
                    "id": _uid("n", int(row["id"])),
                    "date": _iso_date(row["log_date"]),
                    "text": text,
                    "subject": (row["subject"] or "General").strip() or "General",
                }
            )

        garden_events = []
        garden_xp_sum = 0
        for row in conn.execute(
            """SELECT id, event_date, xp_amount, message FROM garden_events
               WHERE user_id = ? ORDER BY id DESC""",
            (user_id,),
        ):
            xp = int(row["xp_amount"] or 0)
            garden_xp_sum += max(0, xp)
            garden_events.append(
                {
                    "id": _uid("g", int(row["id"])),
                    "date": _iso_date(row["event_date"]),
                    "xp": xp,
                    "message": (row["message"] or "Growth").strip(),
                }
            )

        garden_xp = garden_xp_sum
        stored_xp = setting("garden_xp", "")
        if stored_xp != "":
            try:
                garden_xp = max(0, int(float(stored_xp)))
            except ValueError:
                pass

        bonuses: dict[str, str] = {}
        key_map = {
            "last_garden_checkin": "checkin",
            "last_garden_daily_goal": "daily_goal",
            "last_garden_all_targets": "all_targets",
        }
        for src, dest in key_map.items():
            val = setting(src, "")
            if val:
                bonuses[dest] = _iso_date(val)

        harvest = setting("last_harvest_tier", "") or None

        state = {
            "version": 2,
            "name": (name[:40] or "Student"),
            "dailyGoal": daily_goal,
            "hours": hours,
            "plans": plans,
            "notes": notes[:3000],
            "gardenXp": garden_xp,
            "gardenEvents": garden_events[:600],
            "bonuses": bonuses,
            "harvestTier": harvest,
            "welcomeSeen": True,
            "createdAt": datetime.now().isoformat(timespec="seconds"),
            "lastSavedAt": datetime.now().isoformat(timespec="seconds"),
            "migratedFrom": {
                "source": "streamlit-sqlite",
                "db": str(db_path),
                "user_id": user_id,
                "exported_at": datetime.now().isoformat(timespec="seconds"),
            },
        }

        summary = {
            "user_id": user_id,
            "name": state["name"],
            "daily_goal": daily_goal,
            "hour_days": len(hours),
            "total_hours": round(sum(h["hours"] for h in hours.values()), 2),
            "plan_days": len(plans),
            "notes": len(notes),
            "garden_xp": garden_xp,
            "garden_events": len(garden_events),
        }
        return state, summary
    finally:
        conn.close()


def export_android_json_bytes(db_path: Path | None = None) -> tuple[bytes, dict]:
    path = db_path or get_db_path()
    state, summary = export_sqlite_to_android_state(path)
    raw = json.dumps(state, indent=2, ensure_ascii=False).encode("utf-8")
    return raw, summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export Study Routine Tracker SQLite to Android JSON backup"
    )
    parser.add_argument("--db", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--user-id", type=int, default=None)
    args = parser.parse_args(argv)

    db_path = args.db or get_db_path()
    out = args.out
    if out is None:
        export_dir = PROJECT_ROOT / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        out = export_dir / f"android_backup_{date.today().isoformat()}.json"

    print(f"Reading: {db_path}")
    state, summary = export_sqlite_to_android_state(db_path, user_id=args.user_id)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

    print("")
    print("Export complete.")
    print(f"  Name:          {summary['name']}")
    print(f"  Daily goal:    {summary['daily_goal']}h")
    print(f"  Days w/ hours: {summary['hour_days']}  (total {summary['total_hours']}h)")
    print(f"  Plan days:     {summary['plan_days']}")
    print(f"  Notes:         {summary['notes']}")
    print(f"  Garden XP:     {summary['garden_xp']}")
    print(f"  File:          {out.resolve()}")
    print("")
    print("On your Android phone:")
    print("  1. Copy this JSON file to the phone (Drive, WhatsApp, USB, email).")
    print("  2. Open Study Tracker -> More -> Restore backup.")
    print("  3. Pick this file.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
