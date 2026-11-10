"""Terrain v1.1 (art/terrain-v1-1): NEW sprites only, added next to the 111 of v1.0 (which stay as they are).

  1. water edges: tile.shore.* (island sand), tile.shore-desert.* (red desert sand), tile.bank.* (an overlay
     for any grass-like ground: island / plains / lake grass, forest moss, mountain snow, their seasons)
     - <mask>.<frame>: mask = which sides touch water (N 1, E 2, S 4, W 8; 1-15), 2 frames like tile.water
     - inner.<ne|se|sw|nw>.<frame>: only that diagonal neighbour is water
  2. cliff band variants: face.<earth|ruin|wall|stone>.<part>.v1 / .v2 (+ the earth lips' autumn / winter)
  3. plateau faces: face.sand.* (island sand), face.desert.* (red desert sand), face.path.*
  4. autumn for the forest and the mountains: autumn.forest.grass.0-3, autumn.forest.pine,
     autumn.mountains.snow.0-3 (no snow: scree and dry grass), autumn.mountains.pine,
     autumn.face.stone.<top|top-base>.<4|8> (+ .v1 / .v2)

Same method as v1.0: 5-tone ramps, hand-placed stamps, alpha 0 / 255. The variants re-use the v1.0
drawing functions with other hand-chosen detail positions (the column profiles that meet the next
tile stay the same, so every variant joins every other one without a step).
"""

import contextlib
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import gen_samples as S  # noqa: E402
import release_faces as F  # noqa: E402
from release_ground import new_tile, tones, set_ramp, desert_sand, forest_grass, mountains_snow  # noqa: E402
from release_nature import pine  # noqa: E402
from gen_samples import TUFT_S, TUFT_M, SPRIG  # noqa: E402

N, E, SO, W = 1, 2, 4, 8


@contextlib.contextmanager
def patched(module, **values):
    """Draw with other module-level detail tables (variants), then put the originals back."""
    old = {k: getattr(module, k) for k in values}
    for k, v in values.items():
        setattr(module, k, v)
    try:
        yield
    finally:
        for k, v in old.items():
            setattr(module, k, v)


# ---------------------------------------------------------------------------------------------
# 1. Water edges
# ---------------------------------------------------------------------------------------------
# How far the water reaches into a land tile from each side (hand-drawn, wrapping: the last value
# meets the first, so a long shore runs on from tile to tile).
P_N = [7, 7, 8, 8, 9, 9, 8, 8, 7, 7, 6, 6, 7, 7, 8, 9, 9, 9, 8, 7, 7, 6, 6, 6, 7, 8, 8, 8, 7, 7, 7, 7]
P_S = [8, 8, 7, 7, 6, 6, 7, 8, 8, 9, 9, 8, 8, 7, 7, 7, 6, 6, 7, 7, 8, 8, 9, 9, 9, 8, 7, 7, 7, 8, 8, 8]
P_E = [7, 8, 8, 9, 9, 8, 7, 7, 6, 6, 7, 7, 8, 8, 8, 7, 7, 6, 6, 7, 8, 9, 9, 8, 8, 7, 7, 6, 6, 6, 7, 7]
P_W = [8, 7, 7, 6, 6, 7, 7, 8, 9, 9, 8, 8, 7, 7, 6, 6, 6, 7, 8, 8, 9, 8, 8, 7, 7, 7, 6, 6, 7, 7, 8, 8]
R = 4  # radius of the rounded corners
# Foam: where the edge of the water carries a bright cluster (2 px), along the edge, per 32 px.
FOAM = {2, 3, 11, 12, 19, 20, 27, 28}
INNER = {"ne": (N, E), "se": (SO, E), "sw": (SO, W), "nw": (N, W)}


def _round_out(a, b):
    """A land corner (a, b = px inside the land from two water edges) is cut round into the water."""
    return 0 <= a < R and 0 <= b < R and (R - a - 0.5) ** 2 + (R - b - 0.5) ** 2 > R * R


def is_water(x, y, mask=0, inner=None):
    xm, ym = x % 32, y % 32
    if inner:  # a notch of water in one corner
        v, h = INNER[inner]
        a = (x - (32 - P_E[ym])) if h == E else (P_W[ym] - 1 - x)  # px inside the band
        b = (P_N[xm] - 1 - y) if v == N else (y - (32 - P_S[xm]))
        if a < 0 or b < 0:
            return False
        return not _round_out(a, b)
    bands = {N: y < P_N[xm], SO: y >= 32 - P_S[xm], E: x >= 32 - P_E[ym], W: x < P_W[ym]}
    if any(bands[s] for s in (N, E, SO, W) if mask & s):
        return True
    depth = {N: y - P_N[xm], SO: 32 - P_S[xm] - 1 - y, E: 32 - P_E[ym] - 1 - x, W: x - P_W[ym]}
    for s1, s2 in ((N, E), (E, SO), (SO, W), (W, N)):
        if mask & s1 and mask & s2 and _round_out(depth[s1], depth[s2]):
            return True
    return False


def water_edge(land, mask, frame, inner=None, kind="sand"):
    """land: a Tile (the land under the tile) or None for an overlay. kind: 'sand' (a wet band on the
    land side) or 'bank' (a 1-2 px earth bank, the land side transparent elsewhere)."""
    wt = S.water_tile(frame)
    t = land if land is not None else new_tile(32, 32, base=None, wrap_x=False, wrap_y=False)
    if land is None:
        t.wrap_x = t.wrap_y = False
    for m in ("water", "earth"):
        if m not in t.ramps:
            set_ramp(t, m, {"water": "water.surface", "earth": "earth.face"}[m])
    wet = {(x, y) for y in range(32) for x in range(32) if is_water(x, y, mask, inner)}

    def wat(x, y):
        return (x, y) in wet if (0 <= x < 32 and 0 <= y < 32) else is_water(x, y, mask, inner)

    for y in range(32):
        for x in range(32):
            if (x, y) in wet:
                t.px[y][x] = wt.px[y][x]
    for y in range(32):
        for x in range(32):
            if (x, y) in wet:
                if any(not wat(x + dx, y + dy) for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0))):
                    along = x if (not wat(x, y - 1) or not wat(x, y + 1)) else y
                    t.put(x, y, "water", 4 if (along + 2 * frame) % 32 in FOAM else 3)
                continue
            near = [(dx, dy) for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)) if wat(x + dx, y + dy)]
            if not near:
                continue
            if kind == "sand":
                mat = t.px[y][x][0] if t.px[y][x] else "sand"
                t.put(x, y, mat, 1)  # wet sand at the water line
            else:
                t.put(x, y, "earth", 1)  # the bank's edge
                if (0, 1) in near and not wat(x, y - 1) and not wat(x - 1, y - 1) and not wat(x + 1, y - 1):
                    t.put(x, y - 1, "earth", 2)  # water to the south: the bank's face shows (2 px)
    return t


def shore_set(prefix, land_fn, kind):
    out = {}
    for frame in (0, 1):
        for mask in range(1, 16):
            out[f"{prefix}.{mask}.{frame}"] = water_edge(land_fn(), mask, frame, kind=kind)
        for corner in INNER:
            out[f"{prefix}.inner.{corner}.{frame}"] = water_edge(land_fn(), 0, frame, inner=corner, kind=kind)
    return out


def _desert_land():
    t = desert_sand(0)
    t.ramps["sand"] = t.ramps["desert.sand"]
    return t


# ---------------------------------------------------------------------------------------------
# 2. Cliff band variants (other detail positions, the same edge profiles)
# ---------------------------------------------------------------------------------------------
def _shift_table(table, dx):
    """Detail positions moved along the band; a detail that would cross the tile's edge is left out, so the
    edge columns (where the next tile, of any variant, joins) stay plain."""
    out = {}
    for k, v in table.items():
        out[k] = []
        for x, y, p in v:
            x = (x + dx) % 32
            width = len(p) if isinstance(p, str) else max(len(r) for r in p)
            if 1 <= x and x + width <= 31:
                out[k].append((x, y, p))
    return out


EARTH_VAR = {
    1: dict(CLODS=_shift_table(S.CLODS, 11), STONE_AT={("mid", 16): (6, 5), ("mid-base", 16): (25, 4), ("mid", 8): (14, 1)},
            HANG={2: 1, 12: 2, 21: 1, 27: 1}, LEDGE_GAPS={3, 14, 15, 24}),
    2: dict(CLODS=_shift_table(S.CLODS, 21), STONE_AT={("mid", 16): (15, 3), ("top", 16): (8, 11)},
            HANG={7: 2, 15: 1, 23: 1, 29: 2}, LEDGE_GAPS={10, 11, 22, 30}),
}
STONE_VAR = {
    1: dict(FACETS=_shift_table(F.FACETS, 9), CRACKS=[(4, 2, 3), (22, 1, 4), (26, 3, 3)], SNOW_HANG={3: 2, 13: 1, 20: 1, 28: 2},
            LEDGE_GAPS={2, 13, 14, 25}),
    2: dict(FACETS=_shift_table(F.FACETS, 19), CRACKS=[(11, 1, 3), (18, 2, 4)], SNOW_HANG={8: 1, 16: 2, 23: 1, 29: 1},
            LEDGE_GAPS={9, 20, 21, 29}),
}


def _courses(table, dx):
    return {k: [(y0, hc, (st + dx) % 32, ws[::-1]) for y0, hc, st, ws in v] for k, v in table.items()}


RUIN_VAR = {1: dict(RUIN_COURSES=_courses(F.RUIN_COURSES, 9)), 2: dict(RUIN_COURSES=_courses(F.RUIN_COURSES, 22))}
WALL_VAR = {
    1: dict(PLASTER_MARKS=_shift_table(F.PLASTER_MARKS, 10), BEAM_JOINT=6),
    2: dict(PLASTER_MARKS=_shift_table(F.PLASTER_MARKS, 23), BEAM_JOINT=28),
}
KINDS = ("top", "mid", "mid-base", "top-base")


def earth_face(kind, seg, var=0):
    if not var:
        return S.face_tile(kind, seg)
    with patched(S, **EARTH_VAR[var]):
        return S.face_tile(kind, seg)


def face_variants():
    out = {}
    for var in (1, 2):
        for seg in (4, 8):
            for kind in KINDS:
                out[f"face.earth.{kind}.{seg}.v{var}"] = earth_face(kind, seg, var)
                with patched(F, **STONE_VAR[var]):
                    out[f"face.stone.{kind}.{seg}.v{var}"] = F.stone_face(kind, seg)
                with patched(F, **RUIN_VAR[var]):
                    out[f"face.ruin.{kind}.{seg}.v{var}"] = F.ruin_face(kind, seg)
                with patched(F, **WALL_VAR[var]):
                    out[f"face.wall.{kind}.{seg}.v{var}"] = F.wall_face(kind, seg)
    return out


def season_lip_variants(autumn_lip, winter_lip):
    """autumn / winter earth lips for the variants (gen_release's seasonal lips, drawn on the variant)."""
    out = {}
    for var in (1, 2):
        with patched(S, **EARTH_VAR[var]):
            for seg in (4, 8):
                for kind in ("top", "top-base"):
                    out[f"autumn.face.earth.{kind}.{seg}.v{var}"] = autumn_lip(kind, seg)
                    out[f"winter.face.earth.{kind}.{seg}.v{var}"] = winter_lip(kind, seg)
    return out


# ---------------------------------------------------------------------------------------------
# 3. Plateau faces: the earth face drawn with other ramps, tone for tone (palette shift): a body darker
#    than the ground on top (guide 3.4), and a lip of the top ground's own colour instead of the grass.
# ---------------------------------------------------------------------------------------------
PLATEAU = {  # name: (body ramp, lip ramp)
    "sand": ("desert.stone", "island.sand"),  # pale beach sand over a tan sandstone bank
    "desert": ("earth.face", "desert.sand"),  # red desert sand over brown earth
    "path": ("earth.face", "plains.path"),  # a dirt path's edge over earth
}


def plateau_face(name, kind, seg):
    body, lip = PLATEAU[name]
    t = S.face_tile(kind, seg)
    set_ramp(t, "earth", body)
    set_ramp(t, "grass", lip)
    return t


def plateau_faces():
    return {f"face.{n}.{kind}.{seg}": plateau_face(n, kind, seg) for n in PLATEAU for seg in (4, 8) for kind in KINDS}


# ---------------------------------------------------------------------------------------------
# 4. Autumn in the forest and the mountains
# ---------------------------------------------------------------------------------------------
LEAF_A = ["12", "2."]
LEAF_B = [".2", "21"]
LEAF_C = ["21", ".1"]
FOREST_LEAVES = {  # fallen leaves (fire 1-2, guide 3.7), at different heights per variant
    0: [(9, 6, LEAF_A), (24, 21, LEAF_C)],
    1: [(26, 4, LEAF_B), (13, 25, LEAF_A), (2, 16, LEAF_C)],
    2: [(6, 13, LEAF_C), (28, 28, LEAF_B)],
    3: [(18, 19, LEAF_A), (3, 29, LEAF_B), (29, 9, LEAF_C)],
}


def autumn_forest_grass(v):
    t = forest_grass(v)
    set_ramp(t, "forest.moss", "forest.swamp")  # the moss dries olive-brown
    set_ramp(t, "fire", "fire")
    for x, y, p in FOREST_LEAVES[v]:
        t.stamp(x, y, p, tones("fire"))
    return t


SCREE_TUFTS = {  # dry grass (lake.reed) on the scree, at different heights per variant
    0: [(5, 10, TUFT_S), (22, 24, SPRIG)],
    1: [(20, 18, TUFT_M), (3, 27, TUFT_S)],
    2: [(25, 6, SPRIG), (4, 20, TUFT_S)],
    3: [(14, 14, TUFT_M), (27, 29, SPRIG)],
}


def autumn_mountains_ground(v):
    """No snow in autumn: the snow becomes scree (mount.rock, tone for tone, so the drifts become low
    ridges), the ice patch a small pool (water.surface), and tufts of dry grass are drawn on it."""
    t = mountains_snow(v)
    set_ramp(t, "mount.snow", "mount.rock")
    set_ramp(t, "mount.ice", "water.surface")
    set_ramp(t, "lake.reed", "lake.reed")
    for x, y, p in SCREE_TUFTS[v]:
        t.stamp(x, y, p, tones("lake.reed"))
    for y in range(32):  # no bright 4 on the scree (the snow's sparkle would read as snow)
        for x in range(32):
            if t.px[y][x] == ("mount.snow", 4):
                t.px[y][x] = ("mount.snow", 3)
    return t


def autumn_stone_lip(kind, seg, var=0):
    """The mountain cliff's lip without snow: dry grass (lake.reed, tone for tone)."""
    ctx = patched(F, **STONE_VAR[var]) if var else contextlib.nullcontext()
    with ctx:
        t = F.stone_face(kind, seg)
    set_ramp(t, "mount.snow", "lake.reed")
    for y in range(t.h):
        for x in range(t.w):
            if t.px[y][x] == ("mount.snow", 4):
                t.px[y][x] = ("mount.snow", 3)
    return t


GOLDEN = [(11, 10), (18, 19), (8, 28), (21, 31), (5, 41), (24, 42), (9, 48), (20, 50)]  # dried needle tips


def autumn_forest_pine():
    t = pine()
    set_ramp(t, "autumn.grass", "autumn.grass")
    for x, y in GOLDEN:
        for dx in (0, 1):
            v = t.get(x + dx, y)
            if v and v[0] == "forest.pine" and v[1] > 0:
                t.put(x + dx, y, "autumn.grass", 3 if v[1] >= 3 else 2)
    return t


def autumn_set():
    out = {}
    for v in range(4):
        out[f"autumn.forest.grass.{v}"] = autumn_forest_grass(v)
        out[f"autumn.mountains.snow.{v}"] = autumn_mountains_ground(v)
    out["autumn.forest.pine"] = autumn_forest_pine()
    out["autumn.mountains.pine"] = pine(slim=True)
    for seg in (4, 8):
        for kind in ("top", "top-base"):
            out[f"autumn.face.stone.{kind}.{seg}"] = autumn_stone_lip(kind, seg)
            for var in (1, 2):
                out[f"autumn.face.stone.{kind}.{seg}.v{var}"] = autumn_stone_lip(kind, seg, var)
    return out


def build_v11(autumn_lip, winter_lip):
    out = {}
    out.update(shore_set("tile.shore", S.sand_tile, "sand"))
    out.update(shore_set("tile.shore-desert", _desert_land, "sand"))
    out.update(shore_set("tile.bank", lambda: None, "bank"))
    out.update(face_variants())
    out.update(season_lip_variants(autumn_lip, winter_lip))
    out.update(plateau_faces())
    out.update(autumn_set())
    return out
