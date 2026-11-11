"""v3 pilot: the hero at 2x detail (64 x 112, density 4), facing down: idle 4 + walk 6 frames.

Underdrawing: the approved v1 frames (src/art-release/hero/, read only). Method: v3lib.remaster()
then the hand finishing of finish.py (eyes, hair locks, trim glints, seams). The approved design,
proportions and timing stay the same; only the detail doubles (STYLE.md 5.2).
Writes src/art-release-v3/hero/hero.<idle|walk>.down.<n>.png
Run: python3 tools/art_v3/gen_hero_v3.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402,F401  (before the v1 tool folders: they hold an inspect.py)
from PIL import Image  # noqa: E402

import finish  # noqa: E402
from v3lib import ROOT, remaster, save  # noqa: E402

sys.path.append(os.path.join(ROOT, "tools", "hero_release"))
sys.path.append(os.path.join(ROOT, "tools", "art_proto"))
import gen_hero  # noqa: E402

SRC = os.path.join(ROOT, "src", "art-release", "hero")
OUT = os.path.join(ROOT, "src", "art-release-v3", "hero")
FRAMES = [("idle", 4), ("walk", 6)]
INKS = {"lash": gen_hero.EYE["lash"], "dark": gen_hero.EYE["iris_d"], "iris": gen_hero.EYE["iris"],
        "light": "#4ea2ec", "pupil": "#13285e", "shine": gen_hero.EYE["shine"]}


def frame(old):
    c = remaster(old, gen_hero.RAMPS)
    finish.eyes(c, old, INKS)
    hair = np.nonzero(c.mat == c.mid("hair"))
    crown = (hair[1].mean() + 1, hair[0].min() + 3)
    finish.hair_strands(c, "hair", crown=crown, n=26, width=0.12)
    finish.bang_tips(c, "hair", "skin")
    finish.glints(c, "gold", every=6)
    return c


def main():
    out = []
    for action, n in FRAMES:
        for i in range(n):
            name = f"hero.{action}.down.{i}.png"
            old = Image.open(os.path.join(SRC, name)).convert("RGBA")
            c = frame(old)
            out.append(save(c, os.path.join(OUT, name)))
    print("\n".join(os.path.relpath(p, ROOT) for p in out))


if __name__ == "__main__":
    main()
