"""Garden gamification — stages and XP rewards."""

GARDEN_STAGES = [
    {"name": "Dormant Seed", "min_xp": 0, "emoji": "🌰"},
    {"name": "Tiny Sprout", "min_xp": 40, "emoji": "🌱"},
    {"name": "Green Seedling", "min_xp": 100, "emoji": "🪴"},
    {"name": "Young Sapling", "min_xp": 200, "emoji": "🌿"},
    {"name": "Growing Tree", "min_xp": 350, "emoji": "🌳"},
    {"name": "Strong Oak", "min_xp": 550, "emoji": "🌲"},
    {"name": "Blooming Tree", "min_xp": 800, "emoji": "🌸"},
    {"name": "Fruit Bearer", "min_xp": 1100, "emoji": "🍎"},
    {"name": "Ancient Wisdom", "min_xp": 1500, "emoji": "✨"},
    {"name": "Sacred Grove", "min_xp": 2000, "emoji": "🏆"},
]

XP_REWARDS = {
    "daily_checkin": 25,
    "per_hour": 30,
    "target_done": 25,
    "all_targets": 100,
    "daily_goal": 75,
    "streak_per_day": 8,
    "streak_cap": 60,
}


def get_stage_info(xp: int) -> dict:
    stage_idx = 0
    for i, stage in enumerate(GARDEN_STAGES):
        if xp >= stage["min_xp"]:
            stage_idx = i
    current = GARDEN_STAGES[stage_idx]
    next_stage = GARDEN_STAGES[stage_idx + 1] if stage_idx + 1 < len(GARDEN_STAGES) else None
    if next_stage:
        span = next_stage["min_xp"] - current["min_xp"]
        progress = (xp - current["min_xp"]) / span if span else 1.0
        xp_to_next = next_stage["min_xp"] - xp
    else:
        progress = 1.0
        xp_to_next = 0
    return {
        "index": stage_idx,
        "current": current,
        "next": next_stage,
        "progress": min(max(progress, 0.0), 1.0),
        "xp_to_next": max(xp_to_next, 0),
        "is_max": next_stage is None,
    }


def effective_stage_info(xp: int, is_pro: bool) -> dict:
    info = get_stage_info(xp)
    if is_pro:
        return info
    capped_idx = min(info["index"], 3)
    if capped_idx == info["index"]:
        return info
    current = GARDEN_STAGES[capped_idx]
    next_stage = GARDEN_STAGES[capped_idx + 1] if capped_idx + 1 < len(GARDEN_STAGES) else None
    if next_stage:
        span = next_stage["min_xp"] - current["min_xp"]
        progress = (xp - current["min_xp"]) / span if span else 1.0
        xp_to_next = next_stage["min_xp"] - xp
    else:
        progress = 1.0
        xp_to_next = 0
    return {
        "index": capped_idx,
        "current": current,
        "next": next_stage,
        "progress": min(max(progress, 0.0), 1.0),
        "xp_to_next": max(xp_to_next, 0),
        "is_max": next_stage is None,
        "free_capped": True,
    }