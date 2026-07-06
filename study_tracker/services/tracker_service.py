"""Core study tracker business logic."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlmodel import select

from study_tracker.db import get_session

from study_tracker.core.config import DEFAULT_DAILY_GOAL_HOURS, FREE_MAX_TARGETS
from study_tracker.core.garden import XP_REWARDS, effective_stage_info, get_stage_info
from study_tracker.core.tiers import is_pro_tier
from study_tracker.models import (
    AppSetting,
    DailyPlan,
    DailyStudyHours,
    DailyTargetItem,
    GardenEvent,
    ScheduledTest,
    StudyActivityLog,
)


def _get_setting(session, user_id: int, key: str, default: str = "") -> str:
    row = session.exec(
        select(AppSetting).where(AppSetting.user_id == user_id, AppSetting.key == key)
    ).first()
    return row.value if row else default


def _set_setting(session, user_id: int, key: str, value: str) -> None:
    row = session.exec(
        select(AppSetting).where(AppSetting.user_id == user_id, AppSetting.key == key)
    ).first()
    if row:
        row.value = value
        session.add(row)
    else:
        session.add(AppSetting(user_id=user_id, key=key, value=value))


def get_daily_goal(user_id: int) -> float:
    with get_session() as session:
        raw = _get_setting(session, user_id, "daily_study_goal_hours", str(DEFAULT_DAILY_GOAL_HOURS))
    try:
        return max(0.5, float(raw))
    except ValueError:
        return DEFAULT_DAILY_GOAL_HOURS


def set_daily_goal(user_id: int, hours: float) -> None:
    with get_session() as session:
        _set_setting(session, user_id, "daily_study_goal_hours", str(max(0.5, hours)))
        session.commit()


def get_garden_xp(user_id: int) -> int:
    with get_session() as session:
        raw = _get_setting(session, user_id, "garden_xp", "0")
    try:
        return max(0, int(raw))
    except ValueError:
        return 0


def add_garden_xp(user_id: int, amount: int, event_type: str, message: str) -> int:
    if amount <= 0:
        return 0
    with get_session() as session:
        current = int(_get_setting(session, user_id, "garden_xp", "0"))
        new_xp = current + amount
        _set_setting(session, user_id, "garden_xp", str(new_xp))
        session.add(
            GardenEvent(
                user_id=user_id,
                event_type=event_type,
                xp_amount=amount,
                message=message,
            )
        )
        session.commit()
    return amount


def get_study_hours_for_date(user_id: int, log_date: date) -> float:
    with get_session() as session:
        row = session.exec(
            select(DailyStudyHours).where(
                DailyStudyHours.user_id == user_id,
                DailyStudyHours.log_date == log_date,
            )
        ).first()
    return float(row.hours) if row else 0.0


def add_study_hours(user_id: int, log_date: date, hours: float, notes: str = "") -> None:
    with get_session() as session:
        row = session.exec(
            select(DailyStudyHours).where(
                DailyStudyHours.user_id == user_id,
                DailyStudyHours.log_date == log_date,
            )
        ).first()
        if row:
            row.hours = float(row.hours) + float(hours)
            old = (row.notes or "").strip()
            new = (notes or "").strip()
            row.notes = f"{old}; {new}" if old and new else (new or old)
            row.updated_at = datetime.utcnow()
            session.add(row)
        else:
            session.add(
                DailyStudyHours(
                    user_id=user_id,
                    log_date=log_date,
                    hours=float(hours),
                    notes=notes or "",
                )
            )
        session.commit()
    add_garden_xp(
        user_id,
        int(hours * XP_REWARDS["per_hour"]),
        "hours",
        f"Logged {hours}h of study",
    )


def get_study_streak(user_id: int) -> int:
    today = date.today()
    with get_session() as session:
        rows = session.exec(
            select(DailyStudyHours)
            .where(DailyStudyHours.user_id == user_id)
            .order_by(DailyStudyHours.log_date.desc())
        ).all()
    hours_by_date = {r.log_date: float(r.hours) for r in rows}
    streak = 0
    cursor = today
    while hours_by_date.get(cursor, 0) > 0:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def get_longest_streak(user_id: int) -> int:
    with get_session() as session:
        rows = session.exec(
            select(DailyStudyHours)
            .where(DailyStudyHours.user_id == user_id)
            .order_by(DailyStudyHours.log_date.asc())
        ).all()
    study_dates = sorted(d for d, h in ((r.log_date, float(r.hours)) for r in rows) if h > 0)
    if not study_dates:
        return 0
    longest = run = 1
    for i in range(1, len(study_dates)):
        if study_dates[i] - study_dates[i - 1] == timedelta(days=1):
            run += 1
            longest = max(longest, run)
        else:
            run = 1
    return longest


def _get_or_create_plan(session, user_id: int, plan_date: date) -> DailyPlan:
    plan = session.exec(
        select(DailyPlan).where(
            DailyPlan.user_id == user_id,
            DailyPlan.plan_date == plan_date,
        )
    ).first()
    if plan:
        return plan
    plan = DailyPlan(user_id=user_id, plan_date=plan_date)
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return plan


def get_daily_plan(user_id: int, plan_date: date) -> dict | None:
    with get_session() as session:
        plan = session.exec(
            select(DailyPlan).where(
                DailyPlan.user_id == user_id,
                DailyPlan.plan_date == plan_date,
            )
        ).first()
        if not plan:
            return None
        items = session.exec(
            select(DailyTargetItem)
            .where(DailyTargetItem.plan_id == plan.id)
            .order_by(DailyTargetItem.order_index, DailyTargetItem.id)
        ).all()
    return {
        "id": plan.id,
        "evening_reflection": plan.evening_reflection,
        "items": [
            {
                "id": i.id,
                "description": i.description,
                "status": i.status,
                "planned_hours": i.planned_hours,
            }
            for i in items
        ],
    }


def get_plan_summary(user_id: int, plan_date: date) -> dict:
    plan = get_daily_plan(user_id, plan_date)
    if not plan or not plan["items"]:
        return {
            "has_plan": False,
            "total_targets": 0,
            "done": 0,
            "pending": 0,
            "skipped": 0,
            "completion_pct": 0,
            "resolved_pct": 0,
        }
    items = plan["items"]
    done = sum(1 for i in items if i["status"] == "Done")
    pending = sum(1 for i in items if i["status"] == "Pending")
    skipped = sum(1 for i in items if i["status"] == "Skipped")
    total = len(items)
    resolved = done + skipped
    return {
        "has_plan": True,
        "total_targets": total,
        "done": done,
        "pending": pending,
        "skipped": skipped,
        "completion_pct": round(done / total * 100) if total else 0,
        "resolved_pct": round(resolved / total * 100) if total else 0,
    }


def save_targets(
    user_id: int,
    plan_date: date,
    descriptions: list[str],
    tier: str,
) -> tuple[bool, str]:
    targets = [d.strip() for d in descriptions if d.strip()]
    if not targets:
        return False, "Add at least one target."
    if not is_pro_tier(tier) and len(targets) > FREE_MAX_TARGETS:
        return False, f"Free plan allows up to {FREE_MAX_TARGETS} targets per day."
    lowered = [t.lower() for t in targets]
    if len(lowered) != len(set(lowered)):
        return False, "Each target must be unique."

    with get_session() as session:
        plan = _get_or_create_plan(session, user_id, plan_date)
        existing = session.exec(
            select(DailyTargetItem).where(DailyTargetItem.plan_id == plan.id)
        ).all()
        status_by_index = {i.order_index: i.status for i in existing}
        for item in existing:
            session.delete(item)
        for idx, desc in enumerate(targets):
            session.add(
                DailyTargetItem(
                    plan_id=plan.id,
                    description=desc,
                    order_index=idx,
                    status=status_by_index.get(idx, "Pending"),
                )
            )
        plan.updated_at = datetime.utcnow()
        session.add(plan)
        session.commit()
    return True, f"Saved {len(targets)} target(s)."


def update_target_status(user_id: int, item_id: int, status: str, tier: str) -> None:
    with get_session() as session:
        item = session.get(DailyTargetItem, item_id)
        if not item:
            return
        plan = session.get(DailyPlan, item.plan_id)
        if not plan or plan.user_id != user_id:
            return
        item.status = status
        session.add(item)
        session.commit()
    if status == "Done":
        add_garden_xp(user_id, XP_REWARDS["target_done"], "target", "Target completed!")


def save_reflection(user_id: int, plan_date: date, reflection: str) -> None:
    with get_session() as session:
        plan = _get_or_create_plan(session, user_id, plan_date)
        plan.evening_reflection = reflection or ""
        plan.updated_at = datetime.utcnow()
        session.add(plan)
        session.commit()


def process_daily_checkin(user_id: int, streak: int) -> list[dict]:
    today_key = "last_garden_checkin"
    with get_session() as session:
        if _get_setting(session, user_id, today_key) == date.today().isoformat():
            return []
    rewards = []
    xp = add_garden_xp(user_id, XP_REWARDS["daily_checkin"], "checkin", "Daily check-in")
    rewards.append({"xp": xp, "message": "Daily check-in 🌱"})
    streak_bonus = min(streak * XP_REWARDS["streak_per_day"], XP_REWARDS["streak_cap"])
    if streak_bonus > 0:
        xp = add_garden_xp(user_id, streak_bonus, "streak", f"{streak}-day streak")
        rewards.append({"xp": xp, "message": f"{streak}-day streak 🔥"})
    with get_session() as session:
        _set_setting(session, user_id, today_key, date.today().isoformat())
        session.commit()
    return rewards


def sync_daily_bonuses(user_id: int, today: date | None = None) -> list[dict]:
    today = today or date.today()
    rewards = []
    summary = get_plan_summary(user_id, today)
    if summary["has_plan"] and summary["done"] + summary["skipped"] >= summary["total_targets"]:
        key = "last_garden_all_targets"
        with get_session() as session:
            if _get_setting(session, user_id, key) != today.isoformat():
                _set_setting(session, user_id, key, today.isoformat())
                session.commit()
                xp = add_garden_xp(user_id, XP_REWARDS["all_targets"], "all_targets", "All targets done")
                rewards.append({"xp": xp, "message": "All targets done 🎉"})
    hours = get_study_hours_for_date(user_id, today)
    goal = get_daily_goal(user_id)
    if hours >= goal:
        key = "last_garden_daily_goal"
        with get_session() as session:
            if _get_setting(session, user_id, key) != today.isoformat():
                _set_setting(session, user_id, key, today.isoformat())
                session.commit()
                xp = add_garden_xp(user_id, XP_REWARDS["daily_goal"], "daily_goal", "Daily goal hit")
                rewards.append({"xp": xp, "message": f"Daily goal hit ({goal:g}h) 🎯"})
    return rewards


def get_week_hours(user_id: int, anchor: date | None = None) -> list[dict]:
    anchor = anchor or date.today()
    monday = anchor - timedelta(days=anchor.weekday())
    names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    result = []
    with get_session() as session:
        for i, name in enumerate(names):
            d = monday + timedelta(days=i)
            row = session.exec(
                select(DailyStudyHours).where(
                    DailyStudyHours.user_id == user_id,
                    DailyStudyHours.log_date == d,
                )
            ).first()
            result.append(
                {
                    "day": name,
                    "log_date": d.isoformat(),
                    "hours": float(row.hours) if row else 0.0,
                    "is_today": d == date.today(),
                }
            )
    return result


def get_recent_hours(user_id: int, limit: int = 14) -> list[dict]:
    with get_session() as session:
        rows = session.exec(
            select(DailyStudyHours)
            .where(DailyStudyHours.user_id == user_id)
            .order_by(DailyStudyHours.log_date.desc())
            .limit(limit)
        ).all()
    return [
        {"log_date": r.log_date.isoformat(), "hours": float(r.hours), "notes": r.notes or ""}
        for r in rows
    ]


def get_heatmap_hours(user_id: int, days: int = 365) -> dict[str, float]:
    end = date.today()
    start = end - timedelta(days=days)
    with get_session() as session:
        rows = session.exec(
            select(DailyStudyHours).where(
                DailyStudyHours.user_id == user_id,
                DailyStudyHours.log_date >= start,
                DailyStudyHours.log_date <= end,
            )
        ).all()
    return {r.log_date.isoformat(): float(r.hours) for r in rows}


def add_activity_log(
    user_id: int,
    log_date: date,
    activity: str,
    subject: str = "",
    duration: float | None = None,
) -> None:
    activity = (activity or "").strip()
    if not activity:
        raise ValueError("Activity is required.")
    with get_session() as session:
        session.add(
            StudyActivityLog(
                user_id=user_id,
                log_date=log_date,
                subject=subject or "",
                activity=activity,
                duration_hours=duration,
            )
        )
        session.commit()


def get_activity_logs(user_id: int, limit: int = 20) -> list[dict]:
    with get_session() as session:
        rows = session.exec(
            select(StudyActivityLog)
            .where(StudyActivityLog.user_id == user_id)
            .order_by(StudyActivityLog.log_date.desc(), StudyActivityLog.created_at.desc())
            .limit(limit)
        ).all()
    return [
        {
            "id": r.id,
            "log_date": r.log_date.isoformat(),
            "subject": r.subject or "General",
            "activity": r.activity,
        }
        for r in rows
    ]


def delete_activity_log(user_id: int, log_id: int) -> None:
    with get_session() as session:
        row = session.get(StudyActivityLog, log_id)
        if row and row.user_id == user_id:
            session.delete(row)
            session.commit()


def get_scheduled_tests(user_id: int) -> list[dict]:
    with get_session() as session:
        rows = session.exec(
            select(ScheduledTest)
            .where(ScheduledTest.user_id == user_id)
            .order_by(ScheduledTest.test_no)
        ).all()
    return [
        {
            "test_no": r.test_no,
            "subject": r.subject,
            "scheduled_date": r.scheduled_date.isoformat() if r.scheduled_date else "",
            "status": r.status,
            "hours_studied": float(r.hours_studied or 0),
            "score": r.score,
            "remarks": r.remarks or "",
        }
        for r in rows
    ]


def update_test(
    user_id: int,
    test_no: int,
    status: str,
    hours_studied: float,
    score: float | None,
    remarks: str,
) -> None:
    with get_session() as session:
        row = session.exec(
            select(ScheduledTest).where(
                ScheduledTest.user_id == user_id,
                ScheduledTest.test_no == test_no,
            )
        ).first()
        if not row:
            return
        row.status = status
        row.hours_studied = hours_studied
        row.score = score if status == "Attempted" else None
        row.remarks = remarks
        session.add(row)
        session.commit()


def get_test_progress(user_id: int) -> dict:
    tests = get_scheduled_tests(user_id)
    attempted = [t for t in tests if t["status"] == "Attempted"]
    scores = [t["score"] for t in attempted if t["score"] is not None]
    return {
        "total": len(tests),
        "attempted": len(attempted),
        "avg_score": round(sum(scores) / len(scores), 1) if scores else None,
        "total_hours": round(sum(t["hours_studied"] for t in tests), 1),
    }


def get_garden_events(user_id: int, limit: int = 8) -> list[dict]:
    with get_session() as session:
        rows = session.exec(
            select(GardenEvent)
            .where(GardenEvent.user_id == user_id)
            .order_by(GardenEvent.id.desc())
            .limit(limit)
        ).all()
    return [
        {
            "event_date": r.event_date.strftime("%d %b %H:%M"),
            "message": f"+{r.xp_amount} XP — {r.message}",
        }
        for r in rows
    ]


def garden_snapshot(user_id: int, tier: str) -> dict:
    xp = get_garden_xp(user_id)
    streak = get_study_streak(user_id)
    stage = effective_stage_info(xp, is_pro_tier(tier))
    return {
        "xp": xp,
        "streak": streak,
        "stage_info": stage,
        "events": get_garden_events(user_id),
    }


def export_csv_rows(user_id: int) -> dict[str, list[dict]]:
    """Return tabular data for analytics export."""
    with get_session() as session:
        hours = session.exec(
            select(DailyStudyHours).where(DailyStudyHours.user_id == user_id)
        ).all()
        tests = session.exec(
            select(ScheduledTest).where(ScheduledTest.user_id == user_id)
        ).all()
        logs = session.exec(
            select(StudyActivityLog).where(StudyActivityLog.user_id == user_id)
        ).all()
    return {
        "study_hours": [
            {"log_date": h.log_date.isoformat(), "hours": h.hours, "notes": h.notes}
            for h in hours
        ],
        "scheduled_tests": [
            {
                "test_no": t.test_no,
                "subject": t.subject,
                "status": t.status,
                "score": t.score,
            }
            for t in tests
        ],
        "activity_logs": [
            {
                "log_date": l.log_date.isoformat(),
                "subject": l.subject,
                "activity": l.activity,
            }
            for l in logs
        ],
    }