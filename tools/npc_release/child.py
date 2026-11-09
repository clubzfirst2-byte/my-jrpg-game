"""NPC 06 — the village child (村の子).

Small (about two thirds of the frame), a big round head: curly blond hair with a cowlick, big
bright eyes (like the hero's: a lash line, a two-tone iris and a shine), round pink cheeks; a sky-blue
short-sleeved shirt, brown shorts, white socks, little brown shoes; a leather shoulder bag (the strap
over the right shoulder, the bag on the left hip) and a red pinwheel (the village is 風見, "wind
watch") held out in the right hand, its vanes turning.
Map characters (one per pixel; see npc_common):
  0-4 hair (blond)   a-d skin 1-4   e lash  i I iris  w shine  m mouth  r cheeks
  A-E shirt (sky blue) 0-4   F-J socks (white) 0-4   K-O shorts (brown) 0-4   P-T leather 0-4
  f-j vane (red) 0-4   U-Y wood (the stick) 0-4   @ shoulder anchor  * hand anchor (skin)
"""

from npc_common import capsule, half, legend, rows_of, stamp
from villager import Villager

RAMPS = {
    "hair": ["#5a3a10", "#a87a2a", "#d8aa40", "#f0cc68", "#fff0a8"],
    "skin": ["#6e3e2c", "#cc8e6a", "#f4c49e", "#ffdcbc", "#fff0e2"],
    "shirt": ["#0e2a44", "#3a78a8", "#5aa2d0", "#86c4ea", "#c4e8ff"],
    "cloth": ["#4a4846", "#a8a6a0", "#e4e2dc", "#f6f4f0", "#ffffff"],
    "trousers": ["#24160c", "#55361e", "#7a5230", "#9a6e44", "#ba8e5e"],
    "vane": ["#3a0a0a", "#8e1e1e", "#c8302a", "#ec5a48", "#ff9a86"],
}
LEG = legend(
    [("01234", "hair", 0), ("abcd", "skin", 1), ("ABCDE", "shirt", 0), ("FGHIJ", "cloth", 0), ("KLMNO", "trousers", 0),
     ("PQRST", "leather", 0), ("fghij", "vane", 0), ("UVWXY", "wood", 0)],
    {"e": ("skin", 2, "#2a2030"), "i": ("skin", 2, "#3e9a5a"), "I": ("skin", 2, "#1e5a32"), "w": ("skin", 2, "#f4fff8"),
     "m": ("skin", 2, "#b0504a"), "r": ("skin", 2, "#f6a090"), "@": ("shirt", 2), "*": ("skin", 3)},
)

HEAD_FRONT = half("""
............2333
.........2334443
........23443344
.......234432343
......2344343443
.....23433443334
.....23343344343
....234332434433
....2342dc343cd3
....234bcdccdccc
....23bccccccccc
....2abceeeeeccc
....2abcIiiwcccc
....2abcIiiicccc
....2abcbIIccccd
.....abrrccccmcc
.....abrrcccccmm
......abcccccccr
.......abccccccc
........aabbbbbb
""")

HEAD_BACK = half("""
............2333
.........2334443
........23443344
.......234432343
......2344343443
.....23433443334
.....23343344343
....234332434433
....234343343343
....234334343343
...a234343343334
...a234334343343
....234343343343
.....23433433433
.....22332332332
......2bb2bbb2bb
.......bbbbbbbbb
........bbbbbbbb
""")

HEAD_SIDE = rows_of("""
............23332
..........2334443332
.........234433444332
........23443234434432
.......2344334433443332
.......23433443343443dc
......234334433433cdddc
......23433443343cddddcc
......2343344334bcdcccccb
......234334432bccccccccc
.......2343343abcccceeeec
.......234334abaccccIiwcd
.......23433abbcccccIiicc
........2332bbcccccrrcccd
........222bccccccccccmc
.........bbccccccccccmm
..........abccccccccc
...........abcccccccb
............aabbbbbb
""")

BODY_FRONT = half("""
..........BCDDDD
........BCDDDCCC
.......BCDDCCCCC
.......BCDCCCCCC
.......BCDCCCCCC
.......BCDCCCCCC
.......BCCCCCCCC
.......BCCCCCCCC
.......KLMMMMMMM
.......KLMMMMMMM
.......KLMMMMMMM
.......KLMMMMLMM
.......KLMMMML..
""")

BODY_BACK = half("""
..........BCDDDD
........BCDDDDCC
.......BCDDDCCCC
.......BCDDCCCCC
.......BCDCCCCCC
.......BCDCCCCCC
.......BCCCCCCCC
.......BCCCCCCCC
.......KLMMMMMMM
.......KLMMMMMMM
.......KLMMMMMMM
.......KLMMMMLMM
.......KLMMMML..
""")

BODY_SIDE = rows_of("""
...........BCDDC
.........BCDDDDCC
........BCDDDCCCCB
........BCDDCCCCCB
........BCDCCCCCCB
........BCDCCCCCCB
........BCCCCCCCCB
........BCCCCCCCCB
........KLMMMMMMMMK
........KLMMMMMMMMK
........KLMMMMMMMMK
........KLMMMMMMMK
.........KLMMMMMK
""")

ARM = rows_of("""
.@D.
BCDC
BCDC
BDEB
.bc.
.bc.
.bc.
.bd.
.*c.
.bb.
""", 4)

# the pinwheel's head, two phases of its turn (+ and x), and the bag
VANES = [rows_of("""
...h...
..ghi..
.gfhi..
hhiYjhh
..ihfg.
..ihg..
...h...
""", 7), rows_of("""
h.....h
.hi..g.
..hig..
...Y...
..ghi..
.g..ih.
h.....h
""", 7)]
BAG = rows_of("""
QRRRQ
QRSTR
RSiSR
RSSSR
QRRRQ
""", 5)


class Child(Villager):
    id = "child"
    ramps = RAMPS
    LEG = LEG
    HEAD_FRONT, HEAD_BACK, HEAD_SIDE = HEAD_FRONT, HEAD_BACK, HEAD_SIDE
    BODY_FRONT, BODY_BACK, BODY_SIDE = BODY_FRONT, BODY_BACK, BODY_SIDE
    ARM_R = ARM_L = ARM
    head_top = 17
    body_top = 35
    hip = 47
    breath_below = 43
    legs = dict(xs=(10, 18), w=3, mat="skin", shoe="leather", r=1.6)
    shoulders = (8, 23)
    shoulder_y = 37
    side_shoulder = (15, 37)
    side_hip_x = 16
    sleeve = "shirt"
    forearm = "skin"
    walk_gait = dict(stride=3, lift=2, bob=1, arm=2)

    def legs_front(self, c, p, b, back):
        for (fwd, lift), x0 in ((p.near, 10), (p.far, 18)):
            y = min(55, 55 - lift + (1 if fwd > 1 else 0))
            c.rect(x0, self.hip + b, x0 + 3, y - 4, "skin")
            c.rect(x0, y - 5, x0 + 3, y - 3, "cloth")  # socks
            c.rect(x0 - (1 if x0 < 16 else 0), y - 2, x0 + 3 + (0 if x0 < 16 else 1), y, "leather")
            c.line(x0 - (1 if x0 < 16 else 0), y, x0 + 3 + (0 if x0 < 16 else 1), y, "leather", 1)
            if not back:
                c.put(x0 + 1, y - 2, "leather", 4)

    def leg_side(self, c, p, fwd, lift, tone):
        hip = (self.side_hip_x, self.hip + p.bob)
        ax, ay = hip[0] + fwd, 53 - lift
        capsule(c, hip[0], hip[1], ax, ay - 3, 1.6, "skin", tone)
        c.rect(int(ax) - 1, ay - 3, int(ax) + 1, ay - 1, "cloth", tone)
        c.rect(int(ax) - 1, ay, int(ax) + 3, ay + 1, "leather", tone)
        c.line(int(ax) - 1, ay + 2 - (1 if lift > 1 else 0), int(ax) + 3, ay + 2 - (1 if lift > 1 else 0), "leather", 0 if tone == 1 else 1)

    def vanes(self, c, x, y, p, far=False):
        phase = (p.glint + (p.prop != 0)) % 2
        stamp(c, VANES[phase], x - 3, y - 3, LEG)
        if far:
            for yy in range(y - 3, y + 4):
                for xx in range(x - 3, x + 4):
                    t = c.tone[yy][xx] if 0 <= yy < 56 and 0 <= xx < 32 else None
                    if t is not None and t > 1:
                        c.tone[yy][xx] = t - 1

    def pinwheel_front(self, c, p, b, up, back):
        hx, hy = self.hand_r
        top = (hx - 3, hy - 9) if not back else (hx + 3, hy - 9)
        c.line(hx, hy, top[0], top[1], "wood", 2)
        self.vanes(c, top[0], top[1] - 2, p, far=back)
        c.put(hx, hy, "skin", 3)

    def over_front(self, c, p, b, up, back):
        y0 = 36 + b + up
        if not back:
            # the strap: right shoulder (image left) down across the chest to the bag on the left hip
            c.line(10, y0, 20, y0 + 8, "leather", 2)
            stamp(c, BAG, 19, 43 + b, LEG)
            # the cowlick, standing up off-centre
            top = self.head_top + b + up
            for dx, dy in ((17, -1), (17, -2), (18, -3), (19, -3)):
                c.put(dx, top + dy, "hair", 3)
        else:
            c.line(21, y0, 11, y0 + 8, "leather", 2)
            stamp(c, BAG, 8, 43 + b, LEG)
            top = self.head_top + b + up
            for dx, dy in ((14, -1), (14, -2), (13, -3), (12, -3)):
                c.put(dx, top + dy, "hair", 2)
        self.pinwheel_front(c, p, b, up, back)

    def arm_side(self, c, p, sh, swing, far, left):
        if not left:  # his right hand holds the pinwheel out in front
            hx, hy = 24, sh[1] + 6
            capsule(c, sh[0], sh[1] + 1, sh[0] + 3, sh[1] + 5, 1.6, "shirt", 1 if far else None)
            capsule(c, sh[0] + 3, sh[1] + 5, hx, hy, 1.2, "skin", 1 if far else None)
            c.line(hx, hy, 27, hy - 7, "wood", 1 if far else 2)
            self.vanes(c, 28, hy - 9, p, far=far)
            c.rect(hx - 1, hy - 1, hx, hy, "skin", 1 if far else 3)
            return
        hx, hy = sh[0] + swing * 1.3, sh[1] + 8
        capsule(c, sh[0], sh[1] + 1, sh[0] + swing * 0.4, sh[1] + 3, 1.7, "shirt", 1 if far else None)
        capsule(c, sh[0] + swing * 0.4, sh[1] + 3, hx, hy, 1.2, "skin", 1 if far else None)
        c.rect(int(hx) - 1, int(hy), int(hx), int(hy) + 1, "skin", 1 if far else 2)

    def over_side(self, c, p, b, up, swap):
        y0 = 36 + b + up
        top = self.head_top + b + up
        for dx, dy in ((15, -1), (15, -2), (14, -3), (13, -3)):
            c.put(dx, top + dy, "hair", 3)
        if not swap:  # the strap over the near (right) shoulder, across the chest
            c.line(14, y0, 19, y0 + 7, "leather", 2)
        else:  # the bag on the near (left) hip, the strap from the far shoulder across the chest
            c.line(19, y0 + 1, 15, y0 + 7, "leather", 2)
            stamp(c, BAG, 12, 42 + b, LEG)


NPC = Child()
