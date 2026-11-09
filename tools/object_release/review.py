"""Self-check sheets for the release objects (docs/art-release/objects/):

  review_sheet.png    every sprite, 3x, by group, with the hero (32x56) at the start of each row for scale
  review_scenes.png   three small scenes at 1x and 3x: a house interior, a ruin, the field (scale + reading)
  review_icons.png    the 12 icons in a dark UI panel (#20242c, guide 6.1), 3x and 1x
  review_snow.png     effects, lit objects and icons on snow (mount.snow), 3x (guide 6.2: light ground too)
  review_compare.png  placeholder (docs/art-kit) vs release, 3x
Backdrops are flat guide colours (2.5, provisional); the tiles themselves are the terrain wave's.
"""

import os
import random

from PIL import Image, ImageDraw

from mock import BG_UI, HERO, SNOW, compare, grass_tile, label, path_tile, place, to_image
from objects import ANCHOR
from objects2 import ANCHOR2

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
OUT = os.path.join(ROOT, "docs", "art-release", "objects")
AN = {**ANCHOR, **ANCHOR2}
WOOD_FLOOR = [(0x4A, 0x2C, 0x16), (0x6E, 0x44, 0x24), (0x90, 0x60, 0x38)]
RUIN_FLOOR = [(0x3A, 0x42, 0x46), (0x5A, 0x64, 0x68), (0x7C, 0x86, 0x88)]
PLASTER = [(0x7A, 0x6A, 0x58), (0xA8, 0x96, 0x7E), (0xC4, 0xB4, 0x9C)]

GROUPS = [
    ("buildings / entrances", ["obj.house", "obj.door", "obj.cave", "obj.stairs"]),
    ("furniture", ["obj.lowwall", "obj.bed", "obj.table", "obj.shelf", "obj.charm_shelf", "obj.charm_shelf.on",
                   "obj.counter", "obj.stove", "obj.barrel", "obj.mat", "obj.anvil"]),
    ("props", ["obj.chest.closed", "obj.chest.open", "obj.jar", "obj.crate", "obj.campfire.0", "obj.campfire.1",
               ]),
    ("puzzle / ruin", ["obj.checkpoint.off", "obj.checkpoint.on", "obj.brazier.0", "obj.brazier.1", "obj.crystal",
                       "obj.receiver.off", "obj.receiver.on", "obj.sconce.off", "obj.sconce.on", "obj.stone.off",
                       "obj.stone.on", "obj.pillar", "obj.altar", "sw.plate.off", "sw.plate.on", "sw.sensor.off",
                       "sw.sensor.on"]),
    ("icons", ["icon.sword", "icon.bow", "icon.armor", "icon.mushroom", "icon.berry", "icon.herb", "icon.pepper",
               "icon.meat", "icon.fang", "icon.shard", "icon.arrows", "icon.food", "icon.star_shard", "icon.charm"]),
    ("fx / ui", ["fx.slash", "fx.fire.0", "fx.fire.1", "fx.glider", "fx.shadow", "fx.arrow", "fx.orb", "fx.shield",
                 "fx.bow", "fx.smoke", "fx.light", "ui.marker"]),
]


def flat(size, cols, seed):
    rnd = random.Random(seed)
    im = Image.new("RGBA", size, cols[1] + (255,))
    px = im.load()
    for _ in range(size[0] * size[1] // 40):
        px[rnd.randrange(size[0]), rnd.randrange(size[1])] = rnd.choice((cols[0], cols[2])) + (255,)
    return im


def big(im, k=3):
    return im.resize((im.size[0] * k, im.size[1] * k), Image.NEAREST)


def sheet(S, hero):
    k, pad = 3, 10
    rows = []
    for title, names in GROUPS:
        ims = [("hero", hero)] + [(n, to_image(S[n])) for n in names]
        h = max(i.size[1] for _, i in ims) * k + 30
        w = sum(i.size[0] * k + pad for _, i in ims) + pad
        blk = Image.new("RGBA", (w, h), (0x3C, 0x6A, 0x38, 255))
        d = ImageDraw.Draw(blk)
        x = pad
        for n, i in ims:
            b = big(i, k)
            blk.alpha_composite(b, (x, h - 14 - b.size[1]))
            d.text((x, h - 12), n.replace("obj.", "").replace("icon.", "i.")[:14], fill=(255, 255, 255))
            x += b.size[0] + pad
        rows.append((title, blk))
    W = max(b.size[0] for _, b in rows) + 2 * pad
    H = sum(b.size[1] + 18 for _, b in rows) + pad
    out = Image.new("RGBA", (W, H), (0x1C, 0x1C, 0x24, 255))
    d = ImageDraw.Draw(out)
    y = pad
    for t, b in rows:
        label(d, pad, y, t + "  (3x; the hero 32x56 first for scale)")
        out.alpha_composite(b, (pad, y + 14))
        y += b.size[1] + 18
    return out


def put_all(im, S, items, hero=None, hero_at=None):
    drawn = list(items) + ([("hero", *hero_at)] if hero is not None else [])
    flatz = {"obj.mat", "obj.stairs", "sw.plate.off", "sw.plate.on"}
    drawn.sort(key=lambda e: (e[0] not in flatz, e[2]))
    for n, x, y in drawn:
        if n == "hero":
            place(im, hero, x, y)
        else:
            place(im, to_image(S[n]), x, y, AN[n])


def scenes(S, hero):
    # interior: plaster wall band at the top, wood floor
    a = flat((12 * 32, 7 * 32), WOOD_FLOOR, 1)
    a.alpha_composite(flat((12 * 32, 40), PLASTER, 2), (0, 0))
    put_all(a, S, [
        ("obj.lowwall", 16 + 32 * 0, 64), ("obj.lowwall", 16 + 32 * 1, 64), ("obj.lowwall", 16 + 32 * 2, 64),
        ("obj.shelf", 16 + 32 * 4, 64), ("obj.charm_shelf.on", 16 + 32 * 5, 64), ("obj.stove", 16 + 32 * 7, 64),
        ("obj.barrel", 16 + 32 * 8, 64), ("obj.bed", 16 + 32 * 10, 128), ("obj.table", 16 + 32 * 2, 128),
        ("obj.jar", 16 + 32 * 1, 128),
        ("obj.counter", 16 + 32 * 5, 160), ("obj.counter", 16 + 32 * 6, 160), ("obj.counter", 16 + 32 * 7, 160),
        ("obj.anvil", 16 + 32 * 9, 192), ("obj.mat", 16 + 32 * 3, 224), ("obj.crate", 16 + 32 * 0, 224),
    ], hero, (16 + 32 * 3, 196))
    # ruin
    b = flat((12 * 32, 7 * 32), RUIN_FLOOR, 3)
    put_all(b, S, [
        ("obj.pillar", 16, 64), ("obj.door", 16 + 32 * 2, 64), ("obj.pillar", 16 + 32 * 4, 64),
        ("obj.receiver.on", 16 + 32 * 5, 96), ("obj.receiver.off", 16 + 32 * 6, 96), ("obj.altar", 16 + 32 * 9, 96),
        ("obj.brazier.0", 16 + 32 * 8, 64), ("obj.sconce.on", 16 + 32 * 10, 64), ("obj.sconce.off", 16 + 32 * 11, 64),
        ("obj.stone.on", 16 + 32 * 1, 160), ("obj.stone.off", 16 + 32 * 2, 160), ("sw.sensor.on", 16 + 32 * 7, 160),
        ("sw.sensor.off", 16 + 32 * 8, 160), ("sw.plate.on", 16 + 32 * 10, 190), ("sw.plate.off", 16 + 32 * 11, 190),
        ("obj.crystal", 16 + 32 * 5, 208), ("obj.stairs", 16 + 32 * 0, 224), ("obj.checkpoint.on", 16 + 32 * 9, 160),
    ], hero, (16 + 32 * 4, 188))
    b.alpha_composite(to_image(S["fx.light"]), (16 + 32 * 6 - 8, 150))
    # field
    c = Image.new("RGBA", (12 * 32, 7 * 32))
    for ty in range(7):
        for tx in range(12):
            t = path_tile(tx + ty * 5) if ty == 4 else grass_tile(tx * 13 + ty * 7)
            c.alpha_composite(t, (tx * 32, ty * 32))
    # a cliff band with the cave
    c.alpha_composite(flat((5 * 32, 48), [(0x3A, 0x2A, 0x1C), (0x57, 0x40, 0x2A), (0x74, 0x58, 0x3A)], 4), (0, 16))
    put_all(c, S, [
        ("obj.cave", 16 + 32 * 2, 64), ("obj.campfire.1", 16 + 32 * 1, 192),
        ("fx.fire.0", 16 + 32 * 9, 192), ("obj.chest.closed", 16 + 32 * 10, 192), ("icon.berry", 16 + 32 * 6, 186),
        ("icon.mushroom", 16 + 32 * 7, 186), ("icon.arrows", 16 + 32 * 8, 186),
    ], hero, (16 + 32 * 4, 160))
    for n, x, y in (("fx.smoke", 16 + 32 * 1, 140), ("fx.smoke", 22 + 32 * 1, 124), ("fx.orb", 16 + 32 * 6, 150),
                    ("fx.arrow", 16 + 32 * 7, 140)):
        place(c, to_image(S[n]), x, y, "centre")
    place(c, to_image(S["fx.glider"]), 16 + 32 * 4, 160 - 44)
    place(c, to_image(S["fx.shield"]), 16 + 32 * 4 + 12, 160 - 20, "centre")
    place(c, to_image(S["fx.bow"]), 16 + 32 * 4 - 14, 160 - 22, "centre")
    pad = 12
    W = 3 * 12 * 32 + 2 * pad
    H = pad + 3 * (16 + 7 * 32 + pad) + 3 * (16 + 3 * 7 * 32 + pad)
    out = Image.new("RGBA", (W, H), (0x1C, 0x1C, 0x24, 255))
    d = ImageDraw.Draw(out)
    y = pad
    for t, im in (("interior", a), ("ruin", b), ("field", c)):
        label(d, pad, y, f"{t} — 1x (release size)")
        out.alpha_composite(im, (pad, y + 14))
        y += 14 + im.size[1] + pad
    for t, im in (("interior", a), ("ruin", b), ("field", c)):
        label(d, pad, y, f"{t} — 3x")
        out.alpha_composite(big(im), (pad, y + 14))
        y += 14 + im.size[1] * 3 + pad
    return out


def icons(S):
    names = GROUPS[4][1]
    slot, pad = 28, 6
    w = pad + len(names) * (slot + pad)
    h = slot + pad * 2
    im = Image.new("RGBA", (w, h), BG_UI + (255,))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], outline=(0x8A, 0x74, 0x3C, 255))
    for i, n in enumerate(names):
        x = pad + i * (slot + pad)
        d.rectangle([x, pad, x + slot - 1, pad + slot - 1], fill=BG_UI + (255,), outline=(0x4A, 0x52, 0x60, 255))
        im.alpha_composite(to_image(S[n]), (x + 4, pad + 4))
    out = Image.new("RGBA", (w * 3 + 24, h * 4 + 40), (0x1C, 0x1C, 0x24, 255))
    dd = ImageDraw.Draw(out)
    label(dd, 8, 4, "icons in a UI panel #20242c: 3x, then 1x (" + ", ".join(n[5:] for n in names) + ")")
    out.alpha_composite(big(im), (8, 18))
    out.alpha_composite(im, (8, 26 + h * 3))
    return out


def snow(S):
    names = ["fx.slash", "fx.fire.0", "fx.orb", "fx.arrow", "fx.shield", "fx.bow", "fx.smoke", "fx.light", "fx.glider",
             "ui.marker", "obj.checkpoint.on", "obj.receiver.on", "obj.stone.on", "sw.sensor.on", "obj.crystal",
             "obj.brazier.0", "icon.shard", "icon.fang", "icon.arrows", "fx.shadow"]
    w = sum(to_image(S[n]).size[0] + 8 for n in names) + 8
    im = Image.new("RGBA", (w, 64), SNOW[1] + (255,))
    rnd = random.Random(5)
    px = im.load()
    for _ in range(w):
        px[rnd.randrange(w), rnd.randrange(64)] = rnd.choice((SNOW[0], SNOW[2], SNOW[3])) + (255,)
    x = 8
    for n in names:
        i = to_image(S[n])
        if AN[n] == "feet":
            place(im, i, x + i.size[0] // 2, 58)
        else:
            place(im, i, x + i.size[0] // 2, 34, "centre")
        x += i.size[0] + 8
    return big(im)


def main(S):
    os.makedirs(OUT, exist_ok=True)
    hero = Image.open(HERO).convert("RGBA")
    sheet(S, hero).save(os.path.join(OUT, "review_sheet.png"))
    scenes(S, hero).save(os.path.join(OUT, "review_scenes.png"))
    icons(S).save(os.path.join(OUT, "review_icons.png"))
    snow(S).save(os.path.join(OUT, "review_snow.png"))
    compare(S).save(os.path.join(OUT, "review_compare.png"))
    print("wrote the review sheets to", os.path.relpath(OUT, ROOT))
