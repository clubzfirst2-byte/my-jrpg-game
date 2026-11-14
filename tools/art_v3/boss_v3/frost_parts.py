"""凍て角のヌシ (boss_frost), v3: the hand-drawn maps of the body, the head and the effects (pixmap.py
syntax; the antlers are in frost_antlers.py).

Legend:  a-g frostfur (the warm grey-tan coat)   h-n frostfur_d (the dark mane, the far legs, hooves)
         o-u frostfur_p (the pale face)          A-G ice       O-U murk       V W X Y Z $ % glow
HALF maps are the image-left part (mirrored for the right). Positions are the top-left in the
192 x 176 frame in the rest pose. Fur is typed as hanging strands: a dark groove, a lit edge, the
strand's body; the grooves wander and the locks end at different rows.
"""

# ---------------------------------------------------------------- front leg (HALF, rows 122..175)
# near and thick: the upper leg, the knee's knob, the cannon, the fetlock's tuft in points, the hoof
FLEG = """
11|agffeeeeddddddccccbbba
11|aggfeeeedddbddccccbbba
11|aggfeeeeddbdddccccbbba
11|agffeeeedbddddcccbbbba
11|agfffeeeddddddcccbbbba
11|aggffeeedddddbccccbbba
11|aggfeeeeddddbdccccbba
11|agffeeeedddbddccccbba
11|agffeeeeddbdddcccbbba
11|aggfeeeedddddccccbbba
11|aggffeeeddddbcccbbba
11|agfffeeedddbdcccbbba
11|agffeeeeddbddcccbbba
11|aggfeeeedddddccbbbba
11|aggfeeeeddddbccbbba
11|agffeeeedddbdccbbba
11|agfffeeedddddcbbba
11|aggffeeeddbddcbbba
11|aggfeeeedbdddbbba
11|agffeeeeddddbbbba
10|agfffeeedddddbbba
10|aggffeeeddbdbbbba
10|aggfeeedddbbbbba
9|agggffeedddbbbbba
9|aggggfffddddbbbba
9|agggfffdddddbbbba
9|aaggffddddbbbbbaa
10|aaffdddddbbbbaa
10|agffddddbbbba
10|aggfdddbbbba
10|agffddddbbba
10|agffdddbbbba
10|aggfdddbbba
9|aggfddddbbba
9|agffdddbbbba
9|agffddddbba
9|aggfdddbbba
9|aggfddbdbba
9|agffdddbbba
8|agffddddbba
8|aggfdddbbba
6|aaaggffdddbbaaa
5|agggffffdddddbba
4|aggffgffdddbddbbba
4|agffdbgfddbdddbbba
4|agfdbagfdbaddbbbaa
5|aba..ahhhhhha..aba
6|hhkkjjjjiiiihh
6|hkllkjjjiiiiih
5|hkklljjjjiiiiihh
5|hjkkkjjjiiiiiiih
5|hjjkjjjiihiiiiih
5|hiijjiiihhiiiiih
6|hhhhhhhhhhhhhh
"""

# the front leg folded under the raised chest (rearing; HALF, rows 122..168): the upper leg out to the
# knee, the cannon folded back, the hoof hanging
FLEG_FOLD = """
11|agffeeeeddddddccccbbba
10|aggfeeeedddbddccccbbba
10|aggfeeeeddbdddcccbbba
9|agffeeeedddddbccccbbba
9|agfffeeeddddbdcccbbba
9|aggffeeedddbddccbbba
8|aggfeeeeddbdddccbbbba
8|agffeeeedddddcccbbba
8|agfffeeedddbdcccbba
7|aggffeeeddbddcccbbba
7|aggfeeeedddddccbbba
7|agffeeeeddddbccbba
6|agfffeeedddbdcbbbba
6|aggffeeeddbddbbbba
6|aggfeeeeddddbbbba
5|agffeeeedddbdbbbba
5|agfffeeeddbddbbba
4|aggffeeedddddbbbba
4|aggfeeeedddbbbbba
3|agggfffedddbbbbbaa
2|aggggfffdddbbbbbaa
2|agggffffddddbbbaa
2|aggfffddddddbbba
3|aagffddddddbbba
4|aaffdddddbbbba
5|aagfdddddbbba
6|agffddddbbba
7|aggfdddbbba
7|agffddddbbba
8|agffdddbbba
8|aggfdddbbbba
9|aggfddbdbba
9|agffdddbbbba
10|agffdddbbba
10|aggfdddbbbba
11|aggfddbdbba
10|aagffddddbbaa
9|agggffdddbddbba
9|aggfdbgfdbddbbba
10|agdbahhhhhhhaba
11|aba.hjkkjjiiih
15|hkkljjiiih
15|hjklkjiiiih
15|hjkkjjiiiih
16|hjjkjiiiih
16|hiijiihiih
17|hhhhhhhh
"""

# the hind leg (HALF, rows 118..168): further back, thinner, in the dark coat; its hoof stands higher
HIND = """
5|hmllkkkkkkjjjiiih
5|hmmlkkkkkjkjjiiih
5|hmllkkkkjkkjjiiih
5|hmllkkkjkkkjjiiih
5|hmmlkkkkkkjjjiiih
6|hmllkkkkkjjjiiih
6|hmllkkkjkkjjiiih
6|hmmlkkjkkkjjiiih
6|hmmlkkkkkjjjiiih
6|hmllkkkkjjjjiiih
6|hmllkkkkkjjiiih
6|hmmlkkkjkjjiiih
6|hmmlkkjkkjjiiih
7|hmllkkkkjjjiih
7|hmllkkkjkjjiih
7|hmmlkkjkjjjiih
7|hmmlkkkkjjiih
7|hmllkkkjjjiih
7|hmllkkjkjjiih
7|hmmlkkkjjiih
7|hmmlkjkjjiih
7|hmllkkjjjiih
7|hmllkkkjjih
7|hmmmlkkjjih
7|hmmllkkjjiih
7|hmmlkkkjjiih
7|hhmlkkjjiihh
8|hmlkkjjiih
8|hmmkkjjiih
8|hmlkkjjih
8|hmmkkjiih
8|hmlkjjiih
8|hmlkkjih
8|hmmkjjih
8|hmlkjiih
8|hmlkkjih
8|hmmkjiih
7|hhmlkjjihh
6|hmmllkkjjiih
6|hmlmlkkjkjih
6|hmlkmkjkjiih
6|hlkhmkjhjiih
6|hkh.hkh.hih
7|hhhhhhhhhhh
7|hijjiiiiihh
7|hjkkjiiiiih
7|hjkjjiiiiih
7|hijjiiiiihh
7|hiijiihiiih
7|hiiiihhiiih
8|hhhhhhhhh
"""

# ---------------------------------------------------------------- shoulders and chest (HALF)
# origin column 40, rows 90..148: an ice plate on the hump's top, hanks of the coat sweeping out and
# down over the hump, the deep chest's fringe in two points. The part under the mane is left empty.
CHEST = """
20|AAAAAAAA
18|AAGGGFFFDDAA
17|AGGFFFFDDDDBAaaa
17|AFFFDDDDDDBBAggfaaa
16|aADDDDBBBBBBAAbgff
14|aggAAAAAAAAAAAfdbgff
12|aggffdbgffddbgffddbgff
11|aggfffdbgffddbgfdddbgfd
9|agggfffddbgfdddbffdddbff
8|agggffffdbffdddbgfddddbfd
7|agggfbgffdbffdddbffddddbf
6|aagggfbffddbffdddbfdddddbf
5|agggffbffdddbfddddbffddd
5|aggffdbgfdddbffdddbfdddd
4|agbgffdbfddddbffdddbfddd
4|agbffddbffdddbfddddbfddd
3|aggbffddbfdddbffdddbfddd
3|aggbfdddbffddbfddddbffdd
3|agfbffdbfddddbfddddbfddd
2|aagfbfddbffdddbffdddbfdd
2|aggfbffdbfddddbfddddbfdd
2|agffbfddbffdddbffdddbddd
2|agfbbffdbfddddbfddddbfdd
2|aggfbfddbbfdddbffdddbfdd
2|aggfbffddbfdddbbfdddbddd
2|agffbffdbfddddbfdddbbfdd
2|agfbgfddbffddbbfddddbfdd
3|aggbffdbbfdddbffdddbfdd
3|aggbfdddbfddddbffddbbdd
3|agfbffddbffdddbfdddbfdd
4|aggfbfdbfddddbffddbbdd
5|agbffdbbfdddbffdddbfd
6|agfdbffddddbfdddbbdd
6|aagdbfddddbffdddbfdd
7|agfbfdddbbfddddbddd
8|aagbfdddbfddddbfdd
9|agddbfddddbfdddbfddddbfdddddbfddddbfddddbfddbdd
10|agdbfddddbfdddbffdddbfdddddbfdddbbfddddbfddbdd
11|agbfddddbffddbfddddbfdddddbbfdddbfdddddbfdbdd
12|agfddddbfdddbbfdddbfddddddbfddddbfdddddbfdbd
13|agddddbfddddbfdddbbfdddddbfddddbbfddddbfddb
14|agdddbbfdddbfddddbfdddddbbfdddbfdddddbfddd
14|aagddbfddddbfdddbbfddddbfdddddbfdddbbfdddd
15|agdddbfdddbbfdddbfdddddbfddddbfddddbbfddd
16|agddbbfdddbfddddbfdddbbfdddddbfdddbfdddd
17|agdbfdddbbfddddbfdddbfddddbbfdddbfddddd
18|aagbfdddbfdddbbfddbfdddddbfdddbbfddddd
20|agbfddbbfdddbfdddbbfddddbfddbbfddddd
21|aagfdbfdddbfddbbaaafdddbfdddbbfdddd
22|aagdbfddbfddbba..afdddbfddbbfddddd
23|agdbfddbfdbba....afddbbfdddbfdddd
25|agbfddbba(.7)afdbbfdddbfddba
26|agfbba(.10)afdbfddbbfdba
27|agba(.12)afbbfddbdba
28|aa(.14)afdbfdbba
45|afbfdba
46|afdba
47|aba
48|a
"""

# ---------------------------------------------------------------- the mane (HALF, origin column 60)
# rows 62..146: a dark collar of long hair from the withers over the chest, in long points; three
# pale strands lie on it.
MANE = """
30|hhhhhh
26|hhmmlllkkk
24|hmmllkkikkkk
23|hmmlkkikkkikk
22|hmllkkikklkikk
21|hmmlkkiklkkikkk
20|hmllkikklkkikkkk
20|hmmlkikkklkikkik
19|hmllkkikklkkikkik
19|hmmlkkiklkkkikkki
18|hmllkkiklkkikkkikk
18|hmmlkikklkkikkikkk
17|hmllkkikkklkikkikkk
17|hmmlkkiklkkkikkkikk
16|hmllkkikklkkikkkikkk
16|hmmlkikkklkkikkikkkk
15|hmllkkikklkkikkkikkkk
14|hmmlkkikklkkikkikkkkik
13|hmllkikklkkikkkikkkkikk
13|hmmlkikkklkikkikkkkkikk
12|hmllkkikklkikkkikkklkikk
11|hmmlkkikklkikkikkkklkkikk
10|hmllkkikkdkkikkkikkklkikkk
10|hmmlkikkkdikkkikkkkklkikkk
10|hmllkikkkddikkikkklkkkikkk
9|hmmlkkikkkdikkikkkklkkikkkk
9|hmllkkikklddikikkklkkkikkkk
9|hmmlkikkklkdikkikklkkikkkkk
8|hmllkkikkklkikkikkkklkikkkkk
8|hmmlkkikklkkikkkiklkkkikkkkk
8|hmllkikkdlkkikkikkklkkkikkkk
8|hmmlkikkdkkkikkkikklkkkikkkk
7|hmllkkikddkkikkikkkklkkikkkkk
7|hmmlkkikkdkkiklkikkklkkikkkkk
7|hmllkikkkdkikklkkikklkkkikkkk
7|hmmlkikkkkkiklkkikkkklkikkkkk
6|hmllkkikkkkiklkkikkklkkkikkkkk
6|hmmlkkikklkikkkkikklkkkikkkkkk
6|hmllkikkklkikkkikklkkkikkkkkkk
6|hmmlkikkklkikkkilkkkikkkilkkki
5|hmllkkikklkkikkilkkkikklkikkkik
5|hmmlkkikklkikkkilkkikkklkikkkil
5|hmllkikkklkikkddikkikkklkikkilk
5|hmmlkikklkkikkddikkkikklkkikilk
4|hmllkkikklkkikkddikkkiklkkikkilk
4|hmmlkkiklkkkikkdkikkkikklkikkilk
4|hmllkikkklkkikddkikkikkklkikkkil
4|hmmlkikklkkikkddikkkikkklkkikkil
3|hmllkkikklkkikkdkikkkikddklkikkil
3|hmmlkkiklkkkikkdkikkikkddlkkikkil
3|hmllkikkklkkikddikkkikkddkkikkkil
3|hmmlkikklkkikkkdikkikkkddklkikkil
2|hmllkkikklkkikkkiikkkikkddkkikkkil
2|hmmlkkiklkkkikkikkkkikkddklkikkilk
2|hmllkikkklkkikkiklkkikkdkkkikkkilk
2|hmmlkikklkkikkkiklkikkkdkklkikkilk
1|hmllkkikklkkikkiklkkikkddkkikkkilkd
1|hmmlkkiklkkkikkikkkkikkkdklkikkildd
1|hmllkikkklkkikkkilkkikkddkkkikkiddk
1|hmmlkikklkkikkkilkkikkkdkklkikkiddk
0|hmllkkikklkkikkilkkkikkddkkikkkikddk
0|hmmlkkiklkkkikkikkkkikkkdklkikkikdkk
0|hhmlkikkklkkikkiklkkikkkkkkkikkikdkk
2|hhmkikkklkkikkiklkkikkkklkikkikdkk
4|hhmkkklkkikkikkkikkklkkikkikddkk
6|hhmklkkikkikkkikkkkkkikkikdkkk
8|hhmkkikkiklkikkklkkikkikkkkk
10|hhmkikkikkkiklkkkikkikkkkk
12|hhmkkikkkiklkkikkkikkkkk
12|hmlkikkkikkkklkikkikkklk
13|hmlkikkikkkklkkikkikklk
13|hmmkikkikkkkkkikkkikklk
14|hmlkikkikkkkkhikkikklk
14|hmlkikkikkkkihhmkkikkl
15|hmlkikkikih...hmkikkl
15|hmlkikkiih....hmkkikl
16|hmlkikih(.6)hmkikl
16|hmlkiih(.7)hmkkil
17|hmih(.10)hmkil
17|hih(.11)hmkkl
18|h(.13)hmkl
32|hmkl
33|hml
33|hik
34|hh
"""

# ---------------------------------------------------------------- the head (HALF, origin column 60)
# rows 46..104: the long pale face tapering to a dark muzzle, an ear out to the side with a dark
# inside, a brow slanting down to the nose over the eye's socket, the nostril; it ends on the mouth
HEAD = """
22|oooooooooooooo
20|oouuuuuuuuuuuuuu
18|ouuuttttttttttuuuu
18|outtttttttttttuuuu
18|outtttrtttttttuuuu
18|outttrtttttrttuuuu
18|outttttttttrttuuuu
18|outttttrtttttttuuu
12|ooooooptttttttrtttttuuuu
4|oooooooouuuuuttttttttttrttttuuuu
0|oooouuutiiiiiiitttttttrttttttttuuuuu
0|ouuuttiiiiiiiiiptttttttttrtttttuuuuu
0|oottttiijjjjjiipttttttttttttrttuuuuu
1|ootttiijjjjjiiptttttrtttttttttuuuuu
1|opptttiijjjjiipttttttttrttttttuuuuu
2|oopttttiijjiiptttttttttttrtttuuuuu
3|ooptttttiiiiptttttttttttttttuuuuu
3|ooppttttttttpttttpppttttttttuuuuu
4|oopppttttttpttttpppppptttttuuuuu
8|ooopppppttttpppppppppttuuuuu
13|ooopttooopppppppppuuuuu
17|ottoooooopppppppuuu
18|ttooooooooopppuuuu
18|ttoooooooooooopuuu
18|ttoooooooooootuuuu
18|ttpoooooooopttuuuu
18|tttppppppppttttuuu
18|ttttuuuuuuttttuuuu
19|ottttttttrttttuuu
19|otttrttttttttuuuu
19|ottttttttttrtuuuu
20|otttttrttttuuuuu
20|ottttttttrttuuuu
20|otttrtttttttuuuu
21|otttttttrttuuuu
21|ottrttttttuuuuu
21|otttttrttttuuuu
22|otttrttttuuuuu
22|ottttttrttuuuu
22|otttttttttuuuu
23|otttrttttuuuu
23|ottttttrtuuuu
23|otttttttttuuu
23|ottrtttttuuuu
24|otttttrttuuu
24|ottttttttuuu
24|otttrttttuuu
24|otttttttttuu
24|oppppppppppp
24|ohmmllllkkkk
24|ohmlllkkkkkk
24|ohmllkkkkkjk
24|ohmlkkkhhhkk
24|ohmlkkkhhhjk
24|ohlkkkkkhhjj
24|ohlkkkkkkjjj
24|ohkkkkkjjjjj
24|ohkkjjjjjjii
24|ohhhhhhhhhhh
"""

# the chin (HALF, typed in frame columns; rows 103..109): it drops when the mouth opens
JAW = """
85|hhhhhhhhhhh
85|hkkjjjjjjii
85|hkjjjjiiiii
86|hkjjjiiiii
87|hjjiiiiii
89|hhiiiii
91|hhhhh
"""
# the inside of the mouth (HALF, typed in frame columns; rows 100..111): murk
MOUTH = """
86|O(P9)
86|OP(P4)QQQQ
86|O(P4)(Q5)
86|OPP(P3)QQQQ
86|O(P6)QQQ
87|O(P8)
87|OP(P4)QQQ
87|O(P5)QQQ
88|O(P7)
88|OPP(P5)
89|O(P6)
90|(O6)
"""

# the image-left eye in its socket: narrow, slanting down to the nose (rows 68..71, origin column 81)
EYE_OPEN = """
0|WYYYYW
0|Y$$%%$YW
1|WY$%$YYW
3|WYYYW
"""
EYE_SHUT = """
0|WWWWWWWW
1|VVVVVV
"""

# the core crystal on the brow (whole map, 14 x 14)
CORE = """
6|VV
5|V%$V
4|V%$$YV
3|V%$$$YYV
2|V%$$%$YYWV
1|V%$$%%$YYWWV
0|V$$$%$$YYYWWWV
0|VY$$$$YYYWWWWV
1|VYY$$YYYWWWV
2|VYYYYYYWWV
3|VYYYYWWV
4|VYYYWV
5|VWWV
6|VV
"""

# ---------------------------------------------------------------- effects
# ice crystals rising round it (the ring): a large and a small one
SHARD_L = """
5|AA
4|AGGA
4|AGFA
3|AGGFDA
3|AGFFDA
2|AGGFFDBA
2|AGFFDDBA
1|AGGFFDDBBA
1|AGGFDDDBBA
0|AGGFFDDDBBBA
0|AGFFFDDDBBBA
0|AGGFFDDDDBBA
0|AGFFDDDDBBBA
0|AGGFFDDDBBBA
1|AGFFDDDBBA
1|AGGFDDDBBA
1|AGFFDDBBBA
2|AGFFDDBA
2|AGGFDBBA
2|AGFDDBBA
3|AGFDBA
3|AGGDBA
4|AFDA
5|AA
"""
SHARD_S = """
3|AA
2|AGFA
2|AGDA
1|AGGFDA
1|AGFDBA
0|AGGFDDBA
0|AGFFDBBA
0|AGGFDDBA
0|AGFDDBBA
1|AGFDBA
1|AGGDBA
1|AGFBBA
2|AGDA
2|AFBA
3|AA
"""
# a chip of ice thrown up by the slam
CHIP = """
2|AA
1|AGFA
0|AGFDBA
0|AGGDBA
0|AGFBBA
1|AFBA
2|AA
"""
# phase 2: glowing seams down the shoulders (whole maps)
CRACK_L = """
0|WW
0|$W
1|$W
1|$WW
2|$$W
3|$W
3|$W.W
4|$WW$
5|$W
5|$W
6|$WW
7|$W
7|$$W
8|$W
9|$W
9|WW
"""
CRACK_R = """
2|WW
2|W$
1|W$
1|WW$
3|W$
3|W$
4|W$$
0|W.W$
0|$WW$
5|W$
5|WW$
6|W$
7|W$
7|W$$
8|W$
8|WW
"""

# ---------------------------------------------------------------- the purification (HALF maps)
# frame 3 (typed in frame columns, rows 118..170): the body slumped on the ground, its coat still on
# its back, the murk rising up it in tongues. The part under the fallen head is left empty.
FALL_A = """
80|a
74|aaagggf
69|aaagggfffbgf
65|aagggffffbgffbgf
62|aagggfffbgfffdbgfdb
59|aaggfffbgffddbgffdbgfd
57|aagggfbgfffdbgfdddbffdbf
55|aaggffbgffddbffdddbfdddbfd
53|aagggfbffdddbgfdddbffddbbfdd
51|aaggfdbgfdddbffddddbfdddbfdddb
50|aggffdbffddbbfdddddbffddbbfdddb
48|aagfddbbfdddbfddddbbfdddbfddddbfd
47|aggfdbbfddddbfdddbbfddddbfdddbbfdd
46|aagfdbfdddbbfddddbfdddbbfddddbfdddb
45|aggfdbbfdddbfddddbbfdddbfddddbbfdddb
44|aagfdbfddddbfdddbbfddddbfdddbbfddddbf
43|aggfdbbfdddbbfdddbfdddddbfddbbfdddbfdd
42|aagfdbfddddbfddddbbfdddbfdddddbfdddbbfd
42|agfddbbfdddbfdddbbfddddbfddbbfddddbfddd
41|aagdbbfddddbfdddbfdddddbbfddbfdddddbfddb
41|agfdbfdddbbfddddbfdddbbfdddddbfddbbfdddd
40|aagdbPPdddbfdddbbfdRRdbfdddbbfddPPdbfdddd
40|agdbPPPPdbfddbbRRfRRRdbfddbbPPdPPPdbfddPP
39|aagPPRRPPbbfdRRRRRRRRbfdPPPPPRRPPPbbdPPPP
39|OOU(T15)UU(R12)O(P9)
38|OUU(T16)(R14)OO(P8)
38|OOT(T14)UU(R15)(P7)OO
37|OUU(S17)(Q13)O(Q10)
37|OOU(S15)TT(Q14)(Q8)OO
36|OUT(S16)(Q15)O(Q10)
36|OOU(R17)(P13)UU(R10)
35|OUU(R16)O(P14)(R12)
35|OOT(R18)(P12)TT(R11)
34|OUU(Q16)O(Q20)(S22)
34|OOU(Q18)(Q19)TT(S20)
33|OUT(Q17)O(Q21)(S21)
33|OOU(P18)(R20)UU(T20)
32|OUU(P17)O(R22)(T21)
32|OOT(P19)(R21)(T19)UU
32|OUU(Q18)O(S22)(S20)
31|OOU(Q20)(S20)TT(S20)
31|OUT(Q19)O(S23)(S19)
31|OOU(R18)UU(T22)(R20)
30|OUU(R21)(T21)O(R20)
30|OOT(R19)UU(T23)(R19)
30|OUU(S20)O(S22)(Q20)
30|OOU(S22)(S20)O(Q20)
30|OUT(S20)TT(S21)(Q20)
30|OOU(T21)O(R21)(P20)
30|OUU(T19)UU(R22)(P20)
30|OOT(T22)(R20)O(P20)
31|OO(S21)(Q22)(Q20)
32|(O64)
"""
# frame 4 (typed in frame columns, rows 142..169): a low mound of murk, tufts of the coat left in it
FALL_B = """
84|(O12)
78|OOO(U6)(T9)
73|OOUU(T10)UU(R7)
69|OOU(S12)(Q10)OO
65|OUU(S13)TT(Q13)
62|OOT(S14)(Q12)O(Q4)
59|OUU(R15)agfa(P9)(R6)
56|OOU(R14)agfda(P12)(R6)
53|OUT(R16)aggfdba(P10)UU(R5)
51|OOU(Q15)afdbba(Q13)(S8)
48|OUU(Q17)abba(Q14)TT(S8)
46|OOT(Q18)O(Q15)(S13)
44|OUU(P17)(R14)agfa(T14)
42|OOU(P18)O(R12)aggfda(T14)
40|OUT(P19)(R13)afdbba(T15)
38|OOU(Q18)UU(S14)abba(S17)
36|OUU(Q20)(S20)O(S16)
35|OOT(Q19)O(S19)TT(S17)
33|OUU(R20)(T20)UU(R18)
32|OOU(R19)O(T21)(R20)
31|OUT(R21)UU(T20)(R19)
30|OOU(S20)(S22)O(Q20)
29|OUU(S21)TT(S21)(Q20)
28|OOT(S22)O(S22)(Q20)
28|OUU(T20)UU(R23)(P20)
28|OO(T22)(R22)O(P21)
29|O(P66)
31|(O65)
"""
# frame 5 (typed in frame columns, rows 136..170): the heap of coat that is left, its strands by turns
# the grey-tan coat, the pale face hair and the dark mane
REMAINS = """
80|aaaaaaaaaaaaaaaa
78|aaggbgffffimmkkput
75|aapuuttbgfffdimmkkput
73|aapuuttrrbgffddimkkkptt
71|aammpuuttrrbgfdddimmkkptr
68|aaimmkkputtrrrbffdddimkkkput
66|aagfimmkkputrrrrbgfdddimkkiptt
64|aaggfdimkkkputtrrrbffdddimmkkptr
61|aabggffddimmkkpuutrrrbgfdddimkkkput
59|aauubgfffddimkkiputrrrpbffdddimmkkptt
57|aauutrbgffdddimmkkputtrrrbgfddbimkkkptr
54|aagpuuttrbffddddimkkkputrrrrbgfdddimmkiput
52|aaggfputtrrbgfddddimmkkpuutrrrbffdddimkkkptt
51|aggffdputrrrbffddddimkkiputtrrpbgfdddimmkkptr
51|agfffdpuutrrbgfdddbimmkkputrrrrbffdddimkkkput
50|aagffddputtrpbffddddimkkkpuutrrrbgfddbimmkiptt
50|agffdddputrrrbgfddddimmkkputtrrrbffdddimkkkptr
49|agffddddpuutrrbffdddbimkkiputrrrpbgfdddimmkkput
49|aagfddddputtrrbgfddddimmkkpuutrrrbffddbimkkkptt
48|agffdddddputrrpbffddddimkkkputtrrrbgfdddimmkiptr
48|agfdddddbpuutrrbgfdddbimmkkputrrrrbffdddimkkkput
47|aagfddddddptrrrpbfdddddimkkkptrrrrpbfddddimkkiprr
47|agfddddddbputrrrbfdddbbilkkkpttrrrrbfdddbimkkkptr
46|aagfdddddddptrrrrbfdddddimkkiptrrrppbfddddikkkkprr
46|agfddddddbbptrrrpbfdddbbimkkkptrrrrrbfddbbimkkiptr
45|aagfdddddddbptrrppbfddddbikkkkptrrrrpbfdddbimkkkprr
45|agfdddddddbbptrrrpbfdddbbimkkiptrrrppbfddbbikkkiprp
44|aagfdddddddbbprrrppbfddbbbikkkkptrrrppbfddbbimkkiprr
44|agfdddddddbbbptrrppbfdddbbikkkiprrrrppbfdbbbikkkkprp
43|aagfddddddbbbbprrrppbfddbbbikkiiptrrpppbfddbbikkkippr
43|agfddddddbbbbbprrpppbddbbbbikkkiprrrpppbdddbbikkiiprp
42|aagfdddbdbbbbbbprrpppbddbbbbikiiiprrppppbddbbbikkiippp
42|agfddbbbbbbbbbbprppppbdbbbbbikiiiprpppppbdbbbbikiiippp
41|aabbbb(b10)(p6)(b7)(i5)(p7)(b6)(i5)ppp
41|(a55)
"""

# ---------------------------------------------------------------- marks laid over the coat (whole maps)
# pale hanks hanging on the shoulders and chest, a dark underlock, rime on the humps and the mane,
# the feathering down the back of a front cannon
HANK_A = """
1|oo
0|ouuo
0|ouutpo
0|outtrpo
0|ouutrpo
0|outtrpo
1|outtrpo
1|ouutrpo
1|outrrpo
1|outtrpo
2|ouutrpo
2|outtrpo
2|outrrpo
2|ouutrpo
3|outtrpo
3|outrpo
3|ouutpo
4|outpo
4|ouupo
5|oto
5|oo
"""
HANK_B = """
0|oo
0|ouuo
0|outpo
1|outrpo
1|ouutpo
2|outrpo
2|ouurpo
3|outrpo
4|outpo
4|ouupo
5|otpo
6|oto
7|oo
"""
HANK_C = """
0|hh
0|hmih
0|hmkih
1|hmkiih
1|hlkkih
2|hmkiih
2|hlkkih
3|hmkih
3|hlkih
4|hmih
4|hih
5|hh
"""
RIME_A = """
2|AAAAAA
0|AAGGFFFDAA
0|AGFFDDDBBA
1|AADDBBBAA
3|AAAAA
"""
RIME_B = """
1|AAAA
0|AGGFDA
0|AFDBBA
1|AAAA
"""
RIME_C = """
1|AA
0|AGFA
1|AA
"""
FEATHER = """
2|oo
1|ouo
1|outo
0|outpo
0|ouupo
0|outrpo
0|outppo
1|ouupo
1|outpo
1|otrpo
1|ouupo
2|outpo
2|otpo
2|ouupo
3|outo
3|otpo
3|ouo
4|oto
4|oo
"""
# the ruff: long hair standing out at the side of the neck (HALF, rows 76..109, origin column 58)
RUFF = """
9|hh
7|hhmh
6|hmmlkh
5|hmllkkih
4|hmmlkikkh
3|hmllkkikkh
3|hmmlkikklkh
2|hmllkkiklkkh
2|hmmlkkikkkikh
1|hmllkikkklkkih
1|hmmlkkikklkikh
1|hmllkkiklkkkih
0|hmmlkikkklkkikh
0|hmllkkikklkikkh
0|hmmlkkiklkkikkh
0|hhmlkikkklkkikh
1|hmllkkikklkikh
1|hmmlkikklkkkih
1|hhmlkkikkklkih
2|hmllkikklkkih
2|hmmlkkikklkih
2|hhmlkikkklkih
3|hmllkkiklkih
3|hmmlkikkkkih
4|hmlkkikklih
4|hhmkikkklih
5|hmlkkiklih
6|hmkikkkih
6|hhmkkikih
7|hmkikkih
8|hmkkiih
9|hmkiih
10|hmiih
11|hhhh
"""
# a tongue of murk creeping up (the purification)
DRIP = """
2|OO
1|OTRO
1|OTRPO
0|OUTRPO
0|OTRRPO
0|OTRPPO
1|ORPPO
1|OPPO
2|OO
"""
# where they lie on the body in the rest pose (the two halves are not mirrored)
MARKS = (("HANK_C", 52, 98), ("HANK_A", 46, 100), ("HANK_A", 56, 104), ("HANK_B", 44, 112), ("HANK_C", 62, 112),
         ("HANK_A", 50, 118), ("HANK_B", 58, 122), ("HANK_B", 64, 130),
         ("HANK_C", 130, 98), ("HANK_A", 134, 101), ("HANK_A", 126, 107), ("HANK_B", 139, 110), ("HANK_C", 122, 114),
         ("HANK_A", 136, 116), ("HANK_B", 128, 124), ("HANK_B", 120, 131),
         ("RIME_A", 50, 93), ("RIME_A", 132, 94), ("RIME_B", 44, 101), ("RIME_B", 140, 103))
MANE_MARKS = (("RIME_B", 78, 64), ("RIME_B", 108, 66))

HALF = {"FLEG", "FLEG_FOLD", "HIND", "RUFF", "CHEST", "MANE", "HEAD", "JAW", "MOUTH", "FALL_A", "FALL_B", "REMAINS"}
RELIGHT = {"FLEG", "FLEG_FOLD", "HIND"}  # upright limbs: the mirrored one is lit from the left too
PLACE = {
    "FLEG": (40, 122), "FLEG_FOLD": (42, 122), "HIND": (54, 118), "RUFF": (58, 76), "CHEST": (40, 90),
    "MANE": (60, 62), "HEAD": (60, 46), "JAW": (0, 103), "MOUTH": (0, 100), "EYE_OPEN": (81, 68),
    "EYE_SHUT": (81, 69), "CORE": (89, 38), "CRACK_L": (48, 104), "CRACK_R": (133, 106),
    "FALL_A": (0, 118), "FALL_B": (0, 142), "REMAINS": (0, 136),
}
