"""Reference renderer for ground v2 (what the engine should do; used for the review images).

Input: a grid of ground classes, one character per map cell:
  g island grass, p plains grass, l lake grass, m forest moss, n mountain snow, s island sand,
  d desert sand, = path, u ruin floor, ~ water; anything else is drawn with its v1 tile on the cell grid.
Steps (NAMES.md has the same in words):
  1. water cells are DEEP when no land cell is within 2 cells (Chebyshev), else SHALLOW
  2. the display grid is shifted half a tile: display tile (i, j) has corners on the cells
     (i, j) NW, (i+1, j) NE, (i, j+1) SW, (i+1, j+1) SE and is drawn at ((i + .5) * 32, (j + .5) * 32)
  3. per display tile: the lowest terrain among its corners as a full tile (water: shallow, or deep if all
     4 corners are deep; land: a variant or a macro piece), then
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
    H, W = len(grid), len(grid[0])
    land = {(x, y) for y in range(H) for x in range(W) if grid[y][x] != "~"}
    deep = set()
    for y in range(H):
        for x in range(W):
            if grid[y][x] == "~" and not any((x + dx, y + dy) in land for dx in range(-2, 3) for dy in range(-2, 3)):
                deep.add((x, y))
    return deep


def terr(grid, x, y):
    H, W = len(grid), len(grid[0])
    x, y = max(0, min(W - 1, x)), max(0, min(H - 1, y))
    return CLASS.get(grid[y][x], "other")


def macro_blocks(grid, season_prefix=""):
    """2x2 display blocks (even i, j) with all 9 corner cells of one land terrain: a hash picks 1 in 3."""
    H, W = len(grid), len(grid[0])
    out = {}
    for j in range(0, H - 2, 2):
        for i in range(0, W - 2, 2):
            ts = {terr(grid, i + dx, j + dy) for dx in range(3) for dy in range(3)}
            if len(ts) == 1 and next(iter(ts)) not in ("water", "other") and dhash(i, j) % 3 == 0:
                for k, (di, dj) in enumerate(((0, 0), (1, 0), (0, 1), (1, 1))):
                    out[(i + di, j + dj)] = f"m{k}"
    return out


def render_v2(grid, images, frame=0, season=None):
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
                    name = macro.get((i, j)) if len(set(ts)) == 1 else None
                    if name is None:
                        h = dhash(i, j) % 8
                        name = str(0 if h < 4 else h - 4)  # variant 0 on half, 1-3 on 1/8 each (see NAMES.md)
                    im.alpha_composite(key(lowest, name), (px, py))
            for t in sorted(set(land), key=PRIORITY.index):
                if t == lowest:
                    continue
                m = sum(b for b, tt in zip((1, 2, 4, 8), ts) if tt in PRIORITY and PRIORITY.index(tt) >= PRIORITY.index(t))
                if m == 15:
                    im.alpha_composite(key(t, "0"), (px, py))
                else:
                    im.alpha_composite(key(t, f"e{m}.{dhash(i + 7, j) % 2}"), (px, py))
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
