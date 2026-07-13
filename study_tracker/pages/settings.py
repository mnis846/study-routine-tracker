"""Settings — goals, subscription tier, Pro unlock."""

import reflex as rx

from study_tracker.components.layout import page_shell
from study_tracker.components.upgrade import unlock_panel, upgrade_cta
from study_tracker.states.tracker_state import TrackerState


@rx.page(route="/settings", title="Settings — Study Tracker", on_load=TrackerState.guard_load_settings)
def settings_page() -> rx.Component:
    return page_shell(
        "Settings",
        rx.card(
            rx.vstack(
                rx.heading("Daily study goal", size="5"),
                rx.hstack(
                    rx.input(
                        type="number",
                        value=TrackerState.goal_input,
                        on_change=TrackerState.set_goal_input,
                        min=0.5,
                        max=16,
                        step=0.5,
                        width="120px",
                    ),
                    rx.text("hours per day"),
                    rx.button("Save", on_click=TrackerState.update_goal, color="indigo"),
                    spacing="3",
                    align="center",
                ),
                spacing="3",
                width="100%",
            ),
            class_name="p-5",
        ),
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.heading("Your plan", size="5"),
                    rx.badge(TrackerState.tier_label, color=rx.cond(TrackerState.is_pro, "green", "indigo"), size="2"),
                    justify="between",
                    width="100%",
                ),
                rx.cond(
                    TrackerState.is_pro,
                    rx.text(
                        "Full access: unlimited targets, garden stages, CSV export, heatmap analytics, and sticker.",
                        class_name="text-slate-600",
                    ),
                    rx.vstack(
                        rx.text(
                            "Free: 3 targets/day, garden capped at early stages, basic tracking.",
                            class_name="text-slate-600",
                        ),
                        rx.link(
                            rx.button("Compare plans & upgrade", color="indigo"),
                            href="/upgrade",
                        ),
                        spacing="2",
                    ),
                ),
                spacing="3",
                width="100%",
            ),
            class_name="p-5",
        ),
        rx.cond(~TrackerState.is_pro, upgrade_cta(), rx.fragment()),
        unlock_panel(),
    )