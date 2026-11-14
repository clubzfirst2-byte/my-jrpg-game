"""v3 elder (長老), round 4: hand-drawn pixel maps at the v3 grid (npc_pixmap.py).

v1 (src/art-release/npc/npc.elder.*, tools/npc_release/elder.py, read only) is the reference for the look:
a bald crown with white hair at the sides and round the back, thick drooping white brows, eyes closed in a
smile, a long white beard; a navy robe with a silver trim and hem and a crimson sash (its knot at his right);
sandals; a straight wooden staff taller than he is, its head a ring round a gold star with a gem, in his
right hand. New at 2x: the beard's and the hair's locks, the ear, the forehead's line, the sleeve's cuff,
the robe's slanting folds, the sash's light and knot, the sandal's strap and toes, the staff head's ring,
star arms, gem and collar, the fist on the staff.

Legend (6 tones each, 0 outline .. 5 highlight; tone 2 is v3's middle shade):
  0-5 hair / beard   a-f skin   A-F robe   G-L trim (silver)   M-R sash   S-X leather
  g-l gold   m-r wood   s-x gem
  inks: # closed eye   = mouth   ~ blush
"""

from npc_pixmap import grid, half, legend

RAMPS = {  # v1's ramps (tools/npc_release/elder.py RAMPS + tools/art_proto/pixel.py BASE_RAMPS)
    "hair": ["#4a4a58", "#9c9cac", "#cdd0da", "#e6e8ee", "#ffffff"],
    "skin": ["#5e3426", "#b47c62", "#e2ae8a", "#f4c8a4", "#ffe2c8"],
    "robe": ["#0c1024", "#1c2850", "#2c3e74", "#44609c", "#6a88c2"],
    "trim": ["#2a2e38", "#6c7280", "#a6acb8", "#d0d4dc", "#f2f4f8"],
    "sash": ["#26080e", "#661824", "#962a36", "#bc4650", "#de7a7a"],
    "leather": ["#24160c", "#4a3020", "#704c30", "#946c46", "#b88c5e"],
    "gold": ["#5a4018", "#a07a30", "#e8c060", "#f8dc88", "#fff4c8"],
    "wood": ["#1e1008", "#4a2c16", "#6e4424", "#906038", "#b07e50"],
    "gem": ["#0e2a60", "#1a5cb8", "#2a8de2", "#78c8ff", "#e0f6ff"],
}
INKS = {"#": "#3a2620", "=": "#8a4a40", "~": "#ee9c8c"}
EYE_INKS = {INKS["#"]}
IRIS_INKS = EYE_INKS  # his eyes are closed in a smile in every frame (v1: "already closed"): the check
# counts the closed eyes' lines instead of irises: front 2, side 1, back 0, also on the "blink" frame


def IRIS_WANT(view, blink, want):
    return 0 if view == "up" else (2 if view == "down" else 1)


LEG = legend([("012345", "hair"), ("abcdef", "skin"), ("ABCDEF", "robe"), ("GHIJKL", "trim"),
              ("MNOPQR", "sash"), ("STUVWX", "leather"), ("ghijkl", "gold"), ("mnopqr", "wood"),
              ("stuvwx", "gem")], INKS)

# ------------------------------------------------------------------ maps (hand drawn)

HEAD_FRONT = half("""
........................ddeeeeee
......................deeeeeffff
....................ddeeffffffee
...................deeefffffffee
..................deeeffffffffee
.................deeefffffffffee
................deeeffffffffeeee
...............deeefffffffeeeeee
............44ddeeffffeeeeeeeeee
...........445deeefffeeeeeeeeeee
..........345543deeeeeeeeeeeeeee
..........345543deeebbbbbbbbeeee
........3455544433deeeeeeeeeeeee
........3455544433deeeeeeeeeeeee
........345554444332deeeeeeeeeee
........345554444332deeeeeeeeeee
........34555444433221eeeeeeeeee
........34555444433221eeeeeeeeee
........34554433deeeeee4445555ee
........34554433deeeee34455555ee
........34554433deee34555544eeee
........34554433deee3445544eeeee
........345543deeeeeee####eeeeee
........345543deeeee##eeee##eeee
........3454cddeeeeeeeeeeeeeeeff
........3454cddeeee~eeeeeeeeeeff
........3454cddeeee~~~eeeeeeeedd
........3454cddeee~~~eeeeeeeeedd
..........34cddeeeee444555555555
..........34cddeee44455555555555
............34dd3445555554444444
............34dd3445555554444444
............cd3445555544444444==
.............c34455555444444444=
..............345544345544345544
..............345544345544345544
..............345544345544345544
..............345544345544345544
..............345544345544345544
...............34554345544345544
...............34554434554345544
................3455434554345544
................3455434554434554
.................345534554434554
.................345534554434554
..................34534554434554
..................34534554434554
...................4455444434554
....................445544434554
.....................44554434554
......................4455434554
.......................445534554
........................44554444
.........................4455444
..........................445544
...........................44554
............................4444
.............................333
""")

HEAD_BACK = half("""
........................ddeeeeee
......................deeeeeffff
....................ddeeffffffee
...................deeefffffffee
..................deeeffffffffee
.................deeefffffffffee
................deeeffffffffeeee
...............deeefffffffeeeeee
..............ddeeffffeeeeeeeeee
..............deeefffeeeeeeeeeee
............34deeeeeeeeeeeeeeeee
............34deeeeeeeeeeeeeeeee
..........3454deeeeeeeeeddeeeeee
..........3454deeeeeeeeeeddeeeee
........34554445deeeeeeeeeddeeee
........34554445deeeeeeeeeeddeee
........3455444554deeeeeeeeeeeee
........3455444554deeeeeeeeeeeee
........34554445544445deeeeeeeee
........3455444554444554deeeeeee
......cd345544455444455444dddddd
......cd345544455444455444455ddd
......cd345544455444455444455444
......cd345544455444455444455444
........345544455444455444455444
........345544455444455444455444
........345543455443455443455443
........345543455443455443455443
..........5543455443455443455443
..........5543455443455443455443
..........444c44444c44444c44444c
..........33ccc333ccc333ccc333cc
.............cdddddddddddddddddd
..............cddddddddddddddddd
..............cddddddddddddddddd
..............cddddddddddddddddd
""")

# side maps are drawn 4 columns to the right of where they stand (v1's ox = -2)
HEAD_SIDE = grid("""
32|deeeeeeeed
30|deeeeeeeeeeeed
28|deeffffffffeeeeeed
27|deefffffffffeeeeeeed
26|deefffffffffffeeeeeeed
25|deeffffffffffffeeeeeeeed
24|deefffffffffffffeeeeeeeeed
24|deeffffffffffffeeeeeeeeeed
22|44deeffffffffeeeeeeeeeeeeeed
21|444deeffffffeeeeeeeeeeeeeeeeed
20|3454deefffeeeeeeeeeeeeeeeeeeeeed
20|3454deeeeeeeeeeeeebbbbbbbbeeeeed
18|34554433deeeeeeeeeeeeeeeeeeeeeeeed
18|34554433deeeeeeeeeeeeeeeeeeeeeeeed
18|3455544433deeeeeeeeeeeeeeeeeeeeeed
18|3455544433deeeeeeeeeeeeeeeeeeeeeed
18|345554444332deeeeeeeeee4445555555554
18|345554444332deeeeeeeee34455555555554
18|34555444433221deeeee345555443eeeee
18|34555444433221deeeee3445544eeeeeee
18|345554444332dcccceeeeeeeee####eeeeff
18|345554444332cdeedceeeeee##eeee##eeff
18|3455544433decdccdceeeeeeeeeeeeeeeeffff
18|3455544433decdccdceeeeeeeeeeeeeeeeffff
18|34554433ddeeecddceeeeeeeee~~~eeeeeeeeedd
18|34554433ddeeeecceeeeeeeeee~~~eeeeeeeeedd
20|34554433ddeeeeeeeeeeeeeeeeeeeeddddcc
20|34554433ddeeeeeeeeeeeeeeeeeeeeddd
20|3455443322deeeeeeeeeee4445555555555443
20|3455443322deeeeeeeee344555555555555443
22|34443322deeeeeee34554434554434554443
22|33433222deeeee3334554434554434554443
24|3322ddeeee555534554434554434554443
28|ddee34554434554434554434554443
28|cddd3455443455443455443455444
30|cd345544345544345544345544
31|435544434554434554434543
30|3455444434554434554434543
30|345544443455443455443443
30|345544443455443455443443
31|4355444434554345544343
32|345544434554345544343
32|34554443455443455443
32|34554443455443455443
33|4355443455443455443
34|34554345544345543
34|34554345544345543
34|3455434554434543
35|445533455434543
36|4455345543443
37|335345544443
38|3334554443
39|334554443
40|3455443
41|445543
42|4444
""", 60)

BODY_FRONT = half("""
....................BDEEEEEEEEEE
...................BDEEEEDDDDDDD
..................BDEEEDDDDDDDDD
..................BDEEDDDDDDDDDD
..................BDEEDDDDDDDDDD
..................BDEDDDDDDDDDDD
..................BDEDCBEDJKDDDD
..................BDEDCBEDDJKDDD
..................BDDDCBEDDDJKDD
..................BDDDCBEDDDDJKD
..................BDDDCBEDDDDDJJ
..................BDDDCBEDDDDDDJ
..................BDDDCBEDDDDDDD
..................BDDDCBEDDDDDDD
..................BDDDCBEDDDDDDD
..................BDDDCBEDDDDDDD
..................BDDDCBEDDDDDDD
..................BDDDCBEDDDDDDD
..................BDDDCBEDDDDDDD
..................BDDDCBEDDDDDDD
..................BDDDCBEDDDDDDD
..................BDDDCBEDDDDDDD
..............NPPPPPPPPPPPPPPPPP
..............NPQQQQQQQQQQQQQQQQ
..............NQQRRRQQQQQQQQQQQQ
..............NPQQQQQQQQQQQQQQQQ
..............NPPPPPPPPPPPPPPPPP
..............MNOOOOOOOOOOOOOOOO
............BCCCCCBECCCCCCCCJKCC
............BDDDDDBEDDDDDDDDJKDD
............BDDDDDBEDDDDDDDDJKDD
............BDDDDDBEDDDDDDDDJKDD
............BDDDDBEDDDDDDDDDJKDD
...........BCDDDDBEDDDDDDDDDJKDD
..........BDDDDDDBEDDDDCEDDDJKDD
..........BDDDDDDBEDDDDCEDDDJKDD
..........BDDDDDBEDDDDDCEDDDJKDD
..........BDDDDDBEDDDDDCEDDDJKDD
..........BDDDDDBEDDDDDCEDDDJKDD
..........BDDDDDBEDDDDDCEDDDJKDD
..........BDDDDBEDDDDDDCEDDDJKDD
.........BCDDDDBEDDDDDDCEDDDJKDD
........BDDDDDDBEDDDDDCEDDDDJKDD
........BDDDDDDBEDDDDDCEDDDDJKDD
........BDDDDDBEDDDDDDCEDDDDJKDD
........BDDDDDBEDDDDDDCEDDDDJKDD
........BDDDDDBEDDDDDDCDDDDDJKDD
........BDDDDDBEDDDDDDCDDDDDJKDD
........BDDDDBEDDDDDDDCDDDDDJKDD
........BCDDDBEDDDDDDDCDDDDDJKDD
........JKKKKKKKKKKKKKKKKKKKKKKK
........JKKKKKKKKKKKKKKKKKKKKKKK
........HJJJJJJJJJJJJJJJJJJJJJJJ
........HJJJJJJJJJJJJJJJJJJJJJJJ
""")

BODY_BACK = half("""
....................BDEEEEEEEEEE
...................BDEEEEEEEEEED
..................BDEEEEEEEEEDDD
..................BDEEEEEEDDDDDD
..................BDEEEEEDDDDDDD
..................BDEEEDDDDDDDDD
..................BDEEEEEDDDDCBE
..................BDEEEEDDDDDCBE
..................BDEDDDDDDDCBED
..................BDEDDDDDDDCBED
..................BDEDDDDDDDCBED
..................BDEDDDDDDDCBED
..................BDDCCDDDDDCBED
..................BDDDCCDDDDCBED
..................BDDDDCCDDDCBED
..................BDDDDDCCDDCBED
..................BDDDDDDCCDCBED
..................BDDDDDDDDDCBED
..................BDDDDDDDDDCBED
..................BDDDDDDDDDCBED
..................BDDDDDDDDDCBED
..................BDDDDDDDDDCBED
..............NPPPPPPPPPPPPPPPPP
..............NPQQQQQQQQQQQQQQQQ
..............NQQRRRQQQQQQQQQQQQ
..............NPQQQQQQQQQQQQQQQQ
..............NPPPPPPPPPPPPPPPPP
..............MNOOOOOOOOOOOOOOOO
............BCCCCCBECCCCCCCCCCCC
............BDDDDDBEDDDDDDDCDDDD
............BDDDDDBEDDDDDDDCDDDD
............BDDDDDBEDDDDDDDCDDDD
............BDDDDBEDDDDDDDDCDDDD
...........BCDDDDBEDDDDDDDDCDDDD
..........BDDDDDDBEDDDDCEDCDDDDD
..........BDDDDDDBEDDDDCEDCDDDDD
..........BDDDDDBEDDDDDCEDCDDDDD
..........BDDDDDBEDDDDDCEDCDDDDD
..........BDDDDDBEDDDDDCEDCDDDDD
..........BDDDDDBEDDDDDCEDCDDDDD
..........BDDDDBEDDDDDDCCCDDDDDD
.........BCDDDDBEDDDDDDCCCDDDDDD
........BDDDDDDBEDDDDDCECCDDDDDD
........BDDDDDDBEDDDDDCECCDDDDDD
........BDDDDDBEDDDDDDCECCDDDDDD
........BDDDDDBEDDDDDDCECCDDDDDD
........BDDDDDBEDDDDDDCCCDDDDDDD
........BDDDDDBEDDDDDDCCCDDDDDDD
........BDDDDBEDDDDDDDCCCDDDDDDD
........BCDDDBEDDDDDDDCCCDDDDDDD
........JKKKKKKKKKKKKKKKKKKKKKKK
........JKKKKKKKKKKKKKKKKKKKKKKK
........HJJJJJJJJJJJJJJJJJJJJJJJ
........HJJJJJJJJJJJJJJJJJJJJJJJ
""")

BODY_SIDE = grid("""
20|BEEEEEEECB
20|BEEEEEEECB
16|BEEEEEEEEEEEEECB
16|BEEEEEEEEEEEEEECB
12|BDEEEDDDDDDDDDDDDDDDCB
12|BDEEEDDDDDDDDDDDDDDDDCB
10|BDEEEDDDDDDCBEDDDDDDDDDDCB
10|BDEEEDDDDDDCBEDDDDDDDDDDCB
10|BDEEDDDDDDDCBEDDDDDDDDDDDDCB
10|BDEDDDDDDDDCBEDDDDDDDDDDDDCB
8|BDDDDDDDDDDDDCBEDDDDDDDDDDDDCB
8|BDDCCDDDDDDDDCBEDDDDDDDDDDDDDCB
8|BDDDCCDDDDDDCBEDDDDDDDDDDDDDDDCB
8|BDDDDCCDDDDDCBEDDDDDDDDDDDDDDDCB
9|BDDDDCCDDDCBEDDDDDDDDDDDDDDDDCB
9|BDDDDDCCDDCBEDDDDDDDDDDDDDDDDCB
9|BDDDDDDDDDCBEDDDDDDDDDDDDDDDDCB
9|BDDDDDDDDDCBEDDDDDDDDDDDDDDDDCB
9|BDDDDDDDDDCBEDDDDDDDDDDDDDDDDCB
9|BDDDDDDDDDCBEDDDDDDDDDDDDDDDDCB
9|BDDDDDDDDDCBEDDDDDDDDDDDDDDDDCB
9|BDDDDDDDDDCBEDDDDDDDDDDDDDDDDCB
10|NPPPPPPPPPPPPPPPPPPPPPPPPPPPON
10|NPQQQQQQQQQQQQQQQQQQQQQQQQQQPN
10|NQQRRRRQQQQQQQQQQQQQQQQQQQQQPN
10|NPQQQQQQQQQQQQQQQQQQQQQQQQQQPN
10|NPPPPPPPPPPPPPPPPPPPPPPPPPPPON
10|MNOOOOOOOOOOOOOOOOOOOOOOOOOONM
10|BCECCCCCBECCCCCCCCCCCCCCJKCCCB
10|BDEDDDDDBEDDDDDDDDDDDDDDJKDDCB
10|BDEDDDDDBEDDDDDDDDDDDDDDJKDDCB
10|BDEDDDDDBEDDDDDDDDDDDDDDJKDDCB
9|BDEDDDDDBEDDDDDDDDDDDDDDDJKDDCB
9|BDEDDDDDBEDDDDDDDDDDDDDDDJKDDCB
8|BDEDDDDDDBEDDDDDDDDDDDDDDDJKDDCB
8|BDEDDDDDDBEDDDDDDDDDDDDDDDJKDDCB
8|BDEDDDDDBEDDDDDDDDDCDDDDDDJKDDDCB
8|BDEDDDDDBEDDDDDDDDDCDDDDDDJKDDDCB
8|BDEDDDDDBEDDDDDDDDDCDDDDDDJKDDDDCB
8|BDEDDDDDBEDDDDDDDDDCDDDDDDJKDDDDCB
7|BDEDDDDDBEDDDDDDDDDDCDDDDDDJKDDDDCB
7|BDEDDDDDBEDDDDDDDDDDCDDDDDDJKDDDDCB
6|BDEDDDDDDBEDDDDDDDDDDCDDDDDDJKDDDDCB
6|BDEDDDDDDBEDDDDDDDDDCDDDDDDDJKDDDDCB
6|BDEDDDDDBEDDDDDDDDDDCDDDDDDDJKDDDDCB
6|BDEDDDDDBEDDDDDDDDDDCDDDDDDDJKDDDDCB
6|BDEDDDDDBEDDDDDDDDDDCDDDDDDDJKDDDDDCB
6|BDEDDDDDBEDDDDDDDDDDCDDDDDDDJKDDDDDCB
6|BDEDDDDBEDDDDDDDDDDDCDDDDDDDJKDDDDDDCB
6|BDEDDDDBEDDDDDDDDDDDCDDDDDDDJKDDDDDDCB
6|JKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKJ
6|JKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKJ
6|HJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJH
6|HJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJH
""", 48)

# the sash's knot and its two ends, at his right of the front (image left)
KNOT = grid("""
QRRQQP
QRRQQP
PQQQPN
PQQQPN
NPPPNN
NPPPNN
..NPPQ
..NPQP
..PQQP
..PQQN
..PQPN
..PPPN
..NPNM
..NNMM
""", 6)

# the free arm from the front: a wide sleeve, a silver cuff, the hand
ARM_DOWN = grid("""
....DEEEBA
...DEEEEBA
..DEEEEDBA
..DEEEEDBA
.DEEEEDDCB
.DEEEEDDCB
DEEEEDDDCB
DEEEEDDDCB
DEEEDDDDCB
DEEEDDDDCB
DEEEDDDDCB
DEEDDDDDCB
DEEDDDDDCB
DEDDDDDDCB
DDDDDDDCBA
CDDDDDDCBA
JKLLKKKKKJ
HJKKKKKJJH
..deeeed..
..deffed..
..cdeedc..
...cddc...
""", 10)

# the arm that holds the staff, from the front (the fist is its own map, on the staff)
ARM_HOLD = grid("""
10|DEEEBA
9|DEEEEBA
8|DEEEEDBA
8|DEEEEDBA
7|DEEEEDDCB
6|DEEEEDDDCB
6|DEEEDDDDCB
6|DEEEDDDDCB
5|DEEEDDDDCB
5|DEEDDDDDCB
4|DEEEDDDDCB
4|DEEDDDDDCB
4|DEDDDDDCBA
...DDDDDDDCBB
..DDDDDDDCBA
..CDDDDDCCBA
..JKLLKKKKKJ
..HJKKKKKJJH
""", 16)

FIST = grid("""
.deeeed.
deeffeed
deeeeeed
deedeedd
cdedeedc
.cddddc.
""", 8)

# the staff's head: a ring round a gold star with a gem (星環), a collar, the shaft below
STAFF_HEAD = grid("""
4|qrrp
..pqqqqppo
.pqqmmmmpoo
.pqmmmmmmpo
pqmmmwwmmmpo
pqmmmwwmmmpo
pqmhhxxhhmpo
pqmhhxwhhmpo
ppmmmhhmmmoo
.pmmmhhmmmo
.ppmmmmmmoo
..poommooo
4|ppoo
4|qqoo
5|qo
5|qo
""", 12)

FOOT_FRONT = grid("""
VWWWWWWV
VVWWWWVV
eedeedee
eedeedee
UUUUUUUU
TTTTTTTT
""", 8)

FOOT_BACK = grid("""
deVVVVed
deVVVVed
deeeeeed
ddeeeedd
UUUUUUUU
TTTTTTTT
""", 8)

FOOT_SIDE = grid("""
..deee......
..deee......
..deeeVWeeed
..deeeVWeedc
UUUUUUUUUUUU
TTTTTTTTTTTT
""", 12)

# side view: the sleeve reaching to the staff (the cuff and the fist are their own maps)
SLEEVE = grid("""
..EEEE
.EEEEEE
DEEEEEED
DDEEEEEEED
CCDDEEEEEEED
CCDDDDEEEEEED
.CCDDDDDEEEEED
..CCDDDDDDEEEEED
...BBCDDDDDDEEEEED
4|BBCDDDDDDDEEEEED
6|BBCDDDDDDDEEEEED
7|BBCDDDDDDDDEEEEEED
8|BBCDDDDDDDDDEEEEEEEEEE
10|BBCDDDDDDDDDDEEEEEEE
11|BBCDDDDDDDDDDDEEEEE
12|BBCDDDDDDDDDDDDDDD
13|BBCDDDDDDDDDDDDDD
14|BBCDDDDDDDDDDDDD
15|BBCDDDDDDDDDDDD
17|BBCDDDDDDDDDD
19|BBCCDDDDDDD
22|BBCCCDDD
26|BBCC
""", 30)

CUFF = grid("""
JLKJ
JLKJ
JLKJ
JKKJ
JKKJ
JKKJ
JKKJ
JKKJ
JKKJ
JKKJ
HJJH
HHHH
""", 4)

# side view: the free arm hanging (0), swung forward (F), swung back (B)
ARM_FREE_0 = grid("""
...DEEEED...
..DEEEEEDC..
.DEEEEEDDCB.
.DEEEEDDDCB.
.DEEEEDDDCB.
.DEEEEDDDCB.
.DEEEEDDDCB.
.DEEEDDDDCB.
.DEEEDDDDCB.
.DEEEDDDDCB.
.DEEEDDDDCB.
.DEEEDDDDCB.
.DEEDDDDDCB.
.DEEDDDDDCB.
.DEEDDDDDCB.
.DEEDDDDDCB.
.DEDDDDDDCB.
.DEDDDDDDCB.
.DDDDDDDDCB.
.CDDDDDDCCB.
.JKLLKKKKKJ.
.HJKKKKKJJH.
...deeeed...
...deffed...
...cdeedc...
....cddc....
""", 16)

ARM_FREE_F = grid("""
...DEEEED...
..DEEEEEDC..
.DEEEEEDDCB.
.DEEEEDDDCB.
.DEEEEDDDCB.
.DEEEEDDDCB.
.DEEEEDDDCB.
.DEEEDDDDCB.
.DEEEDDDDCB.
..DEEEDDDDCB
..DEEEDDDDCB
..DEEEDDDDCB
..DEEDDDDDCB
..DEEDDDDDCB
..DEEDDDDDCB
...DEEDDDDDCB
...DEDDDDDDCB
...DEDDDDDDCB
...DDDDDDDDCB
...CDDDDDDCCB
....JKLLKKKKKJ
....HJKKKKKJJH
......deeeed
......deffed
......cdeedc
.......cddc
""", 16)

ARM_FREE_B = grid("""
......DEEEED...
.....DEEEEEDC..
....DEEEEEDDCB.
....DEEEEDDDCB.
....DEEEEDDDCB.
....DEEEEDDDCB.
....DEEEEDDDCB.
....DEEEDDDDCB.
....DEEEDDDDCB.
...DEEEDDDDCB..
...DEEEDDDDCB..
...DEEEDDDDCB..
...DEEDDDDDCB..
...DEEDDDDDCB..
...DEEDDDDDCB..
..DEEDDDDDCB...
..DEDDDDDDCB...
..DEDDDDDDCB...
..DDDDDDDDCB...
..CDDDDDDCCB...
.JKLLKKKKKJ....
.HJKKKKKJJH....
...deeeed......
...deffed......
...cdeedc......
....cddc.......
""", 16)

for _m in (HEAD_FRONT, HEAD_BACK, BODY_FRONT, BODY_BACK):
    for _r in _m:
        assert len(_r) == 64, (len(_r), _r)


# ------------------------------------------------------------------ frames (v1's motion, x2)

from npc_pixmap import Fig, t_darker, t_far, t_mirror, v1_back_pose  # noqa: E402

BODY_TOP = 52
# breathing in lifts the chest by 2 (v1: 1 px). The cut is at body row 20 (y 72): rows 12..21 of every body
# map are one repeated row, so the 2 rows the chest leaves are filled by the same row. The sash (rows 22..27)
# is below the cut and keeps its shape.
CUT = 20
FREE = {0: (ARM_FREE_0, 0), 1: (ARM_FREE_F, 0), -1: (ARM_FREE_B, -3)}


def _sway(sway, row, back_only=False):
    """v1: the hem swings below y 44 (dx = round(sway * (y - 44) / 8)): here 1 texel from row 40, 2 from 44."""
    return sway * (0 if row < 40 else 1 if row < 44 else 2)


def _body(f, rows, x0, B, U, half_mirror, sway=0, upto=None):
    def shift(j, i, ch):
        r = j + CUT - 2
        if upto is not None:  # side view: only the back hem swings; it stops 1 texel inside the frame's column 0
            return (0 if i >= upto else max(-1, _sway(sway, r))), 0
        return _sway(sway, r), 0
    if upto is not None and sway:  # the side view's back hem: the 4 columns before the still part stay filled
        keep = [("." * (upto - 4) + r[upto - 4:upto]) if (CUT - 2 + k) >= 40 else "" for k, r in enumerate(rows[CUT - 2:])]
        f.stamp(keep, x0, BODY_TOP + CUT - 2 + B, LEG, part="body")
    f.stamp(rows[CUT - 2:], x0, BODY_TOP + CUT - 2 + B, LEG, part="body", half_mirror=half_mirror, shift=shift)
    f.stamp(rows[:CUT], x0, BODY_TOP + B + U, LEG, part="body", half_mirror=half_mirror)


def _staff(f, sx, top, tone=None):
    """The staff: its head, then a straight 2-texel shaft to the ground (knots fixed on the shaft)."""
    f.stamp(STAFF_HEAD, sx - 5, top, LEG, part="staff")  # v1: the far staff's head is not darkened
    knots = {27: "r", 41: "n", 55: "r", 68: "n", 82: "r", 95: "n"}
    for y in range(top + 16, 110):
        g = knots.get(y - top)
        f.stamp(["r" if g == "r" else "q"], sx, y, LEG, part="staff", tone=tone)
        f.stamp(["n" if g == "n" else "o"], sx + 1, y, LEG, part="staff", tone=tone)
    f.stamp(["po", "on"], sx, 110, LEG, part="staff", tone=tone)


def front(p, back=False):
    f = Fig(RAMPS)
    B, U = 2 * p.bob, -2 * p.breath
    foot = FOOT_BACK if back else FOOT_FRONT
    for (fwd, lift), x0, flip in ((p.near, 22, False), (p.far, 34, True)):
        f.stamp(foot, x0, 106 - 2 * lift, LEG, part="foot", flip=flip)
    _body(f, BODY_BACK if back else BODY_FRONT, 0, B, U, True, sway=p.sway)
    ay = 58 + B + U
    top = 20 + B + U + 2 * p.nod
    if not back:
        f.stamp(KNOT, 20, 74 + B, LEG, part="knot")
        f.stamp(ARM_DOWN, 42, ay - 2 * max(0, p.arm_far), LEG, part="arm", flip=True, tone=t_mirror)
        f.stamp(ARM_HOLD, 6, ay, LEG, part="arm")
        sx = max(6, 6 + 2 * (p.prop // 2))  # the head's ring stays inside the frame's left column
        _staff(f, sx, 4 + B + U)
        f.stamp(FIST, sx - 3, ay + 17, LEG, part="fist")
        f.stamp(HEAD_FRONT, 0, top, LEG, part="head", half_mirror=True)
    else:
        f.stamp(HEAD_BACK, 0, top, LEG, part="head", half_mirror=True)
        f.stamp(ARM_DOWN, 12, ay - 2 * max(0, p.arm_near), LEG, part="arm", tone=t_darker)
        f.stamp(ARM_HOLD, 42, ay, LEG, part="arm", flip=True, tone=t_mirror)
        sx = min(56, 56 + 2 * (p.prop // 2))
        _staff(f, sx, 4 + B + U)
        f.stamp(FIST, sx - 3, ay + 17, LEG, part="fist", flip=True)
    return f.finish()


def _foot_side(f, fwd, lift, tone):
    f.stamp(FOOT_SIDE, 20 + 2 * fwd, 106 - 2 * lift, LEG, part="foot", tone=tone)


def _reach(f, ay, dx, tone=None):
    """The sleeve from the shoulder to the staff. dx (0 / 2): the staff has crept forward: the forearm's
    last 8 columns (one flat band) are drawn again 2 further on, then the cuff."""
    f.stamp(SLEEVE, 18, ay - 4, LEG, part="arm", tone=tone)
    if dx:
        f.stamp([("." * 22 + r[22:]) for r in SLEEVE], 18 + dx, ay - 4, LEG, part="arm", tone=tone)
    f.stamp(CUFF, 48 + dx, ay + 8, LEG, part="arm", tone=tone)


def _free(f, ay, swing, tone=None):
    rows, ox = FREE[(swing > 0) - (swing < 0)]
    f.stamp(rows, 16 + ox, ay, LEG, part="arm", tone=tone)


def side(p, swap=False):
    f = Fig(RAMPS)
    B, U = 2 * p.bob, -2 * p.breath
    ay = 58 + B + U
    dx = 2 if p.prop > 0 else 0
    sx = 54 + dx
    _foot_side(f, p.far[0], p.far[1], t_far)
    if swap:  # facing left: the staff and its arm are on the far side
        _staff(f, sx, 4 + B + U, tone=t_far)
        _reach(f, ay, dx, tone=t_far)
        f.stamp(FIST, sx - 3, ay + 12, LEG, part="fist", tone=t_darker)
    else:
        _free(f, ay, p.arm_far, tone=t_far)
    _body(f, BODY_SIDE, -4, B, U, False, sway=-p.sway, upto=20)
    _foot_side(f, p.near[0], p.near[1], None)
    f.stamp(HEAD_SIDE, -4, 20 + B + U + 2 * p.nod, LEG, part="head")
    if swap:
        _free(f, ay, p.arm_near)
    else:
        _staff(f, sx, 4 + B + U)
        _reach(f, ay, dx)
        f.stamp(FIST, sx - 3, ay + 12, LEG, part="fist")
    return f.finish()


def frame(npc_v1, action, view, i):
    """The Fig of one frame and whether it is mirrored (left)."""
    p = npc_v1.pose(action, i)
    if view == "down":
        return front(p), False
    if view == "up":
        return front(v1_back_pose(p), back=True), False
    if view == "right":
        return side(p), False
    return side(p, swap=True), True
