"""Study Routine Tracker — Flet mobile app (Android APK)."""

import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import flet as ft

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tracker.database import (  # noqa: E402
    DatabaseError,
    add_daily_study_hours,
    award_hours_garden_xp,
    award_target_done_xp,
    get_daily_plan,
    get_daily_plan_summary,
    get_daily_study_goal,
    get_garden_state,
    get_longest_streak,
    get_recent_study_hours,
    get_study_hours_for_date,
    get_study_streak,
    get_week_study_hours,
    init_db,
    process_daily_checkin,
    save_daily_targets,
    save_evening_reflection,
    set_daily_study_goal,
    sync_daily_garden_bonuses,
    update_target_status,
)
from tracker.logbook import (  # noqa: E402
    add_activity_log,
    delete_activity_log,
    get_activity_log_stats,
    get_activity_logs,
)
from tracker.sync import (  # noqa: E402
    default_sync_filename,
    export_database,
    get_sync_metadata,
)
from tracker.garden import GARDEN_STAGES, XP_REWARDS, get_stage_info  # noqa: E402
from tracker.profile import EXAM, EXAM_YEAR, FIRST_NAME, FULL_NAME, MOTTO, greeting, period_nudge, possessive  # noqa: E402

PRIMARY = "#48BB78"
PRIMARY_DARK = "#2F855A"
NAVY = "#1E3A5F"
ACCENT = "#3182CE"
BG = "#F7FAFC"
CARD_BORDER = "#E2E8F0"

MORNING_END_HOUR = 12
EVENING_START_HOUR = 17
LOG_SUBJECTS = [
    "",
    "Paper-1 (Language)",
    "Paper-2 (Essay)",
    "Paper-3 (GS-I)",
    "Paper-4 (GS-II)",
    "Paper-5 (GS-III)",
    "Paper-6 (GS-IV)",
    "Paper-7 (GS-V)",
    "General / Mixed",
]


def period_of_day(now):
    if now.hour < MORNING_END_HOUR:
        return "morning", "🌅 Morning"
    if now.hour < EVENING_START_HOUR:
        return "afternoon", "☀️ Afternoon"
    return "evening", "🌙 Evening"


def metric_card(title, value, subtitle=None):
    return ft.Container(
        content=ft.Column(
            [
                ft.Text(title, size=12, color="#718096"),
                ft.Text(value, size=22, weight=ft.FontWeight.BOLD, color=NAVY),
                ft.Text(subtitle or "", size=11, color="#A0AEC0"),
            ],
            spacing=2,
            tight=True,
        ),
        bgcolor="#FFFFFF",
        border=ft.border.all(1, CARD_BORDER),
        border_radius=12,
        padding=12,
        expand=True,
    )


def section_title(text):
    return ft.Text(text, size=16, weight=ft.FontWeight.BOLD, color=NAVY)


def snack(page, message, color=PRIMARY_DARK):
    page.open(ft.SnackBar(ft.Text(message), bgcolor=color))


def run_db(page, action, error_message="Something went wrong."):
    try:
        return action()
    except DatabaseError as exc:
        snack(page, f"{error_message} ({exc})", "#C53030")
        return None


class TrackerApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.today = date.today()
        self.tomorrow = self.today + timedelta(days=1)
        self.now = datetime.now()
        self.period_key, self.period_label = period_of_day(self.now)
        self.draft_targets = ["", ""]
        self.show_target_form = False
        self.planning_date = None
        self.session_ready = False
        self.tabs = None
        self.export_picker = None
        self.body = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=12)
        self.content_host = ft.Container(content=self.body, expand=True, padding=16)

    def bootstrap(self):
        data_dir = self.page.get_application_documents_directory()
        if data_dir:
            os.environ["TRACKER_DATA_DIR"] = data_dir
        try:
            init_db()
            self.session_ready = True
        except DatabaseError as exc:
            self.body.controls = [
                ft.Text(f"Could not initialize database: {exc}", color="#C53030")
            ]
            return

        xp_before = get_garden_state(get_study_streak())["xp"]
        rewards = process_daily_checkin(get_study_streak())
        rewards += sync_daily_garden_bonuses(self.today)
        for reward in rewards:
            snack(self.page, f"+{reward['xp']} XP — {reward['message']}")

        streak = get_study_streak()
        xp_after = get_garden_state(streak)["xp"]
        if get_stage_info(xp_after)["index"] > get_stage_info(xp_before)["index"]:
            stage = get_stage_info(xp_after)["current"]
            snack(
                self.page,
                f"LEVEL UP! Your tree is now a {stage['name']} {stage['emoji']}!",
                "#6B46C1",
            )

        self.build_shell()
        self.refresh_tab()

    def build_shell(self):
        self.page.title = f"{FIRST_NAME}'s Study Routine Tracker"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.bgcolor = BG
        self.page.padding = 0

        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=200,
            on_change=self.on_tab_change,
            tabs=[
                ft.Tab(label="Targets", icon=ft.Icons.CHECKLIST),
                ft.Tab(label="Hours", icon=ft.Icons.SCHEDULE),
                ft.Tab(label="Logbook", icon=ft.Icons.MENU_BOOK),
                ft.Tab(label="Garden", icon=ft.Icons.PARK),
                ft.Tab(label="Sync", icon=ft.Icons.SYNC),
            ],
            expand=False,
        )

        hero = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        f"🎯 {possessive('Study Routine Tracker')}",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color="#FFFFFF",
                    ),
                    ft.Text(greeting(self.period_key), size=14, color="#FFFFFF"),
                    ft.Text(period_nudge(self.period_key), size=12, italic=True, color="#E2E8F0"),
                    ft.Text(
                        f"{self.now.strftime('%A, %d %B %Y')} · {self.period_label}",
                        size=11,
                        color="#CBD5E0",
                    ),
                ],
                spacing=4,
                tight=True,
            ),
            gradient=ft.LinearGradient(
                begin=ft.alignment.center_left,
                end=ft.alignment.center_right,
                colors=[NAVY, "#2C5282", ACCENT],
            ),
            border_radius=16,
            padding=16,
            margin=ft.margin.only(left=16, right=16, top=12),
        )

        streak = get_study_streak()
        daily_goal = get_daily_study_goal()
        garden = get_garden_state(streak)
        longest = get_longest_streak()

        metrics = ft.Row(
            [
                metric_card("Streak", f"{streak} days"),
                metric_card("Goal", f"{daily_goal:g} h"),
                metric_card("Garden XP", f"{garden['xp']:,}"),
                metric_card("Best", f"{longest} days"),
            ],
            spacing=8,
        )

        self.export_picker = ft.FilePicker(on_result=self._on_export_sync)
        self.page.overlay.append(self.export_picker)

        self.page.add(
            ft.Column(
                [
                    hero,
                    ft.Container(content=metrics, padding=ft.padding.symmetric(horizontal=16)),
                    self.tabs,
                    self.content_host,
                ],
                expand=True,
                spacing=8,
            )
        )

    def _on_export_sync(self, event: ft.FilePickerResultEvent):
        if not event.path:
            return
        if run_db(
            self.page,
            lambda: export_database(event.path),
            "Could not export database",
        ) is None:
            return
        snack(self.page, f"Sync file saved for your computer.")

    def on_tab_change(self, _event):
        self.refresh_tab()

    def refresh_tab(self):
        if not self.session_ready:
            return
        index = self.tabs.selected_index if self.tabs else 0
        self.body.controls.clear()
        builders = [
            self.build_targets_tab,
            self.build_hours_tab,
            self.build_logbook_tab,
            self.build_garden_tab,
            self.build_sync_tab,
        ]
        builders[index]()
        self.page.update()

    def build_targets_tab(self):
        summary = get_daily_plan_summary(self.today)
        plan = get_daily_plan(self.today)
        tomorrow_summary = get_daily_plan_summary(self.tomorrow)

        if not summary["has_plan"] and not self.show_target_form:
            self.body.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                f"{greeting(self.period_key)} No targets set for today yet.",
                                color=NAVY,
                            ),
                            ft.ElevatedButton(
                                "Set today's targets",
                                bgcolor=PRIMARY,
                                color="#FFFFFF",
                                on_click=lambda _: self.open_target_form(self.today),
                            ),
                        ],
                        spacing=8,
                    ),
                    bgcolor="#FFFAF0",
                    border=ft.border.all(1, "#FBD38D"),
                    border_radius=12,
                    padding=12,
                )
            )
        elif summary["has_plan"] and not self.show_target_form:
            self.body.controls.append(
                ft.Text(
                    f"{summary['done']}/{summary['total_targets']} done · "
                    f"{summary['resolved_pct']}% resolved",
                    color=PRIMARY_DARK,
                )
            )
            self.body.controls.append(
                ft.ProgressBar(value=summary["resolved_pct"] / 100, color=PRIMARY, bgcolor="#E2E8F0")
            )
            self.body.controls.append(section_title(f"{FIRST_NAME}'s Targets Today"))

            for item in plan["items"]:
                self.body.controls.append(self.target_row(item))

            if all(i.get("status") in ("Done", "Skipped") for i in plan["items"]):
                self.body.controls.append(
                    ft.Text(
                        f"Well done, {FIRST_NAME}! All targets resolved for today.",
                        color=PRIMARY_DARK,
                        weight=ft.FontWeight.W_600,
                    )
                )
                if not tomorrow_summary["has_plan"]:
                    self.body.controls.append(
                        ft.ElevatedButton(
                            "Plan tomorrow's targets",
                            bgcolor=ACCENT,
                            color="#FFFFFF",
                            on_click=lambda _: self.open_target_form(self.tomorrow),
                        )
                    )

            reflection = (plan.get("evening_reflection") or "") if plan else ""
            reflection_field = ft.TextField(
                label="Evening reflection",
                value=reflection,
                multiline=True,
                min_lines=3,
                max_lines=5,
            )

            def save_reflection(_):
                if run_db(
                    self.page,
                    lambda: save_evening_reflection(self.today, reflection_field.value or ""),
                    "Could not save reflection",
                ) is not None:
                    snack(self.page, "Reflection saved!")

            self.body.controls.extend(
                [
                    section_title("Evening reflection"),
                    reflection_field,
                    ft.ElevatedButton("Save reflection", on_click=save_reflection),
                ]
            )

            self.body.controls.append(
                ft.OutlinedButton(
                    "Replace today's targets",
                    on_click=lambda _: self.open_target_form(
                        self.today,
                        [i["description"] for i in plan["items"]] + [""],
                    ),
                )
            )

        if self.show_target_form and self.planning_date:
            self.body.controls.append(self.target_form(self.planning_date))

    def target_row(self, item):
        item_id = int(item["id"])
        status = item.get("status", "Pending")
        desc = item["description"]
        done = status == "Done"
        skipped = status == "Skipped"

        def toggle_done(e):
            new_status = "Done" if e.control.value else "Pending"
            if run_db(
                self.page,
                lambda: update_target_status(item_id, new_status),
                "Could not update target",
            ) is not None:
                if new_status == "Done":
                    reward = award_target_done_xp()
                    if reward:
                        snack(self.page, f"+{reward['xp']} XP — {reward['message']}")
                self.refresh_tab()

        def skip_target(_):
            if run_db(
                self.page,
                lambda: update_target_status(item_id, "Skipped"),
                "Could not skip target",
            ) is not None:
                self.refresh_tab()

        def undo_skip(_):
            if run_db(
                self.page,
                lambda: update_target_status(item_id, "Pending"),
                "Could not restore target",
            ) is not None:
                self.refresh_tab()

        leading = (
            ft.Text("⏭️", size=18)
            if skipped
            else ft.Checkbox(value=done, on_change=toggle_done)
        )
        text_style = ft.TextStyle(
            decoration=ft.TextDecoration.LINE_THROUGH if done else None,
            color="#718096" if skipped else NAVY,
        )
        actions = []
        if not done and not skipped:
            actions.append(ft.TextButton("Skip", on_click=skip_target))
        elif skipped:
            actions.append(ft.TextButton("Undo", on_click=undo_skip))

        return ft.Container(
            content=ft.Row(
                [
                    leading,
                    ft.Text(desc, expand=True, style=text_style),
                    ft.Row(actions, spacing=0),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor="#FFFFFF",
            border=ft.border.all(1, CARD_BORDER),
            border_radius=12,
            padding=12,
        )

    def open_target_form(self, plan_date, descriptions=None):
        self.show_target_form = True
        self.planning_date = plan_date
        self.draft_targets = list(descriptions) if descriptions else ["", ""]
        self.refresh_tab()

    def target_form(self, plan_date):
        fields = []

        def sync_draft(index, value):
            if index < len(self.draft_targets):
                self.draft_targets[index] = value

        for index, text in enumerate(self.draft_targets):
            field = ft.TextField(
                label=f"Target {index + 1}",
                value=text,
                hint_text="e.g. Paper-7 welfare notes + 10 PYQs",
                on_change=lambda e, i=index: sync_draft(i, e.control.value),
            )
            fields.append(field)

        def add_row(_):
            self.draft_targets = [f.value for f in fields] + [""]
            self.refresh_tab()

        def remove_row(_):
            if len(self.draft_targets) > 1:
                self.draft_targets = [f.value for f in fields][:-1]
                self.refresh_tab()

        def save_targets(_):
            values = [f.value.strip() for f in fields]
            targets = [{"description": text, "planned_hours": 0} for text in values if text]
            if not targets:
                snack(self.page, "Add at least one target.", "#C53030")
                return
            if len(set(t["description"].lower() for t in targets)) != len(targets):
                snack(self.page, "Each target must be unique.", "#C53030")
                return
            if run_db(
                self.page,
                lambda: save_daily_targets(plan_date, targets),
                "Could not save targets",
            ) is None:
                return
            self.show_target_form = False
            self.planning_date = None
            self.draft_targets = ["", ""]
            snack(self.page, f"Saved {len(targets)} target(s)!")
            self.refresh_tab()

        def cancel(_):
            self.show_target_form = False
            self.planning_date = None
            self.draft_targets = ["", ""]
            self.refresh_tab()

        label = (
            "Set today's targets"
            if plan_date == self.today
            else f"Set targets for {plan_date.strftime('%A, %d %b')}"
        )
        return ft.Container(
            content=ft.Column(
                [
                    section_title(label),
                    *fields,
                    ft.Row(
                        [
                            ft.OutlinedButton("＋ Add", on_click=add_row),
                            ft.OutlinedButton("－ Remove last", on_click=remove_row),
                        ]
                    ),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Save Targets",
                                bgcolor=PRIMARY,
                                color="#FFFFFF",
                                on_click=save_targets,
                            ),
                            ft.TextButton("Cancel", on_click=cancel),
                        ]
                    ),
                ],
                spacing=8,
            ),
            bgcolor="#FFFFFF",
            border=ft.border.all(1, CARD_BORDER),
            border_radius=12,
            padding=12,
        )

    def build_hours_tab(self):
        daily_goal = get_daily_study_goal()
        today_hours = get_study_hours_for_date(self.today)
        week_df = get_week_study_hours(self.today)
        week_total = round(week_df["hours"].sum(), 1)
        goal_progress = min(today_hours / daily_goal, 1.0) if daily_goal else 0

        self.body.controls.extend(
            [
                section_title(possessive("Study Hours")),
                ft.Row(
                    [
                        metric_card("Today", f"{today_hours}h", f"Goal {daily_goal:g}h"),
                        metric_card("This week", f"{week_total}h"),
                        metric_card("Progress", f"{round(goal_progress * 100)}%"),
                    ],
                    spacing=8,
                ),
                ft.ProgressBar(value=goal_progress, color=PRIMARY, bgcolor="#E2E8F0"),
            ]
        )

        week_bars = []
        max_hours = max(float(week_df["hours"].max()), daily_goal, 1)
        for _, row in week_df.iterrows():
            height = max(8, int((row["hours"] / max_hours) * 120))
            color = PRIMARY if row["is_today"] else ACCENT
            week_bars.append(
                ft.Column(
                    [
                        ft.Container(
                            height=height,
                            width=28,
                            bgcolor=color,
                            border_radius=6,
                        ),
                        ft.Text(f"{row['hours']:.1f}", size=10, color="#718096"),
                        ft.Text(row["day"], size=10, color=NAVY),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                )
            )
        self.body.controls.append(
            ft.Container(
                content=ft.Row(week_bars, alignment=ft.MainAxisAlignment.SPACE_AROUND),
                bgcolor="#FFFFFF",
                border=ft.border.all(1, CARD_BORDER),
                border_radius=12,
                padding=16,
            )
        )

        hours_field = ft.TextField(label="Hours studied", value="2", keyboard_type=ft.KeyboardType.NUMBER)
        notes_field = ft.TextField(label="Notes (optional)")
        date_field = ft.TextField(
            label="Date (YYYY-MM-DD)",
            value=self.today.isoformat(),
        )

        def log_hours(_):
            try:
                hours = float(hours_field.value)
                log_date = date.fromisoformat(date_field.value.strip())
            except (TypeError, ValueError):
                snack(self.page, "Enter valid hours and date.", "#C53030")
                return
            if hours <= 0:
                snack(self.page, "Hours must be greater than zero.", "#C53030")
                return
            if run_db(
                self.page,
                lambda: add_daily_study_hours(log_date, hours, notes_field.value or ""),
                "Could not log study hours",
            ) is None:
                return
            reward = award_hours_garden_xp(hours)
            if reward:
                snack(self.page, f"+{reward['xp']} XP — {reward['message']}")
            else:
                snack(self.page, f"Logged {hours}h for {log_date.strftime('%d %b %Y')}.")
            self.refresh_tab()

        self.body.controls.extend(
            [
                section_title("Log study time"),
                date_field,
                hours_field,
                notes_field,
                ft.ElevatedButton(
                    "Save Hours",
                    bgcolor=PRIMARY,
                    color="#FFFFFF",
                    on_click=log_hours,
                ),
            ]
        )

        recent = get_recent_study_hours()
        if not recent.empty:
            rows = [
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(row["log_date"]))),
                        ft.DataCell(ft.Text(f"{row['hours']:.1f} h")),
                        ft.DataCell(ft.Text(str(row["notes"] or ""))),
                    ]
                )
                for _, row in recent.iterrows()
            ]
            self.body.controls.append(
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("Date")),
                        ft.DataColumn(ft.Text("Hours")),
                        ft.DataColumn(ft.Text("Notes")),
                    ],
                    rows=rows,
                    heading_row_color="#EDF2F7",
                )
            )

        goal_field = ft.TextField(
            label="Daily study goal (hours)",
            value=str(get_daily_study_goal()),
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        def save_goal(_):
            try:
                goal = float(goal_field.value)
            except (TypeError, ValueError):
                snack(self.page, "Enter a valid goal.", "#C53030")
                return
            if run_db(
                self.page,
                lambda: set_daily_study_goal(goal),
                "Could not save study goal",
            ) is not None:
                snack(self.page, "Goal saved!")
                self.refresh_tab()

        self.body.controls.extend(
            [
                section_title("Daily study goal"),
                goal_field,
                ft.ElevatedButton("Save goal", on_click=save_goal),
            ]
        )

    def build_logbook_tab(self):
        stats = get_activity_log_stats()
        year_stats = get_activity_log_stats(EXAM_YEAR)

        self.body.controls.extend(
            [
                section_title(possessive("Study Logbook")),
                ft.Text(
                    "Describe what you studied. Saved locally, kept year-round.",
                    size=12,
                    color="#718096",
                ),
                ft.Row(
                    [
                        metric_card("Total entries", str(stats["total_entries"])),
                        metric_card(f"Days ({EXAM_YEAR})", str(year_stats["days_logged"])),
                    ],
                    spacing=8,
                ),
            ]
        )

        date_field = ft.TextField(
            label="Date (YYYY-MM-DD)",
            value=self.today.isoformat(),
        )
        subject_field = ft.Dropdown(
            label="Paper / subject (optional)",
            options=[ft.dropdown.Option(s, s or "— Select —") for s in LOG_SUBJECTS],
            value="",
        )
        activity_field = ft.TextField(
            label="What did you study?",
            multiline=True,
            min_lines=4,
            max_lines=8,
        )
        duration_field = ft.TextField(
            label="Duration hours (optional)",
            value="",
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        def save_entry(_):
            activity = (activity_field.value or "").strip()
            if not activity:
                snack(self.page, "Write what you studied before saving.", "#C53030")
                return
            try:
                log_date = date.fromisoformat(date_field.value.strip())
            except ValueError:
                snack(self.page, "Enter a valid date (YYYY-MM-DD).", "#C53030")
                return
            duration = None
            if duration_field.value and duration_field.value.strip():
                try:
                    duration_val = float(duration_field.value)
                    if duration_val > 0:
                        duration = duration_val
                except ValueError:
                    snack(self.page, "Enter a valid duration or leave blank.", "#C53030")
                    return
            if run_db(
                self.page,
                lambda: add_activity_log(
                    log_date,
                    activity,
                    subject_field.value or "",
                    duration,
                ),
                "Could not save log entry",
            ) is None:
                return
            snack(self.page, f"Logged for {log_date.strftime('%d %b %Y')}.")
            activity_field.value = ""
            duration_field.value = ""
            self.refresh_tab()

        self.body.controls.extend(
            [
                section_title("Add an entry"),
                date_field,
                subject_field,
                activity_field,
                duration_field,
                ft.ElevatedButton(
                    "Save entry",
                    bgcolor=PRIMARY,
                    color="#FFFFFF",
                    on_click=save_entry,
                ),
            ]
        )

        entries = get_activity_logs(year=EXAM_YEAR, limit=100)
        self.body.controls.append(section_title(f"Recent entries ({EXAM_YEAR})"))

        if entries.empty:
            self.body.controls.append(
                ft.Text(
                    f"No logbook entries yet. Add what you studied today, {FIRST_NAME}.",
                    color="#718096",
                )
            )
            return

        for _, row in entries.iterrows():
            entry_id = int(row["id"])
            entry_date = str(row["log_date"])[:10]
            subject_label = row["subject"] or "General"
            duration_label = ""
            try:
                duration_val = float(row["duration_hours"])
                if duration_val > 0:
                    duration_label = f" · {duration_val:.1f}h"
            except (TypeError, ValueError):
                pass

            def delete_entry(_e, eid=entry_id):
                if run_db(
                    self.page,
                    lambda: delete_activity_log(eid),
                    "Could not delete entry",
                ) is not None:
                    snack(self.page, "Entry deleted.")
                    self.refresh_tab()

            self.body.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        f"{entry_date} · {subject_label}{duration_label}",
                                        weight=ft.FontWeight.BOLD,
                                        color=NAVY,
                                        expand=True,
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE_OUTLINE,
                                        icon_color="#C53030",
                                        tooltip="Delete",
                                        on_click=delete_entry,
                                    ),
                                ],
                            ),
                            ft.Text(str(row["activity"]), color="#4A5568"),
                        ],
                        spacing=4,
                        tight=True,
                    ),
                    bgcolor="#FFFFFF",
                    border=ft.border.all(1, CARD_BORDER),
                    border_radius=12,
                    padding=12,
                )
            )

    def build_garden_tab(self):
        streak = get_study_streak()
        garden = get_garden_state(streak)
        info = garden["stage_info"]
        stage = info["current"]
        pct = int(info["progress"] * 100)

        self.body.controls.append(section_title(f"🌳 {possessive('Study Garden')}"))
        self.body.controls.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            f"{stage['emoji']} {stage['name']}",
                            size=22,
                            weight=ft.FontWeight.BOLD,
                            color=PRIMARY_DARK,
                        ),
                        ft.Text(f"{garden['xp']:,} Growth XP", color=NAVY),
                        ft.ProgressBar(value=info["progress"], color=PRIMARY, bgcolor="#E2E8F0"),
                        ft.Text(
                            "MAX 🏆"
                            if info["is_max"]
                            else f"{info['xp_to_next']} XP to {info['next']['name']} {info['next']['emoji']}",
                            color="#4A5568",
                        ),
                        ft.Text(
                            f"Every session brings you closer to {EXAM}, {FIRST_NAME}.",
                            italic=True,
                            color="#718096",
                            size=12,
                        ),
                    ],
                    spacing=6,
                ),
                bgcolor="#F0FFF4",
                border=ft.border.all(1, "#9AE6B4"),
                border_radius=16,
                padding=16,
            )
        )

        self.body.controls.append(
            ft.Row(
                [
                    metric_card("Growth XP", f"{garden['xp']:,}"),
                    metric_card("Stage", f"{info['index'] + 1}/{len(GARDEN_STAGES)}"),
                    metric_card("Streak", f"{streak} days"),
                ],
                spacing=8,
            )
        )

        self.body.controls.append(section_title("How to earn Growth XP"))
        self.body.controls.append(
            ft.Container(
                content=ft.Text(
                    f"🌅 Daily check-in — +{XP_REWARDS['daily_checkin']} XP\n"
                    f"⏱️ Study — +{XP_REWARDS['per_hour']} XP/hr\n"
                    f"🎯 Hit goal — +{XP_REWARDS['daily_goal']} XP\n"
                    f"✅ Complete target — +{XP_REWARDS['target_done']} XP\n"
                    f"🏆 All targets — +{XP_REWARDS['all_targets']} XP",
                    color=NAVY,
                ),
                bgcolor="#EBF8FF",
                border_radius=12,
                padding=12,
            )
        )

        badges = ft.Row(wrap=True, spacing=8, run_spacing=8)
        for stage_def in GARDEN_STAGES:
            earned = garden["xp"] >= stage_def["min_xp"]
            badges.controls.append(
                ft.Container(
                    content=ft.Text(
                        f"{stage_def['emoji']} {stage_def['name']}" + ("" if earned else " 🔒"),
                        size=12,
                        color=PRIMARY_DARK if earned else "#A0AEC0",
                    ),
                    bgcolor="#C6F6D5" if earned else "#EDF2F7",
                    border_radius=999,
                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                )
            )
        self.body.controls.extend([section_title("Evolution path"), badges])

        events = garden.get("events")
        if events is not None and not events.empty:
            rows = [
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(row["event_date"])[:16])),
                        ft.DataCell(
                            ft.Text(f"+{int(row['xp_amount'])} XP — {row['message']}")
                        ),
                    ]
                )
                for _, row in events.iterrows()
            ]
            self.body.controls.extend(
                [
                    section_title("Recent growth"),
                    ft.DataTable(
                        columns=[
                            ft.DataColumn(ft.Text("When")),
                            ft.DataColumn(ft.Text("Event")),
                        ],
                        rows=rows,
                        heading_row_color="#EDF2F7",
                    ),
                ]
            )


    def build_sync_tab(self):
        meta = get_sync_metadata()
        updated = meta["modified"] or "not saved yet"
        size_label = f"{meta['size_kb']} KB" if meta["exists"] else "—"

        self.body.controls.extend(
            [
                section_title("Sync with computer"),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Your phone is the daily logger. When you sit at your PC:",
                                weight=ft.FontWeight.BOLD,
                                color=NAVY,
                            ),
                            ft.Text(
                                "1. Open this Sync tab and tap Export\n"
                                "2. Save the .db file (Downloads is easiest)\n"
                                "3. Connect phone via USB or cloud drive\n"
                                "4. On PC: open Streamlit → sidebar → Import phone data",
                                color="#4A5568",
                                size=13,
                            ),
                        ],
                        spacing=8,
                    ),
                    bgcolor="#EBF8FF",
                    border=ft.border.all(1, "#90CDF4"),
                    border_radius=12,
                    padding=14,
                ),
                ft.Row(
                    [
                        metric_card("Database", size_label),
                        metric_card("Last saved", updated),
                    ],
                    spacing=8,
                ),
            ]
        )

        def export_for_pc(_):
            if self.export_picker:
                self.export_picker.save_file(
                    dialog_title="Save sync file for PC",
                    file_name=default_sync_filename(),
                    allowed_extensions=["db"],
                )
                return
            snack(self.page, "File picker not ready. Try again.", "#C53030")

        def export_local_copy(_):
            data_dir = self.page.get_application_documents_directory()
            if not data_dir:
                snack(self.page, "Could not find app storage.", "#C53030")
                return
            dest = os.path.join(data_dir, default_sync_filename())
            if run_db(
                self.page,
                lambda: export_database(dest),
                "Could not export database",
            ) is None:
                return
            snack(
                self.page,
                f"Copy saved in app folder. Use Export above to move it to Downloads.",
            )

        self.body.controls.extend(
            [
                section_title("Export for PC"),
                ft.ElevatedButton(
                    "Export sync file",
                    icon=ft.Icons.UPLOAD_FILE,
                    bgcolor=PRIMARY,
                    color="#FFFFFF",
                    on_click=export_for_pc,
                ),
                ft.OutlinedButton(
                    "Backup inside app",
                    icon=ft.Icons.SAVE_ALT,
                    on_click=export_local_copy,
                ),
                ft.Text(
                    "Tip: export after logging each day (or whenever you open your PC). "
                    "Your PC keeps a backup of its old data before each import.",
                    size=12,
                    italic=True,
                    color="#718096",
                ),
            ]
        )


def main(page: ft.Page):
    app = TrackerApp(page)
    app.bootstrap()


if __name__ == "__main__":
    ft.app(target=main)