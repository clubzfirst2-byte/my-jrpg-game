"""v3 production order 4: the village — houses and village props at density 4, 3 seasons (STYLE.md 7.3).

Replacements of the keys the game already draws (same names, same frame counts, the art exactly 2x the
current art, so the game size and the feet (bottom centre, the anchor) stay where they are):
  obj.house            192x224   half-timbered house (red tiles, plaster, teal shutters, arched door)
  obj.chest.closed/.open 64x56   obj.barrel 48x56   obj.crate 64x64   obj.jar 40x48
  obj.campfire.0/.1    64x56     obj.brazier.0/.1 48x64
  obj.checkpoint.off/.on 48x80   sw.plate.off/.on 56x40
New kinds (".v3.", placed by the map generation):
  obj.v3.fence.h / .l / .r 64x48 (a post in the tile's centre; rails to both / the right / the left
  edge, so runs join tile to tile), obj.v3.fence.post 16x48, obj.v3.well 128x128,
  obj.v3.signpost 48x80, and the seasons of the pilot's obj.v3.house_stone (256x288; its summer file
  is the pilot's and is not rewritten here).
Seasons: <s.> = "" (summer, also spring) | "autumn." | "winter.". Autumn files only where autumn looks
different (the flower boxes of the two houses); every other key falls back to the summer file. Winter:
snow on roofs (a blanket with a rounded front edge, icicles under the eaves) and on every top surface
2 texels wide or more (never a 1-texel cap); no flowers in the boxes; fires keep burning (no snow on
the flames or the hot stones).
Night windows (the fx v2 rule, src/view/houseWindows.js on gfx/fx-v2): only the GLASS lights up. Every
glass texel of the two houses is blue-black glass by `glass_kind` (the same test as houseWindows.js
glassKind); the glints (tones 4-5), frames, mullions and flower boxes are not. The window rectangles
(game px from the feet) are written to docs/art-release-v3/village_windows.json.
No ground shadows and no grass are baked in (STYLE.md 7.3, 8). Ramps lifted to luma >= 36 (3.3).
Run: python3 tools/art_v3/gen_village_v3.py [summer|autumn|winter|all]
"""

import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402

import gen_house_v3 as HS  # noqa: E402  (the pilot stone house: read-only use of its drawing steps)
from gen_flora_v3 import SNOW  # noqa: E402
from gen_nature_v3 import MOSS, hsh  # noqa: E402
from v3lib import ROOT, Canvas, clean_isolated, despeckle, lift_ramp, save  # noqa: E402

OUT = os.path.join(ROOT, "src", "art-release-v3", "objects")
DOC = os.path.join(ROOT, "docs", "art-release-v3", "village_windows.json")
PREFIX = {"summer": "", "autumn": "autumn.", "winter": "winter."}

R = lambda *a: lift_ramp(list(a))  # noqa: E731
BASE = dict(HS.RAMPS)  # roof stone plaster timber plank glass iron gold leaf pink yellow (pilot, lifted)
# night windows: the glass base (tone 3) a touch darker than the pilot's #4e7898 (glassKind luma 111,
# just over its 110 limit, so the upper half of each pane stayed dark at night); now luma 107
BASE["glass"] = BASE["glass"][:3] + [(0x4a, 0x74, 0x94)] + BASE["glass"][4:]
BASE.update(
    chestwood=R("#3a1a0c", "#6a3418", "#82421e", "#9a5426", "#b46c34", "#d08c4c"),
    # a green-leaning teal (green above blue): the shutters are never taken for glass at night
    teal=R("#0e3028", "#1e5e50", "#287464", "#348a78", "#4aa690", "#7ccab4"),
    clay=R("#3e1a10", "#8a3e22", "#a04c2a", "#ba6034", "#d07a48", "#e8a070"),
    glaze=R("#10302e", "#2a6a62", "#348076", "#42988a", "#5cb4a2", "#9adcc8"),
    ash=R("#2a2626", "#4e4846", "#625a56", "#77706a", "#948c84", "#b8b0a6"),
    fire=R("#7a1a08", "#c03a10", "#d85a14", "#f08a20", "#ffc040", "#fff0a0"),
    ruin=R("#22282c", "#46525a", "#56626a", "#6a767c", "#86929a", "#a8b4ba"),
    glow=R("#0e3a3a", "#1a6a66", "#22867e", "#30a89a", "#5cd6c0", "#c0fff0"),
    gem=R("#0e1e4a", "#1e3e8a", "#2850a8", "#3a6ccc", "#68a0f0", "#c8e4ff"),
    rope=R("#3a2a14", "#7a5e32", "#8e6e3c", "#a48248", "#bc9a5c", "#d8bc84"),
    water=R("#0e1a24", "#16303e", "#1e3e4e", "#2a5262", "#3e6e80", "#7aa4b4"),
    moss=MOSS[:6],
    snow=SNOW,
)
AUTUMN = dict(  # the flower boxes in autumn: marigolds and asters, browning leaves
    pink=R("#5a1e10", "#a8401c", "#c45424", "#dc6c2c", "#ec8a40", "#f8b070"),
    yellow=R("#6a3e10", "#b47418", "#d09020", "#e8aa30", "#f4c450", "#fadc88"),
    leaf=R("#2a2a14", "#4a4620", "#5c5628", "#706630", "#867a3a", "#a09448"),
)


def ramps_for(season):
    r = dict(BASE)
    if season == "autumn":
        r.update(AUTUMN)
    return r


def canvas(w, h, season):
    return Canvas(w, h, ramps_for(season))


def glass_kind(r, g, b, a=255):
    """houseWindows.js glassKind (gfx/fx-v2): 0 not glass, 1 glass, 2 the darkest glass."""
    if a < 128 or b < r + 20 or b < g:
        return 0
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    return 2 if lum < 40 else (1 if lum < 110 else 0)


# ------------------------------------------------------------------ shared helpers


def bevel(c, mask, lit=1, dark=-1, hi=5):
    """A part's own edges: top/left rows lit, bottom/right rows dark (the light from the top left)."""
    for y, x in zip(*np.nonzero(mask)):
        t = int(c.tone[y, x])
        down = y == c.h - 1 or not mask[y + 1, x]
        right = x == c.w - 1 or not mask[y, x + 1]
        up = y == 0 or not mask[y - 1, x]
        left = x == 0 or not mask[y, x - 1]
        if down or right:
            c.tone[y, x] = max(1, t + dark)
        elif up or left:
            c.tone[y, x] = min(hi, t + lit)


def grain(c, mask, vertical=True, seed=0):
    """Wood grain: long thin darker streaks along the board, a lit streak beside some."""
    for y, x in zip(*np.nonzero(mask)):
        a, b = (x, y) if vertical else (y, x)
        u = (a * 3 + int(2 * math.sin(b * 0.17 + a))) % 7
        t = int(c.tone[y, x])
        if u == 0:
            c.tone[y, x] = max(1, t - 1)
        elif u == 3 and hsh(a, b // 9, seed) % 3 == 0:
            c.tone[y, x] = min(5, t + 1)


def cyl(c, mask, x0, x1, tones=(4, 4, 3, 3, 3, 3, 2, 1)):
    """A vertical cylinder lit from the left: tone by the column's place across [x0, x1]."""
    for y, x in zip(*np.nonzero(mask)):
        f = (x - x0) / max(1, x1 - x0)
        c.tone[y, x] = tones[min(len(tones) - 1, max(0, int(f * len(tones))))]


def darken_right(c, mask, x_from, by=1, lo=1):
    for y, x in zip(*np.nonzero(mask & (c.mat != 0))):
        if x >= x_from and c.tone[y, x] > lo:
            c.tone[y, x] = max(lo, int(c.tone[y, x]) - by)


def snow_on(c, mats, seed=0, depth=(2, 3), mound=1, min_w=3, region=None):
    """Snow on every top surface of `mats` (a texel with nothing above it) at least `min_w` texels wide:
    the top `depth` rows turn to snow and a low mound (narrowing 2 texels a row) rises above where the
    canvas is empty. The lit side (left) is one tone brighter; the material under the snow gets its
    shadow tone. No cap is thinner than 2 texels (STYLE.md 7.1b)."""
    ks = {c.mid(m) for m in mats}
    rng = random.Random(seed)
    H, W = c.h, c.w
    tops = {}
    for x in range(W):
        for y in range(H):
            if c.mat[y, x] != 0:
                if c.mat[y, x] in ks and (region is None or region[y, x]):
                    tops[x] = y
                break
    xs = sorted(tops)
    runs, cur = [], []
    for x in xs:
        if cur and (x != cur[-1] + 1 or abs(tops[x] - tops[cur[-1]]) > 2):
            runs.append(cur)
            cur = []
        cur.append(x)
    if cur:
        runs.append(cur)
    k = c.mid("snow")
    for run in runs:
        if len(run) < min_w:
            continue
        d = rng.randint(max(2, depth[0]), max(2, depth[1]))
        x0, x1 = run[0], run[-1]
        litw = x0 + (x1 - x0) * 0.62
        for x in run:
            yt = tops[x]
            n = 0
            for i in range(d):
                if yt + i < H and c.mat[yt + i, x] in ks:
                    n += 1
            for i in range(n):
                y = yt + i
                c.mat[y, x], c.tone[y, x] = k, (6 if i == 0 else 5) if x < litw else (5 if i == 0 else 4)
                c.part[y, x] = 0
            if n >= 1 and n < d:  # the run is thinner than the cap: keep at least 2 rows of snow
                pass
            yb = yt + n
            if yb < H and c.mat[yb, x] in ks:
                c.tone[yb, x] = 1
            for i in range(1, mound + 1):  # the mound above
                y = yt - i
                if y < 0 or c.mat[y, x] != 0:
                    continue
                if x0 + 2 * i <= x <= x1 - 2 * i:
                    c.mat[y, x], c.tone[y, x] = k, 6 if x < litw else 5
                    if y + 1 < H and c.mat[y + 1, x] == k:
                        c.tone[y + 1, x] = 5 if x < litw else 4
    return c


def roof_snow(c, roof_mask, bot, mid_x, seed, eave_y=None, icicle_x=None):
    """Winter roof: a snow blanket over the roof face down to a wavy front edge 6-12 texels above the
    eaves (the tiles show below it), the edge rounded (a lit line on top, the snow's thickness facing
    us, a shadow on the tiles under it), the tile rows faintly showing through as broken ridges, the
    right half one tone darker (light from the left), a plush rise on the ridge and icicles under the
    eaves board."""
    k = c.mid("snow")
    rng = random.Random(seed)
    ys, xs = np.nonzero(roof_mask)
    rows = {}
    for y, x in zip(ys, xs):
        rows.setdefault(x, []).append(y)
    ytop = int(ys.min())
    # round 3: each drift its own span, height, slope and wave (not 3 ruled parallel lines)
    x_lo, x_hi = int(xs.min()), int(xs.max())
    span = x_hi - x_lo
    drifts = [  # (row as a share of the roof, from, to (shares of the width), slope, wave amp, wave freq)
        (0.20, 0.05, 0.62, 0.03, 1.5, 0.09),
        (0.44, 0.30, 0.97, -0.04, 2.5, 0.06),
        (0.64, 0.00, 0.55, 0.02, 2.0, 0.11),
        (0.70, 0.62, 1.00, -0.02, 1.5, 0.08),
    ]
    drift_rows = [(ytop + (bot - ytop) * f, x_lo + span * a, x_lo + span * b, sl, amp, fr) for f, a, b, sl, amp, fr in drifts]
    for x, col in rows.items():
        top = min(col)
        edge = int(bot - 9 - 2.5 * math.sin(x * 0.11 + seed) - 1.5 * math.sin(x * 0.047 + 2 * seed))
        right = x > mid_x
        for y in col:
            if y >= edge + 2:
                continue
            if y >= edge:  # the shadow the snow edge casts on the tiles
                c.tone[y, x] = 1
                continue
            c.mat[y, x] = k
            d = edge - y  # rows above the edge
            if d <= 3:
                t = 3 if d <= 2 else 6  # the snow's front thickness, its lit top line
            else:
                # round 2: light by height (bright by the ridge, a tone darker towards the eaves),
                # each drift a lit crest over a 2-row shade
                f = (y - ytop) / max(1, edge - ytop)
                t = 6 if f < 0.28 else 5 if f < 0.62 else 4
                for kd, (yy, xa, xb, sl, amp, fr) in enumerate(drift_rows):
                    if not xa <= x <= xb:
                        continue
                    v = y - yy - sl * (x - xa) - amp * math.sin(x * fr + kd * 1.9 + seed)
                    if 0 <= v < 1:
                        t = 6
                    elif 1 <= v < 3:
                        t = max(3, t - 1)
                if y - top <= 1:
                    t = 6
            if right and t > 3:
                t -= 1
            elif right and t == 3:
                t = 2
            c.tone[y, x] = t
        for i in (1, 2):  # the rise along the ridge
            y = top - i
            if y >= 0 and c.mat[y, x] == 0 and min(rows) + 3 * i <= x <= max(rows) - 3 * i:
                c.mat[y, x], c.tone[y, x] = k, 5 if right else 6
    if eave_y is not None:  # icicles: 2 wide, 3-9 long, irregular spacing
        x = (icicle_x or (min(rows), max(rows)))[0] + rng.randint(3, 9)
        x_end = (icicle_x or (min(rows), max(rows)))[1] - 4
        while x < x_end:
            n = rng.randint(3, 9)
            for i in range(n):
                w = 2 if i < n - 2 else 1 if i == n - 1 else 2
                for dx in range(w):
                    if c.mat[eave_y + i, x + dx] != 0:
                        c.mat[eave_y + i, x + dx] = k
                        c.tone[eave_y + i, x + dx] = (5 if dx == 0 else 3) if x <= mid_x else (4 if dx == 0 else 2)
            x += rng.randint(8, 17)


def ledge_snow(c, x0, x1, y_top, h=3):
    """Snow on a ledge against a wall (a flower box, a sill): a low mound h rows high over whatever is
    behind, narrowing 2 texels a row, lit on the left; the ledge's top row in its shadow tone."""
    k = c.mid("snow")
    litw = x0 + (x1 - x0) * 0.62
    for i in range(h):
        y = y_top - 1 - i
        for x in range(x0 + 2 * i, x1 - 2 * i + 1):
            lit = x < litw
            t = (6 if lit else 5) if i == h - 1 or x in (x0 + 2 * i, x1 - 2 * i) and i > 0 else (5 if lit else 4)
            if i == 0:
                t = 4 if lit else 3
            c.mat[y, x], c.tone[y, x] = k, t
            c.ink.pop((x, y), None)


def cap_part(c, mask, depth=2, min_w=3):
    """Snow on one part (a stone of a ring, a foot under a stem): in every run of at least min_w
    columns, the part's top `depth` texels turn to snow (lit top row, right third one tone darker)."""
    k = c.mid("snow")
    cols = [x for x in range(c.w) if mask[:, x].any()]
    runs, cur = [], []
    for x in cols:
        if cur and x != cur[-1] + 1:
            runs.append(cur)
            cur = []
        cur.append(x)
    if cur:
        runs.append(cur)
    for run in runs:
        if len(run) < min_w:
            continue
        litw = run[0] + (run[-1] - run[0]) * 0.62
        for x in run:
            ys = np.nonzero(mask[:, x])[0]
            for i, y in enumerate(ys[:depth]):
                c.mat[y, x], c.tone[y, x] = k, (6 if i == 0 else 5) if x < litw else (5 if i == 0 else 4)
            if len(ys) > depth:
                c.tone[ys[depth], x] = 1


def finish(c, keep=(), loose=(), skip_outline=()):
    despeckle(c, keep=keep, loose=loose)
    c.outline(skip=skip_outline)
    c.shadow_band()
    return c


def roof_tiles(c, m, top, bot, xl_top, xr_top, xl_bot, xr_bot, mid, rng, row_h=8):
    """Clay tiles one by one (the pilot's roof): each row offset on its own, widths varied, a lit upper
    edge, a shadow lip on the row below; tiles vary within 2 tones; the right half one tone darker."""
    c.fill(m, "roof", 3)
    for j, ry in enumerate(range(top, bot, row_h)):
        f = (ry - top) / max(1, bot - top)
        xl, xr = xl_top + (xl_bot - xl_top) * f, xr_top + (xr_bot - xr_top) * f
        x = xl - rng.randint(0, 12)
        while x < xr:
            w = rng.choice((12, 13, 14, 14, 15, 16))
            tm = m & c.m_rect(int(x) + 1, ry, int(x + w) - 1, ry + row_h - 1)
            base = 4 if hsh(int(x), j, 3) % 4 == 0 else 3
            for yy, xx in zip(*np.nonzero(tm)):
                d = yy - ry
                t = base
                if d == row_h - 1:
                    t = 1
                elif d == row_h - 2:
                    t = base - 1
                elif d <= 1 and xx < x + 8:
                    t = min(5, base + 1)
                if xx >= x + w - 2:
                    t = max(1, t - 1)
                if xx > mid and t > 1:
                    t -= 1
                c.tone[yy, xx] = t
            x += w


def glass_pane(c, x0, y0, w, h):
    """Window glass (the pilot's): blue-black panes, a frame shadow on the top / left rows, two
    diagonal glints (tones 4-5, which stay dark-free at night: houseWindows lights tones 0-3 only)."""
    g = c.m_rect(x0, y0, x0 + w - 1, y0 + h - 1)
    c.fill(g, "glass", 2)
    for y, x in zip(*np.nonzero(g)):
        t = 2 if y - y0 > h * 0.55 else 3
        if y <= y0 + 1 or x <= x0 + 1:
            t = 1
        c.tone[y, x] = t
    return g


def short_glints(c):
    """Round 2: short glints (long diagonal ones read as cracks at night, crossing the lit pane):
    every glass texel of tone 4-5 goes back to the glass base, then each window gets one 3 x 2 light
    in its top-left pane and one short 2-wide stroke (6 texels) beside it: 12 texels a window."""
    gk = c.mid("glass")
    gm = c.mat == gk
    for (x0, y0, x1, y1) in glass_windows(gm):
        h = y1 - y0 + 1
        sel = gm & c.m_rect(x0, y0, x1, y1) & (c.tone >= 4)
        for y, x in zip(*np.nonzero(sel)):
            c.tone[y, x] = 2 if y - y0 > h * 0.55 else 3
        px, py = x0 + 4, y0 + 4
        for dx in range(3):
            for dy in range(2):
                if gm[py + dy, px + dx]:
                    c.tone[py + dy, px + dx] = 5
        for i in range(3):  # the stroke, from lower left to upper right
            for dx in range(2):
                X, Y = px + 5 + i + dx, py + 6 - i
                if gm[Y, X]:
                    c.tone[Y, X] = 4


def glass_windows(gm):
    """Bounding boxes of the windows in a glass mask (panes split by mullions merged into one)."""
    H, W = gm.shape
    seen = np.zeros_like(gm)
    wins = []
    for y in range(H):
        for x in range(W):
            if gm[y, x] and not seen[y, x]:
                st, comp = [(y, x)], []
                seen[y, x] = True
                while st:
                    q = st.pop()
                    comp.append(q)
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        Y, X = q[0] + dy, q[1] + dx
                        if 0 <= Y < H and 0 <= X < W and gm[Y, X] and not seen[Y, X]:
                            seen[Y, X] = True
                            st.append((Y, X))
                if len(comp) >= 20:
                    ys, xs = zip(*comp)
                    wins.append((min(xs), min(ys), max(xs), max(ys)))
    merged = True
    while merged:
        merged = False
        for i in range(len(wins)):
            for j in range(i + 1, len(wins)):
                A, B = wins[i], wins[j]
                if A[0] - 4 <= B[2] and B[0] - 4 <= A[2] and A[1] - 4 <= B[3] and B[1] - 4 <= A[3]:
                    wins[i] = (min(A[0], B[0]), min(A[1], B[1]), max(A[2], B[2]), max(A[3], B[3]))
                    del wins[j]
                    merged = True
                    break
            if merged:
                break
    return sorted(wins, key=lambda r: (r[1], r[0]))


def flower_box(c, x0, x1, y0, season):
    """A plank box under a window; summer pink / yellow flowers, autumn marigolds (the same ramps,
    autumn colours); winter: an empty box under snow (drawn by the caller's snow pass)."""
    b = c.m_rect(x0, y0, x1, y0 + 7)
    c.fill(b, "plank", 3)
    grain(c, b, vertical=False, seed=x0)
    bevel(c, b)
    if season == "winter":
        return
    w = x1 - x0
    for k in range(0, w - 2, 4):
        x = x0 + 2 + k
        c.fill(c.m_ellipse(x + 1.5, y0 - 1, 2.8, 2.4), "leaf", 3 if k % 8 else 4)
    cols = ("pink", "yellow", "pink", "pink", "yellow", "pink", "yellow", "pink", "yellow")
    for i, k in enumerate(range(3, w - 3, 6)):
        x = x0 + k
        col = cols[i % len(cols)]
        c.fill(c.m_ellipse(x + 1, y0 - 2, 2.0, 2.0), col, 4)
        c.fill(c.m_rect(x, y0 - 3, x + 1, y0 - 3), col, 5)


# ------------------------------------------------------------------ obj.house (192 x 224)

HOUSE_W, HOUSE_H = 192, 224
H_ROOF_TOP, H_ROOF_BOT = 24, 90
H_WALL_TOP, H_WALL_BOT = 95, 205
H_DOOR = (72, 119, 114)  # x0, x1, top: the door 104 texels high (the hero is 112: 93%)
H_WIN = ((24, 122, 30, 40), (138, 122, 30, 40))  # glass x, y, w, h


def house(season):
    W, H = HOUSE_W, HOUSE_H
    G = H - 1
    c = canvas(W, H, season)
    rng = random.Random(7)
    mid = (W - 1) / 2
    # chimney (behind the roof)
    ch = c.m_rect(134, 6, 152, 44)
    c.fill(ch, "stone", 3)
    for y in range(11, 45, 7):
        c.fill(c.m_rect(134, y, 152, y), "stone", 1)
        for x in range(134 + (y // 7 % 2) * 5, 153, 10):
            c.fill(c.m_rect(x, y, x, min(44, y + 6)), "stone", 1)
    bevel(c, ch)
    darken_right(c, ch, 148)
    c.fill(c.m_rect(132, 4, 154, 8), "stone", 4)
    c.fill(c.m_rect(132, 8, 154, 8), "stone", 1)
    # stone base
    base = c.m_rect(4, H_WALL_BOT + 1, 187, G)
    c.fill(base, "stone", 3)
    y, r = H_WALL_BOT + 1, 0
    while y <= G:
        x = 4 - (r % 2) * 9
        while x <= 187:
            w = rng.randint(16, 26)
            m = c.m_rect(max(4, x + 1), y + 1, min(187, x + w - 1), min(G, y + 8))
            c.fill(m, "stone", rng.choice((3, 3, 2, 4)))
            bevel(c, m)
            x += w
        y += 9
        r += 1
    c.fill(c.m_rect(4, H_WALL_BOT + 1, 187, G) & (c.tone == 3) & (c.mat == c.mid("stone")) & ~c.m_rect(0, 0, W, 0), "stone", 3, over=False)
    c.fill(c.m_rect(4, H_WALL_BOT + 1, 187, H_WALL_BOT + 1), "stone", 1)
    # plaster wall
    wall = c.m_rect(6, H_WALL_TOP, 185, H_WALL_BOT)
    c.fill(wall, "plaster", 3)
    for y, x in zip(*np.nonzero(wall)):
        if y < H_WALL_TOP + 7:
            c.tone[y, x] = 1 if y < H_WALL_TOP + 3 else 2
        elif hsh(x // 3, y // 2, 1) % 41 == 0:
            c.tone[y, x] = 4
        elif hsh(x // 4, y // 3, 2) % 37 == 0:
            c.tone[y, x] = 2
    # timber frame: corner posts, door jambs, top and sill beams, braces in the lower panels
    for (xa, xb) in ((16, 60), (175, 131)):
        c.fill(c.m_line([(xa, H_WALL_BOT - 4), (xb, 178)], 5.0) & wall, "timber", 3)
        c.fill(c.m_line([(xa - 1, H_WALL_BOT - 5), (xb - 1, 177)], 1.4) & wall, "timber", 4)
    for x0, x1 in ((6, 11), (180, 185), (66, 71), (120, 125)):
        m = c.m_rect(x0, H_WALL_TOP, x1, H_WALL_BOT)
        c.fill(m, "timber", 3)
        grain(c, m, True, x0)
        bevel(c, m)
    for y0, y1 in ((H_WALL_TOP, H_WALL_TOP + 5), (H_WALL_BOT - 5, H_WALL_BOT), (174, 177)):
        m = c.m_rect(6, y0, 185, y1) & ~c.m_rect(72, 0, 119, H)
        c.fill(m, "timber", 3)
        grain(c, m, False, y0)
        bevel(c, m)
    # windows: frame, glass, mullions, teal shutters, flower box
    for gx, gy, gw, gh in H_WIN:
        fr = c.m_rect(gx - 3, gy - 3, gx + gw + 2, gy + gh + 2)
        c.fill(fr, "timber", 3)
        bevel(c, fr)
        glass_pane(c, gx, gy, gw, gh)
        c.fill(c.m_rect(gx + gw // 2 - 1, gy, gx + gw // 2, gy + gh - 1), "timber", 2)
        c.fill(c.m_rect(gx, gy + gh // 2 - 1, gx + gw - 1, gy + gh // 2), "timber", 2)
        c.fill(c.m_rect(gx + gw // 2 - 1, gy + gh // 2 - 1, gx + gw // 2 - 1, gy + gh // 2 - 1), "timber", 4)
        for sx in (gx - 3 - 9, gx + gw + 3):
            s = c.m_rect(sx, gy - 3, sx + 8, gy + gh + 2)
            c.fill(s, "teal", 3)
            for yy in range(gy - 3, gy + gh + 3):
                c.put(sx + 4, yy, "teal", 2)
            for yy in (gy + 4, gy + gh - 5):  # the two battens
                c.fill(c.m_rect(sx, yy, sx + 8, yy + 1), "teal", 1)
                c.fill(c.m_rect(sx + 1, yy - 1, sx + 7, yy - 1), "teal", 4)
            bevel(c, s)
        flower_box(c, gx - 4, gx + gw + 3, gy + gh + 3, season)
    short_glints(c)
    # the door: an arched plank door in a timber arch, iron straps, a ring, a stone step
    x0, x1, y0 = H_DOOR
    cx = (x0 + x1 + 1) / 2
    arch = c.m_ellipse(cx, y0 + 18, (x1 - x0) / 2 + 6, 22) & c.m_rect(0, 0, W - 1, y0 + 18)
    c.fill(arch & c.m_rect(0, H_WALL_TOP + 6, W - 1, H), "timber", 3)
    bevel(c, arch)
    d = (c.m_rect(x0, y0 + 18, x1, G - 6) | c.m_ellipse(cx, y0 + 19, (x1 - x0 + 1) / 2, 17)) & c.m_rect(x0, y0 + 2, x1, G - 6)
    c.fill(d, "plank", 3)
    for x in range(x0 + 6, x1, 8):
        c.fill(c.m_rect(x, 0, x, G) & d, "plank", 1)
    grain(c, d, vertical=True, seed=5)
    for y in (y0 + 30, G - 30):
        c.fill(c.m_rect(x0, y, x1, y + 3) & d, "iron", 3)
        c.fill(c.m_rect(x0, y, x1, y) & d, "iron", 4)
        c.fill(c.m_rect(x0, y + 3, x1, y + 3) & d, "iron", 1)
        for x in range(x0 + 3, x1, 8):
            c.fill(c.m_rect(x, y + 1, x + 1, y + 2), "iron", 5)
    ring = c.m_ellipse(x1 - 9, y0 + 62, 3.4, 3.4) & ~c.m_ellipse(x1 - 9, y0 + 62, 1.6, 1.6)
    c.fill(ring, "gold", 3)
    c.fill(c.m_rect(x1 - 11, y0 + 59, x1 - 10, y0 + 60), "gold", 5)
    for y, x in zip(*np.nonzero(d)):  # set back in the wall: shade under the arch and on the left jamb
        if y < y0 + 8 or x < x0 + 3:
            c.tone[y, x] = max(1, int(c.tone[y, x]) - 1)
    step = c.m_rect(x0 - 8, G - 5, x1 + 8, G)
    c.fill(step, "stone", 4)
    bevel(c, step)
    # roof (over the wall's top), eaves board
    # round 3: the eaves 1 texel in from the picture's sides (their outline inside the picture)
    rm = c.m_poly([(1, H_ROOF_BOT), (191, H_ROOF_BOT), (164, H_ROOF_TOP), (28, H_ROOF_TOP)])
    roof_tiles(c, rm, H_ROOF_TOP, H_ROOF_BOT, 28, 164, 1, 191, mid, rng)
    ridge = c.m_rect(26, H_ROOF_TOP - 6, 165, H_ROOF_TOP + 1)
    c.fill(ridge, "roof", 4)
    for x in range(26, 166, 10):
        c.fill(c.m_rect(x, H_ROOF_TOP - 6, x, H_ROOF_TOP + 1), "roof", 1)
        c.fill(c.m_rect(x + 2, H_ROOF_TOP - 5, x + 3, H_ROOF_TOP - 4), "roof", 5)
    c.fill(c.m_rect(26, H_ROOF_TOP + 1, 165, H_ROOF_TOP + 1), "roof", 1)
    c.fill(c.m_rect(97, H_ROOF_TOP - 6, 165, H_ROOF_TOP + 1) & (c.mat == c.mid("roof")) & (c.tone > 1), "roof", 3)
    eave = c.m_rect(1, H_ROOF_BOT, W - 2, H_ROOF_BOT + 4)
    c.fill(eave, "timber", 2)
    c.fill(c.m_rect(1, H_ROOF_BOT, W - 2, H_ROOF_BOT), "timber", 4)
    roof_all = (c.mat == c.mid("roof")) & c.m_rect(0, 0, W - 1, H_ROOF_BOT)
    # the right end of the wall in shade
    darken_right(c, c.m_rect(0, H_ROOF_BOT + 5, W - 1, H), 176)
    if season == "winter":
        roof_snow(c, roof_all, H_ROOF_BOT, mid, 3, eave_y=H_ROOF_BOT + 5, icicle_x=(4, 186))
        snow_on(c, ("stone",), seed=1, depth=(2, 3), mound=1, region=c.m_rect(130, 0, 156, 10))
        for gx, gy, gw, gh in H_WIN:  # snow on the flower boxes
            ledge_snow(c, gx - 4, gx + gw + 3, gy + gh + 3, 3)
    finish(c, keep=("pink", "yellow", "iron", "gold"), loose=("snow",))
    return c


# ------------------------------------------------------------------ the stone house's seasons


def house_stone(season, pilot_drawing=False):
    """The pilot's drawing steps, in the pilot's order with its random sequence (summer = the pilot's
    file, pixel for pixel; checked by main), then the season: autumn flowers (ramps), winter snow."""
    r = ramps_for(season)
    if pilot_drawing:
        r["glass"] = HS.RAMPS["glass"]
    c = Canvas(HS.W, HS.H, r)
    rng = random.Random(42)
    HS.chimney(c)
    if not pilot_drawing:  # round 3: the chimney cap one row lower, its outline on row 0 (not cut by the edge)
        c.mat[0, :] = 0
    HS.side_wall(c, rng)
    HS.stones(c, 16, HS.UP_BOT, 239, HS.G, rng)
    c.fill(c.m_rect(16, HS.UP_BOT, 239, HS.UP_BOT + 4), "stone", 1)
    HS.upper_floor(c)
    HS.roof(c, rng)
    HS.window(c, 36, 202, 40, 50)
    HS.window(c, 180, 202, 40, 50)
    HS.front_door(c)
    if not pilot_drawing:
        short_glints(c)  # round 2 (the pilot's own drawing keeps its long glints)
    for y, x in zip(*np.nonzero(c.mat != 0)):
        if x > 228 and c.tone[y, x] > 1 and y > HS.ROOF_BOT:
            c.tone[y, x] -= 1
    if season == "winter":
        lantern = c.m_rect(158, 194, 172, 214)
        fl = np.isin(c.mat, [c.mid("leaf"), c.mid("pink"), c.mid("yellow")]) & ~lantern
        c.mat[fl] = c.mid("plaster")  # the boxes are empty in winter: the wall behind, then snow
        c.tone[fl] = 3
        roof_all = (c.mat == c.mid("roof")) & c.m_rect(0, 0, HS.W - 1, HS.ROOF_BOT)
        roof_snow(c, roof_all, HS.ROOF_BOT, HS.W / 2, 5, eave_y=HS.ROOF_BOT + 4, icicle_x=(6, 248))
        snow_on(c, ("stone",), seed=2, depth=(2, 3), mound=2, region=c.m_rect(178, 0, 210, 6)) if pilot_drawing else \
            snow_on(c, ("stone",), seed=2, depth=(2, 2), mound=0, region=c.m_rect(178, 0, 210, 6))
        for x0, w, y0, h in ((36, 40, 202, 50), (180, 40, 202, 50), (40, 30, 114, 40), (186, 30, 114, 40)):
            ledge_snow(c, x0 - 4, x0 + w + 3, y0 + h + 3, 4)
        despeckle(c, keep=("pink", "yellow", "iron"), loose=("snow",))
    else:
        despeckle(c, keep=("pink", "yellow", "iron"))
    c.outline()
    c.shadow_band()
    return c


# ------------------------------------------------------------------ chest (64 x 56)


def chest(season, opened):
    c = canvas(64, 56, season)
    G = 54
    body = c.m_rect(4, 27, 59, G)
    c.fill(body, "chestwood", 3)
    for y0 in (27, 36, 45):  # three planks
        m = c.m_rect(4, y0, 59, min(G, y0 + 8))
        c.fill(m, "chestwood", 3)
        grain(c, m, vertical=False, seed=y0)
        c.fill(c.m_rect(4, y0, 59, y0), "chestwood", 4)
        c.fill(c.m_rect(4, min(G, y0 + 8), 59, min(G, y0 + 8)), "chestwood", 1)
    c.fill(c.m_rect(4, G - 1, 59, G), "chestwood", 2)
    if not opened:
        lid = (c.m_ellipse(31.5, 18, 28.5, 12) & c.m_rect(0, 0, 63, 25)) | c.m_rect(4, 18, 59, 25)
        c.fill(lid, "chestwood", 3)
        c.shade_part(lid, tones=(2, 3, 3, 4, 4), norm=True)
        for y0 in (12, 19):
            c.fill(c.m_rect(4, y0, 59, y0) & lid, "chestwood", 2)
        grain(c, lid & c.m_rect(0, 8, 63, 25), vertical=False, seed=3)
        c.fill(c.m_rect(3, 24, 60, 27), "gold", 3)  # the lid's rim
        c.fill(c.m_rect(3, 24, 60, 24), "gold", 4)
        c.fill(c.m_rect(3, 27, 60, 27), "gold", 1)
    else:  # round 2: the lid thrown right back (its dark underside), a dark mouth, a heap of gold
        under = c.m_poly([(5, 21), (58, 21), (55, 4), (8, 4)])  # round 3: 2 rows lower
        c.fill(under, "chestwood", 1)  # the underside, away from the light: dark
        for y0 in (8, 14):  # the underside's planks: a lit lip over a dark seam
            c.fill(c.m_rect(0, y0, 63, y0) & under, "chestwood", 0)
            c.fill(c.m_rect(0, y0 - 1, 63, y0 - 1) & under, "chestwood", 2)
        c.fill(under & c.m_rect(0, 4, 63, 5), "chestwood", 2)
        edge = c.m_poly([(8, 5), (55, 5), (54, 1), (9, 1)])  # the lid's thickness, lit; outline on row 0
        c.fill(edge, "chestwood", 4)
        c.fill(edge & c.m_rect(0, 4, 63, 4), "chestwood", 3)
        for bx in (11, 46):  # gold bands across the underside
            band = under & c.m_rect(bx, 0, bx + 5, 63)
            c.fill(band, "gold", 2)
            c.fill(band & c.m_rect(bx, 0, bx, 63), "gold", 3)
            c.fill(edge & c.m_rect(bx, 0, bx + 5, 63), "gold", 4)
        c.fill(c.m_rect(5, 19, 58, 21), "chestwood", 3)  # the box's back rim, lit
        c.fill(c.m_rect(5, 19, 58, 19), "chestwood", 4)
        mouth = c.m_rect(6, 22, 57, 29)
        c.fill(mouth, "chestwood", 0)  # the dark inside
        heap = c.m_ellipse(30.5, 33, 17, 7.5) & c.m_rect(0, 0, 63, 29)
        c.fill(heap, "gold", 3)
        c.shade_part(heap, tones=(2, 3, 4, 4), norm=True)
        for gx, gy in ((19, 28), (25, 27), (30, 26), (40, 27), (44, 28)):
            c.fill(c.m_rect(gx, gy, gx + 1, gy + 1), "gold", 5 if gx < 34 else 4)
        c.fill(c.m_rect(34, 25, 36, 27), "gem", 4)  # a blue gem on the heap
        c.fill(c.m_rect(34, 25, 34, 25), "gem", 5)
        c.fill(c.m_rect(3, 29, 60, 31), "gold", 3)  # the box's top rim
        c.fill(c.m_rect(3, 29, 60, 29), "gold", 4)
        c.fill(c.m_rect(3, 31, 60, 31), "gold", 1)
    for bx in (11, 46):  # gold bands
        top = 9 if not opened else 32
        band = c.m_rect(bx, top, bx + 6, G) & (c.mat != 0)
        c.fill(band, "gold", 3)
        c.fill(band & c.m_rect(bx, 0, bx + 1, G), "gold", 4)
        c.fill(band & c.m_rect(bx + 6, 0, bx + 6, G), "gold", 1)
        for ry in ((14, 33, 47) if not opened else (36, 47)):
            c.fill(c.m_rect(bx + 2, ry, bx + 3, ry + 1), "gold", 5)
    # lock plate (on the lid when closed; hanging on the body when open)
    ly = 20 if not opened else 31  # the same plate (shape, colour, keyhole) in both states
    plate = c.m_rect(26, ly, 37, ly + 13)
    c.fill(plate, "gold", 3)
    bevel(c, plate)
    c.fill(c.m_rect(31, ly + 4, 32, ly + 7), "chestwood", 0)
    c.fill(c.m_rect(31, ly + 8, 32, ly + 9), "chestwood", 1)
    darken_right(c, c.m_rect(0, 0, 63, 63) & (c.mat == c.mid("chestwood")), 52)
    if season == "winter":
        if not opened:  # round 3: an opened lid has shed its snow
            snow_on(c, ("chestwood", "gold"), seed=4, depth=(3, 3), mound=2)
    finish(c, keep=("gold", "gem"), loose=("snow",))
    return c


# ------------------------------------------------------------------ barrel (48 x 56)


def barrel(season):
    c = canvas(48, 56, season)
    G = 54
    cx = 23.5
    body = np.zeros((56, 48), bool)
    for y in range(10, G + 1):
        hw = 16 + 3.0 * math.sin(math.pi * (y - 10) / (G - 10))
        body[y, int(round(cx - hw)):int(round(cx + hw)) + 1] = True
    c.fill(body, "plank", 3)
    cyl(c, body, cx - 19, cx + 19, tones=(4, 4, 3, 3, 3, 3, 2, 2, 1))
    for k in range(-15, 17, 6):  # staves: seams that follow the bulge
        for y in range(10, G + 1):
            hw = 16 + 3.0 * math.sin(math.pi * (y - 10) / (G - 10))
            x = int(round(cx + k * hw / 16))
            if body[y, x]:
                c.tone[y, x] = max(1, int(c.tone[y, x]) - 1)
    grain(c, body, vertical=True, seed=2)
    for hy in (17, 44):  # iron hoops
        hoop = body & c.m_rect(0, hy, 47, hy + 3)
        c.fill(hoop, "iron", 3)
        cyl(c, hoop, cx - 19, cx + 19, tones=(5, 4, 4, 3, 3, 3, 2, 2, 1))
        c.fill(hoop & c.m_rect(0, hy + 3, 47, hy + 3), "iron", 1)
        for rx in (cx - 12, cx + 4):
            c.fill(c.m_rect(int(rx), hy + 1, int(rx) + 1, hy + 2), "iron", 5)
    lid = c.m_ellipse(cx + 0.5, 10.5, 16.5, 5.5)
    c.fill(lid, "plank", 2)
    rim = lid & ~c.m_ellipse(cx + 0.5, 10.8, 14, 4.2)
    c.fill(rim, "plank", 4)
    c.fill(rim & c.m_rect(int(cx) + 4, 0, 47, 55), "plank", 3)
    for x in (16, 23, 30):
        c.fill(c.m_rect(x, 7, x, 14) & lid & ~rim, "plank", 1)
    c.fill(c.m_rect(10, 9, 14, 10) & lid & ~rim, "plank", 3)
    if season == "winter":
        snow_on(c, ("plank",), seed=6, depth=(3, 4), mound=2)
    finish(c, keep=("iron",), loose=("snow",))
    return c


# ------------------------------------------------------------------ crate (64 x 64)


def crate(season):
    c = canvas(64, 64, season)
    G = 62
    top = c.m_poly([(4, 13), (8, 5), (60, 5), (60, 13)])
    c.fill(top, "plank", 4)
    for x in range(14, 60, 11):
        c.fill(c.m_rect(x, 5, x, 13) & top, "plank", 2)
    grain(c, top, vertical=True, seed=8)
    front = c.m_rect(4, 14, 59, G)
    c.fill(front, "plank", 3)
    for y0 in range(20, G - 4, 9):  # inner boards
        m = c.m_rect(10, y0, 53, min(G - 6, y0 + 7))
        c.fill(m, "plank", 2 if (y0 // 9) % 2 else 3)
        grain(c, m, vertical=False, seed=y0)
        c.fill(c.m_rect(10, y0 + 8, 53, y0 + 8) & front, "plank", 1)
    c.fill(c.m_line([(12, G - 8), (51, 22)], 6.0), "plank", 3)  # the brace
    c.fill(c.m_line([(11, G - 10), (50, 20)], 1.3), "plank", 4)
    for m in (c.m_rect(4, 14, 59, 19), c.m_rect(4, G - 5, 59, G), c.m_rect(4, 14, 9, G), c.m_rect(54, 14, 59, G)):
        c.fill(m, "plank", 3)
        grain(c, m, vertical=m.sum(0).max() > 20, seed=int(m.sum()))
        bevel(c, m)
    for nx, ny in ((6, 16), (56, 16), (6, G - 3), (56, G - 3)):
        c.fill(c.m_rect(nx, ny, nx + 1, ny + 1), "iron", 4)
    darken_right(c, front, 52)
    if season == "winter":
        snow_on(c, ("plank",), seed=7, depth=(4, 5), mound=2)
    finish(c, keep=("iron",), loose=("snow",))
    return c


# ------------------------------------------------------------------ jar (40 x 48)


def jar(season):
    c = canvas(40, 48, season)
    body = c.m_ellipse(19.5, 30.5, 16.5, 16.5) & c.m_rect(0, 0, 39, 46)
    body |= c.m_rect(10, 41, 29, 46)  # round 2: down to row 46, its outline on the bottom row
    neck = c.m_rect(12, 7, 27, 16)
    c.fill(neck | body, "clay", 3)
    c.shade_part(body, tones=(1, 2, 3, 4, 5), norm=True)
    cyl(c, neck, 12, 27, tones=(4, 3, 3, 2, 1))
    band = body & c.m_rect(0, 22, 39, 28)
    c.fill(band, "glaze", 3)
    c.shade_part(band, tones=(1, 2, 3, 4), norm=True)
    c.fill(band & c.m_rect(0, 22, 39, 22), "glaze", 4)
    c.fill(band & c.m_rect(0, 28, 39, 28), "glaze", 1)
    for x in range(8, 33, 6):
        c.fill(c.m_rect(x, 25, x + 1, 25) & band, "glaze", 5)
    rim = c.m_ellipse(19.5, 6.5, 10.5, 3.6)
    c.fill(rim, "clay", 4)
    c.fill(c.m_ellipse(19.5, 6.6, 7, 1.8), "clay", 1)
    c.fill(c.m_rect(6, 31, 8, 36), "clay", 5)
    if season == "winter":
        snow_on(c, ("clay",), seed=8, depth=(2, 3), mound=1, region=c.m_rect(0, 0, 39, 18))
    finish(c, keep=("glaze",), loose=("snow", "clay"))
    return c


# ------------------------------------------------------------------ fire (campfire, brazier)


def flames(c, cx, base_y, height, width, frame, seed):
    """Three tongues of flame (frame 0 / 1: the tips sway and the heights change), each red outside,
    orange, yellow and a pale core; 2 x 2 sparks above (in other places each frame)."""
    rng = random.Random(seed * 10 + frame)
    tongues = ((-width * 0.32, 0.72, -2), (0, 1.0, 2), (width * 0.3, 0.66, 3))
    allm = np.zeros((c.h, c.w), bool)
    for i, (dx, hf, lean) in enumerate(tongues):
        hgt = min(height * hf * (1.08 if (i + frame) % 2 else 0.92), base_y - 3)
        sway = (2.5 if frame else -2.5) * (1 if i != 1 else -0.6)
        x0 = cx + dx
        pts_l, pts_r = [], []
        for k in range(9):
            t = k / 8
            y = base_y - hgt * t
            w = (width * 0.30) * (1 - t) ** 0.8 * (1 + 0.25 * math.sin(t * 7 + frame))
            xc = x0 + (lean + sway) * t * t
            pts_l.append((xc - w, y))
            pts_r.append((xc + w, y))
        m = c.m_poly(pts_l + pts_r[::-1])
        allm |= m
    c.fill(allm, "fire", 2)
    d = np.zeros_like(allm, np.float32)
    inner = allm.copy()
    for layer, t in ((1, 3), (3, 4), (6, 5)):
        for _ in range(layer if layer == 1 else 2):
            e = inner.copy()
            e[1:, :] &= inner[:-1, :]
            e[:-1, :] &= inner[1:, :]
            e[:, 1:] &= inner[:, :-1]
            e[:, :-1] &= inner[:, 1:]
            inner = e
        sel = inner & (np.arange(c.h)[:, None] > base_y - height * (0.75 if t == 3 else 0.5 if t == 4 else 0.3))
        c.set_tone(sel, t)
    c.set_tone(allm & ~np.roll(allm, 1, 1), 1)  # the left edge red
    for _ in range(3):
        sx = int(cx + rng.randint(-int(width * 0.6), int(width * 0.6)))
        sy = max(2, int(base_y - height * rng.uniform(0.9, 1.25)))
        if 0 <= sy < c.h - 1 and 0 <= sx < c.w - 1 and not allm[sy:sy + 2, sx:sx + 2].any():
            c.fill(c.m_rect(sx, sy, sx + 1, sy + 1), "fire", 4)
    return allm


def campfire(season, frame):
    c = canvas(64, 56, season)
    stones0 = []
    for i in range(11):
        a = math.pi * 2 * (i + 0.5) / 11
        if math.sin(a) <= 0:
            sx, sy = 31.5 + math.cos(a) * 25, 45 + math.sin(a) * 7.5
            m = c.m_ellipse(sx, sy, 4.2, 3.2)
            c.fill(m, "stone", 3)
            c.shade_part(m, tones=(1, 2, 3, 4), norm=True)
            c.set_tone(m & (c.tone >= 3), 4)
    ash = c.m_ellipse(31.5, 46, 21, 6)
    c.fill(ash, "ash", 2)
    c.fill(ash & c.m_rect(0, 0, 63, 44), "ash", 1)
    for (a, b, w) in (((12, 49), (46, 38), 5.5), ((16, 38), (50, 48), 5.5)):  # crossed logs
        lg = c.m_line([a, b], w)
        c.fill(lg, "plank", 3)
        c.fill(c.m_line([(a[0], a[1] - 2), (b[0], b[1] - 2)], 1.4) & lg, "plank", 4)
        c.fill(c.m_line([(a[0], a[1] + 2), (b[0], b[1] + 2)], 1.4) & lg, "plank", 1)
        c.fill(c.m_ellipse(a[0], a[1], 2.8, 2.8), "plank", 4)
        c.fill(c.m_ellipse(a[0], a[1], 1.2, 1.2), "fire", 3)  # the glowing log end
    stones = []
    for i in range(11):  # the stone ring: back stones small and high, front stones big and low
        a = math.pi * 2 * (i + 0.5) / 11
        sx, sy = 31.5 + math.cos(a) * 25, 45 + math.sin(a) * 7.5
        front = math.sin(a) > 0
        rx, ry = (5.2, 4.2) if front else (4.2, 3.2)
        stones.append((sy, sx, rx, ry))
    def stone(sy, sx, rx, ry):
        m = c.m_ellipse(sx, sy, rx, ry) & c.m_rect(0, 0, 63, 54)
        c.fill(m, "stone", 3)
        c.shade_part(m, tones=(1, 2, 3, 4), norm=True)
        if sy < 45:  # the back stones lit by the fire
            c.set_tone(m & (c.tone >= 3), 4)

    order = sorted(stones)
    flames(c, 31.5, 43, 36, 16, frame, 1)
    # round 2: the logs' front halves over the flames' foot (the crossed logs read again)
    for (a, b, w) in (((10, 50), (48, 38), 5.5), ((14, 38), (52, 49), 5.5), ((31, 51), (31, 41), 5.0)):
        lg = c.m_line([a, b], w) & c.m_rect(0, 42, 63, 55)
        c.fill(lg, "plank", 3)
        c.fill(c.m_line([(a[0], a[1] - 2), (b[0], b[1] - 2)], 1.4) & lg, "plank", 4)
        c.fill(c.m_line([(a[0], a[1] + 2), (b[0], b[1] + 2)], 1.4) & lg, "plank", 1)
    for st in order:
        if st[0] >= 45:
            stone(*st)
            if season == "winter" and abs(st[1] - 31.5) > 8:  # snow on the outer front stones (cold)
                m = c.m_ellipse(st[1], st[0], st[2], st[3]) & c.m_rect(0, 0, 63, 54) & (c.mat == c.mid("stone"))
                cap_part(c, m & c.m_rect(2, 0, 61, 63), 2, 4)
    finish(c, keep=("fire",), loose=("snow", "ash"), skip_outline=("fire",))
    return c


def brazier(season, frame):
    c = canvas(48, 64, season)
    G = 62
    foot = c.m_poly([(12, G), (36, G), (32, 55), (16, 55)])
    c.fill(foot, "ruin", 3)
    stem = c.m_rect(19, 40, 28, 55)
    c.fill(stem, "ruin", 3)
    cyl(c, stem, 19, 28, tones=(4, 3, 3, 2, 1))
    cyl(c, foot, 12, 36, tones=(4, 4, 3, 3, 2, 1))
    c.fill(c.m_rect(12, G, 36, G), "ruin", 1)
    bowl = c.m_poly([(4, 30), (44, 30), (36, 41), (12, 41)])
    c.fill(bowl, "ruin", 3)
    cyl(c, bowl, 4, 44, tones=(4, 4, 3, 3, 3, 2, 1))
    band = bowl & c.m_rect(0, 34, 47, 36)
    c.fill(band, "ruin", 2)
    for x in range(9, 40, 6):
        c.fill(c.m_rect(x, 34, x + 1, 35), "glow", 2)
    rim = c.m_rect(3, 27, 44, 30)
    c.fill(rim, "ruin", 4)
    c.fill(c.m_rect(3, 30, 44, 30), "ruin", 2)
    c.fill(c.m_rect(36, 27, 44, 29), "ruin", 3)
    c.fill(c.m_rect(8, 25, 39, 27), "ash", 2)
    flames(c, 23.5, 27, 24, 24, frame, 2)
    if season == "winter":
        cap_part(c, foot & ~c.m_rect(19, 0, 28, 63), 2, 3)  # the foot's two shoulders beside the stem
    finish(c, keep=("fire", "glow"), loose=("snow",), skip_outline=("fire",))
    return c


# ------------------------------------------------------------------ checkpoint (48 x 80)


def checkpoint(season, on):
    c = canvas(48, 80, season)
    G = 78
    s1 = c.m_rect(2, 70, 45, G)
    c.fill(s1, "stone", 3)
    bevel(c, s1)
    s2 = c.m_rect(7, 62, 40, 69)
    c.fill(s2, "stone", 3)
    bevel(c, s2)
    stele = (c.m_rect(11, 24, 36, 61) | c.m_ellipse(23.5, 24, 12.5, 13)) & c.m_rect(0, 11, 47, 61)
    c.fill(stele, "stone", 3)
    c.shade_part(stele, tones=(2, 3, 3, 4), norm=True, dome=0.6)
    cyl(c, stele & c.m_rect(31, 0, 47, 79), 0, 40, tones=(2,))
    groove_t = 1
    ring = c.m_ellipse(23.5, 30, 8.5, 8.5) & ~c.m_ellipse(23.5, 30, 6.5, 6.5)
    cross = (c.m_rect(23, 22, 24, 38) | c.m_rect(15, 29, 32, 30)) & c.m_ellipse(23.5, 30, 6.5, 6.5)
    # round 2: a straight stem with 3 diamonds (the zigzag read as a crack)
    glyph = c.m_rect(23, 42, 24, 57)
    for gy in (45, 50, 55):
        glyph |= c.m_poly([(23.5, gy - 2.5), (26.5, gy), (23.5, gy + 2.5), (20.5, gy)])
    for m in (ring, cross, glyph):
        if on:
            c.fill(m, "gem", 4)
        else:
            c.fill(m, "stone", groove_t)
    if on:
        c.fill(c.m_rect(22, 29, 25, 31), "gem", 5)
        c.fill(ring & c.m_rect(0, 0, 23, 29), "gem", 5)
        halo = (c.m_ellipse(23.5, 30, 10.5, 10.5) & ~c.m_ellipse(23.5, 30, 8.5, 8.5)) & stele
        c.set_tone(halo & (c.mat == c.mid("stone")), 4)
        star = c.m_poly([(23.5, 0), (25.5, 4), (30, 5.5), (25.5, 7), (23.5, 11), (21.5, 7), (17, 5.5), (21.5, 4)])
        c.fill(star, "gem", 4)
        c.fill(c.m_rect(23, 4, 24, 6), "gem", 5)
    moss = (c.m_rect(3, 70, 15, 71) | c.m_rect(5, 72, 8, 74) | c.m_rect(8, 62, 16, 63) | c.m_rect(11, 64, 12, 65)) & (c.mat != 0)
    c.fill(moss, "moss", 3)
    c.fill(moss & c.m_rect(0, 0, 9, 79), "moss", 4)
    if season == "winter":
        snow_on(c, ("stone", "moss"), seed=11, depth=(2, 3), mound=2)
    finish(c, keep=("gem",), loose=("snow",))
    return c


# ------------------------------------------------------------------ pressure plate (56 x 40)


def plate(season, on):
    """Round 2: a floor plate seen from above. A stone frame (a wide top face, a 5-texel front edge)
    round a square slab. off: the slab stands proud (lit top, a 3-texel front lip, a dim carved
    sign). on: the slab sunk into the frame (dark, in the frame's shadow on its top and left), the seam
    and the sign glowing ruin teal, the frame's front studs lit."""
    c = canvas(56, 40, season)
    G = 38
    frame = c.m_rect(1, 3, 54, 33)
    c.fill(frame, "ruin", 3)
    c.fill(c.m_rect(1, 3, 54, 4), "ruin", 4)
    c.fill(c.m_rect(1, 3, 2, 33), "ruin", 4)
    front = c.m_rect(1, 34, 54, G)
    c.fill(front, "ruin", 2)
    c.fill(c.m_rect(1, G, 54, G), "ruin", 1)
    for x in (14, 27, 40):
        c.fill(c.m_rect(x, 34, x, G), "ruin", 1)
    for x in range(6, 52, 8):  # studs on the front edge
        c.fill(c.m_rect(x, 35, x + 1, 36), "glow", 4 if on else 1)
    pit = c.m_rect(6, 7, 49, 29)
    if not on:
        c.fill(pit, "ruin", 1)
        slab = c.m_rect(7, 6, 48, 25)
        c.fill(slab, "ruin", 4)
        bevel(c, slab)
        c.fill(c.m_rect(7, 26, 48, 28), "ruin", 3)  # the slab's front lip (it stands proud)
        c.fill(c.m_rect(7, 28, 48, 28), "ruin", 2)
        c.fill(c.m_rect(7, 6, 48, 6), "ruin", 5)
        sign = c.m_ellipse(27.5, 15.5, 7, 6) & ~c.m_ellipse(27.5, 15.5, 4.6, 3.8)
        c.fill(sign, "ruin", 2)
        c.fill(c.m_rect(26, 14, 29, 17), "ruin", 2)
    else:
        c.fill(pit, "glow", 2)  # the seam glows round the sunk slab
        slab = c.m_rect(8, 9, 47, 28)
        c.fill(slab, "ruin", 1)
        c.fill(c.m_rect(8, 9, 47, 11) | c.m_rect(8, 9, 10, 28), "ruin", 0)  # the frame's shadow
        sign = c.m_ellipse(28.5, 18.5, 7, 6) & ~c.m_ellipse(28.5, 18.5, 4.6, 3.8)
        c.fill(sign, "glow", 4)
        c.fill(c.m_rect(27, 17, 30, 20), "glow", 5)
        c.fill(c.m_rect(6, 7, 49, 7), "glow", 4)
    darken_right(c, frame | front, 50)
    if season == "winter":
        cap_part(c, c.m_rect(1, 3, 54, 4) & (c.mat == c.mid("ruin")), 2, 3)
    finish(c, keep=("glow",), loose=("snow",))
    return c


# ------------------------------------------------------------------ fence (64 x 48, post 16 x 48)


def fence(season, kind):
    w = 16 if kind == "post" else 64
    c = canvas(w, 48, season)
    G = 47
    pc = (w - 1) / 2
    px0, px1 = int(pc - 5.5), int(pc + 5.5)
    span = {"h": (0, w - 1), "l": (px0, w - 1), "r": (0, px1), "post": None}[kind]
    if span:
        for ry in (15, 31):
            rail = c.m_rect(span[0], ry, span[1], ry + 6)
            c.fill(rail, "plank", 3)
            grain(c, rail, vertical=False, seed=ry)
            c.fill(c.m_rect(span[0], ry, span[1], ry), "plank", 4)
            c.fill(c.m_rect(span[0], ry + 6, span[1], ry + 6), "plank", 1)
            c.fill(c.m_rect(span[0], ry + 5, span[1], ry + 5), "plank", 2)
    post = (c.m_rect(px0, 9, px1, G) | c.m_poly([(px0, 10), (pc + 0.5, 4), (px1 + 1, 10)])) & c.m_rect(0, 3, w - 1, G)
    c.fill(post, "timber", 3)
    cyl(c, post, px0, px1, tones=(4, 4, 3, 3, 3, 2, 1))
    grain(c, post & c.m_rect(0, 11, w - 1, G), vertical=True, seed=1)
    if span:
        for ry in (17, 33):
            c.fill(c.m_rect(int(pc) - 1, ry, int(pc), ry + 1), "iron", 4)
    if season == "winter":
        snow_on(c, ("plank", "timber"), seed=13, depth=(2, 3), mound=1, min_w=3)
    finish(c, keep=("iron",), loose=("snow",))
    return c


# ------------------------------------------------------------------ well (128 x 128)


def well(season):
    c = canvas(128, 128, season)
    G = 126
    cx = 63.5
    # roof posts (behind the stones' front)
    for x0 in (22, 98):
        m = c.m_rect(x0, 26, x0 + 7, 96)
        c.fill(m, "timber", 3)
        cyl(c, m, x0, x0 + 7, tones=(4, 3, 3, 2, 1))
        grain(c, m, vertical=True, seed=x0)
    # windlass: axle, rope, bucket, crank
    ax = c.m_rect(30, 46, 97, 51)
    c.fill(ax, "plank", 3)
    c.fill(c.m_rect(30, 46, 97, 46), "plank", 4)
    c.fill(c.m_rect(30, 51, 97, 51), "plank", 1)
    for x in range(52, 76, 2):
        c.fill(c.m_rect(x, 45, x, 52), "rope", 3 if x % 4 else 2)
    c.fill(c.m_rect(62, 52, 63, 55), "rope", 3)
    c.fill(c.m_rect(63, 52, 63, 55), "rope", 2)
    bucket = c.m_poly([(54, 55), (73, 55), (71, 69), (56, 69)])
    c.fill(bucket, "plank", 3)
    cyl(c, bucket, 53, 74, tones=(4, 3, 3, 2, 1))
    for hy in (57, 65):
        c.fill(c.m_rect(53, hy, 74, hy + 1) & bucket, "iron", 3)
        c.fill(c.m_rect(53, hy, 60, hy) & bucket, "iron", 4)
    c.fill(c.m_ellipse(63.5, 55.5, 9.5, 2.0), "plank", 1)
    c.fill(c.m_line([(55, 56), (63.5, 52), (72, 56)], 1.2) & ~bucket, "iron", 2)
    handle = c.m_line([(106, 48), (114, 48), (114, 60)], 3.0)
    c.fill(handle, "iron", 3)
    c.fill(c.m_rect(112, 58, 116, 63), "plank", 3)
    # the stone wall: the opening (water far down), the rim, the round front
    wallm = c.m_rect(18, 82, 109, 116) | c.m_ellipse(cx, 116, 46, 11)  # round 2: down to row 126
    wallm &= c.m_rect(0, 0, 127, G)
    c.fill(wallm, "stone", 3)
    rng = random.Random(14)
    for row, y in enumerate(range(84, 124, 8)):  # stones that curve round the front
        x = 18 - (row % 2) * 7
        while x < 110:
            w = rng.randint(12, 18)
            xa, xb = max(18, x + 1), min(109, x + w - 1)
            mm = c.m_rect(xa, y + 1, xb, y + 7) & wallm
            c.fill(mm, "stone", rng.choice((3, 3, 2, 4)))
            bevel(c, mm)
            x += w
    c.fill(wallm & (c.tone == 3) & c.m_rect(0, 0, 0, 0), "stone", 3)
    edge = (c.mat == c.mid("stone")) & wallm
    for y, x in zip(*np.nonzero(edge)):  # the round wall: lit left, dark right
        f = (x - 18) / 91
        if f > 0.8 and c.tone[y, x] > 1:
            c.tone[y, x] -= 1
        if f > 0.92 and c.tone[y, x] > 1:
            c.tone[y, x] -= 1
        if f < 0.12 and c.tone[y, x] < 4:
            c.tone[y, x] += 1
    for y in range(84, 124, 8):
        c.fill(c.m_rect(18, y, 109, y) & wallm, "stone", 1)
    rimo = c.m_ellipse(cx, 82, 48, 13)
    rimi = c.m_ellipse(cx, 83, 38, 8.5)
    c.fill(rimo & ~rimi, "stone", 4)
    c.fill(rimo & ~rimi & c.m_rect(0, 83, 127, 127), "stone", 3)
    for a in range(0, 360, 24):  # the rim's cap stones
        r = math.radians(a + 7)
        x, y = cx + math.cos(r) * 43, 82.5 + math.sin(r) * 10.8
        c.fill(c.m_line([(x, y), (cx + math.cos(r) * 38, 83 + math.sin(r) * 8.5)], 1.2) & rimo & ~rimi, "stone", 2)
    c.fill(rimo & ~rimi & c.m_rect(96, 0, 127, 127), "stone", 2)
    hole = rimi
    c.fill(hole, "stone", 1)
    water = c.m_ellipse(cx, 86, 30, 4.5) & hole
    c.fill(water, "water", 2)
    c.fill(water & c.m_rect(0, 0, 54, 84), "water", 4)
    c.fill(c.m_rect(48, 85, 53, 85) & water, "water", 5)
    c.fill(hole & c.m_rect(0, 0, 127, 78), "stone", 2)
    # the roof: plank shingles on a gable seen from the front
    rf = c.m_poly([(4, 34), (124, 34), (100, 8), (28, 8)])
    c.fill(rf, "plank", 3)
    rng2 = random.Random(15)
    for j, ry in enumerate(range(8, 34, 6)):
        x = 4 - rng2.randint(0, 9)
        while x < 124:
            w = rng2.choice((9, 10, 11, 12))
            tm = rf & c.m_rect(x + 1, ry, x + w - 1, ry + 5)
            base = 4 if hsh(x, j, 5) % 4 == 0 else 3
            for yy, xx in zip(*np.nonzero(tm)):
                d = yy - ry
                t = 1 if d == 5 else (base - 1 if d == 4 else base)
                if xx >= x + w - 1:
                    t = max(1, t - 1)
                if xx > cx and t > 1:
                    t -= 1
                c.tone[yy, xx] = t
            x += w
    c.fill(c.m_rect(26, 4, 101, 8), "timber", 4)
    c.fill(c.m_rect(26, 8, 101, 8), "timber", 1)
    c.fill(c.m_rect(64, 4, 101, 7), "timber", 3)
    c.fill(c.m_rect(2, 34, 125, 37), "timber", 2)
    c.fill(c.m_rect(2, 34, 125, 34), "timber", 4)
    if season == "winter":
        roofm = (c.mat == c.mid("plank")) & rf
        roof_snow(c, roofm, 34, cx, 7, eave_y=38, icicle_x=(6, 120))
        snow_on(c, ("timber",), seed=16, depth=(2, 2), mound=2, region=c.m_rect(0, 0, 127, 6))
        snow_on(c, ("stone",), seed=17, depth=(2, 3), mound=0, min_w=4, region=c.m_rect(0, 68, 127, 84) & ~c.m_ellipse(cx, 83, 39, 9.5))
    finish(c, keep=("iron", "water"), loose=("snow",))
    return c


# ------------------------------------------------------------------ signpost (48 x 80)


def signpost(season):
    c = canvas(48, 80, season)
    G = 78
    post = c.m_rect(20, 10, 27, G)
    c.fill(post, "timber", 3)
    cyl(c, post, 20, 27, tones=(4, 3, 3, 2, 1))
    grain(c, post, vertical=True, seed=4)
    c.fill(c.m_rect(18, G - 3, 29, G), "timber", 2)  # the foot driven in
    board = c.m_poly([(3, 16), (37, 16), (45, 27), (37, 38), (3, 38)])
    c.fill(board, "plank", 3)
    for y0 in (16, 27):
        m = board & c.m_rect(0, y0, 47, y0 + 10)
        c.fill(m, "plank", 3 if y0 == 16 else 2)
        grain(c, m, vertical=False, seed=y0)
    c.fill(board & c.m_rect(0, 27, 47, 27), "plank", 1)
    bevel(c, board)
    for (x0, x1, y) in ((8, 24, 21), (8, 30, 31), (27, 31, 21)):  # carved strokes (a name, unreadable)
        c.fill(c.m_rect(x0, y, x1, y + 1), "plank", 1)
        c.fill(c.m_rect(x0, y + 2, x1, y + 2), "plank", 4)
    for nx, ny in ((6, 19), (6, 34), (34, 19), (34, 34)):
        c.fill(c.m_rect(nx, ny, nx + 1, ny + 1), "iron", 4)
    cap = c.m_poly([(17, 11), (30, 11), (26, 5), (21, 5)])
    c.fill(cap, "timber", 4)
    c.fill(c.m_rect(17, 11, 30, 11), "timber", 1)
    if season == "winter":
        # round 2: snow only along the board's flat top and the cap (none heaped on the arrow's slope)
        snow_on(c, ("plank", "timber"), seed=18, depth=(2, 3), mound=1, min_w=3, region=c.m_rect(0, 0, 36, 17))
    finish(c, keep=("iron",), loose=("snow",))
    return c


# ------------------------------------------------------------------ the list


ITEMS = [  # key, function(season) -> Canvas, seasons drawn (others fall back to summer)
    ("obj.house", house, ("summer", "autumn", "winter")),
    ("obj.v3.house_stone", house_stone, ("summer", "autumn", "winter")),  # summer replaces the pilot's (round 3)
    ("obj.chest.closed", lambda s: chest(s, False), ("summer", "winter")),
    ("obj.chest.open", lambda s: chest(s, True), ("summer",)),  # winter: no snow on it, the summer file
    ("obj.barrel", barrel, ("summer", "winter")),
    ("obj.crate", crate, ("summer", "winter")),
    ("obj.jar", jar, ("summer", "winter")),
    ("obj.campfire.0", lambda s: campfire(s, 0), ("summer", "winter")),
    ("obj.campfire.1", lambda s: campfire(s, 1), ("summer", "winter")),
    ("obj.brazier.0", lambda s: brazier(s, 0), ("summer", "winter")),
    ("obj.brazier.1", lambda s: brazier(s, 1), ("summer", "winter")),
    ("obj.checkpoint.off", lambda s: checkpoint(s, False), ("summer", "winter")),
    ("obj.checkpoint.on", lambda s: checkpoint(s, True), ("summer", "winter")),
    ("sw.plate.off", lambda s: plate(s, False), ("summer", "winter")),
    ("sw.plate.on", lambda s: plate(s, True), ("summer", "winter")),
    ("obj.v3.fence.h", lambda s: fence(s, "h"), ("summer", "winter")),
    ("obj.v3.fence.l", lambda s: fence(s, "l"), ("summer", "winter")),
    ("obj.v3.fence.r", lambda s: fence(s, "r"), ("summer", "winter")),
    ("obj.v3.fence.post", lambda s: fence(s, "post"), ("summer", "winter")),
    ("obj.v3.well", well, ("summer", "winter")),
    ("obj.v3.signpost", signpost, ("summer", "winter")),
]
HOUSES = {"obj.house": (HOUSE_W, HOUSE_H), "obj.v3.house_stone": (HS.W, HS.H)}


def windows_of(img, key):
    """The glass of a house: each window's rectangle (game px from the feet, 4 texels per game px),
    the lit texels (glass_kind 1 / 2) and the texels inside the rectangles that are NOT window glass
    by material but would light (must be 0)."""
    a = np.array(img.convert("RGBA")).astype(int)
    h, w = a.shape[:2]
    lit = np.zeros((h, w), np.int8)
    for y in range(h):
        for x in range(w):
            lit[y, x] = glass_kind(*a[y, x])
    return lit


def write(season):
    out = []
    for key, fn, seasons in ITEMS:
        if season not in seasons:
            continue
        c = fn(season)
        img = c.image() if key == "obj.v3.house_stone" else clean_isolated(c.image())
        p = save(img, os.path.join(OUT, f"{PREFIX[season]}{key}.png"))
        out.append((key, season, c, img, p))
    return out


def glass_table(results):
    """Windows of the houses from the canvases (material 'glass' components) -> village_windows.json."""
    table = {}
    for key, season, c, img, p in results:
        if key not in HOUSES:
            continue
        gm = c.mat == c.mid("glass")
        a = np.array(img.convert("RGBA")).astype(int)
        lit = np.array([[glass_kind(*a[y, x]) for x in range(c.w)] for y in range(c.h)])
        # glass components = windows
        seen = np.zeros_like(gm)
        wins = []
        for y in range(c.h):
            for x in range(c.w):
                if gm[y, x] and not seen[y, x]:
                    st, comp = [(y, x)], []
                    seen[y, x] = True
                    while st:
                        q = st.pop()
                        comp.append(q)
                        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            Y, X = q[0] + dy, q[1] + dx
                            if 0 <= Y < c.h and 0 <= X < c.w and gm[Y, X] and not seen[Y, X]:
                                seen[Y, X] = True
                                st.append((Y, X))
                    if len(comp) >= 20:
                        ys, xs = zip(*comp)
                        wins.append((min(xs), min(ys), max(xs), max(ys)))
        # merge panes split by mullions into one window (rects that touch within 4 texels)
        merged = True
        while merged:
            merged = False
            for i in range(len(wins)):
                for j in range(i + 1, len(wins)):
                    A, B = wins[i], wins[j]
                    if A[0] - 4 <= B[2] and B[0] - 4 <= A[2] and A[1] - 4 <= B[3] and B[1] - 4 <= A[3]:
                        wins[i] = (min(A[0], B[0]), min(A[1], B[1]), max(A[2], B[2]), max(A[3], B[3]))
                        del wins[j]
                        merged = True
                        break
                if merged:
                    break
        rows = []
        for x0, y0, x1, y1 in sorted(wins, key=lambda r: (r[1], r[0])):
            rect = np.zeros((c.h, c.w), bool)
            rect[y0:y1 + 1, x0:x1 + 1] = True
            n_lit = int(((lit > 0) & rect).sum())
            n_glass = int((gm & rect).sum())
            stray = int(((lit > 0) & rect & ~gm).sum())
            glints = int((gm & rect & (lit == 0)).sum())
            rows.append(dict(art=[x0, y0, x1 - x0 + 1, y1 - y0 + 1],
                             game=[(x0 - c.w / 2) / 4, (y0 - c.h) / 4, (x1 - x0 + 1) / 4, (y1 - y0 + 1) / 4],
                             glass=n_glass, lit=n_lit, glints_unlit=glints, lit_not_glass=stray))
        outside = int(((lit > 0) & ~np.any([np.pad(np.ones((r['art'][3], r['art'][2]), bool),
                                                     ((r['art'][1], c.h - r['art'][1] - r['art'][3]),
                                                      (r['art'][0], c.w - r['art'][0] - r['art'][2])))
                                              for r in rows], axis=0)).sum())
        table[f"{PREFIX[season]}{key}"] = dict(size=[c.w, c.h], game_size=[c.w / 4, c.h / 4], windows=rows,
                                               lit_like_outside_windows=outside)
    return table


def main(which):
    seasons = list(PREFIX) if which == "all" else [which]
    res = []
    for s in seasons:
        res += write(s)
    # round 3 (coordinator's decision): the stone house's summer file is this script's drawing (short
    # glints, the chimney cap inside the picture). Check the pilot's own steps still give the pilot's
    # picture (gfx/v3-art 814aa23), so the seasons are the pilot's house plus only those changes.
    import io
    import subprocess
    from PIL import Image
    try:
        blob = subprocess.run(["git", "-C", ROOT, "show", "814aa23:src/art-release-v3/objects/obj.v3.house_stone.png"],
                              capture_output=True, check=True).stdout
        pilot = np.array(Image.open(io.BytesIO(blob)).convert("RGBA"))
        print("pilot steps (pilot_drawing=True) == the pilot picture of 814aa23:",
              np.array_equal(pilot, house_stone("summer", pilot_drawing=True).rgba()))
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("814aa23 not in this checkout: pilot check skipped")
    if which == "all":
        tab = glass_table(res)
        old = {}
        os.makedirs(os.path.dirname(DOC), exist_ok=True)
        with open(DOC, "w") as f:
            json.dump(dict(note="Night windows of the v3 village houses (gen_village_v3.py). art: [x, y, w, h] in "
                                "texels from the image's top left; game: [x, y, w, h] in game px from the feet "
                                "(bottom centre), 4 texels per game px. lit = texels houseWindows.glassKind lights; "
                                "glints_unlit = glass texels left as drawn (tones 4-5); lit_not_glass must be 0.",
                           **old, houses=tab), f, indent=1)
        print(os.path.relpath(DOC, ROOT))
    print(f"{sum(1 for r in res if r[4])} files")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "all")
