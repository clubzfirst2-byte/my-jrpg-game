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


def _features(mat, variant):
    """(crests, sparkles): shared crests (touching the border band, wrapping round the tile: the same in
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
    sparkles = [(rng_v.randint(12, 48), rng_v.randint(12, 50), rng_v.randrange(FRAMES))] if mat == "shallow" else []
    return crests, sparkles


def water_tile(mat, frame, variant=0):
    c = canvas()
    k = c.mid(mat)
    c.mat[:, :], c.tone[:, :] = k, 3
    crests, sparkles = _features(mat, variant)
    for (x, y, phase, size) in crests:
        stamp_wrap(c, mat, x, y, CREST_LIFE[size][(frame + phase) % FRAMES])
    for (x, y, step) in sparkles:
        s = (frame + step) % FRAMES
        if s in (0, 1):
            stamp_wrap(c, mat, x + 2 * s, y, ["66", ".5"])
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


FOAM_REACH = [2.0, 3.0, 4.0, 3.0]  # round 2: texels from the shore, per frame (lapping)


def foam_overlay(mask, frame):
    """Foam on the water outside a shore (mask = land corners; the land side transparent: the land's
    edge overlay is drawn over it). Round 2: the distance from the shore in texels is the field's
    distance (0.5 - F) / |grad F| (continuous across tiles: F and its gradient are), so the foam keeps one
    width round the coast's bends (no pools). A foam band that laps in and out (FOAM_REACH: 3, 4, 5, 4
    texels), bright 2 x 2 clusters (shallow 6) on a 4-texel pattern of period 16 cells (it runs on into the next
    tile) that shifts with the frame, the rest shallow 5; a wet line (shallow 4, 2 texels) beyond. On masks
    6 / 9 (two shores) only one shore laps. No speck under 6 texels away from the tile's border."""
    F, inside = G.edge_inside(mask, 0)
    T = G._v2_transitions()
    c = canvas()
    k = c.mid("shallow")
    # (round 2) a dropped island (F > 0.5 not reaching the tile's border: edge_inside leaves it water, the
    # land is not drawn there): no foam on it or round it, unless real land is near too (v2's rule)
    isl = (F > 0.5) & ~inside

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
    skip = near(isl, 7) & ~near(inside, 7)
    for y in range(64):
        for x in range(64):
            if inside[y, x] or skip[y, x]:
                continue
            gx, gy = T.gradient(mask, (x + 0.5) / 2 - 0.5, (y + 0.5) / 2 - 0.5)
            g = math.hypot(gx, gy) / 64  # per texel (transitions.gradient is per tile: u, v 0..1 over 64 texels)
            if g < 1e-4:
                continue
            d = (0.5 - F[y, x]) / g
            reach = FOAM_REACH[frame]
            if mask in (6, 9) and ((x - y) < 0 if mask == 6 else (x + y) > 63):
                reach = FOAM_REACH[0]
            fv = F[y, x]
            if d < reach and fv > 0.42:  # (and near the shore in the field too: where the field's wobble keeps
                bright = ((x // 4) + 2 * (y // 4) + frame) % 4 == 0 and x % 4 < 2 and y % 4 < 2 and d < reach - 0.5
                c.mat[y, x], c.tone[y, x] = k, (6 if bright else 5)
            elif d < reach + 2 and fv > 0.40:  # it just under 0.5 over a broad area, d alone made pools offshore)
                c.mat[y, x], c.tone[y, x] = k, 4
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
