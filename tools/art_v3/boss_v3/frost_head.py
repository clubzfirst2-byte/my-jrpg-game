"""凍て角のヌシ (boss_frost), v3: the hand-drawn maps of the head (pixmap.py syntax).

Legend:  a-g frostfur (the coat)     h-n frostfur_d (dark fur: hollows, the nose, far legs, hooves)
         o-u frostfur_m (the tones between the two)
         A-G ice    H-N ice_d (the deeper ice between ice's tones)    O-U murk    V W X Y Z $ % glow
The face is a long brown deer's face seen from the front, lit from the upper left: the bridge of the
nose is a ridge (its lit side to the left, a light line on the ridge), the right cheek falls into
shadow. One map is the whole face (it is not a mirrored half).
"""

# the face at rest (35 wide; column 17 is the ridge). Rows 0..51: poll, forehead, brow, the eye
# sockets (the eyes are their own parts), the bridge, the muzzle, the nose pad, the upper lip.
FACE = """
9|aaaaaaaaaaaaaaaaa
7|aabddtfffuufffddrrpaa
5|aabdttffffuugfffdddrrppaa
4|abddttfffffuugffffdddrrppba
3|apdttffffffuugfffffdddrrrpbba
3|apdtttfffffuuffffffddddrrppba
3|abdttffffffuufffffdddddrrppba
3|apddtfffffuugfffffddddrrrppba
3|apdttffffuuuffffddfddrrrpppba
3|abdttfffffuuffffdddddrrrppbba
3|abddtfffffuufffffddddrrpppbba
2|aapdttfffffuuffffddddrrrrppbbaa
1|aabbbpppdtfffffuufffddrpppbbiibaa
0|aabiiiiibbdtffffuufffddrbbiiiiiibaa
0|abiaaaaaaaibdtfffuuffdrbiaaaaaaaiba
0|abiaaaaaaaaibdtffuufdrbiaaaaaaaaiba
0|abbiaaaaaaaaibdffuufdbiaaaaaaaaibba
0|apbiiaaaaaaaibdffuufdbiaaaaaaaiibpa
1|apbbiiiiiiibbdffuufdrbbiiiiiiibpa
1|apdtbbbbbpddtffuuffdrrpbbbbbbppba
2|apdttddpdttfffuufffddrrpppprpba
2|apdttttttfffffuufffdddrrrrpppba
3|apdtttttfffffuuffffddrrrppbba
3|abdttttffffffuufffdddrrrrppba
3|abddtttfffffuugfffddddrrrpppa
4|abdtttfffffuugffdddddrrppba
4|abdttffffffuuffffdddrrrppba
4|apdttfffffuugfffddddrrpppba
4|abddtfffffuuffffdddrrrrppba
5|abdttffffuugfffdddrrrppba
5|abdtfffffuuffffdddrrpppba
5|apdttffffuuffffddrrrrppba
5|abdttfffuugffffdddrrrppba
5|abddtffffuuffffdddrrpppba
5|abdttffffuufffddddrrrppba
5|abdtfffffuuffffdddrrrppba
5|abdttffffuuufffddddrrppba
5|abdtffffuuuuffffdddrrppba
5|abdtffffuuuugffffdddrrpba
5|abdttfffuuuuuffffddrrrpba
5|abdtffffuuuuffffdddrrppba
5|abdtffuaaaaaaaaaaaddrppba
5|abdtffaikmmmkkkiiiadrppba
5|abdtfakmnnmkkkkiiiiarppba
5|abdtakmmmkkkkkkkiiiiappba
5|abdtakkmkaakkkkaaiiiappba
5|abdtakkkaaakkkaaaiiiappba
5|abdtaikkkaaikkiaaiiiapbba
6|abdpaiikkkiaiikiiiapbba
6|abdtdaaaaaaaaaaaaarppba
7|abdttffddpaprrrppbbba
7|abbdttfddpapprrrpbbba
"""

# the lower jaw (drops when the mouth opens)
JAW = """
0|abiiaaaaaaaaaaaiiba
1|abpddttddrrrppbba
2|abbpddddrrppbba
4|aaaaaaaaaaa
"""

EAR = """
2|aaaaaaaaaaaaaaaaaaaa
1|agfffffffftttttdddrrp
0|aafttddddrrrrrpppbbbbb
0|afdbbiiiiiiiikkkkkmmbp
1|afdbiiiiiiiikkkkkmmmd
2|adbiiiiiiikkkkkmmmmd
3|adbbiiiiikkkkkmmmnd
4|apbbiiiikkkkmmmnnd
6|apbbiiikkkmmmnnd
8|aapbbiikkkmmmd
10|aapbbbkkkmmd
12|aaappbbbpd
15|aaaaaaa
"""

EYE_OPEN = """
aaaa......
aY$Yaaa...
aWY$%$Yaa.
.aaWY$%$Ya
....aWY$Wa
......aaa.
"""

EYE_SHUT = """
aaaa......
abbbaaa...
.aaabbbaa.
....aaabba
.......aa.
"""

# the core on the brow: a cut gem, four facets
CORE = """
7|VV
6|V$YV
5|V$$YYV
4|V$%$YYWV
3|V$%%$YYYWV
2|V$$%%$YYYWWV
1|V$$$%$$YYYYWWV
0|V$$$$$$$YYYYWWWV
0|VY$$$$$%YYYYWWWV
0|VYYYYYYYWWWWWWWV
1|VYYYYYYWWWWWWV
2|VYYYYYWWWWWV
3|VYYYYWWWWV
4|VYYYWWWV
5|VYYWWV
6|VYWV
7|VV
"""
