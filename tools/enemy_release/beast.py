"""澱の獣 (beast): a lean wolf of ash fur, murk crystals along the spine, tail and flank melting
into murk. Right-facing (the game mirrors it), 44x32, feet on row 30, outline on row 31.

Frames (docs/enemy/ENEMY_BOSS_DESIGN.md 2.1): idle 2, move 4, windup 2, attack 2, hurt 1, defeat 3.
Wind-up shows by SHAPE: crouched low, head down, jaw open, crystals 2 px taller. No red painted.
"""

import math

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
                  r.m_ellipse(wx - 0.3, wy, 1.3, 1.1), r.m_ellipse(px + 0.6, py - 0.6, 2.0, 1.2))
    return r.add(m, "ashfur", tex=("fur", 95, 4), **k)


def hind_leg(r, hx_, hy, px, py, **k):
    """Hip (hx,hy) to paw: a strong thigh forward, the hock bent back, a thin cannon."""
    kx, ky = hx_ + 2.5 + (px - hx_) * 0.4, hy + (py - hy) * 0.38
    hkx, hky = px - 2.2, py - 4.5
    m = r.mask_of(r.m_limb(hx_, hy, kx, ky, 3.4, 2.0), r.m_limb(kx, ky, hkx, hky, 1.8, 1.3),
                  r.m_limb(hkx, hky, px, py - 1, 1.2, 1.0), r.m_ellipse(hkx - 0.4, hky, 1.4, 1.3), r.m_ellipse(px + 0.6, py - 0.6, 2.0, 1.2))
    return r.add(m, "ashfur", tex=("fur", 95, 5), **k)


def draw(p):
    r = Rig(W, H)
    if p.puddle >= 3:
        return puddle_only(r, p)
    X, dy = p.x - 2, p.dy
    by = 17 + dy  # body centre line
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
    # body: haunch + barrel + deep chest + neck, one volume
    neck = (31.5 + X + p.stretch * 0.7 + p.head[0] * 0.5, by - 2 + p.pitch * 1.2 + p.head[1] * 0.5)
    body = r.mask_of(
        r.m_ellipse(hip[0] + 0.5, hip[1] - 2.5, 6.2, 5.6),
        r.m_limb(hip[0] + 2, hip[1] - 3.5, sh[0] - 1, sh[1] - 3.5, 4.3, 5.6),
        r.m_ellipse(sh[0], sh[1] - 2.5, 5.2, 6.0),
        r.m_limb(sh[0] + 1, sh[1] - 4, neck[0], neck[1], 4.2, 3.4),
    )
    # belly tucked up between chest and haunch
    belly_cut = r.m_ellipse((hip[0] + sh[0]) / 2, hip[1] + 4.5, 6.5, 3.2)
    body &= ~belly_cut
    r.add(body, "ashfur", tex=("fur", 172, 1))
    # mane ruff on the neck and shoulders (paler, tufted)
    rx, ry = sh[0] + 2, sh[1] - 6
    r.add(r.m_poly([(rx - 7, ry), (rx - 5, ry - 2), (rx - 3, ry - 4), (rx - 1, ry - 3), (rx + 2, ry - 5), (rx + 5, ry - 1), (rx + 3, ry + 1),
                    (rx + 2, ry + 3), (rx, ry + 1), (rx - 2, ry + 3), (rx - 4, ry + 1)]), "ashfur", lit=1, soft=1)
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
    r.add(head, "ashfur", soft=2, tex=("fur", 180, 6))
    # brow ridge and stop (breaks the box of the head): a dark crease from the eye down the muzzle
    r.shade(r.m_line(hx_ + 0.5, hy - 2.6, hx_ + 3, hy - 2.2), lambda t: max(1, t - 1))
    r.shade(r.m_line(hx_ + 4, hy + 0.6, hx_ + 8, hy + 0.4), lambda t: max(1, t - 1))
    # cheek ruff, paler, pointing back
    r.add(r.m_poly([(hx_ - 3.5, hy + 0.5), (hx_ - 6.8, hy + 3.4), (hx_ - 0.5, hy + 3.4)]), "ashfur", lit=1, soft=1)
    # the ear: a tall triangle in front of the crown, dark inside
    et = (hx_ - 2.4 - p.ear * 4.0, hy - 9.2 + p.ear * 5.0)
    r.add(r.m_poly([(hx_ - 3.8, hy - 2.0), et, (hx_ + 0.8, hy - 3.4)]), "ashfur", soft=1)
    r.add(r.m_poly([(hx_ - 2.6, hy - 2.6), (et[0] + 0.7, et[1] + 2.6), (hx_ - 0.4, hy - 3.2)]), "ashfur", tone=1)
    r.px([(round(hx_ + 9), round(hy - 0.6))], "ashfur", 0)  # nose
    r.px([(round(hx_ + 9), round(hy - 1.6))], "ashfur", 3)  # a glint on the nose bridge
    # fangs (bone): the attacking part, brighter than the body
    fy_ = round(hy + 1.6)
    r.px([(round(hx_ + 7), fy_), (round(hx_ + 3.5), fy_)], "bone", 3)
    if jaw >= 2:
        jy = round(hy + 1.0 + jaw * 1.5)
        r.px([(round(hx_ + 7), fy_ + 1), (round(hx_ + 6), jy), (round(hx_ + 3), jy + 1)], "bone", 2)
    # eye: hand-placed yellow eye with a dark lid
    ex, ey = round(hx_ + 1.5), round(hy - 1.6)
    r.stamp(ex, ey, ["ab", "c."], {"a": ("eye", 3), "b": ("eye", 2), "c": ("eye", 0)})
    # spine crystals (glow, the enemy.magic magenta): 5 shards, tallest over the shoulders
    for i, (ox, h) in enumerate(((-2, 3), (3, 5), (8, 6), (12, 5), (16, 3))):
        cx = hip[0] + 1 + ox + p.stretch * (ox / 18)
        base = by - 5 + (p.pitch * (ox / 16)) - (1 if 1 <= i <= 3 else 0)
        h = h + p.spike
        lean = 1.2  # shards lean back
        r.poly([(cx - 1.8, base + 1.5), (cx - lean, base - h), (cx + 1.6, base + 1.5)], "glow", soft=1)
    # fur strands on the back and haunch (a darker groove and a lit ridge)
    r.shade(r.m_line(hip[0] - 2, hip[1] - 1, hip[0] + 2, hip[1] + 2), lambda t: max(1, t - 1))
    return r


def lying(r, p):
    """Defeat frame: fallen on its side, legs out toward the camera, murk spreading under it."""
    gy = GROUND
    # murk pool spreading under the body
    r.ellipse(21, gy - 1, 15 + p.puddle * 2, 1.9, "murk", soft=1)
    # legs sticking out forward (toward the viewer: down-right)
    for i, (x0, x1) in enumerate(((12, 16), (15, 19), (27, 30), (30, 33))):
        r.limb(x0, gy - 5, x1, gy - 1.5, 1.8, 1.3, "ashfur", dark=1 if i % 2 == 0 else 0)
    body = r.mask_of(r.m_ellipse(20, gy - 6, 12, 4.6), r.m_ellipse(10, gy - 6.5, 5, 4.4))
    r.add(body, "ashfur")
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

def frames():
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
