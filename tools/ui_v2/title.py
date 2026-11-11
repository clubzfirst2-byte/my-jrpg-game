"""The title: the logo 「星環のレガリア」 and a layered vista (sky, sea, the island with the star ring, a
foreground frame). 1 art px = 2 CSS px (6 device px on iPhone 15 Pro, 4 on SE): crisp, integer.

The lettering is original hand-drawn pixel art: each character is written below as its own strokes on a
24 x 24 grid (no font is used or traced), scaled to the logo size and cut 3 px thick, then gets the game's
treatment: a gold ramp lit from the top, a navy outline and a gem-blue outer line, a drop shadow; の sits
in the star ring emblem.
"""

import math
import random

from common import col, new, outline

# Hand-drawn strokes per character on a 24 x 24 grid: ("h", x0, x1, y) horizontal, ("v", x, y0, y1)
# vertical, ("p", (x, y), (x, y), ...) a polyline (diagonals and curves, point to point).
GLYPHS = {
    "星": [  # 日 over 生
        ("v", 5, 1, 9), ("v", 18, 1, 9), ("h", 5, 18, 1), ("h", 5, 18, 5), ("h", 5, 18, 9),
        ("p", (8, 11), (6, 14), (3, 16)), ("h", 5, 19, 14), ("v", 11, 11, 22), ("h", 6, 17, 18), ("h", 1, 22, 22),
    ],
    "環": [  # 王 (the jewel radical) beside a simplified 睘: 罒, one bar, a centre post and two sweeps
        ("h", 0, 6, 2), ("h", 1, 5, 10), ("v", 3, 2, 18), ("p", (0, 21), (7, 17)),
        ("h", 10, 22, 1), ("h", 10, 22, 7), ("v", 10, 1, 7), ("v", 22, 1, 7), ("v", 14, 1, 7), ("v", 18, 1, 7),
        ("h", 11, 21, 11), ("v", 16, 11, 23), ("p", (15, 15), (9, 22)), ("p", (17, 15), (23, 22)),
    ],
    "の": [
        ("p", (13, 4), (12, 10), (10, 16), (8, 20), (6, 21), (4, 20), (3, 17), (3, 12), (5, 8), (8, 5), (12, 3),
         (16, 3), (19, 5), (21, 8), (22, 12), (21, 16), (19, 19), (16, 21), (13, 22)),
    ],
    "レ": [
        ("v", 5, 2, 19), ("p", (5, 20), (8, 21), (12, 20), (16, 17), (19, 14), (21, 11)),
    ],
    "ガ": [  # カ + the voiced marks
        ("h", 2, 16, 7), ("p", (16, 7), (16, 17), (15, 20), (13, 21), (11, 21)),
        ("p", (10, 1), (10, 7), (9, 12), (7, 17), (3, 22)),
        ("p", (18, 0), (19, 2)), ("p", (21, 0), (22, 2)),
    ],
    "リ": [
        ("v", 6, 3, 13), ("p", (6, 14), (7, 15)),
        ("v", 17, 1, 13), ("p", (17, 14), (16, 17), (14, 20), (11, 22), (8, 23)),
    ],
    "ア": [
        ("h", 3, 21, 3), ("p", (21, 3), (20, 5), (18, 7), (16, 9)),
        ("p", (12, 8), (12, 13), (11, 17), (9, 20), (5, 23)),
    ],
}
TEXT_A, TEXT_NO, TEXT_B = "星環", "の", "レガリア"
SCALE = 1.25  # 24-grid -> 30 px glyphs
THICK = 3  # px per stroke


def _line(m, x0, y0, x1, y1):
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):
        x = round(x0 + (x1 - x0) * i / n)
        y = round(y0 + (y1 - y0) * i / n)
        if 0 <= y < len(m) and 0 <= x < len(m[0]):
            m[y][x] = True


def _glyph_mask(ch):
    """One hand-drawn character, scaled and thickened (a bold pixel cut), trimmed to its ink left and
    right (its height stays the full cell, so all characters share one baseline)."""
    cell = int(24 * SCALE) + THICK + 1
    m = [[False] * cell for _ in range(cell)]
    S = lambda v: round(v * SCALE)  # noqa: E731
    for st in GLYPHS[ch]:
        if st[0] == "h":
            _line(m, S(st[1]), S(st[3]), S(st[2]), S(st[3]))
        elif st[0] == "v":
            _line(m, S(st[1]), S(st[2]), S(st[1]), S(st[3]))
        else:
            pts = st[1:]
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                _line(m, S(ax), S(ay), S(bx), S(by))
    out = [row[:] for row in m]
    for y in range(cell):  # thicken: each stroke grows right and down
        for x in range(cell):
            if m[y][x]:
                for dy in range(THICK):
                    for dx in range(THICK):
                        if y + dy < cell and x + dx < cell:
                            out[y + dy][x + dx] = True
    cols = [x for x in range(cell) if any(out[y][x] for y in range(cell))]
    return [row[cols[0]:cols[-1] + 1] for row in out]


def _word(text, gap):
    parts = [_letters(_glyph_mask(ch), "gold") for ch in text]
    w = sum(p.width for p in parts) + gap * (len(parts) - 1)
    im = new(w, max(p.height for p in parts))
    x = 0
    for p in parts:
        im.alpha_composite(p, (x, 0))
        x += p.width + gap
    return im


def _letters(mask, mat):
    h, w = len(mask), len(mask[0])
    im = new(w, h)
    rows = [y for y in range(h) if any(mask[y])]
    y0, y1 = rows[0], rows[-1]
    for y in range(h):
        for x in range(w):
            if not mask[y][x]:
                continue
            f = (y - y0) / max(1, y1 - y0)
            t = 4 if f < 0.22 else 3 if f < 0.55 else 2
            if y + 1 < h and not mask[y + 1][x]:
                t = 1  # the underside of each stroke
            if (y == 0 or not mask[y - 1][x]) and t >= 2:
                t = 4  # the lit top of each stroke
            im.putpixel((x, y), col(mat, t))
    return im


def logo():
    gap = 3  # between characters: tight and even
    a = _word(TEXT_A, gap)
    no = _letters(_glyph_mask(TEXT_NO), "gold")
    b = _word(TEXT_B, gap)
    R_IN, R_OUT = 18.5, 23.5
    ring_w = int(2 * R_OUT) + 2
    W = 4 + a.width + gap + ring_w + gap + b.width + 4
    H = 64
    im = new(W, H)
    cy = 33
    # the star ring emblem behind の: a gem ring, a gold four-pointed star on top, small stars around
    rx0 = 4 + a.width + gap + ring_w // 2
    for y in range(H):
        for x in range(W):
            d = math.hypot(x - rx0 + 0.5, (y - cy + 0.5) * 1.0)
            if R_IN <= d <= R_OUT:
                lit = -((x - rx0) + (y - cy)) / max(d, 1)
                t = 4 if d < R_IN + 1 and lit > 0.3 else 3 if lit > 0.2 else 2 if lit > -0.5 else 1
                im.putpixel((x, y), col("gem", t))
            elif R_OUT < d <= R_OUT + 1 or R_IN - 1 <= d < R_IN:
                im.putpixel((x, y), col("navy", 0))
    for k in range(8):  # stars set into the ring
        ang = math.radians(k * 45 - 90)
        sx, sy = round(rx0 + (R_IN + R_OUT) / 2 * math.cos(ang)), round(cy + (R_IN + R_OUT) / 2 * math.sin(ang))
        for dx, dy, t in ((0, 0, 4), (1, 0, 3), (-1, 0, 3), (0, 1, 3), (0, -1, 3)):
            im.putpixel((sx + dx, sy + dy), col("bone", t))
    # the letters, with a drop shadow and a double outline
    letters = new(W, H)
    letters.alpha_composite(a, (4, cy - a.height // 2))
    letters.alpha_composite(no, (rx0 - no.width // 2, cy - no.height // 2))
    letters.alpha_composite(b, (4 + a.width + gap + ring_w + gap, cy - b.height // 2))
    outline(letters, col("navy", 0), diagonal=True)
    outline(letters, col("gem", 1))
    shadow = new(W, H)
    for y in range(H):
        for x in range(W):
            if letters.getpixel((x, y))[3]:
                if y + 2 < H:
                    shadow.putpixel((x, y + 2), col("navy", 0))
    im.alpha_composite(shadow)
    im.alpha_composite(letters)
    # the big star on top of the ring
    sx, sy = rx0, cy - int(R_OUT) - 2
    pts = {(sx, sy)}
    for k in range(1, 6):
        w = max(0, 2 - k // 2)
        for j in range(-w, w + 1):
            pts |= {(sx + j, sy - k), (sx + j, sy + k)} if k < 4 else {(sx, sy - k), (sx, sy + k)}
            pts |= {(sx - k, sy + j), (sx + k, sy + j)} if k < 4 else {(sx - k, sy), (sx + k, sy)}
    pts = {(x, y) for x, y in pts if 0 <= y < H}
    for x, y in pts:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in pts and 0 <= y + dy < H:
                im.putpixel((x + dx, y + dy), col("navy", 0))
    for x, y in pts:
        im.putpixel((x, y), col("gold", 4 if (x <= sx and y <= sy) else 3))
    return im


# ---------------------------------------------------------------- the vista (480 x 200, ×2 CSS)

W, H, HORIZON = 480, 200, 118


def sky():
    im = new(W, H)
    bands = [(0, ("sky", 0)), (26, ("sky", 1)), (52, ("sky", 2)), (74, ("sky", 3)), (90, ("sky", 4)),
             (101, ("dusk", 1)), (109, ("dusk", 2)), (114, ("dusk", 3)), (117, ("dusk", 4))]
    for x in range(W):
        wob = (x // 3) % 2  # the band edges step, they are not ruler-straight
        for y in range(H):
            c = bands[0][1]
            for y0, cc in bands:
                if y >= y0 + (wob if y0 else 0):
                    c = cc
            im.putpixel((x, y), col(*c))
    rnd = random.Random(7)
    for _ in range(70):  # stars, more in the high sky
        x, y = rnd.randrange(W), int(rnd.random() ** 1.8 * 80)
        im.putpixel((x, y), col("bone", rnd.choice((3, 4))) if y < 60 else col("sky", 4))
    # 星環: a great arc of stars across the sky (the ring the game is named for)
    cx, cy, r = 300, 150, 150
    for k in range(60):
        a = math.radians(196 + k * 2.4)
        x, y = int(cx + r * math.cos(a)), int(cy + r * 0.55 * math.sin(a))
        if 0 <= x < W and 0 <= y < 100:
            im.putpixel((x, y), col("gem", 4 if k % 5 == 0 else 3))
            if k % 5 == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    im.putpixel((x + dx, y + dy), col("gem", 3))
    for cxl, cyl, wl in ((90, 70, 70), (210, 88, 90), (400, 60, 60)):  # long dusk clouds
        for y in range(cyl, cyl + 4):
            for x in range(cxl - wl // 2 + (y - cyl) * 3, cxl + wl // 2 - (y - cyl) * 2):
                if 0 <= x < W:
                    im.putpixel((x, y), col("dusk", 2 if y == cyl else 1) if y < cyl + 3 else col("sky", 2))
    return im


def far():
    im = new(W, H)
    for y in range(HORIZON, H):  # the sea, darker toward the viewer, banded
        f = (y - HORIZON) / (H - HORIZON)
        t = 3 if f < 0.08 else 2 if f < 0.3 else 1 if f < 0.65 else 0
        for x in range(W):
            im.putpixel((x, y), col("sea", t))
    rnd = random.Random(3)
    for _ in range(140):  # the sun's glitter on the water, short horizontal strokes
        y = rnd.randrange(HORIZON + 2, H)
        x = int(250 + rnd.gauss(0, 30 + (y - HORIZON)))
        n = rnd.randrange(2, 6)
        for k in range(n):
            if 0 <= x + k < W:
                im.putpixel((x + k, y), col("dusk", 4 if y < HORIZON + 20 else 3))
    # distant islands on the horizon (silhouettes in the haze)
    for x0, x1, top in ((20, 120, 108), (130, 170, 113)):
        for x in range(x0, x1):
            hgt = top + int(4 * math.sin((x - x0) / (x1 - x0) * math.pi * 1.0) * -1) + (x * 7 % 3 == 0)
            for y in range(hgt, HORIZON):
                im.putpixel((x, y), col("sky", 3 if y < hgt + 2 else 2))
    return im


def mid():
    """The island: a grassy headland rising to the right, the star ring glowing on its brow and the
    lighthouse behind it, cliffs of layered stone into the sea.

    Composition (inspection M-1): the subject (ring and lighthouse) sits in art x 80-400, which both the
    15 Pro (x 27-453) and SE (x 73-407) show, and right of the title buttons (art x 190-290, y 98-150) and
    below the logo (y 19-83), so nothing covers it at either size."""
    im = new(W, H)
    rnd = random.Random(5)

    def top(x):
        if x < 312:
            return 138 + (312 - x) * 2
        return int(138 - (x - 312) * 0.22 - 2 * math.sin(x / 19.0))

    x_left = 300
    cracks = {x for x in range(x_left, W) if rnd.random() < 0.02}
    # the strata wander (no brick courses): a smooth offset per column
    ledge_off = [int(9 + 2.2 * math.sin(x / 11.0) + 1.4 * math.sin(x / 4.3)) for x in range(W)]
    for x in range(x_left, W):
        t0 = top(x)
        if t0 >= H:
            continue
        for y in range(max(0, t0), H):
            d = y - t0
            if d == 0:
                c = col("leaf", 3)
            elif d < 3:
                c = col("leaf", 2)
            elif d < 5:
                c = col("leaf", 1)  # the turf's edge, overhanging
            elif d == 5:
                c = col("stone", 0)  # the shadow under the turf
            else:
                # layered stone: ledges every 9 rows (lit top, shadowed underside), cracks, a lit seaward face
                k = (d - 6 + ledge_off[x]) % 9
                t = 2
                if k == 0:
                    t = 3
                elif k == 8:
                    t = 1
                if x in cracks and k not in (0,) and d > 8:
                    t = 1
                if x - x_left < 10 + d // 3 and t == 2:
                    t = 3  # the face turned to the sunset
                if y > H - 16 and t > 1:
                    t -= 1  # wet and dark near the water
                c = col("stone", t)
            im.putpixel((x, y), c)
        im.putpixel((x, max(0, t0 - 1)), col("navy", 0))
    for x in range(x_left - 4, W):  # foam lines where the cliff meets the sea
        for k, y in enumerate((H - 7, H - 4, H - 2)):
            if (x // 5 + k) % 3 != 0 and (x >= x_left or k == 2):
                im.putpixel((x, y), col("bone", 4 if k == 0 else 3))
    # trees behind the lighthouse (decoration; may fall outside on narrow screens)
    for tx in (414, 438, 462):
        ty = top(tx)
        for y in range(ty - 22, ty - 4):
            for x in range(tx - 9, tx + 10):
                if (x - tx) ** 2 / 81 + (y - (ty - 14)) ** 2 / 64 <= 1:
                    lit = (x - tx) + (y - (ty - 14)) < -4
                    im.putpixel((x, y), col("leaf", 3 if lit else 2 if (x - tx) < 3 else 1))
        for y in range(ty - 5, ty):
            im.putpixel((tx, y), col("wood", 2))
            im.putpixel((tx + 1, y), col("wood", 1))
    # the lighthouse tower (subject, inside x 80-400)
    lx = 388
    ly = top(lx)
    for y in range(ly - 46, ly):
        hw = 4 + (y - (ly - 46)) // 14
        for x in range(lx - hw, lx + hw + 1):
            band = ((y - (ly - 46)) // 7) % 2
            im.putpixel((x, y), col("plaster" if not band else "roof", 3 if x < lx else 2))
    for y in range(ly - 54, ly - 46):
        for x in range(lx - 3, lx + 4):
            im.putpixel((x, y), col("gold", 4 if y > ly - 52 else 2))
    for x in range(lx - 4, lx + 5):
        im.putpixel((x, ly - 55), col("roof", 1))
    # the star ring on the headland's brow, glowing (the subject)
    rx = 346
    ry = top(rx) - 18
    for y in range(ry - 20, ry + 20):
        for x in range(rx - 20, rx + 20):
            d = math.hypot(x - rx + 0.5, y - ry + 0.5)
            if 12 <= d <= 17:
                lit = -((x - rx) + (y - ry)) / max(d, 1)
                im.putpixel((x, y), col("stone", 4 if lit > 0.5 else 3 if lit > -0.2 else 2))
            elif 9 <= d < 12:
                im.putpixel((x, y), col("gem", 3))
            elif d < 9:
                im.putpixel((x, y), col("gem", 4 if d < 5 else 3))
            elif 17 < d <= 18:
                im.putpixel((x, y), col("navy", 0))
    for x in range(rx - 10, rx + 11):  # its plinth
        for y in range(ry + 15, ry + 19):
            im.putpixel((x, y), col("stone", 3 if y == ry + 15 else 2))
    for dx, dy in ((-24, -10), (22, -16), (-17, -22), (26, 4)):  # sparks (none above: the logo is there)
        im.putpixel((rx + dx, ry + dy), col("gem", 4))
    return im


def near():
    """The foreground: dark grass and flowers along the bottom, leaves at the top-left corner."""
    im = new(W, H)
    rnd = random.Random(11)
    for x in range(W):
        hgt = 10 + int(6 * math.sin(x / 17.0) + 4 * math.sin(x / 5.3))
        if 140 < x < 340:
            hgt = max(3, hgt - 9)
        for y in range(H - hgt, H):
            im.putpixel((x, y), col("leaf", 1 if y > H - hgt + 2 else 2))
        if rnd.random() < 0.18:  # blades
            for k in range(rnd.randrange(3, 8)):
                y = H - hgt - k
                im.putpixel((x, y), col("leaf", 2 if k < 3 else 3))
        if rnd.random() < 0.04:  # flowers
            y = H - hgt - 2
            for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, -1), (0, 1)):
                im.putpixel((x + dx if 0 <= x + dx < W else x, y + dy), col("bone", 4) if (dx, dy) == (0, 0) else col("berry", 3))
    # an overhanging branch at the top-left: a dark bough with a few solid leaf clusters (silhouette)
    for x in range(0, 70):
        y = int(6 + x * 0.18)
        for k in range(2):
            im.putpixel((x, y + k), col("wood", 0))
    for cx, cy, rx, ry in ((14, 10, 12, 7), (34, 16, 11, 6), (56, 18, 9, 5), (6, 22, 8, 6), (26, 26, 9, 5)):
        for y in range(cy - ry, cy + ry + 1):
            for x in range(cx - rx, cx + rx + 1):
                if 0 <= x < W and 0 <= y < H and (x - cx) ** 2 / rx ** 2 + (y - cy) ** 2 / ry ** 2 <= 1:
                    im.putpixel((x, y), col("leaf", 1 if (x - cx) + (y - cy) < -3 else 0))
    outline(im, col("navy", 0))
    return im
