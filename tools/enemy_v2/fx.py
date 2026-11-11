"""Frame effects applied to a drawn frame (round 2): the defeat DISSOLVE.

A defeat used to hold a pose and then pop to the fallen shape in one frame. Now the last pose
melts over the frames: the body sinks and spreads (squashed toward the ground line, anchored at
its feet), its lower part turns into murk (the same tone index of the murk ramp, so the shading
is kept), a murk pool spreads under it; the outline is re-made from each material's tone 0.
The glow (cores, eyes, crystals) is not recoloured -- it is the last thing to go out.

  FX(rig, squash, murk, pool): a frame whose image() is rig.image() melted.
"""

from rig import RGB8, MID

REV = {}
for _m, _r in RGB8.items():
    for _i, _c in enumerate(_r):
        REV.setdefault(_c, (_m, _i))


def melt(rows, squash, murk, pool):
    h, w = len(rows), len(rows[0])
    op = [(x, y) for y in range(h) for x in range(w) if rows[y][x]]
    if not op:
        return rows
    g = max(y for _, y in op)
    top = min(y for _, y in op)
    cx = sum(x for x, _ in op) / len(op)
    spread = 1 + (1 - squash) * 0.35
    out = [[None] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            sy = g - (g - y) / squash
            sx = cx + (x - cx) / spread
            iy, ix = int(round(sy)), int(round(sx))
            if 0 <= iy <= g and 0 <= ix < w and iy >= top:
                out[y][x] = rows[iy][ix]
    # the lower part of what is left turns into murk (same tone index)
    ops = [y for y in range(h) for x in range(w) if out[y][x]]
    if ops:
        t2 = min(ops)
        line = g - (g - t2) * murk
        for y in range(h):
            if y < line:
                continue
            for x in range(w):
                c = out[y][x]
                if c:
                    m, i = REV.get(c[:3], (None, 0))
                    if m and m != "glow":
                        out[y][x] = RGB8["murk"][i] + (255,)
    # a murk pool spreading on the ground line
    pw = int(round(pool))
    for x in range(int(round(cx - pw)), int(round(cx + pw)) + 1):
        if 0 <= x < w:
            for y, i in ((g - 1, 3), (g, 1)):
                if 0 <= y < h and not out[y][x]:
                    out[y][x] = RGB8["murk"][i] + (255,)
    # the outline: an edge pixel takes its material's tone 0
    res = [r[:] for r in out]
    for y in range(h):
        for x in range(w):
            c = out[y][x]
            if not c:
                continue
            edge = any(not (0 <= x + dx < w and 0 <= y + dy < h) or not out[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if edge:
                m, i = REV.get(c[:3], ("murk", 0))
                res[y][x] = RGB8[m][0] + (255,)
    # the in-between tones only in 2x2 clusters (as Rig.image): a lone one drops a step
    fin = [r[:] for r in res]
    for y in range(h):
        for x in range(w):
            c = res[y][x]
            if not c:
                continue
            m, i = REV.get(c[:3], (None, 0))
            if i not in MID:
                continue
            ok = any(all(0 <= x + ox + dx < w and 0 <= y + oy + dy < h and res[y + oy + dy][x + ox + dx] == c for dx in (0, 1) for dy in (0, 1))
                     for ox, oy in ((0, 0), (-1, 0), (0, -1), (-1, -1)))
            if not ok:
                fin[y][x] = RGB8[m][i - 1] + (255,)
    return fin


class FX:
    def __init__(self, rig, squash, murk, pool):
        self.rig, self.squash, self.murk, self.pool = rig, squash, murk, pool

    def image(self, outline=True):
        return melt(self.rig.image(outline=outline), self.squash, self.murk, self.pool)
