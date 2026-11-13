"""The boss ramps (7 steps: 0 outline, 1 deep shadow, 2 in-between, 3 base, 4 in-between, 5 light,
6 highlight). rotwood / fungus / bone / murk / glow are v2's colours (tools/enemy_v2 at d900394) with
tone 0 lifted to luma 30 (STYLE 3.3), the same values the v3 normal enemies' rig uses (rig.RGBV3).
rotwood_d (wet dark rot) and rotwood_p (dry pale root) are new in v3: two more woods of the same hue,
so the root mass is not one material (STYLE 5.4)."""


def hx(s):
    return (int(s[1:3], 16), int(s[3:5], 16), int(s[5:7], 16))


RAMPS = {k: [hx(c) for c in v] for k, v in {
    "rotwood": ["#281d17", "#3a2a20", "#4c382b", "#5e4636", "#715643", "#846650", "#a88a70"],
    "rotwood_d": ["#2a1c1a", "#32221e", "#3e2b25", "#4a352c", "#5a4236", "#6a5040", "#866854"],
    "rotwood_p": ["#2e221a", "#4a3a2c", "#5e4b3a", "#74604a", "#89745a", "#9e886c", "#c2ac8e"],
    "fungus": ["#3a1a0a", "#8a4420", "#ad5f2d", "#d07a3a", "#dd9151", "#eaa868", "#f8d4a8"],
    "bone": ["#3a3226", "#9a8c70", "#b5a88a", "#d0c4a4", "#dcd1b4", "#e8dec4", "#fff8e4"],
    "murk": ["#2c183c", "#2e1a3e", "#3c2250", "#4a2a62", "#5c3779", "#6e4490", "#9a70c0"],
    "glow": ["#421042", "#6a1e6a", "#8d2f8d", "#b040b0", "#c858c8", "#e070e0", "#ffc8ff"],
}.items()}
GROUPS = [("abcdefg", "rotwood"), ("hijklmn", "rotwood_d"), ("opqrstu", "rotwood_p"), ("ABCDEFG", "fungus"),
          ("HIJKLMN", "bone"), ("OPQRSTU", "murk"), ("VWXYZ$%", "glow")]
