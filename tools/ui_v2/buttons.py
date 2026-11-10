"""Round HUD action buttons (glass discs with a pixel rim) and their icons. 1 art px = 1 CSS px.

Rings come in the exact diameters the HUD uses at its three button sizes (--btn 0.85 / 1 / 1.15, see
src/styles.css), so they are never resampled:
  attack (gold rim)      66 78 90
  ability (teal rim)     44 52 60
  jump                   51 60 69
  dodge                  49 58 67
  bow, guard             44 52 60
  dash                   44 48 55
  ⇄ (ability-next)       44
Icons are drawn per size (20 / 26 / 34 px) from the same shapes, rasterised without anti-aliasing,
then lit from the top left and outlined: they stay crisp at every size.
"""

import math

from PIL import Image, ImageDraw

from common import col, new, outline, side

RIM = {"std": "steel", "gold": "gold", "teal": "ruin_glow"}
RING_SIZES = {
    "gold": (66, 78, 90),
    "teal": (44, 52, 60),
    "std": (44, 48, 49, 51, 52, 55, 58, 60, 67, 69),
}


def ring(d, variant, pressed):
    im = new(d, d)
    c = (d - 1) / 2
    R = d / 2
    rim = RIM[variant]
    for y in range(d):
        for x in range(d):
            dx, dy = x - c, y - c
            dist = math.hypot(dx, dy)
            e = R - dist  # depth from the outer edge
            if e < 0.5:
                continue
            nx, ny = (dx / dist, dy / dist) if dist else (0, 0)
            lit = -(nx + ny) / math.sqrt(2)  # +1 top-left .. -1 bottom-right
            if pressed:
                lit = -lit
            if e < 1.5:
                im.putpixel((x, y), col("navy", 0))
            elif e < 3.5:
                t = 4 if lit > 0.75 else 3 if lit > 0.15 else 2 if lit > -0.45 else 1
                im.putpixel((x, y), col(rim, t))
            elif e < 4.5:
                im.putpixel((x, y), col("navy", 0))
            else:
                # dark, dense glass (inspection M-2: at alpha 150 snow and sand turned it light grey and the
                # cream icons sank): alpha 215, a navy that keeps the icons readable on any ground
                if pressed:
                    im.putpixel((x, y), col(rim if variant != "std" else "gem", 1, 230))
                else:
                    im.putpixel((x, y), col("navy", 1, 215))
                # the glass: a crescent of light on the upper left, inside the rim
                if not pressed and 4.5 <= e < 7.0 and lit > 0.6:
                    im.putpixel((x, y), col("navy", 4, 235))
    return im


# ---------------------------------------------------------------- icons: shapes in a unit square

def _seg(draw, s, a, b, w):
    """A thick segment from a to b (unit coords), width w (unit), as a polygon."""
    (x0, y0), (x1, y1) = a, b
    L = math.hypot(x1 - x0, y1 - y0)
    px, py = -(y1 - y0) / L * w / 2, (x1 - x0) / L * w / 2
    pts = [(x0 + px, y0 + py), (x1 + px, y1 + py), (x1 - px, y1 - py), (x0 - px, y0 - py)]
    draw.polygon([(u * s, v * s) for u, v in pts], fill=1)


def _poly(draw, s, pts):
    draw.polygon([(u * s, v * s) for u, v in pts], fill=1)


def _arc(draw, s, cx, cy, r, w, a0, a1, steps=48):
    for i in range(steps):
        t0 = math.radians(a0 + (a1 - a0) * i / steps)
        t1 = math.radians(a0 + (a1 - a0) * (i + 1) / steps)
        _seg(draw, s, (cx + r * math.cos(t0), cy + r * math.sin(t0)), (cx + r * math.cos(t1), cy + r * math.sin(t1)), w)


def _ellipse(draw, s, cx, cy, rx, ry):
    draw.ellipse([(cx - rx) * s, (cy - ry) * s, (cx + rx) * s, (cy + ry) * s], fill=1)


def shape(name, draw, s):
    if name == "attack":  # a sword, point up-right
        _seg(draw, s, (0.40, 0.60), (0.86, 0.14), 0.16)
        _poly(draw, s, [(0.80, 0.08), (0.92, 0.08), (0.92, 0.20)])
        _seg(draw, s, (0.20, 0.48), (0.52, 0.80), 0.12)
        _seg(draw, s, (0.36, 0.64), (0.16, 0.84), 0.11)
        _ellipse(draw, s, 0.13, 0.87, 0.07, 0.07)
    elif name == "jump":  # an arrow up over the ground
        _poly(draw, s, [(0.50, 0.06), (0.88, 0.46), (0.64, 0.46), (0.64, 0.70), (0.36, 0.70), (0.36, 0.46), (0.12, 0.46)])
        _seg(draw, s, (0.12, 0.86), (0.88, 0.86), 0.12)
    elif name == "dodge":  # a rolling arrow (three-quarter turn)
        _arc(draw, s, 0.50, 0.52, 0.30, 0.14, 150, 420)
        _poly(draw, s, [(0.62, 0.02), (0.92, 0.26), (0.58, 0.40)])
    elif name == "bow":  # a drawn bow, side on: the limb ")" bowed forward, the string pulled back to a point
        # (a ">" shape, open in the middle), the arrow on the string pointing right, its head past the limb
        _arc(draw, s, -0.14, 0.50, 0.64, 0.13, -46, 46, 32)  # the limb
        _seg(draw, s, (0.30, 0.04), (0.10, 0.50), 0.06)  # the string, pulled back
        _seg(draw, s, (0.10, 0.50), (0.30, 0.96), 0.06)
        _seg(draw, s, (0.08, 0.50), (0.80, 0.50), 0.08)  # the arrow's shaft
        _poly(draw, s, [(0.98, 0.50), (0.76, 0.34), (0.76, 0.66)])  # its head
    elif name == "guard":  # a heater shield
        _poly(draw, s, [(0.16, 0.12), (0.84, 0.12), (0.84, 0.50), (0.50, 0.92), (0.16, 0.50)])
    elif name == "dash":  # two chevrons, forward
        for x0 in (0.10, 0.44):
            _poly(draw, s, [(x0, 0.16), (x0 + 0.18, 0.16), (x0 + 0.46, 0.50), (x0 + 0.18, 0.84), (x0, 0.84), (x0 + 0.28, 0.50)])
    elif name == "ability":  # the star ring
        _arc(draw, s, 0.50, 0.50, 0.38, 0.11, 0, 360, 64)
        _poly(draw, s, [(0.50, 0.18), (0.58, 0.42), (0.82, 0.50), (0.58, 0.58), (0.50, 0.82), (0.42, 0.58), (0.18, 0.50), (0.42, 0.42)])
    elif name == "swap":  # ⇄
        _seg(draw, s, (0.14, 0.32), (0.80, 0.32), 0.12)
        _poly(draw, s, [(0.94, 0.32), (0.70, 0.12), (0.70, 0.52)])
        _seg(draw, s, (0.20, 0.70), (0.86, 0.70), 0.12)
        _poly(draw, s, [(0.06, 0.70), (0.30, 0.50), (0.30, 0.90)])
    elif name == "pause":  # two bars
        draw.rectangle([0.22 * s, 0.14 * s, 0.42 * s - 1, 0.86 * s - 1], fill=1)
        draw.rectangle([0.58 * s, 0.14 * s, 0.78 * s - 1, 0.86 * s - 1], fill=1)
    elif name == "bag":  # a tied pouch
        _ellipse(draw, s, 0.50, 0.62, 0.36, 0.30)
        _poly(draw, s, [(0.36, 0.20), (0.64, 0.20), (0.58, 0.40), (0.42, 0.40)])
        _seg(draw, s, (0.30, 0.38), (0.70, 0.38), 0.08)
        _ellipse(draw, s, 0.50, 0.14, 0.12, 0.08)
    elif name == "close":  # ×
        _seg(draw, s, (0.18, 0.18), (0.82, 0.82), 0.16)
        _seg(draw, s, (0.82, 0.18), (0.18, 0.82), 0.16)


ICONS = ("attack", "jump", "dodge", "bow", "guard", "dash", "ability", "swap", "pause", "bag", "close")
ICON_SIZES = (20, 26, 34)
ACCENT = {"attack": "gold", "ability": "ruin_glow"}  # the rest: pale bone


def icon(name, size):
    """Rasterise the shape inside a 1 px margin, then tone it (lit top-left edges, shaded bottom-right) and
    outline it in navy, so it reads on the glass and on bright ground."""
    inner = size - 2
    m1 = Image.new("1", (inner, inner), 0)
    shape(name, ImageDraw.Draw(m1), inner)
    mask = [[m1.getpixel((x, y)) != 0 for x in range(inner)] for y in range(inner)]
    mat = ACCENT.get(name, "bone")
    im = new(size, size)
    for y in range(inner):
        for x in range(inner):
            if not mask[y][x]:
                continue
            sd = side(mask, x, y)
            t = 4 if sd == "tl" else 2 if sd == "br" else 3
            if mat == "bone":
                t = {4: 4, 3: 3, 2: 2}[t]
            im.putpixel((x + 1, y + 1), col(mat, t))
    if name == "bow":  # the string in a darker tone, so the limb and the arrow read as the bow's parts
        m2 = Image.new("1", (inner, inner), 0)
        d2 = ImageDraw.Draw(m2)
        _seg(d2, inner, (0.30, 0.04), (0.10, 0.50), 0.06)
        _seg(d2, inner, (0.10, 0.50), (0.30, 0.96), 0.06)
        m3 = Image.new("1", (inner, inner), 0)
        d3 = ImageDraw.Draw(m3)
        _arc(d3, inner, -0.14, 0.50, 0.64, 0.13, -46, 46, 32)
        _seg(d3, inner, (0.08, 0.50), (0.80, 0.50), 0.08)
        for y in range(inner):
            for x in range(inner):
                if m2.getpixel((x, y)) and not m3.getpixel((x, y)):
                    im.putpixel((x + 1, y + 1), col("bone", 1))
    if name == "guard":  # the shield's emblem: a gem band down the middle
        for y in range(size):
            for x in (size // 2 - 1, size // 2):
                if im.getpixel((x, y))[3] and 0.22 * size < y < 0.78 * size:
                    im.putpixel((x, y), col("gem", 3 if x < size // 2 else 2))
    outline(im, col("navy", 0))
    return im
