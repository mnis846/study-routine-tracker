"""Rewrite flat imports to tracker.* package imports (including indented)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MODS = [
    "app_styles",
    "auth",
    "break_games_config",
    "coach",
    "database",
    "garden_life",
    "garden_map",
    "garden_vitality",
    "garden",
    "git_sync",
    "logbook",
    "pro",
    "profile",
    "relax_games",
    "showup_grid",
    "styles",
    "sync",
    "sticker_sprites",
    "desktop_companion",
    "deathstar_watcher",
]

# Longer names first so garden_life matches before garden
MODS_SORTED = sorted(MODS, key=len, reverse=True)
ALT = "|".join(re.escape(m) for m in MODS_SORTED)

FROM_PAT = re.compile(rf"\bfrom\s+(?!tracker\.)({ALT})\s+import\b")
IMP_PAT = re.compile(rf"(?<!\.)\bimport\s+(?!tracker\.)({ALT})\b(?!\s*\.)")


def rewrite_text(text: str) -> str:
    text = FROM_PAT.sub(r"from tracker.\1 import", text)
    text = IMP_PAT.sub(r"import tracker.\1", text)
    # Fix "import tracker.relax_games" used as relax_games later
    text = text.replace(
        "import tracker.relax_games\n",
        "import tracker.relax_games as relax_games\n",
    )
    return text


def main() -> None:
    paths = list((ROOT / "tracker").glob("*.py"))
    paths += [
        ROOT / "mobile" / "main.py",
        ROOT / "android" / "main.py",
        ROOT / "main.py",
    ]
    for path in paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        new = rewrite_text(text)
        if new != text:
            path.write_text(new, encoding="utf-8")
            print("updated", path.relative_to(ROOT))
        else:
            print("no change", path.relative_to(ROOT))


if __name__ == "__main__":
    main()
