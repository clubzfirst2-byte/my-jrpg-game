"""A pixel canvas for ground v2: every pixel is (material, tone) with 7-tone ramps (ramps_v2.EXT), or None
(transparent). Wraps on both axes by default (ground tiles), so a mark drawn past an edge comes back on
the other side. Alpha is 0 or 255 only.
"""

from PIL import Image

from ramps_v2 import EXT


def _rgb(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


RGB = {k: [_rgb(c) for c in v] for k, v in EXT.items()}


class Canvas:
    def __init__(self, w=32, h=32, base=None, wrap=True):
        self.w, self.h, self.wrap = w, h, wrap
        self.px = [[base] * w for _ in range(h)]

    def _xy(self, x, y):
        if self.wrap:
            return x % self.w, y % self.h
        return (x, y) if 0 <= x < self.w and 0 <= y < self.h else None

    def get(self, x, y):
        p = self._xy(x, y)
        return self.px[p[1]][p[0]] if p else None

    def put(self, x, y, mat, tone):
        p = self._xy(x, y)
        if p:
            self.px[p[1]][p[0]] = (mat, max(0, min(6, tone)))

    def shift(self, x, y, d, lo=0, hi=6):
        v = self.get(x, y)
        if v:
            self.put(x, y, v[0], max(lo, min(hi, v[1] + d)))

    def stamp(self, x0, y0, rows, mat=None, keys=None, only=None):
        """rows: strings. With `mat`, digits 0-6 are tones of mat; `keys` maps other chars -> (mat, tone)
        or (None, d) for a relative shift by d. '.' or ' ' = leave. `only`: draw only over this material."""
        for dy, row in enumerate(rows):
            for dx, ch in enumerate(row):
                if ch in ". ":
                    continue
                x, y = x0 + dx, y0 + dy
                if only is not None:
                    cur = self.get(x, y)
                    if not cur or cur[0] != only:
                        continue
                if keys and ch in keys:
                    m, t = keys[ch]
                    if m is None:
                        self.shift(x, y, t)
                    else:
                        self.put(x, y, m, t)
                elif ch.isdigit() and mat:
                    self.put(x, y, mat, int(ch))

    def image(self):
        im = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        data = []
        for row in self.px:
            for v in row:
                data.append((0, 0, 0, 0) if v is None else RGB[v[0]][v[1]] + (255,))
        im.putdata(data)
        return im

    def copy(self):
        c = Canvas(self.w, self.h, None, self.wrap)
        c.px = [row[:] for row in self.px]
        return c

    def remap(self, mapping):
        """Palette shift (the season method): material -> other material, tone for tone."""
        for row in self.px:
            for i, v in enumerate(row):
                if v and v[0] in mapping:
                    row[i] = (mapping[v[0]], v[1])
        return self
