"""Stacked cliff walls: the check the inspection asked for (desert inspection P1-4), reference numbers only.

For each face material (desert, earth in the 3 seasons) a wall of 14 tiles (x 10..23, y 40) is stacked
1, 2 and 3 levels high (16 / 32 / 48 game px: bands of 8 px, gameView.addFace), the variant chosen by
  rule "now"       the game today: one variant per cell, hash(tx, ty) % n (terrainArt.faceVariant;
                   desert n = 2 today, earth n = 3)
  rule "per-band"  the proposal (DESERT.md 9): band k of the cell takes (hash(tx, ty) + k) % 3
and measured on the mid bands:
  same       the share of texels equal between vertically neighbouring mid bands of one cell (mean)
  dominant   the share of the commonest colour in a mid band (max over its variants)
  steps      the share of neighbouring texel pairs (both opaque) whose brightness differs by more than
             10 / 12 / 14 / 15, over the whole wall
Pictures: wall_<mat>_<rule>_<n>levels_k2.png (1 texel = 2 px, 15 Pro) and _k1.png (SE).
Run: python3 tools/art_v3/check_cliff_v3.py <out dir>
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from v3lib import ROOT  # noqa: E402

sys.path.append(os.path.join(ROOT, "tools", "terrain_v2"))
import render_ref as RR  # noqa: E402

V3T = os.path.join(ROOT, "src", "art-release-v3", "terrain")
VAR = ("", ".v1", ".v2")


def ld(p):
    return Image.open(p).convert("RGBA")


def key_file(mat, season, key):
    for k in ([f"{season}.{key}"] if season != "summer" else []) + [key]:
        p = os.path.join(V3T, f"face.{mat}.{k}.png" if not k.startswith(("autumn.", "winter.")) else
                         f"{k.split('.', 1)[0]}.face.{mat}.{k.split('.', 1)[1]}.png")
        if os.path.exists(p):
            return p
    raise FileNotFoundError(key)


def wall(mat, season, levels, rule, now_n):
    bands = levels * 2
    W = 14
    im = Image.new("RGBA", (W * 64, bands * 32), (0, 0, 0, 0))
    stacks = []
    for i in range(W):
        tx, ty = 10 + i, 40
        h0 = RR.dhash(tx, ty)
        col = []
        for b in range(bands):
            part = ("top" if b == 0 else "mid") + ("-base" if b == bands - 1 else "")
            v = h0 % now_n if rule == "now" else (h0 + b) % 3
            p = key_file(mat, season, f"{part}.8{VAR[v]}")
            t = ld(p)
            im.alpha_composite(t, (i * 64, b * 32))
            col.append((part, np.array(t)))
        stacks.append(col)
    return im, stacks


def measure(im, stacks):
    same = []
    for col in stacks:
        mids = [a for part, a in col if part == "mid"]
        for a, b in zip(mids, mids[1:]):
            same.append((a == b).all(-1).mean())
    a = np.array(im).astype(np.int64)
    op = a[..., 3] == 255
    Y = a[..., :3] @ np.array([0.2126, 0.7152, 0.0722])
    pairs = []
    for d in ((0, 1), (1, 0)):
        A = Y[: Y.shape[0] - d[0], : Y.shape[1] - d[1]]
        B = Y[d[0]:, d[1]:]
        m = op[: Y.shape[0] - d[0], : Y.shape[1] - d[1]] & op[d[0]:, d[1]:]
        pairs.append(np.abs(A - B)[m])
    p = np.concatenate(pairs)
    return (float(np.mean(same)) if same else None), {t: float((p > t).mean()) for t in (10, 12, 14, 15)}


def dominant(mat, season):
    out = 0.0
    for v in VAR:
        a = np.array(ld(key_file(mat, season, f"mid.8{v}"))).astype(np.int64)
        k = (a[..., 0] << 16) | (a[..., 1] << 8) | a[..., 2]
        out = max(out, np.unique(k, return_counts=True)[1].max() / k.size)
    return out


def main(out):
    os.makedirs(out, exist_ok=True)
    for mat, season, now_n in (("desert", "summer", 2), ("earth", "summer", 3), ("earth", "autumn", 3), ("earth", "winter", 3)):
        print(f"{mat} {season}: dominant colour in a mid.8 band (max over variants) {100 * dominant(mat, season):.1f}%")
        for rule in ("now", "per-band"):
            for levels in (1, 2, 3):
                im, st = wall(mat, season, levels, rule, now_n)
                s, steps = measure(im, st)
                tag = f"wall_{mat}{'' if season == 'summer' else '_' + season}_{rule}_{levels}levels"
                if season == "summer" or levels == 3:
                    im.resize((im.width * 2, im.height * 2), Image.NEAREST).save(os.path.join(out, tag + "_k2.png"))
                    im.save(os.path.join(out, tag + "_k1.png"))
                print(f"  {rule:8s} {levels} levels: same between stacked mid bands "
                      f"{'-' if s is None else f'{100 * s:.1f}%'}; steps >10 {100 * steps[10]:.1f}% >12 {100 * steps[12]:.1f}%"
                      f" >14 {100 * steps[14]:.1f}% >15 {100 * steps[15]:.1f}%")


if __name__ == "__main__":
    main(sys.argv[1])
