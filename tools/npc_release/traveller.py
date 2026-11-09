"""NPC 09 — the traveller (旅人). Batch 3.

Design: docs/npc/batch3/DESIGN_PROPOSAL.md (PR #48, approved). Elderly and gender-neutral (no beard,
no make-up; a calm, slightly secretive mouth). The tallest of the villagers: the hat's crown reaches
the top of the frame; thin, long-limbed, a little stooped, the way of someone used to the road.
A narrow sun-browned face with deep lines on the cheeks and a thin nose; narrow eyes (almost a line),
one grey-green pixel of iris in the hat's shadow, the shadow of age under the lids. Grey hair tied at
the back in one tail (a white streak at the temple). A wide-brimmed hat with a crimson band; a dull
brown long coat to the calves, open at the front, its hem worn; a grey jacket under it, dark narrow
trousers, worn boots; a crimson scarf round the neck with one end hanging on the chest (it swings as
they walk). A leather backpack with a rolled dull-green bedroll on top. A long straight walking stick
held upright at the side in the right hand, a water gourd tied near its top (unlike the elder's carved
staff, held out in front). The stick, the scarf's end and the gourd are one-sided, so facing left is
drawn on its own.

Revision 1 (the review of 2026-11-09): from the front only the bedroll's small ends show, above the
shoulders behind the neck, with the pack's straps over the shoulders (they read as shoulder pads
before); the skin a tone lighter and the hat's shadow on the one row under the brim (the face was
the darkest of the villagers); the cheek lines joined into short lines (no scattered dots); the
stick stands still when they stand and is planted, passed, lifted and set down when they walk.

Map characters (one per pixel; see npc_common):
  0-4 hair (grey)   a-d skin 1-4   e eye line  o iris (grey-green)  l lines (wrinkles)  m mouth
  A-E coat (dull brown) 0-4   K-O jacket (grey) 0-4   P-T hat 0-4   F-J scarf (crimson) 0-4
  U-Y bedroll (dull green) 0-4   p-t pack leather (warm) 0-4   u-y trousers 0-4   @ shoulder anchor  * hand anchor
"""

from npc_common import Npc, Pose, capsule, gait, half, legend, rows_of, stamp

RAMPS = {
    "skin": ["#5a2e1c", "#bc7c56", "#daa47a", "#ecbc92", "#f8d2aa"],
    "hair": ["#34343c", "#6e6e78", "#9c9ca4", "#c2c2c8", "#e6e6ea"],
    "hat": ["#16140e", "#363226", "#524c3a", "#6e6850", "#8c866a"],
    "coat": ["#241e16", "#4c4030", "#6a5a44", "#86745c", "#a49278"],
    "pack": ["#28140a", "#5e3420", "#824c2e", "#a06642", "#bc845c"],
    "jacket": ["#22242a", "#4a4e56", "#6a6e76", "#888c94", "#a8acb2"],
    "scarf": ["#2c0610", "#6a1424", "#962234", "#bc3848", "#de6a74"],
    "bedroll": ["#141c10", "#34442a", "#4e6240", "#6a7e58", "#8c9e78"],
    "gourd": ["#3a2608", "#86601e", "#b4862e", "#d4a84a", "#ecc878"],
}
INK = {"e": "#2a1a14", "o": "#6e9a84", "l": "#83492c", "m": "#7a3a2a"}
LEG = legend(
    [("01234", "hair", 0), ("abcd", "skin", 1), ("ABCDE", "coat", 0), ("KLMNO", "jacket", 0), ("PQRST", "hat", 0),
     ("FGHIJ", "scarf", 0), ("UVWXY", "bedroll", 0), ("pqrst", "pack", 0), ("uvwxy", "trousers", 0)],
    {**{ch: ("skin", 2, col) for ch, col in INK.items()}, "@": ("coat", 2), "*": ("skin", 3)},
)

HEAD_TOP = 0
STOOP = 1  # side view: the head this far ahead of the body
BODY_TOP = 19

# ------------------------------------------------------------------ head (the hat's crown at row 0)

HEAD_FRONT = half("""
...........QRSSS
..........QRSSTS
..........QRRSSS
..........QRRSRR
..........PFGHHH
..........PFGGGG
....QRRSSSSSRRRR
..PQQQQQQRRRRRRR
...PPPPP11aaaaaa
........23bcdddd
........34bcccdd
........23b333cc
........2bbeoecc
........2bcdcccc
.........abldccc
..........blcccc
..........blcccc
...........abbmm
............abbb
.............aaa
""")

HEAD_BACK = half("""
...........QRSSS
..........QRSSTS
..........QRRSSS
..........QRRSRR
..........PFGHHH
..........PFGGGG
....QRRSSSSSRRRR
..PQQQQQQRRRRRRR
...PPPPP00000000
.........1232111
.........1123211
.........1112321
.........1211232
..........121123
...........12112
............1211
............aaaa
............aaaa
.............aaa
""")

# facing right: the brim reaches out in front; the face under it; the tail hangs at the back
HEAD_SIDE = rows_of("""
...........QRSSSS
..........QRRSSTSR
..........QRRSSSSR
..........QRRRSRRR
..........PFGHHHHG
..........PFGGGGGF
....QRRSSSSSSRRRRRRRR
...PQQQQQQQQRRRRRRRRRQ
.....PPP234PPaaaaaaPPP
........3432bccccccc
........2342bcc22bcc
.........232bcbeocccd
.........232bcbcccccdd
.........232bblccccccc
..........22bclccccbc
...........2abclcccmm
............abcccccc
.............aabbbb
..............aab
""")

# ------------------------------------------------------------------ body (rows from BODY_TOP)

BODY_FRONT = half("""
...........FGHHH
.........FGHIIHH
.......ABCFGHHHH
......ABCDFGGGGG
......ABCDpqBCKL
......ABCDpqBCKM
......ABCDpqBCKM
......ABCDpqBCKM
......ABCDpqBBKM
......ABCDpqBBKM
......ABCDpqCBKM
......ABCDpqCBKM
......ABCDDCCBKM
......ABCDDCCBKL
......ABCDCCCBqr
......ABCDCCCBKL
......ABCDCCCBKM
......ABCDCCCBKL
......ABCDCCCBKL
......ABCDCCCBuw
......ABCDCCCBuw
......ABCDCCCBuw
......ABCDCCCBuw
.....ABCDCCCCBuw
.....ABCDCCCCBuw
.....ABCDCCCCBuw
.....ABCDCCCCBuw
.....ABCDCCCCBuw
.....ABCDCCCCBuw
.....AABBABBAB.u
""")

BODY_BACK = half("""
...........FGHHH
.........FGHIIHH
.......ABCDDDDDD
......ABCDDCCCCC
......ABCDCCCCCC
......ABCDCCCCCC
......ABCDCCCCCC
......ABCDCCCCCC
......ABCDCCCCCC
......ABCDCCCCCC
......ABCDCCCCCC
......ABCDCCCCCC
......ABCDCCCCCC
......ABCDCCCCCC
......ABCDCCCCCC
......ABCDCCCCCB
......ABCDCCCCCB
......ABCDCCCCCB
......ABCDCCCCBC
......ABCDCCCCBC
......ABCDCCCCBC
......ABCDCCCCBC
......ABCDCCCCBC
.....ABCDCCCCCBC
.....ABCDCCCCCBC
.....ABCDCCCCCBC
.....ABCDCCCCCBC
.....ABCDCCCCCBC
.....ABCDCCCCCBC
.....AABBABBAABA
""")

# facing right, a little stooped: the shoulders forward, the coat open at the front
BODY_SIDE = rows_of("""
...............FGHHH
.............FGHIIHHG
...........ABCDFGHHHG
..........ABCDDDDCCKLM
..........ABCDDDCCCKLM
..........ABCDDCCCCKLM
..........ABCDCCCCCKLM
..........ABCDCCCCCKLM
..........ABCDCCCCCKLM
..........ABCDCCCCCKLM
..........ABCDCCCCCKLM
..........ABCDCCCCCKLM
..........ABCDCCCCCqrs
..........ABCDCCCCCKLM
..........ABCDCCCCCKLM
..........ABCDCCCCCKLM
..........ABCDCCCCCKLM
..........ABCDCCCCCKLMA
..........ABCDCCCCCCBCCB
..........ABCDCCCCCCBCCB
.........ABCDCCCCCCBCCCB
.........ABCDCCCCCCBCCCB
.........ABCDCCCCCCBCCCCB
.........ABCDCCCCCCBCCCCB
.........ABCDCCCCCCBCCCCB
.........ABCDCCCCCCBCCCCB
.........ABCDCCCCCCBCCCCCB
........ABCDCCCCCCCBCCCCCB
........ABCDCCCCCCCBCCCCCB
........AABBABBAABBABBAABA
""")


def stick(c, x, top, ground=55, tone=None, tip=None):
    """The walking stick: straight, a knot at the top; the water gourd hangs from a cord below it.
    tip: the x of its foot when it leans (the top at x, the foot at tip)."""
    tip = x if tip is None else tip
    for y in range(top, ground + 1):
        sx = round(x + (tip - x) * (y - top) / max(1, ground - top))
        c.put(sx, y, "wood", tone if tone is not None else (3 if y % 6 == 0 else 2))
    c.put(x, top - 1, "wood", 1 if tone is not None else 3)


def lean_x(x, top, ground, tip, y):
    """Where a leaning stick is at row y."""
    return round(x + (tip - x) * (y - top) / max(1, ground - top))


# walking, the stick is planted and the walker passes it, then it is lifted and swung ahead:
# per walk frame (top x offset, foot x offset, lift) facing right; front / back use the lift only
STICK_WALK = ((0, 1, 0), (0, 0, 0), (1, -1, 0), (1, -2, 0), (1, 0, 2), (1, 1, 1))


def gourd(c, x, y, side, tone=None, swing=0):
    """The gourd hangs on a short cord from the stick: a small bulb on a large one, a stopper on top.
    side: +1 hangs to the right of the stick, -1 to the left."""
    d = 1 if tone is None else 0
    gx = x + side * 2 + swing
    c.put(x + side, y, "pack", 1)
    c.put(gx, y + 1, "pack", 2)
    c.put(gx, y + 2, "gourd", 2 + d)
    c.rect(gx - 1, y + 3, gx + 1, y + 3, "gourd", 2 if tone is None else 1)
    c.rect(gx - 2, y + 5, gx + 2, y + 6, "gourd", 2 if tone is None else 1)
    c.rect(gx - 1, y + 4, gx + 1, y + 7, "gourd", 2 if tone is None else 1)
    c.put(gx - 1, y + 4, "gourd", 3 + d if tone is None else 2)
    c.put(gx - 1, y + 5, "gourd", 4 if tone is None else 2)
    c.line(gx - 1, y + 7, gx + 1, y + 7, "gourd", 1)
    c.put(gx - 1, y + 3, "gourd", 3 + d if tone is None else 2)


class Traveller(Npc):
    id = "traveller"
    ramps = RAMPS
    walk_gait = dict(stride=3, lift=2, bob=1, arm=2)

    def pose(self, action, i):
        if action == "idle":
            # breathing; the scarf's end stirs; the hand on the stick shifts its grip on the 3rd frame
            return Pose(breath=(0, 1, 1, 0)[i], sway=(0, 1, 0, -1)[i], blink=i == 3, glint=(0, 1, 2, 1)[i], prop=(0, 0, 1, 0)[i],
                        staff=(0, 0, 0))
        p = gait(i, 6, **self.walk_gait)
        p.staff = STICK_WALK[i]
        return p

    # -------------------------------------------------------------- front / back
    def legs_front(self, c, p, b, back):
        for (fwd, lift), x0 in ((p.near, 12), (p.far, 17)):
            y = min(55, 55 - lift + (1 if fwd > 1 else 0))
            c.rect(x0, 40 + b, x0 + 2, y - 4, "trousers")
            c.line(x0 + (2 if x0 < 16 else 0), 41 + b, x0 + (2 if x0 < 16 else 0), y - 5, "trousers", 1)
            c.rect(x0, y - 4, x0 + 2, y, "boot")
            c.rect(x0 - (1 if x0 < 16 else 0), y - 1, x0 + 2 + (0 if x0 < 16 else 1), y, "boot")
            c.line(x0 - (1 if x0 < 16 else 0), y, x0 + 2 + (0 if x0 < 16 else 1), y, "boot", 1)
            c.line(x0, y - 4, x0 + 2, y - 4, "boot", 1)  # the boot's worn top
            if not back:
                c.put(x0 + 1, y - 2, "boot", 3)

    def bedroll_front(self, c, t, back):
        """The bedroll across the top of the pack. From behind it lies over the pack, its rolled ends
        (spirals) past the shoulders. From the front only its ends show, small, behind the neck and
        above the shoulders (tucked under the hat's brim), with the pack's straps over the shoulders."""
        if not back:
            y = 14 + t
            c.rect(7, y, 24, y + 2, "bedroll", 1)
            for x, d in ((5, 1), (26, -1)):  # the roll's ends: a light ring round a dark middle
                x0, x1 = min(x, x + 2 * d), max(x, x + 2 * d)
                c.rect(x0, y, x1, y + 2, "bedroll", 2 if d > 0 else 1)
                c.put(x0, y, "bedroll", 4 if d > 0 else 3)
                c.put(x0 + 1, y, "bedroll", 3 if d > 0 else 2)
                c.put(x0, y + 1, "bedroll", 3 if d > 0 else 2)
                c.put(x0 + 1, y + 1, "bedroll", 0)  # the spiral's core
                c.put(x1, y + 2, "bedroll", 1)
            return
        y = 16 + t
        c.rect(5, y, 26, y + 3, "bedroll")
        c.line(6, y, 25, y, "bedroll", 3)
        c.line(5, y + 1, 26, y + 1, "bedroll", 2)
        c.line(5, y + 2, 26, y + 2, "bedroll", 2)
        c.line(6, y + 3, 25, y + 3, "bedroll", 1)
        for x, d in ((3, 1), (28, -1)):  # the roll's ends: round, with a spiral
            c.rect(min(x, x + d), y, max(x, x + d), y + 3, "bedroll", 2)
            c.put(x + d, y + 1, "bedroll", 3 if d > 0 else 2)
            c.put(x + d, y + 2, "bedroll", 1)
            c.put(x, y + 1, "bedroll", 1)
            c.put(x, y + 2, "bedroll", 2)
        for x in (8, 23):  # the straps round it
            c.line(x, y, x, y + 3, "pack", 2 if x < 16 else 1)
        if back:  # the pack itself, under the roll
            c.rect(9, y + 4, 22, y + 17, "pack")
            c.line(10, y + 4, 21, y + 4, "pack", 3)
            c.rect(10, y + 6, 21, y + 9, "pack", 2)
            c.line(10, y + 9, 21, y + 9, "pack", 1)  # the flap
            c.put(15, y + 8, "gold", 2)  # the buckle
            c.put(16, y + 8, "gold", 1)
            c.rect(11, y + 11, 20, y + 16, "pack", 2)
            c.line(11, y + 16, 20, y + 16, "pack", 1)
            c.line(9, y + 4, 9, y + 17, "pack", 2)
            c.line(22, y + 4, 22, y + 17, "pack", 1)

    def front(self, p, back=False):
        c = self.canvas()
        b = p.bob
        up = -p.breath
        t = b + up
        self.legs_front(c, p, b, back)
        if not back:
            self.bedroll_front(c, t, back)

        def shift(row, col, ch):
            y = BODY_TOP + row
            dx = round(p.sway * (y - 40) / 8) if y > 40 and (col < 8 or col > 23) else 0
            return dx, b + (up if y < 36 else 0)
        if up:
            stamp(c, BODY_BACK if back else BODY_FRONT, 0, BODY_TOP, LEG, mirrored=True, shift=lambda r, x, ch: (shift(r, x, ch)[0], b))
        stamp(c, BODY_BACK if back else BODY_FRONT, 0, BODY_TOP, LEG, mirrored=True, shift=shift)
        if back:
            self.bedroll_front(c, t, back)
        else:  # the pack's straps come over the shoulders: it is carried on the back
            for x, tone in ((8, 2), (23, 1)):
                c.line(x, 20 + t, x + (1 if x < 16 else -1), 22 + t, "pack", tone)
                c.line(x + (1 if x < 16 else -1), 23 + t, x + (1 if x < 16 else -1), 27 + t, "pack", tone)
        # the arms: the right (image left in front) holds the stick at its side; the left hangs and swings
        stick_side = 0 if not back else 1  # 0: image left
        # the stick stands still when they stand (only the hand shifts its grip); walking it is
        # planted, then lifted and set down again
        sx = 4 if stick_side == 0 else 27
        lift = p.staff[2]
        hand_y = 33 + t - lift - (1 if p.prop > 0 and not self.walking else 0)
        for side in (0, 1):
            holds = side == stick_side
            far = side == (1 if not back else 0)
            shx = 7 if side == 0 else 24
            d = -1 if side == 0 else 1
            tone = 1 if far else None
            if holds:
                hx = sx + (1 if side == 0 else -1)
                capsule(c, shx, 22 + t, shx + d, 27 + t, 1.6, "coat", tone)
                capsule(c, shx + d, 27 + t, hx, hand_y - 1, 1.4, "coat", tone)
                c.line(hx - 1, hand_y - 2, hx + 1, hand_y - 2, "coat", 1)  # the cuff
                self.hand = (hx, hand_y)
            else:
                swing = p.arm_far if not back else p.arm_near
                hx = shx + d
                hy = 36 + t - max(0, swing)
                capsule(c, shx, 22 + t, shx + d, 28 + t, 1.6, "coat", tone)
                capsule(c, shx + d, 28 + t, hx, hy - 2, 1.4, "coat", tone)
                c.line(hx - 1, hy - 2, hx + 1, hy - 2, "coat", 1)
                c.rect(hx - 1, hy - 1, hx + 1, hy, "skin", 1 if far else 2)
                c.put(hx, hy + 1, "skin", 1 if far else 2)
        stick(c, sx, 3 + t - lift, ground=55 - lift, tone=None)
        hx, hy = self.hand
        c.rect(sx - 1, hy - 1, sx + 1, hy + 1, "skin", 2)
        c.put(sx - 1, hy - 1, "skin", 3)
        c.put(sx + 1, hy + 1, "skin", 1)
        gourd(c, sx, 10 + t - lift, -1 if stick_side == 0 else 1, swing=0)
        stamp(c, HEAD_BACK if back else HEAD_FRONT, 0, HEAD_TOP + t, LEG, mirrored=True)
        if back:
            self.tail_back(c, p, t)
        else:
            self.face_details(c, p, t)
            self.scarf_end_front(c, p, t)
        return c

    walking = False

    def face_details(self, c, p, t):
        top = HEAD_TOP + t
        for y in (13, 14, 15):  # the thin nose: a shadow down one side
            c.put(16, top + y, "skin", 1)
        c.put(15, top + 15, "skin", 1)
        c.put(18, top + 17, "skin", 3)  # one corner of the mouth a little up: calm, a little secretive
        c.put(18, top + 16, "skin", 2)
        c.paint(18, top + 16, INK["m"])
        c.put(9, top + 9, "hair", 4)  # the white streak at the temple
        c.put(9, top + 10, "hair", 4)
        if p.blink:
            for x in (11, 12, 13, 18, 19, 20):
                c.put(x, top + 12, "skin", 2)
                c.paint(x, top + 12, INK["e"])

    def scarf_end_front(self, c, p, t):
        """The scarf's end hangs on the right side of the chest (image left) and stirs."""
        for k in range(10):
            y = 22 + t + k
            x = 11 + (round(p.sway * k / 7) if k > 3 else 0)
            c.put(x, y, "scarf", 3 if k < 8 else 2)
            c.put(x + 1, y, "scarf", 2 if k < 8 else 1)
        y = 32 + t
        x = 11 + round(p.sway * 9 / 7)
        for k in range(3):  # the fringe
            c.put(x + k - (1 if k == 2 else 0), y, "scarf", 1)
        c.put(x, y + 1, "scarf", 1)

    def tail_back(self, c, p, t):
        """The grey tail hangs down the back from under the hat, tied with a crimson cord."""
        for k in range(10):
            y = 16 + t + k
            x = 15 + (round(p.sway * k / 8))
            c.put(x, y, "hair", 3 if k % 2 == 0 else 2)
            c.put(x + 1, y, "hair", 2 if k % 2 == 0 else 1)
        c.put(15, 17 + t, "scarf", 3)
        c.put(16, 17 + t, "scarf", 2)
        c.put(15, 26 + t, "hair", 2)  # the tip

    # -------------------------------------------------------------- side
    def frame(self, action, d, i):
        self.walking = action == "walk"
        return super().frame(action, d, i)

    def side(self, p, swap=False):
        c = self.canvas()
        b = p.bob
        up = -p.breath
        t = b + up
        hip = (15, 40 + b)

        def leg(fwd, lift, tone):
            ax, ay = hip[0] + fwd, 52 - lift
            kx, ky = hip[0] + fwd * 0.6 + (1.5 if lift else 0.5), (hip[1] + ay) / 2 - lift * 0.5
            capsule(c, hip[0], hip[1], kx, ky, 1.7, "trousers", tone)
            capsule(c, kx, ky, ax, ay - 1, 1.5, "trousers", tone)
            toe = 3 if lift < 2 else 2
            c.rect(int(ax) - 2, ay - 2, int(ax) + 1, ay + 2, "boot", tone)
            c.rect(int(ax) - 2, ay, int(ax) + toe, ay + 2, "boot", tone)
            c.line(int(ax) - 2, ay - 2, int(ax) + 1, ay - 2, "boot", 1)
            yy = ay + 3 - (1 if lift > 1 else 0)
            c.line(int(ax) - 2, yy, int(ax) + toe, yy, "boot", 0 if tone == 1 else 1)
            if tone is None:
                c.put(int(ax) + 1, ay, "boot", 3)

        # the stick in the right hand: walking it is planted ahead, the walker passes it (it leans
        # forward, its foot stays on the ground), then it is lifted and swung ahead (STICK_WALK)
        top_dx, tip_dx, lift = p.staff
        s_top, s_ground = 3 + t - lift, 55 - lift
        stick_x = 24 + top_dx
        tip_x = 24 + tip_dx
        hand_y = 32 + t - lift - (1 if p.prop > 0 and not self.walking else 0)
        hand_x = lean_x(stick_x, s_top, s_ground, tip_x, hand_y)  # where the hand holds it
        hand = (hand_x - 1, hand_y)
        sh = (17, 22 + t)

        def arm_stick(far):
            tone = 1 if far else None
            ex, ey = 19, 27 + t
            capsule(c, sh[0], sh[1], ex, ey, 1.7, "coat", tone)
            capsule(c, ex, ey, hand[0] - 1, hand[1] - 1, 1.5, "coat", tone)
            c.line(hand[0] - 2, hand[1] - 2, hand[0] - 2, hand[1], "coat", 1)

        def hand_on_stick(far):
            tone = 1 if far else 2
            c.rect(hand_x - 1, hand[1] - 1, hand_x + 1, hand[1] + 1, "skin", tone)
            if not far:
                c.put(hand_x - 1, hand[1] - 1, "skin", 3)

        def arm_free(swing, far):
            tone = 1 if far else None
            hx, hy = sh[0] - 1 + swing * 1.5, sh[1] + 14
            ex, ey = sh[0] - 1 + swing * 0.6, sh[1] + 7
            capsule(c, sh[0] - 1, sh[1], ex, ey, 1.7, "coat", tone)
            capsule(c, ex, ey, hx, hy - 1, 1.5, "coat", tone)
            c.line(int(hx) - 1, int(hy) - 1, int(hx) + 1, int(hy) - 1, "coat", 1)
            c.rect(int(hx) - 1, int(hy), int(hx) + 1, int(hy) + 1, "skin", 1 if far else 2)

        # far side
        leg(p.far[0], p.far[1], 1)
        if swap:  # facing left: the stick and its hand are on the far side
            stick(c, stick_x, s_top, ground=s_ground, tone=1, tip=tip_x)
            gourd(c, stick_x, s_top + 7, 1, tone=1)
            arm_stick(True)
            hand_on_stick(True)
        else:
            arm_free(p.arm_far, True)
        leg(p.near[0], p.near[1], None)

        def shift(row, col, ch):
            y = BODY_TOP + row
            dx = -round(p.sway * (y - 40) / 8) if y > 40 and col < 13 else 0
            return dx, b + (up if y < 36 else 0)
        if up:
            stamp(c, BODY_SIDE, 0, BODY_TOP, LEG, shift=lambda r, x, ch: (shift(r, x, ch)[0], b))
        stamp(c, BODY_SIDE, 0, BODY_TOP, LEG, shift=shift)
        self.pack_side(c, p, t)
        stamp(c, HEAD_SIDE, STOOP, HEAD_TOP + t, LEG)  # the head a pixel ahead of the chest: the stoop
        self.tail_side(c, p, t)
        top = HEAD_TOP + t
        c.put(10 + STOOP, top + 9, "hair", 4)  # the white streak
        c.put(10 + STOOP, top + 10, "hair", 4)
        if p.blink:
            for x in (14 + STOOP, 15 + STOOP, 16 + STOOP):
                c.put(x, top + 11, "skin", 2)
                c.paint(x, top + 11, INK["e"])
        if not swap:
            stick(c, stick_x, s_top, ground=s_ground, tip=tip_x)
            gourd(c, stick_x, s_top + 7, 1)
            arm_stick(False)
            hand_on_stick(False)
            self.scarf_end_side(c, p, t)
        else:
            arm_free(p.arm_near, False)
        return c

    def pack_side(self, c, p, t):
        """The pack on the back and the bedroll on top, its rolled end facing us: a spiral."""
        y = 18 + t
        c.rect(5, y + 4, 10, y + 17, "pack")
        c.line(5, y + 4, 10, y + 4, "pack", 3)
        c.line(5, y + 5, 5, y + 17, "pack", 1)
        c.rect(6, y + 7, 9, y + 10, "pack", 2)  # the pocket
        c.line(6, y + 10, 9, y + 10, "pack", 1)
        c.put(8, y + 9, "gold", 2)
        c.line(10, y + 5, 10, y + 17, "pack", 2)
        # the roll's end: a ring of green round a darker middle
        c.ellipse(8, y + 2.5, 3.4, 2.6, "bedroll")
        c.put(8, y + 2, "bedroll", 1)
        c.put(9, y + 2, "bedroll", 1)
        c.put(8, y + 3, "bedroll", 1)
        c.put(7, y + 1, "bedroll", 3)
        c.put(6, y + 2, "bedroll", 3)
        c.line(10, y, 10, y + 5, "pack", 1)  # the strap
        # the shoulder strap crossing the coat
        c.line(13, y + 3, 13, y + 11, "pack", 2)

    def tail_side(self, c, p, t):
        """The grey tail at the back of the head, over the bedroll's strap."""
        for k in range(6):
            y = 17 + t + k
            x = 9 + STOOP - (round(p.sway * k / 6) if k > 2 else 0)
            c.put(x, y, "hair", 3 if k % 2 == 0 else 2)
            c.put(x + 1, y, "hair", 2 if k % 2 == 0 else 1)
        c.put(9 + STOOP, 17 + t, "scarf", 3)
        c.put(10 + STOOP, 17 + t, "scarf", 2)

    def scarf_end_side(self, c, p, t):
        """The scarf's end over the front of the chest (the right side: near when facing right)."""
        for k in range(9):
            y = 21 + t + k
            x = 20 + (round(-p.sway * k / 6) if k > 2 else 0) + (1 if k > 5 and self.walking else 0)
            c.put(x, y, "scarf", 3 if k < 7 else 2)
            c.put(x + 1, y, "scarf", 2 if k < 7 else 1)
        c.put(20 + round(-p.sway * 9 / 6), 30 + t, "scarf", 1)


NPC = Traveller()
