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
    # the sunny grass: tones 4-6 a little toward yellow-green, a little brighter
    sunny = [shift(c, dh=-14, ds=1.05, dv=1.05) for c in g]
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
    for k in range(70):  # small mottles everywhere (to 2 texels from the edge)
        r = rng.uniform(3, 7)
        cx, cy = rng.uniform(r + 2, n - r - 2), rng.uniform(r + 2, n - r - 2)
        m = blob(n, cx, cy, r, r * rng.uniform(0.5, 0.9), seed * 3 + k)
        blades_in(c, m, "grass", 2 if rng.random() < 0.6 else 4, 0.5, rng, seed * 5 + k)
    # grass marks: 3 kinds, uneven spacing (dart throwing), kept 6 texels inside the pattern
    for (x, y) in scatter(rng, n, 300, 9, 7):
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


def flow_tile(season, kind, bits, variant):
    """One flow tile: blades whose density follows the 4 corners (bilinear), 0.75 at a full corner."""
    c = Canvas(64, 64, ramps_for(season))
    rng = random.Random(hash((kind, bits, variant)) & 0xFFFF)
    w = [int(b) for b in bits]  # TL, TR, BR, BL
    yy, xx = np.mgrid[0:64, 0:64]
    u, v = (xx + 0.5) / 64, (yy + 0.5) / 64
    d = (w[0] * (1 - u) * (1 - v) + w[1] * u * (1 - v) + w[2] * u * v + w[3] * (1 - u) * v)
    # ragged: the density wobbles with a fixed 3 x 3-texel scatter, so the patch edge is not a diagonal
    jit = np.vectorize(lambda x, y: (hsh(x // 3, y // 3, variant * 7 + len(bits)) % 1000) / 1000.0)(xx, yy)
    d = np.clip(d * (0.55 + 0.9 * jit) - 0.08, 0, 1)
    d = d * d * (3 - 2 * d) * 0.55
    mat = "grass" if kind == "d" else "sunny"
    k = c.mid(mat)
    for y in range(64):
        for x in range(64):
            if hsh(x, y, variant + 3) % 3 or rng.random() >= d[y, x]:
                continue
            t = (1 if rng.random() < 0.35 * d[y, x] / 0.55 else 2) if kind == "d" else \
                (5 if rng.random() < 0.4 * d[y, x] / 0.55 else 4)
            for dd in range(rng.randint(2, 4)):
                if y - dd >= 0:
                    c.mat[y - dd, x] = k
                    c.tone[y - dd, x] = t
    return c


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
    return c


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
