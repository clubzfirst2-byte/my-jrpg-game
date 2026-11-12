"""Comparison pictures of the v3 normal enemies and shots against v2 (d900394), the same game size.

  <kind>_15pro_k2.png   v2 (top row) and v3 (bottom row): idle 4, attack 5, defeat 6 frames on the v3 grass,
                        15 Pro v3 view: 1 game px = 8 device px (v2 texel 4 px, v3 texel 2 px)
  <kind>_se_k1.png      the same at the SE v3 view: 1 game px = 4 device px (v2 texel 2 px, v3 texel 1 px)
  shots_15pro_k2.png / shots_se_k1.png   the 4 shots, 4 frames each, v2 and v3
  faces_v2_v3_8x.png    the faces at 8x per v3 texel (v2 at 2x | v3), and the hero's face at the same scale
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


FACES = {  # kind: (frame, crop box in v3 texels x0, y0, x1, y1)
    "beast": ("idle.0", 50, 6, 88, 40), "archer": ("idle.0", 18, 22, 60, 56), "sentinel": ("idle.0", 18, 10, 60, 44),
    "slime": ("idle.0", 12, 14, 52, 44),
}


def faces(path, z=8):
    """The faces at 8x per v3 texel: v2 (at 2x first) | v3, with the hero's face (v3) for the scale."""
    rows = []
    for kind, (f, x0, y0, x1, y1) in FACES.items():
        a = v2(f"enemy.{kind}.{f}")
        a = a.resize((a.width * 2, a.height * 2), Image.NEAREST)
        b = v3(f"enemy.{kind}.{f}")
        cells = []
        for im in (a, b):
            bg = Image.new("RGBA", im.size, (70, 72, 78, 255))
            bg.alpha_composite(im)
            cells.append(bg.crop((x0, y0, x1, y1)).resize(((x1 - x0) * z, (y1 - y0) * z), Image.NEAREST))
        rows.append((kind, cells))
    hero = Image.open(os.path.join(ROOT, "src", "art-release-v3", "hero", "hero.idle.down.0.png")).convert("RGBA")
    hb = Image.new("RGBA", hero.size, (70, 72, 78, 255))
    hb.alpha_composite(hero)
    hero = hb.crop((8, 10, 56, 50)).resize((48 * z, 40 * z), Image.NEAREST)
    W = max(c[0].width + c[1].width for _, c in rows) + 60
    H = sum(max(c[0].height, c[1].height) + 40 for _, c in rows) + hero.height + 40
    img = Image.new("RGBA", (W, H), BG)
    d = ImageDraw.Draw(img)
    y = 0
    for kind, (ca, cb) in rows:
        d.text((8, y + 8), f"{kind}: v2 (2x) | v3, {z}x per v3 texel", fill=(230, 230, 230, 255))
        img.alpha_composite(ca, (8, y + 30))
        img.alpha_composite(cb, (ca.width + 40, y + 30))
        y += max(ca.height, cb.height) + 40
    d.text((8, y + 8), "hero v3 (the same scale)", fill=(230, 230, 230, 255))
    img.alpha_composite(hero, (8, y + 30))
    img.save(path, optimize=True)


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
    faces(os.path.join(out, "faces_v2_v3_8x.png"))
    for ver in ("v2", "v3"):
        scene(ver, 2, (2556, 1179)).save(os.path.join(out, f"scene_{ver}_15pro_k2.png"), optimize=True)
        scene(ver, 1, (1334, 750)).save(os.path.join(out, f"scene_{ver}_se_k1.png"), optimize=True)
    print(sorted(os.listdir(out)))


if __name__ == "__main__":
    main(sys.argv[1])
