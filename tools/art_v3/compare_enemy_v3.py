"""Comparison pictures of the v3 normal enemies and shots against v2 (d900394), the same game size.

  <kind>_15pro_k2.png   v2 (top row) and v3 (bottom row): idle 4, attack 5, defeat 6 frames on the v3 grass,
                        15 Pro v3 view: 1 game px = 8 device px (v2 texel 4 px, v3 texel 2 px)
  <kind>_se_k1.png      the same at the SE v3 view: 1 game px = 4 device px (v2 texel 2 px, v3 texel 1 px)
  shots_15pro_k2.png / shots_se_k1.png   the 4 shots, 4 frames each, v2 and v3
  scene_<v2|v3>_15pro_k2.png / scene_<v2|v3>_se_k1.png   a field (v3 grass) with the hero (v3) and
                        the 4 enemies (idle 0) and a shot, cropped to the device view
No contact shadows (the game's).
Run: python3 tools/art_v3/compare_enemy_v3.py <out dir>
"""

import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from PIL import Image, ImageDraw  # noqa: E402

from gen_ground_v3 import ground_tile  # noqa: E402
from v3lib import ROOT  # noqa: E402

V3 = os.path.join(ROOT, "src", "art-release-v3", "enemy")
REF = "d900394"
BG = (40, 44, 52, 255)
_cache = {}


def v2(name):
    if name not in _cache:
        blob = subprocess.run(["git", "-C", ROOT, "show", f"{REF}:src/art-release-v2/enemy/{name}.png"],
                              capture_output=True, check=True).stdout
        _cache[name] = Image.open(io.BytesIO(blob)).convert("RGBA")
    return _cache[name]


def v3(name):
    return Image.open(os.path.join(V3, name + ".png")).convert("RGBA")


def grass(w, h, seed=0):
    """v3 summer grass at 1 texel per px, w x h texels."""
    img = Image.new("RGBA", (w, h))
    for ty in range(h // 64 + 1):
        for tx in range(w // 64 + 1):
            img.alpha_composite(ground_tile(tx + seed, ty + 7, "summer"), (tx * 64, ty * 64))
    return img


def strip(names, k):
    """Rows v2 / v3 of the frames `names` on the grass; k = device px per v3 texel."""
    cell_w = max(v3(n).width for n in names) + 16
    cell_h = max(v3(n).height for n in names) + 12
    W, H = cell_w * len(names), cell_h * 2
    base = grass(W, H, 3)
    for row, ver in enumerate(("v2", "v3")):
        for i, n in enumerate(names):
            if ver == "v2":
                im = v2(n)
                im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
            else:
                im = v3(n)
            fx, fy = i * cell_w + cell_w // 2, row * cell_h + cell_h - 4
            if ".shot." in n:
                fy = row * cell_h + cell_h // 2 + im.height // 2
            base.alpha_composite(im, (fx - im.width // 2, fy - im.height))
    out = base.resize((W * k, H * k), Image.NEAREST)
    lab = Image.new("RGBA", (out.width, 28), BG)
    ImageDraw.Draw(lab).text((6, 8), "top: v2 (each v2 texel = 2 v3 texels)   bottom: v3   " + ", ".join(sorted({n.split('.')[2] for n in names})), fill=(230, 230, 230, 255))
    full = Image.new("RGBA", (out.width, out.height + 28), BG)
    full.alpha_composite(lab, (0, 0))
    full.alpha_composite(out, (0, 28))
    return full


def scene(ver, k, dev):
    """A field with the hero and the 4 enemies. ver v2: the v2 enemies at 2x2 texels per v2 texel."""
    gw, gh = dev[0] // (4 * k) + 1, dev[1] // (4 * k) + 1  # game px shown
    W, H = gw * 4, gh * 4
    img = grass(W, H, 11)
    hero = Image.open(os.path.join(ROOT, "src", "art-release-v3", "hero", "hero.idle.down.0.png")).convert("RGBA")
    things = [("hero", W // 2, H // 2 + 60), ("enemy.slime.idle.0", W // 2 + 170, H // 2 + 40),
              ("enemy.beast.idle.0", W // 2 - 230, H // 2 + 10), ("enemy.archer.idle.0", W // 2 + 330, H // 2 - 70),
              ("enemy.sentinel.idle.0", W // 2 - 420, H // 2 + 120), ("enemy.shot.orb.0", W // 2 + 250, H // 2 - 60)]
    for n, x, y in sorted(things, key=lambda t: t[2]):
        if n == "hero":
            im = hero
        elif ver == "v2":
            im = v2(n)
            im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
        else:
            im = v3(n)
        img.alpha_composite(im, (x - im.width // 2, y - (im.height // 2 if ".shot." in n else im.height)))
    return img.resize((W * k, H * k), Image.NEAREST).crop((0, 0, dev[0], dev[1]))


def main(out):
    os.makedirs(out, exist_ok=True)
    for kind in ("slime", "beast", "archer", "sentinel"):
        names = [f"enemy.{kind}.idle.{i}" for i in range(4)] + [f"enemy.{kind}.attack.{i}" for i in range(5)] + \
                [f"enemy.{kind}.defeat.{i}" for i in range(6)]
        strip(names, 2).save(os.path.join(out, f"{kind}_15pro_k2.png"), optimize=True)
        strip(names, 1).save(os.path.join(out, f"{kind}_se_k1.png"), optimize=True)
    shots = [f"enemy.shot.{s}.{i}" for s in ("orb", "ice", "sand", "spark") for i in range(4)]
    strip(shots, 2).save(os.path.join(out, "shots_15pro_k2.png"), optimize=True)
    strip(shots, 1).save(os.path.join(out, "shots_se_k1.png"), optimize=True)
    for ver in ("v2", "v3"):
        scene(ver, 2, (2556, 1179)).save(os.path.join(out, f"scene_{ver}_15pro_k2.png"), optimize=True)
        scene(ver, 1, (1334, 750)).save(os.path.join(out, f"scene_{ver}_se_k1.png"), optimize=True)
    print(sorted(os.listdir(out)))


if __name__ == "__main__":
    main(sys.argv[1])
