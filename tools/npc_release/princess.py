"""NPC 08 — the princess of the star ring (星環の姫). Batch 3: the story's central character.

Design: docs/npc/batch3/DESIGN_PROPOSAL.md (PR #48, approved). No personal name. The story (PR #55)
has her stay at the centre of the world by her own will and appear as a translucent "copy" (写し身)
at the record stones: the game tints / fades her, so she is drawn here at full opacity.

A little more grown-up than the hero and two pixels shorter; slim, straight-backed, chin a little in.
Long silver hair to the waist (cool blue shadows), straight-cut bangs parted in the middle, a thin
braid on each side hanging in front of the shoulders; dawn-sky eyes (deep indigo at the top, sky blue
at the bottom, a star-shaped shine), the outer corners a little raised; a small smile. A star-ring
circlet: a thin gold band round the head with the hero's stone at the front (the same blue
four-pointed star in gold as his pendant), set in a small gold ring (the star ring) rather than
hanging from the band. A white knee-length travelling dress with a blue border at the hem, white stockings,
soft brown boots; a deep star-blue short cape with a gold rim and a small gold star clasp (to the
chest in front, above the waist at the back), lit at the top left with a few folds; a blue sash
with gold star veins. Nothing in her hands: she holds them together in front of her (her bearing,
not a weapon). A thin gold bracelet on her LEFT wrist: facing left is facing right mirrored (she is
symmetrical: two braids, the hands together) with the bracelet on the near wrist; facing right it
is on the far wrist, hidden behind the near hand.

Revision 1 (the review of 2026-11-09): from the front the long hair falls behind and past the
shoulders to the waist (behind_front); from behind and the side it ends at the waist (not near the
knee) in locks with a sheen and dark partings; the cape has lit faces and folds.

Map characters (one per pixel; see npc_common):
  0-4 hair (silver)   a-d skin 1-4   e lash  o i iris (indigo)  j u iris (sky)  k star shine  l eye white
  n brow  m mouth  r cheeks
  A-E dress (white) 0-4   K-O cape (star blue) 0-4   P-T gold 0-4   U-Y sash (blue) 0-4
  the boots, the stockings and the circlet's stone (the hero's "gem") are drawn directly
"""

from npc_common import Pose, capsule, gait, half, legend, rows_of, stamp
from villager import Villager

RAMPS = {
    "hair": ["#222842", "#5e6888", "#98a2c0", "#c6cee4", "#eef2fc"],
    "skin": ["#6e3e2c", "#c8906a", "#f4c8a2", "#ffdfc4", "#fff2e4"],
    "dress": ["#3e4258", "#9ea4bc", "#dde2ee", "#f2f4fa", "#ffffff"],
    "cape": ["#080c2a", "#18225e", "#263896", "#3e56bc", "#6a86de"],
    "sash": ["#0a1840", "#1c3a86", "#2c5ab8", "#4a7ad8", "#8ab4f4"],
    "boot": ["#2a180e", "#5a3a24", "#86603e", "#a8805a", "#caa27c"],
    "stocking": ["#3e4258", "#a6acc2", "#e2e6f0", "#f2f4fa", "#ffffff"],
}
EYE = {"e": "#26223e", "o": "#24206a", "i": "#4436a8", "j": "#4c9ee6", "u": "#9ad6ff", "k": "#ffffff", "l": "#dcd6e4",
       "n": "#8a8aa8", "m": "#b8585a", "r": "#f6aa98"}
LEG = legend(
    [("01234", "hair", 0), ("abcd", "skin", 1), ("ABCDE", "dress", 0), ("KLMNO", "cape", 0), ("PQRST", "gold", 0),
     ("UVWXY", "sash", 0)],
    {**{ch: ("skin", 2, col) for ch, col in EYE.items()}, "@": ("cape", 2), "*": ("skin", 3)},
)

# ------------------------------------------------------------------ head (rows from head_top = 2)

HEAD_FRONT = half("""
................
..........233444
........22344444
.......234444433
......2344443332
.....23444333221
.....23443332221
....2344QRRRRSRR
....234Q34323432
....234334323422
....23423432342c
....2341221221bc
....234ecnnncccc
....234beeeecccc
....234boiklcccc
....234bijujcccc
....234bcjjccccc
....234bcccccccc
....234brrcccccc
....234abcccccmc
....2321abcccccm
....23211aabbbbb
.....2211111111a
""")

HEAD_BACK = half("""
................
..........233444
........22344443
.......234434432
......2343443321
.....23434433212
.....23433432122
....2343QRRRRRRR
....234223322332
....234223422332
....233213421342
....233213321342
....233213321332
....233213321332
....233213321332
....233213321332
....233213321332
....232213221322
....232213221322
....232213221322
....122112211221
....122112211221
.....22112211221
""")

# facing right: the face on the right, the hair falling behind on the left
HEAD_SIDE = rows_of("""
.
.......2234444433
.....22344344443332
....2343443444333322
...234343443333332221
...2343434333322222111
..23434333333222221112
..23433333QRRRRRRRRRRSR
..2343323323233233233322
..23443443443332332332332
..23441334133232332bc2332
..234413341322bcccc12212
..234313341322bccccnnncc
..233313341322bccceccccc
..233313321322bcccceeeecc
..233313321322bccccoiklccd
...3321332122bcccccijucccdd
...332133212bcccccccjjccccb
...322133212bccccccccrrccb
...32213321bacccccccccccmc
....221222111aaccccccccb
....2212221111aabbbbbb
....2212221111..aab
""")

# ------------------------------------------------------------------ body (rows from body_top = 24)

BODY_FRONT = half("""
.............aab
..........LNNNCD
........LNOONMMM
.......LNOONMMNM
......LMNNMMMNLM
......LMNMMMNLMM
......LMNMMNLMMM
......LMMMMNLMMM
......QRSRMNLMMM
.........QRSRRMM
..........BCDQRS
..........UVWXXX
..........UVWWWW
..........BCDCCC
.........BCDCCCC
.........BCDCCBC
........BCDCCCBC
........BCDCCBCC
.......BCDCCCBCC
.......BCDCCBCCC
.......BCDCCBCCC
.......UVWWWWWWW
.......ABBBBBBBB
""")

BODY_BACK = half("""
................
..........LNNNNM
........LNOONNMM
.......LNOONMMMM
......LMNNMMMNLM
......LMNMMMNLMM
......LMNMMMNLMM
......LMMMMNLMMM
......LMMMNLMMNL
......LMMNLMMMNL
......QRRSRRRRRR
.........BCDCCCC
..........UVWXXX
..........UVWWWW
.........BCDCCCC
.........BCDCCCC
........BCDCCBCC
........BCDCCBCC
.......BCDCCCBCC
.......BCDCCCBCC
.......BCDCCBCCC
.......UVWWWWWWW
.......ABBBBBBBB
""")

BODY_SIDE = rows_of("""
................ab
............LMMMMNL
...........LMNNMMMML
..........LMNNMMMMMML
..........LMNMMMMMMML
..........LMNMMMMMMML
..........LMMMMMMMMRS
..........LMMMMMMQRCD
..........LMMMMQRBCDC
..........LMMQRBCDCCC
..........QRRBCDCCCCB
...........BCDDCCCCB
...........UVWXXXXXV
...........UVWWWWWWV
..........BCDCCCCCCB
..........BCDCCCCCCCB
.........BCDCCCBCCCCB
.........BCDCCBCCCCCCB
........BCDCCCBCCCCCCB
........BCDCCBCCCCCCCCB
........BCDCCBCCCCCCCCB
........UVWWWWWWWWWWWWWV
........ABBBBBBBBBBBBBBB
""")


def star(c, x, y, glint):
    """The star-ring stone: the hero's pendant (a blue four-pointed star in gold), the same form and
    colours; its shine moves with `glint` like his."""
    for dx, dy, m, t in ((1, 0, "gold", 3), (0, 1, "gold", 2), (2, 1, "gold", 2), (1, 1, "gem", 4), (1, 2, "gem", 2), (0, 2, "gem", 3),
                         (2, 2, "gem", 1), (1, 3, "gem", 1), (0, 3, "gold", 1), (2, 3, "gold", 1), (1, 4, "gold", 1), (-1, 2, "gem", 3), (3, 2, "gem", 3)):
        c.put(x + dx, y + dy, m, t)
    c.put(x + (0, 1, 2)[glint], y + 2, "gem", 4)


RING = ((12, 8, 2), (12, 9, 2), (12, 10, 1), (13, 7, 2), (14, 6, 3), (15, 6, 3), (16, 6, 2), (17, 7, 2),
        (18, 8, 1), (18, 9, 1), (18, 10, 1), (13, 11, 1), (14, 12, 1), (15, 12, 1), (16, 12, 1), (17, 11, 1))


def ring(c, cx, cy):
    """The star ring (星環) round the stone: a thin gold ring set in the circlet, lit at the top left.
    The stone sits in the ring like a compass star, not hanging from the band as a drop."""
    for x, y, tone in RING:
        c.put(cx - 15 + x, cy - 9 + y, "gold", tone)


class Princess(Villager):
    id = "princess"
    ramps = RAMPS
    LEG = LEG
    HEAD_FRONT, HEAD_BACK, HEAD_SIDE = HEAD_FRONT, HEAD_BACK, HEAD_SIDE
    BODY_FRONT, BODY_BACK, BODY_SIDE = BODY_FRONT, BODY_BACK, BODY_SIDE
    head_top = 2  # the map's first row is empty: the crown's outline is at row 2, two below the hero's
    body_top = 24
    hip = 44
    breath_below = 35
    legs = dict(xs=(12, 17), w=2, mat="stocking", shoe="boot", skirt=False, r=1.6)
    side_shoulder = (14, 27)
    side_hip_x = 15
    near_leg_over_body = False
    walk_gait = dict(stride=2, lift=2, bob=1, arm=0)

    def pose(self, action, i):
        if action == "idle":
            return Pose(breath=(0, 1, 1, 0)[i], sway=(0, 0, 1, 0)[i], blink=i == 3, glint=(0, 1, 2, 1)[i])
        return gait(i, 6, **self.walk_gait)

    # -------------------------------------------------------------- front / back
    def foot_front(self, c, x0, y, back):
        c.rect(x0, y - 3, x0 + 2, y, "boot")
        c.rect(x0 - (1 if x0 < 16 else 0), y - 1, x0 + 2 + (0 if x0 < 16 else 1), y, "boot")
        c.line(x0 - (1 if x0 < 16 else 0), y, x0 + 2 + (0 if x0 < 16 else 1), y, "boot", 1)
        c.line(x0, y - 3, x0 + 2, y - 3, "boot", 3 if not back else 1)  # the turned-down cuff
        if not back:
            c.put(x0 + 1, y - 1, "boot", 4)

    def body_shift(self, p, b, up, back):
        def shift(row, col, ch):
            y = self.body_top + row
            dx = round(p.sway * (y - 40) / 6) if y > 40 and (col < 10 or col > 21) else 0
            return dx, b + (up if y < self.breath_below else 0)
        return shift

    # the long hair from the front: (column, first row, last row, tone) for the left side; the
    # right side is its mirror, a tone darker (the light is from the top left)
    FLANK = ((3, 22, 34, 2), (4, 20, 37, 3), (5, 20, 38, 3), (6, 20, 36, 2), (7, 20, 27, 1))

    def behind_front(self, c, p, b, up, back):
        if back:
            self.hair_flank_back(c, p, b, up)
        else:
            self.hair_behind_front(c, p, b, up, back)

    def hair_behind_front(self, c, p, b, up, back):
        """The long hair: down both sides behind the shoulders to the waist, framing her; the tips
        are uneven and lag when she walks."""
        t = b + up
        for x, y0, y1, tone in self.FLANK:
            for y in range(y0, y1 + 1):
                lag = round(p.sway * max(0, y - 31) / 9)
                tt = tone if y < y1 - 1 else max(1, tone - 1)
                if x == 6 and y >= 29:
                    tt = 1  # the shadow where the hair falls behind the sleeve
                if x == 5 and y >= 31 and y < y1 - 1:
                    tt = 2  # two locks: the outer one lit, the inner one in shadow
                if y in (26, 27) and x == 4:
                    tt = 4  # the sheen where the hair turns over the shoulder
                c.put(x - lag, y + t, "hair", tt)
                c.put(31 - x + lag, y + t, "hair", tt - 1 if tt >= 3 else tt)

    # the locks below the cape from behind: (column, last row, tone); the three locks of the head map
    # (lit on their left, a dark parting between them) come out under the cape and end at the waist
    FALL = ((9, 36, 3), (10, 37, 3), (11, 37, 2), (12, 36, 1), (13, 37, 3), (14, 38, 4), (15, 38, 2),
            (16, 38, 2), (17, 38, 2), (18, 37, 2), (19, 36, 1), (20, 37, 2), (21, 37, 2), (22, 36, 1))

    def hair_fall_back(self, c, p, t):
        """From behind: the cape's blue band crosses the hair (design: the hair runs under the short
        cape); below its gold rim the hair comes out again in three locks and ends in uneven tips at
        the waist, so the sash and the white skirt show below it."""
        for x, last, tone in self.FALL:
            for y in range(35, last + 1):
                lag = round(p.sway * max(0, y - 35) / 3)
                tt = tone if y < last else max(1, min(tone, 3) - 1)
                if tone == 4 and y > 35:
                    tt = 3 if y < last else 2
                c.put(x - lag, y + t, "hair", tt)

    # from behind the long hair also falls at both sides of the cape, to the waist
    BACK_FLANK = ((3, 25, 32, 2), (4, 24, 35, 3), (5, 24, 34, 2))

    def hair_flank_back(self, c, p, b, up):
        t = b + up
        for x, y0, y1, tone in self.BACK_FLANK:
            for y in range(y0, y1 + 1):
                lag = round(p.sway * max(0, y - 30) / 5)
                tt = tone if y < y1 else 1
                c.put(x - lag, y + t, "hair", tt)
                c.put(31 - x + lag, y + t, "hair", max(1, tt - 1) if tt >= 3 else min(tt, 2) if tt > 1 else 1)

    def arms_front(self, c, p, b, up, back):
        """The sleeves come out from under the cape; the hands are held together in front, at the top
        of the skirt (her right over her left; the bracelet on her left wrist, the image's right).
        From behind only the elbows show beside the waist."""
        t = b + up
        if back:
            for x, d in ((7, 1), (24, -1)):
                capsule(c, x, 33 + t, x + d, 36 + t, 1.2, "dress", 1)
            self.hand_r = self.hand_l = (16, 38 + t)
            return
        for side in (0, 1):
            far = side == 1
            ex = 7 if side == 0 else 24
            d = 1 if side == 0 else -1
            hx = 13 if side == 0 else 18
            capsule(c, ex, 32 + t, ex + d, 35 + t, 1.3, "dress", 1 if far else None)
            capsule(c, ex + d, 35 + t, hx, 39 + t, 1.2, "dress", 1 if far else None)
            # the forearm's shadow on the skirt below it
            for k in range(1, 5):
                c.put(ex + d * (1 + k), 38 + t + (k > 2), "dress", 1)
        y = 39 + t
        c.rect(13, y, 18, y + 2, "skin", 2)
        c.put(13, y, "skin", 3)
        c.put(14, y, "skin", 4)
        c.put(15, y, "skin", 3)
        c.line(14, y + 2, 17, y + 2, "skin", 1)
        c.put(18, y, "skin", 1)
        c.put(16, y + 1, "skin", 1)  # where the fingers meet
        c.put(19, y, "gold", 3)  # the bracelet on her left wrist
        c.put(19, y + 1, "gold", 2)
        c.put(20, y, "gold", 1)
        self.hand_r, self.hand_l = (14, y), (17, y)

    def braid(self, c, pts, far=False):
        """A thin braid along `pts` (top to bottom): two pixels wide, the plaits alternating light and
        dark; a gold tie and a small tuft at the end."""
        for k, (x, y) in enumerate(pts):
            a, b_ = (3, 2) if k % 2 == 0 else (2, 1)
            if far:
                a, b_ = a - 1, max(1, b_ - 1)
            c.put(x, y, "hair", a)
            c.put(x + 1, y, "hair", b_)
        x, y = pts[-1]
        c.put(x, y + 1, "gold", 2 if far else 3)
        c.put(x + 1, y + 1, "gold", 1 if far else 2)
        c.put(x, y + 2, "hair", 2)
        c.put(x + 1, y + 2, "hair", 1)
        c.put(x + (0 if far else 1), y + 3, "hair", 1)

    @staticmethod
    def braid_path(x0, y0, n, drift, lag):
        """From the temple down: straight beside the cheek, then out over the front of the shoulder."""
        pts = []
        for k in range(n):
            x = x0 + min(drift, drift * max(0, k - 8) // 4) + (lag if k > n - 5 else 0)
            pts.append((x, y0 + k))
        return pts

    def over_front(self, c, p, b, up, back):
        t = b + up
        top = self.head_top + t
        if not back:
            sw = 1 if p.sway > 0 else -1 if p.sway < 0 else 0
            self.braid(c, self.braid_path(5, top + 12, 18, 3, -sw))
            right = [(30 - x, y) for x, y in self.braid_path(5, top + 12, 18, 3, sw)]
            self.braid(c, right, far=True)
            ring(c, 15, top + 7)
            star(c, 14, top + 5, p.glint)
            if not p.blink:  # the right eye as the left (not its mirror): both shine on the light's side
                for dy, row in ((14, "oikl"), (15, "ijuj"), (16, ".jj.")):
                    for k, ch in enumerate(row):
                        c.put(20 + k, top + dy, "skin", 3)
                        if ch != ".":
                            c.put(20 + k, top + dy, "skin", 2)
                            c.paint(20 + k, top + dy, EYE[ch])
            c.put(15, top + 17, "skin", 1)  # the nose: one shadow pixel
            c.put(14, top + 19, "skin", 2)  # a soft smile: only the right corner rises
            c.put(16, top + 20, "skin", 2)
            c.paint(16, top + 20, EYE["m"])
            c.put(15, top + 20, "skin", 2)
            c.paint(15, top + 20, EYE["m"])
            # the cape's star clasp
            cy = self.body_top + 2 + t
            for dx, dy, tone in ((1, -1, 4), (0, 0, 2), (1, 0, 3), (2, 0, 2), (1, 1, 2), (1, 2, 1)):
                c.put(14 + dx + (dx > 0), cy + dy, "gold", tone)
            self.sash_veins(c, self.body_top + 11 + t, 10, 21)
        else:
            c.put(11 + p.glint * 4, top + 7, "gold", 4)  # a glint runs round the circlet
            self.sash_veins(c, self.body_top + 12 + t, 8, 23)
            self.hair_fall_back(c, p, t)

    def sash_veins(self, c, y, x0, x1):
        """Star veins: a thin gold line running along the blue sash, rising and falling, with one bright
        point (a star) on it."""
        for x in range(x0 + 1, x1):
            c.put(x, y + (1 if (x // 3) % 2 else 0), "gold", 2 if x < 16 else 1)
        c.put(x0 + 3, y, "gold", 4)

    def blink_front(self, c, top):
        """Eyes closed: the lid comes down, the lashes make a soft downward curve."""
        for x in (8, 9, 10, 11, 20, 21, 22, 23):
            for dy in (13, 14, 15, 16):
                c.put(x, top + dy, "skin", 3)
            c.put(x, top + 15, "skin", 2)
            c.paint(x, top + 15, EYE["e"])
        for x in (7, 24):
            c.put(x, top + 14, "skin", 2)
            c.paint(x, top + 14, EYE["e"])
            c.put(x, top + 12, "skin", 3)

    # -------------------------------------------------------------- side
    def leg_side(self, c, p, fwd, lift, tone):
        hip = (self.side_hip_x, self.hip + p.bob)
        ax, ay = hip[0] + fwd, 52 - lift
        kx, ky = hip[0] + fwd * 0.6 + (1.2 if lift else 0.3), (hip[1] + ay) / 2 - lift * 0.5
        capsule(c, hip[0], hip[1], kx, ky, 1.5, "stocking", tone)
        capsule(c, kx, ky, ax, ay - 1, 1.3, "stocking", tone)
        toe = 3 if lift < 2 else 2
        c.rect(int(ax) - 1, ay - 1, int(ax) + 1, ay, "boot", tone)
        c.line(int(ax) - 1, ay - 1, int(ax) + 1, ay - 1, "boot", 1 if tone == 1 else 3)
        c.rect(int(ax) - 1, ay, int(ax) + toe, ay + 2, "boot", tone)
        c.line(int(ax) - 1, ay + 3 - (1 if lift > 1 else 0), int(ax) + toe, ay + 3 - (1 if lift > 1 else 0), "boot", 0 if tone == 1 else 1)
        if tone is None:
            c.put(int(ax) + 1, ay + 1, "boot", 4)

    def side_body_shift(self, p, b, up):
        def shift(row, col, ch):
            y = self.body_top + row
            dx = round(-p.sway * (y - 40) / 6) if y > 40 and col < 12 else 0
            return dx, b + (up if y < self.breath_below else 0)
        return shift

    # the long hair down her back, facing right: (row, left, right) edges; it trails when she walks
    BACK_HAIR = ((24, 4, 11), (26, 4, 10), (28, 5, 10), (30, 6, 10), (32, 6, 10), (34, 7, 10), (36, 8, 10),
                 (38, 9, 9))

    def back_hair_side(self, c, p, b, up):
        t = b + up
        edges = {}
        for (ya, la, ra), (yb, lb, rb) in zip(self.BACK_HAIR, self.BACK_HAIR[1:]):
            for y in range(ya, yb):
                f = (y - ya) / (yb - ya)
                edges[y] = (round(la + (lb - la) * f), round(ra + (rb - ra) * f))
        edges[38] = (9, 9)
        for y, (l, r) in edges.items():
            lag = round(p.sway * max(0, y - 30) / 6)
            for x in range(l, r + 1):
                k = x - l
                # the head's locks go on down the back: the outer one lit on its edge (a sheen over
                # the shoulder blade), a dark parting, the inner ones against the cape in shadow
                tone = 3 if k in (1, 3) else 2
                if k == 1 and 27 <= y <= 29:
                    tone = 4
                if (k == 2 and r - l >= 3) or (x == r - 1 and r - l >= 6):
                    tone = 1
                if x == r:
                    tone = 1 if y < 30 else 2
                if y >= 36:
                    tone = 2 if k == 0 else 1
                c.put(x - lag, y + t, "hair", tone)

    def behind_side(self, c, p, b, up, swap):
        pass

    def arm_side(self, c, p, sh, swing, far, left):
        """The sleeve from under the cape, the forearm forward to the hands held in front of the top of
        the skirt; the far hand shows beyond the near one. Her left wrist has the bracelet."""
        y = sh[1]
        if far:
            capsule(c, 16, y + 7, 20, y + 10, 1.1, "dress", 1)
            c.rect(20, y + 10, 21, y + 11, "skin", 1)
            if left:
                c.put(19, y + 10, "gold", 2)
            return
        capsule(c, 14, y + 4, 15, y + 8, 1.5, "dress")
        capsule(c, 15, y + 8, 18, y + 11, 1.3, "dress")
        c.rect(19, y + 10, 20, y + 11, "skin", 2)
        c.put(19, y + 10, "skin", 3)
        c.put(20, y + 12, "skin", 1)
        if left:
            c.put(18, y + 10, "gold", 3)
            c.put(18, y + 11, "gold", 2)

    def side(self, p, swap=False):
        c = self.canvas()
        b = p.bob
        up = -p.breath
        sh = (self.side_shoulder[0], self.side_shoulder[1] + b + up)
        self.leg_side(c, p, p.far[0], p.far[1], 1)
        self.leg_side(c, p, p.near[0], p.near[1], None)
        self.arm_side(c, p, sh, 0, True, left=not swap)
        if up:
            stamp(c, self.BODY_SIDE, 0, self.body_top, self.LEG, shift=self.side_body_shift(p, b, 0))
        stamp(c, self.BODY_SIDE, 0, self.body_top, self.LEG, shift=self.side_body_shift(p, b, up))
        self.back_hair_side(c, p, b, up)
        top = self.head_top + b + up
        stamp(c, self.HEAD_SIDE, 0, top, self.LEG)
        if p.blink:
            self.blink_side(c, top)
        star(c, 20, top + 5, p.glint)
        self.arm_side(c, p, sh, 0, False, left=swap)
        c.put(18, self.body_top + 2 + b + up, "gold", 3)  # the clasp
        c.put(18, self.body_top + 3 + b + up, "gold", 2)
        sw = 1 if p.sway > 0 else -1 if p.sway < 0 else 0
        self.braid(c, self.braid_path(12, top + 11, 19, 3, -sw))
        return c

    def blink_side(self, c, top):
        for x in (19, 20, 21, 22):
            for dy in (14, 15, 16):
                c.put(x, top + dy, "skin", 3)
            c.put(x, top + 16, "skin", 2)
            c.paint(x, top + 16, EYE["e"])
        c.put(18, top + 15, "skin", 2)
        c.paint(18, top + 15, EYE["e"])


NPC = Princess()
