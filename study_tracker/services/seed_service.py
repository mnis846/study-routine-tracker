"""Per-user data seeding on registration."""

from __future__ import annotations

from datetime import datetime

from sqlmodel import select

from study_tracker.db import get_session

from study_tracker.core.config import DEFAULT_DAILY_GOAL_HOURS
from study_tracker.core.monsoon_tests import MONSOON_TESTS
from study_tracker.models import AppSetting, ScheduledTest


def seed_user_defaults(user_id: int) -> None:
    with get_session() as session:
        goal = session.exec(
            select(AppSetting).where(
                AppSetting.user_id == user_id,
                AppSetting.key == "daily_study_goal_hours",
            )
        ).first()
        if not goal:
            session.add(
                AppSetting(
                    user_id=user_id,
                    key="daily_study_goal_hours",
                    value=str(DEFAULT_DAILY_GOAL_HOURS),
                )
            )
        tests = session.exec(
            select(ScheduledTest).where(ScheduledTest.user_id == user_id)
        ).first()
        if not tests:
            for test_no, level, test_type, subject, sched, topic in MONSOON_TESTS:
                session.add(
                    ScheduledTest(
                        user_id=user_id,
                        test_no=test_no,
                        level=level,
                        test_type=test_type,
                        subject=subject,
                        scheduled_date=datetime.strptime(sched, "%Y-%m-%d").date(),
                        topic_focus=topic,
                    )
                )
        session.commit()