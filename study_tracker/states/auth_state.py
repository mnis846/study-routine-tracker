"""Authentication state shared across pages."""

from __future__ import annotations

import reflex as rx

from study_tracker.core.tiers import is_pro_tier as _is_pro_tier
from study_tracker.services.auth_service import (
    authenticate,
    bootstrap_admin,
    get_user_session,
    register_user,
)


class AuthState(rx.State):
    user_id: int = 0
    username: str = ""
    email: str = ""
    first_name: str = ""
    role: str = ""
    tier: str = "free"
    institute_id: int = 0
    is_authenticated: bool = False
    auth_error: str = ""
    auth_message: str = ""
    auth_user_id: str = rx.Cookie(name="st_uid", path="/", max_age=30 * 24 * 3600)

    @rx.var
    def is_pro(self) -> bool:
        return _is_pro_tier(self.tier)

    @rx.var
    def is_admin(self) -> bool:
        return self.role == "admin"

    @rx.var
    def is_coach(self) -> bool:
        return self.role in ("coach", "admin")

    @rx.var
    def display_name(self) -> str:
        return (self.first_name or self.username or "Student").split()[0]

    @rx.var
    def tier_label(self) -> str:
        labels = {"free": "Free", "pro": "Pro", "academy": "Academy"}
        return labels.get(self.tier, self.tier.title())

    @rx.event
    def bootstrap(self) -> None:
        bootstrap_admin()

    def _load_user(self, user: dict) -> None:
        self.user_id = user["id"]
        self.username = user["username"]
        self.email = user["email"]
        self.first_name = user["first_name"] or user["username"]
        self.role = user["role"]
        self.tier = user["subscription_tier"]
        self.institute_id = user["institute_id"] or 0
        self.is_authenticated = True
        self.auth_error = ""
        self.auth_user_id = str(user["id"])

    def _clear_user(self) -> None:
        self.user_id = 0
        self.username = ""
        self.email = ""
        self.first_name = ""
        self.role = ""
        self.tier = "free"
        self.institute_id = 0
        self.is_authenticated = False
        self.auth_user_id = ""

    def _try_restore_session(self):
        """Return redirect to login if session cannot be restored."""
        self.bootstrap()
        if self.is_authenticated:
            return None
        raw = (self.auth_user_id or "").strip()
        if not raw:
            return rx.redirect("/login")
        try:
            uid = int(raw)
        except ValueError:
            self._clear_user()
            return rx.redirect("/login")
        user = get_user_session(uid)
        if not user:
            self._clear_user()
            return rx.redirect("/login")
        self._load_user(user)
        return None

    @rx.event
    def restore_session(self):
        return self._try_restore_session()

    @rx.event
    def login(self, form_data: dict):
        self.auth_error = ""
        user = authenticate(
            form_data.get("username", ""),
            form_data.get("password", ""),
        )
        if not user:
            self.auth_error = "Invalid username or password."
            return rx.toast.error(self.auth_error)
        self._load_user(user)
        return rx.redirect("/dashboard")

    @rx.event
    def register(self, form_data: dict):
        self.auth_error = ""
        self.auth_message = ""
        ok, msg = register_user(
            username=form_data.get("username", ""),
            email=form_data.get("email", ""),
            password=form_data.get("password", ""),
            first_name=form_data.get("first_name", ""),
        )
        if ok:
            self.auth_message = msg
            return rx.toast.success(msg)
        self.auth_error = msg
        return rx.toast.error(msg)

    @rx.event
    def logout(self):
        self._clear_user()
        return rx.redirect("/login")