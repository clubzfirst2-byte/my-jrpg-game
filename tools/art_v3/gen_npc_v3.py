"""v3 pilot (round 2): the village woman (npc.woman), hand built at 2x detail (64 x 112), facing down,
idle 4 frames (breath, braid sway, a blink on the last frame like v1).

Drawn part by part on the 64 x 112 grid (hdkit.py), not upscaled. Design and colours follow the approved
v1 woman (tools/npc_release/woman.py, src/art-release/npc/, read only): red headscarf, auburn hair with
a braid over her right shoulder, cream blouse with puffed sleeves, plum skirt, ochre apron, a wicker
basket of herbs on her left forearm. Inspection fixes: the eyes are a lid line over the iris (no ring,
the iris not hidden), a smaller smile with raised corners and a lighter inside, cheeks lifted under the
eyes; the hand holding the basket's handle, the basket's shade on the apron; two clear pockets; the
skirt hem the same line in every frame.
Writes src/art-release-v3/npc/npc.woman.idle.down.<n>.png
Run: python3 tools/art_v3/gen_npc_v3.py
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402

from hdkit import capsule, edge_band, grooves, lock  # noqa: E402
from v3lib import ROOT, Canvas, despeckle, ramp6, save  # noqa: E402

OUT = os.path.join(ROOT, "src", "art-release-v3", "npc")
W, H = 64, 112
V1 = {  # tools/npc_release/woman.py RAMPS + the shared skin / leather (approved values)
    "hair": ["#3a120a", "#7a2c16", "#a8441e", "#cc6a34", "#ec9a5e"],
    "skin": ["#6e3e2c", "#c8906a", "#f2c49b", "#ffdcbc", "#fff0e0"],
    "blouse": ["#4e4636", "#b4a888", "#e8dec2", "#f6efdc", "#fffaf0"],
    "apron": ["#3a2a08", "#8a6a20", "#b8902e", "#d8b04a", "#f0d27a"],
    "skirt": ["#1c1028", "#4a2c5c", "#6a447e", "#8a649c", "#ac8cbc"],
    "wicker": ["#3a2410", "#7a5428", "#a8783c", "#c89a58", "#e4be80"],
    "scarf": ["#3a0808", "#8a1c1c", "#c0302a", "#e05a46", "#f8907a"],
    "herb": ["#0e2a10", "#2e6a28", "#4a9a3a", "#74c058", "#a8e08a"],
    "leather": ["#24160c", "#4a3020", "#704c30", "#946c46", "#b88c5e"],
}
RAMPS = {k: ramp6(v) for k, v in V1.items()}
INK = {"L": "#2a1a18", "D": "#6a3a10", "I": "#c07a2a", "B": "#e2a44a", "K": "#3e1e0a", "W": "#fff8ec",
       "M": "#b04a46", "o": "#e48a7c", "r": "#f4a08e", "q": "#dc9672"}
EYE_OPEN = [  # an arched lid line over the iris; the iris whole and open below it (no ring)
    ".LLLLLL.",
    "LIIKKWWL",
    ".IIKKWI.",
    ".DIIIID.",
    "..BBBB..",
]
EYE_SHUT = [  # a happy closed eye: an arc
    "........",
    ".LLLLLL.",
    "L......L",
    "........",
    "........",
]
MOUTH = [  # 12 wide (2/3 of round 1), corners up, a lighter inside
    "M..........M",
    ".MMMMMMMMMM.",
    "..oooooooo..",
    "...MMMMMM...",
]


def stamp(c, rows, x0, y0):
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch != ".":
                c.dot(x0 + i, y0 + j, INK[ch])


def head(c, oy, blink, sway):
    # hair behind the face (it shows at the sides under the scarf)
    back = c.m_poly([(12, 22 + oy), (52, 22 + oy), (54, 44 + oy), (48, 50 + oy), (16, 50 + oy), (10, 44 + oy)])
    c.fill(back, "hair")
    c.shade_part(back, tones=(1, 2, 2, 3), norm=True)
    # ears
    for ex in (12.0, 52.0):
        e = c.m_ellipse(ex, 35 + oy, 2.4, 4)
        c.fill(e, "skin")
        c.shade_part(e, tones=(1, 2, 3), norm=True)
    face = c.m_poly([(13, 24 + oy), (51, 24 + oy), (52, 36 + oy), (49, 44 + oy), (43, 48 + oy), (33, 50 + oy),
                     (31, 50 + oy), (21, 48 + oy), (15, 44 + oy), (12, 36 + oy)])
    c.fill(face, "skin")
    c.shade_part(face, tones=(2, 3, 3, 3, 4), norm=True, light=(-0.7, -0.3, 0.8))
    # side locks from under the scarf, framing the face
    for root, tip, w, bend in [((16, 22 + oy), (13, 42 + oy), 7, 1.0), ((22, 22 + oy), (18, 31 + oy), 6, 0.5),
                               ((48, 22 + oy), (51, 42 + oy), 7, -1.0), ((42, 22 + oy), (46, 31 + oy), 6, -0.5),
                               ((32, 22 + oy), (29, 28 + oy), 8, 0.4)]:
        m = lock(c, root, tip, w, bend)
        c.fill(m, "hair")
        c.shade_part(m, tones=(2, 3, 4, 5), norm=True)
        grooves(c, m)
    # the headscarf: a rounded cap, two embroidered fold lines, a rolled hem
    cap = c.m_poly([(12, 25 + oy), (11, 16 + oy), (15, 8 + oy), (23, 4 + oy), (41, 4 + oy), (49, 8 + oy),
                    (53, 16 + oy), (52, 25 + oy)])
    c.fill(cap, "scarf")
    c.shade_part(cap, tones=(2, 3, 3, 4, 4), norm=True)
    for k in range(13):  # the folds: arcs from the crown toward the temples
        t = k / 12
        for (ax, sgn) in ((22, -1), (42, 1)):
            x = ax + sgn * 8 * t
            y = 9 + oy + 10 * t ** 1.3
            c.put(int(round(x)), int(round(y)), "apron", 4 if sgn < 0 else 3)
            c.put(int(round(x)) + 1, int(round(y)), "apron", 3 if sgn < 0 else 2)
    hem = c.m_rect(12, 22 + oy, 52, 25 + oy) & cap
    c.fill(hem, "scarf", 2)
    c.fill(c.m_rect(12, 22 + oy, 52, 22 + oy) & cap, "scarf", 4)
    c.fill(c.m_rect(12, 25 + oy, 52, 25 + oy) & cap, "scarf", 1)
    # the scarf's shade on the forehead
    for x in range(14, 51):
        if c.mat[26 + oy, x] == c.mid("skin"):
            c.tone[26 + oy, x] = 2
    # face features
    for ex in (17, 39):
        stamp(c, EYE_SHUT if blink else EYE_OPEN, ex, 33 + oy)
        for i in range(2, 6):  # the cheek lifted under the eye (a smile): one light row
            c.put(ex + i, 39 + oy, "skin", 4)
    for bx in (15, 45):
        for dx in range(4):
            c.dot(bx + dx, 41 + oy, INK["r"])
            if 0 < dx < 3:
                c.dot(bx + dx, 42 + oy, INK["r"])
    for fx, fy in ((21, 41), (41, 41)):  # freckles: one soft 2-texel dab a cheek
        c.dot(fx, fy + oy, INK["q"])
        c.dot(fx + 1, fy + oy, INK["q"])
    c.put(31, 40 + oy, "skin", 2)  # nose
    c.put(32, 41 + oy, "skin", 1)
    stamp(c, MOUTH, 26, 43 + oy)


def braid(c, oy, sway):
    """Plaits: alternating lobes down the right shoulder (viewer's left), a red tie and a tuft."""
    x, y = 14.0, 44.0 + oy
    for k in range(9):
        lx = x + (1.3 if k % 2 else -1.3) + sway * k / 8
        m = c.m_ellipse(lx, y, 3.4, 2.9)
        c.fill(m, "hair")
        c.shade_part(m, tones=(1, 2, 3, 4, 5), norm=True)
        grooves(c, m, drop=2, lift=0)
        y += 3.6
    tie = c.m_ellipse(14 + sway, y - 0.5, 3, 1.6)
    c.fill(tie, "scarf", 3)
    c.put(int(13 + sway), int(y - 1), "scarf", 5)
    tuft = c.m_poly([(11.5 + sway, y + 1), (16.5 + sway, y + 1), (15 + sway, y + 6), (13 + sway, y + 6)])
    c.fill(tuft, "hair")
    c.shade_part(tuft, tones=(2, 3, 4), norm=True)


def body(c, oy, breath):
    # skirt (A-line, 4 pleats), the same hem line in every frame
    skirt = c.m_poly([(15, 64 + oy), (49, 64 + oy), (55, 86), (58, 104), (57, 107), (7, 107), (6, 104), (9, 86)])
    c.fill(skirt, "skirt", 3)
    for y, x in zip(*np.nonzero(skirt)):
        t = 3 if x < 30 else 2
        if x < 14:
            t = 4 if y > 80 else 3
        if x > 50:
            t = 1
        c.tone[y, x] = t
    for x0, x1 in ((20, 14), (26, 23), (38, 41), (45, 51)):  # pleats: groove + lit ridge left of it
        g = c.m_line([(x0, 70 + oy), (x1, 106)], 1.6) & skirt
        r = c.m_line([(x0 - 2, 70 + oy), (x1 - 2.5, 106)], 2.2) & skirt
        for y, x in zip(*np.nonzero(r)):
            c.tone[y, x] = min(5, int(c.tone[y, x]) + 1)
        for y, x in zip(*np.nonzero(g)):
            c.tone[y, x] = max(1, int(c.tone[y, x]) - 1)
    for x in range(7, 58):  # hem: a lit fold line above the edge
        ys = np.nonzero(c.mat[:, x] == c.mid("skirt"))[0]
        if len(ys):
            c.tone[ys.max() - 1, x] = min(5, int(c.tone[ys.max() - 1, x]) + 1)
    # shoes peeking out
    for sx in (24, 34):
        s = c.m_ellipse(sx + 3, 109, 4.5, 2.6) & c.m_rect(0, 107, W - 1, H - 1)
        c.fill(s, "leather")
        c.shade_part(s, tones=(1, 2, 3, 4), norm=True)
    # blouse with puffed sleeves
    bl = c.m_poly([(17, 48 + oy - breath), (47, 48 + oy - breath), (49, 64 + oy), (15, 64 + oy)])
    c.fill(bl, "blouse")
    c.shade_part(bl, tones=(2, 3, 3, 4), norm=True)
    for sx, side in ((14, -1), (50, 1)):
        p = c.m_ellipse(sx, 53 + oy - breath, 6, 6.5)
        c.fill(p, "blouse")
        c.shade_part(p, tones=(1, 2, 3, 4, 5), norm=True)
        c.fill(c.m_rect(sx - 5, 58 + oy - breath, sx + 5, 59 + oy - breath) & p, "blouse", 1)  # the cuff's gather
    neck = c.m_poly([(26, 48 + oy - breath), (38, 48 + oy - breath), (32, 54 + oy)])
    c.fill(neck, "skin", 2)
    c.fill(c.m_rect(27, 48 + oy - breath, 37, 48 + oy - breath), "skin", 1)
    for x in range(25, 40, 3):  # the gathered neckline
        c.put(x, 55 + oy - (abs(x - 32) > 4), "blouse", 2)
    # waistband
    wb = c.m_rect(15, 64 + oy, 49, 67 + oy)
    c.fill(wb, "skirt", 1)
    c.fill(c.m_rect(15, 64 + oy, 49, 64 + oy), "skirt", 3)
    # apron with two pockets (a stitched top edge, a shadowed opening)
    ap = c.m_poly([(20, 66 + oy), (44, 66 + oy), (46, 101), (18, 101)])
    c.fill(ap, "apron", 3)
    for y, x in zip(*np.nonzero(ap)):
        c.tone[y, x] = 4 if x < 22 else (2 if x > 42 else 3)
    for x0 in (22, 34):
        pk = c.m_rect(x0, 76 + oy, x0 + 8, 85 + oy)
        c.fill(pk, "apron", 3)
        c.fill(c.m_rect(x0, 76 + oy, x0 + 8, 77 + oy), "apron", 1)  # the opening's shade
        for x in range(x0 + 1, x0 + 8, 2):
            c.put(x, 78 + oy, "apron", 4)  # stitches
        c.fill(c.m_rect(x0 + 8, 77 + oy, x0 + 8, 85 + oy) | c.m_rect(x0, 85 + oy, x0 + 8, 85 + oy), "apron", 2)
        c.fill(c.m_rect(x0, 78 + oy, x0, 85 + oy), "apron", 4)
    # one soft fold down the lower apron (a lit edge left of a shade line), no other lines
    fold = c.m_line([(31, 88 + oy), (30, 100)], 1.4) & ap
    c.set_tone(fold, 2)
    lit = c.m_line([(29, 88 + oy), (28, 100)], 1.2) & ap & ~fold
    c.set_tone(lit, 4)
    c.fill(c.m_rect(18, 100, 46, 101) & ap, "apron", 2)
    return ap


def arms_and_basket(c, oy, breath):
    # her right arm (viewer's left) hangs beside the skirt, the hand at the hip
    a = capsule(c, (12, 58 + oy), (11, 70 + oy), 3.0)
    c.fill(a, "skin")
    c.shade_part(a, tones=(1, 2, 3, 4), norm=True)
    h = c.m_ellipse(11, 72 + oy, 3.2, 3.6)
    c.fill(h, "skin")
    c.shade_part(h, tones=(1, 2, 3, 4), norm=True)
    c.put(10, 74 + oy, "skin", 1)
    c.put(12, 74 + oy, "skin", 1)
    # her left arm (viewer's right) bent: the forearm across under the basket, the hand on the handle
    fa = capsule(c, (51, 56 + oy), (51, 62 + oy), 3.0)  # the upper arm down to the elbow
    c.fill(fa, "skin")
    c.shade_part(fa, tones=(1, 2, 3, 4), norm=True)
    bo = oy + 5  # the basket hangs a little lower: the hand on its handle sits below the chin
    # the basket on the forearm (its shade first, on the apron)
    sh = c.m_ellipse(43, 72 + bo, 9, 2.5) & (c.mat == c.mid("apron"))
    c.set_tone(sh, 1)
    bk = c.m_poly([(34, 60 + bo), (52, 60 + bo), (50, 69 + bo), (36, 69 + bo)])
    c.fill(bk, "wicker", 3)
    for y, x in zip(*np.nonzero(bk)):  # over-under weave: 3 x 2 blocks, rows offset
        row = (y - 60 - bo) // 2
        u = ((x + (row % 2) * 2) // 3) % 2
        t = 3 if u else 2
        if x < 37:
            t += 1
        if x > 49:
            t -= 1
        if (y - 60 - bo) % 2 == 1:
            t = max(1, t - 1) if u else t
        c.tone[y, x] = t
    c.fill(c.m_rect(34, 59 + bo, 52, 60 + bo), "wicker", 4)  # the rim
    c.fill(c.m_rect(34, 60 + bo, 52, 60 + bo), "wicker", 2)
    # herbs heaped in it
    for (hx_, hy, r) in ((38, 57, 3.2), (43, 55.5, 3.6), (48, 57, 3.0), (41, 58, 2.6), (46, 58.5, 2.4)):
        m = c.m_ellipse(hx_, hy + bo, r, r * 0.8)
        c.fill(m, "herb")
        c.shade_part(m, tones=(1, 2, 3, 4, 5), norm=True)
    c.put(44, 54 + bo, "blouse", 5)  # a small white bloom (2 x 2)
    c.put(45, 54 + bo, "blouse", 4)
    c.put(44, 55 + bo, "blouse", 3)
    c.put(45, 55 + bo, "apron", 4)
    # the handle (arc), then the hand closed round its top: the forearm rises from the elbow, the
    # fingers wrap over the handle (2 fingers with a groove between them), the thumb on the near side
    up = capsule(c, (51, 56 + bo), (46.5, 53 + bo), 2.6)
    c.fill(up, "skin")
    c.shade_part(up, tones=(1, 2, 3, 4), norm=True)
    hd = c.m_ellipse(43.5, 52 + bo, 3.6, 3.2)
    c.fill(hd, "skin")
    c.shade_part(hd, tones=(2, 3, 4), norm=True)
    for fx in (41, 42, 44, 45):  # 2 fingers over the handle: each 2 wide, a groove between
        c.put(fx, 53 + bo, "skin", 3 if fx in (41, 44) else 2)
        c.put(fx, 54 + bo, "skin", 2 if fx in (41, 44) else 1)
    c.put(43, 53 + bo, "skin", 1)
    c.put(43, 54 + bo, "skin", 1)
    c.put(42, 50 + bo, "skin", 4)  # the knuckles' light
    c.put(43, 50 + bo, "skin", 4)
    grooves(c, hd | up, drop=2, lift=0)  # the hand's own dark edge against the blouse
    # the handle: drawn after the hand except under the 2 fingers, so they close over it
    fingers = c.m_rect(40, 53 + bo, 46, 54 + bo)
    for k in range(25):
        t = k / 24
        x = 34 + 18 * t
        y = 59 + bo - 6 * math.sin(math.pi * t)
        xi, yi = int(round(x)), int(round(y))
        for dy, tone in ((0, 4 if t < 0.5 else 3), (1, 1)):
            if not fingers[yi + dy, xi]:
                c.put(xi, yi + dy, "wicker", tone)


def frame(oy=0, breath=0, blink=False, sway=0.0):
    c = Canvas(W, H, RAMPS)
    body(c, oy, breath)
    braid(c, oy, sway)
    arms_and_basket(c, oy, breath)
    head(c, oy, blink, sway)
    despeckle(c, loose=("hair",))
    edge_band(c, "skirt", 1, sides=((1, 0), (0, 1)))
    c.outline()
    c.shadow_band()
    return c


IDLE = [dict(), dict(breath=1, sway=0.5), dict(breath=1, sway=1.0, oy=1), dict(blink=True, sway=0.5)]


def main():
    out = [save(frame(**p), os.path.join(OUT, f"npc.woman.idle.down.{i}.png")) for i, p in enumerate(IDLE)]
    print("\n".join(os.path.relpath(p, ROOT) for p in out))


if __name__ == "__main__":
    main()
