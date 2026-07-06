"""Sign up page."""

import reflex as rx

from study_tracker.states.auth_state import AuthState


@rx.page(route="/register", title="Sign up — Study Tracker")
def register_page() -> rx.Component:
    return rx.center(
        rx.card(
            rx.vstack(
                rx.heading("Create account", size="7"),
                rx.text(
                    "Free personal plan. Upgrade to Pro or Academy anytime.",
                    class_name="text-slate-600 text-center",
                ),
                rx.form(
                    rx.vstack(
                        rx.input(
                            placeholder="First name",
                            name="first_name",
                            width="100%",
                        ),
                        rx.input(
                            placeholder="Username",
                            name="username",
                            required=True,
                            width="100%",
                        ),
                        rx.input(
                            placeholder="Email",
                            name="email",
                            type="email",
                            required=True,
                            width="100%",
                        ),
                        rx.input(
                            placeholder="Password (min 6 chars)",
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
                        rx.button("Sign up", type="submit", width="100%"),
                        spacing="3",
                        width="100%",
                    ),
                    on_submit=AuthState.register,
                    width="100%",
                ),
                rx.link(
                    "Already have an account? Log in",
                    href="/login",
                    class_name="text-sm text-indigo-600",
                ),
                spacing="4",
                width="100%",
            ),
            class_name="w-full max-w-md p-8",
        ),
        height="100vh",
        class_name="bg-gradient-to-br from-indigo-50 to-slate-100",
    )