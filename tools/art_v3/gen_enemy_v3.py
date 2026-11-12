"""v3 production order 6: the normal enemies and their shots at density 4 (STYLE.md 5.4).

Keys, actions, frame counts and fps are v2's (docs/art-release-v2/enemy/frames.json at d900394);
every frame is twice the v2 size (the same game size), the anchor is the same (feet = bottom
centre, shots = centre), every enemy faces right (the game mirrors it).
  beast, archer, sentinel  the approved v2 rigs and key poses (tools/enemy_v2 at d900394, copied to
                           tools/art_v3/enemy_v3/), drawn again on the density-4 grid (rig.py)
  slime                    the passed v3 pilot's drawing, generalised to every action
                           (enemy_v3/slime_v3.py); idle 0-3 ARE the pilot files (checked, not rewritten)
  shot                     redrawn at 24 x 24 (enemy_v3/shots_v3.py)
The minimal pair enemy.beast.0 / .1 and enemy.archer.0 / .1 (= idle.0 / move.0) is written too.
Bosses: later (production order 8); the game keeps v2 for them.
Writes src/art-release-v3/enemy/enemy.*.png and src/art-release-v3/enemy/frames.json.
Run: python3 tools/art_v3/gen_enemy_v3.py
"""

import json
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "enemy_v3"))
sys.path.insert(1, HERE)
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

import archer  # noqa: E402
import palette_v3  # noqa: E402
import beast  # noqa: E402
import sentinel  # noqa: E402
import shots_v3  # noqa: E402
import slime_v3  # noqa: E402
from v3lib import ROOT  # noqa: E402

OUT = os.path.join(ROOT, "src", "art-release-v3", "enemy")
KINDS = [("beast", beast), ("archer", archer), ("slime", slime_v3), ("sentinel", sentinel), ("shot", shots_v3)]
ACTION_ORDER = ("idle", "move", "windup", "attack", "hurt", "defeat")
MINIMAL = ("beast", "archer")
V2_SIZES = {"beast": (44, 32), "archer": (32, 56), "slime": (32, 28), "sentinel": (40, 56), "shot": (12, 12)}


def rgba(fr):
    if hasattr(fr, "rgba"):  # a v3lib Canvas
        return fr.rgba()
    a = fr.image()
    return np.asarray(a, np.uint8)


def build():
    out = {}
    for kind, mod in KINDS:
        for key, fr in mod.frames().items():
            a = rgba(fr)
            if kind in ("beast", "archer", "sentinel"):
                a = palette_v3.recolour(a, kind)  # the body darkened against the ground, mid tones in 3x3
                if a[0, :, 3].any():  # keep the top row empty (v2's rule): drop that row's texels
                    a[0, :, 3] = 0
            out[f"enemy.{kind}.{key}"] = a
        if kind in MINIMAL:
            out[f"enemy.{kind}.0"] = out[f"enemy.{kind}.idle.0"]
            out[f"enemy.{kind}.1"] = out[f"enemy.{kind}.move.0"]
    return out


def manifest(imgs):
    kinds = {}
    for name, a in imgs.items():
        parts = name.split(".")
        if len(parts) == 3:
            continue
        kind, action, n = parts[1], ".".join(parts[2:-1]), int(parts[-1])
        k = kinds.setdefault(kind, {"facing": "right", "actions": {}})
        act = k["actions"].setdefault(action, {"frames": 0, "size": [a.shape[1], a.shape[0]]})
        act["frames"] = max(act["frames"], n + 1)
    for kind, k in kinds.items():
        order = [a for a, _ in shots_v3.ACTIONS] if kind == "shot" else list(ACTION_ORDER)
        k["actions"] = {a: k["actions"][a] for a in order if a in k["actions"]}
    return {
        "version": 3,
        "density": 4,
        "note": "v3 normal enemies and shots (gen_enemy_v3.py). Same kinds, actions, frame counts and fps as v2 "
                "(src/art-release-v2/enemy/frames.json); every size is 2x v2 (the same game size). Bosses: v2.",
        "minimal": {f"enemy.{k}.{i}": f"enemy.{k}.{v}" for k in MINIMAL for i, v in enumerate(("idle.0", "move.0"))},
        "kinds": {k: kinds[k] for k, _ in KINDS if k in kinds},
        "anchor": "feet = bottom centre (shots: centre)",
        "fps_hint_ms": {"idle": 180, "move": 90, "windup": "split the wind-up time evenly", "attack": 80,
                        "hurt": 90, "defeat": 140, "shot": 90},
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    imgs = build()
    pilot_ok = True
    for name, a in sorted(imgs.items()):
        size = (a.shape[1], a.shape[0])
        kind = name.split(".")[1]
        v2 = V2_SIZES[kind]
        assert size == (2 * v2[0], 2 * v2[1]), (name, size)
        path = os.path.join(OUT, f"{name}.png")
        if name.startswith("enemy.slime.idle."):  # the passed pilot: never rewritten, must match
            same = np.array_equal(np.array(Image.open(path).convert("RGBA")), a)
            pilot_ok &= same
            continue
        Image.fromarray(a, "RGBA").save(path, optimize=True)
    print("slime idle 0-3 == the pilot files:", pilot_ok)
    with open(os.path.join(OUT, "frames.json"), "w", encoding="utf-8") as fp:
        json.dump(manifest(imgs), fp, ensure_ascii=False, indent=1)
        fp.write("\n")
    print(f"{len(imgs)} frames ({len(imgs) - 4} written, 4 pilot), frames.json")


if __name__ == "__main__":
    main()
