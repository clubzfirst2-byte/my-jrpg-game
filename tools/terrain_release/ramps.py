"""Terrain palettes (地形の色) — PROPOSAL, awaiting approval (docs/art-candidates/terrain/TERRAIN_PROPOSAL.md).

Every ramp is 5 tones: 0 outline / 1 shadow / 2 core / 3 light / 4 highlight, lit from the top left.
Ground ramps are kept LOWER in contrast and saturation than the characters' ramps (the hero's cloak
core is #6a9048), so people and objects always stand out from the ground.
"""

# --- used by the wave-1 samples ---
SAMPLE = {
    "grass": ["#1e3c22", "#31622f", "#46843c", "#62a24a", "#88c060"],  # tile.grass (island / default)
    "meadow": ["#2a4a1c", "#4a7c2c", "#68a03c", "#88bc50", "#b4d872"],  # plains.grass
    "dirt": ["#3a2416", "#664430", "#8a6444", "#a8805a", "#c49e72"],  # tile.path
    "sand": ["#6e5232", "#c4a26a", "#e0c48a", "#eed8a6", "#faf0d2"],  # tile.sand (island beach)
    "water": ["#132e5a", "#1f4f8a", "#2d6aa8", "#5694cc", "#b0dcf6"],  # tile.water
    "earth": ["#22130c", "#4a2c1c", "#6a4430", "#8a5e40", "#a87c56"],  # face.earth
    "pebble": ["#24232a", "#56545c", "#807c80", "#a8a29e", "#d4ccc2"],  # small stones on paths / faces
    "wood": ["#1e1008", "#4a2c16", "#6e4424", "#906038", "#b07e50"],  # tile.walltop (= hero BASE_RAMPS wood)
    "leaf": ["#0c2214", "#1a4426", "#2a6432", "#45883e", "#74b056"],  # obj.tree canopy
    "bark": ["#1e1008", "#3e2414", "#5e3a22", "#7e5432", "#9c7048"],  # obj.tree trunk
    "flower_w": ["#4a4a5a", "#b4b4c4", "#eeeef4", "#ffffff", "#ffffff"],
    "flower_y": ["#6a4a10", "#c08a20", "#f0c040", "#f8dc80", "#fff4c0"],
    "flower_p": ["#5a2038", "#b0507a", "#e080a8", "#f4b0cc", "#ffe0ee"],
    "shell": ["#6a4a3a", "#c8987e", "#f0cab0", "#fae2d0", "#fff6ee"],
}

# --- proposed for the rest of the regions (not drawn yet; shown as swatches in palettes.png) ---
REGIONS = {
    "平原 plains": {"草": SAMPLE["meadow"], "道": SAMPLE["dirt"], "花": SAMPLE["flower_y"]},
    "島 island (base)": {"草": SAMPLE["grass"], "砂": SAMPLE["sand"], "水": SAMPLE["water"], "崖": SAMPLE["earth"]},
    "砂漠 desert": {
        "赤砂": ["#5a2a1a", "#a0583a", "#c8784c", "#dc9a66", "#f0c08c"],
        "岩": ["#2e1a14", "#6a4034", "#8e5c48", "#b07c62", "#d0a084"],
        "枯草": ["#3a3214", "#6e6024", "#9a8838", "#bca850", "#dccc78"],
    },
    "森 forest": {
        "苔草": ["#10241a", "#1e4028", "#2e5a34", "#447640", "#64944e"],
        "落葉": ["#2a160c", "#5a3418", "#84522a", "#a8723c", "#c89a5c"],
        "針葉": ["#08180e", "#143420", "#1e4a2c", "#2e6838", "#4a8a48"],
    },
    "雪山 snow mountains": {
        "雪": ["#3a4a66", "#8a9ab8", "#cfd9ea", "#e8eef8", "#ffffff"],
        "岩": ["#1e2028", "#4a4e5c", "#6e7484", "#9298a6", "#b8bec8"],
        "氷": ["#1a3a5a", "#4a86b0", "#8cc4e4", "#c4e8f8", "#f4fcff"],
    },
    "湖 lake": {
        "岸草": ["#173a2c", "#2a6446", "#3e8a58", "#5aa86a", "#8acc84"],
        "浅瀬": ["#1a4a6a", "#2c7a9a", "#48a2bc", "#7cc8d8", "#c8f0f4"],
        "葦": ["#2a3014", "#566024", "#7e8a38", "#a4ae56", "#ccd47e"],
    },
    "遺跡 ruins": {
        "石": ["#1c1a22", "#4a4652", "#6e6a74", "#928c94", "#bcb4b4"],
        "苔": ["#142a1c", "#2a4a2c", "#3e663a", "#5a844a", "#80a862"],
        "金属": ["#14181e", "#3a4450", "#5e6a78", "#8894a2", "#c4ccd6"],
    },
}
