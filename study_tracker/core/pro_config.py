"""Pro / Academy subscription configuration."""

from __future__ import annotations

import os

DEFAULT_PRICE_INR = 499
DEFAULT_ACADEMY_PRICE_INR = 2999

PRO_FEATURES = [
    ("targets", "Unlimited daily targets", "Set as many study goals as you need each day."),
    ("garden", "All garden stages", "Grow the full foundation path and exam sprint grove."),
    ("export", "CSV data export", "Download study hours, targets, and logbook."),
    ("analytics", "Advanced analytics", "GitHub heatmap, longest streak, and weekly trends."),
    ("sticker", "Study coach sticker", "Desktop companion with Star Wars coach characters."),
]

FREE_FEATURES = [
    "3 targets per day",
    "Garden capped at early stages",
    "Basic hours & logbook",
]


def _split_codes(raw: str) -> list[str]:
    return [c.strip().upper() for c in raw.split(",") if c.strip()]


PRO_FEATURE_LABELS = {key: label for key, label, _ in PRO_FEATURES}


def pro_feature_label(feature: str) -> str:
    return PRO_FEATURE_LABELS.get(feature, "Pro feature")


def pro_config() -> dict:
    codes = _split_codes(os.getenv("PRO_UNLOCK_CODES", "STUDYPRO,SHOWUP2026"))
    return {
        "price_inr": int(os.getenv("PRO_PRICE_INR", DEFAULT_PRICE_INR)),
        "academy_price_inr": int(os.getenv("ACADEMY_PRICE_INR", DEFAULT_ACADEMY_PRICE_INR)),
        "payment_link": os.getenv("PRO_PAYMENT_LINK", ""),
        "unlock_codes": codes,
        "support_email": os.getenv("PRO_SUPPORT_EMAIL", "support@studytracker.local"),
    }