"""Embed stress-relief mini-games and chess puzzles in Streamlit."""

import io
import json
import urllib.request

import chess
import chess.pgn

from tracker.break_games_config import BREAK_GAMES, GAME_GROUPS
from tracker.paths import GAMES_DIR

_PUZZLE_TEMPLATE = GAMES_DIR / "lichess_puzzle.html"

__all__ = ["BREAK_GAMES", "GAME_GROUPS", "embed_game", "render_break_game"]


def fetch_daily_puzzle():
    """Load today's Lichess puzzle server-side (iframe cannot reach the API)."""
    try:
        req = urllib.request.Request(
            "https://lichess.org/api/puzzle/daily",
            headers={"Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except OSError:
        return None

    try:
        game = chess.pgn.read_game(io.StringIO(data["game"]["pgn"]))
        if game is None:
            return None
        board = game.board()
        for i, move in enumerate(game.mainline_moves()):
            if i >= data["puzzle"]["initialPly"]:
                break
            board.push(move)
        puzzle = data["puzzle"]
        return {
            "fen": board.fen(),
            "turn": "white" if board.turn == chess.WHITE else "black",
            "solution": puzzle["solution"],
            "rating": puzzle["rating"],
            "plays": puzzle["plays"],
            "themes": puzzle.get("themes", []),
            "id": puzzle["id"],
        }
    except (ValueError, KeyError, AttributeError):
        return None


def embed_game(filename: str, height: int = 520) -> None:
    import streamlit.components.v1 as components

    path = GAMES_DIR / filename
    html = path.read_text(encoding="utf-8")
    components.html(html, height=height, scrolling=False)


def embed_chess_puzzle(height: int = 600) -> None:
    import streamlit.components.v1 as components

    payload = fetch_daily_puzzle()
    template = _PUZZLE_TEMPLATE.read_text(encoding="utf-8")
    safe_json = json.dumps(payload).replace("</", "<\\/")
    html = template.replace("/*PUZZLE_DATA*/null", safe_json)
    components.html(html, height=height, scrolling=False)


def render_break_game(game_name: str) -> None:
    kind, target, height = BREAK_GAMES[game_name]
    if game_name == "Chess Puzzles":
        embed_chess_puzzle(height=height)
    else:
        embed_game(target, height=height)