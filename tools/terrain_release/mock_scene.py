"""Mock top-down scene (20 x 12 tiles) built from the terrain samples, with the release hero on it.

Rendered the way src/view/gameView.js draws terrain, so it shows the real look:
  * flat ground tinted by levelTint(0) (x0.8), raised ground by levelTint(h);
  * a raised tile's surface is drawn h px higher, its south face is stacked from face.* segments
    (top / mid / -base, 8 or 4 game px each), with a contact shadow at the foot and dark edges
    where a neighbour is lower;
  * objects and the hero are Y-sorted by their feet.

Writes docs/art-candidates/terrain/:
  mock_scene.png      1x (= the release resolution, 2 art px per game px)
  mock_scene_3x.png   3x (to look at the pixels)
  mock_compare.png    the current placeholders (docs/art-kit) | the samples, same map, 2x
  samples_sheet.png   every sample with its name, 4x
  water_anim.gif      the water's 2 frames as the game plays them (0.6 s each)
  palettes.png        the proposed ramps per region
Run after gen_samples.py: python3 tools/terrain_release/mock_scene.py
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(__file__))

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
DOCS = os.path.join(ROOT, "docs", "art-candidates", "terrain")
SAMPLES = os.path.join(DOCS, "samples")
KIT = os.path.join(ROOT, "docs", "art-kit")
HERO = os.path.join(ROOT, "src", "art-release", "hero", "hero.idle.down.0.png")

TS = 32  # art px per tile
LEVEL = 32  # 1 level (16 game px) in art px
EDGE = (0x1A, 0x1C, 0x2C)
EDGE_PX, SHADOW_PX = 4, 12  # gameView EDGE_PX 2 / CLIFF_SHADOW_PX 6, in art px
EDGE_A, SHADOW_A = 0.55, 0.32


def tile_hash(x, y):
    """gameView.js hash(): which grass variant a tile gets."""
    h = (x * 374761393 + y * 668265263) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return (h ^ (h >> 16)) & 0xFFFFFFFF


def level_tint(h_art):
    level = h_art / LEVEL
    return round(255 * min(1, 0.8 + 0.07 * level)) / 255


# The map: G grass, P path, S sand, W water. Elevation in levels per tile (0 / 1 / 2).
GROUND = [
    "GGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGPGGGGGGGGG",
    "PPPPPPPPPPPGGSSSSSGG",
    "GGGGGGGGGGPGSSWWWSSG",
    "GGGGGGGGGGPSSWWWWWSG",
    "GGGGGGGGGGPSSWWWWWSS",
    "GGGGGGGGGGPGSSWWWSSG",
    "GGGGGGGGGGPGGSSSSSGG",
]
ELEV = [
    "00000000000000000000",
    "22221111110000000000",
    "22221111110000000000",
    "11111111110000000000",
    "00000000000000000000",
    "00000000000000000000",
    "00000000000000000000",
    "00000000000000000000",
    "00000000000000000000",
    "00000000000000000000",
    "00000000000000000000",
    "00000000000000000000",
]
TREES = [(12, 1), (16, 2), (18, 4), (14, 4), (1, 8), (3, 10), (6, 9), (17, 11), (2, 2), (7, 2)]
HERO_AT = (8, 7)  # tile under the hero's feet
W, H = len(GROUND[0]), len(GROUND)


def load(path):
    return Image.open(path).convert("RGBA")


class Art:
    def __init__(self, source):
        self.source = source

    def get(self, name):
        if self.source == "samples":
            p = os.path.join(SAMPLES, f"{name}.png")
            if os.path.exists(p):
                return load(p)
        for sub in os.listdir(KIT):
            p = os.path.join(KIT, sub, f"{name}.png")
            if os.path.exists(p):
                return load(p)
        raise FileNotFoundError(name)


def tinted(im, k):
    if k >= 1:
        return im
    r, g, b, a = im.split()
    r, g, b = (c.point(lambda v: int(v * k)) for c in (r, g, b))
    return Image.merge("RGBA", (r, g, b, a))


def overlay(canvas, x, y, w, h, colour, alpha):
    box = Image.new("RGBA", (max(1, w), max(1, h)), colour + (int(255 * alpha),))
    canvas.alpha_composite(box, (int(x), int(y)))


def surface_key(tx, ty, art):
    ch = GROUND[ty][tx]
    if ch == "P":
        return "tile.path"
    if ch == "S":
        return "tile.sand"
    if ch == "W":
        return "tile.water.0"
    return f"tile.grass.{tile_hash(tx, ty) % 3}"


def elev(tx, ty):
    if 0 <= tx < W and 0 <= ty < H:
        return int(ELEV[ty][tx]) * LEVEL
    return 0


def render(source, water_frame=0):
    art = Art(source)
    cache = {}

    def get(n):
        if n not in cache:
            cache[n] = art.get(n)
        return cache[n]

    img = Image.new("RGBA", (W * TS, H * TS), (0, 0, 0, 255))
    # flat ground
    for ty in range(H):
        for tx in range(W):
            if elev(tx, ty) == 0:
                k = surface_key(tx, ty, art)
                if k.startswith("tile.water"):
                    k = f"tile.water.{water_frame}"
                img.alpha_composite(tinted(get(k), level_tint(0)), (tx * TS, ty * TS))
    # sortable draws: (sort_y, fn)
    draws = []
    for ty in range(H):
        for tx in range(W):
            h = elev(tx, ty)
            if h == 0:
                continue

            def raised(tx=tx, ty=ty, h=h):
                x, top = tx * TS, ty * TS - h
                img.alpha_composite(tinted(get(surface_key(tx, ty, art)), level_tint(h)), (x, top))
                face_top = (ty + 1) * TS - h
                face_bottom = (ty + 1) * TS - elev(tx, ty + 1)
                remaining, y, first = face_bottom - face_top, face_top, True
                while remaining > 0:
                    seg = 16 if remaining >= 16 else 8  # 8 / 4 game px
                    last = remaining - seg <= 0
                    name = f"face.earth.{'top' if first else 'mid'}{'-base' if last else ''}.{seg // 2}"
                    img.alpha_composite(get(name), (x, y))
                    y += seg
                    remaining -= seg
                    first = False
                if face_bottom > face_top:
                    overlay(img, x, face_bottom, TS, SHADOW_PX, EDGE, SHADOW_A)
                if elev(tx + 1, ty) < h and tx + 1 < W:
                    overlay(img, x + TS - EDGE_PX, top, EDGE_PX, TS, EDGE, EDGE_A)
                    overlay(img, x + TS, ty * TS - elev(tx + 1, ty), SHADOW_PX, TS, EDGE, SHADOW_A)
                if elev(tx - 1, ty) < h and tx > 0:
                    overlay(img, x, top, EDGE_PX, TS, EDGE, EDGE_A)
                if ty > 0 and elev(tx, ty - 1) < h:
                    overlay(img, x, top, TS, EDGE_PX, EDGE, EDGE_A)

            draws.append((ty * TS + 0.001, raised))
    tree = get("obj.tree")
    for tx, ty in TREES:
        foot = (ty + 1) * TS - 4 - elev(tx, ty)

        def put_tree(tx=tx, foot=foot):
            img.alpha_composite(tree, (tx * TS + TS // 2 - tree.width // 2, foot - tree.height))

        # sorted by the tile it stands on (raised ground draws first), drawn at its raised height
        draws.append(((ty + 1) * TS - 4, put_tree))
    hero = load(HERO)
    hx_, hy_ = HERO_AT
    hfoot = (hy_ + 1) * TS - 6

    def put_hero():
        sh = Image.new("RGBA", (24, 10), (0, 0, 0, 0))
        ImageDraw.Draw(sh).ellipse((0, 0, 23, 9), fill=(0, 0, 0, 90))
        img.alpha_composite(sh, (hx_ * TS + 4, hfoot - 6))
        img.alpha_composite(hero, (hx_ * TS + TS // 2 - hero.width // 2, hfoot - hero.height))

    draws.append((hfoot, put_hero))
    for _, fn in sorted(draws, key=lambda d: d[0]):
        fn()
    return img


def font(n):
    for p in ("/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf", "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, n)
    return ImageFont.load_default()


def big(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def samples_sheet():
    from gen_samples import build

    tiles = build()
    k, pad, lab = 4, 16, 22
    f = font(14)
    names = list(tiles)
    cols = 6
    cw = 32 * k + pad
    rows = []
    for i in range(0, len(names), cols):
        rows.append(names[i:i + cols])
    heights = [max(tiles[n].height for n in r) * k + lab + pad for r in rows]
    sheet = Image.new("RGBA", (cols * cw + pad, sum(heights) + pad), (34, 36, 46, 255))
    d = ImageDraw.Draw(sheet)
    y = pad
    for r, rh in zip(rows, heights):
        for i, n in enumerate(r):
            im = big(tiles[n], k)
            x = pad + i * cw
            if n == "obj.tree":
                bg = Image.new("RGBA", im.size, (110, 150, 90, 255))
                bg.alpha_composite(im)
                im = bg
            sheet.alpha_composite(im, (x, y + lab))
            d.text((x, y), n, fill=(240, 240, 240), font=f)
        y += rh
    sheet.save(os.path.join(DOCS, "samples_sheet.png"))


def palettes():
    from ramps import REGIONS

    f = font(14)
    sw, rowh = 22, 30
    n = sum(len(v) for v in REGIONS.values())
    im = Image.new("RGBA", (520, 20 + n * rowh + len(REGIONS) * 26), (34, 36, 46, 255))
    d = ImageDraw.Draw(im)
    y = 10
    for region, mats in REGIONS.items():
        d.text((10, y), region, fill=(255, 230, 160), font=f)
        y += 24
        for mname, ramp in mats.items():
            d.text((30, y + 4), mname, fill=(230, 230, 230), font=f)
            for i, c in enumerate(ramp):
                d.rectangle((110 + i * sw, y, 110 + i * sw + sw - 2, y + sw), fill=c)
            d.text((110 + 5 * sw + 10, y + 4), " ".join(ramp), fill=(160, 160, 170), font=font(11))
            y += rowh
    im.save(os.path.join(DOCS, "palettes.png"))


def main():
    new = render("samples")
    new.save(os.path.join(DOCS, "mock_scene.png"))
    big(new, 3).save(os.path.join(DOCS, "mock_scene_3x.png"))
    old = render("placeholder")
    f = font(28)
    gap, lab = 24, 44
    cmp_ = Image.new("RGBA", (new.width * 4 + gap * 3, new.height * 2 + lab + gap), (34, 36, 46, 255))
    cmp_.alpha_composite(big(old, 2), (gap, lab))
    cmp_.alpha_composite(big(new, 2), (gap * 2 + new.width * 2, lab))
    d = ImageDraw.Draw(cmp_)
    d.text((gap, 8), "いま（仮の絵 docs/art-kit）", fill=(240, 240, 240), font=f)
    d.text((gap * 2 + new.width * 2, 8), "提案（本番品質サンプル）", fill=(255, 230, 160), font=f)
    cmp_.save(os.path.join(DOCS, "mock_compare.png"))
    # water animation (as the game plays it: 2 frames, 0.6 s each), on a 4x4 patch at 3x
    frames = []
    for fr in (0, 1):
        t = load(os.path.join(SAMPLES, f"tile.water.{fr}.png"))
        t = tinted(t, level_tint(0))
        p = Image.new("RGBA", (128, 128))
        for j in range(4):
            for i in range(4):
                p.paste(t, (i * 32, j * 32))
        frames.append(big(p, 3).convert("P", palette=Image.ADAPTIVE))
    frames[0].save(os.path.join(DOCS, "water_anim.gif"), save_all=True, append_images=frames[1:], duration=600, loop=0)
    samples_sheet()
    palettes()
    print("wrote mock_scene(.png, _3x), mock_compare, samples_sheet, water_anim.gif, palettes")


if __name__ == "__main__":
    main()
