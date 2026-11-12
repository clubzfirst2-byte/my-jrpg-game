"""v3 NPC production (STYLE order 5): the village woman (npc.woman), every key of the approved v1 woman
(src/art-release/npc/npc.woman.*: idle 4 / walk 6 for down, right, up, left; fps from src/view/npcAnim.js;
anchor = the bottom row's centre). Her own parts (not the hero's head): the red headscarf with its rolled
hem, auburn hair under it, the plait over her right shoulder, the cream blouse with puffed sleeves, the plum
skirt, the ochre apron with 2 pockets, the wicker basket of herbs on her left forearm. Colours and the
front view: gen_npc_v3.py (the approved pilot). This module adds the walk to the front view and draws the
side (right / left) and back views part by part. Facing left is drawn on its own (v1's left frames are not
the mirror of the right ones: the basket is on her left arm, the plait on her right shoulder).
"""

import math

import numpy as np

import gen_npc_v3 as P
from hdkit import capsule, edge_band, grooves, lock
from v3lib import Canvas, despeckle

W, H = 64, 112

EYE_SIDE = [  # the eye from the side: the lid line arched over the iris, the iris to the front
    ".LLLL.",
    "LIIKWL",
    ".IIKW.",
    ".DIIB.",
]
EYE_SIDE_SHUT = ["......", ".LLLL.", "L....L", "......"]


def _finish(c):
    despeckle(c, loose=("hair",))
    edge_band(c, "skirt", 1, sides=((1, 0), (0, 1)))
    c.outline()
    c.shadow_band()
    return c


def _plait(c, x, y, n, dx, sway=0.0):
    """A plait of n lobes going down (dx: drift per lobe), its red tie and the tuft."""
    for k in range(n):
        lx = x + dx * k + (1.2 if k % 2 else -1.2) + sway * k / max(1, n - 1)
        m = c.m_ellipse(lx, y + 3.5 * k, 3.2, 2.8)
        c.fill(m, "hair")
        c.shade_part(m, tones=(1, 2, 3, 4, 5), norm=True)
        grooves(c, m, drop=2, lift=0)
    ex, ey = x + dx * n + sway, y + 3.5 * n - 0.5
    c.fill(c.m_ellipse(ex, ey, 2.8, 1.5), "scarf", 3)
    tuft = c.m_poly([(ex - 2.5, ey + 1), (ex + 2.5, ey + 1), (ex + 1, ey + 6), (ex - 1, ey + 6)])
    c.fill(tuft, "hair")
    c.shade_part(tuft, tones=(2, 3, 4), norm=True)


def _skirt(c, pts, lit_x, shade_x, pleats, oy):
    sk = c.m_poly(pts)
    c.fill(sk, "skirt", 3)
    for y, x in zip(*np.nonzero(sk)):
        c.tone[y, x] = 4 if x < lit_x else (1 if x > shade_x else 3)
    for x0, x1 in pleats:
        g = c.m_line([(x0, 70 + oy), (x1, 106)], 1.6) & sk
        r = c.m_line([(x0 - 2, 70 + oy), (x1 - 2.5, 106)], 2.2) & sk
        for y, x in zip(*np.nonzero(r)):
            c.tone[y, x] = min(5, int(c.tone[y, x]) + 1)
        for y, x in zip(*np.nonzero(g)):
            c.tone[y, x] = max(1, int(c.tone[y, x]) - 1)
    for x in range(W):  # the hem's lit fold line
        ys = np.nonzero(sk[:, x])[0]
        if len(ys) > 3:
            c.tone[ys.max() - 1, x] = min(5, int(c.tone[ys.max() - 1, x]) + 1)
    return sk


def _shoe(c, x, y, w=4.5):
    s = c.m_ellipse(x, y, w, 2.6) & c.m_rect(0, y - 2, W - 1, H - 1)
    c.fill(s, "leather")
    c.shade_part(s, tones=(1, 2, 3, 4), norm=True)


def _basket(c, x0, y0, w=16, herbs=True):
    """The wicker basket (over-under weave), its rim, herbs heaped in it."""
    bk = c.m_poly([(x0, y0), (x0 + w, y0), (x0 + w - 2, y0 + 9), (x0 + 2, y0 + 9)])
    c.fill(bk, "wicker", 3)
    for y, x in zip(*np.nonzero(bk)):
        row = (y - y0) // 2
        u = ((x + (row % 2) * 2) // 3) % 2
        t = (3 if u else 2) + (1 if x < x0 + 3 else 0) - (1 if x > x0 + w - 3 else 0)
        c.tone[y, x] = max(1, t)
    c.fill(c.m_rect(x0, y0 - 1, x0 + w, y0), "wicker", 4)
    c.fill(c.m_rect(x0, y0, x0 + w, y0), "wicker", 2)
    if herbs:
        for (dx, dy, r) in ((3, -3, 3.0), (8, -4.5, 3.4), (13, -3, 2.8), (6, -2, 2.4)):
            m = c.m_ellipse(x0 + dx, y0 + dy, r, r * 0.8)
            c.fill(m, "herb")
            c.shade_part(m, tones=(1, 2, 3, 4, 5), norm=True)
        c.put(x0 + 9, y0 - 6, "blouse", 5)
        c.put(x0 + 10, y0 - 6, "blouse", 4)
    for k in range(17):  # the handle
        t = k / 16
        c.put(int(round(x0 + w * t)), int(round(y0 - 1 - 6 * math.sin(math.pi * t))), "wicker", 4 if t < 0.5 else 2)


# ---------------------------------------------------------------- front view: the walk

def front(oy=0, breath=0, blink=False, sway=0.0, step=0, hem=0):
    """gen_npc_v3.frame plus the walk: step -1 / 0 / +1 brings one shoe forward (lower, larger) and
    lifts the other (hidden under the hem); hem swings the skirt's lower edge sideways."""
    c = Canvas(W, H, P.RAMPS)
    P.body(c, oy, breath)
    if step or hem:
        # redo the shoes and swing the hem: clear below row 100 and redraw the hem and the shoes
        for x in range(W):
            for y in range(100, H):
                if c.mat[y, x] in (c.mid("skirt"), c.mid("leather")):
                    c.mat[y, x] = 0
        lo = c.m_poly([(8 + hem, 99), (56 + hem, 99), (57 + hem, 104), (56 + hem, 107), (8 + hem, 107), (7 + hem, 104)])
        c.fill(lo & (c.mat == 0), "skirt", 3)
        for y, x in zip(*np.nonzero(lo)):
            if c.mat[y, x] == c.mid("skirt"):
                c.tone[y, x] = 4 if x < 14 else (1 if x > 50 else 3)
        for x in range(W):
            ys = np.nonzero(c.mat[:, x] == c.mid("skirt"))[0]
            if len(ys):
                c.tone[ys.max() - 1, x] = min(5, int(c.tone[ys.max() - 1, x]) + 1)
        for sx, s in ((27, -step), (37, step)):
            if s >= 0:
                _shoe(c, sx, 109 + (1 if s > 0 else 0), 4.5 + 0.5 * s)
    P.braid(c, oy, sway)
    P.arms_and_basket(c, oy, breath)
    P.head(c, oy, blink, sway)
    return _finish(c)


# ---------------------------------------------------------------- side view (facing right)

def side(oy=0, breath=0, blink=False, sway=0.0, step=0, hem=0, left=False):
    """Facing right. left=True: the frame for facing left (drawn facing right, then mirrored by the
    caller): her right side is near, so the plait hangs in front and the basket is on the far arm,
    carried a little lower in front of the skirt (v1)."""
    c = Canvas(W, H, P.RAMPS)
    # the far shoe, the skirt
    _shoe(c, 28 - 4 * step, 109, 4.5)
    _skirt(c, [(23, 63 + oy), (41, 63 + oy), (46 + hem, 86), (51 + hem, 104), (50 + hem, 107),
               (12 + hem, 107), (11 + hem, 103), (16, 84)], 18, 44,
           ((28, 22 + hem), (35, 36 + hem)), oy)
    _shoe(c, 37 + 4 * step, 109, 5.0)
    # the apron's front edge (seen edge-on), with the pocket's corner
    ap = c.m_poly([(39, 66 + oy), (43, 66 + oy), (48 + hem, 101), (44 + hem, 101)])
    c.fill(ap, "apron", 3)
    c.fill(c.m_line([(43, 66 + oy), (48 + hem, 101)], 1.2) & ap, "apron", 2)
    c.fill(c.m_rect(41, 77 + oy, 45, 78 + oy) & ap, "apron", 1)
    # the blouse
    bl = c.m_poly([(25, 48 + oy - breath), (38, 48 + oy - breath), (42, 56 + oy), (41, 64 + oy), (24, 64 + oy)])
    c.fill(bl, "blouse")
    c.shade_part(bl, tones=(2, 3, 3, 4), norm=True)
    c.fill(c.m_rect(23, 63 + oy, 42, 66 + oy), "skirt", 1)  # the waistband
    c.fill(c.m_rect(23, 63 + oy, 42, 63 + oy), "skirt", 3)
    neck = c.m_poly([(29, 44 + oy), (35, 44 + oy), (36, 50 + oy - breath), (29, 50 + oy - breath)])
    c.fill(neck, "skin", 2)
    if left:  # facing left: the basket on the far arm, held in front of the skirt
        _basket(c, 37, 72 + oy, 15)
        c.fill(c.m_ellipse(44, 70 + oy, 3.0, 2.8), "skin", 2)
    # the plait over her right shoulder: behind facing right (only its end shows), in front facing left
    if left:
        _plait(c, 36, 50 + oy, 8, 0.6, sway)
    # the near arm: the puffed sleeve, the forearm forward to the basket's handle (facing right)
    sl = c.m_ellipse(31, 54 + oy - breath, 6, 6.5)
    c.fill(sl, "blouse")
    c.shade_part(sl, tones=(1, 2, 3, 4, 5), norm=True)
    c.fill(c.m_rect(26, 59 + oy - breath, 36, 60 + oy - breath) & sl, "blouse", 1)
    if not left:
        ua = capsule(c, (31, 60 + oy), (33, 66 + oy), 2.8)
        fa = capsule(c, (33, 66 + oy), (42, 62 + oy), 2.6)
        c.fill(ua | fa, "skin")
        c.shade_part(ua | fa, tones=(1, 2, 3, 4), norm=True)
        _basket(c, 36, 66 + oy, 16)
        hd = c.m_ellipse(43, 61 + oy, 3.2, 3.0)
        c.fill(hd, "skin")
        c.shade_part(hd, tones=(2, 3, 4), norm=True)
        grooves(c, hd, drop=2, lift=0)
    else:
        ua = capsule(c, (31, 60 + oy), (31, 70 + oy), 2.8)  # her right arm hangs at her side
        c.fill(ua, "skin")
        c.shade_part(ua, tones=(1, 2, 3, 4), norm=True)
        c.fill(c.m_ellipse(31, 72 + oy, 3.0, 3.4), "skin", 3)
    _side_head(c, oy, blink, sway)
    return _finish(c)


def _side_head(c, oy, blink, sway):
    # the hair under the scarf at the back of the head, down to the nape
    hb = c.m_poly([(13, 20 + oy), (28, 20 + oy), (30, 40 + oy), (26, 46 + oy), (18, 44 + oy), (12, 34 + oy)])
    c.fill(hb, "hair")
    c.shade_part(hb, tones=(1, 2, 2, 3), norm=True)
    for root, tip, w, bend in (((20, 22 + oy), (17, 42 + oy), 7, 1.0), ((26, 22 + oy), (25, 44 + oy), 7, 0.5)):
        m = lock(c, root, tip, w, bend)
        c.fill(m, "hair")
        c.shade_part(m, tones=(2, 3, 4, 5), norm=True)
        grooves(c, m)
    face = c.m_poly([(27, 22 + oy), (47, 22 + oy), (50, 28 + oy), (50, 32 + oy), (53, 36 + oy), (50, 38 + oy),
                     (50, 42 + oy), (46, 46 + oy), (38, 48 + oy), (30, 46 + oy), (27, 40 + oy)])
    c.fill(face, "skin")
    c.shade_part(face, tones=(2, 3, 3, 3, 4), norm=True, light=(-0.2, -0.4, 0.8))
    ear = c.m_ellipse(30.5, 34 + oy, 2.4, 3.6)
    c.fill(ear, "skin", 3)
    c.put(31, 34 + oy, "skin", 1)
    c.put(31, 35 + oy, "skin", 1)
    # a lock in front of the ear from under the scarf
    m = lock(c, (34, 22 + oy), (34, 34 + oy), 6, -0.5)
    c.fill(m, "hair")
    c.shade_part(m, tones=(2, 3, 4, 5), norm=True)
    # the headscarf seen from the side: the rounded cap, a fold line, the rolled hem
    cap = c.m_poly([(12, 25 + oy), (11, 15 + oy), (16, 7 + oy), (26, 3 + oy), (38, 4 + oy), (46, 9 + oy),
                    (50, 17 + oy), (50, 25 + oy)])
    c.fill(cap, "scarf")
    c.shade_part(cap, tones=(2, 3, 3, 4, 4), norm=True)
    for k in range(12):
        t = k / 11
        c.put(int(round(26 + 12 * t)), int(round(8 + oy + 9 * t ** 1.2)), "apron", 4)
        c.put(int(round(26 + 12 * t)) + 1, int(round(8 + oy + 9 * t ** 1.2)), "apron", 3)
    c.fill(c.m_rect(11, 22 + oy, 50, 25 + oy) & cap, "scarf", 2)
    c.fill(c.m_rect(11, 22 + oy, 50, 22 + oy) & cap, "scarf", 4)
    c.fill(c.m_rect(11, 25 + oy, 50, 25 + oy) & cap, "scarf", 1)
    for x in range(28, 50):
        if c.mat[26 + oy, x] == c.mid("skin"):
            c.tone[26 + oy, x] = 2
    rows = EYE_SIDE_SHUT if blink else EYE_SIDE
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch != ".":
                c.dot(41 + i, 32 + oy + j, P.INK[ch])
    for dx in range(3):
        c.dot(41 + dx, 39 + oy, P.INK["r"])
    c.dot(45, 39 + oy, P.INK["q"])
    c.put(52, 37 + oy, "skin", 2)  # under the nose
    for x, y, ch in ((46, 42, "M"), (47, 42, "M"), (48, 41, "M"), (47, 43, "o")):  # the smile, its corner up
        c.dot(x, y + oy, P.INK[ch])


# ---------------------------------------------------------------- back view

def back(oy=0, breath=0, sway=0.0, step=0, hem=0):
    c = Canvas(W, H, P.RAMPS)
    for sx, s in ((27, -step), (37, step)):  # the heels below the hem
        if s >= 0:
            _shoe(c, sx, 109, 4.2)
    _skirt(c, [(15, 64 + oy), (49, 64 + oy), (55 + hem, 86), (58 + hem, 104), (57 + hem, 107), (7 + hem, 107),
               (6 + hem, 104), (9 + hem, 86)], 14, 50, ((20, 14 + hem), (26, 23 + hem), (38, 41 + hem), (45, 51 + hem)), oy)
    # the basket on her left arm: on the image's left, at her hip (behind the skirt's edge)
    _basket(c, 2, 66 + oy, 15)
    bl = c.m_poly([(17, 48 + oy - breath), (47, 48 + oy - breath), (49, 64 + oy), (15, 64 + oy)])
    c.fill(bl, "blouse")
    c.shade_part(bl, tones=(2, 3, 3, 4), norm=True)
    c.fill(c.m_line([(32, 50 + oy), (32, 63 + oy)], 1.2) & bl, "blouse", 2)  # the back seam
    c.fill(c.m_rect(15, 64 + oy, 49, 67 + oy), "skirt", 1)
    c.fill(c.m_rect(15, 64 + oy, 49, 64 + oy), "skirt", 3)
    # the apron's ties: a bow at the back of the waist
    for dx in (-1, 1):
        lp = c.m_ellipse(32 + dx * 3.5, 65 + oy, 3.2, 2.2)
        c.fill(lp, "apron", 3 if dx < 0 else 2)
        c.fill(capsule(c, (32 + dx * 1.5, 67 + oy), (32 + dx * 4, 74 + oy), 1.2), "apron", 3 if dx < 0 else 2)
    c.fill(c.m_rect(31, 64 + oy, 33, 66 + oy), "apron", 1)
    # arms: her right (image right) hangs; her left (image left) bent to the basket
    for sx, side in ((14, -1), (50, 1)):
        p = c.m_ellipse(sx, 53 + oy - breath, 6, 6.5)
        c.fill(p, "blouse")
        c.shade_part(p, tones=(1, 2, 3, 4, 5), norm=True)
        c.fill(c.m_rect(sx - 5, 58 + oy - breath, sx + 5, 59 + oy - breath) & p, "blouse", 1)
    a = capsule(c, (52, 59 + oy), (52, 70 + oy), 3.0)
    c.fill(a, "skin")
    c.shade_part(a, tones=(1, 2, 3, 4), norm=True)
    c.fill(c.m_ellipse(52, 72 + oy, 3.2, 3.6), "skin", 2)
    fa = capsule(c, (12, 59 + oy), (10, 66 + oy), 2.8)
    c.fill(fa, "skin")
    c.shade_part(fa, tones=(1, 2, 3), norm=True)
    # the hair below the scarf, the plait over her right shoulder (image right)
    hb = c.m_poly([(12, 22 + oy), (52, 22 + oy), (53, 40 + oy), (46, 48 + oy), (18, 48 + oy), (11, 40 + oy)])
    c.fill(hb, "hair")
    c.shade_part(hb, tones=(1, 2, 3, 3, 4), norm=True)
    for x0 in (16, 23, 30, 37, 44):
        m = lock(c, (x0 + 2, 24 + oy), (x0 + 1.5, 46 + oy), 7, 0.6)
        c.fill(m, "hair")
        c.shade_part(m, tones=(2, 3, 3, 4, 5), norm=True, global_mask=hb, gmix=0.4)
        grooves(c, m, drop=1, sides=True)
    _plait(c, 45, 46 + oy, 8, 0.0, sway)
    # the headscarf from behind: the cap, the knot at the nape with 2 short tails, the rolled hem
    cap = c.m_poly([(12, 26 + oy), (11, 16 + oy), (15, 8 + oy), (23, 4 + oy), (41, 4 + oy), (49, 8 + oy),
                    (53, 16 + oy), (52, 26 + oy)])
    c.fill(cap, "scarf")
    c.shade_part(cap, tones=(2, 3, 3, 4, 4), norm=True)
    for k in range(13):
        t = k / 12
        for (ax, sgn) in ((24, -1), (40, 1)):
            c.put(int(round(ax + sgn * 7 * t)), int(round(9 + oy + 10 * t ** 1.3)), "apron", 4 if sgn < 0 else 3)
    c.fill(c.m_rect(11, 23 + oy, 53, 26 + oy) & cap, "scarf", 2)
    c.fill(c.m_rect(11, 23 + oy, 53, 23 + oy) & cap, "scarf", 4)
    c.fill(c.m_rect(11, 26 + oy, 53, 26 + oy) & cap, "scarf", 1)
    knot = c.m_ellipse(32, 25 + oy, 4, 3)
    c.fill(knot, "scarf", 1)
    c.put(31, 24 + oy, "scarf", 3)
    for dx, tip in ((-1, (28 + sway, 33 + oy)), (1, (36 + sway, 34 + oy))):
        tl = lock(c, (32 + dx * 2, 27 + oy), tip, 4, 0.5 * dx)
        c.fill(tl, "scarf")
        c.shade_part(tl, tones=(1, 2, 3), norm=True)
    return _finish(c)


# ---------------------------------------------------------------- the frames

IDLE = [dict(), dict(breath=1, sway=0.5), dict(breath=1, sway=1.0, oy=1), dict(blink=True, sway=0.5)]
WALK = [dict(step=1, hem=1, sway=0.5), dict(step=1, hem=1, oy=1, sway=1.0), dict(step=0, hem=0, sway=0.5),
        dict(step=-1, hem=-1, sway=-0.5), dict(step=-1, hem=-1, oy=1, sway=-1.0), dict(step=0, hem=0, sway=-0.5)]


def frames(action, view):
    poses = {"idle": IDLE, "walk": WALK}[action]
    out = []
    for p in poses:
        if view == "down":
            q = dict(p)
            if action == "idle":
                q.pop("step", None)
            out.append(front(**q))
        elif view in ("right", "left"):
            out.append(side(left=view == "left", **p))
        else:
            q = {k: v for k, v in p.items() if k != "blink"}
            out.append(back(**q))
    return out
