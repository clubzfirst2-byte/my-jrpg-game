"""P12 round 1 prototypes (仮素材 — waiting for the user's approval, not final art).

  elder    npc.1.walk.<down|up|right|left>.<0..2>   32x56  (the village elder: 老人)
  soldier  npc.3.walk.<down|up|right|left>.<0..2>   32x56  (the watchman: 兵士)
  beast    enemy.beast.<0|1>                        44x32  (獣型: a wolf with a bristling mane)
  goblin   enemy.archer.<0|1>                       32x44  (ゴブリン型: shoots orbs from a bone staff)

Same drawing method and quality as the approved hero v2 (tools/art_proto/pixel.py). NPC frame 0 is
the standing pose (the game plays 1, 0, 2, 0); left is the mirror of right. Enemies face right (the
game mirrors them), frame 0 = idle, 1 = moving. Plan: docs/characters/P12_NPC_ENEMY_PLAN.md.

Writes src/art-proto/npc/, src/art-proto/enemy/ and docs/characters/proto_round1_preview.png.
Run: python3 tools/art_proto/gen_round1.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, hx, mirror, png, sheet  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
OUT_NPC = os.path.join(ROOT, "src", "art-proto", "npc")
OUT_ENEMY = os.path.join(ROOT, "src", "art-proto", "enemy")
PREVIEW = os.path.join(ROOT, "docs", "characters", "proto_round1_preview.png")

# walk poses: (bob, step, arm, sway) — frame 0 stands; 1 and 2 are the two steps
WALK = {0: (0, 0, 0, 0), 1: (1, 1, -1, -1), 2: (1, -1, 1, 1)}

# ------------------------------------------------------------------ elder (老人)

ELDER = {
    "robe": ["#0a1024", "#1c2a52", "#2c3f76", "#435a9c", "#6078bc"],
    "sash": ["#24080a", "#5e1c18", "#8a2e24", "#b04a34", "#d0704e"],
    "beard": ["#3a3a46", "#9c9caa", "#d2d2dc", "#ececf2", "#ffffff"],
    "oldskin": ["#5a3424", "#b07c5a", "#dca882", "#eec4a0", "#fadcc0"],
}


def elder(direction, frame):
    bob, step, arm, sway = WALK[frame]
    c = Canvas(32, 56, ELDER)
    b = bob
    if direction in ("down", "up"):
        # sandals (only the feet show under the robe)
        for side, x0 in ((1, 10), (-1, 17)):
            lift = 2 if step == side else 0
            c.rect(x0, 53 - lift, x0 + 4, 55 - lift, "leather")
            c.line(x0, 55 - lift, x0 + 4, 55 - lift, "leather", 1)
        # the robe: wide, to the ankles, the hem swaying
        c.poly([(10, 27 + b), (22, 27 + b), (25 + sway, 53), (7 + sway, 53)], "robe")
        for x0, x1 in ((13, 11), (18, 20), (11, 8)):
            c.strand(x0, 33 + b, x1 + sway, 51, 1)
        c.strand(12, 30 + b, 10 + sway, 50, 3)
        c.line(7 + sway, 52, 25 + sway, 52, "robe", 1)
        # the sash with its knot
        c.rect(9, 39 + b, 23, 40 + b, "sash")
        if direction == "down":
            c.rect(14, 41 + b, 15, 45 + b + (sway > 0), "sash")
            c.line(9, 39 + b, 23, 39 + b, "sash", 3)
        # wide sleeves, hands, and the staff in his left hand (screen right from the front)
        sx = 25 if direction == "down" else 6
        for side, x in ((-1, 6), (1, 22)):
            lift = -arm * side
            c.poly([(x, 29 + b), (x + 4, 29 + b), (x + 4, 39 + b + lift), (x - 1, 41 + b + lift)], "robe")
            c.rect(x, 40 + b + lift, x + 2, 42 + b + lift, "oldskin")
        top = 17 + b + (1 if step == (1 if direction == "down" else -1) else 0)
        c.line(sx, top, sx, 55, "wood")
        c.line(sx + 1, top, sx + 1, 55, "wood", 1)
        c.ellipse(sx + 0.5, top, 2.2, 2.2, "wood")  # the knob
        c.shade(sx, top - 1, 4)
        hy = 40 + b
        c.rect(sx - 1, hy, sx + 2, hy + 2, "oldskin")
        # head: bald crown, white hair at the sides and back
        c.ellipse(15.5, 21 + b, 6.6, 7.2, "oldskin")
        if direction == "down":
            c.ellipse(9.5, 21 + b, 2.6, 4.2, "beard")
            c.ellipse(21.5, 21 + b, 2.6, 4.2, "beard")
            # bushy brows over small eyes, a big nose, the moustache and the long beard
            c.rect(11, 19 + b, 14, 20 + b, "beard")
            c.rect(17, 19 + b, 20, 20 + b, "beard")
            c.paint(12, 21 + b, "#24223a")
            c.paint(13, 21 + b, "#24223a")
            c.paint(18, 21 + b, "#24223a")
            c.paint(19, 21 + b, "#24223a")
            c.rect(15, 21 + b, 16, 24 + b, "oldskin", 1)
            c.shade(15, 21 + b, 3)
            c.poly([(10, 25 + b), (21, 25 + b), (20, 31 + b), (17, 38 + b + sway), (14, 38 + b + sway), (11, 31 + b)], "beard")
            c.rect(11, 25 + b, 20, 26 + b, "beard", 4)
            for x0, x1 in ((13, 14), (16, 16), (18, 17)):
                c.strand(x0, 28 + b, x1, 36 + b, 1)
            for x in (8, 23):  # wrinkles / cheeks
                c.shade(x + (1 if x < 15 else -1), 23 + b, 1)
        else:
            # from behind: white hair over the back of the head, beard tips at the sides
            c.ellipse(15.5, 22 + b, 6.8, 6.4, "beard")
            c.ellipse(15.5, 17 + b, 4.0, 2.6, "oldskin")
            for x0 in (11, 14, 17, 20):
                c.strand(x0, 21 + b, x0, 27 + b, 1)
            c.rect(10, 28 + b, 21, 29 + b, "robe", 1)  # collar
    else:  # right (3/4, hunched)
        for back, dx in ((True, -step * 2), (False, step * 2)):
            x0 = 13 + dx
            c.rect(x0, 53 - (1 if back and step else 0), x0 + 5, 55 - (1 if back and step else 0), "leather", 1 if back else None)
        c.poly([(9, 30 + b), (14, 27 + b), (20, 28 + b), (22, 53), (8 - sway, 53)], "robe")
        c.ellipse(11, 32 + b, 4.5, 5.5, "robe")  # the rounded back
        for x0, x1 in ((12, 10), (16, 15), (19, 20)):
            c.strand(x0, 34 + b, x1 - sway, 51, 1)
        c.strand(10, 29 + b, 9, 40 + b, 3)
        c.line(8 - sway, 52, 22, 52, "robe", 1)
        c.rect(10, 39 + b, 21, 40 + b, "sash")
        # head forward, beard hanging, staff in front
        c.ellipse(19, 22 + b, 6.0, 6.8, "oldskin")
        c.ellipse(15, 21 + b, 3.4, 5.0, "beard")  # white hair at the back
        c.rect(19, 19 + b, 23, 20 + b, "beard")  # brow
        c.paint(21, 21 + b, "#24223a")
        c.paint(22, 21 + b, "#24223a")
        c.rect(24, 21 + b, 25, 24 + b, "oldskin")  # nose
        c.poly([(17, 25 + b), (25, 25 + b), (24, 31 + b), (21, 38 + b + sway), (19, 33 + b)], "beard")
        c.strand(21, 27 + b, 21, 35 + b, 1)
        c.strand(23, 26 + b, 22, 31 + b, 4)
        sx = 26 + arm
        c.line(sx, 17 + b, sx, 55, "wood")
        c.ellipse(sx + 0.5, 17 + b, 2.2, 2.2, "wood")
        c.poly([(17, 31 + b), (21, 31 + b), (sx + 1, 36 + b), (sx - 2, 38 + b)], "robe")  # arm to the staff
        c.rect(sx - 1, 35 + b, sx + 1, 37 + b, "oldskin")
    return c.colours()


# ------------------------------------------------------------------ soldier (兵士)

SOLDIER = {
    "tabard": ["#0a121c", "#22344a", "#3a5670", "#567894", "#7a9cb8"],
    "plume": ["#2a0806", "#6a1a14", "#9a2c20", "#c04a34", "#e07454"],
    "hairb": ["#1a0e08", "#3a2414", "#5a3820", "#7a5030", "#9a6a44"],
}


def soldier(direction, frame):
    bob, step, arm, sway = WALK[frame]
    c = Canvas(32, 56, SOLDIER)
    b = bob
    if direction in ("down", "up"):
        for side, x0 in ((1, 11), (-1, 17)):
            lift = 2 if step == side else 0
            c.rect(x0, 42 - lift + b, x0 + 3, 47 - lift, "trousers")
            c.rect(x0 - 1, 46 - lift, x0 + 4, 51 - lift, "steel")  # greaves
            c.strand(x0, 47 - lift, x0, 50 - lift, 4)
            c.rect(x0 - 1, 52 - lift, x0 + 4, 55 - lift, "boot")
            c.line(x0 - 1, 55 - lift, x0 + 4, 55 - lift, "boot", 1)
        # tabard over the breastplate, a belt
        c.poly([(9, 22 + b), (23, 22 + b), (23, 44 + b), (9, 44 + b)], "steel")
        c.poly([(11, 24 + b), (21, 24 + b), (22 + sway, 45 + b), (10 + sway, 45 + b)], "tabard")
        c.rect(9, 36 + b, 22, 37 + b, "leather")
        c.rect(15, 36 + b, 16, 37 + b, "gold")
        if direction == "down":
            # the watch's emblem: a silver tower on the tabard
            c.rect(14, 27 + b, 17, 33 + b, "steel", 3)
            c.rect(13, 26 + b, 18, 26 + b, "steel", 3)
            for x in (13, 15, 18):
                c.put(x, 25 + b, "steel", 3)
            c.rect(15, 31 + b, 16, 33 + b, "tabard", 0)
        else:
            c.strand(16, 25 + b, 16 + sway, 43 + b, 1)
        # shoulders, arms with bracers
        for side, x in ((-1, 5), (1, 23)):
            lift = -arm * side
            c.ellipse(x + 2, 23 + b, 3.2, 2.6, "steel")
            c.rect(x + 1, 25 + b, x + 3, 33 + b + lift, "leather")
            c.rect(x + 1, 31 + b + lift, x + 3, 34 + b + lift, "steel")
            c.rect(x + 1, 35 + b + lift, x + 3, 36 + b + lift, "skin" if direction == "down" else "leather")
        # the spear, held upright in his right hand (screen left from the front)
        sx = 6 if direction == "down" else 25
        c.line(sx, 4 + b, sx, 55, "wood")
        c.poly([(sx - 1.5, 6 + b), (sx + 0.5, 0 + b), (sx + 2.5, 6 + b), (sx + 0.5, 8 + b)], "steel")
        c.rect(sx - 1, 34 + b, sx + 1, 36 + b, "skin" if direction == "down" else "leather")
        # head: steel helmet with a red plume, face below the brim
        c.ellipse(15.5, 12 + b, 7.5, 6.5, "steel")
        c.rect(8, 12 + b, 23, 13 + b, "steel", 1)  # brim
        c.poly([(13, 6 + b), (18, 6 + b), (17 + sway, 1 + b), (14 + sway, 1 + b)], "plume")
        if direction == "down":
            c.rect(10, 14 + b, 21, 20 + b, "skin")
            c.rect(11, 21 + b, 20, 21 + b, "skin", 1)
            c.rect(15, 12 + b, 16, 17 + b, "steel", 3)  # nose guard
            for ex in (11, 18):
                c.paint(ex, 16 + b, "#24223a")
                c.paint(ex + 1, 16 + b, "#24223a")
                c.paint(ex, 17 + b, "#3a4a6a")
            c.paint(14, 20 + b, "#a8584e")
            c.paint(17, 20 + b, "#a8584e")
            c.rect(9, 14 + b, 10, 19 + b, "steel", 1)  # cheek guards
            c.rect(21, 14 + b, 22, 19 + b, "steel", 1)
            c.shade(10, 8 + b, 4)
            c.shade(11, 7 + b, 4)
        else:
            c.rect(9, 14 + b, 22, 20 + b, "steel")  # neck guard
            c.rect(11, 19 + b, 20, 21 + b, "hairb")
            c.strand(15, 8 + b, 15, 18 + b, 3)
    else:  # right
        reach = 3 * step
        for dx, back in ((-reach, True), (reach, False)):
            x0 = 14 + dx
            t = 1 if back else None
            c.rect(x0, 42 + b, x0 + 3, 47, "trousers", t)
            c.rect(x0 - 1, 46, x0 + 4, 51, "steel", t)
            c.rect(x0 - 1, 52, x0 + 6, 55, "boot", t)
        c.poly([(11, 22 + b), (21, 22 + b), (21, 44 + b), (11, 44 + b)], "steel")
        c.poly([(13, 24 + b), (20, 24 + b), (21, 45 + b), (12 - sway, 45 + b)], "tabard")
        c.rect(11, 36 + b, 21, 37 + b, "leather")
        c.ellipse(16, 23 + b, 3.4, 2.8, "steel")
        sx = 24 + arm
        c.rect(16, 25 + b, 18, 31 + b, "leather")
        c.poly([(17, 30 + b), (19, 30 + b), (sx + 1, 33 + b), (sx - 1, 35 + b)], "leather")
        c.line(sx, 4 + b, sx, 55, "wood")
        c.poly([(sx - 1.5, 6 + b), (sx + 0.5, 0 + b), (sx + 2.5, 6 + b), (sx + 0.5, 8 + b)], "steel")
        c.rect(sx - 1, 32 + b, sx + 1, 34 + b, "skin")
        c.ellipse(16, 12 + b, 7.0, 6.5, "steel")
        c.rect(9, 12 + b, 24, 13 + b, "steel", 1)
        c.poly([(13, 6 + b), (17, 6 + b), (15 - sway, 1 + b), (12 - sway, 1 + b)], "plume")
        c.rect(15, 14 + b, 22, 20 + b, "skin")
        c.rect(10, 14 + b, 14, 20 + b, "steel")  # neck guard at the back
        c.rect(22, 12 + b, 23, 17 + b, "steel", 3)  # nose guard
        c.paint(20, 16 + b, "#24223a")
        c.paint(19, 16 + b, "#24223a")
        c.paint(21, 19 + b, "#a8584e")
    return c.colours()


# ------------------------------------------------------------------ beast (獣型)

BEAST = {
    "fur": ["#120e12", "#3a3036", "#5c4c52", "#7e6c72", "#a49298"],
    "mane": ["#1e0806", "#5a2012", "#8a3820", "#b0582e", "#d07a44"],
    "fang": ["#3a3226", "#a8a090", "#e8e2d0", "#f6f2e6", "#ffffff"],
}


def beast(frame):
    run = frame == 1
    c = Canvas(44, 32, BEAST)
    lo = 1 if run else 0
    # tail (raised, flowing back when running)
    c.poly([(10, 14 + lo), (13, 17 + lo), (5, 12 + lo * 3), (1, 6 + lo * 4), (4, 8 + lo * 3)], "fur")
    c.poly([(1, 6 + lo * 4), (4, 8 + lo * 3), (2, 4 + lo * 4)], "mane")
    # legs with joints (far legs darker); running: front legs reach forward, hind legs push back
    def leg(x0, far, front, phase):
        t = 1 if far else None
        top = 19 + lo
        if front:
            knee = (x0 + 1 + phase, 25)
            paw = (x0 + 2 + 2 * phase, 29)
        else:  # hind leg: thigh, backward hock, then down
            knee = (x0 - 2 - phase, 24)
            paw = (x0 - 1 - 2 * phase, 29)
        c.poly([(x0, top), (x0 + 4, top), (knee[0] + 2, knee[1]), (knee[0] - 1, knee[1])], "fur", t)
        c.poly([(knee[0] - 1, knee[1]), (knee[0] + 2, knee[1]), (paw[0] + 2, paw[1]), (paw[0] - 1, paw[1])], "fur", t)
        c.rect(paw[0] - 1, 29, paw[0] + 3, 31, "fur", 1 if far else 2)
        c.line(paw[0] - 1, 31, paw[0] + 3, 31, "fur", 0)

    run_k = 2 if run else 0
    leg(14, True, False, -run_k // 2)
    leg(28, True, True, run_k)
    leg(17, False, False, run_k)
    leg(31, False, True, -run_k // 2)
    # body, belly lighter
    c.ellipse(21, 16 + lo, 12.0 + run, 6.0 - lo * 0.5, "fur")
    c.strand(12, 20 + lo, 28, 21 + lo, 3)
    for x0 in (15, 19, 23):
        c.strand(x0, 13 + lo, x0 + 2, 18 + lo, 1)  # ribs / muscle
    # neck and head
    c.poly([(27, 9 + lo), (35, 7 + lo), (36, 17 + lo), (29, 20 + lo)], "fur")
    c.ellipse(35, 11 + lo, 5.4, 4.6, "fur")
    c.poly([(37, 9 + lo), (43, 11 + lo), (43, 14 + lo), (37, 15 + lo)], "fur")  # snout
    c.put(43, 11 + lo, "fur", 0)  # nose
    c.put(42, 11 + lo, "fur", 0)
    open_mouth = run
    c.line(37, 15 + lo, 43, 14 + lo + open_mouth, "fur", 0)
    if open_mouth:
        c.line(38, 16 + lo, 42, 16 + lo, "mane", 1)  # inside of the mouth
    for x in (39, 41):
        c.put(x, 15 + lo, "fang", 3)
    # ears
    c.poly([(31, 7 + lo), (33, 0 + lo), (35, 7 + lo)], "fur")
    c.poly([(34, 7 + lo), (37, 2 + lo), (38, 8 + lo)], "fur")
    c.shade(33, 4 + lo, 1)
    # the bristling mane: tufts along the neck and back, swept backwards
    c.poly([(19, 12 + lo), (33, 6 + lo), (34, 11 + lo), (21, 15 + lo)], "mane")
    for x, y in ((21, 10), (24, 8), (27, 6), (30, 5), (33, 5)):
        c.poly([(x - 1, y + 4 + lo), (x + 3, y + 4 + lo), (x - 4 - (2 if run else 0), y - 1 + lo)], "mane")
    for x0, y0 in ((22, 10), (26, 8), (30, 7)):
        c.strand(x0, y0 + lo, x0 - 3, y0 + 2 + lo, 4)
    for x0, y0 in ((24, 11), (28, 9)):
        c.strand(x0, y0 + lo, x0 - 3, y0 + 3 + lo, 1)
    # glowing eye
    c.paint(36, 10 + lo, "#ffd84a")
    c.paint(37, 10 + lo, "#fff2a8")
    c.paint(36, 11 + lo, "#b06a10")
    return c.colours()


# ------------------------------------------------------------------ goblin (ゴブリン型)

GOBLIN = {
    "gskin": ["#14160a", "#3a3e1e", "#5e6232", "#80844a", "#a4a866"],
    "rag": ["#1a100a", "#3e2a1a", "#5e4228", "#7e5c3a", "#9e7a52"],
    "magic": ["#2a0a2a", "#6a1e6a", "#b040b0", "#e070e0", "#ffc8ff"],
}


def goblin(frame):
    walk = frame == 1
    c = Canvas(32, 44, GOBLIN)
    b = 1 if walk else 0
    # legs: short and bowed, big bare feet
    for back, dx in ((True, -2 if walk else 0), (False, 2 if walk else 0)):
        x0 = 12 + dx
        t = 1 if back else None
        c.poly([(x0, 33), (x0 + 3, 33), (x0 + 3 + dx // 2, 40), (x0 + dx // 2, 40)], "gskin", t)
        c.rect(x0 - 1 + dx // 2, 40, x0 + 5 + dx // 2, 43, "gskin", t)
        c.line(x0 - 1 + dx // 2, 43, x0 + 5 + dx // 2, 43, "gskin", 0)
    # ragged loincloth
    c.poly([(9, 28 + b), (21, 28 + b), (22, 34 + b), (19, 36 + b), (17, 34 + b), (14, 37 + b), (12, 34 + b), (9, 36 + b)], "rag")
    c.strand(13, 29 + b, 12, 35 + b, 1)
    c.strand(18, 29 + b, 19, 34 + b, 1)
    c.rect(9, 28 + b, 21, 28 + b, "leather")
    # hunched torso leaning forward
    c.ellipse(15, 24 + b, 6.4, 6.2, "gskin")
    c.strand(12, 22 + b, 12, 27 + b, 1)
    c.strand(15, 23 + b, 15, 27 + b, 1)
    # bone necklace
    for x, y in ((14, 20), (16, 21), (18, 21), (20, 20)):
        c.put(x, y + b, "bone", 3)
    # the arm holding the bone staff (in front)
    sx = 26 + (1 if walk else 0)
    c.poly([(17, 22 + b), (20, 22 + b), (sx + 1, 26 + b), (sx - 1, 28 + b)], "gskin")
    c.line(sx, 8 + b, sx, 43, "wood")
    c.line(sx + 1, 8 + b, sx + 1, 43, "wood", 1)
    c.rect(sx - 1, 25 + b, sx + 2, 27 + b, "gskin")  # hand
    # the staff's head: a small skull holding a glowing orb
    c.ellipse(sx + 0.5, 6 + b, 3.0, 2.6, "bone")
    c.paint(sx - 1, 6 + b, "#2a2218")
    c.paint(sx + 1, 6 + b, "#2a2218")
    c.ellipse(sx + 0.5, 2 + b, 2.0, 2.0, "magic")
    c.shade(sx, 1 + b, 4)
    # big head, long pointed ear swept back, big nose, glowing eye, grin
    c.ellipse(19, 15 + b, 7.0, 6.4, "gskin")
    c.poly([(13, 11 + b), (2, 6 + b), (5, 9 + b), (13, 17 + b)], "gskin")
    c.strand(5, 8 + b, 12, 12 + b, 1)
    c.poly([(24, 13 + b), (30, 17 + b), (27, 20 + b), (23, 18 + b)], "gskin")  # nose
    c.shade(28, 18 + b, 1)
    c.rect(20, 10 + b, 24, 11 + b, "gskin", 1)  # heavy brow
    c.paint(22, 13 + b, "#ff6a3a")
    c.paint(23, 13 + b, "#ffd06a")
    c.line(18, 20 + b, 24, 20 + b, "gskin", 0)  # mouth
    for x in (19, 21, 23):
        c.put(x, 20 + b, "fang", 3) if False else c.put(x, 20 + b, "bone", 4)
    c.shade(15, 10 + b, 4)
    c.shade(16, 9 + b, 4)
    return c.colours()


# ------------------------------------------------------------------ write

def npc_frames(draw):
    out = {}
    for d in ("down", "up", "right"):
        for f in range(3):
            out[(d, f)] = draw(d, f)
    for f in range(3):
        out[("left", f)] = mirror(out[("right", f)])
    return out


def main():
    os.makedirs(OUT_NPC, exist_ok=True)
    os.makedirs(OUT_ENEMY, exist_ok=True)
    rows = []
    for look, draw in ((1, elder), (3, soldier)):
        frames = npc_frames(draw)
        for (d, f), img in frames.items():
            with open(os.path.join(OUT_NPC, f"npc.{look}.walk.{d}.{f}.png"), "wb") as fh:
                fh.write(png(img))
        rows.append([frames[(d, f)] for d in ("down", "up", "right", "left") for f in (0, 1, 2)])
    enemies = []
    for kind, draw in (("beast", beast), ("archer", goblin)):
        for f in (0, 1):
            img = draw(f)
            with open(os.path.join(OUT_ENEMY, f"enemy.{kind}.{f}.png"), "wb") as fh:
                fh.write(png(img))
            enemies.append(img)
    rows.append(enemies + [mirror(e) for e in enemies])
    sheet(rows, PREVIEW)
    print("round 1: 24 NPC frames, 4 enemy frames -> src/art-proto/{npc,enemy}/; preview ->", os.path.relpath(PREVIEW, ROOT))


if __name__ == "__main__":
    main()
