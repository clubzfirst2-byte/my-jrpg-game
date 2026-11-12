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
from hdkit import capsule, edge_band, gauntlet  # noqa: E402
from v3lib import Canvas, absorb_cloth_islands, despeckle, smooth_lone  # noqa: E402

V1_TOOLS = [os.path.join(HERE, "..", "art_proto"), os.path.join(HERE, "..", "hero_release")]

COMBAT = {"attack1": 4, "attack2": 4, "attack3": 6, "bow": 4, "guard": 2, "dodge": 4, "hurt": 2}
WIDE_ACTIONS = {"attack1", "attack2", "attack3", "bow", "guard", "hurt", "jump", "down"}  # v1: 48 wide
REST = {"jump": 2, "land": 2, "glide": 4, "climb": 4, "swim": 4, "down": 4}  # milestone 3
ARMS_IN_FRONT = {"glide", "climb"}  # raised arms seen whole (v1 stage 5: the face kept clear)
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
    if p.pop("_back", False) and v != "side":  # climbing: he faces the wall in the down view too (v1)
        p = dict(fn("up", i))
        p.pop("_back", None)
        p["_view"] = "up"
    p.pop("_up", None)
    if left:
        p = A.for_left(p, action, i)
    props = []
    for pr in p.get("props", ()):
        when, fn_, key = pr[0], pr[1], (pr[2] if len(pr) > 2 else None)
        names = fn_.__code__.co_names
        cl = dict(zip(fn_.__code__.co_freevars, [c.cell_contents for c in (fn_.__closure__ or ())]))
        kind = "sword" if "sword" in names else ("bow" if "bow" in names else ("shield" if "shield" in names else
                                                   ("ripple" if "ripples" in names else "dots")))
        props.append(dict(kind=kind, when=when, key=key, **cl))
    p["props"] = props
    return p


A_SHARED_BACK = {"jump", "land", "dodge", "hurt", "down"}  # v1 actions.SHARED_BACK


def ripples(c, cx, y, half, phase):
    """v1's water line at 2x: a broken ring of light round the swimmer, moving with the strokes."""
    for k in range(-half - 4, half + 5):
        ry = y + (2 if abs(k) > half - 2 else 0)
        lit = ((k // 2) + phase) % 4 in (0, 1)
        for d in (0, 1):
            c.put(int(cx + k), int(ry + d), "water", (4 if lit else 3) if d == 0 else 2)
    for k in (-half - 8, half + 8):
        if (k > 0) == (phase % 2 == 0):
            c.put(int(cx + k), y + 2, "water", 4)
            c.put(int(cx + k + 1), y + 2, "water", 4)


def V(x):
    """A v1 pixel coordinate -> the v3 texel at its centre."""
    return 2 * x + 1


# ---------------------------------------------------------------- arms and props (wide canvas)

def arm_to(c, shoulder, hand, view, darker=False, sleeve="cloak", mid_x=32.0):
    """A two-bone arm: the sleeve from the shoulder to the elbow, the grey gauntlet (v1's 3 greys, 2
    metal bands) to the wrist, the leather fist at the hand."""
    sx, sy = shoulder
    hx, hy = hand
    hx, hy = min(max(hx, 7.0), c.w - 8.0), max(hy, 6.0)  # the fist stays inside the frame (3 texels)
    d = math.hypot(hx - sx, hy - sy) or 1.0
    # hero round 3: the bones follow the reach (each 0.55 of it, 6..12 texels): an arm held out is
    # nearly straight with the fist at its end, as in v1's arm maps, not folded back on itself
    a = b = min(12.0, max(6.0, 0.55 * d))
    if d > a + b - 1:
        a = b = d / 2
    cosA = max(-1.0, min(1.0, (a * a + d * d - b * b) / (2 * a * d)))
    A = math.acos(cosA)
    ux, uy = (hx - sx) / d, (hy - sy) / d
    # the elbow: of the two bends, the lower one (side view) or the one away from the body's middle
    best = None
    for sgn in (1, -1):
        ca, sa = math.cos(A * sgn), math.sin(A * sgn)
        e = (sx + a * (ux * ca - uy * sa), sy + a * (ux * sa + uy * ca))
        score = e[1] if view == "side" else e[1] - 0.3 * abs(e[0] - mid_x)
        # hero round 3: in the front / back view the fist is always the arm's outer end (v1): an elbow
        # further out than the fist (the arm folding back in) is never chosen
        if view != "side" and abs(e[0] - mid_x) > abs(hx - mid_x) + 1:
            score -= 1000
        if best is None or score > best[0]:
            best = (score, e)
    ex, ey = best[1]
    ex = min(max(ex, 7.0), c.w - 8.0)  # the elbow too (its round end 3 texels inside the frame)
    wx, wy = hx - ux * 3.0, hy - uy * 3.0
    upper = capsule(c, (sx, sy), (ex, ey), 3.6)
    c.fill(upper, sleeve)
    c.shade_part(upper, tones=(1, 2, 3, 4) if sleeve == "cloak" else (2, 3, 3, 4), norm=True)
    g = capsule(c, (ex, ey), (wx, wy), 3.7)
    c.fill(g, "shirt")
    gauntlet(c, g, (ex, ey), (wx, wy))
    fist = c.m_ellipse(hx, hy, 3.7, 3.9)
    if darker:  # the far arm: the sleeve one tone down, the gauntlet's light line to mid grey
        c.set_tone(upper & (c.mat == c.mid(sleeve)), 1)  # (not the gauntlet where the two overlap)
        c.tone[g & (c.tone == 3) & (c.mat == c.mid("shirt"))] = 1
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
    while L > 6:  # the point (and the blade's width) stays 4 texels inside the frame (no cut blade)
        tx, ty = hx + ux * L, hy + uy * L
        if 4 <= tx <= c.w - 5 and ty >= 4:
            break
        L -= 1
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
    R = int(round(2 * reach))
    pts = []
    for k in range(-R, R + 1, 2):
        t = k / R
        bend = 4.8 * (1 - t * t) - 1.6 * (abs(t) > 0.8)
        pts.append((hx + ux * bend + px * k, hy + uy * bend + py * k))
    # a dark edge round the limbs, then the limb in the darker browns: the bow reads over the white
    # tunic (inspection, milestone 2: the front bow was lost in the clothes)
    c.fill(c.m_line(pts, 4.2), "wood", 0)
    limb = c.m_line(pts, 2.2)
    c.fill(limb, "wood", 2)
    c.set_tone(limb & c.m_line(pts[: len(pts) // 2 + 1], 2.2), 3)
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


def shoulders_v1(view, lean, left=False):
    """v1's shoulder points (tools/hero_release/actions.py SHOULDER / shoulders())."""
    if view == "down":
        return {"R": (9.5, 27), "L": (21.5, 27)}
    if view == "up":
        return {"R": (21.5, 27), "L": (9.5, 27)}
    near, far = (16.5 + lean, 26), (15 + lean, 26)
    return {"R": far, "L": near} if left else {"R": near, "L": far}


def tweak(action, v, i, hands, sh, lean, oy):
    """Hero round 3 (inspection P2): hands moved where the v3 head is bigger than v1's x 2."""
    if v == "up" and action in ("attack1", "attack2") and i == 1 and "R" in hands:
        x, y = hands["R"]  # round 4: the fist 3-4 texels further in, so 10+ texels of blade show
        hands["R"] = (min(x, 60.0), y)
    if v != "side":
        return
    if action == "bow" and "L" in hands:  # the bow below the face, in front of the chest
        x, y = hands["L"]
        hands["L"] = (x, y + 8)
    if action == "attack3" and i in (1, 2) and "R" in hands:  # fist and blade ahead of the profile
        x, y = hands["R"]
        hands["R"] = (max(x, 60.0 + lean), y)



def build(action, view, i, H, HV):
    """One combat frame (a Canvas). H: gen_hero_v3, HV: hero_views."""
    left = view == "left" and action in OWN_LEFT
    p = v1_pose(action, view, i, left=left)
    width = 96 if action in WIDE_ACTIONS else 64
    ox = (width - 64) // 2
    bob = p.get("bob", 0)
    oy = max(2 * bob, -1)  # a hop lifts the body 1 texel at most (round 4: v1's crown reaches row 2)
    blink = bool(p.get("blink", False))
    near, far = p.get("near", (0, 0)), p.get("far", (0, 0))
    lean = 2 * p.get("lean", 0)
    sway = p.get("sway", 0)
    v = p.get("_view") or ("side" if view in ("right", "left") else view)
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
    # hero round 3: each hand is placed from ITS shoulder: v3 shoulder + 2 x (v1 hand - v1 shoulder), so a
    # hand v1 holds out past the shoulder is out past the v3 shoulder too (the v3 body is wider than v1 x 2)
    s1 = shoulders_v1(v, p.get("lean", 0), left)

    def T(k, x, y):
        return (sh[k][0] + 2 * (x - s1[k][0]), sh[k][1] + 2 * (y - s1[k][1]))
    hands = {k: T(k, x, y) for k, (x, y) in (p.get("hands") or {}).items()}
    held = {pr["key"] for pr in p.get("props", ()) if pr["kind"] in ("sword", "bow")}
    for k in held & set(hands):  # a hand holding a sword or a bow: the one of the two placements nearer
        x0, y0 = (p["hands"][k])  # the body's middle, so the prop has room inside the frame
        vx = V(x0)
        if abs(vx - 32) < abs(hands[k][0] - 32):
            hands[k] = (vx, hands[k][1])
    tweak(action, v, i, hands, sh, lean, oy)
    for k, (x, y) in list(hands.items()):  # every hand (and what it holds) 7 texels inside the frame
        hands[k] = (min(max(x, 7.0 - ox), width - 8.0 - ox), max(y, 6.0))
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
        if action in ARMS_IN_FRONT:
            raised = hidden_back = False
            if v == "side" and hp[1] < s[1] - 8:  # round 4 (v1): the raised forearm stands upright in front
                hx_ = min(55.0 + min(lean, 4) * 0.5, width - 9.0 - ox)  # of the forehead (a grey
                hp = (hx_, 10.0 + oy)  # tube 14 texels tall), the fist above it; the upper arm goes behind the head
                hands[k] = hp
                behind.append(("arm", k, s, (hx_, 30.0 + oy), far_arm))
                front.append(("raised", k, s, hp, far_arm))
                continue
        if hidden_back and action in A_SHARED_BACK:  # v1: a small hand shows at the side of the cloak
            front.append(("fist", k, s, (10.0 if hp[0] < 32 else 54.0, hp[1]), True))
            continue
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
        if left and key == "R" and v == "side":  # facing left the sword is in the far hand: behind him (v1)
            in_back = True
        if left and (action, i) in {("attack2", 0)} and key == "R":
            in_back = False
        (behind if in_back else front).append(("prop", key, pr))

    def run(items):
        fists = []
        for it in items:
            if it[0] == "raised":  # the upright forearm in front of the forehead and its fist
                hx_, hy_ = it[3][0] + ox, it[3][1]
                g = capsule(c, (hx_, hy_ + 20), (hx_, hy_ + 4), 3.4)
                c.fill(g, "shirt")
                gauntlet(c, g, (hx_, hy_ + 20), (hx_, hy_ + 4))
                fists.append((c.m_ellipse(hx_, hy_, 3.6, 3.8), it[4]))
                continue
            if it[0] == "fist":
                fx = min(max(it[3][0] + ox, 6.0), c.w - 7.0)
                fists.append((c.m_ellipse(fx, it[3][1], 3.7, 3.9), it[4]))
            if it[0] == "arm":
                _, k, s, hp, darker = it
                fists.append((arm_to(c, (s[0] + ox, s[1]), (hp[0] + ox, hp[1]), v, darker,
                                     sleeve="cloak", mid_x=32.0 + ox), darker))  # round 3: the upper arm stays in the cloak
        for it in items:
            if it[0] != "prop":
                continue
            pr = it[2]
            kind = pr["kind"]
            if kind == "sword":
                hx, hy = hands[pr["key"]] if pr["key"] in hands else T(pr["key"] or "R", pr["x"], pr["y"])
                sword(c, hx + ox, hy, pr["ang"], pr["length"])  # (hands already moved by tweak())
            elif kind == "bow":
                hx, hy = hands.get("L") or T("L", pr["x"], pr["y"])
                nock = None
                if pr.get("to_hand") and "R" in hands:
                    nock = (hands["R"][0] + ox, hands["R"][1])
                reach = pr.get("reach", 10) * (0.8 if v == "side" else 1.0)  # side: the bow below the face (v1)
                bow(c, hx + ox, hy, pr["ang"], pr["draw"], pr.get("arrow", True), reach, nock)
            elif kind == "shield":
                sx_, sy_ = T("L", pr["x"], pr["y"])
                shield(c, sx_ + ox, sy_, pr["rx"], pr["ry"])
            elif kind == "ripple":
                pass  # drawn after the water line cuts the body (below)
            elif kind == "dots":  # the front view's arrow point at the bow (pointing out of the picture)
                c.fill(c.m_ellipse(V(16) + ox, V(31 + bob), 1.6, 1.6), "steel", 4)
                if i:
                    c.fill(c.m_ellipse(V(16) + ox, V(30 + bob) - 1, 1.4, 1.2), "gem", 3)
        for fist, darker in fists:
            draw_fist(c, fist, darker)

    run(behind)
    paste(c, body, ox)
    run(front)
    if action == "glide":  # the glider's cords from both fists, up out of the frame's top
        for it in front:
            if it[0] in ("arm", "fist", "raised"):
                hx, hy = it[3][0] + ox, it[3][1]
                c.fill(c.m_line([(hx, hy - 3), (hx + (2 if hx > 32 + ox else -2), 3)], 1.0) & (c.mat == 0), "bone", 3)
    if p.get("water") is not None:  # swimming: nothing below the water line, then the ripples ring him
        wl = V(p["water"]) - 1
        c.mat[wl:, :] = 0
        for (x, y) in [xy for xy in c.ink if xy[1] >= wl]:
            del c.ink[(x, y)]
        for pr in p["props"]:
            if pr["kind"] == "ripple":
                ripples(c, V(pr["cx"]) + ox, wl, 2 * pr["half"], pr["phase"])
    absorb_cloth_islands(c, limit=5)  # round 4: only 1-5 texel slivers are cleaned; a bigger piece stops the generator
    despeckle(c, loose=("hair", "cloak"))
    edge_band(c, "cloak", 1)
    c.outline()
    c.shadow_band()
    smooth_lone(c)  # round 4: fewer lone texels (the swings had up to 5.4 %)
    return c


def frames_for(action, view, H, HV):
    """view: down, right, up, left (left only for OWN_LEFT; returned mirrored)."""
    out = []
    for i in range({**COMBAT, **REST}[action]):
        cv = build(action, view if view != "left" else "left", i, H, HV)
        out.append(cv)
    return out
