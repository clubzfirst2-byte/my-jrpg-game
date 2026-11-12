"""v3 NPC production (STYLE order 5), milestone 3: the child (npc.child), the cook (npc.cook) and the elder
(npc.elder). Each from their own parts (hair / headwear, face map, clothes, held things) on the 64 x 112
grid, following the approved v1 design notes and colours (tools/npc_release/child.py, cook.py, elder.py,
read only). Keys, frame counts and the anchor as the approved v1 ones (idle 4, walk 6; down, right, up,
left). Facing left is drawn on its own (v1's left frames differ from the mirror: what they hold changes
hands' side): drawn facing right with the near and far sides swapped, then mirrored by the caller.
"""

import math

import numpy as np

from hdkit import capsule, grooves, lock
from npc_batch2 import _boot, _finish, _ramps, _shade_locks, _stamp
from v3lib import Canvas

W, H = 64, 112
GOLD = ["#5a4018", "#a07a30", "#e8c060", "#f8dc88", "#fff4c8"]
GEM = ["#0e2a60", "#1a5cb8", "#2a8de2", "#78c8ff", "#e0f6ff"]
LEATHER = ["#24160c", "#4a3020", "#704c30", "#946c46", "#b88c5e"]
WOOD = ["#1e1008", "#4a2c16", "#6e4424", "#906038", "#b07e50"]
STEEL = ["#1a1e26", "#4a5260", "#7a8494", "#a8b2c0", "#e0e6ee"]


def _limb(c, a, b, r, mat, tones=(1, 2, 3, 4)):
    m = capsule(c, a, b, r)
    c.fill(m, mat)
    c.shade_part(m, tones=tones, norm=True)
    return m


def _blob(c, cx, cy, rx, ry, mat, tones=(1, 2, 3, 4)):
    m = c.m_ellipse(cx, cy, rx, ry)
    c.fill(m, mat)
    c.shade_part(m, tones=tones, norm=True)
    return m


def _rim(c, mask, mat, tone):
    """The lowest texel of each column of mask gets mat / tone (a hem or a trim line)."""
    for x in range(W):
        ys = np.nonzero(mask[:, x])[0]
        if len(ys):
            c.put(x, int(ys.max()), mat, tone)


# ================================================================ the child

CH = _ramps({
    "hair": ["#5a3a10", "#a87a2a", "#d8aa40", "#f0cc68", "#fff0a8"],
    "skin": ["#6e3e2c", "#cc8e6a", "#f4c49e", "#ffdcbc", "#fff0e2"],
    "shirt": ["#0e2a44", "#3a78a8", "#5aa2d0", "#86c4ea", "#c4e8ff"],
    "cloth": ["#4a4846", "#a8a6a0", "#e4e2dc", "#f6f4f0", "#ffffff"],
    "trousers": ["#24160c", "#55361e", "#7a5230", "#9a6e44", "#ba8e5e"],
    "vane": ["#3a0a0a", "#8e1e1e", "#c8302a", "#ec5a48", "#ff9a86"],
    "leather": LEATHER, "wood": WOOD,
})
CH_INK = {"e": "#2a1a14", "i": "#2a7a4a", "I": "#5ab87a", "w": "#ffffff", "m": "#a8524a", "r": "#f49a8a"}
CH_EYE = ["eeeeee", "eiiIwe", "eiiIIe", ".iiII."]
CH_EYE_S = ["eeee", "iiwe", "iIIe", ".II."]


def _pinwheel(c, x, y, turn):
    """The red pinwheel on its stick: 4 vanes around a pin, turned by `turn` (0..3)."""
    c.fill(c.m_line([(x, y), (x, y + 14)], 1.6), "wood", 3)
    for k in range(4):
        a = math.pi / 2 * k + turn * math.pi / 8
        tip = (x + 6 * math.cos(a), y + 6 * math.sin(a))
        side = (x + 4.5 * math.cos(a + 0.9), y + 4.5 * math.sin(a + 0.9))
        v = c.m_poly([(x, y), tip, side])
        c.fill(v, "vane", 3 if k % 2 else 2)
    c.fill(c.m_ellipse(x, y, 1.2, 1.2), "cloth", 4)


def _ch_head_front(c, o, blink, sway, back=False):
    face = _blob(c, 32, 52 + o, 18, 16, "skin", (2, 3, 3, 3, 4))
    for ex in (15.5, 48.5):
        _blob(c, ex, 56 + o, 2.4, 3.4, "skin", (1, 2, 3))
    # curly blond hair: a cap of round curls, a cowlick on top
    cap = c.m_poly([(15, 54 + o), (14, 44 + o), (19, 37 + o), (27, 33 + o), (37, 33 + o), (45, 37 + o), (50, 44 + o),
                    (49, 54 + o), (44, 46 + o), (20, 46 + o)] if not back else
                   [(15, 62 + o), (14, 44 + o), (19, 37 + o), (27, 33 + o), (37, 33 + o), (45, 37 + o), (50, 44 + o),
                    (49, 62 + o), (40, 66 + o), (24, 66 + o)])
    c.fill(cap, "hair")
    c.shade_part(cap, tones=(1, 2, 3, 3, 4), norm=True)
    for cx_ in range(17, 48, 5):  # the curls along the fringe / the back
        for cy_ in ((44, 48) if not back else (44, 50, 56, 62)):
            if cap[min(H - 1, cy_ + o), cx_]:
                _blob(c, cx_ + (1 if cy_ % 2 else 0), cy_ + o, 2.8, 2.6, "hair", (2, 3, 4, 5))
    ck = lock(c, (31, 35 + o), (35 + sway, 28 + o), 4, -1.0)
    c.fill(ck, "hair")
    c.shade_part(ck, tones=(2, 3, 4), norm=True)
    if back:
        return
    for ex in (21, 37):
        _stamp(c, ["......", "eeeeee"] if blink else CH_EYE, ex, 51 + o, CH_INK)
    for bx in (19, 42):
        for dx in range(3):
            c.dot(bx + dx, 59 + o, CH_INK["r"])
    c.put(32, 58 + o, "skin", 2)
    for x, y in ((29, 62), (30, 63), (31, 63), (32, 63), (33, 63), (34, 62)):
        c.dot(x, y + o, CH_INK["m"])


def ch_front(oy=0, breath=0, blink=False, sway=0.0, step=0, turn=0):
    c = Canvas(W, H, CH)
    o = oy - 8  # the child stands 2/3 of the frame: a big head, a short wide body (v1)
    for x, s in ((26, -step), (38, step)):
        lift = 2 if s < 0 else 0
        _limb(c, (x, 98 + o), (x, 101 - lift), 3.0, "skin")
        c.fill(c.m_rect(x - 3, 100 - lift, x + 3, 104 - lift), "cloth", 3)
        _boot(c, x, 111 - lift, 8, 6, mat="leather")
    sh = c.m_poly([(17, 68 + o), (47, 68 + o), (49, 94 + o), (15, 94 + o)])
    c.fill(sh, "shirt")
    c.shade_part(sh, tones=(1, 2, 3, 3, 4), norm=True)
    shorts = c.m_poly([(15, 92 + o), (49, 92 + o), (50, 102 + o), (33, 102 + o), (32, 98 + o), (31, 102 + o), (14, 102 + o)])
    c.fill(shorts, "trousers")
    c.shade_part(shorts, tones=(1, 2, 3, 4), norm=True)
    c.fill(c.m_line([(22, 70 + o), (42, 86 + o)], 2.2), "leather", 2)  # the bag's strap (right shoulder)
    _blob(c, 44, 88 + o, 5, 4.5, "leather", (1, 2, 3, 4))  # the bag on the left hip
    c.fill(c.m_rect(40, 85 + o, 48, 86 + o), "leather", 4)
    for sx in (17, 47):
        _blob(c, sx, 74 + o, 4.6, 4.4, "shirt", (2, 3, 3, 4))
    _limb(c, (47, 78 + o), (47, 88 + o - breath), 2.6, "skin")
    _blob(c, 47, 90 + o, 2.8, 2.8, "skin", (2, 3, 4))
    _limb(c, (17, 78 + o), (14, 84 + o), 2.6, "skin")  # the right arm held out with the pinwheel
    _blob(c, 13, 85 + o, 2.8, 2.8, "skin", (2, 3, 4))
    _pinwheel(c, 12, 74 + o, turn)
    _ch_head_front(c, o, blink, sway)
    return _finish(c)


def ch_side(oy=0, breath=0, blink=False, sway=0.0, step=0, turn=0, left=False):
    c = Canvas(W, H, CH)
    o = oy - 8  # the child stands 2/3 of the frame: a big head, a short wide body (v1)
    for dx, near in ((-4 * step, False), (4 * step, True)):
        x = 30 + dx
        _limb(c, (x, 98 + o), (x, 101), 3.0, "skin")
        c.fill(c.m_rect(x - 3, 100, x + 3, 104), "cloth", 3 if near else 2)
        _boot(c, x, 111, 7, 6, mat="leather", toe=3)
        if not near:
            c.set_tone(c.m_rect(x - 5, 94 + o, x + 7, 111), 1)
    if left:  # facing left: the bag (left hip) is on the far side, behind
        _blob(c, 24, 88 + o, 4.5, 4.5, "leather", (1, 1, 2, 3))
    sh = c.m_poly([(21, 68 + o), (43, 68 + o), (45, 94 + o), (19, 94 + o)])
    c.fill(sh, "shirt")
    c.shade_part(sh, tones=(1, 2, 3, 3, 4), norm=True)
    shorts = c.m_poly([(19, 92 + o), (45, 92 + o), (46, 102 + o), (18, 102 + o)])
    c.fill(shorts, "trousers")
    c.shade_part(shorts, tones=(1, 2, 3, 4), norm=True)
    c.fill(c.m_line([(30, 70 + o), (34, 88 + o)], 2.0), "leather", 2)
    if not left:  # facing right: the bag on the near hip
        _blob(c, 32, 89 + o, 4.8, 4.5, "leather", (1, 2, 3, 4))
    _blob(c, 32, 74 + o, 4.6, 4.4, "shirt", (2, 3, 3, 4))
    if left:  # the pinwheel in the near (right) hand, held out in front
        _limb(c, (32, 78 + o), (42, 82 + o), 2.6, "skin")
        _blob(c, 43, 82 + o, 2.8, 2.8, "skin", (2, 3, 4))
        _pinwheel(c, 46, 70 + o, turn)
    else:  # the pinwheel in the far hand, in front of the chest
        _pinwheel(c, 46, 70 + o, turn)
        _limb(c, (32, 78 + o), (40, 84 + o), 2.6, "skin")
        _blob(c, 41, 84 + o, 2.8, 2.8, "skin", (2, 3, 4))
    # the big round head from the side
    face = c.m_poly([(24, 44 + o), (44, 42 + o), (47, 48 + o), (47, 54 + o), (49, 57 + o), (46, 59 + o),
                     (45, 64 + o), (38, 68 + o), (28, 67 + o), (22, 60 + o)])
    c.fill(face, "skin", 4)
    _blob(c, 28, 56 + o, 2.4, 3.4, "skin", (1, 2, 3))
    cap = c.m_poly([(16, 58 + o), (16, 44 + o), (21, 37 + o), (30, 33 + o), (40, 34 + o), (46, 40 + o), (47, 46 + o),
                    (40, 46 + o), (30, 48 + o), (26, 54 + o), (24, 64 + o)])
    c.fill(cap, "hair")
    c.shade_part(cap, tones=(1, 2, 3, 3, 4), norm=True)
    for cx_, cy_ in ((20, 46), (19, 53), (22, 40), (28, 37), (36, 37), (42, 42), (25, 46)):
        _blob(c, cx_, cy_ + o, 2.8, 2.6, "hair", (2, 3, 4, 5))
    ck = lock(c, (31, 35 + o), (34 + sway, 28 + o), 4, -1.0)
    c.fill(ck, "hair")
    c.shade_part(ck, tones=(2, 3, 4), norm=True)
    _stamp(c, ["....", "eeee"] if blink else CH_EYE_S, 39, 51 + o, CH_INK)
    c.dot(38, 59 + o, CH_INK["r"])
    c.dot(39, 59 + o, CH_INK["r"])
    c.put(48, 57 + o, "skin", 2)
    for x, y in ((42, 62), (43, 63), (44, 62)):
        c.dot(x, y + o, CH_INK["m"])
    return _finish(c)


def ch_back(oy=0, breath=0, blink=False, sway=0.0, step=0, turn=0):
    c = Canvas(W, H, CH)
    o = oy - 8  # the child stands 2/3 of the frame: a big head, a short wide body (v1)
    _pinwheel(c, 52, 74 + o, turn)  # held out on his right (the image's right, seen from behind)
    for x, s in ((26, -step), (38, step)):
        lift = 2 if s < 0 else 0
        _limb(c, (x, 98 + o), (x, 101 - lift), 3.0, "skin")
        c.fill(c.m_rect(x - 3, 100 - lift, x + 3, 104 - lift), "cloth", 3)
        _boot(c, x, 111 - lift, 8, 6, mat="leather")
    sh = c.m_poly([(17, 68 + o), (47, 68 + o), (49, 94 + o), (15, 94 + o)])
    c.fill(sh, "shirt")
    c.shade_part(sh, tones=(1, 2, 3, 3, 4), norm=True)
    shorts = c.m_poly([(15, 92 + o), (49, 92 + o), (50, 102 + o), (14, 102 + o)])
    c.fill(shorts, "trousers")
    c.shade_part(shorts, tones=(1, 2, 3, 4), norm=True)
    c.fill(c.m_line([(42, 70 + o), (22, 86 + o)], 2.2), "leather", 2)
    _blob(c, 20, 88 + o, 5, 4.5, "leather", (1, 2, 3, 4))
    for sx in (17, 47):
        _blob(c, sx, 74 + o, 4.6, 4.4, "shirt", (2, 3, 3, 4))
    _limb(c, (17, 78 + o), (17, 88 + o - breath), 2.6, "skin")
    _limb(c, (47, 78 + o), (50, 84 + o), 2.6, "skin")
    _ch_head_front(c, o, False, sway, back=True)
    return _finish(c)


# ================================================================ the cook

CK = _ramps({
    "hair": ["#2e1a0c", "#6a4424", "#946436", "#b8844c", "#d8a86a"],
    "skin": ["#6a3626", "#c07a5c", "#eaa684", "#f8c4a0", "#ffdcc0"],
    "shirt": ["#2a0e08", "#6a2a18", "#984228", "#be6040", "#dc8a64"],
    "cloth": ["#4e4c4a", "#aaa8a2", "#e2e0da", "#f4f2ee", "#ffffff"],
    "trousers": ["#1e140c", "#46301e", "#62442c", "#80603e", "#a07c54"],
    "towel": ["#2c3446", "#6a7c9c", "#a8bcd8", "#d4e0f0", "#f4f8ff"],
    "leather": LEATHER, "wood": WOOD, "steel": STEEL,
})
CK_INK = {"n": "#3e2414", "e": "#2a160c", "k": "#3a2414", "m": "#8a3a2c", "r": "#e8846c"}


def _ladle(c, x, y):
    c.fill(c.m_line([(x, y), (x, y + 14)], 1.6), "wood", 3)
    _blob(c, x, y + 16, 3.2, 2.6, "steel", (1, 2, 3, 4))


def _towel(c, x0, y0, h):
    """The striped hand towel over the shoulder: pale blue with darker stripes."""
    t = c.m_rect(x0, y0, x0 + 5, y0 + h)
    c.fill(t, "towel", 3)
    for y in range(y0 + 2, y0 + h, 4):
        c.fill(c.m_rect(x0, y, x0 + 5, y), "towel", 1)
    c.fill(c.m_rect(x0, y0, x0, y0 + h), "towel", 4)


def _ck_scarf(c, o, view):
    """The white triangular headscarf, its knot at the back."""
    if view == "side":
        cap = c.m_poly([(16, 22 + o), (17, 12 + o), (24, 6 + o), (34, 4 + o), (44, 8 + o), (48, 16 + o), (47, 22 + o)])
    else:
        cap = c.m_poly([(13, 22 + o), (14, 12 + o), (20, 6 + o), (32, 4 + o), (44, 6 + o), (50, 12 + o), (51, 22 + o)])
    c.fill(cap, "cloth")
    c.shade_part(cap, tones=(2, 3, 3, 4, 4), norm=True)
    c.fill(c.m_rect(10, 20 + o, 54, 22 + o) & cap, "cloth", 2)
    if view != "down":
        kx = 16 if view == "side" else 32
        _blob(c, kx, 22 + o, 3.2, 2.6, "cloth", (1, 2, 3))
        for tip in ((kx - 5, 30 + o), (kx + (1 if view == "side" else 4), 31 + o)):
            t = lock(c, (kx, 23 + o), tip, 3, 0.5)
            c.fill(t, "cloth", 3)


def ck_front(oy=0, breath=0, blink=False, sway=0.0, step=0):
    c = Canvas(W, H, CK)
    o = oy
    for x, s in ((24, -step), (40, step)):
        lift = 2 if s < 0 else 0
        t = c.m_rect(x - 5, 90 + o, x + 5, 103 - lift)
        c.fill(t, "trousers")
        c.shade_part(t, tones=(1, 2, 3, 3), norm=True)
        _boot(c, x, 111 - lift, 11, 8, mat="leather")
    sh = c.m_poly([(9, 50 + o - breath), (55, 50 + o - breath), (58, 62 + o), (59, 78 + o), (54, 92 + o), (10, 92 + o),
                   (5, 78 + o), (6, 62 + o)])  # broad shoulders, a belly
    c.fill(sh, "shirt")
    c.shade_part(sh, tones=(1, 2, 3, 3, 4), norm=True)
    ap = c.m_poly([(19, 60 + o), (45, 60 + o), (52, 78 + o), (51, 102 + o), (13, 102 + o), (12, 78 + o)])
    c.fill(ap, "cloth", 3)
    c.shade_part(ap, tones=(2, 3, 3, 4, 4), norm=True)
    c.fill(c.m_line([(26, 50 + o), (22, 60 + o)], 1.6) | c.m_line([(38, 50 + o), (42, 60 + o)], 1.6), "cloth", 2)
    c.fill(c.m_rect(12, 72 + o, 52, 73 + o), "cloth", 2)  # the waist tie
    for x0, x1 in ((24, 21), (40, 43)):
        c.set_tone(c.m_line([(x0, 76 + o), (x1, 101 + o)], 1.2) & ap, 2)
    _ladle(c, 12, 70 + o)  # tucked in the apron string at his right hip (the image's left)
    for side in (-1, 1):
        sx = 32 + side * 23
        _limb(c, (sx, 54 + o), (sx + side, 64 + o), 4.4, "shirt")
        c.fill(c.m_rect(sx - 4, 63 + o, sx + 4, 65 + o) & capsule(c, (sx, 62 + o), (sx, 66 + o), 4.6), "shirt", 4)
        _limb(c, (sx + side, 67 + o), (sx + side * 1.5, 78 + o), 3.8, "skin")
        _blob(c, sx + side * 1.5, 81 + o, 3.8, 3.8, "skin", (1, 2, 3, 4))
    _towel(c, 49, 50 + o, 16)  # over his left shoulder (the image's right)
    c.fill(c.m_rect(26, 44 + o, 38, 50 + o), "skin", 2)
    face = c.m_poly([(13, 20 + o), (51, 20 + o), (53, 34 + o), (50, 42 + o), (42, 48 + o), (22, 48 + o), (14, 42 + o),
                     (11, 34 + o)])  # round and broad
    c.fill(face, "skin", 3)
    for y, x in zip(*np.nonzero(face)):
        if x >= 47 or y >= 46 + o:
            c.tone[y, x] = 2
    for ex in (12.5, 51.5):
        _blob(c, ex, 32 + o, 2.4, 3.6, "skin", (1, 2, 3))
    hr = c.m_poly([(14, 30 + o), (14, 20 + o), (50, 20 + o), (50, 30 + o), (46, 24 + o), (18, 24 + o)])
    c.fill(hr, "hair")
    c.shade_part(hr, tones=(1, 2, 3, 4), norm=True)
    _ck_scarf(c, o, "down")
    for x0 in (19, 38):
        c.fill(c.m_rect(x0, 27 + o, x0 + 7, 28 + o), "hair", 1)
        _stamp(c, ["eeee"] if blink else ["eeee", "ekke"], x0 + 1, 31 + o + (1 if blink else 0), CK_INK)
    for bx in (18, 42):
        for dx in range(4):
            c.dot(bx + dx, 37 + o, CK_INK["r"])
    _blob(c, 32, 36 + o, 2.4, 2.0, "skin", (2, 3, 4))
    for x in range(25, 40):  # the wide smile, its corners up
        c.dot(x, 42 + o - (1 if x in (25, 39) else 0), CK_INK["m"])
    return _finish(c)


def ck_side(oy=0, breath=0, blink=False, sway=0.0, step=0, left=False):
    c = Canvas(W, H, CK)
    o = oy
    for dx, near in ((-5 * step, False), (5 * step, True)):
        x = 30 + dx
        t = c.m_rect(x - 5, 90 + o, x + 5, 103)
        c.fill(t, "trousers", 2 if near else 1)
        _boot(c, x, 111, 11, 8, mat="leather", toe=4)
        if not near:
            c.set_tone(c.m_rect(x - 7, 90 + o, x + 11, 111), 1)
    if left:  # facing left: the towel is on the far shoulder (behind)
        _towel(c, 22, 50 + o, 14)
    sh = c.m_poly([(18, 50 + o - breath), (40, 50 + o - breath), (46, 64 + o), (46, 80 + o), (42, 92 + o), (16, 92 + o),
                   (14, 62 + o)])
    c.fill(sh, "shirt")
    c.shade_part(sh, tones=(1, 2, 3, 3, 4), norm=True)
    ap = c.m_poly([(40, 60 + o), (45, 62 + o), (49, 80 + o), (48, 102 + o), (40, 102 + o), (42, 80 + o)])
    c.fill(ap, "cloth", 3)
    c.shade_part(ap, tones=(2, 3, 4), norm=True)
    c.fill(c.m_rect(16, 72 + o, 48, 73 + o), "cloth", 2)
    if left:  # the ladle at his right hip: the near side facing left
        _ladle(c, 34, 70 + o)
    _limb(c, (29, 54 + o), (30 + 2 * step, 64 + o), 4.6, "shirt")
    _limb(c, (30 + 2 * step, 67 + o), (31 + 4 * step, 78 + o), 3.8, "skin")
    _blob(c, 31 + 4 * step, 81 + o, 3.8, 3.8, "skin", (1, 2, 3, 4))
    if not left:  # facing right: the towel on the near shoulder
        _towel(c, 26, 48 + o, 16)
    c.fill(c.m_rect(28, 44 + o, 36, 50 + o), "skin", 2)
    face = c.m_poly([(22, 20 + o), (46, 20 + o), (49, 28 + o), (49, 32 + o), (53, 36 + o), (49, 39 + o), (49, 43 + o),
                     (44, 48 + o), (30, 48 + o), (22, 42 + o)])
    c.fill(face, "skin", 3)
    for y, x in zip(*np.nonzero(face)):
        if y >= 46 + o or x <= 25:
            c.tone[y, x] = 2
    hr = c.m_poly([(16, 32 + o), (16, 20 + o), (28, 20 + o), (28, 26 + o), (24, 34 + o)])
    c.fill(hr, "hair")
    c.shade_part(hr, tones=(1, 2, 3, 4), norm=True)
    _blob(c, 27, 32 + o, 2.4, 3.6, "skin", (1, 2, 3))
    _ck_scarf(c, o, "side")
    c.fill(c.m_rect(38, 27 + o, 45, 28 + o), "hair", 1)
    _stamp(c, ["eeee"] if blink else ["eeee", "ekke"], 40, 31 + o + (1 if blink else 0), CK_INK)
    for dx in range(3):
        c.dot(39 + dx, 37 + o, CK_INK["r"])
    _blob(c, 51, 35 + o, 2.4, 2.2, "skin", (2, 3, 4))
    for x, y in ((44, 42), (45, 42), (46, 41), (47, 41)):
        c.dot(x, y + o, CK_INK["m"])
    return _finish(c)


def ck_back(oy=0, breath=0, blink=False, sway=0.0, step=0):
    c = Canvas(W, H, CK)
    o = oy
    for x, s in ((24, -step), (40, step)):
        lift = 2 if s < 0 else 0
        t = c.m_rect(x - 5, 90 + o, x + 5, 103 - lift)
        c.fill(t, "trousers")
        c.shade_part(t, tones=(1, 2, 3, 3), norm=True)
        _boot(c, x, 111 - lift, 11, 8, mat="leather")
    sh = c.m_poly([(9, 50 + o - breath), (55, 50 + o - breath), (58, 62 + o), (59, 78 + o), (54, 92 + o), (10, 92 + o),
                   (5, 78 + o), (6, 62 + o)])  # broad shoulders, a belly
    c.fill(sh, "shirt")
    c.shade_part(sh, tones=(1, 2, 3, 3, 4), norm=True)
    c.fill(c.m_line([(26, 50 + o), (32, 58 + o)], 1.6) | c.m_line([(38, 50 + o), (32, 58 + o)], 1.6), "cloth", 2)
    c.fill(c.m_rect(10, 72 + o, 54, 74 + o), "cloth", 3)  # the apron's waist tie and its bow
    for dx in (-1, 1):
        _blob(c, 32 + dx * 4, 73 + o, 3.4, 2.4, "cloth", (2, 3, 4))
    for side in (-1, 1):
        sx = 32 + side * 23
        _limb(c, (sx, 54 + o), (sx + side, 64 + o), 4.4, "shirt")
        _limb(c, (sx + side, 67 + o), (sx + side * 1.5, 78 + o), 3.8, "skin")
        _blob(c, sx + side * 1.5, 81 + o, 3.8, 3.8, "skin", (1, 2, 3, 4))
    _towel(c, 10, 50 + o, 16)  # over his left shoulder: the image's left from behind
    _ladle(c, 52, 70 + o)
    c.fill(c.m_rect(26, 44 + o, 38, 50 + o), "skin", 2)
    hr = c.m_poly([(14, 40 + o), (14, 18 + o), (50, 18 + o), (50, 40 + o), (44, 46 + o), (20, 46 + o)])
    c.fill(hr, "hair")
    c.shade_part(hr, tones=(1, 2, 3, 4), norm=True)
    _shade_locks(c, [((x, 24 + o), (x + 1, 44 + o), 6, 0.3) for x in (19, 26, 32, 38, 45)], hr, tones=(2, 3, 3, 4))
    for ex in (12.5, 51.5):
        _blob(c, ex, 32 + o, 2.4, 3.6, "skin", (1, 2, 3))
    _ck_scarf(c, o, "up")
    return _finish(c)


# ================================================================ the elder

EL = _ramps({
    "hair": ["#4a4a58", "#9c9cac", "#cdd0da", "#e6e8ee", "#ffffff"],
    "skin": ["#5e3426", "#b47c62", "#e2ae8a", "#f4c8a4", "#ffe2c8"],
    "robe": ["#0c1024", "#1c2850", "#2c3e74", "#44609c", "#6a88c2"],
    "trim": ["#2a2e38", "#6c7280", "#a6acb8", "#d0d4dc", "#f2f4f8"],
    "sash": ["#26080e", "#661824", "#962a36", "#bc4650", "#de7a7a"],
    "leather": LEATHER, "wood": WOOD, "gold": GOLD, "gem": GEM,
})
EL_INK = {"e": "#3a2418", "m": "#8a4a3c", "r": "#e89a8a"}
EL_DY = 10  # small and hunched: the head 10 texels lower than the hero's


def _staff(c, x, y0):
    """The wooden staff carved with the star ring: the ring and its gem at the top."""
    c.fill(c.m_line([(x, y0 + 8), (x, 110)], 2.2), "wood", 3)
    c.fill(c.m_line([(x - 0.8, y0 + 8), (x - 0.8, 110)], 0.9), "wood", 4)
    ring = c.m_ellipse(x, y0 + 4, 4.4, 4.4) & ~c.m_ellipse(x, y0 + 4, 2.6, 2.6)
    c.fill(ring, "wood", 3)
    c.set_tone(ring & c.m_rect(0, 0, int(x), int(y0 + 4)), 4)
    c.fill(c.m_ellipse(x, y0 + 4, 1.6, 1.6), "gem", 3)
    c.put(int(x) - 1, int(y0) + 3, "gem", 5)


def _el_robe(c, o, x0, x1, hem_x0, hem_x1, step=0):
    rb = c.m_poly([(x0, 52 + o), (x1, 52 + o), (hem_x1 + step, 106), (hem_x0 + step, 106)])
    c.fill(rb, "robe")
    c.shade_part(rb, tones=(1, 2, 3, 3, 4), norm=True)
    for y in (104, 105):
        for x in range(W):
            if rb[y, x]:
                c.put(x, y, "trim", 3 if y == 104 else 2)
    return rb


def el_front(oy=0, breath=0, blink=False, sway=0.0, step=0):
    c = Canvas(W, H, EL)
    o = oy + EL_DY
    for x, s in ((26, -step), (38, step)):  # sandals
        lift = 2 if s < 0 else 0
        _blob(c, x, 108 - lift, 3.4, 2.6, "skin", (2, 3, 4))
        c.fill(c.m_rect(x - 4, 110 - lift, x + 4, 111 - lift), "leather", 2)
        c.fill(c.m_rect(x - 3, 107 - lift, x + 3, 107 - lift), "leather", 3)
    rb = _el_robe(c, o, 16, 48, 12, 52)
    c.fill(c.m_rect(29, 52 + o, 35, 105) & rb, "trim", 3)  # the front opening's silver trim
    c.fill(c.m_rect(16, 74 + o, 48, 77 + o) & rb, "sash", 3)
    c.fill(c.m_rect(16, 74 + o, 48, 74 + o) & rb, "sash", 4)
    _limb(c, (36, 77 + o), (38, 86 + o), 1.6, "sash", (2, 3, 4))
    _limb(c, (48, 56 + o), (49, 72 + o - breath), 4.2, "robe")  # his left arm in the wide sleeve
    _blob(c, 49, 75 + o, 3.0, 3.0, "skin", (2, 3, 4))
    _staff(c, 10, 30 + o)  # in his right hand (the image's left), leaning on it
    _limb(c, (16, 56 + o), (12, 68 + o), 4.2, "robe")
    _blob(c, 11, 70 + o, 3.2, 3.2, "skin", (2, 3, 4))
    # head: bald crown, white hair at the sides, drooping brows, the long beard
    face = c.m_poly([(17, 24 + o), (47, 24 + o), (48, 36 + o), (45, 44 + o), (19, 44 + o), (16, 36 + o)])
    c.fill(face, "skin", 3)
    crown = c.m_ellipse(32, 24 + o, 15.5, 12)
    c.fill(crown & c.m_rect(0, 0, W - 1, 26 + o), "skin")
    c.shade_part(crown & c.m_rect(0, 0, W - 1, 26 + o), tones=(2, 3, 4, 4, 5), norm=True)
    for side in (-1, 1):
        sh_ = lock(c, (32 + side * 15, 24 + o), (32 + side * 17, 40 + o), 7, side * 1.0)
        c.fill(sh_, "hair")
        c.shade_part(sh_, tones=(1, 2, 3, 4), norm=True)
    beard = c.m_poly([(17, 38 + o), (47, 38 + o), (46, 50 + o), (40, 62 + o), (32, 70 + o + sway), (24, 62 + o),
                      (18, 50 + o)])
    c.fill(beard, "hair")
    c.shade_part(beard, tones=(1, 2, 3, 3, 4), norm=True)
    _shade_locks(c, [((x, 40 + o), (x + (32 - x) * 0.4, 66 + o), 6, 0.0) for x in (22, 28, 36, 42)], beard,
                 tones=(2, 3, 3, 4, 4))
    c.fill(c.m_rect(26, 38 + o, 38, 39 + o), "hair", 4)  # the moustache
    for x0, sgn in ((18, -1), (37, 1)):  # thick drooping brows
        c.fill(c.m_poly([(x0, 29 + o), (x0 + 9, 29 + o), (x0 + 9 + sgn * 0, 31 + o), (x0 + (9 if sgn < 0 else 0), 33 + o)]),
               "hair", 3)
    for ex in (20, 38):
        _stamp(c, ["eeeeee"] if blink else [".eeee.", "e....e"], ex, 33 + o, EL_INK)
    for bx in (18, 43):
        c.dot(bx, 37 + o, EL_INK["r"])
        c.dot(bx + 1, 37 + o, EL_INK["r"])
    _blob(c, 32, 36 + o, 2.4, 2.2, "skin", (2, 3, 4))
    return _finish(c)


def el_side(oy=0, breath=0, blink=False, sway=0.0, step=0, left=False):
    c = Canvas(W, H, EL)
    o = oy + EL_DY
    for dx in (-4 * step, 4 * step):
        x = 32 + dx
        _blob(c, x, 108, 3.4, 2.4, "skin", (2, 3, 4))
        c.fill(c.m_rect(x - 4, 110, x + 5, 111), "leather", 2)
    rb = _el_robe(c, o, 22, 40, 18, 46, step)
    c.fill(c.m_rect(20, 74 + o, 42, 77 + o) & rb, "sash", 3)
    c.fill(c.m_rect(20, 74 + o, 42, 74 + o) & rb, "sash", 4)
    _limb(c, (40, 77 + o), (44, 88 + o), 1.6, "sash", (2, 3, 4))
    # hunched: the arm forward to the staff
    _limb(c, (30, 56 + o), (42, 68 + o), 4.2, "robe")
    _staff(c, 47, 30 + o)  # held out in front of him (v1: in front in both side views)
    _blob(c, 46, 68 + o, 3.2, 3.2, "skin", (2, 3, 4))
    face = c.m_poly([(26, 22 + o), (44, 22 + o), (47, 30 + o), (47, 33 + o), (50, 36 + o), (47, 38 + o), (46, 44 + o),
                     (30, 46 + o), (26, 40 + o)])
    c.fill(face, "skin", 3)
    crown = c.m_ellipse(34, 24 + o, 13, 11)
    c.fill(crown & c.m_rect(0, 0, W - 1, 26 + o), "skin")
    c.shade_part(crown & c.m_rect(0, 0, W - 1, 26 + o), tones=(2, 3, 4, 4, 5), norm=True)
    sh_ = c.m_poly([(20, 22 + o), (28, 24 + o), (30, 40 + o), (24, 44 + o), (20, 36 + o)])
    c.fill(sh_, "hair")
    c.shade_part(sh_, tones=(1, 2, 3, 4), norm=True)
    _blob(c, 30, 32 + o, 2.2, 3.2, "skin", (1, 2, 3))
    beard = c.m_poly([(34, 38 + o), (47, 38 + o), (48, 48 + o), (44, 60 + o), (40, 66 + o + sway), (36, 56 + o), (32, 46 + o)])
    c.fill(beard, "hair")
    c.shade_part(beard, tones=(1, 2, 3, 3, 4), norm=True)
    c.fill(c.m_poly([(38, 28 + o), (46, 28 + o), (44, 32 + o)]), "hair", 3)
    _stamp(c, [".eeee"] if blink else [".eeee", "e...."], 40, 32 + o, EL_INK)
    c.dot(40, 36 + o, EL_INK["r"])
    c.dot(41, 36 + o, EL_INK["r"])
    _blob(c, 48, 35 + o, 2.2, 2.0, "skin", (2, 3, 4))
    return _finish(c)


def el_back(oy=0, breath=0, blink=False, sway=0.0, step=0):
    c = Canvas(W, H, EL)
    o = oy + EL_DY
    _staff(c, 54, 30 + o)  # in his right hand: the image's right from behind
    for x, s in ((26, -step), (38, step)):
        lift = 2 if s < 0 else 0
        c.fill(c.m_rect(x - 4, 109 - lift, x + 4, 111 - lift), "leather", 2)
        _blob(c, x, 108 - lift, 3.0, 2.0, "skin", (2, 3))
    rb = _el_robe(c, o, 16, 48, 12, 52)
    c.fill(c.m_rect(16, 74 + o, 48, 77 + o) & rb, "sash", 3)
    _blob(c, 32, 75 + o, 4, 2.6, "sash", (2, 3, 4))
    for sx, hx_ in ((16, 14), (48, 52)):
        _limb(c, (sx, 56 + o), (hx_, 68 + o), 4.2, "robe")
        _blob(c, hx_, 71 + o, 3.0, 3.0, "skin", (2, 3, 4))
    crown = c.m_ellipse(32, 30 + o, 15.5, 14)
    c.fill(crown, "skin")
    c.shade_part(crown, tones=(2, 3, 4, 4, 5), norm=True)
    hb = c.m_poly([(16, 28 + o), (48, 28 + o), (49, 40 + o), (44, 46 + o), (20, 46 + o), (15, 40 + o)])
    c.fill(hb & ~c.m_rect(0, 0, W - 1, 30 + o), "hair")
    c.shade_part(hb & ~c.m_rect(0, 0, W - 1, 30 + o), tones=(1, 2, 3, 4), norm=True)
    _shade_locks(c, [((x, 32 + o), (x + 1, 45 + o), 5, 0.2) for x in (20, 26, 32, 38, 44)], hb, tones=(2, 3, 3, 4))
    return _finish(c)


# ================================================================ the frames

IDLE = [dict(), dict(breath=1, sway=0.5), dict(breath=1, sway=1.0, oy=1), dict(blink=True, sway=0.5)]
WALK = [dict(step=1, sway=0.5), dict(step=1, oy=1, sway=1.0), dict(step=0, sway=0.5),
        dict(step=-1, sway=-0.5), dict(step=-1, oy=1, sway=-1.0), dict(step=0, sway=-0.5)]
VIEWS = {"child": (ch_front, ch_side, ch_back), "cook": (ck_front, ck_side, ck_back),
         "elder": (el_front, el_side, el_back)}


def frames(who, action, view):
    front, side, back = VIEWS[who]
    poses = {"idle": IDLE, "walk": WALK}[action]
    out = []
    for k, p in enumerate(poses):
        q = dict(p)
        if who == "child":
            q["turn"] = k % 4  # the pinwheel's vanes turn in every frame
        if view == "down":
            out.append(front(**q))
        elif view in ("right", "left"):
            out.append(side(left=view == "left", **q))
        else:
            q.pop("blink", None)
            out.append(back(**q))
    return out
