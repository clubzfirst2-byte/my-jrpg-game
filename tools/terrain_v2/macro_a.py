"""Ground v2, round 4: the grass-like grounds, moss and path ("scheme A") without any 32- or 64-px period.

Round 3 measured that these grounds still repeated: the calm base tile carried the same grain in every cell,
the type-1 edge marks sat at the same place of every tile, and the two 2x2 macro pictures were placed on even
cells only. A mean brightness pattern that is the same in every tile shows as a period however faint it is,
so everything here is built to have NO mean pattern:

  * 16 calm tiles `.0`-`.15`, any of them fits any neighbour (picked by a hash per cell). Their only content
    is a fine grain of 16 two-pixel diagonal specks placed like a permutation: every row and every column of
    the tile holds exactly one speck pixel, in every variant.
  * 8 macro pictures of 2 x 2 tiles (`.macro`, `.macro2` ... `.macro8`) that carry ALL the features (thickets,
    lit patches, clumps, clover carpets / flowers / reeds, pebbles, moss beds, ferns, worn patches, cracks...).
    Each kind of feature is drawn 16 (or 8) times over the 8 pictures, and its x positions are all different
    modulo 32 and evenly spread (0, 2, 4 ... 30, or 0, 4 ... 28, in some order), and so are its y positions. So over the set
    every column and every row of a cell carries the same amount of every feature.
  * The engine places a picture in each 3 x 3 block of display tiles at an offset of 0 / 1 tile in x and y
    taken from a hash (not on even cells), and picks the picture by the hash (NAMES.md).

The layout is searched once per ground (seeded, deterministic): no two features of a picture overlap, all
stay 2 px inside the picture, and among a few candidates the one whose left / right and top / bottom halves
are least alike is kept.
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
from canvas import Canvas, RGB  # noqa: E402
import marks as M  # noqa: E402

N_MACRO = 8
MACRO_NAMES = ["macro"] + [f"macro{k}" for k in range(2, N_MACRO + 1)]
FAMILY = {"grass": "grass", "plains": "grass", "lake": "grass", "moss": "moss", "path": "path", "snow": "snow",
          "sand": "sand", "dsand": "sand"}
FLOWER_COLOURS = ["flower.white", "flower.yellow", "flower.pink"]


# ------------------------------------------------------------------------------------------------------
# The calm tiles: a permutation grain.
# ------------------------------------------------------------------------------------------------------
def _perm(v):
    """A permutation of 0-15 for variant v with no two neighbouring specks close together."""
    rnd = random.Random(7919 * (v + 1))
    while True:
        p = list(range(16))
        rnd.shuffle(p)
        if all(abs(p[k] - p[(k + 1) % 16]) >= 3 and abs(p[k] - p[(k + 2) % 16]) >= 2 for k in range(16)):
            return p


PERMS = [_perm(v) for v in range(16)]


def draw_grain(c, mat, ox, oy, v, ground=None, grp=None):
    """Grains of 2-px specks placed like permutations of 0-15: speck k lies in rows 2k, 2k+1 and in columns
    2p, 2p+1. Light specks are one tone over the core, dark ones one tone under. Grass-likes, moss, path, sand:
    diagonal specks, half lean left, half right. Snow: flat wind-smoothed dashes (2 px across, in row 2k or 2k+1).
    Pictures (grp None): one light and one dark grain (snow: the dark one on every other speck).
    Round 6, calm tiles: the light group (grp 0) has two light grains and half a dark one, the dark group
    (grp 1) two dark grains and half a light one, so a stretch of light-group tiles reads lighter and a stretch
    of dark-group tiles darker (the engine mixes the groups by a large noise). Sand: half of every grain (fewer
    short lines on the bare sand)."""
    fam = FAMILY.get(ground)
    snow = fam == "snow"
    if grp is None:
        grains = [(PERMS[v % 16], 4, 0, 1), (PERMS[(v + 7) % 16], 2, 8, 2 if snow else 1)]
    elif grp == 0:
        grains = [(PERMS[v % 16], 4, 0, 1), (PERMS[(v + 11) % 16], 4, 4, 1), (PERMS[(v + 7) % 16], 2, 8, 2)]
    else:
        grains = [(PERMS[(v + 7) % 16], 2, 8, 1), (PERMS[(v + 11) % 16], 2, 12, 1), (PERMS[v % 16], 4, 0, 2)]
    for gi, (perm, tone, shift, every) in enumerate(grains):
        for k, p in enumerate(perm):
            if every == 2 and (k + v) % 2:
                continue
            if fam == "sand" and (k + v + gi) % 2:
                continue
            x, y = ox + 2 * ((p + shift) % 16), oy + 2 * k
            if snow:
                yy = y + (k + p + v + gi) % 2
                c.put(x, yy, mat, tone)
                c.put(x + 1, yy, mat, tone)
            elif (k + p + v + gi) % 2:
                c.put(x, y, mat, tone)
                c.put(x + 1, y + 1, mat, tone)
            else:
                c.put(x + 1, y, mat, tone)
                c.put(x, y + 1, mat, tone)


N_CALM = 32  # round 6: calm tiles 0-15 the light group, 16-31 the dark group


def calm_tile(ground, v, mat=None, season=None):
    """Calm tile v (0-31): the grain of its group, and the small things the calm layout of its group gives it."""
    mat = mat or ground
    grp, w = divmod(v % N_CALM, 16)
    c = Canvas(32, 32, (mat, 3), wrap=False)
    draw_grain(c, mat, 0, 0, w, ground, grp)
    kinds = calm_kinds_of(ground, season, grp)
    for ki, x, y, p in calm_layout(ground, season, grp)[w]:
        kinds[ki][1](c, ground, mat, x, y, p, season)
    for x, y, tone in _FIX.get((ground, season, grp), [[]] * 16)[w]:
        c.put(x, y, mat, tone)
    return c


# ------------------------------------------------------------------------------------------------------
# Feature kinds: (name, bounding box w, h, how many over the 8 pictures). draw(c, ground, mat, x, y, p, season)
# draws placement number p inside the box at (x, y).
# ------------------------------------------------------------------------------------------------------
def _patch(c, mat, cx, cy, rx, ry, tone, seed, wobble=0.6):
    M.fill_patch(c, mat, M.patch_pixels(cx, cy, rx, ry, seed, 0.0, wobble), tone)


CLOVER_SHAPES = [M.CLOVER, [".5..", "545.", ".454", "..3."], ["5.5", "454", ".3."], ["..5.", ".545", "454.", ".3.."]]


def _clover(c, mat, x, y, shape, bloom):
    c.stamp(x, y, CLOVER_SHAPES[shape % 4], mat)
    if bloom:
        c.put(x + 1, y, "flower.white", 6)
        c.put(x + 1, y + 1, "flower.white", 4)


def d_thicket(c, g, mat, x, y, p, season):
    """A darker bed of taller grass with clumps standing in it (two sizes)."""
    big, tall = p % 2 == 0, ("W" if g == "plains" else "L")
    if big:
        _patch(c, mat, x + 12, y + 9, 10.5, 5.6, 4 if season == "autumn" else 2, 400 + p)
        M.draw_clump(c, mat, x + 8, y + 11, tall)
        M.draw_clump(c, mat, x + 17, y + 12, "M")
        M.draw_clump(c, mat, x + 13, y + 14, "S")
    else:
        _patch(c, mat, x + 11, y + 9, 7.5, 4.2, 4 if season == "autumn" else 2, 400 + p)
        M.draw_clump(c, mat, x + 10, y + 11, tall)
        M.draw_clump(c, mat, x + 16, y + 12, "S")


def d_lit(c, g, mat, x, y, p, season):
    """A low sunlit patch (three sizes)."""
    rx, ry = [(7.2, 3.4), (5.5, 2.8), (6.4, 3.8)][p % 3]
    _patch(c, mat, x + 8, y + 4, rx, ry, 4, 420 + p)


def d_clump_m(c, g, mat, x, y, p, season):
    if p % 2:
        M.draw_clump(c, mat, x + 4, y + 7, "M")
    else:
        M.draw_clump(c, mat, x + 2, y + 6, "S")
        M.draw_clump(c, mat, x + 7, y + 7, "S")


def d_clump_s(c, g, mat, x, y, p, season):
    M.draw_clump(c, mat, x + 2, y + 5, "S")


def d_special(c, g, mat, x, y, p, season):
    """The ground's own feature. Island grass: clover in white bloom, in three forms (a carpet on a lit bed, a
    loose scatter, a pair). Plains: flower clusters in three colours. Lake: reeds."""
    if g == "grass":
        bloom = season is None
        form = p % 3
        if form == 0:  # a carpet
            _patch(c, mat, x + 8, y + 6, 6.5, 4.2, 4, 440 + p, wobble=0.5)
            for j, (dx, dy) in enumerate([(1, 3), (6, 1), (10, 5), (4, 7)]):
                _clover(c, mat, x + dx, y + dy, j + p, bloom and j != 2)
        elif form == 1:  # a loose scatter of three
            for j, (dx, dy) in enumerate([(0, 6), (7, 0), (11, 7)]):
                _clover(c, mat, x + dx, y + dy, j + p + 1, bloom and j == 1)
        else:  # a pair by a clump
            M.draw_clump(c, mat, x + 9, y + 9, "S")
            _clover(c, mat, x + 1, y + 2, p, bloom)
            _clover(c, mat, x + 4, y + 7, p + 2, False)
    elif g == "plains":
        if season is None:
            col = FLOWER_COLOURS[p % 3]
            c.stamp(x + 3, y + 2, M.FLOWERS, keys={"a": (col, 4), "b": (col, 6), "c": ("flower.yellow", 3)})
            if p % 2:
                col2 = FLOWER_COLOURS[(p + 1) % 3]
                c.stamp(x + 10, y + 7, ["ab", "ca"], keys={"a": (col2, 4), "b": (col2, 6), "c": ("flower.yellow", 3)})
        else:
            M.draw_clump(c, mat, x + 6, y + 9, "W")
    else:  # lake
        c.stamp(x + 2, y + 2, M.REED, "reed")
        if p % 2:
            c.stamp(x + 8, y + 4, [r[:5] for r in M.REED[1:]], "reed")


def d_carpet(c, g, mat, x, y, p, season):
    """Island grass: a small clover group on a darker bed (the wide carpets are backdrops, round 6)."""
    bloom = season is None
    _patch(c, mat, x + 7, y + 5, 5.5, 3.4, 2, 700 + p, wobble=0.5)
    for j, (dx, dy) in enumerate([(2, 3), (7, 1), (6, 6)]):
        _clover(c, mat, x + dx, y + dy, j + p, bloom and j != 1)


def d_pebbles(c, g, mat, x, y, p, season):
    c.stamp(x, y, M.PEBBLE_M if p % 2 else M.PEBBLE_S, "pebble")
    c.stamp(x + 5, y + 3, M.PEBBLE_S, "pebble")


def d_leaves(c, g, mat, x, y, p, season):
    c.stamp(x, y + (p % 2), M.LEAF if p % 2 else M.LEAF2, "leaf")
    c.stamp(x + 4, y + 3 - (p % 3), M.LEAF2 if p % 2 else M.LEAF, "leaf")


def d_bed(c, g, mat, x, y, p, season):
    """Moss: a deep bed with a fern or a root across it."""
    _patch(c, mat, x + 11, y + 7, 9.5 if p % 2 else 7.5, 5.2 if p % 2 else 4.4, 4 if season == "autumn" else 2, 460 + p)
    if p % 3 == 0:
        for dx, dy in [(0, 0), (1, 0), (2, 1), (3, 1), (4, 1), (5, 2), (6, 2), (7, 2), (8, 3), (9, 3), (10, 3), (11, 4)]:
            c.put(x + 5 + dx, y + 4 + dy, "bark", 4)
            c.put(x + 5 + dx, y + 5 + dy, "bark", 2)
            c.put(x + 5 + dx, y + 6 + dy, mat, 1)
    else:
        c.stamp(x + 6 + p % 4, y + 3, M.FERN, "fern")


def d_fern(c, g, mat, x, y, p, season):
    c.stamp(x, y, M.FERN, "fern")


def d_needles(c, g, mat, x, y, p, season):
    c.stamp(x, y, M.NEEDLES, "pine")
    c.stamp(x + 5, y + 2 + p % 2, M.NEEDLES, "pine")


def d_mush(c, g, mat, x, y, p, season):
    c.stamp(x, y + 1, M.MUSHROOM, "bark", keys={"b": ("shell", 3)})
    if p % 2:
        c.stamp(x + 5, y, M.MUSHROOM, "bark", keys={"b": ("shell", 3)})


def d_twig(c, g, mat, x, y, p, season):
    c.stamp(x, y, M.TWIG, "bark")


def d_worn(c, g, mat, x, y, p, season):
    """Path: a pale worn stretch, sometimes cracked."""
    _patch(c, mat, x + 10, y + 5, 8.5 if p % 2 else 6.5, 4.0, 4, 480 + p)
    if p % 3 == 0:
        M.crack(c, mat, x + 6, y + 3, M.CRACK_A)


def d_dark(c, g, mat, x, y, p, season):
    _patch(c, mat, x + 8, y + 4, 6.5 if p % 2 else 5.0, 3.2, 2, 500 + p)


def d_peb_l(c, g, mat, x, y, p, season):
    c.stamp(x, y, M.PEBBLE_L if p % 2 else M.PEBBLE_M, "pebble")


def d_crack(c, g, mat, x, y, p, season):
    M.crack(c, mat, x, y, M.CRACK_A if p % 2 else M.CRACK_B)


def d_tuft(c, g, mat, x, y, p, season):
    M.draw_clump(c, "grass", x + 2, y + 5, "S")


def d_drift(c, g, mat, x, y, p, season):
    """Snow: a wind drift, a curved lit crest with its lee shade (three lengths)."""
    n = (20, 14, 17)[p % 3]
    M.drift(c, mat, x + 1 + (20 - n) // 2, y + 4, n, height=2 if n > 14 else 1, phase=0.7 * p)


def _shaded(c, mat, x, y, w, h, seed, dish):
    """A soft oval w x h at (x, y), lit from the upper left. dish: a shallow hollow (blue shade on its upper-left
    inner wall, the deepest along the rim, a lit lower-right wall). Else a drift swell (bright upper-left face,
    a crest highlight, blue lee shade under its lower-right side)."""
    cx, cy, rx, ry = x + w / 2, y + h / 2, w / 2 - 0.5, h / 2 - 0.5
    pts = set(M.patch_pixels(cx, cy, rx, ry, seed, 0.0, 0.5))
    for px, py in pts:
        u = ((py + 0.5 - cy) / ry + 0.45 * (px + 0.5 - cx) / rx)  # -1.4 (upper left) .. +1.4 (lower right)
        rim = (px, py - 1) not in pts or (px - 1, py) not in pts
        if dish:
            t = (1 if rim and u < -0.5 else 2) if u < -0.15 else 3 if u < 0.55 else 4
        else:
            t = (5 if u < -0.75 else 4) if u < 0.1 else 3 if u < 0.7 else 2
        if t != 3:
            c.put(px, py, mat, t)


def d_hollow(c, g, mat, x, y, p, season):
    """Snow: a shallow hollow in blue shade (three sizes)."""
    w, h = [(18, 8), (14, 7), (16, 9)][p % 3]
    _shaded(c, mat, x + (18 - w) // 2, y + (9 - h) // 2, w, h, 520 + p, True)


def d_face(c, g, mat, x, y, p, season):
    """Snow: a drift swell, its bright windward face to the upper left, blue lee shade (three sizes)."""
    w, h = [(20, 9), (15, 7), (17, 8)][p % 3]
    _shaded(c, mat, x + (20 - w) // 2, y + (9 - h) // 2, w, h, 540 + p, False)


def d_sparkle(c, g, mat, x, y, p, season):
    """Snow: a few glints (2-px, the brightest tone)."""
    for j, (dx, dy) in enumerate([(0, 1), (4, 4), (6, 0)][:2 + p % 2]):
        if (j + p) % 2:
            c.put(x + dx, y + dy, mat, 6)
            c.put(x + dx + 1, y + dy + 1, mat, 5)
        else:
            c.put(x + dx + 1, y + dy, mat, 6)
            c.put(x + dx, y + dy + 1, mat, 5)


def d_rock(c, g, mat, x, y, p, season):
    """Snow: a stone under a snow cap, its bare lower face, a short blue shade to its lower right."""
    if p % 2:
        c.stamp(x, y + 2, ["...222.", "..2222."], mat)
        c.stamp(x, y, [".5665.", "554443", "433221", ".2211."], "rock", keys={"5": (mat, 5), "6": (mat, 6), "4": (mat, 4)})
    else:
        c.stamp(x + 1, y + 2, ["..222", ".2222"], mat)
        c.stamp(x, y, [".565.", "54443", "33221", ".211."], "rock", keys={"5": (mat, 5), "6": (mat, 6), "4": (mat, 4)})


def d_tips(c, g, mat, x, y, p, season):
    """Winter: the tips of the buried grass (the ground's own plant)."""
    M.draw_clump(c, season[1], x + 2, y + 5, "S", light=False)
    if p % 3 == 0:
        M.draw_clump(c, season[1], x + 6, y + 6, "S", light=False)


# ------------------------------------------------------------------------------------------------------
# Round 5: island sand and desert sand (scheme A). Pictures: ripple fields that thin out at their ends, dune
# swells (lit windward face, lee shade), pebble clusters, shells (beach) / dry grass (desert), pale smooth
# stretches. Calm tiles: bare sand with a grain and a few short ripples, pebbles, shells / twigs.
# ------------------------------------------------------------------------------------------------------
def _stone(g):
    return "dstone" if g == "dsand" else "pebble"


def d_ripples(c, g, mat, x, y, p, season):
    """A field of 3-4 wind ripples, about 4 px apart, longest in the middle; crest 4 (5 on a short lit run),
    trough 2 under it; they all wave together."""
    n = 3 + p % 2
    for k in range(n):
        half = (24 - 7 * abs(k - (n - 1) / 2)) / 2
        x0, x1 = round(x + 12 - half), round(x + 12 + half)
        y0 = y + 1 + 4 * k - (n - 3) * 2 + 2
        for xx in range(x0, x1):
            yy = y0 + round(1.3 * math.sin((xx - x) / 3.7 + 0.9 * p))
            end = xx in (x0, x1 - 1)
            c.put(xx, yy, mat, 5 if (xx + 2 * k + p) % 9 < 2 and not end else 4)
            if not end:
                c.put(xx, yy + 1, mat, 2)


def d_dune(c, g, mat, x, y, p, season):
    """A low dune swell, lit to the upper left, its lee in shade (three sizes)."""
    w, h = [(22, 10), (17, 8), (20, 9)][p % 3]
    _shaded(c, mat, x + (22 - w) // 2, y + (10 - h) // 2, w, h, 560 + p, False)


def d_pebcl(c, g, mat, x, y, p, season):
    st = _stone(g)
    c.stamp(x, y + 1, M.PEBBLE_M, st)
    c.stamp(x + 5, y + 3 - p % 2, M.PEBBLE_S, st)
    if p % 2:
        c.stamp(x + 7, y, M.PEBBLE_S, st)


def d_sandown(c, g, mat, x, y, p, season):
    """Beach: shells (one or two). Desert: a tuft of dry grass with its shadow."""
    if g == "sand":
        c.stamp(x + 1, y + 3, M.SHELL, "shell")
        if p % 2:
            c.stamp(x + 6, y + 5, ["65", "43"], "shell")
    else:
        M.draw_clump(c, "autumn.grass", x + 5, y + 8, "M" if p % 2 else "S")


def d_smooth(c, g, mat, x, y, p, season):
    """A pale wind-smoothed stretch (three sizes)."""
    rx, ry = [(7.4, 3.2), (5.6, 2.6), (6.6, 3.6)][p % 3]
    _patch(c, mat, x + 8, y + 4, rx, ry, 4, 580 + p)


def c_ripple(c, g, mat, x, y, p, season):
    """Calm sand: one or two short ripples."""
    for k in range(1 + p % 2):
        for xx in range(8 - 2 * k):
            yy = y + 4 * k + round(0.9 * math.sin(xx / 2.6 + p))
            c.put(x + xx + k, yy + 1, mat, 4)
            if 0 < xx < 7 - 2 * k:
                c.put(x + xx + k, yy + 2, mat, 2)


def c_speb(c, g, mat, x, y, p, season):
    c.stamp(x, y, M.PEBBLE_S if p % 3 else M.PEBBLE_M, _stone(g))


def c_sandown(c, g, mat, x, y, p, season):
    if g == "sand":
        c.stamp(x, y, ["65", "43"] if p % 2 else M.SHELL, "shell")
    else:
        c.stamp(x, y, M.TWIG, "bark")


KINDS = {
    "grass": [("thicket", 24, 16, 8, d_thicket), ("special", 15, 12, 8, d_special), ("lit", 15, 7, 16, d_lit),
              ("clump_m", 10, 9, 8, d_clump_m), ("pebbles", 9, 6, 8, d_pebbles)],
    "moss": [("bed", 22, 14, 8, d_bed), ("lit", 16, 8, 16, d_lit), ("fern", 9, 7, 8, d_fern), ("needles", 9, 7, 8, d_needles),
             ("mush", 9, 5, 8, d_mush), ("twig", 5, 3, 8, d_twig)],
    "path": [("worn", 20, 10, 16, d_worn), ("dark", 16, 8, 8, d_dark), ("peb_l", 5, 4, 8, d_peb_l), ("pebbles", 9, 6, 8, d_pebbles),
             ("crack", 7, 6, 8, d_crack), ("tuft", 6, 7, 8, d_tuft)],
}
KINDS["sand"] = [("ripples", 24, 16, 16, d_ripples), ("dune", 22, 10, 8, d_dune), ("smooth", 15, 8, 8, d_smooth),
                 ("pebcl", 10, 6, 8, d_pebcl), ("own", 10, 9, 8, d_sandown)]
KINDS["snow"] = [("drift", 22, 8, 8, d_drift), ("hollow", 18, 9, 16, d_hollow), ("face", 20, 9, 16, d_face),
                 ("sparkle", 8, 6, 8, d_sparkle), ("rock", 7, 5, 8, d_rock)]
LEAVES = ("leaves", 7, 5, 8, d_leaves)
TIPS = ("tips", 10, 8, 8, d_tips)


def kinds_of(ground, season):
    ks = list(KINDS[FAMILY[ground]])
    if ground == "grass":  # island grass: its own feature is the clover carpet (round 5)
        ks = [("carpet", 15, 11, 8, d_carpet) if k[0] == "special" else k for k in ks]
    if season == "autumn":
        ks.append(LEAVES)
    if isinstance(season, tuple):  # ("winter", the plant whose tips show): the winter of a grass-like ground, on snow
        ks.append(TIPS)
    return ks


# ------------------------------------------------------------------------------------------------------
# Round 4: the small things of the 16 calm tiles. Each kind is given to n of the 16 tiles; the left edges
# of its bounding boxes are spread evenly over the room the tile leaves (1 .. 31 - w), and so are the top
# edges, in a shuffled order; light and dark things are mixed so no column / row of a tile is brighter on
# average. Nothing comes nearer than 1 px to a tile edge, so any calm tile joins any.
# ------------------------------------------------------------------------------------------------------
def c_mini_lit(c, g, mat, x, y, p, season):
    _patch(c, mat, x + 4, y + 2, 3.6 if p % 2 else 2.8, 1.6, 4, 600 + p, wobble=0.4)


def c_mini_dark(c, g, mat, x, y, p, season):
    _patch(c, mat, x + 4, y + 2, 3.4 if p % 2 else 2.6, 1.5, 2, 620 + p, wobble=0.4)


def c_clover(c, g, mat, x, y, p, season):
    """Island grass: one or two clover of the 4 forms, white bloom on some (summer)."""
    _clover(c, mat, x, y, p, season is None and p % 3 != 1)
    if p % 2:
        _clover(c, mat, x + 5, y + 3, p + 1, False)


def c_flower(c, g, mat, x, y, p, season):
    """Plains: a pair of small flowers (summer), a wind-bent tuft otherwise."""
    if season is None:
        col = FLOWER_COLOURS[p % 3]
        c.stamp(x, y, ["ab.", "ca.", "..b"] if p % 2 else [".ab", ".ca", "b.."],
                keys={"a": (col, 4), "b": (col, 6), "c": ("flower.yellow", 3)})
    else:
        M.draw_clump(c, mat, x + 4, y + 2, "S")


def c_reed(c, g, mat, x, y, p, season):
    """Lake shore: a short reed tuft."""
    c.stamp(x, y, [r[:5] for r in M.REED[2:]] if p % 2 else [r[2:] for r in M.REED[2:]], "reed")


def c_peb(c, g, mat, x, y, p, season):
    c.stamp(x, y, M.PEBBLE_S if p % 3 else M.PEBBLE_M, "pebble")


def c_crack(c, g, mat, x, y, p, season):
    c.stamp(x, y, ["1...", ".12.", "...1"] if p % 2 else ["..1.", "21..", "1..."], mat)


def c_needle(c, g, mat, x, y, p, season):
    c.stamp(x, y, M.NEEDLES, "pine")


def c_sparkle(c, g, mat, x, y, p, season):
    for j, (dx, dy) in enumerate([(0, 0), (3, 2)][:1 + p % 2]):
        c.put(x + dx + (j + p) % 2, y + dy, mat, 6)
        c.put(x + dx + 1 - (j + p) % 2, y + dy + 1, mat, 5)


def c_hollow(c, g, mat, x, y, p, season):
    """Snow: a small blue hollow, its upper rim deepest, a lit lip under it."""
    w = 7 if p % 2 else 5
    c.stamp(x, y, ["." + "1" * (w - 2) + ".", "1" + "2" * (w - 1), "." + "4" * (w - 2) + "."], mat)


def c_drift(c, g, mat, x, y, p, season):
    """Snow: a short lit drift crest with its lee shade."""
    w = 8 if p % 2 else 6
    c.stamp(x, y, [".." + "5" * (w - 4) + "..", "." + "5" * (w - 3) + "4.", "4" + "2" * (w - 2) + "."], mat)


def c_tips(c, g, mat, x, y, p, season):
    M.draw_clump(c, season[1], x + 2, y + 5, "S", light=False)


def c_leaf(c, g, mat, x, y, p, season):
    c.stamp(x, y, M.LEAF if p % 2 else M.LEAF2, "leaf")


CALM_KINDS = {
    "grass": [("clump_s", d_clump_s, 12), ("mini_lit", c_mini_lit, 8), ("mini_dark", c_mini_dark, 8)],
    "moss": [("needle", c_needle, 10), ("clump_s", d_clump_s, 6), ("mini_lit", c_mini_lit, 8), ("mini_dark", c_mini_dark, 8)],
    "path": [("peb", c_peb, 12), ("crack", c_crack, 6), ("mini_lit", c_mini_lit, 8), ("mini_dark", c_mini_dark, 8)],
    "sand": [("ripple", c_ripple, 10), ("peb", c_speb, 6), ("own", c_sandown, 5), ("mini_lit", c_mini_lit, 8),
             ("mini_dark", c_mini_dark, 5)],
    "snow": [("sparkle", c_sparkle, 10), ("hollow", c_hollow, 8), ("drift", c_drift, 8), ("mini_lit", c_mini_lit, 6)],
}
CALM_OWN = {"grass": ("clover", c_clover, 10), "plains": ("flower", c_flower, 8), "lake": ("reed", c_reed, 6)}


def calm_kinds_of(ground, season, grp=0):
    ks = list(CALM_KINDS[FAMILY[ground]])
    # round 6: the light group has more small lit patches, the dark group more small dark ones
    ks = [(nm, fn, (n * 3 + 1) // 2 if nm == ("mini_lit" if grp == 0 else "mini_dark") else max(1, n // 2)
           if nm in ("mini_lit", "mini_dark") else n) for nm, fn, n in ks]
    if ground == "sand":  # round 6: fewer grey pebbles on the beach (they read as salt and pepper)
        ks = [(nm, fn, 2 if nm == "peb" else n) for nm, fn, n in ks]
    if ground in CALM_OWN:
        ks.append(CALM_OWN[ground])
    if season == "autumn":
        ks.append(("leaf", c_leaf, 10))
    if isinstance(season, tuple):
        ks.append(("tips", c_tips, 5))
    return ks


def _bbox(fn, ground, season, p):
    """The real box of what fn draws (left, top offsets from the origin, width, height)."""
    c = Canvas(64, 64, None, wrap=False)
    fn(c, ground, ground, 20, 20, p, season)
    pts = [(x, y) for y in range(64) for x in range(64) if c.px[y][x]]
    xs, ys = [x for x, _ in pts], [y for _, y in pts]
    return min(xs) - 20, min(ys) - 20, max(xs) - min(xs) + 1, max(ys) - min(ys) + 1


_CALM = {}


def _calm_try(ground, season, kinds, seed, grp=0):
    rnd = random.Random(f"calm/{ground}/{season}/{seed}" + (f"/{grp}" if grp else ""))
    tiles = [[] for _ in range(16)]
    boxes = [[] for _ in range(16)]
    for ki, (_name, fn, n) in enumerate(kinds):
        vs = list(range(16))
        rnd.shuffle(vs)
        ox, oy = rnd.sample(range(n), n), rnd.sample(range(n), n)  # the x / y slots, in a shuffled order
        for k in range(n):
            p = k
            bx, by, w, h = _bbox(fn, ground, season, p)
            lx = 1 + round((30 - w) * (ox[k] + 0.5) / n)
            ly = 1 + round((30 - h) * (oy[k] + 0.5) / n)
            for v in vs[k:] + vs[:k]:
                if len(tiles[v]) < 3 and all(lx + w + 1 <= ax or ax + aw + 1 <= lx or ly + h + 1 <= ay or ay + ah + 1 <= ly
                                             for ax, ay, aw, ah in boxes[v]):
                    tiles[v].append((ki, lx - bx, ly - by, p))
                    boxes[v].append((lx, ly, w, h))
                    break
            else:
                return None
    return tiles


def _flatness(cs):
    """How far the mean row / column brightness of the tiles is from flat (std of the two profiles)."""
    R, C = [0.0] * 32, [0.0] * 32
    for c in cs:
        for y in range(32):
            for x in range(32):
                v = _lum(c.px[y][x])
                R[y] += v
                C[x] += v
    out = 0.0
    for P in (R, C):
        m = sum(P) / 32
        out += (sum((v - m) ** 2 for v in P) / 32) ** 0.5 / (32 * len(cs))
    return out


def calm_layout(ground, season=None, grp=0):
    """Per calm tile w (0-15) of group grp: [(kind index, x, y, p)]. Of the first 16 layouts that fit, the one
    whose 16 tiles have the flattest mean row / column brightness is kept (seeded, deterministic)."""
    key = (ground, season, grp)
    if key in _CALM:
        return _CALM[key]
    kinds = calm_kinds_of(ground, season, grp)
    best, found = None, 0
    for seed in range(400):
        tiles = _calm_try(ground, season, kinds, seed, grp)
        if tiles is None:
            continue
        _CALM[key] = tiles
        f = _flatness([calm_tile(ground, 16 * grp + w, season=season) for w in range(16)])
        if best is None or f < best[0]:
            best = (f, tiles)
        found += 1
        if found >= 16:
            break
    if best is None:
        raise SystemExit(f"no calm layout for {ground} {season}")
    _CALM[key] = best[1]
    _FIX[key] = _balance(ground, season, grp)
    return best[1]


_FIX = {}
MAX_FIX = 10  # at most this many balancing specks in a calm tile (a quarter of a picture)


def _balance(ground, season, grp=0):
    """Grain specks that flatten the mean row / column brightness of the 16 calm tiles of a group (_flatten)."""
    _FIX.pop((ground, season, grp), None)
    cs = [calm_tile(ground, 16 * grp + w, season=season) for w in range(16)]
    return _flatten([(c, 0, 0) for c in cs], ground, season=season)


def _flatten(views, ground, cap=MAX_FIX, thr=0.03, season=None):
    """The small things stay 1+ px inside a tile, so the rows / columns near the tile edges would differ a little
    on average, and a ground whose field is very even shows even that. A speck (2 px, diagonal - on snow flat -,
    one tone under / over the core, like the grain) goes on a core-tone pair where a row and a column that are
    both too bright (too dark) cross, in the tiles in turn, until the mean profiles over the tiles are flat
    (largest deviation under thr) or every tile has `cap` specks. views: (canvas, x0, y0) of 32 x 32 tiles;
    the specks are drawn in place and returned per view."""
    n = len(views)
    base = (ground, 3)
    if season == "autumn":  # the autumn sets are drawn in the summer ramp and recoloured after: weigh by autumn colours
        import grounds as G
        amap = G.AUTUMN_RAMP

        def _lum(v):  # noqa: F811
            m = amap.get(v[0], v[0]) if v[0] == ground else v[0]
            r, g, b = RGB[m][v[1]]
            return 0.299 * r + 0.587 * g + 0.114 * b
    else:
        _lum = globals()["_lum"]
    fix = [[] for _ in range(n)]
    R, C = [0.0] * 32, [0.0] * 32
    for c, x0, y0 in views:
        for y in range(32):
            for x in range(32):
                v = _lum(c.px[y0 + y][x0 + x])
                R[y] += v / (32 * n)
                C[x] += v / (32 * n)
    lo, hi = _lum((ground, 2)), _lum((ground, 4))
    mid = _lum(base)
    turn = 0
    snow = FAMILY[ground] == "snow"
    shapes = [((0, 0), (1, 0))] + ([] if snow else [((0, 0), (1, 1)), ((1, 0), (0, 1)), ((0, 0), (0, 1))])
    for _ in range(40 * n):
        mR, mC = sum(R) / 32, sum(C) / 32
        dR, dC = [r - mR for r in R], [q - mC for q in C]
        big = max(map(abs, dR + dC))
        if big < thr:
            break
        k0 = [abs(v) for v in dR + dC].index(big)
        sign = 1 if (dR + dC)[k0] > 0 else -1  # too bright: a dark speck; too dark: a light one
        cands = []
        for sh in shapes:
            for x in range(32 - max(a for a, _ in sh)):
                for y in range(32 - max(b for _, b in sh)):
                    pts = [(x + a, y + b) for a, b in sh]
                    if k0 < 32 and all(py != k0 for _, py in pts) or k0 >= 32 and all(px != k0 - 32 for px, _ in pts):
                        continue
                    sc = sign * (sum(dR[py] for _, py in pts) + sum(dC[px] for px, _ in pts))
                    cands.append((-sc, x, y, sh))
        cands.sort()
        done = False
        for negsc, x, y, sh in cands[:60]:
            if -negsc <= 0:
                break
            pts = [(x + a, y + b) for a, b in sh]
            for k in range(n):
                v = (turn + k) % n
                c, x0, y0 = views[v]
                if len(fix[v]) >= 2 * cap:
                    continue
                near = [(px + a, py + b) for px, py in pts for a in (-1, 0, 1) for b in (-1, 0, 1)]
                if all(not (0 <= px < 32 and 0 <= py < 32) or c.px[y0 + py][x0 + px] == base for px, py in near):
                    tone = 2 if sign > 0 else 4
                    d = (lo if sign > 0 else hi) - mid
                    for px, py in pts:
                        c.put(x0 + px, y0 + py, ground, tone)
                        fix[v].append((px, py, tone))
                        R[py] += d / (32 * n)
                        C[px] += d / (32 * n)
                    turn = v + 1
                    done = True
                    break
            if done:
                break
        if not done:
            break
    return fix


# ------------------------------------------------------------------------------------------------------
# Layout: per kind, 16 (or 8) placements, 2 (or 1) per picture; x residues mod 32 all different and evenly
# spread, y residues too.
# ------------------------------------------------------------------------------------------------------
LO, HI = 2, 62  # features stay inside [LO, HI) of the 64-px picture


def _try_layout(ground, season, seed):
    rnd = random.Random(f"{ground}/{season}/{seed}")
    placed = [[] for _ in range(N_MACRO)]  # per picture: (kind index, x, y, w, h, p)
    for ki, (name, w, h, n, _fn) in enumerate(kinds_of(ground, season)):
        step = 32 // n
        rx = [step * k + (ki * 5 + k) % step for k in range(n)]  # one per step, the residue inside the step
        ry = [step * k + (ki * 3 + 1 + k) % step for k in range(n)]  # cycling (no parity lock, round 5)
        rnd.shuffle(rx)
        rnd.shuffle(ry)
        for rnd_no in range(n // N_MACRO):  # one placement per picture and round
            xs, ys = rx[rnd_no * N_MACRO:(rnd_no + 1) * N_MACRO], ry[rnd_no * N_MACRO:(rnd_no + 1) * N_MACRO]

            def spots(m, a, b):
                out = []
                for x in (a, a + 32):
                    for y in (b, b + 32):
                        if LO <= x <= HI - w and LO <= y <= HI - h and all(
                                x + w <= bx or bx + bw <= x or y + h <= by or by + bh <= y
                                for _k, bx, by, bw, bh, _p in placed[m]):
                            out.append((x, y))
                return out

            ok = {m: {(a, b): spots(m, a, b) for a in xs for b in ys} for m in range(N_MACRO)}
            budget = [50000]

            def solve(left, fx, fy, got):
                """Each picture gets one x residue and one y residue (all different) where the feature has room:
                the picture with the fewest possibilities first."""
                if not left:
                    return got
                best = None
                for m in left:
                    opts = [(a, b) for a in fx for b in fy if ok[m][(a, b)]]
                    if best is None or len(opts) < len(best[1]):
                        best = (m, opts)
                m, opts = best
                rnd.shuffle(opts)
                for a, b in opts:
                    budget[0] -= 1
                    if budget[0] < 0:
                        return None
                    r = solve([v for v in left if v != m], [v for v in fx if v != a], [v for v in fy if v != b], got + [(m, a, b)])
                    if r:
                        return r
                return None

            got = solve(list(range(N_MACRO)), xs, ys, [])
            if not got:
                if os.environ.get("DBG"):
                    print("fail", name)
                return None
            for m, a, b in got:
                x, y = rnd.choice(ok[m][(a, b)])
                placed[m].append((ki, x, y, w, h, rnd_no * N_MACRO + m))
    return placed


# ------------------------------------------------------------------------------------------------------
# Round 6: backdrops, drawn on some pictures before their features: the island clover carpet (2 of the 8
# pictures, about 2/3 of the picture wide, 20+ white blooms in summer) and the desert's big dunes (3 of 8, a
# ridge across the whole picture with its lit windward face and lee shade).
# ------------------------------------------------------------------------------------------------------
def bd_carpet(c, g, mat, season, cx, cy, seed):
    rx, ry = 22.0, 13.5
    bed = set(M.patch_pixels(cx, cy, rx, ry, seed, 0.0, 0.45))
    for x, y in bed:
        c.put(x, y, mat, 2)
    rnd = random.Random(seed)
    j = 0
    for gy in range(int(cy - ry) + 2, int(cy + ry) - 2, 5):
        for gx in range(int(cx - rx) + 1, int(cx + rx) - 3, 6):
            x, y = gx + rnd.randint(-1, 2) + (3 if (gy // 5) % 2 else 0), gy + rnd.randint(-1, 1)
            if all((x + a, y + b) in bed for a in (0, 3) for b in (0, 3)):
                _clover(c, mat, x, y, j, season is None and j % 4 != 3)
                j += 1
    return lambda bx, by: ((bx - cx) / rx) ** 2 + ((by - cy) / ry) ** 2 <= 1.1  # keep other features off it


def bd_dune(c, g, mat, season, y0, slope, amp, phase):
    for x in range(2, 62):
        t = (x - 2) / 59
        e = math.sin(math.pi * t) ** 0.6
        ridge = round(y0 + slope * (t - 0.5) * 20 + amp * math.sin(math.pi * 1.3 * t + phase))
        lit = round(1 + e * (5.5 + 2.0 * math.sin(x / 4.3 + phase) + 1.2 * math.sin(x / 1.9 + 2 * phase)))
        lee = round(1 + 4 * e)
        for k in range(1, lit + 1):
            c.put(x, ridge - k, mat, 4)
        c.put(x, ridge, mat, 5 if e > 0.45 else 4)
        for k in range(1, lee + 1):
            c.put(x, ridge + k, mat, 2)
    return None


BACKDROPS = {
    "grass": {0: lambda c, g, mat, s: bd_carpet(c, g, mat, s, 30, 28, 811), 4: lambda c, g, mat, s: bd_carpet(c, g, mat, s, 33, 35, 823)},
    "dsand": {1: lambda c, g, mat, s: bd_dune(c, g, mat, s, 26, 0.8, 5, 0.3), 4: lambda c, g, mat, s: bd_dune(c, g, mat, s, 38, -0.9, 4, 1.7),
              6: lambda c, g, mat, s: bd_dune(c, g, mat, s, 31, 0.3, 6, 3.4)},
}


def _draw(ground, season, placed_m, m, mat=None):
    mat = mat or ground
    c = Canvas(64, 64, (mat, 3), wrap=False)
    for q in range(4):
        draw_grain(c, mat, 32 * (q % 2), 32 * (q // 2), (5 * m + 3 * q + 1) % 16, ground)
    keep_off = None
    if m in BACKDROPS.get(ground, {}):
        keep_off = BACKDROPS[ground][m](c, ground, mat, season)
    kinds = kinds_of(ground, season)
    for ki, x, y, w, h, p in placed_m:
        if keep_off and keep_off(x + w / 2, y + h / 2):
            continue
        kinds[ki][4](c, ground, mat, x, y, p, season)
    return c


def _lum(v):
    r, g, b = RGB[v[0]][v[1]]
    return 0.299 * r + 0.587 * g + 0.114 * b


def _score(canvases):
    """How alike the two halves of the pictures are (left / right columns, top / bottom rows): |correlation|."""
    tot = 0.0
    for axis in (0, 1):
        num = den = 0.0
        for c in canvases:
            prof = []
            for a in range(64):
                prof.append(sum(_lum(c.px[b][a] if axis == 0 else c.px[a][b]) for b in range(64)) / 64)
            mean = sum(prof) / 64
            d = [v - mean for v in prof]
            num += sum(d[a] * d[a + 32] for a in range(32))
            den += sum(v * v for v in d) / 2
        tot += abs(num / den) if den else 0
    return tot


_CACHE = {}


def macros(ground, season=None):
    """The 8 pictures (64 x 64 canvases) of a ground."""
    key = (ground, season)
    if key not in _CACHE:
        best = None
        seed = 0
        found = 0
        while found < 6 and seed < 60:
            lay = _try_layout(ground, season, seed)
            seed += 1
            if lay is None:
                continue
            found += 1
            cv = [_draw(ground, season, lay[m], m) for m in range(N_MACRO)]
            s = _score(cv)
            if best is None or s < best[0]:
                best = (s, cv, lay)
        if best is None:
            raise SystemExit(f"no macro layout for {ground} {season}")
        _flatten([(c, 32 * (q % 2), 32 * (q // 2)) for c in best[1] for q in range(4)], ground, season=season)  # round 5
        _CACHE[key] = best
    return _CACHE[key][1]


def cut(c):
    out = []
    for q in range(4):
        p = Canvas(32, 32, None, wrap=False)
        a, b = q % 2, q // 2
        p.px = [row[32 * a:32 * a + 32] for row in c.px[32 * b:32 * b + 32]]
        out.append(p)
    return out


def residues(ground, season=None):
    """For the check: per kind, the sorted x and y residues (mod 32) of its placements."""
    macros(ground, season)
    lay = _CACHE[(ground, season)][2]
    kinds = kinds_of(ground, season)
    out = {}
    for m in range(N_MACRO):
        for ki, x, y, w, h, p in lay[m]:
            out.setdefault(kinds[ki][0], ([], []))
            out[kinds[ki][0]][0].append(x % 32)
            out[kinds[ki][0]][1].append(y % 32)
    return {k: (sorted(v[0]), sorted(v[1])) for k, v in out.items()}
