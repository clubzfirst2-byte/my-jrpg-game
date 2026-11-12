"""v3 round 2: the 2x detail INSIDE the surfaces of the normal enemies (inspection: "the same
information as v2"). Painted at texel size on each volume-shaded part after its shading, anchored to
the part (its bounding box), so it moves with the part and does not boil.

Every mark is a cluster, never a 1-texel speck or line (STYLE 3.4): fur locks 6-7 texels wide, robe
folds 3-texel ridges with 2-texel grooves, stone chips 3 x 2, moss tufts 4-6 wide. An in-between tone
(the ramp's 1.5 / 2.5) is laid only as a band 3 texels wide or more, so it survives the 3 x 3 rule.

Sub-materials (a body is more than one cloth or stone, like the hero's cloak, lining and gold trim):
  beast    ashfur (flanks)  + ashfur_d (the dark saddle on the back and the crown of the head)
                            + ashfur_p (the pale belly and throat)
  archer   plum (robe)      + plum_d (the darker, frayed hem) + patch (a sewn-on worn patch)
  sentinel oldstone (stone) + oldstone_w (weathered, cooler, on the lower part of each block)
                            + moss (tufts on the top faces)
Functions get t (tones 1..4, floats), half (0/1), m (the part's mask), org (texel coordinates of t's
[0, 0] in the frame) and return (t, half, matmap) where matmap holds a sub-material name or None.
"""

import math

import numpy as np


def _hash(a, b, seed=0):
    h = (int(a) * 73856093) ^ (int(b) * 19349663) ^ (seed * 83492791)
    h &= 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def _erode(m, n=1):
    for _ in range(n):
        e = m.copy()
        e[1:, :] &= m[:-1, :]
        e[:-1, :] &= m[1:, :]
        e[:, 1:] &= m[:, :-1]
        e[:, :-1] &= m[:, 1:]
        m = e
    return m


def _bbox(m):
    ys, xs = np.nonzero(m)
    return ys.min(), ys.max(), xs.min(), xs.max()


def _depth(m):
    """Per texel, its place between the top (0) and the bottom (1) of its column of the part."""
    h, w = m.shape
    d = np.full(m.shape, -1.0)
    for x in range(w):
        ys = np.nonzero(m[:, x])[0]
        if len(ys) >= 2:
            d[ys, x] = (ys - ys.min()) / (ys.max() - ys.min())
    return d


# ------------------------------------------------------------------ fur (beast)

def fur(t, half, m, org, seed=3):
    y0, y1, x0, x1 = _bbox(m)
    bw, bh = x1 - x0 + 1, y1 - y0 + 1
    mat = np.full(m.shape, None, dtype=object)
    wide = bw >= 1.2 * bh  # torso, neck, head: saddle on top, pale below; legs stay plain coat
    d = _depth(m)
    if wide:
        ys, xs = np.nonzero(m)
        fx = xs + org[1]
        edge_s = 0.34 + 0.07 * np.sin(fx * 0.31 + seed) + 0.04 * np.sin(fx * 0.83)
        edge_p = 0.74 + 0.05 * np.sin(fx * 0.27 + 2 * seed)
        dd = d[ys, xs]
        sad = dd < edge_s
        pal = dd > edge_p
        mat[ys[sad], xs[sad]] = "ashfur_d"
        mat[ys[pal], xs[pal]] = "ashfur_p"
    # locks lying back and down (the beast faces right): a tapered strand 7 texels wide at the root,
    # its upper 3 texels lit (+ half a step), its lower edge 2 texels dark (- one step), a dark tip
    inner = _erode(m, 2)
    sx, sy = 8, 6
    gx0, gy0 = org[1] - org[1] % sx, org[0] - org[0] % sy
    for j in range((y0 + org[0] - gy0) // sy - 1, (y1 + org[0] - gy0) // sy + 2):
        for i in range((x0 + org[1] - gx0) // sx - 1, (x1 + org[1] - gx0) // sx + 2):
            hv = _hash(i, j, seed)
            if hv < 0.18:
                continue
            rx = gx0 + i * sx + (j % 2) * (sx // 2) + int((hv - 0.5) * 4) - org[1]
            ry = gy0 + j * sy + int((_hash(i, j, seed + 9) - 0.5) * 3) - org[0]
            L = 9 + int(hv * 4)
            dx, dy = -0.9, 0.42
            nn = math.hypot(dx, dy)
            dx, dy = dx / nn, dy / nn
            cells = []
            ok = True
            for yy in range(int(ry - 5), int(ry + L * dy + 6)):
                for xx in range(int(rx + L * dx - 5), int(rx + 5)):
                    vx, vy = xx + 0.5 - rx, yy + 0.5 - ry
                    a = vx * dx + vy * dy  # along the strand
                    if a < 0 or a > L:
                        continue
                    n = -vx * dy + vy * dx  # across: < 0 above the strand
                    wd = 3.5 * (1 - a / L) + 0.8
                    if abs(n) > wd:
                        continue
                    if not (0 <= yy < m.shape[0] and 0 <= xx < m.shape[1] and inner[yy, xx]):
                        ok = False
                        break
                    cells.append((yy, xx, n, wd, a))
                if not ok:
                    break
            if not ok or not cells:
                continue
            for yy, xx, n, wd, a in cells:
                b = t[yy, xx]
                if a > L - 2.5:
                    t[yy, xx] = max(1, b - 1)  # the tip
                    half[yy, xx] = 0
                elif n < -wd + 3.0 and n < 0:
                    if b < 3:
                        half[yy, xx] = 1  # the lit side of the lock
                elif n > wd - 1.8:
                    t[yy, xx] = max(1, b - 1)
                    half[yy, xx] = 0
    return t, half, mat


# ------------------------------------------------------------------ cloth (archer)

def cloth(t, half, m, org, seed=5):
    y0, y1, x0, x1 = _bbox(m)
    bw, bh = x1 - x0 + 1, y1 - y0 + 1
    mat = np.full(m.shape, None, dtype=object)
    d = _depth(m)
    # folds: ridges hanging from about a quarter down, slanting a little, every 9-12 texels
    # round 2: the folds sit on a grid anchored to the body (org), every 8 texels with a small
    # per-fold offset, so they stay put when the cloak's outline sways
    k = (x0 + org[1]) // 8 - 1
    while k * 8 - org[1] < x1 + 2:
        x = k * 8 - org[1] + int(_hash(k, 4, seed) * 2)
        slope = (_hash(k, 2, seed) - 0.5) * 0.25
        start = 0.08 + _hash(k, 3, seed) * 0.15
        for yy in range(y0, y1 + 1):
            xc = x + slope * (yy + org[0])
            for xx in range(int(xc) - 4, int(xc) + 5):
                if not (0 <= xx < m.shape[1]) or not m[yy, xx] or d[yy, xx] < start:
                    continue
                u = xx + 0.5 - xc
                b = t[yy, xx]
                if -3 <= u < 0:
                    if b < 3:
                        t[yy, xx] = b + 1  # the ridge, 3 texels, a tone up
                        half[yy, xx] = 0
                elif 0 <= u < 3:
                    t[yy, xx] = max(1, b - 1)  # the groove, 3 texels
                    half[yy, xx] = 0
        k += 1
    if bh >= 24 and bw >= 16:  # the robe's far side shows its darker lining (the cloak's opening)
        ys, xs = np.nonzero(m)
        lining = (xs - x0) < (bw * (0.30 + 0.06 * np.sin((ys + org[0]) * 0.18 + seed))) * np.clip(d[ys, xs] * 1.6, 0, 1)
        mat[ys[lining], xs[lining]] = "plum_d"
    if bh >= 24:  # the hem: a darker, frayed band (a zigzag edge 3 texels deep)
        ys, xs = np.nonzero(m)
        fx = xs + org[1]
        edge = 0.76 - 0.06 * ((fx // 3) % 2) - 0.03 * np.sin(fx * 0.7 + seed)
        hem = d[ys, xs] > edge
        mat[ys[hem], xs[hem]] = "plum_d"
        # a sewn-on patch on the robe's front, with a 2-texel darker border (stitched edge)
        if bw >= 18:
            py0 = y0 + int(bh * 0.46)
            px0 = x0 + int(bw * 0.18)
            for yy in range(py0, py0 + 9):
                for xx in range(px0, px0 + 10):
                    if 0 <= yy < m.shape[0] and 0 <= xx < m.shape[1] and _erode(m, 2)[yy, xx]:
                        mat[yy, xx] = "patch"
                        border = yy < py0 + 2 or xx >= px0 + 8 or yy >= py0 + 7
                        t[yy, xx] = 1 if border else (2 if xx < px0 + 5 else 2)
                        half[yy, xx] = 1 if (not border and yy < py0 + 5 and xx < px0 + 6) else 0
    return t, half, mat


# ------------------------------------------------------------------ stone (sentinel)

def stone(t, half, m, org, seed=7):
    y0, y1, x0, x1 = _bbox(m)
    mat = np.full(m.shape, None, dtype=object)
    d = _depth(m)
    inner1 = _erode(m, 1)
    # cut blocks (round 2): rows 9 texels high, joints staggered every 13; a joint is 2 texels of
    # shade, the block below / right of it has a lit lip; each block's face keeps its volume tone
    for y in range(y0, y1 + 1):
        fy = y + org[0]
        row = fy // 9
        for x in range(x0, x1 + 1):
            if not inner1[y, x]:
                continue
            fx_ = x + org[1] + (row % 2) * 6 + int(_hash(row, 7, seed) * 5)
            a, b = fy % 9, fx_ % 13
            if a in (0, 1) or b in (0, 1):
                t[y, x] = max(1, t[y, x] - 1)
                half[y, x] = 0
            elif (a in (2, 3) or b in (2, 3)) and t[y, x] < 3:
                t[y, x] = t[y, x] + 1  # the lit lip under / right of a joint (2 texels, one tone up)
                half[y, x] = 0
    ys, xs = np.nonzero(m)
    fx = xs + org[1]
    edge = 0.48 + 0.08 * np.sin(fx * 0.4 + seed) + 0.05 * np.sin(fx * 1.1)
    streak = ((fx // 3) % 5 == 0) & (d[ys, xs] > 0.25)  # weathering running down in 3-texel streaks
    low = (d[ys, xs] > edge) | streak
    mat[ys[low], xs[low]] = "oldstone_w"  # weathered: cooler and darker towards the ground
    # moss on the top faces: tufts 4-6 wide, 2-3 high, here and there
    top = m.copy()
    top[1:, :] &= ~m[:-1, :]
    for x in range(x0, x1 + 1):
        ys_ = np.nonzero(top[:, x])[0]
        if not len(ys_):
            continue
        yt = ys_.min()
        hv = _hash((x + org[1]) // 6, 0, seed)
        if hv < 0.55:
            continue
        w = 4 + int(hv * 3)
        if (x + org[1]) % 6 >= w:
            continue
        hgt = 2 + int(_hash((x + org[1]) // 6, 1, seed) * 2)
        for k in range(hgt):
            if yt + k <= y1 and m[yt + k, x]:
                mat[yt + k, x] = "moss"
                t[yt + k, x] = 3 if k == 0 else 2
                half[yt + k, x] = 0
    # chips: a 3 x 2 notch (dark) with a lit lip under it, on the plates
    inner = _erode(m, 3)
    for j in range((y0 + org[0]) // 9 - 1, (y1 + org[0]) // 9 + 2):
        for i in range((x0 + org[1]) // 11 - 1, (x1 + org[1]) // 11 + 2):
            if _hash(i, j, seed + 3) < 0.2:
                continue
            cx = i * 11 + int(_hash(i, j, seed + 4) * 7) - org[1]
            cy = j * 9 + int(_hash(i, j, seed + 5) * 5) - org[0]
            cells = [(cy + a, cx + b) for a in range(3) for b in range(3)]
            if not all(0 <= a < m.shape[0] and 0 <= b < m.shape[1] and inner[a, b] for a, b in cells):
                continue
            for b in range(3):
                t[cy, cx + b] = max(1, t[cy, cx + b] - 1)
                t[cy + 1, cx + b] = max(1, t[cy + 1, cx + b] - 1)
                t[cy + 2, cx + b] = min(3, t[cy + 2, cx + b] + 1)
                half[cy:cy + 3, cx + b] = 0
    return t, half, mat


# ------------------------------------------------------------------ bronze (sentinel): rivets

def bronze(t, half, m, org, seed=11):
    y0, y1, x0, x1 = _bbox(m)
    mat = np.full(m.shape, None, dtype=object)
    inner = _erode(m, 2)
    for x in range(x0 + 2, x1 - 1, 7):
        y = (y0 + y1) // 2
        if all(inner[y + a, x + b] for a in (0, 1, 2) for b in (0, 1)):
            t[y, x] = t[y, x + 1] = t[y + 1, x] = 4
            t[y + 1, x + 1] = 3
            t[y + 2, x] = t[y + 2, x + 1] = 1
            half[y:y + 3, x:x + 2] = 0
    return t, half, mat


# ------------------------------------------------------------------ skin (archer): wrinkles and warts

def skin(t, half, m, org, seed=13):
    """Goblin skin: curved creases 2 texels dark with a lit band of 3 above them, every 6-7 rows,
    and a few 3 x 3 warts (lit top-left, dark bottom-right)."""
    y0, y1, x0, x1 = _bbox(m)
    mat = np.full(m.shape, None, dtype=object)
    inner = _erode(m, 1)
    for k, yy0 in enumerate(range(y0 + 3, y1 - 2, 5)):
        amp = 1.2 + _hash(k, 0, seed) * 1.5
        for x in range(x0, x1 + 1):
            yc = yy0 + amp * math.sin((x + org[1]) * 0.35 + k)
            for dy in range(-3, 2):
                y = int(round(yc)) + dy
                if not (0 <= y < m.shape[0]) or not inner[y, x]:
                    continue
                if dy >= 0:
                    t[y, x] = max(1, t[y, x] - 1)
                    half[y, x] = 0
                elif t[y, x] < 3:
                    t[y, x] = t[y, x] + 1
                    half[y, x] = 0
    for j in range(3):
        wy = y0 + int(_hash(j, 1, seed) * max(1, y1 - y0 - 3))
        wx = x0 + int(_hash(j, 2, seed) * max(1, x1 - x0 - 3))
        if all(0 <= wy + a < m.shape[0] and 0 <= wx + b < m.shape[1] and inner[wy + a, wx + b] for a in range(3) for b in range(3)):
            for a in range(3):
                for b in range(3):
                    t[wy + a, wx + b] = 3 if a + b <= 1 else (1 if a + b >= 3 else 2)
                    half[wy + a, wx + b] = 0
    return t, half, mat


# ------------------------------------------------------------------ leather: creases and a stitched seam

def leather(t, half, m, org, seed=17):
    y0, y1, x0, x1 = _bbox(m)
    mat = np.full(m.shape, None, dtype=object)
    inner = _erode(m, 1)
    for k, xx0 in enumerate(range(x0 + 2, x1 - 1, 6)):  # diagonal creases, 2 dark under 2 lit
        for y in range(y0, y1 + 1):
            x = xx0 + (y - y0) // 2
            for dx in range(-2, 2):
                xx = x + dx
                if 0 <= xx < m.shape[1] and inner[y, xx]:
                    if dx >= 0:
                        t[y, xx] = max(1, t[y, xx] - 1)
                        half[y, xx] = 0
                    elif t[y, xx] < 3:
                        t[y, xx] = t[y, xx] + 1 if t[y, xx] < 2 else t[y, xx]
    return t, half, mat


# ------------------------------------------------------------------ bronze: hammered dents + rivets

def bronze2(t, half, m, org, seed=19):
    t, half, mat = bronze(t, half, m, org, seed)
    y0, y1, x0, x1 = _bbox(m)
    inner1 = _erode(m, 1)
    # beaten plates (round 2): a joint every 8 texels (2 texels of shade), the plate beside it lit
    # for 2 texels (it catches the light on its raised edge)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if not inner1[y, x]:
                continue
            u = (x + org[1] + ((y + org[0]) // 6) * 3) % 8
            if u in (0, 1):
                t[y, x] = max(1, t[y, x] - 1)
                half[y, x] = 0
            elif u in (2, 3) and t[y, x] < 3:
                t[y, x] = t[y, x] + 1
                half[y, x] = 0
    inner = _erode(m, 2)
    for j in range((y0 + org[0]) // 5 - 1, (y1 + org[0]) // 5 + 2):
        for i in range((x0 + org[1]) // 6 - 1, (x1 + org[1]) // 6 + 2):
            if _hash(i, j, seed) < 0.4:
                continue
            cy, cx = j * 5 - org[0] + (i % 2) * 2, i * 6 - org[1]
            cells = [(cy + a, cx + b) for a in range(2) for b in range(3)]
            if not all(0 <= a < m.shape[0] and 0 <= b < m.shape[1] and inner[a, b] for a, b in cells):
                continue
            for b in range(3):  # a dent: its upper edge in shade, its lower edge catching light
                t[cy, cx + b] = max(1, t[cy, cx + b] - 1)
                t[cy + 1, cx + b] = min(3, t[cy + 1, cx + b] + 1)
                half[cy:cy + 2, cx + b] = 0
    return t, half, mat


def leather2(t, half, m, org, seed=23):
    """Boots and straps: a lit cuff (the folded top, 3 rows a tone up) over a 2-row shade, then the
    diagonal creases."""
    t, half, mat = leather(t, half, m, org, seed)
    d = _depth(m)
    ys, xs = np.nonzero(m)
    for y, x in zip(ys, xs):
        if d[y, x] < 0:
            continue
        col = np.nonzero(m[:, x])[0]
        k = y - col.min()
        if k < 3 and t[y, x] < 3:
            t[y, x] = t[y, x] + 1
            half[y, x] = 0
        elif 3 <= k < 5:
            t[y, x] = max(1, t[y, x] - 1)
            half[y, x] = 0
    return t, half, mat


def wood(t, half, m, org, seed=29):
    """The staff: knots every ~10 texels along it (a 2 x 3 dark knot with a lit lip under it)."""
    mat = np.full(m.shape, None, dtype=object)
    inner = _erode(m, 1)
    ys, xs = np.nonzero(inner)
    for k in range(len(ys)):
        y, x = ys[k], xs[k]
        if (y + org[0]) % 10 != int(_hash(x // 6, 3, seed) * 4):
            continue
        cells = [(y + a, x + b) for a in range(3) for b in range(2)]
        if not all(0 <= a < m.shape[0] and 0 <= b < m.shape[1] and inner[a, b] for a, b in cells):
            continue
        for b in range(2):
            t[y, x + b] = max(1, t[y, x + b] - 1)
            t[y + 1, x + b] = max(1, t[y + 1, x + b] - 1)
            t[y + 2, x + b] = min(3, t[y + 2, x + b] + 1)
            half[y:y + 3, x + b] = 0
    return t, half, mat


DETAIL = {"ashfur": fur, "plum": cloth, "oldstone": stone, "bronze": bronze2, "gobskin": skin, "leather": leather2,
          "wood": wood}
MIN_AREA = 120  # texels
