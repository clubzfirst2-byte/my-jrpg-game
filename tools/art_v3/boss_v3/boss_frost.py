"""凍て角のヌシ (boss_frost) at density 4: 192 x 176 (antlers included), the feet on the bottom rows, seen
from the front.

The same design, keys, frame counts and key poses as v2 (tools/enemy_v2/boss_frost.py at d900394; the
lengths here are v2's x 2, in texels). Every part is a hand-drawn pixel map (frost_parts.py,
frost_antlers.py); a frame only PLACES the parts at whole-texel offsets, back to front. What v2 did by
a formula is done with hand-drawn states here:
  * the antlers' turn (rot) and levelling (lev): five hand-drawn attitudes -- UP, HIGH, MID, DOWN, FLAT;
  * the head's scale and the face's foreshortening (hs, fore): the head comes further down instead;
  * the antlers shrinking to stay in the frame: the head rises less instead (their size never changes);
  * the purification's melt: three hand-drawn frames (FALL_A, FALL_B, REMAINS).
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import frost_antlers as A  # noqa: E402
import frost_parts as R  # noqa: E402
import root_parts as ROOT  # noqa: E402  (the pools of murk are the same hand-drawn maps for every core)
from bossanim import actions, boss_actions  # noqa: E402
from pixmap import Frame, Legend, part  # noqa: E402

W, H = 192, 176
G = 174  # the front hooves' last row is 175
CX = 96


def hx(s):
    return (int(s[1:3], 16), int(s[3:5], 16), int(s[5:7], 16))


# frostfur / ice / murk / glow: v2's colours, tone 0 lifted to luma 30 (the v3 normal enemies' values).
# frostfur_d (the dark mane and far legs) and frostfur_p (the pale face) are new in v3.
RAMPS = {k: [hx(c) for c in v] for k, v in {
    "frostfur": ["#261e1a", "#55483e", "#706155", "#8a7a6c", "#9d8e80", "#b0a294", "#dcd2c6"],
    "frostfur_d": ["#261e1a", "#3c322b", "#4a3e36", "#584b41", "#6a5c50", "#7c6d60", "#9a8a7c"],
    "frostfur_p": ["#2e2622", "#6e6258", "#8a7d70", "#a69a8c", "#bcb0a2", "#d0c6ba", "#eee6dc"],
    "ice": ["#1a3040", "#3e6e88", "#5c91aa", "#7ab4cc", "#99ccde", "#b8e4f0", "#f0fcff"],
    "murk": ["#2c183c", "#2e1a3e", "#3c2250", "#4a2a62", "#5c3779", "#6e4490", "#9a70c0"],
    "glow": ["#421042", "#6a1e6a", "#8d2f8d", "#b040b0", "#c858c8", "#e070e0", "#ffc8ff"],
}.items()}
GROUPS = [("abcdefg", "frostfur"), ("hijklmn", "frostfur_d"), ("opqrstu", "frostfur_p"), ("ABCDEFG", "ice"),
          ("OPQRSTU", "murk"), ("VWXYZ$%", "glow")]
LEG = Legend(GROUPS)

P = {}
PLACE = dict(R.PLACE)
PLACE.update(A.PLACE)
for _n in R.PLACE:
    P[_n] = part(getattr(R, _n), LEG, _n)
    if _n in R.HALF:
        P[_n + "~"] = P[_n].mirror(relight=_n in R.RELIGHT)
for _n in ("SHARD_L", "SHARD_S", "CHIP"):
    P[_n] = part(getattr(R, _n), LEG, _n)
for _n in A.PLACE:
    P[_n] = part(getattr(A, _n), LEG, _n, cols=_n in A.COLS)
    P[_n + "~"] = P[_n].mirror()
P["GLINT"] = part(A.GLINT, LEG, "GLINT")
for _n in ("EYE_OPEN", "EYE_SHUT"):
    P[_n + "~"] = P[_n].mirror(darker=False, band=False)
P["CORE_DIM"] = P["CORE"].swap({}, tones=(0, 1, 1, 1, 1, 1, 3))  # the core gone dark
for _n in ("POOL_A", "POOL_B"):
    P[_n] = part(getattr(ROOT, _n), LEG, _n)
    P[_n + "~"] = P[_n].mirror()


class Pose:
    def __init__(self, **k):
        self.dy = 0  # the whole body down (+)
        self.head = 0  # head down (+) / up (-)
        self.hs = 1.0  # v2: head scale (the charge's lunge). v3: the head comes further down
        self.fore = 1.0  # v2: the face's foreshortening. v3: not drawn (one face)
        self.rot = 0  # the antlers' turn in degrees: picks the hand-drawn attitude
        self.lev = 0  # antlers levelled toward the camera (charge): 0..1
        self.legs = (0, 0, 0, 0)  # lift of each leg in v2 pixels (x 2 texels): front left, hind left, hind right, front right
        self.rear = 0  # rearing: the front of the body up (+), front legs folded
        self.shift = 0
        self.mouth = 0  # the chin's drop
        self.shards = 0  # ice crystals around (ring wind-up): count
        self.shard_r = 0  # how far out they are (0 at the body .. 1 at the frame edge)
        self.shard_s = 1.0  # their size: the large map from 1.0, the small one under it
        self.eyes = "open"
        self.phase2 = False
        self.collapse = 0
        self.chips = False
        self.__dict__.update(k)


def _both(f, name, x, y, cx=CX, **kw):
    p = P[name]
    f.put(p, x, y, **kw)
    f.put(P[name + "~"], 2 * cx - x - p.w, y, **kw)


def attitude(p):
    """The hand-drawn antler set for a pose."""
    if p.lev >= 0.5 or p.collapse >= 2:
        return "FLAT"
    if not (p.phase2 or p.collapse) and (p.rear >= 4 or p.rot <= -7):
        return "HIGH"
    r = p.rot + 6
    if r >= 52:
        return "DOWN"
    if r >= 30:
        return "MID"
    return "UP_BROKEN" if (p.phase2 or p.collapse) else "UP"


def antlers(f, state, ox, oy, cx, **kw):
    # every map is laid twice, a few texels apart (the second over the first): the crystal's two
    # faces, with the seam between them -- a beam 3 texels lower, an upright tine 2 texels inward
    for n in A.SETS[state]:
        x, y = PLACE[n]
        dx, dy = (0, 3) if n in A.COLS else (2, 0)
        _both(f, n, x + ox + dx, y + oy + dy, cx=cx, **kw)
        _both(f, n, x + ox, y + oy, cx=cx, **kw)
    for x, y in A.GLINTS.get(state, ()):
        g = P["GLINT"]
        f.put(g, x + ox, y + oy, **kw)
        f.put(g, 2 * cx - (x + ox) - g.w, y + oy, **kw)


def head(f, ox, oy, cx, jaw=0, eyes="open", core="CORE", state="UP"):
    if jaw:
        _both(f, "MOUTH", PLACE["MOUTH"][0] + ox, PLACE["MOUTH"][1] + oy, cx=cx)
    _both(f, "JAW", PLACE["JAW"][0] + ox, PLACE["JAW"][1] + oy + jaw, cx=cx)
    _both(f, "HEAD", PLACE["HEAD"][0] + ox, PLACE["HEAD"][1] + oy, cx=cx)
    e = "EYE_OPEN" if eyes == "open" else "EYE_SHUT"
    _both(f, e, PLACE[e][0] + ox, PLACE[e][1] + oy, cx=cx)
    antlers(f, state, ox, oy, cx)
    f.put(P[core], PLACE["CORE"][0] + ox, PLACE["CORE"][1] + oy)


def draw(p):
    c = int(p.collapse)
    if c >= 4:
        return remains()
    f = Frame(W, H, LEG, RAMPS)
    dy = int(round(p.dy + c * 12))
    bx = int(round(p.shift))
    rear = int(round(p.rear))
    by = dy - rear
    cx = CX + bx
    # hind legs (further back; rearing puts the weight on them)
    for s, lift in ((-1, p.legs[1]), (1, p.legs[2])):
        x = PLACE["HIND"][0] + int(round(bx * 0.3))
        y = PLACE["HIND"][1] - 2 * int(math.floor(lift + 0.5)) + min(rear, 5)
        q = P["HIND"]
        if s < 0:
            f.put(q, x, y)
        else:
            f.put(P["HIND~"], 2 * (CX + int(round(bx * 0.3))) - x - q.w, y)
    # front legs (near, thick); folded under the chest when it rears
    for s, lift in ((-1, p.legs[0]), (1, p.legs[3])):
        if rear:
            n, x, y, c2 = "FLEG_FOLD", PLACE["FLEG_FOLD"][0] + bx, PLACE["FLEG_FOLD"][1] + by, cx
        else:
            n, x, y, c2 = "FLEG", PLACE["FLEG"][0] + bx // 2, PLACE["FLEG"][1] - 2 * int(math.floor(lift + 0.5)), CX + bx // 2
        q = P[n]
        if s < 0:
            f.put(q, x, y)
        else:
            f.put(P[n + "~"], 2 * c2 - x - q.w, y)
    # shoulders and chest, the mane over them
    _both(f, "CHEST", PLACE["CHEST"][0] + bx, PLACE["CHEST"][1] + by, cx=cx, clip_y=G + 1)
    if p.phase2 or c:
        f.put(P["CRACK_L"], PLACE["CRACK_L"][0] + bx, PLACE["CRACK_L"][1] + by)
        f.put(P["CRACK_R"], PLACE["CRACK_R"][0] + bx, PLACE["CRACK_R"][1] + by)
    _both(f, "MANE", PLACE["MANE"][0] + bx, PLACE["MANE"][1] + by, cx=cx, clip_y=G + 1)
    # the head
    state = attitude(p)
    fwd = int(round((p.hs - 1.0) * 30))
    hy = dy + int(round(p.head)) - int(round(rear * 0.6)) + fwd
    if c:
        hy = max(hy, c * 14)
    if state == "HIGH":
        hy = max(hy, -11)
    if state.startswith("UP"):
        hy = max(hy, -3)  # the antlers' tips stay in the frame: the head rises less (their size is kept)
    hx_ = max(int(round(bx * 1.4)), -12)  # the antlers stay inside the frame
    if state == "MID":
        hx_ = max(min(hx_, 4), -4)
    head(f, hx_, hy, CX + hx_, jaw=int(round(p.mouth * 0.75)), eyes=p.eyes, core="CORE_DIM" if c >= 3 else "CORE", state=state)
    # ring: ice crystals rising around it, then flying out (v2's places x 2)
    n = int(p.shards)
    for i in range(n):
        ang = -math.pi / 2 + (i - (n - 1) / 2) * (2.6 / max(n - 1, 1))
        rx_, ry_ = 44 + 48 * p.shard_r, 36 + 44 * p.shard_r
        x = CX + math.cos(ang) * rx_
        y = 116 + math.sin(ang) * ry_ * 0.4 + 36 * (1 - p.shard_r) - (i % 2) * 8
        q = P["SHARD_L" if p.shard_s >= 1.0 else "SHARD_S"]
        y = min(max(y, 4 + q.h / 2), G - 12)
        x = min(max(x, 2 + q.w / 2), W - 2 - q.w / 2)
        f.put(q, int(round(x - q.w / 2)), int(round(y - q.h / 2)))
    if p.chips:
        for x, y in ((20, G - 6), (172, G - 8), (40, G - 2), (152, G - 2), (60, G - 18), (132, G - 18), (12, G - 22), (180, G - 24)):
            f.put(P["CHIP"], x - 3, y - 6)
    return f


def fall_a():
    """The purification, frame 3: the body slumped on the ground (hand-drawn), the head fallen on it,
    the antlers cracked short, the murk rising."""
    f = Frame(W, H, LEG, RAMPS)
    _both(f, "FALL_A", *PLACE["FALL_A"])
    head(f, 0, 56, CX, eyes="shut", core="CORE_DIM", state="FLAT")
    _both(f, "POOL_A", 0, 167)
    return f


def fall_b():
    """Frame 4: a low mound of murk with tufts of the coat (hand-drawn), the antlers lying on it."""
    f = Frame(W, H, LEG, RAMPS)
    _both(f, "FALL_B", *PLACE["FALL_B"])
    antlers(f, "FLAT", 0, 96, CX)
    f.put(P["CORE_DIM"], 89, 134)
    _both(f, "POOL_B", 0, 165)
    return f


def remains():
    """Frame 5: a heap of pale coat (hand-drawn), the broken antlers on top, the core gone dark."""
    f = Frame(W, H, LEG, RAMPS)
    _both(f, "POOL_A", 0, 165)
    _both(f, "REMAINS", PLACE["REMAINS"][0], PLACE["REMAINS"][1] + 2)
    antlers(f, "FLAT", 0, 88, CX)
    f.put(P["CORE_DIM"], 89, 128)
    return f


SIZE = (W, H)
PATTERNS = ("slam", "ring", "charge")
PHASE2 = ("charge",)
SMOOTH = {"rot", "lev", "fore", "hs", "shard_r", "shard_s", "legs"}  # legs: rounded to v2's whole pixels when drawn


def frames():
    P2 = dict(phase2=True)
    # v2's key poses, the lengths x 2 (texels)
    K = {
        "idle": [{}, dict(dy=2), dict(dy=2, head=2), dict(head=2, mouth=2)],
        "move": [dict(legs=(4, 0, 3, 0), shift=-4), dict(legs=(1, 1, 1, 1), dy=-2, head=-2, rot=-2),
                 dict(legs=(0, 3, 0, 4), shift=4), dict(legs=(1, 1, 1, 1), dy=-1, head=2, rot=2)],
        "windup_slam": (dict(head=14, rot=28, fore=0.85, dy=2), dict(head=28, rot=56, fore=0.68, dy=4)),
        "attack_slam": (dict(head=32, rot=70, fore=0.6, dy=6, chips=True), dict(head=20, rot=40, fore=0.8, dy=4, mouth=2),
                        dict(head=40, rot=96, fore=0.5, dy=8, chips=True, mouth=4)),
        "windup_ring": (dict(rear=8, head=-2, rot=-4, fore=0.75, mouth=2, shards=4, shard_r=0.2, shard_s=1.0),
                        dict(rear=16, head=-2, rot=-6, fore=0.65, mouth=4, shards=6, shard_r=0.35, shard_s=1.3)),
        "attack_ring": (dict(head=-2, rot=-8, fore=0.65, mouth=6, dy=2, shards=8, shard_r=1.0, shard_s=1.1, chips=True),
                        dict(head=-6, rot=-12, fore=0.8, mouth=2, shards=6, shard_r=1.25, shard_s=0.7)),
        "windup_charge": (dict(head=12, lev=0.7, rot=8, fore=0.8, legs=(5, 0, 0, 0), **P2),
                          dict(head=16, lev=0.95, rot=10, fore=0.75, legs=(0, 0, 0, 5), shift=2, **P2)),
        "attack_charge": (dict(head=18, lev=1.0, rot=12, hs=1.12, fore=0.75, legs=(3, 0, 0, 0), **P2),
                          dict(head=12, lev=0.7, rot=8, hs=1.06, fore=0.85, **P2)),
        "hurt": dict(head=-6, rot=-6, eyes="shut", mouth=4, shift=-4),
        "stagger": (dict(shift=-10, legs=(0, 0, 3, 6), head=6, rot=10, eyes="shut"),
                    dict(shift=8, legs=(5, 2, 0, 0), head=8, rot=14, eyes="shut")),
        "idle2": [dict(**P2), dict(dy=2, **P2), dict(dy=2, head=2, **P2), dict(head=2, mouth=2, **P2)],
        "defeat": [dict(head=-8, rot=-8, eyes="shut", mouth=6, shift=-6, **P2),
                   dict(head=-6, rot=-6, eyes="shut", mouth=6, legs=(3, 0, 0, 0), **P2),
                   dict(collapse=2, head=16, rot=32, eyes="shut", **P2)],
    }
    out = actions(Pose, draw, K, PATTERNS, PHASE2)
    # the purification (6 frames): the hit, the buckle, the collapse (v2's three keys), then three
    # hand-drawn frames: slumped with the murk rising, a mound of murk, the heap that is left
    for i, k in enumerate(K["defeat"]):
        out[f"defeat.{i}"] = draw(Pose(**k))
    out["defeat.3"] = fall_a()
    out["defeat.4"] = fall_b()
    out["defeat.5"] = remains()
    return out


ACTIONS = boss_actions(PATTERNS)
