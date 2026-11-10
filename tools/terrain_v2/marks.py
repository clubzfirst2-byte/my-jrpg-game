"""Hand-designed marks for ground v2 (drawn at hand-chosen places by grounds.py). Light from the top left:
lit tips and top / left rims use the high tones, shade goes below and to the right.
Everything is 2+ px clusters (no lone pixels), no checkerboard dither.
"""

import math

# --- grass blades ------------------------------------------------------------------------------------
# A clump = blades (dx from the clump's foot, height, lean: -1 left / 0 / +1 right). Hand-made sets.
CLUMPS = {
    "S": [(-1, 3, -1), (0, 4, 0), (2, 3, 1)],
    "M": [(-3, 3, -1), (-1, 5, -1), (0, 6, 0), (2, 4, 1), (3, 3, 1)],
    "L": [(-5, 3, -1), (-3, 5, -1), (-2, 7, -1), (0, 8, 0), (1, 6, 0), (3, 7, 1), (4, 5, 1), (6, 3, 1)],
    "W": [(-4, 4, 1), (-2, 6, 1), (0, 7, 1), (2, 6, 1), (3, 4, 1), (5, 3, 1)],  # wind-bent (plains)
}


def blade_pixels(fx, fy, dx, h, lean):
    """The pixels of one blade, foot first."""
    out = []
    x = fx + dx
    for k in range(h):
        out.append((x, fy - k))
        if lean and k in (2, 4, 6):
            x += lean
    return out


def draw_clump(c, mat, fx, fy, kind, light=True):
    """A grass clump: blades darkest at the foot (2), lighter toward the tip (4, tip 5; 6 on the lit left
    blades), a 2 px shadow at the foot on the right."""
    blades = CLUMPS[kind]
    for i, (dx, h, lean) in enumerate(blades):
        pix = blade_pixels(fx, fy, dx, h, lean)
        for k, (x, y) in enumerate(pix):
            t = 2 if k == 0 else 3 if k < h * 0.45 else 4
            if k == h - 1:
                t = 6 if (light and dx < 0 and h >= 5) else 5
            c.put(x, y, mat, t)
    for x in range(fx, fx + max(2, len(blades) // 2)):  # the clump's shadow, right of its foot
        c.put(x + 1, fy + 1, mat, 1 if x == fx else 2)


# --- soft patches ------------------------------------------------------------------------------------
def _edge_jitter(x, y, seed):
    """A smooth, deterministic wobble of a patch edge (sum of sines; not a pixel noise). 32-periodic, so a
    seam patch is the same in a single tile and in each quarter of a 2x2 macro."""
    x, y = x % 32, y % 32
    return 0.11 * math.sin(0.9 * x + 1.7 * seed) + 0.09 * math.sin(1.3 * y + 0.6 * seed) + 0.06 * math.sin(0.5 * (x + y) + seed)


def patch_pixels(cx, cy, rx, ry, seed=0, rot=0.0, wobble=1.0):
    """Pixels of a soft-edged blob (an ellipse with a wobbling edge), possibly rotated."""
    out = []
    ca, sa = math.cos(rot), math.sin(rot)
    R = int(max(rx, ry)) + 2
    for y in range(int(cy) - R, int(cy) + R + 1):
        for x in range(int(cx) - R, int(cx) + R + 1):
            px, py = x + 0.5 - cx, y + 0.5 - cy
            u, v = px * ca + py * sa, -px * sa + py * ca
            if (u / rx) ** 2 + (v / ry) ** 2 <= 1 + wobble * _edge_jitter(x, y, seed):
                out.append((x, y))
    return out


def fill_patch(c, mat, pixels, tone, only=None, rim=False):
    """A low-contrast patch: tone inside; with rim, its top-left edge one tone lighter and its
    bottom-right edge one tone darker (a slight mound / hollow)."""
    s = set(pixels)
    for x, y in pixels:
        if only is not None:
            v = c.get(x, y)
            if not v or v[0] != only:
                continue
        t = tone
        if rim:
            if (x, y - 1) not in s or (x - 1, y) not in s:
                t = tone + 1
            elif (x, y + 1) not in s or (x + 1, y) not in s:
                t = tone - 1
        c.put(x, y, mat, t)


# --- small things ------------------------------------------------------------------------------------
PEBBLE_S = ["54", "32"]
PEBBLE_M = [".54.", "5432", ".21."]
PEBBLE_L = [".554.", "54443", "43332", ".221."]
CLOVER = [".5.5.", "54545", ".4.4.", "..3.."]
SHELL = [".65", "654", ".3."]
MUSHROOM = [".55.", "5443", ".bb.", ".bb."]  # cap in its own ramp; stem 'b'
FERN = [
    "....5....",
    "..5.4.5..",
    ".4.343.4.",
    "5.3.3.3.5",
    ".3.232.3.",
    "..2.2.2..",
    "....2....",
]
NEEDLES = ["5...", ".4.5", "..3.", ".2.."]
LEAF = ["32", "2."]
LEAF2 = [".3", "32"]
TWIG = ["5....", ".43..", "...32"]
REED = [  # a reed clump (lake): tall, lit on the left
    "..6.5..",
    ".5.4.5.",
    ".4.4.4.",
    "54.3.3.",
    "4.3.3.2",
    "3.3.2.2",
    ".2.2.1.",
]
FLOWERS = [  # a small cluster: 'a' petal, 'b' lit petal, 'c' centre
    ".ab..b.",
    "acb.bca",
    ".a...a.",
    "...ab..",
    "..acb..",
    "...a...",
]
CRACK_A = [(0, 0), (1, 0), (2, 1), (3, 1), (4, 2), (5, 2), (5, 3), (6, 4)]
CRACK_B = [(0, 0), (1, 1), (1, 2), (2, 3), (3, 3), (4, 4), (4, 5)]


def crack(c, mat, x0, y0, path, dark=1, lip=4):
    """A crack: dark line, its lower side lit (the edge catches the light)."""
    for dx, dy in path:
        c.put(x0 + dx, y0 + dy, mat, dark)
        v = c.get(x0 + dx, y0 + dy + 1)
        if v and v[0] == mat and v[1] >= 3 and (dx, dy + 1) not in path:
            c.put(x0 + dx, y0 + dy + 1, mat, lip)





def ripple(c, mat, x0, y0, length, amp=1.0, phase=0.0, crest=4, trough=2):
    """A sand / snow ripple: a lit crest line and a shaded trough under it, gently waving. Where the
    ripple is highest (facing the light) the crest is one tone brighter, where it dips the trough is one
    tone deeper (2-4 px runs), so a ripple field uses 5 tones while staying low in contrast."""
    for k in range(length):
        s = math.sin(0.35 * k + phase)
        y = y0 + round(amp * s)
        mid = 2 <= k < length - 2
        c.put(x0 + k, y, mat, crest + 2 if (mid and s < -0.97) else crest + 1 if (mid and s < -0.75) else crest)
        c.put(x0 + k, y + 1, mat, trough - 1 if (mid and s > 0.8) else trough)


def drift(c, mat, x0, y0, length, height=2, phase=0.0):
    """A snow drift: a curved crest (5; its top 2-3 px 6), the lit slope above it (4), the lee shade
    below (2, deepest 1 under the top)."""
    for k in range(length):
        bump = math.sin(math.pi * k / max(1, length - 1))
        y = y0 - round(height * bump) + round(0.6 * math.sin(0.5 * k + phase))
        top = bump > 0.93 and length >= 8
        if bump > 0.35:
            c.put(x0 + k, y - 1, mat, 4)  # the lit windward slope
        c.put(x0 + k, y, mat, 6 if top else 5 if bump > 0.35 else 4)  # the lit crest
        c.put(x0 + k, y + 1, mat, 1 if top else 2 if bump > 0.35 else 3)  # the lee shade
