"""雷鳴のヌシ (boss_storm): a huge storm-eel rising out of the lake in an S, seen from the front.
88x96 (the ring of water at its base included); base on row 94, outline row 95. Front-facing only.

Design (ENEMY_BOSS_DESIGN.md 3.4): grey-lavender scales (slate), a pale belly, yellow spark fins
along the back and a jagged spark crest on the head, a long snout; behind it a coil breaks the
water. The core glows on its chest. Patterns: ring, volley, slam (phase 2).
Phase 2: lines of sparks run along the body.
"""

import math

from rig import Rig
from bossparts import glow_eyes

W, H = 88, 96
G = 94


class Pose:
    def __init__(self, **k):
        self.sway = 0  # S bends more to the left (-) / right (+)
        self.raise_ = 0  # the neck reaches higher (+)
        self.drop = 0  # head lower (+)
        self.hs = 1.0
        self.jaw = 0
        self.sparks = 0  # sparks crawling around (ring wind-up): 0, 4, 8
        self.fly = 0  # sparks thrown out (ring attack)
        self.mouth_spark = False
        self.splash = False
        self.eyes = "open"
        self.phase2 = False
        self.collapse = 0
        self.crest = 0  # crest flicker (0/1)
        self.crest_up = 1.0  # crest raised (ring wind-up: bristles tall)
        self.fin = 15  # dorsal fin length (bristle: longer)
        self.pull = 0  # neck drawn back to the left (volley wind-up)
        self.coil = 0  # body pulled down into a tight coil (ring wind-up)
        self.__dict__.update(k)


def zig(r, x, y, s=1):
    """A small spark zig-zag (hand-placed, 2-px groups)."""
    r.stamp(x, y, ["ab..", ".ab.", "..ab", ".ab.", "ab.."] if s > 0 else ["..ba", ".ba.", "ba..", ".ba.", "..ba"],
            {"a": ("spark", 4), "b": ("spark", 2)})


def draw(p):
    r = Rig(W, H)
    c = p.collapse
    if c >= 4:
        return remains(r)
    sink = c * 9
    # the water at the base (the lake ramp), rings of ripples
    r.ellipse(44, G - 5.2, 41, 5.4, "lake", soft=2)
    r.add(r.m_ellipse(44, G - 5.2, 30, 3.2) & ~r.m_ellipse(44, G - 5.8, 27, 2.4), "lake", tone=3)
    water = r.m_rect(-20, G - 6, W + 20, H + 20)  # below the waterline nothing of the eel shows
    if p.splash:
        for x, y, rr in ((10, G - 14, 2.4), (78, G - 16, 2.4), (20, G - 22, 1.8), (68, G - 24, 1.8), (4, G - 8, 1.6), (84, G - 9, 1.6)):
            r.ellipse(x, y, rr, rr * 1.3, "lake", soft=1, lit=1)
    # a coil breaking the water behind (an arch)
    r.add(r.m_chain([(60, G - 4), (64, G - 14 + sink * 0.5), (72, G - 15 + sink * 0.5), (77, G - 4)], [5.0, 5.0, 4.6, 4.2]) & ~water, "slate", dark=1)
    # the S body: base in the water, bending left then right up to the neck
    sw, rz, pl, co = p.sway, p.raise_, p.pull, p.coil
    pts = [(30, G - 4), (24 + sw * 0.5 - co * 0.6, 74 - rz * 0.2 + sink + co * 0.3), (30 + sw - pl * 0.4 - co * 0.8, 58 - rz * 0.5 + sink + co * 0.7),
           (42 + sw - pl * 0.9, 46 - rz * 0.8 + sink + co), (50 + sw * 0.6 - pl * 1.4, 34 - rz + sink + p.drop * 0.4 + co * 1.1 + pl * 0.3)]
    radii = [9.5, 9.0, 8.6, 8.0, 7.4]
    pts = [(x, min(y, G - 4)) for x, y in pts]
    # dorsal fins along the back (left side of the S), behind the body
    for i in range(1, 4):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy) or 1
        nx, ny = dy / L, -dx / L  # left normal
        if nx > 0:
            nx, ny = -nx, -ny
        fl = p.fin + (3 if p.phase2 else 0)
        r.poly([(mx - dx / L * 4, my - dy / L * 4), (mx + nx * fl, my + ny * fl - 3), (mx + dx / L * 4, my + dy / L * 4)], "spark", soft=1, dark=1)
    body = r.m_chain(pts, radii) & ~water
    r.add(body, "slate", soft=4)
    # pale belly scutes down the front of the S
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        r.shade(r.m_line(x0 + 4, y0, x1 + 4, y1), lambda t: min(3, t + 1))
        r.shade(r.m_line(x0 + 5, y0 + 1, x1 + 5, y1 + 1), lambda t: min(3, t + 1))
    # scale rows: short dark arcs
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        for t in (0.3, 0.7):
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            r.shade(r.m_line(x - 4, y, x - 1, y + 2), lambda tt: max(1, tt - 1))
    if p.phase2 or c:
        # phase 2: a 2-px band of sparks down the body, forking at each bend (reads at half size)
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            r.add(r.m_line(x0 - 4, y0, x1 - 4, y1), "spark", tone=3, cast=False)
            r.add(r.m_line(x0 - 3, y0, x1 - 3, y1), "spark", tone=2, cast=False)
            if i:
                r.add(r.m_line(x0 - 3, y0, x0 + 2, y0 + 3) | r.m_line(x0 - 3, y0 + 1, x0 + 2, y0 + 4), "spark", tone=2, cast=False)
    # the core on the chest of the S
    kx, ky = pts[2][0] + 2, pts[2][1] + 2
    r.ellipse(kx, ky, 5, 5, "murk", soft=2)
    r.stamp(round(kx) - 2, round(ky) - 2, ["..a..", ".abb.", "abbcd", ".bcd.", "..d.."] if c < 3 else ["..b..", ".bcc.", "..d.."],
            {"a": ("glow", 4), "b": ("glow", 3), "c": ("glow", 2), "d": ("glow", 1)})
    # head on top, snout reaching right
    hs = p.hs
    hx_, hy = pts[-1][0] + 4, pts[-1][1] - 6 + p.drop * 0.6
    for i, (dx, h) in enumerate(((-10, 9), (-5, 14), (0, 16), (5, 12), (9, 7))):  # jagged spark crest
        h = h * hs * (p.crest_up + (0.2 if p.phase2 else 0)) + (1 if (i + p.crest) % 2 else -1)
        x = hx_ + dx * hs
        r.poly([(x - 3, hy - 6 * hs), (x - 1, hy - 6 * hs - h * 0.6), (x + 1, hy - 6 * hs - h * 0.45), (x + 0.5, hy - 6 * hs - h), (x + 3, hy - 6 * hs)], "spark", soft=1)
    if p.jaw:
        r.add(r.m_poly([(hx_ - 2, hy + 4), (hx_ + 20 * hs, hy + 6 + p.jaw * 2), (hx_ + 18 * hs, hy + 9 + p.jaw * 2), (hx_ - 4, hy + 9)]), "slate", dark=1, soft=1)
        r.add(r.m_poly([(hx_ + 1, hy + 4), (hx_ + 19 * hs, hy + 4), (hx_ + 17 * hs, hy + 5 + p.jaw * 2)]), "murk", tone=0)
    head = r.mask_of(r.m_ellipse(hx_, hy, 12.5 * hs, 9.5 * hs), r.m_poly([(hx_ + 2, hy - 4 * hs), (hx_ + 22 * hs, hy + 0.5), (hx_ + 21 * hs, hy + 3), (hx_ + 4, hy + 5)]))
    if p.jaw:
        head &= ~r.m_poly([(hx_ + 1, hy + 4), (hx_ + 24, hy + 3.6), (hx_ + 24, hy + 12), (hx_ + 1, hy + 12)])
    r.add(head, "slate", soft=3)
    r.px([(round(hx_ + 20 * hs), round(hy))], "slate", 0)  # nostril
    if p.mouth_spark:
        zig(r, round(hx_ + 7), round(hy + 3), 1)
        zig(r, round(hx_ + 12), round(hy + 4), -1)
    # fangs: two hooked bone fangs hang over the lower lip, a row more when the jaw opens
    fangs = [(hx_ + 6 * hs, 3), (hx_ + 13 * hs, 3)] + ([(hx_ + 9.5 * hs, 2), (hx_ + 16.5 * hs, 2)] if p.jaw else [])
    for fx, fl in fangs:
        r.poly([(fx - 1.2, hy + 3.6), (fx + 1.2, hy + 3.6), (fx + 0.4, hy + 3.6 + fl), (fx - 0.2, hy + 3.6 + fl)], "bone", soft=1)
    # a heavy brow ridge over slanted eyes (the eyes glare down toward the snout)
    ex, ey = hx_ + 1, hy - 1
    for sgn in (-1, 1):
        r.add(r.m_poly([(ex + sgn * 2 - 1.5, ey - 3.2 - (0 if sgn > 0 else 1.2)), (ex + sgn * 8 + 1, ey - 4.8 - (0 if sgn > 0 else 1.2)),
                        (ex + sgn * 8 + 1, ey - 2.4), (ex + sgn * 2 - 1.5, ey - 1.2)]), "slate", dark=1, soft=1)
    if p.eyes == "open":
        for sgn in (-1, 1):
            x = round(ex + sgn * 5) - 1
            y = round(ey)
            r.stamp(x - 1, y - 1, ["ab..", ".bcc"] if sgn < 0 else ["..ba", "ccb."], {"a": ("glow", 4), "b": ("glow", 3), "c": ("glow", 2)})
    else:
        glow_eyes(r, ex, ey, round(5 * hs), p.eyes)
    # sparks crawling around it (ring) / thrown out
    ring = [(6, 30), (78, 40), (8, 66), (80, 62), (36, 4), (66, 14), (4, 48), (82, 82)]
    for i, (x, y) in enumerate(ring[:p.sparks]):
        ang = math.atan2(y - 50, x - 44)
        x2, y2 = round(x + math.cos(ang) * p.fly), round(y + math.sin(ang) * p.fly)
        if 0 <= x2 <= W - 5 and 0 <= y2 <= H - 6:
            zig(r, x2, y2, 1 if i % 2 else -1)
    return r


def remains(r):
    """Purified: the eel has sunk; only a coil and its limp head lie on the water."""
    r.ellipse(44, G - 5.2, 41, 5.4, "lake", soft=2)
    r.add(r.m_ellipse(44, G - 5.2, 30, 3.2) & ~r.m_ellipse(44, G - 5.8, 27, 2.4), "lake", tone=3)
    r.chain([(20, G - 4), (26, G - 10), (36, G - 10), (42, G - 5)], [5.0, 5.2, 5.0, 4.6], "slate", soft=2)
    r.add(r.mask_of(r.m_ellipse(54, G - 8, 8, 5.5), r.m_poly([(56, G - 11), (70, G - 8), (69, G - 6), (56, G - 4)])), "slate", soft=2)
    for i, x in enumerate((48, 52, 56)):
        r.poly([(x - 2, G - 13), (x, G - 16 - i % 2), (x + 2, G - 13)], "spark", soft=1, dark=1)
    r.px([(52, G - 9), (53, G - 9)], "glow", 1)
    return r


def frames():
    f = {}
    f["idle.0"] = Pose()
    f["idle.1"] = Pose(sway=1, raise_=1, crest=1)
    f["move.0"] = Pose(sway=-3, crest=1)
    f["move.1"] = Pose(sway=3, raise_=1)
    # ring: it pulls down into a tight coil, the crest and fins bristle tall, sparks run around it;
    # then it rears and they fly out
    f["windup_ring.0"] = Pose(sparks=4, crest=1, coil=7, crest_up=1.5, fin=19, jaw=1)
    f["windup_ring.1"] = Pose(sparks=8, coil=11, crest_up=1.8, fin=22, jaw=1, sway=-2)
    f["attack_ring.0"] = Pose(sparks=8, fly=6, raise_=4, jaw=2, crest=1)
    f["attack_ring.1"] = Pose(sparks=4, fly=12, raise_=2)
    # volley: the neck draws back to the left, the head tips up, the jaw gapes with sparks inside;
    # then the head lunges as the fan leaves
    f["windup_volley.0"] = Pose(jaw=3, mouth_spark=True, pull=8, drop=-3)
    f["windup_volley.1"] = Pose(jaw=4, mouth_spark=True, pull=13, drop=-5, raise_=2, crest=1)
    f["attack_volley.0"] = Pose(jaw=3, drop=6, hs=1.08, sway=1)
    f["attack_volley.1"] = Pose(jaw=1, drop=3)
    # slam (phase 2): rears up high; then crashes down into the water (a splash)
    f["windup_slam.0"] = Pose(raise_=9, phase2=True, jaw=1, crest=1, sway=-2)
    f["windup_slam.1"] = Pose(raise_=12, phase2=True, jaw=2, sway=-4)
    f["attack_slam.0"] = Pose(drop=16, raise_=-6, hs=1.08, phase2=True, splash=True, jaw=2)
    f["attack_slam.1"] = Pose(drop=10, raise_=-3, phase2=True, jaw=1)
    f["hurt.0"] = Pose(sway=-2, drop=-3, eyes="shut", jaw=2)
    f["stagger.0"] = Pose(sway=-5, drop=4, eyes="shut", jaw=1)
    f["stagger.1"] = Pose(sway=4, drop=6, eyes="shut")
    f["idle2.0"] = Pose(phase2=True)
    f["idle2.1"] = Pose(phase2=True, sway=1, raise_=1, crest=1)
    f["defeat.0"] = Pose(raise_=4, eyes="shut", jaw=3, phase2=True)
    f["defeat.1"] = Pose(collapse=1, drop=6, eyes="shut", jaw=1, phase2=True, sway=-2)
    f["defeat.2"] = Pose(collapse=3, drop=8, eyes="shut", phase2=True, sway=-3)
    f["defeat.3"] = Pose(collapse=4)
    return {k: draw(v) for k, v in f.items()}


SIZE = (W, H)
PATTERNS = ("ring", "volley", "slam")
