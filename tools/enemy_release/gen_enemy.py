"""Enemies & bosses — RELEASE art (QUALITY_POLICY: made at release quality, adopted after approval).

Design: docs/enemy/ENEMY_BOSS_DESIGN.md v3 (approved). Style: ART_STYLE_GUIDE.md (branch docs/art-style-guide).
Writes src/art-release/enemy/<name>.png and docs/art-release/enemy/frames.json.

Names:
  1. the MINIMAL set the current code draws (same names as today's placeholders, 2 frames):
       enemy.<kind>.0  standing      enemy.<kind>.1  moving (alternates with .0)
     for beast, archer, boss_root, boss_frost, boss_sand, boss_storm
  2. the FULL set by action: enemy.<kind>.<action>.<n>
       beast archer slime sentinel: idle 2, move 4, windup 2, attack 2, hurt 1, defeat 3
       boss_root/frost/sand/storm:  idle 2, move 2, windup_<p> 2 and attack_<p> 2 for its three
                                    patterns, hurt 1, stagger 2, idle2 2 (phase 2), defeat 4
       boss_source:                 idle 2, idle2 2, windup_/attack_<volley|ring|slam|charge> 2 each,
                                    hurt 1, transform 4, defeat 6, tendril 3 (32x48)
       shot:                        orb, ice, sand, spark: 2 each (12x12, centre anchor)
Every enemy faces right (the game mirrors it); bosses face the camera. Feet at the bottom centre.

Run: python3 tools/enemy_release/gen_enemy.py   (then previews.py for the sheets and GIFs)
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
OUT = os.path.join(ROOT, "src", "art-release", "enemy")
DOC = os.path.join(ROOT, "docs", "art-release", "enemy")

KINDS = [  # (kind, module, facing)
    ("beast", beast, "right"), ("archer", archer, "right"), ("slime", slime, "right"), ("sentinel", sentinel, "right"),
    ("boss_root", boss_root, "front"), ("boss_frost", boss_frost, "front"), ("boss_sand", boss_sand, "front"),
    ("boss_storm", boss_storm, "front"), ("boss_source", boss_source, "front"), ("shot", shots, "right"),
]
MINIMAL = {  # the code's current names -> the full frame they are
    "beast": ("idle.0", "move.0"), "archer": ("idle.0", "move.0"),
    "boss_root": ("idle.0", "move.0"), "boss_frost": ("idle.0", "move.0"),
    "boss_sand": ("idle.0", "move.0"), "boss_storm": ("idle.0", "move.0"),
}


def to_image(rows):
    h, w = len(rows), len(rows[0])
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    for y in range(h):
        for x in range(w):
            if rows[y][x]:
                px[x, y] = rows[y][x]
    return im


def build():
    """name -> PIL image for every frame (full set and minimal set)."""
    out = {}
    for kind, mod, _ in KINDS:
        for key, rig in mod.frames().items():
            out[f"enemy.{kind}.{key}"] = to_image(rig.image(outline=kind != "shot"))
    for kind, (a, b) in MINIMAL.items():
        out[f"enemy.{kind}.0"] = out[f"enemy.{kind}.{a}"]
        out[f"enemy.{kind}.1"] = out[f"enemy.{kind}.{b}"]
    return out


def manifest(imgs):
    kinds = {}
    for name, im in imgs.items():
        parts = name.split(".")
        kind = parts[1]
        if len(parts) == 3:
            continue
        action, n = ".".join(parts[2:-1]), int(parts[-1])
        k = kinds.setdefault(kind, {"facing": dict((a, c) for a, _, c in KINDS)[kind], "actions": {}})
        a = k["actions"].setdefault(action, {"frames": 0, "size": list(im.size)})
        a["frames"] = max(a["frames"], n + 1)
    return {
        "minimal": {f"enemy.{k}.{i}": f"enemy.{k}.{v}" for k, pair in MINIMAL.items() for i, v in enumerate(pair)},
        "kinds": kinds,
        "anchor": "feet = bottom centre (shots: centre)",
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(DOC, exist_ok=True)
    imgs = build()
    keep = {f"{n}.png" for n in imgs}
    for f in os.listdir(OUT):
        if f.endswith(".png") and f not in keep:
            os.remove(os.path.join(OUT, f))
    for name, im in imgs.items():
        im.save(os.path.join(OUT, f"{name}.png"), optimize=True)
    with open(os.path.join(DOC, "frames.json"), "w", encoding="utf-8") as fp:
        json.dump(manifest(imgs), fp, ensure_ascii=False, indent=1)
        fp.write("\n")
    print(f"wrote {len(imgs)} frames to src/art-release/enemy/")


if __name__ == "__main__":
    main()
