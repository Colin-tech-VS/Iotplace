"""Generate PNG brand assets from the Iotplace hex mark (favicon, OG, schema logo)."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "vitrine" / "static" / "brand"
BG = (6, 10, 18)
CYAN = (56, 189, 248)
GREEN = (74, 222, 128)


def hex_points(cx: float, cy: float, radius: float) -> list[tuple[float, float]]:
    return [
        (
            cx + radius * math.cos(math.pi / 6 + i * math.pi / 3),
            cy + radius * math.sin(math.pi / 6 + i * math.pi / 3),
        )
        for i in range(6)
    ]


def draw_mark(draw: ImageDraw.ImageDraw, cx: float, cy: float, radius: float, stroke: int) -> None:
    outer = hex_points(cx, cy, radius)
    inner = hex_points(cx, cy, radius * 0.55)
    draw.polygon(outer, outline=CYAN, width=max(2, stroke))
    draw.polygon(inner, fill=(*CYAN, 95))
    dot = radius * 0.14
    draw.ellipse([cx - dot, cy - dot, cx + dot, cy + dot], fill=GREEN)


def render_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (*BG, 255))
    draw = ImageDraw.Draw(img)
    pad = size * 0.12
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=size * 0.22, fill=(*BG, 255))
    draw_mark(draw, size / 2, size / 2, (size / 2) - pad, max(2, size // 16))
    return img


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in ("arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def render_og() -> Image.Image:
    w, h = 1200, 630
    img = Image.new("RGB", (w, h), BG)
    draw = ImageDraw.Draw(img)

    for y in range(h):
        t = y / h
        color = (
            int(BG[0] + (10 * (1 - t))),
            int(BG[1] + (18 * (1 - t))),
            int(BG[2] + (32 * (1 - t))),
        )
        draw.line([(0, y), (w, y)], fill=color)

    draw.ellipse([420, -120, 980, 280], fill=(56, 189, 248, 18))
    draw_mark(draw, w // 2, h // 2 - 40, 92, 6)

    title_font = load_font(86)
    sub_font = load_font(34)
    tag_font = load_font(26)

    title = "Iotplace"
    sub = "B2B IoT Subcontracting Marketplace"
    tag = "Enterprises · Startups · Asia"

    tw = draw.textlength(title, font=title_font)
    draw.text(((w - tw) / 2, h // 2 + 70), title, fill=(226, 232, 240), font=title_font)
    sw = draw.textlength(sub, font=sub_font)
    draw.text(((w - sw) / 2, h // 2 + 175), sub, fill=CYAN, font=sub_font)
    tg = draw.textlength(tag, font=tag_font)
    draw.text(((w - tg) / 2, h // 2 + 230), tag, fill=(148, 163, 184), font=tag_font)

    return img


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    render_icon(32).save(OUT / "favicon-32.png")
    render_icon(180).save(OUT / "apple-touch-icon.png")
    render_icon(512).save(OUT / "logo-512.png")
    render_og().save(OUT / "og-image.png", optimize=True)
    print("Brand assets written to", OUT)


if __name__ == "__main__":
    main()
