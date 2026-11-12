"""v3 ground (STYLE.md 6): the plains grass, round 4 of the pilot and the start of production (order 1).

Two layers, both ground ART (the human decision 2026-11-11: the large light and dark are drawn into
the ground pictures, not tinted by the game):

  1. the base: 8 patterns (a .. h), each one 256 x 256 picture (4 x 4 tiles) cut into 16 tiles
       <season.>plains.grass.v3.<m><r><c>.png        64 x 64, opaque
     small mottles made of blade density, 3 kinds of grass marks scattered at uneven spacing. The game
     picks the pattern of each 4 x 4-tile block with macro_of(bx, by), the tile in it by (ty % 4, tx % 4).
  2. the flow: the slow light and dark of the field across several tiles, as corner (Wang) tiles
       <season.>plains.grassflow.v3.<kind><corners>.<v>.png   64 x 64, opaque blades on transparent
     kind d = thick grass (one tone darker), l = thin sunny grass (one tone lighter, toward yellow-
     green); corners = 4 bits (top-left, top-right, bottom-right, bottom-left: 1 = that corner is in the
     patch); v = 2 variants. The blade density follows the corners, so neighbouring tiles join without
     an edge. The game reads the corner state from flow_corner(cx, cy): a smooth noise over the WORLD
     corners (not periodic, so the large light and dark never repeat), dark below 1/3, light above 2/3,
     and never dark next to light. Tiles whose corners are all "none" get no flow tile.
Seasons: summer (v2 `plains` ramp), autumn (`autumn.grass`), winter (`snow`); spring uses summer.
Run: python3 tools/art_v3/gen_ground_v3.py [summer|autumn|winter|all]
"""

import functools
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402

from v3lib import ROOT, Canvas, despeckle, lift_ramp, save, shift  # noqa: E402,F401

OUT = os.path.join(ROOT, "src", "art-release-v3", "terrain")
PATTERNS = "abcdefgh"  # 8 base patterns

SEASONS = {  # ground ramp (7 tones), earth ramp, prefix of the file names
    "summer": dict(grass=["#16301c", "#2a5030", "#335d3a", "#3c6a38", "#4e773f", "#528446", "#6c9e58"],
                   earth=["#1c140e", "#3a2a1c", "#483023", "#57402a", "#665332", "#74583a", "#927450"],
                   prefix=""),
    "autumn": dict(grass=["#2e2010", "#5e4420", "#744b28", "#8a6630", "#998238", "#a88440", "#c4a058"],
                   earth=["#1c140e", "#3a2a1c", "#483023", "#57402a", "#665332", "#74583a", "#927450"],
                   prefix="autumn."),
    "winter": dict(grass=["#3a4866", "#7a8cae", "#99abc7", "#b8c8e0", "#cadbe9", "#dce6f2", "#f8fbff"],
                   earth=["#3a3846", "#585668", "#6c677a", "#7a788c", "#8a8698", "#9e9cb0", "#b4b2c4"],
                   prefix="winter."),
}


def hsh(x, y, s=0):
    h = (x * 374761393 + y * 668265263 + s * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return h ^ (h >> 16)


def ramps_for(season):
    sp = SEASONS[season]
    g = lift_ramp(sp["grass"])
    # the sunny grass: a little brighter and turned toward YELLOW in every season (round 5): summer's
    # green turns down the hue circle (to yellow-green), autumn's orange turns up it (to yellow)
    dh = {"summer": -14, "autumn": 14, "winter": 0}[season]
    sunny = [shift(c, dh=dh, ds=1.05, dv=1.05) for c in g]
    # round 6, "fine": the base tone with neighbours only ~11 apart in brightness (summer's own step),
    # for the marks and mottles of autumn and winter whose ramps step 20-30 (they read as grain)
    def toward(a, b, dl):
        from v3lib import luma
        lo, hi = 0.0, 1.0
        for _ in range(20):
            t = (lo + hi) / 2
            m = tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))
            if abs(luma(m) - luma(a)) < dl:
                lo = t
            else:
                hi = t
        return tuple(round(a[i] + (b[i] - a[i]) * lo) for i in range(3))
    if season == "summer":
        fine = list(g)
    else:
        fine = list(g)
        fine[2] = toward(g[3], g[1], 11)
        fine[4] = toward(g[3], g[5], 11)
        fine[5] = toward(g[3], g[6], 19)
    return {"grass": g, "sunny": sunny, "earth": lift_ramp(sp["earth"]), "fine": fine}


@functools.lru_cache(maxsize=None)
def macro_of(bx, by):
    """The base pattern of a 4 x 4-tile block: a hashed order of the 8 patterns per block, the first
    that differs from the block on the left, above, above-left and above-right (4 blocks: at least 4
    candidates always remain, so the choice stays random and there is no fixed period)."""
    near = set()
    if bx > 0:
        near.add(macro_of(bx - 1, by))
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


def blob(n, cx, cy, rx, ry, seed, wrap=False):
    """An irregular patch: an ellipse whose radius wobbles with the angle (optionally on a torus)."""
    rng = random.Random(seed)
    ph = [rng.uniform(0, 6.28) for _ in range(3)]
    yy, xx = np.mgrid[0:n, 0:n]
    dx, dy = xx + 0.5 - cx, yy + 0.5 - cy
    if wrap:
        dx = (dx + n / 2) % n - n / 2
        dy = (dy + n / 2) % n - n / 2
    a = np.arctan2(dy, dx)
    k = 1 + 0.22 * np.sin(2 * a + ph[0]) + 0.15 * np.sin(3 * a + ph[1]) + 0.08 * np.sin(5 * a + ph[2])
    return np.hypot(dx / rx, dy / ry) <= k


def blades_in(c, mask, mat, tone, density, rng, seed, wrap=False):
    """Grass blades of `tone` (vertical strokes 2-4 texels) at `density` inside `mask`."""
    n = c.h
    ys, xs = np.nonzero(mask)
    k = c.mid(mat)
    for y, x in zip(ys, xs):
        if (y + hsh(x, 0, seed) % 4) % 3 == 0 and rng.random() < density:
            for d in range(rng.randint(2, 4)):
                Y = (y - d) % n if wrap else y - d
                if Y >= 0 and mask[Y, x]:
                    c.mat[Y, x] = k
                    c.tone[Y, x] = tone


def scatter(rng, n, count, min_d, margin):
    """Points at uneven spacing (dart throwing): no grid rows."""
    pts = []
    tries = 0
    while len(pts) < count and tries < count * 40:
        tries += 1
        x, y = rng.uniform(margin, n - margin), rng.uniform(margin, n - margin)
        if all((x - a) ** 2 + (y - b) ** 2 >= min_d * min_d for a, b in pts):
            pts.append((x, y))
    return pts


def _set(c, y, x, t, k=None):
    if 0 <= y < c.h and 0 <= x < c.w:
        c.tone[y, x] = t
        if k is not None:
            c.mat[y, x] = k


def mark(c, x, y, kind, base, rng, lo=1, hi=6, k=None):
    """The 3 grass marks: a 3-blade tuft, a 2-blade leaning pair, a single tall blade. Clipped at the
    picture's edge (round 6: marks reach the pattern's edge, the part outside is cut)."""
    x, y = int(x), int(y)
    up1, up2, dn = min(hi, base + 1), min(hi, base + 2), max(lo, base - 1)
    if kind == 0:
        for bx, h in ((-1, 3), (0, 5), (1, 4)):
            for d in range(h):
                _set(c, y - d, x + bx, up1 if d >= h - 2 else base, k)
        for bx in (-1, 0, 1):
            _set(c, y + 1, x + bx, dn, k)
    elif kind == 1:
        lean = rng.choice((-1, 1))
        for bx, h in ((0, 4), (1, 3)):
            for d in range(h):
                _set(c, y - d, x + bx + (lean if d >= 2 else 0), up1 if d >= h - 2 else base, k)
        for bx in (0, 1):
            _set(c, y + 1, x + bx, dn, k)
    else:
        for d in range(6):
            _set(c, y - d, x, up2 if d >= 4 else (up1 if d >= 2 else base), k)
        _set(c, y - 3, x + 1, base, k)


def base_pattern(name, season, n=256):
    """Round 6: the patches and the marks reach the pattern's EDGE (the part outside is cut, plus a
    top-up of marks along the 4 edges), so the pattern has no mark-free band along its border (the
    256-px grid of the 1a re-inspection). Autumn and winter draw their marks and mottles with the
    "fine" ramp (steps of ~11 in brightness like summer's), so they do not read as grain."""
    seed = 100 + PATTERNS.index(name) * 17
    rng = random.Random(seed)
    c = Canvas(n, n, ramps_for(season))
    c.fill(np.ones((n, n), bool), "grass", 3)
    mat = "grass" if season == "summer" else "fine"
    k = c.mid(mat)
    for i in range(rng.randint(3, 4)):  # medium soft patches of blades (may run off the edge)
        r = rng.uniform(16, 26)
        cx, cy = rng.uniform(0, n), rng.uniform(0, n)
        m = blob(n, cx, cy, r, r * rng.uniform(0.6, 0.9), seed + i)
        blades_in(c, m, mat, 2 if i % 2 == 0 else 4, 0.6, rng, seed + i)
    for i in range(400):  # small mottles everywhere, up to and over the edge
        r = rng.uniform(3, 7)
        cx, cy = rng.uniform(-r * 0.5, n + r * 0.5), rng.uniform(-r * 0.5, n + r * 0.5)
        m = blob(n, cx, cy, r, r * rng.uniform(0.5, 0.9), seed * 3 + i)
        blades_in(c, m, mat, 2 if rng.random() < 0.6 else 4, 0.5, rng, seed * 5 + i)
    hi = 6 if season == "summer" else 5

    def put_mark(x, y):
        base = int(c.tone[min(n - 1, max(0, int(y))), min(n - 1, max(0, int(x)))])
        mark(c, x, y, rng.choices((0, 1, 2), weights=(5, 3, 2))[0], min(base, 4), rng, lo=2, hi=hi,
             k=None if season == "summer" else k)
    # grass marks: 3 kinds, uneven spacing (dart throwing) over the whole pattern and 3 px past it
    for (x, y) in scatter(rng, n + 6, 470, 8, 0):
        put_mark(x - 3, y - 3)
    # a top-up along the 4 edges (the dart throw thins out at a border; marks there are partly cut)
    for _ in range(70):
        side = rng.randrange(4)
        a, b = rng.uniform(0, n), rng.uniform(-1, 9)
        put_mark(*{0: (a, b + 4), 1: (a, n - b + 3), 2: (b - 1, a), 3: (n - b, a)}[side])
    # no calm tile: a tile whose most common texel passes 86% gets a few more small mottles
    for ty in range(n // 64):
        for tx in range(n // 64):
            for _ in range(30):
                rgb = c.rgba()[ty * 64:ty * 64 + 64, tx * 64:tx * 64 + 64, :3].astype(np.int32)
                key = (rgb[..., 0] << 16) | (rgb[..., 1] << 8) | rgb[..., 2]
                if np.unique(key, return_counts=True)[1].max() / 4096 <= 0.86:
                    break
                r = rng.uniform(3, 6)
                m = blob(n, tx * 64 + rng.uniform(4, 60), ty * 64 + rng.uniform(4, 60), r, r * 0.7, rng.randrange(1 << 20))
                blades_in(c, m, mat, 2 if rng.random() < 0.6 else 4, 0.5, rng, rng.randrange(1 << 20))
    despeckle(c, loose=(mat,))
    return c


def _value_noise(x, y, scale, seed):
    """Smooth value noise at world corner (x, y) (in tiles), cell size `scale` tiles."""
    gx, gy = x / scale, y / scale
    x0, y0 = math.floor(gx), math.floor(gy)
    fx, fy = gx - x0, gy - y0
    sx, sy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)

    def r(i, j):
        return (hsh(i, j, seed) % 10000) / 10000.0
    a = r(x0, y0) + (r(x0 + 1, y0) - r(x0, y0)) * sx
    b = r(x0, y0 + 1) + (r(x0 + 1, y0 + 1) - r(x0, y0 + 1)) * sx
    return a + (b - a) * sy


def flow_value(cx, cy):
    return 0.65 * _value_noise(cx, cy, 6.0, 1) + 0.35 * _value_noise(cx, cy, 3.0, 2)


@functools.lru_cache(maxsize=None)
def flow_corner(cx, cy):
    # (The game also returns "m" for a corner any of whose 4 cells is not this ground, so the flow
    # fades out before a transition tile; flow tiles are drawn only on full tiles of this ground.)
    """The flow state of a world tile corner: 'd' (thick, dark), 'l' (thin, light) or 'm' (none).
    A corner next to (4 neighbours) the opposite state becomes 'm', so no tile mixes d and l."""
    def raw(x, y):
        v = flow_value(x, y)
        return "d" if v < 0.32 else ("l" if v > 0.66 else "m")
    st = raw(cx, cy)
    if st != "m":
        opp = "l" if st == "d" else "d"
        if any(raw(cx + dx, cy + dy) == opp for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1))):
            return "m"
    return st


SIDES = ("N", "E", "S", "W")

# ---- round 7 (production check 3 + the coordinator's memory decision: plains grass <= 5 MB / season)
# The flow tiles are SHAPES: grey blades (body 214, tip 255) on transparent, shared by the thick
# grass (d) and the sunny grass (l); the game multiplies them by a colour from FLOW_TINT (per season
# and kind). Summer and autumn share one shape set, winter has its own (drift streaks).
# Mirror pairs are stored once: the game draws the partner flipped left-right (MIRROR / flow_key).
SHAPE_BODY, SHAPE_TIP = 214, 255
FLOW_SETS = {"summer": "", "autumn": "", "winter": "winter."}


def flip_bits(bits):
    """Corner bits (TL, TR, BR, BL) of the left-right mirror of a tile."""
    return bits[1] + bits[0] + bits[3] + bits[2]


STORED = ("1000", "0001", "1001", "1110", "0111", "1100", "0011", "1010", "1111")  # the rest are mirrors
MIRROR = {flip_bits(b): b for b in STORED if flip_bits(b) not in STORED}  # 0100->1000, 0110->1001 ...
INNER_SHAPES = 3  # inner shapes of a tile whose border crosses 2 sides (0 on the tile's edges)
FULL_SHAPES = 4  # stored variants of the full tile 1111 (and each may be drawn flipped: 8 looks)


def crossed(bits):
    """The sides a patch border crosses (their 2 corners differ). bits: TL, TR, BR, BL."""
    tl, tr, br, bl = (b == "1" for b in bits)
    return [sd for sd, on in zip(SIDES, (tl != tr, tr != br, bl != br, tl != bl)) if on]


def n_flow_variants(bits):
    cs = crossed(bits)
    if not cs:
        return FULL_SHAPES
    if len(cs) == 4:
        return 16  # 4 side states
    return 4 * INNER_SHAPES  # 2 side states x the inner shapes


def side_state(tx, ty, side):
    """A side's state 0 / 1 from its world position: both tiles sharing the side compute the same."""
    i, j = tx, ty
    h = {"N": hsh(2 * i + 1, 2 * j, 61), "E": hsh(2 * i + 2, 2 * j + 1, 61), "S": hsh(2 * i + 1, 2 * j + 2, 61),
         "W": hsh(2 * i, 2 * j + 1, 61)}[side]
    return (h >> 4) & 1


def flow_key(tx, ty):
    """What the game draws on tile (tx, ty) for the flow layer, or None:
         (kind, bits, v, flip)
    kind  'd' (thick grass) or 'l' (sunny grass): only the colour (FLOW_TINT[season][kind])
    bits  the STORED corner bits (TL, TR, BR, BL), one of STORED
    v     the stored variant of that shape
    flip  True: draw the shape mirrored left-right (scale.x = -1 about the tile's centre)
    File: <set.>plains.grassflow.v3.<bits>.<v>.png, set = "" (summer, autumn) or "winter.".
    Rule (round 7):
      * the tile's own corner bits b; if b is a mirror (in MIRROR), the shape is MIRROR[b], flip = True
        and the side states are read mirrored (the stored tile's W side is the world tile's E side)
      * border crosses 2 sides (A, B in the order N, E, S, W of the STORED tile):
          v = s(A) + 2 s(B) + 4 * ((tx + 2 ty) % 3)   (the inner shape: never the same as the tile
          above or beside it, so a column / row of equal corner sets does not line up)
      * border crosses 4 sides (1010; 0101 is its mirror): v = s(N) + 2 s(E) + 4 s(S) + 8 s(W)
      * full patch 1111: v = hsh(tx, ty, 33) % 4, flip = bit 2 of hsh(tx, ty, 35)"""
    cs = [flow_corner(tx, ty), flow_corner(tx + 1, ty), flow_corner(tx + 1, ty + 1), flow_corner(tx, ty + 1)]
    kinds = {k for k in cs if k != "m"}
    if not kinds:
        return None
    kind = kinds.pop()
    bits = "".join("1" if k == kind else "0" for k in cs)
    flip = bits in MIRROR
    stored = MIRROR.get(bits, bits)

    def st(side):  # the state of the STORED tile's side, read from the world tile
        if flip and side in ("E", "W"):
            side = "W" if side == "E" else "E"
        return side_state(tx, ty, side)
    sides = crossed(stored)
    if not sides:
        return kind, stored, hsh(tx, ty, 33) % FULL_SHAPES, bool((hsh(tx, ty, 35) >> 2) & 1)
    if len(sides) == 4:
        return kind, stored, st("N") + 2 * st("E") + 4 * st("S") + 8 * st("W"), flip
    return kind, stored, st(sides[0]) + 2 * st(sides[1]) + 4 * ((tx + 2 * ty) % INNER_SHAPES), flip


def _tile_noise(seed, n=64):
    """Smooth noise with whole periods over the tile (it repeats every 64 texels, so the same field
    meets itself across every tile edge)."""
    rng = random.Random(seed)
    yy, xx = np.mgrid[0:n, 0:n] / n * 2 * math.pi
    v = np.zeros((n, n))
    for f, a in ((1, 1.0), (2, 0.6), (3, 0.35)):
        for _ in range(2):
            kx, ky = rng.randint(-f, f), rng.randint(-f, f)
            if kx == 0 and ky == 0:
                kx = f
            v += a * np.sin(kx * xx + ky * yy + rng.uniform(0, 6.28))
    return v / np.abs(v).max()


def _push(t, d):
    """Round 7: a side's push, as wide as the tile: 0 at the side's ends, full at the side and fading
    LINEARLY to 0 at the opposite side (so the middle of the tile moves too, not only the rim)."""
    return np.sin(np.pi * t) ** 2 * np.clip(1 - d, 0, 1)  # (symmetric along the side: mirrors join)


def flow_field(bits, variant):
    """The corners' bilinear blend + a weak wobble every tile shares + for each crossed side a push of
    +0.26 (state 1) or -0.26 (state 0) reaching the middle of the tile + an inner shape (0 on the
    tile's edges). Both tiles sharing a side compute the same value along it (the other sides' pushes
    are 0 there), so the border joins; down a column of equal corner sets the crossings and the middle
    move with the side states and the inner shape (no straight line)."""
    w = [int(b) for b in bits]  # TL, TR, BR, BL
    yy, xx = np.mgrid[0:64, 0:64]
    u, v = (xx + 0.5) / 64, (yy + 0.5) / 64
    f = w[0] * (1 - u) * (1 - v) + w[1] * u * (1 - v) + w[2] * u * v + w[3] * (1 - u) * v
    inner = np.sin(np.pi * u) * np.sin(np.pi * v)
    edge_fade = np.clip(np.minimum(np.minimum(xx + 0.5, 63.5 - xx), np.minimum(yy + 0.5, 63.5 - yy)) / 6, 0, 1)
    sides = crossed(bits)
    if not sides:
        shape, states = variant, {}
    elif len(sides) == 4:
        shape, states = 0, {sd: (variant >> i) & 1 for i, sd in enumerate(SIDES)}
    else:
        shape, states = variant >> 2, {sides[0]: variant & 1, sides[1]: (variant >> 1) & 1}
    amp = 0.20 if bits == "1111" else 0.35
    shared = _tile_noise(901)
    shared = (shared + shared[:, ::-1]) / 2  # left-right symmetric, so a mirrored tile meets the others
    F = f + 0.08 * shared + amp * inner * edge_fade * _tile_noise(1000 + shape * 37 + int(bits, 2))
    if len(sides) == 2:  # each inner shape also moves the middle by its own step (-0.3 / 0 / +0.3)
        F = F + (-0.3, 0.0, 0.3, 0.1)[shape] * inner * edge_fade
    for sd, on in states.items():
        t, d = {"N": (u, v), "S": (u, 1 - v), "W": (v, u), "E": (v, 1 - u)}[sd]
        F = F + (0.26 if on else -0.26) * _push(t, d)
    return F


def flow_shape(sset, bits, variant):
    """One flow SHAPE tile (grey on transparent): bundles of 2-3 blades (summer / autumn set) or drift
    streaks (winter set), placed stratified over the tile and 5 rows below it, inside the patch of
    flow_field; then the rows / columns evened out (only growing existing marks or trimming without
    leaving a dot), small clumps of 1-2 texels away from the tile's edge removed."""
    c = Canvas(64, 64, {"shape": [(0, 0, 0)] * 4 + [(SHAPE_BODY,) * 3, (234,) * 3, (SHAPE_TIP,) * 3]})
    seed = hsh(int(bits, 2), variant, 5 if sset else 4) & 0xFFFFFF
    rng = random.Random(seed)
    F = flow_field(bits, variant)
    k = c.mid("shape")
    BODY, TIP = 4, 6

    def inside(x, y):
        xi, yi = min(63, max(0, int(x))), min(63, max(0, int(y)))
        val = F[yi, xi]
        return val > 0.5 or (val > 0.38 and rng.random() < 0.35)
    winter = bool(sset)
    N = 88 if not winter else 64  # winter: as many streaks as round 6, softer colour (FLOW_TINT)
    perm = list(range(N))
    rng.shuffle(perm)
    pts = [((perm[i] + rng.random()) / N * 67 - 2.5, (i + rng.random()) / N * 69) for i in range(N)]
    for (x, y) in pts:
        if not inside(x, min(y, 63.0)):
            continue
        if winter:  # a drift streak: 5-8 wide, its top row lit (tip), the row under it (body)
            ln = rng.randint(5, 8)
            for i in range(ln):
                for j in range(1 + (0 < i < ln - 1)):
                    X, Y = int(x) + i, int(y) - j
                    if 0 <= X < 64 and 0 <= Y < 64:
                        c.mat[Y, X] = k
                        c.tone[Y, X] = BODY if j == 0 else TIP
            continue
        nb = rng.choice((2, 3))
        lean = rng.choice((-1, 0, 1))
        for bi in range(nb):  # the bundle: blades 1 apart, the middle one tallest; tips 2 texels
            h = rng.randint(3, 5) + (1 if bi == 1 else 0)
            for d in range(h):
                X = int(x) + bi + (lean if d >= h - 2 else 0)
                Y = int(y) - d
                if 0 <= X < 64 and 0 <= Y < 64:
                    c.mat[Y, X] = k
                    c.tone[Y, X] = TIP if d >= h - 2 else BODY
    ins = F > 0.5
    GROW_H[0] = winter
    _balance(c, ins, k, BODY, rng, 0.12)
    _drop_small(c, 2)
    _fill_thin(c, ins, k, BODY, rng)
    _drop_small(c, 1)
    return c


def _drop_small(c, size):
    """Remove single texels, and clumps of <= size texels that do not touch the tile's edge (a clump
    at the edge may be the cut end of a mark that goes on in the next tile)."""
    filled = c.mat != 0
    seen = np.zeros_like(filled)
    for y in range(64):
        for x in range(64):
            if not filled[y, x] or seen[y, x]:
                continue
            comp, stack = [], [(x, y)]
            seen[y, x] = True
            while stack:
                p, q = stack.pop()
                comp.append((p, q))
                for a, b in ((p + 1, q), (p - 1, q), (p, q + 1), (p, q - 1)):
                    if 0 <= a < 64 and 0 <= b < 64 and filled[b, a] and not seen[b, a]:
                        seen[b, a] = True
                        stack.append((a, b))
            if len(comp) == 1 or (len(comp) <= size and not any(p in (0, 63) or q in (0, 63) for p, q in comp)):
                for p, q in comp:
                    c.mat[q, p] = 0


def _deg(m, k, y, x):
    return sum(1 for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))
               if 0 <= y + dy < 64 and 0 <= x + dx < 64 and m[y + dy, x + dx] == k)


GROW_H = [False]  # winter streaks grow only sideways (set by flow_shape)


def _can_grow(m, k, y, x):
    """A texel may be added next to a mark: beside it (and, except for winter streaks, above / below)."""
    dirs = ((1, 0), (-1, 0)) if GROW_H[0] else ((0, 1), (0, -1), (1, 0), (-1, 0))
    return any(0 <= y + dy < 64 and 0 <= x + dx < 64 and m[y + dy, x + dx] == k for dx, dy in dirs)


def _balance(c, inside, k, tone_add, rng, tol=0.12):
    """Even out the cover per row and column (round 7: it only GROWS existing marks, never starts a
    new one, and trims only where no texel is left alone)."""
    m = c.mat
    t = ((m == k) & inside).sum() / max(1, inside.sum())
    for _ in range(30):
        for axis in (0, 1):
            for i in range(64):
                line_in = inside[i, :] if axis == 0 else inside[:, i]
                n = line_in.sum()
                if n < 12:
                    continue
                line = (m[i, :] == k) if axis == 0 else (m[:, i] == k)
                have = (line & line_in).sum()
                want = t * n
                slack = max(1.0, tol * want)
                idx = [j for j in range(64) if line_in[j]]
                rng.shuffle(idx)
                if have < want - slack:
                    need = int(want - have)
                    for j in idx:
                        if need <= 0:
                            break
                        y, x = (i, j) if axis == 0 else (j, i)
                        if m[y, x] != k and _can_grow(m, k, y, x):
                            m[y, x] = k
                            c.tone[y, x] = tone_add
                            need -= 1
                elif have > want + slack:
                    extra = int(have - want)
                    for j in idx:
                        if extra <= 0:
                            break
                        y, x = (i, j) if axis == 0 else (j, i)
                        if m[y, x] != k:
                            continue
                        same = [(y + dy, x + dx) for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))
                                if 0 <= y + dy < 64 and 0 <= x + dx < 64 and m[y + dy, x + dx] == k]
                        if same and all(_deg(m, k, *q) >= 2 for q in same):
                            m[y, x] = 0
                            extra -= 1


def _fill_thin(c, inside, k, tone_add, rng):
    """A last pass: a row or column of the patch over 108% of the cover loses texels whose removal
    leaves no texel alone; one under 92% grows texels from the marks in it. Rows, columns, 3 times."""
    m = c.mat
    t = ((m == k) & inside).sum() / max(1, inside.sum())
    for axis in (0, 1, 0, 1, 0, 1):
        for i in range(64):
            line_in = inside[i, :] if axis == 0 else inside[:, i]
            n = line_in.sum()
            if n < 12:
                continue
            idx = [j for j in range(64) if line_in[j]]
            rng.shuffle(idx)
            for j in idx:
                line = (m[i, :] == k) if axis == 0 else (m[:, i] == k)
                if (line & line_in).sum() <= 1.08 * t * n:
                    break
                y, x = (i, j) if axis == 0 else (j, i)
                if m[y, x] != k:
                    continue
                same = [(y + dy, x + dx) for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))
                        if 0 <= y + dy < 64 and 0 <= x + dx < 64 and m[y + dy, x + dx] == k]
                if same and all(_deg(m, k, *q) >= 2 for q in same):
                    m[y, x] = 0
            for j in idx:
                line = (m[i, :] == k) if axis == 0 else (m[:, i] == k)
                if (line & line_in).sum() >= 0.92 * t * n:
                    break
                y, x = (i, j) if axis == 0 else (j, i)
                if m[y, x] != k and _can_grow(m, k, y, x):
                    m[y, x] = k
                    c.tone[y, x] = tone_add
            if GROW_H[0] and axis == 0:  # winter: a thin row may also get a new 3-texel streak
                for x0 in idx:
                    if ((m[i, :] == k) & line_in).sum() >= 0.92 * t * n:
                        break
                    xs = range(x0, x0 + 3)
                    if x0 + 2 < 64 and all(m[i, x] != k and line_in[x] for x in xs) and \
                            not any((i > 0 and m[i - 1, x] == k) or (i < 63 and m[i + 1, x] == k) for x in range(x0 - 1, x0 + 4) if 0 <= x < 64):
                        for x in xs:
                            m[i, x] = k
                            c.tone[i, x] = tone_add


def flow_tints(season):
    """FLOW_TINT[season][kind]: the colour the game multiplies a shape by (the tip = this colour, the
    body = 214/255 of it). d: the ground's tone 2 (thick, darker grass); l: the sunny ramp's tone 5
    (summer), 3 (autumn: calm, less grain), the snow's tone 5 (winter: softer than white)."""
    r = ramps_for(season)
    d = r["grass"][2]
    lt = {"summer": r["sunny"][5], "autumn": r["sunny"][3], "winter": r["grass"][5]}[season]
    return {"d": "#%02x%02x%02x" % tuple(d), "l": "#%02x%02x%02x" % tuple(lt)}


FLOW_TINT = None  # filled lazily: {season: {"d": "#rrggbb", "l": "#rrggbb"}}


def tinted(shape_img, tint_hex):
    """What the game draws: the grey shape multiplied by the tint (alpha kept)."""
    from PIL import Image
    a = np.array(shape_img.convert("RGBA")).astype(np.float64)
    t = np.array([int(tint_hex[i:i + 2], 16) for i in (1, 3, 5)], dtype=np.float64)
    a[..., :3] = np.round(a[..., :3] / 255.0 * t)
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def write(season):
    pre = SEASONS[season]["prefix"]
    out = []
    for name in PATTERNS:
        big = base_pattern(name, season).image()
        for r in range(4):
            for col in range(4):
                out.append(save(big.crop((col * 64, r * 64, col * 64 + 64, r * 64 + 64)),
                                os.path.join(OUT, f"{pre}plains.grass.v3.{name}{r}{col}.png")))
    return out


def write_flow():
    """The 2 shape sets (summer/autumn "" and winter "winter."), STORED masks only."""
    out = []
    for sset in ("", "winter."):
        for bits in STORED:
            for v in range(n_flow_variants(bits)):
                out.append(save(flow_shape(sset, bits, v), os.path.join(OUT, f"{sset}plains.grassflow.v3.{bits}.{v}.png")))
    return out


def ground_tile(tx, ty, season="summer", load=None):
    """The picture of one ground tile, the 2 layers composed (what the game draws): the base tile,
    then the flow shape (flipped if flow_key says so) multiplied by FLOW_TINT[season][kind]."""
    from PIL import Image, ImageOps
    pre = SEASONS[season]["prefix"]
    load = load or (lambda p: Image.open(p).convert("RGBA"))
    t = load(os.path.join(OUT, f"{pre}plains.grass.v3.{macro_of(tx // 4, ty // 4)}{ty % 4}{tx % 4}.png")).copy()
    fk = flow_key(tx, ty)
    if fk:
        kind, bits, v, flip = fk
        sh = load(os.path.join(OUT, f"{FLOW_SETS[season]}plains.grassflow.v3.{bits}.{v}.png"))
        if flip:
            sh = ImageOps.mirror(sh)
        t.alpha_composite(tinted(sh, flow_tints(season)[kind]))
    return t


def main(which, edges=True):
    seasons = list(SEASONS) if which == "all" else [which]
    n = 0
    for s in seasons:
        n += len(write(s))
        if edges:
            n += len(write_edges(s))
    n += len(write_flow())
    print(f"{n} files")



# ------------------------------------------------------------------ transitions (production order 1)
# The v2 dual-grid scheme (docs/art-release-v2/terrain/NAMES.md 2): the overlay
# <season.>plains.grass.v3.edge.<mask>.<v>.png is drawn over the lower terrain's tile; mask = the
# corners that are plains grass (NW 1, NE 2, SW 4, SE 8), v = the side-state variant (0-3; masks 6 / 9:
# 0-1). The border is v2's own curve (tools/terrain_v2/transitions.field) sampled at 2x, so v3 edges
# join v2 ones and the engine's variant rule stays the same.

def _v2_transitions():
    sys.path.append(os.path.join(ROOT, "tools", "terrain_v2"))
    import transitions  # noqa: E402
    return transitions


def edge_inside(mask, variant):
    """(field, inside, dist-to-inside, near-the-edge) at 64 x 64, from the v2 field at 2x."""
    T = _v2_transitions()
    n = 64
    F = np.zeros((n, n))
    for y in range(n):
        for x in range(n):
            F[y, x] = T.field(mask, (x + 0.5) / 2 - 0.5, (y + 0.5) / 2 - 0.5, variant)
    raw = F > 0.5
    # drop islands / fill holes that do not reach the tile's edge (as v2 round 8)
    inside = raw.copy()
    for want in (True, False):
        seen = np.zeros((n, n), bool)
        for y in range(n):
            for x in range(n):
                if raw[y, x] != want or seen[y, x]:
                    continue
                comp, stack = [], [(x, y)]
                seen[y, x] = True
                while stack:
                    p, q = stack.pop()
                    comp.append((p, q))
                    for a, b in ((p + 1, q), (p - 1, q), (p, q + 1), (p, q - 1)):
                        if 0 <= a < n and 0 <= b < n and not seen[b, a] and raw[b, a] == want:
                            seen[b, a] = True
                            stack.append((a, b))
                if not any(p in (0, n - 1) or q in (0, n - 1) for p, q in comp):
                    for p, q in comp:
                        inside[q, p] = not want
    return F, inside


def edge_overlay(season, mask, variant):
    """Plains grass over a lower ground: the grass texture inside the border, a turf edge (lit on
    the sides facing up / left, shaded on the others, 2-3 texels), and grass blades (2-7 texels,
    uneven, some leaning) growing over the border onto the lower ground."""
    T = _v2_transitions()
    F, inside = edge_inside(mask, variant)
    c = Canvas(64, 64, ramps_for(season))
    k = c.mid("grass")
    # inside: the calm base grass (tone 3) with grass marks, like the base patterns' quiet parts
    c.mat[inside] = k
    c.tone[inside] = 3
    rng0 = random.Random(mask * 13 + variant)
    for (x, y) in scatter(rng0, 64, 30, 9, 6):
        if inside[int(y), int(x)] and inside[int(y) - 5, int(x)] and inside[int(y) + 1, int(x)]:
            mark(c, x, y, rng0.choices((0, 1, 2), weights=(5, 3, 2))[0], 3, rng0)
    # the turf edge band: inside texels within 3 of the outside
    outside = ~inside
    d = np.full((64, 64), 9)
    d[outside] = 0
    for step in range(1, 4):
        grow = np.zeros_like(outside)
        prev = d < step
        grow[1:, :] |= prev[:-1, :]
        grow[:-1, :] |= prev[1:, :]
        grow[:, 1:] |= prev[:, :-1]
        grow[:, :-1] |= prev[:, 1:]
        d[grow & (d == 9)] = step
    for y in range(64):
        for x in range(64):
            if not inside[y, x] or d[y, x] > 3:
                continue
            gx, gy = T.gradient(mask, (x + 0.5) / 2 - 0.5, (y + 0.5) / 2 - 0.5)
            lit = (gx + gy) > 0.05
            c.tone[y, x] = (4 if d[y, x] == 1 else 3) if lit else (1 if d[y, x] == 1 else 2)
    # distance of the outside texels to the grass (the blades grow only right at the border)
    do = np.full((64, 64), 9)
    do[inside] = 0
    for step in range(1, 4):
        prev = do < step
        grow = np.zeros_like(prev)
        grow[1:, :] |= prev[:-1, :]
        grow[:-1, :] |= prev[1:, :]
        grow[:, 1:] |= prev[:, :-1]
        grow[:, :-1] |= prev[:, 1:]
        do[grow & (do == 9)] = step
    if season == "winter":  # a snow drift's rounded lip: no blades; a soft blue shade under it
        for y in range(64):
            for x in range(64):
                if inside[y, x] and d[y, x] <= 2:
                    gx, gy = T.gradient(mask, (x + 0.5) / 2 - 0.5, (y + 0.5) / 2 - 0.5)
                    lit = (gx + gy) > 0.05
                    c.tone[y, x] = (6 if d[y, x] == 1 else 5) if lit else (3 if d[y, x] == 1 else 4)
                elif not inside[y, x] and do[y, x] == 1 and 2 <= x < 62 and 2 <= y < 62:
                    gx, gy = T.gradient(mask, (x + 0.5) / 2 - 0.5, (y + 0.5) / 2 - 0.5)
                    if gy < -0.05:  # the drift lies above: its shade falls on the lower ground
                        c.mat[y, x] = k
                        c.tone[y, x] = 2
        _fill_holes(c)
        return c
    # blades over the border (not on the 2 outer rows / columns, so neighbouring tiles join)
    rng = random.Random(mask * 31 + variant * 7 + sum(map(ord, season)))
    for y in range(3, 61):
        for x in range(3, 61):
            if inside[y, x] or do[y, x] > 1:
                continue
            if rng.random() > 0.45:
                continue
            gx, gy = T.gradient(mask, (x + 0.5) / 2 - 0.5, (y + 0.5) / 2 - 0.5)
            step = -1 if gy >= 0 else 1  # turf below: the blades rise; turf above: they hang
            h = rng.randint(2, 7)
            lean = rng.choice((-1, 0, 0, 1))
            xx, yy = x, y
            for i in range(h):
                if not (2 <= xx < 62 and 2 <= yy < 62):
                    break
                tip = i >= h - 2
                c.mat[yy, xx] = k
                c.tone[yy, xx] = (5 if tip else 4) if step < 0 else (2 if tip else 3)
                yy += step
                if i == h // 2:
                    xx += lean
    _fill_holes(c)
    return c


def _fill_holes(c):
    """Round 5 (v2 round 8 rule): a transparent pocket that does not reach the tile's edge (between
    the turf edge and blade roots) is filled with the turf's shade tone."""
    n = c.h
    empty = c.mat == 0
    reach = np.zeros_like(empty)
    stack = [(x, y) for y in range(n) for x in range(n) if empty[y, x] and (x in (0, n - 1) or y in (0, n - 1))]
    for x, y in stack:
        reach[y, x] = True
    while stack:
        x, y = stack.pop()
        for a, b in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= a < n and 0 <= b < n and empty[b, a] and not reach[b, a]:
                reach[b, a] = True
                stack.append((a, b))
    holes = empty & ~reach
    c.mat[holes] = c.mid("grass")
    c.tone[holes] = 2


def write_edges(season):
    pre = SEASONS[season]["prefix"]
    out = []
    for mask in range(1, 15):
        for v in range(2 if mask in (6, 9) else 4):
            out.append(save(edge_overlay(season, mask, v),
                            os.path.join(OUT, f"{pre}plains.grass.v3.edge.{mask}.{v}.png")))
    return out


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "summer")
