"""
Desktop companion desktop watcher — ULTIMATE evolution form.

A fully-armed Imperial battle station that tracks your cursor planet-wide:
hex-shield shimmer, Star Destroyer escorts, tactical hologram HUD, superlaser
charge arrays, and planetary annihilation sequences on lock / attack.

Kept separate from desktop_companion.py so the multi-coach widget stays intact.
Launch: python deathstar_watcher.py  (or Start Desktop companion Watcher.bat)
"""

from __future__ import annotations

import math
import random
import socket
import subprocess
import sys
import threading
import time
import webbrowser
import tkinter as tk
from datetime import date, datetime
from pathlib import Path

from tracker.paths import PROJECT_ROOT

ROOT = PROJECT_ROOT
APP_URL = "http://localhost:8501"
CHARACTER = "deathstar"
MUTEX_NAME = "Global\\Study.DeathStarWatcher"
_INSTANCE_MUTEX_HANDLE = None

NAG_MIN_SEC = 4 * 60
NAG_MAX_SEC = 7 * 60
CAPTION_MS = 14000
REACTION_FRAMES = 48
ANIMATION_MS = 33
TIMER_STRIP_H = 20
TRANSPARENT = "#010203"

ACTOR_W = 200
ACTOR_H = 248
WANDER_LIMIT = 22
IDLE_FRAMES = 110
IDLE_MIN_SEC = 7
IDLE_MAX_SEC = 13
STAR_LAYERS = 2
STARS_PER_LAYER = 22
NEBULA_COUNT = 3
HULL_SPIN = 0.0045
TIE_COUNT = 3
DESTROYER_COUNT = 1
ION_TURRET_COUNT = 4
CARD = "#0a0f1a"
CARD_BORDER = "#1e3a5f"
TEXT = "#e2e8f0"
TEXT_MUTED = "#64748b"
ACCENT_DEFAULT = "#38bdf8"
FONT = ("Segoe UI", 9)
FONT_SM = ("Segoe UI", 8)
FONT_BOLD = ("Segoe UI", 9, "bold")
FONT_LABEL = ("Segoe UI", 8, "bold")
FONT_HUD = ("Consolas", 7)
FONT_TITLE = ("Segoe UI", 10, "bold")

PROFILE = {
    "style": "ultimate",
    "scale": 1.0,
    "speed": 0.16,
    "bob": 5.0,
    "lean": 0.0,
    "body": "#1e293b",
    "body_2": "#334155",
    "body_3": "#475569",
    "cloak": "#0f172a",
    "head": "#64748b",
    "face": "#cbd5e1",
    "skin": "#94a3b8",
    "boot": "#020617",
    "trim": "#94a3b8",
    "glow": "#22c55e",
    "laser_core": "#ecfccb",
    "laser_hot": "#4ade80",
    "shield": "#38bdf8",
    "imperial_red": "#dc2626",
    "hologram": "#22d3ee",
    "eye": "#bbf7d0",
    "fx": "annihilator",
    "name": "DS-1 Orbital Battle Station",
    "class": "ULTIMATE · MK-X",
}

WATCH_STATES = ("scan", "tracking", "locked", "alert")


def _layout_for(caption_open: bool, line_count: int = 1) -> tuple[int, int, int, int]:
    cap_h = 0 if not caption_open else 44 + line_count * 13
    w = max(ACTOR_W + 72, 272)
    h = cap_h + ACTOR_H + TIMER_STRIP_H + 22
    return w, h, ACTOR_W, ACTOR_H


def _evolution_power(watch_state: str, charge: float, reacting: bool, frame: int) -> float:
    """0 = dormant station · 1 = ULTIMATE annihilator (10-year commercial form)."""
    if reacting:
        return 1.0
    base = {
        "scan": 0.22,
        "tracking": 0.52,
        "locked": 0.72,
        "alert": 0.82,
    }.get(watch_state, 0.2)
    power = base + charge * 0.28 + math.sin(frame * 0.04) * 0.03
    return max(0.0, min(1.0, power))


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    if len(color) != 6:
        return (148, 163, 184)
    return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*(max(0, min(255, int(v))) for v in rgb))


def _mix_color(a: str, b: str, amount: float) -> str:
    ar, ag, ab = _hex_to_rgb(a)
    br, bg, bb = _hex_to_rgb(b)
    return _rgb_to_hex((
        ar + (br - ar) * amount,
        ag + (bg - ag) * amount,
        ab + (bb - ab) * amount,
    ))


def _shift_color(color: str, amount: float) -> str:
    target = "#ffffff" if amount >= 0 else "#000000"
    return _mix_color(color, target, abs(amount))


def _draw_tie_fighter(canvas, x: float, y: float, angle: float, *, scale: float = 1.0, glow: str = "#94a3b8") -> None:
    wing = 11 * scale
    body = 4 * scale
    ca = math.cos(angle)
    sa = math.sin(angle)
    lx, ly = x - ca * wing, y - sa * wing * 0.55
    rx, ry = x + ca * wing, y + sa * wing * 0.55
    canvas.create_oval(lx - wing, ly - wing * 0.42, lx + wing, ly + wing * 0.42, fill="#1e293b", outline=glow, width=1)
    canvas.create_oval(rx - wing, ry - wing * 0.42, rx + wing, ry + wing * 0.42, fill="#1e293b", outline=glow, width=1)
    canvas.create_oval(x - body, y - body, x + body, y + body, fill="#0f172a", outline=glow, width=1)
    cockpit = _mix_color(glow, "#ffffff", 0.45)
    canvas.create_oval(x - body * 0.55, y - body * 0.55, x + body * 0.55, y + body * 0.55, fill=cockpit, outline="")


def _draw_starfield(canvas, stars: list[dict], left: int, top: int, right: int, bottom: int) -> None:
    for star in stars:
        depth = star.get("depth", 1.0)
        twinkle = 0.4 + 0.6 * math.sin(star["phase"] + depth)
        size = star["size"] * twinkle * (0.6 + depth * 0.5)
        drift = star.get("drift", 0.0)
        x = left + (star["x"] + drift) % 1.0 * (right - left)
        y = top + star["y"] * (bottom - top)
        color = _mix_color(star["color"], "#ffffff", twinkle * (0.25 + depth * 0.2))
        canvas.create_oval(x - size, y - size, x + size, y + size, fill=color, outline="")


def _draw_nebula(canvas, blobs: list[dict], left: int, top: int, right: int, bottom: int, frame: int) -> None:
    w, h = right - left, bottom - top
    for blob in blobs:
        pulse = 0.7 + 0.3 * math.sin(frame * blob["speed"] + blob["phase"])
        cx = left + blob["x"] * w
        cy = top + blob["y"] * h
        rx = blob["rx"] * w * pulse
        ry = blob["ry"] * h * pulse
        color = _mix_color(blob["color"], "#ffffff", 0.08)
        canvas.create_oval(cx - rx, cy - ry, cx + rx, cy + ry, fill=color, outline="")


def _draw_hex_grid(canvas, cx: float, cy: float, radius: float, frame: int, power: float, color: str) -> None:
    if power < 0.35:
        return
    hex_r = 11 + power * 4
    rows = int(radius / hex_r) + 1
    shimmer = math.sin(frame * 0.12) * 0.3 + 0.7
    for row in range(-rows, rows + 1):
        for col in range(-rows, rows + 1):
            hx = cx + col * hex_r * 1.75 + (row % 2) * hex_r * 0.875
            hy = cy + row * hex_r * 1.5
            if math.hypot(hx - cx, (hy - cy) * 1.1) > radius * (0.92 + shimmer * 0.06):
                continue
            lit = (int(frame * 0.5) + col + row) % 9 < 2
            edge = _mix_color(color, "#ffffff", (0.35 if lit else 0.12) * power)
            pts = []
            for i in range(6):
                ang = math.pi / 6 + i * math.pi / 3 + frame * 0.008
                pts.extend((hx + math.cos(ang) * hex_r, hy + math.sin(ang) * hex_r * 0.55))
            canvas.create_polygon(*pts, fill="", outline=edge, width=1)


def _draw_star_destroyer(canvas, x: float, y: float, angle: float, scale: float, glow: str, frame: int) -> None:
    ca, sa = math.cos(angle), math.sin(angle)
    length = 34 * scale
    width = 10 * scale
    nose_x, nose_y = x + ca * length, y + sa * length * 0.5
    tail_x, tail_y = x - ca * length * 0.85, y - sa * length * 0.42
    left_x = tail_x - sa * width
    left_y = tail_y + ca * width * 0.5
    right_x = tail_x + sa * width
    right_y = tail_y - ca * width * 0.5
    hull = _mix_color(glow, "#0f172a", 0.55)
    canvas.create_polygon(nose_x, nose_y, left_x, left_y, right_x, right_y, fill=hull, outline=glow, width=1)
    bridge_x = x + ca * length * 0.15
    bridge_y = y + sa * length * 0.08
    canvas.create_oval(bridge_x - 4 * scale, bridge_y - 3 * scale, bridge_x + 4 * scale, bridge_y + 3 * scale, fill="#1e293b", outline=glow)
    if frame % 14 < 7:
        canvas.create_oval(nose_x - 3, nose_y - 2, nose_x + 3, nose_y + 2, fill=_mix_color(glow, "#ffffff", 0.4), outline="")


def _draw_target_planet(canvas, x: float, y: float, radius: float, crack: float, frame: int, power: float) -> None:
    if power < 0.55 or radius <= 0:
        return
    canvas.create_oval(x - radius - 4, y - radius - 4, x + radius + 4, y + radius + 4, fill="", outline=_mix_color(PROFILE["shield"], "#ffffff", 0.2), width=1)
    canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill="#1d4ed8", outline="#60a5fa", width=1)
    canvas.create_oval(x - radius * 0.55, y - radius * 0.45, x - radius * 0.1, y - radius * 0.05, fill="#166534", outline="")
    canvas.create_oval(x + radius * 0.05, y + radius * 0.1, x + radius * 0.5, y + radius * 0.45, fill="#14532d", outline="")
    if crack > 0.05:
        for i in range(int(4 + crack * 8)):
            ang = i * 0.9 + frame * 0.02
            length = radius * (0.4 + crack * 0.9)
            ex = x + math.cos(ang) * length
            ey = y + math.sin(ang) * length * 0.85
            canvas.create_line(x, y, ex, ey, fill=_mix_color("#fbbf24", "#ef4444", crack), width=1 + int(crack * 2))
    if crack > 0.75:
        canvas.create_oval(x - radius * 0.3, y - radius * 0.3, x + radius * 0.3, y + radius * 0.3, fill=_mix_color("#ef4444", "#ffffff", 0.4), outline="")


def _draw_tactical_frame(canvas, left: int, top: int, right: int, bottom: int, power: float, frame: int) -> None:
    if power < 0.55:
        return
    color = _mix_color(PROFILE["hologram"], PROFILE["shield"], power * 0.4)
    corner = 8
    for x1, y1, x2, y2 in (
        (left, top, left + corner, top),
        (left, top, left, top + corner),
        (right, top, right - corner, top),
        (right, top, right, top + corner),
        (left, bottom, left + corner, bottom),
        (left, bottom, left, bottom - corner),
        (right, bottom, right - corner, bottom),
        (right, bottom, right, bottom - corner),
    ):
        canvas.create_line(x1, y1, x2, y2, fill=color, width=2)
    sweep_y = top + 8 + (frame * 2) % (bottom - top - 16)
    canvas.create_line(left + 4, sweep_y, right - 4, sweep_y, fill=_mix_color(color, "#ffffff", 0.15), width=1)


def _draw_hud_readout(canvas, left: int, top: int, power: float, watch_state: str, charge: float, evolution: float) -> None:
    if power < 0.5:
        return
    color = PROFILE["hologram"]
    canvas.create_text(
        left + 4,
        top + 4,
        text=f"EVO {int(evolution * 100)}% · LSR {int(charge * 100)}%",
        anchor="nw",
        fill=color,
        font=FONT_HUD,
    )


def _shaded_oval(canvas, bbox, fill: str, outline: str = "", width: int = 1, glow: str | None = None) -> None:
    x1, y1, x2, y2 = bbox
    if glow:
        canvas.create_oval(x1 - 9, y1 - 9, x2 + 9, y2 + 9, fill="", outline=_mix_color(glow, "#ffffff", 0.36), width=2)
        canvas.create_oval(x1 - 4, y1 - 4, x2 + 4, y2 + 4, fill="", outline=glow, width=1)
    canvas.create_oval(x1, y1, x2, y2, fill=_shift_color(fill, -0.22), outline=outline, width=width)
    inset = max(2, int(min(x2 - x1, y2 - y1) * 0.08))
    canvas.create_oval(x1 + inset, y1 + inset, x2 - inset, y2 - inset, fill=fill, outline="")
    hi = inset * 2
    canvas.create_oval(
        x1 + hi,
        y1 + hi,
        x1 + (x2 - x1) * 0.68,
        y1 + (y2 - y1) * 0.48,
        fill=_shift_color(fill, 0.26),
        outline="",
    )


def _get_global_cursor() -> tuple[int, int]:
    if sys.platform == "win32":
        import ctypes

        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

        pt = POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y
    return (0, 0)


def _angle_lerp(current: float, target: float, amount: float) -> float:
    delta = (target - current + math.pi) % (2 * math.pi) - math.pi
    return current + delta * amount


def _notify(title: str, message: str) -> None:
    try:
        from plyer import notification

        notification.notify(title=title, message=message, app_name="Desktop companion", timeout=10)
    except Exception:
        pass


def _port_in_use(port: int = 8501) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.4)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def _acquire_single_instance() -> bool:
    global _INSTANCE_MUTEX_HANDLE
    if sys.platform != "win32":
        return True
    import ctypes

    kernel32 = ctypes.windll.kernel32
    _INSTANCE_MUTEX_HANDLE = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    return kernel32.GetLastError() != 183


def _ensure_streamlit() -> None:
    if _port_in_use():
        return
    script = ROOT / "scripts" / "start_tracker.ps1"
    if not script.exists():
        return
    subprocess.Popen(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)],
        cwd=str(ROOT),
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )


def _open_app() -> None:
    _ensure_streamlit()
    webbrowser.open(APP_URL)


def _quick_log_hours(hours: float) -> None:
    sys.path.insert(0, str(ROOT))
    try:
        from tracker.coach import get_coach, get_line
        from tracker.database import add_daily_study_hours, init_db

        init_db()
        add_daily_study_hours(date.today(), hours, "Quick log - Desktop companion")
        try:
            from tracker.git_sync import notify_data_changed

            notify_data_changed()
        except Exception:
            pass
        coach = get_coach(CHARACTER)
        _notify(coach["name"], f"Logged {hours:g}h. {get_line(CHARACTER, 'praise')}")
    except Exception as exc:
        _notify("Study Tracker", f"Could not log: {exc}")


def _tray_image():
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, 60, 60], fill=(3, 7, 18, 255))
    for i in range(14):
        x = 4 + (i * 5) % 54
        y = 4 + (i * 7) % 18
        draw.ellipse([x, y, x + 2, y + 2], fill=(56, 189, 248, 160))
    draw.ellipse([8, 16, 56, 56], fill=(30, 41, 59, 255), outline=(56, 189, 248, 200))
    draw.ellipse([20, 26, 44, 48], fill=(15, 23, 42, 255))
    draw.ellipse([26, 28, 40, 38], fill=(34, 197, 94, 255))
    draw.ellipse([28, 40, 36, 48], fill=(220, 38, 38, 255))
    draw.polygon([(32, 8), (28, 18), (36, 18)], fill=(148, 163, 184, 255))
    return img


def _draw_deathstar(
    canvas,
    ox: int,
    oy: int,
    frame: int,
    *,
    mode: str,
    progress: float,
    accent: str,
    look_angle: float,
    watch_state: str,
    cursor_dist: float,
    charge_level: float = 0.0,
    hull_spin: float = 0.0,
    evolution: float = 0.5,
    planet_crack: float = 0.0,
) -> tuple[float, float, float, float]:
    """ULTIMATE battle station — 10-year commercial evolution form."""
    p = PROFILE
    phase = frame * p["speed"]
    evo = evolution
    bob_x = math.sin(phase * 0.7) * (6 + evo * 4)
    bob_y = math.sin(phase) * p["bob"]
    if watch_state == "alert" or mode == "touch":
        bob_x += math.sin(frame * 0.9) * (4 + evo * 3)
        bob_y += math.cos(frame * 1.1) * 3
    cx = ox + ACTOR_W // 2 + bob_x
    cy = oy + 86 + bob_y
    pulse = math.sin(phase * 2.0)
    glow = _mix_color(accent or p["glow"], p["imperial_red"], evo * 0.35 if watch_state == "locked" else evo * 0.12)
    r = 46 + pulse * 2 + evo * 4
    dish_ex = dish_ey = cx

    canvas.create_oval(cx - 42, oy + ACTOR_H - 22, cx + 42, oy + ACTOR_H - 8, fill="#1e293b", outline="")
    for i in range(4):
        radius = 34 + i * 10 + (frame + i * 5) % 10
        ring_color = _mix_color(glow, p["shield"] if i % 2 else p["body_2"], 0.45 - i * 0.06)
        canvas.create_oval(cx - radius, cy - radius // 3, cx + radius, cy + radius // 3, outline=ring_color, width=1)

    _draw_hex_grid(canvas, cx, cy, r + 8 + evo * 10, frame, evo, p["shield"])

    aura = r + 14 + evo * 18
    canvas.create_oval(cx - aura, cy - aura, cx + aura, cy + aura, fill="", outline=_mix_color(glow, p["hologram"], evo * 0.25), width=1)

    _shaded_oval(canvas, (cx - r, cy - r, cx + r, cy + r), p["body"], outline=p["trim"], width=2, glow=glow)

    for band in range(7):
        lat = hull_spin + band * 0.52
        yy = cy - r * 0.76 + band * r * 0.13
        canvas.create_arc(cx - r + 8, yy - 9, cx + r - 8, yy + 9, start=math.degrees(lat) % 360, extent=168, outline=p["body_3"], width=1, style=tk.ARC)
        if (frame + band * 3) % 15 < 4:
            lx = cx + math.cos(lat + band) * r * 0.84
            canvas.create_oval(lx - 2, yy - 2, lx + 2, yy + 2, fill=_mix_color(glow, "#fbbf24", 0.4), outline="")

    for i in range(ION_TURRET_COUNT):
        turret_ang = hull_spin * 1.2 + i * (2 * math.pi / ION_TURRET_COUNT)
        tx = cx + math.cos(turret_ang) * r * 0.88
        ty = cy + math.sin(turret_ang) * r * 0.42
        canvas.create_oval(tx - 5, ty - 4, tx + 5, ty + 4, fill="#0f172a", outline=glow, width=1)
        if watch_state in {"alert", "locked"} and (frame + i) % 11 < 3:
            bx = tx + math.cos(turret_ang) * 22
            by = ty + math.sin(turret_ang) * 10
            canvas.create_line(tx, ty, bx, by, fill=_mix_color(glow, "#ffffff", 0.5), width=2, capstyle=tk.ROUND)

    for i in range(6):
        mer_angle = hull_spin * 1.3 + i * 0.58 - 1.1
        x = cx + math.sin(mer_angle) * r * 0.82
        canvas.create_line(x, cy - r * 0.86, x + math.sin(mer_angle) * 16, cy + r * 0.82, fill=p["boot"], width=1)

    if evo > 0.4:
        for arc_i, (start, extent, col) in enumerate(((12, 148, p["body_2"]), (198, 108, "#0f172a"), (310, 72, p["imperial_red"]))):
            inset = 6 + arc_i * 8
            canvas.create_arc(cx - r + inset, cy - r + inset, cx + r - inset, cy + r - inset, start=start, extent=extent, outline=col, width=2 + arc_i, style=tk.ARC)

    trench_y = cy + r * 0.06
    canvas.create_arc(cx - r * 0.94, trench_y - 18, cx + r * 0.94, trench_y + 18, start=6, extent=168, outline="#020617", width=6)
    for i in range(10):
        tx = cx - r * 0.78 + i * (r * 1.56 / 17)
        lit = (frame + i * 2) % 22 < 7
        canvas.create_oval(tx - 2, trench_y - 2, tx + 2, trench_y + 2, fill="#fbbf24" if lit else "#334155", outline="")

    exhaust_pulse = 0.5 + 0.5 * math.sin(frame * 0.22)
    port_y = cy + r * 0.52
    port_w = 20 + exhaust_pulse * 6 + evo * 4
    canvas.create_oval(cx - port_w, port_y - 10, cx + port_w, port_y + 16, fill="#450a0a", outline="#fca5a5", width=1)
    canvas.create_oval(cx - port_w * 0.6, port_y - 3, cx + port_w * 0.6, port_y + 12, fill=_mix_color("#ef4444", "#fde047", exhaust_pulse), outline="")
    for i in range(3):
        flame_h = 8 + i * 5 + exhaust_pulse * 6 + evo * 4
        canvas.create_polygon(cx - 6 + i * 3, port_y + 12, cx - 14 + i * 6, port_y + 12 + flame_h, cx + 2 + i * 3, port_y + 12, fill=_mix_color("#f97316", "#fef9c3", 0.25 + i * 0.12), outline="")

    dish_r = 17 + evo * 4
    dish_dist = r * 0.58
    dish_cx = cx + math.cos(look_angle) * dish_dist
    dish_cy = cy + math.sin(look_angle) * dish_dist * 0.36
    dish_pulse = 1.0 + charge_level * 0.22 + evo * 0.08
    dish_w, dish_h = dish_r * 1.5 * dish_pulse, dish_r * 1.0 * dish_pulse

    for seg in range(5):
        seg_ang = look_angle + (seg - 3.5) * 0.18
        sx = cx + math.cos(seg_ang) * (dish_dist - 8)
        sy = cy + math.sin(seg_ang) * (dish_dist - 8) * 0.36
        ex = dish_cx + math.cos(seg_ang) * 8
        ey = dish_cy + math.sin(seg_ang) * 5
        canvas.create_line(sx, sy, ex, ey, fill=_mix_color(p["body_2"], glow, charge_level * 0.5), width=2)

    canvas.create_oval(dish_cx - dish_w, dish_cy - dish_h, dish_cx + dish_w, dish_cy + dish_h, fill="#020617", outline=p["trim"], width=2)
    eye_mix = 0.2 + evo * 0.35 + (0.35 if watch_state == "locked" else 0.1)
    eye_glow = _mix_color(glow, "#ffffff", eye_mix + charge_level * 0.3)
    canvas.create_oval(dish_cx - 16, dish_cy - 11, dish_cx + 16, dish_cy + 11, fill=eye_glow, outline="")
    canvas.create_oval(dish_cx - 9, dish_cy - 7, dish_cx + 9, dish_cy + 7, fill=p["laser_core"], outline="")
    canvas.create_oval(dish_cx - 5, dish_cy - 5, dish_cx + 5, dish_cy + 5, fill=glow, outline="")

    if charge_level > 0.04 or evo > 0.6:
        for ring_i in range(4):
            ring_r = 14 + ring_i * 8 + math.sin(frame * 0.35 + ring_i) * 3
            ring_alpha = max(0.0, (charge_level + evo * 0.3) - ring_i * 0.16)
            if ring_alpha <= 0:
                continue
            canvas.create_oval(dish_cx - ring_r, dish_cy - ring_r * 0.65, dish_cx + ring_r, dish_cy + ring_r * 0.65, outline=_mix_color(glow, "#ffffff", ring_alpha * 0.65), width=2)

    beam_len = 0.0
    if watch_state in {"tracking", "locked", "alert"} or mode == "touch":
        beam_len = 72 + min(58, cursor_dist * 0.06) + evo * 22
        if watch_state == "locked":
            beam_len += 34 + math.sin(frame * 0.32) * 10 + charge_level * 24
        elif watch_state == "alert":
            beam_len += 24
        if mode == "touch":
            beam_len = 100 + progress * 70
        beam_w = 5 if watch_state == "locked" or mode == "touch" else 3
        ex = dish_cx + math.cos(look_angle) * beam_len
        ey = dish_cy + math.sin(look_angle) * beam_len * 0.42
        dish_ex, dish_ey = ex, ey

        for layer, (width, col, mix) in enumerate(((beam_w + 18, glow, 0.6), (beam_w + 8, glow, 0.35), (beam_w, p["laser_hot"], 0.0), (max(2, beam_w - 3), p["laser_core"], 0.0))):
            canvas.create_line(dish_cx, dish_cy, ex, ey, fill=_mix_color(col, "#ffffff", mix), width=width, capstyle=tk.ROUND)

        seg = 12
        for step in range(2, int(beam_len // seg)):
            t = step * seg / beam_len
            px = dish_cx + (ex - dish_cx) * t
            py = dish_cy + (ey - dish_cy) * t
            if (frame + step) % 2 == 0:
                sr = 2 + (step % 3) + int(evo * 2)
                canvas.create_oval(px - sr, py - sr, px + sr, py + sr, fill=p["laser_core"], outline="")

        planet_r = 9 + evo * 4
        if watch_state in {"locked", "alert"} or mode == "touch":
            _draw_target_planet(canvas, ex, ey, planet_r, planet_crack if mode != "touch" else min(1.0, progress * 1.4), frame, evo)

        if watch_state == "locked" or mode == "touch":
            lock_r = 16 + math.sin(frame * 0.45) * 4 + evo * 4
            canvas.create_oval(ex - lock_r, ey - lock_r, ex + lock_r, ey + lock_r, outline=glow, width=2)
            canvas.create_line(ex - 22, ey, ex + 22, ey, fill=glow, width=2)
            canvas.create_line(ex, ey - 22, ex, ey + 22, fill=glow, width=2)
            if evo > 0.7:
                canvas.create_text(ex, ey - 14, text="LOCK", fill=glow, font=("Segoe UI", 6, "bold"))

    if watch_state == "scan":
        for sweep_i in range(2):
            sweep = (frame * 0.035 + sweep_i * math.tau / 3) % math.tau
            sx = cx + math.cos(sweep) * (r + 28 + sweep_i * 6)
            sy = cy + math.sin(sweep) * (r * 0.34 + 28)
            canvas.create_line(cx, cy, sx, sy, fill=_mix_color(glow, p["hologram"], 0.15 + sweep_i * 0.12), width=2, dash=(4, 8))

    for tie_i in range(TIE_COUNT):
        orbit = frame * 0.028 + tie_i * (math.tau / TIE_COUNT)
        orbit_r = r + 22 + tie_i * 7
        tx = cx + math.cos(orbit) * orbit_r
        ty = cy + math.sin(orbit) * orbit_r * 0.4
        _draw_tie_fighter(canvas, tx, ty, orbit + math.pi / 2, scale=0.55 + evo * 0.1, glow=p["body_2"])

    for dest_i in range(DESTROYER_COUNT):
        orbit = frame * 0.012 + dest_i * math.pi + 0.6
        orbit_r = r + 48 + dest_i * 16
        dx = cx + math.cos(orbit) * orbit_r
        dy = cy + math.sin(orbit) * orbit_r * 0.38
        _draw_star_destroyer(canvas, dx, dy, orbit + math.pi / 2, 0.5 + evo * 0.15, p["trim"], frame)

    for angle in (phase, phase + 1.4, phase + 2.8, phase + 4.2):
        sx = cx + math.cos(angle) * (52 + evo * 8)
        sy = cy + math.sin(angle) * 16
        canvas.create_rectangle(sx - 4, sy - 4, sx + 4, sy + 4, fill=p["body_3"], outline=glow)

    if mode == "touch":
        blast_x = dish_cx + math.cos(look_angle) * beam_len if beam_len else ox - 60
        blast_y = dish_cy + math.sin(look_angle) * beam_len * 0.42 if beam_len else cy
        for ring_i in range(6):
            br = 24 + progress * (80 + ring_i * 28)
            canvas.create_oval(blast_x - br, blast_y - br, blast_x + br, blast_y + br, outline=_mix_color(glow, "#ef4444", ring_i * 0.12), width=2)
        canvas.create_oval(cx - 90 - progress * 70, cy - 90 - progress * 70, cx + 90 + progress * 70, cy + 90 + progress * 70, outline=_mix_color(glow, "#ffffff", 0.35), width=3)
        canvas.create_text(cx, cy - r - 12, text="FIRED", fill=p["imperial_red"], font=("Segoe UI", 7, "bold"))
        dish_ex, dish_ey = blast_x, blast_y

    if watch_state == "alert":
        for ring_i in range(3):
            ring = 52 + ((frame + ring_i * 5) % 16) * 3
            canvas.create_oval(cx - ring, cy - ring, cx + ring, cy + ring, outline=_mix_color(glow, p["imperial_red"], 0.2 + ring_i * 0.15), width=2)

    return dish_cx, dish_cy, dish_ex, dish_ey


class DeathStarWatcher:
    def __init__(self):
        sys.path.insert(0, str(ROOT))
        from tracker.coach import get_coach, get_line

        self.coach = get_coach(CHARACTER)
        self.current_line = get_line(CHARACTER, "startup")
        self.caption_open = True
        self.drag_x = self.drag_y = 0
        self._dragging = False
        self._click_start = 0.0
        self._last_click = 0.0
        self._reacting = False
        self._reaction_t = 0
        self._frame = 0
        self._wander_x = 0.0
        self._wander_dir = random.choice((-1, 1))
        self._idle_t = 0
        self._idle_kind: str | None = None
        self._next_idle_frame = self._frame + self._idle_delay_frames()
        self._char_rect = (0, 0, 0, 0)
        self._caption_rect = (0, 0, 0, 0)
        self._particles: list[dict] = []
        self._laser_sparks: list[dict] = []
        self._explosion_rings: list[dict] = []
        self._stars = self._make_stars()
        self._nebula = self._make_nebula()
        self._shake_x = 0.0
        self._shake_y = 0.0
        self._charge_level = 0.0
        self._planet_crack = 0.0
        self._evolution = 0.2
        self._hull_spin = 0.0
        self._clock_str = ""
        self._evolution_toast_shown = False
        self._tray_icon = None
        self._close_rect = (0, 0, 0, 0)

        self._cursor_gx = 0
        self._cursor_gy = 0
        self._cursor_speed = 0.0
        self._look_angle = -math.pi / 4
        self._scan_angle = 0.0
        self._watch_state = "scan"
        self._still_ticks = 0
        self._move_ticks = 0
        self._locked_announced = False
        self._last_lock_caption = 0.0

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self._place_corner()

        lines = self._wrap(self.current_line, 42)
        w, h, _, _ = _layout_for(self.caption_open, len(lines))
        self.canvas = tk.Canvas(self.root, bg=TRANSPARENT, highlightthickness=0, bd=0, width=w, height=h)
        self.canvas.pack()

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<Button-2>", self._on_middle_click)
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.root.bind("<Escape>", self._on_escape)
        self.root.configure(bg=TRANSPARENT)
        self.canvas.configure(bg=TRANSPARENT)
        try:
            self.root.attributes("-transparentcolor", TRANSPARENT)
        except tk.TclError:
            pass

        gx, gy = _get_global_cursor()
        self._cursor_gx, self._cursor_gy = gx, gy

        self._refresh_clock()
        self._draw()
        self._keep_topmost()
        self._schedule_nag()
        self._schedule_caption_hide()
        self._schedule_tick()
        self._schedule_animation()

    def _accent(self) -> str:
        return self.coach.get("accent", ACCENT_DEFAULT)

    def shutdown(self, icon=None) -> None:
        if icon is not None:
            self._tray_icon = icon
        try:
            if self._tray_icon is not None:
                self._tray_icon.stop()
        except Exception:
            pass
        try:
            self.root.quit()
            self.root.destroy()
        except Exception:
            pass

    def _request_shutdown(self, icon=None) -> None:
        self.root.after(0, lambda: self.shutdown(icon))

    def _hit_close(self, x: int, y: int) -> bool:
        x1, y1, x2, y2 = self._close_rect
        return x1 <= x <= x2 and y1 <= y <= y2

    def _make_stars(self) -> list[dict]:
        palette = ["#e2e8f0", "#cbd5e1", "#94a3b8", "#64748b", "#f8fafc", "#38bdf8", "#a5b4fc"]
        stars = []
        for layer in range(STAR_LAYERS):
            depth = (layer + 1) / STAR_LAYERS
            for _ in range(STARS_PER_LAYER):
                stars.append(
                    {
                        "x": random.random(),
                        "y": random.random(),
                        "size": random.uniform(0.5, 2.8) * depth,
                        "phase": random.uniform(0, math.tau),
                        "color": random.choice(palette),
                        "depth": depth,
                        "drift": random.uniform(-0.0008, 0.0008) * depth,
                    }
                )
        return stars

    def _make_nebula(self) -> list[dict]:
        colors = ["#1e1b4b", "#312e81", "#0c4a6e", "#134e4a", "#4c1d95", "#1e3a5f"]
        blobs = []
        for _ in range(NEBULA_COUNT):
            blobs.append(
                {
                    "x": random.uniform(0.05, 0.95),
                    "y": random.uniform(0.05, 0.95),
                    "rx": random.uniform(0.12, 0.35),
                    "ry": random.uniform(0.08, 0.25),
                    "phase": random.uniform(0, math.tau),
                    "speed": random.uniform(0.01, 0.03),
                    "color": random.choice(colors),
                }
            )
        return blobs

    def _idle_delay_frames(self) -> int:
        seconds = random.randint(IDLE_MIN_SEC, IDLE_MAX_SEC)
        return max(1, int(seconds * 1000 / ANIMATION_MS))

    def _wrap(self, text: str, width: int) -> list[str]:
        words, lines, line = text.split(), [], []
        for word in words:
            test = " ".join(line + [word])
            if len(test) <= width:
                line.append(word)
            else:
                if line:
                    lines.append(" ".join(line))
                line = [word]
        if line:
            lines.append(" ".join(line))
        return lines[:4]

    def _char_base(self) -> tuple[int, int, int, int, int, int]:
        lines = self._wrap(self.current_line, 42)
        ew, eh, sw, sh = _layout_for(self.caption_open, len(lines))
        cap_h = 52 + len(lines) * 15 if self.caption_open else 0
        ox = (ew - sw) // 2 + int(self._wander_x) + int(self._shake_x)
        oy = cap_h + 8 + int(self._shake_y)
        return ew, eh, sw, sh, ox, oy

    def _screen_center(self) -> tuple[float, float]:
        wx = self.root.winfo_rootx()
        wy = self.root.winfo_rooty()
        _, _, sw, sh, ox, oy = self._char_base()
        return wx + ox + sw / 2, wy + oy + sh / 2 - 20

    def _update_watch(self) -> float:
        gx, gy = _get_global_cursor()
        dx = gx - self._cursor_gx
        dy = gy - self._cursor_gy
        speed = math.hypot(dx, dy)
        self._cursor_speed = self._cursor_speed * 0.55 + speed * 0.45
        self._cursor_gx, self._cursor_gy = gx, gy

        scx, scy = self._screen_center()
        dist = math.hypot(gx - scx, gy - scy)
        target_angle = math.atan2(gy - scy, gx - scx)

        if self._reacting or self._dragging:
            self._watch_state = "alert"
            return dist

        if speed > 28 or self._cursor_speed > 18:
            self._watch_state = "alert"
            self._still_ticks = 0
            self._move_ticks = min(40, self._move_ticks + 3)
        elif speed > 1.5:
            self._watch_state = "tracking"
            self._still_ticks = 0
            self._move_ticks = min(40, self._move_ticks + 1)
        else:
            self._move_ticks = max(0, self._move_ticks - 1)
            self._still_ticks += 1
            if self._still_ticks > 35 and self._move_ticks == 0:
                self._watch_state = "locked"
            elif self._still_ticks > 90 and not self._idle_kind:
                self._watch_state = "scan"
            elif self._move_ticks > 0:
                self._watch_state = "tracking"
            else:
                self._watch_state = "scan"

        if self._watch_state == "scan":
            self._scan_angle += 0.045
            blend = 0.08
            self._look_angle = _angle_lerp(self._look_angle, self._scan_angle, blend)
        else:
            responsiveness = 0.12 + min(0.35, self._cursor_speed * 0.012)
            if self._watch_state == "locked":
                responsiveness = 0.22
            elif self._watch_state == "alert":
                responsiveness = 0.28
            self._look_angle = _angle_lerp(self._look_angle, target_angle, responsiveness)

        if self._watch_state == "locked" and not self._locked_announced:
            now = time.time()
            if now - self._last_lock_caption > 45:
                from tracker.coach import get_line

                self._locked_announced = True
                self._last_lock_caption = now
                self.caption_open = True
                self.current_line = get_line(CHARACTER, "nag")
                self._resize()
                self._schedule_caption_hide()
        elif self._watch_state != "locked":
            self._locked_announced = False

        return dist

    def _timer_top(self) -> int:
        _, _, _, sh, _, oy = self._char_base()
        return oy + sh + 6

    def _refresh_clock(self):
        self._clock_str = datetime.now().strftime("%H:%M")

    def _schedule_tick(self):
        self.root.after(30000, self._on_tick)

    def _on_tick(self):
        self._refresh_clock()
        self._schedule_tick()

    def _schedule_animation(self):
        self.root.after(ANIMATION_MS, self._on_animation_frame)

    def _start_idle(self):
        self._idle_kind = random.choice(("scan", "charge", "patrol", "annihilate", "fleet", "hyperspace"))
        self._idle_t = 0

    def _update_visual_fx(self) -> None:
        for star in self._stars:
            star["phase"] += 0.05 + star.get("depth", 1) * 0.03
            star["drift"] = star.get("drift", 0) + random.uniform(-0.00005, 0.00005)
        self._hull_spin += HULL_SPIN

        self._evolution = _evolution_power(
            self._watch_state, self._charge_level, self._reacting, self._frame
        )

        if self._watch_state == "locked":
            self._charge_level = min(1.0, self._charge_level + 0.028)
            self._planet_crack = min(1.0, self._planet_crack + 0.018)
        elif self._watch_state == "alert":
            self._charge_level = min(0.7, self._charge_level + 0.014)
            self._planet_crack = min(0.6, self._planet_crack + 0.008)
        else:
            self._charge_level = max(0.0, self._charge_level - 0.035)
            self._planet_crack = max(0.0, self._planet_crack - 0.025)

        if self._evolution > 0.85 and not self._evolution_toast_shown and self._watch_state == "locked":
            self._evolution_toast_shown = True
            _notify("ULTIMATE FORM", "Battle station fully operational. Target acquired.")
        elif self._evolution < 0.6:
            self._evolution_toast_shown = False

        shake_target = 0.0
        if self._reacting:
            shake_target = 6.5 * math.sin(self._reaction_t * 0.65) * (0.6 + self._evolution * 0.4)
        elif self._watch_state == "alert":
            shake_target = 3.2 * math.sin(self._frame * 0.85)
        elif self._watch_state == "locked" and self._charge_level > 0.5:
            shake_target = (1.5 + self._charge_level * 2.5) * math.sin(self._frame * 0.5)
        self._shake_x = self._shake_x * 0.6 + shake_target * random.uniform(-1, 1) * 0.4
        self._shake_y = self._shake_y * 0.6 + shake_target * random.uniform(-1, 1) * 0.35

        alive_rings = []
        for ring in self._explosion_rings:
            ring["radius"] += ring["speed"]
            ring["life"] -= 1
            if ring["life"] > 0:
                alive_rings.append(ring)
        self._explosion_rings = alive_rings

        alive_sparks = []
        for spark in self._laser_sparks:
            spark["x"] += spark["vx"]
            spark["y"] += spark["vy"]
            spark["life"] -= 1
            if spark["life"] > 0:
                alive_sparks.append(spark)
        self._laser_sparks = alive_sparks

    def _spawn_laser_sparks(self, x: float, y: float, count: int = 4) -> None:
        glow = self._accent() or PROFILE["glow"]
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(0.8, 2.6)
            self._laser_sparks.append(
                {
                    "x": x,
                    "y": y,
                    "vx": math.cos(angle) * speed,
                    "vy": math.sin(angle) * speed,
                    "life": random.randint(6, 14),
                    "color": random.choice([glow, "#ecfccb", "#ffffff"]),
                    "size": random.randint(1, 3),
                }
            )

    def _spawn_explosion(self, x: float, y: float) -> None:
        glow = self._accent() or PROFILE["glow"]
        for _ in range(6):
            self._explosion_rings.append(
                {
                    "x": x,
                    "y": y,
                    "radius": 6 + random.uniform(0, 12),
                    "speed": random.uniform(3.0, 6.5),
                    "life": random.randint(18, 32),
                    "color": _mix_color(glow, PROFILE["imperial_red"], random.uniform(0.25, 0.65)),
                }
            )
        self._spawn_particles(28, int(x), int(y))
        for _ in range(18):
            self._particles.append(
                {
                    "x": x,
                    "y": y,
                    "vx": random.uniform(-4, 4),
                    "vy": random.uniform(-4, 1),
                    "life": random.randint(12, 26),
                    "color": random.choice(["#f97316", "#fbbf24", glow, "#fef08a"]),
                    "size": random.randint(2, 5),
                }
            )

    def _on_animation_frame(self):
        self._frame += 1
        cursor_dist = self._update_watch()
        self._update_visual_fx()

        if self._reacting:
            self._reaction_t += 1
            if self._reaction_t >= REACTION_FRAMES:
                self._reacting = False
                self._reaction_t = 0
                self._next_idle_frame = self._frame + self._idle_delay_frames()

        if self._idle_kind:
            self._idle_t += 1
            if self._idle_t >= IDLE_FRAMES or self._reacting or self._dragging:
                self._idle_t = 0
                self._idle_kind = None
                self._next_idle_frame = self._frame + self._idle_delay_frames()
        elif (
            not self._reacting
            and not self._dragging
            and self._watch_state == "scan"
            and self._frame >= self._next_idle_frame
        ):
            self._start_idle()

        if not self._dragging and not self._idle_kind and self._watch_state == "scan":
            pace = 0.22
            self._wander_x += self._wander_dir * pace
            if abs(self._wander_x) >= WANDER_LIMIT:
                self._wander_x = max(-WANDER_LIMIT, min(WANDER_LIMIT, self._wander_x))
                self._wander_dir *= -1

        self._cursor_dist = cursor_dist
        if self._watch_state in {"tracking", "locked", "alert"} and self._frame % 4 == 0:
            _, _, sw, sh, ox, oy = self._char_base()
            cx = ox + sw // 2
            cy = oy + sh // 2
            self._spawn_laser_sparks(
                cx + math.cos(self._look_angle) * 80,
                cy + math.sin(self._look_angle) * 36,
                count=2 if self._watch_state == "tracking" else 4,
            )
        self._draw()
        self._schedule_animation()

    def _place_corner(self):
        sw = self.root.winfo_screenwidth()
        lines = self._wrap(self.current_line, 42)
        w, h, _, _ = _layout_for(self.caption_open, len(lines))
        self.root.geometry(f"{w}x{h}+{sw - w - 12}+12")

    def _keep_topmost(self):
        self.root.attributes("-topmost", True)
        self.root.lift()
        self.root.after(4000, self._keep_topmost)

    def _schedule_nag(self):
        self.root.after(random.randint(NAG_MIN_SEC, NAG_MAX_SEC) * 1000, self._do_nag)

    def _do_nag(self):
        from tracker.coach import get_line

        self.current_line = get_line(CHARACTER, "nag")
        self.caption_open = True
        self._reacting = True
        self._reaction_t = 0
        self._idle_kind = None
        self._spawn_particles(10)
        self._resize()
        self._draw()
        _notify(self.coach["name"], self.current_line)
        self._schedule_caption_hide()
        self._schedule_nag()

    def _schedule_caption_hide(self):
        self.root.after(CAPTION_MS, self._hide_caption)

    def _hide_caption(self):
        if self._reacting:
            self.root.after(1200, self._hide_caption)
            return
        self.caption_open = False
        self._resize()
        self._draw()

    def _resize(self):
        sw_screen = self.root.winfo_screenwidth()
        lines = self._wrap(self.current_line, 42)
        w, h, _, _ = _layout_for(self.caption_open, len(lines))
        x, y = self.root.winfo_x(), self.root.winfo_y()
        if x < 0 or x > sw_screen - 50:
            x = sw_screen - w - 12
        if y < 0:
            y = 12
        self.canvas.configure(width=w, height=h)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _hit_character(self, x: int, y: int) -> bool:
        x1, y1, x2, y2 = self._char_rect
        return x1 <= x <= x2 and y1 <= y <= y2

    def _hit_caption(self, x: int, y: int) -> bool:
        if not self.caption_open:
            return False
        x1, y1, x2, y2 = self._caption_rect
        return x1 <= x <= x2 and y1 <= y <= y2

    def _spawn_particles(self, n: int, px: int | None = None, py: int | None = None):
        _, _, sw, sh, ox, oy = self._char_base()
        cx = px if px is not None else ox + sw // 2
        cy = py if py is not None else oy + sh // 3
        palette = [self._accent(), PROFILE["glow"], "#f8fafc", "#cbd5e1"]
        for _ in range(n):
            self._particles.append(
                {
                    "x": cx,
                    "y": cy,
                    "vx": random.uniform(-2.4, 2.4),
                    "vy": random.uniform(-3.2, -0.8),
                    "life": random.randint(10, 22),
                    "color": random.choice(palette),
                    "size": random.randint(2, 4),
                }
            )

    def _trigger_reaction(self, px: int | None = None, py: int | None = None):
        from tracker.coach import get_line

        self._reacting = True
        self._reaction_t = 0
        self._idle_kind = None
        self._charge_level = 1.0
        self._planet_crack = 1.0
        self._evolution = 1.0
        self.caption_open = True
        self.current_line = get_line(CHARACTER, "attack")
        if px is not None and py is not None:
            self._spawn_explosion(px, py)
        else:
            _, _, sw, sh, ox, oy = self._char_base()
            self._spawn_explosion(ox + sw // 2, oy + sh // 2)
        self._resize()
        self._draw()
        self._schedule_caption_hide()

    def _on_press(self, event):
        if self._hit_close(event.x, event.y):
            self._request_shutdown()
            return
        self.drag_x, self.drag_y = event.x, event.y
        self._dragging = False
        self._click_start = time.time()
        if self._hit_character(event.x, event.y):
            self._trigger_reaction(event.x, event.y)

    def _on_middle_click(self, _event):
        self._request_shutdown()

    def _on_escape(self, _event):
        self._request_shutdown()

    def _on_release(self, event):
        was_dragging = self._dragging
        self._dragging = False
        if was_dragging:
            self._spawn_particles(4, event.x, event.y)
            return
        now = time.time()
        if now - self._click_start > 0.4:
            return
        if self._hit_caption(event.x, event.y) and now - self._last_click < 0.45:
            _open_app()
        self._last_click = now

    def _on_drag(self, event):
        if abs(event.x - self.drag_x) > 5 or abs(event.y - self.drag_y) > 5:
            self._dragging = True
        lines = self._wrap(self.current_line, 42)
        w, h, _, _ = _layout_for(self.caption_open, len(lines))
        x = self.root.winfo_x() + event.x - self.drag_x
        y = self.root.winfo_y() + event.y - self.drag_y
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _on_right_click(self, _event):
        from tracker.coach import get_line

        self.current_line = get_line(CHARACTER, "startup")
        self.caption_open = True
        self._reacting = True
        self._reaction_t = 0
        self._idle_kind = None
        self._wander_x = 0
        self._spawn_particles(8)
        self._resize()
        self._draw()
        self._schedule_caption_hide()

    def _draw_card(self, left: int, top: int, right: int, bottom: int):
        c = self.canvas
        accent = self._accent() or PROFILE["hologram"]
        c.create_rectangle(left, top, right, bottom, fill=CARD, outline=CARD_BORDER, width=1)
        corner = 10
        for x1, y1, x2, y2 in (
            (left, top, left + corner, top),
            (left, top, left, top + corner),
            (right, top, right - corner, top),
            (right, top, right, top + corner),
            (left, bottom, left + corner, bottom),
            (left, bottom, left, bottom - corner),
            (right, bottom, right - corner, bottom),
            (right, bottom, right, bottom - corner),
        ):
            c.create_line(x1, y1, x2, y2, fill=accent, width=2)
        c.create_line(left + 8, top + 3, right - 8, top + 3, fill=_mix_color(accent, "#ffffff", 0.12), width=1)

    def _draw_caption(self):
        if not self.caption_open:
            self._caption_rect = (0, 0, 0, 0)
            return
        c = self.canvas
        lines = self._wrap(self.current_line, 40)
        ew, _, _, _, _, _ = self._char_base()
        cx = ew // 2
        accent = self._accent() or PROFILE["hologram"]
        body = "\n".join(lines)

        tw = min(250, max(200, max((len(line) for line in lines), default=18) * 5 + 32))
        th = 40 + len(lines) * 13
        left, top = cx - tw // 2, 4
        right, bottom = cx + tw // 2, top + th

        self._draw_card(left, top, right, bottom)
        c.create_text(left + 10, top + 8, text=self.coach["name"], anchor="nw", fill=accent, font=FONT_LABEL)
        c.create_text(left + 10, top + 22, text=body, anchor="nw", fill=TEXT, font=FONT_SM, width=tw - 20)
        c.create_text(right - 8, bottom - 6, text="dbl-click open", anchor="se", fill=TEXT_MUTED, font=FONT_HUD)
        self._caption_rect = (left, top, right, bottom)

    def _draw_time(self):
        c = self.canvas
        ew, _, _, _, _, _ = self._char_base()
        top = self._timer_top()
        cx = ew // 2
        c.create_text(cx, top + 10, text=self._clock_str, anchor="n", fill=TEXT_MUTED, font=FONT_BOLD)

    def _draw_watch_status(self, ox: int, oy: int, sw: int, sh: int):
        labels = {
            "scan": "scanning",
            "tracking": "tracking",
            "locked": f"locked {int(self._charge_level * 100)}%",
            "alert": "alert!",
        }
        label = labels.get(self._watch_state, "")
        if not label:
            return
        cx = ox + sw // 2
        color = self._accent() or PROFILE["hologram"]
        if self._watch_state == "locked":
            color = _mix_color(PROFILE["glow"], PROFILE["imperial_red"], self._evolution * 0.4)
        elif self._watch_state == "alert":
            color = PROFILE["imperial_red"]
        self.canvas.create_text(cx, oy + sh + 2, text=label, anchor="n", fill=color, font=FONT_HUD)

    def _draw_particles(self):
        alive = []
        for p in self._particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.14
            p["life"] -= 1
            if p["life"] > 0:
                alive.append(p)
                size = p["size"]
                self.canvas.create_oval(
                    p["x"] - size,
                    p["y"] - size,
                    p["x"] + size,
                    p["y"] + size,
                    fill=p["color"],
                    outline="",
                )
        self._particles = alive

    def _draw_laser_sparks(self):
        for spark in self._laser_sparks:
            size = spark["size"]
            self.canvas.create_oval(
                spark["x"] - size,
                spark["y"] - size,
                spark["x"] + size,
                spark["y"] + size,
                fill=spark["color"],
                outline="",
            )

    def _draw_explosion_rings(self):
        for ring in self._explosion_rings:
            r = ring["radius"]
            x, y = ring["x"], ring["y"]
            alpha = ring["life"] / 22
            color = _mix_color(ring["color"], "#ffffff", alpha * 0.35)
            self.canvas.create_oval(x - r, y - r, x + r, y + r, outline=color, width=2)

    def _draw_idle_fx(self, ox: int, oy: int, sw: int, sh: int, mode: str, progress: float):
        if not self._idle_kind:
            return
        c = self.canvas
        color = self._accent() or PROFILE["glow"]
        cx, cy = ox + sw // 2, oy + sh // 2

        if self._idle_kind == "charge":
            for i in range(8):
                ring = 40 + i * 18 + math.sin(self._frame * 0.18 + i) * 8
                c.create_oval(cx - ring, cy - ring, cx + ring, cy + ring, outline=_mix_color(color, "#ffffff", 0.15 + i * 0.08), width=2)
            c.create_text(cx, oy + 12, text="charging", fill=color, font=FONT_HUD)
            return

        if self._idle_kind == "annihilate":
            px = cx + 90 + progress * 40
            py = cy - 10
            _draw_target_planet(c, px, py, 18 + progress * 4, progress, self._frame, 0.9)
            c.create_line(cx - 40, cy, px, py, fill=_mix_color(color, "#ffffff", 0.4), width=4)
            c.create_text(cx, oy + 10, text="strike sim", fill=PROFILE["imperial_red"], font=FONT_HUD)
            return

        if self._idle_kind == "fleet":
            for i in range(DESTROYER_COUNT + 3):
                angle = progress * math.tau * 0.5 + i * 1.3
                dx = cx + math.cos(angle) * (100 + i * 18)
                dy = cy + math.sin(angle) * 42
                if i < DESTROYER_COUNT:
                    _draw_star_destroyer(c, dx, dy, angle, 0.65, color, self._frame)
                else:
                    _draw_tie_fighter(c, dx, dy, angle, scale=0.8, glow=color)
            c.create_text(cx, oy + 10, text="fleet", fill=color, font=FONT_HUD)
            return

        if self._idle_kind == "hyperspace":
            for i in range(14):
                streak_len = 30 + i * 8
                sy = oy + 30 + i * ((sh - 60) / 14)
                sx = ox + 20 + (progress * 0.7 + i * 0.04) % 1.0 * (sw - 40)
                c.create_line(sx, sy, sx + streak_len, sy, fill=_mix_color(color, "#ffffff", 0.35), width=2)
            c.create_text(cx, oy + 10, text="hyperspace", fill=PROFILE["hologram"], font=FONT_HUD)
            return

        if self._idle_kind == "patrol":
            for i in range(8):
                angle = progress * math.tau + i * 0.78
                px = cx + math.cos(angle) * (70 + i * 6)
                py = cy + math.sin(angle) * 34
                c.create_line(cx, cy, px, py, fill=_mix_color(color, "#64748b", 0.35), width=1, dash=(3, 5))
            return

        sweep = (progress * 2) % 1
        x = ox + 20 + sweep * (sw - 40)
        c.create_line(x, oy + 24, x, oy + sh - 40, fill=color, width=2)
        for i in range(7):
            angle = progress * math.tau + i * 0.9
            px = cx + math.cos(angle) * 95
            py = cy + math.sin(angle) * 42
            c.create_oval(px - 3, py - 3, px + 3, py + 3, fill=color, outline="")

    def _draw_reaction_fx(self, ox: int, oy: int, sw: int, sh: int):
        if not self._reacting:
            return
        c = self.canvas
        color = self._accent() or PROFILE["glow"]
        progress = min(1.0, self._reaction_t / max(1, REACTION_FRAMES - 1))
        cx, cy = ox + sw // 2, oy + sh // 2
        radius = 28 + progress * 120

        flash_alpha = max(0.0, 1.0 - progress * 1.2)
        if flash_alpha > 0:
            c.create_rectangle(ox - 16, oy - 16, ox + sw + 16, oy + sh + 16, fill=_mix_color("#ffffff", color, flash_alpha * 0.5), outline="")

        beam_end = ox + sw + 80 + progress * 180
        for width, col in ((14, _mix_color(color, "#ffffff", 0.5)), (8, color), (3, "#ffffff")):
            c.create_rectangle(0, cy - width // 2, beam_end, cy + width // 2, fill=col, outline="")

        for i in range(7):
            r = radius + i * 22
            c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=_mix_color(color, PROFILE["imperial_red"], i * 0.12), width=2)

        if progress > 0.35:
            blast_x = cx + 100 + progress * 60
            _draw_target_planet(c, blast_x, cy - 8, 22, min(1.0, (progress - 0.35) * 1.8), self._frame, 1.0)

        phase_text = "CHARGING" if progress < 0.25 else ("FIRING" if progress < 0.55 else "PLANET DESTROYED")
        c.create_text(cx, cy - radius - 8, text=phase_text, fill=_mix_color(color, PROFILE["imperial_red"], progress * 0.5), font=FONT_HUD)

    def _draw_character(self):
        _, _, sw, sh, ox, oy = self._char_base()
        if self._reacting:
            progress = min(1.0, self._reaction_t / max(1, REACTION_FRAMES - 1))
            mode = "touch"
        elif self._dragging:
            progress = 0.0
            mode = "drag"
        elif self._idle_kind:
            progress = min(1.0, self._idle_t / max(1, IDLE_FRAMES - 1))
            mode = "idle"
        else:
            progress = 0.0
            mode = "walk"

        _draw_deathstar(
            self.canvas,
            ox,
            oy,
            self._frame,
            mode=mode,
            progress=progress,
            accent=self._accent(),
            look_angle=self._look_angle,
            watch_state=self._watch_state,
            cursor_dist=getattr(self, "_cursor_dist", 400),
            charge_level=self._charge_level,
            hull_spin=self._hull_spin,
            evolution=self._evolution,
            planet_crack=self._planet_crack,
        )
        self._char_rect = (ox, oy, ox + sw, oy + sh)
        self._draw_idle_fx(ox, oy, sw, sh, mode, progress)
        self._draw_reaction_fx(ox, oy, sw, sh)

    def _draw_close_button(self, ew: int):
        size = 14
        right, top = ew - 6, 4
        left, bottom = right - size, top + size
        self._close_rect = (left, top, right, bottom)
        c = self.canvas
        c.create_rectangle(left, top, right, bottom, fill="#1e293b", outline="#64748b", width=1)
        c.create_line(left + 3, top + 3, right - 3, bottom - 3, fill="#f87171", width=2)
        c.create_line(right - 3, top + 3, left + 3, bottom - 3, fill="#f87171", width=2)

    def _draw(self):
        self.canvas.delete("all")
        self._draw_caption()
        ew, eh, sw, sh, ox, oy = self._char_base()
        self._draw_close_button(ew)
        field_left, field_top = ox - 6, oy - 4
        field_right, field_bottom = ox + sw + 6, oy + sh + 4
        self.canvas.create_rectangle(field_left, field_top, field_right, field_bottom, fill="#030712", outline="")
        _draw_nebula(self.canvas, self._nebula, field_left, field_top, field_right, field_bottom, self._frame)
        _draw_starfield(self.canvas, self._stars, field_left, field_top, field_right, field_bottom)
        _draw_tactical_frame(self.canvas, field_left, field_top, field_right, field_bottom, self._evolution, self._frame)
        _draw_hud_readout(self.canvas, field_left, field_top, self._evolution, self._watch_state, self._charge_level, self._evolution)
        self._draw_character()
        self._draw_time()
        self._draw_watch_status(ox, oy, sw, sh)
        self._draw_explosion_rings()
        self._draw_laser_sparks()
        self._draw_particles()

    def run(self):
        self.root.mainloop()


def _snap_watcher(watcher: DeathStarWatcher):
    watcher.caption_open = False
    watcher._reacting = False
    watcher._idle_kind = None
    watcher._wander_x = 0
    watcher._place_corner()
    watcher._resize()
    watcher._draw()


def _run_tray(watcher: DeathStarWatcher):
    import pystray

    menu = pystray.Menu(
        pystray.MenuItem("Open tracker", lambda *_: _open_app()),
        pystray.MenuItem("Log 2 hours", lambda *_: _quick_log_hours(2.0)),
        pystray.MenuItem("New line", lambda *_: watcher._on_right_click(None)),
        pystray.MenuItem("Snap top-right", lambda *_: _snap_watcher(watcher)),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit Desktop companion", lambda icon, *_: watcher._request_shutdown(icon)),
    )
    icon = pystray.Icon("death_star", _tray_image(), "Desktop companion — right-click to quit", menu)
    watcher._tray_icon = icon
    icon.run()


def main():
    if not _acquire_single_instance():
        sys.exit(0)
    sys.path.insert(0, str(ROOT))
    try:
        from tracker.git_sync import start_background_sync

        start_background_sync()
    except Exception:
        pass
    watcher = DeathStarWatcher()
    threading.Thread(target=_run_tray, args=(watcher,), daemon=True).start()
    from tracker.coach import get_coach, get_line

    coach = get_coach(CHARACTER)
    _notify(
        f"{coach['emoji']} {PROFILE['class']}",
        f"{coach['name']} online — ULTIMATE evolution active.",
    )
    watcher.run()


if __name__ == "__main__":
    main()