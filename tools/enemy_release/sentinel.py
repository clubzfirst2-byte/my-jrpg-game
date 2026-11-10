"""遺跡の番兵 (sentinel, NEW): a guardian machine of the 灯の民 ruins, cool grey stone and dark bronze,
a domed head with a narrow visor slit where one murk-tainted magenta eye glows; the near arm ends
in a huge stone fist. Right-facing (mirrored by the game), 40x56, feet on row 54, outline row 55.

Frames (ENEMY_BOSS_DESIGN.md 2.4): idle 2, move 4, windup 2, attack (slam) 2, hurt 1, defeat 3
(crumbles). Wind-up shows by SHAPE: the fist raised over the head (it clears the dome, behind it). The red ring is the program's.
"""

from rig import Rig

W, H = 40, 56
G = 54


class Pose:
    def __init__(self, **k):
        self.x = 0
        self.dy = 0
        self.tilt = 0  # head tilt (pixels of the visor down at the front)
        self.nf = (22, G)  # near foot (front edge x)
        self.ff = (14, G)
        self.fist = "low"  # low / mid / high / slam / follow / hurt
        self.collapse = 0  # defeat 0..3
        self.eye = 1  # 1 lit, 0 dark
        self.__dict__.update(k)


def leg(r, hx_, hy, fx, fy, **k):
    # thick stone column, a bronze knee ring, a broad bronze foot
    kx, ky = (hx_ + fx) / 2, (hy + fy) / 2 - 1
    r.add(r.mask_of(r.m_rect(hx_ - 3, hy, hx_ + 2, ky), r.m_poly([(kx - 3, ky), (kx + 3, ky), (fx + 2, fy - 3), (fx - 3, fy - 3)])), "oldstone", **k)
    r.ellipse(kx, ky, 3.6, 1.8, "bronze", soft=1, **k)
    r.add(r.m_poly([(fx - 4, fy - 3.5), (fx + 3, fy - 3.5), (fx + 5, fy - 1), (fx + 5, fy + 1), (fx - 4, fy + 1)]), "bronze", **k)


def fist_arm(r, sx, sy, ex, ey, fx, fy, **k):
    """Upper arm (bronze joint) to forearm (stone) to the big stone fist centred at (fx, fy)."""
    r.ellipse(sx, sy, 4.2, 4.2, "bronze", soft=1, **k)  # shoulder joint
    r.limb(sx, sy, ex, ey, 2.6, 2.4, "bronze", soft=1, **k)
    r.limb(ex, ey, fx, fy, 3.6, 4.2, "oldstone", **k)
    r.add(r.m_poly([(fx - 4.5, fy - 4), (fx + 4.5, fy - 4.5), (fx + 5, fy + 4), (fx - 4, fy + 4.5)]), "oldstone", **k)
    # knuckle grooves (dark) on the fist
    r.shade(r.m_line(fx - 3, fy, fx + 3, fy - 0.5), lambda t: 1)
    r.px([(round(fx - 2), round(fy) + 2), (round(fx + 1), round(fy) + 2)], "oldstone", 1)


def draw(p):
    r = Rig(W, H)
    if p.collapse >= 2:
        return rubble(r, p)
    X, dy = p.x, p.dy
    cx = 17 + X
    hip_y = 40 + dy
    top = 21 + dy  # shoulders
    # far arm (small, bronze and stone, hangs behind)
    r.limb(cx - 7, top + 3, cx - 9, top + 13, 2.4, 2.2, "bronze", dark=1, soft=1)
    r.add(r.m_rect(cx - 12, top + 13, cx - 6, top + 18), "oldstone", dark=1)
    leg(r, cx - 4, hip_y, *p.ff, dark=1)
    leg(r, cx + 3, hip_y, *p.nf)
    # pelvis block and the torso: an inverted trapezoid of stone with a bronze band
    r.add(r.m_poly([(cx - 7, hip_y - 4), (cx + 8, hip_y - 4), (cx + 6, hip_y + 2), (cx - 5, hip_y + 2)]), "bronze")
    torso = r.m_poly([(cx - 10, top), (cx + 10, top - 1), (cx + 11, top + 5), (cx + 8, hip_y - 3), (cx - 7, hip_y - 3), (cx - 10, top + 5)])
    r.add(torso, "oldstone", soft=3)
    r.add(r.m_poly([(cx - 9, top + 11), (cx + 10, top + 10), (cx + 9.6, top + 13), (cx - 8.6, top + 14)]), "bronze", soft=1)
    # armour detail, hand-placed (v1.0 finish): rivets on the band, the seam between the chest
    # plates with a lit lip, and the line where the shoulder plate overlaps the chest
    # (v1.0 finish 2) rivets 2x2 with a lit top-left pixel, so they read at 1x
    for x_, y_ in ((cx - 7, top + 11), (cx - 2, top + 11), (cx + 3, top + 10), (cx + 7, top + 10)):
        r.stamp(x_, y_, ["ab", "bc"], {"a": ("bronze", 4), "b": ("bronze", 3), "c": ("bronze", 0)})
    # plate edges: a dark seam (tone 0) with a bright lip beside it
    r.add(r.m_line(cx + 4, top + 1, cx + 4, top + 9), "oldstone", tone=0, cast=False)
    r.add(r.m_line(cx + 5, top + 1, cx + 5, top + 9), "oldstone", tone=4, cast=False)
    r.add(r.m_line(cx - 9, top + 8, cx + 3, top + 8), "oldstone", tone=0, cast=False)
    r.add(r.m_line(cx - 9, top + 9, cx + 3, top + 9), "oldstone", tone=3, cast=False)
    # the chest plate emblem: a dim diamond with a centre point (the light gone out, tainted glow).
    # Symmetric left-right, so it reads the same when the game mirrors the sprite (no letter shape)
    r.stamp(cx - 2, top + 3, ["..a..", ".a.a.", "a.b.a", ".a.a.", "..a.."], {"a": ("glow", 1), "b": ("glow", 2)})
    # cracks in the stone (2-px groups)
    r.px([(cx + 6, top + 4), (cx + 6, top + 5), (cx + 7, top + 6)], "oldstone", 1)
    # head: a dome on a bronze collar, visor slit with the eye
    hx_, hy = cx + 1, top - 7 + p.tilt * 0.5
    r.add(r.m_rect(hx_ - 5, top - 2, hx_ + 5, top + 1), "bronze")
    r.add(r.mask_of(r.m_ellipse(hx_, hy, 7.5, 7), r.m_rect(hx_ - 7, hy, hx_ + 7, hy + 5)), "oldstone", soft=2)
    vy = round(hy + 1 + p.tilt * 0.4)
    r.add(r.m_rect(hx_ - 4, vy, hx_ + 7, vy + 2), "murk", tone=0)
    if p.eye:
        r.stamp(hx_ + 2, vy, ["abba", "bccb"], {"a": ("glow", 4), "b": ("glow", 3), "c": ("glow", 2)})
    else:
        r.stamp(hx_ + 2, vy + 1, ["bb"], {"b": ("glow", 1)})
    r.add(r.m_rect(hx_ - 7, vy + 3, hx_ + 7, vy + 4), "bronze", soft=1)  # a bronze brim under the visor
    # the near arm with the fist
    sx, sy = cx + 9, top + 3
    f = p.fist
    if f == "low":
        fist_arm(r, sx, sy, sx + 3, sy + 8, sx + 5, sy + 16)
    elif f == "mid":
        fist_arm(r, sx, sy, sx + 5, sy - 3, sx + 6, sy - 11)
    elif f == "high":  # over the head and a little behind it: the fist clears the top of the dome
        fist_arm(r, sx - 1, sy, sx + 2, sy - 9, hx_ + 1, 6, inline=True)
    elif f == "slam":
        fist_arm(r, sx, sy, sx + 5, sy + 6, sx + 8, sy + 25)
    elif f == "follow":
        fist_arm(r, sx, sy, sx + 6, sy + 7, sx + 9, sy + 23)
    elif f == "hurt":
        fist_arm(r, sx, sy, sx + 1, sy + 8, sx - 1, sy + 15)
    if f == "slam":
        # stone chips thrown up from the impact (the red ring is the program's)
        for x, y in ((sx + 3, G - 6), (sx + 15, G - 7), (sx + 1, G - 2), (sx + 17, G - 2)):
            r.ellipse(x, y, 1.2, 1.2, "oldstone", soft=1)
    return r


def rubble(r, p):
    """Defeat 2-3: fallen apart into blocks; the eye dims; at the end only a heap of stone."""
    if p.collapse == 2:
        r.add(r.m_poly([(8, G), (10, G - 12), (28, G - 13), (31, G)]), "oldstone", soft=2)  # the torso, toppled
        r.add(r.m_poly([(9, G - 6), (30, G - 7), (30, G - 4), (9, G - 3)]), "bronze", soft=1)
        r.add(r.mask_of(r.m_ellipse(30, G - 12, 6.5, 6), r.m_rect(24, G - 12, 36, G - 8)), "oldstone", soft=2)  # head rolled
        r.add(r.m_rect(26, G - 13, 35, G - 12), "murk", tone=0)
        r.px([(31, G - 13)], "glow", 1)
        r.add(r.m_poly([(1, G), (3, G - 7), (10, G - 8), (11, G)]), "oldstone", soft=1)  # the fist
        r.stamp(14, G - 11, ["a.a", "aaa"], {"a": ("glow", 1)})
    else:
        for x, y, w, h in ((6, G - 5, 8, 5), (13, G - 8, 10, 8), (22, G - 6, 8, 6), (29, G - 4, 7, 4)):
            r.add(r.m_poly([(x, y + h), (x + 1, y), (x + w - 1, y + 1), (x + w, y + h)]), "oldstone", soft=1)
        r.add(r.m_rect(15, G - 3, 26, G - 1), "bronze", soft=1)
        r.ellipse(19, G - 9, 4, 3, "oldstone", soft=1)
    return r


def frames():
    f = {}
    f["idle.0"] = Pose()
    f["idle.1"] = Pose(dy=1, tilt=1)
    # move: a slow, heavy stomp (body sinks on each step)
    f["move.0"] = Pose(nf=(25, G), ff=(11, G), dy=1)
    f["move.1"] = Pose(nf=(21, G - 3), ff=(14, G), dy=0)
    f["move.2"] = Pose(nf=(18, G), ff=(19, G), dy=1, x=0)
    f["move.3"] = Pose(nf=(22, G), ff=(15, G - 3), dy=0)
    # windup: the fist rises (to the shoulder, then over the head), the head tips back
    f["windup.0"] = Pose(fist="mid", tilt=-1, nf=(23, G), ff=(12, G))
    f["windup.1"] = Pose(fist="high", tilt=-2, dy=3, nf=(24, G), ff=(10, G))
    # attack: the slam into the ground in front, then the follow-through (body bent over it)
    f["attack.0"] = Pose(fist="slam", tilt=2, dy=2, x=-2, nf=(23, G), ff=(10, G))
    f["attack.1"] = Pose(fist="follow", tilt=1, dy=1, x=-2, nf=(23, G), ff=(10, G))
    f["hurt.0"] = Pose(fist="hurt", tilt=-3, x=-3, dy=1, eye=0, nf=(18, G), ff=(11, G - 2))
    f["defeat.0"] = Pose(fist="hurt", tilt=3, dy=4, eye=0, nf=(22, G), ff=(13, G))
    f["defeat.1"] = Pose(collapse=2)
    f["defeat.2"] = Pose(collapse=3)
    return {k: draw(v) for k, v in f.items()}


ACTIONS = (("idle", 2), ("move", 4), ("windup", 2), ("attack", 2), ("hurt", 1), ("defeat", 3))
SIZE = (W, H)
