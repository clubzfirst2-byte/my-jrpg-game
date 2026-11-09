"""NPC batch 3 — DESIGN CONCEPTS only (設計案、未制作): the traveller and the star-ring princess as
flat colour blocks beside the adopted hero, to agree silhouette, proportions and colours BEFORE the
pixel work starts. These are not game art and are written to docs/ only.

Run: python3 tools/npc_concepts/batch3_concepts.py
Writes docs/npc/batch3/design_compare.png and docs/npc/batch3/palette_b3.png
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "art_proto"))
from pixel import Canvas, mirror  # noqa: E402

OUT = os.path.join(ROOT, "docs", "npc", "batch3")
HERO = os.path.join(ROOT, "src", "art-release", "hero")
FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"

PRINCESS = {
    "hair": ["#4a5068", "#9aa2be", "#c8d0e6", "#e4eaf6", "#ffffff"],  # silver with a cool blue shadow
    "skin": ["#6e3e2c", "#d09a7c", "#f6cfae", "#ffe2c8", "#fff4e8"],
    "dress": ["#4a4c5a", "#b8bccc", "#e6e8f0", "#f6f7fb", "#ffffff"],  # white travelling dress
    "cape": ["#0a1838", "#1e3c7a", "#2e5aa8", "#4a7ccc", "#7aa8ec"],  # deep star blue
    "gold": ["#5a4018", "#a07a30", "#e8c060", "#f8dc88", "#fff4c8"],
    "gem": ["#0e2a60", "#1a5cb8", "#2a8de2", "#78c8ff", "#e0f6ff"],
    "boot": ["#2a1e18", "#5a4232", "#7e6048", "#a08062", "#c0a080"],
}
TRAVELLER = {
    "hat": ["#1a120a", "#3e2c1a", "#5a4228", "#78583a", "#96744e"],
    "hair": ["#3a3a3e", "#7a7a80", "#a4a4aa", "#c4c4ca", "#e2e2e6"],  # grey
    "skin": ["#4e2a1a", "#9a6040", "#c88a62", "#dca47a", "#ecbe96"],  # weathered, sun-browned
    "coat": ["#1e1a12", "#463e2c", "#665a40", "#867858", "#a69874"],  # dull brown-olive
    "scarf": ["#2a0a10", "#6a1824", "#962a36", "#bc4650", "#de7a7a"],  # crimson
    "pack": ["#24160c", "#4a3020", "#704c30", "#946c46", "#b88c5e"],
    "roll": ["#2a3024", "#56604a", "#7a8668", "#9eaa88", "#c2ccaa"],  # the bedroll
    "wood": ["#1e1008", "#4a2c16", "#6e4424", "#906038", "#b07e50"],
    "gourd": ["#3a2a08", "#8a6a20", "#b8902e", "#d8b04a", "#f0d27a"],
    "boot": ["#1e120a", "#3e2616", "#62402a", "#865c3c", "#a87a52"],
}


def princess(view):
    c = Canvas(32, 56, PRINCESS)
    side = view == "side"
    back = view == "back"
    cx = 15.5
    # long hair falling behind (to the waist)
    if side:
        c.poly([(9, 8), (17, 6), (17, 30), (13, 40), (8, 38)], "hair")
    else:
        c.poly([(6, 10), (25, 10), (26, 38), (21, 41), (10, 41), (5, 38)], "hair")
    # legs and boots (dress to the knee)
    for x0 in ((13,) if side else (11, 17)):
        c.rect(x0, 41, x0 + 3, 50, "dress", 3)
        c.rect(x0, 50, x0 + 3, 55, "boot")
    # dress (A-line to the knee), cape over the shoulders
    if side:
        c.poly([(11, 22), (19, 22), (21, 43), (9, 43)], "dress")
        c.poly([(9, 21), (19, 21), (18, 31), (7, 33)], "cape")
    else:
        c.poly([(10, 22), (21, 22), (24, 43), (7, 43)], "dress")
        c.poly([(7, 21), (24, 21), (26, 31 if back else 28), (5, 31 if back else 28)], "cape")
        c.line(7, 28 if not back else 31, 25, 28 if not back else 31, "gold", 2)
    # the star-vein sash
    c.rect(9 if not side else 11, 32, 22 if not side else 20, 33, "cape", 2)
    if not back:
        c.put(15 if not side else 18, 32, "gold", 3)
    # head
    if side:
        c.ellipse(16, 13, 7.5, 8.5, "hair")
        c.poly([(16, 9), (23, 9), (24, 16), (21, 21), (16, 20)], "skin")
        c.put(21, 14, "gem", 2)
    else:
        c.ellipse(cx, 13, 9, 9, "hair")
        if not back:
            c.poly([(9, 10), (22, 10), (22, 17), (18, 21), (13, 21), (9, 17)], "skin")
            for ex in (11, 19):  # eyes
                c.rect(ex, 14, ex + 1, 15, "gem", 2)
            c.rect(9, 7, 22, 8, "hair", 4)  # fringe
            # side braids in front of the shoulders
            for bx in (7, 23):
                c.rect(bx, 14, bx + 1, 30, "hair", 3)
    # the star-ring circlet with a blue stone (on the forehead)
    c.line(8 if not side else 12, 9, 23 if not side else 22, 9, "gold", 3)
    if not back:
        c.put(15 if not side else 21, 9, "gem", 4)
        c.put(16 if not side else 21, 10, "gem", 2)
    return c


def traveller(view):
    c = Canvas(32, 56, TRAVELLER)
    side = view == "side"
    back = view == "back"
    # backpack with the bedroll on top (behind)
    if side:
        c.rect(6, 21, 11, 36, "pack")
        c.rect(5, 18, 12, 21, "roll")
    else:
        c.rect(8, 20, 23, 36, "pack")
        c.rect(6, 17, 25, 20, "roll")
    # legs (long, thin) and boots
    for x0 in ((14,) if side else (12, 17)):
        c.rect(x0, 44, x0 + 2, 51, "coat", 1)
        c.rect(x0 - 1, 51, x0 + 3, 55, "boot")
    # the long coat (to mid-calf), open at the front
    if side:
        c.poly([(11, 21), (19, 21), (21, 48), (9, 48)], "coat")
    else:
        c.poly([(9, 21), (22, 21), (24, 48), (7, 48)], "coat")
        if not back:
            c.line(15, 30, 15, 48, "coat", 1)
            c.line(16, 30, 16, 48, "coat", 1)
    # the crimson scarf, its end hanging
    c.rect(10 if not side else 12, 19, 21 if not side else 19, 22, "scarf")
    c.rect(18 if not side else 17, 22, 19 if not side else 18, 30, "scarf")
    # head: narrow, weathered; grey hair tied back
    if side:
        c.poly([(13, 8), (20, 8), (21, 15), (19, 19), (14, 19)], "skin")
        c.poly([(10, 9), (14, 9), (13, 18), (9, 20)], "hair")
    else:
        c.poly([(11, 8), (20, 8), (20, 16), (17, 19), (14, 19), (11, 16)], "skin" if not back else "hair")
        if not back:
            c.line(12, 12, 14, 12, "hair", 1)
            c.line(17, 12, 19, 12, "hair", 1)
    # the wide-brimmed hat
    c.rect(2 if not side else 6, 8, 29 if not side else 26, 9, "hat")
    c.poly([(9 if not side else 11, 3), (22 if not side else 20, 3), (23 if not side else 21, 8), (8 if not side else 10, 8)], "hat")
    c.line(9 if not side else 11, 7, 22 if not side else 20, 7, "scarf", 2)  # a crimson band
    # the walking stick with a water gourd tied at the top
    sx = 27 if side else 4
    c.line(sx, 6, sx, 55, "wood", 2)
    c.ellipse(sx + 0.5, 8, 1.6, 2.2, "gourd")
    return c


def to_image(c):
    img = c.colours()
    im = Image.new("RGBA", (32, 56))
    im.putdata([tuple(px) if px else (0, 0, 0, 0) for row in img for px in row])
    return im


def flip(c):
    img = mirror(c.colours())
    im = Image.new("RGBA", (32, 56))
    im.putdata([tuple(px) if px else (0, 0, 0, 0) for row in img for px in row])
    return im


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    k = 5
    f = ImageFont.truetype(FONT, 18)
    rows = [
        ("主人公（正式採用）", [Image.open(os.path.join(HERO, f"hero.idle.{d}.0.png")).convert("RGBA") for d in ("down", "up", "right")]),
        ("星環の姫（設計案）", [to_image(princess("front")), to_image(princess("back")), to_image(princess("side"))]),
        ("旅人（設計案）", [to_image(traveller("front")), to_image(traveller("back")), to_image(traveller("side"))]),
    ]
    W = 220 + 3 * (32 * k + 16) + 40 + 3 * (32 + 10)
    H = 50 + len(rows) * (56 * k + 20)
    canvas = Image.new("RGBA", (W, H), (34, 38, 46, 255))
    g = ImageDraw.Draw(canvas)
    g.text((220, 12), "正面", fill=(230, 230, 230), font=f)
    g.text((220 + 32 * k + 16, 12), "背面", fill=(230, 230, 230), font=f)
    g.text((220 + 2 * (32 * k + 16), 12), "右向き", fill=(230, 230, 230), font=f)
    g.text((220 + 3 * (32 * k + 16) + 20, 12), "ゲーム内の大きさ", fill=(230, 230, 230), font=ImageFont.truetype(FONT, 14))
    for r, (label, ims) in enumerate(rows):
        y = 44 + r * (56 * k + 20)
        g.text((10, y + 56 * k // 2 - 10), label, fill=(240, 240, 240), font=f)
        for i, im in enumerate(ims):
            tile = Image.new("RGBA", (32 * k, 56 * k), (79, 138, 62, 255))
            tile.alpha_composite(im.resize((32 * k, 56 * k), Image.NEAREST))
            canvas.alpha_composite(tile, (220 + i * (32 * k + 16), y))
        small = Image.new("RGBA", (3 * 42, 60), (79, 138, 62, 255))
        for i, im in enumerate(ims):
            small.alpha_composite(im.resize((16, 28), Image.NEAREST).resize((32, 56), Image.NEAREST), (4 + i * 42, 2))
        canvas.alpha_composite(small, (220 + 3 * (32 * k + 16) + 20, y))
    g.text((10, H - 24), "※ 設計案（色と形の確認用の簡易な図）。製品版のドット絵は承認後に手作業で制作します。", fill=(255, 200, 120), font=ImageFont.truetype(FONT, 14))
    canvas.save(os.path.join(OUT, "design_compare.png"))

    # palettes side by side with the hero's
    hero_ramps = {"cloak": ["#10180e", "#3e6234", "#6a9048", "#8eb062", "#b8d48a"], "shirt": ["#4a4640", "#a8a296", "#e4e0d6", "#f6f4ee", "#ffffff"],
                  "hair": ["#2a160c", "#4e2e1a", "#7a4a2a", "#a8703f", "#d09a62"], "gold": PRINCESS["gold"], "gem": PRINCESS["gem"]}
    sets = [("主人公", hero_ramps), ("星環の姫", PRINCESS), ("旅人", TRAVELLER)]
    sw = 24
    W2 = 120 + max(len(s) for _, s in sets) * (5 * sw + 70)
    pal = Image.new("RGBA", (W2, 30 + len(sets) * (sw + 34)), (34, 38, 46, 255))
    g2 = ImageDraw.Draw(pal)
    for r, (name, ramps) in enumerate(sets):
        y = 24 + r * (sw + 34)
        g2.text((10, y + 4), name, fill=(240, 240, 240), font=ImageFont.truetype(FONT, 16))
        for i, (m, ramp) in enumerate(ramps.items()):
            x = 120 + i * (5 * sw + 70)
            g2.text((x, y - 16), m, fill=(200, 200, 200), font=ImageFont.truetype(FONT, 12))
            for t, col in enumerate(ramp):
                g2.rectangle([x + t * sw, y, x + t * sw + sw - 2, y + sw], fill=col)
    pal.save(os.path.join(OUT, "palette_b3.png"))
    print("concepts ->", os.path.relpath(OUT, ROOT))
