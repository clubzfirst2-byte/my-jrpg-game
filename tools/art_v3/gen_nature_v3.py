"""v3 pilot (round 2): trees, plants/props and grass ground at density 4 (STYLE.md 6, 7).

  terrain/obj.v3.oak.png          160 x 224  broadleaf, large (game 40 x 56: 2 x the hero's height)
  terrain/obj.v3.pine.png          96 x 200  pine, medium (game 24 x 50)
  terrain/prop.v3.tuft.png         32 x 24   grass tuft
  terrain/prop.v3.flowers.png      48 x 32   flowers on their own stems (pink / white / yellow)
  terrain/prop.v3.bush.png         64 x 48   bush with berries
  terrain/prop.v3.stump.png        48 x 40   mossy stump
  (the ground moved to gen_ground_v3.py in round 4)
                                   (256 x 256 each, cut into 4 x 4 tiles r, c). Their outer edges are
                                   the same calm band, so any pattern can sit next to any other: the
                                   game picks one per 4 x 4-tile block (by a hash of the block).

Round 2 (inspection fixes): no near-black outlines (every background ramp lifted to luma >= 36), no
lone texels (despeckle; leaf / needle marks are 2 x 2 or larger), the oak's shade spread in uneven
pockets with branches entering the crown, an uneven pine with needle clusters and a longer trunk, the
stump's moss on the lit side, no green bases under the flowers and the stump, 4 mixed grass patterns
with 2 x 2+ flowers, clover and pebbles.
Run: python3 tools/art_v3/gen_nature_v3.py
"""

import functools
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402

from hdkit import lock  # noqa: E402
from v3lib import ROOT, Canvas, despeckle, erode, lift_ramp, save  # noqa: E402

OUT = os.path.join(ROOT, "src", "art-release-v3", "terrain")

# ramps: 0 outline .. 6 highlight (ground and foliage use 7 tones, STYLE.md 3.2); lifted to luma >= 36
LEAF = lift_ramp(["#0e2216", "#183a24", "#22502c", "#2e6432", "#44783a", "#62944a", "#8cb664"])
PINE = lift_ramp(["#08161a", "#123028", "#173a36", "#1f4a3e", "#2a5a46", "#3a7052", "#5a8e66"])
BARK = lift_ramp(["#1e1008", "#3e2414", "#4e301c", "#5e3a22", "#6e502a", "#86603a", "#a07a50"])
MOSS = lift_ramp(["#0c1c16", "#1e3e24", "#2c5430", "#3e6a36", "#56843e", "#6e9a48", "#90b860"])
WOOD = lift_ramp(["#2a1a0c", "#5a3a1e", "#76502c", "#8e6838", "#a88048", "#c09a60", "#dcbc84"])
PLAINS = lift_ramp(["#16301c", "#2a5030", "#335d3a", "#3c6a38", "#4e773f", "#528446", "#6c9e58"])
PINK = lift_ramp(["#5a2038", "#b0507a", "#c8689e", "#e080a8", "#ea98af", "#f4b0cc", "#ffe0ee"])
WHITE = lift_ramp(["#4a4a5a", "#b4b4c4", "#cbcdd7", "#e2e2ea", "#ebebf1", "#f4f4f8", "#ffffff"])
YELLOW = lift_ramp(["#6a4a10", "#c08a20", "#d8bb30", "#f0c040", "#f4d360", "#f8dc80", "#fff4c0"])
BERRY = lift_ramp(["#3a0a14", "#7a1424", "#9a1c2c", "#c02a36", "#e04a4a", "#f07a6a", "#ffc0b0"])
STONE = lift_ramp(["#1c1a24", "#3a3846", "#474757", "#585668", "#6c677a", "#7a788c", "#9e9cb0"])
RAMPS = dict(leaf=LEAF, pine=PINE, bark=BARK, moss=MOSS, wood=WOOD, grass=PLAINS, pink=PINK, white=WHITE,
             yellow=YELLOW, berry=BERRY, stone=STONE)


# ------------------------------------------------------------------ helpers

def hsh(x, y, s=0):
    """A fixed scatter (not a grid, so no diagonal rows of marks)."""
    h = (x * 374761393 + y * 668265263 + s * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return h ^ (h >> 16)


def bark_texture(c, mask, period=5):
    """Vertical bark plates: wandering grooves (tone -2) with a lit ridge (tone +1) left of each."""
    for y, x in zip(*np.nonzero(mask)):
        w = math.sin(y * 0.21 + (x // period) * 1.7) * 1.2
        u = (x + w) % period
        t = int(c.tone[y, x])
        if u < 1.0:
            c.tone[y, x] = max(1, t - 2)
        elif u < 2.0 and t >= 3:
            c.tone[y, x] = min(6, t + 1)


def scalloped(c, cx, cy, rx, ry, rng, scallop=2.2):
    m = c.m_ellipse(cx, cy, rx, ry)
    n = max(6, int(2 * math.pi * max(rx, ry) / 5))
    for k in range(n):
        a = 2 * math.pi * k / n + rng.uniform(-0.2, 0.2)
        m |= c.m_ellipse(cx + math.cos(a) * rx * 0.92, cy + math.sin(a) * ry * 0.92, scallop, scallop)
    return m


def leaf_marks(c, mat, every=31, seed=0):
    """Leaf marks in 2 x 2 / 3 x 2 clusters: lit leaves on the lit side, dark notches in the shade."""
    k = c.mid(mat)
    for y in range(2, c.h - 3):
        for x in range(2, c.w - 3):
            if c.mat[y, x] != k or hsh(x, y, seed) % every:
                continue
            t = int(c.tone[y, x])
            lit = t >= 4
            pts = [(0, 0), (1, 0), (2, 0), (1, 1), (2, 1)] if lit else [(0, 0), (1, 0), (0, 1), (1, 1)]
            for dx, dy in pts:
                X, Y = x + dx, y + dy
                if c.mat[Y, X] == k:
                    c.tone[Y, X] = min(6, t + 1) if lit else max(1, t - 1)


def foliage(c, mat, clumps, rng, crown_mask=None, gmix=0.5, tones=(1, 2, 3, 4, 5, 6), scallop=2.2, seed=0):
    """clumps: [(cx, cy, rx, ry)], drawn top first so lower clumps overlap the ones above."""
    masks = [scalloped(c, *cl, rng, scallop) for cl in clumps]
    whole = np.zeros((c.h, c.w), bool)
    for m in masks:
        whole |= m
    g = crown_mask if crown_mask is not None else whole
    for i in sorted(range(len(clumps)), key=lambda i: clumps[i][1]):
        c.fill(masks[i], mat)
        c.shade_part(masks[i], tones=tones, global_mask=g, gmix=gmix)
    leaf_marks(c, mat, seed=seed)
    return whole


# ------------------------------------------------------------------ trees

def leaf_masses(c, clumps, rng, crown, back, before=None, mat="leaf"):
    """The broadleaf way (STYLE.md 7.1), shared by trees and bushes: a dark inside behind the masses,
    then each mass with its own clear light and shade faces, leaf marks only along the lit edge, its
    bottom 2 rows in shade."""
    H, W = c.h, c.w
    masks = [scalloped(c, *cl, rng, 2.4) for cl in clumps]
    c.fill(back, mat, 2)
    c.shade_part(back, tones=(1, 1, 2), norm=True)
    if before:
        before()
    k = c.mid(mat)
    for i in sorted(range(len(clumps)), key=lambda i: clumps[i][1]):
        m = masks[i]
        c.fill(m, mat)
        c.shade_part(m, tones=(2, 3, 4, 5, 6), global_mask=crown, gmix=0.3, norm=True)
        inner = m & ~erode(erode(erode(m)))
        for y, x in zip(*np.nonzero(inner)):
            if c.tone[y, x] >= 5 and hsh(x, y, 3) % 5 == 0 and y + 1 < H and x + 2 < W:
                for dx, dy in ((0, 0), (1, 0), (2, 0), (1, 1)):
                    if c.mat[y + dy, x + dx] == k:
                        c.tone[y + dy, x + dx] = 6
        cy_ = clumps[i][1]
        for y, x in zip(*np.nonzero(m)):
            if y > cy_ and ((y + 1 < H and not m[y + 1, x]) or (y + 2 < H and not m[y + 2, x])):
                c.tone[y, x] = 2


def oak():
    """Round 3: 10 big leaf masses, each with a clear lit face and shade face (no sponge texture:
    leaf marks only along the lit edges), the trunk showing for under a quarter of the height,
    tapering branches seen in the gap under the crown, curved roots."""
    rng = random.Random(11)
    W, H = 160, 224
    c = Canvas(W, H, RAMPS)
    G = H - 3
    # the trunk tapers on up INTO the crown (20 -> 12 -> 8 wide), splitting into 2 branches on the way
    trunk = c.m_poly([(70, G), (71, 178), (73, 160), (75, 136), (77, 108), (83, 108), (85, 136), (87, 160),
                      (89, 178), (90, G)])
    roots = (lock(c, (73, G - 6), (56, G + 1), 8, -2, 2) | lock(c, (87, G - 6), (105, G + 1), 8, 2, 2)
             | lock(c, (80, G - 4), (82, G + 1), 6, 0, 3))
    branches = (lock(c, (75, 160), (50, 132), 9, 3, 2.5) | lock(c, (85, 150), (110, 124), 8, -3, 2.0))
    clumps = [(80, 50, 24, 20), (52, 70, 22, 18), (108, 68, 22, 18), (80, 94, 30, 23), (36, 108, 22, 19),
              (124, 106, 22, 19), (32, 148, 18, 16), (128, 150, 18, 16), (55, 152, 23, 21), (105, 154, 23, 21)]
    crown = c.m_ellipse(80, 104, 74, 74)
    back = np.zeros((H, W), bool)
    for (cx_, cy_, rx_, ry_) in clumps:
        back |= c.m_ellipse(cx_, cy_ + 2, rx_ + 6, ry_ + 9)
    back &= c.m_ellipse(80, 108, 70, 64)

    def wood_layer():
        wood = trunk | roots | branches
        c.fill(wood, "bark")
        c.shade_part(wood, tones=(1, 2, 3, 4, 5), light=(-0.8, -0.3, 0.5), norm=True)
        bark_texture(c, trunk)
        for y, x in zip(*np.nonzero(wood)):  # wood inside the crown is in its shade
            if y < 172:
                c.tone[y, x] = min(int(c.tone[y, x]), 2)
    leaf_masses(c, clumps, rng, crown, back, before=wood_layer)
    despeckle(c, loose=("leaf",))
    c.outline()
    c.shadow_band()
    return c


def pine():
    rng = random.Random(5)
    W, H = 96, 200
    c = Canvas(W, H, RAMPS)
    G = H - 3
    trunk = c.m_poly([(42, G), (44, 146), (52, 146), (54, G)])
    flare = lock(c, (44, G - 5), (33, G + 1), 7, -1.5, 2) | lock(c, (52, G - 5), (63, G + 1), 7, 1.5, 2)
    c.fill(trunk | flare, "bark")
    c.shade_part(trunk | flare, tones=(1, 2, 3, 4, 5), light=(-0.8, -0.3, 0.5), norm=True)
    bark_texture(c, trunk, period=4)
    # tiers: (bottom y, half width, centre offset, skew); each different (no stamped triangles)
    tiers = [(18, 9, 0, 0.0), (40, 17, 1, 0.1), (64, 24, -1, -0.1), (90, 31, 2, 0.15), (118, 38, -1, -0.05),
             (148, 44, 1, 0.1)]
    whole = c.m_poly([(48, 3), (95, 154), (1, 154)])
    prev = None
    for i, (yb, hw, off, skew) in enumerate(tiers):
        cxi = 48 + off
        yt = 3 if i == 0 else tiers[i - 1][0] - 9
        pts = [(cxi + skew * 10, yt)]
        if i:
            pts.append((cxi + hw * 0.5, yb - 11))
        n = max(4, hw // 4)
        for k in range(n + 1):  # drooping tips, right to left, uneven
            x = cxi + hw - 2 * hw * k / n
            dip = rng.choice((2, 3, 4)) if k % 2 == 0 else rng.choice((-1, 0))
            sag = (1 - abs(x - cxi) / hw) * 3
            pts.append((x, yb + dip + sag))
        if i:
            pts.append((cxi - hw * 0.55, yb - 11))
        m = c.m_poly(pts)
        c.fill(m, "pine")
        c.shade_part(m, tones=(1, 2, 3, 4, 5, 6), global_mask=whole, gmix=0.4, light=(-0.7, -0.5, 0.5), norm=True)
        # the tier above casts shade under its drooping tips (follows its edge, 3 texels)
        if prev is not None:
            sh = np.zeros_like(m)
            sh[3:, :] = prev[:-3, :]
            sh &= m & ~prev
            for y, x in zip(*np.nonzero(sh)):
                c.tone[y, x] = max(1, int(c.tone[y, x]) - 2)
        prev = m if prev is None else (prev | m)
    # needle clusters: small blobs (3-5 texels) lifted on the lit side, sunk in the shade
    k = c.mid("pine")
    for y in range(2, H - 3):
        for x in range(2, W - 3):
            if c.mat[y, x] != k or hsh(x, y, 7) % 23:
                continue
            t = int(c.tone[y, x])
            lit = t >= 4
            pts = [(0, 0), (1, 0), (1, 1), (2, 1)] if lit else [(0, 0), (-1, 0), (-1, 1), (-2, 1)]
            for dx, dy in pts:
                X, Y = x + dx, y + dy
                if c.mat[Y, X] == k:
                    c.tone[Y, X] = min(6, t + 1) if lit else max(1, t - 1)
    despeckle(c)
    c.outline()
    c.shadow_band()
    return c


# ------------------------------------------------------------------ props

def blades(c, x0, G, h, lean, mat="grass", tones=(3, 4, 5, 6)):
    pts = [(x0 - 1.5, G), (x0 + lean, G - h), (x0 + 1.5, G)]
    m = c.m_poly(pts)
    c.fill(m, mat)
    for y, x in zip(*np.nonzero(m)):
        f = (G - y) / h
        c.tone[y, x] = tones[min(len(tones) - 1, int(f * len(tones)))] - (1 if x > x0 + lean * f else 0)
    return m


def tuft():
    c = Canvas(32, 24, RAMPS)
    G = 22
    for bx, h, lean in [(-9, 12, -3), (-6, 17, -2), (-3, 20, -1), (0, 15, 1), (2, 21, 2), (5, 16, 3), (8, 11, 4),
                        (-1, 9, 0)]:
        blades(c, 16 + bx, G, h, lean)
    despeckle(c)
    c.outline()
    # a soft edge: grass sits IN the grass, so its outline is the grass's tone 1, not tone 0
    k = c.mid("grass")
    c.tone[(c.mat == k) & (c.tone == 0)] = 1
    return c


def flowers():
    """Round 3: each flower on a thin curved stem (1-2 texels) with 2-3 leaves, heads at different
    heights; heads are round (r 2.5) with a 2 x 2 centre. No green base."""
    c = Canvas(48, 32, RAMPS)
    G = 31
    heads = [(10, 12, "pink", 1.5), (20, 7, "white", -1.0), (31, 11, "yellow", 1.0), (16, 19, "yellow", -0.5),
             (27, 20, "pink", 0.8), (38, 17, "white", -1.2)]
    for i, (fx, fy, col, bend) in enumerate(heads):
        base_x = fx - bend * 2
        pts = []
        for k in range(9):
            t = k / 8
            pts.append((base_x + bend * 2 * t + bend * 1.2 * math.sin(math.pi * t), G - (G - fy - 2) * t))
        stem = c.m_line(pts, 2.0 if i % 2 else 1.7)
        c.fill(stem, "grass", 3)
        for y, x in zip(*np.nonzero(stem)):
            if x > base_x + bend * 2 * (G - y) / max(1, G - fy):
                c.tone[y, x] = 2
        for j, (t, side) in enumerate(((0.25, -1), (0.5, 1), (0.7, -1))[: 2 + i % 2]):
            sx = base_x + bend * 2 * t
            sy = G - (G - fy - 2) * t
            leaf = lock(c, (sx, sy), (sx + side * 5, sy - 3), 3.2, -side * 0.6, 0.4)
            c.fill(leaf, "grass", 4 if side < 0 else 3)
        hd = c.m_ellipse(fx + 0.5, fy + 0.5, 2.6, 2.4)
        c.fill(hd, col)
        c.shade_part(hd, tones=(4, 5, 5, 6), norm=True)
        ccol = "yellow" if col != "yellow" else "wood"
        c.fill(c.m_rect(int(fx), int(fy), int(fx) + 1, int(fy) + 1), ccol, 4 if col != "yellow" else 2)
    despeckle(c, loose=("grass",))
    c.outline()
    c.shadow_band()
    return c


def bush():
    """Round 4: drawn the broadleaf way (leaf_masses): 4 masses with light and shade faces."""
    rng = random.Random(21)
    c = Canvas(64, 48, RAMPS)
    clumps = [(24, 22, 14, 11), (42, 20, 13, 10), (16, 33, 12, 9), (46, 33, 13, 9), (31, 34, 15, 10)]
    whole = c.m_ellipse(32, 29, 30, 18)
    back = np.zeros((48, 64), bool)
    for (cx_, cy_, rx_, ry_) in clumps:
        back |= c.m_ellipse(cx_, cy_ + 1, rx_ + 3, ry_ + 3)
    back &= c.m_ellipse(32, 30, 30, 17)
    leaf_masses(c, clumps, rng, whole, back)
    for bx, by in ((20, 20), (40, 17), (47, 31), (27, 34), (36, 28), (13, 31)):
        m = c.m_ellipse(bx, by, 2.0, 2.0)
        c.fill(m, "berry")
        c.shade_part(m, tones=(2, 3, 4, 5), norm=True)
        c.put(bx - 1, by - 1, "berry", 6)
        c.put(bx, by - 1, "berry", 5)
    despeckle(c, keep=("berry",), loose=("leaf",))
    c.outline()
    c.shadow_band()
    return c


def stump():
    c = Canvas(48, 40, RAMPS)
    G = 38
    side = c.m_poly([(8, 14), (40, 14), (41, G - 3), (44, G), (4, G), (7, G - 3)])
    roots = c.m_poly([(1, G), (8, G - 5), (12, G)]) | c.m_poly([(36, G), (40, G - 5), (47, G)])
    c.fill(side | roots, "bark")
    c.shade_part(side | roots, tones=(1, 2, 3, 4, 5), light=(-0.9, -0.2, 0.4), norm=True)
    bark_texture(c, side & c.m_rect(0, 16, 47, G - 2), period=4)
    for y, x in zip(*np.nonzero(side)):  # the right side in shade (bark, not moss)
        if x > 34:
            c.tone[y, x] = max(1, int(c.tone[y, x]) - 1)
    top = c.m_ellipse(24, 14, 16.5, 6.5)
    c.fill(top, "wood")
    for y, x in zip(*np.nonzero(top)):  # growth rings
        r = math.hypot((x + 0.5 - 23) / 16.5, (y + 0.5 - 14) / 6.5)
        t = 4 if int(r * 5) % 2 == 0 else 3
        if r > 0.86:
            t = 2
        if x < 20 and y < 13 and t >= 3:
            t += 1
        c.tone[y, x] = t
    for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
        c.put(23 + dx, 13 + dy, "wood", 1)
    for y in range(11, 19):  # a crack
        c.put(30 + (y % 2), y, "wood", 1)
        c.put(31 + (y % 2), y, "wood", 2)
    # moss on the lit side: the rim's upper left and down the left of the trunk
    moss = (c.m_ellipse(11, 16, 6, 4) | c.m_ellipse(8, 24, 4, 7)) & (side | top)
    c.fill(moss, "moss")
    c.shade_part(moss, tones=(3, 4, 5, 6), norm=True)
    despeckle(c)
    c.outline()
    c.shadow_band()
    return c


def main():
    items = {
        "obj.v3.oak.png": oak(), "obj.v3.pine.png": pine(), "prop.v3.tuft.png": tuft(),
        "prop.v3.flowers.png": flowers(), "prop.v3.bush.png": bush(), "prop.v3.stump.png": stump(),
    }
    out = [save(c, os.path.join(OUT, k)) for k, c in items.items()]
    print("\n".join(os.path.relpath(p, ROOT) for p in out))


if __name__ == "__main__":
    main()
