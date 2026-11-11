"""Hand finishing on the 2x grid for remastered characters (STYLE.md 5.2): the details a v1 pixel
could not hold. Each function works on a Canvas made by v3lib.remaster() and on the v1 frame it came
from (to find the features: the eyes from the lash ink, the crown from the hair)."""

import math

import numpy as np

from v3lib import hx

# hi-res eye (8 x 6 texels): L lash, D iris dark, I iris, B iris light, K pupil, W shine, s skin,
# '.' keeps what is there. Same for both eyes, like the v1 eyes (shine on the right).
EYE = [
    ".LLLLLLL",
    "LLDDDDWL",
    "sDDKKWWs",
    "sDIKKIBs",
    "sDIIIBBs",
    "ssIBBBss",
]


def find_eyes(old, lash):
    """The v1 lash runs (row, x0, x1) of both eyes."""
    a = np.array(old.convert("RGBA"))
    H, W = a.shape[:2]
    runs = []
    for y in range(H):
        x = 0
        while x < W:
            if tuple(a[y, x, :3]) == lash and a[y, x, 3]:
                x0 = x
                while x < W and tuple(a[y, x, :3]) == lash and a[y, x, 3]:
                    x += 1
                if x - x0 >= 3:
                    runs.append((y, x0, x - 1))
            else:
                x += 1
    return runs


def eyes(c, old, inks, skin=("skin", 3)):
    """inks: dict with lash, dark, iris, light, pupil, shine colours (hex)."""
    lash = hx(inks["lash"])
    leg = {"L": inks["lash"], "D": inks["dark"], "I": inks["iris"], "B": inks["light"], "K": inks["pupil"],
           "W": inks["shine"]}
    for (y, x0, x1) in find_eyes(old, lash):
        X0, Y0 = 2 * x0, 2 * y
        for j, row in enumerate(EYE):
            for i, ch in enumerate(row):
                x, yy = X0 + i, Y0 + j
                if ch == "." or not (0 <= x < c.w and 0 <= yy < c.h):
                    continue
                if ch == "s":
                    c.put(x, yy, *skin)
                else:
                    c.mat[yy, x] = c.mid("_ink")
                    c.ink[(x, yy)] = hx(leg[ch])


def hair_strands(c, mat="hair", crown=None, n=30, width=0.13, lift=1):
    """Radial strands from the crown: a darker groove between locks and a lit edge beside it, only on
    the base/light tones (shadows stay calm)."""
    k = c.mid(mat)
    sel = c.mat == k
    if not sel.any():
        return
    ys, xs = np.nonzero(sel)
    if crown is None:
        crown = (xs.mean(), ys.min() + 2)
    cx, cy = crown
    for y, x in zip(ys, xs):
        t = int(c.tone[y, x])
        if t < 3 or t >= 5:
            continue
        th = math.atan2(y + 0.5 - cy, x + 0.5 - cx)
        s = (th / (2 * math.pi) * n) % 1.0
        r = math.hypot(x - cx, y - cy)
        if r < 4:
            continue
        if s < width:
            c.tone[y, x] = t - 1
        elif s < width * 2 and t == 3 and lift:
            c.tone[y, x] = 4


def glints(c, mat, every=5, tone=5, phase=0):
    """Tone-5 glints along the lit texels of a trim (embroidery / metal studs)."""
    k = c.mid(mat)
    ys, xs = np.nonzero((c.mat == k) & (c.tone >= 4))
    for y, x in zip(ys, xs):
        if (x + y + phase) % every == 0:
            c.tone[y, x] = tone


def cloth_weave(c, mat, tones=(3,), period=(4, 3)):
    """A calm 2-texel thread texture on large base areas (no checkerboard: short dashes along rows)."""
    k = c.mid(mat)
    px, py = period
    H, W = c.mat.shape
    for y in range(H):
        for x in range(W):
            if c.mat[y, x] != k or c.tone[y, x] not in tones:
                continue
            # only deep inside the area (all 8 neighbours the same material/tone)
            ok = True
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    X, Y = x + dx, y + dy
                    if not (0 <= X < W and 0 <= Y < H) or c.mat[Y, X] != k or c.tone[Y, X] != c.tone[y, x]:
                        ok = False
            if ok and y % py == 0 and (x + (y // py) * 2) % px == 0:
                c.tone[y, x] = c.tone[y, x] - 1


def seam(c, mat, pts, tone):
    """A 1-texel seam / stitch line drawn only where `mat` already is."""
    k = c.mid(mat)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            x, y = round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n)
            if 0 <= x < c.w and 0 <= y < c.h and c.mat[y, x] == k:
                c.tone[y, x] = tone


def bang_tips(c, hair="hair", skin="skin"):
    """A lock tip that hangs alone over the skin (skin left and right of it) ends in the skin's tone 2
    (the lock's shadow) instead of a dark dot."""
    kh, ks = c.mid(hair), c.mid(skin)
    H, W = c.mat.shape
    ch = []
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            if c.mat[y, x] != kh:
                continue
            if c.mat[y + 1, x] == ks and c.mat[y, x - 1] == ks and c.mat[y, x + 1] == ks:
                ch.append((x, y))
    for x, y in ch:
        c.mat[y, x], c.tone[y, x] = ks, 2
