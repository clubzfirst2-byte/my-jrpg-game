"""Terrain RELEASE-quality SAMPLES (wave 1: style approval, not mass production).

Draws, at the release size (32x32 per tile, 2 art px per game px), the sample set:
  tile.grass.0-2, tile.path, tile.sand, tile.water.0-1, plains.grass.0, face.earth.* (8 segments),
  tile.walltop, obj.tree
into docs/art-candidates/terrain/samples/ (NOT src/: these wait for approval), plus a 4x4 repeat test
per ground tile, a cliff stack test and an overview sheet.

How it is drawn: a flat core tone, then HAND-DRAWN STAMPS (tufts, pebbles, ripples, wave crests...)
at HAND-CHOSEN places; the canvas wraps, so the tiles repeat with no seam. See tile.py / ramps.py.
Run: python3 tools/terrain_release/gen_samples.py   (needs Pillow)
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from tile import Tile  # noqa: E402
from ramps import SAMPLE  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
OUT = os.path.join(ROOT, "docs", "art-candidates", "terrain", "samples")

# ---------------------------------------------------------------------------------------------
# Stamps. Digits are tones of the stamp's material; letters are named below per stamp set.
# ---------------------------------------------------------------------------------------------

# Grass blades seen from above: light tips (3/4) up-left, the blade body, a shadow (1) at the root.
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
SPRIG = [  # two blades
    ".3",
    "31",
    "1.",
]
CLOVER = [  # a low round leaf cluster
    ".33.",
    "3221",
    ".11.",
]
SPECK_L = ["3"]
SPECK_D = ["1"]


def g(pattern):
    return pattern, {str(t): ("grass", t) for t in range(5)}


def grass_tile(variant, mat="grass"):
    t = Tile(32, 32, SAMPLE, base=(mat, 2))
    m = {str(k): (mat, k) for k in range(5)}
    # Soft darker ground between the blades: a few hand-placed low patches (tone 1 rims only on
    # their lower-right, so they read as hollows lit from the top left).
    layout = {
        0: [(3, 4, TUFT_M), (19, 2, TUFT_S), (12, 13, TUFT_L), (26, 15, SPRIG), (4, 22, TUFT_S),
            (21, 25, TUFT_M), (29, 28, TUFT_S), (13, 28, SPRIG)],
        1: [(2, 3, TUFT_L), (17, 6, TUFT_S), (26, 1, SPRIG), (10, 15, TUFT_M), (24, 13, TUFT_L),
            (3, 24, TUFT_M), (16, 25, TUFT_S), (27, 26, SPRIG), (8, 9, CLOVER)],
        2: [(5, 2, TUFT_S), (22, 4, TUFT_M), (13, 11, SPRIG), (2, 15, TUFT_M), (25, 18, TUFT_S),
            (14, 22, TUFT_L), (6, 27, SPRIG), (28, 28, TUFT_S), (20, 13, CLOVER)],
    }[variant]
    specks = {
        0: [(9, 2, 3), (24, 8, 1), (7, 13, 3), (30, 20, 1), (17, 19, 3), (2, 30, 1), (24, 31, 3)],
        1: [(12, 1, 1), (21, 10, 3), (5, 12, 3), (30, 8, 1), (20, 20, 3), (10, 30, 1), (30, 22, 3)],
        2: [(1, 6, 3), (17, 1, 1), (29, 10, 3), (9, 19, 1), (21, 28, 3), (31, 25, 1), (11, 31, 3)],
    }[variant]
    for x, y, tn in specks:
        t.put(x, y, mat, tn)
    for x, y, p in layout:
        t.stamp(x, y, p, m)
    return t


FLOWER = [  # 4 petals and a centre, with a shadow pixel on the ground below-right
    ".a.",
    "aca",
    ".a1",
]


def meadow_tile(variant=0):
    t = grass_tile(variant, mat="meadow")
    for x, y, petal in [(8, 20, "flower_w"), (23, 7, "flower_y"), (27, 22, "flower_w"), (4, 6, "flower_p")]:
        t.stamp(x, y, FLOWER, {"a": (petal, 3), "c": ("flower_y", 2), "1": ("meadow", 1)})
        t.put(x, y + 1, petal, 4)  # top-left petal catches the light
    return t


# --- path (dirt) --------------------------------------------------------------------------------
PEBBLE = [
    ".33.",
    "3421",
    ".21d",
    "..dd",
]
PEBBLE_S = [
    "43",
    "2d",
]
DENT = [  # a small hollow: dark upper-left lip, light lower-right lip
    ".11.",
    "1223",
    ".33.",
]
DUST = ["33.3"]


def path_tile():
    t = Tile(32, 32, SAMPLE, base=("dirt", 2))
    peb = {"4": ("pebble", 4), "3": ("pebble", 3), "2": ("pebble", 2), "1": ("pebble", 1), "d": ("dirt", 1)}
    dirt = {str(k): ("dirt", k) for k in range(5)}
    for x, y, p in [(5, 4, DENT), (22, 9, DENT), (11, 23, DENT), (27, 26, DENT)]:
        t.stamp(x, y, p, dirt)
    for x, y, p in [(14, 3, DUST), (2, 15, DUST), (19, 18, DUST), (25, 1, ["3"]), (6, 29, DUST)]:
        t.stamp(x, y, p, dirt)
    for x, y, tn in [(9, 10, 1), (29, 14, 1), (17, 28, 1), (1, 21, 3), (30, 5, 3), (13, 15, 3)]:
        t.put(x, y, "dirt", tn)
    for x, y, p in [(16, 12, PEBBLE), (3, 9, PEBBLE_S), (26, 19, PEBBLE_S), (8, 26, PEBBLE_S), (20, 30, PEBBLE_S)]:
        t.stamp(x, y, p, peb)
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
    s = {str(k): ("sand", k) for k in range(5)}
    for x, y, p in [(2, 5, RIPPLE), (18, 13, RIPPLE), (6, 22, RIPPLE_S), (24, 26, RIPPLE_S), (25, 2, RIPPLE_S)]:
        t.stamp(x, y, p, s)
    for x, y, tn in [(13, 2, 1), (29, 9, 3), (4, 14, 3), (12, 17, 1), (30, 19, 1), (16, 27, 3), (2, 30, 1), (21, 8, 3)]:
        t.put(x, y, "sand", tn)
    t.stamp(12, 9, SHELL, {"a": ("shell", 3), "b": ("shell", 2), "s": ("sand", 1)})
    t.stamp(28, 22, PEBBLE_S, {"4": ("pebble", 4), "3": ("pebble", 3), "2": ("pebble", 2), "d": ("sand", 1)})
    return t


# --- water (2 frames, swapped every 0.6 s in the game) --------------------------------------------
CREST = [  # a wave crest seen from above: a bright smile, with the trough under it
    "3.....3",
    ".34443.",
    "..111..",
]
CREST_S = [
    "3...3",
    ".343.",
    "..1..",
]
GLINT = ["4"]


def water_tile(frame):
    t = Tile(32, 32, SAMPLE, base=("water", 2))
    w = {str(k): ("water", k) for k in range(5)}
    # Deeper swells: SHORT gentle strokes (tone 1), staggered so no stripe runs across the map, the same
    # in both frames so the water does not flicker.
    for x0, y0, n in [(1, 9, 9), (16, 11, 7), (27, 7, 5), (6, 26, 8), (20, 24, 9), (12, 17, 4), (29, 17, 4)]:
        for k in range(n):
            y = y0 + round(0.8 * math.sin(k * math.pi / max(1, n - 1)))
            t.put(x0 + k, y, "water", 1)
    # Crests drift 2 px right and bob 1 px between frames.
    d = 2 * frame
    for x, y, p in [(3, 3, CREST), (19, 15, CREST), (9 , 20, CREST_S), (25, 28, CREST_S), (24, 5, CREST_S)]:
        t.stamp(x + d, y + (frame if p is CREST else -frame), p, w)
    glints = [(14, 7), (2, 13), (29, 21), (16, 30)] if frame == 0 else [(15, 9), (5, 12), (28, 19), (13, 29)]
    for x, y in glints:
        t.put(x, y, "water", 4)
    return t


# --- earth cliff faces ----------------------------------------------------------------------------
# The game stacks faces from segments (gameView.addFace): top(.8|.4) + mid.8 ... + mid-base, or top-base
# for a short face. 1 level (段) = 16 game px = 32 art px = top.8 + mid-base.8.
# Shading by height: the lip's shadow at the top, strata ledges in the middle, the darkest foot at the base.
LIP_DEPTH = [3, 4, 4, 3, 5, 4, 3, 3, 4, 6, 5, 4, 3, 4, 4, 3, 3, 5, 4, 4, 3, 3, 4, 5, 6, 4, 3, 4, 3, 3, 5, 4]
STONE = [
    "0330",
    "3221",
    "0110",
]


# The strata ledge wanders by a pixel (hand-written offsets per column), so it reads as earth, not bricks.
LEDGE_DY = [0, 0, 0, 1, 1, 1, 1, 0, 0, -1, -1, 0, 0, 0, 0, 1, 1, 0, 0, 0, -1, -1, -1, 0, 0, 0, 1, 1, 1, 0, 0, 0]
LEDGE_GAPS = {6, 7, 18, 27}


CLOD = [
    ".333..",
    "32222.",
    "322221",
    ".1111.",
]
CLOD_S = [
    ".33.",
    "3221",
    ".11.",
]


def face_body(t, y0, h, seed_x):
    """Earth: soft vertical erosion streaks, one wandering strata ledge, one embedded stone."""
    for y in range(y0, y0 + h):
        for x in range(32):
            t.put(x, y, "earth", 2)
    ledge = y0 + (10 if h >= 16 else 4)
    # erosion streaks: a light pixel on top, a short dark run below (rain wash), stopping at the ledge
    for gx, gy, gl in [(4, 1, 4), (13, 3, 5), (22, 0, 3), (28, 2, 4), (9, 13, 2), (25, 13, 2)]:
        x = gx + seed_x
        if y0 + gy >= y0 + h:
            continue
        t.put(x, y0 + gy, "earth", 3)
        for k in range(1, gl):
            yy = y0 + gy + k
            if yy >= y0 + h or yy == ledge + LEDGE_DY[x % 32]:
                break
            t.put(x, yy, "earth", 1)
    for x in range(32):
        if (x + seed_x) % 32 in LEDGE_GAPS:
            continue
        y = ledge + LEDGE_DY[(x + seed_x) % 32]
        t.put(x, y, "earth", 3)
        t.put(x, y + 1, "earth", 1)
    # clods: lumps of earth lit on their top-left, hand-placed differently in the top and mid segments
    clods = {0: [(1, 3, CLOD), (19, 5, CLOD_S), (11, 12, CLOD_S), (25, 12, CLOD)],
             3: [(6, 2, CLOD_S), (21, 4, CLOD), (0, 12, CLOD), (14, 12, CLOD_S)]}[seed_x]
    for x, y, p in clods:
        if y + len(p) <= h:
            t.stamp(x, y0 + y, p, {str(k): ("earth", k) for k in range(5)})
    if h >= 16 and seed_x == 3:
        t.stamp(28, y0 + 3, STONE, {str(k): ("pebble", k) for k in range(5)})
    # light grains on the lit (upper-left) faces of the clods
    for x, y in [(2, 3), (11, 6), (20, 2), (30, 5), (7, 13), (16, 14), (26, 12)]:
        if y < h and y0 + y != ledge:
            t.put(x + seed_x, y0 + y, "earth", 3)


def lip(t, short):
    """The grass lip hanging over the face (this part changes in autumn / winter)."""
    depth = [max(2, d - 1) for d in LIP_DEPTH] if short else LIP_DEPTH
    for x in range(32):
        dd = depth[x]
        for y in range(dd):
            tone = 3 if y == 0 else 2 if y < dd - 2 else 1
            t.put(x, y, "grass", tone)
        t.put(x, dd, "earth", 0)  # the lip's shadow line on the earth
        t.put(x, dd + 1, "earth", 1)
    # a few blades hanging lower, with a light tip at the top
    for x, extra in [(4, 2), (9, 2), (17, 1), (24, 2), (30, 1)]:
        dd = depth[x]
        for k in range(extra):
            t.put(x, dd + k, "grass", 1)
        t.put(x, dd + extra, "earth", 0)


def base(t):
    """The foot of the cliff, where it meets the ground: darkest rows."""
    h = t.h
    for x in range(32):
        t.put(x, h - 1, "earth", 0)
        t.shift(x, h - 2, -1, lo=1)
        if (x * 7) % 5 < 2:
            t.shift(x, h - 3, -1, lo=1)


def face_tile(kind, seg):
    h = 16 if seg == 8 else 8
    t = Tile(32, h, SAMPLE, base=None, wrap_y=False)
    face_body(t, 0, h, seed_x={"top": 0, "mid": 3, "mid-base": 3, "top-base": 0}[kind])
    if kind.startswith("top"):
        lip(t, short=(seg == 4))
    if kind.endswith("base"):
        base(t)
    return t


# --- house wall top -------------------------------------------------------------------------------
def walltop_tile():
    t = Tile(32, 32, SAMPLE, base=("wood", 2))
    joints = [(9, 25), (2, 19), (14, 29), (6, 22)]  # per plank: where boards meet (staggered)
    for p in range(4):
        y0 = p * 8
        t.hline(0, 31, y0, "wood", 3)  # lit top edge of the plank
        t.hline(0, 31, y0 + 6, "wood", 1)
        t.hline(0, 31, y0 + 7, "wood", 0)  # the gap between planks
        # grain (hand-placed strokes)
        for gx, gy, gl in [(3, 2, 5), (15, 4, 7), (22, 2, 4), (27, 4, 3)]:
            x = (gx + p * 7) % 32
            t.hline(x, x + gl, y0 + gy, "wood", 1)
            t.put(x - 1, y0 + gy, "wood", 3)
        for jx in joints[p]:
            for y in range(y0, y0 + 7):
                t.put(jx, y, "wood", 0)
                t.put(jx + 1, y, "wood", 2 if y > y0 else 3)
            t.put(jx - 2, y0 + 2, "pebble", 4)  # nail heads
            t.put(jx - 2, y0 + 4, "pebble", 1)
            t.put(jx + 3, y0 + 2, "pebble", 4)
            t.put(jx + 3, y0 + 4, "pebble", 1)
    return t


# --- tree (scale reference) ------------------------------------------------------------------------
# Canopy = hand-placed leaf clumps (cx, cy, r), back to front. Each clump is lit from the top left;
# its lower-right rim gets a shadow line, so the clumps read as separate masses.
CLUMPS = [
    (9, 22, 7.5), (23, 22, 7.5), (16, 25, 8), (6, 15, 6), (26, 14, 6), (16, 9, 8), (11, 16, 7), (21, 16, 7.5), (16, 18, 6.5),
]
LEAF_MARKS = [  # (x, y, tone): leaf shapes painted on the lit sides
    (10, 7, 4), (13, 5, 4), (11, 6, 3), (5, 12, 4), (8, 11, 3), (19, 6, 3), (14, 12, 4), (6, 18, 3), (17, 14, 3),
    (24, 11, 3), (22, 18, 1), (9, 20, 3), (27, 19, 1), (13, 22, 1), (20, 24, 1), (4, 21, 3), (25, 24, 1),
]


def tree_sprite():
    w, h = 32, 56
    t = Tile(w, h, SAMPLE, base=None, wrap_x=False, wrap_y=False)
    # trunk + roots first (the canopy overlaps its top)
    for y in range(30, 52):
        for x in range(13, 19):
            tone = 3 if x == 14 else 1 if x >= 17 else 2
            t.put(x, y, "bark", tone)
    for x, y0, n in [(15, 37, 3), (16, 43, 2), (14, 47, 2), (17, 40, 2)]:  # bark furrows
        for y in range(y0, y0 + n):
            t.put(x, y, "bark", 1)
        t.put(12, y, "bark", 0)
        t.put(19, y, "bark", 0)
    for x, y, tn in [(11, 50, 0), (12, 50, 2), (12, 51, 3), (11, 51, 2), (10, 51, 0), (19, 50, 1), (20, 51, 1),
                     (19, 51, 1), (21, 51, 0), (15, 40, 1), (15, 41, 1), (16, 45, 3), (16, 46, 1)]:
        t.put(x, y, "bark", tn)
    for x in range(10, 22):
        t.put(x, 52, "bark", 0)
    # canopy
    owner = {}
    for i, (cx, cy, r) in enumerate(CLUMPS):
        for y in range(int(cy - r) - 1, int(cy + r) + 2):
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                dx, dy = (x + 0.5 - cx) / r, (y + 0.5 - cy) / r
                d = dx * dx + dy * dy
                if d > 1 or not (0 <= x < w and 0 <= y < h):
                    continue
                lit = -(dx * 0.75 + dy)  # top-left light
                base_tone = 2 if i >= 6 else 1 if cy > 20 else 2  # lower / back clumps sit in shadow
                tone = base_tone + (1 if lit > 0.35 else 0) + (1 if lit > 0.9 and d > 0.45 else 0) - (1 if lit < -0.55 else 0)
                if d > 0.72 and dx + dy > 0.35:
                    tone = 1  # rim shadow on the lower right
                t.put(x, y, "leaf", max(1, min(4, tone)))
                owner[(x, y)] = i
    for x, y, tn in LEAF_MARKS:
        if (x, y) in owner:
            t.put(x, y, "leaf", tn)
            if tn >= 3 and (x + 1, y + 1) in owner:
                t.put(x + 1, y + 1, "leaf", 2 if tn == 4 else 1)
    # shadow of the canopy on the trunk
    for x in range(13, 19):
        for y in range(30, 36):
            if (x, y) not in owner:
                t.put(x, y, "bark", 1 if y < 34 else t.tone_of(x, y))
    # selective outline: darkest tone of the neighbour's material
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
    # soft ground shadow (semi-transparent) under the tree
    for y in range(50, 56):
        for x in range(2, 30):
            if t.px[y][x] is None and ((x + 0.5 - 16) / 13) ** 2 + ((y + 0.5 - 52.5) / 3.4) ** 2 <= 1:
                t.put(x, y, "leaf", 0)
                t.alpha[(x, y)] = 110
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
    out["plains.grass.0"] = meadow_tile(0).image()
    for seg in (4, 8):
        for kind in ("top", "mid", "mid-base", "top-base"):
            out[f"face.earth.{kind}.{seg}"] = face_tile(kind, seg).image()
    out["tile.walltop"] = walltop_tile().image()
    out["obj.tree"] = tree_sprite().image()
    return out


GROUND = ["tile.grass.0", "tile.grass.1", "tile.grass.2", "tile.path", "tile.sand", "tile.water.0", "tile.water.1",
          "plains.grass.0", "tile.walltop"]


def main():
    from PIL import Image

    os.makedirs(OUT, exist_ok=True)
    tiles = build()
    for name, im in tiles.items():
        im.save(os.path.join(OUT, f"{name}.png"))
    # 4x4 repeat tests (shown at 2x so a seam would be easy to see)
    os.makedirs(os.path.join(OUT, "repeat"), exist_ok=True)
    for name in GROUND:
        im = tiles[name]
        rep = Image.new("RGBA", (128, 128))
        for j in range(4):
            for i in range(4):
                rep.paste(im, (i * 32, j * 32))
        rep.resize((256, 256), Image.NEAREST).save(os.path.join(OUT, "repeat", f"repeat_{name}.png"))
    # grass variants mixed the way the game picks them (hash of the tile position)
    from mock_scene import tile_hash

    mix = Image.new("RGBA", (256, 256))
    for j in range(8):
        for i in range(8):
            mix.paste(tiles[f"tile.grass.{tile_hash(i, j) % 3}"], (i * 32, j * 32))
    mix.resize((512, 512), Image.NEAREST).save(os.path.join(OUT, "repeat", "repeat_tile.grass.mixed.png"))
    # cliff stack test: grass on top, faces stacked as gameView.addFace does, for 1/4, 1/2, 1 and 2 levels
    stacks = [("1/4段", ["top-base.4"]), ("1/2段", ["top-base.8"]), ("1段", ["top.8", "mid-base.8"]),
              ("2段", ["top.8", "mid.8", "mid.8", "mid-base.8"]), ("1.25段", ["top.8", "mid.8", "mid-base.4"])]
    cw = 4 * 32 + 16
    st = Image.new("RGBA", (len(stacks) * cw + 16, 32 + 64 + 40), (34, 36, 46, 255))
    for i, (_, segs) in enumerate(stacks):
        x0 = 16 + i * cw
        for k in range(4):
            st.paste(tiles[f"tile.grass.{k % 3}"], (x0 + k * 32, 8))
            y = 40
            for sname in segs:
                im = tiles[f"face.earth.{sname}"]
                st.alpha_composite(im, (x0 + k * 32, y))
                y += im.height
            st.paste(tiles["tile.path"].crop((0, 0, 32, min(24, st.height - y))), (x0 + k * 32, y))  # ground below
    st.resize((st.width * 2, st.height * 2), Image.NEAREST).save(os.path.join(OUT, "repeat", "stack_face.earth.png"))
    print("wrote", len(tiles), "samples to", os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main()
