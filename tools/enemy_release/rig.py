"""The drawing engine of the enemy & boss RELEASE art (tools/enemy_release).

The same rules as the hero and the villagers (ART_STYLE_GUIDE.md 1.1-1.3), made to hold up on
bodies up to 128x128:

  * every part is a MATERIAL with a 5-tone ramp (0 outline, 1 shadow, 2 core, 3 light, 4 highlight);
  * parts are SHAPES (ellipse, polygon, tapered limb, ...) posed per frame by each character's rig,
    plus HAND-PLACED PIXEL MAPS (`stamp`) for faces, eyes, cores, masks and other details, whose
    tones are fixed by hand;
  * shading: each shape is lit as a VOLUME from the top left -- the normal of the shape is taken
    from its softened mask, so a round body gets a lit top-left side, a core and a shaded
    bottom-right side, not only a 1-pixel rim; a part in front casts a 1-pixel shadow on what is
    behind it (down and right of its edge); far limbs are drawn one tone darker (`dark=1`);
  * the outline is selective: each outside pixel takes tone 0 of the material it touches;
  * alpha is 0 or 255 only, no anti-aliasing, no dithering.

Coordinates are pixels of the frame; shapes may reach outside it (they are clipped, but their
shading is computed as if they continued).
"""

import math

import numpy as np

PAD = 12  # shapes are rasterised on a padded canvas so clipping does not shade a false edge


def hx(s):
    return (int(s[1:3], 16), int(s[3:5], 16), int(s[5:7], 16))


# ------------------------------------------------------------------ palette
# 5 tones: outline, shadow, core, light, highlight. The murk / glow / eye ramps are the art style
# guide's (2.6); the others are the approved design's (docs/enemy/ENEMY_BOSS_DESIGN.md 1-3); the
# shared ones (bone, wood, leather) are BASE_RAMPS of tools/art_proto/pixel.py.
RAMPS = {
    "murk": ["#120a1a", "#2e1a3e", "#4a2a62", "#6e4490", "#9a70c0"],
    "glow": ["#2a0a2a", "#6a1e6a", "#b040b0", "#e070e0", "#ffc8ff"],
    "eye": ["#4a2a08", "#b06a10", "#ffd84a", "#fff2a8", "#fffbe0"],
    "ashfur": ["#1a1418", "#3a3036", "#5a4c50", "#7e6e6e", "#a69690"],
    "gobskin": ["#24201a", "#4e4636", "#7a6e54", "#a09474", "#c4ba98"],
    "plum": ["#1e1016", "#3e2430", "#5e3a46", "#80565e", "#a07a80"],
    "oldstone": ["#1e1e26", "#4e4e5a", "#9696a0", "#bcbcc6", "#e2e2ea"],
    "bronze": ["#24140c", "#5a3418", "#8a5628", "#b0783e", "#d4a064"],
    "rotwood": ["#1a120e", "#3a2a20", "#5e4636", "#846650", "#a88a70"],
    "fungus": ["#3a1a0a", "#8a4420", "#d07a3a", "#eaa868", "#f8d4a8"],
    "frostfur": ["#261e1a", "#55483e", "#8a7a6c", "#b0a294", "#dcd2c6"],
    "ice": ["#1a3040", "#3e6e88", "#7ab4cc", "#b8e4f0", "#f0fcff"],
    "murksand": ["#1c1018", "#3e2a3a", "#5e4458", "#82666e", "#a88c88"],
    "mask": ["#2e2a26", "#6e665c", "#a89e90", "#d2cabc", "#f2ece2"],
    "slate": ["#1c1a26", "#46445a", "#7a7896", "#a4a2bc", "#cccade"],
    "spark": ["#4a3a08", "#b08a10", "#ffe14a", "#fff59a", "#ffffff"],
    "lake": ["#081c34", "#143e66", "#22608e", "#3a84b2", "#6aaed2"],
    "ashring": ["#24201e", "#4e4844", "#7c7470", "#a8a09a", "#d6d0ca"],
    # shared materials (tools/art_proto/pixel.py BASE_RAMPS, the hero's own)
    "bone": ["#3a3226", "#9a8c70", "#d0c4a4", "#e8dec4", "#fff8e4"],
    "wood": ["#1e1008", "#4a2c16", "#6e4424", "#906038", "#b07e50"],
    "leather": ["#24160c", "#4a3020", "#704c30", "#946c46", "#b88c5e"],
}
RGB = {k: [hx(c) for c in v] for k, v in RAMPS.items()}
# materials that may carry tone 4 (a glint) in the volume shading; the others stop at tone 3
SHINY = {"glow", "eye", "ice", "spark", "bronze", "bone", "mask", "oldstone"}

LIGHT = np.array([-0.55, -0.68, 0.48])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


def _blur(a, r):
    """Three passes of a box blur of radius r (close to a gaussian)."""
    if r <= 0:
        return a.astype(float)
    out = a.astype(float)
    k = 2 * r + 1
    for _ in range(3):
        for axis in (0, 1):
            p = np.pad(out, [(r + 1, r) if i == axis else (0, 0) for i in range(2)], mode="edge")
            c = np.cumsum(p, axis=axis)
            if axis == 0:
                out = (c[k:, :] - c[:-k, :]) / k
            else:
                out = (c[:, k:] - c[:, :-k]) / k
    return out


def _hash(a, b, seed=0):
    h = (a.astype(np.int64) * 73856093) ^ (b.astype(np.int64) * 19349663) ^ (seed * 83492791)
    h = (h ^ (h >> 13)) * 1274126177
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


TEX = {  # kind -> (strand length, jitter of the light bands, share of dark strokes, share of lit strokes)
    "fur": (4, 0.30, 0.10, 0.05),
    "shag": (6, 0.36, 0.13, 0.06),
    "bark": (8, 0.26, 0.16, 0.04),
}


def _texture(tex, I, oy, ox):
    """Fur / bark: the light is broken along strands. tex = (kind, angle in degrees of the strands,
    seed). Strands are 1 px wide and L px long, anchored to the part (they move with it), so the
    band edges become tufts and the core gets a few hand-like hair / grain strokes."""
    kind, ang = tex[0], math.radians(tex[1])
    seed = tex[2] if len(tex) > 2 else 0
    L, amp, dark, lit = TEX[kind]
    h, w = I.shape
    yy, xx = np.mgrid[0:h, 0:w]
    yy, xx = yy - oy, xx - ox
    u = xx * math.cos(ang) + yy * math.sin(ang)  # along the strand
    v = np.round(-xx * math.sin(ang) + yy * math.cos(ang)).astype(int)  # across: one strand per px
    off = _hash(v, np.zeros_like(v), seed + 7) * L
    seg = np.floor((u + off) / L).astype(int)
    n = _hash(v, seg, seed)
    I = I + (n - 0.5) * amp
    return I, (n > 1 - dark, n < lit)


class Part:
    __slots__ = ("mask", "mat", "tone", "tones", "dark", "soft", "cast", "inline", "lit", "tex")

    def __init__(self, mask, mat, tone=None, tones=None, dark=0, soft=None, cast=True, inline=False, lit=0, tex=None):
        self.mask, self.mat, self.tone, self.tones = mask, mat, tone, tones
        self.dark, self.soft, self.cast, self.inline, self.lit = dark, soft, cast, inline, lit
        self.tex = tex


class Rig:
    """One frame. Draw parts back to front; `image()` returns rows of RGBA tuples (or None)."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.W, self.H = w + 2 * PAD, h + 2 * PAD
        yy, xx = np.mgrid[0:self.H, 0:self.W]
        self.X, self.Y = xx - PAD + 0.5, yy - PAD + 0.5  # pixel centres in frame coordinates
        self.parts = []

    # -------------------------------------------------------------- shapes (masks)
    def m_ellipse(self, cx, cy, rx, ry):
        return ((self.X - cx) / max(rx, 0.01)) ** 2 + ((self.Y - cy) / max(ry, 0.01)) ** 2 <= 1

    def m_rect(self, x0, y0, x1, y1):
        return (self.X >= x0) & (self.X < x1 + 1) & (self.Y >= y0) & (self.Y < y1 + 1)

    def m_poly(self, pts):
        X, Y = self.X, self.Y
        inside = np.zeros(X.shape, bool)
        n = len(pts)
        for i in range(n):
            (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
            if y0 == y1:
                continue
            cond = ((y0 <= Y) & (Y < y1)) | ((y1 <= Y) & (Y < y0))
            xs = x0 + (Y - y0) * (x1 - x0) / (y1 - y0)
            inside ^= cond & (X < xs)
        return inside

    def m_limb(self, x0, y0, x1, y1, r0, r1=None):
        """A capsule from (x0,y0) radius r0 to (x1,y1) radius r1 (tapered)."""
        r1 = r0 if r1 is None else r1
        dx, dy = x1 - x0, y1 - y0
        L = dx * dx + dy * dy or 1e-6
        t = np.clip(((self.X - x0) * dx + (self.Y - y0) * dy) / L, 0, 1)
        d = np.hypot(self.X - x0 - t * dx, self.Y - y0 - t * dy)
        return d <= r0 + (r1 - r0) * t

    def m_chain(self, pts, radii):
        """A tapered polyline: pts [(x,y)...], radii one per point."""
        m = np.zeros(self.X.shape, bool)
        for i in range(len(pts) - 1):
            m |= self.m_limb(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], radii[i], radii[i + 1])
        return m

    def m_line(self, x0, y0, x1, y1):
        m = np.zeros(self.X.shape, bool)
        n = max(abs(round(x1) - round(x0)), abs(round(y1) - round(y0)), 1)
        for i in range(n + 1):
            x = round(x0 + (x1 - x0) * i / n) + PAD
            y = round(y0 + (y1 - y0) * i / n) + PAD
            if 0 <= x < self.W and 0 <= y < self.H:
                m[y, x] = True
        return m

    def m_px(self, pts):
        m = np.zeros(self.X.shape, bool)
        for x, y in pts:
            if 0 <= x + PAD < self.W and 0 <= y + PAD < self.H:
                m[y + PAD, x + PAD] = True
        return m

    # -------------------------------------------------------------- drawing
    def add(self, mask, mat, **k):
        if mask.any():
            self.parts.append(Part(mask, mat, **k))
        return mask

    def ellipse(self, cx, cy, rx, ry, mat, **k):
        return self.add(self.m_ellipse(cx, cy, rx, ry), mat, **k)

    def rect(self, x0, y0, x1, y1, mat, **k):
        return self.add(self.m_rect(x0, y0, x1, y1), mat, **k)

    def poly(self, pts, mat, **k):
        return self.add(self.m_poly(pts), mat, **k)

    def limb(self, x0, y0, x1, y1, r0, r1, mat, **k):
        return self.add(self.m_limb(x0, y0, x1, y1, r0, r1), mat, **k)

    def chain(self, pts, radii, mat, **k):
        return self.add(self.m_chain(pts, radii), mat, **k)

    def line(self, x0, y0, x1, y1, mat, tone=2, **k):
        return self.add(self.m_line(x0, y0, x1, y1), mat, tone=tone, cast=False, **k)

    def px(self, pts, mat, tone, **k):
        return self.add(self.m_px(pts), mat, tone=tone, cast=False, **k)

    def mask_of(self, *masks):
        m = np.zeros(self.X.shape, bool)
        for a in masks:
            m |= a
        return m

    def shade(self, mask, tone_map):
        """Re-tone what is already drawn where `mask` is: tone_map(old_tone) -> new tone.
        Implemented as a part over it that copies the material underneath (adds no pixels)."""
        self.parts.append(Part(mask, None, tones=tone_map, cast=False))

    def stamp(self, x, y, rows, legend, flip=False, cast=False):
        """A hand-placed pixel map. rows: strings; legend: char -> (material, tone); '.' / ' ' = none.
        (x, y) is the top-left of the map in the frame; flip mirrors the map left-right."""
        if isinstance(rows, str):
            rows = [r for r in rows.strip("\n").split("\n")]
        groups = {}
        for j, row in enumerate(rows):
            if flip:
                row = row[::-1]
            for i, ch in enumerate(row):
                if ch in ". " or ch not in legend:
                    continue
                groups.setdefault(legend[ch], []).append((x + i, y + j))
        for (mat, tone), pts in groups.items():
            self.add(self.m_px(pts), mat, tone=tone, cast=cast)

    # -------------------------------------------------------------- rendering
    def _tones(self):
        H, W = self.H, self.W
        top = np.full((H, W), -1)
        for i, p in enumerate(self.parts):
            if p.mat is not None:
                top[p.mask] = i
        # keep a 1-px margin inside the frame so the outline always fits (a shape reaching the
        # edge is cut there and outlined; its shading still sees the whole shape)
        inner = np.zeros((H, W), bool)
        inner[PAD + 1:PAD + self.h - 1, PAD + 1:PAD + self.w - 1] = True
        self.lost = int(((top >= 0) & ~inner & (np.abs(self.X - self.w / 2) < self.w / 2 + 3) & (np.abs(self.Y - self.h / 2) < self.h / 2 + 3)).sum())
        out_ = (top >= 0) & ~inner
        ys, xs = np.nonzero(out_)
        self.lost_sides = sorted({("top" if y <= PAD else "bottom" if y >= PAD + self.h - 1 else "") + ("left" if x <= PAD else "right" if x >= PAD + self.w - 1 else "") for y, x in zip(ys, xs)})
        top[~inner] = -1
        mat = np.full((H, W), None, dtype=object)
        tone = np.full((H, W), -1)
        for i, p in enumerate(self.parts):
            vis = top == i
            if not vis.any():
                continue
            if p.mat is None:  # a re-tone over what is below
                continue
            mat[vis] = p.mat
            if p.tone is not None:
                tone[vis] = p.tone
                continue
            ys, xs = np.nonzero(p.mask)
            area = len(ys)
            s = p.soft if p.soft is not None else int(min(4, max(1, round(math.sqrt(area) / 7))))
            y0, y1 = max(ys.min() - 3 * s - 2, 0), min(ys.max() + 3 * s + 3, H)
            x0, x1 = max(xs.min() - 3 * s - 2, 0), min(xs.max() + 3 * s + 3, W)
            sub = p.mask[y0:y1, x0:x1]
            B = _blur(sub, s)
            gy, gx = np.gradient(B)
            S = 2.2 * (s + 0.6)
            nx, ny, nz = -gx * S, -gy * S, np.ones_like(B)
            nn = np.sqrt(nx * nx + ny * ny + nz * nz)
            I = (nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]) / nn
            strands = None
            if p.tex:
                I, strands = _texture(p.tex, I, ys.min() - y0, xs.min() - x0)
            t = np.full(B.shape, 2)
            t[I > 0.62] = 3
            t[I < 0.30] = 1
            if p.mat in SHINY:
                t[I > 0.86] = 4
            # the 1-pixel rim: an outside edge facing up or left is lit, down or right is shaded
            m = sub
            up = ~np.pad(m, ((1, 0), (0, 0)))[:-1, :]
            left = ~np.pad(m, ((0, 0), (1, 0)))[:, :-1]
            down = ~np.pad(m, ((0, 1), (0, 0)))[1:, :]
            right = ~np.pad(m, ((0, 0), (0, 1)))[:, 1:]
            t[m & (down | right) & ~(up | left)] = 1
            t[m & (up | left) & ~(down | right) & (t < 3)] = 3
            if strands is not None:  # hand-like strokes: dark hairs / grain in the core, a few lit ones
                dk, lt = strands
                t[dk & (t == 2) & m] = 1
                t[lt & (t == 2) & m] = 3
            t = np.clip(t - p.dark + p.lit, 1, 4)
            if p.mat not in SHINY:
                t = np.minimum(t, 3)
            full = np.full((H, W), -1)
            full[y0:y1, x0:x1] = t
            tone[vis] = full[vis]
        # re-tones
        for i, p in enumerate(self.parts):
            if p.mat is None:
                for y, x in zip(*np.nonzero(p.mask & (tone >= 0))):
                    tone[y, x] = p.tones(tone[y, x])
        # cast shadows: a part in front darkens what is just below / right of its edge
        idx = top
        for y in range(1, H):
            for x in range(1, W):
                a = idx[y, x]
                if a < 0 or self.parts[a].tone is not None or tone[y, x] <= 1:
                    continue
                for dx, dy in ((0, 1), (1, 1)):
                    b = idx[y - dy, x - dx]
                    if b > a and self.parts[b].cast and self.parts[b].mat is not None:
                        tone[y, x] = max(1, min(tone[y, x], 2) - 1) if tone[y, x] <= 2 else 2
                        break
        # inline: parts drawn with inline=True get tone 0 where they border a part behind them
        for i, p in enumerate(self.parts):
            if not p.inline:
                continue
            vis = idx == i
            for y, x in zip(*np.nonzero(vis)):
                for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < H and 0 <= xx < W and 0 <= idx[yy, xx] < i and self.parts[idx[yy, xx]].mat is not None:
                        if p.inline == "br" and (dx, dy) in ((-1, 0), (0, -1)):
                            continue
                        tone[y, x] = 0
                        break
        return mat, tone

    def clipped(self):
        """Which frame edges a drawn (non-outline) pixel touches: a sign the shape was cut off."""
        self._tones()
        return self.lost, self.lost_sides

    def image(self, outline=True):
        mat, tone = self._tones()
        H, W, P = self.H, self.W, PAD
        out = [[None] * self.w for _ in range(self.h)]
        filled = tone >= 0
        for y in range(self.h):
            for x in range(self.w):
                Y, X = y + P, x + P
                if filled[Y, X]:
                    out[y][x] = RGB[mat[Y, X]][tone[Y, X]] + (255,)
                elif outline:
                    best = None
                    for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                        yy, xx = Y + dy, X + dx
                        if filled[yy, xx]:
                            c = RGB[mat[yy, xx]][0]
                            if best is None or sum(c) < sum(best):
                                best = c
                    if best is not None:
                        out[y][x] = best + (255,)
        return out


def mirror(img):
    return [list(reversed(r)) for r in img]


def same(a, b):
    return all(ra == rb for ra, rb in zip(a, b))
