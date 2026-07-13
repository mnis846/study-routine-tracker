"""Shared layout — navbar, sidebar, page shell."""

from __future__ import annotations

import reflex as rx

from study_tracker.components.upgrade import upgrade_cta_compact
from study_tracker.states.tracker_state import TrackerState

NAV_ITEMS = [
    ("/dashboard", "Dashboard", "layout-dashboard"),
    ("/targets", "Targets", "target"),
    ("/hours", "Hours", "clock"),
    ("/logbook", "Logbook", "book-open"),
    ("/garden", "Garden", "tree-pine"),
    ("/break", "Break", "coffee"),
    ("/sticker", "Sticker", "bot"),
    ("/settings", "Settings", "settings"),
]


def nav_link(href: str, label: str, icon: str) -> rx.Component:
    return rx.link(
        rx.hstack(
            rx.icon(icon, size=18),
            rx.text(label, class_name="text-sm font-medium"),
            spacing="2",
            align="center",
            class_name="px-3 py-2 rounded-lg hover:bg-slate-100 transition-colors text-slate-700",
        ),
        href=href,
        underline="none",
    )


def sidebar() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text("📚", font_size="1.5rem"),
                rx.vstack(
                    rx.text("Study Tracker", class_name="font-bold text-slate-900"),
                    rx.hstack(
                        rx.badge(TrackerState.tier_label, color=rx.cond(TrackerState.is_pro, "green", "indigo"), size="1"),
                        rx.cond(
                            TrackerState.is_pro,
                            rx.icon("sparkles", size=14, color="var(--green-9)"),
                            rx.fragment(),
                        ),
                        spacing="2",
                        align="center",
                    ),
                    spacing="0",
                    align="start",
                ),
                spacing="3",
                align="center",
            ),
            rx.text(
                f"Hi, {TrackerState.display_name}",
                class_name="text-sm text-slate-600",
            ),
            rx.cond(~TrackerState.is_pro, upgrade_cta_compact(), rx.fragment()),
            rx.separator(),
            rx.vstack(
                *[nav_link(h, l, i) for h, l, i in NAV_ITEMS],
                rx.cond(
                    ~TrackerState.is_pro,
                    nav_link("/upgrade", "Upgrade", "star"),
                    rx.fragment(),
                ),
                rx.cond(
                    TrackerState.is_admin,
                    nav_link("/admin", "Admin", "shield"),
                    rx.fragment(),
                ),
                spacing="1",
                width="100%",
            ),
            rx.spacer(),
            rx.button(
                "Log out",
                on_click=TrackerState.logout,
                variant="outline",
                width="100%",
            ),
            spacing="4",
            height="100%",
            padding="1.5rem",
        ),
        class_name="hidden lg:flex flex-col w-64 min-h-screen border-r border-slate-200 bg-white shrink-0",
    )


def mobile_nav() -> rx.Component:
    return rx.box(
        rx.hstack(
            *[
                rx.link(
                    rx.icon(icon, size=20),
                    href=href,
                    class_name="p-2 text-slate-600 hover:text-indigo-600",
                )
                for href, _, icon in NAV_ITEMS[:5]
            ],
            rx.link(
                rx.icon("star", size=20),
                href="/upgrade",
                class_name="p-2 text-amber-600",
            ),
            justify="between",
            width="100%",
            padding="0.5rem 1rem",
        ),
        class_name="lg:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 z-50",
    )


def page_shell(title: str, *children) -> rx.Component:
    return rx.box(
        rx.hstack(
            sidebar(),
            rx.box(
                rx.vstack(
                    rx.heading(title, size="7", class_name="text-slate-900 tracking-tight"),
                    *children,
                    spacing="5",
                    width="100%",
                    padding_bottom="5rem",
                ),
                class_name="flex-1 p-6 lg:p-8 max-w-6xl w-full",
            ),
            align="start",
            width="100%",
            min_height="100vh",
            class_name="bg-slate-50",
        ),
        mobile_nav(),
    )


def stat_card(label: str, value: rx.Var | str, sub: str = "", *, accent: str = "") -> rx.Component:
    accent_class = f"border-l-4 {accent}" if accent else ""
    return rx.box(
        rx.text(label, class_name="text-xs uppercase tracking-wide text-slate-500 font-medium"),
        rx.heading(value, size="6", class_name="text-slate-900 mt-1"),
        rx.cond(sub != "", rx.text(sub, class_name="text-sm text-slate-500 mt-0.5"), rx.fragment()),
        class_name=f"bg-white rounded-xl border border-slate-200 p-4 shadow-sm {accent_class}",
    )


def heatmap_section() -> rx.Component:
    return rx.cond(
        TrackerState.heatmap_html != "",
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.heading("Study activity", size="5", class_name="text-slate-900"),
                        rx.text(
                            "GitHub-style contribution graph — every green square is a day you showed up.",
                            class_name="text-sm text-slate-500",
                        ),
                        spacing="1",
                        align="start",
                    ),
                    rx.cond(
                        TrackerState.is_pro,
                        rx.badge(f"Longest streak: {TrackerState.longest_streak}d", color="green", variant="soft"),
                        rx.link(
                            rx.badge("Pro: longest streak + export", color="amber", variant="soft"),
                            href="/upgrade",
                        ),
                    ),
                    justify="between",
                    align="start",
                    width="100%",
                    flex_wrap="wrap",
                    gap="3",
                ),
                rx.box(dangerously_set_inner_html={"__html": TrackerState.heatmap_html}),
                rx.grid(
                    stat_card("Show-ups", f"{TrackerState.heatmap_showups}", "days with study", accent="border-l-indigo-500"),
                    stat_card("Total hours", f"{TrackerState.heatmap_total_hours}h", "last 12 months", accent="border-l-emerald-500"),
                    stat_card("Current streak", f"{TrackerState.streak}d", "consecutive days", accent="border-l-amber-500"),
                    columns="3",
                    spacing="4",
                    width="100%",
                    class_name="grid-cols-1 sm:grid-cols-3",
                ),
                spacing="4",
                width="100%",
            ),
            class_name="w-full",
        ),
        rx.fragment(),
    )