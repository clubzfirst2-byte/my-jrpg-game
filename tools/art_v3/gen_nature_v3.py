"""v3 pilot: trees, plants/props and grass ground at density 4 (STYLE.md 6, 7).

  terrain/obj.v3.oak.png         160 x 224  broadleaf, large (game 40 x 56: 2 x the hero's height)
  terrain/obj.v3.pine.png         96 x 176  pine, medium (game 24 x 44)
  terrain/prop.v3.tuft.png        32 x 24   grass tuft
  terrain/prop.v3.flowers.png     48 x 32   flower clump (pink / white / yellow)
  terrain/prop.v3.bush.png        64 x 48   bush with berries
  terrain/prop.v3.stump.png       48 x 40   mossy stump
  terrain/plains.grass.v3.<0..3>.png  64 x 64  summer plains ground, tiles seamlessly

Foliage is drawn as leaf CLUMPS: each clump a dome lit from the top left, mixed with the dome of the
whole crown (so the crown reads as one mass), with a scalloped edge and leaf marks on the lit side.
Everything is drawn fresh on the density-4 grid (new kinds; the v1 32 x 56 trees stay as saplings).
Run: python3 tools/art_v3/gen_nature_v3.py
"""

import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402

from v3lib import ROOT, Canvas, save  # noqa: E402

OUT = os.path.join(ROOT, "src", "art-release-v3", "terrain")

# ramps: 0 outline .. 6 highlight (ground and foliage use 7 tones, STYLE.md 3.2)
LEAF = ["#0e2216", "#183a24", "#22502c", "#2e6432", "#44783a", "#62944a", "#8cb664"]
PINE = ["#08161a", "#123028", "#173a36", "#1f4a3e", "#2a5a46", "#3a7052", "#5a8e66"]
BARK = ["#1e1008", "#3e2414", "#4e301c", "#5e3a22", "#6e502a", "#86603a", "#a07a50"]
MOSS = ["#0c1c16", "#1e3e24", "#2c5430", "#3e6a36", "#56843e", "#6e9a48", "#90b860"]
WOOD = ["#2a1a0c", "#5a3a1e", "#76502c", "#8e6838", "#a88048", "#c09a60", "#dcbc84"]
PLAINS = ["#16301c", "#2a5030", "#335d3a", "#3c6a38", "#4e773f", "#528446", "#6c9e58"]
PINK = ["#5a2038", "#b0507a", "#c8689e", "#e080a8", "#ea98af", "#f4b0cc", "#ffe0ee"]
WHITE = ["#4a4a5a", "#b4b4c4", "#cbcdd7", "#e2e2ea", "#ebebf1", "#f4f4f8", "#ffffff"]
YELLOW = ["#6a4a10", "#c08a20", "#d8bb30", "#f0c040", "#f4d360", "#f8dc80", "#fff4c0"]
BERRY = ["#3a0a14", "#7a1424", "#9a1c2c", "#c02a36", "#e04a4a", "#f07a6a", "#ffc0b0"]
STONE = ["#1c1a24", "#3a3846", "#474757", "#585668", "#6c677a", "#7a788c", "#9e9cb0"]
RAMPS = dict(leaf=LEAF, pine=PINE, bark=BARK, moss=MOSS, wood=WOOD, grass=PLAINS, pink=PINK, white=WHITE,
             yellow=YELLOW, berry=BERRY, stone=STONE)


# ------------------------------------------------------------------ helpers

def hsh(x, y, s=0):
    """A fixed scatter (not a grid, so no diagonal rows of marks)."""
    h = (x * 374761393 + y * 668265263 + s * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return h ^ (h >> 16)


def bark_texture(c, mask, rng, period=5):
    """Vertical bark plates: wandering grooves (tone 1) with a lit ridge (tone +1) left of each."""
    ys, xs = np.nonzero(mask)
    if not len(xs):
        return
    phase = {}
    for y, x in zip(ys, xs):
        w = math.sin(y * 0.21 + (x // period) * 1.7) * 1.2
        u = (x + w) % period
        t = int(c.tone[y, x])
        if u < 1.0:
            c.tone[y, x] = max(1, t - 2)
        elif u < 2.0 and t >= 3:
            c.tone[y, x] = min(6, t + 1)
    del phase


def foliage(c, mat, clumps, rng, crown_mask=None, gmix=0.5, tones=(1, 2, 3, 4, 5, 6), marks=True,
            scallop=2.2):
    """clumps: [(cx, cy, rx, ry)], drawn back (top) to front (bottom) so lower clumps overlap."""
    whole = np.zeros((c.h, c.w), bool)
    masks = []
    for cx, cy, rx, ry in clumps:
        m = c.m_ellipse(cx, cy, rx, ry)
        # scalloped rim: small bumps round the edge (leaf tips)
        n = max(6, int(2 * math.pi * max(rx, ry) / 5))
        for k in range(n):
            a = 2 * math.pi * k / n + rng.uniform(-0.15, 0.15)
            m |= c.m_ellipse(cx + math.cos(a) * rx * 0.92, cy + math.sin(a) * ry * 0.92, scallop, scallop)
        masks.append(m)
        whole |= m
    g = crown_mask if crown_mask is not None else whole
    order = sorted(range(len(clumps)), key=lambda i: clumps[i][1])
    for i in order:
        m = masks[i]
        c.fill(m, mat)
        c.shade_part(m, tones=tones, global_mask=g, gmix=gmix)
    # inner shade where a clump sits under the one above it (a dark crescent), then leaf marks
    if marks:
        k = c.mid(mat)
        for y in range(2, c.h - 2):
            for x in range(2, c.w - 2):
                if c.mat[y, x] != k:
                    continue
                if hsh(x, y) % 29 == 0:
                    t = int(c.tone[y, x])
                    lit = t >= 4
                    # a 3-texel leaf: a lit leaf on the lit side, a dark notch on the shade side
                    pts = [(0, 0), (1, 0), (1, -1)] if lit else [(0, 0), (-1, 0), (0, 1)]
                    for dx, dy in pts:
                        X, Y = x + dx, y + dy
                        if c.mat[Y, X] == k:
                            c.tone[Y, X] = min(6, t + 1) if lit else max(1, t - 1)
    return whole


# ------------------------------------------------------------------ trees

def oak():
    rng = random.Random(11)
    W, H = 160, 224
    c = Canvas(W, H, RAMPS)
    G = H - 3
    # trunk with root flare and two branches into the crown
    trunk = c.m_poly([(68, G), (62, G - 3), (70, G - 10), (71, 120), (66, 96), (76, 104), (80, 86),
                      (86, 104), (95, 94), (90, 120), (89, G - 10), (98, G - 3), (92, G)])
    roots = c.m_poly([(54, G), (64, G - 6), (72, G - 2)]) | c.m_poly([(88, G - 2), (96, G - 6), (106, G)])
    c.fill(trunk | roots, "bark")
    c.shade_part(trunk | roots, tones=(1, 2, 3, 4, 5), light=(-0.8, -0.3, 0.5))
    bark_texture(c, trunk, rng)
    # crown: clumps on a rounded crown shape
    clumps = []
    cx, cy = 80, 82
    for ring, (r, n, sz) in enumerate([(0, 1, 26), (30, 6, 22), (50, 10, 19)]):
        for k in range(n):
            a = 2 * math.pi * k / n + ring * 0.4 + rng.uniform(-0.12, 0.12)
            x = cx + math.cos(a) * r * 1.08
            y = cy + math.sin(a) * r * 0.86
            if y > 140:
                continue
            s = sz + rng.uniform(-3, 3)
            clumps.append((x, y, s, s * 0.82))
    crown = c.m_ellipse(cx, cy - 2, 70, 62)
    foliage(c, "leaf", clumps, rng, crown_mask=crown, gmix=0.55)
    # a few gaps into the crown's dark interior, and the trunk's shadow under the crown
    for gx, gy in ((62, 118), (100, 112)):  # gaps: a crescent of shade under a clump, not a hole
        m = (c.m_ellipse(gx, gy, 7, 3.5) & ~c.m_ellipse(gx - 1, gy - 2, 7, 3.5)) & (c.mat == c.mid("leaf"))
        c.set_tone(m, 1)
    under = (c.mat == c.mid("bark")) & c.m_rect(0, 118, W - 1, 134)
    c.set_tone(under, 1)
    c.outline()
    c.shadow_band()
    return c


def pine():
    rng = random.Random(5)
    W, H = 96, 176
    c = Canvas(W, H, RAMPS)
    G = H - 3
    trunk = c.m_poly([(42, G), (44, 130), (52, 130), (54, G)])
    c.fill(trunk | c.m_poly([(36, G), (44, G - 6), (48, G)]) | c.m_poly([(48, G), (52, G - 6), (60, G)]), "bark")
    c.shade_part(c.mat == c.mid("bark"), tones=(1, 2, 3, 4, 5), light=(-0.8, -0.3, 0.5))
    bark_texture(c, trunk, rng, period=4)
    tiers = [(14, 10), (34, 18), (56, 26), (80, 34), (106, 42), (132, 46)]  # (bottom y, half width)
    whole = c.m_poly([(48, 4), (95, 138), (1, 138)])
    top = 4
    for i, (yb, hw) in enumerate(tiers):
        yt = top if i == 0 else tiers[i - 1][0] - 8
        pts = [(48, yt)]
        # drooping needle tips along the bottom edge, right to left
        n = max(4, hw // 4)
        if i:
            pts.append((48 + hw * 0.55, yb - 10))
        for k in range(n + 1):
            x = 48 + hw - 2 * hw * k / n
            dip = 3 if k % 2 == 0 else -1
            sag = (1 - abs(x - 48) / hw) * 3
            pts.append((x, yb + dip + sag))
        if i:
            pts.append((48 - hw * 0.55, yb - 10))
        m = c.m_poly(pts)
        c.fill(m, "pine")
        c.shade_part(m, tones=(1, 2, 3, 4, 5, 6), global_mask=whole, gmix=0.45, light=(-0.7, -0.5, 0.5))
        # needle strokes: short diagonal dark lines down-right on the shade, lit on the left
        for y, x in zip(*np.nonzero(m)):
            if hsh(x, y, 2) % 13 == 0:
                for d in range(3):
                    X, Y = x + (d if x > 48 else -d), y + d
                    if 0 <= X < W and Y < H and m[Y, X]:
                        t = int(c.tone[Y, X])
                        c.tone[Y, X] = min(6, t + 1) if x < 48 else max(1, t - 1)
        # the tier above casts a band of shade on the top of this one
        if i:  # the tier above casts shade on the top of this one (under its drooping tips)
            prev = tiers[i - 1]
            for y, x in zip(*np.nonzero(m)):
                if y < prev[0] + 4 - abs(x - 48) * 0.05 and abs(x - 48) < prev[1] + 2:
                    c.tone[y, x] = max(1, int(c.tone[y, x]) - 2)
    c.outline()
    c.shadow_band()
    return c


# ------------------------------------------------------------------ props

def tuft():
    rng = random.Random(3)
    c = Canvas(32, 24, RAMPS)
    G = 22
    blades = [(-9, 12, -3), (-6, 17, -2), (-3, 20, -1), (0, 15, 1), (2, 21, 2), (5, 16, 3), (8, 11, 4), (-1, 9, 0)]
    for bx, h, lean in blades:
        x0 = 16 + bx
        pts = [(x0 - 1.5, G), (x0 + lean, G - h), (x0 + 1.5, G)]
        m = c.m_poly(pts)
        c.fill(m, "grass")
        for y, x in zip(*np.nonzero(m)):
            f = (G - y) / h
            c.tone[y, x] = 2 + int(f * 3.9) - (1 if x > x0 + lean * f else 0)
        tip_y = int(G - h)
        c.put(int(round(x0 + lean)), tip_y + 1, "grass", 6)
    c.outline()
    return c


def flowers():
    rng = random.Random(8)
    c = Canvas(48, 32, RAMPS)
    G = 30
    leaves = [(10, G - 4, 7, 3.5), (22, G - 3, 9, 4), (36, G - 4, 8, 3.5), (16, G - 8, 6, 3), (30, G - 9, 6, 3)]
    m = np.zeros((32, 48), bool)
    for x, y, rx, ry in leaves:
        m |= c.m_ellipse(x, y, rx, ry)
    c.fill(m, "grass")
    c.shade_part(m, tones=(1, 2, 3, 4, 5))
    for (fx, fy, col, s) in [(12, 14, "pink", 3.2), (24, 9, "white", 3.4), (35, 15, "yellow", 3.0),
                             (18, 20, "yellow", 2.6), (30, 21, "pink", 2.8), (40, 22, "white", 2.4)]:
        for y in range(int(fy + s), G - 2):  # stem
            c.put(int(fx), y, "grass", 2)
        for k in range(5):
            a = -math.pi / 2 + 2 * math.pi * k / 5
            p = c.m_ellipse(fx + math.cos(a) * s * 0.75, fy + math.sin(a) * s * 0.75, s * 0.55, s * 0.55)
            c.fill(p, col)
            c.shade_part(p, tones=(2, 3, 4, 5, 6))
        c.put(int(fx), int(fy), "yellow" if col != "yellow" else "wood", 4 if col != "yellow" else 2)
        c.put(int(fx) - 1, int(fy), "yellow" if col != "yellow" else "wood", 5 if col != "yellow" else 3)
    c.outline()
    c.shadow_band()
    return c


def bush():
    rng = random.Random(21)
    c = Canvas(64, 48, RAMPS)
    clumps = [(32, 22, 15, 12), (18, 30, 12, 10), (46, 30, 12, 10), (24, 36, 12, 8), (40, 37, 12, 8),
              (32, 33, 13, 10)]
    whole = c.m_ellipse(32, 30, 30, 17)
    foliage(c, "leaf", clumps, rng, crown_mask=whole, gmix=0.5, scallop=1.8)
    for bx, by in ((22, 26), (40, 22), (46, 34), (28, 38), (36, 30), (16, 34)):
        m = c.m_ellipse(bx, by, 1.8, 1.8)
        c.fill(m, "berry")
        c.shade_part(m, tones=(2, 3, 4, 5))
        c.put(bx - 1, by - 1, "berry", 6)
    c.outline()
    c.shadow_band()
    return c


def stump():
    rng = random.Random(4)
    c = Canvas(48, 40, RAMPS)
    G = 38
    side = c.m_poly([(8, 14), (40, 14), (41, G - 2), (46, G), (2, G), (7, G - 2)])
    c.fill(side, "bark")
    c.shade_part(side, tones=(1, 2, 3, 4, 5), light=(-0.9, -0.2, 0.4))
    bark_texture(c, side & c.m_rect(0, 16, 47, G - 3), rng, period=4)
    top = c.m_ellipse(24, 14, 16.5, 6.5)
    c.fill(top, "wood")
    for y, x in zip(*np.nonzero(top)):  # growth rings
        r = math.hypot((x + 0.5 - 23) / 16.5, (y + 0.5 - 14) / 6.5)
        t = 4 if int(r * 5) % 2 == 0 else 3
        if r > 0.86:
            t = 2
        if x < 20 and y < 13 and t >= 3:
            t += 1
        c.tone[y, x] = t
    c.put(23, 14, "wood", 1)
    c.put(24, 14, "wood", 1)
    # a crack and moss on the shaded side and the base
    for y in range(11, 19):
        c.put(30 + (y % 2), y, "wood", 1)
    moss = (c.m_ellipse(38, 26, 6, 9) | c.m_ellipse(10, G - 2, 9, 3) | c.m_ellipse(34, G - 2, 8, 3)) & side
    c.fill(moss, "moss")
    c.shade_part(moss, tones=(2, 3, 4, 5))
    c.outline()
    c.shadow_band()
    return c


# ------------------------------------------------------------------ ground

def periodic_noise(n, seed, octaves=((1, 1.0), (2, 0.5), (4, 0.25))):
    """Smooth noise that tiles every n texels (sum of sines with whole periods)."""
    rng = random.Random(seed)
    yy, xx = np.mgrid[0:n, 0:n] / n * 2 * math.pi
    v = np.zeros((n, n))
    for f, a in octaves:
        for _ in range(3):
            kx, ky = rng.randint(-f, f), rng.randint(-f, f)
            if kx == 0 and ky == 0:
                kx = f
            v += a * np.sin(kx * xx + ky * yy + rng.uniform(0, 6.28))
    v -= v.min()
    return v / v.max()


def grass_macro(n=256):
    """The summer plains ground as ONE 4 x 4-tile picture (256 x 256, tiles with itself), sliced into
    16 tiles plains.grass.v3.<row><col> placed by (ty % 4, tx % 4): the broad patches span 4 tiles,
    so the 16-px repeat of v1 is gone (STYLE.md 6.1)."""
    variant = 0
    c = Canvas(n, n, RAMPS)
    c.fill(np.ones((n, n), bool), "grass", 3)
    rng = random.Random(100 + variant)
    v = periodic_noise(n, 7, octaves=((1, 1.0), (2, 0.6), (3, 0.4), (6, 0.22), (12, 0.12)))
    # broad soft patches (base 3, darker 2, lighter 4) — calm, low value contrast (ground v2 rules)
    # ragged patch edges: the threshold moves by a fixed scatter per 2 x 2 texels (blades, not blobs)
    yy, xx = np.mgrid[0:n, 0:n]
    jit = np.vectorize(lambda x, y: (hsh(x // 2, y // 2, 9) % 1000) / 1000.0)(xx, yy) * 0.10 - 0.05
    v = v + jit
    c.tone[:] = np.where(v < 0.22, 2, np.where(v > 0.84, 4, 3))
    # blade tufts on a jittered grid (wraps round the tile edges)
    step = 7
    for gy in range(0, n, step):
        for gx in range(0, n, step):
            x = gx + rng.randint(0, step - 3)
            y = gy + rng.randint(0, step - 3)
            base = int(c.tone[y % n, x % n])
            kind = rng.random()
            if kind < 0.70:  # a tuft: 3 blades, the middle one tallest, lit tip on the left
                for bx, h in ((-1, 2), (0, 4), (1, 3)):
                    for d in range(h):
                        X, Y = (x + bx + (1 if d == h - 1 and bx else 0) * bx) % n, (y - d) % n
                        c.tone[Y, X] = min(5, base + 1) if d >= h - 2 else base
                c.tone[(y + 1) % n, x % n] = max(1, base - 1)  # its root shade
                c.tone[(y + 1) % n, (x + 1) % n] = max(1, base - 1)
                bright = rng.random() < 0.35
                c.tone[(y - 4) % n, x % n] = 6 if (bright and base >= 3) else min(5, base + 2)
                if rng.random() < 0.3:
                    c.tone[(y + 1) % n, x % n] = max(1, base - 2)
            elif kind < 0.85:  # a darker sprig
                for d in range(3):
                    c.tone[(y - d) % n, (x + d // 2) % n] = max(1, base - 1)
    if True:  # a few clover leaves and tiny white flowers
        for (x, y) in ((14, 20), (44, 46), (150, 76), (90, 200), (222, 140), (190, 30)):
            for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
                c.tone[(y + dy) % n, (x + dx) % n] = 4
            c.dot(x + 2, y, WHITE[5])
            c.dot(x + 3, y, WHITE[4])
            c.dot(x + 2, y + 1, YELLOW[3])
    return c


def main():
    items = {
        "obj.v3.oak.png": oak(), "obj.v3.pine.png": pine(), "prop.v3.tuft.png": tuft(),
        "prop.v3.flowers.png": flowers(), "prop.v3.bush.png": bush(), "prop.v3.stump.png": stump(),
    }
    out = [save(c, os.path.join(OUT, k)) for k, c in items.items()]
    big = grass_macro().image()
    for r in range(4):
        for col in range(4):
            out.append(save(big.crop((col * 64, r * 64, col * 64 + 64, r * 64 + 64)),
                            os.path.join(OUT, f"plains.grass.v3.{r}{col}.png")))
    print("\n".join(os.path.relpath(p, ROOT) for p in out))


if __name__ == "__main__":
    main()
