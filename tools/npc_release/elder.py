"""NPC 01 — the elder (長老): the village's head, who gives the hero his first quest.

Small and hunched, a bald crown with white hair at the sides, thick drooping white brows, kind
smiling eyes, a long white beard; a navy robe with silver-grey trim and a crimson sash; leather
sandals; a wooden staff carved with the star ring (his right hand, held out in front: he leans on it).
Map characters (one per pixel; see npc_common):
  0-4 hair / beard (white)   a-d skin 1-4   e lash  m mouth  r blush
  A-E robe (navy) 0-4        F-J trim (silver) 0-4   K-O sash (crimson) 0-4
  P-T leather 0-4            U-Y wood 0-4            f-j gold 0-4   v-z gem 0-4
  @ shoulder anchor          * hand anchor (skin)
"""

from npc_common import (H, Npc, Pose, capsule, half, legend, rows_of, stamp, stamp_at)

RAMPS = {
    "hair": ["#4a4a58", "#9c9cac", "#cdd0da", "#e6e8ee", "#ffffff"],
    "skin": ["#5e3426", "#b47c62", "#e2ae8a", "#f4c8a4", "#ffe2c8"],
    "robe": ["#0c1024", "#1c2850", "#2c3e74", "#44609c", "#6a88c2"],
    "trim": ["#2a2e38", "#6c7280", "#a6acb8", "#d0d4dc", "#f2f4f8"],
    "sash": ["#26080e", "#661824", "#962a36", "#bc4650", "#de7a7a"],
}
LEG = legend(
    [("01234", "hair", 0), ("abcd", "skin", 1), ("ABCDE", "robe", 0), ("FGHIJ", "trim", 0), ("KLMNO", "sash", 0),
     ("PQRST", "leather", 0), ("UVWXY", "wood", 0), ("fghij", "gold", 0), ("vwxyz", "gem", 0)],
    {"e": ("skin", 2, "#3a2620"), "m": ("skin", 2, "#8a4a40"), "r": ("skin", 2, "#ee9c8c"),
     "@": ("robe", 2), "*": ("skin", 3)},
)

# ------------------------------------------------------------------ front (left half; mirrored)

HEAD_FRONT = half("""
............bccc
..........bcdddd
.........bcddddc
........bcdddccc
......2bcddccccc
.....234bcaaaacc
....23443bcccccc
....234432bccccc
....2344321ccccc
....2343bcc2344c
....2343bc2443cc
....234bcc1eeccc
....23abcceccecd
....23abcrcccccb
.....2abc2334444
......2b23444333
......a23443333m
.......234344343
.......234344343
.......234344343
........23344343
........23344343
.........2344343
.........2344343
..........234343
...........23343
............2343
.............233
..............22
""")

HEAD_BACK = half("""
............bccc
..........bcdddd
.........bcddddc
........bcdddccc
.......bcddccccc
......2bcccccccc
.....23bccccbccc
....2343bccccbcc
....23443bcccccc
....2344332bcccc
...a234343322bbb
...a234343343322
....234343343343
....234343343343
.....23343343343
.....22332bb2332
......2bbbbbbbbb
.......bbbbbbbbb
""")

BODY_FRONT = half("""
..........BCDDDD
.........BCDDCCC
.........BDDCCCC
.........BDCCHCC
.........BCCCCHC
.........BCBCCCH
.........BCBCCCC
.........BCBCCCC
.........BCBCCCC
.........BCBCCCC
.........BBCCCCC
.......KLMMMMMMM
.......KMNNNNNNN
.......KLMMMMMMM
......BCCBCCCCHC
......BCCBCCCCHC
......BCBCCCCCHC
.....BCCBCCCCCHC
.....BCCBCCCCCHC
.....BCBCCCCCCHC
.....BCBCCCCCCHC
....BCCBCCCCCCHC
....BCCBCCCCCCHC
....BCBCCCCCCCHC
....BCBCCCCCCCHC
....HIIIIIIIIIII
....GHHHHHHHHHHH
""")

BODY_BACK = half("""
..........BCDDDD
.........BCDDDDC
.........BDDDDCC
.........BDDDCCC
.........BDDCCBC
.........BCDCCBC
.........BCCCBCC
.........BCCCBCC
.........BCCCBCC
.........BCCBCCC
.........BCCBCCC
.......KLMMMMMMM
.......KMNNNNNNN
.......KLMMMMMMM
......BCCBCCCBCC
......BCCBCCCBCC
......BCBCCCCBCC
.....BCCBCCCBCCC
.....BCCBCCCBCCC
.....BCBCCCCBCCC
.....BCBCCCCBCCC
....BCCBCCCCBCCC
....BCCBCCCCBCCC
....BCBCCCCBCCCC
....BCBCCCCBCCCC
....HIIIIIIIIIII
....GHHHHHHHHHHH
""")
BODY_TOP = 26

# the sash's knot: its two ends hang on his left of the front (image left)
KNOT = [(11, 40, "L"), (12, 40, "M"), (11, 41, "M"), (12, 41, "N"), (11, 42, "M"), (12, 42, "L"), (11, 43, "L"), (12, 43, "K"),
        (10, 37, "N"), (11, 37, "O"), (12, 37, "N"), (10, 38, "M"), (11, 38, "N"), (12, 38, "L"), (10, 39, "L"), (11, 39, "M"), (12, 39, "L")]

# the arms seen from the front: wide sleeves, a silver cuff, the hand below
ARM_DOWN = rows_of("""
..@DA
.CDDA
.CDDB
CDDCB
CDDCB
CDDCB
CDCCB
CDCCA
HIIIH
.*bc.
.ab..
""", 5)
ARM_HOLD = rows_of("""
.....@DA
....CDDA
....CDDB
...CDDCB
...CDDCB
..CDDCB.
..CDCCA.
.CDCCA..
.HIIIH..
.*bc....
.ab.....
""", 8)

# the staff's head: a ring carved round a gold star (星環)
STAFF_HEAD = rows_of("""
..WXW..
.X...W.
X..g..V
W.gzg.V
V..g..V
.V...V.
..VWV..
...W...
""", 7)

# ------------------------------------------------------------------ side (facing right)

HEAD_SIDE = rows_of("""
................bcccb
..............bcddddccb
.............bcdddddcccb
............bcddddddccccb
...........2bcddddccccccb
..........23bcddcccaaaaccb
.........2343bcccccccccccb
.........23443bccccccccccc
.........234432bcccc2344443
.........2344321bcc2344ccc
.........234432bcbcccceeccd
.........23443bacbccceccecdd
.........2343bbabcccccrcccccb
..........2343bbcccccccccbba
..........23432bccccc23444432
...........2332bccc2344433332
............22bcc234434434332
..............bb234434434332
...............234434434332
...............234434434332
................2443443432
................2443443432
.................243443432
.................23443432
..................2344342
...................24432
....................2432
.....................22
""")

BODY_SIDE = rows_of("""
..........BCDDC
........BCDDDDCC
......BCDDDDCCCCB
.....BCDDDCCCCCCCB
.....BCDDCCCCCCCCCB
....BCDDCCCCCCCCCCB
....BCDCCCCBCCCCCCCB
....BCDCCCCBCCCCCCCB
....BCCCCCBCCCCCCCCB
.....BCCCCBCCCCCCCCB
.....BCCCCBCCCCCCCCB
.....KLMMMMMMMMMMMLK
.....KMNNNNNNNNNNNMK
.....KLMMMMMMMMMMMLK
.....BCCCBCCCCCCCHCB
.....BCCCBCCCCCCCHCB
....BCCCBCCCCCCCCHCB
....BCCCBCCCCCCCCHCB
....BCCBCCCCCCCCCHCCB
....BCCBCCCCCCCCCHCCB
...BCCCBCCCCCCCCCHCCB
...BCCCBCCCCCCCCCHCCB
...BCCBCCCCCCCCCCHCCB
...BCCBCCCCCCCCCCHCCCB
...BCCBCCCCCCCCCCHCCCB
...HIIIIIIIIIIIIIIIIIH
...GHHHHHHHHHHHHHHHHHG
""")

HAND_SIDE = rows_of("""
.bc.
*cdc
.bcb
""", 4)


def staff(c, x, top, ground=55, tone=None):
    """The staff: a straight shaft from just under its carved head to the ground."""
    for y in range(top + 7, ground + 1):
        c.put(x, y, "wood", tone if tone is not None else (3 if y % 7 == 0 else 2))
    stamp_at(c, STAFF_HEAD, "g", "f", (x, top + 3), LEG)
    c.put(x, top + 3, "gem", 3)


class Elder(Npc):
    id = "elder"
    ramps = RAMPS
    walk_gait = dict(stride=2, lift=1, bob=1, arm=1)

    def pose(self, action, i):
        p = super().pose(action, i)
        if action == "idle":
            p.nod = (0, 0, 1, 1)[i]  # a slow nod while he breathes
        return p

    # -------------------------------------------------------------- front / back
    def front(self, p, back=False):
        c = self.canvas()
        b = p.bob
        up = -p.breath
        # feet (sandals) below the hem; the stepping foot lifts
        for (fwd, lift), x0 in ((p.near, 11), (p.far, 17)):
            y = 55 - lift
            if back:
                c.rect(x0, y - 2, x0 + 3, y - 1, "skin")
                c.rect(x0 + 1, y - 2, x0 + 2, y - 2, "leather", 2)
                c.rect(x0, y, x0 + 3, y, "leather", 1)
            else:
                c.rect(x0, y - 2, x0 + 3, y - 1, "skin")
                c.put(x0 + (0 if x0 < 16 else 3), y - 2, "skin", 1)
                c.rect(x0, y - 2, x0 + 3, y - 2, "leather", 3)
                c.rect(x0, y, x0 + 3, y, "leather", 1)
                for k in range(4):
                    c.shade(x0 + k, y - 1, 3 if k % 2 == 0 else 2)
        # the body: the hem swings with the step (rows below the sash)
        def shift(row, col, ch):
            y = BODY_TOP + row
            dy = b + (up if y < 37 else 0)
            dx = round(p.sway * (y - 44) / 8) if y > 44 else 0
            return dx, dy
        stamp(c, BODY_BACK if back else BODY_FRONT, 0, BODY_TOP, LEG, mirrored=True, shift=shift)
        if not back:
            for x, y, ch in KNOT:
                xx = x + (round(p.sway * 0.5) if y > 40 else 0)
                c.put(xx, y + b, *LEG[ch])
        # arms: his right (the staff) on the image's left in front, on the right from behind
        top = 10 + b + up + p.nod
        st_side = 0 if not back else 1
        sh_r = (8, 29 + b + up) if not back else (23, 29 + b + up)
        sh_l = (23, 29 + b + up) if not back else (8, 29 + b + up)
        # the free arm swings: forward lifts the hand a little
        swing = p.arm_far if not back else p.arm_near
        hand_lift = max(0, swing)
        if back:
            stamp(c, HEAD_BACK, 0, top, LEG, mirrored=True)
        free = stamp_at(c, ARM_DOWN, "@", "*", (sh_l[0], sh_l[1] - hand_lift), LEG, flip=not back, darker=back)
        # the staff, then the hand round it
        sx = 3 + p.prop // 2 if not back else 28 + p.prop // 2
        hand = stamp_at(c, ARM_HOLD, "@", "*", sh_r, LEG, flip=back, darker=False)
        staff(c, sx, 1 + b + up - p.prop // 2 * 0)
        hy = hand[1]
        for dy in (-1, 0, 1):
            c.put(sx + (1 if not back else -1), hy + dy, "skin", 3 if dy < 0 else 2)
            c.put(sx, hy + dy, "skin", 3 if dy <= 0 else 2)
        c.put(sx - (1 if not back else -1), hy, "skin", 2)
        del free, st_side
        if not back:
            stamp(c, HEAD_FRONT, 0, top, LEG, mirrored=True)
            if p.blink:
                pass  # his eyes are already closed in a smile
        return c

    # -------------------------------------------------------------- side
    def side(self, p, swap=False):
        c = self.canvas()
        b = p.bob
        up = -p.breath
        ox = -2  # he stands a little back in the frame: the staff is held out in front
        sh = (13 + ox, 29 + b + up)
        # the staff is in his right hand: near facing right, far (behind him) facing left; it is
        # planted ahead of him and only creeps forward as he steps
        staff_x = 28 + (1 if p.prop > 0 else 0)
        hand_at = (staff_x - 1, 37 + b + up)

        def foot(fwd, lift, tone):
            x = 13 + ox + fwd
            y = 55 - lift
            c.rect(x, y - 1, x + 4, y - 1, "skin", tone)
            c.put(x, y - 2, "skin", tone)
            c.put(x + 1, y - 2, "skin", tone)
            c.put(x + 2, y - 1, "leather", 3 if tone is None else 1)
            c.rect(x - 1, y, x + 4, y, "leather", 1 if tone is None else 0)

        def arm_reach(tone, far=False):
            sx, sy = sh
            hx, hy = hand_at
            ex, ey = (sx + hx) / 2 - 1, (sy + hy) / 2 + 2
            capsule(c, sx, sy, ex, ey, 2.3, "robe", 0 if far else 1)
            capsule(c, ex, ey, hx - 2, hy - 1, 2.1, "robe", 0 if far else 1)
            capsule(c, sx, sy - 0.6, ex, ey - 0.6, 1.3, "robe", 1 if far else 3)
            capsule(c, ex, ey - 0.6, hx - 2, hy - 1.6, 1.1, "robe", 1 if far else 3)
            c.line(int(hx) - 3, int(hy) - 3, int(hx) - 3, int(hy) + 1, "trim", 1 if far else 3)
            c.line(int(hx) - 2, int(hy) - 3, int(hx) - 2, int(hy) + 1, "trim", 1 if far else 2)
            stamp_at(c, HAND_SIDE, "*", "*", (hx - 1, hy), LEG, darker=far)

        def arm_free(swing, far=False):
            sx, sy = sh
            hx, hy = sx + swing * 1.5, sy + 11
            capsule(c, sx, sy + 1, hx, hy - 2, 2.4, "robe", 0 if far else 1)
            capsule(c, sx - 0.5, sy + 1, hx - 0.5, hy - 2.5, 1.3, "robe", 1 if far else 3)
            c.line(int(hx) - 2, int(hy) - 1, int(hx) + 2, int(hy) - 1, "trim", 1 if far else 3)
            c.rect(int(hx) - 1, int(hy), int(hx) + 1, int(hy) + 1, "skin", 1 if far else None)
            c.put(int(hx), int(hy) + 2, "skin", 1 if far else 2)

        # far side: the far foot, the far arm (and the staff when he faces left)
        foot(p.far[0], p.far[1], 1)
        if swap:
            staff(c, staff_x, 1 + b + up, tone=1)
            arm_reach(1, far=True)
        else:
            arm_free(p.arm_far, far=True)

        def shift(row, col, ch):
            y = BODY_TOP + row
            dy = b + (up if y < 37 else 0)
            dx = -round(p.sway * (y - 44) / 8) if y > 44 and col < 10 else 0
            return dx, dy
        stamp(c, BODY_SIDE, ox, BODY_TOP, LEG, shift=shift)
        foot(p.near[0], p.near[1], None)
        stamp(c, HEAD_SIDE, ox, 10 + b + up + p.nod, LEG)
        if swap:
            arm_free(p.arm_near)
        else:
            staff(c, staff_x, 1 + b + up)
            arm_reach(None)
        return c


NPC = Elder()
