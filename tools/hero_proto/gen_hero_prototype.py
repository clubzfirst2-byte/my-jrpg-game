"""P12 hero PROTOTYPE sprites, v2 (仮素材 — a quality check stage, NOT final art).

Draws the hero (approved design: docs/hero/HERO_DESIGN_SPEC.md; poses after the prototype sheet in
docs/hero/reference/sprite_prototype/) as 32x56 transparent PNGs, feet at the bottom centre:
  walk 3 frames x 4 directions (frame 0 is also the idle pose, as the game plays 1,0,2,0)
  swim 2 frames x 4 directions
Left is the mirror of right, as in the game's placeholder.

How it is drawn (so later animations reuse it):
  * every part is drawn as a MATERIAL (hair, skin, cloak, ...), each with a ramp of 4-5 tones;
  * a shading pass lights every material from the top left (rim light / core / shadow);
  * a selective outline gives each edge a dark tone of its own material instead of pure black;
  * a POSE (bob, legs, arms, hair and cloak sway, how deep in water) drives every frame, so a new
    animation (run, jump, attack, ...) is a new list of poses, not new drawing code.

Writes src/art-proto/hero/<name>.png (loaded only with ?hero=proto) and docs/hero/prototype_preview.png.
Run: python3 tools/hero_proto/gen_hero_prototype.py
"""

import os
import struct
import zlib
from dataclasses import dataclass, replace

W, H = 32, 56
ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
OUT = os.path.join(ROOT, "src", "art-proto", "hero")
PREVIEW = os.path.join(ROOT, "docs", "hero", "prototype_preview.png")


def hx(s):
    return (int(s[1:3], 16), int(s[3:5], 16), int(s[5:7], 16))


# Material ramps, darkest first: [outline, shadow, core, light, highlight]
RAMP = {
    "hair": ["#2a160c", "#4e2e1a", "#7a4a2a", "#a8703f", "#d09a62"],
    "skin": ["#6e3e2c", "#c8906a", "#f2c49b", "#ffdcbc", "#fff0e0"],
    # yellower and brighter than the grass, with a near-black outline, so the hero reads on grass
    "cloak": ["#10180e", "#3e6234", "#6a9048", "#8eb062", "#b8d48a"],
    "lining": ["#10180e", "#22382a", "#2e4a36", "#3c5c44", "#4a6c52"],
    "shirt": ["#5a5650", "#a8a296", "#e4e0d6", "#f6f4ee", "#ffffff"],
    "leather": ["#24160c", "#4a3020", "#704c30", "#946c46", "#b88c5e"],
    "boot": ["#1e120a", "#3e2616", "#62402a", "#865c3c", "#a87a52"],
    "trousers": ["#14141c", "#22222e", "#323244", "#44445a", "#585872"],
    "gold": ["#5a4018", "#a07a30", "#e8c060", "#f8dc88", "#fff4c8"],
    "gem": ["#0e2a60", "#1a5cb8", "#2a8de2", "#78c8ff", "#e0f6ff"],
}
EYE = {"lash": hx("#24223a"), "iris": hx("#2a78d0"), "iris_d": hx("#1a3c86"), "shine": hx("#f0fbff")}
MOUTH = hx("#a8584e")
BLUSH = hx("#f0a888")
WATER = {"foam": hx("#f4fbff"), "ring": hx("#bfe4ff"), "ring_d": hx("#6aaee6"), "under": (40, 110, 170)}


@dataclass(frozen=True)
class Pose:
    bob: int = 0  # body down (+) / up (-), in pixels
    step: int = 0  # 0 together; +1 his right foot (screen left on front view) forward; -1 the other
    arm: int = 0  # arm swing: +1 right arm forward, -1 left arm forward
    sway: int = 0  # hair tips and cloak hem lag behind the motion: -1 / 0 / +1
    water: int = 0  # water line row (0 = not swimming)
    stroke: int = 0  # swim stroke phase 0 / 1


class Canvas:
    """Material ids (with a tone override) per pixel; shading and outline turn them into colours."""

    def __init__(self):
        self.mat = [[None] * W for _ in range(H)]
        self.tone = [[None] * W for _ in range(H)]  # fixed tone index (0..4) or None = auto
        self.rgb = [[None] * W for _ in range(H)]  # explicit colour (eyes, mouth, ...)

    def put(self, x, y, m, tone=None):
        if 0 <= x < W and 0 <= y < H:
            self.mat[y][x] = m
            self.tone[y][x] = tone
            self.rgb[y][x] = None

    def paint(self, x, y, rgb):
        """An explicit colour on top of what is there (keeps the pixel solid)."""
        if 0 <= x < W and 0 <= y < H and self.mat[y][x] is not None:
            self.rgb[y][x] = rgb

    def shade(self, x, y, tone):
        if 0 <= x < W and 0 <= y < H and self.mat[y][x] is not None:
            self.tone[y][x] = tone

    def m(self, x, y):
        return self.mat[y][x] if 0 <= x < W and 0 <= y < H else None

    def rect(self, x0, y0, x1, y1, m, tone=None):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, m, tone)

    def ellipse(self, cx, cy, rx, ry, m, tone=None):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1:
                    self.put(x, y, m, tone)

    def poly(self, pts, m, tone=None):
        ys = [p[1] for p in pts]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            yc = y + 0.5
            xs = []
            n = len(pts)
            for i in range(n):
                (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
                if (y0 <= yc < y1) or (y1 <= yc < y0):
                    xs.append(x0 + (yc - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for a, b in zip(xs[::2], xs[1::2]):
                for x in range(int(round(a)), int(round(b))):
                    self.put(x, y, m, tone)

    def line(self, x0, y0, x1, y1, m, tone=None):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            self.put(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), m, tone)

    def strand(self, x0, y0, x1, y1, tone):
        """A line of hair tone over existing hair (does not add pixels outside it)."""
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            self.shade(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), tone)

    # ---- the passes that make it look finished

    def colours(self):
        """Light from the top left: rim light on top-left edges, shadow on bottom-right edges."""
        out = [[None] * W for _ in range(H)]
        for y in range(H):
            for x in range(W):
                m = self.mat[y][x]
                if m is None:
                    continue
                if self.rgb[y][x] is not None:
                    out[y][x] = self.rgb[y][x]
                    continue
                t = self.tone[y][x]
                if t is None:
                    up, left = self.m(x, y - 1) != m, self.m(x - 1, y) != m
                    down, right = self.m(x, y + 1) != m, self.m(x + 1, y) != m
                    t = 3 if (up or left) and not (down or right) else 1 if (down or right) and not (up or left) else 2
                    if up and left:
                        t = 4 if m in ("hair", "gem", "gold") else 3
                out[y][x] = hx(RAMP[m][t])
        # selective outline: each outside edge gets the darkest tone of the material it borders
        add = []
        for y in range(H):
            for x in range(W):
                if self.mat[y][x] is not None:
                    continue
                nb = [self.m(x + dx, y + dy) for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))]
                nb = [n for n in nb if n is not None]
                if nb:
                    # hair, boots and trousers are outlined darkest (the silhouette must read on grass)
                    pick = min(nb, key=lambda n: sum(hx(RAMP[n][0])))
                    add.append((x, y, hx(RAMP[pick][0])))
        for x, y, c in add:
            out[y][x] = c
        return out


# ------------------------------------------------------------------ parts

def hair_mass(c, cx, top, front=True, side=False, sway=0):
    """The big, messy hair: rounded clumps (not thin spikes), a cowlick, tips that move with `sway`."""
    c.ellipse(cx, top + 11, 10.6, 10.0, "hair")
    clumps = [(-7, 4.5), (-2, 2.5), (3.5, 2.5), (8, 5), (-10, 10), (10, 10), (-9.5, 15), (9.5, 15)]
    if side:
        clumps = [(-6, 4.5), (-1, 2.5), (4, 3), (8, 6), (-10, 10), (-10, 15), (-8, 19)]
    for dx, dy in clumps:
        c.ellipse(cx + dx, top + dy, 4.2, 3.6, "hair")
    # a few pointed tips (wide at the base) at the sides, lagging behind the motion
    tips = [(-13, 8, -15, 6), (13, 8, 15, 6), (-12, 17, -13, 20 + sway), (12, 17, 13, 20 + sway)]
    if side:
        tips = [(-13, 8, -15, 6), (-13, 14, -15, 15 + sway), (-11, 20, -12, 23 + sway), (11, 6, 13, 4)]
    for bx, by, tx, ty in tips:
        c.poly([(cx + bx - 2, top + by - 1), (cx + bx + 2, top + by + 1), (cx + tx, top + ty)], "hair")
    # the cowlick
    c.line(int(cx) + 1, top, int(cx) + 2, top - 3, "hair")
    c.put(int(cx) + 3, top - 4, "hair")
    c.put(int(cx) + 4, top - 4, "hair")
    # clump edges: a shadow along the lower edge of each top clump, light along the upper edge
    for dx, dy in clumps[:4]:
        for a in range(-3, 4):
            x = int(cx + dx + a)
            y = top + int(dy + 3.4 * (1 - (a / 4.2) ** 2) ** 0.5)
            if 0 <= y < H and c.m(x, y + 1) == "hair":
                c.shade(x, y, 1)
        for a in range(-2, 2):
            c.shade(int(cx + dx + a), top + int(dy - 2.2), 4 if a < 0 else 3)
    # a few long strands for direction
    for x0, y0, x1, y1 in ((-9, 7, -10, 12), (9, 7, 10, 12), (-4, 6, -5, 9), (4, 6, 5, 9)):
        c.strand(int(cx + x0), top + y0, int(cx + x1), top + y1, 1)


def face_front(c, cx, top, sway=0):
    # face shape: wide cheeks, small chin
    c.poly([(cx - 6.5, top + 10), (cx + 6.5, top + 10), (cx + 6.5, top + 17), (cx + 3.5, top + 21), (cx - 3.5, top + 21), (cx - 6.5, top + 17)], "skin")
    c.rect(int(cx) - 2, top + 21, int(cx) + 1, top + 21, "skin")
    # the fringe: pointed strands over the forehead, longer on his right (screen left)
    # the fringe: three wide locks, the one over his right eye (screen left) longest
    for bx0, bx1, tx, ty in ((-8, -2, -6, 15), (-3, 3, 0, 13), (2, 8, 5, 14)):
        c.poly([(cx + bx0, top + 8), (cx + bx1, top + 8), (cx + bx1 - 1, top + 10), (cx + tx + 0.5, top + ty)], "hair")
    c.poly([(cx - 8, top + 7), (cx + 8, top + 7), (cx + 8, top + 10), (cx - 8, top + 10)], "hair")
    for x0, y0, x1, y1 in ((-3, 9, -4, 13), (2, 9, 2, 12), (-7, 10, -7, 13)):
        c.strand(int(cx + x0), top + y0, int(cx + x1), top + y1, 1)
    for x0, y0, x1, y1 in ((-6, 8, -4, 8), (0, 8, 1, 8), (4, 8, 5, 8)):
        c.strand(int(cx + x0), top + y0, int(cx + x1), top + y1, 3)
    # side locks down the cheeks
    c.poly([(cx - 9, top + 10), (cx - 7, top + 10), (cx - 6, top + 20 + sway), (cx - 8, top + 21 + sway)], "hair")
    c.poly([(cx + 7, top + 10), (cx + 9, top + 10), (cx + 8, top + 20 + sway), (cx + 6, top + 19 + sway)], "hair")
    # eyes: narrow, blue, with a shine (left/right of centre)
    for ex in (int(cx) - 5, int(cx) + 2):
        for dx in range(4):
            c.paint(ex + dx, top + 14, EYE["lash"])
        c.paint(ex, top + 15, EYE["iris_d"])
        c.paint(ex + 1, top + 15, EYE["iris"])
        c.paint(ex + 2, top + 15, EYE["iris"])
        c.paint(ex + 3, top + 15, EYE["shine"])
        c.paint(ex + 1, top + 16, EYE["iris_d"])
        c.paint(ex + 2, top + 16, EYE["iris"])
        c.shade(ex, top + 16, 1)
        c.shade(ex + 3, top + 16, 2)
    # brows (hair coloured, a little angled: resolute)
    c.paint(int(cx) - 5, top + 12, hx(RAMP["hair"][1]))
    c.paint(int(cx) - 4, top + 12, hx(RAMP["hair"][1]))
    c.paint(int(cx) + 4, top + 12, hx(RAMP["hair"][1]))
    c.paint(int(cx) + 5, top + 12, hx(RAMP["hair"][1]))
    # nose, mouth, blush
    c.shade(int(cx), top + 18, 1)
    c.paint(int(cx) - 1, top + 20, MOUTH)
    c.paint(int(cx), top + 20, MOUTH)
    c.paint(int(cx) - 5, top + 18, BLUSH)
    c.paint(int(cx) + 4, top + 18, BLUSH)
    # jaw shadow
    for x in range(int(cx) - 3, int(cx) + 3):
        c.shade(x, top + 21, 1)


def face_side(c, cx, top, sway=0):
    """Facing right (3/4 view): the face on the right, one eye, the ear and the back hair."""
    c.poly([(cx - 2, top + 10), (cx + 9, top + 10), (cx + 10, top + 16), (cx + 8, top + 20), (cx + 4, top + 21), (cx - 1, top + 20)], "skin")
    c.put(int(cx) + 10, top + 17, "skin")  # nose tip
    fringe = [(-1, 9, 0, 14), (1, 9, 2, 13), (3, 9, 4, 14), (5, 9, 6, 12), (7, 9, 8, 13)]
    for bx, by, tx, ty in fringe:
        c.poly([(cx + bx - 1, top + by), (cx + bx + 2, top + by), (cx + tx + 0.5, top + ty)], "hair")
    c.rect(int(cx) - 2, top + 8, int(cx) + 9, top + 10, "hair")
    # back hair over the nape (moves with sway)
    c.poly([(cx - 9, top + 10), (cx - 1, top + 10), (cx - 1, top + 19), (cx - 4, top + 22 + sway), (cx - 9, top + 20 + sway)], "hair")
    c.strand(int(cx) - 6, top + 12, int(cx) - 5, top + 19, 1)
    c.strand(int(cx) - 3, top + 12, int(cx) - 3, top + 18, 1)
    # ear
    c.rect(int(cx), top + 15, int(cx) + 1, top + 17, "skin")
    c.shade(int(cx), top + 16, 1)
    # eye
    ex = int(cx) + 5
    for dx in range(4):
        c.paint(ex + dx, top + 14, EYE["lash"])
    c.paint(ex, top + 15, EYE["iris_d"])
    c.paint(ex + 1, top + 15, EYE["iris"])
    c.paint(ex + 2, top + 15, EYE["shine"])
    c.paint(ex + 1, top + 16, EYE["iris_d"])
    c.paint(ex + 2, top + 16, EYE["iris"])
    c.paint(ex + 1, top + 12, hx(RAMP["hair"][1]))
    c.paint(ex + 2, top + 12, hx(RAMP["hair"][1]))
    c.paint(int(cx) + 8, top + 20, MOUTH)
    c.paint(int(cx) + 6, top + 18, BLUSH)


def pendant(c, x, y):
    """The star-ring pendant: a blue star in a gold frame, with a soft glow."""
    for dx, dy, m, t in ((1, 0, "gold", 3), (0, 1, "gold", 2), (2, 1, "gold", 2), (1, 1, "gem", 4), (1, 2, "gem", 2), (0, 2, "gem", 3),
                         (2, 2, "gem", 1), (1, 3, "gem", 1), (0, 3, "gold", 1), (2, 3, "gold", 1), (1, 4, "gold", 1),
                         (-1, 2, "gem", 3), (3, 2, "gem", 3)):  # the star's side points (a four-pointed star)
        c.put(x + dx, y + dy, m, t)


def body_front(c, p):
    b = p.bob
    # back of the cloak (seen around the legs) and its dark lining
    c.poly([(7, 24 + b), (25, 24 + b), (28 + p.sway, 45 + b), (4 + p.sway, 45 + b)], "lining")
    # tunic (long white shirt) with folds
    c.poly([(11, 24 + b), (21, 24 + b), (22, 42 + b), (10, 42 + b)], "shirt")
    for x, y0, y1 in ((13, 37, 41), (18, 37, 41), (15, 27, 32)):
        for y in range(y0 + b, y1 + b + 1):
            c.shade(x, y, 1)
    # belt with a gold buckle and a pouch
    c.rect(10, 34 + b, 21, 35 + b, "leather")
    c.rect(15, 34 + b, 16, 35 + b, "gold")
    c.rect(18, 36 + b, 20, 39 + b, "leather")
    c.shade(18, 36 + b, 4)
    # arms and gloves (swing with the walk)
    for side, x in ((-1, 9), (1, 21)):
        lift = -p.arm * side
        c.rect(x, 28 + b, x + 1, 35 + b + lift, "shirt")
        c.rect(x, 35 + b + lift, x + 1, 38 + b + lift, "leather")
        c.shade(x, 38 + b + lift, 1)
    # front cloak panels: open in the middle, wider and ragged at the hem
    hem = 44 + b
    left = [(8, 23 + b), (12, 23 + b), (12, hem - 1), (10, hem + 1), (7 + p.sway, hem), (4 + p.sway, hem + 1)]
    right = [(19, 23 + b), (24, 23 + b), (28 + p.sway, hem + 1), (25 + p.sway, hem), (22, hem + 1), (19, hem - 1)]
    c.poly(left, "cloak")
    c.poly(right, "cloak")
    # folds (vertical shadow lines) and lights
    for x0, x1, y0 in ((9, 6, 28), (11, 10, 30), (21, 23, 28), (23, 26, 31)):
        c.strand(x0 + 0, y0 + b, x1 + p.sway, hem - 2, 1)
    for x0, x1, y0 in ((10, 8, 27), (22, 25, 29)):
        c.strand(x0, y0 + b, x1 + p.sway, hem - 4, 3)
    # gold trim along the front edges and the hem
    c.line(12, 25 + b, 12, hem - 1, "gold", 2)
    c.line(19, 25 + b, 19, hem - 1, "gold", 2)
    for x in range(4 + p.sway, 12):
        if c.m(x, hem) == "cloak":
            c.put(x, hem, "gold", 2)
    for x in range(20, 29 + p.sway):
        if c.m(x, hem) == "cloak":
            c.put(x, hem, "gold", 2)
    for x, y in ((7, 33), (9, 40), (24, 33), (26, 40)):  # embroidery
        c.put(x + p.sway * (y > 36), y + b, "gold", 3)
    # hood folded over the shoulders, gold clasps, the pendant
    c.poly([(8, 21 + b), (24, 21 + b), (25, 25 + b), (7, 25 + b)], "cloak")
    c.line(9, 21 + b, 23, 21 + b, "cloak", 3)
    c.line(8, 25 + b, 24, 25 + b, "cloak", 1)
    c.put(11, 24 + b, "gold", 3)
    c.put(20, 24 + b, "gold", 3)
    pendant(c, 14, 25 + b)
    c.put(15, 24 + b, "leather", 1)  # cord


def body_back(c, p):
    b = p.bob
    for side, x in ((-1, 8), (1, 22)):
        lift = p.arm * side
        c.rect(x, 35 + b + lift, x + 1, 38 + b + lift, "leather")
    hem = 46 + b
    c.poly([(8, 22 + b), (24, 22 + b), (28 + p.sway, hem), (24 + p.sway, hem + 1), (20, hem), (16, hem + 1), (12, hem), (8 + p.sway, hem + 1), (4 + p.sway, hem)], "cloak")
    for x0, x1 in ((10, 7), (13, 12), (19, 20), (22, 25)):
        c.strand(x0, 27 + b, x1 + p.sway, hem - 2, 1)
    for x0, x1 in ((11, 9), (21, 23)):
        c.strand(x0, 27 + b, x1 + p.sway, hem - 3, 3)
    for x in range(4 + p.sway, 29 + p.sway):
        if c.m(x, hem) == "cloak":
            c.put(x, hem, "gold", 2)
    # the hood, folded on the shoulders
    c.poly([(9, 21 + b), (23, 21 + b), (22, 27 + b), (16, 29 + b), (10, 27 + b)], "cloak")
    c.line(10, 22 + b, 22, 22 + b, "cloak", 3)
    c.line(11, 27 + b, 21, 27 + b, "cloak", 1)
    c.line(16, 28 + b, 16, 28 + b, "cloak", 1)
    # the gold star (star ring) on the back
    cx, cy = 16 + (p.sway > 0), 36 + b
    for dx, dy in ((0, -4), (0, -3), (0, 3), (0, 4), (-4, 0), (-3, 0), (3, 0), (4, 0), (-2, -2), (2, -2), (-2, 2), (2, 2), (-1, 0), (1, 0), (0, -1), (0, 1)):
        c.put(cx + dx - 1, cy + dy, "gold", 2)
    c.put(cx - 1, cy, "gem", 3)
    for dx, dy in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
        c.put(cx + dx - 1, cy + dy, "gold", 1)


def body_side(c, p):
    """Facing right; the cloak flows behind him (to the left)."""
    b = p.bob
    hem = 45 + b
    c.poly([(9, 23 + b), (15, 23 + b), (15, hem), (8 - p.sway, hem + 1), (3 - p.sway, hem)], "cloak")  # behind
    c.poly([(14, 24 + b), (21, 24 + b), (22, 42 + b), (14, 42 + b)], "shirt")
    c.strand(17, 30 + b, 17, 41 + b, 1)
    c.rect(14, 34 + b, 21, 35 + b, "leather")
    c.rect(19, 34 + b, 20, 35 + b, "gold")
    c.rect(14, 36 + b, 16, 39 + b, "leather")
    # the near arm swings forward and back
    ax = 18 + 2 * p.arm
    c.rect(ax, 27 + b, ax + 2, 33 + b, "shirt")
    c.rect(ax, 33 + b, ax + 2, 36 + b, "leather")
    # folds and trim on the cloak behind
    for x0, x1 in ((11, 6), (13, 10)):
        c.strand(x0, 27 + b, x1 - p.sway, hem - 2, 1)
    c.strand(12, 26 + b, 8 - p.sway, hem - 4, 3)
    c.line(15, 25 + b, 15, hem - 1, "gold", 2)
    for x in range(3 - p.sway, 16):
        if c.m(x, hem) == "cloak":
            c.put(x, hem, "gold", 2)
    c.put(7 - p.sway, 38 + b, "gold", 3)
    # hood / collar, the pendant at the front of the chest
    c.poly([(9, 21 + b), (21, 21 + b), (21, 25 + b), (9, 26 + b)], "cloak")
    c.line(10, 21 + b, 20, 21 + b, "cloak", 3)
    pendant(c, 19, 25 + b)


def legs_front(c, p):
    for side, x0 in ((1, 11), (-1, 17)):  # his right leg is on the screen left
        lift = 2 if p.step == side else 0
        drop = 1 if p.step == -side else 0
        y = 41 + drop - lift + max(0, p.bob)
        c.rect(x0, y, x0 + 3, 48 - lift, "trousers")
        c.rect(x0 - 1, 48 - lift, x0 + 4, 49 - lift, "boot", 3)  # folded cuff
        c.rect(x0, 50 - lift, x0 + 3, 54 - lift, "boot")
        c.rect(x0 - 1, 53 - lift, x0 + 4, 55 - lift, "boot")
        c.put(x0 + 1, 51 - lift, "leather", 4)  # buckle strap
        c.put(x0 + 2, 51 - lift, "leather", 3)
        c.line(x0 - 1, 55 - lift, x0 + 4, 55 - lift, "boot", 1)  # sole


def legs_side(c, p):
    reach = 3 * p.step
    for dx, back in ((-reach, True), (reach, False)):
        x0 = 15 + dx
        lift = 1 if (back and p.step) else 0
        c.rect(x0, 41 + max(0, p.bob), x0 + 3, 48 - lift, "trousers", 1 if back else None)
        c.rect(x0 - 1, 48 - lift, x0 + 4, 49 - lift, "boot", 3)
        c.rect(x0, 50 - lift, x0 + 3, 54 - lift, "boot", 1 if back else None)
        c.rect(x0, 53 - lift, x0 + 6, 55 - lift, "boot", 1 if back else None)  # toe pointing right
        c.line(x0, 55 - lift, x0 + 6, 55 - lift, "boot", 0 if back else 1)


# ------------------------------------------------------------------ frames

def draw(direction, p):
    c = Canvas()
    top = 1 + p.bob
    if direction == "down":
        legs_front(c, p)
        body_front(c, p)
        hair_mass(c, 15.5, top, sway=p.sway)
        face_front(c, 15.5, top, sway=p.sway)
    elif direction == "up":
        legs_front(c, replace(p, step=-p.step))
        body_back(c, p)
        hair_mass(c, 15.5, top, sway=p.sway)
        # nape: pointed locks over the hood
        for bx in (-6, -3, 0, 3, 6):
            c.poly([(15.5 + bx - 1.5, top + 18), (15.5 + bx + 1.5, top + 18), (15.5 + bx + p.sway * 0.5, top + 22)], "hair")
        for x0 in (11, 16, 20):
            c.strand(x0, top + 9, x0 + (1 if x0 > 15 else -1), top + 19, 1)
        for x0, y0 in ((10, 4), (17, 3), (13, 9), (20, 9)):
            c.strand(x0, top + y0, x0 + 2, top + y0, 4)
    else:
        legs_side(c, p)
        body_side(c, p)
        hair_mass(c, 14.5, top, side=True, sway=p.sway)
        face_side(c, 14.5, top, sway=p.sway)
    return c


WALK = {  # frame index -> pose (the game plays 1, 0, 2, 0; frame 0 is also the idle pose)
    0: Pose(),
    1: Pose(bob=1, step=1, arm=-1, sway=-1),
    2: Pose(bob=1, step=-1, arm=1, sway=1),
}
SWIM = {0: Pose(water=44, stroke=0, sway=-1), 1: Pose(water=44, stroke=1, sway=1)}


def swim(direction, p):
    """Floating: head and shoulders above the water line, the rest seen faintly under the water."""
    sink = 21  # the standing pose moved down so the chest sits at the water line
    body = draw(direction, replace(p, water=0))
    cols = body.colours()
    out = [[None] * W for _ in range(H)]
    wl = p.water
    for y in range(H):
        sy = y - sink
        if not (0 <= sy < H):
            continue
        for x in range(W):
            col = cols[sy][x]
            if col is None:
                continue
            if y < wl:
                out[y][x] = col + (255,)
            elif y < wl + 7:
                # under the water: tinted towards the water colour, half seen
                k = 0.55
                u = WATER["under"]
                out[y][x] = tuple(round(col[i] * (1 - k) + u[i] * k) for i in range(3)) + (150 - (y - wl) * 15,)
    # arms stroking at the surface (alternating), gloves out of the water
    side_x = (6, 23) if direction in ("down", "up") else (21, 21)
    hand = side_x[p.stroke] if direction in ("down", "up") else side_x[0] + (2 if p.stroke else -1)
    glove = hx(RAMP["leather"][2]), hx(RAMP["leather"][0])
    for dx in range(3):
        out[wl - 1][hand + dx] = glove[0] + (255,)
        out[wl][hand + dx] = glove[1] + (255,)
    # the water surface: a ring of ripples with foam, alternating each frame
    ring = WATER["ring"] + (255,)
    ring_d = WATER["ring_d"] + (230,)
    foam = WATER["foam"] + (255,)
    for x in range(W):
        on = (x + p.stroke * 2) % 5
        if 2 <= x <= 29:
            out[wl][x] = (ring if on < 3 else ring_d) if out[wl][x] is None or on < 2 else out[wl][x]
        if 0 <= x <= 31 and on == 0:
            out[wl + 2][x] = ring_d
    for x in (4 + p.stroke * 3, 25 - p.stroke * 3):
        out[wl - 1][x] = foam
        out[wl - 1][x + 1] = foam
    for x in (1 + p.stroke, 29 - p.stroke):
        out[wl + 1][x] = ring
    return out


def finished(c):
    cols = c.colours()
    return [[(col + (255,)) if col else None for col in row] for row in cols]


def mirror(img):
    return [list(reversed(row)) for row in img]


def all_frames():
    frames = {}
    for d in ("down", "up", "right"):
        for i, pose in WALK.items():
            frames[f"player.walk.{d}.{i}"] = finished(draw(d, pose))
        for i, pose in SWIM.items():
            frames[f"player.swim.{d}.{i}"] = swim(d, pose)
    for k in [k for k in frames if ".right." in k]:
        frames[k.replace(".right.", ".left.")] = mirror(frames[k])
    return frames


# ------------------------------------------------------------------ PNG

def encode(w, h, raw):
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")


def png(img):
    raw = bytearray()
    for row in img:
        raw.append(0)
        for px in row:
            raw += bytes(px) if px else b"\x00\x00\x00\x00"
    return encode(W, H, raw)


def preview(frames, path, scale=4):
    """All frames in a grid (rows: down, up, right, left; columns: walk 0-2, swim 0-1) on grass and water."""
    order = [f"player.walk.{{d}}.{i}" for i in range(3)] + [f"player.swim.{{d}}.{i}" for i in range(2)]
    dirs = ("down", "up", "right", "left")
    gap = 4
    cw, ch = (W + gap) * len(order) + gap, (H + gap) * len(dirs) + gap
    raw = bytearray()
    for Y in range(ch * scale):
        raw.append(0)
        for X in range(cw * scale):
            x, y = X // scale, Y // scale
            col, row = (x - gap) // (W + gap), (y - gap) // (H + gap)
            fx, fy = (x - gap) % (W + gap), (y - gap) % (H + gap)
            bg = (0x2E, 0x5E, 0x9A) if col >= 3 else (0x4F, 0x8A, 0x3E)
            c = bg
            if 0 <= col < len(order) and 0 <= row < len(dirs) and fx < W and fy < H and x >= gap and y >= gap:
                px = frames[order[col].format(d=dirs[row])][fy][fx]
                if px:
                    a = px[3] / 255
                    c = tuple(round(px[i] * a + bg[i] * (1 - a)) for i in range(3))
            raw += bytes(c) + b"\xff"
    with open(path, "wb") as f:
        f.write(encode(cw * scale, ch * scale, raw))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    frames = all_frames()
    for name, img in frames.items():
        with open(os.path.join(OUT, f"{name}.png"), "wb") as f:
            f.write(png(img))
    preview(frames, PREVIEW)
    print(f"{len(frames)} frames -> src/art-proto/hero/, preview -> docs/hero/prototype_preview.png")
