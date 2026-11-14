"""v2's timing of a boss's key poses (tools/enemy_v2/anim.py boss() at d900394, unchanged): idle / idle2
4-frame loops, move a 6-frame loop, a wind-up 4 frames (nearly there, the key, a step on, held), an
attack 5 frames (release, strike, follow-through, settling, nearly at rest), hurt 3, stagger 4. The
purification's frames are each boss's own (hand-drawn)."""

import os
import sys

sys.path.insert(1, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "enemy_v3"))
from anim import boss_actions, loop, mix, name, once  # noqa: E402,F401


def actions(Pose, draw, K, patterns, phase2=()):
    out = {}
    idle, idle2 = K["idle"][0], K["idle2"][0]
    name(out, "idle", loop(Pose, 4, [(i / 4, k) for i, k in enumerate(K["idle"])]), draw)
    name(out, "move", loop(Pose, 6, [(i / 4, k) for i, k in enumerate(K["move"])]), draw)
    for p in patterns:
        rest = idle2 if p in phase2 else idle
        w0, w1 = K[f"windup_{p}"][:2]
        a0, a1 = K[f"attack_{p}"][:2]
        strike = K[f"attack_{p}"][2] if len(K[f"attack_{p}"]) > 2 else mix(Pose, rest, a0, 1.45)
        name(out, f"windup_{p}", once(Pose, 4, [(0.0, mix(Pose, rest, w0, 0.9)), (0.34, w0), (1.0, w1)]), draw)
        name(out, f"attack_{p}", once(Pose, 5, [(0.0, a0), (0.25, strike, "in"), (0.5, mix(Pose, strike, a1, 0.45)),
                                                (0.75, mix(Pose, strike, rest, 0.7)), (1.0, mix(Pose, strike, rest, 0.9))]), draw)
    for suffix, base in (("", idle), ("2", idle2)):
        extra = {"phase2": True} if suffix else {}
        h = dict(K["hurt"], **extra)
        name(out, "hurt" + suffix, once(Pose, 3, [(0.0, h), (0.5, mix(Pose, h, base, 0.45)), (1.0, mix(Pose, h, base, 0.85))]), draw)
        s0, s1 = dict(K["stagger"][0], **extra), dict(K["stagger"][1], **extra)
        name(out, "stagger" + suffix, once(Pose, 4, [(0.0, s0), (0.5, s1), (1.0, mix(Pose, s1, base, 0.6))]), draw)
    name(out, "idle2", loop(Pose, 4, [(i / 4, k) for i, k in enumerate(K["idle2"])]), draw)
    return out
