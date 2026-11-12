"""v3 enemy palette: the v2 ramps (rig.RGBV3) with each kind's body darkened so the enemy stands
apart from the v3 ground by brightness (STYLE 5.4: mean luma of the body at least 25 under the
summer grass, 92.8; the pilot slime is 61.6). Light materials (glow, eye, spark, ice) keep their
colours. Tone 0 is lifted again to luma >= 30 after the darkening (never near-black)."""

from rig import MID, RGBV3, _lift

LIGHT_MATS = {"glow", "eye", "spark", "ice"}
VALUE = {"beast": 0.88, "archer": 0.84, "sentinel": 0.72}  # body value per kind (1 = v2's)


def ramps_for(kind):
    f = VALUE.get(kind, 1.0)
    out = {}
    for m, r in RGBV3.items():
        if m in LIGHT_MATS or f == 1.0:
            out[m] = [tuple(int(v) for v in c) for c in r]
        else:
            sc = [tuple(min(255, int(v * f + 0.5)) for v in c) for c in r]
            out[m] = [_lift(sc[0])] + sc[1:]
    return out


def reverse(ramps):
    rev = {}
    for m, r in ramps.items():
        for i, c in enumerate(r):
            rev.setdefault(tuple(c), (m, i))
    return rev


def recolour(a, kind):
    """The rig's image (RGBV3 colours) -> this kind's colours, and the in-between tones kept only
    inside a 3 x 3 block of themselves (a last pass after the melt / stamps)."""
    import numpy as np
    src = reverse({m: [tuple(int(v) for v in c) for c in r] for m, r in RGBV3.items()})
    dst = ramps_for(kind)
    out = a.copy()
    H, W = a.shape[:2]
    lab = np.full((H, W), -1)
    names = {m: i for i, m in enumerate(dst)}
    for y, x in zip(*np.nonzero(a[..., 3] == 255)):
        m, i = src.get(tuple(int(v) for v in a[y, x, :3]), (None, 0))
        if m is None:
            continue
        lab[y, x] = names[m] * 16 + i
    for y, x in zip(*np.nonzero(lab >= 0)):
        code = lab[y, x]
        m, i = list(dst)[code // 16], code % 16
        if i in MID:
            ok = any((lab[y0:y0 + 3, x0:x0 + 3] == code).all()
                     for y0 in range(max(0, y - 2), min(H - 2, y + 1)) for x0 in range(max(0, x - 2), min(W - 2, x + 1)))
            if not ok:
                i -= 1
        out[y, x, :3] = dst[m][i]
    return out
