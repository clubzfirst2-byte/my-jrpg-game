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


def grooves(c, mask, drop=2, lift=1):
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
