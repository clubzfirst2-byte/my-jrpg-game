"""v3 hero, production (STYLE order 2): the side (facing right) and back (facing up) views.

Same parts and colours as the front view in gen_hero_v3.py (v1 ramps, v1 grey gauntlets, leather
hands, hair to below the ears), drawn on the 64 x 112 grid, the feet's bottom centre at (32, 111) like
v1's (bottom centre) anchor. Facing left is facing right mirrored (the game flips it; v1's left frames
are exact mirrors of its right frames for every action without a held prop).
"""

import math

import numpy as np

from hdkit import capsule, edge_band, gauntlet, grooves, lock
from v3lib import Canvas, absorb_cloth_islands, despeckle

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


def _off(no_arms, side):
    """no_arms: True, False, or a set of the arms left out (side view: 0 far, 1 near; back: -1 / +1)."""
    return no_arms is True or (not isinstance(no_arms, bool) and side in no_arms)


def _shade_lock_set(c, locks, mass, lit_tones=(2, 3, 3, 4, 5)):
    for root, tip, w, bend in locks:
        m = lock(c, root, tip, w, bend)
        c.fill(m, "hair")
        c.shade_part(m, tones=lit_tones, norm=True, global_mask=mass, gmix=0.45)
        grooves(c, m, drop=1, sides=True)


# ---------------------------------------------------------------- side view (facing right)

def side_head(c, oy, lag, EYE, BLUSH, MOUTH, lean=0, blink=False):
    """Profile: the big hair mass at the back (left), spikes up and back, the face on the right with
    one eye, a small nose step and the mouth at the front edge."""
    X = lean
    # hero round 3: v1's onion crown (the middle spike highest) and the back hair as 4 locks pointing
    # back, their tips on the back edge (no round bun)
    mass = c.m_poly([(8 + X, 14 + oy), (14 + X, 11 + oy), (20 + X, 9 + oy), (26 + X, 7.5 + oy), (31 + X, 4 + oy),
                     (37 + X, 7.5 + oy), (45 + X, 10 + oy), (51 + X, 14 + oy), (54 + X, 20 + oy), (50 + X, 24 + oy),
                     (28 + X, 26 + oy), (24 + X, 38 + oy + lag), (14 + X, 41 + oy + lag), (12 + X, 36 + oy),
                     (6 + X, 34 + oy + lag), (8 + X, 29 + oy), (4 + X, 25 + oy + lag), (7 + X, 20 + oy),
                     (5 + X, 16 + oy + lag)])
    c.fill(mass, "hair")
    c.shade_part(mass, tones=(1, 2, 2, 3, 3), norm=True)
    # hero round 2: the nose's tip is the frontmost point of the profile (v1), the mouth inside the face
    face = c.m_poly([(26 + X, 22 + oy), (50 + X, 21 + oy), (53 + X, 27 + oy), (54 + X, 32 + oy), (57 + X, 36 + oy),
                     (54 + X, 38 + oy), (53 + X, 41 + oy), (51 + X, 44 + oy), (46 + X, 46 + oy), (36 + X, 46 + oy),
                     (28 + X, 42 + oy)])
    c.fill(face, "skin", 4)
    for y, x in zip(*np.nonzero(face)):  # the jaw and the back of the cheek in shade
        if y >= 44 + oy or x <= 29 + X:
            c.tone[y, x] = 3
    # locks: crown spikes up and back, the back locks flowing down the nape, bangs over the brow
    # hero round 2: the back hair is one mass behind the ear ending at the chin line, several short
    # pointed tips (no long lock hanging down the nape: it read as a ponytail)
    back = [((24 + X, 12 + oy), (5 + X, 16 + oy + lag), 11, 1.5), ((25 + X, 16 + oy), (4 + X, 25 + oy + lag), 11, 2.0),
            ((26 + X, 21 + oy), (6 + X, 34 + oy + lag), 10, 2.0), ((27 + X, 26 + oy), (14 + X, 41 + oy + lag), 9, 1.5)]
    top = [((31 + X, 13 + oy), (31 + X, 3 + oy), 9, 0.3), ((37 + X, 12 + oy), (43 + X, 8 + oy), 8, -1.0),
           ((44 + X, 14 + oy), (55 + X, 15 + oy), 8, -2.0), ((25 + X, 12 + oy), (19 + X, 8 + oy), 8, 1.0)]
    bangs = [((40 + X, 14 + oy), (52 + X, 27 + oy), 8, -2.0), ((34 + X, 15 + oy), (40 + X, 28 + oy + lag), 8, -1.5),
             ((28 + X, 16 + oy), (27 + X, 30 + oy + lag), 7, 1.0)]
    _shade_lock_set(c, back + top, mass)
    # the fringe over the forehead (round 4: its lower edge falls toward the front in 4 slanted locks, v1)
    fore = c.m_poly([(27 + X, 14 + oy), (52 + X, 15 + oy), (55 + X, 24 + oy), (53 + X, 30 + oy), (50 + X, 26 + oy),
                     (47 + X, 29 + oy), (43 + X, 24 + oy), (40 + X, 27 + oy), (36 + X, 22 + oy), (32 + X, 25 + oy),
                     (28 + X, 22 + oy)])
    c.fill(fore, "hair", 2)
    bangs = bangs + [((47 + X, 15 + oy), (54 + X, 30 + oy), 7, -1.5), ((44 + X, 16 + oy), (47 + X, 29 + oy + lag), 7, -1.0)]
    _shade_lock_set(c, bangs, mass)
    _shade_lock_set(c, [((26 + X, 26 + oy), (16 + X, 47 + oy + lag), 9, 1.5)], mass)  # the lock down the nape (v1)
    keep_to_outline(c, "right", oy, X)  # round 4: v1's outline (3 top spikes, the nape lock)
    # the ear (hero round 2: drawn over the back hair, 4 x 6, its inside one tone darker)
    ear = c.m_ellipse(30.5 + X, 35 + oy, 2.6, 3.6)
    c.fill(ear, "skin", 3)
    edge = ear & ~(np.roll(ear, 1, 0) & np.roll(ear, -1, 0) & np.roll(ear, 1, 1) & np.roll(ear, -1, 1))
    c.set_tone(edge & (c.mat == c.mid("skin")), 2)  # hero round 3: a darker rim and inside (readable)
    for yy in (34, 35, 36):
        c.put(31 + X, yy + oy, "skin", 1)
    # hero round 3: above row 16 the hair keeps to the onion (the mass) and the spikes only — the
    # crown locks' wide roots no longer square the top off
    _spk = np.zeros(c.mat.shape, bool)
    for _r, _t, _w, _b in top:
        _spk |= lock(c, _r, _t, _w, _b)
    _yy = np.mgrid[0:c.h, 0:c.w][0]
    _out = (c.mat == c.mid("hair")) & ~(mass | _spk) & (_yy < 16 + oy)
    c.mat[_out] = 0
    hairm = c.mat == c.mid("hair")
    for y, x in zip(*np.nonzero(c.mat == c.mid("skin"))):  # the bangs' shade on the face
        if y >= 2 and (hairm[y - 1, x] or hairm[y - 2, x]) and y < 34 + oy:
            c.tone[y, x] = 3
    # the eye (toward the front), the brow (2-row band) above it, the nose step, cheek, mouth
    ex, ey = 42 + X, 31 + oy
    for j, row in enumerate(EYE_SIDE if not blink else ["", "", ".LLLLL.", "..LLL..", ""]):
        for i, ch in enumerate(row):
            if ch != ".":
                c.dot(ex + i, ey + j, EYE[ch])
    for xs, y in ((range(43, 49), ey - 2), (range(42, 47), ey - 1)):
        for x in xs:
            c.put(x + X, y, "hair", 1)
    if 55 + X <= c.w - 4:
        c.put(55 + X, 37 + oy, "skin", 3)  # the nose's underside
    c.dot(46 + X, ey + 7, BLUSH)
    c.dot(47 + X, ey + 7, BLUSH)
    c.dot(49 + X, 42 + oy, MOUTH)  # the mouth: 2 x 1 inside the face (v1)
    c.dot(50 + X, 42 + oy, MOUTH)


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
    under = (c.mat == c.mid("shirt")) & ~upper & ~g  # the tunic under the arm
    c.fill(g, "shirt")
    gauntlet(c, g, (ex, ey), (wx, wy))
    ring = (np.roll(g, 1, 0) | np.roll(g, -1, 0) | np.roll(g, 1, 1) | np.roll(g, -1, 1)) & ~g & under
    c.tone[ring] = 1  # hero round 2: a 1-texel line parts the gauntlet from the white tunic
    L = math.hypot(wx - ex, wy - ey) or 1
    ux, uy = (wx - ex) / L, (wy - ey) / L
    fist = c.m_ellipse(wx + ux * 3.5, wy + uy * 3.5, 3.6, 3.8)
    c.fill(fist, "leather")
    c.shade_part(fist, tones=(1, 2, 3, 4), norm=True)
    c.put(int(round(wx + ux * 3.5 - 1)), int(round(wy + uy * 3.5 - 1)), "leather", 5)
    if not near:
        c.set_tone(upper | g | fist, 1)


def _largest(m):
    """The largest 4-connected piece of mask m."""
    lab = np.zeros(m.shape, np.int32)
    n, best, bestn = 0, 0, 0
    for y0, x0 in zip(*np.nonzero(m)):
        if lab[y0, x0]:
            continue
        n += 1
        st, cnt = [(y0, x0)], 0
        lab[y0, x0] = n
        while st:
            y, x = st.pop()
            cnt += 1
            for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= yy < m.shape[0] and 0 <= xx < m.shape[1] and m[yy, xx] and not lab[yy, xx]:
                    lab[yy, xx] = n
                    st.append((yy, xx))
        if cnt > bestn:
            best, bestn = n, cnt
    return lab == best if best else m


def side_drape(c, oy, lean):
    """Hero round 2 (v1's side view): the cloak's front part over the shoulder and the upper chest,
    a gold edge along its lower side, and the gold cross clasp with the blue gem at the chest's front."""
    drape = c.m_poly([(25 + lean, 45 + oy), (36 + lean, 45 + oy), (42 + lean, 49 + oy), (44 + lean, 55 + oy),
                      (42 + lean, 60 + oy), (34 + lean, 62 + oy), (27 + lean, 61 + oy), (24 + lean, 54 + oy)])
    c.fill(drape, "cloak", 3)
    c.shade_part(drape, tones=(2, 3, 3, 4, 4), norm=True)
    for y, x in zip(*np.nonzero(drape)):  # the lower edge: 2 rows of gold trim
        if not drape[min(y + 2, c.h - 1), x] or not drape[min(y + 1, c.h - 1), x]:
            c.mat[y, x] = c.mid("gold")
            c.tone[y, x] = 3 if drape[min(y + 1, c.h - 1), x] else 1
    gx, gy = 44 + lean, 53 + oy
    cross = c.m_rect(gx - 4, gy - 1, gx + 4, gy) | c.m_rect(gx - 1, gy - 4, gx, gy + 4)
    c.fill(cross, "gold", 3)
    c.fill(c.m_rect(gx - 4, gy - 1, gx - 1, gy - 1) | c.m_rect(gx - 1, gy - 4, gx - 1, gy - 1), "gold", 4)
    gem = c.m_rect(gx - 2, gy - 2, gx + 1, gy + 1)
    c.fill(gem, "gem", 3)
    c.put(gx - 2, gy - 2, "gem", 5)
    c.put(gx - 1, gy - 2, "gem", 4)
    c.put(gx + 1, gy + 1, "gem", 2)
    c.put(gx, gy + 1, "gem", 2)


def side_frame(R, EYE, BLUSH, MOUTH, oy=0, lag=0, sway=0, legs=((0, 0, 0), (0, 0, 0)), arms=(0.0, 0.0),
               lean=0, bent=0.0, cloak_fly=0.0, breath=0, no_arms=False, finish=True, blink=False):
    """legs: (dx of the foot from the body line, lift of the heel, knee bend) for the far and near leg.
    arms: swing of the far and near arm. lean: the upper body forward (run)."""
    c = Canvas(W, H, R)
    hip = (32 + lean * 0.3, 78 + oy)
    # the far arm (behind the body), the far leg
    if not _off(no_arms, 0):
        side_arm(c, (30 + lean, 52 + oy - breath), arms[0], False, oy, bent)
    for k, (dx, lift, bend) in enumerate(legs):
        if k == 1:
            continue
        side_leg(c, hip, (27 + dx, 111 - lift), max(0, lift // 2), False, bend)
    # the cloak behind (from the shoulders to the hem, flaring back; cloak_fly lifts it in the run)
    hem = min(92 + oy, 106)  # crouching / kneeling: the cloak lies on the ground
    back = c.m_poly([(26 + lean, 46 + oy - breath), (36 + lean, 46 + oy - breath), (34 + lean * 0.5, 60 + oy),
                     (26, 86 + oy), (25 + sway, hem - cloak_fly * 3), (16 + sway - cloak_fly * 6, hem - cloak_fly * 8),
                     (9 + sway - cloak_fly * 6, hem - 2 - cloak_fly * 12), (10 - cloak_fly * 5, 72 + oy - cloak_fly * 6),
                     (14 + lean * 0.5, 54 + oy), (20 + lean, 47 + oy)])
    back = _largest(back)  # hero round 2: no stray piece of the cloak
    # (round 4: its front edge below the hip is 4 texels further back, behind the legs: run 4's green
    # piece between the knees came from here)
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
    # the near leg (crouching, oy >= 8: drawn after the torso, the knee bent forward in front of it)
    dx, lift, bend = legs[1]
    crouch = oy >= 8
    if not crouch:
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
    if crouch:
        side_leg(c, (hip[0] + 2, hip[1] - 4), (29 + dx, 111 - lift), max(0, lift // 2), True, bend + 6)
    # the near arm in front
    if not _off(no_arms, 1):
        side_arm(c, (32 + lean, 52 + oy - breath), arms[1], True, oy, bent)
    side_drape(c, oy - breath, lean)
    side_head(c, oy, lag, EYE, BLUSH, MOUTH, lean=min(lean, 4), blink=blink)  # round 3: the nose stays 3 inside
    if not finish:
        return c
    absorb_cloth_islands(c, limit=5)  # round 4: only 1-5 texel slivers are cleaned; a bigger piece stops the generator
    despeckle(c, loose=("hair", "cloak"))
    edge_band(c, "cloak", 1)
    c.outline()
    c.shadow_band()
    return c


# ---------------------------------------------------------------- back view (facing up)

def back_frame(R, oy=0, lag=0, sway=0, feet=(0, 0), arms=(0.0, 0.0), breath=0, bent=0.0, no_arms=False, finish=True):
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
        if lift > 1:  # hero round 2: the lifted boot shows its heel (lit leather block) over a dark sole
            c.fill(c.m_rect(x0 - 6, 109 - lift, x0 + 6, 111 - lift), "boot", 0)
            c.fill(c.m_rect(x0 - 4, 104 - lift, x0 + 4, 108 - lift), "leather", 3)
            c.fill(c.m_rect(x0 - 4, 104 - lift, x0 + 4, 104 - lift), "leather", 4)
            c.fill(c.m_rect(x0 - 4, 108 - lift, x0 + 4, 108 - lift), "leather", 1)
        tr = c.m_rect(x0 - 4, 86 + oy, x0 + 4, bt)
        c.fill(tr & (c.mat == 0), "trousers", 2)
    # the arms at the sides (gauntlet + hand), mostly outside the cloak
    for side, s in ((-1, arms[0]), (1, arms[1])):
        if _off(no_arms, side):
            continue
        sx = 31.5 + side * 22
        ex, ey = sx, 58 + oy
        wx, wy = sx - side * 1.0 * bent * 6, ey + 12 - 3 * abs(s) - 4 * bent
        wy += -2 * s
        wx += 3 * s * side  # hero round 2: the arm swings, the hand moving 3 texels sideways too (v1)
        g = capsule(c, (ex, ey), (wx, wy), 3.8)
        c.fill(g, "shirt")
        gauntlet(c, g, (ex, ey), (wx, wy), mid=-0.1)  # seen from behind the arm shows its lit side wider
        fist = c.m_ellipse(wx, wy + 4, 4, 4.2)
        c.fill(fist, "leather")
        c.shade_part(fist, tones=(1, 2, 3, 4), norm=True)
    # the cloak
    hem = min(92 + oy, 106)  # crouching / kneeling: the cloak lies on the ground
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
    # hero round 2 (v1's back): vertical locks falling from the crown to the nape, each with its own
    # pointed tip on the lower edge (a zigzag, not a smooth arc), no rays from the whorl
    L = lag
    mass = c.m_poly([(4, 26 + oy), (4, 18 + oy), (8, 13 + oy), (14, 11 + oy), (20, 9 + oy), (26, 7.5 + oy), (32, 4 + oy),
                     (38, 7.5 + oy), (44, 9 + oy), (50, 11 + oy), (56, 13 + oy), (60, 18 + oy), (60, 26 + oy), (58, 32 + oy), (55, 39 + oy + L), (51, 36 + oy), (47, 43 + oy + L), (43, 38 + oy), (38, 45 + oy + L),
                     (34, 39 + oy), (30, 46 + oy + L), (26, 39 + oy), (22, 45 + oy + L), (18, 37 + oy), (14, 42 + oy + L),
                     (10, 35 + oy), (8, 38 + oy + L), (5, 30 + oy)])
    c.fill(mass, "hair")
    c.shade_part(mass, tones=(1, 2, 2, 3, 3), norm=True)
    cr = (31, 10 + oy)
    # round 4: 5 thick locks of different widths and lengths, slanting, not even stripes (v1's back)
    locks = [((12, 14 + oy), (7, 37 + oy + L), 13, 2.0), ((22, 9 + oy), (17, 44 + oy + L), 14, 1.5),
             ((32, 8 + oy), (31, 46 + oy), 15, -0.5), ((42, 9 + oy), (45, 42 + oy + L), 14, -1.5),
             ((52, 14 + oy), (56, 36 + oy + L), 12, -2.0)]
    spikes = [((32, 13 + oy), (32, 3 + oy), 9, 0.3), ((26, 13 + oy), (21, 8 + oy), 8, 1.0),
              ((38, 13 + oy), (43, 8 + oy), 8, -1.0), ((13, 17 + oy), (5, 18 + oy), 8, 1.5),
              ((51, 17 + oy), (59, 20 + oy), 8, -1.5)]
    _shade_lock_set(c, spikes + locks, mass)
    keep_to_outline(c, "up", oy)  # round 4: v1's outline
    # hero round 3: above row 16 the hair keeps to the onion (the mass) and the spikes only — the
    # crown locks' wide roots no longer square the top off
    _spk = np.zeros(c.mat.shape, bool)
    for _r, _t, _w, _b in spikes:
        _spk |= lock(c, _r, _t, _w, _b)
    _yy = np.mgrid[0:c.h, 0:c.w][0]
    _out = (c.mat == c.mid("hair")) & ~(mass | _spk) & (_yy < 16 + oy)
    c.mat[_out] = 0
    c.put(cr[0], cr[1], "hair", 1)  # the whorl
    c.put(cr[0] + 1, cr[1] + 1, "hair", 1)
    if not finish:
        return c
    absorb_cloth_islands(c, limit=5)  # round 4: only 1-5 texel slivers are cleaned; a bigger piece stops the generator
    despeckle(c, loose=("hair", "cloak"))
    edge_band(c, "cloak", 1)
    c.outline()
    c.shadow_band()
    return c


# ---------------------------------------------------------------- the head's outline from v1 (round 4)

_V1_OUTLINE = {}


def _scale2x(m):
    """EPX / Scale2x on a boolean mask: 2x, with the diagonal steps smoothed (no 2x2 staircase)."""
    h, w = m.shape
    P = np.pad(m, 1)
    A, B, C, D = P[:-2, 1:-1], P[1:-1, 2:], P[1:-1, :-2], P[2:, 1:-1]  # up, right, left, down
    out = np.zeros((2 * h, 2 * w), bool)
    out[0::2, 0::2] = np.where((C == A) & (C != D) & (A != B), A, m)
    out[0::2, 1::2] = np.where((A == B) & (A != C) & (B != D), B, m)
    out[1::2, 0::2] = np.where((D == C) & (D != B) & (C != A), C, m)
    out[1::2, 1::2] = np.where((B == D) & (B != A) & (D != C), D, m)
    return out


def v1_head_outline(view):
    """Hero round 4 (inspection P1-1): the outer outline of v1's head (hair + face, its own outline
    left out) in v1's idle frame 0 of this view, at 2x with Scale2x — the stencil the v3 hair keeps to:
    v1's three top spikes, the pointed locks down to the chin (front), the lock down the nape (side)."""
    if view in _V1_OUTLINE:
        return _V1_OUTLINE[view]
    from PIL import Image
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(here, "..", "..", "src", "art-release", "hero", f"hero.idle.{view}.0.png")
    a = np.array(Image.open(p).convert("RGBA")).astype(int)
    key = a[..., 0] * 65536 + a[..., 1] * 256 + a[..., 2]
    def hexes(*cs):
        return [int(c[1:], 16) for c in cs]
    hair = np.isin(key, hexes("#4e2e1a", "#7a4a2a", "#a8703f", "#d09a62"))
    skin = np.isin(key, hexes("#c8906a", "#f2c49b", "#ffdcbc", "#fff0e0"))
    eye = np.isin(key, hexes("#24223a", "#1a3c86", "#2a78d0", "#f0fbff", "#d8cfc6", "#a8584e", "#f0a888"))
    rows = np.arange(a.shape[0])[:, None]
    m = (hair | ((skin | eye) & (rows <= 22))) & (a[..., 3] == 255) & (rows <= 24)
    # fill the holes (enclosed empty texels)
    outside = np.zeros(m.shape, bool)
    st = [(y, x) for y in range(m.shape[0]) for x in (0, m.shape[1] - 1)] + [(0, x) for x in range(m.shape[1])]
    while st:
        y, x = st.pop()
        if 0 <= y < m.shape[0] and 0 <= x < m.shape[1] and not m[y, x] and not outside[y, x]:
            outside[y, x] = True
            st += [(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)]
    m = ~outside
    m[25:, :] = False
    out = _scale2x(m)
    # the v3 outline is 1 texel where v1's (x 2) is 2: the spikes above row 10 are thinned by 1 texel a
    # side, so with its outline the v3 head covers v1's x 2 outline, not more
    top = out[:10].copy()
    thin = top & np.roll(top, 1, 1) & np.roll(top, -1, 1)
    out[:10] = thin
    _V1_OUTLINE[view] = out
    return out


def keep_to_outline(c, view, oy, dx=0, rows=50):
    """Hair outside v1's outline goes; empty texels inside it (above the face's bottom) become hair
    (tone 2, the mass); the outline moves with the body (oy) and the lean (dx)."""
    o = v1_head_outline(view)
    sh = np.zeros(c.mat.shape, bool)
    H_, W_ = o.shape
    for y in range(min(H_, c.h)):
        yy = y + oy
        if not (0 <= yy < c.h):
            continue
        xs = np.nonzero(o[y])[0] + dx
        xs = xs[(xs >= 0) & (xs < c.w)]
        sh[yy, xs] = True
    hair = c.mid("hair")
    yy = np.mgrid[0:c.h, 0:c.w][0]
    top = yy < rows + oy
    c.mat[(c.mat == hair) & ~sh & top] = 0
    fill = sh & (c.mat == 0) & top
    c.mat[fill] = hair
    c.tone[fill] = 2
    return sh
