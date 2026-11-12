"""v3 enemy shots (density 4): 24 x 24, anchor the centre, 4 frames each (v2's keys and counts).

Drawn new on the 2x grid (v2's 12 x 12 hand maps are only the reference for shape and colours):
  orb    a murk-glow sphere lit from the top left, a dark swirl band that turns 90 degrees a frame,
         a 3 x 2 highlight and a pale heart
  ice    a faceted shard pointing right (the way it flies): lit top-left facet, mid facet, dark
         underside, a glowing heart; a glint runs along the top edge from frame to frame
  sand   a grit ball (murksand) with 2 x 2 to 3 x 2 grains that tumble (turn 90 degrees a frame)
         round a glowing heart
  spark  an eight-point star (long and short rays alternating) turning 22.5 degrees a frame,
         around a pink-white heart
Ramps: the v2 ramps of rig.py (RGBV3: tone 0 lifted to luma >= 30). Outline: the material's tone 0.
"""

import math

import numpy as np

from rig import RGBV3
from v3lib import Canvas, despeckle

W = H = 24
C = 11.5  # the centre (texel 12 is the anchor's right half: the 24 x 24 frame's centre)


def canvas():
    """Tones 0-5 -> the ramp's outline, shadow, core, light, highlight (no in-between steps, like
    v2's shots): indices 0, 1, 3, 5, 6, 6 of the v2 ramp."""
    return Canvas(W, H, {k: [RGBV3[k][i] for i in (0, 1, 3, 5, 6, 6)] for k in ("glow", "ice", "murksand", "spark")})


def sphere_tones(c, mask, cx, cy, r, lo=1, hi=5):
    for y, x in zip(*np.nonzero(mask)):
        nx, ny = (x + 0.5 - cx) / r, (y + 0.5 - cy) / r
        nz = math.sqrt(max(0.0, 1 - nx * nx - ny * ny))
        v = (-0.55 * nx - 0.68 * ny + 0.48 * nz) * 0.5 + 0.5  # 0..1
        cuts = np.linspace(0.30, 0.80, hi - lo)  # clear bands, not a gradient
        c.tone[y, x] = lo + int(np.searchsorted(cuts, v))


def orb(i):
    c = canvas()
    r = 8.9
    m = c.m_ellipse(C + 0.5, C + 0.5, r, r)
    c.fill(m, "glow", 3)
    sphere_tones(c, m, C + 0.5, C + 0.5, r, 1, 4)
    a0 = i * math.pi / 2
    for y, x in zip(*np.nonzero(m)):  # the swirl: a dark band spiralling in
        dx, dy = x + 0.5 - C - 0.5, y + 0.5 - C - 0.5
        rr = math.hypot(dx, dy)
        ang = math.atan2(dy, dx) - a0
        if 3.0 < rr < r - 1.2 and abs(((ang - rr * 0.45) % (2 * math.pi)) - math.pi) < 0.55:
            c.tone[y, x] = max(1, int(c.tone[y, x]) - 2)
    heart = c.m_ellipse(C + 0.5, C + 0.5, 2.6, 2.6)
    c.fill(heart, "glow", 4)
    c.fill(c.m_rect(8, 7, 10, 8), "glow", 5)  # the highlight
    return finish(c)


def ice(i):
    c = canvas()
    tip, tail = (22, C + 0.5), (2.5, C + 0.5)
    top, bot = (9.5, 5.5), (11.5, 18.5)
    shard = c.m_poly([tail, top, tip, bot])
    c.fill(shard, "ice", 2)
    up = c.m_poly([tail, top, tip, (12, C)])
    c.fill(up & shard, "ice", 3)  # the lit facet (the glint, tone 4-5, runs over it)
    c.fill(c.m_poly([(12, C + 3.5), tip, bot]) & shard, "ice", 1)
    heart = c.m_ellipse(11.5, C + 0.5, 2.6, 1.8)
    c.fill(heart, "glow", 3)
    c.fill(c.m_rect(10, 11, 11, 11), "glow", 4)
    gx = 6 + i * 3  # the glint runs along the top edge
    for d in range(3):
        x = gx + d
        ys = np.nonzero(shard[:, x])[0]
        if len(ys):
            c.put(x, ys.min() + 1, "ice", 5)
            c.put(x, ys.min() + 2, "ice", 5)
    return finish(c)


def sand(i):
    c = canvas()
    r = 8.4
    m = c.m_ellipse(C + 0.5, C + 0.5, r, r * 0.92)
    c.fill(m, "murksand", 3)
    sphere_tones(c, m, C + 0.5, C + 0.5, r, 1, 3)
    a0 = i * math.pi / 2
    grains = ((5.0, 0.3, 3), (5.5, 1.9, 2), (4.0, 3.3, 3), (6.2, 4.4, 2), (3.0, 5.4, 3))
    for rr, a, w in grains:  # tumbling grains: lit on the light side, dark on the shade side
        gx = C + 0.5 + rr * math.cos(a + a0)
        gy = C + 0.5 + rr * math.sin(a + a0) * 0.92
        gm = c.m_rect(int(gx) - 1, int(gy) - 1, int(gx) - 1 + w - 1, int(gy)) & m
        lit = (gx - C) + (gy - C) < 0
        c.fill(gm, "murksand", 4 if lit else 1)
    heart = c.m_ellipse(C + 0.5, C + 0.5, 3.0, 3.0)
    c.fill(heart, "glow", 3)
    c.fill(c.m_rect(11, 10, 12, 11), "glow", 4)
    return finish(c)


def spark(i):
    c = canvas()
    a0 = i * math.pi / 8
    pts = []
    for k in range(16):
        a = a0 + k * math.pi / 8
        rr = (10.5 if k % 4 == 0 else 7.0) if k % 2 == 0 else 3.6
        pts.append((C + 0.5 + rr * math.cos(a), C + 0.5 + rr * math.sin(a)))
    star = c.m_poly(pts)
    c.fill(star, "spark", 3)
    for y, x in zip(*np.nonzero(star)):
        dx, dy = x + 0.5 - C - 0.5, y + 0.5 - C - 0.5
        rr = math.hypot(dx, dy)
        c.tone[y, x] = 4 if rr < 5.5 else (3 if dx + dy < 0 else 2)
    heart = c.m_ellipse(C + 0.5, C + 0.5, 3.0, 3.0)
    c.fill(heart, "glow", 4)
    c.fill(c.m_rect(11, 11, 12, 12), "glow", 5)
    return finish(c)


def finish(c):
    despeckle(c)
    c.outline()
    return c


KINDS = {"orb": orb, "ice": ice, "sand": sand, "spark": spark}
ACTIONS = (("orb", 4), ("ice", 4), ("sand", 4), ("spark", 4))


def frames():
    return {f"{k}.{i}": f(i) for k, f in KINDS.items() for i in range(4)}
