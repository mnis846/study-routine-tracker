"""Activity logbook page."""

import reflex as rx

from study_tracker.components.layout import page_shell
from study_tracker.states.tracker_state import TrackerState

LOG_SUBJECTS = [
    "Language / Communication",
    "Essay / Writing",
    "General Studies I",
    "General Studies II",
    "General Studies III",
    "General Studies IV",
    "Optional / Specialization",
    "General / Mixed",
]


def log_row(entry: dict) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.text(entry["log_date"], class_name="text-xs text-slate-500"),
                rx.text(entry["subject"], class_name="text-xs text-indigo-600"),
                spacing="0",
                align="start",
            ),
            rx.text(entry["activity"], class_name="text-slate-800 flex-1"),
            rx.button(
                "✕",
                size="1",
                variant="ghost",
                color="red",
                on_click=TrackerState.remove_log(entry["id"]),
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        class_name="bg-white rounded-lg border border-slate-200 p-3",
    )


@rx.page(route="/logbook", title="Logbook — Study Tracker", on_load=TrackerState.guard_load_logbook)
def logbook_page() -> rx.Component:
    return page_shell(
        "Study Logbook",
        rx.text(
            "One line is enough — saved to your account, kept forever.",
            class_name="text-slate-600",
        ),
        rx.card(
            rx.vstack(
                rx.select(
                    LOG_SUBJECTS,
                    value=TrackerState.log_subject,
                    on_change=TrackerState.set_log_subject,
                    width="100%",
                ),
                rx.hstack(
                    rx.input(
                        placeholder="e.g. Read chapter 3 + 10 practice questions",
                        value=TrackerState.log_activity,
                        on_change=TrackerState.set_log_activity,
                        flex="1",
                    ),
                    rx.button("Log it", on_click=TrackerState.quick_log),
                    width="100%",
                    spacing="3",
                ),
                spacing="3",
                width="100%",
            ),
            class_name="p-4",
        ),
        rx.cond(
            TrackerState.activity_logs.length() > 0,
            rx.vstack(
                rx.heading("Recent entries", size="5"),
                rx.foreach(TrackerState.activity_logs, log_row),
                spacing="3",
                width="100%",
            ),
            rx.callout(
                "No entries yet — log what you studied today.",
                icon="book-open",
                color="blue",
            ),
        ),
    )