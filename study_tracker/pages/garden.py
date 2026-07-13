"""Study garden gamification page."""

import reflex as rx

from study_tracker.components.layout import page_shell, stat_card
from study_tracker.components.upgrade import upgrade_cta
from study_tracker.core.config import FREE_GARDEN_MAX_STAGE
from study_tracker.core.garden import GARDEN_STAGES, XP_REWARDS
from study_tracker.states.tracker_state import TrackerState


def event_row(event: dict) -> rx.Component:
    return rx.hstack(
        rx.text(event["event_date"], class_name="text-xs text-slate-500 w-28"),
        rx.text(event["message"], class_name="text-sm text-slate-700"),
        spacing="3",
        width="100%",
    )


def stage_badge(stage: dict, index: int) -> rx.Component:
    locked = (index > FREE_GARDEN_MAX_STAGE) & ~TrackerState.is_pro
    return rx.badge(
        f"{stage['emoji']} {stage['name']}",
        color=rx.cond(
            TrackerState.garden_xp >= stage["min_xp"],
            rx.cond(locked, "amber", "green"),
            rx.cond(locked, "gray", "gray"),
        ),
        variant="soft",
        class_name=rx.cond(locked, "opacity-70", ""),
    )


@rx.page(route="/garden", title="Garden — Study Tracker", on_load=TrackerState.guard_load_garden)
def garden_page() -> rx.Component:
    return page_shell(
        "Study Garden",
        rx.text(
            "Grow your tree as you study — XP from check-ins, hours, and targets.",
            class_name="text-slate-600",
        ),
        rx.cond(
            TrackerState.garden_free_capped,
            rx.callout(
                rx.vstack(
                    rx.text(
                        "Free plan caps growth at Young Sapling. Your XP still accumulates — unlock Pro to reveal higher stages.",
                        class_name="text-sm",
                    ),
                    rx.link(rx.button("Unlock all stages", size="2", color="indigo"), href="/upgrade"),
                    spacing="2",
                ),
                icon="lock",
                color="amber",
            ),
            rx.fragment(),
        ),
        rx.box(
            rx.center(
                rx.vstack(
                    rx.text(TrackerState.stage_emoji, font_size="5rem"),
                    rx.heading(TrackerState.stage_name, size="7"),
                    rx.progress(value=TrackerState.stage_progress_pct, width="300px"),
                    spacing="3",
                    align="center",
                ),
                class_name="bg-gradient-to-b from-sky-100 to-emerald-100 rounded-2xl p-12 border border-emerald-200 shadow-sm",
            ),
        ),
        rx.grid(
            stat_card("Growth XP", f"{TrackerState.garden_xp}"),
            stat_card("Streak", f"{TrackerState.streak} days"),
            columns="2",
            spacing="4",
            width="100%",
        ),
        rx.callout(
            f"Daily check-in +{XP_REWARDS['daily_checkin']} XP · "
            f"Study +{XP_REWARDS['per_hour']} XP/hr · "
            f"Target +{XP_REWARDS['target_done']} XP · "
            f"All targets +{XP_REWARDS['all_targets']} XP",
            icon="info",
            color="green",
        ),
        rx.heading("Evolution stages", size="5", class_name="text-slate-800"),
        rx.flex(
            *[stage_badge(s, i) for i, s in enumerate(GARDEN_STAGES)],
            wrap="wrap",
            gap="2",
        ),
        rx.cond(~TrackerState.is_pro, upgrade_cta(), rx.fragment()),
        rx.cond(
            TrackerState.garden_events.length() > 0,
            rx.card(
                rx.vstack(
                    rx.heading("Recent growth", size="5"),
                    rx.foreach(TrackerState.garden_events, event_row),
                    spacing="2",
                    width="100%",
                ),
                class_name="p-4",
            ),
            rx.fragment(),
        ),
    )