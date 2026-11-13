"""v3 villagers, round 4: every part is a HAND-DRAWN PIXEL MAP at the v3 grid (64 x 112), one character
per texel, the way the approved hero's face and v1's villagers were made (tools/npc_release/*.py).

Nothing is derived from the v1 pixels: no upscaling, no blur, no noise, no half-texel offset. The v1 frames
and their tools are used only for two things, both read-only:
  * the look (as a reference beside the drawing: what each part is, its colours = v1's ramps);
  * the MOTION of each frame: v1's own pose table (npc_common.idle / gait: bob, breath, the feet's
    forward/lift, the arm swing, the hem's sway, the prop's bob, the blink), applied x2 to the v3 parts.

A part is drawn once and moved as the same picture from frame to frame (a head that only moves keeps every
texel). Front / back maps are drawn as their LEFT half and completed by mirroring with the right half one
step darker (STYLE.md 3.1; v1 did the same). Facing left: drawn facing right with the character's left side
near (the held thing stays in its hand), then mirrored, as v1 did.

Map syntax: rows of characters, '.' = empty. A row "NN|text" starts at column NN. A legend maps a character
to (material, tone 0-5) or to an ink colour '#rrggbb' (eyes, mouth, stubble: STYLE.md 3.2, 8 inks a person).
"""

import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "npc_release"))
sys.path.insert(0, os.path.join(HERE, "..", "art_proto"))
from v3lib import Canvas, despeckle, ramp6  # noqa: E402

W, H = 64, 112


# ------------------------------------------------------------------ maps

def grid(text, width=None):
    """Rows of a hand-drawn map. 'NN|abc' puts abc at column NN. Returns equal-width rows."""
    rows = []
    for line in text.strip("\n").split("\n"):
        line = line.rstrip()
        if "|" in line:
            off, body = line.split("|", 1)
            line = "." * int(off) + body
        rows.append(line)
    w = width or max(len(r) for r in rows)
    for r in rows:
        assert len(r) <= w, (len(r), w, r)
    return [r.ljust(w, ".") for r in rows]


def half(text, hw=32):
    """A front / back map drawn as its left half (each row ends at the centre line, column hw-1:
    rows are right-aligned). Returns (rows, mirrored) where the right half is the mirror."""
    rows = []
    for line in text.strip("\n").split("\n"):
        line = line.rstrip()
        assert len(line) <= hw, (len(line), line)
        r = line.rjust(hw, ".")
        rows.append(r + r[::-1])
    return rows


def legend(groups, inks=None):
    """groups: [("abcdef", "skin"), ...]: the 6 characters are the material's tones 0..5."""
    out = {}
    for chars, mat in groups:
        assert len(chars) == 6, chars
        for t, ch in enumerate(chars):
            assert ch not in out, ch
            out[ch] = (mat, t)
    for ch, rgb in (inks or {}).items():
        assert ch not in out, ch
        out[ch] = rgb
    return out


def mirror_rows(rows):
    return [r[::-1] for r in rows]


# tone changes
def t_mirror(t):  # the mirrored (right) half of a front / back map: the lights drop one step
    return t - 1 if t >= 4 else t


def t_darker(t):  # the far arm / far side (v1's `darker`)
    return t - 1 if t > 1 else t


def t_far(t):  # the far leg / far arm in a side view (v1 drew it flat in tone 1): two dark steps
    return (0, 1, 1, 2, 2, 3)[t]


# ------------------------------------------------------------------ the figure

class Fig:
    """A v3lib.Canvas plus which part drew each texel (for the eye check)."""

    def __init__(self, ramps5):
        self.c = Canvas(W, H, {k: ramp6(v) for k, v in ramps5.items()})
        self.part = np.zeros((H, W), object)
        self.part[:] = ""

    def stamp(self, rows, x0, y0, leg, part="", half_mirror=False, flip=False, tone=None, shift=None,
              skip=""):
        """Puts a map with its top-left at (x0, y0). half_mirror: columns >= half the width are the
        mirrored half (lights one step down). flip: the map is mirrored left-right. tone: a function
        on every ramp tone (darker / far). shift(row, col, ch) -> (dx, dy) moves single texels (the hem's
        sway, the breath)."""
        c = self.c
        wmap = len(rows[0]) if rows else 0
        for j, row in enumerate(rows):
            r = row[::-1] if flip else row
            for i, ch in enumerate(r):
                if ch == "." or ch in skip:
                    continue
                v = leg[ch]
                dx, dy = shift(j, i, ch) if shift else (0, 0)
                x, y = x0 + i + dx, y0 + j + dy
                if not (0 <= x < W and 0 <= y < H):
                    continue
                if isinstance(v, str):
                    c.dot(x, y, v)
                else:
                    m, t = v
                    if half_mirror and i >= wmap // 2:
                        t = t_mirror(t)
                    if tone is not None and t > 0:
                        t = tone(t)
                    c.put(x, y, m, t)
                self.part[y, x] = part

    def finish(self):
        # STYLE.md 3.4: the clean-up every picture gets (as the hero): a texel unlike all 4 neighbours, 3 of
        # which (2 in hair) are one other tone of its material, takes that tone. Inks (eyes) are kept.
        despeckle(self.c, loose=("hair",))
        self.c.outline()
        self.c.shadow_band()
        return self

    def rgba(self):
        return self.c.rgba()


# ------------------------------------------------------------------ v1's motion (read only)

def v1_pose(npc, action, i):
    """v1's pose for this frame (tools/npc_release/npc_common.py: idle / gait), the same table that made
    the approved frames."""
    return npc.pose(action, i)


def v1_back_pose(p):
    """v1's back view swaps the feet and the arms (npc_common.Npc.frame)."""
    from npc_common import Pose
    return Pose(**{**p.__dict__, "near": p.far, "far": p.near, "arm_near": p.arm_far, "arm_far": p.arm_near})


# ------------------------------------------------------------------ checks

def eye_inks_outside(fig, eye_inks, head_parts):
    """Eye inks (lash, iris, shine) drawn by anything but a head part: must be 0."""
    bad = 0
    for (x, y), rgb in fig.c.ink.items():
        if "#%02x%02x%02x" % rgb in eye_inks and fig.part[y, x] not in head_parts:
            bad += 1
    return bad


def iris_blobs(fig, iris_inks):
    """The number of separate iris blobs (8-connected) in the frame: front 2, side 1, back 0."""
    pts = {xy for xy, rgb in fig.c.ink.items() if "#%02x%02x%02x" % rgb in iris_inks}
    n = 0
    seen = set()
    for p in pts:
        if p in seen:
            continue
        n += 1
        st = [p]
        seen.add(p)
        while st:
            x, y = st.pop()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    q = (x + dx, y + dy)
                    if q in pts and q not in seen:
                        seen.add(q)
                        st.append(q)
    return n


def translucent(img):
    a = img[..., 3]
    return int(((a > 0) & (a < 255)).sum())
