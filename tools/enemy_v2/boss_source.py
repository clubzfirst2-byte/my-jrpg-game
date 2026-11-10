"""淀みの源 (boss_source, the final boss — NOT in the code yet): a blackened, inverted 星環 (the
hero's pendant ring, its blue and gold lost to ash-grey stone and murk), seen from the front.
Inside the ring the murk pools around one great magenta eye; four sockets on the ring are the
seats of the four cores; murk tendrils reach down to the ground; stone shards circle it.
128x128 (the guide's maximum); the tendrils touch row 126, outline row 127. Front-facing only.

Frames (ENEMY_BOSS_DESIGN.md 3.5, 34): idle 2, idle2 (phase 2) 2, windup 2 x 4 patterns,
attack 2 x 4 patterns, hurt 1, transform (phase 1 -> 2) 4, defeat (purified) 6, and a separate
tendril sprite (32x48) 3. The four patterns are named after the cores' own (volley, ring, slam,
charge) and are told apart by HOW MANY SOCKETS OPEN in the wind-up (1, 2, 3, 4: big 6x6 glows in black
rims; a closed socket is a stone plug) and by the pose of the tendrils.
"""

import math

import numpy as np

from rig import Rig, _connect4
from bossparts import cracks, orb

W, H = 128, 128
G = 126
CX, CY = 64, 54
R_OUT, R_IN = 42, 32
SOCKETS = [(64, 54 - 37), (64 + 37, 54), (64, 54 + 37), (64 - 37, 54)]  # top, right, bottom, left


class Pose:
    def __init__(self, **k):
        self.dy = 0
        self.scale = 1.0  # ring closer to the camera (charge)
        self.eye = "open"  # open / narrow / wide / shut
        self.look = (0, 0)  # pupil offset
        self.open = 0  # sockets opened (0..4)
        self.phase2 = False
        self.crack = 0  # transform / defeat crack stage 0..3
        self.tendrils = "hang"  # hang / lift / slam / limp / gone
        self.tback = 0.0  # round 3: 0..1, how far the tendrils have eased back to "hang" (recovery)
        self.shards = 4  # orbiting shards
        self.orbit = 0  # shard radius change (+ out)
        self.spin = 0  # shards' angle step
        self.orbs = 0  # volley: orbs leaving the eye
        self.broken = 0  # defeat: 0 whole .. 3 fallen apart
        self.__dict__.update(k)


def tendril(r, x0, y0, x1, y1, bend, rad=4.2, **k):
    mx, my = (x0 + x1) / 2 + bend, (y0 + y1) / 2
    r.chain([(x0, y0), (mx, my), (x1, y1)], [rad, rad * 0.75, rad * 0.4], "murk", soft=2, **k)


def ring(r, cx, cy, s, p):
    ro, ri = R_OUT * s, R_IN * s
    band = r.m_ellipse(cx, cy, ro, ro) & ~r.m_ellipse(cx, cy, ri, ri)
    if p.broken >= 2:
        # the ring split into arcs: cut two gaps
        band &= ~r.m_poly([(cx - 4, cy - ro - 2), (cx + 4, cy - ro - 2), (cx + 2, cy - ri + 2), (cx - 2, cy - ri + 2)])
        band &= ~r.m_poly([(cx + ri - 3, cy + 10), (cx + ro + 3, cy + 16), (cx + ro + 3, cy + 24), (cx + ri - 3, cy + 18)])
    r.add(band, "ashring", soft=3)
    # engraved notches of the star-ring, eight around the band (the pendant's pattern, gone dull)
    for i in range(8):
        a = i * math.pi / 4 + math.pi / 8
        x0, y0 = cx + math.cos(a) * (ri + 2), cy + math.sin(a) * (ri + 2)
        x1, y1 = cx + math.cos(a) * (ro - 2), cy + math.sin(a) * (ro - 2)
        r.shade(r.m_line(x0, y0, x1, y1), lambda t: max(1, t - 1))
    # inner and outer grooves
    groove = r.m_ellipse(cx, cy, ro - 4 * s, ro - 4 * s) & ~r.m_ellipse(cx, cy, ro - 5 * s, ro - 5 * s)
    r.shade(groove, lambda t: max(1, t - 1))
    # the four sockets
    for i, (sx, sy) in enumerate(SOCKETS):
        x, y = cx + (sx - CX) * s, cy + (sy - CY) * s
        if p.broken >= 2 and i == 0:
            continue
        r.ellipse(x, y, 6.2 * s, 6.2 * s, "ashring", soft=1, dark=1)
        if i < p.open:  # an OPEN socket: a black rim around a big bright glow (6x6, reads at half size)
            r.ellipse(x, y, 4.6 * s, 4.6 * s, "murk", tone=0)
            r.stamp(round(x) - 3, round(y) - 3, ["..aa..", ".aabb.", "aabbbc", "abbbcc", ".bbcc.", "..cd.."],
                    {"a": ("glow", 4), "b": ("glow", 3), "c": ("glow", 2), "d": ("glow", 1)})
        elif p.phase2 and p.open == 0 and not p.broken:  # phase 2 idle: all four smoulder dimly
            r.ellipse(x, y, 4.0 * s, 4.0 * s, "murk", tone=0)
            r.stamp(round(x) - 1, round(y) - 1, ["ab", "bd"], {"a": ("glow", 3), "b": ("glow", 2), "d": ("glow", 1)})
        else:  # CLOSED: a domed stone plug, no hole
            r.ellipse(x, y, 3.8 * s, 3.8 * s, "ashring", soft=1)
    # cracks (phase 2 / transform / defeat)
    segs = [(cx - 30 * s, cy - 26 * s, cx - 22 * s, cy - 18 * s), (cx + 26 * s, cy + 22 * s, cx + 33 * s, cy + 29 * s),
            (cx + 8 * s, cy - 40 * s, cx + 5 * s, cy - 33 * s), (cx - 38 * s, cy + 12 * s, cx - 33 * s, cy + 6 * s),
            (cx + 36 * s, cy - 14 * s, cx + 40 * s, cy - 6 * s), (cx - 12 * s, cy + 34 * s, cx - 6 * s, cy + 40 * s)]
    n = {0: 0, 1: 2, 2: 4, 3: 6}[p.crack] if not p.phase2 else max(4, {0: 0, 1: 2, 2: 4, 3: 6}[p.crack])
    cracks(r, segs[:n])


def eye(r, cx, cy, s, p):
    # the murk pooled inside the ring
    orbm = r.ellipse(cx, cy, R_IN * s, R_IN * s, "murk", soft=4)
    # round 4: the miasma swirls round the eye -- three curved bands, 2-3 px wide, each winding in
    # from the rim toward the eye: the band is one tone off the murk under it (lighter in the
    # shade, darker in the light) with a darker lip below it. Drawn from the orb's centre, so
    # they move with it. No dots, no glow colour.
    for a0 in (0.5, 2.6, 4.7):
        pts = [(cx + math.cos(a0 + t * 1.7) * (28.5 - t * 8) * s, cy + math.sin(a0 + t * 1.7) * (28.5 - t * 8) * s) for t in (0, 0.25, 0.5, 0.75, 1)]
        band = _connect4(r.m_chain(pts, [0.9, 1.4, 1.5, 1.3, 0.9]) & orbm) & orbm
        lip = np.zeros_like(band)
        lip[1:, :] = band[:-1, :]
        r.shade(_connect4(lip & ~band & orbm) & ~band & orbm, lambda t: max(1, t - 1), on=True)
        r.shade(band, lambda t: 2 if t >= 3 else min(3, t + 1), on=True)
    if p.eye == "gone":
        return
    ry = {"open": 12, "narrow": 5, "wide": 15, "shut": 1.4}[p.eye] * s
    rx = 19 * s
    r.add(r.m_ellipse(cx, cy, rx + 2, ry + 2), "murk", tone=0)  # lids
    if p.eye == "shut":
        r.add(r.m_ellipse(cx, cy, rx, 1.2), "glow", tone=1)
        return
    r.ellipse(cx, cy, rx, ry, "glow", soft=2)
    # the pupil: a tall slit of murk, shifted by the look
    px_, py_ = cx + p.look[0], cy + p.look[1]
    r.add(r.m_ellipse(px_, py_, 4.5 * s, min(ry - 1, 10 * s)), "murk", tone=0)
    r.add(r.m_ellipse(px_, py_, 2.2 * s, min(ry - 2, 7 * s)), "murk", tone=1)
    # glints (hand-placed, upper left)
    gx, gy = round(cx - 9 * s), round(cy - ry * 0.45)
    r.stamp(gx, gy, ["ab", "b."], {"a": ("glow", 4), "b": ("glow", 3)})
    r.px([(round(px_ - 2 * s), round(py_ - 3 * s))], "glow", 4)




def draw(p):
    r = Rig(W, H)
    s = p.scale
    cx, cy = CX, CY + p.dy + (G - CY - 72) * (s - 1)
    br = p.broken
    if br >= 3:
        return remains(r, br)
    # tendrils down to the ground (behind the ring)
    roots = [(-26, 20), (-10, 30), (10, 30), (26, 20)]
    for i, (dx, dy) in enumerate(roots):
        x0, y0 = cx + dx * s, cy + dy * s
        sgn = -1 if dx < 0 else 1
        if p.tendrils == "hang":
            x1, y1, b = cx + dx * 1.7 + sgn * 6, G - 1, sgn * (3 + (p.spin + i) % 2 * 2)
        elif p.tendrils == "lift":
            x1, y1, b = cx + dx * 2.4 + sgn * 14, cy + 18 - abs(dx) * 0.4, sgn * 6
        elif p.tendrils == "slam":
            x1, y1, b = cx + dx * 2.1 + sgn * 14, G - 1, -sgn * 4
        elif p.tendrils == "aim":  # volley: raised up beside the ring like arms, tips curled in
            x1, y1, b = cx + sgn * (44 + abs(dx) * 0.4), cy - 6 - abs(dx) * 0.9, sgn * 8
        elif p.tendrils == "spread":  # ring: planted far apart, bracing
            x1, y1, b = cx + sgn * (34 + abs(dx) * 1.2), G - 1, sgn * 9
        elif p.tendrils == "tuck":  # charge: pulled up tight under the ring, ready to spring
            x1, y1, b = cx + dx * 0.9 + sgn * 3, cy + 50 - abs(dx) * 0.3, -sgn * 7
        elif p.tendrils == "limp":
            x1, y1, b = cx + dx * 1.2 + sgn * 2, G - 1, sgn * 1
        else:
            continue
        if p.tback and p.tendrils != "hang":  # easing back to hanging, over the recovery frames
            hx1, hy1, hb = cx + dx * 1.7 + sgn * 6, G - 1, sgn * (3 + (p.spin + i) % 2 * 2)
            f = p.tback
            x1, y1, b = x1 + (hx1 - x1) * f, y1 + (hy1 - y1) * f, b + (hb - b) * f
        x1 = max(8, min(W - 9, x1))
        tendril(r, x0, y0, x1, min(y1, G - 2), b, 4.6 * s, dark=1 if abs(dx) < 15 else 0)
    if p.tendrils == "slam":  # murk splashes where the tendrils strike
        for x in (12, 116, 30, 98):
            r.ellipse(x, G - 2.5, 4, 1.4, "murk", soft=1)
    eye(r, cx, cy, s, p)
    ring(r, cx, cy, s, p)
    # orbiting shards
    for i in range(p.shards):
        a = (i / max(p.shards, 1)) * 2 * math.pi + p.spin * 0.35 + 0.4
        rad = (54 + p.orbit) * s
        x, y = cx + math.cos(a) * rad, cy + math.sin(a) * rad * 0.9
        y = max(y, 7)  # a shard never reaches the top edge (1 px of clear space above its outline)
        if 4 <= x <= W - 5 and y <= G - 3:
            r.poly([(x, y - 5), (x + 3, y), (x, y + 5), (x - 3, y)], "ashring", soft=1)
    # volley: orbs leaving the eye
    for i in range(p.orbs):
        a = -math.pi / 2 + (i - (p.orbs - 1) / 2) * 0.55 + math.pi
        ox, oy = cx + math.cos(a) * 0, cy + 18 + i % 2 * 3
        orb(r, cx + (i - (p.orbs - 1) / 2) * 12, cy + 26 + abs(i - (p.orbs - 1) / 2) * -3, 4)
    return r


def remains(r, br):
    """Purified: the ring lies broken on the ground; the murk has drained; at the very end
    the stone shows a faint line of its old star pattern (no glow)."""
    r.ellipse(CX, G - 3, 46, 2.6, "murk", soft=2, dark=1 if br == 3 else 2)
    for (x0, y0, x1, y1, x2, y2) in ((20, G - 4, 34, G - 20, 54, G - 24), (70, G - 23, 92, G - 20, 108, G - 6)):
        r.chain([(x0, y0), (x1, y1), (x2, y2)], [5.5, 5.5, 5.0], "ashring", soft=2)
    r.ellipse(60, G - 6, 6, 3, "ashring", soft=1, dark=1)
    for x in (16, 112, 44, 84):
        r.poly([(x, G - 6), (x + 3, G - 2), (x, G), (x - 3, G - 2)], "ashring", soft=1)
    if br == 3:
        r.stamp(CX - 2, G - 10, [".a.", "abb", ".b."], {"a": ("glow", 2), "b": ("glow", 1)})
    return r


def tendril_frames():
    """The separate tendril sprite (32x48, feet = the root at the bottom centre): it rises out
    of the ground, sways, and lashes. For the engineer to place around the arena."""
    out = {}
    for i, (bend, tip, lean) in enumerate(((3, 6, -2), (-4, 4, 3), (2, 2, 8))):
        r = Rig(32, 48)
        r.ellipse(16, 45, 9, 1.5, "murk", soft=1, dark=1)
        r.chain([(16, 42.5), (16 + bend, 30), (16 + lean, 12 + tip), (16 + lean + bend * 0.5, 4 + tip)], [5.0, 4.0, 2.8, 1.0], "murk", soft=2)
        # a magenta bead of glow near the tip (the same in every frame)
        r.stamp(round(16 + lean) - 1, round(14 + tip) - 1, ["ab", "bc"], {"a": ("glow", 4), "b": ("glow", 3), "c": ("glow", 2)})
        r.shade(r.m_line(16 + 2, 44, 16 + bend + 2, 30), lambda t: min(3, t + 1))
        out[f"tendril.{i}"] = r
    return out


def frames_v1():  # the v1 key poses (kept for reference; v2 frames() is at the end)
    f = {}
    f["idle.0"] = Pose(spin=0)
    f["idle.1"] = Pose(spin=1, dy=1, look=(1, 0))
    f["idle2.0"] = Pose(phase2=True, spin=0, crack=3, shards=6)
    f["idle2.1"] = Pose(phase2=True, spin=1, dy=1, crack=3, shards=6, look=(-1, 0))
    # each pattern opens 1 / 2 / 3 / 4 sockets in its wind-up (big glowing holes) and has its own pose:
    # volley = tendrils reach out sideways; ring = tendrils brace far apart, shards drawn in;
    # slam = tendrils lifted, the ring rises; charge = tendrils tucked up, the ring draws back (smaller)
    f["windup_volley.0"] = Pose(eye="narrow", open=1, spin=0, tendrils="aim", dy=-2)
    f["windup_volley.1"] = Pose(eye="narrow", open=1, spin=1, orbs=3, dy=-3, tendrils="aim")
    f["attack_volley.0"] = Pose(eye="wide", open=1, spin=2, orbs=5)
    f["attack_volley.1"] = Pose(eye="open", open=1, spin=3)
    f["windup_ring.0"] = Pose(eye="narrow", open=2, shards=6, orbit=-6, spin=0, tendrils="spread", dy=3)
    f["windup_ring.1"] = Pose(eye="narrow", open=2, shards=8, orbit=-10, spin=1, dy=4, tendrils="spread")
    f["attack_ring.0"] = Pose(eye="wide", open=2, shards=8, orbit=4, spin=2)
    f["attack_ring.1"] = Pose(eye="open", open=2, shards=8, orbit=8, spin=3)
    f["windup_slam.0"] = Pose(eye="narrow", open=3, tendrils="lift", dy=-3, spin=0)
    f["windup_slam.1"] = Pose(eye="narrow", open=3, tendrils="lift", dy=-6, spin=1)
    f["attack_slam.0"] = Pose(eye="wide", open=3, tendrils="slam", dy=2, spin=2)
    f["attack_slam.1"] = Pose(eye="open", open=3, tendrils="slam", dy=1, spin=3)
    f["windup_charge.0"] = Pose(eye="narrow", open=4, scale=0.92, dy=-4, look=(0, 2), tendrils="tuck")
    f["windup_charge.1"] = Pose(eye="narrow", open=4, scale=0.86, dy=-6, look=(0, 3), shards=2, tendrils="tuck")
    f["attack_charge.0"] = Pose(eye="wide", open=4, scale=1.12, dy=4, shards=0)
    f["attack_charge.1"] = Pose(eye="open", open=4, scale=1.06, dy=2, shards=2)
    f["hurt.0"] = Pose(eye="shut", dy=-2, spin=1, tendrils="limp")
    # transform (phase 1 -> 2): the eye clenches, the ring cracks, the sockets wake
    f["transform.0"] = Pose(eye="shut", crack=1, spin=0)
    f["transform.1"] = Pose(eye="shut", crack=2, spin=1, dy=-2, tendrils="lift")
    f["transform.2"] = Pose(eye="wide", crack=3, spin=2, dy=-3, open=4, tendrils="lift", shards=6, orbit=6)
    f["transform.3"] = Pose(eye="open", crack=3, spin=3, phase2=True, shards=6)
    # defeat (purified): the eye shuts, the murk drains, the ring breaks and falls
    f["defeat.0"] = Pose(eye="wide", phase2=True, crack=3, dy=-2, tendrils="limp", shards=4, orbit=8)
    f["defeat.1"] = Pose(eye="shut", phase2=True, crack=3, dy=0, tendrils="limp", shards=2, orbit=14)
    f["defeat.2"] = Pose(eye="gone", crack=3, dy=8, tendrils="limp", shards=0, broken=2)
    f["defeat.3"] = Pose(eye="gone", crack=3, dy=20, tendrils="gone", shards=0, broken=2)
    f["defeat.4"] = Pose(broken=3)
    f["defeat.5"] = Pose(broken=4)
    out = {k: draw(v) for k, v in f.items()}
    out.update(tendril_frames())
    return out


SIZE = (W, H)
PATTERNS = ("volley", "ring", "slam", "charge")


# ------------------------------------------------------------------ v2 frames (4-8 per action)

def tendril_frames_v2():
    """The separate tendril sprite, v2: 4 frames (rise, sway left, sway right, lash)."""
    out = {}
    for i, (bend, tip, lean) in enumerate(((3, 6, -2), (-4, 4, 3), (1, 3, 6), (2, 2, 8))):
        r = Rig(32, 48)
        r.ellipse(16, 45, 9, 1.5, "murk", soft=1, dark=1)
        r.chain([(16, 42.5), (16 + bend, 30), (16 + lean, 12 + tip), (16 + lean + bend * 0.5, 4 + tip)], [5.0, 4.0, 2.8, 1.0], "murk", soft=2)
        r.stamp(round(16 + lean) - 1, round(14 + tip) - 1, ["ab", "bc"], {"a": ("glow", 4), "b": ("glow", 3), "c": ("glow", 2)})
        r.shade(r.m_line(16 + 2, 44, 16 + bend + 2, 30), lambda t: min(3, t + 1))
        out[f"tendril.{i}"] = r
    return out


def frames():
    from anim import loop, once, name, mix
    out = {}
    I = [dict(spin=0), dict(spin=0, dy=1), dict(spin=1, dy=1, look=(1, 0)), dict(spin=2, look=(1, 0))]  # round 4: 4 outlines
    name(out, "idle", loop(Pose, 4, [(i / 4, k) for i, k in enumerate(I)]), draw)
    I2 = [dict(k, phase2=True, crack=3, shards=6) for k in (dict(spin=0), dict(spin=0, dy=1), dict(spin=1, dy=1, look=(-1, 0)), dict(spin=2, look=(-1, 0)))]
    name(out, "idle2", loop(Pose, 4, [(i / 4, k) for i, k in enumerate(I2)]), draw)
    # each pattern opens 1 / 2 / 3 / 4 sockets and takes its own tendril pose; the eye narrows
    W = {
        "volley": (dict(eye="narrow", open=1, spin=0, tendrils="aim", dy=-2), dict(eye="narrow", open=1, spin=1, orbs=3, dy=-3, tendrils="aim")),
        "ring": (dict(eye="narrow", open=2, shards=6, orbit=-6, spin=0, tendrils="spread", dy=3),
                 dict(eye="narrow", open=2, shards=8, orbit=-10, spin=1, dy=4, tendrils="spread")),
        "slam": (dict(eye="narrow", open=3, tendrils="lift", dy=-3, spin=0), dict(eye="narrow", open=3, tendrils="lift", dy=-6, spin=1)),
        "charge": (dict(eye="narrow", open=4, scale=0.92, dy=-4, look=(0, 2), tendrils="tuck"),
                   dict(eye="narrow", open=4, scale=0.86, dy=-6, look=(0, 3), shards=2, tendrils="tuck")),
    }
    A = {
        "volley": (dict(eye="wide", open=1, spin=2, orbs=5), dict(eye="open", open=1, spin=3)),
        "ring": (dict(eye="wide", open=2, shards=8, orbit=4, spin=2), dict(eye="open", open=2, shards=8, orbit=8, spin=3)),
        "slam": (dict(eye="wide", open=3, tendrils="slam", dy=4, spin=2, scale=1.05), dict(eye="open", open=3, tendrils="slam", dy=1, spin=3)),
        "charge": (dict(eye="wide", open=4, scale=1.14, dy=5, shards=0, tendrils="tuck"), dict(eye="open", open=4, scale=1.06, dy=2, shards=2)),
    }
    # round 2: the strike of each pattern (the impact pose: volley -- the ring jerks back as the
    # orbs leave, tendrils flung up; ring -- it slams down wide as the shards burst; charge -- it
    # rams forward, biggest)
    S = {
        "volley": dict(eye="wide", open=1, spin=3, orbs=5, tendrils="aim", dy=-5, scale=1.04),
        "ring": dict(eye="wide", open=2, shards=8, orbit=14, spin=3, tendrils="spread", dy=5, scale=1.04),
        "charge": dict(eye="wide", open=4, scale=1.16, dy=6, shards=0, tendrils="tuck"),
    }
    A["volley"] = (dict(eye="wide", open=1, spin=2, orbs=5, tendrils="aim", dy=-3), A["volley"][1])
    A["ring"] = (dict(eye="wide", open=2, shards=8, orbit=8, spin=2, tendrils="spread", dy=3), A["ring"][1])
    for p in PATTERNS:
        w0, w1 = W[p]
        a0, a1 = A[p]
        name(out, f"windup_{p}", once(Pose, 4, [(0.0, dict(w0, dy=w0.get("dy", 0) * 0.6, spin=3)), (0.34, w0), (1.0, w1)]), draw)
        # round 2: frame 1 is the strike -- an overshoot past the release (the ring lunges, the eye
        # bulges, the tendrils whip further), then it recovers
        name(out, f"attack_{p}", once(Pose, 5, [(0.0, a0), (0.25, S.get(p, dict(mix(Pose, I[0], a0, 1.5), eye="wide")), "in"), (0.5, mix(Pose, S.get(p, a0), a1, 0.45)),
                                                (0.75, dict(mix(Pose, S.get(p, a0), I[0], 0.6), spin=(a1.get("spin", 0) + 1) % 4,
                                                            tendrils=S.get(p, a0).get("tendrils", "hang"), tback=0.45)),
                                                (1.0, dict(mix(Pose, S.get(p, a0), I[0], 0.9), tendrils=S.get(p, a0).get("tendrils", "hang"),
                                                           tback=0.85))]), draw)
    for suf, ex in (("", {}), ("2", dict(phase2=True, crack=3, shards=6))):  # hurt2: the cracks stay in phase 2
        name(out, "hurt" + suf, once(Pose, 3, [(0.0, dict(eye="shut", dy=-2, spin=1, tendrils="limp", **ex)),
                                               (0.5, dict(eye="shut", dy=-1, spin=2, tendrils="limp", **ex)),
                                               (1.0, dict(eye="narrow", dy=0, spin=3, **ex))]), draw)
    # transform (phase 1 -> 2): the eye clenches, the ring cracks, rises, the sockets wake, it settles
    T = [dict(eye="shut", crack=1, spin=0), dict(eye="shut", crack=1, spin=1, dy=-1), dict(eye="shut", crack=2, spin=1, dy=-2, tendrils="lift"),
         dict(eye="shut", crack=2, spin=2, dy=-3, tendrils="lift", shards=5, orbit=3), dict(eye="wide", crack=3, spin=2, dy=-3, open=4, tendrils="lift", shards=6, orbit=6),
         dict(eye="open", crack=3, spin=3, phase2=True, shards=6)]
    name(out, "transform", [Pose(**dict(k)) for k in T], draw)
    # defeat (round 2): the eye bulges, shuts, the ring breaks and sinks -- then melts over two
    # frames into the murk -- and only the broken ring is left
    from anim import dissolve
    D = [dict(eye="wide", phase2=True, crack=3, dy=-2, tendrils="limp", shards=4, orbit=8),
         dict(eye="shut", phase2=True, crack=3, dy=0, tendrils="limp", shards=2, orbit=14),
         dict(eye="gone", crack=3, dy=8, tendrils="limp", shards=0, broken=2)]
    name(out, "defeat", dissolve(Pose, draw, D, dict(broken=4), pools=(16, 26)), None)
    out.update(tendril_frames_v2())
    return out


PATTERNS = ("volley", "ring", "slam", "charge")
ACTIONS = (("idle", 4), ("idle2", 4)) + tuple(x for p in PATTERNS for x in ((f"windup_{p}", 4), (f"attack_{p}", 5))) + \
    (("hurt", 3), ("hurt2", 3), ("transform", 6), ("defeat", 6), ("tendril", 4))
SMOOTH = {"scale", "tback"}  # shape fields that stay smooth (the rest snap to whole pixels)
