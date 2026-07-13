"""
Animated study coach widget — Ultimatrix-evolved celestial coaches.

Desktop companion, Jupiter, and Saturn in 50-year ULTIMATE forms: hex shields,
superlaser arrays, magnetospheric storms, ring resonance, orbital escorts,
and fluid rotation / react / idle cycles. Each body stays visually distinct.
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

ROOT = Path(__file__).resolve().parent
APP_URL = "http://localhost:8501"
_INSTANCE_MUTEX_HANDLE = None
NAG_MIN_SEC = 3 * 60
NAG_MAX_SEC = 6 * 60
CAPTION_MS = 14000
REACTION_FRAMES = 36
ANIMATION_MS = 33
TIMER_STRIP_H = 28
TRANSPARENT = "#010203"

ACTOR_W = 248
ACTOR_H = 308
WANDER_LIMIT = 52
IDLE_FRAMES = 56
HULL_SPIN = 0.0048
TIE_ESCORTS = 3
MOON_LAYERS = 4
RING_PARTICLES = 28
IDLE_MIN_SEC = 7
IDLE_MAX_SEC = 14

# Minimal palette
CARD = "#f8fafc"
CARD_BORDER = "#e2e8f0"
TEXT = "#1e293b"
TEXT_MUTED = "#64748b"
ACCENT_DEFAULT = "#6366f1"
FONT = ("Segoe UI", 9)
FONT_SM = ("Segoe UI", 8)
FONT_BOLD = ("Segoe UI", 9, "bold")
FONT_LABEL = ("Segoe UI", 8, "bold")
FONT_HUD = ("Consolas", 7)


CHARACTER_PROFILES = {
    "deathstar": {
        "style": "ultimate_core",
        "evolution": 1.0,
        "class": "ULTIMATE · MK-X",
        "scale": 1.12,
        "speed": 0.2,
        "bob": 7.2,
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
    },
    "jupiter": {
        "style": "ultimate_jupiter",
        "evolution": 1.0,
        "class": "ULTIMATE · STORM KING",
        "scale": 1.0,
        "speed": 0.17,
        "bob": 6.2,
        "lean": 0.0,
        "body": "#c9a66b",
        "body_2": "#8b5e34",
        "body_3": "#e8d4a8",
        "band_dark": "#5c3317",
        "band_mid": "#b87333",
        "band_light": "#edd9b5",
        "band_storm": "#7c4a2d",
        "spot": "#c44d34",
        "spot_core": "#7f1d1d",
        "aurora": "#a78bfa",
        "trim": "#5c3d1e",
        "glow": "#f59e0b",
        "hologram": "#fbbf24",
        "shield": "#fb923c",
        "fx": "storm_burst",
    },
    "saturn": {
        "style": "ultimate_saturn",
        "evolution": 1.0,
        "class": "ULTIMATE · RING LORD",
        "scale": 1.0,
        "speed": 0.15,
        "bob": 5.5,
        "lean": 0.0,
        "body": "#e8d4a8",
        "body_2": "#d4bc82",
        "body_3": "#c9ad72",
        "band_light": "#f0e2c4",
        "band_soft": "#c4a86a",
        "ring_outer": "#d4c4a8",
        "ring_inner": "#a89878",
        "ring_bright": "#e8dcc8",
        "ring_shadow": "#5a5040",
        "ring_gap": "#1a1814",
        "hex_storm": "#d4a574",
        "trim": "#8a7a5c",
        "glow": "#fde68a",
        "hologram": "#fef3c7",
        "shield": "#f5deb3",
        "fx": "ring_pulse",
    },
}


def _layout_for(character: str, caption_open: bool, line_count: int = 1) -> tuple[int, int, int, int]:
    sw, sh = image_pixel_size(character)
    cap_h = 0 if not caption_open else 52 + line_count * 15
    w = max(sw + 178, 398)
    h = cap_h + sh + TIMER_STRIP_H + 34
    return w, h, sw, sh


def image_pixel_size(_character: str) -> tuple[int, int]:
    return ACTOR_W, ACTOR_H


def _profile(character: str) -> dict:
    base = CHARACTER_PROFILES.get(character) or CHARACTER_PROFILES["deathstar"]
    return dict(base)


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    if len(color) != 6:
        return (99, 102, 241)
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


def _evolution_power(watch_state: str, charge: float, reacting: bool, frame: int, base: float = 1.0) -> float:
    if reacting:
        return 1.0
    tier = {
        "patrol": 0.28,
        "scan": 0.38,
        "tracking": 0.58,
        "locked": 0.78,
        "alert": 0.88,
    }.get(watch_state, 0.25)
    power = base * (tier + charge * 0.22 + math.sin(frame * 0.04) * 0.04)
    return max(0.0, min(1.0, power))


def _draw_hex_grid(canvas, cx: float, cy: float, radius: float, frame: int, power: float, color: str) -> None:
    if power < 0.3:
        return
    hex_r = 9 + power * 3
    rows = int(radius / hex_r) + 1
    shimmer = math.sin(frame * 0.12) * 0.3 + 0.7
    for row in range(-rows, rows + 1):
        for col in range(-rows, rows + 1):
            hx = cx + col * hex_r * 1.75 + (row % 2) * hex_r * 0.875
            hy = cy + row * hex_r * 1.5
            if math.hypot(hx - cx, (hy - cy) * 1.1) > radius * (0.9 + shimmer * 0.06):
                continue
            lit = (int(frame * 0.5) + col + row) % 9 < 2
            edge = _mix_color(color, "#ffffff", (0.35 if lit else 0.1) * power)
            pts = []
            for i in range(6):
                ang = math.pi / 6 + i * math.pi / 3 + frame * 0.008
                pts.extend((hx + math.cos(ang) * hex_r, hy + math.sin(ang) * hex_r * 0.55))
            canvas.create_polygon(*pts, fill="", outline=edge, width=1)


def _draw_tie_fighter(canvas, x: float, y: float, angle: float, *, scale: float = 1.0, glow: str = "#94a3b8") -> None:
    wing = 9 * scale
    body = 3.5 * scale
    ca, sa = math.cos(angle), math.sin(angle)
    lx, ly = x - ca * wing, y - sa * wing * 0.55
    rx, ry = x + ca * wing, y + sa * wing * 0.55
    canvas.create_oval(lx - wing, ly - wing * 0.42, lx + wing, ly + wing * 0.42, fill="#1e293b", outline=glow, width=1)
    canvas.create_oval(rx - wing, ry - wing * 0.42, rx + wing, ry + wing * 0.42, fill="#1e293b", outline=glow, width=1)
    canvas.create_oval(x - body, y - body, x + body, y + body, fill="#0f172a", outline=glow, width=1)
    cockpit = _mix_color(glow, "#ffffff", 0.45)
    canvas.create_oval(x - body * 0.55, y - body * 0.55, x + body * 0.55, y + body * 0.55, fill=cockpit, outline="")


def _draw_star_destroyer(canvas, x: float, y: float, angle: float, scale: float, glow: str, frame: int) -> None:
    ca, sa = math.cos(angle), math.sin(angle)
    length = 28 * scale
    width = 8 * scale
    nose_x, nose_y = x + ca * length, y + sa * length * 0.5
    tail_x, tail_y = x - ca * length * 0.85, y - sa * length * 0.42
    left_x, left_y = tail_x - sa * width, tail_y + ca * width * 0.5
    right_x, right_y = tail_x + sa * width, tail_y - ca * width * 0.5
    hull = _mix_color(glow, "#0f172a", 0.55)
    canvas.create_polygon(nose_x, nose_y, left_x, left_y, right_x, right_y, fill=hull, outline=glow, width=1)
    bridge_x = x + ca * length * 0.15
    bridge_y = y + sa * length * 0.08
    canvas.create_oval(bridge_x - 3 * scale, bridge_y - 2.5 * scale, bridge_x + 3 * scale, bridge_y + 2.5 * scale, fill="#1e293b", outline=glow)
    if frame % 14 < 7:
        canvas.create_oval(nose_x - 2, nose_y - 2, nose_x + 2, nose_y + 2, fill=_mix_color(glow, "#ffffff", 0.4), outline="")


def _draw_target_planet(canvas, x: float, y: float, radius: float, crack: float, frame: int, power: float) -> None:
    if power < 0.45 or radius <= 0:
        return
    canvas.create_oval(x - radius - 3, y - radius - 3, x + radius + 3, y + radius + 3, fill="", outline=_mix_color("#38bdf8", "#ffffff", 0.2), width=1)
    canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill="#1d4ed8", outline="#60a5fa", width=1)
    canvas.create_oval(x - radius * 0.55, y - radius * 0.45, x - radius * 0.1, y - radius * 0.05, fill="#166534", outline="")
    if crack > 0.05:
        for i in range(int(3 + crack * 6)):
            ang = i * 0.9 + frame * 0.02
            length = radius * (0.4 + crack * 0.9)
            ex = x + math.cos(ang) * length
            ey = y + math.sin(ang) * length * 0.85
            canvas.create_line(x, y, ex, ey, fill=_mix_color("#fbbf24", "#ef4444", crack), width=1 + int(crack * 2))
    if crack > 0.75:
        canvas.create_oval(x - radius * 0.3, y - radius * 0.3, x + radius * 0.3, y + radius * 0.3, fill=_mix_color("#ef4444", "#ffffff", 0.4), outline="")


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


def _shaded_poly(canvas, points, fill: str, outline: str = "", width: int = 1) -> None:
    canvas.create_polygon(*points, fill=_shift_color(fill, -0.18), outline=outline, width=width)
    cx = sum(points[::2]) / (len(points) // 2)
    cy = sum(points[1::2]) / (len(points) // 2)
    inner = []
    for x, y in zip(points[::2], points[1::2]):
        inner.extend((cx + (x - cx) * 0.86, cy + (y - cy) * 0.86))
    canvas.create_polygon(*inner, fill=fill, outline="")

def _line(canvas, points, *, fill: str, width: float, smooth: bool = True) -> None:
    canvas.create_line(
        *points,
        fill=fill,
        width=max(1, int(width)),
        capstyle=tk.ROUND,
        joinstyle=tk.ROUND,
        smooth=smooth,
    )


def _soft_line(canvas, points, *, fill: str, width: float, glow: str | None = None) -> None:
    if glow:
        _line(canvas, points, fill=glow, width=width + 8)
    _line(canvas, points, fill=fill, width=width)


def _notify(title: str, message: str) -> None:
    try:
        from plyer import notification

        notification.notify(title=title, message=message, app_name="Study Coach", timeout=10)
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
    _INSTANCE_MUTEX_HANDLE = kernel32.CreateMutexW(None, False, "Global\\Study.StudySticker")
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
        from coach import get_coach, get_line, pick_coach_key
        from database import add_daily_study_hours, init_db

        init_db()
        add_daily_study_hours(date.today(), hours, "Quick log - widget")
        try:
            from git_sync import notify_data_changed

            notify_data_changed()
        except Exception:
            pass
        key = pick_coach_key()
        coach = get_coach(key)
        _notify(coach["name"], f"Logged {hours:g}h. {get_line(key, 'praise')}")
    except Exception as exc:
        _notify("Study Tracker", f"Could not log: {exc}")


def _tray_image():
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([2, 2, 62, 62], fill=(3, 7, 18, 255), outline=(56, 189, 248, 180))
    draw.ellipse([14, 18, 50, 54], fill=(180, 120, 50, 255))
    draw.ellipse([8, 30, 56, 44], fill=(200, 180, 140, 200))
    draw.ellipse([22, 24, 42, 44], fill=(30, 41, 59, 255), outline=(148, 163, 184, 200))
    draw.ellipse([28, 30, 36, 38], fill=(34, 197, 94, 255))
    return img


def _draw_ultimate_deathstar(
    canvas,
    p: dict,
    ox: int,
    oy: int,
    frame: int,
    mode: str,
    progress: float,
    accent: str,
    *,
    look_angle: float = 0.0,
    watch_state: str = "scan",
    charge_level: float = 0.0,
    hull_spin: float = 0.0,
    evolution: float = 1.0,
    cursor_dist: float = 120.0,
) -> None:
    """ULTIMATE battle station — 50-year Ultimatrix evolution form."""
    phase = frame * p["speed"]
    evo = evolution
    bob_x = math.sin(phase * 0.7) * (7 + evo * 5)
    bob_y = math.sin(phase) * p["bob"]
    if watch_state == "alert" or mode == "touch":
        bob_x += math.sin(frame * 0.9) * (5 + evo * 3)
        bob_y += math.cos(frame * 1.1) * 3
    cx = ox + ACTOR_W // 2 + bob_x
    cy = oy + 108 + bob_y
    pulse = math.sin(phase * 2.0)
    glow = _mix_color(
        accent or p["glow"],
        p["imperial_red"],
        evo * 0.35 if watch_state == "locked" else evo * 0.1,
    )
    r = 48 + pulse * 2 + evo * 5
    beam_len = 0.0

    canvas.create_oval(cx - 46, oy + ACTOR_H - 26, cx + 46, oy + ACTOR_H - 8, fill="#1e293b", outline="")
    for i in range(4):
        radius = 36 + i * 11 + (frame + i * 5) % 10
        ring_color = _mix_color(glow, p["shield"] if i % 2 else p["body_2"], 0.42 - i * 0.06)
        canvas.create_oval(cx - radius, cy - radius // 3, cx + radius, cy + radius // 3, outline=ring_color, width=1)

    _draw_hex_grid(canvas, cx, cy, r + 10 + evo * 12, frame, evo, p["shield"])
    aura = r + 16 + evo * 20
    canvas.create_oval(cx - aura, cy - aura, cx + aura, cy + aura, fill="", outline=_mix_color(glow, p["hologram"], evo * 0.25), width=1)
    _shaded_oval(canvas, (cx - r, cy - r, cx + r, cy + r), p["body"], outline=p["trim"], width=2, glow=glow)

    for band in range(7):
        lat = hull_spin + band * 0.52
        yy = cy - r * 0.76 + band * r * 0.13
        canvas.create_arc(cx - r + 8, yy - 9, cx + r - 8, yy + 9, start=math.degrees(lat) % 360, extent=168, outline=p["body_3"], width=1, style=tk.ARC)
        if (frame + band * 3) % 15 < 4:
            lx = cx + math.cos(lat + band) * r * 0.84
            canvas.create_oval(lx - 2, yy - 2, lx + 2, yy + 2, fill=_mix_color(glow, "#fbbf24", 0.4), outline="")

    for i in range(4):
        turret_ang = hull_spin * 1.2 + i * (math.tau / 4)
        tx = cx + math.cos(turret_ang) * r * 0.88
        ty = cy + math.sin(turret_ang) * r * 0.42
        canvas.create_oval(tx - 5, ty - 4, tx + 5, ty + 4, fill="#0f172a", outline=glow, width=1)
        if watch_state in {"alert", "locked"} and (frame + i) % 11 < 3:
            bx = tx + math.cos(turret_ang) * 20
            by = ty + math.sin(turret_ang) * 10
            canvas.create_line(tx, ty, bx, by, fill=_mix_color(glow, "#ffffff", 0.5), width=2, capstyle=tk.ROUND)

    for i in range(6):
        mer_angle = hull_spin * 1.3 + i * 0.58 - 1.1
        x = cx + math.sin(mer_angle) * r * 0.82
        canvas.create_line(x, cy - r * 0.86, x + math.sin(mer_angle) * 14, cy + r * 0.82, fill=p["boot"], width=1)

    if evo > 0.35:
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

    if charge_level > 0.04 or evo > 0.5:
        for ring_i in range(4):
            ring_r = 14 + ring_i * 8 + math.sin(frame * 0.35 + ring_i) * 3
            ring_alpha = max(0.0, (charge_level + evo * 0.3) - ring_i * 0.16)
            if ring_alpha <= 0:
                continue
            canvas.create_oval(dish_cx - ring_r, dish_cy - ring_r * 0.65, dish_cx + ring_r, dish_cy + ring_r * 0.65, outline=_mix_color(glow, "#ffffff", ring_alpha * 0.65), width=2)

    if watch_state in {"tracking", "locked", "alert"} or mode == "touch":
        beam_len = 68 + min(52, cursor_dist * 0.05) + evo * 20
        if watch_state == "locked":
            beam_len += 30 + math.sin(frame * 0.32) * 10 + charge_level * 22
        elif watch_state == "alert":
            beam_len += 22
        if mode == "touch":
            beam_len = 96 + progress * 68
        beam_w = 5 if watch_state == "locked" or mode == "touch" else 3
        ex = dish_cx + math.cos(look_angle) * beam_len
        ey = dish_cy + math.sin(look_angle) * beam_len * 0.42
        for width, col, mix in (
            (beam_w + 16, glow, 0.6),
            (beam_w + 7, glow, 0.35),
            (beam_w, p["laser_hot"], 0.0),
            (max(2, beam_w - 3), p["laser_core"], 0.0),
        ):
            canvas.create_line(dish_cx, dish_cy, ex, ey, fill=_mix_color(col, "#ffffff", mix), width=width, capstyle=tk.ROUND)
        seg = 12
        for step in range(2, int(beam_len // seg)):
            t = step * seg / beam_len
            px = dish_cx + (ex - dish_cx) * t
            py = dish_cy + (ey - dish_cy) * t
            if (frame + step) % 2 == 0:
                sr = 2 + (step % 3) + int(evo * 2)
                canvas.create_oval(px - sr, py - sr, px + sr, py + sr, fill=p["laser_core"], outline="")
        planet_r = 8 + evo * 4
        if watch_state in {"locked", "alert"} or mode == "touch":
            crack = min(1.0, progress * 1.4) if mode == "touch" else 0.0
            _draw_target_planet(canvas, ex, ey, planet_r, crack, frame, evo)
        if watch_state == "locked" or mode == "touch":
            lock_r = 14 + math.sin(frame * 0.45) * 4 + evo * 4
            canvas.create_oval(ex - lock_r, ey - lock_r, ex + lock_r, ey + lock_r, outline=glow, width=2)
            canvas.create_line(ex - 20, ey, ex + 20, ey, fill=glow, width=2)
            canvas.create_line(ex, ey - 20, ex, ey + 20, fill=glow, width=2)

    if watch_state in {"scan", "patrol"}:
        for sweep_i in range(2):
            sweep = (frame * 0.035 + sweep_i * math.tau / 3) % math.tau
            sx = cx + math.cos(sweep) * (r + 26 + sweep_i * 6)
            sy = cy + math.sin(sweep) * (r * 0.34 + 26)
            canvas.create_line(cx, cy, sx, sy, fill=_mix_color(glow, p["hologram"], 0.15 + sweep_i * 0.12), width=2, dash=(4, 8))

    for tie_i in range(TIE_ESCORTS):
        orbit = frame * 0.028 + tie_i * (math.tau / TIE_ESCORTS)
        orbit_r = r + 20 + tie_i * 7
        tx = cx + math.cos(orbit) * orbit_r
        ty = cy + math.sin(orbit) * orbit_r * 0.4
        _draw_tie_fighter(canvas, tx, ty, orbit + math.pi / 2, scale=0.52 + evo * 0.1, glow=p["body_2"])

    _draw_star_destroyer(canvas, cx + r + 38, cy - 18, frame * 0.012 + 0.6, 0.48 + evo * 0.14, p["trim"], frame)

    for angle in (phase, phase + 1.4, phase + 2.8, phase + 4.2):
        sx = cx + math.cos(angle) * (54 + evo * 8)
        sy = cy + math.sin(angle) * 16
        canvas.create_rectangle(sx - 4, sy - 4, sx + 4, sy + 4, fill=p["body_3"], outline=glow)

    if mode == "touch":
        blast_x = dish_cx + math.cos(look_angle) * beam_len if beam_len else ox - 60
        blast_y = dish_cy + math.sin(look_angle) * beam_len * 0.42 if beam_len else cy
        for ring_i in range(6):
            br = 22 + progress * (76 + ring_i * 26)
            canvas.create_oval(blast_x - br, blast_y - br, blast_x + br, blast_y + br, outline=_mix_color(glow, "#ef4444", ring_i * 0.12), width=2)
        canvas.create_oval(cx - 88 - progress * 68, cy - 88 - progress * 68, cx + 88 + progress * 68, cy + 88 + progress * 68, outline=_mix_color(glow, "#ffffff", 0.35), width=3)
        canvas.create_text(cx, cy - r - 12, text="ULTIMATE FIRED", fill=p["imperial_red"], font=("Segoe UI", 7, "bold"))

    if evo > 0.7:
        canvas.create_text(cx - r - 4, cy - r - 4, text="MK-X", anchor="nw", fill=p["hologram"], font=FONT_HUD)

    if watch_state == "alert":
        for ring_i in range(3):
            ring = 50 + ((frame + ring_i * 5) % 16) * 3
            canvas.create_oval(cx - ring, cy - ring, cx + ring, cy + ring, outline=_mix_color(glow, p["imperial_red"], 0.2 + ring_i * 0.15), width=2)


def _draw_ultimate_jupiter(
    canvas,
    p: dict,
    ox: int,
    oy: int,
    frame: int,
    mode: str,
    progress: float,
    accent: str,
    *,
    spin: float = 0.0,
    look_angle: float = 0.0,
    watch_state: str = "scan",
    charge_level: float = 0.0,
    evolution: float = 1.0,
    cursor_dist: float = 120.0,
) -> None:
    """50-year ULTIMATE gas giant — banded storms, Red Spot, magnetosphere."""
    phase = frame * p["speed"]
    evo = evolution
    cx = ox + ACTOR_W // 2 + math.sin(phase * 0.65) * (6 + evo * 3)
    cy = oy + 108 + math.sin(phase) * p["bob"]
    if watch_state == "alert" or mode == "touch":
        cx += math.sin(frame * 0.85) * 3
        cy += math.cos(frame * 1.05) * 2
    r = 60 + evo * 4
    glow = _mix_color(accent or p["glow"], p["spot"], evo * 0.12)
    drift = spin * 48

    canvas.create_oval(cx - 54, oy + ACTOR_H - 24, cx + 54, oy + ACTOR_H - 8, fill="#0f172a", outline="")
    for i in range(4):
        aura_r = r + 14 + i * 12 + math.sin(frame * 0.06 + i) * 4
        canvas.create_oval(cx - aura_r, cy - aura_r, cx + aura_r, cy + aura_r, outline=_mix_color(glow, p["shield"], 0.18 - i * 0.03), width=1)

    _shaded_oval(canvas, (cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2), "#0f172a", outline="")
    band_colors = (
        p["band_light"], p["band_mid"], p["body_3"], p["band_storm"], p["band_dark"],
        p["body"], p["band_mid"], p["body_2"], p["band_light"], p["band_storm"], p["band_dark"],
    )
    band_h = (r * 2) / len(band_colors)
    for i, col in enumerate(band_colors):
        wobble = math.sin(drift + i * 0.55) * (1.5 + evo)
        y1 = cy - r + i * band_h + wobble
        y2 = y1 + band_h + 1.2
        canvas.create_arc(cx - r + 2, y1, cx + r - 2, y2, start=6 + drift * 0.55, extent=168, fill=col, outline="", style=tk.CHORD)
        if (frame + i) % 7 < 2:
            vx = cx + math.cos(drift + i * 0.8) * r * 0.7
            canvas.create_oval(vx - 3, y1 + 2, vx + 3, y1 + 8, fill=_mix_color(col, "#ffffff", 0.15), outline="")

    canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill="", outline=_shift_color(p["trim"], 0.2), width=2)
    canvas.create_oval(cx - r * 0.9, cy - r * 0.88, cx - r * 0.12, cy + r * 0.18, fill=_mix_color("#000000", p["body_3"], 0.5), outline="")

    for pole, py_off in (("north", -r * 0.82), ("south", r * 0.72)):
        pulse = 0.5 + 0.5 * math.sin(frame * 0.1 + (0 if pole == "north" else 1.5))
        canvas.create_oval(cx - 14, cy + py_off - 6, cx + 14, cy + py_off + 6, fill=_mix_color(p["aurora"], glow, pulse * 0.35), outline="")

    spot_x = cx + r * 0.2 + math.sin(spin * 0.35) * 4
    spot_y = cy + r * 0.1
    spot_pulse = 1.0 + charge_level * 0.15 + math.sin(frame * 0.12) * 0.06
    sw, sh = 24 * spot_pulse, 16 * spot_pulse
    for ring_i in range(3):
        sr = sw + ring_i * 6 + charge_level * 8
        canvas.create_oval(spot_x - sr, spot_y - sh - ring_i * 3, spot_x + sr, spot_y + sh + ring_i * 2, outline=_mix_color(p["spot"], "#ffffff", 0.2 - ring_i * 0.05), width=1)
    canvas.create_oval(spot_x - sw, spot_y - sh, spot_x + sw, spot_y + sh, fill=p["spot"], outline=p["spot_core"], width=2)
    canvas.create_oval(spot_x - sw * 0.5, spot_y - sh * 0.45, spot_x + sw * 0.4, spot_y + sh * 0.4, fill=p["spot_core"], outline="")
    for arm in range(4):
        ang = drift * 0.4 + arm * 1.57
        ex = spot_x + math.cos(ang) * (sw + 10)
        ey = spot_y + math.sin(ang) * (sh + 6)
        canvas.create_line(spot_x, spot_y, ex, ey, fill=_mix_color(p["spot_core"], "#ffffff", 0.25), width=1)

    moons = ((r + 20, 3.5, "#e7e5e4", "Io"), (r + 32, 3.0, "#d6d3d1", "Europa"), (r + 44, 4.2, "#fbbf24", "Ganymede"), (r + 56, 2.8, "#a8a29e", "Callisto"))
    for moon_i, (orbit_r, size, col, _name) in enumerate(moons):
        ang = spin * (1.3 + moon_i * 0.28) + moon_i * 1.62
        mx = cx + math.cos(ang) * orbit_r
        my = cy + math.sin(ang) * orbit_r * 0.34
        canvas.create_oval(mx - size - 1, my - size - 1, mx + size + 1, my + size + 1, fill="", outline=_mix_color(glow, "#ffffff", 0.12), width=1)
        canvas.create_oval(mx - size, my - size, mx + size, my + size, fill=col, outline="#57534e", width=1)

    if evo > 0.4:
        for i in range(3):
            field_r = r + 28 + i * 16
            canvas.create_arc(cx - field_r, cy - field_r * 0.5, cx + field_r, cy + field_r * 0.5, start=30 + i * 40, extent=120, outline=_mix_color(p["aurora"], glow, 0.15), width=1, style=tk.ARC)

    if watch_state in {"tracking", "locked", "alert"} or mode == "touch":
        beam_len = 36 + min(40, cursor_dist * 0.04) + (24 if watch_state == "locked" else 0) + evo * 16
        if mode == "touch":
            beam_len = 60 + progress * 50
        ex = cx + math.cos(look_angle) * (r + beam_len)
        ey = cy + math.sin(look_angle) * (r + beam_len) * 0.38
        for width, col, mix in ((10, glow, 0.5), (5, p["spot"], 0.2), (2, "#ffffff", 0.0)):
            canvas.create_line(cx, cy, ex, ey, fill=_mix_color(col, "#ffffff", mix), width=width, capstyle=tk.ROUND)
        if watch_state == "locked":
            canvas.create_oval(ex - 10, ey - 10, ex + 10, ey + 10, outline=glow, width=2)

    if watch_state in {"scan", "patrol"}:
        sweep = (frame * 0.032) % math.tau
        sx = cx + math.cos(sweep) * (r + 22)
        sy = cy + math.sin(sweep) * (r * 0.35 + 22)
        canvas.create_line(cx, cy, sx, sy, fill=_mix_color(glow, p["hologram"], 0.2), width=2, dash=(5, 7))

    if mode == "touch":
        for ring_i in range(6):
            shock = 18 + progress * (55 + ring_i * 20)
            canvas.create_oval(spot_x - shock, spot_y - shock * 0.55, spot_x + shock, spot_y + shock * 0.55, outline=_mix_color(p["spot"], "#ffffff", 0.35 - ring_i * 0.05), width=2)
        canvas.create_oval(cx - r - progress * 80, cy - r - progress * 80, cx + r + progress * 80, cy + r + progress * 80, outline=_mix_color(glow, "#ffffff", 0.3), width=3)
        canvas.create_text(cx, cy - r - 16, text="ULTIMATE STORM", fill=p["spot"], font=("Segoe UI", 7, "bold"))

    if watch_state == "alert":
        for ring_i in range(3):
            ring = 50 + ((frame + ring_i * 4) % 14) * 3
            canvas.create_oval(cx - ring, cy - ring * 0.85, cx + ring, cy + ring * 0.85, outline=_mix_color(p["spot"], "#ffffff", 0.2), width=2)


def _draw_ultimate_saturn(
    canvas,
    p: dict,
    ox: int,
    oy: int,
    frame: int,
    mode: str,
    progress: float,
    accent: str,
    *,
    spin: float = 0.0,
    look_angle: float = 0.0,
    watch_state: str = "scan",
    charge_level: float = 0.0,
    evolution: float = 1.0,
    cursor_dist: float = 120.0,
) -> None:
    """50-year ULTIMATE ringed giant — Cassini rings, hex storm, shepherd moons."""
    phase = frame * p["speed"]
    evo = evolution
    cx = ox + ACTOR_W // 2 + math.sin(phase * 0.58) * (5 + evo * 2)
    cy = oy + 116 + math.sin(phase) * p["bob"]
    r = 36 + evo * 3
    ring_rx, ring_ry = 96 + evo * 8, 28 + evo * 2
    glow = accent or p["glow"]
    shimmer = math.sin(frame * 0.09) * 0.18 + charge_level * 0.12

    canvas.create_oval(cx - ring_rx, oy + ACTOR_H - 20, cx + ring_rx, oy + ACTOR_H - 6, fill="#0f172a", outline="")

    def _ring_arc(start: float, extent: float, rx: float, ry: float, color: str, width: int = 10) -> None:
        canvas.create_arc(cx - rx, cy - ry, cx + rx, cy + ry, start=start, extent=extent, outline=color, width=width, style=tk.ARC)

    _draw_hex_grid(canvas, cx, cy, ring_rx * 0.55, frame, evo * 0.65, p["shield"])
    _ring_arc(188, 164, ring_rx + 6, ring_ry + 2, _mix_color(p["ring_shadow"], "#000000", 0.3), 4)
    _ring_arc(188, 164, ring_rx, ring_ry, _mix_color(p["ring_shadow"], "#000000", 0.22), 13)
    _ring_arc(192, 156, ring_rx - 6, ring_ry - 2, p["ring_bright"], 10)
    _ring_arc(194, 152, ring_rx - 20, ring_ry - 4, p["ring_inner"], 6)
    for i in range(RING_PARTICLES):
        t = i / RING_PARTICLES * math.tau + spin * 0.6
        px = cx + math.cos(t) * (ring_rx - 4)
        py = cy + math.sin(t) * (ring_ry - 1)
        if py < cy:
            canvas.create_oval(px - 1.2, py - 1.2, px + 1.2, py + 1.2, fill=_mix_color(p["ring_outer"], "#ffffff", 0.15), outline="")

    _shaded_oval(canvas, (cx - r, cy - r, cx + r, cy + r), p["body"], outline=p["trim"], width=1, glow=_mix_color(glow, "#ffffff", 0.1))
    for i, col in enumerate((p["band_light"], p["band_soft"], p["body_2"], p["band_soft"], p["band_light"])):
        lat = cy - r * 0.72 + i * (r * 1.44 / 5) + math.sin(spin + i) * 0.8
        canvas.create_arc(cx - r + 3, lat, cx + r - 3, lat + r * 0.3, start=8 + spin * 20, extent=164, fill=col, outline="", style=tk.CHORD)
    canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill="", outline=_shift_color(p["trim"], 0.12), width=1)
    canvas.create_oval(cx - r * 0.88, cy - r * 0.82, cx - r * 0.1, cy + r * 0.12, fill=_mix_color("#000000", p["body"], 0.38), outline="")

    hex_r = 11 + evo * 2
    hx, hy = cx, cy - r * 0.55
    hex_pts = []
    for i in range(6):
        ang = math.pi / 6 + i * math.pi / 3 + math.sin(frame * 0.05) * 0.08
        hex_pts.extend((hx + math.cos(ang) * hex_r, hy + math.sin(ang) * hex_r * 0.55))
    canvas.create_polygon(*hex_pts, fill="", outline=_mix_color(p["hex_storm"], glow, 0.35), width=1)

    if evo > 0.35:
        for spoke_i in range(8):
            spoke_ang = spin * 2.2 + spoke_i * (math.tau / 8)
            sx = cx + math.cos(spoke_ang) * (ring_rx - 10)
            sy = cy + math.sin(spoke_ang) * (ring_ry - 3)
            canvas.create_line(cx, cy, sx, sy, fill=_mix_color(p["ring_gap"], "#ffffff", 0.08), width=1)

    moons = ((ring_rx + 10, 4.5, "#d97706", "Titan"), (r + 24, 2.5, "#e7e5e4", "Rhea"), (ring_rx - 14, 2.2, "#f8fafc", "Enceladus"), (r + 38, 2.0, "#94a3b8", "Mimas"))
    for moon_i, (orbit_r, size, col, _name) in enumerate(moons):
        ang = spin * (0.85 + moon_i * 0.22) + moon_i * 1.4
        mx = cx + math.cos(ang) * orbit_r
        my = cy + math.sin(ang) * orbit_r * 0.32
        canvas.create_oval(mx - size, my - size, mx + size, my + size, fill=col, outline="#57534e", width=1)

    _ring_arc(8, 164, ring_rx + 4, ring_ry + 1, _mix_color(p["ring_outer"], "#ffffff", shimmer + 0.12), 3)
    _ring_arc(8, 164, ring_rx, ring_ry, _mix_color(p["ring_bright"], "#ffffff", shimmer + 0.15), 12)
    _ring_arc(12, 156, ring_rx - 6, ring_ry - 2, p["ring_inner"], 8)
    _ring_arc(14, 152, ring_rx - 20, ring_ry - 4, _mix_color(p["ring_gap"], p["ring_shadow"], 0.45), 4)
    for i in range(RING_PARTICLES):
        t = i / RING_PARTICLES * math.tau + spin * 0.6
        px = cx + math.cos(t) * (ring_rx - 4)
        py = cy + math.sin(t) * (ring_ry - 1)
        if py >= cy - 2:
            canvas.create_oval(px - 1.4, py - 1.4, px + 1.4, py + 1.4, fill=_mix_color(p["ring_bright"], glow, 0.2), outline="")

    if watch_state in {"tracking", "locked", "alert"} or mode == "touch":
        sweep = look_angle if watch_state != "scan" else (frame * 0.04) % math.tau
        sx = cx + math.cos(sweep) * ring_rx
        sy = cy + math.sin(sweep) * ring_ry * 0.55
        beam_w = 4 if watch_state == "locked" or mode == "touch" else 2
        canvas.create_line(cx, cy, sx, sy, fill=_mix_color(glow, "#ffffff", 0.35), width=beam_w + 6, capstyle=tk.ROUND)
        canvas.create_line(cx, cy, sx, sy, fill=glow, width=beam_w, capstyle=tk.ROUND)
        if watch_state == "locked":
            canvas.create_oval(sx - 12, sy - 12, sx + 12, sy + 12, outline=glow, width=2)

    if mode == "touch":
        for ring_i in range(7):
            pulse_rx = ring_rx + progress * (28 + ring_i * 12)
            pulse_ry = ring_ry + progress * (7 + ring_i * 2)
            canvas.create_arc(cx - pulse_rx, cy - pulse_ry, cx + pulse_rx, cy + pulse_ry, start=0, extent=359, outline=_mix_color(glow, "#ffffff", 0.32 - ring_i * 0.04), width=2, style=tk.ARC)
        canvas.create_text(cx, cy - ring_ry - 20, text="ULTIMATE RINGS", fill=glow, font=("Segoe UI", 7, "bold"))

    if watch_state == "alert":
        for ring_i in range(3):
            ring = 44 + ((frame + ring_i * 5) % 14) * 3
            canvas.create_oval(cx - ring, cy - ring * 0.38, cx + ring, cy + ring * 0.38, outline=_mix_color(glow, p["hex_storm"], 0.25), width=2)


def _draw_head(canvas, p: dict, style: str, cx: float, head_y: float, scale: float, bob: float, facing: int) -> None:
    glow = p["glow"]
    eye = p["eye"]

    if style == "sage":
        ear_y = head_y + 4 * scale
        canvas.create_polygon(
            cx - 20 * scale,
            ear_y,
            cx - 70 * scale,
            ear_y - 16 * scale,
            cx - 35 * scale,
            ear_y + 18 * scale,
            fill=p["head"],
            outline="#3f6212",
            width=1,
        )
        canvas.create_polygon(
            cx + 20 * scale,
            ear_y,
            cx + 70 * scale,
            ear_y - 16 * scale,
            cx + 35 * scale,
            ear_y + 18 * scale,
            fill=p["head"],
            outline="#3f6212",
            width=1,
        )
        canvas.create_oval(
            cx - 28 * scale,
            head_y - 25 * scale,
            cx + 28 * scale,
            head_y + 28 * scale,
            fill=p["face"],
            outline="#4d7c0f",
            width=2,
        )
        canvas.create_line(cx - 15 * scale, head_y - 5 * scale, cx - 5 * scale, head_y - 6 * scale, fill=eye, width=2)
        canvas.create_line(cx + 5 * scale, head_y - 6 * scale, cx + 15 * scale, head_y - 5 * scale, fill=eye, width=2)
        canvas.create_arc(
            cx - 12 * scale,
            head_y + 7 * scale,
            cx + 12 * scale,
            head_y + 18 * scale,
            start=190,
            extent=160,
            outline="#3f6212",
            width=2,
        )
        return

    if style == "warden":
        canvas.create_polygon(
            cx,
            head_y - 39 * scale,
            cx - 39 * scale,
            head_y + 8 * scale,
            cx - 25 * scale,
            head_y + 35 * scale,
            cx + 25 * scale,
            head_y + 35 * scale,
            cx + 39 * scale,
            head_y + 8 * scale,
            fill=p["head"],
            outline=p["trim"],
            width=2,
        )
        canvas.create_polygon(
            cx - 23 * scale,
            head_y - 4 * scale,
            cx + 23 * scale,
            head_y - 4 * scale,
            cx + 16 * scale,
            head_y + 23 * scale,
            cx - 16 * scale,
            head_y + 23 * scale,
            fill=p["face"],
            outline="#27272a",
        )
        canvas.create_line(cx - 19 * scale, head_y + 2 * scale, cx + 19 * scale, head_y + 2 * scale, fill=eye, width=max(2, int(3 * scale)))
        canvas.create_line(cx, head_y - 32 * scale, cx, head_y + 31 * scale, fill="#3f3f46", width=2)
        return

    if style == "ranger":
        canvas.create_polygon(
            cx - 34 * scale,
            head_y - 30 * scale,
            cx + 34 * scale,
            head_y - 30 * scale,
            cx + 29 * scale,
            head_y + 25 * scale,
            cx,
            head_y + 37 * scale,
            cx - 29 * scale,
            head_y + 25 * scale,
            fill=p["head"],
            outline=p["trim"],
            width=2,
        )
        canvas.create_polygon(
            cx - 22 * scale,
            head_y - 8 * scale,
            cx + 24 * scale,
            head_y - 8 * scale,
            cx + 15 * scale,
            head_y + 12 * scale,
            cx - 18 * scale,
            head_y + 12 * scale,
            fill=p["face"],
            outline="",
        )
        canvas.create_line(cx - 18 * scale, head_y + 2 * scale, cx + 17 * scale, head_y + 2 * scale, fill=eye, width=3)
        return

    if style == "duelist":
        canvas.create_oval(
            cx - 26 * scale,
            head_y - 28 * scale,
            cx + 26 * scale,
            head_y + 28 * scale,
            fill=p["face"],
            outline="#a8a29e",
            width=1,
        )
        canvas.create_arc(
            cx - 31 * scale,
            head_y - 35 * scale,
            cx + 25 * scale,
            head_y + 14 * scale,
            start=35,
            extent=205,
            outline=p["head"],
            width=max(7, int(10 * scale)),
        )
        canvas.create_line(cx - 12 * scale, head_y - 4 * scale, cx - 3 * scale, head_y - 5 * scale, fill=eye, width=2)
        canvas.create_line(cx + 4 * scale, head_y - 5 * scale, cx + 13 * scale, head_y - 4 * scale, fill=eye, width=2)
        canvas.create_line(cx + 4 * scale * facing, head_y + 8 * scale, cx + 14 * scale * facing, head_y + 12 * scale, fill="#78350f", width=2)
        return

    # Kinetic young-hero profile.
    canvas.create_oval(
        cx - 26 * scale,
        head_y - 27 * scale,
        cx + 26 * scale,
        head_y + 27 * scale,
        fill=p["face"],
        outline="#7c2d12",
        width=1,
    )
    hair = [
        (cx - 28 * scale, head_y - 18 * scale),
        (cx - 16 * scale, head_y - 35 * scale + bob),
        (cx - 4 * scale, head_y - 20 * scale),
        (cx + 8 * scale, head_y - 37 * scale - bob),
        (cx + 26 * scale, head_y - 18 * scale),
        (cx + 22 * scale, head_y - 2 * scale),
        (cx - 22 * scale, head_y - 3 * scale),
    ]
    canvas.create_polygon(*hair, fill="#7c2d12", outline="#451a03")
    canvas.create_line(cx - 13 * scale, head_y - 3 * scale, cx - 4 * scale, head_y - 4 * scale, fill=eye, width=2)
    canvas.create_line(cx + 4 * scale, head_y - 4 * scale, cx + 13 * scale, head_y - 3 * scale, fill=eye, width=2)
    canvas.create_line(cx - 8 * scale, head_y + 13 * scale, cx + 10 * scale, head_y + 12 * scale, fill="#7c2d12", width=2)


def _draw_weapon(canvas, p: dict, hand: tuple[float, float], scale: float, facing: int, progress: float) -> None:
    fx = p["fx"]
    glow = p["glow"]
    hx, hy = hand

    if fx == "annihilator_blade":
        sweep = math.sin(progress * math.pi)
        angle = -1.05 + sweep * 2.0
        length = 102 * scale
        ex = hx + facing * math.cos(angle) * length
        ey = hy + math.sin(angle) * length
        energy = p.get("energy", glow)
        for layer, (width, col, mix) in enumerate(
            ((14 * scale, energy, 0.5), (9 * scale, glow, 0.3), (5 * scale, "#fee2e2", 0.0), (2 * scale, "#ffffff", 0.0))
        ):
            _line(canvas, (hx, hy, ex, ey), fill=_mix_color(col, "#ffffff", mix), width=width)
        arc_r = 28 + progress * 42
        canvas.create_arc(
            hx - arc_r, hy - arc_r, hx + arc_r, hy + arc_r,
            start=200 - sweep * 60, extent=140 + sweep * 80,
            outline=_mix_color(energy, "#ffffff", 0.35), width=2, style=tk.ARC,
        )
        for i in range(4):
            t = (i + 1) / 5
            px = hx + (ex - hx) * t
            py = hy + (ey - hy) * t
            canvas.create_oval(px - 3, py - 3, px + 3, py + 3, fill=_mix_color(glow, "#ffffff", 0.4), outline="")
        return

    if fx in {"blade", "duel"}:
        sweep = math.sin(progress * math.pi)
        angle = -0.95 + sweep * 1.8
        length = 86 * scale
        ex = hx + facing * math.cos(angle) * length
        ey = hy + math.sin(angle) * length
        _soft_line(canvas, (hx, hy, ex, ey), fill="#fee2e2", width=4 * scale, glow=glow)
        return

    if fx == "blaster":
        ex = hx + facing * 96 * scale
        ey = hy - (18 + progress * 18) * scale
        _soft_line(canvas, (hx, hy, ex, ey), fill="#e0f2fe", width=3 * scale, glow=glow)
        for i in range(3):
            bx = hx + facing * (32 + i * 21 + progress * 20) * scale
            by = hy - (6 + i * 4) * scale
            canvas.create_oval(bx - 4, by - 4, bx + 4, by + 4, fill=glow, outline="")
        return

    if fx == "calm":
        for i in range(3):
            r = (28 + i * 16 + progress * 28) * scale
            canvas.create_oval(hx - r, hy - r, hx + r, hy + r, outline=glow, width=2)


def _draw_humanoid(
    canvas,
    p: dict,
    ox: int,
    oy: int,
    frame: int,
    mode: str,
    progress: float,
    facing: int,
    accent: str,
) -> None:
    style = p["style"]
    phase = frame * p["speed"]
    scale = p["scale"]
    step = math.sin(phase)
    counter_step = math.sin(phase + math.pi)
    calm = style == "sage"

    if calm:
        step *= 0.45
        counter_step *= 0.45
    if mode == "drag":
        step *= 0.25
        counter_step *= 0.25
    if mode == "hover":
        step *= 0.15
        counter_step *= 0.15
    if mode == "idle":
        step *= 0.08
        counter_step *= 0.08

    bob = math.sin(phase * 2) * p["bob"]
    lean = math.sin(phase) * p["lean"]
    if mode == "touch":
        bob -= math.sin(progress * math.pi) * 12
        lean += facing * math.sin(progress * math.pi) * 9
    elif mode == "hover":
        bob *= 0.45
        lean = facing * (4.0 if not calm else 2.0)
    elif mode == "idle":
        bob = math.sin(progress * math.tau * 2) * (p["bob"] * 0.75)
        lean *= 0.2

    cx = ox + ACTOR_W / 2 + lean
    ground = oy + ACTOR_H - 17
    leg_h = 71 * scale
    torso_h = 87 * scale
    shoulder_w = 59 * scale
    waist_w = 39 * scale
    hip_y = ground - leg_h + bob
    chest_y = hip_y - torso_h
    head_y = chest_y - 27 * scale
    glow = accent or p["glow"]

    shadow_w = 72 * scale + abs(step) * 18
    canvas.create_oval(cx - shadow_w, ground - 6, cx + shadow_w, ground + 6, fill="#d1d5db", outline="")

    if calm:
        for i in range(3):
            radius = (42 + i * 18 + (frame + i * 7) % 14) * scale
            canvas.create_oval(
                cx - radius,
                head_y - radius,
                cx + radius,
                head_y + radius,
                outline=glow if i == 0 else "#bbf7d0",
                width=1,
            )

    if style in {"warden", "duelist", "blaze"}:
        cape_sway = math.sin(phase + 0.8) * 12 * scale
        canvas.create_polygon(
            cx - shoulder_w * 0.78,
            chest_y + 12 * scale,
            cx + shoulder_w * 0.78,
            chest_y + 12 * scale,
            cx + shoulder_w * 0.95 + cape_sway,
            ground - 12 * scale,
            cx + 9 * scale,
            ground - 23 * scale,
            cx - shoulder_w * 0.95 + cape_sway * 0.4,
            ground - 12 * scale,
            fill=p["cloak"],
            outline="",
        )

    left_hip = (cx - 19 * scale, hip_y)
    right_hip = (cx + 19 * scale, hip_y)
    left_knee = (cx - 18 * scale + step * 16 * scale, hip_y + 32 * scale)
    right_knee = (cx + 18 * scale + counter_step * 16 * scale, hip_y + 32 * scale)
    left_foot = (cx - 20 * scale - step * 25 * scale, ground - max(0, step) * 7 * scale)
    right_foot = (cx + 20 * scale - counter_step * 25 * scale, ground - max(0, counter_step) * 7 * scale)

    _line(canvas, (*right_hip, *right_knee, *right_foot), fill=p["boot"], width=13 * scale)
    _line(canvas, (*left_hip, *left_knee, *left_foot), fill=p["boot"], width=14 * scale)
    for fx, fy in (right_foot, left_foot):
        canvas.create_oval(fx - 16 * scale, fy - 5 * scale, fx + 17 * scale, fy + 6 * scale, fill=p["boot"], outline="")

    canvas.create_polygon(
        cx - shoulder_w,
        chest_y + 4 * scale,
        cx + shoulder_w,
        chest_y + 4 * scale,
        cx + waist_w,
        hip_y + 12 * scale,
        cx - waist_w,
        hip_y + 12 * scale,
        fill=p["body"],
        outline=p["trim"],
        width=1,
    )
    canvas.create_polygon(
        cx - shoulder_w * 0.35,
        chest_y + 7 * scale,
        cx + shoulder_w * 0.35,
        chest_y + 7 * scale,
        cx + waist_w * 0.58,
        hip_y + 8 * scale,
        cx - waist_w * 0.58,
        hip_y + 8 * scale,
        fill=p["body_2"],
        outline="",
    )
    canvas.create_rectangle(cx - waist_w * 0.8, hip_y + 2 * scale, cx + waist_w * 0.8, hip_y + 10 * scale, fill=p["trim"], outline="")

    left_shoulder = (cx - shoulder_w * 0.78, chest_y + 25 * scale)
    right_shoulder = (cx + shoulder_w * 0.78, chest_y + 25 * scale)
    arm_swing = math.sin(phase + math.pi) * 18 * scale
    left_hand = (cx - 49 * scale - arm_swing * 0.45, hip_y - 1 * scale + abs(step) * 5 * scale)
    right_hand = (cx + 49 * scale + arm_swing * 0.45, hip_y - 1 * scale + abs(counter_step) * 5 * scale)

    if calm:
        left_hand = (cx - 13 * scale, hip_y - 32 * scale + math.sin(phase) * 2)
        right_hand = (cx + 13 * scale, hip_y - 32 * scale + math.sin(phase) * 2)
        staff_x = cx - 55 * scale + math.sin(phase) * 2
        _line(canvas, (staff_x, chest_y - 16 * scale, staff_x, ground - 8 * scale), fill="#7c2d12", width=4 * scale)
        canvas.create_oval(staff_x - 8 * scale, chest_y - 25 * scale, staff_x + 8 * scale, chest_y - 9 * scale, fill=glow, outline="")

    if mode == "hover":
        right_hand = (right_hand[0] + facing * 8 * scale, right_hand[1] - 10 * scale)
    if mode == "touch" and p["fx"] in {"blade", "duel", "blaster", "annihilator_blade"}:
        right_hand = (cx + facing * 61 * scale, chest_y + 58 * scale - progress * 30 * scale)

    _line(canvas, (*right_shoulder, cx + 42 * scale, chest_y + 60 * scale, *right_hand), fill=p["body_2"], width=12 * scale)
    _line(canvas, (*left_shoulder, cx - 42 * scale, chest_y + 60 * scale, *left_hand), fill=p["body_2"], width=12 * scale)
    canvas.create_oval(right_hand[0] - 7 * scale, right_hand[1] - 7 * scale, right_hand[0] + 7 * scale, right_hand[1] + 7 * scale, fill=p["skin"], outline="")
    canvas.create_oval(left_hand[0] - 7 * scale, left_hand[1] - 7 * scale, left_hand[0] + 7 * scale, left_hand[1] + 7 * scale, fill=p["skin"], outline="")

    if mode == "touch":
        hand = right_hand if p["fx"] != "calm" else ((left_hand[0] + right_hand[0]) / 2, (left_hand[1] + right_hand[1]) / 2)
        _draw_weapon(canvas, {**p, "glow": glow}, hand, scale, facing, progress)

    _draw_head(canvas, {**p, "glow": glow}, style, cx, head_y, scale, bob, facing)


def _smooth_lift(value: float) -> float:
    v = max(0.0, value)
    eased = v * v * (3.0 - 2.0 * v)
    return eased ** 0.88


def _vader_leg_phase(phase: float, offset: float = 0.0) -> tuple[float, float]:
    t = phase + offset
    raw = math.sin(t) * 0.8 + math.sin(t * 2.0) * 0.14
    swing = math.tanh(raw * 1.2) * 0.96
    lift = _smooth_lift(swing)
    return swing, lift


def _draw_vader_arm(
    canvas,
    shoulder: tuple[float, float],
    hand: tuple[float, float],
    *,
    scale: float,
    body_color: str,
    body_2: str,
    trim: str,
    bend: float = 1.0,
) -> None:
    sx, sy = shoulder
    hx, hy = hand
    side = 1.0 if hx >= sx else -1.0
    elbow = (
        (sx + hx) * 0.5 + side * 8 * scale * bend,
        (sy + hy) * 0.5 + 14 * scale,
    )
    for width, fill in ((16 * scale, _shift_color(body_2, -0.2)), (11 * scale, body_2)):
        _line(canvas, (sx, sy, *elbow), fill=fill, width=width)
        _line(canvas, (*elbow, hx, hy), fill=fill, width=width * 0.92)
    _shaded_oval(
        canvas,
        (elbow[0] - 7 * scale, elbow[1] - 7 * scale, elbow[0] + 7 * scale, elbow[1] + 7 * scale),
        body_2,
        outline=trim,
    )


def _draw_vader_helmet(
    canvas,
    p: dict,
    cx: float,
    head_y: float,
    scale: float,
    facing: int,
    accent: str,
    look_angle: float,
    watch_state: str,
    *,
    head_tilt: float = 0.0,
    frame: int = 0,
) -> None:
    glow = accent or p["glow"]
    energy = p.get("energy", glow)
    evo = p.get("evolution", 0.0)
    eye = p["eye"]
    gaze_x = math.cos(look_angle)
    gaze_y = math.sin(look_angle) * 0.55
    visor_x = max(-7, min(7, gaze_x * 9 * facing))
    visor_y = max(-4, min(4, gaze_y * 7))
    s = scale
    hy = head_y + head_tilt
    trim = p["trim"]
    head = p["head"]
    face = p["face"]
    chrome = "#d4d4d8" if evo > 0.5 else "#a1a1aa"

    if evo > 0.5:
        for side in (-1, 1):
            horn_x = cx + side * 34 * s
            canvas.create_polygon(
                horn_x, hy - 38 * s,
                horn_x + side * 8 * s, hy - 52 * s,
                horn_x + side * 3 * s, hy - 30 * s,
                fill=_shift_color(head, -0.12),
                outline=chrome,
                width=1,
            )
            canvas.create_line(horn_x, hy - 36 * s, horn_x + side * 6 * s, hy - 48 * s, fill=_mix_color(energy, "#ffffff", 0.35), width=1)

    canvas.create_arc(
        cx - 39 * s, hy - 47 * s, cx + 39 * s, hy + 5 * s,
        start=6, extent=168, fill=head, outline=trim, width=2, style=tk.PIESLICE,
    )
    for start, extent in ((10, 55), (70, 55), (130, 44)):
        canvas.create_arc(
            cx - 36 * s, hy - 43 * s, cx + 36 * s, hy + 1 * s,
            start=start, extent=extent, outline=_shift_color(head, 0.28), width=1, style=tk.ARC,
        )
    canvas.create_line(cx - 12 * s, hy - 45 * s, cx + 12 * s, hy - 45 * s, fill=chrome, width=2)
    canvas.create_line(cx - 5 * s, hy - 45 * s, cx + 5 * s, hy - 39 * s, fill=_shift_color(head, 0.18), width=1)
    canvas.create_line(cx, hy - 45 * s, cx, hy - 33 * s, fill="#52525b", width=2)

    _shaded_poly(
        canvas,
        (
            cx, hy - 41 * s,
            cx - 36 * s, hy - 2 * s,
            cx - 27 * s, hy + 37 * s,
            cx + 27 * s, hy + 37 * s,
            cx + 36 * s, hy - 2 * s,
        ),
        head,
        outline=trim,
        width=2,
    )
    canvas.create_line(cx - 36 * s, hy - 8 * s, cx + 36 * s, hy - 8 * s, fill="#3f3f46", width=1)
    canvas.create_polygon(
        cx - 12 * s, hy - 35 * s,
        cx + 12 * s, hy - 35 * s,
        cx + 9 * s, hy - 27 * s,
        cx - 9 * s, hy - 27 * s,
        fill=_shift_color(head, 0.14),
        outline=chrome,
        width=1,
    )

    for side in (-1, 1):
        bx = cx + side * 31 * s
        canvas.create_polygon(
            bx, hy - 12 * s,
            bx + side * 10 * s, hy - 8 * s,
            bx + side * 9 * s, hy + 18 * s,
            bx + side * 2 * s, hy + 22 * s,
            bx - side * 2 * s, hy + 14 * s,
            fill="#101012",
            outline=chrome,
            width=2,
        )
        canvas.create_line(bx, hy - 4 * s, bx + side * 7 * s, hy + 8 * s, fill="#27272a", width=2)
        canvas.create_line(bx + side * 3 * s, hy + 2 * s, bx + side * 8 * s, hy + 16 * s, fill="#18181b", width=1)

    canvas.create_polygon(
        cx - 28 * s + visor_x * 0.25, hy - 5 * s + visor_y,
        cx + 28 * s + visor_x * 0.25, hy - 5 * s + visor_y,
        cx + 23 * s + visor_x, hy + 9 * s + visor_y,
        cx - 23 * s + visor_x, hy + 9 * s + visor_y,
        fill="#010102",
        outline=chrome,
        width=2,
    )
    canvas.create_polygon(
        cx - 25 * s + visor_x, hy - 2 * s + visor_y,
        cx + 25 * s + visor_x, hy - 2 * s + visor_y,
        cx + 21 * s + visor_x, hy + 6 * s + visor_y,
        cx - 21 * s + visor_x, hy + 6 * s + visor_y,
        fill=face,
        outline="#27272a",
        width=1,
    )
    canvas.create_line(
        cx + visor_x, hy - 1 * s + visor_y,
        cx + visor_x, hy + 5.5 * s + visor_y,
        fill="#09090b",
        width=3,
    )
    visor_glow = eye if watch_state == "locked" else _mix_color(eye, "#450a0a", 0.12)
    for slot_x, slot_w in ((-18, 15), (3, 15)):
        x1 = cx + slot_x * s + visor_x
        x2 = cx + (slot_x + slot_w) * s + visor_x
        y1 = hy + 1.2 * s + visor_y
        y2 = hy + 4.8 * s + visor_y
        canvas.create_rectangle(x1, y1, x2, y2, fill=visor_glow, outline="#991b1b", width=1)
        canvas.create_line(x1 + 1, y1 + 1, x2 - 1, y1 + 1, fill=_mix_color(visor_glow, "#ffffff", 0.55), width=1)
        canvas.create_line(x1 + 1, y2 - 1, x2 - 1, y2 - 1, fill="#450a0a", width=1)

    if evo > 0.5:
        scan_offset = math.sin(frame * 0.18) * 2 * s
        for scan_i in range(3):
            sy = hy + (1.5 + scan_i * 2.2) * s + visor_y + scan_offset
            canvas.create_line(cx - 22 * s + visor_x, sy, cx + 22 * s + visor_x, sy, fill=_mix_color(energy, "#ffffff", 0.25), width=1)

    canvas.create_polygon(
        cx, hy + 14 * s,
        cx - 21 * s, hy + 12 * s,
        cx - 15 * s, hy + 37 * s,
        cx + 15 * s, hy + 37 * s,
        cx + 21 * s, hy + 12 * s,
        fill=_shift_color(head, -0.08),
        outline="#3f3f46",
        width=2,
    )
    canvas.create_arc(
        cx - 33 * s, hy + 29 * s, cx + 33 * s, hy + 45 * s,
        start=0, extent=180, fill="#0a0a0c", outline=trim, width=2, style=tk.CHORD,
    )
    for i in range(7):
        vx = cx - 15 * s + i * 4.8 * s
        canvas.create_rectangle(vx, hy + 32 * s, vx + 2.5 * s, hy + 39 * s, fill="#1f1f23", outline="#52525b", width=1)
        if i < 6:
            canvas.create_line(vx + 2.5 * s, hy + 32 * s, vx + 2.5 * s, hy + 39 * s, fill="#09090b", width=1)
    canvas.create_arc(cx - 35 * s, hy + 37 * s, cx + 35 * s, hy + 49 * s, start=0, extent=180, outline=chrome, width=2, style=tk.ARC)
    canvas.create_arc(cx - 29 * s, hy + 39 * s, cx + 29 * s, hy + 47 * s, start=0, extent=180, outline="#3f3f46", width=1, style=tk.ARC)
    for seg in (-18, 0, 18):
        canvas.create_line(cx + seg * s, hy + 39 * s, cx + seg * s, hy + 46 * s, fill="#27272a", width=1)

    if watch_state in {"tracking", "locked", "alert"}:
        sx = cx + visor_x
        sy = hy + 3.2 * s + visor_y
        beam = 52 + (24 if watch_state == "locked" else 0) + evo * 18
        ex = sx + gaze_x * beam
        ey = sy + gaze_y * beam
        canvas.create_line(sx, sy, ex, ey, fill=_mix_color(energy if evo > 0.5 else glow, "#ffffff", 0.3), width=6 + int(evo * 2), capstyle=tk.ROUND)
        canvas.create_line(sx, sy, ex, ey, fill=glow, width=2, capstyle=tk.ROUND)
        if evo > 0.5 and watch_state == "locked":
            canvas.create_oval(ex - 8, ey - 8, ex + 8, ey + 8, outline=energy, width=2)


def _draw_vader_full(
    canvas,
    p: dict,
    ox: int,
    oy: int,
    frame: int,
    mode: str,
    progress: float,
    facing: int,
    accent: str,
    *,
    look_angle: float = 0.0,
    watch_state: str = "patrol",
) -> None:
    scale = p["scale"]
    walk_phase = frame * p["speed"]
    phase = walk_phase

    if mode == "walk":
        left_swing, left_lift = _vader_leg_phase(walk_phase, 0.0)
        right_swing, right_lift = _vader_leg_phase(walk_phase, math.pi)
        step = left_swing
        counter_step = right_swing
        step_scale = 1.0
        bob = (left_lift + right_lift) * p["bob"] * 0.68
        lean = math.sin(walk_phase * 0.5) * p["lean"] * 0.8
        pelvis_shift = (left_swing - right_swing) * 5.0 * scale
        torso_tilt = (left_swing - right_swing) * 2.4 * scale
        head_bob = (left_lift - right_lift) * 3.0 * scale
    else:
        damp = {"drag": 0.25, "hover": 0.15, "idle": 0.08, "touch": 0.2}.get(mode, 0.15)
        step = math.sin(phase) * damp
        counter_step = math.sin(phase + math.pi) * damp
        step_scale = damp
        bob = math.sin(phase * 2) * p["bob"] * damp
        lean = math.sin(phase) * p["lean"] * damp
        pelvis_shift = 0.0
        torso_tilt = 0.0
        head_bob = 0.0

    if mode == "touch":
        bob -= math.sin(progress * math.pi) * 14
        lean += facing * math.sin(progress * math.pi) * 11
    elif mode == "hover":
        bob *= 0.42
        lean = facing * 5.5
    elif mode == "idle":
        bob = math.sin(progress * math.tau * 2) * (p["bob"] * 0.75)
        lean *= 0.2

    watch_lean = 0.0
    if watch_state in {"tracking", "locked", "alert"}:
        watch_lean = math.cos(look_angle) * 10 * facing
    elif watch_state == "patrol":
        watch_lean = math.sin(look_angle) * 4

    if mode == "hover":
        lean = facing * 5.5 + watch_lean * 0.5

    cx = ox + ACTOR_W / 2 + lean + watch_lean + pelvis_shift + torso_tilt
    ground = oy + ACTOR_H - 17
    leg_h = 74 * scale
    torso_h = 90 * scale
    shoulder_w = 62 * scale
    waist_w = 40 * scale
    hip_y = ground - leg_h + bob
    chest_y = hip_y - torso_h
    head_y = chest_y - 30 * scale + head_bob
    glow = accent or p["glow"]
    energy = p.get("energy", glow)
    evo = p.get("evolution", 0.0)

    if evo > 0.5:
        for ring_i in range(3):
            ring_r = 68 + ring_i * 22 + math.sin(frame * 0.08 + ring_i) * 6
            canvas.create_oval(
                cx - ring_r, chest_y - ring_r * 0.55,
                cx + ring_r, hip_y + ring_r * 0.35,
                outline=_mix_color(energy, "#ffffff", 0.12 + ring_i * 0.08),
                width=1,
            )

    if mode == "walk":
        shadow_w = 76 * scale + (left_lift + right_lift) * 14
    else:
        shadow_w = 76 * scale + abs(step) * 16
    canvas.create_oval(cx - shadow_w, ground - 6, cx + shadow_w, ground + 6, fill="#cbd5e1", outline="")
    canvas.create_oval(cx - shadow_w * 0.62, ground - 4, cx + shadow_w * 0.62, ground + 4, fill="#94a3b8", outline="")

    cape_sway = math.sin(walk_phase + 0.65) * 16 * scale
    if mode == "walk":
        cape_sway += (left_swing - right_swing) * 5 * scale
    cape_points = (
        cx - shoulder_w * 0.9,
        chest_y + 6 * scale,
        cx + shoulder_w * 0.9,
        chest_y + 6 * scale,
        cx + shoulder_w * 1.18 + cape_sway,
        ground - 6 * scale,
        cx + 18 * scale,
        ground - 24 * scale,
        cx - shoulder_w * 1.14 + cape_sway * 0.35,
        ground - 6 * scale,
    )
    _shaded_poly(canvas, cape_points, p["cloak"])
    canvas.create_line(
        cx - shoulder_w * 0.62,
        chest_y + 18 * scale,
        cx - shoulder_w * 0.98 + cape_sway * 0.3,
        ground - 14 * scale,
        fill=_shift_color(p["cloak"], 0.14),
        width=2,
    )
    canvas.create_line(
        cx + shoulder_w * 0.5,
        chest_y + 20 * scale,
        cx + shoulder_w * 0.92 + cape_sway,
        ground - 14 * scale,
        fill=_shift_color(p["cloak"], -0.28),
        width=2,
    )
    if evo > 0.5:
        canvas.create_line(
            cx - shoulder_w * 0.9, chest_y + 8 * scale,
            cx - shoulder_w * 1.1 + cape_sway * 0.35, ground - 10 * scale,
            fill=_mix_color(energy, "#ffffff", 0.35), width=2,
        )
        canvas.create_line(
            cx + shoulder_w * 0.9, chest_y + 8 * scale,
            cx + shoulder_w * 1.15 + cape_sway, ground - 10 * scale,
            fill=_mix_color(energy, "#ffffff", 0.25), width=2,
        )

    stride = 30 * scale
    knee_drop = 34 * scale
    if mode == "walk":
        left_knee_fwd = left_swing * 15 * scale
        right_knee_fwd = right_swing * 15 * scale
        left_foot_fwd = left_swing * stride + left_lift * 4 * scale
        right_foot_fwd = right_swing * stride + right_lift * 4 * scale
        left_foot_lift = left_lift * 12 * scale
        right_foot_lift = right_lift * 12 * scale
        left_knee_lift = left_lift * 6 * scale
        right_knee_lift = right_lift * 6 * scale
    else:
        left_swing = step
        right_swing = counter_step
        left_lift = _smooth_lift(step)
        right_lift = _smooth_lift(counter_step)
        left_knee_fwd = step * 14 * scale * step_scale
        right_knee_fwd = counter_step * 14 * scale * step_scale
        left_foot_fwd = step * stride * step_scale
        right_foot_fwd = counter_step * stride * step_scale
        left_foot_lift = left_lift * 8 * scale * step_scale
        right_foot_lift = right_lift * 8 * scale * step_scale
        left_knee_lift = left_lift * 4 * scale * step_scale
        right_knee_lift = right_lift * 4 * scale * step_scale

    left_hip = (cx - 20 * scale, hip_y)
    right_hip = (cx + 20 * scale, hip_y)
    left_knee = (cx - 19 * scale + left_knee_fwd, hip_y + knee_drop - left_knee_lift)
    right_knee = (cx + 19 * scale + right_knee_fwd, hip_y + knee_drop - right_knee_lift)
    left_foot = (cx - 22 * scale + left_foot_fwd, ground - left_foot_lift)
    right_foot = (cx + 22 * scale + right_foot_fwd, ground - right_foot_lift)

    for hip, knee, foot, thick in (
        (right_hip, right_knee, right_foot, 12),
        (left_hip, left_knee, left_foot, 13),
    ):
        _line(canvas, (*hip, *knee, *foot), fill=_shift_color(p["boot"], -0.18), width=(thick + 5) * scale)
        _line(canvas, (*hip, *knee, *foot), fill=p["boot"], width=thick * scale)
        kx, ky = knee
        canvas.create_rectangle(kx - 10 * scale, ky - 6 * scale, kx + 10 * scale, ky + 8 * scale, fill="#18181b", outline=p["trim"])
    for fx, fy in (right_foot, left_foot):
        _shaded_oval(canvas, (fx - 18 * scale, fy - 6 * scale, fx + 19 * scale, fy + 7 * scale), p["boot"], outline=p["trim"])
        canvas.create_line(fx - 12 * scale, fy + 1 * scale, fx + 12 * scale, fy + 1 * scale, fill="#27272a", width=2)

    if evo > 0.5 and mode == "walk" and max(left_lift, right_lift) > 0.55:
        for crack_i in range(4):
            crack_x = cx - 28 * scale + crack_i * 18 * scale
            canvas.create_line(crack_x, ground, crack_x + (-1) ** crack_i * 8, ground + 4, fill=_mix_color(energy, "#52525b", 0.3), width=1)

    torso_points = (
        cx - shoulder_w,
        chest_y + 2 * scale,
        cx + shoulder_w,
        chest_y + 2 * scale,
        cx + waist_w,
        hip_y + 10 * scale,
        cx - waist_w,
        hip_y + 10 * scale,
    )
    _shaded_poly(canvas, torso_points, p["body"], outline=p["trim"], width=1)
    canvas.create_polygon(
        cx - shoulder_w * 0.38,
        chest_y + 6 * scale,
        cx + shoulder_w * 0.38,
        chest_y + 6 * scale,
        cx + waist_w * 0.55,
        hip_y + 6 * scale,
        cx - waist_w * 0.55,
        hip_y + 6 * scale,
        fill=p["body_2"],
        outline="",
    )
    for i in range(5):
        yy = chest_y + (18 + i * 11) * scale
        canvas.create_arc(cx - 28 * scale, yy - 8 * scale, cx + 28 * scale, yy + 8 * scale, start=0, extent=180, outline="#3f3f46", width=1)
    canvas.create_polygon(
        cx - 18 * scale,
        chest_y + 34 * scale,
        cx + 18 * scale,
        chest_y + 34 * scale,
        cx + 14 * scale,
        chest_y + 58 * scale,
        cx - 14 * scale,
        chest_y + 58 * scale,
        fill="#111827",
        outline="#52525b",
    )
    for i, color in enumerate(("#ef4444", "#60a5fa", "#22c55e")):
        bx = cx - 12 * scale + i * 9 * scale
        canvas.create_rectangle(bx, chest_y + 48 * scale, bx + 5 * scale, chest_y + 55 * scale, fill=color, outline="")
    canvas.create_rectangle(cx - 24 * scale, chest_y + 36 * scale, cx + 24 * scale, chest_y + 47 * scale, fill="#0a0a0c", outline="#52525b")
    if evo > 0.5:
        reactor_pulse = 0.5 + 0.5 * math.sin(frame * 0.14)
        reactor_r = 10 + reactor_pulse * 4
        canvas.create_oval(cx - reactor_r, chest_y + 38 * scale - reactor_r * 0.3, cx + reactor_r, chest_y + 38 * scale + reactor_r * 0.7, fill="", outline=_mix_color(energy, "#ffffff", 0.4), width=2)
        canvas.create_oval(cx - 6, chest_y + 40 * scale, cx + 6, chest_y + 52 * scale, fill=_mix_color(energy, "#450a0a", 0.2 + reactor_pulse * 0.3), outline="")
        for ring_i in range(3):
            rr = 14 + ring_i * 8 + reactor_pulse * 4
            canvas.create_arc(cx - rr, chest_y + 34 * scale, cx + rr, chest_y + 56 * scale, start=0, extent=180, outline=_mix_color(energy, "#ffffff", 0.2 - ring_i * 0.05), width=1, style=tk.ARC)
    canvas.create_rectangle(cx - waist_w * 0.85, hip_y + 1 * scale, cx + waist_w * 0.85, hip_y + 11 * scale, fill="#18181b", outline=p["trim"])
    canvas.create_rectangle(cx - 8 * scale, hip_y + 2 * scale, cx + 8 * scale, hip_y + 10 * scale, fill="#27272a", outline="")
    canvas.create_rectangle(cx - 5 * scale, hip_y + 12 * scale, cx + 5 * scale, hip_y + 20 * scale, fill="#18181b", outline=p["trim"])

    left_shoulder = (cx - shoulder_w * 0.8, chest_y + 22 * scale)
    right_shoulder = (cx + shoulder_w * 0.8, chest_y + 22 * scale)
    if mode == "walk":
        arm_phase = walk_phase + math.pi * 0.5
        arm_swing = (math.sin(arm_phase) * 0.88 + math.sin(arm_phase * 2) * 0.12) * 24 * scale
        left_hand = (cx - 54 * scale - arm_swing * 0.55, hip_y - 2 * scale + left_lift * 5 * scale)
        right_hand = (cx + 54 * scale + arm_swing * 0.55, hip_y - 2 * scale + right_lift * 5 * scale)
    else:
        arm_swing = math.sin(phase + math.pi) * 18 * scale * step_scale
        left_hand = (cx - 52 * scale - arm_swing * 0.42, hip_y - 2 * scale + left_lift * 5 * scale)
        right_hand = (cx + 52 * scale + arm_swing * 0.42, hip_y - 2 * scale + right_lift * 5 * scale)

    if mode == "hover":
        right_hand = (right_hand[0] + facing * 10 * scale, right_hand[1] - 12 * scale)
        left_hand = (left_hand[0] - facing * 4 * scale, left_hand[1] - 4 * scale)
    if mode == "touch":
        right_hand = (cx + facing * 64 * scale, chest_y + 60 * scale - progress * 32 * scale)

    arm_bend = 1.15 if mode == "walk" else 1.0
    _draw_vader_arm(
        canvas, right_shoulder, right_hand,
        scale=scale, body_color=p["body"], body_2=p["body_2"], trim=p["trim"], bend=arm_bend,
    )
    _draw_vader_arm(
        canvas, left_shoulder, left_hand,
        scale=scale, body_color=p["body"], body_2=p["body_2"], trim=p["trim"], bend=arm_bend,
    )

    for shoulder in (left_shoulder, right_shoulder):
        _shaded_oval(
            canvas,
            (shoulder[0] - 16 * scale, shoulder[1] - 13 * scale, shoulder[0] + 16 * scale, shoulder[1] + 15 * scale),
            p["body_2"],
            outline=p["trim"],
            width=2,
        )
        if evo > 0.5:
            side = 1 if shoulder[0] > cx else -1
            canvas.create_polygon(
                shoulder[0] + side * 14 * scale, shoulder[1] - 10 * scale,
                shoulder[0] + side * 26 * scale, shoulder[1] - 4 * scale,
                shoulder[0] + side * 22 * scale, shoulder[1] + 10 * scale,
                shoulder[0] + side * 10 * scale, shoulder[1] + 6 * scale,
                fill=p.get("body_3", p["body_2"]),
                outline=_mix_color(energy, "#ffffff", 0.2),
                width=1,
            )
    for hand in (left_hand, right_hand):
        _shaded_oval(canvas, (hand[0] - 8 * scale, hand[1] - 8 * scale, hand[0] + 8 * scale, hand[1] + 8 * scale), p["skin"], outline=p["trim"])
        canvas.create_line(hand[0] - 5 * scale, hand[1], hand[0] + 5 * scale, hand[1], fill="#3f3f46", width=1)

    if mode != "touch":
        hilt_x = cx - facing * 28 * scale
        _line(canvas, (hilt_x, hip_y + 14 * scale, hilt_x, hip_y + 34 * scale), fill="#52525b", width=4 * scale)
        canvas.create_rectangle(hilt_x - 5 * scale, hip_y + 12 * scale, hilt_x + 5 * scale, hip_y + 18 * scale, fill="#71717a", outline="")
        canvas.create_oval(hilt_x - 4 * scale, hip_y + 30 * scale, hilt_x + 4 * scale, hip_y + 38 * scale, fill="#27272a", outline="")

    if mode == "touch":
        _draw_weapon(canvas, {**p, "glow": glow}, right_hand, scale, facing, progress)

    head_tilt = torso_tilt * 0.35 if mode == "walk" else watch_lean * 0.15
    _draw_vader_helmet(
        canvas, p, cx, head_y, scale, facing, glow, look_angle, watch_state, head_tilt=head_tilt, frame=frame,
    )

    if watch_state == "alert":
        for ring_i in range(3 if evo > 0.5 else 1):
            ring = 80 + ((frame + ring_i * 4) % 12) * 3 + ring_i * 12
            canvas.create_oval(cx - ring, chest_y - ring * 0.4, cx + ring, chest_y + ring * 0.6, outline=_mix_color(energy if evo > 0.5 else glow, "#ffffff", 0.25 - ring_i * 0.06), width=2)
    if mode == "touch" and evo > 0.5:
        shock_r = 40 + progress * 90
        canvas.create_oval(cx - shock_r, ground - shock_r * 0.2, cx + shock_r, ground + 8, outline=_mix_color(energy, "#ffffff", 0.3), width=2)


def draw_actor(
    canvas,
    character: str,
    frame: int,
    ox: int,
    oy: int,
    *,
    mode: str,
    progress: float,
    facing: int,
    accent: str,
    look_angle: float = 0.0,
    watch_state: str = "patrol",
    charge_level: float = 0.0,
    hull_spin: float = 0.0,
    evolution: float = 1.0,
    cursor_dist: float = 120.0,
) -> None:
    p = _profile(character)
    if p["style"] == "ultimate_core":
        _draw_ultimate_deathstar(
            canvas, p, ox, oy, frame, mode, progress, accent,
            look_angle=look_angle,
            watch_state=watch_state if watch_state != "patrol" else "scan",
            charge_level=charge_level,
            hull_spin=hull_spin,
            evolution=evolution,
            cursor_dist=cursor_dist,
        )
        return
    if p["style"] in {"planet_jupiter", "ultimate_jupiter"}:
        _draw_ultimate_jupiter(
            canvas, p, ox, oy, frame, mode, progress, accent,
            spin=hull_spin,
            look_angle=look_angle,
            watch_state=watch_state if watch_state != "patrol" else "scan",
            charge_level=charge_level,
            evolution=evolution,
            cursor_dist=cursor_dist,
        )
        return
    if p["style"] in {"planet_saturn", "ultimate_saturn"}:
        _draw_ultimate_saturn(
            canvas, p, ox, oy, frame, mode, progress, accent,
            spin=hull_spin,
            look_angle=look_angle,
            watch_state=watch_state if watch_state != "patrol" else "scan",
            charge_level=charge_level,
            evolution=evolution,
            cursor_dist=cursor_dist,
        )
        return
    _draw_humanoid(canvas, p, ox, oy, frame, mode, progress, facing, accent)


class StudySticker:
    def __init__(self):
        from coach import get_startup_brief

        self.coach, self.current_line = get_startup_brief()
        self.key = self.coach["key"]
        self.caption_open = True
        self.drag_x = self.drag_y = 0
        self._dragging = False
        self._click_start = 0.0
        self._last_click = 0.0
        self._reacting = False
        self._reaction_t = 0
        self._frame = 0
        self._wander_x = random.uniform(-12, 12)
        self._wander_dir = random.choice((-1, 1))
        self._facing = self._wander_dir
        self._hovering = False
        self._hover_x = 0
        self._hover_y = 0
        self._look_angle = -math.pi / 4
        self._watch_state = "patrol"
        self._charge_level = 0.0
        self._hull_spin = 0.0
        self._evolution = 1.0
        self._idle_t = 0
        self._idle_kind: str | None = None
        self._next_idle_frame = self._frame + self._idle_delay_frames()
        self._char_rect = (0, 0, 0, 0)
        self._caption_rect = (0, 0, 0, 0)
        self._particles: list[dict] = []
        self._clock_str = ""

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self._place_corner()

        lines = self._wrap(self.current_line, 42)
        w, h, _, _ = _layout_for(self.key, self.caption_open, len(lines))
        self.canvas = tk.Canvas(self.root, bg=TRANSPARENT, highlightthickness=0, bd=0, width=w, height=h)
        self.canvas.pack()

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.root.configure(bg=TRANSPARENT)
        self.canvas.configure(bg=TRANSPARENT)
        try:
            self.root.attributes("-transparentcolor", TRANSPARENT)
        except tk.TclError:
            pass

        self._refresh_clock()
        self._draw()
        self._keep_topmost()
        self._schedule_nag()
        self._schedule_caption_hide()
        self._schedule_tick()
        self._schedule_animation()

    def _accent(self) -> str:
        return self.coach.get("accent", ACCENT_DEFAULT)

    def _idle_delay_frames(self) -> int:
        seconds = random.randint(IDLE_MIN_SEC, IDLE_MAX_SEC)
        return max(1, int(seconds * 1000 / ANIMATION_MS))

    def _refresh_hover_state(self) -> None:
        """Borderless windows often miss <Leave>; poll the pointer so hover cannot stick."""
        try:
            px = self.root.winfo_pointerx()
            py = self.root.winfo_pointery()
            wx = self.root.winfo_rootx()
            wy = self.root.winfo_rooty()
            ww = self.root.winfo_width()
            wh = self.root.winfo_height()
            if not (wx <= px < wx + ww and wy <= py < wy + wh):
                self._hovering = False
                return
            self._hover_x = px - wx
            self._hover_y = py - wy
            self._hovering = self._hit_character(self._hover_x, self._hover_y)
        except tk.TclError:
            self._hovering = False

    def _update_look(self) -> None:
        style = _profile(self.key)["style"]
        if style not in {"ultimate_core", "planet_jupiter", "ultimate_jupiter", "planet_saturn", "ultimate_saturn"}:
            return
        if self._reacting:
            self._watch_state = "alert"
            self._look_angle = self._facing * math.pi / 4
            self._charge_level = min(1.0, self._charge_level + 0.08)
            return
        if self._dragging:
            self._watch_state = "scan"
            self._look_angle = math.sin(self._frame * 0.04) * 0.6
            self._charge_level *= 0.92
            return
        if self._hovering:
            _, _, sw, sh, ox, oy = self._char_base()
            char_cx = ox + sw / 2
            char_cy = oy + sh / 3
            self._look_angle = math.atan2(self._hover_y - char_cy, self._hover_x - char_cx)
            dist = math.hypot(self._hover_x - char_cx, self._hover_y - char_cy)
            self._watch_state = "locked" if dist < 55 else "tracking"
            self._charge_level = min(1.0, self._charge_level + (0.06 if dist < 55 else 0.03))
            return
        self._watch_state = "scan"
        self._look_angle = math.sin(self._frame * 0.035) * 0.9 + self._facing * 0.3
        self._charge_level *= 0.96
        self._evolution = _evolution_power(self._watch_state, self._charge_level, self._reacting, self._frame, _profile(self.key).get("evolution", 1.0))

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
        ew, eh, sw, sh = _layout_for(self.key, self.caption_open, len(lines))
        cap_h = 52 + len(lines) * 15 if self.caption_open else 0
        ox = (ew - sw) // 2 + round(self._wander_x)
        oy = cap_h + 16
        return ew, eh, sw, sh, ox, oy

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
        style = _profile(self.key)["style"]
        if style == "sage":
            self._idle_kind = "meditate"
        elif style in {"core", "ultimate_core", "planet_jupiter", "ultimate_jupiter", "planet_saturn", "ultimate_saturn"}:
            self._idle_kind = "orbit"
        elif style == "ranger":
            self._idle_kind = "check"
        else:
            self._idle_kind = "pose"
        self._idle_t = 0

    def _on_animation_frame(self):
        try:
            self._frame += 1
            self._hull_spin += HULL_SPIN
            self._refresh_hover_state()
            self._update_look()
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
                and not self._hovering
                and self._frame >= self._next_idle_frame
            ):
                self._start_idle()

            if not self._dragging:
                p = _profile(self.key)
                pace = max(0.55, p["speed"] * 2.8)
                if self._hovering:
                    pace *= 0.55
                    _, _, sw, _, ox, _ = self._char_base()
                    char_cx = ox + sw // 2
                    if abs(self._hover_x - char_cx) > 8:
                        self._facing = 1 if self._hover_x > char_cx else -1
                elif not self._reacting:
                    self._facing = self._wander_dir
                self._wander_x += self._wander_dir * pace
                if abs(self._wander_x) >= WANDER_LIMIT:
                    self._wander_x = max(-WANDER_LIMIT, min(WANDER_LIMIT, self._wander_x))
                    self._wander_dir *= -1
            self._draw()
        finally:
            self._schedule_animation()

    def _place_corner(self):
        sw = self.root.winfo_screenwidth()
        lines = self._wrap(self.current_line, 42)
        w, h, _, _ = _layout_for(self.key, self.caption_open, len(lines))
        self.root.geometry(f"{w}x{h}+{sw - w - 12}+12")

    def _keep_topmost(self):
        self.root.attributes("-topmost", True)
        self.root.lift()
        self.root.after(4000, self._keep_topmost)

    def _schedule_nag(self):
        self.root.after(random.randint(NAG_MIN_SEC, NAG_MAX_SEC) * 1000, self._do_nag)

    def _do_nag(self):
        from coach import get_coach, get_line, pick_coach_key

        self.key = pick_coach_key()
        self.coach = get_coach(self.key)
        self.current_line = get_line(self.key, "nag")
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
        w, h, _, _ = _layout_for(self.key, self.caption_open, len(lines))
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
        palette = [self._accent(), _profile(self.key)["glow"], "#f8fafc", "#cbd5e1"]
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
        from coach import get_line

        self._reacting = True
        self._reaction_t = 0
        self._idle_kind = None
        self.caption_open = True
        self.current_line = get_line(self.key, "attack")
        self._charge_level = 1.0
        self._spawn_particles(18, px, py)
        self._resize()
        self._draw()
        self._schedule_caption_hide()

    def _on_press(self, event):
        self.drag_x, self.drag_y = event.x, event.y
        self._dragging = False
        self._click_start = time.time()
        if self._hit_character(event.x, event.y):
            self._trigger_reaction(event.x, event.y)

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
            if event.x != self.drag_x:
                self._facing = 1 if event.x > self.drag_x else -1
        lines = self._wrap(self.current_line, 42)
        w, h, _, _ = _layout_for(self.key, self.caption_open, len(lines))
        x = self.root.winfo_x() + event.x - self.drag_x
        y = self.root.winfo_y() + event.y - self.drag_y
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _on_motion(self, event):
        self._hover_x, self._hover_y = event.x, event.y
        self._hovering = self._hit_character(event.x, event.y)
        if self._hovering:
            self._idle_kind = None

    def _on_leave(self, _event):
        self._hovering = False

    def _on_right_click(self, _event):
        from coach import get_coach, get_line, next_coach_key

        self.key = next_coach_key(self.key)
        self.coach = get_coach(self.key)
        self.current_line = get_line(self.key, "startup")
        self.caption_open = True
        self._reacting = True
        self._reaction_t = 0
        self._idle_kind = None
        self._wander_x = 0
        self._look_angle = -math.pi / 4
        self._watch_state = "patrol"
        self._charge_level = 0.0
        self._hull_spin = 0.0
        self._spawn_particles(12)
        self._resize()
        self._draw()
        self._schedule_caption_hide()

    def _draw_card(self, left: int, top: int, right: int, bottom: int):
        c = self.canvas
        c.create_rectangle(left + 1, top + 1, right + 1, bottom + 1, fill="#cbd5e1", outline="")
        c.create_rectangle(left, top, right, bottom, fill=CARD, outline=CARD_BORDER, width=1)

    def _draw_caption(self):
        if not self.caption_open:
            self._caption_rect = (0, 0, 0, 0)
            return
        c = self.canvas
        lines = self._wrap(self.current_line, 42)
        ew, _, _, _, _, _ = self._char_base()
        cx = ew // 2
        accent = self._accent()
        body = "\n".join(lines)

        tw = min(280, max(220, max((len(line) for line in lines), default=18) * 6 + 36))
        th = 48 + len(lines) * 15
        left, top = cx - tw // 2, 4
        right, bottom = cx + tw // 2, top + th

        self._draw_card(left, top, right, bottom)
        c.create_text(left + 12, top + 10, text=self.coach["name"], anchor="nw", fill=accent, font=FONT_LABEL)
        c.create_text(left + 12, top + 26, text=body, anchor="nw", fill=TEXT, font=FONT, width=tw - 24)
        c.create_text(
            right - 12,
            bottom - 10,
            text="double-click to open",
            anchor="se",
            fill=TEXT_MUTED,
            font=FONT_SM,
        )
        self._caption_rect = (left, top, right, bottom)

    def _draw_time(self):
        c = self.canvas
        ew, _, _, _, _, _ = self._char_base()
        top = self._timer_top()
        cx = ew // 2
        c.create_text(cx, top + 10, text=self._clock_str, anchor="n", fill=TEXT_MUTED, font=FONT_BOLD)

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

    def _draw_idle_fx(self, ox: int, oy: int, sw: int, sh: int, mode: str, progress: float):
        if mode not in {"hover", "idle"}:
            return
        c = self.canvas
        profile = _profile(self.key)
        color = self._accent() or profile["glow"]
        cx, cy = ox + sw // 2, oy + sh // 2
        head_y = oy + 45

        if mode == "hover":
            pulse = 1 + math.sin(self._frame * 0.22) * 0.35
            for i in range(3):
                dot_x = cx + (i - 1) * 10
                dot_y = head_y - 24 - abs(math.sin(self._frame * 0.16 + i)) * 5
                radius = 2.5 * pulse
                c.create_oval(dot_x - radius, dot_y - radius, dot_x + radius, dot_y + radius, fill=color, outline="")
            return

        wave = math.sin(progress * math.tau)
        if self._idle_kind == "meditate":
            for i in range(4):
                radius = 34 + i * 18 + wave * 5
                c.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline=color, width=1)
            for i in range(5):
                angle = progress * math.tau + i * 1.26
                px = cx + math.cos(angle) * (38 + i * 6)
                py = cy - 42 + math.sin(angle) * 18
                c.create_oval(px - 3, py - 3, px + 3, py + 3, fill=color, outline="")
            return

        if self._idle_kind == "scan":
            sweep = (progress * 2) % 1
            x = ox + 20 + sweep * (sw - 40)
            c.create_line(x, oy + 25, x, oy + sh - 42, fill=color, width=2)
            for i in range(6):
                angle = progress * math.tau + i * math.pi / 3
                px = cx + math.cos(angle) * (72 + i * 4)
                py = cy + math.sin(angle) * 34
                c.create_oval(px - 4, py - 4, px + 4, py + 4, fill=color, outline="")
            if profile["style"] == "ultimate_core":
                _draw_hex_grid(c, cx, cy - 10, 58 + progress * 18, self._frame, self._evolution, profile.get("shield", color))
                px = cx + self._facing * (48 + progress * 30)
                py = cy - 20
                _draw_target_planet(c, px, py, 12 + progress * 4, progress * 0.4, self._frame, self._evolution)
            return

        if self._idle_kind == "orbit":
            for i in range(6):
                angle = progress * math.tau + i * (math.tau / 6)
                orbit_r = 52 + i * 6
                px = cx + math.cos(angle) * orbit_r
                py = cy + math.sin(angle) * orbit_r * 0.35
                c.create_oval(px - 3, py - 3, px + 3, py + 3, fill=color, outline="")
            label = "ORBIT"
            if profile["style"] in {"planet_saturn", "ultimate_saturn"}:
                c.create_arc(cx - 88, cy - 24, cx + 88, cy + 24, start=0, extent=359, outline=_mix_color(color, "#ffffff", 0.25), width=2, style=tk.ARC)
                for i in range(8):
                    ang = progress * math.tau + i * 0.78
                    c.create_oval(cx + math.cos(ang) * 82 - 2, cy + math.sin(ang) * 22 - 2, cx + math.cos(ang) * 82 + 2, cy + math.sin(ang) * 22 + 2, fill=color, outline="")
                label = "ULTIMATE RINGS"
            elif profile["style"] in {"planet_jupiter", "ultimate_jupiter"}:
                for i in range(5):
                    c.create_arc(cx - 50 - i * 8, cy - 50 - i * 8, cx + 50 + i * 8, cy + 50 + i * 8, start=20, extent=140, outline=_mix_color(color, "#ffffff", 0.15), width=1, style=tk.ARC)
                label = "ULTIMATE STORM"
            elif profile["style"] == "ultimate_core":
                label = "ULTIMATE SCAN"
            c.create_text(cx, oy + 18, text=label, fill=color, font=FONT_HUD)
            return

        if self._idle_kind == "check":
            sight_y = head_y + 14 + wave * 5
            c.create_line(cx - 47, sight_y, cx + 47, sight_y, fill=color, width=2)
            c.create_line(cx - 47, sight_y - 8, cx - 47, sight_y + 8, fill=color, width=2)
            c.create_line(cx + 47, sight_y - 8, cx + 47, sight_y + 8, fill=color, width=2)
            return

        r = 24 + abs(wave) * 10
        c.create_arc(cx - r, cy - r, cx + r, cy + r, start=35, extent=235, outline=color, width=2)
        c.create_line(cx + self._facing * 26, cy + 18, cx + self._facing * 82, cy - 42, fill=color, width=3)

    def _draw_reaction_fx(self, ox: int, oy: int, sw: int, sh: int):
        if not self._reacting:
            return
        c = self.canvas
        profile = _profile(self.key)
        color = self._accent() or profile["glow"]
        progress = min(1.0, self._reaction_t / max(1, REACTION_FRAMES - 1))
        cx, cy = ox + sw // 2, oy + sh // 2
        pulse = math.sin(progress * math.pi)
        radius = 18 + progress * 78

        if profile["fx"] == "calm":
            for i in range(3):
                r = radius + i * 20
                c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=color, width=2)
            c.create_text(cx, oy + 24, text="focus", fill=color, font=FONT_LABEL)
            return

        if profile["fx"] in {"laser", "annihilator"}:
            beam_h = 6 if profile["fx"] == "annihilator" else 3
            for layer, width, mix in ((beam_h + 14, color, 0.5), (beam_h + 6, color, 0.3), (beam_h, profile.get("laser_core", "#ecfccb"), 0.0)):
                c.create_rectangle(0, cy - width // 2, ox + sw + 45 + progress * 96, cy + width // 2, fill=_mix_color(color, "#ffffff", mix), outline="")
            for ring_i in range(5 if profile["fx"] == "annihilator" else 1):
                r = radius + ring_i * 22
                c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=_mix_color(color, "#ef4444", ring_i * 0.1), width=2)
            if profile["fx"] == "annihilator":
                blast_x = ox + sw + 60 + progress * 80
                _draw_target_planet(c, blast_x, cy, 16 + progress * 10, min(1.0, progress * 1.2), self._frame, 1.0)
            return

        if profile["fx"] == "storm_burst":
            spot_col = profile.get("spot", color)
            for ring_i in range(7):
                r = 14 + progress * (48 + ring_i * 18)
                c.create_oval(cx + 12 - r, cy - r * 0.55, cx + 12 + r, cy + r * 0.55, outline=_mix_color(spot_col, "#ffffff", 0.38 - ring_i * 0.05), width=2)
            for i in range(4):
                ang = progress * math.pi + i * 1.2
                c.create_line(cx + 12, cy, cx + 12 + math.cos(ang) * (30 + progress * 60), cy + math.sin(ang) * (20 + progress * 40), fill=_mix_color(spot_col, color, 0.4), width=2)
            c.create_text(cx, oy + 20, text="ULTIMATE STORM", fill=spot_col, font=FONT_LABEL)
            return

        if profile["fx"] == "ring_pulse":
            for ring_i in range(7):
                rx = 74 + progress * (24 + ring_i * 14)
                ry = 20 + progress * (5 + ring_i * 2)
                c.create_arc(cx - rx, cy - ry, cx + rx, cy + ry, start=0, extent=359, outline=_mix_color(color, "#ffffff", 0.38 - ring_i * 0.05), width=2, style=tk.ARC)
            for i in range(6):
                ang = i * math.tau / 6 + progress * math.tau
                c.create_line(cx, cy, cx + math.cos(ang) * (80 + progress * 40), cy + math.sin(ang) * (22 + progress * 10), fill=_mix_color(color, profile.get("hex_storm", "#d4a574"), 0.3), width=1)
            c.create_text(cx, oy + 20, text="ULTIMATE RINGS", fill=color, font=FONT_LABEL)
            return

        if profile["fx"] == "blaster":
            for i in range(4):
                bx = cx + self._facing * (28 + i * 24 + progress * 46)
                by = cy - 45 + i * 8
                c.create_oval(bx - 6, by - 6, bx + 6, by + 6, fill=color, outline="")
            return

        c.create_arc(
            cx - radius,
            cy - radius,
            cx + radius,
            cy + radius,
            start=205 - pulse * 80,
            extent=110 + pulse * 90,
            outline=color,
            width=3,
            style=tk.ARC,
        )

    def _draw_character(self):
        _, _, sw, sh, ox, oy = self._char_base()
        if self._reacting:
            progress = min(1.0, self._reaction_t / max(1, REACTION_FRAMES - 1))
            mode = "touch"
        elif self._dragging:
            progress = 0.0
            mode = "drag"
        else:
            progress = 0.0
            mode = "walk"

        if self._hovering:
            fx_mode = "hover"
            fx_progress = 0.0
        elif self._idle_kind:
            fx_mode = "idle"
            fx_progress = min(1.0, self._idle_t / max(1, IDLE_FRAMES - 1))
        else:
            fx_mode = mode
            fx_progress = progress

        char_cx = ox + sw // 2
        char_cy = oy + sh // 3
        cursor_dist = math.hypot(self._hover_x - char_cx, self._hover_y - char_cy) if self._hovering else 120.0
        draw_actor(
            self.canvas,
            self.key,
            self._frame,
            ox,
            oy,
            mode=mode,
            progress=progress,
            facing=self._facing,
            accent=self._accent(),
            look_angle=self._look_angle,
            watch_state=self._watch_state,
            charge_level=self._charge_level,
            hull_spin=self._hull_spin,
            evolution=self._evolution,
            cursor_dist=cursor_dist,
        )
        self._char_rect = (ox, oy, ox + sw, oy + sh)
        self._draw_idle_fx(ox, oy, sw, sh, fx_mode, fx_progress)
        self._draw_reaction_fx(ox, oy, sw, sh)

    def _draw(self):
        self.canvas.delete("all")
        self._draw_caption()
        self._draw_character()
        self._draw_time()
        self._draw_particles()

    def run(self):
        self.root.mainloop()


def _snap_sticker(sticker: StudySticker):
    sticker.caption_open = False
    sticker._reacting = False
    sticker._idle_kind = None
    sticker._wander_x = 0
    sticker._place_corner()
    sticker._resize()
    sticker._draw()


def _run_tray(sticker: StudySticker):
    import pystray

    menu = pystray.Menu(
        pystray.MenuItem("Open tracker", lambda *_: _open_app()),
        pystray.MenuItem("Log 2 hours", lambda *_: _quick_log_hours(2.0)),
        pystray.MenuItem("Next coach", lambda *_: sticker._on_right_click(None)),
        pystray.MenuItem("Snap top-right", lambda *_: _snap_sticker(sticker)),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", lambda icon, *_: (icon.stop(), sticker.root.destroy())),
    )
    icon = pystray.Icon("study_coach", _tray_image(), "Study Coach", menu)
    icon.run()


def main():
    if not _acquire_single_instance():
        sys.exit(0)
    sys.path.insert(0, str(ROOT))
    sticker_only = "--sticker-only" in sys.argv
    try:
        from git_sync import notify_data_changed, start_background_sync

        start_background_sync()
    except Exception:
        pass
    if not sticker_only:
        _ensure_streamlit()
        time.sleep(1)
    sticker = StudySticker()
    threading.Thread(target=_run_tray, args=(sticker,), daemon=True).start()
    from coach import get_startup_brief

    coach, line = get_startup_brief()
    _notify(f"{coach['emoji']} {coach['name']}", line)
    sticker.run()


if __name__ == "__main__":
    main()
