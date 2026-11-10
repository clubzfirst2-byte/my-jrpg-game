"""Ground v2 water: shallow and deep water, 4 frames each, the deep-over-shallow overlay and the shore
foam overlay (both dual-grid, the same masks and curve as transitions.py).

Waves: hand-placed crests, each going through a 4-frame life (forming, rising, cresting, falling) with
its own phase, so at every frame some crests peak somewhere and the loop has no jump (0 -> 1 -> 2 -> 3
-> 0). The broad swells (soft bands of tone 2 / 4) do not move. Sparkles (2 px, tone 5-6) step along.
Shallow = the v1 water.surface ramp (the guide's dark water blue, not the hero's splash colours);
deep = a darker blue (registered in PRODUCTION.md). The foam is the shallow ramp's 5 / 6 in 2-3 px
clusters, lapping in and out over the 4 frames.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from canvas import Canvas  # noqa: E402
import marks as M  # noqa: E402
from transitions import field, gradient  # noqa: E402

FRAMES = 4
CREST_LIFE = [  # (rows) per life stage; digits = tones, '.' = leave the water
    ["44"],
    ["4334", ".22."],
    [".455.", "43334", "..22."],
    ["4..4", ".33."],
]
SWELLS = [(8, 9, 9, 2.2, 2, 201, 0.1), (24, 24, 8, 2.0, 4, 202, -0.1)]  # broad, static, soft bands


def water_tile(mat, frame, variant=0):
    c = Canvas(32, 32, (mat, 3))
    for cx, cy, rx, ry, tone, seed, rot in SWELLS:
        M.fill_patch(c, mat, M.patch_pixels(cx, cy, rx, ry, seed, rot, 0.3), tone)
    crests = CRESTS[mat][variant]
    for x, y, phase in crests:
        stage = (frame + phase) % FRAMES
        c.stamp(x, y, CREST_LIFE[stage], mat)
    for x, y, step in SPARKLES[mat][variant]:
        if (frame + step) % FRAMES in (0, 1):
            c.stamp(x + 2 * ((frame + step) % FRAMES), y, ["56"], mat)
    return c


CRESTS = {  # (x, y, phase) per variant: wrap freely (all water tiles are the same seam)
    "shallow": {0: [(3, 4, 0), (19, 9, 2), (9, 19, 1), (25, 24, 3)],
                1: [(6, 6, 1), (22, 4, 3), (13, 17, 0), (27, 22, 2)]},
    "deep": {0: [(5, 7, 0), (21, 14, 2), (11, 25, 1)],
             1: [(15, 5, 3), (3, 17, 1), (24, 26, 0)]},
}
SPARKLES = {
    "shallow": {0: [(12, 13, 0)], 1: [(9, 11, 1)]},
    "deep": {0: [(17, 20, 1)], 1: [(8, 9, 3)]},
}


def deep_overlay(mask, frame, variant=0):
    """Deep water over shallow, on the dual grid. Its rim steps 5 -> 4 of the deep ramp, so the change from
    shallow to deep is soft. (The engine only makes 2x2-or-larger areas deep: NAMES.md.)"""
    tex = water_tile("deep", frame, variant)
    c = Canvas(32, 32, None, wrap=False)
    for y in range(32):
        for x in range(32):
            f = field(mask, x, y, variant)
            if f > 0.5:
                c.px[y][x] = tex.px[y][x]
                if f < 0.53:
                    c.put(x, y, "deep", 5)  # two soft steps from the shallow water into the deep
                elif f < 0.58:
                    c.put(x, y, "deep", 4)
    return c


FOAM_DEPTH = [0.04, 0.05, 0.06, 0.05]  # how far the foam reaches from the shore, per frame (lapping)
FOAM_BITS = {2, 3, 9, 10, 11, 17, 18, 25, 26}  # where the foam is brightest (6) along a shore, 32-periodic


def foam_overlay(mask, frame, variant=0):
    """Foam on the water just outside a shore (mask = corners that are land). Land side transparent (the
    land overlay is drawn over it). Includes a 1-px lighter shallow line beyond the foam."""
    c = Canvas(32, 32, None, wrap=False)
    for y in range(32):
        for x in range(32):
            f = field(mask, x, y, variant)
            if f > 0.5:
                continue
            reach = FOAM_DEPTH[frame]
            if mask in (6, 9) and ((x - y) < 0 if mask == 6 else (x + y) > 31):
                reach = FOAM_DEPTH[0]  # two shores on one tile: only one of them laps, so the tile changes <= 40 px
            if f > 0.5 - reach:
                gx, gy = gradient(mask, x, y)
                along = (x if abs(gy) >= abs(gx) else y) % 32  # along the shore (the bright bits stay; the band laps)
                c.put(x, y, "shallow", 6 if along in FOAM_BITS else 5)
            elif f > 0.5 - reach - 0.035:
                c.put(x, y, "shallow", 4)
    return c
