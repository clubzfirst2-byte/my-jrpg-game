"""Reference renderer for ground v2 (what the engine should do; used for the review images).

Input: a grid of ground classes, one character per map cell:
  g island grass, p plains grass, l lake grass, m forest moss, n mountain snow, s island sand,
  d desert sand, = path, u ruin floor, ~ water; anything else is drawn with its v1 tile on the cell grid.
Steps (NAMES.md has the same in words):
  1. water cells are DEEP when no land cell is within 2 cells (Chebyshev) and they lie in a 2x2 block of such
     cells; else SHALLOW
  2. the display grid is shifted half a tile: display tile (i, j) has corners on the cells
     (i, j) NW, (i+1, j) NE, (i, j+1) SW, (i+1, j+1) SE and is drawn at ((i + .5) * 32, (j + .5) * 32)
  3. every ground but the ruin (scheme A, round 5): at most one 2x2 picture per 3x3 block (density noise, offsets
     0 / 1 / 2, no block with the picture of any of its 8 neighbours), else one of 32 calm tiles (light / dark group
     by a noise, never the number of any of its 8 neighbours); ruin: row
     phase + column symbols
  4. per display tile: the lowest terrain among its corners as a full tile (water: shallow, or deep if all
     4 corners are deep), then
       water: the deep overlay (mask = deep corners) if mixed; the foam overlay (mask = land corners)
       land: for each higher terrain present, low to high, its overlay with mask = corners whose
       priority >= that terrain
"""

import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from transitions import PRIORITY  # noqa: E402

CLASS = {"g": "grass", "p": "plains", "l": "lake", "m": "moss", "n": "snow", "s": "sand", "d": "dsand", "=": "path", "u": "ruin",
         "~": "water"}
V1_OTHER = {"M": "tile.metal", "W": "tile.walltop", "w": "tile.wood", "%": "tile.dark", "_": "tile.pit"}


def dhash(i, j):
    """gameView.js hash() (the same as tools/terrain_release/mock_scene.tile_hash)."""
    h = (i * 374761393 + j * 668265263) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return (h ^ (h >> 16)) & 0xFFFFFFFF


def depth_map(grid):
    """Deep water: a water cell with no land within 2 cells (Chebyshev) AND inside a 2x2 block of such cells
    (a 1-cell-wide strip stays shallow, so the deep colour never makes a dark 1-cell trench)."""
    H, W = len(grid), len(grid[0])
    land = {(x, y) for y in range(H) for x in range(W) if grid[y][x] != "~"}
    cand = {(x, y) for y in range(H) for x in range(W)
            if grid[y][x] == "~" and not any((x + dx, y + dy) in land for dx in range(-2, 3) for dy in range(-2, 3))}
    deep = set()
    for x, y in cand:
        for ax in (x - 1, x):
            for ay in (y - 1, y):
                if all((ax + dx, ay + dy) in cand for dx in (0, 1) for dy in (0, 1)):
                    deep.add((x, y))
    return deep


def terr(grid, x, y):
    H, W = len(grid), len(grid[0])
    x, y = max(0, min(W - 1, x)), max(0, min(H - 1, y))
    return CLASS.get(grid[y][x], "other")


def lowest_land(grid, i, j):
    ts = [terr(grid, i + dx, j + dy) for dy in (0, 1) for dx in (0, 1)]
    if "water" in ts or "other" in ts:
        return None
    return min(ts, key=PRIORITY.index)


BUSY_MACRO = {"grass", "plains", "lake", "moss", "path", "snow", "sand", "dsand"}  # the grounds with pictures (scheme A)
N_MACRO = 8
MACRO_NAMES = ["macro"] + [f"macro{k}" for k in range(2, N_MACRO + 1)]
_SEASON = None

# Round 5 placement (NAMES.md 1 A). Offsets 0 / 1 / 2 tiles with these chances per axis (hash % 6), and an
# offset 2 (the picture reaches one tile into the next block) taken back to 1 where it would meet the next
# block's picture: every column / row of a block is then covered equally often (2/3 of the blocks).
OFF = [0, 0, 1, 2, 2, 2]
NOISE_CELL = 4  # blocks per cell of the density noise


def raw_offsets(a, b):
    h = dhash(a, b)
    return OFF[h % 6], OFF[(h >> 8) % 6]


def offsets(a, b):
    ox, oy = raw_offsets(a, b)
    if ox == 2 and raw_offsets(a + 1, b)[0] == 0:
        ox = 1
    if oy == 2 and raw_offsets(a, b + 1)[1] == 0:
        oy = 1
    if ox == 2 and oy == 2 and raw_offsets(a + 1, b + 1) == (0, 0):
        oy = 1
    if ox == 2 and oy == 0 and raw_offsets(a + 1, b - 1) == (0, 2):
        ox = 1
    return ox, oy


def density(a, b):
    """0..1, a smooth noise over the blocks: value noise on a lattice of NOISE_CELL blocks, smoothstep-blended."""
    return _smooth_noise(a, b, NOISE_CELL, 5003, 7919)


def raw_picture(a, b):
    return dhash(a + 409, b + 1031) % N_MACRO


_PIC = {}


def picture(a, b):
    """Round 6: no block shares its picture with any of its 8 neighbours where it can be helped. The blocks are
    taken in 4 classes by (a % 2, b % 2): A (0, 0) keeps its raw number; B (1, 0) avoids its A neighbours; C (0, 1)
    its A and B neighbours; D (1, 1) all 8 neighbours (if that leaves nothing: its 4 side neighbours). The choice is
    the k-th free number, k = floor(hash(a + 409, b + 1031) / 8) % len(free)."""
    if (a, b) in _PIC:
        return _PIC[(a, b)]
    cls = (a % 2, b % 2)
    if cls == (0, 0):
        m = raw_picture(a, b)
    else:
        if cls == (1, 0):
            nb = [(a - 1, b), (a + 1, b)]
        elif cls == (0, 1):
            nb = [(a, b - 1), (a, b + 1), (a - 1, b - 1), (a + 1, b - 1), (a - 1, b + 1), (a + 1, b + 1)]
        else:
            nb = [(a + da, b + db) for da in (-1, 0, 1) for db in (-1, 0, 1) if (da, db) != (0, 0)]
        free = [m for m in range(N_MACRO) if m not in {picture(*q) for q in nb}]
        if not free:  # D only
            free = [m for m in range(N_MACRO) if m not in {picture(*q) for q in [(a - 1, b), (a + 1, b), (a, b - 1), (a, b + 1)]}]
        m = free[dhash(a + 409, b + 1031) // N_MACRO % len(free)]
    _PIC[(a, b)] = m
    return m


def _smooth_noise(x, y, cell, sx_, sy_):
    """Value noise in [0, 1]: lattice values (hash(gx + sx_, gy + sy_) % 1024) / 1023 every `cell` units,
    smoothstep-blended (NAMES.md 1 A)."""
    gx, gy = x // cell, y // cell
    fx, fy = (x % cell + 0.5) / cell, (y % cell + 0.5) / cell
    v = lambda p, q: (dhash(p + sx_, q + sy_) % 1024) / 1023
    sx, sy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    top = v(gx, gy) + (v(gx + 1, gy) - v(gx, gy)) * sx
    bot = v(gx, gy + 1) + (v(gx + 1, gy + 1) - v(gx, gy + 1)) * sx
    return top + (bot - top) * sy


MOTTLE_CELL = 6  # display tiles per cell of the light / dark noise
MOTTLE_SLOPE = 0.8  # how far the mix of the two groups swings (0.5 +- 0.4 at the noise's extremes)


def calm_group(i, j):
    """0 = the light calm tiles (0-15), 1 = the dark ones (16-31), mixed by a large noise (round 6)."""
    n = _smooth_noise(i, j, MOTTLE_CELL, 12011, 3407)
    q = min(1.0, max(0.0, MOTTLE_SLOPE * (n - 0.5) + 0.5))
    return 1 if (dhash(i + 71, j + 113) % 1024) / 1024 < q else 0


def calm_raw(i, j):
    return 16 * calm_group(i, j) + dhash(i + 3, j + 11) % 16


_CALMN = {}


def calm_number(i, j):
    """No calm tile shares its number with any of its 8 neighbours: the display tiles are taken in 4 classes by
    (i % 2, j % 2), as the picture blocks: A (0, 0) keeps its raw number; B (1, 0) avoids its A neighbours
    (i +- 1, j); C (0, 1) its A neighbours (i, j +- 1) and B neighbours (i +- 1, j +- 1); D (1, 1) all 8. The
    choice is in the tile's own group: the k-th of the 16 numbers of the group not avoided,
    k = (hash(i + 3, j + 11) >> 4) % len(free)."""
    if (i, j) in _CALMN:
        return _CALMN[(i, j)]
    r = calm_raw(i, j)
    cls = (i % 2, j % 2)
    if cls == (0, 0):
        n = r
    else:
        if cls == (1, 0):
            nb = [(i - 1, j), (i + 1, j)]
        elif cls == (0, 1):
            nb = [(i, j - 1), (i, j + 1), (i - 1, j - 1), (i + 1, j - 1), (i - 1, j + 1), (i + 1, j + 1)]
        else:
            nb = [(i + di, j + dj) for di in (-1, 0, 1) for dj in (-1, 0, 1) if (di, dj) != (0, 0)]
        g = r // 16
        taken = {calm_number(*q) for q in nb}
        free = [16 * g + k for k in range(16) if 16 * g + k not in taken]
        n = free[(dhash(i + 3, j + 11) >> 4) % len(free)]
    _CALMN[(i, j)] = n
    return n


def dune(a, b):
    """Desert blocks (round 8): one dune per cell of 4 x 3 blocks, on a hashed block of the cell; its shape 1-6
    from the cell's place in a 3 x 2 pattern of cells, turned by a hash per pattern (so the 6 shapes are spread
    out and none comes twice close together). 0 = no dune (NAMES.md 1 A, step 4b)."""
    sa, sb = a // 4, b // 3
    hs = dhash(sa + 77, sb + 31)
    if (a, b) != (4 * sa + hs % 4, 3 * sb + (hs >> 2) % 3):
        return 0
    return 1 + (sa % 3 + 3 * (sb % 2) + dhash(sa // 3 + 13, sb // 2 + 29)) % 6


def p_none(a, b):
    """The chance that block (a, b) has no picture: 0 where the noise is under 0.3 (thick), 1 over 0.8 (bare)."""
    return min(1.0, max(0.0, 2 * (density(a, b) - 0.3)))


def has_picture(a, b):
    return ((dhash(a, b) >> 16) % 1024) / 1024 >= p_none(a, b)


def macro_blocks(grid):
    """Display tiles drawn with a 2x2 picture (rounds 5-6; NAMES.md 1 A)."""
    _PIC.clear()
    _CALMN.clear()
    H, W = len(grid), len(grid[0])
    out = {}
    for b in range((H + 2) // 3 + 1):
        for a in range((W + 2) // 3 + 1):
            ox, oy = offsets(a, b)
            i, j = 3 * a + ox, 3 * b + oy
            if i + 2 >= W or j + 2 >= H:
                continue
            ts = {terr(grid, i + dx, j + dy) for dx in range(3) for dy in range(3)}
            if len(ts) != 1 or next(iter(ts)) not in BUSY_MACRO:
                continue
            k = dune(a, b) if ts == {"dsand"} else 0
            if k:
                name = f"dune{k}"
            elif not has_picture(a, b):
                continue
            else:
                name = MACRO_NAMES[picture(a, b)]
            for q in range(4):
                assert (i + q % 2, j + q // 2) not in out, "pictures overlap"
                out[(i + q % 2, j + q // 2)] = (name, q, (i, j, 2))
    return out


from wang import TEX4, LINE_GROUNDS, index_of, ruin_row, ruin_symbol  # noqa: E402


def edge_type(grid, a, b, edge_id):
    """Sand / desert / snow: the phase 0-7 of a vertical edge between display tiles a and b = (hash >> 8) % 8,
    0 when the two tiles' lowest grounds differ (NAMES.md)."""
    if lowest_land(grid, *a) != lowest_land(grid, *b):
        return 0
    return (dhash(*edge_id) >> 8) % 8


def mask_of(grid, t, i, j):
    """The overlay mask of terrain t on display tile (i, j): its corners whose priority is >= t's."""
    ts = [terr(grid, *c) for c in [(i, j), (i + 1, j), (i, j + 1), (i + 1, j + 1)]]
    return sum(b for b, tt in zip((1, 2, 4, 8), ts) if tt in PRIORITY and PRIORITY.index(tt) >= PRIORITY.index(t))


SIDE_GEOM = {  # side: (edge hash args, its two end cells, the display tile across it)
    "N": (lambda i, j: (2 * i + 1, 2 * j), lambda i, j: [(i, j), (i + 1, j)], lambda i, j: (i, j - 1)),
    "E": (lambda i, j: (2 * i + 2, 2 * j + 1), lambda i, j: [(i + 1, j), (i + 1, j + 1)], lambda i, j: (i + 1, j)),
    "S": (lambda i, j: (2 * i + 1, 2 * j + 2), lambda i, j: [(i, j + 1), (i + 1, j + 1)], lambda i, j: (i, j + 1)),
    "W": (lambda i, j: (2 * i, 2 * j + 1), lambda i, j: [(i, j), (i, j + 1)], lambda i, j: (i - 1, j)),
}


def side_state(grid, t, i, j, sd):
    """Round 7 (NAMES.md 2): 0 or 1 for a side of display tile (i, j) that terrain t's border crosses."""
    hargs, ends, across = SIDE_GEOM[sd]
    if any(terr(grid, *c) == "water" for c in ends(i, j)):
        return 0  # shores: the foam's curve
    if mask_of(grid, t, *across(i, j)) in (6, 9) or mask_of(grid, t, i, j) in (6, 9):
        return 0
    return (dhash(*hargs(i, j)) >> 4) & 1


def edge_variant(grid, t, m, i, j):
    """The overlay variant of terrain t (mask m) on display tile (i, j)."""
    if m in (6, 9):
        return dhash(i + 7, j) % 2
    from transitions import crossing_sides
    a, b = crossing_sides(m)
    return side_state(grid, t, i, j, a) + 2 * side_state(grid, t, i, j, b)


def render_v2(grid, images, frame=0, season=None):
    global _SEASON
    _SEASON = season
    H, W = len(grid), len(grid[0])
    sp = f"{season}." if season else ""
    seasonal = {"grass", "plains", "lake", "moss"}

    def key(base, name):
        k = f"{sp}g2.{base}.{name}" if (season and base in seasonal) else f"g2.{base}.{name}"
        return images[k]

    deep = depth_map(grid)
    macro = macro_blocks(grid)
    im = Image.new("RGBA", (W * 32, H * 32), (0, 0, 0, 255))
    for j in range(H - 1):
        for i in range(W - 1):
            cells = [(i, j), (i + 1, j), (i, j + 1), (i + 1, j + 1)]
            ts = [terr(grid, *c) for c in cells]
            px, py = i * 32 + 16, j * 32 + 16
            land = [t for t in ts if t not in ("water", "other")]
            if "water" in ts:
                isdeep = [c in deep for c in cells]
                v = dhash(i, j) % 2
                base = "deep" if all(isdeep) else "shallow"
                im.alpha_composite(images[f"g2.water.{base}.{v}.{frame}"], (px, py))
                if any(isdeep) and not all(isdeep):
                    m = sum(b for b, d in zip((1, 2, 4, 8), isdeep) if d)
                    im.alpha_composite(images[f"g2.water.deep.e{m}.{frame}"], (px, py))
                if land:
                    m = sum(b for b, t in zip((1, 2, 4, 8), ts) if t != "water")
                    if m != 15:
                        im.alpha_composite(images[f"g2.water.foam.e{m}.{frame}"], (px, py))
                lowest = None
            else:
                lowest = min(land, key=PRIORITY.index) if land else None
                if lowest:
                    mk = macro.get((i, j))
                    look = "snow" if (season == "winter" and lowest in seasonal) else lowest
                    if mk:
                        name = f"{mk[0]}.{mk[1]}"
                    elif look == "ruin":  # row phase + the symbols of the column's two edges
                        name = str(index_of({"R": ruin_row(j), 8: ruin_symbol(i, dhash), 2: ruin_symbol(i + 1, dhash)}, look))
                    elif look in LINE_GROUNDS:  # the phases of its W and E edges
                        name = str(index_of({1: 0, 4: 0, 2: edge_type(grid, (i, j), (i + 1, j), (2 * i + 2, 2 * j + 1)),
                                             8: edge_type(grid, (i - 1, j), (i, j), (2 * i, 2 * j + 1))}, look))
                    else:  # a calm tile: any of the 16
                        name = str(calm_number(i, j))
                    im.alpha_composite(key(lowest, name), (px, py))
            for t in sorted(set(land), key=PRIORITY.index):
                if t == lowest:
                    continue
                m = sum(b for b, tt in zip((1, 2, 4, 8), ts) if tt in PRIORITY and PRIORITY.index(tt) >= PRIORITY.index(t))
                if m == 15:
                    im.alpha_composite(key(t, "0"), (px, py))
                else:
                    v = ruin_row(j) if t == "ruin" else edge_variant(grid, t, m, i, j)
                    im.alpha_composite(key(t, f"e{m}.{v}"), (px, py))
    for y in range(H):  # other grounds: their v1 tile, on the cell grid
        for x in range(W):
            if grid[y][x] in V1_OTHER:
                im.paste(images["v1:" + V1_OTHER[grid[y][x]]], (x * 32, y * 32))
    return im.crop((16, 16, W * 32 - 16, H * 32 - 16))


def render_v1(grid, v1):
    """The current look (v1 / v1.1 terrain on the cell grid, frame 0), cropped like render_v2."""
    H, W = len(grid), len(grid[0])
    im = Image.new("RGBA", (W * 32, H * 32), (0, 0, 0, 255))
    region = {"g": "tile.grass.{}", "p": "plains.grass.{}", "l": "lake.grass.{}", "m": "forest.grass.{}", "n": "mountains.snow.{}",
              "s": "tile.sand", "d": "desert.sand.{}", "=": "tile.path", "u": "tile.ruin", "~": "tile.water.0"}
    count = {"g": 3, "p": 4, "l": 4, "m": 4, "n": 4, "d": 3}

    def w(x, y):
        return 0 <= y < H and 0 <= x < W and grid[y][x] == "~"

    for y in range(H):
        for x in range(W):
            c = grid[y][x]
            if c in V1_OTHER:
                im.paste(v1[V1_OTHER[c]], (x * 32, y * 32))
                continue
            n = count.get(c, 1)
            k = dhash(x, y) % (2 * n)
            var = 0 if k <= n else k - n
            im.paste(v1[region[c].format(var)], (x * 32, y * 32))
            if c != "~":
                mask = (1 if w(x, y - 1) else 0) | (2 if w(x + 1, y) else 0) | (4 if w(x, y + 1) else 0) | (8 if w(x - 1, y) else 0)
                if mask:
                    if c == "s":
                        im.paste(v1[f"tile.shore.{mask}.0"], (x * 32, y * 32))
                    elif c == "d":
                        im.paste(v1[f"tile.shore-desert.{mask}.0"], (x * 32, y * 32))
                    elif c in "gplmn":
                        im.alpha_composite(v1[f"tile.bank.{mask}.0"], (x * 32, y * 32))
    return im.crop((16, 16, W * 32 - 16, H * 32 - 16))
