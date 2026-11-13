"""v3 forest trees and props, 3 seasons (STYLE.md 7; the plains' passed ways: gen_flora_v3.py).

Files (src/art-release-v3/terrain/, <s.> = "" | "autumn." | "winter."), anchor the bottom centre:
  <s.>forest.tree.v3.<kind>.<f>.png  sway frames f 0-2 (the crown / tiers move, the trunk stays)
      pine_s   64 x 120   the forest's common pine (v2 forest.pine: 32 x 60) -- also written as
                          <s.>forest.pine.png (= frame 0), the key the game draws today
      pine_l  128 x 256   a big pine (8 tiers)
      spruce   80 x 208   a narrow spruce, tiers hanging down
      birch   112 x 160   a birch: white bark with dark marks, a light crown (autumn yellow);
                          winter: bare, frame 0 only
  <s.>forest.prop.v3.<kind>.<f>.png
      fern 48 x 40 (f 0-1, sway), toadstool 32 x 32, log_moss 80 x 40, rock_moss 48 x 40, roots 64 x 32
Winter: snow on the tiers / tops (2 texels or more, no crumbs under 4 texels), the fern dry under snow,
the toadstools snow-capped. No ground shadows baked in (STYLE 8).
"""

import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402

import gen_flora_v3 as FL  # noqa: E402  (the passed plains flora, read-only use)
from gen_nature_v3 import bark_texture, hsh  # noqa: E402
from hdkit import lock  # noqa: E402
from v3lib import ROOT, Canvas, clean_isolated, lift_ramp, save  # noqa: E402

OUT = os.path.join(ROOT, "src", "art-release-v3", "terrain")
PREFIX = FL.PREFIX
SWAY = FL.SWAY
BIRCH_BARK = lift_ramp(["#3a3a3a", "#8a8680", "#b4b0a8", "#d4d0c6", "#e6e2d8", "#f2efe6", "#ffffff"])
BIRCH_LEAF = {"summer": lift_ramp(["#10261a", "#204422", "#2c5628", "#3a6a2e", "#4e7e36", "#669440", "#86ac52"]),
              "autumn": lift_ramp(["#3a2c0a", "#644a0e", "#806012", "#a07e1a", "#bc9826", "#d4b034", "#ecce64"])}
TOAD = lift_ramp(["#3a0808", "#7a1010", "#9a1818", "#c02424", "#d83c30", "#ea5c44", "#ff9a7c"])
FERN = {"summer": lift_ramp(["#0e2214", "#1c3e22", "#24502a", "#2e6432", "#3e783a", "#549048", "#76ae5a"]),
        "autumn": lift_ramp(["#2a1a0c", "#5a3416", "#74441c", "#8a5624", "#a06a30", "#b8823e", "#d0a058"]),
        "winter": lift_ramp(["#2a2016", "#4e3e2a", "#62503a", "#766248", "#8a7658", "#a08c6c", "#bcaa88"])}


_FL_CANVAS = FL.canvas


def canvas(w, h, season, extra=None):
    c = _FL_CANVAS(w, h, season)
    for k, v in (extra or {}).items():
        c.ramps[k] = [tuple(x) for x in v]
    return c


# ------------------------------------------------------------------ conifers

CONIFERS = {  # W, H, tiers, crown top, crown bottom (fraction of H), half width at the bottom, trunk hw, droop, seed, gap
    # round 2 (P2-6): the three are told apart at 1x -- pine_s the plain cone; pine_l fewer tiers with
    # the trunk showing between them (a tall old pine); spruce many fine tiers whose tips hang down,
    # in a darker, bluer green
    "pine_s": (64, 120, 5, 0.02, 0.80, 30, 3.5, 0.0, 21, 0.0),
    "pine_l": (128, 256, 6, 0.01, 0.74, 56, 7.0, 0.0, 22, 0.45),
    "spruce": (80, 208, 12, 0.01, 0.86, 32, 4.0, 2.5, 23, 0.0),
}
SPRUCE = lift_ramp(["#061214", "#0e2426", "#122e30", "#163834", "#1c4238", "#244c44", "#365e56"])


def conifer(kind, season, frame):
    """The plains pine's way (tiers with jagged hanging edges, shaded as one cone, a shadow under
    each tier, needle sprays as 2-texel strokes, snow on the tiers in winter), made general: size,
    number of tiers, width and (spruce) tiers hanging down."""
    W, H, n, top, bot, hw_bot, tw, droop, seed, gap = CONIFERS[kind]
    rng = random.Random(seed)
    c = canvas(W, H, season, {"pine": SPRUCE} if kind == "spruce" else None)
    G = H - 3
    cx = W / 2
    yb_last = int(H * bot)
    ttop = (int(H * top) + 20) if gap else (yb_last - 12)  # pine_l: the trunk runs up between the tiers
    trunk = c.m_poly([(cx - tw, G), (cx - tw * 0.8, ttop + 12), (cx - 1.5, ttop), (cx + 1.5, ttop), (cx + tw * 0.8, ttop + 12), (cx + tw, G)])
    flare = lock(c, (cx - tw * 0.9, G - 5), (cx - tw * 3, G + 1), tw * 2, -1.5, 2) | \
        lock(c, (cx + tw * 0.9, G - 5), (cx + tw * 3, G + 1), tw * 2, 1.5, 2)
    c.fill(trunk | flare, "bark")
    c.shade_part(trunk | flare, tones=(1, 2, 3, 4, 5), light=(-0.8, -0.3, 0.5), norm=True)
    bark_texture(c, trunk, period=max(3, int(tw)))
    y_top = int(H * top) + 1
    whole = c.m_poly([(cx, y_top), (cx + hw_bot + 2, yb_last + 4), (cx - hw_bot - 2, yb_last + 4)])
    prev = None
    shelves, tiers = [], []  # (round 3) the winter spruce's snow shelves
    sway = SWAY[frame]
    rj = random.Random(seed * 31 + 5)  # round 3 (P3): pine_l's uneven tiers (own stream: pine_s / spruce unchanged)
    for i in range(n):
        f = (i + 1) / n
        yb = int(y_top + (yb_last - y_top) * (0.12 + 0.88 * f ** 1.1))
        hw = max(5, hw_bot * (0.18 + 0.82 * f))
        uneven = kind == "pine_l"
        if uneven and 0 < i < n - 1:
            yb += rj.choice((-3, -2, 0, 2, 3))
            hw *= 1 + rj.uniform(-0.08, 0.08)
        off = (rng.choice((-1, 0, 1)) if i else 0) * max(1, W // 64)
        skew = rng.uniform(-0.12, 0.12)
        cxi = cx + off + round(sway * (1 - i / (n - 1)))
        yt = y_top if i == 0 else int(y_top + (yb_last - y_top) * (0.12 + 0.88 * (i / n) ** 1.1)) - int(H * 0.04)
        if gap and i:  # a gap above each tier (the trunk shows)
            yt = int(yt + (yb - yt) * gap)
        pts = [(cxi + skew * 10, yt)]
        if i or uneven:  # round 3: pine_l's top tier gets shoulders too (snow lies on them in winter)
            pts.append((cxi + hw * 0.5, yb - H * (0.045 if i == 0 else 0.055)))
        k = max(6 if uneven else 4, int(hw // 4))
        for j in range(k + 1):
            x = cxi + hw - 2 * hw * j / k
            dip = rng.choice((2, 3, 4)) if j % 2 == 0 else rng.choice((-1, 0))
            hang = droop * (1 - abs(x - cxi) / hw) * -2 + droop * 4 * (abs(x - cxi) / hw) ** 2
            pts.append((x, yb + dip + (1 - abs(x - cxi) / hw) * 3 + hang))
        if i or uneven:
            pts.append((cxi - hw * 0.55, yb - H * (0.045 if i == 0 else 0.055)))
        m = c.m_poly(pts)
        c.fill(m, "pine")
        c.shade_part(m, tones=(1, 2, 3, 4, 5, 6), global_mask=whole, gmix=0.4, light=(-0.7, -0.5, 0.5), norm=True)
        if prev is not None:
            sh = np.zeros_like(m)
            sh[3:, :] = prev[:-3, :]
            sh &= m & ~prev
            for y, x in zip(*np.nonzero(sh)):
                c.tone[y, x] = max(1, int(c.tone[y, x]) - 2)
            shelves.append((i, sh, cxi, hw))
        tiers.append(m)
        prev = m if prev is None else (prev | m)
    kp = c.mid("pine")
    for y in range(2, H - 3):
        for x in range(2, W - 3):
            if c.mat[y, x] != kp or hsh(x, y, seed) % 23:
                continue
            t = int(c.tone[y, x])
            lit = t >= 4
            for dx, dy in ([(0, 0), (1, 0), (1, 1), (2, 1)] if lit else [(0, 0), (-1, 0), (-1, 1), (-2, 1)]):
                if c.mat[y + dy, x + dx] == kp:
                    c.tone[y + dy, x + dx] = min(6, t + 1) if lit else max(1, t - 1)
    if season == "winter":
        if kind == "spruce":
            spruce_shelves(c, shelves, tiers, seed)
        if kind == "pine_l":
            top_tier_snow(c, tiers, seed)
        FL.snow_caps(c, ("pine",), depth=(2, 5), seed=seed)
        FL.drop_small_snow(c, 4, back="pine")
    return FL.finish(c, loose=())


def spruce_shelves(c, shelves, tiers, seed):
    """Round 3 (inspection P2-2: the winter spruce had almost no snow, 0.9 %): its drooping tiers
    overlap, so snow_caps finds almost no top surface. The snow lies instead on each tier's upper
    face where it shows under the tier above (the 3 rows under the hanging edge, the summer's shade
    band): a shelf 1-2 rows deep on the outer part of each layer (lit left: 6, some columns over 5; the shaded
    right: 5 over 4, with gaps), the middle of the tree left green. Pieces
    under 4 texels go back to pine (drop_small_snow)."""
    kp, ks = c.mid("pine"), c.mid("snow")
    rng = random.Random(seed * 7 + 3)
    for i, sh, cxi, hw in shelves:
        later = np.zeros_like(sh)
        for m in tiers[i + 1:]:
            later |= m
        vis = sh & ~later & (c.mat == kp)
        lo, hi = 0.42 + 0.1 * rng.random(), 0.78 + 0.08 * rng.random()  # the outer part of the branch layer
        for y, x in zip(*np.nonzero(vis)):
            r = (x + 0.5 - cxi) / hw
            if not (lo < abs(r) < hi) or (r > 0 and hsh(x // 2, i, seed + 9) % 2 == 0):
                continue  # the shaded right side holds less
            top = y - 1 < 0 or not vis[y - 1, x]
            if not top and not (hsh(x, i, seed + 5) % 3 == 0 and (y - 2 < 0 or not vis[y - 2, x])):
                continue  # 1 row, or 2 on a third of the columns
            c.mat[y, x] = ks
            c.tone[y, x] = (6 if top else 5) if r < 0 else (5 if top else 4)


def top_tier_snow(c, tiers, seed):
    """Round 3 (P3): pine_l's top tier is a steep spire, so snow_caps (top runs 2+ wide) leaves it bare.
    Snow clings along its outer slope instead: on the lit left the outermost 2 texels of each row, on the
    shaded right 1 texel on every other pair of rows, from 30 % to 90 % of the tier's visible height.
    Pieces under 4 texels go back to pine (drop_small_snow)."""
    kp, ks = c.mid("pine"), c.mid("snow")
    later = np.zeros_like(tiers[0])
    for m in tiers[1:]:
        later |= m
    vis = tiers[0] & ~later & (c.mat == kp)
    ys = np.nonzero(vis.any(axis=1))[0]
    if not len(ys):
        return
    y0, y1 = ys.min(), ys.max()
    for y in range(y0, y1 + 1):
        fy = (y - y0) / max(1, y1 - y0)
        xs = np.nonzero(vis[y])[0]
        if not (0.3 <= fy <= 0.9) or len(xs) < 4:
            continue
        for x in xs[:2]:
            c.mat[y, x] = ks
            c.tone[y, x] = 6 if x == xs[0] else 5
        if (y // 2) % 2 == 0:
            c.mat[y, xs[-1]] = ks
            c.tone[y, xs[-1]] = 4


# ------------------------------------------------------------------ birch (round 2: its own form)

BIRCH_BRANCHES = [  # (height on the trunk 0..1 from the foot, side -1 left / 1 right, length, rise in degrees)
    (0.36, 1, 22, 38), (0.45, -1, 26, 46), (0.55, 1, 28, 52), (0.63, -1, 20, 58), (0.71, 1, 22, 62),
    (0.79, -1, 16, 66), (0.86, 1, 14, 70)]
BIRCH_CLUMPS = [  # leaf clusters at branch tips and up the trunk: (branch index or -1 = trunk, t along, rx, ry)
    (0, 1.0, 11, 8), (1, 1.0, 12, 9), (1, 0.55, 8, 6), (2, 1.0, 12, 9), (2, 0.5, 9, 7), (3, 1.0, 10, 8),
    (4, 1.0, 10, 8), (5, 1.0, 9, 7), (6, 1.0, 8, 7), (-1, 0.97, 9, 8), (-1, 0.84, 8, 6), (4, 0.5, 7, 6)]


def birch(season, frame):
    """Round 2 (inspection P1-1: the round-1 birch was the plains oak recoloured): a birch of its own.
    A tall slender trunk (7 -> 2 texels, leaning a little to the right, 80 % of the height), 7 thin
    branches rising at 38-70 degrees, alternating sides at uneven heights, short at the top; small
    light leaf clusters (rx 7-12) at the branch tips and up the trunk, more on the right (asymmetric),
    shaded the broadleaf way (leaf_masses). Winter: the same skeleton bare, twigs off the branch tips,
    snow only on the thick parts. 112 x 160, the foot at the bottom centre."""
    W, H = 112, 160
    ramps = {"bark": BIRCH_BARK}
    if season in BIRCH_LEAF:
        ramps["leaf"] = BIRCH_LEAF[season]
    c = canvas(W, H, season, ramps)
    rng = random.Random(43)
    G = H - 3
    top = int(H * 0.12)

    def trunk_at(t):  # t 0 = foot, 1 = top
        return (W / 2 - 2 + 6 * t * t, G - (G - top) * t)
    pts = [trunk_at(i / 10) for i in range(11)]
    trunk = np.zeros((H, W), bool)
    for i in range(10):
        trunk |= lock(c, pts[i], pts[i + 1], 7.5 - 5.2 * i / 10, 0, 7.5 - 5.2 * (i + 1) / 10)
    roots = lock(c, trunk_at(0.02), (W / 2 - 12, G + 1), 6, -1, 2) | lock(c, trunk_at(0.02), (W / 2 + 9, G + 1), 6, 1, 2)
    sway = SWAY[frame]
    tips = []
    branches = np.zeros((H, W), bool)
    for (t, side, ln, rise) in BIRCH_BRANCHES:
        bx, by = trunk_at(t)
        a = math.radians(rise)
        sw = sway * t  # the upper branches move more
        tip = (bx + side * math.cos(a) * ln + sw, by - math.sin(a) * ln)
        branches |= lock(c, (bx, by), tip, 4.0 - 1.5 * t, side * 2, 1.4)
        tips.append(((bx, by), tip))
    wood = trunk | roots | branches
    if season == "winter":
        twigs = np.zeros((H, W), bool)
        for (b0, tip) in tips:
            for k in range(2):
                ang = math.radians(rng.uniform(50, 85))
                side = 1 if tip[0] > b0[0] else -1
                ln = rng.uniform(7, 12)
                twigs |= lock(c, tip, (tip[0] + side * math.cos(ang) * ln * (0.4 + 0.6 * k), tip[1] - math.sin(ang) * ln), 2.2, 0.5, 1.0)
        wood |= twigs
    c.fill(wood, "bark")
    c.shade_part(wood, tones=(2, 3, 4, 5, 6), light=(-0.8, -0.3, 0.5), norm=True)
    # the birch's marks: short dark dashes across the trunk (2-4 wide, 2 high), uneven
    ys, xs = np.nonzero(trunk)
    for y, x in zip(ys, xs):
        if (y * 7 + (x // 3) * 3) % 13 or rng.random() > 0.55:
            continue
        w = rng.randint(2, 4)
        if all(trunk[y, x + d] and trunk[y + 1, x + d] for d in range(w) if x + d < W and y + 1 < H):
            for d in range(w):
                if x + d < W and y + 1 < H:
                    c.tone[y, x + d] = 1
                    c.tone[y + 1, x + d] = 1
    if season == "winter":
        FL.snow_caps(c, ("bark",), depth=(2, 2), seed=7, min_thick=5)
        FL.drop_small_snow(c, 10)
        return FL.finish(c, loose=("bark", "snow"))
    clumps = []
    for (bi, t, rx, ry) in BIRCH_CLUMPS:
        if bi < 0:
            x, y = trunk_at(t)
            x += sway * t
        else:
            (b0, tip) = tips[bi]
            x, y = b0[0] + (tip[0] - b0[0]) * t, b0[1] + (tip[1] - b0[1]) * t
        clumps.append((x, y - 2, rx, ry))
    crown = np.zeros((H, W), bool)
    for (x, y, rx, ry) in clumps:
        crown |= c.m_ellipse(x, y, rx + 4, ry + 4)
    back = np.zeros((H, W), bool)  # no dark inside behind the clusters: the birch is airy (gaps show)
    from gen_nature_v3 import leaf_masses
    leaf_masses(c, clumps, rng, crown, back, before=None)
    return FL.finish(c)


# ------------------------------------------------------------------ props

def fern(season, frame):
    """A fern: 7 arching fronds from one root, each a tapering rib with paired leaflets (2-3 texels),
    lit on its upper side. Sway: the tips move 1 texel. Winter: dry brown fronds, snow on the root."""
    W, H = 48, 40
    c = canvas(W, H, season, {"fern": FERN[season]})
    G = H - 2
    k = c.mid("fern")
    fronds = [(-1.9, 26), (-1.35, 30), (-1.0, 24), (-1.57, 32), (-2.15, 24), (-0.7, 20), (-2.5, 19)]
    if season == "winter":  # round 2: three dry frond tips standing out of a snow mound (no brown smudge)
        fronds = [(-1.75, 22), (-1.3, 20), (-2.0, 17)]
    for i, (a, ln) in enumerate(fronds):
        for d in range(ln):
            t = d / ln
            bend = 0.9 * t * t * (1 if math.cos(a) > 0 else -1)
            x = W / 2 + math.cos(a) * d + bend * 6 + frame * t * t
            y = G - math.sin(-a) * d + t * t * 4
            xi, yi = int(x), int(y)
            if not (1 <= xi < W - 1 and 1 <= yi < H - 1):
                continue
            c.mat[yi, xi], c.tone[yi, xi] = k, 3
            if d % 2 == 0 and 2 < d < ln - 1:
                ll = max(1, int(3 * (1 - t)) + 1)
                for s in (-1, 1):
                    for e in range(1, ll + 1):
                        X, Y = xi + s * e, yi - (1 if s < 0 else 0)
                        if 1 <= X < W - 1 and 1 <= Y < H - 1:
                            c.mat[Y, X], c.tone[Y, X] = k, 5 if s < 0 else 2
    if season == "winter":
        mound = c.m_ellipse(W / 2, G + 2, 15, 8) & c.m_rect(0, 0, W - 1, G)
        c.fill(mound, "snow")
        c.shade_part(mound, tones=(3, 4, 5, 6), light=(-0.5, -0.8, 0.5), norm=True)
        return FL.finish(c, loose=("fern", "snow"))
    return FL.finish(c, loose=("fern",))


def toadstool(season, frame):
    """3 fly agarics: red domed caps with 2 x 2 white spots, pale gills and stems. Winter: snow on the
    caps (the spots under it)."""
    W, H = 32, 32
    c = canvas(W, H, season, {"toad": TOAD})
    G = H - 2
    for cx, h, r in ((10, 12, 6.5), (20, 16, 7.5), (26, 8, 4.5)):
        stem = c.m_rect(int(cx - 1.5), G - h, int(cx + 1.5), G)
        c.fill(stem, "white")
        c.shade_part(stem, tones=(2, 3, 4, 5), norm=True)
        cap = c.m_ellipse(cx, G - h, r, r * 0.75) & c.m_rect(0, 0, W - 1, int(G - h + 1))
        c.fill(cap, "toad")
        c.shade_part(cap, tones=(2, 3, 4, 5), norm=True)
        c.fill(c.m_rect(int(cx - r + 1), int(G - h + 1), int(cx + r - 1), int(G - h + 1)), "white", 2)
        if season != "winter":
            for dx, dy in ((-r * 0.45, -r * 0.35), (r * 0.25, -r * 0.5), (r * 0.5, -r * 0.1)):
                x, y = int(cx + dx), int(G - h + dy)
                if cap[y, x] and cap[y + 1, x + 1]:
                    c.fill(c.m_rect(x, y, x + 1, y + 1), "white", 6)
    if season == "winter":
        FL.snow_caps(c, ("toad",), depth=(2, 3), seed=12)
    return FL.finish(c, loose=("toad", "white", "snow"))


def log_moss(season, frame):
    """A fallen log (80 x 40): bark with grooves along it, a cut end with rings on the left, a moss
    cushion along its top (lit), a broken branch stub. Winter: snow over the moss."""
    W, H = 80, 40
    c = canvas(W, H, season)
    G = H - 3
    body = c.m_poly([(10, G - 22), (74, G - 20), (77, G - 10), (74, G), (10, G), (6, G - 10)])
    c.fill(body, "bark")
    c.shade_part(body, tones=(1, 2, 3, 4), light=(-0.3, -0.9, 0.5), norm=True)
    for y in range(G - 19, G - 1, 4):  # grooves along the log
        for x in range(12, 74):
            if body[y, x] and hsh(x // 9, y, 3) % 4:
                c.tone[y, x] = max(1, int(c.tone[y, x]) - 1)
    end = c.m_ellipse(9, G - 11, 6, 11)
    c.fill(end, "wood", 4)
    for r, t in ((8, 3), (5, 4), (2.5, 3)):
        c.fill(c.m_ellipse(9, G - 11, r * 0.55, r) & ~c.m_ellipse(9, G - 11, r * 0.55 - 1, r - 1), "wood", t - 1)
    stub = lock(c, (52, G - 20), (60, G - 31), 5, 1, 2)
    c.fill(stub & ~body, "bark")
    c.shade_part(stub & ~body, tones=(2, 3, 4), norm=True)
    if season == "winter":
        FL.snow_caps(c, ("bark", "wood"), depth=(3, 4), seed=21)
        FL.drop_small_snow(c, 6)
    else:
        moss = c.m_poly([(14, G - 21), (40, G - 25), (70, G - 23), (72, G - 18), (16, G - 17)]) & body
        c.fill(moss, "moss")
        c.shade_part(moss, tones=(2, 3, 4, 5), light=(-0.5, -0.8, 0.5), norm=True)
    return FL.finish(c, loose=("bark", "snow", "moss"))


def rock_moss(season, frame):
    """The plains' rock_m (48 x 36, passed) on a 48 x 40 frame with a moss cushion over its top and
    down its left side (summer / autumn); winter: the plains rock's snow cap."""
    r = FL.rock(season, frame, "rock_m")
    c = canvas(48, 40, season)
    c.mat[4:, :] = 0
    names = r.names
    for y in range(r.h):
        for x in range(r.w):
            if r.mat[y, x]:
                c.mat[y + 4, x] = c.mid(names[r.mat[y, x]])
                c.tone[y + 4, x] = r.tone[y, x]
    if season != "winter":
        ks = c.mid("stone")
        top = np.zeros_like(c.mat, bool)
        for x in range(c.w):
            ys = np.nonzero(c.mat[:, x] == ks)[0]
            if len(ys):
                for d in range(3 + (x < 24) * 2):
                    if ys.min() + d < c.h and c.mat[ys.min() + d, x] == ks:
                        top[ys.min() + d, x] = True
        top &= c.m_rect(4, 0, 34, 39)
        c.fill(top, "moss")
        c.shade_part(top, tones=(2, 3, 4, 5), light=(-0.5, -0.8, 0.5), norm=True)
    c.mat[c.tone == 0] = 0  # the old outline goes; finish() outlines again
    return FL.finish(c, loose=("stone", "moss", "snow"))


def roots(season, frame):
    """Surface roots (64 x 32): 3 tapering roots arching out of the ground, lit on top, a dark crease
    where each enters the ground. Winter: snow along their tops."""
    W, H = 64, 32
    c = canvas(W, H, season)
    G = H - 3
    m = np.zeros((H, W), bool)
    for (x0, x1, top, w) in ((6, 40, 12, 6), (24, 60, 17, 5), (12, 30, 22, 4)):
        pts = [(x0 + (x1 - x0) * t / 10, G - math.sin(math.pi * t / 10) * (G - top)) for t in range(11)]
        for a, b in zip(pts, pts[1:]):
            m |= lock(c, a, b, w * (1 - 0.3 * abs(a[0] - (x0 + x1) / 2) / (x1 - x0)), 0, w * 0.8)
    c.fill(m, "bark")
    c.shade_part(m, tones=(1, 2, 3, 4), light=(-0.5, -0.8, 0.5), norm=True)
    bark_texture(c, m, period=4)
    if season == "winter":
        FL.snow_caps(c, ("bark",), depth=(2, 3), seed=17, min_thick=6)
        FL.drop_small_snow(c, 10)  # no spots on the bark's bumps: only the root's thick tops
    return FL.finish(c, loose=("bark", "snow"))


TREES = {"pine_s": lambda s, f: conifer("pine_s", s, f), "pine_l": lambda s, f: conifer("pine_l", s, f),
         "spruce": lambda s, f: conifer("spruce", s, f), "birch": birch}
PROPS = {"fern": (fern, 2), "toadstool": (toadstool, 1), "log_moss": (log_moss, 1), "rock_moss": (rock_moss, 1),
         "roots": (roots, 1)}


SNOW_RGB = [tuple(int(v) for v in c) for c in FL.SNOW]


def clean_snow(img, n=4):
    """Both passes (round 2): all snow tones 1-6, then only the bright ones (4-6): a bright piece of
    2-3 texels inside the shaded snow is a crumb too (inspection P3)."""
    img = _clean_snow(_clean_snow(img, n, SNOW_RGB[1:]), n, SNOW_RGB[4:])
    return _clean_snow(img, n, SNOW_RGB[1:])  # what the bright pass leaves (a shaded piece) goes too


def _clean_snow(img, n, tones):
    """A last pass on the picture: a piece of snow (snow tones 1-6, not the outline) smaller than n
    texels takes the commonest neighbouring colour that is not snow (no crumbs: STYLE 7.1b)."""
    a = np.array(img.convert("RGBA"))
    H, W = a.shape[:2]
    snow = set(tones)
    m = np.zeros((H, W), bool)
    for y, x in zip(*np.nonzero(a[..., 3] == 255)):
        m[y, x] = tuple(int(v) for v in a[y, x, :3]) in snow
    seen = np.zeros_like(m)
    for y in range(H):
        for x in range(W):
            if not m[y, x] or seen[y, x]:
                continue
            comp, st = [], [(y, x)]
            seen[y, x] = True
            while st:
                p, q = st.pop()
                comp.append((p, q))
                for c, d in ((p + 1, q), (p - 1, q), (p, q + 1), (p, q - 1)):
                    if 0 <= c < H and 0 <= d < W and m[c, d] and not seen[c, d]:
                        seen[c, d] = True
                        st.append((c, d))
            if len(comp) >= n:
                continue
            cs = set(comp)
            nb = [tuple(int(v) for v in a[c, d]) for p, q in comp for c, d in ((p + 1, q), (p - 1, q), (p, q + 1), (p, q - 1))
                  if 0 <= c < H and 0 <= d < W and (c, d) not in cs and a[c, d, 3] == 255 and not m[c, d]]
            if not nb:
                continue
            best = max(set(nb), key=nb.count)
            for p, q in comp:
                a[p, q] = best
    from PIL import Image
    return Image.fromarray(a, "RGBA")


def write_trees():
    out = []
    for season, pre in PREFIX.items():
        for kind, fn in TREES.items():
            frames = 1 if (season == "winter" and kind == "birch") else 3
            for f in range(frames):
                img = clean_isolated(fn(season, f).image())
                if season == "winter":
                    img = clean_snow(img)
                out.append(save(img, os.path.join(OUT, f"{pre}forest.tree.v3.{kind}.{f}.png")))
                if kind == "pine_s" and f == 0:  # the key the game draws today (v2 forest.pine, 32 x 60)
                    out.append(save(img, os.path.join(OUT, f"{pre}forest.pine.png")))
    return out


def write_props():
    out = []
    for season, pre in PREFIX.items():
        for kind, (fn, frames) in PROPS.items():
            for f in range(frames):
                img = clean_isolated(fn(season, f).image())
                if season == "winter":
                    img = clean_snow(img)
                out.append(save(img, os.path.join(OUT, f"{pre}forest.prop.v3.{kind}.{f}.png")))
    return out
