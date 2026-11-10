"""Enemies & bosses -- v2 art (graphics project W3): 4-8 frames per action, 8-step ramps, the
hero's outline rule. New folder: src/art-release-v2/enemy/ (the approved src/art-release/enemy is
untouched). Docs: docs/art-release-v2/enemy/PRODUCTION.md.

Same names, sizes and anchors as v1 (enemy.<kind>.<action>.<n>; feet = bottom centre, shots =
centre; every enemy faces right, bosses face the camera); only the frame counts change. The counts
are in src/art-release-v2/enemy/frames.json, which the engine reads (a copy is in the docs folder).
The minimal pair enemy.<kind>.0 / .1 (= idle.0 / move.0) is kept for the code that draws it today.

Run: python3 tools/enemy_v2/gen_enemy.py [kind ...]   (then previews.py for sheets, GIFs, compare)
"""

import json
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image  # noqa: E402

import archer  # noqa: E402
import beast  # noqa: E402
import boss_frost  # noqa: E402
import boss_root  # noqa: E402
import boss_sand  # noqa: E402
import boss_source  # noqa: E402
import boss_storm  # noqa: E402
import sentinel  # noqa: E402
import shots  # noqa: E402
import slime  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "src", "art-release-v2", "enemy")
DOC = os.path.join(ROOT, "docs", "art-release-v2", "enemy")

KINDS = [  # (kind, module, facing)
    ("beast", beast, "right"), ("archer", archer, "right"), ("slime", slime, "right"), ("sentinel", sentinel, "right"),
    ("boss_root", boss_root, "front"), ("boss_frost", boss_frost, "front"), ("boss_sand", boss_sand, "front"),
    ("boss_storm", boss_storm, "front"), ("boss_source", boss_source, "front"), ("shot", shots, "right"),
]
MINIMAL = ("beast", "archer", "boss_root", "boss_frost", "boss_sand", "boss_storm")


def to_image(rows):
    h, w = len(rows), len(rows[0])
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    for y in range(h):
        for x in range(w):
            if rows[y][x]:
                px[x, y] = rows[y][x]
    return im


def build(only=None):
    out = {}
    for kind, mod, _ in KINDS:
        if only and kind not in only:
            continue
        for key, rig in mod.frames().items():
            out[f"enemy.{kind}.{key}"] = to_image(rig.image(outline=kind != "shot"))
        if kind in MINIMAL:
            out[f"enemy.{kind}.0"] = out[f"enemy.{kind}.idle.0"]
            out[f"enemy.{kind}.1"] = out[f"enemy.{kind}.move.0"]
    return out


def manifest():
    """frames.json from the PNGs in the folder (so a partial run keeps the other kinds)."""
    kinds = {}
    facing = {k: f for k, _, f in KINDS}
    order = [k for k, _, _ in KINDS]
    for f in sorted(os.listdir(OUT)):
        if not f.endswith(".png"):
            continue
        parts = f[:-4].split(".")
        if len(parts) == 3:
            continue
        kind, action, n = parts[1], ".".join(parts[2:-1]), int(parts[-1])
        size = list(Image.open(os.path.join(OUT, f)).size)
        k = kinds.setdefault(kind, {"facing": facing[kind], "actions": {}})
        a = k["actions"].setdefault(action, {"frames": 0, "size": size})
        a["frames"] = max(a["frames"], n + 1)
    mods = dict((k, m) for k, m, _ in KINDS)
    for kind, k in kinds.items():  # actions in the order the character's module lists them
        frames = [a for a, _ in getattr(mods[kind], "ACTIONS", ())]
        if frames:
            k["actions"] = {a: k["actions"][a] for a in frames if a in k["actions"]}
    return {
        "version": 2,
        "minimal": {f"enemy.{k}.{i}": f"enemy.{k}.{v}" for k in MINIMAL if k in kinds for i, v in enumerate(("idle.0", "move.0"))},
        "kinds": {k: kinds[k] for k in order if k in kinds},
        "anchor": "feet = bottom centre (shots: centre)",
        "fps_hint_ms": {"idle": 180, "idle2": 180, "move": 90, "windup": "split the wind-up time evenly", "attack": 80,
                        "hurt": 90, "stagger": 120, "defeat": 140, "transform": 140, "tendril": 120, "shot": 90},
    }


def main():
    only = sys.argv[1:]
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(DOC, exist_ok=True)
    imgs = build(only)
    kinds_done = {n.split(".")[1] for n in imgs}
    for f in os.listdir(OUT):  # drop stale frames of the kinds just rebuilt
        if f.endswith(".png") and f.split(".")[1] in kinds_done and f[:-4] not in imgs:
            os.remove(os.path.join(OUT, f))
    for name, im in imgs.items():
        im.save(os.path.join(OUT, f"{name}.png"), optimize=True)
    man = manifest()
    for path in (os.path.join(OUT, "frames.json"), os.path.join(DOC, "frames.json")):
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(man, fp, ensure_ascii=False, indent=1)
            fp.write("\n")
    print(f"wrote {len(imgs)} frames to src/art-release-v2/enemy/ ({', '.join(sorted(kinds_done))})")


if __name__ == "__main__":
    main()
