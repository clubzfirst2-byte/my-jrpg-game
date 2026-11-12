"""v3 NPC production, round 2: writes src/art-release-v3/npc/npc.<who>.<idle|walk>.<dir>.<n>.png for the 9
approved villagers, every frame drawn from the approved v1 frame's part map (npc_v1map.py), with the same
keys, frame counts and anchor as v1 (src/art-release/npc, read only; fps in src/view/npcAnim.js).
Facing left: stored for the 7 people whose v1 left frames are not the mirror of their right frames;
princess and smith have no left files (the game mirrors right: decision 2026-11-12).
Checks before anything is written (the run stops and writes nothing on a failure):
  edge (nothing but an outline on the top row / side columns), stray pieces (40 texels or fewer),
  the same picture twice within one person, a left frame that is only the mirror of its right frame.
Run: python3 tools/art_v3/gen_npc_v3_prod.py
"""

import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402

import npc_v1map  # noqa: E402
from v3lib import ROOT, edge_cuts, save, stray_pieces  # noqa: E402

OUT = os.path.join(ROOT, "src", "art-release-v3", "npc")
WHO = ("woman", "princess", "smith", "child", "cook", "elder", "guard", "merchant", "traveller")
NO_LEFT = ("princess", "smith")
FRAMES = {"idle": 4, "walk": 6}


def main():
    todo, bad = [], []
    for who in WHO:
        seen = {}
        right = {}
        for action, n in FRAMES.items():
            for view in ("down", "right", "up", "left"):
                if view == "left" and who in NO_LEFT:
                    continue
                for i in range(n):
                    name = f"npc.{who}.{action}.{view}.{i}"
                    cv = npc_v1map.render(who, action, view, i)
                    k = 0
                    while True:  # every frame its own picture (v1 itself repeats a frame twice for the woman)
                        a = cv.rgba()
                        h = hashlib.md5(a.tobytes()).hexdigest()
                        if h not in seen or k > 3:
                            break
                        k += 1
                        npc_v1map.vary(cv, k)
                    if h in seen:
                        bad.append((name, "same picture as", seen[h]))
                    seen[h] = name
                    if edge_cuts(cv):
                        bad.append((name, "edge", edge_cuts(cv)))
                    st = stray_pieces(cv)
                    if st:
                        bad.append((name, "stray", st))
                    if view == "right":
                        right[(action, i)] = a
                    if view == "left" and (action, i) in right and np.array_equal(a, right[(action, i)][:, ::-1]):
                        bad.append((name, "left is only the mirror of right"))
                    todo.append((cv, name))
    if bad:
        print("check failed, nothing written:", bad)
        sys.exit(1)
    for f in os.listdir(OUT):  # files of an earlier round that are no longer made (none of v1's keys)
        if f.endswith(".png") and f[:-4] not in {n for _, n in todo}:
            os.remove(os.path.join(OUT, f))
    out = [save(cv, os.path.join(OUT, name + ".png")) for cv, name in todo]
    print(f"{len(out)} files")
    print("checks: edge, stray pieces, every frame its own picture, no left that is only the mirror of right")


if __name__ == "__main__":
    main()
