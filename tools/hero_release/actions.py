"""Stage 2 of the hero's release art: every action besides idle / walk / run.

Each action is a list of key poses per view ("down" = facing the viewer, "up" = the back, "side" =
facing right; left is the mirror). A pose sets the body (gen_hero.Pose: crouch via bob, lean, feet,
cloak and hair sway, blink) and, unlike stage 1, places the HANDS explicitly and adds PROPS:

  * hands — {"R": (x, y), "L": (x, y)} in the 32-px frame; "R" is the sword hand (his right).
    Front view: his right is on the image's left; back view: on the right; side view: R is the near
    arm (drawn over the body), L the far arm (drawn behind it).
  * props — the sword (steel blade, gold guard), the bow (wood, string, arrow), the shield (wood face,
    steel rim, gold star boss): drawn from the hands, at real angles, a pixel at a time.
  * width — sword and bow frames are 48 px wide (the body stays centred, the feet on the same spot) so
    a swing is never cut off; the game anchors every frame at the feet's centre.
  * water — swimming: everything below the water line is hidden, ripples ring the body.

The glider canopy, the slash trail and the aim line stay game effects (src/view/gameView.js); the
hero's frames only show him holding / swinging. Pure drawing data, run from gen_hero.py.
"""

import math

from pixel import Canvas

WIDE = 48

# ---------------------------------------------------------------- canvas helpers


def widen(c, w):
    """The frame copied into a wider one, centred (the feet stay at the centre)."""
    if w == c.w:
        return c
    out = Canvas(w, c.h, {})
    out.ramps = c.ramps
    ox = (w - c.w) // 2
    for y in range(c.h):
        for x in range(c.w):
            out.mat[y][x + ox], out.tone[y][x + ox], out.rgb[y][x + ox] = c.mat[y][x], c.tone[y][x], c.rgb[y][x]
    return out


class Layer:
    """Draws on a frame either over everything (front) or only into empty pixels (behind)."""

    def __init__(self, c, ox, behind=False):
        self.c, self.ox, self.behind = c, ox, behind

    def put(self, x, y, m, tone=None):
        x, y = int(round(x)) + self.ox, int(round(y))
        if self.behind and self.c.m(x, y) is not None:
            return
        self.c.put(x, y, m, tone)

    def paint(self, x, y, rgb):
        self.c.paint(int(round(x)) + self.ox, int(round(y)), rgb)

    def capsule(self, x0, y0, x1, y1, r, m, tone=None):
        dx, dy = x1 - x0, y1 - y0
        L = dx * dx + dy * dy or 1
        for y in range(int(min(y0, y1) - r - 1), int(max(y0, y1) + r + 2)):
            for x in range(int(min(x0, x1) - r - 1), int(max(x0, x1) + r + 2)):
                px, py = x + 0.5, y + 0.5
                t = max(0, min(1, ((px - x0) * dx + (py - y0) * dy) / L))
                if (px - x0 - t * dx) ** 2 + (py - y0 - t * dy) ** 2 <= r * r:
                    self.put(x, y, m, tone)

    def line(self, x0, y0, x1, y1, m, tone=None):
        n = int(max(abs(x1 - x0), abs(y1 - y0), 1))
        for i in range(n + 1):
            self.put(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n, m, tone)


# ---------------------------------------------------------------- arms and props


ARM = 5.6  # upper arm = forearm length (px)


def arm(L, sh, hand, sleeve_tone=None, cloak=True, cloak_tone=2):
    """Shoulder -> elbow -> gloved hand. The elbow bends outwards/down from the straight line.
    Over the body, the arm gets its own dark contour first so it reads against the cloak."""
    (sx, sy), (hx, hy) = sh, hand
    dx, dy = hx - sx, hy - sy
    n = math.hypot(dx, dy) or 1
    if n > ARM * 2 - 0.5:  # out of reach: the arm is straight, the hand as far as it goes
        k = (ARM * 2 - 0.5) / n
        hx, hy, dx, dy, n = sx + dx * k, sy + dy * k, dx * k, dy * k, ARM * 2 - 0.5
    # the elbow sits where upper arm and forearm (ARM px each) meet: the closer the hand, the more it bends
    bend = math.sqrt(max(0.0, ARM * ARM - (n / 2) ** 2))
    mx, my = (sx + hx) / 2, (sy + hy) / 2
    # bend away from the body's centre line (x = 15.5) and downwards
    px, py = -dy / n, dx / n
    if px * (mx - 15.5) + py * 1 < 0:
        px, py = -px, -py
    ex, ey = mx + px * bend, my + py * bend
    upper = "cloak" if cloak else "shirt"
    segs = ((sx, sy, ex, ey, 1.5, upper, cloak_tone if cloak else sleeve_tone),
            (ex, ey, hx, hy, 1.2, "shirt", sleeve_tone),
            (hx, hy, hx, hy, 1.5, "leather", sleeve_tone if sleeve_tone == 1 else None))
    if not L.behind:
        for x0, y0, x1, y1, r, m, _ in segs[1:]:
            L.capsule(x0, y0, x1, y1, r + 0.9, m, 0)
        L.capsule(sx, sy, ex, ey, 1.5 + 0.9, upper, 0)
    for x0, y0, x1, y1, r, m, t in segs:
        L.capsule(x0, y0, x1, y1, r, m, t)
    # the shoulder end stays inside the body: no contour there
    L.capsule(sx, sy, sx, sy, 1.6, upper, cloak_tone if cloak else sleeve_tone)


def sword(L, hx, hy, ang, length=13, tone_shift=0):
    """Held at the hand, pointing at `ang` degrees (0 = right, 90 = down)."""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    px, py = -uy, ux
    # pommel and grip behind the fist
    L.put(hx - ux * 3, hy - uy * 3, "gold", 3)
    L.line(hx - ux * 2, hy - uy * 2, hx - ux * 1, hy - uy * 1, "leather", 1)
    # cross-guard
    gx, gy = hx + ux * 1.6, hy + uy * 1.6
    L.line(gx - px * 2.4, gy - py * 2.4, gx + px * 2.4, gy + py * 2.4, "gold", 2)
    L.put(gx, gy, "gem", 3)
    # blade: a lit edge and a shaded edge, a bright tip
    for i in range(3, length):
        bx, by = hx + ux * i, hy + uy * i
        L.put(bx, by, "steel", 4 if i % 4 == 1 else 3)
        if i < length - 1:
            L.put(bx + px * 0.9, by + py * 0.9, "steel", 1 + tone_shift)
    L.put(hx + ux * length, hy + uy * length, "steel", 4)


def bow(L, hx, hy, ang, draw, arrow=True, reach=10):
    """A recurve bow held at the hand, facing `ang`; `draw` 0..1 pulls the string back."""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    px, py = -uy, ux
    pts = []
    for k in range(-reach, reach + 1):
        t = k / reach
        bend = 2.4 * (1 - t * t) - 0.8 * (abs(t) > 0.8)
        pts.append((hx + ux * bend + px * k, hy + uy * bend + py * k))
    for i, (x, y) in enumerate(pts):
        L.put(x, y, "wood", 3 if i < reach else 2)
    top, bot = pts[0], pts[-1]
    nock = (hx - ux * (1 + 7 * draw), hy - uy * (1 + 7 * draw))
    L.line(top[0], top[1], nock[0], nock[1], "bone", 4)
    L.line(bot[0], bot[1], nock[0], nock[1], "bone", 4)
    for x, y in (top, bot):
        L.put(x, y, "gold", 3)
    L.put(hx, hy, "leather", 2)
    if arrow and draw > 0:
        tip = (hx + ux * 4, hy + uy * 4)
        L.line(nock[0], nock[1], tip[0], tip[1], "wood", 3)
        L.put(tip[0], tip[1], "steel", 4)
        L.put(nock[0] - ux, nock[1] - uy, "gem", 3)  # blue fletching
    return nock


def shield(L, cx, cy, rx, ry):
    """A round wooden shield, steel rim, gold star boss (rx < ry: seen edge-on)."""
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            d = ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2
            if d <= 1:
                rim = d > 0.62
                lit = (x - cx) + (y - cy) < -1
                L.put(x, y, "steel" if rim else "wood", (3 if lit else 1) if rim else (3 if lit else 2))
    if rx >= 3:
        for dx, dy in ((0, -2), (0, 2), (-2, 0), (2, 0), (0, -1), (0, 1), (-1, 0), (1, 0)):
            L.put(cx + dx - 0.5, cy + dy - 0.5, "gold", 3 if dx <= 0 and dy <= 0 else 2)
        L.put(cx - 0.5, cy - 0.5, "gem", 4)
    else:
        L.line(cx - 0.5, cy - 2, cx - 0.5, cy + 2, "gold", 2)


def ripples(L, cx, y, half, phase):
    """The water line around the swimmer: a broken ring of light, moving with the strokes."""
    for k in range(-half - 2, half + 3):
        ry = y + (1 if abs(k) > half - 1 else 0)
        lit = (k + phase) % 4 in (0, 1)
        L.put(cx + k, ry, "water", 4 if lit else 3)
    for k in (-half - 4, half + 4):
        if (k > 0) == (phase % 2 == 0):
            L.put(cx + k, y + 1, "water", 4)


# ---------------------------------------------------------------- shoulders per view

SHOULDER = {
    "down": {"R": (9.5, 27), "L": (21.5, 27)},
    "up": {"R": (21.5, 27), "L": (9.5, 27)},
}


def shoulders(view, p):
    b = p.bob - p.breath
    if view == "side":
        return {"R": (16.5 + p.lean, 26 + b), "L": (15 + p.lean, 26 + b)}
    sx = p.shift
    return {k: (x + sx, y + b) for k, (x, y) in SHOULDER[view].items()}


def finish(c, p, view):
    """Arms, props and the water line over the drawn body; returns the (possibly wider) frame."""
    c = widen(c, p.width)
    ox = (p.width - 32) // 2
    front, behind = Layer(c, ox), Layer(c, ox, behind=True)
    sh = shoulders(view, p)
    b = p.bob - p.breath
    for when, fn in p.props:  # props behind the body (or behind the arms) first
        if when == "behind":
            fn(behind, b)
    if p.hands:
        for k in ("L", "R"):
            if k not in p.hands:
                continue
            hand = p.hands[k]
            hand = (hand[0], hand[1] + b)
            if view == "side":
                arm(behind if k == "L" else front, sh[k], hand, sleeve_tone=1 if k == "L" else None, cloak=k == "R")
            elif view == "up":
                # from behind: an arm reaching forward is hidden by the body; raised ones show
                arm(front if hand[1] < sh[k][1] + 4 or abs(hand[0] - 15.5) > 9 else behind, sh[k], hand, cloak_tone=3)
            else:
                arm(front, sh[k], hand, cloak=False)
    for when, fn in p.props:
        if when == "front":
            fn(front, b)
    if p.water is not None:
        wl = p.water
        for y in range(wl + 1, c.h):
            for x in range(c.w):
                c.put(x, y, None)
                c.mat[y][x] = None
        for when, fn in p.props:
            if when == "water":
                fn(front, b)
    return c


# ---------------------------------------------------------------- the poses
# Each entry: the Pose fields for one frame. Hands are given before the body's bob (added in finish).

def _sw(x, y, ang, length=13, when="front"):
    return (when, lambda L, b: sword(L, x, y + b, ang, length))


def _bow(x, y, ang, draw, when="front", arrow=True, reach=10):
    return (when, lambda L, b: bow(L, x, y + b, ang, draw, arrow, reach))


def _shield(x, y, rx, ry, when="front"):
    return (when, lambda L, b: shield(L, x, y + b, rx, ry))


def _ripple(cx, y, half, phase):
    return ("water", lambda L, b: ripples(L, cx, y, half, phase))


def jump(view, i):
    # 0 rising: knees tucked, arms up for balance; 1 falling: legs reach for the ground, hair and cloak lift
    if view == "side":
        return [
            dict(bob=-1, lean=1, near=(3, 5), far=(-2, 3), sway=1, flare=1, hands={"R": (24, 31), "L": (9, 31)}),
            dict(bob=0, lean=0, near=(2, 1), far=(-1, 0), sway=-1, flare=0, hands={"R": (25, 27), "L": (8, 25)}),
        ][i]
    return [
        dict(bob=-1, near=(0, 4), far=(0, 2), sway=1, hands={"R": (4, 34), "L": (27, 34)}),
        dict(bob=0, near=(0, 1), far=(0, 0), sway=-1, hands={"R": (3, 25), "L": (28, 25)}),
    ][i]


def land(view, i):
    # 0 the impact: deep crouch, arms out to catch the weight; 1 rising out of it
    if view == "side":
        return [
            dict(bob=5, lean=2, near=(2, 0), far=(-2, 0), sway=2, flare=0, hands={"R": (23, 33), "L": (11, 34)}),
            dict(bob=2, lean=1, near=(1, 0), far=(-1, 0), sway=1, hands={"R": (21, 34), "L": (13, 35)}),
        ][i]
    return [
        dict(bob=5, near=(0, 0), far=(0, 0), sway=2, hands={"R": (5, 34), "L": (26, 34)}),
        dict(bob=2, near=(0, 0), far=(0, 0), sway=1, hands={"R": (7, 35), "L": (24, 35)}),
    ][i]


def glide(view, i):
    # hanging from the glider: both hands up at the cords, legs swaying, the cloak streaming back
    lift = ((1, 3), (2, 2), (3, 1), (2, 2))[i]
    sway = (-1, 0, 1, 0)[i]
    if view == "side":
        return dict(bob=(0, -1, 0, 1)[i], lean=1, near=(2, lift[0] + 2), far=(-2, lift[1] + 1), sway=2, flare=(3, 4, 3, 2)[i],
                    hands={"R": (25, 19), "L": (23, 18)})
    return dict(bob=(0, -1, 0, 1)[i], near=(0, lift[0]), far=(0, lift[1]), sway=sway,
                hands={"R": (6, 17 + (i == 1)), "L": (25, 17 + (i == 3))})


def climb(view, i):
    # hands over hands on the wall: one reaches up while the opposite foot pushes
    up = (0, 1, 2, 1)[i]  # 0 right hand high, 2 left hand high
    hi, lo, mid = 13, 23, 18
    if view == "side":
        r_y = (hi, mid, lo, mid)[i]
        l_y = (lo, mid, hi, mid)[i]
        return dict(bob=(0, 1, 0, 1)[i], lean=2, near=((1, 6), (0, 3), (-1, 0), (0, 3))[i], far=((-1, 0), (0, 3), (1, 6), (0, 3))[i],
                    sway=0, hands={"R": (26 if r_y < 20 else 24, r_y), "L": (25 if l_y < 20 else 23, l_y)})
    r = (hi, mid, lo, mid)[i]
    l_ = (lo, mid, hi, mid)[i]
    # seen from behind (both down and up: he faces the wall)
    return dict(bob=(0, 1, 0, 1)[i], near=((0, 0), (0, 2), (0, 5), (0, 2))[i], far=((0, 5), (0, 2), (0, 0), (0, 2))[i],
                sway=(1, 0, -1, 0)[i], hands={"R": (24 - (r < 15), r), "L": (7 + (l_ < 15), l_)}, _back=True, _up=up)


def swim(view, i):
    # head and shoulders above the water; the arms stroke in turn, ripples move with them
    wl = 44
    stroke = ((0, 2), (1, 1), (2, 0), (1, 1))[i]
    if view == "side":
        return dict(bob=11, lean=3, sway=1, flare=2, hands={"R": (27 - stroke[0] * 2, 33 + stroke[0]), "L": (22 + stroke[1], 35)},
                    water=wl, props=(_ripple(17, wl, 9, i),))
    if view == "up":
        return dict(bob=11, sway=(1, 0, -1, 0)[i], hands={"R": (23 + stroke[0], 33 - stroke[0] * 2), "L": (8 - stroke[1], 33 - stroke[1] * 2)},
                    water=wl, props=(_ripple(15.5, wl, 10, i),))
    return dict(bob=11, sway=(1, 0, -1, 0)[i], hands={"R": (8 - stroke[0], 36 - stroke[0] * 2), "L": (23 + stroke[1], 36 - stroke[1] * 2)},
                water=wl, props=(_ripple(15.5, wl, 10, i),))


def dodge(view, i):
    # a quick low roll-dash: dip, tuck, the tuck rolling through, rising — the cloak wraps and trails
    if view == "side":
        return [
            dict(bob=3, lean=3, near=(3, 0), far=(-3, 1), sway=2, flare=2, hands={"R": (22, 33), "L": (12, 33)}),
            dict(bob=8, lean=5, near=(2, 4), far=(-4, 3), sway=3, flare=4, hands={"R": (23, 36), "L": (19, 37)}),
            dict(bob=7, lean=4, near=(1, 3), far=(-1, 4), sway=3, flare=3, hands={"R": (22, 37), "L": (19, 38)}),
            dict(bob=2, lean=2, near=(2, 0), far=(-2, 0), sway=2, flare=1, hands={"R": (21, 34), "L": (13, 34)}),
        ][i]
    return [
        dict(bob=3, near=(0, 0), far=(0, 1), sway=2, hands={"R": (8, 34), "L": (23, 34)}),
        dict(bob=8, near=(0, 4), far=(0, 3), sway=-2, hands={"R": (11, 37), "L": (20, 37)}),
        dict(bob=7, near=(0, 3), far=(0, 4), sway=2, hands={"R": (11, 38), "L": (20, 38)}),
        dict(bob=2, near=(0, 0), far=(0, 0), sway=1, hands={"R": (8, 35), "L": (23, 35)}),
    ][i]


# Sword swings. Front view: his right hand is on the image's left. The blade is shorter when it
# points towards / away from the viewer (foreshortened).
def attack1(view, i):
    # a horizontal cut: wind up high on the sword side, sweep across, follow through low, recover
    if view == "side":
        return [
            dict(bob=1, lean=-1, near=(2, 0), far=(-2, 0), sway=1, hands={"R": (13, 21), "L": (12, 32)}, props=(_sw(13, 21, -115),)),
            dict(bob=1, lean=2, near=(4, 0), far=(-3, 0), sway=2, flare=1, hands={"R": (24, 28), "L": (13, 33)}, props=(_sw(24, 28, -8),)),
            dict(bob=2, lean=3, near=(4, 0), far=(-3, 0), sway=2, flare=1, hands={"R": (23, 34), "L": (14, 34)}, props=(_sw(23, 34, 55),)),
            dict(bob=1, lean=1, near=(3, 0), far=(-2, 0), sway=1, hands={"R": (21, 34), "L": (13, 34)}, props=(_sw(21, 34, 95, 11),)),
        ][i] | {"width": WIDE}
    if view == "up":
        return [
            dict(bob=1, shift=1, sway=-1, hands={"R": (26, 22), "L": (9, 33)}, props=(_sw(26, 22, -60, 11),)),
            dict(bob=1, sway=0, hands={"R": (17, 22), "L": (9, 33)}, props=(_sw(17, 22, -95, 9, when="behind"),)),
            dict(bob=2, shift=-1, sway=1, hands={"R": (7, 26), "L": (10, 33)}, props=(_sw(7, 26, -165, 12),)),
            dict(bob=1, shift=-1, sway=1, hands={"R": (7, 30), "L": (10, 34)}, props=(_sw(7, 30, 160, 11),)),
        ][i] | {"width": WIDE}
    return [
        dict(bob=1, shift=-1, sway=1, hands={"R": (5, 22), "L": (22, 34)}, props=(_sw(5, 22, -120, 12, when="behind"),)),
        dict(bob=1, sway=0, hands={"R": (13, 33), "L": (22, 34)}, props=(_sw(13, 33, 75, 9),)),
        dict(bob=2, shift=1, sway=-1, hands={"R": (22, 35), "L": (24, 33)}, props=(_sw(22, 35, 15, 13),)),
        dict(bob=1, shift=1, sway=-1, hands={"R": (21, 35), "L": (24, 34)}, props=(_sw(21, 35, 50, 12),)),
    ][i] | {"width": WIDE}


def attack2(view, i):
    # the return cut: from low across to high on the other side
    if view == "side":
        return [
            dict(bob=2, lean=2, near=(3, 0), far=(-3, 0), sway=2, hands={"R": (22, 35), "L": (14, 34)}, props=(_sw(22, 35, 130, 12),)),
            dict(bob=1, lean=2, near=(4, 0), far=(-3, 0), sway=1, flare=1, hands={"R": (25, 29), "L": (13, 33)}, props=(_sw(25, 29, -25),)),
            dict(bob=0, lean=1, near=(4, 0), far=(-2, 0), sway=0, hands={"R": (24, 20), "L": (13, 31)}, props=(_sw(24, 20, -50, 12),)),
            dict(bob=1, lean=1, near=(3, 0), far=(-2, 0), sway=1, hands={"R": (23, 25), "L": (13, 33)}, props=(_sw(23, 25, -30, 12),)),
        ][i] | {"width": WIDE}
    if view == "up":
        return [
            dict(bob=2, shift=-1, sway=1, hands={"R": (8, 32), "L": (10, 34)}, props=(_sw(8, 32, 150, 11),)),
            dict(bob=1, sway=0, hands={"R": (16, 24), "L": (9, 33)}, props=(_sw(16, 24, -90, 9, when="behind"),)),
            dict(bob=0, shift=1, sway=-1, hands={"R": (26, 21), "L": (9, 32)}, props=(_sw(26, 21, -35, 12),)),
            dict(bob=1, shift=1, sway=-1, hands={"R": (25, 27), "L": (9, 33)}, props=(_sw(25, 27, -15, 11),)),
        ][i] | {"width": WIDE}
    return [
        dict(bob=2, shift=1, sway=-1, hands={"R": (22, 35), "L": (24, 33)}, props=(_sw(22, 35, 30, 12),)),
        dict(bob=1, sway=0, hands={"R": (15, 34), "L": (23, 34)}, props=(_sw(15, 34, 100, 9),)),
        dict(bob=0, shift=-1, sway=1, hands={"R": (5, 25), "L": (22, 33)}, props=(_sw(5, 25, -150, 13),)),
        dict(bob=1, shift=-1, sway=1, hands={"R": (6, 29), "L": (22, 34)}, props=(_sw(6, 29, -130, 12),)),
    ][i] | {"width": WIDE}


def attack3(view, i):
    # the finisher: crouch, both hands raise the sword high, a hop, the overhead slam, the impact, recover
    if view == "side":
        return [
            dict(bob=3, lean=0, near=(2, 0), far=(-3, 0), sway=1, hands={"R": (15, 30), "L": (14, 31)}, props=(_sw(15, 30, 160, 12, when="behind"),)),
            dict(bob=0, lean=-1, near=(2, 0), far=(-2, 0), sway=0, hands={"R": (12, 19), "L": (13, 20)}, props=(_sw(12, 19, -145, 13),)),
            dict(bob=-2, lean=0, near=(3, 4), far=(-2, 3), sway=-1, flare=2, hands={"R": (12, 17), "L": (13, 18)}, props=(_sw(12, 17, -120, 13),)),
            dict(bob=4, lean=3, near=(4, 0), far=(-3, 0), sway=2, flare=3, hands={"R": (24, 30), "L": (23, 31)}, props=(_sw(24, 30, 25, 14),)),
            dict(bob=5, lean=3, near=(4, 0), far=(-3, 0), sway=3, flare=2, hands={"R": (24, 33), "L": (23, 34)}, props=(_sw(24, 33, 40, 14),)),
            dict(bob=2, lean=1, near=(3, 0), far=(-2, 0), sway=1, flare=0, hands={"R": (21, 33), "L": (20, 34)}, props=(_sw(21, 33, 70, 12),)),
        ][i] | {"width": WIDE}
    if view == "up":
        return [
            dict(bob=3, sway=1, hands={"R": (18, 33), "L": (14, 33)}, props=(_sw(16, 33, 90, 10, when="behind"),)),
            dict(bob=0, sway=0, hands={"R": (17, 13), "L": (14, 13)}, props=(_sw(16, 12, -90, 11),)),
            dict(bob=-2, near=(0, 4), far=(0, 3), sway=-1, hands={"R": (17, 11), "L": (14, 11)}, props=(_sw(16, 10, -95, 11),)),
            dict(bob=4, sway=2, hands={"R": (18, 30), "L": (14, 30)}, props=(_sw(16, 27, -90, 10, when="behind"),)),
            dict(bob=5, sway=2, hands={"R": (18, 32), "L": (14, 32)}, props=(_sw(16, 29, -90, 9, when="behind"),)),
            dict(bob=2, sway=1, hands={"R": (21, 31), "L": (11, 33)}, props=(_sw(22, 31, -45, 10),)),
        ][i] | {"width": WIDE}
    return [
        dict(bob=3, sway=1, hands={"R": (13, 34), "L": (18, 34)}, props=(_sw(15, 33, -150, 12, when="behind"),)),
        dict(bob=0, shift=-1, sway=1, hands={"R": (5, 20), "L": (7, 21)}, props=(_sw(5, 20, -105, 13),)),
        dict(bob=-2, near=(0, 4), far=(0, 3), sway=-1, hands={"R": (5, 18), "L": (7, 19)}, props=(_sw(5, 18, -80, 13),)),
        dict(bob=4, sway=2, hands={"R": (14, 34), "L": (17, 34)}, props=(_sw(15.5, 34, 90, 12),)),
        dict(bob=5, sway=2, hands={"R": (14, 36), "L": (17, 36)}, props=(_sw(15.5, 36, 90, 13),)),
        dict(bob=2, sway=1, hands={"R": (11, 35), "L": (20, 34)}, props=(_sw(11, 35, 120, 12),)),
    ][i] | {"width": WIDE}


def bow_draw(view, i):
    # 0-2 drawing the string back to the cheek, 3 fully drawn, aiming
    d = (0.15, 0.45, 0.8, 1.0)[i]
    if view == "side":
        nx = 26 - round(9 * d)
        return dict(bob=0, lean=0, near=(3, 0), far=(-3, 0), sway=0, hands={"L": (26, 27), "R": (nx, 26 + (i == 0))},
                    props=(_bow(26, 27, 0, d),), width=WIDE)
    if view == "up":
        return dict(bob=0, sway=0, hands={"L": (13, 30), "R": (22 + round(3 * d), 27 + round(1 - d))},
                    props=(_bow(13, 30, -90, d, when="behind", arrow=False, reach=9),), width=WIDE)
    # facing the viewer: the bow upright in front of him, the arrow pointing out of the picture
    return dict(bob=0, sway=0, hands={"L": (17, 31), "R": (12 + round(-2 * d), 28 - round(2 * d))},
                props=(_bow(17, 31, 0, 0, arrow=False, reach=9), ("front", lambda L, b: (L.put(16, 31 + b, "steel", 4), L.put(16, 30 + b, "gem", 3) if i else None))), width=WIDE)


def guard(view, i):
    # 0 bringing the shield up, 1 braced behind it
    up = i == 1
    if view == "side":
        return dict(bob=1 + up, lean=1, near=(3, 0), far=(-3, 0), sway=up, hands={"R": (17, 34), "L": (22, 30 - up)},
                    props=(_shield(24 - (not up), 31 - up * 2, 2.6, 7 - (not up)),), width=WIDE)
    if view == "up":
        return dict(bob=1 + up, sway=0, hands={"L": (11, 32 - up * 2), "R": (22, 34)},
                    props=(_shield(15.5, 31 - up * 2, 6 + up, 7, when="behind"),), width=WIDE)
    return dict(bob=1 + up, sway=0, hands={"R": (8, 35), "L": (20, 32 - up * 2)},
                props=(_shield(18 - up, 34 - up * 3, 5.5 + up * 0.5, 6.5 + up * 0.5),), width=WIDE)


def hurt(view, i):
    # thrown back by the hit: head back, eyes shut, arms flung; then curling in against it
    if view == "side":
        return [
            dict(bob=1, lean=-2, near=(3, 1), far=(-2, 0), sway=-1, flare=0, blink=True, hands={"R": (23, 25), "L": (8, 27)}),
            dict(bob=2, lean=-1, near=(2, 0), far=(-2, 0), sway=0, blink=True, hands={"R": (20, 32), "L": (12, 33)}),
        ][i] | {"width": WIDE}
    return [
        dict(bob=1, sway=-1, blink=True, hands={"R": (4, 28), "L": (27, 28)}),
        dict(bob=2, sway=0, blink=True, hands={"R": (8, 33), "L": (23, 33)}),
    ][i] | {"width": WIDE}


def down(view, i):
    # collapsing: staggers, the knees give, kneels, slumps forward onto his hands
    if view == "side":
        return [
            dict(bob=1, lean=-2, near=(2, 0), far=(-2, 0), sway=-1, blink=True, hands={"R": (21, 30), "L": (10, 30)}),
            dict(bob=5, lean=0, near=(4, 0), far=(-3, 0), sway=1, blink=True, hands={"R": (19, 36), "L": (12, 37)}),
            dict(bob=10, lean=2, near=(5, 0), far=(-4, 0), sway=2, blink=True, hands={"R": (22, 42), "L": (20, 42)}),
            dict(bob=12, lean=4, near=(5, 0), far=(-4, 0), sway=2, blink=True, hands={"R": (24, 41), "L": (22, 42)}),
        ][i] | {"width": WIDE}
    return [
        dict(bob=1, sway=-1, blink=True, hands={"R": (6, 31), "L": (25, 31)}),
        dict(bob=5, sway=1, blink=True, hands={"R": (8, 37), "L": (23, 37)}),
        dict(bob=10, sway=2, blink=True, hands={"R": (7, 41), "L": (24, 41)}),
        dict(bob=12, sway=2, blink=True, hands={"R": (8, 41), "L": (23, 41)}),
    ][i] | {"width": WIDE}


STAGE2 = {
    "jump": (2, jump), "land": (2, land), "glide": (4, glide), "climb": (4, climb), "swim": (4, swim),
    "dodge": (4, dodge), "attack1": (4, attack1), "attack2": (4, attack2), "attack3": (6, attack3),
    "bow": (4, bow_draw), "guard": (2, guard), "hurt": (2, hurt), "down": (4, down),
}

# actions whose back view uses the front view's pose (symmetric): the hands swap sides
SHARED_BACK = {"jump", "land", "glide", "dodge", "hurt", "down"}
