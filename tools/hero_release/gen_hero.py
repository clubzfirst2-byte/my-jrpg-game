"""The hero — RELEASE art (QUALITY_POLICY.md): made at release quality, adopted after approval.

Design: docs/hero/HERO_DESIGN_SPEC.md (approved v2 direction). Animation: docs/hero/HERO_ANIMATION_SPEC.md.
Frames: hero.<action>.<down|up|right|left>.<n>.png, 32x56, feet at the bottom centre (row 55);
left is the mirror of right. Stage 1: idle (4), walk (6), run (6).

How it is drawn:
  * a SKELETON per frame (hip, knees, ankles, shoulders, elbows, hands, head) computed from the gait
    phase, so feet plant and lift, knees bend, the body bobs, the arms counter-swing and the cloak and
    hair trail behind — every frame in step with the others;
  * limbs are filled capsules; every part is a MATERIAL with a 5-tone ramp, lit from the top left,
    with a selective outline (tools/art_proto/pixel.py);
  * the head, face, hair and pendant are drawn pixel by pixel on top.

Writes src/art-release/hero/ and docs/hero/release/ previews.
Run: python3 tools/hero_release/gen_hero.py
"""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "art_proto"))
from pixel import Canvas, mirror, png  # noqa: E402

sys.path.insert(0, os.path.dirname(__file__))
import heads  # noqa: E402  (the hand-placed heads, option A)
import actions  # noqa: E402  (stage 2: every other action, with hands and props)
import body  # noqa: E402  (the hand-placed cloak, tunic and belt)

# the head: hand-placed pixel maps (heads.py) or the earlier shape-built head (kept for comparison)
HAND_HEADS = os.environ.get("HERO_HEAD", "hand") == "hand"
# the body: hand-placed pixel maps (body.py) or the earlier shape-built cloak and tunic
HAND_BODY = os.environ.get("HERO_BODY", "hand") == "hand"

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
OUT = os.path.join(ROOT, "src", "art-release", "hero")
W, H = 32, 56

RAMPS = {
    "hair": ["#2a160c", "#4e2e1a", "#7a4a2a", "#a8703f", "#d09a62"],
    "skin": ["#6e3e2c", "#c8906a", "#f2c49b", "#ffdcbc", "#fff0e0"],
    "cloak": ["#10180e", "#3e6234", "#6a9048", "#8eb062", "#b8d48a"],
    "lining": ["#10180e", "#1e3424", "#2a4632", "#3a5a40", "#4a6c50"],
    "shirt": ["#4a4640", "#a8a296", "#e4e0d6", "#f6f4ee", "#ffffff"],
    "leather": ["#24160c", "#4a3020", "#704c30", "#946c46", "#b88c5e"],
    "boot": ["#1e120a", "#3e2616", "#62402a", "#865c3c", "#a87a52"],
    "trousers": ["#14141c", "#22222e", "#323244", "#44445a", "#585872"],
    "gold": ["#5a4018", "#a07a30", "#e8c060", "#f8dc88", "#fff4c8"],
    "gem": ["#0e2a60", "#1a5cb8", "#2a8de2", "#78c8ff", "#e0f6ff"],
    "water": ["#0e3050", "#2a6a9a", "#5aa0d0", "#a8dcf8", "#f4fcff"],
}
EYE = {"lash": "#24223a", "iris": "#2a78d0", "iris_d": "#1a3c86", "shine": "#f0fbff"}
MOUTH, BLUSH = "#a8584e", "#f0a888"


def capsule(c, x0, y0, x1, y1, r, mat, tone=None):
    """A limb: every pixel within r of the segment (x0,y0)-(x1,y1)."""
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


# ------------------------------------------------------------------ the pose

class Pose:
    """Where everything is for one frame (all in pixels; feet on row 55 unless lifted)."""

    def __init__(self, **k):
        self.bob = 0  # body down (+) / up (-)
        self.lean = 0  # head and shoulders forward (side view, +x)
        self.near = (0, 0)  # near foot: (forward offset, lift)  — side: his right leg is near
        self.far = (0, 0)
        self.arm_near = 0  # hand forward (+) / back (-)
        self.arm_far = 0
        self.arm_bend = 0  # elbows bent (running)
        self.sway = 0  # cloak hem and hair tips lag: -1..2 (positive = trailing back / right)
        self.flare = 0  # how far the cloak flies back (running)
        self.breath = 0  # chest up (idle)
        self.glint = 0  # pendant highlight phase
        self.shift = 0  # front/back view: upper body sideways over the planted foot
        self.blink = False  # eyes shut (hurt, collapsing)
        # stage 2 (actions.py): the hands placed explicitly, props, the water line, the frame width
        self.hands = None
        self.props = ()
        self.water = None
        self.width = W
        # stage 5: arm poses chosen by name ({"R": "diag_up"}), and facing left drawn on its own
        self.arms = None
        self.swap = False
        self.__dict__.update(k)


def gait(i, n, stride, lift, bob_amp, arm, run=False):
    """Pose for frame i of an n-frame step cycle."""
    ph = 2 * math.pi * i / n
    s, cph = math.sin(ph), math.cos(ph)
    near = (round(stride * s), round(max(0.0, cph) * lift))
    far = (round(-stride * s), round(max(0.0, -cph) * lift))
    if run:
        bob = -round(abs(cph) * bob_amp)  # airborne between steps
    else:
        bob = round(abs(s) * bob_amp)  # lowest on the contact (legs apart)
    return Pose(
        bob=bob,
        near=near,
        far=far,
        arm_near=round(-arm * s),
        arm_far=round(arm * s),
        sway=round((2.2 if run else 1.4) * math.sin(ph - math.pi / 2)),
        shift=round(0.9 * s),  # the upper body shifts over the planted foot
        lean=2 if run else 0,
        arm_bend=3 if run else 0,
        flare=3 if run else 0,
        glint=i % 3,
    )


# ------------------------------------------------------------------ head (pixel work on top of shapes)

def hair_mass(c, cx, top, side=False, sway=0):
    c.ellipse(cx, top + 11, 10.6, 10.0, "hair")
    clumps = [(-7, 4.5), (-2, 2.5), (3.5, 2.5), (8, 5), (-10, 10), (10, 10), (-9.5, 15), (9.5, 15)]
    if side:
        clumps = [(-6, 4.5), (-1, 2.5), (4, 3), (8, 6), (-10, 10), (-10, 15), (-8, 19)]
    for dx, dy in clumps:
        c.ellipse(cx + dx, top + dy, 4.2, 3.6, "hair")
    tips = [(-13, 8, -15, 6), (13, 8, 15, 6), (-12, 17, -13 - max(0, sway), 20 + abs(sway)), (12, 17, 13 + max(0, -sway), 20 + abs(sway))]
    if side:
        tips = [(-13, 8, -15, 6), (-13, 14, -15 - sway, 15), (-11, 20, -12 - sway, 23), (11, 6, 13, 4)]
    for bx, by, tx, ty in tips:
        c.poly([(cx + bx - 2, top + by - 1), (cx + bx + 2, top + by + 1), (cx + tx, top + ty)], "hair")
    c.line(int(cx) + 1, top, int(cx) + 2, top - 3, "hair")  # the cowlick
    c.put(int(cx) + 3, top - 4, "hair")
    c.put(int(cx) + 4, top - 4, "hair")
    for dx, dy in clumps[:4]:  # each clump: a shadowed lower edge, a lit upper edge
        for a in range(-3, 4):
            x = int(cx + dx + a)
            y = top + int(dy + 3.4 * (1 - (a / 4.2) ** 2) ** 0.5)
            if c.m(x, y + 1) == "hair":
                c.shade(x, y, 1)
        for a in range(-2, 2):
            c.shade(int(cx + dx + a), top + int(dy - 2.2), 4 if a < 0 else 3)
    for x0, y0, x1, y1 in ((-9, 7, -10, 12), (9, 7, 10, 12), (-4, 6, -5, 9), (4, 6, 5, 9)):
        c.strand(int(cx + x0), top + y0, int(cx + x1), top + y1, 1)


def face_front(c, cx, top, sway=0, blink=False):
    c.poly([(cx - 6.5, top + 10), (cx + 6.5, top + 10), (cx + 6.5, top + 17), (cx + 3.5, top + 21), (cx - 3.5, top + 21), (cx - 6.5, top + 17)], "skin")
    for bx0, bx1, tx, ty in ((-8, -2, -6, 15), (-3, 3, 0, 13), (2, 8, 5, 14)):  # three locks of fringe
        c.poly([(cx + bx0, top + 8), (cx + bx1, top + 8), (cx + bx1 - 1, top + 10), (cx + tx + 0.5, top + ty)], "hair")
    c.poly([(cx - 8, top + 7), (cx + 8, top + 7), (cx + 8, top + 10), (cx - 8, top + 10)], "hair")
    for x0, y0, x1, y1 in ((-3, 9, -4, 13), (2, 9, 2, 12), (-7, 10, -7, 13)):
        c.strand(int(cx + x0), top + y0, int(cx + x1), top + y1, 1)
    for x0, y0, x1, y1 in ((-6, 8, -4, 8), (0, 8, 1, 8), (4, 8, 5, 8)):
        c.strand(int(cx + x0), top + y0, int(cx + x1), top + y1, 3)
    c.poly([(cx - 9, top + 10), (cx - 7, top + 10), (cx - 6, top + 20 + max(0, sway)), (cx - 8, top + 21 + max(0, sway))], "hair")
    c.poly([(cx + 7, top + 10), (cx + 9, top + 10), (cx + 8, top + 20 + max(0, -sway)), (cx + 6, top + 19 + max(0, -sway))], "hair")
    for ex in (int(cx) - 5, int(cx) + 2):  # narrow blue eyes with a shine
        for dx in range(4):
            c.paint(ex + dx, top + 14, EYE["lash"])
        if blink:
            for dx in range(4):
                c.paint(ex + dx, top + 15, RAMPS["skin"][1])
            continue
        c.paint(ex, top + 15, EYE["iris_d"])
        c.paint(ex + 1, top + 15, EYE["iris"])
        c.paint(ex + 2, top + 15, EYE["iris"])
        c.paint(ex + 3, top + 15, EYE["shine"])
        c.paint(ex + 1, top + 16, EYE["iris_d"])
        c.paint(ex + 2, top + 16, EYE["iris"])
        c.shade(ex, top + 16, 1)
        c.shade(ex + 3, top + 16, 2)
    for x in (int(cx) - 5, int(cx) - 4, int(cx) + 4, int(cx) + 5):
        c.paint(x, top + 12, RAMPS["hair"][1])  # resolute brows
    c.shade(int(cx), top + 18, 1)
    c.paint(int(cx) - 1, top + 20, MOUTH)
    c.paint(int(cx), top + 20, MOUTH)
    c.paint(int(cx) - 5, top + 18, BLUSH)
    c.paint(int(cx) + 4, top + 18, BLUSH)
    for x in range(int(cx) - 3, int(cx) + 3):
        c.shade(x, top + 21, 1)


def face_side(c, cx, top, sway=0):
    c.poly([(cx - 2, top + 10), (cx + 9, top + 10), (cx + 10, top + 16), (cx + 8, top + 20), (cx + 4, top + 21), (cx - 1, top + 20)], "skin")
    c.put(int(cx) + 10, top + 17, "skin")
    for bx, by, tx, ty in ((-1, 9, 0, 14), (1, 9, 2, 13), (3, 9, 4, 14), (5, 9, 6, 12), (7, 9, 8, 13)):
        c.poly([(cx + bx - 1, top + by), (cx + bx + 2, top + by), (cx + tx + 0.5, top + ty)], "hair")
    c.rect(int(cx) - 2, top + 8, int(cx) + 9, top + 10, "hair")
    c.poly([(cx - 9, top + 10), (cx - 1, top + 10), (cx - 1, top + 19), (cx - 4 - sway, top + 22), (cx - 9 - sway, top + 20)], "hair")
    c.strand(int(cx) - 6, top + 12, int(cx) - 5, top + 19, 1)
    c.strand(int(cx) - 3, top + 12, int(cx) - 3, top + 18, 1)
    c.rect(int(cx), top + 15, int(cx) + 1, top + 17, "skin")
    c.shade(int(cx), top + 16, 1)
    ex = int(cx) + 5
    for dx in range(4):
        c.paint(ex + dx, top + 14, EYE["lash"])
    c.paint(ex, top + 15, EYE["iris_d"])
    c.paint(ex + 1, top + 15, EYE["iris"])
    c.paint(ex + 2, top + 15, EYE["shine"])
    c.paint(ex + 1, top + 16, EYE["iris_d"])
    c.paint(ex + 2, top + 16, EYE["iris"])
    c.paint(ex + 1, top + 12, RAMPS["hair"][1])
    c.paint(ex + 2, top + 12, RAMPS["hair"][1])
    c.paint(int(cx) + 8, top + 20, MOUTH)
    c.paint(int(cx) + 6, top + 18, BLUSH)


def head_back_detail(c, top, sway):
    for bx in (-6, -3, 0, 3, 6):  # pointed locks over the hood, moving with the sway
        c.poly([(15.5 + bx - 1.5, top + 18), (15.5 + bx + 1.5, top + 18), (15.5 + bx + sway * 0.6, top + 22)], "hair")
    for x0 in (11, 16, 20):
        c.strand(x0, top + 9, x0 + (1 if x0 > 15 else -1), top + 19, 1)
    for x0, y0 in ((10, 4), (17, 3), (13, 9), (20, 9)):
        c.strand(x0, top + y0, x0 + 2, top + y0, 4)


def pendant(c, x, y, glint):
    """The star-ring pendant: a blue four-pointed star in a gold frame; its shine moves (glint)."""
    for dx, dy, m, t in ((1, 0, "gold", 3), (0, 1, "gold", 2), (2, 1, "gold", 2), (1, 1, "gem", 4), (1, 2, "gem", 2), (0, 2, "gem", 3),
                         (2, 2, "gem", 1), (1, 3, "gem", 1), (0, 3, "gold", 1), (2, 3, "gold", 1), (1, 4, "gold", 1), (-1, 2, "gem", 3), (3, 2, "gem", 3)):
        c.put(x + dx, y + dy, m, t)
    c.put(x + (0, 1, 2)[glint], y + 2, "gem", 4)


# ------------------------------------------------------------------ bodies

def front(p, back=False):
    """Front (down) or back (up) view."""
    c = Canvas(W, H, RAMPS)
    b = p.bob - p.breath
    # back of the cloak / lining, behind everything
    hem = 46 + p.bob
    c.poly([(7, 24 + b), (25, 24 + b), (28 + p.sway, hem), (4 + p.sway, hem)], "cloak" if back else "lining")
    # legs: the stepping foot lifts (knee up), the planted one carries the body; forward foot 1 lower
    for (fwd, lift), x0 in ((p.near, 11), (p.far, 17)):
        down = 1 if fwd > 1 else 0
        y_foot = 55 - lift + down
        y_foot = min(55, y_foot)
        knee = 47 - lift // 2 + p.bob // 2
        c.rect(x0, 41 + p.bob, x0 + 3, y_foot - 7, "trousers")
        c.rect(x0, knee, x0 + 3, knee, "trousers", 3 if lift else 2)  # knee highlight when it lifts
        c.rect(x0 - 1, y_foot - 7, x0 + 4, y_foot - 6, "boot", 3)  # folded cuff
        c.rect(x0, y_foot - 5, x0 + 3, y_foot - 1, "boot")
        c.rect(x0 - 1, y_foot - 2, x0 + 4, y_foot, "boot")
        c.line(x0 - 1, y_foot, x0 + 4, y_foot, "boot", 1)  # sole
        c.put(x0 + 1, y_foot - 4, "leather", 4)  # buckle
        c.put(x0 + 2, y_foot - 4, "leather", 3)
    if not back and not HAND_BODY:
        # tunic, folds, belt with a gold buckle, pouch
        c.poly([(11, 24 + b), (21, 24 + b), (22, 42 + p.bob), (10, 42 + p.bob)], "shirt")
        for x, y0, y1 in ((13, 37, 41), (18, 37, 41), (15, 27, 32)):
            c.strand(x, y0 + p.bob, x, y1 + p.bob, 1)
        c.rect(10, 34 + p.bob, 21, 35 + p.bob, "leather")
        c.rect(15, 34 + p.bob, 16, 35 + p.bob, "gold")
        c.rect(18, 36 + p.bob, 20, 39 + p.bob, "leather")
        c.shade(18, 36 + p.bob, 4)
    # arms swinging (the hand rises as the arm swings forward); actions place the hands themselves
    for side, x, swing in ((-1, 8, p.arm_near), (1, 22, p.arm_far)) if p.hands is None and not actions.HAND_ARMS else ():
        hand_y = 37 + b - abs(swing) - p.arm_bend
        c.rect(x, 28 + b, x + 1, hand_y - 1, "shirt" if not back else "lining")
        c.rect(x, hand_y, x + 1, hand_y + 2, "leather")
        c.shade(x, hand_y + 2, 1)
    if HAND_BODY:
        body.body_front(c, b, p.sway, back=back)
        if back:  # the gold star on the back
            cx, cy = 16 + (p.sway > 0), 36 + b
            for dx, dy in ((0, -4), (0, -3), (0, 3), (0, 4), (-4, 0), (-3, 0), (3, 0), (4, 0), (-2, -2), (2, -2), (-2, 2), (2, 2), (-1, 0), (1, 0), (0, -1), (0, 1)):
                c.put(cx + dx - 1, cy + dy, "gold", 3 if dy < 0 or dx < 0 else 2)
            c.put(cx - 1, cy, "gem", 3 + (p.glint == 1))
        else:
            pendant(c, 14, 25 + b, p.glint)
            c.put(15, 24 + b, "leather", 1)
    elif back:
        # the whole back is cloak: folds, the gold star, the ragged gold hem, the folded hood
        c.poly([(8, 22 + b), (24, 22 + b), (28 + p.sway, hem), (24 + p.sway, hem + 1), (20, hem), (16, hem + 1), (12, hem), (8 + p.sway, hem + 1), (4 + p.sway, hem)], "cloak")
        for x0, x1 in ((10, 7), (13, 12), (19, 20), (22, 25)):
            c.strand(x0, 27 + b, x1 + p.sway, hem - 2, 1)
        for x0, x1 in ((11, 9), (21, 23)):
            c.strand(x0, 27 + b, x1 + p.sway, hem - 3, 3)
        for x in range(4 + p.sway, 29 + p.sway):
            if c.m(x, hem) == "cloak":
                c.put(x, hem, "gold", 2)
        c.poly([(9, 21 + b), (23, 21 + b), (22, 27 + b), (16, 29 + b), (10, 27 + b)], "cloak")
        c.line(10, 22 + b, 22, 22 + b, "cloak", 3)
        c.line(11, 27 + b, 21, 27 + b, "cloak", 1)
        cx, cy = 16 + (p.sway > 0), 36 + b
        for dx, dy in ((0, -4), (0, -3), (0, 3), (0, 4), (-4, 0), (-3, 0), (3, 0), (4, 0), (-2, -2), (2, -2), (-2, 2), (2, 2), (-1, 0), (1, 0), (0, -1), (0, 1)):
            c.put(cx + dx - 1, cy + dy, "gold", 2)
        c.put(cx - 1, cy, "gem", 3 + (p.glint == 1))
    else:
        # front cloak panels, open in the middle, folds and light, gold trim and embroidery
        left = [(8, 23 + b), (12, 23 + b), (12, hem - 1), (10, hem + 1), (7 + p.sway, hem), (4 + p.sway, hem + 1)]
        right = [(19, 23 + b), (24, 23 + b), (28 + p.sway, hem + 1), (25 + p.sway, hem), (22, hem + 1), (19, hem - 1)]
        c.poly(left, "cloak")
        c.poly(right, "cloak")
        for x0, x1, y0 in ((9, 6, 28), (11, 10, 30), (21, 23, 28), (23, 26, 31)):
            c.strand(x0, y0 + b, x1 + p.sway, hem - 2, 1)
        for x0, x1, y0 in ((10, 8, 27), (22, 25, 29)):
            c.strand(x0, y0 + b, x1 + p.sway, hem - 4, 3)
        c.line(12, 25 + b, 12, hem - 1, "gold", 2)
        c.line(19, 25 + b, 19, hem - 1, "gold", 2)
        for x in list(range(4 + p.sway, 12)) + list(range(20, 29 + p.sway)):
            if c.m(x, hem) == "cloak":
                c.put(x, hem, "gold", 2)
        for x, y in ((7, 33), (9, 40), (24, 33), (26, 40)):
            c.put(x + p.sway * (y > 36), y + b, "gold", 3)
        c.poly([(8, 21 + b), (24, 21 + b), (25, 25 + b), (7, 25 + b)], "cloak")  # the hood on the shoulders
        c.line(9, 21 + b, 23, 21 + b, "cloak", 3)
        c.line(8, 25 + b, 24, 25 + b, "cloak", 1)
        c.put(11, 24 + b, "gold", 3)
        c.put(20, 24 + b, "gold", 3)
        pendant(c, 14, 25 + b, p.glint)
        c.put(15, 24 + b, "leather", 1)
    top = 1 + b
    if HAND_HEADS:
        (heads.head_back(c, top, p.sway) if back else heads.head_front(c, top, p.sway, p.blink))
    else:
        hair_mass(c, 15.5, top, sway=p.sway)
        if back:
            head_back_detail(c, top, p.sway)
        else:
            face_front(c, 15.5, top, sway=p.sway, blink=getattr(p, "blink", False))
    # the forward-swinging hand comes out past the cloak's edge (running: fists pumping at the chest)
    for side, x, swing in ((-1, 11, p.arm_near), (1, 19, p.arm_far)):
        if swing > 0 and not back and p.hands is None and not actions.HAND_ARMS:
            hy = 36 + b - swing - p.arm_bend
            c.rect(x, hy, x + 1, hy + 2, "leather")
            c.shade(x, hy, 4)
            c.put(x + (1 if side < 0 else 0), hy - 1, "shirt", 1)  # cuff
    if p.shift:
        shift_upper(c, 41 + p.bob, p.shift)
    return c


def shift_upper(c, y_hip, dx):
    """Moves everything above the hip sideways by dx (the weight shift of a step)."""
    for y in range(0, y_hip):
        for grid in (c.mat, c.tone, c.rgb):
            row = grid[y]
            grid[y] = ([None] * dx + row[:-dx]) if dx > 0 else (row[-dx:] + [None] * (-dx))


def side(p):
    """Facing right. His left side is near (the far leg/arm are behind, darker)."""
    c = Canvas(W, H, RAMPS)
    b = p.bob - p.breath
    hip = (16, 41 + p.bob)
    sh = (16 + p.lean, 26 + b)
    hem = 45 + p.bob
    # the cloak behind him: it trails back (left) and flares when running
    tail = 3 - p.sway - p.flare
    if not HAND_BODY:
        c.poly([(9 + p.lean, 23 + b), (15 + p.lean, 23 + b), (15, hem), (8 - p.sway - p.flare, hem + 1), (tail, hem - p.flare)], "cloak")
    # far leg, far arm (behind, in shadow)
    def leg(fwd, lift, tone):
        ax, ay = hip[0] + fwd, 52 - lift
        kx, ky = hip[0] + fwd * 0.6 + (1.5 if lift else 0.5), (hip[1] + ay) / 2 - (lift * 0.5)
        capsule(c, hip[0], hip[1], kx, ky, 2.0, "trousers", tone)
        capsule(c, kx, ky, ax, ay - 2, 1.8, "trousers", tone)
        capsule(c, ax, ay - 3, ax, ay, 1.9, "boot", tone)
        toe = 4 if lift < 2 else 3
        c.rect(int(ax) - 1, ay + 1, int(ax) + toe, ay + 3 - (1 if lift > 2 else 0), "boot", tone)
        c.line(int(ax) - 1, ay + 3 - (1 if lift > 2 else 0), int(ax) + toe, ay + 3 - (1 if lift > 2 else 0), "boot", 0 if tone == 1 else 1)
        c.rect(int(ax) - 2, ay - 3, int(ax) + 2, ay - 2, "boot", 3 if tone is None else 1)  # cuff

    def arm(swing, tone, near=False):
        ex, ey = sh[0] + swing * 0.6, sh[1] + 6 - p.arm_bend
        hx_, hy = sh[0] + swing + (p.arm_bend if swing > 0 else 0), sh[1] + 11 - p.arm_bend * (1.6 if swing > 0 else 0.8)
        # the upper arm is under the cloak (it drapes over the shoulder); the sleeve shows below it
        capsule(c, sh[0], sh[1] + 1, ex, ey, 1.4 if near else 1.2, "cloak" if near else "shirt", 2 if near else tone)
        capsule(c, ex, ey, hx_, hy, 1.1, "shirt", 1 if near else tone)
        capsule(c, hx_, hy, hx_ + 0.5, hy + 1.2, 1.3, "leather", tone)

    leg(p.far[0], p.far[1], 1)
    if p.hands is None and not actions.HAND_ARMS:
        arm(p.arm_far, 1)
    if HAND_BODY:
        body.body_side(c, b, p.lean, p.sway, p.flare)
        leg(p.near[0], p.near[1], None)
    else:
        # torso: tunic leaning with the run, belt, pouch at the back
        c.poly([(13 + p.lean, 24 + b), (20 + p.lean, 24 + b), (21, 42 + p.bob), (13, 42 + p.bob)], "shirt")
        c.strand(17 + p.lean // 2, 30 + b, 17, 41 + p.bob, 1)
        c.rect(13, 34 + p.bob, 21, 35 + p.bob, "leather")
        c.rect(19, 34 + p.bob, 20, 35 + p.bob, "gold")
        c.rect(12, 36 + p.bob, 14, 39 + p.bob, "leather")
        leg(p.near[0], p.near[1], None)
        # folds and trim on the trailing cloak
        for x0, x1 in ((11, 6), (13, 10)):
            c.strand(x0 + p.lean, 27 + b, x1 - p.sway - p.flare, hem - 2, 1)
        c.strand(12 + p.lean, 26 + b, 8 - p.sway - p.flare, hem - 4, 3)
        c.line(15 + p.lean, 25 + b, 15, hem - 1, "gold", 2)
        for x in range(0, 16):
            if c.m(x, hem) == "cloak" or c.m(x, hem - p.flare) == "cloak":
                c.put(x, hem if c.m(x, hem) == "cloak" else hem - p.flare, "gold", 2)
        c.put(7 - p.sway - p.flare, 38 + p.bob, "gold", 3)
        # hood / collar
        c.poly([(9 + p.lean, 21 + b), (21 + p.lean, 21 + b), (21 + p.lean, 25 + b), (9 + p.lean, 26 + b)], "cloak")
        c.line(10 + p.lean, 21 + b, 20 + p.lean, 21 + b, "cloak", 3)
    pendant(c, 19 + p.lean, 25 + b, p.glint)
    if p.hands is None and not actions.HAND_ARMS:
        arm(p.arm_near, None, near=True)
    top = 1 + b
    if HAND_HEADS:
        heads.head_side(c, top, p.sway + (1 if p.flare else 0), dx=p.lean, blink=p.blink)
    else:
        hair_mass(c, 14.5 + p.lean, top, side=True, sway=p.sway + (1 if p.flare else 0))
        face_side(c, 14.5 + p.lean, top, sway=p.sway + (1 if p.flare else 0))
    return c


# ------------------------------------------------------------------ the actions (stage 1)

def idle(i):
    # breathing in over two frames, out over two; the cloak hem and hair settle; the pendant glints
    return Pose(breath=(0, 1, 1, 0)[i], sway=(0, 0, 1, 1)[i] if i else 0, glint=(0, 1, 2, 1)[i])


def walk(i):
    return gait(i, 6, stride=3, lift=3, bob_amp=1, arm=2)


def run(i):
    return gait(i, 6, stride=5, lift=5, bob_amp=1, arm=3, run=True)


ACTIONS = {"idle": (4, idle), "walk": (6, walk), "run": (6, run), **{k: (n, None) for k, (n, _) in actions.STAGE2.items()}}


def draw(action, d, i):
    if action in actions.STAGE2 and d == "left" and action in actions.OWN_LEFT:
        # facing left with a weapon: drawn facing right with his LEFT arm near and the sword arm far,
        # then mirrored, so the sword stays in his right hand (not a plain mirror of facing right)
        _, pose_of = actions.STAGE2[action]
        k = pose_of("side", i)
        k.pop("_back", None)
        k.pop("_up", None)
        k = actions.for_left(k)
        p = Pose(**k, swap=True)
        return mirror(actions.finish(side(p), p, "side").colours())
    if action in actions.STAGE2:
        _, pose_of = actions.STAGE2[action]
        view = "side" if d == "right" else d
        k = pose_of(view, i)
        if k.pop("_back", False):
            view = "up"  # climbing: he faces the wall whichever way he goes
            k = pose_of("up", i)
            k.pop("_back", None)
        k.pop("_up", None)
        if view == "up" and action in actions.SHARED_BACK and k.get("hands"):
            k["hands"] = {"R": k["hands"]["L"], "L": k["hands"]["R"]}
        p = Pose(**k)
        if view == "up":
            p = Pose(**{**p.__dict__, "near": p.far, "far": p.near})
        c = side(p) if view == "side" else front(p, back=view == "up")
        return actions.finish(c, p, view).colours()
    count, pose_of = ACTIONS[action]
    p = pose_of(i)
    if d == "down":
        return actions.finish(front(p), p, "down").colours()
    if d == "up":
        p2 = Pose(**{**p.__dict__, "near": p.far, "far": p.near, "arm_near": p.arm_far, "arm_far": p.arm_near})
        return actions.finish(front(p2, back=True), p2, "up").colours()
    return actions.finish(side(p), p, "side").colours()


def all_frames():
    out = {}
    for action, (count, _) in ACTIONS.items():
        for d in ("down", "up", "right"):
            for i in range(count):
                out[f"hero.{action}.{d}.{i}"] = draw(action, d, i)
        for i in range(count):
            out[f"hero.{action}.left.{i}"] = draw(action, "left", i) if action in actions.OWN_LEFT else mirror(out[f"hero.{action}.right.{i}"])
    return out


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    frames = all_frames()
    for name, img in frames.items():
        with open(os.path.join(OUT, f"{name}.png"), "wb") as fh:
            fh.write(png(img))
    print(f"{len(frames)} release frames -> src/art-release/hero/")
