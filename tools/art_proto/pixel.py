"""Shared pixel-art drawing for the P12 prototypes (仮素材): NPCs and enemies.

The same method as the approved hero v2 (tools/hero_proto/gen_hero_prototype.py), for any size:
  * parts are drawn as MATERIALS, each with a ramp of 5 tones (outline, shadow, core, light, highlight);
  * a shading pass lights every material from the top left;
  * a selective outline gives each outside edge the darkest tone of the material it borders.
"""

import struct
import zlib


def hx(s):
    return (int(s[1:3], 16), int(s[3:5], 16), int(s[5:7], 16))


# Materials shared by every character (the hero's own ramps, so the world reads as one style)
BASE_RAMPS = {
    "skin": ["#6e3e2c", "#c8906a", "#f2c49b", "#ffdcbc", "#fff0e0"],
    "leather": ["#24160c", "#4a3020", "#704c30", "#946c46", "#b88c5e"],
    "boot": ["#1e120a", "#3e2616", "#62402a", "#865c3c", "#a87a52"],
    "trousers": ["#14141c", "#22222e", "#323244", "#44445a", "#585872"],
    "gold": ["#5a4018", "#a07a30", "#e8c060", "#f8dc88", "#fff4c8"],
    "gem": ["#0e2a60", "#1a5cb8", "#2a8de2", "#78c8ff", "#e0f6ff"],
    "wood": ["#1e1008", "#4a2c16", "#6e4424", "#906038", "#b07e50"],
    "steel": ["#1a1e26", "#4a5260", "#7a8494", "#a8b2c0", "#e0e6ee"],
    "bone": ["#3a3226", "#9a8c70", "#d0c4a4", "#e8dec4", "#fff8e4"],
}
SHINY = ("hair", "gem", "gold", "steel", "beard")


class Canvas:
    """Material ids (with a tone override) per pixel; `colours()` turns them into RGBA."""

    def __init__(self, w, h, ramps):
        self.w, self.h = w, h
        self.ramps = {k: [hx(c) for c in v] for k, v in {**BASE_RAMPS, **ramps}.items()}
        self.mat = [[None] * w for _ in range(h)]
        self.tone = [[None] * w for _ in range(h)]
        self.rgb = [[None] * w for _ in range(h)]

    def inside(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def put(self, x, y, m, tone=None):
        if self.inside(x, y):
            self.mat[y][x], self.tone[y][x], self.rgb[y][x] = m, tone, None

    def paint(self, x, y, rgb):
        if self.inside(x, y) and self.mat[y][x] is not None:
            self.rgb[y][x] = rgb if isinstance(rgb, tuple) else hx(rgb)

    def shade(self, x, y, tone):
        if self.inside(x, y) and self.mat[y][x] is not None:
            self.tone[y][x] = tone

    def m(self, x, y):
        return self.mat[y][x] if self.inside(x, y) else None

    def rect(self, x0, y0, x1, y1, m, tone=None):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, m, tone)

    def ellipse(self, cx, cy, rx, ry, m, tone=None):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1:
                    self.put(x, y, m, tone)

    def poly(self, pts, m, tone=None):
        ys = [p[1] for p in pts]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            yc = y + 0.5
            xs = []
            for i in range(len(pts)):
                (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % len(pts)]
                if (y0 <= yc < y1) or (y1 <= yc < y0):
                    xs.append(x0 + (yc - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for a, b in zip(xs[::2], xs[1::2]):
                for x in range(int(round(a)), int(round(b))):
                    self.put(x, y, m, tone)

    def line(self, x0, y0, x1, y1, m, tone=None):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            self.put(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), m, tone)

    def strand(self, x0, y0, x1, y1, tone):
        """A line of another tone over what is drawn (adds no pixels)."""
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            self.shade(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), tone)

    def colours(self):
        out = [[None] * self.w for _ in range(self.h)]
        for y in range(self.h):
            for x in range(self.w):
                m = self.mat[y][x]
                if m is None:
                    continue
                if self.rgb[y][x] is not None:
                    out[y][x] = self.rgb[y][x] + (255,)
                    continue
                t = self.tone[y][x]
                if t is None:
                    up, left = self.m(x, y - 1) != m, self.m(x - 1, y) != m
                    down, right = self.m(x, y + 1) != m, self.m(x + 1, y) != m
                    t = 3 if (up or left) and not (down or right) else 1 if (down or right) and not (up or left) else 2
                    if up and left:
                        t = 4 if m in SHINY else 3
                out[y][x] = self.ramps[m][t] + (255,)
        add = []
        for y in range(self.h):
            for x in range(self.w):
                if self.mat[y][x] is not None:
                    continue
                nb = [self.m(x + dx, y + dy) for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))]
                nb = [n for n in nb if n is not None]
                if nb:
                    pick = min(nb, key=lambda n: sum(self.ramps[n][0]))
                    add.append((x, y, self.ramps[pick][0] + (255,)))
        for x, y, c in add:
            out[y][x] = c
        return out


def mirror(img):
    return [list(reversed(row)) for row in img]


def encode(w, h, raw):
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")


def png(img):
    raw = bytearray()
    for row in img:
        raw.append(0)
        for px in row:
            raw += bytes(px) if px else b"\x00\x00\x00\x00"
    return encode(len(img[0]), len(img), raw)


def sheet(rows, path, scale=4, gap=4, bg=(0x4F, 0x8A, 0x3E)):
    """A preview: `rows` is a list of lists of images (any sizes), bottom-aligned in each row."""
    cw = max(sum(len(im[0]) + gap for im in r) + gap for r in rows)
    heights = [max(len(im) for im in r) for r in rows]
    ch = sum(h + gap for h in heights) + gap
    canvas = [[bg] * cw for _ in range(ch)]
    y0 = gap
    for r, rh in zip(rows, heights):
        x0 = gap
        for im in r:
            ih, iw = len(im), len(im[0])
            for y in range(ih):
                for x in range(iw):
                    px = im[y][x]
                    if px:
                        a = px[3] / 255
                        cy, cx = y0 + rh - ih + y, x0 + x
                        canvas[cy][cx] = tuple(round(px[i] * a + canvas[cy][cx][i] * (1 - a)) for i in range(3))
            x0 += iw + gap
        y0 += rh + gap
    raw = bytearray()
    for Y in range(ch * scale):
        raw.append(0)
        for X in range(cw * scale):
            raw += bytes(canvas[Y // scale][X // scale]) + b"\xff"
    with open(path, "wb") as f:
        f.write(encode(cw * scale, ch * scale, raw))
