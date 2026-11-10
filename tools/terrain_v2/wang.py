"""Ground v2, round 2: edge-matched (Wang) ground tiles, so the ground does not repeat every 32 px.

Every display tile edge has a TYPE, 0 or 1, decided by the engine from a hash of the edge (NAMES.md).
What crosses an edge depends only on the edge's type, so two tiles that share an edge always agree, and
a tile is chosen by its 4 edge types:

    index n = N + 2 E + 4 S + 8 W   (N = type of the top edge, E right, S bottom, W left)  ->  <prefix>.<n>, n = 0-15

The patterns therefore run ACROSS tile edges (a swale, a clump, a ripple, a drift, a paving joint
continues into the next tile) and the same tile is rarely beside itself, so there is no 32-px lattice.
`.0` (all edges type 0) is the calm base: no marks of its own (grass, moss, path) — or, where the ground
is all texture (sand / snow ripples, ruin paving), the lines that every tile continues.

Macro pieces (2x2 `.macro` and `.macro2`, 3x3 `.macro3`) are drawn on one canvas with type-0 outer edges,
so the engine forces the edges around a macro block to type 0.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from canvas import Canvas  # noqa: E402
import marks as M  # noqa: E402

N, E, S, W = 1, 2, 4, 8
AY, AX = 13, 19  # where a type-1 feature crosses a vertical / a horizontal edge (off-centre on purpose)
# Probability (%) that an edge is type 1, per ground look (NAMES.md). Grass-like grounds are mostly calm.
P_TYPE1 = {"grass": 22, "plains": 10, "lake": 10, "moss": 12, "path": 10, "snow": 50, "sand": 50, "dsand": 50, "ruin": 25}


# Round 3: edge-type alphabets per ground.
#   grass, plains, lake, moss, path:  N, E, S, W in {0, 1}         n = N + 2E + 4S + 8W        (16 tiles)
#   sand, desert, snow (and the winter of the grass-likes, which is snow): only the W / E edges carry anything
#   (the ripples / ridges crossing them), at 8 phases:  E, W in 0-7   n = E + 8W   (64 tiles)
#   ruin: straight stone courses 11 px high across the whole map. A tile is picked by its ROW phase
#   R = (32 * j) mod 11 (0-10: where the courses' joints are in that row of tiles) and by the symbols (0-2) of
#   its west and east edges, which are a function of the COLUMN only and always differ:
#   n = 6R + 2W + (E if E < W else E - 1)   (66 tiles)
# With 8 phases (11 for the ruin) every row of a tile is equally likely to carry a ripple / ridge / joint, so
# the rows' mean brightness has no 32-px period.
LINE_GROUNDS = {"sand", "dsand"}  # (round 4: snow is drawn like the grass-likes, macro_a.py)
TEX4 = LINE_GROUNDS | {"ruin"}  # the all-texture grounds: no macro pieces, their own edge alphabets
RUIN_COMBOS = [(w, e) for w in range(3) for e in range(3) if w != e]  # index 2w + (e if e < w else e - 1)


def tile_count(ground):
    return 64 if ground in LINE_GROUNDS else 66 if ground == "ruin" else 16


def types_of(n, ground=None):
    if ground in LINE_GROUNDS:
        return {N: 0, E: n % 8, S: 0, W: n // 8}
    if ground == "ruin":
        w, e = RUIN_COMBOS[n % 6]
        return {N: 0, E: e, S: 0, W: w, "R": n // 6}
    return {N: n & 1, E: (n >> 1) & 1, S: (n >> 2) & 1, W: (n >> 3) & 1}


def index_of(t, ground=None):
    if ground in LINE_GROUNDS:
        return t[E] + 8 * t[W]
    if ground == "ruin":
        return 6 * t["R"] + RUIN_COMBOS.index((t[W], t[E]))
    return t[N] + 2 * t[E] + 4 * t[S] + 8 * t[W]


def ruin_row(j):
    """The ruin row phase of display-tile row j: (32 j) mod 11."""
    return (10 * j) % 11


def ruin_symbol(i, hash2):
    """The symbol (0-2) of the vertical line of tile edges at the west of display-tile column i; neighbouring
    lines never have the same symbol. hash2 = gameView's hash(a, b)."""
    k = i // 2
    e0, e1 = hash2(k, 7) % 3, hash2(k + 1, 7) % 3
    if i % 2 == 0:
        return e0
    return 3 - e0 - e1 if e0 != e1 else (e0 + 1 + hash2(k, 11) % 2) % 3


def edge_origin(side, ox=0, oy=0):
    return {W: (ox, oy + AY), E: (ox + 32, oy + AY), N: (ox + AX, oy), S: (ox + AX, oy + 32)}[side]


def patch(c, mat, cx, cy, rx, ry, tone, seed=0, rot=0.0, wobble=0.6, rim=False):
    M.fill_patch(c, mat, M.patch_pixels(cx, cy, rx, ry, seed, rot, wobble), tone, rim=rim)


# ------------------------------------------------------------------------------------------------------
# What a type-1 edge carries, per ground family. (ex, ey) = the crossing point; vertical = a W / E edge.
# ------------------------------------------------------------------------------------------------------
def grass_edge(c, mat, ex, ey, vertical, ground):
    if vertical:
        patch(c, mat, ex, ey, 5, 6.5, 2, seed=301, rot=0.2)  # a darker swale across the edge
        M.draw_clump(c, mat, ex - 1, ey + 3, "M" if ground != "plains" else "W")
        c.stamp(ex + 2, ey - 5, M.CLOVER, mat)
    else:
        patch(c, mat, ex, ey, 8, 4, 4, seed=302, rot=-0.15)  # a sunlit strip across the edge
        M.draw_clump(c, mat, ex + 3, ey + 2, "S")
        M.draw_clump(c, mat, ex - 4, ey - 1, "S")


def moss_edge(c, mat, ex, ey, vertical, ground):
    if vertical:
        patch(c, mat, ex, ey, 5, 7, 4, seed=311, rot=0.1, rim=True)  # a moss bed across the edge
        c.stamp(ex - 2, ey + 5, M.NEEDLES, "pine")
    else:
        patch(c, mat, ex, ey, 8, 4, 2, seed=312)  # a damp hollow
        c.stamp(ex + 1, ey - 3, M.TWIG, "bark")


def path_edge(c, mat, ex, ey, vertical, ground):
    if vertical:
        patch(c, mat, ex, ey, 5, 7, 4, seed=321, rot=0.3)  # a worn, lighter stretch
        c.stamp(ex - 1, ey + 3, M.PEBBLE_M, "pebble")
    else:
        patch(c, mat, ex, ey, 8, 4, 2, seed=322)  # a damper, darker stretch
        c.stamp(ex + 3, ey - 1, M.PEBBLE_S, "pebble")


EDGE = {"grass": grass_edge, "plains": grass_edge, "lake": grass_edge, "moss": moss_edge, "path": path_edge}

# Sand ripples / snow ridges cross the W / E edges at these rows, per edge type (8 phases). Sand: an 8-px
# spacing, so every row 0-31 is a crest in exactly one phase; snow: the same rows, but each ridge is drawn in
# dashes (7 px on, 9 off, placed by its edge row), so the snow stays mostly open.
LINES = {"sand": {p: [p, p + 8, p + 16, p + 24] for p in range(8)}, "dsand": {p: [p, p + 8, p + 16, p + 24] for p in range(8)},
         "snow": {p: [p, p + 8, p + 16, p + 24] for p in range(8)}}


def _smooth(t):
    return t * t * (3 - 2 * t)


def _pair(left, right):
    """Join each line on the W edge to the nearest one on the E edge (all shifted the same way, so they never
    cross). A line without a partner heads for where the next line would be, outside the tile (it runs out
    through the top / bottom edge and stops there)."""
    gap = left[1] - left[0]
    s = min((-1, 0, 1), key=lambda k: abs(left[0] - (right[0] + k * gap)))
    out = []
    for k in range(-2, len(left) + 2):
        out.append((left[0] + k * gap, right[0] + (k + s) * gap))
    return out


SWELL = [-5, 3, 0, 5, -3, 4, -2, 2]  # px: how far a tile's bundle of lines swells up / down, by (E phase - W phase) mod 8
BEND = [16, 9, 22, 13, 19, 8, 23, 11]  # the column around which the lines go from their W rows to their E rows, by the same
PEAK = [1.0, 0.6, 1.5, 0.8, 1.3, 0.55, 1.7, 0.7]  # where the swell peaks (exponent on the 0-1 run across the tile)

# Round 4. What a ridge / ripple carries besides its crest, by the parity (snow) or the residue mod 4 (sand) of
# its edge row h, as (dy, first k, last k, tone) with k = (x + 11 h) mod 16 along the line. All spans have even
# lengths (snow) / lengths 4 or 8 (sand), so over the edge rows of a class every column gets the same amount;
# the snow classes are balanced so that even and odd rows get the same brightness.
SNOW_PARTS = {
    0: [(0, 0, 7, 4), (1, 1, 6, 2), (0, 2, 5, 5), (-1, 0, 7, 4), (-1, 3, 4, 5), (-2, 2, 5, 4)],  # a drift: a bright face over the ridge
    1: [(0, 0, 7, 4), (1, 1, 6, 2), (2, 3, 6, 2), (2, 4, 5, 1), (3, 3, 6, 2)],  # a blue hollow under the ridge, a deep core
}
SAND_PARTS = {
    0: [(0, 0, 15, 4), (1, 0, 15, 2)],
    1: [(0, 0, 15, 4), (1, 0, 15, 2), (-1, 0, 7, 4), (-2, 1, 6, 4)],  # the lit windward face of a low dune (as in round 3)
    2: [(0, 0, 15, 4), (1, 0, 15, 2)],
    3: [(0, 0, 15, 4), (1, 0, 15, 2)],
}


def draw_lines(c, ground, mat, ox, oy, tw, te, idx):
    """Ripples / ridges from the W edge rows to the E edge rows. All lines of a tile bend, swell and wave together
    (so they never cross), by a shape that depends only on the difference of its two edge phases and is 0 at
    both ends, and every pixel's tone is a function of the line's own edge row and its x: so a tile's edge
    columns depend only on its edge types, and over the tile set every row and every column carries the same
    amount of everything (no 32-px bands)."""
    d = (te - tw) % 8
    snow = ground == "snow"
    parts = SNOW_PARTS if snow else SAND_PARTS
    todo = []
    for yl, yr in _pair(LINES[ground][tw], LINES[ground][te]):
        for x in range(32):
            wv = min(1.0, max(0.0, (x - 2) / 27))
            wave = (SWELL[d] * math.sin(math.pi * wv ** PEAK[d]) * (0.4 if snow else 1.0)
                    + 0.8 * math.sin(2 * math.pi * wv) * math.cos(2.3 * d + 0.4))
            t = min(1.0, max(0.0, (x - (BEND[d] - 8)) / 16))
            y = round(yl + (yr - yl) * _smooth(t) + wave)
            h = yl if x < 16 else yr  # keyed to the line's own edge row on that side
            k = (x + (11 if snow else 7) * h) % 16
            for dy, k0, k1, tone in parts[h % (2 if snow else 4)]:
                if k0 <= k <= k1:
                    todo.append((5 if dy in (0, 1) else 1, x, y + dy, tone))
            if snow and h % 8 == 2 and k in (3, 4):
                todo.append((9, x, y - 1, 6))  # a sparkle on some drifts
            if not snow:
                if (x + 3 * h) % 16 < 2:
                    todo.append((8, x, y, 5))  # a brighter run on the crest
                if (x + 5 * h + 6) % 16 < 2:
                    todo.append((8, x, y + 1, 1))  # a deeper run in the trough
    for _, x, y, tone in sorted(todo, key=lambda v: v[0]):  # faces and hollows first, then crests, then the runs
        if 0 <= y <= 31:
            c.put(ox + x, oy + y, mat, tone)


# ------------------------------------------------------------------------------------------------------
# Ruin paving (round 3): rectangular stones in straight COURSES 11 px high (1 joint row + 10 stone rows) that
# run across the whole map; the joints of a course are staggered against the course above.
#   - 11 does not divide 32, so a row of tiles has one of 11 phases R = (32 j) mod 11, and every row of a
#     tile is a joint in exactly one of them (no 32-px bands);
#   - there are 32 different courses G (352 px = 11 tiles = 32 courses); ruin_layout.py holds, per course and
#     edge symbol, where the stone that crosses a tile edge has its joints, searched so that the vertical
#     joints fall evenly on all 32 columns for every (west, east) pair of symbols.
# Joints are tone 1 (never 0); every stone is lit on its top row and left column (4, the corner 5) and shaded
# on its bottom row and right column (2). Some stones are worn (lit specks), pitted, cracked or mossy, by a
# hash of the stone, so a stone cut by a tile edge is the same stone in both tiles.
# ------------------------------------------------------------------------------------------------------
def _h(*vals):
    h = 2166136261
    for v in vals:
        h = ((h ^ (v & 0xFFFF)) * 16777619) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return h ^ (h >> 16)


def ruin_joints(G, w, e):
    """The columns of the vertical joints of course G in a tile with symbols (w, e), from -A (in the tile on
    the left) to 32 + B (in the tile on the right), and the id of the stone right of each joint."""
    from ruin_layout import A, B, D

    l, r = B[G][w], 32 - A[G][e]
    xs = [(-A[G][w], ("x", G, w)), (l, ("m", G, w, e, 0))]
    if r - l >= 21:
        xs.append((l + (r - l) // 2 + D[G], ("m", G, w, e, 1)))
    xs += [(r, ("x", G, e)), (32 + B[G][e], None)]
    return xs


def draw_ruin(c, mat, ox, oy, R, w, e):
    top = 32 * ((10 * R) % 11)  # the y of this tile's top in the 352-px cycle of courses

    def course(y):
        return ((top + y) // 11) % 32, (top + y) % 11

    cols = {}

    def joint(x, y):
        G, k = course(y)
        if k == 0:
            return True
        if G not in cols:
            cols[G] = {x for x, _ in ruin_joints(G, w, e)}
        return x in cols[G]

    for y in range(32):
        for x in range(32):
            if joint(x, y):
                c.put(ox + x, oy + y, mat, 1)
            elif joint(x, y - 1) and joint(x - 1, y):
                c.put(ox + x, oy + y, mat, 5)
            elif joint(x, y - 1) or joint(x - 1, y):
                c.put(ox + x, oy + y, mat, 4)
            elif joint(x, y + 1) or joint(x + 1, y):
                c.put(ox + x, oy + y, mat, 2)
    seen = set()
    for y in range(32):
        G, k = course(y)
        if G in seen:
            continue
        seen.add(G)
        y0 = y - k  # the course's joint row (may be above the tile)
        xs = ruin_joints(G, w, e)
        for (x0, sid), (x1, _) in zip(xs, xs[1:]):
            draw_stone(c, mat, ox, oy, x0, y0, x1 - x0, _h(*[v if isinstance(v, int) else ord(v) for v in sid], 77))


def draw_stone(c, mat, ox, oy, x0, y0, wd, h):
    """The face of one stone (joint column x0, joint row y0; its face is x0+1 .. x0+wd-1, y0+1 .. y0+10)."""
    def put(dx, dy, tone, m=None):
        x, y = x0 + dx, y0 + dy
        if 0 <= x < 32 and 0 <= y < 32 and (m or (2 <= dx <= wd - 2 and 2 <= dy <= 9)):
            c.put(ox + x, oy + y, m or mat, tone)

    style = h % 16
    r = h >> 4
    if style in (4, 5, 6):  # worn: a few lit specks
        for k in range(2 + style % 2):
            dx, dy = 3 + (r >> (5 * k)) % max(1, wd - 6), 3 + (r >> (5 * k + 3)) % 6
            put(dx, dy, 4)
            put(dx + 1, dy, 4)
    elif style in (7, 8):  # pitted: small dark pits
        for k in range(2 + style % 2):
            dx, dy = 3 + (r >> (5 * k)) % max(1, wd - 6), 3 + (r >> (5 * k + 2)) % 6
            put(dx, dy, 2)
            if k == 0:
                put(dx + 1, dy + 1, 2)
    elif style == 9 and wd >= 12:  # a hairline crack from the top edge
        dx = 4 + r % (wd - 8)
        for k, (ddx, ddy) in enumerate([(0, 1), (0, 2), (1, 3), (1, 4), (2, 5), (3, 5), (3, 6)][:4 + r % 4]):
            put(dx + ddx, ddy, 2, mat)
    elif style == 10:  # moss in the joint at the foot of the stone
        dx = 1 + r % max(1, wd - 6)
        for ddx, ddy, tn in [(1, 9, 4), (2, 9, 5), (0, 10, 3), (1, 10, 4), (2, 10, 4), (3, 10, 3), (4, 10, 2), (1, 11, 2), (2, 11, 2)]:
            put(dx + ddx, ddy, tn, "moss")


# ------------------------------------------------------------------------------------------------------
# Interior marks per tile index (kept 5 px inside so they never meet an edge feature of another tile)
# ------------------------------------------------------------------------------------------------------
GRASS_POOL = [
    [("patch", 16, 16, 6, 4, 4), ("clump", 13, 19, "L"), ("clump", 21, 15, "S")],
    [("clump", 11, 14, "M"), ("clump", 19, 21, "M"), ("clover", 15, 9)],
    [("patch", 15, 18, 7, 4, 2), ("clump", 17, 18, "L"), ("pebbles", 22, 21)],
    [("clump", 10, 21, "S"), ("clump", 16, 12, "M"), ("clump", 22, 19, "S")],
    [("patch", 17, 14, 6, 3, 4), ("clover", 9, 18), ("clump", 20, 22, "S")],
    [("special", 14, 13), ("clump", 9, 22, "S")],
]
MOSS_POOL = [
    [("patch", 16, 16, 6, 4, 4), ("needles", 12, 20)],
    [("fern", 13, 12), ("needles", 21, 21)],
    [("root", 7, 15), ("mush", 21, 9)],
    [("patch", 15, 17, 7, 4, 2), ("twig", 18, 11), ("clump", 11, 22, "S")],
    [("mush", 12, 18), ("needles", 20, 12)],
    [("fern", 17, 15)],
]
PATH_POOL = [
    [("pebble", 14, 13, "M"), ("pebble", 20, 20, "S")],
    [("crack", 10, 12, "A")],
    [("pebble", 17, 17, "L"), ("tuft", 10, 21)],
    [("crack", 15, 9, "B"), ("pebble", 10, 20, "S")],
    [("patch", 16, 16, 6, 3, 2), ("pebble", 20, 12, "S")],
]
SAND_POOL = [[("shell", 15, 15)], [("pebble", 12, 18)], [("twig", 16, 11)], [], [("pebble", 19, 14), ("shell", 11, 20)], []]
SNOW_POOL = [[("rock", 15, 15)], [("twig", 12, 18)], [], [], [("rock", 19, 11), ("twig", 10, 20)], []]
RUIN_POOL = [[("crack", 14, 15, "A")], [("moss", 16, 16)], [("chip", 18, 14)], [], [("crack", 10, 18, "B"), ("chip", 20, 9)],
             [("wear", 16, 16)], []]
# The island's own grass (round 3): clover carpets with white blossoms in two of its six mark sets.
ISLAND_POOL = [GRASS_POOL[0], [("clump", 11, 14, "M"), ("carpet", 19, 19), ("clover", 13, 8)], GRASS_POOL[2],
               [("carpet", 14, 14), ("clump", 23, 21, "S")], GRASS_POOL[4], [("carpet", 16, 17), ("clump", 9, 22, "S"), ("clover", 22, 9)]]
POOL = {"grass": ISLAND_POOL, "plains": GRASS_POOL, "lake": GRASS_POOL, "moss": MOSS_POOL, "path": PATH_POOL,
        "sand": SAND_POOL, "dsand": SAND_POOL, "snow": SNOW_POOL, "ruin": RUIN_POOL}
SPECIAL = {"plains": "flowers", "lake": "reeds", "grass": "clover"}
FLOWER_COLOURS = ["flower.white", "flower.yellow", "flower.pink"]


def draw_marks(c, ground, mat, marks, ox, oy, season, k=0):
    stone = "dstone" if ground == "dsand" else "pebble"
    for m in marks:
        kind = m[0]
        x, y = ox + m[1], oy + m[2]
        if kind == "patch":
            if season == "autumn":  # the autumn colour patches: low, lit only (2 / 4 of the autumn ramp read as spots)
                patch(c, mat, x, y, m[3], m[4], 4, seed=340 + k, wobble=0.5)
            else:
                patch(c, mat, x, y, m[3], m[4], m[5], seed=340 + k)
        elif kind == "clump":
            M.draw_clump(c, mat, x, y, ("W" if ground == "plains" and m[3] == "L" else m[3]))
        elif kind == "clover" and season != "winter":
            c.stamp(x, y, M.CLOVER, mat)
            if ground == "grass" and season is None:  # the island's clover is in bloom
                c.put(x + 2, y, "flower.white", 6)
        elif kind == "carpet" and season != "winter":  # a clover carpet: a low lit bed, clover leaves, a few white blossoms
            patch(c, mat, x, y, 6, 4, 4, seed=360 + k, wobble=0.6)
            for j, (dx, dy) in enumerate([(-6, -2), (-1, -3), (2, 0), (-4, 1)]):
                c.stamp(x + dx, y + dy, M.CLOVER, mat)
                if season is None and (j + k) % 2 == 0:
                    c.put(x + dx + 2, y + dy, "flower.white", 6)
                    c.put(x + dx + 2, y + dy + 1, "flower.white", 4)
        elif kind == "pebbles":
            c.stamp(x, y, M.PEBBLE_M, "pebble")
            c.stamp(x + 5, y + 3, M.PEBBLE_S, "pebble")
        elif kind == "special":
            sp = SPECIAL.get(ground)
            if sp == "flowers" and season is None:
                col = FLOWER_COLOURS[k % 3]
                c.stamp(x, y, M.FLOWERS, keys={"a": (col, 4), "b": (col, 6), "c": ("flower.yellow", 3)})
            elif sp == "reeds":
                c.stamp(x, y, M.REED, "reed")
            elif sp == "clover" and season != "winter":
                draw_marks(c, ground, mat, [("carpet", m[1] + 2, m[2] + 2)], ox, oy, season, k)
        elif kind == "needles":
            c.stamp(x, y, M.NEEDLES, "pine")
        elif kind == "fern":
            c.stamp(x, y, M.FERN, "fern")
        elif kind == "twig":
            c.stamp(x, y, M.TWIG, "bark")
        elif kind == "mush" and season != "winter":
            c.stamp(x, y, M.MUSHROOM, "bark", keys={"b": ("shell", 3)})
        elif kind == "root":
            for dx, dy in [(0, 0), (1, 0), (2, 1), (3, 1), (4, 1), (5, 2), (6, 2), (7, 2), (8, 3), (9, 3), (10, 3), (11, 4)]:
                c.put(x + dx, y + dy, "bark", 4)
                c.put(x + dx, y + dy + 1, "bark", 2)
                c.put(x + dx, y + dy + 2, mat, 1)
        elif kind == "pebble":
            c.stamp(x, y, {"S": M.PEBBLE_S, "M": M.PEBBLE_M, "L": M.PEBBLE_L}[m[3]] if len(m) > 3 else M.PEBBLE_M, stone)
        elif kind == "crack":
            M.crack(c, mat, x, y, M.CRACK_A if m[3] == "A" else M.CRACK_B)
        elif kind == "tuft":
            M.draw_clump(c, "grass", x, y, "S")
        elif kind == "shell":
            if ground == "sand":
                c.stamp(x, y, M.SHELL, "shell")
            else:
                M.crack(c, mat, x - 3, y - 3, M.CRACK_B)
        elif kind == "rock":
            if ground == "snow" and k >= 0:  # a stone under the snow: a snow cap, a little rock showing on its lee side
                c.stamp(x, y, [".55.", "5443", ".22."], mat)
                c.stamp(x + 2, y + 2, ["32"], "rock")
            else:
                c.stamp(x, y, [".44.", "4332", "3221"], "rock")
                c.stamp(x, y + 3, [".55."], mat)
        elif kind == "drift":
            M.drift(c, mat, x, y, m[3], height=1)
        elif kind == "moss":
            c.stamp(x, y, [".45..", "34432", ".22.."], "moss")
        elif kind == "chip":
            c.stamp(x, y, ["11", "15"], mat)
        elif kind == "wear":
            patch(c, mat, x, y, 4, 3, 2, seed=350 + k)


LEAVES = [(9, 9), (22, 12), (14, 23), (25, 24), (7, 18), (19, 6)]  # autumn: fallen leaves, a few per tile by index


# A fine, even grain of 2-px marks (one ramp step from the core) on the grass-like grounds, moss and path,
# so the calm base is not an empty sheet. Hand-jittered; 3 px clear of the edges.
GRAIN = [(5, 4), (22, 3), (13, 9), (27, 12), (7, 17), (19, 18), (4, 26), (14, 25), (25, 27), (10, 13)]
GRAIN_MARK = {"grass": ["4", "4"], "plains": ["4", "4"], "lake": ["4", "4"], "moss": ["44"], "path": ["44"]}  # lit only: very low contrast


def draw_grain(c, ground, mat, ox, oy):
    rows = GRAIN_MARK.get(ground)
    if rows:
        for x, y in GRAIN:
            c.stamp(ox + x, oy + y, rows, mat)


def draw_tile(c, ground, mat, ox, oy, t, idx, season=None, interior=True):
    """One tile's content at (ox, oy): grain, edge crossings for its 4 edge types, lines / paving, interior marks."""
    if ground == "ruin":
        draw_ruin(c, mat, ox, oy, t["R"], t[W], t[E])
        return
    draw_grain(c, ground, mat, ox, oy)
    if ground in LINES:
        draw_lines(c, ground, mat, ox, oy, t[W], t[E], idx)
    for side in (N, E, S, W):
        if t[side] and ground in EDGE:
            ex, ey = edge_origin(side, ox, oy)
            EDGE[ground](c, mat, ex, ey, side in (W, E), ground)
    if interior and idx:
        pool = POOL[ground]
        marks = pool[(idx * 5 + 3) % len(pool)]
        if ground in LINE_GROUNDS:  # all-texture grounds: a mark on about one tile in five, anywhere in the tile (by index)
            if idx % 3 == 1:
                marks = [(m[0], 1 + (idx * 7 + j * 11) % 25, 1 + (idx * 13 + j * 5) % 27) + tuple(m[3:]) for j, m in enumerate(marks)]
                draw_marks(c, ground, mat, marks, ox, oy, season, idx)
        else:
            dx, dy = (idx * 3) % 7 - 3, (idx * 5 + 2) % 7 - 3  # the marks move with the tile index (no fixed spot)
            draw_marks(c, ground, mat, marks, ox + dx, oy + dy, season, idx)
    if season == "autumn" and idx:
        for k in range(1 + idx % 3):
            x, y = LEAVES[(idx + 2 * k) % len(LEAVES)]
            c.stamp(ox + x, oy + y, M.LEAF if k % 2 else M.LEAF2, "leaf")


def wang_tile(ground, n, mat=None, season=None):
    mat = mat or ground
    if ground not in TEX4:  # round 4: the grass-likes, moss and path have 16 calm tiles (macro_a.py)
        import macro_a

        return macro_a.calm_tile(ground, n, mat)
    c = Canvas(32, 32, (mat, 3), wrap=False)
    draw_tile(c, ground, mat, 0, 0, types_of(n, ground), n, season)
    return c


# ------------------------------------------------------------------------------------------------------
# Macro pieces: k x k tiles on one canvas, outer edges type 0, inner edges type 1 where listed, plus big
# marks across the whole block (kept 4 px inside the outer border).
# ------------------------------------------------------------------------------------------------------
BIG = {  # per family and macro name: marks in canvas coordinates
    ("grass", "macro"): [("patch", 32, 30, 16, 9, 2), ("patch", 20, 44, 9, 4, 4), ("clump", 26, 28, "L"), ("clump", 35, 33, "L"),
                         ("clump", 40, 27, "M"), ("clump", 29, 37, "M"), ("clover", 44, 44)],
    ("grass", "macro2"): [("patch", 30, 22, 14, 6, 4), ("patch", 36, 42, 13, 7, 2), ("clump", 18, 20, "M"), ("clump", 44, 40, "L"),
                          ("clump", 38, 44, "M"), ("special", 22, 38), ("pebbles", 46, 18)],
    ("grass", "macro3"): [("patch", 48, 46, 26, 13, 2), ("patch", 30, 26, 10, 5, 4), ("patch", 66, 64, 12, 6, 4),
                          ("clump", 40, 44, "L"), ("clump", 50, 50, "L"), ("clump", 58, 42, "M"), ("clump", 44, 54, "M"),
                          ("clump", 24, 70, "S"), ("clump", 72, 26, "S"), ("special", 68, 70), ("clover", 20, 22)],
    ("moss", "macro"): [("patch", 30, 31, 18, 10, 2), ("patch", 24, 26, 8, 5, 4), ("patch", 42, 38, 8, 5, 4), ("root", 16, 30),
                        ("fern", 33, 25), ("mush", 44, 44), ("needles", 26, 40)],
    ("moss", "macro2"): [("patch", 32, 32, 20, 8, 4), ("fern", 20, 22), ("fern", 40, 38), ("twig", 30, 46), ("needles", 46, 18)],
    ("moss", "macro3"): [("patch", 48, 48, 28, 14, 2), ("patch", 36, 40, 10, 6, 4), ("patch", 60, 56, 10, 6, 4),
                         ("root", 24, 46), ("root", 54, 62), ("fern", 46, 36), ("mush", 66, 30), ("needles", 30, 66),
                         ("needles", 70, 50), ("clump", 20, 24, "M")],
    ("path", "macro"): [("patch", 32, 32, 18, 9, 4), ("crack", 26, 28, "A"), ("crack", 33, 33, "B"), ("pebble", 44, 20, "L"),
                        ("pebble", 18, 44, "M"), ("tuft", 12, 36)],
    ("path", "macro2"): [("patch", 30, 32, 16, 8, 2), ("pebble", 22, 24, "L"), ("pebble", 40, 40, "M"), ("pebble", 46, 22, "S"),
                         ("crack", 34, 18, "A")],
    ("path", "macro3"): [("patch", 48, 48, 26, 12, 4), ("patch", 40, 44, 10, 5, 2), ("crack", 36, 40, "A"), ("crack", 50, 52, "B"),
                         ("pebble", 66, 30, "L"), ("pebble", 26, 66, "M"), ("pebble", 70, 66, "S"), ("tuft", 20, 30),
                         ("tuft", 64, 72)],
    ("sand", "macro"): [("shell", 44, 44), ("pebble", 18, 20)],
    ("sand", "macro2"): [("pebble", 40, 22), ("twig", 20, 42)],
    ("sand", "macro3"): [("shell", 60, 66), ("pebble", 30, 28), ("pebble", 36, 31), ("twig", 66, 30)],
    ("snow", "macro"): [("drift", 12, 34, 40), ("rock", 44, 42)],
    ("snow", "macro2"): [("drift", 16, 26, 32), ("twig", 40, 44)],
    ("snow", "macro3"): [("drift", 14, 50, 66), ("drift", 30, 30, 34), ("rock", 64, 66), ("twig", 24, 70)],
    ("ruin", "macro"): [("crack", 26, 28, "A"), ("crack", 32, 33, "A"), ("moss", 38, 46), ("chip", 46, 20)],
    ("ruin", "macro2"): [("wear", 30, 30), ("moss", 18, 40), ("crack", 40, 20, "B")],
    ("ruin", "macro3"): [("crack", 40, 42, "A"), ("crack", 46, 47, "A"), ("crack", 52, 52, "B"), ("moss", 24, 62), ("moss", 62, 26),
                         ("wear", 66, 66), ("chip", 30, 30)],
}
FAMILY = {"grass": "grass", "plains": "grass", "lake": "grass", "moss": "moss", "path": "path", "sand": "sand", "dsand": "sand",
          "snow": "snow", "ruin": "ruin"}
MACROS = {"macro": 2, "macro2": 2, "macro3": 3}
INNER_TYPE = {"macro": 1, "macro2": 0, "macro3": 1}  # the type of the inner edges (lines / joints continue inside)


def macro_canvas(ground, name, mat=None, season=None):
    mat = mat or ground
    k = MACROS[name]
    c = Canvas(32 * k, 32 * k, (mat, 3), wrap=False)
    inner = INNER_TYPE[name]
    for b in range(k):
        for a in range(k):
            t = {N: 0 if b == 0 else inner, S: 0 if b == k - 1 else inner, W: 0 if a == 0 else inner, E: 0 if a == k - 1 else inner}
            if ground in ("grass", "plains", "lake", "moss", "path"):  # their inner edges stay calm: the big marks carry the block
                t = {N: 0, S: 0, W: 0, E: 0}
            draw_tile(c, ground, mat, 32 * a, 32 * b, t, 5 + 3 * (a + k * b), season, interior=False)  # its own swell
    draw_marks(c, ground, mat, BIG[(FAMILY[ground], name)], 0, 0, season, k)
    if season == "autumn":
        for x, y in [(14, 18), (40, 30), (26, 46), (52, 50), (70, 20), (20, 76), (60, 74)]:
            if x < 32 * k - 6 and y < 32 * k - 6:
                c.stamp(x, y, M.LEAF if (x + y) % 2 else M.LEAF2, "leaf")
    return c


def cut(c, k):
    """k x k canvas -> pieces in reading order (0 = NW ... k*k-1 = SE)."""
    out = []
    for b in range(k):
        for a in range(k):
            p = Canvas(32, 32, None, wrap=False)
            p.px = [row[32 * a:32 * a + 32] for row in c.px[32 * b:32 * b + 32]]
            out.append(p)
    return out
