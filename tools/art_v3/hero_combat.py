"""v3 hero, production (STYLE order 2), milestone 2: combat — attack 1-3, bow, guard, dodge, hurt.

The body is drawn by the same part functions as idle / walk / run (gen_hero_v3.frame for the front,
hero_views.side_frame / back_frame for the side and the back: hair locks, face map, cloak, gauntlets,
legs), so a fix to any part reaches every action. This module adds, per frame:
  * the pose — read from the approved v1 hero's own pose tables (tools/hero_release/actions.py, read
    only: body crouch/lean/feet/sway, where each hand is, the sword's angle and length, the bow's draw,
    the shield's size), every v1 pixel position x2 (v3 texel = 2 x v1 pixel + 1);
  * the arms to those hands (two-bone: sleeve / gauntlet with its 2 metal bands / leather fist);
  * the props, redrawn at 2x detail: the sword (pommel, leather grip, gold cross-guard with the blue
    gem, a 3-texel blade with a lit and a shaded edge and a tapered point), the recurve bow (2-texel
    limbs, gold tips, the string, the arrow with its steel point and blue fletching), the round shield
    (planks, steel rim, gold star boss with the gem).
Frames v1 draws 48 wide are 96 x 112 here (the body centred, the feet's centre the anchor).
Facing left: drawn only for the actions with a prop (v1's OWN_LEFT): the side pose with his sword arm
as the far arm (behind the body), the bow / shield arm near, then mirrored. Other actions: right
mirrored by the game.
"""

import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from hdkit import capsule, edge_band  # noqa: E402
from v3lib import Canvas, despeckle  # noqa: E402

V1_TOOLS = [os.path.join(HERE, "..", "art_proto"), os.path.join(HERE, "..", "hero_release")]

COMBAT = {"attack1": 4, "attack2": 4, "attack3": 6, "bow": 4, "guard": 2, "dodge": 4, "hurt": 2}
WIDE_ACTIONS = {"attack1", "attack2", "attack3", "bow", "guard", "hurt"}  # v1: 48 wide
OWN_LEFT = {"attack1", "attack2", "attack3", "bow", "guard"}


def _v1():
    for p in V1_TOOLS:
        if os.path.abspath(p) not in [os.path.abspath(q) for q in sys.path]:
            sys.path.append(os.path.abspath(p))  # appended: tools/hero_release/inspect.py must not shadow the stdlib
    import actions  # noqa: E402  (read only: the approved v1 pose tables)
    return actions


def v1_pose(action, view, i, left=False):
    """The v1 pose of one frame: body fields, hands, arms, props (as plain data)."""
    A = _v1()
    fn = A.STAGE2[action][1]
    v = "side" if view in ("right", "left") else view
    if v == "up" and action in A.SHARED_BACK:
        p = dict(fn("down", i))  # the front pose seen from behind: the same places, the hands' names swap
        p["hands"] = {{"R": "L", "L": "R"}[k]: xy for k, xy in (p.get("hands") or {}).items()}
    else:
        p = dict(fn(v, i))
    if left:
        p = A.for_left(p, action, i)
    props = []
    for pr in p.get("props", ()):
        when, fn_, key = pr[0], pr[1], (pr[2] if len(pr) > 2 else None)
        names = fn_.__code__.co_names
        cl = dict(zip(fn_.__code__.co_freevars, [c.cell_contents for c in (fn_.__closure__ or ())]))
        kind = "sword" if "sword" in names else ("bow" if "bow" in names else ("shield" if "shield" in names else "dots"))
        props.append(dict(kind=kind, when=when, key=key, **cl))
    p["props"] = props
    return p


def V(x):
    """A v1 pixel coordinate -> the v3 texel at its centre."""
    return 2 * x + 1


# ---------------------------------------------------------------- arms and props (wide canvas)

def arm_to(c, shoulder, hand, view, darker=False, sleeve="cloak", mid_x=32.0):
    """A two-bone arm: the sleeve from the shoulder to the elbow, the grey gauntlet (v1's 3 greys, 2
    metal bands) to the wrist, the leather fist at the hand."""
    sx, sy = shoulder
    hx, hy = hand
    d = math.hypot(hx - sx, hy - sy) or 1.0
    a, b = 11.0, 12.0
    if d > a + b - 1:
        a, b = d * a / (a + b), d * b / (a + b)
    cosA = max(-1.0, min(1.0, (a * a + d * d - b * b) / (2 * a * d)))
    A = math.acos(cosA)
    ux, uy = (hx - sx) / d, (hy - sy) / d
    # the elbow: of the two bends, the lower one (side view) or the one away from the body's middle
    best = None
    for sgn in (1, -1):
        ca, sa = math.cos(A * sgn), math.sin(A * sgn)
        e = (sx + a * (ux * ca - uy * sa), sy + a * (ux * sa + uy * ca))
        score = e[1] if view == "side" else abs(e[0] - mid_x) + 0.3 * e[1]
        if best is None or score > best[0]:
            best = (score, e)
    ex, ey = best[1]
    wx, wy = hx - ux * 3.0, hy - uy * 3.0
    upper = capsule(c, (sx, sy), (ex, ey), 3.6)
    c.fill(upper, sleeve)
    c.shade_part(upper, tones=(1, 2, 3, 4) if sleeve == "cloak" else (2, 3, 3, 4), norm=True)
    g = capsule(c, (ex, ey), (wx, wy), 3.7)
    c.fill(g, "shirt")
    c.shade_part(g, tones=(0, 0, 1, 1, 3), norm=True, light=(-0.9, -0.2, 0.4))
    L = math.hypot(wx - ex, wy - ey) or 1
    px, py = -(wy - ey) / L, (wx - ex) / L
    for t in (0.25, 0.7):
        bx, by = ex + (wx - ex) * t, ey + (wy - ey) * t
        c.set_tone(c.m_line([(bx - px * 4, by - py * 4), (bx + px * 4, by + py * 4)], 1.2) & g, 0)
    fist = c.m_ellipse(hx, hy, 3.7, 3.9)
    if darker:
        c.set_tone(upper | g, 1)
    return fist


def draw_fist(c, fist, darker=False):
    c.fill(fist, "leather")
    c.shade_part(fist, tones=(1, 2, 3, 4) if not darker else (1, 1, 2, 3), norm=True)
    ys, xs = np.nonzero(fist)
    if len(ys):  # the knuckles' light and one finger groove
        c.put(int(xs.min()) + 1, int(ys.min()) + 1, "leather", 5 if not darker else 3)
        my = int(ys.mean())
        for x in range(int(xs.min()) + 2, int(xs.max())):
            if fist[my, x] and (x - xs.min()) % 3 == 0:
                c.put(x, my, "leather", 1)


def sword(c, hx, hy, ang, length):
    """v1's sword at 2x: pommel, grip, cross-guard with the gem, the blade with a lit and a shaded edge."""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    px, py = -uy, ux
    if px * -0.6 + py * -0.8 < 0:  # the lit edge faces the top left
        px, py = -px, -py
    L = 2 * length
    c.fill(c.m_line([(hx - ux * 5, hy - uy * 5), (hx + ux * 1, hy + uy * 1)], 2.2), "leather", 2)  # grip
    c.fill(c.m_ellipse(hx - ux * 6, hy - uy * 6, 1.6, 1.6), "gold", 3)  # pommel
    c.put(int(round(hx - ux * 6 - 0.5)), int(round(hy - uy * 6 - 0.5)), "gold", 5)
    gx, gy = hx + ux * 3.5, hy + uy * 3.5
    guard = c.m_line([(gx - px * 5, gy - py * 5), (gx + px * 5, gy + py * 5)], 2.2)
    c.fill(guard, "gold", 3)
    c.fill(guard & c.m_line([(gx + px * 1.5, gy + py * 1.5), (gx + px * 5, gy + py * 5)], 2.2), "gold", 4)
    c.fill(c.m_ellipse(gx, gy, 1.3, 1.3), "gem", 3)
    b0 = 5.0
    core = c.m_line([(hx + ux * b0, hy + uy * b0), (hx + ux * (L - 3), hy + uy * (L - 3))], 3.0)
    c.fill(core, "steel", 3)
    lit = c.m_line([(hx + ux * b0 + px * 1.0, hy + uy * b0 + py * 1.0), (hx + ux * (L - 3) + px * 1.0, hy + uy * (L - 3) + py * 1.0)], 1.1)
    shd = c.m_line([(hx + ux * b0 - px * 1.0, hy + uy * b0 - py * 1.0), (hx + ux * (L - 3) - px * 1.0, hy + uy * (L - 3) - py * 1.0)], 1.1)
    c.set_tone(lit & core, 4)
    c.set_tone(shd & core, 1)
    tip = c.m_line([(hx + ux * (L - 3), hy + uy * (L - 3)), (hx + ux * L, hy + uy * L)], 1.6)
    c.fill(tip, "steel", 4)
    c.put(int(hx + ux * (b0 + 3) + px), int(hy + uy * (b0 + 3) + py), "steel", 5)  # the glint


def bow(c, hx, hy, ang, draw, arrow=True, reach=10, nock_at=None):
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    px, py = -uy, ux
    R = 2 * reach
    pts = []
    for k in range(-R, R + 1, 2):
        t = k / R
        bend = 4.8 * (1 - t * t) - 1.6 * (abs(t) > 0.8)
        pts.append((hx + ux * bend + px * k, hy + uy * bend + py * k))
    c.fill(c.m_line(pts, 3.4), "wood", 1)  # a dark edge round the limbs (they read over the tunic)
    limb = c.m_line(pts, 1.8)
    c.fill(limb, "wood", 3)
    c.set_tone(limb & c.m_line(pts[: len(pts) // 2 + 1], 1.8), 4)
    top, bot = pts[0], pts[-1]
    nock = nock_at or (hx - ux * (2 + 14 * draw), hy - uy * (2 + 14 * draw))
    string = c.m_line([top, nock], 1.0) | c.m_line([bot, nock], 1.0)
    c.fill(string & (c.mat == 0) | string & ~limb, "bone", 4)
    for x, y in (top, bot):
        c.fill(c.m_ellipse(x, y, 1.3, 1.3), "gold", 3)
    c.fill(c.m_ellipse(hx, hy, 2.0, 3.0), "leather", 2)  # the grip wrap
    if arrow and draw > 0:
        tip = (hx + ux * 7, hy + uy * 7)
        c.fill(c.m_line([nock, tip], 1.2), "wood", 3)
        c.fill(c.m_line([tip, (tip[0] + ux * 2, tip[1] + uy * 2)], 1.8), "steel", 4)
        fl = (nock[0] + ux * 2, nock[1] + uy * 2)
        c.fill(c.m_line([(fl[0] + px * 1.5, fl[1] + py * 1.5), (fl[0] - px * 1.5, fl[1] - py * 1.5)], 1.6), "gem", 3)
    return nock


def shield(c, cx, cy, rx, ry):
    """v1's round shield at 2x: wooden planks, a 2-texel steel rim, the gold star boss and the gem."""
    rx, ry = 2 * rx, 2 * ry
    face = c.m_ellipse(cx, cy, rx, ry)
    inner = c.m_ellipse(cx, cy, max(1.0, rx - 2), max(1.0, ry - 2))
    c.fill(face, "steel", 2)
    yy, xx = np.nonzero(face & ~inner)
    for y, x in zip(yy, xx):
        c.tone[y, x] = 4 if (x + 0.5 - cx) + (y + 0.5 - cy) < -1 else 1
    c.fill(inner, "wood", 2)
    for y, x in zip(*np.nonzero(inner)):
        t = 3 if (x + 0.5 - cx) + (y + 0.5 - cy) < 0 else 2
        if rx >= 6 and int(x - cx + 100) % 5 == 0:
            t = 1  # the planks' seams
        c.tone[y, x] = t
    if rx >= 6:
        star = c.m_line([(cx, cy - 4), (cx, cy + 4)], 1.6) | c.m_line([(cx - 4, cy), (cx + 4, cy)], 1.6)
        c.fill(star & inner, "gold", 3)
        c.fill(c.m_ellipse(cx, cy, 1.6, 1.6), "gem", 4)
    else:
        c.fill(c.m_line([(cx, cy - ry + 3), (cx, cy + ry - 3)], 1.6) & inner, "gold", 3)


# ---------------------------------------------------------------- composing a frame

def paste(dst, src, ox):
    """Copy every drawn texel of src (64 wide) onto dst at x offset ox (materials matched by name)."""
    for k, name in enumerate(src.names):
        if k == 0:
            continue
        sel = src.mat == k
        if not sel.any():
            continue
        kd = dst.mid(name)
        ys, xs = np.nonzero(sel)
        dst.mat[ys, xs + ox] = kd
        dst.tone[ys, xs + ox] = src.tone[ys, xs]
    for (x, y), rgb in src.ink.items():
        dst.ink[(x + ox, y)] = rgb


def shoulders(view, oy, lean):
    if view == "down":
        return {"R": (12.0, 53.0 + oy), "L": (52.0, 53.0 + oy)}
    if view == "up":
        return {"R": (52.0, 53.0 + oy), "L": (12.0, 53.0 + oy)}
    return {"R": (34.0 + lean, 53.0 + oy), "L": (30.0 + lean, 53.0 + oy)}  # near, far (facing right)


def build(action, view, i, H, HV):
    """One combat frame (a Canvas). H: gen_hero_v3, HV: hero_views."""
    left = view == "left" and action in OWN_LEFT
    p = v1_pose(action, view, i, left=left)
    width = 96 if action in WIDE_ACTIONS else 64
    ox = (width - 64) // 2
    bob = p.get("bob", 0)
    oy = 2 * bob
    blink = bool(p.get("blink", False))
    near, far = p.get("near", (0, 0)), p.get("far", (0, 0))
    lean = 2 * p.get("lean", 0)
    sway = p.get("sway", 0)
    v = "side" if view in ("right", "left") else view
    # an arm whose v1 pose is "down" (hanging) is the body's own arm (the same as idle); the others
    # are drawn to their hands below
    poses = p.get("arms") or {}
    own = {k for k in (p.get("hands") or {}) if poses.get(k) == "down"}
    if v == "down":
        off = {s for s, k in ((-1, "R"), (1, "L")) if k not in own}
        body = H.frame(oy=oy, sway=sway, feet=(-2 * far[1], -2 * near[1]), no_arms=off, finish=False, blink=blink)
    elif v == "up":
        off = {s for s, k in ((-1, "L"), (1, "R")) if k not in own}
        body = HV.back_frame(H.RAMPS, oy=oy, sway=sway, feet=(2 * far[1], 2 * near[1]), no_arms=off, finish=False)
    else:
        nk, fk = ("L", "R") if left else ("R", "L")
        off = {s for s, k in ((0, fk), (1, nk)) if k not in own}
        body = HV.side_frame(H.RAMPS, H.EYE, H.BLUSH, H.MOUTH, oy=oy, sway=sway, lean=lean,
                             legs=((2 * far[0], 2 * far[1], 0), (2 * near[0], 2 * near[1], 0)),
                             cloak_fly=0.3 * p.get("flare", 0), no_arms=off, finish=False, blink=blink)
    c = Canvas(width, 112, H.RAMPS)
    sh = shoulders(v, oy, lean)
    if left:  # facing left (drawn facing right, then mirrored): his left arm is the near one
        sh = {"R": sh["L"], "L": sh["R"]}
    hands = {k: (V(x), V(y + bob)) for k, (x, y) in (p.get("hands") or {}).items()}
    if left and "R" in hands:  # the sword hand at full stretch ahead (v1's "reach" for the far arm)
        x, y = hands["R"]
        if (p.get("arms") or {}).get("R") == "reach":
            hands["R"] = (x + 4, y)
    behind, front = [], []
    for k, hp in hands.items():
        if k in own:
            continue
        s = sh[k]
        if v == "side":
            far_arm = (k == "R") if left else (k == "L")
            raised = False
        else:
            far_arm = False
            raised = hp[1] < s[1] - 10
        hidden_back = v == "up" and abs(hp[0] - 32) < 15 and hp[1] > s[1] - 2  # an arm in front of him, seen from behind
        layer = behind if (far_arm or raised or hidden_back) else front
        darker = far_arm or (v == "down" and k == "L") or (v == "up" and k == "R")
        # front view, the bow hand in front of the body: the arm stays under the cloak, only the fist shows
        bow_hand = v == "down" and any(pr["kind"] == "bow" and pr["key"] == k for pr in p["props"])
        # seen from behind, a hand reaching across to the other side: the arm is in front of him (hidden)
        bow_hand = bow_hand or (v == "up" and (hp[0] - 32) * (s[0] - 32) < 0 and abs(hp[0] - 32) > 12)
        layer.append(("fist", k, s, hp, darker) if bow_hand else ("arm", k, s, hp, darker))
    for pr in p["props"]:
        key = pr["key"]
        in_back = pr["when"] == "behind" or any(e[1] == key and e[0] == "arm" for e in behind)
        if left and (action, i) in {("attack2", 0)} and key == "R":
            in_back = False
        (behind if in_back else front).append(("prop", key, pr))

    def run(items):
        fists = []
        for it in items:
            if it[0] == "fist":
                fists.append((c.m_ellipse(it[3][0] + ox, it[3][1], 3.7, 3.9), it[4]))
            if it[0] == "arm":
                _, k, s, hp, darker = it
                fists.append((arm_to(c, (s[0] + ox, s[1]), (hp[0] + ox, hp[1]), v, darker,
                                     sleeve="shirt" if v == "side" else "cloak", mid_x=32.0 + ox), darker))
        for it in items:
            if it[0] != "prop":
                continue
            pr = it[2]
            kind = pr["kind"]
            if kind == "sword":
                hx, hy = V(pr["x"]), V(pr["y"] + bob)
                if pr["key"] in hands:
                    hx, hy = hands[pr["key"]]
                sword(c, hx + ox, hy, pr["ang"], pr["length"])
            elif kind == "bow":
                hx, hy = V(pr["x"]), V(pr["y"] + bob)
                nock = None
                if pr.get("to_hand") and "R" in hands:
                    nock = (hands["R"][0] + ox, hands["R"][1])
                bow(c, hx + ox, hy, pr["ang"], pr["draw"], pr.get("arrow", True), pr.get("reach", 10), nock)
            elif kind == "shield":
                shield(c, V(pr["x"]) + ox, V(pr["y"] + bob), pr["rx"], pr["ry"])
            elif kind == "dots":  # the front view's arrow point at the bow (pointing out of the picture)
                c.fill(c.m_ellipse(V(16) + ox, V(31 + bob), 1.6, 1.6), "steel", 4)
                if i:
                    c.fill(c.m_ellipse(V(16) + ox, V(30 + bob) - 1, 1.4, 1.2), "gem", 3)
        for fist, darker in fists:
            draw_fist(c, fist, darker)

    run(behind)
    paste(c, body, ox)
    run(front)
    despeckle(c, loose=("hair", "cloak"))
    edge_band(c, "cloak", 1)
    c.outline()
    c.shadow_band()
    return c


def frames_for(action, view, H, HV):
    """view: down, right, up, left (left only for OWN_LEFT; returned mirrored)."""
    out = []
    for i in range(COMBAT[action]):
        cv = build(action, view if view != "left" else "left", i, H, HV)
        out.append(cv)
    return out
