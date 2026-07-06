"""Build AR-filter style sticker frames — 3D poses with lean/bounce animation."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PIL import Image

OUT_DIR = ROOT / "assets" / "stickers"
SOURCE_DIR = OUT_DIR / "sources"
TARGET_HEIGHT = 340
FRAME_COUNT = 4

# dx, dy, scale — mimics AR filter idle animation
AR_POSES = (
    (0, 0, 1.00),
    (-10, -6, 1.03),
    (0, -12, 1.06),
    (10, -6, 1.03),
)

CHARACTERS = (
    "vader", "deathstar", "dooku", "mando", "anakin", "yoda",
)


def _is_background(r: int, g: int, b: int, tol: int = 34) -> bool:
    brightness = (r + g + b) / 3
    neutral = max(r, g, b) - min(r, g, b) < 28
    if brightness > 238 and neutral:
        return True
    if brightness > 205 and neutral and abs(r - g) < tol and abs(g - b) < tol:
        return True
    return False


def _remove_background(img: Image.Image) -> Image.Image:
    rgba = img.convert("RGBA")
    pixels = rgba.load()
    w, h = rgba.size
    seen: set[tuple[int, int]] = set()
    stack: list[tuple[int, int]] = []

    for x in range(w):
        stack.extend([(x, 0), (x, h - 1)])
    for y in range(h):
        stack.extend([(0, y), (w - 1, y)])

    while stack:
        x, y = stack.pop()
        if (x, y) in seen or x < 0 or y < 0 or x >= w or y >= h:
            continue
        seen.add((x, y))
        r, g, b, _ = pixels[x, y]
        if not _is_background(r, g, b):
            continue
        pixels[x, y] = (r, g, b, 0)
        stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if a and _is_background(r, g, b, tol=22):
                pixels[x, y] = (r, g, b, 0)
    return rgba


def _trim_transparent(img: Image.Image) -> Image.Image:
    bbox = img.getbbox()
    return img.crop(bbox) if bbox else img


def _resize_to_height(img: Image.Image, height: int) -> Image.Image:
    w, h = img.size
    scale = height / h
    return img.resize((max(1, int(w * scale)), height), Image.Resampling.LANCZOS)


def _load_source(character: str) -> Image.Image:
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        path = SOURCE_DIR / f"{character}{ext}"
        if path.exists():
            return Image.open(path)
    raise FileNotFoundError(f"No source art for {character} in {SOURCE_DIR}")


def prepare_character(character: str) -> Image.Image:
    img = _load_source(character)
    img = _remove_background(img)
    img = _trim_transparent(img)
    return _resize_to_height(img, TARGET_HEIGHT)


def render_frames(base: Image.Image) -> list[Image.Image]:
    pad = 24
    raw: list[Image.Image] = []
    max_w = max_h = 0
    for dx, dy, scale in AR_POSES:
        w, h = base.size
        nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
        scaled = base.resize((nw, nh), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (nw + pad * 2, nh + pad * 2), (0, 0, 0, 0))
        canvas.paste(scaled, (pad + dx, pad + dy), scaled)
        trimmed = _trim_transparent(canvas)
        raw.append(trimmed)
        max_w = max(max_w, trimmed.size[0])
        max_h = max(max_h, trimmed.size[1])

    frames = []
    for img in raw:
        unified = Image.new("RGBA", (max_w, max_h), (0, 0, 0, 0))
        x = (max_w - img.size[0]) // 2
        y = max_h - img.size[1]
        unified.paste(img, (x, y), img)
        frames.append(unified)
    return frames


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    for character in CHARACTERS:
        base = prepare_character(character)
        for i, frame in enumerate(render_frames(base)[:FRAME_COUNT]):
            path = OUT_DIR / f"{character}_{i}.png"
            frame.save(path, "PNG")
            count += 1
            print(f"{path.name}  {frame.size[0]}x{frame.size[1]}")
    print(f"Generated {count} AR frames in {OUT_DIR}")


if __name__ == "__main__":
    main()