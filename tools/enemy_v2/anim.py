"""Key poses -> in-between frames (v2: 4-8 frames per action).

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


def loop(Pose, n, keys):
    base = _defaults(Pose)
    keys = list(keys) + [(1.0, keys[0][1]) + tuple(keys[0][2:])]
    return [Pose(**_state(base, keys, i / n)) for i in range(n)]


def once(Pose, n, keys):
    base = _defaults(Pose)
    return [Pose(**_state(base, keys, i / (n - 1))) for i in range(n)]


def wave(i, n, amp=1.0, phase=0.0):
    """A sine step for small secondary motion (tail, cloak, hair) in a cycle of n frames."""
    return amp * math.sin(2 * math.pi * (i / n) + phase)


def name(out, action, poses, draw):
    for i, p in enumerate(poses):
        out[f"{action}.{i}"] = draw(p)
    return out


def boss(Pose, draw, K, patterns, out=None):
    """The core bosses' v2 actions from their key poses K (dicts of Pose fields):
      K["idle"], K["idle2"]: 4 keys of the breathing cycle (loop, 4 frames)
      K["move"]: 4 keys of the step cycle (loop, 6 frames)
      K["windup_<p>"]: (w0, w1) -- 4 frames: 80% toward w0 already (so even the first wind-up
                       frame reads by shape), w0, a step past it, w1 held
      K["attack_<p>"]: (a0, a1) -- 5 frames: the release a0, the strike past it (accelerated),
                       a1, settling, the recovery toward idle
      K["hurt"]: 3 frames (the hit, the recoil, recovering); K["stagger"]: (s0, s1) 4 frames;
      K["defeat"]: 6 explicit keys (the stages are drawn by the rig)."""
    out = {} if out is None else out
    idle = K["idle"][0]
    name(out, "idle", loop(Pose, 4, [(i / 4, k) for i, k in enumerate(K["idle"])]), draw)
    name(out, "move", loop(Pose, 6, [(i / 4, k) for i, k in enumerate(K["move"])]), draw)
    for p in patterns:
        w0, w1 = K[f"windup_{p}"]
        a0, a1 = K[f"attack_{p}"]
        name(out, f"windup_{p}", once(Pose, 4, [(0.0, mix(Pose, idle, w0, 0.8)), (0.34, w0), (1.0, w1)]), draw)
        name(out, f"attack_{p}", once(Pose, 5, [(0.0, a0), (0.25, mix(Pose, a0, a1, 0.6), "in"), (0.5, a1),
                                                (1.0, mix(Pose, a1, idle, 0.75))]), draw)
    h = K["hurt"]
    name(out, "hurt", once(Pose, 3, [(0.0, h), (0.5, mix(Pose, h, idle, 0.45)), (1.0, mix(Pose, h, idle, 0.85))]), draw)
    s0, s1 = K["stagger"]
    name(out, "stagger", once(Pose, 4, [(0.0, s0), (0.5, s1), (1.0, mix(Pose, s1, idle, 0.6))]), draw)
    name(out, "idle2", loop(Pose, 4, [(i / 4, k) for i, k in enumerate(K["idle2"])]), draw)
    name(out, "defeat", [Pose(**_floats(dict(_defaults(Pose), **k))) for k in K["defeat"]], draw)
    return out


def boss_actions(patterns):
    return (("idle", 4), ("move", 6)) + tuple(x for p in patterns for x in ((f"windup_{p}", 4), (f"attack_{p}", 5))) + \
        (("hurt", 3), ("stagger", 4), ("idle2", 4), ("defeat", 6))
