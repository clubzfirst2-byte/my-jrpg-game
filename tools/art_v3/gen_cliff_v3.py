"""v3 steps and cliffs (STYLE.md 6 "まだ": the step rims, step shadows and cliff faces), drawn by hand
at density 4 (no v2 picture is scaled). DESERT.md 7 (round 1, the desert), 8 (round 4: earth faces,
plains / forest rims; round 5: the edge-typed faces, the forest's tops, the winter earth faces).

Rims (v2's rules, unchanged: docs/art-release-v2/terrain/NAMES.md 2b): `<prefix>.v3.step.<mask>.<v>`
over a raised cell's surface (mask = 1 lowerNorth + 2 lowerEast + 4 lowerWest, v = hash(tx + 5, ty + 9)
% 2), the shadow `<prefix>.v3.step.shade.<v>` on the lower cell east of it (v = hash(tx + 6, ty + 9) % 2),
the inner corners `<prefix>.v3.step.inner.<ne|nw>`; 64 x 64, anchor top-left. Their waves have a period of
64 along the side and a variant only adds a bump that is 0 at the tile's ends.
Faces: bands of 8 / 4 game px stacked down the south side of a raised cell (gameView.addFace), 64 x 32 /
64 x 16, the v1 / v2 key names `face.<desert|earth>.<top|mid><-base?>.<8|4>` with
  * ""  / ".v1" / ".v2": the set for the rule decided on 2026-11-14 (band k takes (hash(tx, ty) + k) % 3)
  * ".e<L><R>" (L, R 0-2): the round-5 edge-typed set (NAMES.md 5, DESERT.md 8.7): a band's left / right
    end has one of 3 edge types (layer heights and thicknesses), chosen by the engine per tile end, so the
    ends of a row of tiles are not all the same (no "chain" of narrow waists every 64 texels)
  seasons: summer (no prefix), "autumn." for the tops (top, top-base), "winter." for every part (snow
  caps on the ledges); the forest's tops `<season.>face.earth.forest.<top|top-base>.<8|4><suffix>`
  (a moss lip). The first / last rows of a band have no ledge edge, so bands stack in any order.
Run: python3 tools/art_v3/gen_cliff_v3.py [desert|earth|all]
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


FACE_VARIANTS = 3  # the plain / ".v1" / ".v2" set (the rule decided 2026-11-14: band k takes (hash + k) % 3)
EDGE_TYPES = 3  # round 5 (inspection 2, P1-A): the edge-typed set ".e<L><R>" (DESERT.md 8.7)

# Round 5: a face picture is described by a spec (L, R, mid): L, R the edge types (0-2) of its left /
# right end, mid its own movement in the middle of the tile. Every profile (the layer edges, the lip,
# the foot, the laminations) runs from the left type's value at x = 0 to the right type's at x = 63
# (smoothstep), plus a wave every picture shares and the middle's bump. The values at a tile's end
# depend only on that end's type, so a tile joins any neighbour that has the same type on the shared
# end; with 3 types the ends of a row are not all the same any more (no node every 64 texels: the
# "chain" of P1-A). The plain / .v1 / .v2 set (kept for the rule (hash + k) % 3) is (1, 1, -1 / 0 / 1)
# with a small middle movement.
ENDS = {  # per profile: the offset (rows) of each edge type (round 6, inspection 3 P2: type 0 makes the
    # layer thick (about 17 rows), type 2 thin (about 3; where it would be under 3 rows it is not drawn),
    # so the light layers of stacked bands differ a lot in thickness: no even stripe every 8 px)
    "ya": (-4.0, 0.0, 3.0), "yb": (4.0, 0.0, -3.0), "yc": (-2.0, 0.0, 2.0), "lam": (-2.0, 0.0, 2.0),
    "lip": (-1.5, 0.0, 1.5), "foot": (-2.0, 0.0, 2.0),
}


def smooth(x):
    t = x / 63.0
    return t * t * (3 - 2 * t)


def prof(x, base, key, seed, spec, amp=1.5, mid_scale=1.0):
    """base + the ends' offsets (left type -> right type) + a shared wave (0 at both ends' values is not
    needed: the wave has a period of 64, so x = 63 and the next tile's x = 0 are neighbours on it) + the
    middle bump (0 at both ends)."""
    L, R, mid = spec
    e = ENDS[key]
    s = smooth(x)
    v = base + e[L] * (1 - s) + e[R] * s + amp * wave(x, seed, (1.0, 0.6))
    return v + mid * mid_scale * math.sin(math.pi * x / 63.0) ** 2


def spec_seed(spec):
    L, R, mid = spec
    return L * 7 + R * 3 + int(round(mid * 10)) * 31


def specs():
    """(suffix, spec) of every picture of a part: the compat set and the 9 edge-typed ones."""
    out = [("", (1, 1, -1.2)), (".v1", (1, 1, 0.0)), (".v2", (1, 1, 1.2))]
    for L in range(EDGE_TYPES):
        for R in range(EDGE_TYPES):
            mid = ((L * 3 + R) % 5 - 2) * 1.3  # -2.6 .. 2.6 by the pair
            out.append((f".e{L}{R}", (L, R, mid)))
    return out


def band_body(c, H, part, spec, seed, style, pebbles=False):
    """The body of one face band (64 x H): layers whose edges follow prof() (sandstone: a lighter hard
    layer, lit top row, shaded rows under; soil: a darker packed layer, its top row in shadow), an 8-px
    band's thin dark seam, bedding laminations (shared waves, broken by the spec), a lens in about half
    of the pictures (inside the tile, never at its ends), partial joints, pits, streaks (sandstone),
    pebbles (soil, 0-2, one tone darker than round 4, at varying heights)."""
    rng = random.Random(seed * 13 + spec_seed(spec))
    big = H > 16
    pi = {"top": 1, "mid": 2, "top-base": 3, "mid-base": 4}[part]
    pm = (0.8, -0.8, 1.2, -1.2)[pi - 1]
    sp = (spec[0], spec[1], spec[2] + pm)
    y_a, y_b = (9, 18) if big else (5, 10)
    lay_t = 4 if style == "sandstone" else 2
    for li, y0 in enumerate((4, 13, 22, 29) if big else (3, 12)):  # laminations first (the layer covers them)
        gaps = []
        for _ in range(rng.randint(1, 3)):
            g0 = rng.randint(4, 52)
            gaps.append((g0, min(60, g0 + rng.randint(4, 12))))
        lt = 2 if li % 2 == 0 else 4
        for x in range(64):
            if any(g0 <= x < g1 for g0, g1 in gaps):
                continue
            y = int(round(prof(x, y0, "lam", 97 + li, sp, 1.0, 0.3)))
            if 2 <= y < H - 2:
                c.tone[y, x] = lt
    ledges = {}
    for x in range(64):
        ya = int(round(prof(x, y_a, "ya", 91, sp, 1.6, 1.0)))
        yb = int(round(prof(x, y_b, "yb", 92, sp, 1.8, -0.8)))
        ya = max(2, min(H - 8 if big else H - 6, ya))
        yb = min(H - 6 if big else H - 3, yb)
        if yb - ya < 3:  # the layer has thinned out here (edge type 2): not drawn
            if big:
                yc = int(round(prof(x, 26, "yc", 93, sp, 1.2, -0.5)))
                c.tone[min(H - 4, max(4, yc)), x] = 2
            continue
        ledges[x] = yb
        for y in range(ya, yb):
            c.tone[y, x] = lay_t
        c.tone[ya, x] = (lay_t + 1) if style == "sandstone" else 1
        c.tone[yb, x] = 1 if style == "sandstone" else 3
        if style == "sandstone" and yb + 1 < H - 2:
            c.tone[yb + 1, x] = 2
        if big:
            yc = int(round(prof(x, 26, "yc", 93, sp, 1.2, -0.5)))
            yc = min(H - 4, max(yb + 3, yc))
            c.tone[yc, x] = 2
    if rng.random() < 0.5:  # a lens in about half of the pictures (inside the tile)
        ln = rng.randint(14, 30)
        x0 = rng.randint(6, 58 - ln)
        th = rng.uniform(3.0, 5.0)
        yc = rng.uniform(3 + th / 2, H - 3 - th / 2)
        kind = -1 if style == "sandstone" else 1
        for x in range(x0, x0 + ln):
            half = th * math.sin(math.pi * (x - x0) / ln) ** 0.6 / 2
            if half < 1.0:
                continue
            for y in range(max(2, int(round(yc - half))), min(H - 3, int(round(yc + half)))):
                c.tone[y, x] = 3 + kind
    for n_ in range(rng.randint(0, 2)):  # partial joints (some pictures none)
        x = rng.randint(6, 56)
        y0 = rng.randint(2, H // 2)
        y1 = rng.randint(min(H - 3, y0 + 5), H - 3)
        for y in range(y0, y1):
            xx = x + (1 if ((y + n_ * 3) // 7) % 2 else 0)
            c.tone[y, xx] = 1
            if c.tone[y, xx + 1] in (2, 3):
                c.tone[y, xx + 1] = c.tone[y, xx + 1] + 1
    for _ in range(rng.randint(2, 5) if big else rng.randint(0, 2)):  # pits
        x, y = rng.randint(4, 56), rng.randint(3, H - 6)
        for dx in range(3):
            c.tone[y, x + dx] = 1
            c.tone[y + 1, x + dx] = 2
            c.tone[y + 2, x + dx] = min(5, max(int(c.tone[y + 2, x + dx]), 4))
    if style == "sandstone":
        for _ in range(rng.randint(0, 2)):  # dark streaks down from the layer
            x = rng.randint(6, 54)
            ys = np.nonzero(c.tone[:, x] == 1)[0]
            y0 = int(ys[0]) if len(ys) else H // 2
            for y in range(y0 + 2, min(H - 3, y0 + 2 + rng.randint(4, 9))):
                for dx in (0, 1):
                    if c.tone[y, x + dx] >= 3:
                        c.tone[y, x + dx] = 2
    if pebbles:  # round 5 (P2): 0-2 stones, one tone darker, at varying heights (some pictures none)
        kp = c.mid("pebble")
        ke = c.mat[H // 2, 32]
        for _ in range(rng.choice((0, 0, 1, 1, 2))):
            x, y = rng.randint(5, 54), rng.randint(3, H - 7)
            for dy, (a, b, t) in enumerate(((1, 3, 4), (0, 4, 2), (0, 4, 1))):
                for dx in range(a, b):
                    c.mat[y + dy, x + dx], c.tone[y + dy, x + dx] = kp, (3 if (dy == 1 and dx == 0) else t)
            for dx in range(1, 5):
                if c.mat[y + 3, x + dx] == ke:
                    c.tone[y + 3, x + dx] = 1
    return sp, ledges


def face(mat, part, h, spec):
    """One sandstone face band (64 x 4h): band_body, a sand lip with drips on a top band, a sand pile at
    the foot of a base band (both following prof(): their ends by the edge types)."""
    H = 4 * h
    top, base = part.startswith("top"), part.endswith("base")
    c = face_canvas(h)
    pi = {"top": 1, "mid": 2, "top-base": 3, "mid-base": 4}[part]
    seed = MATERIALS[mat]["seed"] * 1000 + pi * 10 + h
    rng = random.Random(seed + 1 + spec_seed(spec))
    kr, kf = c.mid("rock"), c.mid("fine")
    c.mat[:, :], c.tone[:, :] = kr, 3
    sp, _ = band_body(c, H, part, spec, seed, "sandstone")
    if top:
        for x in range(64):
            L = int(round(prof(x, 8, "lip", 31, sp, 1.4, 0.7)))
            L = max(7, min(10, L))
            for y in range(L):
                c.mat[y, x] = kf
                c.tone[y, x] = 6 if y == 0 else (5 if y < 3 else (4 if y < L - 1 else 2))
            c.mat[L, x], c.tone[L, x] = kr, 1
            c.mat[L + 1, x], c.tone[L + 1, x] = kr, 1
            if c.tone[L + 2, x] == 3:
                c.tone[L + 2, x] = 2
        for _ in range(rng.randint(1, 3)):
            x = rng.randint(4, 57)
            y0 = int(np.argmax(c.mat[:, x] == kr))
            for k in range(rng.randint(4, 9)):
                if y0 + k < H - 3:
                    for dx in (0, 1):
                        c.mat[y0 + k, x + dx], c.tone[y0 + k, x + dx] = kf, (4 if dx == 0 else 3)
    if base:
        for x in range(64):
            S = int(round(prof(x, 5, "foot", 53, sp, 1.8, 1.0)))
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
            for suf, spec in specs():
                out.append(save(face(mat, part, h, spec), os.path.join(OUT, f"face.{mat}.{part}.{h}{suf}.png")))
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


SNOW = ["#3a4866", "#7a8cae", "#99abc7", "#b8c8e0", "#cadbe9", "#dce6f2", "#f8fbff"]  # v2 "snow"
LEAF_AUT = ["#4a1e0e", "#7a2e14", "#9a4018", "#b85a20", "#d07a28", "#e09a38", "#f0c060"]


def earth_canvas(h, season, lip="plains"):
    lr = lip_ramp(season) if lip == "plains" else FO.ramps_for(season)["moss"]
    return Canvas(64, 4 * h, {"earth": lift_ramp(EARTH), "pebble": lift_ramp(PEBBLE), "root": lift_ramp(ROOT_R),
                              "lip": lr, "snow": lift_ramp(SNOW), "leaf": lift_ramp(LEAF_AUT)})


def earth_face(season, part, h, spec, lip="plains"):
    """One earth face band (64 x 4h) under a grass-topped (lip "plains") or moss-topped (lip "forest",
    round 5, P1-B: face.earth.forest.top*) cell: band_body (soil), roots on some top bands; a top band
    has the season's lip:
      plains  grass 9-13 rows with blade tips hanging 0-5 texels (autumn grass; winter a rounded snow lip)
      forest  moss 8-11 rows with rounded cushion bumps hanging 1-3 texels (the forest floor's moss
              ramp); autumn a few fallen leaves on it; winter a rounded snow lip
    a base band darkens in its last rows. Winter (round 5, P3): small snow caps on the ledges (the tops
    of the packed layer), 0-2 per band, 2 rows (6 over 5), 8-16 wide."""
    H = 4 * h
    top, base = part.startswith("top"), part.endswith("base")
    c = earth_canvas(h, season, lip)
    pi = {"top": 1, "mid": 2, "top-base": 3, "mid-base": 4}[part]
    seed = 5000 + pi * 10 + h
    rng = random.Random(seed + spec_seed(spec) + (7 if lip == "forest" else 0))
    ke, kr, kl = c.mid("earth"), c.mid("root"), c.mid("lip")
    c.mat[:, :], c.tone[:, :] = ke, 3
    sp, ledges = band_body(c, H, part, spec, seed, "soil", pebbles=True)
    winter = season == "winter"
    if winter:  # round 6 (inspection 3 P2): snow sitting ON a ledge (the top of the soil under the packed
        # layer): 2 rows of snow (6 over 5, the right end 4: its shaded side) and the ledge's underside in
        # shadow right under it (soil 1); 3 rows (6, 6, 5; the ends and the right end shaded), 0-2 caps per
        # band, 8-18 wide, only where the ledge is drawn
        ks = c.mid("snow")
        for _ in range(rng.choice((0, 1, 1, 2)) if H > 16 else rng.choice((0, 0, 1))):
            x0 = rng.randint(3, 44)
            xs = [x for x in range(x0, min(61, x0 + rng.randint(8, 18))) if x in ledges]
            run = []
            for x in xs:  # the longest run of neighbouring columns
                if run and x != run[-1][-1] + 1:
                    run.append([x])
                elif run:
                    run[-1].append(x)
                else:
                    run.append([x])
            run = max(run, key=len) if run else []
            if len(run) < 6:
                continue
            for x in run:
                y = ledges[x]
                if y - 2 < 3 or y + 1 >= H - 2:
                    continue
                end = x in (run[0], run[-1])
                if y - 3 < 3:
                    continue
                if not end:
                    c.mat[y - 3, x], c.tone[y - 3, x] = ks, 6  # rounded ends: the top row not at the ends
                c.mat[y - 2, x], c.tone[y - 2, x] = ks, (5 if end else 6)
                c.mat[y - 1, x], c.tone[y - 1, x] = ks, (4 if (end or x > run[-1] - 3) else 5)
                c.mat[y, x], c.tone[y, x] = ke, 1
                if c.mat[y + 1, x] == ke:
                    c.tone[y + 1, x] = 2
    if top:
        for x in range(64):
            if lip == "forest" and not winter:
                L = int(round(prof(x, 9, "lip", 63, sp, 1.2, 0.5)))
                L = max(8, min(11, L)) if H > 16 else max(6, min(8, L - 3))
                bump = int(round(2 + 1.5 * math.sin(2 * math.pi * x / 9.14 + 0.7)))  # cushions every ~9 texels
                hang = min(max(0, bump), H - 3 - L)
                for y in range(L + hang):
                    c.mat[y, x] = kl
                    c.tone[y, x] = 5 if y < 2 else (4 if y < 4 else (3 if y < L + hang - 2 else 2))
            else:
                L = int(round(prof(x, 10 if winter else 11, "lip", 61, sp, 1.5, 0.6)))
                L = max(9, min(13, L)) if H > 16 else max(7, min(9, L - 3))
                hang = 0 if winter else (GR.hsh(x, 3, 71) % 6 if GR.hsh(x // 2, 1, 72) % 3 else 0)
                hang = min(hang, H - 3 - L)
                for y in range(L + hang):
                    c.mat[y, x] = kl
                    if winter:
                        c.tone[y, x] = 6 if y < 2 else (5 if y < L - 2 else (4 if y < L - 1 else 2))
                    else:
                        c.tone[y, x] = 5 if y < 2 else (4 if y < 5 else (3 if y < L - 2 else 2))
            y_end = int(np.argmax(c.mat[:, x] != kl))
            for y in range(y_end, min(H - 2, y_end + 2)):
                if c.mat[y, x] == ke:
                    c.tone[y, x] = 1 if y == y_end else 2
        if lip == "forest" and season == "autumn":  # fallen leaves on the moss lip (3 x 2, 3-5)
            for _ in range(rng.randint(1, 3)):  # round 6 (P3): heights 1-8, some in pairs (no row of leaves)
                x, y = rng.randint(3, 56), rng.randint(1, 8 if H > 16 else 5)
                for (ox, oy) in ([(0, 0)] if rng.random() < 0.6 else [(0, 0), (3, rng.choice((-1, 1)))]):
                    for dx in range(3):
                        for dy in range(2):
                            X, Y = x + ox + dx, y + oy + dy
                            if 0 <= Y < H and X < 64:
                                c.mat[Y, X], c.tone[Y, X] = c.mid("leaf"), (4 if dy == 0 else 2)
        if spec[2] > 1.0 and lip == "plains":  # roots hanging from the lip on some top bands
            for x in (rng.randint(8, 24), rng.randint(36, 54)):
                y0 = int(np.argmax(c.mat[:, x] != kl))
                room = H - y0 - 3
                for k in range(rng.randint(min(7, room), max(min(7, room), min(14, room)))):
                    xx = x + int(round(1.2 * math.sin(k * 0.45)))
                    c.mat[y0 + k, xx], c.tone[y0 + k, xx] = kr, 3
                    c.mat[y0 + k, xx + 1], c.tone[y0 + k, xx + 1] = kr, 1
    if base:
        for x in range(64):
            S = int(round(prof(x, 4, "foot", 67, sp, 1.2, 0.5)))
            for y in range(H - max(2, min(6, S)), H):
                if c.mat[y, x] == ke:
                    c.tone[y, x] = min(int(c.tone[y, x]), 2 if y < H - 2 else 1)
    return c


def write_earth_faces():
    """face.earth.* (all parts; summer and, round 5, winter for every part: the snow caps), the autumn
    lips (top, top-base), and the forest's tops face.earth.forest.top* (3 seasons)."""
    out = []
    for season in SEASONS:
        for part in ("top", "mid", "top-base", "mid-base"):
            if season == "autumn" and not part.startswith("top"):
                continue  # (autumn: only the lips have season files, as v2)
            for h in (8, 4):
                for suf, spec in specs():
                    out.append(save(earth_face(season, part, h, spec), os.path.join(OUT, f"{SPRE[season]}face.earth.{part}.{h}{suf}.png")))
                    if part.startswith("top"):
                        out.append(save(earth_face(season, part, h, spec, "forest"),
                                        os.path.join(OUT, f"{SPRE[season]}face.earth.forest.{part}.{h}{suf}.png")))
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
                c.tone[y, x] = T["lit"][0] if kk < d + T.get("lit_w", 1) else T["lit"][1]


def g_tones(ground, season, ramp):
    """rim_tones, and (round 5, inspection 2 P3) the autumn forest: its dark edge (37) is as dark as the
    floor's darkest colour (38), so its lit line is 2 texels of the brightest tone (it reads by the light)."""
    T = rim_tones(ramp)
    if ground == "moss" and season == "autumn":
        T["lit_w"] = 2
    return T


def g_step(ground, season, mask, variant):
    c = g_rim_canvas(ground, season)
    T = g_tones(ground, season, c.ramps["g"])
    for bit, side in ((1, "N"), (2, "E"), (4, "W")):
        if mask & bit:
            g_draw_side(c, side, variant, T)
    return c


def g_inner(ground, season, corner):
    c = g_rim_canvas(ground, season)
    T = g_tones(ground, season, c.ramps["g"])
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
