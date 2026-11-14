"""凍て角のヌシ (boss_frost) at density 4: 192 x 176 (antlers included), the feet on the bottom rows, seen
from the front.

The same design, keys, frame counts and key poses as v2 (tools/enemy_v2/boss_frost.py at d900394; the
lengths here are v2's x 2, in texels). Every part is a hand-drawn pixel map (frost_head.py,
frost_body.py, frost_antlers.py, frost_fall.py); a frame only PLACES the parts at whole-texel offsets,
back to front, each part once.
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import frost_antlers as A  # noqa: E402
import frost_body as B  # noqa: E402
import frost_head as HD  # noqa: E402
from bossanim import actions, boss_actions  # noqa: E402
from pixmap import Frame, Legend, part  # noqa: E402

W, H = 192, 176
G = 174  # the front hooves' last row is 175
CX = 96


def hx(s):
    return (int(s[1:3], 16), int(s[3:5], 16), int(s[5:7], 16))


# frostfur / ice / murk / glow: v2's colours, tone 0 lifted to luma 30 (the v3 normal enemies' values).
# frostfur_d (dark fur), frostfur_m and ice_d (tones between the others) are new in v3.
RAMPS = {k: [hx(c) for c in v] for k, v in {
    "frostfur": ["#261e1a", "#55483e", "#706155", "#8a7a6c", "#9d8e80", "#b0a294", "#dcd2c6"],
    "frostfur_d": ["#261e1a", "#3c322b", "#4a3e36", "#584b41", "#6a5c50", "#7c6d60", "#9a8a7c"],
    "frostfur_m": ["#261e1a", "#63554a", "#75665a", "#7d6e61", "#958678", "#a39486", "#c6baac"],
    "ice": ["#1a3040", "#3e6e88", "#5c91aa", "#7ab4cc", "#99ccde", "#b8e4f0", "#f0fcff"],
    "ice_d": ["#1a3040", "#2c5068", "#3e6a84", "#4f84a0", "#6ea4bc", "#8cc2d8", "#d4f0f8"],
    "murk": ["#2c183c", "#2e1a3e", "#3c2250", "#4a2a62", "#5c3779", "#6e4490", "#9a70c0"],
    "glow": ["#421042", "#6a1e6a", "#8d2f8d", "#b040b0", "#c858c8", "#e070e0", "#ffc8ff"],
}.items()}
GROUPS = [("abcdefg", "frostfur"), ("hijklmn", "frostfur_d"), ("opqrstu", "frostfur_m"), ("ABCDEFG", "ice"),
          ("HIJKLMN", "ice_d"), ("OPQRSTU", "murk"), ("VWXYZ$%", "glow")]
LEG = Legend(GROUPS)

P = {}
COLS = set()
for _m in (HD, B, A):
    for _n in dir(_m):
        _v = getattr(_m, _n)
        if _n.isupper() and isinstance(_v, str) and "\n" in _v:
            P[_n] = part(_v, LEG, _n, cols=_n in getattr(_m, "COLS", ()))
for _n in A.COLS | {"DOWN_BEAM", "SLAM_BEAM"}:
    P[_n + "~"] = P[_n].mirror(band=False)
for _n in ("UP_T1", "UP_T2", "UP_T3", "LEAN_T", "PRONG", "FLAT_T", "FLEG", "HIND"):
    P[_n + "~"] = P[_n].mirror(relight=True)
for _n in ("SHOULDER", "EAR", "RIME_A", "BREAK", "FOREARM"):
    P[_n + "~"] = P[_n].mirror()
for _n in ("EYE_OPEN", "EYE_SHUT", "EYE_NARROW"):
    P[_n + "~"] = P[_n].mirror(darker=False, band=False)
for _n in ("CL_A", "CL_B", "CL_C", "CM_A", "CM_B", "CM_C", "CM_D", "CD_A", "CD_B", "CD_C", "CD_D"):
    P[_n + "~"] = P[_n].mirror(darker=False, band=False)


def both(f, name, x, y, cx=CX, **kw):
    p = P[name]
    f.put(p, x, y, **kw)
    f.put(P[name + "~"], 2 * cx - x - p.w, y, **kw)


# the clumps of the mane and chest, back to front (name, x, y in the frame at rest)
MANE = (
    ("CD_B", 68, 124), ("CD_B~", 112, 123), ("CD_D", 72, 124), ("CD_D~", 100, 122), ("CD_A~", 89, 127),
    ("CD_A", 70, 104), ("CD_B~", 114, 104), ("CD_C~", 82, 112), ("CD_A~", 96, 106), ("CD_C", 108, 110), ("CM_B", 86, 104),
    ("CM_C", 68, 92), ("CD_C~", 113, 92), ("CM_D", 76, 90), ("CM_A", 100, 90), ("CD_C", 92, 100),
    ("CL_C", 66, 84), ("CL_B", 67, 72), ("CD_A~", 112, 72), ("CD_C~", 114, 62), ("CL_C", 71, 62),
)


# ---- the antler attitudes: (part, x, y) of the image-left antler with the head at rest; the right one
# is its mirror. Each map is placed once. "~" in a name: the mirrored map on the image-left side.
ANTLERS = {
    "UP": [("UP_BEAM", 18, 4), ("UP_T3", 25, 6), ("UP_T2", 40, 4), ("UP_T1", 68, 18)],
    "MID": [("MID_BEAM", 14, 40), ("UP_T3", 20, 32), ("LEAN_T", 36, 27), ("UP_T1", 58, 27)],
    "LOW": [("LOW_BEAM", 14, 50), ("UP_T3", 21, 58), ("UP_T1", 40, 50), ("LEAN_T", 56, 40)],
    "DOWN": [("DOWN_BEAM", 40, 46), ("SIDE_T1", 57, 52), ("SIDE_T2", 45, 76)],
    "SLAM": [("SLAM_BEAM", 60, 48), ("SIDE_T2", 59, 62), ("SIDE_T1", 55, 90)],
    "HIGH": [("HIGH_BEAM", 44, 20), ("UP_T3", 48, 13), ("UP_T1", 64, 20)],
    "FLAT": [("FLAT_BEAM", 20, 40), ("FLAT_T", 30, 37), ("FLAT_T", 52, 36), ("PRONG", 70, 34)],
    "THRUST": [("THRUST_BEAM", 8, 48), ("FLAT_T", 58, 44), ("PRONG", 30, 56)],
}
# phase 2: the parts left out (snapped off) and where the glowing break sits
BROKEN = {
    "UP": ({"UP_T3"}, [(16, 22), (46, 3)]),
    "MID": ({"UP_T3"}, [(12, 52)]),
    "LOW": ({"UP_T3"}, [(12, 80)]),
    "FLAT": (set(), [(14, 46)]),
    "THRUST": (set(), [(6, 74)]),
}


def antlers(f, state, ox, oy, cx=CX, broken=False):
    gone, breaks = BROKEN.get(state, (set(), [])) if broken else (set(), [])
    for n, x, y in ANTLERS[state]:
        if n not in gone:
            both(f, n, x + ox, y + oy, cx=cx)
    for x, y in breaks:
        both(f, "BREAK", x + ox, y + oy, cx=cx)


# the faces: (map, eye row in the frame at rest, jaw row or None)
FACES = {"FACE": (66, 105), "FACE_DOWN": (68, None), "FACE_UP": (60, 81)}


def head(f, ox=0, oy=0, state="UP", face="FACE", eyes="EYE_OPEN", jaw=0, core="CORE", broken=False):
    cx = CX + ox
    ey, jy = FACES[face]
    both(f, "EAR", 61 + ox, 55 + oy, cx=cx)
    antlers(f, state, ox, oy, cx, broken)
    if jy is not None and jaw > 0:
        f.put(P["MOUTH"], 88 + ox, jy - 2 + oy)
    f.put(P[face], 79 + ox, 53 + oy)
    if jy is not None:
        f.put(P["JAW"], 87 + ox, jy + oy + jaw)
    both(f, eyes, 81 + ox, ey + oy, cx=cx)
    f.put(P[core], 88 + ox, 37 + oy)


def body(f, dy=0, bx=0, rear=0, legs=(0, 0, 0, 0), spread=0, phase2=False, clip=None):
    """The legs stay on the ground; the shoulders, chest and mane move by (bx, dy - rear)."""
    by = dy - rear
    for s, lift in ((-1, legs[1]), (1, legs[2])):
        x, y = 60 + int(round(bx * 0.3)), 136 - 2 * int(math.floor(lift + 0.5))
        if s < 0:
            f.put(P["HIND"], x, y)
        else:
            f.put(P["HIND~"], 2 * (CX + int(round(bx * 0.3))) - x - P["HIND"].w, y)
    for s, lift in ((-1, legs[0]), (1, legs[3])):
        x, y = 44 - spread + bx // 2, 133 - 2 * int(math.floor(lift + 0.5))
        c2 = CX + bx // 2
        if rear:
            fx = x + 1 if s < 0 else 2 * c2 - x - 1 - P["FOREARM"].w
            f.put(P["FOREARM" if s < 0 else "FOREARM~"], fx, 127 - rear + dy)
        if s < 0:
            f.put(P["FLEG"], x, y)
        else:
            f.put(P["FLEG~"], 2 * c2 - x - P["FLEG"].w, y)
    both(f, "SHOULDER", 40 + bx, 88 + by, cx=CX + bx, clip_y=clip)
    for n, x, y in (("CL_A", 43, 101), ("CL_C", 58, 110), ("CL_B", 49, 117)):
        f.put(P[n], x + bx, y + by, clip_y=clip)
    for n, x, y in (("CM_A", 130, 101), ("CM_C~", 123, 110), ("CM_B~", 130, 117)):
        f.put(P[n], x + bx, y + by, clip_y=clip)
    both(f, "RIME_A", 54 + bx, 85 + by, cx=CX + bx)
    if phase2:
        f.put(P["CRACK_A"], 47 + bx, 100 + by)
        f.put(P["CRACK_B"], 134 + bx, 104 + by)
    f.put(P["CHEST_BASE"], 64 + bx, 60 + by, clip_y=clip)
    f.put(P["NAPE"], 78 + bx, 57 + by)
    for n, x, y in MANE:
        f.put(P[n], x + bx, y + by, clip_y=clip)


class Pose:
    def __init__(self, **k):
        self.dy = 0  # the whole body down (+)
        self.head = 0  # head down (+) / up (-)
        self.hs = 1.0  # v2: head scale (the charge's lunge). v3: the thrust attitude; the body sinks forward
        self.fore = 1.0  # v2: the face's foreshortening. v3: not used (the face is picked by the head's height)
        self.rot = 0  # the antlers' turn in degrees: picks the hand-drawn attitude
        self.lev = 0  # antlers levelled toward the camera (charge): 0..1
        self.legs = (0, 0, 0, 0)  # lift of each leg in v2 pixels (x 2 texels): front left, hind left, hind right, front right
        self.rear = 0  # rearing: the front of the body up (+)
        self.shift = 0
        self.mouth = 0  # the chin's drop
        self.shards = 0  # ice crystals around (ring): count
        self.shard_r = 0  # how far out they are (0 at the body .. 1 at the frame edge)
        self.shard_s = 1.0  # their size: the large map from 1.0, the small one under it
        self.eyes = "open"
        self.phase2 = False
        self.collapse = 0
        self.chips = False
        self.__dict__.update(k)


def attitude(p):
    if p.lev >= 0.5:
        return "THRUST" if p.hs >= 1.05 else "FLAT"
    if p.rear >= 4:
        return "HIGH"
    if p.rot >= 85:
        return "SLAM"
    if p.rot >= 60:
        return "DOWN"
    if p.rot >= 40:
        return "LOW"
    if p.rot >= 22:
        return "MID"
    return "UP"


def pick_face(p, state):
    if state in ("SLAM", "DOWN", "THRUST", "FLAT") or p.head >= 18:
        return "FACE_DOWN"
    if p.head <= -4 or p.mouth >= 6:
        return "FACE_UP"
    return "FACE"


def draw(p):
    f = Frame(W, H, LEG, RAMPS)
    c = int(p.collapse)
    lunge = max(0.0, (p.hs - 1.0) / 0.12)  # 0 .. 1 at the charge's strike
    dy = int(round(p.dy + 3 * lunge)) + c * 12
    bx = int(round(p.shift))
    rear = int(round(p.rear))
    state = attitude(p)
    face = pick_face(p, state)
    body(f, dy, bx, rear, p.legs, spread=int(round(4 * lunge)), phase2=p.phase2 or c > 0)
    hy = dy + int(round(p.head)) - int(round(rear * 0.6)) + int(round(10 * lunge))
    if state == "UP":
        hy = max(hy, -3)  # the tips stay in the frame: the head rises less (the antlers keep their size)
    if state == "HIGH":
        hy = max(hy, -8)
    hx_ = max(min(int(round(bx * 1.4)), 12), -12)
    eyes = {"open": "EYE_OPEN", "shut": "EYE_SHUT"}[p.eyes]
    if face == "FACE_DOWN" and eyes == "EYE_OPEN":
        eyes = "EYE_NARROW"
    head(f, hx_, hy, state, face, eyes, jaw=int(round(p.mouth * 0.75)), core="CORE",
         broken=p.phase2 or c > 0)
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
        for i, (x, y) in enumerate(((20, G - 6), (172, G - 8), (40, G - 2), (152, G - 2), (60, G - 18), (132, G - 18), (12, G - 22), (180, G - 24))):
            q = P["CHIP_A" if i % 2 == 0 else "CHIP_B"]
            f.put(q, x - q.w // 2, y - q.h)
    return f


SIZE = (W, H)
PATTERNS = ("slam", "ring", "charge")
PHASE2 = ("charge",)
SMOOTH = {"rot", "lev", "fore", "hs", "shard_r", "shard_s", "legs"}


def keys():
    P2 = dict(phase2=True)
    # v2's key poses, the lengths x 2 (texels)
    return {
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


def frames():
    K = keys()
    out = actions(Pose, draw, K, PATTERNS, PHASE2)
    for i, k in enumerate(K["defeat"]):
        out[f"defeat.{i}"] = draw(Pose(**k))
    out["defeat.3"] = melt_a()
    out["defeat.4"] = melt_b()
    out["defeat.5"] = remains()
    return out


def melt_a():
    return draw(Pose(collapse=2, head=24, rot=60, eyes="shut", phase2=True))


def melt_b():
    return draw(Pose(collapse=2, head=30, rot=60, eyes="shut", phase2=True, dy=8))


def remains():
    return draw(Pose(collapse=2, head=36, rot=60, eyes="shut", phase2=True, dy=12))


ACTIONS = boss_actions(PATTERNS)


def debug_poses():
    rec = []

    def grab(p):
        rec.append(dict(p.__dict__))
        return draw(p)
    out = actions(Pose, grab, keys(), PATTERNS, PHASE2)
    return list(zip(out.keys(), rec))


def idle_test():
    return draw(Pose())


def att_test(state):
    f = Frame(W, H, LEG, RAMPS)
    body(f)
    head(f, 0, 0, state)
    return f
