"""Break games — embed HTML/JS mini-games."""

import reflex as rx

from study_tracker.components.layout import page_shell
from study_tracker.states.tracker_state import TrackerState


@rx.page(route="/break", title="Break — Study Tracker", on_load=TrackerState.guard_load_break)
def break_page() -> rx.Component:
    return page_shell(
        "Break Time",
        rx.text("Five minutes, then back to study.", class_name="text-slate-600"),
        rx.segmented_control.root(
            rx.segmented_control.item("Pop", value="Pop"),
            rx.segmented_control.item("Arcade", value="Arcade"),
            rx.segmented_control.item("Calm", value="Calm"),
            value=TrackerState.break_category,
            on_change=TrackerState.set_break_category,
            width="100%",
        ),
        rx.select(
            [
                "Bubble Pop",
                "Balloon Pop",
                "Star Catch",
                "Space Shooter",
                "Neon Racer",
                "Snake",
                "Breathing",
            ],
            value=TrackerState.break_game,
            on_change=TrackerState.set_break_game,
            width="100%",
        ),
        rx.el.iframe(
            src=TrackerState.break_game_url,
            class_name="w-full rounded-xl border border-slate-200 bg-white",
            style={"height": "520px", "border": "none"},
        ),
    )