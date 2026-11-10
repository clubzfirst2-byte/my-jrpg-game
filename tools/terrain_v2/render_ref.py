"""Reference renderer for ground v2 (what the engine should do; used for the review images).

Input: a grid of ground classes, one character per map cell:
  g island grass, p plains grass, l lake grass, m forest moss, n mountain snow, s island sand,
  d desert sand, = path, u ruin floor, ~ water; anything else is drawn with its v1 tile on the cell grid.
Steps (NAMES.md has the same in words):
  1. water cells are DEEP when no land cell is within 2 cells (Chebyshev) and they lie in a 2x2 block of such
     cells; else SHALLOW
  2. the display grid is shifted half a tile: display tile (i, j) has corners on the cells
     (i, j) NW, (i+1, j) NE, (i, j+1) SW, (i+1, j+1) SE and is drawn at ((i + .5) * 32, (j + .5) * 32)
  3. macro blocks (3x3 then 2x2) on uniform ground; every other land tile is picked by its 4 edge types
     (n = N + 2E + 4S + 8W; sand / desert / snow: n = E + 8W, E / W 0-7; ruin: n = N + 2E + 16S + 32W, E / W 0-7)
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


BUSY_MACRO = {"grass", "plains", "lake", "moss", "path"}  # macros are placed on these only (on sand / snow / ruin they would force type-0 edges and band the texture)


_SEASON = None


def macro_blocks(grid):
    """Display-tile blocks drawn with macro pieces. 3x3 blocks first (i, j multiples of 3, all 16 corner cells
    one land ground, hash % 6 == 0 -> macro3), then 2x2 blocks (even i, j, all 9 corner cells one ground, not
    overlapping a 3x3 one, hash % 4: 0 -> macro, 1 -> macro2)."""
    H, W = len(grid), len(grid[0])
    out = {}

    def uniform(i, j, k):
        ts = {terr(grid, i + dx, j + dy) for dx in range(k + 1) for dy in range(k + 1)}
        return len(ts) == 1 and next(iter(ts)) not in ("water", "other")

    for j in range(0, H - 3, 3):
        for i in range(0, W - 3, 3):
            g = terr(grid, i, j)
            if g in BUSY_MACRO and _SEASON != "winter" and uniform(i, j, 3) and dhash(i, j) % 6 == 0:
                for q in range(9):
                    out[(i + q % 3, j + q // 3)] = ("macro3", q, (i, j, 3))
    for j in range(0, H - 2, 2):
        for i in range(0, W - 2, 2):
            cells = [(i, j), (i + 1, j), (i, j + 1), (i + 1, j + 1)]
            if any(c in out for c in cells) or not uniform(i, j, 2) or terr(grid, i, j) not in BUSY_MACRO or _SEASON == "winter":
                continue
            h = dhash(i + 1, j) % 4
            if h < 2:
                for q, c in enumerate(cells):
                    out[c] = ("macro" if h == 0 else "macro2", q, (i, j, 2))
    return out


from wang import P_TYPE1 as P_LOOK, TEX4, LINE_GROUNDS, index_of, ruin_row, ruin_symbol  # noqa: E402


def edge_type(grid, macro, a, b, edge_id, look, vertical=False):
    """The type of the edge between display tiles a and b (NAMES.md).
    Sand / desert / snow: a vertical edge has a phase 0-7 = (hash >> 8) % 8, 0 when the two tiles' lowest grounds
    differ; nothing crosses their horizontal edges (0).
    Grass-likes, moss, path: 0 when the two tiles' lowest grounds differ or the edge is on the outside of a macro
    block; else 1 with probability P_LOOK[look] % (hash % 100)."""
    if lowest_land(grid, *a) != lowest_land(grid, *b):
        return 0
    ma, mb = macro.get(a), macro.get(b)
    if (ma or mb) and (ma is None or mb is None or ma[2] != mb[2]):
        return 0
    if look in LINE_GROUNDS:
        return (dhash(*edge_id) >> 8) % 8 if vertical else 0
    return 1 if dhash(*edge_id) % 100 < P_LOOK[look] else 0


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
                    else:
                        t = {1: edge_type(grid, macro, (i, j - 1), (i, j), (2 * i + 1, 2 * j), look),
                             2: edge_type(grid, macro, (i, j), (i + 1, j), (2 * i + 2, 2 * j + 1), look, True),
                             4: edge_type(grid, macro, (i, j), (i, j + 1), (2 * i + 1, 2 * j + 2), look),
                             8: edge_type(grid, macro, (i - 1, j), (i, j), (2 * i, 2 * j + 1), look, True)}
                        name = str(index_of(t, look))
                    im.alpha_composite(key(lowest, name), (px, py))
            for t in sorted(set(land), key=PRIORITY.index):
                if t == lowest:
                    continue
                m = sum(b for b, tt in zip((1, 2, 4, 8), ts) if tt in PRIORITY and PRIORITY.index(tt) >= PRIORITY.index(t))
                if m == 15:
                    im.alpha_composite(key(t, "0"), (px, py))
                else:
                    v = ruin_row(j) if t == "ruin" else dhash(i + 7, j) % 2
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
