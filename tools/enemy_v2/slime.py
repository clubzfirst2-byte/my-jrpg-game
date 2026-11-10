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


# round 4: a bubble in the jelly: a round 3x3 (or 2x2) patch of the jelly's own light tone, its
# lower right one step darker -- a cluster with a form, not a dot
BUB_LEG = {"3": ("murk", 3), "2": ("murk", 2)}
BUB4 = [".33.", "3332", "3322", ".22."]  # round 5: round (corners cut)
BUB3 = [".3.", "332", ".2."]
BUB2 = ["33", "32"]

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
    # round 4: three bubbles at fixed places in the dark lower jelly -- they scale with the body
    # (squash and stretch), they never jump from frame to frame
    if p.melt < 2:
        for fx_, fy_, bub in ((0.5, 0.05, BUB4), (-0.55, 0.4, BUB3), (0.62, 0.62, BUB2)):
            r.stamp(int(round(cx + fx_ * rx)) - 1, int(round(base - ry + fy_ * ry)) - 1, bub, BUB_LEG)
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
        r.px([(sx, sy), (sx + 1, sy - 1), (sx, sy + 1)], "murk", 3)  # round 2: the shine in tone 3 (6 tones max)
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


def frames_v1():  # the v1 key poses (kept for reference; v2 frames() is at the end)
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


# ------------------------------------------------------------------ v2 frames (4-8 per action)

def frames():
    """v2: idle 4, move 8, windup 4, attack 5, hurt 3, defeat 6 -- squash and stretch throughout
    (the jelly keeps its volume: wider when it is lower, narrower when it is taller)."""
    from anim import loop, once, name
    out = {}
    name(out, "idle", loop(Pose, 4, [
        (0.0, dict(rx=11.0, ry=9.0)), (0.25, dict(rx=11.5, ry=8.5)), (0.5, dict(rx=11.5, ry=8.5, lean=2)), (0.75, dict(rx=11.0, ry=9.0, lean=2, eyes="shut")),
    ]), draw)
    # move: squash (gather), stretch up off the ground, the arc leaning forward, the fall, the
    # landing squash, the rebound
    name(out, "move", loop(Pose, 8, [
        (0.0, dict(rx=12.5, ry=7.5, lift=0.0, lean=0.0, puddle=1)),
        (0.125, dict(rx=9.0, ry=10.8, lift=1.0, lean=1.0, puddle=0)),
        (0.375, dict(rx=9.6, ry=10.0, lift=4.0, lean=2.0, puddle=0), "out"),
        (0.5, dict(rx=10.8, ry=8.8, lift=3.4, lean=3.0, puddle=0)),  # round 5: over the top -- rounder, tipping forward
        (0.625, dict(rx=10.4, ry=9.6, lift=2.0, lean=1.5, puddle=0), "in"),
        (0.75, dict(rx=13.0, ry=7.0, lift=0.0, lean=0.5, puddle=1), "in"),
        (0.875, dict(rx=11.0, ry=9.2, lift=0.0, lean=0.0, puddle=1)),
    ]), draw)
    # windup: a small rise (anticipation), then flattens wide, eyes widening
    name(out, "windup", once(Pose, 4, [
        (0.0, dict(rx=10.4, ry=9.8, eyes="open")),
        (0.34, dict(rx=12.5, ry=7.0, eyes="open")),
        (1.0, dict(rx=13.8, ry=5.4, eyes="wide", x=-1)),
    ]), draw)
    # attack: launched forward and stretched, the hang at the top, the slam (flattened against
    # the target), the rebound, the settle
    name(out, "attack", once(Pose, 5, [
        (0.0, dict(rx=9.4, ry=10.6, lift=2.4, lean=3.0, x=2, puddle=0, eyes="wide")),
        (0.25, dict(rx=9.9, ry=10.0, lift=3.4, lean=3.0, x=3, puddle=0, eyes="wide"), "out"),
        (0.5, dict(rx=13.5, ry=6.2, lift=0.0, lean=2.0, x=2, puddle=1, eyes="wide"), "in"),
        (0.75, dict(rx=10.2, ry=9.8, lift=0.0, lean=-1.0, x=1, puddle=1, eyes="open")),
        (1.0, dict(rx=11.4, ry=8.7, lift=0.0, lean=0.0, x=0, puddle=1, eyes="open")),
    ]), draw)
    name(out, "hurt", once(Pose, 3, [
        (0.0, dict(rx=10.0, ry=9.6, lean=-3.0, x=-2, eyes="shut")),
        (0.5, dict(rx=12.6, ry=7.6, lean=-1.0, x=-2, eyes="shut")),
        (1.0, dict(rx=11.0, ry=9.0, lean=0.0, x=-1, eyes="open")),
    ]), draw)
    # round 2: it sags, its top rounds off, then it melts flat into its own pool; the dimmed core last
    from anim import dissolve_from
    d = once(Pose, 3, [
        (0.0, dict(rx=12.6, ry=7.4, eyes="shut", melt=0.0)),
        (0.5, dict(rx=13.0, ry=6.8, eyes="shut", melt=0.0)),
        (1.0, dict(rx=13.4, ry=5.8, eyes="shut", melt=0.0, puddle=1)),
    ])
    name(out, "defeat", dissolve_from(draw, d, Pose(melt=3), pools=(10, 13)), None)
    return out


ACTIONS = (("idle", 4), ("move", 8), ("windup", 4), ("attack", 5), ("hurt", 3), ("defeat", 6))
SMOOTH = {"rx", "ry", "melt"}  # shape fields that stay smooth (the rest snap to whole pixels)
