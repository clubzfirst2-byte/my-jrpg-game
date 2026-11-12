"""Drawing kit for the hand-built v3 characters (round 2, after the pilot inspection).

The v1 frames are no longer upscaled. Every part is drawn on the 64 x 112 grid from a shape chosen for
it (hair locks, cloak panels and folds, sleeves, gloves with fingers, legs, boots), shaded as a volume
lit from the top left with even bands (no scattered single texels), then features are placed from hand
maps (eyes, brows, mouth). Proportions and colours follow the approved v1 frames.
"""

import math

import numpy as np

from v3lib import erode


def lock(c, root, tip, w, bend=0.0, tipw=0.0):
    """A tapered hair lock / cloth strip: a quad-ish polygon from a root (width w) to a tip, bent
    sideways by `bend` texels at the middle."""
    (x0, y0), (x1, y1) = root, tip
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    left, right = [], []
    steps = 8
    for i in range(steps + 1):
        t = i / steps
        cx = x0 + dx * t + nx * bend * math.sin(math.pi * t)
        cy = y0 + dy * t + ny * bend * math.sin(math.pi * t)
        hw = (w / 2) * (1 - t) + (tipw / 2) * t
        left.append((cx + nx * hw, cy + ny * hw))
        right.append((cx - nx * hw, cy - ny * hw))
    return c.m_poly(left + right[::-1])


def grooves(c, mask, drop=2, lift=1, sides=False):
    """Edges of a part inside a mass of the same material: the right/bottom edge sinks (a groove
    between locks or folds), the left/top edge lifts (the lit rim)."""
    inner = erode(mask)
    edge = mask & ~inner
    ys, xs = np.nonzero(edge)
    for y, x in zip(ys, xs):
        t = int(c.tone[y, x])
        right = x + 1 >= c.w or not mask[y, x + 1]
        down = y + 1 >= c.h or not mask[y + 1, x]
        left = x == 0 or not mask[y, x - 1]
        up = y == 0 or not mask[y - 1, x]
        if sides:  # only the side edges (locks flowing down: no horizontal grooves across the crown)
            down = up = False
        if right or down:
            c.tone[y, x] = max(1, t - drop)
        elif (left or up) and lift:
            c.tone[y, x] = min(5, t + lift)


def edge_band(c, mat, tone=1, sides="all"):
    """The texel inside the silhouette of `mat` (next to empty) takes `tone`: the dark band that
    separates the cloak from the grass (inspection item 12)."""
    k = c.mid(mat)
    m = c.mat == k
    out = []
    for y, x in zip(*np.nonzero(m)):
        for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            if sides != "all" and (dx, dy) not in sides:
                continue
            X, Y = x + dx, y + dy
            if not (0 <= X < c.w and 0 <= Y < c.h) or c.mat[Y, X] == 0:
                out.append((x, y))
                break
    for x, y in out:
        c.tone[y, x] = min(int(c.tone[y, x]), tone)


def capsule(c, a, b, r):
    return c.m_line([a, b], 2 * r)


def hand(c, mat, wrist, side, open_=0, tones=(1, 2, 3, 4, 5), far=False):
    """A gloved hand hanging down from the wrist: back of the hand, the thumb on the inner side
    (toward the body), two finger grooves at the bottom, a knuckle light. side: -1 left of the body
    (thumb on its right), +1 right of the body (thumb on its left)."""
    wx, wy = wrist
    m = c.m_ellipse(wx, wy + 4.2, 4.2, 4.8)
    thumb = capsule(c, (wx - side * 2.5, wy + 2), (wx - side * 3.6, wy + 6.5), 1.6)
    c.fill(m | thumb, mat)
    c.shade_part(m | thumb, tones=tones, norm=True)
    c.set_tone(thumb & ~m, tones[1])
    # the thumb's crease against the palm
    for y in range(int(wy + 3), int(wy + 7)):
        x = int(round(wx - side * 2.0))
        if m[y, x]:
            c.tone[y, x] = tones[0]
    # finger grooves (2 lines) on the lower third, and the finger tips' shade
    for gx in (-1, 1):
        x = int(round(wx + gx * 1.2 + side * 0.3))
        for y in range(int(wy + 6), int(wy + 9)):
            if 0 <= y < c.h and m[y, x]:
                c.tone[y, x] = tones[0]
    c.put(int(wx - 2), int(wy + 2), mat, tones[-1])
    c.put(int(wx - 1), int(wy + 2), mat, tones[-2])
    if far:
        c.set_tone(m | thumb, tones[1])


# a hanging gloved hand, seen from the front (8 x 10): o edge, s shade, b base, l light, g finger
# groove, t thumb (lit), k knuckle light. Drawn for the hand on the image's left (thumb on its right,
# toward the body); mirrored for the other hand (the tones stay lit from the left).
HAND_MAP = [
    ".sbbbbs.",
    "sbkkbbbs",
    "sbbbbbbt",
    "sbbbbbtt",
    "sbbbbbtt",
    "sbgbgbts",
    "sbgbgbs.",
    "sbgbgbs.",
    ".sgsgs..",
    "..ss....",
]


def hand_stamp(c, mat, wrist, side, tones=(1, 2, 3, 4, 5)):
    """The gloved hand from HAND_MAP, its top centre at the wrist. side -1: image left (thumb right)."""
    tm = {"o": tones[0], "s": tones[1], "b": tones[2], "l": tones[3], "g": tones[0], "t": tones[3],
          "k": tones[4]}
    wx, wy = wrist
    x0 = int(round(wx - 4))
    y0 = int(round(wy))
    for j, row in enumerate(HAND_MAP):
        r = row if side < 0 else row[::-1]
        for i, ch in enumerate(r):
            if ch == ".":
                continue
            t = tm[ch]
            if side > 0 and ch == "t":
                t = tones[2]  # the thumb on the far side of the light
            c.put(x0 + i, y0 + j, mat, t)


def gauntlet(c, g, a, b, mid=0.25):
    """v1's dark iron gauntlet on the forearm mask g, from the elbow a to the wrist b (hero round 2):
    mostly the dark grey (tone 0), a mid-grey strip on the lit side (tone 1), the light grey only as
    one line on the lit edge (tone 3) along the upper part; the 2 metal bands are dark grooves with
    a single lit texel at their lit end (not light stripes). v1: dark ~72 %, mid ~21 %, light ~8 %."""
    (ax, ay), (bx, by) = a, b
    L = math.hypot(bx - ax, by - ay) or 1.0
    ux, uy = (bx - ax) / L, (by - ay) / L
    nx, ny = -uy, ux
    if nx * -0.8 + ny * -0.6 < 0:  # n points to the light (top left)
        nx, ny = -nx, -ny
    ys, xs = np.nonzero(g)
    if not len(ys):
        return
    px, py = xs + 0.5 - ax, ys + 0.5 - ay
    t = (px * ux + py * uy) / L
    d = px * nx + py * ny
    r = max(1.0, float(d.max()))
    tone = np.zeros(len(ys), np.int8)
    tone[(d > mid * r) & (d <= 0.75 * r)] = 1
    lit = (d > 0.75 * r) & (t < 0.7)
    tone[lit] = 3
    tone[(d > 0.75 * r) & ~lit] = 1
    for tb in (0.3, 0.72):  # the bands: a dark groove across, one lit texel at its lit end
        band = np.abs(t - tb) < 0.6 / L * 2
        tone[band] = 0
    c.tone[ys, xs] = tone
    for tb in (0.3, 0.72):
        cx, cy = ax + (bx - ax) * (tb - 1.4 / L), ay + (by - ay) * (tb - 1.4 / L)
        x, y = int(cx + nx * r * 0.8), int(cy + ny * r * 0.8)
        if 0 <= x < c.w and 0 <= y < c.h and g[y, x]:
            c.tone[y, x] = 3
