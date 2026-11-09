"""A small pixel canvas for terrain (地形) release art — the same method as the hero (tools/art_proto/pixel.py):

  * every pixel is a MATERIAL with a 5-tone ramp: 0 outline / 1 shadow / 2 core / 3 light / 4 highlight;
  * light comes from the top left;
  * details are HAND-DRAWN STAMPS (small pixel maps written as text) put at hand-chosen places —
    no noise, no random blobs.

Ground tiles WRAP: anything drawn past an edge comes back on the other side, so every tile repeats with
no seam (checked by the 4x4 repeat images). Faces wrap only left/right.
"""

from PIL import Image


def hx(s):
    return (int(s[1:3], 16), int(s[3:5], 16), int(s[5:7], 16))


class Tile:
    def __init__(self, w, h, ramps, base=None, wrap_x=True, wrap_y=True):
        """`ramps`: {material: [5 hex colours]}. `base`: (material, tone) to fill with, or None (transparent)."""
        self.w, self.h = w, h
        self.ramps = {k: [hx(c) for c in v] for k, v in ramps.items()}
        self.wrap_x, self.wrap_y = wrap_x, wrap_y
        self.px = [[base] * w for _ in range(h)]
        self.alpha = {}  # (x, y) -> alpha for soft shadows only

    def _xy(self, x, y):
        if self.wrap_x:
            x %= self.w
        if self.wrap_y:
            y %= self.h
        return (x, y) if 0 <= x < self.w and 0 <= y < self.h else None

    def put(self, x, y, mat, tone):
        p = self._xy(x, y)
        if p:
            self.px[p[1]][p[0]] = (mat, tone)

    def get(self, x, y):
        p = self._xy(x, y)
        return self.px[p[1]][p[0]] if p else None

    def tone_of(self, x, y):
        v = self.get(x, y)
        return v[1] if v else None

    def shift(self, x, y, d, lo=0, hi=4):
        """Darken (d<0) or lighten (d>0) what is there, keeping the material."""
        v = self.get(x, y)
        if v:
            self.put(x, y, v[0], max(lo, min(hi, v[1] + d)))

    def stamp(self, x0, y0, pattern, mats, only_on=None):
        """`pattern`: list of strings. Each char is a key of `mats` -> (material, tone); '.' = leave.
        `only_on`: draw only where the current material is this one (keeps details off paths etc.)."""
        for dy, row in enumerate(pattern):
            for dx, ch in enumerate(row):
                if ch == "." or ch == " ":
                    continue
                if only_on is not None:
                    cur = self.get(x0 + dx, y0 + dy)
                    if not cur or cur[0] != only_on:
                        continue
                m, t = mats[ch]
                if t is None:  # relative: darken/lighten what is there
                    self.shift(x0 + dx, y0 + dy, m)
                else:
                    self.put(x0 + dx, y0 + dy, m, t)

    def hline(self, x0, x1, y, mat, tone):
        for x in range(x0, x1 + 1):
            self.put(x, y, mat, tone)

    def image(self):
        im = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        for y in range(self.h):
            for x in range(self.w):
                v = self.px[y][x]
                if v is None:
                    continue
                a = self.alpha.get((x, y), 255)
                im.putpixel((x, y), self.ramps[v[0]][v[1]] + (a,))
        return im


def tone_stamp(pattern, mat):
    """Shorthand: a stamp whose digits are tones of one material."""
    return pattern, {str(t): (mat, t) for t in range(5)}
