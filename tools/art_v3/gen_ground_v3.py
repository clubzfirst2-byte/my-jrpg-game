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

from v3lib import ROOT, Canvas, despeckle, lift_ramp, save, shift  # noqa: E402

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
    return {"grass": g, "sunny": sunny, "earth": lift_ramp(sp["earth"])}


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


def mark(c, x, y, kind, base, rng):
    """The 3 grass marks: a 3-blade tuft, a 2-blade leaning pair, a single tall blade."""
    x, y = int(x), int(y)
    if kind == 0:
        for bx, h in ((-1, 3), (0, 5), (1, 4)):
            for d in range(h):
                c.tone[y - d, x + bx] = min(5, base + 1) if d >= h - 2 else base
        c.tone[y + 1, x - 1:x + 2] = max(1, base - 1)
    elif kind == 1:
        lean = rng.choice((-1, 1))
        for bx, h in ((0, 4), (1, 3)):
            for d in range(h):
                c.tone[y - d, x + bx + (lean if d >= 2 else 0)] = min(5, base + 1) if d >= h - 2 else base
        c.tone[y + 1, x:x + 2] = max(1, base - 1)
    else:
        for d in range(6):
            c.tone[y - d, x] = min(6, base + 2) if d >= 4 else (min(5, base + 1) if d >= 2 else base)
        c.tone[y - 3, x + 1] = base


def base_pattern(name, season, n=256):
    seed = 100 + PATTERNS.index(name) * 17
    rng = random.Random(seed)
    c = Canvas(n, n, ramps_for(season))
    c.fill(np.ones((n, n), bool), "grass", 3)
    for k in range(rng.randint(3, 4)):  # medium soft patches of blades
        r = rng.uniform(16, 26)
        cx, cy = rng.uniform(r + 3, n - r - 3), rng.uniform(r + 3, n - r - 3)
        m = blob(n, cx, cy, r, r * rng.uniform(0.6, 0.9), seed + k)
        blades_in(c, m, "grass", 2 if k % 2 == 0 else 4, 0.6, rng, seed + k)
    for k in range(300):  # small mottles everywhere (to 2 texels from the edge); round 5: 70 -> 300
        r = rng.uniform(3, 7)
        cx, cy = rng.uniform(r + 2, n - r - 2), rng.uniform(r + 2, n - r - 2)
        m = blob(n, cx, cy, r, r * rng.uniform(0.5, 0.9), seed * 3 + k)
        blades_in(c, m, "grass", 2 if rng.random() < 0.6 else 4, 0.5, rng, seed * 5 + k)
    # grass marks: 3 kinds, uneven spacing (dart throwing), kept 6 texels inside the pattern
    for (x, y) in scatter(rng, n, 420, 8, 7):
        mark(c, x, y, rng.choices((0, 1, 2), weights=(5, 3, 2))[0], int(c.tone[int(y), int(x)]), rng)
    despeckle(c)
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


def flow_key(tx, ty):
    """(kind, corner bits) of tile (tx, ty), or None: corners TL, TR, BR, BL."""
    cs = [flow_corner(tx, ty), flow_corner(tx + 1, ty), flow_corner(tx + 1, ty + 1), flow_corner(tx, ty + 1)]
    kinds = {k for k in cs if k != "m"}
    if not kinds:
        return None
    kind = kinds.pop()
    bits = "".join("1" if k == kind else "0" for k in cs)
    return kind, bits


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


def flow_field(bits, variant):
    """Round 5: the corners' bilinear blend plus noise, so a patch's outline is a free curve (not the
    45-degree / square / diamond shapes of the tile geometry). The edge noise is the same in every
    flow tile (it joins), the inner noise is the variant's own and 0 on the tile's edges."""
    w = [int(b) for b in bits]  # TL, TR, BR, BL
    yy, xx = np.mgrid[0:64, 0:64]
    u, v = (xx + 0.5) / 64, (yy + 0.5) / 64
    f = w[0] * (1 - u) * (1 - v) + w[1] * u * (1 - v) + w[2] * u * v + w[3] * (1 - u) * v
    inner = np.sin(np.pi * u) * np.sin(np.pi * v)
    return f + 0.22 * _tile_noise(901) + 0.38 * inner * _tile_noise(1000 + variant * 37 + int(bits, 2))


def flow_tile(season, kind, bits, variant):
    """Round 5 (the 1a inspection): marks in BUNDLES (2-3 blades) over about 22% of a full patch,
    placed by dart throwing over the tile AND 5 rows below it (so the bottom row is as covered as the
    middle), inside a patch whose edge is a free curve (flow_field). Winter: wind-swept drift strokes
    instead of blades. Seeds are fixed numbers (the same files every run)."""
    c = Canvas(64, 64, ramps_for(season))
    seed = hsh(int(bits, 2), variant, 3 if kind == "d" else 4) & 0xFFFFFF
    rng = random.Random(seed)
    F = flow_field(bits, variant)
    mat = "grass" if kind == "d" else "sunny"
    k = c.mid(mat)

    def inside(x, y):
        xi, yi = min(63, max(0, int(x))), min(63, max(0, int(y)))
        val = F[yi, xi]
        return val > 0.5 or (val > 0.38 and rng.random() < 0.35)

    pts = []
    tries = 0
    while len(pts) < 110 and tries < 6000:  # dart throwing, spacing >= 4.5
        tries += 1
        x, y = rng.uniform(-3, 65), rng.uniform(0, 69)
        if all((x - a) ** 2 + (y - b) ** 2 >= 20 for a, b in pts):
            pts.append((x, y))
    for (x, y) in pts:
        if not inside(x, min(y, 63.0)):
            continue
        if season == "winter":  # a drift stroke: 3-5 wide, 1-2 rows, a lit or a shaded one
            ln = rng.randint(3, 5)
            for i in range(ln):
                for j in range(1 + (i > 0 and i < ln - 1)):
                    X, Y = int(x) + i, int(y) - j
                    if 0 <= X < 64 and 0 <= Y < 64:
                        c.mat[Y, X] = k
                        c.tone[Y, X] = (2 if j == 0 else 1) if kind == "d" else (6 if j == 0 else 5)
            continue
        nb = rng.choice((2, 3))
        lean = rng.choice((-1, 0, 1))
        for bi in range(nb):  # the bundle: blades 1 apart, the middle one tallest
            h = rng.randint(3, 5) + (1 if bi == 1 else 0)
            for d in range(h):
                X = int(x) + bi + (lean if d >= h - 2 else 0)
                Y = int(y) - d
                if 0 <= X < 64 and 0 <= Y < 64:
                    c.mat[Y, X] = k
                    if kind == "d":
                        c.tone[Y, X] = 1 if d < 2 else 2
                    else:
                        c.tone[Y, X] = 5 if d >= h - 2 else 4
    _balance(c, F > 0.5, k, kind, season, rng)
    despeckle(c, loose=(mat,))
    return c


def _balance(c, inside, k, kind, season, rng, tol=0.08):
    """Round 5: even out the cover so no row and no column of the patch is thinner or thicker than
    the patch as a whole (the 64-px grid of the 1a inspection came from a thin bottom row). Thin
    rows / columns get blade texels added next to existing ones (a blade grows by one), thick ones
    lose blade tips."""
    def tone_for(y, x):
        if season == "winter":
            return 2 if kind == "d" else 6
        return 2 if kind == "d" else 4
    cov = (c.mat == k) & inside
    t = cov.sum() / max(1, inside.sum())
    for _ in range(8):
        for axis in (0, 1):
            for i in range(64):
                line_in = inside[i, :] if axis == 0 else inside[:, i]
                n = line_in.sum()
                if n < 12:
                    continue
                line = (c.mat[i, :] == k) if axis == 0 else (c.mat[:, i] == k)
                have = (line & line_in).sum()
                want = t * n
                idx = [j for j in range(64) if line_in[j]]
                rng.shuffle(idx)
                if have < want * (1 - tol):
                    need = int(want - have)
                    for j in idx:
                        if need <= 0:
                            break
                        y, x = (i, j) if axis == 0 else (j, i)
                        if c.mat[y, x] == k:
                            continue
                        near = any(0 <= y + dy < 64 and 0 <= x + dx < 64 and c.mat[y + dy, x + dx] == k
                                   for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)))
                        if near or rng.random() < 0.2:
                            c.mat[y, x] = k
                            c.tone[y, x] = tone_for(y, x)
                            need -= 1
                elif have > want * (1 + tol):
                    extra = int(have - want)
                    for j in idx:
                        if extra <= 0:
                            break
                        y, x = (i, j) if axis == 0 else (j, i)
                        if c.mat[y, x] != k:
                            continue
                        top = y == 0 or c.mat[y - 1, x] != k  # a blade's tip
                        if top:
                            c.mat[y, x] = 0
                            extra -= 1


def write(season):
    pre = SEASONS[season]["prefix"]
    out = []
    for name in PATTERNS:
        big = base_pattern(name, season).image()
        for r in range(4):
            for col in range(4):
                out.append(save(big.crop((col * 64, r * 64, col * 64 + 64, r * 64 + 64)),
                                os.path.join(OUT, f"{pre}plains.grass.v3.{name}{r}{col}.png")))
    for kind in "dl":
        for i in range(1, 16):
            bits = format(i, "04b")
            for v in range(2):
                out.append(save(flow_tile(season, kind, bits, v),
                                os.path.join(OUT, f"{pre}plains.grassflow.v3.{kind}{bits}.{v}.png")))
    return out


def ground_tile(tx, ty, season="summer", load=None):
    """The picture of one ground tile, the 2 layers composed (what the game draws)."""
    from PIL import Image
    pre = SEASONS[season]["prefix"]
    load = load or (lambda p: Image.open(p).convert("RGBA"))
    t = load(os.path.join(OUT, f"{pre}plains.grass.v3.{macro_of(tx // 4, ty // 4)}{ty % 4}{tx % 4}.png")).copy()
    fk = flow_key(tx, ty)
    if fk:
        v = hsh(tx, ty, 33) % 2
        t.alpha_composite(load(os.path.join(OUT, f"{pre}plains.grassflow.v3.{fk[0]}{fk[1]}.{v}.png")))
    return t


def main(which, edges=True):
    seasons = list(SEASONS) if which == "all" else [which]
    n = 0
    for s in seasons:
        n += len(write(s))
        if edges:
            n += len(write_edges(s))
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
