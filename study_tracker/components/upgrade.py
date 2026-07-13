"""Reusable Pro upgrade UI — pricing cards, feature comparison, unlock panel."""

from __future__ import annotations

import reflex as rx

from study_tracker.core.pro_config import PRO_FEATURES
from study_tracker.states.tracker_state import TrackerState


def pricing_card(
    name: str,
    price: str,
    subtitle: str,
    features: list[str],
    *,
    highlighted: bool = False,
    badge: str = "",
) -> rx.Component:
    border = "border-2 border-indigo-500 shadow-lg shadow-indigo-100" if highlighted else "border border-slate-200"
    return rx.box(
        rx.vstack(
            rx.cond(
                badge != "",
                rx.badge(badge, color="indigo", class_name="mb-2"),
                rx.fragment(),
            ),
            rx.heading(name, size="5", class_name="text-slate-900"),
            rx.hstack(
                rx.text(price, class_name="text-3xl font-bold text-slate-900"),
                rx.text(subtitle, class_name="text-sm text-slate-500"),
                align="baseline",
                spacing="2",
            ),
            rx.separator(width="100%"),
            rx.vstack(
                *[rx.hstack(rx.icon("check", size=14, color="var(--green-9)"), rx.text(f, class_name="text-sm text-slate-700"), spacing="2", align="center") for f in features],
                spacing="2",
                width="100%",
                align="start",
            ),
            spacing="4",
            width="100%",
            align="start",
        ),
        class_name=f"bg-white rounded-2xl p-6 {border}",
    )


def unlock_panel(compact: bool = False) -> rx.Component:
    return rx.cond(
        TrackerState.is_pro,
        rx.callout(
            rx.vstack(
                rx.hstack(
                    rx.icon("sparkles", size=18),
                    rx.text(f"⭐ {TrackerState.tier_label} is active", class_name="font-semibold"),
                    spacing="2",
                    align="center",
                ),
                rx.text(
                    "Unlimited targets, full garden path, CSV export, and analytics.",
                    class_name="text-sm",
                ),
                spacing="2",
                align="start",
            ),
            icon="circle_check",
            color="green",
        ),
        rx.card(
            rx.vstack(
                rx.cond(
                    compact,
                    rx.heading("Unlock Pro", size="4"),
                    rx.heading("Already paid? Activate with your code", size="5"),
                ),
                rx.text(
                    "Enter the unlock code from your payment confirmation email.",
                    class_name="text-sm text-slate-600",
                ),
                rx.hstack(
                    rx.input(
                        placeholder="e.g. STUDYPRO",
                        value=TrackerState.unlock_code,
                        on_change=TrackerState.set_unlock_code,
                        width="100%",
                    ),
                    rx.button(
                        "Activate Pro",
                        on_click=TrackerState.unlock_pro,
                        color="indigo",
                    ),
                    spacing="3",
                    width="100%",
                ),
                rx.cond(
                    TrackerState.unlock_message != "",
                    rx.callout(
                        TrackerState.unlock_message,
                        icon=rx.cond(TrackerState.unlock_success, "circle_check", "triangle_alert"),
                        color=rx.cond(TrackerState.unlock_success, "green", "red"),
                    ),
                    rx.fragment(),
                ),
                spacing="3",
                width="100%",
            ),
            class_name="p-5 bg-gradient-to-br from-indigo-50 to-white border-indigo-100",
        ),
    )


def upgrade_cta_compact() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.icon("lock", size=16, color="var(--amber-9)"),
            rx.vstack(
                rx.text(
                    f"Pro — ₹{TrackerState.pro_price_inr} one-time",
                    class_name="font-medium text-sm text-slate-800",
                ),
                rx.text("Unlock unlimited targets, tests, export & more.", class_name="text-xs text-slate-500"),
                spacing="0",
                align="start",
            ),
            rx.link(
                rx.button("Upgrade", size="1", color="indigo"),
                href="/upgrade",
            ),
            justify="between",
            align="center",
            width="100%",
        ),
        class_name="bg-amber-50 border border-amber-200 rounded-xl p-3",
    )


def upgrade_cta() -> rx.Component:
    return rx.callout(
        rx.vstack(
            rx.text(
                f"Pro unlock — ₹{TrackerState.pro_price_inr} one-time",
                class_name="font-semibold",
            ),
            rx.text(
                "Unlimited targets, full garden path, CSV export, and GitHub-style analytics.",
                class_name="text-sm",
            ),
            rx.hstack(
                rx.cond(
                    TrackerState.has_payment_link,
                    rx.link(
                        rx.button(
                            f"Pay ₹{TrackerState.pro_price_inr}",
                            color="indigo",
                        ),
                        href=TrackerState.pro_payment_link,
                        is_external=True,
                    ),
                    rx.fragment(),
                ),
                rx.link(rx.button("View plans", variant="soft"), href="/upgrade"),
                spacing="3",
            ),
            spacing="2",
            align="start",
        ),
        icon="star",
        color="amber",
    )


def pro_features_grid() -> rx.Component:
    return rx.grid(
        *[
            rx.box(
                rx.vstack(
                    rx.icon(icon, size=22, color="var(--indigo-9)"),
                    rx.text(title, class_name="font-semibold text-slate-900 text-sm"),
                    rx.text(desc, class_name="text-xs text-slate-500"),
                    spacing="2",
                    align="start",
                ),
                class_name="bg-white rounded-xl border border-slate-200 p-4 hover:border-indigo-200 transition-colors",
            )
            for icon, title, desc in [
                ("target", PRO_FEATURES[0][1], PRO_FEATURES[0][2]),
                ("clipboard-list", PRO_FEATURES[1][1], PRO_FEATURES[1][2]),
                ("tree-pine", PRO_FEATURES[2][1], PRO_FEATURES[2][2]),
                ("download", PRO_FEATURES[3][1], PRO_FEATURES[3][2]),
                ("chart-no-axes-column", PRO_FEATURES[4][1], PRO_FEATURES[4][2]),
                ("bot", PRO_FEATURES[5][1], PRO_FEATURES[5][2]),
            ]
        ],
        columns="3",
        spacing="4",
        width="100%",
        class_name="grid-cols-1 md:grid-cols-2 lg:grid-cols-3",
    )