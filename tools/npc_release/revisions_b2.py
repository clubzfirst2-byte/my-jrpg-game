"""NPC batch 2 — revision 1 (the review's fixes), kept apart from the batch 2 frames under review.

The 160 batch 2 frames (src/art-release/npc/npc.{woman,cook,child,smith}.*) are not overwritten:
these villagers are drawn by subclasses that replace only the parts under review, into
src/art-release/npc-revision-b2/ (same names; the cook is unchanged, so he has no files there).
The game shows them with ?npc=revision-b2.

  woman  thinner lashes (a soft brown at the corners, dark only in the middle), a light brow above
         each eye, a brighter amber at the bottom of the iris: awake, not sleepy. Headscarf, braid,
         clothes and basket as they are.
  child  the blond hair in round curls: each curl lit at its top left and shaded at its bottom right,
         the curls set like bricks (each band shifted half a curl), so the hair no longer reads as
         stripes. Face, eyes, build, pinwheel and clothes as they are.
  smith  the soot is a round smudge low on each cheek (no line under the eye, so no "tear") and the
         eye's iris is two pixels wide (an eye, not a drop under the lash); the
         gloves one pixel bigger; the arms cast a one-pixel shadow on the apron beside them, so arm
         and apron part clearly. Hair, headband, build, hammer and clothes as they are.
"""

import child
import smith
import woman
from npc_common import half, legend, rows_of
from villager import Villager


def _half_rows(rows):
    return [r[:16] for r in rows]


def _set(rows, at, new, width=16):
    rows = list(rows)
    for k, r in new.items():
        assert len(r) == width or width is None, (len(r), r)
        rows[at + k] = r
    return rows


# ------------------------------------------------------------------ woman

WOMAN_LEG = {**woman.LEG, **legend([], {"l": ("skin", 2, "#8a5038"), "o": ("skin", 2, "#eab050")})}

_W_FRONT = _set(_half_rows(woman.HEAD_FRONT), 9, {
    0: "....a234b22ccccc",
    1: "....a23bleelcccc",
    2: "....a2bcIiwicccc",
    3: "....a2bcIiiicccc",
    4: "....a2bcbooccccd",
})


def _patch(row, x0, changes):
    r = list(row)
    for k, ch in enumerate(changes):
        r[x0 + k] = ch
    return "".join(r)


_W_SIDE = list(woman.HEAD_SIDE)
_W_SIDE[9] = _patch(_W_SIDE[9], 19, "22")
_W_SIDE[10] = _patch(_W_SIDE[10], 19, "leec")
_W_SIDE[12] = _patch(_W_SIDE[12], 19, "oo")


class WomanR1(woman.Woman):
    LEG = WOMAN_LEG
    HEAD_FRONT = half("\n".join(_W_FRONT))
    HEAD_SIDE = _W_SIDE

    def blink_front(self, c, top):
        for x in (8, 9, 10, 11, 20, 21, 22, 23):
            c.put(x, top + 10, "skin", 3)
            c.put(x, top + 11, "skin", 2)
            c.paint(x, top + 11, "#5a3226" if x in (8, 11, 20, 23) else "#2a1a18")
            c.put(x, top + 12, "skin", 3)
            c.put(x, top + 13, "skin", 3)

    def blink_side(self, c, top):
        for x in (19, 20, 21):
            c.put(x, top + 10, "skin", 3)
            c.put(x, top + 11, "skin", 2)
            c.paint(x, top + 11, "#2a1a18")
            c.put(x, top + 12, "skin", 3)


# ------------------------------------------------------------------ child

CURL = [  # one curl, 4 wide and 4 tall: lit at the top left, shaded at the bottom right
    "2332",
    "3443",
    "3432",
    "1221",
]


def curls(rows, mirrored_half=False):
    """Re-tones the hair (0-4) as round curls laid like bricks; the silhouette's edge keeps its tone."""
    out = []
    h = len(rows)
    for y, r in enumerate(rows):
        row = list(r)
        for x, ch in enumerate(r):
            if ch not in "01234":
                continue
            edge = any(
                not (0 <= yy < h and 0 <= xx < len(r)) or rows[yy][xx] == "."
                for yy, xx in ((y - 1, x), (y, x - 1), (y, x + 1 if not mirrored_half or x < len(r) - 1 else x))
            )
            if edge:
                continue
            band = y // 4
            cx = (x + (2 if band % 2 else 0)) % 4
            row[x] = CURL[y % 4][cx]
        out.append("".join(row))
    return out


class ChildR1(child.Child):
    HEAD_FRONT = half("\n".join(curls(_half_rows(child.HEAD_FRONT), mirrored_half=True)[:9] + _half_rows(child.HEAD_FRONT)[9:]))
    HEAD_BACK = half("\n".join(curls(_half_rows(child.HEAD_BACK), mirrored_half=True)))
    HEAD_SIDE = curls(child.HEAD_SIDE)


# ------------------------------------------------------------------ smith

SMITH_LEG = {**smith.LEG, **legend([], {"%": ("skin", 2, "#a08a7e")})}

_S_FRONT = _set(_half_rows(smith.HEAD_FRONT), 10, {
    0: "....abccckkccccd",
    1: "....abccccccccbd",
    2: "....ab%#ccccccbb",
    3: ".....b%cccccccmm",
})
_S_SIDE = list(smith.HEAD_SIDE)
_S_SIDE[11] = _S_SIDE[11].replace("#", "c")
_S_SIDE[12] = _patch(_S_SIDE[12].replace("#", "c"), 14, "%#")
_S_SIDE[13] = _patch(_S_SIDE[13], 14, "%")

SMITH_ARM = rows_of("""
.@CD..
BCDDC.
BCDEC.
BCDDC.
CDEED.
.bccb.
bcddcb
bccdcb
bcdccb
bccdcb
bcccb.
prrtqp
p*rtqp
pqqqqp
.pppp.
""", 6)


class SmithR1(smith.Smith):
    LEG = SMITH_LEG
    HEAD_FRONT = half("\n".join(_S_FRONT))
    HEAD_SIDE = _S_SIDE
    ARM_R = ARM_L = SMITH_ARM

    def arms_front(self, c, p, b, up, back):
        before = [row[:] for row in c.mat]
        Villager.arms_front(self, c, p, b, up, back)
        # the arms' shadow on the apron (and trousers) beside them: one pixel, on the body's side
        y0 = self.shoulder_y + b + up + 5
        arm = {(x, y) for y in range(56) for x in range(32) if c.mat[y][x] is not None and c.mat[y][x] != before[y][x]}
        for x, y in arm:
            if y < y0:
                continue
            nx = x + 1 if x < 16 else x - 1
            if (nx, y) in arm or not 0 <= nx < 32:
                continue
            if c.mat[y][nx] in ("apron", "trousers", "shirt"):
                c.tone[y][nx] = 0 if c.mat[y][nx] == "apron" else 1


REVISED_B2 = [WomanR1(), ChildR1(), SmithR1()]
