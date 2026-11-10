"""小鬼の呪い手 (archer, the hex-caster): a hunched goblin bandit in a ragged plum hood and cloak,
grey-earth skin, big sideways ears, long nose, one tusk, yellow eyes; a bone staff topped by a
skull holding a murk orb. Right-facing (the game mirrors it), 32x56 (the hero's frame), feet on
row 54, outline on row 55. The body stands about 44 high inside the frame.

Frames (ENEMY_BOSS_DESIGN.md 2.2): idle 2, move 4, windup 2, attack 2, hurt 1, defeat 3.
Wind-up shows by SHAPE: the staff thrust forward, the orb grows. No red painted.
"""

import math

from rig import Rig

W, H = 32, 56
G = 54


class Pose:
    def __init__(self, **k):
        self.x = 0
        self.dy = 0  # body down
        self.lean = 0  # upper body forward
        self.nf = (19, G)  # near foot
        self.ff = (13, G)  # far foot
        self.staff = "hold"  # hold / raise / thrust / cast / drop / none
        self.orb = 2.2  # orb radius (grows in the wind-up)
        self.head = (0, 0)
        self.mouth = 0
        self.cloak = 0  # hem sway (+ back)
        self.fallen = 0  # defeat stage
        self.__dict__.update(k)


def leg(r, hx_, hy, fx, fy, **k):
    kx, ky = (hx_ + fx) / 2 + 1.5, (hy + fy) / 2
    r.add(r.mask_of(r.m_limb(hx_, hy, kx, ky, 2.2, 1.8), r.m_limb(kx, ky, fx, fy - 2, 1.8, 1.6)), "gobskin", **k)
    # wrapped foot (leather), toes pointing forward
    r.add(r.m_poly([(fx - 2.5, fy - 3), (fx + 1.5, fy - 3), (fx + 4, fy - 0.8), (fx + 4, fy + 1), (fx - 2.5, fy + 1)]), "leather", **k)


# hand offset from the shoulder, staff foot and staff head offsets from the hand
STAFF = {
    "hold": (6, 4, 1, 21, 1, -17),
    "raise": (3, -1, -5, 12, 3, -15),
    "thrust": (6, -1, -7, 10, 3, -7),
    "cast": (6, 1, -9, 6, 4, -6),
    "flail": (2, -3, 4, 12, -5, -11),
    "none": None,
}


def S(n):
    """A named staff pose as a tuple of floats (for easing)."""
    return tuple(float(v) for v in STAFF[n])


def staff(r, x0, y0, x1, y1, orb, behind=False):
    """Bone shaft from the foot end (x0,y0) to the head (x1,y1); skull and orb at the head."""
    r.limb(x0, y0, x1, y1, 1.0, 1.0, "wood", soft=1, dark=1 if behind else 0)
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1
    ux, uy = dx / L, dy / L
    sx, sy = x1 + ux * 1.5, y1 + uy * 1.5
    r.ellipse(sx, sy, 2.6, 2.3, "bone", soft=1)  # the skull
    r.px([(round(sx) - 1, round(sy)), (round(sx) + 1, round(sy))], "bone", 0)  # eye sockets
    ox, oy = sx + ux * (orb + 2.4), sy + uy * (orb + 2.4)
    # the murk orb: hand-shaded so it glows from the inside (same colour in every frame)
    r.ellipse(ox, oy, orb, orb, "glow", tone=2)
    r.ellipse(ox - 0.4, oy - 0.4, orb * 0.62, orb * 0.62, "glow", tone=3)
    r.px([(math.floor(ox - orb * 0.35), math.floor(oy - orb * 0.35))], "glow", 4)
    return ox, oy


def draw(p):
    r = Rig(W, H)
    if p.fallen >= 2:
        return heap(r, p)
    X, dy = p.x, p.dy
    hip = (15 + X, 41 + dy)
    sh = (16 + X + p.lean, 29 + dy + abs(p.lean) * 0.3)
    hx_, hy = sh[0] + 2 + p.lean * 0.6 + p.head[0], sh[1] - 7 + p.head[1]
    # far arm and the staff when it is held behind (hold / raise)
    leg(r, hip[0] - 2, hip[1], *p.ff, dark=1)
    # cloak: a ragged bell from the shoulders, hem cut into tatters, swaying back
    c = p.cloak
    cloak = r.m_poly([(sh[0] - 6, sh[1] - 2), (sh[0] + 5, sh[1] - 3), (sh[0] + 7, sh[1] + 6), (hip[0] + 7, hip[1] + 4),
                      (hip[0] + 4, hip[1] + 6), (hip[0] + 1, hip[1] + 4), (hip[0] - 2, hip[1] + 7 + c * 0.3),
                      (hip[0] - 5 - c, hip[1] + 4), (hip[0] - 8 - c, hip[1] + 5), (sh[0] - 9 - c * 0.5, sh[1] + 6)])
    r.add(cloak, "plum")
    # tatters: dark notches in the hem and a fold line down the back
    r.shade(r.m_line(sh[0] - 3, sh[1] + 2, hip[0] - 4 - c, hip[1] + 3), lambda t: max(1, t - 1))
    r.shade(r.m_line(sh[0] + 2, sh[1] + 3, hip[0] + 3, hip[1] + 3), lambda t: max(1, t - 1))
    leg(r, hip[0] + 1, hip[1], *p.nf)
    # rope belt with a pouch
    r.limb(hip[0] - 4, hip[1] - 4, hip[0] + 5, hip[1] - 5, 1.0, 1.0, "leather", soft=1)
    r.ellipse(hip[0] - 4, hip[1] - 2, 1.8, 2.0, "leather", soft=1)
    # head: big sideways ear back, round skull under the hood, long nose forward
    r.ellipse(hx_, hy, 5.2, 5.0, "gobskin")
    r.add(r.m_poly([(hx_ + 3, hy - 1.5), (hx_ + 9.5, hy + 2.6), (hx_ + 8.5, hy + 3.8), (hx_ + 3, hy + 3.0)]), "gobskin", soft=1)  # nose
    # hood over the crown, its point flopping back
    hood = r.m_poly([(hx_ - 5.8, hy + 2.5), (hx_ - 6, hy - 3), (hx_ - 9, hy - 9), (hx_ - 1, hy - 7.5), (hx_ + 4, hy - 6.0),
                     (hx_ + 5.6, hy - 3.6), (hx_ + 2.5, hy - 4.2), (hx_ - 1.5, hy - 3), (hx_ - 3.0, hy + 2.5)])
    r.add(hood, "plum", soft=2)
    # the big ear sticks out sideways through a slit in the hood, drooping back (the silhouette)
    et = (hx_ - 13, hy - 4.5 + p.head[1] * 0.5)
    r.add(r.m_poly([(hx_ - 3, hy - 2.2), et, (hx_ - 11, hy - 1.6), (hx_ - 3, hy + 1.5)]), "gobskin", soft=1)
    r.add(r.m_poly([(hx_ - 4, hy - 1.2), (et[0] + 3, et[1] + 1.6), (hx_ - 4, hy + 0.6)]), "gobskin", tone=1)  # inner ear
    # brow, eyes, tusk, mouth (hand-placed)
    ex, ey = round(hx_ + 1), round(hy - 2)
    r.stamp(ex, ey, ["aaa", ".bc", ".dd"], {"a": ("gobskin", 0), "b": ("eye", 3), "c": ("eye", 2), "d": ("gobskin", 1)})
    r.px([(round(hx_ + 3), round(hy + 3) + p.mouth)], "gobskin", 0)
    r.px([(round(hx_ + 2), round(hy + 3) + p.mouth), (round(hx_ + 1), round(hy + 3) + p.mouth)], "gobskin", 0)
    r.px([(round(hx_ + 2), round(hy + 4) + p.mouth)], "bone", 3)  # the tusk
    # arm and staff (v2: the staff pose is a tuple, so it can be eased between the named poses)
    hand = None
    st = STAFF[p.staff] if isinstance(p.staff, str) else p.staff
    if st:
        hdx, hdy, bdx, bdy, tdx, tdy = st
        hand = (sh[0] + hdx, sh[1] + hdy)
        staff(r, hand[0] + bdx, min(G, hand[1] + bdy), hand[0] + tdx, hand[1] + tdy, p.orb)
        r.limb(sh[0] + 1, sh[1] + 0.5, hand[0], hand[1], 2.0, 1.7, "plum", soft=1)
    if hand:
        r.ellipse(hand[0], hand[1], 1.6, 1.6, "gobskin", soft=1)
    return r


def heap(r, p):
    """Defeat 2-3: the goblin crumples; then only the cloak, staff and a murk stain are left."""
    if p.fallen == 2:
        r.ellipse(15, G - 1, 12, 2.2, "murk", soft=1)
        r.add(r.m_poly([(5, G), (9, G - 8), (16, G - 11), (23, G - 8), (26, G)]), "plum")  # slumped cloak
        r.ellipse(23, G - 9, 4.2, 3.8, "gobskin")  # head down
        r.add(r.m_poly([(18, G - 9), (12, G - 14), (14, G - 9)]), "gobskin", soft=1)  # ear, drooping
        r.add(r.m_poly([(19, G - 9), (17, G - 14), (24, G - 13), (27, G - 10)]), "plum", soft=1)  # hood
        r.px([(25, G - 9), (26, G - 9)], "gobskin", 0)  # eyes shut
        r.limb(2, G - 1, 29, G - 3, 1.0, 1.0, "wood", soft=1)  # staff on the ground
        r.ellipse(30, G - 3.5, 2.2, 2.0, "bone", soft=1)
    else:
        r.ellipse(15, G - 0.5, 13, 1.8, "murk", soft=1)
        r.add(r.m_poly([(6, G), (10, G - 4), (17, G - 5), (22, G - 3), (25, G)]), "plum")  # empty cloak
        r.limb(2, G - 1, 29, G - 2, 1.0, 1.0, "wood", soft=1)
        r.ellipse(30, G - 2.5, 2.2, 2.0, "bone", soft=1)
        r.px([(12, G - 7), (19, G - 8)], "murk", 2)  # the last wisps
    return r


def frames_v1():  # the v1 key poses (kept for reference; v2 frames() is at the end)
    f = {}
    f["idle.0"] = Pose()
    f["idle.1"] = Pose(dy=1, head=(0, 1), cloak=1, orb=2.6)
    # move (4): a shuffling, hunched walk; the staff rides along
    f["move.0"] = Pose(nf=(22, G), ff=(10, G), dy=0, cloak=1)
    f["move.1"] = Pose(nf=(18, G - 2), ff=(14, G), dy=-1, cloak=2, lean=1)
    f["move.2"] = Pose(nf=(11, G), ff=(21, G), dy=0, cloak=1)
    f["move.3"] = Pose(nf=(15, G), ff=(17, G - 2), dy=-1, cloak=0, lean=1)
    # windup: draws the staff back and up (orb swells), then thrusts it forward (orb biggest)
    f["windup.0"] = Pose(staff="raise", orb=3.2, lean=-1, nf=(21, G), ff=(11, G), mouth=1, cloak=1)
    f["windup.1"] = Pose(staff="thrust", orb=4.0, x=-3, lean=2, nf=(19, G), ff=(8, G), mouth=1, head=(1, 0))
    # attack: the orb leaves (small spark left), body follows through, then recovers
    f["attack.0"] = Pose(staff="cast", orb=1.4, x=-2, lean=3, nf=(21, G), ff=(8, G), dy=1, mouth=1, cloak=2)
    f["attack.1"] = Pose(staff="hold", orb=1.6, lean=1, nf=(21, G), ff=(11, G), cloak=1)
    f["hurt.0"] = Pose(staff="flail", orb=2.0, x=-2, lean=-2, head=(-1, -1), mouth=1, nf=(17, G), ff=(12, G - 1), cloak=-1)
    f["defeat.0"] = Pose(staff="flail", orb=1.4, dy=4, lean=-1, head=(0, 2), nf=(19, G), ff=(12, G), cloak=1)
    f["defeat.1"] = Pose(fallen=2)
    f["defeat.2"] = Pose(fallen=3)
    return {k: draw(v) for k, v in f.items()}


ACTIONS = (("idle", 2), ("move", 4), ("windup", 2), ("attack", 2), ("hurt", 1), ("defeat", 3))
SIZE = (W, H)


# ------------------------------------------------------------------ v2 frames (4-8 per action)

def frames():
    """v2: idle 4, move 8, windup 4, attack 5, hurt 3, defeat 6 (key poses eased in between)."""
    from anim import loop, once, name
    hold = dict(staff=S("hold"), nf=(19.0, G), ff=(13.0, G))
    # idle: the hunched breath, the hood point and cloak hem lag behind, the orb pulses
    name(out := {}, "idle", loop(Pose, 4, [
        (0.0, dict(hold, orb=2.2)), (0.25, dict(hold, dy=1, orb=2.2)), (0.5, dict(hold, dy=1, orb=2.7)), (0.75, dict(hold, orb=2.7)),
    ]), draw)
    # move: a shuffling, hunched walk, the body bobs on the passing steps, the hem trails
    name(out, "move", loop(Pose, 8, [
        (0.0, dict(hold, nf=(22.0, G), ff=(10.0, G), dy=0.0, cloak=1.0, lean=0.0)),
        (0.25, dict(hold, nf=(18.0, G - 2.0), ff=(14.0, G), dy=-1.0, cloak=2.0, lean=1.0)),
        (0.5, dict(hold, nf=(11.0, G), ff=(21.0, G), dy=0.0, cloak=1.0, lean=0.0)),
        (0.75, dict(hold, nf=(15.0, G), ff=(17.0, G - 2.0), dy=-1.0, cloak=0.0, lean=1.0)),
    ]), draw)
    # windup: rears back (anticipation), draws the staff up and back while the orb swells, then
    # thrusts it forward; the last frame is the held thrust with the orb at its biggest
    name(out, "windup", once(Pose, 4, [
        (0.0, dict(staff=S("hold"), orb=2.8, lean=-1.0, dy=0.5, nf=(20.0, G), ff=(12.0, G), mouth=0, cloak=0.0)),
        (0.4, dict(staff=S("raise"), orb=3.2, lean=-2.0, x=1, nf=(21.0, G), ff=(11.0, G), mouth=1, cloak=1.0)),
        (0.67, dict(staff=(5.0, -1.0, -6.0, 11.0, 3.0, -10.0), orb=3.7, x=-1, lean=1.0, nf=(20.0, G), ff=(9.0, G), mouth=1, head=(1.0, 0.0), cloak=1.0)),
        (1.0, dict(staff=S("thrust"), orb=4.0, x=-3, lean=2.0, nf=(19.0, G), ff=(8.0, G), mouth=1, head=(1.0, 0.0), cloak=1.0), "in"),
    ]), draw)
    # attack: the release (orb gone, staff whipped low), the follow-through, the settle, back to hold
    name(out, "attack", once(Pose, 5, [
        (0.0, dict(staff=S("cast"), orb=1.4, x=-2, lean=3.0, nf=(21.0, G), ff=(8.0, G), dy=1.0, mouth=1, cloak=2.0)),
        (0.3, dict(staff=S("cast"), orb=1.2, x=-2, lean=3.5, nf=(21.0, G), ff=(8.0, G), dy=1.5, mouth=1, cloak=3.0)),
        (0.65, dict(staff=S("thrust"), orb=1.5, x=-1, lean=1.5, nf=(21.0, G), ff=(10.0, G), dy=0.5, mouth=0, cloak=2.0)),
        (1.0, dict(staff=S("hold"), orb=1.8, lean=0.5, nf=(20.0, G), ff=(12.0, G), cloak=1.0)),
    ]), draw)
    # hurt: knocked back, the staff flails, then recovers
    name(out, "hurt", once(Pose, 3, [
        (0.0, dict(staff=S("flail"), orb=2.0, x=-2, lean=-2.0, head=(-1.0, -1.0), mouth=1, nf=(17.0, G), ff=(12.0, G - 1.0), cloak=-1.0)),
        (0.5, dict(staff=S("flail"), orb=2.0, x=-3, lean=-1.0, head=(-1.0, 0.0), mouth=1, nf=(16.0, G), ff=(11.0, G), cloak=0.0, dy=1.0)),
        (1.0, dict(staff=S("hold"), orb=2.1, x=-1, lean=0.0, nf=(18.0, G), ff=(12.0, G), cloak=0.5)),
    ]), draw)
    # defeat: the hit, the knees give, sinking, the slumped heap, the empty cloak
    d = once(Pose, 4, [
        (0.0, dict(staff=S("flail"), orb=1.8, x=-2, lean=-3.0, head=(-1.0, -2.0), mouth=1, nf=(17.0, G), ff=(12.0, G), cloak=-1.0)),
        (0.4, dict(staff=S("flail"), orb=1.4, dy=2.0, lean=-1.0, head=(0.0, 1.0), nf=(18.0, G), ff=(12.0, G), cloak=1.0)),
        (1.0, dict(staff=S("flail"), orb=1.0, dy=6.0, lean=1.0, head=(0.0, 3.0), nf=(19.0, G), ff=(12.0, G), cloak=2.0)),
    ])
    # round 2: the slumped goblin melts into the murk over two frames, then only the cloak is left
    from anim import dissolve_from
    name(out, "defeat", dissolve_from(draw, [d[0], d[2], d[3]], Pose(fallen=3), pools=(7, 11)), None)
    return out


ACTIONS = (("idle", 4), ("move", 8), ("windup", 4), ("attack", 5), ("hurt", 3), ("defeat", 6))
SMOOTH = {"orb"}  # shape fields that stay smooth (the rest snap to whole pixels)
