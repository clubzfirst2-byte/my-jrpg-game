"""P12 round 2 prototypes (仮素材 — waiting for the user's approval, not final art): 6 NPCs.

  look 6  villager  村人      look 4  merchant  商人      look 7  smith     鍛冶屋
  look 5  child     子ども    look 8  traveler  旅人      look 9  princess  星環の姫

Each: npc.<look>.walk.<down|up|right|left>.<0..2>.png, 32x56, feet at the bottom centre. Frame 0
is the standing pose (the game plays 1, 0, 2, 0); left is the mirror of right. Same method as the
hero v2 and round 1 (tools/art_proto/pixel.py). Looks 4 and 5 replace the merchant's and the
village child's frames; 6-9 are new looks (no NPC uses them yet — preview only).

Writes src/art-proto/npc/ (only the files above; round 1 is not touched).
Run: python3 tools/art_proto/gen_round2.py   (previews: tools/art_proto/previews_round2.py)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, mirror, png  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
OUT = os.path.join(ROOT, "src", "art-proto", "npc")

# walk poses: (bob, step, arm, sway); the child moves livelier
WALK = {0: (0, 0, 0, 0), 1: (1, 1, -1, -1), 2: (1, -1, 1, 1)}
WALK_CHILD = {0: (0, 0, 0, 0), 1: (2, 1, -2, -1), 2: (2, -1, 2, 1)}
EYE_DARK = "#24223a"
MOUTH = "#a8584e"
BLUSH = "#f0a888"


# ------------------------------------------------------------------ shared body parts


def legs(c, d, step, top, x_l, x_r, mat, boot, w=4, lift_px=2, toe=True):
    """Two legs from `top` to the ground (row 55). Front/back: the stepping foot lifts; side: apart."""
    if d in ("down", "up"):
        for side, x0 in ((1, x_l), (-1, x_r)):
            lift = lift_px if step == side else 0
            c.rect(x0, top, x0 + w - 1, 50 - lift, mat)
            c.rect(x0 - 1, 51 - lift, x0 + w, 55 - lift, boot)
            c.line(x0 - 1, 55 - lift, x0 + w, 55 - lift, boot, 1)
    else:
        reach = 3 * step
        for dx, back in ((-reach, True), (reach, False)):
            x0 = (x_l + x_r) // 2 + dx
            t = 1 if back else None
            lift = 1 if back and step else 0
            c.rect(x0, top, x0 + w - 1, 50 - lift, mat, t)
            c.rect(x0 - 1, 51 - lift, x0 + w + (2 if toe else 0), 55 - lift, boot, t)
            c.line(x0 - 1, 55 - lift, x0 + w + (2 if toe else 0), 55 - lift, boot, 0 if back else 1)


def front_face(c, cx, cy, iris="#3a6a3a", big=False, brow=None, blush=True, mouth=True):
    """Two eyes, nose shade, mouth on a skin face centred at (cx, cy) (eye row = cy)."""
    for ex in (cx - 4, cx + 2):
        c.paint(ex, cy - 1, EYE_DARK)
        c.paint(ex + 1, cy - 1, EYE_DARK)
        c.paint(ex, cy, iris)
        c.paint(ex + 1, cy, "#f0fbff" if ex > cx else iris)
        if big:
            c.paint(ex, cy + 1, iris)
            c.paint(ex + 1, cy + 1, iris)
        if brow:
            c.paint(ex, cy - 3, brow)
            c.paint(ex + 1, cy - 3, brow)
    c.shade(cx - 1, cy + 2 + big, 1)
    if mouth:
        c.paint(cx - 1, cy + 4 + big, MOUTH)
        c.paint(cx, cy + 4 + big, MOUTH)
    if blush:
        c.paint(cx - 5, cy + 2 + big, BLUSH)
        c.paint(cx + 4, cy + 2 + big, BLUSH)


def side_face(c, cx, cy, iris="#3a6a3a", big=False, brow=None):
    ex = cx + 3
    c.paint(ex, cy - 1, EYE_DARK)
    c.paint(ex + 1, cy - 1, EYE_DARK)
    c.paint(ex, cy, iris)
    c.paint(ex + 1, cy, "#f0fbff")
    if big:
        c.paint(ex, cy + 1, iris)
    if brow:
        c.paint(ex, cy - 3, brow)
        c.paint(ex + 1, cy - 3, brow)
    c.paint(cx + 5, cy + 4 + big, MOUTH)
    c.paint(cx + 2, cy + 2 + big, BLUSH)


def arms_front(c, b, arm, y0, y1, xs, sleeve, hand, w=2):
    """Arms at the sides (front/back views), swinging with the walk."""
    for side, x in xs:
        lift = -arm * side
        c.rect(x, y0 + b, x + w - 1, y1 + b + lift, sleeve)
        c.rect(x, y1 + 1 + b + lift, x + w - 1, y1 + 3 + b + lift, hand)


# ------------------------------------------------------------------ 6: villager (村人)

VILLAGER = {
    "dress": ["#2a1806", "#6a4618", "#9a7030", "#be9448", "#dcb868"],
    "blouse": ["#5a5650", "#b0a894", "#e8e0cc", "#f6f0e2", "#ffffff"],
    "kerchief": ["#2a0a10", "#7a2a36", "#b04a56", "#d0707a", "#f0a0a8"],
    "hair": ["#1e0c06", "#4a2210", "#783a1c", "#a0582c", "#c87c48"],
}


def villager(d, f):
    b, step, arm, sway = WALK[f]
    c = Canvas(32, 56, VILLAGER)
    legs(c, d, step, 47, 12, 17, "leather", "boot", w=3)
    # long skirt with apron, blouse with sleeves
    c.poly([(10, 31 + b), (22, 31 + b), (25 + sway, 49), (7 + sway, 49)], "dress")
    c.strand(13, 34 + b, 11 + sway, 47, 1)
    c.strand(19, 34 + b, 21 + sway, 47, 1)
    c.line(7 + sway, 48, 25 + sway, 48, "dress", 1)
    c.rect(10, 21 + b, 21, 31 + b, "blouse")
    if d == "down":
        c.poly([(12, 30 + b), (20, 30 + b), (21 + sway, 46), (11 + sway, 46)], "blouse", 2)  # apron
        c.line(11, 30 + b, 20, 30 + b, "dress", 1)  # waist tie
        c.strand(16, 31 + b, 16 + sway, 45, 1)
    if d in ("down", "up"):
        arms_front(c, b, arm, 22, 31, ((-1, 8), (1, 22)), "blouse", "skin")
    else:
        c.rect(15 + arm * 2, 23 + b, 17 + arm * 2, 31 + b, "blouse")
        c.rect(15 + arm * 2, 32 + b, 17 + arm * 2, 33 + b, "skin")
    # head, hair with a single braid, kerchief
    cx = 15.5 if d != "right" else 16.5
    c.ellipse(cx, 13 + b, 6.6, 7.4, "hair")
    if d == "down":
        c.rect(10, 11 + b, 21, 19 + b, "skin")
        c.rect(11, 20 + b, 20, 20 + b, "skin")
        c.poly([(10, 10 + b), (21, 10 + b), (21, 13 + b), (17, 12 + b), (13, 14 + b), (10, 13 + b)], "hair")  # parted fringe
        front_face(c, 15, 16 + b, iris="#6a4a2a")
        c.poly([(20, 14 + b), (23, 14 + b), (24, 30 + b + sway), (21, 30 + b + sway)], "hair")  # braid over the shoulder
        for y in range(17, 30, 3):
            c.shade(21 + (y > 22), y + b, 1)
        c.rect(21, 30 + b + sway, 24, 31 + b + sway, "kerchief")
    elif d == "up":
        c.ellipse(15.5, 15 + b, 6.0, 6.0, "hair")
        for x in (12, 15, 18):
            c.strand(x, 9 + b, x + (1 if x > 15 else -1), 19 + b, 1)
        c.poly([(14, 19 + b), (17, 19 + b), (17, 31 + b + sway), (14, 31 + b + sway)], "hair")
        for y in range(21, 31, 3):
            c.shade(15, y + b, 1)
        c.rect(14, 31 + b + sway, 17, 32 + b + sway, "kerchief")
    else:
        c.rect(15, 11 + b, 22, 19 + b, "skin")
        c.rect(16, 20 + b, 21, 20 + b, "skin")
        c.poly([(14, 10 + b), (23, 10 + b), (23, 12 + b), (17, 14 + b), (14, 13 + b)], "hair")
        side_face(c, 17, 16 + b, iris="#6a4a2a")
        c.poly([(9, 14 + b), (12, 14 + b), (11 - sway, 29 + b), (8 - sway, 29 + b)], "hair")  # braid behind
        c.rect(8 - sway, 29 + b, 11 - sway, 30 + b, "kerchief")
    # kerchief on the head
    c.poly([(9, 7 + b), (22, 7 + b), (22, 9 + b), (9, 10 + b)], "kerchief")
    c.ellipse(15.5 if d != "right" else 15.0, 7 + b, 6.4, 3.4, "kerchief")
    c.strand(10, 9 + b, 21, 9 + b, 1)
    if d == "up":
        c.poly([(14, 9 + b), (17, 9 + b), (18 + sway, 14 + b), (13 + sway, 14 + b)], "kerchief")  # knot tails
    return c.colours()


# ------------------------------------------------------------------ 4: merchant (商人)

MERCHANT = {
    "vest": ["#1c0408", "#4e1018", "#7a1e28", "#a03440", "#c4545c"],
    "hair": ["#08080c", "#1c1c24", "#2e2e3a", "#464656", "#626274"],
    "sack": ["#2a2010", "#5e4c2a", "#8a7244", "#ae9462", "#ccb482"],
    "pants": ["#1a1008", "#3a2818", "#5a4028", "#76583a", "#927250"],
    "shirt": ["#5a5650", "#a8a296", "#e4e0d6", "#f6f4ee", "#ffffff"],
}


def merchant(d, f):
    b, step, arm, sway = WALK[f]
    c = Canvas(32, 56, MERCHANT)
    if d == "down":
        # the goods sack on his back: only its top shows above one shoulder
        c.ellipse(21, 19 + b, 4.5, 3.2, "sack")
    legs(c, d, step, 42, 11, 17, "pants", "boot")
    # round belly: shirt, burgundy vest, belt, purse
    c.ellipse(15.5, 32 + b, 9.0, 9.5, "shirt")
    c.rect(8, 22 + b, 23, 30 + b, "shirt")
    if d == "down":
        c.poly([(7, 22 + b), (14, 22 + b), (15, 41 + b), (8, 40 + b)], "vest")
        c.poly([(17, 22 + b), (24, 22 + b), (23, 40 + b), (16, 41 + b)], "vest")
        c.line(9, 22 + b, 14, 33 + b, "leather", 1)  # the sack's strap
        for y in (27, 31, 35):
            c.put(13, y + b, "gold", 3)  # vest buttons
        c.rect(7, 37 + b, 24, 38 + b, "leather")
        c.ellipse(21, 41 + b, 2.6, 2.6, "leather")  # the purse
        c.put(21, 40 + b, "gold", 3)
        c.put(20, 41 + b, "gold", 2)
    elif d == "up":
        c.ellipse(15.5, 30 + b, 10.0, 9.0, "sack")  # the sack covers his back
        c.line(8, 23 + b, 23, 23 + b, "leather", 1)
        c.strand(15, 23 + b, 13, 38 + b, 1)
        c.strand(12, 26 + b, 10, 34 + b, 3)
        c.rect(14, 21 + b, 17, 22 + b, "sack", 1)  # tied neck
    else:
        c.poly([(16, 22 + b), (22, 22 + b), (24, 40 + b), (16, 41 + b)], "vest")
        c.ellipse(10, 29 + b, 5.5, 7.0, "sack")  # sack on the back (left)
        c.line(13, 23 + b, 17, 33 + b, "leather", 1)  # strap
        c.rect(15, 37 + b, 25, 38 + b, "leather")
        c.ellipse(24, 40 + b, 2.4, 2.4, "leather")
        c.put(24, 39 + b, "gold", 3)
    # arms; the ledger under the arm (front/side)
    if d in ("down", "up"):
        arms_front(c, b, arm, 23, 33, ((-1, 5), (1, 25)), "shirt", "skin")
        if d == "down":
            c.rect(24, 30 + b, 27, 35 + b, "leather")  # ledger
            c.line(24, 30 + b, 27, 30 + b, "gold", 3)
    else:
        ax = 19 + arm * 2
        c.rect(ax, 24 + b, ax + 2, 33 + b, "shirt")
        c.rect(ax - 1, 30 + b, ax + 3, 35 + b, "leather")
        c.line(ax - 1, 30 + b, ax + 3, 30 + b, "gold", 3)
    # head: round, short black hair, moustache
    cx = 15.5 if d != "right" else 17.0
    c.ellipse(cx, 13 + b, 7.0, 7.4, "skin")
    c.ellipse(cx, 9 + b, 7.2, 4.4, "hair")
    if d == "down":
        c.rect(9, 9 + b, 10, 15 + b, "hair")
        c.rect(21, 9 + b, 22, 15 + b, "hair")
        front_face(c, 15, 14 + b, iris="#2a2a3a", brow="#1c1c24", mouth=False)
        c.rect(12, 17 + b, 19, 18 + b, "hair")  # moustache
        c.put(11, 18 + b, "hair", 1)
        c.put(20, 18 + b, "hair", 1)
        c.paint(15, 19 + b, MOUTH)
    elif d == "up":
        c.ellipse(15.5, 12 + b, 7.0, 6.0, "hair")
        c.rect(10, 17 + b, 21, 18 + b, "skin", 1)  # neck
    else:
        c.ellipse(13, 12 + b, 4.0, 5.5, "hair")
        side_face(c, 18, 14 + b, iris="#2a2a3a", brow="#1c1c24")
        c.rect(21, 17 + b, 24, 18 + b, "hair")
        c.rect(24, 13 + b, 25, 15 + b, "skin")  # nose
    return c.colours()


# ------------------------------------------------------------------ 7: smith (鍛冶屋)

SMITH = {
    "work": ["#14161a", "#30343c", "#4a505a", "#646c78", "#848c98"],
    "apron": ["#1a0e06", "#42281a", "#66402a", "#88583a", "#a8744e"],
    "hair": ["#2a0804", "#6a1c0c", "#9a3018", "#c04c28", "#e0703c"],
    "band": ["#3a3226", "#9a8c70", "#d0c4a4", "#e8dec4", "#fff8e4"],
}


def smith(d, f):
    b, step, arm, sway = WALK[f]
    c = Canvas(32, 56, SMITH)
    legs(c, d, step, 42, 10, 18, "trousers", "boot", w=5)
    # broad chest and shoulders in a grey work shirt, sleeves rolled to the elbow
    c.poly([(6, 21 + b), (26, 21 + b), (23, 42 + b), (9, 42 + b)], "work")
    c.ellipse(7, 23 + b, 3.4, 3.0, "work")
    c.ellipse(25, 23 + b, 3.4, 3.0, "work")
    if d in ("down", "up"):
        for side, x in ((-1, 3), (1, 26)):
            lift = -arm * side
            c.rect(x, 23 + b, x + 3, 28 + b, "work")
            c.rect(x, 28 + b, x + 3, 29 + b, "work", 1)  # rolled sleeve
            c.rect(x, 30 + b, x + 3, 36 + b + lift, "skin")  # thick forearms
            c.strand(x + (3 if side < 0 else 0), 31 + b, x + (3 if side < 0 else 0), 35 + b + lift, 1)
            c.rect(x, 37 + b + lift, x + 3, 39 + b + lift, "skin", 1)
    if d == "down":
        # leather apron with a pocket, soot marks
        c.poly([(9, 25 + b), (22, 25 + b), (23 + sway, 47), (8 + sway, 47)], "apron")
        c.line(9, 25 + b, 9, 21 + b, "apron", 1)
        c.line(22, 25 + b, 22, 21 + b, "apron", 1)
        c.rect(12, 34 + b, 19, 38 + b, "apron", 1)
        c.line(12, 34 + b, 19, 34 + b, "apron", 3)
        for x, y in ((11, 30), (20, 41), (14, 44)):
            c.shade(x, y + b if y < 44 else y, 0)
    elif d == "up":
        c.line(9, 30 + b, 22, 30 + b, "apron", 1)  # apron ties
        c.poly([(14, 30 + b), (17, 30 + b), (17 + sway, 34 + b), (14 + sway, 34 + b)], "apron", 1)
        c.strand(16, 22 + b, 16, 40 + b, 1)
    else:
        c.poly([(17, 25 + b), (23, 25 + b), (24 + sway, 47), (17 + sway, 47)], "apron")
        ax = 16 + arm * 2
        c.rect(ax, 23 + b, ax + 3, 29 + b, "work")
        c.rect(ax, 30 + b, ax + 3, 37 + b, "skin")
    # the hammer at his hip (side and front)
    hx_, hy = (24, 39) if d == "down" else (7, 39) if d == "up" else (12, 38)
    c.line(hx_, hy + b, hx_, hy + 7 + b, "wood")
    c.rect(hx_ - 2, hy - 1 + b, hx_ + 2, hy + 1 + b, "steel")
    # head: square jaw, red buzz cut, twisted headband
    cx = 15.5 if d != "right" else 17.0
    c.poly([(cx - 7, 8 + b), (cx + 7, 8 + b), (cx + 7, 17 + b), (cx + 4, 21 + b), (cx - 4, 21 + b), (cx - 7, 17 + b)], "skin")
    c.ellipse(cx, 8 + b, 7.2, 4.2, "hair")
    c.rect(int(cx) - 7, 10 + b, int(cx) + 7, 11 + b, "band")
    for x in range(int(cx) - 7, int(cx) + 8, 3):
        c.shade(x, 10 + b, 1)
    if d == "down":
        front_face(c, 15, 15 + b, iris="#3a2a1a", brow="#6a1c0c", blush=False)
        c.rect(11, 19 + b, 20, 20 + b, "hair", 1)  # short beard on the jaw
        c.paint(15, 19 + b, MOUTH)
        c.shade(9, 17 + b, 0)  # soot
    elif d == "up":
        c.ellipse(15.5, 12 + b, 7.4, 6.6, "hair")  # short cropped hair all round the back
        for x in (11, 14, 17, 20):
            c.strand(x, 9 + b, x, 17 + b, 1)
        c.rect(12, 19 + b, 19, 20 + b, "skin", 1)  # thick neck
        c.rect(8, 10 + b, 23, 11 + b, "band")  # the headband goes round the back
        for x in range(8, 24, 3):
            c.shade(x, 10 + b, 1)
        c.line(14, 12 + b, 13 + sway, 15 + b, "band", 2)  # the knot's two ends
        c.line(17, 12 + b, 18 + sway, 15 + b, "band", 2)
    else:
        c.rect(10, 12 + b, 14, 19 + b, "hair")
        side_face(c, 18, 15 + b, iris="#3a2a1a", brow="#6a1c0c")
        c.rect(19, 19 + b, 23, 20 + b, "hair", 1)
        c.rect(24, 14 + b, 25, 16 + b, "skin")
    return c.colours()


# ------------------------------------------------------------------ 5: child (子ども)

CHILD = {
    "tunic": ["#0a2a40", "#1e5a86", "#3a86b8", "#62aad6", "#9aceec"],
    "hair": ["#3a2a06", "#8a6a18", "#c89a30", "#e8c050", "#fff0a0"],
    "shorts": ["#1a1008", "#4a3420", "#6e5032", "#8e6c48", "#ae8a62"],
}


def child(d, f):
    b, step, arm, sway = WALK_CHILD[f]
    c = Canvas(32, 56, CHILD)
    # short legs, bare knees, small shoes
    for_side = d in ("down", "up")
    if for_side:
        for side, x0 in ((1, 12), (-1, 17)):
            lift = 3 if step == side else 0
            c.rect(x0, 44 - lift, x0 + 2, 47 - lift, "shorts")
            c.rect(x0, 48 - lift, x0 + 2, 51 - lift, "skin")
            c.rect(x0 - 1, 52 - lift, x0 + 3, 55 - lift, "boot")
    else:
        for dx, back in ((-3 * step, True), (3 * step, False)):
            x0 = 14 + dx
            t = 1 if back else None
            c.rect(x0, 44, x0 + 2, 47, "shorts", t)
            c.rect(x0, 48, x0 + 2, 51, "skin", t)
            c.rect(x0 - 1, 52, x0 + 4, 55, "boot", t)
    # tunic and a satchel strap across
    c.poly([(11, 33 + b), (20, 33 + b), (21, 45 + b), (10, 45 + b)], "tunic")
    c.line(10, 44 + b, 21, 44 + b, "tunic", 1)
    if d in ("down", "up"):
        arms_front(c, b, arm, 34, 40, ((-1, 8), (1, 22)), "tunic", "skin")
        c.line(11, 34 + b, 20, 41 + b, "leather", 1)  # strap
        bag_x = 19 if d == "down" else 9
        c.rect(bag_x, 40 + b, bag_x + 4, 44 + b, "leather")
        c.line(bag_x, 40 + b, bag_x + 4, 40 + b, "leather", 3)
    else:
        ax = 15 + arm
        c.rect(ax, 35 + b, ax + 2, 40 + b, "tunic")
        c.rect(ax, 41 + b, ax + 2, 42 + b, "skin")
        c.rect(10, 39 + b, 13, 43 + b, "leather")  # satchel at the back
        c.line(12, 34 + b, 14, 39 + b, "leather", 1)
    # big head, messy blond hair with a cowlick, big eyes
    cx = 15.5 if d != "right" else 16.5
    c.ellipse(cx, 25 + b, 7.4, 8.2, "hair")
    for tx, ty, ex, ey in ((-6, 21, -9, 18), (6, 21, 9, 18), (-1, 17, -2, 14), (3, 17, 5, 14)):
        c.poly([(cx + tx - 1.5, ty + b), (cx + tx + 1.5, ty + b + 1), (cx + ex, ey + b)], "hair")
    if d == "down":
        c.rect(10, 25 + b, 21, 31 + b, "skin")
        c.rect(11, 32 + b, 20, 32 + b, "skin")
        c.poly([(9, 23 + b), (22, 23 + b), (22, 26 + b), (19, 25 + b), (16, 27 + b), (12, 25 + b), (9, 27 + b)], "hair")
        front_face(c, 15, 28 + b, iris="#2a7ab8", big=True)
    elif d == "up":
        for x in (12, 15, 18):
            c.strand(x, 20 + b, x, 31 + b, 1)
        c.rect(11, 32 + b, 20, 32 + b, "skin", 1)
    else:
        c.rect(15, 25 + b, 23, 31 + b, "skin")
        c.rect(16, 32 + b, 22, 32 + b, "skin")
        c.poly([(14, 23 + b), (23, 23 + b), (23, 25 + b), (18, 27 + b), (14, 26 + b)], "hair")
        side_face(c, 17, 28 + b, iris="#2a7ab8", big=True)
    return c.colours()


# ------------------------------------------------------------------ 8: traveler (旅人)

TRAVELER = {
    "mantle": ["#14100a", "#3a3020", "#5a4a32", "#7a6646", "#9a845e"],
    "hat": ["#120c06", "#34261a", "#54402a", "#70583c", "#8e7452"],
    "hair": ["#1e1e24", "#4e4e58", "#7a7a86", "#9e9eaa", "#c4c4ce"],
    "scarf": ["#1c0408", "#4e1018", "#7a1e28", "#a03440", "#c4545c"],
    "pack": ["#1a1408", "#4a3a1e", "#6e5830", "#8e7444", "#ae925e"],
    "shirt": ["#3a3830", "#6a6656", "#8e8a78", "#aaa694", "#c6c2b0"],
}


def traveler(d, f):
    b, step, arm, sway = WALK[f]
    c = Canvas(32, 56, TRAVELER)
    if d == "down":
        c.rect(8, 21 + b, 23, 34 + b, "pack")  # the pack behind him, seen at the sides
    legs(c, d, step, 40, 12, 17, "trousers", "boot", w=3)
    # long drab mantle (cloak) to the shins, narrow body
    c.poly([(10, 20 + b), (21, 20 + b), (24 + sway, 47), (7 + sway, 47)], "mantle")
    for x0, x1 in ((12, 9), (19, 22), (15, 15)):
        c.strand(x0, 24 + b, x1 + sway, 45, 1)
    c.line(7 + sway, 46, 24 + sway, 46, "mantle", 1)
    if d == "down":
        c.poly([(13, 22 + b), (18, 22 + b), (17, 46), (14, 46)], "shirt", 1)  # open front, tunic underneath
        c.rect(12, 33 + b, 19, 34 + b, "leather")
        arms_front(c, b, arm, 22, 34, ((-1, 7), (1, 23)), "mantle", "leather")
    elif d == "up":
        # backpack with a rolled bedroll on top
        c.rect(9, 22 + b, 22, 36 + b, "pack")
        c.line(9, 29 + b, 22, 29 + b, "pack", 1)
        c.rect(14, 30 + b, 17, 33 + b, "leather")
        c.ellipse(15.5, 21 + b, 8.0, 2.4, "scarf")  # bedroll
        c.strand(9, 21 + b, 22, 21 + b, 1)
        arms_front(c, b, arm, 22, 34, ((-1, 7), (1, 23)), "mantle", "leather")
    else:
        c.rect(6, 22 + b, 11, 37 + b, "pack")
        c.ellipse(8.5, 21 + b, 3.2, 2.4, "scarf")
        ax = 16 + arm * 2
        c.rect(ax, 22 + b, ax + 2, 33 + b, "mantle")
        c.rect(ax, 34 + b, ax + 2, 35 + b, "leather")
    # scarf at the neck (the colour accent)
    c.rect(10, 18 + b, 21, 20 + b, "scarf")
    if d == "down":
        c.poly([(18, 20 + b), (21, 20 + b), (21 + sway, 27 + b), (18 + sway, 26 + b)], "scarf")
    # thin face, long ash-grey hair tied back, wide-brimmed hat
    cx = 15.5 if d != "right" else 16.5
    c.ellipse(cx, 12 + b, 5.6, 7.0, "hair")
    if d == "down":
        c.rect(11, 10 + b, 20, 17 + b, "skin")
        c.rect(12, 18 + b, 19, 18 + b, "skin")
        front_face(c, 15, 13 + b, iris="#3a4a5a", blush=False)
        c.shade(12, 16 + b, 1)
        c.shade(19, 16 + b, 1)  # lean cheeks
    elif d == "up":
        c.poly([(14, 16 + b), (17, 16 + b), (17 + sway, 24 + b), (14 + sway, 24 + b)], "hair")  # tied tail
        c.rect(14, 17 + b, 17, 17 + b, "leather")
    else:
        c.rect(15, 10 + b, 21, 17 + b, "skin")
        c.rect(16, 18 + b, 20, 18 + b, "skin")
        side_face(c, 16, 13 + b, iris="#3a4a5a")
        c.poly([(9, 13 + b), (12, 13 + b), (10 - sway, 22 + b), (7 - sway, 22 + b)], "hair")  # tail behind
    # hat: wide brim and crown with a band
    c.ellipse(cx, 7 + b, 11.0, 2.2, "hat")
    c.poly([(cx - 5, 7 + b), (cx + 5, 7 + b), (cx + 4, 1 + b), (cx - 4, 1 + b)], "hat")
    c.line(int(cx) - 5, 6 + b, int(cx) + 5, 6 + b, "scarf", 1)
    return c.colours()


# ------------------------------------------------------------------ 9: princess (星環の姫)

PRINCESS = {
    "gown": ["#3e4256", "#a6acc4", "#e2e6f2", "#f4f6fc", "#ffffff"],
    "royal": ["#08163a", "#1a3474", "#2a52a8", "#4878d4", "#7aa4f0"],
    "silver": ["#2e3040", "#7c8094", "#babed0", "#dcdeea", "#ffffff"],
}


def star(c, x, y, mat="gold", core=True):
    """A small four-pointed star."""
    for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
        c.put(x + dx, y + dy, mat, 3)
    c.put(x, y, "gem" if core else mat, 4)


def princess(d, f):
    b, step, arm, sway = WALK[f]
    c = Canvas(32, 56, PRINCESS)
    # travel boots under a calf-length gown (she walks the road herself)
    legs(c, d, step, 44, 12, 17, "gown", "royal", w=3)
    # the gown: white, gold hem with the star-vein pattern
    c.poly([(11, 23 + b), (20, 23 + b), (24 + sway, 47), (7 + sway, 47)], "gown")
    c.line(7 + sway, 47, 24 + sway, 47, "gold", 2)
    for x in range(9 + sway, 24 + sway, 4):
        c.put(x, 46, "gold", 3)  # star-vein dots on the hem
    for x0, x1 in ((13, 11), (18, 20)):
        c.strand(x0, 30 + b, x1 + sway, 45, 1)
    # belt: the star-vein sash, blue with gold
    c.rect(10, 31 + b, 21, 32 + b, "royal")
    c.line(10, 31 + b, 21, 31 + b, "gold", 3)
    # the short blue capelet over the shoulders, gold edge, star clasp
    if d == "down":
        # the capelet drapes over both shoulders and opens at the chest (a star clasp joins it)
        c.poly([(7, 21 + b), (14, 21 + b), (13, 28 + b), (7, 29 + b), (6, 26 + b)], "royal")
        c.poly([(17, 21 + b), (24, 21 + b), (25, 26 + b), (24, 29 + b), (18, 28 + b)], "royal")
        for y in range(24, 31, 2):
            c.put(15, y + b, "gold", 2)  # the star-vein line down the bodice
            c.put(16, y + b, "gold", 1)
    elif d == "right":
        c.poly([(9, 21 + b), (21, 21 + b), (22, 27 + b), (15, 29 + b), (8, 28 + b)], "royal")
    else:
        c.poly([(8, 21 + b), (23, 21 + b), (25 + sway, 35 + b), (16, 37 + b), (6 + sway, 35 + b)], "royal")
    if d == "up":
        c.line(6 + sway, 35 + b, 25 + sway, 35 + b, "gold", 2)
        star(c, 15 + (sway > 0), 28 + b)  # the star of the royal line on her back
        c.strand(11, 23 + b, 9 + sway, 33 + b, 1)
        c.strand(20, 23 + b, 22 + sway, 33 + b, 1)
    elif d == "down":
        c.line(6, 28 + b, 13, 28 + b, "gold", 2)
        c.line(18, 28 + b, 25, 28 + b, "gold", 2)
        c.line(13, 22 + b, 13, 27 + b, "gold", 3)
        c.line(18, 22 + b, 18, 27 + b, "gold", 3)
        c.line(14, 23 + b, 17, 23 + b, "gold", 2)  # the clasp chain
        star(c, 15, 23 + b)
    else:
        c.line(8, 28 + b, 15, 29 + b, "gold", 2)
        c.line(21, 22 + b, 21, 27 + b, "gold", 3)
        star(c, 20, 23 + b)
    # arms in white sleeves, gloved hands
    if d in ("down", "up"):
        arms_front(c, b, arm, 24, 33, ((-1, 7), (1, 23)), "gown", "skin")
    else:
        ax = 16 + arm * 2
        c.rect(ax, 25 + b, ax + 2, 33 + b, "gown")
        c.rect(ax, 34 + b, ax + 2, 35 + b, "skin")
    # long silver hair with a braid, the star-ring circlet with a blue gem
    cx = 15.5 if d != "right" else 16.5
    c.ellipse(cx, 13 + b, 7.4, 8.0, "silver")
    if d == "down":
        c.poly([(8, 14 + b), (11, 14 + b), (11 + sway, 30 + b), (8 + sway, 31 + b)], "silver")  # long hair at the sides
        c.poly([(20, 14 + b), (23, 14 + b), (23 + sway, 31 + b), (20 + sway, 30 + b)], "silver")
        c.rect(10, 11 + b, 21, 19 + b, "skin")
        c.rect(11, 20 + b, 20, 20 + b, "skin")
        c.poly([(9, 9 + b), (22, 9 + b), (22, 12 + b), (18, 13 + b), (15, 11 + b), (12, 13 + b), (9, 12 + b)], "silver")  # side-swept fringe
        # eyes: lashes, deep blue iris with a highlight each (clear and resolute), a small smile
        for ex in (11, 18):
            c.paint(ex, 15 + b, EYE_DARK)
            c.paint(ex + 1, 15 + b, EYE_DARK)
            c.paint(ex + 2, 15 + b, EYE_DARK)
            c.paint(ex, 16 + b, "#f0fbff")
            c.paint(ex + 1, 16 + b, "#2a6ad0")
            c.paint(ex + 2, 16 + b, "#1a3c86")
            c.paint(ex + 1, 17 + b, "#1a3c86")
            c.paint(ex, 13 + b, "#7c8094")  # fine brows
            c.paint(ex + 1, 13 + b, "#7c8094")
        c.shade(15, 18 + b, 1)
        c.paint(14, 19 + b, MOUTH)
        c.paint(15, 19 + b, MOUTH)
        c.paint(11, 18 + b, BLUSH)
        c.paint(20, 18 + b, BLUSH)
        for y in range(16, 30, 3):
            c.shade(21 + sway * (y > 24), y + b, 1)  # braid on her left
    elif d == "up":
        c.poly([(9, 13 + b), (22, 13 + b), (23 + sway, 33 + b), (8 + sway, 33 + b)], "silver")  # hair down her back
        for x in (11, 13, 16, 18, 20):
            c.strand(x, 10 + b, x + sway, 31 + b, 1)
        for x in (12, 17):
            c.strand(x, 8 + b, x, 20 + b, 4)
        for x in (14, 19):
            c.strand(x, 12 + b, x + sway, 28 + b, 3)
        c.poly([(14, 31 + b), (17, 31 + b), (17 + sway, 36 + b), (14 + sway, 36 + b)], "silver")  # braid tip
        c.put(15 + sway, 32 + b, "gold", 3)  # gold ribbon on the braid
    else:
        c.poly([(8, 12 + b), (14, 12 + b), (13 - sway, 32 + b), (8 - sway, 32 + b)], "silver")  # long hair behind
        c.rect(15, 11 + b, 23, 19 + b, "skin")
        c.rect(16, 20 + b, 22, 20 + b, "skin")
        c.poly([(14, 9 + b), (24, 9 + b), (24, 11 + b), (19, 13 + b), (14, 12 + b)], "silver")
        side_face(c, 17, 16 + b, iris="#2a6ad0")
        c.strand(10, 14 + b, 10 - sway, 30 + b, 1)
    # the circlet: a gold band with the star-ring gem at the brow
    c.line(int(cx) - 6, 8 + b, int(cx) + 6, 8 + b, "gold", 3)
    if d == "down":
        star(c, 15, 7 + b)
        c.put(15, 5 + b, "gold", 3)
        c.put(14, 7 + b, "gem", 3)
        c.put(16, 7 + b, "gem", 3)
    elif d == "right":
        star(c, 21, 7 + b)
    else:
        c.put(int(cx), 8 + b, "gold", 4)
    return c.colours()


# ------------------------------------------------------------------ write

NPCS = (
    (6, "villager", "村人", villager),
    (4, "merchant", "商人", merchant),
    (7, "smith", "鍛冶屋", smith),
    (5, "child", "子ども", child),
    (8, "traveler", "旅人", traveler),
    (9, "princess", "星環の姫", princess),
)


def frames_of(draw):
    out = {}
    for d in ("down", "up", "right"):
        for f in range(3):
            out[(d, f)] = draw(d, f)
    for f in range(3):
        out[("left", f)] = mirror(out[("right", f)])
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    n = 0
    for look, _, _, draw in NPCS:
        for (d, f), img in frames_of(draw).items():
            with open(os.path.join(OUT, f"npc.{look}.walk.{d}.{f}.png"), "wb") as fh:
                fh.write(png(img))
            n += 1
    print(f"round 2: {n} frames for {len(NPCS)} NPCs -> src/art-proto/npc/")


if __name__ == "__main__":
    main()
