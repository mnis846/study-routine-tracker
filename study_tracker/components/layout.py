"""Shared layout — navbar, sidebar, page shell."""

from __future__ import annotations

import reflex as rx

from study_tracker.states.tracker_state import TrackerState

NAV_ITEMS = [
    ("/dashboard", "Dashboard", "layout-dashboard"),
    ("/targets", "Targets", "target"),
    ("/hours", "Hours", "clock"),
    ("/logbook", "Logbook", "book-open"),
    ("/tests", "Tests", "clipboard-list"),
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
            class_name="px-3 py-2 rounded-lg hover:bg-slate-100 transition-colors",
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
                    rx.text(TrackerState.tier_label, class_name="text-xs text-indigo-600"),
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
            rx.separator(),
            rx.vstack(
                *[nav_link(h, l, i) for h, l, i in NAV_ITEMS],
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
        class_name="hidden lg:flex flex-col w-64 min-h-screen border-r border-slate-200 bg-white",
    )


def mobile_nav() -> rx.Component:
    return rx.box(
        rx.hstack(
            *[
                rx.link(
                    rx.icon(icon, size=20),
                    href=href,
                    class_name="p-2 text-slate-600",
                )
                for href, _, icon in NAV_ITEMS[:6]
            ],
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
                    rx.heading(title, size="7", class_name="text-slate-900"),
                    *children,
                    spacing="5",
                    width="100%",
                    padding_bottom="5rem",
                ),
                class_name="flex-1 p-6 lg:p-8 max-w-6xl",
            ),
            align="start",
            width="100%",
            min_height="100vh",
            class_name="bg-slate-50",
        ),
        mobile_nav(),
    )


def stat_card(label: str, value: rx.Var | str, sub: str = "") -> rx.Component:
    return rx.box(
        rx.text(label, class_name="text-xs uppercase tracking-wide text-slate-500"),
        rx.heading(value, size="6", class_name="text-slate-900 mt-1"),
        rx.cond(sub != "", rx.text(sub, class_name="text-sm text-slate-500"), rx.fragment()),
        class_name="bg-white rounded-xl border border-slate-200 p-4 shadow-sm",
    )