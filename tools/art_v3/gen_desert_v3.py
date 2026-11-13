"""v3 production order 7, region 2: the DESERT ground (赤砂の荒野; STYLE.md 6, NAMES.md 1-3), one season.

The desert has no seasons (src/view/groundV2.js SEASONAL holds grass, plains, lake and moss only; the
weather gives the dry region no snow, src/game/env/weather.js), so there is one set of files.

Made the way the plains and the forest passed (gen_ground_v3.py, gen_forest_v3.py), same rules and
formulas, its own drawing:
  1. the base: 8 patterns (a .. h), each a 256 x 256 picture cut into 16 tiles
       desert.sand.v3.<m><r><c>.png                 64 x 64, opaque
     the tile of world tile (tx, ty) = pattern macro_of(tx // 4, ty // 4), row ty % 4, column tx % 4
     (gen_ground_v3.macro_of, unchanged). Red sand: small wind ripples (a lit crest row over a shaded
     trough row, wavy, 5-12 long), ripple fields (3-4 per pattern, may run off the edge), 400 small
     mottles of ripples everywhere, marks at uneven spacing (ripple pairs, pebble clusters of 2-3
     pebbles 2 x 2 / 3 x 2, small wind hollows). No 1-texel dots.
  2. the flow: the same corner (Wang) scheme and the same key rule (gen_ground_v3.flow_key). Its own
     SHAPE set (grey, body 214 / tip 255):
       desert.sandflow.v3.<bits>.<v>.png
     long wavy ripple crests 2 rows thick, ONE flat grey (255) per crest, the game multiplies them by
     DESERT_FLOW_TINT[kind] (d = the shaded lee of a dune, l = the sunlit windward face).
  3. transitions: the v2 dual-grid rule (desert sand is "dsand" in the v2 priority: above ruin and
     path, below the island sand and every grass):
       desert.sand.v3.edge.<mask>.<v>.png           (mask 1-14, v 0-3; masks 6 / 9: 0-1)
     the inside is a base tile (the forest's round 3 way: the same amount of pattern as the floor),
     cut by v2's curve at 2x, a dry sand lip (lit up / left: bright, shaded: darker) and sand spill
     (2 x 2 / 3 x 2 grains) just over the border onto the lower ground.
Run: python3 tools/art_v3/gen_desert_v3.py [ground|flow|edges|trees|props|all]
"""

import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402

import gen_ground_v3 as G  # noqa: E402  (the passed plains rules, read-only use)
from v3lib import ROOT, Canvas, despeckle, lift_ramp, luma, save  # noqa: E402

OUT = os.path.join(ROOT, "src", "art-release-v3", "terrain")
PATTERNS = G.PATTERNS
SAND = ["#3e1e12", "#82442a", "#954533", "#a8603c", "#b57d48", "#c27e54", "#daa274"]  # v2 ramps.json "dsand"
DSTONE = ["#2e2018", "#6a5240", "#7f6050", "#947a60", "#a4916e", "#b49a7c", "#d2bc9e"]  # v2 "dstone"


def _toward(a, b, dl):
    """The colour on the way from a to b whose brightness is dl from a's (the plains' "fine" rule)."""
    lo, hi = 0.0, 1.0
    for _ in range(24):
        t = (lo + hi) / 2
        m = tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))
        if abs(luma(m) - luma(a)) < dl:
            lo = t
        else:
            hi = t
    return tuple(round(a[i] + (b[i] - a[i]) * lo) for i in range(3))


def ramps_for():
    """sand: v2 dsand lifted (STYLE 3.3); fine: the base with its neighbours ~11 apart in brightness
    (dsand steps ~24: drawn with it, the ripples read as grain -- the plains' autumn / winter rule)."""
    s = lift_ramp(SAND)
    fine = list(s)
    fine[2] = _toward(s[3], s[1], 11)
    fine[1] = _toward(s[3], s[1], 18)
    fine[4] = _toward(s[3], s[5], 11)
    fine[5] = _toward(s[3], s[6], 19)
    return {"sand": s, "fine": fine, "stone": lift_ramp(DSTONE)}


# ------------------------------------------------------------------ base patterns

def ripple(c, x, y, ln, slope, bow, lit=4, shade=2, mask=None):
    """One wind ripple: for each column a lit crest texel and the shaded trough texel under it
    (2 rows: reads at 1x as a short line), bowed smoothly (bow texels at the middle). Clipped at the
    picture / mask."""
    k = c.mid("fine")
    for i in range(ln):
        X = int(x) + i
        Y = int(round(y + slope * i - bow * math.sin(math.pi * i / max(1, ln - 1))))
        for dy, t in ((0, lit), (1, shade)):
            YY = Y + dy
            if 0 <= X < c.w and 0 <= YY < c.h and (mask is None or mask[YY, X]):
                c.mat[YY, X], c.tone[YY, X] = k, t


def ripples_in(c, mask, density, rng, spacing, lmin=5, lmax=12):
    """Ripples inside `mask`: rows of ripples `spacing` apart (wavy, broken, each its own length)."""
    ys, xs = np.nonzero(mask)
    if len(ys) == 0:
        return
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    slope = rng.uniform(-0.12, 0.12)
    bow = rng.choice((-1, 1)) * rng.uniform(0.8, 1.8)  # one bow per field: its ripples run parallel
    y = y0 + rng.uniform(0, spacing)
    while y <= y1:
        x = x0 - rng.uniform(0, 6)
        while x <= x1:
            ln = rng.randint(lmin, lmax)
            if rng.random() < density:
                ripple(c, x, y + slope * (x - x0), ln, slope, bow * ln / 12, mask=mask)
            x += ln + rng.randint(3, 8)
        y += spacing + rng.uniform(-1.0, 1.5)


def pebble(c, x, y, w):
    """A pebble w x 3 (w 3-4, rounded top corners): lit top-left, base tone, shaded bottom row, and a
    1-row shadow on the sand under its right part (desert stone)."""
    k, ks = c.mid("stone"), c.mid("fine")
    rows = ((1, w - 1, 5), (0, w, 3), (0, w, 2)) if w >= 3 else ((0, w, 4), (0, w, 2))
    for dy, (a, b, t) in enumerate(rows):
        for dx in range(a, b):
            X, Y = x + dx, y + dy
            if 0 <= X < c.w and 0 <= Y < c.h:
                c.mat[Y, X], c.tone[Y, X] = k, (4 if (dy == 1 and dx == 0) else t)
    for dx in range(1, w + 1):
        X, Y = x + dx, y + len(rows)
        if 0 <= X < c.w and 0 <= Y < c.h and c.mat[Y, X] != k:
            c.mat[Y, X], c.tone[Y, X] = ks, 1


def mark(c, x, y, kind, rng):
    """Desert marks (clipped at the picture's edge):
      0 a ripple 6-12 long; 1 a ripple pair (2 crests 3-4 rows apart, offset)
      2 a pebble cluster: 2-3 pebbles (2 x 2 / 3 x 2), 1-3 texels apart
      3 a wind hollow: a 6 x 3 dip, shaded upper rows, lit lower rim (light from the top left)"""
    x, y = int(x), int(y)
    if kind == 0:
        ripple(c, x, y, rng.randint(6, 12), rng.uniform(-0.15, 0.15), rng.uniform(-1.2, 1.2))
    elif kind == 1:
        s, bw = rng.uniform(-0.12, 0.12), rng.uniform(-1.2, 1.2)
        ripple(c, x, y, rng.randint(8, 12), s, bw)
        ripple(c, x + rng.randint(-3, 3), y + rng.randint(4, 5), rng.randint(6, 10), s, bw)
    elif kind == 2:
        px, py = x, y
        for i in range(rng.randint(2, 3)):
            pebble(c, px, py, rng.choice((3, 4, 4)))
            px += rng.randint(5, 7) * rng.choice((-1, 1))
            py += rng.randint(-2, 3)
    else:
        k = c.mid("fine")
        for dy, row, t in ((0, (1, 6), 2), (1, (0, 7), 2), (2, (1, 6), 4)):
            for dx in range(*row):
                X, Y = x + dx, y + dy
                if 0 <= X < c.w and 0 <= Y < c.h:
                    c.mat[Y, X], c.tone[Y, X] = k, t


def base_pattern(name, n=256):
    """The desert floor: ripple fields (3-4, may run off the edge), 400 small mottles of ripples (up to
    and over the edge), marks at uneven spacing over the whole pattern and 3 texels past it, a top-up
    of marks along the 4 edges (no mark-free border band), no calm tile (the most common texel of a
    64 x 64 tile under 86 %)."""
    seed = 700 + PATTERNS.index(name) * 23
    rng = random.Random(seed)
    c = Canvas(n, n, ramps_for())
    c.fill(np.ones((n, n), bool), "sand", 3)
    for i in range(rng.randint(3, 4)):
        r = rng.uniform(18, 30)
        m = G.blob(n, rng.uniform(0, n), rng.uniform(0, n), r, r * rng.uniform(0.5, 0.8), seed + i)
        ripples_in(c, m, 0.9, rng, rng.uniform(4.0, 5.0), 9, 18)
    for i in range(400):
        r = rng.uniform(3, 7)
        cx, cy = rng.uniform(-r * 0.5, n + r * 0.5), rng.uniform(-r * 0.5, n + r * 0.5)
        m = G.blob(n, cx, cy, r * 1.4, r * rng.uniform(0.5, 0.8), seed * 3 + i)
        ripples_in(c, m, 0.35, rng, rng.uniform(4.5, 6.5), 6, 11)

    def put_mark(x, y):
        mark(c, x, y, rng.choices((0, 1, 2, 3), weights=(6, 3, 1, 2))[0], rng)
    for (x, y) in G.scatter(rng, n + 6, 170, 13, 0):
        put_mark(x - 3, y - 3)
    for _ in range(40):
        side = rng.randrange(4)
        a, b = rng.uniform(0, n), rng.uniform(-1, 9)
        put_mark(*{0: (a, b + 4), 1: (a, n - b + 3), 2: (b - 1, a), 3: (n - b, a)}[side])
    for ty in range(n // 64):
        for tx in range(n // 64):
            for _ in range(30):
                rgb = c.rgba()[ty * 64:ty * 64 + 64, tx * 64:tx * 64 + 64, :3].astype(np.int32)
                key = (rgb[..., 0] << 16) | (rgb[..., 1] << 8) | rgb[..., 2]
                if np.unique(key, return_counts=True)[1].max() / 4096 <= 0.84:
                    break
                r = rng.uniform(4, 7)
                m = G.blob(n, tx * 64 + rng.uniform(4, 60), ty * 64 + rng.uniform(4, 60), r * 1.4, r * 0.7, rng.randrange(1 << 20))
                ripples_in(c, m, 0.8, rng, 4.5, 6, 11)
    despeckle(c, loose=("fine", "sand"))
    return c


_BASE_CACHE = {}


def _base_canvas(name):
    if name not in _BASE_CACHE:
        _BASE_CACHE[name] = base_pattern(name)
    return _BASE_CACHE[name]


def write_ground():
    out = []
    for name in PATTERNS:
        big = _base_canvas(name).image()
        for r in range(4):
            for col in range(4):
                out.append(save(big.crop((col * 64, r * 64, col * 64 + 64, r * 64 + 64)),
                                os.path.join(OUT, f"desert.sand.v3.{name}{r}{col}.png")))
    return out


# ------------------------------------------------------------------ flow shapes (long ripple crests)

SSET = "desert."


def flow_shape(sset, bits, variant, F=None):
    """One desert flow SHAPE tile: the plains' placement (stratified over the tile and 5 rows below it,
    inside flow_field's patch, the soft rim, rows / columns evened out, small clumps away from the edge
    removed) with long wavy RIPPLE CRESTS: a tip row (255, the crest) over a body row (214, the
    trough), 7-14 long, 2 rows, one flat grey 255 (so the tint is the colour), waving with the patch's own phase (not the plains winter's straight streaks)."""
    c = Canvas(64, 64, {"shape": [(0, 0, 0)] * 4 + [(G.SHAPE_BODY,) * 3, (234,) * 3, (G.SHAPE_TIP,) * 3]})
    seed = G.hsh(int(bits, 2), variant, 17) & 0xFFFFFF
    rng = random.Random(seed)
    if F is None:
        F = G.flow_field(bits, variant, sset=sset)
    k = c.mid("shape")
    BODY, TIP = 4, 6
    soft = F > 0.38
    if bits in G.STRAIGHT:
        core = F > 0.5
        near = core.copy()
        for _ in range(2):
            g = near.copy()
            g[1:] |= near[:-1]
            g[:-1] |= near[1:]
            g[:, 1:] |= near[:, :-1]
            g[:, :-1] |= near[:, 1:]
            near = g
        soft = soft & near

    def inside(x, y):
        xi, yi = min(63, max(0, int(x))), min(63, max(0, int(y)))
        return F[yi, xi] > 0.5 or (soft[yi, xi] and rng.random() < 0.35)
    N = 52
    perm = list(range(N))
    rng.shuffle(perm)
    pts = [((perm[i] + rng.random()) / N * 67 - 2.5, (i + rng.random()) / N * 69) for i in range(N)]
    ph = rng.uniform(0, 6.28)
    for (x, y) in pts:
        if not inside(x, min(y, 63.0)):
            continue
        ln = rng.randint(7, 14)
        for i in range(ln):
            X = int(x) + i
            Y = int(round(y + 0.9 * math.sin(ph + X * 0.33)))
            for j, t in ((0, TIP), (1, TIP)):  # one flat grey per crest (the forest's round 2 rule: no inner step)
                if 0 <= X < 64 and 0 <= Y + j < 64:
                    c.mat[Y + j, X] = k
                    c.tone[Y + j, X] = t
    ins = F > 0.5
    G.GROW_H[0] = True
    G._balance(c, ins, k, TIP, rng, 0.12)
    G._drop_small(c, 2)
    G._fill_thin(c, ins, k, TIP, rng)
    G._drop_small(c, 3)
    return c


def _with_desert_shapes(fn):
    """gen_ground_v3's straight-set widths (_middle_step) measure the DRAWN shape: use this module's
    flow_shape for the desert set (cached under its own set name)."""
    old = G.flow_shape

    def pick(sset, bits, variant, F=None):
        return (flow_shape if sset == SSET else old)(sset, bits, variant, F)
    G.flow_shape = pick
    try:
        return fn()
    finally:
        G.flow_shape = old


def write_flow():
    def go():
        out = []
        for bits in G.STORED:
            for v in range(G.n_flow_variants(bits)):
                sh = flow_shape(SSET, bits, v, F=G.flow_field(bits, v, sset=SSET))
                G._drop_small(sh, 6)  # no 4-6 texel scraps away from the edge (the forest's round 3 rule)
                out.append(save(sh, os.path.join(OUT, f"desert.sandflow.v3.{bits}.{v}.png")))
        return out
    return _with_desert_shapes(go)


def flow_tints():
    """DESERT_FLOW_TINT[kind]: d the dune's shaded lee (redder, darker), l the sunlit windward face
    (lighter, toward yellow). See DESERT.md for the measured colour differences."""
    return {"d": "#a24e3c", "l": "#b47236"}


def ground_tile(tx, ty, load=None):
    """One desert tile as the game draws it: the base, then the flow shape (flipped when flow_key says
    so) multiplied by DESERT_FLOW_TINT."""
    from PIL import Image, ImageOps
    load = load or (lambda p: Image.open(p).convert("RGBA"))
    t = load(os.path.join(OUT, f"desert.sand.v3.{G.macro_of(tx // 4, ty // 4)}{ty % 4}{tx % 4}.png")).copy()
    fk = G.flow_key(tx, ty)
    if fk:
        kind, bits, v, flip = fk
        sh = load(os.path.join(OUT, f"desert.sandflow.v3.{bits}.{v}.png"))
        if flip:
            sh = ImageOps.mirror(sh)
        t.alpha_composite(G.tinted(sh, flow_tints()[kind]))
    return t


# ------------------------------------------------------------------ transitions

def _edge_base_pick0(mask, variant):
    h = G.hsh(mask, variant, 79)
    return PATTERNS[h % 8], (h >> 3) % 4, (h >> 5) % 4


def _edge_base_table():
    """The base tile each (mask, v) is cut from. Within one mask the v's take different patterns (the
    forest's round 3 rule, inspection P3-3), and no two (mask, v) take the same tile."""
    keys = [(m, v) for m in range(1, 15) for v in range(2 if m in (6, 9) else 4)]
    used = set()
    out = {}
    for m in range(1, 15):
        pats = []
        for v in range(2 if m in (6, 9) else 4):
            p, r, c = _edge_base_pick0(m, v)
            i = PATTERNS.index(p)
            p = next(PATTERNS[(i + d) % 8] for d in range(8) if PATTERNS[(i + d) % 8] not in pats)
            for d in range(16):
                rr, cc = (r + (c + d) // 4) % 4, (c + d) % 4
                if (p, rr, cc) not in used:
                    r, c = rr, cc
                    break
            used.add((p, r, c))
            pats.append(p)
            out[(m, v)] = (p, r, c)
    assert len(out) == len(keys)
    return out


_EDGE_BASE = _edge_base_table()


def edge_base_pick(mask, variant):
    return _EDGE_BASE[(mask, variant)]


def _dist(m, steps):
    """Distance (4-neighbourhood, up to `steps`) of every texel to the True texels of m (0 on them)."""
    d = np.full(m.shape, 9)
    d[m] = 0
    for step in range(1, steps + 1):
        prev = d < step
        grow = np.zeros_like(prev)
        grow[1:, :] |= prev[:-1, :]
        grow[:-1, :] |= prev[1:, :]
        grow[:, 1:] |= prev[:, :-1]
        grow[:, :-1] |= prev[:, 1:]
        d[grow & (d == 9)] = step
    return d


def edge_overlay(mask, variant):
    """Desert sand over a lower ground (path, ruin floor): the inside is a base tile cut by the v2 curve
    at 2x (gen_ground_v3.edge_inside); a dry lip 2 texels (lit facing up / left: tones 5 / 4 of the
    fine ramp; shaded: 2 / 1... the sand's own darker tones); sand spill: 2 x 2 / 3 x 2 grains of sand
    just over the border, not on the 2 outer rows / columns (neighbouring tiles join)."""
    T = G._v2_transitions()
    F, inside = G.edge_inside(mask, variant)
    c = Canvas(64, 64, ramps_for())
    src, sr, sc = edge_base_pick(mask, variant)
    b = _base_canvas(src)
    bm = b.mat[sr * 64:sr * 64 + 64, sc * 64:sc * 64 + 64]
    bt = b.tone[sr * 64:sr * 64 + 64, sc * 64:sc * 64 + 64]
    remap = np.zeros(len(b.names), np.int16)
    for i, nm in enumerate(b.names):
        if nm is not None:
            remap[i] = c.mid(nm)
    c.mat[:] = remap[bm]
    c.tone[:] = bt
    c.mat[~inside] = 0
    kf = c.mid("fine")
    d = _dist(~inside, 3)
    for y in range(64):
        for x in range(64):
            if not inside[y, x] or d[y, x] > 2:
                continue
            gx, gy = T.gradient(mask, (x + 0.5) / 2 - 0.5, (y + 0.5) / 2 - 0.5)
            lit = (gx + gy) > 0.05
            c.mat[y, x] = kf
            c.tone[y, x] = (5 if d[y, x] == 1 else 4) if lit else (1 if d[y, x] == 1 else 2)
    do = _dist(inside, 2)
    rng = random.Random(mask * 37 + variant * 11 + 5)
    for y in range(3, 60):
        for x in range(3, 59):
            if inside[y, x] or do[y, x] != 1 or rng.random() > 0.2:
                continue
            w = rng.choice((2, 3))
            for dy in range(2):
                for dx in range(w):
                    X, Y = x + dx, y + dy
                    if 2 <= X < 62 and 2 <= Y < 62 and not inside[Y, X]:
                        c.mat[Y, X] = kf
                        c.tone[Y, X] = 4 if dy == 0 else 2
    G._fill_holes(c)
    c.mat[c.mat == c.mid("grass")] = kf  # _fill_holes fills with "grass": the desert's is the sand
    _drop_cut_pieces(c, inside)
    despeckle(c, loose=("fine", "sand"))
    return c


def _drop_cut_pieces(c, inside):
    """Pieces of the base's marks cut by the curve: a run of 1-3 texels of one colour left against the
    transparent part takes the colour of its inner neighbour (no crumbs on the border)."""
    import gen_forest_v3 as FO
    FO._drop_cut_pieces(c, inside, "summer")


def write_edges():
    out = []
    for mask in range(1, 15):
        for v in range(2 if mask in (6, 9) else 4):
            out.append(save(edge_overlay(mask, v), os.path.join(OUT, f"desert.sand.v3.edge.{mask}.{v}.png")))
    return out


def main(which):
    n = 0
    if which in ("ground", "all"):
        n += len(write_ground())
    if which in ("flow", "all"):
        n += len(write_flow())
    if which in ("edges", "all"):
        n += len(write_edges())
    if which in ("trees", "props", "all"):
        import gen_desert_flora_v3 as FL
        if which in ("trees", "all"):
            n += len(FL.write_trees())
        if which in ("props", "all"):
            n += len(FL.write_props())
    print(f"{n} files")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "all")
