"""Garden mood from daily show-up + study hours — LDoE-style zone health."""

from datetime import date

from database import get_daily_study_goal, get_setting, get_study_hours_for_date, set_setting

VITALITY_KEY = "garden_vitality"
MOOD_KEY = "garden_mood"
LAST_VISIT_KEY = "garden_last_visit_date"

MOODS = {
    "thriving": {
        "label": "Thriving Jungle",
        "emoji": "🌲",
        "region": "Green Pine Zone",
        "hint": "Daily show-up + full study goal — jungle stays lush and calming.",
    },
    "wilting": {
        "label": "Oak Bush Wilting",
        "emoji": "🍂",
        "region": "Oak Bush Region",
        "hint": "You logged in but study is below goal — oak turns yellow, water dulls.",
    },
    "frozen": {
        "label": "Cold Zone Freeze",
        "emoji": "❄️",
        "region": "Frozen Sector",
        "hint": "Missed days without opening the app — cold zone spreads, map freezes.",
    },
}

REGIONS = ("pine", "oak", "cold", "water")


def sync_garden_vitality(today=None):
    """Update vitality from missed days and today's logged study hours."""
    if today is None:
        today = date.today()

    vitality = _read_int(VITALITY_KEY, 72)
    mood = get_setting(MOOD_KEY, "thriving") or "thriving"
    last_visit_raw = get_setting(LAST_VISIT_KEY)

    missed_days = 0
    if last_visit_raw:
        last_visit = date.fromisoformat(last_visit_raw)
        if last_visit < today:
            missed_days = max(0, (today - last_visit).days - 1)
            vitality = max(0, vitality - missed_days * 18)

    hours = float(get_study_hours_for_date(today) or 0)
    goal = float(get_daily_study_goal())
    checked_in = get_setting("last_garden_checkin") == today.isoformat()

    if hours >= goal:
        vitality = min(100, vitality + 12)
        mood = "thriving"
    elif checked_in:
        vitality = max(8, vitality - 6)
        mood = "wilting"
    elif missed_days > 0:
        mood = "frozen"
    else:
        mood = mood if mood in MOODS else "wilting"

    if missed_days > 0 and hours < goal:
        mood = "frozen" if hours <= 0 else "wilting"

    set_setting(VITALITY_KEY, str(vitality))
    set_setting(MOOD_KEY, mood)
    set_setting(LAST_VISIT_KEY, today.isoformat())

    info = MOODS[mood]
    return {
        "vitality": vitality,
        "mood": mood,
        "label": info["label"],
        "emoji": info["emoji"],
        "region": info["region"],
        "hint": info["hint"],
        "today_hours": hours,
        "daily_goal": goal,
        "goal_met": hours >= goal,
        "missed_days": missed_days,
        "checked_in": checked_in,
    }


def _read_int(key, default):
    raw = get_setting(key, str(default))
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default