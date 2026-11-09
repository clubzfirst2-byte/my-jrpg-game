"""凍て角のヌシ (boss_frost): a huge shaggy elk with spreading antlers of ice crystal, seen from the
front. 96x88 (antlers included), feet on row 86, outline on row 87. Front-facing only.

Design (ENEMY_BOSS_DESIGN.md 3.2): warm grey-tan fur (frostfur), a dark mane collar, a paler long
face, a magenta core crystal on the brow, glowing eyes; the wide branching ice antlers ARE the
silhouette. Patterns: slam, ring, charge (phase 2). Phase 2: the antler tips crack.
"""

from rig import Rig
from bossparts import glow_eyes, cracks

W, H = 96, 88
G = 86
CX = 48


class Pose:
    def __init__(self, **k):
        self.dy = 0
        self.head = 0  # head down (+)
        self.hs = 1.0
        self.ant = 0  # antlers tipped forward / down (+)
        self.legs = (0, 0, 0, 0)  # lift of each leg, left to right
        self.shift = 0
        self.mouth = 0
        self.shards = 0  # ice crystals floating around (ring wind-up): 0, 4, 8
        self.eyes = "open"
        self.phase2 = False
        self.collapse = 0
        self.chips = False
        self.__dict__.update(k)


def antler(r, s, x0, y0, k, ant, broken):
    """One antler: a main beam out and up with tines; s = -1 left, 1 right. k = scale."""
    def P(dx, dy):
        return (x0 + s * dx * k * (1 - abs(ant) * 0.02), max(3.0, y0 + (dy + ant * 0.045 * abs(dx) * (1 + abs(dy) / 30)) * k))
    beam = [P(0, 0), P(10, -10), P(22, -17), P(34, -21), P(43, -22)]
    if broken:
        beam = beam[:-1]
    r.chain(beam, [3.0, 2.6, 2.2, 1.8, 1.0][:len(beam)], "ice", soft=1)
    tines = [((10, -10), (8, -24)), ((22, -17), (21, -32)), ((34, -21), (38, -34)), ((16, -14), (26, -27))]
    for i, (a, b) in enumerate(tines):
        if broken and i in (1, 2):
            mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + 2)
            r.chain([P(*a), P(*mid)], [1.8, 1.4], "ice", soft=1)
            cracks(r, [(P(*mid)[0] - 1, P(*mid)[1], P(*mid)[0] + 1, P(*mid)[1] + 2)])
        else:
            r.chain([P(*a), P(*b)], [1.8, 0.7], "ice", soft=1)


def draw(p):
    r = Rig(W, H)
    c = p.collapse
    dy = p.dy + c * 5
    cx = CX + p.shift
    if c >= 4:
        return remains(r)
    by = 58 + dy
    # legs: four pillars, the inner pair further back (darker), hooves of dark fur
    for i, (lx, dark) in enumerate(((28, 0), (40, 1), (56, 1), (68, 0))):
        lift = p.legs[i]
        x = CX + (lx - CX) * (1 + c * 0.08)
        r.limb(x + p.shift * 0.4, by + 4, x, min(G - 3 - lift, G - 3), 5.0, 3.6, "frostfur", dark=dark)
        r.ellipse(x, G - 2.5 - lift, 4.2, 1.8, "frostfur", tone=1 if not dark else 0)
    # body: a shaggy barrel seen head-on, hair hanging in points at the bottom
    body = r.mask_of(r.m_ellipse(cx, by, 33, 15), r.m_poly([(cx - 30, by + 2), (cx + 30, by + 2), (cx + 24, by + 14), (cx + 16, by + 11),
                                                              (cx + 8, by + 16), (cx, by + 12), (cx - 8, by + 16), (cx - 16, by + 11), (cx - 24, by + 14)]))
    body &= r.m_rect(-50, -50, W + 50, G - 1)  # a collapsed body rests flat on the ground
    r.add(body, "frostfur", soft=4)
    for x in (-24, -14, 14, 24):  # hair strands
        r.shade(r.m_line(cx + x, by - 8, cx + x * 1.05, by + 9), lambda t: max(1, t - 1))
    if p.phase2 or c:
        cracks(r, [(cx - 22, by - 10, cx - 17, by - 1), (cx + 18, by - 8, cx + 22, by + 2)])
    hs = p.hs
    hy = max(min(37 + dy + p.head, G - 26 * hs), 37 + p.collapse * 3)
    hx_ = cx + p.shift * 0.4
    # mane: a dark collar of long hair in front of the body
    mane = r.m_poly([(hx_ - 19, hy + 6), (hx_ + 19, hy + 6), (hx_ + 21, hy + 17), (hx_ + 14, hy + 15), (hx_ + 10, hy + 22), (hx_ + 4, hy + 18),
                     (hx_, hy + 24), (hx_ - 4, hy + 18), (hx_ - 10, hy + 22), (hx_ - 14, hy + 15), (hx_ - 21, hy + 17)])
    r.add(mane, "frostfur", dark=1, soft=2, inline="br")
    # ears (pointing out sideways, under the antlers)
    for s in (-1, 1):
        r.add(r.m_poly([(hx_ + s * 7, hy - 4), (hx_ + s * 20, hy - 3), (hx_ + s * 17, hy + 1), (hx_ + s * 8, hy + 3)]), "frostfur", soft=1, inline=True)
        r.add(r.m_poly([(hx_ + s * 9, hy - 2.5), (hx_ + s * 17, hy - 2), (hx_ + s * 9, hy + 1)]), "frostfur", tone=1)
    # the long pale face, tapering to the muzzle
    face = r.m_poly([(hx_ - 9 * hs, hy - 8 * hs), (hx_ + 9 * hs, hy - 8 * hs), (hx_ + 8 * hs, hy + 6 * hs), (hx_ + 5 * hs, hy + 18 * hs),
                     (hx_ - 5 * hs, hy + 18 * hs), (hx_ - 8 * hs, hy + 6 * hs)])
    r.add(face, "frostfur", lit=1, soft=2, inline=True)
    r.ellipse(hx_, hy + 18 * hs, 5.5 * hs, 3.6 * hs, "frostfur", dark=1, soft=1)  # muzzle
    r.px([(round(hx_ - 2), round(hy + 18 * hs)), (round(hx_ + 1), round(hy + 18 * hs))], "frostfur", 0)
    if p.mouth:
        r.add(r.m_ellipse(hx_, hy + 21 * hs + p.mouth * 0.5, 2.6, 0.6 + p.mouth * 0.7), "murk", tone=0)
    glow_eyes(r, hx_, hy + 3 * hs, round(5 * hs), p.eyes)
    # antlers from the brow
    for s in (-1, 1):
        antler(r, s, hx_ + s * 5 * hs, hy - 6 * hs, hs * 0.86, p.ant, p.phase2)
    # the core crystal on the brow (hand-placed)
    r.stamp(round(hx_) - 3, round(hy - 12 * hs), ["...a...", "..abb..", ".abbcb.", "abbccbd", ".bccbd.", "..bdd..", "...d..."],
            {"a": ("glow", 4), "b": ("glow", 3), "c": ("glow", 2), "d": ("glow", 1)} if c < 3 else {"a": ("glow", 2), "b": ("glow", 1), "c": ("glow", 1), "d": ("glow", 0)})
    # ring wind-up: ice crystals rising around it (same colours as the antlers)
    pts = [(8, 52), (88, 52), (14, 76), (82, 76), (22, 30), (74, 30), (4, 66), (92, 66)]
    for x, y in pts[:p.shards]:
        r.poly([(x, y - 4), (x + 2.5, y), (x, y + 4), (x - 2.5, y)], "ice", soft=1)
    if p.chips:
        for x, y in ((10, G - 3), (86, G - 4), (20, G - 1), (76, G - 1), (30, G - 8), (66, G - 8)):
            r.poly([(x, y - 2.5), (x + 1.5, y), (x, y + 1.5), (x - 1.5, y)], "ice", soft=1)
    return r


def remains(r):
    """Purified: the elk has sunk into a heap of pale fur; the antlers lie broken on top."""
    r.ellipse(CX, G - 2, 32, 2.4, "murk", soft=2, dark=1)
    r.add(r.m_poly([(20, G), (26, G - 12), (40, G - 18), (56, G - 18), (70, G - 12), (76, G)]), "frostfur", soft=3)
    for s in (-1, 1):
        r.chain([(CX + s * 6, G - 16), (CX + s * 20, G - 22), (CX + s * 32, G - 18)], [2.4, 2.0, 1.0], "ice", soft=1)
        r.chain([(CX + s * 18, G - 21), (CX + s * 20, G - 29)], [1.6, 0.7], "ice", soft=1)
    r.stamp(CX - 2, G - 14, [".a.", "abb", ".b."], {"a": ("glow", 2), "b": ("glow", 1)})
    return r


def frames():
    f = {}
    f["idle.0"] = Pose()
    f["idle.1"] = Pose(dy=1, head=1)
    f["move.0"] = Pose(legs=(4, 0, 0, 4), shift=-2)
    f["move.1"] = Pose(legs=(0, 4, 4, 0), shift=2)
    # slam: head lowered, antlers tipped to the ground; then the antlers strike (ice chips fly)
    f["windup_slam.0"] = Pose(head=-1, ant=-1, dy=-1, mouth=1)
    f["windup_slam.1"] = Pose(head=-2, ant=-2, dy=-2, legs=(3, 0, 0, 3), mouth=2)
    f["attack_slam.0"] = Pose(head=8, ant=6, dy=2, chips=True)
    f["attack_slam.1"] = Pose(head=6, ant=4, dy=1)
    # ring: ice crystals rise around it (4, then 8); then it throws its head up as they fly
    f["windup_ring.0"] = Pose(shards=4, head=-1, mouth=1)
    f["windup_ring.1"] = Pose(shards=8, head=-2, mouth=2, dy=-1)
    f["attack_ring.0"] = Pose(head=-2, mouth=3, dy=-1, ant=-1)
    f["attack_ring.1"] = Pose(head=-2, mouth=1)
    # charge (phase 2): antlers forward, a hoof scrapes; then the lunge (head bigger, closer)
    f["windup_charge.0"] = Pose(head=4, ant=3, legs=(5, 0, 0, 0), phase2=True)
    f["windup_charge.1"] = Pose(head=6, ant=5, legs=(0, 0, 0, 5), phase2=True)
    f["attack_charge.0"] = Pose(head=8, ant=6, hs=1.12, phase2=True, legs=(2, 0, 0, 2))
    f["attack_charge.1"] = Pose(head=5, ant=4, hs=1.06, phase2=True)
    f["hurt.0"] = Pose(head=-2, ant=-1, eyes="shut", mouth=2, shift=-2)
    f["stagger.0"] = Pose(shift=-5, legs=(0, 0, 3, 6), head=3, ant=2, eyes="shut")
    f["stagger.1"] = Pose(shift=4, legs=(5, 2, 0, 0), head=4, ant=3, eyes="shut")
    f["idle2.0"] = Pose(phase2=True)
    f["idle2.1"] = Pose(phase2=True, dy=1, head=1)
    f["defeat.0"] = Pose(head=-2, ant=-1, eyes="shut", mouth=3, phase2=True, legs=(2, 0, 0, 2))
    f["defeat.1"] = Pose(collapse=1, head=5, ant=3, eyes="shut", phase2=True)
    f["defeat.2"] = Pose(collapse=3, head=8, ant=5, eyes="shut", phase2=True)
    f["defeat.3"] = Pose(collapse=4)
    return {k: draw(v) for k, v in f.items()}


SIZE = (W, H)
PATTERNS = ("slam", "ring", "charge")
