"""Exam test series page."""

import reflex as rx

from study_tracker.components.layout import page_shell, stat_card
from study_tracker.states.tracker_state import TrackerState


def test_row(test: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(f"#{test['test_no']}"),
        rx.table.cell(test["subject"]),
        rx.table.cell(test["scheduled_date"]),
        rx.table.cell(test["status"]),
        rx.table.cell(f"{test['hours_studied']}h"),
        rx.table.cell(rx.cond(test["score"] != None, test["score"], "—")),
    )


@rx.page(route="/tests", title="Tests — Study Tracker", on_load=TrackerState.guard_load_tests)
def tests_page() -> rx.Component:
    return page_shell(
        "Exam Test Series",
        rx.text(
            "Track scheduled mock tests — hours studied, scores, and weak areas.",
            class_name="text-slate-600",
        ),
        rx.cond(
            TrackerState.is_pro,
            rx.fragment(
                rx.grid(
                    stat_card(
                        "Attempted",
                        f"{TrackerState.tests_attempted}/{TrackerState.tests_total}",
                    ),
                    stat_card("Hours studied", f"{TrackerState.tests_total_hours}h"),
                    columns="2",
                    spacing="4",
                    width="100%",
                ),
                rx.card(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("#"),
                                rx.table.column_header_cell("Subject"),
                                rx.table.column_header_cell("Date"),
                                rx.table.column_header_cell("Status"),
                                rx.table.column_header_cell("Hours"),
                                rx.table.column_header_cell("Score"),
                            ),
                        ),
                        rx.table.body(rx.foreach(TrackerState.tests, test_row)),
                        width="100%",
                    ),
                    class_name="p-4 overflow-x-auto",
                ),
            ),
            rx.callout(
                rx.vstack(
                    rx.text(
                        "Upgrade to Pro for the full exam test schedule, score tracking, and trends."
                    ),
                    rx.link(rx.button("View settings", size="2"), href="/settings"),
                    spacing="2",
                ),
                icon="lock",
                color="amber",
            ),
        ),
    )