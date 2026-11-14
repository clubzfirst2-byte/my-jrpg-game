"""v3 traveller (旅人), round 4: hand-drawn pixel maps at the v3 grid (npc_pixmap.py).

v1 (src/art-release/npc/npc.traveller.*, tools/npc_release/traveller.py, read only) is the reference for the
look: tall and thin, a little stooped; a wide-brimmed hat with a crimson band; a narrow sun-browned face,
narrow eyes (a line with a grey-green iris), a deep line on each cheek, grey hair tied in one tail with a
crimson cord, a white streak at the temple; a crimson scarf with one end on the chest; a dull-brown long
coat, open at the front, its hem worn; a grey jacket, a belt, dark trousers, boots; a leather pack with a
green bedroll on top; a long straight stick in the right hand with a water gourd on a cord.
New at 2x: the hat band's light and fold, the brim's two planes, the eye's lid and lower shade, the braid
of the tail, the coat's folds and pocket flap, the pack's flap, buckle and pocket, the bedroll's spiral
ends and straps, the gourd's stopper, neck and two bulbs, the boot's cuff.

Legend (6 tones each, 0 outline .. 5 highlight; tone 2 is v3's middle shade):
  0-5 hair   a-f skin   A-F coat   G-L jacket   M-R hat   S-X scarf   g-l bedroll   m-r pack leather
  s-x trousers   ! $ % ^ & ? boot   < > ( ) { } wood (the stick)   [ ] + - / : gourd   ; , ' ` _ @ gold
  inks: # eye line   z iris   y cheek line   = mouth
"""

from npc_pixmap import grid, half, legend

RAMPS = {  # v1's ramps (tools/npc_release/traveller.py RAMPS + tools/art_proto/pixel.py BASE_RAMPS)
    "skin": ["#5a2e1c", "#bc7c56", "#daa47a", "#ecbc92", "#f8d2aa"],
    "hair": ["#34343c", "#6e6e78", "#9c9ca4", "#c2c2c8", "#e6e6ea"],
    "hat": ["#16140e", "#363226", "#524c3a", "#6e6850", "#8c866a"],
    "coat": ["#241e16", "#4c4030", "#6a5a44", "#86745c", "#a49278"],
    "pack": ["#28140a", "#5e3420", "#824c2e", "#a06642", "#bc845c"],
    "jacket": ["#22242a", "#4a4e56", "#6a6e76", "#888c94", "#a8acb2"],
    "scarf": ["#2c0610", "#6a1424", "#962234", "#bc3848", "#de6a74"],
    "bedroll": ["#141c10", "#34442a", "#4e6240", "#6a7e58", "#8c9e78"],
    "gourd": ["#3a2608", "#86601e", "#b4862e", "#d4a84a", "#ecc878"],
    "trousers": ["#14141c", "#22222e", "#323244", "#44445a", "#585872"],
    "boot": ["#1e120a", "#3e2616", "#62402a", "#865c3c", "#a87a52"],
    "wood": ["#1e1008", "#4a2c16", "#6e4424", "#906038", "#b07e50"],
    "gold": ["#5a4018", "#a07a30", "#e8c060", "#f8dc88", "#fff4c8"],
}
INKS = {"#": "#2a1a14", "z": "#6e9a84", "y": "#83492c", "=": "#7a3a2a"}
EYE_INKS = {INKS["#"], INKS["z"]}
IRIS_INKS = {INKS["z"]}
LEG = legend([("012345", "hair"), ("abcdef", "skin"), ("ABCDEF", "coat"), ("GHIJKL", "jacket"),
              ("MNOPQR", "hat"), ("STUVWX", "scarf"), ("ghijkl", "bedroll"), ("mnopqr", "pack"),
              ("stuvwx", "trousers"), ("!$%^&?", "boot"), ("<>(){}", "wood"), ("[]+-/:", "gourd"),
              (";,'`_@", "gold")], INKS)

# ------------------------------------------------------------------ maps (hand drawn)

# the head maps start at the hat's crown; they stand 3 texels below the frame's top (v1: at the top row)
# and the crown is 3 texels lower than v1 x2, so the hat stays inside the frame when the chest rises.
HEAD_FRONT = half("""
......................NPQQQQQQQQ
.....................NPPQQQQRRQQ
....................NPPPQQQQRRQQ
....................NPPPQQQQQQQQ
....................NPPPPQQPPPPP
....................MSTVVVVVVVVV
....................MSTVVVVVVVVV
....................MSTUUUUUUUUU
....................MSTTTTTTTTTT
........NPPPQQQQQQQQQQQQPPPPPPPP
......NNPPPQQQQQQQQQQQQPPPPPPPPP
....MNNNNNNNNNNNNNPPPPPPPPPPPPPP
....MMNNNNNNNNNNNNNNPPPPPPPPPPPP
......MMMMMMMMMM1111bbbbbbbbbbbb
........MMMMMMMM1221bccccccccccc
................3455ddeeffffffff
................3455ddeeffffffff
................4555ddeeeeeeffff
................4555ddeeeeeeffff
................3454dd444444eeee
................3444dde33333eeee
................34dddd######eeee
................33dddde#zz#eeeee
................33ddeeddddddeeee
.................3ddeeffeeeeeeee
..................cddeyeffeeeeee
..................cddeyeffeeeeee
....................cdeyeeeeeeee
....................cdeyeeeeeeee
....................cdeyeeeeeeee
....................cdeeeeeeeeee
......................cddeee====
.......................cddeeeeee
........................cddddddd
.........................cdddddd
..........................cccccc
...........................ccccc
""")

HEAD_BACK = half("""
......................NPQQQQQQQQ
.....................NPPQQQQRRQQ
....................NPPPQQQQRRQQ
....................NPPPQQQQQQQQ
....................NPPPPQQPPPPP
....................MSTVVVVVVVVV
....................MSTVVVVVVVVV
....................MSTUUUUUUUUU
....................MSTTTTTTTTTT
........NPPPQQQQQQQQQQQQPPPPPPPP
......NNPPPQQQQQQQQQQQQPPPPPPPPP
....MNNNNNNNNNNNNNPPPPPPPPPPPPPP
....MMNNNNNNNNNNNNNNPPPPPPPPPPPP
......MMMMMMMMMM1111111111111111
........MMMMMMMM1111111111111111
..................44332211334421
..................34433221133421
..................33443322113321
..................13344332211321
..................11334433221121
..................31133443322121
..................33113344332221
..................33311334433221
....................331133443321
....................333113344321
......................3311334421
......................3331133421
........................33113321
........................33311321
........................bbbbbbbb
........................bbbbbbbb
........................bbbbbbbb
........................bbbbbbbb
..........................bbbbbb
..........................bbbbbb
""")

HEAD_SIDE = grid("""
22|NPQQQQQQQQQP
20|NPPQQQQQQQQQQQPN
20|NPPPQQQQQQQQQQPN
20|NPPPQQQQQQQQQPPN
20|NPPPPQQQPPPPPPPN
20|MSTVVVVVVVVVVVTS
20|MSTVVVVVVVVVVVTS
20|MSTUUUUUUUUUUUTS
20|MSTTTTTTTTTTTTSS
8|NPPPQQQQQQQQQQQQQQPPPPPPPPPPPPPPPP
7|NNPPPQQQQQQQQQQQQQQPPPPPPPPPPPPPPPPN
6|MNNNNNNNNNNNNNNNNNNPPPPPPPPPPPPPPPPPNN
6|MMNNNNNNNNNNNNNNNNNNNNPPPPPPPPPPPPPNNM
10|MMMMMM334455MMMMbbbbbbbbbbbbMMMMMM
12|MMMM334555MMMMbcccccccccccMMMM
16|44554433ddeeeeeeeeeeeeee
16|44554433ddeeeeeeeeeeeeee
16|34554433ddeeee34443eeeee
16|34554433ddeeeee333eeeeee
18|345443ddeedd#####eeeeeff
18|345443ddeedd#ezz#eeeeefff
18|344443ddeedddddddeeeeeffff
18|344433ddeeeeeeeeeeeeeeeffe
18|343433dddeyeeeeeeeeeeeeedd
18|343433dddeyeeeeeeeeeeeeed
20|3433ddeeeyeeeeeeeeddee
20|3433ddeeeyeeeeeeeedeee
22|33cdddeeyeeeeeee====
22|33cdddeeeyeeeeeeeee
24|cdddeeeeeeeeeeee
24|cdddeeeeeeeeeee
26|ccdddddddddd
27|ccdddddddd
28|ccccdd
28|cccccc
""", 48)

# shut eyes (the lid's line one row down, no iris): rows 21..22 of the front head, 19..20 of the side head
BLINK_FRONT = ["eeeeee", "######"]
BLINK_SIDE = ["eeeee", "#####"]

# the thin nose: a shadow down one side (the image's right of the centre line), the nostril's base
NOSE = grid("""
..c.
..c.
..c.
..c.
..c.
..c.
ccc.
ccc.
""", 4)

# the mouth's right corner a little up (calm, a little secretive)
MOUTH_CORNER = grid("""
.=
=.
""", 2)

BODY_FRONT = half("""
......................STVVVVVVVV
....................STTVVVVVVVVV
..................STVVWWWWVVVVVV
................STTVVWWWWWVVVVVV
..............ABBDDDSTVVVVVVVVVV
.............ABBDDDESTVVVVVVVVVV
............ABBDDDEESTTTTTTTTTTT
............ABBDDDEESSTTTTTTTTTT
............ABBDDDEEmnnoBBDDGHHH
............ABBDDDEEmnnoBBDDGHHH
............ABBDDDEEmnnoBBDDGHJJ
............ABBDDDEEmnnoBBDDGHJJ
............ABBDDDEEmnnoBBDDGHJJ
............ABBDDDEEmnnoBBDDGHJJ
............ABBDDDEEmnnoBBDDGHJJ
............ABBDDDEEmnnoBBDDGHJJ
............ABBDDDEEmnnoBBBBGHJJ
............ABBDDDEEmnnoBBBBGHJJ
............ABBDDDEEmnnoBBBBGHJJ
............ABBDDDEEmnnoBBBBGHJJ
............ABBDDDEEmnnoDDBBGHJJ
............ABBDDDEEmnnoDDBBGHJJ
............ABBDDDEEmnnoDDBBGHJJ
............ABBDDDEEmnnoDDBBGHJJ
............ABBDDDEEEEDDDDBBGHJJ
............ABBDDDEEEEDDDDBBGHJJ
............ABBDDDEEEEDDDDBBGHHH
............ABBDDDEEEEDDDDBBGHHH
............ABBDDDEEDDDDDDBBnnpp
............ABBDDDEEDDDDDDBBnnpp
............ABBDDDDEBDDDDDBBGHHH
............ABBDDDDEBDDDDDBBGHHH
............ABBDDDDEBDDDDDBBGHJJ
............ABBDDDDEBDDDDDBBGHJJ
............ABBDDDDEBDDDDDBBGHJJ
............ABBDDDDEBDDDDDBBGHJJ
............ABBDDDDEBDDDCDBBGHHH
............ABBDDDEBDDDDCDBBGHHH
............ABBDDDEBDDDDCDBBsuvv
............ABBDEEEBEDDDCDBBsuvv
............ABBBBBBBBBDDCDBBsuvv
............ABBBDDEBDBDDCDBBsuvv
............ABBDDDEBDDDDCDBBsuvv
............ABBDDDEBDDDDCDBBsuvv
............ABBDDEBDDDDDCDBBsuvv
............ABBDDEBDDDDDCDBBsuvv
..........ABBDDDEEBDDDDDCDBBsuvv
..........ABBDDDEEBDDDDCDDBBsuvv
..........ABBDDDEEBDDDDCDDBBsuvv
..........ABBDDDEEBDDDDCDDBBsuvv
..........ABBDDDEEBDEBDCDDBBsuvv
..........ABBDDDEBDDEBDCDDBBsuvv
..........ABBDEBEBDDEBDCDDBBsuvv
..........ABBDEBEBDDEBDCDDBBsuvv
..........ABBDEBEBDDEBDCDDBBsuvv
..........ABBDEBEBDDEBDCDDBBsuvv
..........ABBDEBEBDDEBDCDDBBsuvv
..........ABBDEBEBDDEBDCDDBBsuvv
..........AABBBBAABBBBAABBBB..sv
..........AA..AAAA..AAAA..AA..ss
""")

BODY_BACK = half("""
......................STVVVVVVVV
....................STTVVVVVVVVV
..............ABBDDDEEEEEEEEEEEE
.............ABBDDDEEEEEEEDDDDDD
............ABBDDDEEDDDDDDDDDDDD
............ABBDDDEEDDDDDDDDDDDD
............ABBDDDEEDDDDDDDDDDDD
............ABBDDDEEDDDDDDDDDDDD
............ABBDDDEEDDDDDDDDDDDD
............ABBDDDEEDDDDDDDDDDDD
............ABBDDDEEDDDDDDDDDDDD
............ABBDDDEEDDDDDDDDDDDD
............ABBDDDEEDDDDDDDDDDDD
............ABBDDDEEDDDDDDDDDDDD
............ABBDDDEEDDDDDDDDDDDD
............ABBDDDEEDDDDDDDDDDDD
............ABBDDDEEDDDDDDDDDDDD
............ABBDDDEEDDDDDDDDDDDD
............ABBDDDEEDDDDDDDDDDDD
............ABBDDDEEDDDDDDDDDDDD
............ABBDDDEEDDDDDDDDDDDD
............ABBDDDEEDDDDDDDDDDDD
............ABBDDDEEDDDDDDDDDDDD
............ABBDDDEEDDDDDDDDDDDD
............ABBDDDEEDDDDDDDDDDDD
............ABBDDDEEDDDDDDDDDDDD
............ABBDDDEEDDDDDDDDDDDD
............ABBDDDEEDDDDDDDDDDDD
............ABBDDDEEDDDDDDDDDDDD
............ABBDDDEEDDDDDDDDDDDD
............ABBDDDDEBDDDDDDCDDBD
............ABBDDDDEBDDDDDDCDDBD
............ABBDDDDEBDDDDDDCDDBD
............ABBDDDDEBDDDDDDCDDBD
............ABBDDDDEBDDDDDDCDDBD
............ABBDDDDEBDDDDDDCDDBD
............ABBDDDDEBDDDDDDCBDDD
............ABBDDDEBDDDDDDDCBDDD
............ABBDDDEBDDDDDDDCBDDD
............ABBDDDEBDDDDDDCDBDDD
............ABBDDDEBDDDDDDCDBDDD
............ABBDDDEBDDDDDDCDBDDD
............ABBDDDEBDDDDDDCDBDDD
............ABBDDDEBDDDDDDCDBDDD
............ABBDDEBDDDDDDDCDBDDD
............ABBDDEBDDDDDDDCDBDDD
..........ABBDDDEEBDDDDDDDCDBDDD
..........ABBDDDEEBDDDDDDDCDBDDD
..........ABBDDDEEBDDDDDDCDDBDDD
..........ABBDDDEEBDDDDDDCDDBDDD
..........ABBDDDEEBDEBDDDCBDBDDD
..........ABBDDDEBDDEBDDDCBDBDDD
..........ABBDEBEBDDEBDDDCBDBDDD
..........ABBDEBEBDDEBDDDCBDBDDD
..........ABBDEBEBDDEBDDDCBDBDDD
..........ABBDEBEBDDEBDDDCBDBDDD
..........ABBDEBEBDDEBDDDCBDBDDD
..........ABBDEBEBDDEBDDDEBDBDDD
..........AABBBBAABBBBAABBBBAABB
..........AA..AAAA..AAAA..AAAA..
""")

BODY_SIDE = grid("""
30|STVVVVVVVV
28|STVVVVVVVVVV
26|STTVVWWWVVVVVVVT
24|STTVVWWWWVVVVVVVVT
22|ABBDDDEESTVVVVVVVVTT
21|ABBDDDEEESTTVVVVVVVTT
20|ABBDDDEEEEEEEEDDDDGHHJJK
20|ABBDDDEEEEEEEEDDDDGHHJJK
20|ABBDDDEEEEEEDDDDDDGHHJJK
20|ABBDDDEEEEEEDDDDDDGHHJJK
20|ABBDDDEEEEDDDDDDDDGHHJJK
20|ABBDDDEEEEDDDDDDDDGHHJJK
20|ABBDDDEEDDDDDDDDDDGHHJJK
20|ABBDDDEEDDDDDDDDDDGHHJJK
20|ABBDDDEEDDDDDDDDDDGHHJJK
20|ABBDDDEEDDDDDDDDDDGHHJJK
20|ABBDDDEEDDDDDDDDDDGHHJJK
20|ABBDDDEEDDDDDDDDDDGHHJJK
20|ABBDDDEEDDDDDDDDDDGHHJJK
20|ABBDDDEEDDDDDDDDDDGHHJJK
20|ABBDDDEEDDDDDDDDDDGHHJJK
20|ABBDDDEEDDDDDDDDDDGHHJJK
20|ABBDDDEEDDDDDDDDDDGHHJJK
20|ABBDDDEEDDDDDDDDDDGHHJJK
20|ABBDDDEEDDDDDDDDDDnnppqq
20|ABBDDDEEDDDDDDDDDDnnppqq
20|ABBDDDEEDDDDDDDDDDGHHJJK
20|ABBDDDEEDDDDDDDDDDGHHJJK
20|ABBDDDEEDDDDDDDDDDGHHJJK
20|ABBDDDEEDDDDDDDDDDGHHJJK
20|ABBDDDEEBDDDDDDDDDGHHJJK
20|ABBDDDEEBDDDDDDDDDGHHJJK
20|ABBDDDEEBDDDDDDDDDGHHJJK
20|ABBDDDEEBDDDDDDDDDGHHJJK
20|ABBDDDEEBDDDDDDDDDGHHJJKAA
20|ABBDDDEBDDDDDDDDDDGHHJJKAA
20|ABBDDDEBDDDDDDDCDDDDBBDDDDBB
20|ABBDDDEBDDDDDDDCDDDDBBDDDDBB
20|ABBDDDEBDDDDDDDCDDDDBBDDDDBB
20|ABBDDDEBDDDDDDDCDDDDBBDDDDBB
18|ABBDDDEEEBDDDDDDDCDDDDBBDDDDBB
18|ABBDDDEEEBDDDDDDDCDDDDBBDDDDBB
18|ABBDDDEEEBDDDDDDDCDDDDBBDDDDBB
18|ABBDDDEEEBDDDDDDDCDDDDBBDDDDBB
18|ABBDDDEEBDDDDDDDDCDDDDBBDDDDDDBB
18|ABBDDDEEBDDDDDDDDCDDDDBBDDDDDDBB
18|ABBDDDEEBDDDDDDDDCDDDDBBDDDDDDBB
18|ABBDDDEEBDDDDDDDCDDDDDBBDDDDDDBB
18|ABBDDDEEBDDDDDDDCDDDDDBBDDDDDDBB
18|ABBDDDEEBDDDDDDDCDDDDDBBDDDDDDBB
18|ABBDDDEEBDDDDDEBCDDDDDBBDDDDDDBB
18|ABBDDDEEBDDDDDEBCDDDDDBBDDEBDDBB
18|ABBDEBEEBDDDDDEBCDDDDDBBDDEBDDDDBB
18|ABBDEBEBDDDDDDEBCDDDDDBBDDEBDDDDBB
16|ABBDDDEBEBDDDDDDEBCDDDDDBBDDEBDDDDBB
16|ABBDDDEBEBDDDDDDEBCDDDDDBBDDEBDDDDBB
16|ABBDDDEBEBDDDDDDEBCDDDDDBBDDEBDDDDBB
16|ABBDDDEBEBDDDDDDEBCDDDDDBBDDEBDDDDBB
16|AABBBBAABBBBAABBBBAABBBBAABBBBAABBAA
16|AA..AAAA..AAAA..AAAA..AAAA..AAAA..AA
""", 54)

# the scarf's end on the chest (front) and its fringe
SCARF_END = grid("""
VWWV
VWWV
VWWV
VWWV
VWVV
VWVV
VWWV
VWWV
VWWV
VWVV
VWVV
VWWV
VWWV
VWWV
VWVV
VWVV
TVVT
TVVT
TVVT
TVTT
TTTTT
T.TT.
TT...
""", 6)

SCARF_END_SIDE = grid("""
VWWV
VWWV
VWWV
VWVV
VWVV
VWWV
VWWV
VWWV
VWVV
VWVV
VWWV
VWWV
VWWV
VWVV
TVVT
TVVT
TVTT
TTTT
TT..
""", 4)

# the grey tail down the back, tied with a crimson cord (back view); its base at the side
TAIL_BACK = grid("""
3443
3443
TVVT
STTS
3443
3442
2332
2332
3442
3442
2332
2332
3442
3442
2332
2332
3442
3442
2332
2322
.32
.22
""", 4)

TAIL_SIDE = grid("""
TVVT
STTS
3443
3442
2332
2332
3442
3442
2332
2322
.32
.22
""", 4)

# front view: the bedroll's ends above the shoulders (a ring round a dark middle), image left / right
ROLL_END = grid("""
.kkkk
kkjjjh
kjghjh
kjhhjh
jjjjih
.iiii
""", 6)

# back view: the bedroll across the pack's top, its straps, the round ends
ROLL_BACK = grid("""
..ijjkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkjji
.ijkkjjjjjjjnnjjjjjjjjjjjjjjjjjjjjjjjjnnjjjjjjjjjjih
ijjjhjjjjjjjppjjjjjjjjjjjjjjjjjjjjjjjjppjjjjjjjjhjih
ijjhhjjjjjjjppjjjjjjjjjjjjjjjjjjjjjjjjppjjjjjjjhhjih
ijjhijiiiiiippiiiiiiiiiiiiiiiiiiiiiiiippiiiiiihijih
ijjjjiiiiiiippiiiiiiiiiiiiiiiiiiiiiiiippiiiiiijjjih
.iiiiihhhhhhnnhhhhhhhhhhhhhhhhhhhhhhhhnnhhhhhhiiiih
..hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh
""", 52)

# back view: the pack under the roll (the flap, the buckle, the pocket)
PACK_BACK = grid("""
pqqqqqqqqqqqqqqqqqqqqqqqqqqo
pqqqqqqqqqqqqqqqqqqqqqqqqqpo
ppoooooooooooooooooooooooono
ppoooooooooooooooooooooooono
pppppppppppppppppppppppppono
pqqppppppppppppppppppppppono
pqppppppppppp`,pppppppppppno
pppppppppppp``,,ppppppppppno
pppppppppppp,,``ppppppppppno
pppppppppppppnnpppppppppppno
ponnnnnnnnnnnnnnnnnnnnnnnnno
poooooooooooooooooooooooooon
poooooooooooooooooooooooooon
poooooooooooooooooooooooooon
pooopppppppppppppppppppoooon
pooopqqpppppppppppppppnoooon
pooopqppppppppppppppppnoooon
pooopppppppppppppppppponoooo
pooopppppppppppppppppponooon
pooopppppppppppppppppponooon
pooopppppppppppppppppponooon
pooopppppppppppppppppponooon
pooopppppppppppppppppponooon
pooopppppppppppppppppponooon
pooopoooooooooooooooooonooon
pooonnnnnnnnnnnnnnnnnnnnooon
poooooooooooooooooooooooooon
onnnnnnnnnnnnnnnnnnnnnnnnnnn
""", 28)

# side view: the pack on the back (a pocket and its buckle), the roll's end as a spiral, the strap
PACK_SIDE = grid("""
4|jkkkkj
..jkkjjjjjih
.jjjjhhhhjjih
jjjhhjjjjhjiih
kjhjjhhhjhjiih
kjhjhjjhjhjiin
jjhjhhhhjhjinn
jjhjjjjjjjiinn
ijjhhhhhjjihnn
.ijjjjjjjiihn
pqqqqqqqqqqqo
pqppppppppppo
poooooooooopo
noooooooooopo
nooppppppoopo
noopqqpppnopo
noopqp``pnopo
noopppp`pnopo
noopppppnnopo
noopppppnoopo
noonnnnnnoopo
noooooooooopo
noooooooooopo
noooooooooopo
noooooooooopo
noooooooooopo
noooooooooopo
noooooooooopo
noooooooooopo
noooooooooopo
noooooooooopo
noooooooooopo
noooooooooopo
noooooooooopo
noooooooooono
nnnnnnnnnnnnn
""", 14)

# the water gourd: a stopper, the neck, a small bulb on a large one
GOURD = grid("""
...pp
...pp
...]+
...-+
..-/---
..-/---
.-/:----
.-/:----
-//:-----
-//:-----
-/------+
--------+
.------+
.-----++
..++++]
...]]]
""", 9)

# front view: the arm that holds the stick (upper arm; the forearm and cuff move with the hand)
ARM_UP = grid("""
..BDEEDB
.BDEEEDB
.BDEEDDB
BDEEEDDB
BDEEDDDB
BDEEDDDB
BDEEDDB.
BDEDDDB.
BDEDDDB.
BDEDDDB.
BDEDDDB.
BDDDDDB.
""", 8)

FOREARM = grid("""
.BDEDDB
.BDEDDB
BDEEDDB
BDEEDDB
BDEDDDB
BDEDDDB
BDDDDDB
BBBBBBB
""", 7)

FIST = grid("""
.deeed
deffed
deeeed
deeede
cddddc
.cccc
""", 6)

# front view: the free arm (it hangs; the lower part and the hand rise when it swings forward)
ARM_FREE_UP = grid("""
BDEEDB..
BDEEEDB.
BDEEDDB.
BDEEEDDB
.BDEEDDB
.BDEEDDB
.BDEEDDB
.BDEDDDB
.BDEDDDB
.BDEDDDB
.BDEDDDB
.BDEDDDB
.BDEDDDB
.BDDDDDB
""", 8)

ARM_FREE_LOW = grid("""
BDEDDDB
BDEDDDB
BDEDDDB
BDEDDDB
BDEDDDB
BDDDDDB
BDDDDDB
BBBBBBB
.deeed.
.deffed
.deeeed
.cdeddc
..cddc.
...cc..
""", 7)

# side view: the upper arm, the forearm to the stick (anchored at the hand), the hand on the stick
ARM_UP_SIDE = grid("""
..EEEE
BDEEEEDB
BDEEEDDB
BDEEEDDDB
.BDEEDDDB
.BDEEEDDB
..BDEEDDDB
..BDEEDDDB
..BDEEDDDB
...BDDDDDB
...BBDDDB
""", 10)

FOREARM_SIDE = grid("""
BDEE
BDEEEE
BDEEEEEE
.BBDEEEEEB
..BBDDEEEB
...BBDDDDB
5|BBDDB
7|BBB
""", 10)

HAND_SIDE = grid("""
.deeed
deffed
deeeed
dededc
.cddc.
""", 6)

# side view: the free arm hanging (0), swung forward (F), swung back (B)
ARM_SIDE_0 = grid("""
...EEEE
.BDEEEEDB
.BDEEEDDB
.BDEEEDDB
.BDEEDDDB
.BDEEDDDB
.BDEEDDDB
.BDEEDDDB
.BDEEDDDB
.BDEDDDDB
.BDEDDDDB
.BDEDDDDB
.BDEDDDDB
.BDEDDDDB
..BDEDDDB
..BDEDDDB
..BDEDDDB
..BDEDDDB
..BDEDDDB
..BDEDDDB
..BDDDDDB
..BDDDDDB
..BBBBBBB
...deeed
...deffed
...deeeed
...cdeddc
4|cddc
""", 16)

ARM_SIDE_F = grid("""
...EEEE
.BDEEEEDB
.BDEEEDDB
.BDEEEDDB
.BDEEDDDB
.BDEEDDDB
.BDEEDDDB
..BDEEDDDB
..BDEEDDDB
..BDEDDDDB
...BDEDDDDB
...BDEDDDDB
...BDEDDDDB
4|BDEDDDDB
4|BDEDDDB
4|BDEDDDB
5|BDEDDDB
5|BDEDDDB
5|BDEDDDB
6|BDDDDDB
6|BDDDDDB
6|BDDDDDB
6|BBBBBBB
7|deeed
7|deffed
7|deeeed
7|cdeddc
8|cddc
""", 16)

ARM_SIDE_B = grid("""
7|EEEE
5|BDEEEEDB
5|BDEEEDDB
5|BDEEEDDB
5|BDEEDDDB
5|BDEEDDDB
5|BDEEDDDB
4|BDEEDDDB
4|BDEEDDDB
4|BDEDDDDB
...BDEDDDDB
...BDEDDDDB
...BDEDDDDB
..BDEDDDDB
..BDEDDDB
..BDEDDDB
.BDEDDDB
.BDEDDDB
.BDEDDDB
BDDDDDB
BDDDDDB
BDDDDDB
BBBBBBB
.deeed
.deffed
.deeeed
.cdeddc
..cddc
""", 16)

# his legs from the front (the right leg, image left; the other is its mirror): narrow trousers, worn boots
LEG_FRONT = grid("""
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tttttt
..$$$$$$
..%^^^%$
..%^^^%$
..%^^^%$
..%^^^%$
..%^^^%$
%%^^^^%$
%^^^^^%$
$$$$$$$$
$$$$$$$!
""", 8)

LEG_BACK = grid("""
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tuvvut
..tttttt
..$$$$$$
..%^^^%$
..%^^^%$
..%^^^%$
..%^^^%$
..%^^^%$
%%^^^^%$
%^^^^^%$
$$$$$$$$
$$$$$$$!
""", 8)

# side view (facing right): (forward, lift) of v1's gait; the coat hides the thigh
LEG_SIDE_p0_0 = grid("""
13|uvvvvt
13|uvvvvt
13|uvvvvt
13|uvvvvt
13|uvvvvt
13|uvvvvt
13|uvvvvt
13|uvvvvt
13|uvvvvt
13|uvvvvt
13|uvvvvt
13|uvvvvt
13|uvvvvt
13|uvvvvt
13|uvvvvt
13|uvvvvt
12|$$$$$$$$
12|%^^^^^%$
12|%^^^^^%$
12|%^^^^^%$
12|%^^^^^%$
12|%^^^^^%$
12|%^^^^^^^%$
12|%^^^^^^^^^%
12|%^^^^^^^^^^^%
12|%^^^^^^^^^^^%$
12|%^^^^^^^^^^^%$
12|$$$$$$$$$$$$$$
""", 32)

LEG_SIDE_p3_0 = grid("""
13|uvvvvt
13|uvvvvt
13|uvvvvt
14|uvvvvt
14|uvvvvt
14|uvvvvt
15|uvvvvt
15|uvvvvt
15|uvvvvt
16|uvvvvt
16|uvvvvt
17|uvvvvt
17|uvvvvt
18|uvvvvt
18|uvvvvt
19|uvvvvt
18|$$$$$$$$
18|%^^^^^%$
18|%^^^^^%$
18|%^^^^^%$
18|%^^^^^%$
18|%^^^^^%$
18|%^^^^^^^%$
18|%^^^^^^^^^%
18|%^^^^^^^^^^^%
18|%^^^^^^^^^^^%$
18|%^^^^^^^^^^^%$
18|$$$$$$$$$$$$$$
""", 32)

LEG_SIDE_m3_0 = grid("""
13|uvvvvt
13|uvvvvt
13|uvvvvt
12|uvvvvt
12|uvvvvt
12|uvvvvt
11|uvvvvt
11|uvvvvt
11|uvvvvt
10|uvvvvt
10|uvvvvt
9|uvvvvt
9|uvvvvt
8|uvvvvt
8|uvvvvt
7|uvvvvt
6|$$$$$$$$
6|%^^^^^%$
6|%^^^^^%$
6|%^^^^^%$
6|%^^^^^%$
6|%^^^^^%$
6|%^^^^^^^%$
6|%^^^^^^^^^%
6|%^^^^^^^^^^^%
6|%^^^^^^^^^^^%$
6|%^^^^^^^^^^^%$
6|$$$$$$$$$$$$$$
""", 32)

LEG_SIDE_p3_1 = grid("""
13|uvvvvt
13|uvvvvt
14|uvvvvt
14|uvvvvt
15|uvvvvt
15|uvvvvt
16|uvvvvt
16|uvvvvt
17|uvvvvt
17|uvvvvt
18|uvvvvt
18|uvvvvt
19|uvvvvt
19|uvvvvt
19|uvvvvt
18|$$$$$$$$
18|%^^^^^%$
18|%^^^^^%$
18|%^^^^^%$
18|%^^^^^%$
18|%^^^^^%$
18|%^^^^^^^%$
18|%^^^^^^^^^%
18|%^^^^^^^^^^^%
18|%^^^^^^^^^^%$
18|$$$$$$$$$$$$
""", 32)

LEG_SIDE_m3_1 = grid("""
13|uvvvvt
13|uvvvvt
12|uvvvvt
12|uvvvvt
11|uvvvvt
11|uvvvvt
10|uvvvvt
10|uvvvvt
9|uvvvvt
9|uvvvvt
8|uvvvvt
8|uvvvvt
7|uvvvvt
7|uvvvvt
7|uvvvvt
6|$$$$$$$$
6|%^^^^^%$
6|%^^^^^%$
6|%^^^^^%$
6|%^^^^^%$
6|%^^^^^%$
6|%^^^^^^^%$
6|%^^^^^^^^^%
6|%^^^^^^^^^^^%
6|%^^^^^^^^^^%$
6|$$$$$$$$$$$$
""", 32)

LEG_SIDE_p0_2 = grid("""
13|uvvvvt
14|uvvvvt
14|uvvvvt
15|uvvvvt
15|uvvvvt
16|uvvvvt
16|uvvvvt
17|uvvvvt
17|uvvvvt
16|uvvvvt
16|uvvvvt
15|uvvvvt
14|uvvvvt
13|$$$$$$$$
13|%^^^^^%$
13|%^^^^^%$
13|%^^^^^%$
13|%^^^^^%$
13|%^^^^^%$
13|%^^^^^^^%
14|%^^^^^^^^%
15|%^^^^^^^%$
16|$$$$$$$$$
""", 32)

for _m in (HEAD_FRONT, HEAD_BACK, BODY_FRONT, BODY_BACK):
    for _r in _m:
        assert len(_r) == 64, (len(_r), _r)


# ------------------------------------------------------------------ frames (v1's motion, x2)

from npc_pixmap import Fig, t_darker, t_far, t_mirror, v1_back_pose  # noqa: E402

SIDE_LEGS = {(0, 0): LEG_SIDE_p0_0, (3, 0): LEG_SIDE_p3_0, (-3, 0): LEG_SIDE_m3_0, (3, 1): LEG_SIDE_p3_1,
             (-3, 1): LEG_SIDE_m3_1, (0, 2): LEG_SIDE_p0_2}
HANG = {0: (ARM_SIDE_0, 0), 1: (ARM_SIDE_F, 0), -1: (ARM_SIDE_B, -4)}
HEAD_Y = 3
BODY_TOP = 38
# breathing in lifts the chest by 2 (v1: 1 px). The cut is at body row 34 (y 72), inside 4 repeated rows
# below the belt (the belt rises with the chest, as in v1).
CUT = 34


def _sw(sway, row):
    """v1: the coat's outer hem swings below y 40 (dx = round(sway * (y - 40) / 8)): 1 texel from body
    row 46, 2 from row 52."""
    return sway * (0 if row < 46 else 1 if row < 52 else 2)


def _cols(rows, a, b):
    return [("." * a + r[a:b]) for r in rows]


def _body(f, rows, B, U, half_mirror, sway, outer):
    """outer: [(a, b)] column ranges that swing with the hem; the 4 columns next to the still part are
    drawn first where they stand (no hole when the hem swings away), then the swinging parts, then the
    still part on top."""
    low = rows[CUT - 2:]
    y0 = BODY_TOP + CUT - 2 + B
    w = len(rows[0])
    if sway:
        for a, b in outer:
            k0, k1 = (b - 4, b) if a == 0 else (a, a + 4)
            f.stamp(_cols(low, k0, k1), 0, y0, LEG, part="body", half_mirror=half_mirror)
        for a, b in outer:
            f.stamp(_cols(low, a, b), 0, y0, LEG, part="body", half_mirror=half_mirror,
                    shift=lambda j, i, ch: (_sw(sway, j + CUT - 2), 0))
    still = low
    if sway:
        still = [list(r) for r in low]
        for a, b in outer:
            for k, r in enumerate(still):
                if _sw(sway, k + CUT - 2):
                    r[a:b] = "." * (b - a)
        still = ["".join(r) for r in still]
    f.stamp(still, 0, y0, LEG, part="body", half_mirror=half_mirror)
    f.stamp(rows[:CUT], 0, BODY_TOP + B + U, LEG, part="body", half_mirror=half_mirror)


def _stick(f, x, top, ground, tip=None, tone=None):
    """The stick: a straight 2-texel line from its knob to its foot (x at the top, tip at the foot when it
    leans: v1's lean_x), knots fixed on the wood."""
    tip = x if tip is None else tip
    knots = {9: "{", 23: ">", 38: "{", 52: ">", 67: "{", 81: ">", 96: "{"}
    f.stamp(["{(", "{("], x, top - 2, LEG, part="stick", tone=tone)
    for y in range(top, ground + 1):
        sx = x + round((tip - x) * (y - top) / max(1, ground - top))
        g = knots.get(y - top)
        f.stamp(["}" if g == "{" else "{"], sx, y, LEG, part="stick", tone=tone)
        f.stamp([">" if g == ">" else "("], sx + 1, y, LEG, part="stick", tone=tone)


def _lean(x, top, ground, tip, y):
    return x + round((tip - x) * (y - top) / max(1, ground - top))


def _gourd(f, sx, y, side, tone=None):
    """The gourd on its cord: side -1 hangs to the image's left of the stick, +1 to its right."""
    gx = sx - 9 if side < 0 else sx + 2
    f.stamp(["nn"], sx - 1 if side < 0 else sx + 1, y, LEG, part="gourd", tone=tone)
    f.stamp(GOURD, gx, y + 1, LEG, part="gourd", flip=side > 0, tone=tone)


def front(p, back=False, blink=False, walking=False):
    f = Fig(RAMPS)
    B, U = 2 * p.bob, -2 * p.breath
    T = B + U
    legmap = LEG_BACK if back else LEG_FRONT
    for (fwd, lift), x0, flip in ((p.near, 22, False), (p.far, 34, True)):
        yv1 = min(55, 55 - lift + (1 if fwd > 1 else 0))
        bottom = 111 - 2 * (55 - yv1)
        f.stamp(legmap, x0, bottom - len(legmap) + 1, LEG, part="leg", flip=flip,
                tone=t_mirror if flip else None)
    if not back:  # the roll's ends above the shoulders, the dark roll behind the neck
        f.stamp(["hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh"] * 6, 14, 28 + T, LEG, part="roll")
        f.stamp(ROLL_END, 10, 28 + T, LEG, part="roll")
        f.stamp(ROLL_END, 48, 28 + T, LEG, part="roll", flip=True, tone=t_mirror)
    _body(f, BODY_BACK if back else BODY_FRONT, B, U, True, p.sway, [(0, 16), (48, 64)])
    lift = 2 * p.staff[2]
    grip = 2 if (p.prop > 0 and not walking) else 0
    hand_y = 66 + T - lift - grip
    sx = 10 if not back else 52  # v1 x2 is 8 / 54: the gourd beside it stays inside the frame's side column
    free_up = 2 * max(0, p.arm_far if not back else p.arm_near)
    if back:
        f.stamp(ROLL_BACK, 6, 32 + T, LEG, part="roll")
        f.stamp(PACK_BACK, 18, 40 + T, LEG, part="pack")
        f.stamp(ARM_FREE_UP, 8, 44 + T, LEG, part="arm", tone=t_far)
        f.stamp(ARM_FREE_LOW, 8, 58 + T - free_up, LEG, part="arm", tone=t_far)
        f.stamp(ARM_UP, 46, 44 + T, LEG, part="arm", flip=True, tone=t_mirror)
        f.stamp(FOREARM, 48, hand_y - 10, LEG, part="arm", flip=True, tone=t_mirror)
    else:
        f.stamp(["oo", "oo", ".oo", ".oo", ".oo", ".oo", ".oo", ".oo", ".oo", ".oo", ".oo", ".oo", ".oo",
                 ".oo", ".oo", ".oo"], 16, 40 + T, LEG, part="strap")  # the pack's straps over the shoulders
        f.stamp(["nn", "nn", ".nn", ".nn", ".nn", ".nn", ".nn", ".nn", ".nn", ".nn", ".nn", ".nn", ".nn",
                 ".nn", ".nn", ".nn"], 45, 40 + T, LEG, part="strap", flip=True)
        f.stamp(ARM_UP, 10, 44 + T, LEG, part="arm")
        f.stamp(FOREARM, 9, hand_y - 10, LEG, part="arm")
        f.stamp(ARM_FREE_UP, 48, 44 + T, LEG, part="arm", flip=True, tone=t_far)
        f.stamp(ARM_FREE_LOW, 49, 58 + T - free_up, LEG, part="arm", flip=True, tone=t_far)
    _stick(f, sx, 8 + T - lift, 111 - lift)
    f.stamp(FIST, sx - 2, hand_y - 2, LEG, part="fist", flip=back)
    _gourd(f, sx, 20 + T - lift, 1 if back else -1)
    top = HEAD_Y + T
    if back:
        f.stamp(HEAD_BACK, 0, top, LEG, part="head", half_mirror=True)
        sw = p.sway
        f.stamp(TAIL_BACK, 30, 32 + T, LEG, part="tail",
                shift=lambda j, i, ch: (sw * (0 if j < 8 else 1 if j < 14 else 2), 0))
    else:
        f.stamp(HEAD_FRONT, 0, top, LEG, part="head", half_mirror=True)
        f.stamp(NOSE, 30, top + 23, LEG, part="head")
        f.stamp(MOUTH_CORNER, 36, top + 29, LEG, part="head")
        if blink:
            f.stamp(BLINK_FRONT, 22, top + 21, LEG, part="head")
            f.stamp(BLINK_FRONT, 36, top + 21, LEG, part="head")
        sw = p.sway
        f.stamp(SCARF_END, 22, 44 + T, LEG, part="scarf",
                shift=lambda j, i, ch: (sw * (0 if j < 8 else 1 if j < 14 else 2), 0))
    return f.finish()


def _side_leg(f, pose, tone):
    rows = SIDE_LEGS[pose]
    lift = pose[1]
    sole = 111 - 2 * lift - (2 if lift > 1 else 0)
    f.stamp(rows, 16, sole - len(rows) + 1, LEG, part="leg", tone=tone)


def _free_side(f, ay, swing, tone=None):
    rows, ox = HANG[(swing > 0) - (swing < 0)]
    f.stamp(rows, 26 + ox, ay, LEG, part="arm", tone=tone)


def side(p, swap=False, blink=False, walking=False):
    f = Fig(RAMPS)
    B, U = 2 * p.bob, -2 * p.breath
    T = B + U
    top_dx, tip_dx, lift = (2 * v for v in p.staff)
    s_top, s_ground = 8 + T - lift, 111 - lift
    stick_x, tip_x = 48 + top_dx, 48 + tip_dx
    grip = 2 if (p.prop > 0 and not walking) else 0
    hand_y = 64 + T - lift - grip
    hand_x = _lean(stick_x, s_top, s_ground, tip_x, hand_y)
    ay = 44 + T

    def stick_arm(tone, hand_tone):
        f.stamp(ARM_UP_SIDE, 30, ay, LEG, part="arm", tone=tone)
        f.stamp(FOREARM_SIDE, hand_x - 11, hand_y - 8, LEG, part="arm", tone=tone)
        f.stamp(HAND_SIDE, hand_x - 2, hand_y - 2, LEG, part="fist", tone=hand_tone)

    _side_leg(f, p.far, t_far)
    if swap:  # facing left: the stick, the gourd and their arm are on the far side
        _stick(f, stick_x, s_top, s_ground, tip=tip_x, tone=t_far)
        _gourd(f, stick_x, s_top + 14, 1, tone=t_darker)
        stick_arm(t_far, t_darker)
    else:
        _free_side(f, ay, p.arm_far, tone=t_far)
    _side_leg(f, p.near, None)
    _body(f, BODY_SIDE, B, U, False, -p.sway, [(0, 26)])
    f.stamp(PACK_SIDE, 9, 36 + T, LEG, part="pack")
    f.stamp(["pp"] * 18, 26, 42 + T, LEG, part="strap")  # the shoulder strap across the coat
    top = HEAD_Y + T
    f.stamp(HEAD_SIDE, 2, top, LEG, part="head")  # the head 2 texels ahead of the chest: the stoop
    sw = p.sway
    f.stamp(TAIL_SIDE, 20, 34 + T, LEG, part="tail", shift=lambda j, i, ch: (-sw if j >= 6 else 0, 0))
    if blink:
        f.stamp(BLINK_SIDE, 32, top + 19, LEG, part="head")
    if not swap:
        _stick(f, stick_x, s_top, s_ground, tip=tip_x)
        _gourd(f, stick_x, s_top + 14, 1)
        stick_arm(None, None)
        f.stamp(SCARF_END_SIDE, 40 + (2 if walking else 0), 42 + T, LEG, part="scarf",
                shift=lambda j, i, ch: (-sw * (0 if j < 6 else 1 if j < 12 else 2), 0))
    else:
        _free_side(f, ay, p.arm_near)
    return f.finish()


def frame(npc_v1, action, view, i):
    """The Fig of one frame and whether it is mirrored (left)."""
    p = npc_v1.pose(action, i)
    w = action == "walk"
    if view == "down":
        return front(p, blink=p.blink, walking=w), False
    if view == "up":
        return front(v1_back_pose(p), back=True, walking=w), False
    if view == "right":
        return side(p, blink=p.blink, walking=w), False
    return side(p, swap=True, blink=p.blink, walking=w), True
