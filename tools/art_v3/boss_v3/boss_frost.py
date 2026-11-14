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
P["UP_BEAM~"] = P["UP_BEAM"].mirror(band=False)
for _n in ("UP_T1", "UP_T2", "UP_T3", "FLEG", "HIND"):
    P[_n + "~"] = P[_n].mirror(relight=True)
for _n in ("SHOULDER", "EAR", "RIME_A"):
    P[_n + "~"] = P[_n].mirror()
for _n in ("EYE_OPEN", "EYE_SHUT"):
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


def idle_test():
    f = Frame(W, H, LEG, RAMPS)
    both(f, "HIND", 60, 136)
    both(f, "FLEG", 44, 133)
    both(f, "SHOULDER", 40, 88)
    for n, x, y in (("CL_A", 43, 101), ("CL_C", 58, 110), ("CL_B", 49, 117)):
        f.put(P[n], x, y)
    for n, x, y in (("CM_A", 130, 101), ("CM_C~", 123, 110), ("CM_B~", 130, 117)):
        f.put(P[n], x, y)
    both(f, "RIME_A", 54, 85)
    f.put(P["CHEST_BASE"], 64, 60)
    for n, x, y in MANE:
        f.put(P[n], x, y)
    both(f, "EAR", 61, 55)
    both(f, "UP_BEAM", 18, 4)
    for n, (x, y) in (("UP_T3", (25, 6)), ("UP_T2", (40, 4)), ("UP_T1", (68, 18))):
        both(f, n, x, y)
    f.put(P["FACE"], 79, 53)
    f.put(P["JAW"], 87, 105)
    both(f, "EYE_OPEN", 81, 66)
    f.put(P["CORE"], 88, 37)
    return f
