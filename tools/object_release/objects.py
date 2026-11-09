"""The sample objects, props, puzzle parts, icons and effects (wave 1: style approval).

Every function returns {name: rgba_rows}. Sizes are the release size (2 art px per game px) of the
placeholder, with the same anchor (docs/art-kit/LIST.md):
  obj.house 96x112 (feet; docs/ART.md: buildings may grow upward, the door opening is 64+ tall)
  obj.chest.closed / .open 32x28, obj.jar 20x24, obj.crate 32x32, obj.checkpoint.off / .on 24x40,
  obj.campfire.0 / .1 32x28, sw.plate.off / .on 28x20, icon.sword / herb / meat 20x20 (feet),
  fx.slash 32x40 (centre; points right, the game rotates it to the aim), fx.fire.0 / .1 24x28 (feet).
Feet anchor = the bottom centre: the lowest row of every "feet" sprite is the ground line.
"""

import math

from draw import RAMPS, canvas, check_rows, clear, halo, hx, layers, legend, round_shade, stamp, to_rgba


# ------------------------------------------------------------------ helpers

def hline(c, x0, x1, y, m, t=None):
    for x in range(x0, x1 + 1):
        c.put(x, y, m, t)


def vline(c, x, y0, y1, m, t=None):
    for y in range(y0, y1 + 1):
        c.put(x, y, m, t)


def box(c, x0, y0, x1, y1, m, core=2, lit=3, dark=1, top=None, bottom=None):
    """A flat panel: lit left column, dark right column, optional top / bottom rows."""
    c.rect(x0, y0, x1, y1, m, core)
    vline(c, x0, y0, y1, m, lit)
    vline(c, x1, y0, y1, m, dark)
    if top is not None:
        hline(c, x0, x1, y0, m, top)
    if bottom is not None:
        hline(c, x0, x1, y1, m, bottom)


def shade_px(c, x, y, t):
    c.shade(x, y, t)


def blend(a, b, k):
    return tuple(round(a[i] * (1 - k) + b[i] * k) for i in range(3))


def spill(img, src_cols, tint, k=0.35, reach=2):
    """Light spill: opaque pixels near a glowing colour are tinted towards it."""
    h, w = len(img), len(img[0])
    srcs = [(x, y) for y in range(h) for x in range(w) if img[y][x] and img[y][x][:3] in src_cols]
    done = set()
    for x, y in srcs:
        for dy in range(-reach, reach + 1):
            for dx in range(-reach, reach + 1):
                X, Y = x + dx, y + dy
                if (X, Y) in done or not (0 <= X < w and 0 <= Y < h):
                    continue
                p = img[Y][X]
                if p and p[3] == 255 and p[:3] not in src_cols:
                    kk = k if abs(dx) + abs(dy) <= reach else k / 2
                    img[Y][X] = blend(p[:3], tint, kk) + (255,)
                    done.add((X, Y))
    return img


# ------------------------------------------------------------------ obj.house (96 x 112)

def house():
    W, H = 96, 112
    c = canvas(W, H)

    # --- roof: tiles in rows, ridge on top, the front slope seen from above
    top, eave = 3, 33
    for y in range(top, eave + 1):
        k = (y - top) / (eave - top)
        inset = round(13 * (1 - k))
        c.rect(1 + inset, y, 94 - inset, y, "roof", 2)
    band = 5
    for y in range(top + 4, eave + 1):
        r = (y - top - 4) % band
        row = (y - top - 4) // band
        k = (y - top) / (eave - top)
        inset = round(13 * (1 - k))
        x0, x1 = 1 + inset, 94 - inset
        for x in range(x0, x1 + 1):
            if r == 0:
                t = 1  # the shadow cast by the row above
            elif r == band - 1:
                t = 3  # the lit lip of each tile
            else:
                t = 2
            gap = (x + (4 if row % 2 else 0)) % 8
            tile = (x + (4 if row % 2 else 0)) // 8
            odd = (tile * 7 + row * 5) % 11  # a few tiles a shade darker or lighter
            if 0 < r < band - 1 and odd == 0:
                t = 1 if r == 1 else 2
            if 0 < r < band - 1 and odd == 3 and r < 3:
                t = 3
            if 0 < r < band - 1 and gap == 0:
                t = 1  # the seam between two tiles
            elif 0 < r < band - 1 and gap == 1 and r == 1:
                t = 3  # the lit top-left corner of a tile
            c.put(x, y, "roof", t)
        # the slope's ends: lit on the left, in shade on the right
        c.put(x0, y, "roof", 3 if r else 2)
        c.put(x0 + 1, y, "roof", 3 if r == band - 1 else c.tone[y][x0 + 1])
        c.put(x1, y, "roof", 1)
        c.put(x1 - 1, y, "roof", 1 if r else 0)
    # the ridge cap
    hline(c, 14, 81, top, "roof", 3)
    hline(c, 14, 81, top + 1, "roof", 4)
    hline(c, 14, 81, top + 2, "roof", 3)
    hline(c, 14, 81, top + 3, "roof", 1)
    for x in range(16, 81, 6):
        c.put(x, top + 1, "roof", 3)
        c.put(x, top + 2, "roof", 2)
    c.put(14, top + 1, "roof", 3)
    c.put(81, top + 1, "roof", 2)
    c.put(81, top + 2, "roof", 1)
    # the fascia board under the eave
    c.rect(1, eave + 1, 94, eave + 3, "timber", 2)
    hline(c, 1, 94, eave + 1, "timber", 3)
    hline(c, 1, 94, eave + 3, "timber", 1)
    for x in range(6, 94, 12):
        c.put(x, eave + 2, "timber", 1)

    # --- chimney (stone) on the right of the roof
    cx0, cx1 = 70, 79
    c.rect(cx0, 0, cx1, 17, "stone", 2)
    vline(c, cx0, 0, 17, "stone", 3)
    vline(c, cx1, 0, 17, "stone", 1)
    for y in (6, 12):
        hline(c, cx0 + 1, cx1 - 1, y, "stone", 1)
    for x, y0, y1 in ((74, 1, 5), (72, 7, 11), (77, 7, 11), (75, 13, 17)):
        vline(c, x, y0, y1, "stone", 1)
    for x, y in ((71, 2), (71, 8), (75, 8), (73, 14), (76, 2)):
        c.put(x, y, "stone", 3)
    c.rect(cx0 - 1, 0, cx1 + 1, 1, "stone", 3)
    hline(c, cx0, cx1 + 1, 1, "stone", 2)
    c.put(cx1 + 1, 0, "stone", 2)
    hline(c, cx0 + 2, cx1 - 2, 0, "ash", 0)  # the dark flue
    # the chimney's shadow on the roof, down to the right
    for y in range(18, 22):
        for x in range(cx0 + 1, cx1 + 3):
            if c.m(x, y) == "roof" and c.tone[y][x] is not None:
                c.tone[y][x] = max(0, c.tone[y][x] - 1)

    # --- the wall: plaster in a timber frame
    wt, wb = eave + 4, 103  # wall rows 37..103
    c.rect(4, wt, 91, wb, "plaster", 2)
    for y in range(wt, wt + 3):  # the eave's shadow
        hline(c, 4, 91, y, "plaster", 1)
    # corner posts and door posts
    for x0 in (4, 88):
        box(c, x0, wt, x0 + 3, wb, "timber")
    # the top beam (under the eave shadow) and the mid rail
    for x0, x1 in ((8, 33), (62, 87)):
        c.rect(x0, 64, x1, 66, "timber", 2)
        hline(c, x0, x1, 64, "timber", 3)
        hline(c, x0, x1, 66, "timber", 1)
        hline(c, x0, x1, 67, "plaster", 1)  # the rail's shadow
    # diagonal braces in the lower panels
    for (xa, ya, xb, yb) in ((9, 99, 31, 69), (86, 99, 64, 69)):
        n = max(abs(xb - xa), abs(yb - ya))
        for i in range(n + 1):
            x = round(xa + (xb - xa) * i / n)
            y = round(ya + (yb - ya) * i / n)
            c.put(x, y, "timber", 3)
            c.put(x + 1, y, "timber", 2)
            c.put(x + 2, y, "timber", 1)
    # plaster texture: a few lit flecks and hairline cracks
    for x, y in ((12, 74), (20, 82), (26, 92), (14, 90), (70, 76), (80, 88), (74, 95), (84, 78), (40, 44), (52, 46)):
        if c.m(x, y) == "plaster" and c.tone[y][x] == 2:
            c.shade(x, y, 3)
    for x, y in ((22, 75), (23, 76), (23, 77), (78, 92), (79, 93), (16, 96), (17, 96)):
        if c.m(x, y) == "plaster" and c.tone[y][x] == 2:
            c.shade(x, y, 1)

    # --- windows with shutters and flower boxes
    for wx in (11, 69):
        # frame
        box(c, wx - 1, 42, wx + 16, 61, "timber", top=3, bottom=1)
        # glass in four panes
        c.rect(wx + 1, 44, wx + 14, 59, "glass", 1)
        for y in range(44, 60):
            for x in range(wx + 1, wx + 15):
                d = (x - wx) + (y - 44)
                if 3 <= d <= 5 or d == 9:
                    c.shade(x, y, 3)  # the reflection, top left
                elif y < 46:
                    c.shade(x, y, 0)  # shade under the lintel
        c.put(wx + 2, 45, "glass", 4)
        c.put(wx + 3, 45, "glass", 4)
        c.put(wx + 2, 46, "glass", 4)
        # mullions
        vline(c, wx + 7, 44, 59, "timber", 2)
        vline(c, wx + 8, 44, 59, "timber", 1)
        hline(c, wx + 1, wx + 14, 51, "timber", 3)
        hline(c, wx + 1, wx + 14, 52, "timber", 1)
        # shutters (painted teal), slatted
        for sx in (wx - 4, wx + 17):
            c.rect(sx, 42, sx + 2, 61, "glaze", 2)
            vline(c, sx, 42, 61, "glaze", 3)
            vline(c, sx + 2, 42, 61, "glaze", 1)
            for y in range(44, 61, 3):
                hline(c, sx, sx + 2, y, "glaze", 1)
        # flower box
        box(c, wx - 1, 60, wx + 16, 63, "timber", top=3, bottom=1)
        for i, fx in enumerate(range(wx, wx + 16, 3)):
            c.put(fx, 59, "leaf", 2)
            c.put(fx + 1, 59, "leaf", 3)
            c.put(fx + 1, 58, "leaf", 2)
            col = ("meat", "string", "meat", "clay", "string", "meat")[i % 6]
            c.put(fx, 58, col, 3)
            c.put(fx + 1, 57, col, 4 if col != "meat" else 3)
            c.put(fx + 2, 58, "leaf", 1)

    # --- the door: an arched plank door, 22 wide, 64 tall opening
    dx0, dx1 = 37, 58
    dtop = wt + 1  # 38
    for y in range(dtop, wb + 1):
        for x in range(dx0 - 3, dx1 + 4):
            c.put(x, y, "timber", 2)
    # arch: cut the frame's top corners round
    for y in range(dtop, dtop + 6):
        r = dtop + 6 - y
        for x in range(dx0 - 3, dx1 + 4):
            ax = abs(x - (dx0 + dx1) / 2) - (dx1 - dx0) / 2 - 3 + r * 1.2
            if ax > 0:
                c.put(x, y, "plaster", 1 if y < wt + 3 else 2)
    # frame tones
    for y in range(dtop, wb + 1):
        for x in (dx0 - 3, dx0 - 2, dx0 - 1, dx1 + 1, dx1 + 2, dx1 + 3):
            if c.m(x, y) == "timber":
                c.tone[y][x] = 3 if x in (dx0 - 3, dx1 + 1) else 1 if x in (dx0 - 1, dx1 + 3) else 2
    # the leaf: vertical planks
    for y in range(dtop + 3, wb + 1):
        for x in range(dx0, dx1 + 1):
            ax = abs(x + 0.5 - (dx0 + dx1 + 1) / 2) - (dx1 - dx0 + 1) / 2 + max(0, (dtop + 8 - y)) * 1.1
            if ax > 0:
                continue
            p = (x - dx0) % 5
            t = 1 if p == 4 else 3 if p == 0 else 2
            c.put(x, y, "chestwood", t)
    # the arch's shadow on the leaf
    for y in range(dtop + 3, dtop + 6):
        for x in range(dx0, dx1 + 1):
            if c.m(x, y) == "chestwood":
                c.tone[y][x] = 1
    # iron straps with rivets, a ring handle
    for sy in (52, 88):
        hline(c, dx0, dx1, sy, "steel", 3)
        hline(c, dx0, dx1, sy + 1, "steel", 1)
        for x in range(dx0 + 2, dx1, 5):
            c.put(x, sy, "steel", 4)
    for x, y, t in ((52, 72, 3), (53, 71, 3), (54, 71, 3), (55, 72, 2), (55, 73, 1), (54, 74, 1), (53, 74, 1), (52, 73, 2)):
        c.put(x, y, "gold", t)
    c.put(53, 72, "chestwood", 0)
    c.put(54, 72, "chestwood", 0)
    c.put(53, 73, "chestwood", 0)
    c.put(54, 73, "chestwood", 1)
    # --- foundation stones and the door step
    fy0, fy1 = 100, 109
    door_cols = range(dx0 - 3, dx1 + 4)
    saved = {(x, y): (c.mat[y][x], c.tone[y][x]) for x in door_cols for y in range(fy0, 104)}
    c.rect(4, fy0, 91, fy1, "stone", 2)
    hline(c, 4, 91, fy0, "stone", 3)
    rows = ((fy0, fy0 + 4, 0), (fy0 + 5, fy1, 5))
    for y0, y1, off in rows:
        x = 4 - off
        widths = (11, 9, 13, 10, 12, 9, 11, 14, 10, 12)
        i = 0
        while x < 92:
            w = widths[(i + off) % len(widths)]
            xe = min(91, x + w - 1)
            if xe >= 4:
                xs = max(4, x)
                for yy in range(y0, y1 + 1):
                    for xx in range(xs, xe + 1):
                        t = 2
                        if yy == y0:
                            t = 3
                        if xx == xs:
                            t = 3
                        if xx == xe or yy == y1:
                            t = 1
                        c.put(xx, yy, "stone", t)
                c.put(xs + 1, y0 + 1, "stone", 4)
            x += w
            i += 1
    for (x, y), (m, t) in saved.items():  # the door comes down to the step, in front of the foundation
        c.put(x, y, m, t)
    # door step: a slab that sticks out
    c.rect(31, 104, 64, 110, "stone", 2)
    hline(c, 31, 64, 104, "stone", 4)
    hline(c, 31, 64, 105, "stone", 3)
    hline(c, 31, 64, 110, "stone", 1)
    vline(c, 31, 104, 110, "stone", 3)
    vline(c, 64, 104, 110, "stone", 1)
    for x in (42, 53):
        vline(c, x, 106, 110, "stone", 1)
    # the door's foot is in shade on the step
    for x in range(dx0, dx1 + 1):
        c.put(x, 103, "chestwood", 1)
    # grass tufts against the foundation
    for (gx, h) in ((6, 3), (9, 4), (12, 2), (25, 3), (83, 3), (86, 4), (89, 2), (70, 2)):
        for i in range(h):
            c.put(gx, fy1 - i, "leaf", 3 if i == h - 1 else 2)
        c.put(gx + 1, fy1, "leaf", 1)
        c.put(gx - 1, fy1, "leaf", 2)
    # moss on the lowest stones
    for x, y in ((5, 107), (6, 108), (7, 108), (90, 106), (89, 107), (16, 109), (17, 109)):
        c.put(x, y, "moss", 3)
    return {"obj.house": to_rgba(c)}


# ------------------------------------------------------------------ obj.chest (32 x 28)

def chest():
    out = {}
    for opened in (False, True):
        c = canvas(32, 28)
        W = "chestwood"
        # body: front panel rows 14..25
        box(c, 2, 14, 29, 25, W, bottom=1)
        hline(c, 3, 28, 14, W, 1)  # under the lid / rim
        hline(c, 3, 28, 19, W, 1)  # plank seam
        hline(c, 3, 28, 20, W, 3)
        for x, y in ((11, 16), (19, 22), (13, 23), (21, 17)):
            c.put(x, y, W, 1)  # wood grain
            c.put(x + 1, y, W, 1)
        if not opened:
            # the lid: a rounded top, rows 4..13
            spans = {4: (6, 25), 5: (4, 27), 6: (3, 28)}
            for y in range(4, 14):
                x0, x1 = spans.get(y, (2, 29))
                for x in range(x0, x1 + 1):
                    t = 4 if y == 4 else 3 if y <= 6 else 2
                    if y == 12:
                        t = 1
                    if y == 13:
                        t = 0
                    c.put(x, y, W, t)
                if y < 13:
                    c.put(x0, y, W, 3 if y < 12 else 2)
                    c.put(x1, y, W, 1)
            hline(c, 3, 28, 8, W, 1)  # the lid's plank seam
            hline(c, 3, 28, 9, W, 3)
            # gold bands over lid and body
            for bx in (6, 23):
                for y in range(4, 26):
                    if c.m(bx, y) is None and c.m(bx + 2, y) is None:
                        continue
                    for i, x in enumerate((bx, bx + 1, bx + 2)):
                        if c.m(x, y) is None:
                            continue
                        t = (3, 2, 1)[i]
                        if y <= 6:
                            t = (4, 3, 2)[i]
                        if y in (12, 13):
                            t = (1, 1, 0)[i]
                        c.put(x, y, "gold", t)
                for y in (16, 23):
                    c.put(bx + 1, y, "gold", 4)
            # the lock plate and keyhole
            box(c, 13, 9, 18, 17, "gold", top=3, bottom=1)
            c.put(13, 9, "gold", 4)
            c.put(14, 9, "gold", 4)
            hline(c, 13, 18, 13, "gold", 1)
            vline(c, 15, 11, 12, "chestwood", 0)
            vline(c, 16, 11, 12, "chestwood", 0)
            c.put(15, 13, "chestwood", 0)
            c.put(16, 13, "chestwood", 0)
            vline(c, 15, 14, 15, "chestwood", 0)
            c.put(16, 14, "gold", 2)
            hline(c, 13, 18, 18, W, 1)  # the plate's shadow
        else:
            # the lid thrown back: its inside, in shade, rows 1..6 (shorter: it leans away)
            for y in range(1, 7):
                x0, x1 = (4, 27) if y == 1 else (3, 28)
                for x in range(x0, x1 + 1):
                    c.put(x, y, W, 2 if y == 1 else 1)
                c.put(x0, y, W, 2)
                c.put(x1, y, W, 0)
            hline(c, 4, 27, 4, W, 0)  # plank seam inside the lid
            for bx in (6, 23):
                for y in range(1, 7):
                    for i, x in enumerate((bx, bx + 1, bx + 2)):
                        c.put(x, y, "gold", (3, 2, 1)[i] if y == 1 else (2, 1, 1)[i])
            # the box seen from above: back rim, the dark hollow, front rim
            for y in range(7, 14):
                for x in range(2, 30):
                    c.put(x, y, W, 0)
            hline(c, 2, 29, 7, W, 3)  # back rim
            for y in range(8, 14):  # side rims (lit left, shaded right)
                c.put(2, y, W, 3)
                c.put(3, y, W, 2)
                c.put(29, y, W, 1)
                c.put(28, y, W, 1)
            hline(c, 4, 27, 8, W, 1)  # the back wall inside
            hline(c, 4, 27, 9, W, 1)
            for x in range(5, 27, 4):
                c.put(x, 9, W, 0)  # its planks
            hline(c, 2, 29, 13, W, 4)  # front rim, lit
            hline(c, 3, 28, 12, W, 0)
            # a little gleam of light falling into the empty chest
            for x, y in ((9, 10), (10, 10), (11, 11), (18, 10)):
                c.put(x, y, W, 1)
            # gold bands on the front panel
            for bx in (6, 23):
                for y in range(13, 26):
                    for i, x in enumerate((bx, bx + 1, bx + 2)):
                        c.put(x, y, "gold", (4, 3, 2)[i] if y == 13 else (3, 2, 1)[i])
                for y in (16, 23):
                    c.put(bx + 1, y, "gold", 4)
            # the hasp hangs open
            box(c, 14, 14, 17, 18, "gold", top=3, bottom=1)
            c.put(15, 16, "chestwood", 0)
            c.put(16, 16, "chestwood", 0)
            hline(c, 14, 17, 19, W, 1)
        # metal feet on the corners
        for x0 in (2, 27):
            c.rect(x0, 23, x0 + 2, 25, "gold", 2)
            c.put(x0, 23, "gold", 3)
            hline(c, x0, x0 + 2, 25, "gold", 1)
        img = to_rgba(c)
        out["obj.chest." + ("open" if opened else "closed")] = img
    return out


# ------------------------------------------------------------------ obj.jar (20 x 24)

def jar():
    c = canvas(20, 24)
    c.ellipse(10, 15.5, 7.6, 7.1, "clay")
    round_shade(c, "clay", 10, 15.5, 7.6, 7.1)
    c.rect(7, 6, 12, 9, "clay", 2)
    vline(c, 7, 6, 9, "clay", 3)
    vline(c, 12, 6, 9, "clay", 1)
    hline(c, 7, 12, 9, "clay", 1)
    # the rim seen from above, with the dark mouth
    c.ellipse(10, 4.5, 5.2, 2.4, "clay", 3)
    for x in range(6, 14):
        c.put(x, 6, "clay", 2)
    c.put(5, 4, "clay", 3)
    c.put(14, 4, "clay", 2)
    c.ellipse(10, 4.3, 3.2, 1.2, "clay", 0)
    hline(c, 8, 11, 3, "clay", 4)
    c.put(14, 5, "clay", 1)
    c.put(13, 6, "clay", 1)
    # a glazed band with a wave
    for y in (11, 12, 13):
        for x in range(2, 18):
            if c.m(x, y) == "clay":
                t = c.tone[y][x]
                c.put(x, y, "glaze", max(1, min(3, t)))
    for x in range(2, 18):
        y = 12 + (1 if (x // 2) % 2 else 0) - 1
        if c.m(x, y) == "glaze":
            c.shade(x, y, min(4, c.tone[y][x] + 1))
    # the highlight
    c.put(6, 10, "clay", 4)
    c.put(5, 15, "clay", 4)
    c.put(5, 16, "clay", 3)
    # the base rests flat
    hline(c, 6, 13, 22, "clay", 1)
    return {"obj.jar": to_rgba(c)}


# ------------------------------------------------------------------ obj.crate (32 x 32)

def crate():
    c = canvas(32, 32)
    M = "crate"
    # top face rows 2..10, front face rows 11..30
    c.rect(1, 2, 30, 10, M, 3)
    for y in (4, 7):
        hline(c, 2, 29, y, M, 2)  # top boards
    hline(c, 1, 30, 2, M, 4)
    vline(c, 30, 2, 10, M, 2)
    # the top's frame
    for y in range(2, 11):
        c.put(1, y, M, 4)
        c.put(2, y, M, 4 if y < 10 else 3)
    hline(c, 1, 30, 10, M, 1)
    # front face
    c.rect(1, 11, 30, 30, M, 2)
    # boards
    for y in (17, 24):
        hline(c, 5, 26, y, M, 1)
        hline(c, 5, 26, y + 1, M, 3)
    # frame: left and right posts, top and bottom rails
    for x0 in (1, 27):
        c.rect(x0, 11, x0 + 3, 30, M, 3 if x0 == 1 else 1)
        vline(c, x0, 11, 30, M, 3)
        vline(c, x0 + 3, 11, 30, M, 1 if x0 == 1 else 0)
        vline(c, x0 + 1, 11, 30, M, 4 if x0 == 1 else 2)
    for y0 in (11, 27):
        c.rect(5, y0, 26, y0 + 3, M, 2)
        hline(c, 5, 26, y0, M, 3)
        hline(c, 5, 26, y0 + 3, M, 1)
    # the diagonal brace
    for i in range(0, 21):
        x = 5 + i
        y = round(26 - i * 11 / 20)
        c.put(x, y, M, 3)
        c.put(x, y + 1, M, 2)
        c.put(x, y + 2, M, 1)
    # nails
    for x, y in ((2, 12), (28, 12), (2, 28), (28, 28), (6, 12), (25, 12), (6, 28), (25, 28)):
        c.put(x, y, "steel", 3)
    # grain marks
    for x, y in ((10, 14), (11, 14), (20, 21), (21, 21), (14, 20), (9, 22), (18, 15), (19, 15)):
        if c.tone[y][x] == 2:
            c.put(x, y, M, 1)
    hline(c, 1, 30, 30, M, 1)
    return {"obj.crate": to_rgba(c)}


# ------------------------------------------------------------------ obj.checkpoint (24 x 40)

RING = [  # the 星環 ring with a four-point star, carved into the stone (11 x 11)
    "...xxxxx...",
    "..x.....x..",
    ".x...s...x.",
    "x....s....x",
    "x...sss...x",
    "x.sssSsss.x",
    "x...sss...x",
    "x....s....x",
    ".x...s...x.",
    "..x.....x..",
    "...xxxxx...",
]
GLYPHS = [".x.", "x.x", ".x.", "...", "x.x", ".x.", ".x."]  # two small runes under the ring


def checkpoint():
    out = {}
    for on in (False, True):
        c = canvas(24, 40)
        S = "stone"
        # plinth: two steps
        box(c, 1, 33, 22, 38, S, top=3, bottom=1)
        hline(c, 1, 22, 34, S, 4)
        box(c, 4, 29, 19, 33, S, top=3, bottom=1)
        hline(c, 4, 19, 30, S, 4)
        hline(c, 2, 21, 35, S, 3)
        # the stele, rounded on top
        for y in range(2, 30):
            x0, x1 = (8, 15) if y == 2 else (7, 16) if y == 3 else (6, 17)
            for x in range(x0, x1 + 1):
                c.put(x, y, S, 2)
            c.put(x0, y, S, 3)
            c.put(x0 + 1, y, S, 3 if y < 5 else 2)
            c.put(x1, y, S, 1)
        hline(c, 8, 15, 2, S, 4)
        hline(c, 7, 13, 3, S, 3)
        hline(c, 6, 17, 28, S, 1)
        # chips and moss
        for x, y in ((16, 9), (16, 10), (6, 22), (15, 26)):
            c.put(x, y, S, 0 if x == 16 else 1)
        for x, y in ((1, 36), (2, 37), (3, 37), (2, 36), (4, 33), (5, 33), (19, 37), (20, 37), (6, 28), (7, 27)):
            c.put(x, y, "moss", 3 if y in (33, 27, 36) else 2)
        # carvings
        cm, ct, st = ("glow", 3, 4) if on else (S, 0, 1)
        for y, row in enumerate(RING):
            for x, ch in enumerate(row):
                if ch == "x":
                    c.put(6 + x, 7 + y, cm, ct if on else (0 if y > 5 or x > 5 else 1))
                elif ch in "sS":
                    c.put(6 + x, 7 + y, cm, (4 if ch == "S" else 3) if on else (0 if ch == "S" else 1))
        for i, row in enumerate(GLYPHS):
            for x, ch in enumerate(row):
                if ch == "x":
                    c.put(10 + x, 19 + i, cm, 2 if on else 1)
        img = to_rgba(c)
        if on:
            g = c.ramps["glow"]
            img = spill(img, {g[2], g[3], g[4]}, g[3], k=0.3, reach=1)
            # a spark above the stone
            for (x, y, t) in ((12, 0, 4), (11, 0, 2), (13, 0, 2), (12, 1, 3)):
                if img[y][x] is None or img[y][x][3] < 255:
                    img[y][x] = g[t] + (255 if t == 4 else 200,)
        out["obj.checkpoint." + ("on" if on else "off")] = img
    return out


# ------------------------------------------------------------------ flames (shared by the campfire and fx.fire)

def tongue(c, bx, by, w, tx, ty, mat="fire"):
    """A flame tongue: a round base of radius w at (bx, by - w), tapering and curving to the tip (tx, ty)."""
    c.ellipse(bx, by - w, w, w, mat)
    top = by - w
    for y in range(int(ty), int(top) + 1):
        t = (top - y) / max(1, top - ty)
        cx = bx + (tx - bx) * t ** 1.5
        hw = w * (1 - t) ** 0.8
        for x in range(int(cx - hw - 1), int(cx + hw + 2)):
            if abs(x + 0.5 - cx) <= hw:
                c.put(x, y, mat)


def flame_tones(c, top, bottom, mat="fire"):
    """Red at the edge, orange, yellow, a small white heart low down."""
    def bias(x, y):
        return 1.2 * (y - top) / max(1, bottom - top) - 0.4

    layers(c, mat, [1, 2, 2, 3, 3, 4], bias)


FIRE_FX = [  # (base x, base y, radius, tip x, tip y) per tongue, per frame
    [(12, 28, 6.0, 10, 2), (6, 28, 3.4, 3, 11), (18, 28, 3.6, 21, 8), (15, 27, 2.8, 17, 15)],
    [(12, 28, 6.0, 15, 4), (6, 28, 3.6, 4, 7), (18, 28, 3.2, 20, 12), (9, 27, 2.8, 7, 15)],
]


def fire_fx():
    out = {}
    for i, tongues in enumerate(FIRE_FX):
        c = canvas(24, 28)
        for t in tongues:
            tongue(c, *t)
        # keep the outline inside the frame: clear the outer columns and the top row
        for y in range(28):
            for x in (0, 23):
                clear(c, x, y)
        for x in range(24):
            clear(c, x, 0)
        flame_tones(c, 2, 27)
        img = to_rgba(c)
        g = c.ramps["fire"]
        for (x, y, t) in (((3, 5, 3), (20, 2, 4)), ((19, 6, 3), (4, 2, 4)))[i]:
            img[y][x] = g[t] + (255,)
        out[f"fx.fire.{i}"] = img
    return out


# ------------------------------------------------------------------ obj.campfire (32 x 28)

CAMP = [
    [(16, 21, 5.0, 15, 2), (11, 21, 3.0, 8, 9), (21, 21, 3.0, 24, 7), (18, 20, 2.4, 20, 12)],
    [(16, 21, 5.0, 18, 3), (11, 21, 3.0, 9, 7), (21, 21, 2.8, 23, 10), (13, 20, 2.4, 11, 12)],
]
STONES_BACK = [(5, 20), (10, 18.5), (16, 18), (22, 18.5), (27, 20)]
STONES_FRONT = [(4, 23.5), (9.5, 25.5), (16, 26), (22.5, 25.5), (28, 23.5)]


def stone_lump(c, sx, sy, rx=2.8, ry=2.0):
    c.ellipse(sx, sy, rx, ry, "stone")
    for y in range(int(sy - ry) - 1, int(sy + ry) + 2):
        for x in range(int(sx - rx) - 1, int(sx + rx) + 2):
            if c.m(x, y) == "stone":
                dx, dy = (x + 0.5 - sx) / rx, (y + 0.5 - sy) / ry
                c.tone[y][x] = 3 if dx + dy < -0.5 else 1 if dx + dy > 0.6 else 2
    c.put(int(sx) - 1, int(sy) - 1, "stone", 4)


def campfire():
    out = {}
    for i, tongues in enumerate(CAMP):
        c = canvas(32, 28)
        # the ash bed
        c.ellipse(16, 21.5, 10, 3.6, "ash")
        round_shade(c, "ash", 16, 21, 10, 3.6)
        for sx, sy in STONES_BACK:
            stone_lump(c, sx, sy, 2.6, 1.9)
        # flames
        for t in tongues:
            tongue(c, *t)
        flame_tones(c, 2, 21)
        # two logs crossing in front of the flame's base, 3 px thick, bark lit on top
        for (x0, y0, x1, y1) in ((6, 24, 22, 17), (26, 24, 10, 17)):
            n = max(abs(x1 - x0), abs(y1 - y0))
            for k in range(n + 1):
                x = round(x0 + (x1 - x0) * k / n)
                y = round(y0 + (y1 - y0) * k / n)
                burnt = k > n * 0.55  # the end in the fire is charred
                c.put(x, y - 1, "ash" if burnt else "wood", 3)
                c.put(x, y, "ash" if burnt else "wood", 2)
                c.put(x, y + 1, "ash" if burnt else "wood", 1)
            # the cut end towards the viewer shows rings
            c.put(x0, y0 - 1, "string", 3)
            c.put(x0, y0, "string", 2)
            c.put(x0, y0 + 1, "wood", 1)
        # glowing embers on the charred ends
        for x, y in ((14, 20), (18, 20), (16, 21), (13, 19), (19, 19)):
            if c.m(x, y) == "ash":
                c.put(x, y, "ember", 4 if (x + i) % 2 else 3)
        for sx, sy in STONES_FRONT:
            stone_lump(c, sx, sy)
        img = to_rgba(c)
        g = c.ramps["fire"]
        st = set(c.ramps["stone"][1:])
        # firelight on the stones only
        h, w = len(img), len(img[0])
        for y in range(h):
            for x in range(w):
                p = img[y][x]
                if p and p[:3] in st and y < 24:
                    img[y][x] = blend(p[:3], g[3], 0.12) + (255,)
        for (x, y, t) in (((6, 4, 3), (26, 1, 4)), ((25, 5, 3), (7, 1, 4)))[i]:
            img[y][x] = g[t] + (255,)
        out[f"obj.campfire.{i}"] = img
    return out


# ------------------------------------------------------------------ sw.plate (28 x 20)

def plate():
    out = {}
    for down in (False, True):
        c = canvas(28, 20)
        S = "stone"
        # the frame set in the ground
        box(c, 1, 7, 26, 18, S, top=3, bottom=1)
        hline(c, 2, 25, 8, S, 3)
        # the recess around the plate
        c.rect(3, 9, 24, 16, "ash", 0)
        hline(c, 3, 24, 16, S, 1)
        if not down:
            # raised slab: top face rows 3..11, side rows 12..14
            box(c, 4, 3, 23, 11, "steel", top=4, bottom=2)
            hline(c, 5, 22, 4, "steel", 3)
            box(c, 4, 12, 23, 14, "steel", core=1, lit=2, dark=0)
            hline(c, 4, 23, 12, "steel", 1)
            # a dull engraved ring
            for x, y in ((11, 6), (12, 5), (13, 5), (14, 5), (15, 5), (16, 6), (16, 7), (16, 8), (15, 9), (14, 9), (13, 9), (12, 9), (11, 8), (11, 7)):
                c.put(x, y, "steel", 1)
            c.put(13, 7, "steel", 1)
            c.put(14, 7, "steel", 1)
        else:
            # pressed: flush with the frame, the ring lights up
            box(c, 4, 9, 23, 15, "steel", core=1, lit=2, dark=0, top=2, bottom=0)
            for x, y in ((11, 11), (12, 10), (13, 10), (14, 10), (15, 10), (16, 11), (16, 12), (16, 13), (15, 14), (14, 14), (13, 14), (12, 14), (11, 13), (11, 12)):
                c.put(x, y, "glow", 3)
            c.put(13, 12, "glow", 4)
            c.put(14, 12, "glow", 4)
            c.put(12, 10, "glow", 4)
            for x in range(5, 23, 3):
                c.put(x, 15, "glow", 2)
        img = to_rgba(c)
        if down:
            g = c.ramps["glow"]
            img = spill(img, {g[3], g[4]}, g[3], k=0.3, reach=1)
            img = halo(img, g[3], alpha=90, reach=1, only={g[2]})
        out["sw.plate." + ("on" if down else "off")] = img
    return out


# ------------------------------------------------------------------ icons (20 x 20, feet)
# Drawn on the Canvas pixel by pixel (blade, guard, grip ...) and outlined by the selective outline.

def icon_sword():
    c = canvas(20, 20)
    # the blade: three pixels a row on the diagonal: lit edge, core, shaded edge
    for i in range(10):
        x, y = 8 + i, 11 - i
        c.put(x - 1, y, "steel", 4 if 1 <= i <= 7 else 3)
        c.put(x, y, "steel", 3 if i > 7 else 2)
        c.put(x + 1, y, "steel", 1)
    c.put(17, 1, "steel", 4)
    for i in range(1, 7):  # the fuller: a darker groove down the core
        c.shade(8 + i, 11 - i, 2 if i % 3 else 3)
    # the guard: a gold bar across the blade, lit on its upper side
    for k in range(-3, 4):
        x, y = 8 + k, 12 + k
        c.put(x, y, "gold", 4 if k == -3 else 3)
        c.put(x, y + 1, "gold", 1 if k > -3 else 2)
    c.put(8, 12, "gem", 4)
    c.put(8, 13, "gem", 2)
    # the grip, wrapped in leather
    for k in range(1, 5):
        x, y = 8 - k, 13 + k
        c.put(x, y, "leather", 3 if k % 2 else 2)
        c.put(x + 1, y, "leather", 1)
    # the pommel
    c.put(2, 18, "gold", 3)
    c.put(3, 18, "gold", 2)
    c.put(2, 17, "gold", 4)
    c.put(3, 17, "gold", 3)
    return to_rgba(c)


def leaf(c, cx, cy, rx, ry, rib_to, mat):
    """One round leaf as its own material (same ramp), so the leaves in front can shade the ones behind."""
    c.ramps[mat] = c.ramps["leaf"]
    c.ellipse(cx, cy, rx, ry, mat)
    round_shade(c, mat, cx, cy, rx, ry, cuts=(0.9, 0.62, 0.05))
    x0, y0 = int(cx), int(cy)
    x1, y1 = rib_to
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):  # the midrib, from the leaf's middle towards the stem
        x, y = round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n)
        if c.m(x, y) == mat:
            c.shade(x, y, 1)


def overlap_shadow(c, order):
    """Where a later part touches an earlier one, the earlier one's pixel goes to tone 0 (a shadow line)."""
    rank = {m: i for i, m in enumerate(order)}
    marks = []
    for y in range(c.h):
        for x in range(c.w):
            m = c.m(x, y)
            if m not in rank:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = c.m(x + dx, y + dy)
                if n in rank and rank[n] > rank[m]:
                    marks.append((x, y))
                    break
    for x, y in marks:
        c.tone[y][x] = 0


def icon_herb():
    c = canvas(20, 20)
    # the stem, gently curved
    for x, y in ((10, 17), (10, 16), (10, 15), (10, 14), (9, 13), (9, 12), (9, 11), (9, 10), (9, 9), (9, 8), (9, 7), (9, 6), (10, 5)):
        c.put(x, y, "stem", 2)
        c.put(x + 1, y, "stem", 1)
    c.ramps["stem"] = c.ramps["leaf"]
    # round leaves, alternating up the stem (back to front)
    leaves = [
        ("lf0", 10.0, 2.6, 1.9, 2.1, (10, 4)),
        ("lf1", 13.9, 5.0, 2.9, 2.0, (11, 5)),
        ("lf2", 5.8, 6.0, 3.1, 2.1, (9, 6)),
        ("lf3", 14.4, 9.8, 3.4, 2.2, (10, 10)),
        ("lf4", 5.4, 11.4, 3.5, 2.3, (9, 11)),
    ]
    for m, cx, cy, rx, ry, rib in leaves:
        leaf(c, cx, cy, rx, ry, rib, m)
    overlap_shadow(c, ["stem"] + [l[0] for l in leaves])
    # a white flower bud on top
    c.put(10, 0, "plaster", 4)
    c.put(11, 1, "plaster", 3)
    c.put(9, 1, "plaster", 3)
    # the tie
    hline(c, 9, 12, 14, "string", 3)
    hline(c, 9, 12, 15, "string", 1)
    c.put(13, 15, "string", 2)
    c.put(14, 16, "string", 2)
    # the cut ends of the stems
    for x in (9, 10, 11):
        c.put(x, 16, "stem", 2)
        c.put(x, 17, "stem", 3 if x == 9 else 1)
        c.put(x, 18, "fat", 2 if x != 11 else 1)
    return to_rgba(c)


def icon_meat():
    c = canvas(20, 20)
    # the meat: an oval slab on the diagonal, the bone sticking out at the lower right
    cx, cy, a, b = 8.2, 8.2, 7.6, 5.4
    for y in range(20):
        for x in range(20):
            px, py = x + 0.5 - cx, y + 0.5 - cy
            u, v = (px + py) / 1.4142, (py - px) / 1.4142
            if (u / a) ** 2 + (v / b) ** 2 <= 1:
                c.put(x, y, "meat")
    round_shade(c, "meat", cx, cy, 6.5, 6.5, cuts=(0.96, 0.7, 0.12))
    # a rim of white fat along the upper-right side
    for y in range(20):
        for x in range(20):
            if c.m(x, y) != "meat":
                continue
            px, py = x + 0.5 - cx, y + 0.5 - cy
            u, v = (px + py) / 1.4142, (py - px) / 1.4142
            e = (u / a) ** 2 + (v / b) ** 2
            if v < -1.5 and e > 0.55:
                c.put(x, y, "fat", 3 if u < 0 else 2)
    # marbling: short streaks of fat
    for x, y in ((5, 9), (6, 10), (9, 12), (10, 12), (8, 7)):
        c.put(x, y, "fat", 2)
    c.put(4, 5, "meat", 4)
    c.put(3, 6, "meat", 4)
    c.put(4, 6, "meat", 3)
    # the bone: a shaft and a double knob
    for k in range(4):
        x, y = 13 + k, 13 + k
        c.put(x, y, "bone", 3)
        c.put(x + 1, y, "bone", 2)
        c.put(x, y + 1, "bone", 1)
    c.ellipse(17.6, 15.6, 1.5, 1.5, "bone", 2)
    c.ellipse(15.6, 17.6, 1.5, 1.5, "bone", 2)
    c.put(17, 15, "bone", 4)
    c.put(15, 17, "bone", 3)
    c.put(18, 16, "bone", 1)
    c.put(16, 18, "bone", 1)
    c.put(17, 17, "bone", 1)
    return to_rgba(c)


def icons():
    return {"icon.sword": icon_sword(), "icon.herb": icon_herb(), "icon.meat": icon_meat()}


# ------------------------------------------------------------------ fx.slash (32 x 40, centre, points right)

def slash():
    """A crescent sweep, bulging right (the game turns it to the aim). White leading edge, pale blue body,
    fading to clear at the inner edge and towards both tips."""
    W, H = 32, 40
    cx, cy, R = 8.0, 20.0, 21.5
    g = [hx(v) for v in RAMPS["slash"]]
    img = [[None] * W for _ in range(H)]
    amax = math.radians(62)
    for y in range(H):
        for x in range(W):
            px, py = x + 0.5 - cx, y + 0.5 - cy
            r = math.hypot(px, py)
            a = math.atan2(py, px)
            if abs(a) > amax:
                continue
            k = abs(a) / amax  # 0 at the middle, 1 at the tips
            th = 9.0 * (1 - k ** 1.6) + 0.8
            u = (R - r) / th  # 0 on the outer (leading) edge, 1 on the inner
            fade = 1 - 0.55 * k ** 2
            if -1.2 / th <= u < 0:
                img[y][x] = g[1] + (int(230 * fade),)  # a thin blue rim keeps it readable on light ground
            elif 0 <= u <= 1:
                t = 4 if u < 0.24 else 3 if u < 0.48 else 2 if u < 0.72 else 1
                a8 = 255 if u < 0.72 else int(210 - 150 * (u - 0.72) / 0.28)
                img[y][x] = g[t] + (int(a8 * fade),)
    return {"fx.slash": img}


def all_samples():
    out = {}
    for f in (house, chest, jar, crate, checkpoint, campfire, plate, icons, slash, fire_fx):
        out.update(f())
    return out


SIZES = {
    "obj.house": (96, 112), "obj.chest.closed": (32, 28), "obj.chest.open": (32, 28), "obj.jar": (20, 24),
    "obj.crate": (32, 32), "obj.checkpoint.off": (24, 40), "obj.checkpoint.on": (24, 40),
    "obj.campfire.0": (32, 28), "obj.campfire.1": (32, 28), "sw.plate.off": (28, 20), "sw.plate.on": (28, 20),
    "icon.sword": (20, 20), "icon.herb": (20, 20), "icon.meat": (20, 20), "fx.slash": (32, 40),
    "fx.fire.0": (24, 28), "fx.fire.1": (24, 28),
}
ANCHOR = {k: ("centre" if k == "fx.slash" else "feet") for k in SIZES}

__all__ = ["all_samples", "SIZES", "ANCHOR", "check_rows"]
