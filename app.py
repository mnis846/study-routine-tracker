import html
from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from app_styles import APP_CSS
from database import (
    DB_PATH,
    DatabaseError,
    add_daily_study_hours,
    award_hours_garden_xp,
    award_target_done_xp,
    get_daily_plan,
    get_daily_plan_summary,
    get_daily_study_goal,
    get_export_dataframes,
    get_garden_state,
    get_garden_xp,
    get_longest_streak,
    get_next_scheduled_test,
    get_recent_study_hours,
    get_scheduled_tests,
    get_study_hours_for_date,
    get_study_streak,
    get_test_series_progress,
    get_week_study_hours,
    init_db,
    process_daily_checkin,
    save_daily_targets,
    save_evening_reflection,
    seed_sample_tests,
    set_daily_study_goal,
    sync_daily_garden_bonuses,
    update_scheduled_test,
    update_target_status,
)
from garden import GARDEN_CSS, GARDEN_STAGES, XP_REWARDS, get_stage_info, render_garden_card
from pro import (
    FREE_GARDEN_MAX_STAGE,
    FREE_MAX_TARGETS,
    effective_garden_stage_index,
    free_target_cap_reached,
    is_pro,
    render_pro_unlock_panel,
    render_upgrade_cta,
)
from styles import MOBILE_CSS

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


def greeting(period_key):
    return GREETINGS.get(period_key, "Hello!")


def period_nudge(period_key):
    return PERIOD_NUDGES.get(period_key, APP_MOTTO)


st.set_page_config(
    page_title="Study Tracker",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(GARDEN_CSS + APP_CSS + MOBILE_CSS, unsafe_allow_html=True)

MORNING_END_HOUR = 12
EVENING_START_HOUR = 17
PERIOD_BADGES = {
    "morning": "morning-badge",
    "afternoon": "afternoon-badge",
    "evening": "evening-badge",
}


def ensure_db_ready():
    try:
        if not st.session_state.get("schema_ready"):
            init_db()
            st.session_state.schema_ready = True
        if not st.session_state.get("data_seeded"):
            seed_sample_tests()
            st.session_state.data_seeded = True
    except DatabaseError as exc:
        st.error(f"Could not initialize the database: {exc}")
        st.stop()


def run_db(action, error_message="Something went wrong. Please try again."):
    try:
        return action()
    except DatabaseError as exc:
        st.error(f"{error_message} ({exc})")
        return None


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
    st.markdown("### 📚 Study Tracker")
    st.caption(APP_MOTTO)
    st.caption(f"{'⭐ Pro' if is_pro() else 'Free plan'}")
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
    )
    if st.button("Save goal", key="save_goal_main", width="stretch"):
        if run_db(
            lambda: set_daily_study_goal(new_goal),
            "Could not save study goal",
        ) is not None:
            st.success("Daily goal updated!")
            st.rerun()
    st.divider()
    render_pro_unlock_panel()
    st.divider()
    st.markdown("**Data storage**")
    st.caption("Saved locally — persists year-round.")
    st.code(DB_PATH, language=None)


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


def render_mobile_test_editor(df):
    """Simplified per-test editor for small screens."""
    options = {
        int(row["test_no"]): f"#{int(row['test_no'])} — {row['subject']}"
        for _, row in df.iterrows()
    }
    test_no = st.selectbox(
        "Select test",
        options=list(options.keys()),
        format_func=lambda x: options[x],
        key="mobile_test_pick",
    )
    row = df[df["test_no"] == test_no].iloc[0]
    status = st.selectbox(
        "Status",
        ["Not Attempted", "Attempted"],
        index=0 if row["status"] != "Attempted" else 1,
        key="mobile_test_status",
    )
    hours_val = float(row["hours_studied"]) if pd.notna(row["hours_studied"]) else 0.0
    hours_studied = st.number_input(
        "Hours studied", min_value=0.0, step=0.5, value=hours_val, key="mobile_test_hours"
    )
    score_val = float(row["score"]) if pd.notna(row["score"]) else 0.0
    score = st.number_input("Score", min_value=0.0, step=1.0, value=score_val, key="mobile_test_score")
    remarks = st.text_input(
        "Notes",
        value=row["remarks"] if pd.notna(row["remarks"]) else "",
        key="mobile_test_remarks",
    )
    if st.button("Save this test", type="primary", key="mobile_save_test", width="stretch"):
        new_score = float(score) if status == "Attempted" else None
        if status == "Attempted" and new_score <= 0:
            st.error("Enter a score when marked Attempted.")
        elif run_db(
            lambda: update_scheduled_test(
                test_no,
                status=status,
                hours_studied=hours_studied,
                score=new_score,
                remarks=remarks,
            ),
            f"Could not save test #{test_no}",
        ) is not None:
            st.success(f"Test #{test_no} saved!")
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


def validate_test_rows(edit_df):
    errors = []
    for _, row in edit_df.iterrows():
        test_no = int(row["test_no"])
        if row["status"] == "Attempted" and pd.isna(row["score"]):
            errors.append(f"Test #{test_no}: enter a score when marked Attempted.")
    return errors


def test_row_changed(original_df, edited_row):
    test_no = int(edited_row["test_no"])
    original = original_df[original_df["test_no"] == test_no].iloc[0]
    for col in ("status", "hours_studied", "score", "remarks"):
        orig_val = original[col]
        edit_val = edited_row[col]
        if pd.isna(orig_val):
            orig_val = None
        if pd.isna(edit_val):
            edit_val = None
        if orig_val != edit_val:
            return True
    return False


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
            st.success(
                f"Saved {len(targets)} target(s) for "
                f"{plan_date.strftime('%d %b %Y')}!"
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


ensure_db_ready()
flush_pending_garden_toasts()

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
except DatabaseError:
    daily_goal = 6.0
    streak = 0
    longest_streak = None
    garden_state = {"xp": 0, "stage_info": get_stage_info(0), "events": pd.DataFrame()}

if "garden_session_awarded" not in st.session_state:
    xp_before = garden_state["xp"]
    session_rewards = process_daily_checkin(streak)
    session_rewards += sync_daily_garden_bonuses(today)
    show_garden_rewards(session_rewards, xp_before)
    garden_state = get_garden_state(streak)
    garden_state["stage_info"] = effective_garden_stage_index(garden_state["xp"])
    st.session_state.garden_session_awarded = True
else:
    xp_before = garden_state["xp"]
    milestone_rewards = sync_daily_garden_bonuses(today)
    if milestone_rewards:
        show_garden_rewards(milestone_rewards, xp_before)
        garden_state = get_garden_state(streak)
        garden_state["stage_info"] = effective_garden_stage_index(garden_state["xp"])

with st.sidebar:
    render_sidebar()

st.markdown(
    f"""
    <div class="app-hero">
        <p class="app-hero-title">📚 Study Tracker</p>
        <p class="app-hero-greeting">{html.escape(greeting(period_key))}</p>
        <p class="app-hero-motto">{html.escape(period_nudge(period_key))}</p>
        <p class="app-hero-meta">
            {now.strftime("%A, %d %B %Y")} · {now.strftime("%I:%M %p")}
            · <span class="period-badge {PERIOD_BADGES[period_key]}">{period_label}</span>
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Study streak", f"{streak} days")
m2.metric("Daily goal", f"{daily_goal:g} h")
m3.metric("Garden XP", f"{garden_state['xp']:,}")
m4.metric(
    "Best streak",
    f"{longest_streak} days" if is_pro() and longest_streak is not None else "Pro",
)

st.markdown(render_garden_card(garden_state, compact=True), unsafe_allow_html=True)

tab_daily, tab_hours, tab_tests, tab_garden = st.tabs(
    ["📋 Targets", "⏱️ Hours", "📝 Monsoon", "🌳 Garden"]
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
            st.info(f"{greeting('morning')} You haven't set today's targets yet.")
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
        target_cols = st.columns(2)
        for index, item in enumerate(plan["items"]):
            with target_cols[index % 2]:
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
                        st.success("Reflection saved!")
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

    hours_left, hours_right = st.columns([1, 1.8])

    with hours_left:
        st.subheader("Study Hours")
        h1, h2, h3 = st.columns(3)
        h1.metric("Today", f"{today_hours}h", f"Goal {daily_goal:g}h")
        h2.metric("This week", f"{week_total}h")
        h3.metric("Goal progress", f"{round(goal_progress * 100)}%")
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
                    st.success(f"Logged {hours}h for {log_date.strftime('%d %b %Y')}!")
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
            exp_cols = st.columns(len(export_frames) or 1)
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

    with hours_right:
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
            height=480,
            margin=dict(l=20, r=20, t=48, b=20),
            showlegend=False,
            font=dict(size=13),
        )
        fig.update_yaxes(range=[0, max(chart_df["hours"].max() * 1.2, daily_goal * 1.2, 4)])
        st.plotly_chart(fig, width="stretch")

with tab_tests:
    st.subheader("Monsoon Test Series 2026")
    st.caption("Track all 32 tests from Delhi IAS Monsoon Mains Test Series")

    try:
        next_test = get_next_scheduled_test()
        progress = get_test_series_progress()
    except DatabaseError as exc:
        st.error(f"Could not load test series: {exc}")
        st.stop()

    if next_test:
        test_date = pd.to_datetime(next_test["scheduled_date"]).strftime("%d %b %Y")
        days_left = (pd.to_datetime(next_test["scheduled_date"]).date() - today).days
        if days_left > 0:
            countdown = f" · {days_left} day(s) away"
        elif days_left == 0:
            countdown = " · Today!"
        else:
            countdown = " · Overdue"
        safe_subject = html.escape(str(next_test["subject"]))
        safe_type = html.escape(str(next_test["test_type"]))
        safe_topic = html.escape(str(next_test["topic_focus"]))
        st.markdown(
            f"""
        <div class="next-test-card">
            <h3>Next Test</h3>
            <p class="test-title">Test #{int(next_test['test_no'])} — {safe_subject}</p>
            <p class="test-date">{test_date}{countdown} · {safe_type} · {safe_topic}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
    elif progress["total"] > 0:
        st.success(f"All {progress['total']} tests completed! 🎉")
    else:
        st.info("No tests scheduled yet.")

    if not is_pro():
        st.divider()
        render_upgrade_cta("tests")
        st.caption(
            "Pro includes full 32-test Monsoon schedule, hours + score tracking, "
            "trends, and weak-area notes."
        )
    else:
        completion_pct = (
            round(progress["attempted"] / progress["total"] * 100)
            if progress["total"]
            else None
        )
        t1, t2, t3, t4, t5 = st.columns(5)
        t1.metric("Attempted", f"{progress['attempted']}/{progress['total']}")
        t2.metric("Hours studied", f"{progress['total_hours']}h")
        t3.metric("Avg score", f"{progress['avg_score']}" if progress["avg_score"] else "—")
        t4.metric("Completion", f"{completion_pct}%" if completion_pct is not None else "—")
        t5.metric("Remaining", progress["total"] - progress["attempted"])

        tests_chart_col, tests_table_col = st.columns([1, 1.4])

        with tests_chart_col:
            if not progress["scores"].empty:
                chart_df = progress["scores"].copy()
                chart_df["scheduled_date"] = pd.to_datetime(chart_df["scheduled_date"])
                fig = px.line(
                    chart_df,
                    x="test_no",
                    y="score",
                    markers=True,
                    title="Score trend",
                    labels={"test_no": "Test #", "score": "Score"},
                )
                fig.update_layout(height=360, margin=dict(l=20, r=20, t=48, b=20), font=dict(size=13))
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("Score trend will appear after your first attempted test.")

        df = get_scheduled_tests()
        with tests_table_col:
            if df.empty:
                st.caption("Test schedule will appear here once data is seeded.")
            else:
                st.markdown("**Test schedule & results**")
                original_df = df[
                    ["test_no", "subject", "scheduled_date", "status", "hours_studied", "score", "remarks"]
                ]
                edit_df = st.data_editor(
                    original_df,
                    column_config={
                        "test_no": st.column_config.NumberColumn("Test #", disabled=True),
                        "subject": st.column_config.TextColumn("Subject", disabled=True),
                        "scheduled_date": st.column_config.DateColumn("Date", disabled=True),
                        "status": st.column_config.SelectboxColumn(
                            "Status", options=["Not Attempted", "Attempted"]
                        ),
                        "hours_studied": st.column_config.NumberColumn(
                            "Hours Studied", min_value=0, step=0.5
                        ),
                        "score": st.column_config.NumberColumn("Score", min_value=0, step=1),
                        "remarks": st.column_config.TextColumn("Remarks / Weak Areas"),
                    },
                    hide_index=True,
                    width="stretch",
                    height=360,
                    key="tests_editor",
                )

        if not df.empty:
            st.markdown("**Quick update (mobile)**")
            st.caption("Best for phone — update one test at a time.")
            render_mobile_test_editor(df)

            if st.button("Save table results", type="primary", key="save_tests", width="stretch"):
                errors = validate_test_rows(edit_df)
                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    changed = 0
                    for _, row in edit_df.iterrows():
                        if not test_row_changed(original_df, row):
                            continue
                        score = float(row["score"]) if pd.notna(row["score"]) else None
                        if row["status"] == "Not Attempted":
                            score = None
                        hours = (
                            float(row["hours_studied"])
                            if pd.notna(row["hours_studied"])
                            else 0.0
                        )
                        if run_db(
                            lambda r=row, s=score, h=hours: update_scheduled_test(
                                int(r["test_no"]),
                                status=r["status"],
                                hours_studied=h,
                                score=s,
                                remarks=r["remarks"] if pd.notna(r["remarks"]) else "",
                            ),
                            f"Could not save test #{int(row['test_no'])}",
                        ) is None:
                            break
                        changed += 1
                    if changed:
                        st.success(
                            f"Saved {changed} test update(s)."
                            if changed > 1
                            else "Test results saved!"
                        )
                        st.rerun()
                    else:
                        st.info("No changes to save.")

with tab_garden:
    garden_left, garden_right = st.columns([1.1, 1])

    with garden_left:
        st.subheader("🌳 Your Study Garden")
        st.caption("Every study session feeds your tree. Come back daily to watch it grow.")
        st.markdown(render_garden_card(garden_state, compact=False), unsafe_allow_html=True)

        if garden_state["stage_info"].get("free_capped"):
            render_upgrade_cta("garden", compact=True)

        info = garden_state["stage_info"]
        next_label = "MAX 🏆" if info["is_max"] else str(info["xp_to_next"])
        g1, g2, g3, g4 = st.columns(4)
        g1.metric("Growth XP", f"{garden_state['xp']:,}")
        g2.metric("Stage", f"{info['index'] + 1}/{len(GARDEN_STAGES)}")
        g3.metric("Streak", f"{streak} days")
        g4.metric("XP to next", next_label)

    with garden_right:
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
                "start earning XP!"
            )