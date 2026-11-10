"""Ground v2 ramps: one 7-tone ramp per ground material, built from the guide's 5-tone ramp of that
material (ART_STYLE_GUIDE 2.5 / the terrain v1 table) so the regions keep their colours and the core
(tone 3 here = the guide's tone 2) keeps the hero-cloak rule.

  ext tone: 0       1       2              3       4              5       6
  guide   : 0       1       (1+2)/2 cool   2       (2+3)/2 warm   3       4

The two new middle tones sit half a step from the core, so large patterns can be drawn with LOW value
contrast (tones 2-3-4) and still show: the shadow-side middle is shifted a little toward blue, the
lit-side middle a little toward yellow (shadows cool, light warm), as the art audit asked.
"""

import colorsys
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "terrain_release"))
from ramps import RELEASE  # noqa: E402  (the v1 terrain table: guide + registered ramps)


def _rgb(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


def _hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(v))) for v in rgb)


def _mid(a, b, hue_to, amount=0.022):
    """Half way between two tones, the hue nudged toward hue_to (0-1) by `amount` of a turn."""
    r, g, bl = [(x + y) / 2 / 255 for x, y in zip(_rgb(a), _rgb(b))]
    h, s, v = colorsys.rgb_to_hsv(r, g, bl)
    if s > 0.05:
        d = (hue_to - h + 0.5) % 1 - 0.5
        h = (h + max(-amount, min(amount, d))) % 1
    return _hex([c * 255 for c in colorsys.hsv_to_rgb(h, s, v)])


COOL, WARM = 0.6, 0.13  # blue, yellow


def extend(ramp5):
    g = ramp5
    return [g[0], g[1], _mid(g[1], g[2], COOL), g[2], _mid(g[2], g[3], WARM), g[3], g[4]]


# Ground materials -> the 5-tone ramp they extend.
BASE5 = {
    "grass": RELEASE["plains.grass"],  # island grass
    "plains": RELEASE["plains.grass"],  # plains: same green, its own features (flowers, wind-bent clumps)
    "lake": RELEASE["lake.grass"],
    "moss": RELEASE["forest.moss"],
    "snow": RELEASE["mount.snow"],
    "sand": RELEASE["island.sand"],
    "dsand": RELEASE["desert.sand"],
    "path": RELEASE["plains.path"],
    "ruin": RELEASE["ruin.stone"],
    # seasons (the v1 method: the same tones, another ramp)
    "autumn.grass": RELEASE["autumn.grass"],
    "autumn.lake": RELEASE["lake.reed"],
    "autumn.moss": RELEASE["forest.swamp"],
    # water
    "shallow": RELEASE["water.surface"],
    "deep": ["#081c34", "#143e66", "#1c4f80", "#28649a", "#3e7cb2"],  # deep water: lake.deep's 0-1, a core 10 darker than shallow
    # features (5 tones are enough for small things; extended for consistency)
    "pebble": RELEASE["pebble"],
    "bark": RELEASE["tree.bark"],
    "pine": RELEASE["forest.pine"],
    "reed": RELEASE["lake.reed"],
    "leaf": RELEASE["fire"],
    "fern": RELEASE["forest.pine"],
    "flower.white": RELEASE["flower.white"],
    "flower.yellow": RELEASE["flower.yellow"],
    "flower.pink": RELEASE["flower.pink"],
    "shell": RELEASE["shell"],
    "dstone": RELEASE["desert.stone"],
    "rock": RELEASE["mount.rock"],
}
EXT = {k: extend(v) for k, v in BASE5.items()}
NEW_RAMPS = {"deep"}  # registered as new in PRODUCTION.md (everything else extends a registered ramp)
