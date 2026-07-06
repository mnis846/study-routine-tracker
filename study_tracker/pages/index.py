"""Root redirect to dashboard or login."""

import reflex as rx

from study_tracker.services.auth_service import get_user_session
from study_tracker.states.auth_state import AuthState


class IndexState(AuthState):
    @rx.event
    def redirect_home(self):
        self.bootstrap()
        raw = (self.auth_user_id or "").strip()
        if raw and not self.is_authenticated:
            try:
                user = get_user_session(int(raw))
                if user:
                    self._load_user(user)
                    return rx.redirect("/dashboard")
            except ValueError:
                self._clear_user()
        if self.is_authenticated:
            return rx.redirect("/dashboard")
        return rx.redirect("/login")


@rx.page(route="/", title="Study Tracker", on_load=IndexState.redirect_home)
def index() -> rx.Component:
    return rx.center(rx.spinner(size="3"), height="100vh")