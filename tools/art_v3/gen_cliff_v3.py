"""v3 steps and cliffs (STYLE.md 6 "まだ": the step rims, step shadows and cliff faces), drawn by hand
at density 4 (no v2 picture is scaled). Round 1: the DESERT (DESERT.md 7).

The engine's rules are v2's, unchanged (docs/art-release-v2/terrain/NAMES.md 2b and 4):
  * cliff faces: `face.<mat>.<top|mid><-base?>.<4|8><.v1?>` stacked down the south side of a raised cell
    in bands of 8 / 4 game px (gameView.addFace); the variant from the cell's hash (terrainArt.faceVariant:
    plateau materials sand / desert / path have "" and ".v1"). The same KEYS as today at density 4:
    64 x 32 (.8) and 64 x 16 (.4).
  * step rims: `<prefix>.v3.step.<mask>.<v>` over a raised cell's surface (mask = 1 lowerNorth +
    2 lowerEast + 4 lowerWest, v = hash(tx + 5, ty + 9) % 2), the shadow `<prefix>.v3.step.shade.<v>` on
    the lower cell east of it (v = hash(tx + 6, ty + 9) % 2), the inner corners
    `<prefix>.v3.step.inner.<ne|nw>`. 64 x 64, anchor top-left. (".v3." as the v3 ground keys: the
    same scheme as v2's `<prefix>.step.*`.)
Joins: every wave here has a period of 64 texels along the side (the tile's width), and a variant only
adds a bump that is 0 at the tile's two ends, so a rim / face joins its neighbours whatever their
variants (v2's rule: the same outermost columns). Face bands: the first and last 3 rows of a band are
plain rock, so bands stack in any order.
Run: python3 tools/art_v3/gen_cliff_v3.py [desert]
"""

import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402

import gen_desert_v3 as D  # noqa: E402
from v3lib import ROOT, Canvas, lift_ramp, save  # noqa: E402

OUT = os.path.join(ROOT, "src", "art-release-v3", "terrain")
TAU = 2 * math.pi

MATERIALS = {
    # face material: rock ramp (7 tones), lip / foot ramp (the ground above / below), seed
    "desert": dict(rock=["#2e1814", "#5a2e26", "#6c3a30", "#80483a", "#965a46", "#ac7058", "#c8907a"],
                   seed=11),
}


def wave(t, seed, amp=(1.0, 0.6), variant=0, bump=0.0):
    """A periodic profile over t in texels (period 64): two sines with phases from the seed, plus the
    variant's bump sin(pi t / 64)^2 (0 at both ends of the tile)."""
    rng = random.Random(seed)
    p1, p2 = rng.uniform(0, TAU), rng.uniform(0, TAU)
    k2 = rng.choice((2, 3))
    v = amp[0] * math.sin(TAU * t / 64 + p1) + amp[1] * math.sin(TAU * k2 * t / 64 + p2)
    if variant and 3 <= t <= 60:  # round 4: exactly 0 in the outer 3 columns (no rounding flip at the ends)
        v += bump * math.sin(math.pi * t / 64) ** 2
    return v


def face_canvas(h):
    r = D.ramps_for()
    return Canvas(64, 4 * h, {"rock": lift_ramp(MATERIALS["desert"]["rock"]), "sand": r["sand"], "fine": r["fine"]})


FACE_VARIANTS = 3  # round 4: 3 variants for every face material (".v1", ".v2"); see DESERT.md 9 (engine)


def band_body(c, k, H, part, variant, seed, style):
    """The body of one face band (round 4, inspection P1-4: no lattice when bands stack):
      * the base tone, with 1-2 faint seams (one row a tone darker) across the whole tile on waves that
        every part and variant shares (the ends meet any neighbour tile; no pinch at the tile's ends)
      * lenses: 1-3 layers that thicken and thin out INSIDE the tile (x 4..60), each part / variant its
        own places and sizes (sandstone: a lighter lens, lit top row, shaded underside; soil: packed
        darker soil, its top row a little lighter); a lens never reaches the band's top / bottom 2 rows
      * joints: 1-2 per band, partial height, own columns per part / variant
      * weathering: pits (3 x 2: dark top, shaded row, a lit lip under) and, on sandstone, dark streaks
        (2 wide) running down from a lens
    style "sandstone" (desert) / "soil" (earth)."""
    rng = random.Random(seed)
    big = H > 16
    # round 4c: strata across the whole tile. A middle layer between two edges on waves every part and
    # variant shares (the ends meet any neighbour tile); each part / variant moves the two edges by its
    # own bumps in the middle of the tile (0 at the ends), independently, so the layer is thicker,
    # thinner, higher or lower from band to band. Sandstone: the layer a tone lighter (a lit top row,
    # a shaded row under it); soil: a tone darker (packed soil, its top row in shadow). An 8-px band also
    # has a thin dark seam lower down. Then 1-2 small lenses of the other kind inside the tile.
    pi = {"top": 1, "mid": 2, "top-base": 3, "mid-base": 4}[part]
    ba = (0.0, 5.0, -4.0)[variant] + (0.8, -0.8, 1.2, -1.2)[pi - 1]
    bb = (0.0, -3.0, 5.0)[variant] + (-0.6, 0.9, -1.0, 0.7)[pi - 1]
    y_a, y_b = (9, 18) if big else (5, 10)
    lay_t = 4 if style == "sandstone" else 2
    for x in range(64):
        ya = int(round(y_a + 1.6 * wave(x, 91, (1.0, 0.6), 1, ba)))
        yb = int(round(y_b + 1.8 * wave(x, 92, (1.0, 0.5), 1, bb)))
        ya = max(2, min(H - 8 if big else H - 6, ya))
        yb = min(H - 6 if big else H - 3, max(ya + 2, yb))
        for y in range(ya, yb):
            c.tone[y, x] = lay_t
        c.tone[ya, x] = (lay_t + 1) if style == "sandstone" else 1
        c.tone[yb, x] = 1 if style == "sandstone" else 3
        if style == "sandstone" and yb + 1 < H - 2:
            c.tone[yb + 1, x] = 2
        if big:
            yc = int(round(26 + 1.2 * wave(x, 93, (1.0, 0.6), 1, -ba * 0.5)))
            yc = min(H - 4, max(yb + 3, yc))
            c.tone[yc, x] = 2
    # thin bedding laminations in the plain rock / soil: 1-row lines on shared waves, alternately a tone
    # darker and a tone lighter, broken in 1-3 places of each part / variant's own
    for li, y0 in enumerate((4, 13, 22, 29) if big else (3, 12)):
        gaps = []
        for _ in range(rng.randint(1, 3)):  # (inside x 4..60: the tile's ends stay the same for every variant)
            g0 = rng.randint(4, 52)
            gaps.append((g0, min(60, g0 + rng.randint(4, 12))))
        lt = 2 if li % 2 == 0 else 4
        for x in range(64):
            if any(g0 <= x < g1 for g0, g1 in gaps):
                continue
            y = int(round(y0 + 1.0 * wave(x, 97 + li, (1.0, 0.6), 1, (ba - bb) * 0.3)))
            if 2 <= y < H - 2 and c.tone[y, x] == 3:
                c.tone[y, x] = lt
    for i in range(rng.randint(1, 2) if big else 1):  # small lenses of the other kind
        ln = rng.randint(14, 30)
        x0 = rng.randint(4, 60 - ln)
        th = rng.uniform(3.0, 5.0)
        yc = rng.uniform(3 + th / 2, H - 3 - th / 2)
        kind = -1 if style == "sandstone" else 1
        for x in range(x0, x0 + ln):
            half = th * math.sin(math.pi * (x - x0) / ln) ** 0.6 / 2
            if half < 1.0:
                continue
            for y in range(max(2, int(round(yc - half))), min(H - 3, int(round(yc + half)))):
                c.tone[y, x] = 3 + kind
    lenses = []
    for n_ in range(1 + (rng.random() < 0.6)):  # partial joints
        x = rng.randint(6, 56)
        y0 = rng.randint(2, H // 2)
        y1 = rng.randint(min(H - 3, y0 + 5), H - 3)
        for y in range(y0, y1):
            xx = x + (1 if ((y + n_ * 3) // 7) % 2 else 0)
            c.tone[y, xx] = 1
            if c.tone[y, xx + 1] in (2, 3):
                c.tone[y, xx + 1] = c.tone[y, xx + 1] + 1
    for _ in range(rng.randint(3, 6) if big else rng.randint(1, 3)):  # pits
        x, y = rng.randint(4, 56), rng.randint(3, H - 6)
        for dx in range(3):
            c.tone[y, x + dx] = 1
            c.tone[y + 1, x + dx] = 2
            c.tone[y + 2, x + dx] = min(5, max(int(c.tone[y + 2, x + dx]), 4))
    if style == "sandstone":
        for _ in range(rng.randint(1, 2)):  # dark streaks down from the layer
            x = rng.randint(6, 54)
            ys = np.nonzero(c.tone[:, x] == 1)[0]
            y0 = int(ys[0]) if len(ys) else H // 2
            for y in range(y0 + 2, min(H - 3, y0 + 2 + rng.randint(4, 9))):
                for dx in (0, 1):
                    if c.tone[y, x + dx] >= 3:
                        c.tone[y, x + dx] = 2


JOINTS = {0: (21, 47), 1: (14, 38)}  # round 3: 2 vertical joints per tile, by variant (never at the ends)


def face(mat, part, h, variant):
    """One face band (64 x 4h) of a sandstone mesa: blocks between vertical joints (the joint a dark
    column, the block left of it ends in a shaded column, the block right of it starts with a lit
    column: light from the left; the joints run from the band's top to its bottom, so stacked bands
    give continuous joints), one wavy ledge in an 8-px band (a shaded seam under a lit row, its height
    per part / variant), short fractures and cracks, a sand lip with drips on a top band, a sand pile
    at the foot of a base band. The first / last rows of a band hold only the blocks, so bands stack."""
    H = 4 * h
    top, base = part.startswith("top"), part.endswith("base")
    c = face_canvas(h)
    pi = {"top": 1, "mid": 2, "top-base": 3, "mid-base": 4}[part]
    seed = MATERIALS[mat]["seed"] * 1000 + pi * 10 + h + 5 * variant
    rng = random.Random(seed + 1)
    kr, kf = c.mid("rock"), c.mid("fine")
    c.mat[:, :], c.tone[:, :] = kr, 3
    band_body(c, kr, H, part, variant, seed, "sandstone")
    bump = (1.0, -1.4, 1.8, -1.0)[pi - 1] + (0.0, 2.6, -2.6)[variant]
    if top:  # the sand lip: 5-8 rows of the plateau's sand, lit top rows, a shadow under it on the rock
        for x in range(64):
            L = int(round(8 + 1.4 * wave(x, 31, (1.0, 0.6), 1, bump * 0.7)))
            L = max(7, min(10, L))
            for y in range(L):
                c.mat[y, x] = kf
                c.tone[y, x] = 6 if y == 0 else (5 if y < 3 else (4 if y < L - 1 else 2))
            c.mat[L, x], c.tone[L, x] = kr, 1
            c.mat[L + 1, x], c.tone[L + 1, x] = kr, 1
            if c.tone[L + 2, x] == 3:
                c.tone[L + 2, x] = 2
        for _ in range(rng.randint(2, 3)):  # drips: sand run down the rock, 2 wide, 3-7 long
            x = rng.randint(4, 57)
            y0 = int(np.argmax(c.mat[:, x] == kr))
            for k in range(rng.randint(4, 9)):
                if y0 + k < H - 3:
                    for dx in (0, 1):
                        c.mat[y0 + k, x + dx], c.tone[y0 + k, x + dx] = kf, (4 if dx == 0 else 3)
    if base:  # the foot: the rock darkens in its last rows, a sand pile against it (lit top)
        for x in range(64):
            S = int(round(5 + 1.8 * wave(x, 53, (1.0, 0.7), 1, bump)))
            S = max(3, min(9, S))
            for y in range(H - S, H):
                c.mat[y, x], c.tone[y, x] = kf, (5 if y == H - S else (4 if y < H - S + 3 else 3))
            for y in range(max(0, H - S - 3), H - S):
                if c.mat[y, x] == kr:
                    c.tone[y, x] = min(int(c.tone[y, x]), 2 if y < H - S - 1 else 1)
    return c


def write_faces(mat="desert"):
    out = []
    for part in ("top", "mid", "top-base", "mid-base"):
        for h in (8, 4):
            for v in range(FACE_VARIANTS):
                name = f"face.{mat}.{part}.{h}{('', '.v1', '.v2')[v]}.png"
                out.append(save(face(mat, part, h, v), os.path.join(OUT, name)))
    return out


# ------------------------------------------------------------------ step rims (seen from above)

SIDE_SEED = {"N": 101, "E": 202, "W": 303}


def rim_profile(side, t, variant):
    """(outline depth, rim depth) at position t along a side: the outline 0 or 2-5 texels (it swells,
    thins and breaks off), the rim inside it 2-4 texels. Period 64, the variant's bump 0 at the ends."""
    d = 3.2 + 1.3 * wave(t, SIDE_SEED[side], (1.0, 0.6), variant, 1.4)
    d = max(2, min(5, int(round(d))))  # round 2: no breaks (they read as a dashed line)
    r = int(round(3 + 0.9 * wave(t, SIDE_SEED[side] + 9, (1.0, 0.5), variant, -1.0)))
    return d, max(2, min(4, r))


def rim_canvas():
    r = D.ramps_for()
    return Canvas(64, 64, {"sand": r["sand"], "fine": r["fine"]})


def draw_side(c, side, variant, limit=None):
    """Draw one side's outline + rim. limit(x, y) -> bool restricts the texels (inner corners)."""
    ks, kf = c.mid("sand"), c.mid("fine")
    for t in range(64):
        d, r = rim_profile(side, t, variant)
        for k in range(d + r):
            x, y = {"N": (t, k), "E": (63 - k, t), "W": (k, t)}[side]
            if limit and not limit(x, y):
                continue
            if k < d:
                c.mat[y, x], c.tone[y, x] = ks, 0 if k < d - 1 else 1  # the dark edge
            elif side == "E":
                c.mat[y, x], c.tone[y, x] = ks, 1 if k == d else 2  # the shaded east rim
            else:
                c.mat[y, x], c.tone[y, x] = ks, 6 if k == d else 5  # the lit north / west rim (round 2: brighter)


def step(mask, variant):
    c = rim_canvas()
    for bit, side in ((1, "N"), (2, "E"), (4, "W")):
        if mask & bit:
            draw_side(c, side, variant)
    return c


def inner(corner):
    """The inner corner (round 8 of v2): the turn between the north rim of the side neighbour and the
    east / west rim of the north neighbour. Both run on with the same profiles (period 64: the value at
    this tile's corner is the neighbours' value at their ends); here only the square where they meet."""
    c = rim_canvas()
    dn, rn = rim_profile("N", 63 if corner == "ne" else 0, 0)
    side = "E" if corner == "ne" else "W"
    ds, rs = rim_profile(side, 0, 0)
    wN, wS = max(2, dn + rn), max(2, ds + rs)
    if corner == "ne":
        draw_side(c, "E", 0, limit=lambda x, y: y < wN)
        draw_side(c, "N", 0, limit=lambda x, y: x >= 64 - wS)
    else:
        draw_side(c, "W", 0, limit=lambda x, y: y < wN)
        draw_side(c, "N", 0, limit=lambda x, y: x < wS)
    return c


def shade(variant):
    """The shadow on the lower cell east of a step: from its west side, 6-15 texels wide with a wavy
    edge (period 64 down the side), the sand's tone 2 (24 darker than the ground's main colour), its
    outer 1-2 texels the fine ramp's tone 1."""
    c = rim_canvas()
    ks, kf = c.mid("sand"), c.mid("fine")
    for y in range(64):
        w = int(round(10 + 3.5 * wave(y, 404, (1.0, 0.5), variant, 2.5)))
        w = max(6, min(15, w))
        for x in range(w):
            c.mat[y, x], c.tone[y, x] = (ks, 2) if x < w - 2 else (kf, 1)
    return c


def write_steps(prefix="desert.sand"):
    out = []
    for mask in range(1, 8):
        for v in (0, 1):
            out.append(save(step(mask, v), os.path.join(OUT, f"{prefix}.v3.step.{mask}.{v}.png")))
    for v in (0, 1):
        out.append(save(shade(v), os.path.join(OUT, f"{prefix}.v3.step.shade.{v}.png")))
    for corner in ("ne", "nw"):
        out.append(save(inner(corner), os.path.join(OUT, f"{prefix}.v3.step.inner.{corner}.png")))
    return out




# ================================================================== round 2: the earth faces and the
# plains / forest rims (DESERT.md 8). The desert functions above are unchanged (their files keep their md5).

import gen_forest_v3 as FO  # noqa: E402
import gen_ground_v3 as GR  # noqa: E402
from v3lib import luma  # noqa: E402

EARTH = ["#1c140e", "#3a2a1c", "#483023", "#57402a", "#665332", "#74583a", "#927450"]  # v2 "earth"
PEBBLE = ["#24232a", "#56545c", "#6a686e", "#807c80", "#948f8f", "#a8a29e", "#d4ccc2"]  # v2 "pebble"
ROOT_R = ["#1e1008", "#3e2414", "#4e281b", "#5e3a22", "#6e502a", "#7e5432", "#9c7048"]  # v2 "bark"
SEASONS = ("summer", "autumn", "winter")
SPRE = {"summer": "", "autumn": "autumn.", "winter": "winter."}


def lip_ramp(season):
    """The lip of an earth face: the plains grass of the season (winter: the snow)."""
    return GR.ramps_for(season)["grass"]


def earth_canvas(h, season):
    return Canvas(64, 4 * h, {"earth": lift_ramp(EARTH), "pebble": lift_ramp(PEBBLE), "root": lift_ramp(ROOT_R),
                              "lip": lip_ramp(season)})


def earth_face(season, part, h, variant):
    """One earth face band (64 x 4h) under a grass-topped cell: soil lumps split by wavering cracks
    (a dark crack, the lump under / right of it lit along it: light from the top left), a few stones
    set in the soil (4 x 3, lit top), on .v2 roots hanging from the lip; a top band has the season's lip
    (grass: 6-9 rows, blade tips hanging 0-3 texels below its edge; autumn grass; winter: a rounded
    snow lip) and its shadow on the soil; a base band darkens in its last rows. The waves of the lip and
    the foot share one seed for every part / variant / season (they differ by bumps that are 0 at the
    tile ends), the cracks keep 3 texels from the tile's sides and 2 rows from the band's top / bottom."""
    H = 4 * h
    top, base = part.startswith("top"), part.endswith("base")
    c = earth_canvas(h, season)
    pi = {"top": 1, "mid": 2, "top-base": 3, "mid-base": 4}[part]
    seed = 5000 + pi * 10 + h + 5 * variant
    rng = random.Random(seed)
    ke, kp, kr, kl = c.mid("earth"), c.mid("pebble"), c.mid("root"), c.mid("lip")
    c.mat[:, :], c.tone[:, :] = ke, 3
    bump = (1.0, -1.0, 1.6, -1.6)[pi - 1] + (0.0, 2.0, -2.0)[variant]
    band_body(c, ke, H, part, variant, seed, "soil")
    n_st = (1, 2, 1)[variant]  # round 4: mid bands too (the engine proposal gives stacked bands other variants)
    for _ in range(n_st):  # stones set in the soil
        x, y = rng.randint(5, 54), rng.randint(4, H - 7)
        for dy, (a, b, t) in enumerate(((1, 3, 5), (0, 4, 3), (0, 4, 2))):
            for dx in range(a, b):
                c.mat[y + dy, x + dx], c.tone[y + dy, x + dx] = kp, (4 if (dy == 1 and dx == 0) else t)
        for dx in range(1, 5):
            if c.mat[y + 3, x + dx] == ke:
                c.tone[y + 3, x + dx] = 1
    if top:
        winter = season == "winter"
        for x in range(64):
            L = int(round((10 if winter else 11) + 1.5 * wave(x, 61, (1.0, 0.6), 1, bump * 0.6)))
            L = max(9, min(13, L)) if H > 16 else max(7, min(9, L - 3))  # (a 4-px band: a thinner lip)
            hang = 0 if winter else (GR.hsh(x, 3, 71) % 6 if GR.hsh(x // 2, 1, 72) % 3 else 0)
            hang = min(hang, H - 3 - L)
            for y in range(L + hang):
                c.mat[y, x] = kl
                if winter:
                    c.tone[y, x] = 6 if y < 2 else (5 if y < L - 2 else (4 if y < L - 1 else 2))
                else:
                    c.tone[y, x] = 5 if y < 2 else (4 if y < 5 else (3 if y < L - 2 else 2))
            for y in range(L + hang, min(H - 2, L + hang + 2)):
                if c.mat[y, x] == ke:
                    c.tone[y, x] = 1 if y == L + hang else 2
        if variant == 2:  # roots hanging from the lip: 2 wide, 7-14 long, wavering
            for x in (rng.randint(8, 24), rng.randint(36, 54)):
                y0 = int(np.argmax(c.mat[:, x] != kl))
                room = H - y0 - 3
                for k in range(rng.randint(min(7, room), max(min(7, room), min(14, room)))):
                    xx = x + int(round(1.2 * math.sin(k * 0.45)))
                    c.mat[y0 + k, xx], c.tone[y0 + k, xx] = kr, 3
                    c.mat[y0 + k, xx + 1], c.tone[y0 + k, xx + 1] = kr, 1
    if base:  # the foot: the soil darkens in its last 4 rows (wavy)
        for x in range(64):
            S = int(round(4 + 1.2 * wave(x, 67, (1.0, 0.6), 1, bump * 0.5)))
            for y in range(H - max(2, min(6, S)), H):
                if c.mat[y, x] == ke:
                    c.tone[y, x] = min(int(c.tone[y, x]), 2 if y < H - 2 else 1)
    return c


def write_earth_faces():
    out = []
    for season in SEASONS:
        for part in ("top", "mid", "top-base", "mid-base"):
            if season != "summer" and not part.startswith("top"):
                continue  # (v2: only the lips have season files)
            for h in (8, 4):
                for v in (0, 1, 2):
                    name = f"{SPRE[season]}face.earth.{part}.{h}{('', '.v1', '.v2')[v]}.png"
                    out.append(save(earth_face(season, part, h, v), os.path.join(OUT, name)))
    return out


# ------------------------------------------------------------------ rims of the plains grass and moss

def ground_ramp(ground, season):
    return GR.ramps_for(season)["grass"] if ground == "plains" else FO.ramps_for(season)["moss"]


def rim_tones(r):
    """v2's rule (NAMES v2 2b, round 8 N2): the dark edge a tone at least 28 darker than the ground's
    main tone 3 (and not brighter than tone 1), the east rim and the shadow a tone at least 15 darker;
    the lit rim the two brightest tones."""
    L = [luma(c) for c in r]
    edge = max([t for t in range(0, 2) if L[t] <= L[3] - 28] or [0])
    shade_t = max([t for t in range(0, 3) if L[t] <= L[3] - 15] or [1])
    return {"edge": (0, edge), "east": (shade_t, min(3, shade_t + 1)) if shade_t < 2 else (1, 2),
            "lit": (6, 5), "shadow": shade_t, "wide": L[3] - L[shade_t] < 20}


def g_rim_canvas(ground, season):
    return Canvas(64, 64, {"g": ground_ramp(ground, season)})


def g_draw_side(c, side, variant, T, limit=None):
    k = c.mid("g")
    for t in range(64):
        d, r = rim_profile(side, t, variant)
        for kk in range(d + r):
            x, y = {"N": (t, kk), "E": (63 - kk, t), "W": (kk, t)}[side]
            if limit and not limit(x, y):
                continue
            c.mat[y, x] = k
            if kk < d:
                c.tone[y, x] = T["edge"][0] if kk < d - 1 else T["edge"][1]
            elif side == "E":
                c.tone[y, x] = T["east"][0] if kk == d else T["east"][1]
            else:
                c.tone[y, x] = T["lit"][0] if kk == d else T["lit"][1]


def g_step(ground, season, mask, variant):
    c = g_rim_canvas(ground, season)
    T = rim_tones(c.ramps["g"])
    for bit, side in ((1, "N"), (2, "E"), (4, "W")):
        if mask & bit:
            g_draw_side(c, side, variant, T)
    return c


def g_inner(ground, season, corner):
    c = g_rim_canvas(ground, season)
    T = rim_tones(c.ramps["g"])
    dn, rn = rim_profile("N", 63 if corner == "ne" else 0, 0)
    side = "E" if corner == "ne" else "W"
    ds, rs = rim_profile(side, 0, 0)
    wN, wS = max(2, dn + rn), max(2, ds + rs)
    if corner == "ne":
        g_draw_side(c, "E", 0, T, limit=lambda x, y: y < wN)
        g_draw_side(c, "N", 0, T, limit=lambda x, y: x >= 64 - wS)
    else:
        g_draw_side(c, "W", 0, T, limit=lambda x, y: y < wN)
        g_draw_side(c, "N", 0, T, limit=lambda x, y: x < wS)
    return c


def g_shade(ground, season, variant):
    """The shadow on the lower cell east of a step: from its west side, 6-15 texels (moss and other
    grounds whose shadow tone is under 20 darker: 3 texels wider, v2's rule), wavy, the shadow tone,
    its outer 2 texels one tone lighter."""
    c = g_rim_canvas(ground, season)
    T = rim_tones(c.ramps["g"])
    k = c.mid("g")
    extra = 3 if T["wide"] else 0
    for y in range(64):
        w = int(round(10 + extra + 3.5 * wave(y, 404, (1.0, 0.5), variant, 2.5)))
        w = max(6 + extra, min(15 + extra, w))
        for x in range(w):
            c.mat[y, x], c.tone[y, x] = k, (T["shadow"] if x < w - 2 else min(3, T["shadow"] + 1))
    return c


def write_ground_steps():
    out = []
    for ground, name in (("plains", "plains.grass"), ("moss", "forest.grass")):
        for season in SEASONS:
            pre = f"{SPRE[season]}{name}.v3.step"
            for mask in range(1, 8):
                for v in (0, 1):
                    out.append(save(g_step(ground, season, mask, v), os.path.join(OUT, f"{pre}.{mask}.{v}.png")))
            for v in (0, 1):
                out.append(save(g_shade(ground, season, v), os.path.join(OUT, f"{pre}.shade.{v}.png")))
            for corner in ("ne", "nw"):
                out.append(save(g_inner(ground, season, corner), os.path.join(OUT, f"{pre}.inner.{corner}.png")))
    return out


def main(which="all"):
    n = 0
    if which in ("desert", "all"):
        n += len(write_faces("desert")) + len(write_steps("desert.sand"))
    if which in ("earth", "all"):
        n += len(write_earth_faces()) + len(write_ground_steps())
    print(f"{n} files")


if __name__ == "__main__":
    main(*(sys.argv[1:] or ["all"]))
