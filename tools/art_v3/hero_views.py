"""v3 hero, production (STYLE order 2): the side (facing right) and back (facing up) views.

Same parts and colours as the front view in gen_hero_v3.py (v1 ramps, v1 grey gauntlets, leather
hands, hair to below the ears), drawn on the 64 x 112 grid, the feet's bottom centre at (32, 111) like
v1's (bottom centre) anchor. Facing left is facing right mirrored (the game flips it; v1's left frames
are exact mirrors of its right frames for every action without a held prop).
"""

import math

import numpy as np

from hdkit import capsule, edge_band, grooves, lock
from v3lib import Canvas, despeckle

W, H = 64, 112

# the eye seen from the side (5 x 6): lid on top, the iris toward the front (right), v1's shine
EYE_SIDE = [  # the eye seen from the side (7 x 6): v1's side eye at 2x (the front eye's lid, iris and shine)
    "LLLLL..",
    "LLLLLLL",
    "DDDDWWG",
    "DIIIWWG",
    "DIKKI..",
    ".DIIB..",
]


def _shade_lock_set(c, locks, mass, lit_tones=(2, 3, 3, 4, 5)):
    for root, tip, w, bend in locks:
        m = lock(c, root, tip, w, bend)
        c.fill(m, "hair")
        c.shade_part(m, tones=lit_tones, norm=True, global_mask=mass, gmix=0.45)
        grooves(c, m, drop=1, sides=True)


# ---------------------------------------------------------------- side view (facing right)

def side_head(c, oy, lag, EYE, BLUSH, MOUTH, lean=0):
    """Profile: the big hair mass at the back (left), spikes up and back, the face on the right with
    one eye, a small nose step and the mouth at the front edge."""
    X = lean
    mass = c.m_poly([(4 + X, 18 + oy), (8 + X, 8 + oy), (18 + X, 2 + oy), (30 + X, 0 + oy), (42 + X, 4 + oy),
                     (50 + X, 12 + oy), (54 + X, 20 + oy), (50 + X, 24 + oy), (28 + X, 26 + oy),
                     (24 + X, 40 + oy + lag), (14 + X, 44 + oy + lag), (8 + X, 38 + oy)])
    c.fill(mass, "hair")
    c.shade_part(mass, tones=(1, 2, 2, 3, 3), norm=True)
    face = c.m_poly([(26 + X, 22 + oy), (50 + X, 21 + oy), (53 + X, 27 + oy), (53 + X, 33 + oy), (55 + X, 37 + oy),
                     (53 + X, 39 + oy), (52 + X, 43 + oy), (46 + X, 46 + oy), (36 + X, 46 + oy), (28 + X, 42 + oy)])
    c.fill(face, "skin", 4)
    for y, x in zip(*np.nonzero(face)):  # the jaw and the back of the cheek in shade
        if y >= 44 + oy or x <= 29 + X:
            c.tone[y, x] = 3
    # the ear (in front of the side hair), its inner shade
    ear = c.m_ellipse(30.5 + X, 34 + oy, 2.6, 3.6)
    c.fill(ear, "skin", 3)
    c.put(31 + X, 34 + oy, "skin", 2)
    c.put(31 + X, 35 + oy, "skin", 2)
    # locks: crown spikes up and back, the back locks flowing down the nape, bangs over the brow
    back = [((22 + X, 8 + oy), (2 + X, 20 + oy), 12, 3.0), ((26 + X, 12 + oy), (6 + X, 36 + oy + lag), 12, 3.0),
            ((24 + X, 20 + oy), (14 + X, 46 + oy + lag), 11, 2.0), ((28 + X, 6 + oy), (12 + X, 2 + oy), 9, 2.0)]
    top = [((32 + X, 6 + oy), (30 + X, -1 + oy), 9, 1.0), ((38 + X, 7 + oy), (46 + X, 0 + oy), 8, -1.5),
           ((44 + X, 12 + oy), (57 + X, 14 + oy), 8, -2.0)]
    bangs = [((40 + X, 14 + oy), (52 + X, 27 + oy), 8, -2.0), ((34 + X, 15 + oy), (40 + X, 28 + oy + lag), 8, -1.5),
             ((28 + X, 16 + oy), (27 + X, 30 + oy + lag), 7, 1.0)]
    _shade_lock_set(c, back + top, mass)
    fore = c.m_poly([(27 + X, 14 + oy), (52 + X, 15 + oy), (54 + X, 22 + oy), (46 + X, 26 + oy), (36 + X, 27 + oy),
                     (28 + X, 26 + oy)])  # the fringe over the forehead (v1: the hair comes down to the brow)
    c.fill(fore, "hair", 2)
    bangs = bangs + [((47 + X, 15 + oy), (55 + X, 27 + oy), 7, -1.5), ((44 + X, 16 + oy), (47 + X, 29 + oy + lag), 7, -1.0)]
    _shade_lock_set(c, bangs, mass)
    hairm = c.mat == c.mid("hair")
    for y, x in zip(*np.nonzero(c.mat == c.mid("skin"))):  # the bangs' shade on the face
        if y >= 2 and (hairm[y - 1, x] or hairm[y - 2, x]) and y < 34 + oy:
            c.tone[y, x] = 3
    # the eye (toward the front), the brow (2-row band) above it, the nose step, cheek, mouth
    ex, ey = 42 + X, 31 + oy
    for j, row in enumerate(EYE_SIDE):
        for i, ch in enumerate(row):
            if ch != ".":
                c.dot(ex + i, ey + j, EYE[ch])
    for xs, y in ((range(43, 49), ey - 2), (range(42, 47), ey - 1)):
        for x in xs:
            c.put(x + X, y, "hair", 1)
    c.put(54 + X, 38 + oy, "skin", 2)
    c.dot(46 + X, ey + 7, BLUSH)
    c.dot(47 + X, ey + 7, BLUSH)
    for x in range(49, 53):
        c.dot(x + X, 42 + oy, MOUTH)
    c.dot(51 + X, 43 + oy, MOUTH)


def side_leg(c, hip, foot, lift, near, bend=0.0):
    """Thigh + shin (trousers) from the hip to the ankle, the boot pointing right. lift: heel up."""
    hx, hy = hip
    fx, fy = foot  # the sole's back corner (heel), on the ground when fy == 111
    kx, ky = (hx + fx) / 2 + bend, (hy + fy - 14) / 2
    t = capsule(c, (hx, hy), (kx, ky), 3.4) | capsule(c, (kx, ky), (fx + 3, fy - 15), 3.2)
    c.fill(t, "trousers")
    c.shade_part(t, tones=(1, 2, 3, 3), norm=True, light=(-0.9, -0.1, 0.4))
    bt = fy - 15
    shaft = c.m_poly([(fx - 1, bt), (fx + 8, bt), (fx + 8, bt + 9), (fx - 1, bt + 9)])
    toe = c.m_poly([(fx - 1, bt + 9), (fx + 8, bt + 8), (fx + 14 - lift, bt + 11 + lift * 0.3),
                    (fx + 14 - lift, fy - 1), (fx - 1, fy - 1)])
    c.fill(shaft | toe, "boot")
    c.shade_part(shaft | toe, tones=(1, 2, 3, 3, 4), norm=True)
    c.fill(c.m_rect(fx - 1, bt, fx + 8, bt + 2), "leather", 3)  # the cuff
    c.fill(c.m_rect(fx - 1, bt, fx + 8, bt), "leather", 5)
    c.fill(c.m_rect(fx - 1, bt + 3, fx + 8, bt + 3), "leather", 1)
    c.fill(c.m_rect(fx - 1, fy - 1, fx + 14 - lift, fy), "boot", 1)  # the sole
    c.put(int(fx + 11 - lift), int(bt + 11), "boot", 5)
    if not near:
        c.set_tone(t | shaft | toe, 1)
        c.fill(c.m_rect(fx - 1, bt, fx + 8, bt + 2) & (c.mat == c.mid("leather")), "leather", 2)


def side_arm(c, shoulder, swing, near, oy, bent=0.0):
    """The gauntleted forearm and hand, swinging forward (+, right) or back (-). bent: run (forearm
    raised forward, the fist in front of the chest)."""
    sx, sy = shoulder
    ex, ey = sx + 4 * swing, sy + 12
    if bent:
        wx, wy = ex + 9 * bent, ey + 2 - 7 * bent * (1 if swing >= 0 else 0.3)
    else:
        wx, wy = ex + 7 * swing, ey + 11 - 2 * abs(swing)
    upper = capsule(c, (sx, sy), (ex, ey), 3.6)
    c.fill(upper, "shirt", 3)
    c.shade_part(upper, tones=(2, 3, 3, 4), norm=True)
    g = capsule(c, (ex, ey), (wx, wy), 3.8)
    c.fill(g, "shirt")
    c.shade_part(g, tones=(0, 0, 1, 1, 3), norm=True, light=(-0.9, -0.2, 0.4))
    for t in (0.2, 0.65):
        bx, by = ex + (wx - ex) * t, ey + (wy - ey) * t
        dx, dy = wy - ey, -(wx - ex)
        L = math.hypot(dx, dy) or 1
        band = c.m_line([(bx - 4 * dx / L, by - 4 * dy / L), (bx + 4 * dx / L, by + 4 * dy / L)], 1.2) & g
        c.set_tone(band, 0)
    c.put(int(round(ex)), int(round(ey + 1)), "shirt", 4)
    L = math.hypot(wx - ex, wy - ey) or 1
    ux, uy = (wx - ex) / L, (wy - ey) / L
    fist = c.m_ellipse(wx + ux * 3.5, wy + uy * 3.5, 3.6, 3.8)
    c.fill(fist, "leather")
    c.shade_part(fist, tones=(1, 2, 3, 4), norm=True)
    c.put(int(round(wx + ux * 3.5 - 1)), int(round(wy + uy * 3.5 - 1)), "leather", 5)
    if not near:
        c.set_tone(upper | g | fist, 1)


def side_frame(R, EYE, BLUSH, MOUTH, oy=0, lag=0, sway=0, legs=((0, 0, 0), (0, 0, 0)), arms=(0.0, 0.0),
               lean=0, bent=0.0, cloak_fly=0.0, breath=0):
    """legs: (dx of the foot from the body line, lift of the heel, knee bend) for the far and near leg.
    arms: swing of the far and near arm. lean: the upper body forward (run)."""
    c = Canvas(W, H, R)
    hip = (32 + lean * 0.3, 78 + oy)
    # the far arm (behind the body), the far leg
    side_arm(c, (30 + lean, 52 + oy - breath), arms[0], False, oy, bent)
    for k, (dx, lift, bend) in enumerate(legs):
        if k == 1:
            continue
        side_leg(c, hip, (27 + dx, 111 - lift), max(0, lift // 2), False, bend)
    # the cloak behind (from the shoulders to the hem, flaring back; cloak_fly lifts it in the run)
    hem = 92 + oy
    back = c.m_poly([(26 + lean, 46 + oy - breath), (36 + lean, 46 + oy - breath), (34 + lean * 0.5, 60 + oy),
                     (30, 86 + oy), (29 + sway, hem - cloak_fly * 3), (16 + sway - cloak_fly * 6, hem - cloak_fly * 8),
                     (6 + sway - cloak_fly * 10, hem - 2 - cloak_fly * 12), (8 - cloak_fly * 6, 72 + oy - cloak_fly * 6),
                     (14 + lean * 0.5, 54 + oy), (20 + lean, 47 + oy)])
    c.fill(back, "cloak", 3)
    yy, xx = np.nonzero(back)
    for y, x in zip(yy, xx):
        c.tone[y, x] = 4 if x < 12 + (y - 50) * 0.05 else (2 if x > 26 else 3)
    for x0, x1 in ((20, 12), (25, 19)):  # two long folds down the back
        ridge = c.m_line([(x0 + lean * 0.5, 52 + oy), (x1 + sway - cloak_fly * 6, hem - 2 - cloak_fly * 8)], 2.4) & back
        groove = c.m_line([(x0 + 2.5 + lean * 0.5, 54 + oy), (x1 + 3 + sway - cloak_fly * 6, hem - 2 - cloak_fly * 8)], 1.6) & back
        for y, x in zip(*np.nonzero(ridge)):
            c.tone[y, x] = min(5, int(c.tone[y, x]) + 1)
        for y, x in zip(*np.nonzero(groove)):
            c.tone[y, x] = max(1, int(c.tone[y, x]) - 1)
    hemm = np.zeros((H, W), bool)
    for x in range(0, W):
        ys = np.nonzero(back[:, x])[0]
        if len(ys) and ys.max() > 70 + oy:
            for d in range(3):
                hemm[ys.max() - d, x] = True
    c.fill(hemm, "gold", 3)
    for y, x in zip(*np.nonzero(hemm)):
        c.tone[y, x] = 4 if not hemm[y - 1, x] else (1 if not (y + 1 < H and hemm[y + 1, x]) else 3)
    # the near leg
    dx, lift, bend = legs[1]
    side_leg(c, hip, (29 + dx, 111 - lift), max(0, lift // 2), True, bend)
    # the torso: the tunic front, the belt and pouch, the pendant at the chest's front edge
    torso = c.m_poly([(28 + lean, 48 + oy - breath), (41 + lean, 48 + oy - breath), (43 + lean, 58 + oy),
                      (42 + lean * 0.6, 70 + oy), (41, 82 + oy), (27, 82 + oy), (27 + lean * 0.5, 62 + oy)])
    c.fill(torso, "shirt")
    c.shade_part(torso, tones=(2, 3, 3, 4, 4), norm=True, light=(-0.2, -0.6, 0.5))
    belt = c.m_rect(26 + lean * 0.6, 68 + oy, 43 + lean * 0.6, 71 + oy) & (torso | c.m_rect(26, 68 + oy, 44 + lean, 71 + oy))
    c.fill(belt, "leather", 2)
    c.fill(belt & c.m_rect(0, 68 + oy, W, 68 + oy), "leather", 4)
    bx = int(39 + lean * 0.6)
    c.fill(c.m_rect(bx, 67 + oy, bx + 3, 72 + oy), "gold", 3)
    c.put(bx, 67 + oy, "gold", 5)
    c.fill(c.m_rect(25 + lean * 0.5, 71 + oy, 30 + lean * 0.5, 78 + oy), "leather", 3)  # the pouch at the hip
    c.fill(c.m_rect(25 + lean * 0.5, 71 + oy, 30 + lean * 0.5, 72 + oy), "leather", 4)
    # the hood rolled round the neck (cloak green)
    hood = c.m_ellipse(31 + lean, 47 + oy - breath, 10, 4.2)
    c.fill(hood, "cloak")
    c.shade_part(hood, tones=(2, 3, 4, 4, 5), norm=True)
    gy = 54 + oy
    gx = 41 + lean
    c.fill(c.m_poly([(gx, gy - 4), (gx + 4, gy), (gx, gy + 4), (gx - 3, gy)]), "gold", 2)
    gem = c.m_poly([(gx, gy - 2.5), (gx + 2.5, gy), (gx, gy + 2.5), (gx - 2, gy)])
    c.fill(gem, "gem", 3)
    c.put(gx - 1, gy - 1, "gem", 5)
    c.put(gx + 1, gy + 1, "gem", 2)
    # the near arm in front
    side_arm(c, (32 + lean, 52 + oy - breath), arms[1], True, oy, bent)
    side_head(c, oy, lag, EYE, BLUSH, MOUTH, lean=lean)
    despeckle(c, loose=("hair", "cloak"))
    edge_band(c, "cloak", 1)
    c.outline()
    c.shadow_band()
    return c


# ---------------------------------------------------------------- back view (facing up)

def back_frame(R, oy=0, lag=0, sway=0, feet=(0, 0), arms=(0.0, 0.0), breath=0, bent=0.0):
    """The back: the hair as one big mass with locks falling to the nape, the cloak from the shoulders
    to the hem with the gold star between the shoulder blades, the grey gauntlets at the sides, the
    boots' heels below the hem. feet: lift of the left / right foot (the sole shows when lifted)."""
    c = Canvas(W, H, R)
    # boots (behind the cloak's hem)
    for side, lift in ((-1, feet[0]), (1, feet[1])):
        x0 = 31.5 + side * 7
        bt = 92 - lift
        boot = c.m_poly([(x0 - 6, bt), (x0 + 6, bt), (x0 + 6.5, 110 - lift), (x0 - 6.5, 110 - lift)])
        c.fill(boot, "boot")
        c.shade_part(boot, tones=(1, 2, 3, 3), norm=True)
        c.fill(c.m_rect(x0 - 6.5, 110 - lift, x0 + 6.5, 111 - lift), "boot", 1)
        c.fill(c.m_rect(x0 - 6, bt, x0 + 6, bt + 3), "leather", 3)  # the cuff, as in front
        c.fill(c.m_rect(x0 - 6, bt, x0 + 6, bt), "leather", 5)
        c.fill(c.m_rect(x0 - 6, bt + 3, x0 + 6, bt + 3), "leather", 1)
        c.fill(c.m_rect(x0 + 2, bt + 5, x0 + 5, 109 - lift) & boot, "boot", 1)  # the back seam's shade
        if lift > 1:  # the sole and heel show
            c.fill(c.m_rect(x0 - 5, 106 - lift, x0 + 5, 111 - lift), "boot", 1)
            c.fill(c.m_rect(x0 - 3, 108 - lift, x0 + 3, 110 - lift), "leather", 2)
        tr = c.m_rect(x0 - 4, 86 + oy, x0 + 4, bt)
        c.fill(tr & (c.mat == 0), "trousers", 2)
    # the arms at the sides (gauntlet + hand), mostly outside the cloak
    for side, s in ((-1, arms[0]), (1, arms[1])):
        sx = 31.5 + side * 22
        ex, ey = sx, 58 + oy
        wx, wy = sx - side * 1.0 * bent * 6, ey + 12 - 3 * abs(s) - 4 * bent
        wy += -2 * s
        g = capsule(c, (ex, ey), (wx, wy), 3.8)
        c.fill(g, "shirt")
        c.shade_part(g, tones=(0, 0, 1, 1, 3), norm=True, light=(-0.9, -0.2, 0.4))
        for t in (0.2, 0.65):
            by = ey + (wy - ey) * t
            c.set_tone(c.m_line([(ex - 5, by), (ex + 5, by)], 1.2) & g, 0)
        fist = c.m_ellipse(wx, wy + 4, 4, 4.2)
        c.fill(fist, "leather")
        c.shade_part(fist, tones=(1, 2, 3, 4), norm=True)
    # the cloak
    hem = 92 + oy
    body = c.m_poly([(20, 44 + oy - breath), (44, 44 + oy - breath), (52, 52 + oy), (54, 70 + oy),
                     (56 + sway, hem - 1), (8 + sway, hem - 1), (10, 70 + oy), (12, 52 + oy)])
    c.fill(body, "cloak", 3)
    for y, x in zip(*np.nonzero(body)):
        c.tone[y, x] = 4 if x < 16 else (2 if x > 46 else 3)
    for x0, x1 in ((18, 14), (25, 23), (39, 41), (46, 50)):  # long folds down the back
        ridge = c.m_line([(x0, 54 + oy), (x1 + sway, hem - 2)], 2.4) & body
        groove = c.m_line([(x0 + 2.5, 56 + oy), (x1 + 2.5 + sway, hem - 2)], 1.6) & body
        for y, x in zip(*np.nonzero(ridge)):
            c.tone[y, x] = min(5, int(c.tone[y, x]) + 1)
        for y, x in zip(*np.nonzero(groove)):
            c.tone[y, x] = max(1, int(c.tone[y, x]) - 1)
    hemm = np.zeros((H, W), bool)
    for x in range(W):
        ys = np.nonzero(body[:, x])[0]
        if len(ys):
            for d in range(3):
                hemm[ys.max() - d, x] = True
    c.fill(hemm, "gold", 3)
    for y, x in zip(*np.nonzero(hemm)):
        c.tone[y, x] = 4 if not hemm[y - 1, x] else (1 if not (y + 1 < H and hemm[y + 1, x]) else 3)
    # the gold star (v1's back emblem) with the blue gem in its middle
    cx, cy = 31.5, 72 + oy
    star = c.m_line([(cx, cy - 8), (cx, cy + 8)], 1.6) | c.m_line([(cx - 8, cy), (cx + 8, cy)], 1.6) | \
        c.m_line([(cx - 4.5, cy - 4.5), (cx + 4.5, cy + 4.5)], 1.2) | c.m_line([(cx - 4.5, cy + 4.5), (cx + 4.5, cy - 4.5)], 1.2)
    c.fill(star & body, "gold", 3)
    for y, x in zip(*np.nonzero(star & body)):
        c.tone[y, x] = 4 if (x < cx and y < cy) else 3
    gem = c.m_ellipse(cx, cy, 2.2, 2.2)
    c.fill(gem, "gem", 3)
    c.put(int(cx - 1), int(cy - 1), "gem", 5)
    # the hood rolled round the shoulders
    hood = c.m_ellipse(31.5, 46 + oy - breath, 20, 5.5)
    c.fill(hood & (body | c.m_rect(10, 40 + oy, 54, 52 + oy)), "cloak")
    c.shade_part(hood, tones=(2, 3, 4, 4, 5), norm=True)
    grooves(c, hood, drop=1)
    # the hair from behind: one mass, locks falling from the crown to the nape, spikes on top
    mass = c.m_poly([(3, 18 + oy), (10, 6 + oy), (22, 1 + oy), (34, 0 + oy), (46, 3 + oy), (55, 10 + oy), (60, 20 + oy),
                     (58, 32 + oy), (52, 40 + oy + lag), (40, 44 + oy + lag), (24, 44 + oy + lag), (12, 40 + oy + lag),
                     (6, 32 + oy)])
    c.fill(mass, "hair")
    c.shade_part(mass, tones=(1, 2, 2, 3, 3), norm=True)
    cr = (31, 10 + oy)
    locks = [((cr[0] - 3, cr[1]), (6, 34 + oy), 12, 3.0), ((cr[0] + 3, cr[1]), (57, 34 + oy), 12, -3.0),
             ((cr[0] - 2, cr[1] + 2), (16, 42 + oy + lag), 11, 2.0), ((cr[0] + 2, cr[1] + 2), (47, 42 + oy + lag), 11, -2.0),
             ((cr[0], cr[1] + 3), (30, 45 + oy + lag), 10, 0.5), ((cr[0] - 1, cr[1] + 3), (23, 44 + oy + lag), 9, 1.0),
             ((cr[0] + 1, cr[1] + 3), (39, 44 + oy + lag), 9, -1.0)]
    spikes = [((26, 10 + oy), (20, -1 + oy), 9, 1.5), ((32, 9 + oy), (33, -2 + oy), 9, 0.5),
              ((37, 10 + oy), (44, 0 + oy), 8, -1.5), ((12, 14 + oy), (1, 15 + oy), 8, 2.0),
              ((51, 14 + oy), (62, 19 + oy), 8, -2.0)]
    _shade_lock_set(c, spikes + locks, mass)
    c.put(cr[0], cr[1], "hair", 1)  # the whorl
    c.put(cr[0] + 1, cr[1] + 1, "hair", 1)
    despeckle(c, loose=("hair", "cloak"))
    edge_band(c, "cloak", 1)
    c.outline()
    c.shadow_band()
    return c
