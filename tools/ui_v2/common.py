"""Shared helpers for the v2 UI art (W4: title, buttons, menus in the game's pixel style).

Density (docs/art-release-v2/ui/PRODUCTION.md):
  * HUD, buttons, menus: 1 art px = 1 CSS px  (= 3 device px on iPhone 15 Pro (DPR 3), 2 on SE (DPR 2)),
    the same density as the item icons the menus already show. Always an integer number of device px.
  * Title screen (logo + background): 1 art px = 2 CSS px (6 / 4 device px).
Colours come from the guide's ramps (gem blue and gold for 星環, the world's stone, leaf, sand, wood) plus
UI ramps defined here (navy panel, sky). Light from the top left, as in the world. UI is not world art:
semi-transparent fills are allowed (HUD glass, panel fills); rims and icons stay opaque.
"""

import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "art_proto"))
sys.path.insert(0, os.path.join(HERE, "..", "object_release"))
from pixel import BASE_RAMPS, hx  # noqa: E402
from draw import RAMPS  # noqa: E402
from ramps2 import RAMPS2  # noqa: E402

WORLD = {**BASE_RAMPS, **RAMPS, **RAMPS2}
UI = {
    # the panel navy: the current --panel colour family, deepened into a 5-tone ramp
    "navy": ["#05080e", "#0b121d", "#142033", "#1f3150", "#2f4a72"],
    # the title sky (dusk over the sea): deep blue -> violet -> warm horizon
    "sky": ["#0b1230", "#18225a", "#2c3a86", "#5a5aa8", "#9a7ab8"],
    "dusk": ["#5a3a6a", "#9a5a72", "#d8806a", "#f2b07a", "#ffe2a8"],
    "sea": ["#06142c", "#0c2a52", "#16467a", "#2a6aa2", "#6aa8d8"],
}
R = {k: [hx(c) for c in v] for k, v in {**WORLD, **UI}.items()}


def col(mat, tone, a=255):
    r, g, b = R[mat][tone]
    return (r, g, b, a)


def new(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def put(im, x, y, c):
    if 0 <= x < im.width and 0 <= y < im.height:
        im.putpixel((x, y), c)


def get(im, x, y):
    if 0 <= x < im.width and 0 <= y < im.height:
        return im.getpixel((x, y))
    return (0, 0, 0, 0)


def outline(im, c, diagonal=False):
    """Add a 1 px outline of colour c around every opaque-ish pixel (on clear pixels only)."""
    w, h = im.size
    src = im.copy()
    nb = [(1, 0), (-1, 0), (0, 1), (0, -1)] + ([(1, 1), (-1, -1), (1, -1), (-1, 1)] if diagonal else [])
    for y in range(h):
        for x in range(w):
            if src.getpixel((x, y))[3] != 0:
                continue
            if any(get(src, x + dx, y + dy)[3] != 0 for dx, dy in nb):
                im.putpixel((x, y), c)
    return im


def mask_from(im):
    w, h = im.size
    return [[im.getpixel((x, y))[3] != 0 for x in range(w)] for y in range(h)]


def rounded_rect_mask(w, h, r):
    """A pixel rounded rectangle: corners cut on a stair of radius r (no anti-aliasing)."""
    m = [[True] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            cx = r - 0.5 if x < r else (w - r - 0.5 if x >= w - r else None)
            cy = r - 0.5 if y < r else (h - r - 0.5 if y >= h - r else None)
            if cx is not None and cy is not None:
                if (x - cx) ** 2 + (y - cy) ** 2 > (r - 0.15) ** 2:
                    m[y][x] = False
    return m


def edge_dist(mask):
    """4-neighbour distance from each inside pixel to the outside (1 on the edge)."""
    h, w = len(mask), len(mask[0])
    INF = 10 ** 6
    d = [[INF if mask[y][x] else 0 for x in range(w)] for y in range(h)]
    changed = True
    while changed:
        changed = False
        for y in range(h):
            for x in range(w):
                if d[y][x] == 0:
                    continue
                best = min(d[y - 1][x] if y > 0 else 0, d[y + 1][x] if y < h - 1 else 0,
                           d[y][x - 1] if x > 0 else 0, d[y][x + 1] if x < w - 1 else 0) + 1
                if best < d[y][x]:
                    d[y][x] = best
                    changed = True
    return d


def side(mask, x, y):
    """'tl' if the pixel faces the light (an edge above or to the left), 'br' if it faces away."""
    h, w = len(mask), len(mask[0])

    def out(xx, yy):
        return not (0 <= xx < w and 0 <= yy < h and mask[yy][xx])

    up_left = out(x, y - 1) or out(x - 1, y)
    down_right = out(x, y + 1) or out(x + 1, y)
    if up_left and not down_right:
        return "tl"
    if down_right and not up_left:
        return "br"
    return "mid"


def save(im, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path, optimize=True)


def nine_slice(src, w, h, inset, scale=1):
    """Stretch a 9-slice image to w x h (CSS border-image with `round`/`stretch`: here, the edges and the
    centre are tiled, as CSS `border-image-repeat: round` would do for the pixel patterns)."""
    l, t, r, b = inset if isinstance(inset, (tuple, list)) else (inset,) * 4
    sw, sh = src.size
    out = new(w, h)
    cw, ch = sw - l - r, sh - t - b

    def tile(box, dx0, dy0, dw, dh):
        piece = src.crop(box)
        pw, ph = piece.size
        if pw <= 0 or ph <= 0:
            return
        for yy in range(dy0, dy0 + dh, ph):
            for xx in range(dx0, dx0 + dw, pw):
                cut = piece.crop((0, 0, min(pw, dx0 + dw - xx), min(ph, dy0 + dh - yy)))
                out.alpha_composite(cut, (xx, yy))

    tile((0, 0, l, t), 0, 0, l, t)
    tile((sw - r, 0, sw, t), w - r, 0, r, t)
    tile((0, sh - b, l, sh), 0, h - b, l, b)
    tile((sw - r, sh - b, sw, sh), w - r, h - b, r, b)
    tile((l, 0, l + cw, t), l, 0, w - l - r, t)
    tile((l, sh - b, l + cw, sh), l, h - b, w - l - r, b)
    tile((0, t, l, t + ch), 0, t, l, h - t - b)
    tile((sw - r, t, sw, t + ch), w - r, t, r, h - t - b)
    tile((l, t, l + cw, t + ch), l, t, w - l - r, h - t - b)
    if scale != 1:
        out = out.resize((w * scale, h * scale), Image.NEAREST)
    return out
