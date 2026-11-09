"""Shared drawing helpers for the object samples (release art, awaiting approval).

The same method as the approved hero (tools/art_proto/pixel.py, tools/hero_release/):
  * every part is a MATERIAL with a 5-tone ramp (0 outline, 1 shadow, 2 core, 3 light, 4 highlight);
  * the light comes from the top left;
  * a selective outline: each outside edge takes the darkest tone of the material it borders.
On top of the Canvas this adds:
  * `stamp` — a hand-placed pixel map (one character per pixel, a legend per sprite);
  * `round_shade` — tones for a rounded part (jar belly, meat, stones) from a top-left light;
  * `layers` — tones by depth from the edge (flames, the sword trail: hot / bright inside);
  * `to_rgba` — the finished image as RGBA rows (every pixel fully opaque or fully clear: guide 1.1, 6.2).
"""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "art_proto"))
from pixel import Canvas, hx  # noqa: E402,F401

# Ramps for the objects (outline, shadow, core, light, highlight).
# Reused as they are (ART_STYLE_GUIDE.md 2.1 / 2.5 / 6.2): the hero's wood, gold, steel, leather, gem, bone
# (pixel.BASE_RAMPS), ruin.stone, ruin.glow and the fire colours. Every other ramp here is NEW and is listed
# in OBJECT_PROPOSAL.md for the art director to register in the guide (chapter 2) after approval.
GUIDE = {
    "ruin_stone": ["#1a1e22", "#3a4246", "#5a6468", "#7c8688", "#a2aaaa"],  # guide 2.5 ruin.stone
    "ruin_glow": ["#08302e", "#146a64", "#22a49a", "#62d6c6", "#c6fff0"],  # guide 2.5 ruin.glow
    "fire": ["#5a1a0a", "#c0461c", "#f08a3a", "#ffd060", "#fff4c8"],  # guide 6.2 flames
}
NEW = {
    # buildings
    "roof": ["#2a0e10", "#6e2a26", "#9c4234", "#c4643f", "#e58f5f"],  # village roof tiles
    "plaster": ["#3a2e24", "#b2a088", "#ddd0b4", "#efe6d0", "#fcf8ee"],  # outside walls (lighter than room.plaster)
    "stone": ["#22222a", "#565664", "#80808c", "#a8a8b2", "#d2d2d8"],  # village / field stone (not the ruin)
    "glass": ["#101a2c", "#26425e", "#3c6890", "#78a8cc", "#d6eefa"],  # window panes
    "moss": ["#142010", "#2e4a22", "#4a6e30", "#6e9440", "#9cbc5c"],  # small patches on stone
    # furniture and props
    "chestwood": ["#2a0e08", "#5e2814", "#8a4220", "#b0623a", "#d08a5a"],  # red-brown furniture wood
    "clay": ["#2e140c", "#7a3a22", "#b45e36", "#d8845a", "#f0b088"],  # terracotta
    "glaze": ["#0c2428", "#1e5258", "#2e7e80", "#5aaaa4", "#9cdad0"],  # painted teal (jar band, shutters)
    "crate": ["#24140a", "#5a3a1e", "#86592e", "#a87a44", "#c89c62"],  # light crate wood
    "ash": ["#141414", "#2c2626", "#463c38", "#5e524c", "#7a6c64"],  # ash, charcoal, dark gaps
    # items
    "leaf": ["#0e2210", "#24562a", "#3c8a3a", "#68b84a", "#a8e070"],  # herbs, small plants
    "meat": ["#3a0e10", "#8e2a28", "#c64a3c", "#e8786a", "#ffbcae"],  # raw meat
    "fat": ["#5a3a2a", "#c89a7a", "#ecc8a8", "#f8e2cc", "#fff6ec"],  # fat on meat
    "string": ["#3a2a14", "#8a6a3a", "#c8a468", "#e2c890", "#f8ecc8"],  # twine
    # the sword trail (white and sky blue, the hero's colours: guide 6.2)
    "slash": ["#1a4a8a", "#6ab0f0", "#b8e4ff", "#e8f8ff", "#ffffff"],
}
RAMPS = {**GUIDE, **NEW}


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


def check_rows(rows, w, name):
    for i, r in enumerate(rows):
        assert len(r) == w, f"{name}: row {i} is {len(r)} wide, not {w}: {r!r}"
