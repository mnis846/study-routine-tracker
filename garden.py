"""Study Garden — visual growth system and SVG renderer."""

GARDEN_STAGES = [
    {"name": "Dormant Seed", "min_xp": 0, "emoji": "🌰", "sky": "#E8F4FC", "ground": "#8B6914"},
    {"name": "Tiny Sprout", "min_xp": 40, "emoji": "🌱", "sky": "#E0F2FE", "ground": "#7C5E12"},
    {"name": "Green Seedling", "min_xp": 100, "emoji": "🪴", "sky": "#D1FAE5", "ground": "#6B4F0E"},
    {"name": "Young Sapling", "min_xp": 200, "emoji": "🌿", "sky": "#BBF7D0", "ground": "#5D8209"},
    {"name": "Growing Tree", "min_xp": 350, "emoji": "🌳", "sky": "#A7F3D0", "ground": "#4A7C04"},
    {"name": "Strong Oak", "min_xp": 550, "emoji": "🌲", "sky": "#86EFAC", "ground": "#3D6B03"},
    {"name": "Blooming Tree", "min_xp": 800, "emoji": "🌸", "sky": "#FBCFE8", "ground": "#2F5A02"},
    {"name": "Fruit Bearer", "min_xp": 1100, "emoji": "🍎", "sky": "#FDE68A", "ground": "#234A01"},
    {"name": "Ancient Wisdom", "min_xp": 1500, "emoji": "✨", "sky": "#C4B5FD", "ground": "#1A3D01"},
    {"name": "Sacred Grove", "min_xp": 2000, "emoji": "🏆", "sky": "#A5B4FC", "ground": "#0F2D00"},
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
    """Return inline SVG for the garden tree at the given stage."""
    anim = (
        '<animateTransform attributeName="transform" type="rotate" '
        'values="-1 100 170;1 100 170;-1 100 170" dur="4s" repeatCount="indefinite"/>'
        if sway
        else ""
    )
    glow = "filter: drop-shadow(0 0 12px rgba(72,187,120,0.45));" if stage_idx >= 5 else ""

    parts = {
        0: """
            <ellipse cx="100" cy="218" rx="55" ry="10" fill="#5D4037" opacity="0.5"/>
            <ellipse cx="100" cy="210" rx="18" ry="10" fill="#8D6E63"/>
            <ellipse cx="100" cy="205" rx="10" ry="6" fill="#6D4C41"/>
        """,
        1: """
            <rect x="97" y="175" width="6" height="35" rx="3" fill="#558B2F"/>
            <ellipse cx="100" cy="172" rx="14" ry="9" fill="#7CB342"/>
            <ellipse cx="92" cy="178" rx="8" ry="5" fill="#8BC34A"/>
        """,
        2: """
            <rect x="96" y="155" width="8" height="55" rx="4" fill="#558B2F"/>
            <ellipse cx="100" cy="148" rx="22" ry="14" fill="#66BB6A"/>
            <ellipse cx="88" cy="158" rx="12" ry="8" fill="#81C784"/>
            <ellipse cx="112" cy="160" rx="10" ry="7" fill="#81C784"/>
        """,
        3: """
            <rect x="94" y="130" width="12" height="80" rx="5" fill="#6D4C41"/>
            <ellipse cx="100" cy="118" rx="32" ry="22" fill="#43A047"/>
            <ellipse cx="78" cy="132" rx="16" ry="12" fill="#66BB6A"/>
            <ellipse cx="122" cy="128" rx="14" ry="11" fill="#66BB6A"/>
        """,
        4: """
            <rect x="92" y="108" width="16" height="102" rx="6" fill="#5D4037"/>
            <ellipse cx="100" cy="88" rx="42" ry="30" fill="#2E7D32"/>
            <ellipse cx="68" cy="105" rx="20" ry="16" fill="#388E3C"/>
            <ellipse cx="132" cy="100" rx="18" ry="14" fill="#388E3C"/>
            <ellipse cx="100" cy="72" rx="28" ry="18" fill="#43A047"/>
        """,
        5: """
            <rect x="90" y="88" width="20" height="122" rx="7" fill="#4E342E"/>
            <ellipse cx="100" cy="68" rx="52" ry="36" fill="#1B5E20"/>
            <ellipse cx="58" cy="90" rx="24" ry="18" fill="#2E7D32"/>
            <ellipse cx="142" cy="85" rx="22" ry="17" fill="#2E7D32"/>
            <ellipse cx="100" cy="48" rx="36" ry="24" fill="#388E3C"/>
            <ellipse cx="80" cy="62" rx="16" ry="12" fill="#43A047"/>
            <ellipse cx="120" cy="58" rx="15" ry="11" fill="#43A047"/>
        """,
        6: """
            <rect x="88" y="72" width="24" height="138" rx="8" fill="#3E2723"/>
            <ellipse cx="100" cy="52" rx="58" ry="40" fill="#1B5E20"/>
            <ellipse cx="52" cy="78" rx="26" ry="20" fill="#2E7D32"/>
            <ellipse cx="148" cy="72" rx="24" ry="19" fill="#2E7D32"/>
            <circle cx="72" cy="55" r="7" fill="#F48FB1"/>
            <circle cx="88" cy="42" r="6" fill="#F06292"/>
            <circle cx="108" cy="38" r="7" fill="#EC407A"/>
            <circle cx="128" cy="50" r="6" fill="#F48FB1"/>
            <circle cx="115" cy="62" r="5" fill="#F06292"/>
        """,
        7: """
            <rect x="86" y="58" width="28" height="152" rx="9" fill="#3E2723"/>
            <ellipse cx="100" cy="38" rx="62" ry="44" fill="#1B5E20"/>
            <ellipse cx="48" cy="68" rx="28" ry="22" fill="#2E7D32"/>
            <ellipse cx="152" cy="62" rx="26" ry="21" fill="#2E7D32"/>
            <circle cx="70" cy="48" r="9" fill="#E53935"/>
            <circle cx="92" cy="32" r="8" fill="#FB8C00"/>
            <circle cx="112" cy="28" r="9" fill="#E53935"/>
            <circle cx="132" cy="42" r="8" fill="#FDD835"/>
            <circle cx="118" cy="58" r="7" fill="#FB8C00"/>
            <circle cx="85" cy="62" r="7" fill="#FDD835"/>
        """,
        8: """
            <rect x="84" y="42" width="32" height="168" rx="10" fill="#2E1B0E"/>
            <ellipse cx="100" cy="28" rx="68" ry="48" fill="#0D3B1E"/>
            <ellipse cx="42" cy="58" rx="32" ry="25" fill="#1B5E20"/>
            <ellipse cx="158" cy="52" rx="30" ry="24" fill="#1B5E20"/>
            <circle cx="65" cy="35" r="10" fill="#FFD700" opacity="0.9"/>
            <circle cx="95" cy="22" r="9" fill="#FFF59D"/>
            <circle cx="125" cy="30" r="10" fill="#FFD700" opacity="0.9"/>
            <circle cx="140" cy="48" r="8" fill="#FFF59D"/>
            <text x="155" y="30" font-size="14" fill="#FFD700">✦</text>
            <text x="38" y="35" font-size="12" fill="#FFD700">✦</text>
            <text x="168" y="55" font-size="10" fill="#FFF59D">✦</text>
        """,
        9: """
            <rect x="82" y="30" width="36" height="180" rx="11" fill="#1A0F05"/>
            <ellipse cx="100" cy="22" rx="74" ry="52" fill="#052E14"/>
            <ellipse cx="36" cy="50" rx="34" ry="28" fill="#0D3B1E"/>
            <ellipse cx="164" cy="44" rx="32" ry="27" fill="#0D3B1E"/>
            <ellipse cx="100" cy="8" rx="40" ry="20" fill="#1B5E20"/>
            <circle cx="60" cy="28" r="11" fill="#FFD700"/>
            <circle cx="90" cy="14" r="10" fill="#FFF176"/>
            <circle cx="118" cy="12" r="11" fill="#FFD700"/>
            <circle cx="145" cy="28" r="10" fill="#FFF176"/>
            <circle cx="78" cy="42" r="9" fill="#FF8F00"/>
            <circle cx="122" cy="38" r="9" fill="#FF8F00"/>
            <text x="30" y="25" font-size="16" fill="#FFD700">✦</text>
            <text x="172" y="22" font-size="14" fill="#FFD700">✦</text>
            <text x="100" y="6" font-size="18" fill="#FFF59D">👑</text>
            <circle cx="175" cy="70" r="4" fill="#81D4FA"/>
            <circle cx="25" cy="65" r="4" fill="#81D4FA"/>
        """,
    }

    idx = min(stage_idx, 9)
    trunk = parts.get(idx, parts[9])
    sparkles = ""
    if idx >= 7:
        sparkles = """
            <circle cx="30" cy="40" r="2" fill="#FFF9C4"><animate attributeName="opacity" values="0.3;1;0.3" dur="2s" repeatCount="indefinite"/></circle>
            <circle cx="170" cy="35" r="2" fill="#FFF9C4"><animate attributeName="opacity" values="1;0.3;1" dur="2.5s" repeatCount="indefinite"/></circle>
            <circle cx="100" cy="15" r="2" fill="#FFFDE7"><animate attributeName="opacity" values="0.5;1;0.5" dur="1.8s" repeatCount="indefinite"/></circle>
        """

    return f"""
    <svg viewBox="0 0 200 230" width="100%" height="220" style="{glow}">
      <defs>
        <linearGradient id="skyGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="{GARDEN_STAGES[idx]['sky']}"/>
          <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0"/>
        </linearGradient>
      </defs>
      <rect x="0" y="0" width="200" height="230" rx="16" fill="url(#skyGrad)"/>
      <ellipse cx="100" cy="220" rx="80" ry="14" fill="{GARDEN_STAGES[idx]['ground']}" opacity="0.35"/>
      <g transform="translate(0,0)">{anim}{trunk}{sparkles}</g>
    </svg>
    """


def render_garden_card(garden_state, compact=False):
    """Build HTML for the garden widget."""
    info = garden_state["stage_info"]
    stage = info["current"]
    xp = garden_state["xp"]
    pct = int(info["progress"] * 100)

    if info["is_max"]:
        next_line = "Maximum stage reached — you're a legend! 🏆"
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
        </div>
        """

    return f"""
    <div class="garden-hero">
      <div class="garden-visual">{svg}</div>
      <div class="garden-details">
        <div class="garden-stage-title">{stage['emoji']} {stage['name']}</div>
        <div class="garden-xp-total">{xp:,} Growth XP</div>
        <div class="garden-bar"><div class="garden-bar-fill" style="width:{pct}%;background:{bar_color}"></div></div>
        <div class="garden-next">{next_line}</div>
        <div class="garden-hint">🧠 Your tree grows when you study, complete targets & check in daily.</div>
      </div>
    </div>
    """


GARDEN_CSS = """
<style>
    .garden-compact {
        display: flex; align-items: center; gap: 1rem;
        background: linear-gradient(135deg, #F0FFF4 0%, #EBF8FF 100%);
        border: 1px solid #C6F6D5; border-radius: 16px;
        padding: 0.75rem 1.25rem; margin-bottom: 1rem;
        animation: gardenPulse 3s ease-in-out infinite;
    }
    @keyframes gardenPulse {
        0%, 100% { box-shadow: 0 0 0 0 rgba(72,187,120,0); }
        50% { box-shadow: 0 0 20px 2px rgba(72,187,120,0.25); }
    }
    .garden-compact-tree { width: 90px; flex-shrink: 0; }
    .garden-compact-info { flex: 1; }
    .garden-hero {
        display: flex; align-items: center; gap: 2rem;
        background: linear-gradient(135deg, #F0FFF4 0%, #E9D8FD 50%, #EBF8FF 100%);
        border: 2px solid #9AE6B4; border-radius: 20px;
        padding: 1.5rem 2rem; margin-bottom: 1rem;
        animation: gardenPulse 3s ease-in-out infinite;
    }
    .garden-visual { width: 200px; flex-shrink: 0; }
    .garden-details { flex: 1; }
    .garden-stage-title { font-size: 1.5rem; font-weight: 700; color: #22543D; margin-bottom: 0.25rem; }
    .garden-xp, .garden-xp-total { font-size: 1rem; color: #2F855A; font-weight: 600; margin-bottom: 0.5rem; }
    .garden-bar { height: 10px; background: #E2E8F0; border-radius: 999px; overflow: hidden; margin-bottom: 0.5rem; }
    .garden-bar-fill { height: 100%; border-radius: 999px; transition: width 0.6s ease; }
    .garden-next { font-size: 0.95rem; color: #4A5568; margin-bottom: 0.35rem; }
    .garden-hint { font-size: 0.85rem; color: #718096; font-style: italic; }
    .reward-toast { color: #22543D; font-weight: 600; }
    .badge-grid { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem; }
    .badge {
        display: inline-block; padding: 0.35rem 0.75rem; border-radius: 999px;
        font-size: 0.8rem; font-weight: 600;
    }
    .badge-earned { background: #C6F6D5; color: #22543D; }
    .badge-locked { background: #EDF2F7; color: #A0AEC0; }
</style>
"""