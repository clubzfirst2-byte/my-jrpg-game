"""Enemy projectiles: 12x12, centre anchor, 2 frames each (a flicker / spin), hand-placed.
ENEMY_BOSS_DESIGN.md 4.2: one shape per region, the enemy-magic magenta as the base colour.

  shot.orb    murk orb (hex-caster, forest core's volley, the final boss)   glow
  shot.ice    ice shard (mountain core's ring)                             ice + a glow heart
  shot.sand   grit ball (desert core's volley / ring)                      murksand + glow
  shot.spark  spark ball (lake core's ring / volley)                       spark + glow
They point right where they have a direction; the game rotates them.
"""

from rig import Rig

LEG = {"0": ("glow", 0), "1": ("glow", 1), "2": ("glow", 2), "3": ("glow", 3), "4": ("glow", 4),
       "i": ("ice", 0), "j": ("ice", 1), "k": ("ice", 2), "l": ("ice", 3), "m": ("ice", 4),
       "s": ("murksand", 0), "t": ("murksand", 1), "u": ("murksand", 2), "v": ("murksand", 3), "w": ("murksand", 4),
       "a": ("spark", 0), "b": ("spark", 1), "c": ("spark", 2), "d": ("spark", 3), "e": ("spark", 4)}

MAPS = {
    "orb.0": """
....0000....
..00112100..
.0112333210.
.0123443321.
01234443321.
01233443221.
0123333221 0
.012222211..
.0111111110.
..00111100..
....0000....
............""",
    "orb.1": """
............
....0000....
..01122100..
.0123332110.
.0124443210.
012344432210
012334432110
.0123332110.
.0112222100.
..00111100..
....0000....
............""",
    "ice.0": """
............
....ii......
...ilmi.....
..ilmlkii...
.ilmlk23kii.
ilmlk2343kji
ijkkk2332jji
.ijjkk22jji.
..iijjjjii..
....iiii....
............
............""",
    "ice.1": """
............
.....i......
....imi.....
...ilmkii...
..ilmk23kii.
iilmk23432ji
ijjkk2332jji
..ijjk22jji.
...iijjjii..
.....iii....
............
............""",
    "sand.0": """
............
....ssss....
..sstvvuss..
.stvwvvuuts.
.svwvu1uuts.
stvvu232uts.
stuu23432ts.
.stuu222tts.
.sttuu1utts.
..sstttss...
....ssss....
............""",
    "sand.1": """
............
.....sss....
..ssvvuuss..
.stvwwvuuts.
sstvu212uts.
stvu23432tts
.su2343uuts.
.stuu222tts.
..sttuuttss.
...ssttss...
.....ss.....
............""",
    "spark.0": """
.....a......
....ada.....
..a.adda.a..
..adcdecda..
.aadc343dca.
adde34443eda
.aadc343dca.
..adcdecda..
..a.adda.a..
....ada.....
.....a......
............""",
    "spark.1": """
............
..a.....a...
...ad.ada...
...adddda...
.aadc343da..
aadc34443caa
..adc343dcaa
...adddda...
..ada.ada...
..a.....a...
............
............""",
}


def frames_v1():  # the v1 key poses (kept for reference; v2 frames() is at the end)
    out = {}
    for name, rows in MAPS.items():
        r = Rig(12, 12)
        r.stamp(0, 0, [row.ljust(12, ".")[:12].replace(" ", ".") for row in rows.strip("\n").split("\n")], LEG)
        out[name] = r
    return out


SIZE = (12, 12)


# ------------------------------------------------------------------ v2 frames (4 per shot)

def frames():
    """v2: 4 frames per shot -- the two hand-placed frames and their vertical mirrors (the ball
    turns over as it flies; a shard keeps pointing right). A map that mirrors onto itself is
    nudged one pixel down instead, so every frame is a different picture."""
    out = {}
    for kind in ("orb", "ice", "sand", "spark"):
        base = []
        for n in (0, 1):
            rows = [row.ljust(12, ".")[:12].replace(" ", ".") for row in MAPS[f"{kind}.{n}"].strip("\n").split("\n")]
            rows = (rows + ["." * 12] * 12)[:12]
            base.append(rows)
        seq = [base[0], base[1]]
        for rows in base:
            m = rows[::-1]
            if m in seq:
                m = ["." * 12] + rows[:-1]
            seq.append(m)
        for i, rows in enumerate(seq):
            r = Rig(12, 12)
            r.stamp(0, 0, rows, LEG)
            out[f"{kind}.{i}"] = r
    return out


ACTIONS = (("orb", 4), ("ice", 4), ("sand", 4), ("spark", 4))
