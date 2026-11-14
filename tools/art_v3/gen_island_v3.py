"""v3 island grass, island sand and path (STYLE.md 6 "まだ"; DESERT.md 10): base, transitions, flow.

The same rules as the plains, forest and desert grounds (NAMES.md 1-3; gen_ground_v3, gen_forest_v3):
  base   <s.>tile.grass.v3.<m><r><c> (3 seasons), tile.sand.v3.<m><r><c>, tile.path.v3.<m><r><c>:
         8 patterns (a-h) of 256 x 256 cut into 16 tiles of 64 x 64; macro_of(tx // 4, ty // 4), ty % 4, tx % 4
  edges  <s.>tile.grass.v3.edge.<mask>.<v>, tile.sand.v3.edge.*, tile.path.v3.edge.*: the v2 dual-grid rule
         (priority ruin < path < dsand < sand < ... < grass), the v2 curve at 2x; the inside is a base tile
         (one per (mask, v), different patterns within a mask: the forest's round 3 rule)
  flow   the plains' corner scheme and flow_key, unchanged, with SHAPES that already exist (no new files):
         island grass -> <set.>plains.grassflow.v3.* (the plains' grass bundles: "" summer / autumn,
         "winter." winter); island sand and path -> forest.grassflow.v3.* (the forest's one-grey cushions),
         multiplied by ISLAND_FLOW_TINT[ground][season][kind] (flow_tints)
Island grass: a short meadow with clover carpets (the plains: tall blades). Island sand: a pale beach,
ripples, shells, pebbles. Path: packed earth, worn hollows, set pebbles, short cracks. Sand and path have
no seasons (v2 groundV2.SEASONAL).
Run: python3 tools/art_v3/gen_island_v3.py [grass|sand|path|all]
"""

import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402

import gen_forest_v3 as FO  # noqa: E402  (read-only use: _drop_cut_pieces)
import gen_ground_v3 as G  # noqa: E402  (read-only use)
from v3lib import ROOT, Canvas, despeckle, lift_ramp, luma, save  # noqa: E402

OUT = os.path.join(ROOT, "src", "art-release-v3", "terrain")
PATTERNS = G.PATTERNS
SPRE = {"summer": "", "autumn": "autumn.", "winter": "winter."}
V2 = {  # v2 ramps.json
    "sand": ["#6e5232", "#c4a26a", "#d2bf7a", "#e0c48a", "#e7d698", "#eed8a6", "#faf0d2"],
    "path": ["#3a2c1e", "#6a5238", "#7b5a44", "#8c7050", "#9a865c", "#a88c68", "#c4aa84"],
    "shell": ["#6a4a3a", "#c8987e", "#dca897", "#f0cab0", "#f5ddc0", "#fae2d0", "#fff6ee"],
    "pebble": ["#24232a", "#56545c", "#6a686e", "#807c80", "#948f8f", "#a8a29e", "#d4ccc2"],
    "clover": ["#16301c", "#2a5a30", "#346a36", "#3e7a3c", "#4e8a44", "#5e9a4c", "#7cb466"],
}


def _toward(a, b, dl):
    lo, hi = 0.0, 1.0
    for _ in range(24):
        t = (lo + hi) / 2
        m = tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))
        if abs(luma(m) - luma(a)) < dl:
            lo = t
        else:
            hi = t
    return tuple(round(a[i] + (b[i] - a[i]) * lo) for i in range(3))


def fine_of(r):
    """The base tone with its neighbours ~11 apart in brightness (the plains' "fine" rule)."""
    f = list(r)
    f[2] = _toward(r[3], r[1], 11)
    f[1] = _toward(r[3], r[1], 18)
    f[4] = _toward(r[3], r[5], 11)
    f[5] = _toward(r[3], r[6], 19)
    return f


def ramps_for(ground, season="summer"):
    if ground == "grass":
        g = G.ramps_for(season)
        clover = lift_ramp(V2["clover"]) if season == "summer" else g["fine"]
        return {"main": g["grass"], "fine": g["fine"] if season != "summer" else fine_of(g["grass"]),
                "clover": clover, "pebble": lift_ramp(V2["pebble"])}
    m = lift_ramp(V2[ground])
    return {"main": m, "fine": fine_of(m), "shell": lift_ramp(V2["shell"]), "pebble": lift_ramp(V2["pebble"])}


# ------------------------------------------------------------------ marks

def put(c, x, y, mat, t):
    if 0 <= x < c.w and 0 <= y < c.h:
        c.mat[y, x], c.tone[y, x] = c.mid(mat), t


def ripple(c, x, y, ln, slope, bow):
    for i in range(ln):
        X = int(x) + i
        Y = int(round(y + slope * i - bow * math.sin(math.pi * i / max(1, ln - 1))))
        put(c, X, Y, "fine", 4)
        put(c, X, Y + 1, "fine", 2)


def pebble(c, x, y, w, mat="pebble"):
    rows = ((1, w - 1, 5), (0, w, 3), (0, w, 2))
    for dy, (a, b, t) in enumerate(rows):
        for dx in range(a, b):
            put(c, x + dx, y + dy, mat, 4 if (dy == 1 and dx == 0) else t)
    for dx in range(1, w + 1):
        X, Y = x + dx, y + 3
        if 0 <= X < c.w and 0 <= Y < c.h and c.names[c.mat[Y, X]] not in ("pebble", "shell"):
            put(c, X, Y, "fine", 1)


def shell(c, x, y, rng):
    """A small shell 4 x 3: a lit fan top, ribs, a shaded base."""
    for dy, row in enumerate((".55.", "4554", "3443")):
        for dx, ch in enumerate(row):
            if ch != ".":
                put(c, x + dx, y + dy, "shell", int(ch) - (1 if dx == 3 and dy == 2 else 0))


def clover(c, x, y, base):
    """A clover: 3 round leaves of 2 x 2 round a dark heart (a trefoil 6 x 5)."""
    up = min(6, base + 1)
    for (dx, dy) in ((2, 0), (0, 2), (4, 2)):
        for ex in (0, 1):
            for ey in (0, 1):
                put(c, x + dx + ex, y + dy + ey, "clover", up if ey == 0 else base)
    put(c, x + 2, y + 2, "clover", max(1, base - 2))
    put(c, x + 3, y + 2, "clover", max(1, base - 1))


def hollow(c, x, y, w):
    """A worn hollow w x 3: shaded upper rows, a lit lower rim (light from the top left)."""
    for dy, (a, b, t) in enumerate(((1, w - 1, 2), (0, w, 2), (1, w - 1, 4))):
        for dx in range(a, b):
            put(c, x + dx, y + dy, "fine", t)


def crack(c, x, y, ln, rng):
    for i in range(ln):
        X, Y = x + i, y + (1 if (i // 3) % 2 else 0)
        put(c, X, Y, "fine", 1)
        put(c, X, Y + 1, "fine", 4)


def mark(c, ground, season, x, y, rng):
    x, y = int(x), int(y)
    if ground == "grass":
        if season == "winter":
            FO.litter(c, x, y, 5, 3, rng, "winter") if "fine" in c.names else None
            return
        k = rng.choices((0, 1, 2), weights=(5, 3, 2))[0]
        if k == 2:
            clover(c, x, y, 3)
        else:
            G.mark(c, x, y, k, 3, rng, lo=2, hi=5, k=c.mid("fine"))
    elif ground == "sand":
        k = rng.choices((0, 1, 2), weights=(7, 2, 1))[0]
        if k == 0:
            ripple(c, x, y, rng.randint(6, 11), rng.uniform(-0.12, 0.12), rng.uniform(-1.0, 1.0))
        elif k == 1:
            shell(c, x, y, rng)
        else:
            pebble(c, x, y, rng.choice((3, 4)))
    else:
        k = rng.choices((0, 1, 2), weights=(5, 1, 3))[0]
        if k == 0:
            hollow(c, x, y, rng.randint(5, 8))
        elif k == 1:
            pebble(c, x, y, rng.choice((3, 4)))
        else:
            crack(c, x, y, rng.randint(5, 9), rng)


# ------------------------------------------------------------------ base

def base_pattern(ground, name, season="summer", n=256):
    """The plains' passed construction: patches (3-4, may run off the edge), 400 small mottles up to and
    over the edge, marks at uneven spacing over the whole pattern and 3 texels past it and along the 4
    edges, then every border band (outer 6 rows / columns) topped up to 0.88 of the middle's marks, no
    calm tile over 84 %, despeckle."""
    seed = {"grass": 900, "sand": 1100, "path": 1300}[ground] + PATTERNS.index(name) * 29 + \
        {"summer": 0, "autumn": 1, "winter": 2}[season] * 1000
    rng = random.Random(seed)
    c = Canvas(n, n, ramps_for(ground, season))
    c.fill(np.ones((n, n), bool), "main", 3)
    for i in range(rng.randint(3, 4)):  # patches
        r = rng.uniform(16, 28)
        m = G.blob(n, rng.uniform(0, n), rng.uniform(0, n), r, r * rng.uniform(0.55, 0.85), seed + i)
        tone = 2 if i % 2 == 0 else 4
        if ground == "grass" and season != "winter":
            G.blades_in(c, m, "fine", tone, 0.6, rng, seed + i)
            if i % 2:  # a clover carpet
                ys, xs = np.nonzero(m)
                for j in range(0, len(ys), max(1, len(ys) // 30)):
                    clover(c, xs[j] - 3, ys[j] - 2, 3)
        else:
            k = c.mid("fine")
            for y, x in zip(*np.nonzero(m)):
                if (x * 5 + y * 11 + G.hsh(x // 4, y // 3, seed)) % 7 == 0 and rng.random() < 0.7:
                    for dx in range(rng.choice((2, 3))):
                        if x + dx < n and m[y, x + dx]:
                            c.mat[y, x + dx], c.tone[y, x + dx] = k, tone
    for i in range(400):  # small mottles
        r = rng.uniform(3, 7)
        cx, cy = rng.uniform(-r * 0.5, n + r * 0.5), rng.uniform(-r * 0.5, n + r * 0.5)
        m = G.blob(n, cx, cy, r * 1.2, r * rng.uniform(0.5, 0.85), seed * 3 + i)
        tone = 2 if rng.random() < 0.6 else 4
        if ground == "grass":
            G.blades_in(c, m, "fine", tone, 0.5, rng, seed * 5 + i)
        else:
            k = c.mid("fine")
            for y, x in zip(*np.nonzero(m)):
                if (x * 3 + y * 7 + G.hsh(x // 3, y // 2, seed + i)) % 9 == 0:
                    for dx in range(2):
                        if x + dx < n and m[y, x + dx]:
                            c.mat[y, x + dx], c.tone[y, x + dx] = k, tone

    def put_mark(x, y):
        mark(c, ground, season, x, y, rng)
    count, gap = (80, 20) if (ground == "grass" and season == "winter") else ((220, 11) if ground != "grass" else (330, 9))
    for (x, y) in G.scatter(rng, n + 6, count, gap, 0):
        put_mark(x - 3, y - 3)
    for _ in range(20):
        side = rng.randrange(4)
        a, b = rng.uniform(0, n), rng.uniform(-1, 9)
        put_mark(*{0: (a, b + 4), 1: (a, n - b + 3), 2: (b - 1, a), 3: (n - b - 6, a)}[side])
    for ty in range(n // 64):
        for tx in range(n // 64):
            for _ in range(30):
                rgb = c.rgba()[ty * 64:ty * 64 + 64, tx * 64:tx * 64 + 64, :3].astype(np.int64)
                key = (rgb[..., 0] << 16) | (rgb[..., 1] << 8) | rgb[..., 2]
                if np.unique(key, return_counts=True)[1].max() / 4096 <= 0.84:
                    break
                put_mark(tx * 64 + rng.uniform(4, 54), ty * 64 + rng.uniform(4, 58))

    def marked():
        k = c.rgba()[..., :3].astype(np.int64)
        k = (k[..., 0] << 16) | (k[..., 1] << 8) | k[..., 2]
        v, cnt = np.unique(k, return_counts=True)
        return k != v[np.argmax(cnt)]
    for side in range(4):
        for _ in range(60):
            mk = marked()
            mid = mk[12:-12, 12:-12].mean()
            band = (mk[:6], mk[-6:], mk[:, :6], mk[:, -6:])[side].mean()
            if band >= 0.88 * mid:
                break
            a, b = rng.uniform(-8, n), rng.uniform(0, 5)
            put_mark(*{0: (a, b), 1: (a, n - 6 + b), 2: (b - 3, a), 3: (n - 9 + b, a)}[side])
    despeckle(c, loose=("fine", "main"), keep=("clover", "shell", "pebble"))
    return c


_BASE = {}


def base_canvas(ground, name, season="summer"):
    key = (ground, name, season)
    if key not in _BASE:
        _BASE[key] = base_pattern(ground, name, season)
    return _BASE[key]


def seasons_of(ground):
    return ("summer", "autumn", "winter") if ground == "grass" else ("summer",)


def prefix(ground, season):
    return f"{SPRE[season] if ground == 'grass' else ''}tile.{ground}.v3"


def write_base(ground):
    out = []
    for season in seasons_of(ground):
        for name in PATTERNS:
            big = base_canvas(ground, name, season).image()
            for r in range(4):
                for col in range(4):
                    out.append(save(big.crop((col * 64, r * 64, col * 64 + 64, r * 64 + 64)),
                                    os.path.join(OUT, f"{prefix(ground, season)}.{name}{r}{col}.png")))
    return out


# ------------------------------------------------------------------ edges

def _pick0(ground, mask, v):
    h = G.hsh(mask, v, {"grass": 83, "sand": 85, "path": 87}[ground])
    return PATTERNS[h % 8], (h >> 3) % 4, (h >> 5) % 4


def edge_table(ground):
    used, out = set(), {}
    for m in range(1, 15):
        pats = []
        for v in range(2 if m in (6, 9) else 4):
            p, r, c = _pick0(ground, m, v)
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
    return out


def _dist(m, steps):
    d = np.full(m.shape, 9)
    d[m] = 0
    for step in range(1, steps + 1):
        prev = d < step
        g = np.zeros_like(prev)
        g[1:] |= prev[:-1]
        g[:-1] |= prev[1:]
        g[:, 1:] |= prev[:, :-1]
        g[:, :-1] |= prev[:, 1:]
        d[g & (d == 9)] = step
    return d


def edge_overlay(ground, season, mask, v, table):
    """The ground over a lower one: the inside a base tile cut by the v2 curve at 2x; the lip:
    grass  a turf edge 3 texels (lit facing up / left, shaded otherwise) and blades 2-6 texels over the
           border (winter: a rounded snow lip, its lit rim, no blades)
    sand   a dry lip 2 texels and sand spill (2 x 2 / 3 x 2) just over the border
    path   a trodden darker edge 2 texels (the v2 path's dark rim) and a few pebbles just over it
    nothing on the 2 outer rows / columns outside the curve (neighbouring tiles join)."""
    T = G._v2_transitions()
    F, inside = G.edge_inside(mask, v)
    c = Canvas(64, 64, ramps_for(ground, season))
    src, sr, sc = table[(mask, v)]
    b = base_canvas(ground, src, season)
    remap = np.zeros(len(b.names), np.int16)
    for i, nm in enumerate(b.names):
        if nm is not None:
            remap[i] = c.mid(nm)
    c.mat[:] = remap[b.mat[sr * 64:sr * 64 + 64, sc * 64:sc * 64 + 64]]
    c.tone[:] = b.tone[sr * 64:sr * 64 + 64, sc * 64:sc * 64 + 64]
    c.mat[~inside] = 0
    km, kf = c.mid("main"), c.mid("fine")
    d = _dist(~inside, 3)
    rim = 3 if ground == "grass" else 2
    winter = ground == "grass" and season == "winter"
    for y in range(64):
        for x in range(64):
            if not inside[y, x] or d[y, x] > rim:
                continue
            gx, gy = T.gradient(mask, (x + 0.5) / 2 - 0.5, (y + 0.5) / 2 - 0.5)
            lit = (gx + gy) > 0.05
            if ground == "path":
                c.mat[y, x], c.tone[y, x] = km, (1 if d[y, x] == 1 else 2)
            elif winter:
                c.mat[y, x], c.tone[y, x] = km, ((6 if d[y, x] == 1 else 5) if lit else (3 if d[y, x] == 1 else 4))
            else:
                c.mat[y, x], c.tone[y, x] = (km if ground == "grass" else kf), \
                    ((4 if d[y, x] == 1 else 3) if lit else (1 if d[y, x] == 1 else 2)) if ground == "grass" else \
                    ((5 if d[y, x] == 1 else 4) if lit else (1 if d[y, x] == 1 else 2))
    do = _dist(inside, 2)
    rng = random.Random(mask * 41 + v * 13 + {"grass": 1, "sand": 2, "path": 3}[ground] + len(season))
    for y in range(3, 60):
        for x in range(3, 59):
            if inside[y, x] or do[y, x] != 1:
                continue
            if ground == "grass" and not winter and rng.random() < 0.4:
                gx, gy = T.gradient(mask, (x + 0.5) / 2 - 0.5, (y + 0.5) / 2 - 0.5)
                step = -1 if gy >= 0 else 1
                h = rng.randint(2, 6)
                for i in range(h):
                    Y = y + step * i
                    if 2 <= Y < 62 and not inside[Y, x]:
                        c.mat[Y, x], c.tone[Y, x] = km, ((5 if i >= h - 2 else 4) if step < 0 else (2 if i >= h - 2 else 3))
            elif ground == "sand" and rng.random() < 0.2:
                for dy in range(2):
                    for dx in range(rng.choice((2, 3))):
                        X, Y = x + dx, y + dy
                        if 2 <= X < 62 and 2 <= Y < 62 and not inside[Y, X]:
                            c.mat[Y, X], c.tone[Y, X] = kf, (4 if dy == 0 else 2)
            elif ground == "path" and rng.random() < 0.05:
                if 3 <= x < 56 and 3 <= y < 56 and not inside[y:y + 4, x:x + 5].any():
                    pebble(c, x, y + 1, 3)
    G._fill_holes(c)
    c.mat[c.mat == c.mid("grass")] = km if ground == "grass" else kf
    FO._drop_cut_pieces(c, inside, "summer")
    despeckle(c, loose=("fine", "main"), keep=("clover", "shell", "pebble"))
    return c


def write_edges(ground):
    out = []
    table = edge_table(ground)
    for season in seasons_of(ground):
        for m in range(1, 15):
            for v in range(2 if m in (6, 9) else 4):
                out.append(save(edge_overlay(ground, season, m, v, table),
                                os.path.join(OUT, f"{prefix(ground, season)}.edge.{m}.{v}.png")))
    return out


# ------------------------------------------------------------------ flow (existing shapes, own tints)

FLOW_SHAPES = {"grass": ("plains.grassflow.v3", {"summer": "", "autumn": "", "winter": "winter."}),
               "sand": ("forest.grassflow.v3", {"summer": ""}),
               "path": ("forest.grassflow.v3", {"summer": ""})}


def flow_tints(ground, season="summer"):
    """ISLAND_FLOW_TINT[ground][season][kind] (chosen by looking at the 10 / 12 / 14 / 15 numbers and the
    pictures, DESERT.md 10)."""
    return {
        ("grass", "summer"): {"d": "#3a6a3a", "l": "#5e8c44"},
        ("grass", "autumn"): {"d": "#82602e", "l": "#a69240"},
        ("grass", "winter"): {"d": "#b4c4dc", "l": "#f4f8fe"},
        ("sand", "summer"): {"d": "#d4b47c", "l": "#ead4a2"},
        ("path", "summer"): {"d": "#7e6448", "l": "#9a8260"},
    }[(ground, season)]


def ground_tile(ground, tx, ty, season="summer", load=None):
    from PIL import Image, ImageOps
    load = load or (lambda p: Image.open(p).convert("RGBA"))
    t = load(os.path.join(OUT, f"{prefix(ground, season)}.{G.macro_of(tx // 4, ty // 4)}{ty % 4}{tx % 4}.png")).copy()
    fk = G.flow_key(tx, ty)
    if fk:
        kind, bits, v, flip = fk
        name, sets = FLOW_SHAPES[ground]
        sh = load(os.path.join(OUT, f"{sets[season]}{name}.{bits}.{v}.png"))
        if flip:
            sh = ImageOps.mirror(sh)
        t.alpha_composite(G.tinted(sh, flow_tints(ground, season)[kind]))
    return t


def main(which="all"):
    n = 0
    for ground in (("grass", "sand", "path") if which == "all" else (which,)):
        n += len(write_base(ground)) + len(write_edges(ground))
    print(f"{n} files")


if __name__ == "__main__":
    main(*(sys.argv[1:] or ["all"]))
