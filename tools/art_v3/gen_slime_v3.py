"""v3 pilot: the slime at hero-level detail (64 x 56, density 4), idle 4 frames.

New drawing on the 2x grid (not a remaster: STYLE.md 5.3 asks enemies to reach the hero's detail).
Same design as v1 (enemy.slime: a violet jelly dome with a magenta crystal core and two glowing eyes),
new: the outline is the jelly's own tone 0 (not near-black, STYLE.md 3.3), the jelly has depth (the
lower half darker, a glow halo round the core), bubbles drifting up, a curved shine, side drips and a
seep line on the ground. Idle: a 4-step wobble (wide-low, settle, tall-narrow, settle) with the
bubbles rising 1 texel a frame.
Writes src/art-release-v3/enemy/enemy.slime.idle.<n>.png
Run: python3 tools/art_v3/gen_slime_v3.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402

from v3lib import ROOT, Canvas, save  # noqa: E402

OUT = os.path.join(ROOT, "src", "art-release-v3", "enemy")
W, H = 64, 56
G = 53  # ground row (feet line), 3 texels above the bottom for the seep
RAMPS = {
    "jelly": ["#2e1a3e", "#40245a", "#55306f", "#6e4490", "#9a70c0", "#c8a4e8"],
    "deep": ["#2e1a3e", "#2e1a3e", "#36204c", "#40245a", "#4a2a62", "#55306f"],
    "core": ["#4a1050", "#6a1e6a", "#8e2c8e", "#b040b0", "#e070e0", "#ffc8ff"],
    "glow": ["#4a2a62", "#7a4aa0", "#8a58b0", "#a070c8", "#c090e0", "#e0b8f4"],
}
EYE = "#ffd8ff"
EYE_D = "#e070e0"
POSES = [  # rx, ry, lean
    (29.0, 17.0, 0),
    (28.0, 18.0, 0),
    (27.0, 19.0, 0),
    (28.0, 18.0, 0),
]
BUBBLES = [(17, 36, 2.2), (45, 38, 1.6), (22, 42, 1.2)]


def body_mask(c, rx, ry, cx=32.0):
    """A dome wider at the bottom: an ellipse on top, flattened and widened toward the ground."""
    yy, xx = np.mgrid[0:H, 0:W]
    top = G - 2 * ry + 4
    cy = G - ry + 2
    t = np.clip((yy + 0.5 - top) / (G - top), 0, 1)  # 0 at the top, 1 at the ground
    rxx = rx * (0.80 + 0.24 * t ** 1.6)
    m = ((xx + 0.5 - cx) / rxx) ** 2 + ((yy + 0.5 - cy) / ry) ** 2 <= 1
    m &= yy < G
    return m


def frame(i):
    rx, ry, _ = POSES[i]
    c = Canvas(W, H, RAMPS)
    body = body_mask(c, rx, ry)
    c.fill(body, "jelly")
    c.shade_part(body, tones=(1, 2, 3, 3, 4, 4))
    ys, xs = np.nonzero(body)
    top, cx = ys.min(), 32
    hgt = G - top
    # depth: the lower third is the deep jelly (a darker material inside the same outline)
    yy, xx = np.mgrid[0:H, 0:W]
    lower = body & (yy >= G - hgt * 0.36) & (((xx + 0.5 - cx) / (rx * 0.95)) ** 2 + ((yy + 0.5 - (G + 2)) / (hgt * 0.46)) ** 2 <= 1)
    c.fill(lower, "deep")
    c.shade_part(lower, tones=(2, 3, 4, 5), light=(-0.6, -0.4, 0.7))
    # the core: a glow halo, then the crystal (diamond), lit from the inside
    ccy = G - hgt * 0.42
    halo = c.m_ellipse(cx + 1, ccy, 8.0, 7.5) & body & ~lower
    c.fill(halo, "glow")
    c.shade_part(halo, tones=(0, 1, 1, 2, 3), light=(0.0, 0.0, 1.0))
    cry = c.m_poly([(cx + 1, ccy - 7), (cx + 6, ccy), (cx + 1, ccy + 6), (cx - 4, ccy)])
    c.fill(cry, "core")
    # facets: left upper bright, right lower dark, a hot centre
    for y, x in zip(*np.nonzero(cry)):
        dx, dy = x + 0.5 - (cx + 1), y + 0.5 - ccy
        t = 3
        if dx < 0 and dy < 0:
            t = 5 if (dx > -2 and dy > -4) else 4
        elif dx >= 0 and dy >= 0:
            t = 1 if dx + dy > 4 else 2
        elif dx < 0:
            t = 3
        else:
            t = 4 if dx + (-dy) < 3 else 3
        c.tone[y, x] = t
    # bubbles rising (1 texel a frame), each a ring of tone 4 with a tone-5 point
    for bx, by, r in BUBBLES:
        y0 = by - i
        m = c.m_ellipse(bx, y0, r, r) & body & ~cry & ~halo & ~lower
        ring = m & ~c.m_ellipse(bx, y0, r - 1, r - 1) if r > 1.4 else m
        c.set_tone(ring, 4)
        c.put(int(bx - r / 2), int(y0 - r / 2), "jelly", 5)
    # the shine: a curved streak on the top left and a point
    for k in range(9):
        a = 2.35 + k * 0.11
        x = cx + np.cos(a) * rx * 0.62
        y = G - hgt * 0.55 + np.sin(a) * -hgt * 0.42
        for w in (0, 1):
            xx_, yy_ = int(round(x + w)), int(round(y))
            if body[yy_, xx_]:
                c.put(xx_, yy_, "jelly", 5 if 2 <= k <= 6 else 4)
    c.put(int(cx - rx * 0.20), int(top + 3), "jelly", 5)
    c.put(int(cx - rx * 0.20) + 1, int(top + 3), "jelly", 5)
    # eyes: two glowing slits above the core
    ey = int(round(G - hgt * 0.70))
    for ex in (cx - 11, cx + 7):
        for dx in range(5):
            c.dot(ex + dx, ey, EYE_D if dx in (0, 4) else EYE)
            c.dot(ex + dx, ey + 1, EYE_D if dx in (0, 4) else EYE)
        for dx in (1, 2, 3):
            c.dot(ex + dx, ey - 1, "#40245a")
            c.dot(ex + dx, ey + 2, EYE_D)
    # side drips (jelly running down), shift with the wobble
    for sx, ln in ((cx - rx * 0.70, 5 + (i % 2)), (cx + rx * 0.74, 6 - (i % 2))):
        x = int(round(sx))
        for d in range(ln):
            y = G - 6 + d
            if 0 <= y < G and body[y, x]:
                c.put(x, y, "deep", 1 if d < ln - 1 else 5)
    c.outline()
    # the seep on the ground: one row of deep jelly just under the body, a little wider each wobble
    ys2 = np.nonzero(body[G - 1])[0]
    if len(ys2):
        for x in range(ys2.min() - 2, ys2.max() + 3):
            if 0 <= x < W:
                c.put(x, G, "deep", 3 if (x + i) % 5 else 4)
                c.put(x, G + 1, "jelly", 0)
    c.shadow_band()
    return c


def main():
    out = [save(frame(i), os.path.join(OUT, f"enemy.slime.idle.{i}.png")) for i in range(4)]
    print("\n".join(os.path.relpath(p, ROOT) for p in out))


if __name__ == "__main__":
    main()
