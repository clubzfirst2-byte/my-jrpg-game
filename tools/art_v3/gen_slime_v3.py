"""v3 pilot (round 2): the slime at hero-level detail (64 x 56, density 4), idle 4 frames.

Back to the v1 design (enemy.slime: a tall violet drop whose foot spreads on the ground, a magenta
crystal core, two pink eyes) and v1's darker values (it must stand apart from the grass by brightness,
not only by hue). New on the 2x grid: the body is shaded as a round drop (curved bands, no straight
line inside), a bounce light along the foot, the foot spreading into lips on the ground, a curved
shine, bubbles, the core glowing through the jelly. Idle: 4 different frames (settle, swell to the
right, rise, lean left) with the bubbles and the shine moving.
Outline: the jelly's own tone 0 #2e1a3e (not near-black, STYLE.md 3.3).
Writes src/art-release-v3/enemy/enemy.slime.idle.<n>.png
Run: python3 tools/art_v3/gen_slime_v3.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402

from v3lib import ROOT, Canvas, despeckle, save  # noqa: E402

OUT = os.path.join(ROOT, "src", "art-release-v3", "enemy")
W, H = 64, 56
G = 54  # the foot's bottom row
RAMPS = {
    "jelly": ["#2e1a3e", "#3a2150", "#47295f", "#573271", "#6e4490", "#9a70c0", "#c4a0e4"],
    "core": ["#4a1050", "#6a1e6a", "#8e2c8e", "#b040b0", "#e070e0", "#ffc8ff"],
    "glow": ["#3a2150", "#55306f", "#62387e", "#70428e", "#80509e", "#9a70c0"],
}
EYE, EYE_D, EYE_W, PUPIL = "#e070e0", "#b040b0", "#ffd8ff", "#3a1a44"
POSES = [  # cx shift of the top, dome half width, top row, foot half width, bubbles phase
    dict(lean=0, rx=21.5, top=16, foot=30, ph=0),
    dict(lean=1, rx=22.5, top=17, foot=31, ph=1),
    dict(lean=0, rx=21.0, top=14, foot=29, ph=2),
    dict(lean=-1, rx=21.5, top=16, foot=30.5, ph=3),
]


def body_mask(c, lean, rx, top, foot):
    """A drop: a round top, straight-ish sides, and a foot that spreads into lips on the ground."""
    yy, xx = np.mgrid[0:H, 0:W]
    cx = 31.5
    m = np.zeros((H, W), bool)
    for y in range(top, G + 1):
        t = (y - top) / (G - top)
        sx = cx + lean * (1 - t)
        if t < 0.50:  # the round top
            u = t / 0.50
            hw = rx * np.sqrt(max(0.0, 1 - (1 - u) ** 2))
        elif t < 0.80:  # the sides, widening a little
            hw = rx + (t - 0.50) / 0.30 * 2.5
        else:  # the foot: spreads fast (concave) into the lips
            u = (t - 0.80) / 0.20
            hw = rx + 2.5 + (foot - rx - 2.5) * u ** 1.8
        if hw >= 3:
            m[y] |= np.abs(xx[y] + 0.5 - sx) <= hw
    return m


def frame(i):
    p = POSES[i]
    c = Canvas(W, H, RAMPS)
    body = body_mask(c, p["lean"], p["rx"], p["top"], p["foot"])
    c.fill(body, "jelly")
    # a round drop lit from the top left: curved bands from a normal over the whole body (no rows)
    hgt = G - p["top"]
    cx0 = 31.5 + p["lean"] * 0.5
    for y, x in zip(*np.nonzero(body)):
        row = np.nonzero(body[y])[0]
        hw = max(1.0, (row.max() - row.min() + 1) / 2)
        nx = (x + 0.5 - (row.min() + hw)) / hw
        ny = (y + 0.5 - (p["top"] + hgt * 0.55)) / (hgt * 0.62)
        v = 0.55 - 0.42 * nx - 0.38 * ny - 0.18 * (nx * nx + ny * ny)
        c.tone[y, x] = 1 if v < 0.12 else 2 if v < 0.42 else 3 if v < 0.72 else 4
    cx = 31.5 + p["lean"] * 0.5
    # bounce light along the foot: the 2 rows above the bottom edge, inside, one tone up (curved, it
    # follows the silhouette), and the lips' lit tops
    for x in range(W):
        ys = np.nonzero(body[:, x])[0]
        if not len(ys):
            continue
        yb = ys.max()
        for d in (1, 2):
            if body[yb - d, x] and abs(x + 0.5 - cx) < p["foot"] - 3:
                c.tone[yb - d, x] = min(5, int(c.tone[yb - d, x]) + (1 if d == 2 else 0))
        if abs(x + 0.5 - cx) > p["rx"] + 3:  # the lips
            c.tone[ys.min(), x] = 5 if x < cx else 4
    # the core glowing through the jelly (a soft halo, then the crystal with 4 facets)
    ccy = G - 15
    halo = c.m_ellipse(cx + 1, ccy, 7.5, 6.5) & body
    c.fill(halo, "glow")
    c.shade_part(halo, tones=(1, 2, 3, 4), light=(0.0, 0.0, 1.0), norm=True)
    cry = c.m_poly([(cx + 1, ccy - 6), (cx + 5.5, ccy), (cx + 1, ccy + 5.5), (cx - 3.5, ccy)])
    c.fill(cry, "core")
    for y, x in zip(*np.nonzero(cry)):
        dx, dy = x + 0.5 - (cx + 1), y + 0.5 - ccy
        c.tone[y, x] = 5 if (dx < 0 and dy < 0 and dx > -2.5 and dy > -4) else 4 if (dx < 0 and dy < 0) else \
            1 if (dx >= 0 and dy >= 0 and dx + dy > 3.5) else 2 if (dx >= 0 and dy >= 0) else 3
    # eyes: v1's form at 2x — a bright pink square (4 x 4, a 2 x 2 light in its upper left) and a
    # dark pupil (2 x 2) under its left half
    ey = p["top"] + 9
    for ex in (int(cx - 9), int(cx + 5)):
        for dy in range(4):
            for dx in range(4):
                col = EYE_W if (dx < 2 and dy < 2) else (EYE_D if (dx == 3 and dy == 3) else EYE)
                c.dot(ex + dx, ey + dy, col)
        for dy in (4, 5):
            for dx in (0, 1):
                c.dot(ex + dx, ey + dy, PUPIL)
    # the shine: a curved streak just inside the upper left edge, and a 2 x 2 point
    top = p["top"]
    for y in range(top + 3, top + 15):
        xs = np.nonzero(body[y])[0]
        if not len(xs):
            continue
        x = xs.min() + 3 + max(0, (top + 6 - y)) // 2
        c.put(x, y, "jelly", 6 if top + 5 <= y <= top + 11 else 5)
        c.put(x + 1, y, "jelly", 5)
    sx, sy = int(cx - 6), top + 3
    for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
        c.put(sx + dx, sy + dy, "jelly", 6 if (dx, dy) != (1, 1) else 5)
    # bubbles drifting up: small 4 x 4 rings (tone 5) with a lit point, only in the jelly
    ring = [".##.", "#..#", "#..#", ".##."]
    for k, (bx, by) in enumerate(((cx - 15, 40), (cx + 12, 36), (cx - 8, 47))):
        y0 = int(by - ((p["ph"] + k) % 4) * 2)
        x0 = int(bx)
        if not all(body[y0 + j, x0 + i] for j in range(4) for i in range(4)):
            continue
        if (halo | cry)[y0:y0 + 4, x0:x0 + 4].any():
            continue
        for j, r_ in enumerate(ring):
            for i, ch in enumerate(r_):
                if ch == "#":
                    c.put(x0 + i, y0 + j, "jelly", 5)
        c.put(x0 + 1, y0 + 1, "jelly", 6)
    despeckle(c)
    c.outline()
    c.shadow_band()
    return c


def main():
    out = [save(frame(i), os.path.join(OUT, f"enemy.slime.idle.{i}.png")) for i in range(4)]
    print("\n".join(os.path.relpath(p, ROOT) for p in out))


if __name__ == "__main__":
    main()
