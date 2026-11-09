"""澱だまり (slime, NEW): a mound of murk jelly with a magenta crystal core showing through and two
glowing eyes; murk seeps onto the ground around it. Right-facing (mirrored by the game), 32x28,
base on row 26, outline on row 27. Made only of the murk and glow ramps.

Frames (ENEMY_BOSS_DESIGN.md 2.3): idle 2, move (hop) 4, windup 2, attack (body slam) 2, hurt 1,
defeat 3 (melts away). Wind-up shows by SHAPE: squashed flat and wide before the hop.
"""

from rig import Rig

W, H = 32, 28
G = 26


class Pose:
    def __init__(self, **k):
        self.x = 0
        self.lift = 0  # off the ground (hop)
        self.rx = 11  # half width
        self.ry = 9  # half height
        self.lean = 0  # top leans forward (+)
        self.eyes = "open"  # open / shut / wide
        self.melt = 0  # defeat 0..3
        self.puddle = 1  # seep under it
        self.__dict__.update(k)


def draw(p):
    r = Rig(W, H)
    cx = 16 + p.x
    base = G - p.lift
    if p.melt >= 3:
        r.ellipse(16, G - 0.5, 13, 2.0, "murk", soft=1)
        r.ellipse(14, G - 1.5, 5, 1.6, "murk", soft=1)
        r.poly([(15, G - 1), (16.5, G - 5), (18, G - 1)], "glow", soft=1)  # the dimmed core left behind
        r.px([(9, G - 4), (23, G - 3)], "murk", 3)
        return r
    if p.puddle and p.lift == 0:
        r.ellipse(cx, G - 0.5, p.rx + 3, 1.8, "murk", soft=1, dark=1)
    # the body: a dome (wider at the bottom), the top leaning with the motion
    rx, ry = p.rx, p.ry
    top = base - 2 * ry
    body = r.m_poly([(cx - rx, base), (cx - rx - 1, base - 2), (cx - rx + 1, base - ry), (cx - rx * 0.6 + p.lean, top + ry * 0.35),
                     (cx + p.lean, top), (cx + rx * 0.6 + p.lean, top + ry * 0.35), (cx + rx - 1, base - ry),
                     (cx + rx + 1, base - 2), (cx + rx, base)])
    body |= r.m_ellipse(cx + p.lean * 0.5, base - ry, rx, ry)
    if p.melt:
        body &= ~r.m_ellipse(cx + 2, top - 3, rx * 0.9, ry * (0.5 + 0.45 * p.melt))
        body |= r.m_ellipse(cx, base - 1, rx + 2 * p.melt, 2.4)
    r.add(body, "murk", soft=3)
    # the core seen through the jelly: a crystal, hand-shaded so it glows from the inside
    ky = base - ry * 0.55 + (1 if p.melt else 0)
    kx = cx + p.lean * 0.4 + 1
    r.stamp(round(kx) - 2, round(ky) - 3, [
        "..a..",
        ".abb.",
        "abccb",
        ".bcb.",
        "..b..",
    ] if p.melt < 2 else ["..a..", ".bcb.", "..b.."], {"a": ("glow", 3), "b": ("glow", 2), "c": ("glow", 1)})
    # a shine on the jelly (top left) and inner swirls
    sx, sy = round(cx - rx * 0.5 + p.lean * 0.6), round(top + ry * 0.45)
    if p.melt < 2:
        r.px([(sx, sy), (sx + 1, sy - 1), (sx, sy + 1)], "murk", 4)
    r.shade(r.m_line(cx - rx + 3, base - 3, cx - 2, base - 2), lambda t: max(1, t - 1))
    # eyes: two glowing slits above the core
    ey = round(top + ry * 0.45) + (1 if p.melt else 0)
    ex = round(cx + p.lean * 0.8 + 2)
    if p.eyes == "open":
        r.stamp(ex - 4, ey, ["ab...ab", "bb...bb", "c.....c"], {"a": ("glow", 4), "b": ("glow", 3), "c": ("murk", 0)})
    elif p.eyes == "wide":
        r.stamp(ex - 4, ey - 1, ["ab...ab", "bb...bb", "bb...bb"], {"a": ("glow", 4), "b": ("glow", 3)})
    elif p.eyes == "shut":
        r.stamp(ex - 4, ey + 1, ["bb...bb"], {"b": ("glow", 1)})
    # drips on the sides
    if p.lift == 0:
        r.px([(round(cx - rx) + 1, base + 0), (round(cx + rx) - 2, base)], "murk", 1)
    return r


def frames():
    f = {}
    f["idle.0"] = Pose()
    f["idle.1"] = Pose(rx=11.5, ry=8.5)  # wobble: a little wider and lower
    # move: squash -> stretch upward off the ground -> in the air leaning forward -> land wide
    f["move.0"] = Pose(rx=12.5, ry=7.5)
    f["move.1"] = Pose(rx=9, ry=10.5, lift=2, lean=1, puddle=0)
    f["move.2"] = Pose(rx=10, ry=9.5, lift=4, lean=2, puddle=0)
    f["move.3"] = Pose(rx=12, ry=8, lift=0, lean=1)
    # windup: squashed flat and wide (two steps), eyes narrow
    f["windup.0"] = Pose(rx=13, ry=6.5, eyes="open")
    f["windup.1"] = Pose(rx=13.5, ry=5.5, eyes="wide", x=-1)
    # attack: launched forward, stretched; then the slam, flattened against the target
    f["attack.0"] = Pose(rx=9, ry=10.5, lift=3, lean=3, x=2, puddle=0, eyes="wide")
    f["attack.1"] = Pose(rx=12.5, ry=7, lean=2, x=1, eyes="wide")
    f["hurt.0"] = Pose(rx=10, ry=9.5, lean=-3, x=-2, eyes="shut")
    f["defeat.0"] = Pose(melt=1, eyes="shut", rx=12)
    f["defeat.1"] = Pose(melt=2, eyes="shut", rx=12.5, ry=6)
    f["defeat.2"] = Pose(melt=3)
    return {k: draw(v) for k, v in f.items()}


ACTIONS = (("idle", 2), ("move", 4), ("windup", 2), ("attack", 2), ("hurt", 1), ("defeat", 3))
SIZE = (W, H)
