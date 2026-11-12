"""Frame effects applied to a drawn frame: the defeat DISSOLVE (v3 copy of tools/enemy_v2/fx.py).

v3: works on the texel image (numpy RGBA, density 4) with the v3 ramps (rig.RGBV3). The last pose
melts: the body sinks and spreads (squashed toward the ground line, anchored at its feet), its lower
part turns into murk (the same tone index of the murk ramp, so the shading is kept), a murk pool 2
texel rows high spreads under it; the outline is re-made from each material's tone 0; an in-between
tone is kept only inside a K_MID x K_MID block of itself. The glow is not recoloured.
"""

import numpy as np

from rig import K_MID, MID, RGBV3, S

REV = {}
for _m, _r in RGBV3.items():
    for _i, _c in enumerate(_r):
        REV.setdefault(tuple(_c), (_m, _i))


def melt(img, squash, murk, pool):
    h, w = img.shape[:2]
    op = img[..., 3] > 0
    if not op.any():
        return img
    ys, xs = np.nonzero(op)
    g, top, cx = ys.max(), ys.min(), xs.mean()
    spread = 1 + (1 - squash) * 0.35
    out = np.zeros_like(img)
    for y in range(h):
        for x in range(w):
            iy = int(round(g - (g - y) / squash))
            ix = int(round(cx + (x - cx) / spread))
            if top <= iy <= g and 0 <= ix < w:
                out[y, x] = img[iy, ix]
    ops = np.nonzero(out[..., 3] > 0)[0]
    lab = {}
    if len(ops):
        line = g - (g - ops.min()) * murk
        for y in range(h):
            if y < line:
                continue
            for x in range(w):
                if out[y, x, 3]:
                    m, i = REV.get(tuple(int(v) for v in out[y, x, :3]), (None, 0))
                    if m and m != "glow":
                        out[y, x, :3] = RGBV3["murk"][i]
    pw = int(round(pool * S))
    for x in range(int(round(cx - pw)), int(round(cx + pw)) + 1):
        if 0 <= x < w:
            for y, i in ((g - 3, 3), (g - 2, 3), (g - 1, 1), (g, 1)):
                if 0 <= y < h and not out[y, x, 3]:
                    out[y, x, :3] = RGBV3["murk"][i]
                    out[y, x, 3] = 255
    # round 2: no 1-texel-high streaks (a row of texels with nothing above or below it)
    for _ in range(2):
        op_ = out[..., 3] > 0
        up_ = np.zeros_like(op_)
        up_[1:] = op_[:-1]
        dn_ = np.zeros_like(op_)
        dn_[:-1] = op_[1:]
        thin = op_ & ~up_ & ~dn_
        out[thin] = 0
    res = out.copy()
    for y in range(h):
        for x in range(w):
            if not out[y, x, 3]:
                continue
            edge = any(not (0 <= x + dx < w and 0 <= y + dy < h) or not out[y + dy, x + dx, 3] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if edge:
                m, i = REV.get(tuple(int(v) for v in out[y, x, :3]), ("murk", 0))
                res[y, x, :3] = RGBV3[m][0]
    fin = res.copy()
    k = K_MID
    for y in range(h):
        for x in range(w):
            if not res[y, x, 3]:
                continue
            c = tuple(int(v) for v in res[y, x, :3])
            m, i = REV.get(c, (None, 0))
            if i not in MID:
                continue
            ok = False
            for oy in range(-k + 1, 1):
                for ox in range(-k + 1, 1):
                    y0, x0 = y + oy, x + ox
                    if y0 >= 0 and x0 >= 0 and y0 + k <= h and x0 + k <= w and \
                            (res[y0:y0 + k, x0:x0 + k, :3] == res[y, x, :3]).all() and (res[y0:y0 + k, x0:x0 + k, 3] > 0).all():
                        ok = True
                        break
                if ok:
                    break
            if not ok:
                fin[y, x, :3] = RGBV3[m][i - 1]
    return fin


class FX:
    def __init__(self, rig, squash, murk, pool):
        self.rig, self.squash, self.murk, self.pool = rig, squash, murk, pool

    def image(self, outline=True):
        return melt(self.rig.image(outline=outline), self.squash, self.murk, self.pool)
