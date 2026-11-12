"""v3 NPC production (STYLE order 5), milestone 2: the princess (npc.princess) and the smith (npc.smith).

Each is drawn from their own parts (their own hair / headwear, face map, clothes, props) on the 64 x 112
grid, following the approved v1 design notes and colours (tools/npc_release/princess.py, smith.py, read
only). Keys, frame counts and the anchor are the approved v1 ones (idle 4, walk 6; down, right, up).
Facing left is NOT stored for these two: the game draws facing right mirrored (decision 2026-11-12;
v1's left frames differ from the mirror by 40 / 272 pixels only).
"""

import numpy as np

from hdkit import capsule, edge_band, gauntlet, grooves, lock
from v3lib import Canvas, despeckle, ramp6

W, H = 64, 112
GOLD = ["#5a4018", "#a07a30", "#e8c060", "#f8dc88", "#fff4c8"]
GEM = ["#0e2a60", "#1a5cb8", "#2a8de2", "#78c8ff", "#e0f6ff"]


def _ramps(d):
    return {k: ramp6(v) for k, v in d.items()}


def _finish(c, band=None):
    despeckle(c, loose=("hair",))
    if band:
        edge_band(c, band, 1)
    c.outline()
    c.shadow_band()
    return c


def _stamp(c, rows, x0, y0, ink, mirror=False):
    for j, row in enumerate(rows):
        r = row[::-1] if mirror else row
        for i, ch in enumerate(r):
            if ch != ".":
                c.dot(x0 + i, y0 + j, ink[ch])


def _shade_locks(c, locks, mass, tones=(2, 3, 3, 4, 5)):
    for root, tip, w, bend in locks:
        m = lock(c, root, tip, w, bend)
        c.fill(m, "hair")
        c.shade_part(m, tones=tones, norm=True, global_mask=mass, gmix=0.4)
        grooves(c, m, drop=1, sides=True)


def _boot(c, x, y, w, h, mat="boot", toe=0):
    b = c.m_poly([(x - w / 2, y - h), (x + w / 2, y - h), (x + w / 2 + toe, y - 2), (x + w / 2 + toe, y),
                  (x - w / 2, y)])
    c.fill(b, mat)
    c.shade_part(b, tones=(1, 2, 3, 3, 4), norm=True)
    c.fill(c.m_rect(x - w / 2, y - 1, x + w / 2 + toe, y), mat, 1)
    return b


# ================================================================ the princess

PR = _ramps({
    "hair": ["#222842", "#5e6888", "#98a2c0", "#c6cee4", "#eef2fc"],
    "skin": ["#6e3e2c", "#c8906a", "#f4c8a2", "#ffdfc4", "#fff2e4"],
    "dress": ["#3e4258", "#9ea4bc", "#dde2ee", "#f2f4fa", "#ffffff"],
    "cape": ["#080c2a", "#18225e", "#263896", "#3e56bc", "#6a86de"],
    "sash": ["#0a1840", "#1c3a86", "#2c5ab8", "#4a7ad8", "#8ab4f4"],
    "boot": ["#2a180e", "#5a3a24", "#86603e", "#a8805a", "#caa27c"],
    "stocking": ["#3e4258", "#a6acc2", "#e2e6f0", "#f2f4fa", "#ffffff"],
    "gold": GOLD, "gem": GEM,
})
PR_INK = {"e": "#26223e", "o": "#24206a", "i": "#4436a8", "j": "#4c9ee6", "u": "#9ad6ff", "k": "#ffffff",
          "l": "#dcd6e4", "n": "#8a8aa8", "m": "#b8585a", "r": "#f6aa98"}
PR_EYE = [  # dawn-sky eye: the lash line rising to the outer corner, indigo above, sky blue below, a star shine
    "....eeee",
    ".eeeeeee",
    "eoiiikie",
    ".oiijuj.",
    ".ojjuuj.",
    "..jjuu..",
]
PR_EYE_SIDE = ["eeee.", "oiike", "oijuj", ".juu."]
PR_SHUT = [".eeeeee.", "e......e"]
PR_DY = 4  # she is 2 v1 pixels shorter than the hero: 4 texels lower at the head


def _pr_circlet(c, y, x0, x1, front_x=None):
    c.fill(c.m_rect(x0, y, x1, y + 1), "gold", 3)
    c.fill(c.m_rect(x0, y, x1, y), "gold", 4)
    if front_x is not None:  # the star ring with the hero's stone
        ring = c.m_ellipse(front_x, y, 3.6, 3.6) & ~c.m_ellipse(front_x, y, 2.2, 2.2)
        c.fill(ring, "gold", 3)
        star = c.m_poly([(front_x, y - 2.5), (front_x + 1, y - 0.6), (front_x + 2.5, y), (front_x + 1, y + 0.6),
                         (front_x, y + 2.5), (front_x - 1, y + 0.6), (front_x - 2.5, y), (front_x - 1, y - 0.6)])
        c.fill(star, "gem", 3)
        c.put(int(front_x) - 1, int(y) - 1, "gem", 5)


def pr_front(oy=0, breath=0, blink=False, sway=0.0, step=0):
    c = Canvas(W, H, PR)
    o = oy + PR_DY
    # the long hair behind, past the shoulders to the waist
    back = c.m_poly([(9, 24 + o), (55, 24 + o), (58, 50 + o), (56, 74 + o + sway), (8, 74 + o - sway), (6, 50 + o)])
    c.fill(back, "hair")
    c.shade_part(back, tones=(1, 2, 2, 3, 3), norm=True)
    _shade_locks(c, [((14, 30 + o), (10, 72 + o), 8, 1.0), ((50, 30 + o), (54, 72 + o), 8, -1.0)], back)
    # legs: white stockings, soft brown boots (one steps forward)
    for x, s in ((26, -step), (38, step)):
        lift = 2 if s < 0 else 0
        c.fill(c.m_rect(x - 3, 92 + o, x + 3, 104 - lift), "stocking", 3)
        c.shade_part(c.m_rect(x - 3, 92 + o, x + 3, 104 - lift), tones=(2, 3, 4), norm=True)
        _boot(c, x, 111 - lift, 9, 8)
    # the dress (knee length), the blue border at the hem
    dr = c.m_poly([(20, 50 + o), (44, 50 + o), (47, 76 + o), (50, 94 + o), (14, 94 + o), (17, 76 + o)])
    c.fill(dr, "dress")
    c.shade_part(dr, tones=(1, 2, 3, 3, 4), norm=True)
    for x0, x1 in ((24, 21), (32, 32), (40, 43)):
        c.set_tone(c.m_line([(x0, 76 + o), (x1, 93 + o)], 1.2) & dr, 1)
    c.fill(c.m_rect(14, 91 + o, 50, 93 + o) & dr, "sash", 3)
    c.fill(c.m_rect(14, 91 + o, 50, 91 + o) & dr, "sash", 4)
    # the sash with gold star veins
    sa = c.m_rect(18, 68 + o, 46, 72 + o)
    c.fill(sa, "sash", 2)
    c.fill(c.m_rect(18, 68 + o, 46, 68 + o), "sash", 4)
    for x in (24, 32, 40):
        c.put(x, 70 + o, "gold", 4)
    # the short cape over the shoulders to the chest, gold rim, the star clasp
    cape = c.m_poly([(14, 50 + o - breath), (50, 50 + o - breath), (54, 58 + o), (52, 66 + o), (12, 66 + o), (10, 58 + o)])
    c.fill(cape, "cape", 3)
    c.shade_part(cape, tones=(2, 3, 3, 4, 4), norm=True)
    for x0, x1 in ((20, 17), (44, 47)):
        c.set_tone(c.m_line([(x0, 54 + o), (x1, 65 + o)], 1.4) & cape, 1)
    for x in range(10, 55):
        ys = np.nonzero(cape[:, x])[0]
        if len(ys):
            c.put(x, int(ys.max()), "gold", 3)
            c.put(x, int(ys.max()) - 1, "gold", 2)
    c.fill(c.m_rect(29, 50 + o, 35, 66 + o), "dress", 3)  # the dress's front between the cape's halves
    c.fill(c.m_rect(29, 50 + o, 29, 66 + o) | c.m_rect(35, 50 + o, 35, 66 + o), "gold", 3)
    c.fill(c.m_ellipse(32, 54 + o, 2.8, 2.8), "gold", 3)
    c.put(31, 53 + o, "gold", 5)
    # the hands held together in front (sleeves of the dress), the bracelet on her left wrist
    for sx in (19, 45):
        a = capsule(c, (sx, 60 + o), (29 if sx < 32 else 35, 70 + o), 3.0)
        c.fill(a & ~cape, "dress")
        c.shade_part(a & ~cape, tones=(2, 3, 4), norm=True)
    hands = c.m_ellipse(32, 72 + o, 5.0, 3.6)
    c.fill(hands, "skin")
    c.shade_part(hands, tones=(2, 3, 3, 4), norm=True)
    c.fill(c.m_line([(32, 70 + o), (32, 75 + o)], 1.0), "skin", 1)
    c.fill(c.m_rect(36, 70 + o, 37, 73 + o), "gold", 3)
    # neck, face
    c.fill(c.m_rect(28, 44 + o, 36, 50 + o), "skin", 2)
    face = c.m_poly([(16, 22 + o), (48, 22 + o), (49, 33 + o), (46, 41 + o), (39, 46 + o), (25, 46 + o), (18, 41 + o),
                     (15, 33 + o)])
    c.fill(face, "skin", 4)
    for y, x in zip(*np.nonzero(face)):
        if x >= 46 or y >= 44 + o:
            c.tone[y, x] = 3
    # the silver hair over the head: straight-cut bangs parted in the middle, braids in front
    top = c.m_poly([(12, 30 + o), (12, 16 + o), (18, 8 + o), (26, 4 + o), (38, 4 + o), (46, 8 + o), (52, 16 + o),
                    (52, 30 + o), (46, 26 + o), (46, 20 + o), (18, 20 + o), (18, 26 + o)])
    c.fill(top, "hair")
    c.shade_part(top, tones=(2, 3, 3, 4, 4), norm=True)
    bangs = c.m_poly([(17, 18 + o), (31, 18 + o), (31, 27 + o), (17, 26 + o)]) | \
        c.m_poly([(33, 18 + o), (47, 18 + o), (47, 26 + o), (33, 27 + o)])
    c.fill(bangs, "hair")
    c.shade_part(bangs, tones=(2, 3, 4, 4, 5), norm=True)
    c.fill(c.m_rect(31, 14 + o, 32, 27 + o) & ~face | c.m_rect(31, 18 + o, 32, 27 + o), "skin", 4)  # the parting
    for x in range(18, 47, 4):
        c.fill(c.m_line([(x, 19 + o), (x, 26 + o)], 1.0) & bangs, "hair", 2)
    _shade_locks(c, [((14, 24 + o), (12, 46 + o), 7, 1.0), ((50, 24 + o), (52, 46 + o), 7, -1.0)], top)
    for bx, s in ((15, 1), (49, -1)):  # the thin braids in front of the shoulders
        for k in range(7):
            m = c.m_ellipse(bx + (0.8 if k % 2 else -0.8), 46 + o + 3 * k, 2.4, 2.0)
            c.fill(m, "hair")
            c.shade_part(m, tones=(2, 3, 4, 5), norm=True)
        c.put(bx, 46 + o + 21, "sash", 3)
    _pr_circlet(c, 15 + o, 13, 51, front_x=32)
    # the face
    for ex, mir in ((17, False), (39, True)):
        if blink:
            _stamp(c, PR_SHUT, ex, 33 + o, PR_INK, mir)
        else:
            _stamp(c, PR_EYE, ex, 29 + o, PR_INK, mir)
    for x in range(18, 23):
        c.dot(x, 27 + o, PR_INK["n"])
        c.dot(x + 23, 27 + o, PR_INK["n"])
    c.put(32, 37 + o, "skin", 2)
    for bx in (19, 43):
        c.dot(bx, 38 + o, PR_INK["r"])
        c.dot(bx + 1, 38 + o, PR_INK["r"])
    for x, y in ((29, 41), (30, 42), (31, 42), (32, 42), (33, 42), (34, 41)):
        c.dot(x, y + o, PR_INK["m"])
    return _finish(c, "cape")


def pr_side(oy=0, breath=0, blink=False, sway=0.0, step=0):
    c = Canvas(W, H, PR)
    o = oy + PR_DY
    # the long hair down the back to the waist
    hb = c.m_poly([(10, 14 + o), (30, 10 + o), (32, 40 + o), (30, 74 + o), (12 - sway, 74 + o), (8, 46 + o)])
    c.fill(hb, "hair")
    c.shade_part(hb, tones=(1, 2, 3, 3, 4), norm=True)
    _shade_locks(c, [((16, 20 + o), (13 - sway, 72 + o), 8, 1.0), ((24, 20 + o), (22 - sway, 72 + o), 8, 0.5)], hb)
    # legs
    for dx, near in ((-4 * step, False), (4 * step, True)):
        x = 31 + dx
        st = c.m_rect(x - 3, 92 + o, x + 3, 104)
        c.fill(st, "stocking", 3 if near else 2)
        _boot(c, x, 111, 8, 8, toe=4)
        if not near:
            c.set_tone(c.m_rect(x - 5, 92 + o, x + 9, 111), 1)
    dr = c.m_poly([(24, 50 + o), (40, 50 + o), (43, 76 + o), (46 + step, 94 + o), (18 + step, 94 + o), (21, 76 + o)])
    c.fill(dr, "dress")
    c.shade_part(dr, tones=(1, 2, 3, 3, 4), norm=True)
    c.fill(c.m_rect(16, 91 + o, 48, 93 + o) & dr, "sash", 3)
    c.fill(c.m_rect(22, 68 + o, 42, 72 + o) & (dr | c.m_rect(22, 68 + o, 42, 72 + o)), "sash", 2)
    c.put(38, 70 + o, "gold", 4)
    # the cape over the shoulder to the chest
    cape = c.m_poly([(20, 50 + o - breath), (38, 50 + o - breath), (42, 58 + o), (40, 66 + o), (18, 66 + o), (16, 56 + o)])
    c.fill(cape, "cape", 3)
    c.shade_part(cape, tones=(2, 3, 3, 4, 4), norm=True)
    for x in range(14, 44):
        ys = np.nonzero(cape[:, x])[0]
        if len(ys):
            c.put(x, int(ys.max()), "gold", 3)
    c.fill(c.m_ellipse(40, 54 + o, 2.4, 2.4), "gold", 3)
    # the near arm: the sleeve down to the hands held in front
    a = capsule(c, (30, 58 + o), (38, 70 + o), 3.0)
    c.fill(a & ~cape, "dress")
    c.shade_part(a & ~cape, tones=(2, 3, 4), norm=True)
    hands = c.m_ellipse(40, 72 + o, 3.6, 3.4)
    c.fill(hands, "skin")
    c.shade_part(hands, tones=(2, 3, 4), norm=True)
    c.fill(c.m_rect(28, 44 + o, 34, 50 + o), "skin", 2)
    face = c.m_poly([(26, 20 + o), (46, 20 + o), (48, 28 + o), (48, 32 + o), (51, 36 + o), (48, 38 + o), (48, 41 + o),
                     (44, 45 + o), (34, 46 + o), (27, 42 + o)])
    c.fill(face, "skin", 4)
    for y, x in zip(*np.nonzero(face)):
        if y >= 44 + o or x <= 29:
            c.tone[y, x] = 3
    # the hair over the head from the side: the bangs to the brow, a braid in front of the shoulder
    top = c.m_poly([(10, 26 + o), (11, 14 + o), (17, 7 + o), (27, 3 + o), (37, 4 + o), (45, 9 + o), (49, 17 + o),
                    (48, 24 + o), (40, 25 + o), (32, 22 + o), (28, 26 + o), (28, 36 + o), (22, 40 + o)])
    c.fill(top, "hair")
    c.shade_part(top, tones=(2, 3, 3, 4, 4), norm=True)
    _shade_locks(c, [((22, 8 + o), (12, 30 + o), 9, 1.5), ((34, 6 + o), (46, 24 + o), 8, -1.0)], top)
    for k in range(7):
        m = c.m_ellipse(34 + (0.8 if k % 2 else -0.8), 46 + o + 3 * k, 2.4, 2.0)
        c.fill(m, "hair")
        c.shade_part(m, tones=(2, 3, 4, 5), norm=True)
    _pr_circlet(c, 15 + o, 12, 47, front_x=45)
    ear = c.m_ellipse(30, 32 + o, 2.2, 3.2)
    c.fill(ear & ~top, "skin", 3)
    rows = [".eeeee", "e....e"] if blink else PR_EYE_SIDE
    _stamp(c, rows, 41, 29 + o + (3 if blink else 0), PR_INK)
    for x in range(41, 46):
        c.dot(x, 27 + o, PR_INK["n"])
    c.put(50, 36 + o, "skin", 2)
    c.dot(43, 37 + o, PR_INK["r"])
    c.dot(44, 37 + o, PR_INK["r"])
    for x, y in ((45, 41), (46, 42), (47, 41)):
        c.dot(x, y + o, PR_INK["m"])
    return _finish(c, "cape")


def pr_back(oy=0, breath=0, blink=False, sway=0.0, step=0):
    c = Canvas(W, H, PR)
    o = oy + PR_DY
    for x, s in ((26, -step), (38, step)):
        lift = 2 if s < 0 else 0
        c.fill(c.m_rect(x - 3, 92 + o, x + 3, 104 - lift), "stocking", 3)
        _boot(c, x, 111 - lift, 9, 8)
    dr = c.m_poly([(20, 50 + o), (44, 50 + o), (47, 76 + o), (50, 94 + o), (14, 94 + o), (17, 76 + o)])
    c.fill(dr, "dress")
    c.shade_part(dr, tones=(1, 2, 3, 3, 4), norm=True)
    c.fill(c.m_rect(14, 91 + o, 50, 93 + o) & dr, "sash", 3)
    for sx in (13, 51):  # the sleeves at her sides
        a = capsule(c, (sx, 58 + o), (sx + (2 if sx < 32 else -2), 70 + o), 3.0)
        c.fill(a, "dress")
        c.shade_part(a, tones=(2, 3, 4), norm=True)
    # the cape to above the waist, gold rim
    cape = c.m_poly([(12, 50 + o - breath), (52, 50 + o - breath), (56, 58 + o), (54, 70 + o), (10, 70 + o), (8, 58 + o)])
    c.fill(cape, "cape", 3)
    c.shade_part(cape, tones=(2, 3, 3, 4, 4), norm=True)
    for x in range(8, 57):
        ys = np.nonzero(cape[:, x])[0]
        if len(ys):
            c.put(x, int(ys.max()), "gold", 3)
            c.put(x, int(ys.max()) - 1, "gold", 2)
    # the long silver hair over the back to the waist: locks with sheen and dark partings
    # (the hair narrows below the shoulders, so the blue cape shows at both sides, as in v1)
    hb = c.m_poly([(10, 26 + o), (11, 14 + o), (17, 7 + o), (26, 3 + o), (38, 3 + o), (47, 7 + o), (53, 14 + o),
                   (54, 26 + o), (50, 50 + o), (48 + sway, 74 + o), (16 + sway, 74 + o), (14, 50 + o)])
    c.fill(hb, "hair")
    c.shade_part(hb, tones=(1, 2, 3, 3, 4), norm=True)
    _shade_locks(c, [((x0 + 1, 10 + o), (x0 + sway, 73 + o), 9, 0.4) for x0 in (18, 25, 32, 39, 46)], hb)
    for y0 in (24, 26):  # the sheen band across the locks
        for x in range(12, 53):
            if c.mat[y0 + o, x] == c.mid("hair"):
                c.tone[y0 + o, x] = 5 if y0 == 24 else 4
    _pr_circlet(c, 15 + o, 12, 52)
    return _finish(c, "cape")


# ================================================================ the smith

SM = _ramps({
    "hair": ["#3a0c06", "#7a2010", "#b03a1a", "#d85a2a", "#f28a52"],
    "skin": ["#5a3020", "#a86c4a", "#d49a72", "#eab48a", "#f8cca6"],
    "shirt": ["#1e2024", "#4a4e56", "#6c727c", "#8e949e", "#b4bac2"],
    "band": ["#4a4a4e", "#a8a8ac", "#e2e2e4", "#f4f4f6", "#ffffff"],
    "indigo": ["#0a0e24", "#1e2a5a", "#2e4084", "#4a60aa", "#7088cc"],
    "trousers": ["#0e0e12", "#1e1e24", "#2e2e36", "#40404a", "#565662"],
    "apron": ["#140a04", "#3a2210", "#583418", "#764a26", "#946438"],
    "glove": ["#2a1a0c", "#6a4626", "#8e6236", "#ae7e4a", "#cc9c64"],
    "iron": ["#14161c", "#40464f", "#6c7480", "#9aa2ae", "#d4dae2"],
    "wood": ["#1e1008", "#4a2c16", "#6e4424", "#906038", "#b07e50"],
    "boot": ["#1e120a", "#3e2616", "#62402a", "#865c3c", "#a87a52"],
})
SM_INK = {"n": "#3a1408", "e": "#24160e", "k": "#3e2a1a", "m": "#7a3a2c", "#": "#6e6460"}
SM_EYE = ["eeeeee", "ekkkke"]  # narrow, determined


def _sm_band(c, y, x0, x1, knot_x=None):
    """The twisted headband: white and indigo in diagonal turns, a knot with 2 tails at the back."""
    for x in range(x0, x1 + 1):
        for dy in range(4):
            twist = ((x + dy) // 3) % 2
            c.put(x, y + dy, "band" if twist else "indigo", (3 if dy < 2 else 2) if twist else (3 if dy < 2 else 2))
    if knot_x is not None:
        k = c.m_ellipse(knot_x, y + 2, 3, 3)
        c.fill(k, "indigo", 2)
        for dy, tip in ((0, (knot_x - 7, y + 4)), (2, (knot_x - 6, y + 9))):
            t = lock(c, (knot_x - 1, y + 1 + dy), tip, 3, 0.5)
            c.fill(t, "band" if dy else "indigo", 3)


def _sm_hammer(c, x, y):
    """The hammer hanging at his hip: the wooden haft, the iron head."""
    c.fill(c.m_rect(x - 1, y, x + 1, y + 14), "wood", 3)
    c.fill(c.m_rect(x - 1, y, x - 1, y + 14), "wood", 4)
    hd = c.m_rect(x - 4, y + 13, x + 4, y + 17)
    c.fill(hd, "iron", 2)
    c.fill(c.m_rect(x - 4, y + 13, x + 4, y + 13), "iron", 4)


def sm_front(oy=0, breath=0, blink=False, sway=0.0, step=0):
    c = Canvas(W, H, SM)
    o = oy
    # trousers, boots
    for x, s in ((24, -step), (40, step)):
        lift = 2 if s < 0 else 0
        t = c.m_rect(x - 6, 80 + o, x + 6, 102 - lift)
        c.fill(t, "trousers")
        c.shade_part(t, tones=(1, 2, 3, 3), norm=True)
        _boot(c, x, 111 - lift, 14, 10)
    # the grey shirt, broad shoulders
    sh = c.m_poly([(10, 50 + o - breath), (54, 50 + o - breath), (56, 60 + o), (50, 84 + o), (14, 84 + o), (8, 60 + o)])
    c.fill(sh, "shirt")
    c.shade_part(sh, tones=(1, 2, 3, 3, 4), norm=True)
    # the heavy leather apron with its straps and burn marks
    ap = c.m_poly([(18, 56 + o), (46, 56 + o), (48, 96 + o), (16, 96 + o)])
    c.fill(ap, "apron", 3)
    c.shade_part(ap, tones=(1, 2, 3, 3, 4), norm=True)
    for x0 in (20, 44):
        c.fill(c.m_line([(x0, 50 + o), (x0 + (4 if x0 < 32 else -4), 57 + o)], 2.0), "apron", 1)
    for (bx, by) in ((26, 72), (38, 84), (30, 90)):
        c.fill(c.m_ellipse(bx, by + o, 2.0, 1.4), "apron", 0)
    c.fill(c.m_rect(16, 74 + o, 48, 75 + o) & ap, "apron", 1)  # the waist strap
    # arms: rolled sleeves, thick bare forearms, leather gloves
    for side in (-1, 1):
        sx = 32 + side * 21
        sl = capsule(c, (sx, 54 + o), (sx + side, 64 + o), 4.4)
        c.fill(sl, "shirt")
        c.shade_part(sl, tones=(1, 2, 3, 4), norm=True)
        c.fill(c.m_rect(sx - 4, 64 + o, sx + 4, 66 + o) & capsule(c, (sx, 63 + o), (sx, 67 + o), 4.6), "shirt", 4)
        fa = capsule(c, (sx + side, 67 + o), (sx + side * 1.5, 76 + o), 3.8)
        c.fill(fa, "skin")
        c.shade_part(fa, tones=(1, 2, 3, 4), norm=True)
        gl = c.m_ellipse(sx + side * 1.5, 80 + o, 4.4, 4.6)
        c.fill(gl, "glove")
        c.shade_part(gl, tones=(1, 2, 3, 4), norm=True)
    _sm_hammer(c, 13, 82 + o)
    # neck and the square face
    c.fill(c.m_rect(26, 44 + o, 38, 50 + o), "skin", 2)
    face = c.m_poly([(15, 18 + o), (49, 18 + o), (50, 36 + o), (47, 44 + o), (40, 48 + o), (24, 48 + o), (17, 44 + o),
                     (14, 36 + o)])
    c.fill(face, "skin", 3)
    for y, x in zip(*np.nonzero(face)):
        if x >= 46 or y >= 45 + o:
            c.tone[y, x] = 2
    for ex in (13.5, 50.5):
        c.fill(c.m_ellipse(ex, 31 + o, 2.4, 3.8), "skin", 2)
    # red hair cropped short, the headband over it
    hr = c.m_poly([(14, 22 + o), (14, 12 + o), (20, 5 + o), (32, 3 + o), (44, 5 + o), (50, 12 + o), (50, 22 + o)])
    c.fill(hr, "hair")
    c.shade_part(hr, tones=(1, 2, 3, 4, 4), norm=True)
    _shade_locks(c, [((x, 12 + o), (x + 2, 4 + o), 5, 0.3) for x in (20, 26, 32, 38, 44)], hr, tones=(2, 3, 4, 5))
    _sm_band(c, 14 + o, 14, 50)
    # thick straight brows, narrow eyes, soot
    for x0 in (18, 37):
        c.fill(c.m_rect(x0, 25 + o, x0 + 9, 26 + o), "hair", 1)
    if blink:
        for x0 in (19, 38):
            _stamp(c, ["eeeeee"], x0, 30 + o, SM_INK)
    else:
        for x0 in (19, 38):
            _stamp(c, SM_EYE, x0, 29 + o, SM_INK)
    c.fill(c.m_rect(31, 33 + o, 33, 37 + o), "skin", 2)
    c.put(33, 37 + o, "skin", 1)
    for x in range(27, 38):
        c.dot(x, 41 + o, SM_INK["m"])
    for (sx_, sy_) in ((20, 37), (22, 38), (44, 36)):
        c.dot(sx_, sy_ + o, SM_INK["#"])
        c.dot(sx_ + 1, sy_ + o, SM_INK["#"])
    return _finish(c)


def sm_side(oy=0, breath=0, blink=False, sway=0.0, step=0):
    c = Canvas(W, H, SM)
    o = oy
    for dx, near in ((-5 * step, False), (5 * step, True)):
        x = 30 + dx
        t = c.m_rect(x - 5, 80 + o, x + 5, 102)
        c.fill(t, "trousers", 2 if near else 1)
        _boot(c, x, 111, 12, 10, toe=4)
        if not near:
            c.set_tone(c.m_rect(x - 7, 80 + o, x + 11, 111), 1)
    sh = c.m_poly([(18, 50 + o - breath), (42, 50 + o - breath), (46, 60 + o), (44, 84 + o), (18, 84 + o), (16, 60 + o)])
    c.fill(sh, "shirt")
    c.shade_part(sh, tones=(1, 2, 3, 3, 4), norm=True)
    ap = c.m_poly([(38, 56 + o), (45, 56 + o), (48, 96 + o), (41, 96 + o)])
    c.fill(ap, "apron", 3)
    c.shade_part(ap, tones=(1, 2, 3, 4), norm=True)
    c.fill(c.m_rect(18, 74 + o, 46, 75 + o), "apron", 1)
    sl = capsule(c, (30, 54 + o), (30 + 2 * step, 64 + o), 4.6)
    c.fill(sl, "shirt")
    c.shade_part(sl, tones=(1, 2, 3, 4), norm=True)
    fa = capsule(c, (30 + 2 * step, 66 + o), (31 + 4 * step, 76 + o), 3.8)
    c.fill(fa, "skin")
    c.shade_part(fa, tones=(1, 2, 3, 4), norm=True)
    gl = c.m_ellipse(31 + 4 * step, 80 + o, 4.4, 4.6)
    c.fill(gl, "glove")
    c.shade_part(gl, tones=(1, 2, 3, 4), norm=True)
    c.fill(c.m_rect(28, 44 + o, 36, 50 + o), "skin", 2)
    face = c.m_poly([(24, 18 + o), (46, 18 + o), (49, 26 + o), (49, 32 + o), (52, 35 + o), (49, 37 + o), (49, 44 + o),
                     (44, 48 + o), (30, 48 + o), (24, 42 + o)])
    c.fill(face, "skin", 3)
    for y, x in zip(*np.nonzero(face)):
        if y >= 45 + o or x <= 27:
            c.tone[y, x] = 2
    hr = c.m_poly([(14, 26 + o), (14, 12 + o), (20, 5 + o), (32, 3 + o), (42, 5 + o), (48, 12 + o), (48, 20 + o),
                   (28, 22 + o), (26, 32 + o), (18, 32 + o)])
    c.fill(hr, "hair")
    c.shade_part(hr, tones=(1, 2, 3, 4, 4), norm=True)
    _shade_locks(c, [((x, 12 + o), (x - 2, 4 + o), 5, 0.3) for x in (22, 28, 34, 40)], hr, tones=(2, 3, 4, 5))
    ear = c.m_ellipse(29, 31 + o, 2.4, 3.6)
    c.fill(ear, "skin", 2)
    _sm_band(c, 14 + o, 14, 48, knot_x=15)
    c.fill(c.m_rect(38, 25 + o, 46, 26 + o), "hair", 1)
    _stamp(c, ["eeeee"] if blink else ["eeeee", "ekkke"], 40, 29 + o + (1 if blink else 0), SM_INK)
    c.fill(c.m_rect(50, 33 + o, 51, 36 + o), "skin", 2)
    for x in range(44, 49):
        c.dot(x, 41 + o, SM_INK["m"])
    c.dot(38, 37 + o, SM_INK["#"])
    c.dot(39, 37 + o, SM_INK["#"])
    return _finish(c)


def sm_back(oy=0, breath=0, blink=False, sway=0.0, step=0):
    c = Canvas(W, H, SM)
    o = oy
    for x, s in ((24, -step), (40, step)):
        lift = 2 if s < 0 else 0
        t = c.m_rect(x - 6, 80 + o, x + 6, 102 - lift)
        c.fill(t, "trousers")
        c.shade_part(t, tones=(1, 2, 3, 3), norm=True)
        _boot(c, x, 111 - lift, 14, 10)
    sh = c.m_poly([(10, 50 + o - breath), (54, 50 + o - breath), (56, 60 + o), (50, 84 + o), (14, 84 + o), (8, 60 + o)])
    c.fill(sh, "shirt")
    c.shade_part(sh, tones=(1, 2, 3, 3, 4), norm=True)
    for a, b in (((20, 50), (30, 74)), ((44, 50), (34, 74))):  # the apron's straps crossing on the back
        c.fill(c.m_line([(a[0], a[1] + o), (b[0], b[1] + o)], 2.4), "apron", 2)
    c.fill(c.m_rect(14, 74 + o, 50, 77 + o), "apron", 2)
    c.fill(c.m_rect(29, 73 + o, 35, 78 + o), "iron", 3)  # the buckle
    for side in (-1, 1):
        sx = 32 + side * 21
        sl = capsule(c, (sx, 54 + o), (sx + side, 64 + o), 4.4)
        c.fill(sl, "shirt")
        c.shade_part(sl, tones=(1, 2, 3, 4), norm=True)
        fa = capsule(c, (sx + side, 67 + o), (sx + side * 1.5, 76 + o), 3.8)
        c.fill(fa, "skin")
        c.shade_part(fa, tones=(1, 2, 3, 4), norm=True)
        gl = c.m_ellipse(sx + side * 1.5, 80 + o, 4.4, 4.6)
        c.fill(gl, "glove")
        c.shade_part(gl, tones=(1, 2, 3, 4), norm=True)
    _sm_hammer(c, 51, 82 + o)
    c.fill(c.m_rect(26, 44 + o, 38, 50 + o), "skin", 2)
    hr = c.m_poly([(14, 40 + o), (14, 12 + o), (20, 5 + o), (32, 3 + o), (44, 5 + o), (50, 12 + o), (50, 40 + o), (44, 46 + o),
                   (20, 46 + o)])
    c.fill(hr, "hair")
    c.shade_part(hr, tones=(1, 2, 3, 4, 4), norm=True)
    _shade_locks(c, [((x, 18 + o), (x + 1, 44 + o), 6, 0.3) for x in (19, 26, 32, 38, 45)], hr, tones=(2, 3, 3, 4))
    for ex in (13.5, 50.5):
        c.fill(c.m_ellipse(ex, 31 + o, 2.4, 3.8), "skin", 2)
    _sm_band(c, 14 + o, 14, 50)
    k = c.m_ellipse(32, 16 + o, 3.4, 3.0)
    c.fill(k, "indigo", 2)
    for tip in ((28 + sway, 26 + o), (36 + sway, 27 + o)):
        t = lock(c, (32, 18 + o), tip, 3, 0.5)
        c.fill(t, "band", 3)
    return _finish(c)


IDLE = [dict(), dict(breath=1, sway=0.5), dict(breath=1, sway=1.0, oy=1), dict(blink=True, sway=0.5)]
WALK = [dict(step=1, sway=0.5), dict(step=1, oy=1, sway=1.0), dict(step=0, sway=0.5),
        dict(step=-1, sway=-0.5), dict(step=-1, oy=1, sway=-1.0), dict(step=0, sway=-0.5)]
VIEWS = {"princess": {"down": pr_front, "right": pr_side, "up": pr_back},
         "smith": {"down": sm_front, "right": sm_side, "up": sm_back}}


def frames(who, action, view):
    fn = VIEWS[who][view]
    poses = {"idle": IDLE, "walk": WALK}[action]
    return [fn(**{k: v for k, v in p.items() if not (k == "blink" and view == "up")}) for p in poses]
