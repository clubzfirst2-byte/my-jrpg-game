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
P_TYPE1 = {"grass": 10, "plains": 10, "lake": 10, "moss": 12, "path": 10, "snow": 50, "sand": 50, "dsand": 50, "ruin": 50}


def types_of(n):
    return {N: n & 1, E: (n >> 1) & 1, S: (n >> 2) & 1, W: (n >> 3) & 1}


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


def band_edge(c, mat, ex, ey, vertical, ground):
    """sand / snow: a horizontal (N / S) type-1 edge carries a long soft lit band; vertical edges carry lines."""
    if not vertical:
        patch(c, mat, ex, ey, 10, 3, 4, seed=331, rot=0.05, wobble=0.35)


EDGE = {"grass": grass_edge, "plains": grass_edge, "lake": grass_edge, "moss": moss_edge, "path": path_edge,
        "snow": band_edge, "sand": band_edge, "dsand": band_edge}

# Lines that cross the W / E edges at these heights (sand ripples, snow ridges), per edge type.
LINES = {"sand": {0: [3, 9, 18, 24], 1: [6, 14, 20, 27]}, "dsand": {0: [3, 9, 18, 24], 1: [6, 14, 20, 27]},  # uneven spacing
         "snow": {0: [9, 24], 1: [15, 26]}}
# Ruin paving: a horizontal joint crosses W / E edges at RUIN_H[type]; a vertical joint crosses N / S at RUIN_V[type].
RUIN_H = {0: 9, 1: 22}
RUIN_V = {0: 12, 1: 25}


SWELL = [-4, 3, 0, 4, -3, 5, -2, 2, -5, 1, 4, -4, 3, -1, 5, -3]  # px, per tile index (hand-set, mixed)


def _smooth(t):
    return t * t * (3 - 2 * t)


def draw_lines(c, ground, mat, ox, oy, tw, te, idx):
    """Ripples / ridges from the W edge heights to the E edge heights, gently waving inside (the wave is 0 at
    both ends, so it continues the next tile's line)."""
    left, right = LINES[ground][tw], LINES[ground][te]
    # the bundle of lines swells up or down inside the tile by an amount that depends on the tile index
    # (all lines together, so they never cross), plus a small wave of its own per line
    swell = SWELL[idx % 16] * (1.25 if ground == "snow" else 1.0)
    amp = 0.9
    for k, (yl, yr) in enumerate(zip(left, right)):
        prev = None
        for x in range(32):
            t = x / 31
            tw = min(1.0, max(0.0, (x - 2) / 27))  # the wave is 0 on the 3 px at each end: every tile's band agrees
            bump = math.sin(math.pi * tw)
            y = yl + (yr - yl) * _smooth(t) + swell * bump + amp * math.sin(2 * math.pi * tw) * math.sin(1.7 * k + 0.9 * idx + 0.6)
            y = max(3, min(28, round(y)))  # never into the 2-px edge bands (those belong to the edge types)
            if ground == "snow":  # a low ridge: lit crest (4; 5 at its top), lee shade below (2) on the high part only
                top = abs(t - 0.5) < 0.12 and (k + idx) % 2 == 0
                c.put(ox + x, oy + y, mat, 5 if top else 4)
                if bump > 0.3:
                    c.put(ox + x, oy + y + 1, mat, 2)
            else:  # a ripple: crest (4; 5 on its highest run), trough (2; 1 on its lowest run)
                hi = prev is not None and y < prev
                c.put(ox + x, oy + y, mat, 5 if (hi and 6 < x < 26) else 4)
                c.put(ox + x, oy + y + 1, mat, 1 if (k == 1 and 12 < x < 16) else 2)
            if prev is not None and abs(y - prev) > 1:  # keep the line joined on a steep step
                step = 1 if y > prev else -1
                for yy in range(prev + step, y, step):
                    c.put(ox + x, oy + yy, mat, 4)
            prev = y


INSETS = [None, (15, 13, 7, 6), (5, 15, 6, 5), (17, 3, 8, 5), (6, 23, 7, 5), (19, 16, 6, 7), None, (8, 3, 7, 5),
          (14, 22, 8, 6), (4, 11, 6, 6), (20, 9, 7, 5), None, (10, 17, 6, 5), (16, 4, 6, 6), (5, 20, 8, 5), (18, 18, 7, 6)]


def draw_ruin_joints(c, mat, ox, oy, t, idx=0):
    """Paving joints that cross the tile's edges away from its corners and wander inside: each joint leaves
    its edge, steps to a middle height / column that depends on the tile index, and steps again to the far
    edge's crossing. Flagstones of changing size, never on the tile grid. Lit (4) below / right of a joint,
    shade (2) above / left; 0 where joints meet."""
    yw, ye = RUIN_H[t[W]], RUIN_H[t[E]]
    xn, xs = RUIN_V[t[N]], RUIN_V[t[S]]
    ymid = (yw + ye) // 2 + (-5, -2, 3, 5, 0, 4, -4, 2)[idx % 8]
    xmid = (xn + xs) // 2 + (4, -4, 0, 5, -3, 2, -5, 3)[(idx * 3) % 8]
    jx1, jx2 = 5 + idx % 4, 22 + (idx // 4) % 4  # where the horizontal joint steps (in, then out)
    jy1, jy2 = 5 + (idx // 2) % 4, 23 + idx % 3
    pts = set()

    def hseg(x0, x1, y):
        for x in range(x0, x1 + 1):
            pts.add((x, y))

    def vseg(y0, y1, x):
        for y in range(min(y0, y1), max(y0, y1) + 1):
            pts.add((x, y))

    hseg(0, jx1, yw)
    vseg(yw, ymid, jx1)
    hseg(jx1, jx2, ymid)
    vseg(ymid, ye, jx2)
    hseg(jx2, 31, ye)
    vseg(0, jy1, xn)
    hseg(min(xn, xmid), max(xn, xmid), jy1)
    vseg(jy1, jy2, xmid)
    hseg(min(xmid, xs), max(xmid, xs), jy2)
    vseg(jy2, 31, xs)
    inset = INSETS[idx % len(INSETS)]
    if inset:  # a smaller stone set into the paving (its joints stay 3 px away from the tile's edges)
        x0, y0, w, h = inset
        for x in range(x0, x0 + w + 1):
            pts.add((x, y0))
            pts.add((x, y0 + h))
        for y in range(y0, y0 + h + 1):
            pts.add((x0, y))
            pts.add((x0 + w, y))
    for x, y in pts:
        for dx, dy, tone in ((0, 1, 4), (1, 0, 4), (0, -1, 2), (-1, 0, 2)):
            if (x + dx, y + dy) not in pts and 0 <= x + dx < 32 and 0 <= y + dy < 32:
                c.put(ox + x + dx, oy + y + dy, mat, tone)
    for x, y in pts:
        c.put(ox + x, oy + y, mat, 1)
    for x, y in pts:  # where joints cross: the deepest point
        if sum((x + dx, y + dy) in pts for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) >= 3:
            c.put(ox + x, oy + y, mat, 0)


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
SNOW_POOL = [[("rock", 15, 15)], [("twig", 12, 18)], [], [("drift", 9, 19, 14)], [("rock", 19, 11), ("twig", 10, 20)], []]
RUIN_POOL = [[("crack", 14, 15, "A")], [("moss", 16, 16)], [("chip", 18, 14)], [], [("crack", 10, 18, "B"), ("chip", 20, 9)],
             [("wear", 16, 16)], []]
POOL = {"grass": GRASS_POOL, "plains": GRASS_POOL, "lake": GRASS_POOL, "moss": MOSS_POOL, "path": PATH_POOL,
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
                c.stamp(x, y, M.CLOVER, mat)
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
    """One tile's content at (ox, oy): grain, edge crossings for its 4 edge types, lines / joints, interior marks."""
    draw_grain(c, ground, mat, ox, oy)
    if ground in LINES:
        draw_lines(c, ground, mat, ox, oy, t[W], t[E], idx)
    if ground == "ruin":
        draw_ruin_joints(c, mat, ox, oy, t, idx)
    for side in (N, E, S, W):
        if t[side] and ground in EDGE:
            ex, ey = edge_origin(side, ox, oy)
            EDGE[ground](c, mat, ex, ey, side in (W, E), ground)
    if interior and idx:
        pool = POOL[ground]
        draw_marks(c, ground, mat, pool[(idx * 5 + 3) % len(pool)], ox, oy, season, idx)
    if season == "autumn" and idx:
        for k in range(1 + idx % 3):
            x, y = LEAVES[(idx + 2 * k) % len(LEAVES)]
            c.stamp(ox + x, oy + y, M.LEAF if k % 2 else M.LEAF2, "leaf")


def wang_tile(ground, n, mat=None, season=None):
    mat = mat or ground
    c = Canvas(32, 32, (mat, 3), wrap=False)
    draw_tile(c, ground, mat, 0, 0, types_of(n), n, season)
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
