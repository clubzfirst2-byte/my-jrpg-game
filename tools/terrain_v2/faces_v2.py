"""Ground v2, round 3: the cliff faces redrawn under their v1 keys (same sizes: 32 x 16 for `.8`, 32 x 8 for
`.4`; same stacking: top, mid..., mid-base, or top-base alone; same variants: plain, .v1, .v2).

  face.earth.*   brown earth under a turf lip (autumn.* / winter.*: the lip in the season's colours)
  face.stone.*   grey-violet rock under a snow lip (autumn.*: the snow with bare stretches of dry grass)
  face.sand.*    tan sandstone under the beach sand        } plateau faces: a thin lip of the ground on top,
  face.desert.*  brown earth under the red desert sand     } plain / .v1 only
  face.path.*    brown earth under the path's dirt         }
(face.ruin.* and face.wall.* are masonry / house walls: not redrawn, copied from v1.)

The v1 faces were a flat band with evenly spaced dots. Here a face is built of CHUNKS (clods of earth, blocks
of rock) in strata: irregular vertical cracks, a wandering crack between the two strata of a 16-px segment,
every chunk lit on its top edge and shaded on its bottom / right edge, the whole face darkening downwards
(tone 4 under the lip, 3, then 2 and a dark foot on `-base` segments) with a shadow under the lip.
Details by variant: small ledges, a stone in the earth here and there, roots under the turf, a long crack in the rock.

Variants join each other: the chunk that crosses the tile's left / right edge, the wandering crack and the lip
are the same in every variant for 3 px from the edges; the rest differs.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from canvas import Canvas  # noqa: E402

KINDS = ("top", "mid", "mid-base", "top-base")
# name: (body ramp, lip ramp, style, lip kind, variants)
MATS = {
    "earth": ("earth", "grass", "earth", "turf", 3),
    "stone": ("rock", "snow", "stone", "snow", 3),
    "sand": ("dstone", "sand", "earth", "thin", 2),
    "desert": ("earth", "dsand", "earth", "thin", 2),
    "path": ("earth", "path", "earth", "thin", 2),
}
LIP = [3, 4, 4, 3, 5, 4, 3, 3, 4, 5, 5, 4, 3, 4, 4, 3, 3, 5, 4, 4, 3, 3, 4, 5, 5, 4, 3, 4, 3, 3, 4, 4]
WANDER = [0, 0, 0, 1, 1, 1, 0, 0, -1, -1, 0, 0, 1, 1, 1, 0, 0, 0, -1, -1, -1, 0, 0, 1, 1, 0, 0, -1, -1, 0, 0, 0]


def _h(*vals):
    h = 2166136261
    for v in vals:
        h = ((h ^ (v & 0xFFFF)) * 16777619) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return h ^ (h >> 16)


def _shared(x):
    return x < 3 or x > 28


def lip_depth(x, var, short, lipkind):
    d = LIP[x] if _shared(x) else LIP[(x + 11 * var) % 32]
    if lipkind == "thin":
        d = 2 + (d - 3) // 2
    elif short:
        d = max(2, d - 1)
    return d


def hang(x, var, lipkind):
    """Blades / drips hanging below the lip (0-2 px), never on the shared columns."""
    if lipkind == "thin" or _shared(x) or _shared(x + 1) or _shared(x - 1):
        return 0
    r = _h(x, var, 5) % 16
    return 2 if r == 0 else 1 if r < 4 else 0


def base_tone(kind, h, x, y):
    j = (WANDER[(x * 3 + 5) % 32] + 1) // 2  # the tone steps follow a ragged line
    if kind == "top":
        return 4 if y < (10 if h == 16 else 6) + j else 3
    if kind == "mid":
        return 3
    if kind == "mid-base":
        if h == 16:
            return 3 if y < 8 + j else 2 if y < 14 else 1 if y == 14 else 0
        return 3 if y < 2 + j else 2 if y < 6 else 1 if y == 6 else 0
    if h == 16:  # top-base
        return 4 if y < 8 + j else 3 if y < 11 + j else 2 if y < 14 else 1 if y == 14 else 0
    return 4 if y < 5 else 3 if y == 5 else 1 if y == 6 else 0


def bands_of(kind, h):
    """(first row, last row) of each stratum of chunks; a 16-px segment below the top has two."""
    top, base = kind.startswith("top"), kind.endswith("base")
    last = h - 2 if base else h - 1
    if top:
        return [(0, last)]
    if h == 16:
        return [(0, 7), (8, last)]
    return [(0, last)]


def cracks(kind, h, var, band, y0, y1, style):
    """The vertical cracks of a stratum: {x: lean seed}. The chunk crossing the tile edge is the same in every
    variant (its cracks at B and 32 - A)."""
    k = KINDS.index(kind)
    a = 4 + _h(k, h, band, 1) % 5  # 4-8 px of the crossing chunk on the left of the edge
    b = 4 + _h(k, h, band, 2) % 5
    xs = [b]
    x = b
    seed = 0
    while True:
        w = (9 if style == "earth" else 7) + _h(k, h, band, var, seed, 3) % 7
        seed += 1
        if x + w > 32 - a - 5:
            break
        x += w
        xs.append(x)
    xs.append(32 - a)
    return xs


def face(mat, kind, seg, var=0, season=None):
    body, lipmat, style, lipkind, _ = MATS[mat]
    h = 16 if seg == 8 else 8
    short = h == 8
    is_top, is_base = kind.startswith("top"), kind.endswith("base")
    k = KINDS.index(kind)
    c = Canvas(32, h, None, wrap=False)
    if season == "winter" and mat == "earth":
        lipmat, lipkind = "snow", "snow"
    # --- the lip's lower edge per column (the body starts under it)
    lip = [0] * 32
    hg = [0] * 32
    if is_top:
        for x in range(32):
            lip[x] = lip_depth(x, var, short, lipkind)
            hg[x] = hang(x, var, lipkind)
    # --- cracks
    crack = [[False] * 32 for _ in range(h)]
    bands = bands_of(kind, h)
    split = {}
    xs_of = [cracks(kind, h, var, bi, y0, y1, style) for bi, (y0, y1) in enumerate(bands)]
    tall = []  # x ranges where a chunk is as tall as both strata (no crack between them, none under it)
    if len(bands) == 2:  # the wandering crack between the two strata
        base_row = 6 + _h(k, h, 6) % 3
        xs = xs_of[0]
        tall = [(xs[n] + 1, xs[n + 1] - 1) for n in range(1, len(xs) - 2) if _h(k, h, var, n, 7) % 3 == 0]
        for x in range(32):
            w = WANDER[x] if _shared(x) else WANDER[(x + 9 * var + 7 * k) % 32] + (WANDER[(x * 2 + 5 * var) % 32] > 0)
            split[x] = base_row + w
            if any(a - 1 <= x <= b + 1 for a, b in tall):
                continue
            if _h(x // 3, 0 if _shared(x) else var + 1, k, 9) % 4:  # with gaps
                crack[split[x]][x] = True
    for bi, (y0, y1) in enumerate(bands):
        xs = xs_of[bi]
        for n, xb in enumerate(xs):
            shared = n in (0, len(xs) - 1)
            if bi == 1 and not shared and any(a - 2 <= xb <= b + 2 for a, b in tall):
                continue
            s = _h(k, h, bi, 0 if shared else var + 1, n, 4)
            lean = ((s % 5) - 2) * (0.16 if style == "earth" else 0.14)
            ymid = (y0 + y1) / 2
            ya, yb = y0 + (s >> 6) % 3, y1 - (s >> 9) % (4 if style == "earth" else 2)  # a crack does not always run the whole stratum
            for y in range(ya, yb + 1):
                sp = split.get(min(31, max(0, xb)), 7)
                if len(bands) == 2 and ((bi == 0 and y > sp) or (bi == 1 and y < sp)):
                    continue
                if is_top and y <= lip[min(31, max(0, xb))] + 1:
                    continue
                x = round(xb + lean * (y - ymid) + (0.6 if (s >> 4) % 3 == 0 and y > ymid else 0))
                if 3 <= x <= 28 and not (style == "earth" and (s >> 8) % 4 == 0 and y == y0):
                    crack[y][x] = True
    # --- tones
    for y in range(h):
        for x in range(32):
            b = base_tone(kind, h, x, y)
            if is_top and y < lip[x] + hg[x]:
                continue  # the lip (drawn below)
            if b == 0 or (is_base and y == h - 1):
                c.put(x, y, body, 0)
                continue
            under_lip = is_top and y == lip[x] + hg[x]
            cr = crack[y][x]
            vx = 0 if _shared(x) else var + 1
            up = (y > 0 and crack[y - 1][x]) or (y == 0 and not is_top and _h(x // 3, vx, k, 11) % 5 < 2)
            down = (y + 1 < h and crack[y + 1][x]) or (y == h - 1 and not is_base and _h(x // 3, vx, k, 12) % 5 < 2)
            left = x > 0 and crack[y][x - 1]
            right = x < 31 and crack[y][x + 1]
            if under_lip:
                t = 1  # the lip's shadow
            elif cr:
                deep = style == "stone" or (y + 1 < h and not crack[y + 1][x]) or (x + y) % 4 == 0
                t = b - 2 if deep else b - 1  # earth: a soft groove, deep only at its foot
            elif up or (style == "stone" and left):
                t = b + 1
            elif down or right:
                t = b - 1
            else:
                t = b
                r = _h(x, y, vx, k, h, 21) % (90 if style == "earth" else 120)
                if r == 0:
                    t = b - 1  # a pit
                elif r == 1 and y > 0 and not crack[y - 1][x]:
                    t = b + 1  # a lit grain
            c.put(x, y, body, max(0 if is_base and y >= h - 3 else 1, min(5, t)))
    if style == "stone":  # a second lit row on the top of the wider blocks (a ledge), a facet line under it
        for y in range(1, h - 1):
            for x in range(1, 31):
                v = c.get(x, y)
                if v and v[0] == body and crack[y - 1][x] is False and y >= 2 and crack[y - 2][x] and _h(x // 4, y, var, k, 31) % 3 == 0:
                    if not crack[y][x] and not (is_top and y <= lip[x] + hg[x]):
                        c.put(x, y, body, min(5, base_tone(kind, h, x, y) + 1))
    details(c, mat, body, style, kind, h, var, crack, lip, hg)
    if is_base:  # rubble at the foot: a few lit crumbs on the dark rows
        for n in range(3):
            x = 3 + _h(n, var, k, h, 41) % 25
            c.put(x, h - 2, body, 3)
            c.put(x + 1, h - 2, body, 2)
    if is_top:
        draw_lip(c, lipmat, lipkind, lip, hg, var, k, season, mat)
    return c


def details(c, mat, body, style, kind, h, var, crack, lip, hg):
    is_top = kind.startswith("top")
    k = KINDS.index(kind)

    def free(x0, y0, w, hh):
        for y in range(y0 - 1, y0 + hh + 1):
            for x in range(x0 - 1, x0 + w + 1):
                if not (3 <= x <= 28 and 0 <= y < h) or crack[y][x] or (is_top and y <= lip[x] + hg[x] + 1):
                    return False
                v = c.get(x, y)
                if not v or v[1] < 2:
                    return False
        return True

    def place(seed, w, hh):
        for n in range(24):
            x, y = 4 + _h(seed, n, var, k, h, 51) % 22, 1 + _h(seed, n, var, k, h, 52) % max(1, h - hh - 2)
            if free(x, y, w, hh):
                return x, y
        return None

    if style == "earth":  # small ledges: a lit run with a shade under it (the strata show inside the clods)
        for n in range(3 if h == 16 else 1):
            w = 3 + _h(n, var, k, h, 55) % 4
            p = place(40 + n, w, 2)
            if p:
                x, y = p
                for dx in range(w):
                    v = c.get(x + dx, y)
                    c.put(x + dx, y, body, min(5, v[1] + 1))
                    c.put(x + dx, y + 1, body, max(1, v[1] - 1))
    if style == "earth" and h == 16 and (var, kind) in ((1, "mid"), (2, "mid-base"), (0, "top-base")):
        stone = "pebble" if mat != "sand" else "dstone"
        for n in range(1):  # a stone in the earth: lit top-left, a shade under it
            p = place(60 + n, 4, 3)
            if p:
                x, y = p
                rows = [".54.", "5432", ".21."] if (n + var) % 2 == 0 else ["54.", "432"]
                c.stamp(x, y, rows, stone)
                for dx in range(1, len(rows[0])):
                    v = c.get(x + dx, y + len(rows))
                    if v and v[0] == body:
                        c.put(x + dx, y + len(rows), body, max(1, v[1] - 1))
    if style == "earth" and is_top and mat == "earth" and var in (1, 2) and h == 16:  # roots hanging out under the turf
        for n in range(2):
            x = 6 + _h(n, var, 71) % 20
            y = lip[x] + hg[x] + 1
            for i in range(3 + _h(n, var, 72) % 3):
                xx = x + (0, 0, 1, 1, 0)[i]
                if 3 <= xx <= 28 and y + i < h - 1:
                    c.put(xx, y + i, "bark", 4 if i < 2 else 3)
    if style == "stone" and not is_top:  # a long crack down a block
        p = place(90, 2, 5 if h == 16 else 3)
        if p:
            x, y = p
            for i in range(5 if h == 16 else 3):
                xx = x + (0, 0, 1, 1, 1)[i]
                v = c.get(xx, y + i)
                c.put(xx, y + i, body, max(1, v[1] - 2))
                c.put(xx - 1, y + i, body, min(5, v[1] + 1))


def draw_lip(c, mat, kind, lip, hg, var, k, season, face_mat):
    for x in range(32):
        d = lip[x]
        for y in range(d):
            if kind == "turf":  # lit edge of the turf, its body, its shaded underside
                t = (5 if _h(x, 0 if _shared(x) else var + 1, 101) % 4 == 0 else 4) if y == 0 else 3 if y < d - 1 else 2
            elif kind == "snow":  # a rounded cushion: bright top, soft shade under it
                t = (6 if x % 9 in (2, 3) else 5) if y == 0 else 5 if y == 1 and d > 3 else 4 if y < d - 1 else 2
            else:  # a thin lip of sand / dirt
                t = 5 if y == 0 else 3 if y < d - 1 or d == 2 else 2
            c.put(x, y, mat, t)
        for i in range(hg[x]):  # blades / drips hanging over the edge
            c.put(x, d + i, mat, (3 if kind == "snow" else 2) if i == 0 else (2 if kind == "snow" else 1))
    if kind == "turf":  # a few blades standing over the edge row (lighter tips)
        for n in range(4):
            x = 3 + _h(n, var, 111) % 26
            c.put(x, 0, mat, 5)
            c.put(x, 1, mat, 4)
    if season == "autumn" and face_mat == "earth":
        c.remap({"grass": "autumn.grass"})
        for n in range(3):  # fallen leaves on the lip
            x = 4 + _h(n, var, k, 121) % 24
            c.put(x, n % 2, "leaf", 3)
            c.put(x + 1, n % 2, "leaf", 2)
    if season == "autumn" and face_mat == "stone":  # the snow lip with bare stretches of dry grass
        for n in range(2):
            a = 4 + _h(n, var, k, 131) % 18
            ln = 3 + _h(n, var, k, 132) % 6
            for x in range(a, min(28, a + ln) + 1):
                end = x in (a, min(28, a + ln))
                for y in range(lip[x] + hg[x]):
                    v = c.get(x, y)
                    if v and v[0] == "snow" and (not end or y == 0):
                        c.put(x, y, "autumn.grass", 5 if y == 0 else 4 if y < lip[x] - 1 else 3)


def build():
    """key -> canvas (the v1 keys of the redrawn faces)."""
    out = {}
    for mat, (_, _, _, _, nvar) in MATS.items():
        for kind in KINDS:
            for seg in (4, 8):
                for var in range(nvar):
                    sfx = "" if var == 0 else f".v{var}"
                    out[f"face.{mat}.{kind}.{seg}{sfx}"] = face(mat, kind, seg, var)
                    if kind.startswith("top"):
                        if mat == "earth":
                            out[f"autumn.face.earth.{kind}.{seg}{sfx}"] = face(mat, kind, seg, var, "autumn")
                            out[f"winter.face.earth.{kind}.{seg}{sfx}"] = face(mat, kind, seg, var, "winter")
                        if mat == "stone":
                            out[f"autumn.face.stone.{kind}.{seg}{sfx}"] = face(mat, kind, seg, var, "autumn")
    return out


def check_joins(cv):
    """Variants of one key agree on their outermost columns (so any two join left / right)."""
    errors = []
    for key, c in cv.items():
        if ".v" in key:
            base = cv[key.rsplit(".v", 1)[0]]
            for x in (0, 31):
                if [row[x] for row in c.px] != [row[x] for row in base.px]:
                    errors.append(f"{key} column {x}")
    return errors
