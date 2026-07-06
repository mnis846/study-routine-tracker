"""Study Tracker — Reflex commercial MVP."""

import reflex as rx

import study_tracker.pages  # noqa: F401 — register @rx.page routes
from study_tracker.db import create_tables
from study_tracker.models import (  # noqa: F401 — register tables for migrations
    AppSetting,
    DailyPlan,
    DailyStudyHours,
    DailyTargetItem,
    GardenEvent,
    Institute,
    ScheduledTest,
    StudyActivityLog,
    User,
)
tailwind = {
    "theme": {
        "extend": {
            "colors": {
                "brand": {
                    "50": "#eef2ff",
                    "500": "#6366f1",
                    "600": "#4f46e5",
                },
            },
        },
    },
}

async def _startup():
    create_tables()
    from study_tracker.services.auth_service import bootstrap_admin

    bootstrap_admin()


app = rx.App(
    theme=rx.theme(
        appearance="light",
        accent_color="indigo",
        radius="large",
    ),
    stylesheets=["/styles.css"],
)
app.register_lifespan_task(_startup)