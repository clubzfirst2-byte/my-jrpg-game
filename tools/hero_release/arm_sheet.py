"""The four basic arm poses (stage 4), in each view, on the standing hero.

  docs/hero/release/arm_poses.png
Run after gen_hero.py: python3 tools/hero_release/arm_sheet.py
"""

import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "art_proto"))
sys.path.insert(0, os.path.dirname(__file__))
import actions  # noqa: E402
import gen_hero as g  # noqa: E402
from previews import BG, GRASS, INK, font  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "hero", "release", "arm_poses.png")
# hand positions that pick each basic pose (both arms the same way)
HANDS = {
    "down": {"down": {"R": (9, 37), "L": (22, 37)}, "forward": {"R": (12, 34), "L": (19, 34)},
             "up": {"R": (3, 19), "L": (28, 19)}, "out": {"R": (0, 30), "L": (31, 30)}},
    "up": {"down": {"R": (22, 37), "L": (9, 37)}, "forward": {"R": (19, 34), "L": (12, 34)},
           "up": {"R": (28, 19), "L": (3, 19)}, "out": {"R": (31, 30), "L": (0, 30)}},
    "side": {"down": {"R": (17, 35), "L": (15, 35)}, "forward": {"R": (24, 32), "L": (22, 32)},
             "up": {"R": (25, 19), "L": (23, 19)}, "back": {"R": (12, 34), "L": (11, 34)}},
}
LABEL = {"down": "下ろす", "forward": "前に出す", "up": "上げる", "out": "横に広げる", "back": "後ろへ振る"}
VIEW = {"down": "正面", "up": "背面", "side": "横"}


def frame(view, pose):
    p = g.Pose(hands=HANDS[view][pose], width=48)
    c = g.side(p) if view == "side" else g.front(p, back=view == "up")
    img = actions.finish(c, p, view).colours()
    im = Image.new("RGBA", (len(img[0]), len(img)))
    im.putdata([px if px else (0, 0, 0, 0) for row in img for px in row])
    return im


def main(scale=5):
    cw, ch = 48 * scale + 10, 56 * scale + 40
    out = Image.new("RGB", (120 + cw * 4, 10 + ch * 3), BG)
    d = ImageDraw.Draw(out)
    for r, view in enumerate(("down", "up", "side")):
        d.text((10, 10 + r * ch + ch // 2 - 12), VIEW[view], fill=INK, font=font(24))
        for c, pose in enumerate(HANDS[view]):
            im = frame(view, pose)
            bg = Image.new("RGBA", im.size, GRASS + (255,))
            bg.alpha_composite(im)
            x, y = 120 + c * cw, 10 + r * ch
            d.text((x + 6, y), LABEL[pose], fill=INK, font=font(18))
            out.paste(bg.resize((im.width * scale, im.height * scale), Image.NEAREST), (x, y + 30))
    out.save(OUT)


if __name__ == "__main__":
    main()
