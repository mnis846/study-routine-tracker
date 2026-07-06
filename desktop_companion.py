"""
Minimal study coach widget — character, message, timer. Touch to interact.
"""

from __future__ import annotations

import math
import random
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
NAG_MIN_SEC = 3 * 60
NAG_MAX_SEC = 6 * 60
CAPTION_MS = 14000
ATTACK_FRAMES = 28
TIMER_STRIP_H = 28
TRANSPARENT = "#010203"

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

from sticker_sprites import asset_path, assets_available, draw_sprite, image_pixel_size


def _layout_for(character: str, caption_open: bool, line_count: int = 1) -> tuple[int, int, int, int]:
    sw, sh = image_pixel_size(character)
    pad = 32
    cap_h = 0 if not caption_open else 52 + line_count * 15
    w = max(sw + pad, 272)
    h = cap_h + sh + TIMER_STRIP_H + 18
    return w, h, sw, sh


def _notify(title: str, message: str) -> None:
    try:
        from plyer import notification

        notification.notify(title=title, message=message, app_name="Study Coach", timeout=10)
    except Exception:
        pass


def _ensure_streamlit() -> None:
    script = ROOT / "scripts" / "start_tracker.ps1"
    if not script.exists():
        return
    subprocess.Popen(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)],
        cwd=str(ROOT),
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )


def _open_app() -> None:
    webbrowser.open(APP_URL)


def _quick_log_hours(hours: float) -> None:
    sys.path.insert(0, str(ROOT))
    try:
        from coach import get_coach, get_line, pick_coach_key
        from database import add_daily_study_hours, init_db

        init_db()
        add_daily_study_hours(date.today(), hours, "Quick log — widget")
        key = pick_coach_key()
        coach = get_coach(key)
        _notify(coach["name"], f"Logged {hours:g}h. {get_line(key, 'praise')}")
    except Exception as exc:
        _notify("Study Tracker", f"Could not log: {exc}")


def _tray_image():
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([8, 8, 56, 56], fill=(99, 102, 241, 255))
    draw.ellipse([24, 24, 40, 40], fill=(255, 255, 255, 230))
    return img


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
        self._attacking = False
        self._attack_t = 0
        self._char_rect = (0, 0, 0, 0)
        self._caption_rect = (0, 0, 0, 0)
        self._particles: list[dict] = []
        self._photo_cache: dict[tuple[str, int], tk.PhotoImage] = {}
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
        self.canvas.bind("<Button-3>", self._on_right_click)
        self._ensure_assets()
        self.root.configure(bg=TRANSPARENT)
        self.canvas.configure(bg=TRANSPARENT)
        self.root.attributes("-transparentcolor", TRANSPARENT)

        self._refresh_clock()
        self._draw()
        self._keep_topmost()
        self._schedule_nag()
        self._schedule_caption_hide()
        self._schedule_tick()

    def _accent(self) -> str:
        return self.coach.get("accent", ACCENT_DEFAULT)

    def _ensure_assets(self):
        if assets_available():
            return
        import importlib.util

        spec = importlib.util.spec_from_file_location("gen_assets", ROOT / "scripts" / "generate_sticker_assets.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.main()

    def _get_photo(self, character: str, frame_idx: int) -> tk.PhotoImage | None:
        key = (character, frame_idx)
        if key in self._photo_cache:
            return self._photo_cache[key]
        path = asset_path(character, frame_idx)
        if not path.exists():
            return None
        photo = tk.PhotoImage(file=str(path))
        self._photo_cache[key] = photo
        return photo

    def _wrap(self, text: str, width: int) -> list[str]:
        words, lines, line = text.split(), [], []
        for w in words:
            test = " ".join(line + [w])
            if len(test) <= width:
                line.append(w)
            else:
                if line:
                    lines.append(" ".join(line))
                line = [w]
        if line:
            lines.append(" ".join(line))
        return lines[:4]

    def _char_base(self) -> tuple[int, int, int, int, int, int]:
        lines = self._wrap(self.current_line, 42)
        ew, eh, sw, sh = _layout_for(self.key, self.caption_open, len(lines))
        cap_h = 52 + len(lines) * 15 if self.caption_open else 0
        ox = (ew - sw) // 2
        oy = cap_h + 4
        return ew, eh, sw, sh, ox, oy

    def _timer_top(self) -> int:
        _, _, _, sh, _, oy = self._char_base()
        return oy + sh + 6

    def _refresh_clock(self):
        self._clock_str = datetime.now().strftime("%H:%M")

    def _schedule_tick(self):
        self.root.after(30000, self._on_tick)

    def _on_tick(self):
        prev = self._clock_str
        self._refresh_clock()
        if prev != self._clock_str and not self._attacking:
            self._draw()
        self._schedule_tick()

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
        self._resize()
        self._draw()
        _notify(self.coach["name"], self.current_line)
        self._schedule_caption_hide()
        self._schedule_nag()

    def _schedule_caption_hide(self):
        self.root.after(CAPTION_MS, self._hide_caption)

    def _hide_caption(self):
        if self._attacking:
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
        for _ in range(n):
            self._particles.append({
                "x": cx, "y": cy,
                "vx": random.uniform(-2, 2),
                "vy": random.uniform(-3, -1),
                "life": random.randint(8, 18),
                "color": self._accent(),
                "size": random.randint(2, 3),
            })

    def _trigger_attack(self):
        from coach import get_line

        self._attacking = True
        self._attack_t = 0
        self.caption_open = True
        self.current_line = get_line(self.key, "attack")
        self._spawn_particles(8)
        self._resize()
        self._draw()
        self._animate()
        self._schedule_caption_hide()

    def _on_press(self, event):
        self.drag_x, self.drag_y = event.x, event.y
        self._dragging = False
        self._click_start = time.time()
        if self._hit_character(event.x, event.y):
            self._trigger_attack()

    def _on_release(self, event):
        if self._dragging:
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
        w, h, _, _ = _layout_for(self.key, self.caption_open, len(lines))
        x = self.root.winfo_x() + event.x - self.drag_x
        y = self.root.winfo_y() + event.y - self.drag_y
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _on_right_click(self, _event):
        from coach import get_coach, get_line, next_coach_key

        self.key = next_coach_key(self.key)
        self.coach = get_coach(self.key)
        self.current_line = get_line(self.key, "startup")
        self.caption_open = True
        self._attacking = False
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
        ew, _, sw, _, ox, _ = self._char_base()
        cx = ox + sw // 2
        accent = self._accent()
        body = "\n".join(lines)

        tw = min(280, max(220, max((len(l) for l in lines), default=18) * 6 + 36))
        th = 48 + len(lines) * 15
        left, top = cx - tw // 2, 4
        right, bottom = cx + tw // 2, top + th

        self._draw_card(left, top, right, bottom)
        c.create_text(left + 12, top + 10, text=self.coach["name"], anchor="nw", fill=accent, font=FONT_LABEL)
        c.create_text(left + 12, top + 26, text=body, anchor="nw", fill=TEXT, font=FONT, width=tw - 24)
        c.create_text(
            right - 12, bottom - 10, text="double-click to open",
            anchor="se", fill=TEXT_MUTED, font=FONT_SM,
        )
        self._caption_rect = (left, top, right, bottom)

    def _draw_time(self):
        c = self.canvas
        ew, _, sw, _, ox, _ = self._char_base()
        top = self._timer_top()
        cx = ox + sw // 2
        c.create_text(cx, top + 10, text=self._clock_str, anchor="n", fill=TEXT_MUTED, font=FONT_BOLD)

    def _draw_particles(self):
        alive = []
        for p in self._particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.12
            p["life"] -= 1
            if p["life"] > 0:
                alive.append(p)
                self.canvas.create_oval(
                    p["x"] - p["size"], p["y"] - p["size"],
                    p["x"] + p["size"], p["y"] + p["size"],
                    fill=p["color"], outline="",
                )
        self._particles = alive

    def _draw_attack_fx(self, ox: int, oy: int, sw: int, sh: int):
        c = self.canvas
        color = self.coach.get("saber", self._accent())
        t = self._attack_t
        cx, cy = ox + sw // 2, oy + sh // 2
        r = 16 + t * 5
        c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=color, width=2)
        kind = self.coach.get("attack", "saber")
        if kind == "saber":
            c.create_line(ox + sw - 10, oy + 30, ox + sw + 50 + t * 4, oy - 30, fill=color, width=3, capstyle=tk.ROUND)
        elif kind == "laser":
            c.create_rectangle(0, cy - 2, ox + sw + 60 + t * 6, cy + 2, fill=color, outline="")

    def _draw_character(self):
        _, _, sw, sh, ox, oy = self._char_base()

        if self._attacking:
            oy -= int(abs(math.sin(self._attack_t * 0.55)) * 16)
            ox += int(math.sin(self._attack_t * 0.4) * 12)

        photo = self._get_photo(self.key, 0)
        if photo:
            self.canvas.create_image(ox, oy, image=photo, anchor="nw")
        else:
            draw_sprite(self.canvas, self.key, 0, ox, oy, bob=0)

        self._char_rect = (ox, oy, ox + sw, oy + sh)
        if self._attacking:
            self._draw_attack_fx(ox, oy, sw, sh)

    def _draw(self):
        self.canvas.delete("all")
        self._draw_caption()
        self._draw_character()
        self._draw_time()
        self._draw_particles()

    def _needs_animation(self) -> bool:
        return self._attacking or bool(self._particles)

    def _animate(self):
        if self._attacking:
            self._attack_t += 1
            if self._attack_t >= ATTACK_FRAMES:
                self._attacking = False
        self._draw()
        if self._needs_animation():
            self.root.after(40, self._animate)

    def run(self):
        self.root.mainloop()


def _snap_sticker(sticker: StudySticker):
    sticker.caption_open = False
    sticker._attacking = False
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