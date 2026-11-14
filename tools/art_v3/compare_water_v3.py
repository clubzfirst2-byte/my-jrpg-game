"""Comparison pictures of the v3 water (gen_water_v3.py) against v2, the same place, all 4 frames.

A map 40 x 24 cells: sea with a desert-sand island (west), a plains island (east), a 1-cell strait and a
small pond. The current picture is v2's own reference renderer (tools/terrain_v2/render_ref.render_v2,
unchanged: shallow / deep by its depth rule, deep edges, foam, land edges). For v3 the keys render_v2 draws
on each display tile are recorded and swapped: tile.water* -> the v3 water of the same key and frame; desert
sand / plains grass -> the v3 bases (+ flow) and v3 edges. No level tint.
  water_15pro_<now|v3>_f<0-3>_k2.png (2556 x 1179), water_se_<now|v3>_f0_k1.png (1334 x 750),
  water_frames_v3_k2.png (4 frames of one place side by side), water_v3_k2.gif / water_now_k2.gif (the loop,
  0.28 s a frame), water_tiles_x4.png (the 32 water keys of frame 0, 4x)
Run: python3 tools/art_v3/compare_water_v3.py <out dir>
"""

import functools
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from PIL import Image  # noqa: E402

import compare_desert_v3 as CD  # noqa: E402
import gen_ground_v3 as G  # noqa: E402
from v3lib import ROOT  # noqa: E402

sys.path.append(os.path.join(ROOT, "tools", "terrain_v2"))
import render_ref as RR  # noqa: E402

V2T = os.path.join(ROOT, "src", "art-release-v2", "terrain")
V3T = os.path.join(ROOT, "src", "art-release-v3", "terrain")
W, H = 40, 24


@functools.lru_cache(maxsize=None)
def ld(p):
    return Image.open(p).convert("RGBA")


def grid():
    rows = []
    for y in range(H + 1):
        r = ""
        for x in range(W + 1):
            c = "~"
            if (x - 9) ** 2 / 40 + (y - 11) ** 2 / 30 + 0.12 * math.sin(x * 0.9 + y) < 1:
                c = "d"
            if (x - 30) ** 2 / 36 + (y - 12) ** 2 / 42 + 0.12 * math.sin(y * 0.8) < 1:
                c = "p"
            if x == 30 and 9 <= y <= 13:
                c = "~"  # a 1-cell strait into the plains island
            if (x - 31) ** 2 + (y - 18) ** 2 <= 2:
                c = "~"  # a pond
            r += c
        rows.append(r)
    return rows


def water_file(key, frame):
    """g2.water.* -> the file of the same key (v2 or v3 folder decided by the caller)."""
    parts = key.split(".")
    if parts[2] in ("shallow", "deep"):
        base = "tile.water" if parts[2] == "shallow" else "tile.water.deep"
        return f"{base}{'.v1' if parts[3] == '1' else ''}.{frame}.png"
    if parts[2] == "deep":
        pass
    m = parts[3][1:]
    return f"tile.water.{'deep.edge' if parts[2] == 'deep' else 'foam'}.{m}.{frame}.png"


def record(g, frame):
    class Key:
        def __init__(self, k):
            self.k = k

    class Images(dict):
        def __missing__(self, k):
            return Key(k)
    draws = {}

    def ac(self, im, dest=(0, 0), source=(0, 0)):
        draws.setdefault(((dest[0] - 16) // 32, (dest[1] - 16) // 32), []).append(im.k)
    old = Image.Image.alpha_composite, Image.Image.paste
    Image.Image.alpha_composite = ac
    Image.Image.paste = lambda self, *a, **k: None
    try:
        RR.render_v2(g, Images(), frame=frame)
    finally:
        Image.Image.alpha_composite, Image.Image.paste = old
    return draws


V2PRE = {"plains": "plains.grass", "dsand": "desert.sand"}


def tile_for(ver, key, frame, g, i, j):
    parts = key.split(".")
    if parts[1] == "water":
        if parts[2] == "deep" and parts[3].startswith("e"):
            name = f"tile.water.deep.edge.{parts[3][1:]}.{frame}.png"
        elif parts[2] == "foam":
            name = f"tile.water.foam.{parts[3][1:]}.{frame}.png"
        else:
            name = f"{'tile.water' if parts[2] == 'shallow' else 'tile.water.deep'}{'.v1' if parts[3] == '1' else ''}.{frame}.png"
        return ld(os.path.join(V2T if ver == "now" else V3T, name))
    cls, name = parts[1], parts[2] if len(parts) == 3 else ".".join(parts[2:])
    if name.startswith("e") and name[1].isdigit():
        m, v = name[1:].split(".")
        if ver == "now":
            return ld(os.path.join(V2T, f"{V2PRE[cls]}.edge.{m}.{v}.png"))
        return ld(os.path.join(V3T, f"{V2PRE[cls]}.v3.edge.{m}.{v}.png"))
    if ver == "now":
        return ld(os.path.join(V2T, f"{V2PRE[cls]}.{name}.png"))
    if cls == "dsand":
        return CD.v3_base(g, i, j)
    return G.ground_tile(i, j, "summer", load=ld)


def scene(ver, frame):
    d = 2 if ver == "now" else 4
    T = 16 * d
    g = grid()
    im = Image.new("RGBA", ((W + 1) * T, (H + 1) * T), (0, 0, 0, 255))
    for (i, j), keys in record(g, frame).items():
        for k in keys:
            im.alpha_composite(tile_for(ver, k, frame, g, i, j), (i * T + T // 2, j * T + T // 2))
    return im.crop((T // 2, T // 2, T // 2 + W * T, T // 2 + H * T))


def tiles_sheet(path):
    keys = ["tile.water", "tile.water.v1", "tile.water.deep", "tile.water.deep.v1"] + \
        [f"tile.water.deep.edge.{m}" for m in range(1, 15)] + [f"tile.water.foam.{m}" for m in range(1, 15)]
    out = Image.new("RGBA", (8 * 264, 4 * 264), (60, 60, 70, 255))
    for n, k in enumerate(keys):
        t = ld(os.path.join(V3T, f"{k}.0.png")).resize((256, 256), Image.NEAREST)
        out.alpha_composite(t, ((n % 8) * 264, (n // 8) * 264))
    out.save(path, optimize=True)


def main(out):
    os.makedirs(out, exist_ok=True)
    gifs = {"now": [], "v3": []}
    for ver in ("now", "v3"):
        d = 2 if ver == "now" else 4
        for f in range(4):
            im = scene(ver, f)
            big = im.resize((im.width * (8 // d), im.height * (8 // d)), Image.NEAREST)
            x0, y0 = 10 * 16 * 8, 6 * 16 * 8
            crop = big.crop((x0, y0, x0 + 2556, y0 + 1179))
            crop.save(os.path.join(out, f"water_15pro_{ver}_f{f}_k2.png"), optimize=True)
            gifs[ver].append(crop.crop((0, 0, 1278, 590)).convert("P", palette=Image.ADAPTIVE))
            if f == 0:
                bse = im.resize((im.width * (4 // d), im.height * (4 // d)), Image.NEAREST) if d == 2 else im
                x0, y0 = 6 * 16 * 4, 5 * 16 * 4
                bse.crop((x0, y0, x0 + 1334, y0 + 750)).save(os.path.join(out, f"water_se_{ver}_f0_k1.png"), optimize=True)
        gifs[ver][0].save(os.path.join(out, f"water_{ver}_k2.gif"), save_all=True, append_images=gifs[ver][1:],
                          duration=280, loop=0)
    strip = Image.new("RGBA", (4 * 640 + 30, 400), (30, 30, 30, 255))
    for f in range(4):
        strip.paste(Image.open(os.path.join(out, f"water_15pro_v3_f{f}_k2.png")).crop((600, 300, 1240, 700)), (f * 650, 0))
    strip.save(os.path.join(out, "water_frames_v3_k2.png"), optimize=True)
    tiles_sheet(os.path.join(out, "water_tiles_x4.png"))
    print(sorted(f for f in os.listdir(out) if f.startswith("water")))


if __name__ == "__main__":
    main(sys.argv[1])
