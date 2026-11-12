"""Comparison pictures of the v3 village art (gen_village_v3.py) against the current art.

Both at the 15 Pro v3 view (k = 2: 1 game px = 8 device px, 2556 x 1179 = 20 x 9.2 tiles): the current
art (density 2) at 4 device px per texel, the v3 art (density 4) at 2. Integer scales only.
  01_items_same_size.png          every village key: now | v3 summer | v3 winter (autumn where it differs)
  02_village_now_15pro_k2.png     the village, current art (current houses, chest, barrels ... on the v2 grass)
  03_village_v3_<season>_15pro_k2.png   the same place, v3 art (the v3 grass, trees and props of gfx/v3-art)
  04_village_<now|v3>_night_15pro_k2.png  night: the scene darkened, only the window glass lit
                                  (houseWindows.glassKind and WINDOW_GLOW colours, gfx/fx-v2)
  05_zoom_x3_now_v3.png           the door, the hero and the chest at device px x3: now | v3
  06_states_<k2|k1>.png           the state pairs on v3 grass (chest closed / open, plate off / on,
                                  checkpoint off / on, campfire 0 / 1, brazier 0 / 1): rows now | v3 | v3 winter;
                                  k2 = 15 Pro (8 device px per game px), k1 = SE (4)
  07_night_windows_k2x2.png       the windows of the 3 house pictures at night (the scene's night rule),
                                  15 Pro device px shown x2: house, stone house (summer = the pilot file),
                                  stone house winter
New kinds (well, fence, signpost, the stone house) have no current counterpart: the "now" scene leaves
their places empty. No contact shadows (the game's, STYLE.md 8).
Run: python3 tools/art_v3/compare_village_v3.py <out dir>
"""

import functools
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

import gen_village_v3 as V  # noqa: E402
from gen_ground_v3 import ground_tile  # noqa: E402
from gen_nature_v3 import hsh  # noqa: E402
from v3lib import ROOT  # noqa: E402

NOW = os.path.join(ROOT, "src", "art-release")
NOWT = os.path.join(ROOT, "src", "art-release-v2", "terrain")
V3 = os.path.join(ROOT, "src", "art-release-v3")
BG = (40, 44, 52, 255)
DEV_W, DEV_H = 2556, 1179
GW, GH = 320, 148  # game px shown (20 x 9.25 tiles)


@functools.lru_cache(maxsize=None)
def ld(*p):
    return Image.open(os.path.join(*p)).convert("RGBA")


def v3obj(key, season):
    pre = V.PREFIX[season]
    p = os.path.join(V.OUT, f"{pre}{key}.png")
    return ld(p if os.path.exists(p) else os.path.join(V.OUT, f"{key}.png"))


def v3terr(key, season):
    pre = V.PREFIX[season]
    p = os.path.join(V3, "terrain", f"{pre}{key}.png")
    return ld(p if os.path.exists(p) else os.path.join(V3, "terrain", f"{key}.png"))


def now_obj(key, season):
    return ld(NOW, "objects", key + ".png")


# ------------------------------------------------------------------ 01 items

ITEM_KEYS = [k for k, _, _ in V.ITEMS]


def items(path):
    pad = 20
    cells = []
    for key, _, seasons in V.ITEMS:
        imgs = []
        cur = os.path.join(NOW, "objects", key + ".png")
        if os.path.exists(cur):
            a = ld(cur)
            imgs.append(("now", a.resize((a.width * 4, a.height * 4), Image.NEAREST)))
        for s in ("summer", "autumn", "winter"):
            if s == "summer" or s in seasons:
                b = v3obj(key, s)
                imgs.append((s, b.resize((b.width * 2, b.height * 2), Image.NEAREST)))
        cells.append((key, imgs))
    rows, row, wsum = [], [], 0
    for cell in cells:
        w = sum(i.width + pad for _, i in cell[1]) + pad
        if row and wsum + w > 2600:
            rows.append(row)
            row, wsum = [], 0
        row.append(cell)
        wsum += w
    rows.append(row)
    widths = [sum(sum(i.width + pad for _, i in c[1]) + pad for c in r) for r in rows]
    heights = [max(i.height for c in r for _, i in c[1]) + 44 for r in rows]
    img = Image.new("RGBA", (max(widths) + pad, sum(heights) + pad), BG)
    d = ImageDraw.Draw(img)
    y = pad
    for r, h in zip(rows, heights):
        x = pad
        for key, ims in r:
            d.text((x, y), key + "  (" + " | ".join(n for n, _ in ims) + ")", fill=(230, 230, 230, 255))
            for _, im in ims:
                img.alpha_composite(im, (x, y + h - 6 - im.height))
                x += im.width + pad
            x += pad
        y += h
    img.save(path, optimize=True)


# ------------------------------------------------------------------ the village scene (game px, feet)

SCENE = [  # kind, key, x, y; kind: obj (village), terr (v3 plains), char
    ("terr", "plains.tree.v3.pine", 14, 62), ("terr", "plains.tree.v3.oak_m", 306, 44),
    ("obj", "obj.house", 62, 74), ("obj", "obj.v3.house_stone", 150, 80), ("obj", "obj.v3.well", 236, 86),
    ("obj", "obj.checkpoint.off", 292, 76),
    ("obj", "obj.barrel", 96, 100), ("obj", "obj.barrel", 104, 106), ("obj", "obj.crate", 118, 104),
    ("obj", "obj.jar", 128, 98), ("obj", "obj.chest.closed", 28, 118),
    ("terr", "plains.prop.v3.bush", 40, 92), ("terr", "plains.prop.v3.flowers_mix", 196, 102),
    ("terr", "plains.prop.v3.tuft", 84, 132), ("terr", "plains.prop.v3.tuft", 262, 110),
    ("obj", "obj.v3.signpost", 204, 124),
    ("obj", "obj.v3.fence.l", 232, 126), ("obj", "obj.v3.fence.h", 248, 126), ("obj", "obj.v3.fence.h", 264, 126),
    ("obj", "obj.v3.fence.h", 280, 126), ("obj", "obj.v3.fence.r", 296, 126),
    ("char", "npc.woman.idle.down.0", 140, 112), ("char", "hero.idle.down.0", 160, 122),
    ("obj", "obj.campfire.0", 120, 142), ("obj", "sw.plate.off", 24, 144),
]
NOW_TERR = {"plains.tree.v3.pine": ("terrain", "forest.pine.png"), "plains.tree.v3.oak_m": ("terrain", "obj.tree.png")}


def scene(version, season):
    d = 2 if version == "now" else 4
    img = Image.new("RGBA", (GW * d, GH * d), (0, 0, 0, 255))
    for ty in range(GH // 16 + 1):
        for tx in range(GW // 16):
            if version == "now":
                pre = {"summer": "", "autumn": "autumn.", "winter": "winter."}[season]
                t = ld(NOWT, f"{pre}plains.grass.{hsh(tx, ty, 5) % 32}.png")
            else:
                t = ground_tile(tx + 40, ty + 40, season, load=lambda p: ld(p))
            img.alpha_composite(t, (tx * 16 * d, ty * 16 * d))
    lit_boxes = []
    for kind, key, x, y in sorted(SCENE, key=lambda o: o[3]):
        if version == "now":
            if kind == "obj":
                p = os.path.join(NOW, "objects", key + ".png")
                if not os.path.exists(p):
                    continue
                im = ld(p)
            elif kind == "terr":
                if key not in NOW_TERR:
                    continue
                im = ld(NOW, *NOW_TERR[key])
            else:
                grp = "hero" if key.startswith("hero") else "npc"
                im = ld(NOW, grp, key + ".png")
        else:
            if kind == "obj":
                im = v3obj(key, season)
            elif kind == "terr":
                im = v3terr(key + ".0", season)
            else:
                grp = "hero" if key.startswith("hero") else "npc"
                im = ld(V3, grp, key + ".png")
        px, py = x * d - im.width // 2, y * d - im.height
        img.alpha_composite(im, (px, py))
        if key in ("obj.house", "obj.v3.house_stone"):
            lit_boxes.append((im, px, py))
    return img, lit_boxes


def night(img, lit_boxes):
    """A night view: ambient (0.30, 0.34, 0.55) on everything, then only the glass of the windows lit
    with houseWindows.WINDOW_GLOW (glass #ffc860, darkest glass #d8903c), drawn above the dark."""
    a = np.array(img).astype(np.float32)
    a[..., 0] *= 0.30
    a[..., 1] *= 0.34
    a[..., 2] *= 0.55
    out = a.astype(np.uint8)
    for im, px, py in lit_boxes:
        b = np.array(im)
        for y in range(b.shape[0]):
            for x in range(b.shape[1]):
                k = V.glass_kind(*[int(v) for v in b[y, x]])
                if k and 0 <= py + y < out.shape[0] and 0 <= px + x < out.shape[1] and b[y, x, 3] == 255:
                    out[py + y, px + x, :3] = (0xd8, 0x90, 0x3c) if k == 2 else (0xff, 0xc8, 0x60)
    return Image.fromarray(out, "RGBA")


def to_device(img, d):
    k = 8 // d
    return img.resize((img.width * k, img.height * k), Image.NEAREST).crop((0, 0, DEV_W, DEV_H))


def zoom(path, now, v3):
    """Door, hero and chest: a crop of each scene at device px x3 (now | v3)."""
    box = (16 * 8, 40 * 8, 176 * 8, 124 * 8)
    a = now.crop(box)
    b = v3.crop(box)
    a = a.resize((a.width * 3 // 2, a.height * 3 // 2), Image.NEAREST)
    b = b.resize((b.width * 3 // 2, b.height * 3 // 2), Image.NEAREST)
    img = Image.new("RGBA", (a.width + b.width + 24, a.height), BG)
    img.alpha_composite(a, (0, 0))
    img.alpha_composite(b, (a.width + 24, 0))
    img.save(path, optimize=True)


STATE_PAIRS = [("obj.chest.closed", "obj.chest.open"), ("sw.plate.off", "sw.plate.on"),
               ("obj.checkpoint.off", "obj.checkpoint.on"), ("obj.campfire.0", "obj.campfire.1"),
               ("obj.brazier.0", "obj.brazier.1")]


def states(path, gpx):
    """State pairs on v3 grass, gpx device px per game px; rows: now | v3 summer | v3 winter."""
    cell_w, cell_h, pad = 30, 24, 4  # game px
    cols = [k for pr in STATE_PAIRS for k in pr]
    W, H = (len(cols) * (cell_w + pad) + pad) * 4, (3 * (cell_h + pad) + pad) * 4
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    for ty in range(H // 64 + 1):
        for tx in range(W // 64 + 1):
            img.alpha_composite(ground_tile(tx + 7, ty + 3, "summer", load=lambda p: ld(p)), (tx * 64, ty * 64))
    for r, (ver, season) in enumerate((("now", "summer"), ("v3", "summer"), ("v3", "winter"))):
        for i, key in enumerate(cols):
            if ver == "now":
                im = ld(NOW, "objects", key + ".png")
                im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
            else:
                im = v3obj(key, season)
            fx = (pad + i * (cell_w + pad) + cell_w // 2) * 4
            fy = (pad + r * (cell_h + pad) + cell_h) * 4
            img.alpha_composite(im, (fx - im.width // 2, fy - im.height))
    k = gpx // 4 if gpx >= 4 else 1
    if gpx == 4:
        img = img  # SE: 1 texel = 1 device px
    else:
        img = img.resize((img.width * k, img.height * k), Image.NEAREST)
    img.save(path, optimize=True)


def night_windows(path):
    """The houses' windows at night (scene's night rule), 15 Pro device px (x2 per texel) shown x2."""
    parts = []
    for key, season in (("obj.house", "summer"), ("obj.v3.house_stone", "summer"), ("obj.v3.house_stone", "winter")):
        im = v3obj(key, season)
        dark = night(im, [(im, 0, 0)])
        parts.append(dark)
    crops = [parts[0].crop((8, 110, 184, 178)), parts[1].crop((28, 104, 228, 266)), parts[2].crop((28, 104, 228, 266))]
    crops = [c.resize((c.width * 4, c.height * 4), Image.NEAREST) for c in crops]
    W = sum(c.width for c in crops) + 24 * (len(crops) + 1)
    H = max(c.height for c in crops) + 48
    img = Image.new("RGBA", (W, H), BG)
    x = 24
    for c in crops:
        img.alpha_composite(c, (x, 24))
        x += c.width + 24
    img.save(path, optimize=True)


def main(out):
    os.makedirs(out, exist_ok=True)
    items(os.path.join(out, "01_items_same_size.png"))
    now, nb = scene("now", "summer")
    nowd = to_device(now, 2)
    nowd.save(os.path.join(out, "02_village_now_15pro_k2.png"), optimize=True)
    v3d = None
    for s in ("summer", "autumn", "winter"):
        img, lb = scene("v3", s)
        dv = to_device(img, 4)
        dv.save(os.path.join(out, f"03_village_v3_{s}_15pro_k2.png"), optimize=True)
        if s == "summer":
            v3d = dv
            to_device(night(img, lb), 4).save(os.path.join(out, "04_village_v3_night_15pro_k2.png"), optimize=True)
    to_device(night(now, []), 2).save(os.path.join(out, "04_village_now_night_15pro_k2.png"), optimize=True)
    zoom(os.path.join(out, "05_zoom_x3_now_v3.png"), nowd, v3d)
    states(os.path.join(out, "06_states_k2.png"), 8)
    states(os.path.join(out, "06_states_k1.png"), 4)
    night_windows(os.path.join(out, "07_night_windows_k2x2.png"))
    print(sorted(os.listdir(out)))


if __name__ == "__main__":
    main(sys.argv[1])
