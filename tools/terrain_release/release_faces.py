"""Release terrain: cliff faces (32 x 8 for `.4`, 32 x 16 for `.8`), wrapping left / right only.

face.earth.* are the approved samples (gen_samples.face_tile). This module adds face.stone (snow
mountains: mount.rock under a snow lip), face.ruin (ruin.stone blocks under a capstone) and face.wall
(house walls: stone cap, timber beam, plaster, skirting board). Shading top -> bottom 3 -> 2 -> 1 and the
last row 0 on `-base` segments (guide 3.4), so stacked segments darken downwards.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from gen_samples import LIP_DEPTH, HANG, LIT_DEPTH, DARK_FROM, LEDGE_DY, LEDGE_GAPS, rel  # noqa: E402
from release_ground import new_tile, tones, slab_rows  # noqa: E402

KINDS = ("top", "mid", "mid-base", "top-base")


def _dims(kind, seg):
    h = 16 if seg == 8 else 8
    return h, kind.startswith("top"), kind.endswith("base"), h == 8


# ---------------------------------------------------------------------------------------------
# face.stone: like the earth face, but grey-violet rock (mount.rock) under a snow lip (mount.snow).
# Details are angular facets and vertical cracks instead of clods.
# ---------------------------------------------------------------------------------------------
FACET = [  # an angular block: lit top-left planes, a shaded lower-right plane (relative)
    "333..",
    "3...1",
    ".1111",
]
FACET_S = [
    "33.",
    "3.1",
    ".11",
]
FACETS = {
    ("top", 16): [(3, 9, FACET_S), (17, 8, FACET), (26, 12, FACET_S)],
    ("top-base", 16): [(6, 9, FACET), (22, 8, FACET_S)],
    ("mid", 16): [(2, 2, FACET), (19, 3, FACET_S), (9, 12, FACET_S), (25, 11, FACET)],
    ("mid-base", 16): [(12, 1, FACET), (27, 3, FACET_S), (2, 10, FACET_S)],
    ("top", 8): [(20, 5, FACET_S)],
    ("top-base", 8): [],
    ("mid", 8): [(5, 1, FACET_S), (21, 2, FACET)],
    ("mid-base", 8): [(14, 1, FACET_S)],
}
CRACKS = [(7, 1, 4), (15, 3, 3), (30, 0, 4)]  # (x, y, length): a lit edge on the left of a dark crack
SNOW_LIP = [3, 3, 4, 4, 3, 2, 3, 3, 4, 5, 4, 3, 3, 3, 4, 4, 3, 3, 4, 3, 2, 3, 3, 4, 5, 5, 4, 3, 3, 4, 3, 3]
SNOW_HANG = {5: 1, 10: 2, 18: 1, 25: 2, 29: 1}  # drips of snow over the edge


def stone_face(kind, seg):
    h, is_top, is_base, short = _dims(kind, seg)
    t = new_tile(32, h, base=None, wrap_y=False)
    lip_d = [max(2, d - 1) for d in SNOW_LIP] if short else SNOW_LIP
    for x in range(32):
        for y in range(h):
            tone = 2
            if is_top:
                start = lip_d[x] + SNOW_HANG.get(x, 0) + 1
                if y < start + LIT_DEPTH[x] - (1 if short else 0):
                    tone = 3
            if is_base:
                dark_from = DARK_FROM[x] if not short else DARK_FROM[x] // 2 + 1
                if is_top and short:
                    dark_from = max(dark_from, 6)
                if y >= dark_from:
                    tone = 1
                if y == h - 1:
                    tone = 0
            t.put(x, y, "mount.rock", tone)
    r = rel()
    if not (is_top and short):
        ledge = (12 if is_top else 11) if h == 16 else 4
        for x in range(32):
            if x in LEDGE_GAPS:
                continue
            y = ledge + (1 if LEDGE_DY[x] > 0 else 0)  # rock strata: flatter than earth
            if y + 1 < h - (1 if is_base else 0):
                t.shift(x, y, +1, lo=1, hi=3)
                t.shift(x, y + 1, -1, lo=1, hi=3)
    for x, y, p in FACETS[(kind, h)]:
        t.stamp(x, y, p, r)
    if not is_top:
        for x, y0, n in CRACKS:
            if y0 + n >= h - 1:
                n = h - 2 - y0
            for k in range(n):
                t.shift(x, y0 + k, -1, lo=1)
                t.shift(x - 1, y0 + k, +1, hi=3)
    if is_top:
        for x in range(32):
            d = lip_d[x]
            for y in range(d):
                t.put(x, y, "mount.snow", 4 if (y == 0 and x % 9 in (2, 3)) else 3 if y < 2 else 2 if y < d - 1 else 1)
            for k in range(SNOW_HANG.get(x, 0)):
                t.put(x, d + k, "mount.snow", 2 if k == 0 else 1)
            t.put(x, d + SNOW_HANG.get(x, 0), "mount.rock", 1)
    return t


# ---------------------------------------------------------------------------------------------
# face.ruin: ruin.stone blocks (courses of 7-8 px) under a lit capstone. A carved groove on mid.8.
# ---------------------------------------------------------------------------------------------
RUIN_COURSES = {  # (y0, height, start x, widths) per segment
    ("top", 16): [(3, 7, 5, [14, 18]), (10, 6, 13, [16, 16])],
    ("top-base", 16): [(3, 7, 9, [12, 20]), (10, 6, 1, [18, 14])],
    ("mid", 16): [(0, 8, 3, [17, 15]), (8, 8, 11, [13, 19])],
    ("mid-base", 16): [(0, 8, 7, [15, 17]), (8, 8, 15, [18, 14])],
    ("top", 8): [(3, 5, 6, [16, 16])],
    ("top-base", 8): [(3, 5, 12, [14, 18])],
    ("mid", 8): [(0, 8, 9, [19, 13])],
    ("mid-base", 8): [(0, 8, 2, [13, 19])],
}


def ruin_face(kind, seg):
    h, is_top, is_base, short = _dims(kind, seg)
    t = new_tile(32, h, base=("ruin.stone", 2), wrap_y=False)
    slab_rows(t, "ruin.stone", RUIN_COURSES[(kind, h)], joint=0)
    if is_top:
        for x in range(32):
            t.put(x, 0, "ruin.stone", 4 if x % 11 in (3, 4) else 3)
            t.put(x, 1, "ruin.stone", 3)
            t.put(x, 2, "ruin.stone", 0)  # under the capstone's overhang
        for x in range(32):  # lit band right under the cap (3 -> 2 -> 1 from top to bottom)
            if t.tone_of(x, 4) == 2:
                t.put(x, 4, "ruin.stone", 3)
    if is_base:
        for x in range(32):
            for y in range(max(3, h - 4), h - 1):
                t.shift(x, y, -1, lo=1)
            t.put(x, h - 1, "ruin.stone", 0)
    if (kind, h) == ("mid", 16):  # a carved line motif (the lamp-folk): groove (1) with a lit lower lip (3)
        for x, y in [(22, 3), (23, 3), (24, 3), (24, 4), (24, 5), (25, 5), (26, 5)]:
            t.put(x, y, "ruin.stone", 1)
            t.put(x, y + 1, "ruin.stone", 3)
    return t


# ---------------------------------------------------------------------------------------------
# face.wall: house walls. Stone cap (wall.stone, matching tile.walltop), timber beam (wood),
# plaster (room.plaster) with a few worn patches, skirting board (wood) at the base.
# ---------------------------------------------------------------------------------------------
PLASTER_MARKS = {  # short worn streaks in the plaster (a lit edge over a shaded one, 3-4 px)
    ("top", 16): [(6, 11, "3331"), (21, 13, "331")],
    ("top-base", 16): [(14, 8, "3311")],
    ("mid", 16): [(4, 3, "333"), (19, 6, "3311"), (11, 11, "1133"), (27, 12, "331")],
    ("mid-base", 16): [(8, 2, "3311"), (24, 5, "333")],
    ("top", 8): [],
    ("top-base", 8): [],
    ("mid", 8): [(13, 2, "3311"), (26, 4, "331")],
    ("mid-base", 8): [(20, 1, "1133")],
}
BEAM_JOINT = 19  # where two beams meet (x)


def wall_face(kind, seg):
    h, is_top, is_base, short = _dims(kind, seg)
    t = new_tile(32, h, base=("room.plaster", 2), wrap_y=False)
    y = 0
    if is_top:
        for x in range(32):
            t.put(x, 0, "stone", 3)
            t.put(x, 1, "stone", 2)
            t.put(x, 2, "stone", 0)
        beam = [3, 2, 1] if not short else [3, 1]
        if short and is_base:
            beam = [3, 1]
        for k, tn in enumerate(beam):
            for x in range(32):
                t.put(x, 3 + k, "wood", tn)
        for k in range(len(beam)):
            t.put(BEAM_JOINT, 3 + k, "wood", 0)
        y = 3 + len(beam)
        for x in range(32):
            t.put(x, y, "room.plaster", 1)  # the beam's shadow on the plaster
            for yy in range(y + 1, min(h, y + 3)):
                t.put(x, yy, "room.plaster", 3)  # lit band
    for x, yy, mark in PLASTER_MARKS[(kind, h)]:
        for k, ch in enumerate(mark):
            t.put(x + k, yy, "room.plaster", int(ch))
    if is_base:
        skirt = [3, 2, 1, 0] if h == 16 or not is_top else [3, 0]
        y0 = h - len(skirt)
        for x in range(32):
            t.put(x, y0 - 1, "room.plaster", 1)
            for k, tn in enumerate(skirt):
                t.put(x, y0 + k, "wood", tn)
    return t
