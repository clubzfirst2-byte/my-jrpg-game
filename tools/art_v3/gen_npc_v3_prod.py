"""v3 NPC production (STYLE order 5): writes src/art-release-v3/npc/npc.<who>.<idle|walk>.<dir>.<n>.png
for every finished villager, with the same keys, frame counts and anchor as the approved v1 NPCs
(src/art-release/npc, read only; fps in src/view/npcAnim.js: idle 4 at 3 fps, walk 6 at 8 fps).
Facing left: drawn on its own when v1's left frames are not the mirror of its right frames.
Ends with the hero's checks: nothing but an outline on the top row / side columns, no stray piece.
Run: python3 tools/art_v3/gen_npc_v3_prod.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from PIL import Image  # noqa: E402

import npc_batch2  # noqa: E402
import npc_woman  # noqa: E402
from v3lib import ROOT, edge_cuts, save, stray_pieces  # noqa: E402

OUT = os.path.join(ROOT, "src", "art-release-v3", "npc")
WHO = {"woman": npc_woman}


def main():
    out, bad = [], []
    jobs = [(who, action, view, (lambda m=mod, a=action, v=view: m.frames(a, v)))
            for who, mod in WHO.items() for action in ("idle", "walk") for view in ("down", "right", "up", "left")]
    # princess and smith: no left files (the game mirrors their right frames, decision 2026-11-12)
    jobs += [(who, action, view, (lambda w=who, a=action, v=view: npc_batch2.frames(w, a, v)))
             for who in ("princess", "smith") for action in ("idle", "walk") for view in ("down", "right", "up")]
    for who, action, view, make in jobs:
        if True:
            for i, cv in enumerate(make()):
                    name = f"npc.{who}.{action}.{view}.{i}"
                    if edge_cuts(cv):
                        bad.append((name, "edge", edge_cuts(cv)))
                    st = stray_pieces(cv)
                    if st:
                        bad.append((name, "stray", st))
                    img = cv.image()
                    if view == "left":
                        img = img.transpose(Image.FLIP_LEFT_RIGHT)
                    out.append(save(img, os.path.join(OUT, name + ".png")))
    print(f"{len(out)} files")
    if bad:
        print("check failed:", bad)
        sys.exit(1)
    print("check: no frame cut by the edge, no stray piece of 40 texels or fewer")


if __name__ == "__main__":
    main()
