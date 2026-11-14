"""Comparison images for the v3 bosses. Run: python3 tools/art_v3/compare_boss_v3.py <out dir> [kind]
  cmp_<action>_15pro_k2.png   top row v2 (d900394) at 2x2 per pixel, bottom row v3; the 15 Pro's v3 view
                              (1 game px = 8 screen px: a v3 texel = 2 px, a v2 pixel = 4 px)
  all_v3_se_k1.png            every v3 frame, the SE's v3 view (1 game px = 4 px: a v3 texel = 1 px)
  all_v3_15pro_k2_a/b.png     every v3 frame at the 15 Pro's view
  all_v2_se_k1.png            every v2 frame at the same size (2x2 per pixel)
  idle0_v2_v3_x6.png          idle 0: v2 at 2x2 | v3, a v3 texel = 6 px
  parts.png                   every hand-drawn part map (a texel = 3 px)
The ground is the v3 plains grass (summer) -- the boss arenas are not made yet. No contact shadow.
"""

import io
import os
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "boss_v3"))
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(ROOT, "src", "art-release-v3", "boss")
TILES = os.path.join(ROOT, "src", "art-release-v3", "terrain")


def ground(w, h):
    g = Image.new("RGB", (w, h), (78, 110, 62))
    for ty in range(0, h, 64):
        for tx in range(0, w, 64):
            p = os.path.join(TILES, f"plains.grass.v3.a{(ty // 64) % 4}{(tx // 64) % 4}.png")
            if os.path.exists(p):
                g.paste(Image.open(p).convert("RGB"), (tx, ty))
    return g


def v2(name):
    blob = subprocess.run(["git", "-C", ROOT, "show", f"d900394:src/art-release-v2/enemy/{name}.png"],
                          capture_output=True, check=True).stdout
    im = Image.open(io.BytesIO(blob)).convert("RGBA")
    return im.resize((im.width * 2, im.height * 2), Image.NEAREST)


def v3(name):
    return Image.open(os.path.join(SRC, f"{name}.png")).convert("RGBA")


def sheet(rows, load, k, cols=6):
    w, h = load(rows[0][0]).size
    g = ground(w * cols, h * len(rows))
    for r, names in enumerate(rows):
        for c, n in enumerate(names):
            im = load(n)
            g.paste(im, (c * w, r * h), im)
    return g.resize((g.width * k, g.height * k), Image.NEAREST) if k != 1 else g


def main():
    out = sys.argv[1]
    kind = sys.argv[2] if len(sys.argv) > 2 else "boss_root"
    os.makedirs(out, exist_ok=True)
    mod = __import__(kind)
    acts = [(a, [f"enemy.{kind}.{a}.{i}" for i in range(n)]) for a, n in mod.ACTIONS]
    for a, names in acts:
        w, h = v3(names[0]).size
        g = ground(w * len(names), h * 2)
        for c, n in enumerate(names):
            for r, im in enumerate((v2(n), v3(n))):
                g.paste(im, (c * w, r * h), im)
        g.resize((g.width * 2, g.height * 2), Image.NEAREST).save(os.path.join(out, f"cmp_{a}_15pro_k2.png"))
    rows = [n for _, n in acts]
    sheet(rows, v3, 1).save(os.path.join(out, "all_v3_se_k1.png"))
    sheet(rows, v2, 1).save(os.path.join(out, "all_v2_se_k1.png"))
    sheet(rows[:7], v3, 2).save(os.path.join(out, "all_v3_15pro_k2_a.png"))
    sheet(rows[7:], v3, 2).save(os.path.join(out, "all_v3_15pro_k2_b.png"))
    n = f"enemy.{kind}.idle.0"
    w, h = v3(n).size
    g = ground(w * 2, h)
    for c, im in enumerate((v2(n), v3(n))):
        g.paste(im, (c * w, 0), im)
    g.resize((g.width * 6, g.height * 6), Image.NEAREST).save(os.path.join(out, "idle0_v2_v3_x6.png"))
    # the part maps
    parts = [(k, p) for k, p in mod.P.items() if not k.endswith("~") and not k.endswith("_DIM")]
    W = 660
    x = y = 4
    rowh = 0
    place = []
    for k, p in parts:
        if x + p.w + 4 > W:
            x, y, rowh = 4, y + rowh + 6, 0
        place.append((k, p, x, y))
        x += p.w + 6
        rowh = max(rowh, p.h)
    g = Image.new("RGB", (W, y + rowh + 4), (78, 110, 62))
    from pixmap import Frame
    for k, p, x, y in place:
        f = Frame(p.w, p.h, mod.LEG, mod.RAMPS)
        f.put(p, 0, 0)
        im = Image.fromarray(f.rgba(), "RGBA")
        g.paste(im, (x, y), im)
    g.resize((g.width * 3, g.height * 3), Image.NEAREST).save(os.path.join(out, "parts.png"))
    print("written to", out, ":", len(os.listdir(out)), "files;", len(parts), "part maps")


if __name__ == "__main__":
    main()
