"""Records what the reference renderer (tools/terrain_v2/render_ref.py, unchanged) draws on fixed maps, for
tests/unit/groundV2Ref.test.js: the engine must pick exactly the same tiles.

  python3 tools/ground_v2_ref_fixture.py   ->  tests/fixtures/ground_v2_ref.json

render_v2 is run as is; its images are stand-ins that only carry their key, and the drawing calls are
recorded instead of drawn: per display tile (i, j), the keys drawn at it, bottom first.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "terrain_v2"))
from PIL import Image  # noqa: E402
import render_ref  # noqa: E402


class Key:
    def __init__(self, k):
        self.k = k


class Images(dict):
    def __missing__(self, k):
        return Key(k)


def record(grid, season=None):
    draws = {}

    def alpha_composite(self, im, dest=(0, 0), source=(0, 0)):
        i, j = (dest[0] - 16) // 32, (dest[1] - 16) // 32
        draws.setdefault(f"{i},{j}", []).append(im.k)

    old = Image.Image.alpha_composite, Image.Image.paste
    Image.Image.alpha_composite = alpha_composite
    Image.Image.paste = lambda self, *a, **k: None
    try:
        render_ref.render_v2(grid, Images(), frame=0, season=season)
    finally:
        Image.Image.alpha_composite, Image.Image.paste = old
    return {k: "|".join(v) for k, v in draws.items()}


def mixed_grid(W=96, H=72):
    """Every ground of the reference, with uneven borders, a lake, a 1-cell path, a ruin by the water, a wood patch."""
    h = render_ref.dhash
    rows = []
    for y in range(H):
        r = ""
        for x in range(W):
            wob = h(x // 3, y // 3) % 3 - 1
            band = (x + wob) // 12
            c = "gplmnsd=gp"[band % 10] if band < 8 else "g"
            if 20 + wob <= y <= 26 + wob and 30 <= x <= 60:
                c = "~"
            if 40 <= x <= 52 and 27 <= y <= 33:
                c = "u"
            if y == 50 or x == 70:
                c = "="
            if 60 <= y <= 66 and 10 <= x <= 13:
                c = "w"
            if y >= 68 and x < 40:
                c = "~"
            r += c
        rows.append(r)
    return rows


def main():
    out = []
    g = mixed_grid()
    out.append({"name": "mixed96x72", "rows": g, "season": None, "draws": record(g)})
    small = [r[:48] for r in g[:36]]
    out.append({"name": "mixed48x36.winter", "rows": small, "season": "winter", "draws": record(small, "winter")})
    big = ["g" * 96 for _ in range(72)]
    out.append({"name": "grass96x72", "rows": big, "season": None, "draws": record(big)})
    path = os.path.join(HERE, "..", "tests", "fixtures", "ground_v2_ref.json")
    with open(path, "w") as f:
        json.dump(out, f, separators=(",", ":"))
    print(path, os.path.getsize(path))


if __name__ == "__main__":
    main()
