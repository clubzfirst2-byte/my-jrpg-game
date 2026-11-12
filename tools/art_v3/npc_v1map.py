"""v3 NPC production, round 2 (after the inspections of the 9 villagers): every villager frame is drawn from
the approved v1 frame's PART MAP, the way the hero's head keeps to v1's outline (hero_views.v1_head_outline).

Why: the inspections asked first of all that each villager looks like the approved v1 person, in every
direction and frame, with v1's motion (the walk's bob and stride, the idle breath, every frame its own
picture, left drawn on its own where v1 does). The hand-built bodies (npc_batch2-4) drifted from v1 (the
elder's staff, the child's head and eyes, the cook's apron, the merchant's glasses, the guard's spear).

How, per frame (src/art-release/npc/npc.<who>.<action>.<dir>.<n>.png, read only):
  1. each v1 texel is read as a PART (material + v1 tone, from the person's v1 ramps in
     tools/npc_release/<who>.py and the shared ramps in tools/art_proto/pixel.py) or an ink (eyes, mouth);
     v1's outer outline is left out (v3 draws its own 1-texel outline);
  2. the part map is doubled with Scale2x (diagonal steps smoothed, not 2 x 2 blocks);
  3. every part is painted again in the v3 6-tone ramp: v1's tone, then the part's own volume lit from the
     top left (dome light of each connected piece) moves a texel one step up or down and brings in the new
     middle shade (tone 2) between light and shadow: even bands, not the 2 x 2 blocks of a plain upscale;
  4. the v3 outline (v1's values) and the shadow-side band; a lone texel takes its neighbours' tone.
The pose, the props and the motion are therefore v1's own; the painting is v3's.
"""

import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from v3lib import Canvas, despeckle, dome_light, ramp6, smooth_lone  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
V1 = os.path.join(ROOT, "src", "art-release", "npc")
NPC_TOOLS = os.path.join(ROOT, "tools", "npc_release")
PROTO = os.path.join(ROOT, "tools", "art_proto")


def _v1_ramps(who):
    """The person's v1 ramps (their own first, then the shared ones), read from the v1 tools."""
    for p in (PROTO, NPC_TOOLS):
        if p not in sys.path:
            sys.path.append(p)
    import importlib
    pixel = importlib.import_module("pixel")
    mod = importlib.import_module(who if who != "woman" else "woman")
    ramps = dict(getattr(mod, "RAMPS", {}))
    out = dict(ramps)
    for k, v in pixel.BASE_RAMPS.items():
        out.setdefault(k, v)
    return out


def _hx(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


def _scale2x(lab):
    """Scale2x (EPX) on a label array (any values)."""
    h, w = lab.shape
    P = np.pad(lab, 1, mode="edge")
    A, B, C, D = P[:-2, 1:-1], P[1:-1, 2:], P[1:-1, :-2], P[2:, 1:-1]
    out = np.zeros((2 * h, 2 * w), lab.dtype)
    out[0::2, 0::2] = np.where((C == A) & (C != D) & (A != B), A, lab)
    out[0::2, 1::2] = np.where((A == B) & (A != C) & (B != D), B, lab)
    out[1::2, 0::2] = np.where((D == C) & (D != B) & (C != A), C, lab)
    out[1::2, 1::2] = np.where((B == D) & (B != A) & (D != C), D, lab)
    return out


V1_TO_V3 = (0, 1, 3, 4, 5)  # v1's 5 tones in the v3 6-tone ramp (tone 2 is v3's new middle shade)


def render(who, action, view, i, flip=False):
    """One v3 frame (a Canvas) drawn from v1's frame of the same key."""
    ramps = _v1_ramps(who)
    look = {}
    for mat, cols in ramps.items():
        for t, col in enumerate(cols):
            look.setdefault(_hx(col), (mat, t))
    img = np.array(Image.open(os.path.join(V1, f"npc.{who}.{action}.{view}.{i}.png")).convert("RGBA")).astype(int)
    if flip:
        img = img[:, ::-1]
    h, w = img.shape[:2]
    op = img[..., 3] == 255
    # labels: 0 empty; parts 1..; inks
    names, keys = [None], {}
    lab = np.zeros((h, w), np.int32)
    tp = np.pad(~op, 1, constant_values=True)
    outer = op & (tp[:-2, 1:-1] | tp[2:, 1:-1] | tp[1:-1, :-2] | tp[1:-1, 2:])
    for y in range(h):
        for x in range(w):
            if not op[y, x]:
                continue
            rgb = tuple(img[y, x, :3])
            part = look.get(rgb)
            if part is not None and part[1] == 0 and outer[y, x]:
                continue  # v1's outer outline: v3 draws its own
            key = ("p",) + part if part is not None else ("i", rgb)
            if key not in keys:
                keys[key] = len(names)
                names.append(key)
            lab[y, x] = keys[key]
    big = _scale2x(lab)
    R6 = {k: ramp6(v) for k, v in ramps.items()}
    c = Canvas(2 * w, 2 * h, R6)
    for k in range(1, len(names)):
        sel = big == k
        if not sel.any():
            continue
        key = names[k]
        if key[0] == "p":
            c.fill(sel, key[1], V1_TO_V3[key[2]])
        else:
            for yy, xx in zip(*np.nonzero(sel)):
                c.dot(int(xx), int(yy), "#%02x%02x%02x" % key[1])
    _repaint(c)
    _folds(c)
    # what v1 drew in its first row / column (the elder's staff, the guard's spear, the child's pinwheel)
    # stops 2 texels inside, so only the v3 outline touches the frame's edge
    c.mat[:2, :] = 0
    c.mat[:, :2] = 0
    c.mat[:, -2:] = 0
    c.ink = {(x, y): v for (x, y), v in c.ink.items() if y >= 2 and 2 <= x < c.w - 2}
    despeckle(c, loose=tuple(ramps))
    c.outline()
    c.shadow_band()
    smooth_lone(c)
    return c


def _repaint(c):
    """Every connected piece of a material is lit as a volume: a texel moves one tone up on the lit
    side, one down on the shadow side (never past its neighbours in the ramp), and the middle shade
    (tone 2) comes in where v1 had its shade (1) on the lit half or its base (3) on the shadow half."""
    yy, xx = np.mgrid[0:c.h, 0:c.w]
    for k, name in enumerate(c.names):
        if k == 0 or name in (None, "_ink"):
            continue
        m = c.mat == k
        if not m.any():
            continue
        lam = dome_light(m, (-0.55, -0.75, 0.55), 1.0)
        v = lam[m]
        lo, hi = float(np.percentile(v, 5)), float(np.percentile(v, 95))
        lam = (lam - lo) / max(1e-6, hi - lo)
        t = c.tone.astype(int)
        nt = t.copy()
        up = m & (lam > 0.66) & (t >= 3) & (t <= 4)
        dn = m & (lam < 0.30) & (t >= 3)
        nt[up] = t[up] + 1
        nt[dn] = t[dn] - 1
        nt[m & (t == 1) & (lam > 0.45)] = 2
        nt[m & (t == 3) & (lam < 0.48) & ~dn] = 2
        nt[m & (t == 0)] = 0
        c.tone[m] = np.clip(nt[m], 0, 5)


def vary(c, k):
    """A frame that would repeat an earlier one: the hair / headwear (the top 40 rows' parts) sway one
    texel sideways (k odd: right, even: left) — the smallest change that keeps the pose."""
    dx = 1 if k % 2 else -1
    top = slice(0, 40)
    m = c.mat[top].copy()
    t = c.tone[top].copy()
    c.mat[top] = np.roll(m, dx, 1)
    c.tone[top] = np.roll(t, dx, 1)
    ink = {}
    for (x, y), v in c.ink.items():
        ink[(x + dx, y) if y < 40 else (x, y)] = v
    c.ink = ink


SKIP_FOLDS = {"skin", "gem", "gold", "iron", "steel", "glass", "eye", "_ink", "wood", "leather", "boot", "gourd",
              "vane", "herb", "bone", "water"}
HAIRS = {"hair", "beard"}


def _folds(c):
    """The large faces get the hero's kind of drawing inside them (round 2, inspection: flat cloth):
    cloth falls in soft vertical folds (a 1-texel groove, its lit ridge on the left) that wander with
    the height; hair gets strands (a darker line every 4 texels, a lighter one beside it). Only where the
    face is at least 5 texels wide, never on its outline, never on skin, metal, props or inks."""
    yy, xx = np.mgrid[0:c.h, 0:c.w]
    for k, name in enumerate(c.names):
        if k == 0 or name in SKIP_FOLDS or name is None:
            continue
        m = c.mat == k
        inner = m & np.roll(m, 2, 1) & np.roll(m, -2, 1) & np.roll(m, 1, 0) & np.roll(m, -1, 0)
        if inner.sum() < 30:
            continue
        ph = (k * 37) % 11
        if name in HAIRS:
            pos = (xx + np.round(1.5 * np.sin(yy / 6.0 + ph))).astype(int) % 4
        else:
            pos = (xx + np.round(2.0 * np.sin(yy / 9.0 + ph))).astype(int) % 7
        t = c.tone.astype(int)
        groove = inner & (pos == 0) & (t >= 2)
        ridge = inner & (pos == (3 if name in HAIRS else 6)) & (t >= 1) & (t <= 4)
        t[groove] -= 1
        t[ridge] += 1
        c.tone[:] = np.clip(t, 0, 5)

