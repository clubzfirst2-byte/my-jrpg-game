"""v3 NPC production (STYLE order 5), milestone 4: the guard (npc.guard), the merchant (npc.merchant) and the
traveller (npc.traveller). Each from their own parts on the 64 x 112 grid, following the approved v1 design
notes and colours (tools/npc_release/guard.py, merchant.py, traveller.py, read only). Keys, frame counts and
the anchor as the approved v1 ones (idle 4, walk 6; down, right, up, left). Facing left is drawn on its own
(what they hold is one-sided): the side view with near and far swapped, mirrored by the caller.
"""

import math

import numpy as np

from hdkit import capsule, lock
from npc_batch2 import _boot, _finish, _ramps, _shade_locks, _stamp
from npc_batch3 import GOLD, LEATHER, STEEL, WOOD, _blob, _limb
from v3lib import Canvas

W, H = 64, 112


def _crest(c, x, y, r=4.5):
    """The village crest: a gold ring round a four-pointed star (the wind vane of the village)."""
    ring = c.m_ellipse(x, y, r, r) & ~c.m_ellipse(x, y, r - 1.4, r - 1.4)
    c.fill(ring, "gold", 3)
    st = c.m_poly([(x, y - r + 1.5), (x + 0.9, y - 0.9), (x + r - 1.5, y), (x + 0.9, y + 0.9), (x, y + r - 1.5),
                   (x - 0.9, y + 0.9), (x - r + 1.5, y), (x - 0.9, y - 0.9)])
    c.fill(st, "gold", 4)


# ================================================================ the guard

GD = _ramps({
    "hair": ["#160e08", "#3a2414", "#5a3a22", "#7a5434", "#9a7048"],
    "skin": ["#5e3424", "#b47a5a", "#e0aa84", "#f2c4a0", "#ffdcc0"],
    "coat": ["#10161e", "#2e3e50", "#4a6078", "#6a849c", "#98b2c6"],
    "iron": ["#14161c", "#40464f", "#6c7480", "#9aa2ae", "#d4dae2"],
    "cloth": ["#0e0e14", "#1e2028", "#2e3240", "#424858", "#5a6274"],
    "leather": LEATHER, "gold": GOLD, "wood": WOOD,
})
GD_INK = {"n": "#2a1a10", "e": "#1e140c", "k": "#3a4a3a", "m": "#7a3a2c", "z": "#8a6a58"}


def _spear(c, x, top):
    c.fill(c.m_line([(x, top + 10), (x, 110)], 2.0), "wood", 3)
    c.fill(c.m_line([(x - 0.7, top + 10), (x - 0.7, 110)], 0.9), "wood", 4)
    head = c.m_poly([(x, top), (x + 2.6, top + 6), (x + 1.2, top + 10), (x - 1.2, top + 10), (x - 2.6, top + 6)])
    c.fill(head, "iron", 3)
    c.fill(c.m_line([(x - 0.6, top + 1), (x - 0.6, top + 9)], 0.9) & head, "iron", 4)
    c.fill(c.m_rect(x - 2, top + 10, x + 2, top + 11), "iron", 2)


def _gd_helmet(c, o, view, X=0):
    """The iron helmet: a round cap with a brim band, the nose guard in front."""
    if view == "side":
        cap = c.m_poly([(15 + X, 24 + o), (16 + X, 12 + o), (23 + X, 5 + o), (34 + X, 3 + o), (44 + X, 7 + o), (50 + X, 15 + o),
                        (51 + X, 24 + o)])
    else:
        cap = c.m_poly([(12, 25 + o), (13, 13 + o), (20, 6 + o), (32, 3 + o), (44, 6 + o), (51, 13 + o), (52, 25 + o)])
    c.fill(cap, "iron")
    c.shade_part(cap, tones=(1, 2, 3, 4, 4), norm=True)
    c.fill(c.m_rect(10, 22 + o, 54, 25 + o) & cap, "iron", 2)
    c.fill(c.m_rect(10, 22 + o, 54, 22 + o) & cap, "iron", 4)
    for x in range(14, 52, 6):  # rivets on the band
        if cap[23 + o, x]:
            c.put(x, 23 + o, "iron", 4)
    if view == "down":
        c.fill(c.m_rect(31, 22 + o, 33, 36 + o), "iron", 3)
        c.fill(c.m_rect(31, 22 + o, 31, 36 + o), "iron", 4)
    elif view == "side":
        c.fill(c.m_rect(49 + X, 22 + o, 51 + X, 34 + o), "iron", 3)


def gd_front(oy=0, breath=0, blink=False, sway=0.0, step=0):
    c = Canvas(W, H, GD)
    o = oy
    for x, s in ((24, -step), (40, step)):
        lift = 2 if s < 0 else 0
        t = c.m_rect(x - 5, 84 + o, x + 5, 101 - lift)
        c.fill(t, "cloth")
        c.shade_part(t, tones=(1, 2, 3, 3), norm=True)
        _boot(c, x, 111 - lift, 12, 11, mat="leather")
    body = c.m_poly([(12, 50 + o - breath), (52, 50 + o - breath), (54, 64 + o), (50, 90 + o), (14, 90 + o), (10, 64 + o)])
    c.fill(body, "cloth")
    c.shade_part(body, tones=(1, 2, 2, 3), norm=True)
    sc = c.m_poly([(18, 54 + o), (46, 54 + o), (48, 92 + o), (16, 92 + o)])  # the surcoat
    c.fill(sc, "coat")
    c.shade_part(sc, tones=(1, 2, 3, 3, 4), norm=True)
    c.fill(c.m_rect(16, 90 + o, 48, 91 + o) & sc, "coat", 1)
    c.fill(c.m_rect(18, 74 + o, 46, 76 + o), "leather", 2)  # the belt and its buckle
    c.fill(c.m_rect(30, 73 + o, 34, 77 + o), "gold", 3)
    _crest(c, 32, 64 + o)
    bp = c.m_poly([(22, 50 + o - breath), (42, 50 + o - breath), (44, 56 + o), (20, 56 + o)])  # breastplate's top
    c.fill(bp, "iron")
    c.shade_part(bp, tones=(2, 3, 4, 4), norm=True)
    for side in (-1, 1):
        sx = 32 + side * 19
        pd = c.m_ellipse(sx, 54 + o - breath, 7, 5.5) & c.m_rect(0, 0, W - 1, 58 + o)  # pauldrons
        c.fill(pd, "iron")
        c.shade_part(pd, tones=(1, 2, 3, 4, 5), norm=True)
        c.fill(c.m_line([(sx - 6, 57 + o), (sx + 6, 57 + o)], 1.2) & pd, "iron", 1)
        _limb(c, (sx + side, 59 + o), (sx + side * 2, 72 + o), 3.8, "cloth")
        _limb(c, (sx + side * 2, 70 + o), (sx + side * 2, 78 + o), 3.6, "leather")  # the bracer
        _blob(c, sx + side * 2, 81 + o, 3.4, 3.4, "skin", (1, 2, 3, 4))
    _spear(c, 11, 16 + o)  # in his right hand (the image's left)
    _blob(c, 11, 81 + o, 3.4, 3.4, "skin", (1, 2, 3, 4))
    c.fill(c.m_rect(27, 44 + o, 37, 50 + o), "skin", 2)
    face = c.m_poly([(16, 22 + o), (48, 22 + o), (49, 34 + o), (46, 42 + o), (38, 47 + o), (26, 47 + o), (18, 42 + o),
                     (15, 34 + o)])
    c.fill(face, "skin", 3)
    for y, x in zip(*np.nonzero(face)):
        if x >= 46 or y >= 45 + o:
            c.tone[y, x] = 2
    for (x, y) in ((20, 41), (23, 43), (27, 45), (37, 45), (41, 43), (44, 41), (30, 44), (34, 44)):  # stubble
        c.dot(x, y + o, GD_INK["z"])
    _gd_helmet(c, o, "down")
    for x0 in (19, 37):
        c.fill(c.m_rect(x0, 28 + o, x0 + 7, 29 + o), "hair", 1)
        _stamp(c, ["eeeeee"] if blink else ["eeeeee", "ekkkke"], x0 + 1, 31 + o, GD_INK)
    for x in range(28, 37):
        c.dot(x, 41 + o, GD_INK["m"])
    return _finish(c, "coat")


def gd_side(oy=0, breath=0, blink=False, sway=0.0, step=0, left=False):
    c = Canvas(W, H, GD)
    o = oy
    for dx, near in ((-5 * step, False), (5 * step, True)):
        x = 30 + dx
        t = c.m_rect(x - 5, 84 + o, x + 5, 101)
        c.fill(t, "cloth", 2 if near else 1)
        _boot(c, x, 111, 11, 11, mat="leather", toe=4)
        if not near:
            c.set_tone(c.m_rect(x - 7, 84 + o, x + 11, 111), 1)
    body = c.m_poly([(20, 50 + o - breath), (40, 50 + o - breath), (44, 64 + o), (42, 90 + o), (18, 90 + o), (16, 64 + o)])
    c.fill(body, "cloth")
    c.shade_part(body, tones=(1, 2, 2, 3), norm=True)
    sc = c.m_poly([(22, 54 + o), (42, 54 + o), (44, 92 + o), (20, 92 + o)])
    c.fill(sc, "coat")
    c.shade_part(sc, tones=(1, 2, 3, 3, 4), norm=True)
    c.fill(c.m_rect(20, 74 + o, 44, 76 + o), "leather", 2)
    pd = c.m_ellipse(30, 54 + o - breath, 7, 5.5) & c.m_rect(0, 0, W - 1, 58 + o)
    c.fill(pd, "iron")
    c.shade_part(pd, tones=(1, 2, 3, 4, 5), norm=True)
    _spear(c, 46, 16 + o)  # held upright in front of him (the near hand facing left, the far one facing right)
    _limb(c, (31, 59 + o), (40, 72 + o), 3.8, "cloth")
    _limb(c, (40, 70 + o), (44, 78 + o), 3.4, "leather")
    _blob(c, 46, 80 + o, 3.4, 3.4, "skin", (1, 2, 3, 4))
    c.fill(c.m_rect(28, 44 + o, 36, 50 + o), "skin", 2)
    face = c.m_poly([(24, 22 + o), (46, 22 + o), (48, 30 + o), (48, 33 + o), (52, 36 + o), (48, 39 + o), (48, 43 + o),
                     (42, 47 + o), (30, 47 + o), (24, 42 + o)])
    c.fill(face, "skin", 3)
    for y, x in zip(*np.nonzero(face)):
        if y >= 45 + o or x <= 27:
            c.tone[y, x] = 2
    _blob(c, 28, 32 + o, 2.4, 3.6, "skin", (1, 2, 3))
    hr = c.m_poly([(16, 24 + o), (26, 24 + o), (26, 34 + o), (18, 32 + o)])
    c.fill(hr, "hair")
    c.shade_part(hr, tones=(1, 2, 3), norm=True)
    for (x, y) in ((40, 43), (43, 44), (46, 42)):
        c.dot(x, y + o, GD_INK["z"])
    _gd_helmet(c, o, "side")
    c.fill(c.m_rect(39, 28 + o, 46, 29 + o), "hair", 1)
    _stamp(c, ["eeeee"] if blink else ["eeeee", "ekkke"], 40, 31 + o, GD_INK)
    for x in range(44, 48):
        c.dot(x, 41 + o, GD_INK["m"])
    return _finish(c, "coat")


def gd_back(oy=0, breath=0, blink=False, sway=0.0, step=0):
    c = Canvas(W, H, GD)
    o = oy
    _spear(c, 53, 16 + o)  # in his right hand: the image's right from behind
    for x, s in ((24, -step), (40, step)):
        lift = 2 if s < 0 else 0
        t = c.m_rect(x - 5, 84 + o, x + 5, 101 - lift)
        c.fill(t, "cloth")
        c.shade_part(t, tones=(1, 2, 3, 3), norm=True)
        _boot(c, x, 111 - lift, 12, 11, mat="leather")
    body = c.m_poly([(12, 50 + o - breath), (52, 50 + o - breath), (54, 64 + o), (50, 90 + o), (14, 90 + o), (10, 64 + o)])
    c.fill(body, "cloth")
    c.shade_part(body, tones=(1, 2, 2, 3), norm=True)
    sc = c.m_poly([(16, 52 + o), (48, 52 + o), (50, 92 + o), (14, 92 + o)])
    c.fill(sc, "coat")
    c.shade_part(sc, tones=(1, 2, 3, 3, 4), norm=True)
    c.fill(c.m_rect(16, 74 + o, 48, 76 + o), "leather", 2)
    _crest(c, 32, 64 + o)
    for side in (-1, 1):
        sx = 32 + side * 19
        pd = c.m_ellipse(sx, 54 + o - breath, 7, 5.5) & c.m_rect(0, 0, W - 1, 58 + o)
        c.fill(pd, "iron")
        c.shade_part(pd, tones=(1, 2, 3, 4, 5), norm=True)
        _limb(c, (sx + side, 59 + o), (sx + side * 2, 72 + o), 3.8, "cloth")
        _limb(c, (sx + side * 2, 70 + o), (sx + side * 2, 78 + o), 3.6, "leather")
        _blob(c, sx + side * 2, 81 + o, 3.4, 3.4, "skin", (1, 2, 3, 4))
    c.fill(c.m_rect(27, 44 + o, 37, 50 + o), "skin", 2)
    hr = c.m_poly([(15, 24 + o), (49, 24 + o), (48, 40 + o), (42, 46 + o), (22, 46 + o), (16, 40 + o)])
    c.fill(hr, "hair")
    c.shade_part(hr, tones=(1, 2, 3, 3), norm=True)
    _shade_locks(c, [((x, 26 + o), (x + 1, 44 + o), 6, 0.3) for x in (20, 27, 33, 39, 45)], hr, tones=(1, 2, 3, 3))
    for ex in (13.5, 50.5):
        _blob(c, ex, 32 + o, 2.4, 3.6, "skin", (1, 2, 3))
    _gd_helmet(c, o, "up")
    return _finish(c, "coat")


# ================================================================ the merchant

MC = _ramps({
    "hair": ["#0c0b12", "#211f2c", "#353346", "#4d4b64", "#6c6a88"],
    "skin": ["#6a3a28", "#c48a66", "#eeba92", "#fcd2ac", "#ffe8d0"],
    "vest": ["#22070c", "#5c1622", "#8a2632", "#b2404a", "#d4686c"],
    "shirt": ["#4a4640", "#a8a296", "#e4e0d6", "#f6f4ee", "#ffffff"],
    "trousers": ["#2c1c08", "#6a4618", "#986a28", "#bc8c3e", "#dcb466"],
    "cover": ["#3a3226", "#a49478", "#d8cca8", "#ece2c4", "#fffaea"],
    "leather": LEATHER, "gold": GOLD, "wood": WOOD,
})
MC_INK = {"n": "#1a1824", "e": "#1e1a24", "m": "#8a3a34", "r": "#f09a86", "w": "#ffffff", "g": "#2a2834"}


def _book(c, x, y):
    """The account book: a cream cover, a dark binding, its page edges."""
    b = c.m_rect(x - 5, y - 6, x + 5, y + 6)
    c.fill(b, "cover", 3)
    c.shade_part(b, tones=(2, 3, 3, 4), norm=True)
    c.fill(c.m_rect(x - 5, y - 6, x - 4, y + 6), "leather", 1)
    for yy in (y - 2, y + 2):
        c.fill(c.m_rect(x - 2, yy, x + 3, yy), "cover", 1)


def _glasses(c, centres, y):
    for cx in centres:
        ring = c.m_ellipse(cx, y, 4.2, 3.6) & ~c.m_ellipse(cx, y, 3.0, 2.4)
        for yy, xx in zip(*np.nonzero(ring)):
            c.dot(int(xx), int(yy), MC_INK["g"])
        c.dot(int(cx) + 1, y - 1, MC_INK["w"])


def mc_front(oy=0, breath=0, blink=False, sway=0.0, step=0):
    c = Canvas(W, H, MC)
    o = oy
    for x, s in ((24, -step), (40, step)):
        lift = 2 if s < 0 else 0
        t = c.m_rect(x - 6, 82 + o, x + 6, 103 - lift)
        c.fill(t, "trousers")
        c.shade_part(t, tones=(1, 2, 3, 3, 4), norm=True)
        _boot(c, x, 111 - lift, 12, 8, mat="leather")
    sh = c.m_poly([(12, 50 + o - breath), (52, 50 + o - breath), (56, 64 + o), (54, 84 + o), (10, 84 + o), (8, 64 + o)])
    c.fill(sh, "shirt")
    c.shade_part(sh, tones=(1, 2, 3, 3, 4), norm=True)
    vt = c.m_poly([(16, 52 + o), (28, 52 + o), (32, 64 + o), (36, 52 + o), (48, 52 + o), (52, 66 + o), (50, 84 + o),
                   (14, 84 + o), (12, 66 + o)])
    c.fill(vt, "vest")
    c.shade_part(vt, tones=(1, 2, 3, 3, 4), norm=True)
    for y in (66, 72, 78):  # gold buttons
        c.fill(c.m_ellipse(34.5, y + o, 1.4, 1.4), "gold", 4)
    c.fill(c.m_rect(10, 82 + o, 54, 85 + o), "leather", 2)
    c.fill(c.m_rect(29, 81 + o, 35, 86 + o), "gold", 3)
    _blob(c, 15, 90 + o, 6, 6, "leather", (1, 2, 3, 4))  # the purse on his right hip
    c.fill(c.m_rect(10, 86 + o, 20, 87 + o), "leather", 4)
    for side in (-1, 1):
        sx = 32 + side * 22
        _limb(c, (sx, 54 + o), (sx + side * 0.5, 64 + o), 4.4, "shirt")
        c.fill(capsule(c, (sx, 63 + o), (sx, 66 + o), 4.6), "shirt", 4)
    _limb(c, (10, 67 + o), (11, 78 + o), 3.6, "skin")
    _blob(c, 11, 81 + o, 3.6, 3.6, "skin", (1, 2, 3, 4))
    _limb(c, (54, 67 + o), (50, 74 + o), 3.6, "skin")  # his left hand holding the book at the chest
    _book(c, 47, 72 + o)
    _blob(c, 50, 76 + o, 3.2, 3.0, "skin", (2, 3, 4))
    c.fill(c.m_rect(26, 44 + o, 38, 50 + o), "skin", 2)
    face = c.m_poly([(13, 22 + o), (51, 22 + o), (53, 34 + o), (49, 43 + o), (40, 48 + o), (24, 48 + o), (15, 43 + o),
                     (11, 34 + o)])
    c.fill(face, "skin", 3)
    for y, x in zip(*np.nonzero(face)):
        if x >= 49 or y >= 46 + o:
            c.tone[y, x] = 2
    for ex in (10.5, 53.5):
        _blob(c, ex, 32 + o, 2.4, 3.6, "skin", (1, 2, 3))
    hr = c.m_poly([(12, 28 + o), (12, 14 + o), (18, 7 + o), (32, 4 + o), (46, 7 + o), (52, 14 + o), (52, 28 + o),
                   (48, 22 + o), (16, 22 + o)])
    c.fill(hr, "hair")
    c.shade_part(hr, tones=(1, 2, 3, 4, 4), norm=True)
    _shade_locks(c, [((x, 18 + o), (x + 3, 8 + o), 6, 0.5) for x in (18, 25, 32, 39, 46)], hr, tones=(1, 2, 3, 4))
    c.fill(c.m_line([(8, 26 + o), (16, 20 + o)], 1.4), "wood", 3)  # the pen behind his right ear
    for x0 in (18, 38):
        c.fill(c.m_rect(x0, 27 + o, x0 + 7, 28 + o), "hair", 2)
        _stamp(c, ["eeeee"] if blink else [".eee.", "e...e"], x0 + 1, 31 + o, MC_INK)
    _glasses(c, (21.5, 41.5), 32 + o)
    _blob(c, 32, 36 + o, 2.4, 2.2, "skin", (2, 3, 4))
    must = c.m_poly([(24, 39 + o), (40, 39 + o), (42, 42 + o), (34, 41 + o), (32, 42 + o), (30, 41 + o), (22, 42 + o)])
    c.fill(must, "hair", 1)
    for x in range(26, 39):
        c.dot(x, 44 + o - (1 if x in (26, 38) else 0), MC_INK["m"])
    for bx in (16, 45):
        c.dot(bx, 38 + o, MC_INK["r"])
        c.dot(bx + 1, 38 + o, MC_INK["r"])
    return _finish(c)


def mc_side(oy=0, breath=0, blink=False, sway=0.0, step=0, left=False):
    c = Canvas(W, H, MC)
    o = oy
    for dx, near in ((-5 * step, False), (5 * step, True)):
        x = 30 + dx
        t = c.m_rect(x - 5, 82 + o, x + 5, 103)
        c.fill(t, "trousers", 3 if near else 2)
        _boot(c, x, 111, 11, 8, mat="leather", toe=4)
        if not near:
            c.set_tone(c.m_rect(x - 7, 82 + o, x + 11, 111), 1)
    if not left:  # facing right: the purse (right hip) on the far side
        _blob(c, 20, 88 + o, 5, 5, "leather", (1, 1, 2, 3))
    sh = c.m_poly([(18, 50 + o - breath), (40, 50 + o - breath), (46, 64 + o), (46, 78 + o), (42, 84 + o), (16, 84 + o),
                   (14, 64 + o)])
    c.fill(sh, "shirt")
    c.shade_part(sh, tones=(1, 2, 3, 3, 4), norm=True)
    vt = c.m_poly([(18, 52 + o), (38, 52 + o), (42, 64 + o), (44, 82 + o), (16, 84 + o), (14, 64 + o)])
    c.fill(vt, "vest")
    c.shade_part(vt, tones=(1, 2, 3, 3, 4), norm=True)
    for y in (66, 72, 78):
        c.fill(c.m_ellipse(41, y + o, 1.2, 1.2), "gold", 4)
    c.fill(c.m_rect(14, 82 + o, 46, 85 + o), "leather", 2)
    if left:  # facing left: the purse on the near hip
        _blob(c, 36, 89 + o, 5.5, 5.5, "leather", (1, 2, 3, 4))
    _limb(c, (29, 54 + o), (30, 64 + o), 4.4, "shirt")
    c.fill(capsule(c, (30, 63 + o), (30, 66 + o), 4.6), "shirt", 4)
    _limb(c, (30, 67 + o), (40, 72 + o), 3.6, "skin")
    if not left:  # the book in his left hand: the near hand facing right
        _book(c, 44, 70 + o)
    _blob(c, 41, 73 + o, 3.2, 3.0, "skin", (2, 3, 4))
    c.fill(c.m_rect(28, 44 + o, 36, 50 + o), "skin", 2)
    face = c.m_poly([(22, 20 + o), (46, 20 + o), (49, 28 + o), (49, 32 + o), (53, 36 + o), (49, 39 + o), (49, 43 + o),
                     (44, 48 + o), (30, 48 + o), (22, 42 + o)])
    c.fill(face, "skin", 3)
    for y, x in zip(*np.nonzero(face)):
        if y >= 46 + o or x <= 25:
            c.tone[y, x] = 2
    hr = c.m_poly([(14, 30 + o), (14, 14 + o), (20, 7 + o), (32, 4 + o), (44, 7 + o), (49, 14 + o), (48, 20 + o),
                   (30, 22 + o), (28, 34 + o), (20, 36 + o)])
    c.fill(hr, "hair")
    c.shade_part(hr, tones=(1, 2, 3, 4, 4), norm=True)
    _blob(c, 27, 32 + o, 2.4, 3.6, "skin", (1, 2, 3))
    if left:  # the pen behind his right ear: seen facing left
        c.fill(c.m_line([(24, 30 + o), (31, 24 + o)], 1.4), "wood", 3)
    c.fill(c.m_rect(38, 27 + o, 45, 28 + o), "hair", 2)
    _stamp(c, ["eeee"] if blink else [".ee.", "e..e"], 40, 31 + o, MC_INK)
    _glasses(c, (42,), 32 + o)
    _blob(c, 51, 35 + o, 2.4, 2.2, "skin", (2, 3, 4))
    c.fill(c.m_poly([(44, 39 + o), (52, 39 + o), (51, 42 + o), (45, 41 + o)]), "hair", 1)
    for x, y in ((45, 44), (46, 44), (47, 43)):
        c.dot(x, y + o, MC_INK["m"])
    return _finish(c)


def mc_back(oy=0, breath=0, blink=False, sway=0.0, step=0):
    c = Canvas(W, H, MC)
    o = oy
    for x, s in ((24, -step), (40, step)):
        lift = 2 if s < 0 else 0
        t = c.m_rect(x - 6, 82 + o, x + 6, 103 - lift)
        c.fill(t, "trousers")
        c.shade_part(t, tones=(1, 2, 3, 3, 4), norm=True)
        _boot(c, x, 111 - lift, 12, 8, mat="leather")
    _book(c, 13, 72 + o)  # in his left hand: the image's left from behind
    sh = c.m_poly([(12, 50 + o - breath), (52, 50 + o - breath), (56, 64 + o), (54, 84 + o), (10, 84 + o), (8, 64 + o)])
    c.fill(sh, "shirt")
    c.shade_part(sh, tones=(1, 2, 3, 3, 4), norm=True)
    vt = c.m_poly([(14, 52 + o), (50, 52 + o), (52, 66 + o), (50, 84 + o), (14, 84 + o), (12, 66 + o)])
    c.fill(vt, "vest")
    c.shade_part(vt, tones=(1, 2, 3, 3, 4), norm=True)
    c.fill(c.m_rect(10, 82 + o, 54, 85 + o), "leather", 2)
    _blob(c, 49, 90 + o, 6, 6, "leather", (1, 2, 3, 4))  # the purse on his right hip
    for side in (-1, 1):
        sx = 32 + side * 22
        _limb(c, (sx, 54 + o), (sx + side * 0.5, 64 + o), 4.4, "shirt")
        _limb(c, (sx + side * 0.5, 67 + o), (sx + side, 78 + o), 3.6, "skin")
        _blob(c, sx + side, 81 + o, 3.6, 3.6, "skin", (1, 2, 3, 4))
    c.fill(c.m_rect(26, 44 + o, 38, 50 + o), "skin", 2)
    hr = c.m_poly([(12, 34 + o), (12, 14 + o), (18, 7 + o), (32, 4 + o), (46, 7 + o), (52, 14 + o), (52, 34 + o), (46, 44 + o),
                   (18, 44 + o)])
    c.fill(hr, "hair")
    c.shade_part(hr, tones=(1, 2, 3, 4, 4), norm=True)
    _shade_locks(c, [((x, 12 + o), (x + 1, 42 + o), 7, 0.3) for x in (18, 25, 32, 39, 46)], hr, tones=(1, 2, 3, 4))
    for ex in (10.5, 53.5):
        _blob(c, ex, 32 + o, 2.4, 3.6, "skin", (1, 2, 3))
    c.fill(c.m_line([(48, 26 + o), (56, 20 + o)], 1.4), "wood", 3)  # the pen's end behind his right ear
    return _finish(c)


# ================================================================ the traveller

TR = _ramps({
    "skin": ["#5a2e1c", "#bc7c56", "#daa47a", "#ecbc92", "#f8d2aa"],
    "hair": ["#34343c", "#6e6e78", "#9c9ca4", "#c2c2c8", "#e6e6ea"],
    "hat": ["#16140e", "#363226", "#524c3a", "#6e6850", "#8c866a"],
    "coat": ["#241e16", "#4c4030", "#6a5a44", "#86745c", "#a49278"],
    "pack": ["#28140a", "#5e3420", "#824c2e", "#a06642", "#bc845c"],
    "jacket": ["#22242a", "#4a4e56", "#6a6e76", "#888c94", "#a8acb2"],
    "scarf": ["#2c0610", "#6a1424", "#962234", "#bc3848", "#de6a74"],
    "bedroll": ["#141c10", "#34442a", "#4e6240", "#6a7e58", "#8c9e78"],
    "gourd": ["#3a2608", "#86601e", "#b4862e", "#d4a84a", "#ecc878"],
    "leather": LEATHER, "wood": WOOD,
})
TR_INK = {"e": "#2a1a12", "k": "#5a7a6a", "m": "#7a3a2c", "l": "#a86a48"}


def _stick(c, x, gourd=True):
    c.fill(c.m_line([(x, 14), (x, 110)], 2.0), "wood", 3)
    c.fill(c.m_line([(x - 0.7, 14), (x - 0.7, 110)], 0.9), "wood", 4)
    if gourd:
        _blob(c, x + 3.5, 30, 3.0, 3.6, "gourd", (1, 2, 3, 4))
        _blob(c, x + 3.5, 25.5, 1.8, 1.8, "gourd", (2, 3, 4))
        c.fill(c.m_line([(x, 22), (x + 3.5, 24)], 1.0), "leather", 2)


def _tr_hat(c, o, view, X=0):
    """The wide-brimmed hat with its crimson band; its crown reaches the frame's top."""
    if view == "side":
        brim = c.m_poly([(8 + X, 16 + o), (56 + X, 15 + o), (58 + X, 18 + o), (8 + X, 20 + o)])
        crown = c.m_poly([(18 + X, 16 + o), (20 + X, 6 + o), (28 + X, 3 + o), (40 + X, 3 + o), (46 + X, 8 + o), (47 + X, 16 + o)])
    else:
        brim = c.m_poly([(4, 16 + o), (60, 16 + o), (61, 20 + o), (3, 20 + o)])
        crown = c.m_poly([(16, 16 + o), (18, 6 + o), (26, 3 + o), (38, 3 + o), (46, 6 + o), (48, 16 + o)])
    c.fill(crown, "hat")
    c.shade_part(crown, tones=(1, 2, 3, 4), norm=True)
    c.fill(c.m_rect(0, 12 + o, W - 1, 15 + o) & crown, "scarf", 2)
    c.fill(c.m_rect(0, 12 + o, W - 1, 12 + o) & crown, "scarf", 4)
    c.fill(brim, "hat", 2)
    c.fill(brim & c.m_rect(0, 16 + o, W - 1, 16 + o), "hat", 4)


def tr_front(oy=0, breath=0, blink=False, sway=0.0, step=0):
    c = Canvas(W, H, TR)
    o = oy
    _blob(c, 50, 44 + o, 6, 8, "bedroll", (1, 2, 3, 4))  # the bedroll on the pack, over his shoulder
    for x, s in ((26, -step), (38, step)):
        lift = 2 if s < 0 else 0
        t = c.m_rect(x - 4, 84 + o, x + 4, 102 - lift)
        c.fill(t, "jacket", 1)
        _boot(c, x, 111 - lift, 10, 8, mat="leather")
    coat = c.m_poly([(12, 48 + o - breath), (52, 48 + o - breath), (54, 64 + o), (56, 100 + sway), (8, 100 - sway), (10, 64 + o)])
    c.fill(coat, "coat")
    c.shade_part(coat, tones=(1, 2, 3, 3, 4), norm=True)
    for y in range(97, 101):  # the worn hem
        for x in range(W):
            if coat[y, x] and (x * 7 + y) % 5 == 0:
                c.put(x, y, "coat", 1)
    jk = c.m_poly([(24, 48 + o), (40, 48 + o), (40, 86 + o), (24, 86 + o)])  # the open front: the grey jacket
    c.fill(jk, "jacket")
    c.shade_part(jk, tones=(1, 2, 3, 3), norm=True)
    for x0, x1 in ((24, 22), (40, 42)):
        c.fill(c.m_line([(x0, 50 + o), (x1, 99)], 1.2), "coat", 1)
    sc = c.m_ellipse(32, 48 + o, 10, 3.6)  # the crimson scarf, one end hanging on the chest
    c.fill(sc, "scarf")
    c.shade_part(sc, tones=(2, 3, 4), norm=True)
    end = lock(c, (35, 50 + o), (37 + sway, 66 + o), 5, -0.5)
    c.fill(end, "scarf")
    c.shade_part(end, tones=(1, 2, 3, 4), norm=True)
    for side in (-1, 1):
        sx = 32 + side * 20
        _limb(c, (sx, 52 + o), (sx + side, 74 + o), 4.0, "coat")
        _blob(c, sx + side, 78 + o, 3.2, 3.4, "skin", (1, 2, 3, 4))
    _stick(c, 11)  # held upright at his right side (the image's left), the gourd near its top
    c.fill(c.m_rect(28, 40 + o, 36, 46 + o), "skin", 2)
    face = c.m_poly([(19, 18 + o), (45, 18 + o), (46, 30 + o), (43, 38 + o), (36, 43 + o), (28, 43 + o), (21, 38 + o),
                     (18, 30 + o)])
    c.fill(face, "skin", 3)
    for y, x in zip(*np.nonzero(face)):
        if y <= 22 + o or x >= 44:
            c.tone[y, x] = 2  # the hat's shadow
    for side in (-1, 1):  # grey hair at the sides, a white streak at the temple
        h_ = lock(c, (32 + side * 13, 18 + o), (32 + side * 15, 36 + o), 6, side * 0.5)
        c.fill(h_, "hair")
        c.shade_part(h_, tones=(1, 2, 3, 4), norm=True)
    c.fill(c.m_rect(19, 19 + o, 20, 26 + o), "hair", 4)
    for x0 in (23, 35):  # narrow eyes, one grey-green iris texel, the shadow under the lids
        _stamp(c, ["eeeeee"] if blink else ["eeeeee", "..k..."], x0, 27 + o, TR_INK)
        c.put(x0 + 1, 29 + o, "skin", 1)
        c.put(x0 + 2, 29 + o, "skin", 1)
    c.fill(c.m_line([(32, 28 + o), (32, 34 + o)], 1.0), "skin", 2)  # the thin nose
    for (x0, x1) in ((22, 24), (40, 42)):  # the deep lines on the cheeks
        c.dot(x0, 34 + o, TR_INK["l"])
        c.dot(x1, 36 + o, TR_INK["l"])
    for x in range(29, 36):
        c.dot(x, 38 + o, TR_INK["m"])
    _tr_hat(c, o, "down")
    return _finish(c, "coat")


def tr_side(oy=0, breath=0, blink=False, sway=0.0, step=0, left=False):
    c = Canvas(W, H, TR)
    o = oy
    for dx, near in ((-5 * step, False), (5 * step, True)):
        x = 32 + dx
        t = c.m_rect(x - 4, 84 + o, x + 4, 102)
        c.fill(t, "jacket", 1)
        _boot(c, x, 111, 9, 8, mat="leather", toe=4)
    pack = c.m_rect(10, 50 + o, 20, 76 + o)  # the backpack and the bedroll on top
    c.fill(pack, "pack")
    c.shade_part(pack, tones=(1, 2, 3, 4), norm=True)
    c.fill(c.m_rect(10, 60 + o, 20, 61 + o), "pack", 1)
    _blob(c, 15, 47 + o, 7, 4.5, "bedroll", (1, 2, 3, 4))
    coat = c.m_poly([(20, 48 + o - breath), (40, 48 + o - breath), (44, 64 + o), (46 + sway, 100), (16 + sway, 100), (18, 64 + o)])
    c.fill(coat, "coat")
    c.shade_part(coat, tones=(1, 2, 3, 3, 4), norm=True)
    jk = c.m_poly([(38, 50 + o), (42, 52 + o), (44, 86 + o), (40, 86 + o)])
    c.fill(jk, "jacket", 2)
    c.fill(c.m_line([(26, 50 + o), (34, 60 + o)], 3.0), "leather", 2)  # the pack's strap
    sc = c.m_ellipse(34, 48 + o, 7, 3.4)
    c.fill(sc, "scarf")
    c.shade_part(sc, tones=(2, 3, 4), norm=True)
    end = lock(c, (39, 50 + o), (42 + sway, 64 + o), 4, -0.5)
    c.fill(end, "scarf")
    c.shade_part(end, tones=(1, 2, 3, 4), norm=True)
    _limb(c, (30, 52 + o), (38, 72 + o), 4.0, "coat")
    _stick(c, 44)  # held upright in front of him in both side views (v1)
    _blob(c, 40, 75 + o, 3.2, 3.4, "skin", (1, 2, 3, 4))
    c.fill(c.m_rect(28, 40 + o, 36, 46 + o), "skin", 2)
    face = c.m_poly([(26, 18 + o), (44, 18 + o), (46, 26 + o), (46, 29 + o), (50, 33 + o), (46, 35 + o), (45, 39 + o),
                     (40, 43 + o), (30, 43 + o), (26, 38 + o)])
    c.fill(face, "skin", 3)
    for y, x in zip(*np.nonzero(face)):
        if y <= 22 + o or x <= 28:
            c.tone[y, x] = 2
    tail = lock(c, (24, 22 + o), (17, 44 + o + sway), 6, 1.0)  # the grey tail tied at the back
    c.fill(tail, "hair")
    c.shade_part(tail, tones=(1, 2, 3, 4), norm=True)
    hs = c.m_poly([(20, 18 + o), (30, 18 + o), (30, 34 + o), (24, 36 + o), (20, 28 + o)])
    c.fill(hs, "hair")
    c.shade_part(hs, tones=(1, 2, 3, 4), norm=True)
    c.fill(c.m_rect(28, 19 + o, 29, 26 + o), "hair", 4)
    _blob(c, 30, 28 + o, 2.2, 3.2, "skin", (1, 2, 3))
    _stamp(c, ["eeeee"] if blink else ["eeeee", "...k."], 39, 26 + o, TR_INK)
    c.dot(38, 33 + o, TR_INK["l"])
    for x in range(42, 46):
        c.dot(x, 38 + o, TR_INK["m"])
    _tr_hat(c, o, "side")
    return _finish(c, "coat")


def tr_back(oy=0, breath=0, blink=False, sway=0.0, step=0):
    c = Canvas(W, H, TR)
    o = oy
    _stick(c, 53, gourd=False)  # in his right hand: the image's right from behind
    for x, s in ((26, -step), (38, step)):
        lift = 2 if s < 0 else 0
        t = c.m_rect(x - 4, 84 + o, x + 4, 102 - lift)
        c.fill(t, "jacket", 1)
        _boot(c, x, 111 - lift, 10, 8, mat="leather")
    coat = c.m_poly([(12, 48 + o - breath), (52, 48 + o - breath), (54, 64 + o), (56 + sway, 100), (8 + sway, 100), (10, 64 + o)])
    c.fill(coat, "coat")
    c.shade_part(coat, tones=(1, 2, 3, 3, 4), norm=True)
    for side in (-1, 1):
        sx = 32 + side * 20
        _limb(c, (sx, 52 + o), (sx + side, 74 + o), 4.0, "coat")
        _blob(c, sx + side, 78 + o, 3.2, 3.4, "skin", (1, 2, 3, 4))
    pack = c.m_rect(20, 52 + o, 44, 80 + o)  # the backpack, its flap, the bedroll rolled on top
    c.fill(pack, "pack")
    c.shade_part(pack, tones=(1, 2, 3, 4), norm=True)
    c.fill(c.m_rect(20, 52 + o, 44, 60 + o), "pack", 3)
    c.fill(c.m_rect(20, 60 + o, 44, 61 + o), "pack", 1)
    c.fill(c.m_rect(31, 58 + o, 33, 63 + o), "leather", 2)
    br = c.m_ellipse(32, 48 + o, 15, 4.5)
    c.fill(br, "bedroll")
    c.shade_part(br, tones=(1, 2, 3, 4), norm=True)
    for x in (24, 40):
        c.fill(c.m_rect(x, 44 + o, x + 1, 52 + o), "leather", 2)
    hb = c.m_poly([(19, 18 + o), (45, 18 + o), (46, 34 + o), (40, 40 + o), (24, 40 + o), (18, 34 + o)])
    c.fill(hb, "hair")
    c.shade_part(hb, tones=(1, 2, 3, 4), norm=True)
    tail = lock(c, (32, 30 + o), (32 + sway, 46 + o), 6, 0.5)
    c.fill(tail, "hair")
    c.shade_part(tail, tones=(2, 3, 4), norm=True)
    c.fill(c.m_rect(30, 32 + o, 34, 33 + o), "leather", 2)  # the tie
    _tr_hat(c, o, "up")
    return _finish(c, "coat")


# ================================================================ the frames

IDLE = [dict(), dict(breath=1, sway=0.5), dict(breath=1, sway=1.0, oy=1), dict(blink=True, sway=0.5)]
WALK = [dict(step=1, sway=0.5), dict(step=1, oy=1, sway=1.0), dict(step=0, sway=0.5),
        dict(step=-1, sway=-0.5), dict(step=-1, oy=1, sway=-1.0), dict(step=0, sway=-0.5)]
VIEWS = {"guard": (gd_front, gd_side, gd_back), "merchant": (mc_front, mc_side, mc_back),
         "traveller": (tr_front, tr_side, tr_back)}


def frames(who, action, view):
    front, side, back = VIEWS[who]
    out = []
    for p in {"idle": IDLE, "walk": WALK}[action]:
        q = dict(p)
        if view == "down":
            out.append(front(**q))
        elif view in ("right", "left"):
            out.append(side(left=view == "left", **q))
        else:
            q.pop("blink", None)
            out.append(back(**q))
    return out
