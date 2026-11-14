"""v3 cook (宿の料理人), round 4: hand-drawn pixel maps at the v3 grid (npc_pixmap.py).

v1 (src/art-release/npc/npc.cook.*, tools/npc_release/cook.py, read only) is the reference for the look:
sturdy, a round ruddy face, thick brows, thin smiling eyes (a lash line with a small dark eye under it),
red cheeks, a wide U smile; light-brown short hair under a white triangular headscarf knotted at the back;
a rust shirt with the sleeves rolled to the elbow, bare forearms; a long white apron with a neck strap and a
waist tie (a bow at the back); brown trousers, boots; a ladle at his right hip, a striped towel over his
left shoulder. New at 2x: the scarf's hem and the knot's ends and point; hair strands; the ear; the nose's
underside; the apron's pocket, hem and crease; the bow's loops and tails; the cuff of the rolled sleeve;
the boot's cuff and seam; the towel's double stripes; the ladle's neck and bowl.

Legend (6 tones each, 0 outline .. 5 highlight; tone 2 is v3's middle shade):
  0-5 hair   a-f skin   A-F shirt   G-L cloth (scarf, apron)   M-R trousers   S-X boot
  g-l towel  m-r wood   s-x steel
  inks: # lash   y brow   % eye   = mouth   ~ cheeks, lower lip
"""

from npc_pixmap import grid, half, legend

RAMPS = {  # v1's ramps (tools/npc_release/cook.py RAMPS + tools/art_proto/pixel.py BASE_RAMPS)
    "hair": ["#2e1a0c", "#6a4424", "#946436", "#b8844c", "#d8a86a"],
    "skin": ["#6a3626", "#c07a5c", "#eaa684", "#f8c4a0", "#ffdcc0"],
    "shirt": ["#2a0e08", "#6a2a18", "#984228", "#be6040", "#dc8a64"],
    "cloth": ["#4e4c4a", "#aaa8a2", "#e2e0da", "#f4f2ee", "#ffffff"],
    "trousers": ["#1e140c", "#46301e", "#62442c", "#80603e", "#a07c54"],
    "boot": ["#1e120a", "#3e2616", "#62402a", "#865c3c", "#a87a52"],
    "towel": ["#2c3446", "#6a7c9c", "#a8bcd8", "#d4e0f0", "#f4f8ff"],
    "wood": ["#1e1008", "#4a2c16", "#6e4424", "#906038", "#b07e50"],
    "steel": ["#1a1e26", "#4a5260", "#7a8494", "#a8b2c0", "#e0e6ee"],
}
INKS = {"#": "#2a1a14", "y": "#3e2414", "%": "#3a2418", "=": "#8a3a34", "~": "#e8806a"}
EYE_INKS = {INKS[k] for k in "#%"}
IRIS_INKS = {INKS["%"]}  # his eye: the small dark eye under the lash line (v1's 'k'); shut: the lash only
LEG = legend([("012345", "hair"), ("abcdef", "skin"), ("ABCDEF", "shirt"), ("GHIJKL", "cloth"),
              ("MNOPQR", "trousers"), ("STUVWX", "boot"), ("ghijkl", "towel"), ("mnopqr", "wood"),
              ("stuvwx", "steel")], INKS)

# ------------------------------------------------------------------ maps (hand drawn)

HEAD_FRONT = half("""
.....................JJKKKKKKKKK
..................JJKKKKLLLLLKKK
................JJKKKKLLLLLLLKKK
...............JJKKKLLLLLLKKKKKK
..............JJKKKLLLLKKKKKKKKK
.............JJKKKLLLKKKKKKKKKKK
............IJKKKLLLKKKKKKKKKKKK
............IJKKLLLKKKKKKKKKKKKK
...........IJKKLLKKKKKKKKKKKKKKK
...........IJKKLLKKKKKKKKKKKKKKK
..........IJKKKKKKKKKKKKKKKKKKKK
..........IJKKKKKKKKKKKKKKJJJJJJ
..........HIKKKKKKKJJJIIJJJJJJJJ
..........HIJJIIIJJJJJJJJJJKKJJJ
..........4554GHHHHHHIJJIIIIIIII
..........45543GHHHHHHHHHHIIIIII
..........455434dddddddddddddddd
..........455434deeeeyyyeeffffff
..........445434deeyyyyyyeeeeeee
..........444434deyyyyyyyeeeeeee
..........cd4434deyeeeeeeeeeeeee
.........cdee4343eeeeeeeeeeeeeee
........cdeeeeeeeee####eeeeeeeee
........cdceeeeeee#e%%e#eeeeeeee
........cdceeeeeeeeeeeeeeeeeeeff
........cdeeeeeeeeddddddeeeeeeff
.........cdeee~~~~~~eeeeeeeedeff
..........cde~~~~~~~eeeeeeeedeff
..........cdde~~~~~eeeeeeeeeccdd
..........cddee~~~edeeeeeeeeeeee
..........cddeeeeeed=eeeeeeeeeee
...........cddeeeeee==eeeeeeeeee
...........cddeeeeee=====eeeeeee
............cddeeeeee===========
.............cddeeeeeeee========
..............cddeeeeeeee~~~~~~~
...............cddeeeeeeeedddddd
.................cddeeeeeeeeeeee
...................cdddddddddddd
......................cccccccccc
""")

HEAD_FRONT_BLINK = half("""
.....................JJKKKKKKKKK
..................JJKKKKLLLLLKKK
................JJKKKKLLLLLLLKKK
...............JJKKKLLLLLLKKKKKK
..............JJKKKLLLLKKKKKKKKK
.............JJKKKLLLKKKKKKKKKKK
............IJKKKLLLKKKKKKKKKKKK
............IJKKLLLKKKKKKKKKKKKK
...........IJKKLLKKKKKKKKKKKKKKK
...........IJKKLLKKKKKKKKKKKKKKK
..........IJKKKKKKKKKKKKKKKKKKKK
..........IJKKKKKKKKKKKKKKJJJJJJ
..........HIKKKKKKKJJJIIJJJJJJJJ
..........HIJJIIIJJJJJJJJJJKKJJJ
..........4554GHHHHHHIJJIIIIIIII
..........45543GHHHHHHHHHHIIIIII
..........455434dddddddddddddddd
..........455434deeeeyyyeeffffff
..........445434deeyyyyyyeeeeeee
..........444434deyyyyyyyeeeeeee
..........cd4434deyeeeeeeeeeeeee
.........cdee4343eeeeeeeeeeeeeee
........cdeeeeeeeeeeeeeeeeeeeeee
........cdceeeeeeeddddddeeeeeeee
........cdceeeeeee######eeeeeeff
........cdeeeeeeeeeeeeeeeeeeeeff
.........cdeee~~~~~~eeeeeeeedeff
..........cde~~~~~~~eeeeeeeedeff
..........cdde~~~~~eeeeeeeeeccdd
..........cddee~~~edeeeeeeeeeeee
..........cddeeeeeed=eeeeeeeeeee
...........cddeeeeee==eeeeeeeeee
...........cddeeeeee=====eeeeeee
............cddeeeeee===========
.............cddeeeeeeee========
..............cddeeeeeeee~~~~~~~
...............cddeeeeeeeedddddd
.................cddeeeeeeeeeeee
...................cdddddddddddd
......................cccccccccc
""")

HEAD_BACK = half("""
.....................JJKKKKKKKKK
..................JJKKKKLLLLLKKK
................JJKKKKLLLLLLLKKK
...............JJKKKLLLLLLKKKKKK
..............JJKKKLLLLKKKKKKKKK
.............JJKKKLLLKKKKKKKKKKK
............IJKKKLLLKKKKKKKKKKKK
............IJKKLLLKKKKKKKKKKKKK
...........IJKKLLKKKKKKKKKKKKKKK
...........IJKKLLKKKKKKKKKKKKKKK
..........IJKKKKKKKKKKKKKKKKKKKK
..........IJKKKKKKKKKKKKKKKKKKKK
..........IJKKKKKKKKKKKKKKKKKKKK
..........IJKKKKKKKKKKKKKKKKJJKK
..........HIJJJJJJJJJJJJJJIKLLKK
..........HIJJJJJJJJJJJJJJIKLLKK
..........44443444443444IKKKLKKJ
..........45543455543444IKKKKKJJ
........cd455434555434IKKJJKKKJI
........cd455434554434IKJ4IJJJJI
........cd445444455434IJ344IKKKK
........cd44544455543454345IKKKJ
........cd445434554434543455IKKJ
........cd445434454434543445IKKJ
..........4454344544344434454IKJ
..........44443444443444344444IJ
..........4443334443334333444333
...........443.34443c343c34443c3
................cccccccccccccccc
................ccdddddddddddddd
................ccdddddddddddddd
................ccdddddddddddddd
................ccdddddddddddddd
................ccdddddddddddddd
...............ccddddddddddddddd
..............ccdddddddddddddddd
""")

HEAD_SIDE = grid("""
25|JJKKKKKKJJ
22|JJKKLLLLKKKKKJJ
20|JJKKLLLLLKKKKKKKKJJ
19|JJKLLLLLKKKKKKKKKKKJJ
17|JJKKLLLLKKKKKKKKKKKKKKKJJ
16|JJKKLLLKKKKKKKKKKKKKKKKKKJJ
15|JJKKLLLKKKKKKKKKKKKKKKKKKKKJJ
14|IJKKLLKKKKKKKKKKKKKKKKKKKKKKKJJ
14|IJKLLKKKKKKKKKKKKKKKKKKKKKKKKKJI
13|IJKKLKKKKKKKKKKKKKKKKKKKKKKKKKKJI
13|IJKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKJI
12|IJKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKJI
12|IJKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKJI
11|JJJKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKJI
9|IKLLKKJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJI
9|IKLKKKJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJI
9|IKKKKKJI44534dddddddddddddddddddddddddd
9|IKKKKKJI45534deeeeeeeeeeeeeffffffeeeeee
9|IJKKKKJI45534deeeeeeeeeeeeeyyyyyyeeeeee
9|IJKKKJJI45534deeeeeeeeeeeeyyyyyyyyeeeee
10|IKKKJI454434454cccceeeeeeeeeeeeeeeeeeef
10|IKKKJI45443445cdeedceeeeeeeeeeeeeeeeeeff
11|IKKJI45543445cdccdceeeeeeee####eeeeeeff
11|IKKJI45543445cdccdceeeeeee#e%%e#eeeeeeff
12|IKJI44543444cdccdceeeeeeeeeeeeeeeeeeeefff
13|IJ244543444ecddceeeeeeedddddddeeeeddeeee
16|4454344ceecceeee~~~~~~~eeeeeeeeeccdd
16|445434cdeeeeeee~~~~~~~~eeeeeeeeedd
17|4543cdeeeeeeeee~~~~~~deeeeeeeeed
18|443cddeeeeeeeee~~~~edeeeeeeeeee
19|43cddeeeeeeeeeeeeee=eeeeeeeeeee
21|cddeeeeeeeeeeeeee==eeeeeeeeee
21|cddeeeeeeeeeeeeee====eeeeeee
22|cddeeeeeeeeeeeeeee========
23|cddeeeeeeeeeeeeeeee~~~~~~
24|cddeeeeeeeeeeeeeeeeddd
25|cddeeeeeeeeeeeeeeeee
27|cddeeeeeeeeeeeee
29|cddddddddddd
32|cccccc
""", 54)

HEAD_SIDE_BLINK = grid("""
25|JJKKKKKKJJ
22|JJKKLLLLKKKKKJJ
20|JJKKLLLLLKKKKKKKKJJ
19|JJKLLLLLKKKKKKKKKKKJJ
17|JJKKLLLLKKKKKKKKKKKKKKKJJ
16|JJKKLLLKKKKKKKKKKKKKKKKKKJJ
15|JJKKLLLKKKKKKKKKKKKKKKKKKKKJJ
14|IJKKLLKKKKKKKKKKKKKKKKKKKKKKKJJ
14|IJKLLKKKKKKKKKKKKKKKKKKKKKKKKKJI
13|IJKKLKKKKKKKKKKKKKKKKKKKKKKKKKKJI
13|IJKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKJI
12|IJKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKJI
12|IJKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKJI
11|JJJKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKJI
9|IKLLKKJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJI
9|IKLKKKJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJI
9|IKKKKKJI44534dddddddddddddddddddddddddd
9|IKKKKKJI45534deeeeeeeeeeeeeffffffeeeeee
9|IJKKKKJI45534deeeeeeeeeeeeeyyyyyyeeeeee
9|IJKKKJJI45534deeeeeeeeeeeeyyyyyyyyeeeee
10|IKKKJI454434454cccceeeeeeeeeeeeeeeeeeef
10|IKKKJI45443445cdeedceeeeeeeeeeeeeeeeeeff
11|IKKJI45543445cdccdceeeeeeeeeeeeeeeeeeff
11|IKKJI45543445cdccdceeeeeeeddddddeeeeeeff
12|IKJI44543444cdccdceeeeeee######eeeeeeefff
13|IJ244543444ecddceeeeeeeeeeeeeeeeeeddeeee
16|4454344ceecceeee~~~~~~~eeeeeeeeeccdd
16|445434cdeeeeeee~~~~~~~~eeeeeeeeedd
17|4543cdeeeeeeeee~~~~~~deeeeeeeeed
18|443cddeeeeeeeee~~~~edeeeeeeeeee
19|43cddeeeeeeeeeeeeee=eeeeeeeeeee
21|cddeeeeeeeeeeeeee==eeeeeeeeee
21|cddeeeeeeeeeeeeee====eeeeeee
22|cddeeeeeeeeeeeeeee========
23|cddeeeeeeeeeeeeeeee~~~~~~
24|cddeeeeeeeeeeeeeeeeddd
25|cddeeeeeeeeeeeeeeeee
27|cddeeeeeeeeeeeee
29|cddddddddddd
32|cccccc
""", 54)

BODY_FRONT = half("""
..............CDEEEEEEDDDDJKDDDD
............CDEEEEEEEEDDDJKDDDDD
..........CDEEEEEEEEEDDDJKDDDDDD
.........CDEEEEEEEDDDDDJKDDDDDDD
........CDEEEEEEDDDDDDJKDDDDDDDD
.......BCDEEEEDDDDDDDJKDDDDDDDDD
......BCDEEEDDDDDDDDJKLLLLLLLLLL
......BCDEEEDDDDDDDDJKLKKKKKKKKK
......BCDEEDDDDDDDDDJKKKKKKKKKKK
......BCDEEDDDDDDDDDJKKKKKKKKKKK
......BCDEEDDDDDDDDDJJKKKKJJJJJJ
......BCDEEDDDDDDDDDJJKKKKJKKKKK
......BCDEEDDDDDDDDDJJKKKKJKKKKK
......BCDEEDDDDDDDDDJJKKKKJKKKKK
......BCDEEDDDDDDDDDJJKKKKJKKKKK
......BCDEEDDDDDDDDDJJKKKKJJJJJJ
......BCDEEDDDDDDDDDJJIIIIKKKKKK
......BCDEEDDDDDDDDDJJKKKKIIIIII
......BCDEEDDDDDDDDDJJKKKKKKKKKK
......BCDEEDDDDDDDDDJJKKKKKKKKKK
......BCDEEDDDDDDDDDJJKKKKKKKKKK
......BCDEEDDDDDDDDDJJKKKKKKKKKK
....BCDDEEDDDDDDJJJJJJJJJJJJJJJJ
....BCDDEDDDDDDDJJJJIIIIIIIIIIII
....BCDDEDDDDDDDIJIIIIIIIIIIIIII
....BCDDEDDDDDDDIJKKIKKKIKKKKIKK
....BCDDEDDDDDIJKLKKIKKKIKKKKIKK
....BCDDEDDDDDIJKLLKIKKKIKKKKKKK
....BCDDEDDDDDIJKKLLKKKKIKKKKKKK
....BCDDEDDDDDIJKKLLKKKKIKKKKKKK
....BCDDEDDDDDIJKKLLKIKKKKKKKKKK
....BCDDEDDDDDIJKKLLKIKKKKKKKKKK
.....BCDDDDDIJKKKKLLKIKKKKIKKKKK
.....BCDDDDDIJKKKKLLKIKKKKIKKKKK
......BCDDDDIJKKKKKKKIKKKKIKKKKK
......BCCCCCIJKKKKKKKIKKKKIKKKKK
........NOPPIJJKKKKKIKKKKKIKKKKK
........NOPPIJJKKKKKIKKKKKIKKKKK
........NOPPIJJKKKKKIKKKKKIKKKKK
........NOPPIJJKKKKKIKKKKKIKKKKK
........NOPPIJJKKKKKIKJJJKIKKKKK
........NOPPIJJKKKKKIJJJJJIKKKKK
............IJJKKKKIJJJJJJIKKKKK
............IJJKKKKIJJJJJJIKKKKK
............IJJKKKKIJJJJJJIIKKKK
............IJJKKKKIJJJJJJKIKKKK
............IJJKKKKIJJJJJJKIKKKK
............IJJKKKKIJJJJJJKIIKKK
............IJJJJJJJJJJJJJJJJJJJ
............HIIIIIIIIIIIIIIIIIII
""")

BODY_BACK = half("""
..................CDEEEEJKKKKKKK
................CDEEEEEEIJJJJJJJ
..............CDEEEEEEEEDDDDDDDD
............CDEEEEEEEEEDDDDDDDDD
..........CDEEEEEEEEEDDDDDDDDDDD
.........CDEEEEEEECCDDDDDDDDDDDD
........CDEEEEEEDDCCDEEEEEEEDDDD
.......BCDEEEEDDDDCCDEEEEEEEDDDD
......BCDEEEDDDDDDCCDEEEEEEDDDCC
......BCDEEEDDDDDDCCDEEEEEDDDDCC
......BCDEEDDDDDDDCCDDEEEDDDDDCC
......BCDEEDDDDDDDCCDDDDDDDDDDCC
......BCDEEDDDDDDDCCDCCCCCCDDDCC
......BCDEEDDDDDDDCCDDCCCCCCDDCC
......BCDEEDDDDDDDCCCCCCCCCCEECC
......BCDEEDDDDDDDCCCCCCCCCDEECC
......BCDEEDDDDDDDCCCCCCCCDDEECC
......BCDEEDDDDDDDCCCCCCCDDDEECC
......BCDEEDDDDDDDCCCCCCDDDDEECC
......BCDEEDDDDDDDCCCCCCDDDDEECC
......BCDEEDDDDDDDCCCCCDDDDDEECC
......BCDEEDDDDDDDCCCCCDDDDDEECC
......BCDEEDDDDDDDCCCCCDDDDDEECC
......BCDEEDDDDDDDCCCCCDDDDDEECC
....BCDDEEDDDDJJJJJJJJKKKKKKIKKK
....BCDDEDDDDDIIIIIIIKKLLKKKIKKK
....BCDDEDDDDDCCCCCCCKKKKKKKIIKK
....BCDDEDDDDDCCCCCCDDIIIIIIDIII
....BCDDEDDDDDDDDCCDDDDDDDDDIKKI
....BCDDEDDDDDDDCCDDDDDDDDDIKKCC
....BCDDEDDDDDDCCDDDDDDDDDDIKKCC
....BCDDEDDDDDDDDDDDDDDDDDIKKICC
....BCDDEDDDDDDDDDDDDDDDDDIKKICC
....BCDDEDDDDDDDDDDDDDDDDDIIIDCC
.....BCDDDDDDDDDDDDDDDDDDDDDDDCC
.....BCDDDDDDDDDDDDDDDDDDDDDDDCC
......BCDDDDDDDDDDDDDDDDDDDDDDCC
......BCCCCCCCCCCCCCCCCCCCCCCCCC
........NOPQQPPPPPPPPPPPPPPPPPPN
........NOPQQPPPPPPPPPPPPPPPPPPN
........NOPQQPPPPPPPPPPPPPPPPPPN
........NOPQQPPPPPPPPPPPPPPPPPPN
........NOPQQPPPPPPPPPPPPPPPPPPN
........NOPQQPPPPPPPPPPPPPPPPPPN
""")

BODY_SIDE = grid("""
21|CDEEEEEDDDC
19|CDEEEEEEEDDDJKK
17|CDEEEEEEEEDDDDDJKKK
16|CDEEEEEEEEDDDDDDJKKKKL
15|BCDEEEEEEEDDDDDDDJJJKKKL
14|BCDEEEEEEDDDDDDDDDJJJKKKKL
13|BCDEEEEEDDDDDDDDDDDJKJJKKKKL
12|BCDEEECCDDDDDDDDDDDDJKJJKKKKKL
12|BCDEEEDCCDDDDDDDDDDDJKKJJKKKKKL
12|BCDEEEDDCCDDDDDDDDDDJKKJJKKKKKKL
11|BCDEEEDDDDCCDDDDDDDDDJKKKJJKKKKKKL
11|BCDEEDDDDDDDDDDDDDDDDJKKKKKKKKKKKKL
10|BCDEEDDDDDDDDDDDDDDDDDJJKKKKKKKKJJKL
10|BCDEEDDDDDDDDDDDDDDDDDJJKKKKKKKKJJJKL
10|BCDEEDDDDDDDDDDDDDDDDDJJKKKKKKKKJJJKL
10|BCDEEDDDDDDDDDDDDDDDDDJJKKKKKKKKJJJJKL
10|BCDEEDDDDDDDDDDDDDDDDDJJKKKKKKKKJJJJKL
10|BCDEEDDDDDDDDDDDDDDDDDJJKKKKKKKKJJJJKL
10|BCDEEDDDDDDDDDDDDDDDDDJJKKKKKKKKJJJJKL
10|BCDEEDDDDDDDDDDDDDDDDDJJKKKKKKKKJJJJKL
10|BCDEEDDDDDDDDDDDDDDDDDJJKKKKKKKKJJJJKL
10|BCDEEDDDDDDDDDDDDDDDDDJJKKKKKKKKJJJJKL
10|BCDEEDDDDDJJJJJJJJJJJJJJJJJJJJJJJJJJJJ
10|BCDEEDDDDDIIIIIIIIIIIIIIIIIIIIIIIIIIII
10|BCDEEDDDDDDDDDDDDDDDIIIIIIIIIIIIIIIIIL
10|BCDEEDCCDDDDDDDDDDDIJKKIKKIKKKKIKKKKKL
10|BCDEEDDCCDDDDDDDDDIJKKKIKKIKKKKIKKKKKL
10|BCDEEDDDCCDDDDDDDDIJKKKIKKIKKKKIKKKKKL
10|BCDEEDDDDCCDDDDDDIJKKKKKKKIKKKKIKKKKL
10|BCDEEDDDDDDDDDDDDIJKKKKKKKIKKKKKKKKKL
10|BCDEEDDDDDDDDDDDIJKKKKKKKKIKKKKJJJKL
10|BCDEEDDDDDDDDDDDIJKKKKKKKKIKKKJJJJKL
11|BCDEDDDDDDDDDDDIJKKKKKKKKIKKJJJJKL
11|BCCCCCCCCCCCCCCIJKKKKKKKKIKJJJJJKL
12|NOPQQPPPPPPOIJKKKKKKKKKKIKJJJJKL
12|NOPQQPPPPPPOIJKKKKKKKKKKIKJJJJKL
12|NOPQQPPPPPPOIJKKKKKKKKKKIJJJJJKL
12|NOPQQPPPPPPOIJKKKKKKKKKKIKKKKKL
12|NOPQQPPPPPPOIJKKKKIJJJJJIKKKKKL
12|NOPQQPPPPPPOIJKKKKIJJJJJIKKKKKL
14|NOPQPPPPPOIJKKKKIJJJJJIKKKKL
14|NOPQPPPPPOIJKKKKIJJJJJIKKKKL
14|NOPQPPPPPOIJKKKKIJJJJJIKKKL
14|NOPQPPPPPOIJKKKKIJJJJJIKKKL
15|NOPPPPPPOIJKKKKIJJJJJIIKL
15|NOPPPPPPOIJKKKKIJJJJJKIKL
17|NOPPPPOIJKKKKIJJJJJKIKL
17|NOPPPPOIJKKKKIJJJJJKIIL
19|NOPPOIJJJJJJJJJJJJJJJJ
21|NOOHIIIIIIIIIIIIIII
""", 48)

# his arm from the front: the sleeve rolled to the elbow, the bare forearm, the hand
ARM = grid("""
..DEEEED
.DDEEEEDD
BDEEEEDDCB
BDEEEDDDCB
BDEEEDDDCB
BDEECCDDCB
BDEDDCCDCB
BCDDDDDCCB
CEFFFFEEDC
CEFFFEEEDC
.deeeeeed
.deeffeed
.deeffeed
.deeeeeed
.deeeeeed
.deeeeedd
.deeeeedd
.deeeeeed
cdeffeeedc
cdeedededc
cdeedededc
.cddddddc
""", 10)

# side view: the arm hanging (0), swung forward (F), swung back (B)
ARM_SIDE_0 = grid("""
...DDEEDD
..DDEEEEDD
.BDEEEEEDCB
.BDEEEEDDCB
.BDEEEDDDCB
.BDEEEDDDCB
.BDEEDDDDCB
.BDEECCDDCB
.BDEDDCCDCB
.BDEDDDDCCB
.BDDDDDDCCB
.CEFFFFEEDC
.CEFFFEEEDC
..deeeeeed
..deeffeed
..deeffeed
..deeeeeed
..deeeeeed
..deeeeedd
..deeeeedd
..deeeeeed
.cdeffeeedc
.cdeedededc
.cdeedededc
..cddddddc
...cccccc
""", 22)

ARM_SIDE_F = grid("""
...DDEEDD
..DDEEEEDD
.BDEEEEEDCB
.BDEEEEDDCB
.BDEEEDDDCB
.BDEEEDDDCB
..BDEEDDDDCB
..BDEEDDDDCB
..BDEDDDDDCB
...BDDDDDDCCB
...BDDDDDDCCB
...CEFFFFEEDC
4|CEFFFEEEDC
5|deeeeeed
5|deeffeed
6|deeffeed
6|deeeeeed
7|deeeeeed
7|deeeeedd
8|deeeeedd
8|deeeeeed
7|cdeffeeedc
8|cdeeeeeedc
8|cdeeeedddc
9|cddddddc
10|cccccc
""", 22)

ARM_SIDE_B = grid("""
10|DDEEDD
9|DDEEEEDD
8|BDEEEEEDCB
8|BDEEEEDDCB
8|BDEEEDDDCB
8|BDEEEDDDCB
7|BDEEDDDDCB
7|BDEEDDDDCB
7|BDEDDDDDCB
6|BDDDDDDCCB
6|BDDDDDDCCB
6|CEFFFFEECC
5|CEFFFEEEDC
5|deeeeeed
5|deeffeed
4|deeffeed
4|deeeeeed
...deeeeeed
...deeeeedd
..deeeeedd
..deeeeeed
cdeffeeedc
cdeeeeeedc
cdeeeedddc
.cddddddc
..cccccc
""", 22)

# his legs from the front (his right leg, image left; the other is its mirror)
LEG_FRONT = grid("""
..OPQQPPPNPO
..OPQQPPPNPO
..OPQQPPPNPO
..OPQQPPPNPO
..OPQQPPPNPO
..OPQQPPPNPO
..OPQQPPPNPO
..OPQQPPPNPO
..OPQQPPPNPO
..OPQQPPPNPO
..OPQQPPPNPO
..OPQQPPPNPO
..OPQQPPPNPO
..OPQQPPPNPO
..OPQQPPPNPO
..OPQQPPPNPO
..OPQPPPPNPO
..OPQPPPPNPO
..OPPPPPPNOO
..NNNNNNNNNN
..VWXXWVVVUT
..VWWWVVVVUT
..UUUUUUUUUT
..VWVVVVVVUT
..VWVVVVVVUT
UUWWVVVVVVUT
UWWVVVVVVVUT
TTTTTTTTTTTT
""", 12)

LEG_BACK = grid("""
..OPQQPPPNPO
..OPQQPPPNPO
..OPQQPPPNPO
..OPQQPPPNPO
..OPQQPPPNPO
..OPQQPPPNPO
..OPQQPPPNPO
..OPQQPPPNPO
..OPQQPPPNPO
..OPQQPPPNPO
..OPQQPPPNPO
..OPQQPPPNPO
..OPQQPPPNPO
..OPQQPPPNPO
..OPQQPPPNPO
..OPQQPPPNPO
..OPQPPPPNPO
..OPQPPPPNPO
..OPPPPPPNOO
..NNNNNNNNNN
..VVVVVVVVUT
..VVVVVVVVUT
..UUUUUUUUUT
..VVVVVVVVUT
..VVVVVVVVUT
UUVVVVVVVVUT
UVVVVVVVVVUT
TTTTTTTTTTTT
""", 12)

# side view (facing right): (forward, lift) of v1's gait
LEG_SIDE_p0_0 = grid("""
11|OPQQPPPPON
11|OPQQPPPPON
11|OPQQPPPPON
11|OPQQPPPPON
11|OPQQPPPPON
11|OPQQPPPPON
11|OPQQPPPPON
11|OPQQPPPPON
11|OPQQPPPPON
11|OPQQPPPPON
11|OPQQPPPPON
11|OPQQPPPPON
11|OPQQPPPPON
11|OPQQPPPPON
11|OPQQPPPPON
11|OPQQPPPPON
11|OPQQPPPPON
11|OPQQPPPPON
11|OPQPPPPPON
11|OPQPPPPPON
11|OPPPPPPPOO
11|NNNNNNNNNN
10|UWXXWVVVVUT
10|UWWWVVVVVUT
10|TUUUUUUUUUT
11|UWVVVVVVVU
11|UWVVVVVVVVVU
10|UWWVVVVVVVVWWVU
10|UVVVVVVVVVVVVVU
10|TTTTTTTTTTTTTTT
""", 32)

LEG_SIDE_p3_0 = grid("""
11|OPQQPPPPON
11|OPQQPPPPON
11|OPQQPPPPON
12|OPQQPPPPON
12|OPQQPPPPON
12|OPQQPPPPON
13|OPQQPPPPON
13|OPQQPPPPON
13|OPQQPPPPON
14|OPQQPPPPON
14|OPQQPPPPON
14|OPQQPPPPON
15|OPQQPPPPON
15|OPQQPPPPON
15|OPQQPPPPON
16|OPQQPPPPON
16|OPQQPPPPON
16|OPQQPPPPON
16|OPQPPPPPON
16|OPQPPPPPON
16|OPPPPPPPOO
16|NNNNNNNNNN
15|UWXXWVVVVUT
15|UWWWVVVVVUT
15|TUUUUUUUUUT
16|UWVVVVVVVU
16|UWVVVVVVVVVU
15|UWWVVVVVVVVWWVU
15|UVVVVVVVVVVVVVU
15|TTTTTTTTTTTTTTT
""", 32)

LEG_SIDE_m3_0 = grid("""
11|OPQQPPPPON
11|OPQQPPPPON
11|OPQQPPPPON
10|OPQQPPPPON
10|OPQQPPPPON
10|OPQQPPPPON
9|OPQQPPPPON
9|OPQQPPPPON
9|OPQQPPPPON
8|OPQQPPPPON
8|OPQQPPPPON
8|OPQQPPPPON
7|OPQQPPPPON
7|OPQQPPPPON
7|OPQQPPPPON
6|OPQQPPPPON
6|OPQQPPPPON
6|OPQQPPPPON
6|OPQPPPPPON
6|OPQPPPPPON
6|OPPPPPPPOO
6|NNNNNNNNNN
5|UWXXWVVVVUT
5|UWWWVVVVVUT
5|TUUUUUUUUUT
6|UWVVVVVVVU
6|UWVVVVVVVVVU
5|UWWVVVVVVVVWWVU
5|UVVVVVVVVVVVVVU
5|TTTTTTTTTTTTTTT
""", 32)

LEG_SIDE_p3_1 = grid("""
11|OPQQPPPPON
11|OPQQPPPPON
12|OPQQPPPPON
12|OPQQPPPPON
13|OPQQPPPPON
13|OPQQPPPPON
14|OPQQPPPPON
14|OPQQPPPPON
15|OPQQPPPPON
15|OPQQPPPPON
16|OPQQPPPPON
16|OPQQPPPPON
17|OPQQPPPPON
17|OPQQPPPPON
17|OPQQPPPPON
17|OPQQPPPPON
17|OPQPPPPPON
17|OPQPPPPPON
17|OPPPPPPPOO
17|NNNNNNNNNN
16|UWXXWVVVVUT
16|UWWWVVVVVUT
16|TUUUUUUUUUT
17|UWVVVVVVVU
17|UWVVVVVVVVVVWU
16|UWWVVVVVVVVVVVU
16|UVVVVVVVVVVVVU
16|TTTTTTTTTTTTT
""", 32)

LEG_SIDE_m3_1 = grid("""
11|OPQQPPPPON
11|OPQQPPPPON
10|OPQQPPPPON
10|OPQQPPPPON
10|OPQQPPPPON
9|OPQQPPPPON
9|OPQQPPPPON
9|OPQQPPPPON
8|OPQQPPPPON
8|OPQQPPPPON
8|OPQQPPPPON
7|OPQQPPPPON
7|OPQQPPPPON
7|OPQQPPPPON
6|OPQQPPPPON
6|OPQQPPPPON
6|OPQPPPPPON
6|OPQPPPPPON
6|OPPPPPPPOO
6|NNNNNNNNNN
5|UWXXWVVVVUT
5|UWWWVVVVVUT
5|TUUUUUUUUUT
6|UWVVVVVVVU
6|UWVVVVVVVVU
6|UWWVVVVVVVVWU
7|UVVVVVVVVVVVU
8|TTTTTTTTTTTT
""", 32)

LEG_SIDE_p0_2 = grid("""
11|OPQQPPPPON
12|OPQQPPPPON
12|OPQQPPPPON
13|OPQQPPPPON
13|OPQQPPPPON
14|OPQQPPPPON
14|OPQQPPPPON
15|OPQQPPPPON
15|OPQQPPPPON
15|OPQQPPPPON
15|OPQQPPPPON
14|OPQQPPPPON
14|OPQPPPPPON
13|OPPPPPPPOO
13|OPPPPPPPOO
13|NNNNNNNNNN
12|UWXXWVVVVUT
12|UWWWVVVVVUT
12|TUUUUUUUUUT
13|UWVVVVVVVU
13|UWVVVVVVVVU
12|UWWVVVVVVVVVU
12|UVVVVVVVVVVVWU
13|UVVVVVVVVVVVVU
14|TTTTTTTTTTTT
""", 32)

# the ladle at his right hip: the wooden handle up, the steel neck, the bowl down
LADLE = grid("""
..qp....
..qp....
..qp....
..qp....
..qp....
..po....
..po....
..po....
..po....
..on....
..vu....
..vu....
..vu....
..vu....
.tvvvvt.
tvwwwwvt
tvwwwwvt
tuvwwvut
.tuvvut.
..tttt..
""", 8)

# the towel over his left shoulder: its end down his chest (front) and down his back (back)
TOWEL_FRONT = grid("""
jkkkkkkkjj
jkklkkkkjj
jkllkkkkjj
jkkkkkkjjj
jhhhhhhhhj
jkkkkkkjjj
jhhhhhhhhj
jkkkkkjjjj
jkkkkkjjjj
jkkkkjjjjj
jkkkkjjjjj
jhhhhhhhhj
jkkkjjjjjj
jhhhhhhhhj
jkkkjjjjjj
jjjjjjjjjj
ijjjjjjjji
.iiiiiiii.
""", 10)

TOWEL_BACK = grid("""
jkkkkkkkjjjj
jkklkkkkjjjj
jkllkkkjjjjj
jkkkkkkjjjjj
jhhhhhhhhhhj
jkkkkkjjjjjj
jhhhhhhhhhhj
jkkkkkjjjj..
jkkkkjjjjj..
jkkkkjjjjj..
jkkkkjjjjj..
jhhhhhhhhj..
jkkkjjjjjj..
jhhhhhhhhj..
jkkkjjjjjj..
jkkkjjjjjj..
jjjjjjjjjj..
jhhhhhhhhj..
jjjjjjjjjj..
jhhhhhhhhj..
ijjjjjjjji..
.iiiiiiii...
""", 12)

# facing left: the towel lies over the near shoulder (from the back to the front)
TOWEL_OVER = grid("""
..jkkkkkkkkkjj
jjkkllkkkkkkjj
""", 14)

for _m in (HEAD_FRONT, HEAD_FRONT_BLINK, HEAD_BACK, BODY_FRONT, BODY_BACK):
    for _r in _m:
        assert len(_r) == 64, (len(_r), _r)


# ------------------------------------------------------------------ frames (v1's motion, x2)

from npc_pixmap import Fig, t_darker, t_far, t_mirror, v1_back_pose  # noqa: E402

SIDE_LEGS = {(0, 0): LEG_SIDE_p0_0, (3, 0): LEG_SIDE_p3_0, (-3, 0): LEG_SIDE_m3_0, (3, 1): LEG_SIDE_p3_1,
             (-3, 1): LEG_SIDE_m3_1, (0, 2): LEG_SIDE_p0_2}
HANG = {0: ARM_SIDE_0, 1: ARM_SIDE_F, -1: ARM_SIDE_B}
BODY_TOP = 44
# breathing in lifts the chest by 2 (v1: 1 px). The cut is at body row 20 (y 64): rows 18..21 of every body
# map are one repeated row (the back map: its rows 20..23), so the 2 rows the chest leaves are filled by the
# same row: no doubled line. The pocket and the sag under it are above the cut, the waist tie below it.
CUT = 20


def _body(f, rows, B, U, half_mirror, top=BODY_TOP):
    cut = CUT + BODY_TOP - top
    f.stamp(rows[cut - 2:], 0, top + cut - 2 + B, LEG, part="body", half_mirror=half_mirror)
    f.stamp(rows[:cut], 0, top + B + U, LEG, part="body", half_mirror=half_mirror)


def _ladle(f, x, y, glint):
    f.stamp(LADLE, x, y, LEG, part="ladle")
    f.stamp(["xx"], x + 2 + 2 * (glint % 2), y + 15, LEG, part="ladle")  # the light on the bowl


def front(p, back=False, blink=False):
    f = Fig(RAMPS)
    B, U = 2 * p.bob, -2 * p.breath
    legmap = LEG_BACK if back else LEG_FRONT
    for (fwd, lift), x0, flip in ((p.near, 18, False), (p.far, 36, True)):
        yv1 = min(55, 55 - lift + (1 if fwd > 1 else 0))
        bottom = 111 - 2 * (55 - yv1)
        f.stamp(legmap, x0, bottom - len(legmap) + 1, LEG, part="leg", flip=flip,
                tone=t_mirror if flip else None)
    if back:  # the back map starts 2 rows higher: the collar and the apron's neck strap
        _body(f, BODY_BACK, B, U, True, top=BODY_TOP - 2)
    else:
        _body(f, BODY_FRONT, B, U, True)
    ay = 52 + B + U
    if not back:  # his right arm is image left
        f.stamp(ARM, 8, ay - 2 * max(0, p.arm_near), LEG, part="arm")
        f.stamp(ARM, 46, ay - 2 * max(0, p.arm_far), LEG, part="arm", flip=True, tone=t_darker)
    else:
        f.stamp(ARM, 46, ay - 2 * max(0, p.arm_far), LEG, part="arm", flip=True, tone=t_darker)
        f.stamp(ARM, 8, ay - 2 * max(0, p.arm_near), LEG, part="arm", tone=t_darker)
    head = HEAD_BACK if back else (HEAD_FRONT_BLINK if blink else HEAD_FRONT)
    f.stamp(head, 0, 6 + B + U, LEG, part="head", half_mirror=True)
    if back:
        f.stamp(TOWEL_BACK, 10, 45 + B + U, LEG, part="towel")
        f.stamp(["LL"], 28 + 2 * p.glint, 6 + 16 + B + U, LEG, part="head")  # the light on the knot
    else:
        _ladle(f, 14, 60 + B, p.glint)
        f.stamp(TOWEL_FRONT, 42, 45 + B + U, LEG, part="towel")
    return f.finish()


def _side_leg(f, pose, tone):
    rows = SIDE_LEGS[pose]
    lift = pose[1]
    sole = 111 - 2 * lift - (2 if lift > 1 else 0)
    f.stamp(rows, 16, sole - len(rows) + 1, LEG, part="leg", tone=tone)


def _hang_arm(f, ay, swing, tone=None):
    k = (swing > 0) - (swing < 0)
    f.stamp(HANG[k], 23 - (7 if k < 0 else 0), ay, LEG, part="arm", tone=tone)  # B is drawn 7 to the right


def side(p, swap=False, blink=False):
    f = Fig(RAMPS)
    B, U = 2 * p.bob, -2 * p.breath
    ay = 50 + B + U
    _side_leg(f, p.far, t_far)
    _hang_arm(f, ay, p.arm_far, tone=t_darker)
    if not swap:  # the towel on the far shoulder: its end hangs down his back
        f.stamp(TOWEL_BACK, 10, 50 + B + U, LEG, part="towel", tone=t_darker)
    _side_leg(f, p.near, None)  # the long apron hides the thigh
    _body(f, BODY_SIDE, B, U, False)
    f.stamp(HEAD_SIDE_BLINK if blink else HEAD_SIDE, 0, 6 + B + U, LEG, part="head")
    _hang_arm(f, ay, p.arm_near)
    if not swap:  # facing right: the ladle at the near hip
        _ladle(f, 31, 60 + B, p.glint)
    else:  # facing left: the towel over the near shoulder
        f.stamp(TOWEL_FRONT, 31, 47 + B + U, LEG, part="towel")
        f.stamp(TOWEL_OVER, 21, 45 + B + U, LEG, part="towel")
        f.stamp(["ll"], 33 + 2 * p.glint, 50 + B + U, LEG, part="towel")
    return f.finish()


def frame(npc_v1, action, view, i):
    """The Fig of one frame and whether it is mirrored (left)."""
    p = npc_v1.pose(action, i)
    if view == "down":
        return front(p, blink=p.blink), False
    if view == "up":
        return front(v1_back_pose(p), back=True), False
    if view == "right":
        return side(p, blink=p.blink), False
    return side(p, swap=True, blink=p.blink), True
