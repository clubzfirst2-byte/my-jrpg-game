"""Machine check of the v3 desert (reference numbers only, no pass / fail).

  inventory   files per kind
  alpha       semi-transparent texels
  lone        opaque texels whose 4 neighbours are transparent (or outside)
  isolated    opaque texels whose 4 opaque neighbours are all of other colours (mech.py's rule), % of
              texels with 4 opaque neighbours
  palette     base / edge colours outside the desert ramps; flow shapes outside the grey 255
  holes       transparent pieces not touching the tile's edge (edges, flow); islands = opaque pieces of
              an edge overlay not touching the tile's edge
  tiny        flow: opaque pieces of 1-6 texels not touching the tile's edge
  border band the base patterns (256 x 256): share of marked texels (not the commonest colour) in the
              outer 6 + 6 rows / columns against the middle
  calm        base tiles: the share of the commonest colour (mean, max)
  edge inside edges: the commonest colour's share and the mean luma of the texels more than 5 from
              the cut, against the base tiles
  darkest     luma of the darkest opaque texel of trees / props (STYLE 3.3: background objects >= 36)
  sway        texels that differ between frame 0 and the other frames
  memory      the desert set resident (RGBA; 64 x 64 tiles: no packing waste, trees / props +10 %)
Run: python3 tools/art_v3/check_desert_v3.py
"""

import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

import gen_desert_v3 as D  # noqa: E402
from check_forest_v3 import luma, pieces  # noqa: E402

T = D.OUT


def load(p):
    return np.array(Image.open(p).convert("RGBA")).astype(np.int64)


def keyof(a):
    return (a[..., 0] << 16) | (a[..., 1] << 8) | a[..., 2]


def isolated(a):
    op = a[..., 3] == 255
    k = keyof(a)
    H, W = op.shape
    n = iso = 0
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            if not op[y, x]:
                continue
            nb = [(y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)]
            if not all(op[q] for q in nb):
                continue
            n += 1
            if all(k[q] != k[y, x] for q in nb):
                iso += 1
    return iso, n


def lone(a):
    op = a[..., 3] == 255
    p = np.pad(op, 1)
    nb = p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
    return int((op & ~nb).sum())


def main():
    files = {
        "base": sorted(glob.glob(os.path.join(T, "desert.sand.v3.[a-h][0-3][0-3].png"))),
        "edge": sorted(glob.glob(os.path.join(T, "desert.sand.v3.edge.*.png"))),
        "flow": sorted(glob.glob(os.path.join(T, "desert.sandflow.v3.*.png"))),
        "tree": sorted(glob.glob(os.path.join(T, "desert.tree.v3.*.png"))),
        "prop": sorted(glob.glob(os.path.join(T, "desert.prop.v3.*.png"))) + [os.path.join(T, "obj.cactus.png")],
    }
    r = D.ramps_for()
    ramp_cols = {tuple(int(v) for v in c) for k in ("sand", "fine", "stone", "straw") for c in r[k]}
    print("inventory", {k: len(v) for k, v in files.items()}, "total", sum(len(v) for v in files.values()))
    for kind, fs in files.items():
        alpha = lones = iso = isn = out_pal = holes = islands = tiny = 0
        dark = 999.0
        sizes = set()
        for f in fs:
            a = load(f)
            sizes.add(a.shape[1::-1])
            alpha += int(((a[..., 3] > 0) & (a[..., 3] < 255)).sum())
            lones += lone(a)
            i, n = isolated(a)
            iso, isn = iso + i, isn + n
            op = a[..., 3] == 255
            cols = {tuple(int(v) for v in c) for c in a[op][:, :3]}
            if kind in ("base", "edge"):
                out_pal += len(cols - ramp_cols)
            if kind == "flow":
                out_pal += len(cols - {(255, 255, 255)})
                tiny += sum(1 for (m, e) in pieces(op) if m <= 6 and not e)
            if kind in ("edge", "flow"):
                holes += sum(1 for (m, e) in pieces(~op) if not e)
            if kind == "edge":
                islands += sum(1 for (m, e) in pieces(op) if not e)
            if kind in ("tree", "prop"):
                dark = min(dark, float(luma(a[op]).min()))
        line = f"{kind:5s} files {len(fs):3d} sizes {sorted(sizes)} alpha {alpha} lone {lones} isolated {100.0 * iso / max(1, isn):.2f}%"
        if kind in ("base", "edge", "flow"):
            line += f" off-palette colours {out_pal}"
        if kind in ("edge", "flow"):
            line += f" holes {holes}"
        if kind == "edge":
            line += f" islands {islands}"
        if kind == "flow":
            line += f" tiny(<=6, off the edge) {tiny}"
        if kind in ("tree", "prop"):
            line += f" darkest luma {dark:.1f}"
        print(line)
    # calm tiles and the border band
    shares = []
    for f in files["base"]:
        k = keyof(load(f))
        shares.append(np.unique(k, return_counts=True)[1].max() / k.size)
    print(f"calm  commonest colour per base tile: mean {100 * np.mean(shares):.1f}% max {100 * max(shares):.1f}%"
          f" ({os.path.basename(files['base'][int(np.argmax(shares))])})")
    lo, hi = 9.0, 0.0
    for m in D.PATTERNS:
        big = np.zeros((256, 256), np.int64)
        for rr in range(4):
            for cc in range(4):
                big[rr * 64:rr * 64 + 64, cc * 64:cc * 64 + 64] = keyof(load(os.path.join(T, f"desert.sand.v3.{m}{rr}{cc}.png")))
        vals, cnt = np.unique(big, return_counts=True)
        marked = big != vals[np.argmax(cnt)]
        mid = marked[12:-12, 12:-12].mean()
        for band in (marked[:6].mean(), marked[-6:].mean(), marked[:, :6].mean(), marked[:, -6:].mean()):
            lo, hi = min(lo, band / mid), max(hi, band / mid)
    print(f"band  border 6-texel bands / middle, marks: {lo:.2f} .. {hi:.2f}")
    # edge insides against the base
    base_l = np.mean([luma(load(f)[..., :3].astype(float)).mean() for f in files["base"]])
    ins_share, ins_l = [], []
    for f in files["edge"]:
        a = load(f)
        op = a[..., 3] == 255
        d = np.full(op.shape, 9)
        d[~op] = 0
        for step in range(1, 6):
            prev = d < step
            g = np.zeros_like(prev)
            g[1:] |= prev[:-1]
            g[:-1] |= prev[1:]
            g[:, 1:] |= prev[:, :-1]
            g[:, :-1] |= prev[:, 1:]
            d[g & (d == 9)] = step
        inn = d > 5
        if inn.sum() < 200:
            continue
        k = keyof(a)[inn]
        ins_share.append(np.unique(k, return_counts=True)[1].max() / k.size)
        ins_l.append(luma(a[inn][:, :3].astype(float)).mean())
    print(f"edge  inside (>5 from the cut): commonest colour {100 * np.mean(ins_share):.1f}% (base {100 * np.mean(shares):.1f}%),"
          f" mean luma {np.mean(ins_l):.1f} (base {base_l:.1f})")
    # sway
    for kind in ("tree", "prop"):
        groups = {}
        for f in files[kind]:
            b = os.path.basename(f)
            if b.startswith("desert."):
                groups.setdefault(b.rsplit(".", 2)[0], []).append(f)
        for g, fs in sorted(groups.items()):
            if len(fs) > 1:
                a0 = load(fs[0])
                diffs = [int((load(f) != a0).any(-1).sum()) for f in fs[1:]]
                print(f"sway  {g.split('.v3.')[1]}: frames {len(fs)}, texels differing from frame 0 {diffs}")
    # memory
    tile = 64 * 64 * 4
    ground = (len(files["base"]) + len(files["edge"]) + len(files["flow"])) * tile
    obj = sum(Image.open(f).width * Image.open(f).height * 4 for f in files["tree"] + files["prop"] if "obj.cactus" not in f)
    print(f"memory ground {ground / 1e6:.3f} MB ({len(files['base'])} + {len(files['edge'])} + {len(files['flow'])} tiles of 64 x 64,"
          f" no packing waste); trees / props {obj / 1e6:.3f} MB, +10 % packing {obj * 1.1 / 1e6:.3f} MB"
          f" (obj.cactus = desert.prop.v3.cactus.0, counted once)")


if __name__ == "__main__":
    main()
