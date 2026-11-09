"""NPC 07 — the blacksmith (鍛冶職人). New: not placed in the village (no forge or dialogue yet).

Big and broad: the widest shoulders of the villagers, thick bare forearms; a square face with a
strong jaw, thick straight brows, narrow determined eyes, soot on the cheeks; red hair cropped short
under a twisted headband (white and indigo, tied at the back); a grey work shirt with the sleeves
rolled up, a heavy leather apron with straps and burn marks, dark trousers and boots; thick leather
gloves; a hammer hanging at his right hip.
Map characters (one per pixel; see npc_common):
  0-4 hair (red)   a-d skin 1-4   n brow  e lash  k eye  m mouth  # soot
  A-E shirt (grey) 0-4   F-J headband (white) 0-4   f-j headband (indigo) 0-4   K-O trousers 0-4
  P-T apron (heavy leather) 0-4   p q r t u gloves 0-4   U-Y wood 0-4   v-z iron 0-4
  @ shoulder anchor  * hand anchor (glove)
"""

from npc_common import capsule, half, legend, rows_of, stamp
from villager import Villager

RAMPS = {
    "hair": ["#3a0c06", "#7a2010", "#b03a1a", "#d85a2a", "#f28a52"],
    "skin": ["#5a3020", "#a86c4a", "#d49a72", "#eab48a", "#f8cca6"],
    "shirt": ["#1e2024", "#4a4e56", "#6c727c", "#8e949e", "#b4bac2"],
    "band": ["#4a4a4e", "#a8a8ac", "#e2e2e4", "#f4f4f6", "#ffffff"],
    "indigo": ["#0a0e24", "#1e2a5a", "#2e4084", "#4a60aa", "#7088cc"],
    "trousers": ["#0e0e12", "#1e1e24", "#2e2e36", "#40404a", "#565662"],
    "apron": ["#140a04", "#3a2210", "#583418", "#764a26", "#946438"],
    "glove": ["#2a1a0c", "#6a4626", "#8e6236", "#ae7e4a", "#cc9c64"],
    "iron": ["#14161c", "#40464f", "#6c7480", "#9aa2ae", "#d4dae2"],
}
LEG = legend(
    [("01234", "hair", 0), ("abcd", "skin", 1), ("ABCDE", "shirt", 0), ("FGHIJ", "band", 0), ("fghij", "indigo", 0),
     ("KLMNO", "trousers", 0), ("PQRST", "apron", 0), ("pqrtu", "glove", 0), ("UVWXY", "wood", 0), ("vwxyz", "iron", 0)],
    {"n": ("skin", 2, "#3a1408"), "e": ("skin", 2, "#24160e"), "k": ("skin", 2, "#3e2a1a"), "m": ("skin", 2, "#7a3a2c"),
     "#": ("skin", 2, "#6e6460"), "@": ("shirt", 2), "*": ("glove", 3)},
)

HEAD_FRONT = half("""
...........3..34
.........2334334
.......233443443
......2344344344
......2343343433
.....fFGfFGfFGfF
.....FGfFGfFGfFG
.....23bccccdddd
.....2bnnnnccccc
....abccceeecccc
....abccckcccccd
....abccc#ccccbd
....abcc#cccccbb
.....bccccccccmm
.....bcccccccccc
.....abccccccccc
.....abccccccccc
......abbbbbbbbb
""")

HEAD_BACK = half("""
...........3..34
.........2334334
.......233443443
......2344344344
......2343343433
.....fFGfFGfFGfF
.....FGfFGfFGFGH
.....2343343FGHI
.....2343343fgGH
....a23433432FgH
....a234334332Gg
.....23343343323
.....22332332332
......bbbbbbbbbb
......bbbbbbbbbb
.......bbbbbbbbb
""")

HEAD_SIDE = rows_of("""
...........3..343
..........23343343
........2334434433
.......234434434433
.......2343343343343
......FGfFGfFGfFGfFGf
.....FGHGfFGfFGfFGfFG
.....GHI23433bccccdddd
.....fG2343bcccnnnnccc
......Gg234abccceeeccd
.......g23aabacckcccdd
........2abacc#c#cccbb
........2abccc#ccccbc
.........abccccccccmm
.........abcccccccccc
.........abcccccccccc
..........abbbbbbbbbb
""")

BODY_FRONT = half("""
..........bcccdd
......BCDDQbccdd
...BCDDDDDQRbccc
..BCDDDDCCQRSbcc
..BCDDDCCCQRSSSS
..BCDDCCCCQRSTSS
..BCDCCCCCQRSSSS
..BCDCCCCCQRSSSS
..BCDCCCCCQRSSRS
..BCDCCCCCQRSSSS
..BCCCCCCCQRSSSS
...BCCCCCCQRSSSS
...BCCCCCQRSSSSS
...BCCCCQRSSSSSS
...PQQQRSSSSSSSS
...LMMMRSSSSSSSS
...LMMMRSSSSSTSS
...LMMMRSSSSSSSS
....LMMRSSSSSSSS
....LMMRSSSSSSSS
....LMMRSSSSSRSS
....LMRSSSSSSSSS
....LMRSSSSSSSSS
....LMRSSSSSSSSS
......RSSSSSSSSS
......QRRRRRRRRR
""")

BODY_BACK = half("""
..........bcccdd
......BCDDDDDDDD
...BCDDDDDDDDCCC
..BCDDDDQCCCCCCC
..BCDDDCQCCCCCCC
..BCDDCCCQCCCCCC
..BCDCCCCQCCCCCC
..BCDCCCCCQCCCCC
..BCDCCCCCCQCCCC
..BCDCCCCCCCQCCC
..BCCCCCCCCCCQCC
...BCCCCCCCCCCQQ
...BCCCCCCCCCCCC
...BCCCCCCCCCCCC
...PQQQQQQQQQQQQ
...LMMMMMMMMMPQR
...LMMMMMMMMMMPQ
...LMMMMMMMMMMMP
....LMMMMMMMMMMM
....LMMMMMMMMMMM
....LMMMMMMMMMMM
....LMMMMMMMMMLM
....LMMMMMMMMMLM
....LMMMMMMMMMLM
""")

BODY_SIDE = rows_of("""
..........bccdd
........BCDDQccd
......BCDDDDQRbc
.....BCDDDDDCQRb
.....BCDDDDCCCQRSS
.....BCDDDCCCCCQRSS
.....BCDDCCCCCCQRSS
.....BCDCCCCCCCQRSS
.....BCDCCCCCCCQRSS
.....BCDCCCCCCCQRSS
.....BCDCCCCCCCQRSS
.....BCCCCCCCCQRSSS
.....BCCCCCCCQRSSSS
.....BCCCCCCQRSSSSS
.....PQQQQQQRSSSSSS
.....LMMMMMQRSSSSSS
.....LMMMMMQRSSSSSS
.....LMMMMMQRSSSTSS
.....LMMMMQRSSSSSSS
......LMMMQRSSSSSSS
......LMMMQRSSSSSSS
......LMMMQRSSSSSSS
......LMMMQRSSSSSS
......LMMMQRSSSSSS
........QRSSSSSSS
........QRRRRRRRR
""")

ARM = rows_of("""
.@CD..
BCDDC.
BCDEC.
BCDDC.
CDEED.
.bccb.
bcddcb
bccdcb
bcdccb
bccdcb
bcccb.
.prtq.
.p*tq.
.pqqp.
..pp..
""", 6)

HAMMER = rows_of("""
vwxyzyw
vwxyyxw
..vWV..
...W...
...V...
...W...
...V...
...U...
""", 7)


class Smith(Villager):
    id = "smith"
    ramps = RAMPS
    LEG = LEG
    HEAD_FRONT, HEAD_BACK, HEAD_SIDE = HEAD_FRONT, HEAD_BACK, HEAD_SIDE
    BODY_FRONT, BODY_BACK, BODY_SIDE = BODY_FRONT, BODY_BACK, BODY_SIDE
    ARM_R = ARM_L = ARM
    head_top = 2
    body_top = 20
    hip = 43
    breath_below = 34
    legs = dict(xs=(9, 18), w=5, mat="trousers", shoe="boot", r=2.6)
    shoulders = (4, 27)
    shoulder_y = 23
    side_shoulder = (13, 23)
    sleeve = "shirt"
    forearm = "skin"
    near_leg_over_body = False
    walk_gait = dict(stride=3, lift=2, bob=1, arm=2)

    def blink_front(self, c, top):
        for x in (9, 10, 11, 20, 21, 22):
            c.put(x, top + 9, "skin", 3)
        c.put(9, top + 10, "skin", 3)
        c.put(22, top + 10, "skin", 3)

    def blink_side(self, c, top):
        c.put(21, top + 10, "skin", 3)

    def over_front(self, c, p, b, up, back):
        hx = 6 if not back else 20
        stamp(c, HAMMER, hx, 34 + b, LEG)
        c.put(hx + 2 + p.glint, 34 + b, "iron", 4)

    def arm_side(self, c, p, sh, swing, far, left):
        hx, hy = sh[0] + swing * 1.4, sh[1] + 15
        ex, ey = sh[0] + swing * 0.6, sh[1] + 6
        tone = 1 if far else None
        capsule(c, sh[0], sh[1] + 1, ex, ey, 2.6, "shirt", tone)
        capsule(c, ex, ey, ex, ey + 0.5, 2.8, "shirt", 1 if far else 3)  # the rolled sleeve
        capsule(c, ex, ey + 2, hx, hy - 2, 2.1, "skin", tone)
        capsule(c, hx, hy - 1, hx + 0.5, hy + 1, 2.0, "glove", tone)

    def over_side(self, c, p, b, up, swap):
        top = self.head_top + b + up
        c.put(5 - p.glint, top + 9, "indigo", 2)  # the headband's tails sway
        c.put(5 - p.glint, top + 10, "band", 3)
        if not swap:  # the hammer at the near (right) hip
            stamp(c, HAMMER, 13, 34 + b, LEG)
            c.put(15 + p.glint, 34 + b, "iron", 4)


NPC = Smith()
