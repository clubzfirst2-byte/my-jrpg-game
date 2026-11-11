"""v3 pilot (round 2): trees, plants/props and grass ground at density 4 (STYLE.md 6, 7).

  terrain/obj.v3.oak.png          160 x 224  broadleaf, large (game 40 x 56: 2 x the hero's height)
  terrain/obj.v3.pine.png          96 x 200  pine, medium (game 24 x 50)
  terrain/prop.v3.tuft.png         32 x 24   grass tuft
  terrain/prop.v3.flowers.png      48 x 32   flowers on their own stems (pink / white / yellow)
  terrain/prop.v3.bush.png         64 x 48   bush with berries
  terrain/prop.v3.stump.png        48 x 40   mossy stump
  terrain/plains.grass.v3.<m><r><c>.png  64 x 64  summer plains ground: 4 macro patterns m = a, b, c, d
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

from v3lib import ROOT, Canvas, despeckle, lift_ramp, save  # noqa: E402

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

def oak():
    rng = random.Random(11)
    W, H = 160, 224
    c = Canvas(W, H, RAMPS)
    G = H - 3
    # trunk with root flare, forking into 3 branches that enter the crown
    trunk = c.m_poly([(70, G), (63, G - 3), (71, G - 12), (72, 160), (76, 148), (86, 148), (90, 160),
                      (89, G - 12), (97, G - 3), (90, G)])
    roots = c.m_poly([(54, G), (65, G - 7), (73, G - 2)]) | c.m_poly([(87, G - 2), (95, G - 7), (106, G)])
    branches = (c.m_line([(76, 152), (66, 136), (54, 122)], 5.5) | c.m_line([(85, 152), (95, 134), (108, 118)], 5.0)
                | c.m_line([(80, 150), (82, 132), (80, 116)], 4.5))
    wood = trunk | roots | branches
    c.fill(wood, "bark")
    c.shade_part(wood, tones=(1, 2, 3, 4, 5), light=(-0.8, -0.3, 0.5), norm=True)
    bark_texture(c, trunk)
    # crown: clumps on a rounded crown, no two shade pockets at the same height
    clumps = []
    cx, cy = 80, 76
    for ring, (r, n, sz) in enumerate([(0, 1, 24), (28, 6, 21), (49, 11, 18)]):
        for k in range(n):
            a = 2 * math.pi * k / n + ring * 0.55 + rng.uniform(-0.22, 0.22)
            x = cx + math.cos(a) * r * 1.10 + rng.uniform(-3, 3)
            y = cy + math.sin(a) * r * 0.84 + rng.uniform(-3, 3)
            if y > 116:
                continue
            s = sz + rng.uniform(-4, 4)
            clumps.append((x, y, s, s * rng.uniform(0.74, 0.9)))
    crown = c.m_ellipse(cx, cy - 2, 70, 60)
    foliage(c, "leaf", clumps, rng, crown_mask=crown, gmix=0.55, seed=3)
    # small clumps over the branches' ends (the branches disappear into the leaves)
    tips = [(52, 118, 10, 8), (110, 114, 10, 8), (79, 112, 9, 7)]
    tm = foliage(c, "leaf", tips, rng, crown_mask=crown, gmix=0.6, seed=4)
    del tm
    # the crown's shade on the trunk top (uneven, follows the crown's lower edge)
    for y, x in zip(*np.nonzero(c.mat == c.mid("bark"))):
        if y < 150 + (hsh(x, 0, 5) % 4):
            c.tone[y, x] = min(int(c.tone[y, x]), 2)
    despeckle(c)
    c.outline()
    c.shadow_band()
    return c


def pine():
    rng = random.Random(5)
    W, H = 96, 200
    c = Canvas(W, H, RAMPS)
    G = H - 3
    trunk = c.m_poly([(43, G), (45, 128), (51, 128), (53, G)])
    flare = c.m_poly([(34, G), (44, G - 8), (48, G)]) | c.m_poly([(48, G), (52, G - 8), (62, G)])
    c.fill(trunk | flare, "bark")
    c.shade_part(trunk | flare, tones=(1, 2, 3, 4, 5), light=(-0.8, -0.3, 0.5), norm=True)
    bark_texture(c, trunk, period=4)
    # tiers: (bottom y, half width, centre offset, skew); each different (no stamped triangles)
    tiers = [(16, 9, 0, 0.0), (36, 17, 1, 0.1), (57, 24, -1, -0.1), (80, 31, 2, 0.15), (104, 38, -1, -0.05),
             (130, 44, 1, 0.1)]
    whole = c.m_poly([(48, 3), (95, 136), (1, 136)])
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

def blades(c, x0, G, h, lean, mat="grass", tones=(2, 3, 4, 5)):
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
    return c


def flowers():
    """Flowers on their own stems among a few leaf blades: no green base."""
    c = Canvas(48, 32, RAMPS)
    G = 30
    for bx, h, lean in [(-15, 8, -3), (-9, 11, -2), (-2, 9, 1), (6, 12, 2), (13, 9, 3), (17, 7, 4)]:
        blades(c, 24 + bx, G, h, lean)
    for (fx, fy, col, s) in [(12, 13, "pink", 3.2), (24, 8, "white", 3.4), (35, 14, "yellow", 3.0),
                             (19, 19, "yellow", 2.6), (30, 20, "pink", 2.8), (40, 21, "white", 2.4)]:
        for y in range(int(fy + s), G):  # stem, 2 wide
            c.put(int(fx), y, "grass", 3)
            c.put(int(fx) + 1, y, "grass", 2)
        # the head: 4 petals of 2 x 2 round a 2 x 2 centre (lit petal on top, shaded ones right/below)
        x0, y0 = int(fx) - 2, int(fy) - 2
        for dx, dy, t in ((2, 0, 5), (0, 2, 4), (4, 2, 3), (2, 4, 3)):
            c.fill(c.m_rect(x0 + dx, y0 + dy, x0 + dx + 1, y0 + dy + 1), col, t)
        ccol = "yellow" if col != "yellow" else "wood"
        c.fill(c.m_rect(x0 + 2, y0 + 2, x0 + 3, y0 + 3), ccol, 4 if col != "yellow" else 2)
    despeckle(c)
    c.outline()
    c.shadow_band()
    return c


def bush():
    rng = random.Random(21)
    c = Canvas(64, 48, RAMPS)
    clumps = [(32, 22, 15, 12), (18, 30, 12, 10), (46, 30, 12, 10), (24, 36, 12, 8), (40, 37, 12, 8),
              (32, 33, 13, 10)]
    whole = c.m_ellipse(32, 30, 30, 17)
    foliage(c, "leaf", clumps, rng, crown_mask=whole, gmix=0.5, scallop=1.8, seed=8)
    for bx, by in ((22, 26), (40, 22), (46, 34), (28, 38), (36, 30), (16, 34)):
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


# ------------------------------------------------------------------ ground

def periodic_noise(n, seed, octaves=((1, 1.0), (2, 0.5), (4, 0.25))):
    """Smooth noise that tiles every n texels (sum of sines with whole periods)."""
    rng = random.Random(seed)
    yy, xx = np.mgrid[0:n, 0:n] / n * 2 * math.pi
    v = np.zeros((n, n))
    for f, a in octaves:
        for _ in range(3):
            kx, ky = rng.randint(-f, f), rng.randint(-f, f)
            if kx == 0 and ky == 0:
                kx = f
            v += a * np.sin(kx * xx + ky * yy + rng.uniform(0, 6.28))
    v -= v.min()
    return v / v.max()


def blob(n, cx, cy, rx, ry, seed):
    """An irregular patch: an ellipse whose radius wobbles with the angle."""
    rng = random.Random(seed)
    ph = [rng.uniform(0, 6.28) for _ in range(4)]
    yy, xx = np.mgrid[0:n, 0:n]
    a = np.arctan2(yy + 0.5 - cy, xx + 0.5 - cx)
    k = 1 + 0.22 * np.sin(2 * a + ph[0]) + 0.15 * np.sin(3 * a + ph[1]) + 0.08 * np.sin(5 * a + ph[2])
    d = np.hypot((xx + 0.5 - cx) / rx, (yy + 0.5 - cy) / ry)
    return d <= k


MACROS = {  # light patches (1-2, each its own shape), seed of the dark patches
    "a": dict(seed=7, light=[(96, 120, 34, 22, 1)]),
    "b": dict(seed=19, light=[(168, 70, 26, 30, 2), (70, 182, 20, 14, 3)]),
    "c": dict(seed=31, light=[(132, 166, 40, 18, 4)]),
    "d": dict(seed=43, light=[(60, 72, 22, 26, 5), (190, 196, 28, 16, 6)]),
}

EDGE = 18  # the calm band along a pattern's outer edge (shared by all patterns)


@functools.lru_cache(maxsize=None)
def macro_of(bx, by):
    """Which pattern a 4 x 4-tile block uses: a hashed order of the 4 patterns per block, taking the
    first that differs from the block on its left and the block above (so two blocks side by side or
    one above the other never repeat, and there is no fixed period). Blocks off the map: none."""
    left = macro_of(bx - 1, by) if bx > 0 else None
    up = macro_of(bx, by - 1) if by > 0 else None
    order = sorted("abcd", key=lambda m: hsh(bx * 7 + ord(m), by * 13 + ord(m), 91))
    for m in order:
        if m != left and m != up:
            return m
    return order[0]


def grass_macro(name, n=256):
    spec = MACROS[name]
    c = Canvas(n, n, RAMPS)
    c.fill(np.ones((n, n), bool), "grass", 3)
    rng = random.Random(spec["seed"] * 7 + 1)
    v = periodic_noise(n, spec["seed"], octaves=((2, 1.0), (3, 0.6), (5, 0.35), (9, 0.18)))
    yy, xx = np.mgrid[0:n, 0:n]
    # fade the patches out toward the outer edge, so every pattern meets every other on base grass
    e = np.minimum(np.minimum(xx, n - 1 - xx), np.minimum(yy, n - 1 - yy))
    win = np.clip((e - 4) / EDGE, 0, 1)
    jit = np.vectorize(lambda x, y: (hsh(x // 2, y // 2, spec["seed"]) % 1000) / 1000.0)(xx, yy) * 0.08 - 0.04
    vd = 0.5 + (v - 0.5) * win + jit * win
    c.tone[:] = np.where(vd < 0.26, 2, 3)
    for (lx, ly, rx, ry, s) in spec["light"]:
        c.tone[blob(n, lx, ly, rx, ry, s * 13 + spec["seed"]) & (win > 0.6)] = 4
    # features, kept off the outer 3 texels (nothing crosses into a neighbouring pattern)
    step = 8
    for gy in range(2, n - 4, step):
        for gx in range(1, n - 6, step):
            x = gx + rng.randint(1, step - 3)
            y = gy + rng.randint(4, step - 1)
            if y > n - 2 or x > n - 3:
                continue
            base = int(c.tone[y, x])
            kind = rng.random()
            if kind < 0.62:  # a tuft: 3 blades, the middle one tallest, a lit 2-texel tip
                for bx, h in ((-1, 3), (0, 5), (1, 4)):
                    for d in range(h):
                        c.tone[y - d, x + bx] = min(5, base + 1) if d >= h - 2 else base
                c.tone[y - 5, x] = 6 if base >= 3 and rng.random() < 0.4 else min(5, base + 2)
                c.tone[y - 4, x] = min(5, base + 2)
                c.tone[y + 1, x - 1:x + 2] = max(1, base - 1)  # its root shade, 3 wide
            elif kind < 0.74:  # a darker sprig, 2 wide
                for d in range(4):
                    c.tone[y - d, x + d // 2:x + d // 2 + 2] = max(1, base - 1)
    # clover clumps (3 leaflets of 2 x 2), pebbles (3 x 2 with a light), flowers (3 x 3, a centre)
    for _ in range(5):
        x, y = rng.randint(8, n - 12), rng.randint(8, n - 12)
        for dx, dy in ((0, 0), (3, 0), (1, 2)):
            c.tone[y + dy:y + dy + 2, x + dx:x + dx + 2] = 5
        c.tone[y + 4, x + 1:x + 3] = 2
    for _ in range(4):
        x, y = rng.randint(8, n - 12), rng.randint(8, n - 12)
        for dx in range(3):
            c.dot(x + dx, y, STONE[5] if dx == 0 else STONE[4])
            c.dot(x + dx, y + 1, STONE[3] if dx < 2 else STONE[2])
        c.tone[y + 2, x:x + 3] = 2
    for _ in range(6):
        x, y = rng.randint(8, n - 12), rng.randint(8, n - 12)
        col = (WHITE, YELLOW, PINK)[rng.randint(0, 2)]
        for dx, dy, t in ((1, 0, 5), (0, 1, 4), (2, 1, 4), (1, 2, 3)):
            c.dot(x + dx, y + dy, col[t])
        c.dot(x + 1, y + 1, YELLOW[3] if col is not YELLOW else WOOD[3])
        c.tone[y + 3, x:x + 3] = 2
    despeckle(c)
    return c


def main():
    items = {
        "obj.v3.oak.png": oak(), "obj.v3.pine.png": pine(), "prop.v3.tuft.png": tuft(),
        "prop.v3.flowers.png": flowers(), "prop.v3.bush.png": bush(), "prop.v3.stump.png": stump(),
    }
    out = [save(c, os.path.join(OUT, k)) for k, c in items.items()]
    for name in MACROS:
        big = grass_macro(name).image()
        for r in range(4):
            for col in range(4):
                out.append(save(big.crop((col * 64, r * 64, col * 64 + 64, r * 64 + 64)),
                                os.path.join(OUT, f"plains.grass.v3.{name}{r}{col}.png")))
    print("\n".join(os.path.relpath(p, ROOT) for p in out))


if __name__ == "__main__":
    main()
