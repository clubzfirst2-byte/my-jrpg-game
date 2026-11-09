"""Shared drawing helpers for the object samples (release art, awaiting approval).

The same method as the approved hero (tools/art_proto/pixel.py, tools/hero_release/):
  * every part is a MATERIAL with a 5-tone ramp (0 outline, 1 shadow, 2 core, 3 light, 4 highlight);
  * the light comes from the top left;
  * a selective outline: each outside edge takes the darkest tone of the material it borders.
On top of the Canvas this adds:
  * `stamp` — a hand-placed pixel map (one character per pixel, a legend per sprite);
  * `round_shade` — tones for a rounded part (jar belly, meat, stones) from a top-left light;
  * `layers` — tones by depth from the edge (flames, the sword trail: hot / bright inside);
  * `to_rgba` / `halo` — the finished image as RGBA rows, and a soft glow around lit parts.
"""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "art_proto"))
from pixel import Canvas, hx  # noqa: E402,F401

# Ramps for the objects (outline, shadow, core, light, highlight). The hero's own ramps
# (wood, gold, steel, leather, gem, bone ...) come from pixel.BASE_RAMPS, so the world reads as one set.
RAMPS = {
    # buildings
    "roof": ["#2a0e10", "#6e2a26", "#9c4234", "#c4643f", "#e58f5f"],
    "plaster": ["#3a2e24", "#b2a088", "#ddd0b4", "#efe6d0", "#fcf8ee"],
    "timber": ["#1e1008", "#46291a", "#68422a", "#8a5e3a", "#a87a50"],
    "stone": ["#22222a", "#565664", "#80808c", "#a8a8b2", "#d2d2d8"],
    "glass": ["#101a2c", "#26425e", "#3c6890", "#78a8cc", "#d6eefa"],
    "moss": ["#142010", "#2e4a22", "#4a6e30", "#6e9440", "#9cbc5c"],
    # furniture and props
    "chestwood": ["#2a0e08", "#5e2814", "#8a4220", "#b0623a", "#d08a5a"],
    "clay": ["#2e140c", "#7a3a22", "#b45e36", "#d8845a", "#f0b088"],
    "glaze": ["#0c2428", "#1e5258", "#2e7e80", "#5aaaa4", "#9cdad0"],
    "crate": ["#24140a", "#5a3a1e", "#86592e", "#a87a44", "#c89c62"],
    "ash": ["#141414", "#2c2626", "#463c38", "#5e524c", "#7a6c64"],
    "rune_off": ["#14141c", "#2e2e3a", "#44445a", "#5c5c74", "#74748e"],
    # light and fire (the outline tone is a deep red, not black: fire never reads as a dark shape)
    "fire": ["#6a1606", "#cc3a14", "#f2801e", "#ffcc40", "#fff6c4"],
    "ember": ["#3a0c06", "#8a2010", "#d0461a", "#f08a2a", "#ffd060"],
    "glow": ["#0e2a60", "#2a7ad8", "#5ab8ff", "#a8e4ff", "#f0fcff"],
    # items
    "leaf": ["#0e2210", "#24562a", "#3c8a3a", "#68b84a", "#a8e070"],
    "meat": ["#3a0e10", "#8e2a28", "#c64a3c", "#e8786a", "#ffbcae"],
    "fat": ["#5a3a2a", "#c89a7a", "#ecc8a8", "#f8e2cc", "#fff6ec"],
    "string": ["#3a2a14", "#8a6a3a", "#c8a468", "#e2c890", "#f8ecc8"],
    # the sword trail
    "slash": ["#1a4a8a", "#6ab0f0", "#b8e4ff", "#e8f8ff", "#ffffff"],
}


def canvas(w, h, extra=None):
    return Canvas(w, h, {**RAMPS, **(extra or {})})


def legend(**mats):
    """legend(wood="01234", gold="fghij") -> {char: (material, tone)}."""
    out = {}
    for m, chars in mats.items():
        for i, ch in enumerate(chars):
            if ch != " ":
                out[ch] = (m, i)
    return out


def stamp(c, ox, oy, rows, lg):
    """A hand-placed pixel map; '.' and unknown characters are left as they are."""
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in lg:
                m, t = lg[ch]
                c.put(ox + x, oy + y, m, t)


def unstamp(c, ox, oy, rows, ch="x"):
    """Clear the pixels marked `ch` (cut holes)."""
    for y, row in enumerate(rows):
        for x, k in enumerate(row):
            if k == ch and c.inside(ox + x, oy + y):
                c.mat[oy + y][ox + x] = None


def clear(c, x, y):
    if c.inside(x, y):
        c.mat[y][x] = None
        c.tone[y][x] = None
        c.rgb[y][x] = None


LIGHT = (-0.5, -0.62, 0.6)


def round_shade(c, mat, cx, cy, rx, ry, cuts=(0.93, 0.7, 0.22), box=None):
    """Tone every pixel of `mat` inside the box as if it were part of an ellipsoid lit from the top left."""
    lx, ly, lz = LIGHT
    n = math.sqrt(lx * lx + ly * ly + lz * lz)
    lx, ly, lz = lx / n, ly / n, lz / n
    x0, y0, x1, y1 = box or (int(cx - rx) - 1, int(cy - ry) - 1, int(cx + rx) + 1, int(cy + ry) + 1)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if c.m(x, y) != mat:
                continue
            nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            r2 = nx * nx + ny * ny
            nz = math.sqrt(max(0.0, 1 - min(r2, 1.0)))
            if r2 > 1:
                k = 1 / math.sqrt(r2)
                nx, ny = nx * k, ny * k
            lit = nx * lx + ny * ly + nz * lz
            c.tone[y][x] = 4 if lit > cuts[0] else 3 if lit > cuts[1] else 2 if lit > cuts[2] else 1


def depth_map(c, mat):
    """Distance (in pixels, 4-neighbour) from each pixel of `mat` to the nearest pixel that is not."""
    INF = 999
    d = [[INF if c.mat[y][x] == mat else 0 for x in range(c.w)] for y in range(c.h)]
    changed = True
    while changed:
        changed = False
        for y in range(c.h):
            for x in range(c.w):
                if d[y][x] == 0:
                    continue
                best = min(
                    d[y - 1][x] if y > 0 else 0,
                    d[y + 1][x] if y < c.h - 1 else 0,
                    d[y][x - 1] if x > 0 else 0,
                    d[y][x + 1] if x < c.w - 1 else 0,
                ) + 1
                if best < d[y][x]:
                    d[y][x] = best
                    changed = True
    return d


def layers(c, mat, tones_by_depth, bias=None):
    """Tone `mat` by depth from its edge: tones_by_depth[0] on the edge, the last one deep inside.
    `bias(x, y)` may add to the depth (e.g. flames are hotter low down)."""
    d = depth_map(c, mat)
    for y in range(c.h):
        for x in range(c.w):
            if c.mat[y][x] != mat:
                continue
            k = d[y][x] - 1 + (bias(x, y) if bias else 0)
            k = max(0, min(len(tones_by_depth) - 1, int(k)))
            c.tone[y][x] = tones_by_depth[k]


def to_rgba(c, outline=True):
    """RGBA rows. outline=False skips the selective outline (used for soft FX)."""
    if outline:
        return c.colours()
    out = [[None] * c.w for _ in range(c.h)]
    for y in range(c.h):
        for x in range(c.w):
            m = c.mat[y][x]
            if m is None:
                continue
            if c.rgb[y][x] is not None:
                out[y][x] = c.rgb[y][x] + (255,)
            else:
                t = c.tone[y][x] if c.tone[y][x] is not None else 2
                out[y][x] = c.ramps[m][t] + (255,)
    return out


def halo(img, colour, alpha=90, reach=1, only=None):
    """A soft glow: empty pixels within `reach` of a pixel whose colour is in `only` (or any pixel)."""
    h, w = len(img), len(img[0])
    rgb = hx(colour) if isinstance(colour, str) else colour
    src = [(x, y) for y in range(h) for x in range(w) if img[y][x] and (only is None or img[y][x][:3] in only)]
    add = {}
    for x, y in src:
        for dy in range(-reach, reach + 1):
            for dx in range(-reach, reach + 1):
                X, Y = x + dx, y + dy
                if 0 <= X < w and 0 <= Y < h and img[Y][X] is None and abs(dx) + abs(dy) <= reach:
                    a = alpha if abs(dx) + abs(dy) <= 1 else alpha // 2
                    add[(X, Y)] = max(add.get((X, Y), 0), a)
    for (x, y), a in add.items():
        img[y][x] = rgb + (a,)
    return img


def check_rows(rows, w, name):
    for i, r in enumerate(rows):
        assert len(r) == w, f"{name}: row {i} is {len(r)} wide, not {w}: {r!r}"
