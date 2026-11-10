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


# ------------------------------------------------------------------ v2: 7-step ramps (round 2)
# The v1 ramps keep their 5 tones (0 outline, 1 shadow, 2 core, 3 light, 4 highlight); v2 adds ONE
# in-between step under the core and one over it (1.5, 2.5) -- the hero's style is a few clear
# tones in clusters, not a gradient. Per material: normal enemies use at most 6 tones (a shiny
# material drops 1.5), bosses at most 7. An in-between pixel is only kept inside a 2x2 block of
# itself (clusters >= 2 px wide, never a 1-px diagonal stair; see Rig.image).
# The outline is the material's own tone 0, as dark as the hero's (his cloak #10180e, trousers
# #14141c): only a tone 0 darker than max(r, g, b) 24 is lifted a quarter toward tone 1.
# Index: 0 outline, 1 tone 1, 2 = 1.5, 3 tone 2, 4 = 2.5, 5 tone 3, 6 tone 4.
def _mix(a, b, f):
    return tuple(int(math.floor(a[i] + (b[i] - a[i]) * f + 0.5)) for i in range(3))  # = JS Math.round


def _ramp7(c):
    o = c[0] if max(c[0]) >= 34 else _mix(c[0], c[1], 0.2)
    return [o, c[1], _mix(c[1], c[2], 0.5), c[2], _mix(c[2], c[3], 0.5), c[3], c[4]]


RGB8 = {k: _ramp7(v) for k, v in RGB.items()}
MID = (2, 4)  # the in-between indices


def idx8(tone, sub=0):
    """v1 tone (0..4, or a fixed in-between 1.5 / 2.5) + the in-between flag -> v2 ramp index (0..6)."""
    if tone <= 0:
        return 0
    if tone >= 4:
        return 6
    return min(5, int(math.floor(2 * (tone - 1) + 1 + sub + 0.5)))


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


# Hand-drawn clusters for fur and bark (v1.0 finish). Each map is a lock of fur drawn the way
# the hero's hair locks are: a lit stroke on its upper-left (L = one tone up) and a dark trailing
# tip on its lower-right (D = one tone down). They are stamped on a staggered grid anchored to the
# part (so they move with it and never flicker), only where the whole lock fits one pixel inside
# the part (the silhouette edge and the tone-0 outline stay clean).
LOCKS = {
    # hanging locks (angle ~90: hair hangs down), 3 variants
    "down": [
        ["L..", "LL.", ".LD", "..D", "..D"],
        [".L.", "LL.", "LD.", ".D.", ".DD"],
        ["L..", "LL.", "LLD", ".LD", "..D"],
    ],
    # long shaggy locks (the frost elk's coat)
    # long shaggy locks (the frost elk's coat): 3-4 px wide bundles, lit body, dark right side,
    # a dark tip pointing down (v1.0 finish 2: no thin 1-px strokes)
    "shag": [
        ["LL...", "LLL..", "LLLD.", ".LLD.", ".LDD.", "..D..", "..D.."],
        [".LL..", "LLLD.", "LLLD.", ".LLD.", "..DD.", "..D.."],
        ["LLL..", "LLLD.", ".LLD.", ".LLD.", "..DD.", "...D."],
    ],
    # locks flowing back (angle ~180: the beast faces right, its coat lies back to the left)
    "back": [
        ["...LL", ".LLD.", "LDD.."],
        ["..LL.", "LLDD.", "DD..."],
        ["...LL", "..LD.", "LDD.."],
    ],
}
LOCK_GRID = {"down": (4, 5, 2), "shag": (6, 7, 3), "back": (5, 3, 2)}  # step x, step y, row stagger


def _erode(m):
    e = m.copy()
    e[1:, :] &= m[:-1, :]
    e[:-1, :] &= m[1:, :]
    e[:, 1:] &= m[:, :-1]
    e[:, :-1] &= m[:, 1:]
    return e


def _clusters(tex, t, m, oy, ox, org=(0, 0)):
    """Re-tone the volume shading `t` (tones 1..4) inside mask `m` with hand-drawn clusters.
    tex = (kind, angle, seed[, options]): kind "fur" / "shag" (locks) or "bark" (plates).
    org = the frame coordinates of t[0, 0]."""
    kind, ang = tex[0], tex[1]
    seed = tex[2] if len(tex) > 2 else 0
    opt = tex[3] if len(tex) > 3 else {}
    h, w = t.shape
    out = t.copy()
    inner = _erode(m)
    if kind == "bark":
        return _plates(out, t, m, inner, oy, ox, ang, seed, opt, org)
    style = "shag" if kind == "shag" else ("down" if 45 <= ang % 180 <= 135 else "back")
    flip = style == "back" and (ang % 360) < 90  # a coat flowing to the right
    sx, sy, stag = LOCK_GRID[style]
    maps = LOCKS[style]
    for row in range(-(oy // sy) - 2, (h - oy) // sy + 2):
        for col in range(-(ox // sx) - 2, (w - ox) // sx + 2):
            hv = _hash(np.array([col]), np.array([row]), seed)[0]
            if hv < 0.12:  # a few gaps keep it from reading as a pattern
                continue
            lock = maps[int(hv * 997) % len(maps)]
            jx = int(hv * 7919) % 3 - 1
            jy = int(hv * 104729) % 3 - 1
            X0 = ox + col * sx + (row % 2) * stag + jx
            Y0 = oy + row * sy + jy
            cells = []
            ok = True
            for j, r_ in enumerate(lock):
                if flip:
                    r_ = r_[::-1]
                for i, ch in enumerate(r_):
                    if ch == ".":
                        continue
                    X, Y = X0 + i, Y0 + j
                    if not (0 <= X < w and 0 <= Y < h and inner[Y, X]):
                        ok = False
                        break
                    cells.append((X, Y, ch))
                if not ok:
                    break
            if not ok:
                continue
            for X, Y, ch in cells:
                b = t[Y, X]
                if ch == "L" and b <= 2:
                    out[Y, X] = b + 1
                elif ch == "D" and b >= 2:
                    out[Y, X] = b - 1
    return out


def _keep_runs(mask):
    """Drop pixels of `mask` that have no 8-neighbour in it (no lone dots: lines and edges only)."""
    p = np.pad(mask, 1)
    n = np.zeros(mask.shape, int)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy or dx:
                n += p[1 + dy:1 + dy + mask.shape[0], 1 + dx:1 + dx + mask.shape[1]]
    return mask & (n > 0)


def _connect4(mask):
    """Make diagonal steps of a 1-px line 4-connected (a pixel under each diagonal step), so the
    line reads as a line and never as a chain of lone dots."""
    m = mask.copy()
    dr = np.zeros_like(m)
    dr[:-1, :-1] = mask[:-1, :-1] & mask[1:, 1:] & ~mask[1:, :-1] & ~mask[:-1, 1:]
    m[1:, :-1] |= dr[:-1, :-1]
    dl = np.zeros_like(m)
    dl[:-1, 1:] = mask[:-1, 1:] & mask[1:, :-1] & ~mask[1:, 1:] & ~mask[:-1, :-1]
    m[1:, 1:] |= dl[:-1, 1:]
    return m


def _plates(out, t, m, inner, oy, ox, ang, seed, opt, org):
    """Bark (v1.0 finish 2): long plates (8 px along the root, ~3.6 px across) running along each
    root -- or out from a centre for the body (ang "radial") -- with a 1-px seam only between
    some plates (about every 2-3), tone 3 only on the top-left lip of a plate below / right of a
    seam, the rest of each plate a flat tone 2. Around opt["calm"] = (x, y, r) nothing is drawn
    and the face is a calm tone 2 (the core sits there)."""
    h, w = t.shape
    yy, xx = np.mgrid[0:h, 0:w]
    fy, fx = yy + org[0], xx + org[1]  # frame coordinates
    if ang == "radial":
        cx, cy = opt["centre"]
        dx, dy = fx - cx, fy - cy
        u = np.hypot(dx, dy)
        v = np.arctan2(dy, dx) * 16.0
    else:
        a = math.radians(ang)
        ly, lx = yy - oy, xx - ox
        u = lx * math.cos(a) + ly * math.sin(a)  # along the grain: plates are long
        v = -lx * math.sin(a) + ly * math.cos(a)
    WID, LEN = 3.6, 8.0
    row = np.floor(v / WID).astype(int)
    roff = _hash(row, np.zeros_like(row), seed + 11) * LEN
    seg = np.floor((u + roff) / LEN).astype(int)
    drawn = _hash(row, seg, seed + 5) < 0.42  # a seam only for some plates
    along = np.floor((v + 1.0) / WID).astype(int) != row
    across = np.floor((u + roff + 1.0) / LEN).astype(int) != seg
    calm = np.zeros((h, w), bool)
    if opt.get("calm"):
        x, y, r = opt["calm"]
        calm = np.hypot(fx - x, fy - y) <= r
    seam = (along | across) & drawn & inner & ~calm
    seam = _connect4(_keep_runs(seam)) & inner & ~calm
    out[seam] = np.maximum(t[seam] - 1, 1)
    lit = np.zeros_like(seam)
    lit[1:, :] |= seam[:-1, :]
    lit[:, 1:] |= seam[:, :-1]
    lit &= inner & ~seam & (t == 2) & ~calm
    lit = _connect4(_keep_runs(lit)) & inner & ~seam & (t == 2) & ~calm
    out[lit] = 3
    flat = calm & inner & (t == 3)
    out[flat] = 2
    return out


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
        self.boss = w >= 64  # a boss may use 7 tones per material, a normal enemy 6

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
            x, y = int(round(x)), int(round(y))  # v2: eased poses give fractional positions
            if 0 <= x + PAD < self.W and 0 <= y + PAD < self.H:
                m[y + PAD, x + PAD] = True
        return m

    # -------------------------------------------------------------- drawing
    darken = {}  # v2: material -> extra darkening for every volume-shaded part (a per-character tint)

    def add(self, mask, mat, **k):
        if mat in self.darken and k.get("tone") is None:
            k = dict(k, dark=k.get("dark", 0) + self.darken[mat])
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
        tone = np.full((H, W), -1.0)  # v2: a fixed tone may be a half step (2.5 = between 2 and 3)
        half = np.zeros((H, W), int)  # v2: the half step between two tones (volume shading only)
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
            t = np.full(B.shape, 2)
            t[I > 0.62] = 3
            t[I < 0.30] = 1
            # v2: the brighter part of the shadow band takes 1.5 and the brighter part of the core
            # band takes 2.5 (a normal enemy's shiny material keeps only 2.5: at most 6 tones)
            hf = np.zeros(t.shape, int)
            if not (p.mat in SHINY and not self.boss):
                hf[(t == 1) & (I > 0.20)] = 1
            hf[(t == 2) & (I > 0.48)] = 1
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
            if p.tex:  # fur locks / bark plates, hand-drawn clusters
                t = _clusters(p.tex, t, m, ys.min() - y0, xs.min() - x0, (y0 - PAD, x0 - PAD))
            t = np.clip(t - p.dark + p.lit, 1, 4)
            if p.mat not in SHINY:
                t = np.minimum(t, 3)
            hf[t > 2] = 0
            if p.mat in SHINY and not self.boss:
                hf[t == 1] = 0
            full = np.full((H, W), -1)
            full[y0:y1, x0:x1] = t
            tone[vis] = full[vis]
            fh = np.zeros((H, W), int)
            fh[y0:y1, x0:x1] = hf
            half[vis] = fh[vis]
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
                        half[y, x] = 0
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
                        half[y, x] = 0
                        break
        self.half = half
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
        # ramp index per pixel; an in-between tone survives only inside a 2x2 block of the same
        # material and index (clusters, not stairs or dither): else it drops to the tone below
        idx = np.zeros((H, W), int)
        code = np.full((H, W), -1)
        names = {m: i for i, m in enumerate(RGB8)}
        for Y, X in zip(*np.nonzero(filled)):
            idx[Y, X] = idx8(tone[Y, X], self.half[Y, X])
            code[Y, X] = names[mat[Y, X]] * 16 + idx[Y, X]
        mid = filled & np.isin(idx, MID)
        keep = np.zeros((H, W), bool)
        for dy in (0, 1):
            for dx in (0, 1):
                a = code[:H - 1, :W - 1]
                blk = mid[:H - 1, :W - 1] & mid[1:, :W - 1] & mid[:H - 1, 1:] & mid[1:, 1:] & \
                    (code[1:, :W - 1] == a) & (code[:H - 1, 1:] == a) & (code[1:, 1:] == a)
                keep[dy:H - 1 + dy, dx:W - 1 + dx] |= blk
        idx[mid & ~keep] -= 1
        for y in range(self.h):
            for x in range(self.w):
                Y, X = y + P, x + P
                if filled[Y, X]:
                    out[y][x] = RGB8[mat[Y, X]][idx[Y, X]] + (255,)
                elif outline:
                    best = None
                    for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                        yy, xx = Y + dy, X + dx
                        if filled[yy, xx]:
                            c = RGB8[mat[yy, xx]][0]
                            if best is None or sum(c) < sum(best):
                                best = c
                    if best is not None:
                        out[y][x] = best + (255,)
        return out


def mirror(img):
    return [list(reversed(r)) for r in img]


def same(a, b):
    return all(ra == rb for ra, rb in zip(a, b))
