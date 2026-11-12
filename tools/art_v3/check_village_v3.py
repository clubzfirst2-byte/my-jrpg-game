"""Machine check of the v3 village art (gen_village_v3.py), reference numbers only (no pass / fail):
size against the current key (exactly 2x, the same feet), semi-transparent texels, colours, lone texels
(4 neighbours transparent), isolated colour texels (4 opaque neighbours all of other colours; the same
definition as the inspection's mech.py), holes (transparent pieces not touching the border), colours
outside the item's ramps, darkest luma (Rec.709), and the night glass of the houses.
Also the GPU memory of the village set per season (RGBA, +10% packing).
Run: python3 tools/art_v3/check_village_v3.py
"""

import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

import gen_village_v3 as V  # noqa: E402
from v3lib import ROOT  # noqa: E402

CUR = os.path.join(ROOT, "src", "art-release", "objects")


def luma(rgb):
    return 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]


def components(m):
    h, w = m.shape
    lab = np.zeros((h, w), np.int32)
    n = 0
    sizes, border = [], []
    for y in range(h):
        for x in range(w):
            if m[y, x] and not lab[y, x]:
                n += 1
                st, cnt, b = [(y, x)], 0, False
                lab[y, x] = n
                while st:
                    a, c = st.pop()
                    cnt += 1
                    b |= a in (0, h - 1) or c in (0, w - 1)
                    for p, q in ((a + 1, c), (a - 1, c), (a, c + 1), (a, c - 1)):
                        if 0 <= p < h and 0 <= q < w and m[p, q] and not lab[p, q]:
                            lab[p, q] = n
                            st.append((p, q))
                sizes.append(cnt)
                border.append(b)
    return sizes, border


def analyse(path, season):
    a = np.array(Image.open(path).convert("RGBA")).astype(np.int64)
    al = a[..., 3]
    op = al == 255
    rgb = a[..., :3]
    key = np.where(op, (rgb[..., 0] << 16) | (rgb[..., 1] << 8) | rgb[..., 2], -1)
    pad = np.pad(op, 1)
    nbr = pad[:-2, 1:-1].astype(int) + pad[2:, 1:-1] + pad[1:-1, :-2] + pad[1:-1, 2:]
    kp = np.pad(key, 1, constant_values=-1)
    nb = [kp[:-2, 1:-1], kp[2:, 1:-1], kp[1:-1, :-2], kp[1:-1, 2:]]
    allop = np.all([n >= 0 for n in nb], axis=0) & op
    diff = np.all([n != key for n in nb], axis=0)
    hs, hb = components(al == 0)
    holes = [s for s, b in zip(hs, hb) if not b]
    pal = {tuple(int(v) for v in c) for r in V.ramps_for(season).values() for c in r}
    cols = {tuple(int(v) for v in c) for c in rgb[op]}
    return dict(size=(a.shape[1], a.shape[0]), semi=int(((al > 0) & (al < 255)).sum()), colours=len(cols),
                lone=int((op & (nbr == 0)).sum()), iso=round(100 * float((allop & diff).sum()) / max(1, int(allop.sum())), 2),
                holes=len(holes), hole_px=sum(holes), off=len(cols - pal),
                minL=round(float(luma(rgb[op]).min()), 1), meanL=round(float(luma(rgb[op]).mean()), 1),
                opaque=int(op.sum()))


def main():
    rows = []
    for key, fn, seasons in V.ITEMS:
        for s in ("summer", "autumn", "winter"):
            f = f"{V.PREFIX[s]}{key}.png"
            p = os.path.join(V.OUT, f)
            if not os.path.exists(p):
                continue
            r = analyse(p, s)
            cur = os.path.join(CUR, key + ".png")
            if os.path.exists(cur):
                cw, ch = Image.open(cur).size
                r["now"] = f"{cw}x{ch}"
                r["x2"] = r["size"] == (2 * cw, 2 * ch)
            else:
                r["now"], r["x2"] = "new", None
            r["f"] = f
            rows.append(r)
    print(f"{'file':42s} {'size':8s} {'now':6s} x2  semi col  lone iso%  holes(px) off minL  meanL")
    for r in rows:
        print(f"{r['f']:42s} {r['size'][0]}x{r['size'][1]:<4d} {r['now']:6s} {str(r['x2'])[0]:2s} "
              f"{r['semi']:4d} {r['colours']:3d} {r['lone']:5d} {r['iso']:5.2f} {r['holes']:2d}({r['hole_px']:4d}) "
              f"{r['off']:3d} {r['minL']:5.1f} {r['meanL']:5.1f}")
    # state pairs: changed texels over the union of opaque ones, mean |luma difference| over that union
    print("\nstate pairs (changed % of the opaque union, mean |dL| over it):")
    for a_, b_ in (("obj.chest.closed", "obj.chest.open"), ("sw.plate.off", "sw.plate.on"),
                   ("obj.checkpoint.off", "obj.checkpoint.on"), ("obj.campfire.0", "obj.campfire.1"),
                   ("obj.brazier.0", "obj.brazier.1")):
        for name, d in (("now", CUR), ("v3", V.OUT), ("v3 winter", V.OUT)):
            pre = "winter." if name == "v3 winter" else ""
            def ld(k):  # a season without its own file falls back to the summer file
                f = os.path.join(d, pre + k + ".png")
                return np.array(Image.open(f if os.path.exists(f) else os.path.join(d, k + ".png")).convert("RGBA")).astype(float)
            x, y = ld(a_), ld(b_)
            op = (x[..., 3] > 0) | (y[..., 3] > 0)
            df = (x != y).any(-1) & op
            dl = np.abs(luma(x) * (x[..., 3] > 0) - luma(y) * (y[..., 3] > 0))
            print(f"  {a_:20s} {name:10s} {100 * df.sum() / op.sum():5.1f}%  {dl[op].mean():5.1f}")
    # snow faces of the roofs: share of the 2 commonest colours
    print("\nwinter roof snow (texels of the snow ramp above the eaves): share of the 2 commonest colours")
    snow = {tuple(int(v) for v in c) for c in V.SNOW}
    for f, eave in (("winter.obj.house.png", V.H_ROOF_BOT), ("winter.obj.v3.house_stone.png", V.HS.ROOF_BOT)):
        a = np.array(Image.open(os.path.join(V.OUT, f)).convert("RGBA"))[:eave]
        cols = [tuple(int(v) for v in p[:3]) for p in a.reshape(-1, 4) if p[3] == 255 and tuple(int(v) for v in p[:3]) in snow]
        cnt = sorted(collections.Counter(cols).values(), reverse=True)
        print(f"  {f:34s} {len(cols)} texels, {len(cnt)} colours, top 2 = {100 * sum(cnt[:2]) / len(cols):.1f}%")
    # night glass
    tab = json.load(open(V.DOC))["houses"]
    print("\nnight glass (houseWindows.glassKind):")
    for k, t in tab.items():
        lit = sum(w["lit"] for w in t["windows"])
        print(f"  {k:32s} windows {len(t['windows'])}  lit {lit}  glints unlit {sum(w['glints_unlit'] for w in t['windows'])}"
              f" (per window {min(w['glints_unlit'] for w in t['windows'])}-{max(w['glints_unlit'] for w in t['windows'])})"
              f"  lit-but-not-glass in windows {sum(w['lit_not_glass'] for w in t['windows'])}"
              f"  glass-like texels outside the windows {t['lit_like_outside_windows']}")
    # memory: one season resident (the summer files, or the season's own where it has one)
    print("\nGPU memory, one season resident (RGBA, +10% packing):")
    for s in ("summer", "autumn", "winter"):
        tot = 0
        for key, fn, seasons in V.ITEMS:
            f = os.path.join(V.OUT, f"{V.PREFIX[s]}{key}.png")
            if not os.path.exists(f):
                f = os.path.join(V.OUT, f"{key}.png")
            w, h = Image.open(f).size
            tot += w * h * 4
        print(f"  {s:7s} {len(V.ITEMS)} images  {tot / 1e6:.3f} MB raw  {tot * 1.1 / 1e6:.3f} MB with packing")
    json.dump(rows, open(os.path.join(os.path.dirname(V.DOC), ".village_check.json"), "w"), default=str) if False else None


if __name__ == "__main__":
    main()
