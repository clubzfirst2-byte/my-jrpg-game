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
        return a if f < 1 else b
    if isinstance(a, int) and isinstance(b, int):  # counts and steps stay whole (write 1.0 for smooth)
        return int(math.floor(a + (b - a) * f + 0.5))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a + (b - a) * f
    if isinstance(a, tuple) and isinstance(b, tuple) and len(a) == len(b):
        return tuple(_blend(x, y, f) for x, y in zip(a, b))
    return a if f < 1 else b


def _state(base, keys, t):
    """The pose dict at time t from keys [(t, dict, ease)]: blend the two keys around t."""
    full = []
    for k in keys:
        tk, d = k[0], k[1]
        ease = k[2] if len(k) > 2 else "smooth"
        dd = dict(base)
        dd.update(d)
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
