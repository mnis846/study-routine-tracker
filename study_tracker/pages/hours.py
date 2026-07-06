"""Study hours logging page."""

import reflex as rx

from study_tracker.components.layout import page_shell, stat_card
from study_tracker.states.tracker_state import TrackerState


def recent_row(row: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(row["log_date"]),
        rx.table.cell(f"{row['hours']}h"),
        rx.table.cell(rx.cond(row["notes"] != "", row["notes"], "—")),
    )


def week_row(day: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(day["day"]),
        rx.table.cell(day["log_date"]),
        rx.table.cell(f"{day['hours']}h"),
    )


@rx.page(route="/hours", title="Hours — Study Tracker", on_load=TrackerState.guard_load_hours)
def hours_page() -> rx.Component:
    return page_shell(
        "Study Hours",
        rx.grid(
            stat_card("Today", f"{TrackerState.today_hours}h"),
            stat_card("This week", f"{TrackerState.week_total}h"),
            stat_card("Goal progress", f"{TrackerState.goal_progress_pct}%"),
            columns="3",
            spacing="4",
            width="100%",
        ),
        rx.card(
            rx.vstack(
                rx.heading("Log study time", size="5"),
                rx.hstack(
                    rx.input(
                        type="number",
                        value=TrackerState.log_hours,
                        on_change=TrackerState.set_log_hours,
                        min=0.25,
                        max=16,
                        step=0.25,
                        width="120px",
                    ),
                    rx.input(
                        placeholder="Notes (optional)",
                        value=TrackerState.log_notes,
                        on_change=TrackerState.set_log_notes,
                        flex="1",
                    ),
                    rx.button("Save", on_click=TrackerState.log_study_hours),
                    width="100%",
                    spacing="3",
                ),
                spacing="3",
                width="100%",
            ),
            class_name="p-4",
        ),
        rx.card(
            rx.vstack(
                rx.heading("This week", size="5"),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Day"),
                            rx.table.column_header_cell("Date"),
                            rx.table.column_header_cell("Hours"),
                        ),
                    ),
                    rx.table.body(rx.foreach(TrackerState.week_hours, week_row)),
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            class_name="p-4",
        ),
        rx.cond(
            TrackerState.recent_hours.length() > 0,
            rx.card(
                rx.vstack(
                    rx.heading("Recent log", size="5"),
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Date"),
                                rx.table.column_header_cell("Hours"),
                                rx.table.column_header_cell("Notes"),
                            ),
                        ),
                        rx.table.body(
                            rx.foreach(TrackerState.recent_hours, recent_row),
                        ),
                        width="100%",
                    ),
                    spacing="3",
                    width="100%",
                ),
                class_name="p-4",
            ),
            rx.fragment(),
        ),
    )