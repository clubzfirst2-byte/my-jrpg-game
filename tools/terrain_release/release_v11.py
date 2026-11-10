"""Terrain v1.1 (art/terrain-v1-1): NEW sprites only, added next to the 111 of v1.0 (which stay as they are).

  1. water edges: tile.shore.* (island sand), tile.shore-desert.* (red desert sand), tile.bank.* (an overlay
     for any grass-like ground: island / plains / lake grass, forest moss, mountain snow, their seasons)
     - <mask>.<frame>: mask = which sides touch water (N 1, E 2, S 4, W 8; 1-15), 2 frames like tile.water
     - inner.<ne|se|sw|nw>.<frame>: only that diagonal neighbour is water
  2. cliff band variants: face.<earth|ruin|wall|stone>.<part>.v1 / .v2 (+ the earth lips' autumn / winter)
  3. plateau faces: face.sand.* (island sand), face.desert.* (red desert sand), face.path.*
  4. autumn for the forest and the mountains: autumn.forest.grass.0-3, autumn.forest.pine,
     autumn.mountains.snow.0-3 (partial snow: bare warm rock and dry grass), autumn.mountains.pine,
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
LAP = {6, 7, 8, 22, 23, 24}  # ripples just off the foam (small pieces only, see water_edge)
LAP_DENSE = {p for p in range(32) if p % 4 in (1, 2)}  # the inner corners' small notch of water
INNER = {"ne": (N, E), "se": (SO, E), "sw": (SO, W), "nw": (N, W)}


def _round_out(a, b):
    """A land corner (a, b = px inside the land from two water edges) is cut round into the water."""
    return 0 <= a < R and 0 <= b < R and (R - a - 0.5) ** 2 + (R - b - 0.5) ** 2 > R * R


ISLET = [  # mask 15 (water on all 4 sides): a low sandbar, longer than wide, hand-drawn ("#" = land)
    "..........................",
    "..........#######.........",
    ".......#############......",
    ".....#################....",
    "...#####################..",
    "..######################..",
    "..#######################.",
    "...#####################..",
    "....###################...",
    "......##############......",
    "..........######..........",
]
ISLET_AT = (3, 11)  # top-left of the drawing in the tile


def is_water(x, y, mask=0, inner=None):
    xm, ym = x % 32, y % 32
    if mask == 15 and not inner:  # the islet: a drawn shape, water all round (the edges stay water)
        ix, iy = x - ISLET_AT[0], y - ISLET_AT[1]
        return not (0 <= iy < len(ISLET) and 0 <= ix < len(ISLET[0]) and ISLET[iy][ix] == "#")
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


def water_edge(land, mask, frame, inner=None, kind="sand", moving=None, lap=False):
    """land: a Tile (the land under the tile) or None for an overlay. kind: 'sand' (a wet band on the
    land side) or 'bank' (a 1-2 px earth bank, the land side transparent elsewhere). moving: in frame 1,
    how many foam pixels (in reading order) take the moved foam pattern (None = all); the others keep
    frame 0's, so each piece's two frames differ by 12-30 px like tile.water (guide 3.5). lap: short
    lit ripples one px further out (moving 2 px per frame), for the small pieces whose foam alone moves too
    little."""
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
    foam_n = 0
    for y in range(32):
        for x in range(32):
            if (x, y) in wet:
                if any(not wat(x + dx, y + dy) for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0))):
                    along = y if (not wat(x - 1, y) or not wat(x + 1, y)) else x  # along a side edge: y
                    f = frame if (moving is None or foam_n < moving) else 0
                    foam_n += 1
                    t.put(x, y, "water", 4 if (along + 2 * f) % 32 in FOAM else 3)
                elif lap and any(not wat(x + dx, y + dy) for dx in (-2, 0, 2) for dy in (-2, 0, 2)):
                    along = y if (not wat(x - 2, y) or not wat(x + 2, y)) else x
                    if (along + 2 * frame) % 32 in lap:
                        t.put(x, y, "water", 3)
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


def _diff(a, b):
    return sum(1 for p, q in zip(a.image().get_flattened_data(), b.image().get_flattened_data()) if p != q)


def _pair(land_fn, kind, mask, inner):
    """Frame 0 and a frame 1 whose difference is in the guide's 12-30 px (closest to 20): as much of the
    foam moves as keeps it there."""
    best = None
    for lap in (False, LAP, LAP_DENSE):
        f0 = water_edge(land_fn(), mask, 0, inner=inner, kind=kind, lap=lap)
        for n in [None] + list(range(200, -1, -4)):
            f1 = water_edge(land_fn(), mask, 1, inner=inner, kind=kind, moving=n, lap=lap)
            d = _diff(f0, f1)
            score = (0 if 12 <= d <= 30 else 1, abs(d - 20))
            if best is None or score < best[0]:
                best = (score, f0, f1)
            if score == (0, 0) or (n is None and d < 12):
                break
        if best[0][0] == 0:
            break
    return best[1], best[2]


def shore_set(prefix, land_fn, kind):
    out = {}
    for mask in range(1, 16):
        out[f"{prefix}.{mask}.0"], out[f"{prefix}.{mask}.1"] = _pair(land_fn, kind, mask, None)
    for corner in INNER:
        out[f"{prefix}.inner.{corner}.0"], out[f"{prefix}.inner.{corner}.1"] = _pair(land_fn, kind, 0, corner)
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
    """v0 and one variant .v1 (the earth face's v1 detail positions), so the pebbles do not repeat every 32 px."""
    out = {f"face.{n}.{kind}.{seg}": plateau_face(n, kind, seg) for n in PLATEAU for seg in (4, 8) for kind in KINDS}
    with patched(S, **EARTH_VAR[1]):
        out.update({f"face.{n}.{kind}.{seg}.v1": plateau_face(n, kind, seg) for n in PLATEAU for seg in (4, 8) for kind in KINDS})
    return out


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


# Autumn in the mountains (director's decision after the v1.1 inspection): PARTIAL snow. The summer snow
# ground with bare patches (about 20-30 % of the tile) of warm rock (desert.stone) and dry ochre grass
# (autumn.grass), at different places per variant. The patches wrap like everything on a ground tile.
BARE = {  # the bare patches per variant: each a few overlapping ellipses (cx, cy, rx, ry), hand-placed and
    # kept 1 px inside the tile (a patch cut by the tile's edge would not continue on a neighbour of another variant)
    0: [[(8, 9, 6, 3.5), (12, 11, 5, 3), (4, 11, 3, 2)], [(23, 23, 5, 3), (19, 25, 4, 2.5), (26, 26, 3, 2.5)]],
    1: [[(21, 7, 6, 3.5), (25, 9.5, 4.5, 3), (16, 9, 3, 2)], [(8, 22, 6, 3.5), (5, 25, 4, 2.5), (12, 24, 3, 2)]],
    2: [[(15, 15, 7, 4), (20, 18.5, 5, 3), (10, 18.5, 3.5, 2.5)], [(26, 5, 3.5, 2.5), (28.5, 7, 2, 1.5)]],
    3: [[(24, 12, 5, 3.5), (20.5, 15.5, 4, 2.5), (27, 15, 2.5, 2)], [(9, 26, 6, 3), (14, 24, 4, 2.5), (4, 27, 2.5, 2)]],
}
BARE_GRASS = {  # dry grass tufts, drawn only on the bare rock
    0: [(5, 8, TUFT_S), (21, 23, SPRIG), (11, 10, SPRIG)],
    1: [(20, 5, TUFT_M), (5, 21, TUFT_S), (10, 23, SPRIG)],
    2: [(12, 14, TUFT_M), (19, 17, SPRIG), (25, 4, SPRIG)],
    3: [(22, 11, TUFT_S), (7, 24, TUFT_M)],
}
BARE_STONES = {0: [(13, 8), (25, 24)], 1: [(24, 8), (9, 21)], 2: [(17, 17)], 3: [(25, 13), (12, 25)]}


def autumn_mountains_ground(v):
    t = mountains_snow(v)
    for m in ("desert.stone", "autumn.grass"):
        set_ramp(t, m, m)
    bare = set()
    for patch in BARE[v]:
        for cx, cy, rx, ry in patch:
            rx, ry = rx * 1.2, ry * 1.2  # about 20-30 % of the ground bare (director, v1.1 inspection)
            for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
                for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                    if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1 and 1 <= x <= 30 and 1 <= y <= 30:
                        bare.add((x, y))
    for x, y in bare:
        up, down = ((x, (y - 1) % 32) in bare), ((x, (y + 1) % 32) in bare)
        left, right = (((x - 1) % 32, y) in bare), (((x + 1) % 32, y) in bare)
        tone = 2
        if not up:
            tone = 1  # the snow bank above casts a shadow on the rock
        elif not down or not right:
            tone = 3 if left else 2  # the lower right rim catches the light from the top left
        t.put(x, y, "desert.stone", tone)
    for x, y in bare:  # the snow's edge around the patch: a lit rim on top, a shaded rim below
        for dx, dy, tone in ((0, -1, 3), (0, 1, 1), (1, 0, 2), (-1, 0, 3)):
            q = ((x + dx) % 32, (y + dy) % 32)
            if q not in bare and t.px[q[1]][q[0]] and t.px[q[1]][q[0]][0] == "mount.snow":
                t.put(q[0], q[1], "mount.snow", tone)
    for x, y, p in BARE_GRASS[v]:
        t.stamp(x, y, p, tones("autumn.grass"), only_on="desert.stone")
    for x, y in BARE_STONES[v]:
        t.stamp(x, y, ["43", "32"], tones("desert.stone"), only_on="desert.stone")
    return t


LIP_BARE = [(5, 12), (20, 26)]  # x ranges where the autumn lip shows dry grass instead of snow


def autumn_stone_lip(kind, seg, var=0):
    """The mountain cliff's snow lip with bare stretches of dry grass (autumn.grass, tone for tone)."""
    ctx = patched(F, **STONE_VAR[var]) if var else contextlib.nullcontext()
    with ctx:
        t = F.stone_face(kind, seg)
    set_ramp(t, "autumn.grass", "autumn.grass")
    shift = 7 * var
    for y in range(t.h):
        for x in range(t.w):
            v = t.px[y][x]
            if v and v[0] == "mount.snow" and any(a <= (x - shift) % 32 <= b for a, b in LIP_BARE):
                t.px[y][x] = ("autumn.grass", min(3, v[1]))
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
    out["autumn.mountains.pine"] = pine(snow=1, slim=True)  # a light snow, as on the partly snowy ground
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
