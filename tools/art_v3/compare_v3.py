"""Comparison pictures of the v3 pilot against the current art (STYLE.md 10).

  01_items_same_size.png   each pilot item beside the current one, the same size in the game, shown at
                           the proposed iPhone 15 Pro scale (1 game px = 8 device px: v1 texel 4 px,
                           v3 texel 2 px). Integer scales only.
  02_scene_15pro_now.png       the same small scene, current art, current view (2556 x 1179, x2.5 per
                               v1 texel: art pixels alternate 2 and 3 device px — what ships today)
  03_scene_15pro_v1_x4.png     current art at the proposed integer view (x4 per v1 texel, 20 x 9.2 tiles)
  04_scene_15pro_v3_x2.png     v3 pilot art at the proposed integer view (x2 per v3 texel, 20 x 9.2 tiles)
  05_scene_se_v3_x1.png        v3 pilot art on iPhone SE (1334 x 750, x1 per texel, 20.8 x 11.7 tiles)
  06_crop_hero_x3.png          the hero's surroundings, device pixels enlarged x3: now / v1 x4 / v3 x2
The v3-only kinds (props, the big oak, the stone house) have no v1 counterpart: the v1 scene uses the
v1 tree, pine and house in the same places and no props.
Run: python3 tools/art_v3/compare_v3.py <out dir>
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from PIL import Image, ImageDraw  # noqa: E402

from gen_nature_v3 import hsh  # noqa: E402
from v3lib import ROOT  # noqa: E402

V1 = os.path.join(ROOT, "src", "art-release")
V1T = os.path.join(ROOT, "src", "art-release-v2", "terrain")
V3 = os.path.join(ROOT, "src", "art-release-v3")
BG = (40, 44, 52, 255)


def ld(*p):
    return Image.open(os.path.join(*p)).convert("RGBA")


PAIRS = [  # label, v1 image, v3 image
    ("hero idle", ld(V1, "hero", "hero.idle.down.0.png"), ld(V3, "hero", "hero.idle.down.0.png")),
    ("hero walk", ld(V1, "hero", "hero.walk.down.1.png"), ld(V3, "hero", "hero.walk.down.1.png")),
    ("npc woman", ld(V1, "npc", "npc.woman.idle.down.0.png"), ld(V3, "npc", "npc.woman.idle.down.0.png")),
    ("slime", ld(V1, "enemy", "enemy.slime.idle.0.png"), ld(V3, "enemy", "enemy.slime.idle.0.png")),
    ("tree -> oak (new size)", ld(V1, "terrain", "obj.tree.png"), ld(V3, "terrain", "obj.v3.oak.png")),
    ("pine", ld(V1, "terrain", "forest.pine.png"), ld(V3, "terrain", "obj.v3.pine.png")),
    ("house -> stone house (new kind)", ld(V1, "objects", "obj.house.png"), ld(V3, "objects", "obj.v3.house_stone.png")),
    ("grass tile (v2 ground)", ld(V1T, "plains.grass.0.png"), ld(V3, "terrain", "plains.grass.v3.11.png")),
    ("tuft (new)", None, ld(V3, "terrain", "prop.v3.tuft.png")),
    ("flowers (new)", None, ld(V3, "terrain", "prop.v3.flowers.png")),
    ("bush (new)", None, ld(V3, "terrain", "prop.v3.bush.png")),
    ("stump (new)", None, ld(V3, "terrain", "prop.v3.stump.png")),
]


def items(path, gpx=8):
    """v1 at 4 device px per texel, v3 at 2 (both = 8 per game px)."""
    pad = 24
    cols = []
    for label, a, b in PAIRS:
        ia = a.resize((a.width * gpx // 2, a.height * gpx // 2), Image.NEAREST) if a else None
        ib = b.resize((b.width * gpx // 4, b.height * gpx // 4), Image.NEAREST)
        cols.append((label, ia, ib))
    rows = [cols[:4], cols[4:8], cols[8:]]
    widths = [sum((ia.width if ia else 0) + ib.width + pad * 3 for _, ia, ib in r) for r in rows]
    heights = [max(max(ia.height if ia else 0, ib.height) for _, ia, ib in r) + 60 for r in rows]
    img = Image.new("RGBA", (max(widths) + pad, sum(heights) + pad), BG)
    d = ImageDraw.Draw(img)
    y = pad
    for r, h in zip(rows, heights):
        x = pad
        for label, ia, ib in r:
            d.text((x, y), label + ("   v1 (x4/texel) | v3 (x2/texel)" if ia else "   v3 (x2/texel)"),
                   fill=(230, 230, 230, 255))
            base = y + h - 8
            if ia:
                img.alpha_composite(ia, (x, base - ia.height))
                x += ia.width + pad
            img.alpha_composite(ib, (x, base - ib.height))
            x += ib.width + pad * 2
        y += h
    img.save(path, optimize=True)


# ------------------------------------------------------------------ the scene (game px)
TW, TH = 34, 17  # tiles
GW, GH = TW * 16, TH * 16
HERO = (GW // 2, GH // 2 + 10)
# kind, x, y (feet, game px)
OBJECTS = [  # placed inside the proposed 15 Pro view (319 x 147 game px round the hero)
    ("house", 172, 112), ("oak", 402, 120), ("pine", 334, 104), ("pine", 128, 196), ("oak", 196, 204),
    ("npc", 222, 126), ("hero", *HERO), ("slime", 334, 168), ("bush", 124, 122), ("bush", 418, 196),
    ("stump", 368, 140), ("flowers", 240, 164), ("flowers", 150, 154), ("flowers", 392, 156),
    ("flowers", 300, 194), ("tuft", 258, 186), ("tuft", 312, 128), ("tuft", 140, 176), ("tuft", 284, 98),
    ("tuft", 430, 150), ("tuft", 360, 200), ("pine", 60, 120), ("oak", 500, 200), ("pine", 520, 60),
]
V1ART = {
    "house": ld(V1, "objects", "obj.house.png"), "oak": ld(V1, "terrain", "obj.tree.png"),
    "pine": ld(V1, "terrain", "forest.pine.png"), "npc": ld(V1, "npc", "npc.woman.idle.down.0.png"),
    "hero": ld(V1, "hero", "hero.idle.down.0.png"), "slime": ld(V1, "enemy", "enemy.slime.idle.0.png"),
}
V3ART = {
    "house": ld(V3, "objects", "obj.v3.house_stone.png"), "oak": ld(V3, "terrain", "obj.v3.oak.png"),
    "pine": ld(V3, "terrain", "obj.v3.pine.png"), "npc": ld(V3, "npc", "npc.woman.idle.down.0.png"),
    "hero": ld(V3, "hero", "hero.idle.down.0.png"), "slime": ld(V3, "enemy", "enemy.slime.idle.0.png"),
    "bush": ld(V3, "terrain", "prop.v3.bush.png"), "stump": ld(V3, "terrain", "prop.v3.stump.png"),
    "flowers": ld(V3, "terrain", "prop.v3.flowers.png"), "tuft": ld(V3, "terrain", "prop.v3.tuft.png"),
}
SHADOW = (20, 30, 18)


def scene(density):
    """The world at `density` texels per game px (2 = v1 art, 4 = v3 art)."""
    d = density
    img = Image.new("RGBA", (GW * d, GH * d), (0, 0, 0, 255))
    for ty in range(TH):
        for tx in range(TW):
            if d == 2:
                t = ld(V1T, f"plains.grass.{hsh(tx, ty, 5) % 32}.png")
            else:
                t = ld(V3, "terrain", f"plains.grass.v3.{ty % 4}{tx % 4}.png")
            img.alpha_composite(t, (tx * 16 * d, ty * 16 * d))
    art = V1ART if d == 2 else V3ART
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    for kind, x, y in sorted(OBJECTS, key=lambda o: o[2]):
        if kind not in art or d != 4:
            continue
        w = art[kind].width / d
        sd.ellipse(((x - w * 0.36) * d, (y - 2.5) * d, (x + w * 0.36) * d, (y + 1.5) * d), fill=SHADOW + (90,))
    # (v3 only: the contact shadows of STYLE.md 8 — v1 has the hero's only)
    if d == 4:
        img.alpha_composite(sh.point(lambda v: v) if False else sh)
    for kind, x, y in sorted(OBJECTS, key=lambda o: o[2]):
        if kind not in art:
            continue
        a = art[kind]
        img.alpha_composite(a, (int(x * d - a.width / 2), int(y * d - a.height)))
    return img


def view(world, density, dev_w, dev_h, per_texel):
    """Crop the device view round the hero and scale by `per_texel` device px per texel (nearest)."""
    vw, vh = dev_w / per_texel, dev_h / per_texel  # texels
    cx, cy = HERO[0] * density, (HERO[1] - 14) * density
    box = (int(cx - vw / 2), int(cy - vh / 2), int(cx - vw / 2) + int(round(vw)), int(cy - vh / 2) + int(round(vh)))
    crop = world.crop(box)
    return crop.resize((dev_w, dev_h), Image.NEAREST)


def main(out):
    os.makedirs(out, exist_ok=True)
    items(os.path.join(out, "01_items_same_size.png"))
    w1, w3 = scene(2), scene(4)
    now = view(w1, 2, 2556, 1179, 2.5)
    now.save(os.path.join(out, "02_scene_15pro_now.png"), optimize=True)
    v1x4 = view(w1, 2, 2556, 1179, 4)
    v1x4.save(os.path.join(out, "03_scene_15pro_v1_x4.png"), optimize=True)
    v3x2 = view(w3, 4, 2556, 1179, 2)
    v3x2.save(os.path.join(out, "04_scene_15pro_v3_x2.png"), optimize=True)
    view(w3, 4, 1334, 750, 1).save(os.path.join(out, "05_scene_se_v3_x1.png"), optimize=True)
    # crops round the hero, enlarged x3 (device pixels): what one sees up close on the phone
    cw, ch = 300, 300
    strip = Image.new("RGBA", (cw * 3 * 3 + 40, ch * 3), BG)
    for i, im in enumerate((now, v1x4, v3x2)):
        c = im.crop((1278 - cw // 2, 590 - ch // 2 - 40, 1278 + cw // 2, 590 + ch // 2 - 40))
        strip.alpha_composite(c.resize((cw * 3, ch * 3), Image.NEAREST), (i * (cw * 3 + 20), 0))
    strip.save(os.path.join(out, "06_crop_hero_x3.png"), optimize=True)
    print("\n".join(sorted(os.listdir(out))))


if __name__ == "__main__":
    main(sys.argv[1])
