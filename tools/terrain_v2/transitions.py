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


# Round 7. The side of a tile where a boundary crosses (the middle of the side) can carry a bump: side state 0
# (the round-6 crossing) or 1 (the crossing moved by about 3 px and the edge curving to it). A bump is a
# function of the position along the side times a fall-off away from it, so the two tiles sharing a side see
# the same field there: with the same state on a shared side they join. Overlay variant v = sA + 2·sB with
# sA, sB the states of the first and second side the boundary crosses, in the order N, E, S, W (NAMES.md 2).
# Masks 6 and 9 (the boundary crosses all 4 sides) keep their 2 round-6 variants (all sides state 0).
# INNER_AMP: every variant also gets an inner wobble (zero on the tile's edges), strong enough that the border
# swings 4+ px inside every tile (round 7, W2: the west-half mask 5 was almost straight).
SIDES = ("N", "E", "S", "W")
BUMP = 0.15
SHARED = 0.35  # round 7: the wobble every tile shares (32-periodic) is weaker; the per-tile parts carry the shape
INNER_AMP = {1: 3.6, 2: 3.1, 3: 3.5, 4: 2.7, 5: 2.1, 7: 2.8, 8: 2.8, 10: 2.0, 11: 2.2, 12: 1.7, 13: 1.6, 14: 2.4}  # tuned: border swing per variant (jit)


def crossing_sides(mask):
    nw, ne, sw, se = (bool(mask & b) for b in (NW, NE, SW, SE))
    return [sd for sd, on in zip(SIDES, (nw != ne, ne != se, sw != se, nw != sw)) if on]


def n_variants(mask):
    return 2 if mask in (6, 9) else 4


def side_states(mask, variant):
    if mask in (6, 9):
        return {}
    cs = crossing_sides(mask)
    return {cs[0]: variant & 1, cs[1]: (variant >> 1) & 1}


def _bump(t, d):
    """t: 0-1 along the side, d: 0-1 away from it. Peaks at the side's middle, 0 at the corners and from d = 0.45."""
    fall = max(0.0, 1 - d / 0.45) ** 2
    return BUMP * math.sin(math.pi * t) ** 2 * (1 + 0.5 * math.sin(TAU * t + 0.6)) * fall


def side_terms(mask, x, y, variant):
    st = side_states(mask, variant)
    if not st:
        return 0.0
    u, v = (x + 0.5) / 32, (y + 0.5) / 32
    out = 0.0
    for sd, on in st.items():
        if not on:
            continue
        t, d = {"N": (u, v), "S": (u, 1 - v), "W": (v, u), "E": (v, 1 - u)}[sd]
        out += _bump(t, d)
    return out


def inner7(mask, x, y, variant):
    """Round 7: an inner wobble on every variant (two phase sets by the variant's parity), zero on the edges."""
    u, v = (x + 0.5) / 32, (y + 0.5) / 32
    w = math.sin(math.pi * u) * math.sin(math.pi * v)  # 0 on the tile's edges
    ph = 3.1 * (variant % 2) + 4.7 * (variant // 2) + 0.9 * mask  # round 8: the 4 variants far apart (mask 10 repeated)
    amp = INNER_AMP.get(mask, 1.0)
    return amp * w * (0.05 * math.sin(TAU * (1.5 * u + 1.2 * v) + 0.4 + ph) + 0.035 * math.sin(TAU * (2.5 * v - 0.7 * u) + 1.1 - ph))


def field(mask, x, y, variant=0, legacy=False):
    """> 0.5 inside the overlay's terrain. legacy: the round-6 field (deep-water edges keep it)."""
    u, v = (x + 0.5) / 32, (y + 0.5) / 32
    nw, ne, sw, se = (1.0 if mask & b else 0.0 for b in (NW, NE, SW, SE))
    f = nw * (1 - u) * (1 - v) + ne * u * (1 - v) + sw * (1 - u) * v + se * u * v
    if legacy:
        return f + wobble(x, y) + inner_wobble(x, y, variant)
    if mask in (6, 9):  # round 8: the same shared wobble as the other masks, so they join their neighbours
        return f + SHARED * wobble(x, y) + inner_wobble(x, y, variant)
    return f + SHARED * wobble(x, y) + inner7(mask, x, y, variant) + side_terms(mask, x, y, variant)


def gradient(mask, x, y):
    """Direction toward the inside of the terrain (from the corners only)."""
    u, v = (x + 0.5) / 32, (y + 0.5) / 32
    nw, ne, sw, se = (1.0 if mask & b else 0.0 for b in (NW, NE, SW, SE))
    return (ne - nw) * (1 - v) + (se - sw) * v, (sw - nw) * (1 - u) + (se - ne) * u


# Edge looks per terrain style. Each returns the overlay canvas from the terrain's ground tile `tex`.
RIM = 0.06  # field band of the rim (about 2 px)


_CLEAN = {}


def clean_inside(mask, variant, legacy=False):
    """Round 8: which pixels are the terrain's, as one piece. The field can leave a small island of terrain or a
    round hole near a corner; a terrain part that does not reach the tile's edge is dropped, and a hole (a
    clear part that does not reach the edge) is filled. Returns (F, inside, dist): the field, the cleaned
    inside, and each pixel's 4-step distance to the inside (capped at 9)."""
    key = (mask, variant, legacy)
    if key in _CLEAN:
        return _CLEAN[key]
    F = [[field(mask, x, y, variant, legacy=legacy) for x in range(32)] for y in range(32)]
    raw = [[F[y][x] > 0.5 for x in range(32)] for y in range(32)]

    def parts(want):
        seen, out = set(), []
        for y in range(32):
            for x in range(32):
                if raw[y][x] != want or (x, y) in seen:
                    continue
                comp, stack = [], [(x, y)]
                seen.add((x, y))
                while stack:
                    p, q = stack.pop()
                    comp.append((p, q))
                    for a, b in ((p + 1, q), (p - 1, q), (p, q + 1), (p, q - 1)):
                        if 0 <= a < 32 and 0 <= b < 32 and (a, b) not in seen and raw[b][a] == want:
                            seen.add((a, b))
                            stack.append((a, b))
                out.append(comp)
        return out

    inside = [row[:] for row in raw]
    for want in (True, False):
        for comp in parts(want):
            if not any(p in (0, 31) or q in (0, 31) for p, q in comp):
                for p, q in comp:
                    inside[q][p] = not want
    dist = [[0 if inside[y][x] else 9 for x in range(32)] for y in range(32)]
    frontier = [(x, y) for y in range(32) for x in range(32) if inside[y][x]]
    for d in range(1, 9):
        nxt = []
        for p, q in frontier:
            for a, b in ((p + 1, q), (p - 1, q), (p, q + 1), (p, q - 1)):
                if 0 <= a < 32 and 0 <= b < 32 and dist[b][a] > d:
                    dist[b][a] = d
                    nxt.append((a, b))
        frontier = nxt
    near = [[False] * 32 for _ in range(32)]  # inside pixels within 3 steps of the clear part (where the rim goes)
    frontier = [(x, y) for y in range(32) for x in range(32) if not inside[y][x]]
    for _ in range(3):
        nxt = []
        for p, q in frontier:
            for a, b in ((p + 1, q), (p - 1, q), (p, q + 1), (p, q - 1)):
                if 0 <= a < 32 and 0 <= b < 32 and inside[b][a] and not near[b][a]:
                    near[b][a] = True
                    nxt.append((a, b))
        frontier = nxt
    _CLEAN[key] = (F, inside, dist, near)
    return _CLEAN[key]


def overlay(tex, mat, mask, variant, style):
    c = Canvas(32, 32, None, wrap=False)
    F, inside, dist, near = clean_inside(mask, variant, legacy=(style == "ruin"))  # ruin: round-6 shapes
    for y in range(32):
        for x in range(32):
            f = F[y][x]
            if not inside[y][x]:
                continue
            c.px[y][x] = tex.px[y][x]
            gx, gy = gradient(mask, x, y)
            lit_side = (gx + gy) > 0.05  # the terrain lies to the lower right: this edge faces up / left
            if 0.5 < f < 0.5 + RIM and near[y][x]:  # (no rim around a filled hole)
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
    if style == "grass":  # tufts over the turf edge: uneven heights (1-3 px), widths and gaps, some leaning
        for y in range(32):
            for x in range(32):
                f = F[y][x]
                if inside[y][x] or dist[y][x] > 2 or not 0.5 - 0.05 < f or x in (0, 31) or y in (0, 31):  # r7: not on the outer ring
                    continue
                r = _rnd(x, y, mask, variant)
                if r > 0.42:
                    continue  # a gap
                h = 1 + int(r * 17) % 3
                lean = (-1, 0, 0, 1)[int(r * 41) % 4]
                gx, gy = gradient(mask, x, y)
                step = -1 if gy >= 0 else 1  # the turf below: blades rise; the turf above: they hang
                xx, yy = x, y
                for k in range(h):
                    if not (1 <= xx < 31 and 1 <= yy < 31) or (k and inside[yy][xx]):
                        break
                    tip = k == h - 1
                    c.put(xx, yy, mat, (5 if tip else 4) if step < 0 else (2 if tip else 3))
                    yy += step
                    if k == 1:
                        xx += lean
        _open_pockets(c, inside)
    return c


def _open_pockets(c, inside):
    """Round 8: tufts may close a clear pocket (in the narrow gap of masks 6 / 9); take the tufts around it away."""
    seen = set()
    for y in range(32):
        for x in range(32):
            if c.px[y][x] is not None or (x, y) in seen:
                continue
            comp, stack, edge = [], [(x, y)], False
            seen.add((x, y))
            while stack:
                p, q = stack.pop()
                comp.append((p, q))
                edge |= p in (0, 31) or q in (0, 31)
                for a, b in ((p + 1, q), (p - 1, q), (p, q + 1), (p, q - 1)):
                    if 0 <= a < 32 and 0 <= b < 32 and (a, b) not in seen and c.px[b][a] is None:
                        seen.add((a, b))
                        stack.append((a, b))
            if edge:
                continue
            for p, q in comp:
                for a in range(p - 2, p + 3):
                    for b in range(q - 2, q + 3):
                        if 0 <= a < 32 and 0 <= b < 32 and not inside[b][a]:
                            c.px[b][a] = None


def _rnd(x, y, mask, variant):
    """A fixed pseudo-random value per pixel, mask and variant (so no two edges show the same row of tufts)."""
    h = (x * 73856093) ^ (y * 19349663) ^ ((mask * 7 + variant * 3 + 1) * 83492791)
    h = (h ^ (h >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65536


STYLE = {"grass": "grass", "plains": "grass", "lake": "grass", "moss": "moss", "snow": "snow", "sand": "sand",
         "dsand": "sand", "path": "path", "ruin": "ruin"}
PRIORITY = ["ruin", "path", "dsand", "sand", "snow", "moss", "lake", "plains", "grass"]  # low -> high (water lowest)
