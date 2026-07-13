"""Subscription upgrades and Pro unlock."""

from __future__ import annotations

from study_tracker.core.pro_config import pro_config
from study_tracker.models import SubscriptionTier
from study_tracker.services.auth_service import get_user_session, update_user_tier


def unlock_with_code(user_id: int, code: str) -> tuple[bool, str, dict | None]:
    normalized = (code or "").strip().upper()
    if not normalized:
        return False, "Enter your Pro unlock code.", None

    user = get_user_session(user_id)
    if not user:
        return False, "Session expired. Log in again.", None

    if user["subscription_tier"] in (
        SubscriptionTier.PRO.value,
        SubscriptionTier.ACADEMY.value,
    ):
        return True, "Pro is already active on your account.", user

    valid = pro_config()["unlock_codes"]
    if normalized not in valid:
        return False, "Invalid code. Check your payment confirmation email.", None

    update_user_tier(user_id, SubscriptionTier.PRO.value)
    updated = get_user_session(user_id)
    return True, "Pro unlocked! Enjoy unlimited targets, full tests, export, and more.", updated