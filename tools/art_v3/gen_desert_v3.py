"""v3 production order 7, region 2: the DESERT ground (赤砂の荒野; STYLE.md 6, NAMES.md 1-3), one season.

The desert has no seasons (src/view/groundV2.js SEASONAL holds grass, plains, lake and moss only; the
weather gives the dry region no snow, src/game/env/weather.js), so there is one set of files.

Made the way the plains and the forest passed (gen_ground_v3.py, gen_forest_v3.py), same rules and
formulas, its own drawing:
  1. the base: 8 patterns (a .. h), each a 256 x 256 picture cut into 16 tiles
       desert.sand.v3.<m><r><c>.png                 64 x 64, opaque
     the tile of world tile (tx, ty) = pattern macro_of(tx // 4, ty // 4), row ty % 4, column tx % 4
     (gen_ground_v3.macro_of, unchanged). Red sand: small wind ripples (a lit crest row over a shaded
     trough row, wavy, 5-12 long), ripple fields (3-4 per pattern, may run off the edge), 400 small
     mottles of ripples everywhere, marks at uneven spacing (ripple pairs, pebble clusters of 2-3
     pebbles 3-4 x 3, small wind hollows, dry grass tufts), 2-3 pale wind-smoothed patches. No 1-texel dots.
  2. the flow: the same corner (Wang) scheme and the same key rule (gen_ground_v3.flow_key). Its own
     SHAPE set (grey, body 214 / tip 255):
       desert.sandflow.v3.<bits>.<v>.png
     long wavy ripple crests 2 rows thick, ONE flat grey (255) per crest, the game multiplies them by
     DESERT_FLOW_TINT[kind] (d = the shaded lee of a dune, l = the sunlit windward face).
  3. transitions: the v2 dual-grid rule (desert sand is "dsand" in the v2 priority: above ruin and
     path, below the island sand and every grass):
       desert.sand.v3.edge.<mask>.<v>.png           (mask 1-14, v 0-3; masks 6 / 9: 0-1)
     the inside is a base tile (the forest's round 3 way: the same amount of pattern as the floor),
     cut by v2's curve at 2x, a dry sand lip (lit up / left: bright, shaded: darker) and sand spill
     (2 x 2 / 3 x 2 grains) just over the border onto the lower ground.
Run: python3 tools/art_v3/gen_desert_v3.py [ground|flow|edges|trees|props|all]
"""

import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402

import gen_ground_v3 as G  # noqa: E402  (the passed plains rules, read-only use)
from v3lib import ROOT, Canvas, despeckle, lift_ramp, luma, save  # noqa: E402

OUT = os.path.join(ROOT, "src", "art-release-v3", "terrain")
PATTERNS = G.PATTERNS
SAND = ["#3e1e12", "#82442a", "#954533", "#a8603c", "#b57d48", "#c27e54", "#daa274"]  # v2 ramps.json "dsand"
STRAW = ["#3a2a14", "#6a5028", "#80622e", "#967638", "#ac8c48", "#c0a45a", "#dcc47c"]  # dry grass (as the flora's "dry")
DSTONE = ["#2e2018", "#6a5240", "#7f6050", "#947a60", "#a4916e", "#b49a7c", "#d2bc9e"]  # v2 "dstone"


def _toward(a, b, dl):
    """The colour on the way from a to b whose brightness is dl from a's (the plains' "fine" rule)."""
    lo, hi = 0.0, 1.0
    for _ in range(24):
        t = (lo + hi) / 2
        m = tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))
        if abs(luma(m) - luma(a)) < dl:
            lo = t
        else:
            hi = t
    return tuple(round(a[i] + (b[i] - a[i]) * lo) for i in range(3))


def ramps_for():
    """sand: v2 dsand lifted (STYLE 3.3); fine: the base with its neighbours ~11 apart in brightness
    (dsand steps ~24: drawn with it, the ripples read as grain -- the plains' autumn / winter rule)."""
    s = lift_ramp(SAND)
    fine = list(s)
    fine[2] = _toward(s[3], s[1], 11)
    fine[1] = _toward(s[3], s[1], 18)
    fine[4] = _toward(s[3], s[5], 11)
    fine[5] = _toward(s[3], s[6], 19)
    return {"sand": s, "fine": fine, "stone": lift_ramp(DSTONE), "straw": lift_ramp(STRAW)}


# ------------------------------------------------------------------ base patterns

def ripple(c, x, y, ln, slope, bow, lit=4, shade=2, mask=None, thick=1):
    """One wind ripple: for each column a lit crest texel and the shaded trough texel under it
    (2 rows: reads at 1x as a short line), bowed smoothly (bow texels at the middle). Clipped at the
    picture / mask."""
    k = c.mid("fine")
    for i in range(ln):
        X = int(x) + i
        Y = int(round(y + slope * i - bow * math.sin(math.pi * i / max(1, ln - 1))))
        for dy, t in (((0, lit), (1, shade)) if thick == 1 else ((0, lit), (1, lit), (2, shade))):
            YY = Y + dy
            if 0 <= X < c.w and 0 <= YY < c.h and (mask is None or mask[YY, X]):
                c.mat[YY, X], c.tone[YY, X] = k, t


def ripples_in(c, mask, density, rng, spacing, lmin=5, lmax=12, thick=1):
    """Ripples inside `mask`: rows of ripples `spacing` apart (wavy, broken, each its own length)."""
    ys, xs = np.nonzero(mask)
    if len(ys) == 0:
        return
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    slope = rng.uniform(-0.12, 0.12)
    bow = rng.choice((-1, 1)) * rng.uniform(0.8, 1.8)  # one bow per field: its ripples run parallel
    y = y0 + rng.uniform(0, spacing)
    while y <= y1:
        x = x0 - rng.uniform(0, 6)
        while x <= x1:
            ln = rng.randint(lmin, lmax)
            if rng.random() < density:
                ripple(c, x, y + slope * (x - x0), ln, slope, bow * ln / 12, mask=mask, thick=thick)
            x += ln + rng.randint(3, 8)
        y += spacing + rng.uniform(-1.0, 1.5)


def pebble(c, x, y, w):
    """A pebble w x 3 (w 3-4, rounded top corners): lit top-left, base tone, shaded bottom row, and a
    1-row shadow on the sand under its right part (desert stone)."""
    k, ks = c.mid("stone"), c.mid("fine")
    rows = ((1, w - 1, 5), (0, w, 3), (0, w, 2)) if w >= 3 else ((0, w, 4), (0, w, 2))
    for dy, (a, b, t) in enumerate(rows):
        for dx in range(a, b):
            X, Y = x + dx, y + dy
            if 0 <= X < c.w and 0 <= Y < c.h:
                c.mat[Y, X], c.tone[Y, X] = k, (4 if (dy == 1 and dx == 0) else t)
    for dx in range(1, w + 1):
        X, Y = x + dx, y + len(rows)
        if 0 <= X < c.w and 0 <= Y < c.h and c.mat[Y, X] != k:
            c.mat[Y, X], c.tone[Y, X] = ks, 1


def mark(c, x, y, kind, rng):
    """Desert marks (clipped at the picture's edge):
      0 a ripple 6-12 long; 1 a ripple pair (2 crests 3-4 rows apart, offset)
      2 a pebble cluster: 2-3 pebbles (2 x 2 / 3 x 2), 1-3 texels apart
      3 a wind hollow: a 6 x 3 dip, shaded upper rows, lit lower rim (light from the top left)"""
    x, y = int(x), int(y)
    if kind == 0:
        ripple(c, x, y, rng.randint(6, 12), rng.uniform(-0.15, 0.15), rng.uniform(-1.2, 1.2))
    elif kind == 1:
        s, bw = rng.uniform(-0.12, 0.12), rng.uniform(-1.2, 1.2)
        ripple(c, x, y, rng.randint(8, 12), s, bw)
        ripple(c, x + rng.randint(-3, 3), y + rng.randint(4, 5), rng.randint(6, 10), s, bw)
    elif kind == 2:
        px, py = x, y
        for i in range(rng.randint(2, 3)):
            pebble(c, px, py, rng.choice((3, 4, 4)))
            px += rng.randint(5, 7) * rng.choice((-1, 1))
            py += rng.randint(-2, 3)
    elif kind == 4:  # round 2: a dry grass tuft, 3-4 straw blades 3-6 tall from one root, leaning out
        k = c.mid("straw")
        nb = rng.randint(3, 4)
        for b in range(nb):
            lean = (b - (nb - 1) / 2) * 0.45
            h = rng.randint(3, 6)
            for d in range(h):
                X, Y = int(round(x + b - nb // 2 + lean * d)), y - d
                if 0 <= X < c.w and 0 <= Y < c.h:
                    c.mat[Y, X], c.tone[Y, X] = k, (5 if d >= h - 2 else (3 if d else 2))
    else:
        k = c.mid("fine")
        for dy, row, t in ((0, (1, 6), 2), (1, (0, 7), 2), (2, (1, 6), 4)):
            for dx in range(*row):
                X, Y = x + dx, y + dy
                if 0 <= X < c.w and 0 <= Y < c.h:
                    c.mat[Y, X], c.tone[Y, X] = k, t


def base_pattern(name, n=256):
    """The desert floor: ripple fields (3-4, may run off the edge), 400 small mottles of ripples (up to
    and over the edge), marks at uneven spacing over the whole pattern and 3 texels past it, a top-up
    of marks along the 4 edges (no mark-free border band), no calm tile (the most common texel of a
    64 x 64 tile under 86 %)."""
    seed = 700 + PATTERNS.index(name) * 23
    rng = random.Random(seed)
    c = Canvas(n, n, ramps_for())
    c.fill(np.ones((n, n), bool), "sand", 3)
    # round 2: 2-3 pale wind-smoothed patches (the fine ramp's tone 4, no marks drawn in them later
    # except the ones that run in from outside), each with a 1-row lit upper rim (fine 5)
    pale = np.zeros((n, n), bool)
    for i in range(rng.randint(2, 3)):
        r = rng.uniform(10, 17)
        m = G.blob(n, rng.uniform(0, n), rng.uniform(0, n), r * 1.5, r * rng.uniform(0.45, 0.65), seed + 50 + i)
        pale |= m
    kf = c.mid("fine")
    c.mat[pale], c.tone[pale] = kf, 4
    rim = pale & ~np.roll(pale, 1, axis=0)
    c.tone[rim] = 5
    # round 2 (inspection 1, P2-8): the pale patch is a low smooth rise, not a flat stain: a second lit
    # row along its upper rim, a shaded row on the sand under its lower rim (2 rows under the middle),
    # and 2-3 long ripples across it (lit row over a base-tone row). Its own generator, so the rest of
    # the pattern is drawn as before.
    prng = random.Random(seed * 7 + 3)
    rim2 = pale & np.roll(rim, 1, axis=0) & ~rim
    cols_w = pale.sum(0)
    c.tone[rim2 & (np.roll(cols_w, 0) > 8)[None, :]] = 5
    under = ~pale & np.roll(pale, 1, axis=0)
    c.mat[under], c.tone[under] = kf, 2
    under2 = ~pale & ~under & np.roll(under, 1, axis=0) & (cols_w > 12)[None, :]
    c.mat[under2], c.tone[under2] = kf, 2
    ys, xs = np.nonzero(pale)
    if len(ys):
        for yr in range(int(ys.min()) + 5, int(ys.max()) - 2, prng.randint(5, 7)):
            row = np.nonzero(pale[yr % n])[0]
            if len(row) < 14:
                continue
            x = int(row.min()) + prng.randint(3, 6)
            while x < int(row.max()) - 8:
                ln = prng.randint(9, 16)
                ripple(c, x, yr, ln, 0.0, prng.uniform(0.6, 1.4), lit=5, shade=3, mask=pale)
                x += ln + prng.randint(4, 8)
    for i in range(rng.randint(3, 4)):
        r = rng.uniform(18, 30)
        m = G.blob(n, rng.uniform(0, n), rng.uniform(0, n), r, r * rng.uniform(0.5, 0.8), seed + i)
        ripples_in(c, m, 0.9, rng, rng.uniform(5.5, 6.5), 10, 20, thick=2)  # round 2: thicker field ripples
    for i in range(400):
        r = rng.uniform(3, 7)
        cx, cy = rng.uniform(-r * 0.5, n + r * 0.5), rng.uniform(-r * 0.5, n + r * 0.5)
        m = G.blob(n, cx, cy, r * 1.4, r * rng.uniform(0.5, 0.8), seed * 3 + i) & ~pale
        ripples_in(c, m, 0.35, rng, rng.uniform(4.5, 6.5), 6, 11)

    def put_mark(x, y):
        mark(c, x, y, rng.choices((0, 1, 2, 3, 4), weights=(6, 3, 1, 2, 2))[0], rng)
    for (x, y) in G.scatter(rng, n + 6, 170, 13, 0):
        put_mark(x - 3, y - 3)
    for _ in range(20):
        side = rng.randrange(4)
        a, b = rng.uniform(0, n), rng.uniform(-1, 9)
        put_mark(*{0: (a, b + 4), 1: (a, n - b + 3), 2: (b - 1, a), 3: (n - b, a)}[side])
    for ty in range(n // 64):
        for tx in range(n // 64):
            for _ in range(30):
                rgb = c.rgba()[ty * 64:ty * 64 + 64, tx * 64:tx * 64 + 64, :3].astype(np.int32)
                key = (rgb[..., 0] << 16) | (rgb[..., 1] << 8) | rgb[..., 2]
                if np.unique(key, return_counts=True)[1].max() / 4096 <= 0.84:
                    break
                r = rng.uniform(4, 7)
                m = G.blob(n, tx * 64 + rng.uniform(4, 60), ty * 64 + rng.uniform(4, 60), r * 1.4, r * 0.7, rng.randrange(1 << 20))
                ripples_in(c, m, 0.8, rng, 4.5, 6, 11)
    # the 4 border bands (outer 6 rows / columns): a band under 0.85 of the middle's marks gets more
    # marks inside it (the dart throw and the ripples running right thin out some borders: 0.67 seen)
    def marked():
        k = c.rgba()[..., :3].astype(np.int64)
        k = (k[..., 0] << 16) | (k[..., 1] << 8) | k[..., 2]
        v, cnt = np.unique(k, return_counts=True)
        return k != v[np.argmax(cnt)]
    for side in range(4):
        for _ in range(60):
            mk = marked()
            mid = mk[12:-12, 12:-12].mean()
            band = (mk[:6], mk[-6:], mk[:, :6], mk[:, -6:])[side].mean()
            if band >= 0.88 * mid:
                break
            a, b = rng.uniform(-8, n), rng.uniform(0, 5)
            put_mark(*{0: (a, b), 1: (a, n - 6 + b), 2: (b - 3, a), 3: (n - 9 + b, a)}[side])
    despeckle(c, loose=("fine", "sand"), keep=("straw",))
    return c


_BASE_CACHE = {}


def _base_canvas(name):
    if name not in _BASE_CACHE:
        _BASE_CACHE[name] = base_pattern(name)
    return _BASE_CACHE[name]


def write_ground():
    out = []
    for name in PATTERNS:
        big = _base_canvas(name).image()
        for r in range(4):
            for col in range(4):
                out.append(save(big.crop((col * 64, r * 64, col * 64 + 64, r * 64 + 64)),
                                os.path.join(OUT, f"desert.sand.v3.{name}{r}{col}.png")))
    return out


# ------------------------------------------------------------------ flow shapes (round 2: dunes)
#
# Round 2 (inspection 1, P1-1): the flow layer is drawn as FACES AND CRESTS, not as scattered short
# lines. A flow patch (flow_field > 0.5; the corner scheme, keys, mirrors and variants are unchanged)
# is a sheet of wind-blown sand that ends, on its SOUTH border, in a dune:
#     a slip face in shadow along the border, the crest line over it, the sunlit face over the crest
#     (two flat tones). The dune is as high as the border faces south: it tapers to nothing where the
#     border turns to run north-south (the horns of the crescent).
# The rest of the patch carries long parallel wind ripples (a lit row over a shaded row) that cross
# the tile's west / east sides at fixed rows, so they run on from tile to tile; a full (1111) tile may
# hold a small crescent dune of its own. The light is from the TOP only in this layer (a shape may be
# drawn mirrored left-right by flow_key, so nothing here depends on left / right).
# The pictures stay GREY (the game multiplies them by DESERT_FLOW_TINT[kind]); they now hold 7 greys.

SSET = "desert."
# grey levels (tone index 0-6 of the "shape" material)
T_CORE, T_SHADE, T_RLO, T_FACE2, T_RHI, T_FACE, T_CREST = range(7)
GREYS = (128, 150, 208, 236, 250, 246, 255)
RIPPLE_ROWS = (7, 19, 28, 41, 52)  # the rows where a ripple crosses a west / east side (every tile)
SHADOW_W, CREST_W, FACE_W, FACE2_W = 12.0, 2.0, 8.0, 20.0  # texels at full height


def desert_field(bits, variant):
    """flow_field for the desert set. The straight sets take the step that gives the FIELD the wanted
    width (gen_ground_v3.straight_want): the dune is drawn exactly to the field's border, so the drawn
    width is the field's (the plains measure a scatter of blades instead, _middle_step)."""
    if bits in G.STRAIGHT:
        F0 = G.flow_field(bits, variant, raw=True)
        bump = G._straight_bump(bits)
        return F0 + G._step_for(F0, bump, bits, G.straight_want(variant)) * bump
    return G.flow_field(bits, variant)


def _side_row(state):
    """The row where the patch border crosses a west / east side whose upper corner is in the patch,
    for the side's state (0 / 1): from the side's own profile (the corners' blend, the side's push, the
    shared wobble), so both tiles sharing the side get the same row."""
    v = (np.arange(64) + 0.5) / 64
    shared = G._tile_noise(901)
    shared = (shared + shared[:, ::-1]) / 2
    prof = (1 - v) + (0.26 if state else -0.26) * np.sin(np.pi * v) ** 2 * (1 - 0.5 / 64) + 0.08 * shared[:, 0]
    return int(np.nonzero(prof <= 0.5)[0][0])


def _band(c, k, x, foot, sc, taken, cut=None):
    """One column of a dune, upward from the foot row (the first row under the slip face): the slip
    face in shadow (its upper half darker), the crest line, the lit face in 2 tones. sc 0..1 = height."""
    sw = int(round(SHADOW_W * sc))
    if sw < 2:
        return
    cw = 2 if sc > 0.3 else 1
    fw, f2 = int(round(FACE_W * sc)), int(round(FACE2_W * sc))
    core = max(2, int(round(sw * 0.5)))
    rows = [T_SHADE] * (sw - core) + [T_CORE] * core + [T_CREST] * cw + [T_FACE] * fw + [T_FACE2] * (f2 - fw)
    for j, tone in enumerate(rows):
        y = foot - 1 - j
        if 0 <= y < 64:
            c.mat[y, x], c.tone[y, x] = k, tone
    taken[max(0, foot - len(rows) - 5):min(64, foot + 3), max(0, x - 2):x + 3] = True


def _put(c, k, sel, tone):
    c.mat[sel] = k
    c.tone[sel] = tone


def _crescent(c, k, cx, cy, half, sag, taken):
    """A small crescent dune inside a full tile (v2's dune at this density): a wide flat arch, the
    crest highest left of the middle, the two horns `sag` lower and the right horn longer; the slip
    face under the crest, the lit face (2 tones) over it."""
    for x in range(64):
        t = (x + 0.5 - cx) / (half if x + 0.5 < cx else half * 1.25)
        if abs(t) >= 1:
            continue
        h = (1 - t * t) ** 0.8
        yc = int(round(cy + sag * t * t))
        sw, fw, f2 = int(round(6 * h)), int(round(4 * h)), int(round(9 * h))
        if sw < 2:
            continue
        core = max(2, int(round(sw * 0.5)))
        rows = [T_SHADE] * (sw - core) + [T_CORE] * core + [T_CREST] * (2 if h > 0.35 else 1) + [T_FACE] * fw + [T_FACE2] * (f2 - fw)
        for j, tone in enumerate(rows):
            y = yc + sw - 1 - j
            c.mat[y, x], c.tone[y, x] = k, tone
        taken[max(0, yc - f2 - 7):yc + sw + 4, max(0, x - 3):x + 4] = True


def flow_shape(sset, bits, variant, F=None):
    """One desert flow SHAPE tile (grey on transparent), see the note above."""
    c = Canvas(64, 64, {"shape": [(g, g, g) for g in GREYS]})
    k = c.mid("shape")
    rng = random.Random(G.hsh(int(bits, 2), variant, 23) & 0xFFFFFF)
    if F is None:
        F = desert_field(bits, variant)
    full = bits == "1111"
    taken = np.zeros((64, 64), bool)  # where no ripple may be drawn
    FULL_H = SHADOW_W + CREST_W + FACE2_W + 2
    tl, tr, br, bl = (ch == "1" for ch in bits)
    west, east = tl and not bl, tr and not br  # sides the border crosses facing south: a ridge crosses them
    if west or east:
        cs = G.crossed(bits)
        if len(cs) == 4:
            st = {sd: (variant >> i) & 1 for i, sd in enumerate(G.SIDES)}
            inner = 0
        else:
            st = {cs[0]: variant & 1, cs[1]: (variant >> 1) & 1}
            inner = variant >> 2
        if west and east:  # 1100: the ridge runs through, from the west side's row to the east side's
            y0, y1 = _side_row(st["W"]), _side_row(st["E"])
            ins = F > 0.5
            low = np.array([np.nonzero(ins[:, x])[0].max() + 1 if ins[:, x].any() else 0 for x in range(64)], float)
            low = np.convolve(np.pad(low, 10, mode="edge"), np.ones(21) / 21, "valid")  # the field's own border, smoothed
            s0, s1 = min(1.0, (y0 - 1) / FULL_H), min(1.0, (y1 - 1) / FULL_H)
            for x in range(64):
                t = x / 63.0
                e = (1 - math.cos(math.pi * t)) / 2
                pin = y0 + (y1 - y0) * e
                wgt = 0.7 * math.sin(math.pi * t)  # toward the field's border in the middle, the sides' rows at the sides
                foot = int(round(pin + (low[x] - pin) * wgt))
                sc = min(s0 + (s1 - s0) * e + 0.18 * math.sin(math.pi * t), 1.0, (foot - 1) / FULL_H)
                if inner == 2:  # the ridge sinks (a saddle, or to nothing: two dunes meeting) and rises again
                    gap = 24 + (variant & 3) * 5
                    if variant & 1:  # a saddle
                        g = float(np.clip((abs(x + 0.5 - gap) - 2.0) / 20.0, 0, 1))
                        sc *= 0.42 + 0.58 * g * g * (3 - 2 * g)
                    else:  # two round ends (as the caps') with 4 texels of sand between them
                        tt = x / (gap - 2.0) if x < gap else (63 - x) / (61.0 - gap)
                        sc *= (1 - min(1.0, tt) ** 2) ** 0.8
                _band(c, k, x, foot, sc, taken)
        else:  # the ridge comes in from the west side and ends in this tile: a horn bending south
            y0 = _side_row(st["W"])
            ln = (50, 58, 44)[inner % 3]
            drop = (7.0, 10.0, 5.0)[inner % 3]
            sc0 = min(1.0, (y0 - 1) / FULL_H)
            for x in range(ln):
                t = x / (ln - 1.0)
                foot = int(round(y0 + drop * t * t))
                _band(c, k, x, foot, sc0 * (1 - t * t) ** 0.8, taken)  # a round end, as the crescents'
    elif full and variant == 3:
        _crescent(c, k, 28.0, 27.0, 23.0, 8.0, taken)
    # the ripples: rows fixed on the west / east sides, each waving its own way inside the tile
    ok = (F > 0.62) & ~taken
    for row in RIPPLE_ROWS:
        a1, a2 = rng.uniform(-2.6, 2.6), rng.uniform(-1.4, 1.4)
        style = rng.random()
        gaps = []
        if style < 0.3:  # only the two ends that join the neighbours
            gaps.append((rng.randint(9, 14), rng.randint(49, 54)))
        else:
            for _ in range(rng.randint(1, 2)):
                g0 = rng.randint(9, 46)
                gaps.append((g0, g0 + rng.randint(5, 11)))
        cols = []
        for x in range(64):
            if any(g0 <= x < g1 for g0, g1 in gaps):
                continue
            tt = x / 63.0
            y = int(round(row + a1 * math.sin(math.pi * tt) + a2 * math.sin(2 * math.pi * tt)))
            if 0 <= y < 63 and ok[y, x] and ok[y + 1, x]:
                cols.append((x, y))
        # keep runs of 5 or more columns (no crumbs where the border or a dune cuts a ripple)
        run = []
        for i, (x, y) in enumerate(cols + [(999, 0)]):
            if run and x != run[-1][0] + 1:
                if len(run) >= 5 or run[0][0] == 0 or run[-1][0] == 63:
                    for (p, q) in run:
                        c.mat[q, p], c.tone[q, p] = k, T_RHI
                        c.mat[q + 1, p], c.tone[q + 1, p] = k, T_RLO
                run = []
            run.append((x, y))
    return c


def write_flow():
    out = []
    for bits in G.STORED:
        for v in range(G.n_flow_variants(bits)):
            sh = flow_shape(SSET, bits, v)
            G._drop_small(sh, 6)  # no scraps of 1-6 texels away from the edge
            out.append(save(sh, os.path.join(OUT, f"desert.sandflow.v3.{bits}.{v}.png")))
    return out


def flow_tints():
    """DESERT_FLOW_TINT[kind] (the colour of grey 255, the crest): l a pale high dune, d a low red
    dune. Chosen by eye on the device views; DESERT.md 4 lists the neighbour-step shares at 10 / 12 /
    14 / 15."""
    return {"d": "#c46a46", "l": "#c88454"}


def ground_tile(tx, ty, load=None):
    """One desert tile as the game draws it: the base, then the flow shape (flipped when flow_key says
    so) multiplied by DESERT_FLOW_TINT."""
    from PIL import Image, ImageOps
    load = load or (lambda p: Image.open(p).convert("RGBA"))
    t = load(os.path.join(OUT, f"desert.sand.v3.{G.macro_of(tx // 4, ty // 4)}{ty % 4}{tx % 4}.png")).copy()
    fk = G.flow_key(tx, ty)
    if fk:
        kind, bits, v, flip = fk
        sh = load(os.path.join(OUT, f"desert.sandflow.v3.{bits}.{v}.png"))
        if flip:
            sh = ImageOps.mirror(sh)
        t.alpha_composite(G.tinted(sh, flow_tints()[kind]))
    return t


# ------------------------------------------------------------------ transitions

def _edge_base_pick0(mask, variant):
    h = G.hsh(mask, variant, 79)
    return PATTERNS[h % 8], (h >> 3) % 4, (h >> 5) % 4


def _edge_base_table():
    """The base tile each (mask, v) is cut from. Within one mask the v's take different patterns (the
    forest's round 3 rule, inspection P3-3), and no two (mask, v) take the same tile."""
    keys = [(m, v) for m in range(1, 15) for v in range(2 if m in (6, 9) else 4)]
    used = set()
    out = {}
    for m in range(1, 15):
        pats = []
        for v in range(2 if m in (6, 9) else 4):
            p, r, c = _edge_base_pick0(m, v)
            i = PATTERNS.index(p)
            p = next(PATTERNS[(i + d) % 8] for d in range(8) if PATTERNS[(i + d) % 8] not in pats)
            for d in range(16):
                rr, cc = (r + (c + d) // 4) % 4, (c + d) % 4
                if (p, rr, cc) not in used:
                    r, c = rr, cc
                    break
            used.add((p, r, c))
            pats.append(p)
            out[(m, v)] = (p, r, c)
    assert len(out) == len(keys)
    return out


_EDGE_BASE = _edge_base_table()


def edge_base_pick(mask, variant):
    return _EDGE_BASE[(mask, variant)]


def _dist(m, steps):
    """Distance (4-neighbourhood, up to `steps`) of every texel to the True texels of m (0 on them)."""
    d = np.full(m.shape, 9)
    d[m] = 0
    for step in range(1, steps + 1):
        prev = d < step
        grow = np.zeros_like(prev)
        grow[1:, :] |= prev[:-1, :]
        grow[:-1, :] |= prev[1:, :]
        grow[:, 1:] |= prev[:, :-1]
        grow[:, :-1] |= prev[:, 1:]
        d[grow & (d == 9)] = step
    return d


def edge_overlay(mask, variant):
    """Desert sand over a lower ground (path, ruin floor): the inside is a base tile cut by the v2 curve
    at 2x (gen_ground_v3.edge_inside); a dry lip 2 texels (lit facing up / left: tones 5 / 4 of the
    fine ramp; shaded: 2 / 1... the sand's own darker tones); sand spill: 2 x 2 / 3 x 2 grains of sand
    just over the border, not on the 2 outer rows / columns (neighbouring tiles join)."""
    T = G._v2_transitions()
    F, inside = G.edge_inside(mask, variant)
    c = Canvas(64, 64, ramps_for())
    src, sr, sc = edge_base_pick(mask, variant)
    b = _base_canvas(src)
    bm = b.mat[sr * 64:sr * 64 + 64, sc * 64:sc * 64 + 64]
    bt = b.tone[sr * 64:sr * 64 + 64, sc * 64:sc * 64 + 64]
    remap = np.zeros(len(b.names), np.int16)
    for i, nm in enumerate(b.names):
        if nm is not None:
            remap[i] = c.mid(nm)
    c.mat[:] = remap[bm]
    c.tone[:] = bt
    c.mat[~inside] = 0
    kf, ks = c.mid("fine"), c.mid("sand")
    d = _dist(~inside, 3)
    for y in range(64):
        for x in range(64):
            if not inside[y, x] or d[y, x] > 3:
                continue
            gx, gy = T.gradient(mask, (x + 0.5) / 2 - 0.5, (y + 0.5) / 2 - 0.5)
            lit = (gx + gy) > 0.05
            if lit:  # round 2: the bright dry band of v2's shore (sand tones 5 / 4), 3 texels
                c.mat[y, x] = ks
                c.tone[y, x] = 5 if d[y, x] == 1 else 4
            elif d[y, x] <= 2:
                c.mat[y, x] = kf
                c.tone[y, x] = 1 if d[y, x] == 1 else 2
    do = _dist(inside, 2)
    rng = random.Random(mask * 37 + variant * 11 + 5)
    for y in range(3, 60):
        for x in range(3, 59):
            if inside[y, x] or do[y, x] != 1 or rng.random() > 0.2:
                continue
            w = rng.choice((2, 3))
            for dy in range(2):
                for dx in range(w):
                    X, Y = x + dx, y + dy
                    if 2 <= X < 62 and 2 <= Y < 62 and not inside[Y, X]:
                        c.mat[Y, X] = kf
                        c.tone[Y, X] = 4 if dy == 0 else 2
    G._fill_holes(c)
    c.mat[c.mat == c.mid("grass")] = kf  # _fill_holes fills with "grass": the desert's is the sand
    _drop_cut_pieces(c, inside)
    despeckle(c, loose=("fine", "sand"))
    return c


def _drop_cut_pieces(c, inside):
    """Pieces of the base's marks cut by the curve: a run of 1-3 texels of one colour left against the
    transparent part takes the colour of its inner neighbour (no crumbs on the border)."""
    import gen_forest_v3 as FO
    FO._drop_cut_pieces(c, inside, "summer")


def write_edges():
    out = []
    for mask in range(1, 15):
        for v in range(2 if mask in (6, 9) else 4):
            out.append(save(edge_overlay(mask, v), os.path.join(OUT, f"desert.sand.v3.edge.{mask}.{v}.png")))
    return out


def main(which):
    n = 0
    if which in ("ground", "all"):
        n += len(write_ground())
    if which in ("flow", "all"):
        n += len(write_flow())
    if which in ("edges", "all"):
        n += len(write_edges())
    if which in ("trees", "props", "all"):
        import gen_desert_flora_v3 as FL
        if which in ("trees", "all"):
            n += len(FL.write_trees())
        if which in ("props", "all"):
            n += len(FL.write_props())
    print(f"{n} files")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "all")
