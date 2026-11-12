"""v3 production order 3: the plains trees and props, 3 seasons, with sway frames (STYLE.md 7).

Drawn the way the pilot settled (round 4): broadleaf crowns as leaf masses with clear light / shade
faces (gen_nature_v3.leaf_masses), trunks tapering on into the crown, no near-black (ramps lifted to
luma >= 36), no lone texels (despeckle), outlines in the material's own tone 0.

Files (src/art-release-v3/terrain/, <s.> = "" | "autumn." | "winter."):
  <s.>plains.tree.v3.<kind>.<f>.png   kind: oak_l 160x224, oak_m 112x160, sapling 64x112, pine 96x200
                                      f = sway frame 0-2 (the crown moves 1 texel; the trunk stays)
  <s.>plains.prop.v3.<kind>.<f>.png   15 kinds (PROPS below); f = 0-1 for grass and flowers (sway),
                                      0 for the rest
Anchor: the bottom centre (the trunk's / object's foot on the bottom row).
Winter: the broadleaf trees are bare (trunk, branches, twigs, snow on their tops), the pine and the
props get snow caps, grass and flowers are dry stalks. Autumn: leaves and grass in autumn colours.
Run: python3 tools/art_v3/gen_flora_v3.py [summer|autumn|winter|all]
"""

import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402

from gen_nature_v3 import (BARK, BERRY, LEAF, MOSS, PINE, PINK, STONE, WHITE, WOOD, YELLOW, bark_texture,  # noqa: E402
                           hsh, leaf_masses)
from hdkit import lock  # noqa: E402
from v3lib import ROOT, Canvas, clean_isolated, despeckle, erode, lift_ramp, save  # noqa: E402

OUT = os.path.join(ROOT, "src", "art-release-v3", "terrain")
GRASS = lift_ramp(["#16301c", "#2a5030", "#335d3a", "#3c6a38", "#4e773f", "#528446", "#6c9e58"])
SEASON_RAMPS = {
    "summer": dict(leaf=LEAF, grass=GRASS, moss=MOSS),
    "autumn": dict(leaf=lift_ramp(["#4a1e0e", "#7a2e14", "#9a4018", "#b85a20", "#d07a28", "#e09a38", "#f0c060"]),
                   grass=lift_ramp(["#2e2010", "#5e4420", "#744b28", "#8a6630", "#998238", "#a88440", "#c4a058"]),
                   moss=lift_ramp(["#10160e", "#232e1c", "#2a3723", "#36402a", "#434a31", "#4a5438", "#62684a"])),
    "winter": dict(leaf=LEAF,
                   grass=lift_ramp(["#3a3020", "#6a5a3a", "#80704a", "#98865a", "#ab9a6c", "#bcac80", "#d4c8a0"]),
                   moss=lift_ramp(["#2a3040", "#4a5468", "#5a6478", "#6c7688", "#7e889a", "#909aac", "#b0b8c8"])),
}
SNOW = lift_ramp(["#3a4866", "#7a8cae", "#99abc7", "#b8c8e0", "#cadbe9", "#dce6f2", "#f8fbff"])
PREFIX = {"summer": "", "autumn": "autumn.", "winter": "winter."}
SWAY = (0, 1, -1)


def canvas(w, h, season):
    r = dict(bark=BARK, pine=PINE, wood=WOOD, stone=STONE, pink=PINK, white=WHITE, yellow=YELLOW, berry=BERRY,
             snow=SNOW)
    r.update(SEASON_RAMPS[season])
    return Canvas(w, h, r)


def finish(c, keep=(), loose=("leaf",)):
    despeckle(c, keep=keep, loose=loose)
    c.outline()
    c.shadow_band()
    return c


def snow_caps(c, mats, depth=(2, 4), seed=0, min_thick=0):
    """Snow on the tops: every top surface of `mats` (a texel with no `mats` above it) gets snow 2-4
    deep with a lit top row. Round 5: only where the top surface is at least 2 texels wide (no lone
    snow dots on twig tips), and a cap is never thinner than 2 rows."""
    ks = {c.mid(m) for m in mats}
    rng = random.Random(seed)
    H, W = c.h, c.w
    top = np.zeros((H, W), bool)
    for y in range(1, H):
        for x in range(W):
            top[y, x] = c.mat[y, x] in ks and c.mat[y - 1, x] not in ks
            if top[y, x] and min_thick:  # round 6: only where the wood is thick (not on the thin tips)
                th = 0
                while y + th < H and c.mat[y + th, x] in ks:
                    th += 1
                top[y, x] = th >= min_thick
    caps = []
    for y in range(1, H):
        x = 0
        while x < W:
            if not top[y, x]:
                x += 1
                continue
            x0 = x
            while x < W and (top[y, x] or (y > 0 and top[y - 1, x]) or (y + 1 < H and top[y + 1, x])) and \
                    c.mat[y, x] in ks:
                x += 1
            if x - x0 >= 2:
                d = rng.randint(max(2, depth[0]), max(2, depth[1]))
                caps.extend((xx, y, d) for xx in range(x0, x))
            x = max(x, x0 + 1)
    for x, y, d in caps:
        for i in range(d):
            if y + i < H and c.mat[y + i, x] in ks:
                c.mat[y + i, x] = c.mid("snow")
                c.tone[y + i, x] = 6 if i == 0 else (5 if i == 1 else 4)
    return c


# ------------------------------------------------------------------ broadleaf trees

OAK_CLUMPS = [(80, 50, 24, 20), (52, 70, 22, 18), (108, 68, 22, 18), (80, 94, 30, 23), (36, 108, 22, 19),
              (124, 106, 22, 19), (32, 148, 18, 16), (128, 150, 18, 16), (55, 152, 23, 21), (105, 154, 23, 21)]


def broadleaf(kind, season, frame):
    """oak_l 160x224, oak_m 112x160, sapling 64x112: one design scaled (the large oak of the pilot)."""
    W, H, s, nclumps = {"oak_l": (160, 224, 1.0, 10), "oak_m": (112, 160, 0.70, 8),
                        "sapling": (64, 112, 0.40, 5)}[kind]
    c = canvas(W, H, season)
    rng = random.Random({"oak_l": 11, "oak_m": 12, "sapling": 13}[kind])
    G = H - 3

    def P(x, y):  # the large oak's coordinates -> this size (foot at the bottom centre)
        return (W / 2 + (x - 80) * s, G - (221 - y) * s)

    def L(root, tip, w, bend, tipw):
        return lock(c, P(*root), P(*tip), max(2.0, w * s), bend * s, max(1.0, tipw * s))
    tw = max(4, 10 * s)
    trunk = c.m_poly([P(80 - tw, 221), P(80 - tw * 0.9, 178), P(80 - tw * 0.7, 160), P(80 - tw * 0.5, 136),
                      P(80 - tw * 0.3, 108), P(80 + tw * 0.3, 108), P(80 + tw * 0.5, 136), P(80 + tw * 0.7, 160),
                      P(80 + tw * 0.9, 178), P(80 + tw, 221)])
    roots = L((73, 215), (56, 222), 8, -2, 2) | L((87, 215), (105, 222), 8, 2, 2)
    branches = L((75, 160), (50, 132), 9, 3, 2.5) | L((85, 150), (110, 124), 8, -3, 2.0)
    if season == "winter":
        return bare(c, trunk, roots, branches, P, L, s, rng, kind)
    sway = SWAY[frame]
    clumps = []
    shapes = {"oak_l": OAK_CLUMPS,
              # round 5: the lower masses close in on the trunk and sit lower (trunk-only rows <= 25%)
              "oak_m": OAK_CLUMPS[:6] + [(46, 150, 22, 18), (114, 152, 22, 18), (70, 164, 26, 20), (96, 166, 26, 20)],
              "sapling": [(80, 60, 30, 24), (54, 96, 26, 22), (106, 94, 26, 22), (80, 122, 30, 22),
                          (64, 160, 24, 18), (98, 162, 24, 18)]}[kind]
    for (x, y, rx, ry) in shapes:
        px, py = P(x, y)
        dx = round(sway * max(0.0, 1 - (y - 40) / 140))  # the top moves 1, the bottom 0
        clumps.append((px + dx, py, rx * s, ry * s))
    ccx, ccy = P(80, 104)
    crown = c.m_ellipse(ccx + sway * 0.5, ccy, 74 * s, 74 * s)
    back = np.zeros((H, W), bool)
    for (cx_, cy_, rx_, ry_) in clumps:
        back |= c.m_ellipse(cx_, cy_ + 2 * s, rx_ + 6 * s, ry_ + 9 * s)
    back &= c.m_ellipse(ccx, P(80, 108)[1], 70 * s, 64 * s)

    def wood_layer():
        wood = trunk | roots | branches
        c.fill(wood, "bark")
        c.shade_part(wood, tones=(1, 2, 3, 4, 5), light=(-0.8, -0.3, 0.5), norm=True)
        bark_texture(c, trunk, period=max(3, int(5 * s + 0.5)))
        lim = P(80, 172)[1]
        for y, x in zip(*np.nonzero(wood)):
            if y < lim:
                c.tone[y, x] = min(int(c.tone[y, x]), 2)
    leaf_masses(c, clumps, rng, crown, back, before=wood_layer)
    return finish(c)


def bare(c, trunk, roots, branches, P, L, s, rng, kind):
    """Winter: the same tree without leaves: the trunk tapers on up, branches fork into twigs, snow
    lies along their tops."""
    twigs = np.zeros_like(trunk)
    # the trunk's top continues, and each main branch forks twice
    limbs = [((80, 112), (78, 60), 8, 2), ((50, 132), (30, 92), 6, 3), ((50, 132), (58, 84), 5, -2),
             ((110, 124), (130, 86), 6, -3), ((110, 124), (98, 70), 5, 2), ((78, 60), (60, 30), 4, 2),
             ((78, 60), (96, 34), 4, -2), ((30, 92), (18, 70), 3, 1), ((130, 86), (142, 66), 3, -1),
             ((58, 84), (48, 56), 3, 1), ((98, 70), (112, 46), 3, -1)]
    for root, tip, w, bend in limbs:
        twigs |= L(root, tip, max(w, 3.4 / max(s, 0.4)), bend, 1.5 / max(s, 0.4))  # round 6: tapering tips
    for _ in range(int(18 * s) + 4):  # fine twigs off the limbs
        r = limbs[rng.randrange(len(limbs))]
        t = rng.uniform(0.4, 1.0)
        bx = r[0][0] + (r[1][0] - r[0][0]) * t
        by = r[0][1] + (r[1][1] - r[0][1]) * t
        ang = rng.uniform(-2.6, -0.5)
        ln = rng.uniform(8, 18)
        twigs |= L((bx, by), (bx + math.cos(ang) * ln * rng.choice((-1, 1)), by + math.sin(ang) * ln), max(3.4, 4.2 * s), 0.5, 1.2)
    wood = trunk | roots | branches | twigs
    c.fill(wood, "bark")
    c.shade_part(wood, tones=(1, 2, 3, 4, 5), light=(-0.8, -0.3, 0.5), norm=True)
    bark_texture(c, trunk, period=max(3, int(5 * s + 0.5)))
    snow_caps(c, ("bark",), depth=(2, 2), seed=7, min_thick=5)
    return finish(c, loose=("bark", "snow"))


def pine(season, frame):
    rng = random.Random(5)
    W, H = 96, 200
    c = canvas(W, H, season)
    G = H - 3
    trunk = c.m_poly([(42, G), (44, 146), (52, 146), (54, G)])
    flare = lock(c, (44, G - 5), (33, G + 1), 7, -1.5, 2) | lock(c, (52, G - 5), (63, G + 1), 7, 1.5, 2)
    c.fill(trunk | flare, "bark")
    c.shade_part(trunk | flare, tones=(1, 2, 3, 4, 5), light=(-0.8, -0.3, 0.5), norm=True)
    bark_texture(c, trunk, period=4)
    tiers = [(18, 9, 0, 0.0), (40, 17, 1, 0.1), (64, 24, -1, -0.1), (90, 31, 2, 0.15), (118, 38, -1, -0.05),
             (148, 44, 1, 0.1)]
    whole = c.m_poly([(48, 3), (95, 154), (1, 154)])
    prev = None
    sway = SWAY[frame]
    for i, (yb, hw, off, skew) in enumerate(tiers):
        cxi = 48 + off + round(sway * (1 - i / 5))  # the top sways, the lowest tier stays
        yt = 3 if i == 0 else tiers[i - 1][0] - 9
        pts = [(cxi + skew * 10, yt)]
        if i:
            pts.append((cxi + hw * 0.5, yb - 11))
        n = max(4, hw // 4)
        for k in range(n + 1):
            x = cxi + hw - 2 * hw * k / n
            dip = rng.choice((2, 3, 4)) if k % 2 == 0 else rng.choice((-1, 0))
            pts.append((x, yb + dip + (1 - abs(x - cxi) / hw) * 3))
        if i:
            pts.append((cxi - hw * 0.55, yb - 11))
        m = c.m_poly(pts)
        c.fill(m, "pine")
        c.shade_part(m, tones=(1, 2, 3, 4, 5, 6), global_mask=whole, gmix=0.4, light=(-0.7, -0.5, 0.5), norm=True)
        if prev is not None:
            sh = np.zeros_like(m)
            sh[3:, :] = prev[:-3, :]
            sh &= m & ~prev
            for y, x in zip(*np.nonzero(sh)):
                c.tone[y, x] = max(1, int(c.tone[y, x]) - 2)
        prev = m if prev is None else (prev | m)
    k = c.mid("pine")
    for y in range(2, H - 3):
        for x in range(2, W - 3):
            if c.mat[y, x] != k or hsh(x, y, 7) % 23:
                continue
            t = int(c.tone[y, x])
            lit = t >= 4
            for dx, dy in ([(0, 0), (1, 0), (1, 1), (2, 1)] if lit else [(0, 0), (-1, 0), (-1, 1), (-2, 1)]):
                if c.mat[y + dy, x + dx] == k:
                    c.tone[y + dy, x + dx] = min(6, t + 1) if lit else max(1, t - 1)
    if season == "winter":
        snow_caps(c, ("pine",), depth=(2, 5), seed=3)
    return finish(c, loose=())


# ------------------------------------------------------------------ props

def blade(c, x0, G, h, lean, mat="grass", tones=(3, 4, 5, 6), width=1.5):
    m = c.m_poly([(x0 - width, G), (x0 + lean, G - h), (x0 + width, G)])
    c.fill(m, mat)
    for y, x in zip(*np.nonzero(m)):
        f = (G - y) / h
        c.tone[y, x] = tones[min(len(tones) - 1, int(f * len(tones)))] - (1 if x > x0 + lean * f else 0)
    return m


def grass_prop(season, frame, kind):
    """tuft 32x24, tallgrass 40x40. Winter: dry straw (the winter grass ramp). Sway: lean +1."""
    W, H, blades_ = {"tuft": (32, 24, [(-9, 12, -3), (-6, 17, -2), (-3, 20, -1), (0, 15, 1), (2, 21, 2), (5, 16, 3),
                                         (8, 11, 4), (-1, 9, 0)]),
                     "tallgrass": (40, 40, [(-12, 18, -4), (-8, 30, -3), (-4, 36, -1), (-1, 26, 0), (2, 37, 2),
                                            (5, 31, 3), (9, 24, 4), (12, 16, 5), (0, 14, 1)])}[kind]
    c = canvas(W, H, season)
    G = H - 2
    for bx, h, lean in blades_:
        blade(c, W // 2 + bx, G, h, lean + (frame if h > 14 else 0))
    if kind == "tallgrass":  # seed heads on the tallest blades
        for bx, h, lean in blades_:
            if h >= 30:
                x, y = W // 2 + bx + lean + frame, G - h
                for d in range(4):
                    c.put(int(x), int(y + d), "grass", 6 if d < 2 else 5)
                    c.put(int(x) + 1, int(y + d), "grass", 5)
    despeckle(c)
    c.outline()
    c.tone[(c.mat == c.mid("grass")) & (c.tone == 0)] = 1  # grass sits IN the grass: a soft edge
    return c


def flowers(season, frame, scheme):
    """Flowers on curved stems with 2-3 leaves; scheme mix / white / yellow. Winter: dry seed heads."""
    W, H = 48, 32
    c = canvas(W, H, season)
    G = H - 1
    cols = {"mix": ("pink", "white", "yellow", "yellow", "pink", "white"),
            "white": ("white",) * 6, "yellow": ("yellow",) * 6}[scheme]
    heads = [(10, 12, 1.5), (20, 7, -1.0), (31, 11, 1.0), (16, 19, -0.5), (27, 20, 0.8), (38, 17, -1.2)]
    if season == "winter":  # round 5: each set its own number and height of stems
        heads = {"mix": heads, "white": [(12, 5, 1.0), (24, 3, -0.6), (34, 8, 0.8), (40, 14, -1.0)],
                 "yellow": [(9, 17, 0.6), (17, 15, -0.4), (25, 18, 0.5), (33, 16, -0.6), (40, 19, 0.4)]}[scheme]
        cols = cols[: len(heads)]
    for i, ((fx, fy, bend), col) in enumerate(zip(heads, cols)):
        fx = fx + frame * (1 if fy < 15 else 0)
        base_x = fx - bend * 2 - frame * (1 if fy < 15 else 0)
        pts = [(base_x + (fx - base_x) * k / 8 + bend * 1.2 * math.sin(math.pi * k / 8), G - (G - fy - 2) * k / 8)
               for k in range(9)]
        stem = c.m_line(pts, 2.0 if i % 2 else 1.7)
        c.fill(stem, "grass", 3)
        for j, (t, side) in enumerate(((0.25, -1), (0.5, 1), (0.7, -1))[: 2 + i % 2]):
            sx = base_x + (fx - base_x) * t
            sy = G - (G - fy - 2) * t
            c.fill(lock(c, (sx, sy), (sx + side * 5, sy - 3), 3.2, -side * 0.6, 0.4), "grass", 4 if side < 0 else 3)
        hd = c.m_ellipse(fx + 0.5, fy + 0.5, 2.6, 2.4)
        if season == "winter":
            dry_head(c, fx, fy, scheme, i)
            continue
        c.fill(hd, col)
        c.shade_part(hd, tones=(4, 5, 5, 6), norm=True)
        ccol = "yellow" if col != "yellow" else "wood"
        c.fill(c.m_rect(int(fx), int(fy), int(fx) + 1, int(fy) + 1), ccol, 4 if col != "yellow" else 2)
    despeckle(c, loose=("grass",))
    c.outline()
    c.shadow_band()
    return c


def dry_head(c, fx, fy, scheme, i):
    """Round 5: the 3 winter flower sets are different dead heads (no round balls).
    mix: wilted heads hanging down from a bent tip (2-3 limp petals); white: seed clusters (3 small
    2 x 2 seeds in a spray); yellow: flat dried umbels (a 6 x 2 cap of seeds on short rays)."""
    x, y = int(fx), int(fy)
    if scheme == "mix":
        for dx, dy, t in ((0, 0, 4), (1, 0, 3), (1, 1, 4), (2, 1, 3), (1, 2, 2), (2, 2, 2), (2, 3, 3), (3, 3, 2)):
            c.put(x + dx, y + dy, "grass", t)
    elif scheme == "white":
        for (dx, dy) in ((-2, -1), (1, -2), (2, 1)):
            c.fill(c.m_rect(x + dx, y + dy, x + dx + 1, y + dy + 1), "grass", 5)
            c.put(x + dx + 1, y + dy + 1, "grass", 3)
            c.put(x + dx // 2, y + dy // 2 + 1, "grass", 3)
    else:
        for dx in range(-3, 3):
            c.put(x + dx, y + 1 + (abs(dx) > 2), "grass", 3)
        c.fill(c.m_rect(x - 3, y - 1, x + 2, y), "grass", 5)
        for dx in (-3, -1, 1):
            c.put(x + dx, y - 1, "grass", 6)


def bush(season, frame, berries):
    rng = random.Random(21 if berries else 22)
    c = canvas(64, 48, season)
    clumps = [(24, 22, 14, 11), (42, 20, 13, 10), (16, 33, 12, 9), (46, 33, 13, 9), (31, 34, 15, 10)]
    if season == "winter":  # round 5: a mound of tangled branches under a blanket of snow (no fan)
        return winter_mound(c, rng, WINTER_LUMPS[berries], berries=berries)
    clumps = [(x + (SWAY[frame] if y < 26 else 0), y, rx, ry) for x, y, rx, ry in clumps]
    whole = c.m_ellipse(32, 29, 30, 18)
    back = np.zeros((48, 64), bool)
    for (cx_, cy_, rx_, ry_) in clumps:
        back |= c.m_ellipse(cx_, cy_ + 1, rx_ + 3, ry_ + 3)
    back &= c.m_ellipse(32, 30, 30, 17)
    leaf_masses(c, clumps, rng, whole, back)
    if berries and season == "summer":
        for bx, by in ((20, 20), (40, 17), (47, 31), (27, 34), (36, 28), (13, 31)):
            c.fill(c.m_ellipse(bx, by, 2.0, 2.0), "berry")
            c.shade_part(c.m_ellipse(bx, by, 2.0, 2.0), tones=(2, 3, 4, 5), norm=True)
            c.put(bx - 1, by - 1, "berry", 6)
    return finish(c, keep=("berry",))


def shrub(season, frame):
    """A young round shrub (32 x 32): 3 masses."""
    rng = random.Random(31)
    c = canvas(32, 32, season)
    if season == "winter":
        return bush_small_winter(c, rng)
    clumps = [(12, 15, 8, 7), (21, 13, 8, 7), (16, 21, 10, 7)]
    clumps = [(x + (SWAY[frame] if y < 16 else 0), y, rx, ry) for x, y, rx, ry in clumps]
    whole = c.m_ellipse(16, 18, 15, 12)
    back = np.zeros((32, 32), bool)
    for (cx_, cy_, rx_, ry_) in clumps:
        back |= c.m_ellipse(cx_, cy_ + 1, rx_ + 2, ry_ + 2)
    back &= c.m_ellipse(16, 18, 15, 12)
    leaf_masses(c, clumps, rng, whole, back)
    return finish(c)


def bush_small_winter(c, rng):
    return winter_mound(c, rng, [(16, 21, 8, 7), (10, 24, 6, 5), (22, 23, 6, 6)], twigs=6)


WINTER_LUMPS = {  # round 6: each bush its own outline (lumps of different sizes, not one ellipse)
    False: [(22, 30, 14, 11), (38, 32, 13, 9), (12, 36, 9, 7), (50, 37, 9, 6), (30, 37, 15, 8)],   # low, wide
    True: [(28, 24, 12, 13), (18, 32, 10, 9), (40, 30, 11, 11), (31, 37, 14, 8)],                  # tall, to the left
}


def winter_mound(c, rng, lumps, berries=False, twigs=10):
    """A leafless bush in winter (round 6): its outline is a cluster of lumps of different sizes;
    inside, crossing branches on a dark tangle; snow lies on each lump's top (a wavy edge, a lit top,
    a blue lip); a few branch tips stick out ABOVE the snow (tapering, no snow on them); a few red
    berries left on the berry bush."""
    H, W = c.h, c.w
    mound = np.zeros((H, W), bool)
    for (x, y, rx, ry) in lumps:
        mound |= c.m_ellipse(x, y, rx, ry)
    base = max(y + ry * 0.75 for (x, y, rx, ry) in lumps)
    mound &= c.m_rect(0, 0, W - 1, int(base))
    cx = sum(l[0] for l in lumps) / len(lumps)
    c.fill(mound, "bark", 1)
    for i in range(len(lumps) * 4):  # branches rising from the base across the lumps
        x0 = cx + rng.uniform(-10, 10)
        tx, ty = lumps[i % len(lumps)][0] + rng.uniform(-4, 4), lumps[i % len(lumps)][1] - rng.uniform(0, 6)
        br = lock(c, (x0, base - 1), (tx, ty), 3.2, rng.uniform(-2, 2), 1.6) & mound
        c.fill(br, "bark", 3)
    k = c.mid("bark")
    for y, x in zip(*np.nonzero(c.mat == k)):
        if c.tone[y, x] == 3:
            c.tone[y, x] = 4 if x < cx - 6 else (2 if x > cx + 8 else 3)
    snow = np.zeros((H, W), bool)
    lip = np.zeros((H, W), bool)
    yy, xx = np.mgrid[0:H, 0:W]
    for j, (x, y, rx, ry) in enumerate(lumps):
        lump = c.m_ellipse(x, y, rx, ry) & mound
        edge = y - ry * 0.15 + 1.6 * np.sin((xx - x) * 0.6 + j) + 0.8 * np.sin((xx - x) * 1.3 + 2 * j)
        snow |= lump & (yy < edge)
        lip |= lump & (yy >= edge) & (yy < edge + 2)
    c.fill(lip & ~snow, "snow", 2)
    c.fill(snow, "snow")
    c.shade_part(snow, tones=(4, 5, 6), norm=True)
    for i in range(twigs):  # tips sticking out above the snow
        (x, y, rx, ry) = lumps[i % len(lumps)]
        a = -math.pi / 2 + rng.uniform(-0.7, 0.7)
        x0, y0 = x + rng.uniform(-rx * 0.5, rx * 0.5), y - ry * 0.6
        ln = rng.uniform(8, 13)
        tip = lock(c, (x0, y0 + 3), (x0 + math.cos(a) * ln, y0 + math.sin(a) * ln), 2.4, rng.uniform(-1.5, 1.5), 0.8)
        c.fill(tip & ~snow, "bark", 3)
    if berries:
        for (bx, by) in ((cx - 9, base - 9), (cx + 6, base - 7), (cx - 1, base - 5)):
            c.fill(c.m_ellipse(bx, by, 1.8, 1.8), "berry", 3)
            c.put(int(bx) - 1, int(by) - 1, "berry", 5)
    return finish(c, keep=("berry",), loose=("bark", "snow"))


def stump(season, frame):
    c = canvas(48, 40, season)
    G = 38
    side = c.m_poly([(8, 14), (40, 14), (41, G - 3), (44, G), (4, G), (7, G - 3)])
    roots = c.m_poly([(1, G), (8, G - 5), (12, G)]) | c.m_poly([(36, G), (40, G - 5), (47, G)])
    c.fill(side | roots, "bark")
    c.shade_part(side | roots, tones=(1, 2, 3, 4, 5), light=(-0.9, -0.2, 0.4), norm=True)
    bark_texture(c, side & c.m_rect(0, 16, 47, G - 2), period=4)
    for y, x in zip(*np.nonzero(side)):
        if x > 34:
            c.tone[y, x] = max(1, int(c.tone[y, x]) - 1)
    top = c.m_ellipse(24, 14, 16.5, 6.5)
    c.fill(top, "wood")
    for y, x in zip(*np.nonzero(top)):
        r = math.hypot((x + 0.5 - 23) / 16.5, (y + 0.5 - 14) / 6.5)
        t = 4 if int(r * 5) % 2 == 0 else 3
        if r > 0.86:
            t = 2
        if x < 20 and y < 13 and t >= 3:
            t += 1
        c.tone[y, x] = t
    for y in range(11, 19):
        c.put(30 + (y % 2), y, "wood", 1)
        c.put(31 + (y % 2), y, "wood", 2)
    moss = (c.m_ellipse(11, 16, 6, 4) | c.m_ellipse(8, 24, 4, 7)) & (side | top)
    c.fill(moss, "moss")
    c.shade_part(moss, tones=(3, 4, 5, 6), norm=True)
    if season == "winter":
        snow = c.m_ellipse(24, 13, 15.5, 5.5)
        c.fill(snow, "snow")
        c.shade_part(snow, tones=(4, 5, 6), norm=True)
    return finish(c, loose=())


def rock(season, frame, size):
    """rock_s 32x24, rock_m 48x36: a faceted stone, lit top-left face, lichen; winter snow cap."""
    W, H = {"rock_s": (32, 24), "rock_m": (48, 36)}[size]
    c = canvas(W, H, season)
    rng = random.Random(len(size) * 7)
    G = H - 2
    cx = W / 2
    pts = [(2, G), (W * 0.12, G - H * 0.45), (W * 0.32, G - H * 0.78), (W * 0.6, G - H * 0.85),
           (W * 0.86, G - H * 0.55), (W - 2, G)]
    m = c.m_poly(pts)
    c.fill(m, "stone", 3)
    # facets: the top-left plane lit, the front base, the right in shade
    for y, x in zip(*np.nonzero(m)):
        u = (x - cx) / (W / 2)
        v = (G - y) / H
        t = 3
        if v > 0.45 and u < 0.2:
            t = 5 if u < -0.2 else 4
        elif u > 0.35:
            t = 2
        if v < 0.12:
            t = min(t, 2)
        c.tone[y, x] = t
    crack = c.m_line([(cx + 2, G - H * 0.7), (cx + 4, G - H * 0.45), (cx + 1, G - H * 0.2)], 1.2) & m
    c.set_tone(crack, 1)
    if season != "winter":
        lich = (c.m_ellipse(W * 0.3, G - H * 0.35, W * 0.09, H * 0.08) | c.m_ellipse(W * 0.62, G - H * 0.2, W * 0.07, H * 0.06)) & m
        c.fill(lich, "moss")
        c.shade_part(lich, tones=(3, 4, 5), norm=True)
    else:
        snow_caps(c, ("stone",), depth=(2, 4), seed=size == "rock_m")
    del rng
    return finish(c, loose=())


def pebbles(season, frame):
    c = canvas(40, 20, season)
    for (x, y, rx, ry) in ((8, 13, 5, 3.5), (18, 10, 4, 3), (27, 14, 6, 4), (35, 9, 3, 2.5), (14, 16, 3, 2)):
        m = c.m_ellipse(x, y, rx, ry)
        c.fill(m, "stone")
        c.shade_part(m, tones=(2, 3, 4, 5), norm=True)
    if season == "winter":
        snow_caps(c, ("stone",), depth=(2, 2), seed=9)
    return finish(c, loose=("stone", "snow"))


def log(season, frame):
    """A fallen log 64 x 28: bark side, the cut end with rings, moss on the lit top, a broken branch."""
    c = canvas(64, 28, season)
    body = c.m_poly([(8, 8), (56, 6), (58, 22), (10, 24)])
    c.fill(body, "bark")
    c.shade_part(body, tones=(1, 2, 3, 4, 5), light=(-0.3, -0.9, 0.4), norm=True)
    for y, x in zip(*np.nonzero(body)):  # bark runs along the log
        u = (y + int(2 * math.sin(x * 0.2))) % 5
        if u == 0:
            c.tone[y, x] = max(1, int(c.tone[y, x]) - 2)
    end = c.m_ellipse(9, 16, 5, 8.5)
    c.fill(end, "wood")
    for y, x in zip(*np.nonzero(end)):
        r = math.hypot((x + 0.5 - 9) / 5, (y + 0.5 - 16) / 8.5)
        c.tone[y, x] = 2 if r > 0.85 else (4 if int(r * 4) % 2 == 0 else 3)
    br = lock(c, (40, 8), (46, 1), 4, 1, 2)
    c.fill(br & (c.mat == 0), "bark", 3)
    if season == "winter":
        snow_caps(c, ("bark",), depth=(2, 3), seed=11)
    else:
        moss = c.m_ellipse(30, 8, 12, 2.6) & body
        c.fill(moss, "moss")
        c.shade_part(moss, tones=(3, 4, 5, 6), norm=True)
    return finish(c, loose=())


def mushrooms(season, frame):
    """3 brown caps (32 x 24); winter: snow-capped."""
    c = canvas(32, 24, season)
    for (x, y, r, h) in ((9, 14, 5, 8), (19, 10, 6.5, 12), (26, 16, 3.5, 6)):
        stem = c.m_rect(int(x - 1), int(y), int(x + 1), 22)
        c.fill(stem, "white", 3)
        c.fill(c.m_rect(int(x + 1), int(y), int(x + 1), 22), "white", 1)
        cap = c.m_ellipse(x, y, r, r * 0.62) & c.m_rect(0, 0, 31, int(y + 1))
        c.fill(cap, "wood")
        c.shade_part(cap, tones=(2, 3, 4, 5), norm=True)
        for dx in (-r * 0.4, r * 0.2):
            c.put(int(x + dx), int(y - r * 0.3), "white", 5)
            c.put(int(x + dx) + 1, int(y - r * 0.3), "white", 4)
    if season == "winter":
        snow_caps(c, ("wood",), depth=(2, 3), seed=12)
    return finish(c, loose=("wood", "white", "snow"))


def clover(season, frame):
    """A low clover patch 40 x 20 (3-leaf clusters of 2 x 2 leaflets), a white bloom in summer."""
    c = canvas(40, 20, season)
    rng = random.Random(41)
    for _ in range(9):
        x, y = rng.randint(4, 32), rng.randint(5, 14)
        for dx, dy, t in ((0, 0, 5), (3, 0, 4), (1, 2, 3)):
            c.fill(c.m_rect(x + dx, y + dy, x + dx + 1, y + dy + 1), "grass", t)
    if season == "summer":
        for (x, y) in ((12, 5), (27, 8)):
            c.fill(c.m_ellipse(x, y, 2.2, 2.0), "white", 5)
            c.put(x, y, "white", 3)
    if season == "winter":
        snow_caps(c, ("grass",), depth=(1, 1), seed=13)
    despeckle(c)
    c.outline()
    c.tone[(c.mat == c.mid("grass")) & (c.tone == 0)] = 1
    return c


PROPS = {  # kind: (function, frames)
    "tuft": (lambda s, f: grass_prop(s, f, "tuft"), 2),
    "tallgrass": (lambda s, f: grass_prop(s, f, "tallgrass"), 2),
    "flowers_mix": (lambda s, f: flowers(s, f, "mix"), 2),
    "flowers_white": (lambda s, f: flowers(s, f, "white"), 2),
    "flowers_yellow": (lambda s, f: flowers(s, f, "yellow"), 2),
    "bush_berry": (lambda s, f: bush(s, f, True), 1),
    "bush": (lambda s, f: bush(s, f, False), 1),
    "shrub": (shrub, 1),
    "stump": (stump, 1),
    "rock_s": (lambda s, f: rock(s, f, "rock_s"), 1),
    "rock_m": (lambda s, f: rock(s, f, "rock_m"), 1),
    "pebbles": (pebbles, 1),
    "log": (log, 1),
    "mushrooms": (mushrooms, 1),
    "clover": (clover, 1),
}
TREES = {"oak_l": lambda s, f: broadleaf("oak_l", s, f), "oak_m": lambda s, f: broadleaf("oak_m", s, f),
         "sapling": lambda s, f: broadleaf("sapling", s, f), "pine": pine}


def write(season):
    pre = PREFIX[season]
    out = []
    for kind, fn in TREES.items():
        frames = 1 if (season == "winter" and kind != "pine") else 3
        for f in range(frames):
            out.append(save(clean_isolated(fn(season, f).image()), os.path.join(OUT, f"{pre}plains.tree.v3.{kind}.{f}.png")))
    for kind, (fn, frames) in PROPS.items():
        for f in range(frames):
            out.append(save(clean_isolated(fn(season, f).image()), os.path.join(OUT, f"{pre}plains.prop.v3.{kind}.{f}.png")))
    return out


def main(which):
    seasons = list(PREFIX) if which == "all" else [which]
    n = sum(len(write(s)) for s in seasons)
    print(f"{n} files")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "summer")
