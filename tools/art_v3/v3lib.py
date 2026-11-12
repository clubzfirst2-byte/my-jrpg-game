"""Shared drawing for the v3 art ("2x detail", docs/art-release-v3/STYLE.md).

Density 4: 4 art pixels (texels) per game pixel. A 16-px tile is 64x64, the hero 64x112.
Rules kept from the v1 guide (docs/art-direction/ART_STYLE_GUIDE.md): light from the top left,
selective outline (the darkest tone of the bordering material), fully opaque or fully transparent
pixels only, no dithering checkerboards, fixed ramps.
New in v3 (STYLE.md 3): 6-tone ramps for characters/objects (0 outline .. 5 highlight; tone 2 is the
new mid shadow between the v1 shadow and base), 7-tone ramps for the ground (v2 ramps.json),
1-texel outer outline with a tone-1 band inside on the shadow side.

Two ways to make a picture:
  * Canvas: draw parts (ellipses, polygons, lines) as materials, shade each part as a volume lit from
    the top left (shade_part), then outline();
  * remaster() (round 1 only, no longer used for pilot art: STYLE.md 5.2): the approved v1 frame is
    the UNDERDRAWING. It is moved to the 2x grid (edge-directed,
    so diagonals become finer steps), the outline is redrawn at half the thickness, the 6-tone ramp is
    re-applied (mid tones on every shadow edge, rim light on the lit silhouette), then details are hand
    stamped on the 2x grid (eyes, hair strands, seams) by the caller.
"""

import colorsys
import os

import numpy as np
from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


def hx(s):
    return (int(s[1:3], 16), int(s[3:5], 16), int(s[5:7], 16))


def to_hex(c):
    return "#%02x%02x%02x" % tuple(int(v) for v in c[:3])


def mix(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def shift(c, dh=0.0, ds=1.0, dv=1.0):
    h, s, v = colorsys.rgb_to_hsv(*(x / 255 for x in c))
    h = (h + dh / 360) % 1
    r, g, b = colorsys.hsv_to_rgb(h, min(1, s * ds), min(1, v * dv))
    return (round(r * 255), round(g * 255), round(b * 255))


def ramp6(r5):
    """A v1 5-tone ramp -> the v3 6-tone ramp: the new tone 2 sits between the v1 shadow and base,
    a little cooler (the shadow side leans blue, STYLE.md 3.2)."""
    c = [hx(x) if isinstance(x, str) else x for x in r5]
    mid = shift(mix(c[1], c[2], 0.5), dh=-4, ds=1.04)
    return [c[0], c[1], mid, c[2], c[3], c[4]]


def ramp(r):
    return [hx(x) if isinstance(x, str) else tuple(x) for x in r]


# ---------------------------------------------------------------- the canvas


class Canvas:
    """Per texel: material name (or None) and tone; `rgb` overrides a texel's colour (inks)."""

    def __init__(self, w, h, ramps):
        self.w, self.h = w, h
        self.ramps = {k: ramp(v) for k, v in ramps.items()}
        self.names = [None]
        self.mat = np.zeros((h, w), np.int16)  # 0 = empty
        self.tone = np.full((h, w), 3, np.int8)
        self.ink = {}  # (x, y) -> rgb
        self.part = np.zeros((h, w), np.int32)  # which part drew it (for shading)
        self._parts = 0

    def mid(self, name):
        if name not in self.names:
            self.names.append(name)
        return self.names.index(name)

    # --- masks
    def m_ellipse(self, cx, cy, rx, ry):
        yy, xx = np.mgrid[0:self.h, 0:self.w]
        return ((xx + 0.5 - cx) / rx) ** 2 + ((yy + 0.5 - cy) / ry) ** 2 <= 1

    def m_poly(self, pts):
        yy, xx = np.mgrid[0:self.h, 0:self.w]
        xs, ys = xx + 0.5, yy + 0.5
        inside = np.zeros((self.h, self.w), bool)
        n = len(pts)
        for i in range(n):
            (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
            if y0 == y1:
                continue
            cond = ((y0 <= ys) & (ys < y1)) | ((y1 <= ys) & (ys < y0))
            xint = x0 + (ys - y0) * (x1 - x0) / (y1 - y0)
            inside ^= cond & (xs < xint)
        return inside

    def m_rect(self, x0, y0, x1, y1):
        x0, y0, x1, y1 = (int(round(v)) for v in (x0, y0, x1, y1))
        m = np.zeros((self.h, self.w), bool)
        m[max(0, y0):max(0, y1 + 1), max(0, x0):max(0, x1 + 1)] = True
        return m

    def m_line(self, pts, width=1.0):
        yy, xx = np.mgrid[0:self.h, 0:self.w]
        px, py = xx + 0.5, yy + 0.5
        m = np.zeros((self.h, self.w), bool)
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            dx, dy = x1 - x0, y1 - y0
            L2 = dx * dx + dy * dy or 1e-9
            t = np.clip(((px - x0) * dx + (py - y0) * dy) / L2, 0, 1)
            d = np.hypot(px - (x0 + t * dx), py - (y0 + t * dy))
            m |= d <= width / 2
        return m

    # --- filling
    def fill(self, mask, mat, tone=3, over=True):
        k = self.mid(mat)
        self._parts += 1
        sel = mask if over else (mask & (self.mat == 0))
        self.mat[sel] = k
        self.tone[sel] = tone
        self.part[sel] = self._parts
        for xy in [xy for xy in self.ink if sel[xy[1], xy[0]]]:
            del self.ink[xy]
        return sel

    def put(self, x, y, mat, tone):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.mat[y, x] = self.mid(mat)
            self.tone[y, x] = tone
            self.ink.pop((x, y), None)

    def dot(self, x, y, rgb):
        """An ink texel (a fixed colour outside the ramps: eyes, glows)."""
        if 0 <= x < self.w and 0 <= y < self.h:
            self.mat[y, x] = self.mid("_ink")
            self.ink[(x, y)] = hx(rgb) if isinstance(rgb, str) else tuple(rgb)

    def set_tone(self, mask, tone):
        sel = mask & (self.mat != 0)
        self.tone[sel] = tone

    def stamp(self, rows, x0, y0, legend):
        """rows: strings, one char per texel; legend: char -> (mat, tone) or '#rrggbb' ink; '.' skips."""
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch in ". ":
                    continue
                v = legend[ch]
                x, y = x0 + i, y0 + j
                if not (0 <= x < self.w and 0 <= y < self.h):
                    continue
                if isinstance(v, str):
                    if self.mat[y, x] == 0:
                        self.mat[y, x] = self.mid("_ink")
                    self.ink[(x, y)] = hx(v)
                else:
                    self.put(x, y, v[0], v[1])

    # --- shading
    def shade_part(self, mask, tones=(1, 2, 3, 4, 5), light=(-0.55, -0.75, 0.55), dome=1.0, bias=0.0,
                   global_mask=None, gmix=0.0, rim=True, norm=False, cuts=None):
        """Shade the texels of `mask` as a dome lit from the top left; tones from dark to light.
        global_mask: a larger shape (e.g. the whole canopy) whose dome lighting is mixed in (gmix)."""
        mask = mask & (self.mat != 0)
        if not mask.any():
            return
        lam = dome_light(mask, light, dome)
        if global_mask is not None and gmix > 0:
            lam = lam * (1 - gmix) + dome_light(global_mask, light, dome) * gmix
        lam = lam + bias
        n = len(tones)
        if norm:  # spread the part's own range over all the tones (clean, even bands)
            v = lam[mask]
            lo, hi = float(np.percentile(v, 3)), float(np.percentile(v, 97))
            lam = (lam - lo) / max(1e-6, hi - lo) + bias
        if cuts is not None:  # explicit band edges (len(tones) - 1 ascending values in 0..1)
            idx = np.searchsorted(np.array(cuts), np.clip(lam, 0, 1))
        else:
            idx = np.clip((lam * n).astype(int), 0, n - 1)
        t = np.array(tones)[idx]
        self.tone[mask] = t[mask]

    def outline(self, skip=()):
        """Selective outline: every empty texel touching a drawn one gets the darkest tone (0) of the
        darkest touching material (4-neighbourhood)."""
        filled = self.mat != 0
        out = []
        for y in range(self.h):
            for x in range(self.w):
                if filled[y, x]:
                    continue
                best = None
                for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    X, Y = x + dx, y + dy
                    if 0 <= X < self.w and 0 <= Y < self.h and filled[Y, X]:
                        name = self.names[self.mat[Y, X]]
                        if name == "_ink" or name in skip:
                            continue
                        c = self.ramps[name][0]
                        if best is None or sum(c) < sum(self.ramps[best][0]):
                            best = name
                if best:
                    out.append((x, y, best))
        for x, y, name in out:
            self.mat[y, x] = self.mid(name)
            self.tone[y, x] = 0

    def shadow_band(self):
        """STYLE.md 3.3: on the shadow side (outline below or right of a texel), the texel inside the
        outline drops to tone 1 (a 2-texel dark edge that reads at 1 device px per texel)."""
        m, t = self.mat, self.tone
        H, W = m.shape
        ch = []
        for y in range(H):
            for x in range(W):
                if m[y, x] == 0 or t[y, x] <= 1 or self.names[m[y, x]] == "_ink":
                    continue
                for dx, dy in ((1, 0), (0, 1)):
                    X, Y = x + dx, y + dy
                    if X < W and Y < H and m[Y, X] != 0 and t[Y, X] == 0:
                        # only if that outline is an outer one (empty beyond it)
                        X2, Y2 = X + dx, Y + dy
                        if X2 >= W or Y2 >= H or m[Y2, X2] == 0:
                            ch.append((x, y))
                            break
        for x, y in ch:
            self.tone[y, x] = 1

    def rgba(self):
        img = np.zeros((self.h, self.w, 4), np.uint8)
        for k, name in enumerate(self.names):
            if k == 0 or name == "_ink":
                continue
            sel = self.mat == k
            if not sel.any():
                continue
            r = self.ramps[name]
            ts = np.clip(self.tone, 0, len(r) - 1)
            for ti, c in enumerate(r):
                s = sel & (ts == ti)
                img[s, :3] = c
                img[s, 3] = 255
        for (x, y), c in self.ink.items():
            img[y, x, :3] = c
            img[y, x, 3] = 255
        return img

    def image(self):
        return Image.fromarray(self.rgba(), "RGBA")


def erode(mask):
    m = mask.copy()
    m[1:, :] &= mask[:-1, :]
    m[:-1, :] &= mask[1:, :]
    m[:, 1:] &= mask[:, :-1]
    m[:, :-1] &= mask[:, 1:]
    m[0, :] = m[-1, :] = False
    m[:, 0] = m[:, -1] = False
    return m


def dist_in(mask, cap=64):
    d = np.zeros(mask.shape, np.float32)
    cur = mask.copy()
    for i in range(cap):
        if not cur.any():
            break
        d[cur] += 1
        cur = erode(cur)
    return d


def box_blur(a, r):
    if r <= 0:
        return a.astype(np.float32)
    a = np.pad(a.astype(np.float32), r, mode="edge")
    c = a.cumsum(0)
    c = np.vstack([np.zeros((1, c.shape[1]), np.float32), c])
    a = (c[2 * r + 1:] - c[:-2 * r - 1]) / (2 * r + 1)
    c = a.cumsum(1)
    c = np.hstack([np.zeros((c.shape[0], 1), np.float32), c])
    return (c[:, 2 * r + 1:] - c[:, :-2 * r - 1]) / (2 * r + 1)


def dome_light(mask, light=(-0.55, -0.75, 0.55), dome=1.0):
    """0..1 light of a dome filling `mask`: the height is the distance to the edge, the normal its slope."""
    d = dist_in(mask)
    mx = max(1.0, d.max())
    h = np.sqrt(np.clip(d / mx, 0, 1)) * mx * 0.9 * dome
    hb = box_blur(h, 1)
    gy, gx = np.gradient(hb)
    nx, ny, nz = -gx, -gy, np.ones_like(hb) * 1.0
    n = np.sqrt(nx * nx + ny * ny + nz * nz)
    lx, ly, lz = light
    ln = (lx * lx + ly * ly + lz * lz) ** 0.5
    lam = (nx * lx + ny * ly + nz * lz) / (n * ln)
    return np.clip(lam * 0.5 + 0.5, 0, 1) * mask


# ---------------------------------------------------------------- remaster (v1 frame as underdrawing)


def label_frame(img, ramps5, inks=()):
    """v1 RGBA frame -> (key array, table): key 0 empty; table[key] = (mat, tone5) or ('_ink', rgb)."""
    lut = {}
    for name, r in ramps5.items():
        for t, c in enumerate(r):
            lut.setdefault(hx(c) if isinstance(c, str) else tuple(c), (name, t))
    a = np.array(img.convert("RGBA"))
    H, W = a.shape[:2]
    table = [None]
    index = {}
    K = np.zeros((H, W), np.int32)
    for y in range(H):
        for x in range(W):
            if a[y, x, 3] < 128:
                continue
            c = tuple(int(v) for v in a[y, x, :3])
            lab = lut.get(c)
            if lab is None:
                lab = ("_ink", c)
            if lab not in index:
                index[lab] = len(table)
                table.append(lab)
            K[y, x] = index[lab]
    return K, table


def scale2x(K):
    """AdvMAME2x on labels: diagonals of the v1 drawing become 1-texel steps on the 2x grid."""
    H, W = K.shape
    P = np.pad(K, 1, mode="edge")
    E = K
    A = P[0:H, 1:W + 1]  # up
    B = P[1:H + 1, 2:W + 2]  # right
    C = P[1:H + 1, 0:W]  # left
    D = P[2:H + 2, 1:W + 1]  # down
    o = np.zeros((2 * H, 2 * W), K.dtype)
    e0 = np.where((C == A) & (C != D) & (A != B), A, E)
    e1 = np.where((A == B) & (A != C) & (B != D), B, E)
    e2 = np.where((D == C) & (D != B) & (C != A), C, E)
    e3 = np.where((B == D) & (B != A) & (D != C), D, E)
    o[0::2, 0::2], o[0::2, 1::2], o[1::2, 0::2], o[1::2, 1::2] = e0, e1, e2, e3
    return o


TONE5_TO_6 = [0, 1, 3, 4, 5]


def remaster(img, ramps5, protect_inks=True):
    """The v1 frame moved to the 2x grid and redrawn there (module docstring). Returns a Canvas."""
    K, table = label_frame(img, ramps5)
    K2 = scale2x(K)
    H, W = K2.shape
    c = Canvas(W, H, {k: ramp6(v) for k, v in ramps5.items()})
    for y in range(H):
        for x in range(W):
            k = K2[y, x]
            if k == 0:
                continue
            name, v = table[k]
            if name == "_ink":
                c.mat[y, x] = c.mid("_ink")
                c.ink[(x, y)] = v
            else:
                c.mat[y, x] = c.mid(name)
                c.tone[y, x] = TONE5_TO_6[v]
    thin_outline(c)
    mid_tones(c)
    return c


def _is(c, x, y, f):
    return 0 <= x < c.w and 0 <= y < c.h and f(x, y)


def thin_outline(c):
    """The v1 outline is 2 texels thick on the 2x grid; redraw it 1 texel thick (STYLE.md 3.3):
    on the top/left silhouette the inner texel joins the fill (a rim of light), on the bottom/right
    and on inner lines it becomes the fill's tone 1."""
    m, t = c.mat, c.tone
    ink = c.mid("_ink")
    empty = lambda x, y: m[y, x] == 0  # noqa: E731
    outl = lambda x, y: m[y, x] not in (0, ink) and t[y, x] == 0  # noqa: E731
    fillp = lambda x, y: m[y, x] not in (0,) and (m[y, x] == ink or t[y, x] > 0)  # noqa: E731
    changes = []
    for y in range(c.h):
        for x in range(c.w):
            if not outl(x, y):
                continue
            if any(_is(c, x + dx, y + dy, empty) or not (0 <= x + dx < c.w and 0 <= y + dy < c.h)
                   for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))):
                continue  # the outer texel stays tone 0
            for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0)):
                X, Y = x + dx, y + dy
                if not _is(c, X, Y, fillp) or m[Y, X] == ink:
                    continue
                bx, by = x - 2 * dx, y - 2 * dy
                beyond_empty = not (0 <= bx < c.w and 0 <= by < c.h) or m[by, bx] == 0
                if (dx, dy) in ((0, 1), (1, 0)):  # fill below/right: outline goes up/left
                    if beyond_empty:
                        nt = int(t[Y, X])
                        changes.append((x, y, m[Y, X], min(5, nt + 1) if nt >= 3 else nt))
                        break
                else:  # fill above/left: the shadow side of that fill
                    changes.append((x, y, m[Y, X], 1))
                    break
    for x, y, mm, tt in changes:
        m[y, x], t[y, x] = mm, tt


def mid_tones(c):
    """Where a material's base (3) meets its shadow (1), the base texel takes the new mid tone (2);
    where light (4) meets base on the lower side, nothing (keeps forms crisp)."""
    m, t = c.mat, c.tone
    ink = c.mid("_ink")
    ch = []
    for y in range(c.h):
        for x in range(c.w):
            if m[y, x] in (0, ink) or t[y, x] != 3:
                continue
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                X, Y = x + dx, y + dy
                if 0 <= X < c.w and 0 <= Y < c.h and m[Y, X] == m[y, x] and t[Y, X] == 1:
                    ch.append((x, y))
                    break
    for x, y in ch:
        t[y, x] = 2


# ---------------------------------------------------------------- io


def save(img, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if isinstance(img, Canvas):
        img = img.image()
    img.save(path, optimize=True)
    return path


def nearest(img, k):
    return img.resize((img.width * k, img.height * k), Image.NEAREST)


def colours(img):
    a = np.array(img.convert("RGBA")).reshape(-1, 4)
    a = a[a[:, 3] > 0]
    return len({tuple(p) for p in a[:, :3]})


def block_detail(img):
    """Share of opaque 2x2-aligned blocks that are NOT one flat colour (0 for a 2x upscale)."""
    a = np.array(img.convert("RGBA")).astype(np.int32)
    H, W = a.shape[0] // 2 * 2, a.shape[1] // 2 * 2
    a = a[:H, :W]
    key = (a[..., 0] << 24) | (a[..., 1] << 16) | (a[..., 2] << 8) | a[..., 3]
    b = key.reshape(H // 2, 2, W // 2, 2).transpose(0, 2, 1, 3).reshape(H // 2, W // 2, 4)
    alpha = a[..., 3].reshape(H // 2, 2, W // 2, 2).transpose(0, 2, 1, 3).reshape(H // 2, W // 2, 4)
    opaque = (alpha > 0).all(-1)
    flat = (b == b[..., :1]).all(-1)
    n = opaque.sum()
    return float((opaque & ~flat).sum() / n) if n else 0.0


def luma(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def lift_ramp(r, min_l=36.0):
    """Raise every tone darker than `min_l` (Rec.709 luma) to it, keeping the hue: outlines of
    background objects are the material's own dark colour, never near-black (STYLE.md 3.3)."""
    out = []
    for col in ramp(r):
        L = luma(col)
        if L < min_l:
            f = min_l / max(L, 1.0)
            col = tuple(min(255, round(v * f + 0.5)) for v in col)
            while luma(col) < min_l:
                col = tuple(min(255, v + 1) for v in col)
        out.append(col)
    return out


def despeckle(c, keep=(), loose=()):
    """Clean-up (STYLE.md 3.4): a texel unlike all its 4 neighbours, 3 or 4 of which are one other
    tone of the same material, takes that tone (no lone dots from band edges). Inks and materials in
    `keep` are left alone."""
    m, t = c.mat, c.tone
    ink = c.mid("_ink")
    keepk = {c.mid(k) for k in keep}
    loosek = {c.mid(k) for k in loose}  # materials where 2 agreeing neighbours are enough
    ch = []
    for y in range(1, c.h - 1):
        for x in range(1, c.w - 1):
            k = m[y, x]
            if k in (0, ink) or k in keepk:
                continue
            nb = [(m[y + dy, x + dx], t[y + dy, x + dx]) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            if (k, t[y, x]) in nb:
                continue
            for cand in set(nb):  # 3 or 4 neighbours agree on one tone of this material
                if cand[0] == k and nb.count(cand) >= (2 if k in loosek else 3):
                    ch.append((x, y, cand[1]))
                    break
    for x, y, v in ch:
        t[y, x] = v


def clean_isolated(img, passes=2):
    """Image-level clean-up (round 6 of the production checks): an opaque texel whose 4 neighbours
    are all opaque and all of other colours takes the most common colour among them (ties: the
    darker one, which keeps outlines closed). For thin props whose 1-texel steps read as specks."""
    a = np.array(img.convert("RGBA")).astype(np.int64)
    for _ in range(passes):
        op = a[..., 3] == 255
        key = (a[..., 0] << 16) | (a[..., 1] << 8) | a[..., 2]
        H, W = key.shape
        ch = []
        for y in range(1, H - 1):
            for x in range(1, W - 1):
                if not op[y, x]:
                    continue
                nb = [(y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)]
                if not all(op[q] for q in nb):
                    continue
                ks = [key[q] for q in nb]
                if key[y, x] in ks:
                    continue
                best = max(set(ks), key=lambda k: (ks.count(k), -luma(((k >> 16) & 255, (k >> 8) & 255, k & 255))))
                q = nb[ks.index(best)]
                ch.append((y, x, a[q].copy()))
        if not ch:
            break
        for y, x, v in ch:
            a[y, x] = v
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def edge_cuts(c):
    """The texels on the top row and the left / right columns that are not an outline (tone 0): a part
    cut by the frame's edge. Returns their count (0 = nothing cut)."""
    m = c.mat != 0
    shirt = c.mat == c.mid("shirt") if "shirt" in c.names else np.zeros_like(m)
    bad = 0
    for sel in (np.s_[0, :], np.s_[:, 0], np.s_[:, c.w - 1]):
        # hero round 3: the gauntlet's dark grey is the same colour as its outline: counted as a cut too
        bad += int((m[sel] & ((c.tone[sel] != 0) | shirt[sel])).sum())
    ink = sum(1 for (x, y) in c.ink if y == 0 or x in (0, c.w - 1))
    return bad + ink


def stray_pieces(c, limit=40, skip=("water",)):
    """Hero round 3: 4-connected pieces of drawn texels (outline included) apart from the largest one,
    of `limit` texels or fewer (a fragment of cloak, trim or leg left floating). Materials in `skip`
    (the swimmer's water ring) are not counted. Returns [(size, (x0, y0, x1, y1), names)]."""
    sk = {c.mid(n) for n in skip if n in c.names}
    m = (c.mat != 0) & ~np.isin(c.mat, list(sk) or [-1])
    lab = np.zeros(m.shape, np.int32)
    comps = []
    for y0, x0 in zip(*np.nonzero(m)):
        if lab[y0, x0]:
            continue
        k = len(comps) + 1
        st, pts = [(y0, x0)], []
        lab[y0, x0] = k
        while st:
            y, x = st.pop()
            pts.append((y, x))
            for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= yy < c.h and 0 <= xx < c.w and m[yy, xx] and not lab[yy, xx]:
                    lab[yy, xx] = k
                    st.append((yy, xx))
        comps.append(pts)
    if not comps:
        return []
    big = max(range(len(comps)), key=lambda i: len(comps[i]))
    out = []
    for i, pts in enumerate(comps):
        if i == big or len(pts) > limit:
            continue
        ys, xs = zip(*pts)
        names = sorted({c.names[c.mat[y, x]] for y, x in pts})
        out.append((len(pts), (min(xs), min(ys), max(xs), max(ys)), names))
    return out


def _pieces_of(m):
    lab = np.zeros(m.shape, np.int32)
    comps = []
    for y0, x0 in zip(*np.nonzero(m)):
        if lab[y0, x0]:
            continue
        k = len(comps) + 1
        st, pts = [(y0, x0)], []
        lab[y0, x0] = k
        while st:
            y, x = st.pop()
            pts.append((y, x))
            for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= yy < m.shape[0] and 0 <= xx < m.shape[1] and m[yy, xx] and not lab[yy, xx]:
                    lab[yy, xx] = k
                    st.append((yy, xx))
        comps.append(pts)
    return comps


def cloth_islands(c, cloth="cloak", trim=("gold",), limit=40):
    """Hero round 3: pieces of the cloak's green (with its gold trim) cut off from the rest of the
    cloak by what was drawn over it, of `limit` texels or fewer. [(size, (x0, y0, x1, y1))]."""
    if cloth not in c.names:
        return []
    k = c.mid(cloth)
    grp = np.isin(c.mat, [k] + [c.mid(t) for t in trim if t in c.names])
    comps = [p for p in _pieces_of(grp) if any(c.mat[y, x] == k for y, x in p)]
    if len(comps) < 2:
        return []
    big = max(comps, key=len)
    out = []
    for p in comps:
        if p is big or len(p) > limit:
            continue
        ys, xs = zip(*p)
        out.append((len(p), (min(xs), min(ys), max(xs), max(ys)), p))
    return out


def absorb_cloth_islands(c, **kw):
    """Each such piece takes, texel by texel, the most common other material around it (the leg or
    the tunic it sits on)."""
    k = c.mid(kw.get("cloth", "cloak"))
    trim = [c.mid(t) for t in kw.get("trim", ("gold",))]
    for _, _, pts in cloth_islands(c, **kw):
        todo = set(pts)
        for _ in range(12):
            if not todo:
                break
            for (y, x) in list(todo):
                nb = [(c.mat[yy, xx], c.tone[yy, xx]) for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1))
                      if 0 <= yy < c.h and 0 <= xx < c.w and (yy, xx) not in todo
                      and c.mat[yy, xx] not in [k] + trim and c.mat[yy, xx] != 0]
                if nb:
                    m, t = max(set(nb), key=nb.count)
                    c.mat[y, x], c.tone[y, x] = m, t
                    todo.discard((y, x))

