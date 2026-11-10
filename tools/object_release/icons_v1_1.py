"""v1.0.1 icons: weapons and armour that fell back to another item's icon (src/view/itemView.js
ICON_BY_TYPE: every weapon showed icon.sword, every armour icon.armor).

  icon.spear        guard_spear        (見張りの槍)     wood, steel, leather
  icon.greatsword   rusty_greatsword   (錆びた大剣)     iron, clay (rust), leather
  icon.ember_sword  ember_sword        (灯火の剣)       steel, fire, leather
  icon.star_sword   star_steel_sword   (星鋼の剣)       gem, steel, gold
  icon.cap          insulated_cap      (雷よけの帽子)   leather, shock, linen
  icon.boots        grip_boots         (岩登りの靴)     leather, iron, string

Same rules as the other icons (objects2.py): 20x20, drawn inside 2..17 so the selective outline keeps a
1 px clear margin, at most 3 materials, light from the top left, every pixel opaque or clear.
Each is told apart from icon.sword by its shape (spear, upright broad blade, cap, boot) or, for the two
swords that share its pose, by the blade's own colour (fire / star blue) and a light around it.
"""

from draw import to_rgba
from objects import hline, vline
from icons_dishes import DISH_ICONS
from objects2 import cv


def _diag(x, y, axis=19):
    """(u, v) for the up-right diagonal: v runs along x+y=axis (bottom left -> top right), u across it."""
    return x + y - axis, x - y


def icon_spear():
    """A long spear on the diagonal: a wooden shaft, a leaf-shaped steel head at the top right, a leather
    wrap under the head and a small steel butt cap."""
    c = cv(20, 20)
    for y in range(2, 18):
        for x in range(2, 18):
            u, v = _diag(x, y)
            if -15 <= v <= 3 and -1 <= u <= 1:  # the shaft (2 px on the stair)
                c.put(x, y, "wood", 4 if u < 0 else 3 if u == 0 else 1)  # dark wood: lit wide (guide 6.1)
            if 1 <= v <= 4 and -2 <= u <= 2:  # the wrap
                c.put(x, y, "leather", 4 if u < 0 else 3 if u == 0 else 1)
            if 4 <= v <= 15:  # the head: a long narrow leaf, widest a third of the way up
                w = {4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 2, 10: 2, 11: 1, 12: 1, 13: 1, 14: 0, 15: 0}[v]
                if abs(u) <= w:
                    c.put(x, y, "steel", 4 if (u == 0 and v >= 9) else 3 if u <= 0 else 2)
            if -15 <= v <= -13 and -1 <= u <= 1:  # the butt cap
                c.put(x, y, "steel", 3 if u <= 0 else 2)
    for x, y in ((12, 6), (13, 5)):  # the shine on the head's lit face
        c.put(x, y, "steel", 4)
    return to_rgba(c)


def icon_greatsword():
    """The rusty greatsword, upright: a broad blade (6 px) with a dark fuller, a chipped edge and rust,
    a wide crossguard, a long two-hand grip and a heavy pommel."""
    c = cv(20, 20)
    I = "iron"
    for y in range(2, 12):
        x0, x1 = (9, 10) if y == 2 else (8, 11) if y == 3 else (7, 12)
        for x in range(x0, x1 + 1):
            t = 3 if x <= 8 else 2 if x <= 11 else 1
            if x0 == 9:
                t = 3
            c.put(x, y, I, t)
    c.put(7, 4, I, 4)
    c.put(8, 5, I, 4)
    c.put(7, 6, I, 4)
    vline(c, 10, 5, 11, I, 1)  # the fuller
    vline(c, 9, 5, 11, I, 3)
    for x, y in ((12, 6), (12, 9)):  # chips out of the edge
        c.mat[y][x] = None
    for x, y, t in ((11, 4, 2), (12, 7, 1), (11, 8, 2), (8, 10, 2), (11, 11, 1), (7, 9, 3)):  # rust
        c.put(x, y, "clay", t)
    c.rect(3, 12, 16, 13, I, 2)  # the crossguard
    hline(c, 3, 16, 12, I, 4)
    hline(c, 4, 16, 13, I, 2)
    c.put(16, 13, I, 1)
    c.put(3, 13, I, 3)
    c.put(15, 12, "clay", 2)
    for y in range(14, 17):  # the long grip, wound leather
        c.put(9, y, "leather", 3 if y % 2 == 0 else 2)
        c.put(10, y, "leather", 2 if y % 2 == 0 else 1)
    c.rect(8, 17, 11, 17, I, 2)  # the pommel
    c.put(8, 17, I, 3)
    c.put(9, 17, I, 4)
    c.put(11, 17, I, 1)
    return to_rgba(c)


def _sword_blade(c, edge, core, shade, lit_mat, lit_tones):
    """The one-handed blade on the diagonal, as icon.sword's (4 px a row), with its own materials."""
    for y in range(3, 12):
        x = 18 - y
        c.put(x - 1, y, lit_mat, lit_tones[0])
        c.put(x, y, core[0], core[1] if y > 4 else lit_tones[1])
        c.put(x + 1, y, core[0], core[2])
        c.put(x + 2, y, shade[0], shade[1])
    c.put(16, 2, edge[0], edge[1])
    c.put(17, 2, shade[0], shade[1])


def icon_ember_sword():
    """The ember sword: the blade glows hot along its edge (fire), small flames lick up from it; a dark
    steel guard and pommel, a leather grip. Fire on the blade sets it apart from icon.sword."""
    c = cv(20, 20)
    _sword_blade(c, ("fire", 4), ("steel", 3, 2), ("steel", 2), "fire", (3, 4))
    for y in range(5, 11):  # the hot core line (one unbroken line, no dither)
        c.put(18 - y, y, "fire", 2)
    for x, y, t in ((10, 6, 2), (10, 5, 3), (9, 5, 3), (9, 4, 4),  # two solid tongues of flame licking up
                    (7, 9, 2), (7, 8, 3), (6, 8, 3), (6, 7, 4)):  # from the blade's lit edge
        if c.m(x, y) is None:
            c.put(x, y, "fire", t)
    for k in range(-3, 4):  # the guard: dark steel
        x, y = 7 + k, 12 + k
        c.put(x, y, "steel", 3 if k < 3 else 2)
        c.put(x, y + 1, "steel", 2 if k < 2 else 1)
    c.put(4, 9, "steel", 4)
    for k in range(1, 4):  # the grip
        x, y = 7 - k, 13 + k
        c.put(x, y, "leather", 4 if k % 2 else 3)
        c.put(x + 1, y, "leather", 2)
    c.rect(2, 16, 3, 17, "steel", 3)
    c.put(2, 16, "steel", 4)
    c.put(3, 17, "steel", 1)
    return to_rgba(c)


def icon_star_sword():
    """The star-steel sword: forged from the murk crystal, the blade shines a faint blue (gem blue, 星環),
    a steel edge; a gold guard with a star at its heart. Blue blade + star set it apart from icon.sword."""
    c = cv(20, 20)
    _sword_blade(c, ("gem", 4), ("gem", 3, 2), ("gem", 1), "steel", (4, 4))
    for y in (5, 6, 7):
        c.put(18 - y, y, "gem", 4)
    for k in range(-3, 4):  # the guard: gold
        x, y = 7 + k, 12 + k
        c.put(x, y, "gold", 3 if k < 3 else 2)
        c.put(x, y + 1, "gold", 1)
    c.put(4, 9, "gold", 3)
    for x, y, t in ((7, 12, 4), (7, 11, 4), (6, 12, 4), (8, 12, 3), (7, 13, 3)):  # the star in the guard
        c.put(x, y, "gem", t)
    for k in range(1, 4):  # the grip: wound steel wire
        x, y = 7 - k, 13 + k
        c.put(x, y, "steel", 3 if k % 2 else 2)
        c.put(x + 1, y, "steel", 1)
    c.rect(2, 16, 3, 17, "gold", 2)
    c.put(2, 16, "gold", 3)
    c.put(3, 17, "gold", 1)
    return to_rgba(c)


def icon_cap():
    """The insulated cap: a padded leather cap with ear flaps and a pale linen band, a yellow lightning
    mark (the shock crystal's colour) on its front."""
    c = cv(20, 20)
    L = "leather"
    for y in range(3, 12):  # the dome
        for x in range(2, 18):
            dx, dy = (x + 0.5 - 10) / 7.6, (y + 0.5 - 11.5) / 8.4
            if dx * dx + dy * dy <= 1:
                c.put(x, y, L, 3 if (x < 12 or y < 6) else 2 if x < 15 else 1)
    for x in range(5, 15, 3):  # the padded seams
        vline(c, x + 1, 5, 11, L, 1 if x > 8 else 2)
    c.put(6, 4, L, 4)
    c.put(5, 5, L, 4)
    c.put(4, 6, L, 4)
    c.rect(2, 11, 17, 12, "linen", 2)  # the band
    hline(c, 2, 13, 11, "linen", 3)
    hline(c, 14, 17, 12, "linen", 1)
    for x0 in (3, 14):  # the ear flaps
        c.rect(x0, 13, x0 + 2, 16, L, 2 if x0 == 3 else 1)
        vline(c, x0, 13, 16, L, 3 if x0 == 3 else 2)
        hline(c, x0 + 1, x0 + 1, 17, L, 1)
    for x, y, t in ((10, 4, 3), (11, 4, 4), (9, 5, 3), (10, 5, 4), (8, 6, 3), (9, 6, 4), (10, 6, 3),
                    (11, 6, 3), (10, 7, 4), (9, 8, 3), (8, 9, 2), (9, 7, 2)):  # the lightning mark
        c.put(x, y, "shock", t)
    return to_rgba(c)


def icon_boots():
    """The climbing boot, side on (toe to the left): leather, laced up the front with cord, a thick iron-
    studded sole that grips (the studs make the bottom edge bumpy)."""
    c = cv(20, 20)
    L = "leather"
    c.rect(8, 2, 14, 13, L, 3)  # the shaft (dark leather: lit wide, guide 6.1)
    vline(c, 13, 4, 13, L, 2)
    vline(c, 8, 2, 13, L, 3)
    vline(c, 9, 2, 13, L, 3)
    vline(c, 14, 2, 15, L, 1)
    hline(c, 8, 14, 2, L, 4)
    hline(c, 8, 14, 3, L, 1)  # the cuff's fold
    for y in range(10, 16):  # the foot, toe to the left, rounded
        x0 = {10: 6, 11: 4, 12: 3, 13: 2, 14: 2, 15: 2}[y]
        for x in range(x0, 15):
            if c.m(x, y) != L:
                c.put(x, y, L, 3 if y <= 12 or x < 6 else 2)
    hline(c, 4, 7, 11, L, 4)
    c.put(3, 12, L, 4)
    for y in range(5, 13, 2):  # the laces: rungs of cord up the front (solid rows, no checker)
        c.put(8, y, "string", 4)
        c.put(9, y, "string", 3)
        c.put(10, y, "string", 2)
    c.rect(2, 16, 15, 16, "iron", 3)  # the sole
    hline(c, 2, 15, 16, "iron", 3)
    c.put(15, 16, "iron", 1)
    for x in range(2, 16, 2):  # the studs
        c.put(x, 17, "iron", 2 if x < 10 else 1)
    c.put(2, 16, "iron", 4)
    return to_rgba(c)


def all_icons_v1_1():
    return {
        "icon.spear": icon_spear(), "icon.greatsword": icon_greatsword(), "icon.ember_sword": icon_ember_sword(),
        "icon.star_sword": icon_star_sword(), "icon.cap": icon_cap(), "icon.boots": icon_boots(),
    }


SIZES3 = {k: (20, 20) for k in ("icon.spear", "icon.greatsword", "icon.ember_sword", "icon.star_sword",
                                "icon.cap", "icon.boots")}
ANCHOR3 = {k: "feet" for k in SIZES3}
# item id -> icon (for src/view/itemView.js ICON_BY_ID; wired by the game side, not here)
ITEM_ICONS = {
    "guard_spear": "icon.spear", "rusty_greatsword": "icon.greatsword", "ember_sword": "icon.ember_sword",
    "star_steel_sword": "icon.star_sword", "insulated_cap": "icon.cap", "grip_boots": "icon.boots",
    **DISH_ICONS,  # the eight dishes (icons_dishes.py); icon.food stays the fallback
}
