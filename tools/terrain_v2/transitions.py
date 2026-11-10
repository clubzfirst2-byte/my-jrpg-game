"""Ground v2 transitions: the "dual grid" 4-corner (Wang) scheme with layered overlays.

The ground is drawn on a grid shifted by half a tile: each DISPLAY tile's four corners sit on the
centres of four map cells. For a display tile, the engine draws the full ground tile of the
lowest-priority terrain among its 4 corners, then, for every higher terrain present (low to high), the
OVERLAY of that terrain with the mask of the corners whose terrain priority is >= that terrain's:

    mask bits: NW = 1, NE = 2, SW = 4, SE = 8 (1-14; 15 = the full ground tile, 0 = nothing)

So one set of 14 overlays per terrain covers every pair it can meet (grass over sand, over path, over
ruin, over water...), the borders run along the map cells' edges (a 1-cell path stays 1 cell wide), and
the 16-px staircase becomes a drawn curve.

The boundary is the same curve for every terrain: a bilinear blend of the 4 corners plus a 32-periodic
wobble (so it joins across display tiles) plus, for variant .1, an extra wobble that is zero on the tile
edges. The foam overlay (water.py) uses the same curve, so foam hugs every shore exactly.
Each terrain draws its own EDGE on that curve (grass: a darker turf edge with blades over it; sand: a dry
lit rim; snow: a lit / shaded rounded lip; path: a packed darker rim; ruin: a stone joint; moss: a lit
cushion rim).
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from canvas import Canvas  # noqa: E402

NW, NE, SW, SE = 1, 2, 4, 8
TAU = 2 * math.pi


def wobble(x, y):
    """32-periodic smooth wobble of the boundary (integer frequencies, so it joins tile to tile)."""
    a, b = TAU * (x + 0.5) / 32, TAU * (y + 0.5) / 32
    return (0.05 * math.sin(a + 0.7) + 0.035 * math.sin(2 * a + 2.1) + 0.04 * math.sin(b + 1.9) + 0.025 * math.sin(2 * b + 0.4)
            + 0.025 * math.sin(a + 2 * b + 0.3))


def inner_wobble(x, y, variant):
    """Extra wobble for variant .1, zero on the tile's edges (so .0 and .1 join each other)."""
    if variant == 0:
        return 0.0
    u, v = (x + 0.5) / 32, (y + 0.5) / 32
    w = math.sin(math.pi * u) * math.sin(math.pi * v)
    return w * (0.07 * math.sin(TAU * (1.5 * u + 0.8 * v) + 0.4) + 0.04 * math.sin(TAU * (2.5 * v - u) + 1.1))


def field(mask, x, y, variant=0):
    """> 0.5 inside the overlay's terrain."""
    u, v = (x + 0.5) / 32, (y + 0.5) / 32
    nw, ne, sw, se = (1.0 if mask & b else 0.0 for b in (NW, NE, SW, SE))
    f = nw * (1 - u) * (1 - v) + ne * u * (1 - v) + sw * (1 - u) * v + se * u * v
    return f + wobble(x, y) + inner_wobble(x, y, variant)


def gradient(mask, x, y):
    """Direction toward the inside of the terrain (from the corners only)."""
    u, v = (x + 0.5) / 32, (y + 0.5) / 32
    nw, ne, sw, se = (1.0 if mask & b else 0.0 for b in (NW, NE, SW, SE))
    return (ne - nw) * (1 - v) + (se - sw) * v, (sw - nw) * (1 - u) + (se - ne) * u


# Edge looks per terrain style. Each returns the overlay canvas from the terrain's ground tile `tex`.
RIM = 0.06  # field band of the rim (about 2 px)


def overlay(tex, mat, mask, variant, style):
    c = Canvas(32, 32, None, wrap=False)
    F = [[field(mask, x, y, variant) for x in range(32)] for y in range(32)]
    for y in range(32):
        for x in range(32):
            f = F[y][x]
            if f <= 0.5:
                continue
            c.px[y][x] = tex.px[y][x]
            gx, gy = gradient(mask, x, y)
            lit_side = (gx + gy) > 0.05  # the terrain lies to the lower right: this edge faces up / left
            if f < 0.5 + RIM:
                if style == "grass":
                    c.put(x, y, mat, 4 if lit_side else 2)  # turf edge: lit toward the light, shaded away
                elif style == "sand":
                    c.put(x, y, mat, 4 if lit_side else 3)  # a dry lit lip; no dark rim (it read as a stain)
                elif style == "snow":
                    c.put(x, y, mat, 5 if lit_side else 2)
                elif style == "path":
                    c.put(x, y, mat, 2)
                elif style == "ruin":
                    c.put(x, y, mat, 1 if f < 0.5 + RIM / 2 else 4)
                elif style == "moss":
                    c.put(x, y, mat, 4 if lit_side else 2)
    if style == "grass":  # blades over the edge: 2-px blades standing on the turf edge, lit tips
        for y in range(32):
            for x in range(32):
                f = F[y][x]
                if 0.5 - 0.05 < f <= 0.5 and _comb(x, y):
                    gx, gy = gradient(mask, x, y)
                    if gy >= 0:  # the turf is below: blades stick up out of it
                        c.put(x, y, mat, 4)
                        if y - 1 >= 0 and F[y - 1][x] <= 0.5:
                            c.put(x, y - 1, mat, 5)
                    else:
                        c.put(x, y, mat, 3)
                        if y + 1 < 32 and F[y + 1][x] <= 0.5:
                            c.put(x, y + 1, mat, 2)
    return c


def _comb(x, y):
    """Where blades stand along a grass edge: hand-chosen 32-periodic pattern of 2-3 px groups."""
    return (x * 5 + y * 3) % 11 in (0, 1)


STYLE = {"grass": "grass", "plains": "grass", "lake": "grass", "moss": "moss", "snow": "snow", "sand": "sand",
         "dsand": "sand", "path": "path", "ruin": "ruin"}
PRIORITY = ["ruin", "path", "dsand", "sand", "snow", "moss", "lake", "plains", "grass"]  # low -> high (water lowest)
