"""NPC 05 — the inn's cook (宿の料理人).

Middle-aged and sturdy: broad shoulders, a belly under the apron; a round ruddy face, thick brows,
small cheerful eyes, a wide smile; light-brown short hair under a white triangular headscarf tied at
the back; a rust shirt with the sleeves rolled to the elbow (strong bare forearms), a long white
apron with a neck strap and a waist tie, brown trousers; a ladle tucked in the apron string at his
right hip, a striped hand towel over his left shoulder.
Map characters (one per pixel; see npc_common):
  0-4 hair (light brown)   a-d skin 1-4   n brow  e lash  k eye  m mouth  r cheeks
  A-E shirt (rust) 0-4     F-J cloth (white: headscarf, apron) 0-4   K-O trousers (brown) 0-4
  P-T leather 0-4          U-Y wood (the ladle's handle) 0-4         v-z steel (the ladle) 0-4
  p q s t u towel 0-4      @ shoulder anchor  * hand anchor (skin)
"""

from npc_common import half, legend, rows_of, stamp
from villager import Villager

RAMPS = {
    "hair": ["#2e1a0c", "#6a4424", "#946436", "#b8844c", "#d8a86a"],
    "skin": ["#6a3626", "#c07a5c", "#eaa684", "#f8c4a0", "#ffdcc0"],
    "shirt": ["#2a0e08", "#6a2a18", "#984228", "#be6040", "#dc8a64"],
    "cloth": ["#4e4c4a", "#aaa8a2", "#e2e0da", "#f4f2ee", "#ffffff"],
    "trousers": ["#1e140c", "#46301e", "#62442c", "#80603e", "#a07c54"],
    "towel": ["#2c3446", "#6a7c9c", "#a8bcd8", "#d4e0f0", "#f4f8ff"],
}
LEG = legend(
    [("01234", "hair", 0), ("abcd", "skin", 1), ("ABCDE", "shirt", 0), ("FGHIJ", "cloth", 0), ("KLMNO", "trousers", 0),
     ("PQRST", "leather", 0), ("UVWXY", "wood", 0), ("vwxyz", "steel", 0), ("pqstu", "towel", 0)],
    {"n": ("skin", 2, "#3e2414"), "e": ("skin", 2, "#2a1a14"), "k": ("skin", 2, "#3a2418"), "m": ("skin", 2, "#8a3a34"),
     "r": ("skin", 2, "#e8806a"), "@": ("shirt", 2), "*": ("skin", 3)},
)

HEAD_FRONT = half("""
..........GHIIII
........GHIJJJII
.......GHIJJIIII
......GHIJIIIIII
.....GHIJIIIIIII
.....GHIIIIIIIII
.....FGHHHHHHHHH
.....23FGGGGGGGG
.....234bcccdddd
.....234bnnnnccc
....ab23cccccccc
....abccceeecccc
....abcccckccccd
....abcrrrcccccd
.....bcrrccccbbb
.....bccccmccccc
.....abcccmmmmmm
......abccccrrrr
.......abccccccc
........aabbbbbb
""")

HEAD_BACK = half("""
..........GHIIII
........GHIJJJII
.......GHIJJIIII
......GHIJIIIIII
.....GHIJIIIIIII
.....GHIIIIIIIII
.....GHIIIIIIHHH
.....FGHHHHHHGIJ
.....2343343GHIJ
....a2343343FGHI
....a23433432GHG
....a234334332GH
.....223323322GG
.....bb222222222
......bbbbbbbbbb
.......bbbbbbbbb
""")

HEAD_SIDE = rows_of("""
............GHIIIH
..........GHIJJJIIH
.........GHIJJIIIIIH
........GHIJIIIIIIIIH
.......GHIJIIIIIIIIIIH
.......GHIIIIIIIIIIIIIH
......GHHIIIIIIIIIIIIIIH
.....GHIJHHHHHHHHHHHHHHH
.....FGHI23bccccccdddccc
.....FGH234bcccccnnnnccc
......GG2334abccccccccccd
......FG2343abacccceeccdd
.......F234aabcccccckccddc
........234abcccrrrcccbbb
........23abccccrrcccccb
.........2abcccccccmccccc
..........abcccccccmmmrc
...........abcccccccc
............abbbbbbb
""")

BODY_FRONT = half("""
.......BCDDDDHCC
.....BCDDDDDHCCC
....BCDDDDDHCCCC
...BCDDDDCHIJJJJ
...BCDDCCCHIJIII
...BCDCCCCHIIIII
...BCDCCCCHIIIII
...BCDCCCCHIIIHI
...BCDCCCCHIIIHI
...BCDCCCCHIIIII
..BCDCCCCCHIIIII
..BCDCCCHHHHHHHH
..BCDCCCGIIIIIII
..BCCCCHIIIIIIII
..BCCCCHIJIIIIII
..BCCCCHIJIIIIII
...BCCGHIJIIIIII
...BCCGHIIIIIHII
....LMGHIIIIIHII
....LMGHIIIIIHII
....LMGHIIIIIHII
......GHIIIIIHII
......GHIIIIIHII
......GHIIIIIHII
......FGGGGGGGGG
""")

BODY_BACK = half("""
.......BCDDDDDDD
.....BCDDDDDDDCC
....BCDDDDDCCCCC
...BCDDDDCCCCCCC
...BCDDCCCCCCCCB
...BCDCCCCCCCCCB
...BCDCCCCCCCCCB
...BCDCCCCCCCCCB
...BCDCCCCCCCCCB
...BCDCCCCCCCCCB
..BCDCCCCCCCCCCB
..BCDCCHHHHHHHHH
..BCDCCCCCCCCGHI
..BCCCCCCCCCCCGH
..BCCCCCCCCCCCGH
..BCCCCCCCCCCCCB
...BCCCCCCCCCCCB
...BCCCCCCCCCCCB
....LMMMMMMMMMMM
....LMMMMMMMMMMM
....LMMMMMMMMMLM
""")

BODY_SIDE = rows_of("""
..........BCDDDC
........BCDDDDCCHI
.......BCDDDDCCCHIJ
......BCDDDCCCCCHIJJ
......BCDDCCCCCCHIJIJ
......BCDCCCCCCCHIIIIJ
.....BCDCCCCCCCCHIIIIIJ
.....BCDCCCCCCCCHIIIIIJ
.....BCDCCCCCCCCHIIIIIIJ
.....BCDCCCCCCCCHIIIIIIJ
.....BCDCCCCCCCCHIIIIIIJ
.....BCCCCHHHHHHHHHHHHHH
.....BCCCCCCCCCGIIIIIIIJ
.....BCCCCCCCCGHIIIIIIIJ
.....BCCCCCCCCGHIIIIIIJ
......BCCCCCCGHIIIIIIJ
......BCCCCCCGHIIIIIIJ
......LMMMMMGHIIIIIIIJ
......LMMMMMGHIIIIIIJ
......LMMMMMGHIIIIIIJ
.......LMMMMGHIIIIIIJ
.......LMMMMGHIIIIIJ
.......LMMMMGHIIIIIJ
.......LMMMMGHIIIIIJ
........LMMMFGGGGGGG
""")

ARM = rows_of("""
.@DD.
BCDDC
BCDDC
BCDDC
DEEED
.bccb
.bccb
.bccb
.bcdb
.b*cb
..bb.
""", 5)

# the ladle, tucked in the apron string: the handle up, the bowl down
LADLE = rows_of("""
.X.
.W.
.W.
.V.
.V.
.x.
.w.
wyzx
wxyw
.ww.
""", 4)

# the towel over his left shoulder, seen from the front (it hangs down his chest) and from behind
TOWEL_FRONT = rows_of("""
sttts
stuts
sqqqs
stsss
stsss
sqqqs
stsss
sssss
.sss.
""", 5)
TOWEL_BACK = rows_of("""
stttss
sttsss
sqqqss
stsss.
stsss.
sqqqs.
stsss.
stsss.
sssss.
sqqqs.
.sss..
""", 6)


class Cook(Villager):
    id = "cook"
    ramps = RAMPS
    LEG = LEG
    HEAD_FRONT, HEAD_BACK, HEAD_SIDE = HEAD_FRONT, HEAD_BACK, HEAD_SIDE
    BODY_FRONT, BODY_BACK, BODY_SIDE = BODY_FRONT, BODY_BACK, BODY_SIDE
    ARM_R = ARM_L = ARM
    head_top = 3
    body_top = 22
    hip = 42
    breath_below = 34
    legs = dict(xs=(10, 18), w=4, mat="trousers", shoe="boot", r=2.4)
    shoulders = (5, 26)
    shoulder_y = 26
    side_shoulder = (14, 26)
    sleeve = "shirt"
    forearm = "skin"
    near_leg_over_body = False
    walk_gait = dict(stride=3, lift=2, bob=1, arm=2)

    def blink_front(self, c, top):
        for x in (9, 10, 11, 20, 21, 22):
            c.put(x, top + 12, "skin", 3)

    def blink_side(self, c, top):
        c.put(20, top + 12, "skin", 3)

    def over_front(self, c, p, b, up, back):
        if back:
            stamp(c, TOWEL_BACK, 6, 23 + b + up, LEG)  # down his back, from the left shoulder
            c.put(14 + p.glint, self.head_top + 7 + b + up, "cloth", 4)  # light on the scarf's knot
            return
        stamp(c, LADLE, 7, 30 + b, LEG)  # his right hip (image left)
        c.put(8 + (p.glint % 2), 37 + b, "steel", 4)
        stamp(c, TOWEL_FRONT, 21, 23 + b + up, LEG)  # his left shoulder (image right)

    def behind_side(self, c, p, b, up, swap):
        if not swap:  # the towel on the far shoulder: its end hangs down his back
            stamp(c, TOWEL_BACK, 5, 25 + b + up, LEG)

    def over_side(self, c, p, b, up, swap):
        if not swap:  # facing right: the ladle at the near hip
            stamp(c, LADLE, 16, 30 + b, LEG)
            c.put(17 + (p.glint % 2), 37 + b, "steel", 4)
        else:  # facing left: the towel over the near shoulder, front and back
            stamp(c, TOWEL_FRONT, 16, 24 + b + up, LEG)
            c.put(17 + p.glint, 26 + b + up, "towel", 4)
            for x in range(11, 18):
                c.put(x, 23 + b + up, "towel", 3 if x < 14 else 2)


NPC = Cook()
