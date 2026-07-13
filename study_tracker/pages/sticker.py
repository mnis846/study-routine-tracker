"""Study coach sticker — web preview of desktop companion characters."""

import reflex as rx

from study_tracker.components.layout import page_shell
from study_tracker.components.upgrade import upgrade_cta
from study_tracker.states.tracker_state import TrackerState

COACHES = {
    "yoda": {"name": "Master Yoda", "emoji": "🟢", "accent": "#4ade80", "quote": "Study, you must."},
    "vader": {"name": "Darth Vader", "emoji": "⚫", "accent": "#f87171", "quote": "I find your lack of study disturbing."},
    "mando": {"name": "The Mandalorian", "emoji": "🛡️", "accent": "#94a3b8", "quote": "This is the way… to the books."},
    "dooku": {"name": "Count Dooku", "emoji": "🟤", "accent": "#c084fc", "quote": "Twice the focus, double the notes."},
    "anakin": {"name": "Anakin Skywalker", "emoji": "🔵", "accent": "#60a5fa", "quote": "Another hour closer to victory."},
    "deathstar": {"name": "Desktop companion", "emoji": "🌑", "accent": "#94a3b8", "quote": "Fully operational study station."},
}


def coach_card(key: str, coach: dict) -> rx.Component:
    locked = (key != "yoda") & ~TrackerState.is_pro
    return rx.box(
        rx.vstack(
            rx.image(
                src=f"/stickers/{key}_0.png",
                alt=coach["name"],
                width="120px",
                height="auto",
                class_name=rx.cond(locked, "opacity-40 grayscale", ""),
            ),
            rx.text(coach["emoji"], font_size="1.5rem"),
            rx.text(coach["name"], class_name="font-semibold text-slate-900"),
            rx.text(coach["quote"], class_name="text-xs text-slate-500 text-center"),
            rx.cond(
                locked,
                rx.badge("Pro", color="amber", size="1"),
                rx.fragment(),
            ),
            spacing="2",
            align="center",
        ),
        class_name=rx.cond(
            locked,
            "bg-slate-50 rounded-xl border border-dashed border-slate-300 p-4 opacity-90",
            "bg-white rounded-xl border border-slate-200 p-4 hover:shadow-md transition-shadow cursor-pointer",
        ),
        on_click=TrackerState.select_sticker_coach(key),
    )


@rx.page(route="/sticker", title="Sticker — Study Tracker", on_load=TrackerState.guard_load_sticker)
def sticker_page() -> rx.Component:
    return page_shell(
        "Study Coach Sticker",
        rx.callout(
            "The desktop sticker widget (Tkinter) still runs alongside this web app. "
            "Pick your coach character — same sprites as the floating companion.",
            icon="bot",
            color="indigo",
        ),
        rx.cond(~TrackerState.is_pro, upgrade_cta(), rx.fragment()),
        rx.grid(
            *[coach_card(k, c) for k, c in COACHES.items()],
            columns="3",
            spacing="4",
            width="100%",
            class_name="grid-cols-2 lg:grid-cols-3",
        ),
        rx.card(
            rx.vstack(
                rx.heading("Selected coach", size="5"),
                rx.text(TrackerState.sticker_coach, class_name="text-slate-600 capitalize"),
                rx.text(
                    "Run the desktop companion: python desktop_companion.py",
                    class_name="text-sm text-slate-500",
                ),
                spacing="2",
            ),
            class_name="p-4",
        ),
    )