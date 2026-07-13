"""Per-user data seeding on registration."""

from __future__ import annotations

from sqlmodel import select

from study_tracker.core.config import DEFAULT_DAILY_GOAL_HOURS
from study_tracker.db import get_session
from study_tracker.models import AppSetting


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
        session.commit()
