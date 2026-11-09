"""Release terrain: the ground tiles (32x32, wrap on all sides) and the special tiles that are not ground.

Same method as the approved samples (gen_samples.py): a flat core tone (2), then HAND-DRAWN stamps at
HAND-CHOSEN places. Every mark is a cluster of 2-5 px, every colour is a ramp tone, nothing is random.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from tile import Tile, hx  # noqa: E402
from ramps import RELEASE, SAMPLE  # noqa: E402
from gen_samples import TUFT_L, TUFT_M, TUFT_S, SPRIG, CLOVER, RIPPLE, RIPPLE_S  # noqa: E402

# Aliases: a second name for a ramp, so a season can shift one use of it and keep the other
# (e.g. the reed clump on the lake shore, or summer grass blades poking out of winter snow).
ALIASES = {"reed": "lake.reed", "grass_g": "plains.grass", "lakeg": "lake.grass"}
ALL = {**RELEASE, **SAMPLE}
ALL.update({k: ALL[v] for k, v in ALIASES.items()})


def tones(mat):
    return {str(k): (mat, k) for k in range(5)}


def new_tile(w, h, base=None, wrap_x=True, wrap_y=True):
    return Tile(w, h, ALL, base=base, wrap_x=wrap_x, wrap_y=wrap_y)


def set_ramp(t, mat, ramp_name):
    """Palette shift: the material `mat` is drawn with another ramp, tone for tone (2 -> 2)."""
    t.ramps[mat] = [hx(c) for c in ALL[ramp_name]]


def stamps(t, items, mat):
    for x, y, p in items:
        t.stamp(x, y, p, tones(mat))


# ---------------------------------------------------------------------------------------------
# Lake shore grass (lake.grass): the same tuft drawings as the island, its own layout, + one feature.
# ---------------------------------------------------------------------------------------------
LAKE_TUFTS = [(4, 3, TUFT_S), (14, 6, TUFT_M), (26, 4, SPRIG), (7, 14, SPRIG), (21, 16, TUFT_L), (2, 24, TUFT_M),
              (13, 26, TUFT_S), (27, 27, SPRIG)]
REEDS = [  # a clump of dry reeds (lake.reed), lit on the left, its foot in the grass shadow
    ".3...4.",
    ".2.3.3.",
    "32.2.2.",
    "2.12.21",
    "21.2.1.",
    ".1.1.1.",
    "..g.g..",
]
SHORE_STONES = [  # two pale shore pebbles (lake.shore) with their shadow on the grass
    ".43..3.",
    "3221.21",
    ".gg..g.",
]
LAKE = {  # variant: (shift of the tuft layout, feature, position)
    0: ((0, 0), None, None),
    1: ((11, 19), "reeds", (8, 9)),
    2: ((21, 7), "stones", (16, 22)),
    3: ((5, 13), "clover", (24, 7)),
}


def lake_grass(variant, winter=False):
    (dx, dy), feat, pos = LAKE[variant]
    t = new_tile(32, 32, base=("lake.grass", 2))
    stamps(t, [(x + dx, y + dy, p) for x, y, p in LAKE_TUFTS], "lake.grass")
    if feat == "reeds":
        t.stamp(*pos, REEDS[:4] if winter else REEDS, {**tones("reed"), "g": ("lake.grass", 1)})  # winter: the tops only
    elif feat == "stones":
        t.stamp(*pos, SHORE_STONES, {**tones("lake.shore"), "g": ("lake.grass", 1)})
    elif feat == "clover":
        t.stamp(*pos, CLOVER, tones("lake.grass"))
        t.stamp(pos[0] - 9, pos[1] + 12, CLOVER, tones("lake.grass"))
    return t


# ---------------------------------------------------------------------------------------------
# Forest floor (forest.moss): moss cushions and short tufts; fallen needles, a fern, mushrooms.
# ---------------------------------------------------------------------------------------------
MOSS = [
    ".33.",
    "3431",
    ".11.",
]
MOSS_L = [
    ".333..",
    "334331",
    ".33311",
    "..11..",
]
NEEDLES = [  # two fallen pine needles crossing (forest.pine)
    "3...3",
    ".1.1.",
    "..1..",
]
NEEDLES_2 = [
    "..3",
    ".31",
    "31.",
    "1..",
]
FERN = [
    "..3..",
    "3.3.3",
    ".323.",
    "3.2.1",
    ".1.1.",
    "..1..",
]
MUSHROOMS = [  # two small brown caps (tree.bark) on pale stems (shell), shadow on the moss
    ".ab.....",
    "abbc.ab.",
    ".ss.abbc",
    ".sm..ss.",
    "......sm",
]
FOREST_BASE = [(2, 3, MOSS_L), (19, 9, MOSS), (8, 21, MOSS), (24, 25, MOSS_L), (13, 13, TUFT_S), (28, 17, TUFT_S),
               (3, 28, TUFT_S), (16, 1, TUFT_S)]
FOREST = {
    0: ((0, 0), []),
    1: ((16, 0), [("needles", (5, 10)), ("needles2", (22, 18)), ("needles", (12, 27))]),
    2: ((0, 16), [("fern", (20, 4))]),
    3: ((16, 16), [("mushrooms", (6, 6))]),
}


def forest_grass(variant, winter=False):
    (dx, dy), feats = FOREST[variant]
    t = new_tile(32, 32, base=("forest.moss", 2))
    stamps(t, [(x + dx, y + dy, p) for x, y, p in FOREST_BASE], "forest.moss")
    for i, (kind, (x, y)) in enumerate(feats):
        if winter and i > 0:
            continue  # under snow: one dark feature per tile at most (design inspection 1)
        if kind == "needles":
            t.stamp(x, y, NEEDLES, tones("forest.pine"))
        elif kind == "needles2":
            t.stamp(x, y, NEEDLES_2, tones("forest.pine"))
        elif kind == "fern" and winter:  # only the fern's tips show above the snow
            t.stamp(x, y, SHRUB_TIP[:2], tones("forest.pine"))
        elif kind == "fern":
            t.stamp(x, y, FERN, tones("forest.pine"))
        elif kind == "mushrooms" and winter:  # under snow: a buried shrub's tips instead
            t.stamp(x, y, SHRUB_TIP[:2], tones("forest.pine"))
        elif kind == "mushrooms":
            t.stamp(x, y, MUSHROOMS, {"a": ("tree.bark", 4), "b": ("tree.bark", 3), "c": ("tree.bark", 1),
                                      "s": ("shell", 2), "m": ("forest.moss", 1)})
    return t


# ---------------------------------------------------------------------------------------------
# Red desert sand (desert.sand): wind ripples; a pebble pair; a half-buried rock (desert.stone).
# ---------------------------------------------------------------------------------------------
DESERT = {
    0: [(3, 4, RIPPLE), (17, 12, RIPPLE_S), (6, 20, RIPPLE), (22, 26, RIPPLE_S), (25, 1, RIPPLE_S)],
    1: [(20, 3, RIPPLE), (4, 11, RIPPLE_S), (14, 21, RIPPLE), (1, 27, RIPPLE_S)],
    2: [(9, 2, RIPPLE_S), (22, 9, RIPPLE), (2, 15, RIPPLE), (18, 25, RIPPLE_S)],
}
PEBBLES_D = [
    ".43...",
    "3221.3",
    ".ss.32",
    "....s.",
]
ROCK_D = [
    ".343..",
    "32221.",
    "22111s",
    ".ssss.",
]


def desert_sand(variant):
    t = new_tile(32, 32, base=("desert.sand", 2))
    stamps(t, DESERT[variant], "desert.sand")
    keys = {**tones("desert.stone"), "s": ("desert.sand", 1)}
    if variant == 1:
        t.stamp(25, 15, PEBBLES_D, keys)
    elif variant == 2:
        t.stamp(6, 23, ROCK_D, keys)
    return t


# ---------------------------------------------------------------------------------------------
# Mountain snow (mount.snow): drifts (lit crest, blue lee shade); a rock, an ice patch, a shrub tip.
# ---------------------------------------------------------------------------------------------
DRIFT = [
    "..3333..",
    ".3....11",
    "3......1",
]
DRIFT_S = [
    ".333.",
    "3...1",
]
SNOW = {
    0: [(2, 3, DRIFT), (19, 10, DRIFT_S), (7, 18, DRIFT_S), (21, 23, DRIFT), (27, 2, DRIFT_S)],
    1: [(16, 2, DRIFT), (3, 12, DRIFT_S), (12, 24, DRIFT), (26, 18, DRIFT_S)],
    2: [(5, 6, DRIFT_S), (20, 4, DRIFT), (1, 22, DRIFT), (18, 27, DRIFT_S)],
    3: [(10, 2, DRIFT), (24, 13, DRIFT_S), (3, 17, DRIFT), (19, 26, DRIFT_S)],
}
SNOW_ROCK = [  # a rock with a snow cap
    ".aba.",
    "a3221",
    "32211",
    ".sss.",
]
ICE = [
    ".43322.",
    "3322221",
    ".22211.",
]
SHRUB_TIP = [  # the tips of a buried shrub (forest.pine) and their blue shadow
    "3.2.3",
    ".212.",
    "..1s.",
]


def mountains_snow(variant):
    t = new_tile(32, 32, base=("mount.snow", 2))
    stamps(t, SNOW[variant], "mount.snow")
    if variant == 1:
        t.stamp(6, 4, SNOW_ROCK, {**tones("mount.rock"), "a": ("mount.snow", 3), "b": ("mount.snow", 4), "s": ("mount.snow", 1)})
    elif variant == 2:
        t.stamp(11, 14, ICE, tones("mount.ice"))
    # variant 3 stays plain drifts: only 2 tiles in 4 carry an object (design inspection 2)
    return t


# ---------------------------------------------------------------------------------------------
# Ruin floor (ruin.stone): large slabs in staggered rows, lit top / left bevel, a crack, a worn dip.
# ---------------------------------------------------------------------------------------------
def slab_rows(t, mat, rows, joint=1, bevel_lo=1):
    """rows: [(y0, height, start_x, [widths])]. Each block: lit top row and left column (3), shaded bottom
    row (bevel_lo), joint line (joint) on its left and below. Wraps."""
    for y0, hgt, start, widths in rows:
        x = start
        for w in widths:
            for k in range(w):
                t.put(x + k, y0 + hgt - 1, mat, joint)  # gap below
                t.put(x + k, y0, mat, 3)
                t.put(x + k, y0 + hgt - 2, mat, bevel_lo)
            for y in range(y0, y0 + hgt):
                t.put(x, y, mat, joint)
                if y < y0 + hgt - 1:
                    t.put(x + 1, y, mat, 3 if y < y0 + hgt - 2 else bevel_lo)
            x += w


RUIN_CRACK = [
    "1....",
    ".1...",
    ".11..",
    "...1.",
    "...31",
]
RUIN_WEAR = [
    ".11.",
    "1..3",
    ".33.",
]


def ruin_floor():
    t = new_tile(32, 32, base=("ruin.stone", 2))
    slab_rows(t, "ruin.stone", [(0, 16, 3, [18, 14]), (16, 16, 11, [12, 20])])
    # tile.ruin is ONE tile: only quiet marks (a sharp crack or a carved line showed the 32 px grid)
    t.stamp(8, 6, RUIN_CRACK[2:], tones("ruin.stone"))
    t.stamp(22, 22, RUIN_WEAR, tones("ruin.stone"))
    return t


# ---------------------------------------------------------------------------------------------
# Wood floor (wood): boards 8 px tall, joints staggered per row, grain marks, a knot.
# ---------------------------------------------------------------------------------------------
WOOD_ROWS = [(0, 8, 0, [20, 12]), (8, 8, 7, [14, 18]), (16, 8, 3, [24, 8]), (24, 8, 12, [10, 22])]
GRAIN = [(4, 3, 5, 1), (24, 4, 4, 3), (12, 11, 6, 1), (27, 13, 3, 3), (6, 19, 4, 3), (17, 20, 6, 1), (2, 27, 5, 1),
         (20, 28, 4, 3)]  # (x, y, length, tone)
KNOT = [
    ".11.",
    "1331",
    ".11.",
]


def wood_floor():
    t = new_tile(32, 32, base=("wood", 2))
    for y0, hgt, start, widths in WOOD_ROWS:
        x = start
        for w in widths:
            for k in range(w):
                t.put(x + k, y0, "wood", 3)
                t.put(x + k, y0 + hgt - 2, "wood", 1)
                t.put(x + k, y0 + hgt - 1, "wood", 0)
            for y in range(y0, y0 + hgt - 1):
                t.put(x, y, "wood", 0)
            x += w
    for x, y, n, tn in GRAIN:
        for k in range(n):
            t.put(x + k, y, "wood", tn)
    t.stamp(9, 2, KNOT, tones("wood"))
    return t


# ---------------------------------------------------------------------------------------------
# Metal floor (iron): 16 px plates, lit seams, 2x2 rivets, a diagonal sheen. Conducts electricity.
# ---------------------------------------------------------------------------------------------
RIVET = [
    "43",
    "31",
]


def metal_floor():
    t = new_tile(32, 32, base=("iron", 2))
    for k in range(32):
        for s in (0, 16):
            t.put(k, s, "iron", 0)
            t.put(s, k, "iron", 0)
            t.put(k, s + 1, "iron", 3)
            t.put(s + 1, k, "iron", 3)
            t.put(k, s + 15, "iron", 1)
            t.put(s + 15, k, "iron", 1)
    for px in (0, 16):
        for py in (0, 16):
            t.put(px, py + 1, "iron", 0)
            t.put(px + 1, py, "iron", 0)
            for rx, ry in ((3, 3), (11, 3), (3, 11), (11, 11)):
                t.stamp(px + rx, py + ry, RIVET, tones("iron"))
    # sheen: short diagonal strokes on two plates (2 px wide)
    for px, py in ((16, 0), (0, 16)):
        for k in range(4):
            t.put(px + 6 + k, py + 9 - k, "iron", 3)
            t.put(px + 7 + k, py + 9 - k, "iron", 3)
    return t


# ---------------------------------------------------------------------------------------------
# Pit (earth.face wall falling into cave.rock darkness). Seen from above: the far (north) wall faces us.
# ---------------------------------------------------------------------------------------------
PIT_WALL = [5, 6, 6, 7, 6, 5, 5, 6, 7, 7, 6, 5, 6, 6, 5, 5, 6, 7, 6, 6, 5, 6, 7, 7, 6, 5, 5, 6, 6, 7, 6, 5]
PIT_DUST = [(6, 16, "11"), (21, 13, "11"), (13, 24, "111"), (27, 27, "11"), (3, 29, "11")]


def pit_tile():
    t = new_tile(32, 32, base=("cave.rock", 0), wrap_y=False)
    for x in range(32):
        d = PIT_WALL[x]
        t.put(x, 0, "earth", 3)  # the lit rim
        for y in range(1, d):
            t.put(x, y, "earth", 2 if y < d - 2 else 1)
        t.put(x, d, "cave.rock", 1)
    for x, y0, n in [(5, 2, 3), (14, 1, 3), (25, 2, 3)]:  # roots / clods on the wall
        for k in range(n):
            t.put(x, y0 + k, "earth", 1)
        t.put(x + 1, y0, "earth", 3)
    for x, y, s in PIT_DUST:
        for k, ch in enumerate(s):
            t.put(x + k, y, "cave.rock", int(ch))
    return t


def dark_tile():
    """Outside every room: nothing. Flat darkest tone (cave.rock 0)."""
    return new_tile(32, 32, base=("cave.rock", 0))


# ---------------------------------------------------------------------------------------------
# Vine platform (drawn OVER water or a pit by puzzleView): a leafy mat, transparent outside, outlined.
# ---------------------------------------------------------------------------------------------
VINE_SHAPE = [  # '#' = mat, '.' = transparent (32 x 32), hand-drawn ragged edge
    "......##.......####.....##......",
    "....######...########..####.....",
    "...#########################....",
    "..###########################...",
    ".#############################..",
    ".#############################..",
    "###############################.",
    ".##############################.",
    ".###############################",
    "################################",
    "################################",
    ".###############################",
    ".##############################.",
    "###############################.",
    "################################",
    "################################",
    ".###############################",
    ".##############################.",
    "###############################.",
    "################################",
    "################################",
    ".###############################",
    "..#############################.",
    "..############################..",
    ".#############################..",
    ".##############################.",
    "..############################..",
    "...##########################...",
    "...#########################....",
    "....######...#########..###.....",
    ".....####.....#######....#......",
    "................................",
]
VINE_STEMS = [  # (points) two woven stems, tree.bark
    [(1, 9), (6, 8), (11, 10), (16, 9), (21, 11), (26, 10), (30, 12)],
    [(2, 20), (7, 22), (12, 20), (17, 22), (22, 20), (27, 22), (31, 20)],
    [(8, 2), (9, 8), (8, 14), (10, 20), (9, 27)],
    [(22, 3), (23, 9), (21, 15), (23, 21), (22, 28)],
]
LEAF = [
    ".33.",
    "3421",
    ".21.",
]
LEAF_S = [
    "33",
    "21",
]
VINE_LEAVES = [(3, 3, LEAF), (13, 4, LEAF_S), (26, 5, LEAF), (3, 13, LEAF_S), (14, 13, LEAF), (27, 15, LEAF_S),
               (5, 24, LEAF), (16, 25, LEAF_S), (25, 24, LEAF), (18, 17, LEAF_S), (11, 17, LEAF_S), (17, 1, LEAF_S)]


def _line(t, pts, mat, tone, under=None):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(abs(x1 - x0), abs(y1 - y0))
        for k in range(n + 1):
            x = x0 + round((x1 - x0) * k / n)
            y = y0 + round((y1 - y0) * k / n)
            t.put(x, y, mat, tone)
            if under is not None:
                t.put(x, y + 1, mat, under)


def outline(t, bottom_row=None):
    """Selective outline (guide 1.3): an empty pixel next to the art takes the neighbour's material, tone 0."""
    add = []
    for y in range(t.h):
        for x in range(t.w):
            if t.px[y][x] is not None:
                continue
            for ddx, ddy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                xx, yy = x + ddx, y + ddy
                if 0 <= xx < t.w and 0 <= yy < t.h and t.px[yy][xx] is not None:
                    add.append((x, y, t.px[yy][xx][0]))
                    break
    for x, y, mat in add:
        t.put(x, y, mat, 0)


def vine_tile():
    t = new_tile(32, 32, base=None, wrap_x=False, wrap_y=False)
    for y, row in enumerate(VINE_SHAPE):
        for x, ch in enumerate(row):
            if ch == "#":
                t.put(x, y, "tree.leaf", 2)
    inside = {(x, y) for y in range(32) for x in range(32) if t.px[y][x]}
    # shade: lower-right rim darker, upper-left rim lighter
    for x, y in inside:
        if (x + 1, y) not in inside or (x, y + 1) not in inside:
            t.put(x, y, "tree.leaf", 1)
        elif (x - 1, y) not in inside or (x, y - 1) not in inside:
            t.put(x, y, "tree.leaf", 3)
    for pts in VINE_STEMS:
        _line(t, pts, "tree.bark", 3, under=1)
    for x, y, p in VINE_LEAVES:
        t.stamp(x, y, p, tones("tree.leaf"))
    t.px = [[v if (x, y) in inside else None for x, v in enumerate(row)] for y, row in enumerate(t.px)]
    # shrink one px so the outline stays inside 32 x 32
    keep = [[t.px[y][x] if (0 < x < 31 and 0 < y < 31) else None for x in range(32)] for y in range(32)]
    t.px = keep
    outline(t)
    return t


# ---------------------------------------------------------------------------------------------
# Ramp (32 x 64): stone stairs rising north (wall.stone). 8 steps of 8 px; side stringers.
# ---------------------------------------------------------------------------------------------
STEP_JOINTS = [9, 21, 14, 5, 25, 11, 18, 7]  # where each step's two blocks meet (hand-chosen, not aligned)
STEP_CHIPS = [(24, 3), (6, 2), (27, 3), (15, 2), (4, 3), (22, 2), (10, 3), (26, 2)]


def ramp_tile():
    t = new_tile(32, 64, base=("stone", 2), wrap_x=False, wrap_y=False)
    for s in range(8):
        y0 = s * 8
        for x in range(32):
            t.put(x, y0, "stone", 4 if s == 0 else 3)  # the lit nose of the tread
            t.put(x, y0 + 1, "stone", 3)
            t.put(x, y0 + 5, "stone", 1)  # riser below the next nose (in shade)
            t.put(x, y0 + 6, "stone", 1)
            t.put(x, y0 + 7, "stone", 0)
        j = STEP_JOINTS[s]
        for y in range(y0 + 1, y0 + 5):
            t.put(j, y, "stone", 1)
            t.put(j + 1, y, "stone", 3)
        cx, cy = STEP_CHIPS[s]
        t.put(cx, y0 + cy, "stone", 1)
        t.put(cx + 1, y0 + cy, "stone", 1)
        t.put(cx + 1, y0 + cy + 1, "stone", 3)
    for y in range(64):  # stringers: left lit, right shaded
        t.put(0, y, "stone", 1)
        t.put(1, y, "stone", 3)
        t.put(2, y, "stone", 2)
        t.put(29, y, "stone", 2)
        t.put(30, y, "stone", 1)
        t.put(31, y, "stone", 0)
    return t
