"""NPC 03 — the guard (見張り): the soldier who watches over the village.

Tall and broad-shouldered; an iron helmet with a nose guard, sharp eyes, stubble; iron pauldrons and
breastplate under a blue-grey surcoat with the village crest in gold (a ring round a four-pointed
star: the wind vane of 風見の村); a dark gambeson, leather bracers and boots; a spear in his right hand.
Map characters (one per pixel; see npc_common):
  0-4 hair (dark brown)   a-d skin 1-4   n brow  e lash  k l iris  m mouth  z stubble
  A-E surcoat (blue-grey) 0-4   F-J iron 0-4   K-O gambeson / trousers 0-4   P-T leather 0-4
  f-j gold 0-4   U-Y wood (the spear's shaft) 0-4
  @ shoulder anchor  * hand anchor (skin)
"""

from npc_common import (Npc, capsule, half, legend, rows_of, stamp, stamp_at)

RAMPS = {
    "hair": ["#160e08", "#3a2414", "#5a3a22", "#7a5434", "#9a7048"],
    "skin": ["#5e3424", "#b47a5a", "#e0aa84", "#f2c4a0", "#ffdcc0"],
    "coat": ["#10161e", "#2e3e50", "#4a6078", "#6a849c", "#98b2c6"],
    "iron": ["#14161c", "#40464f", "#6c7480", "#9aa2ae", "#d4dae2"],
    "cloth": ["#0e0e14", "#1e2028", "#2e3240", "#424858", "#5a6274"],
}
LEG = legend(
    [("01234", "hair", 0), ("abcd", "skin", 1), ("ABCDE", "coat", 0), ("FGHIJ", "iron", 0), ("KLMNO", "cloth", 0),
     ("PQRST", "leather", 0), ("fghij", "gold", 0), ("UVWXY", "wood", 0)],
    {"n": ("skin", 2, "#2a1a12"), "e": ("skin", 2, "#1e1820"), "k": ("skin", 2, "#5a7a4a"), "l": ("skin", 2, "#2e4428"),
     "m": ("skin", 2, "#7a3c34"), "z": ("skin", 2, "#a8806a"), "@": ("cloth", 2), "*": ("skin", 3)},
)

# ------------------------------------------------------------------ front (left half; mirrored)

HEAD_FRONT = half("""
...........HIIII
.........HIJJJII
........HIJJIIII
.......HIJIIIIII
......HIJIIIIIIJ
......HIIIIIIIIJ
.....GHIIIIIIIIJ
.....GHIIIIIIIHJ
....GHHHHHHHHHHI
....FGGGGGGGGGGH
......2bcnnncccH
......2bcccnnccH
......2bceeeeccH
.....abccclkccdH
.....abccccccccG
.....abcccccccbb
......bccczccczc
......bczcccccmm
.......bcczcczcc
........abbzbbzb
""")

HEAD_BACK = half("""
...........HIIII
.........HIJJJII
........HIJJIIII
.......HIJIIIIII
......HIJIIIIIII
......HIIIIIIIII
.....GHIIIIIIIII
.....GHIIIIIIIII
....GHHHHHHHHHHH
....FGGGGGGGGGGG
......2233333333
.....a2343343343
.....a2343343343
......2343343343
......2233233233
.......bbbbbbbbb
........bbbbbbbb
""")

BODY_FRONT = half("""
.........KLMMMMM
....GHIIHGHIJJJJ
...GHIJIIHGHIJJI
...GHIJIIHGHIIII
...GHIIIIHFGHHHH
...FGHHHHGBCDDDD
.......BCDDCCCCC
.......BCDDCCCCC
.......BCDCCCCCC
.......BCDCCCCCC
.......BCDCCCCCC
.......BCDCCCCCC
.......BCDCCCCCC
.......BCCCCCCCC
.......PQRRRRRgh
.......PQQQQQQhi
.......BCDCCCCCA
......BCDCCCCCCA
......BCDCCCCCCA
......BCDCCCCCCA
......BCDCCCCCCA
......BCCCCCCCCA
......fggggggggA
""")

BODY_BACK = half("""
.........KLMMMMM
....GHIIHGBCDDDD
...GHIJIIHBCDDDD
...GHIJIIHBCDDCC
...GHIIIIHBCDCCC
...FGHHHHGBCDCCC
.......BCDDCCCCC
.......BCDCCCCCC
.......BCDCCCCCC
.......BCDCCCCCC
.......BCDCCCCCC
.......BCDCCCCCC
.......BCCCCCCCC
.......PQRRRRRRR
.......PQQQQQQQQ
.......BCDCCCCCC
.......BCDCCCCCC
......BCDCCCCCCC
......BCDCCCCCCC
......BCDCCCCCCC
......BCDCCCCCCC
......BCCCCCCCCC
......fggggggggg
""")
BODY_TOP = 20

# the village crest: a ring round a four-pointed star (the wind vane)
CREST = rows_of("""
..ghhg..
.h....h.
g..ij..g
h.ijji.h
g..ji..g
.h....h.
..gghg..
""", 8)

ARM = rows_of("""
.@L.
KLMM
KLMM
KLML
KLML
PQRS
PRSS
PRSR
PQRQ
.b*c
.bbb
""", 4)

SPEAR_HEAD = rows_of("""
..I..
.IJH.
.IJH.
HIJHG
HIJHG
.IJG.
.HIG.
..H..
.PRQ.
..R..
""", 5)


def spear(c, x, top, tone=None, glint=0):
    stamp_at(c, SPEAR_HEAD, "I", "*", (x, top), LEG, darker=tone is not None)
    if tone is None:  # a glint runs down the blade
        c.put(x - 1, top + 1 + glint * 2, "iron", 4)
    for y in range(top + 10, 56):
        c.put(x, y, "wood", tone if tone is not None else (3 if y % 6 == 0 else 2))
    c.put(x, 55, "iron", 1)


# ------------------------------------------------------------------ side (facing right)

HEAD_SIDE = rows_of("""
............HIIIIIH
..........HIJJJIIIIH
.........HIJJIIIIIIIH
........HIJIIIIIIIIIIH
........HIIIIIIIIIIIIIH
.......GHIIIIIIIIIIIIIH
.......GHIIIIIIIIIIIIIIH
.......GHIIIIIIIIIIIIIIH
......GHHHHHHHHHHHHHHHHHH
......FGGGGGGGGGGGGGGGGGH
.........221bcccccccnnncH
.........21babccccccccnnH
.........21aabcccccceeeeH
.........21abbcccccccklcGd
.........2abbcccccccccccddc
..........abcccccccccccbbb
..........abczcczcczccmmm
...........bzczczczczccc
............bzczczczccb
.............bbzbzbzbb
""")

BODY_SIDE = rows_of("""
...........KLMMMK
.........BCDCCCCHI
........BCDCCCCCHIJ
.......BCDCCCCCCHIJJ
.......BCDCCCCCCHIJJH
.......BCDCCCCCCCHIJH
.......BCDCCCCCCCHIIH
.......BCDCCCCCCCCHIH
.......BCDCCCCCCCCHHG
.......BCDCCCCCCCCCCB
.......BCDCCCCCCCCCCB
.......BCDCCCCCCCCCCB
.......BCDCCCCCCCCCCB
.......BCCCCCCCCCCCCB
.......PQRRRRRRRRRRRQP
.......PQQQQQQQQQQQQQP
.......BCDCCCCCCCCCCCB
......BCDCCCCCCCCCCCCB
......BCDCCCCCCCCCCCCB
......BCDCCCCCCCCCCCCB
......BCDCCCCCCCCCCCCB
......BCCCCCCCCCCCCCCB
......fgggggggggggggggf
""")

# side view arms: the pauldron on the shoulder, the gambeson sleeve, the leather bracer, the hand
ARM_SIDE_SPEAR = rows_of("""
..H@JI...........
.GHIJJIH.........
.GHIIIIH.........
.FGHHHGF.........
..KLMMK..........
..KLMNK..........
..KLMMK..........
..KLMMLPQRRRSS...
...KLLPQRSSTTScc.
....PQQQRRRRQbc*.
.............bb..
""", 17)
ARM_SIDE_HANG = rows_of("""
..H@JI.
.GHIJJH
.GHIIIH
.FGHHGF
..KLMK.
..KLMK.
..KLNK.
..KLMK.
..PRSQ.
..PRTQ.
..PRSQ.
..PQRQ.
..bcc..
..b*c..
""", 7)


def arm_hang(c, sh, swing, far):
    """The free arm, hanging; its forearm swings forward (+) / back (-)."""
    ax, ay = 3, 0
    for y, row in enumerate(ARM_SIDE_HANG):
        dx = round(swing) if y >= 8 else round(swing / 2) if y >= 4 else 0
        for x, ch in enumerate(row):
            if ch == ".":
                continue
            m, t = LEG[ch][0], LEG[ch][1]
            if far and t is not None and t > 1:
                t -= 1
            c.put(sh[0] + x - ax + dx, sh[1] + y - ay, m, t)


class Guard(Npc):
    # the maps, as attributes so a revision (a subclass) can replace them
    HEAD_FRONT = HEAD_FRONT
    HEAD_BACK = HEAD_BACK
    BODY_FRONT = BODY_FRONT
    BODY_BACK = BODY_BACK
    CREST = CREST
    id = "guard"
    ramps = RAMPS
    walk_gait = dict(stride=3, lift=2, bob=1, arm=2)

    def legs_front(self, c, p, b, back):
        for (fwd, lift), x0 in ((p.near, 9), (p.far, 18)):
            down = 1 if fwd > 1 else 0
            y = min(55, 55 - lift + down)
            c.rect(x0, 40 + b, x0 + 4, y - 8, "cloth")
            c.rect(x0 - (1 if x0 < 16 else 0), y - 8, x0 + 4 + (0 if x0 < 16 else 1), y - 7, "leather", 3)  # boot cuff
            c.rect(x0, y - 6, x0 + 4, y, "boot")
            c.rect(x0 - (1 if x0 < 16 else 0), y - 1, x0 + 4 + (0 if x0 < 16 else 1), y, "boot")
            c.line(x0 - (1 if x0 < 16 else 0), y, x0 + 4 + (0 if x0 < 16 else 1), y, "boot", 1)
            if not back:
                c.rect(x0 + 1, y - 5, x0 + 3, y - 3, "iron")  # the greave's plate
                c.put(x0 + 1, y - 5, "iron", 4)

    # -------------------------------------------------------------- front / back
    def front(self, p, back=False):
        c = self.canvas()
        b = p.bob
        up = -p.breath
        self.legs_front(c, p, b, back)

        def shift(row, col, ch):
            y = BODY_TOP + row
            dx = round(p.sway * (y - 36) / 6) if y > 36 and ch in "ABCDEfghij" else 0
            return dx, b + (up if y < 34 else 0)
        stamp(c, self.BODY_BACK if back else self.BODY_FRONT, 0, BODY_TOP, LEG, mirrored=True, shift=shift)
        stamp(c, self.CREST, 12, 27 + b + up, LEG)
        sh_r = (5, 25 + b + up) if not back else (26, 25 + b + up)
        sh_l = (26, 25 + b + up) if not back else (5, 25 + b + up)
        free_swing = max(0, p.arm_far if not back else p.arm_near)
        stamp_at(c, ARM, "@", "*", (sh_l[0], sh_l[1] - free_swing), LEG, flip=not back, darker=back)
        hand = stamp_at(c, ARM, "@", "*", sh_r, LEG, flip=back)
        sx = 2 if not back else 29
        spear(c, sx, 1 + b + (1 if p.prop > 0 else 0), glint=p.glint)  # held: it does not breathe
        for dy in (-1, 0, 1):  # the fist round the shaft
            c.put(sx, hand[1] + dy, "skin", 3 if dy < 1 else 2)
        c.put(sx + (1 if not back else -1), hand[1], "skin", 2)
        stamp(c, self.HEAD_BACK if back else self.HEAD_FRONT, 0, 1 + b + up, LEG, mirrored=True)
        if p.blink and not back:  # eyes shut: the lash line drops over the eye
            for x in (9, 10, 11, 12, 19, 20, 21, 22):
                c.put(x, 13 + b + up, "skin", 2)
                c.paint(x, 13 + b + up, "#1e1820")
                c.put(x, 14 + b + up, "skin", 3)
        return c

    # -------------------------------------------------------------- side
    def side(self, p, swap=False):
        c = self.canvas()
        b = p.bob
        up = -p.breath
        hip = (15, 41 + b)
        sh = (14, 25 + b + up)
        spear_x = 28

        def leg(fwd, lift, tone):
            ax, ay = hip[0] + fwd, 52 - lift
            kx, ky = hip[0] + fwd * 0.6 + (1.5 if lift else 0.5), (hip[1] + ay) / 2 - lift * 0.5
            capsule(c, hip[0], hip[1], kx, ky, 2.2, "cloth", tone)
            capsule(c, kx, ky, ax, ay - 3, 2.0, "cloth", tone)
            capsule(c, ax, ay - 5, ax, ay, 2.1, "boot", tone)
            c.rect(int(ax) - 2, ay - 5, int(ax) + 2, ay - 4, "leather", 3 if tone is None else 1)
            toe = 4 if lift < 2 else 3
            c.rect(int(ax) - 1, ay + 1, int(ax) + toe, ay + 3 - (1 if lift > 1 else 0), "boot", tone)
            c.line(int(ax) - 1, ay + 3 - (1 if lift > 1 else 0), int(ax) + toe, ay + 3 - (1 if lift > 1 else 0), "boot", 0 if tone == 1 else 1)
            if tone is None:
                c.rect(int(ax), ay - 3, int(ax) + 1, ay - 1, "iron")

        def arm_spear(far):
            hand = stamp_at(c, ARM_SIDE_SPEAR, "@", "*", (sh[0], sh[1] - 3), LEG, darker=far)
            for dy in (-1, 0, 1):  # the fist closes round the shaft
                c.put(spear_x, hand[1] + dy, "skin", (1 if far else 3) if dy < 1 else (1 if far else 2))

        def arm_swing(swing, far):
            arm_hang(c, (sh[0], sh[1] - 3), swing * 1.5, far)

        top = 1 + b + up
        leg(p.far[0], p.far[1], 1)
        if swap:
            spear(c, spear_x, 1 + b + (1 if p.prop > 0 else 0), tone=1)
            arm_spear(True)
        else:
            arm_swing(p.arm_far, True)

        def shift(row, col, ch):
            y = BODY_TOP + row
            dx = -round(p.sway * (y - 36) / 6) if y > 36 and col < 12 and ch in "ABCDEfghij" else 0
            return dx, b + (up if y < 33 else 0)
        stamp(c, BODY_SIDE, 0, BODY_TOP, LEG, shift=shift)
        leg(p.near[0], p.near[1], None)
        stamp(c, HEAD_SIDE, 0, top, LEG)
        if p.blink:
            for x in (20, 21, 22, 23):
                c.put(x, top + 12, "skin", 2)
                c.paint(x, top + 12, "#1e1820")
            for x in (21, 22):
                c.put(x, top + 13, "skin", 3)
        if swap:
            arm_swing(p.arm_near, False)
        else:
            spear(c, spear_x, 1 + b + (1 if p.prop > 0 else 0), glint=p.glint)
            arm_spear(False)
        return c


NPC = Guard()
