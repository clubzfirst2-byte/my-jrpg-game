"""Quick look: one character's frames enlarged next to the hero (for drawing by hand).
Run: python3 tools/npc_release/preview.py <id> <out.png> [scale]"""
import os
import sys
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import gen_npc  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")


def to_image(img):
    im = Image.new("RGBA", (len(img[0]), len(img)))
    im.putdata([tuple(px) if px else (0, 0, 0, 0) for row in img for px in row])
    return im


def sheet(npc_id, out, scale=5, actions=("idle", "walk")):
    npc = gen_npc.BY_ID[npc_id]
    rows = []
    for a in actions:
        for d in ("down", "up", "right", "left"):
            n = 4 if a == "idle" else 6
            rows.append([to_image(npc.frame(a, d, i)) for i in range(n)])
    hero = [Image.open(os.path.join(ROOT, "src/art-release/hero", f"hero.idle.{d}.0.png")) for d in ("down", "up", "right", "left")]
    w = 36 * 7 + 4
    hgt = 60 * len(rows) + 4
    canvas = Image.new("RGBA", (w, hgt), (79, 138, 62, 255))
    for r, row in enumerate(rows):
        for k, im in enumerate(row):
            canvas.alpha_composite(im, (4 + k * 36, 4 + r * 60))
        canvas.alpha_composite(hero[r % 4], (4 + 6 * 36, 4 + r * 60))
    canvas.resize((w * scale, hgt * scale), Image.NEAREST).save(out)


if __name__ == "__main__":
    sheet(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 5,
          tuple(sys.argv[4].split(",")) if len(sys.argv) > 4 else ("idle", "walk"))
