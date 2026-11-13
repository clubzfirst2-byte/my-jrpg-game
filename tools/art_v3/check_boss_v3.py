"""Reference numbers for the v3 bosses (no pass / fail here: the independent inspection decides).
Run after gen_boss_v3.py: python3 tools/art_v3/check_boss_v3.py [kind]
"""

import glob
import io
import os
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "boss_v3"))
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

import palette  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "src", "art-release-v3", "boss")
V2 = "d900394"
GLOW = {"glow"}


def luma(a):
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def v2img(name):
    blob = subprocess.run(["git", "-C", ROOT, "show", f"{V2}:src/art-release-v2/enemy/{name}.png"],
                          capture_output=True, check=True).stdout
    return np.array(Image.open(io.BytesIO(blob)).convert("RGBA"))


def components(m):
    """8-connected components of a mask -> list of sizes."""
    h, w = m.shape
    seen = np.zeros((h, w), bool)
    sizes = []
    for y, x in zip(*np.nonzero(m)):
        if seen[y, x]:
            continue
        st, n = [(y, x)], 0
        seen[y, x] = True
        while st:
            a, b = st.pop()
            n += 1
            for p in range(max(0, a - 1), min(h, a + 2)):
                for q in range(max(0, b - 1), min(w, b + 2)):
                    if m[p, q] and not seen[p, q]:
                        seen[p, q] = True
                        st.append((p, q))
        sizes.append(n)
    return sizes


def isolated(a):
    """Clusters of 1-2 texels of one colour whose outside neighbours are all opaque and whose luma is
    12+ away from their mean (the inspection's 'isolated point'), per 1000 opaque texels."""
    op = a[..., 3] == 255
    key = (a[..., 0].astype(int) << 16) | (a[..., 1].astype(int) << 8) | a[..., 2]
    L = luma(a.astype(float))
    h, w = op.shape
    seen = np.zeros((h, w), bool)
    n = 0
    for y, x in zip(*np.nonzero(op)):
        if seen[y, x]:
            continue
        comp, st = [(y, x)], [(y, x)]
        seen[y, x] = True
        while st and len(comp) <= 2:
            p, q = st.pop()
            for r, s in ((p + 1, q), (p - 1, q), (p, q + 1), (p, q - 1)):
                if 0 <= r < h and 0 <= s < w and not seen[r, s] and op[r, s] and key[r, s] == key[y, x]:
                    seen[r, s] = True
                    comp.append((r, s))
                    st.append((r, s))
        if len(comp) > 2:
            continue
        cs, nb, ok = set(comp), [], True
        for p, q in comp:
            for r, s in ((p + 1, q), (p - 1, q), (p, q + 1), (p, q - 1)):
                if (r, s) in cs:
                    continue
                if not (0 <= r < h and 0 <= s < w) or not op[r, s]:
                    ok = False
                else:
                    nb.append(L[r, s])
        if ok and nb and abs(sum(nb) / len(nb) - L[y, x]) >= 12:
            n += 1
    return 1000.0 * n / max(1, op.sum())


def win_colours(a, s=32, step=16):
    out = []
    for y in range(0, a.shape[0] - s + 1, step):
        for x in range(0, a.shape[1] - s + 1, step):
            b = a[y:y + s, x:x + s]
            op = b[..., 3] == 255
            if op.mean() < 0.9:
                continue
            out.append(len({tuple(c) for c in b[op][:, :3]}))
    return out


def block22(a):
    """Share of aligned 2x2 blocks (all opaque) that are not one colour."""
    h, w = a.shape[:2]
    b = a[:h // 2 * 2, :w // 2 * 2].reshape(h // 2, 2, w // 2, 2, 4).transpose(0, 2, 1, 3, 4).reshape(h // 2, w // 2, 4, 4)
    op = (b[..., 3] == 255).all(-1)
    same = (b[..., :3] == b[:, :, :1, :3]).all(-1).all(-1)
    return float((~same & op).sum() / max(1, op.sum()))


def main():
    kind = sys.argv[1] if len(sys.argv) > 1 else "boss_root"
    files = sorted(glob.glob(os.path.join(OUT, f"enemy.{kind}.*.png")))
    names = [os.path.basename(f)[:-4] for f in files]
    v2 = sorted(os.path.basename(x)[:-4] for x in subprocess.run(
        ["git", "-C", ROOT, "ls-tree", "-r", "--name-only", V2, "src/art-release-v2/enemy/"],
        capture_output=True, text=True, check=True).stdout.split() if f"enemy.{kind}." in x)
    print(f"keys: v3 {len(names)}, v2 {len(v2)}, extra {sorted(set(names) - set(v2))}, missing {sorted(set(v2) - set(names))}")
    rev = {}
    for m, r in palette.RAMPS.items():
        for i, c in enumerate(r):
            rev.setdefault(tuple(c), []).append((m, i))
    imgs = {n: np.array(Image.open(f).convert("RGBA")) for n, f in zip(names, files)}
    raw_modes = {Image.open(f).mode for f in files}
    print("png modes:", raw_modes)
    tot = dict(size=[], semi=0, off=0, top=[], left=[], right=[], bottom=[], frag=[], ring_min=999.0, ring_lt30=0, mid=0)
    tones = {}
    per = {}
    for n, a in imgs.items():
        v = v2img(n)
        if a.shape[0] != 2 * v.shape[0] or a.shape[1] != 2 * v.shape[1]:
            tot["size"].append(n)
        al = a[..., 3]
        op = al == 255
        tot["semi"] += int(((al > 0) & (al < 255)).sum())
        cols = {tuple(c) for c in a[op][:, :3]}
        tot["off"] += len([c for c in cols if c not in rev])
        for c in cols:
            for m, i in rev.get(c, []):
                tones.setdefault(m, set()).add(i)
        if op[0].any():
            tot["top"].append(n)
        if op[:, 0].any():
            tot["left"].append(n)
        if op[:, -1].any():
            tot["right"].append(n)
        low = int(np.nonzero(op.any(1))[0].max())
        vlow = 2 * int(np.nonzero((v[..., 3] > 0).any(1))[0].max()) + 1
        if low != vlow:
            tot["bottom"].append((n, low, vlow))
        cs = components(op)
        small = sorted(c for c in cs if c < 12)
        if small:
            tot["frag"].append((n, small))
        # the silhouette ring
        pad = np.pad(op, 1)
        inner = pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:]
        ring = op & ~inner
        glow0 = tuple(palette.RAMPS["glow"][0])
        L = luma(a.astype(float))
        tot["ring_min"] = min(tot["ring_min"], float(L[ring].min()))
        tot["ring_lt30"] += int((L[ring] < 30).sum())
        # in-between tones outside a 3x3 block of themselves
        key = (a[..., 0].astype(int) << 16) | (a[..., 1].astype(int) << 8) | a[..., 2]
        for m, r in palette.RAMPS.items():
            for i in (2, 4):
                k = (r[i][0] << 16) | (r[i][1] << 8) | r[i][2]
                sel = op & (key == k)
                if not sel.any():
                    continue
                ok = np.zeros_like(sel)
                s = sel
                blk = s[:-2, :-2] & s[:-2, 1:-1] & s[:-2, 2:] & s[1:-1, :-2] & s[1:-1, 1:-1] & s[1:-1, 2:] & s[2:, :-2] & s[2:, 1:-1] & s[2:, 2:]
                for dy in range(3):
                    for dx in range(3):
                        ok[dy:dy + blk.shape[0], dx:dx + blk.shape[1]] |= blk
                tot["mid"] += int((sel & ~ok).sum())
        per[n] = dict(colours=len(cols), iso=isolated(a), b22=block22(a), meanL=float(L[op].mean()), sdL=float(L[op].std()),
                      area=int(op.sum()))
    print("size not 2x v2:", tot["size"])
    print("semi-transparent texels:", tot["semi"], " colours outside the ramps:", tot["off"])
    print("tones used per material:", {m: len(t) for m, t in tones.items()})
    print("in-between tones outside a 3x3 block (texels, all frames):", tot["mid"],
          "(a part's block can be covered by the part in front of it)")
    print("silhouette ring: darkest luma", round(tot["ring_min"], 1), " texels under 30:", tot["ring_lt30"])
    print("edges -- frames with texels on the top row:", tot["top"], " left column:", len(tot["left"]), tot["left"][:4],
          " right column:", len(tot["right"]), tot["right"][:4])
    print("lowest row differs from v2 x 2 (name, v3, v2x2+1):", tot["bottom"])
    print("fragments (frames with separate pieces under 12 texels):", tot["frag"])
    cs_n = {n: len(components(imgs[n][..., 3] == 255)) for n in names}
    print("frames with more than 1 separate piece (orbs, chips are meant):", {n: c for n, c in cs_n.items() if c > 1})
    # identical frames
    same = []
    ns = [n for n in names if len(n.split(".")) > 3]
    for i, p in enumerate(ns):
        for q in ns[i + 1:]:
            if np.array_equal(imgs[p], imgs[q]):
                same.append((p, q))
    print("identical frames (any pair, the minimal pair aside):", same)
    cn = [per[n]["colours"] for n in ns]
    print(f"colours per frame: {min(cn)}-{max(cn)} (median {int(np.median(cn))})")
    idle = [f"enemy.{kind}.idle.{i}" for i in range(4)]
    c32 = [c for n in idle for c in win_colours(imgs[n])]
    c32v = [c for n in idle for c in win_colours(v2img(n), 16, 8)]
    print(f"32x32 window colours (idle, windows 90%+ opaque): median {np.median(c32):.1f}, min {min(c32)}, max {max(c32)}"
          f"  | v2 16x16: median {np.median(c32v):.1f}")
    ag = tt = 0
    for n in idle:
        v = v2img(n).repeat(2, 0).repeat(2, 1)
        a = imgs[n]
        both = (a[..., 3] == 255) & (v[..., 3] == 255)
        ag += int(((a[..., :3] == v[..., :3]).all(-1) & both).sum())
        tt += int(both.sum())
    print(f"agreement with v2 x 2 (same colour, idle): {ag / tt:.3f}")
    vL = [luma(v2img(n).astype(float))[v2img(n)[..., 3] > 0] for n in idle]
    print(f"luma idle: v3 mean {np.mean([per[n]['meanL'] for n in idle]):.1f} sd {np.mean([per[n]['sdL'] for n in idle]):.1f}"
          f"  | v2 mean {np.mean([x.mean() for x in vL]):.1f} sd {np.mean([x.std() for x in vL]):.1f}")
    print(f"isolated points per 1000 (idle): {[round(per[n]['iso'], 1) for n in idle]}  2x2 not one colour: {[round(per[n]['b22'], 2) for n in idle]}")
    # shape change against idle 0 (silhouette XOR / idle area), v3 and v2
    base, vbase = imgs[idle[0]][..., 3] == 255, v2img(idle[0])[..., 3] > 0
    print("silhouette change against idle 0, % of idle area (v3 / v2):")
    acts = {}
    for n in ns:
        acts.setdefault(".".join(n.split(".")[2:-1]), []).append(n)
    for act, fl in acts.items():
        d3 = [100 * ((imgs[n][..., 3] == 255) ^ base).sum() / base.sum() for n in fl]
        d2 = [100 * ((v2img(n)[..., 3] > 0) ^ vbase).sum() / vbase.sum() for n in fl]
        print(f"  {act:14s} " + " ".join(f"{a:.0f}/{b:.0f}" for a, b in zip(d3, d2)))
    # carried parts: the back (rows above the head) of idle n against idle 0, shifted by the body's bob
    print("idle: the part of the body above row 76 against idle 0 after moving it by the bob (texels that differ, %):")
    A = imgs[idle[0]]
    for n in idle[1:]:
        best = None
        for dy in range(-4, 5):
            B = np.roll(imgs[n], -dy, 0)
            d = (A[4:76] != B[4:76]).any(-1).sum() / max(1, (A[4:76, :, 3] == 255).sum())
            best = d if best is None else min(best, d)
        print(f"  {n}: {100 * best:.2f}")
    raw = sum(a.shape[0] * a.shape[1] * 4 for n, a in imgs.items() if n in ns)
    trim = 0
    for n in ns:
        op = imgs[n][..., 3] == 255
        ys, xs = np.nonzero(op.any(1))[0], np.nonzero(op.any(0))[0]
        trim += (ys.max() - ys.min() + 1) * (xs.max() - xs.min() + 1) * 4
    print(f"memory: {len(ns)} frames (the minimal pair shares idle.0 / move.0): full frames {raw / 1e6:.3f} MB, +10% {raw * 1.1 / 1e6:.3f} MB;"
          f" trimmed to the opaque box {trim / 1e6:.3f} MB, +10% {trim * 1.1 / 1e6:.3f} MB")
    print(f"png bytes: {sum(os.path.getsize(f) for f in files) / 1e3:.1f} KB")


if __name__ == "__main__":
    main()
