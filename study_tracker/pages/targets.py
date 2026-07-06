"""Daily targets page."""

import reflex as rx

from study_tracker.components.layout import page_shell
from study_tracker.states.tracker_state import TrackerState


def target_row(item: dict) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.cond(
                item["status"] == "Done",
                rx.badge("Done", color="green"),
                rx.cond(
                    item["status"] == "Skipped",
                    rx.badge("Skipped", color="gray"),
                    rx.badge("Pending", color="blue"),
                ),
            ),
            rx.text(item["description"], class_name="text-slate-800 flex-1"),
            rx.cond(
                item["status"] == "Pending",
                rx.button(
                    "Done",
                    size="1",
                    on_click=TrackerState.mark_target_done(item["id"]),
                ),
                rx.cond(
                    item["status"] == "Done",
                    rx.button(
                        "Undo",
                        size="1",
                        variant="ghost",
                        on_click=TrackerState.mark_target_pending(item["id"]),
                    ),
                    rx.fragment(),
                ),
            ),
            spacing="3",
            align="center",
            width="100%",
        ),
        class_name="bg-white rounded-lg border border-slate-200 p-3",
    )


@rx.page(route="/targets", title="Targets — Study Tracker", on_load=TrackerState.guard_load_targets)
def targets_page() -> rx.Component:
    return page_shell(
        "Daily Targets",
        rx.cond(
            TrackerState.free_target_hint != "",
            rx.callout(TrackerState.free_target_hint, icon="info", color="blue"),
            rx.fragment(),
        ),
        rx.card(
            rx.vstack(
                rx.heading("Set today's targets", size="5"),
                rx.input(
                    placeholder="Target 1",
                    value=TrackerState.target_1,
                    on_change=TrackerState.set_target_1,
                    width="100%",
                ),
                rx.input(
                    placeholder="Target 2",
                    value=TrackerState.target_2,
                    on_change=TrackerState.set_target_2,
                    width="100%",
                ),
                rx.input(
                    placeholder="Target 3",
                    value=TrackerState.target_3,
                    on_change=TrackerState.set_target_3,
                    width="100%",
                ),
                rx.button(
                    "Save targets",
                    on_click=TrackerState.save_daily_targets,
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            class_name="p-4",
        ),
        rx.cond(
            TrackerState.has_plan,
            rx.vstack(
                rx.heading("Today's list", size="5"),
                rx.foreach(TrackerState.plan_items, target_row),
                rx.text_area(
                    placeholder="Evening reflection — what went well?",
                    value=TrackerState.evening_reflection,
                    on_change=TrackerState.set_evening_reflection,
                    width="100%",
                ),
                rx.button(
                    "Save reflection",
                    on_click=TrackerState.save_evening_reflection,
                    variant="soft",
                ),
                spacing="3",
                width="100%",
            ),
            rx.fragment(),
        ),
    )