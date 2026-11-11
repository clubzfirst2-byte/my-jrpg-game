"""v3 pilot (round 2): trees, plants/props and grass ground at density 4 (STYLE.md 6, 7).

  terrain/obj.v3.oak.png          160 x 224  broadleaf, large (game 40 x 56: 2 x the hero's height)
  terrain/obj.v3.pine.png          96 x 200  pine, medium (game 24 x 50)
  terrain/prop.v3.tuft.png         32 x 24   grass tuft
  terrain/prop.v3.flowers.png      48 x 32   flowers on their own stems (pink / white / yellow)
  terrain/prop.v3.bush.png         64 x 48   bush with berries
  terrain/prop.v3.stump.png        48 x 40   mossy stump
  terrain/plains.grass.v3.<m><r><c>.png  64 x 64  summer plains ground: 6 macro patterns m = a .. f
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

def oak():
    """Round 3: 10 big leaf masses, each with a clear lit face and shade face (no sponge texture:
    leaf marks only along the lit edges), the trunk showing for under a quarter of the height,
    tapering branches seen in the gap under the crown, curved roots."""
    rng = random.Random(11)
    W, H = 160, 224
    c = Canvas(W, H, RAMPS)
    G = H - 3
    trunk = c.m_poly([(71, G), (72, 176), (74, 168), (86, 168), (88, 176), (89, G)])
    roots = (lock(c, (73, G - 6), (56, G + 1), 8, -2, 2) | lock(c, (87, G - 6), (105, G + 1), 8, 2, 2)
             | lock(c, (80, G - 4), (82, G + 1), 6, 0, 3))
    branches = (lock(c, (76, 174), (52, 140), 9, 3, 2.5) | lock(c, (84, 174), (108, 140), 9, -3, 2.5)
                | lock(c, (80, 172), (79, 128), 8, 1, 2.5))
    clumps = [(80, 50, 24, 20), (52, 70, 22, 18), (108, 68, 22, 18), (80, 94, 30, 23), (36, 108, 22, 19),
              (124, 106, 22, 19), (32, 144, 18, 15), (128, 146, 18, 15), (55, 148, 23, 19), (105, 150, 23, 19)]
    crown = c.m_ellipse(80, 104, 74, 74)
    masks = [scalloped(c, *cl, rng, 2.4) for cl in clumps]
    # the crown's dark inside behind the masses (no holes through the crown), then the wood over it
    back = np.zeros((H, W), bool)
    for (cx_, cy_, rx_, ry_) in clumps:
        back |= c.m_ellipse(cx_, cy_ + 2, rx_ + 6, ry_ + 9)
    back &= c.m_ellipse(80, 108, 70, 64)
    c.fill(back, "leaf", 2)
    c.shade_part(back, tones=(1, 1, 2), norm=True)
    wood = trunk | roots | branches
    c.fill(wood, "bark")
    c.shade_part(wood, tones=(1, 2, 3, 4, 5), light=(-0.8, -0.3, 0.5), norm=True)
    bark_texture(c, trunk)
    for y, x in zip(*np.nonzero(branches & ~trunk)):  # branches inside the crown are in its shade
        if y < 168:
            c.tone[y, x] = min(int(c.tone[y, x]), 2)
    for i in sorted(range(len(clumps)), key=lambda i: clumps[i][1]):
        m = masks[i]
        c.fill(m, "leaf")
        # each mass: its own clear light (top left) and shade (bottom right), a little of the crown's
        c.shade_part(m, tones=(2, 3, 4, 5, 6), global_mask=crown, gmix=0.3, norm=True)
        inner = m & ~erode(erode(erode(m)))
        k = c.mid("leaf")
        for y, x in zip(*np.nonzero(inner)):  # leaf marks along the lit edge only
            if c.tone[y, x] >= 5 and hsh(x, y, 3) % 5 == 0 and y + 1 < H and x + 2 < W:
                for dx, dy in ((0, 0), (1, 0), (2, 0), (1, 1)):
                    if c.mat[y + dy, x + dx] == k:
                        c.tone[y + dy, x + dx] = 6
        # the mass's lower edge turns into its own shade: a 2-texel rim along the bottom only
        cy_ = clumps[i][1]
        for y, x in zip(*np.nonzero(m)):
            if y > cy_ and ((y + 1 < H and not m[y + 1, x]) or (y + 2 < H and not m[y + 2, x])):
                c.tone[y, x] = 2
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


PATTERNS = "abcdef"  # 6 macro patterns, each 256 x 256 (4 x 4 tiles)


@functools.lru_cache(maxsize=None)
def macro_of(bx, by):
    """Which pattern a 4 x 4-tile block uses: a hashed order of the 6 patterns per block, taking the
    first that differs from the 2 blocks on the left, the block above, above-left and above-right (5
    blocks, so one always remains): no pattern meets itself side by side, one above the other or
    diagonally, nor 2 blocks apart in a row; there is no fixed period."""
    near = set()
    if bx > 0:
        near.add(macro_of(bx - 1, by))
    if bx > 1:
        near.add(macro_of(bx - 2, by))
    if by > 0:
        near.add(macro_of(bx, by - 1))
        near.add(macro_of(bx + 1, by - 1))
        if bx > 0:
            near.add(macro_of(bx - 1, by - 1))
    order = sorted(PATTERNS, key=lambda m: hsh(bx * 7 + ord(m), by * 13 + ord(m), 91))
    for m in order:
        if m not in near:
            return m
    return order[0]


def blades_in(c, mask, tone, density, rng, n):
    """Fill a patch with grass blades of `tone` (vertical strokes 2-4 texels) at `density`, not a flat
    colour: the patch reads as thicker / thinner grass, with ragged edges, at about half the step."""
    ys, xs = np.nonzero(mask)
    for y, x in zip(ys, xs):
        if (y + hsh(x, 0, n) % 4) % 3 == 0 and rng.random() < density:
            for d in range(rng.randint(2, 4)):
                if y - d >= 0 and mask[y - d, x]:
                    c.tone[y - d, x] = tone


def grass_macro(name, n=256):
    """One 256 x 256 pattern of summer plains grass (round 3): no big light or dark shapes. Even small
    mottles of denser / sparser blades over the whole pattern (up to 2 texels from its edge, never
    across it), 3-4 medium soft patches made of blades, tufts, clover and pebbles. No ground flowers
    (flowers are props)."""
    seed = 100 + PATTERNS.index(name) * 17
    rng = random.Random(seed)
    c = Canvas(n, n, RAMPS)
    c.fill(np.ones((n, n), bool), "grass", 3)
    # medium soft patches (2-3), darker or lighter, made of blades (about half the contrast of a fill)
    for k in range(rng.randint(3, 4)):
        r = rng.uniform(16, 26)
        cx, cy = rng.uniform(r + 3, n - r - 3), rng.uniform(r + 3, n - r - 3)
        m = blob(n, cx, cy, r, r * rng.uniform(0.6, 0.9), seed + k)
        blades_in(c, m, 2 if k % 2 == 0 else 4, 0.65, rng, seed + k)
    # small mottles everywhere (to 2 texels from the edge): the texture is even, so no 4-tile grid
    for k in range(70):
        r = rng.uniform(3, 7)
        cx, cy = rng.uniform(r + 2, n - r - 2), rng.uniform(r + 2, n - r - 2)
        m = blob(n, cx, cy, r, r * rng.uniform(0.5, 0.9), seed * 3 + k)
        blades_in(c, m, 2 if rng.random() < 0.6 else 4, 0.5, rng, seed * 5 + k)
    # tufts on a jittered grid (inside the pattern)
    step = 8
    for gy in range(2, n - 4, step):
        for gx in range(1, n - 6, step):
            x = gx + rng.randint(1, step - 3)
            y = gy + rng.randint(4, step - 1)
            if y > n - 2 or x > n - 3:
                continue
            base = int(c.tone[y, x])
            kind = rng.random()
            if kind < 0.55:  # 3 blades, the middle one tallest, a lit 2-texel tip
                for bx, h in ((-1, 3), (0, 5), (1, 4)):
                    for d in range(h):
                        c.tone[y - d, x + bx] = min(5, base + 1) if d >= h - 2 else base
                c.tone[y - 5, x] = min(5, base + 2)
                c.tone[y - 4, x] = min(5, base + 2)
                c.tone[y + 1, x - 1:x + 2] = max(1, base - 1)
            elif kind < 0.70:  # a darker sprig, 2 wide
                for d in range(4):
                    c.tone[y - d, x + d // 2:x + d // 2 + 2] = max(1, base - 1)
    # clover (3 leaflets of 2 x 2) and pebbles (3 x 2), a few
    for _ in range(3):
        x, y = rng.randint(8, n - 12), rng.randint(8, n - 12)
        for dx, dy in ((0, 0), (3, 0), (1, 2)):
            c.tone[y + dy:y + dy + 2, x + dx:x + dx + 2] = 5
        c.tone[y + 4, x + 1:x + 3] = 2
    for _ in range(2):
        x, y = rng.randint(8, n - 12), rng.randint(8, n - 12)
        for dx in range(3):
            c.dot(x + dx, y, STONE[5] if dx == 0 else STONE[4])
            c.dot(x + dx, y + 1, STONE[3] if dx < 2 else STONE[2])
        c.tone[y + 2, x:x + 3] = 2
    despeckle(c)
    return c


def main():
    items = {
        "obj.v3.oak.png": oak(), "obj.v3.pine.png": pine(), "prop.v3.tuft.png": tuft(),
        "prop.v3.flowers.png": flowers(), "prop.v3.bush.png": bush(), "prop.v3.stump.png": stump(),
    }
    out = [save(c, os.path.join(OUT, k)) for k, c in items.items()]
    for name in PATTERNS:
        big = grass_macro(name).image()
        for r in range(4):
            for col in range(4):
                out.append(save(big.crop((col * 64, r * 64, col * 64 + 64, r * 64 + 64)),
                                os.path.join(OUT, f"plains.grass.v3.{name}{r}{col}.png")))
    print("\n".join(os.path.relpath(p, ROOT) for p in out))


if __name__ == "__main__":
    main()
