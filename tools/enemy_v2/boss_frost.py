"""凍て角のヌシ (boss_frost): a huge shaggy elk with spreading antlers of ice crystal, seen from the
front. 96x88 (antlers included), feet on row 86, outline on row 87. Front-facing only.

Design (ENEMY_BOSS_DESIGN.md 3.2): warm grey-tan fur (frostfur), a dark mane collar, a paler long
face, a magenta core crystal on the brow, glowing eyes; the wide branching ice antlers ARE the
silhouette. Patterns: slam, ring, charge (phase 2). Phase 2: the antler tips crack.

Rework after the inspection (F1-F5): the body is a beast's mass seen head-on -- two shoulder humps
over a deep shaggy chest, the back and rump showing behind them, a thick neck under a long hanging
mane, FRONT legs thick and near (elbow, knee, cannon, fetlock tuft, hoof) and HIND legs thinner,
darker and further back (their hooves stand higher on the ground). Fur is drawn as hanging strands
(rig texture "shag"). The mouth is a jaw that drops under the muzzle, never a dot on the chest.
Wind-ups are told by pose: slam = the head goes down to the chest and the antlers turn their tips
to the ground; ring = it rears, front hooves off the ground, head thrown up, antlers raised, large
ice crystals rising around it; charge = antlers levelled forward, a front hoof scraping.
"""

import math

from rig import Rig
from bossparts import glow_eyes, cracks

W, H = 96, 88
G = 86
CX = 48


class Pose:
    def __init__(self, **k):
        self.dy = 0  # the whole body down (+)
        self.head = 0  # head down (+) / up (-)
        self.hs = 1.0  # head scale (charge lunge: closer)
        self.fore = 1.0  # face length (foreshortening: < 1 when it points at / away from the camera)
        self.rot = 0  # antler rotation in degrees: + tips turn out and down (slam), - up and in (ring)
        self.lev = 0  # antlers levelled toward the camera (charge): 0..1 (flattened)
        self.legs = (0, 0, 0, 0)  # lift of each leg: front left, hind left, hind right, front right
        self.rear = 0  # rearing: front of the body up (+ px), front legs folded
        self.shift = 0
        self.mouth = 0  # jaw drop 0..3
        self.shards = 0  # ice crystals around (ring wind-up): count
        self.shard_r = 0  # how far out they are (0 at the body .. 1 at the frame edge)
        self.shard_s = 1.0  # their size
        self.eyes = "open"
        self.phase2 = False
        self.collapse = 0
        self.chips = False
        self.__dict__.update(k)


BEAM = [(0, 0), (9, -9), (20, -16), (32, -20), (42, -21)]
TINES = [(1, (6, -22)), (2, (20, -32)), (3, (37, -33)), ((1.5), (25, -27))]
BEAM_R = [3.2, 2.7, 2.3, 1.8, 1.0]


def antler(r, s, x0, y0, k, rot, lev, broken):
    """One antler: a main beam out and up with tines; s = -1 left, 1 right. k = scale.
    rot turns it about its base (+ = tips out and down), lev flattens it toward the camera."""
    a = math.radians(rot)
    ca, sa = math.cos(a), math.sin(a)

    def raw(dx, dy):
        dy = dy * (1 - 0.55 * lev)
        dx = dx * (1 + 0.12 * lev)
        return dx * ca - dy * sa, dx * sa + dy * ca

    # keep the whole antler (tip radius + outline) 1 px clear of the top edge: when a pose throws
    # the tips higher than the frame allows, the antler is drawn a little smaller instead of cut flat
    top = min(raw(*q)[1] for q in BEAM + [t for _, t in TINES])
    if y0 + top * k < 4.0 and top < 0:
        k = (y0 - 4.0) / -top

    def P(dx, dy):
        x, y = raw(dx, dy)
        return (x0 + s * x * k, y0 + y * k)

    def along(i):  # a point part-way along the beam (i may be fractional)
        j = int(i)
        if j >= len(BEAM) - 1:
            return BEAM[-1]
        f = i - j
        (ax, ay), (bx, by) = BEAM[j], BEAM[j + 1]
        return (ax + (bx - ax) * f, ay + (by - ay) * f)

    beam = [P(*q) for q in BEAM]
    radii = BEAM_R[:]
    if broken:
        beam, radii = beam[:-1], radii[:-1]
    r.chain(beam, radii, "ice", soft=1)
    for i, (at, tip) in enumerate(TINES):
        base = along(at)
        if broken and i in (1, 2):
            mid = ((base[0] + tip[0]) / 2, (base[1] + tip[1]) / 2 + 2)
            r.chain([P(*base), P(*mid)], [1.9, 1.4], "ice", soft=1)
            m = P(*mid)
            cracks(r, [(m[0] - 1, m[1], m[0] + 1, m[1] + 2)])
        else:
            r.chain([P(*base), P(*tip)], [1.9, 0.7], "ice", soft=1)
    # a crystal facet line down the beam (hand-like: the lit edge of the ice)
    for q0, q1 in zip(BEAM[1:3], BEAM[2:4]):
        (x0_, y0_), (x1_, y1_) = P(q0[0], q0[1] - 1), P(q1[0], q1[1] - 1)
        r.add(r.m_line(x0_, y0_, x1_, y1_), "ice", tone=4 if s < 0 else 3, cast=False)


def leg(r, top, knee, foot, r_top, r_knee, r_foot, dark, hoof_tone):
    """A leg with a joint: a thick upper leg to the knee, a thin cannon to the fetlock, a fur tuft
    at the fetlock, a dark hoof."""
    (tx, ty), (kx, ky), (fx, fy) = top, knee, foot
    up = r.limb(tx, ty, kx, ky, r_top, r_knee, "frostfur", dark=dark, soft=2, tex=("fur", 90, 3))
    if not dark:  # round 3: ice crusts on the near legs too
        r.pattern(up, (tx, ty), (5, 5), ICE_CRUST, ICE_LEG, seed=15, gaps=0.05)
    r.limb(kx, ky, fx, fy - 2, r_knee * 0.8, r_foot, "frostfur", dark=dark, soft=1)
    # the knee: a knob, one tone lighter on its lit side
    r.ellipse(kx - 0.5, ky, r_knee * 0.95, r_knee * 0.8, "frostfur", dark=dark, soft=1)
    # the fetlock tuft: hair hanging over the hoof in points
    fx_, fy_ = fx, fy - 3
    r.poly([(fx_ - r_foot - 1.5, fy_ - 2), (fx_ + r_foot + 1.5, fy_ - 2), (fx_ + r_foot + 1, fy_ + 1), (fx_ + 1, fy_ + 2.5),
            (fx_ - 0.5, fy_ + 1), (fx_ - 2, fy_ + 2.5), (fx_ - r_foot - 1, fy_ + 1)], "frostfur", dark=dark, soft=1)
    r.ellipse(fx, fy - 0.8, r_foot + 1.4, 1.7, "frostfur", tone=hoof_tone)


# round 3: hand-drawn material clusters (existing tones only)
ICE_LEG = {"a": ("ice", 4), "b": ("ice", 3), "c": ("ice", 2), "d": ("ice", 1), "f": ("frostfur", 1)}
ICE_CRUST = [["ab", "cd"], ["ab.", ".cd"], [".a", "bc", "d."], ["ac", "bd"]]
TAINT_LEG = {"a": ("glow", 3), "b": ("glow", 2), "c": ("glow", 1)}
TAINT = [["ab", "bc"], [".a.", "abc"], ["ab", "cc"]]
MANE_TIPS = [["b", "c"], ["bc", ".d"], ["c", "d"]]


def draw(p):
    r = Rig(W, H)
    c = p.collapse
    if c >= 4:
        return remains(r)
    dy = p.dy + c * 6
    cx = CX + p.shift
    rear = p.rear
    sy = 54 + dy - rear  # shoulder line
    # ---- hind legs (further back: thinner, darker, hooves higher on the ground)
    for i, s in ((1, -1), (2, 1)):
        lift = p.legs[i]
        hx0 = cx + s * 13
        foot = (CX + s * 14 + p.shift * 0.3, G - 4 - lift + min(rear, 3))  # rearing: the weight goes onto them
        leg(r, (hx0, sy + 6 + rear * 0.6), (hx0 + s * 1, min(sy + 18, G - 13) + rear * 0.3), foot, 4.2, 2.6, 1.8, 1, 0)
    # ---- the back and rump behind the shoulders (seen over them)
    back = r.add(r.m_ellipse(cx, sy - 3 + rear * 0.5, 24, 8), "frostfur", dark=1, soft=3, tex=("shag", 90, 1))
    r.pattern(back, (cx, sy), (7, 5), ICE_CRUST, ICE_LEG, seed=13)
    r.pattern(back, (cx + 4, sy), (12, 6), TAINT, TAINT_LEG, seed=17, gaps=0.2)
    # ---- front legs (near, thick): elbow, knee, cannon, fetlock, hoof
    for i, s in ((0, -1), (3, 1)):
        lift = p.legs[i]
        top = (cx + s * 17, sy + 9)
        if rear:  # folded under the raised chest
            knee = (cx + s * 22, sy + 18)
            foot = (cx + s * 18, sy + 27)
        else:
            knee = (cx + s * 20 + p.shift * 0.2, min(sy + 20, G - 10) - lift * 0.6)
            foot = (CX + s * 22 + p.shift * 0.5, G - lift)
        leg(r, top, knee, foot, 5.4, 3.3, 2.3, 0, 1)
    # ---- shoulders and the deep shaggy chest (one mass)
    chest = r.mask_of(
        r.m_ellipse(cx - 14, sy + 2, 13, 10), r.m_ellipse(cx + 14, sy + 2, 13, 10),  # shoulder humps
        r.m_poly([(cx - 25, sy + 3), (cx + 25, sy + 3), (cx + 20, sy + 13), (cx + 14, sy + 17), (cx + 10, sy + 15), (cx + 5, sy + 20),
                  (cx + 1, sy + 16), (cx - 4, sy + 20), (cx - 9, sy + 15), (cx - 14, sy + 18), (cx - 20, sy + 13)]))
    chest &= r.m_rect(-50, -50, W + 50, G - 1)
    r.add(chest, "frostfur", soft=4, tex=("shag", 90, 2))
    # round 3: ice crusts frozen into the coat (hand-drawn 2-3 px clusters in the ice ramp),
    # anchored to the shoulders so they move with the body
    r.pattern(chest, (cx, sy), (6, 5), ICE_CRUST, ICE_LEG, seed=11, gaps=0.05)
    # ...and the murk's taint: small magenta sores where the ice has split the hide
    r.pattern(chest, (cx + 3, sy + 2), (8, 6), TAINT, TAINT_LEG, seed=16, gaps=0.1)
    # the crease between the shoulder humps and the chest (a fold, not a line across)
    for s in (-1, 1):
        r.shade(r.m_line(cx + s * 4, sy + 6, cx + s * 9, sy + 13), lambda t: max(1, t - 1))
    if p.phase2 or c:
        cracks(r, [(cx - 24, sy - 2, cx - 19, sy + 6), (cx + 19, sy - 1, cx + 23, sy + 8)])
    # ---- the head
    hs = p.hs
    fo = p.fore
    hy = 32 + dy + p.head - rear * 0.6
    if c:
        hy = max(hy, 32 + c * 7)
    hx_ = cx + p.shift * 0.4
    # neck: thick, from the chest up into the head
    neck = r.add(r.m_limb(cx, sy + 3, hx_, hy + 8, 11, 8), "frostfur", dark=1, soft=3, tex=("shag", 90, 4))
    r.pattern(neck, (hx_, hy), (7, 6), ICE_CRUST, ICE_LEG, seed=14)
    # mane: a dark collar of long hair hanging from the throat over the chest, in long points
    mt = hy + 6 * fo
    mb = max(mt + 16, sy + 14)
    mane = r.m_poly([(hx_ - 8, mt - 2), (hx_ + 8, mt - 2), (hx_ + 13, mt + 4), (hx_ + 18, mb - 6), (hx_ + 12, mb - 3), (hx_ + 9, mb + 3), (hx_ + 4, mb - 1),
                     (hx_ + 1, mb + 5), (hx_ - 3, mb - 1), (hx_ - 8, mb + 3), (hx_ - 12, mb - 3), (hx_ - 18, mb - 6), (hx_ - 13, mt + 4)])
    r.add(mane, "frostfur", dark=1, soft=2, inline="br", tex=("shag", 90, 5))
    # round 3: frost on the hair tips of the mane
    r.pattern(mane, (hx_, mt), (6, 5), MANE_TIPS, ICE_LEG, seed=12, gaps=0.3)
    # ears (pointing out sideways, under the antlers)
    for s in (-1, 1):
        r.add(r.m_poly([(hx_ + s * 6, hy - 4), (hx_ + s * 18, hy - 4), (hx_ + s * 16, hy), (hx_ + s * 7, hy + 2)]), "frostfur", soft=1, inline=True)
        r.add(r.m_poly([(hx_ + s * 8.5, hy - 2.6), (hx_ + s * 15, hy - 2.6), (hx_ + s * 8.5, hy + 0.5)]), "frostfur", tone=1)
    # the long pale face, tapering to the muzzle
    L = 18 * hs * fo  # brow to muzzle
    face = r.m_poly([(hx_ - 9 * hs, hy - 8 * hs), (hx_ + 9 * hs, hy - 8 * hs), (hx_ + 8 * hs, hy + 0.35 * L), (hx_ + 5 * hs, hy + L),
                     (hx_ - 5 * hs, hy + L), (hx_ - 8 * hs, hy + 0.35 * L)])
    r.add(face, "frostfur", lit=1, soft=2, inline=True, tex=("fur", 90, 6))
    # the lower jaw: drops with the mouth; the open mouth is the dark gap between muzzle and jaw
    mo = p.mouth
    if mo:
        r.add(r.m_ellipse(hx_, hy + L + 1.5 + mo * 0.6, 3.6 * hs, 1.0 + mo * 0.9), "murk", tone=1)
        r.add(r.m_ellipse(hx_, hy + L + 3 + mo * 1.4, 3.8 * hs, 1.8), "frostfur", soft=1, inline=True)
    r.add(r.m_ellipse(hx_, hy + L, 5.5 * hs, 3.4 * hs * max(fo, 0.8)), "frostfur", dark=1, soft=1, inline="br")  # muzzle
    r.px([(round(hx_ - 2), round(hy + L)), (round(hx_ + 1), round(hy + L))], "frostfur", 0)
    glow_eyes(r, hx_, hy + 3 * hs * fo, round(5 * hs), p.eyes, socket="frostfur")
    # antlers from the brow
    for s in (-1, 1):
        antler(r, s, hx_ + s * 5 * hs, hy - 6 * hs, hs * 0.8, p.rot + 6, p.lev, p.phase2)
    # the core crystal on the brow (hand-placed)
    r.stamp(round(hx_) - 3, round(hy - 13 * hs), ["...a...", "..abb..", ".abbcb.", "abbccbd", ".bccbd.", "..bdd..", "...d..."],
            {"a": ("glow", 4), "b": ("glow", 3), "c": ("glow", 2), "d": ("glow", 1)} if c < 3 else {"a": ("glow", 2), "b": ("glow", 1), "c": ("glow", 1), "d": ("glow", 0)})
    # ring: large ice crystals around it (same colours as the antlers), rising then flying out
    for i in range(p.shards):
        a = math.pi * (0.08 + 0.84 * i / max(p.shards - 1, 1))  # spread from the right over the top to the left
        a = -a if i % 2 else a
        ang = -math.pi / 2 + (i - (p.shards - 1) / 2) * (2.6 / max(p.shards - 1, 1))
        rx_, ry_ = 22 + 24 * p.shard_r, 18 + 22 * p.shard_r
        x = CX + math.cos(ang) * rx_
        y = 58 + math.sin(ang) * ry_ * 0.4 + 18 * (1 - p.shard_r) - (i % 2) * 4
        y = min(max(y, 8), G - 6)
        x = min(max(x, 6), W - 7)
        k = p.shard_s
        r.poly([(x, y - 6 * k), (x + 3 * k, y - 1 * k), (x + 1.5 * k, y + 5 * k), (x - 1.5 * k, y + 5 * k), (x - 3 * k, y - 1 * k)], "ice", soft=1)
        r.add(r.m_line(x - 1, y - 4 * k, x - 1, y + 3 * k), "ice", tone=4, cast=False)
    if p.chips:
        for x, y in ((10, G - 3), (86, G - 4), (20, G - 1), (76, G - 1), (30, G - 9), (66, G - 9), (6, G - 11), (90, G - 12)):
            r.poly([(x, y - 2.5), (x + 1.5, y), (x, y + 1.5), (x - 1.5, y)], "ice", soft=1)
    return r


def remains(r):
    """Purified: the elk has sunk into a heap of pale fur; the antlers lie broken on top."""
    r.ellipse(CX, G - 2, 32, 2.4, "murk", soft=2, dark=1)
    r.add(r.m_poly([(20, G), (26, G - 12), (40, G - 18), (56, G - 18), (70, G - 12), (76, G)]), "frostfur", soft=3, tex=("shag", 90, 2))
    for s in (-1, 1):
        r.chain([(CX + s * 6, G - 16), (CX + s * 20, G - 22), (CX + s * 32, G - 18)], [2.4, 2.0, 1.0], "ice", soft=1)
        r.chain([(CX + s * 18, G - 21), (CX + s * 20, G - 29)], [1.6, 0.7], "ice", soft=1)
    r.stamp(CX - 2, G - 14, [".a.", "abb", ".b."], {"a": ("glow", 2), "b": ("glow", 1)})
    return r


def frames_v1():  # the v1 key poses (kept for reference; v2 frames() is at the end)
    f = {}
    f["idle.0"] = Pose()
    f["idle.1"] = Pose(dy=1, head=1)
    f["move.0"] = Pose(legs=(4, 0, 3, 0), shift=-2)
    f["move.1"] = Pose(legs=(0, 3, 0, 4), shift=2)
    # slam: the head goes down to the chest, the antler tips turn to the ground; then they strike
    f["windup_slam.0"] = Pose(head=7, rot=28, fore=0.85, dy=1)
    f["windup_slam.1"] = Pose(head=13, rot=52, fore=0.7, dy=2, legs=(0, 0, 0, 0))
    f["attack_slam.0"] = Pose(head=16, rot=70, fore=0.6, dy=3, chips=True)
    f["attack_slam.1"] = Pose(head=10, rot=40, fore=0.8, dy=2)
    # ring: it rears up, head thrown back, antlers raised; big ice crystals rise around it;
    # then the front hooves stamp down and the crystals fly out to the edges
    f["windup_ring.0"] = Pose(rear=4, head=-1, rot=-4, fore=0.75, mouth=1, shards=4, shard_r=0.2, shard_s=1.0)
    f["windup_ring.1"] = Pose(rear=8, head=-1, rot=-6, fore=0.65, mouth=2, shards=6, shard_r=0.35, shard_s=1.3)
    f["attack_ring.0"] = Pose(head=-1, rot=-8, fore=0.65, mouth=3, dy=1, shards=8, shard_r=1.0, shard_s=1.1, chips=True)
    f["attack_ring.1"] = Pose(head=-3, rot=-12, fore=0.8, mouth=1, shards=6, shard_r=1.25, shard_s=0.7)
    # charge (phase 2): antlers levelled forward, a front hoof scrapes; then the lunge
    f["windup_charge.0"] = Pose(head=6, lev=0.7, rot=8, fore=0.8, legs=(5, 0, 0, 0), phase2=True)
    f["windup_charge.1"] = Pose(head=8, lev=0.9, rot=10, fore=0.75, legs=(0, 0, 0, 5), phase2=True, shift=1)
    f["attack_charge.0"] = Pose(head=9, lev=1.0, rot=12, hs=1.12, fore=0.75, phase2=True, legs=(3, 0, 0, 0))
    f["attack_charge.1"] = Pose(head=6, lev=0.7, rot=8, hs=1.06, fore=0.85, phase2=True)
    f["hurt.0"] = Pose(head=-3, rot=-6, eyes="shut", mouth=2, shift=-2)
    f["stagger.0"] = Pose(shift=-5, legs=(0, 0, 3, 6), head=3, rot=10, eyes="shut")
    f["stagger.1"] = Pose(shift=4, legs=(5, 2, 0, 0), head=4, rot=14, eyes="shut")
    f["idle2.0"] = Pose(phase2=True)
    f["idle2.1"] = Pose(phase2=True, dy=1, head=1)
    f["defeat.0"] = Pose(head=-3, rot=-6, eyes="shut", mouth=3, phase2=True, legs=(3, 0, 0, 0))
    f["defeat.1"] = Pose(collapse=1, head=6, rot=24, eyes="shut", phase2=True)
    f["defeat.2"] = Pose(collapse=3, head=10, rot=40, eyes="shut", phase2=True)
    f["defeat.3"] = Pose(collapse=4)
    return {k: draw(v) for k, v in f.items()}


SIZE = (W, H)
PATTERNS = ("slam", "ring", "charge")


# ------------------------------------------------------------------ v2 frames (4-8 per action)

def frames():
    from anim import boss
    P2 = dict(phase2=True)
    K = {
        "idle": [{}, dict(dy=1), dict(dy=1, fore=0.92), dict(fore=0.92, mouth=1)],
        "move": [dict(legs=(4, 0, 3, 0), shift=-2), dict(legs=(1, 1, 1, 1), dy=-1, head=-1, rot=-2),
                 dict(legs=(0, 3, 0, 4), shift=2), dict(legs=(1, 1, 1, 1), dy=-0.5, head=1, rot=2)],
        "windup_slam": (dict(head=7, rot=28, fore=0.85, dy=1), dict(head=14, rot=56, fore=0.68, dy=2)),
        "attack_slam": (dict(head=16, rot=70, fore=0.6, dy=3, chips=True), dict(head=10, rot=40, fore=0.8, dy=2)),
        "windup_ring": (dict(rear=4, head=-1, rot=-4, fore=0.75, mouth=1, shards=4, shard_r=0.2, shard_s=1.0),
                        dict(rear=8, head=-1, rot=-6, fore=0.65, mouth=2, shards=6, shard_r=0.35, shard_s=1.3)),
        "attack_ring": (dict(head=-1, rot=-8, fore=0.65, mouth=3, dy=1, shards=8, shard_r=1.0, shard_s=1.1, chips=True),
                        dict(head=-3, rot=-12, fore=0.8, mouth=1, shards=6, shard_r=1.25, shard_s=0.7)),
        "windup_charge": (dict(head=6, lev=0.7, rot=8, fore=0.8, legs=(5, 0, 0, 0), **P2),
                          dict(head=8, lev=0.95, rot=10, fore=0.75, legs=(0, 0, 0, 5), shift=1, **P2)),
        "attack_charge": (dict(head=9, lev=1.0, rot=12, hs=1.12, fore=0.75, legs=(3, 0, 0, 0), **P2),
                          dict(head=6, lev=0.7, rot=8, hs=1.06, fore=0.85, **P2)),
        "hurt": dict(head=-3, rot=-6, eyes="shut", mouth=2, shift=-2),
        "stagger": (dict(shift=-5, legs=(0, 0, 3, 6), head=3, rot=10, eyes="shut"), dict(shift=4, legs=(5, 2, 0, 0), head=4, rot=14, eyes="shut")),
        "idle2": [dict(**P2), dict(dy=1, **P2), dict(dy=1, fore=0.92, **P2), dict(fore=0.92, mouth=1, **P2)],
        # defeat (round 2): the hit, the buckle, the collapse -- which then melts over two frames
        "defeat": [dict(head=-4, rot=-8, eyes="shut", mouth=3, shift=-3, **P2), dict(head=-3, rot=-6, eyes="shut", mouth=3, legs=(3, 0, 0, 0), **P2),
                   dict(collapse=2, head=8, rot=32, eyes="shut", **P2)],
        "remains": dict(collapse=4),
    }
    return boss(Pose, draw, K, PATTERNS, phase2=("charge",))


PATTERNS = ("slam", "ring", "charge")
ACTIONS = __import__("anim").boss_actions(PATTERNS)
SMOOTH = {"rot", "lev", "fore", "hs", "shard_r", "shard_s"}  # shape fields that stay smooth (the rest snap to whole pixels)
