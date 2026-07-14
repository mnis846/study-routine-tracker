"""Break-tab game registry (no Streamlit imports — safe to import anywhere)."""

BREAK_GAMES = {
    "Bubble Pop": ("local", "bubble_pop.html", 520),
    "Balloon Pop": ("local", "balloon_pop.html", 520),
    "Star Catch": ("local", "star_catch.html", 520),
    "Space Shooter": ("local", "space_shooter.html", 560),
    "Neon Racer": ("local", "neon_racer.html", 520),
    "Snake": ("local", "snake.html", 500),
    "Breathing": ("local", "breathing.html", 420),
    "Chess Puzzles": ("local", "lichess_puzzle.html", 580),
}

GAME_GROUPS = {
    "Pop": ["Bubble Pop", "Balloon Pop", "Star Catch"],
    "Arcade": ["Space Shooter", "Neon Racer", "Snake"],
    "Calm": ["Breathing"],
    "Chess": ["Chess Puzzles"],
}