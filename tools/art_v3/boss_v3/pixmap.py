"""v3 bosses: parts are HAND-DRAWN PIXEL MAPS at the density-4 grid, one character per texel.

Nothing here draws a shape: no ellipse, no shading by a formula, no noise, no scaling. A part is a
map typed by hand (rows of characters); this module only reads the maps, mirrors them, and puts them
on a frame at whole-texel offsets, back to front. A part is the same picture in every frame.

Map syntax: rows of characters, '.' = empty. A row "NN|text" starts at column NN.
Legend: 7 characters per material = the ramp indices 0..6
    0 outline / deep gap, 1 deep shadow, 2 shadow (in-between), 3 base, 4 half light (in-between),
    5 light, 6 highlight.
Rules applied to a part when it is loaded (the same for every frame, so nothing boils):
  * an in-between tone (2, 4) that is not inside a 3 x 3 block of itself drops one step (STYLE 5.4);
  * mirror(): the mirrored copy is one step darker in its lights (6>5, 5>4, 4>3; STYLE 3.1) and the
    texel inside its right-hand outline takes tone 1 (the shadow side's dark band, STYLE 3.3).
Rules applied to a frame after the parts are placed:
  * a part's own outline texel (tone 0 next to the part's empty) that ends up INSIDE the figure
    becomes tone 1 (parts are separated by a shadow line, not by an outline; deep gaps drawn as
    tone 0 inside a map stay);
  * a texel on the figure's silhouette that is not an outline (a part cut at the ground) becomes
    tone 0 of its material.
"""

import re

import numpy as np

MID = (2, 4)


def _runs(m):
    return m.group(1) * int(m.group(2))


def grid(text):
    """'NN|text' starts at column NN; '(cN)' is the character c typed N times (a flat run)."""
    rows = []
    for line in text.strip("\n").split("\n"):
        line = line.strip()
        if not line or line.startswith(";"):  # ';' starts a note line
            continue
        line = re.sub(r"\((.)(\d+)\)", _runs, line)
        if "|" in line:
            off, body = line.split("|", 1)
            line = "." * int(off) + body
        rows.append(line)
    w = max(len(r) for r in rows)
    return [r.ljust(w, ".") for r in rows]


class Legend:
    def __init__(self, groups):
        """groups: [("abcdefg", "rotwood"), ...] 7 characters = tones 0..6."""
        self.mats = [m for _, m in groups]
        self.code = {}
        for k, (chars, _) in enumerate(groups):
            assert len(chars) == 7, chars
            for t, ch in enumerate(chars):
                assert ch not in self.code and ch != ".", ch
                self.code[ch] = (k, t)

    def mid(self, name):
        return self.mats.index(name)


class Part:
    """mat: int8 (-1 empty), tone: int8, edge: bool (the part's own outline)."""

    def __init__(self, mat, tone, edge=None, name=""):
        self.mat, self.tone, self.name = mat, tone, name
        self.h, self.w = mat.shape
        self.edge = _edge(mat, tone) if edge is None else edge

    def mirror(self, darker=True, band=True, relight=False):
        """The part for the image-right side.
        relight=False: the picture flipped. The lit rim that was inside its left outline would now sit
          on the shadow side, so the 3 texels inside a right-hand outline lose their lights (to base)
          and the first of them takes tone 1 (the shadow side's dark band, STYLE 3.3).
        relight=True (an upright limb typed in rows, one cross-section per run): the SHAPE is flipped,
          but every run keeps its own left-to-right order, so the limb on the right is lit from the
          left like the one on the left.
        darker: the lights drop one step (6>5, 5>4, 4>3: the right half is one step darker, STYLE 3.1)."""
        mat, tone, edge = self.mat[:, ::-1].copy(), self.tone[:, ::-1].copy(), self.edge[:, ::-1].copy()
        if relight:
            for y in range(self.h):
                x = 0
                while x < self.w:
                    if mat[y, x] < 0:
                        x += 1
                        continue
                    x1 = x
                    while x1 < self.w and mat[y, x1] >= 0:
                        x1 += 1
                    mat[y, x:x1] = mat[y, x:x1][::-1].copy()
                    tone[y, x:x1] = tone[y, x:x1][::-1].copy()
                    edge[y, x:x1] = edge[y, x:x1][::-1].copy()
                    x = x1
            edge = _edge(mat, tone)
        elif band:
            for y, x in zip(*np.nonzero(edge)):
                if x + 1 < self.w and mat[y, x + 1] >= 0:
                    continue  # not a right-hand outline
                for k in (1, 2, 3):
                    if x - k < 0 or mat[y, x - k] < 0 or edge[y, x - k]:
                        break
                    if k == 1 and tone[y, x - k] > 1:
                        tone[y, x - k] = 1
                    elif tone[y, x - k] > 3:
                        tone[y, x - k] = 3
        if darker:
            tone = np.where(tone >= 4, tone - 1, tone).astype(np.int8)
        return Part(mat, _mid_rule(mat, tone), edge, self.name + "~")

    def swap(self, mapping, tones=None):
        """The same picture in other materials ({from: to} material indices), tones remapped."""
        mat = self.mat.copy()
        for a, b in mapping.items():
            mat[self.mat == a] = b
        tone = self.tone.copy()
        if tones is not None:
            lut = np.array(tones, np.int8)
            tone = np.where(mat >= 0, lut[np.clip(tone, 0, 6)], tone).astype(np.int8)
        return Part(mat, tone, self.edge, self.name + "*")

    def rows(self, y0, y1):
        return Part(self.mat[y0:y1], self.tone[y0:y1], self.edge[y0:y1], self.name)


def _edge(mat, tone):
    h, w = mat.shape
    op = mat >= 0
    pad = np.pad(op, 1)
    out = ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    return op & (tone == 0) & out


def _mid_rule(mat, tone):
    h, w = mat.shape
    code = np.where(mat >= 0, mat.astype(int) * 8 + tone, -1)
    ok = np.zeros((h, w), bool)
    for y in range(h - 2):
        for x in range(w - 2):
            c = code[y, x]
            if c >= 0 and (c % 8) in MID and (code[y:y + 3, x:x + 3] == c).all():
                ok[y:y + 3, x:x + 3] = True
    bad = (mat >= 0) & np.isin(tone, MID) & ~ok
    return np.where(bad, tone - 1, tone).astype(np.int8)


def part(text, legend, name="", cols=False):
    """cols=True: every typed line is one COLUMN of the part, top to bottom (used for parts that run
    sideways -- a line is then the limb's cross-section, as it is for upright parts typed in rows)."""
    rows = grid(text)
    if cols:
        rows = ["".join(r[i] for r in rows) for i in range(len(rows[0]))]
    h, w = len(rows), len(rows[0])
    mat = np.full((h, w), -1, np.int8)
    tone = np.zeros((h, w), np.int8)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == ".":
                continue
            assert ch in legend.code, (name, y, x, ch)
            mat[y, x], tone[y, x] = legend.code[ch]
    return Part(mat, _mid_rule(mat, tone), None, name)


class Frame:
    def __init__(self, w, h, legend, ramps):
        self.w, self.h, self.legend, self.ramps = w, h, legend, ramps
        self.mat = np.full((h, w), -1, np.int8)
        self.tone = np.zeros((h, w), np.int8)
        self.edge = np.zeros((h, w), bool)
        self.log = []  # (name, x, y): the placement of each part (for the check of carried parts)

    def put(self, p, x, y, clip_y=None):
        """Place a part with its top-left at (x, y). clip_y: rows from clip_y down are not drawn."""
        x, y = int(x), int(y)
        self.log.append((p.name, x, y))
        y1 = min(self.h, y + p.h, clip_y if clip_y is not None else self.h)
        x0, y0, x1 = max(0, x), max(0, y), min(self.w, x + p.w)
        if x1 <= x0 or y1 <= y0:
            return
        sm = p.mat[y0 - y:y1 - y, x0 - x:x1 - x]
        sel = sm >= 0
        self.mat[y0:y1, x0:x1][sel] = sm[sel]
        self.tone[y0:y1, x0:x1][sel] = p.tone[y0 - y:y1 - y, x0 - x:x1 - x][sel]
        self.edge[y0:y1, x0:x1][sel] = p.edge[y0 - y:y1 - y, x0 - x:x1 - x][sel]

    def finish(self):
        op = self.mat >= 0
        pad = np.pad(op, 1)
        inner = pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:]
        tone = self.tone.copy()
        tone[op & self.edge & inner] = 1
        tone[op & ~inner] = 0
        # an in-between tone whose 3 x 3 block is cut by the part in front of it drops one step
        return _mid_rule(self.mat, tone)

    def rgba(self):
        tone = self.finish()
        img = np.zeros((self.h, self.w, 4), np.uint8)
        for k, name in enumerate(self.legend.mats):
            r = self.ramps[name]
            for t in range(7):
                s = (self.mat == k) & (tone == t)
                if s.any():
                    img[s, :3] = r[t]
                    img[s, 3] = 255
        return img
