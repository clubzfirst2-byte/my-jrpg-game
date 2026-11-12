"""v3 pilot (round 2): one house at density 4 — a new kind (STYLE.md 7): a stone ground floor and a
timber-framed upper floor under a clay-tile roof. 256 x 288 (game 64 x 72: 4 tiles wide), the door's
sill on the bottom row's centre (the anchor, like obj.house).

Round 2 (inspection fixes): sized to the hero — the door is 103 texels high (the hero is 112: 92%),
the ground-floor windows 52 high (from the hero's chest up past the head), the upper windows 32;
no grass baked into the bottom row; the roof's right half one tone darker (the light from the left),
tiles varying within 2 tones. Round 3: a lower roof and an upper floor 82 texels high (73% of the
hero), upper windows 30 x 40, the door 99 (88%), no moss dots; ramps lifted so no texel
is near-black (luma >= 36); no lone texels (despeckle).
Detail that needs 2x: single roof tiles with a lit upper edge and a shadow lip, mortar between stones,
wood grain on beams and planks, glass with a reflection, iron straps and rivets, a flower box.
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

from gen_nature_v3 import LEAF, PINK, YELLOW, hsh  # noqa: E402
from v3lib import ROOT, Canvas, despeckle, lift_ramp, save  # noqa: E402

OUT = os.path.join(ROOT, "src", "art-release-v3", "objects")
W, H = 256, 288
G = H - 1
RAMPS = {k: lift_ramp(v) for k, v in {
    "roof": ["#3a1208", "#6a2412", "#86321a", "#a24020", "#bc5a30", "#d8804e"],
    "stone": ["#24222a", "#4a4650", "#5e5a64", "#77727a", "#938d92", "#b4aeb0"],
    "plaster": ["#4e4636", "#b4a888", "#cfc4a4", "#e8dec2", "#f6efdc", "#fffaf0"],
    "timber": ["#1e1008", "#4a2c16", "#5c3a1e", "#6e4424", "#906038", "#b07e50"],
    "plank": ["#2a1a0c", "#5a3a1e", "#6a4424", "#7c522c", "#986a3c", "#b48a58"],
    "glass": ["#14202e", "#2a4058", "#3a5878", "#4a7494", "#7aa8c8", "#cfe8f8"],
    "iron": ["#14161c", "#40464f", "#56606a", "#6c7480", "#9aa2ae", "#d4dae2"],
    "gold": ["#5a4018", "#a07a30", "#c49a44", "#e8c060", "#f8dc88", "#fff4c8"],
    "leaf": LEAF[:6],
    "pink": PINK[:6],
    "yellow": YELLOW[:6],
}.items()}

ROOF_TOP, ROOF_BOT = 20, 94
UP_TOP, UP_BOT = 98, 180  # the upper floor's wall: 82 texels, 73% of the hero (round 3)
DOOR_X0, DOOR_X1, DOOR_TOP = 106, 149, 188  # the door: 99 texels, 88% of the hero


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
    for y, x in zip(*np.nonzero(mask)):
        t = int(c.tone[y, x])
        down = y == H - 1 or not mask[y + 1, x]
        right = x == W - 1 or not mask[y, x + 1]
        up = y == 0 or not mask[y - 1, x]
        left = x == 0 or not mask[y, x - 1]
        if down or right:
            c.tone[y, x] = max(1, t + dark)
        elif up or left:
            c.tone[y, x] = min(5, t + lit)


def stones(c, x0, y0, x1, y1, rng, row_h=12):
    y, r = y0, 0
    while y <= y1:
        x = x0 - (r % 2) * 10
        while x <= x1:
            w = rng.randint(16, 28)
            m = c.m_rect(max(x0, x + 1), y + 1, min(x1, x + w - 1), min(y1, y + row_h - 1))
            c.fill(m, "stone", rng.choice((3, 3, 3, 2, 4)))
            bevel(c, m)
            if rng.random() < 0.35 and x + w <= x1 - 2 and x >= x0 + 2:
                cx_, cy_ = x + rng.randint(4, max(4, w - 5)), y + rng.randint(3, row_h - 4)
                for dx, dy, t in ((0, 0, 1), (1, 0, 2), (0, 1, 2)):
                    c.put(cx_ + dx, cy_ + dy, "stone", t)
            x += w
        y += row_h
        r += 1
    c.fill(c.m_rect(x0, y0, x1, y1) & (c.mat == 0), "stone", 1)  # mortar


def roof(c, rng):
    top, bot = ROOF_TOP, ROOF_BOT
    m = c.m_poly([(3, bot), (252, bot), (214, top), (42, top)])
    c.fill(m, "roof", 3)
    mid = W / 2
    for j, ry in enumerate(range(top, bot, 8)):
        f = (ry - top) / (bot - top)
        xl, xr = 42 - 39 * f, 214 + 38 * f
        x = xl - rng.randint(0, 12)  # each row starts at its own offset (no grid)
        while x < xr:
            w = rng.choice((12, 13, 14, 14, 15, 16))
            tm = m & c.m_rect(int(x) + 1, ry, int(x + w) - 1, ry + 7)
            base = 4 if hsh(int(x), j, 3) % 4 == 0 else 3  # tiles vary within 2 tones
            for yy, xx in zip(*np.nonzero(tm)):
                d = yy - ry
                t = base
                if d == 7:
                    t = 1  # the lip's shadow on the row below
                elif d == 6:
                    t = base - 1
                elif d <= 1 and xx < x + 8:
                    t = min(5, base + 1)
                if xx >= x + w - 2:
                    t = max(1, t - 1)
                if xx > mid and t > 1:  # the right half faces away from the light
                    t -= 1
                c.tone[yy, xx] = t
            x += w
    ridge = c.m_rect(40, top - 7, 216, top + 1)
    c.fill(ridge, "roof", 4)
    for x in range(40, 217, 10):
        c.fill(c.m_rect(x, top - 7, x, top + 1), "roof", 1)
        c.fill(c.m_rect(x + 2, top - 6, x + 3, top - 5), "roof", 5)
    c.fill(c.m_rect(40, top + 1, 216, top + 1), "roof", 1)
    c.fill(c.m_rect(129, top - 7, 216, top + 1) & (c.mat == c.mid("roof")) & (c.tone > 1), "roof", 3)
    # the eaves' board
    c.fill(c.m_rect(3, bot, 252, bot + 3), "timber", 2)
    c.fill(c.m_rect(3, bot, 252, bot), "timber", 4)


def chimney(c):
    m = c.m_rect(182, 0, 206, 52)
    c.fill(m, "stone", 3)
    for y in range(4, 52, 7):
        for x in range(182 + (y // 7 % 2) * 6, 207, 12):
            c.fill(c.m_rect(x, y, x, y + 6), "stone", 1)
        c.fill(c.m_rect(182, y, 206, y), "stone", 1)
    bevel(c, m)
    for y, x in zip(*np.nonzero(m)):
        if x > 200:
            c.tone[y, x] = max(1, int(c.tone[y, x]) - 1)
    c.fill(c.m_rect(180, 0, 208, 3), "stone", 4)
    c.fill(c.m_rect(180, 3, 208, 3), "stone", 1)


def window(c, x0, y0, w, h, shutters=True, box=True):
    frame = c.m_rect(x0 - 3, y0 - 3, x0 + w + 2, y0 + h + 2)
    c.fill(frame, "timber", 3)
    bevel(c, frame)
    g = c.m_rect(x0, y0, x0 + w - 1, y0 + h - 1)
    c.fill(g, "glass", 2)
    for y, x in zip(*np.nonzero(g)):
        u = (x - x0) - (y - y0) * 0.6
        t = 2 if y - y0 > h * 0.55 else 3
        if 5 <= u % (w * 0.8) <= 8 and y - y0 < h * 0.7:
            t = 5
        elif 9 <= u % (w * 0.8) <= 10 and y - y0 < h * 0.7:
            t = 4
        if y <= y0 + 1 or x <= x0 + 1:
            t = 1  # the frame's shadow on the glass
        c.tone[y, x] = t
    c.fill(c.m_rect(x0 + w // 2 - 1, y0, x0 + w // 2 + 1, y0 + h - 1), "timber", 2)  # mullions
    c.fill(c.m_rect(x0, y0 + h // 2 - 1, x0 + w - 1, y0 + h // 2 + 1), "timber", 2)
    c.fill(c.m_rect(x0 + w // 2 - 1, y0 + h // 2 - 1, x0 + w // 2, y0 + h // 2 - 1), "timber", 4)
    if shutters:
        sw = max(10, w // 3)
        for sx in (x0 - 3 - sw, x0 + w + 3):
            s = c.m_rect(sx, y0 - 3, sx + sw - 1, y0 + h + 2)
            c.fill(s, "plank", 3)
            for y in range(y0 - 3, y0 + h + 3):
                c.put(sx + sw // 2, y, "plank", 2)
            for yy in (y0 + 3, y0 + h - 4):
                c.fill(c.m_rect(sx, yy, sx + sw - 1, yy + 1), "plank", 1)
                c.fill(c.m_rect(sx + 1, yy - 1, sx + sw - 2, yy - 1), "plank", 4)
            grain(c, s & ~c.m_rect(0, y0 + 2, W - 1, y0 + 4), vertical=True, seed=sx)
            bevel(c, s)
    if box:
        b = c.m_rect(x0 - 4, y0 + h + 3, x0 + w + 3, y0 + h + 10)
        c.fill(b, "plank", 3)
        grain(c, b, vertical=False, seed=x0)
        bevel(c, b)
        for k in range(0, w + 6, 4):
            x = x0 - 3 + k
            c.fill(c.m_ellipse(x + 1.5, y0 + h + 2, 2.8, 2.4), "leaf", 3 if k % 8 else 4)
        for k, col in zip(range(2, w + 4, 6), ("pink", "yellow", "pink", "pink", "yellow", "pink", "yellow", "pink")):
            x = x0 - 2 + k
            c.fill(c.m_ellipse(x + 1, y0 + h + 1, 2.0, 2.0), col, 4)
            c.fill(c.m_rect(x, y0 + h, x + 1, y0 + h), col, 5)


def door():
    pass


def front_door(c):
    x0, x1, y0 = DOOR_X0, DOOR_X1, DOOR_TOP
    cx = (x0 + x1 + 1) / 2
    arch = (c.m_rect(x0 - 7, y0 + 10, x1 + 7, G) | c.m_ellipse(cx, y0 + 12, (x1 - x0) / 2 + 8, 16))
    arch &= c.m_rect(0, UP_BOT + 2, W - 1, G)
    c.fill(arch, "stone", 3)
    for k in range(11):  # voussoirs
        a = math.pi + k * math.pi / 10
        for r in range(23, 30):
            c.put(int(cx + math.cos(a) * r), int(y0 + 12 + math.sin(a) * r * 0.62), "stone", 1 if r == 23 else 3)
    bevel(c, arch)
    d = c.m_rect(x0, y0 + 12, x1, G) | c.m_ellipse(cx, y0 + 13, (x1 - x0 + 1) / 2, 13)
    d &= c.m_rect(x0, y0, x1, G)
    c.fill(d, "plank", 3)
    for x in range(x0 + 6, x1, 7):
        c.fill(c.m_rect(x, y0, x, G) & d, "plank", 1)
    grain(c, d, vertical=True, seed=5)
    for y in (y0 + 26, G - 22):  # iron straps with rivets
        c.fill(c.m_rect(x0, y, x1, y + 3) & d, "iron", 3)
        c.fill(c.m_rect(x0, y, x1, y) & d, "iron", 4)
        c.fill(c.m_rect(x0, y + 3, x1, y + 3) & d, "iron", 1)
        for x in range(x0 + 3, x1, 7):
            c.fill(c.m_rect(x, y + 1, x + 1, y + 2), "iron", 5)
    ring = c.m_ellipse(x1 - 8, y0 + 56, 3.2, 3.2) & ~c.m_ellipse(x1 - 8, y0 + 56, 1.6, 1.6)
    c.fill(ring, "gold", 3)
    c.fill(c.m_rect(x1 - 10, y0 + 53, x1 - 9, y0 + 54), "gold", 5)
    for y, x in zip(*np.nonzero(d)):  # the door is set back: shade along its top and left
        if y < y0 + 16 + 0 * x and (y - y0) < 4 + abs(x - cx) * 0.0:
            c.tone[y, x] = max(1, int(c.tone[y, x]) - 1)
    st = c.m_rect(x0 - 10, G - 4, x1 + 10, G)
    c.fill(st, "stone", 4)
    bevel(c, st)
    # a lantern by the door
    c.fill(c.m_rect(160, 196, 170, 197), "iron", 2)
    lam = c.m_rect(161, 198, 169, 211)
    c.fill(lam, "gold", 3)
    c.fill(c.m_rect(163, 200, 167, 208), "yellow", 5)
    c.fill(c.m_rect(163, 200, 164, 202), "yellow", 5)
    c.fill(c.m_rect(160, 212, 170, 213), "iron", 2)


def upper_floor(c):
    y0, y1 = UP_TOP, UP_BOT
    wall = c.m_rect(22, y0, 233, y1)
    c.fill(wall, "plaster", 3)
    for y, x in zip(*np.nonzero(wall)):  # plaster: darker under the eaves, soft 2 x 2 trowel marks
        if y < y0 + 6:
            c.tone[y, x] = 1 if y < y0 + 2 else 2
        elif hsh(x // 3, y // 2, 1) % 41 == 0:
            c.tone[y, x] = 4
        elif hsh(x // 4, y // 3, 2) % 37 == 0:
            c.tone[y, x] = 2
    for x in (22, 86, 150, 176, 227):
        m = c.m_rect(x, y0, x + 6, y1)
        c.fill(m, "timber", 3)
        grain(c, m, vertical=True, seed=x)
        bevel(c, m)
    for y in (y0, y1 - 5):
        m = c.m_rect(22, y, 233, y + 5)
        c.fill(m, "timber", 3)
        grain(c, m, vertical=False, seed=y)
        bevel(c, m)
    for (xa, xb) in ((150, 176),):  # a brace
        c.fill(c.m_line([(xa, y1 - 6), (xb - 1, y0 + 6)], 4.2) & wall, "timber", 3)
        c.fill(c.m_line([(xa - 1, y1 - 7), (xb - 2, y0 + 5)], 1.2) & wall, "timber", 4)
    window(c, 40, 114, 30, 40)
    window(c, 112, 118, 32, 34, shutters=False, box=False)
    window(c, 186, 114, 30, 40)


def side_wall(c, rng):
    """Depth (round 4): the right side of the house seen at a slant, a 10-texel strip in shade next
    to each floor (stones below, plaster with a corner post above), under the roof's overhang."""
    up = c.m_poly([(234, UP_TOP), (244, UP_TOP + 5), (244, UP_BOT), (234, UP_BOT)])
    c.fill(up, "plaster", 1)
    c.fill(up & c.m_rect(241, 0, 244, H - 1), "timber", 1)
    c.fill(up & c.m_rect(0, UP_BOT - 5, W - 1, UP_BOT), "timber", 1)
    lo = c.m_poly([(240, UP_BOT), (250, UP_BOT + 4), (250, G), (240, G)])
    c.fill(lo, "stone", 2)
    for y in range(UP_BOT, G, 12):
        c.fill(c.m_rect(240, y, 250, y) & lo, "stone", 1)
        xs = 244 + (y // 12 % 2) * 3
        c.fill(c.m_rect(xs, y, xs, min(G, y + 11)) & lo, "stone", 1)


def main():
    rng = random.Random(42)
    c = Canvas(W, H, RAMPS)
    chimney(c)
    side_wall(c, rng)
    stones(c, 16, UP_BOT, 239, G, rng)
    c.fill(c.m_rect(16, UP_BOT, 239, UP_BOT + 4), "stone", 1)  # shade under the upper floor
    upper_floor(c)
    roof(c, rng)
    window(c, 36, 202, 40, 50)
    window(c, 180, 202, 40, 50)
    front_door(c)
    for y, x in zip(*np.nonzero(c.mat != 0)):  # the whole right end in shade (light from the left)
        if x > 228 and c.tone[y, x] > 1 and y > ROOF_BOT:
            c.tone[y, x] -= 1
    despeckle(c, keep=("pink", "yellow", "iron"))
    c.outline()
    c.shadow_band()
    p = save(c, os.path.join(OUT, "obj.v3.house_stone.png"))
    print(os.path.relpath(p, ROOT))


if __name__ == "__main__":
    main()
