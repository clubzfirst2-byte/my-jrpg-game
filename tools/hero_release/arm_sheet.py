"""The basic arm poses (stage 4: four, stage 5: the added ones, marked ★), in each view, on the standing hero.

  docs/hero/release/arm_poses.png (and docs/hero/release/stage5/02_arm_poses.png)
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
# every basic pose of each view (stage 4: the first four; stage 5: grip, diag_up, diag_down, bent, across)
POSES = {
    "down": ["down", "forward", "up", "out", "grip", "diag_up", "diag_down"],
    "up": ["down", "forward", "up", "out", "grip", "diag_up", "diag_down", "across"],
    "side": ["down", "forward", "up", "back", "grip", "diag_up", "diag_down", "bent"],
}
LABEL = {"down": "下ろす", "forward": "前に出す", "up": "上げる", "out": "横に広げる", "back": "後ろへ振る",
         "grip": "握る（滑空）★", "diag_up": "斜め上 ★", "diag_down": "斜め下 ★", "bent": "肘を曲げる（走行）★",
         "across": "体の前を横切る ★"}
VIEW = {"down": "正面", "up": "背面", "side": "横"}


def frame(view, pose):
    # the sword-arm poses on his right arm only (the left one hanging), so the shape reads alone
    left = pose if pose in ("down", "forward", "up", "out", "back", "grip") else "down"
    arms = {"R": pose, "L": left}
    hands = {k: actions.hand_at(view, k, arms[k]) for k in ("R", "L")}
    p = g.Pose(hands=hands, arms=arms, width=48)
    c = g.side(p) if view == "side" else g.front(p, back=view == "up")
    img = actions.finish(c, p, view).colours()
    im = Image.new("RGBA", (len(img[0]), len(img)))
    im.putdata([px if px else (0, 0, 0, 0) for row in img for px in row])
    return im


def main(scale=5):
    cw, ch = 48 * scale + 10, 56 * scale + 40
    out = Image.new("RGB", (120 + cw * 8, 10 + ch * 3), BG)
    d = ImageDraw.Draw(out)
    for r, view in enumerate(("down", "up", "side")):
        d.text((10, 10 + r * ch + ch // 2 - 12), VIEW[view], fill=INK, font=font(24))
        for c, pose in enumerate(POSES[view]):
            im = frame(view, pose)
            bg = Image.new("RGBA", im.size, GRASS + (255,))
            bg.alpha_composite(im)
            x, y = 120 + c * cw, 10 + r * ch
            d.text((x + 6, y), LABEL[pose], fill=INK, font=font(18))
            out.paste(bg.resize((im.width * scale, im.height * scale), Image.NEAREST), (x, y + 30))
    out.save(OUT)
    os.makedirs(os.path.join(os.path.dirname(OUT), "stage5"), exist_ok=True)
    out.save(os.path.join(os.path.dirname(OUT), "stage5", "02_arm_poses.png"))


if __name__ == "__main__":
    main()
