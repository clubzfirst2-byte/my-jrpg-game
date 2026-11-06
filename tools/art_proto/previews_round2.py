"""Preview images for the P12 round 2 NPC prototypes (needs Pillow and a Japanese font).

  docs/characters/round2/all_frames.png        every frame of the 6 NPCs, with names
  docs/characters/round2/<name>_x6.png         each NPC enlarged (4 directions x 3 frames)
  docs/characters/round2/walk.gif              the walk as the game plays it (1,0,2,0 at 8 fps)
Run after gen_round2.py: python3 tools/art_proto/previews_round2.py
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
from gen_round2 import NPCS  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
SRC = os.path.join(ROOT, "src", "art-proto", "npc")
OUT = os.path.join(ROOT, "docs", "characters", "round2")
DIRS = ("down", "up", "right", "left")
DIR_JA = {"down": "下", "up": "上", "right": "右", "left": "左"}
GRASS = (79, 138, 62)
INK = (240, 240, 240)
BG = (34, 36, 46)


def font(size):
    for p in ("/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf", "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def frame(look, d, f):
    return Image.open(os.path.join(SRC, f"npc.{look}.walk.{d}.{f}.png")).convert("RGBA")


def tile(img, scale):
    bg = Image.new("RGBA", img.size, GRASS + (255,))
    bg.alpha_composite(img)
    return bg.resize((img.width * scale, img.height * scale), Image.NEAREST)


def all_frames(scale=3):
    f_name = font(22)
    label_w = 150
    cw, ch = 32 * scale + 6, 56 * scale + 6
    img = Image.new("RGB", (label_w + cw * 12 + 6, 34 + ch * len(NPCS) + 6), BG)
    g = ImageDraw.Draw(img)
    for i, d in enumerate(DIRS):
        g.text((label_w + i * cw * 3 + 6, 6), f"{DIR_JA[d]}向き  コマ0（待機）・1・2", fill=INK, font=font(16))
    for r, (look, key, ja, _) in enumerate(NPCS):
        y = 34 + r * ch
        g.text((8, y + ch // 2 - 24), ja, fill=INK, font=f_name)
        g.text((8, y + ch // 2 + 4), f"look {look}", fill=(170, 170, 180), font=font(14))
        for i, d in enumerate(DIRS):
            for fr in range(3):
                img.paste(tile(frame(look, d, fr), scale), (label_w + (i * 3 + fr) * cw, y))
    img.save(os.path.join(OUT, "all_frames.png"))


def enlarged(scale=6):
    for look, key, ja, _ in NPCS:
        cw, ch = 32 * scale + 8, 56 * scale + 8
        img = Image.new("RGB", (cw * 3 + 8, 44 + (ch + 28) * 4), BG)
        g = ImageDraw.Draw(img)
        g.text((10, 8), f"{ja}（look {look}）  32×56 × 12 コマ・仮素材", fill=INK, font=font(24))
        for i, d in enumerate(DIRS):
            y = 44 + i * (ch + 28)
            g.text((10, y), f"{DIR_JA[d]}向き", fill=(200, 200, 210), font=font(18))
            for fr in range(3):
                img.paste(tile(frame(look, d, fr), scale), (8 + fr * cw, y + 26))
        img.save(os.path.join(OUT, f"{key}_x6.png"))


def walk_gif(scale=3):
    cycle = (1, 0, 2, 0)
    cw, ch = 32 * scale + 8, 56 * scale + 8
    label_w = 130
    frames = []
    for k in range(8):
        img = Image.new("RGB", (label_w + cw * 4, 30 + ch * len(NPCS)), BG)
        g = ImageDraw.Draw(img)
        for i, d in enumerate(DIRS):
            g.text((label_w + i * cw + 6, 6), f"{DIR_JA[d]}", fill=INK, font=font(16))
        for r, (look, key, ja, _) in enumerate(NPCS):
            y = 30 + r * ch
            g.text((8, y + ch // 2 - 12), ja, fill=INK, font=font(20))
            for i, d in enumerate(DIRS):
                img.paste(tile(frame(look, d, cycle[k % 4]), scale), (label_w + i * cw, y))
        frames.append(img)
    frames[0].save(os.path.join(OUT, "walk.gif"), save_all=True, append_images=frames[1:], duration=125, loop=0)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    all_frames()
    enlarged()
    walk_gif()
    print("previews -> docs/characters/round2/")
