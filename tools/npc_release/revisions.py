"""NPC batch 1 — revision 1 (the review's small fixes), kept apart from the approved frames.

The approved 120 frames (src/art-release/npc/) are not overwritten: these villagers are drawn by
subclasses that replace only the parts under review, into src/art-release/npc-revision/ (same names).
The game shows them with ?npc=revision; after approval they can replace the originals.

  elder     front: the beard one pixel narrower at each side; wider sleeves with a lit outer edge,
            a dark inner edge and a bright silver cuff, so the arms read apart from the beard; the
            free arm on the shaded side one tone darker
  merchant  back: the hair gets a crown whorl, strands that flow down and highlights; front: the
            purse hangs on the hip in front of the leg, the arm hangs outside it (no overlap)
  guard     front: a dark collar under the chin and a brass-rimmed breastplate with a centre ridge
            and rivets, so the plate no longer reads as a grey beard
"""

import elder
import guard
import merchant
from npc_common import half, rows_of


def _half_rows(rows):
    return [r[:16] for r in rows]


def _replace(rows, at, new):
    rows = list(rows)
    for k, r in enumerate(new):
        assert len(r) == 16, (len(r), r)
        rows[at + k] = r
    return rows


# ------------------------------------------------------------------ elder

_ELDER_HEAD = _replace(_half_rows(elder.HEAD_FRONT), 18, [
    "........24344343",
    "........24344343",
    "........24344343",
    ".........2344343",
    ".........2344343",
    "..........234343",
    "..........234343",
])

ELDER_ARM_DOWN = rows_of("""
..@DDA
.CDDCA
.CEDCB
CEDCCB
CEDCCB
CEDCCB
CDDCBA
CDCCBA
HIJIIH
.*bcc.
.abb..
""", 6)
ELDER_ARM_HOLD = rows_of("""
.....@DA
....CDDA
....EDCB
...EDCCB
...EDCCB
..EDCCB.
..CDCBA.
.CDCCA..
.HIJIH..
.*bc....
.ab.....
""", 8)


def _wider(rows, first, last):
    """The upper body two pixels wider at each side (the sleeves hang outside the beard)."""
    rows = list(rows)
    for k in range(first, last + 1):
        r = rows[k]
        assert r.startswith(".........B"), r
        rows[k] = ".......BC" + r[9:]
    return rows


class ElderR1(elder.Elder):
    HEAD_FRONT = half("\n".join(_ELDER_HEAD))
    BODY_FRONT = half("\n".join(_wider(_half_rows(elder.BODY_FRONT), 1, 10)))
    BODY_BACK = half("\n".join(_wider(_half_rows(elder.BODY_BACK), 1, 10)))
    shoulders_x = (6, 25)
    ARM_DOWN = ELDER_ARM_DOWN
    ARM_HOLD = ELDER_ARM_HOLD
    free_arm_shaded = True


# ------------------------------------------------------------------ merchant

class MerchantR1(merchant.Merchant):
    HEAD_BACK = half("""
..........233333
........23444443
.......234444443
......2344334432
.....23443443343
.....23434334433
.....23343343343
.....22343343343
.....22334334332
....a22233433232
....ab2223322322
....ab2222232222
.....b1222222221
.....bb112121211
......bbb1111111
.......bcbbcbbbb
........bbbbbbbb
""")
    purse_front, purse_back = (6, 39), (21, 39)


# ------------------------------------------------------------------ guard

_GUARD_BODY = _replace(_half_rows(guard.BODY_FRONT), 0, [
    ".........KLMMMMM",
    "....GHIIHGKLMMMM",
    "...GHIJIIHfghhhh",
    "...GHIJIIHgIJJIJ",
    "...GHIIIIHhIIIIJ",
    "...FGHHHHGgHIIHI",
    ".......BCfghhhhh",
])


class GuardR1(guard.Guard):
    BODY_FRONT = half("\n".join(_GUARD_BODY))


REVISED = [ElderR1(), MerchantR1(), GuardR1()]
