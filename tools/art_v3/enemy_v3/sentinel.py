"""遺跡の番兵 (sentinel, NEW): a guardian machine of the 灯の民 ruins, cool grey stone and dark bronze,
a domed head with a narrow visor slit where one murk-tainted magenta eye glows; the near arm ends
in a huge stone fist. Right-facing (mirrored by the game), 40x56, feet on row 54, outline row 55.

Frames (ENEMY_BOSS_DESIGN.md 2.4): idle 2, move 4, windup 2, attack (slam) 2, hurt 1, defeat 3
(crumbles). Wind-up shows by SHAPE: the fist raised over the head (it clears the dome, behind it). The red ring is the program's.
"""

import numpy as np

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
    kk = dict(k, dark=k.get("dark", 0) + 1)  # v2: the corrupted stone is a tone darker
    r.add(r.mask_of(r.m_rect(hx_ - 3, hy, hx_ + 2, ky), r.m_poly([(kx - 3, ky), (kx + 3, ky), (fx + 2, fy - 3), (fx - 3, fy - 3)])), "oldstone", **kk)
    # murk creeping up the leg from the foot
    r.add(r.m_poly([(fx - 3, fy - 3), (fx + 2, fy - 3), (fx + 1, fy - 6), (fx - 1, fy - 4.5), (fx - 2.5, fy - 7)]), "murk", soft=1, **k)
    r.ellipse(kx, ky, 3.6, 1.8, "bronze", soft=1, **k)
    r.add(r.m_poly([(fx - 4, fy - 3.5), (fx + 3, fy - 3.5), (fx + 5, fy - 1), (fx + 5, fy + 1), (fx - 4, fy + 1)]), "bronze", **k)


# elbow and fist offsets from the shoulder (v1's named arm poses)
FIST = {
    "low": (3, 8, 5, 16),
    "mid": (5, -3, 6, -11),
    "high": (2, -9, -7, -18),
    "slam": (5, 6, 8, 25),
    "follow": (6, 7, 9, 23),
    "hurt": (1, 8, -1, 15),
}


def F(n):
    return tuple(float(v) for v in FIST[n])


def fist_arm(r, sx, sy, ex, ey, fx, fy, **k):
    """Upper arm (bronze joint) to forearm (stone) to the big stone fist centred at (fx, fy)."""
    r.ellipse(sx, sy, 4.2, 4.2, "bronze", soft=1, **k)  # shoulder joint
    r.limb(sx, sy, ex, ey, 2.6, 2.4, "bronze", soft=1, **k)
    kk = dict(k, dark=k.get("dark", 0) + 1)
    r.limb(ex, ey, fx, fy, 3.6, 4.2, "oldstone", **kk)
    r.add(r.m_poly([(fx - 4.5, fy - 4), (fx + 4.5, fy - 4.5), (fx + 5, fy + 4), (fx - 4, fy + 4.5)]), "oldstone", **kk)
    # spikes of corrupted crystal grown out of the knuckles (the fist is a weapon)
    for i in (-3, 0, 3):
        r.poly([(fx + i - 1.2, fy - 4), (fx + i + 0.6, fy - 7.5), (fx + i + 1.4, fy - 4)], "glow", soft=1)
    # knuckle grooves (dark) on the fist
    r.shade(r.m_line(fx - 3, fy, fx + 3, fy - 0.5), lambda t: 1)
    r.px([(round(fx - 2), round(fy) + 2), (round(fx + 1), round(fy) + 2)], "oldstone", 1)


def draw(p):
    r = Rig(W, H)
    r.darken = {"bronze": 1}  # v2 (hostile): tarnished, darker bronze -- no bright orange
    if p.collapse >= 2:
        return rubble(r, p)
    X, dy = p.x, p.dy
    cx = 17 + X
    hip_y = 40 + dy
    top = 21 + dy  # shoulders
    r.anchor = (cx, top)  # v3 round 2: the surface detail moves with the body
    # far arm (small, bronze and stone, hangs behind)
    r.limb(cx - 7, top + 3, cx - 9, top + 13, 2.4, 2.2, "bronze", dark=1, soft=1)
    r.add(r.m_rect(cx - 12, top + 13, cx - 6, top + 18), "oldstone", dark=1)
    leg(r, cx - 4, hip_y, *p.ff, dark=1)
    leg(r, cx + 3, hip_y, *p.nf)
    # pelvis block and the torso: an inverted trapezoid of stone with a bronze band
    r.add(r.m_poly([(cx - 7, hip_y - 4), (cx + 8, hip_y - 4), (cx + 6, hip_y + 2), (cx - 5, hip_y + 2)]), "bronze")
    torso = r.m_poly([(cx - 10, top), (cx + 10, top - 1), (cx + 11, top + 5), (cx + 8, hip_y - 3), (cx - 7, hip_y - 3), (cx - 10, top + 5)])
    r.add(torso, "oldstone", soft=3, dark=1)
    # v2 (hostile): jagged shoulder shards pointing up and back
    for dx, h in ((-9, 6), (-5, 8), (-1, 5)):
        r.poly([(cx + dx - 2, top + 1), (cx + dx - 2.5, top - h), (cx + dx + 2, top + 1)], "oldstone", soft=1, dark=1)
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
    r.stamp(cx - 2, top + 3, ["..a..", ".aba.", "abcba", ".aba.", "..a.."], {"a": ("glow", 2), "b": ("glow", 3), "c": ("glow", 4)})
    # v2 (hostile): the murk has split the stone -- two thick glowing cracks run out of the emblem
    # (round 2: 2 px wide, a bright core with a dark lip under it; two, not three, so they read at
    # 1x without being busy)
    for (x0, y0, x1, y1, x2, y2) in ((cx + 2, top + 5, cx + 6, top + 3, cx + 9, top + 6), (cx - 1, top + 8, cx - 3, top + 12, cx - 1, top + 16)):
        core = r.m_line(x0, y0, x1, y1) | r.m_line(x1, y1, x2, y2)
        wide = core.copy()
        wide[:, 1:] |= core[:, :-1]
        lip = np.zeros_like(wide)
        lip[1:, :] = wide[:-1, :]
        r.add(lip & ~wide, "glow", tone=1, cast=False)
        r.add(wide & ~core, "glow", tone=2, cast=False)
        r.add(core, "glow", tone=3, cast=False)
    # head: a dome on a bronze collar, visor slit with the eye
    hx_, hy = cx + 1, top - 7 + p.tilt * 0.5
    r.add(r.m_rect(hx_ - 5, top - 2, hx_ + 5, top + 1), "bronze")
    r.add(r.mask_of(r.m_ellipse(hx_, hy, 7.5, 7), r.m_rect(hx_ - 7, hy, hx_ + 7, hy + 5)), "oldstone", soft=2, dark=1)
    # a crack down the dome
    r.add(r.m_line(hx_ - 2, hy - 6, hx_ - 1, hy - 2) | r.m_line(hx_ - 1, hy - 2, hx_ - 3, hy), "glow", tone=2, cast=False)
    vy = round(hy + 1 + p.tilt * 0.4)
    # v2 (hostile): a visor slit that slants down toward the front (a glare), the eye a long
    # bright magenta streak, and murk weeping from it
    r.add(r.m_poly([(hx_ - 4, vy - 1), (hx_ + 7.5, vy + 0.5), (hx_ + 7.5, vy + 3), (hx_ - 4, vy + 2)]), "murk", tone=0)
    # v3 round 2: the slit's depth at texel size -- its upper lip lit stone, the inside stepping down
    # from murk 2 (near the lip) to murk 0 (deep), the lower lip in shade
    r.add(r.m_limb(hx_ - 4, vy - 1.2, hx_ + 7.5, vy + 0.3, 0.45, 0.45), "oldstone", tone=3, cast=False)
    r.add(r.m_limb(hx_ - 3.5, vy - 0.3, hx_ + 7, vy + 1.0, 0.5, 0.5), "murk", tone=1, cast=False)
    if p.eye:
        # the eye: a long glare in 4 tones with a hot white core and a halo fading into the slit
        r.tstamp(hx_ - 1.5, vy, ["aab..........", ".abbbcc......", "..bccgggcc...", "...bccggcccd.", ".....ddcccd..", "........dd..."],
                 {"a": ("glow", 1), "b": ("glow", 2), "c": ("glow", 3), "g": ("glow", 4), "d": ("glow", 1)})
        # weeping murk, 2 texels wide
        r.tstamp(hx_ + 1.8, vy + 3.6, ["mm.", "mm.", ".mm", ".m."], {"m": ("murk", 2)})
    else:
        r.stamp(hx_ + 2, vy + 1, ["bb"], {"b": ("glow", 1)})
    r.add(r.m_rect(hx_ - 7, vy + 3, hx_ + 7, vy + 4), "bronze", soft=1)  # a bronze brim under the visor
    # the near arm with the fist
    sx, sy = cx + 9, top + 3
    f = p.fist
    ex_, ey_, fx_, fy_ = FIST[f] if isinstance(f, str) else f  # v2: a tuple, eased between poses
    fist_arm(r, sx, sy, sx + ex_, sy + ey_, sx + fx_, max(6.5, sy + fy_), inline=fy_ < -8)
    if f == "slam" or (not isinstance(f, str) and fy_ > 22):
        # stone chips thrown up from the impact (the red ring is the program's)
        for x, y in ((sx + 3, G - 6), (sx + 15, G - 7), (sx + 1, G - 2), (sx + 17, G - 2)):
            r.ellipse(x, y, 1.2, 1.2, "oldstone", soft=1)
    return r


def rubble(r, p):
    r.darken = {"bronze": 1, "oldstone": 1}
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


def frames_v1():  # the v1 key poses (kept for reference; v2 frames() is at the end)
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


# ------------------------------------------------------------------ v2 frames (4-8 per action)

def frames():
    """v2: idle 4, move 8, windup 4, attack 5, hurt 3, defeat 6. A heavy machine: slow, with the
    weight landing on each step (the body sinks after the foot lands), a long wind-up."""
    from anim import loop, once, name
    out = {}
    st = dict(fist=F("low"), nf=(22.0, G), ff=(14.0, G))
    name(out, "idle", loop(Pose, 4, [
        (0.0, dict(st)), (0.25, dict(st, dy=1)), (0.5, dict(st, dy=1, tilt=1)), (0.75, dict(st, tilt=1, fist=(3, 9, 5, 17))),
    ]), draw)
    name(out, "move", loop(Pose, 8, [
        (0.0, dict(st, nf=(25.0, G), ff=(11.0, G), dy=1.0, fist=(3.0, 8.0, 4.0, 16.0))),
        (0.25, dict(st, nf=(21.0, G - 3.0), ff=(14.0, G), dy=0.0, fist=(3.0, 8.0, 5.0, 16.0))),
        (0.5, dict(st, nf=(18.0, G), ff=(19.0, G), dy=1.0, fist=(3.0, 8.0, 6.0, 16.0))),
        (0.75, dict(st, nf=(22.0, G), ff=(15.0, G - 3.0), dy=0.0, fist=(3.0, 8.0, 5.0, 16.0))),
    ]), draw)
    # windup: drops its weight (anticipation), the fist swings up past the shoulder, then high over
    # the dome; the head tips back
    name(out, "windup", once(Pose, 4, [
        (0.0, dict(fist=F("hurt"), tilt=0.0, dy=2.0, nf=(23.0, G), ff=(12.0, G))),
        (0.4, dict(fist=F("mid"), tilt=-1.0, dy=0.0, nf=(23.0, G), ff=(12.0, G))),
        (1.0, dict(fist=F("high"), tilt=-2.0, dy=3.0, nf=(24.0, G), ff=(10.0, G))),
    ]), draw)
    # attack: the fist comes down (fast), the impact, the follow-through bent over it, the
    # recovery as it straightens
    name(out, "attack", once(Pose, 5, [
        (0.0, dict(fist=(5.0, -2.0, 9.0, -4.0), tilt=0.0, dy=1.0, x=-1, nf=(23.0, G), ff=(10.0, G))),
        (0.25, dict(fist=F("slam"), tilt=2.0, dy=2.0, x=-2, nf=(23.0, G), ff=(10.0, G)), "in"),
        (0.5, dict(fist=(5.0, 6.0, 8.0, 24.0), tilt=2.5, dy=3.0, x=-2, nf=(23.0, G), ff=(10.0, G))),
        (0.75, dict(fist=F("follow"), tilt=1.0, dy=1.0, x=-2, nf=(23.0, G), ff=(10.0, G))),
        (1.0, dict(fist=F("low"), tilt=0.0, dy=0.0, x=-1, nf=(22.0, G), ff=(12.0, G))),
    ]), draw)
    name(out, "hurt", once(Pose, 3, [
        (0.0, dict(fist=F("hurt"), tilt=-3.0, x=-3, dy=1.0, eye=0, nf=(18.0, G), ff=(11.0, G - 2.0))),
        (0.5, dict(fist=F("hurt"), tilt=-1.0, x=-3, dy=2.0, eye=0, nf=(18.0, G), ff=(11.0, G))),
        (1.0, dict(fist=F("low"), tilt=0.0, x=-1, dy=0.5, eye=1, nf=(21.0, G), ff=(13.0, G))),
    ]), draw)
    d = once(Pose, 4, [
        (0.0, dict(fist=F("hurt"), tilt=-3.0, x=-2, dy=1.0, eye=0, nf=(20.0, G), ff=(12.0, G))),
        (0.5, dict(fist=F("hurt"), tilt=1.0, dy=3.0, eye=0, nf=(22.0, G), ff=(13.0, G))),
        (1.0, dict(fist=F("hurt"), tilt=3.0, dy=5.0, eye=0, nf=(22.0, G), ff=(13.0, G))),
    ])
    # round 2: the machine sags and its corrupted stone melts into the murk, then only rubble is left
    from anim import dissolve_from
    name(out, "defeat", dissolve_from(draw, [d[0], d[2], d[3]], Pose(collapse=3), pools=(8, 12)), None)
    return out


ACTIONS = (("idle", 4), ("move", 8), ("windup", 4), ("attack", 5), ("hurt", 3), ("defeat", 6))
SMOOTH = set()  # shape fields that stay smooth (the rest snap to whole pixels)
