"""v3 production order 8: the bosses at density 4. 朽ち根のヌシ (boss_root), 凍て角のヌシ (boss_frost).

Keys, actions, frame counts and fps are v2's (src/art-release-v2/enemy/frames.json at d900394); every
frame is twice the v2 size (the same game size), the anchor is the same (feet = bottom centre), the
boss is seen from the front. Every part is a hand-drawn pixel map (tools/art_v3/boss_v3/); a frame
places the parts, nothing is scaled up from v2 and nothing is shaded by a formula.
Writes src/art-release-v3/boss/enemy.boss_<kind>.*.png and src/art-release-v3/boss/frames.json.
The other v3 groups (src/art-release-v3/enemy, ...) are not touched.
Run: python3 tools/art_v3/gen_boss_v3.py
"""

import json
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "boss_v3"))
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

import boss_frost  # noqa: E402
import boss_root  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "src", "art-release-v3", "boss")
KINDS = [("boss_root", boss_root), ("boss_frost", boss_frost)]
V2_SIZES = {"boss_root": (96, 80), "boss_frost": (96, 88)}
FPS = {"idle": 180, "idle2": 180, "move": 90, "windup": "split the wind-up time evenly", "attack": 80, "hurt": 90,
       "stagger": 120, "defeat": 140}


def build():
    out = {}
    for kind, mod in KINDS:
        for key, fr in mod.frames().items():
            out[f"enemy.{kind}.{key}"] = fr.rgba()
        out[f"enemy.{kind}.0"] = out[f"enemy.{kind}.idle.0"]
        out[f"enemy.{kind}.1"] = out[f"enemy.{kind}.move.0"]
    return out


def manifest(imgs):
    kinds = {}
    for kind, mod in KINDS:
        acts = {}
        for action, n in mod.ACTIONS:
            a = imgs[f"enemy.{kind}.{action}.0"]
            assert all(f"enemy.{kind}.{action}.{i}" in imgs for i in range(n)), (kind, action)
            acts[action] = {"frames": n, "size": [a.shape[1], a.shape[0]]}
        kinds[kind] = {"facing": "front", "actions": acts}
    return {
        "version": 3,
        "density": 4,
        "note": "v3 bosses (gen_boss_v3.py). Same kinds, actions, frame counts and fps as v2 "
                "(src/art-release-v2/enemy/frames.json); every size is 2x v2 (the same game size).",
        "minimal": {f"enemy.{k}.{i}": f"enemy.{k}.{v}" for k, _ in KINDS for i, v in enumerate(("idle.0", "move.0"))},
        "kinds": kinds,
        "anchor": "feet = bottom centre",
        "fps_hint_ms": FPS,
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    imgs = build()
    for name, a in sorted(imgs.items()):
        kind = name.split(".")[1]
        v2 = V2_SIZES[kind]
        assert (a.shape[1], a.shape[0]) == (2 * v2[0], 2 * v2[1]), name
        Image.fromarray(a, "RGBA").save(os.path.join(OUT, f"{name}.png"), optimize=True)
    with open(os.path.join(OUT, "frames.json"), "w", encoding="utf-8") as fp:
        json.dump(manifest(imgs), fp, ensure_ascii=False, indent=1)
        fp.write("\n")
    print(f"{len(imgs)} frames, frames.json -> {OUT}")


if __name__ == "__main__":
    main()
