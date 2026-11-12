"""澱の獣 (beast): a lean wolf of ash fur, murk crystals along the spine, tail and flank melting
into murk. Right-facing (the game mirrors it), 44x32, feet on row 30, outline on row 31.

Frames (docs/enemy/ENEMY_BOSS_DESIGN.md 2.1): idle 2, move 4, windup 2, attack 2, hurt 1, defeat 3.
Wind-up shows by SHAPE: crouched low, head down, jaw open, crystals 2 px taller. No red painted.
"""

import math

import numpy as np

from rig import Rig

W, H = 44, 32
GROUND = 30  # the row the paws stand on

EYE = ["32", "10"]  # hand-placed eye: 2x2 (tone 3/2 lit, 1/0 lower lid)


class Pose:
    def __init__(self, **k):
        self.x = 0  # whole body shift (+ forward)
        self.dy = 0  # body down (+)
        self.pitch = 0  # front of the body down (+) / up (-), in pixels at the chest
        self.head = (0, 0)  # head offset from the neck
        self.jaw = 0  # 0 closed .. 3 wide open
        self.ear = 0  # 0 up, 1 laid back
        self.tail = 0  # tail angle offset (+ up)
        self.spike = 0  # crystals taller
        self.stretch = 0  # body longer (leap)
        # paws: (x, y) of each foot; None = default standing
        self.ff = (29, GROUND)  # far front
        self.fh = (11, GROUND)  # far hind
        self.nf = (27, GROUND)  # near front
        self.nh = (13, GROUND)  # near hind
        self.puddle = 0  # defeat: 0 none .. 3 all murk
        self.lying = 0  # defeat: 0 standing .. 2 on its side
        self.__dict__.update(k)


def front_leg(r, sx, sy, px, py, **k):
    """Shoulder (sx,sy) to paw (px,py): elbow tucked back, a thin foreleg, a small paw."""
    ex, ey = sx - 1.5 + (px - sx) * 0.3, sy + (py - sy) * 0.45
    wx, wy = px - 0.5, py - 2
    m = r.mask_of(r.m_limb(sx, sy, ex, ey, 2.6, 1.6), r.m_ellipse(ex, ey, 1.7, 1.5), r.m_limb(ex, ey, wx, wy, 1.3, 1.0),
                  r.m_ellipse(wx - 0.3, wy, 1.3, 1.1), r.m_ellipse(px + 0.6, py - 0.6, 2.0, 1.2),
                  r.m_poly([(ex, ey - 1.4), (ex - 2.6, ey + 0.6), (ex + 0.4, ey + 1.2)]))  # the elbow corner
    return _leg(r, m, k)


def hind_leg(r, hx_, hy, px, py, **k):
    """Hip (hx,hy) to paw: a strong thigh forward, the hock bent back, a thin cannon."""
    kx, ky = hx_ + 2.5 + (px - hx_) * 0.4, hy + (py - hy) * 0.38
    hkx, hky = px - 2.2, py - 4.5
    m = r.mask_of(r.m_limb(hx_, hy, kx, ky, 3.4, 2.0), r.m_limb(kx, ky, hkx, hky, 1.8, 1.3),
                  r.m_limb(hkx, hky, px, py - 1, 1.2, 1.0), r.m_ellipse(hkx - 0.4, hky, 1.4, 1.3), r.m_ellipse(px + 0.6, py - 0.6, 2.0, 1.2),
                  r.m_poly([(hkx - 0.2, hky - 1.6), (hkx - 2.8, hky + 0.2), (hkx + 0.2, hky + 1.2)]))  # the heel (hock) corner
    return _leg(r, m, k)


def _leg(r, m, k):
    """Draw a leg; a NEAR leg (not darkened) also gets a 1-px tone-3 edge on its top-left, so it
    does not sink into dark ground (swamp, cave)."""
    r.add(m, "ashfur", **k)
    if not k.get("dark"):
        up = np.zeros_like(m)
        up[1:, :] = ~m[:-1, :]
        left = np.zeros_like(m)
        left[:, 1:] = ~m[:, :-1]
        right = np.zeros_like(m)
        right[:, :-1] = ~m[:, 1:]
        edge = m & (left | (up & ~right))
        r.add(edge, "ashfur", tone=3, cast=False)
    return m


# round 4: the coat's own tones for wedges and the scar
WEDGE_LEG = {"3": ("ashfur", 3), "1": ("ashfur", 1)}

def draw(p):
    r = Rig(W, H)
    if p.puddle >= 3:
        return puddle_only(r, p)
    X, dy = p.x - 2, p.dy
    by = 17 + dy  # body centre line
    r.anchor = (12 + X, by)  # v3 round 2: the surface detail moves with the body
    hip = (12 + X - p.stretch * 0.5, by + 2 - p.pitch * 0.2)
    sh = (28 + X + p.stretch * 0.5, by + 2 + p.pitch)
    if p.lying:
        return lying(r, p)
    # far legs (one tone darker), behind everything
    hind_leg(r, hip[0] - 1, hip[1], p.fh[0] - 2, p.fh[1], dark=1)
    front_leg(r, sh[0] + 1, sh[1], p.ff[0] - 2, p.ff[1], dark=1)
    # tail of murk: a tapered curl back and up, dripping
    a = math.radians(128 - p.tail * 10)
    t0 = (hip[0] - 3, hip[1] - 4)
    t1 = (t0[0] + 5 * math.cos(a), t0[1] - 5 * math.sin(a))
    t2 = (t1[0] + 4 * math.cos(a - 0.9), t1[1] - 4 * math.sin(a - 0.9))
    r.chain([t0, t1, t2], [3.0, 2.2, 1.1], "murk", soft=1)
    r.px([(round(t0[0]) - 1, round(t0[1]) + 3)], "murk", 1)  # a drip
    # body (beast finish): haunch + barrel + deep chest + neck, with fur tufts cut into the outline.
    # Shaded BY MASS, not by a light that sweeps the whole tube: each round mass (haunch, chest,
    # neck) has its own lit crescent on its upper-left and its own shadow crescent on its
    # lower-right; the barrel between them stays the core tone. No light-back / dark-belly bands.
    neck = (31.5 + X + p.stretch * 0.7 + p.head[0] * 0.5, by - 2 + p.pitch * 1.2 + p.head[1] * 0.5)
    H_ = (hip[0] + 0.5, hip[1] - 2.5, 6.2, 5.6)
    C_ = (sh[0], sh[1] - 2.5, 5.2, 6.0)
    haunch, chest = r.m_ellipse(*H_), r.m_ellipse(*C_)
    barrel = r.m_limb(hip[0] + 2, hip[1] - 3.5, sh[0] - 1, sh[1] - 3.5, 4.3, 5.6)
    neckm = r.m_limb(sh[0] + 1, sh[1] - 4, neck[0], neck[1], 4.2, 3.4)
    body = r.mask_of(haunch, barrel, chest, neckm)
    belly_cut = r.m_ellipse((hip[0] + sh[0]) / 2, hip[1] + 4.5, 6.5, 3.2)
    body &= ~belly_cut
    # fur tufts on the silhouette: hanging points under the belly and chest, a ruff jutting at the
    # throat, a tuft at the back of the haunch (each a small hand-set triangle)
    bx0, bx1 = (hip[0] + sh[0]) / 2 - 5, (hip[0] + sh[0]) / 2 + 5
    belly_y = hip[1] + 1.4 + (p.pitch * 0.4)
    tufts = []
    for i, tx in enumerate((bx0, bx0 + 3.5, bx0 + 7, bx1)):
        ty = belly_y + (sh[1] - hip[1]) * ((tx - hip[0]) / max(sh[0] - hip[0], 1)) * 0.4
        tufts.append([(tx - 1.8, ty - 1.5), (tx + 1.6, ty - 1.5), (tx - 0.8, ty + 2.6 + (i % 2))])
    cx_, cy_ = C_[0], C_[1]
    tufts.append([(cx_ - 2.2, cy_ + 4.5), (cx_ + 1.8, cy_ + 4.5), (cx_ - 1.4, cy_ + 8.4)])  # chest
    tufts.append([(cx_ + 3, cy_ + 2.5), (cx_ + 5.5, cy_ - 0.5), (cx_ + 4.4, cy_ + 5.2)])  # throat
    hx0, hy0 = H_[0], H_[1]
    tufts.append([(hx0 - 4, hy0 - 3.5), (hx0 - 7.4, hy0 - 2.4), (hx0 - 5, hy0 + 0.5)])  # rump
    tufts.append([(hx0 - 2, hy0 + 3), (hx0 - 5.6, hy0 + 4.6), (hx0 - 2.4, hy0 + 5.6)])  # haunch
    for t_ in tufts:
        body |= r.m_poly(t_)

    def crescent(e, d):
        cx0, cy0, rx0, ry0 = e
        return r.m_ellipse(cx0, cy0, rx0, ry0) & ~r.m_ellipse(cx0 + d, cy0 + d, rx0, ry0)

    lit = (crescent(H_, 1.3) | crescent(C_, 1.3)) & body
    nl = neckm & ~r.m_limb(sh[0] + 1.6, sh[1] - 3.0, neck[0] + 1.0, neck[1] + 1.0, 4.2, 3.4)
    lit |= nl & body
    dark = (crescent(H_, -1.3) | crescent(C_, -1.3)) & body
    # the underside: the lowest row of the belly and of each tuft
    below = r.mask_of(body)
    below[:-1, :] = body[:-1, :] & ~body[1:, :]
    dark |= below
    dark &= ~lit
    # v2: a half-step ring inside each crescent (2.5 under the light, 1.5 over the shadow), so the
    # masses turn in 5 steps instead of 3
    lit2 = (crescent(H_, 2.6) | crescent(C_, 2.6)) & body & ~lit & ~dark
    dark2 = (crescent(H_, -2.6) | crescent(C_, -2.6)) & body & ~lit & ~dark & ~lit2
    r.add(body & ~lit & ~dark & ~lit2 & ~dark2, "ashfur", tone=2)
    r.add(dark2, "ashfur", tone=1.5)
    r.add(lit2, "ashfur", tone=2.5)
    r.add(dark, "ashfur", tone=1)
    r.add(lit, "ashfur", tone=3)
    # round 4: two fur wedges on the shoulder, two on the haunch (lit over a dark tip, lying back),
    # and one 2-px scar across the haunch -- all from the masses' centres, so they ride the body
    # round 6: the shoulder and the haunch are cut into planes -- each muscle is its own rounded
    # mass (a lit upper-left plane, a core plane) set off from the body by a 2-px shadow arc
    # behind and under it. Whole pixels from the masses' centres, so they ride the body.
    for (mx, my, mrx, mry) in ((round(C_[0]) - 0.5, round(C_[1]) + 1.0, 4.4, 5.4), (round(H_[0]) - 0.5, round(H_[1]) + 1.5, 5.4, 4.8)):
        muscle = r.m_ellipse(mx, my, mrx, mry) & body
        arc = r.m_ellipse(mx + 1.6, my + 1.2, mrx + 1.2, mry + 1.2) & ~r.m_ellipse(mx, my, mrx, mry) & body
        r.add(arc, "ashfur", tone=1, cast=False)
        r.add(muscle, "ashfur", tone=2, cast=False)
        r.add(muscle & ~r.m_ellipse(mx + 3.4, my + 3.4, mrx, mry), "ashfur", tone=2.5, cast=False)
        r.add(muscle & ~r.m_ellipse(mx + 1.6, my + 1.6, mrx, mry), "ashfur", tone=3, cast=False)
    # ...and the ribs show on the barrel between them: three short slanted shadows, 2 px wide
    for i in range(3):
        rx0 = round(H_[0] + 7 + i * 3.4 + p.stretch * 0.3 * i)
        ry0 = round((hip[1] + sh[1]) / 2 - 3)
        r.add(r.m_px([(rx0, ry0), (rx0, ry0 + 1), (rx0 - 1, ry0 + 1), (rx0 - 1, ry0 + 2), (rx0 - 1, ry0 + 3), (rx0 - 2, ry0 + 3)]) & body, "ashfur", tone=1, cast=False)
    # mane ruff on the neck and shoulders (paler, tufted)
    rx, ry = sh[0] + 2, sh[1] - 6
    ruff = r.m_poly([(rx - 7, ry), (rx - 5, ry - 2), (rx - 3, ry - 4), (rx - 1, ry - 3), (rx + 2, ry - 5), (rx + 5, ry - 1), (rx + 3, ry + 1),
                     (rx + 2, ry + 3), (rx, ry + 1), (rx - 2, ry + 3), (rx - 4, ry + 1)])
    r.add(ruff, "ashfur", tone=2)
    # fur locks, hand-drawn (beast finish): three bold locks flowing back along the back, each a
    # 2-px lit band over a dark 1-px underside, spaced by the core tone -- a clear light / dark
    # rhythm at 1x; two locks on the ruff
    leg_ = {"3": ("ashfur", 3), "1": ("ashfur", 1), "2": ("ashfur", 2)}
    LOCK = [".33333", "311111"]
    for i, (ox, oy) in enumerate(((0, -1), (8, 2), (15, -2))):  # staggered: no continuous stripe
        lx = round(hip[0] + ox - 2 + p.stretch * (ox / 18))
        ly = round(by - 3 + oy + p.pitch * (ox / 16))
        r.stamp(lx, ly, LOCK, leg_)
    r.stamp(round(rx) - 6, round(ry) + 1, [".3333", "31111"], leg_)
    # murk melting on the flank: a patch on the haunch with drips
    fx, fy = hip[0] + 3, hip[1] - 1
    r.ellipse(fx, fy, 5.0, 2.6, "murk", soft=1)
    r.px([(round(fx) - 3, round(fy) + 3), (round(fx) + 1, round(fy) + 3), (round(fx) + 1, round(fy) + 4)], "murk", 1)
    # near legs
    hind_leg(r, hip[0] + 1, hip[1], p.nh[0] - 2, p.nh[1])
    front_leg(r, sh[0] - 1, sh[1], p.nf[0] - 2, p.nf[1])
    # head (profile): crown, stop, long muzzle; the ear stands up behind the crown; jaw drops open
    hx_, hy = neck[0] + 3.5 + p.head[0] * 0.5, neck[1] - 2 + p.head[1] * 0.5
    jaw = p.jaw
    head = r.m_poly([(hx_ - 5, hy - 0.5), (hx_ - 3.5, hy - 3.2), (hx_ - 0.5, hy - 4.2), (hx_ + 2.5, hy - 3.2),
                     (hx_ + 8.6, hy - 1.4), (hx_ + 9.6, hy - 0.2), (hx_ + 9.2, hy + 1.2), (hx_ + 2.5, hy + 2.4),
                     (hx_ - 1.5, hy + 3.8), (hx_ - 5, hy + 3.2)])
    if jaw:
        lower = r.m_poly([(hx_ - 1.5, hy + 1.2), (hx_ + 8, hy + 1.6 + jaw * 1.5), (hx_ + 7.4, hy + 2.8 + jaw * 1.5), (hx_ - 2, hy + 3.8)])
        r.add(lower, "ashfur", dark=1, soft=1)
        mouth = r.m_poly([(hx_ + 0.5, hy + 1.4), (hx_ + 9, hy + 1.2), (hx_ + 7.6, hy + 1.6 + jaw * 1.5)])
        r.add(mouth, "murk", tone=0)
        head &= ~r.m_poly([(hx_ + 0.5, hy + 1.4), (hx_ + 10, hy + 1.2), (hx_ + 10, hy + 4), (hx_ + 0.5, hy + 4)])
    r.add(head, "ashfur", soft=2)
    # brow ridge and stop (breaks the box of the head): a dark crease from the eye down the muzzle
    r.shade(r.m_line(hx_ + 0.5, hy - 2.6, hx_ + 3, hy - 2.2), lambda t: max(1, t - 1))
    r.shade(r.m_line(hx_ + 4, hy + 0.6, hx_ + 8, hy + 0.4), lambda t: max(1, t - 1))
    # cheek ruff, paler, pointing back
    r.add(r.m_poly([(hx_ - 3.5, hy + 0.5), (hx_ - 6.8, hy + 3.4), (hx_ - 0.5, hy + 3.4)]), "ashfur", lit=1, soft=1)
    # the ear: a tall triangle in front of the crown, dark inside
    et = (hx_ - 2.4 - p.ear * 4.0, hy - 9.2 + p.ear * 5.0)
    r.add(r.m_poly([(hx_ - 3.8, hy - 2.0), et, (hx_ + 0.8, hy - 3.4)]), "ashfur", soft=1)
    r.add(r.m_poly([(hx_ - 2.6, hy - 2.6), (et[0] + 0.7, et[1] + 2.6), (hx_ - 0.4, hy - 3.2)]), "ashfur", tone=1)
    # v3 round 2: the head's volume at texel size -- a lit forehead and muzzle top (a 2.5 band), the
    # cheek under the eye lit, the underside of the muzzle and the throat in shade
    r.shade(r.m_ellipse(hx_ + 0.5, hy - 2.2, 3.2, 1.3) | r.m_ellipse(hx_ + 5.5, hy - 1.6, 3.6, 0.9), lambda t: 2.5 if 1 <= t <= 2.5 else t)
    r.shade(r.m_ellipse(hx_ + 0.5, hy + 1.4, 2.6, 1.1), lambda t: 2.5 if 1 <= t <= 2 else t)
    r.shade(r.m_ellipse(hx_ + 5, hy + 1.6, 4.5, 0.8) | r.m_ellipse(hx_ - 2.5, hy + 3.0, 2.4, 1.0), lambda t: max(1, t - 1))
    # the nose: a dark wet nose with a lit top and a nostril (texels)
    r.tstamp(hx_ + 8.0, hy - 1.5, [".hh..", "00000", "00n00", ".000."], {"h": ("ashfur", 3), "0": ("ashfur", 0), "n": ("murk", 0)})
    # fangs (bone), hand-set: a long upper fang near the nose and a short one behind; when the jaw
    # opens a row of lower teeth shows against the dark mouth (the bite reads at 1x)
    # v3 round 2: the lip line (2 texels, dark) from the nose back to the corner of the mouth
    r.add(r.m_limb(hx_ + 1.0, hy + 1.3, hx_ + 8.6, hy + 1.0, 0.45, 0.4), "ashfur", tone=0, cast=False)
    # fangs drawn at texel size: a long upper fang (2 wide, tapering, lit left, shaded right), a short
    # one behind; an open jaw shows the lower teeth against the dark mouth and a dark gum line
    fy_ = hy + 1.6
    FANG = {"a": ("bone", 4), "b": ("bone", 2.5), "c": ("bone", 1)}
    if jaw:
        r.tstamp(hx_ + 6.5, fy_, ["ab", "ab", "ab", "ac", "a."] if jaw >= 2 else ["ab", "ab", "ac", "a."], FANG)
        r.tstamp(hx_ + 3.5, fy_, ["ab", "ac", "a."], FANG)
        jy = hy + 0.6 + jaw * 1.5
        for tx in (5.5, 3.5, 1.8):
            r.tstamp(hx_ + tx, jy, [".a", "ab", "ab"], FANG)
    else:
        r.tstamp(hx_ + 6.5, fy_, ["ab", "ab", "a."], FANG)
        r.tstamp(hx_ + 3.2, fy_, ["ab", "a."], FANG)
    # the eye (texels, 8 x 6): a heavy brow slanting down to the snout, a dark rim, a yellow iris in 3
    # tones (light, core, deep), a slit pupil and a 2 x 1 glint
    r.tstamp(hx_ - 0.6, hy - 3.6, ["0000000...", ".00000000.", "..0ggbbbp0", "..0gbbbcp0", "...0bcccd0", "....0ccd0.", ".....000.."],
             {"0": ("ashfur", 0), "g": ("eye", 4), "b": ("eye", 3), "c": ("eye", 2), "d": ("eye", 1), "p": ("murk", 0)})
    r.add(r.m_limb(hx_ + 4.2, hy - 2.4, hx_ + 8, hy - 1.5, 0.5, 0.45), "ashfur", tone=3, cast=False)  # lit bridge
    # spine crystals (glow, the enemy.magic magenta): 5 shards, tallest over the shoulders
    for i, (ox, h) in enumerate(((-2, 3), (3, 5), (8, 6), (12, 5), (16, 3))):
        cx = hip[0] + 1 + ox + p.stretch * (ox / 18)
        base = by - 5 + (p.pitch * (ox / 16)) - (1 if 1 <= i <= 3 else 0)
        h = h + p.spike
        lean = 1.2  # shards lean back
        r.poly([(cx - 1.8, base + 1.5), (cx - lean, base - h), (cx + 1.6, base + 1.5)], "glow", soft=1)
    return r


def lying(r, p):
    """Defeat frame: fallen on its side, legs out toward the camera, murk spreading under it."""
    gy = GROUND
    # murk pool spreading under the body
    r.ellipse(21, gy - 1, 15 + p.puddle * 2, 1.9, "murk", soft=1)
    # legs sticking out forward (toward the viewer: down-right)
    for i, (x0, x1) in enumerate(((12, 16), (15, 19), (27, 30), (30, 33))):
        r.limb(x0, gy - 5, x1, gy - 1.5, 1.8, 1.3, "ashfur", dark=1 if i % 2 == 0 else 0)
    B_, R_ = (20, gy - 6, 12, 4.6), (10, gy - 6.5, 5, 4.4)
    body = r.mask_of(r.m_ellipse(*B_), r.m_ellipse(*R_))
    # fur tufts on the outline: the back (top edge) and the rump
    for tx in (14, 20, 26):
        body |= r.m_poly([(tx - 1.8, gy - 10.2), (tx + 1.6, gy - 10.2), (tx - 1.2, gy - 12.6)])
    body |= r.m_poly([(6, gy - 9), (3.4, gy - 10.4), (5, gy - 6.5)])

    def crescent(e, d):
        return r.m_ellipse(*e) & ~r.m_ellipse(e[0] + d, e[1] + d, e[2], e[3])

    lit = (crescent(B_, 1.3) | crescent(R_, 1.3)) & body
    dark = (crescent(B_, -1.3) | crescent(R_, -1.3)) & body & ~lit
    r.add(body & ~lit & ~dark, "ashfur", tone=2)
    r.add(dark, "ashfur", tone=1)
    r.add(lit, "ashfur", tone=3)
    # the same wedge locks as standing
    for lx in (12, 19):
        r.stamp(lx, gy - 8, [".33333", "311111"], {"3": ("ashfur", 3), "1": ("ashfur", 1)})
    # head lying flat, snout forward, jaw slack
    hx_, hy = 33, gy - 5
    r.add(r.mask_of(r.m_ellipse(hx_, hy, 4.2, 3.4), r.m_poly([(hx_ + 1, hy - 2), (hx_ + 8, hy + 0.5), (hx_ + 7.5, hy + 2), (hx_ + 1, hy + 2.2)])), "ashfur")
    r.poly([(hx_ - 4, hy - 1), (hx_ - 9, hy - 2), (hx_ - 2, hy - 3)], "ashfur", soft=1)  # ear laid flat
    r.px([(hx_ + 8, hy + 1)], "ashfur", 0)
    r.px([(hx_ + 1, hy - 1), (hx_ + 2, hy - 1)], "ashfur", 0)  # eye shut
    r.px([(hx_ + 5, hy + 2)], "bone", 3)
    # crystals cracked and fallen: low shards along the back
    for cx, h in ((12, 2), (18, 3), (24, 2)):
        r.poly([(cx - 1.5, gy - 10), (cx - 0.5, gy - 10 - h), (cx + 1.5, gy - 10)], "glow", soft=1)
    # tail of murk lying on the ground
    r.chain([(7, gy - 5), (4.5, gy - 2.5), (3.5, gy - 1)], [2.4, 1.8, 1.1], "murk", soft=1)
    if p.puddle >= 2:
        # the fur dissolving: murk eats the back half
        r.ellipse(12, gy - 6, 7, 4.6, "murk", soft=1)
        r.px([(9, gy - 9), (14, gy - 10), (11, gy - 3)], "murk", 3)
    return r


def puddle_only(r, p):
    gy = GROUND
    r.ellipse(22, gy - 1.2, 17, 1.9, "murk", soft=1)
    r.ellipse(18, gy - 2.5, 8, 2.2, "murk", soft=1)
    r.ellipse(29, gy - 2, 5, 1.6, "murk", soft=1)
    # broken crystal shards and the last tuft of fur
    for cx, h in ((14, 2), (22, 3), (27, 2)):
        r.poly([(cx - 1.5, gy - 2), (cx, gy - 2 - h), (cx + 1.5, gy - 2)], "glow", soft=1)
    r.ellipse(34, gy - 1.5, 2.5, 1.5, "ashfur", soft=1)
    r.px([(9, gy - 4), (31, gy - 5)], "murk", 2)  # drops thrown up
    return r


# ------------------------------------------------------------------ the frames

def frames_v1():  # the v1 key poses (kept for reference; v2 frames() is at the end)
    G = GROUND
    f = {}
    # idle: breathing (body bobs 1 px), the tail sways, the head lifts a little
    f["idle.0"] = Pose()
    f["idle.1"] = Pose(dy=1, tail=1, head=(0, 1), ff=(29, G), nf=(27, G))
    # move (4 poses): contact, gathered (legs under the body, back up), the other contact, extended
    # (forelegs reaching, hind legs pushed back): move.1 and move.3 are different poses, not a mirror
    f["move.0"] = Pose(nf=(31, G), fh=(15, G), ff=(25, G - 2), nh=(8, G - 1), dy=0, tail=1, head=(1, 0))
    f["move.1"] = Pose(nf=(26, G - 2), ff=(24, G - 1), nh=(17, G - 1), fh=(15, G), dy=-1, pitch=1, tail=0, head=(0, 1))  # gathered
    f["move.2"] = Pose(ff=(31, G), nh=(15, G), nf=(25, G - 2), fh=(8, G - 1), dy=0, tail=-1, head=(1, 0))
    f["move.3"] = Pose(nf=(34, G - 3), ff=(32, G - 1), nh=(7, G - 2), fh=(5, G), dy=-1, pitch=-1, tail=2, head=(1, 0))  # extended
    # windup: crouch low, head down, jaw opens, crystals bristle (2 frames, deeper)
    f["windup.0"] = Pose(dy=2, pitch=2, head=(-1, 3), jaw=1, ear=1, spike=1, tail=1, nf=(30, G), ff=(32, G), nh=(14, G), fh=(12, G))
    f["windup.1"] = Pose(dy=3, pitch=3, x=-1, head=(-2, 4), jaw=2, ear=1, spike=2, tail=2, nf=(30, G), ff=(32, G), nh=(12, G), fh=(10, G))
    # attack: the leap (stretched in the air, forelegs reaching) and the bite on landing
    f["attack.0"] = Pose(dy=-3, pitch=-1, stretch=2, x=0, head=(0, -1), jaw=3, ear=1, spike=1, tail=-1,
                         nf=(38, G - 6), ff=(39, G - 8), nh=(8, G - 5), fh=(7, G - 7))
    f["attack.1"] = Pose(dy=1, pitch=3, stretch=2, x=0, head=(1, 3), jaw=1, ear=1, spike=1, tail=1,
                         nf=(37, G), ff=(39, G - 1), nh=(10, G - 2), fh=(8, G - 3))
    # hurt: recoils back, head thrown up, jaw open, ears flat
    f["hurt.0"] = Pose(x=0, dy=0, pitch=-2, head=(-2, -3), jaw=2, ear=1, tail=-2, nf=(26, G), ff=(29, G - 1), nh=(10, G), fh=(13, G))
    # defeat: legs buckle -> on its side in murk -> only murk and shards left
    f["defeat.0"] = Pose(dy=5, pitch=3, head=(-1, 4), jaw=1, ear=1, tail=-2, spike=-1, nf=(29, G), ff=(31, G), nh=(13, G), fh=(11, G))
    f["defeat.1"] = Pose(lying=1, puddle=1)
    f["defeat.2"] = Pose(puddle=3)
    return {k: draw(v) for k, v in f.items()}


ACTIONS = (("idle", 2), ("move", 4), ("windup", 2), ("attack", 2), ("hurt", 1), ("defeat", 3))
SIZE = (W, H)


# ------------------------------------------------------------------ v2 frames (4-8 per action)

def frames():
    """v2: idle 4, move 8, windup 4, attack 5, hurt 3, defeat 6 (key poses eased in between)."""
    from anim import loop, once, name
    G = GROUND
    out = {}
    stand = dict(nf=(27.0, G), ff=(29.0, G), nh=(13.0, G), fh=(11.0, G))
    # idle: breathing -- the chest rises and falls, the head bobs after it, the tail sways
    name(out, "idle", loop(Pose, 4, [
        (0.0, dict(stand)), (0.25, dict(stand, dy=1)), (0.5, dict(stand, dy=1, tail=2.5)), (0.75, dict(stand, tail=2.5, jaw=1)),
    ]), draw)
    # move: a 4-beat lope (contact, gathered, contact, extended) with the passing poses between;
    # the body rises on the gathered beat and stretches on the extended one
    c0 = dict(nf=(31.0, G), fh=(15.0, G), ff=(25.0, G - 2.0), nh=(8.0, G - 1.0), dy=0.0, tail=1.0, head=(1.0, 0.0), pitch=0.0, stretch=0.0)
    g1 = dict(nf=(26.0, G - 2.0), ff=(24.0, G - 1.0), nh=(17.0, G - 1.0), fh=(15.0, G), dy=-1.0, pitch=1.0, tail=0.0, head=(0.0, 1.0), stretch=-0.5)
    c2 = dict(ff=(31.0, G), nh=(15.0, G), nf=(25.0, G - 2.0), fh=(8.0, G - 1.0), dy=0.0, tail=-1.0, head=(1.0, 0.0), pitch=0.0, stretch=0.0)
    e3 = dict(nf=(34.0, G - 3.0), ff=(32.0, G - 1.0), nh=(7.0, G - 2.0), fh=(5.0, G), dy=-1.0, pitch=-1.0, tail=2.0, head=(1.0, 0.0), stretch=1.0)
    name(out, "move", loop(Pose, 8, [(0.0, c0), (0.25, g1), (0.5, c2), (0.75, e3)]), draw)
    # windup: settles back on the haunches (anticipation), then sinks low, head down, jaw open,
    # crystals bristling; the last frame is the held, coiled pose
    w1 = dict(dy=1.0, pitch=-1.0, x=-1, head=(-1.0, 1.0), jaw=0, ear=1, spike=0, tail=2.0, nf=(28.0, G), ff=(30.0, G), nh=(12.0, G), fh=(10.0, G))
    w2 = dict(dy=2.0, pitch=2.0, head=(-1.0, 3.0), jaw=1, ear=1, spike=1, tail=1.0, nf=(30.0, G), ff=(32.0, G), nh=(14.0, G), fh=(12.0, G))
    w3 = dict(dy=3.0, pitch=3.0, x=-1, head=(-2.0, 4.0), jaw=2, ear=1, spike=2, tail=2.0, nf=(30.0, G), ff=(32.0, G), nh=(12.0, G), fh=(10.0, G))
    name(out, "windup", once(Pose, 4, [(0.0, w1), (0.5, w2), (1.0, w3)]), draw)
    # attack: the spring (hind legs drive), the leap (stretched, jaws wide), the bite on landing
    # (pitched down, squashed), the follow-through and the recovery
    a0 = dict(w3, dy=1.0, pitch=0.0, stretch=1.0, jaw=3, nh=(9.0, G), fh=(7.0, G))
    a1 = dict(dy=-3.0, pitch=-1.0, stretch=2.0, x=0, head=(0.0, -1.0), jaw=3, ear=1, spike=1, tail=-1.0,
              nf=(38.0, G - 6.0), ff=(39.0, G - 8.0), nh=(8.0, G - 5.0), fh=(7.0, G - 7.0))
    a2 = dict(dy=1.0, pitch=3.0, stretch=2.0, x=0, head=(1.0, 3.0), jaw=1, ear=1, spike=1, tail=1.0,
              nf=(37.0, G), ff=(39.0, G - 1.0), nh=(10.0, G - 2.0), fh=(8.0, G - 3.0))
    a3 = dict(dy=2.0, pitch=2.0, stretch=1.0, head=(2.0, 3.0), jaw=2, ear=1, spike=1, tail=1.5,
              nf=(35.0, G), ff=(37.0, G), nh=(13.0, G), fh=(11.0, G))
    a4 = dict(dy=1.0, pitch=1.0, stretch=0.5, head=(1.0, 1.0), jaw=0, ear=0, spike=0, tail=1.0,
              nf=(31.0, G), ff=(33.0, G), nh=(14.0, G), fh=(12.0, G))
    name(out, "attack", once(Pose, 5, [(0.0, a0), (0.25, a1, "out"), (0.5, a2, "in"), (0.75, a3), (1.0, a4)]), draw)
    # hurt: the snap back (head up, ears flat), the recoil, the recovery
    h0 = dict(x=-1, dy=0.0, pitch=-2.0, head=(-2.0, -3.0), jaw=2, ear=1, tail=-2.0, nf=(26.0, G), ff=(29.0, G - 1.0), nh=(10.0, G), fh=(13.0, G))
    h1 = dict(x=-2, dy=1.0, pitch=-1.0, head=(-2.0, -1.0), jaw=1, ear=1, tail=-1.0, nf=(25.0, G), ff=(28.0, G), nh=(10.0, G), fh=(12.0, G))
    h2 = dict(stand, x=-1, dy=0.5, head=(-1.0, 0.0), ear=0)
    name(out, "hurt", once(Pose, 3, [(0.0, h0), (0.5, h1), (1.0, h2)]), draw)
    # defeat: the hit, the legs buckle, sinking, on its side, the murk eats it, only murk left
    d = once(Pose, 3, [
        (0.0, dict(h0, dy=1.0, jaw=3, x=-2, tail=-3.0)),
        (0.5, dict(dy=3.0, pitch=2.0, head=(-1.0, 2.0), jaw=1, ear=1, tail=-2.0, spike=0, nf=(28.0, G), ff=(30.0, G), nh=(13.0, G), fh=(11.0, G))),
        (1.0, dict(dy=5.0, pitch=3.0, head=(-1.0, 4.0), jaw=1, ear=1, tail=-2.0, spike=-1, nf=(29.0, G), ff=(31.0, G), nh=(13.0, G), fh=(11.0, G))),
    ])
    # round 2: the collapse melts into the murk over two frames (no pop to the lying pose)
    from anim import dissolve_from
    name(out, "defeat", dissolve_from(draw, d, Pose(puddle=3), pools=(8, 12)), None)
    return out


ACTIONS = (("idle", 4), ("move", 8), ("windup", 4), ("attack", 5), ("hurt", 3), ("defeat", 6))
SMOOTH = {"tail"}  # shape fields that stay smooth (the rest snap to whole pixels)
