"""P12 round 3 prototypes (仮素材 — waiting for the user's approval, not final art): 4 enemies.

  enemy.slime.<0|1>   32x24  スライム   a jelly with a seed core and two glossy eyes; 0 wobble, 1 hop
  enemy.flyer.<0|1>   36x28  飛行型     灯尾蛾 (lantern-tail moth): feathery antennae, four veined
                                         wings, a curled tail with a glowing tip; 0 wings up, 1 down
  enemy.plant.<0|1>   32x40  植物型     牙つぼみ (fang bud): roots, thorny vines, a bud that opens
                                         into a toothed maw; 0 closed and swaying, 1 open
  enemy.golem.<0|1>   64x72  大型       苔岩の巨人 (moss-rock giant): horns, armour slabs, long arms,
                                         a glowing ember core; 0 breathing, 1 a heavy step

Facing right (the game mirrors enemies facing left), feet / ground contact at the bottom centre.
Same method as the hero v2 and rounds 1-2 (tools/art_proto/pixel.py). Art only: no AI, attacks,
hit boxes, damage or defeat — these kinds do not exist in the game.

Writes src/art-proto/enemy/enemy.{slime,flyer,plant,golem}.{0,1}.png (rounds 1-2 untouched).
Run: python3 tools/art_proto/gen_round3.py   (previews: tools/art_proto/previews_round3.py)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, hx, png  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
OUT = os.path.join(ROOT, "src", "art-proto", "enemy")

# ------------------------------------------------------------------ slime (32x24)

SLIME = {
    "jelly": ["#0a2a30", "#1c6070", "#2c98a6", "#5cc8d0", "#c8f8f4"],
    "core": ["#3a1a04", "#8a4a10", "#d08a20", "#f8c050", "#fff0b0"],
}


def slime(f):
    c = Canvas(32, 24, SLIME)
    if f == 0:  # wobbling at rest: a wide, soft dome sagging onto the ground
        c.ellipse(16, 16.0, 13.0, 9.0, "jelly")
        c.ellipse(16, 21.0, 14.2, 3.0, "jelly")
        for y in range(24):  # flat where it rests on the ground
            for x in range(32):
                if y > 23:
                    c.mat[y][x] = None
        base, top = 23, 7
    else:  # hopping: narrower and taller, lifted off the ground, a drip falling
        c.ellipse(16, 12.0, 10.6, 10.0, "jelly")
        c.ellipse(16, 18.5, 11.4, 2.6, "jelly")
        c.ellipse(9, 22.5, 1.2, 1.2, "jelly")  # a drop left behind
        base, top = 21, 2
    # inner light: a soft band and a glossy highlight
    c.strand(8, base - 4, 24, base - 4, 1)
    for x0, y0, x1, y1 in ((9, top + 3, 12, top + 2), (8, top + 4, 9, top + 5)):
        c.strand(x0, y0, x1, y1, 4)
    # the seed core inside, with bubbles
    cy = base - 5
    c.ellipse(21, cy - 1, 2.2, 2.0, "core")  # the seed core, off-centre and deep inside
    c.put(21, cy - 1, "core", 0)  # its dark nucleus
    c.shade(20, cy - 2, 4)
    for x, y in ((11, cy + 1), (25, cy - 4), (14, cy + 2), (17, cy - 1)):
        c.shade(x, y, 3)  # bubbles
    # two glossy eyes (wide apart, a little sleepy when resting, round when hopping)
    ey = top + 5
    for ex in (11, 18):
        c.paint(ex, ey, "#10202a")
        c.paint(ex + 1, ey, "#10202a")
        c.paint(ex, ey + 1, "#10202a")
        c.paint(ex + 1, ey + 1, "#10202a")
        c.paint(ex, ey, "#ffffff")
        if f == 1:
            c.paint(ex, ey + 2, "#10202a")
            c.paint(ex + 1, ey + 2, "#10202a")
    c.paint(15, ey + 3, "#10202a")  # a small mouth
    c.paint(16, ey + 3, "#10202a")
    img = c.colours()
    # the jelly is see-through: the body lets a little of the ground show, the outline and
    # highlights stay solid
    jelly = [hx(v) for v in SLIME["jelly"][1:4]]
    for y in range(24):
        for x in range(32):
            px = img[y][x]
            if px and px[:3] in jelly:
                img[y][x] = px[:3] + (205,)
    return img


# ------------------------------------------------------------------ flyer (36x28)

FLYER = {
    "wing": ["#1a0e24", "#3e2458", "#6a4090", "#9a70c0", "#d0b0f0"],
    "body": ["#0e0a1a", "#2a2040", "#463864", "#62528a", "#8a7ab0"],
    "lantern": ["#3a2004", "#a06008", "#f0b020", "#ffe070", "#fffbe0"],
    "fur": ["#2a2018", "#6a5a44", "#a08c6a", "#c8b48e", "#ece0c0"],
}


def flyer(f):
    up = f == 0
    c = Canvas(36, 28, FLYER)
    # the shadow on the ground (it floats above it)
    c.ellipse(19, 26.5, 7.0, 1.4, "body", 0)
    lift = 0 if up else 2
    # far wings (behind the body), darker
    if up:
        c.poly([(18, 10), (22, 9), (30, 0), (33, 2), (26, 11)], "wing", 1)
        c.poly([(17, 12), (21, 12), (27, 16), (24, 18)], "wing", 1)
    else:
        c.poly([(18, 12), (22, 12), (32, 20), (29, 22), (24, 18)], "wing", 1)
        c.poly([(17, 13), (21, 13), (25, 21), (21, 22)], "wing", 1)
    # the curled tail with its glowing lantern tip (to the left, behind)
    c.poly([(12, 13 + lift), (15, 13 + lift), (10, 18 + lift), (6, 19 + lift), (4, 17 + lift)], "body")
    c.poly([(4, 17 + lift), (6, 19 + lift), (3, 22 + lift), (1, 20 + lift)], "body")
    c.ellipse(2.5, 22.5 + lift, 2.2, 2.2, "lantern")
    c.shade(2, 22 + lift, 4)
    # body: furry thorax and a segmented abdomen
    c.ellipse(21, 12 + lift, 5.0, 4.0, "fur")
    c.ellipse(14, 14 + lift, 5.2, 3.2, "body")
    for x in (11, 14, 17):
        c.strand(x, 12 + lift, x, 16 + lift, 1)
    # head with big compound eyes, small mandibles
    c.ellipse(27, 11 + lift, 3.6, 3.4, "body")
    c.paint(28, 10 + lift, "#ff5a3a")
    c.paint(29, 10 + lift, "#ffb070")
    c.paint(28, 11 + lift, "#c02a1a")
    c.paint(29, 11 + lift, "#ff5a3a")
    c.put(31, 13 + lift, "fur", 1)
    c.put(30, 14 + lift, "fur", 1)
    # feathery antennae
    for x0, y0, x1, y1 in ((27, 8, 31, 2), (25, 8, 26, 1)):
        c.line(x0, y0 + lift, x1, y1 + lift, "fur", 3)
        for t in range(1, 4):
            xx = x0 + (x1 - x0) * t // 4
            yy = y0 + (y1 - y0) * t // 4 + lift
            c.put(xx + 1, yy, "fur", 2)
            c.put(xx - 1, yy, "fur", 2)
    # little claws under the thorax
    c.line(20, 16 + lift, 19, 19 + lift, "body", 1)
    c.line(23, 16 + lift, 23, 19 + lift, "body", 1)
    # near wings (in front), with veins and eye spots
    if up:
        c.poly([(16, 10), (21, 9), (14, 0), (6, 0), (4, 3), (11, 9)], "wing")
        c.poly([(15, 13), (19, 13), (13, 19), (8, 18)], "wing")
        veins = ((17, 9, 10, 2), (18, 9, 15, 1), (16, 13, 11, 17))
        spot = (10, 4)
    else:
        c.poly([(16, 12), (21, 12), (14, 22), (5, 24), (3, 21), (10, 15)], "wing")
        c.poly([(15, 14), (19, 14), (16, 21), (11, 22)], "wing")
        veins = ((17, 13, 8, 21), (18, 13, 13, 22), (16, 15, 13, 20))
        spot = (9, 20)
    for x0, y0, x1, y1 in veins:
        c.strand(x0, y0, x1, y1, 1)
    c.put(spot[0], spot[1], "lantern", 3)  # glowing eye spot on the wing
    c.put(spot[0] + 1, spot[1], "lantern", 2)
    img = c.colours()
    # the wings are thin membranes: a little see-through
    wing = [hx(v) for v in FLYER["wing"][1:5]]
    for y in range(28):
        for x in range(36):
            px = img[y][x]
            if px and px[:3] in wing:
                img[y][x] = px[:3] + (225,)
    return img


# ------------------------------------------------------------------ plant (32x40)

PLANT = {
    "stem": ["#06180e", "#123a24", "#1e5a3a", "#2e7a52", "#4c9c70"],
    "petal": ["#2a0610", "#6a1426", "#a02838", "#d0484e", "#f08080"],
    "root": ["#1a0e06", "#3e2414", "#5e3a22", "#7e5232", "#9e6c46"],
    "maw": ["#08020a", "#20081a", "#3a1028", "#5a1a3a", "#7a2a4e"],
}


def plant(f):
    opened = f == 1
    c = Canvas(32, 40, PLANT)
    sway = 0 if opened else 1
    # roots gripping the ground
    for x0, x1 in ((15, 6), (16, 26), (14, 10), (17, 22)):
        c.line(x0, 35, x1, 39, "root")
    c.ellipse(15.5, 37, 6.0, 2.5, "root")
    # thick stem (bends with the sway), two broad leaves
    for y in range(18, 37):
        x = 14 + (sway if y < 28 else 0)
        c.rect(x, y, x + 3, y, "stem")
    c.strand(15 + sway, 20, 15, 34, 3)
    c.poly([(14, 30), (4, 25), (2, 28), (8, 32), (14, 33)], "stem")
    c.poly([(18, 28), (27, 22), (30, 25), (24, 30), (18, 31)], "stem")
    c.strand(13, 31, 5, 27, 1)
    c.strand(19, 29, 28, 24, 1)
    # thorny vines curling out to the sides
    for pts in (((12, 24), (6, 20), (3, 14), (5, 10)), ((19, 22), (25, 18), (28, 12), (26, 8))):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            c.line(x0, y0 + (0 if opened else 1), x1, y1 + (0 if opened else 1), "stem", 2)
        for x, y in pts[1:]:
            c.put(x + 1, y + (0 if opened else 1) - 1, "petal", 3)  # thorns
    if not opened:
        # the closed bud: petals wrapped tight, swaying, a hint of teeth at the seam
        c.ellipse(16 + sway, 11, 7.0, 8.2, "petal")
        c.poly([(10 + sway, 14), (16 + sway, 2), (22 + sway, 14)], "petal")
        for x0 in (13, 16, 19):
            c.strand(x0 + sway, 5, x0 + sway, 17, 1)
        c.strand(12 + sway, 6, 12 + sway, 12, 4)
        for x in (14, 17):
            c.put(x + sway, 17, "bone", 3)
        for x, y in ((11, 9), (20, 13), (15, 6)):
            c.put(x + sway, y, "gold", 3)  # yellow spots
    else:
        # the bud opens: four petals spread around a toothed maw with a tongue
        for pts in (((9, 12), (1, 4), (6, 2), (13, 8)), ((23, 12), (31, 4), (26, 2), (19, 8)), ((10, 15), (2, 18), (5, 21), (13, 17)), ((22, 15), (30, 18), (27, 21), (19, 17))):
            c.poly(list(pts), "petal")
        c.ellipse(16, 12, 7.6, 6.4, "petal")
        c.ellipse(16, 12, 5.4, 4.4, "maw")
        for x in range(12, 21, 2):
            c.put(x, 8, "bone", 3)  # upper teeth
            c.put(x + 1, 16, "bone", 3)  # lower teeth
        c.rect(15, 12, 17, 15, "petal", 4)  # tongue
        c.put(16, 16, "petal", 3)
        for x, y in ((4, 5), (28, 5), (5, 19)):
            c.put(x, y, "gold", 3)
    return c.colours()


# ------------------------------------------------------------------ golem (64x72)

GOLEM = {
    "stone": ["#14141a", "#3a3a44", "#5e5e6a", "#868692", "#b0b0ba"],
    "slab": ["#0e0e14", "#26262e", "#3c3c48", "#54545e", "#6e6e7a"],
    "moss": ["#0c1c0a", "#244018", "#3e6426", "#5e8638", "#86ac52"],
    "ember": ["#3a0a04", "#8a2a08", "#d0561a", "#ff9a3a", "#ffe8b0"],
    "horn": ["#1e1810", "#4a3e2c", "#76664a", "#9e8c6a", "#c8b894"],
}


def golem(f):
    step = f == 1
    c = Canvas(64, 72, GOLEM)
    d = 2 if step else 0  # the whole body sinks into the step: weight
    # legs: short pillars; on the step the near leg comes forward and lands heavily
    for x0, near in ((20, False), (34, True)):
        fwd = 5 if (step and near) else 0
        back = -4 if (step and not near) else 0
        x = x0 + fwd + back
        c.rect(x, 54 + d, x + 9, 66, "stone", None if near else 1)
        c.rect(x - 2, 66, x + 11, 71, "stone", None if near else 1)
        c.line(x - 2, 71, x + 11, 71, "stone", 0)
        c.strand(x + 2, 57 + d, x + 2, 64, 3 if near else 1)
    if step:  # dust kicked up where the foot lands
        for x, y in ((36, 69), (49, 68), (51, 70), (34, 70)):
            c.put(x, y, "horn", 3)
    # torso: a hunched boulder with armour slabs and moss on the back
    c.ellipse(32, 38 + d, 19.0, 17.0, "stone")
    c.ellipse(27, 27 + d, 15.0, 10.0, "stone")  # the hunched back / shoulders rise high
    c.poly([(19, 36 + d), (45, 34 + d), (46, 48 + d), (20, 50 + d)], "slab")  # chest plate
    c.strand(20, 42 + d, 45, 41 + d, 0)
    c.strand(32, 35 + d, 33, 49 + d, 0)
    for x0, y0 in ((14, 22), (22, 18), (31, 18), (38, 22)):  # moss on the shoulders and back
        c.ellipse(x0, y0 + d, 5.5, 3.2, "moss")
    for x, y in ((12, 24), (19, 20), (28, 20), (36, 21), (40, 25)):
        c.put(x, y + d + 2, "moss", 1)  # hanging moss strands
        c.put(x, y + d + 3, "moss", 1)
    # the ember core in the chest: glowing through a crack (brighter when breathing in)
    glow = 4 if not step else 3
    c.ellipse(33, 42 + d, 3.6, 3.0, "ember")
    c.shade(32, 41 + d, glow)
    c.shade(33, 41 + d, glow)
    for x0, y0, x1, y1 in ((33, 45, 35, 49), (30, 39, 27, 36)):
        c.line(x0, y0 + d, x1, y1 + d, "ember", 2)
    # the far arm (behind), the near arm long enough to touch the ground (gorilla stance)
    # the far arm swings back and its fist lifts off the ground as the weight shifts
    far_reach, far_lift = (-4, 5) if step else (0, 0)
    c.poly([(14, 28 + d), (21, 28 + d), (16 + far_reach, 58 - far_lift), (8 + far_reach, 58 - far_lift)], "stone", 1)
    c.rect(5 + far_reach, 57 - far_lift, 16 + far_reach, 66 - far_lift, "stone", 1)  # far fist
    near = 6 if step else 0
    c.poly([(42, 26 + d), (52, 28 + d), (56 + near, 54), (46 + near, 56)], "stone")
    c.poly([(44, 30 + d), (53, 31 + d), (54 + near, 41 + d), (45, 42 + d)], "slab")  # shoulder plate
    c.ellipse(52 + near, 61, 7.5, 6.5, "stone")  # near fist
    c.strand(47 + near, 59, 57 + near, 59, 1)  # knuckles
    c.strand(47 + near, 62, 57 + near, 62, 1)
    c.ellipse(49, 30 + d, 4.0, 2.4, "moss")
    # head: small, low, set forward under the shoulders; curved horns; glowing eyes
    hx0, hy0 = 44 + (3 if step else 0), 24 + d  # the head lunges forward on the step
    c.ellipse(hx0, hy0, 7.0, 6.0, "stone")
    c.poly([(hx0 - 3, hy0 + 3), (hx0 + 7, hy0 + 2), (hx0 + 6, hy0 + 7), (hx0 - 2, hy0 + 7)], "slab")  # heavy jaw
    for x in range(hx0 - 1, hx0 + 6, 2):
        c.put(x, hy0 + 4, "horn", 3)  # stone teeth
    # horns: one curving up and forward, one back
    # thick ram-like horns curving back and up (the near one bright, the far one in shadow)
    c.poly([(hx0 - 6, hy0 - 3), (hx0 - 1, hy0 - 6), (hx0 - 4, hy0 - 12), (hx0 - 10, hy0 - 14), (hx0 - 13, hy0 - 11), (hx0 - 9, hy0 - 10), (hx0 - 7, hy0 - 7)], "horn", 1)
    c.poly([(hx0, hy0 - 4), (hx0 + 4, hy0 - 6), (hx0 + 3, hy0 - 12), (hx0 - 2, hy0 - 16), (hx0 - 6, hy0 - 15), (hx0 - 2, hy0 - 12), (hx0 - 1, hy0 - 8)], "horn")
    for y in range(-14, -6, 2):
        c.strand(hx0 - 1 - (y + 14) // 4, hy0 + y, hx0 + 2 - (y + 14) // 4, hy0 + y, 1)  # ridges
    c.strand(hx0 - 4, hy0 - 15, hx0 - 2, hy0 - 14, 4)
    # brow ridge and eyes
    c.line(hx0 - 2, hy0 - 2, hx0 + 6, hy0 - 2, "slab", 1)
    for ex in (hx0 + 1, hx0 + 5):
        c.paint(ex, hy0, "#ff7a2a")
        c.paint(ex + 1, hy0, "#ffd080")
    return c.colours()


ENEMIES = (
    ("slime", "スライム", (32, 24), slime),
    ("flyer", "飛行型（灯尾蛾）", (36, 28), flyer),
    ("plant", "植物型（牙つぼみ）", (32, 40), plant),
    ("golem", "大型（苔岩の巨人）", (64, 72), golem),
)


def main():
    os.makedirs(OUT, exist_ok=True)
    n = 0
    for key, _, _, draw in ENEMIES:
        for f in (0, 1):
            with open(os.path.join(OUT, f"enemy.{key}.{f}.png"), "wb") as fh:
                fh.write(png(draw(f)))
            n += 1
    print(f"round 3: {n} frames for {len(ENEMIES)} enemies -> src/art-proto/enemy/")


if __name__ == "__main__":
    main()
