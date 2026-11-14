"""朽ち根のヌシ (boss_root) at density 4: 192 x 160, the feet on the bottom rows, seen from the front.

The same design, keys, frame counts and key poses as v2 (tools/enemy_v2/boss_root.py at d900394; the
pose numbers here are v2's x 2, in texels). Nothing is drawn by a formula: every part is a hand-drawn
pixel map (root_body.py, root_parts.py) and a frame only PLACES the parts at whole-texel offsets, back
to front. A part is the same picture in every frame; what changes between frames is where the parts
are (the body's bob, the head's drop, the legs' lift and spread, the spikes' bristle and fan, the chin's
drop) and which of a few hand-drawn states is used (eye open / shut, core caged / bared, leg down /
out / up, the pools of the purification).
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(HERE, "..", "enemy_v3"))
import palette  # noqa: E402
import root_body as B  # noqa: E402
import root_parts as R  # noqa: E402
from bossanim import actions, boss_actions  # noqa: E402
from pixmap import Frame, Legend, part  # noqa: E402

W, H = 192, 160
G = 158  # the last row the feet stand on (the outline is row 159)
LEG = Legend(palette.GROUPS)
M_ = {m: i for i, m in enumerate(LEG.mats)}

P = {}  # name -> Part (left / whole), name + "~" -> its mirror
for _n in B.ORDER:
    P[_n] = part(getattr(B, _n), LEG, _n, cols=_n in B.COLS)
    P[_n + "~"] = P[_n].mirror()
for _n in R.PLACE:
    P[_n] = part(getattr(R, _n), LEG, _n, cols=_n in R.COLS)
for _n in ("FUNGUS_L", "FUNGUS_M", "FUNGUS_S", "ORB", "CHIP_A", "CHIP_B", "LEG_OUT", "LEG_UP", "KNOT_A", "SCAR_A", "SCAR_B", "FOLD_A", "FOLD_B"):
    if hasattr(R, _n):
        P[_n] = part(getattr(R, _n), LEG, _n, cols=_n in R.COLS)
RELIGHT = {"LEG", "VINE", "VINE2", "HIND", "SPK_1", "SPK_2", "SPK_3", "RIB2"}  # upright limbs typed in rows
for _n in list(P):
    if _n in R.HALF or _n in ("LEG_OUT", "LEG_UP"):
        P[_n + "~"] = P[_n].mirror(relight=_n in RELIGHT)
P["V1~"] = P["V1"].mirror(relight=True)
for _n in ("EYE_OPEN", "EYE_SHUT"):
    P[_n + "~"] = P[_n].mirror(darker=False, band=False)  # a light does not get a shadow side
# the core gone dark (the purification): the same crystal, its lights put out
P["CRYSTAL2_DIM"] = P["CRYSTAL2"].swap({}, tones=(0, 1, 1, 1, 1, 1, 3))
PLACE = dict(B.PLACE)
PLACE.update(R.PLACE)
# the murk the body turns into when it is purified: the same pictures in the murk ramp
_TO_MURK = {M_[m]: M_["murk"] for m in ("rotwood", "rotwood_d", "rotwood_p", "fungus", "bone")}
MURK = {n: p.swap(_TO_MURK) for n, p in P.items()}


class Pose:
    def __init__(self, **k):
        self.dy = 0  # whole body down
        self.lift = 0  # back / shoulders up (-) (charge wind-up, rearing)
        self.head = 0  # head down (+)
        self.hs = 1.0  # v2: the head's scale. v3: the head comes forward = further down and the tusks out
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
        self.melt = 0  # 0 none, 1 / 2 the two frames of the purification (drawn in murk, sinking)
        self.__dict__.update(k)


def _both(f, parts, name, x, y, cx=96, **kw):
    """A HALF map and its mirror about the frame's centre line moved by cx - 96."""
    p = parts[name]
    f.put(p, x, y, **kw)
    f.put(parts[name + "~"], 2 * cx - x - p.w, y, **kw)


def draw(p):
    if p.collapse >= 4:
        return remains()
    if int(p.melt) == 2:
        return mound()
    f = Frame(W, H, LEG, palette.RAMPS)
    p.melt = int(p.melt)
    parts = MURK if p.melt else P
    sink = (0, 34, 62)[p.melt]
    clip = G + 2 if p.melt else None
    c = p.collapse
    dy = int(round(p.dy + c * 8)) + sink
    bx = int(round(p.shift))  # the body's sideways offset
    by = dy + int(round(p.lift))  # the body's vertical offset
    cx = 96 + bx
    kw = dict(clip_y=clip)

    def at(name, ox=0, oy=0):
        x, y = PLACE[name]
        return x + ox, y + oy

    # hind legs: they stand on the ground (seen between the front legs)
    if c < 3 and not p.melt:
        _both(f, parts, "HIND", *at("HIND"))
        hx0, hy0 = at("HIND")
        f.put(P["KNOT_A"], 192 - hx0 - 14, hy0 + 22)  # the right hind leg's own knot, higher than the knee's
    # front legs (behind the body unless they are raised)
    def front_legs():
        for s, lf in ((-1, p.legs[0]), (1, p.legs[1])):
            lf = int(round(lf))
            sp = min(int(round(p.spread * 0.5)), 6)  # the toes stay inside the frame
            name = "LEG"
            x, y = at("LEG", -sp, -lf + int(round(dy * 0.5)) + sink // 2)
            if p.raise_ >= 0.75:
                name = "LEG_UP"
                x, y = R.PLACE_UP[0] + bx, R.PLACE_UP[1] + by
            elif p.raise_ >= 0.3:
                name = "LEG_OUT"
                x, y = R.PLACE_OUT[0] + bx, R.PLACE_OUT[1] + by
            q = parts[name]
            if s < 0:
                f.put(q, x, y, **kw)
            else:
                f.put(parts[name + "~"], 192 - x - q.w + (2 * bx if name != "LEG" else 0), y, **kw)
            if name == "LEG":  # the thin root winding down its outer side
                v = parts["VINE"]
                if s < 0:
                    f.put(v, x, y + 8, **kw)
                else:
                    f.put(parts["VINE~"], 192 - x - v.w, y + 8, **kw)
                v = parts["VINE2"]  # and the wet root down the inside of its lower half
                if s < 0:
                    f.put(v, x, y + 38, **kw)
                else:
                    f.put(parts["VINE2~"], 192 - x - v.w, y + 38, **kw)
    if p.raise_ < 0.3:
        front_legs()
    # back spikes: they rise (bristle) and move apart (fan) as whole pictures
    sk = int(round(p.spikes))
    rise = max(by - sk, 1 - PLACE["SPK_C"][1])  # the middle spike's tip stops at row 1; the others keep their step below it
    for i, n in ((3, "SPK_3"), (2, "SPK_2"), (1, "SPK_1")):
        fan = min(int(round(p.fan * i * 0.4)), 6)  # the outer spike stays rooted in the back
        x, y = at(n, bx - fan, rise)
        f.put(parts[n], x, y, **kw)
        f.put(parts[n + "~"], 2 * cx - x - parts[n].w, y, **kw)
    f.put(parts["SPK_C"], *at("SPK_C", bx, rise), **kw)
    # the body
    for n in B.ORDER:
        _both(f, parts, n, *at(n, bx, by), cx=cx, **kw)
    _both(f, parts, "SHOULDER", *at("SHOULDER", bx, by), cx=cx, **kw)
    for n, x, y in R.RIGHT_MARKS:  # the image-right half's own knots and splits
        f.put(parts[n], x + bx, y + by, **kw)
    for n, x, y in R.FUNGI:
        f.put(parts[n], x + bx, y + by, **kw)
    f.put(parts["NECK"], *at("NECK", bx, by), **kw)
    if p.raise_ >= 0.3:
        front_legs()
    # the core
    bared = p.phase2 or c
    if p.melt:  # the bared socket stays (already murk), its crystal gone dark
        f.put(P["SOCKET2"], *at("SOCKET2", bx, by), **kw)
        f.put(P["CRYSTAL2_DIM"], *at("CRYSTAL2", bx, by), **kw)
        _both(f, parts, "RIB2", *at("RIB2", bx, by), cx=cx, **kw)
    if not p.melt:
        if bared:
            f.put(P["SOCKET2"], *at("SOCKET2", bx, by))
            f.put(P["CRYSTAL2_DIM" if c >= 2 else "CRYSTAL2"], *at("CRYSTAL2", bx, by))
            _both(f, P, "RIB2", *at("RIB2", bx, by), cx=cx)
            f.put(P["CRACK_A"], *at("CRACK_A", bx, by))
            f.put(P["CRACK_B"], *at("CRACK_B", bx, by))
        else:
            f.put(P["SOCKET"], *at("SOCKET", bx, by))
            f.put(P["CRYSTAL"], *at("CRYSTAL", bx, by))
            f.put(P["RIBS"], *at("RIBS", bx, by))
    # the head: pushed forward and low. v2 scaled it up when it came forward (hs); here it comes
    # further down and the tusks move apart instead (the same pictures)
    fwd = int(round((p.hs - 1.0) * 30))
    hy = dy + int(round(p.head)) + fwd
    if p.melt:
        hy = min(hy, 24)  # the head and the tusks rest on the ground while the body sinks
    else:
        hy = min(hy, 16)  # the chin stays above the ground (v2: the head's centre at most 7 px down)
    hx = int(round(bx * 0.3))
    hcx = 96 + hx
    jaw = int(round(p.jaw * 0.75))
    if not p.melt:
        _both(f, parts, "MOUTH", *at("MOUTH", hx, hy), cx=hcx)
        _both(f, parts, "JAW", *at("JAW", hx, hy + jaw), cx=hcx)
    if c < 2 and not p.melt:
        x, y = at("BEARD", hx, hy + jaw)
        f.put(parts["BEARD"], x, min(y, G - parts["BEARD"].h + 1))
    _both(f, parts, "HEAD", *at("HEAD", hx, hy), cx=hcx, **kw)
    tw = fwd // 2
    _both(f, P, "TUSK", *at("TUSK", hx - tw, hy), cx=hcx, **kw)  # the tusks stay bone while the body turns to murk
    if not p.melt:
        e = "EYE_OPEN" if p.eyes == "open" else "EYE_SHUT"
        _both(f, P, e, *at(e, hx, hy), cx=hcx)
    # volley: orbs lined up in front of the core
    n = int(p.orbs)
    for i in range(n):
        k = i - (n - 1) / 2
        f.put(P["ORB"], int(round(cx + k * 20 - 7)), int(round(62 + by + 8 - abs(k) * 6 - 7)))
    if p.chips:
        for q, x, y in (("CHIP_A", 40, G - 9), ("CHIP_B", 148, G - 8), ("CHIP_B", 2, G - 22), ("CHIP_A", 180, G - 26),
                        ("CHIP_A", 76, G - 7), ("CHIP_B", 110, G - 6)):
            f.put(P[q], x, y)
    if p.melt:
        n = "POOL_A" if p.melt == 1 else "POOL_B"
        _both(f, P, n, PLACE[n][0], PLACE[n][1] + (1 if p.melt == 1 else 0))
    return f


def mound():
    """The purification, frame 4: the hand-drawn mound of murk (MELT), the tips of the tusks still
    bone, the dark crystal half sunk, the wide pool in front."""
    f = Frame(W, H, LEG, palette.RAMPS)
    _both(f, P, "TUSK", 49, 119, clip_y=G - 6)
    _both(f, P, "MELT", *PLACE["MELT"])
    f.put(P["CRYSTAL2_DIM"], 85, 125, clip_y=145)
    for n, x, y in (("FOLD_A", 40, 136), ("FOLD_B", 62, 128), ("FOLD_A", 70, 142), ("FOLD_B", 30, 144), ("FOLD_B", 112, 126),
                    ("FOLD_A", 124, 134), ("FOLD_B", 146, 140), ("FOLD_A", 104, 143), ("FUNGUS_S", 54, 138), ("FUNGUS_M", 132, 142),
                    ("CHIP_B", 86, 146), ("FOLD_B", 152, 146), ("CHIP_B", 44, 146), ("FOLD_B", 60, 122), ("FOLD_A", 90, 121),
                    ("FOLD_B", 124, 122), ("FOLD_B", 84, 132), ("FOLD_A", 114, 130), ("FOLD_B", 66, 137), ("FOLD_B", 116, 139),
                    ("FOLD_B", 148, 136), ("FOLD_A", 56, 147), ("FOLD_B", 118, 147), ("FUNGUS_S", 98, 126), ("CHIP_B", 158, 139),
                    ("FOLD_B", 100, 134), ("CHIP_B", 72, 130)):
        f.put(P[n], x, y)
    _both(f, P, "POOL_B", *PLACE["POOL_B"])
    return f


def remains():
    """The last frame of the purification: a heap of dead roots (the arch of the back and the belly
    root on the ground), stubs of the spikes, the two tusks, the core gone dark, a thin pool."""
    f = Frame(W, H, LEG, palette.RAMPS)
    kw = dict(clip_y=G)  # v2's remains end two texels above the frame's last row
    for n, dx, y in (("SPK_2", 14, 106), ("SPK_1", 6, 102)):
        x = PLACE[n][0] + dx
        f.put(P[n], x, y, **kw)
        f.put(P[n + "~"], 192 - x - P[n].w, y + 3, **kw)
    _both(f, P, "S5", 50, 134, **kw)
    _both(f, P, "S1", 44, 124, **kw)
    f.put(P["CRYSTAL2_DIM"], 85, 116)
    _both(f, P, "TUSK", 53, 119, **kw)
    f.put(P["FUNGUS_M"], 122, 132)
    f.put(P["FUNGUS_S"], 60, 138)
    _both(f, P, "POOL_A", 0, 149)
    return f


SIZE = (W, H)
PATTERNS = ("charge", "slam", "volley")
SMOOTH = {"raise_", "hs"}  # fields that pick a state or scale a move; the rest snap to whole texels


PHASE2 = ("volley",)


def frames():
    P2 = dict(phase2=True)
    # v2's key poses, the lengths x 2 (texels)
    K = {
        "idle": [{}, dict(dy=2), dict(dy=2, head=2), dict(head=2, jaw=2)],
        "move": [dict(legs=(10, 0), shift=-4), dict(legs=(4, 4), dy=-2, head=-2), dict(legs=(0, 10), shift=4),
                 dict(legs=(2, 2), dy=-1, head=2)],
        "windup_charge": (dict(lift=-7, head=20, hs=1.04, spikes=8, fan=5, spread=10),
                          dict(lift=-8, head=24, hs=1.1, spikes=10, fan=6, spread=12, jaw=2)),
        "attack_charge": (dict(lift=-6, head=24, hs=1.2, spread=12, jaw=6, legs=(6, 6), fan=4, spikes=6),
                          dict(lift=-2, head=10, hs=1.1, spread=4, jaw=2, fan=1),
                          dict(lift=-7, head=26, hs=1.26, spread=16, jaw=6, legs=(8, 8), fan=5, spikes=8, dy=4)),
        "windup_slam": (dict(dy=-10, lift=-2, head=-10, raise_=0.55, spread=-4, jaw=2),
                        dict(dy=-16, lift=-3, head=-16, raise_=0.9, spread=-6, jaw=4)),
        "attack_slam": (dict(dy=8, head=10, spread=14, jaw=6, chips=True, fan=3), dict(dy=4, head=4, spread=6, jaw=2),
                        dict(dy=10, head=12, spread=18, jaw=6, chips=True, fan=5, spikes=6, lift=4)),
        "windup_volley": (dict(jaw=6, orbs=3, head=-20, spread=16, fan=7, spikes=8, lift=-2, dy=-2, **P2),
                          dict(jaw=8, orbs=5, head=-24, spread=18, fan=8, spikes=8, lift=-4, dy=-3, **P2)),
        "attack_volley": (dict(jaw=8, head=-24, spread=16, fan=8, spikes=8, lift=-4, dy=-3, **P2), dict(jaw=2, head=0, **P2),
                          dict(jaw=8, head=-14, spread=18, fan=9, spikes=10, lift=-6, dy=-6, hs=1.08, **P2)),
        "hurt": dict(head=-8, eyes="shut", dy=-2, jaw=2, shift=-4),
        "stagger": (dict(shift=-10, legs=(0, 12), head=4, eyes="shut", jaw=2), dict(shift=8, legs=(8, 0), head=6, eyes="shut")),
        "idle2": [dict(spikes=2, **P2), dict(dy=2, spikes=2, **P2), dict(dy=2, head=2, spikes=2, **P2),
                  dict(head=2, jaw=2, spikes=2, **P2)],
        "defeat": [dict(head=-12, eyes="shut", jaw=6, shift=-6, **P2), dict(head=-10, eyes="shut", jaw=4, **P2),
                   dict(collapse=2, head=10, eyes="shut", spread=8, **P2)],
        "remains": dict(collapse=4),
    }
    out = actions(Pose, draw, K, PATTERNS, PHASE2)
    # the purification (6 frames): the hit, the buckle, the collapse (v2's three keys); then v2 melted
    # the collapsed frame by a formula -- here frames 3 and 4 are the collapsed parts in the murk ramp,
    # sinking behind a hand-drawn pool; frame 5 is the remains
    for i, k in enumerate(K["defeat"]):
        out[f"defeat.{i}"] = draw(Pose(**k))
    last = dict(K["defeat"][2])
    out["defeat.3"] = draw(Pose(**dict(last, melt=1)))
    out["defeat.4"] = draw(Pose(**dict(last, melt=2)))
    out["defeat.5"] = remains()
    return out


ACTIONS = boss_actions(PATTERNS)
RAMPS = palette.RAMPS
