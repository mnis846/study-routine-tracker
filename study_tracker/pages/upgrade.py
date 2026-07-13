"""Pro / Academy upgrade — pricing, features, unlock."""

import reflex as rx

from study_tracker.components.layout import page_shell
from study_tracker.components.upgrade import (
    pricing_card,
    pro_features_grid,
    unlock_panel,
)
from study_tracker.core.pro_config import FREE_FEATURES, PRO_FEATURES
from study_tracker.states.tracker_state import TrackerState


@rx.page(route="/upgrade", title="Upgrade — Study Tracker", on_load=TrackerState.guard_load_upgrade)
def upgrade_page() -> rx.Component:
    pro_feature_labels = [f[1] for f in PRO_FEATURES]
    return page_shell(
        "Upgrade your study tracker",
        rx.box(
            rx.vstack(
                rx.heading("Level up your discipline", size="8", class_name="text-slate-900"),
                rx.text(
                    "One-time Pro unlock. No subscription. Keep your data forever.",
                    class_name="text-slate-600 text-lg",
                ),
                spacing="2",
                align="start",
            ),
            class_name="mb-2",
        ),
        rx.cond(
            TrackerState.is_pro,
            rx.callout(
                "You're on Pro — every feature below is unlocked. Thank you for supporting the project!",
                icon="sparkles",
                color="green",
            ),
            rx.fragment(),
        ),
        rx.grid(
            pricing_card(
                "Free",
                "₹0",
                "forever",
                FREE_FEATURES,
            ),
            pricing_card(
                "Pro",
                f"₹{TrackerState.pro_price_inr}",
                "one-time",
                pro_feature_labels,
                highlighted=True,
                badge="Most popular",
            ),
            pricing_card(
                "Academy",
                f"₹{TrackerState.academy_price_inr}",
                "per institute",
                [
                    "Everything in Pro",
                    "Coach dashboard",
                    "Bulk student accounts",
                    "Institute analytics",
                    "Priority support",
                ],
            ),
            columns="3",
            spacing="4",
            width="100%",
            class_name="grid-cols-1 lg:grid-cols-3",
        ),
        rx.cond(
            TrackerState.has_payment_link,
            rx.cond(
                ~TrackerState.is_pro,
                rx.card(
                    rx.hstack(
                        rx.vstack(
                            rx.heading("Ready to unlock?", size="5"),
                            rx.text(
                                "Pay securely via Razorpay, then enter your unlock code below.",
                                class_name="text-indigo-100",
                            ),
                            spacing="2",
                            align="start",
                        ),
                        rx.link(
                            rx.button(
                                f"Pay ₹{TrackerState.pro_price_inr} — Get Pro",
                                size="3",
                                color="indigo",
                            ),
                            href=TrackerState.pro_payment_link,
                            is_external=True,
                        ),
                        justify="between",
                        align="center",
                        width="100%",
                        flex_wrap="wrap",
                        gap="4",
                    ),
                    class_name="p-6 bg-gradient-to-r from-indigo-600 to-indigo-500 text-white [&_h5]:text-white",
                ),
                rx.fragment(),
            ),
            rx.fragment(),
        ),
        unlock_panel(),
        rx.heading("Everything in Pro", size="6", class_name="text-slate-900"),
        pro_features_grid(),
        rx.card(
            rx.vstack(
                rx.heading("Free vs Pro", size="5"),
                rx.grid(
                    rx.text("Feature", class_name="font-semibold text-slate-500 text-xs uppercase"),
                    rx.text("Free", class_name="font-semibold text-slate-500 text-xs uppercase text-center"),
                    rx.text("Pro", class_name="font-semibold text-slate-500 text-xs uppercase text-center"),
                    *[
                        item
                        for feat in [
                            ("Daily targets", "3 per day", "Unlimited"),
                            ("Garden stages", "Early stages", "Full foundation + sprint"),
                            ("Study heatmap", "Basic", "Full year + longest streak"),
                            ("CSV export", "—", "Hours, targets, logs"),
                            ("Study sticker", "Preview", "Full coach access"),
                        ]
                        for item in (
                            rx.text(feat[0], class_name="text-sm text-slate-700 py-2"),
                            rx.text(feat[1], class_name="text-sm text-slate-500 py-2 text-center"),
                            rx.text(feat[2], class_name="text-sm text-indigo-700 py-2 text-center font-medium"),
                        )
                    ],
                    columns="3",
                    spacing="2",
                    width="100%",
                    class_name="grid-cols-3",
                ),
                rx.text(
                    f"Questions? Email {TrackerState.pro_support_email}",
                    class_name="text-sm text-slate-500 mt-4",
                ),
                spacing="3",
                width="100%",
            ),
            class_name="p-6",
        ),
    )