"""Subscription tier helpers."""

from study_tracker.models import SubscriptionTier


def is_pro_tier(tier: str) -> bool:
    return tier in (SubscriptionTier.PRO.value, SubscriptionTier.ACADEMY.value)