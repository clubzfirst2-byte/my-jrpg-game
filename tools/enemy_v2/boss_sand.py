"""砂嵐のヌシ (boss_sand): a floating sand-wraith, seen from the front. 80x96; only the tip of its
whirl touches the ground (row 94, outline row 95). Front-facing only.

Design (ENEMY_BOSS_DESIGN.md 3.3): a pointed hood, a pale stone mask whose eye holes glow
magenta, a body of murk-soaked sand (murksand) narrowing into a whirl, stone blades on both
forearms, pebbles floating around. Patterns: volley, charge, ring (phase 2).
Phase 2: the mask cracks.
"""

import math

import numpy as np

from rig import Rig, _connect4
from bossparts import cracks, orb

W, H = 80, 96
G = 94
CX = 40


class Pose:
    def __init__(self, **k):
        self.dy = 0  # float height change (+ down)
        self.arms = "rest"  # rest / up / forward / wide / fling / limp
        self.lean = 0  # head / body tilted toward the camera (charge): mask lower and bigger
        self.shift = 0
        self.spin = 0  # whirl phase (0..3)
        self.tight = 0  # whirl narrower (charge)
        self.grains = 0  # volley: grains gathering in front
        self.pebbles = 4  # floating pebbles
        self.orbit = 0  # pebble ring radius change (ring)
        self.eyes = "open"
        self.phase2 = False
        self.collapse = 0
        self.__dict__.update(k)


# hand positions (x from the centre, y from the top) for the named arm poses
ARMS = {
    "rest": (-25, 52, 25, 52), "up": (-24, 18, 24, 18), "forward": (-12, 58, 12, 58), "wide": (-30, 34, 30, 34),
    "fling": (-29, 25, 29, 25), "limp": (-20, 58, 20, 58), "brace": (-22, 26, 26, 46),
}


def A(n):
    return tuple(float(v) for v in ARMS[n])


def blade_arm(r, sx, sy, hx_, hy, s, **k):
    """Arm of sand from the shoulder to the hand, a stone blade jutting past the hand."""
    r.limb(sx, sy, hx_, hy, 4.4, 3.2, "murksand", soft=2, **k)
    dx, dy = hx_ - sx, hy - sy
    L = math.hypot(dx, dy) or 1
    ux, uy = dx / L, dy / L
    tip = (hx_ + ux * 11, hy + uy * 11)
    px_, py_ = -uy, ux
    r.add(r.m_poly([(hx_ + px_ * 3, hy + py_ * 3), (tip[0], tip[1]), (hx_ - px_ * 3, hy - py_ * 3)]), "mask", soft=1, **k)



def draw(p):
    r = Rig(W, H)
    c = p.collapse
    if c >= 4:
        return remains(r)
    dy = p.dy + c * 6
    cx = CX + p.shift
    # the whirl: bands of sand narrowing to the ground, offset by the spin phase
    n = 7 - c
    for i in range(n):
        y = 60 + dy + i * 5
        if y > G - 1:
            break
        w = max(3, (22 - p.tight * 3) - i * (3 - p.tight * 0.3))
        off = [-2, 0, 2, 0][(i + p.spin) % 4]
        r.add(r.m_ellipse(cx + off * (1 - c * 0.3), y, w, 3.2) & r.m_rect(-50, -50, W + 50, G - 1), "murksand", soft=1, dark=1 if (i + p.spin) % 2 else 0)
    if c < 3:
        r.limb(cx + [-1, 0, 1, 0][p.spin % 4], 60 + dy + (n - 1) * 5, cx, G - 0.6, 2, 1.0, "murksand", soft=1)  # the tip
    # body: a draped mass of sand under the hood
    body = r.m_poly([(cx - 16, 28 + dy), (cx + 16, 28 + dy), (cx + 22, 50 + dy), (cx + 14, 62 + dy), (cx, 66 + dy), (cx - 14, 62 + dy), (cx - 22, 50 + dy)])
    # round 4: the robe's hem is torn -- four ragged tails hang from it over the whirl
    for tx in (-11, -4, 4, 10):
        hy_ = 66 + dy - abs(tx) * 4 / 14
        body |= r.m_poly([(cx + tx - 2.5, hy_ - 2), (cx + tx + 2.5, hy_ - 2), (cx + tx + 2, hy_ + 2), (cx + tx + 1.5, hy_ + 5), (cx + tx - 0.5, hy_ + 5), (cx + tx - 1.5, hy_ + 2)])
    r.add(body, "murksand", soft=4)
    # sand streams on the robe
    for x in (-12, -5, 6, 13):
        r.shade(r.m_line(cx + x, 36 + dy, cx + x * 1.15, 60 + dy), lambda t: max(1, t - 1))
    # the core on the chest
    ky = 46 + dy
    r.ellipse(cx, ky, 6, 6, "murk", soft=2)
    r.stamp(cx - 3, ky - 3, ["..a..", ".abb.", "abbcb", ".bcd.", "..d.."], {"a": ("glow", 4), "b": ("glow", 3), "c": ("glow", 2), "d": ("glow", 1)}
            if c < 3 else {"a": ("glow", 2), "b": ("glow", 1), "c": ("glow", 1), "d": ("glow", 0)})
    # arms
    sl, sr = (cx - 15, 33 + dy), (cx + 15, 33 + dy)
    a = ARMS[p.arms] if isinstance(p.arms, str) else p.arms  # v2: a tuple, eased between the named poses
    hands = ((cx + a[0], a[1] + dy), (cx + a[2], a[3] + dy))
    blade_arm(r, sl[0], sl[1], hands[0][0], hands[0][1], -1)
    blade_arm(r, sr[0], sr[1], hands[1][0], hands[1][1], 1)
    # hood: pointed, its point bending back slightly
    hy = max(26 + dy + p.lean, 27)
    hood = r.m_poly([(cx - 17, hy + 2), (cx - 12, hy - 12), (cx - 2, hy - 23), (cx + 1, hy - 25), (cx + 4, hy - 21), (cx + 13, hy - 11),
                     (cx + 17, hy + 2), (cx + 11, hy + 9), (cx - 11, hy + 9)])
    r.add(hood, "murksand", soft=3)
    # round 4: wind folds in the hood -- four bands flaring down from the point, each a 2-px
    # crease one tone lighter than the cloth under it with its shadow (one tone darker) on the
    # right. Offsets from the hood's point, so the folds belong to the hood and move with it.
    for fx0, fx1, fx2 in ((-3, -9, -15), (-1, -5, -10), (3, 7, 11), (5, 11, 16)):
        crease = _connect4(r.m_chain([(cx + fx0 * 1.6, hy - 12), (cx + fx1, hy - 5), (cx + fx2, hy + 6)], [1.2, 1.2, 1.2]) & hood) & hood
        shadow = np.zeros_like(crease)
        shadow[:, 1:] = crease[:, :-1]
        r.shade(_connect4(shadow & ~crease & hood) & ~crease & hood, lambda t: max(1, t - 1), on=True)
        r.shade(crease, lambda t: min(3, t + 1), on=True)
    r.add(r.m_ellipse(cx, hy + 1, 11, 11), "murksand", tone=0)  # the dark inside of the hood
    # the stone mask (hand-placed details on a shaded oval)
    ms = 1 + p.lean * 0.04
    r.add(r.m_ellipse(cx, hy + 1, 8.5 * ms, 10 * ms), "mask", soft=2)
    # the carved face, hand-placed (v1.0 finish): heavy brow ridges slanting in, deep slanted eye
    # holes with the glow in them, a nose ridge, two tear grooves and a mouth slit
    face = MASK_FACE_SHUT if p.eyes == "shut" else MASK_FACE
    r.stamp(round(cx) - 6, round(hy) - 4, face, {"1": ("mask", 1), "3": ("mask", 3), "0": ("murk", 0), "a": ("glow", 4),
                                                   "b": ("glow", 3), "c": ("glow", 2), "d": ("glow", 1)})
    if p.phase2 or c:
        cracks(r, [(cx - 6, hy - 7, cx - 3, hy - 2), (cx + 3, hy + 3, cx + 6, hy + 8)])
    # floating pebbles around it
    base = [(6, 22), (74, 20), (4, 70), (76, 72), (12, 48), (68, 46), (40, 2), (24, 86), (56, 86)]
    for i, (x, y) in enumerate(base[:p.pebbles]):
        ang = math.atan2(y - 48, x - 40)
        x2, y2 = x + math.cos(ang) * p.orbit, y + math.sin(ang) * p.orbit + (p.spin % 2)
        if 1 <= x2 <= W - 2 and 1 <= y2 <= H - 2:
            r.ellipse(x2, y2, 2.6, 2.1, "mask", soft=1, dark=1)
    # volley: grains of sand and murk gathering in front of the body
    for i in range(p.grains):
        gx = cx + (i - (p.grains - 1) / 2) * 8
        gy = 72 + dy - abs(i - (p.grains - 1) / 2) * 2
        orb(r, gx, gy, 2.4)
    return r


def remains(r):
    """Purified: the whirl has fallen into a mound of sand; the mask lies on top, eyes dark."""
    r.ellipse(CX, G - 2, 26, 2.2, "murk", soft=2, dark=1)
    r.add(r.m_poly([(16, G), (24, G - 9), (36, G - 13), (48, G - 12), (58, G - 7), (64, G)]), "murksand", soft=3)
    r.ellipse(CX + 2, G - 12, 7.5, 5.5, "mask", soft=2)
    r.add(r.m_rect(CX - 3, G - 13, CX - 1, G - 12), "murk", tone=0)
    r.add(r.m_rect(CX + 4, G - 13, CX + 6, G - 12), "murk", tone=0)
    cracks(r, [(CX + 6, G - 16, CX + 8, G - 10)])
    for x, y in ((12, G - 2), (68, G - 3), (28, G - 1)):
        r.ellipse(x, y, 2.4, 1.8, "mask", soft=1, dark=1)
    return r


MASK_FACE = [
    "11.........11",
    ".111.....111.",
    "..0000.0000..",
    "..0abc.cba0..",
    "...000.000...",
    "...1..3..1...",
    "...1..1..1...",
    "....00000....",
]
MASK_FACE_SHUT = [
    "11.........11",
    ".111.....111.",
    "..0000.0000..",
    "..00d0.0d00..",
    "...000.000...",
    "...1..3..1...",
    "...1..1..1...",
    "....00000....",
]


def frames_v1():  # the v1 key poses (kept for reference; v2 frames() is at the end)
    f = {}
    f["idle.0"] = Pose(spin=0)
    f["idle.1"] = Pose(spin=1, dy=1)
    f["move.0"] = Pose(spin=2, shift=-3, arms="rest")
    f["move.1"] = Pose(spin=3, shift=3, arms="rest", dy=1)
    # volley: arms raised, grains gather in front; then the arms sweep forward and the fan flies
    f["windup_volley.0"] = Pose(arms="up", grains=3, spin=0, dy=-3)
    f["windup_volley.1"] = Pose(arms="up", grains=5, spin=1, dy=-2)
    f["attack_volley.0"] = Pose(arms="forward", spin=2, dy=1, lean=2)
    f["attack_volley.1"] = Pose(arms="rest", spin=3)
    # charge: tilts toward the camera, the whirl tightens and spins fast; then the rush
    f["windup_charge.0"] = Pose(arms="brace", lean=3, tight=3, spin=0)
    f["windup_charge.1"] = Pose(arms="brace", lean=3, tight=3, spin=2)
    f["attack_charge.0"] = Pose(arms="forward", lean=4, tight=3, spin=1, dy=2)
    f["attack_charge.1"] = Pose(arms="forward", lean=3, tight=2, spin=3, dy=1)
    # ring (phase 2): arms spread wide, more pebbles circle close; then they are flung out
    f["windup_ring.0"] = Pose(arms="wide", pebbles=8, orbit=-6, spin=0, phase2=True)
    f["windup_ring.1"] = Pose(arms="wide", pebbles=9, orbit=-10, spin=2, phase2=True, dy=-1)
    f["attack_ring.0"] = Pose(arms="fling", pebbles=9, orbit=4, spin=1, phase2=True, dy=-2)
    f["attack_ring.1"] = Pose(arms="wide", pebbles=5, orbit=6, spin=3, phase2=True)
    f["hurt.0"] = Pose(arms="limp", eyes="shut", dy=-2, lean=-1, spin=1)
    f["stagger.0"] = Pose(arms="limp", shift=-5, eyes="shut", spin=2, dy=2)
    f["stagger.1"] = Pose(arms="limp", shift=4, eyes="shut", spin=0, dy=3)
    f["idle2.0"] = Pose(phase2=True, spin=0, pebbles=6)
    f["idle2.1"] = Pose(phase2=True, spin=2, pebbles=6, dy=1)
    f["defeat.0"] = Pose(arms="fling", eyes="shut", phase2=True, dy=-2, spin=1, pebbles=2)
    f["defeat.1"] = Pose(collapse=1, arms="limp", eyes="shut", phase2=True, spin=2, pebbles=0)
    f["defeat.2"] = Pose(collapse=3, arms="limp", eyes="shut", phase2=True, spin=3, pebbles=0)
    f["defeat.3"] = Pose(collapse=4)
    return {k: draw(v) for k, v in f.items()}


SIZE = (W, H)
PATTERNS = ("volley", "charge", "ring")


# ------------------------------------------------------------------ v2 frames (4-8 per action)

def frames():
    from anim import boss
    P2 = dict(phase2=True)
    K = {
        "idle": [dict(spin=0, arms=A("rest")), dict(spin=0, dy=1, arms=A("rest")), dict(spin=0, dy=1, arms=(-25, 53, 25, 53)), dict(spin=0, arms=(-25, 53, 25, 53), lean=1)],
        "move": [dict(spin=0, shift=-3, arms=(-26.0, 50.0, 23.0, 54.0)), dict(spin=1, shift=0, dy=1, arms=A("rest")),
                 dict(spin=2, shift=3, arms=(-23.0, 54.0, 26.0, 50.0)), dict(spin=3, shift=0, dy=-1, arms=A("rest"))],
        "windup_volley": (dict(arms=A("up"), grains=3, spin=0, dy=-3), dict(arms=(-25.0, 15.0, 25.0, 15.0), grains=5, spin=1, dy=-3)),
        "attack_volley": (dict(arms=(-8, 64, 8, 64), spin=2, dy=4, lean=5, tight=3, shift=2), dict(arms=A("rest"), spin=3),
                          dict(arms=(-6, 66, 6, 66), spin=1, dy=5, lean=6, tight=3, shift=3)),
        "windup_charge": (dict(arms=A("brace"), lean=3, tight=3, spin=0), dict(arms=(-23.0, 24.0, 27.0, 47.0), lean=3.5, tight=3, spin=2)),
        "attack_charge": (dict(arms=A("forward"), lean=4, tight=3, spin=1, dy=2), dict(arms=A("forward"), lean=3, tight=2, spin=3, dy=1)),
        "windup_ring": (dict(arms=A("wide"), pebbles=8, orbit=-6, spin=0, **P2), dict(arms=(-31.0, 33.0, 31.0, 33.0), pebbles=9, orbit=-10, spin=2, dy=-1, **P2)),
        "attack_ring": (dict(arms=A("fling"), pebbles=9, orbit=4, spin=1, dy=-2, **P2), dict(arms=A("wide"), pebbles=5, orbit=6, spin=3, **P2)),
        "hurt": dict(arms=A("limp"), eyes="shut", dy=-2, lean=-1, spin=1),
        "stagger": (dict(arms=A("limp"), shift=-5, eyes="shut", spin=2, dy=2), dict(arms=A("limp"), shift=4, eyes="shut", spin=0, dy=3)),
        "idle2": [dict(spin=0, pebbles=6, arms=A("rest"), **P2), dict(spin=0, dy=1, pebbles=6, arms=A("rest"), **P2), dict(spin=0, dy=1, pebbles=6, arms=(-25, 53, 25, 53), **P2), dict(spin=0, pebbles=6, arms=(-25, 53, 25, 53), lean=1, **P2)],
        # defeat (round 2): the hit, the buckle, the collapse -- which then melts over two frames
        "defeat": [dict(arms=A("limp"), eyes="shut", dy=-1, spin=0, pebbles=4, **P2), dict(arms=A("fling"), eyes="shut", dy=-2, spin=1, pebbles=2, **P2),
                   dict(collapse=2, arms=A("limp"), eyes="shut", spin=3, pebbles=0, **P2)],
        "remains": dict(collapse=4),
    }
    return boss(Pose, draw, K, PATTERNS, phase2=("ring",))


PATTERNS = ("volley", "charge", "ring")
ACTIONS = __import__("anim").boss_actions(PATTERNS)
SMOOTH = set()  # shape fields that stay smooth (the rest snap to whole pixels)
