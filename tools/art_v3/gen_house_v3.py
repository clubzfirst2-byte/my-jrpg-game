"""v3 pilot: one house at density 4 — a new kind (STYLE.md 7): two storeys, a stone ground floor and
a timber-framed upper floor under a clay-tile roof. 192 x 224 (game 48 x 56, the v1 house's footprint:
3 tiles wide), the door's sill on the bottom row's centre (the anchor, like obj.house).

Detail that needs 2x: single roof tiles with a lit upper edge and a shadow lip, mortar between stones,
wood grain on beams and planks, glass with a reflection, iron hinges, a flower box with petals.
Writes src/art-release-v3/objects/obj.v3.house_stone.png
Run: python3 tools/art_v3/gen_house_v3.py
"""

import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402

from v3lib import ROOT, Canvas, save  # noqa: E402
from gen_nature_v3 import LEAF, PINK, YELLOW, hsh  # noqa: E402

OUT = os.path.join(ROOT, "src", "art-release-v3", "objects")
W, H = 192, 224
G = H - 1
RAMPS = {
    "roof": ["#3a1208", "#6a2412", "#86321a", "#a24020", "#bc5a30", "#d8804e"],
    "stone": ["#24222a", "#4a4650", "#5e5a64", "#77727a", "#938d92", "#b4aeb0"],
    "plaster": ["#4e4636", "#b4a888", "#cfc4a4", "#e8dec2", "#f6efdc", "#fffaf0"],
    "timber": ["#1e1008", "#4a2c16", "#5c3a1e", "#6e4424", "#906038", "#b07e50"],
    "plank": ["#2a1a0c", "#5a3a1e", "#6a4424", "#7c522c", "#986a3c", "#b48a58"],
    "glass": ["#14202e", "#2a4058", "#3a5878", "#4e7898", "#7aa8c8", "#cfe8f8"],
    "iron": ["#14161c", "#40464f", "#56606a", "#6c7480", "#9aa2ae", "#d4dae2"],
    "gold": ["#5a4018", "#a07a30", "#c49a44", "#e8c060", "#f8dc88", "#fff4c8"],
    "leaf": LEAF[:6],
    "pink": PINK[:6],
    "yellow": YELLOW[:6],
}


def grain(c, mask, vertical=True, seed=0):
    """Wood grain: long thin darker streaks along the board, a lit streak beside some."""
    for y, x in zip(*np.nonzero(mask)):
        a, b = (x, y) if vertical else (y, x)
        u = (a * 3 + int(2 * math.sin(b * 0.17 + a))) % 7
        t = int(c.tone[y, x])
        if u == 0:
            c.tone[y, x] = max(1, t - 1)
        elif u == 3 and hsh(a, b // 9, seed) % 3 == 0:
            c.tone[y, x] = min(5, t + 1)


def bevel(c, mask, lit=1, dark=-1):
    """A part's own edges: top/left rows lit, bottom/right rows dark (the light from the top left)."""
    ys, xs = np.nonzero(mask)
    for y, x in zip(ys, xs):
        t = int(c.tone[y, x])
        up = y == 0 or not mask[y - 1, x]
        left = x == 0 or not mask[y, x - 1]
        down = y == H - 1 or not mask[y + 1, x]
        right = x == W - 1 or not mask[y, x + 1]
        if down or right:
            c.tone[y, x] = max(1, t + dark)
        elif up or left:
            c.tone[y, x] = min(5, t + lit)


def stones(c, x0, y0, x1, y1, rng, row_h=11):
    y = y0
    r = 0
    while y <= y1:
        x = x0 - (r % 2) * 9
        while x <= x1:
            w = rng.randint(14, 24)
            m = c.m_rect(max(x0, x + 1), y + 1, min(x1, x + w - 1), min(y1, y + row_h - 1))
            c.fill(m, "stone", rng.choice((3, 3, 3, 2, 4)))
            bevel(c, m)
            # a chip or two
            if rng.random() < 0.4 and x + w <= x1:
                cx_, cy_ = x + rng.randint(3, max(3, w - 4)), y + rng.randint(3, row_h - 3)
                c.put(cx_, cy_, "stone", 1)
                c.put(cx_ + 1, cy_, "stone", 2)
            x += w
        y += row_h
        r += 1
    # mortar
    mort = c.m_rect(x0, y0, x1, y1) & (c.mat == 0)
    c.fill(mort, "stone", 1)


def roof(c, rng):
    top, bot = 22, 100
    poly = [(2, bot), (190, bot), (164, top), (28, top)]
    m = c.m_poly(poly)
    c.fill(m, "roof", 3)
    rows = list(range(top, bot, 8))
    for j, ry in enumerate(rows):
        f = (ry - top) / (bot - top)
        xl, xr = 28 - 26 * f, 164 + 26 * f
        off = (j % 2) * 6
        x = xl - off
        while x < xr:
            w = 12
            tm = m & c.m_rect(int(x) + 1, ry, int(x + w) - 1, ry + 7)
            base = 3 if hsh(int(x), j, 3) % 5 else (2 if hsh(int(x), j, 4) % 2 else 4)
            for yy, xx in zip(*np.nonzero(tm)):
                d = yy - ry
                t = base
                if d == 7:
                    t = 1  # the lip's shadow on the row below
                elif d == 6:
                    t = base - 1
                elif d <= 1 and xx < x + 7:
                    t = min(5, base + 1)
                if xx >= x + w - 2:
                    t = max(1, t - 1)
                c.tone[yy, xx] = t
            x += w
        # a gap line between tiles (vertical, 1 texel)
    # the ridge: caps along the top
    ridge = c.m_rect(26, top - 6, 166, top + 1)
    c.fill(ridge, "roof", 4)
    for x in range(26, 167, 9):
        c.fill(c.m_rect(x, top - 6, x, top + 1), "roof", 1)
        c.put(x + 2, top - 5, "roof", 5)
        c.put(x + 3, top - 5, "roof", 5)
    c.fill(c.m_rect(26, top + 1, 166, top + 1), "roof", 1)
    # shade on the right half (the light from the left)
    for yy, xx in zip(*np.nonzero(m)):
        if xx > 150 + (yy - top) * 0.3 and c.tone[yy, xx] > 1:
            c.tone[yy, xx] -= 1
    # moss in a few tiles
    for (mx, my) in ((40, 90), (52, 92), (150, 84)):
        c.fill(c.m_ellipse(mx, my, 4, 2), "leaf", 3)
        c.put(mx - 2, my - 1, "leaf", 4)
    # the eaves' edge (a dark board) and fascia
    c.fill(c.m_rect(2, bot, 189, bot + 3), "timber", 2)
    c.fill(c.m_rect(2, bot, 189, bot), "timber", 4)


def chimney(c):
    m = c.m_rect(132, 2, 152, 40)
    c.fill(m, "stone", 3)
    for y in range(4, 40, 6):
        for x in range(132 + (y // 6 % 2) * 5, 153, 10):
            c.fill(c.m_rect(x, y, x, y + 5), "stone", 1)
        c.fill(c.m_rect(132, y, 152, y), "stone", 1)
    bevel(c, m)
    c.fill(c.m_rect(130, 0, 154, 3), "stone", 4)
    c.fill(c.m_rect(130, 3, 154, 3), "stone", 1)


def window(c, x0, y0, w, h, shutters=True, box=True):
    frame = c.m_rect(x0 - 2, y0 - 2, x0 + w + 1, y0 + h + 1)
    c.fill(frame, "timber", 3)
    bevel(c, frame)
    g = c.m_rect(x0, y0, x0 + w - 1, y0 + h - 1)
    c.fill(g, "glass", 2)
    for y, x in zip(*np.nonzero(g)):
        u = (x - x0) + (y - y0)
        t = 2 if y - y0 > h * 0.55 else 3
        if 4 <= u - (y - y0) * 0 <= 6:
            t = 5
        elif u in (7, 9):
            t = 4
        if y == y0 or x == x0:
            t = 1  # the frame's shadow on the glass
        c.tone[y, x] = t
    # mullions (a cross)
    c.fill(c.m_rect(x0 + w // 2 - 1, y0, x0 + w // 2, y0 + h - 1), "timber", 2)
    c.fill(c.m_rect(x0, y0 + h // 2 - 1, x0 + w - 1, y0 + h // 2), "timber", 2)
    c.put(x0 + w // 2 - 1, y0 + h // 2 - 1, "timber", 4)
    if shutters:
        for sx in (x0 - 2 - 9, x0 + w + 2):
            s = c.m_rect(sx, y0 - 2, sx + 8, y0 + h + 1)
            c.fill(s, "plank", 3)
            for y in range(y0 - 2, y0 + h + 2):
                c.put(sx + 4, y, "plank", 2)
            for yy in (y0 + 2, y0 + h - 3):
                c.fill(c.m_rect(sx, yy, sx + 8, yy), "plank", 1)
                c.fill(c.m_rect(sx + 1, yy - 1, sx + 7, yy - 1), "plank", 4)
            bevel(c, s)
    if box:
        b = c.m_rect(x0 - 3, y0 + h + 2, x0 + w + 2, y0 + h + 7)
        c.fill(b, "plank", 3)
        grain(c, b, vertical=False, seed=x0)
        bevel(c, b)
        # leaves and petals spilling over the box
        for k in range(0, w + 4, 3):
            x = x0 - 2 + k
            c.fill(c.m_ellipse(x + 1, y0 + h + 1, 2.2, 2.0), "leaf", 3 if k % 2 else 4)
        for k, col in zip(range(1, w + 2, 5), ("pink", "yellow", "pink", "pink", "yellow", "pink", "yellow")):
            x = x0 - 1 + k
            c.fill(c.m_ellipse(x + 0.5, y0 + h, 1.6, 1.6), col, 4)
            c.put(x, y0 + h - 1, col, 5)


def door(c):
    x0, x1, y0 = 82, 109, 166
    arch = c.m_rect(x0 - 5, y0 + 4, x1 + 5, G) | c.m_ellipse((x0 + x1 + 1) / 2, y0 + 6, 19, 12)
    arch &= c.m_rect(0, 0, W - 1, G)
    c.fill(arch, "stone", 3)
    for k in range(9):  # voussoirs (wedge stones of the arch)
        a = math.pi + k * math.pi / 8
        for r in range(13, 19):
            c.put(int(96 + math.cos(a) * r), int(y0 + 6 + math.sin(a) * r * 0.66), "stone", 1 if r == 13 else 3)
    bevel(c, arch)
    d = c.m_rect(x0, y0 + 6, x1, G) | c.m_ellipse((x0 + x1 + 1) / 2, y0 + 7, 14, 9)
    d &= c.m_rect(x0, 0, x1, G)
    c.fill(d, "plank", 3)
    for x in range(x0 + 4, x1, 5):
        c.fill(c.m_rect(x, y0 - 4, x, G) & d, "plank", 1)
    grain(c, d, vertical=True, seed=5)
    for y in (y0 + 16, G - 12):  # iron straps with rivets
        c.fill(c.m_rect(x0, y, x1, y + 2), "iron", 3)
        c.fill(c.m_rect(x0, y, x1, y), "iron", 4)
        c.fill(c.m_rect(x0, y + 2, x1, y + 2), "iron", 1)
        for x in range(x0 + 2, x1, 6):
            c.put(x, y + 1, "iron", 5)
    c.fill(c.m_ellipse(104, y0 + 30, 2.2, 2.2), "gold", 3)
    c.put(103, y0 + 29, "gold", 5)
    # the step
    st = c.m_rect(x0 - 6, G - 3, x1 + 6, G)
    c.fill(st, "stone", 4)
    bevel(c, st)
    # a lantern by the door
    c.fill(c.m_rect(118, 168, 124, 169), "iron", 2)
    lam = c.m_rect(119, 170, 123, 177)
    c.fill(lam, "gold", 3)
    c.fill(c.m_rect(120, 171, 122, 175), "yellow", 5)
    c.put(120, 171, "yellow", 5)
    c.fill(c.m_rect(118, 178, 124, 179), "iron", 2)


def timber_floor(c, rng):
    y0, y1 = 104, 150
    wall = c.m_rect(18, y0, 173, y1)
    c.fill(wall, "plaster", 3)
    for y, x in zip(*np.nonzero(wall)):  # plaster: soft trowel marks, darker under the eaves
        if y < y0 + 5:
            c.tone[y, x] = 1 if y < y0 + 2 else 2
        elif hsh(x // 3, y // 2, 1) % 41 == 0:
            c.tone[y, x] = 4
        elif hsh(x // 4, y // 3, 2) % 37 == 0:
            c.tone[y, x] = 2
    posts = [18, 56, 92, 128, 168]
    for x in posts:
        m = c.m_rect(x, y0, x + 5, y1)
        c.fill(m, "timber", 3)
        grain(c, m, vertical=True, seed=x)
        bevel(c, m)
    for y in (y0, y1 - 4):
        m = c.m_rect(18, y, 173, y + 4)
        c.fill(m, "timber", 3)
        grain(c, m, vertical=False, seed=y)
        bevel(c, m)
    for (xa, xb) in ((61, 92), (133, 168)):  # braces
        for d in range(-2, 3):
            c.fill(c.m_line([(xa, y1 - 5 + d * 0), (xb - 1, y0 + 5)], 3.2) & wall, "timber", 3 if d else 4)
    window(c, 26, 114, 22, 24)
    window(c, 140, 114, 22, 24)
    window(c, 98, 116, 24, 18, shutters=False, box=False)


def main():
    rng = random.Random(42)
    c = Canvas(W, H, RAMPS)
    chimney(c)
    stones(c, 14, 150, 177, G, rng)
    # the shade line under the upper floor's overhang
    c.fill(c.m_rect(14, 150, 177, 153), "stone", 1)
    timber_floor(c, rng)
    roof(c, rng)
    window(c, 30, 174, 24, 22)
    window(c, 140, 174, 24, 22)
    door(c)
    # moss and grass at the foot
    for x in range(14, 178, 3):
        if 76 <= x <= 116:
            continue
        h = 2 + hsh(x, 1, 7) % 4
        for d in range(h):
            c.put(x, G - d, "leaf", 3 if d < h - 1 else 5)
    c.outline()
    c.shadow_band()
    p = save(c, os.path.join(OUT, "obj.v3.house_stone.png"))
    print(os.path.relpath(p, ROOT))


if __name__ == "__main__":
    main()
