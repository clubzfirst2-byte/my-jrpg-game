"""v3 villagers, round 4 (hand-drawn pixel maps): writes src/art-release-v3/npc/npc.<who>.<idle|walk>.<dir>.<n>.png
for the people made with npc_pixmap.py (here: guard, child, woman, smith; cook, elder, merchant and traveller are
made on another branch with the same tools). The other people's files are not touched.

Each frame is assembled from that person's hand-drawn part maps (npc_pm_<who>.py), placed by v1's own pose
table for that frame (tools/npc_release, read only). Keys, frame counts and anchor are v1's
(src/art-release/npc; fps in src/view/npcAnim.js). Left is stored (v1's left frames differ from the mirror
of the right: the held thing stays in its hand).

Checks before anything is written (a failure stops the run and writes nothing):
  edge         nothing but an outline on the top row / side columns
  stray        no piece of 40 texels or fewer apart from the figure
  translucent  no texel with 0 < alpha < 255
  same         no two frames of one person are the same picture
  mirror       no left frame that is only the mirror of its right frame
  eyes         no eye ink (lash, iris, shine) drawn by any part but the head; iris blobs: front 2, side 1,
               back 0, eyes shut 0
Run: python3 tools/art_v3/gen_npc_v3_pm.py [who ...]
"""

import hashlib
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "npc_release"))
sys.path.insert(0, os.path.join(HERE, "..", "art_proto"))
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from npc_pixmap import eye_inks_outside, iris_blobs, translucent  # noqa: E402
from v3lib import ROOT, edge_cuts, stray_pieces  # noqa: E402

OUT = os.path.join(ROOT, "src", "art-release-v3", "npc")
WHO = ("guard", "child", "woman", "smith")
FRAMES = {"idle": 4, "walk": 6}
VIEWS = ("down", "right", "up", "left")
NO_LEFT = ("princess", "smith")  # no left files: the game draws their right mirrored (decision 2026-11-12)


def build(who):
    M = importlib.import_module("npc_pm_" + who)
    v1 = importlib.import_module(who).NPC
    out, bad, seen, right = [], [], {}, {}
    for action, n in FRAMES.items():
        for view in VIEWS:
            if view == "left" and who in NO_LEFT:
                continue
            for i in range(n):
                name = f"npc.{who}.{action}.{view}.{i}"
                fig, mirrored = M.frame(v1, action, view, i)
                a = fig.rgba()
                if mirrored:
                    a = a[:, ::-1].copy()
                if edge_cuts(fig.c):
                    bad.append((name, "edge", edge_cuts(fig.c)))
                st = stray_pieces(fig.c)
                if st:
                    bad.append((name, "stray", st))
                if translucent(a):
                    bad.append((name, "translucent", translucent(a)))
                h = hashlib.md5(a.tobytes()).hexdigest()
                if h in seen:
                    bad.append((name, "same picture as", seen[h]))
                seen[h] = name
                if view == "right":
                    right[(action, i)] = a
                if view == "left" and np.array_equal(a, right[(action, i)][:, ::-1]):
                    bad.append((name, "left is only the mirror of right"))
                n_out = eye_inks_outside(fig, M.EYE_INKS, ("head",))
                if n_out:
                    bad.append((name, "eye ink off the head", n_out))
                blink = v1.pose(action, i).blink
                want = 0 if (view == "up" or blink) else (2 if view == "down" else 1)
                got = iris_blobs(fig, M.IRIS_INKS)
                if got != want:
                    bad.append((name, "iris blobs", got, "want", want))
                out.append((name, a, fig))
    return out, bad


def head_stability(frames):
    """For every pair of frames of one view where the head is drawn from the same map (no blink), the share
    of head texels that differ after the head's own move: the most over all pairs (reference value)."""
    by_view = {}
    for name, a, fig in frames:
        _, who, action, view, i = name.split(".")
        by_view.setdefault(view, []).append((name, a, fig))
    worst = 0.0
    for view, fs in by_view.items():
        heads = []
        for name, a, fig in fs:
            m = fig.part == "head"
            if view == "left":
                m = m[:, ::-1]
            ys, xs = np.nonzero(m)
            if not len(ys):
                continue
            heads.append((name, a, m, ys.min()))
        for j in range(len(heads)):
            for k in range(j + 1, len(heads)):
                n1, a1, m1, t1 = heads[j]
                n2, a2, m2, t2 = heads[k]
                dy = t2 - t1
                ys, xs = np.nonzero(m1)
                ok = (ys + dy >= 0) & (ys + dy < a1.shape[0])
                ys, xs = ys[ok], xs[ok]
                same_map = m2[ys + dy, xs]
                if same_map.mean() < 0.97:
                    continue
                diff = np.any(a1[ys, xs] != a2[ys + dy, xs], axis=-1)
                b1 = "blink" if (n1.endswith("idle." + view + ".3")) else ""
                b2 = "blink" if (n2.endswith("idle." + view + ".3")) else ""
                if b1 or b2:
                    continue
                worst = max(worst, float(diff.mean()))
    return worst


def main(people=WHO):
    todo, bad = [], []
    for who in people:
        fr, b = build(who)
        bad += b
        todo.append((who, fr))
    if bad:
        print("check failed, nothing written:", bad)
        sys.exit(1)
    for who, fr in todo:
        for name, a, fig in fr:
            Image.fromarray(a, "RGBA").save(os.path.join(OUT, name + ".png"), optimize=True)
        print(f"{who}: {len(fr)} files; head texels changed between frames (no blink), most: "
              f"{100 * head_stability(fr):.2f}%")
    print("checks: edge, stray, translucent, same picture, mirror-only left, eye inks off the head, iris blobs")


if __name__ == "__main__":
    main(tuple(sys.argv[1:]) or WHO)
