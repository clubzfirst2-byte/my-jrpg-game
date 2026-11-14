"""Comparison pictures of the v3 desert steps and cliffs (gen_cliff_v3.py) against v2, the same place.

A map 40 x 20 cells of desert sand with two mesas (one 2 levels high with a 1-level shelf on its east
part, one 3 levels high), drawn the way gameView draws heights (v2 NAMES.md 2b and 4):
  * flat ground on the dual grid (v2: render_ref.render_v2; v3: the v3 desert base + flow),
  * then each raised row, north to south: per cell its surface on the cell grid at (tx*16, ty*16 - h),
    the step rim <prefix>.step.<mask>.<v> (mask 1 N + 2 E + 4 W lower, v = hash(tx+5, ty+9) % 2), the
    inner corners, the south face down to the south neighbour's height (bands of 8 / 4 px:
    face.desert.<top|mid><-base>.<8|4>, ".v1" when hash(tx, ty) % 2), then the row's east shadows
    <prefix>.step.shade.<v> on the lower east cells (v = hash(tx+6, ty+9) % 2).
  * no level tint and no translucent contact shadow (the engine adds both the same way to v2 and v3).
  cliff_15pro_<now|v3>_k2.png (2556 x 1179), cliff_se_<now|v3>_k1.png (1334 x 750),
  cliff_parts_x4.png (the v3 faces and rims enlarged).
Run: python3 tools/art_v3/compare_cliff_v3.py <out dir>
"""

import functools
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from PIL import Image  # noqa: E402

import gen_desert_v3 as D  # noqa: E402
import compare_desert_v3 as CD  # noqa: E402
from v3lib import ROOT  # noqa: E402

sys.path.append(os.path.join(ROOT, "tools", "terrain_v2"))
import render_ref as RR  # noqa: E402

V2T = os.path.join(ROOT, "src", "art-release-v2", "terrain")
V3T = os.path.join(ROOT, "src", "art-release-v3", "terrain")
W, H = 40, 20


@functools.lru_cache(maxsize=None)
def ld(p):
    return Image.open(p).convert("RGBA")


def heights():
    """Height in game px per cell (16 = one level)."""
    e = [[0] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            if 4 <= x <= 16 and 3 <= y <= 9 and not (x >= 14 and y <= 4):
                e[y][x] = 32
            if 14 <= x <= 19 and 6 <= y <= 11:
                e[y][x] = max(e[y][x], 16)
            if 25 <= x <= 33 and 5 <= y <= 12 and not (x == 25 and y >= 11) and not (x >= 32 and y <= 6):
                e[y][x] = 48
    return e


def el(e, x, y):
    return e[y][x] if 0 <= x < W and 0 <= y < H else 0


GROUNDS = {  # ground: (v2 grid char, v2 prefix, face material, plateau faces' variants)
    "desert": ("d", "desert.sand", "desert", 2),
    "plains": ("p", "plains.grass", "earth", 3),
    "forest": ("m", "forest.grass", "earth", 3),
}


def v3_surface(ground, season, tx, ty):
    if ground == "desert":
        return D.ground_tile(tx, ty, load=ld)
    import gen_ground_v3 as G3
    import gen_forest_v3 as F3
    return (G3 if ground == "plains" else F3).ground_tile(tx, ty, season, load=ld)


def v3_flat(g, ground, season, i, j):
    if ground == "desert":
        return CD.v3_base(g, i, j)
    return v3_surface(ground, season, i, j)  # (all one ground: the flow is the plain rule)


def scene(ver, ground="desert", season="summer"):
    ch, gpre, fmat, nvar = GROUNDS[ground]
    sp = "" if season == "summer" else season + "."
    d = 2 if ver == "now" else 4
    T = 16 * d
    g = [ch * (W + 1) for _ in range(H + 1)]
    im = Image.new("RGBA", (W * T, H * T), (0, 0, 0, 255))
    rec = CD.record(g) if ground == "desert" else record_season(g, season)
    for (i, j), keys in rec.items():  # flat ground (dual grid)
        for k in keys:
            tile = ld(v2_file_s(k, season)) if ver == "now" else v3_flat(g, ground, season, i, j)
            im.alpha_composite(tile, (i * T + T // 2, j * T + T // 2))
    im = im.crop((T // 2, T // 2, T // 2 + W * T, T // 2 + H * T))
    big = Image.new("RGBA", (W * T, H * T), (0, 0, 0, 255))
    big.paste(im, (0, 0))
    im = big
    e = heights()
    hsh = RR.dhash
    folder = V2T if ver == "now" else V3T
    pre = (sp + gpre) if ver == "now" else (sp + gpre + ".v3")
    if ground == "desert":
        pre = "desert.sand" if ver == "now" else "desert.sand.v3"
    for ty in range(H):
        shades = []
        for tx in range(W):
            h = e[ty][tx]
            if h == 0:
                continue
            X, Y = tx * T, (ty * 16 - h) * d
            if ver == "now":
                surf = ld(os.path.join(V2T, f"{sp if ground != 'desert' else ''}{gpre}.{RR.calm_number(tx, ty) % 32}.png"))
            else:
                surf = v3_surface(ground, season, tx, ty)
            im.alpha_composite(surf, (X, Y))
            n, ea, we = el(e, tx, ty - 1) < h, el(e, tx + 1, ty) < h, el(e, tx - 1, ty) < h
            mask = n + 2 * ea + 4 * we
            if mask:
                im.alpha_composite(ld(os.path.join(folder, f"{pre}.step.{mask}.{hsh(tx + 5, ty + 9) % 2}.png")), (X, Y))
            if not n and not ea and el(e, tx + 1, ty - 1) < h:
                im.alpha_composite(ld(os.path.join(folder, f"{pre}.step.inner.ne.png")), (X, Y))
            if not n and not we and el(e, tx - 1, ty - 1) < h:
                im.alpha_composite(ld(os.path.join(folder, f"{pre}.step.inner.nw.png")), (X, Y))
            top, bottom = (ty + 1) * 16 - h, (ty + 1) * 16 - el(e, tx, ty + 1)
            rem, y, first = bottom - top, top, True
            var = ("", ".v1", ".v2")[hsh(tx, ty) % nvar]
            while rem > 0:
                seg = 8 if rem >= 8 else 4
                last = rem - seg <= 0
                key = f"face.{fmat}.{'top' if first else 'mid'}{'-base' if last else ''}.{seg}"
                cands = [sp + key + var, sp + key, key + var, key] if fmat == "earth" else [key + var, key]
                p = next(os.path.join(folder, k_ + ".png") for k_ in cands if os.path.exists(os.path.join(folder, k_ + ".png")))
                im.alpha_composite(ld(p), (X, y * d))
                y += seg
                rem -= seg
                first = False
            if ea and tx + 1 < W:
                shades.append((tx + 1, ty, el(e, tx + 1, ty), hsh(tx + 6, ty + 9) % 2))
        for (sx, sy, sh, v) in shades:
            im.alpha_composite(ld(os.path.join(folder, f"{pre}.step.shade.{v}.png")), (sx * T, (sy * 16 - sh) * d))
    return im


def record_season(g, season):
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
        RR.render_v2(g, Images(), frame=0, season=None if season == "summer" else season)
    finally:
        Image.Image.alpha_composite, Image.Image.paste = old
    return draws


V2PRE = {"plains": "plains.grass", "moss": "forest.grass", "dsand": "desert.sand"}


def v2_file_s(key, season):
    """<season.>g2.<class>.<name> -> the v2 file."""
    sp = ""
    if not key.startswith("g2."):
        sp, key = key.split("g2.", 1)
        key = "g2." + key
    _, cls, name = key.split(".", 2)
    if name.startswith("e") and name[1].isdigit():
        m, v = name[1:].split(".")
        name = f"edge.{m}.{v}"
    return os.path.join(V2T, f"{sp}{V2PRE[cls]}.{name}.png")


def parts(path):
    names = [f"face.desert.{p}.{h}{v}" for p in ("top", "mid", "top-base", "mid-base") for h in (8, 4) for v in ("", ".v1")]
    cells = [ld(os.path.join(V3T, n + ".png")) for n in names]
    steps = [ld(os.path.join(V3T, f"desert.sand.v3.step.{m}.{v}.png")) for m in range(1, 8) for v in (0, 1)] + \
        [ld(os.path.join(V3T, f"desert.sand.v3.step.{k}.png")) for k in ("shade.0", "shade.1", "inner.ne", "inner.nw")]
    k = 4
    Wd = 8 * (64 * k + 8)
    out = Image.new("RGBA", (Wd, 2 * (32 * k + 8) + 3 * (64 * k + 8)), (40, 44, 70, 255))
    for i, c in enumerate(cells):
        out.alpha_composite(c.resize((c.width * k, c.height * k), Image.NEAREST), ((i % 8) * (64 * k + 8), (i // 8) * (32 * k + 8)))
    y0 = 2 * (32 * k + 8)
    for i, c in enumerate(steps):
        out.alpha_composite(c.resize((64 * k, 64 * k), Image.NEAREST), ((i % 8) * (64 * k + 8), y0 + (i // 8) * (64 * k + 8)))
    out.save(path, optimize=True)


def main(out):
    os.makedirs(out, exist_ok=True)
    which = sys.argv[2] if len(sys.argv) > 2 else "desert"
    sets = [("desert", "summer")] if which == "desert" else [(g, s) for g in ("plains", "forest") for s in ("summer", "autumn", "winter")]
    for ground, season in sets:
        tag = "cliff" if ground == "desert" else f"cliff_{ground}_{season}"
        for ver in ("now", "v3"):
            im = scene(ver, ground, season)
            d = 2 if ver == "now" else 4
            big = im.resize((im.width * (8 // d), im.height * (8 // d)), Image.NEAREST)
            x0, y0 = 2 * 16 * 8, 1 * 16 * 8
            big.crop((x0, y0, x0 + 2556, y0 + 1179)).save(os.path.join(out, f"{tag}_15pro_{ver}_k2.png"), optimize=True)
            bse = im.resize((im.width * (4 // d), im.height * (4 // d)), Image.NEAREST) if d == 2 else im
            x0, y0 = 2 * 16 * 4, 1 * 16 * 4
            bse.crop((x0, y0, x0 + 1334, y0 + 750)).save(os.path.join(out, f"{tag}_se_{ver}_k1.png"), optimize=True)
    if which == "desert":
        parts(os.path.join(out, "cliff_parts_x4.png"))
    print(sorted(f for f in os.listdir(out) if f.startswith("cliff")))


if __name__ == "__main__":
    main(sys.argv[1])
