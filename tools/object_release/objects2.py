"""Release wave 2: every remaining object, puzzle part, icon, effect and UI sprite (45 sprites;
rock, bramble, stump and cactus are the terrain producer's, art/terrain-release).

Same method as the approved wave-1 samples (objects.py): materials with 5-tone ramps, light from the top
left, the selective outline (Canvas.colours), hand-placed pixels and shapes; no mixed colours, every pixel
fully opaque or fully clear. Sizes are 2x the placeholder's (docs/art-kit/LIST.md), the anchors are the
same (placeholderPack.js): feet = bottom centre (the last row is the ground line), centre for fx / ui.

Light colours (approved): 星環 objects (receiver, altar, the elder's charm) = the hero's gem blue;
ruin mechanisms (door rune, resonance stone, pillar, sensor) = ruin.glow teal; fire = the guide's flames.
"""

import math

from draw import canvas, clear, layers, round_shade, to_rgba
from objects import box, flame_tones, hline, lit_by, overlap_shadow, stone_lump, tongue, vline
from ramps2 import RAMPS2


def cv(w, h):
    return canvas(w, h, RAMPS2)


def drop(img, n=None):
    """Move the picture down so its lowest drawn row is the last row (feet on the ground: no floating)."""
    w = len(img[0])
    empty = 0
    while all(p is None for p in img[len(img) - 1 - empty]):
        empty += 1
    n = empty if n is None else min(n, empty)
    return [[None] * w for _ in range(n)] + img[: len(img) - n]


def ring_px(cx, cy, r0, r1, n=1.0):
    """Pixels between radius r0 and r1 (an annulus) around (cx, cy); n squashes y."""
    out = []
    for y in range(int(cy - r1) - 1, int(cy + r1) + 2):
        for x in range(int(cx - r1) - 1, int(cx + r1) + 2):
            d = math.hypot(x + 0.5 - cx, (y + 0.5 - cy) / n)
            if r0 <= d <= r1:
                out.append((x, y))
    return out


def blocks(c, x0, y0, x1, y1, m, rows, seed=0):
    """Stone blocks in courses: rows = [(y_start, y_end), ...]; lit top/left, shaded bottom/right."""
    widths = (9, 7, 11, 8, 10, 6, 9, 12)
    for i, (ya, yb) in enumerate(rows):
        x = x0 - (i * 4 + seed) % 7
        k = i + seed
        while x <= x1:
            w = widths[k % len(widths)]
            xs, xe = max(x0, x), min(x1, x + w - 1)
            for yy in range(ya, yb + 1):
                for xx in range(xs, xe + 1):
                    t = 2
                    if yy == ya or xx == xs:
                        t = 3
                    if yy == yb or xx == xe:
                        t = 1
                    c.put(xx, yy, m, t)
            x += w
            k += 1


# ================================================================== buildings and entrances

def door():
    """obj.door 32x40: the rune door of the ruins (opened when its receiver is powered). Ruin stone, a
    carved rune ring in ruin teal, dim (not lit: it is a closed door)."""
    c = cv(32, 40)
    S = "ruin_stone"
    # the two posts and the lintel
    for x0 in (1, 26):
        box(c, x0, 5, x0 + 4, 38, S, top=3, bottom=1)
        for y in (12, 20, 28):
            hline(c, x0, x0 + 4, y, S, 1)
            hline(c, x0, x0 + 4, y + 1, S, 3)
    c.rect(1, 1, 30, 6, S, 2)
    hline(c, 1, 30, 1, S, 4)
    hline(c, 1, 30, 2, S, 3)
    hline(c, 1, 30, 6, S, 1)
    vline(c, 30, 1, 6, S, 1)
    for x in (8, 16, 24):
        vline(c, x, 3, 5, S, 1)
    # the slab between the posts, in shade under the lintel
    c.rect(6, 7, 25, 38, S, 2)
    hline(c, 6, 25, 7, S, 0)
    hline(c, 6, 25, 8, S, 1)
    vline(c, 6, 9, 38, S, 1)
    vline(c, 25, 9, 38, S, 1)
    vline(c, 7, 9, 38, S, 3)
    for y in (17, 30):
        hline(c, 7, 24, y, S, 1)
        hline(c, 7, 24, y + 1, S, 3)
    # the rune ring and the bar across the seam
    for x, y in ring_px(16, 19.5, 4.2, 5.4):
        c.put(x, y, "ruin_glow", 1)
    for x, y in ring_px(16, 19.5, 4.2, 4.9):
        if (x - 16) + (y - 19.5) < -2:
            c.put(x, y, "ruin_glow", 2)
    for y in range(16, 24):
        c.put(16, y, "ruin_glow", 1)
        c.put(15, y, "ruin_glow", 2 if y < 19 else 1)
    for x, y in ((13, 19), (14, 19), (17, 20), (18, 20)):
        c.put(x, y, "ruin_glow", 1)
    # one connected rune (inspection 5: no separate dots or wave, which read as eyes and a mouth): the bar
    # runs on through the ring as a staff, from a point above to a diamond foot below
    for y in list(range(11, 15)) + list(range(25, 33)):
        c.put(16, y, "ruin_glow", 1)
        c.put(15, y, "ruin_glow", 2 if y < 15 else 1)
    for x, y in ((15, 10), (16, 10), (14, 32), (17, 32), (14, 33), (17, 33), (15, 34), (16, 34)):
        c.put(x, y, "ruin_glow", 1)
    c.put(15, 33, "ruin_glow", 2)
    c.put(16, 33, "ruin_glow", 1)
    # chips, moss at the foot
    for x, y in ((3, 37), (4, 37), (27, 37), (28, 36), (8, 37), (9, 37)):
        c.put(x, y, "moss", 2)
    hline(c, 1, 30, 38, S, 1)
    return {"obj.door": to_rgba(c)}


def cave():
    """obj.cave 32x28: a cave mouth on a cliff face — an arch of cut stones (voussoirs) around the dark."""
    c = cv(32, 28)
    cx, cy = 15.5, 13.0
    n_blocks = 9
    for y in range(1, 28):
        for x in range(1, 31):
            px, py = x + 0.5 - cx, y + 0.5 - cy
            if py < 0:
                r = math.hypot(px, py)
                if r > 14.5:
                    continue
                inner = r < 10.5
            else:
                if abs(px) > 14.5:
                    continue
                inner = abs(px) < 10.5
            if inner:
                c.put(x, y, "cave_rock", 0)
                continue
            # which stone: by angle on the arch, by course on the jambs
            if py < 0:
                a = math.atan2(-py, px)  # 0 right .. pi left
                k = int(a / math.pi * n_blocks)
                edge = abs(a / math.pi * n_blocks - round(a / math.pi * n_blocks)) < 0.09
                r = math.hypot(px, py)
                t = 3 if (r > 13.6 and px < 4) else 1 if r < 11.4 and px > -4 else 2
                if px < -6 and r < 11.4:
                    t = 3  # the inner face on the left catches the light
            else:
                k = 100 + int(py // 5)
                edge = int(py) % 5 == 4
                t = 3 if abs(px) > 13.6 and px < 0 else 1 if abs(px) > 13.6 else 2
                if abs(px) < 11.4:
                    t = 1 if px > 0 else 3
            c.put(x, y, "stone", 1 if edge else t)
            if k % 2 and t == 2 and not edge:
                c.tone[y][x] = 2
    for x, y in ((8, 4), (12, 1), (4, 9), (2, 15), (2, 21), (23, 3)):
        if c.m(x, y) == "stone":
            c.tone[y][x] = 4
    # the dark: a little rock shows on the upper left inside, deepest further in
    for y in range(28):
        for x in range(32):
            if c.m(x, y) != "cave_rock":
                continue
            if c.m(x, y - 1) == "stone" or c.m(x - 1, y) == "stone" or c.m(x, y - 2) == "stone":
                c.tone[y][x] = 2 if x < cx else 1
            elif c.m(x - 2, y) == "stone" and y < 20:
                c.tone[y][x] = 1
    for x, y in ((1, 26), (2, 26), (3, 25), (29, 26), (30, 26), (28, 25), (5, 27)):
        c.put(x, y, "moss", 2)
    return {"obj.cave": to_rgba(c)}


def stairs():
    """obj.stairs 32x32 (lies flat): steps down into the mine — each step one tone darker, the last in the dark.
    Each step: a lit nosing, the tread, and the shadow the step above casts on it."""
    c = cv(32, 32)
    R = "mount_rock"
    for y in range(1, 32):
        for x in range(32):
            c.put(x, y, R, 2)
    hline(c, 0, 31, 0, R, 0)
    for x0, x1 in ((0, 3), (28, 31)):  # side walls in courses
        for y in range(1, 32):
            for x in range(x0, x1 + 1):
                c.put(x, y, R, 3 if x == x0 else 1 if x == x1 else 2)
        for y in (7, 15, 23):
            hline(c, x0, x1, y, R, 0)
    for i in range(4):
        y0 = 1 + i * 8
        tread = (3, 2, 1, 1)[i]
        for y in range(y0, y0 + 8):
            for x in range(4, 28):
                if y == y0:
                    t = min(4, tread + 1)  # the nosing
                elif y == y0 + 1 and i > 0:
                    t = tread
                elif y >= y0 + 6:
                    t = 0  # the drop to the next step
                else:
                    t = tread
                c.put(x, y, R, t)
        for x, dy in ((9 + i * 3, 3), (20 - i * 2, 4)):
            c.put(x, y0 + dy, R, max(0, tread - 1))  # a chip in the tread
            c.put(x + 1, y0 + dy, R, max(0, tread - 1))
    for y in range(28, 32):
        for x in range(4, 28):
            c.put(x, y, "cave_rock", 0)
    return {"obj.stairs": to_rgba(c)}


# ================================================================== furniture (the plains houses)

def lowwall():
    """obj.lowwall 32x24: a wainscot of planks with a cap rail; repeats left-right without a seam."""
    c = cv(32, 24)
    W = "wood"
    c.rect(0, 1, 31, 4, "chestwood", 3)
    hline(c, 0, 31, 1, "chestwood", 4)
    hline(c, 0, 31, 4, "chestwood", 2)
    hline(c, 0, 31, 5, "chestwood", 1)
    hline(c, 0, 31, 6, W, 0)
    for y in range(7, 21):
        for x in range(32):
            p = x % 8
            t = 3 if p == 0 else 1 if p == 7 else 2
            if y == 7:
                t = 1
            c.put(x, y, W, t)
    for x, y in ((3, 10), (4, 10), (12, 15), (13, 15), (20, 11), (27, 17), (28, 17), (5, 18)):
        c.put(x, y, W, 1)
    for x in range(32):
        c.put(x, 21, W, 3)
        c.put(x, 22, W, 1)
    for x in (4, 20):
        c.put(x, 2, "chestwood", 2)
    return {"obj.lowwall": to_rgba(c)}


def bed():
    """obj.bed 32x52, head to the north: headboard, pillow, a red blanket with the sheet folded over."""
    c = cv(32, 52)
    W = "chestwood"
    # headboard with two posts
    box(c, 2, 2, 29, 9, W, top=3, bottom=1)
    for x0 in (2, 27):
        box(c, x0, 0 + 1, x0 + 2, 11, W, top=4, bottom=1)
    hline(c, 5, 26, 5, W, 1)
    hline(c, 5, 26, 6, W, 3)
    # the frame sides
    for x0 in (2, 27):
        box(c, x0, 10, x0 + 2, 46, W)
    # mattress / sheet
    c.rect(5, 10, 26, 45, "linen", 2)
    hline(c, 5, 26, 10, "linen", 1)
    # pillow
    c.rect(8, 12, 23, 18, "linen", 3)
    hline(c, 8, 23, 12, "linen", 4)
    hline(c, 8, 23, 18, "linen", 1)
    vline(c, 23, 13, 18, "linen", 2)
    vline(c, 8, 13, 17, "linen", 4)
    c.put(15, 15, "linen", 2)
    c.put(16, 15, "linen", 2)
    hline(c, 7, 24, 19, "linen", 1)
    # the folded sheet band, then the blanket
    c.rect(5, 21, 26, 23, "linen", 3)
    hline(c, 5, 26, 21, "linen", 4)
    hline(c, 5, 26, 24, "linen", 1)
    c.rect(5, 25, 26, 45, "room_rug", 2)
    vline(c, 5, 25, 45, "room_rug", 3)
    vline(c, 26, 25, 45, "room_rug", 1)
    hline(c, 5, 26, 25, "room_rug", 3)
    for y in (31, 39):
        hline(c, 6, 25, y, "room_rug", 1)
        hline(c, 6, 25, y + 1, "room_rug", 3)
    for x in range(8, 25, 4):  # a gold stitched hem
        c.put(x, 44, "gold", 2)
    for x, y in ((10, 28), (11, 28), (18, 35), (19, 35), (13, 42)):
        c.put(x, y, "room_rug", 1)
    hline(c, 5, 26, 45, "room_rug", 1)
    # footboard and legs
    box(c, 2, 46, 29, 48, W, top=3, bottom=1)
    for x0 in (2, 27):
        box(c, x0, 49, x0 + 2, 50, W, core=1, lit=2, dark=0)
    return {"obj.bed": to_rgba(c)}


def table():
    """obj.table 32x28: a plank table top seen from above-front, two legs, a cup and a loaf on a cloth."""
    c = cv(32, 28)
    W = "wood"
    c.rect(1, 1, 30, 10, W, 3)
    for y in (4, 7):
        hline(c, 2, 29, y, W, 2)
    hline(c, 1, 30, 1, W, 4)
    vline(c, 1, 1, 10, W, 4)
    vline(c, 30, 1, 10, W, 2)
    for x, y in ((9, 2), (10, 2), (22, 5), (23, 5), (6, 8), (17, 9)):
        c.put(x, y, W, 2)
    c.rect(1, 11, 30, 13, W, 2)
    hline(c, 1, 30, 13, W, 1)
    vline(c, 30, 11, 13, W, 1)
    for x0 in (3, 26):
        box(c, x0, 14, x0 + 2, 26, W, core=2, lit=3, dark=1)
        hline(c, x0, x0 + 2, 14, W, 0)
    hline(c, 6, 25, 14, W, 0)
    c.rect(19, 3, 23, 7, "clay", 2)
    vline(c, 19, 3, 7, "clay", 3)
    vline(c, 23, 3, 7, "clay", 1)
    hline(c, 20, 22, 3, "clay", 0)
    c.put(20, 4, "clay", 4)
    c.put(24, 5, "clay", 1)
    hline(c, 19, 23, 8, W, 1)
    c.rect(6, 4, 13, 7, "linen", 3)
    hline(c, 6, 13, 7, "linen", 1)
    c.rect(8, 3, 12, 5, "stew", 3)
    hline(c, 9, 11, 3, "stew", 4)
    hline(c, 8, 12, 6, "stew", 1)
    return {"obj.table": to_rgba(c)}


def _shelf_body(c):
    W = "wood"
    box(c, 1, 7, 30, 38, W, top=3, bottom=1)
    hline(c, 1, 30, 7, W, 4)
    c.rect(4, 9, 27, 33, W, 0)  # the dark back
    for y in (16, 24, 32):  # boards
        hline(c, 3, 28, y, W, 3)
        hline(c, 3, 28, y + 1, W, 1)
    for x0 in (1, 28):
        vline(c, x0, 8, 38, W, 3 if x0 == 1 else 1)
        vline(c, x0 + 1, 8, 38, W, 2)
        vline(c, x0 + 2, 8, 38, W, 2 if x0 == 1 else 1)
    vline(c, 3, 9, 33, W, 1)
    # the open bottom between the feet
    for y in range(34, 38):
        for x in range(4, 28):
            c.put(x, y, W, 1 if y < 36 else 2)
    hline(c, 4, 27, 34, W, 0)
    # top shelf: jars and a bottle
    for x0, m in ((5, "clay"), (10, "glaze")):
        c.rect(x0, 11, x0 + 3, 15, m, 2)
        vline(c, x0, 11, 15, m, 3)
        vline(c, x0 + 3, 11, 15, m, 1)
        hline(c, x0 + 1, x0 + 2, 10, m, 3)
        c.put(x0 + 1, 12, m, 4)
    c.rect(16, 12, 18, 15, "glass", 2)
    vline(c, 16, 12, 15, "glass", 3)
    c.put(17, 10, "wood", 2)
    c.put(17, 11, "glass", 3)
    c.put(16, 12, "glass", 4)
    c.rect(21, 13, 26, 15, "linen", 3)  # folded cloth
    hline(c, 21, 26, 13, "linen", 4)
    hline(c, 21, 26, 15, "linen", 1)
    # middle shelf: books
    x = 5
    for i, (m, w, h) in enumerate((("roof", 2, 6), ("glaze", 2, 5), ("leather", 3, 6), ("string", 2, 4), ("roof", 2, 5), ("glaze", 3, 6))):
        top = 23 - h + 1
        c.rect(x, top, x + w - 1, 23, m, 2)
        vline(c, x, top, 23, m, 3)
        if w > 2:
            vline(c, x + w - 1, top, 23, m, 1)
        c.put(x, top + 2, "gold", 3)
        x += w + (1 if i == 2 else 0)
    # a leaning book
    for k in range(5):
        c.put(23 + k // 2, 23 - k, "leather", 2)
        c.put(24 + k // 2, 23 - k, "leather", 1)
    # bottom shelf: a basket and a jar
    c.rect(5, 27, 14, 31, "string", 2)
    hline(c, 5, 14, 27, "string", 3)
    for xx in range(6, 14, 2):
        vline(c, xx, 28, 31, "string", 1)
    c.rect(18, 26, 23, 31, "clay", 2)
    vline(c, 18, 26, 31, "clay", 3)
    vline(c, 23, 26, 31, "clay", 1)
    hline(c, 19, 22, 26, "clay", 3)
    c.put(19, 27, "clay", 4)


def shelves():
    """obj.shelf / obj.charm_shelf / obj.charm_shelf.on 32x40: the shelf (jars, books, a basket).
    The elder's charm shelf has a small cushion on top; .on = the charm (a 星環 thing: gem blue) is home,
    glowing, with a star above it (shape + light change)."""
    out = {}
    c = cv(32, 40)
    _shelf_body(c)
    out["obj.shelf"] = to_rgba(c)
    for on in (False, True):
        c = cv(32, 40)
        _shelf_body(c)
        # the cushion on top
        c.rect(12, 4, 19, 6, "room_rug", 2)
        hline(c, 12, 19, 4, "room_rug", 3)
        hline(c, 12, 19, 6, "room_rug", 1)
        c.put(12, 6, "gold", 2)
        c.put(19, 6, "gold", 2)
        if on:
            # the charm: a ring with a gem, standing on the cushion; a star floats above
            for x, y in ring_px(15.5, 2.5, 1.6, 2.6):
                if y <= 4:
                    c.put(x, y, "gold", 3 if x < 15 else 2)
            c.put(15, 2, "gem", 4)
            c.put(16, 2, "gem", 3)
            c.put(15, 3, "gem", 3)
            c.put(16, 3, "gem", 2)
            for x, y, t in ((22, 1, 4), (21, 1, 3), (23, 1, 3), (22, 0, 3), (22, 2, 3), (9, 2, 3)):
                c.put(x, y, "gem", t)
            lit_by(c, {"gem"}, "room_rug", 3)
            lit_by(c, {"gem"}, "gold", 4)
        img = to_rgba(c)
        out["obj.charm_shelf" + (".on" if on else "")] = img
    return out


def counter():
    """obj.counter 32x32: one length of the shop counter; repeats left-right without a seam."""
    c = cv(32, 32)
    T, F = "crate", "chestwood"
    c.rect(0, 1, 31, 6, T, 3)
    hline(c, 0, 31, 1, T, 4)
    for y in (3, 5):
        for x in range(32):
            if (x + y * 3) % 16 < 9:
                c.put(x, y, T, 2)
    hline(c, 0, 31, 6, T, 2)
    hline(c, 0, 31, 7, T, 1)
    hline(c, 0, 31, 8, F, 0)
    c.rect(0, 9, 31, 28, F, 2)
    for x0 in (0, 16):  # two framed panels per length
        for y in range(11, 26):
            c.put(x0 + 2, y, F, 1)
            c.put(x0 + 13, y, F, 3)
        hline(c, x0 + 2, x0 + 13, 11, F, 1)
        hline(c, x0 + 2, x0 + 13, 26, F, 3)
        c.rect(x0 + 4, 13, x0 + 11, 24, F, 2)
        hline(c, x0 + 4, x0 + 11, 13, F, 3)
        vline(c, x0 + 4, 13, 24, F, 3)
        vline(c, x0 + 11, 14, 24, F, 1)
        hline(c, x0 + 5, x0 + 11, 24, F, 1)
        c.put(x0 + 7, 18, F, 1)
        c.put(x0 + 8, 18, F, 1)
    hline(c, 0, 31, 9, F, 1)
    hline(c, 0, 31, 28, F, 1)
    c.rect(0, 29, 31, 30, "wood", 1)
    hline(c, 0, 31, 29, "wood", 2)
    return {"obj.counter": to_rgba(c)}


def stove():
    """obj.stove 32x40: a stone oven with an iron cooktop, a pot, a chimney pipe and a fire inside."""
    c = cv(32, 40)
    S = "stone"
    # the pipe
    box(c, 22, 1, 26, 12, "iron", top=3, bottom=1)
    hline(c, 21, 27, 1, "iron", 3)
    hline(c, 22, 26, 6, "iron", 1)
    # the pot
    c.ellipse(11, 9, 6, 4.2, "iron", 2)
    round_shade(c, "iron", 11, 8.5, 6, 4.2)
    c.ellipse(11, 5.5, 4.5, 1.6, "iron", 0)
    hline(c, 8, 13, 4, "iron", 3)
    c.put(5, 8, "iron", 3)
    c.put(17, 8, "iron", 1)
    # the body: a stone block with a lit top
    c.rect(2, 13, 29, 38, S, 2)
    blocks(c, 2, 17, 29, 38, S, [(17, 21), (22, 26), (27, 31), (32, 38)], seed=2)
    c.rect(1, 12, 30, 16, "iron", 2)
    hline(c, 1, 30, 12, "iron", 4)
    hline(c, 1, 30, 13, "iron", 3)
    hline(c, 1, 30, 16, "iron", 1)
    vline(c, 30, 12, 16, "iron", 1)
    for x in (8, 15, 22):
        c.put(x, 14, "iron", 1)
    # the fire mouth: an arch, dark inside, flames
    for y in range(20, 35):
        for x in range(8, 24):
            dx = abs(x + 0.5 - 16)
            if y >= 20 + max(0, (dx - 4)) * 0.8:
                c.put(x, y, "ash", 0)
    for y in range(19, 36):
        for x in range(6, 26):
            if c.m(x, y) == S and any(c.m(x + a, y + b) == "ash" for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                c.put(x, y, S, 3 if x >= 16 else 1)
    for t in ((16, 34, 3.4, 15, 24), (12, 34, 2.4, 11, 28), (20, 34, 2.4, 21, 27)):
        tongue(c, *t)
    for y in range(20, 36):
        for x in range(8, 24):
            if c.m(x, y) == "fire" and (c.m(x, y + 1) is None or y > 34):
                pass
    flame_tones(c, 24, 34)
    for x in range(8, 24):
        if c.m(x, 35) in ("fire", "ash"):
            c.put(x, 35, "ash", 1)
    for x in (10, 13, 18, 21):
        c.put(x, 34, "fire", 4 if x % 2 else 3)
    lit_by(c, {"fire"}, S, 3)
    hline(c, 2, 29, 38, S, 1)
    return {"obj.stove": to_rgba(c)}


def barrel():
    """obj.barrel 24x28: wooden staves, iron hoops, the lid seen from above."""
    c = cv(24, 28)
    W = "wood"
    for y in range(5, 27):
        bulge = 1 - ((y - 15.5) / 12) ** 2
        hw = 8.0 + 2.2 * bulge
        for x in range(24):
            if abs(x + 0.5 - 12) <= hw:
                c.put(x, y, W)
    round_shade(c, W, 12, 15, 10.5, 30, cuts=(0.97, 0.62, 0.0))
    for y in range(5, 27):  # stave seams
        for x in (6, 10, 14, 18):
            if c.m(x, y) == W:
                c.tone[y][x] = max(0, c.tone[y][x] - 1)
    for yh in (8, 9, 21, 22):
        for x in range(24):
            if c.m(x, yh) == W:
                t = c.tone[yh][x]
                c.put(x, yh, "iron", min(4, t + (1 if yh in (8, 21) else 0)))
    # the lid
    c.ellipse(12, 4.5, 8.2, 3.2, W, 3)
    for y in range(1, 9):
        for x in range(24):
            if c.m(x, y) == W and y <= 6:
                dx = (x + 0.5 - 12) / 8.2
                dy = (y + 0.5 - 4.5) / 3.2
                if dx * dx + dy * dy <= 1:
                    c.tone[y][x] = 3 if dx * dx + dy * dy > 0.55 else 2
    for x in range(6, 18):
        if c.m(x, 4) == W and x % 4 == 1:
            c.tone[4][x] = 1
    hline(c, 8, 12, 2, W, 4)
    hline(c, 6, 18, 7, W, 1)
    hline(c, 5, 19, 26, W, 1)
    return {"obj.barrel": to_rgba(c)}


def mat():
    """obj.mat 32x16: the door mat (walk down onto it to go out): a red rug, gold border, fringes."""
    c = cv(32, 16)
    c.rect(3, 2, 28, 13, "room_rug", 2)
    hline(c, 3, 28, 2, "room_rug", 3)
    hline(c, 3, 28, 13, "room_rug", 1)
    vline(c, 3, 2, 13, "room_rug", 3)
    vline(c, 28, 2, 13, "room_rug", 1)
    for x in range(5, 27):
        c.put(x, 4, "gold", 2)
        c.put(x, 11, "gold", 1)
    for y in range(4, 12):
        c.put(5, y, "gold", 2)
        c.put(26, y, "gold", 1)
    for x, y in ((15, 7), (16, 7), (14, 8), (17, 8), (15, 9), (16, 9), (10, 8), (21, 8)):  # a diamond
        c.put(x, y, "gold", 3 if y < 8 else 2)
    for y in range(3, 13, 2):  # fringes
        c.put(1, y, "string", 3)
        c.put(2, y, "string", 2)
        c.put(29, y, "string", 2)
        c.put(30, y, "string", 1)
    return {"obj.mat": drop(to_rgba(c))}


def anvil():
    """obj.anvil 32x24: an iron anvil (horn to the left) on a wooden block."""
    c = cv(32, 24)
    I = "iron"
    # face and horn
    c.rect(9, 2, 28, 6, I, 2)
    for x in range(2, 9):
        k = (9 - x) / 7
        y0 = 2 + round(k * 1.5)
        y1 = 6 - round(k * 2.5)
        for y in range(y0, y1 + 1):
            c.put(x, y, I, 2)
    hline(c, 3, 28, 2, I, 4)
    hline(c, 2, 28, 3, I, 3)
    hline(c, 2, 28, 6, I, 1)
    vline(c, 28, 2, 6, I, 1)
    c.put(24, 3, I, 0)  # the hardy hole
    # waist and foot
    c.rect(12, 7, 22, 10, I, 2)
    vline(c, 12, 7, 10, I, 3)
    vline(c, 22, 7, 10, I, 1)
    hline(c, 12, 22, 7, I, 0)
    c.rect(9, 11, 25, 13, I, 2)
    hline(c, 9, 25, 11, I, 3)
    hline(c, 9, 25, 13, I, 1)
    vline(c, 25, 11, 13, I, 1)
    # the block
    c.rect(6, 14, 27, 22, "wood", 2)
    hline(c, 6, 27, 14, "wood", 3)
    vline(c, 6, 14, 22, "wood", 3)
    vline(c, 27, 14, 22, "wood", 1)
    hline(c, 6, 27, 22, "wood", 1)
    for x in (11, 17, 23):
        vline(c, x, 16, 21, "wood", 1)
    for x, y in ((8, 17), (14, 19), (20, 16), (25, 19)):
        c.put(x, y, "wood", 3)
    return {"obj.anvil": to_rgba(c)}


# ================================================================== puzzle parts and ruins

BRAZIER = [
    [(12, 16, 4.2, 10, 1), (7, 16, 2.6, 5, 7), (17, 16, 2.6, 19, 5)],
    [(12, 16, 4.2, 14, 2), (7, 16, 2.6, 6, 4), (17, 16, 2.4, 18, 8)],
]


def brazier():
    """obj.brazier.0 / .1 24x32: a ruin-stone bowl on a stem, burning (2 frames)."""
    out = {}
    S = "ruin_stone"
    for i, ts in enumerate(BRAZIER):
        c = cv(24, 32)
        for t in ts:
            tongue(c, *t)
        flame_tones(c, 2, 16)
        # bowl
        for y in range(14, 22):
            hw = 10.5 - max(0, y - 16) * 1.2
            for x in range(24):
                if abs(x + 0.5 - 12) <= hw:
                    c.put(x, y, S, 2)
        hline(c, 2, 21, 14, S, 4)
        hline(c, 1, 22, 15, S, 3)
        hline(c, 2, 21, 16, S, 1)
        for y in range(17, 22):
            for x in range(24):
                if c.m(x, y) == S:
                    c.tone[y][x] = 3 if x < 8 else 1 if x > 16 else 2
        for x in range(4, 21, 4):  # carved band
            c.put(x, 18, S, 1)
            c.put(x + 1, 18, "ruin_glow", 1)
        # stem and foot
        box(c, 9, 22, 14, 26, S)
        box(c, 5, 27, 18, 30, S, top=3, bottom=1)
        hline(c, 9, 14, 22, S, 1)
        # embers in the bowl
        for x in range(5, 19):
            if c.m(x, 14) == "fire" or c.m(x, 13) == "fire":
                c.put(x, 14, "fire", 3 if (x + i) % 3 else 4)
        lit_by(c, {"fire"}, S, 4)
        img = to_rgba(c)
        g = c.ramps["fire"]
        for x, y, t in (((3, 4, 3), (20, 1, 4)), ((19, 3, 3), (4, 1, 4)))[i]:
            img[y][x] = g[t] + (255,)
        out[f"obj.brazier.{i}"] = img
    return out


def crystal():
    """obj.crystal 24x36: the shock crystal (breaks; its charge runs through water and metal): a cluster of
    pale-yellow electric prisms on a field stone."""
    c = cv(24, 36)
    X = "shock"

    def prism(x0, x1, ytop, ybot, tip):
        mid = (x0 + x1) / 2
        for y in range(ytop, ybot + 1):
            for x in range(x0, x1 + 1):
                if y < ytop + tip:
                    k = (y - ytop) / tip
                    if abs(x + 0.5 - mid - 0.5) > (x1 - x0 + 1) / 2 * k + 0.5:
                        continue
                f = (x - x0) / max(1, x1 - x0)
                t = 3 if f < 0.34 else 2 if f < 0.67 else 1
                c.put(x, y, X, t)

    prism(15, 19, 12, 27, 4)
    prism(3, 7, 16, 28, 4)
    prism(8, 15, 2, 28, 6)
    for y in range(4, 28):  # the bright ridge and a crack
        if c.m(10, y) == X:
            c.tone[y][10] = 4 if y < 11 or y in (16, 17) else 3
    for x, y in ((12, 13), (13, 14), (12, 15), (13, 16)):
        c.put(x, y, X, 1)
    overlap_shadow(c, [X])
    c.put(4, 18, X, 4)
    c.put(16, 14, X, 4)
    # the stone
    c.ellipse(12, 31.5, 10.5, 4.0, "stone")
    round_shade(c, "stone", 12, 31, 10.5, 4.0)
    for x in range(3, 21):
        if c.m(x, 28) == "stone" and c.m(x, 27) == X:
            c.tone[28][x] = 1
    lit_by(c, {X}, "stone", 3)
    return {"obj.crystal": to_rgba(c)}


def receiver():
    """obj.receiver.off / .on 24x32: the 星環 receiver (powers its door). A stone post with a gold ring that
    holds a gem. Off: the gem is dark, the inlay is plain stone. On: the gem and inlay glow gem blue and a
    star floats above the ring (shape + light, like the record stone)."""
    out = {}
    S = "stone"
    for on in (False, True):
        c = cv(24, 32)
        box(c, 2, 27, 21, 30, S, top=3, bottom=1)
        hline(c, 2, 21, 27, S, 4)
        box(c, 4, 24, 19, 26, S, top=3, bottom=1)
        box(c, 7, 14, 16, 23, S)
        vline(c, 8, 14, 23, S, 3)
        hline(c, 7, 16, 14, S, 1)
        for y in (17, 20):
            c.put(11, y, "gem" if on else S, 3 if on else 1)
            c.put(12, y, "gem" if on else S, 2 if on else 0)
        for x, y in ring_px(11.5, 9, 3.2, 5.6):
            c.put(x, y, "gold", 2)
        round_shade(c, "gold", 11.5, 9, 5.6, 5.6)
        for x, y in ring_px(11.5, 9, 0, 3.2):
            c.put(x, y, S, 0)
        c.ellipse(11.5, 9, 2.2, 2.2, "gem", 0)
        if on:
            round_shade(c, "gem", 11.5, 9, 2.2, 2.2, cuts=(0.9, 0.5, -1))
            c.put(10, 8, "gem", 4)
            for x, y, t in ((11, 1, 4), (10, 1, 3), (12, 1, 3), (11, 0, 3), (11, 2, 3), (4, 3, 3), (19, 3, 3)):
                c.put(x, y, "gem", t)
            lit_by(c, {"gem"}, "gold", 4)
            lit_by(c, {"gem"}, S, 3)  # only the inner rim catches the light (before the inlay is set)
        else:
            c.put(10, 8, "gem", 1)
        out["obj.receiver." + ("on" if on else "off")] = to_rgba(c)
    return out


def sconce():
    """obj.sconce.off / .on 20x36: a ruin-stone torch stand with an iron cup. On: a flame stands in the
    cup (shape) and lights the stone (light)."""
    out = {}
    S = "ruin_stone"
    for lit in (False, True):
        c = cv(20, 36)
        # cup
        for y in range(12, 17):
            hw = 7.5 - (y - 12) * 1.1
            for x in range(20):
                if abs(x + 0.5 - 10) <= hw:
                    c.put(x, y, "iron", 2)
        hline(c, 3, 16, 12, "iron", 4)
        hline(c, 2, 17, 13, "iron", 3)
        for y in range(14, 17):
            for x in range(20):
                if c.m(x, y) == "iron":
                    c.tone[y][x] = 3 if x < 7 else 1 if x > 12 else 2
        hline(c, 4, 15, 12, "ash", 1 if not lit else 2)  # coals
        # post
        box(c, 8, 17, 11, 29, S)
        for y in (21, 25):
            hline(c, 8, 11, y, S, 1)
        box(c, 5, 30, 14, 33, S, top=3, bottom=1)
        hline(c, 6, 13, 29, S, 3)
        if lit:
            for t in ((10, 12, 3.6, 9, 1), (6, 12, 2.0, 5, 6), (14, 12, 2.0, 15, 5)):
                tongue(c, *t)
            flame_tones(c, 1, 12)
            for x in range(4, 16):
                if c.m(x, 12) == "fire":
                    c.put(x, 12, "fire", 3)
            lit_by(c, {"fire"}, "iron", 4)
            for y in range(17, 22):
                c.put(8, y, S, 4)
        out["obj.sconce." + ("on" if lit else "off")] = drop(to_rgba(c))
    return out


def resonance_stone():
    """obj.stone.off / .on 24x32: the resonance stone (ruin mechanism). A rounded standing stone with a
    carved spiral. On: the spiral glows ruin teal and three motes rise above it (shape + light)."""
    out = {}
    S = "ruin_stone"
    spiral = [(12, 15), (13, 15), (13, 16), (12, 17), (11, 17), (10, 16), (10, 15), (10, 14), (11, 13),
              (12, 12), (13, 12), (14, 13), (15, 14), (15, 15), (15, 16), (15, 17), (14, 18), (13, 19),
              (12, 19), (11, 19), (10, 19), (9, 18), (8, 17), (8, 16), (8, 15), (8, 14), (8, 13), (9, 12),
              (9, 11), (10, 10), (11, 10)]
    for on in (False, True):
        c = cv(24, 32)
        c.ellipse(12, 17, 8.4, 11, S)
        for y in range(25, 31):
            for x in range(3, 21):
                c.put(x, y, S)
        round_shade(c, S, 11.5, 16, 9, 12, cuts=(0.95, 0.66, 0.15))
        box(c, 1, 27, 22, 30, S, top=3, bottom=1)
        hline(c, 1, 22, 27, S, 4)
        for i, (x, y) in enumerate(spiral):
            if on:
                c.put(x, y, "ruin_glow", 4 if i < 3 else 3 if i < 16 else 2)
            else:
                c.put(x, y, S, 0 if i % 3 else 1)
        for x, y in ((5, 24), (6, 25), (17, 23), (18, 24), (2, 29)):
            c.put(x, y, "moss", 2)
        if on:
            lit_by(c, {"ruin_glow"}, S, 3)
            for x, y, t in ((11, 1, 4), (12, 1, 3), (11, 2, 3), (6, 4, 3), (17, 3, 3), (17, 4, 2)):
                c.put(x, y, "ruin_glow", t)
        out["obj.stone." + ("on" if on else "off")] = to_rgba(c)
    return out


def pillar():
    """obj.pillar 24x48: the trial entrance pillar: a ruin-stone column with teal-glowing inlay."""
    c = cv(24, 48)
    S = "ruin_stone"
    # capital
    box(c, 2, 1, 21, 6, S, top=4, bottom=1)
    hline(c, 2, 21, 2, S, 3)
    box(c, 4, 7, 19, 9, S, top=3, bottom=1)
    # shaft with flutes
    for y in range(10, 39):
        for x in range(5, 19):
            f = (x - 5) % 4
            t = 3 if f == 0 else 1 if f == 3 else 2
            if x <= 6:
                t = 3
            if x >= 17:
                t = 1
            c.put(x, y, S, t)
    hline(c, 5, 18, 10, S, 1)
    # glowing inlay: a vertical channel and rune marks
    for y in range(12, 37):
        c.put(11, y, "ruin_glow", 3 if y % 6 else 4)
        c.put(12, y, "ruin_glow", 2)
    for y0 in (15, 25):
        for x, y in ((9, y0), (8, y0 + 1), (9, y0 + 2), (14, y0), (15, y0 + 1), (14, y0 + 2)):
            c.put(x, y, "ruin_glow", 3)
    lit_by(c, {"ruin_glow"}, S, 3)
    # base
    box(c, 3, 39, 20, 41, S, top=3, bottom=1)
    box(c, 1, 42, 22, 46, S, top=4, bottom=1)
    hline(c, 1, 22, 43, S, 3)
    for x in (7, 14, 19):
        vline(c, x, 44, 46, S, 1)
    for x, y in ((2, 45), (3, 46), (21, 45), (5, 41)):
        c.put(x, y, "moss", 2)
    return {"obj.pillar": to_rgba(c)}


def altar():
    """obj.altar 32x28: the 星環 altar: a stepped stone base holding an upright ring with gem-blue inlay."""
    c = cv(32, 28)
    S = "stone"
    # the ring (gold), its inner band of gem blue
    for x, y in ring_px(15.5, 7.5, 4.2, 6.6, 1.0):
        c.put(x, y, "gold", 2)
    round_shade(c, "gold", 15.5, 7.5, 6.6, 6.6)
    for x, y in ring_px(15.5, 7.5, 4.2, 5.0, 1.0):
        c.put(x, y, "gem", 3 if (x - 15.5) + (y - 7.5) < 0 else 2)
    for x, y in ((15, 2), (11, 6), (20, 9)):
        c.put(x, y, "gem", 4)
    # the star in the middle of the ring
    for x, y, t in ((15, 7, 4), (16, 7, 3), (15, 6, 3), (15, 8, 3), (14, 7, 3), (17, 7, 2), (16, 8, 2)):
        c.put(x, y, "gem", t)
    # the cradle under the ring
    c.rect(11, 13, 20, 15, "gold", 2)
    hline(c, 11, 20, 13, "gold", 3)
    hline(c, 11, 20, 15, "gold", 1)
    # base: two steps
    box(c, 5, 16, 26, 20, S, top=3, bottom=1)
    hline(c, 5, 26, 16, S, 4)
    box(c, 1, 21, 30, 26, S, top=3, bottom=1)
    hline(c, 1, 30, 21, S, 4)
    hline(c, 2, 29, 22, S, 3)
    for x in (9, 22):
        c.put(x, 18, "gem", 2)
        c.put(x + 1, 18, "gem", 1)
    for x in (8, 16, 24):
        vline(c, x, 23, 26, S, 1)
    lit_by(c, {"gem"}, S, 3)
    for x, y in ((2, 25), (3, 26), (28, 25)):
        c.put(x, y, "moss", 2)
    return {"obj.altar": to_rgba(c)}


def sensor():
    """sw.sensor.off / .on 24x28: the light sensor (ruin mechanism): an eye in a stone. Off: the lid is
    shut: one large closed-eye carving (no brow marks, no second line: it must not read as a face). On: the lid
    is open, the teal iris looks out and sparks rise beside the stone (shape + light)."""
    out = {}
    S = "ruin_stone"
    for on in (False, True):
        c = cv(24, 28)
        # the stone, rounded top
        for y in range(2, 26):
            hw = 9.5 if y > 5 else 9.5 - (5 - y) * 1.6
            for x in range(24):
                if abs(x + 0.5 - 12) <= hw:
                    c.put(x, y, S, 2)
        round_shade(c, S, 11, 12, 11, 16, cuts=(0.96, 0.72, 0.2))
        box(c, 1, 22, 22, 25, S, top=3, bottom=1)
        hline(c, 1, 22, 22, S, 4)
        bare = [row[:] for row in c.tone]  # the stone's own tones (the shut lid gives some back)
        # the eye socket (almond)
        for y in range(8, 17):
            for x in range(4, 20):
                dx = (x + 0.5 - 12) / 7.5
                dy = (y + 0.5 - 12.5) / 4.2
                if dx * dx + dy * dy <= 1:
                    c.put(x, y, S, 0)
        if on:
            for y in range(9, 17):
                for x in range(5, 19):
                    if c.m(x, y) == S and c.tone[y][x] == 0:
                        dx = (x + 0.5 - 12) / 6.6
                        dy = (y + 0.5 - 12.5) / 3.4
                        if dx * dx + dy * dy <= 1:
                            c.put(x, y, "linen", 2 if y > 12 else 3)
            c.ellipse(12, 12.5, 3.2, 3.2, "ruin_glow", 3)
            round_shade(c, "ruin_glow", 12, 12.5, 3.2, 3.2)
            c.rect(11, 12, 12, 13, "ash", 0)
            c.put(10, 11, "ruin_glow", 4)
            # no marks on the brow (inspection: two marks over the eye read as a face)
            lit_by(c, {"ruin_glow"}, S, 3)
            # sparks beside the brow: the silhouette changes too (guide 4.2)
            for x, y, t in ((3, 3, 4), (2, 4, 3), (20, 3, 3), (21, 4, 2), (12, 0, 4)):
                c.put(x, y, "ruin_glow", t)
        else:
            # the shut lid: ONE large closed eye (inspection 1: no brow marks and no second line under it, which
            # read as a sleeping face). The socket is filled back with stone; one wide carved groove curves down
            # from corner to corner (the closed lid), its lower lip catching the light, with three short lashes.
            for y in range(8, 17):
                for x in range(4, 20):
                    if c.m(x, y) == S and c.tone[y][x] == 0:
                        c.tone[y][x] = bare[y][x]

            lid = dict(zip(range(4, 20), (10, 11, 11, 12, 12, 12, 13, 13, 13, 13, 12, 12, 12, 11, 11, 10)))
            for x, y in lid.items():
                c.put(x, y, S, 0)
                c.put(x, y + 1, S, 3 if x < 14 else 2)
            for x, y in ((6, 13), (5, 14), (9, 14), (9, 15), (14, 14), (14, 15), (17, 13), (18, 14)):
                c.put(x, y, S, 0)
        out["sw.sensor." + ("on" if on else "off")] = drop(to_rgba(c))
    return out


def star_ring():
    """obj.star_ring.off / .on 48x52 (feet): the 星環 standing ring on the beach (the gate to the source).
    A thick ring of field stone, built of blocks, stands in a two-step plinth; a gem-blue inlay runs round
    its face with four set stones (the seats) at the top, the sides and the bottom. Gem blue = 星環 (guide).
    Off: dormant: the inlay and the seats are dark blue, the middle is open (the sand shows through).
    On: the middle fills with light on the same gem ramp (bright core, opaque pixels only), the inlay and the
    seats light up, the stone beside them catches the light, and sparks rise beside the ring (shape + light)."""
    out = {}
    S = "stone"
    cx, cy, ro, ri = 24.0, 22.5, 21.0, 14.0
    for on in (False, True):
        c = cv(48, 52)
        # the ring: blocks of stone, lit from the top left
        for x, y in ring_px(cx, cy, ri, ro):
            c.put(x, y, S, 2)
        round_shade(c, S, cx, cy, ro, ro, cuts=(0.9, 0.62, 0.15))
        for k in range(12):  # the joints between the blocks (radial), not across the inlay
            a = (k + 0.5) / 12 * 2 * math.pi
            for r10 in range(int(ri * 10) + 5, int(ro * 10) - 4, 3):
                r = r10 / 10
                if 16.0 <= r <= 18.6:
                    continue
                x, y = int(cx + r * math.cos(a)), int(cy + r * math.sin(a))
                if c.m(x, y) == S:
                    c.tone[y][x] = 1
        if on:
            # the light in the middle: bright core, the same ramp to the edge
            for y in range(52):
                for x in range(48):
                    d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                    if d < ri - 0.01 and c.m(x, y) is None:
                        c.put(x, y, "gem", 4 if d < 6.5 else 3 if d < 11.0 else 2)
            for x, y in ((23, 13), (23, 14), (23, 30), (23, 31), (14, 22), (15, 22), (32, 22), (33, 22),
                         (17, 16), (30, 16), (17, 28), (30, 28)):  # a faint star of rays through the light
                c.put(x, y, "gem", 3 if 12 <= x <= 35 and 11 <= y <= 33 and math.hypot(x + 0.5 - cx, y + 0.5 - cy) < 11 else 4)
            lit_by(c, {"gem"}, S, 3)
            for x, y, t in ((2, 9, 4), (3, 8, 3), (1, 15, 3), (45, 9, 3), (44, 8, 4), (46, 15, 3),
                            (24, 0, 4), (8, 1, 3), (39, 1, 3)):  # sparks rising beside the ring
                c.put(x, y, "gem", t)
        # the inlay (a groove of gem blue round the face)
        for x, y in ring_px(cx, cy, 16.6, 18.0):
            up_left = (x + 0.5 - cx) + (y + 0.5 - cy) < 0
            c.put(x, y, "gem", (4 if up_left else 3) if on else (1 if up_left else 0))
        # the four seats: gem stones set in the inlay (N, E, S, W)
        for sx, sy in ((cx, cy - 17.3), (cx + 17.3, cy), (cx, cy + 17.3), (cx - 17.3, cy)):
            x0, y0 = int(sx - 1.5), int(sy - 1.5)
            for dy in range(3):
                for dx in range(3):
                    if (dx, dy) in ((0, 0), (2, 0), (0, 2), (2, 2)):
                        continue
                    if on:
                        t = 4 if dx + dy <= 2 else 3
                    else:
                        t = 3 if (dx, dy) == (1, 0) else 2 if dx + dy <= 2 else 1
                    c.put(x0 + dx, y0 + dy, "gem", t)
        # the plinth the ring stands in: two steps of the same stone
        box(c, 9, 39, 38, 45, S, top=3, bottom=1)
        hline(c, 9, 38, 39, S, 4)
        for x in (16, 24, 31):
            vline(c, x, 40, 45, S, 1)
        box(c, 4, 46, 43, 50, S, top=3, bottom=1)
        hline(c, 4, 43, 46, S, 4)
        hline(c, 5, 42, 47, S, 3)
        for x in (12, 21, 30, 38):
            vline(c, x, 48, 50, S, 1)
        out["obj.star_ring." + ("on" if on else "off")] = drop(to_rgba(c))
    return out


# ================================================================== icons (20x20; content within 18x18)

def icon_bow():
    """Wood, string (bone), leather grip: a thick bow on the diagonal, bowing up-left, lit wooden tips."""
    c = cv(20, 20)
    P0, P1, P2 = (3.5, 15.5), (2.6, 2.6), (15.5, 3.5)
    pts = []
    for i in range(41):
        t = i / 40
        x = (1 - t) ** 2 * P0[0] + 2 * t * (1 - t) * P1[0] + t * t * P2[0]
        y = (1 - t) ** 2 * P0[1] + 2 * t * (1 - t) * P1[1] + t * t * P2[1]
        pts.append((int(x), int(y), t))
    for x, y, t in pts:  # the limb: two pixels thick toward the string, the outer side lit
        c.put(x + 1, y + 1, "wood", 2 if t < 0.75 else 1)  # the inner face: core, shade only at the far tip
    for x, y, t in pts:  # the middle of the limb is lit too (inspection 3, guide 6.1: dark wood, more tone 3)
        c.put(x, y + 1, "wood", 3)
        c.put(x + 1, y, "wood", 3)
    for x, y, t in pts:
        c.put(x, y, "wood", 3)
    for x, y in ((5, 6), (6, 5), (4, 8)):
        c.put(x, y, "wood", 4)
    c.line(4, 16, 16, 4, "bone", 3)  # the string
    for x, y in ((3, 16), (4, 15), (15, 3), (16, 4)):  # the tips: lit wood (3 materials: wood, string, grip)
        c.put(x, y, "wood", 4)
    c.put(4, 16, "wood", 3)
    c.put(16, 3, "wood", 3)
    for x, y, t in ((5, 6, 3), (6, 6, 2), (6, 5, 3), (7, 6, 2), (6, 7, 1)):  # the grip
        c.put(x, y, "leather", t)
    return to_rgba(c)


def icon_armor():
    """A leather jerkin with a laced seam, steel shoulder guards, a gold belt buckle."""
    c = cv(20, 20)
    L = "leather"
    for y in range(4, 18):
        if y <= 10:
            x0, x1 = 4, 15
        elif y <= 12:
            x0, x1 = 5, 14
        else:
            x0, x1 = 4, 15
        for x in range(x0, x1 + 1):
            # the lit face is wide (inspection 3, guide 6.1: a dark material needs more of tone 3): the chest
            # and the left of the skirt take the light, only the right edge falls into shade
            lit = x <= x0 + 2 or (y <= 10 and x <= x1 - 2) or (y >= 13 and x <= x1 - 3)
            c.put(x, y, L, 3 if lit else 1 if x >= x1 else 2)
    for y, w in ((4, 2), (5, 2), (6, 1), (7, 0)):  # the V neck
        for x in range(10 - w - 1, 10 + w):
            c.mat[y][x] = None
    for y in range(5, 11):  # the lacing seam
        c.put(9 if y > 7 else 10, y, L, 1)
    for y in (8, 10):
        c.put(10, y, "gold", 3)
    hline(c, 5, 14, 11, L, 1)
    hline(c, 5, 14, 12, L, 0)
    c.rect(9, 11, 10, 12, "gold", 3)
    c.put(9, 11, "gold", 4)
    c.put(10, 12, "gold", 1)
    hline(c, 4, 15, 17, L, 1)
    for x in (6, 9, 12):
        vline(c, x, 14, 17, L, 1)
    for cx0, side in ((4.5, 0), (15.5, 1)):  # shoulder guards: caps over the shoulders
        for y in range(2, 7):
            for x in range(1, 19):
                dx = (x + 0.5 - cx0) / 3.1
                dy = (y + 0.5 - 6.0) / 3.6
                if dx * dx + dy * dy <= 1 and 2 <= x <= 17:
                    c.put(x, y, "steel")
    round_shade(c, "steel", 9.5, 6, 9, 5, cuts=(0.96, 0.6, 0.15))
    for y in range(2, 6):  # the right guard keeps its shade only on its outer column (inspection 3)
        for x in range(12, 17):
            if c.m(x, y) == "steel" and c.tone[y][x] == 1:
                c.tone[y][x] = 2
    for x in range(2, 18):
        if c.m(x, 6) == "steel":  # the guards' lower rim: in shade on the right only (inspection 3)
            c.tone[6][x] = 1 if x >= 14 else 2
    c.put(3, 3, "steel", 4)
    return to_rgba(c)


def icon_mushroom():
    """A red cap with pale spots (bone), a pale stem."""
    c = cv(20, 20)
    c.rect(8, 10, 12, 16, "bone", 2)
    vline(c, 8, 10, 16, "bone", 3)
    vline(c, 12, 10, 16, "bone", 1)
    hline(c, 7, 13, 17, "bone", 1)
    c.put(7, 16, "bone", 2)
    c.put(13, 16, "bone", 1)
    for y in range(3, 11):
        for x in range(2, 18):
            dx = (x + 0.5 - 10) / 7.6
            dy = (y + 0.5 - 10.5) / 7.4
            if dx * dx + dy * dy <= 1:
                c.put(x, y, "cap")
    round_shade(c, "cap", 8.5, 9, 8, 7, cuts=(0.94, 0.6, 0.1))
    hline(c, 3, 16, 10, "cap", 1)
    for x, y in ((6, 6), (7, 6), (6, 7), (12, 5), (13, 5), (14, 8), (9, 4), (10, 8), (11, 8)):
        c.put(x, y, "bone", 3 if x < 10 else 2)
    c.put(6, 6, "bone", 4)
    hline(c, 8, 12, 11, "bone", 1)
    return to_rgba(c)


def icon_berry():
    """Three red berries and two leaves."""
    c = cv(20, 20)
    for m, cx, cy in (("e0", 6.5, 12.5), ("e1", 13, 13.5), ("e2", 9.5, 8.5)):
        c.ramps[m] = c.ramps["berry"]
        c.ellipse(cx, cy, 3.6, 3.6, m)
        round_shade(c, m, cx, cy, 3.6, 3.6, cuts=(0.95, 0.62, 0.05))
        c.put(int(cx) - 1, int(cy) - 1, m, 4)
    overlap_shadow(c, ["e0", "e1", "e2"])
    c.ramps["lf"] = c.ramps["leaf"]
    for (x, y, t) in ((11, 3, 3), (12, 3, 3), (13, 3, 2), (12, 4, 2), (14, 4, 2), (15, 4, 1), (13, 2, 3),
                      (8, 3, 3), (7, 3, 3), (6, 4, 2), (7, 4, 2), (10, 4, 2), (10, 5, 1)):
        c.put(x, y, "lf", t)
    c.put(13, 2, "lf", 4)
    return to_rgba(c)


def icon_pepper():
    """The ember pepper: a curved red pod on the diagonal, its green cap and stalk at the top right."""
    c = cv(20, 20)
    for i in range(14):
        t = i / 13
        cx = 13.6 - i * 0.6 - t * t * 2.6
        cy = 6.0 + i * 0.82
        r = 2.9 * (1 - t) ** 0.8 + 0.7
        c.ellipse(cx, cy, r, r, "pepper")
    round_shade(c, "pepper", 9.5, 9, 6, 6, cuts=(0.97, 0.72, 0.1))
    for x, y in ((11, 5), (10, 6), (9, 8), (8, 9)):
        if c.m(x, y) == "pepper":
            c.shade(x, y, 4 if (x, y) == (11, 5) else 3)
    for x, y, t in ((12, 4, 3), (13, 4, 2), (14, 4, 2), (15, 5, 1), (11, 4, 2), (14, 3, 3), (15, 2, 3), (16, 2, 2)):
        c.put(x, y, "leaf", t)
    return to_rgba(c)


def icon_fang():
    """A beast fang on a leather cord: bone, leather."""
    c = cv(20, 20)
    for y in range(4, 18):
        t = (y - 4) / 13
        cx = 7 + 6 * t * t
        hw = 3.2 * (1 - t) + 0.4
        for x in range(20):
            if abs(x + 0.5 - cx) <= hw:
                c.put(x, y, "bone")
    for y in range(20):
        for x in range(20):
            if c.m(x, y) == "bone":
                l = c.m(x - 1, y) != "bone"
                r = c.m(x + 1, y) != "bone"
                c.tone[y][x] = 3 if l else 1 if r else 3 if y < 9 else 2
    c.put(5, 6, "bone", 4)
    c.put(5, 7, "bone", 4)
    hline(c, 4, 11, 4, "leather", 2)
    hline(c, 4, 11, 3, "leather", 3)
    for x, y in ((3, 4), (2, 5), (12, 4), (13, 5), (14, 6)):
        c.put(x, y, "leather", 1)
    return to_rgba(c)


def icon_shard():
    """The murk crystal shard: miasma purple, an enemy-magic glint inside."""
    c = cv(20, 20)
    M = "miasma"
    c.poly([(11, 2), (16, 7), (13, 18), (5, 15), (4, 7)], M)
    for y in range(20):
        for x in range(20):
                c.tone[y][x] = 3 if x < 10 else 2 if x < 13 else 1
                c.tone[y][x] = 4 if x < 7 and y < 9 else 3 if x < 10 else 2
    c.line(11, 3, 9, 16, M, 2)
    c.line(10, 3, 8, 15, M, 4)
    for x, y, t in ((7, 7, 3), (7, 8, 2), (6, 9, 2), (12, 11, 2), (13, 10, 3)):
        c.put(x, y, "enemy_magic", t)
    c.put(7, 6, "enemy_magic", 4)
    c.put(6, 7, M, 4)
    return to_rgba(c)


def icon_arrows():
    """Two arrows on the diagonal: wood shafts, steel heads with barbs, pale fletching (bone)."""
    c = cv(20, 20)

    def arrow_at(tx, ty, n, shaft_t):
        for i in range(n):
            c.put(tx + i, ty - i, "wood", shaft_t)
        hx_, hy = tx + n, ty - n
        for x, y, t in ((hx_, hy, 4), (hx_ - 1, hy, 3), (hx_, hy + 1, 2), (hx_ - 2, hy, 3), (hx_, hy + 2, 1),
                        (hx_ - 1, hy + 1, 2)):
            c.put(x, y, "steel", t)
        for x, y, t in ((tx - 1, ty, 3), (tx, ty - 1, 3), (tx + 1, ty, 2), (tx, ty + 1, 2), (tx - 1, ty - 1, 4),
                        (tx + 1, ty + 1, 1)):
            c.put(x, y, "bone", t)
        c.put(tx - 1, ty + 1, "wood", 1)

    arrow_at(4, 12, 10, 3)
    arrow_at(8, 15, 8, 2)
    return to_rgba(c)


def icon_food():
    """A bowl of stew: clay bowl, stew, a green leaf."""
    c = cv(20, 20)
    for y in range(9, 17):
        hw = 8 - max(0, y - 11) * 0.9
        for x in range(20):
            if abs(x + 0.5 - 10) <= hw:
                c.put(x, y, "clay")
    round_shade(c, "clay", 8, 9, 10, 9, cuts=(0.95, 0.6, 0.1))
    hline(c, 7, 13, 17, "clay", 1)
    c.ellipse(10, 9, 7.4, 2.6, "stew", 2)
    hline(c, 4, 15, 8, "stew", 3)
    hline(c, 5, 10, 8, "stew", 4)  # the heap catches the light on the left (inspection 3)
    for x, y in ((6, 9), (12, 10), (9, 8), (14, 9)):
        c.put(x, y, "stew", 1)
    for x, y in ((7, 8), (11, 8)):
        c.put(x, y, "stew", 4)
    # the rim: a bright lip (inspection 3: the bowl melted into the path and the red sand, whose brightness
    # is the clay's middle tones), the lit front of the rim under it, dark where it turns away on the right
    hline(c, 3, 15, 11, "clay", 4)
    c.put(16, 11, "clay", 3)
    hline(c, 4, 11, 12, "clay", 3)
    for x, y, t in ((12, 6, 3), (13, 6, 2), (13, 5, 3), (14, 5, 2), (11, 7, 2), (12, 7, 1)):
        c.put(x, y, "leaf", t)
    return to_rgba(c)


def icons2():
    return {
        "icon.bow": icon_bow(), "icon.armor": icon_armor(), "icon.mushroom": icon_mushroom(),
        "icon.berry": icon_berry(), "icon.pepper": icon_pepper(), "icon.fang": icon_fang(),
        "icon.shard": icon_shard(), "icon.arrows": icon_arrows(), "icon.food": icon_food(),
    }


# ================================================================== effects and UI

def glider():
    """fx.glider 44x20 (feet = the hero's shoulders): a striped canopy (shirt white and gold, the hero's
    colours) lit on top, its underside in shade, a wooden spar, two cords down to the shoulders."""
    c = cv(44, 20)
    cx = 21.5
    for y in range(1, 11):
        for x in range(44):
            dx = (x + 0.5 - cx) / 21
            dy = (y + 0.5 - 11) / 10
            if dx * dx + dy * dy <= 1:
                stripe = int((x + 2) // 6) % 2
                c.put(x, y, "gold" if stripe else "shirt", 2)
    for y in range(1, 11):
        for x in range(44):
            m = c.m(x, y)
            if m is None:
                continue
            up = c.m(x, y - 1) is None
            t = 3 if (up and x < cx) else 2
            if y >= 8:
                t = 1
            if x > 34 and y > 4:
                t = 1
            if up and x < 14:
                t = 4 if m == "shirt" else 3
            c.tone[y][x] = t
    hline(c, 2, 41, 10, "wood", 2)
    c.put(2, 10, "wood", 3)
    c.put(41, 10, "wood", 1)
    c.line(4, 11, 15, 18, "leather", 2)
    c.line(39, 11, 28, 18, "leather", 1)
    return {"fx.glider": to_rgba(c)}


def shadow():
    """fx.shadow 24x10: one dark oval, one colour (the game sets its transparency)."""
    from draw import hx
    col = hx("#141414") + (255,)
    img = [[None] * 24 for _ in range(10)]
    for y in range(10):
        for x in range(24):
            if ((x + 0.5 - 12) / 12) ** 2 + ((y + 0.5 - 5) / 5) ** 2 <= 1:
                img[y][x] = col
    return {"fx.shadow": img}


def arrow():
    """fx.arrow 20x6 (centre, points right; the game rotates it): steel head, wood shaft, pale fletching."""
    c = cv(20, 6)
    hline(c, 4, 14, 2, "wood", 3)
    hline(c, 4, 14, 3, "wood", 1)
    for x, y, t in ((15, 1, 3), (15, 2, 3), (15, 3, 2), (15, 4, 1), (16, 1, 3), (16, 2, 4), (16, 3, 2),
                    (17, 2, 3), (17, 3, 1)):
        c.put(x, y, "steel", t)
    for x, y, t in ((1, 1, 3), (2, 1, 3), (3, 2, 3), (1, 4, 2), (2, 4, 2), (3, 3, 2)):
        c.put(x, y, "bone", t)
    return {"fx.arrow": to_rgba(c)}


MARKER = [
    "..............",
    "..............",
    "..dc..........",
    "..dccc........",
    "..dcccbb......",
    "...cccbbbb....",
    "....dccbbbbc..",
    "....bbbbbbaa..",
    "...bbbbbaa....",
    "..bbbbaa......",
    "..bbaa........",
    "..aa..........",
    "..............",
    "..............",
]


def orb():
    """fx.orb 12x12 (centre): the enemy's magic bullet in enemy-magic red-purple, a white-pink core."""
    c = cv(12, 12)
    c.ellipse(6, 6, 4.6, 4.6, "enemy_magic")
    round_shade(c, "enemy_magic", 6, 6, 4.6, 4.6, cuts=(0.9, 0.55, 0.0))
    c.rect(4, 4, 5, 5, "enemy_magic", 4)
    c.put(6, 4, "enemy_magic", 3)
    return {"fx.orb": to_rgba(c)}


def shield_fx():
    """fx.shield 16x18 (centre): the hero's shield from the front: wood face, steel rim, gold star boss,
    the gem in the middle (the same shield as the hero's guard frames)."""
    c = cv(16, 18)
    cx, cy, rx, ry = 8, 9, 6.6, 7.6
    for y in range(18):
        for x in range(16):
            d = ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2
            if d <= 1:
                rim = d > 0.66
                lit = (x - cx) + (y - cy) < -1
                c.put(x, y, "steel" if rim else "wood", (3 if lit else 1) if rim else (3 if lit else 2))
    for x, y in ((5, 3), (4, 4)):
        c.put(x, y, "steel", 4)
    for x in range(5, 12):  # the planks
        if (x - 5) % 3 == 2:
            for y in range(4, 15):
                if c.m(x, y) == "wood":
                    c.tone[y][x] = 1
    for dx, dy in ((0, -2), (0, 2), (-2, 0), (2, 0), (0, -1), (0, 1), (-1, 0), (1, 0), (0, 0)):
        c.put(7 + dx, 8 + dy, "gold", 3 if dx <= 0 and dy <= 0 else 2)
    c.put(7, 8, "gem", 4)
    return {"fx.shield": to_rgba(c)}


def bow_fx():
    """fx.bow 10x24 (centre): the hero's bow upright, string on the left: wood, string, gold tips, grip."""
    c = cv(10, 24)
    pts = []
    for y in range(2, 22):
        t = (y - 11.5) / 9.5
        x = round(3 + 4.0 * (1 - t * t))
        pts.append((x, y))
    for x, y in pts:
        c.put(x, y, "wood", 3)
        if 4 < y < 19:
            c.put(x + 1, y, "wood", 1)
    for y in range(2, 22):
        if y not in (2, 21):
            c.put(2, y, "bone", 3)
    c.put(3, 2, "gold", 3)
    c.put(3, 21, "gold", 2)
    c.rect(6, 10, 7, 13, "leather", 2)
    c.put(6, 10, "leather", 3)
    c.put(5, 6, "wood", 4)
    return {"fx.bow": to_rgba(c)}


def smoke():
    """fx.smoke 12x12 (centre): a grey puff (the game grows and fades it)."""
    c = cv(12, 12)
    c.ellipse(5, 6.6, 3.8, 3.6, "smoke")
    c.ellipse(7.4, 5.2, 3.4, 3.4, "smoke")
    round_shade(c, "smoke", 5.6, 5.4, 5, 5, cuts=(0.95, 0.66, 0.15))
    return {"fx.smoke": to_rgba(c)}


def light_orb():
    """fx.light 16x16 (centre): the light orb carried to the sensors: a warm gold-white ball, four short rays."""
    c = cv(16, 16)
    c.ellipse(8, 8, 4.6, 4.6, "gold")
    round_shade(c, "gold", 8, 8, 4.6, 4.6, cuts=(0.75, 0.3, -0.3))
    for y in range(16):
        for x in range(16):
            if c.m(x, y) == "gold" and c.tone[y][x] == 1:
                c.tone[y][x] = 2
    for x, y in ((8, 1), (7, 1), (8, 14), (7, 14), (1, 8), (1, 7), (14, 7), (14, 8)):
        c.put(x, y, "gold", 3)
    c.rect(6, 6, 7, 7, "gold", 4)
    return {"fx.light": to_rgba(c)}


def marker():
    """ui.marker 14x14 (centre, points right; screen space, rotated toward the landmark): a gold arrow head,
    notched at the back, lit on its upper half."""
    c = cv(14, 14)
    lg = {"a": ("gold", 1), "b": ("gold", 2), "c": ("gold", 3), "d": ("gold", 4)}
    for y, row in enumerate(MARKER):
        for x, ch in enumerate(row):
            if ch in lg:
                c.put(x, y, *lg[ch])
    return {"ui.marker": to_rgba(c)}


# ================================================================== registry

def all_wave2():
    out = {}
    for f in (door, cave, stairs, lowwall, bed, table, shelves, counter, stove, barrel, mat, anvil,
              brazier, crystal, receiver, sconce, resonance_stone, pillar, altar, sensor, star_ring,
              icons2, glider, shadow, arrow, orb, shield_fx, bow_fx, smoke,
              light_orb, marker):
        out.update(f())
    return out


SIZES2 = {
    "obj.door": (32, 40), "obj.cave": (32, 28), "obj.stairs": (32, 32),
    "obj.lowwall": (32, 24), "obj.bed": (32, 52), "obj.table": (32, 28), "obj.shelf": (32, 40),
    "obj.charm_shelf": (32, 40), "obj.charm_shelf.on": (32, 40), "obj.counter": (32, 32),
    "obj.stove": (32, 40), "obj.barrel": (24, 28), "obj.mat": (32, 16), "obj.anvil": (32, 24),
    "obj.brazier.0": (24, 32), "obj.brazier.1": (24, 32), "obj.crystal": (24, 36),
    "obj.receiver.off": (24, 32), "obj.receiver.on": (24, 32), "obj.sconce.off": (20, 36),
    "obj.sconce.on": (20, 36), "obj.stone.off": (24, 32), "obj.stone.on": (24, 32),
    "obj.pillar": (24, 48), "obj.altar": (32, 28), "sw.sensor.off": (24, 28), "sw.sensor.on": (24, 28),
    "obj.star_ring.off": (48, 52), "obj.star_ring.on": (48, 52),
    **{f"icon.{n}": (20, 20) for n in ("bow", "armor", "mushroom", "berry", "pepper", "fang", "shard", "arrows", "food")},
    "fx.glider": (44, 20), "fx.shadow": (24, 10), "fx.arrow": (20, 6), "fx.orb": (12, 12),
    "fx.shield": (16, 18), "fx.bow": (10, 24), "fx.smoke": (12, 12), "fx.light": (16, 16),
    "ui.marker": (14, 14),
}
CENTRE2 = {"fx.shadow", "fx.arrow", "fx.orb", "fx.shield", "fx.bow", "fx.smoke", "fx.light", "ui.marker"}
ANCHOR2 = {k: ("centre" if k in CENTRE2 else "feet") for k in SIZES2}
# lies flat on the floor or is cut by the cliff / repeats: no ground line rule needed beyond the last row
TILING2 = {"obj.lowwall", "obj.counter"}
