"""Ground v2, round 7: one-level step edges drawn as a rim instead of a 1-px line (NAMES.md section 5).

The engine draws an elevated cell's surface square on the cell grid, then (v1) a 1-px dark line on its east,
west and north sides where the neighbour is lower and a translucent strip of shadow on the lower ground to the
east. These overlays replace the lines and the strip:

  <prefix>.step.<mask>.<v>   on the HIGH cell, over its surface (same position, 32 x 32 art px = 1 cell).
                             mask = the sides whose neighbour is lower: N 1, E 2, W 4 (1-7); v = 0 / 1.
                             An outline 0-3 px deep that swells and thins along the side (tone 1), and inside it
                             the rim: lit (tones 5 / 4) on the north and west sides, which face the light, in
                             shade (tone 2) on the east side.
  <prefix>.step.shade.<v>    on the LOW cell east of a higher cell, over its ground (the cell's own position):
                             the shadow the step casts, 2-8 px wide with a wavy edge (tone 2, its foot tone 1).

The depth of the outline / rim / shadow along a side is a 32-periodic function of the position along it (so
a straight step joins from cell to cell) plus, for v = 1, a bump that is 0 at the cell's corners.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from canvas import Canvas  # noqa: E402

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


def step_overlay(mat, mask, variant):
    c = Canvas(32, 32, None, wrap=False)
    sides = [sd for sd, bit in (("N", N), ("E", E), ("W", W)) if mask & bit]
    for y in range(32):
        for x in range(32):
            best = None
            for sd in sides:
                t, d = {"N": (x, y), "E": (y, 31 - x), "W": (y, x)}[sd]
                out = _depth(t, sd, variant, 1.3, 1.7)  # the outline: 0-3 px (it breaks off here and there)
                rim = max(out, 0) + _depth(t + 7, sd, variant, 2.6, 1.5)  # the rim inside it: 1-4 px more
                if d < out:
                    tone = 1
                elif d < rim:
                    tone = 2 if sd == "E" else (5 if d < out + 1 else 4)
                else:
                    continue
                if best is None or (tone == 1) > (best == 1):
                    best = tone
            if best is not None:
                c.put(x, y, mat, best)
    return c


def shade_overlay(mat, variant):
    c = Canvas(32, 32, None, wrap=False)
    for y in range(32):
        for x in range(32):
            w = _depth(y, "S", variant, 5.0, 3.0)  # 2-8 px from the west side
            if x < w:
                c.put(x, y, mat, 1 if x < 1 else 2)
    return c


def step_tiles(mat):
    """{internal suffix: canvas}: step<mask>.<v> and stepshade.<v>."""
    out = {f"step{m}.{v}": step_overlay(mat, m, v) for m in range(1, 8) for v in (0, 1)}
    out.update({f"stepshade.{v}": shade_overlay(mat, v) for v in (0, 1)})
    return out
