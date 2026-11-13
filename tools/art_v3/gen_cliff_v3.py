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
    if variant:
        v += bump * math.sin(math.pi * t / 64) ** 2
    return v


def face_canvas(h):
    r = D.ramps_for()
    return Canvas(64, 4 * h, {"rock": lift_ramp(MATERIALS["desert"]["rock"]), "sand": r["sand"], "fine": r["fine"]})


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
    rng = random.Random(seed)
    kr, kf = c.mid("rock"), c.mid("fine")
    c.mat[:, :], c.tone[:, :] = kr, 3
    joints = JOINTS[variant]
    for n_, j in enumerate(joints):
        rr = random.Random(seed * 3 + n_)
        y0 = rr.randint(0, H // 3)
        y1 = H if (n_ + pi) % 2 else rr.randint(H // 2, H - 4)  # one joint runs to the band's foot
        for y in range(y0, y1):
            jx = j + (1 if (y // 11 + j) % 5 == 0 else 0)  # the joint steps a texel now and then
            c.tone[y, jx] = 1
            c.tone[y, jx + 1] = 4
    # the waves of the ledge, the lip and the foot share one seed for every part and variant (so their
    # ends meet the neighbour's whatever it is); parts and variants differ only by a bump (0 at the ends)
    bump = (1.0, -1.0, 1.6, -1.6)[pi - 1] + (2.2 if variant else 0.0)
    if h == 8:  # one ledge at ~17 rows
        for x in range(64):
            y = int(round(17 + 2.2 * wave(x, 7, (1.0, 0.5), 1, bump)))
            y = max(5, min(H - 6, y))
            c.tone[y, x] = 4 if c.tone[y, x] != 1 else 1
            c.tone[y + 1, x] = 1
            c.tone[y + 2, x] = 2
    for _ in range(rng.randint(2, 3)):  # short fractures: 3-6 long, slanting a little, dark under lit
        x = rng.randint(4, 54)
        y = rng.randint(4, H - 6)
        for k in range(rng.randint(3, 6)):
            xx, yy = x + k, y + (k // 3) * rng.choice((0, 1))
            if xx < 62 and c.tone[yy, xx] == 3:
                c.tone[yy, xx] = 2
                if c.tone[yy - 1, xx] == 3:
                    c.tone[yy - 1, xx] = 4
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
            for v in (0, 1):
                name = f"face.{mat}.{part}.{h}{'.v1' if v else ''}.png"
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


def main(which="desert"):
    n = len(write_faces("desert")) + len(write_steps("desert.sand"))
    print(f"{n} files")


if __name__ == "__main__":
    main(*(sys.argv[1:] or ["desert"]))
