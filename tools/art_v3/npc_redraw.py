"""v3 NPC production, round 3: each villager frame is redrawn at the texel, with the approved v1 frame only as
the underdrawing (its parts, held things and motion) — the hero's way of working.

The round-2 frames were judged "v1 doubled with Scale2x and repainted": their edges sat on v1's 2-texel grid
(inspection: shifted/aligned 2x2 ratio 0.53-0.72, 56-71 % of colour edges on v1's grid lines) and their
faces were v1's inks doubled. Round 3, per frame:
  1. the underdrawing: v1's frame read as parts (material + v1 tone) and face marks (lash, iris, brow,
     mouth, cheek, stubble... per person, from the v1 tools' legends);
  2. the shapes redrawn at the texel: every part's outline is drawn again from the underdrawing as a soft
     shape (bilinear) whose edge wanders by up to one texel along its length (a smooth hand-drawn wobble),
     so no edge keeps v1's 2-texel steps; holes inside the figure are closed;
  3. the shading redrawn at the texel: v1's tones as a soft field, the part's volume lit from the top left
     (not on skin: skin keeps v1's flat faces, only the hair's shade and the jaw), and the v3 middle shade;
     the band edges fall between v1's grid lines;
  4. the face drawn again at 2x detail: each eye is an 8 x 6 (front) eye — the lash line thicker at the
     outer end, an iris in 3 tones (dark top, middle, light bottom), a 2-texel pupil and a shine texel;
     closed eyes (the elder's, the merchant's) are a curved lid line; brows a tapered 2-row band; the mouth
     redrawn at its double width with its corners; stubble as single dots; cheeks soft;
  5. the v3 outline (v1's values) and the shadow-side band.
"""

import hashlib
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from v3lib import Canvas, despeckle, dome_light, ramp6, smooth_lone  # noqa: E402
import npc_v1map as M  # noqa: E402  (the v1 ramps and paths)

FACE = {  # v1 face colours by role, per person (tools/npc_release/<who>.py legends, read only)
    "woman": {"#2a1a18": "lash", "#6a3a10": "iris_d", "#c07a2a": "iris", "#fff8ec": "shine", "#b04a46": "mouth",
              "#f4a08e": "blush", "#c47a52": "freckle"},
    "princess": {"#26223e": "lash", "#24206a": "iris_d", "#4436a8": "iris", "#4c9ee6": "iris_l", "#9ad6ff": "iris_l",
                 "#ffffff": "shine", "#dcd6e4": "white", "#8a8aa8": "brow", "#b8585a": "mouth", "#f6aa98": "blush"},
    "smith": {"#3a1408": "brow", "#24160e": "lash", "#3e2a1a": "iris", "#7a3a2c": "mouth", "#6e6460": "soot"},
    "child": {"#2a2030": "lash", "#1e5a32": "iris_d", "#3e9a5a": "iris", "#f4fff8": "shine", "#b0504a": "mouth",
              "#f6a090": "blush"},
    "cook": {"#3e2414": "brow", "#2a1a14": "lash", "#3a2418": "iris", "#8a3a34": "mouth", "#e8806a": "blush"},
    "elder": {"#3a2620": "lash", "#8a4a40": "mouth", "#ee9c8c": "blush"},
    "guard": {"#2a1a12": "brow", "#1e1820": "lash", "#5a7a4a": "iris", "#2e4428": "iris_d", "#7a3c34": "mouth",
              "#a8806a": "stub"},
    "merchant": {"#24202a": "brow", "#2a2230": "lash", "#9a4a42": "mouth", "#f0a08c": "blush", "#f4fbff": "glint"},
    "traveller": {"#2a1a14": "lash", "#6e9a84": "iris", "#83492c": "line", "#7a3a2a": "mouth"},
}
EYE_ROLES = {"lash", "iris", "iris_d", "iris_l", "shine", "white"}


def _hx(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


def _hex(rgb):
    return "#%02x%02x%02x" % tuple(int(v) for v in rgb)


def _noise(h, w, seed, period=6.0):
    """Smooth value noise in [-1, 1] (a fixed grid of hashed values, bilinear between them)."""
    gh, gw = int(h / period) + 3, int(w / period) + 3
    g = np.zeros((gh, gw))
    for y in range(gh):
        for x in range(gw):
            v = int(hashlib.md5(f"{seed}:{x}:{y}".encode()).hexdigest()[:8], 16)
            g[y, x] = v / 0xFFFFFFFF * 2 - 1
    yy, xx = np.mgrid[0:h, 0:w] / period
    x0, y0 = xx.astype(int), yy.astype(int)
    fx, fy = xx - x0, yy - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = g[y0, x0], g[y0, x0 + 1]
    c, d = g[y0 + 1, x0], g[y0 + 1, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


OFF = 0.25  # the redraw is laid half a texel off v1's grid: v1's edges fall on texel centres, the wander decides


def _up(a):
    """Bilinear 2x of a float array (texel centres)."""
    h, w = a.shape
    ys = (np.arange(2 * h) + 0.5) / 2 - 0.5 - OFF
    xs = (np.arange(2 * w) + 0.5) / 2 - 0.5 - OFF
    y0 = np.clip(np.floor(ys).astype(int), 0, h - 1)
    x0 = np.clip(np.floor(xs).astype(int), 0, w - 1)
    y1, x1 = np.clip(y0 + 1, 0, h - 1), np.clip(x0 + 1, 0, w - 1)
    fy = np.clip(ys - np.floor(ys), 0, 1)[:, None]
    fx = np.clip(xs - np.floor(xs), 0, 1)[None, :]
    A = a[np.ix_(y0, x0)] * (1 - fx) + a[np.ix_(y0, x1)] * fx
    B = a[np.ix_(y1, x0)] * (1 - fx) + a[np.ix_(y1, x1)] * fx
    return A * (1 - fy) + B * fy


def _blur(a, sig):
    """Separable Gaussian blur (edge values repeated)."""
    r = int(3 * sig + 1)
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sig) ** 2)
    k /= k.sum()
    p = np.pad(a, r, mode="edge")
    p = np.apply_along_axis(lambda v: np.convolve(v, k, "valid"), 1, p)
    return np.apply_along_axis(lambda v: np.convolve(v, k, "valid"), 0, p)


def _nb(a, op):
    p = np.pad(a, 1, constant_values=(op is np.logical_and))
    return op.reduce([p[1:-1, 1:-1], p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:]])


def _thin(o):
    """The v1 texels of a part one texel wide (a staff, a strap, a seam)."""
    p = np.pad(o, 1)
    l, r, u, d = p[1:-1, :-2], p[1:-1, 2:], p[:-2, 1:-1], p[2:, 1:-1]
    return o & ((~l & ~r) | (~u & ~d))


SIG, AMP = 1.4, 0.30  # the edge's softness and its wander (about one texel either way)
TS, TA, TP = 1.1, 0.45, 3.5  # the tone areas: softness, wander, wander's period
LK, LN = 1.2, 0.35  # the volume light's strength and its wander
CREASE = 80  # one cloth crease per this many inner cloth texels


def underdrawing(who, action, view, i):
    """v1's frame as (part map: material name or None, v1 tone; face-role map; ink colours)."""
    ramps = M._v1_ramps(who)
    look = {}
    for mat, cols in ramps.items():
        for t, col in enumerate(cols):
            look.setdefault(_hx(col), (mat, t))
    roles = {_hx(k): v for k, v in FACE.get(who, {}).items()}
    img = np.array(Image.open(os.path.join(M.V1, f"npc.{who}.{action}.{view}.{i}.png")).convert("RGBA")).astype(int)
    h, w = img.shape[:2]
    op = img[..., 3] == 255
    tp = np.pad(~op, 1, constant_values=True)
    outer = op & (tp[:-2, 1:-1] | tp[2:, 1:-1] | tp[1:-1, :-2] | tp[1:-1, 2:])
    mat = np.full((h, w), "", object)
    tone = np.zeros((h, w))
    role = np.full((h, w), "", object)
    ink = {}
    for y in range(h):
        for x in range(w):
            if not op[y, x]:
                continue
            rgb = tuple(img[y, x, :3])
            if rgb in roles:
                role[y, x] = roles[rgb]
                ink[roles[rgb]] = rgb
                mat[y, x], tone[y, x] = "skin", 3  # the face under the mark
                continue
            part = look.get(rgb)
            if part is None:
                role[y, x] = "other"
                ink[("other", rgb)] = rgb
                mat[y, x], tone[y, x] = "skin", 3
                continue
            if part[1] == 0 and outer[y, x]:
                continue
            mat[y, x], tone[y, x] = part
    # a face colour away from the face (the scarf's embroidery in the iris's brown) is a decoration of
    # the part it sits on, not a face mark
    face = (mat == "skin") & (role == "")
    near = face.copy()
    for _ in range(2):
        p = np.pad(near, 1)
        near = p[1:-1, 1:-1] | p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:] | p[:-2, :-2] | p[2:, 2:] \
            | p[:-2, 2:] | p[2:, :-2]
    # a one-row slit across the figure (v1's cook from behind: an empty row between the hair and the
    # shirt) is closed: the neck, in the shade of the head
    gap = ~op
    gap[1:-1] &= op[:-2] & op[2:]
    gap[0] = gap[-1] = False
    for y in range(h):
        x = 0
        while x < w:
            if gap[y, x]:
                e = x
                while e + 1 < w and gap[y, e + 1]:
                    e += 1
                if e - x + 1 >= 3:
                    for xx in range(x, e + 1):
                        for yy, y2 in ((y - 1, y - 2), (y + 1, y + 2)):  # v1's outline rows: the part beyond
                            if mat[yy, xx] == "" and 0 <= y2 < h and mat[y2, xx]:
                                mat[yy, xx], tone[yy, xx] = mat[y2, xx], tone[y2, xx]
                        mat[y, xx], tone[y, xx] = ("skin", 1) if "skin" in ramps else (mat[y - 1, xx], tone[y - 1, xx])
                x = e + 1
            else:
                x += 1
    if view == "up":  # no face from behind: v1's face colours there are on held things (the child's catapult)
        near[:] = False
    for y, x in zip(*np.nonzero((role != "") & ~near)):
        nb = [(mat[yy, xx], tone[yy, xx]) for yy in range(y - 1, y + 2) for xx in range(x - 1, x + 2)
              if 0 <= yy < h and 0 <= xx < w and role[yy, xx] == "" and mat[yy, xx]]
        if nb:
            mat[y, x], tone[y, x] = max(sorted(set(nb)), key=nb.count)  # sorted: reproducible ties
        rgb = tuple(img[y, x, :3])
        role[y, x] = "deco"
        ink[("deco", rgb)] = rgb
    return ramps, mat, tone, role, ink, img


def render(who, action, view, i, frame_no=0):
    ramps, mat, tone, role, ink, img = underdrawing(who, action, view, i)
    h, w = mat.shape
    H2, W2 = 2 * h, 2 * w
    names = sorted({m for m in mat.ravel() if m})
    # 2. the shapes: soft one-hot planes, a wandering edge, the strongest part wins
    seed = f"{who}"
    score = np.zeros((len(names) + 1, H2, W2))
    score[0] = _blur(_up((mat == "").astype(float)), SIG) + AMP * _noise(H2, W2, f"{seed}:bg", 5.0)
    for k, n in enumerate(names, 1):
        o = mat == n
        score[k] = _blur(_up(o.astype(float)), SIG) + AMP * _noise(H2, W2, f"{seed}:{n}", 5.0)
        score[k] += 0.9 * _blur(_up(_thin(o).astype(float)), 0.7)  # thin things keep their line
    lab = score.argmax(0)
    # close holes inside the figure (an enclosed empty texel takes its most common neighbour)
    lab = _close_holes(lab, np.kron(mat != "", np.ones((2, 2), bool)))
    # the feet stand on the ground: where v1's outline is on its bottom row, the redrawn sole reaches the
    # row above the frame's last (the outline then lies on the last row), whatever the wander did
    v1op = img[..., 3] == 255
    for x in range(W2):
        if not v1op[h - 1, min(w - 1, max(0, (x - 1) // 2))]:
            continue
        col = np.nonzero(lab[H2 - 6:H2 - 1, x])[0]
        if len(col):
            y = H2 - 6 + col.max()
            lab[y + 1:H2 - 1, x] = lab[y, x]
    R6 = {k: ramp6(v) for k, v in ramps.items()}
    c = Canvas(W2, H2, R6)
    # 3. the shading: v1's tones as a soft field + the volume light (not on skin) + a small wander
    # v1's tone areas redrawn like the parts: soft planes whose edges wander, the strongest tone wins
    nz = _noise(H2, W2, f"{seed}:tone", 4.0)
    tsc = np.stack([_blur(_up((tone == t).astype(float)), TS) + TA * _noise(H2, W2, f"{seed}:t{t}", TP)
                    for t in range(5)])
    base = np.array([0, 1, 3, 4, 5])[tsc.argmax(0)].astype(float)
    for k, n in enumerate(names, 1):
        m = lab == k
        if not m.any():
            continue
        c.fill(m, n, 3)
        t3 = base.copy()
        if n != "skin":
            lam = dome_light(m, (-0.55, -0.75, 0.55), 1.0)
            v = lam[m]
            lo, hi = float(np.percentile(v, 5)), float(np.percentile(v, 95))
            lam = (lam - lo) / max(1e-6, hi - lo)
            t3 = t3 + LK * (lam - 0.5) + LN * nz
        else:
            t3 = t3 + 0.2 * nz  # skin keeps v1's flat planes: no light from above
        t3 = np.clip(np.round(t3), 1, 5)
        c.tone[m] = t3[m].astype(np.int8)
    _lines(c, lab, names, mat, tone, nz)
    if who == "child" and view == "up" and "hair" in names:
        _locks(c, lab == names.index("hair") + 1)
    _creases(c, lab, names, f"{who}:{view}")
    _rims(c, lab, names)
    # 4. the face
    _face(c, who, role, ink, view, img[..., :3])
    # what v1 drew in its first row / column stops 2 texels inside the frame
    c.mat[:2, :] = 0
    c.mat[:, :2] = 0
    c.mat[:, -2:] = 0
    c.ink = {(x, y): v for (x, y), v in c.ink.items() if y >= 2 and 2 <= x < c.w - 2}
    despeckle(c, loose=tuple(ramps))
    c.outline()
    c.shadow_band()
    smooth_lone(c)
    _cap_colours(c, CAP.get(who))
    return c


CAP = {"traveller": 64}  # the traveller's coat, pack, scarf, hat... : at most this many colours a frame


def _cap_colours(c, cap):
    """Over the cap: the smallest parts drop the v3 middle shade (tone 2 -> 1 or 3 by the light), one part at
    a time, until the frame's colours fit."""
    if not cap:
        return

    def count():
        a = c.rgba()
        return len({tuple(p) for p in a[a[..., 3] == 255][:, :3]})

    sizes = sorted((int((c.mat == k).sum()), k) for k in range(1, len(c.names)))
    for _, k in sizes:
        if count() <= cap:
            break
        m = (c.mat == k) & (c.tone == 2)
        c.tone[m] = 1
    for _, k in sizes:  # then the light tops (tone 5 -> 4)
        if count() <= cap:
            break
        m = (c.mat == k) & (c.tone == 5)
        c.tone[m] = 4


def _locks(c, hair):
    """The child's back hair as locks (inspection: a woven pad): from the crown, curved partings run down
    and out, each a dark texel with a lit texel on its left; partings start at different heights, so the
    locks are of different lengths and widths, and the lock tips break the hair's lower edge."""
    ys, xs = np.nonzero(hair)
    if not len(ys):
        return
    top, bot = ys.min(), ys.max()
    cx = (xs.min() + xs.max()) / 2
    hh = max(1, bot - top)
    lam = dome_light(hair, (-0.55, -0.75, 0.55), 1.0)
    v = lam[hair]
    lam = (lam - v.min()) / max(1e-6, v.max() - v.min())
    t = np.clip(np.round(2.5 + 2.4 * (lam - 0.3)), 1, 5)  # one smooth lit dome first
    c.tone[hair] = t[hair].astype(np.int8)
    for off, start in ((-11, 0.30), (-6, 0.18), (-2, 0.42), (3, 0.22), (8, 0.35), (12, 0.55)):
        for y in range(int(top + start * hh), bot + 1):
            f = (y - top) / hh
            x = int(round(cx + off * (0.55 + 0.6 * f)))
            if 0 <= x < c.w and hair[y, x]:
                c.tone[y, x] = 1
                if x - 1 >= 0 and hair[y, x - 1]:
                    c.tone[y, x - 1] = min(5, int(c.tone[y, x - 1]) + 1)


def _h(*k):
    return int(hashlib.md5(":".join(map(str, k)).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def _creases(c, lab, names, key):
    """Cloth creases drawn like the hero's: short strokes (4-9 texels) that fall mostly downward with their
    own slant, a dark texel with a lit texel on its upper-left side — scattered by a hash inside the larger
    cloth faces, at their own lengths and angles (no evenly spaced stripes)."""
    skip = M.SKIP_FOLDS | M.HAIRS
    for k, n in enumerate(names, 1):
        if n in skip:
            continue
        m = lab == k
        inner = m.copy()
        for _ in range(2):
            p = np.pad(inner, 1)
            inner = inner & p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]
        area = int(inner.sum())
        if area < 120:
            continue
        ys, xs = np.nonzero(inner)
        y0, x0 = ys.min(), xs.min()
        hh, ww = ys.max() - y0 + 1, xs.max() - x0 + 1
        for j in range(area // CREASE):
            sx = x0 + int(_h(key, n, j, "x") * ww)
            sy = y0 + int(_h(key, n, j, "y") * hh)
            if not inner[min(sy, c.h - 1), min(sx, c.w - 1)]:
                continue
            L = 4 + int(_h(key, n, j, "L") * 6)
            slant = (_h(key, n, j, "s") - 0.5) * 0.8
            x = float(sx)
            for t in range(L):
                yy, xx = sy + t, int(round(x))
                if not (0 <= yy < c.h and 0 <= xx < c.w) or not inner[yy, xx]:
                    break
                c.tone[yy, xx] = max(1, int(c.tone[yy, xx]) - 1)
                if xx - 1 >= 0 and inner[yy, xx - 1] and t < L - 1:
                    c.tone[yy, xx - 1] = min(5, int(c.tone[yy, xx - 1]) + 1)
                x += slant


def _rims(c, lab, names):
    """The hero's part edges: a part's texel whose upper or left neighbour is another part or the air
    catches the light (+1 tone, not on skin and not in a part's dark tones); a texel whose lower or right
    neighbour is another part (not the air: the outline does that) sits in its shadow (-1 tone)."""
    h, w = lab.shape
    p = np.pad(lab, 1, constant_values=0)
    up, lf, dn, rt = p[:-2, 1:-1], p[1:-1, :-2], p[2:, 1:-1], p[1:-1, 2:]
    skin = names.index("skin") + 1 if "skin" in names else -1
    body = (lab > 0) & (lab != skin)
    lit = body & ((up != lab) | (lf != lab)) & (c.tone >= 3)
    shut = (lab > 0) & (((dn != lab) & (dn > 0)) | ((rt != lab) & (rt > 0))) & ~lit  # skin too: under the hair
    c.tone[lit] = np.minimum(c.tone[lit] + 1, 5)
    c.tone[shut] = np.maximum(c.tone[shut] - 1, 1)


def _lines(c, lab, names, mat, tone, nz):
    """v1's lines one or two texels wide drawn in a part's own tones (a seam, the apron's panels, a fold)
    come back as lines one or two texels wide at 2x (half v1's doubled width), each row/column stepping
    by the wander — not a 2 x 2 band."""
    h, w = mat.shape
    idx = {n: k for k, n in enumerate(names, 1)}
    to3 = (0, 1, 3, 4, 5)
    for vert in (True, False):
        M, T = (mat, tone) if vert else (mat.T, tone.T)
        for y in range(M.shape[0]):
            x = 0
            while x < M.shape[1]:
                n, t = M[y, x], T[y, x]
                e = x
                while e + 1 < M.shape[1] and M[y, e + 1] == n and T[y, e + 1] == t:
                    e += 1
                L = e - x + 1
                if n and n != "skin" and L <= 2 and x > 0 and e + 1 < M.shape[1] \
                        and M[y, x - 1] == n and M[y, e + 1] == n:
                    ta, tb = T[y, x - 1], T[y, e + 1]
                    if (ta > t and tb > t) or (ta < t and tb < t):
                        for k in (0, 1):
                            r = 2 * y + k
                            mid = 2 * x + L  # the doubled run's centre (left of it), half a texel off as the parts
                            wob = 1 if (nz[r, mid] if vert else nz[mid, r]) > 0 else 0
                            for q in range(L):
                                cc = mid - (L - 1) // 2 + q + wob - (1 if L == 2 else 0)
                                yy, xx = (r, cc) if vert else (cc, r)
                                if 0 <= yy < lab.shape[0] and 0 <= xx < lab.shape[1] and lab[yy, xx] == idx[n]:
                                    c.tone[yy, xx] = max(1, to3[int(t)])
                x = e + 1


def _close_holes(lab, v1_opaque):
    h, w = lab.shape
    empty = lab == 0
    outside = np.zeros_like(empty)
    st = [(y, x) for y in range(h) for x in (0, w - 1)] + [(y, x) for y in (0, h - 1) for x in range(w)]
    while st:
        y, x = st.pop()
        if 0 <= y < h and 0 <= x < w and empty[y, x] and not outside[y, x]:
            outside[y, x] = True
            st += [(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)]
    holes = empty & ~outside & v1_opaque  # only what the redraw opened; v1's own gaps stay open
    for _ in range(6):
        if not holes.any():
            break
        for y, x in zip(*np.nonzero(holes)):
            nb = [lab[yy, xx] for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1))
                  if 0 <= yy < h and 0 <= xx < w and lab[yy, xx] != 0]
            if nb:
                lab[y, x] = max(sorted(set(nb)), key=nb.count)
                holes[y, x] = False
    return lab


def _shade(rgb, f):
    return tuple(max(0, min(255, int(round(v * f)))) for v in rgb)


def _face(c, who, role, ink, view, img_rgb):
    h, w = role.shape
    # eyes: 8-connected clusters of eye roles
    eye = np.isin(role, list(EYE_ROLES))
    seen = np.zeros_like(eye)
    lash = ink.get("lash", (30, 24, 30))
    eyes = []
    for y0, x0 in zip(*np.nonzero(eye)):
        if seen[y0, x0]:
            continue
        st, pts = [(y0, x0)], []
        seen[y0, x0] = True
        while st:
            y, x = st.pop()
            pts.append((y, x))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < h and 0 <= xx < w and eye[yy, xx] and not seen[yy, xx]:
                        seen[yy, xx] = True
                        st.append((yy, xx))
        ys, xs = zip(*pts)
        bx0, by0, bx1, by1 = min(xs), min(ys), max(xs), max(ys)
        has_iris = any(role[y, x].startswith("iris") for y, x in pts)
        outer_right = (bx0 + bx1) / 2 > w / 2 if view == "down" else True
        side = view in ("left", "right")
        if side:  # the side eye: its outer end toward the back of the head
            outer_right = view == "left"
        eyes.append((bx0 + bx1 + 1, 2 * by0 - 1, side, has_iris, outer_right))
    # the other marks, redrawn from soft planes (a wandering edge, not v1's 2 x 2)
    for r in ("brow", "mouth", "blush", "freckle", "line", "glint", "soot", "deco"):
        rs = [k for k in ink if (k == r or (isinstance(k, tuple) and k[0] == r))]
        for key in rs:
            m1 = role == r
            if isinstance(key, tuple):
                m1 = m1 & (img_rgb == np.array(key[1])).all(-1)
            if not m1.any():
                continue
            soft = _blur(_up(m1.astype(float)), 0.6) + 0.18 * _noise(2 * h, 2 * w, f"{who}:{r}", 3.0)
            m2 = soft > 0.42
            col = ink[key]
            for y, x in zip(*np.nonzero(m2)):
                if r == "blush" and (x + y) % 2:
                    continue  # soft cheeks: every other texel
                c.dot(int(x), int(y), _hex(col))
            if r == "mouth":  # the lighter inside of the mouth's lower row
                ys, xs = np.nonzero(m2)
                if len(ys):
                    yb = ys.max()
                    for x in xs[ys == yb][1:-1]:
                        c.dot(int(x), int(yb), _hex(_shade(col, 1.25)))
    ink["_blink"] = any(v.startswith("iris") for v in FACE.get(who, {}).values())  # shut = blinking
    for cx, top, side, has_iris, outer_right in eyes:  # the eyes last, over brows and cheeks
        _eye(c, cx, top, side, has_iris, ink, lash, outer_right)
    st = role == "stub"
    if st.any():  # stubble: single dots, every other texel of the v1 area
        m2 = _up(st.astype(float)) > 0.4
        for y, x in zip(*np.nonzero(m2)):
            if int(hashlib.md5(f"{who}:{x}:{y}".encode()).hexdigest()[:2], 16) < 70 \
                    and not any(c.ink.get((x + dx, y + dy)) for dx, dy in ((-1, 0), (0, -1), (-1, -1), (1, -1))):
                c.dot(int(x), int(y), _hex(ink["stub"]))


EYE8 = (  # the open eye, front, its outer end on the right: L lash, d/m/l iris dark/middle/light, p pupil,
    ".LLLLLL.",  # S shine, toward the light (upper left)
    "LLLLLLLL",
    ".dSppddL",
    ".mmppmm.",
    ".mmmmmm.",
    "..llll..",
)
EYE6 = (  # the open eye seen from the side (the face's own outer end toward the back of the head)
    ".LLLL.",
    "LLLLLL",
    "dSpdL.",
    "mppm..",
    "mmmm..",
    ".ll...",
)


def _lift(rgb, f):
    """Toward a light warm grey by f (keeps the hue's lean)."""
    return tuple(int(round(v + (t - v) * f)) for v, t in zip(rgb, (230, 214, 190)))


def _eye(c, cx, top, side, iris, ink, lash, outer_right):
    """An eye at 2x detail centred on v1's eye: open, 8 x 6 (6 x 6 from the side) — a lash line 2 texels deep
    whose outer end drops a row, an iris in 3 tones, a 2-texel pupil, a shine texel; shut, a lid arc."""
    if not iris:
        ew = 6 if side else 8
        x0 = cx - ew // 2
        for k in range(ew):
            t = k / (ew - 1)
            if ink.get("_blink"):  # a blink: the lid comes down, a line sagging at its middle
                yy = top + 3 + int(round(1.0 * np.sin(np.pi * t)))
            else:  # the elder's and merchant's smiling shut eyes: an arch
                yy = top + 3 - int(round(1.6 * np.sin(np.pi * t)))
            c.dot(x0 + k, yy, _hex(lash))
            if 0 < k < ew - 1:
                c.dot(x0 + k, yy + 1, _hex(lash))
        return
    if "iris_d" in ink:
        i_d = ink["iris_d"]
        i_m = ink.get("iris") or _lift(i_d, 0.35)
    else:  # one v1 iris colour (often near black): it is the dark tier, the others lifted from it
        i_d = ink.get("iris", (60, 60, 60))
        i_m = _lift(i_d, 0.30)
    i_l = ink.get("iris_l") or _lift(i_m, 0.30)
    col = {"L": lash, "d": i_d, "m": i_m, "l": i_l, "p": _shade(i_d, 0.55), "S": ink.get("shine", (255, 255, 255))}
    pat = EYE6 if side else EYE8
    ew = len(pat[0])
    x0 = cx - ew // 2
    for j, row in enumerate(pat):
        if not outer_right:
            row = row[::-1]
            row = row.replace("S", "#").replace("#", "S")
        for k, ch in enumerate(row):
            if ch in col:
                c.dot(x0 + k, top + j, _hex(col[ch]))


def breathe(c, k):
    """A frame that would repeat an earlier one (v1 repeats the woman's idle 0 as walk 3; the redraw can
    make two near frames one picture): the body moves, not the head — the shoulders and arms settle one
    texel (k odd) or lift one texel (k even) between the neck and the waist; the head and legs stay."""
    ys = np.nonzero((c.mat > 0).any(1))[0]
    top, bot = int(ys.min()), int(ys.max())
    neck = top + int(0.42 * (bot - top))
    waist = top + int(0.72 * (bot - top))
    sl = slice(neck, waist)
    m, t = c.mat.copy(), c.tone.copy()
    if k % 2:  # settle: rows neck..waist-1 move down one, the neck row is kept twice
        c.mat[neck + 1:waist + 1], c.tone[neck + 1:waist + 1] = m[sl], t[sl]
        mv = lambda x, y: (x, y + 1) if neck <= y < waist else (x, y)  # noqa: E731
    else:  # lift: rows neck+1..waist move up one, the waist row is kept twice
        c.mat[neck:waist], c.tone[neck:waist] = m[neck + 1:waist + 1], t[neck + 1:waist + 1]
        mv = lambda x, y: (x, y - 1) if neck < y <= waist else (x, y)  # noqa: E731
    c.ink = {mv(x, y): v for (x, y), v in c.ink.items()}
