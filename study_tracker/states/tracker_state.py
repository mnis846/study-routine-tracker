"""Dashboard and tracker page state."""

from __future__ import annotations

from datetime import date, datetime

import reflex as rx

from study_tracker.components.heatmap import render_heatmap_html
from study_tracker.core.config import FREE_MAX_TARGETS
from study_tracker.services.tracker_service import (
    add_activity_log,
    add_study_hours,
    delete_activity_log,
    garden_snapshot,
    get_activity_logs,
    get_daily_goal,
    get_daily_plan,
    get_heatmap_hours,
    get_longest_streak,
    get_plan_summary,
    get_recent_hours,
    get_scheduled_tests,
    get_study_hours_for_date,
    get_study_streak,
    get_test_progress,
    get_week_hours,
    process_daily_checkin,
    save_reflection,
    save_targets,
    set_daily_goal,
    sync_daily_bonuses,
    update_target_status,
    update_test,
)
from study_tracker.states.auth_state import AuthState


class TrackerState(AuthState):
    """Extends auth with study data loaded per page."""

    streak: int = 0
    daily_goal: float = 6.0
    today_hours: float = 0.0
    garden_xp: int = 0
    longest_streak: int = 0
    plan_summary: dict = {}
    plan_items: list[dict] = []
    week_hours: list[dict] = []
    recent_hours: list[dict] = []
    activity_logs: list[dict] = []
    tests: list[dict] = []
    test_progress: dict = {}
    tests_attempted: int = 0
    tests_total: int = 0
    tests_total_hours: float = 0.0
    garden_events: list[dict] = []
    stage_name: str = "Dormant Seed"
    stage_emoji: str = "🌰"
    stage_progress: float = 0.0
    toast_message: str = ""

    target_1: str = ""
    target_2: str = ""
    target_3: str = ""
    has_plan: bool = False
    plan_done: int = 0
    plan_total: int = 0
    plan_resolved_pct: int = 0
    log_hours: float = 2.0
    log_notes: str = ""
    log_activity: str = ""
    log_subject: str = "General Studies I"
    evening_reflection: str = ""
    goal_input: float = 6.0

    break_category: str = "Pop"
    break_game: str = "Bubble Pop"
    sticker_coach: str = "yoda"
    heatmap_html: str = ""

    def _guard(self):
        return self._try_restore_session()

    @rx.event
    def guard_load_dashboard(self):
        redirect = self._guard()
        if redirect:
            return redirect
        self.load_dashboard()

    @rx.event
    def guard_load_targets(self):
        redirect = self._guard()
        if redirect:
            return redirect
        self.load_targets()

    @rx.event
    def guard_load_hours(self):
        redirect = self._guard()
        if redirect:
            return redirect
        self.load_hours()

    @rx.event
    def guard_load_logbook(self):
        redirect = self._guard()
        if redirect:
            return redirect
        self.load_logbook()

    @rx.event
    def guard_load_tests(self):
        redirect = self._guard()
        if redirect:
            return redirect
        self.load_tests()

    @rx.event
    def guard_load_garden(self):
        redirect = self._guard()
        if redirect:
            return redirect
        self.load_garden()

    @rx.event
    def guard_load_break(self):
        redirect = self._guard()
        if redirect:
            return redirect

    @rx.event
    def guard_load_sticker(self):
        redirect = self._guard()
        if redirect:
            return redirect

    @rx.event
    def load_dashboard(self) -> None:
        if not self.is_authenticated:
            return
        uid = self.user_id
        today = date.today()
        self.streak = get_study_streak(uid)
        self.daily_goal = get_daily_goal(uid)
        self.goal_input = self.daily_goal
        self.today_hours = get_study_hours_for_date(uid, today)
        self.longest_streak = get_longest_streak(uid) if self.is_pro else 0
        snap = garden_snapshot(uid, self.tier)
        self.garden_xp = snap["xp"]
        self.garden_events = snap["events"]
        info = snap["stage_info"]
        self.stage_name = info["current"]["name"]
        self.stage_emoji = info["current"]["emoji"]
        self.stage_progress = info["progress"]
        process_daily_checkin(uid, self.streak)
        sync_daily_bonuses(uid, today)
        summary = get_plan_summary(uid, today)
        self.plan_summary = summary
        self._apply_summary(summary)
        plan = get_daily_plan(uid, today)
        self.plan_items = plan["items"] if plan else []
        self.evening_reflection = (plan or {}).get("evening_reflection", "")
        self.week_hours = get_week_hours(uid)
        raw_hours = get_heatmap_hours(uid)
        hours_by_date = {
            datetime.strptime(k, "%Y-%m-%d").date(): v for k, v in raw_hours.items()
        }
        self.heatmap_html = render_heatmap_html(
            hours_by_date,
            streak=self.streak,
            daily_goal=self.daily_goal,
            display_name=self.display_name,
        )

    def _apply_summary(self, summary: dict) -> None:
        self.has_plan = bool(summary.get("has_plan"))
        self.plan_done = int(summary.get("done", 0))
        self.plan_total = int(summary.get("total_targets", 0))
        self.plan_resolved_pct = int(summary.get("resolved_pct", 0))

    @rx.event
    def load_targets(self) -> None:
        if not self.is_authenticated:
            return
        today = date.today()
        summary = get_plan_summary(self.user_id, today)
        self.plan_summary = summary
        self._apply_summary(summary)
        plan = get_daily_plan(self.user_id, today)
        self.plan_items = plan["items"] if plan else []
        self.evening_reflection = (plan or {}).get("evening_reflection", "")

    @rx.event
    def save_daily_targets(self):
        descriptions = [self.target_1, self.target_2, self.target_3]
        ok, msg = save_targets(self.user_id, date.today(), descriptions, self.tier)
        if not ok:
            return rx.toast.error(msg)
        self.load_targets()
        return rx.toast.success(msg)

    @rx.event
    def set_target_1(self, value: str) -> None:
        self.target_1 = value

    @rx.event
    def set_target_2(self, value: str) -> None:
        self.target_2 = value

    @rx.event
    def set_target_3(self, value: str) -> None:
        self.target_3 = value

    @rx.event
    def set_evening_reflection(self, value: str) -> None:
        self.evening_reflection = value

    @rx.event
    def mark_target_done(self, item_id: int) -> None:
        update_target_status(self.user_id, item_id, "Done", self.tier)
        self.load_targets()
        self.load_dashboard()

    @rx.event
    def mark_target_pending(self, item_id: int) -> None:
        update_target_status(self.user_id, item_id, "Pending", self.tier)
        self.load_targets()

    @rx.event
    def skip_target(self, item_id: int) -> None:
        update_target_status(self.user_id, item_id, "Skipped", self.tier)
        self.load_targets()

    @rx.event
    def save_evening_reflection(self):
        save_reflection(self.user_id, date.today(), self.evening_reflection)
        return rx.toast.success("Reflection saved.")

    @rx.event
    def load_hours(self) -> None:
        if not self.is_authenticated:
            return
        uid = self.user_id
        today = date.today()
        self.daily_goal = get_daily_goal(uid)
        self.today_hours = get_study_hours_for_date(uid, today)
        self.week_hours = get_week_hours(uid)
        self.recent_hours = get_recent_hours(uid)

    @rx.event
    def log_study_hours(self):
        add_study_hours(self.user_id, date.today(), self.log_hours, self.log_notes)
        self.log_notes = ""
        self.load_hours()
        self.load_dashboard()
        return rx.toast.success(f"Logged {self.log_hours}h.")

    @rx.event
    def update_goal(self):
        set_daily_goal(self.user_id, self.goal_input)
        self.daily_goal = self.goal_input
        return rx.toast.success("Daily goal updated.")

    @rx.event
    def load_logbook(self) -> None:
        if not self.is_authenticated:
            return
        self.activity_logs = get_activity_logs(self.user_id)

    @rx.event
    def quick_log(self):
        if not self.log_activity.strip():
            return rx.toast.error("Write what you studied.")
        add_activity_log(
            self.user_id,
            date.today(),
            self.log_activity,
            self.log_subject,
        )
        self.log_activity = ""
        self.load_logbook()
        return rx.toast.success("Logged!")

    @rx.event
    def remove_log(self, log_id: int) -> None:
        delete_activity_log(self.user_id, log_id)
        self.load_logbook()

    @rx.event
    def load_tests(self) -> None:
        if not self.is_authenticated:
            return
        self.tests = get_scheduled_tests(self.user_id)
        progress = get_test_progress(self.user_id)
        self.test_progress = progress
        self.tests_attempted = int(progress.get("attempted", 0))
        self.tests_total = int(progress.get("total", 0))
        self.tests_total_hours = float(progress.get("total_hours", 0))

    @rx.event
    def load_garden(self) -> None:
        if not self.is_authenticated:
            return
        snap = garden_snapshot(self.user_id, self.tier)
        self.garden_xp = snap["xp"]
        self.garden_events = snap["events"]
        self.streak = get_study_streak(self.user_id)
        info = snap["stage_info"]
        self.stage_name = info["current"]["name"]
        self.stage_emoji = info["current"]["emoji"]
        self.stage_progress = info["progress"]

    @rx.var
    def greeting(self) -> str:
        hour = datetime.now().hour
        name = self.display_name
        if hour < 12:
            return f"Good morning, {name}!"
        if hour < 17:
            return f"Good afternoon, {name}!"
        return f"Good evening, {name}!"

    @rx.var
    def free_target_hint(self) -> str:
        if self.is_pro:
            return ""
        return f"Free plan: up to {FREE_MAX_TARGETS} targets per day."

    @rx.var
    def week_total(self) -> float:
        return round(sum(d["hours"] for d in self.week_hours), 1)

    @rx.event
    def set_log_hours(self, value: str) -> None:
        try:
            self.log_hours = float(value)
        except ValueError:
            pass

    @rx.event
    def set_log_notes(self, value: str) -> None:
        self.log_notes = value

    @rx.event
    def set_log_activity(self, value: str) -> None:
        self.log_activity = value

    @rx.event
    def set_log_subject(self, value: str) -> None:
        self.log_subject = value

    @rx.event
    def set_goal_input(self, value: str) -> None:
        try:
            self.goal_input = float(value)
        except ValueError:
            pass

    @rx.event
    def set_break_category(self, value: str | list[str]) -> None:
        self.break_category = value if isinstance(value, str) else value[0]

    @rx.event
    def set_break_game(self, value: str | list[str]) -> None:
        self.break_game = value if isinstance(value, str) else value[0]

    @rx.event
    def set_sticker_coach(self, key: str) -> None:
        self.sticker_coach = key

    @rx.var
    def goal_progress_pct(self) -> int:
        if not self.daily_goal:
            return 0
        return min(100, int(self.today_hours / self.daily_goal * 100))

    @rx.var
    def stage_progress_pct(self) -> int:
        return min(100, int(self.stage_progress * 100))

    @rx.var
    def break_game_url(self) -> str:
        urls = {
            "Bubble Pop": "/games/bubble_pop.html",
            "Balloon Pop": "/games/balloon_pop.html",
            "Star Catch": "/games/star_catch.html",
            "Space Shooter": "/games/space_shooter.html",
            "Neon Racer": "/games/neon_racer.html",
            "Snake": "/games/snake.html",
            "Breathing": "/games/breathing.html",
        }
        return urls.get(self.break_game, "/games/bubble_pop.html")