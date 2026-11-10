"""Release art for every object / puzzle part / icon / effect / UI sprite (not trees or nature props).

  wave 1 (objects.py, approved samples, unchanged) + wave 2 (objects2.py) = 62 sprites
  (rock, bramble, stump, cactus: the terrain producer, art/terrain-release)
  -> src/art-release/objects/<name>.png         (the game's sprite names; NOT wired into the game)
  -> docs/art-release/objects/review_*.png       (self-check sheets, review.py)
Run: python3 tools/object_release/gen_release.py   (deterministic: the same PNGs every time)
Stops on any break of the guide's measurable rules (check()).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from draw import RAMPS, hx  # noqa: E402
from objects import ANCHOR, SIZES, all_samples  # noqa: E402
from objects2 import ANCHOR2, SIZES2, all_wave2  # noqa: E402
from icons_v1_1 import ANCHOR3, SIZES3, all_icons_v1_1  # noqa: E402
from icons_dishes import ANCHOR4, SIZES4, all_dishes  # noqa: E402
from ramps2 import RAMPS2  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "art_proto"))
from pixel import BASE_RAMPS, png  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
OUT = os.path.join(ROOT, "src", "art-release", "objects")
ALL_SIZES = {**SIZES, **SIZES2, **SIZES3, **SIZES4}
ALL_ANCHOR = {**ANCHOR, **ANCHOR2, **ANCHOR3, **ANCHOR4}
ALLOWED = {hx(c) for r in {**BASE_RAMPS, **RAMPS, **RAMPS2}.values() for c in r}


def check(name, img):
    """ART_STYLE_GUIDE.md 1.1, 4.1, 6.1, 6.2."""
    w, h = ALL_SIZES[name]
    assert (len(img[0]), len(img)) == (w, h), f"{name}: {len(img[0])}x{len(img)}, want {w}x{h}"
    for row in img:
        assert len(row) == w, name
        for p in row:
            if p is None:
                continue
            assert p[3] == 255, f"{name}: a semi-transparent pixel {p}"
            assert tuple(p[:3]) in ALLOWED, f"{name}: colour {p[:3]} is in no ramp"
    assert any(p for row in img for p in row), f"{name}: empty"
    if name.startswith("icon."):
        edge = img[0] + img[h - 1] + [r[0] for r in img] + [r[w - 1] for r in img]
        assert not any(edge), f"{name}: touches the edge (needs a 1 px margin)"
    elif ALL_ANCHOR[name] == "feet":
        assert any(img[h - 1]), f"{name}: the last row is empty (it would float)"


def build():
    out = {**all_samples(), **all_wave2(), **all_icons_v1_1(), **all_dishes()}
    assert set(out) == set(ALL_SIZES), sorted(set(out) ^ set(ALL_SIZES))
    for name, img in out.items():
        check(name, img)
    return out


def main():
    sprites = build()
    os.makedirs(OUT, exist_ok=True)
    for name, img in sorted(sprites.items()):
        with open(os.path.join(OUT, name + ".png"), "wb") as f:
            f.write(png(img))
    print(f"wrote {len(sprites)} sprites to {os.path.relpath(OUT, ROOT)}")
    import review  # noqa: E402

    review.main(sprites)


if __name__ == "__main__":
    main()
