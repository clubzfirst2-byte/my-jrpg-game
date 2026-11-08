"""Shared drawing for the villagers' RELEASE art (NPC batch 1).

The same method as the adopted hero (tools/hero_release/):
  * heads and bodies are hand-made pixel maps, one character per pixel, with a 5-tone ramp per
    material, the light from the top left and an outline (tools/art_proto/pixel.py);
  * front and back views are drawn as their LEFT half and completed by mirroring: the mirrored half
    loses its highlights (tone 4 -> 3, 3 -> 2), so the light stays on the left;
  * the legs, the arm swing and the props follow a pose per frame (gait), like the hero's legs;
  * facing left with a one-hand prop is drawn on its own (the prop stays in the same hand) and then
    mirrored; anything else facing left is the mirror of facing right.

Frames: npc.<id>.<idle|walk>.<down|up|right|left>.<n>.png, 32x56, feet at the bottom centre (row 55).
"""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "art_proto"))
from pixel import Canvas, mirror  # noqa: E402,F401

W, H = 32, 56
DIRS = ("down", "up", "right", "left")
ACTIONS = {"idle": 4, "walk": 6}


# ------------------------------------------------------------------ maps

def legend(groups, inks=None):
    """groups: [("01234", "hair", 0), ...] -> {char: (material, tone)}; inks: {char: (material, tone, "#rgb")}."""
    out = {}
    for chars, mat, start in groups:
        for i, ch in enumerate(chars):
            out[ch] = (mat, start + i)
    for ch, v in (inks or {}).items():
        out[ch] = v
    return out


def rows_of(text, width=W):
    rows = [r for r in text.strip("\n").split("\n")]
    for r in rows:
        assert len(r) <= width, (len(r), r)
    return [r.ljust(width, ".") for r in rows]


def half(text):
    """A front / back map given as its left 16 columns: the right half is its mirror (marked by
    upper bit: the stamp drops its highlights)."""
    rows = []
    for r in text.strip("\n").split("\n"):
        assert len(r) == 16, (len(r), r)
        rows.append(r + r[::-1])
    return rows


def stamp(c, rows, x0, y0, leg, mirrored=False, shift=None, skip=()):
    """Places a map with its top-left at (x0, y0). mirrored: columns >= 16 are the mirrored half
    (their highlights drop one tone). shift(row, col, ch) -> (dx, dy) moves single pixels
    (a swinging hem, breathing). Characters in `skip` are not drawn."""
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == "." or ch in skip:
                continue
            v = leg[ch]
            m, t = v[0], v[1]
            if mirrored and x >= 16 and t is not None and t >= 3 and len(v) == 2:
                t -= 1
            dx, dy = shift(y, x, ch) if shift else (0, 0)
            px, py = x0 + x + dx, y0 + y + dy
            c.put(px, py, m, t)
            if len(v) == 3:
                c.paint(px, py, v[2])


def anchor(rows, ch):
    for y, r in enumerate(rows):
        x = r.find(ch)
        if x >= 0:
            return x, y
    raise KeyError(ch)


def stamp_at(c, rows, at, ch, pos, leg, flip=False, darker=False):
    """Stamps a small map so that its anchor character `ch` lands on `pos`; returns where its '*'
    (hand) lands. flip mirrors the map; darker drops every tone by one (the far side)."""
    ax, ay = anchor(rows, at)
    hand = None
    for y, row in enumerate(rows):
        for x, c_ in enumerate(row):
            if c_ == ".":
                continue
            dx = (ax - x) if flip else (x - ax)
            px, py = round(pos[0]) + dx, round(pos[1]) + y - ay
            if c_ == "*":
                hand = (px, py)
            v = leg[c_]
            t = v[1]
            if darker and t is not None and t > 1:
                t -= 1
            c.put(px, py, v[0], t)
            if len(v) == 3:
                c.paint(px, py, v[2])
    return hand


# ------------------------------------------------------------------ geometry helpers

def capsule(c, x0, y0, x1, y1, r, mat, tone=None):
    xa, xb = int(min(x0, x1) - r - 1), int(max(x0, x1) + r + 1)
    ya, yb = int(min(y0, y1) - r - 1), int(max(y0, y1) + r + 1)
    dx, dy = x1 - x0, y1 - y0
    L = dx * dx + dy * dy or 1
    for y in range(ya, yb + 1):
        for x in range(xa, xb + 1):
            px, py = x + 0.5, y + 0.5
            t = max(0, min(1, ((px - x0) * dx + (py - y0) * dy) / L))
            if (px - x0 - t * dx) ** 2 + (py - y0 - t * dy) ** 2 <= r * r:
                c.put(x, y, mat, tone)


def shift_rows(c, y0, y1, dx):
    """Moves rows y0..y1-1 sideways by dx (a weight shift)."""
    if not dx:
        return
    for y in range(max(0, y0), min(H, y1)):
        for grid in (c.mat, c.tone, c.rgb):
            row = grid[y]
            grid[y] = ([None] * dx + row[:-dx]) if dx > 0 else (row[-dx:] + [None] * (-dx))


# ------------------------------------------------------------------ poses

class Pose:
    def __init__(self, **k):
        self.bob = 0  # whole body down (+)
        self.breath = 0  # chest and head up (+)
        self.near = (0, 0)  # side view: near foot (forward, lift); front: image-left foot
        self.far = (0, 0)
        self.arm_near = 0  # hand forward (+) / back (-)
        self.arm_far = 0
        self.sway = 0  # hems and hair tips lag (-1..1)
        self.shift = 0  # front view: upper body over the planted foot
        self.blink = False
        self.glint = 0
        self.nod = 0  # head down (+)
        self.prop = 0  # prop moves with the step (staff planted, spear bobbing)
        self.__dict__.update(k)


def gait(i, n=6, stride=3, lift=2, bob=1, arm=2):
    ph = 2 * math.pi * i / n
    s, cph = math.sin(ph), math.cos(ph)
    return Pose(
        bob=round(abs(s) * bob),
        near=(round(stride * s), round(max(0.0, cph) * lift)),
        far=(round(-stride * s), round(max(0.0, -cph) * lift)),
        arm_near=round(-arm * s),
        arm_far=round(arm * s),
        sway=round(1.2 * math.sin(ph - math.pi / 2)),
        shift=round(0.6 * s),
        glint=i % 3,
        prop=round(s * 2),
    )


def idle(i):
    # breathing in over two frames, out over two; a blink on the last; the hems settle
    return Pose(breath=(0, 1, 1, 0)[i], sway=(0, 0, 1, 0)[i], blink=i == 3, glint=(0, 1, 2, 1)[i], nod=(0, 0, 0, 0)[i])


# ------------------------------------------------------------------ frames

class Npc:
    """A villager: subclasses draw a view (front / back / side) for a pose."""

    id = "npc"
    ramps = {}
    walk_gait = dict(stride=3, lift=2, bob=1, arm=2)

    def canvas(self):
        return Canvas(W, H, self.ramps)

    def pose(self, action, i):
        return idle(i) if action == "idle" else gait(i, 6, **self.walk_gait)

    def front(self, p, back=False):  # pragma: no cover - per character
        raise NotImplementedError

    def side(self, p, swap=False):  # pragma: no cover - per character
        raise NotImplementedError

    # facing left: a prop in one hand stays in that hand (drawn on its own)
    own_left = True

    def frame(self, action, d, i):
        p = self.pose(action, i)
        if d == "down":
            return self.front(p).colours()
        if d == "up":
            q = Pose(**{**p.__dict__, "near": p.far, "far": p.near, "arm_near": p.arm_far, "arm_far": p.arm_near})
            return self.front(q, back=True).colours()
        if d == "right":
            return self.side(p).colours()
        if self.own_left:
            return mirror(self.side(p, swap=True).colours())
        return mirror(self.side(p).colours())

    def frames(self):
        out = {}
        for action, n in ACTIONS.items():
            for d in DIRS:
                for i in range(n):
                    out[f"npc.{self.id}.{action}.{d}.{i}"] = self.frame(action, d, i)
        return out
