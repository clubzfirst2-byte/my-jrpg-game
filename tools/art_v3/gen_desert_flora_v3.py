"""v3 desert trees and props, one season (STYLE.md 7; the plains' and the forest's passed ways:
gen_flora_v3.py, gen_forest_flora_v3.py). Every picture is drawn here part by part (no v1 / v2 picture
is scaled); the v1 cactus is only the reference for the design of `cactus` (column, left arm lower,
right arm higher, a pink flower on top, tan spines).

Files (src/art-release-v3/terrain/), anchor the bottom centre, no ground or ground shadow baked in:
  desert.tree.v3.<kind>.<f>.png
      palm_l  128 x 224  a date palm (oasis): a curved ringed trunk, 13 arching feathered fronds,
                         2 hanging date clusters; sway f 0-2 (the frond tips move, the trunk stays)
      palm_s   80 x 144  a young date palm (shorter trunk, 9 fronds, no dates); sway f 0-2
      snag     96 x 128  a dead acacia: a twisted grey trunk forking into bare branches; f 0
  desert.prop.v3.<kind>.<f>.png
      cactus 48 x 80 (the v1 obj.cactus design at density 4; also written as obj.cactus.png, the key
      the game draws today), cactus_l 64 x 128 (a tall saguaro, 3 arms), barrel 40 x 40, pear 64 x 56
      (prickly pear pads, red fruit), agave 56 x 44, rock_l 64 x 48 and rock_s 40 x 28 (layered red
      sandstone), bones 56 x 32 (a horned skull and a rib), tumbleweed 40 x 36, drygrass 40 x 32
      (f 0-1, sway), sage 56 x 40 (a grey-green desert shrub), pebbles 40 x 20
Run: python3 tools/art_v3/gen_desert_v3.py trees|props|all
"""

import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402

from gen_nature_v3 import hsh, leaf_marks, scalloped  # noqa: E402
from hdkit import lock  # noqa: E402
from v3lib import ROOT, Canvas, clean_isolated, despeckle, erode, lift_ramp, save  # noqa: E402

OUT = os.path.join(ROOT, "src", "art-release-v3", "terrain")
SWAY = (0, 1, -1)
RAMPS = {
    "frond": ["#14260e", "#28421a", "#345422", "#42662a", "#547a32", "#6a903e", "#8aac56"],
    "palmbark": ["#2a1c12", "#4e3624", "#604430", "#74543a", "#886646", "#9c7a56", "#b89a74"],
    "date": ["#3a160a", "#7a2e12", "#963c16", "#b0501c", "#c86a26", "#dc8a36", "#f0b060"],
    "deadwood": ["#2a2420", "#504640", "#625650", "#766a60", "#8a7e72", "#a09486", "#c0b6a6"],
    "cactus": ["#0e2418", "#1e4028", "#285030", "#326038", "#407446", "#548a54", "#76a670"],
    "spine": ["#5a4630", "#9a8060", "#b09474", "#c8ac88", "#dcc49e", "#ecd8b4", "#fff0d0"],
    "pink": ["#5a2038", "#b0507a", "#c8689e", "#e080a8", "#ea98af", "#f4b0cc", "#ffe0ee"],
    "yellow": ["#6a4a10", "#c08a20", "#d8bb30", "#f0c040", "#f4d360", "#f8dc80", "#fff4c0"],
    "fruit": ["#4a0c14", "#7e1424", "#98182c", "#b42036", "#cc3446", "#e05462", "#f4908e"],
    "agave": ["#10221e", "#22423a", "#2c5246", "#386452", "#487660", "#5e8c72", "#82aa90"],
    "rstone": ["#2e1814", "#5a2e26", "#6c3a30", "#80483a", "#965a46", "#ac7058", "#c8907a"],
    "bone": ["#4a4038", "#8a8070", "#a89c88", "#c4b8a0", "#d8ceb6", "#e8e0cc", "#fffaf0"],
    "dry": ["#3a2a14", "#6a5028", "#80622e", "#967638", "#ac8c48", "#c0a45a", "#dcc47c"],
    "sage": ["#1e2a24", "#3c4a40", "#4a5a4c", "#5a6c5a", "#6e806a", "#84967c", "#a6b69a"],
}


def canvas(w, h):
    return Canvas(w, h, {k: lift_ramp(v) for k, v in RAMPS.items()})


def finish(c, loose=()):
    despeckle(c, loose=loose)
    c.outline()
    c.shadow_band()
    return c


def cyl_tone(c, mask, ridge=0, light=0.42, tones=(1, 2, 3, 4, 5)):
    """A vertical cylinder lit from the left: tone by the position across each row."""
    for y in range(c.h):
        xs = np.nonzero(mask[y])[0]
        if len(xs) == 0:
            continue
        x0, x1 = xs.min(), xs.max()
        for x in xs:
            u = (x - x0 + 0.5) / max(1, x1 - x0 + 1)  # 0 left .. 1 right
            v = 1 - abs(u - light) / max(light, 1 - light)
            c.tone[y, x] = tones[min(len(tones) - 1, int(v * len(tones)))]


# ------------------------------------------------------------------ palms

def frond(c, x0, y0, ang, L, droop, w0, side_bias=0.0):
    """One feathered palm frond: a solid tapered midrib arc from (x0, y0) at angle `ang` (radians,
    0 = right, -pi/2 = up), bending down by `droop`, with leaflets every 3 texels on both sides that
    hang down and out (length w0 at the base to 2 at the tip, 1.6 texels wide). Returns the mask, the
    midrib mask and the centre line."""
    pts = []
    n = max(8, int(L / 2))
    dx, dy = math.cos(ang), math.sin(ang)
    for i in range(n + 1):
        t = i / n
        pts.append((x0 + dx * L * t, y0 + dy * L * t + droop * L * t * t))
    left, right = [], []
    for i, (x, y) in enumerate(pts):
        t = i / n
        hw = 1.6 * (1 - t) + 0.6 * t
        a_, b_ = pts[min(n, i + 1)], pts[max(0, i - 1)]
        tx, ty = a_[0] - b_[0], a_[1] - b_[1]
        ln = math.hypot(tx, ty) or 1
        left.append((x - ty / ln * hw, y + tx / ln * hw))
        right.append((x + ty / ln * hw, y - tx / ln * hw))
    rib = c.m_poly(left + right[::-1])
    m = rib.copy()
    step = 0.0
    for i in range(2, n + 1):
        x, y = pts[i]
        t = i / n
        step += math.hypot(x - pts[i - 1][0], y - pts[i - 1][1])
        if step < 3.0:
            continue
        step = 0.0
        a_, b_ = pts[min(n, i + 1)], pts[i - 1]
        tx, ty = a_[0] - b_[0], a_[1] - b_[1]
        ln = math.hypot(tx, ty) or 1
        tx, ty = tx / ln, ty / ln
        ll = w0 * (1 - t) + 2.0 * t
        for sgn in (1, -1):
            nx, ny = -ty * sgn, tx * sgn
            ex, ey = nx * 0.55 + tx * 0.45, ny * 0.55 + ty * 0.45 + 0.75  # out, toward the tip, and down
            el = math.hypot(ex, ey)
            m |= c.m_line([(x, y), (x + ex / el * ll, y + ey / el * ll)], 1.6)
    del side_bias
    return m, rib, pts


PALMS = {  # W, H, trunk height (fraction), base half width, top half width, lean, fronds, frond length, dates
    "palm_l": (144, 256, 0.62, 9.0, 5.5, 12, 13, 62, True),
    "palm_s": (80, 144, 0.46, 6.0, 4.5, 5, 9, 34, False),
}


def palm(kind, frame):
    W, H, th, bw, tw, lean, nf, FL, dates = PALMS[kind]
    c = canvas(W, H)
    rng = random.Random({"palm_l": 51, "palm_s": 52}[kind])
    G = H - 2
    cx = W / 2 - lean * 0.3
    top_y = G - H * th

    def at(t):  # the trunk's centre line: a gentle curve leaning right
        return (cx + lean * t * t, G - (G - top_y) * t)
    left, right = [], []
    for i in range(21):
        t = i / 20
        x, y = at(t)
        hw = bw * (1 - t) + tw * t + (1.5 if t < 0.06 else 0)
        left.append((x - hw, y))
        right.append((x + hw, y))
    trunk = c.m_poly(left + right[::-1])
    c.fill(trunk, "palmbark")
    cyl_tone(c, trunk, tones=(1, 2, 3, 4, 4))
    # leaf-base rings: uneven spacing 4-6, a dark scar row under a lit row, the scar dipping a little
    y = G - 3
    while y > top_y + 2:
        x, _ = at((G - y) / (G - top_y))
        for X in range(int(x - bw - 2), int(x + bw + 3)):
            dip = int(round(abs(X - x) * 0.18))
            for dy, d in ((0, -2), (-1, 1)):
                Y = int(y) - dip + dy
                if 0 <= Y < H and 0 <= X < W and trunk[Y, X]:
                    c.tone[Y, X] = max(1, min(5, int(c.tone[Y, X]) + d))
        y -= rng.choice((4, 5, 5, 6))
    sway = SWAY[frame]
    hx, hy = at(1.0)
    # fronds: back ones (darker) first, then the front ones; angles spread from left-down to right-down
    angs = []
    for i in range(nf):
        a = math.pi + 0.35 - (math.pi + 0.7) * (i + 0.5) / nf + rng.uniform(-0.08, 0.08)
        angs.append(-a if i % 2 == 0 else -a)
    order = sorted(range(nf), key=lambda i: (i % 3 != 0, rng.random()))
    for rank, i in enumerate(order):
        a = -(math.pi * 0.06 + (math.pi * 0.88) * (i + 0.5) / nf)  # -11 .. -169 deg: up and to the sides
        a += rng.uniform(-0.07, 0.07)
        side = math.cos(a)
        L = FL * (0.8 + 0.3 * abs(side)) * (1.0 if i % 2 else 0.86) * rng.uniform(0.94, 1.06)
        droop = (0.18 + 0.5 * abs(side) ** 1.5) * rng.uniform(0.85, 1.15)
        back = rank < nf // 3
        m, rib0, pts = frond(c, hx, hy + 2, a, L, droop, w0=(9 if kind == "palm_l" else 6.5))
        if sway:  # the tips move with the wind (the outer third), the base stays
            shift = np.zeros_like(m)
            n = len(pts)
            ys, xs = np.nonzero(m)
            for y_, x_ in zip(ys, xs):
                d = math.hypot(x_ - hx, y_ - hy) / L
                s = sway if d > 0.62 else 0
                X = x_ + s
                if 0 <= X < W:
                    shift[y_, X] = True
            m = shift
            del n
        c.fill(m, "frond")
        lo, hi = (1, 3) if back else (2, 5)
        for y_, x_ in zip(*np.nonzero(m)):
            d = math.hypot(x_ - hx, y_ - hy) / L
            above = m[y_ - 1, x_] if y_ > 0 else False
            below = m[y_ + 1, x_] if y_ + 1 < H else False
            t = hi if (not above and below) else (lo if (above and not below) else (lo + hi) // 2 + (1 if d < 0.4 else 0))
            c.tone[y_, x_] = max(lo, min(hi, t))
        if not back:  # the midrib: lit along the front fronds
            ys_, xs_ = np.nonzero(rib0)
            for y_, x_ in zip(ys_, xs_):
                X = x_ + (sway if math.hypot(x_ - hx, y_ - hy) / L > 0.62 else 0)
                if 0 <= X < W and m[y_, X]:
                    c.tone[y_, X] = 5
    # the crown's heart: a dark knot where the fronds meet
    knot = c.m_ellipse(hx, hy + 3, tw + 1.5, 3.5)
    c.fill(knot, "palmbark", 2)
    c.shade_part(knot, tones=(1, 2, 3), norm=True)
    if dates:  # two hanging clusters of dates: 2 x 2 fruits, lit top-left, under the crown
        for (ox, oy) in ((-8, 9), (8, 10)):  # a cluster: a hanging oval, shaded, a few 2 x 2 lit dates
            cl = c.m_ellipse(hx + ox, hy + oy, 4.5, 6.5)
            c.fill(cl, "date")
            c.shade_part(cl, tones=(1, 2, 3, 4), norm=True)
            for (ddx, ddy) in ((-2, -3), (1, -1), (-1, 2), (2, 3)):
                fx, fy = int(hx + ox + ddx), int(hy + oy + ddy)
                for ex, ey, t in ((0, 0, 6), (1, 0, 5), (0, 1, 5), (1, 1, 4)):
                    if cl[fy + ey, fx + ex] and (fx + ddx) < hx + ox + 1:
                        c.put(fx + ex, fy + ey, "date", t)
    flare = c.m_ellipse(cx, G - 1, bw + 3, 3) & (np.mgrid[0:H, 0:W][0] <= G)
    c.fill(flare & ~trunk, "palmbark", 2)
    return finish(c, loose=("frond",))


# ------------------------------------------------------------------ dead tree

def snag(frame):
    """A dead acacia: a twisted trunk, a fork, bare branches with smaller forks, weathered grey wood
    with dark cracks along the grain."""
    W, H = 96, 128
    c = canvas(W, H)
    G = H - 2
    rng = random.Random(61)
    parts = lock(c, (46, G), (50, G - 58), 15, -4, 8)
    parts |= lock(c, (49, G - 52), (24, G - 96), 8, 6, 3)  # left limb
    parts |= lock(c, (51, G - 54), (74, G - 104), 8, -5, 3)  # right limb
    parts |= lock(c, (36, G - 76), (12, G - 84), 4, -2, 1.5)
    parts |= lock(c, (30, G - 86), (34, G - 118), 4, 3, 1.5)
    parts |= lock(c, (66, G - 88), (88, G - 92), 4, 2, 1.5)
    parts |= lock(c, (71, G - 98), (64, G - 124), 3.5, -2, 1.5)
    parts |= lock(c, (48, G - 26), (80, G - 50), 6, -3, 2)  # a low side branch (from the trunk's middle)
    parts |= lock(c, (44, G - 4), (30, G + 1), 7, -1, 2) | lock(c, (50, G - 4), (64, G + 1), 7, 1, 2)  # roots
    parts &= np.mgrid[0:H, 0:W][0] <= G
    c.fill(parts, "deadwood")
    c.shade_part(parts, tones=(1, 2, 3, 4, 5), light=(-0.8, -0.3, 0.5), norm=True)
    # cracks along the grain: wandering dark lines with a lit edge on their left (on the trunk only)
    trunk = lock(c, (46, G), (50, G - 58), 15, -4, 8)
    for y, x in zip(*np.nonzero(trunk & erode(parts))):
        u = (x + 1.6 * math.sin(y * 0.17) + 0.08 * y) % 6
        if u < 1.0:
            c.tone[y, x] = max(1, int(c.tone[y, x]) - 2)
        elif u < 2.0 and c.tone[y, x] >= 3:
            c.tone[y, x] = min(5, int(c.tone[y, x]) + 1)
    del rng, frame
    return finish(c)


# ------------------------------------------------------------------ cacti

def spines(c, mask, step, seed, rows=(0, 1)):
    """Spine marks: 2-texel diagonal pairs of the spine ramp (the v1 cactus's tan pairs), uneven."""
    for y, x in zip(*np.nonzero(mask)):
        if hsh(x, y, seed) % step == 0 and c.tone[y, x] >= 2:
            if all(0 <= y + r < c.h and 0 <= x + r < c.w and mask[y + r, x + r] for r in rows):
                c.put(x, y, "spine", 5)
                c.put(x + 1, y + 1, "spine", 3)


def saguaro(W, H, col_hw, arms, flower, seed):
    c = canvas(W, H)
    G = H - 2
    cx = W / 2
    yy, xx = np.mgrid[0:H, 0:W]
    top = 6 if flower else 3

    def capsule(x0, y0, x1, y1, hw):  # a vertical or horizontal rounded bar
        return ((xx + 0.5 >= min(x0, x1) - hw) & (xx + 0.5 <= max(x0, x1) + hw) & (yy + 0.5 >= min(y0, y1)) &
                (yy + 0.5 <= max(y0, y1))) | c.m_ellipse(x0, y0, hw, hw) | c.m_ellipse(x1, y1, hw, hw)
    col = capsule(cx, top + col_hw, cx, G + col_hw + 2, col_hw) & (yy <= G)
    parts = [col]
    for (side, y_join, reach, rise, hw) in arms:
        x_out = cx + side * reach
        arm = capsule(cx, y_join, x_out, y_join, hw) | capsule(x_out, y_join - rise, x_out, y_join, hw)
        parts.append(arm & ~col)
    # draw the far side's arm first, the column, then each arm with its own cylinder shading
    for p in parts:
        c.fill(p, "cactus")
    for p in parts:
        cyl_tone(c, p, tones=(1, 2, 3, 4, 5, 4))
    # ribs: vertical grooves every 4-5 texels, a lit ridge left of each (follows each part)
    for p in parts:
        for y in range(H):
            xs = np.nonzero(p[y])[0]
            if len(xs) < 6:
                continue
            x0, x1 = xs.min(), xs.max()
            for x in xs:
                u = (x - x0) % 5
                if u == 4 and x < x1 - 1:
                    c.tone[y, x] = max(1, int(c.tone[y, x]) - 1)
                elif u == 3 and c.tone[y, x] >= 3:
                    c.tone[y, x] = min(5, int(c.tone[y, x]) + 1)
    # the joints of the arms: a 2-row shade under the elbow
    for (side, y_join, reach, rise, hw) in arms:
        x_out = cx + side * reach
        for y in range(int(y_join + hw - 2), int(y_join + hw)):
            for x in range(int(min(cx, x_out)), int(max(cx, x_out)) + 1):
                if 0 <= y < H and 0 <= x < W and c.mat[y, x] and not col[y, x]:
                    c.tone[y, x] = 1
    spines(c, np.logical_or.reduce(parts) & erode(np.logical_or.reduce(parts)), 23, seed)
    if flower:  # the v1 pink flower on the top: 3 petals and a light heart
        fx, fy = int(cx), top - 1
        c.stamp([".pPp.", "pPhPp", ".ppp."], fx - 2, fy - 2,
                {"p": ("pink", 2), "P": ("pink", 4), "h": ("pink", 6)})
    return finish(c, loose=("cactus",))


def cactus(frame):
    """The v1 obj.cactus design at density 4 (24 x 40 -> 48 x 80): a column, the left arm lower, the
    right arm higher, a pink flower on top, tan spine pairs."""
    del frame
    return saguaro(48, 80, 8, [(-1, 50, 14, 16, 5), (1, 34, 14, 18, 5)], True, 3)


def cactus_l(frame):
    """A tall saguaro, 3 arms of different heights (no flower)."""
    del frame
    return saguaro(64, 128, 10, [(-1, 74, 18, 26, 6), (1, 54, 18, 30, 6), (1, 92, 15, 12, 5)], False, 4)


def barrel(frame):
    """A barrel cactus: a squat dome with ribs curving round it, a crown of small yellow flowers."""
    del frame
    W, H = 40, 40
    c = canvas(W, H)
    G = H - 2
    m = c.m_ellipse(20, 23, 14, 15) & (np.mgrid[0:H, 0:W][0] <= G)
    c.fill(m, "cactus")
    c.shade_part(m, tones=(1, 2, 3, 4, 5), norm=True)
    for y, x in zip(*np.nonzero(m)):  # ribs bend with the dome: grooves along x = 20 + k * w(y)
        w = max(1.0, math.sqrt(max(0.0, 1 - ((y - 23) / 15) ** 2)) * 14)
        u = ((x - 20) / w * 3.2 + 3.2) % 1.0
        if u < 0.16:
            c.tone[y, x] = max(1, int(c.tone[y, x]) - 1)
        elif u < 0.32 and c.tone[y, x] >= 3:
            c.tone[y, x] = min(5, int(c.tone[y, x]) + 1)
    spines(c, m & erode(m), 19, 5)
    for fx in (14, 19, 24):
        c.stamp([".y.", "yYy"], fx, 7 + (fx == 19) * -1, {"y": ("yellow", 3), "Y": ("yellow", 5)})
    return finish(c, loose=("cactus",))


def pear(frame):
    """A prickly pear: flat oval pads growing from each other, red fruit on the top pads."""
    del frame
    W, H = 64, 56
    c = canvas(W, H)
    G = H - 2
    pads = [(30, 42, 10, 12, -0.1), (16, 40, 8, 10, 0.4), (46, 38, 9, 11, -0.4), (24, 22, 8, 10, 0.25),
            (40, 20, 7, 9, -0.2), (52, 26, 6, 7, -0.6)]
    yy, xx = np.mgrid[0:H, 0:W]
    for (px, py, rx, ry, rot) in pads:  # back pads first (higher first)
        pass
    for (px, py, rx, ry, rot) in sorted(pads, key=lambda p: p[1]):
        X, Y = xx + 0.5 - px, yy + 0.5 - py
        u = X * math.cos(rot) + Y * math.sin(rot)
        v = -X * math.sin(rot) + Y * math.cos(rot)
        m = ((u / rx) ** 2 + (v / ry) ** 2 <= 1) & (yy <= G)
        c.fill(m, "cactus")
        c.shade_part(m, tones=(2, 3, 4, 5), norm=True)
        rim = m & ~erode(m)
        for y, x in zip(*np.nonzero(rim)):
            if x > px and y > py - 2:
                c.tone[y, x] = 1
        spines(c, m & erode(erode(m)), 13, int(px + py))
    for (fx, fy) in ((22, 11), (27, 12), (39, 10), (51, 18)):
        c.stamp([".fF", "fFf", "ffs"], fx - 1, fy - 1, {"f": ("fruit", 3), "F": ("fruit", 5), "s": ("fruit", 2)})
    return finish(c, loose=("cactus",))


def agave(frame):
    """An agave: a rosette of thick pointed blue-green leaves, the inner ones upright, a pale edge."""
    del frame
    W, H = 56, 44
    c = canvas(W, H)
    G = H - 2
    leaves = [(-70, 20, 7), (-110, 20, 7), (-35, 24, 7), (-145, 24, 7), (-10, 22, 6), (-170, 22, 6),
              (-90, 30, 8), (-55, 28, 7), (-125, 28, 7)]
    for (deg, L, w) in leaves:
        a = math.radians(deg)
        m = lock(c, (28, G - 4), (28 + math.cos(a) * L, G - 4 + math.sin(a) * L * 1.15), w, 0, 1)
        c.fill(m, "agave")
        c.shade_part(m, tones=(2, 3, 4, 5), norm=True, light=(-0.7, -0.6, 0.4))
        edge = m & ~erode(m)
        for y, x in zip(*np.nonzero(edge)):
            if math.cos(a) < 0 and x < 28 or math.cos(a) >= 0 and y < G - 6 and hsh(x, y, 2) % 3 == 0:
                c.tone[y, x] = 6
    return finish(c, loose=("agave",))


# ------------------------------------------------------------------ stones, bones, dry plants

def sandstone(W, H, seed):
    """A block of layered red sandstone: a flat lit top face, a front face in strata (alternate bands
    of 2 tones, wavy, each 3-6 rows), the right side in shade, a dark undercut at the base."""
    c = canvas(W, H)
    rng = random.Random(seed)
    G = H - 2
    top_y = int(H * 0.22)
    face_y = int(H * 0.42)
    pts = [(2, G), (3, face_y + 2), (W * 0.18, top_y + 2), (W * 0.5, top_y - 1), (W * 0.78, top_y + 3),
           (W - 3, face_y), (W - 2, G)]
    m = c.m_poly(pts)
    c.fill(m, "rstone", 3)
    bands = []
    y = face_y
    while y < G:
        bands.append(y)
        y += rng.randint(3, 6)
    for y_, x_ in zip(*np.nonzero(m)):
        yt = top_y + (face_y - top_y) * 0.0
        right = x_ > W * 0.72 + (y_ - face_y) * 0.15
        if y_ < face_y + int(1.5 * math.sin(x_ * 0.2)):
            t = 5 if x_ < W * 0.6 else 4
        else:
            k = sum(1 for b in bands if y_ >= b + int(1.2 * math.sin(x_ * 0.15 + b)))
            t = 3 if k % 2 else 2
            if right:
                t -= 1
            if y_ >= G - 2:
                t = 1
        del yt
        c.tone[y_, x_] = max(1, t)
    # a few cracks: short vertical dark lines through 1-2 strata
    for _ in range(max(2, W // 20)):
        x0 = rng.randint(6, W - 10)
        y0 = rng.randint(face_y + 3, G - 6)
        crack = c.m_line([(x0, y0), (x0 + rng.choice((-1, 1)), y0 + rng.randint(4, 7))], 1.2) & m
        c.set_tone(crack, 1)
    return finish(c, loose=("rstone",))


def rock_l(frame):
    del frame
    return sandstone(64, 48, 71)


def rock_s(frame):
    del frame
    return sandstone(40, 28, 72)


def bones(frame):
    """A bleached horned skull (facing left-front) and a curved rib beside it, half in the sand."""
    del frame
    W, H = 56, 32
    c = canvas(W, H)
    G = H - 2
    skull = c.m_poly([(8, 18), (12, 12), (22, 10), (28, 14), (28, 22), (22, 27), (14, 28), (9, 24)])
    snout = c.m_ellipse(13, 25, 6, 4)
    horn_l = lock(c, (12, 13), (3, 4), 4.5, 2, 1)
    horn_r = lock(c, (25, 12), (34, 5), 4.5, -2, 1)
    whole = skull | snout | horn_l | horn_r
    c.fill(whole, "bone")
    c.shade_part(whole, tones=(2, 3, 4, 5, 6), norm=True)
    c.fill(horn_l | horn_r, "bone")
    c.shade_part(horn_l | horn_r, tones=(1, 2, 3, 4), norm=True)
    for (ex, ey) in ((14, 17), (22, 17)):  # eye holes: dark 3 x 3 with a shaded rim
        c.stamp(["ddd", "ddd", ".d."], ex - 1, ey - 1, {"d": ("bone", 1)})
    c.stamp(["n.n"], 12, 24, {"n": ("bone", 1)})
    for i in range(5):  # a rib bone: a curved bar, and 3 short ribs
        pass
    rib = c.m_line([(34, 26), (40, 20), (47, 18), (53, 21)], 2.6)
    c.fill(rib & (np.mgrid[0:H, 0:W][0] <= G), "bone")
    c.shade_part(rib, tones=(2, 3, 4, 5), norm=True)
    for x0 in (39, 45, 51):
        r = c.m_line([(x0, 21), (x0 + 1, 27)], 2.2) & (np.mgrid[0:H, 0:W][0] <= G)
        c.fill(r, "bone", 3)
        c.set_tone(r & (np.mgrid[0:H, 0:W][1] > x0), 2)
    return finish(c, loose=("bone",))


def tumbleweed(frame):
    """A tumbleweed: a round lattice of dry curved stems (no solid fill; the sand shows between them),
    lit on the top left, darker on the bottom right."""
    del frame
    W, H = 40, 36
    c = canvas(W, H)
    rng = random.Random(81)
    cx, cy, R = 20, 18, 15
    ball = c.m_ellipse(cx, cy, R + 1, R)
    for _ in range(16):  # arcs: pieces of circles crossing the ball
        a0 = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(6, 14)
        ox, oy = cx + math.cos(a0) * rng.uniform(0, 8), cy + math.sin(a0) * rng.uniform(0, 7)
        s0 = rng.uniform(0, 2 * math.pi)
        pts = [(ox + math.cos(s0 + k * 0.25) * r, oy + math.sin(s0 + k * 0.25) * r * 0.85) for k in range(rng.randint(5, 9))]
        st = c.m_line(pts, 1.5) & ball
        c.fill(st, "dry")
    for a0 in (2.4, 4.0, 5.6):  # 3 long outer stems give the ball its round outline
        pts = [(cx + math.cos(a0 + k * 0.2) * R, cy + math.sin(a0 + k * 0.2) * (R - 1)) for k in range(9)]
        c.fill(c.m_line(pts, 1.6) & ball, "dry")
    k = c.mid("dry")
    for y, x in zip(*np.nonzero(c.mat == k)):
        d = (x - cx) + (y - cy)
        c.tone[y, x] = 5 if d < -10 else (4 if d < 0 else (3 if d < 10 else 2))
    return finish(c, loose=("dry",))


def drygrass(frame):
    """Dry desert grass: thin straw blades in a fan, seed tips on the tallest; sway: lean +1."""
    W, H = 40, 32
    c = canvas(W, H)
    G = H - 2
    for bx, h, lean in ((-12, 12, -5), (-8, 20, -4), (-4, 26, -2), (-1, 18, 0), (2, 27, 2), (5, 22, 3),
                        (9, 16, 5), (12, 10, 6), (0, 11, 1)):
        x0 = W // 2 + bx
        l2 = lean + (frame if h > 14 else 0)
        m = c.m_poly([(x0 - 1.3, G), (x0 + l2, G - h), (x0 + 1.3, G)])
        c.fill(m, "dry")
        for y, x in zip(*np.nonzero(m)):
            f = (G - y) / h
            c.tone[y, x] = (2, 3, 4, 5)[min(3, int(f * 4))] - (1 if x > x0 + l2 * f else 0)
        if h >= 22:
            tx, ty = int(x0 + l2), int(G - h)
            for d in range(4):
                c.put(tx, ty + d, "dry", 6 if d < 2 else 5)
                c.put(tx + 1, ty + d, "dry", 4)
    despeckle(c)
    c.outline()
    return c


def sage(frame):
    """A desert sage bush: 6 rounded grey-green masses of small leaves on a few woody stems, the top
    left masses lit, leaf marks on the lit edge only (the broadleaf way)."""
    del frame
    W, H = 56, 40
    c = canvas(W, H)
    rng = random.Random(91)
    G = H - 2
    stems = lock(c, (26, G), (16, G - 14), 3, 1, 1.5) | lock(c, (29, G), (40, G - 15), 3, -1, 1.5) | \
        lock(c, (28, G), (28, G - 18), 3, 0, 1.5)
    c.fill(stems, "deadwood", 2)
    clumps = [(16, 22, 10, 8), (28, 15, 11, 9), (40, 21, 10, 8), (10, 30, 8, 6), (46, 30, 8, 6), (28, 27, 12, 8)]
    whole = np.zeros((H, W), bool)
    for cl in clumps:
        whole |= scalloped(c, *cl, rng, 1.8)
    for cl in sorted(clumps, key=lambda q: q[1]):
        m = scalloped(c, *cl, rng, 1.8) & (np.mgrid[0:H, 0:W][0] <= G - 3)
        c.fill(m, "sage")
        c.shade_part(m, tones=(2, 3, 4, 5), global_mask=whole, gmix=0.4, norm=True)
        for y, x in zip(*np.nonzero(m)):
            if y > cl[1] and (y + 2 < H and not m[y + 2, x]):
                c.tone[y, x] = 2
    leaf_marks(c, "sage", every=23, seed=4)
    return finish(c, loose=("sage",))


def pebbles(frame):
    """Red-brown stones of different sizes, half sunk, lit top-left."""
    del frame
    c = canvas(40, 20)
    for (x, y, rx, ry) in ((8, 13, 5, 3.5), (19, 11, 4.5, 3), (28, 14, 6, 4), (35, 9, 3, 2.5), (15, 16, 3, 2)):
        m = c.m_ellipse(x, y, rx, ry)
        c.fill(m, "rstone")
        c.shade_part(m, tones=(2, 3, 4, 5), norm=True)
    return finish(c, loose=("rstone",))


def crop_top(img, rows=None):
    """Drop the fully transparent rows above the picture (the anchor is the bottom centre, so the feet do
    not move). `rows`: crop this many (the same for every sway frame of one kind)."""
    a = np.array(img)
    if rows is None:
        rows = int(np.argmax(a[..., 3].any(1)))
    return img.crop((0, rows, img.width, img.height)), rows


TREES = {"palm_l": (lambda f: palm("palm_l", f), 3), "palm_s": (lambda f: palm("palm_s", f), 3), "snag": (snag, 1)}
PROPS = {"cactus": (cactus, 1), "cactus_l": (cactus_l, 1), "barrel": (barrel, 1), "pear": (pear, 1),
         "agave": (agave, 1), "rock_l": (rock_l, 1), "rock_s": (rock_s, 1), "bones": (bones, 1),
         "tumbleweed": (tumbleweed, 1), "drygrass": (drygrass, 2), "sage": (sage, 1), "pebbles": (pebbles, 1)}


def write_trees():
    out = []
    for kind, (fn, frames) in TREES.items():
        imgs = [clean_isolated(fn(f).image()) for f in range(frames)]
        rows = min(int(np.argmax(np.array(i)[..., 3].any(1))) for i in imgs)  # the same crop for all frames
        for f, img in enumerate(imgs):
            out.append(save(crop_top(img, rows)[0], os.path.join(OUT, f"desert.tree.v3.{kind}.{f}.png")))
    return out


def write_props():
    out = []
    for kind, (fn, frames) in PROPS.items():
        imgs = [clean_isolated(fn(f).image()) for f in range(frames)]
        rows = min(int(np.argmax(np.array(i)[..., 3].any(1))) for i in imgs)
        if kind == "cactus":
            rows = 0  # obj.cactus replaces the v1 key: exactly 2 x its size (24 x 40 -> 48 x 80)
        for f in range(frames):
            img = crop_top(imgs[f], rows)[0]
            out.append(save(img, os.path.join(OUT, f"desert.prop.v3.{kind}.{f}.png")))
            if kind == "cactus":  # the key the game draws today (the v1 obj.cactus, exactly 2x its size)
                out.append(save(img, os.path.join(OUT, "obj.cactus.png")))
    return out
