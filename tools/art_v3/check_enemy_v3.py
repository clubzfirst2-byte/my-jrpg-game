"""Machine check of the v3 normal enemies and shots (gen_enemy_v3.py). Reference numbers only.

  keys        the same keys as v2's normal enemies + shots + the minimal pair (d900394, via git)
  size        exactly 2x the v2 frame of the same key
  alpha       semi-transparent texels (must be 0)
  tones       colours per material ramp (normal enemies: at most 6, STYLE 5.4)
  mid 3x3     in-between ramp tones (rig.MID) outside a 3x3 block of themselves (rig-drawn kinds)
  outline     the outer ring (opaque texels touching transparency): darkest luma, share < 30
  contrast    mean luma of the body (all opaque texels) against the mean luma of the v3 ground
  isolated    opaque texels whose 4 opaque neighbours are all of other colours (mech.py's rule)
  2x2         share of 2x2 blocks that are not one colour (0 for a plain 2x enlargement)
  frames      every frame of an action differs from its neighbours
  memory      RGBA bytes of the set (+10% packing), against STYLE 10.2
Run: python3 tools/art_v3/check_enemy_v3.py
"""

import collections
import glob
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "enemy_v3"))
sys.path.insert(1, HERE)
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from rig import MID, RGBV3  # noqa: E402
from slime_v3 import RAMPS as SLIME_RAMPS  # noqa: E402
from v3lib import ROOT, block_detail, ramp  # noqa: E402

OUT = os.path.join(ROOT, "src", "art-release-v3", "enemy")
TERR = os.path.join(ROOT, "src", "art-release-v3", "terrain")
V2REF = "d900394"


def luma(a):
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def v2_list():
    out = subprocess.run(["git", "-C", ROOT, "ls-tree", "--name-only", f"{V2REF}:src/art-release-v2/enemy"],
                         capture_output=True, text=True, check=True).stdout.split()
    return {f[:-4] for f in out if f.endswith(".png") and "boss" not in f}


def v2_size(name):
    blob = subprocess.run(["git", "-C", ROOT, "show", f"{V2REF}:src/art-release-v2/enemy/{name}.png"],
                          capture_output=True, check=True).stdout
    return Image.open(io.BytesIO(blob)).size


def palette():
    """colour -> (material, index): the kinds' ramps (palette_v3), the slime's own and its eye inks."""
    import palette_v3
    from slime_v3 import EYE, EYE_D, EYE_W, PUPIL
    rev = {}
    for kind in ("beast", "archer", "sentinel", "shot"):
        for m, r in palette_v3.ramps_for(kind).items():
            for i, c in enumerate(r):
                rev.setdefault(tuple(int(v) for v in c), (m, i))
    for k, h in (("EYE", EYE), ("EYE_D", EYE_D), ("EYE_W", EYE_W), ("PUPIL", PUPIL)):
        rev.setdefault(tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)), ("slime.ink." + k, 0))
    for m, r in SLIME_RAMPS.items():
        for i, c in enumerate(ramp(r)):
            rev.setdefault(tuple(c), ("slime." + m, i))
    return rev


def ground_luma():
    out = {}
    for s, pre in (("summer", ""), ("autumn", "autumn."), ("winter", "winter.")):
        fs = glob.glob(os.path.join(TERR, f"{pre}plains.grass.v3.[a-h][0-3][0-3].png"))
        vals = [luma(np.array(Image.open(f).convert("RGB")).astype(float)).mean() for f in fs]
        out[s] = float(np.mean(vals)) if vals else None
    return out


def analyse(a, rev):
    al = a[..., 3]
    op = al == 255
    rgb = a[..., :3].astype(np.int64)
    key = np.where(op, (rgb[..., 0] << 16) | (rgb[..., 1] << 8) | rgb[..., 2], -1)
    kp = np.pad(key, 1, constant_values=-1)
    nb = [kp[:-2, 1:-1], kp[2:, 1:-1], kp[1:-1, :-2], kp[1:-1, 2:]]
    allop = np.all([n >= 0 for n in nb], axis=0) & op
    iso = int((allop & np.all([n != key for n in nb], axis=0)).sum())
    ring = op & ~np.all([n >= 0 for n in nb], axis=0)
    L = luma(rgb.astype(float))
    mats = collections.defaultdict(set)
    off = 0
    mid_bad = 0
    lab = np.full(op.shape, -1)
    for y, x in zip(*np.nonzero(op)):
        c = tuple(int(v) for v in rgb[y, x])
        m = rev.get(c)
        if m is None:
            off += 1
            continue
        mats[m[0]].add(m[1])
    # in-between tones (rig ramps only) outside a 3x3 block of themselves
    H, W = op.shape
    for y, x in zip(*np.nonzero(op)):
        m = rev.get(tuple(int(v) for v in rgb[y, x]))
        if not m or m[0].startswith("slime.") or m[1] not in MID:
            continue
        ok = False
        for oy in range(-2, 1):
            for ox in range(-2, 1):
                y0, x0 = y + oy, x + ox
                if y0 >= 0 and x0 >= 0 and y0 + 3 <= H and x0 + 3 <= W and (key[y0:y0 + 3, x0:x0 + 3] == key[y, x]).all():
                    ok = True
        mid_bad += not ok
    return dict(semi=int(((al > 0) & (al < 255)).sum()), iso=iso, isoden=int(allop.sum()),
                tones=max((len(v) for k, v in mats.items() if not k.startswith("slime.")), default=0),
                slime_tones=max((len(v) for k, v in mats.items() if k.startswith("slime.")), default=0),
                off=off, mid_bad=mid_bad, ring_min=float(L[ring].min()) if ring.any() else None,
                ring_dark=int((ring & (L < 30)).sum()), ring_n=int(ring.sum()), meanL=float(L[op].mean()),
                blk=block_detail(Image.fromarray(a, "RGBA")), op=int(op.sum()), top=bool(op[0].any()),
                foot=int(np.nonzero(op.any(1))[0].max()), h=H)


def main():
    rev = palette()
    files = sorted(f[:-4] for f in os.listdir(OUT) if f.endswith(".png"))
    v2 = v2_list()
    print(f"keys: v3 {len(files)}, v2 normal enemies + shots + minimal {len(v2)}, "
          f"missing {sorted(v2 - set(files))}, extra {sorted(set(files) - v2)}")
    g = ground_luma()
    print("ground mean luma (v3 plains grass):", {k: round(v, 1) for k, v in g.items() if v})
    rows = {}
    bad_size = []
    for n in files:
        a = np.array(Image.open(os.path.join(OUT, n + ".png")).convert("RGBA"))
        w2, h2 = v2_size(n)
        if (a.shape[1], a.shape[0]) != (2 * w2, 2 * h2):
            bad_size.append(n)
        rows[n] = analyse(a, rev)
    print("size not 2x v2:", bad_size)
    by_kind = collections.defaultdict(list)
    for n, r in rows.items():
        by_kind[n.split(".")[1]].append((n, r))
    print(f"\n{'kind':9s} {'n':>3s} semi off tones(max) mid3x3 ringMinL ring<30 iso%  2x2   meanL  diff(summer/autumn/winter) top-row")
    for kind, lst in by_kind.items():
        R = [r for _, r in lst]
        meanL = np.mean([r["meanL"] for r in R if not False])
        diffs = "/".join(f"{meanL - g[s]:+.0f}" for s in ("summer", "autumn", "winter") if g[s])
        print(f"{kind:9s} {len(R):3d} {sum(r['semi'] for r in R):4d} {sum(r['off'] for r in R):3d} "
              f"{max(r['tones'] for r in R):3d}/{max(r['slime_tones'] for r in R)} {sum(r['mid_bad'] for r in R):6d} "
              f"{min(r['ring_min'] for r in R):8.1f} {sum(r['ring_dark'] for r in R):6d} "
              f"{100 * sum(r['iso'] for r in R) / max(1, sum(r['isoden'] for r in R)):5.2f} "
              f"{np.mean([r['blk'] for r in R]):.2f}  {meanL:6.1f}  {diffs:22s} {sum(r['top'] for r in R)}")
    # idle frames: mean luma per kind (the body against the ground)
    # distinct neighbouring frames
    same = []
    for n in files:
        p = n.split(".")
        if len(p) < 4:
            continue
        nxt = ".".join(p[:-1] + [str(int(p[-1]) + 1)])
        if nxt in rows:
            a = np.array(Image.open(os.path.join(OUT, n + ".png")))
            b = np.array(Image.open(os.path.join(OUT, nxt + ".png")))
            if np.array_equal(a, b):
                same.append((n, nxt))
    print("\nneighbouring frames that are identical:", same)
    tot = sum(rows[n]["op"] * 0 + np.prod(Image.open(os.path.join(OUT, n + ".png")).size) * 4 for n in files
              if len(n.split(".")) > 3)
    print(f"\nmemory: {len([n for n in files if len(n.split('.')) > 3])} frames (the minimal pair shares idle.0 / move.0), "
          f"{tot / 1e6:.3f} MB RGBA, {tot * 1.1 / 1e6:.3f} MB with packing")
    per = collections.Counter()
    for n in files:
        if len(n.split(".")) > 3:
            per[n.split(".")[1]] += np.prod(Image.open(os.path.join(OUT, n + ".png")).size) * 4 * 1.1
    print("  per kind (MB, +10%):", {k: round(v / 1e6, 3) for k, v in per.items()})


if __name__ == "__main__":
    main()
