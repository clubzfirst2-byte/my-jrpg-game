"""Review images for ground v2 (docs/art-release-v2/terrain/review/):
  fields_<season>.png            every ground as a large field (10 x 7 tiles: variants + macro pieces), 2x
  map_<excerpt>.png              a real map excerpt: before (v1 terrain) | after (v2), 1x, with the hero
  map_<excerpt>_2.5x.png         the middle of the same, at 2.5x (the iPhone scale), before | after
  map_plains_path_<season>.png   the plains excerpt in autumn and winter (after only), 1x
  transitions_<group>.png        every overlay (14 masks x 2 variants) over a lower ground, 3x
  water.gif                      the lake shore excerpt, 4 frames (shallow / deep / foam), 1x -> 2x
"""

import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
from excerpts import EXCERPTS  # noqa: E402
from render_ref import render_v1, render_v2  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
V1 = os.path.join(ROOT, "src", "art-release", "terrain")
HERO = os.path.join(ROOT, "src", "art-release", "hero", "hero.idle.down.0.png")
BG = (28, 30, 38, 255)


def load_v1():
    out = {}
    for f in os.listdir(V1):
        if f.endswith(".png"):
            out[f[:-4]] = Image.open(os.path.join(V1, f)).convert("RGBA")
    return out


def with_hero(im):
    hero = Image.open(HERO).convert("RGBA")
    im = im.copy()
    im.alpha_composite(hero, (im.width // 2 - 16, im.height // 2 - 28))
    return im


def label(im, text):
    out = Image.new("RGBA", (im.width, im.height + 14), BG)
    out.paste(im, (0, 14))
    ImageDraw.Draw(out).text((2, 1), text, fill=(235, 235, 235, 255))
    return out


def side(a, b, gap=12):
    out = Image.new("RGBA", (a.width + b.width + gap, max(a.height, b.height)), BG)
    out.paste(a, (0, 0))
    out.paste(b, (a.width + gap, 0))
    return out


def stack(ims, gap=10):
    out = Image.new("RGBA", (max(i.width for i in ims), sum(i.height + gap for i in ims)), BG)
    y = 0
    for i in ims:
        out.paste(i, (0, y))
        y += i.height + gap
    return out


def scale(im, k):
    return im.resize((round(im.width * k), round(im.height * k)), Image.NEAREST)


def reviews(images, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    v1 = load_v1()
    imgs = dict(images)
    for k in ("tile.metal", "tile.walltop", "tile.wood", "tile.dark", "tile.pit"):
        imgs["v1:" + k] = v1[k]
    # fields
    for season, chars in ((None, "gplmnsd=u"), ("autumn", "gplm"), ("winter", "gplm")):
        rows = []
        for ch in chars:
            grid = [ch * 11 for _ in range(8)]
            rows.append(label(render_v2(grid, imgs, season=season), f"{season or 'summer'} {ch}"))
        pairs = [side(rows[k], rows[k + 1]) if k + 1 < len(rows) else rows[k] for k in range(0, len(rows), 2)]
        scale(stack(pairs), 2).save(os.path.join(out_dir, f"fields_{season or 'summer'}.png"))
    # map excerpts
    for name, (x0, y0, grid) in EXCERPTS.items():
        before = with_hero(render_v1(grid, v1))
        after = with_hero(render_v2(grid, imgs))
        side(label(before, f"before (v1) {name} @{x0},{y0}"), label(after, "after (v2)")).save(os.path.join(out_dir, f"map_{name}.png"))
        cw, ch = 12 * 32, 7 * 32  # the middle at 2.5x
        box = ((before.width - cw) // 2, (before.height - ch) // 2, (before.width + cw) // 2, (before.height + ch) // 2)
        side(scale(before.crop(box), 2.5), scale(after.crop(box), 2.5), gap=20).save(os.path.join(out_dir, f"map_{name}_2.5x.png"))
    _, _, grid = EXCERPTS["plains_path"]
    for season in ("autumn", "winter"):
        with_hero(render_v2(grid, imgs, season=season)).save(os.path.join(out_dir, f"map_plains_path_{season}.png"))
    # transitions sheets: each overlay over a lower ground
    groups = [("grass_family", [("grass", "path"), ("plains", "sand"), ("lake", "ruin"), ("moss", "path")]),
              ("others", [("snow", "ruin"), ("sand", "path"), ("dsand", "path"), ("path", "ruin"), ("ruin", None)]),
              ("seasons", [("autumn.grass", "path"), ("autumn.lake", "sand"), ("autumn.moss", "path"), ("winter.plains", "path")])]
    for gname, pairs in groups:
        rows = []
        for top, under in pairs:
            season, t = (top.split(".") if "." in top else (None, top))
            pre = f"{season}.g2.{t}" if season else f"g2.{t}"
            row = Image.new("RGBA", (15 * 34, 2 * 34), BG)
            for v in (0, 1):
                for m in range(1, 16):
                    x, y = (m - 1) * 34, v * 34
                    base = imgs[f"g2.{under}.0"] if under else imgs["g2.water.shallow.0.0"]
                    row.paste(base, (x, y))
                    if not under and m < 15:
                        row.alpha_composite(imgs[f"g2.water.foam.e{m}.0"], (x, y))
                    row.alpha_composite(imgs[f"{pre}.0"] if m == 15 else imgs[f"{pre}.e{m}.{v}"], (x, y))
            rows.append(label(row, f"{top} over {under or 'water + foam'}  (masks 1-14, full; variants .0 / .1)"))
        scale(stack(rows), 3).save(os.path.join(out_dir, f"transitions_{gname}.png"))
    # water animation
    _, _, grid = EXCERPTS["lake_shore"]
    frames = [scale(render_v2(grid, imgs, frame=f), 2).convert("P", palette=Image.ADAPTIVE) for f in range(4)]
    frames[0].save(os.path.join(out_dir, "water.gif"), save_all=True, append_images=frames[1:], duration=250, loop=0)
