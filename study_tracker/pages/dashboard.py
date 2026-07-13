"""Main dashboard with metrics and quick overview."""

import reflex as rx

from study_tracker.components.layout import heatmap_section, page_shell, stat_card
from study_tracker.states.tracker_state import TrackerState


@rx.page(route="/dashboard", title="Dashboard — Study Tracker", on_load=TrackerState.guard_load_dashboard)
def dashboard_page() -> rx.Component:
    return page_shell(
        TrackerState.greeting,
        heatmap_section(),
        rx.grid(
            stat_card("Study streak", f"{TrackerState.streak} days"),
            stat_card("Daily goal", f"{TrackerState.daily_goal} h"),
            stat_card("Garden XP", f"{TrackerState.garden_xp}"),
            stat_card(
                "Tree stage",
                f"{TrackerState.stage_emoji} {TrackerState.stage_name}",
            ),
            columns="4",
            spacing="4",
            width="100%",
            class_name="grid-cols-2 lg:grid-cols-4",
        ),
        rx.box(
            rx.hstack(
                rx.text("Today's hours", class_name="font-medium text-slate-800"),
                rx.badge(f"{TrackerState.today_hours}h / {TrackerState.daily_goal}h goal", color="indigo"),
                justify="between",
            ),
            rx.progress(value=TrackerState.goal_progress_pct, width="100%", class_name="mt-3"),
            class_name="bg-white rounded-xl border border-slate-200 p-5 shadow-sm",
        ),
        rx.cond(
            TrackerState.has_plan,
            rx.box(
                rx.heading("Today's targets", size="5", class_name="text-slate-900"),
                rx.text(
                    f"{TrackerState.plan_done}/{TrackerState.plan_total} done · "
                    f"{TrackerState.plan_resolved_pct}% resolved",
                    class_name="text-slate-600",
                ),
                rx.link(rx.button("Manage targets", variant="soft", color="indigo"), href="/targets"),
                class_name="bg-white rounded-xl border border-slate-200 p-5 space-y-3 shadow-sm",
            ),
            rx.callout(
                rx.vstack(
                    rx.text("No targets set for today."),
                    rx.link(rx.button("Set targets", size="2", color="indigo"), href="/targets"),
                    spacing="2",
                ),
                icon="target",
                color="amber",
            ),
        ),
        rx.grid(
            rx.link(
                rx.card(
                    rx.vstack(
                        rx.icon("clock", size=28, color="var(--indigo-9)"),
                        rx.text("Log hours", class_name="font-medium"),
                        align="center",
                    ),
                    class_name="p-6 hover:shadow-md hover:border-indigo-200 transition-all",
                ),
                href="/hours",
            ),
            rx.link(
                rx.card(
                    rx.vstack(
                        rx.icon("tree-pine", size=28, color="var(--green-9)"),
                        rx.text("Visit garden", class_name="font-medium"),
                        align="center",
                    ),
                    class_name="p-6 hover:shadow-md hover:border-emerald-200 transition-all",
                ),
                href="/garden",
            ),
            rx.link(
                rx.card(
                    rx.vstack(
                        rx.icon("coffee", size=28, color="var(--orange-9)"),
                        rx.text("Take a break", class_name="font-medium"),
                        align="center",
                    ),
                    class_name="p-6 hover:shadow-md transition-shadow",
                ),
                href="/break",
            ),
            columns="3",
            spacing="4",
            width="100%",
        ),
    )