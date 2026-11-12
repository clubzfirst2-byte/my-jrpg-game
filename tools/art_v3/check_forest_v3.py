"""Machine check of the v3 forest (reference numbers only, no pass / fail).

  inventory   files per kind and season
  alpha       semi-transparent texels
  lone        opaque texels whose 4 neighbours are transparent (or outside)
  isolated    opaque texels whose 4 opaque neighbours are all of other colours (mech.py's rule), % of
              texels with 4 opaque neighbours
  palette     base / edge colours outside the forest ramps; flow shapes outside the greys 214 / 234 / 255
  holes       transparent pieces not touching the tile's edge (edges, flow); islands = opaque pieces of
              an edge overlay not touching the tile's edge
  tiny        flow: opaque pieces of 1-3 texels not touching the tile's edge
  border band the base patterns (256 x 256): share of marked texels (not the base tone 3) in the
              outer 6 + 6 texels of rows / columns against the middle (1.0 = even; a band near 0 is a
              256-texel grid)
  calm        base tiles: the share of the commonest colour (max over tiles)
  snow        winter trees / props: snow pieces under 4 texels
  darkest     luma of the darkest opaque texel of trees / props (STYLE 3.3: background objects >= 36)
  memory      one season of the forest set resident (RGBA, +10 % packing)
Run: python3 tools/art_v3/check_forest_v3.py
"""

import collections
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

import gen_forest_v3 as F  # noqa: E402

T = F.OUT


def luma(a):
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def pieces(m):
    h, w = m.shape
    seen = np.zeros_like(m)
    out = []
    for y in range(h):
        for x in range(w):
            if m[y, x] and not seen[y, x]:
                st, n, edge = [(y, x)], 0, False
                seen[y, x] = True
                while st:
                    a, b = st.pop()
                    n += 1
                    edge |= a in (0, h - 1) or b in (0, w - 1)
                    for c, d in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                        if 0 <= c < h and 0 <= d < w and m[c, d] and not seen[c, d]:
                            seen[c, d] = True
                            st.append((c, d))
                out.append((n, edge))
    return out


def basic(a):
    al = a[..., 3]
    op = al == 255
    rgb = a[..., :3].astype(np.int64)
    key = np.where(op, (rgb[..., 0] << 16) | (rgb[..., 1] << 8) | rgb[..., 2], -1)
    pad = np.pad(op, 1)
    nbr = pad[:-2, 1:-1].astype(int) + pad[2:, 1:-1] + pad[1:-1, :-2] + pad[1:-1, 2:]
    kp = np.pad(key, 1, constant_values=-1)
    nb = [kp[:-2, 1:-1], kp[2:, 1:-1], kp[1:-1, :-2], kp[1:-1, 2:]]
    allop = np.all([n >= 0 for n in nb], axis=0) & op
    iso = int((allop & np.all([n != key for n in nb], axis=0)).sum())
    return dict(semi=int(((al > 0) & (al < 255)).sum()), lone=int((op & (nbr == 0)).sum()), iso=iso,
                isoden=int(allop.sum()), cols={tuple(int(v) for v in c) for c in a[op][:, :3]}, op=op)


def group(f):
    g = f.split(".")
    s = g[0] if g[0] in ("autumn", "winter") else "summer"
    if ".grassflow." in f:
        return s if s == "winter" else "summer/autumn", "flow"
    if ".grass.v3.edge." in f:
        return s, "edge"
    if ".grass.v3." in f:
        return s, "base"
    if ".tree.v3." in f or f.endswith("forest.pine.png"):
        return s, "tree"
    if ".prop.v3." in f:
        return s, "prop"
    return s, "other"


def main():
    files = sorted(os.path.basename(p) for p in glob.glob(os.path.join(T, "*forest.*.png")))
    pal = {s: {tuple(int(v) for v in c) for r in F.ramps_for(s).values() for c in r} for s in F.PREFIX}
    agg = collections.defaultdict(lambda: collections.defaultdict(list))
    for f in files:
        s, g = group(f)
        a = np.array(Image.open(os.path.join(T, f)).convert("RGBA"))
        r = basic(a)
        A = agg[(s, g)]
        for k in ("semi", "lone", "iso", "isoden"):
            A[k].append(r[k])
        A["n"].append(1)
        A["size"].append(a.shape[1] * a.shape[0])
        if g in ("base", "edge"):
            A["off"].append(len(r["cols"] - pal[s]))
        elif g == "flow":
            A["off"].append(len(r["cols"] - {(214,) * 3, (234,) * 3, (255,) * 3}))
        else:
            A["minL"].append(float(luma(a[r["op"]][:, :3].astype(float)).min()))
        if g in ("edge", "flow"):
            P = pieces(~r["op"])
            A["holes"].append(sum(1 for n, e in P if not e))
        if g == "edge":
            A["islands"].append(sum(1 for n, e in pieces(r["op"]) if not e))
        if g == "flow":
            A["tiny"].append(sum(1 for n, e in pieces(r["op"]) if n <= 3 and not e))
        if g == "base":
            rgb = a[..., :3].astype(np.int64)
            key = (rgb[..., 0] << 16) | (rgb[..., 1] << 8) | rgb[..., 2]
            A["calm"].append(np.unique(key, return_counts=True)[1].max() / key.size)
    print(f"{'season':14s} {'kind':5s} {'n':>4s} semi lone  iso%  off holes islands tiny  calm(max) minL")
    for (s, g), A in sorted(agg.items()):
        print(f"{s:14s} {g:5s} {sum(A['n']):4d} {sum(A['semi']):4d} {sum(A['lone']):4d} "
              f"{100 * sum(A['iso']) / max(1, sum(A['isoden'])):5.2f} {sum(A['off']) if A['off'] else '-':>4} "
              f"{sum(A['holes']) if A['holes'] else '-':>5} {sum(A['islands']) if A['islands'] else '-':>7} "
              f"{sum(A['tiny']) if A['tiny'] else '-':>4}  {max(A['calm']) if A['calm'] else 0:6.3f}   "
              f"{min(A['minL']) if A['minL'] else '-'}")
    # the border band of the base patterns
    print("\nbase patterns: marked share in the outer 6 + 6 texels / the middle (rows, columns)")
    for s, pre in F.PREFIX.items():
        rs, cs = [], []
        for m in F.PATTERNS:
            big = np.zeros((256, 256), bool)
            for r in range(4):
                for c in range(4):
                    a = np.array(Image.open(os.path.join(T, f"{pre}forest.grass.v3.{m}{r}{c}.png")).convert("RGB")).astype(int)
                    base = np.array(F.ramps_for(s)["moss"][3])
                    big[r * 64:r * 64 + 64, c * 64:c * 64 + 64] = (np.abs(a - base).sum(-1) > 0)
            band_r = np.r_[big[:6].mean(), big[-6:].mean()].mean()
            band_c = np.r_[big[:, :6].mean(), big[:, -6:].mean()].mean()
            mid = big[64:192, 64:192].mean()
            rs.append(band_r / mid)
            cs.append(band_c / mid)
        print(f"  {s:7s} rows {min(rs):.2f}-{max(rs):.2f}  columns {min(cs):.2f}-{max(cs):.2f}")
    # winter snow crumbs
    # the snow tones 1-6 (tone 0 is the snow's outline, not a piece of snow)
    snow_rgb = {tuple(int(v) for v in c) for c in F.G.lift_ramp(["#3a4866", "#7a8cae", "#99abc7", "#b8c8e0", "#cadbe9", "#dce6f2", "#f8fbff"])[1:]}
    crumbs = 0
    for f in files:
        s, g = group(f)
        if s != "winter" or g not in ("tree", "prop"):
            continue
        a = np.array(Image.open(os.path.join(T, f)).convert("RGBA"))
        m = np.zeros(a.shape[:2], bool)
        for y, x in zip(*np.nonzero(a[..., 3] == 255)):
            m[y, x] = tuple(int(v) for v in a[y, x, :3]) in snow_rgb
        crumbs += sum(1 for n, e in pieces(m) if n < 4)
    print(f"\nwinter trees / props: snow pieces under 4 texels: {crumbs}")
    # memory: one season resident
    print("\nGPU memory, one season resident (RGBA, +10 % packing):")
    for s, pre in F.PREFIX.items():
        fs = [f for f in files if group(f)[0] in (s, "summer/autumn" if s != "winter" else "winter")]
        tot = collections.Counter()
        for f in fs:
            if f.endswith("forest.pine.png"):  # the alias of pine_s frame 0: the same texture
                continue
            w, h = Image.open(os.path.join(T, f)).size
            tot[group(f)[1]] += w * h * 4 * 1.1
        print(f"  {s:7s} " + "  ".join(f"{k} {v / 1e6:.3f}" for k, v in sorted(tot.items())) + f"   total {sum(tot.values()) / 1e6:.3f} MB")


if __name__ == "__main__":
    main()
