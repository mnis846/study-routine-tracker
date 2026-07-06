"""Login page."""

import reflex as rx

from study_tracker.states.auth_state import AuthState


@rx.page(route="/login", title="Log in — Study Tracker")
def login_page() -> rx.Component:
    return rx.center(
        rx.card(
            rx.vstack(
                rx.heading("📚 Study Tracker", size="7"),
                rx.text(
                    "Log in to track targets, hours, and grow your garden.",
                    class_name="text-slate-600 text-center",
                ),
                rx.form(
                    rx.vstack(
                        rx.input(
                            placeholder="Username",
                            name="username",
                            required=True,
                            width="100%",
                        ),
                        rx.input(
                            placeholder="Password",
                            name="password",
                            type="password",
                            required=True,
                            width="100%",
                        ),
                        rx.cond(
                            AuthState.auth_error != "",
                            rx.callout(
                                AuthState.auth_error,
                                icon="triangle_alert",
                                color="red",
                                width="100%",
                            ),
                            rx.fragment(),
                        ),
                        rx.button("Log in", type="submit", width="100%"),
                        spacing="3",
                        width="100%",
                    ),
                    on_submit=AuthState.login,
                    width="100%",
                ),
                rx.link(
                    "Create a free account",
                    href="/register",
                    class_name="text-sm text-indigo-600",
                ),
                spacing="4",
                width="100%",
            ),
            class_name="w-full max-w-md p-8",
        ),
        on_mount=AuthState.bootstrap,
        height="100vh",
        class_name="bg-gradient-to-br from-indigo-50 to-slate-100",
    )