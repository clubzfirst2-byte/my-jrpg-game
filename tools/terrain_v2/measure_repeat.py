"""The 32-px repeat measure of the W1 inspection (gfx_r1/ins/work/period.py), on large fields of every ground
drawn by render_ref (40 x 24 cells): mean |L(x) - L(x + s)| over both axes, for s = 24 and 32. A ground
that repeats every 32 px has a much smaller difference at 32 than at 24; the target is ratio 32/24 >= 0.8.
Round 3 adds the banding measure: the autocorrelation at 32 px of the row means and of the column means
(horizontal / vertical stripes every tile); target <= 0.3.

Run: python3 tools/terrain_v2/measure_repeat.py   (after gen_v2.py; also called by gen_v2.py for check.txt)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))


def lum(im):
    px = list(im.convert("RGB").get_flattened_data())
    w, h = im.size
    return [[0.299 * r + 0.587 * g + 0.114 * b for r, g, b in px[y * w:(y + 1) * w]] for y in range(h)]


def diff(L, s):
    h, w = len(L), len(L[0])
    a = sum(abs(L[y][x + s] - L[y][x]) for y in range(h) for x in range(w - s)) / (h * (w - s))
    b = sum(abs(L[y + s][x] - L[y][x]) for y in range(h - s) for x in range(w)) / ((h - s) * w)
    return a + b


def autocorr(profile, lag=32):
    """Normalised autocorrelation of a 1-D brightness profile at a lag (1 = repeats exactly, 0 = unrelated)."""
    n = len(profile)
    m = sum(profile) / n
    d = [v - m for v in profile]
    var = sum(v * v for v in d)
    if var == 0:
        return 0.0
    return (sum(d[i] * d[i + lag] for i in range(n - lag)) / (n - lag)) / (var / n)


def row_col(L, lag=32):
    """The inspection's banding measure: autocorrelation at 32 px of the row means and of the column means."""
    rows = [sum(r) / len(r) for r in L]
    cols = [sum(L[y][x] for y in range(len(L))) / len(L) for x in range(len(L[0]))]
    return autocorr(rows, lag), autocorr(cols, lag)


def measure(images, season=None, grounds="gplmnsd=u", cells=(40, 24)):
    from render_ref import render_v2

    out = {}
    for ch in grounds:
        grid = [ch * cells[0] for _ in range(cells[1])]
        L = lum(render_v2(grid, images, season=season))
        d24, d32 = diff(L, 24), diff(L, 32)
        rc = row_col(L)
        out[ch] = (d24, d32, d32 / d24 if d24 else 1.0, rc[0], rc[1])
    return out


if __name__ == "__main__":
    from PIL import Image
    import gen_v2

    imgs = {k: c.image() for k, c in gen_v2.build().items()}
    v1 = os.path.join(gen_v2.ROOT, "src", "art-release", "terrain")
    for k in ("tile.metal", "tile.walltop", "tile.wood", "tile.dark", "tile.pit"):
        imgs["v1:" + k] = Image.open(os.path.join(v1, k + ".png")).convert("RGBA")
    for season in (None, "autumn", "winter"):
        res = measure(imgs, season, "gplmnsd=u" if season is None else "gplm")
        print(season or "summer", " ".join(f"{k}:{r[2]:.2f}/{r[3]:.2f}/{r[4]:.2f}" for k, r in res.items()))
