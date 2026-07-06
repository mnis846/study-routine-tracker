"""Admin dashboard for institutes — user management and analytics."""

import reflex as rx
from sqlmodel import select

from study_tracker.components.layout import page_shell
from study_tracker.models import DailyStudyHours, User
from study_tracker.states.tracker_state import TrackerState


class AdminState(TrackerState):
    institute_users: list[dict] = []
    total_students: int = 0
    active_today: int = 0

    @rx.event
    def load_admin(self):
        redirect = self.restore_session()
        if redirect:
            return redirect
        if self.role != "admin":
            return rx.redirect("/dashboard")
        from study_tracker.db import get_session

        with get_session() as session:
            users = list(
                session.exec(
                    select(User).where(User.institute_id == self.institute_id)
                ).all()
            )
            today_hours = session.exec(
                select(DailyStudyHours).where(
                    DailyStudyHours.log_date == __import__("datetime").date.today()
                )
            ).all()
        self.institute_users = [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "role": u.role,
                "tier": u.subscription_tier,
            }
            for u in users
        ]
        self.total_students = sum(1 for u in users if u.role == "student")
        self.active_today = len({h.user_id for h in today_hours})
        return None


def user_row(user: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(user["username"]),
        rx.table.cell(user["email"]),
        rx.table.cell(user["role"]),
        rx.table.cell(user["tier"]),
    )


@rx.page(route="/admin", title="Admin — Study Tracker", on_load=AdminState.load_admin)
def admin_page() -> rx.Component:
    return page_shell(
        "Institute Admin",
        rx.grid(
            rx.card(
                rx.vstack(
                    rx.text("Students", class_name="text-slate-500 text-sm"),
                    rx.heading(AdminState.total_students, size="7"),
                    spacing="1",
                ),
                class_name="p-4",
            ),
            rx.card(
                rx.vstack(
                    rx.text("Active today", class_name="text-slate-500 text-sm"),
                    rx.heading(AdminState.active_today, size="7"),
                    spacing="1",
                ),
                class_name="p-4",
            ),
            columns="2",
            spacing="4",
            width="100%",
        ),
        rx.card(
            rx.vstack(
                rx.heading("Users in your institute", size="5"),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Username"),
                            rx.table.column_header_cell("Email"),
                            rx.table.column_header_cell("Role"),
                            rx.table.column_header_cell("Tier"),
                        ),
                    ),
                    rx.table.body(rx.foreach(AdminState.institute_users, user_row)),
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            class_name="p-4 overflow-x-auto",
        ),
        rx.callout(
            "Analytics export and coach assignment coming in the next sprint. "
            "PostgreSQL + multi-tenant institutes are ready in the schema.",
            icon="chart-bar",
            color="indigo",
        ),
    )