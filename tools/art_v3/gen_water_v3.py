"""v3 water (STYLE.md 6 "まだ"; DESERT.md 9): shallow and deep water, the deep-over-shallow edge and the
shore foam, 4 frames each, drawn by hand at density 4 (no v2 picture is scaled).

Keys, sizes and rules are v2's, unchanged (docs/art-release-v2/terrain/NAMES.md 3; the engine's water
layer src/view/waterLayer.js and groundV2.displayLayers): 64 x 64, anchor top-left, frames f = 0-3 all
switching together (WATER_FRAME_SEC 0.28 s):
  tile.water.<f>, tile.water.v1.<f>            shallow water, 2 variants (hash(i, j) % 2)
  tile.water.deep.<f>, tile.water.deep.v1.<f>  deep water
  tile.water.deep.edge.<mask>.<f>              deep over shallow (mask = deep corners 1-14)
  tile.water.foam.<mask>.<f>                   shore foam over the water (mask = land corners 1-14)
Joins: every water tile is a torus at its border: the features within 6 texels of the tile's border are
the same in both variants and every frame's border rows / columns continue the opposite side, so any
tile joins any other; the variants differ inside (x, y 8..56). The deep edge uses v2's own curve
(transitions.field, legacy, variant 0) at 2x, the foam the land edges' curve (gen_ground_v3.edge_inside,
variant 0: a shore's land edge always has v = 0 for masks other than 6 / 9).
The loop: each crest goes through a 4-frame life (forming, rising, cresting, breaking) with its own
phase, sparkles step 2 texels for 2 frames, the foam laps in and out; frame 3 -> 0 is a step like the
others.
Run: python3 tools/art_v3/gen_water_v3.py
"""

import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402

import gen_ground_v3 as G  # noqa: E402
from v3lib import ROOT, Canvas, lift_ramp, save  # noqa: E402

OUT = os.path.join(ROOT, "src", "art-release-v3", "terrain")
FRAMES = 4
RAMPS = {  # v2 ramps.json
    "shallow": ["#132e5a", "#1f4f8a", "#265499", "#2d6aa8", "#428fba", "#5694cc", "#b0dcf6"],
    "deep": ["#081c34", "#143e66", "#183c73", "#1c4f80", "#22688d", "#28649a", "#3e7cb2"],
}
EDGE_BAND = 6  # texels from the tile's border where every feature is shared by both variants

# crest life stages at density 4: rows of tones ('.' = leave the water), anchored at the row's left end
CREST_LIFE = {  # round 2: 3 lengths (no blob motifs: the water is an even field of crests)
    "s": [["44"], ["4334", ".22."], [".45.", "4334", ".22."], ["4..4", ".33."]],
    "m": [["444"], ["443344", ".2222."], ["..55..", "433334", ".2222."], ["44..44", ".3..3."]],
    "l": [["4444"], ["44334433", ".222222."], ["..4554..", "44333344", ".222222."], ["44....44", ".33..33."]],
}


def canvas():
    return Canvas(64, 64, {k: lift_ramp(v) for k, v in RAMPS.items()})


def stamp_wrap(c, mat, x, y, rows):
    k = c.mid(mat)
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == ".":
                continue
            X, Y = (x + i) % 64, (y + j) % 64
            c.mat[Y, X], c.tone[Y, X] = k, int(ch)


# (round 3) swell lines: long, gently curving rows of ripples across the tile, light on top (tone 4, 5 at a
# few crests) with a darker trough under the longer pieces (tone 2). They give the water a slow light / dark
# swell readable at 1x without blobs (blobs showed the tile grid). Drawn by hand: each line is
# y = y0 + amp * sin(2 pi x / 64 + phase) (+ a bump of the variant's own inside x 6..58), its pieces given as
# on / off runs over x 0..63 (wrapping). Lines in the 6-texel border band, and every line's pieces at x < 6 or
# x >= 58, are the same in both variants. Each line bobs 0, 0, 1, 1 texels with its own phase.
SWELLS = {
    "shallow": [  # (y0, amp, phase, frame phase, variant bump (v0, v1), runs (v0, v1))
        (2, 1.5, 0.0, 0, (0, 0), ([4, 6, 8, 6, 5, 7, 10, 6, 6, 3, 3], None)),
        (17, 2.5, 1.7, 1, (2, -2), ([3, 7, 7, 5, 4, 8, 11, 5, 6, 8], [3, 9, 9, 6, 3, 6, 8, 6, 6, 8])),
        (31, 2.0, 3.9, 3, (-2, 1), ([7, 6, 5, 8, 9, 5, 4, 7, 7, 6], [7, 8, 10, 5, 4, 8, 7, 4, 4, 7])),
        (46, 2.5, 5.2, 2, (1, -2), ([2, 6, 8, 6, 6, 5, 5, 8, 11, 7], [2, 10, 5, 4, 10, 7, 6, 5, 8, 7])),
    ],
    "deep": [
        (5, 1.5, 0.9, 0, (0, 0), ([3, 14, 5, 12, 4, 15, 6, 4, 1], None)),
        (25, 2.5, 2.8, 2, (2, -1), ([6, 9, 6, 7, 10, 8, 4, 8, 6], [6, 6, 9, 10, 5, 7, 7, 8, 6])),
        (44, 2.0, 4.6, 1, (-1, 2), ([4, 10, 9, 7, 5, 9, 7, 8, 5], [4, 7, 5, 10, 10, 6, 8, 9, 5])),
    ],
}
BOB = [0, 0, 1, 1]  # each line holds 2 frames, then rises / falls 1 texel; lines at their own phase
# (round 3) broad soft streaks of light (tone 4 round a core of 5, a lit top of 5 that glides 0, 1, 2, 1 texels) and of shade
# (tone 2): long thin lenses drawn by hand (row lengths from the top, centred), the variant's own, wholly
# inside x, y 8..56 so they never meet at the tile's border; few, so the tile does not show as a grid
STREAKS = {
    "shallow": {
        0: [(30, 22, 4, [8, 18, 12]), (19, 38, 2, [10, 16]), (42, 51, 4, [6, 14, 8])],
        1: [(24, 26, 4, [10, 20, 10]), (44, 13, 2, [8, 14]), (33, 47, 4, [8, 16, 6])],
    },
    "deep": {
        0: [(26, 13, 4, [8, 16, 8]), (40, 43, 2, [12, 18, 8])],
        1: [(38, 34, 4, [10, 18, 8]), (20, 23, 2, [10, 14, 6])],
    },
}
# glints: a small star that shows on one frame and fades on the next (tone 6 with tone 5 arms), per variant
GLINTS = {
    # each frame shows the glints of one variant only (variant 0 on frames 0 / 2, variant 1 on 1 / 3), so the
    # tiles that flash together are the hash's scattered half, not every tile (round 3: all tiles at once
    # made a lattice of stars)
    "shallow": {0: [(21, 13, 0), (44, 41, 2)], 1: [(38, 18, 1), (17, 46, 3)]},
    "deep": {0: [(30, 16, 0)], 1: [(43, 40, 3)]},
}


def _runs(runs):
    out, on = [], True
    for r in runs:
        out += [on] * r
        on = not on
    assert len(out) == 64, runs
    return out


def _swell_pieces(mat, variant):
    """[(x, y_at_frame0 as a function of x, frame phase, on)] for the swell lines of this variant."""
    lines = []
    for (y0, amp, ph, fph, bump, runs) in SWELLS[mat]:
        base = _runs(runs[0])
        own = _runs(runs[variant]) if (variant and runs[1]) else base
        on = [base[x] if (x < 6 or x >= 58) else own[x] for x in range(64)]
        b = bump[variant]
        ys = []
        for x in range(64):
            y = y0 + amp * math.sin(2 * math.pi * x / 64 + ph)
            if 6 <= x < 58:
                y += b * math.sin(math.pi * (x - 6) / 52)
            ys.append(int(math.floor(y + 0.5)))
        lines.append((ys, on, fph))
    return lines


def _features(mat, variant):
    """(crests, glints): shared crests (touching the border band, wrapping round the tile: the same in
    both variants) and the variant's own (wholly inside 8..56). Round 2: no swell blobs (they showed the
    tile grid); more, smaller crests of 3 lengths. Fixed by seeds: the same every run."""
    rng_s = random.Random({"shallow": 501, "deep": 502}[mat])
    rng_v = random.Random({"shallow": 511, "deep": 512}[mat] + 17 * variant)
    n_shared, n_own = (12, 12) if mat == "shallow" else (8, 8)
    crests = []
    for i in range(n_shared):
        side = i % 4
        a = rng_s.uniform(0, 64)
        b = rng_s.uniform(-3, EDGE_BAND - 2)
        x, y = {0: (a, b), 1: (a, 64 - b - 3), 2: (b, a), 3: (64 - b - 8, a)}[side]
        crests.append((int(x) % 64, int(y) % 64, rng_s.randrange(FRAMES), rng_s.choice("ssmml")))
    pts = G.scatter(rng_v, 48, n_own, 9, 0)
    for i, (x, y) in enumerate(pts):
        crests.append((8 + int(x * 40 / 48), 8 + int(y * 44 / 48), (i + variant) % FRAMES, rng_v.choice("ssmml")))
    return crests, GLINTS[mat][variant]


def water_tile(mat, frame, variant=0):
    c = canvas()
    k = c.mid(mat)
    c.mat[:, :], c.tone[:, :] = k, 3
    # swell lines first (the crests' life plays over them)
    for (ys, on, fph) in _swell_pieces(mat, variant):
        dy = BOB[(frame + fph) % FRAMES]
        x = 0
        # piece lengths (wrapping) decide the trough and the crest-top
        runs, start = [], None
        for i in range(64):
            if on[i] and not on[i - 1]:
                start = i
            if on[i] and not on[(i + 1) % 64]:
                runs.append((start if start is not None else i, i))
        if all(on):
            runs = [(0, 63)]
        for (s0, s1) in runs:
            n = (s1 - s0) % 64 + 1
            for j in range(n):
                x = (s0 + j) % 64
                y = (ys[x] + dy) % 64
                c.tone[y, x] = 5 if (n >= 7 and j in (n // 2, n // 2 + 1)) else 4
                if n >= 8 and 2 <= j < n - 2:  # the longer pieces: the swell's lit face 2 texels deep
                    c.tone[(y + 1) % 64, x] = 4
                    c.tone[(y + 2) % 64, x] = 2
                elif n >= 5 and 1 <= j < n - 1:
                    c.tone[(y + 1) % 64, x] = 2
    for (cx, cy, tone, rows) in STREAKS[mat][variant]:
        for r, n in enumerate(rows):
            x0 = cx - n // 2 + (r % 2)
            core = tone == 4 and len(rows) == 3 and r == 1  # the lens' middle row: a brighter core (5)
            for i in range(n):
                c.tone[cy + r, x0 + i] = 5 if (core and 3 <= i < n - 3) else tone
        if tone == 4:  # the lit top glides along it and back
            g = [0, 1, 2, 1][frame]
            n = rows[0]
            for i in range(3):
                c.tone[cy, cx - n // 2 + 1 + 2 * g + i] = 5
    crests, glints = _features(mat, variant)
    for (x, y, phase, size) in crests:
        stamp_wrap(c, mat, x, y, CREST_LIFE[size][(frame + phase) % FRAMES])
    for (x, y, f0) in glints:
        if frame == f0:
            stamp_wrap(c, mat, x - 1, y - 1, [".5.", "565", ".5."])
        elif (frame - f0) % FRAMES == 1:
            stamp_wrap(c, mat, x, y, ["5"])
    return c


def deep_overlay(mask, frame):
    """Deep water over shallow: v2's curve (transitions.field legacy, variant 0) at 2x; inside, the deep
    water tile (variant 0) of the same frame; its rim in two soft steps (deep 5, then 4)."""
    T = G._v2_transitions()
    tex = water_tile("deep", frame, 0)
    c = canvas()
    for y in range(64):
        for x in range(64):
            f = T.field(mask, (x + 0.5) / 2 - 0.5, (y + 0.5) / 2 - 0.5, 0, legacy=True)
            if f > 0.5:
                c.mat[y, x], c.tone[y, x] = c.mid("deep"), int(tex.tone[y, x])
                if f < 0.515:
                    c.tone[y, x] = 5
                elif f < 0.545:
                    c.tone[y, x] = 4
    return c


FOAM_REACH = [3, 4, 5, 4]  # the white wave front's band (texels from the shore), per frame: it laps out and back
# (round 3) per frame, what each band from the shore holds (band k = water texels k - 0.5 <= d < k + 0.5 from
# the nearest land texel; band 1 touches the land): S = the white shore line, F = the white wave front,
# L = the front breaking up as it draws back (white lace, the rest 5), 5 = foam, 4 = the wet line. Nothing past
# band 5. Between the shore line and the front there is always foam (5), so the front reads as its own line.
FOAM_BANDS = [
    "S5F4",   # 0: the wave close in, front at 3
    "S55F4",  # 1: going out, front at 4, wet line at 5
    "S555F",  # 2: furthest out, front at 5
    "S55L4",  # 3: drawing back, the front breaks into lace at 4
]
# along the shore (x on a shore running across, y on one running down; 32-periodic so it runs on into the next
# tile), drawn by hand: where the shore line / the front / the lace are white ('1') or foam 5 ('0')
SHORE_W = "11111011111110111101111111011111"
FRONT_W = "11011111101111110110111111101110"
LACE_W = "10010110001001101000110100100110"
FOAM_PAD = 8  # the land is continued this far past the tile's border (its border texels repeated) for d


def _land_distance(land):
    """Distance (texels, centre to centre) from every texel to the nearest land texel, and the vector to it;
    the land continued past the tile's border by repeating its border texels (the shore crosses the border
    where the next tile's land goes on)."""
    P = FOAM_PAD
    big = np.pad(land, P, mode="edge")
    ly, lx = np.nonzero(big)
    if len(ly) == 0:
        return np.full(land.shape, 99.0), np.zeros(land.shape), np.zeros(land.shape)
    # only the land texels next to water matter
    edge = np.zeros_like(big)
    pb = np.pad(big, 1, mode="edge")
    edge = big & ~(pb[:-2, 1:-1] & pb[2:, 1:-1] & pb[1:-1, :-2] & pb[1:-1, 2:])
    ly, lx = np.nonzero(edge)
    ly, lx = ly - P, lx - P
    yy, xx = np.mgrid[0:64, 0:64]
    dy = ly[None, None, :] - yy[..., None]
    dx = lx[None, None, :] - xx[..., None]
    d2 = dx * dx + dy * dy
    i = np.argmin(d2, axis=2)
    d = np.sqrt(np.take_along_axis(d2, i[..., None], 2)[..., 0])
    vx = np.take_along_axis(dx, i[..., None], 2)[..., 0]
    vy = np.take_along_axis(dy, i[..., None], 2)[..., 0]
    d[land] = 0
    return d, vx, vy


def foam_overlay(mask, frame):
    """Foam on the water outside a shore (mask = land corners; the land side transparent: the land's
    edge overlay is drawn over it). Round 3: the distance from the shore is the real distance from the land
    texels (gen_ground_v3.edge_inside, variant 0: the land edges' own line; continued past the tile's border),
    so the foam keeps one width on straight shores, bends, coves and ponds alike (round 2 divided the field's
    value by its slope: where the slope was small the foam swelled into a pool or a ball offshore).
    Bands from the shore (FOAM_BANDS, FOAM_REACH 2, 3, 4, 3: the white front laps out and back; nothing past
    5 texels): a broken white shore line, foam (shallow 5), the white wave front, the wet line (shallow 4);
    on frame 3 the front breaks into lace. The white breaks are hand-drawn rows along the shore (SHORE_W,
    FRONT_W, LACE_W), fixed in place: the white moves only out and back. On masks 6 / 9 (two shores) only
    one shore laps (the other keeps frame 0). No speck under 6 texels away from the tile's border."""
    F, inside = G.edge_inside(mask, 0)
    c = canvas()
    k = c.mid("shallow")
    if mask in (6, 9):  # two land pieces: each its own distance (one laps, the other keeps frame 0)
        yy, xx = np.mgrid[0:64, 0:64]
        side_a = ((xx - yy) < 0) if mask == 6 else ((xx + yy) > 63)  # the half whose shore keeps frame 0
        da, ax, ay = _land_distance(inside & side_a)
        db, bx, by = _land_distance(inside & ~side_a)
        use_a = da < db
        d = np.where(use_a, da, db)
        vx = np.where(use_a, ax, bx)
        vy = np.where(use_a, ay, by)
        still = use_a
    else:
        d, vx, vy = _land_distance(inside)
        still = np.zeros((64, 64), bool)

    def near(m, r):
        out = m.copy()
        for _ in range(r):
            g_ = out.copy()
            g_[1:] |= out[:-1]
            g_[:-1] |= out[1:]
            g_[:, 1:] |= out[:, :-1]
            g_[:, :-1] |= out[:, 1:]
            out = g_
        return out
    for y in range(64):
        for x in range(64):
            if inside[y, x]:
                continue
            band = int(math.floor(d[y, x] + 0.5))
            bands = FOAM_BANDS[0 if still[y, x] else frame]
            if band < 1 or band > len(bands):
                continue
            ch = bands[band - 1]
            t = (x if abs(vy[y, x]) >= abs(vx[y, x]) else y) % 32
            if ch == "S":
                tone = 6 if SHORE_W[t] == "1" else 5
            elif ch == "F":
                tone = 6 if FRONT_W[t] == "1" else 5
            elif ch == "L":
                tone = 6 if LACE_W[t] == "1" else 5
            else:
                tone = int(ch)
            c.mat[y, x], c.tone[y, x] = k, tone
    near1 = near(inside, 1)
    # no specks: 8-connected pieces under 6 texels that do not reach the tile's border
    op = c.mat != 0
    seen = np.zeros_like(op)
    for y0 in range(64):
        for x0 in range(64):
            if not op[y0, x0] or seen[y0, x0]:
                continue
            st, comp, edge = [(y0, x0)], [], False
            seen[y0, x0] = True
            while st:
                y, x = st.pop()
                comp.append((y, x))
                edge |= y in (0, 63) or x in (0, 63)
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        Y, X = y + dy, x + dx
                        if 0 <= Y < 64 and 0 <= X < 64 and op[Y, X] and not seen[Y, X]:
                            seen[Y, X] = True
                            st.append((Y, X))
            touches_land = any(near1[y, x] for y, x in comp)
            if (len(comp) < 6 and not edge) or (not edge and not touches_land):
                for y, x in comp:  # (round 2: also a piece that touches neither the land nor the border)
                    c.mat[y, x] = 0
    op = c.mat != 0  # and no texel joined only at a corner (no opaque 4-neighbour)
    p_ = np.pad(op, 1)
    lone = op & ~(p_[:-2, 1:-1] | p_[2:, 1:-1] | p_[1:-1, :-2] | p_[1:-1, 2:])
    c.mat[lone] = 0
    return c


def write_all():
    out = []
    for f in range(FRAMES):
        for mat, name in (("shallow", "tile.water"), ("deep", "tile.water.deep")):
            out.append(save(water_tile(mat, f, 0), os.path.join(OUT, f"{name}.{f}.png")))
            out.append(save(water_tile(mat, f, 1), os.path.join(OUT, f"{name}.v1.{f}.png")))
        for m in range(1, 15):
            out.append(save(deep_overlay(m, f), os.path.join(OUT, f"tile.water.deep.edge.{m}.{f}.png")))
            out.append(save(foam_overlay(m, f), os.path.join(OUT, f"tile.water.foam.{m}.{f}.png")))
    return out


if __name__ == "__main__":
    print(f"{len(write_all())} files")
