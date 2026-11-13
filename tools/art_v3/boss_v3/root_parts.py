"""朽ち根のヌシ (boss_root), v3: the hand-drawn maps of everything but the body (pixmap.py syntax).

Legend:  a-g rotwood   h-n rotwood_d (wet dark rot)   o-u rotwood_p (dry pale root)
         A-G fungus    H-N bone    O-U murk    V W X Y Z $ % glow
HALF maps are the image-left part (mirrored for the right, one step darker in the lights); the others
are drawn whole. Positions are the top-left in the 192 x 160 frame in the rest pose (PLACE).
"""

# ---------------------------------------------------------------- back spikes (behind the body)
# dead roots standing out of the back: a dry pale tip, grain lines, the lit side on the left

SPK_C = """
6|oo
6|oo
5|ouro
5|ouro
5|otro
4|outro
4|ouurpo
4|ottrpo
4|ottrpo
3|ouurrpo
3|ouurrpo
3|aggddba
3|aggddba
3|affddbba
2|aggfddbba
2|aggfddbba
2|aggbddbba
2|aggbdddba
2|affbbddbba
2|afffdddbba
1|aggfdddbbba
1|aggfdddbbba
1|aggfdddbbba
1|aggffddbbba
1|affffddbbba
1|afffdddbbbba
0|aggffdddbbbba
0|aggffdddbbbba
0|aggfbbddddbba
0|aggfbbdddbbba
0|affbbddddbbba
0|afffddddddbba
0|aggffdddddbbba
0|aggffdddddbbba
0|aggffdddbbbbba
0|aggfdddddbbbba
0|afffddddddbbba
0|afffddddddbbba
0|aggfddddddbbba
0|aggfddddddbbba
0|aggffdddddbbba
0|aggffdddddbbba
0|afffddddddbbba
0|afffddddddbbba
"""

SPK_1 = """
5|oo
5|oo
5|ouo
5|ouro
4|ouro
4|otrpo
4|otrpo
4|ouurpo
4|ouurpo
4|ottrpo
4|ottrppo
4|aggddba
4|aggddbba
4|affddbba
4|affdbbba
3|aggddbbba
3|aggdddbba
3|aggfddbba
3|affdddbbba
3|affddddbba
3|aggddddbba
3|aggbdddbbba
3|aggbdddbbba
3|affbbdddbba
3|afffdddddba
3|aggfddddbbba
3|aggfdddbbbba
3|aggdddddbbba
3|affdddddbbba
3|afffddddbbbba
3|aggfddddbbbba
3|aggfdddddbbba
3|aggddbbddbbba
3|affddbbdddbba
3|afffddddddbba
3|aggfddddddbbba
3|aggfdddddbbbba
3|aggdddddddbbba
3|affdddddddbbba
3|afffddddddbbba
3|aggfddddddbbba
3|aggfddddddbbba
3|affdddddddbbba
"""

SPK_2 = """
2|oo
2|oo
2|ouo
2|ouro
2|ouro
2|otrpo
2|otrpo
2|ouurpo
2|ottrpo
2|aggdba
2|aggddba
2|affdbba
2|affdbbba
2|aggddbba
2|aggdddbba
2|affdddbba
2|affddbbba
3|aggddbbba
3|aggdddbbba
3|affdddbbba
3|affddddbba
3|aggddddbba
3|aggfdddbbba
3|affddddbbba
3|affdddbbbba
4|aggdddbbbba
4|aggddddbbba
4|affddddbbbba
4|afffdddbbbba
4|aggddddddbba
4|aggddddddbba
4|affdddddbbba
4|affdddddbbba
4|aggdddddbbba
4|aggdddddbbba
4|affdddddbbba
4|affdddddbbba
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

# the front leg swung out to the side (rearing, half way), typed in COLUMNS from the toes (column 8)
# to the shoulder (column 56): three toes, the forearm, the elbow knot, the upper root
LEG_OUT = """
26|ooo
13|ooo(.9)otrpo
13|otto(.8)otrpo(.8)ooo
14|otto(.7)otrpo(.7)otpo
14|ottpo(.6)otrpo(.6)otrpo
15|affba(.5)afdba(.5)afdba
16|affba(.3)afddba(.5)afdba
16|affdba..agfddba...afddba
17|affdba.agfddba..afddba
18|aggdbbgfdddbbgfddbba
18|aggfdbgfdddbbfdddba
19|aggfddbfdddbfddba
19|aggfddddddddbbba
19|aggfdddddddddbbba
20|aggfdddddddddbbba
21|aggffddddddddbbbba
21|aggffdddbbdddbbbba
22|aggffddddbbdddbbbba
23|aggffdddddbbddbbbba
23|aggffeeeeedddcccccba
24|aggffeeeeedbbcccccba
23|aggffeeeeebfbcccccba
22|aggffeeeeedbbcccccba
21|aggffeeeeedddcccccba
20|aggffeeeeeddddcccccba
20|aggffeeeeeddddcccccba
19|aggffeeeeeddddcccccba
18|aggffeeeeeddddcccccba
17|aggffeeeeeddddcccccbba
16|aggffeeeeeddddcccccbba
15|aggffeeeeedbbdcccccbba
14|aggffeeeeedbbdcccccbba
13|aggffeeeeedbbddcccccbba
13|aggffeeeeedbbddcccccbba
12|aggffeeeeedddddcccccbba
11|aggffeeeeedddddcccccbba
10|aggffeeeeedddddcccccbbba
9|aggffeeeeedddddcccccbbba
8|aggffeeeeedddddcccccbbba
7|aggffeeeeedddddcccccbbba
6|aggffeeeeeddddddcccccbbba
6|aggffeeeeeddddbbcccccbbba
5|aggffeeeeeddddbbcccccbbba
4|aggffeeeeeddddbbcccccbbba
3|aggffeeeeeddddbbcccccbbbba
2|aggffeeeeeddddbbcccccbbbba
2|aggffeeeeeddddddcccccbbbba
1|aggffeeeeeddddddcccccbbbba
0|aggffeeeeeddddddcccccbbbba
"""

# the front leg raised above the shoulder (rearing): the upper root out to the elbow, the forearm up,
# the three toes clawing upward. Rows 28..86, origin column 8.
LEG_UP = """
8|ooo
0|ooo(.4)otrpo(.4)ooo
0|otto(.3)otrpo(.3)otpo
0|ottpo(.2)otrpo(.2)otrpo
1|affba.afdba..afdba
1|affbaagfddbaafdba
2|affbbgfdddbbfdba
2|aggdbgfdddbbfdba
2|aggfdbfdddbfddba
1|aggfddddddddbbbba
1|aggfeeeedddcccba
1|aggfeeeedddcccba
1|aggfeeeedddcccba
1|aggfeeeedddcccba
1|aggfeeeebbdcccba
1|aggfeeeebbdcccba
1|aggfeeeebbddcccba
1|aggfeeeebbddcccba
1|aggfeeeeddddcccba
1|aggfeeeeddddcccba
1|aggfeeeeddddcccba
1|aggfeeeeddddcccba
2|aggfeeeeddddcccba
2|aggfeeeeddddcccba
2|aggfeeeedbbdcccba
2|aggfeeeedbbdcccba
2|aggfeeeedbbdcccba
2|aggfeeeedbbdcccba
2|aggfeeeeddddcccbba
2|aggfeeeeddddcccbba
2|aggfeeeeddddcccbba
2|aggfeeeeddddcccbba(.24)aaaaa
2|aggfeeeeddddcccbba(.20)aaaaggggg
2|aggfeeeeddddcccbba(.16)aaaaggggfffff
3|aggffeeeeddddcccbba(.10)aaaaggggfffffffff
3|aggffeeeeddddcccbba(.6)aaaaggggffffffffffffe
3|aggffeeeeddddcccbba(.2)aaaagggg(f12)eeeee
3|aggffeeeedddddcccbbgggggg(f12)(e9)
4|aggf(g12)(f16)(e13)
4|aggff(g4)(f18)(e18)
4|aggff(f12)(e20)(d8)
4|aggff(f6)(e22)(d12)
4|aggff(e12)bbbbbb(e6)(d16)
4|aggfe(e18)(d22)
4|aggfe(e10)(d24)(c6)
4|aggfe(e4)(d10)bbbbb(d9)(c12)
4|aggfeedbb(d19)(c17)
4|aggfeebfb(d13)(c23)
4|aggfeedbb(d6)(c24)(b6)
4|aggfeedd(d2)(c23)(b12)
5|aggeedd(c19)(b17)a
5|aggeedd(c13)(b23)a
6|aggddd(c8)(b28)a
7|aggdd(c5)(b31)a
8|aggdd(b35)a
9|aggd(b35)a
11|aafd(b33)a
13|aa(b33)a
15|(a34)
"""
PLACE_OUT = (8, 56)
PLACE_UP = (8, 28)

# the hind legs, seen between the front legs: short, thick, in wet dark rot. Rows 96..158.
HIND = """
4|hmmllkkkkkjjjiiiih
4|hmmllkkkkkjjjiiiih
4|hmmllkkkkkjjjiiiih
4|hmmllkkiikjjjiiiih
4|hmmllkkiikjjjiiiih
4|hmmllkkkiijjjiiiih
4|hmmllkkkiijjjiiiih
4|hmmllkkkkkjjjiiiih
4|hmmllkkkkkjjjiiiih
4|hmmllkkkkkjjjiiiih
4|hmmllkkkkkjjjiiiih
4|hmmllkkkkkjjjiiiih
4|hmmllkkkkkjjjiiiih
4|hmmllkkkkkjjjiiiih
4|hmmllkkkkkjjjiiiih
3|hmmllkkkkjjjiiiih
3|hmmllkkkkjjjiiiih
3|hmmllkiikjjjiiiih
3|hmmllkiikjjjiiiih
3|hmmllkkiijjjiiiih
3|hmmllkkkkjjjiiiih
3|hmmllkkkkjjjiiiih
3|hmmllkkkkjjjiiiih
3|hmmllkkkkjjjiiiih
3|hmmllkkkkjjjiiiih
3|hmmllkkkkjjjiiiih
3|hmmllkkkkjjjiiiih
3|hmmllkkkkjjjiiiih
3|hmmllkkkkjjjiiiih
3|hmmllkkkkjjjiiiih
3|hmmllkkkkjjjiiih
3|hmmllkkkkjjjiiih
3|hmmllkkkkjjjiiih
3|hmmllkkiijjjiiih
3|hmmllkkiijjjiiih
3|hmmllkkkkjjjiiih
3|hmmllkkkkjjjiiih
3|hmmllkkkkjjjiiih
3|hmmllkkkkjjjiiih
3|hmmllkkkkjjjiiih
3|hmmllkkkkjjjiiih
3|hmmllkkkkjjjiiih
3|hmmllkkkkjjjiiih
3|hmmllkkkkjjjiiih
3|hmmllkkkkjjjiiih
2|hmmkkkkkjjjiiih
2|hmmkkkkkjjjiiih
2|hmmkkkkkjjjiiih
2|hmmkkkkkjjjiiih
2|hmmkkiikjjjiiih
2|hmmkkiikjjjiiih
2|hmmkkkkkjjjiiih
2|hmmkkkkkjjjiiih
2|hmmkkkkkjjjiiih
2|hmmkkkkkjjjiiih
1|hmmkkkkkkjjjiiiiih
0|hmmkkkkkkkkjjjiiiiih
0|hmmkkkiikkkkiikkkiiiih
0|hmmkkkiikkkkiikkkiiiih
0|hmmkkkiikkkkiikkkiiiih
0|hmmkkkiikkkkiikkkiiiih
0|hiiiiiiiiiiiiiiiiiiiih
1|hhhhhhhhhhhhhhhhhhhh
"""

# ---------------------------------------------------------------- head (HALF: columns 62..95)
# a low boar head: a pointed ear with a dark inside, a heavy root brow slanting down to the nose
# (the eye sits in the dark socket under it), a lit cheek with a crack, the snout disc and nostril.
# Rows 78..130; the map ends on the mouth line (the chin is JAW).

HEAD = """
0|aa
0|afa
1|afa
1|afda
1|afdda
2|affbba
2|affbbda
2|affbbdda
3|affbbbda
3|affdbbbdda
3|affdbbbbdda(.14)aaaaaa
4|affdbbbbdda(.10)aaagggttr
4|affdbbbbbddda(.6)aaggggggtrr
4|affddbbbbbddda(.3)aagffffffftrr
5|affddbbbbbdddbgffffffffffftrr
5|affddbbbbbdddbgffffdfffffftrr
5|affdddbbbbddbfffffffdffffftrr
6|affddbbbbddbfffffffffdffftrr
6|affddbbbdbffffffffffffdfftrr
6|affdbbdbgggggffffffffffdftrr
7|affdbbbffffffffggggffffftrr
7|affddbfddddddddffffggggftrr
8|affdbfbbbbbbbbddddffffgtrr
8|aagfffffdbaaaabbbbddddftrr
9|aggfffffdbaaaaaaabbbbdtrr
10|aggfffffdaaaaaaaaaaabtrr
9|aggfffffffaaaaaaaaaaadtrr
9|aggfffffffaaaaaaaaaaadtrr
9|aggfffffffbaaaaaaaaabdtrr
9|aggffffffffbbbbbbbbbfdtrr
9|aggfffffffffgggggggffdtrr
9|aggfffffbffffffeeeeeeetrr
9|aggffffbfffffffeeeeeeetrr
9|aggfffbffffffffeeeeeeetrr
9|affffbffffffffeeeeeeeetrr
10|afffbffffffffeeeeeeeetrr
10|afffffffffffeeeeeeeeetrr
11|affffffffffeeeeeeeeetrr
11|afffffeeeeeebbbbbbbbbbb
12|affeeeeeeeebgggggggggg
12|affeeeeeeeebgfffffffff
13|affeeeeeedbgfffffffff
14|affddddddbgfffffffff
15|adddddddbgffffaafff
16|addddddbgffffaafff
18|addddbfffffaaffe
19|adddbfffffaafed
19|adddbffffffffed
19|addbbfffffffddd
20|addbfffffddddd
20|adbbdddddddddd
21|adbbbbbbbbbbb
21|aaaaaaaaaaaaa
"""

# the neck (HALF, columns 74..95, rows 92..128): wet dark roots between the chest and the head, seen
# when the head drops for the charge
NECK = """
0|hmmllkkiikkkmkkiikkkkk
0|hmmllkkiikkkmkkiikkkkk
0|hmmllkkiikkkmkkiikkkkk
0|hmmllkkiikkkmkkiikkkkk
0|hmmllkkiikkkmkkiikkkkk
0|hmmllkkiikkkmkkiikkkkk
0|hmmllkkiikkkmkkkiikkkk
0|hmmllkkiikkkmkkkiikkkk
0|hmmllkkiikkkmkkkiikkkk
0|hmmllkkiikkkmkkkiikkkk
0|hmmllkkiikkkmkkkiikkkk
0|hmmllkkiikkkmkkkiikkkk
0|hmmllkkiikkkmkkkiikkkk
1|hmmllkiikkkmkkkiikkkk
1|hmmllkiikkkmkkkiikkkk
1|hmmllkiikkkmkkkiikkkk
1|hmmllkiikkkmkkkiikkkk
1|hmmllkiikkkmkkkiikkkk
1|hmmllkiikkkmkkkiikkkk
1|hmmllkiikkmkkkkiikkkk
1|hmmllkiikkmkkkkiikkkk
1|hmmllkiikkmkkkkiikkkk
1|hmmllkiikkmkkkkiikkkk
1|hmmllkiikkmkkkkiikkkk
1|hmmllkiikkmkkkkiikkkk
1|hmmllkiikkmkkkkiikkkk
2|hmmlkkiikkmkkkiikkkk
2|hmmlkkiikkmkkkiikkkk
2|hmmlkkiikkmkkkiikkkk
2|hmmlkkiikkmkkkiikkkk
2|hmmlkkiikkmkkkiikkkk
2|hmmlkkiikkmkkkiikkkk
2|hmmkkkiikkmkkkiikkkk
2|hmmkkkiikkmkkkiikkkk
2|hmmkkkiikkmkkkiikkkk
2|hmmkkkiikkmkkkiikkkk
3|hiiiiiiiiiiiiiiiiii
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

# the inside of the mouth (HALF, columns 85..95, rows 126..134): murk, seen only when the chin drops
MOUTH = """
0|O(P10)
0|O(P10)
0|O(P10)
0|O(P10)
0|O(P10)
0|O(P10)
0|O(P10)
0|O(P10)
0|(O11)
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
5|hmmih(.3)hmkih(.5)hlkih
5|hmmih(.3)hmkih(.5)hlkih
5|hmmih(.3)hmkkih(.4)hlkih
5|hmmih(.3)hmkih(.5)hlkih
4|hmmih(.4)hmkih(.6)hlkih
4|hmmih(.4)hmkih(.6)hlkih
4|hmmkih(.3)hmkih(.6)hlkih
4|hmmih(.4)hmkih(.6)hlkih
3|hmmih(.5)hmkih(.7)hlkih
3|hmmih(.5)hmkih(.7)hlkih
3|hmmih(.5)hmkih(.7)hlkih
3|hmmih(.5)hmkih(.7)hlkih
2|hmmh(.7)hmkih(.8)hlih
2|hmmh(.7)hmkih(.8)hlih
2|hmmh(.7)hmkh(.9)hlih
2|hmmh(.7)hmkh(.9)hlih
1|hmmh(.8)hmkh(.10)hlih
1|hmmh(.8)hmkh(.10)hlih
1|hmm(.9)hmkh(.10)hlh
1|hmm(.9)hmkh(.10)hlh
0|hmm(.10)hmh(.12)hlh
0|hh(.12)hh(.13)hh
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
8|ouup(.4)otrp
8|ouup(.4)otrp
1|oooo(.3)outp(.4)otrp(.3)oooo
1|ouup(.3)outp(.4)otrp(.3)otrp
1|ouup(.3)outp(.4)otrp(.3)otrp
1|ouup(.3)outp(.4)otrp(.3)otrp
1|ouup(.3)ottp(.4)otrp(.3)otrp
1|ouup(.3)ottp(.4)otrp(.3)otrp
0|ouup(.4)outp(.4)otrp(.4)otrp
0|ouup(.4)outp(.4)otrp(.4)otrp
0|ouup(.4)outp(.4)otrp(.4)otrp
0|ouup(.4)outp(.4)ottp(.4)otrp
0|ouup(.4)oupp(.4)ottp(.4)otrp
0|ottp(.4)outp(.4)otrp(.4)otrp
0|ottp(.4)outp(.4)otrp(.4)otrp
0|ouup(.4)outp(.4)otrp(.4)otrp
0|ouup(.4)outp(.4)otrp(.4)orrp
0|ouup(.4)outp(.4)otrp(.4)orrp
0|ouup(.4)outp(.4)otrp(.4)otrp
0|ouup(.4)ottp(.4)otrp(.4)otrp
0|ouup(.4)outp(.4)otrp(.4)otrp
1|ouup(.3)outp(.4)otrp(.3)otrp
1|ouup(.3)outp(.4)otrp(.3)otrp
1|ouup(.3)outp(.4)otrp(.3)otrp
1|ouup(.3)outp(.4)otrp(.3)otrp
1|ouup(.3)outp(.4)otrp(.3)otrp
1|oooo(.3)outp(.4)otrp(.3)oooo
8|ouup(.4)otrp
8|ouup(.4)otrp
8|ouup(.4)otrp
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
11|ouurpo
10|ouurpo
10|ouurpo
9|ouurpo
8|ouurpo
7|ouurpo
7|ouurpo
6|ouurpo
5|ouurpo
4|ouurpo
4|ouutpo
3|ouutpo
2|ouurpo
1|ouurpo
1|ouurpo
0|ouurpo
0|ouurpo
0|ouurpo
1|ouurpo
1|ouurpo
1|ouurpo
2|ouurpo
2|ouurpo
2|ouurpo
3|ouurpo
3|ouurpo
3|ouurpo
4|ouurpo
4|ouutpo
4|ouurpo
5|ouurpo
5|ouurpo
6|ouurpo
6|ouurpo
6|ouurpo
7|ouurpo
7|ouurpo
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
11|WW
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
9|WW
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
1|aaaa
0|aggdba
0|affdba
0|abbbba
1|aaaa
"""
CHIP_B = """
1|aaa
0|agfba
0|afdba
1|aaa
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

HALF = {"SPK_1", "SPK_2", "SPK_3", "SHOULDER", "LEG", "HIND", "HEAD", "NECK", "JAW", "MOUTH", "TUSK", "RIB2",
        "POOL_A", "POOL_B"}
COLS = {"SHOULDER", "LEG_OUT"}
# top-left in the frame, rest pose (HALF maps: the left one)
PLACE = {
    "SPK_C": (89, 4), "SPK_1": (66, 8), "SPK_2": (50, 16), "SPK_3": (32, 28), "SHOULDER": (16, 47),
    "LEG": (8, 80), "HIND": (58, 97), "HEAD": (62, 78), "NECK": (74, 92), "JAW": (83, 129), "MOUTH": (85, 126),
    "TUSK": (43, 101), "BEARD": (81, 134), "EYE_OPEN": (82, 102), "EYE_SHUT": (82, 104),
    "SOCKET": (79, 47), "CRYSTAL": (87, 52), "RIBS": (82, 45), "SOCKET2": (75, 43), "CRYSTAL2": (85, 50),
    "RIB2": (72, 42), "CRACK_A": (58, 52), "CRACK_B": (122, 48), "POOL_A": (0, 150), "POOL_B": (0, 149),
}
# fungus caps on the body: (map, x, y) in the rest pose
FUNGI = (("FUNGUS_L", 48, 55), ("FUNGUS_S", 40, 71), ("FUNGUS_M", 134, 45), ("FUNGUS_L", 132, 60),
         ("FUNGUS_M", 121, 72), ("FUNGUS_S", 146, 79), ("FUNGUS_M", 80, 81), ("FUNGUS_S", 105, 85),
         ("FUNGUS_S", 64, 79))
