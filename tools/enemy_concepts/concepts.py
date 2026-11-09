"""Enemy & boss DESIGN CONCEPTS (設計案) — not production art.

Writes:
  docs/enemy/concepts.png  flat-colour concept silhouettes next to the approved hero,
                           at 1x (art pixels = what the game shows in HD) and enlarged
  docs/enemy/palette.png   the proposed 5-tone ramps (hex) next to the hero's colours

Run:  python3 tools/enemy_concepts/concepts.py
Uses the shared Canvas of tools/art_proto/pixel.py (materials with 5-tone ramps, light from the
top left, selective outline), the same method as the hero, so the concepts sit in the same style.
Nothing here goes into the game (src/ is not touched). See docs/enemy/ENEMY_BOSS_DESIGN.md.
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.dont_write_bytecode = True  # do not touch the tracked tools/art_proto/__pycache__
sys.path.insert(0, os.path.join(ROOT, "tools", "art_proto"))
from pixel import Canvas, BASE_RAMPS  # noqa: E402

OUT = os.path.join(ROOT, "docs", "enemy")
HERO = os.path.join(ROOT, "src", "art-release", "hero")

# ------------------------------------------------------------------ palette (5 tones each:
# outline, shadow, core, light, highlight). No greens, no hero white/gold/blue as a main colour.
RAMPS = {
    # The murk language (shared by every enemy). Both ramps are the art style guide's own
    # (ART_STYLE_GUIDE.md 2.6): miasma purple for bodies, enemy.magic magenta (hue 300, 60 deg away
    # from the telegraph red #ff3a3a) for glowing cores / crystals / orbs. The glow is the same in
    # every frame: the wind-up shows by SHAPE; the red flash belongs to the program only.
    "murk": ["#120a1a", "#2e1a3e", "#4a2a62", "#6e4490", "#9a70c0"],
    "glow": ["#2a0a2a", "#6a1e6a", "#b040b0", "#e070e0", "#ffc8ff"],
    # Yellow eyes for the living (beast, goblin), as the guide allows (5.1).
    "eye": ["#4a2a08", "#b06a10", "#ffd84a", "#fff2a8", "#fffbe0"],
    # Beast
    "ashfur": ["#1a1418", "#3a3036", "#5a4c50", "#7e6e6e", "#a69690"],
    # Goblin bandit
    "gobskin": ["#24201a", "#4e4636", "#7a6e54", "#a09474", "#c4ba98"],
    "plum": ["#1e1016", "#3e2430", "#5e3a46", "#80565e", "#a07a80"],
    # Ancient machine
    # cool grey stone (hue 240, lightness 59): cool against the warm sandstone (28, 50), lighter than the ruin floor (39); dark bronze bands + dark outline
    "oldstone": ["#1e1e26", "#4e4e5a", "#9696a0", "#bcbcc6", "#e2e2ea"],
    "bronze": ["#24140c", "#5a3418", "#8a5628", "#b0783e", "#d4a064"],
    # Forest core
    "rotwood": ["#1a120e", "#3a2a20", "#5e4636", "#846650", "#a88a70"],
    "fungus": ["#3a1a0a", "#8a4420", "#d07a3a", "#eaa868", "#f8d4a8"],
    # Mountain core
    # warm grey-tan (hue 28, lightness 49): apart from the grey-violet rock (247, 35) and the blue snow
    "frostfur": ["#261e1a", "#55483e", "#8a7a6c", "#b0a294", "#dcd2c6"],
    "ice": ["#1a3040", "#3e6e88", "#7ab4cc", "#b8e4f0", "#f0fcff"],
    # Desert core
    # sand soaked with murk: dark mauve-brown (hue 314, lightness 31), apart from the desert sand (20, 44)
    "murksand": ["#1c1018", "#3e2a3a", "#5e4458", "#82666e", "#a88c88"],
    "mask": ["#2e2a26", "#6e665c", "#a89e90", "#d2cabc", "#f2ece2"],
    # Lake core
    # storm grey-lavender (hue 244, lightness 49): apart from the deep lake (206, 32) and shore grass
    "slate": ["#1c1a26", "#46445a", "#7a7896", "#a4a2bc", "#cccade"],
    "spark": ["#4a3a08", "#b08a10", "#ffe14a", "#fff59a", "#ffffff"],
    "lake": ["#081c34", "#143e66", "#22608e", "#3a84b2", "#6aaed2"],  # = guide lake.deep
    # Final boss
    "ashring": ["#24201e", "#4e4844", "#7c7470", "#a8a09a", "#d6d0ca"],
}
SHINY_TONE = 4

NAMES = {
    "murk": "澱（からだ）＝ガイドの miasma", "glow": "澱の光（核・結晶・玉）＝ガイドの enemy.magic", "eye": "生き物の目（黄）", "ashfur": "灰の毛皮", "gobskin": "小鬼の肌",
    "plum": "野盗の布", "oldstone": "古い石（冷たい灰）", "bronze": "古い青銅", "rotwood": "朽ち木",
    "fungus": "きのこ", "frostfur": "霜の毛（黄みの灰）", "ice": "氷の角", "murksand": "澱の混ざった砂",
    "mask": "石の面", "slate": "嵐の鱗（灰ラベンダー）", "spark": "雷の火花", "lake": "湖の水（ガイド lake.deep）",
    "ashring": "褪せた星環",
}


def capsule(c, x0, y0, x1, y1, r, mat, tone=None):
    xa, xb = int(min(x0, x1) - r - 1), int(max(x0, x1) + r + 1)
    ya, yb = int(min(y0, y1) - r - 1), int(max(y0, y1) + r + 1)
    dx, dy = x1 - x0, y1 - y0
    L = dx * dx + dy * dy or 1
    for y in range(ya, yb + 1):
        for x in range(xa, xb + 1):
            px, py = x + 0.5, y + 0.5
            t = max(0, min(1, ((px - x0) * dx + (py - y0) * dy) / L))
            if (px - x0 - t * dx) ** 2 + (py - y0 - t * dy) ** 2 <= r * r:
                c.put(x, y, mat, tone)


def eye_dot(c, x, y, size=1):
    for dy in range(size):
        for dx in range(size):
            c.put(x + dx, y + dy, "eye", 2)


def glow_dot(c, x, y, bright, size=1):
    for dy in range(size):
        for dx in range(size):
            c.put(x + dx, y + dy, "glow", 3)  # same in every frame (no painted warning)


def to_img(c):
    img = Image.new("RGBA", (c.w, c.h), (0, 0, 0, 0))
    px = img.load()
    for y, row in enumerate(c.colours()):
        for x, p in enumerate(row):
            if p:
                px[x, y] = p
    return img


# ------------------------------------------------------------------ enemies (right-facing)

def beast(wind=False):
    """澱の獣: a lean wolf of ash fur, murk crystals along the spine. 44x32 (guide max), feet on row 30.
    Wind-up = shape only: crouch, head down, jaw open, crystals bristle taller."""
    c = Canvas(44, 32, RAMPS)
    b = 2 if wind else 0
    capsule(c, 12, 20 + b, 10, 30, 2, "ashfur", 1)  # far legs (dark)
    capsule(c, 28, 20 + b, 30, 30, 2, "ashfur", 1)
    capsule(c, 8, 16 + b, 2, 10 + b, 2, "murk")  # tail of murk
    c.ellipse(18, 18 + b, 12, 6, "ashfur")
    c.ellipse(28, 17 + b, 7, 7, "ashfur")
    capsule(c, 14, 21 + b, 13, 30, 2, "ashfur")  # near legs
    capsule(c, 26, 21 + b, 25, 30, 2, "ashfur")
    hy = 17 + b + (2 if wind else 0)
    c.ellipse(35, hy, 5, 4.5, "ashfur")
    c.poly([(36, hy - 1), (43, hy + 1), (42, hy + 3), (36, hy + 4)], "ashfur")
    c.poly([(31, hy - 3), (33, hy - 9), (35, hy - 3)], "ashfur")  # ear
    if wind:  # open jaw, fangs
        c.poly([(36, hy + 4), (42, hy + 6), (36, hy + 6)], "ashfur", 1)
        c.put(41, hy + 4, "bone", 3)
        c.put(38, hy + 4, "bone", 3)
    else:
        c.put(41, hy + 3, "bone", 3)
    c.ellipse(15, 20 + b, 5, 2.5, "murk")  # murk patch on the flank, dripping
    c.put(13, 23 + b, "murk")
    c.put(17, 23 + b, "murk")
    for x, h in ((11, 3), (15, 5), (20, 6), (24, 5), (28, 3)):
        h += 2 if wind else 0  # crystals bristle
        c.poly([(x - 2, 14 + b), (x, 13 + b - h), (x + 2, 14 + b)], "glow", 2)
    eye_dot(c, 37, hy - 1, 1)
    return c


def archer(wind=False):
    """小鬼の呪い手 (goblin bandit casting murk orbs). 32x56 (hero frame), feet on row 54."""
    c = Canvas(32, 56, RAMPS)
    capsule(c, 13, 42, 12, 53, 2, "gobskin", 1)
    capsule(c, 18, 42, 19, 53, 2, "gobskin")
    c.rect(10, 52, 14, 54, "leather")
    c.rect(17, 52, 22, 54, "leather")
    # Hunched body in a ragged plum cloak.
    c.poly([(9, 26), (21, 24), (24, 34), (23, 45), (19, 43), (16, 46), (12, 43), (8, 45), (7, 34)], "plum")
    # Head: big sideways ears, long nose, under a hood.
    hx_, hy = 17, 22
    c.poly([(9, hy - 3), (1, hy - 8), (6, hy + 1)], "gobskin")
    c.ellipse(hx_, hy, 6, 6, "gobskin")
    c.poly([(21, hy), (28, hy + 3), (22, hy + 4)], "gobskin")
    c.poly([(9, hy - 2), (11, hy - 8), (18, hy - 9), (17, hy - 5), (12, hy + 2)], "plum")
    c.rect(18, hy - 2, 21, hy - 2, "gobskin", 1)  # brow
    eye_dot(c, 19, hy - 1, 2)
    c.put(19, hy + 4, "bone", 3)  # tusk
    # Staff: bone shaft with a murk orb held by a skull.
    if wind:
        capsule(c, 18, 32, 26, 26, 2, "gobskin")  # arm forward
        c.line(22, 40, 29, 12, "wood")
        c.ellipse(29, 10, 3.5, 3.5, "glow", 2)  # the orb grows (shape, not colour)
        c.put(29, 10, "glow", 3)
    else:
        capsule(c, 16, 30, 23, 32, 2, "gobskin")
        c.line(24, 50, 24, 16, "wood")
        c.ellipse(24, 15, 2.5, 2.5, "bone")
        c.ellipse(24, 11, 2, 2, "glow", 3)
    return c


def slime(wind=False):
    """澱だまり (new, murk monster): a puddle of murk with a crystal core. 32x28, base on row 26."""
    c = Canvas(32, 28, RAMPS)
    if wind:  # squash before the hop
        c.ellipse(16, 21, 14, 6, "murk")
    else:
        c.ellipse(16, 18, 11, 9, "murk")
        c.poly([(5, 24), (27, 24), (29, 26), (3, 26)], "murk")
    for x, y in ((8, 26), (24, 26), (13, 26)):
        c.put(x, y, "murk", 1)
    cy = 20 if wind else 17
    c.poly([(16, cy - 4), (19, cy), (16, cy + 4), (13, cy)], "glow", 2)
    glow_dot(c, 11, cy - 3, wind)
    glow_dot(c, 20, cy - 3, wind)
    return c


def sentry(wind=False):
    """遺跡の番兵 (new, ancient machine): a stone-and-bronze guard, one murk-tainted eye.
    40x56, feet on row 54."""
    c = Canvas(40, 56, RAMPS)
    c.rect(12, 44, 17, 54, "oldstone", 1)
    c.rect(22, 44, 27, 54, "oldstone")
    c.rect(11, 52, 18, 54, "bronze")
    c.rect(21, 52, 28, 54, "bronze")
    c.poly([(8, 22), (31, 22), (29, 45), (10, 45)], "oldstone")
    c.rect(9, 33, 30, 35, "bronze")
    c.line(19, 25, 19, 31, "glow", 1)  # dim rune line, tainted
    c.ellipse(19, 17, 8, 7, "oldstone")
    c.rect(11, 18, 27, 19, "bronze")
    c.rect(14, 13, 26, 16, "murk", 0)  # visor slit
    c.rect(19, 13, 22, 16, "glow", 3)
    capsule(c, 8, 25, 6, 36, 3, "bronze", 1)  # far arm
    if wind:  # near arm raised over the head for a slam
        capsule(c, 31, 24, 35, 10, 3, "bronze")
        c.rect(31, 2, 38, 9, "oldstone")
    else:
        capsule(c, 31, 25, 33, 38, 3, "bronze")
        c.rect(30, 38, 37, 45, "oldstone")
    return c


# ------------------------------------------------------------------ bosses (front-facing)

def boss_root(wind=False):
    """朽ち根のヌシ: a boar of dead roots, seen from the front. 96x80.
    Silhouette: tall root spikes on the back, front legs splayed wide like roots, the head pushed
    forward and low, long tusks sweeping out sideways with clear gaps around them."""
    c = Canvas(96, 80, RAMPS)
    lift = -4 if wind else 0  # wind-up (charge): back rises, head drops
    drop = 4 if wind else 0
    for s_ in (-1, 1):  # splayed front legs ending in root toes
        capsule(c, 48 + s_ * 22, 44 + lift, 48 + s_ * 40, 70, 4.5, "rotwood")
        capsule(c, 48 + s_ * 40, 70, 48 + s_ * 46, 77, 3, "rotwood")
        capsule(c, 48 + s_ * 40, 70, 48 + s_ * 34, 77, 2.5, "rotwood", 1)
    c.ellipse(48, 34 + lift, 30, 17, "rotwood")
    for x, h in ((24, 12), (32, 18), (40, 22), (48, 24), (56, 22), (64, 18), (72, 12)):  # back spikes
        c.poly([(x - 3, 24 + lift), (x, 24 + lift - h), (x + 3, 24 + lift)], "rotwood")
    for s_ in (-1, 1):  # shoulder spikes pointing out
        c.poly([(48 + s_ * 26, 28 + lift), (48 + s_ * 40, 22 + lift), (48 + s_ * 28, 36 + lift)], "rotwood")
    c.ellipse(48, 30 + lift, 8, 7, "murk")  # the core between root ribs
    c.ellipse(48, 30 + lift, 4, 4, "glow", 3)
    for x in (41, 45, 51, 55):
        c.line(x, 23 + lift, x + (1 if x < 48 else -1), 37 + lift, "rotwood", 1)
    for fx, fy in ((28, 30), (68, 32)):  # pale fungus caps
        c.ellipse(fx, fy + lift, 3.5, 2, "fungus")
    hy = 54 + drop
    c.ellipse(48, hy, 12, 10, "rotwood")
    c.ellipse(48, hy + 8, 7, 5, "rotwood")  # snout
    c.ellipse(48, hy + 9, 4, 2, "rotwood", 1)
    for s_ in (-1, 1):  # ears
        c.poly([(48 + s_ * 8, hy - 8), (48 + s_ * 15, hy - 14), (48 + s_ * 12, hy - 4)], "rotwood")
    for s_ in (-1, 1):  # tusks: out to the side, then up, free of the body
        capsule(c, 48 + s_ * 6, hy + 8, 48 + s_ * 17, hy + 13, 2.5, "bone")
        capsule(c, 48 + s_ * 17, hy + 13, 48 + s_ * 24, hy + 4, 2.5, "bone")
        capsule(c, 48 + s_ * 24, hy + 4, 48 + s_ * 25, hy - 3, 2, "bone")
    for x in (44, 48, 52):  # root beard to the ground
        c.line(x, hy + 13, x + (x - 48) // 2, 77, "rotwood", 1)
    glow_dot(c, 42, hy - 3, wind, 2)
    glow_dot(c, 52, hy - 3, wind, 2)
    return c


def boss_frost(wind=False):
    """凍て角のヌシ: a shaggy frost-elk with crystal antlers. 96x88."""
    c = Canvas(96, 88, RAMPS)
    b = 4 if wind else 0
    for lx in (28, 40, 56, 68):
        capsule(c, lx, 62, lx, 86, 5, "frostfur", 1 if lx in (40, 56) else None)
    c.ellipse(48, 56 + b, 34, 20, "frostfur")
    c.poly([(20, 60 + b), (76, 60 + b), (70, 72 + b), (58, 70 + b), (48, 76 + b), (38, 70 + b), (26, 72 + b)], "frostfur")
    hy = 40 + b
    c.ellipse(48, hy + 16, 18, 12, "frostfur", 1)  # dark mane (collar) in front of the body
    c.poly([(38, hy - 6), (58, hy - 6), (56, hy + 14), (52, hy + 26), (44, hy + 26), (40, hy + 14)], "frostfur", 3)  # paler face
    c.ellipse(48, hy + 24, 5, 3, "frostfur", 1)  # muzzle
    # Antlers: branching ice crystals, wide (they are the silhouette).
    for s in (-1, 1):
        x0 = 48 + s * 8
        capsule(c, x0, hy - 8, 48 + s * 30, hy - 26, 2.5, "ice")
        capsule(c, 48 + s * 30, hy - 26, 48 + s * 44, hy - 30, 2, "ice")
        capsule(c, 48 + s * 22, hy - 20, 48 + s * 24, hy - 36, 2, "ice")
        capsule(c, 48 + s * 36, hy - 28, 48 + s * 40, hy - 40, 2, "ice")
        capsule(c, 48 + s * 14, hy - 13, 48 + s * 12, hy - 26, 1.5, "ice")
    c.poly([(44, hy - 8), (48, hy - 14), (52, hy - 8), (48, hy - 2)], "glow", 3)
    glow_dot(c, 42, hy + 4, wind, 2)
    glow_dot(c, 53, hy + 4, wind, 2)
    if wind:  # frost crystals rising around it (ring of shots about to fly)
        for x, y in ((10, 50), (86, 50), (16, 76), (80, 76), (48, 6)):
            c.poly([(x, y - 3), (x + 2, y), (x, y + 3), (x - 2, y)], "ice", 3)
    return c


def boss_sand(wind=False):
    """砂嵐のヌシ: a floating sand-wraith with a stone mask; its lower body is a whirl. 80x96."""
    c = Canvas(80, 96, RAMPS)
    for i, y in enumerate(range(60, 92, 5)):  # the whirl narrows to the ground
        w = 22 - i * 3
        c.ellipse(40 + (2 if i % 2 else -2), y, max(w, 3), 3, "murksand", 2 if i % 2 else 1)
    c.poly([(16, 28), (64, 28), (62, 60), (40, 66), (18, 60)], "murksand")
    c.poly([(22, 26), (40, 6), (58, 26), (52, 34), (28, 34)], "murksand")  # hood
    c.ellipse(40, 26, 9, 10, "mask")
    for x in (34, 43):
        c.rect(x, 22, x + 3, 25, "murk", 0)
        glow_dot(c, x + 1, 23, wind, 2)
    c.line(40, 29, 40, 33, "mask", 1)
    c.ellipse(40, 46, 5, 5, "glow", 3)
    arm = -10 if wind else 0
    capsule(c, 18, 32, 6, 50 + arm, 4, "murksand")
    capsule(c, 62, 32, 74, 50 + arm, 4, "murksand")
    c.poly([(2, 50 + arm), (10, 50 + arm), (6, 62 + arm)], "mask")  # sand blades
    c.poly([(70, 50 + arm), (78, 50 + arm), (74, 62 + arm)], "mask")
    for x, y in ((8, 20), (72, 18), (4, 72), (76, 74)):  # floating stones
        c.ellipse(x, y, 2.5, 2, "mask", 1)
    if wind:  # a fan of grit gathering in front
        for x in (28, 40, 52):
            c.ellipse(x, 78, 2, 2, "glow", 3)
    return c


def boss_storm(wind=False):
    """雷鳴のヌシ: a storm-eel rising from the lake, fin-crest crackling. 88x96."""
    c = Canvas(88, 96, RAMPS)
    c.ellipse(44, 88, 40, 7, "lake")
    c.ellipse(44, 88, 30, 4, "lake", 3)
    capsule(c, 30, 86, 24, 66, 9, "slate")  # S-shaped body
    capsule(c, 24, 66, 40, 48, 9, "slate")
    capsule(c, 40, 48, 54, 34, 9, "slate")
    capsule(c, 58, 88, 64, 78, 5, "slate", 1)  # a coil breaking the water (arc)
    capsule(c, 64, 78, 72, 78, 5, "slate", 1)
    capsule(c, 72, 78, 76, 88, 5, "slate", 1)
    for x0, y0, x1, y1 in ((24, 66, 40, 48), (40, 48, 54, 34)):
        c.strand(x0 + 4, y0 + 4, x1 + 4, y1 + 4, 3)  # pale belly line
    hx_, hy = 54 + (0 if not wind else -2), 26 + (4 if wind else 0)
    c.ellipse(hx_, hy, 13, 10, "slate")
    c.poly([(hx_ + 2, hy - 4), (hx_ + 20, hy + 1), (hx_ + 6, hy + 4)], "slate")  # long snout
    if wind:  # jaw drops open, sparks inside
        c.poly([(hx_ + 2, hy + 5), (hx_ + 18, hy + 12), (hx_ + 4, hy + 10)], "slate", 1)
        c.put(hx_ + 8, hy + 6, "spark", 3)
        c.put(hx_ + 12, hy + 8, "spark", 3)
    for i, (dx, h) in enumerate(((-10, 10), (-4, 16), (2, 14), (8, 9))):  # crest fins
        c.poly([(hx_ + dx - 3, hy - 6), (hx_ + dx, hy - 6 - h), (hx_ + dx + 3, hy - 6)], "spark", 2)
    for x, y in ((14, 58), (30, 40), (44, 72), (20, 82)):  # fins along the body
        c.poly([(x, y), (x - 6, y - 5), (x - 2, y + 3)], "spark", 1)
    glow_dot(c, hx_ - 4, hy - 1, wind, 2)
    glow_dot(c, hx_ + 5, hy - 1, wind, 2)
    c.ellipse(38, 56, 3.5, 3.5, "glow", 3)
    if wind:  # sparks orbiting before the ring of shots
        for x, y in ((6, 30), (80, 40), (8, 70), (82, 64), (40, 8)):
            c.line(x, y, x + 3, y + 3, "spark", 3)
            c.line(x + 3, y + 3, x, y + 6, "spark", 3)
    return c


def boss_source(phase2=False):
    """淀みの源 (final, not in code yet): a corrupted 星環 ring with a murk heart and tendrils.
    128x128 body (tendrils may become separate sprites)."""
    c = Canvas(128, 128, RAMPS)
    for x0, x1 in ((40, 20), (54, 48), (74, 80), (88, 108)):  # tendrils down into the ground
        capsule(c, x0, 80, (x0 + x1) // 2, 104, 4, "murk", 1)
        capsule(c, (x0 + x1) // 2, 104, x1, 124, 3, "murk", 1)
    c.ellipse(64, 56, 44, 44, "ashring")
    c.ellipse(64, 56, 34, 34, "murk")
    if phase2:  # the ring cracks: gaps of glow
        for a, b in (((30, 30), (40, 40)), ((96, 70), (88, 80)), ((70, 12), (66, 22))):
            capsule(c, a[0], a[1], b[0], b[1], 3, "glow", 3)
    for x, y in ((64, 14), (106, 56), (64, 98), (22, 56)):  # four sockets (the four cores)
        c.ellipse(x, y, 4, 4, "murk", 0 if not phase2 else 1)
        if phase2:
            c.ellipse(x, y, 2, 2, "glow", 3)
    c.ellipse(64, 56, 18, 12, "glow", 2)  # the eye
    c.ellipse(64, 56, 8, 10, "murk", 0)
    c.ellipse(62, 52, 2, 2, "glow", 3)
    for x, y in ((8, 20), (118, 26), (6, 92), (122, 96)):  # orbiting shards
        c.poly([(x, y - 5), (x + 3, y), (x, y + 5), (x - 3, y)], "ashring")
    return c


# ------------------------------------------------------------------ the sheet

FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


# Ground colours: the art style guide 2.5, tone 2 (the widest colour of each ground).
GRASS, DARK, BG, INK = rgb("#3c6a38"), (0x24, 0x22, 0x2a), (0xF4, 0xF1, 0xEA), (0x22, 0x20, 0x26)
GROUND = {
    "root": [("森の苔", rgb("#244834"))],
    "frost": [("雪", rgb("#b8c8e0")), ("灰紫の岩", rgb("#585668"))],
    "sand": [("赤い砂", rgb("#a8603c")), ("砂岩", rgb("#947a60"))],
    "storm": [("深い水", rgb("#22608e")), ("岸の草", rgb("#36684c"))],
    "source": [("未定・暗い地面", rgb("#302c36"))],
}


def font(size):
    return ImageFont.truetype(FONT, size)


def up(img, k):
    return img.resize((img.width * k, img.height * k), Image.NEAREST)


def hero_imgs():
    return [Image.open(os.path.join(HERO, n)).convert("RGBA") for n in ("hero.idle.down.0.png", "hero.attack1.right.2.png")]


def panel(items, ground, k, pad=6, gap=6):
    """items bottom-aligned on a ground strip, enlarged k times."""
    w = sum(im.width for im in items) + gap * (len(items) - 1) + pad * 2
    h = max(im.height for im in items) + pad * 2
    p = Image.new("RGBA", (w, h), ground + (255,))
    x = pad
    for im in items:
        p.alpha_composite(im, (x, h - pad - im.height))
        x += im.width + gap
    return up(p, k)


def silhouette(img):
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.paste((16, 14, 20, 255), mask=img.split()[3])
    return out


def stamp_small(img, text):
    d = ImageDraw.Draw(img)
    d.text((3, 2), text, font=font(10), fill=(255, 255, 255, 255), stroke_width=1, stroke_fill=(0, 0, 0, 255))
    return img


def stamp(img, text):
    d = ImageDraw.Draw(img)
    d.text((6, 4), text, font=font(14), fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0, 255))
    return img


def build_concepts():
    hero = hero_imgs()
    enemies = [
        ("澱の獣（既存 beast）44×32", beast), ("小鬼の呪い手（既存 archer）32×56", archer),
        ("澱だまり（新・承認が必要）32×28", slime), ("遺跡の番兵（新）40×56 ※表に無い", sentry),
    ]
    bosses = [
        ("朽ち根のヌシ 96×80", boss_root, "root"), ("凍て角のヌシ 96×88", boss_frost, "frost"),
        ("砂嵐のヌシ 80×96", boss_sand, "sand"), ("雷鳴のヌシ 88×96", boss_storm, "storm"),
        ("淀みの源（未実装）128×128", boss_source, "source"),
    ]
    blocks = []  # (title, image)
    # A. 1x beside the hero, on grass and on dark ground.
    row = [hero[0]] + [to_img(f()) for _, f in enemies] + [hero[1]]
    a1 = panel(row, GRASS, 1)
    a2 = panel(row, DARK, 1)
    a = Image.new("RGBA", (a1.width + a2.width + 16, a1.height), BG + (255,))
    a.alpha_composite(a1, (0, 0))
    a.alpha_composite(a2, (a1.width + 16, 0))
    blocks.append(("A. 実寸（絵 1 ドット＝HD 画面 1 ドット）：主人公・獣・呪い手・澱だまり・番兵・主人公。左は草地、右は暗い地面", a))
    # B. Enemies enlarged: idle and wind-up.
    tiles = []
    for name, f in enemies:
        t = panel([hero[0], to_img(f()), to_img(f(True))], GRASS, 3)
        tiles.append(stamp(t, name + "　待機／構え"))
    blocks.append(("B. 敵（3 倍）：主人公・待機・構え（構えは形だけで見せ、色は変えない。赤い点滅はプログラムが付ける）", tiles))
    # C. Bosses at 1x on their region ground.
    row = []
    for name, f, key in bosses:
        for gname, g in GROUND[key]:
            row.append(stamp_small(panel([hero[0], to_img(f())], g, 1), gname))
    cw = sum(r.width for r in row) + 12 * (len(row) - 1)
    cimg = Image.new("RGBA", (cw, max(r.height for r in row)), BG + (255,))
    x = 0
    for r in row:
        cimg.alpha_composite(r, (x, cimg.height - r.height))
        x += r.width + 12
    blocks.append(("C. ボス 実寸：闘技場の地面（ガイド 2.5 の色）の上で主人公と並べる。山・荒野・湖は 2 種類の地面", cimg))
    # D. Bosses enlarged x2: idle and wind-up (final boss: phase 1 / phase 2).
    tiles = []
    for name, f, key in bosses:
        t = panel([hero[0], to_img(f()), to_img(f(True))], GROUND[key][0][1], 2)
        tiles.append(stamp(t, name + ("　第 1 段階／第 2 段階" if key == "source" else "　待機／構え") + "（" + GROUND[key][0][0] + "）"))
    blocks.append(("D. ボス（2 倍）：主人公・待機・構え", tiles))
    # E. Pure silhouettes (black), 2x: every boss and enemy must read by shape alone.
    sil = [silhouette(hero[0])] + [silhouette(to_img(f())) for _, f, _ in bosses] + [silhouette(to_img(f())) for _, f in enemies]
    blocks.append(("E. 黒いシルエット（2 倍）：主人公・ヌシ 4 体・淀みの源・敵 4 体。形だけで何か分かるか", panel(sil, (0xe8, 0xe4, 0xdc), 2)))

    # Layout.
    W = 1500
    title_f, head_f = font(30), font(18)
    y = 0
    placed = []
    y += 92
    for title, content in blocks:
        placed.append(("head", title, y))
        y += 30
        imgs = content if isinstance(content, list) else [content]
        x, line_h = 16, 0
        for im in imgs:
            if x + im.width > W - 16 and x > 16:
                x, y = 16, y + line_h + 12
                line_h = 0
            placed.append(("img", im, (x, y)))
            x += im.width + 16
            line_h = max(line_h, im.height)
        y += line_h + 24
    sheet = Image.new("RGBA", (W, y + 40), BG + (255,))
    d = ImageDraw.Draw(sheet)
    d.rectangle([0, 0, W, 76], fill=(0x7a, 0x14, 0x30, 255))
    d.text((16, 10), "設計案（承認用の下絵。本番の絵ではありません）", font=title_f, fill=(255, 255, 255, 255))
    d.text((16, 48), "敵とボスのシルエット案 — 星環のレガリア v1.0 ／ 平塗りの形と色の確認用。細部・コマは承認後に描く", font=font(16), fill=(255, 230, 236, 255))
    for kind, a, b in placed:
        if kind == "head":
            d.text((16, b), a, font=head_f, fill=INK + (255,))
        else:
            sheet.alpha_composite(a, b)
    d.text((16, sheet.height - 30), "tools/enemy_concepts/concepts.py が出力。主人公は承認済みの src/art-release/hero/ の絵をそのまま使用。", font=font(14), fill=(0x60, 0x5c, 0x66, 255))
    sheet.convert("RGB").save(os.path.join(OUT, "concepts.png"))


def build_palette():
    hero_cols = [("主人公 緑のマント", ["#10180e", "#3e6234", "#6a9048", "#8eb062", "#b8d48a"]),
                 ("主人公 白い服", ["#4a4640", "#a8a296", "#e4e0d6", "#f6f4ee", "#ffffff"]),
                 ("主人公 金", BASE_RAMPS["gold"]), ("主人公 青い光（星環）", BASE_RAMPS["gem"])]
    groups = [
        ("澱（全部の敵に共通）", ["murk", "glow"]), ("獣・小鬼の目", ["eye"]), ("澱の獣", ["ashfur"]), ("小鬼の呪い手", ["gobskin", "plum"]),
        ("遺跡の番兵（新）", ["oldstone", "bronze"]), ("朽ち根のヌシ", ["rotwood", "fungus"]),
        ("凍て角のヌシ", ["frostfur", "ice"]), ("砂嵐のヌシ", ["murksand", "mask"]),
        ("雷鳴のヌシ", ["slate", "spark", "lake"]), ("淀みの源", ["ashring"]),
    ]
    rows = []
    for g, keys in groups:
        for k in keys:
            rows.append((g, NAMES[k] + f"（{k}）", RAMPS[k]))
    sw, rh, lw = 96, 44, 420
    W = lw + sw * 5 + 32
    H = 110 + rh * (len(rows) + len(hero_cols)) + 80
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 70], fill=(0x7a, 0x14, 0x30))
    d.text((16, 8), "設計案：敵とボスの色（5 段階：輪郭・影・基本・明・最明）", font=font(24), fill=(255, 255, 255))
    d.text((16, 42), "緑を使わない。主人公の白・金・青は主な色にしない。澱＝ガイドの澱の紫＋敵の魔法の赤紫（色合い 300°、溜めの赤から 60°）", font=font(14), fill=(255, 230, 236))
    y = 84
    d.text((16, y), "敵・ボス", font=font(18), fill=INK)
    y += 28

    def ramp_row(y, label, sub, cols):
        d.text((16, y + 4), label, font=font(15), fill=INK)
        d.text((16, y + 24), sub, font=font(12), fill=(0x60, 0x5c, 0x66))
        for i, cc in enumerate(cols):
            x = lw + i * sw
            d.rectangle([x, y, x + sw - 4, y + rh - 6], fill=cc)
            lum = sum(int(cc[j:j + 2], 16) for j in (1, 3, 5))
            d.text((x + 6, y + 12), cc, font=font(13), fill=(0, 0, 0) if lum > 380 else (255, 255, 255))

    for g, label, cols in rows:
        ramp_row(y, g, label, cols)
        y += rh
    y += 12
    d.text((16, y), "比べるための主人公の色（敵には使わない）", font=font(18), fill=INK)
    y += 28
    for label, cols in hero_cols:
        ramp_row(y, label, "", cols)
        y += rh
    img = img.crop((0, 0, W, y + 16))
    img.save(os.path.join(OUT, "palette.png"))


RESERVED = {"溜めの赤": "#ff3a3a", "ひるみの青": "#60a0ff", "マント": "#6a9048", "遺跡の光": "#22a49a"}
MEASURE = [  # (name, main colour = tone 2 of the body ramp, arena grounds)
    ("澱の光 glow", "glow", []), ("澱の体 murk（澱だまり）", "murk", ["#3c6a38", "#244834"]),
    ("獣 ashfur", "ashfur", ["#3c6a38"]), ("呪い手 plum", "plum", ["#3c6a38", "#585668"]),
    ("番兵 oldstone", "oldstone", ["#947a60", "#5a6468"]), ("朽ち根 rotwood", "rotwood", ["#244834"]),
    ("凍て角 frostfur", "frostfur", ["#b8c8e0", "#585668"]), ("砂嵐 murksand", "murksand", ["#a8603c", "#947a60"]),
    ("雷鳴 slate", "slate", ["#22608e", "#36684c"]), ("淀みの源 ashring", "ashring", []),
]


def hue_light(h):
    import colorsys
    r, g, b = rgb(h)
    hh, _, ss = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    return round(hh * 360), round((0.299 * r + 0.587 * g + 0.114 * b) / 2.55), round(ss * 100)


def hue_gap(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)


def measure():
    """Markdown table: hue (deg) / lightness (0-100, the guide's formula) of each main colour, and the
    gaps to the reserved colours and to its own arena grounds."""
    print("| 色 | 値 | 色合い° | 明るさ | 鮮やかさ% | " + " | ".join(f"{k} {v}" for k, v in RESERVED.items()) + " | 地面との差（色合い°／明るさ） |")
    print("|" + "---|" * (6 + len(RESERVED)))
    for name, key, grounds in MEASURE:
        c = RAMPS[key][2]
        h, l, sat = hue_light(c)
        gaps = []
        for v in RESERVED.values():
            rh, rl, _ = hue_light(v)
            gaps.append(f"{hue_gap(h, rh)}°／{abs(l - rl)}")
        gs = []
        for g in grounds:
            gh, gl, _ = hue_light(g)
            gs.append(f"{g}：{hue_gap(h, gh)}°／{abs(l - gl)}")
        print(f"| {name} | {c} | {h} | {l} | {sat} | " + " | ".join(gaps) + " | " + ("、".join(gs) or "—") + " |")


if __name__ == "__main__":
    if "--table" in sys.argv:
        measure()
        sys.exit()
    os.makedirs(OUT, exist_ok=True)
    build_concepts()
    build_palette()
    print("wrote docs/enemy/concepts.png, docs/enemy/palette.png")
