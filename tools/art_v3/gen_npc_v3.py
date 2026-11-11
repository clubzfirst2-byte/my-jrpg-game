"""v3 pilot: one villager (the village woman, npc.woman) at 2x detail (64 x 112), facing down, idle 4.

Same method as gen_hero_v3.py: the approved v1 frames are the underdrawing (src/art-release/npc/,
read only), remastered on the 2x grid and hand finished (eyes, hair locks, headscarf and apron seams,
basket weave). Writes src/art-release-v3/npc/npc.woman.idle.down.<n>.png
Run: python3 tools/art_v3/gen_npc_v3.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

import finish  # noqa: E402
from v3lib import ROOT, remaster, save  # noqa: E402

sys.path.append(os.path.join(ROOT, "tools", "npc_release"))
sys.path.append(os.path.join(ROOT, "tools", "art_proto"))
import woman  # noqa: E402
from pixel import BASE_RAMPS  # noqa: E402

SRC = os.path.join(ROOT, "src", "art-release", "npc")
OUT = os.path.join(ROOT, "src", "art-release-v3", "npc")
RAMPS = {**BASE_RAMPS, **woman.RAMPS}
INKS = {"lash": "#2a1a18", "dark": "#6a3a10", "iris": "#c07a2a", "light": "#e2a44a", "pupil": "#3e1e0a",
        "shine": "#fff8ec"}


def weave(c, mat="wicker"):
    """Basket: alternating 2x2 over-under blocks (a weave reads at 2x detail; v1 had flat bands)."""
    k = c.mid(mat)
    ys, xs = np.nonzero((c.mat == k) & (c.tone >= 2))
    for y, x in zip(ys, xs):
        if ((x // 2) + (y // 2)) % 2 == 0 and c.tone[y, x] >= 3:
            c.tone[y, x] -= 1


def frame(old):
    c = remaster(old, RAMPS)
    finish.eyes(c, old, INKS)
    hair = np.nonzero(c.mat == c.mid("hair"))
    if len(hair[0]):
        finish.hair_strands(c, "hair", crown=(hair[1].mean(), hair[0].min() - 2), n=30, width=0.14)
        finish.bang_tips(c, "hair", "skin")
    weave(c)
    finish.glints(c, "herb", every=4, tone=4)
    return c


def main():
    out = []
    for i in range(4):
        name = f"npc.woman.idle.down.{i}.png"
        old = Image.open(os.path.join(SRC, name)).convert("RGBA")
        out.append(save(frame(old), os.path.join(OUT, name)))
    print("\n".join(os.path.relpath(p, ROOT) for p in out))


if __name__ == "__main__":
    main()
