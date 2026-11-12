"""v3 copy of tools/enemy_v2/anim.py (d900394): poses snap to texels (half v2 pixels), not whole pixels.

Key poses -> in-between frames (v2: 4-8 frames per action).

Each character's rig is driven by a Pose (numbers, tuples of numbers, and a few named states).
An action is written as KEY POSES at times 0..1; the frames in between are interpolated with
easing, so the motion has weight:
  * numbers and tuples of numbers ease between keys (smoothstep by default; "in" accelerates
    into a key -- a strike -- and "out" decelerates out of one -- a recovery);
  * named states (a staff "raise" / "thrust", an eye "open" / "shut", a defeat stage) switch at
    the key, they are drawn by hand in the rig and do not blend.

loop(): a cycle (idle, move): frame i is at t = i / n, the last key wraps to the first.
once(): a one-shot (windup, attack, hurt, defeat): frame i is at t = i / (n - 1), so the first
and last frames ARE the first and last keys (the wind-up ends on its held pose, the attack
starts on its release).
"""

import math


def _ease(f, kind):
    if kind == "in":
        return f * f
    if kind == "out":
        return 1 - (1 - f) * (1 - f)
    if kind == "lin":
        return f
    return f * f * (3 - 2 * f)


def _blend(a, b, f):
    if isinstance(a, bool) or isinstance(b, bool):
        return a if f < 0.5 else b
    if isinstance(a, int) and isinstance(b, int):  # counts and steps stay whole (write 1.0 for smooth)
        return int(math.floor(a + (b - a) * f + 0.5))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a + (b - a) * f
    if isinstance(a, tuple) and isinstance(b, tuple) and len(a) == len(b):
        return tuple(_blend(x, y, f) for x, y in zip(a, b))
    return a if f < 0.5 else b  # named states switch half-way


# fields that count things or pick a stage (they stay whole numbers); every other whole number in
# a key is eased as a float, so small moves (a 1-px bob) still spread over the in-betweens
INT_FIELDS = {"spin", "shards", "orbs", "sparks", "collapse", "pebbles", "open", "grains", "crack", "broken",
              "lying", "puddle", "fallen", "tendrils_n"}


def _floats(d):
    return {k: (float(v) if isinstance(v, int) and not isinstance(v, bool) and k not in INT_FIELDS else
                tuple(float(x) if isinstance(x, int) and not isinstance(x, bool) else x for x in v) if isinstance(v, tuple) else v)
            for k, v in d.items()}


def mix(Pose, a, b, f):
    """A key between two keys (f = 0 -> a, 1 -> b)."""
    base = _defaults(Pose)
    A, B = dict(base), dict(base)
    A.update(a)
    B.update(b)
    A, B = _floats(A), _floats(B)
    return {k: _blend(A[k], B[k], f) for k in A}


def _state(base, keys, t):
    """The pose dict at time t from keys [(t, dict, ease)]: blend the two keys around t."""
    full = []
    for k in keys:
        tk, d = k[0], k[1]
        ease = k[2] if len(k) > 2 else "smooth"
        dd = dict(base)
        dd.update(d)
        dd = _floats(dd)
        full.append((tk, dd, ease))
    if t <= full[0][0]:
        return dict(full[0][1])
    for (t0, d0, _), (t1, d1, e1) in zip(full, full[1:]):
        if t0 <= t <= t1:
            f = 0 if t1 == t0 else _ease((t - t0) / (t1 - t0), e1)
            return {k: _blend(d0[k], d1[k], f) for k in d0}
    return dict(full[-1][1])


def _defaults(Pose):
    return dict(Pose().__dict__)


def _snap(Pose, d):
    """Round 2: offsets and positions snap to whole pixels, so a body part moves as a block and
    its shading moves WITH it (painted once, carried) instead of being re-rasterised a fraction
    of a pixel away every frame ("boiling"). Shape-changing fields (sizes, angles, the slime's
    radii...) stay smooth: each module lists them in SMOOTH."""
    import sys
    smooth = getattr(sys.modules[Pose.__module__], "SMOOTH", set())

    def rnd(v):  # v3: to the nearest texel (half a v2 pixel), so in-betweens move in 1-texel steps
        return math.floor(v * 2 + 0.5) / 2

    out = {}
    for k, v in d.items():
        if k in smooth or isinstance(v, bool):
            out[k] = v
        elif isinstance(v, float):
            out[k] = rnd(v)
        elif isinstance(v, tuple) and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in v):
            out[k] = tuple(rnd(x) for x in v)
        else:
            out[k] = v
    return out


def loop(Pose, n, keys):
    base = _defaults(Pose)
    keys = list(keys) + [(1.0, keys[0][1]) + tuple(keys[0][2:])]
    return [Pose(**_snap(Pose, _state(base, keys, i / n))) for i in range(n)]


def once(Pose, n, keys):
    base = _defaults(Pose)
    return [Pose(**_snap(Pose, _state(base, keys, i / (n - 1)))) for i in range(n)]


def wave(i, n, amp=1.0, phase=0.0):
    """A sine step for small secondary motion (tail, cloak, hair) in a cycle of n frames."""
    return amp * math.sin(2 * math.pi * (i / n) + phase)


def name(out, action, poses, draw):
    for i, p in enumerate(poses):
        out[f"{action}.{i}"] = draw(p) if draw else p
    return out


def dissolve(Pose, draw, keys, remains, pools=(6, 10)):
    """A 6-frame defeat (round 2): three drawn keys (the hit, the buckle, the collapse), then the
    collapse MELTS over two frames (fx.melt: sinking, spreading, turning to murk, a pool), then the
    drawn remains. No frame holds and then pops."""
    from fx import FX
    poses = [Pose(**_snap(Pose, _floats(dict(_defaults(Pose), **k)))) for k in keys]
    frames = [draw(p) for p in poses]
    last = poses[-1]
    frames += [FX(draw(last), 0.62, 0.45, pools[0]), FX(draw(last), 0.34, 0.8, pools[1])]
    frames.append(draw(Pose(**_floats(dict(_defaults(Pose), **remains)))))
    return frames


def dissolve_from(draw, poses, remains, pools=(6, 10)):
    """The dissolve for a normal enemy: poses = the hit, the buckle, the collapse (Pose objects),
    remains = the last drawn pose."""
    from fx import FX
    last = poses[-1]
    return [draw(p) for p in poses] + [FX(draw(last), 0.62, 0.45, pools[0]), FX(draw(last), 0.34, 0.8, pools[1]), draw(remains)]


def boss(Pose, draw, K, patterns, out=None, phase2=()):
    """The core bosses' v2 actions from their key poses K (dicts of Pose fields):
      K["idle"], K["idle2"]: 4 keys of the breathing cycle (loop, 4 frames)
      K["move"]: 4 keys of the step cycle (loop, 6 frames)
      K["windup_<p>"]: (w0, w1) -- 4 frames: 80% toward w0 already (so even the first wind-up
                       frame reads by shape), w0, a step past it, w1 held
      K["attack_<p>"]: (a0, a1) -- 5 frames: the release a0, the STRIKE (an overshoot past a0,
                       accelerated into), a1, settling, back toward the rest pose
      K["hurt"]: 3 frames; K["stagger"]: (s0, s1) 4 frames; both again in phase 2 (hurt2,
      stagger2: the cracks / bared core stay)
      K["defeat"]: 3 drawn keys + K["remains"]: the dissolve (6 frames).
    A pattern in `phase2` is a phase-2 attack: its wind-up starts from and its attack returns to
    idle2, so the phase-2 marks stay on every frame."""
    out = {} if out is None else out
    idle = K["idle"][0]
    idle2 = K["idle2"][0]
    name(out, "idle", loop(Pose, 4, [(i / 4, k) for i, k in enumerate(K["idle"])]), draw)
    name(out, "move", loop(Pose, 6, [(i / 4, k) for i, k in enumerate(K["move"])]), draw)
    for p in patterns:
        rest = idle2 if p in phase2 else idle
        w0, w1 = K[f"windup_{p}"][:2]
        f0 = K[f"windup_{p}"][2] if len(K[f"windup_{p}"]) > 2 else mix(Pose, rest, w0, 0.9)  # an explicit first frame
        a0, a1 = K[f"attack_{p}"][:2]
        name(out, f"windup_{p}", once(Pose, 4, [(0.0, f0), (0.34, w0), (1.0, w1)]), draw)
        # the strike: a hand-set impact pose when given, else an overshoot past the release
        strike = K[f"attack_{p}"][2] if len(K[f"attack_{p}"]) > 2 else mix(Pose, rest, a0, 1.45)
        # round 3: the recovery is spread over the last three frames (strike -> follow-through ->
        # settling -> nearly at rest), no pop back to idle right after the strike
        name(out, f"attack_{p}", once(Pose, 5, [(0.0, a0), (0.25, strike, "in"), (0.5, mix(Pose, strike, a1, 0.45)),
                                                (0.75, mix(Pose, strike, rest, 0.7)), (1.0, mix(Pose, strike, rest, 0.9))]), draw)
    for suffix, base in (("", idle), ("2", idle2)):
        extra = {"phase2": True} if suffix else {}
        h = dict(K["hurt"], **extra)
        name(out, "hurt" + suffix, once(Pose, 3, [(0.0, h), (0.5, mix(Pose, h, base, 0.45)), (1.0, mix(Pose, h, base, 0.85))]), draw)
        s0, s1 = dict(K["stagger"][0], **extra), dict(K["stagger"][1], **extra)
        name(out, "stagger" + suffix, once(Pose, 4, [(0.0, s0), (0.5, s1), (1.0, mix(Pose, s1, base, 0.6))]), draw)
    name(out, "idle2", loop(Pose, 4, [(i / 4, k) for i, k in enumerate(K["idle2"])]), draw)
    name(out, "defeat", dissolve(Pose, draw, K["defeat"], K["remains"]), draw=None)
    return out


def boss_actions(patterns):
    return (("idle", 4), ("move", 6)) + tuple(x for p in patterns for x in ((f"windup_{p}", 4), (f"attack_{p}", 5))) + \
        (("hurt", 3), ("stagger", 4), ("idle2", 4), ("hurt2", 3), ("stagger2", 4), ("defeat", 6))
