"""One-off search for the ruin paving layout (round 3); writes ruin_layout.py. Deterministic (seeded).

The ruin floor is stone COURSES 11 px high that run straight across the whole map (wang.py, "Ruin paving").
There are 32 distinct courses G (11 x 32 = 352 px = 11 tiles). A vertical tile edge has a symbol s (0-2 on
the map, 3 = next to a shore overlay); in course G the stone that crosses an edge of symbol s has its left
joint A[G][s] px left of the edge and its right joint at column B[G][s] of the tile on the right. Between
them a tile (west symbol w, east symbol e) has one stone, or two (SPLIT) when the gap is wide.

Searched for: (1) per (w, e) the vertical joints of the 32 courses spread evenly over the 32 columns (so the
columns' mean brightness has no 32-px period), (2) no joint within 3 px of a joint of the course above
(staggered courses), (3) stones 9-24 px long.

Run: python3 tools/terrain_v2/ruin_search.py
"""

import os
import random

COMBOS = [(w, e) for w in range(3) for e in range(3) if w != e]
ALL = COMBOS + [(3, 3)]


def joints(A, B, D, G, w, e):
    l, r = B[G][w], 32 - A[G][e]
    out = [l, r]
    if r - l >= 21:
        out.append(l + (r - l) // 2 + D[G])
    return out


def cost(A, B, D):
    c = 0.0
    for (w, e) in ALL:
        hist = [0] * 32
        prev = joints(A, B, D, 31, w, e)
        for G in range(32):
            js = joints(A, B, D, G, w, e)
            l, r = B[G][w], 32 - A[G][e]
            if r - l < 10:
                c += 50 * (10 - (r - l))
            for x in js:
                hist[x % 32] += 1
                for p in prev:
                    d = abs(x - p)
                    if d <= 3:
                        c += (4 - d) * (6 if (w, e) != (3, 3) else 2)
            prev = js
        if (w, e) != (3, 3):
            m = sum(hist) / 32
            c += sum((h - m) ** 2 for h in hist)
    for G in range(32):
        for s in range(3):
            ln = A[G][s] + B[G][s]
            if ln < 12:
                c += 50 * (12 - ln)
            if ln > 24:
                c += 50 * (ln - 24)
            for s2 in (3,):  # next to a shore overlay (symbol 3 on one side): no slivers
                for ln2 in (A[G][s] + B[G][s2], A[G][s2] + B[G][s]):
                    if ln2 < 8:
                        c += 20 * (8 - ln2)
        for s in range(3):
            for s2 in range(s + 1, 3):  # the symbols differ visibly
                if abs(B[G][s] - B[G][s2]) < 3:
                    c += 3
    return c


def main():
    rnd = random.Random(20261110)
    A = [[rnd.randint(1, 16) for _ in range(4)] for _ in range(32)]
    B = [[rnd.randint(0, 15) for _ in range(4)] for _ in range(32)]
    D = [rnd.randint(-3, 3) for _ in range(32)]
    for G in range(32):
        A[G][3], B[G][3] = rnd.randint(7, 10), rnd.randint(6, 10)
    cur = cost(A, B, D)
    T = 4.0
    import math
    for it in range(60000):
        G = rnd.randrange(32)
        which = rnd.randrange(3)
        if which == 0:
            s = rnd.randrange(4)
            old = A[G][s]
            A[G][s] = rnd.randint(7, 11) if s == 3 else rnd.randint(1, 17)
        elif which == 1:
            s = rnd.randrange(4)
            old = B[G][s]
            B[G][s] = rnd.randint(6, 11) if s == 3 else rnd.randint(0, 16)
        else:
            old = D[G]
            D[G] = rnd.randint(-3, 3)
        new = cost(A, B, D)
        if new <= cur or rnd.random() < math.exp((cur - new) / T):
            cur = new
        else:
            if which == 0:
                A[G][s] = old
            elif which == 1:
                B[G][s] = old
            else:
                D[G] = old
        T = max(0.05, T * 0.99992)
        if it % 10000 == 0:
            print(it, round(cur, 1), round(T, 2))
    print("final", cur)
    with open(os.path.join(os.path.dirname(__file__), "ruin_layout.py"), "w") as f:
        f.write('"""Ruin paving layout (written by ruin_search.py; see there). Per course G (0-31) and edge symbol s (0-3)."""\n\n')
        f.write(f"A = {A!r}\nB = {B!r}\nD = {D!r}\n")


if __name__ == "__main__":
    main()
