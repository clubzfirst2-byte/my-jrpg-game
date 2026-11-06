"""P12 hero PROTOTYPE sprites (仮素材 — waiting for the user's approval).

Draws the hero's walk (3 frames x 4 directions; frame 0 is also the idle pose) and swim (2 x 4)
frames as 32x56 transparent PNGs, from shapes in the approved colours (docs/hero/HERO_DESIGN_SPEC.md),
using the prototype sheet (docs/hero/reference/hero_sprite_prototype_sheet.png) as the guide for
poses. Left is the mirror of right, as in the game's placeholder.

Writes src/art-proto/hero/<name>.png (only loaded with ?hero=proto) and a preview sheet.
Run: python3 tools/hero_proto/gen_hero_prototype.py
"""

import os
import struct
import zlib

W, H = 32, 56
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "src", "art-proto", "hero")
PREVIEW = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "hero", "prototype_preview.png")

PAL = {
    "k": (0x1A, 0x1C, 0x2C),  # outline
    "H": (0x7A, 0x4A, 0x2A),  # hair
    "h": (0x4E, 0x2E, 0x1A),  # hair shadow
    "L": (0xA8, 0x70, 0x42),  # hair light
    "s": (0xF2, 0xC4, 0x9B),  # skin
    "S": (0xC8, 0x94, 0x6C),  # skin shadow
    "e": (0x1F, 0x3F, 0x7A),  # eye dark
    "b": (0x3A, 0x90, 0xD8),  # eye blue
    "w": (0xE8, 0xF8, 0xFF),  # eye light
    "m": (0xA8, 0x58, 0x58),  # mouth
    "G": (0x73, 0x93, 0x55),  # cloak
    "g": (0x40, 0x6A, 0x53),  # cloak shadow
    "V": (0x96, 0xB1, 0x88),  # cloak light
    "y": (0xF8, 0xD6, 0x84),  # gold
    "Y": (0xB0, 0x8A, 0x40),  # gold shadow
    "p": (0x2A, 0x8D, 0xE2),  # pendant
    "P": (0xD8, 0xF4, 0xFF),  # pendant glow
    "c": (0xEC, 0xE8, 0xE0),  # shirt
    "C": (0xB8, 0xB2, 0xA8),  # shirt shadow
    "l": (0x7A, 0x5A, 0x3A),  # leather
    "d": (0x4A, 0x34, 0x24),  # leather dark
    "t": (0x3A, 0x3A, 0x4E),  # trousers
    "T": (0x26, 0x26, 0x34),  # trousers shadow
    "o": (0x6A, 0x46, 0x2A),  # boot
    "O": (0x96, 0x6A, 0x42),  # boot light
    "r": (0xCF, 0xE8, 0xFF),  # ripple
    "R": (0x7F, 0xB8, 0xE8),  # ripple shadow
}


class Canvas:
    def __init__(self):
        self.px = [["." for _ in range(W)] for _ in range(H)]

    def put(self, x, y, c):
        if 0 <= x < W and 0 <= y < H:
            self.px[y][x] = c

    def get(self, x, y):
        return self.px[y][x] if 0 <= x < W and 0 <= y < H else "."

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1:
                    self.put(x, y, c)

    def rows(self, x0, y0, rows):
        """Pastes hand-drawn rows ('.' = leave as is)."""
        for dy, row in enumerate(rows):
            for dx, c in enumerate(row):
                if c != ".":
                    self.put(x0 + dx, y0 + dy, c)

    def trapezoid(self, y0, y1, xl0, xr0, xl1, xr1, c):
        for y in range(y0, y1 + 1):
            f = (y - y0) / max(1, y1 - y0)
            xl = round(xl0 + (xl1 - xl0) * f)
            xr = round(xr0 + (xr1 - xr0) * f)
            for x in range(xl, xr + 1):
                self.put(x, y, c)

    def outline(self):
        """A 1-pixel dark outline around everything drawn."""
        add = []
        for y in range(H):
            for x in range(W):
                if self.px[y][x] != ".":
                    continue
                if any(self.get(x + dx, y + dy) not in (".", "k") for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    add.append((x, y))
        for x, y in add:
            self.px[y][x] = "k"

    def mirrored(self):
        m = Canvas()
        m.px = [list(reversed(r)) for r in self.px]
        return m

    def shifted(self, dy, cut_from=None):
        """Moves everything down by dy; rows at or below `cut_from` (before moving) are dropped."""
        m = Canvas()
        for y in range(H):
            if cut_from is not None and y >= cut_from:
                continue
            ny = y + dy
            if 0 <= ny < H:
                m.px[ny] = list(self.px[y])
        return m


# ---------------------------------------------------------------- heads (rows 0..23)

def head_front(c, bob=0):
    y = bob
    # hair mass: big and round, messy
    c.ellipse(15.5, 11 + y, 11.5, 10.5, "H")
    c.rows(4, 0 + y, [
        "...........hh...........",
        "..........hHHh..........",
        "....hh...HHHHHh..hh.....",
        "...hHHhhHHHHHHHHhHHh....",
    ])
    for x, yy in ((4, 8), (3, 10), (4, 13), (26, 9), (27, 12), (26, 15)):  # side tufts
        c.rect(x, yy + y, x + 1, yy + 1 + y, "H")
    # highlights and strands
    c.rows(7, 4 + y, [
        "..LLLL....LLL....",
        ".LLHHLL..LLHLL...",
        "..........h...h..",
    ])
    # face
    c.rect(9, 11 + y, 22, 19 + y, "s")
    c.rect(10, 20 + y, 21, 20 + y, "s")
    c.rect(12, 21 + y, 19, 21 + y, "s")
    c.rect(9, 18 + y, 9, 20 + y, "S")
    c.rect(22, 18 + y, 22, 20 + y, "S")
    # fringe: asymmetric, longer on his right (screen left)
    c.rows(8, 9 + y, [
        "HHHHHHHHHHHHHHHH",
        "HHHhHHHHHHHhHHHH",
        "HHh.HHHHHHh.HhHH",
        "Hh..HHhHHh...hHH",
        "H...Hh.Hh.....hH",
        "h...h...h......h",
    ])
    # eyes (narrow, blue)
    for ex in (11, 18):
        c.rows(ex, 15 + y, ["eee", "bbw", "ebb"])
    c.rect(15, 20 + y, 16, 20 + y, "m")
    # locks of hair along the cheeks
    c.rect(7, 13 + y, 8, 20 + y, "H")
    c.rect(23, 13 + y, 24, 19 + y, "H")
    c.rect(7, 18 + y, 7, 21 + y, "h")


def head_back(c, bob=0):
    y = bob
    c.ellipse(15.5, 11 + y, 11.5, 10.5, "H")
    c.rows(4, 0 + y, [
        "...........hh...........",
        "..........hHHh..........",
        "....hh...HHHHHh..hh.....",
        "...hHHhhHHHHHHHHhHHh....",
    ])
    for x, yy in ((4, 8), (3, 10), (4, 13), (26, 9), (27, 12), (26, 15)):
        c.rect(x, yy + y, x + 1, yy + 1 + y, "H")
    c.rows(7, 5 + y, [
        "..LLLL....LLLL...",
        ".LLHHLL..LLHHLL..",
        "...h...h....h....",
        "....h....h...h...",
        "..h...h....h..h..",
        "...h....h....h...",
    ])
    # nape: hair tips over the neck
    c.rows(9, 19 + y, [
        "HHhHHHHhHHHhHH",
        ".hH.hHHh.Hh.h.",
        "..h..hh...h...",
    ])


def head_side(c, bob=0):
    """Facing right (3/4 view, as in the sheet)."""
    y = bob
    c.ellipse(15.0, 11 + y, 11.0, 10.5, "H")
    c.rows(3, 0 + y, [
        "..........hh............",
        ".........hHHh...........",
        "...hh...HHHHHh..hh......",
        "..hHHhhHHHHHHHHhHHh.....",
    ])
    for x, yy in ((3, 8), (2, 11), (3, 14), (4, 17), (25, 8)):
        c.rect(x, yy + y, x + 1, yy + 1 + y, "H")
    c.rows(6, 4 + y, [
        "..LLLL...LLL....",
        ".LLHHLL.LLHLL...",
    ])
    # face to the right
    c.rect(14, 11 + y, 24, 19 + y, "s")
    c.rect(15, 20 + y, 23, 20 + y, "s")
    c.rect(17, 21 + y, 22, 21 + y, "s")
    c.rect(25, 15 + y, 25, 18 + y, "s")  # nose / cheek line
    c.rect(15, 17 + y, 15, 19 + y, "S")  # ear shadow
    c.rows(13, 9 + y, [
        "HHHHHHHHHHHH",
        "HHHHHhHHHHHH",
        "HHhHH.HhHHHh",
        "Hh.Hh..hHh.h",
        "h...h...h...",
    ])
    c.rows(20, 15 + y, ["eee", "bbw", "ebb"])
    c.rect(23, 20 + y, 23, 20 + y, "m")
    # the hair behind the ear, down the neck (rounded, with strands)
    c.ellipse(10.0, 15.5 + y, 5.0, 6.5, "H")
    c.rows(6, 17 + y, [
        "..h..h...",
        ".h..hh.h.",
        "..h..h..h",
    ])


# ---------------------------------------------------------------- bodies (rows ~21..46)

def body_front(c, sway=0):
    # shirt (long white tunic) with belt
    c.rect(11, 25, 20, 41, "c")
    c.rect(11, 25, 11, 41, "C")
    c.rect(11, 35, 20, 36, "l")
    c.rect(15, 35, 16, 36, "y")
    c.rect(12, 37, 13, 40, "d")  # pouch
    # gloves
    c.rect(9, 36, 10, 39, "l")
    c.rect(21, 36, 22, 39, "l")
    # cloak panels (open at the front), longer at the sides, swaying with the walk
    c.trapezoid(23, 44, 9, 12, 4 + sway, 11, "G")
    c.trapezoid(23, 44, 19, 22, 20, 27 + sway, "G")
    c.trapezoid(23, 44, 9, 10, 4 + sway, 6 + sway, "g")
    c.trapezoid(23, 44, 21, 22, 25 + sway, 27 + sway, "g")
    # gold trim down the front edges and along the hem
    c.trapezoid(25, 44, 12, 12, 11, 11, "y")
    c.trapezoid(25, 44, 19, 19, 20, 20, "y")
    for x in range(4 + sway, 12):
        c.put(x, 44, "y")
    for x in range(20, 28 + sway):
        c.put(x, 44, "y")
    for x, y in ((6, 33), (8, 39), (24, 31), (25, 38)):  # embroidery dots
        c.put(x + (sway if x < 16 else 0), y, "Y")
    # hood / collar over the shoulders, the gold clasp and the pendant
    c.rect(9, 22, 22, 24, "V")
    c.rect(8, 23, 23, 24, "G")
    c.rect(9, 22, 22, 22, "G")
    c.rect(13, 23, 13, 23, "y")
    c.rect(18, 23, 18, 23, "y")
    c.rows(13, 25, [
        "..yyyy..",
        ".yYppYy.",
        ".ypPPpy.",
        "..ypPy..",
        "...yy...",
    ])


def body_back(c, sway=0):
    c.rect(9, 36, 10, 39, "l")
    c.rect(21, 36, 22, 39, "l")
    c.trapezoid(22, 46, 8, 23, 4 + sway, 27 + sway, "G")
    c.trapezoid(22, 46, 8, 9, 4 + sway, 6 + sway, "g")
    c.trapezoid(22, 46, 22, 23, 25 + sway, 27 + sway, "g")
    for x in range(4 + sway, 28 + sway):
        c.put(x, 46, "y")
    # folded hood
    c.rect(9, 22, 22, 25, "V")
    c.rect(10, 26, 21, 26, "G")
    c.rect(9, 25, 22, 25, "g")
    # the gold star on the back
    cx, cy = 15 + sway // 2, 34
    c.rows(cx - 4, cy - 4, [
        "....y....",
        "....y....",
        ".y..y..y.",
        "..yyyyy..",
        "yyyyPyyyy",
        "..yyyyy..",
        ".y..y..y.",
        "....y....",
        "....y....",
    ])
    for x, y in ((7, 30), (8, 41), (23, 30), (24, 41)):
        c.put(x, y, "Y")


def body_side(c, sway=0):
    """Facing right: the cloak flows behind (to the left)."""
    c.rect(14, 25, 21, 41, "c")
    c.rect(14, 25, 15, 41, "C")
    c.rect(14, 35, 21, 36, "l")
    c.rect(19, 35, 20, 36, "y")
    c.rect(20, 33, 22, 38, "l")  # front arm / glove
    c.rect(21, 37, 22, 38, "d")
    # cloak behind
    c.trapezoid(23, 45, 9, 16, 3 - sway, 15, "G")
    c.trapezoid(23, 45, 9, 10, 3 - sway, 5 - sway, "g")
    c.trapezoid(25, 45, 15, 15, 15, 15, "y")
    for x in range(3 - sway, 16):
        c.put(x, 45, "y")
    for x, y in ((6, 32), (8, 39), (11, 28)):
        c.put(x - (sway if y > 35 else 0), y, "Y")
    # hood / collar and the pendant on the chest
    c.rect(10, 22, 20, 24, "V")
    c.rect(9, 23, 20, 24, "G")
    c.rect(10, 22, 20, 22, "G")
    c.rows(19, 25, [
        ".yyy.",
        "yYpYy",
        "ypPpy",
        ".ypy.",
        "..y..",
    ])


# ---------------------------------------------------------------- legs (rows 41..55)

def legs_front(c, step):
    """step 0: standing; 1/-1: one foot lifted (the other carries the weight)."""
    for side, x0 in ((-1, 11), (1, 17)):
        lift = 2 if step == side else 0
        c.rect(x0, 42 - lift, x0 + 3, 49 - lift, "t")
        c.rect(x0 + (0 if side < 0 else 3), 42 - lift, x0 + (0 if side < 0 else 3), 49 - lift, "T")
        c.rect(x0 - 1, 49 - lift, x0 + 4, 50 - lift, "O")  # cuff
        c.rect(x0, 51 - lift, x0 + 3, 54 - lift, "o")
        c.rect(x0 - 1, 54 - lift, x0 + 4, 54 - lift, "o")
        c.rect(x0, 51 - lift, x0, 53 - lift, "O")


def legs_side(c, step):
    """Facing right. step 0: together; 1: right leg forward; -1: left leg forward."""
    front = 3 * step
    for dx, shade in ((-front, "T"), (front, "t")):
        x0 = 15 + dx
        c.rect(x0, 42, x0 + 3, 49, shade)
        c.rect(x0 - 1, 49, x0 + 4, 50, "O")
        c.rect(x0, 51, x0 + 3, 54, "o")
        c.rect(x0 + 2, 53, x0 + 5, 54, "o")  # toe pointing right
        c.rect(x0, 51, x0, 53, "O")


# ---------------------------------------------------------------- frames

def frame(direction, step):
    c = Canvas()
    if direction == "down":
        legs_front(c, step)
        body_front(c, sway=-step)
        head_front(c, bob=0 if step == 0 else 1)
    elif direction == "up":
        legs_front(c, step)
        body_back(c, sway=step)
        head_back(c, bob=0 if step == 0 else 1)
    else:
        legs_side(c, step)
        body_side(c, sway=abs(step))
        head_side(c, bob=0 if step == 0 else 1)
    c.outline()
    return c


def swim_frame(direction, f):
    # Head and shoulders above the water: the standing frame moved down, cut below the shoulders.
    base = frame(direction, 0)
    c = base.shifted(25, cut_from=27)
    # the water line: a ring of ripples (alternating), a hand stroking on frame 1
    if f == 0:
        c.rows(2, 49, [
            "..rrrrRR........RRrrrr....",
            "rRR....RRrrrrrrRR....RRr..",
            "..RRrr..............rrRR..",
        ])
    else:
        c.rows(2, 49, [
            "....RRrrrr....rrrrRR......",
            "..rrR.....RRRR.....RRrr...",
            "rRR....rrr....rrr.....RRr.",
        ])
        hx = 23 if direction != "up" else 7
        c.rect(hx, 46, hx + 2, 48, "s" if direction != "up" else "l")
    # nothing of the body below the water line
    for y in range(52, H):
        for x in range(W):
            if c.px[y][x] not in ("r", "R"):
                c.px[y][x] = "."
    return c


def png(canvas, scale=1):
    w, h = W * scale, H * scale
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w):
            ch = canvas.px[y // scale][x // scale]
            raw += bytes(PAL[ch]) + b"\xff" if ch != "." else b"\x00\x00\x00\x00"
    return encode(w, h, raw)


def encode(w, h, raw):
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )


def all_frames():
    frames = {}
    for d in ("down", "up", "right"):
        for i, step in enumerate((0, 1, -1)):
            frames[f"player.walk.{d}.{i}"] = frame(d, step)
        for f in (0, 1):
            frames[f"player.swim.{d}.{f}"] = swim_frame(d, f)
    for k in [k for k in frames if ".right." in k]:
        frames[k.replace(".right.", ".left.")] = frames[k].mirrored()
    return frames


def preview(frames, path, scale=4):
    """All frames in a grid on a neutral background (rows: down, up, right, left)."""
    order = [f"player.walk.{{d}}.{i}" for i in range(3)] + [f"player.swim.{{d}}.{f}" for f in range(2)]
    dirs = ("down", "up", "right", "left")
    gap = 4
    cw, ch = (W + gap) * len(order) + gap, (H + gap) * len(dirs) + gap
    bg = (0x5F, 0x8A, 0x4E)
    raw = bytearray()
    for Y in range(ch * scale):
        raw.append(0)
        for X in range(cw * scale):
            x, y = X // scale, Y // scale
            col, row = (x - gap) // (W + gap), (y - gap) // (H + gap)
            fx, fy = (x - gap) % (W + gap), (y - gap) % (H + gap)
            c = "."
            if 0 <= col < len(order) and 0 <= row < len(dirs) and fx < W and fy < H and x >= gap and y >= gap:
                c = frames[order[col].format(d=dirs[row])].px[fy][fx]
            raw += bytes(PAL[c] if c != "." else bg) + b"\xff"
    with open(path, "wb") as f:
        f.write(encode(cw * scale, ch * scale, raw))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    frames = all_frames()
    for name, canvas in frames.items():
        with open(os.path.join(OUT, f"{name}.png"), "wb") as f:
            f.write(png(canvas))
    preview(frames, PREVIEW)
    print(f"{len(frames)} frames -> src/art-proto/hero/, preview -> docs/hero/prototype_preview.png")
