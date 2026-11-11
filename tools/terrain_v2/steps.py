"""Ground v2, round 7: one-level step edges drawn as a rim instead of a 1-px line (NAMES.md section 5).

The engine draws an elevated cell's surface square on the cell grid, then (v1) a 1-px dark line on its east,
west and north sides where the neighbour is lower and a translucent strip of shadow on the lower ground to the
east. These overlays replace the lines and the strip:

  <prefix>.step.<mask>.<v>   on the HIGH cell, over its surface (same position, 32 x 32 art px = 1 cell).
                             mask = the sides whose neighbour is lower: N 1, E 2, W 4 (1-7); v = 0 / 1.
                             An outline 0-3 px deep that swells and thins along the side (round 8: the lightest tone 28+ darker than the core), and inside it
                             the rim: lit (tones 5 / 4) on the north and west sides, which face the light, in
                             shade (tone 2) on the east side.
  <prefix>.step.shade.<v>    on the LOW cell east of a higher cell, over its ground (the cell's own position):
                             the shadow the step casts, 2-8 px wide (4-9 px on moss, autumn moss, path, ruin) with a wavy edge (round 8: the lightest tone 15+ darker
                             than the core; its foot in the outline's tone).

The depth of the outline / rim / shadow along a side is a 32-periodic function of the position along it (so
a straight step joins from cell to cell) plus, for v = 1, a bump that is 0 at the cell's corners.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from canvas import RGB, Canvas  # noqa: E402


def _lum(mat, t):
    r, g, b = RGB[mat][t]
    return 0.299 * r + 0.587 * g + 0.114 * b


def dark_tone(mat, need):
    """Round 8: the lightest tone of the ramp at least `need` (0-255 lightness) darker than the core (3), so the
    step reads on every ground (the outline: 28, the shadow and the shaded east rim: 15)."""
    return max(t for t in range(3) if _lum(mat, t) - _lum(mat, 3) <= -need) if _lum(mat, 0) - _lum(mat, 3) <= -need else 0

N, E, W = 1, 2, 4
TAU = 2 * math.pi


def _depth(t, side, variant, base, amp):
    """Depth (px) of a band along a side at position t (0-31 along it)."""
    a = TAU * (t + 0.5) / 32
    ph = {"N": 0.4, "E": 2.1, "W": 4.0, "S": 1.0}[side]
    d = base + amp * (0.55 * math.sin(a + ph) + 0.3 * math.sin(2 * a + 2 * ph + 1.3) + 0.15 * math.sin(3 * a + ph))
    if variant:
        d += amp * 0.9 * math.sin(math.pi * (t + 0.5) / 32) ** 2 * math.sin(TAU * (t + 0.5) / 32 * 1.5 + ph)
    return d


OUTLINE, SHADE = 28, 15


def step_overlay(mat, mask, variant):
    c = Canvas(32, 32, None, wrap=False)
    t_out, t_sh = min(1, dark_tone(mat, OUTLINE)), dark_tone(mat, SHADE)  # outline: never lighter than tone 1 (r7)
    sides = [sd for sd, bit in (("N", N), ("E", E), ("W", W)) if mask & bit]
    for y in range(32):
        for x in range(32):
            best = None
            for sd in sides:
                t, d = {"N": (x, y), "E": (y, 31 - x), "W": (y, x)}[sd]
                out = _depth(t, sd, variant, 1.3, 1.7)  # the outline: 0-3 px (it breaks off here and there)
                rim = max(out, 0) + _depth(t + 7, sd, variant, 2.6, 1.5)  # the rim inside it: 1-4 px more
                if d < out:
                    tone = t_out
                elif d < rim:
                    tone = t_sh if sd == "E" else (5 if d < out + 1 else 4)
                else:
                    continue
                if best is None or (tone == t_out) > (best == t_out):
                    best = tone
            if best is not None:
                c.put(x, y, mat, best)
    return c


def shade_overlay(mat, variant):
    c = Canvas(32, 32, None, wrap=False)
    t_out, t_sh = min(1, dark_tone(mat, OUTLINE)), dark_tone(mat, SHADE)  # outline: never lighter than tone 1 (r7)
    wide = 1.5 if _lum(mat, t_sh) - _lum(mat, 3) > -20 else 0.0  # round 9: moss / autumn moss / ruin shadows a column wider
    for y in range(32):
        for x in range(32):
            w = _depth(y, "S", variant, 5.0 + wide, 3.0)  # 2-8 px from the west side (+1.5 where the shadow tone is lighter: 4-9 px)
            if x < w:
                c.put(x, y, mat, t_out if x < 1 else t_sh)
    return c


def inner_corner(mat, corner):
    """Round 8: the piece for an inner corner of a step, on the cell whose two neighbours on that corner's sides
    are high (not lower) but whose diagonal neighbour there is lower: ne = north and east high, NE lower; nw =
    north and west high, NW lower. It joins the end of the north rim of the east (west) neighbour and the end
    of the east (west) rim of the north neighbour, which do not depend on the variant at the cells' corners."""
    c = Canvas(32, 32, None, wrap=False)
    t_out, t_sh = min(1, dark_tone(mat, OUTLINE)), dark_tone(mat, SHADE)  # outline: never lighter than tone 1 (r7)
    if corner == "ne":  # the north rim of the east cell at its t = 0, the east rim of the north cell at its t = 31
        out_a, rim_a = _depth(0, "N", 0, 1.3, 1.7), _depth(7, "N", 0, 2.6, 1.5)
        out_b, rim_b = _depth(31, "E", 0, 1.3, 1.7), _depth(38, "E", 0, 2.6, 1.5)
    else:
        out_a, rim_a = _depth(31, "N", 0, 1.3, 1.7), _depth(38, "N", 0, 2.6, 1.5)
        out_b, rim_b = _depth(31, "W", 0, 1.3, 1.7), _depth(38, "W", 0, 2.6, 1.5)
    for y in range(32):
        for x in range(32):
            dx = 31 - x if corner == "ne" else x  # from the side the other rim runs along
            if y < max(out_a, 0.6) and dx < max(out_b, 0.6):
                c.put(x, y, mat, t_out)
            elif y < max(out_a, 0) + rim_a and dx < max(out_b, 0) + rim_b:
                c.put(x, y, mat, t_sh if corner == "ne" and dx < y else (5 if min(y, dx) < 1 else 4))
    return c


def step_tiles(mat):
    """{internal suffix: canvas}: step<mask>.<v>, stepshade.<v>, stepinner.<ne|nw> (round 8)."""
    out = {f"step{m}.{v}": step_overlay(mat, m, v) for m in range(1, 8) for v in (0, 1)}
    out.update({f"stepinner.{k}": inner_corner(mat, k) for k in ("ne", "nw")})
    out.update(step2_tiles(mat))  # round 10
    out.update({f"stepshade.{v}": shade_overlay(mat, v) for v in (0, 1)})
    return out


# ------------------------------------------------------------------------------------------------------
# Round 10: step2 — the step line moved off the cell's edges (NAMES.md 2c).
#
# The visible step is the rim line; it now runs INSIDE the high cell, at a depth that is set at every cell
# corner (vertex) by a hash: state 0 -> 3 px, state 1 -> 9 px from the edge, blended along the side with a
# small wave that is 0 at the corners (east side: 6 / 12 px). A straight terrace therefore wanders in and out
# by about 6 px from corner to corner instead of following the cell edges, and two cells sharing a corner
# agree on the depth there. Convex (outer) corners are rounded (radius 6 px). The band between the rim and the
# cell's edge is left clear (it reads as the lower ground), except on the east side, where a 2.5-4.5 px wavy
# shadow follows the rim (stopping short of the cell's edge), so the shadow is on the high cell itself and
# always shows (round 10, R2).
#   <prefix>.step2.<mask>.<code>      mask = N 1, E 2, W 4 (sides whose neighbour is lower); code = the
#                                     states of the corners those sides touch, in the order NW, NE, SE, SW,
#                                     bit k = state of the k-th of them
#   <prefix>.step2.inner.<ne|nw>.<s>  an inner corner (as step.inner) with the state s of that corner
# ------------------------------------------------------------------------------------------------------
VERT_D = {"N": (3.0, 9.0), "W": (3.0, 9.0), "E": (6.0, 12.0)}  # rim depth at a corner of state 0 / 1, per side
SHADOW_W = 3.5  # the east shadow band: 2.5-4.5 px from the rim line (it stops short of the cell's edge)
ROUND = 6.0  # radius of the rounded outer corners
OUT_W, RIM_W = 1.6, 2.6  # outline and rim band widths
CORNERS = ("NW", "NE", "SE", "SW")
SIDE_CORNERS = {"N": ("NW", "NE"), "E": ("NE", "SE"), "W": ("NW", "SW")}


def step2_corners(mask):
    """The corners whose state matters for a mask, in the order NW, NE, SE, SW."""
    used = set()
    for sd, bit in (("N", N), ("E", E), ("W", W)):
        if mask & bit:
            used.update(SIDE_CORNERS[sd])
    return [c for c in CORNERS if c in used]


def _smooth(t):
    return t * t * (3 - 2 * t)


def _side_depth(sd, t, s0, s1):
    """Depth of the rim line on a side at t (0-1 from its first corner), its corners in states s0, s1."""
    ph = {"N": 0.3, "E": 1.9, "W": 3.7}[sd]
    wave = 2.2 * math.sin(math.pi * t) * math.sin(2 * math.pi * 1.4 * t + ph)
    d0, d1 = VERT_D[sd][s0], VERT_D[sd][s1]
    return d0 + (d1 - d0) * _smooth(t) + wave


def step2_overlay(mat, mask, code):
    c = Canvas(32, 32, None, wrap=False)
    t_out, t_sh = min(1, dark_tone(mat, OUTLINE)), dark_tone(mat, SHADE)
    corners = step2_corners(mask)
    st = {k: (code >> i) & 1 for i, k in enumerate(corners)}
    sides = [sd for sd, bit in (("N", N), ("E", E), ("W", W)) if mask & bit]
    for y in range(32):
        for x in range(32):
            # signed distance into the high part from each lowered side's rim line
            vals = {}
            for sd in sides:
                a, b = SIDE_CORNERS[sd]
                if sd == "N":
                    vals[sd] = (y + 0.5) - _side_depth(sd, (x + 0.5) / 32, st[a], st[b])
                elif sd == "E":
                    vals[sd] = (31.5 - x) - _side_depth(sd, (y + 0.5) / 32, st[a], st[b])
                else:
                    vals[sd] = (x + 0.5) - _side_depth(sd, (y + 0.5) / 32, st[a], st[b])
            dist = min(vals.values())
            near = min(vals, key=vals.get)
            # rounded outer corners: two sides both closer than ROUND
            for p, q in (("N", "E"), ("N", "W")):
                if p in vals and q in vals and vals[p] < ROUND and vals[q] < ROUND and vals[p] > -ROUND and vals[q] > -ROUND:
                    r = math.hypot(ROUND - vals[p], ROUND - vals[q])
                    if vals[p] >= 0 and vals[q] >= 0:
                        dist = min(dist, ROUND - r)
                    if dist < 0:
                        near = q if vals[q] < vals[p] else p
            if dist < 0:
                if near == "E" and dist > -(SHADOW_W + math.sin((y + 0.5) / 3.1 + code) * 1.0):
                    c.put(x, y, mat, t_sh)  # the step's shadow, on the high cell's east band
                continue
            if dist < OUT_W:
                c.put(x, y, mat, t_out)
            elif dist < OUT_W + RIM_W:
                c.put(x, y, mat, t_sh if near == "E" else (5 if dist < OUT_W + 1 else 4))
    return c


def step2_inner(mat, corner, s):
    """An inner corner (the high cell's two side neighbours there are not lower, its diagonal one is): the rim
    turns around the corner on a quarter ellipse, from the end of the north neighbour's east (west) rim to the
    start of the east (west) neighbour's north rim. ne: the shadow band of the east rim comes round it."""
    c = Canvas(32, 32, None, wrap=False)
    t_out, t_sh = min(1, dark_tone(mat, OUTLINE)), dark_tone(mat, SHADE)
    rx = VERT_D["E" if corner == "ne" else "W"][s]  # across: the depth of the side rim coming down from the north
    ry = VERT_D["N"][s]  # down: the depth of the north rim going on to the side
    cx = 32.0 if corner == "ne" else 0.0
    for y in range(32):
        for x in range(32):
            u, v = abs(x + 0.5 - cx) / rx, (y + 0.5) / ry
            q = math.hypot(u, v)
            dist = (q - 1) * min(rx, ry)  # roughly px from the arc, positive on the high side
            east_like = corner == "ne" and u * rx > v * ry * 0.6
            if dist < 0:
                if east_like and dist > -SHADOW_W:
                    c.put(x, y, mat, t_sh)
            elif dist < OUT_W:
                c.put(x, y, mat, t_out)
            elif dist < OUT_W + RIM_W:
                c.put(x, y, mat, t_sh if east_like else 4)
    return c


def step2_tiles(mat):
    out = {}
    for m in range(1, 8):
        for code in range(2 ** len(step2_corners(m))):
            out[f"steptwo{m}.{code}"] = step2_overlay(mat, m, code)
    for k in ("ne", "nw"):
        for s in (0, 1):
            out[f"steptwoinner{k}.{s}"] = step2_inner(mat, k, s)
    return out
