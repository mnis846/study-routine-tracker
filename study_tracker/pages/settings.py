"""Settings — goals, subscription tier, Pro unlock."""

import reflex as rx

from study_tracker.components.layout import page_shell
from study_tracker.states.tracker_state import TrackerState


@rx.page(route="/settings", title="Settings — Study Tracker", on_load=TrackerState.guard_load_hours)
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
                    rx.button("Save", on_click=TrackerState.update_goal),
                    spacing="3",
                    align="center",
                ),
                spacing="3",
                width="100%",
            ),
            class_name="p-4",
        ),
        rx.card(
            rx.vstack(
                rx.heading("Your plan", size="5"),
                rx.badge(TrackerState.tier_label, color="indigo", size="2"),
                rx.cond(
                    TrackerState.is_pro,
                    rx.text("You have full access to tests, export, and garden stages.", class_name="text-slate-600"),
                    rx.vstack(
                        rx.text(
                            "Free: 3 targets/day, garden capped at Young Sapling, basic tests preview.",
                            class_name="text-slate-600",
                        ),
                        rx.text(
                            "Pro / Academy: unlimited targets, full test series, export, admin dashboard.",
                            class_name="text-slate-600",
                        ),
                        spacing="2",
                    ),
                ),
                spacing="3",
                width="100%",
            ),
            class_name="p-4",
        ),
        rx.callout(
            "Payment integration (Razorpay / Stripe) and Supabase Auth can be wired via environment variables. "
            "See .env.example for DATABASE_URL, SUPABASE_URL, and AUTH_SECRET.",
            icon="credit-card",
            color="blue",
        ),
    )