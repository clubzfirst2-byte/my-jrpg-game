"""Terrain RELEASE-quality SAMPLES (wave 1: style approval, not mass production). Rev 2 after the
design inspection (docs/art-candidates/terrain/TERRAIN_PROPOSAL.md, "第 2 版で直したこと").

Draws, at the release size (32x32 per tile, 2 art px per game px), the sample set:
  tile.grass.0-2, tile.path, tile.sand, tile.water.0-1, plains.grass.0-3, face.earth.* (8 segments),
  tile.walltop, obj.tree
into docs/art-candidates/terrain/samples/ (NOT src/: these wait for approval), plus a 4x4 repeat test
per ground tile, a cliff stack test, and a check of the rules (check.txt).

How it is drawn: a flat core tone, then HAND-DRAWN STAMPS (tufts, pebbles, ripples, wave crests...)
at HAND-CHOSEN places; the canvas wraps, so the tiles repeat with no seam. Every mark is a cluster of
2-5 px (no scattered single pixels). Every pixel is fully opaque or fully transparent.
Run: python3 tools/terrain_release/gen_samples.py   (needs Pillow)
"""

import colorsys
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from tile import Tile  # noqa: E402
from ramps import SAMPLE, GUIDE, NEW  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
OUT = os.path.join(ROOT, "docs", "art-candidates", "terrain", "samples")


def tones(mat):
    return {str(k): (mat, k) for k in range(5)}


def rel():
    """Relative stamp keys: '3' lightens by 1, '4' by 2, '1' darkens by 1, '0' by 2 (keeps the material)."""
    return {"4": (2, None), "3": (1, None), "1": (-1, None), "0": (-2, None)}


# ---------------------------------------------------------------------------------------------
# Grass. Blades seen from above: light tips (3/4) up-left, the blade body, a shadow (1) at the root.
# ---------------------------------------------------------------------------------------------
TUFT_L = [
    "..3..4.",
    ".31.3..",
    ".1.31.3",
    "31.1..1",
    "1..1...",
]
TUFT_M = [
    ".3.4.",
    "31.1.",
    "1.31.",
    "..1..",
]
TUFT_S = [
    "3.4",
    "1.1",
]
SPRIG = [
    ".3",
    "31",
    "1.",
]
CLOVER = [
    ".33.",
    "3221",
    ".11.",
]
GRASS_LAYOUT = {
    0: [(3, 4, TUFT_M), (19, 2, TUFT_S), (12, 13, TUFT_L), (26, 15, SPRIG), (4, 22, TUFT_S),
        (21, 25, TUFT_M), (29, 28, TUFT_S), (13, 28, SPRIG)],
    1: [(2, 3, TUFT_L), (17, 6, TUFT_S), (26, 1, SPRIG), (10, 15, TUFT_M), (24, 13, TUFT_L),
        (3, 24, TUFT_M), (16, 25, TUFT_S), (27, 26, SPRIG), (8, 9, CLOVER)],
    2: [(5, 2, TUFT_S), (22, 4, TUFT_M), (13, 11, SPRIG), (2, 15, TUFT_M), (25, 18, TUFT_S),
        (14, 22, TUFT_L), (6, 27, SPRIG), (28, 28, TUFT_S), (20, 13, CLOVER)],
}


def grass_tile(variant, mat="grass", dx=0, dy=0):
    t = Tile(32, 32, SAMPLE, base=(mat, 2))
    for x, y, p in GRASS_LAYOUT[variant]:
        t.stamp(x + dx, y + dy, p, tones(mat))
    return t


FLOWER = [  # 4 petals and a centre, with a shadow on the ground below-right (one per tile at most)
    ".a.",
    "bca",
    ".a1",
]
# plains.grass.N: (grass layout, shift, flower colour, flower position). 0 = the plainest (no flower).
MEADOW = {
    0: (0, (0, 0), None, None),
    1: (1, (0, 0), "flower_w", (20, 20)),
    2: (2, (0, 0), "flower_y", (8, 6)),
    3: (0, (16, 16), "flower_p", (26, 8)),
}


def meadow_tile(variant):
    layout, (dx, dy), petal, pos = MEADOW[variant]
    t = grass_tile(layout, mat="meadow", dx=dx, dy=dy)
    if petal:
        t.stamp(pos[0], pos[1], FLOWER, {"a": (petal, 3), "b": (petal, 4), "c": ("flower_y", 2), "1": ("meadow", 1)})
    return t


# --- path (dirt) --------------------------------------------------------------------------------
# Low-contrast on purpose: tile.path is ONE tile, so anything bright would show the 32 px grid.
PEBBLE = [  # a 3 px stone, lit top-left, with its shadow on the dirt (guide 3.6: 1-2 pebbles of 2-3 px)
    "32.",
    "2d.",
]
PEBBLE_2 = [
    "3.",
    "2d",
]
DENT = [  # a shallow hollow: dark upper-left lip, light lower-right lip
    ".11..",
    "1...3",
    ".333.",
]
DUST = ["333"]


def path_tile():
    t = Tile(32, 32, SAMPLE, base=("dirt", 2))
    for x, y, p in [(4, 5, DENT), (21, 10, DENT), (10, 23, DENT)]:
        t.stamp(x, y, p, tones("dirt"))
    for x, y in [(14, 3), (1, 15), (24, 21)]:
        t.stamp(x, y, DUST, tones("dirt"))
    peb = {"4": ("pebble", 4), "3": ("pebble", 3), "2": ("pebble", 2), "1": ("pebble", 1), "d": ("dirt", 1)}
    t.stamp(15, 14, PEBBLE, peb)
    t.stamp(28, 27, PEBBLE_2, peb)
    return t


# --- sand ---------------------------------------------------------------------------------------
RIPPLE = [  # a wind ripple: lit crest, shade on the lee side
    "..3333...",
    ".3....11.",
    "1.......1",
]
RIPPLE_S = [
    ".333.",
    "3...1",
]
SHELL = [
    ".ab",
    "abb",
    ".s.",
]


def sand_tile():
    t = Tile(32, 32, SAMPLE, base=("sand", 2))
    for x, y, p in [(2, 5, RIPPLE), (18, 13, RIPPLE), (6, 22, RIPPLE_S), (24, 26, RIPPLE_S), (25, 2, RIPPLE_S)]:
        t.stamp(x, y, p, tones("sand"))
    t.stamp(12, 9, SHELL, {"a": ("shell", 3), "b": ("shell", 2), "s": ("sand", 1)})
    return t


# --- water (2 frames, swapped every 0.6 s in the game) --------------------------------------------
# Only the short sparkle lines move (2 px right): the frames differ by about 20 px (guide 3.5: 12-30).
SWELLS = [(1, 9, [0, 0, 1, 1, 1, 1, 0, 0]), (16, 11, [0, 1, 1, 1, 0]), (6, 26, [0, 0, 1, 1, 1, 0, 0]),
          (21, 23, [0, 1, 1, 1, 1, 0]), (27, 3, [0, 1, 1, 0])]  # deeper strokes (tone 1)
CRESTS = [(3, 3), (19, 16)]  # static wave crests (a light smile over a trough)
CREST = [
    "3....3",
    ".3333.",
    "..11..",
]
SPARKLES = [(10, 19, "334"), (25, 13, "334"), (13, 29, "334"), (28, 25, "34")]


def water_tile(frame):
    t = Tile(32, 32, SAMPLE, base=("water", 2))
    for x0, y0, dys in SWELLS:
        for k, d in enumerate(dys):
            t.put(x0 + k, y0 + d, "water", 1)
    for x, y in CRESTS:
        t.stamp(x, y, CREST, tones("water"))
    for x, y, s in SPARKLES:
        t.stamp(x + 2 * frame, y, [s], tones("water"))
    return t


# --- earth cliff faces ----------------------------------------------------------------------------
# The game stacks faces from segments (gameView.addFace): 1 level = top.8 + mid-base.8, 2 levels =
# top.8 + mid.8 + mid.8 + mid-base.8, short faces use top-base. Shading from top to bottom 3 -> 2 -> 1:
#   top:  grass lip, its shadow (1), then a lit band (3) that steps down to 2 along a ragged line;
#   mid:  core 2;
#   base: core 2 stepping down to 1 along a ragged line, the last row 0 (where it meets the ground).
# Details (strata ledge, clods, erosion) are RELATIVE (+1 / -1 on what is there), so they follow the steps.
LIP_DEPTH = [3, 4, 4, 3, 5, 4, 3, 3, 4, 5, 5, 4, 3, 4, 4, 3, 3, 5, 4, 4, 3, 3, 4, 5, 5, 4, 3, 4, 3, 3, 4, 4]
HANG = {4: 2, 9: 1, 17: 1, 24: 2, 30: 1}  # blades hanging lower
LIT_DEPTH = [3, 3, 4, 4, 4, 3, 3, 2, 3, 3, 4, 4, 3, 3, 3, 4, 4, 4, 3, 2, 2, 3, 3, 4, 4, 3, 3, 3, 4, 4, 3, 3]
DARK_FROM = [9, 9, 8, 8, 9, 10, 10, 9, 9, 8, 8, 8, 9, 10, 10, 10, 9, 9, 8, 9, 9, 10, 10, 9, 8, 8, 9, 9, 10, 10, 9, 9]
LEDGE_DY = [0, 0, 0, 1, 1, 1, 1, 0, 0, -1, -1, 0, 0, 0, 0, 1, 1, 0, 0, 0, -1, -1, -1, 0, 0, 0, 1, 1, 1, 0, 0, 0]
LEDGE_GAPS = {6, 7, 18, 27}
CLOD = [
    ".333..",
    "3....1",
    "3...1.",
    ".111..",
]
CLOD_S = [
    ".33.",
    "3..1",
    ".11.",
]
STONE = [
    "0330",
    "3221",
    "0110",
]
# (x, y, stamp) per segment kind and height: placed differently in every segment so a stack does not
# show the same clod above itself.
CLODS = {
    ("top", 16): [(1, 9, CLOD_S), (18, 8, CLOD), (27, 12, CLOD_S)],
    ("top-base", 16): [(1, 9, CLOD_S), (18, 8, CLOD)],
    ("mid", 16): [(6, 1, CLOD_S), (21, 3, CLOD), (0, 12, CLOD), (14, 12, CLOD_S)],
    ("mid-base", 16): [(9, 1, CLOD), (25, 2, CLOD_S), (3, 12, CLOD_S)],
    ("top", 8): [(22, 5, CLOD_S)],
    ("top-base", 8): [],
    ("mid", 8): [(11, 1, CLOD_S), (26, 3, CLOD_S)],
    ("mid-base", 8): [(16, 1, CLOD_S)],
}
STONE_AT = {("mid", 16): (28, 4), ("mid-base", 16): (17, 5)}


def face_tile(kind, seg):
    h = 16 if seg == 8 else 8
    t = Tile(32, h, SAMPLE, base=None, wrap_y=False)
    is_top, is_base = kind.startswith("top"), kind.endswith("base")
    short = h == 8
    # 1. core tone per pixel: the 3 -> 2 -> 1 steps
    lip_d = [max(2, d - 1) for d in LIP_DEPTH] if short else LIP_DEPTH
    for x in range(32):
        for y in range(h):
            tone = 2
            if is_top:
                start = lip_d[x] + HANG.get(x, 0) + 1
                lit = LIT_DEPTH[x] - (1 if short else 0)
                if y < start + lit:
                    tone = 3
            if is_base:
                dark_from = DARK_FROM[x] if not short else DARK_FROM[x] // 2 + 1
                if is_top and short:
                    dark_from = max(dark_from, 6)
                if y >= dark_from:
                    tone = 1
                if y == h - 1:
                    tone = 0
            t.put(x, y, "earth", tone)
    # 2. relative details: strata ledge (not in the top band), clods, erosion streaks
    r = rel()
    if not (is_top and short):
        ledge = 11 if h == 16 else 4
        if is_top and h == 16:
            ledge = 12
        for x in range(32):
            if x in LEDGE_GAPS:
                continue
            y = ledge + LEDGE_DY[x]
            if y + 1 < h - (1 if is_base else 0):
                t.shift(x, y, +1, lo=1, hi=3)
                t.shift(x, y + 1, -1, lo=1, hi=3)
    for x, y, p in CLODS[(kind, h)]:
        t.stamp(x, y, p, r)
    for x, y0, n in [(4, 1, 3), (13, 2, 4), (28, 1, 3)]:
        if is_top or y0 + n >= h - 1:
            continue
        t.shift(x, y0, +1, hi=3)
        for k in range(1, n):
            t.shift(x, y0 + k, -1, lo=1)
    if (kind, h) in STONE_AT:
        sx, sy = STONE_AT[(kind, h)]
        t.stamp(sx, sy, STONE, tones("pebble"))
    # 3. the grass lip on top (the part that changes in autumn / winter) and its shadow
    if is_top:
        for x in range(32):
            d = lip_d[x]
            for y in range(d):
                t.put(x, y, "grass", 3 if y == 0 else 2 if y < d - 1 else 1)
            for k in range(HANG.get(x, 0)):
                t.put(x, d + k, "grass", 1)
            t.put(x, d + HANG.get(x, 0), "earth", 1)  # shadow under the overhang; the lit rim (3) follows
    return t


# --- house wall top: capstones (wall.stone) ---------------------------------------------------------
# Rows of 8 px; block widths differ per row (hand-chosen) and wrap, so joints do not line up.
WALL_ROWS = [[10, 12, 10], [7, 13, 12], [12, 9, 11], [9, 11, 12]]
WALL_START = [0, 4, 9, 2]
CHIPS = [(5, 3), (19, 11), (27, 19), (11, 27)]  # small worn spots (2 px clusters)


def walltop_tile():
    t = Tile(32, 32, SAMPLE, base=("stone", 2))
    for row, widths in enumerate(WALL_ROWS):
        y0 = row * 8
        x = WALL_START[row]
        for wdt in widths:
            for k in range(wdt):
                t.put(x + k, y0, "stone", 3)  # lit top edge
                t.put(x + k, y0 + 6, "stone", 1)  # shaded lower edge
                t.put(x + k, y0 + 7, "stone", 0)  # mortar gap
            for y in range(y0, y0 + 7):
                t.put(x, y, "stone", 0)  # joint
                t.put(x + 1, y, "stone", 3 if y < y0 + 6 else 1)  # lit left edge of the next block
            x += wdt
    for x, y in CHIPS:
        t.put(x, y, "stone", 1)
        t.put(x + 1, y, "stone", 1)
        t.put(x + 1, y + 1, "stone", 3)
    return t


# --- tree (scale reference) ------------------------------------------------------------------------
# Canopy = hand-placed leaf clumps (cx, cy, r), back to front. Each clump is lit from the top left;
# its lower-right rim gets a shadow line, so the clumps read as separate masses. No drawn ground
# shadow: the game draws shadows itself.
CLUMPS = [
    (9, 22, 7.5), (23, 22, 7.5), (16, 25, 8), (6, 15, 6), (26, 14, 6), (16, 9, 8), (11, 16, 7), (21, 16, 7.5), (16, 18, 6.5),
]
LEAF_MARKS = [  # (x, y, tone): small leaf shapes painted on the lit sides (2 px each)
    (10, 7, 4), (13, 5, 4), (5, 12, 4), (8, 11, 3), (19, 6, 3), (14, 12, 4), (6, 18, 3), (17, 14, 3),
    (24, 11, 3), (22, 18, 1), (9, 20, 3), (27, 19, 1), (13, 22, 1), (20, 24, 1), (4, 21, 3), (25, 24, 1),
    (6, 25, 2), (14, 28, 2), (22, 27, 2), (18, 31, 2), (10, 29, 2), (27, 24, 2),  # leaves in the shaded lower half
]


def tree_sprite():
    w, h = 32, 56
    t = Tile(w, h, SAMPLE, base=None, wrap_x=False, wrap_y=False)
    for y in range(30, 54):
        for x in range(13, 19):
            t.put(x, y, "bark", 3 if x == 14 else 1 if x >= 17 else 2)
    for x, y0, n in [(15, 37, 3), (16, 43, 2), (14, 48, 2), (17, 40, 2)]:  # bark furrows
        for y in range(y0, y0 + n):
            t.put(x, y, "bark", 1)
    for x, y, tn in [(12, 52, 2), (12, 53, 3), (11, 53, 2), (19, 52, 1), (20, 53, 1), (19, 53, 1)]:  # roots
        t.put(x, y, "bark", tn)
    owner = {}
    for i, (cx, cy, r) in enumerate(CLUMPS):
        for y in range(int(cy - r) - 1, int(cy + r) + 2):
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                dx, dy = (x + 0.5 - cx) / r, (y + 0.5 - cy) / r
                d = dx * dx + dy * dy
                if d > 1 or not (0 <= x < w and 0 <= y < h):
                    continue
                lit = -(dx * 0.75 + dy)
                base_tone = 2 if i >= 6 else 1 if cy > 20 else 2
                tone = base_tone + (1 if lit > 0.35 else 0) + (1 if lit > 0.9 and d > 0.45 else 0) - (1 if lit < -0.55 else 0)
                if d > 0.72 and dx + dy > 0.35:
                    tone = 1
                t.put(x, y, "leaf", max(1, min(4, tone)))
                owner[(x, y)] = i
    for x, y, tn in LEAF_MARKS:
        if (x, y) in owner:
            t.put(x, y, "leaf", tn)
            if (x + 1, y) in owner:
                t.put(x + 1, y, "leaf", max(1, tn - 1))
    for x in range(13, 19):  # the canopy's shadow on the trunk
        for y in range(30, 35):
            if (x, y) not in owner:
                t.put(x, y, "bark", 1)
    # selective outline: the darkest tone of the neighbour's material (bottom row = the trunk's base)
    add = []
    for y in range(h):
        for x in range(w):
            if t.px[y][x] is not None:
                continue
            for ddx, ddy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                v = t.get(x + ddx, y + ddy)
                if v is not None:
                    add.append((x, y, v[0]))
                    break
    for x, y, mat in add:
        t.put(x, y, mat, 0)
    for x in range(10, 22):
        if t.px[54][x] is not None or t.px[53][x] is not None:
            t.put(x, 55, "bark", 0)
    return t


# ---------------------------------------------------------------------------------------------
def build():
    """name -> PIL image, the sample set."""
    out = {}
    for v in range(3):
        out[f"tile.grass.{v}"] = grass_tile(v).image()
    out["tile.path"] = path_tile().image()
    out["tile.sand"] = sand_tile().image()
    out["tile.water.0"] = water_tile(0).image()
    out["tile.water.1"] = water_tile(1).image()
    for v in range(4):
        out[f"plains.grass.{v}"] = meadow_tile(v).image()
    for seg in (4, 8):
        for kind in ("top", "mid", "mid-base", "top-base"):
            out[f"face.earth.{kind}.{seg}"] = face_tile(kind, seg).image()
    out["tile.walltop"] = walltop_tile().image()
    out["obj.tree"] = tree_sprite().image()
    return out


GROUND = ["tile.grass.0", "tile.grass.1", "tile.grass.2", "tile.path", "tile.sand", "tile.water.0", "tile.water.1",
          "plains.grass.0", "plains.grass.1", "plains.grass.2", "plains.grass.3", "tile.walltop"]

CLOAK = "#6a9048"


def lightness(c):
    r, g, b = (int(c[i:i + 2], 16) for i in (1, 3, 5))
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255 * 100


def hue(c):
    r, g, b = (int(c[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return colorsys.rgb_to_hsv(r, g, b)[0] * 360


def checks(tiles):
    """Measured rule checks, written to samples/check.txt."""
    lines = ["# 自動の確認（gen_samples.py が毎回書く）", ""]
    def px(im):
        return [im.getpixel((x, y)) for y in range(im.height) for x in range(im.width)]

    bad_alpha = {n: sum(1 for p in px(im) if p[3] not in (0, 255)) for n, im in tiles.items()}
    lines.append("半透明の点（0 であること）: " + ", ".join(f"{n}={v}" for n, v in bad_alpha.items() if v) or "なし")
    if not any(bad_alpha.values()):
        lines[-1] = "半透明の点（0 であること）: 全部 0"
    d = sum(1 for a, b in zip(px(tiles["tile.water.0"]), px(tiles["tile.water.1"])) if a != b)
    lines.append(f"水の 2 コマの違い: {d} ドット（ガイド 3.5：12〜30）")
    lines.append("")
    lines.append(f"地面の 2 番とマントの 2 番 {CLOAK}（明るさ {lightness(CLOAK):.0f}・色合い {hue(CLOAK):.0f}°）")
    rows = [("島の草 tile.grass / 平原 plains.grass", SAMPLE["grass"][2]), ("道 tile.path", SAMPLE["dirt"][2]),
            ("砂 tile.sand", SAMPLE["sand"][2]), ("水 tile.water", SAMPLE["water"][2]), ("崖 face.earth", SAMPLE["earth"][2]),
            ("壁の上 tile.walltop", SAMPLE["stone"][2]), ("森の苔 forest.moss", GUIDE["forest.moss"][2]),
            ("岸の草 lake.grass", GUIDE["lake.grass"][2]), ("葦 lake.reed", NEW["lake.reed"][2]),
            ("赤い砂 desert.sand", GUIDE["desert.sand"][2]), ("雪 mount.snow", GUIDE["mount.snow"][2]),
            ("岩 mount.rock", GUIDE["mount.rock"][2]), ("遺跡の石 ruin.stone", GUIDE["ruin.stone"][2])]
    lines.append("")
    lines.append("見本の PNG で実際にいちばん多い色（＝2 番の面）を数えたもの:")
    for n in ["tile.grass.0", "tile.grass.1", "tile.grass.2", "plains.grass.0", "plains.grass.3", "tile.path", "tile.sand",
              "tile.water.0", "face.earth.mid.8", "tile.walltop"]:
        cnt, rgb = max(tiles[n].getcolors(4096))
        c = "#%02x%02x%02x" % rgb[:3]
        share = 100 * cnt / (tiles[n].width * tiles[n].height)
        lines.append(f"  {n:<20} {c}（面積 {share:3.0f}%）  明るさ {lightness(c):5.1f}（差 {lightness(CLOAK) - lightness(c):+5.1f}）  色合い {hue(c):4.0f}°")
    lines.append("")
    lines.append("ランプの 2 番（ほかの地方の提案）:")
    for name, c in rows:
        lines.append(f"  {name:<34} {c}  明るさ {lightness(c):5.1f}（差 {lightness(CLOAK) - lightness(c):+5.1f}）  色合い {hue(c):5.0f}°")
    return "\n".join(lines) + "\n"


def main():
    from PIL import Image

    os.makedirs(OUT, exist_ok=True)
    tiles = build()
    for name, im in tiles.items():
        im.save(os.path.join(OUT, f"{name}.png"))
    rep_dir = os.path.join(OUT, "repeat")
    os.makedirs(rep_dir, exist_ok=True)
    for name in GROUND:  # 4x4 repeat tests (shown at 2x so a seam would be easy to see)
        im = tiles[name]
        rep = Image.new("RGBA", (128, 128))
        for j in range(4):
            for i in range(4):
                rep.paste(im, (i * 32, j * 32))
        rep.resize((256, 256), Image.NEAREST).save(os.path.join(rep_dir, f"repeat_{name}.png"))
    from mock_scene import tile_hash  # the variants mixed the way the game picks them

    for prefix, n in (("tile.grass", 3), ("plains.grass", 4)):
        mix = Image.new("RGBA", (256, 256))
        for j in range(8):
            for i in range(8):
                mix.paste(tiles[f"{prefix}.{tile_hash(i, j) % n}"], (i * 32, j * 32))
        mix.resize((512, 512), Image.NEAREST).save(os.path.join(rep_dir, f"repeat_{prefix}.mixed.png"))
    # cliff stack test: grass on top, faces stacked as gameView.addFace does
    stacks = [["top-base.4"], ["top-base.8"], ["top.8", "mid-base.8"], ["top.8", "mid.8", "mid.8", "mid-base.8"],
              ["top.8", "mid.8", "mid-base.4"]]
    cw = 4 * 32 + 16
    st = Image.new("RGBA", (len(stacks) * cw + 16, 32 + 64 + 40), (34, 36, 46, 255))
    for i, segs in enumerate(stacks):
        x0 = 16 + i * cw
        for k in range(4):
            st.paste(tiles[f"tile.grass.{k % 3}"], (x0 + k * 32, 8))
            y = 40
            for sname in segs:
                im = tiles[f"face.earth.{sname}"]
                st.alpha_composite(im, (x0 + k * 32, y))
                y += im.height
            st.paste(tiles["tile.path"].crop((0, 0, 32, min(24, st.height - y))), (x0 + k * 32, y))
    st.resize((st.width * 2, st.height * 2), Image.NEAREST).save(os.path.join(rep_dir, "stack_face.earth.png"))
    report = checks(tiles)
    with open(os.path.join(OUT, "check.txt"), "w", encoding="utf-8") as f:
        f.write(report)
    print(report)
    print("wrote", len(tiles), "samples to", os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main()
