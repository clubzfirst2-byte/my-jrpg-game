"""Review image for the object samples: docs/art-candidates/objects/mock_scene.png

  1. a small village scene on grass with the approved hero for scale, at 1x (the release art size)
  2. the same scene at 3x
  3. the icons in a dark UI panel (3x)
  4. each sample next to the current placeholder (docs/art-kit/, the same size), 3x
The grass and path here are only a stand-in backdrop for the review (tiles are not part of this wave).
"""

import glob
import os
import random

from PIL import Image, ImageDraw

from objects import ANCHOR

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
OUT = os.path.join(ROOT, "docs", "art-candidates", "objects", "mock_scene.png")
HERO = os.path.join(ROOT, "src", "art-release", "hero", "hero.idle.down.0.png")

GRASS = [(0x3E, 0x74, 0x34), (0x4A, 0x84, 0x3A), (0x58, 0x94, 0x42), (0x6C, 0xA8, 0x4C), (0x2E, 0x5C, 0x2A)]
PATH = [(0x9A, 0x7E, 0x58), (0xB0, 0x94, 0x6A), (0xC4, 0xA8, 0x7C), (0x80, 0x66, 0x46)]
BG_UI = (0x16, 0x14, 0x22)


def to_image(rows):
    h, w = len(rows), len(rows[0])
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    for y in range(h):
        for x in range(w):
            if rows[y][x]:
                px[x, y] = tuple(rows[y][x])
    return im


def grass_tile(seed):
    rnd = random.Random(seed)
    im = Image.new("RGBA", (32, 32), GRASS[1] + (255,))
    px = im.load()
    for _ in range(26):
        x, y = rnd.randrange(32), rnd.randrange(32)
        px[x, y] = GRASS[2] + (255,)
    for _ in range(5):  # tufts: a lit blade over a shadow
        x, y = rnd.randrange(1, 31), rnd.randrange(2, 31)
        px[x, y] = GRASS[3] + (255,)
        px[x, y - 1] = GRASS[3] + (255,)
        px[x - 1, y] = GRASS[2] + (255,)
        px[x + 1, y] = GRASS[0] + (255,)
        if y + 1 < 32:
            px[x, y + 1] = GRASS[0] + (255,)
    return im


def path_tile(seed):
    rnd = random.Random(seed)
    im = Image.new("RGBA", (32, 32), PATH[1] + (255,))
    px = im.load()
    for _ in range(30):
        x, y = rnd.randrange(32), rnd.randrange(32)
        px[x, y] = rnd.choice((PATH[0], PATH[2])) + (255,)
    for _ in range(3):
        x, y = rnd.randrange(1, 30), rnd.randrange(1, 30)
        px[x, y] = PATH[2] + (255,)
        px[x + 1, y] = PATH[2] + (255,)
        px[x, y + 1] = PATH[3] + (255,)
        px[x + 1, y + 1] = PATH[0] + (255,)
    return im


def shadow(im, cx, fy, w):
    """A soft oval ground shadow under a standing object (like fx.shadow in the game)."""
    d = ImageDraw.Draw(im, "RGBA")
    d.ellipse([cx - w // 2, fy - 4, cx + w // 2, fy + 2], fill=(10, 30, 10, 70))


def place(dst, img, x, y, anchor="feet"):
    """x, y: the anchor point (feet: bottom centre; centre: the middle)."""
    w, h = img.size
    if anchor == "feet":
        dst.alpha_composite(img, (x - w // 2, y - h))
    else:
        dst.alpha_composite(img, (x - w // 2, y - h // 2))


def scene(s):
    tw, th = 12, 8
    im = Image.new("RGBA", (tw * 32, th * 32))
    paths = {(5, 5), (5, 6), (5, 7), (6, 6), (7, 6), (8, 6), (4, 6), (3, 6)}
    for ty in range(th):
        for tx in range(tw):
            t = path_tile(tx * 7 + ty) if (tx, ty) in paths else grass_tile(tx * 31 + ty * 17)
            im.alpha_composite(t, (tx * 32, ty * 32))
    hero = Image.open(HERO).convert("RGBA")
    S = {k: to_image(v) for k, v in s.items()}
    # the house: its door tile is (5, 4) -> feet at the bottom of that tile, centre of it
    items = [
        ("obj.house", 5 * 32 + 16, 5 * 32),
        ("obj.checkpoint.on", 9 * 32 + 16, 3 * 32),
        ("obj.checkpoint.off", 10 * 32 + 16, 3 * 32),
        ("obj.jar", 1 * 32 + 16, 4 * 32),
        ("obj.jar", 2 * 32 + 16, 4 * 32),
        ("obj.crate", 8 * 32 + 16, 5 * 32),
        ("obj.chest.closed", 1 * 32 + 16, 7 * 32),
        ("obj.chest.open", 2 * 32 + 16, 7 * 32),
        ("obj.campfire.0", 9 * 32 + 16, 8 * 32),
        ("sw.plate.off", 10 * 32 + 16, 6 * 32),
        ("sw.plate.on", 11 * 32 + 16, 6 * 32),
        ("fx.fire.0", 3 * 32 + 16, 3 * 32),
        ("icon.sword", 7 * 32 + 16, 8 * 32 - 6),
        ("icon.herb", 6 * 32 + 16, 8 * 32 - 6),
        ("icon.meat", 7 * 32 + 16, 7 * 32 - 4),
    ]
    flat = {"sw.plate.off", "sw.plate.on", "fx.fire.0"}
    drawn = sorted(items + [("hero", 5 * 32 + 16, 7 * 32 - 4)], key=lambda e: e[2])
    for name, x, y in drawn:
        if name == "hero":
            shadow(im, x, y, 20)
            place(im, hero, x, y)
            # the sword trail to the hero's right, as in an attack facing right
            place(im, S["fx.slash"], x + 26, y - 18, "centre")
            continue
        if name not in flat and not name.startswith("icon"):
            shadow(im, x, y, min(S[name].size[0], 40) - 4)
        if name.startswith("icon"):
            shadow(im, x, y + 2, 12)
        place(im, S[name], x, y, ANCHOR.get(name, "feet"))
    return im


def label(d, x, y, text, fill=(240, 240, 240)):
    d.text((x, y), text, fill=fill)


def placeholder(name):
    hits = glob.glob(os.path.join(ROOT, "docs", "art-kit", "*", name + ".png"))
    return Image.open(hits[0]).convert("RGBA") if hits else None


def compare(s, scale=3):
    names = list(s.keys())
    cells = []
    for n in names:
        new = to_image(s[n])
        old = placeholder(n)
        cells.append((n, old, new))
    col_w = max(max((o.size[0] if o else 0), nw.size[0]) for _, o, nw in cells) * scale
    pad = 12
    per_row = 4
    blocks = []
    for n, old, new in cells:
        w = (old.size[0] if old else new.size[0]) * scale + new.size[0] * scale + pad * 3
        h = max(new.size[1], old.size[1] if old else 0) * scale + pad * 2 + 14
        blk = Image.new("RGBA", (w, h), GRASS[1] + (255,))
        d = ImageDraw.Draw(blk)
        label(d, pad, 3, n + "   old -> new")
        y_base = h - pad
        x = pad
        for im in (old, new):
            if im is None:
                x += new.size[0] * scale + pad
                continue
            big = im.resize((im.size[0] * scale, im.size[1] * scale), Image.NEAREST)
            blk.alpha_composite(big, (x, y_base - big.size[1]))
            x += big.size[0] + pad
        blocks.append(blk)
    rows = [blocks[i:i + per_row] for i in range(0, len(blocks), per_row)]
    W = max(sum(b.size[0] for b in r) + pad * (len(r) + 1) for r in rows)
    H = sum(max(b.size[1] for b in r) + pad for r in rows) + pad
    out = Image.new("RGBA", (W, H), (0x22, 0x30, 0x22, 255))
    y = pad
    for r in rows:
        x = pad
        for b in r:
            out.alpha_composite(b, (x, y))
            x += b.size[0] + pad
        y += max(b.size[1] for b in r) + pad
    del col_w
    return out


def ui_panel(s, scale=3):
    icons = ["icon.sword", "icon.herb", "icon.meat"]
    slot = 28
    pad = 6
    w = pad + len(icons) * (slot + pad) + 120
    h = slot + pad * 2
    im = Image.new("RGBA", (w, h), BG_UI + (255,))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], outline=(0x8A, 0x74, 0x3C, 255))
    d.rectangle([1, 1, w - 2, h - 2], outline=(0x3A, 0x32, 0x48, 255))
    for i, n in enumerate(icons):
        x = pad + i * (slot + pad)
        d.rectangle([x, pad, x + slot - 1, pad + slot - 1], fill=(0x2A, 0x26, 0x3A, 255), outline=(0x5A, 0x52, 0x70, 255))
        ic = to_image(s[n])
        im.alpha_composite(ic, (x + (slot - 20) // 2, pad + (slot - 20) // 2))
    big = im.resize((w * scale, h * scale), Image.NEAREST)
    return big


def main(samples):
    sc = scene(samples)
    sc3 = sc.resize((sc.size[0] * 3, sc.size[1] * 3), Image.NEAREST)
    ui = ui_panel(samples)
    cmp_ = compare(samples)
    pad = 16
    W = max(sc3.size[0], cmp_.size[0], ui.size[0] + sc.size[0] + pad) + pad * 2
    H = pad + 16 + sc.size[1] + pad + 16 + sc3.size[1] + pad + 16 + cmp_.size[1] + pad
    out = Image.new("RGBA", (W, H), (0x1C, 0x1C, 0x24, 255))
    d = ImageDraw.Draw(out)
    y = pad
    label(d, pad, y, "1x (release art size; the game shows it at half size on a 2x screen)")
    label(d, pad + sc.size[0] + pad, y, "icons in a UI panel (3x)")
    y += 16
    out.alpha_composite(sc, (pad, y))
    out.alpha_composite(ui, (pad + sc.size[0] + pad, y))
    y += sc.size[1] + pad
    label(d, pad, y, "3x")
    y += 16
    out.alpha_composite(sc3, (pad, y))
    y += sc3.size[1] + pad
    label(d, pad, y, "placeholder (docs/art-kit, left) vs sample (right), 3x")
    y += 16
    out.alpha_composite(cmp_, (pad, y))
    out.save(OUT)
    print("wrote", os.path.relpath(OUT, ROOT), out.size)
