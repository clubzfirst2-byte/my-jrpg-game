"""Object / icon / effect SAMPLES at release quality (wave 1: style approval, not yet adopted).

Writes docs/art-candidates/objects/samples/<name>.png (the game's sprite names; NOT src/ until approved)
and docs/art-candidates/objects/mock_scene.png (tools/object_release/mock.py).
Run: python3 tools/object_release/gen_objects.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from objects import SIZES, all_samples  # noqa: E402
from draw import hx  # noqa: E402,F401

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "art_proto"))
from pixel import png  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
OUT = os.path.join(ROOT, "docs", "art-candidates", "objects", "samples")


def main():
    os.makedirs(OUT, exist_ok=True)
    samples = all_samples()
    for name, img in samples.items():
        w, h = SIZES[name]
        assert (len(img[0]), len(img)) == (w, h), f"{name}: {len(img[0])}x{len(img)}, want {w}x{h}"
        with open(os.path.join(OUT, name + ".png"), "wb") as f:
            f.write(png(img))
    print(f"wrote {len(samples)} samples to {os.path.relpath(OUT, ROOT)}")
    import mock  # noqa: E402

    mock.main(samples)


if __name__ == "__main__":
    main()
