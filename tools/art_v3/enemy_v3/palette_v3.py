"""v3 enemy palette: the v2 ramps (rig.RGBV3) with each kind's body darkened so the enemy stands
apart from the v3 ground by brightness (STYLE 5.4: mean luma of the body at least 25 under the
summer grass, 92.8; the pilot slime is 61.6). Light materials (glow, eye, spark, ice) keep their
colours. Tone 0 is lifted again to luma >= 30 after the darkening (never near-black)."""

from rig import MID, RGBV3, _lift

LIGHT_MATS = {"glow", "eye", "spark", "ice"}
# round 2 (inspection): the factor depends on the TONE -- the shadow and core tones (indices 0-3 of
# the 7-step ramp: outline, shadow, 1.5, core) go down, the light tones (2.5, light, highlight) stay
# near v2, so the light-to-dark range is kept (the sentinel's pale ruin stone stays pale on its lit
# faces) and the mean still sits 25 or more under the summer grass.
VALUE = {  # per kind: factors for the ramp indices 0..6
    "beast": (0.80, 0.70, 0.74, 0.80, 0.92, 1.0, 1.0),
    "archer": (0.80, 0.66, 0.70, 0.76, 0.90, 1.0, 1.0),
    "sentinel": (0.80, 0.58, 0.60, 0.70, 0.92, 1.0, 1.0),
}


# round 3 (inspection): per MATERIAL where one kind mixes a pale and a dark material. The sentinel's
# ruin stone keeps v2's pale faces (its core tone stays at v2, its shadow goes down); the darkness
# against the ground comes from its bronze and leather and from the stone's shadow side.
VALUE_MAT = {
    "sentinel": {
        "oldstone": (0.80, 0.88, 0.92, 1.0, 1.0, 1.0, 1.0),
        "oldstone_w": (0.80, 0.88, 0.92, 1.0, 1.0, 1.0, 1.0),
        "moss": (0.80, 0.70, 0.74, 0.86, 0.95, 1.0, 1.0),
        "bronze": (0.80, 0.36, 0.40, 0.46, 0.60, 0.76, 0.90),
        "leather": (0.80, 0.36, 0.40, 0.46, 0.60, 0.76, 0.90),
    },
}


def ramps_for(kind):
    fs0 = VALUE.get(kind)
    out = {}
    for m, r in RGBV3.items():
        fs = VALUE_MAT.get(kind, {}).get(m, fs0)
        if m in LIGHT_MATS or fs is None:
            out[m] = [tuple(int(v) for v in c) for c in r]
        else:
            sc = [tuple(min(255, int(v * fs[i] + 0.5)) for v in c) for i, c in enumerate(r)]
            out[m] = [_lift(sc[0])] + sc[1:]
    return out


def reverse(ramps):
    rev = {}
    for m, r in ramps.items():
        for i, c in enumerate(r):
            rev.setdefault(tuple(c), (m, i))
    return rev


BODY = {"ashfur", "ashfur_d", "ashfur_p", "plum", "plum_d", "patch", "gobskin", "leather", "wood", "oldstone",
        "oldstone_w", "moss", "bronze"}


def _clean_isolated(lab, names, dst, passes=2):
    """Round 3: a body-material cluster of 1-2 texels of one colour, all its outside neighbours opaque
    and its luma 12+ away from theirs (the inspection's 'isolated point'), takes the commonest colour
    around it. Eyes, glints, glow, fangs (bone) and the murk are left alone."""
    import numpy as np
    H, W = lab.shape

    def L(code):
        c = dst[names[code // 16]][code % 16]
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    for _ in range(passes):
        seen = np.zeros((H, W), bool)
        changes = []
        for y in range(H):
            for x in range(W):
                c = lab[y, x]
                if c < 0 or seen[y, x] or names[c // 16] not in BODY:
                    continue
                comp, st = [(y, x)], [(y, x)]
                seen[y, x] = True
                while st and len(comp) <= 2:
                    a, b = st.pop()
                    for p_, q_ in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                        if 0 <= p_ < H and 0 <= q_ < W and not seen[p_, q_] and lab[p_, q_] == c:
                            seen[p_, q_] = True
                            comp.append((p_, q_))
                            st.append((p_, q_))
                if len(comp) > 2:
                    continue
                cs = set(comp)
                nb = []
                ok = True
                for a, b in comp:
                    for p_, q_ in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                        if (p_, q_) in cs:
                            continue
                        if not (0 <= p_ < H and 0 <= q_ < W) or lab[p_, q_] < 0:
                            ok = False
                        else:
                            nb.append(int(lab[p_, q_]))
                if not ok or not nb:
                    continue
                if abs(sum(L(v) for v in nb) / len(nb) - L(c)) < 12:
                    continue
                best = max(set(nb), key=lambda v: (nb.count(v), -L(v)))
                if names[best // 16] not in BODY:
                    continue
                changes += [(a, b, best) for a, b in comp]
        if not changes:
            break
        for a, b, v in changes:
            lab[a, b] = v


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
    _clean_isolated(lab, list(dst), dst)
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
