"""v1.0.1 dish icons: every cooked dish showed the generic stew bowl (icon.food stays the fallback).

  icon.dish.grilled_meat     grilled_meat     焼き肉          stew (seared meat), bone, fire
  icon.dish.mushroom_skewer  mushroom_skewer  きのこ串        wood (stick), cap, bone
  icon.dish.berry_jam        berry_jam        木の実のジャム  glass, berry, linen
  icon.dish.hunter_stew      hunter_stew      狩人の煮込み    iron (pot), stew, bone
  icon.dish.ember_soup       ember_soup       火照りのスープ  glaze (teal bowl), pepper, fire
  icon.dish.hearty_skewer    hearty_skewer    がっつり串      wood (stick), stew (meat), leaf
  icon.dish.mixed_stew       mixed_stew       ごった煮        wood (bowl), leaf, berry
  icon.dish.dubious_food     dubious_food     あやしい料理    linen (plate), ash (a charred lump), smoke

Same rules as the other icons: 20x20, drawn inside 2..17 (the selective outline keeps a 1 px clear margin),
at most 3 materials, light from the top left, every pixel opaque or clear. Each has its own silhouette
or colour: a drumstick, two different skewers (round caps on a thin stick / big cubes), a jar, an iron pot
with a bone, a teal bowl with red soup and a flame, a wooden bowl heaped green, a smoking burnt lump.
"""

from draw import round_shade, to_rgba
from objects import hline, vline
from objects2 import cv, ring_px


def _shade_rows(c, mat, lit_cols, dark_cols):
    """Tone a flat-filled part: lit on its left columns, dark on its right ones, core between."""
    for y in range(20):
        xs = [x for x in range(20) if c.m(x, y) == mat]
        if not xs:
            continue
        x0, x1 = min(xs), max(xs)
        for x in xs:
            if c.tone[y][x] is None:
                c.tone[y][x] = 3 if x < x0 + lit_cols else 1 if x > x1 - dark_cols else 2


def grilled_meat():
    """A seared drumstick on the diagonal: the meat browned (stew ramp) with dark grill stripes, a light
    glaze on top, the bone end sticking out at the lower right, a tiny curl of fire-gold sheen."""
    c = cv(20, 20)
    for x, y in ring_px(8.0, 8.0, 0, 5.8):
        c.put(x, y, "stew")
    round_shade(c, "stew", 8.0, 8.0, 5.8, 5.8, cuts=(0.9, 0.5, 0.05))
    for k in range(4):  # the bone: a short shaft to the lower right and a knob
        c.put(12 + k, 12 + k, "bone", 3)
        c.put(13 + k, 12 + k, "bone", 2)
        c.put(12 + k, 13 + k, "bone", 1)
    c.rect(15, 15, 17, 16, "bone", 3)
    c.put(16, 17, "bone", 2)
    c.put(17, 14, "bone", 3)
    c.put(15, 15, "bone", 4)
    for x0 in (5, 8, 11):  # the grill stripes, on the diagonal
        for k in range(4):
            x, y = x0 - k + 1, 4 + k + (x0 - 5) // 1 // 3 * 0
            if c.m(x, y + 1) == "stew":
                c.put(x, y + 1, "stew", 1)
    for x, y in ((5, 5), (6, 4), (4, 6), (7, 4)):  # the glaze shine
        c.put(x, y, "fire", 3)
    c.put(5, 4, "fire", 4)
    return to_rgba(c)


def mushroom_skewer():
    """Three grilled mushrooms on a thin upright stick: each a domed cap (cap ramp) with a pale spot, its
    short pale stem below, the stick running through."""
    c = cv(20, 20)
    vline(c, 9, 2, 17, "wood", 4)
    vline(c, 10, 2, 17, "wood", 2)
    for top in (2, 7, 12):
        for y in range(top, top + 3):  # the dome: 9 wide at its base
            hw = (2.5, 3.6, 4.4)[y - top]
            for x in range(20):
                if abs(x + 0.5 - 10) <= hw:
                    c.put(x, y, "cap", 3 if x < 9 else 2 if x < 12 else 1)
        hline(c, 7, 9, top, "cap", 4)
        c.put(7, top + 1, "bone", 4)  # a pale spot on the cap
        c.rect(9, top + 3, 10, top + 4, "bone", 2)  # the stem under it
        c.put(9, top + 3, "bone", 3)
    return to_rgba(c)

def berry_jam():
    """A glass jar of red jam: a cloth cover (linen) tied over the mouth, the jam showing through the glass
    with a lit streak on the left."""
    c = cv(20, 20)
    c.rect(5, 7, 14, 17, "berry", 3)  # the jam inside the glass (lit: the dark red needs tone 3, guide 6.1)
    for y in range(8, 17):
        c.put(12, y, "berry", 2)
    for y in range(7, 18):
        c.put(5, y, "glass", 3)
        c.put(6, y, "berry", 3)
        c.put(14, y, "glass", 1)
        c.put(13, y, "berry", 1)
    hline(c, 6, 13, 17, "glass", 1)
    for y in range(9, 15):  # the glint on the glass
        c.put(7, y, "glass", 4)
    hline(c, 6, 13, 7, "berry", 3)  # the jam's surface
    c.rect(4, 3, 15, 5, "linen", 2)  # the cloth cover, tied
    hline(c, 4, 15, 3, "linen", 3)
    hline(c, 5, 15, 5, "linen", 1)
    c.put(4, 3, "linen", 4)
    c.put(3, 5, "linen", 2)
    c.put(16, 5, "linen", 1)
    hline(c, 5, 14, 6, "berry", 1)  # the tie (dyed cord) round the neck
    c.put(6, 6, "berry", 3)
    return to_rgba(c)


def hunter_stew():
    """A small iron pot of hearty stew with two handles, chunks in the stew and a big bone sticking out."""
    c = cv(20, 20)
    for y in range(9, 17):  # the pot: round-bellied
        hw = 7.2 - max(0, y - 13) * 1.1
        for x in range(20):
            if abs(x + 0.5 - 10) <= hw:
                c.put(x, y, "iron")
    round_shade(c, "iron", 8.0, 10.5, 9.0, 7.0, cuts=(0.9, 0.5, 0.05))
    hline(c, 3, 16, 9, "iron", 4)  # the rim
    hline(c, 3, 16, 10, "iron", 2)
    for x in (2, 17):  # the handles
        c.put(x, 11, "iron", 3 if x == 2 else 1)
        c.put(x, 12, "iron", 2 if x == 2 else 1)
    c.ellipse(9.5, 8.6, 6.0, 1.6, "stew", 3)  # the stew, heaped a little
    for x, y in ((6, 8), (9, 7), (12, 8)):
        c.put(x, y, "stew", 4)
    for x, y in ((8, 8), (11, 8), (13, 8)):
        c.put(x, y, "stew", 2)
    for k in range(5):  # the bone, up and out to the right
        c.put(11 + k, 7 - k, "bone", 3)
        c.put(12 + k, 7 - k, "bone", 2)
    c.rect(15, 2, 17, 3, "bone", 3)
    c.put(15, 2, "bone", 4)
    c.put(17, 3, "bone", 2)
    return to_rgba(c)


def ember_soup():
    """A teal glazed bowl of fiery red soup with a small flame rising off it (it keeps the cold away)."""
    c = cv(20, 20)
    for y in range(11, 18):
        hw = 7.6 - max(0, y - 13) * 1.2
        for x in range(20):
            if abs(x + 0.5 - 10) <= hw:
                c.put(x, y, "glaze")
    round_shade(c, "glaze", 8.0, 11.0, 10.0, 7.0, cuts=(0.9, 0.5, 0.05))
    hline(c, 3, 16, 11, "glaze", 4)  # the rim
    c.ellipse(9.5, 10.4, 6.4, 1.6, "pepper", 3)  # the soup
    hline(c, 5, 9, 10, "pepper", 4)
    for x, y in ((12, 10), (14, 11)):
        c.put(x, y, "pepper", 2)
    for x, y, t in ((9, 8, 2), (10, 8, 2), (9, 7, 3), (10, 7, 3), (10, 6, 3), (9, 6, 4), (10, 5, 4),
                    (11, 5, 3), (10, 4, 4), (11, 3, 4), (7, 6, 3), (7, 5, 4), (13, 7, 3), (13, 6, 4)):
        c.put(x, y, "fire", t)  # the flame: one big tongue and two small ones
    return to_rgba(c)


def hearty_skewer():
    """A thick skewer on the diagonal: big cubes of seared meat (stew ramp) between green vegetables."""
    c = cv(20, 20)
    for k in range(15):  # the stick, bottom left to top right
        c.put(2 + k, 17 - k, "wood", 4)
        c.put(3 + k, 17 - k, "wood", 2)
    for i, (cx, cy) in enumerate(((5, 13), (8, 10), (11, 7), (14, 4))):
        m = "stew" if i % 2 == 0 else "leaf"
        x0, y0, x1, y1 = (cx - 2, cy - 2, cx + 2, cy + 2) if m == "stew" else (cx - 1, cy - 2, cx + 2, cy + 1)
        c.rect(x0, y0, x1, y1, m, 3)
        hline(c, x0, x1, y0, m, 4)
        vline(c, x0, y0, y1, m, 4)
        hline(c, x0 + 1, x1, y1, m, 2)
        vline(c, x1, y0 + 1, y1, m, 2)
    for x, y in ((4, 13), (5, 12), (13, 4)):  # sear marks on the meat
        c.put(x, y, "stew", 1)
    return to_rgba(c)

def mixed_stew():
    """A wooden bowl heaped with a bit of everything: greens (leaf) with red bits (berry) in the heap."""
    c = cv(20, 20)
    for y in range(11, 18):
        hw = 7.6 - max(0, y - 13) * 1.2
        for x in range(20):
            if abs(x + 0.5 - 10) <= hw:
                c.put(x, y, "wood")
    round_shade(c, "wood", 8.0, 11.0, 10.0, 7.0, cuts=(0.75, 0.15, -0.6))
    hline(c, 3, 16, 11, "wood", 4)
    for x in (6, 10, 14):  # the bowl's staves
        vline(c, x, 13, 16, "wood", 1)
    for x, y in ring_px(9.5, 10.5, 0, 6.2, 0.75):  # the heap
        if y <= 10:
            c.put(x, y, "leaf")
    round_shade(c, "leaf", 8.0, 9.0, 7.0, 4.5, cuts=(0.8, 0.3, -0.6))
    for x, y, t in ((6, 8, 3), (7, 8, 2), (11, 7, 3), (12, 7, 2), (9, 9, 3), (13, 9, 2), (5, 10, 2)):
        c.put(x, y, "berry", t)  # red bits in the heap
    c.put(6, 7, "berry", 4)
    c.put(11, 6, "berry", 4)
    return to_rgba(c)


def dubious_food():
    """Something went wrong: a charred black lump, lopsided, on a pale plate, a cartoon curl of smoke above
    it (funny, not gross: no drips, no flies, no sickly colours)."""
    c = cv(20, 20)
    c.ellipse(9.5, 15.2, 7.6, 1.9, "linen")  # the plate
    for y in range(13, 18):
        for x in range(20):
            if c.m(x, y) == "linen":
                c.tone[y][x] = 3 if y <= 14 else 1 if y >= 17 else 2
    hline(c, 4, 9, 14, "linen", 4)
    for y in range(8, 15):  # the lump: lopsided, taller on the left
        for x in range(4, 16):
            dx = (x + 0.5 - 9.0) / 5.2
            dy = (y + 0.5 - (14.0 - 0.25 * (x - 9))) / 5.0
            if dx * dx + dy * dy <= 1 and y <= 14:
                c.put(x, y, "ash")
    round_shade(c, "ash", 7.5, 10.0, 6.0, 5.0, cuts=(0.88, 0.45, 0.0))
    for x, y in ((6, 10), (7, 9), (10, 12), (12, 11)):  # cracks of a burnt crust
        c.put(x, y, "ash", 4)
    for x, y, t in ((8, 7, 2), (9, 6, 3), (9, 5, 3), (8, 4, 4), (9, 4, 3), (10, 3, 4), (11, 3, 3),
                    (11, 4, 2), (12, 2, 4), (13, 2, 3), (7, 4, 3)):
        c.put(x, y, "smoke", t)  # one curly wisp of smoke
    return to_rgba(c)


DISHES = {
    "grilled_meat": grilled_meat, "mushroom_skewer": mushroom_skewer, "berry_jam": berry_jam,
    "hunter_stew": hunter_stew, "ember_soup": ember_soup, "hearty_skewer": hearty_skewer,
    "mixed_stew": mixed_stew, "dubious_food": dubious_food,
}


def all_dishes():
    return {f"icon.dish.{k}": f() for k, f in DISHES.items()}


SIZES4 = {f"icon.dish.{k}": (20, 20) for k in DISHES}
ANCHOR4 = {k: "feet" for k in SIZES4}
DISH_ICONS = {k: f"icon.dish.{k}" for k in DISHES}  # item id -> icon (itemView.js ICON_BY_ID)
