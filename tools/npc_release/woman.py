"""NPC 04 — a village woman (村の女性). New: not placed in the village (no dialogue yet).

Young, an ordinary build; bright amber eyes, freckles, a small smile; auburn hair under a red
headscarf tied at the nape, one braid over her right shoulder with a red tie; a cream blouse with
elbow-length puffed sleeves, a plum skirt to the ankles, an ochre apron, a dark waistband; little
brown shoes; a wicker basket of herbs on her left forearm.
Map characters (one per pixel; see npc_common):
  0-4 hair (auburn)   a-d skin 1-4   e lash  i I iris  w shine  m mouth  r cheeks  q freckle
  A-E blouse (cream) 0-4   F-J apron (ochre) 0-4   K-O skirt (plum) 0-4   P-T leather 0-4
  U-Y wicker 0-4   f-j scarf (red) 0-4   v-z herbs (green) 0-4   @ shoulder anchor  * hand anchor (skin)
"""

from npc_common import half, legend, rows_of, stamp
from villager import Villager

RAMPS = {
    "hair": ["#3a120a", "#7a2c16", "#a8441e", "#cc6a34", "#ec9a5e"],
    "skin": ["#6e3e2c", "#c8906a", "#f2c49b", "#ffdcbc", "#fff0e0"],
    "blouse": ["#4e4636", "#b4a888", "#e8dec2", "#f6efdc", "#fffaf0"],
    "apron": ["#3a2a08", "#8a6a20", "#b8902e", "#d8b04a", "#f0d27a"],
    "skirt": ["#1c1028", "#4a2c5c", "#6a447e", "#8a649c", "#ac8cbc"],
    "wicker": ["#3a2410", "#7a5428", "#a8783c", "#c89a58", "#e4be80"],
    "scarf": ["#3a0808", "#8a1c1c", "#c0302a", "#e05a46", "#f8907a"],
    "herb": ["#0e2a10", "#2e6a28", "#4a9a3a", "#74c058", "#a8e08a"],
}
LEG = legend(
    [("01234", "hair", 0), ("abcd", "skin", 1), ("ABCDE", "blouse", 0), ("FGHIJ", "apron", 0), ("KLMNO", "skirt", 0),
     ("PQRST", "leather", 0), ("UVWXY", "wicker", 0), ("fghij", "scarf", 0), ("vwxyz", "herb", 0)],
    {"e": ("skin", 2, "#2a1a18"), "i": ("skin", 2, "#c07a2a"), "I": ("skin", 2, "#6a3a10"), "w": ("skin", 2, "#fff8ec"),
     "m": ("skin", 2, "#b04a46"), "r": ("skin", 2, "#f4a08e"), "q": ("skin", 2, "#c47a52"), "@": ("blouse", 2), "*": ("skin", 3)},
)

HEAD_FRONT = half("""
..........fghhhh
........fghiiihh
.......fghiihhhh
......fghihhhhhh
.....fghihhhhhhh
.....fghhhhhhhhh
.....fgggggggggg
.....23443234cdd
....a2342bc23ccd
....a234bccccccc
....a23bceeeeccc
....a2bcIiiwcccc
....a2bcIiiicccc
....a2bcbIIccccd
.....2bcqcqrrccb
.....2abcccmcccc
.....2abccccmmmm
......2abccccccc
.......2abcccccc
........2aabbbbb
""")

HEAD_BACK = half("""
..........fghhhh
........fghiiihh
.......fghiihhhh
......fghihhhhhh
.....fghihhhhhhh
.....fghhhhhhhhh
.....fgggggghhij
.....2344334fghi
....a2343433fghi
....a234343323gh
....a2343433423g
.....23434334433
.....23343343343
.....22343343343
......2233233232
.......bbbbbbbbb
........bbbbbbbb
""")

HEAD_SIDE = rows_of("""
............fghhhg
..........fghiiihhg
.........fghiihhhhhg
........fghihhhhhhhhg
.......fghihhhhhhhhhhg
......fghhhhhhhhhhhhhhg
.....fghiggggggggggggggg
.....fgh2344323443ddcccc
......gh23443234bccccccc
.......g2344323abccccccccc
.......2344323abacceeeec
.......234432abacccIiwcd
.......23443aabcccIiicdd
........2332bccqcqrccbb
........222bccccccccmcc
.........2bbcccccccmmc
..........2abcccccccc
...........2abccccccb
............2aabbbbb
""")

BODY_FRONT = half("""
..........BCDDDD
........BCDDDCbc
.......BCDDCCCCb
.......BCDCCCCCC
.......BCDCCCCCC
.......BCDCCCCCC
.......BCDCCCCCC
.......BCCCCCCCC
.......BCCCCCCCC
.......KLLLLLLLL
......KLMFGIIIII
......KLMFGHHHHH
......KLMFGHHHHH
.....KLMMFGHHHHH
.....KLMMFGHHHHH
.....KLMMFGGGGGH
.....KLMMFGIHHGH
....KLMMMFGIHHGH
....KLMMLFGGGGGH
....KLMMLFGHHHHH
....KLMLMFGHHGHH
....KLMLMFGHHGHH
...KLMMLMFGHHGHH
...KLMMLMFGHHGHH
...KLMLMMFGHHGHH
...KLMLMMFGHHGHH
...KLMLMMFFFFFFF
...KLMLMMMMMMMMM
...LLLLLLLLLLLLL
""")

BODY_BACK = half("""
..........BCDDDD
........BCDDDDCC
.......BCDDDCCCC
.......BCDDCCCCC
.......BCDCCCCCC
.......BCDCCCCCC
.......BCDCCCCCC
.......BCCCCCCCC
.......BCCCCCCCC
.......KLLLLLGHI
......KLMMMMMFGH
......KLMMMMMMFG
......KLMMMMMMMF
.....KLMMMMMMMMM
.....KLMMMMLMMMM
.....KLMMMMLMMMM
.....KLMMMMLMMMM
....KLMMMMMLMMMM
....KLMMLMMLMMMM
....KLMMLMMLMMMM
....KLMLMMMLMMMM
....KLMLMMMLMMMM
...KLMMLMMMLMMMM
...KLMMLMMMLMMMM
...KLMLMMMMLMMMM
...KLMLMMMMLMMMM
...KLMLMMMMLMMMM
...KLMLMMMMMMMMM
...LLLLLLLLLLLLL
""")

BODY_SIDE = rows_of("""
...........BCDDC
.........BCDDDCCb
........BCDDDCCCCb
........BCDDCCCCCB
........BCDCCCCCCB
........BCDCCCCCCB
........BCDCCCCCCB
........BCCCCCCCCB
.........BCCCCCCB
.........KLLLLLLLK
........KLMMMMMMFGH
........KLMMMMMMFGHI
........KLMMMMMMFGHI
........KLMMLMMMFGHI
.......KLMMMLMMMFGHI
.......KLMMMLMMMFGHI
.......KLMMMLMMMFGHI
.......KLMMLMMMMFGHI
.......KLMMLMMMMFGHI
.......KLMMLMMMMFGHI
.......KLMMLMMMMFGHI
......KLMMMLMMMMFGHI
......KLMMMLMMMMFGHI
......KLMMLMMMMMFGHI
......KLMMLMMMMMFGHI
......KLMLMMMMMMFGHI
......KLMLMMMMMMFFFF
......KLMLMMMMMMMMMMK
......LLLLLLLLLLLLLLL
""")

ARM_R = rows_of("""
.@DD.
BCDDC
BCDEC
BCDDB
.BCB.
.bcb.
.bcb.
.bcb.
.bcd.
.*cb.
..b..
""", 5)
# her left arm bent at the elbow: the forearm forward, the basket hanging from it
ARM_L = rows_of("""
.@DD...
BCDDC..
BCDEC..
BCDDB..
.BCBbc.
..bcccb
.....*.
""", 7)

BASKET = rows_of("""
..YXXY..
.X....X.
vxwyxzwv
WXWXWXWX
VWVWVWVW
WVWVWVWV
.VVVVVV.
""", 8)


class Woman(Villager):
    id = "woman"
    ramps = RAMPS
    LEG = LEG
    HEAD_FRONT, HEAD_BACK, HEAD_SIDE = HEAD_FRONT, HEAD_BACK, HEAD_SIDE
    BODY_FRONT, BODY_BACK, BODY_SIDE = BODY_FRONT, BODY_BACK, BODY_SIDE
    ARM_R, ARM_L = ARM_R, ARM_L
    head_top = 5
    body_top = 24
    hip = 46
    breath_below = 33
    legs = dict(xs=(11, 17), w=3, mat="skirt", shoe="leather", skirt=True)
    shoulders = (7, 24)
    shoulder_y = 26
    side_shoulder = (14, 26)
    sleeve = "blouse"
    forearm = "skin"
    near_leg_over_body = False
    swing_l = 0  # the basket arm does not swing
    walk_gait = dict(stride=2, lift=2, bob=1, arm=2)

    def foot_front(self, c, x0, y, back):
        c.rect(x0, y - 1, x0 + 3, y, "leather")
        c.line(x0, y, x0 + 3, y, "leather", 1)
        if not back:
            c.put(x0 + 1, y - 1, "leather", 4)

    def body_shift(self, p, b, up, back):
        def shift(row, col, ch):
            y = self.body_top + row
            dx = round(p.sway * (y - 42) / 8) if y > 42 and ch in "KLMNO" and (col < 8 or col > 23) else 0
            return dx, b + (up if y < self.breath_below else 0)
        return shift

    def braid(self, c, pts, tie_at):
        for k, (x, y) in enumerate(pts):
            c.put(x, y, "hair", 3 if k % 2 == 0 else 2)
            c.put(x + 1, y, "hair", 2 if k % 2 == 0 else 1)
        c.put(tie_at[0], tie_at[1], "scarf", 3)
        c.put(tie_at[0] + 1, tie_at[1], "scarf", 2)
        c.put(tie_at[0], tie_at[1] + 1, "hair", 2)

    def blink_front(self, c, top):
        for x in (8, 9, 10, 11, 20, 21, 22, 23):
            c.put(x, top + 11, "skin", 2)
            c.paint(x, top + 11, "#2a1a18")
            c.put(x, top + 12, "skin", 3)
            c.put(x, top + 13, "skin", 3)

    def blink_side(self, c, top):
        for x in (19, 20, 21):
            c.put(x, top + 11, "skin", 2)
            c.paint(x, top + 11, "#2a1a18")
            c.put(x, top + 12, "skin", 3)

    def over_front(self, c, p, b, up, back):
        t = b + up
        if not back:
            self.braid(c, [(8, 23 + t + k) for k in range(10)], (8, 33 + t))
            hx, hy = self.hand_l
            stamp(c, BASKET, hx - 4, hy - 1, LEG)
            c.put(hx - 3 + p.glint * 2, hy + 1, "herb", 4)  # the herbs stir
            c.put(hx, hy - 1, "skin", 3)  # her fingers round the handle
        else:
            self.braid(c, [(16 + k // 2, 22 + t + k) for k in range(6)], (19, 28 + t))
            hx, hy = self.hand_l
            stamp(c, BASKET, hx - 3, hy - 1, LEG)
            c.put(hx - 2 + p.glint * 2, hy + 1, "herb", 3)

    def arm_side(self, c, p, sh, swing, far, left):
        if left:  # the basket arm: the elbow at her side, the forearm forward, the basket below it
            ex, ey = sh[0], sh[1] + 6
            from npc_common import capsule
            capsule(c, sh[0], sh[1] + 1, ex, ey - 1, 2.0, "blouse", 1 if far else None)
            capsule(c, ex, ey, 21, ey + 1, 1.3, "skin", 1 if far else None)
            stamp(c, BASKET, 18, ey + 1 + (1 if p.prop > 0 else 0), LEG)
            c.put(19 + p.glint * 2, ey + 3 + (1 if p.prop > 0 else 0), "herb", 4)
            if far:
                for yy in range(ey, ey + 9):
                    for xx in range(17, 27):
                        t = c.tone[yy][xx]
                        if c.mat[yy][xx] in ("wicker", "herb") and t is not None and t > 1:
                            c.tone[yy][xx] = t - 1
            c.rect(21, ey, 22, ey + 1, "skin", 1 if far else 3)
            return
        super().arm_side(c, p, sh, swing, far, left)

    def over_side(self, c, p, b, up, swap):
        t = b + up
        if not swap:  # her braid in front of the near (right) shoulder
            self.braid(c, [(17 + (k > 5), 23 + t + k) for k in range(10)], (18, 33 + t))


NPC = Woman()
