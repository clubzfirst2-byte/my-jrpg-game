"""v3 merchant (雑貨屋), round 4: hand-drawn pixel maps at the v3 grid (npc_pixmap.py).

v1 (src/art-release/npc/npc.merchant.*, tools/npc_release/merchant.py, read only) is the reference for the
look: stout, a round face, square gold glasses, eyes closed in a smile, a black moustache, a broad open
smile; short black hair, a pen behind his right ear; a white shirt with the sleeves rolled up, a crimson
vest with gold buttons (a seam down its back), a leather belt with a gold buckle, golden-brown trousers,
boots; a big purse on his right hip, an account book in his left hand. New at 2x: the lens's glint and the
bridge, the ear, the moustache's ends, the teeth, the rolled cuff, the buckle's frame, the purse's clasp,
the book's lines and page edge, the hair's locks.

Legend (6 tones each, 0 outline .. 5 highlight; tone 2 is v3's middle shade):
  0-5 hair, moustache, the book's ink   a-f skin   A-F vest   G-L shirt   M-R trousers   S-X boot
  g-l gold   m-r leather   s-x book cover   ! $ % ^ & ? wood (the pen)
  inks: # closed eye   y brow   = mouth   ~ blush   * the lens's glint
"""

from npc_pixmap import grid, half, legend

RAMPS = {  # v1's ramps (tools/npc_release/merchant.py RAMPS + tools/art_proto/pixel.py BASE_RAMPS)
    "hair": ["#0c0b12", "#211f2c", "#353346", "#4d4b64", "#6c6a88"],
    "skin": ["#6a3a28", "#c48a66", "#eeba92", "#fcd2ac", "#ffe8d0"],
    "vest": ["#22070c", "#5c1622", "#8a2632", "#b2404a", "#d4686c"],
    "shirt": ["#4a4640", "#a8a296", "#e4e0d6", "#f6f4ee", "#ffffff"],
    "trousers": ["#2c1c08", "#6a4618", "#986a28", "#bc8c3e", "#dcb466"],
    "cover": ["#3a3226", "#a49478", "#d8cca8", "#ece2c4", "#fffaea"],
    "leather": ["#24160c", "#4a3020", "#704c30", "#946c46", "#b88c5e"],
    "boot": ["#1e120a", "#3e2616", "#62402a", "#865c3c", "#a87a52"],
    "gold": ["#5a4018", "#a07a30", "#e8c060", "#f8dc88", "#fff4c8"],
    "wood": ["#1e1008", "#4a2c16", "#6e4424", "#906038", "#b07e50"],
}
INKS = {"#": "#2a2230", "y": "#24202a", "=": "#9a4a42", "~": "#f0a08c", "*": "#f4fbff"}
EYE_INKS = {INKS["#"]}
IRIS_INKS = EYE_INKS  # his eyes are closed in a smile in every frame (v1 has no open eye): the check counts
# the closed eyes' lines instead of irises: front 2, side 1, back 0, also on the "blink" frame


def IRIS_WANT(view, blink, want):
    return 0 if view == "up" else (2 if view == "down" else 1)


LEG = legend([("012345", "hair"), ("abcdef", "skin"), ("ABCDEF", "vest"), ("GHIJKL", "shirt"),
              ("MNOPQR", "trousers"), ("STUVWX", "boot"), ("ghijkl", "gold"), ("mnopqr", "leather"),
              ("stuvwx", "cover"), ("!$%^&?", "wood")], INKS)

# ------------------------------------------------------------------ maps (hand drawn)

HEAD_FRONT = half("""
....................444444444444
..................44445555554444
................3344445555555544
...............33444555555555444
..............334444555555444433
.............3344445555554444333
............33444455554444333311
...........334444555444433333111
..........3344445544443333111133
..........3344444444433331111333
..........344444333311eeffffeeee
..........34444433311eeeffffeeee
..........344443deefffffffffeeee
..........344443dfffffffffffeeee
..........344433deefffffffeeeeee
..........344433deeeeyyyeeeeeeee
..........3443eeeeeyyyyyyeeeeeee
..........3443eeeeyyyyyyyyeeeeee
.........cdd43eekkkkkkkkkkkkeeee
........cdde43eejjjjjjjjjjjjeeee
........cdce33eejj**eeeeeejjjjjj
........cdce3deejj*eeeeeeejjjjjj
........cdceeeeejjee####eejjeeee
........cdceeeeejj##eeee##jjeeee
.........cdeeeeejjeeeeeeeejjeeff
..........deeeeejjeeeeeeeejjeeff
..........deeeeejjjjjjjjjjjjeeff
..........deeee~~jjjjjjjjjjjeeff
..........ddee~~~~eeeeeeeeeeeddd
..........ddeee~~~~eeeeeeeeeeeee
..........ddeeeeeeee444444444333
..........ddeeeeee33444444443331
..........cdeeee1333ee=fffffffff
...........cdeee133eee==ffffffff
............cdeeeeeeeee====fffff
.............cdeeeeeeeeee=======
..............cdeeeeeeeeeeffffff
...............cdeeeeeeeeeeeeeee
.................cdddddddddddddd
....................cccccccccccc
""")

HEAD_BACK = half("""
....................444444444444
..................44445555554444
................3344445555555544
...............33444555555555444
..............334444555555444433
.............3344445555554444333
............55434555434554345544
...........455434555434554345544
..........3455434555434554345544
..........3455434555434554345544
..........3455434555434554345544
..........3455434555434554345544
..........3445434454434454344544
..........3445434454434454344544
..........3445434454434454344544
..........3445434454434454344544
..........3443334433334433344333
..........3443334433334433344333
........cd3343333433333433334333
........cd3343333433333433334333
........cd3433334333343333433433
........cd3433334333343333433433
........cd3343333433333433334333
........cd3343333433333433334333
..........dd34333433343334333433
..........dd34333433343334333433
..........cddd333433343334333433
...........cdd33dd3333dd3333dd33
............cddddd11dd1111dd1111
............cddddddddddddddddddd
..............ddeeddddeedddddddd
..............ddeeddddeedddddddd
................dddddddddddddddd
................dddddddddddddddd
""")

HEAD_SIDE = grid("""
24|444444444444
21|334445555554444433
20|33444555555544444333
18|334445555555544444333333
17|3344455555555444443333333
16|33444555555544443333331111
16|334445555555444433333111133
16|3344455555544443333311ffeedd
14|3344445555544443333311ffffffeedd
14|3344445555444433333311ffffffeedd
12|3344445544443333deffffffffffeeeeeedd
12|334444554444333ddeffffffffffeeeeeedd
12|334444444433deffffffffffeeeyyyyyeedd
12|334444444433deeeeeeeeeeeeeyyyyyyyedd
12|3344444443deeeeeeeeeeekkkkkkkkkkkkdd
12|3344444443deeeeeeeeeeejjjjjjjjjjjjdd
12|33444443ddjjjjjjjjjjjjjjeeeeeeeejjdd
12|33444443ddjjjjjjjjjjjjjjeeeeeeeejjdd
12|33444443dddceeeeeeeeeejjee######jjee
12|3344444cceedeeeeeeeeeejj##eeeeeejjee
12|334444cdccdceeeeeeeeeejjeeeeeeeejjee
12|334443cdccdceeeeeeeeeejjeeeeeeeejjee
12|334433cdeedceeeeeeeeeejjjjjjjjjjjjfff
12|334433ccddcceeeeeeeeeejjjjjjjjjjjjfffe
16|33ddddeeeeeeeeee~~~~eeeeeeeeeeffee
16|33ddddeeeeeeeeee~~~~eeeeeeeeeeddd
16|33ddeeeeeeeeeeeeee34444444444331
17|3ddeeeeeeeeeeeee334444444444331
18|cdeeeeeeeeeeee1334eeeeeeeeeee
18|cdeeeeeeeeeeee133eeeeeeeeeee
18|cdeeeeeeeeeeeeeeee=ffffffffe
18|cdeeeeeeeeeeeeeeee==fffffff
20|cdeeeeeeeeeeeeeee====ffff
20|cdeeeeeeeeeeeeeeeee======
22|cdeeeeeeeeeeeeeeeeffff
22|cdeeeeeeeeeeeeeeeeeee
24|cddddddddddddddddd
26|cccccccccccccc
""", 54)

BODY_FRONT = half("""
................CDEEEEEEEDJKKKKK
..............CDEEEEEEEEDDJKKKKL
............CDEEEEEEEEDDDDJKKKKL
...........CDEEEEEEEDDDDDDJKKKKK
..........BCDEEEEEEDDDDDDDJKKKKK
.........BCDEEEEEDDDDDDDDDJKKKKK
........BCDEEEEDDDDDDDDDDDjkJKKK
........BCDEEEEDDDDDDDDDDDijJKKK
........BCDEEEDDDDDDDDDDDDCBJKKK
........BCDEEEDDDDDDDDDDDDCBJKKK
........BCDEEEDDDDDDDDDDDDjkJKKK
........BCDEEEDDDDDDDDDDDDijJKKK
........BCDEEEDDDDDDDDDDDDCBJKKK
........BCDEEEDDDDDDDDDDDDCBJKKK
........BCDEEEDDDDDDDDDDDDCBJKKK
........BCDEEEDDDDDDDDDDDDCBJKKK
......BCDDEEEDDDDDDDDDDDDDjkJKKK
......BCDDEEEDDDDDDDDDDDDDijJKKK
......BCDDEEEDDDDDDDDDDDDDCBJKKK
......BCDDEEEDDDDDDDDDDDDDCBJKKK
......BCDDEEEDDDDDDDDDDDDDCBJKKK
......BCDDEEEDDDDDDDDDDDDDCBJKKK
......BCDDEEEDDDDDDDDDDDDDjkJKKK
......BCDDEEEDDDDDDDDDDDDDijJKKK
......BCDDEEEDDDDDDDDECDDDCBJKKK
......BCDDEEEDDDDDDDDECDDDCBJKKK
......BCDDEEEDDDDDDDDECDDDCBJKKK
......BCDDEEEDDDDDDDDECDDDCBJKKK
......BCDDEEEDDDDDDDDECDDDCBJKKK
......BCDDEEEDDDDDDDDECDDDCBJKKK
......BCDDDDDDDDDDDDDECDDDCBJKKK
......BCCCCCCCCCCCCCCCCCCBBIIJJJ
......noppppppppqqqqpppppppppppp
......noppppppppppppppppppppjkkk
......nooooooooooooooooooooojkpp
......mnnnnnnnnnnnnnnnnnnnnnhjjj
........NOPQQPPPPPPPPPPPPPPPPPPO
........NOPQQPPPPPPPPPPPPPPPPPPO
........NOPQQPPPPPPPPPPPPPPPPPPO
........NOPQQPPPPPPPPPPPPPPPPPPO
........NOPQQPPPPPPPPPPPPPPPPPPO
........NOPQQPPPPPPPPPPPPPPPPPPO
""")

BODY_BACK = half("""
................CDEEEEEEJKKKKKKK
..............CDEEEEEEEEDDCCCCCC
............CDEEEEEEEEDDDDDDDDDD
...........CDEEEEEEEDDDDDDDDDDDD
..........BCDEEEEEEDDDDDDDDDDDDD
.........BCDEEEEEDDDDDDDDDDDDDDD
........BCDEEEEDDDDDCCEEEEEEDDDD
........BCDEEEEDDDDDCCEEEEEEDDDD
........BCDEEEDDDDDDCCEEEEEDDDBB
........BCDEEEDDDDDDCCEEEEDDDDBB
........BCDEEEDDDDDDCCEEEDDDDDBB
........BCDEEEDDDDDDCCEEDDDDDDBB
........BCDEEEDDDDDDCCCCCCDDDDBB
........BCDEEEDDDDDDCCCCCCCDDDBB
........BCDEEEDDDDDDCCCCCCCCEEBB
........BCDEEEDDDDDDCCCCCCCDEEBB
......BCDDEEEDDDDDDDCCCCCCDDEEBB
......BCDDEEEDDDDDDDCCCCCDDDEEBB
......BCDDEEEDDDDDDDCCCCDDDDEEBB
......BCDDEEEDDDDDDDCCCCDDDDEEBB
......BCDDEEEDDDDDDDCCECDDDDEEBB
......BCDDEEEDDDDDDDCCECDDDDEEBB
......BCDDEEEDDDDDDDCCECDDDDEEBB
......BCDDEEEDDDDDDDCCECDDDDEEBB
......BCDDEEEDDDDDDDCCECDDECEEBB
......BCDDEEEDDDDDDDCCECDDECEEBB
......BCDDEEEDDDDDDDCCECDDECEEBB
......BCDDEEEDDDDDDDCCECDDECEEBB
......BCDDEEEDDDDDDDCCECDDECEEBB
......BCDDEEEDDDDDDDCCECDDECEEBB
......BCDDEEEDDDDDDDCCECDDECEEBB
......BCCCCCCCCCCCCCCCCCCCCCCCCB
......noppppppppqqqqpppppppppppp
......nopppppppppppppppppppppppp
......nooooooooooooooooooooooooo
......mnnnnnnnnnnnnnnnnnnnnnnnnn
........NOPQQPPPPPPPPPPPPPPPPPPO
........NOPQQPPPPPPPPPPPPPPPPPPO
........NOPQQPPPPPPPPPPPPPPPPPPO
........NOPQQPPPPPPPPPPPPPPPPPPO
........NOPQQPPPPPPPPPPPPPPPPPPO
........NOPQQPPPPPPPPPPPPPPPPPPO
""")

BODY_SIDE = grid("""
20|CDEEEEEEEDJKKKKK
18|CDEEEEEEEEDDJKKKKK
16|CDEEEEEEEEDDDDDDCBJK
15|CDEEEEEEEEDDDDDDDCBJKK
14|BCDEEEEEEEDDDDDDDDDDCBJK
13|BCDEEEEEEDDDDDDDDDDDDCBJKI
12|BCDEEEEEEEDDDDDDDDDDDDjkJKKI
12|BCDEEEEEEEDDDDDDDDDDDDijJKKI
12|BCDEEEEEEDDDDDDDDDDDDDCBJKKKI
12|BCDEEEEEDDDDDDDDDDDDDDCBJKKKKI
11|BCDEEEEEDDDDDDDDDDDDDDDjkJKKKKI
11|BCDEEEEDDDDDDDDDDDDDDDDijJKKKKI
10|BCDEECCCCCDDDDDDDDDDDDDDCBJKKKKKI
10|BCDEEECCCCCDDDDDDDDDDDDDCBJKKKKKI
10|BCDEEEDDDDDDDDDDDDDDDDDDCBJKKKKKKI
10|BCDEEEDDDDDDDDDDDDDDDDDDCBJKKKKKKI
10|BCDEEEDDDDDDDDDDDDDDDDDDjkJKKKKKKI
10|BCDEEEDDDDDDDDDDDDDDDDDDijJKKKKKKI
10|BCDEEEECDDDDDDDDDDDDDDDDCBJKKKKKKI
10|BCDEEEECDDDDDDDDDDDDDDDDCBJKKKKKKI
10|BCDEEEECDDDDDDDDDDDDDDDDCBJKKKKKKI
10|BCDEEEECDDDDDDDDDDDDDDDDCBJKKKKKKI
10|BCDEEEECDDDECDDDDDDDDDDDjkJKKKKKKI
10|BCDEEEECDDDECDDDDDDDDDDDijJKKKKKKI
10|BCDEEEECDDDECDDDDDDDDDDDCBJKKKKKI
10|BCDEEEECDDDECDDDDDDDDDDDCBJKKKKKI
10|BCDEEEECDDDECDDDDDDDDDDDCBJKKKKKI
10|BCDEEEECDDDECDDDDDDDDDDDCBJKKKKKI
10|BCDDDDECDDDECDDDDDDDDDCBIJJJJJI
10|BCCCCCCCCCCCCCCCCCCCCBHIIIIIH
8|noppppppppppppppppppppppppppppppppon
8|nopppppppqqqqpppppppppppppppppppppon
8|nooooooooooooooooooooooooooooooooonm
8|mnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnm
10|NOPQQPPPPPPPPPPPPPPPPPPPPPPONN
10|NOPQQPPPPPPPPPPPPPPPPPPPPPPONN
10|NOPQQPPPPPPPPPPPPPPPPPPPPPPONN
10|NOPQQPPPPPPPPPPPPPPPPPPPPPPONN
10|NOPQQPPPPPPPPPPPPPPPPPPPPPPONN
10|NOPQQPPPPPPPPPPPPPPPPPPPPPPONN
10|NOPQQPPPPPPPPPPPPPPPPPPPPPON
10|NOPQQPPPPPPPPPPPPPPPPPPPPPON
""", 48)

# the right arm hanging: the rolled-up sleeve, the bare forearm, the hand
ARM_DOWN = grid("""
..IJJJJI
.HJJKKKJH
GHJJJKKJHG
GHJJJKKJHG
GHJJJKKJHG
GHJJJKKJHG
GHJJJJKJHG
GHJJJJKJHG
HJKLLLKKJH
HJKLLKKKJH
HIJKKKJJIH
.HHHHHHHH
..deeeed
..deffed
..deffed
..deeeed
..deeeed
..deeeed
..deeeed
..deeeed
.cdeffedc
.cdeeeedc
.cdeedddc
..cddddc
""", 10)

# the left arm bent, its hand on the book's edge
ARM_BOOK = grid("""
..IJJJJI
.HJJKKKJH
GHJJJKKJHG
GHJJJKKJHG
GHJJJKKJHG
GHJJJKKJHG
GHJJJJKJHG
GHJJJJKJHG
HJKLLLKKJH
HJKLLKKKJH
HIJKKKJJIH
.HHHHHHHH
..deeeed
..deeeed
.ddeeeed
cdeeeeed
cdeffeed
.cddddd
""", 10)

# the account book from the front: the binding on its left, a cream cover, lines of ink, the pages' edge
BOOK_FRONT = grid("""
oppppppppppppp
opwwwwwwwwwwwv
opwwvvvvvvvvvv
opwvvvvvvvvvvv
opwvvvvvvvvvvv
opwvv000000vvv
opwvvvvvvvvvvv
opwvv0000vvvvv
opwvvvvvvvvvvv
opwvv000000vvv
opwvvvvvvvvvvv
opwvv00000vvvv
opwvvvvvvvvvvv
opwvv000000vvv
opwvvvvvvvvvvv
opwvv000vvvvvv
opwvvvvvvvvvvv
opvvvvvvvvvvvu
opuuuuuuuuuuuu
ottttttttttttt
""", 14)

BOOK_SIDE = grid("""
opwww
opwww
opwww
opwww
opwww
opwww
opwww
opwww
opwww
opwww
opwww
opwww
opwww
opwww
opwww
opwww
opvvu
oottt
""", 5)

# the big purse, hanging from the belt on his right hip (the clasp is gold)
PURSE = grid("""
..ooppo
.oopqqpn
oopqqqqnn
opqqqqqqnn
pqkkkjqqon
pqkkjjqqon
pqqqqqqqon
pqqqqqqqon
pqqqqqqpon
.pqqqqonn
..oppppo
...oooo
""", 10)

# the pen behind his right ear: from the front only its end shows past the hair; from the side it lies on it
PEN_FRONT = grid("""
??
&??
.&&&
..&&&
...&&^
4|&&^
5|$$$
6|$$$
7|!!!
8|!!
""", 10)

PEN_SIDE = grid("""
&&....
&&....
.^^...
.^^...
..^^..
..^^..
...$$.
...$$.
...!!.
...!!.
""", 6)

# side view: the left arm, its elbow back and the forearm forward under the book
ARM_BOOK_SIDE = grid("""
....IJJJJI
...HJJKKKJH
..GHJJKKKKHG
..GHJKKKKKHG
..GHJKKKKJHG
..GHJKKKKJHG
..GHJKKKKJHG
.GHJKKKKJHG
.GHJKKKJJHG
.GHJJKKJJHG
GHJKKKJJJHG
HJKLLLKKJH
HJKLLKKKJH
HIJKKKJJIHdddddddddddddddd
.HHHHdeeeeeeeeeeeeeeeeeeeeed
....deeffffffffeeeeeeeeeeffed
....deeeeeeeeeeeeeeeeeeeeeeed
.....ddeeeeeeeeeeeeeeeeeedddc
.......ddddddddddddddddddccc
""", 30)

# side view: the right arm hanging (0), swung forward (F), swung back (B)
ARM_SIDE_0 = grid("""
...JJKKJJ
..JJKKKKJJ
.HJKKKKKJIH
.HJKKKKJJIH
.HJKKKJJJIH
.HJKKKJJJIH
.HJKKJJJJIH
.HJKKIIJJIH
.HJKJJIIJIH
.HJKJJJJIIH
.HJJJJJJIIH
.IKLLLLKKJI
.IKLLLKKKJI
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
...JJKKJJ
..JJKKKKJJ
.HJKKKKKJIH
.HJKKKKJJIH
.HJKKKJJJIH
.HJKKKJJJIH
..HJKKJJJJIH
..HJKKJJJJIH
..HJKJJJJJIH
...HJJJJJJIIH
...HJJJJJJIIH
...IKLLLLKKJI
4|IKLLLKKKJI
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
10|JJKKJJ
9|JJKKKKJJ
8|HJKKKKKJIH
8|HJKKKKJJIH
8|HJKKKJJJIH
8|HJKKKJJJIH
7|HJKKJJJJIH
7|HJKKJJJJIH
7|HJKJJJJJIH
6|HJJJJJJIIH
6|HJJJJJJIIH
6|IKLLLLKKII
5|IKLLLKKKJI
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

for _m in (HEAD_FRONT, HEAD_BACK, BODY_FRONT, BODY_BACK):
    for _r in _m:
        assert len(_r) == 64, (len(_r), _r)


# ------------------------------------------------------------------ frames (v1's motion, x2)

from npc_pixmap import Fig, t_darker, t_far, t_mirror, v1_back_pose  # noqa: E402

SIDE_LEGS = {(0, 0): LEG_SIDE_p0_0, (3, 0): LEG_SIDE_p3_0, (-3, 0): LEG_SIDE_m3_0, (3, 1): LEG_SIDE_p3_1,
             (-3, 1): LEG_SIDE_m3_1, (0, 2): LEG_SIDE_p0_2}
HANG = {0: ARM_SIDE_0, 1: ARM_SIDE_F, -1: ARM_SIDE_B}
BODY_TOP = 44
# breathing in lifts the chest by 2 (v1: 1 px). The cut is inside 4 or more repeated rows (no button there),
# above the vest's hem and the belt: front / back at body row 28, side at row 26.
CUT_FRONT, CUT_SIDE = 28, 26


def _body(f, rows, B, U, half_mirror, cut):
    f.stamp(rows[cut - 2:], 0, BODY_TOP + cut - 2 + B, LEG, part="body", half_mirror=half_mirror)
    f.stamp(rows[:cut], 0, BODY_TOP + B + U, LEG, part="body", half_mirror=half_mirror)


def _purse(f, x, y, glint):
    f.stamp(PURSE, x, y, LEG, part="purse")
    if glint is not None:  # the clasp catches the light
        f.stamp(["ll"], x + 2 + glint, y + 4, LEG, part="purse")


def front(p, back=False):
    f = Fig(RAMPS)
    B, U = 2 * p.bob, -2 * p.breath
    legmap = LEG_BACK if back else LEG_FRONT
    for (fwd, lift), x0, flip in ((p.near, 16, False), (p.far, 36, True)):
        yv1 = min(55, 55 - lift + (1 if fwd > 1 else 0))
        bottom = 111 - 2 * (55 - yv1)
        f.stamp(legmap, x0, bottom - len(legmap) + 1, LEG, part="leg", flip=flip,
                tone=t_mirror if flip else None)
    _body(f, BODY_BACK if back else BODY_FRONT, B, U, True, CUT_FRONT)
    ay = 50 + B + U
    top = 8 + B + U
    if not back:  # his right arm is image left
        _purse(f, 4, 74 + B, p.glint)
        f.stamp(ARM_DOWN, 10, ay - 2 * max(0, p.arm_near), LEG, part="arm")
        f.stamp(BOOK_FRONT, 34, 56 + B + U, LEG, part="book")
        f.stamp(ARM_BOOK, 44, ay, LEG, part="arm", flip=True, tone=t_mirror)
        f.stamp(PEN_FRONT, 4, top + 8, LEG, part="pen")
        f.stamp(HEAD_FRONT, 0, top, LEG, part="head", half_mirror=True)
    else:
        _purse(f, 50, 74 + B, p.glint)
        f.stamp(ARM_DOWN, 44, ay - 2 * max(0, p.arm_far), LEG, part="arm", flip=True, tone=t_mirror)
        f.stamp(ARM_BOOK, 10, ay, LEG, part="arm", tone=t_darker)
        f.stamp(HEAD_BACK, 0, top, LEG, part="head", half_mirror=True)
    return f.finish()


def _side_leg(f, pose, tone):
    rows = SIDE_LEGS[pose]
    lift = pose[1]
    sole = 111 - 2 * lift - (2 if lift > 1 else 0)
    f.stamp(rows, 16, sole - len(rows) + 1, LEG, part="leg", tone=tone)


def _hang_arm(f, ay, swing, tone=None):
    k = (swing > 0) - (swing < 0)
    f.stamp(HANG[k], 23 - (7 if k < 0 else 0), ay, LEG, part="arm", tone=tone)  # B is drawn 7 to the right


def _book_arm(f, ay, tone=None, book_tone=None):
    f.stamp(BOOK_SIDE, 48, ay + 6, LEG, part="book", tone=book_tone)
    f.stamp(ARM_BOOK_SIDE, 21, ay, LEG, part="arm", tone=tone)


def side(p, swap=False):
    f = Fig(RAMPS)
    B, U = 2 * p.bob, -2 * p.breath
    ay = 50 + B + U
    top = 8 + B + U
    _side_leg(f, p.far, t_far)
    if swap:  # facing left: the purse and the hanging arm are on the far side
        _purse(f, 22, 74 + B, None)
        _hang_arm(f, ay, p.arm_far, tone=t_far)
    else:
        _book_arm(f, ay, tone=t_far, book_tone=None)  # v1: the far book is not darkened
    _body(f, BODY_SIDE, B, U, False, CUT_SIDE)
    _side_leg(f, p.near, None)
    f.stamp(HEAD_SIDE, 0, top, LEG, part="head")
    f.stamp(["**"], 36 + 2 * p.glint, top + 16, LEG, part="head")  # light moving across the lens
    if swap:
        _book_arm(f, ay)
    else:
        _purse(f, 18, 74 + B, p.glint)
        _hang_arm(f, ay, p.arm_near)
        f.stamp(PEN_SIDE, 25, top + 5, LEG, part="pen")
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
