"""Preview images for the P12 round 3 enemy prototypes (needs Pillow and a Japanese font).

  docs/characters/round3/all_frames.png    every frame of the 4 enemies, with names and sizes
  docs/characters/round3/<key>_x6.png      each enemy enlarged 6x (frames 0 and 1)
  docs/characters/round3/anim.gif          the 2 frames alternating, all 4 side by side
  docs/characters/round3/compare.png       the 4 together at the same scale, with the hero and the
                                           round-1 beast and goblin for size
Run after gen_round3.py: python3 tools/art_proto/previews_round3.py
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
from gen_round3 import ENEMIES  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
PROTO = os.path.join(ROOT, "src", "art-proto")
OUT = os.path.join(ROOT, "docs", "characters", "round3")
GRASS = (79, 138, 62)
BG = (34, 36, 46)
INK = (240, 240, 240)


def font(size):
    for p in ("/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf", "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def img(group, name):
    return Image.open(os.path.join(PROTO, group, f"{name}.png")).convert("RGBA")


def on_grass(im, scale, pad=0):
    bg = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), GRASS + (255,))
    bg.alpha_composite(im, (pad, pad))
    return bg.resize((bg.width * scale, bg.height * scale), Image.NEAREST)


def all_frames(scale=4):
    tiles = [(ja, size, [on_grass(img("enemy", f"enemy.{k}.{f}"), scale, 2) for f in (0, 1)]) for k, ja, size, _ in ENEMIES]
    W = 24 + sum(max(t[0].width, 160) * 2 + 24 for *_, t in tiles)
    H = 60 + max(t[0].height for *_, t in tiles) + 40
    out = Image.new("RGB", (W, H), BG)
    g = ImageDraw.Draw(out)
    x = 12
    for ja, (w, h), (a, b) in tiles:
        g.text((x, 10), ja, fill=INK, font=font(22))
        g.text((x, 36), f"{w}×{h} ドット × 2 コマ（コマ0・コマ1）", fill=(190, 190, 200), font=font(15))
        out.paste(a, (x, 60 + max(t[0].height for *_, t in tiles) - a.height))
        out.paste(b, (x + a.width + 8, 60 + max(t[0].height for *_, t in tiles) - b.height))
        x += max(a.width, 160) * 2 + 24
    out.save(os.path.join(OUT, "all_frames.png"))


def enlarged(scale=6):
    for k, ja, (w, h), _ in ENEMIES:
        a, b = (on_grass(img("enemy", f"enemy.{k}.{f}"), scale, 1) for f in (0, 1))
        out = Image.new("RGB", (a.width * 2 + 36, a.height + 90), BG)
        g = ImageDraw.Draw(out)
        g.text((12, 10), f"{ja}  {w}×{h}・仮素材（6 倍）", fill=INK, font=font(24))
        out.paste(a, (12, 76))
        out.paste(b, (24 + a.width, 76))
        g.text((12, 48), "コマ0（待機）", fill=(190, 190, 200), font=font(18))
        g.text((24 + a.width, 48), "コマ1（移動）", fill=(190, 190, 200), font=font(18))
        out.save(os.path.join(OUT, f"{k}_x6.png"))


def anim(scale=4):
    frames = []
    hmax = max(h for _, _, (w, h), _ in ENEMIES)
    for f in (0, 1):
        x = 12
        out = Image.new("RGB", (sum((w + 4) * scale + 30 for _, _, (w, h), _ in ENEMIES) + 12, (hmax + 4) * scale + 50), BG)
        g = ImageDraw.Draw(out)
        for k, ja, (w, h), _ in ENEMIES:
            t = on_grass(img("enemy", f"enemy.{k}.{f}"), scale, 2)
            g.text((x, 8), ja.split("（")[0], fill=INK, font=font(18))
            out.paste(t, (x, out.height - t.height - 6))
            x += t.width + 30
        frames.append(out)
    frames[0].save(os.path.join(OUT, "anim.gif"), save_all=True, append_images=frames[1:], duration=330, loop=0)


def compare(scale=4):
    """Everyone at the same scale on one ground line (the art standard: 2 art px per game px)."""
    cast = [("主人公 v2", img("hero", "player.walk.down.0")), ("獣（第1回）", img("enemy", "enemy.beast.0")), ("ゴブリン（第1回）", img("enemy", "enemy.archer.0"))]
    cast += [(ja.split("（")[0], img("enemy", f"enemy.{k}.0")) for k, ja, _, _ in ENEMIES]
    gap = 10
    W = sum(im.width + gap for _, im in cast) + gap
    H = max(im.height for _, im in cast) + 8
    ground = Image.new("RGBA", (W, H), GRASS + (255,))
    x = gap
    for _, im in cast:
        ground.alpha_composite(im, (x, H - 4 - im.height))
        x += im.width + gap
    ground = ground.resize((W * scale, H * scale), Image.NEAREST)
    out = Image.new("RGB", (ground.width, ground.height + 70), BG)
    g = ImageDraw.Draw(out)
    g.text((10, 8), "同じ縮尺で比較（絵 2 ドット＝ゲーム内 1 ドット。地面 1 マス＝絵 32 ドット）", fill=INK, font=font(18))
    x = gap * scale
    for name, im in cast:
        g.text((x, 40), name, fill=(200, 200, 210), font=font(15))
        x += (im.width + gap) * scale
    out.paste(ground, (0, 70))
    out.save(os.path.join(OUT, "compare.png"))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    all_frames()
    enlarged()
    anim()
    compare()
    print("previews -> docs/characters/round3/")
