"""v3 pilot (round 2): the hero, hand built at 2x detail (64 x 112, density 4), facing down:
idle 4 + walk 6 frames.

Round 1 upscaled the v1 frames; the inspection asked for a real redraw. Every part is now drawn on the
64 x 112 grid (hdkit.py): hair as separate locks flowing from the crown, the face from a hand map
(v1's brows and one-colour mouth), the cloak as panels with 3 large folds a side and a dark band inside
its edge, v1's grey gauntlets along the body (round 3), leather hands with a thumb and two finger grooves, trousers and
boots that step. Proportions, colours (v1 ramps, outline values unchanged) and timing follow the
approved v1 frames (src/art-release/hero/, read only).
Writes src/art-release-v3/hero/hero.<idle|walk>.down.<n>.png
Run: python3 tools/art_v3/gen_hero_v3.py
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402

from hdkit import capsule, edge_band, gauntlet, grooves, hand, hand_stamp, lock  # noqa: E402
from v3lib import ROOT, Canvas, absorb_cloth_islands, cloth_islands, despeckle, edge_cuts, erode, hx, ramp6, save, stray_pieces  # noqa: E402

OUT = os.path.join(ROOT, "src", "art-release-v3", "hero")
W, H = 64, 112
# the approved v1 ramps (tools/hero_release/gen_hero.py RAMPS), as v3 6-tone ramps
V1 = {
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
    # the props' v1 ramps (tools/art_proto/pixel.py BASE_RAMPS)
    "wood": ["#1e1008", "#4a2c16", "#6e4424", "#906038", "#b07e50"],
    "steel": ["#1a1e26", "#4a5260", "#7a8494", "#a8b2c0", "#e0e6ee"],
    "bone": ["#3a3226", "#9a8c70", "#d0c4a4", "#e8dec4", "#fff8e4"],
    "water": ["#0e3050", "#2a6a9a", "#5aa0d0", "#a8dcf8", "#f4fcff"],
}
RAMPS = {k: ramp6(v) for k, v in V1.items()}
EYE = {"L": "#24223a", "D": "#1a3c86", "I": "#2a78d0", "B": "#4ea2ec", "K": "#13285e", "W": "#f0fbff",
       "G": "#d8cfc6"}
MOUTH, BLUSH = "#a8584e", "#f0a888"

# hand map of one eye (8 x 6): the v1 eye (flat lash, iris below, shine on the right) at 2x detail
EYE_L = [  # the image-left eye (v1 at 2x): a thick upper lid slanting down to the outer corner, the
    # iris below it with v1's shine box (white + light grey) on the right
    "..LLLLLL",
    "LLLLLLLL",
    "LDDDDWWG",
    ".DIIIWWG",
    ".DIKKI..",
    "..DIIB..",
]
EYE_R = [  # the image-right eye: the lid slants down to the outer (right) corner
    "LLLLLL..",
    "LLLLLLLL",
    ".DDDDWWG",
    ".DIIIWWG",
    ".DIKKI..",
    "..DIIB..",
]


EYE_SHUT = [  # the image-left eye shut (8 x 3)
    "L.......",
    ".LLLLLL.",
    "..LLLL..",
]


def head(c, oy, lag, blink=False):
    """Hair (back mass, then tapered locks from the crown), the face, then the features.
    Round 3: v1's outline (side hair ending in points just below the ears, spikes on top and out at
    the sides, not a helmet), curved pointed locks, a flat-lit face (shade only under the bangs and
    along the jaw)."""
    # hero round 3: v1's onion crown — the top rises to the middle spike (the highest, row 3), the side
    # spikes 3-4 rows lower, the head's shoulders down to row ~12 at x 8 / 56; drawn inside the frame
    # from the start (nothing squeezed), so the head keeps its height in every frame
    mass = c.m_poly([(4, 26 + oy), (4, 18 + oy), (8, 13 + oy), (14, 11 + oy), (20, 9 + oy), (26, 7.5 + oy), (32, 4 + oy),
                     (38, 7.5 + oy), (44, 9 + oy), (50, 11 + oy), (56, 13 + oy), (60, 18 + oy), (60, 26 + oy), (57, 30 + oy), (53, 40 + oy + lag), (48, 33 + oy), (47, 26 + oy), (16, 26 + oy),
                     (15, 33 + oy), (10, 40 + oy + lag), (6, 30 + oy)])
    c.fill(mass, "hair")
    c.shade_part(mass, tones=(1, 2, 2, 3, 3), norm=True)
    face = c.m_poly([(15, 22 + oy), (48, 22 + oy), (49, 33 + oy), (47, 40 + oy), (42, 44 + oy), (35, 46 + oy),
                     (28, 46 + oy), (21, 44 + oy), (17, 40 + oy), (15, 33 + oy)])
    c.fill(face, "skin", 4)  # v1's skin: the face #ffdcbc, its shade #f2c49b (round 4)
    for y, x in zip(*np.nonzero(face)):  # shade: one column on the right and the jaw only
        if x >= 47 or (y >= 44 + oy) or (x >= 45 and y >= 41 + oy):
            c.tone[y, x] = 3
    # hero round 3: the fringe comes down to just over the brows with a jagged lower edge (locks' tips)
    fore = c.m_poly([(15, 14 + oy), (49, 14 + oy), (49, 27 + oy), (46, 29 + oy), (42, 26 + oy), (38, 29 + oy), (35, 26 + oy),
                     (32, 28 + oy), (29, 26 + oy), (26, 29 + oy), (22, 26 + oy), (19, 29 + oy), (15, 27 + oy)])
    c.fill(fore, "hair", 2)
    cr = (31, 9 + oy)
    # (root, tip, root width, bend): every lock tapers to a point and curves
    side = [((14, 18 + oy), (9, 40 + oy + lag), 9, 2.5), ((50, 18 + oy), (54, 40 + oy + lag), 9, -2.5)]
    crown = [((cr[0] - 4, cr[1] + 2), (6, 23 + oy), 12, 3.0), ((cr[0] + 4, cr[1] + 2), (58, 25 + oy), 12, -3.0),
             ((cr[0] - 2, cr[1]), (15, 28 + oy), 11, 2.5), ((cr[0] + 2, cr[1]), (49, 28 + oy), 11, -2.5)]
    spikes = [((32, 13 + oy), (32, 3 + oy), 9, 0.3), ((26, 13 + oy), (21, 8 + oy), 8, 1.0),
              ((38, 13 + oy), (43, 8 + oy), 8, -1.0), ((13, 17 + oy), (5, 18 + oy), 8, 1.5),
              ((51, 17 + oy), (59, 20 + oy), 8, -1.5)]
    bangs = [((20, 13 + oy), (17, 30 + oy), 8, 2.0), ((27, 13 + oy), (24, 29 + oy + lag), 8, 1.5),
             ((32, 13 + oy), (31, 28 + oy), 7, -0.5), ((38, 13 + oy), (40, 29 + oy + lag), 8, -1.5),
             ((44, 13 + oy), (48, 30 + oy), 8, -2.0)]  # hero round 3: down to just over the brows
    # the top of the head (hero round, inspection P3-15): the crown and spike locks are drawn first;
    # each keeps its own light/dark facet but no dark lower band (which stacked into horizontal lines
    # across the crown), and each has one groove running out from the crown along it (1 texel darker,
    # stopping before the tip). Then the face-framing side locks and bangs in front, as before.
    top = np.zeros((H, W), bool)
    for root, tip, w, bend in crown + spikes:
        m = lock(c, root, tip, w, bend)
        top |= m
        c.fill(m, "hair")
        c.shade_part(m, tones=(3, 3, 4, 4, 5), norm=True, global_mask=mass, gmix=0.6)
    for root, tip, w, bend in crown + spikes:
        (x0, y0), (x1, y1) = root, tip
        L = math.hypot(x1 - x0, y1 - y0) or 1
        nx, ny = -(y1 - y0) / L, (x1 - x0) / L
        if ny < 0 or (ny == 0 and nx < 0):  # the groove on the lock's lower / right side (away from the light)
            nx, ny = -nx, -ny
        pts = []
        for i in range(1, 8):
            t = i / 10
            off = bend * math.sin(math.pi * t) + w * 0.2 * (1 - t)
            pts.append((x0 + (x1 - x0) * t + nx * off, y0 + (y1 - y0) * t + ny * off))
        g = c.m_line(pts, 0.9) & top
        for y, x in zip(*np.nonzero(g)):
            c.tone[y, x] = 2
    for root, tip, w, bend in side + bangs:
        m = lock(c, root, tip, w, bend)
        c.fill(m, "hair")
        c.shade_part(m, tones=(2, 3, 3, 4, 5), norm=True, global_mask=mass, gmix=0.35)
        grooves(c, m, drop=1, sides=True)
    # hero round 3: above row 16 the hair keeps to the onion (the mass) and the spikes only — the
    # crown locks' wide roots no longer square the top off
    _spk = np.zeros(c.mat.shape, bool)
    for _r, _t, _w, _b in spikes:
        _spk |= lock(c, _r, _t, _w, _b)
    _yy = np.mgrid[0:c.h, 0:c.w][0]
    _out = (c.mat == c.mid("hair")) & ~(mass | _spk) & (_yy < 16 + oy)
    c.mat[_out] = 0
    import hero_views as _HV
    _HV.keep_to_outline(c, "down", oy)  # round 4: the hair keeps to v1's outline (spikes, chin locks)
    hairm = c.mat == c.mid("hair")
    skin = c.mat == c.mid("skin")
    for y, x in zip(*np.nonzero(skin)):  # the bangs' shade: 1-2 rows under the hair
        if y >= 2 and (hairm[y - 1, x] or hairm[y - 2, x]) and y < 34 + oy:
            c.tone[y, x] = 3
    features(c, oy, blink)


def features(c, oy, blink=False):
    """v1's expression at 2x: narrow eyes under a thick slanted lid, short brows close above them
    sloping down to the outer side, a nose, cheeks inside the face under the eyes, a 6 x 2 mouth."""
    for ex, rows in ((14, EYE_L), (36, EYE_R)):
        if blink:  # shut tight (hurt): the lid as a thick line bending down, lashes at the outer end
            for j, row in enumerate(EYE_SHUT if ex < 30 else [r[::-1] for r in EYE_SHUT]):
                for i, ch in enumerate(row):
                    if ch != ".":
                        c.dot(ex + i, 33 + oy + j, EYE[ch])
            continue
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch != ".":
                    c.dot(ex + i, 32 + oy + j, EYE[ch])
    # brows (hero round): v1's 2-row band, one row lower than the pilot, sloping down to the outer side
    for xs, y in ((range(17, 22), 30), (range(16, 21), 31)):  # 1 texel of skin from the side hair
        for x in xs:
            c.put(x, y + oy, "hair", 1)
            c.put(57 - x, y + oy, "hair", 1)
    for x, y in ((27, 38), (28, 38), (27, 39), (28, 39)):  # nose: v1's dot at 2x (2 x 2 of shade)
        c.put(x, y + oy, "skin", 2)
    for bx in (18, 41):  # cheeks: inside the face, under the eyes' outer corners
        c.dot(bx, 39 + oy, BLUSH)
        c.dot(bx + 1, 39 + oy, BLUSH)
    for x in range(28, 34):
        c.dot(x, 42 + oy, MOUTH)
        c.dot(x, 43 + oy, MOUTH)


def cloak(c, oy, sway, breath):
    hem = min(93 + oy, 106)  # crouching / kneeling: the cloak lies on the ground
    # outer silhouette (shoulders breathe, hem sways), dips at the folds' grooves
    L = [(12, 46 + oy - breath), (7, 56 + oy), (6, 74 + oy), (5 + sway, hem - 1), (10 + sway, hem + 1),
         (16 + sway, hem), (22 + sway, hem + 1)]
    R = [(41 + sway, hem + 1), (47 + sway, hem), (53 + sway, hem + 1), (58 + sway, hem - 1), (57, 74 + oy),
         (56, 56 + oy), (51, 46 + oy - breath)]
    body = c.m_poly(L + [(25 + sway, hem), (25, 82 + oy), (38, 82 + oy), (38 + sway, hem)] + R +
                    [(44, 43 + oy - breath), (20, 43 + oy - breath)])
    c.fill(body, "cloak", 3)
    # light from the top left: the left panel is base, its outer strip lit; the right panel in shade
    for y, x in zip(*np.nonzero(body)):
        t = 3
        if x >= 32:
            t = 2
        if x < 14 and y < 80 + oy:
            t = 4
        if x > 50:
            t = 2 if y < 70 + oy else 1
        c.tone[y, x] = t
    # 3 large folds a side: a lit ridge (3 wide) and a groove (2 wide) from the shoulder to the hem
    folds = [(17, 53, 11 + sway), (21, 56, 18 + sway), (45, 53, 47 + sway), (49, 55, 54 + sway)]
    for x0, y0, x1 in folds:
        ridge = c.m_line([(x0 - 1, y0 + oy), (x1 - 1.5, hem - 1)], 2.6) & body
        groove = c.m_line([(x0 + 1.5, y0 + 4 + oy), (x1 + 1.5, hem - 1)], 1.8) & body
        for y, x in zip(*np.nonzero(ridge)):
            c.tone[y, x] = min(5, int(c.tone[y, x]) + 1)
        for y, x in zip(*np.nonzero(groove)):
            c.tone[y, x] = max(1, int(c.tone[y, x]) - 1)
    # the hood rolled round the shoulders (lighter, its own soft shape)
    hood = (c.m_ellipse(31.5, 47 + oy - breath, 21, 5.5) & ~c.m_ellipse(31.5, 44.5 + oy - breath, 11, 4)) & body
    c.fill(hood, "cloak")
    c.shade_part(hood, tones=(2, 3, 4, 4, 5), norm=True)
    grooves(c, hood, drop=1)
    # the lining shows inside the front edges below the belt
    lin = c.m_poly([(25, 82 + oy), (27, 82 + oy), (27 + sway, hem), (25 + sway, hem)]) | \
        c.m_poly([(36, 82 + oy), (38, 82 + oy), (38 + sway, hem), (36 + sway, hem)])
    c.fill(lin & body, "lining", 2)
    # gold trim: the hem and the two front edges
    trim_l = c.m_poly([(22, 47 + oy), (25, 47 + oy), (25, 82 + oy), (27 + sway, hem), (25 + sway, hem + 1), (23, 82 + oy)])
    trim_r = c.m_poly([(38, 47 + oy), (41, 47 + oy), (40, 82 + oy), (38 + sway, hem + 1), (36 + sway, hem), (38, 82 + oy)])
    c.fill(trim_l | trim_r, "gold", 3)
    for y, x in zip(*np.nonzero(trim_l | trim_r)):
        left = not (trim_l | trim_r)[y, x - 1]
        c.tone[y, x] = 4 if left else (2 if (trim_l | trim_r)[y, x + 1] is False or not (trim_l | trim_r)[y, x + 1] else 3)
    hemm = np.zeros((H, W), bool)
    for x in range(4, 60):
        ys = np.nonzero(c.mat[:, x] == c.mid("cloak"))[0]
        if len(ys) and ys.max() > 80:
            yb = ys.max()
            for d in range(3):
                hemm[yb - d, x] = True
    c.fill(hemm, "gold")
    for y, x in zip(*np.nonzero(hemm)):
        below = y + 1 < H and hemm[y + 1, x]
        above = hemm[y - 1, x]
        c.tone[y, x] = 4 if not above else (1 if not below else 3)
    return body


def shirt(c, oy, breath):
    col = c.m_poly([(25, 46 + oy - breath), (38, 46 + oy - breath), (38, 82 + oy), (25, 82 + oy)])
    c.fill(col, "shirt")
    c.shade_part(col, tones=(2, 3, 3, 4, 4), norm=True, light=(-0.9, -0.2, 0.4))
    # two soft vertical creases and the neck opening
    for x, y0, y1 in ((28, 58, 66), (34, 57, 80)):
        for y in range(y0 + oy, y1 + oy):
            c.put(x + (1 if y > 70 + oy else 0), y, "shirt", 2)
    neck = c.m_poly([(28, 46 + oy - breath), (35, 46 + oy - breath), (31.5, 51 + oy)])
    c.fill(neck, "skin", 2)
    c.put(31, 47 + oy - breath, "skin", 1)
    c.put(32, 47 + oy - breath, "skin", 1)
    # belt, buckle, pouch
    belt = c.m_rect(25, 68 + oy, 38, 71 + oy)
    c.fill(belt, "leather", 2)
    c.fill(c.m_rect(25, 68 + oy, 38, 68 + oy), "leather", 4)
    c.fill(c.m_rect(25, 71 + oy, 38, 71 + oy), "leather", 1)
    buckle = c.m_rect(29, 67 + oy, 34, 72 + oy)
    c.fill(buckle, "gold", 3)
    c.fill(c.m_rect(31, 69 + oy, 32, 70 + oy), "leather", 1)
    c.put(29, 67 + oy, "gold", 5)
    c.put(30, 67 + oy, "gold", 4)
    c.fill(c.m_rect(34, 67 + oy, 34, 72 + oy) | c.m_rect(29, 72 + oy, 34, 72 + oy), "gold", 1)
    pouch = c.m_rect(34, 72 + oy, 39, 79 + oy)
    c.fill(pouch, "leather", 3)
    c.shade_part(pouch, tones=(2, 3, 3, 4), norm=True)
    c.fill(c.m_rect(34, 72 + oy, 39, 74 + oy), "leather", 4)
    c.fill(c.m_rect(34, 75 + oy, 39, 75 + oy), "leather", 1)
    c.put(36, 74 + oy, "gold", 4)
    # the tunic's hem below the belt
    c.fill(c.m_rect(25, 81 + oy, 33, 82 + oy), "shirt", 2)
    # the pendant: a gold chain V and the star gem
    for k in range(6):
        c.put(27 + k // 2 + (1 if k > 2 else 0), 48 + oy + k, "gold", 3)
        c.put(36 - k // 2 - (1 if k > 2 else 0), 48 + oy + k, "gold", 2)
    gy = 56 + oy
    setting = c.m_poly([(31.5, gy - 4), (36, gy + 0.5), (31.5, gy + 5), (27, gy + 0.5)])
    c.fill(setting, "gold", 2)
    gem = c.m_poly([(31.5, gy - 2.5), (34.5, gy + 0.5), (31.5, gy + 3.5), (28.5, gy + 0.5)])
    c.fill(gem, "gem", 3)
    for y, x in zip(*np.nonzero(gem)):
        c.tone[y, x] = 4 if (x < 31.5 and y < gy + 0.5) else (2 if (x >= 31.5 and y >= gy + 0.5) else 3)
    c.put(30, gy - 1, "gem", 5)
    c.put(31, gy, "gem", 5)
    for (x, y) in ((27, gy + 0), (35, gy + 1), (31, gy + 4)):
        c.put(x, y, "gold", 4 if x < 31 else 1)


def leg(c, x0, top, foot_dy, near=True):
    """Trousers from `top` to the boot, the boot (cuff, shaft, foot, sole). foot_dy < 0 = lifted."""
    bt = 97 + foot_dy  # boot top
    trous = c.m_rect(x0 + 1, top, x0 + 6, bt + 1)
    c.fill(trous, "trousers")
    c.shade_part(trous, tones=(1, 2, 3, 4), norm=True, light=(-0.9, -0.1, 0.4))
    shaft = c.m_poly([(x0 - 1, bt), (x0 + 9, bt), (x0 + 9, bt + 7), (x0 - 1, bt + 7)])
    footm = c.m_poly([(x0 - 1.5, bt + 7), (x0 + 9.5, bt + 7), (x0 + 10, bt + 13), (x0 - 2, bt + 13)])
    c.fill(shaft | footm, "boot")
    c.shade_part(shaft | footm, tones=(1, 2, 3, 3, 4), norm=True)
    cuff = c.m_rect(x0 - 1, bt, x0 + 9, bt + 3)
    c.fill(cuff, "leather", 3)
    c.fill(c.m_rect(x0 - 1, bt, x0 + 9, bt), "leather", 5)
    c.fill(c.m_rect(x0 - 1, bt + 3, x0 + 9, bt + 3), "leather", 1)
    c.put(x0 + 1, bt + 1, "leather", 4)
    # toe cap light and the sole
    c.put(x0 + 1, bt + 9, "boot", 5)
    c.put(x0 + 2, bt + 9, "boot", 4)
    c.fill(c.m_rect(x0 - 2, bt + 13, x0 + 10, bt + 14), "boot", 1)
    if foot_dy < -1:  # lifted: the heel and the sole's underside show
        c.fill(c.m_rect(x0 - 1, bt + 12, x0 + 9, bt + 14), "boot", 1)
        c.fill(c.m_rect(x0 + 5, bt + 13, x0 + 8, bt + 14), "leather", 2)
    if not near:
        c.set_tone(shaft | footm, 2)


def arm(c, side, swing, oy):
    """v1's arm: the upper arm inside the cloak, the forearm in a grey metal GAUNTLET along the body,
    the leather hand below it. side -1: the arm on the image's left. swing: -1 back .. 0 down .. +1
    forward. Forward, the forearm comes in front of the hip (inward, never out from the body); back, it
    goes behind the cloak (drawn first, mostly hidden)."""
    sx = 31.5 + side * 22.0
    ey = 60 + oy
    if swing > 0:  # forward: the hand to the front of the hip
        elbow = (sx - side * 0.5, ey)
        wrist = (sx - side * (2 + 8 * swing), ey + 11 - 1.5 * swing)
    else:  # down / back: along the body, the hand a little back and up
        elbow = (sx, ey)
        wrist = (sx + side * (-0.5 * swing), ey + 11 + 2.5 * swing)
    g = capsule(c, elbow, wrist, 3.7)
    c.fill(g, "shirt")  # v1's gauntlet greys (#4a4640 #a8a296 #e4e0d6), v1's darkness (hdkit.gauntlet)
    wx, wy = wrist
    gauntlet(c, g, elbow, wrist)
    hand_stamp(c, "leather", (wx, wy + 1), side if swing <= 0 else -side, tones=(1, 2, 3, 4, 5))


def arm_off(no_arms, side):
    """no_arms: True (no arms), False, or a set of the sides (-1 image left, +1 image right) left out."""
    return no_arms is True or (not isinstance(no_arms, bool) and side in no_arms)


def frame(oy=0, breath=0, sway=0, lag=0, feet=(0, 0), swing=(0.0, 0.0), no_arms=False, finish=True, blink=False):
    """The front view. no_arms / finish=False: the body only, unfinished (hero_combat.py adds the
    arms and the props on a wider canvas, then finishes)."""
    c = Canvas(W, H, RAMPS)
    # arms swung back go behind the cloak
    for side, s in ((-1, swing[0]), (1, swing[1])):
        if s < -0.45 and not arm_off(no_arms, side):
            arm(c, side, s, oy)
    # legs (the lifted one behind)
    order = sorted(((-1, feet[0]), (1, feet[1])), key=lambda f: f[1])
    for side, dy in order:
        x0 = 19 if side < 0 else 36
        leg(c, x0 + (1 if side < 0 else -1), 80 + oy, dy, near=dy >= -1)
    # the lining between the legs (inside of the cloak), then the cloak and what is in front of it
    c.fill(c.m_rect(29, 82 + oy, 34, 90 + oy) & (c.mat == 0), "lining", 1)
    cloak(c, oy, sway, breath)
    shirt(c, oy, breath)
    for side, s in ((-1, swing[0]), (1, swing[1])):
        if s >= -0.45 and not arm_off(no_arms, side):
            arm(c, side, s, oy)
    head(c, oy, lag, blink)
    if not finish:
        return c
    absorb_cloth_islands(c, limit=5)  # round 4: only 1-5 texel slivers are cleaned; a bigger piece stops the generator
    despeckle(c, loose=("hair", "cloak"))
    edge_band(c, "cloak", 1)
    c.outline()
    c.shadow_band()
    return c


IDLE = [  # hero round 2: the breath as in v1 — head and shoulders 2 texels down, held for 2 frames
    dict(breath=0, swing=(0.0, 0.0)), dict(breath=0, lag=0, swing=(-0.15, -0.15), oy=0),
    dict(breath=0, lag=1, swing=(-0.25, -0.25), oy=2), dict(breath=0, lag=1, swing=(-0.1, -0.1), oy=2)]
WALK = [  # left foot / right foot lift, arm swing (left, right), bob, cloak sway
    dict(feet=(0, -2), swing=(0.3, -0.3), oy=0, sway=0, lag=1),
    dict(feet=(0, -4), swing=(0.9, -0.8), oy=2, sway=1, lag=0),
    dict(feet=(-1, -2), swing=(0.4, -0.6), oy=1, sway=1, lag=1),
    dict(feet=(-2, 0), swing=(-0.3, 0.3), oy=0, sway=0, lag=1),
    dict(feet=(-4, 0), swing=(-0.8, 0.9), oy=2, sway=-1, lag=0),
    dict(feet=(-2, -1), swing=(-0.6, 0.4), oy=1, sway=-1, lag=1),
]


RUN = [  # down: both fists pumping in front of the belly (v1's run), feet lifted high, the body up on the float frames
    dict(feet=(0, -3), swing=(0.8, 0.2), oy=1, sway=1, lag=1),
    dict(feet=(0, -6), swing=(1.0, 0.1), oy=-1, sway=2, lag=0),
    dict(feet=(-2, -4), swing=(0.6, 0.4), oy=0, sway=1, lag=1),
    dict(feet=(-3, 0), swing=(0.2, 0.8), oy=1, sway=-1, lag=1),
    dict(feet=(-6, 0), swing=(0.1, 1.0), oy=-1, sway=-2, lag=0),
    dict(feet=(-4, -2), swing=(0.4, 0.6), oy=0, sway=-1, lag=1),
]

# side (facing right): legs = ((foot dx, heel lift, knee bend) far, near), arms = (far, near) swing
S_IDLE = [dict(breath=0), dict(breath=0, arms=(-0.1, -0.1)), dict(breath=0, lag=1, oy=2, arms=(-0.15, -0.15)),
          dict(breath=0, lag=1, oy=2, arms=(-0.05, -0.05))]
S_WALK = [
    dict(legs=((-8, 0, 0), (8, 2, 1)), arms=(0.7, -0.7), oy=0, sway=1, lag=1),
    dict(legs=((-4, 4, -2), (3, 0, 1)), arms=(0.3, -0.3), oy=2, sway=1, lag=0),
    dict(legs=((2, 6, -3), (-2, 0, 0)), arms=(-0.2, 0.2), oy=1, sway=0, lag=1),
    dict(legs=((8, 2, 1), (-8, 0, 0)), arms=(-0.7, 0.7), oy=0, sway=-1, lag=1),
    dict(legs=((3, 0, 1), (-4, 4, -2)), arms=(-0.3, 0.3), oy=2, sway=-1, lag=0),
    dict(legs=((-2, 0, 0), (2, 6, -3)), arms=(0.2, -0.2), oy=1, sway=0, lag=1),
]
S_RUN = [  # hero round 2: the feet 3 lower, so frames 0 and 3 stand on the bottom row (the float kept)
    dict(legs=((-12, 0, -2), (11, 0, 2)), arms=(0.8, -0.8), oy=1, lean=3, bent=0.8, cloak_fly=0.6, lag=1),
    dict(legs=((-8, 9, -6), (6, 5, 2)), arms=(0.5, -0.4), oy=-1, lean=3, bent=0.8, cloak_fly=0.9, lag=0),
    dict(legs=((2, 10, -6), (-6, 3, 0)), arms=(-0.3, 0.3), oy=0, lean=3, bent=0.8, cloak_fly=0.7, lag=1),
    dict(legs=((11, 0, 2), (-12, 0, -2)), arms=(-0.8, 0.8), oy=1, lean=3, bent=0.8, cloak_fly=0.6, lag=1),
    dict(legs=((6, 5, 2), (-8, 9, -6)), arms=(-0.4, 0.5), oy=-1, lean=3, bent=0.8, cloak_fly=0.9, lag=0),
    dict(legs=((-6, 3, 0), (2, 10, -6)), arms=(0.3, -0.3), oy=0, lean=3, bent=0.8, cloak_fly=0.7, lag=1),
]
# back (facing up): feet = heel lift left / right, arms = swing left / right
B_IDLE = [dict(breath=0), dict(breath=0, lag=1, sway=1), dict(breath=0, lag=1, oy=2), dict(breath=0, lag=0, oy=2, sway=-1)]  # every frame its own
B_WALK = [dict(feet=(0, 3), arms=(0.5, -0.5), oy=0, sway=1, lag=1), dict(feet=(0, 6), arms=(0.8, -0.8), oy=2, sway=1),
          dict(feet=(1, 3), arms=(0.4, -0.4), oy=1, sway=0, lag=1), dict(feet=(3, 0), arms=(-0.5, 0.5), oy=0, sway=-1, lag=1),
          dict(feet=(6, 0), arms=(-0.8, 0.8), oy=2, sway=-1), dict(feet=(3, 1), arms=(-0.4, 0.4), oy=1, sway=0, lag=1)]
B_RUN = [dict(feet=(0, 5), arms=(0.9, -0.9), oy=1, sway=2, lag=1, bent=0.7), dict(feet=(0, 9), arms=(1.0, -1.0), oy=-1, sway=2, bent=0.7),
         dict(feet=(3, 5), arms=(0.4, -0.4), oy=0, sway=1, lag=1, bent=0.7), dict(feet=(5, 0), arms=(-0.9, 0.9), oy=1, sway=-2, lag=1, bent=0.7),
         dict(feet=(9, 0), arms=(-1.0, 1.0), oy=-1, sway=-2, bent=0.7), dict(feet=(5, 3), arms=(-0.4, 0.4), oy=0, sway=-1, lag=1, bent=0.7)]


def frames_for(view, action):
    """The Canvas for every frame of (view, action): view down / right / up."""
    import hero_views as HV
    if view == "down":
        return [frame(**p) for p in {"idle": IDLE, "walk": WALK, "run": RUN}[action]]
    if view == "right":
        return [HV.side_frame(RAMPS, EYE, BLUSH, MOUTH, **p) for p in {"idle": S_IDLE, "walk": S_WALK, "run": S_RUN}[action]]
    return [HV.back_frame(RAMPS, **p) for p in {"idle": B_IDLE, "walk": B_WALK, "run": B_RUN}[action]]


# Facing left is not stored: the game draws facing right mirrored (v1's left frames are exact mirrors
# of its right frames for every action without a held prop).
CUT = []


def _check(cv, name):
    """Hero round 2, the edge check: a texel that is not an outline (tone 0) on the top row or a side
    column means a part is cut by the frame's edge."""
    n = edge_cuts(cv)
    if n:
        CUT.append((name, n))
    st = stray_pieces(cv)
    if st:
        CUT.append((name, "stray pieces", st))
    # hero round 4: counted on the finished frame, where only slivers of 1-5 texels were cleaned up: a
    # cut-off piece of the cloak of 6-40 texels below the shoulders (row 56) stops the generator
    isl = [(n, box) for n, box, _ in cloth_islands(cv, min_size=6, below=56)]
    if isl:
        CUT.append((name, "cloak / gold pieces cut off", isl))


def main():
    out = []
    for view in ("down", "right", "up"):
        for action in ("idle", "walk", "run"):
            for i, cv in enumerate(frames_for(view, action)):
                _check(cv, f"hero.{action}.{view}.{i}")
                out.append(save(cv, os.path.join(OUT, f"hero.{action}.{view}.{i}.png")))
    import hero_combat as HC
    import hero_views as HV
    from PIL import Image
    me = sys.modules[__name__]
    for action in list(HC.COMBAT) + list(HC.REST):
        for view in ("down", "right", "up") + (("left",) if action in HC.OWN_LEFT else ()):
            for i, cv in enumerate(HC.frames_for(action, view, me, HV)):
                _check(cv, f"hero.{action}.{view}.{i}")
                img = cv.image()
                if view == "left":
                    img = img.transpose(Image.FLIP_LEFT_RIGHT)
                out.append(save(img, os.path.join(OUT, f"hero.{action}.{view}.{i}.png")))
    print(f"{len(out)} files")
    if CUT:
        print("edge check:", f"{len(CUT)} frames cut: {CUT}")
        sys.exit(1)
    print("edge check: no frame has a texel other than an outline on its top row or side columns "
          "(the gauntlet's dark grey counted as a cut); no stray piece of 40 texels or fewer; "
          "no piece of the cloak's green / gold of 6-40 texels below row 56 cut off from the cloak "
          "(counted before any fill; only 1-5 texel slivers are cleaned)")


if __name__ == "__main__":
    main()
