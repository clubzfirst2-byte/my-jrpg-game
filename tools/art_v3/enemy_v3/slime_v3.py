"""v3 slime, every action (density 4, 64 x 56), drawn the way the passed pilot is drawn
(tools/art_v3/gen_slime_v3.py: the v1 drop, curved round shading, the lips on the ground, the core
glowing through the jelly, v1's pink eyes, the shine, the bubbles; outline the jelly's tone 0 #2e1a3e).

The pilot's frame is generalised by a few pose numbers: dx (the body shifted along the ground), lift
(off the ground: no lips spread while airborne), lean, rx, top, foot, ph (bubbles), eyes ("open",
"squint", "shut", "x"), charge (the core flares in the wind-up / attack), sink (defeat: the drop
sinks into a puddle, the eyes and core going out last). With dx = lift = 0, eyes "open" and charge 0
the frame is the pilot's, texel for texel (gen_enemy_v3 checks the 4 idle frames against the pilot
files and keeps them).
Actions and frame counts are v2's (frames.json): idle 4 (the pilot), move 8 (a hop), windup 4
(rises, then squashes back), attack 5 (lunges forward and slams, recovers over 3 frames), hurt 3
(knocked back, eyes shut), defeat 6 (squashed, sinking, melting into a puddle, the core last).
"""

import numpy as np

from v3lib import Canvas, despeckle

W, H = 64, 56
G = 54
RAMPS = {
    "jelly": ["#2e1a3e", "#3a2150", "#47295f", "#573271", "#6e4490", "#9a70c0", "#c4a0e4"],
    "core": ["#4a1050", "#6a1e6a", "#8e2c8e", "#b040b0", "#e070e0", "#ffc8ff"],
    "glow": ["#3a2150", "#55306f", "#62387e", "#70428e", "#80509e", "#9a70c0"],
}
EYE, EYE_D, EYE_W, PUPIL = "#e070e0", "#b040b0", "#ffd8ff", "#3a1a44"

BASE = dict(lean=0, rx=21.5, top=16, foot=30, ph=0, dx=0, lift=0, eyes="open", charge=0, sink=0, pilot_bubbles=False)
IDLE = [  # the pilot's 4 poses
    dict(lean=0, rx=21.5, top=16, foot=30, ph=0),
    dict(lean=1, rx=22.5, top=17, foot=31, ph=1),
    dict(lean=0, rx=21.0, top=14, foot=29, ph=2),
    dict(lean=-1, rx=21.5, top=16, foot=30.5, ph=3),
]


def P(**k):
    d = dict(BASE)
    d.update(k)
    return d


ACTIONS = {
    "idle": [P(pilot_bubbles=True, **p) for p in IDLE],
    # a hop: gather (squash) -> spring up (tall, narrow) -> apex -> falling -> land (squash wide) ->
    # rebound -> settle -> a step forward ready for the next hop
    "move": [
        P(top=21, rx=23.5, foot=32, ph=0),
        P(top=10, rx=18.5, foot=22, ph=1, lift=3, lean=1),
        P(top=8, rx=19.0, foot=23, ph=2, lift=6, lean=1),
        P(top=10, rx=19.5, foot=24, ph=3, lift=4, lean=0),
        P(top=23, rx=24.0, foot=33, ph=0),
        P(top=13, rx=20.5, foot=28, ph=1, lean=-1),
        P(top=17, rx=22.0, foot=30.5, ph=2, lean=0),
        P(top=16, rx=21.5, foot=30, ph=3),
    ],
    # wind-up: a small rise (anticipation), then it squashes back, leaning away, the core flaring;
    # the last frame is the held pose
    "windup": [  # round 2: deeper -- a rise, then squashed far back and low (held)
        P(top=11, rx=19.5, foot=27.5, ph=0, lean=1, charge=1),
        P(top=21, rx=23.5, foot=30.5, ph=1, lean=-4, charge=1, eyes="squint"),
        P(top=28, rx=25.5, foot=30.5, ph=2, lean=-6, charge=2, eyes="squint"),
        P(top=31, rx=26.0, foot=30.5, ph=3, lean=-7, charge=2, eyes="squint"),
    ],
    # attack (round 2): two frames in the air (the launch, tall and leaning forward; the flight, high
    # and stretched forward), the slam flattened forward on landing, then two frames back to rest
    "attack": [
        P(top=4, rx=16.5, foot=22, ph=0, lean=7, lift=8, charge=2, eyes="squint"),
        P(top=4, rx=20.0, foot=24, ph=1, lean=10, lift=16, charge=2, eyes="squint"),
        P(top=30, rx=26.0, foot=30.5, ph=2, lean=8, charge=1),
        P(top=13, rx=20.5, foot=29, ph=3, lean=3),
        P(top=17, rx=22.0, foot=30, ph=0, lean=1),
    ],
    # hurt (round 2): knocked up and back (narrow, tilted away, eyes shut), squashed on landing, back
    "hurt": [
        P(top=14, rx=18.0, foot=24, ph=0, lean=-9, lift=6, eyes="shut"),
        P(top=24, rx=24.5, foot=30.5, ph=1, lean=-5, eyes="shut"),
        P(top=17, rx=22.0, foot=30, ph=2, lean=-2),
    ],
    # defeat: the hit, the buckle, sinking, melting, a puddle, the last of the core
    "defeat": [
        P(top=20, rx=23.0, foot=31.5, ph=0, lean=-3, eyes="shut"),
        P(top=26, rx=24.5, foot=33, ph=1, lean=-1, eyes="shut", sink=1),
        P(top=32, rx=25.5, foot=34, ph=2, eyes="x", sink=2),
        P(top=38, rx=26.5, foot=35, ph=3, eyes="x", sink=3),
        P(top=44, rx=27.5, foot=36, ph=0, eyes="none", sink=4),
        P(top=48, rx=27.5, foot=36, ph=1, eyes="none", sink=5),
    ],
}


def body_mask(lean, rx, top, foot, dx, lift, sink):
    """The pilot's drop (round top, sides widening a little, the foot spreading into lips), moved
    by dx, lifted by `lift` (airborne: no spreading lips) and, when sinking, flattened (a puddle)."""
    yy, xx = np.mgrid[0:H, 0:W]
    cx = 31.5 + dx
    g = G - lift
    m = np.zeros((H, W), bool)
    for y in range(top, g + 1):
        t = (y - top) / (g - top)
        sx = cx + lean * (1 - t)
        if t < 0.50:
            u = t / 0.50
            hw = rx * np.sqrt(max(0.0, 1 - (1 - u) ** 2))
        elif t < 0.80:
            hw = rx + (t - 0.50) / 0.30 * 2.5
        else:
            u = (t - 0.80) / 0.20
            if lift:  # airborne: the bottom rounds off (no lips)
                hw = (rx + 2.5) * np.sqrt(max(0.0, 1 - u * u * 0.55))
            else:
                spread = min(foot, 30.5)  # the frame is 64 wide: the lips stop 1 texel inside
                hw = rx + 2.5 + (spread - rx - 2.5) * u ** 1.8
        if sink >= 4:  # a puddle: flat, wide, a rounded top
            u = (y - top) / max(1, g - top)
            hw = min(foot, 30.5) * min(1.0, np.sqrt(max(0.0, u)) * 1.1)
        if hw >= 3:
            m[y] |= np.abs(xx[y] + 0.5 - sx) <= hw
    return m


def frame(p):
    p = dict(BASE, **p)
    c = Canvas(W, H, RAMPS)
    lift, dx, sink = p["lift"], p["dx"], p["sink"]
    body = body_mask(p["lean"], p["rx"], p["top"], p["foot"], dx, lift, sink)
    g = G - lift
    c.fill(body, "jelly")
    hgt = g - p["top"]
    for y, x in zip(*np.nonzero(body)):
        row = np.nonzero(body[y])[0]
        hw = max(1.0, (row.max() - row.min() + 1) / 2)
        nx = (x + 0.5 - (row.min() + hw)) / hw
        ny = (y + 0.5 - (p["top"] + hgt * 0.55)) / (hgt * 0.62)
        v = 0.55 - 0.42 * nx - 0.38 * ny - 0.18 * (nx * nx + ny * ny)
        c.tone[y, x] = 1 if v < 0.12 else 2 if v < 0.42 else 3 if v < 0.72 else 4
    cx = 31.5 + p["lean"] * 0.5 + dx
    if not lift:
        for x in range(W):
            ys = np.nonzero(body[:, x])[0]
            if not len(ys):
                continue
            if abs(x + 0.5 - cx) > p["rx"] + 3:
                c.tone[ys.min(), x] = 5 if x < cx else 4
    # the core (smaller and dimmer as it sinks; brighter when charged)
    ccy = g - 15 if sink < 3 else g - max(5, (g - p["top"]) // 2)
    k = 1.0 if sink < 3 else (0.75 if sink < 5 else 0.55)
    halo = c.m_ellipse(cx + 1, ccy, 7.5 * k + p["charge"], 6.5 * k + p["charge"]) & body
    c.fill(halo, "glow")
    c.shade_part(halo, tones=(1, 2, 3, 4) if not p["charge"] else (2, 3, 4, 5), light=(0.0, 0.0, 1.0), norm=True)
    cry = c.m_poly([(cx + 1, ccy - 6 * k), (cx + 1 + 4.5 * k, ccy), (cx + 1, ccy + 5.5 * k), (cx + 1 - 4.5 * k, ccy)])
    c.fill(cry, "core")
    for y, x in zip(*np.nonzero(cry)):
        ddx, ddy = x + 0.5 - (cx + 1), y + 0.5 - ccy
        t = 5 if (ddx < 0 and ddy < 0 and ddx > -2.5 and ddy > -4) else 4 if (ddx < 0 and ddy < 0) else \
            1 if (ddx >= 0 and ddy >= 0 and ddx + ddy > 3.5) else 2 if (ddx >= 0 and ddy >= 0) else 3
        if p["charge"] == 2 and t < 4:
            t += 1
        if sink >= 5:
            t = max(1, t - 1)
        c.tone[y, x] = t
    # eyes
    ey = p["top"] + 9
    eyes = p["eyes"]
    for ex in (int(cx - 9), int(cx + 5)):
        if eyes == "open":
            for ddy in range(4):
                for ddx in range(4):
                    col = EYE_W if (ddx < 2 and ddy < 2) else (EYE_D if (ddx == 3 and ddy == 3) else EYE)
                    c.dot(ex + ddx, ey + ddy, col)
            for ddy in (4, 5):
                for ddx in (0, 1):
                    c.dot(ex + ddx, ey + ddy, PUPIL)
        elif eyes == "squint":  # narrowed, angry: the lower half, the inner corner raised
            for ddx in range(4):
                for ddy in (2, 3):
                    c.dot(ex + ddx, ey + ddy, EYE if ddy == 3 or ddx in (1, 2) else EYE_D)
            inner = 0 if ex > cx else 3
            c.dot(ex + inner, ey + 1, EYE_D)
            for ddx in (0, 1):
                c.dot(ex + ddx, ey + 4, PUPIL)
        elif eyes == "shut":  # a closed lid: a 4 x 2 dark curve
            for ddx in range(4):
                c.dot(ex + ddx, ey + (3 if ddx in (1, 2) else 2), PUPIL)
                c.dot(ex + ddx, ey + (4 if ddx in (1, 2) else 3), PUPIL)
        elif eyes == "x":  # going out: a small dim cross 4 x 4
            for d in range(4):
                c.dot(ex + d, ey + d, EYE_D)
                c.dot(ex + 3 - d, ey + d, EYE_D)
    # the shine
    top = p["top"]
    if sink < 4:
        for y in range(top + 3, min(top + 15, g)):
            xs = np.nonzero(body[y])[0]
            if not len(xs):
                continue
            x = xs.min() + 3 + max(0, (top + 6 - y)) // 2
            c.put(x, y, "jelly", 6 if top + 5 <= y <= top + 11 else 5)
            c.put(x + 1, y, "jelly", 5)
        sx, sy = int(cx - 6), top + 3
        for ddx, ddy in ((0, 0), (1, 0), (0, 1), (1, 1)):
            c.put(sx + ddx, sy + ddy, "jelly", 6 if (ddx, ddy) != (1, 1) else 5)
    # bubbles
    for kk, (bx, by) in enumerate(((cx - 15, 40 - lift), (cx + 12, 36 - lift), (cx - 8, 47 - lift))):
        y0 = int(by - ((p["ph"] + kk) % 4) * 2)
        x0 = int(bx)
        if y0 < 0 or x0 < 0 or y0 + 3 > H or x0 + 3 > W:
            continue
        if not all(body[y0 + j, x0 + i] for j in range(3) for i in range(3)):
            continue
        if (halo | cry)[y0:y0 + 3, x0:x0 + 3].any():
            continue
        if p.get("pilot_bubbles", False):  # the pilot's idle bubble (kept texel for texel)
            for ddx, ddy in ((0, 0), (1, 0), (0, 1)):
                c.put(x0 + ddx, y0 + ddy, "jelly", 6)
            c.put(x0 + 1, y0 + 1, "jelly", 5)
            c.put(x0 + 1, y0 + 2, "jelly", 1)
            c.put(x0 + 2, y0 + 2, "jelly", 1)
        else:  # round 2: a 2 x 2 light and a 2 x 1 shade under it (no single texels)
            for ddx, ddy in ((0, 0), (1, 0), (0, 1), (1, 1)):
                c.put(x0 + ddx, y0 + ddy, "jelly", 6 if ddy == 0 else 5)
            c.put(x0, y0 + 2, "jelly", 1)
            c.put(x0 + 1, y0 + 2, "jelly", 1)
    despeckle(c)
    c.outline()
    c.shadow_band()
    return c


def frames():
    return {f"{a}.{i}": frame(p) for a, ps in ACTIONS.items() for i, p in enumerate(ps)}
