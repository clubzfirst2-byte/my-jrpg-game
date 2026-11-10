"""朽ち根のヌシ (boss_root): a huge boar of dead roots, seen from the front. 96x80, feet on row 78,
outline on row 79. Front-facing only (the game may mirror it for a charge to the left).

Silhouette (ENEMY_BOSS_DESIGN.md 3.1): long root spikes on the back, spikes out of the shoulders,
front legs splayed wide like roots ending in root toes, the head pushed forward and low with
pointed ears, pale tusks sweeping out sideways and up (free of the body), a root beard to the
ground; the core shows between root ribs on the chest; pale orange fungus on the body.
Patterns: charge, slam, volley (phase 2). Phase 2: the ribs split, the core is bared.
"""

from rig import Rig
from bossparts import core, glow_eyes, orb, cracks

W, H = 96, 80
G = 78
CX = 48


class Pose:
    def __init__(self, **k):
        self.dy = 0  # whole body down
        self.lift = 0  # back / shoulders up (-) (charge wind-up, rearing)
        self.head = 0  # head down (+)
        self.hs = 1.0  # head scale (closer to the camera when charging)
        self.legs = (0, 0)  # lift of the left / right front leg
        self.spread = 0  # legs further apart (+)
        self.shift = 0  # upper body sideways (stagger)
        self.jaw = 0
        self.orbs = 0  # orbs gathering in front of the core (volley)
        self.eyes = "open"
        self.phase2 = False
        self.collapse = 0  # defeat 0..4
        self.chips = False
        self.spikes = 0  # spikes bristle (+ longer)
        self.fan = 0  # spikes fan out sideways (+), bristling
        self.raise_ = 0  # front legs raised above the body (rearing) 0..1
        self.__dict__.update(k)


# round 3: hand-drawn material clusters (existing tones only)
FUNGI_LEG = {"a": ("fungus", 3), "b": ("fungus", 2), "c": ("fungus", 1), "g": ("glow", 3), "h": ("glow", 2), "k": ("glow", 1)}
FUNGI = [["ab", "cc"], [".a.", "abc"], ["gh", "hk"], ["ab", "ck"]]

def draw(p):
    r = Rig(W, H)
    c = p.collapse
    dy = p.dy + c * 4
    lift = p.lift
    cx = CX + p.shift
    by = 34 + dy + lift  # body centre
    if c >= 4:
        return remains(r)
    # hind legs: short and thick, seen between the front legs (they carry it when it rears)
    if c < 3:
        for s in (-1, 1):
            r.limb(cx + s * 12, by + 8, CX + s * 14, G - 3, 5.0, 3.6, "rotwood", dark=1, tex=("bark", 90, 1))
            r.ellipse(CX + s * 14, G - 2.5, 4.4, 1.6, "rotwood", tone=0)
    # splayed front legs ending in root toes (behind the body), each a bent root
    def front_legs():
        for s, lf in ((-1, p.legs[0]), (1, p.legs[1])):
            sx_, sy_ = cx + s * 20, by + 10
            kx, ky = CX + s * (30 + p.spread * 0.6), 56 + dy * 0.5 - lf * 0.7
            fx, fy = CX + s * (35 + p.spread * 0.5), G - 3 - lf
            up = 1
            if p.raise_:  # rearing: the root legs swing out and up above the shoulders, toes clawing
                k = p.raise_
                sx_, sy_ = cx + s * 22, by + 2
                kx, ky = kx + (cx + s * 37 - kx) * k, ky + (by + 2 - ky) * k
                fx, fy = fx + (cx + s * 40 - fx) * k, fy + (by - 20 - fy) * k
                up = 1 - 2 * k
            r.chain([(sx_, sy_), (kx, ky), (fx, fy)], [6.5, 5.0, 4.0], "rotwood", tex=("bark", 70 if s < 0 else 110, 2))
            # root toes: three spreading fingers
            for t, (dx, ln) in enumerate(((-6, 4), (0, 5), (6, 4))):
                r.limb(fx, fy, fx + dx * 0.8 + s * 1.0, fy + (1.4 + (ln - 4) * 0.4) * up - (4 if up < 0 else 0), 2.4, 1.1, "rotwood", soft=1, dark=1 if t == 1 else 0)
    if not p.raise_:
        front_legs()
    # back spikes: long roots of different lengths, curving back
    for x, h in ((22, 10), (30, 16), (38, 20), (48, 22), (58, 20), (66, 16), (74, 10)):
        h = min(h + p.spikes, by - 12.5)
        bx = cx + (x - CX) * 1.0
        fan = (x - CX) * 0.06 * p.fan
        r.chain([(bx, by - 10), (bx + (x - CX) * 0.08 + fan * 0.5, by - 10 - h * 0.6), (bx + (x - CX) * 0.2 + fan, by - 10 - h + abs(fan) * 0.4)],
                [3.4, 2.2, 0.8], "rotwood", soft=1)
    # the body: a broad hunched mass
    body = r.mask_of(r.m_ellipse(cx, by, 30, 17), r.m_ellipse(cx, by + 6, 24, 13))
    r.add(body, "rotwood", soft=4, tex=("bark", "radial", 3, {"centre": (cx, by - 3), "calm": (cx, by - 3, 11)}))
    # round 3: tiny fungus caps and beads of tainted sap in the bark's seams (hand-drawn clusters)
    r.pattern(body, (cx, by), (9, 7), FUNGI, FUNGI_LEG, seed=41, gaps=0.3)
    # shoulder spikes pointing out
    for s in (-1, 1):
        r.chain([(cx + s * 24, by - 2), (cx + s * 32, by - 7), (cx + s * 40, by - 10)], [4.2, 2.6, 0.8], "rotwood", soft=1)
    # root grain: dark grooves sweeping over the body
    # fungus caps
    for fx_, fy_, rr in ((cx - 22, by - 4, 3.5), (cx + 21, by - 2, 3.0), (cx - 15, by + 7, 2.4), (cx + 25, by + 6, 2.0)):
        r.ellipse(fx_, fy_, rr, rr * 0.6, "fungus", soft=1)
        r.px([(round(fx_ - rr * 0.4), round(fy_) - 1)], "fungus", 4)
    if p.raise_:  # raised in front of the body
        front_legs()
    # the core between root ribs
    ky = by - 3
    core(r, cx, ky, 9 if p.phase2 or c else 7, bright=not c >= 3)
    if not p.phase2 and c < 2:
        for x in (-6, -2, 2, 6):  # ribs of root across the core
            r.limb(cx + x, ky - 8, cx + x * 1.1, ky + 8, 1.4, 1.4, "rotwood", soft=1)
    else:
        for s in (-1, 1):  # ribs split open
            r.chain([(cx + s * 5, ky - 10), (cx + s * 11, ky - 2), (cx + s * 7, ky + 9)], [1.6, 1.8, 1.4], "rotwood", soft=1)
    if p.phase2 or c:
        cracks(r, [(cx - 18, by - 8, cx - 12, by + 2), (cx + 14, by - 10, cx + 19, by + 1), (cx - 4, by + 9, cx + 3, by + 14)])
    # head: pushed forward and low
    hs = p.hs
    hy = min(54 + dy + p.head, G - 17 * hs)
    hx_ = cx + p.shift * 0.3
    for s in (-1, 1):  # pointed ears
        r.add(r.m_poly([(hx_ + s * 8 * hs, hy - 8 * hs), (hx_ + s * 17 * hs, hy - 15 * hs), (hx_ + s * 13 * hs, hy - 3 * hs)]), "rotwood", soft=1)
        r.add(r.m_poly([(hx_ + s * 10 * hs, hy - 8 * hs), (hx_ + s * 15 * hs, hy - 12.5 * hs), (hx_ + s * 12.5 * hs, hy - 5 * hs)]), "rotwood", tone=1)
    head = r.mask_of(r.m_ellipse(hx_, hy, 12.5 * hs, 10 * hs), r.m_ellipse(hx_, hy + 8 * hs, 7.5 * hs, 5.5 * hs))
    if p.jaw:
        r.add(r.m_ellipse(hx_, hy + 11 * hs + p.jaw, 6.5 * hs, 3.0 + p.jaw * 0.6), "rotwood", dark=1, soft=1)
        r.add(r.m_ellipse(hx_, hy + 10 * hs + p.jaw * 0.5, 5 * hs, 1.2 + p.jaw * 0.7), "murk", tone=0)
        head &= ~r.m_ellipse(hx_, hy + 11 * hs + p.jaw * 0.5, 5 * hs, 1.2 + p.jaw * 0.7)
    r.add(head, "rotwood", soft=2, tex=("bark", 0, 7))
    # snout disc with nostrils (hand-placed)
    r.ellipse(hx_, hy + 8 * hs, 4.6 * hs, 3.0 * hs, "rotwood", lit=1, soft=1)
    r.px([(round(hx_ - 2), round(hy + 8 * hs)), (round(hx_ + 1), round(hy + 8 * hs))], "rotwood", 0)
    # tusks: out to the side, then up, free of the body
    for s in (-1, 1):
        t0 = (hx_ + s * 6 * hs, hy + 8 * hs)
        t1 = (hx_ + s * 17 * hs, hy + 13 * hs)
        t2 = (hx_ + s * 24 * hs, hy + 4 * hs)
        t3 = (hx_ + s * 25 * hs, hy - 3 * hs)
        r.chain([t0, t1, t2, t3], [2.6, 2.6, 2.2, 0.8], "bone", soft=1)
    # root beard to the ground
    if c < 2:
        for x in (-4, 0, 4):
            r.limb(hx_ + x, hy + 13 * hs + p.jaw, hx_ + x * 1.6, min(G - 1, hy + 23), 1.2, 0.8, "rotwood", soft=1, dark=1)
    glow_eyes(r, hx_, hy - 3 * hs, round(5 * hs), p.eyes, socket="rotwood")
    # volley: orbs lined up in front of the core
    for i in range(p.orbs):
        orb(r, cx + (i - (p.orbs - 1) / 2) * 10, ky + 4 - abs(i - (p.orbs - 1) / 2) * 3, 3.4)
    if p.chips:
        for x, y in ((14, G - 4), (82, G - 5), (24, G - 1), (72, G - 2), (8, G - 9), (88, G - 10)):
            r.ellipse(x, min(y, G - 2), 1.6, 1.3, "rotwood", soft=1)
    return r


def remains(r):
    """The last frame of the purification: a heap of dead roots, the core gone dark, two tusks."""
    r.ellipse(CX, G - 2, 30, 2.4, "murk", soft=2, dark=1)
    r.add(r.m_poly([(20, G), (28, G - 12), (42, G - 17), (56, G - 16), (70, G - 10), (76, G)]), "rotwood", soft=3)
    for x, h in ((32, 8), (44, 12), (56, 9), (64, 6)):
        r.chain([(x, G - 12), (x - 2, G - 12 - h)], [2.0, 0.8], "rotwood", soft=1)
    for s in (-1, 1):
        r.chain([(CX + s * 14, G - 3), (CX + s * 24, G - 2), (CX + s * 29, G - 7)], [2.0, 2.0, 0.8], "bone", soft=1)
    r.ellipse(CX, G - 9, 3.5, 3, "glow", tone=1)
    return r


def frames_v1():  # the v1 key poses (kept for reference; v2 frames() is at the end)
    f = {}
    f["idle.0"] = Pose()
    f["idle.1"] = Pose(dy=1, lift=1, spikes=1)
    f["move.0"] = Pose(legs=(5, 0), shift=-2, dy=0)
    f["move.1"] = Pose(legs=(0, 5), shift=2, dy=0)
    # charge: back rises, spikes bristle and fan, head drops low, tusks forward; the lunge
    f["windup_charge.0"] = Pose(lift=-5, head=10, hs=1.04, spikes=4, fan=5, spread=5)
    f["windup_charge.1"] = Pose(lift=-5, head=11, hs=1.08, spikes=4, fan=5, spread=5, jaw=1)
    f["attack_charge.0"] = Pose(lift=-2, head=8, hs=1.15, spread=3, jaw=2, legs=(2, 2), fan=2)
    f["attack_charge.1"] = Pose(lift=-1, head=5, hs=1.1, spread=2, jaw=1, fan=1)
    # slam: rears up on the hind legs, front legs lifted above the body, head up; then crashes down
    f["windup_slam.0"] = Pose(dy=-5, lift=-2, head=-5, raise_=0.55, spread=-2, jaw=1)
    f["windup_slam.1"] = Pose(dy=-8, lift=-3, head=-8, raise_=0.9, spread=-3, jaw=2)
    f["attack_slam.0"] = Pose(dy=3, head=3, spread=4, jaw=2, chips=True)
    f["attack_slam.1"] = Pose(dy=2, head=2, spread=3, jaw=1)
    # volley: the head throws up, the mouth gapes, the front legs brace wide, the spikes fan;
    # orbs line up before the bared core; then the fan leaves (recoil)
    f["windup_volley.0"] = Pose(jaw=3, orbs=3, head=-8, spread=8, fan=5, spikes=3, lift=-1, phase2=True)
    f["windup_volley.1"] = Pose(jaw=4, orbs=5, head=-9, spread=9, fan=6, spikes=3, lift=-2, phase2=True)
    f["attack_volley.0"] = Pose(jaw=3, head=-2, dy=-1, phase2=True)
    f["attack_volley.1"] = Pose(jaw=1, head=0, phase2=True)
    f["hurt.0"] = Pose(head=-4, eyes="shut", dy=-1, jaw=1)
    # stagger (after a perfect guard): knocked off balance to one side, then the other
    f["stagger.0"] = Pose(shift=-5, legs=(0, 6), head=2, eyes="shut", jaw=1)
    f["stagger.1"] = Pose(shift=4, legs=(4, 0), head=3, eyes="shut")
    f["idle2.0"] = Pose(phase2=True, spikes=1)
    f["idle2.1"] = Pose(phase2=True, dy=1, lift=1, spikes=2)
    f["defeat.0"] = Pose(head=-5, eyes="shut", jaw=2, phase2=True)
    f["defeat.1"] = Pose(collapse=1, head=4, eyes="shut", spread=3, phase2=True)  # the core stays bared through the purification
    f["defeat.2"] = Pose(collapse=3, head=6, eyes="shut", spread=5)
    f["defeat.3"] = Pose(collapse=4)
    return {k: draw(v) for k, v in f.items()}


SIZE = (W, H)
PATTERNS = ("charge", "slam", "volley")


# ------------------------------------------------------------------ v2 frames (4-8 per action)

def frames():
    from anim import boss
    P2 = dict(phase2=True)
    K = {
        "idle": [{}, dict(dy=1), dict(dy=1, head=1), dict(head=1, jaw=1)],
        "move": [dict(legs=(5, 0), shift=-2), dict(legs=(2, 2), dy=-1, head=-1), dict(legs=(0, 5), shift=2), dict(legs=(1, 1), dy=-0.5, head=1)],
        "windup_charge": (dict(lift=-5, head=10, hs=1.04, spikes=4, fan=5, spread=5), dict(lift=-6, head=12, hs=1.1, spikes=5, fan=6, spread=6, jaw=1)),
        "attack_charge": (dict(lift=-4, head=12, hs=1.2, spread=6, jaw=3, legs=(3, 3), fan=4, spikes=3), dict(lift=-1, head=5, hs=1.1, spread=2, jaw=1, fan=1),
                          dict(lift=-5, head=13, hs=1.26, spread=8, jaw=3, legs=(4, 4), fan=5, spikes=4, dy=2)),
        "windup_slam": (dict(dy=-5, lift=-2, head=-5, raise_=0.55, spread=-2, jaw=1), dict(dy=-8, lift=-3, head=-8, raise_=0.9, spread=-3, jaw=2)),
        "attack_slam": (dict(dy=4, head=5, spread=7, jaw=3, chips=True, fan=3), dict(dy=2, head=2, spread=3, jaw=1),
                        dict(dy=5, head=6, spread=9, jaw=3, chips=True, fan=5, spikes=3, lift=2)),
        "windup_volley": (dict(jaw=3, orbs=3, head=-8, spread=8, fan=5, spikes=3, lift=-1, **P2),
                          dict(jaw=4, orbs=5, head=-9, spread=9, fan=6, spikes=3, lift=-2, **P2)),
        "attack_volley": (dict(jaw=4, head=-9, spread=8, fan=6, spikes=3, lift=-2, **P2), dict(jaw=1, head=0, **P2),
                          dict(jaw=4, head=-5, spread=9, fan=7, spikes=4, lift=-3, dy=-2, hs=1.08, **P2)),
        "hurt": dict(head=-4, eyes="shut", dy=-1, jaw=1, shift=-2),
        "stagger": (dict(shift=-5, legs=(0, 6), head=2, eyes="shut", jaw=1), dict(shift=4, legs=(4, 0), head=3, eyes="shut")),
        "idle2": [dict(spikes=1, **P2), dict(dy=1, spikes=1, **P2), dict(dy=1, head=1, spikes=1, **P2), dict(head=1, jaw=1, spikes=1, **P2)],
        # defeat (round 2): the hit, the buckle, the collapse -- which then melts over two frames
        "defeat": [dict(head=-6, eyes="shut", jaw=3, shift=-3, **P2), dict(head=-5, eyes="shut", jaw=2, **P2),
                   dict(collapse=2, head=5, eyes="shut", spread=4, **P2)],
        "remains": dict(collapse=4),
    }
    return boss(Pose, draw, K, PATTERNS, phase2=("volley",))


PATTERNS = ("charge", "slam", "volley")
ACTIONS = __import__("anim").boss_actions(PATTERNS)
SMOOTH = {"raise_", "hs"}  # shape fields that stay smooth (the rest snap to whole pixels)
