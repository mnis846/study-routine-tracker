"""App configuration from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

DEFAULT_DAILY_GOAL_HOURS = 6.0
FREE_MAX_TARGETS = 3
FREE_GARDEN_MAX_STAGE = 3

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{ROOT / 'reflex_study_tracker.db'}",
)

AUTH_SECRET = os.getenv("AUTH_SECRET", "dev-change-me-in-production")
ADMIN_BOOTSTRAP_EMAIL = os.getenv("ADMIN_BOOTSTRAP_EMAIL", "admin@studytracker.local")
ADMIN_BOOTSTRAP_PASSWORD = os.getenv("ADMIN_BOOTSTRAP_PASSWORD", "admin123")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")