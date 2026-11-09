"""Object / icon / effect SAMPLES at release quality (wave 1: style approval, not yet adopted).

Writes docs/art-candidates/objects/samples/<name>.png (the game's sprite names; NOT src/ until approved)
and docs/art-candidates/objects/mock_scene.png (tools/object_release/mock.py).
Run: python3 tools/object_release/gen_objects.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from objects import ANCHOR, SIZES, all_samples  # noqa: E402
from draw import RAMPS, hx  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "art_proto"))
from pixel import BASE_RAMPS, png  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
OUT = os.path.join(ROOT, "docs", "art-candidates", "objects", "samples")


def check(name, img):
    """The style guide's measurable rules (ART_STYLE_GUIDE.md 1.1, 4.1, 6.1, 6.2)."""
    w, h = SIZES[name]
    assert (len(img[0]), len(img)) == (w, h), f"{name}: {len(img[0])}x{len(img)}, want {w}x{h}"
    allowed = {hx(c) for r in {**BASE_RAMPS, **RAMPS}.values() for c in r}
    for row in img:
        for p in row:
            if p is None:
                continue
            assert p[3] == 255, f"{name}: a semi-transparent pixel {p}"
            assert tuple(p[:3]) in allowed, f"{name}: colour {p[:3]} is in no ramp"
    if ANCHOR[name] == "feet" and not name.startswith("icon."):  # icons keep a margin instead (6.1)
        assert any(img[h - 1]), f"{name}: the last row is empty (it would float)"
    if name.startswith("icon."):
        edge = img[0] + img[h - 1] + [r[0] for r in img] + [r[w - 1] for r in img]
        assert not any(edge), f"{name}: touches the edge (needs a 1 px margin)"


def main():
    os.makedirs(OUT, exist_ok=True)
    samples = all_samples()
    for name, img in samples.items():
        check(name, img)
        with open(os.path.join(OUT, name + ".png"), "wb") as f:
            f.write(png(img))
    print(f"wrote {len(samples)} samples to {os.path.relpath(OUT, ROOT)}")
    import mock  # noqa: E402

    mock.main(samples)


if __name__ == "__main__":
    main()
