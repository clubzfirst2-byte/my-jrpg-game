"""Ramps added for the release wave (wave 2). 5 tones each: 0 outline, 1 shadow, 2 core, 3 light, 4 highlight.

GUIDE2: copied unchanged from ART_STYLE_GUIDE.md (origin/docs/art-style-guide 7e0f6bc).
  Those from 2.5 (cave_rock, mount_rock, room_rug) are still marked provisional there:
  if the terrain table changes them, change them here too and re-run gen_release.py.
NEW2: new ramps (marked 新 in docs/art-release/objects/PRODUCTION.md) for the art director to register in
  chapter 2 of the guide, like the wave-1 NEW ramps in draw.py.
"""

GUIDE2 = {
    "shirt": ["#4a4640", "#a8a296", "#e4e0d6", "#f6f4ee", "#ffffff"],  # 2.2 the hero's shirt (glider cloth)
    "iron": ["#14161c", "#40464f", "#6c7480", "#9aa2ae", "#d4dae2"],  # 2.1 note: iron (anvil, stove, hoops)
    "enemy_magic": ["#2a0a2a", "#6a1e6a", "#b040b0", "#e070e0", "#ffc8ff"],  # 2.6 enemy bullets (fx.orb)
    "miasma": ["#120a1a", "#2e1a3e", "#4a2a62", "#6e4490", "#9a70c0"],  # 2.6 murk (icon.shard)
    "cave_rock": ["#0c0c12", "#1c1c26", "#2c2c3a", "#403e52", "#585670"],  # 2.5 (provisional) cave dark
    "mount_rock": ["#1c1a24", "#3a3846", "#585668", "#7a788c", "#9e9cb0"],  # 2.5 (provisional) mine stairs
    "room_rug": ["#2a0a10", "#5a1a22", "#7e2a30", "#a04440", "#c06a5a"],  # 2.5 rug (mat, blanket)
}

NEW2 = {
    "linen": ["#3e3a34", "#a49c8c", "#d8d2c4", "#ece8de", "#faf8f2"],  # bed sheet and pillow
    "shock": ["#2a2a10", "#7a7020", "#c8c040", "#eeea88", "#fffff0"],  # shock crystal (electric)
    "berry": ["#2a0a1a", "#6a1630", "#a8263e", "#e05060", "#ffb0b8"],  # red berries
    "cap": ["#3a1008", "#8a2a14", "#c84a24", "#e8783e", "#ffb07a"],  # mushroom cap
    "pepper": ["#3a0a06", "#9a1e10", "#d8361c", "#f86a3a", "#ffc08a"],  # ember pepper
    "stew": ["#2e1608", "#6a3414", "#9a5a24", "#c4843c", "#e8b064"],  # cooked food in a bowl
    "smoke": ["#5a5a62", "#9a9aa2", "#c4c4ca", "#e2e2e6", "#f8f8fa"],  # smoke puffs (light outline)
}

RAMPS2 = {**GUIDE2, **NEW2}
