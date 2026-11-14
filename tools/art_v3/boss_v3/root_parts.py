"""朽ち根のヌシ (boss_root), v3: the hand-drawn maps of everything but the body (pixmap.py syntax).

Legend:  a-g rotwood   h-n rotwood_d (wet dark rot)   o-u rotwood_p (dry pale root)
         A-G fungus    H-N bone    O-U murk    V W X Y Z $ % glow
HALF maps are the image-left part (mirrored for the right, one step darker in the lights); the others
are drawn whole. Positions are the top-left in the 192 x 160 frame in the rest pose (PLACE).
"""

# ---------------------------------------------------------------- back spikes (behind the body)
# dead roots standing out of the back: a dry pale tip, grain lines, the lit side on the left

SPK_C = """
7|ooo
6|outpo
6|ouurpo
6|outrpo
5|outrrpo
5|ouutrpo
5|outtrppo
4|ouutrrpo
4|outtrrppo
4|ouuttrrpo
3|outtrrrppo
3|aggfddbbba
3|agffdddbba
3|agffddbdba
3|agffdddbba
3|aggfdbdbba
3|aggfdbddbba
3|agffddbdbba
2|agffdddbdbba
2|aggfddddbbba
2|aggffdddbbba
2|agfffdddbdbba
1|agffdddddbbbba
1|aggfbdddddbbba
1|aggfbddddbdbba
1|agffdbdddbdbbba
1|agffdbddddbbbba
0|aggffdbdddddbbba
0|aggfdddbdddbbbba
0|agfffddbddddbbbba
0|agffddddbdddbbbba
0|aggfdddddbddbbbba
0|aggffddddbdddbbba
0|agfffdddddbdbbbba
0|agffddbdddddbbbba
0|aggfddbddddbbbbba
0|aggffddbdddbdbbba
0|agfffdddbdddbbbba
0|agffdddddbddbbbba
0|aggfddddddbdbbbba
0|aggffdddddbbbbbba
0|agfffddddddbbbbba
0|agffdddddddbbbbba
0|aggfddddddddbbbba
"""

SPK_1 = """
5|ooo
5|outo
5|ouupo
4|outrpo
4|ouurpo
4|outrppo
4|outtrpo
3|ouutrrpo
3|outtrrpo
3|outtrrppo
3|ouutrrppo
3|aggfddbba
3|agffddbbba
3|agffdbdbba
3|aggfdbdbba
3|aggfddbdba
3|aggfdddbbba
2|agffdddbdbba
2|agffbdddbbba
2|aggfbddddbbba
2|aggfdbdddbbba
2|agffdbddddbbba
2|agffddbdddbbba
1|aggfdddbdddbbba
1|aggffddbddbbbba
1|agfffdddbddbbbba
1|agffddddbdddbbba
1|aggfdddddbddbbba
1|aggffdddddbdbbba
0|agfffbdddddbdbbba
0|agffdbddddddbbbba
0|aggfddbdddddbbbba
0|aggffddbddddbbbba
0|agfffdddbdddbbbbba
0|agffdddddbddbbbbba
0|aggfddddddbdbbbbba
0|aggffdddddddbbbbba
0|agfffddddddbbbbbba
0|agffdddbddddbbbbba
0|aggfdddbbdddbbbbba
0|aggffdddbdddbbbbba
0|agfffddddddddbbbba
0|agffddddddddbbbbba
"""

SPK_2 = """
3|ooo
2|outo
2|ouupo
2|outrpo
2|ouurpo
2|outtrpo
1|outtrppo
1|ouutrrpo
1|outtrrppo
1|aggfddbba
1|agffdbdba
2|agffddbba
2|agfdbdbba
2|aggfdbdba
2|aggfddbbba
2|agffddbdba
2|agffdddbbba
2|aggfbddbdba
2|aggfbdddbbba
2|agffdbddbdba
2|agffdbdddbbba
2|aggfddbddbbba
2|aggffddbddbbba
2|agfffdddbdbbba
3|agffddddbbdbba
3|aggfddddbdbbbba
3|aggffdddddbbbba
3|agfffddbddbbbba
3|agffdddbdddbbbba
3|aggfddddbddbbbba
4|aggfdddddbdbbbba
4|agffddddddbbbbba
4|agfffddddddbbbba
4|aggfddbddddbbbba
4|aggffdbddddbbbba
4|agfffddbdddbbbba
4|agffdddddddbbbba
"""

SPK_3 = """
1|oo
1|ouo
2|ouo
2|ouro
2|otro
3|otrpo
3|otrpo
3|ouurpo
3|aggdba
4|aggdba
4|affdba
4|affdbba
4|aggdbba
5|aggddba
5|affddbba
5|affdbbba
6|aggdbbba
6|aggddbbba
6|affdddbba
6|affddbbba
7|aggdddbba
7|aggdddbbba
8|affdddbba
8|affddbbbba
9|aggdddbbba
9|aggddddbba
10|affdddbbba
10|affddbbbba
11|aggdddbbba
11|affdddbbba
12|aggfdddbbba
12|aggfdddbbba
13|affddddbbba
13|affdddbbbba
14|aggfdddbbba
14|aggfddddbba
15|affddddbbba
15|affdddbbbba
16|aggfdddbbba
16|aggfdddbbba
17|affddddbbba
"""

# the spike out of each shoulder, typed in COLUMNS from its tip (column 16) to the body (column 50)
SHOULDER = """
0|oo
0|oto
0|oto
0|outo
0|outo
0|outpo
1|outpo
1|ouurpo
1|ouurpo
1|ouurrpo
1|ottrrpo
1|ottrrppo
1|aggddbba
1|aggdddbba
2|aggdddbba
2|aggfdddbba
2|affddddbba
3|affddbbbba
3|afffdbbdbba
3|aggfdbbdbba
3|aggfddddbbba
4|aggfddddbbba
4|aggffddddbbba
5|afffdddddbbba
5|afffdddbbdbbba
6|afffddbbddbbba
6|aggfdddbbddbbba
6|aggfdddddddbbba
7|aggffdddddddbbba
7|aggffdddddddbbba
7|afffddddddddbbbba
8|afffddddddddbbbba
9|afffddddddddbbbba
9|aggfddddddddbbbba
9|aggfddddddddbbbba
"""

# ---------------------------------------------------------------- front legs (behind the body)
# one bent root from the shoulder out to the knee and down to three root toes with dry pale tips;
# a grain line twists down it, a knot sits on the knee. Rows 80..159, origin column 8.

LEG = """
40|aggffeeeeedddddddcccccbbbbba
39|aggffeeeeedddddddcccccbbbbba
38|aggffeeeeedddddddcccccbbbbba
38|aggffeeeeedddddddcccccbbbbba
37|aggffeeeeedddddddcccccbbbbba
36|aggffeeeeedddddddcccccbbbbba
35|aggffeeeeedddddddcccccbbbbba
35|aggffeeeeedddddddcccccbbbbba
34|aggffeeeeedddddddcccccbbbbba
33|aggffeeeeeddbbdddcccccbbbbba
33|aggffeeeeedddbbddcccccbbbbba
32|aggffeeeeedddbbddcccccbbbbba
31|aggffeeeeeddddbbcccccbbbbba
30|aggffeeeeeddddbbcccccbbbbba
30|affffeeeeedddddbcccccbbbbba
29|affffeeeeeddddddcccccbbbbba
28|aggffeeeeeddddddcccccbbbba
28|aggffeeeeeddddddcccccbbbba
27|aggfbbeeeeddddddcccccbbbba
26|aggfbbeeeeddddddcccccbbbba
25|aggffbbeeedddddcccccbbbba
25|aggffbbeeedddddcccccbbbba
24|aggffebbeedddddcccccbbbba
23|aggffeeeeedddddcccccbbbba
23|aggffeeeedddddcccccbbbba
22|aggffeeeedddddcccccbbbba
21|affffeeeedddddcccccbbbba
20|affffeeeeddbbdcccccbbbba
20|aggffeeeeddbbcccccbbbba
19|aggffeeeedbbdcccccbbbba
18|aggffeeeedbfbcccccbbbba
18|aggffeeeeddbbcccccbbbba
17|aggffeeeeddddccccbbbba
17|aggffeeeeddddccccbbbba
17|aggffeeeeddddccccbbbba
16|afffeeeeeddddccccbbbba
16|afffeeeeeddddccccbbbba
16|aggfeeeedddddcccbbbba
16|aggfeeeedddddcccbbbba
15|aggfeeeeddbbdcccbbbba
15|aggfeeeeddbbdcccbbbba
15|aggfeeeedddbbcccbbbba
15|aggfeeeedddbbcccbbbba
15|aggfeeeedddbcccbbbba
14|aggfeeeeddddcccbbbba
14|afffeeeeddddcccbbbba
14|afffeeeeddddcccbbbba
14|aggfeeeeddddcccbbbba
14|aggfeeeeddddcccbbbba
13|aggfeeeedddcccbbbba
13|aggfeeeedddcccbbbba
13|aggfeeeedbbcccbbbba
13|aggfeeeedbbcccbbbba
13|aggfeeeeddbcccbbbba
12|aggfeeeeddbcccbbbba
12|aggfeeedddcccbbbba
12|afffeeedddcccbbbba
12|afffeeedddcccbbbba
12|aggfeeedddcccbbbba
11|aggfeeedddcccbbbba
11|aggfeeedddcccbbbba
11|aggfeeedddcccbbba
11|aggfeeedddcccbbba
11|aggfeeedddcccbbba
11|aggfeeedddcccbbba
10|aggfeeedddcccbbba
10|aggfeeedddcccbba
9|aggffddddddddbbbba
8|aggffddddddddddbbbba
7|aggffdddbbdddddbbbbbba
5|aggfdddbbfdddddbbfddddbba
5|aggfdddbafdddddbafddddbba
4|aggfddba..afdddba..afdddbba
4|aggfddba..afdddba..afdddbba
3|aggddba....afdddba....afddbba
3|aggddba....afdddba....afddbba
2|ottrpo......otrrrpo.....otrrppo
2|ottpo........otrpo.......otrppo
2|otto..........oto.........otppo
2|ooo...........ooo..........ooo
"""

# a thin dry root winding down the outside of the front leg (rows 88..147, the leg's origin column): it
# swells into a knot, ends, and comes out from under the bark again three rows lower
VINE = """
31|ooo
29|outpo
29|ouutpo
28|outrpo
27|outtrpo
26|ouutrpo
26|outrrpo
25|outtrpo
24|outtrppo
24|ouutrpo
23|outrrpo
22|outtrpo
21|ouutrppo
21|outrrpo
20|outtrpo
19|outtrrpo
19|ouutrpo
18|outrppo
17|oupprpo
16|outprrpo
16|ouutrpo
15|outttrpo
14|ouuttrrpo
13|outttrrppo
13|ouutprrrpo
13|outtrrrppo
13|ouuttrrpo
12|outtrrppo
12|ouutrpo
12|outrpo
12|oupo
12|oo
.
.
11|oo
11|oupo
10|outrpo
10|ouutrpo
10|outtrppo
10|ouutrrpo
10|outtrpo
9|ouuttrpo
9|outtrrpo
9|ouutrppo
9|outrrpo
9|outtrpo
8|ouuttrpo
8|outtrrppo
8|ouutrrpo
8|outtrpo
8|outrppo
7|ouuttrpo
7|outtrrpo
7|ouutrpo
7|outrrppo
7|outtrpo
7|ouurpo
6|outtrppo
6|oottrpo
7|ooooo
"""

# a wet dark root down the inside of the front leg's lower half (rows 118..148, the leg's origin column)
VINE2 = """
36|hh
35|hmih
35|hmkih
34|hmkkih
34|hmmkiih
33|hmkkkih
33|hmmkkiih
32|hmkkikih
32|hmmkkkih
31|hmkkkiih
31|hmmkikkih
31|hmkkkkih
30|hmmkkkiih
30|hmkkikkih
30|hmmkkkih
29|hmkkkkiih
29|hmmkikkih
29|hmkkkkih
28|hmmkkkiih
28|hmkkkikih
28|hmmkkkih
27|hmkkikiih
27|hmmkkkkih
27|hmkkkiih
26|hmmkikkih
26|hmkkkkih
26|hmmkkiih
25|hmkkkih
25|hmkiih
26|hmih
26|hh
"""

# the front leg swung out to the side (rearing, half way), typed in COLUMNS from the toes (column 8)
# to the shoulder (column 56): three toes, the forearm, the elbow knot, the upper root
LEG_OUT = """
26|ooo
13|ooo(.9)otrpo
13|otpo(.8)otrpo(.8)ooo
14|otpo(.7)ouupo(.7)otpo
14|otrpo(.6)outpo(.6)otrpo
15|afdba(.5)agdba(.5)afdba
16|agdba(.3)aggdba(.5)afdba
16|aggdba..agffdba...afddba
17|agfdba.aggfdba..aggdba
18|agfdbbgfdddbbgfddbba
18|aggfdbgffddbbfdddba
19|aggfddbfdddbfddba
19|aggfddddddddbbba
19|agffdddddbddbbbba
20|agffddddbbdddbbba
21|aggfdddbbdddddbbba
21|aggffdbbddddddbbba
22|agffdbbddddddddbbba
23|agffbbdddddddddbbbba
23|aggfbddddddddddcccbba
24|aggffeeeeddddddcccbbba
23|agfffeeeeedddddcccbbba
22|agfffeeeeeddbddcccbbba
21|aggffeeeeedbfbdcccbba
20|aggffeeeeeddbdcccccba
20|agfffeeeeedddddcccbba
19|agfffeeeeeddddbccccba
18|aggffeeeeedddbbccccba
17|aggffeeeeedddbbdccccba
16|agfffeeeeeddbbddccccba
15|agfffeeeeedbbdddcccbba
14|aggffeeeeebbddddcccbba
13|aggffeeeebbdddddcccccba
13|agfffeeeebdddddddccccba
12|agfffeeeeedddddddcccbba
11|aggffeeeeeddddddcccccba
10|aggffeeeeeddddbddcccccba
9|agfffeeeeedddbbddccccbba
8|agfffeeeeeddbbdddccccbba
7|aggffeeeeedbbddddcccccba
6|aggffeeeeebbddddddccccbba
6|agfffeeeeebdddddddcccccba
5|agfffeeeeeddddbfbdccccbba
4|aggffeeeeedddddbddcccccba
3|aggffeeeeeddddddddcccccbba
2|agfffeeeeeddddddddccccbbba
3|aagffeeeedddddddccccbaa
6|aaaffeeeedddcccbaaa
9|aaaaaaaaaaaaa
"""

# the front leg raised above the shoulder (rearing): the upper root out to the elbow, the forearm up,
# the three toes clawing upward. Rows 28..86, origin column 8.
LEG_UP = """
16|ooo
8|ooo(.4)ouupo(.4)ooo
8|otpo(.3)outpo(.3)otpo
8|outpo(.2)ottpo(.2)otrpo
9|agdba.aggda..afdba
9|affbaagfddbaagdba
10|agdbbgffddbbfdba
10|agfdbgfdbddbfdba
10|aggfdbfddbdfddba
9|aggffddbdddddbbba
9|aggffeeeedddcccba
9|aggfeeeeddbdcccba
9|agffeeeedddbcccba
9|agffeeeeddddbccba
9|aggfeeeedddddbbba
9|aggffeeeddddcccbba
9|agffbeeedddddccbba
9|agffbbeeddddcccbba
9|aggffbbedddddcccba
9|aggfffbbdddddcccba
9|agffeeebbddddcccba
9|agffeeeebbdddcccba
9|aggfeeeedbbddcccbba
9|aggffeeeddbbdcccbba
10|agffeeedddbbccccba
10|agffeeeddbfbccccba
10|aggfeeeddbbbdcccbba
10|aggffeeedddddcccbba
10|agfffeeeddddccccbba
10|agffeeeedddbdcccbba
10|aggfeeeeddbddcccbba
10|aggfeeeedbdddcccbba
10|aggfeeeebddddcccbbba
10|agffeeebdddddcccbbbba
11|agffeebddddddccccbbba
11|aggfebdddddddccccbbbba
11|aggfeedddddddcccccbbbbaa
11|agffeeddddbdddcccccbbbbbaaaa
12|agffedddddbbddddddffffgggggaaaaa
12|agffeddddddbbdddddddffffffggggggggaaaaa
12|aggfedddddddbbdddddddeeeeefffffffggggggaaaaaaaaa
12|aggfe(d9)bb(e12)(f10)(g10)ga
13|agffe(d10)bb(e13)(f12)(g6)fa
13|agffd(d11)bbb(e14)(f14)fda
14|agfd(d13)bbb(e16)(f10)dda
14|aggfd(d13)bbbb(e18)(f6)dba
15|agfd(d15)bbbb(e12)(d10)dba
16|agfd(d17)bbbbb(e6)(d12)bba
17|agfd(d19)(b6)(d14)bba
18|aggd(d10)bfb(d8)(b7)(d10)bba
19|agfd(d9)bbb(d12)(b7)(d6)bba
20|agfd(d16)(c12)(b6)ddbba
21|agfd(d12)(c16)(b7)bba
22|agfd(d8)(c20)(b6)bba
24|agfd(d5)(c21)(b6)bba
25|agfddd(c20)(b9)bba
27|aafd(c18)(b11)bba
29|aaf(c14)(b13)baa
31|aaf(c9)(b15)aaa
34|aaa(c4)(b14)aaaa
38|aaaa(b11)aaaa
42|(a12)
"""
PLACE_OUT = (3, 56)
PLACE_UP = (0, 28)

# the hind legs, seen between the front legs: short, thick, in wet dark rot. Rows 73..159.
HIND = """
6|hmlllkkkkkjjjiih
6|hmmllkkkkkjjjiih
6|hmlllkikkkjjjiih
6|hmlllkkikkjjjiih
6|hmlllkkkikjjjiih
6|hmmllkkkkijjjiih
6|hmlllkkkkkjjjiih
6|hmlllikkkkjjjiih
6|hmmlllikkkjjjiih
6|hmlllkkikkjjjiih
5|hmlllkkkikkjjjiih
5|hmmllkkkkikjjjiih
5|hmmllkkkkkkjjjiih
5|hmlllkkkkkkjjjiih
5|hmlllkkikkkjjjiih
5|hmlllkiikkkjjjiih
5|hmmllkiikkkjjjiih
5|hmmllkkikkkjjjiih
5|hmlllkkkkkkjjjiih
5|hmlllkkkkikjjjiih
5|hmlllkkkkiikjjjiih
4|hmmlllkkkkikjjjiih
4|hmmlllkkkkkkjjjiih
4|hmllllkkkkkkjjjiih
4|hmlllkkkkkkkjjjiih
4|hmmllkkikkkkjjjiih
4|hmmlllkkikkkjjjiih
4|hmlllkkkkikkjjjiih
4|hmlllkkkkkikjjjiih
4|hmmllkkkkkkijjjiih
3|hmmlllkkkkkkkjjjiih
3|hmllllkkkkkkkjjjiih
3|hmlllkkkikkkkjjjiih
3|hmmllkkkkikkkjjjiih
3|hmmlllkkkkikkjjjiih
3|hmlllkkkkkkkkjjjiih
3|hmlllkkkkkkkijjjiih
3|hmmllkkkkkkkkjjjiih
2|hmmlllkkkkkkkkjjjiih
1|hmmmmllkkkkkkkkjjjiih
0|hmmmmlllkkiiikkkjjjiih
0|hmmmlllkkikkkikkjjjiiih
0|hmmllllkkikmkikkjjjiiih
0|hmmmlllkkikkkikkjjjiih
1|hmmmlllkkiiikkkjjjiih
2|hmlllkkkkkkkkkjjjiih
2|hmlllkkkkkkkikjjjiih
2|hmmllkkkkkkikkjjjiih
2|hmmlllkkkkikkkjjjiih
2|hmlllkkkkkkkkkjjiiih
2|hmiiikkkkkkkkkjjiiih
3|hmlllkkkkkkjjjiiih
3|hmmllkkkkkkjjjiiih
3|hmmllkikkkkjjjiiih
3|hmlllkkikkkjjjiiih
3|hmlllkkkikkjjjiiih
3|hmmllkkkkikjjjiiih
4|hmlllkkkkkjjjiih
4|hmmllkkkkkjjjiih
4|hmmllkkikkjjjiih
4|hmlllkikkkjjjiih
4|hmlllikkkkjjjiih
4|hmmllkkkkkjjjiih
4|hmlllkkkkikjjjih
4|hmlllkkkikkjjjih
5|hmmkkkkkkjjjiih
5|hmkkkkkkkjjjiih
5|hmmkkkikkjjjiih
5|hmmkkikkkjjjiih
5|hmkkkikkkjjjiih
5|hmkkkkkkkjjjiih
5|hmmkkkkkjjjiih
5|hmmkkkkijjjiih
5|hmkkkkikjjjiih
5|hmkkkkkkjjjiih
5|hmmkkkkkjjjiih
4|hmmkkkkkkkjjjiih
3|hmmkkkkkkkkjjjiiih
2|hmmkkkkkkkkkjjjiiih
1|hmmkkkkkikkkkkjjiiih
0|hmmkkkkikkkkkikkkkiiih
0|hmkkkkkikkkkkikkkkiiih
0|hmkkkkiikkkkiikkkkiiih
0|hmkkkkihkkkkihkkkiiiih
0|hmkkkihhkkkihhkkkiiiih
0|hiiiihhiiiiihhiiiiiiih
1|hhhhh.hhhhhh.hhhhhhhh
"""

# ---------------------------------------------------------------- head (HALF: columns 62..95)
# a low boar head: a pointed ear with a dark inside, three roots down the forehead, a heavy brow of pale
# dry root slanting down to the nose (the eye sits in the dark socket under it), two grooves round the
# cheek, the pale snout disc with its nostril.
# Rows 78..130; the map ends on the mouth line (the chin is JAW).

HEAD = """
0|aa
0|aga
1|aga
1|agfa
1|aggfa
2|aggifa
2|aggiifa
2|aggiiifa
3|aggiiifa
3|aggfiiiifa
3|aggfiiiiffa(.14)aaaaaa
4|aggfiiiiffa(.10)aaagggggg
4|aggfiiiiiiffa(.6)aagggffffff
4|aggfiiiiiiiffa(.3)aaggfffffffff
5|aggfiiiiiiiffbggfffffffffffff
5|aggffiiiiiifdbgffffffbfffffff
5|aggffiiuuifdbffffffffbfffffff
6|aggffittuudbfffffffffbffffff
6|aggfffrrttuuuffffffffffbffff
6|aggffdpprrtttuufffffffffffff
7|aggfdffpprrrttuuuffffffffff
7|aggffffbbppprrtttuuffffffff
8|aggfffffbbapppppttuuffffff
9|aggffffffbaaaaaapptuuffff
6|aggffffffffbaaaaaaaappttuuff
5|aggfffffffffbaaaaaaaaaappttff
5|aggfffffffffbaaaaaaaaaaaappff
4|aggffffffffffbaaaaaaaaaaaabbff
4|aggfffffffffffbaaaaaaaaaabffff
4|agggffffffffffbbbbbbbbbbbbffff
4|agggfffffffffffggggggggggfffff
4|aggffffffffbbfffffffffffffffff
5|aggffffffffbbffffeeeeeeeeefff
5|aggbbfffffffbbfffeeeeeeeeefff
6|aggbbfffffffbbffeeeeeeeeefff
7|agfbbbffffffbbfeeeeeeeeefff
8|agffbbddddddbbeeeeeeeeefff
9|agffdbbdddddbbeeeeeeeefff
10|affddbbdddddddbbbbbbbbbb
12|afddbbddddddbpuuuuuuuu
13|afddddddddbpuuttttsss
14|afddddddbputtttttsss
16|addddbputttttttsss
17|adddbputttpoooprr
18|addbpttttooooprr
19|adbpttttooooprr
20|abptttttpooprr
20|abpptttttrrrrr
21|abprtttttrrrr
21|abpprrrrrrrrr
22|abpprrrrrrrr
22|aapppppppppp
23|aaaaaaaaaaa
"""

# the neck (whole map, columns 74..117, rows 92..128): a bundle of four roots of different thickness
# twisting round each other between the chest and the head (wet rot, wood, wood, a thin dry root);
# the chest's shadow lies on its top rows. Seen when the head drops for the charge.
NECK = """
2|hiiiiiiiiabbbbbbbbbbbbabbbbbbbbbboppppppo
2|hkjjjiiiiafdddbbbbbbbbafddbbbbbbbotrppppo
1|hmkkjjjiiiafdddddbbbbbaffdddbbbbbbottrrpppo
1|hmlkkkjjjiiagfdddddbbbaffdddddbbboutrrrpppo
1|hmllkkkjjjiagffdddddbbafffddddbbbouttrrrppo
0|hmmlllkkjjjiagffddddbbaggfddddddbbouutrrrppo
0|hmmlllkkkjjjiagfdddbbbaggfddbddddbouttrrpppo
0|hmmlllkkikjjiagfddbbbagffddbdddbbottrrrpppo
0|hmlllkkkiijjiaffddbbbagffdddbddbbottrrrrppo
1|hmlllkkkkijiaffdddbbafffdddbdbbboutrrrrppo
1|hmmllkkkkjiagfdddbbagfffdddddbbboutrrrppo
1|hmmlllkkkjiagfddbbbaggffddddddbbboutrrppo
2|hmlllkkkjiagffdbbbagfffdddbdddbbottrrppo
2|hmllkkkjiagffddbbbbagfffddbbddbbottrpppo
2|hmllkkjjiaggfdddbbbafffdddbfbddbbotrrpppo
2|hmlkkkjjiaggfddddbbbafffdddbbdbbbotrrrppo
3|hmlkkjiagffddddbbbbagffddddddbbboutrrppo
3|hmkkkjiagffdddddbbbbagffdddddbbbboutrrrpo
3|hmkkjjiafffdddbddbbbaggfdddddbbbbouttrrpo
2|hmmkkkjiafffddbbdddbbbaggfddddbbbbouutrrpo
2|hmmlkkkjiagffddbdddbbbagffddddbbbbouttrpo
2|hmllkkijiagfddddddbbbbaffddddbbbbouttrrpo
1|hmmlllkkkjiaggfdddddbbbbaffdddbbbbottrrppo
1|hmmlllkkjjiaggffddddbbbbagfdddbbbbottrrpo
1|hmlllkkkkjjiagfffddddbbbagfddbbbbotrrrppo
1|hmlllkkikjjiafffddddbbbaggfddbbbbotrrpppo
2|hmllkkiikjiaffddddbbbbaggfdddbbbottrpppo
2|hmmllkkkikjiagffdddbbbagfdddbbboutrpppo
3|hmmllkkkkjiagffddbbbagffdddbbboutrrppo
3|hmlllkkkjjiagfdddbbbafffdddbbbouurrppo
3|hmllkkkjjiaffdddbbbafffddddbbboutrrpo
4|hmlkkkjjiaffddbbbbagffdddddbbbotrrpo
4|hmlkkjjiiagfddbbbbagffddddbbbbotrpo
5|hmkkjiiagfdddbbbbbagfddddbbbbotppo
5|hmkjjiiafddddbbbbbaffdddbbbborrpo
6|hkkjiiafdddbbbbbbafddbbbbbborppo
7|hiiiiabbbbbbbbbbabbbbbbbbooooo
"""

# the chin (HALF, columns 83..95, rows 129..137): it drops when the mouth opens
JAW = """
0|abbbbbbbbbbbb
0|abddddddddddd
1|abffdddddddd
2|abfdddddddd
3|abdddddddd
4|abbdddddd
6|abbbbbb
8|aabbb
10|aaa
"""

# the inside of the mouth (HALF, columns 85..95, rows 124..136): murk, seen only when the chin drops
MOUTH = """
0|O(P10)
0|O(P7)QQQ
0|O(P6)QQQQ
0|O(P5)(Q5)
0|OP(P5)QQQP
1|O(P9)
1|O(P5)QQQP
1|OP(P8)
2|O(P8)
2|O(P8)
3|O(P7)
4|O(P6)
5|(O6)
"""

# the left tusk (mirrored for the right): out of the side of the snout, down and out, then up to a
# point, free of the body. Rows 101..138, origin column 43.
TUSK = """
3|aa
2|HMKH
2|HNMKH
2|HNMKH
1|HNNKIH
1|HNNKKIH
1|HNNMKIH
1|HNNMKKIH
1|HNNMKKIH
0|HNNMKKKIH
0|HNNMMKKIH
0|HNNMMKKIIH
0|HNNMMKKKIH
0|HNNMMKKKIH
0|HNNMMMKKIIH
0|HMNNMMKKKIH
1|HMNNMMKKKIIH(.32)HH
1|HMNNMMKKKKIH(.30)HHNH
2|HMNNMMKKKKIH(.26)HHNNMH
2|HMMNNMMKKKIIH(.23)HHNNMMMH
3|HMMNNMMKKKIIH(.20)HHNNMMMKKH
4|HMMNNMMKKKKIH(.16)HHHNNMMMKKKKH
4|HMMMNNMMKKKIIH(.13)HHNNMMMMKKKKKKH
5|HMMMNNMMKKKKIIH(.9)HHNNMMMMKKKKKKKKH
5|HMMMNNMMKKKKKIIH(.6)HHNNMMMMKKKKKKKKKIH
6|HMMMNNMMKKKKKKIH(.2)HHHNNMMMMKKKKKKKKIIIHH
6|HMMMNNMMKKKKKKMMNNMMMMMMKKKKKKKKKKKKIIIH
7|HMMMNNMKKKKKKKMMMMMMMKKKKKKKKKIIIIHHH
7|HMMMNNMMKKKKKKMMMMMMMKKKKKKKIIIIIHH
8|HMMMNNMMKKKKKKKKMMMMKKKKKIIIIIHH
9|HMMMNNMM(K14)IIIIIHH
10|HMMMNNMM(K11)IIIIIHH
11|HMMMNNM(K9)IIIIIHH
12|HMMMMM(K6)IIIIIHHH
13|HMMM(K5)IIIIIHH
15|HHMMKKKIIIHH
17|HHIIIIHH
19|HHHH
"""

# the root beard under the chin: three strands to the ground (whole map, rows 134..155, origin column 81)
BEARD = """
5|affba(.3)afdba(.5)afdba
5|affba(.3)afdba(.5)afdba
5|affba(.3)afddba(.4)afdba
5|affba(.3)afdba(.5)afdba
4|affba(.4)afdba(.6)afdba
4|affba(.4)afdba(.6)afdba
4|affdba(.3)afdba(.6)afdba
4|affba(.4)afdba(.6)afdba
3|affba(.5)afdba(.7)afdba
3|affba(.5)afdba(.7)afdba
3|affba(.5)afdba(.7)afdba
3|affba(.5)afdba(.7)afdba
2|affa(.7)afdba(.8)afba
2|affa(.7)afdba(.8)afba
2|affa(.7)afda(.9)afba
2|affa(.7)afda(.9)afba
1|affa(.8)afda(.10)afba
1|affa(.8)afda(.10)afba
1|aff(.9)afda(.10)afa
1|aff(.9)afda(.10)afa
0|aff(.10)afa(.12)afa
0|aa(.12)aa(.13)aa
"""

# ---------------------------------------------------------------- eyes (the image-left eye)
# a slanted glowing eye in the socket under the brow: rows 102..106, origin column 82
EYE_OPEN = """
0|WYYYW
0|Y$$%%$YYW
0|WY$%%$$YW
1|WYY$$YW
2|WYYYW
"""
# shut: the lid's line, a dim glow left in it (rows 104..105, origin column 82)
EYE_SHUT = """
0|WWWWWWWWW
1|VVVVVVV
"""

# ---------------------------------------------------------------- the core
# the murk socket in the chest (whole map): rows 47..77, columns 79..112
SOCKET = """
13|(O8)
10|(O3)(P8)(O3)
8|OO(P14)OO
6|OO(P18)OO
5|O(P22)O
4|O(P24)O
3|O(P26)O
2|O(P28)O
2|O(P28)O
1|O(P30)O
1|O(P30)O
0|O(P32)O
0|O(P32)O
0|O(P32)O
0|O(P32)O
0|O(P32)O
0|O(P32)O
0|O(P31)RO
0|O(P30)RRO
0|O(P30)RRO
1|O(P27)RRRO
1|O(P26)RRRRO
2|O(P22)(R6)O
2|O(P18)(R10)O
3|O(P13)(R13)O
4|O(P10)(R14)O
5|O(P8)(R14)O
6|OO(P4)(R14)OO
8|OO(R14)OO
10|(O3)(R8)(O3)
13|(O8)
"""

# the crystal heart (whole map, 18 x 19): the lit facet on the upper left, the dark facet on the right
CRYSTAL = """
8|VV
7|V%$V
6|V%$$YV
5|V%$$$YYV
4|V%$$$$YYWV
3|V%$$$$$YYWWV
2|V%$$%$$$YYWWWV
1|V%$$%%$$$YYWWWWV
0|V$$$%%$$$YYYWWWWWV
0|VY$$$$$$YYYYWWWWWV
1|VYY$$$$YYYYWWWWV
1|VYYY$$YYYYYWWWWV
2|VYYYYYYYYYWWWV
3|VYYYYYYYYWWV
4|VYYYYYYWWV
5|VYYYYYWV
6|VWYYWV
7|VWWV
8|VV
"""

# the root ribs across the core (whole map): rows 45..79, origin column 82
RIBS = """
8|oooo(.4)oooo
8|ouup(.4)otrp
8|ouup(.4)otrp
8|outp(.4)ottp
8|ouup(.4)otrp
1|oooo(.3)outp(.4)otrp(.3)oooo
1|ouup(.3)outp(.4)otrp(.3)otrp
1|ouup(.3)outp(.4)otrp(.3)otrp
1|outp(.3)outp(.4)ottp(.3)orrp
1|ouup(.3)ottp(.4)otrp(.3)otrp
1|ouup(.3)ottp(.4)otrp(.3)otrp
0|ouup(.4)outp(.4)otrp(.4)otrp
0|ouup(.4)outp(.4)otrp(.4)ottp
0|outp(.4)ouup(.4)otrp(.4)otrp
0|ouup(.4)outp(.4)ottp(.4)otrp
0|ouup(.4)oupp(.4)ottp(.4)otrp
0|ottp(.4)outp(.4)otrp(.4)otrp
0|ottp(.4)outp(.4)otrp(.4)otrp
0|ouup(.4)outp(.4)otrp(.4)otrp
0|ouup(.4)outp(.4)otrp(.4)orrp
0|ouup(.4)outp(.4)ottp(.4)orrp
0|ouup(.4)outp(.4)otrp(.4)otrp
0|ouup(.4)ottp(.4)otrp(.4)otrp
0|ouup(.4)outp(.4)otrp(.4)otrp
1|ouup(.3)outp(.4)otrp(.3)otrp
1|outp(.3)ouup(.4)otrp(.3)otrp
1|ottp(.3)outp(.4)otrp(.3)ottp
1|outp(.3)outp(.4)ottp(.3)otrp
1|ouup(.3)outp(.4)otrp(.3)otrp
1|oooo(.3)outp(.4)otrp(.3)oooo
8|ouup(.4)otrp
8|ouup(.4)otrp
8|outp(.4)ottp
8|ouup(.4)otrp
8|oooo(.4)oooo
"""

# ---- phase 2: the ribs split open, the core bared
# the wider socket (whole map): rows 43..81, columns 75..116
SOCKET2 = """
16|(O10)
13|(O3)(P10)(O3)
11|OO(P16)OO
9|OO(P20)OO
8|O(P24)O
6|OO(P26)OO
5|O(P30)O
4|O(P32)O
4|O(P32)O
3|O(P34)O
2|O(P36)O
2|O(P36)O
1|O(P38)O
1|O(P38)O
1|O(P38)O
0|O(P40)O
0|O(P40)O
0|O(P40)O
0|O(P40)O
0|O(P40)O
0|O(P40)O
0|O(P39)RO
0|O(P38)RRO
0|O(P38)RRO
1|O(P35)RRRO
1|O(P34)RRRRO
1|O(P32)(R6)O
2|O(P28)(R8)O
2|O(P24)(R12)O
3|O(P20)(R14)O
4|O(P16)(R16)O
4|O(P14)(R18)O
5|O(P12)(R18)O
6|OO(P8)(R18)OO
8|O(P6)(R18)O
9|OO(R20)OO
11|OO(R16)OO
13|(O3)(R10)(O3)
16|(O10)
"""

# the bared crystal (whole map, 22 x 23)
CRYSTAL2 = """
10|VV
9|V%$V
8|V%$$YV
7|V%$$$YYV
6|V%$$$$YYWV
5|V%$$$$$YYWWV
4|V%$$%$$$$YYWWV
3|V%$$%%$$$$YYWWWV
2|V%$$%%%$$$$YYWWWWV
1|V%$$$%%$$$$YYYWWWWWV
0|V$$$$$%$$$$YYYYWWWWWWV
0|VY$$$$$$$$YYYYYWWWWWWV
1|VYY$$$$$$YYYYYWWWWWV
1|VYYY$$$$YYYYYYWWWWWV
2|VYYYY$$YYYYYYWWWWV
3|VYYYYYYYYYYYWWWV
4|VYYYYYYYYYYWWV
5|VYYYYYYYYWWV
6|VYYYYYYYWV
7|VYYYYYWV
8|VWYYWV
9|VWWV
10|VV
"""

# a split rib bowed outward (HALF: the left one; rows 42..80, origin column 72)
RIB2 = """
12|oooo
11|outrpo
10|ouurpo
10|outtpo
9|ottrpo
8|ouutpo
7|outrpo
7|ouutrpo
6|outtrpo
5|ottrpo
4|ouurpo
4|outtpo
3|outrppo
2|ouutrpo
1|outtpo
1|ottrpo
0|ouurppo
0|outtrpo
0|oupprpo
1|outprpo
1|ouutpo
1|ottrpo
2|outrpo
2|ouurpo
2|outtrpo
3|ottrppo
3|ouutpo
3|outrpo
4|ouurpo
4|outtpo
4|ottrpo
5|ouutrpo
5|outrppo
6|ouurpo
6|outtpo
6|ottrpo
7|ouutpo
7|outrpo
8|oooo
"""

# glowing seams through the roots (whole maps; a light line with a deep line under it)
CRACK_A = """
0|WW
0|$W
1|$W
1|$WW
2|$$W
3|$W
3|$W
4|$W
4|$WW$W
5|$W.$$W
6|$W..WW
6|$$W
7|$W
8|$W
8|$W
9|$W
9|$WW
10|$W
11|$W
11|$W
12|$W
12|$WW
13|$W
14|$W
14|$W
15|WW
"""
CRACK_B = """
0|WW
0|W$
1|W$
1|W$
2|W$$
3|W$
3|W$
3|WW$
4|W$
4|W$
5|W$
1|W$W.W$
0|WW$$WW$
5|WW$
7|W$
7|W$
8|W$
8|W$$
9|W$
9|W$
10|W$
10|WW$
11|W$
11|W$
12|WW
"""

# ---------------------------------------------------------------- fungus caps (whole maps)
FUNGUS_L = """
4|AAAAAAAA
2|AAGGGGFFFFAA
1|AGGFFFFFFDDDDA
0|AGFFFFDDDDDDDDBA
0|AFFDDDDDDDDDBBBA
0|ABBBBBBBBBBBBBBA
1|AABBBBBBBBBBAA
3|AAAAAAAAAA
"""
FUNGUS_M = """
3|AAAAAA
1|AAGGFFFFAA
0|AGFFFDDDDDBA
0|AFDDDDDDDBBA
0|ABBBBBBBBBBA
2|AAAAAAAA
"""
FUNGUS_S = """
2|AAAA
0|AAGFFDAA
0|AFDDDDBA
0|AABBBBAA
2|AAAA
"""

# ---------------------------------------------------------------- effects drawn into the frames
# a magic orb gathering before the core (volley), 14 x 14
ORB = """
4|VVVVVV
2|VVYYYYYYVV
1|VYY$$$$YYYWV
1|VY$%%$$$YYWV
0|VY$%%%$$$YYWWV
0|VY$%%$$$$YYWWV
0|VY$$$$$$YYYWWV
0|VYY$$$$YYYYWWV
0|VYYYYYYYYYWWWV
0|VWYYYYYYYWWWWV
1|VWWYYYYWWWWV
1|VWWWWWWWWWWV
2|VVWWWWWWVV
4|VVVVVV
"""
# chips of root thrown up by the slam
CHIP_A = """
3|aaaa
1|aaggfaa
0|aggffddaa
0|agffdddbba
0|affddbdbba
1|addddbbba
2|aabbbbaa
4|aaaa
"""
CHIP_B = """
2|aaaa
0|aaggfaa
0|agffddba
0|afdddbba
1|abbbbba
2|aaaaa
"""

# the pool of murk a purified core leaves (HALF maps, right-aligned to the centre line: typed in
# frame columns). A: 9 rows, B: 11 rows.
POOL_A = """
56|(O40)
44|OO(T10)(S12)(R28)
38|O(T6)(S14)(R37)
36|O(S10)(R49)
36|O(R24)(Q35)
36|O(R14)(Q45)
38|O(Q57)
44|OO(P50)
56|(O40)
"""
POOL_B = """
56|(O40)
38|OO(T12)(S16)(R28)
28|O(T8)(S20)(R39)
22|O(S14)(R59)
20|O(S6)(R69)
20|O(R30)(Q45)
20|O(R16)(Q59)
22|O(Q73)
28|OO(P66)
38|(O4)(P54)
56|(O40)
"""

# marks on the image-right side only (placed after the mirrored roots, so the two halves differ):
# a knot, a split, a torn strip of bark
KNOT_A = """
1|bbb
0|bdfdb
0|bfgfb
0|bddfb
1|bbb
"""
SCAR_A = """
0|bb
1|bbb
2|bfb
3|bbb
5|bb
6|bb
"""
SCAR_B = """
0|bb....bb
1|bbbbbbb
2|bfffb
3|bbb
"""
RIGHT_MARKS = (("KNOT_A", 126, 38), ("SCAR_A", 137, 64), ("SCAR_B", 118, 86), ("KNOT_A", 150, 62))

# the purification, frame 4 (HALF, typed in frame columns; rows 107..151): what is left of the body, a
# low slumped mound of murk with the stubs of three spikes, sagging in folds toward the ground
MELT = """
82|OO
81|OTRO
80|OTRRO
80|OTTRPO
80|OUTRRPO
81|OTTRRPO
82|OTTRRPO
82|OUTRRPPO
60|OO(.20)OTTRRRPO(.2)OOOO
59|OTRO(.19)OTTRRRPPO(O5)
59|OTRPO(.16)OOTTRRRPPOUUTTTT
60|OTRRPO(.12)OOOTTTRRRPPTTTTSSS
60|OTTRPO(.9)OOOUUTTTRRRRPPTSSSSSS
61|OTRRPO(.5)OOOUUTTTTRRRRRRPPSSSSSSS
61|OTTRPPOOOOUUTTTT(R9)PP(S8)
58|OOOUTRRPPUUTTTT(R12)PPP(S8)
55|OOOUUTTRRRPTTTT(R14)(P4)(S8)
52|OOOUUTTT(R10)PP(R12)(P5)(S7)
50|OOUUTTT(R12)PPP(R12)(P6)(R6)
44|OO..OOOUTTT(R14)PPP(R10)(P8)(R6)
43|OTRO.OOUUTT(R16)PPPP(R8)(P10)(R4)
43|OTRPOOUUTTT(R16)(P5)(R6)(P12)(R3)
42|OTTRPOUUTTT(R18)(P5)(R5)(P13)(R2)
40|OOTTRRPUTTT(R20)(P6)(R4)(P14)R
38|OOUTTRRRTTT(R20)(P7)(R4)(P16)
36|OOUUTTRRRR(R22)(P8)(R3)(P17)
34|OOUUTTT(R29)(P9)(Q17)
33|OUUTTT(R28)(P11)(Q18)
31|OOUTTTT(R26)(P13)(Q19)
30|OUUTTT(R25)(P15)(Q20)
28|OOUTTT(R24)(P17)(Q21)
27|OUTTT(R22)(P20)(Q22)
25|OOUTT(R21)(P22)(Q23)
24|OUTT(R19)(P25)(Q24)
23|OUTT(R16)(P29)(Q24)
22|OOTT(R13)(P57)
21|OOT(R10)(P62)
20|OOT(R6)(P67)
20|O(P75)
19|OO(P20)(Q30)(P25)
19|O(P18)(Q36)(P22)
19|O(P14)(Q44)(P18)
20|O(P12)(Q48)(P15)
20|O(P75)
22|(O74)
"""

# folds of light on the mound of murk (the purification, frame 4)
FOLD_A = """
1|UUUTTT
0|UTTTSSSSRO
0|TSSSRRRPPO
2|PPPPOO
"""
FOLD_B = """
0|OUUT
0|OTTSSP
1|OSRRPPO
2|OPPO
"""

HALF = {"VINE", "VINE2", "SPK_1", "SPK_2", "SPK_3", "SHOULDER", "LEG", "HIND", "HEAD", "JAW", "MOUTH", "TUSK", "RIB2",
        "POOL_A", "POOL_B", "MELT"}
COLS = {"SHOULDER", "LEG_OUT"}
# top-left in the frame, rest pose (HALF maps: the left one)
PLACE = {
    "SPK_C": (87, 2), "SPK_1": (66, 5), "SPK_2": (50, 12), "SPK_3": (32, 24), "SHOULDER": (16, 47),
    "LEG": (5, 80), "VINE": (5, 88), "VINE2": (5, 118), "HIND": (55, 73), "HEAD": (62, 78), "NECK": (74, 92), "JAW": (83, 129), "MOUTH": (85, 124),
    "TUSK": (43, 101), "BEARD": (81, 134), "EYE_OPEN": (82, 102), "EYE_SHUT": (82, 104),
    "SOCKET": (79, 47), "CRYSTAL": (87, 52), "RIBS": (82, 45), "SOCKET2": (75, 43), "CRYSTAL2": (85, 50),
    "RIB2": (72, 42), "CRACK_A": (58, 52), "CRACK_B": (122, 48), "POOL_A": (0, 150), "POOL_B": (0, 149), "MELT": (0, 107),
}
# fungus caps on the body: (map, x, y) in the rest pose
FUNGI = (("FUNGUS_L", 48, 55), ("FUNGUS_S", 40, 71), ("FUNGUS_M", 134, 45), ("FUNGUS_L", 132, 60),
         ("FUNGUS_M", 121, 72), ("FUNGUS_S", 146, 79), ("FUNGUS_M", 80, 81), ("FUNGUS_S", 105, 85),
         ("FUNGUS_S", 64, 79))
