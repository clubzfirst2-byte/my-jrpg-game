"""Comparison pictures of the v3 pilot against the current art (STYLE.md 12), rounds 2-3.

Integer scales only, except the "now" pictures, which show what ships today (x2.5 / x1.5 per v1 texel).
  01_items_same_size.png        each pilot item beside the current one, the same size in the game
                                (15 Pro proposal: 1 game px = 8 device px; v1 texel 4 px, v3 texel 2 px)
  02_15pro_now.png              the scene, current art, current 15 Pro view (2556 x 1179, 32 x 14.7 tiles)
  03_15pro_v3_k2.png            the scene, v3 art, 15 Pro k = 2 (2556 x 1179, 20 x 9.2 tiles)
  04_se_now.png                 the scene, current art, current SE view (1334 x 750, 27.8 x 15.6 tiles)
  05_se_v3_k1.png               the scene, v3 art, SE k = 1 (1334 x 750, 20.8 x 11.7 tiles)
  06_zoom_x3_now_v3.png         round the hero, the woman and the door, device pixels x3: now | v3 (15 Pro)
  07_grass_24x12_x1.png         24 x 12 tiles of v3 ground at 1 texel = 1 px, patterns chosen by macro_of()
  08_grass_48x24_half.png       48 x 24 tiles, shrunk to half (every other texel): the wide view
No contact shadows are drawn in any scene (the art alone; shadows are the game's, STYLE.md 8).
The v3-only kinds (props, the big oak, the stone house) have no v1 counterpart: the v1 scene uses the
v1 tree, pine and house in the same places and no props.
Run: python3 tools/art_v3/compare_v3.py <out dir>
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from PIL import Image, ImageDraw  # noqa: E402

from gen_nature_v3 import hsh, macro_of  # noqa: E402
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
    ("grass tile (v2 ground)", ld(V1T, "plains.grass.0.png"), ld(V3, "terrain", "plains.grass.v3.a11.png")),
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
    ("house", 172, 128), ("oak", 404, 128), ("pine", 338, 110), ("pine", 126, 204), ("oak", 196, 214),
    ("npc", 226, 136), ("hero", *HERO), ("slime", 330, 176), ("bush", 120, 130), ("bush", 420, 200),
    ("stump", 372, 150), ("flowers", 246, 170), ("flowers", 150, 160), ("flowers", 398, 166),
    ("flowers", 300, 200), ("tuft", 262, 192), ("tuft", 312, 136), ("tuft", 140, 182), ("tuft", 286, 104),
    ("tuft", 432, 160), ("tuft", 362, 206), ("pine", 58, 128), ("oak", 500, 206), ("pine", 520, 70),
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
                t = ld(V3, "terrain", f"plains.grass.v3.{macro_of(tx // 4, ty // 4)}{ty % 4}{tx % 4}.png")
            img.alpha_composite(t, (tx * 16 * d, ty * 16 * d))
    art = V1ART if d == 2 else V3ART
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


def ground_only(tw, th):
    g = Image.new("RGBA", (tw * 64, th * 64))
    for ty in range(th):
        for tx in range(tw):
            g.alpha_composite(ld(V3, "terrain", f"plains.grass.v3.{macro_of(tx // 4, ty // 4)}{ty % 4}{tx % 4}.png"),
                              (tx * 64, ty * 64))
    return g


def main(out):
    os.makedirs(out, exist_ok=True)
    items(os.path.join(out, "01_items_same_size.png"))
    w1, w3 = scene(2), scene(4)
    now = view(w1, 2, 2556, 1179, 2.5)
    now.save(os.path.join(out, "02_15pro_now.png"), optimize=True)
    v3 = view(w3, 4, 2556, 1179, 2)
    v3.save(os.path.join(out, "03_15pro_v3_k2.png"), optimize=True)
    view(w1, 2, 1334, 750, 1.5).save(os.path.join(out, "04_se_now.png"), optimize=True)
    view(w3, 4, 1334, 750, 1).save(os.path.join(out, "05_se_v3_k1.png"), optimize=True)
    # zoom: the same game area round the hero, the woman and the door, device pixels x3
    gx0, gy0, gx1, gy1 = HERO[0] - 110, HERO[1] - 62, HERO[0] + 20, HERO[1] + 4

    def crop(im, d, per_texel):
        vw, vh = im.width / per_texel, im.height / per_texel
        ox, oy = int(HERO[0] * d - vw / 2), int((HERO[1] - 14) * d - vh / 2)
        return im.crop((int((gx0 * d - ox) * per_texel), int((gy0 * d - oy) * per_texel),
                        int((gx1 * d - ox) * per_texel), int((gy1 * d - oy) * per_texel)))
    a, b = crop(now, 2, 2.5), crop(v3, 4, 2)
    z = Image.new("RGBA", (a.width * 3 + b.width * 3 + 30, max(a.height, b.height) * 3), BG)
    z.alpha_composite(a.resize((a.width * 3, a.height * 3), Image.NEAREST), (0, 0))
    z.alpha_composite(b.resize((b.width * 3, b.height * 3), Image.NEAREST), (a.width * 3 + 30, 0))
    z.save(os.path.join(out, "06_zoom_x3_now_v3.png"), optimize=True)
    ground_only(24, 12).save(os.path.join(out, "07_grass_24x12_x1.png"), optimize=True)
    g = ground_only(48, 24)
    g.resize((g.width // 2, g.height // 2), Image.NEAREST).save(os.path.join(out, "08_grass_48x24_half.png"),
                                                                  optimize=True)
    print("\n".join(sorted(os.listdir(out))))


if __name__ == "__main__":
    main(sys.argv[1])
