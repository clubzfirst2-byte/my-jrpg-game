"""ROUND 1 (kept for reference; the files now come from wang.py, round 2 — this module still supplies
GROUNDS / SEASONAL / AUTUMN_RAMP to gen_v2.py). Ground v2 tiles: per ground, 4 single variants (.0-.3) and one 2x2 macro piece (.m0 TL, .m1 TR,
.m2 BL, .m3 BR). 8 tiles per ground.

How the variants stay seamless with each other in ANY order: every tile of a ground is
  base (tone 3) + the ground's SEAM layer (identical in all its tiles, 32-periodic, the only marks that
  cross a tile edge) + the variant's own INTERIOR marks (kept >= 3 px inside the tile; checked).
A macro piece is drawn on a 64x64 canvas: the same seam layer at its four 32-px positions, plus big
marks that cross the INNER edges of the 2x2 (kept >= 3 px inside the outer edge), then cut in four.
So a macro's outer edges equal every single variant's edges, and its inner edges join only each other.

Every mark is placed by hand (positions in the tables below). Patterns are large (patches of 8-20 px,
clumps of 6-12 px) and low in value contrast: most of a tile is tones 2-3-4 of its 7-tone ramp.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from canvas import Canvas  # noqa: E402
import marks as M  # noqa: E402

MARGIN = 3
QUADS = [(0, 0), (32, 0), (0, 32), (32, 32)]


def patch(c, mat, cx, cy, rx, ry, tone, seed=0, rot=0.0, rim=False, only=None, wobble=1.0):
    M.fill_patch(c, mat, M.patch_pixels(cx, cy, rx, ry, seed, rot, wobble), tone, only=only, rim=rim)


# ======================================================================================================
# Grass family (island grass, plains, lake shore grass)
# ======================================================================================================
def grass_seam(c, mat, ox=0, oy=0, season=None):
    if season != "autumn":  # (autumn: the dry ramp's wider steps would make these repeat as spots)
        patch(c, mat, ox + 0, oy + 11, 6, 3.2, 2, seed=1, rot=0.2)  # a darker swale across the left/right edge
        patch(c, mat, ox + 21, oy + 0, 7, 2.6, 4, seed=2, rot=-0.15)  # a sunlit strip across the top/bottom edge
    M.draw_clump(c, mat, ox + 31, oy + 26, "M")  # a clump astride the right edge
    M.draw_clump(c, mat, ox + 9, oy + 1, "S")  # one astride the top edge


GRASS_VARIANTS = {
    # (patches: (cx, cy, rx, ry, tone, seed, rot)), (clumps: (x, y, kind)), extras
    0: ([(16, 18, 10, 5, 2, 3, 0.4)], [], []),  # the calm base: one soft swale (it is half of the ground: no marks that would repeat)
    1: ([(11, 9, 6, 4, 4, 5, -0.3), (22, 22, 6.5, 4, 2, 6, 0.2)], [(19, 21, "M"), (8, 13, "S"), (25, 9, "M"), (12, 26, "S")], ["clover"]),
    2: ([(19, 10, 8, 3.5, 2, 7, 0.1), (8, 22, 5, 3, 4, 8, 0.5)], [(15, 11, "L"), (24, 24, "M"), (6, 18, "S")], ["pebbles"]),
    3: ([(14, 16, 9, 6, 2, 9, -0.2), (24, 7, 4, 2.5, 4, 10, 0.0)], [(10, 14, "M"), (17, 19, "L"), (23, 15, "S"), (8, 25, "S")], []),
}
GRASS_MACRO = (
    [(32, 30, 18, 9, 2, 11, 0.25), (20, 44, 10, 5, 4, 12, -0.3), (46, 18, 8, 4, 4, 13, 0.1), (33, 31, 9, 4.5, 1, 14, 0.25)],
    [(26, 28, "L"), (35, 33, "L"), (40, 27, "M"), (29, 37, "M"), (17, 20, "S"), (48, 44, "M"), (14, 48, "S"), (52, 12, "S")],
    ["clover"],
)


def _grass_extras(c, mat, extras, kind, season, quad=(0, 0)):
    ox, oy = quad
    for e in extras:
        if e == "clover" and season != "winter":
            c.stamp(ox + 17, oy + 5, M.CLOVER, mat)
            c.stamp(ox + 5, oy + 17, M.CLOVER, mat)
        elif e == "pebbles":
            c.stamp(ox + 20, oy + 17, M.PEBBLE_M, "pebble")
            c.stamp(ox + 25, oy + 20, M.PEBBLE_S, "pebble")
        elif e == "dirt":  # a worn spot of bare earth across the macro's middle (path ramp, soft rim)
            pix = M.patch_pixels(ox + 33, oy + 31, 5.5, 3, 15, 0.25)
            M.fill_patch(c, "path", pix, 3, rim=True)
            c.stamp(ox + 31, oy + 30, M.PEBBLE_S, "pebble")


def _flowers(c, x, y, colour):
    c.stamp(x, y, M.FLOWERS, keys={"a": (colour, 4), "b": (colour, 6), "c": ("flower.yellow", 3)})


PLAINS_FLOWERS = {1: (8, 7, "flower.white"), 2: (20, 21, "flower.yellow"), 3: (6, 20, "flower.pink"), "m": (22, 40, "flower.white")}
LAKE_REEDS = {1: (21, 13), 3: (9, 9), "m": (38, 22)}


def grass_family(ground, variant, season=None):
    """ground: grass | plains | lake. variant: 0-3 or 'm' (returns the 64x64 macro canvas)."""
    mat = ground
    clump_kind = (lambda k: "W" if ground == "plains" and k == "L" else k)
    if variant == "m":
        c = Canvas(64, 64, (mat, 3))
        for q in QUADS:
            grass_seam(c, mat, *q, season=season)
        pts, clumps, extras = GRASS_MACRO
    else:
        c = Canvas(32, 32, (mat, 3))
        grass_seam(c, mat, season=season)
        pts, clumps, extras = GRASS_VARIANTS[variant]
    for cx, cy, rx, ry, tone, seed, rot in pts:
        if season != "autumn":  # autumn: the dry ramp's wider steps make soft patches read as spots; leaves instead
            patch(c, mat, cx, cy, rx, ry, tone, seed, rot)
    for x, y, k in clumps:
        M.draw_clump(c, mat, x, y, clump_kind(k))
    _grass_extras(c, mat, extras, ground, season)
    if ground == "plains" and variant in PLAINS_FLOWERS and season is None:
        x, y, col = PLAINS_FLOWERS[variant]
        _flowers(c, x, y, col)
    if ground == "lake" and variant in LAKE_REEDS:
        x, y = LAKE_REEDS[variant]
        c.stamp(x, y, M.REED, "reed")
    return c


# ======================================================================================================
# Forest floor (moss)
# ======================================================================================================
def moss_seam(c, mat, ox=0, oy=0):
    patch(c, mat, ox + 14, oy + 0, 7, 2.6, 2, seed=22, rot=0.1, wobble=0.6)  # a damp hollow across top/bottom
    c.stamp(ox + 30, oy + 20, M.NEEDLES[:2], "pine")  # fallen needles across the right edge


# The forest floor: wide low-contrast moss beds (4, irregular) and damp hollows (2); one raised cushion
# (rim) per tile at most; fallen needles, a fern, a surface root, small mushrooms, twigs.
MOSS_VARIANTS = {
    0: ([(16, 16, 10, 5, 4, 23, 0.3, False)], []),  # the calm base
    1: ([(13, 17, 9, 5, 4, 25, -0.2, False), (22, 10, 4, 3, 4, 26, 0.3, True)], [("fern", 14, 18), ("needles", 23, 23)]),
    2: ([(17, 17, 10, 6, 2, 27, 0.1, False)], [("root", 4, 19), ("mush", 22, 8), ("needles", 9, 7)]),
    3: ([(18, 17, 9, 6, 4, 29, -0.3, False), (9, 11, 4, 2.5, 4, 30, 0.4, True)], [("needles", 13, 24), ("twig", 20, 7), ("clump", 7, 26, "S")]),
}
MOSS_MACRO = (
    [(32, 31, 20, 11, 2, 31, 0.3, False), (24, 26, 9, 5, 4, 32, 0.2, False), (42, 38, 9, 5, 4, 33, -0.2, False),
     (46, 15, 5, 3, 4, 34, 0.0, True)],
    [("root", 18, 31), ("fern", 33, 25), ("mush", 44, 44), ("needles", 26, 40), ("needles", 50, 26), ("clump", 12, 18, "M"),
     ("twig", 12, 50)],
)


ROOT = [(0, 0), (1, 0), (2, 1), (3, 1), (4, 1), (5, 2), (6, 2), (7, 2), (8, 3), (9, 3), (10, 3), (11, 4), (12, 4), (13, 5)]


def moss(variant, season=None):
    mat = "moss"
    if variant == "m":
        c = Canvas(64, 64, (mat, 3))
        for q in QUADS:
            moss_seam(c, mat, *q)
        pts, feats = MOSS_MACRO
    else:
        c = Canvas(32, 32, (mat, 3))
        moss_seam(c, mat)
        pts, feats = MOSS_VARIANTS[variant]
    for cx, cy, rx, ry, tone, seed, rot, rim in pts:
        patch(c, mat, cx, cy, rx, ry, tone, seed, rot, rim=rim, wobble=0.6)
    for f in feats:
        k = f[0]
        if k == "needles":
            c.stamp(f[1], f[2], M.NEEDLES, "pine")
        elif k == "fern":
            c.stamp(f[1], f[2], M.FERN, "fern")
        elif k == "twig":
            c.stamp(f[1], f[2], M.TWIG, "bark")
        elif k == "mush" and season != "winter":
            c.stamp(f[1], f[2], M.MUSHROOM, "bark", keys={"b": ("shell", 3)})
        elif k == "clump":
            M.draw_clump(c, mat, f[1], f[2], f[3])
        elif k == "root":  # a surface root (bark): lit top, shade below
            for dx, dy in ROOT:
                c.put(f[1] + dx, f[2] + dy, "bark", 4)
                c.put(f[1] + dx, f[2] + dy + 1, "bark", 2)
                c.put(f[1] + dx, f[2] + dy + 2, mat, 1)
    return c


# ======================================================================================================
# Snow (mountains, and the winter of every grass)
# ======================================================================================================
def snow_seam(c, mat, ox=0, oy=0):
    # one low drift crossing the right edge (the same in every snow tile: kept faint so it does not repeat as a pattern)
    M.drift(c, mat, ox + 25, oy + 25, 12, height=1, phase=0.4)


# Snow: long soft bands (low wobble) of lit snow (4) or shade (2) lying along the wind, low drifts
# (crest 5 / lee 2), fine ridges, now and then a rock tip or a twig.
SNOW_VARIANTS = {
    0: ([(16, 17, 12, 3, 4, 43, 0.12)], []),  # the calm base
    1: ([(15, 14, 12, 3.5, 4, 44, -0.1)], [("drift", 8, 12, 12, 1), ("ripple", 6, 20, 10), ("rock", 21, 19)]),
    2: ([(16, 19, 12, 3, 4, 46, 0.05)], [("drift", 5, 17, 18, 2), ("ripple", 11, 10, 11)]),
    3: ([(17, 13, 11, 3, 4, 47, 0.2)], [("drift", 10, 20, 13, 1), ("ripple", 7, 11, 9), ("twig", 21, 23)]),
}
SNOW_MACRO = (
    [(32, 27, 24, 5, 4, 49, 0.12)],
    [("drift", 9, 34, 42, 3), ("drift", 22, 20, 26, 2), ("ripple", 16, 45, 22), ("ripple", 20, 49, 16), ("rock", 44, 40)],
)
SNOW_ROCK = [".44.", "4332", "3221"]  # 'rock' ramp; a snow lip goes under it


def snow(variant, mat="snow", season=None):
    big = variant == "m"
    c = Canvas(64 if big else 32, 64 if big else 32, (mat, 3))
    pts, feats = SNOW_MACRO if big else SNOW_VARIANTS[variant]
    for cx, cy, rx, ry, tone, seed, rot in pts:
        patch(c, mat, cx, cy, rx, ry, tone, seed, rot, wobble=0.35)
    for q in (QUADS if big else [(0, 0)]):
        snow_seam(c, mat, *q)
    for f in feats:
        if f[0] == "drift":
            M.drift(c, mat, f[1], f[2], f[3], height=f[4])
        elif f[0] == "ripple":
            M.ripple(c, mat, f[1], f[2], f[3], amp=0.6, crest=4, trough=2)
        elif f[0] == "rock":
            c.stamp(f[1], f[2], SNOW_ROCK, "rock")
            c.stamp(f[1], f[2] + 3, [".55."], mat)
        elif f[0] == "twig":
            c.stamp(f[1], f[2], M.TWIG, "bark")
    return c


# ======================================================================================================
# Sand (island beach) and red desert sand: wind ripples are the pattern (long, gently waving, spaced
# 6-9 px), with long soft bands of lit (4) / shaded (2) sand along them; shells or pebbles now and then.
# ======================================================================================================
def sand_seam(c, mat, ox=0, oy=0):
    M.ripple(c, mat, ox + 24, oy + 4, 15, amp=0.8, phase=0.0)  # ripples crossing the left / right edge
    M.ripple(c, mat, ox + 26, oy + 28, 12, amp=0.8, phase=1.3)


SAND_VARIANTS = {
    0: ([(16, 17, 12, 3, 4, 63, 0.1)], [("ripple", 4, 11, 20, 0.3), ("ripple", 6, 18, 21, 1.2), ("ripple", 8, 24, 15, 2.0)]),
    1: ([(15, 14, 12, 3.5, 2, 64, -0.1)], [("ripple", 4, 12, 21, 0.8), ("ripple", 7, 20, 17, 2.2), ("shell", 22, 23), ("pebble", 6, 23)]),
    2: ([(16, 19, 12, 3, 4, 66, 0.05)], [("ripple", 5, 9, 16, 2.0), ("ripple", 4, 15, 22, 0.5), ("ripple", 8, 22, 18, 1.5)]),
    3: ([(17, 15, 11, 3, 4, 68, 0.15)], [("ripple", 6, 10, 19, 1.0), ("ripple", 9, 18, 15, 0.2), ("pebble", 22, 22), ("twig", 5, 24)]),
}
SAND_MACRO = (
    [(32, 26, 24, 5, 4, 69, 0.1), (32, 38, 22, 4, 2, 70, 0.1)],
    [("ripple", 6, 12, 44, 0.0), ("ripple", 8, 19, 46, 1.2), ("ripple", 10, 27, 44, 2.4), ("ripple", 9, 35, 44, 0.6),
     ("ripple", 12, 43, 38, 1.8), ("ripple", 16, 51, 30, 0.9), ("shell", 44, 56), ("pebble", 14, 56)],
)


def sand(variant, mat="sand"):
    big = variant == "m"
    c = Canvas(64 if big else 32, 64 if big else 32, (mat, 3))
    pts, feats = SAND_MACRO if big else SAND_VARIANTS[variant]
    for cx, cy, rx, ry, tone, seed, rot in pts:
        if mat == "dsand" and tone == 2:
            tone = 4  # red sand: no darker bands (they read as stains); lit bands only
        patch(c, mat, cx, cy, rx, ry, tone, seed, rot, wobble=0.35)
    for q in (QUADS if big else [(0, 0)]):
        sand_seam(c, mat, *q)
    stone = "dstone" if mat == "dsand" else "pebble"
    for f in feats:
        if f[0] == "ripple":
            M.ripple(c, mat, f[1], f[2], f[3], amp=1.0, phase=f[4])
        elif f[0] == "shell":
            if mat == "sand":
                c.stamp(f[1], f[2], M.SHELL, "shell")
            else:  # the desert has no shells: a small dry crack instead
                M.crack(c, mat, f[1] - 3, f[2] - 3, M.CRACK_B)
        elif f[0] == "pebble":
            c.stamp(f[1], f[2], M.PEBBLE_M, stone)
        elif f[0] == "twig":
            c.stamp(f[1], f[2], M.TWIG, "bark")
    return c


# ======================================================================================================
# Path (packed earth): worn lighter patches (4) with soft edges, pebbles, small cracks, a grass tuft.
# ======================================================================================================
def path_seam(c, mat, ox=0, oy=0):
    c.stamp(ox + 30, oy + 22, M.PEBBLE_S, "pebble")  # a pebble astride the right edge


PATH_VARIANTS = {
    0: ([(16, 16, 9, 5, 4, 83, 0.3)], []),  # the calm base
    1: ([(15, 17, 10, 4, 4, 85, -0.2)], [("crack", 7, 19, "A"), ("pebble", 22, 22, "S"), ("pebble", 12, 8, "S")]),
    2: ([(16, 15, 8, 5, 2, 86, 0.0)], [("pebble", 18, 18, "L"), ("tuft", 8, 12), ("pebble", 24, 8, "S")]),
    3: ([(16, 16, 10, 5, 4, 88, 0.4)], [("crack", 14, 9, "B"), ("pebble", 8, 22, "M"), ("pebble", 24, 24, "S")]),
}
PATH_MACRO = (
    [(32, 32, 20, 9, 4, 89, 0.2)],
    [("crack", 26, 28, "A"), ("crack", 33, 33, "B"), ("pebble", 44, 20, "L"), ("pebble", 18, 44, "M"), ("pebble", 48, 46, "S"),
     ("pebble", 30, 14, "S"), ("tuft", 12, 36)],
)


def path(variant):
    mat = "path"
    big = variant == "m"
    c = Canvas(64 if big else 32, 64 if big else 32, (mat, 3))
    pts, feats = PATH_MACRO if big else PATH_VARIANTS[variant]
    for cx, cy, rx, ry, tone, seed, rot in pts:
        patch(c, mat, cx, cy, rx, ry, tone, seed, rot, wobble=0.6)
    for q in (QUADS if big else [(0, 0)]):
        path_seam(c, mat, *q)
    for f in feats:
        if f[0] == "pebble":
            c.stamp(f[1], f[2], {"S": M.PEBBLE_S, "M": M.PEBBLE_M, "L": M.PEBBLE_L}[f[3]], "pebble")
        elif f[0] == "crack":
            M.crack(c, mat, f[1], f[2], M.CRACK_A if f[3] == "A" else M.CRACK_B)
        elif f[0] == "tuft":
            M.draw_clump(c, "grass", f[1], f[2], "S")
    return c


# ======================================================================================================


# Ruin floor: big flagstones of different sizes (rectangles that tile the 32-px torus). Their joints are
# the seam layer (identical in every variant); the variants differ by wear, cracks and moss in a joint.
SLABS = [(3, 0, 18, 16), (21, 0, 14, 12), (21, 12, 14, 20), (3, 16, 9, 16), (12, 16, 9, 16)]  # x, y, w, h


def ruin_seam(c, mat, ox=0, oy=0):
    for x0, y0, w, h in SLABS:
        for k in range(1, w):
            c.put(ox + x0 + k, oy + y0 + h - 2, mat, 2)  # the slab's shaded lower bevel
        for k in range(h - 1):
            c.put(ox + x0 + w - 1, oy + y0 + k, mat, 2)  # its shaded right bevel
        for k in range(w):
            c.put(ox + x0 + k, oy + y0, mat, 4)  # its lit top edge
            c.put(ox + x0 + k, oy + y0 + h - 1, mat, 1)  # the joint below it
        for k in range(h):
            c.put(ox + x0, oy + y0 + k, mat, 1)  # the joint left of it
            if k < h - 1:
                c.put(ox + x0 + 1, oy + y0 + k, mat, 4 if k < h - 2 else 2)  # its lit left edge
        c.put(ox + x0 + 1, oy + y0, mat, 5)  # the worn, lit corner
        c.put(ox + x0 + 2, oy + y0, mat, 5)
        c.put(ox + x0, oy + y0 + h - 1, mat, 0)  # where joints cross


RUIN_VARIANTS = {
    0: ([(12, 8, 5, 3, 2, 101, 0.0)], []),  # the calm base
    1: ([(26, 22, 4, 4, 4, 102, 0.0)], [("moss", 6, 14), ("crack", 14, 20, "B")]),
    2: ([(8, 24, 3, 4, 2, 104, 0.0), (15, 8, 4, 3, 4, 105, 0.0)], [("chip", 25, 5), ("crack", 7, 4, "B")]),
    3: ([(26, 24, 4, 5, 2, 106, 0.0)], [("moss", 23, 10), ("chip", 15, 24)]),
}
RUIN_MACRO = (
    [(16, 8, 6, 4, 2, 107, 0.0), (48, 40, 5, 6, 4, 108, 0.0)],
    [("crack", 26, 28, "A"), ("crack", 32, 32, "A"), ("crack", 38, 37, "B"), ("moss", 38, 46), ("moss", 7, 46), ("chip", 46, 20)],
)


def ruin(variant):
    mat = "ruin"
    big = variant == "m"
    c = Canvas(64 if big else 32, 64 if big else 32, (mat, 3))
    quads = QUADS if big else [(0, 0)]
    pts, feats = RUIN_MACRO if big else RUIN_VARIANTS[variant]
    for cx, cy, rx, ry, tone, seed, rot in pts:  # wear on a slab (drawn first; the joints go over it)
        patch(c, mat, cx, cy, rx, ry, tone, seed, rot)
    for q in quads:
        ruin_seam(c, mat, *q)
    for f in feats:
        if f[0] == "crack":
            M.crack(c, mat, f[1], f[2], M.CRACK_A if f[3] == "A" else M.CRACK_B)
        elif f[0] == "moss":  # moss creeping along a joint
            c.stamp(f[1], f[2], [".45..", "34432", ".22.."], "moss")
        elif f[0] == "chip":
            c.stamp(f[1], f[2], ["11", "15"], mat)
    return c


# ======================================================================================================
GROUNDS = {  # key part -> builder(variant, season)
    "grass": lambda v, s=None: grass_family("grass", v, s),
    "plains": lambda v, s=None: grass_family("plains", v, s),
    "lake": lambda v, s=None: grass_family("lake", v, s),
    "moss": lambda v, s=None: moss(v, s),
    "snow": lambda v, s=None: snow(v),
    "sand": lambda v, s=None: sand(v, "sand"),
    "dsand": lambda v, s=None: sand(v, "dsand"),
    "path": lambda v, s=None: path(v),
    "ruin": lambda v, s=None: ruin(v),
}
SEASONAL = ["grass", "plains", "lake", "moss"]  # grounds that change with the season (as in v1)
AUTUMN_RAMP = {"grass": "autumn.grass", "plains": "autumn.grass", "lake": "autumn.lake", "moss": "autumn.moss"}
AUTUMN_LEAVES = {0: [(20, 8), (9, 20)], 1: [(14, 24), (25, 15)], 2: [(8, 9), (23, 19)], 3: [(17, 7), (11, 24), (25, 23)],
                 "m": [(20, 26), (40, 22), (30, 44), (48, 40), (14, 12)]}
WINTER_TIPS = {0: [], 1: [(19, 22)], 2: [(15, 12)], 3: [], "m": [(26, 29), (36, 34)]}


def seasonal(ground, variant, season):
    """autumn: the ground's ramp shifted tone for tone + fallen leaves (guide 3.7);
    winter: the snow tile of the same variant + a few tips of the summer grass poking out (low contrast)."""
    if season == "autumn":
        c = GROUNDS[ground](variant, "autumn")
        c.remap({ground: AUTUMN_RAMP[ground], "flower.white": AUTUMN_RAMP[ground]})
        for x, y in AUTUMN_LEAVES[variant]:
            c.stamp(x, y, M.LEAF if (x + y) % 2 else M.LEAF2, "leaf")
        return c
    c = snow(variant)
    tip_mat = {"grass": "grass", "plains": "plains", "lake": "lake", "moss": "pine"}[ground]
    for x, y in WINTER_TIPS[variant]:  # a few blades of the buried grass, sticking out of the snow
        M.draw_clump(c, tip_mat, x, y + 3, "S", light=False)
    return c


def cut_macro(c64):
    return [cut(c64, x, y) for x, y in QUADS]


def cut(c, x0, y0, w=32, h=32):
    out = Canvas(w, h, None)
    out.px = [row[x0:x0 + w] for row in c.px[y0:y0 + h]]
    return out
