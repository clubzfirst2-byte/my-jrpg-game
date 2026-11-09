"""Terrain palettes (地形の色) — wave 1 rev 2, awaiting approval (docs/art-candidates/terrain/TERRAIN_PROPOSAL.md).

Every ramp is 5 tones: 0 outline / 1 shadow / 2 core / 3 light / 4 highlight, lit from the top left.
Rule (ART_STYLE_GUIDE 2.3 / 2.5): a GREEN ground's core (tone 2) is darker AND bluer than the hero's
cloak core #6a9048 (lightness 49, hue 92°): lightness gap >= 12 measured on the art itself (not after
the game's x0.8 darkening). No yellow-green ground. Values marked "guide" are ART_STYLE_GUIDE 2.5 as is;
the others are new ramps to be registered in the guide.
"""

GUIDE = {
    "plains.grass": ["#16301c", "#2a5030", "#3c6a38", "#528446", "#6c9e58"],
    "plains.path": ["#3a2c1e", "#6a5238", "#8c7050", "#a88c68", "#c4aa84"],
    "earth.face": ["#1c140e", "#3a2a1c", "#57402a", "#74583a", "#927450"],
    "desert.sand": ["#3e1e12", "#82442a", "#a8603c", "#c27e54", "#daa274"],
    "desert.stone": ["#2e2018", "#6a5240", "#947a60", "#b49a7c", "#d2bc9e"],
    "forest.moss": ["#0c1c16", "#183426", "#244834", "#345e42", "#4a7654"],
    "forest.pine": ["#08161a", "#123028", "#1c443a", "#2a5a4c", "#3e7462"],
    "forest.swamp": ["#10160e", "#232e1c", "#36402a", "#4a5438", "#62684a"],
    "mount.rock": ["#1c1a24", "#3a3846", "#585668", "#7a788c", "#9e9cb0"],
    "mount.snow": ["#3a4866", "#7a8cae", "#b8c8e0", "#dce6f2", "#f8fbff"],
    "mount.ice": ["#16344a", "#346684", "#5e98b4", "#9cc8dc", "#dcf2fa"],
    "lake.grass": ["#12302a", "#244e3e", "#36684c", "#4a825a", "#669c6c"],
    "lake.shore": ["#4e4230", "#9a8866", "#c0ae88", "#d8caa6", "#eee4c8"],
    "lake.deep": ["#081c34", "#143e66", "#22608e", "#3a84b2", "#6aaed2"],
    "ruin.stone": ["#1a1e22", "#3a4246", "#5a6468", "#7c8688", "#a2aaaa"],
    "ruin.glow": ["#08302e", "#146a64", "#22a49a", "#62d6c6", "#c6fff0"],
}

# New ramps proposed by the terrain samples (to be registered in ART_STYLE_GUIDE 2.5).
NEW = {
    "island.sand": ["#6e5232", "#c4a26a", "#e0c48a", "#eed8a6", "#faf0d2"],  # tile.sand (beach)
    "water.surface": ["#132e5a", "#1f4f8a", "#2d6aa8", "#5694cc", "#b0dcf6"],  # tile.water (accepted: darker than splash)
    "pebble": ["#24232a", "#56545c", "#807c80", "#a8a29e", "#d4ccc2"],  # small stones on paths / cliffs
    "wall.stone": ["#221e1c", "#4a4440", "#6c645c", "#8e857a", "#b0a698"],  # tile.walltop capstones
    "tree.leaf": ["#0c2214", "#1a4426", "#2a6432", "#45883e", "#74b056"],  # obj.tree canopy
    "tree.bark": ["#1e1008", "#3e2414", "#5e3a22", "#7e5432", "#9c7048"],  # obj.tree trunk
    "lake.reed": ["#2a2410", "#54461e", "#76632e", "#957f44", "#b29c62"],  # dry ochre reeds (was yellow-green)
    "flower.white": ["#4a4a5a", "#b4b4c4", "#e2e2ea", "#f4f4f8", "#ffffff"],
    "flower.yellow": ["#6a4a10", "#c08a20", "#f0c040", "#f8dc80", "#fff4c0"],
    "flower.pink": ["#5a2038", "#b0507a", "#e080a8", "#f4b0cc", "#ffe0ee"],
    "shell": ["#6a4a3a", "#c8987e", "#f0cab0", "#fae2d0", "#fff6ee"],
}

# Material names used by the generator -> ramp.
SAMPLE = {
    "grass": GUIDE["plains.grass"],  # tile.grass (island) and plains.grass share the guide's dark grass
    "meadow": GUIDE["plains.grass"],
    "dirt": GUIDE["plains.path"],
    "sand": NEW["island.sand"],
    "water": NEW["water.surface"],
    "earth": GUIDE["earth.face"],
    "pebble": NEW["pebble"],
    "stone": NEW["wall.stone"],
    "leaf": NEW["tree.leaf"],
    "bark": NEW["tree.bark"],
    "flower_w": NEW["flower.white"],
    "flower_y": NEW["flower.yellow"],
    "flower_p": NEW["flower.pink"],
    "shell": NEW["shell"],
}

# Swatches per region (palettes.png). (name, ramp, source)
REGIONS = {
    "島・草原 island / plains": [("草 plains.grass", GUIDE["plains.grass"], "guide"), ("道 plains.path", GUIDE["plains.path"], "guide"),
                              ("土の崖 earth.face", GUIDE["earth.face"], "guide"), ("砂浜 island.sand", NEW["island.sand"], "new"),
                              ("水 water.surface", NEW["water.surface"], "new"), ("小石 pebble", NEW["pebble"], "new"),
                              ("花 flower.*", NEW["flower.yellow"], "new")],
    "砂漠 desert": [("赤い砂 desert.sand", GUIDE["desert.sand"], "guide"), ("砂岩 desert.stone", GUIDE["desert.stone"], "guide")],
    "森 forest": [("苔 forest.moss", GUIDE["forest.moss"], "guide"), ("針葉樹 forest.pine", GUIDE["forest.pine"], "guide"),
                 ("沼 forest.swamp", GUIDE["forest.swamp"], "guide")],
    "雪山 snow mountains": [("岩 mount.rock", GUIDE["mount.rock"], "guide"), ("雪 mount.snow", GUIDE["mount.snow"], "guide"),
                         ("氷 mount.ice", GUIDE["mount.ice"], "guide")],
    "湖 lake": [("岸の草 lake.grass", GUIDE["lake.grass"], "guide"), ("浜 lake.shore", GUIDE["lake.shore"], "guide"),
               ("深い水 lake.deep", GUIDE["lake.deep"], "guide"), ("葦 lake.reed", NEW["lake.reed"], "new")],
    "遺跡 ruins": [("石 ruin.stone", GUIDE["ruin.stone"], "guide"), ("光 ruin.glow", GUIDE["ruin.glow"], "guide")],
    "家・木 house / tree": [("壁の上 wall.stone", NEW["wall.stone"], "new"), ("葉 tree.leaf", NEW["tree.leaf"], "new"),
                          ("幹 tree.bark", NEW["tree.bark"], "new")],
}


# ---------------------------------------------------------------------------------------------------
# RELEASE (art/terrain-release): every ramp the release terrain uses, by material name.
# GUIDE / GUIDE_OTHER = ART_STYLE_GUIDE 2.1 / 2.5 / 3.7 / 6.2 values as they are; NEW / NEW_RELEASE =
# added by the terrain work (registered in docs/art-release/terrain/PRODUCTION.md for the guide 2.5).
# ---------------------------------------------------------------------------------------------------
GUIDE_OTHER = {
    "wood": ["#1e1008", "#4a2c16", "#6e4424", "#906038", "#b07e50"],  # guide 2.1
    "iron": ["#14161c", "#40464f", "#6c7480", "#9aa2ae", "#d4dae2"],  # guide 2.1 (guard / smith iron)
    "room.plaster": ["#3a3028", "#7a6a58", "#a8967e", "#c4b49c", "#e0d4c0"],  # guide 2.5
    "cave.rock": ["#0c0c12", "#1c1c26", "#2c2c3a", "#403e52", "#585670"],  # guide 2.5
    "autumn.grass": ["#2e2010", "#5e4420", "#8a6630", "#a88440", "#c4a058"],  # guide 3.7 (autumn grass)
    "fire": ["#5a1a0a", "#c0461c", "#f08a3a", "#ffd060", "#fff4c8"],  # guide 6.2 (fallen leaves use 0-2, as 3.7)
}

NEW_RELEASE = {
    "autumn.foliage": ["#3a1a08", "#7a3814", "#b05a1e", "#d88a30", "#f2b850"],  # autumn.obj.tree canopy
    "cactus": ["#0e2420", "#1e4a3a", "#2e6a4e", "#4a8a62", "#78ae84"],  # obj.cactus (blue-green, hue ~150)
}

RELEASE = {**GUIDE, **NEW, **GUIDE_OTHER, **NEW_RELEASE}
RELEASE_NEW = set(NEW) | set(NEW_RELEASE)
