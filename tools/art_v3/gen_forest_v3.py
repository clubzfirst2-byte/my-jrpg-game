"""v3 production order 7, region 1: the FOREST ground (STYLE.md 6, NAMES.md 1-3 and 5), 3 seasons.

Made the way the plains grass passed (gen_ground_v3.py), with the same rules and the same formulas:
  1. the base: 8 patterns (a .. h), each a 256 x 256 picture cut into 16 tiles
       <season.>forest.grass.v3.<m><r><c>.png        64 x 64, opaque
     the tile of world tile (tx, ty) = pattern macro_of(tx // 4, ty // 4), row ty % 4, column tx % 4
     (gen_ground_v3.macro_of, unchanged). The forest floor: moss beds and moss cushions (clusters, not
     blades), litter marks at uneven spacing -- needle sprays, twigs, cushion bumps; autumn adds fallen
     leaves (2 x 2 and 3 x 2), winter is snow with dark sprigs and snow lumps. No 1-texel dots.
  2. the flow: the same corner (Wang) scheme and the same keys rule (gen_ground_v3.flow_key: corner
     states from flow_corner, the 9 stored corner sets, mirrors drawn flipped, side states, the 1111
     variant rule). Its own SHAPE set (grey, body 214 / tip 255):
       <set.>forest.grassflow.v3.<bits>.<v>.png     set "" (summer, autumn) / "winter."
     moss cushions in summer and autumn (rounded 3-6 x 2-3 clumps, a lit top row), drift streaks in
     winter; the game multiplies them by FOREST_FLOW_TINT[season][kind].
  3. transitions: the v2 dual-grid rule (forest moss is "moss" in the v2 priority: below the plains
     grass, above path, sand, snow and ruin):
       <season.>forest.grass.v3.edge.<mask>.<v>.png  (mask 1-14, v 0-3; masks 6 / 9: 0-1)
     the moss over a lower ground: a cushion lip (lit up / left, shaded down / right) and moss tufts
     (2 x 2 to 3 x 2) over the border; winter: the snow drift lip of the plains winter edges.
     The forest / plains border is drawn by the PLAINS edges over this base (plains is higher).
Seasons: summer (v2 `moss`), autumn (v2 `autumn.moss`, fallen leaves), winter (v2 `snow`).
Run: python3 tools/art_v3/gen_forest_v3.py [ground|flow|edges|trees|props|all]
"""

import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402

import gen_ground_v3 as G  # noqa: E402  (the passed plains rules, read-only use)
from v3lib import ROOT, Canvas, despeckle, lift_ramp, save, shift  # noqa: E402

OUT = os.path.join(ROOT, "src", "art-release-v3", "terrain")
PATTERNS = G.PATTERNS
PREFIX = {"summer": "", "autumn": "autumn.", "winter": "winter."}
FLOW_SETS = {"summer": "", "autumn": "", "winter": "winter."}

GROUND = {  # v2's forest ramps (docs/art-release-v2/terrain/ramps.json), 7 tones
    "summer": ["#0c1c16", "#183426", "#1e3e31", "#244834", "#2c5336", "#345e42", "#4a7654"],
    "autumn": ["#10160e", "#232e1c", "#2a3723", "#36402a", "#434a31", "#4a5438", "#62684a"],
    "winter": ["#3a4866", "#7a8cae", "#99abc7", "#b8c8e0", "#cadbe9", "#dce6f2", "#f8fbff"],
}
NEEDLE = ["#08161a", "#123028", "#173a36", "#1c443a", "#234f3d", "#2a5a4c", "#3e7462"]  # v2 pine
BARK = ["#1e1008", "#3e2414", "#4e301c", "#5e3a22", "#6e502a", "#86603a", "#a07a50"]
LEAF_AUT = ["#4a1e0e", "#7a2e14", "#9a4018", "#b85a20", "#d07a28", "#e09a38", "#f0c060"]


def ramps_for(season):
    g = lift_ramp(GROUND[season])
    sunny = [shift(c, dh=-14 if season == "summer" else (14 if season == "autumn" else 0), ds=1.05, dv=1.08) for c in g]
    # "fine": winter's mottles step ~11 in brightness (the plains' winter rule: the snow ramp steps
    # 20-30 and reads as grain); summer and autumn moss already step ~8
    fine = G.ramps_for("winter")["fine"] if season == "winter" else list(g)
    return {"moss": g, "sunny": sunny, "needle": lift_ramp(NEEDLE), "bark": lift_ramp(BARK), "leaf": lift_ramp(LEAF_AUT),
            "fine": fine}


# ------------------------------------------------------------------ base patterns

def clumps_in(c, mask, mat, tone, density, rng, seed, n=256):
    """Moss cushions inside `mask`: rounded clumps 2-4 wide and 2-3 high (a lit top row on the lit
    side), at uneven spacing. Never a single texel."""
    ys, xs = np.nonzero(mask)
    k = c.mid(mat)
    for y, x in zip(ys, xs):
        if (x * 7 + y * 13 + G.hsh(x // 5, y // 4, seed)) % 11 or rng.random() > density:
            continue
        w, h = rng.choice(((3, 2), (4, 2), (2, 2), (4, 3), (3, 3)))
        for dy in range(h):
            for dx in range(w):
                if (dy == 0 and dx in (0, w - 1) and w >= 4):
                    continue  # rounded corners
                Y, X = y - dy, x + dx
                if 0 <= Y < n and 0 <= X < n and mask[Y, X]:
                    c.mat[Y, X] = k
                    c.tone[Y, X] = min(6, tone + 1) if (dy == h - 1 and tone < 5) else tone


def litter(c, x, y, kind, base, rng, season):
    """Forest litter marks (clipped at the picture's edge):
      0 a needle spray: 3-5 needles, 1 texel wide, 3-5 long, from one point (needle ramp)
      1 a twig: a 1-texel line 6-10 long, slanting, with a lit texel row over it (bark)
      2 a cushion bump: a 5 x 3 rounded mound, lit top, shaded under (the ground's ramp)
      3 (autumn) fallen leaves: 2-3 leaves, 2 x 2 or 3 x 2, orange to yellow
      4 (winter) a dark sprig: 3 needles 1 wide, 3-4 long, from a point; 5 (winter) a snow lump 5 x 2
    """
    x, y = int(x), int(y)
    km, kn, kb, kl = c.mid("moss"), c.mid("needle"), c.mid("bark"), c.mid("leaf")

    def put(X, Y, k, t):
        if 0 <= X < c.w and 0 <= Y < c.h:
            c.mat[Y, X], c.tone[Y, X] = k, t
    if kind == 0:
        for i in range(rng.randint(3, 5)):
            a = rng.uniform(-2.6, -0.5)
            ln = rng.randint(3, 5)
            for d in range(ln):
                put(x + int(round(math.cos(a) * d)), y + int(round(math.sin(a) * d)), kn, 5 if d == ln - 1 else 4)
    elif kind == 1:
        ln = rng.randint(6, 10)
        sl = rng.choice((-0.4, -0.25, 0.25, 0.4))
        for d in range(ln):
            X, Y = x + d, y + int(round(sl * d))
            put(X, Y, kb, 1)
            put(X, Y - 1, kb, 3 if d % 3 else 2)
    elif kind == 2:
        for dy, row in enumerate(((1, 4), (0, 5), (0, 5))):
            for dx in range(row[0], row[1]):
                put(x + dx, y + dy, km, min(6, base + 1) if dy == 0 else (base if dy == 1 else max(1, base - 1)))
    elif kind == 3:  # a loose drift of 4-7 leaves, rust to old gold (muted: tones 1-3)
        for i in range(rng.randint(4, 7)):
            X, Y = x + rng.randint(-7, 7), y + rng.randint(-4, 4)
            w = rng.choice((2, 3))
            t = rng.choice((1, 2, 2, 3))
            for dy in range(2):
                for dx in range(w):
                    put(X + dx, Y + dy, kl, t if dy == 0 else max(0, t - 1))
    elif kind == 4:
        for i in range(3):
            a = (-2.2, -1.57, -0.9)[i]
            for d in range(rng.randint(3, 4)):
                put(x + int(round(math.cos(a) * d)), y + int(round(math.sin(a) * d)), kn, 3 if d < 2 else 4)
    else:  # a soft snow mound 7 x 3: a lit top, the body, a blue shade under it
        kf = c.mid("fine")
        for dx in range(1, 6):
            put(x + dx, y, kf, 5)
        for dx in range(7):
            put(x + dx, y + 1, kf, 4 if 0 < dx < 6 else 3)
        for dx in range(1, 6):
            put(x + dx, y + 2, kf, 2)


def base_pattern(name, season, n=256):
    """The forest floor (round 1, made with the plains' passed rules): moss beds (3-4 soft patches of
    cushions that may run off the edge), 400 small mottles of cushions everywhere (up to and over the
    edge), litter marks at uneven spacing over the whole pattern and 3 texels past it, a top-up of
    marks along the 4 edges (no mark-free border band: no 256-texel grid), no calm tile (the most
    common texel of each 64 x 64 tile under 86 %)."""
    seed = 300 + PATTERNS.index(name) * 17 + {"summer": 0, "autumn": 1, "winter": 2}[season] * 1000
    rng = random.Random(seed)
    c = Canvas(n, n, ramps_for(season))
    c.fill(np.ones((n, n), bool), "moss", 3)
    mott = "fine" if season == "winter" else "moss"
    for i in range(rng.randint(3, 4)):
        r = rng.uniform(16, 28)
        m = G.blob(n, rng.uniform(0, n), rng.uniform(0, n), r, r * rng.uniform(0.6, 0.9), seed + i)
        clumps_in(c, m, mott, 2 if i % 2 == 0 else 4, 0.9, rng, seed + i)
    for i in range(400):
        r = rng.uniform(3, 7)
        cx, cy = rng.uniform(-r * 0.5, n + r * 0.5), rng.uniform(-r * 0.5, n + r * 0.5)
        m = G.blob(n, cx, cy, r, r * rng.uniform(0.5, 0.9), seed * 3 + i)
        clumps_in(c, m, mott, 2 if rng.random() < 0.6 else 4, 0.8, rng, seed * 5 + i)
    # (round 1: no twigs -- the bark-red lines read as confetti on the dark moss)
    kinds = {"summer": ((0, 2), (8, 5)), "autumn": ((0, 2, 3), (5, 3, 3)), "winter": ((5,), (1,))}[season]  # winter: snow mounds only (sprigs were trimmed to dots)

    def put_mark(x, y):
        base = int(c.tone[min(n - 1, max(0, int(y))), min(n - 1, max(0, int(x)))])
        litter(c, x, y, rng.choices(kinds[0], weights=kinds[1])[0], min(base, 4), rng, season)
    for (x, y) in G.scatter(rng, n + 6, 160 if season != "winter" else 80, 14 if season != "winter" else 20, 0):
        put_mark(x - 3, y - 3)
    for _ in range(40):  # (round 1: 26 left the border bands of some patterns at 0.7 of the middle)
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
                r = rng.uniform(3, 6)
                m = G.blob(n, tx * 64 + rng.uniform(4, 60), ty * 64 + rng.uniform(4, 60), r, r * 0.7, rng.randrange(1 << 20))
                clumps_in(c, m, mott, 2 if rng.random() < 0.6 else 4, 0.9, rng, rng.randrange(1 << 20))
    despeckle(c, loose=("moss", "fine"))
    return c


def write_ground(season):
    out = []
    for name in PATTERNS:
        big = base_pattern(name, season).image()
        for r in range(4):
            for col in range(4):
                out.append(save(big.crop((col * 64, r * 64, col * 64 + 64, r * 64 + 64)),
                                os.path.join(OUT, f"{PREFIX[season]}forest.grass.v3.{name}{r}{col}.png")))
    return out


# ------------------------------------------------------------------ flow shapes (moss cushions)

def flow_shape(sset, bits, variant, F=None):
    """One forest flow SHAPE tile: the plains' placement (stratified over the tile and 5 rows below it,
    inside flow_field's patch, the soft rim, then rows / columns evened out and small clumps away from
    the edge removed) with moss CUSHIONS (summer / autumn: rounded clumps 3-6 wide, 2-3 high, the top
    row the tip tone) or drift streaks (winter, as the plains winter set)."""
    c = Canvas(64, 64, {"shape": [(0, 0, 0)] * 4 + [(G.SHAPE_BODY,) * 3, (234,) * 3, (G.SHAPE_TIP,) * 3]})
    winter = sset.endswith("winter.")
    seed = G.hsh(int(bits, 2), variant, 15 if winter else 14) & 0xFFFFFF
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
    N = 64 if winter else 40  # round 2: fewer, bigger cushions (fewer edges: no "scribble")
    perm = list(range(N))
    rng.shuffle(perm)
    pts = [((perm[i] + rng.random()) / N * 67 - 2.5, (i + rng.random()) / N * 69) for i in range(N)]
    for (x, y) in pts:
        if not inside(x, min(y, 63.0)):
            continue
        if winter:
            ln = rng.randint(5, 8)
            for i in range(ln):
                for j in range(1 + (0 < i < ln - 1)):
                    X, Y = int(x) + i, int(y) - j
                    if 0 <= X < 64 and 0 <= Y < 64:
                        c.mat[Y, X] = k
                        c.tone[Y, X] = BODY if j == 0 else TIP
            continue
        w, h = rng.choice(((6, 3), (7, 3), (8, 4), (9, 4), (6, 4)))
        for dy in range(h):
            for dx in range(w):
                if dy == h - 1 and w >= 4 and dx in (0, w - 1):
                    continue  # the rounded top
                X, Y = int(x) + dx, int(y) - dy
                if 0 <= X < 64 and 0 <= Y < 64:
                    c.mat[Y, X] = k
                    c.tone[Y, X] = TIP  # round 2: one flat grey per cushion (no inner tip / body edge)
    ins = F > 0.5
    G.GROW_H[0] = winter
    grow = BODY if winter else TIP
    G._balance(c, ins, k, grow, rng, 0.12)
    G._drop_small(c, 2)
    G._fill_thin(c, ins, k, grow, rng)
    G._drop_small(c, 3)  # round 1: no pieces of 1-3 texels away from the tile's edge
    return c


def _with_forest_shapes(fn):
    """gen_ground_v3's straight-set widths (_middle_step) measure the DRAWN shape: use this module's
    flow_shape for the forest sets (cached under their own set names)."""
    old = G.flow_shape

    def pick(sset, bits, variant, F=None):
        return (flow_shape if sset.startswith("forest") else old)(sset, bits, variant, F)
    G.flow_shape = pick
    try:
        return fn()
    finally:
        G.flow_shape = old


def write_flow():
    def go():
        out = []
        for name, sset in (("", "forest."), ("winter.", "forest.winter.")):
            for bits in G.STORED:
                for v in range(G.n_flow_variants(bits)):
                    sh = flow_shape(sset, bits, v, F=G.flow_field(bits, v, sset=sset))
                    out.append(save(sh, os.path.join(OUT, f"{name}forest.grassflow.v3.{bits}.{v}.png")))
        return out
    return _with_forest_shapes(go)


def flow_tints(season):
    """FOREST_FLOW_TINT[season][kind] (round 2: the summer / autumn cushions are ONE flat grey, 255,
    so the shape is the tint itself; winter keeps the plains' drift streaks, body 214 / tip 255).
    Chosen so the patch reads (colour difference to the plain moss ΔE 1.4-2.4) without grain (texel
    pairs more than 15 apart in brightness: 3-5 % on full patches):
      summer d #1a382a (deep shade), l #2d5632 (a sun fleck); autumn d #4a3c20 (browner, not darker),
      l #544c28 (old gold, near the moss's brightness); winter: the plains winter tints."""
    return {"summer": {"d": "#1a382a", "l": "#2d5632"}, "autumn": {"d": "#4a3c20", "l": "#544c28"},
            "winter": {"d": "#aabcd6", "l": "#fafcff"}}[season]


def ground_tile(tx, ty, season="summer", load=None):
    """One forest tile as the game draws it: the base, then the flow shape (flipped when flow_key says
    so) multiplied by FOREST_FLOW_TINT."""
    from PIL import Image, ImageOps
    load = load or (lambda p: Image.open(p).convert("RGBA"))
    t = load(os.path.join(OUT, f"{PREFIX[season]}forest.grass.v3.{G.macro_of(tx // 4, ty // 4)}{ty % 4}{tx % 4}.png")).copy()
    fk = G.flow_key(tx, ty)
    if fk:
        kind, bits, v, flip = fk
        sh = load(os.path.join(OUT, f"{FLOW_SETS[season]}forest.grassflow.v3.{bits}.{v}.png"))
        if flip:
            sh = ImageOps.mirror(sh)
        t.alpha_composite(G.tinted(sh, flow_tints(season)[kind]))
    return t


# ------------------------------------------------------------------ transitions

_BASE_CACHE = {}


def _base_canvas(name, season):
    key = (name, season)
    if key not in _BASE_CACHE:
        _BASE_CACHE[key] = base_pattern(name, season)
    return _BASE_CACHE[key]


def edge_base_pick(mask, variant):
    """The base tile an edge's inside is cut from: (pattern, row, column), fixed per (mask, v)."""
    h = G.hsh(mask, variant, 77)
    return PATTERNS[h % 8], (h >> 3) % 4, (h >> 5) % 4


def edge_overlay(season, mask, variant):
    """Forest moss over a lower ground (the v2 curve at 2x, gen_ground_v3.edge_inside): moss with
    cushions inside, a cushion lip 3 texels (lit facing up / left: 4-5, shaded: 1-2), moss tufts
    (2 x 2 / 3 x 2) right over the border, not on the 2 outer rows / columns; winter: the plains winter
    snow with no rim and no shade line (round 2: snow meets snow, no line round the border), no tufts. In winter the game draws THIS edge over the plains snow at a forest / plains
    border (the pair's priority swapped in winter only, FOREST.md 1), so that border has no line."""
    T = G._v2_transitions()
    F, inside = G.edge_inside(mask, variant)
    c = Canvas(64, 64, ramps_for(season))
    k = c.mid("moss")
    # round 3: the inside IS a base tile (the same mottles, cushions and litter as the floor, so the
    # same amount of pattern: no flat band along the border, no step on the tile lines). The tile is
    # picked per (mask, v) from the 8 patterns x 16 tiles; it is cut by the curve, then the lip and
    # the tufts are drawn as before.
    src, sr, sc = edge_base_pick(mask, variant)
    b = _base_canvas(src, season)
    bm = b.mat[sr * 64:sr * 64 + 64, sc * 64:sc * 64 + 64]
    bt = b.tone[sr * 64:sr * 64 + 64, sc * 64:sc * 64 + 64]
    remap = np.zeros(len(b.names), np.int16)
    for i, nm in enumerate(b.names):
        if nm is not None:
            remap[i] = c.mid(nm)
    c.mat[:] = remap[bm]
    c.tone[:] = bt
    c.mat[~inside] = 0
    outside = ~inside
    d = np.full((64, 64), 9)
    d[outside] = 0
    for step in range(1, 4):
        prev = d < step
        grow = np.zeros_like(prev)
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
            if season == "winter":  # round 2: no rim at all (snow meeting snow: no line round the border);
                continue  # round 3: the base's snow pattern runs up to the cut
            c.mat[y, x] = k
            c.tone[y, x] = (5 if d[y, x] == 1 else 4) if lit else (1 if d[y, x] == 1 else 2)
    do = np.full((64, 64), 9)
    do[inside] = 0
    for step in range(1, 3):
        prev = do < step
        grow = np.zeros_like(prev)
        grow[1:, :] |= prev[:-1, :]
        grow[:-1, :] |= prev[1:, :]
        grow[:, 1:] |= prev[:, :-1]
        grow[:, :-1] |= prev[:, 1:]
        do[grow & (do == 9)] = step
    if season == "winter":
        pass  # round 2: no 1-texel blue shade outside the drift (it read as a line round the border)
    else:  # moss tufts over the border: 2 x 2 / 3 x 2 clumps whose base touches the moss
        rng = random.Random(mask * 31 + variant * 7 + len(season))
        for y in range(3, 60):
            for x in range(3, 59):
                if inside[y, x] or do[y, x] != 1 or rng.random() > 0.22:
                    continue
                w = rng.choice((2, 3))
                for dy in range(2):
                    for dx in range(w):
                        X, Y = x + dx, y + dy
                        if 2 <= X < 62 and 2 <= Y < 62 and not inside[Y, X]:
                            c.mat[Y, X] = k
                            c.tone[Y, X] = 4 if dy == 0 else 2
    kg = c.mid("grass")
    G._fill_holes(c)
    c.mat[c.mat == kg] = k  # _fill_holes fills with "grass"; the forest's is "moss"
    _drop_cut_pieces(c, inside, season)
    despeckle(c, loose=("moss", "fine"))
    return c


def _drop_cut_pieces(c, inside, season):
    """Pieces of the base's marks cut by the curve: a run of 1-3 texels of one colour left against the
    transparent part takes the colour of its inner neighbour (no crumbs on the border)."""
    H, W = c.mat.shape
    col = c.mat.astype(np.int32) * 16 + c.tone.astype(np.int32)
    seen = np.zeros((H, W), bool)
    op = c.mat != 0
    for y0 in range(H):
        for x0 in range(W):
            if not op[y0, x0] or seen[y0, x0]:
                continue
            st, comp = [(y0, x0)], []
            seen[y0, x0] = True
            while st:
                y, x = st.pop()
                comp.append((y, x))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    Y, X = y + dy, x + dx
                    if 0 <= Y < H and 0 <= X < W and op[Y, X] and not seen[Y, X] and col[Y, X] == col[y0, x0]:
                        seen[Y, X] = True
                        st.append((Y, X))
            if len(comp) > 3 or not all(inside[y, x] for y, x in comp):
                continue  # (the tufts over the border are left as drawn)
            touches_cut = any(0 <= y + dy < H and 0 <= x + dx < W and not op[y + dy, x + dx]
                              for y, x in comp for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if not touches_cut:
                continue
            nb = {}
            for y, x in comp:
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    Y, X = y + dy, x + dx
                    if 0 <= Y < H and 0 <= X < W and op[Y, X] and col[Y, X] != col[y0, x0]:
                        nb[col[Y, X]] = nb.get(col[Y, X], 0) + 1
            if nb:
                best = max(sorted(nb), key=lambda q: nb[q])
                for y, x in comp:
                    c.mat[y, x], c.tone[y, x] = best // 16, best % 16


def write_edges(season):
    out = []
    for mask in range(1, 15):
        for v in range(2 if mask in (6, 9) else 4):
            out.append(save(edge_overlay(season, mask, v),
                            os.path.join(OUT, f"{PREFIX[season]}forest.grass.v3.edge.{mask}.{v}.png")))
    return out


def main(which):
    n = 0
    seasons = list(PREFIX)
    if which in ("ground", "all"):
        for s in seasons:
            n += len(write_ground(s))
    if which in ("flow", "all"):
        n += len(write_flow())
    if which in ("edges", "all"):
        for s in seasons:
            n += len(write_edges(s))
    if which in ("trees", "props", "all"):
        import gen_forest_flora_v3 as FL
        if which in ("trees", "all"):
            n += len(FL.write_trees())
        if which in ("props", "all"):
            n += len(FL.write_props())
    print(f"{n} files")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "all")
