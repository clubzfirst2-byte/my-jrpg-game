"""朽ち根のヌシ (boss_root), v3: the BODY's hand-drawn maps (pixmap.py syntax).

The body is a hunched mass of dead roots seen from the front: five thick roots lie across each half
like shingles (S1 the arch of the back .. S5 the belly), one root runs down each flank (V1), and the
dark rot between them shows where they part (UNDER). Every map is the image-LEFT half; the right half
is its mirror, one step darker in the lights.

Legend:  a-g rotwood   h-n rotwood_d (wet dark rot)   o-u rotwood_p (dry pale root)
         A-G fungus    H-N bone    O-U murk    V W X Y Z $ % glow
A root that runs sideways is typed in COLUMNS (cols=True): each line is one column, top to bottom =
the root's cross-section (lit on top). An upright root is typed in rows (lit on the left).
Positions (the map's top-left in the 192 x 160 frame) are in PLACE.
"""

# the dark rot between the roots: one flat tone, the silhouette of the mass (rows 36..104, columns
# typed in frame coordinates, to the centre line at column 95)
UNDER = """
75|h(i20)
71|h(i24)
68|h(i27)
65|h(i30)
63|h(i32)
60|h(i35)
58|h(i37)
56|h(i39)
55|h(i40)
53|h(i42)
52|h(i43)
50|h(i45)
49|h(i46)
48|h(i47)
47|h(i48)
46|h(i49)
45|h(i50)
44|h(i51)
43|h(i52)
42|h(i53)
42|h(i53)
41|h(i54)
40|h(i55)
40|h(i55)
39|h(i56)
39|h(i56)
39|h(i56)
39|h(i56)
38|h(i57)
38|h(i57)
38|h(i57)
38|h(i57)
38|h(i57)
38|h(i57)
38|h(i57)
38|h(i57)
39|h(i56)
39|h(i56)
39|h(i56)
39|h(i56)
40|h(i55)
40|h(i55)
41|h(i54)
42|h(i53)
42|h(i53)
43|h(i52)
44|h(i51)
45|h(i50)
46|h(i49)
47|h(i48)
48|h(i47)
49|h(i46)
50|h(i45)
52|h(i43)
53|h(i42)
55|h(i40)
56|h(i39)
57|h(i38)
58|h(i37)
59|h(i36)
61|h(i34)
63|h(i32)
64|h(i31)
66|h(i29)
68|h(i27)
71|h(i24)
74|h(i21)
77|h(i18)
82|(h14)
"""

# S1: the arch of the back, columns 44..95 (rotwood). Grain lines along it, a crack from the top at 66, a knot at 73.
S1 = """
17|aafdba
16|aggddba
15|aggfddba
14|aggfdddba
13|aggfddbbba
12|aggffdbbdba
12|aggffdbbddba
11|aggffddbbddba
10|aggffddbbddba
10|affffdddbbdba
9|afffddddddbbba
8|aggfeeeedddbba
8|aggfeeeedddbba
7|aggfeeeedddbba
7|aggfeeeebbdbba
6|aggfeeeebbdbba
6|aggfeeeebbddba
6|afffeeeebbddba
5|afffeeeeddddbba
5|afffeeeeddddbba
4|aggfeeeedddcccba
4|aggfeeeedddcccba
4|aggbeeeedddcccba
3|aggfbbeeedddcccba
3|aggffbbeedddcccba
3|aggffeeeedddcccba
2|aggffeeeedbbcccba
2|affffeeeedbbcccba
2|affffeeeedbbcccba
2|afffeeeeedbfbcbba
1|aggffeeeeedbbcccba
1|aggffeeeeedddcccba
1|aggffeeeeedddcccba
1|aggffeeeeedddcccba
1|aggffeeeeebbdcccba
1|aggffeeeeebbdcccba
0|agggffeeeeebbdcccba
0|agggffeeeeebbdcccba
0|aggfffeeeedbbdcccba
0|aggfffeeeedddbcccba
0|aggfffeeeedddbcccba
0|affffeeeeedddbcccba
0|affffeeeeeddbbcccba
0|aggffeeeeedddbbccba
0|aggffeeeeedddbcccba
0|aggffeeeeeddddcccba
0|aggffeeeeedbbdcccba
0|aggffeeeeedbbdcccba
0|aggffeeeeedbbddccba
0|affffeeeeedbbddccba
0|affffeeeeeddddbccba
0|affffeeeeeddddbccba
"""

# S2: the second root, columns 42..80 (pale dry root). Seams at 50, 61, 72; a split along 64..70.
S2 = """
20|ootpo
19|ouurpo
18|ouurrpo
17|ouutrrpo
16|ouutrrrpo
15|ouutrrrrpo
14|ouuttrrrrpo
14|ouuttrrrrpo
13|ouutrrpprrpo
12|ouuttttrrrrpo
12|ouutssssrrrpo
11|ouutssssrrrpo
10|ouutssssrrrppo
10|otttssssrrrppo
9|otttssssrrrrpo
9|ouutssssrrrrpo
8|ouutssssrrrrpo
8|ouutssssrrrrpo
7|ouutssssrrrrppo
7|otttssssrpprppo
6|ouuuttttrrrrrppo
6|ouuttssssrrrrppo
6|ouuttsssoprrrrpo
5|ouuttsssoputrrrpo
5|otttsssstoputrrpo
4|otttssssstoprrrpo
4|ouutsssssstoprrpo
4|ouutssssssrrorrpo
3|ouutssssssrrrrrpo
3|ouutssssssrrrrppo
3|otttssssssrppppo
2|ouuuuttttrrrrrppo
2|ouuttssssrrrrrppo
2|ouuttssssrrrrrppo
2|ouuttssssrrrrrppo
1|ouuttssssrrrrrrppo
1|otttsssssrrrrrrppo
1|otttsssssrrrrrrpoo
1|ooooooooooooooooo
"""

# S3: the third root, columns 40..80 (rotwood, in the shade of the back). Seams at 51, 63, 74.
S3 = """
22|aadba
21|affdba
20|affddba
19|affdddba
18|affddddba
17|aggfddddba
16|aggfdddddba
15|aggfddddddba
14|aggfddddddbba
14|aggffdddddbba
13|aggffddddddbba
12|afffdddbbddbba
12|aggfffdddddbba
11|aggffdddcccbba
10|aggffdddcccbba
10|affffdddcccbba
9|affffdddcccbbba
9|afffddddcccbbba
8|afffdbbdcccbbba
8|aggfdbbdcccbbba
7|aggfddbbdcccbbba
7|aggfdddddcccbbba
6|aggffddddcccbbba
6|afffddbbdcccbbba
5|aggffffddddbbbbba
5|aggffddddcccbbbba
4|aggffddddcccbbbba
4|affffddddcccbbbba
4|affffddddcccbbbba
3|afffdddddcccbbbba
3|afffdddbbcccbbbba
3|aggfddbfbcccbbbba
2|aggfdddbbdcccbbbba
2|aggfddddddcccbbbba
2|afffdddbbdcccbbbba
2|aggfffdddddbbbbbba
1|aggfffddddcccbbbba
1|aggffdddddcccbbbba
1|aggffdddddcccbbbba
1|affffdddddcccbbaaa
1|aaaaaaaaaaaaaaaa
"""

# S4: the fourth root, columns 44..95 (rotwood, under the chest). Seams at 54, 67, 81.
S4 = """
23|aadba
22|affdba
21|affddba
20|affdddba
19|affddddba
18|affdddddba
17|affddddddba
16|affdddddddba
15|aggfddddddbba
14|aggfdddddddbba
14|affdddbbdddbba
13|aggfffdddddbba
12|aggffdddcccbba
12|aggffdddcccbba
11|afffddddcccbbba
10|afffddddcccbbba
10|afffddddcccbbba
9|afffdddbcccbbbba
9|afffddbbcccbbbba
8|aggfdddbbcccbbbba
8|aggfdddddcccbbbba
7|aggfdddddcccbbbba
7|aggffddddcccbbbba
6|afffddbbdccccccbba
6|aggffffddddbbbbbba
5|aggffdddddcccbbbba
5|aggffdddddcccbbbba
4|affffdddddccccccbba
4|affffdddddccccccbba
4|afffddddddccccccbba
3|afffdddddddccccccbba
3|afffdddddddccccccbba
3|aggfdddddddccccccbba
2|aggfddddddddccccccbba
2|aggfddddddddccccccbba
2|aggffdddddddccccccbba
2|aggffdddddddccccccbba
2|afffdddbbddccccccbbba
2|aggffffddddddbbbbbbba
2|aggffddddddccccccbbba
2|aggffddddddccccccbbba
2|affffddddddccccccbbba
2|affffdddbbdccccccbbba
2|afffdddbfbbccccccbbba
2|afffddddbbdccccccbbba
2|aggfdddddddccccccbbba
2|aggfdddddddccccccbbba
2|aggfdddddddccccccbbba
2|aggffddddddccccccbbba
2|aggffddddddccccccbbba
2|afffdddddddccccccbbba
2|afffdddddddccccccbbba
"""

# S5: the belly root, columns 50..95 (wet dark rot); its lower edge is the body's lower edge.
S5 = """
0|hhlkih
1|hmmkkih
2|hmmkkkih
2|hmmlkkkih
3|hmmlkkkiih
4|hmmlkkkkiih
5|hmmlkkkkiih
6|hmmllkkkiiih
6|hmmlkkiiiiih
7|hmmlllkkkiiih
7|hmmllkkkjjjih
8|hmmllkkkjjjih
9|hmmllkkkjjjih
9|hmmllkkkjjjih
10|hmmllkkkjjjih
10|hllllkkkjjjih
11|hllllkkkjjjih
11|hlllkkkkjjjih
11|hlllkkiijjjih
12|hmmlkkiikjjih
12|hmmlkkkiijjih
13|hmmlkkkkjjjih
13|hlllkkiijjjih
13|hmmlllkkkiiih
14|hmmllkkkjjjih
14|hmmllkkkjjjih
14|hmmllkkkjjjih
14|hllllkkkjjjih
15|hllllkkkjjjih
15|hlllkkkkjjjih
15|hlllkkkkjjjih
15|hmmlkkkkjjjih
16|hmmlkkkkjjjih
16|hmmlkkkkjjjih
16|hlllkkiijjjih
16|hmmlllkkkiiih
16|hmmllkkkjjjih
16|hmmllkkkjjjih
16|hllllkkkjjjih
16|hllllkkkjjjih
16|hlllkkkkjjjih
16|hlllkkkkjjjih
16|hmmlkkkkjjjih
16|hmmlkkkkjjjih
16|hmmlkkkkjjjih
16|hmmlkkkkjjjih
"""

# V1: the root down the flank, rows 50..88 (pale dry root), typed in rows; lit on its left.
V1 = """
9|ooto
8|outpo
7|ouurpo
6|ouurrpo
5|ouutrrpo
5|ouutrrrpo
4|ouutrrrpo
3|ouuttrrrpo
2|ouuttrrrrpo
2|ouutsssrrrpo
1|ouutsssrrrpo
1|ouutsssrrrrpo
1|ouutsssrrrrpo
1|otttsssrpprpo
0|ouuuttttrrrrpo
0|ouuttsssrrrrpo
0|ouuttsssrrrrpo
0|ouuttsssrrrrpo
0|ouuttsssrorrpo
0|otttssssroprpo
0|otttssssrroppo
0|otttssssrrrppo
1|ouutsssrrrrppo
1|ouutsssrrrrppo
1|otttsssrpprpo
1|ouuuttttrrrpo
2|ouuttsssrrrpo
2|ouuttsssrrrpo
3|ouuttsssrrpo
4|otttsssrrrpo
4|otttsssrrppo
5|otttsssrrpo
6|ouutsssrrpo
7|ouutssrrpo
8|ouuttrrppo
9|ouutrrppo
10|otttrrpo
11|ottrrpo
12|oopppo
"""

# frame positions of the maps' top-left (left half); the right half mirrors about the centre line
PLACE = {"UNDER": (0, 36), "S1": (44, 34), "S2": (42, 44), "S3": (40, 54), "S4": (44, 63), "S5": (50, 77),
         "V1": (34, 50)}
COLS = {"S1", "S2", "S3", "S4", "S5"}
ORDER = ("UNDER", "S1", "S2", "S3", "S4", "S5", "V1")  # the lower roots are nearer: each lies over the one above
