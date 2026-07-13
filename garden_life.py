"""Study grove — scales from 1 tree through foundation prep and exam sprint."""

from datetime import date, timedelta

from database import (
    get_daily_study_goal,
    get_setting,
    get_study_hours_for_date,
    get_study_hours_map,
    set_setting,
)

HARVEST_KEY = "last_harvest_tier"

# 220 foundation days → ~55 trees; +90 exam-sprint days → ~22 more
FOUNDATION_DAYS = 220
SPRINT_DAYS = 90
STREAK_DAYS_PER_TREE = 4
FOUNDATION_TREE_TARGET = FOUNDATION_DAYS // STREAK_DAYS_PER_TREE  # 55
MAX_GROVE_TREES = FOUNDATION_TREE_TARGET + (SPRINT_DAYS // STREAK_DAYS_PER_TREE)  # 77
STREAK_LOOKBACK_DAYS = FOUNDATION_DAYS + SPRINT_DAYS + 30

HARVEST_TIERS = (
    {"id": "sprout", "min_days": 0, "emoji": "🌱", "label": "First Tree", "min_trees": 1},
    {"id": "grove", "min_days": 4, "emoji": "🌳", "label": "Second Tree", "min_trees": 2},
    {"id": "fruit", "min_days": 6, "emoji": "🍎", "label": "Fruit Season", "min_trees": 2},
    {"id": "golden", "min_days": 7, "emoji": "🏆", "label": "Golden Grove", "min_trees": 2},
)


def get_goal_streak(today=None):
    """Consecutive complete days (ending today or yesterday)."""
    if today is None:
        today = date.today()
    goal = float(get_daily_study_goal())
    hours_map = get_study_hours_map(today - timedelta(days=STREAK_LOOKBACK_DAYS), today)
    cursor = today
    if hours_map.get(today, 0) < goal:
        cursor = today - timedelta(days=1)
    streak = 0
    while cursor >= today - timedelta(days=STREAK_LOOKBACK_DAYS):
        if hours_map.get(cursor, 0) >= goal:
            streak += 1
            cursor -= timedelta(days=1)
        else:
            break
    return streak


def get_week_goal_days(today=None):
    if today is None:
        today = date.today()
    goal = float(get_daily_study_goal())
    hours_map = get_study_hours_map(today - timedelta(days=6), today)
    days = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        hours = hours_map.get(d, 0)
        if hours >= goal:
            status = "complete"
        elif hours > 0:
            status = "partial"
        else:
            status = "empty"
        days.append({"date": d.isoformat(), "hours": hours, "status": status})
    return days


def unlocked_tree_count(goal_streak):
    """1 tree at start; +1 every 4 complete days, up to full foundation+sprint arc."""
    if goal_streak < STREAK_DAYS_PER_TREE:
        return 1
    return min(MAX_GROVE_TREES, 1 + goal_streak // STREAK_DAYS_PER_TREE)


def _tree_phase(tree_no):
    return "foundation" if tree_no <= FOUNDATION_TREE_TARGET else "sprint"


def _tests_by_no():
    return {}


def _tree_growth(goal_streak, has_sakura, has_fruit):
    if has_sakura:
        return "sakura"
    if has_fruit:
        return "fruiting"
    if goal_streak >= 4:
        return "mature"
    if goal_streak >= 2:
        return "young"
    return "sapling"


def _tree_meta(tree_no, test_row, goal_streak, water, has_fruit):
    """Build metadata for one grove tree (study blocks only — no mock schedule)."""
    phase = _tree_phase(tree_no)
    has_sakura = False
    if phase == "foundation":
        subject = f"Foundation Block {tree_no}"
        topic = (
            f"Study arc · days "
            f"{(tree_no - 1) * STREAK_DAYS_PER_TREE + 1}–{tree_no * STREAK_DAYS_PER_TREE}"
        )
    else:
        block = tree_no - FOUNDATION_TREE_TARGET
        subject = f"Exam Sprint {block}"
        topic = f"Sprint phase · block {block}"

    tree_fruit = has_fruit and not has_sakura

    return {
        "tree_no": tree_no,
        "test_no": None,
        "kind": "block",
        "phase": phase,
        "subject": subject,
        "topic": topic,
        "score": None,
        "has_sakura": has_sakura,
        "has_fruit": tree_fruit,
        "water": round(water, 3),
        "growth": _tree_growth(goal_streak, has_sakura, tree_fruit),
        "slot": tree_no - 1,
    }


def build_study_trees(today=None):
    """Build unlocked trees along the foundation → exam-sprint journey."""
    if today is None:
        today = date.today()

    goal_streak = get_goal_streak(today)
    goal = float(get_daily_study_goal())
    today_hours = float(get_study_hours_for_date(today) or 0)
    water = min(1.0, today_hours / goal) if goal > 0 else 0.0
    has_fruit = goal_streak >= 6
    unlocked = unlocked_tree_count(goal_streak)
    tests = _tests_by_no()
    test_count = len(tests)

    trees = []
    for tree_no in range(1, unlocked + 1):
        test_row = tests.get(tree_no) if tree_no <= test_count else None
        trees.append(_tree_meta(tree_no, test_row, goal_streak, water, has_fruit))

    if unlocked < MAX_GROVE_TREES:
        days_to_next_tree = max(0, unlocked * STREAK_DAYS_PER_TREE - goal_streak)
    else:
        days_to_next_tree = 0

    next_tree = None
    if unlocked < MAX_GROVE_TREES:
        nxt_no = unlocked + 1
        test_row = tests.get(nxt_no) if nxt_no <= test_count else None
        meta = _tree_meta(nxt_no, test_row, goal_streak, water, has_fruit)
        next_tree = {
            "tree_no": nxt_no,
            "test_no": meta["test_no"],
            "subject": meta["subject"],
            "phase": meta["phase"],
            "days_away": days_to_next_tree,
        }

    return trees, unlocked, days_to_next_tree, next_tree


def _harvest_tier(goal_streak):
    tier = HARVEST_TIERS[0]
    for candidate in HARVEST_TIERS:
        if goal_streak >= candidate["min_days"]:
            tier = candidate
    return tier


def sync_garden_life(today=None):
    if today is None:
        today = date.today()

    goal = float(get_daily_study_goal())
    today_hours = float(get_study_hours_for_date(today) or 0)
    goal_streak = get_goal_streak(today)
    week = get_week_goal_days(today)
    complete_this_week = sum(1 for d in week if d["status"] == "complete")

    trees, unlocked, days_to_next_tree, next_tree = build_study_trees(today)
    sakura_count = sum(1 for t in trees if t["has_sakura"])
    foundation_trees = min(unlocked, FOUNDATION_TREE_TARGET)

    life = 28
    for d in week:
        if d["status"] == "complete":
            life += 10
        elif d["status"] == "partial":
            life += 3
    life = min(100, life)

    tier = _harvest_tier(goal_streak)
    goal_met_today = today_hours >= goal
    has_fruit = goal_streak >= 6
    water_pct = int(min(100, (today_hours / goal) * 100)) if goal > 0 else 0

    journey_phase = "foundation" if unlocked <= FOUNDATION_TREE_TARGET else "sprint"
    trees_to_foundation_full = max(0, FOUNDATION_TREE_TARGET - unlocked)

    if goal_met_today:
        mood = "flourishing"
        hint = (
            f"{goal_streak}-day streak · {unlocked}/{MAX_GROVE_TREES} trees planted. "
            f"Foundation path: {foundation_trees}/{FOUNDATION_TREE_TARGET}."
        )
    elif today_hours > 0:
        remaining = max(0, goal - today_hours)
        hint = (
            f"Watering {water_pct}% — {remaining:g}h more today. "
            f"Grove: {unlocked} tree{'s' if unlocked != 1 else ''} "
            f"({foundation_trees}/{FOUNDATION_TREE_TARGET} in foundation phase)."
        )
        mood = "growing"
    elif goal_streak > 0:
        mood = "thirsty"
        hint = "Trees are thirsty — log today before midnight to protect your streak."
    else:
        mood = "resting"
        hint = (
            f"Your long prep journey fits ~{FOUNDATION_TREE_TARGET} trees "
            f"(+{MAX_GROVE_TREES - FOUNDATION_TREE_TARGET} for exam sprint). "
            f"Study {goal:g}h daily — 4 days per new tree."
        )

    if days_to_next_tree > 0 and next_tree:
        hint += f" · {days_to_next_tree}d until tree #{next_tree['tree_no']}."

    next_tier = next((t for t in HARVEST_TIERS if t["min_days"] > goal_streak), None)
    days_to_next_tier = (next_tier["min_days"] - goal_streak) if next_tier else 0

    return {
        "life": life,
        "mood": mood,
        "goal_streak": goal_streak,
        "harvest_tier": tier["id"],
        "harvest_label": tier["label"],
        "harvest_emoji": tier["emoji"],
        "trees": trees,
        "tree_count": len(trees),
        "unlocked_count": unlocked,
        "max_trees": MAX_GROVE_TREES,
        "foundation_target": FOUNDATION_TREE_TARGET,
        "sprint_slots": MAX_GROVE_TREES - FOUNDATION_TREE_TARGET,
        "foundation_trees": foundation_trees,
        "trees_to_foundation_full": trees_to_foundation_full,
        "journey_phase": journey_phase,
        "has_fruit": has_fruit,
        "has_flowers": sakura_count > 0,
        "sakura_count": sakura_count,
        "water_level": min(1.0, today_hours / goal) if goal > 0 else 0.0,
        "water_pct": water_pct,
        "today_hours": today_hours,
        "daily_goal": goal,
        "goal_met": goal_met_today,
        "week_days": week,
        "complete_this_week": complete_this_week,
        "days_to_next_tier": days_to_next_tier,
        "days_to_next_tree": days_to_next_tree,
        "next_tree": next_tree,
        "next_tier_label": next_tier["label"] if next_tier else "Max harvest",
        "hint": hint,
    }


_TIER_ALIASES = {"bloom": "grove"}


def pop_harvest_unlocks(today=None):
    life = sync_garden_life(today)
    prev = _TIER_ALIASES.get(get_setting(HARVEST_KEY, None), get_setting(HARVEST_KEY, None))
    current = life["harvest_tier"]
    if prev is None:
        set_setting(HARVEST_KEY, current)
        return None
    order = {t["id"]: i for i, t in enumerate(HARVEST_TIERS)}
    if order.get(current, 0) <= order.get(prev, 0):
        return None
    set_setting(HARVEST_KEY, current)
    messages = {
        "grove": "4 study days — another tree joins your foundation path! 🌳",
        "fruit": "6-day streak — fruit on your nurtured trees! 🍎",
        "golden": "7 perfect days — golden hour over the whole grove! 🏆",
    }
    return {
        "tier": current,
        "emoji": life["harvest_emoji"],
        "label": life["harvest_label"],
        "message": messages.get(current, f"Grove milestone: {life['harvest_label']}"),
    }