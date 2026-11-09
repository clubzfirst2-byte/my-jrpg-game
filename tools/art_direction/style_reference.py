"""The art style reference sheet (docs/art-direction/style_reference.png).

What it shows (see docs/art-direction/ART_STYLE_GUIDE.md):
  A. every shared ramp (5 tones: 0 outline, 1 shadow, 2 core, 3 light, 4 highlight):
     the character materials, the hero, two NPCs, the region terrain ramps and the signal colours;
  B. the approved hero (idle down / right) and two NPCs, on the plains grass, at 4x and at 1x;
  C. terrain: a seamless grass tile repeated 3x2 with a path and a cliff face, and the seasonal
     palette shift (a PROPOSAL, not approved);
  D. do / don't: the same chest drawn by the rules and broken in five common ways,
     an interactive object in its 2 states, and the enemy telegraph colours.

The ramps in REGION and SIGNAL below are the source of the hex values in the guide.
Run: python3 tools/art_direction/style_reference.py   (needs Pillow)
"""

import os
import random
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "art_proto"))
from pixel import BASE_RAMPS, Canvas, hx  # noqa: E402

OUT = os.path.join(ROOT, "docs", "art-direction", "style_reference.png")
NPC_BRANCH = "origin/feature/npc-release-batch2-fix"

# ------------------------------------------------------------------ ramps (the master palette)

HERO = {
    "hair": ["#2a160c", "#4e2e1a", "#7a4a2a", "#a8703f", "#d09a62"],
    "cloak": ["#10180e", "#3e6234", "#6a9048", "#8eb062", "#b8d48a"],
    "lining": ["#10180e", "#1e3424", "#2a4632", "#3a5a40", "#4a6c50"],
    "shirt": ["#4a4640", "#a8a296", "#e4e0d6", "#f6f4ee", "#ffffff"],
    "water": ["#0e3050", "#2a6a9a", "#5aa0d0", "#a8dcf8", "#f4fcff"],
}
NPC = {
    "elder.robe": ["#0c1024", "#1c2850", "#2c3e74", "#44609c", "#6a88c2"],
    "elder.sash": ["#26080e", "#661824", "#962a36", "#bc4650", "#de7a7a"],
    "woman.apron": ["#3a2a08", "#8a6a20", "#b8902e", "#d8b04a", "#f0d27a"],
    "woman.skirt": ["#1c1028", "#4a2c5c", "#6a447e", "#8a649c", "#ac8cbc"],
    "merchant.vest": ["#22070c", "#5c1622", "#8a2632", "#b2404a", "#d4686c"],
    "guard.coat": ["#10161e", "#2e3e50", "#4a6078", "#6a849c", "#98b2c6"],
}
# terrain: drawn without outline, mostly tones 1-3 (see the guide, section 3)
REGION = {
    "plains.grass": ["#16301c", "#2a5030", "#3c6a38", "#528446", "#6c9e58"],
    "plains.path": ["#3a2c1e", "#6a5238", "#8c7050", "#a88c68", "#c4aa84"],
    "earth.face": ["#1c140e", "#3a2a1c", "#57402a", "#74583a", "#927450"],
    "desert.sand": ["#3e1e12", "#82442a", "#a8603c", "#c27e54", "#daa274"],
    "desert.stone": ["#2e2018", "#6a5240", "#947a60", "#b49a7c", "#d2bc9e"],
    "forest.moss": ["#0c1c16", "#183426", "#244834", "#345e42", "#4a7654"],
    "forest.pine": ["#08161a", "#123028", "#1c443a", "#2a5a4c", "#3e7462"],
    "forest.swamp": ["#10160e", "#232e1c", "#36402a", "#4a5438", "#62684a"],
    "mount.rock": ["#1c1a24", "#3a3846", "#585668", "#7a788c", "#9e9cb0"],
    "mount.snow": ["#3a4866", "#7a8cae", "#b8c8e0", "#dce6f2", "#f8fbff"],
    "mount.ice": ["#16344a", "#346684", "#5e98b4", "#9cc8dc", "#dcf2fa"],
    "lake.grass": ["#12302a", "#244e3e", "#36684c", "#4a825a", "#669c6c"],
    "lake.shore": ["#4e4230", "#9a8866", "#c0ae88", "#d8caa6", "#eee4c8"],
    "lake.deep": ["#081c34", "#143e66", "#22608e", "#3a84b2", "#6aaed2"],
    "ruin.stone": ["#1a1e22", "#3a4246", "#5a6468", "#7c8688", "#a2aaaa"],
    "ruin.glow": ["#08302e", "#146a64", "#22a49a", "#62d6c6", "#c6fff0"],
    "room.plaster": ["#3a3028", "#7a6a58", "#a8967e", "#c4b49c", "#e0d4c0"],
    "room.rug": ["#2a0a10", "#5a1a22", "#7e2a30", "#a04440", "#c06a5a"],
    "cave.rock": ["#0c0c12", "#1c1c26", "#2c2c3a", "#403e52", "#585670"],
}
# reserved colours: only for what the name says (section 5)
SIGNAL = {
    "miasma(enemy)": ["#120a1a", "#2e1a3e", "#4a2a62", "#6e4490", "#9a70c0"],
    "enemy.magic": ["#2a0a2a", "#6a1e6a", "#b040b0", "#e070e0", "#ffc8ff"],
    "telegraph": ["#3a0808", "#a01818", "#ff3a3a", "#ff8a7a", "#ffffff"],
    "flinch": ["#0a1a3a", "#2a4a90", "#60a0ff", "#a8ccff", "#ffffff"],
}
SEASON = {  # PROPOSAL: the plains grass ramp, shifted per season
    "autumn.grass": ["#2e2010", "#5e4420", "#8a6630", "#a88440", "#c4a058"],
    "winter.snow": ["#3a4866", "#7a8cae", "#b8c8e0", "#dce6f2", "#f8fbff"],
}

BG_DARK = (0x20, 0x24, 0x2C)
PAPER = (0x2A, 0x2E, 0x38)
INK = (0xE8, 0xEA, 0xF0)
SUB = (0x9A, 0xA0, 0xB0)
GOOD = (0x6A, 0xD0, 0x6A)
BAD = (0xFF, 0x5A, 0x5A)


def font(size):
    for f in ("DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)


F_H = font(20)
F_T = font(13)
F_S = font(11)


# ------------------------------------------------------------------ sprites

def load_png(rel):
    """A release PNG: from the working tree, else from the NPC branch (not merged yet)."""
    p = os.path.join(ROOT, rel)
    if os.path.exists(p):
        return Image.open(p).convert("RGBA")
    data = subprocess.run(["git", "-C", ROOT, "show", f"{NPC_BRANCH}:{rel}"], capture_output=True, check=True).stdout
    import io

    return Image.open(io.BytesIO(data)).convert("RGBA")


def to_image(px):
    h, w = len(px), len(px[0])
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for y in range(h):
        for x in range(w):
            if px[y][x]:
                im.putpixel((x, y), tuple(px[y][x]))
    return im


def chest(open_=False, ramps=None):
    """A chest drawn by the rules (pixel.py: materials, top-left light, selective outline)."""
    c = Canvas(32, 28, ramps or {})
    c.rect(4, 13, 27, 26, "wood")  # body
    for x in (4, 27):
        c.rect(x, 13, x, 26, "wood", 1)
    for x in range(6, 26, 5):
        c.strand(x, 15, x, 25, 1)  # planks
    c.rect(4, 13, 27, 14, "gold")  # band
    c.rect(14, 15, 17, 19, "gold")  # lock
    c.put(15, 17, "gold", 0)
    c.put(16, 17, "gold", 0)
    if open_:
        c.rect(5, 4, 26, 9, "wood", 1)  # lid seen from inside, tilted back
        c.rect(5, 10, 26, 12, "wood", 0)  # dark inside
        c.rect(9, 10, 22, 11, "gem", 3)  # treasure glint
        c.put(12, 10, "gem", 4)
        c.put(19, 10, "gem", 4)
    else:
        c.ellipse(16, 12, 12.5, 6.0, "wood")  # rounded lid
        c.rect(4, 11, 27, 13, "wood")
        c.rect(14, 6, 17, 13, "gold")  # band over the lid
        for y in (9,):
            c.strand(6, y, 25, y, 3)
    return c


def chest_px(open_=False):
    return to_image(chest(open_).colours())


def chest_bad_outline():
    """DON'T: one black outline everywhere and the light from the bottom right."""
    c = chest()
    px = c.colours()
    for y in range(c.h):
        for x in range(c.w):
            m = c.mat[y][x]
            if m is None:
                if px[y][x]:
                    px[y][x] = (0, 0, 0, 255)
                continue
            t = c.tone[y][x]
            if t is None:
                r = c.ramps[m]
                cur = tuple(px[y][x][:3])
                if cur in r:
                    t = r.index(cur)
                    px[y][x] = r[{1: 3, 3: 1, 4: 1}.get(t, t)] + (255,)
    for y in range(c.h):  # black lines also inside, between materials
        for x in range(c.w):
            if c.mat[y][x] == "gold" and any(c.m(x + dx, y + dy) == "wood" for dx, dy in ((1, 0), (0, 1))):
                px[y][x] = (0, 0, 0, 255)
    return to_image(px)


def chest_bad_aa():
    """DON'T: smoothed edges, half-transparent pixels."""
    im = chest_px().resize((64, 56), Image.NEAREST).resize((32, 28), Image.BILINEAR)
    big = im.resize((128, 112), Image.BICUBIC)
    return big.resize((32, 28), Image.LANCZOS)


def chest_bad_upscale():
    """DON'T: a small picture blown up 2x (blocks of 2x2)."""
    return chest_px().resize((16, 14), Image.NEAREST).resize((32, 28), Image.NEAREST)


def chest_bad_flat():
    """DON'T: flat colours, no ramp (no shadow, no light)."""
    c = chest()
    px = c.colours()
    for y in range(c.h):
        for x in range(c.w):
            m = c.mat[y][x]
            if m is not None:
                px[y][x] = c.ramps[m][2] + (255,)
    return to_image(px)


def chest_bad_noise():
    """DON'T: random single pixels / dithering that read as dirt at game size."""
    im = chest_px()
    rnd = random.Random(3)
    w = BASE_RAMPS["wood"]
    for y in range(13, 27):
        for x in range(4, 28):
            if (x + y) % 2 == 0 and rnd.random() < 0.55 and im.getpixel((x, y))[3]:
                im.putpixel((x, y), hx(w[rnd.choice((1, 3, 4))]) + (255,))
    return im


def plate(on):
    """An interactive switch plate (sw.plate), 28x20: off = dull, on = sunk + glowing."""
    c = Canvas(28, 20, {"ruin": REGION["ruin.stone"], "glow": REGION["ruin.glow"]})
    c.ellipse(14, 12, 13, 7, "ruin")
    c.ellipse(14, 12 + (1 if on else 0), 9, 4.5, "ruin", 1 if on else None)
    if on:
        c.ellipse(14, 13, 6, 2.6, "glow")
        c.rect(12, 12, 15, 13, "glow", 4)
    else:
        c.ellipse(14, 11, 6, 2.6, "ruin", 1)
    return to_image(c.colours())


def blob():
    """A small miasma enemy for the telegraph demo."""
    c = Canvas(32, 26, {"miasma": SIGNAL["miasma(enemy)"], "magic": SIGNAL["enemy.magic"]})
    c.ellipse(16, 16, 13, 9, "miasma")
    c.poly([(8, 12), (12, 3), (15, 11)], "miasma")
    c.poly([(17, 11), (21, 2), (24, 12)], "miasma")
    c.ellipse(16, 17, 4, 3, "magic")
    c.put(15, 16, "magic", 4)
    c.paint(11, 13, "#ffd84a")
    c.paint(21, 13, "#ffd84a")
    return to_image(c.colours())


def tint(im, rgb, k):
    out = im.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if a:
                px[x, y] = (round(r + (rgb[0] - r) * k), round(g + (rgb[1] - g) * k), round(b + (rgb[2] - b) * k), 255)
    return out


# ------------------------------------------------------------------ terrain

def ground_tile(ramp, seed=1, tufts=7, path_ramp=None):
    """A seamless 32x32 ground tile: core tone, tufts that wrap around the edges, no outline."""
    r = [hx(c) for c in ramp]
    im = Image.new("RGBA", (32, 32), r[2] + (255,))
    rnd = random.Random(seed)

    def put(x, y, t):
        im.putpixel((x % 32, y % 32), r[t] + (255,))

    for _ in range(tufts):  # tufts: light blades over a shadow foot
        x, y = rnd.randrange(32), rnd.randrange(32)
        for dx, h in ((0, 3), (2, 2), (-2, 2)):
            for k in range(h):
                put(x + dx, y - k, 3)
            put(x + dx, y + 1, 1)
        put(x, y - 3, 4)
    for _ in range(6):  # soft darker patches, 2x1
        x, y = rnd.randrange(32), rnd.randrange(32)
        put(x, y, 1)
        put(x + 1, y, 1)
    if path_ramp:
        p = [hx(c) for c in path_ramp]
        for y in range(32):
            for x in range(10, 22):
                edge = x in (10, 21) and rnd.random() < 0.5
                if not edge:
                    im.putpixel((x, y), p[2] + (255,))
            im.putpixel((10, y), r[1] + (255,)) if y % 3 else None  # grass shadow on the path's left lip
            im.putpixel((21, y), p[3] + (255,)) if y % 4 == 0 else None
        for _ in range(8):  # pebbles: light on top, shadow under
            x, y = rnd.randrange(12, 20), rnd.randrange(32)
            im.putpixel((x, y), p[3] + (255,))
            im.putpixel((x, (y + 1) % 32), p[1] + (255,))
    return im


def cliff_face(ramp, top_ramp):
    """face.earth top 8 + mid 16 + base 8 (32x32 total): lip lit, darker towards the ground."""
    r = [hx(c) for c in ramp]
    g = [hx(c) for c in top_ramp]
    im = Image.new("RGBA", (32, 32), r[2] + (255,))
    for x in range(32):
        im.putpixel((x, 0), g[3] + (255,))  # the lit grass lip
        im.putpixel((x, 1), g[1] + (255,))
        im.putpixel((x, 2), r[3] + (255,))  # the edge catches the light
        for y in range(3, 32):
            band = 3 if y < 8 else 2 if y < 22 else 1
            im.putpixel((x, y), r[band] + (255,))
        im.putpixel((x, 31), r[0] + (255,))  # contact line with the ground
        im.putpixel((x, 30), r[0] + (255,)) if x % 5 else None
    rnd = random.Random(7)
    for _ in range(9):  # strata / stones: light top-left, shadow bottom-right
        x, y = rnd.randrange(1, 28), rnd.randrange(5, 27)
        for dx in range(3):
            im.putpixel((x + dx, y), r[3] + (255,))
            im.putpixel((x + dx + 1, y + 1), r[1] + (255,))
    return im


def tiled(tile, nx, ny):
    out = Image.new("RGBA", (tile.width * nx, tile.height * ny))
    for j in range(ny):
        for i in range(nx):
            out.paste(tile, (i * tile.width, j * tile.height))
    return out


def seam_bad(ramp):
    """DON'T: a tile whose features stop at the edge (a grid shows when repeated)."""
    r = [hx(c) for c in ramp]
    im = Image.new("RGBA", (32, 32), r[2] + (255,))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 31, 1), fill=r[3] + (255,))
    d.rectangle((0, 0, 1, 31), fill=r[3] + (255,))
    d.rectangle((0, 30, 31, 31), fill=r[1] + (255,))
    d.rectangle((12, 12, 18, 18), fill=r[4] + (255,))
    return im


def recolour(im, src, dst):
    m = {hx(a): hx(b) for a, b in zip(src, dst)}
    out = im.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            p = px[x, y]
            if p[3] and p[:3] in m:
                px[x, y] = m[p[:3]] + (255,)
    return out


def winter(im):
    """PROPOSAL: grass -> snow ramp, then hand-placed bare-grass spots stay on top."""
    out = recolour(im, REGION["plains.grass"], SEASON["winter.snow"])
    g = [hx(c) for c in REGION["plains.grass"]]
    for x, y in ((5, 6), (6, 6), (22, 20), (23, 20), (23, 19), (14, 27)):
        out.putpixel((x, y), g[1] + (255,))
    return out


def autumn(im):
    """PROPOSAL: grass -> autumn ramp, plus hand-placed fallen leaves."""
    out = recolour(im, REGION["plains.grass"], SEASON["autumn.grass"])
    leaf = [hx(c) for c in ("#5a1a0a", "#c0461c", "#f08a3a")]
    for x, y in ((7, 9), (20, 4), (26, 22), (12, 25)):
        out.putpixel((x, y), leaf[1] + (255,))
        out.putpixel((x + 1, y), leaf[2] + (255,))
        out.putpixel((x, y + 1), leaf[0] + (255,))
    return out


# ------------------------------------------------------------------ layout

class Sheet:
    def __init__(self, w, h):
        self.im = Image.new("RGB", (w, h), BG_DARK)
        self.d = ImageDraw.Draw(self.im)

    def text(self, xy, s, f=F_T, fill=INK):
        self.d.text(xy, s, font=f, fill=fill)

    def panel(self, box, title):
        self.d.rectangle(box, fill=PAPER)
        self.text((box[0] + 10, box[1] + 6), title, F_H)

    def sprite(self, im, xy, k, bg=None):
        big = im.resize((im.width * k, im.height * k), Image.NEAREST)
        if bg is not None:
            self.im.paste(bg.resize((bg.width * k, bg.height * k), Image.NEAREST), xy)
        self.im.paste(big, xy, big)
        return big.width, big.height

    def ramp(self, xy, name, ramp, sw=16):
        x, y = xy
        for i, c in enumerate(ramp):
            self.d.rectangle((x + i * sw, y, x + i * sw + sw - 1, y + sw - 1), fill=hx(c))
        self.text((x + 5 * sw + 6, y + 1), name, F_S)


def main():
    S = Sheet(1600, 1356)
    S.text((20, 14), "Seikan no Regalia - art style reference v1.0  (docs/art-direction/ART_STYLE_GUIDE.md)", F_H)
    S.text((20, 40), "5-tone ramps: 0 outline, 1 shadow, 2 core, 3 light, 4 highlight.  Light from the top left.  "
           "Selective outline.  No anti-aliasing, no half-transparent pixels.", F_T, SUB)

    # A. ramps -------------------------------------------------------------
    S.panel((16, 66, 1584, 520), "A. Master palette (all ramps)")
    groups = [
        ("Shared character materials", BASE_RAMPS),
        ("Hero only", HERO),
        ("NPC samples", NPC),
        ("Terrain / regions", REGION),
        ("Signal (reserved)", SIGNAL),
        ("Season (PROPOSAL)", SEASON),
    ]
    col_x = [30, 300, 570, 840, 1120, 1120]
    col_y = [100, 100, 100, 100, 100, 330]
    for (title, ramps), x, y in zip(groups, col_x, col_y):
        S.text((x, y), title, F_T, SUB)
        y += 20
        for name, r in ramps.items():
            S.ramp((x, y), name, r)
            y += 20
            if title.startswith("Terrain") and y > 500:
                x, y = x + 140, 120
    S.text((1300, 120), "tone index:", F_S, SUB)
    for i in range(5):
        S.text((1300 + i * 16 + 4, 136), str(i), F_S, SUB)

    # B. characters ----------------------------------------------------------
    S.panel((16, 530, 1000, 870), "B. Approved characters on plains grass (4x, and 1x = real size)")
    grass = ground_tile(REGION["plains.grass"], seed=4)
    bg = tiled(grass, 2, 2).crop((0, 0, 36, 60))
    chars = [
        ("src/art-release/hero/hero.idle.down.0.png", "hero idle down"),
        ("src/art-release/hero/hero.idle.right.0.png", "hero idle right"),
        ("src/art-release/npc/npc.elder.idle.down.0.png", "NPC elder"),
        ("src/art-release/npc/npc.woman.idle.down.0.png", "NPC woman"),
    ]
    x = 30
    for path, label in chars:
        im = load_png(path)
        b = bg.copy()
        b.alpha_composite(im, (2, 2))
        S.sprite(b, (x, 568), 4)
        S.text((x, 812), label, F_S, SUB)
        x += 36 * 4 + 14
    x1 = x + 10
    S.text((x1, 568), "1x (game screen,", F_S, SUB)
    S.text((x1, 582), "2 art px = 1 game px)", F_S, SUB)
    for i, (path, _) in enumerate(chars):
        b = bg.copy()
        b.alpha_composite(load_png(path), (2, 2))
        S.sprite(b, (x1 + (i % 2) * 44, 604 + (i // 2) * 70), 1)
    S.text((30, 834), "Check: the hero's cloak (#6a9048) is yellower and brighter than the grass core (#3c6a38); "
           "outlines keep every character off the ground.", F_S, SUB)

    # C. terrain -------------------------------------------------------------
    S.panel((1010, 530, 1584, 870), "C. Terrain (32x32, seamless)")
    path = ground_tile(REGION["plains.grass"], seed=4, path_ramp=REGION["plains.path"])
    field = Image.new("RGBA", (96, 64))
    field.paste(tiled(grass, 3, 2), (0, 0))
    field.paste(path, (32, 0))
    field.paste(path, (32, 32))
    S.sprite(field, (1026, 568), 2)
    S.text((1026, 700), "grass x6 + path x2 (repeat with no seam)", F_S, SUB)
    face = cliff_face(REGION["earth.face"], REGION["plains.grass"])
    S.sprite(face, (1230, 568), 2)
    S.text((1230, 636), "cliff face:", F_S, SUB)
    S.text((1230, 650), "lit lip, darker", F_S, SUB)
    S.text((1230, 664), "to the ground", F_S, SUB)
    S.sprite(tiled(seam_bad(REGION["plains.grass"]), 2, 2), (1340, 568), 1)
    S.d.rectangle((1338, 566, 1405, 633), outline=BAD, width=2)
    S.text((1412, 568), "DON'T: features", F_S, BAD)
    S.text((1412, 582), "stop at the edge", F_S, BAD)
    S.text((1412, 596), "(a grid shows)", F_S, BAD)
    xs = 1026
    for lab, t in (("summer (base)", grass), ("autumn PROPOSAL", autumn(grass)), ("winter PROPOSAL", winter(grass))):
        S.sprite(tiled(t, 2, 1), (xs, 730), 2)
        S.text((xs, 864 - 12), lab, F_S, SUB)
        xs += 140 + 50

    # D. do / don't ----------------------------------------------------------
    S.panel((16, 880, 1584, 1340), "D. Do / Don't  (same chest, 32x28, drawn with tools/art_proto/pixel.py)")
    items = [
        ("DO", chest_px(), "ramps, top-left light,", "selective outline", GOOD),
        ("DON'T", chest_bad_outline(), "black outline +", "light from bottom right", BAD),
        ("DON'T", chest_bad_aa(), "smoothed edges,", "half-transparent pixels", BAD),
        ("DON'T", chest_bad_upscale(), "small art blown up 2x", "(2x2 blocks)", BAD),
        ("DON'T", chest_bad_flat(), "flat colours,", "no ramp", BAD),
        ("DON'T", chest_bad_noise(), "dithering / single-", "pixel noise", BAD),
    ]
    x = 30
    for tag, im, l1, l2, col in items:
        b = Image.new("RGBA", (34, 30), hx(REGION["plains.grass"][2]) + (255,))
        b.alpha_composite(im, (1, 1))
        S.sprite(b, (x, 950), 5)
        S.d.rectangle((x - 3, 947, x + 34 * 5 + 2, 947 + 30 * 5 + 5), outline=col, width=3)
        S.text((x, 920), tag, F_T, col)
        S.text((x, 1110), l1, F_S, SUB)
        S.text((x, 1124), l2, F_S, SUB)
        x += 34 * 5 + 22
    # check box: the "flat" one
    # interactive objects
    y = 1160
    S.text((30, y), "Interactive objects: 2 states that differ in SHAPE and LIGHT", F_T)
    x = 30
    for lab, im in (("chest closed", chest_px()), ("chest open", chest_px(True)), ("plate off", plate(False)), ("plate on", plate(True))):
        b = Image.new("RGBA", (im.width + 2, 30), hx(REGION["plains.grass"][2]) + (255,))
        b.alpha_composite(im, (1, 30 - im.height - 1))
        S.sprite(b, (x, y + 24), 4)
        S.text((x, y + 24 + 124), lab, F_S, SUB)
        x += (im.width + 2) * 4 + 18
    # telegraph
    x = 760
    S.text((x, y), "Enemy colour signals (tinted by the game, not drawn into the sprite)", F_T)
    e = blob()
    for lab, im in (
        ("normal (miasma purple)", e),
        ("wind-up: red #ff3a3a 50%", tint(e, (0xFF, 0x3A, 0x3A), 0.5)),
        ("strike: white flash", tint(e, (0xFF, 0xFF, 0xFF), 0.85)),
        ("flinch: blue #60a0ff 50%", tint(e, (0x60, 0xA0, 0xFF), 0.5)),
    ):
        b = Image.new("RGBA", (34, 28), hx(REGION["plains.grass"][2]) + (255,))
        b.alpha_composite(im, (1, 1))
        S.sprite(b, (x, y + 24), 4)
        S.text((x, y + 24 + 116), lab, F_S, SUB)
        x += 34 * 4 + 22

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    S.im.save(OUT, optimize=True)
    print("wrote", OUT, S.im.size)


if __name__ == "__main__":
    main()
