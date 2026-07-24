import html
from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from tracker.app_styles import APP_CSS
from tracker.database import (
    DatabaseError,
    add_daily_study_hours,
    award_hours_garden_xp,
    award_target_done_xp,
    get_daily_plan,
    get_daily_plan_summary,
    get_daily_study_goal,
    get_data_status,
    get_db_path,
    get_export_dataframes,
    get_garden_state,
    get_garden_xp,
    get_local_display_name,
    get_longest_streak,
    get_recent_study_hours,
    get_study_hours_for_date,
    get_study_streak,
    get_week_study_hours,
    init_db,
    process_daily_checkin,
    read_database_backup_bytes,
    save_daily_targets,
    save_evening_reflection,
    set_daily_study_goal,
    set_local_display_name,
    sync_daily_garden_bonuses,
    update_target_status,
)
from tracker.garden import (
    GARDEN_CSS,
    GARDEN_STAGES,
    XP_REWARDS,
    get_stage_info,
    render_interactive_garden,
)
from tracker.logbook import (
    add_activity_log,
    delete_activity_log,
    get_activity_log_stats,
    get_activity_logs,
)
from tracker.showup_grid import load_showup_hours, render_github_heatmap
from tracker.break_games_config import GAME_GROUPS
import tracker.relax_games as relax_games
from tracker.pro import (
    FREE_GARDEN_MAX_STAGE,
    FREE_MAX_TARGETS,
    effective_garden_stage_index,
    free_target_cap_reached,
    is_pro,
    render_pro_unlock_panel,
    render_upgrade_cta,
)
from tracker.styles import MOBILE_CSS

MAX_TARGETS_PER_DAY = 99
LOG_SUBJECTS = [
    "",
    "Language / Communication",
    "Essay / Writing",
    "General Studies I",
    "General Studies II",
    "General Studies III",
    "General Studies IV",
    "Optional / Specialization",
    "General / Mixed",
]
MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
CURRENT_YEAR = date.today().year

APP_MOTTO = "Show up daily. Grow your knowledge."
GREETINGS = {
    "morning": "Good morning!",
    "afternoon": "Good afternoon!",
    "evening": "Good evening!",
}
PERIOD_NUDGES = {
    "morning": "Start the day with clear targets — one topic, one win.",
    "afternoon": "Afternoon check-in: stay on track before the day slips away.",
    "evening": "Evening wrap-up — log hours and reflect on what moved the needle.",
}


def greeting(period_key, first_name=None):
    base = GREETINGS.get(period_key, "Hello!")
    if first_name:
        return base.replace("!", f", {first_name}!")
    return base


def period_nudge(period_key):
    return PERIOD_NUDGES.get(period_key, APP_MOTTO)


def display_first_name():
    try:
        name = get_local_display_name()
    except DatabaseError:
        name = "Student"
    return (name or "Student").split()[0]


st.set_page_config(
    page_title="Study Tracker",
    page_icon="📚",
    layout="wide",
    # Collapsed by default so Android tablets / phones show content first
    initial_sidebar_state="collapsed",
)

st.markdown(GARDEN_CSS + APP_CSS + MOBILE_CSS, unsafe_allow_html=True)

try:
    init_db()  # creates local SQLite profile; no login required
except DatabaseError as exc:
    st.error(f"Could not initialize the database: {exc}")
    st.info(
        "Check that this folder is writable, or set environment variable "
        "`TRACKER_DATA_DIR` to a folder you can write to."
    )
    st.stop()

first_name = display_first_name()
user_id = "local"

# One-time welcome for empty profiles
if "welcome_seen" not in st.session_state:
    st.session_state.welcome_seen = True
    try:
        _status = get_data_status()
        st.session_state.show_welcome = (
            _status["hours_days"] == 0 and _status["plan_days"] == 0
        )
    except DatabaseError:
        st.session_state.show_welcome = False

MORNING_END_HOUR = 12
EVENING_START_HOUR = 17
PERIOD_BADGES = {
    "morning": "morning-badge",
    "afternoon": "afternoon-badge",
    "evening": "evening-badge",
}


def run_db(action, error_message="Something went wrong. Please try again."):
    try:
        return action()
    except DatabaseError as exc:
        st.error(f"{error_message} ({exc})")
        return None


def flash(message, *, level="success", toast=None, toast_icon="💾"):
    """Show a message after the next rerun (Streamlit clears pre-rerun banners)."""
    st.session_state["flash_message"] = {"text": message, "level": level}
    if toast:
        st.session_state.setdefault("pending_ui_toasts", []).append(
            {"text": toast, "icon": toast_icon}
        )


def show_flash():
    payload = st.session_state.pop("flash_message", None)
    if not payload:
        return
    text = payload.get("text", "")
    level = payload.get("level", "success")
    if level == "error":
        st.error(text)
    elif level == "warning":
        st.warning(text)
    elif level == "info":
        st.info(text)
    else:
        st.success(text)


def flush_pending_ui_toasts():
    for item in st.session_state.pop("pending_ui_toasts", []):
        st.toast(item.get("text", "Saved"), icon=item.get("icon", "💾"))


def queue_garden_reward(reward):
    if reward:
        st.session_state.setdefault("pending_garden_toasts", []).append(reward)


def show_garden_rewards(rewards, xp_before):
    if not rewards:
        return
    xp_after = get_garden_xp()
    leveled_up = get_stage_info(xp_after)["index"] > get_stage_info(xp_before)["index"]
    for reward in rewards:
        st.toast(f"+{reward['xp']} XP — {reward['message']}", icon="🌳")
    if leveled_up:
        new_stage = get_stage_info(xp_after)["current"]
        st.balloons()
        st.toast(
            f"LEVEL UP! Your tree is now a {new_stage['name']} {new_stage['emoji']}!",
            icon="🎉",
        )


def flush_pending_garden_toasts():
    pending = st.session_state.pop("pending_garden_toasts", [])
    for reward in pending:
        st.toast(f"+{reward['xp']} XP — {reward['message']}", icon="🌳")


def show_harvest_unlocks(today=None):
    """Toast newly unlocked harvest tiers from the study grove."""
    try:
        from tracker.garden_life import pop_harvest_unlocks

        unlock = pop_harvest_unlocks(today)
    except Exception:
        return
    if not unlock:
        return
    emoji = unlock.get("emoji", "🌳")
    message = unlock.get("message") or unlock.get("label", "Harvest unlocked")
    st.toast(message, icon=emoji)
    if unlock.get("tier") in {"golden", "fruit"}:
        st.balloons()


def render_metric_rows(metric_rows):
    """Render metrics in 2-column rows for mobile-friendly layout."""
    for row in metric_rows:
        cols = st.columns(len(row))
        for col, item in zip(cols, row):
            if len(item) == 3:
                col.metric(item[0], item[1], item[2])
            else:
                col.metric(item[0], item[1])


def render_sidebar():
    st.markdown(f"### Hi, {first_name}")
    st.caption("Local profile · auto-saves on this device")
    st.caption(f"{'⭐ Pro' if is_pro() else 'Free plan'}")
    st.divider()

    st.markdown("**Quick start**")
    st.caption(
        "1. Set today's targets · 2. Log hours · 3. Note what you studied · "
        "4. Grow your garden"
    )
    st.divider()

    st.markdown("**Your name**")
    if "display_name_input" not in st.session_state:
        st.session_state.display_name_input = first_name
    new_name = st.text_input(
        "Display name",
        key="display_name_input",
        label_visibility="collapsed",
        max_chars=40,
        placeholder="What should we call you?",
        help="Shown in greetings. Saved on this device only.",
    )
    if st.button("Save name", key="save_display_name", width="stretch"):
        if run_db(
            lambda: set_local_display_name(new_name),
            "Could not save name",
        ) is not None:
            flash("Name updated!", toast="Name saved", toast_icon="✅")
            st.rerun()

    st.divider()
    st.markdown("**Daily study goal**")
    if "daily_goal_input" not in st.session_state:
        st.session_state.daily_goal_input = float(daily_goal)
    new_goal = st.number_input(
        "Hours per day",
        min_value=0.5,
        max_value=16.0,
        step=0.5,
        key="daily_goal_input",
        label_visibility="collapsed",
        help="Your personal daily hour target. Used for streaks and garden growth.",
    )
    if st.button("Save goal", key="save_goal_main", width="stretch"):
        if run_db(
            lambda: set_daily_study_goal(new_goal),
            "Could not save study goal",
        ) is not None:
            flash("Daily goal updated!", toast="Goal saved", toast_icon="🎯")
            st.rerun()

    st.divider()
    st.markdown("**Local data**")
    try:
        status = get_data_status()
    except DatabaseError as exc:
        st.error(f"Data check failed: {exc}")
        status = None

    if status:
        if status["ok"]:
            st.success("Saving works on this device", icon="💾")
        else:
            st.error("Database needs attention — see path below.")
        st.caption(
            f"**{status['hours_days']}** day(s) with hours · "
            f"**{status['plan_days']}** day(s) with targets · "
            f"**{status['garden_xp']:,}** garden XP"
        )
        st.caption(f"File: `{status['path']}`")
        size_kb = max(1, round(status["size_bytes"] / 1024))
        st.caption(f"Size ~{size_kb} KB · integrity: {status['integrity']}")
    else:
        st.caption(f"Database file:\n`{get_db_path()}`")

    backup_bytes = run_db(read_database_backup_bytes, "Could not build backup")
    if backup_bytes is not None:
        st.download_button(
            label="Download full backup (.db)",
            data=backup_bytes,
            file_name=f"study_routine_tracker_backup_{date.today().isoformat()}.db",
            mime="application/x-sqlite3",
            key="download_sqlite_backup",
            width="stretch",
            help="Free: copy of your entire local database. Keep it somewhere safe.",
        )
    st.caption("Tip: download a backup weekly. Cloud demos can reset when the host sleeps.")
    st.divider()
    render_pro_unlock_panel()


def render_target_item(item):
    """Touch-friendly target card."""
    item_id = int(item["id"])
    status = item.get("status", "Pending")
    is_done = status == "Done"
    is_skipped = status == "Skipped"
    safe_desc = html.escape(item["description"])

    with st.container(border=True):
        row = st.columns([0.12, 0.88])
        with row[0]:
            if not is_skipped:
                st.checkbox(
                    "done",
                    value=is_done,
                    key=f"chk_{item_id}",
                    label_visibility="collapsed",
                    on_change=on_target_toggle,
                    args=(item_id,),
                )
            else:
                st.markdown("⏭️")
        with row[1]:
            if is_done:
                st.markdown(
                    f'<p class="target-card-text target-done">✅ {safe_desc}</p>',
                    unsafe_allow_html=True,
                )
            elif is_skipped:
                st.markdown(
                    f'<p class="target-card-text target-skipped">⏭️ {safe_desc} (skipped)</p>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<p class="target-card-text">⬜ {safe_desc}</p>',
                    unsafe_allow_html=True,
                )

        if not is_done and not is_skipped:
            if st.button("Skip target", key=f"skip_{item_id}", width="stretch"):
                on_target_skip(item_id)
                st.rerun()
        elif is_skipped:
            if st.button("Undo skip", key=f"unskip_{item_id}", width="stretch"):
                on_target_unskip(item_id)
                st.rerun()


def period_of_day(now):
    if now.hour < MORNING_END_HOUR:
        return "morning", "🌅 Morning"
    if now.hour < EVENING_START_HOUR:
        return "afternoon", "☀️ Afternoon"
    return "evening", "🌙 Evening"


def all_targets_resolved(items):
    if not items:
        return False
    return all(i.get("status") in ("Done", "Skipped") for i in items)


def has_duplicate_descriptions(targets):
    descriptions = [t.strip().lower() for t in targets if t.strip()]
    return len(descriptions) != len(set(descriptions))


def draft_count_key(plan_date):
    return f"draft_count_{plan_date.isoformat()}"


def draft_field_key(plan_date, index):
    return f"draft_{plan_date.isoformat()}_{index}"


def init_draft_form(plan_date, descriptions=None):
    items = list(descriptions) if descriptions else ["", ""]
    st.session_state[draft_count_key(plan_date)] = len(items)
    for index, text in enumerate(items):
        st.session_state[draft_field_key(plan_date, index)] = text


def read_draft_targets(plan_date):
    count = st.session_state.get(draft_count_key(plan_date), 2)
    return [
        st.session_state.get(draft_field_key(plan_date, index), "").strip()
        for index in range(count)
    ]


def clear_draft_form(plan_date):
    init_draft_form(plan_date)


def render_target_form(plan_date, label):
    st.markdown(f"**{label}**")
    if draft_count_key(plan_date) not in st.session_state:
        init_draft_form(plan_date)

    count = st.session_state[draft_count_key(plan_date)]
    for index in range(count):
        st.text_input(
            f"Target {index + 1}",
            key=draft_field_key(plan_date, index),
            placeholder="e.g. Finish chapter 5 notes + 20 practice questions",
        )

    max_targets = 99 if is_pro() else FREE_MAX_TARGETS
    if not is_pro():
        st.caption(f"Free plan: up to {FREE_MAX_TARGETS} targets per day.")

    b1, b2 = st.columns(2)
    with b1:
        if st.button("＋ Add target", key=f"add_{plan_date}", width="stretch"):
            if count >= max_targets:
                st.warning(
                    f"Free plan allows {FREE_MAX_TARGETS} targets. "
                    "Upgrade to Pro in Settings for unlimited targets."
                )
            else:
                next_index = st.session_state[draft_count_key(plan_date)]
                st.session_state[draft_count_key(plan_date)] = next_index + 1
                st.session_state[draft_field_key(plan_date, next_index)] = ""
                st.rerun()
    with b2:
        if count > 1 and st.button("－ Remove last", key=f"remove_{plan_date}", width="stretch"):
            st.session_state[draft_count_key(plan_date)] = count - 1
            st.rerun()
    if st.button("Save Targets", type="primary", key=f"save_{plan_date}", width="stretch"):
        descriptions = read_draft_targets(plan_date)
        targets = [
            {"description": text, "planned_hours": 0}
            for text in descriptions
            if text
        ]
        if not targets:
            st.error("Add at least one target before saving.")
        elif free_target_cap_reached(len(targets)):
            st.error(
                f"Free plan allows up to {FREE_MAX_TARGETS} targets per day. "
                "Open Settings → Pro to unlock unlimited targets."
            )
        elif has_duplicate_descriptions([t["description"] for t in targets]):
            st.error("Each target must have a unique description.")
        elif run_db(
            lambda: save_daily_targets(plan_date, targets),
            "Could not save targets",
        ) is None:
            pass
        else:
            clear_draft_form(plan_date)
            st.session_state.show_target_form = False
            st.session_state.planning_date = None
            flash(
                f"Saved {len(targets)} target(s) for "
                f"{plan_date.strftime('%d %b %Y')} — stored on this device.",
                toast="Targets saved",
            )
            st.rerun()


def on_target_toggle(item_id):
    checked = st.session_state[f"chk_{item_id}"]
    if run_db(
        lambda: update_target_status(item_id, "Done" if checked else "Pending"),
        "Could not update target",
    ) is not None and checked:
        queue_garden_reward(award_target_done_xp())


def on_target_skip(item_id):
    run_db(
        lambda: update_target_status(item_id, "Skipped"),
        "Could not skip target",
    )


def on_target_unskip(item_id):
    run_db(
        lambda: update_target_status(item_id, "Pending"),
        "Could not restore target",
    )


flush_pending_garden_toasts()
flush_pending_ui_toasts()
show_flash()

now = datetime.now()
today = date.today()
tomorrow = today + timedelta(days=1)
period_key, period_label = period_of_day(now)
try:
    daily_goal = get_daily_study_goal()
    streak = get_study_streak()
    longest_streak = get_longest_streak() if is_pro() else None
    garden_state = get_garden_state(streak)
    garden_state["stage_info"] = effective_garden_stage_index(garden_state["xp"])
    show_harvest_unlocks(today)
except DatabaseError:
    daily_goal = 6.0
    streak = 0
    longest_streak = None
    garden_state = {
        "xp": 0,
        "stage_info": get_stage_info(0),
        "events": pd.DataFrame(),
        "life": {},
        "vitality": {},
    }

garden_award_key = f"garden_session_awarded_{user_id}"
if garden_award_key not in st.session_state:
    xp_before = garden_state["xp"]
    try:
        session_rewards = process_daily_checkin(streak)
        session_rewards += sync_daily_garden_bonuses(today)
        show_garden_rewards(session_rewards, xp_before)
        garden_state = get_garden_state(streak)
        garden_state["stage_info"] = effective_garden_stage_index(garden_state["xp"])
    except DatabaseError as exc:
        st.warning(f"Could not update garden XP right now: {exc}")
    st.session_state[garden_award_key] = True
else:
    xp_before = garden_state["xp"]
    try:
        milestone_rewards = sync_daily_garden_bonuses(today)
        if milestone_rewards:
            show_garden_rewards(milestone_rewards, xp_before)
            garden_state = get_garden_state(streak)
            garden_state["stage_info"] = effective_garden_stage_index(garden_state["xp"])
    except DatabaseError as exc:
        st.warning(f"Could not update garden XP right now: {exc}")

with st.sidebar:
    render_sidebar()

st.markdown(
    f"""
    <div class="app-hero">
        <p class="app-hero-title">📚 Study Tracker</p>
        <p class="app-hero-greeting">{html.escape(greeting(period_key, first_name))}</p>
        <p class="app-hero-motto">{html.escape(period_nudge(period_key))}</p>
        <p class="app-hero-meta">
            {now.strftime("%A, %d %B %Y")} · {now.strftime("%I:%M %p")}
            · <span class="period-badge {PERIOD_BADGES[period_key]}">{period_label}</span>
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

if st.session_state.get("show_welcome"):
    with st.container(border=True):
        st.markdown(f"**Welcome, {first_name}!** Your progress is saved automatically on this device.")
        st.markdown(
            "- **Targets** — plan what you’ll finish today  \n"
            "- **Hours** — log study time (builds your streak)  \n"
            "- **Logbook** — one line on what you studied  \n"
            "- **Garden** — watch consistency turn into growth  \n"
            "- **Backup** — sidebar → *Download full backup*"
        )
        if st.button("Got it — let's study", type="primary", key="dismiss_welcome"):
            st.session_state.show_welcome = False
            st.rerun()

# 2×2 metrics — readable on phone and Android tablet portrait
render_metric_rows(
    [
        [
            ("Study streak", f"{streak} days"),
            ("Daily goal", f"{daily_goal:g} h"),
        ],
        [
            ("Garden XP", f"{garden_state['xp']:,}"),
            (
                "Best streak",
                f"{longest_streak} days"
                if is_pro() and longest_streak is not None
                else "Pro",
            ),
        ],
    ]
)

heatmap_start = today - timedelta(days=400)
try:
    showup_hours = load_showup_hours(heatmap_start, today)
except DatabaseError:
    showup_hours = {}
st.markdown(
    render_github_heatmap(
        showup_hours,
        streak=streak,
        daily_goal=daily_goal,
        display_name=first_name,
    ),
    unsafe_allow_html=True,
)

tab_daily, tab_hours, tab_logbook, tab_garden, tab_break = st.tabs(
    ["📋 Targets", "⏱️ Hours", "📓 Logbook", "🌳 Garden", "☕ Break"]
)

with tab_daily:
    try:
        summary = get_daily_plan_summary(today)
        plan = get_daily_plan(today)
        tomorrow_summary = get_daily_plan_summary(tomorrow)
    except DatabaseError as exc:
        st.error(f"Could not load daily targets: {exc}")
        st.stop()

    if "show_target_form" not in st.session_state:
        st.session_state.show_target_form = False
    if "planning_date" not in st.session_state:
        st.session_state.planning_date = None
    if "tomorrow_prompt_dismissed_date" not in st.session_state:
        st.session_state.tomorrow_prompt_dismissed_date = None
    if "morning_prompt_dismissed_date" not in st.session_state:
        st.session_state.morning_prompt_dismissed_date = None

    if period_key == "morning":
        show_morning_prompt = (
            not summary["has_plan"]
            and not st.session_state.show_target_form
            and st.session_state.morning_prompt_dismissed_date != today.isoformat()
        )
        if show_morning_prompt:
            st.info(f"{greeting('morning', first_name)} You haven't set today's targets yet.")
            if st.button("Yes, set today's targets", type="primary", key="morning_yes", width="stretch"):
                st.session_state.show_target_form = True
                st.session_state.planning_date = today
                init_draft_form(today)
                st.rerun()
            if st.button("Not now", key="morning_no", width="stretch"):
                st.session_state.morning_prompt_dismissed_date = today.isoformat()
                st.rerun()
        elif summary["has_plan"] and not st.session_state.show_target_form:
            st.success(
                f"You have {summary['total_targets']} target(s) for today. "
                "Check them off as you go!"
            )
            if st.button("Replace today's targets", key="morning_replace", width="stretch"):
                st.session_state.show_target_form = True
                st.session_state.planning_date = today
                if plan and plan["items"]:
                    init_draft_form(
                        today,
                        [i["description"] for i in plan["items"]] + [""],
                    )
                else:
                    init_draft_form(today)
                st.rerun()
    else:
        if not summary["has_plan"] and not st.session_state.show_target_form:
            st.warning("No targets set for today yet.")
            if st.button("Set today's targets now", type="primary", key="afternoon_set", width="stretch"):
                st.session_state.show_target_form = True
                st.session_state.planning_date = today
                init_draft_form(today)
                st.rerun()
        elif summary["has_plan"]:
            st.caption("Check off targets throughout the day.")

    if st.session_state.show_target_form and st.session_state.planning_date:
        plan_label = (
            "Set today's targets"
            if st.session_state.planning_date == today
            else f"Set targets for {st.session_state.planning_date.strftime('%A, %d %b')}"
        )
        render_target_form(st.session_state.planning_date, plan_label)
        if st.button("Cancel", key="cancel_form", width="stretch"):
            clear_draft_form(st.session_state.planning_date)
            st.session_state.show_target_form = False
            st.session_state.planning_date = None
            st.rerun()

    if summary["has_plan"]:
        st.subheader("Today's Targets")
        third_metric = (
            ("Skipped", str(summary["skipped"]))
            if summary["skipped"]
            else ("Done %", f"{summary['completion_pct']}%")
        )
        render_metric_rows(
            [
                [("Done", f"{summary['done']}/{summary['total_targets']}"), ("Pending", str(summary["pending"]))],
                [third_metric, ("Resolved", f"{summary['resolved_pct']}%")],
            ]
        )
        st.progress(summary["resolved_pct"] / 100)

        st.markdown("**Check off each target**")
        # Single column: large touch targets on tablets / phones
        for item in plan["items"]:
            render_target_item(item)

        if all_targets_resolved(plan["items"]):
            st.success("All targets resolved for today!")
            show_tomorrow_prompt = (
                not tomorrow_summary["has_plan"]
                and st.session_state.tomorrow_prompt_dismissed_date != today.isoformat()
                and not st.session_state.show_target_form
            )
            if show_tomorrow_prompt:
                st.markdown("**Set targets for tomorrow?**")
                t1, t2 = st.columns(2)
                with t1:
                    if st.button("Yes, plan tomorrow", type="primary", key="tomorrow_yes", width="stretch"):
                        st.session_state.show_target_form = True
                        st.session_state.planning_date = tomorrow
                        init_draft_form(tomorrow)
                        st.rerun()
                with t2:
                    if st.button("Not now", key="tomorrow_no", width="stretch"):
                        st.session_state.tomorrow_prompt_dismissed_date = today.isoformat()
                        st.rerun()
            elif tomorrow_summary["has_plan"]:
                st.info(
                    f"Tomorrow already has {tomorrow_summary['total_targets']} "
                    "target(s) set."
                )

            reflection = (plan.get("evening_reflection") or "") if plan else ""
            if "evening_reflection_input" not in st.session_state:
                st.session_state.evening_reflection_input = reflection
            with st.expander("🌙 Evening reflection", expanded=not reflection):
                st.text_area(
                    "What went well? What will you improve tomorrow?",
                    key="evening_reflection_input",
                    placeholder="Short notes on today's study session...",
                )
                if st.button("Save reflection", key="save_reflection", width="stretch"):
                    if run_db(
                        lambda: save_evening_reflection(
                            today, st.session_state.evening_reflection_input
                        ),
                        "Could not save reflection",
                    ) is not None:
                        flash(
                            "Reflection saved on this device.",
                            toast="Reflection saved",
                        )
                        st.rerun()

    elif not st.session_state.show_target_form:
        st.info("No targets for today. Use the button above to set them.")

with tab_hours:
    try:
        today_hours = get_study_hours_for_date(today)
        week_df = get_week_study_hours(today)
    except DatabaseError as exc:
        st.error(f"Could not load study hours: {exc}")
        st.stop()
    week_total = round(week_df["hours"].sum(), 1)
    goal_progress = min(today_hours / daily_goal, 1.0) if daily_goal else 0

    # Stacked layout: form first, chart below (works on tablet + desktop)
    st.subheader("Study Hours")
    render_metric_rows(
        [
            [
                ("Today", f"{today_hours}h", f"Goal {daily_goal:g}h"),
                ("This week", f"{week_total}h"),
            ],
            [("Goal progress", f"{round(goal_progress * 100)}%")],
        ]
    )
    st.progress(goal_progress)

    st.markdown("**Log study time**")
    with st.form("study_hours_form", clear_on_submit=True):
        log_date = st.date_input("Date", today)
        existing = get_study_hours_for_date(log_date)
        if existing > 0:
            st.caption(
                f"Already logged **{existing}h** for this date — new hours will be "
                "added; notes will be appended if provided."
            )
        hours = st.number_input(
            "Hours studied", min_value=0.25, max_value=16.0, step=0.25, value=2.0
        )
        notes = st.text_input(
            "Notes (optional)",
            placeholder="e.g. Revision + practice questions",
        )
        if st.form_submit_button("Save Hours", type="primary", width="stretch"):
            if run_db(
                lambda: add_daily_study_hours(log_date, hours, notes),
                "Could not log study hours",
            ) is not None:
                queue_garden_reward(award_hours_garden_xp(hours))
                total_after = get_study_hours_for_date(log_date)
                flash(
                    f"Logged {hours}h for {log_date.strftime('%d %b %Y')} "
                    f"(total now **{total_after:g}h**). Saved on this device.",
                    toast=f"Saved · {total_after:g}h total",
                )
                st.rerun()

    try:
        recent = get_recent_study_hours()
    except DatabaseError as exc:
        st.error(f"Could not load recent study hours: {exc}")
        recent = pd.DataFrame()
    if not recent.empty:
        st.markdown("**Recent log**")
        recent = recent.copy()
        recent["log_date"] = pd.to_datetime(recent["log_date"]).dt.strftime("%d %b %Y")
        st.dataframe(
            recent[["log_date", "hours", "notes"]],
            column_config={
                "log_date": "Date",
                "hours": st.column_config.NumberColumn("Hours", format="%.1f h"),
                "notes": "Notes",
            },
            hide_index=True,
            width="stretch",
        )
    else:
        st.caption("No study hours logged yet. Log your first session above.")

    if is_pro():
        st.markdown("**Export data (Pro)**")
        export_frames = get_export_dataframes()
        exp_cols = st.columns(min(2, len(export_frames) or 1))
        for col, (name, frame) in zip(exp_cols, export_frames.items()):
            if frame.empty:
                continue
            with col:
                st.download_button(
                    label=f"{name}.csv",
                    data=frame.to_csv(index=False),
                    file_name=f"{name}.csv",
                    mime="text/csv",
                    key=f"export_{name}",
                    width="stretch",
                )
    else:
        with st.expander("📤 Export data (Pro)", expanded=False):
            render_upgrade_cta("export")

    chart_df = week_df.copy()
    chart_df["label"] = chart_df.apply(
        lambda r: f"{r['day']}<br>{r['log_date'].strftime('%d %b')}",
        axis=1,
    )
    chart_df["goal_met"] = chart_df["hours"] >= daily_goal
    colors = [
        "#48BB78" if r["is_today"] else "#38A169" if r["goal_met"] else "#4299E1"
        for _, r in chart_df.iterrows()
    ]
    fig = px.bar(
        chart_df,
        x="label",
        y="hours",
        text="hours",
        title="Weekly study hours",
        labels={"label": "Day", "hours": "Hours"},
    )
    fig.update_traces(
        marker_color=colors, texttemplate="%{text:.1f}h", textposition="outside"
    )
    fig.add_hline(
        y=daily_goal,
        line_dash="dash",
        line_color="#E53E3E",
        annotation_text=f"Goal ({daily_goal:g}h)",
    )
    fig.update_layout(
        height=360,
        margin=dict(l=12, r=12, t=48, b=16),
        showlegend=False,
        font=dict(size=12),
        dragmode=False,
    )
    fig.update_yaxes(range=[0, max(chart_df["hours"].max() * 1.2, daily_goal * 1.2, 4)])
    st.plotly_chart(
        fig,
        width="stretch",
        config={
            "displayModeBar": False,
            "responsive": True,
            "scrollZoom": False,
        },
    )

with tab_logbook:
    st.markdown(
        '<p class="section-label">Logbook</p>'
        '<p class="section-title">What did you study?</p>',
        unsafe_allow_html=True,
    )
    st.caption("One line is enough — saved on this device (use sidebar backup anytime).")

    try:
        year_stats = get_activity_log_stats(CURRENT_YEAR)
        recent_entries = get_activity_logs(year=CURRENT_YEAR, limit=20)
    except DatabaseError as exc:
        st.error(f"Could not load logbook: {exc}")
        st.stop()

    s1, s2 = st.columns(2)
    s1.metric(f"Days logged ({CURRENT_YEAR})", year_stats["days_logged"])
    s2.metric(f"Entries ({CURRENT_YEAR})", year_stats["total_entries"])

    paper_options = [s for s in LOG_SUBJECTS if s]
    if "logbook_paper" not in st.session_state:
        st.session_state.logbook_paper = paper_options[0] if paper_options else ""

    st.markdown("**Subject**")
    # 2 columns on tablet — easier to tap than 4 skinny chips
    paper_cols = st.columns(2)
    for idx, paper in enumerate(paper_options):
        with paper_cols[idx % 2]:
            short = paper.split(" /")[0][:16] if paper else "Any"
            if st.button(
                short,
                key=f"log_paper_{idx}",
                width="stretch",
                type="primary" if st.session_state.logbook_paper == paper else "secondary",
            ):
                st.session_state.logbook_paper = paper
                st.rerun()

    quick_log = st.text_input(
        "Today's study",
        placeholder="e.g. Read chapter 3 + 10 practice questions",
        key="quick_log_text",
        label_visibility="collapsed",
    )
    save_log = st.button("Log it", type="primary", width="stretch", key="quick_log_save")

    if save_log:
        if not quick_log.strip():
            st.error("Write what you studied.")
        elif run_db(
            lambda: add_activity_log(
                today,
                quick_log,
                st.session_state.logbook_paper,
                None,
            ),
            "Could not save log entry",
        ) is not None:
            st.session_state.pop("quick_log_text", None)
            flash("Logbook entry saved on this device.", toast="Logged!", toast_icon="📓")
            st.rerun()

    st.markdown("**Recent**")
    if recent_entries.empty:
        st.info(f"No entries yet — log what you studied today, {first_name}.")
    else:
        for _, row in recent_entries.iterrows():
            entry_id = int(row["id"])
            entry_date = pd.to_datetime(row["log_date"]).strftime("%d %b")
            subject_label = row["subject"] or "General"
            safe_activity = html.escape(str(row["activity"]))
            safe_subject = html.escape(str(subject_label))
            del_col, body_col = st.columns([0.12, 0.88])
            with del_col:
                if st.button("✕", key=f"del_log_{entry_id}", help="Delete"):
                    if run_db(
                        lambda eid=entry_id: delete_activity_log(eid),
                        "Could not delete entry",
                    ) is not None:
                        st.rerun()
            with body_col:
                st.markdown(
                    f'<div class="log-entry">'
                    f'<div class="log-entry-meta">{entry_date} · {safe_subject}</div>'
                    f'<div class="log-entry-body">{safe_activity}</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )

    with st.expander("More options — date, duration, export, browse"):
        with st.form("activity_log_advanced", clear_on_submit=True):
            adv_date = st.date_input("Date", today, key="logbook_entry_date")
            adv_subject = st.selectbox(
                "Subject",
                LOG_SUBJECTS,
                format_func=lambda s: "— Any —" if not s else s,
                key="logbook_entry_subject",
            )
            adv_activity = st.text_area("Details", key="logbook_entry_activity", height=80)
            adv_duration = st.number_input(
                "Hours (optional)", min_value=0.0, max_value=16.0, step=0.25, value=0.0,
                key="logbook_entry_duration",
            )
            if st.form_submit_button("Save detailed entry", width="stretch"):
                if not adv_activity.strip():
                    st.error("Write what you studied.")
                elif run_db(
                    lambda: add_activity_log(
                        adv_date,
                        adv_activity,
                        adv_subject,
                        adv_duration if adv_duration > 0 else None,
                    ),
                    "Could not save log entry",
                ) is not None:
                    flash(
                        "Detailed logbook entry saved on this device.",
                        toast="Logged!",
                        toast_icon="📓",
                    )
                    st.rerun()

        if is_pro():
            export_frames = get_export_dataframes()
            activity_export = export_frames.get("activity_logs")
            if activity_export is not None and not activity_export.empty:
                st.download_button(
                    label="Download activity_logs.csv",
                    data=activity_export.to_csv(index=False),
                    file_name=f"activity_logs_{CURRENT_YEAR}.csv",
                    mime="text/csv",
                    key="export_logbook_activity_logs",
                    width="stretch",
                )
        else:
            st.caption("Activity log export is included with Pro.")

        browse_mode = st.radio(
            "Browse by", ["Month", "Full year"], horizontal=True, key="logbook_browse_mode"
        )
        if browse_mode == "Month":
            year_col, month_col = st.columns(2)
            view_year = year_col.number_input(
                "Year", min_value=2020, max_value=2035, value=CURRENT_YEAR, key="logbook_year"
            )
            view_month = month_col.selectbox(
                "Month",
                list(range(1, 13)),
                format_func=lambda m: MONTH_NAMES[m - 1],
                index=today.month - 1,
                key="logbook_month",
            )
            entries = get_activity_logs(year=view_year, month=view_month, limit=500)
            st.caption(f"{MONTH_NAMES[view_month - 1]} {view_year} — {len(entries)} entries")
        else:
            view_year = st.number_input(
                "Year", min_value=2020, max_value=2035, value=CURRENT_YEAR, key="logbook_full_year"
            )
            entries = get_activity_logs(year=view_year, limit=2000)
            st.caption(f"All of {view_year} — {len(entries)} entries")
        if not entries.empty:
            st.dataframe(
                entries[["log_date", "subject", "activity"]],
                hide_index=True,
                width="stretch",
            )

with tab_garden:
    st.markdown(
        '<p class="section-label">Study Garden</p>'
        '<p class="section-title">Long prep path — foundation grove + exam sprint</p>',
        unsafe_allow_html=True,
    )
    life = garden_state.get("life") or {}
    st.caption(life.get("hint", "Log hours daily — 4 complete days grow a new tree, 6 days bring fruit."))

    week = life.get("week_days") or []
    if week:
        dots = '<div class="week-dots"><span style="font-size:0.8rem;color:#558B2F;font-weight:600">This week</span>'
        for d in week:
            dots += f'<span class="week-dot {d["status"]}" title="{d["date"]}: {d["hours"]}h"></span>'
        dots += "</div>"
        st.markdown(dots, unsafe_allow_html=True)

    # Shorter map height fits tablet screens; swipe still pans the full world
    render_interactive_garden(garden_state, height=560)

    render_metric_rows(
        [
            [
                (
                    "Trees planted",
                    f"🌳 {life.get('tree_count', 1)} / {life.get('max_trees', 77)}",
                ),
                (
                    "Foundation path",
                    f"{life.get('foundation_trees', 1)} / {life.get('foundation_target', 55)}",
                ),
            ],
            [
                ("Study streak", f"{life.get('goal_streak', streak)} days"),
                ("Growth XP", f"{garden_state.get('xp', 0):,}"),
            ],
        ]
    )

    st.markdown("**Your long prep journey**")
    st.info(
        f"🌳 **Start** — 1 tree. Every **4 complete study days** ({daily_goal:g}h each) plants the next tree.\n\n"
        f"📅 **~55 trees** in the foundation phase (220 days ÷ 4) — drag the map to walk your path.\n\n"
        f"🍎 **6-day streak** — fruit on your trees.\n\n"
        f"🏁 **After the foundation phase** — trees 56–77 are your **3-month exam sprint** grove."
    )

    trees = life.get("trees") or []
    if trees:
        show = trees[-8:] if len(trees) > 8 else trees
        if len(trees) > 8:
            st.caption(f"Showing latest 8 of {len(trees)} trees — drag the map to see all.")
        rows = []
        for tr in show:
            status = "🍎 Fruit" if tr.get("has_fruit") else "🌿 Growing"
            tag = f"#{tr['tree_no']}"
            phase = str(tr.get("phase", "foundation")).title()
            rows.append(
                f"**{tag}** · {phase} · {tr.get('subject', '')} · {status}"
            )
        st.markdown("**Latest trees**\n\n" + "\n\n".join(rows))
    if life.get("days_to_next_tier", 0) > 0:
        st.caption(
            f"{life['days_to_next_tier']} more complete day(s) until "
            f"**{life.get('next_tier_label', 'next tier')}**."
        )

    st.markdown("**How to earn Growth XP**")
    st.info(
        f"🌅 Daily check-in — +{XP_REWARDS['daily_checkin']} XP "
        f"(streak bonus up to +{XP_REWARDS['streak_cap']})\n\n"
        f"⏱️ Study — +{XP_REWARDS['per_hour']} XP/hr · "
        f"🎯 Hit goal — +{XP_REWARDS['daily_goal']} XP\n\n"
        f"✅ Complete target — +{XP_REWARDS['target_done']} XP · "
        f"🏆 All targets — +{XP_REWARDS['all_targets']} XP"
    )

    st.markdown("**Evolution path**")
    badge_html = '<div class="badge-grid">'
    for i, stage in enumerate(GARDEN_STAGES):
        pro_locked = not is_pro() and i > FREE_GARDEN_MAX_STAGE
        if pro_locked:
            earned = False
            css = "badge-locked"
            lock = " 🔒 Pro"
        else:
            earned = garden_state["xp"] >= stage["min_xp"]
            css = "badge-earned" if earned else "badge-locked"
            lock = "" if earned else " 🔒"
        badge_html += (
            f'<span class="badge {css}">{stage["emoji"]} {stage["name"]}{lock}</span>'
        )
    badge_html += "</div>"
    st.markdown(badge_html, unsafe_allow_html=True)

    if not is_pro():
        render_upgrade_cta("garden")

    events = garden_state.get("events")
    if events is not None and not events.empty:
        st.markdown("**Recent growth**")
        feed = events.copy()
        feed["event_date"] = pd.to_datetime(feed["event_date"]).dt.strftime(
            "%d %b %H:%M"
        )
        feed["growth"] = feed.apply(
            lambda r: f"+{int(r['xp_amount'])} XP — {r['message']}", axis=1
        )
        st.dataframe(
            feed[["event_date", "growth"]],
            column_config={"event_date": "When", "growth": "Event"},
            hide_index=True,
            width="stretch",
            height=280,
        )
    else:
        st.caption(
            "Your growth log is empty. Log study hours or complete a target to "
            "start growing your map!"
        )

with tab_break:
    st.markdown(
        '<p class="section-label">Break</p>'
        '<p class="section-title">Five minutes, then back to study</p>',
        unsafe_allow_html=True,
    )

    category = st.segmented_control(
        "Category",
        options=list(GAME_GROUPS.keys()),
        default="Pop",
        key="break_category",
    )
    games_in_cat = GAME_GROUPS[category]
    if st.session_state.get("break_game_pick") not in games_in_cat:
        st.session_state.break_game_pick = games_in_cat[0]

    game_pick = st.segmented_control(
        "Game",
        options=games_in_cat,
        key="break_game_pick",
    )

    if game_pick == "Chess Puzzles":
        st.link_button(
            "Full Lichess site",
            "https://lichess.org/training",
            width="content",
        )

    relax_games.render_break_game(game_pick)