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

# the face with the head brought down toward the viewer (the slam, the charge): seen more from above,
# the brow is broad and high, the muzzle is short (it points at the ground), and only the top of the
# nose pad shows. 34 rows against the 52 of the face at rest; the jaw is hidden behind the muzzle.
FACE_DOWN = """
9|aaaaaaaaaaaaaaaaa
7|aabdttffuuffffddrrpaa
5|aabdttfffffuugfffdddrrpaa
4|abddtffffffuugfffffdddrrppa
3|apdttffffffuugffffffdddrrrpba
3|apdttfffffffuufffffddddrrppba
3|abdtgffffffuugfffffdddrrrppba
3|apdtggfffffuuffffffddddrrppba
3|apddtfffffuugffffffdddrrrppba
3|abdttffffuuuffffddfdddrrpppba
3|abdtfffffuufffffdddddrrrppbba
3|apddttffffuuffffddddrrrrppbba
3|abdtffffffuugfffdddddrrrppbba
2|aapdttfffffuuffffdddrrrrpppbbaa
1|aabbbpppdtffffuuffffddrpppbbiibaa
0|aabiiiiibbdtfffuuffffddrbbiiiiiibaa
0|abiaaaaaaaibdtfffuuffdrbiaaaaaaaiba
0|abbiaaaaaaaibdtffuufdrbiaaaaaaaibba
1|apbiiiiiiibbdtffuufdrbbiiiiiiibpa
1|apdtbbbbbpddtffuuffdrrpbbbbbbppba
2|apdttddpdttfffuufffddrrpppprpba
3|apdtttffffffuufffffddrrrrppba
4|abdttfffffuugfffddddrrrppba
4|apdtffffffuuggfffddddrrppba
5|abdtffffuuuggffdddrrrppba
5|abdtfffuuuugfffdddrrppbba
5|apdtffuuuuufffffddrrrppba
5|abdtffaaaaaaaaaaaaadrppba
5|abdtfakmnnmkkkkkiiiiarpba
5|abdtakmmmkkkkkkkkiiiiapba
6|abdakkkaakkkkaaiiiiapba
6|abdaiikkkkkkkiiiiiiabba
7|abaaaaaaaaaaaaaaaaaba
9|aaaaaaaaaaaaaaaaa
"""

# the face with the head thrown back (hurt, the roar of the ring, the fall): seen from below, the
# forehead recedes, the eyes sit high, the muzzle is short and the nose pad is wide with both nostrils
# open toward the viewer. The lower jaw hangs under it.
FACE_UP = """
9|aaaaaaaaaaaaaaaaa
6|aabddtfffuuffffdddrrpaa
4|aabdttffffuugfffffddrrrppaa
3|apddtfffffuugffffffdddrrrppba
3|abdttffffffuuffffdddddrrrppba
2|aapdtfffffuugfffffddddrrrpppbaa
1|aabbbpppdtffffuuffffddrpppbbiibaa
0|aabiiiiibbdtfffuuffffddrbbiiiiiibaa
0|abiaaaaaaaibdtfffuuffdrbiaaaaaaaiba
0|abiaaaaaaaaibdtffuufdrbiaaaaaaaaiba
0|apbiiaaaaaaaibdffuufdbiaaaaaaaiibpa
1|apbbiiiiiiibbdffuufdrbbiiiiiiibpa
1|apdtbbbbbpddtffuuffdrrpbbbbbbppba
2|apdttdddttfffuufffddrrrpppprpba
3|apdttfffffffuufffffdddrrrppba
3|abdtfffffffuuugffffddddrrppba
4|abdttfffffuuuuffffdddrrppba
4|apdtffffuuuuugfffddddrrppba
4|abdtfffuuuuuufffffdddrrrpba
4|abdtaaaaaaaaaaaaaaaaaaarpba
4|abdakmmnnmmkkkkkkkkiiiiiaba
4|abakmmkaaaakkkkkaaaakiiiaba
4|abakmkaaaaakkkaaaaakiiiiaba
4|abakkkiaaaikkkiaaaikiiiiaba
5|abaikkkiiikkkkiiikiiiiaba
5|aabaaaaaaaaaaaaaaaaaaabaa
6|abddttffddpaprrrrppbbba
7|abbdttfddpapprrrpbbba
"""

# the eyes narrowed to slits (the slam's blow)
EYE_NARROW = """
aaaa......
aY$Waaa...
.aaaWY$Wa.
.....aaaa.
"""

# the open mouth: the dark of the throat (murk), the tongue's ridge in it
MOUTH = """
1|aaaaaaaaaaaaaaa
0|aOOOPPPPPPPOOOOa
0|aOPPQQQQQQQPPPOa
0|aOPQRRRSRRQQPPOa
1|aOPQRRRQQQPPOa
2|aOPPQQQPPPOa
3|aaaaaaaaaa
"""
