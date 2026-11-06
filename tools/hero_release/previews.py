"""Preview images for the hero's release art (needs Pillow and a Japanese font).

  docs/hero/release/frames.png      every frame, by action and direction, with labels
  docs/hero/release/anim.gif        idle / walk / run playing as in the game, in 4 directions
  docs/hero/release/compare_v2.png  approved v2 (prototype) next to the release frames
Run after gen_hero.py: python3 tools/hero_release/previews.py
"""

import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
REL = os.path.join(ROOT, "src", "art-release", "hero")
PROTO = os.path.join(ROOT, "src", "art-proto", "hero")
OUT = os.path.join(ROOT, "docs", "hero", "release")
GRASS, BG, INK = (79, 138, 62), (34, 36, 46), (240, 240, 240)
DIRS = ("down", "up", "right", "left")
DJ = {"down": "下", "up": "上", "right": "右", "left": "左"}
ACTIONS = (("idle", "待機", 4), ("walk", "歩行", 6), ("run", "走行", 6))


def font(n):
    for p in ("/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf", "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, n)
    return ImageFont.load_default()


def tile(path, scale):
    im = Image.open(path).convert("RGBA")
    bg = Image.new("RGBA", im.size, GRASS + (255,))
    bg.alpha_composite(im)
    return bg.resize((im.width * scale, im.height * scale), Image.NEAREST)


def frames(scale=4):
    cw, ch = 32 * scale + 6, 56 * scale + 6
    rows = [(a, ja, n, d) for a, ja, n in ACTIONS for d in DIRS]
    out = Image.new("RGB", (150 + cw * 6, 10 + ch * len(rows)), BG)
    g = ImageDraw.Draw(out)
    for r, (a, ja, n, d) in enumerate(rows):
        y = 10 + r * ch
        g.text((10, y + ch // 2 - 20), f"{ja}（{n} コマ）", fill=INK, font=font(20))
        g.text((10, y + ch // 2 + 6), f"{DJ[d]}向き", fill=(180, 180, 190), font=font(16))
        for i in range(n):
            out.paste(tile(os.path.join(REL, f"hero.{a}.{d}.{i}.png"), scale), (150 + i * cw, y))
    out.save(os.path.join(OUT, "frames.png"))


def anim(scale=4):
    """24 frames at the game's speeds: idle 4/s, walk 10/s, run ~14/s (shown at 12 per second)."""
    cw, ch = 32 * scale + 8, 56 * scale + 8
    frames_out = []
    for k in range(24):
        out = Image.new("RGB", (110 + cw * 4, 30 + ch * 3), BG)
        g = ImageDraw.Draw(out)
        for i, d in enumerate(DIRS):
            g.text((110 + i * cw + 8, 6), DJ[d], fill=INK, font=font(16))
        for r, (a, ja, n) in enumerate(ACTIONS):
            rate = {"idle": 4, "walk": 10, "run": 14}[a] / 12
            f = int(k * rate) % n
            g.text((10, 30 + r * ch + ch // 2 - 10), ja, fill=INK, font=font(20))
            for i, d in enumerate(DIRS):
                out.paste(tile(os.path.join(REL, f"hero.{a}.{d}.{f}.png"), scale), (110 + i * cw, 30 + r * ch))
        frames_out.append(out)
    frames_out[0].save(os.path.join(OUT, "anim.gif"), save_all=True, append_images=frames_out[1:], duration=83, loop=0)


def compare(scale=5):
    pairs = [("v2（仮素材）歩行", [os.path.join(PROTO, f"player.walk.{d}.{i}.png") for d in ("down", "right") for i in (1, 0, 2)]),
             ("製品版候補 歩行", [os.path.join(REL, f"hero.walk.{d}.{i}.png") for d in ("down", "right") for i in (0, 2, 4)]),
             ("製品版候補 走行", [os.path.join(REL, f"hero.run.{d}.{i}.png") for d in ("down", "right") for i in (0, 2, 4)])]
    cw, ch = 32 * scale + 8, 56 * scale + 8
    out = Image.new("RGB", (200 + cw * 6, 10 + ch * 3), BG)
    g = ImageDraw.Draw(out)
    for r, (label, paths) in enumerate(pairs):
        g.text((10, 10 + r * ch + ch // 2 - 10), label, fill=INK, font=font(20))
        for i, p in enumerate(paths):
            out.paste(tile(p, scale), (200 + i * cw, 10 + r * ch))
    out.save(os.path.join(OUT, "compare_v2.png"))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    frames()
    anim()
    compare()
    print("previews -> docs/hero/release/")
