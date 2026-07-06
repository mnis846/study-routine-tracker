"""Default profile constants for shared modules (garden, coach, mobile)."""

from datetime import date

FULL_NAME = "Student"
FIRST_NAME = "Student"
EXAM = "your goals"
EXAM_YEAR = date.today().year
MOTTO = "Show up daily. Grow your knowledge."

GREETINGS = {
    "morning": f"Good morning, {FIRST_NAME}!",
    "afternoon": f"Good afternoon, {FIRST_NAME}!",
    "evening": f"Good evening, {FIRST_NAME}!",
}

PERIOD_NUDGES = {
    "morning": "Start the day with clear targets — one topic, one win.",
    "afternoon": "Afternoon check-in: stay on track before the day slips away.",
    "evening": "Evening wrap-up — log hours and reflect on what moved the needle.",
}


def greeting(period_key):
    return GREETINGS.get(period_key, f"Hello, {FIRST_NAME}!")


def period_nudge(period_key):
    return PERIOD_NUDGES.get(period_key, MOTTO)


def possessive(label):
    return f"{FIRST_NAME}'s {label}"