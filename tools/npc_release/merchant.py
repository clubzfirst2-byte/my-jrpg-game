"""NPC 02 — the merchant (雑貨屋): the village's general store.

Middle-aged and stout, round shoulders and a round face, round glasses, a black moustache, a broad
smile, short black hair with a pen tucked behind his right ear; a white shirt with the sleeves rolled
up, a crimson vest with gold buttons, a leather belt, golden-brown trousers; a big leather purse on
his right hip and an account book (cream cover, dark binding) held in his left hand.
Map characters (one per pixel; see npc_common):
  0-4 hair (black)   a-d skin 1-4   n brow  e lash  m mouth  r blush  w lens glint
  A-E vest (crimson) 0-4   F-J shirt (white) 0-4   K-O trousers (golden brown) 0-4
  P-T leather 0-4          f-j gold 0-4            p q s t u book cover 0-4   U-Y wood (the pen) 0-4
  @ shoulder anchor  * hand anchor (skin)
"""

from npc_common import (Npc, capsule, half, legend, rows_of, stamp, stamp_at)

RAMPS = {
    "hair": ["#0c0b12", "#211f2c", "#353346", "#4d4b64", "#6c6a88"],
    "skin": ["#6a3a28", "#c48a66", "#eeba92", "#fcd2ac", "#ffe8d0"],
    "vest": ["#22070c", "#5c1622", "#8a2632", "#b2404a", "#d4686c"],
    "shirt": ["#4a4640", "#a8a296", "#e4e0d6", "#f6f4ee", "#ffffff"],
    "trousers": ["#2c1c08", "#6a4618", "#986a28", "#bc8c3e", "#dcb466"],
    "cover": ["#3a3226", "#a49478", "#d8cca8", "#ece2c4", "#fffaea"],
}
LEG = legend(
    [("01234", "hair", 0), ("abcd", "skin", 1), ("ABCDE", "vest", 0), ("FGHIJ", "shirt", 0), ("KLMNO", "trousers", 0),
     ("PQRST", "leather", 0), ("fghij", "gold", 0), ("pqstu", "cover", 0), ("UVWXY", "wood", 0)],
    {"n": ("skin", 2, "#24202a"), "e": ("skin", 2, "#2a2230"), "m": ("skin", 2, "#9a4a42"), "r": ("skin", 2, "#f0a08c"),
     "w": ("skin", 2, "#f4fbff"), "@": ("shirt", 2), "*": ("skin", 3)},
)

# ------------------------------------------------------------------ front (left half; mirrored)

HEAD_FRONT = half("""
..........233333
........23344443
.......233444332
......2334433221
.....23343322112
.....233322cddcc
.....233dddddccc
.....232cddddccc
.....22ccnnnnccc
....ab2chhhhhccc
....ab2chwccchhh
....abcchceechcc
....acccheccehcc
....bcccchhhhccd
.....bcrrccccccb
.....bccc1233221
.....abc21cmcccc
......abcccdmmmm
.......abcccdccc
........aabbbbbb
""")

HEAD_BACK = half("""
..........233333
........23344443
.......234444433
......2344443333
.....23443433433
.....23433433433
.....23433433433
.....23433433433
.....22433433433
....a22333333333
....ab2233233233
....ab2223223223
.....b2222222222
.....bb222222222
......bbb1221111
.......bcbbcbbbb
........bbbbbbbb
""")

BODY_FRONT = half("""
........BCDDDHII
......BCDDDDCHIJ
.....BCDDDDCCHII
....BCDDDCCCCiHI
....BCDDCCCCCBHI
....BCDCCCCCCiHI
....BCDCCCCCCBHI
....BCDCCCCCCBII
...BCDCCCCCCCiHI
...BCDCCCCCCCBHI
...BCDCCCCCCCBII
...BCDCCCCCCCiHI
...BCDCCCCCCCBHI
...BCDCCCCCCCBII
...BCCCCCCCCCBHI
...BCCCCCCCCBGHH
...PQRRRRSSRRRRR
...PQQQQQQQQQQgh
....KLMMMMMMMMMM
....KLMMMMMMMMMM
....KLMMMMMMLMMM
""")

BODY_BACK = half("""
........BCDDDDDD
......BCDDDDDDCC
.....BCDDDDDCCCC
....BCDDDDCCCCCC
....BCDDCCCCCCCB
....BCDCCCCCCCCB
....BCDCCCCCCCCB
....BCDCCCCCCCCB
...BCDCCCCCCCCCB
...BCDCCCCCCCCCB
...BCDCCCCCCCCCB
...BCCCCCCCCCCCB
...BCCCCCCCCCCCB
...BCCCCCCCCCCCB
...BCCCCCCCCCCCB
...BCCCCCCCCCCCB
...PQRRRRSSRRRRR
...PQQQQQQQQQQQQ
....KLMMMMMMMMMM
....KLMMMMMMMMMM
....KLMMMMMMLMMM
""")
BODY_TOP = 22

# the right arm hanging (front: image left): the rolled-up sleeve, a bare forearm, the hand
ARM_DOWN = rows_of("""
.@HH.
FGHIG
FGHIG
FGHIG
GIJIG
GHIHG
.bcc.
.bcc.
.bcd.
.bcc.
.b*c.
..bb.
""", 5)
# the left arm (front: image right) bent, holding the book against his belly
ARM_BOOK = rows_of("""
.HH@.
GIHGF
GIHGF
GIHGF
GIJIG
GHIHG
.cccb
.bccb
bcccb
""", 5)

# the account book from the front: cream cover, dark binding on its left, lines of ink
BOOK_FRONT = rows_of("""
QRRRRRR
Qtsssss
Qtsssss
Qts000s
Qtsssss
Qts00ss
Qtsssss
Qts000s
Qtsssss
Qqqqqqq
""", 7)
BOOK_SIDE = rows_of("""
Rs
Rs
Rs
Rs
Rs
Rs
Rs
Rs
Rq
""", 2)

# the big purse, hanging from the belt on his right hip
PURSE = rows_of("""
.QRQ.
QRSRQ
RihSR
RSSSR
RSSRQ
.QRQ.
""", 5)

# the pen behind his right ear (front view: image left)
PEN_FRONT = [(2, 8, "X"), (3, 9, "W"), (4, 10, "W"), (5, 11, "V"), (6, 12, "0")]

# ------------------------------------------------------------------ side (facing right)

HEAD_SIDE = rows_of("""
............233333
..........2334444332
.........233444433322
........2334443332221
........23344433222dcb
.......23334432211dddcb
......23333432ddddddcccb
......233332cdddddcnnncb
......23332bccccchhhhhcb
......2332bhhhhhhhwccchb
......2332abccccchceeech
......232abacccchccccchc
......232aabcccchhhhhhcd
........2bbcccccrrccccdc
........2bccccccc1233332
.........abccccc21122c1
.........abcccccccmmmmc
..........abccccccccdc
...........aabbbbbbbb
""")

BODY_SIDE = rows_of("""
..........BCDDDHII
........BCDDDDCCHI
.......BCDDDDCCCBHI
......BCDDDCCCCCCBHI
......BCDDCCCCCCCiHIG
......BCDCCCCCCCCBHIG
.....BCDCCCCCCCCCiHIG
.....BCDCCCCCCCCCBHIIG
.....BCDCCCCCCCCCiHIIG
.....BCDCCCCCCCCCBHIIG
.....BCDCCCCCCCCCiHIIG
.....BCCCCCCCCCCCBHIIG
.....BCCCCCCCCCCCiHIG
.....BCCCCCCCCCCBGHHG
.....BCCCCCCCCCBGGGG
....PQRRRRRRRRRRRRRRQP
....PQQQQQQQQQQQQQQQQP
.....KLMMMMMMMMMMMMLK
.....KLMMMMMMMMMMMMLK
.....KLMMMMMMMMMMMLK
""")


class Merchant(Npc):
    # the maps, as attributes so a revision (a subclass) can replace them
    HEAD_FRONT = HEAD_FRONT
    HEAD_BACK = HEAD_BACK
    BODY_FRONT = BODY_FRONT
    BODY_BACK = BODY_BACK
    ARM_DOWN = ARM_DOWN
    ARM_BOOK = ARM_BOOK
    PURSE = PURSE
    HEAD_SIDE = HEAD_SIDE
    BODY_SIDE = BODY_SIDE
    purse_front, purse_back = (2, 37), (25, 37)  # where the purse hangs (front / back view)
    id = "merchant"
    ramps = RAMPS
    walk_gait = dict(stride=3, lift=2, bob=1, arm=2)

    def legs_front(self, c, p, b, back):
        for (fwd, lift), x0 in ((p.near, 9), (p.far, 18)):
            down = 1 if fwd > 1 else 0
            y = min(55, 55 - lift + down)
            c.rect(x0, 42 + b, x0 + 4, y - 4, "trousers")
            c.rect(x0, y - 4, x0 + 4, y - 4, "trousers", 1)  # the hem's shadow
            c.rect(x0, y - 3, x0 + 4, y, "boot")
            c.rect(x0 - (1 if x0 < 16 else 0), y - 1, x0 + 4 + (0 if x0 < 16 else 1), y, "boot")
            c.line(x0 - (1 if x0 < 16 else 0), y, x0 + 4 + (0 if x0 < 16 else 1), y, "boot", 1)
            if not back:
                c.put(x0 + 1, y - 3, "boot", 3)
                c.put(x0 + 2, y - 3, "boot", 4)
            c.line(x0 + (3 if x0 < 16 else 1), 43 + b, x0 + (3 if x0 < 16 else 1), y - 5, "trousers", 1)  # crease

    # -------------------------------------------------------------- front / back
    def front(self, p, back=False):
        c = self.canvas()
        b = p.bob
        up = -p.breath
        self.legs_front(c, p, b, back)

        def shift(row, col, ch):
            y = BODY_TOP + row
            return 0, b + (up if y < 38 else 0)
        stamp(c, self.BODY_BACK if back else self.BODY_FRONT, 0, BODY_TOP, LEG, mirrored=True, shift=shift)
        top = 4 + b + up
        sh_r = (6, 25 + b + up) if not back else (25, 25 + b + up)
        sh_l = (25, 25 + b + up) if not back else (6, 25 + b + up)
        swing = max(0, p.arm_near if not back else p.arm_far)
        # the purse on his right hip
        px, py = self.purse_back if back else self.purse_front
        stamp(c, self.PURSE, px, py + b, LEG)
        c.put(px + (1, 2, 3)[p.glint], py + 2 + b, "gold", 4)  # the clasp catches the light
        # the right arm hangs (and swings), the left holds the book
        stamp_at(c, self.ARM_DOWN, "@", "*", (sh_r[0], sh_r[1] - swing), LEG, flip=back)
        if not back:
            stamp(c, BOOK_FRONT, 17, 28 + b + up, LEG)
            stamp_at(c, self.ARM_BOOK, "@", "*", sh_l, LEG)
        else:
            stamp_at(c, self.ARM_BOOK, "@", "*", sh_l, LEG, flip=True, darker=True)
        if not back:  # the pen: only its ends show past his head
            for x, y, ch in PEN_FRONT:
                c.put(x, y + top - 4, *LEG[ch][:2])
        stamp(c, self.HEAD_BACK if back else self.HEAD_FRONT, 0, top, LEG, mirrored=True)
        return c

    # -------------------------------------------------------------- side
    def side(self, p, swap=False):
        c = self.canvas()
        b = p.bob
        up = -p.breath
        hip = (15, 42 + b)
        sh = (14, 25 + b + up)

        def leg(fwd, lift, tone):
            ax, ay = hip[0] + fwd, 52 - lift
            kx, ky = hip[0] + fwd * 0.6 + (1.5 if lift else 0.5), (hip[1] + ay) / 2 - lift * 0.5
            capsule(c, hip[0], hip[1], kx, ky, 2.6, "trousers", tone)
            capsule(c, kx, ky, ax, ay - 1, 2.3, "trousers", tone)
            c.rect(int(ax) - 2, ay, int(ax) + 3, ay + 2, "boot", tone)
            c.put(int(ax) + 4, ay + 2 - (1 if lift > 1 else 0), "boot", tone)
            c.line(int(ax) - 2, ay + 3 - (1 if lift > 1 else 0), int(ax) + 4, ay + 3 - (1 if lift > 1 else 0), "boot", 0 if tone == 1 else 1)

        def arm_swing(swing, far):
            hx, hy = sh[0] + swing * 1.4, sh[1] + 13
            ex, ey = sh[0] + swing * 0.6, sh[1] + 6
            capsule(c, sh[0], sh[1] + 1, ex, ey, 2.0, "shirt", 1 if far else None)
            capsule(c, ex, ey, ex, ey + 0.5, 2.3, "shirt", 1 if far else 3)  # the rolled-up cuff
            capsule(c, ex, ey + 1.5, hx, hy, 1.4, "skin", 1 if far else None)
            c.rect(int(hx) - 1, int(hy), int(hx) + 1, int(hy) + 1, "skin", 1 if far else 2)

        def arm_book(far):
            # the elbow back at his side, the forearm forward under the book at the belly
            ex, ey = sh[0] - 1, sh[1] + 7
            capsule(c, sh[0], sh[1] + 1, ex, ey, 2.0, "shirt", 1 if far else None)
            capsule(c, ex, ey, ex + 0.5, ey + 0.5, 2.3, "shirt", 1 if far else 3)
            capsule(c, ex + 1, ey + 1, 23, ey + 2, 1.4, "skin", 1 if far else None)

        def book(far):
            stamp(c, BOOK_SIDE, 24, 28 + b + up, LEG) if not far else stamp(c, BOOK_SIDE, 24, 28 + b + up, LEG)

        def purse(far):
            stamp(c, self.PURSE, 9 if not far else 11, 37 + b, LEG)
            if not far:
                c.put(10 + (0, 1, 2)[p.glint], 39 + b, "gold", 4)

        # far side first
        leg(p.far[0], p.far[1], 1)
        if swap:
            purse(True)
            arm_swing(p.arm_far, True)
        else:
            book(True)
            arm_book(True)

        def shift(row, col, ch):
            y = BODY_TOP + row
            return 0, b + (up if y < 38 else 0)
        stamp(c, self.BODY_SIDE, 0, BODY_TOP, LEG, shift=shift)
        leg(p.near[0], p.near[1], None)
        top = 4 + b + up
        stamp(c, self.HEAD_SIDE, 0, top, LEG)
        c.put(19 + p.glint, top + 10, "skin", 2)  # light moving across the lens
        c.paint(19 + p.glint, top + 10, "#f4fbff")
        if swap:
            book(False)
            arm_book(False)
        else:
            purse(False)
            arm_swing(p.arm_near, False)
            for x, y, ch in ((13, 7, "X"), (14, 8, "W"), (14, 9, "W"), (15, 10, "V"), (15, 11, "0")):
                c.put(x, y + top - 4, *LEG[ch][:2])  # the pen behind his ear
        return c


NPC = Merchant()
