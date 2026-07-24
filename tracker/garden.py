"""Study Garden — year-long jungle map that grows with your prep."""

from tracker.profile import EXAM, FIRST_NAME

GARDEN_STAGES = [
    {"name": "Barren Plot", "min_xp": 0, "emoji": "🏚️", "sky": "#5c5348", "ground": "#3a3228", "biome": "wasteland"},
    {"name": "Ash Soil", "min_xp": 30, "emoji": "🪨", "sky": "#635a4f", "ground": "#40362c", "biome": "wasteland"},
    {"name": "First Sprout", "min_xp": 80, "emoji": "🌱", "sky": "#6a6155", "ground": "#443a30", "biome": "wasteland"},
    {"name": "Scrubland", "min_xp": 150, "emoji": "🌿", "sky": "#6e6558", "ground": "#4a4236", "biome": "scrubland"},
    {"name": "Trail Cleared", "min_xp": 250, "emoji": "🥾", "sky": "#756b5c", "ground": "#504638", "biome": "scrubland"},
    {"name": "Campfire Ring", "min_xp": 400, "emoji": "🔥", "sky": "#7a6f5e", "ground": "#524a3c", "biome": "camp"},
    {"name": "Fence Line", "min_xp": 600, "emoji": "🪵", "sky": "#6d7560", "ground": "#4f5a42", "biome": "camp"},
    {"name": "Small Outpost", "min_xp": 850, "emoji": "🏕️", "sky": "#647060", "ground": "#4a5540", "biome": "outpost"},
    {"name": "Water Tank", "min_xp": 1150, "emoji": "💧", "sky": "#5a6b62", "ground": "#425248", "biome": "outpost"},
    {"name": "Green Patch", "min_xp": 1500, "emoji": "🌳", "sky": "#556854", "ground": "#3d523c", "biome": "green_zone"},
    {"name": "Pine Belt", "min_xp": 1900, "emoji": "🌲", "sky": "#4f6350", "ground": "#364a38", "biome": "green_zone"},
    {"name": "Supply Yard", "min_xp": 2400, "emoji": "📦", "sky": "#4a5e4c", "ground": "#314436", "biome": "green_zone"},
    {"name": "Reinforced Base", "min_xp": 3000, "emoji": "🛡️", "sky": "#455a46", "ground": "#2c3f30", "biome": "reclaimed"},
    {"name": "Berry Thicket", "min_xp": 3700, "emoji": "🫐", "sky": "#3f553f", "ground": "#283a2a", "biome": "reclaimed"},
    {"name": "Overgrown Wall", "min_xp": 4500, "emoji": "🌴", "sky": "#3a5038", "ground": "#243526", "biome": "overgrown"},
    {"name": "Wild Perimeter", "min_xp": 5400, "emoji": "🦌", "sky": "#344a32", "ground": "#1f3020", "biome": "overgrown"},
    {"name": "Reclaimed Sector", "min_xp": 6500, "emoji": "🦜", "sky": "#2e442c", "ground": "#1a2a1a", "biome": "overgrown"},
    {"name": "Apex Haven", "min_xp": 8000, "emoji": "🏆", "sky": "#284028", "ground": "#142214", "biome": "apex_haven"},
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


def get_stage_info(xp):
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


def _tree_svg(stage_idx, sway=True):
    """Compact SVG tree for dashboard cards."""
    anim = (
        '<animateTransform attributeName="transform" type="rotate" '
        'values="-1 100 170;1 100 170;-1 100 170" dur="4s" repeatCount="indefinite"/>'
        if sway
        else ""
    )
    visual_idx = min(stage_idx, 9)
    glow = "filter: drop-shadow(0 0 12px rgba(72,187,120,0.45));" if stage_idx >= 6 else ""

    parts = {
        0: '<ellipse cx="100" cy="210" rx="18" ry="10" fill="#8D6E63"/><ellipse cx="100" cy="205" rx="10" ry="6" fill="#6D4C41"/>',
        1: '<rect x="97" y="175" width="6" height="35" rx="3" fill="#558B2F"/><ellipse cx="100" cy="172" rx="14" ry="9" fill="#7CB342"/>',
        2: '<rect x="96" y="155" width="8" height="55" rx="4" fill="#558B2F"/><ellipse cx="100" cy="148" rx="22" ry="14" fill="#66BB6A"/>',
        3: '<rect x="94" y="130" width="12" height="80" rx="5" fill="#6D4C41"/><ellipse cx="100" cy="118" rx="32" ry="22" fill="#43A047"/>',
        4: '<rect x="92" y="108" width="16" height="102" rx="6" fill="#5D4037"/><ellipse cx="100" cy="88" rx="42" ry="30" fill="#2E7D32"/>',
        5: '<rect x="90" y="88" width="20" height="122" rx="7" fill="#4E342E"/><ellipse cx="100" cy="68" rx="52" ry="36" fill="#1B5E20"/>',
        6: '<rect x="88" y="72" width="24" height="138" rx="8" fill="#3E2723"/><ellipse cx="100" cy="52" rx="58" ry="40" fill="#1B5E20"/><circle cx="88" cy="42" r="6" fill="#F06292"/>',
        7: '<rect x="86" y="58" width="28" height="152" rx="9" fill="#3E2723"/><ellipse cx="100" cy="38" rx="62" ry="44" fill="#1B5E20"/><circle cx="92" cy="32" r="8" fill="#E53935"/>',
        8: '<rect x="84" y="42" width="32" height="168" rx="10" fill="#2E1B0E"/><ellipse cx="100" cy="28" rx="68" ry="48" fill="#0D3B1E"/><circle cx="95" cy="22" r="9" fill="#FFD700"/>',
        9: '<rect x="82" y="30" width="36" height="180" rx="11" fill="#1A0F05"/><ellipse cx="100" cy="22" rx="74" ry="52" fill="#052E14"/><text x="100" y="6" font-size="18" fill="#FFF59D">👑</text>',
    }
    trunk = parts.get(visual_idx, parts[9])
    return f"""
    <svg viewBox="0 0 200 230" width="100%" height="220" style="{glow}">
      <defs><linearGradient id="skyGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="{GARDEN_STAGES[stage_idx]['sky']}"/>
        <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0"/>
      </linearGradient></defs>
      <rect x="0" y="0" width="200" height="230" rx="16" fill="url(#skyGrad)"/>
      <ellipse cx="100" cy="220" rx="80" ry="14" fill="{GARDEN_STAGES[stage_idx]['ground']}" opacity="0.35"/>
      <g>{anim}{trunk}</g>
    </svg>
    """


def render_garden_card(garden_state, compact=False):
    info = garden_state["stage_info"]
    stage = info["current"]
    xp = garden_state["xp"]
    pct = int(info["progress"] * 100)
    if info["is_max"]:
        next_line = f"Apex Haven unlocked — {FIRST_NAME}, you reclaimed the zone! 🏆"
    else:
        next_line = f"{info['xp_to_next']} XP to <b>{info['next']['name']}</b> {info['next']['emoji']}"
    bar_color = "#48BB78" if pct > 50 else "#4299E1"
    svg = _tree_svg(info["index"])
    if compact:
        return f"""
        <div class="garden-compact">
          <div class="garden-compact-tree">{svg}</div>
          <div class="garden-compact-info">
            <div class="garden-stage-title">{stage['emoji']} {stage['name']}</div>
            <div class="garden-xp">{xp:,} XP · {pct}% to next</div>
            <div class="garden-bar"><div class="garden-bar-fill" style="width:{pct}%;background:{bar_color}"></div></div>
          </div>
        </div>"""
    return f"""
    <div class="garden-hero">
      <div class="garden-visual">{svg}</div>
      <div class="garden-details">
        <div class="garden-stage-title">{stage['emoji']} {stage['name']}</div>
        <div class="garden-xp-total">{xp:,} Growth XP</div>
        <div class="garden-bar"><div class="garden-bar-fill" style="width:{pct}%;background:{bar_color}"></div></div>
        <div class="garden-next">{next_line}</div>
        <div class="garden-hint">🌾 {FIRST_NAME}, 55 foundation trees + exam sprint — water daily, +1 tree every 4 days, &gt;60% on tests blooms sakura.</div>
      </div>
    </div>"""


GARDEN_CSS = """
<style>
    .garden-compact {
        display: flex; align-items: center; gap: 1rem;
        background: linear-gradient(135deg, #ecfdf5, #ede9fe);
        border: 1px solid #99f6e4; border-radius: 12px;
        padding: 0.75rem 1.25rem; margin-bottom: 1rem;
    }
    .garden-compact-tree { width: 90px; flex-shrink: 0; }
    .garden-compact-info { flex: 1; }
    .garden-hero {
        display: flex; align-items: center; gap: 2.5rem;
        background: linear-gradient(135deg, #ecfdf5 0%, #f0fdfa 50%, #ede9fe 100%);
        border: 1px solid #99f6e4; border-radius: 14px;
        padding: 1.5rem 2rem; margin-bottom: 1rem;
    }
    .garden-visual { width: 240px; flex-shrink: 0; }
    .garden-details { flex: 1; }
    .garden-stage-title { font-size: 1.5rem; font-weight: 700; color: #22543D; margin-bottom: 0.25rem; }
    .garden-xp, .garden-xp-total { font-size: 1rem; color: #2F855A; font-weight: 600; margin-bottom: 0.5rem; }
    .garden-bar { height: 10px; background: #E2E8F0; border-radius: 999px; overflow: hidden; margin-bottom: 0.5rem; }
    .garden-bar-fill { height: 100%; border-radius: 999px; transition: width 0.6s ease; }
    .garden-next { font-size: 0.95rem; color: #4A5568; margin-bottom: 0.35rem; }
    .garden-hint { font-size: 0.85rem; color: #718096; font-style: italic; }
    .badge-grid { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem; }
    .badge {
        display: inline-block; padding: 0.35rem 0.75rem; border-radius: 999px;
        font-size: 0.8rem; font-weight: 600;
    }
    .badge-earned { background: #ccfbf1; color: #0f766e; }
    .badge-locked { background: #f1f5f9; color: #94a3b8; }
    .garden-map-fullbleed {
        margin-left: -1.5rem; margin-right: -1.5rem;
        width: calc(100% + 3rem); max-width: none;
    }
    @media (min-width: 900px) {
        .garden-map-fullbleed {
            margin-left: calc(-50vw + 50%);
            margin-right: calc(-50vw + 50%);
            width: 100vw;
        }
    }
    .hay-farm-panel {
        background: linear-gradient(180deg, #E3F2FD 0%, #E8F5E9 100%);
        border: 2px solid #A5D6A7; border-radius: 16px;
        padding: 1rem 1.25rem; margin-top: 0.75rem;
    }
    .week-dots { display: flex; gap: 0.5rem; align-items: center; margin: 0.5rem 0; }
    .week-dot {
        width: 14px; height: 14px; border-radius: 50%;
        border: 2px solid #fff; box-shadow: 0 1px 4px rgba(0,0,0,0.12);
    }
    .week-dot.complete { background: #43A047; }
    .week-dot.partial { background: #FDD835; }
    .week-dot.empty { background: #E0E0E0; }
</style>
"""


def render_interactive_garden(garden_state, height=560, **_kwargs):
    """Cinematic study jungle — full-width draggable map (tablet-friendly height)."""
    from tracker.garden_map import render_garden_world

    render_garden_world(garden_state, height=height)
