"""Release terrain: trees (obj.tree + its seasons), pines, and the nature objects (rock, bramble,
stump, cactus). Anchor = feet (bottom centre); the last row is the outline where the object meets the
ground. Selective outline (each edge takes the tone 0 of the material it touches). No drawn shadow: the
game draws shadows itself.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from gen_samples import CLUMPS, LEAF_MARKS  # noqa: E402
from release_ground import new_tile, outline, tones, _line  # noqa: E402


# ---------------------------------------------------------------------------------------------
# obj.tree and its seasons. The canopy is the approved sample (gen_samples.tree_sprite), redrawn here
# with hooks so the seasons keep EXACTLY the same shape (guide 3.7: the palette shifts, tone for tone,
# and hand-drawn additions go on top).
# ---------------------------------------------------------------------------------------------
def tree(season=None):
    w, h = 32, 56
    t = new_tile(w, h, base=None, wrap_x=False, wrap_y=False)
    leaf = {"autumn": "autumn.foliage"}.get(season, "leaf")
    for y in range(30, 54):
        for x in range(13, 19):
            t.put(x, y, "bark", 3 if x == 14 else 1 if x >= 17 else 2)
    for x, y0, n in [(15, 37, 3), (16, 43, 2), (14, 48, 2), (17, 40, 2)]:
        for y in range(y0, y0 + n):
            t.put(x, y, "bark", 1)
    for x, y, tn in [(12, 52, 2), (12, 53, 3), (11, 53, 2), (19, 52, 1), (20, 53, 1), (19, 53, 1)]:
        t.put(x, y, "bark", tn)
    owner = {}
    local = {}
    for i, (cx, cy, r) in enumerate(CLUMPS):
        for y in range(int(cy - r) - 1, int(cy + r) + 2):
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                dx, dy = (x + 0.5 - cx) / r, (y + 0.5 - cy) / r
                d = dx * dx + dy * dy
                if d > 1 or not (0 <= x < w and 0 <= y < h):
                    continue
                lit = -(dx * 0.75 + dy)
                base_tone = 2 if i >= 6 else 1 if cy > 20 else 2
                tone = base_tone + (1 if lit > 0.35 else 0) + (1 if lit > 0.9 and d > 0.45 else 0) - (1 if lit < -0.55 else 0)
                if d > 0.72 and dx + dy > 0.35:
                    tone = 1
                t.put(x, y, leaf, max(1, min(4, tone)))
                owner[(x, y)] = i
                local[(x, y)] = (dx, dy, lit)
    for x, y, tn in LEAF_MARKS:
        if (x, y) in owner:
            t.put(x, y, leaf, tn)
            if (x + 1, y) in owner:
                t.put(x + 1, y, leaf, max(1, tn - 1))
    for x in range(13, 19):
        for y in range(30, 35):
            if (x, y) not in owner:
                t.put(x, y, "bark", 1)
    if season == "spring":
        _blossoms(t, owner)
    elif season == "autumn":
        for x, y, s in AUTUMN_FALLEN:
            for k, ch in enumerate(s):
                t.put(x + k, y, "fire", int(ch))
    elif season == "winter":
        _snow_caps(t, owner, local)
    outline(t)
    for x in range(10, 22):
        if t.px[54][x] is not None or t.px[53][x] is not None:
            t.put(x, 55, "bark", 0)
    return t


BLOSSOMS = [  # (x, y): small pink flower clusters (2-3 px) placed by hand over the canopy
    (11, 4), (17, 3), (6, 10), (13, 8), (21, 7), (25, 11), (9, 14), (16, 12), (3, 16), (20, 14), (27, 16),
    (12, 19), (24, 20), (6, 22), (17, 22), (9, 27), (22, 26), (14, 29),
]
BLOSSOM = ["ab", "b."]


def _blossoms(t, owner):
    for x, y in BLOSSOMS:
        v = t.get(x, y)
        if (x, y) not in owner or v is None:
            continue
        lit = v[1] >= 3
        a, b = (4, 3) if lit else (2, 1) if v[1] <= 1 else (3, 2)
        t.stamp(x, y, BLOSSOM, {"a": ("flower.pink", a), "b": ("flower.pink", b)})


AUTUMN_FALLEN = [(6, 53, "12"), (7, 54, "21"), (23, 53, "21"), (25, 54, "12")]  # fallen leaves at the foot


def _snow_caps(t, owner, local):
    """Snow on the top of each leaf clump: where the clump faces up (its upper part), snow tones 2-4;
    the leaves under it keep their tones."""
    for (x, y), i in owner.items():
        dx, dy, lit = local[(x, y)]
        above = owner.get((x, y - 1))
        top_rows = above is None or above != i and CLUMPS[above][1] > CLUMPS[i][1]
        if dy < -0.45 or (top_rows and dy < 0.1):
            tone = 4 if (lit > 0.95 and dy < -0.6) else 3 if dx < 0.25 else 2
            if dx > 0.6:
                tone = 1
            t.put(x, y, "mount.snow", tone)


# ---------------------------------------------------------------------------------------------
# Pines (32 x 60): tiers of needles (forest.pine), lit on the left, shadow under each tier.
#   forest.pine        summer forest pine
#   winter.forest.pine the same shape + snow on each tier
#   mountains.pine     a slimmer alpine fir with heavy snow (the snow mountains are white all year)
# ---------------------------------------------------------------------------------------------
PINE_TIERS = [(1, 14, 6), (8, 24, 9), (16, 34, 12), (25, 44, 14), (35, 52, 15)]  # (top y, bottom y, half width)
DROOP = [0, 1, 2, 1, 0, 0, 1, 2, 2, 1, 0, 1, 2, 1, 0, 0]  # the bottom edge of a tier: drooping branch tips
NEEDLE_MARKS = [  # (x, y, tone): 2 px needle marks (one tier each), hand-placed
    (12, 9, 3), (17, 12, 1), (10, 18, 3), (19, 20, 1), (8, 27, 3), (14, 29, 3), (21, 30, 1),
    (6, 37, 3), (12, 39, 3), (20, 40, 1), (24, 38, 1), (4, 47, 3), (10, 48, 3), (18, 47, 1), (25, 48, 1),
]


def pine(snow=0, slim=False):
    w, h = 32, 60
    t = new_tile(w, h, base=None, wrap_x=False, wrap_y=False)
    cx = 15.5
    for y in range(50, 59):  # trunk
        for x in range(14, 18):
            t.put(x, y, "bark", 3 if x == 14 else 1 if x == 17 else 2)
    tiers = [(a, b, hw * (0.8 if slim else 1.0)) for a, b, hw in PINE_TIERS]
    masks = []
    for ti, (y0, y1, hw) in enumerate(tiers):
        mask = {}
        for y in range(y0, y1 + 3):
            for x in range(w):
                v = (y - y0) / (y1 - y0)
                half = max(1.0, hw * min(1.0, v)) + 0.5
                u = (x + 0.5 - cx) / half
                if abs(u) > 1:
                    continue
                bottom = y1 + DROOP[(x + ti * 5) % len(DROOP)] * (1 if abs(u) > 0.35 else 0)
                if y > bottom:
                    continue
                mask[(x, y)] = (u, v, y >= bottom - 1)
        masks.append(mask)
    for ti in range(len(tiers) - 1, -1, -1):  # the bottom tier first: upper tiers hang over the lower ones
        for (x, y), (u, v, edge) in masks[ti].items():
            tone = 2
            if u < -0.25:
                tone = 3
            if u > 0.45:
                tone = 1
            if edge:
                tone = 2 if u < -0.5 else 1
            t.put(x, y, "forest.pine", tone)
        if ti > 0:  # shadow cast by the tier above onto this one
            for (x, y) in masks[ti - 1]:
                if (x, y + 1) in masks[ti] and (x, y + 1) not in masks[ti - 1]:
                    t.put(x, y + 1, "forest.pine", 1 if (x + 0.5 - cx) > -tiers[ti][2] * 0.5 else 2)
    for ti, (y0, y1, hw) in enumerate(tiers):  # lit tips on the left edge of each tier
        x = int(cx - hw * 0.85)
        t.put(x, y1 - 1, "forest.pine", 4)
        t.put(x + 1, y1 - 1, "forest.pine", 3)
    for x, y, tn in NEEDLE_MARKS:
        if slim:
            x = int(cx + (x - cx) * 0.8)
        if t.get(x, y) and t.get(x + 1, y):
            t.put(x, y, "forest.pine", tn)
            t.put(x + 1, y, "forest.pine", max(1, tn - 1))
    if snow:
        for ti, (y0, y1, hw) in enumerate(tiers):
            m = masks[ti]
            for (x, y), (u, v, edge) in m.items():
                if (x, y - 1) in m:
                    continue  # only the upper surface of the tier
                for k in range(snow):
                    if (x, y + k) not in m or m[(x, y + k)][2]:
                        break
                    tone = 3 if u < -0.2 else 2 if u < 0.45 else 1
                    if k == 0 and u < -0.55 and (x + y) % 3 == 0:
                        tone = 4
                    if k == snow - 1 and snow > 1:
                        tone = max(1, tone - 1)
                    t.put(x, y + k, "mount.snow", tone)
            # snow resting on the drooping tips of the tier's lower edge (lit side and middle)
            for (x, y), (u, v, edge) in m.items():
                if edge and (x, y - 1) in m and not m[(x, y - 1)][2] and u < 0.3 and (x + ti) % 4 == 0:
                    t.put(x, y - 1, "mount.snow", 3 if u < 0 else 2)
    outline(t)
    for x in range(12, 20):
        if t.px[58][x] is not None:
            t.put(x, 59, "bark", 0)
    return t


# ---------------------------------------------------------------------------------------------
# Nature objects.
# ---------------------------------------------------------------------------------------------
def _blob(t, mat, parts, base_tone=2, w=None, h=None, lit3=0.3):
    """Fill rounded masses lit from the top left; parts = [(cx, cy, rx, ry)] back to front."""
    w, h = w or t.w, h or t.h
    owner = {}
    for i, (cx, cy, rx, ry) in enumerate(parts):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
                d = dx * dx + dy * dy
                if d > 1 or not (0 <= x < w and 0 <= y < h):
                    continue
                lit = -(dx * 0.75 + dy)
                tone = base_tone + (1 if lit > lit3 else 0) + (1 if lit > 0.95 and d > 0.4 else 0) - (1 if lit < -0.45 else 0)
                if d > 0.75 and dx + dy > 0.4:
                    tone = 1
                t.put(x, y, mat, max(1, min(4, tone)))
                owner[(x, y)] = i
    return owner


def rock():
    """obj.rock 32 x 28: a boulder (pebble) with a facet crack and a tuft of grass at its foot."""
    t = new_tile(32, 28, base=None, wrap_x=False, wrap_y=False)
    _blob(t, "pebble", [(19.5, 18.5, 9, 8), (14, 15.5, 12.5, 11)], lit3=0.6)
    for x, y in [(11, 9), (12, 10), (12, 11), (13, 12), (13, 13), (14, 14), (14, 15)]:  # facet edge
        if t.get(x, y):
            t.put(x, y, "pebble", 1)
            if t.get(x - 1, y):
                t.put(x - 1, y, "pebble", 3)
    for x, y in [(21, 16), (22, 17), (23, 18), (23, 19)]:  # a crack on the shaded side
        if t.get(x, y):
            t.put(x, y, "pebble", 0 if y > 17 else 1)
    t.stamp(3, 21, ["3.4.", "31.3", "1.11"], tones("grass"))
    outline(t)
    for x in range(6, 26):  # the rock sits on the ground: a flat dark base row under it
        if t.px[26][x] is not None:
            t.put(x, 27, "pebble", 0)
    return t


def bramble():
    """obj.bramble 32 x 24: a thorny bush (forest.swamp leaves, tree.bark stems with thorns, berries)."""
    t = new_tile(32, 24, base=None, wrap_x=False, wrap_y=False)
    owner = _blob(t, "forest.swamp", [(8, 15, 7, 7), (24, 15, 7, 7), (16, 11, 9, 8), (16, 17, 10, 5.5)], w=32, h=23)
    for pts in ([(3, 18), (8, 12), (14, 9), (19, 6)], [(28, 18), (24, 11), (18, 8), (12, 5)], [(5, 9), (11, 14), (17, 17), (25, 19)]):
        _line(t, pts, "tree.bark", 3, under=1)
    for x, y in [(2, 7), (30, 7), (9, 2), (23, 2), (1, 13), (31, 13)]:  # thorny shoots poking out (2-3 px)
        dx = 1 if x < 16 else -1
        t.put(x, y, "tree.bark", 4)
        t.put(x + dx, y + 1, "tree.bark", 3)
        t.put(x + 2 * dx, y + 2, "tree.bark", 1)
    for x, y in [(7, 10), (14, 14), (21, 9), (25, 16), (11, 18)]:  # thorns on the stems: lit spikes
        if (x, y) in owner:
            t.put(x, y, "tree.bark", 4)
            t.put(x + 1, y - 1, "tree.bark", 3)
    for x, y in [(19, 13), (9, 15)]:  # berries (2x2)
        t.stamp(x, y, ["ab", "bc"], {"a": ("flower.pink", 3), "b": ("flower.pink", 1), "c": ("flower.pink", 0)})
    t.px = [[v if y < 23 else None for v in row] for y, row in enumerate(t.px)]
    outline(t)
    _sit(t)
    return t


def _sit(t):
    """Move the art down so its lowest row is the sprite's last row (feet anchor = where it meets the ground)."""
    low = max(y for y in range(t.h) if any(t.px[y]))
    d = t.h - 1 - low
    if d:
        t.px = [[None] * t.w for _ in range(d)] + t.px[:t.h - d]


def stump():
    """obj.stump 28 x 16: a cut stump. The top shows the rings (wood), the sides the bark."""
    t = new_tile(28, 16, base=None, wrap_x=False, wrap_y=False)
    cx = 13.5
    for y in range(5, 14):  # the side (bark), lit on the left
        for x in range(5, 23):
            u = (x + 0.5 - cx) / 9
            tone = 3 if u < -0.6 else 2 if u < 0.4 else 1
            t.put(x, y, "bark", tone)
    for x, y0, n in [(8, 7, 4), (13, 8, 4), (18, 7, 3)]:  # bark furrows
        for k in range(n):
            t.put(x, y0 + k, "bark", 1)
    for x, y, s in [(3, 11, "23"), (2, 12, "321"), (21, 11, "21"), (22, 12, "211"), (12, 13, "21")]:  # roots
        for k, ch in enumerate(s):
            t.put(x + k, y, "bark", int(ch))
    for y in range(1, 9):  # the cut top: an ellipse of wood rings
        for x in range(4, 24):
            dx, dy = (x + 0.5 - cx) / 9.5, (y + 0.5 - 5) / 4
            d = dx * dx + dy * dy
            if d > 1:
                continue
            tone = 3
            if 0.3 < d < 0.5:
                tone = 2
            if d < 0.08:
                tone = 2
            if d > 0.8:
                tone = 2 if dy < 0 else 1
            t.put(x, y, "wood", tone)
    t.put(9, 3, "wood", 4)
    t.put(10, 3, "wood", 4)
    for x, y in [(15, 5), (16, 6)]:  # a radial crack
        t.put(x, y, "wood", 1)
    outline(t)
    _sit(t)
    return t


def cactus():
    """obj.cactus 24 x 40: a ribbed column with two arms (new ramp `cactus`), spines, a bud on top."""
    t = new_tile(24, 40, base=None, wrap_x=False, wrap_y=False)

    def column(x0, x1, y0, y1):
        wd = x1 - x0 + 1
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if y == y0 and x in (x0, x1):
                    continue  # rounded top
                rx = x - x0
                tone = 3 if rx == 0 else 2
                if rx == 1 and wd > 4:
                    tone = 3
                if rx == wd - 1:
                    tone = 1
                if wd > 4 and rx == wd // 2:
                    tone = 1  # rib groove
                t.put(x, y, "cactus", tone)

    column(3, 6, 13, 24)  # left arm (upright part)
    for y in range(22, 26):  # left arm elbow
        for x in range(3, 10):
            t.put(x, y, "cactus", 2 if y < 25 else 1)
    column(17, 20, 9, 21)  # right arm
    for y in range(18, 22):
        for x in range(14, 21):
            t.put(x, y, "cactus", 2 if y < 21 else 1)
    column(8, 15, 3, 38)  # main column
    t.put(3, 13, "cactus", 4)
    t.put(17, 9, "cactus", 4)
    t.put(9, 4, "cactus", 4)
    t.put(10, 4, "cactus", 4)
    for x, y in [(9, 9), (9, 17), (9, 26), (9, 33), (13, 12), (13, 22), (13, 30), (4, 16), (18, 13)]:  # spines (2 px)
        t.put(x, y, "desert.stone", 4)
        t.put(x + 1, y + 1, "desert.stone", 3)
    t.stamp(10, 1, [".ab.", "abba"], {"a": ("flower.pink", 3), "b": ("flower.pink", 2)})  # a bud on top
    for x in range(6, 18):  # sand heaped at the foot
        t.put(x, 38, "desert.sand", 3 if x < 9 else 2 if x < 15 else 1)
    outline(t)
    for x in range(5, 19):
        if t.px[38][x] is not None:
            t.put(x, 39, "desert.sand", 0)
    return t
