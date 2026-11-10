"""Hand-placed details shared by the bosses: the murk core, glowing eyes, orbs, cracks.
All glow is the same colour in every frame (the wind-up flash is the program's, not painted)."""

CORE = {  # a crystal heart, hand-shaded: light from the top left, brightest at the upper left
    7: [
        "....a....",
        "...abb...",
        "..abbcb..",
        ".abbbccb.",
        "abbbcccbd",
        ".bbcccbd.",
        "..bccbd..",
        "...bdd...",
        "....d....",
    ],
}
LEG = {"a": ("glow", 4), "b": ("glow", 3), "c": ("glow", 2), "d": ("glow", 1)}


def core(r, cx, cy, size=7, bright=True):
    """A murk socket with the magenta crystal heart in it."""
    r.ellipse(cx, cy, size + 1.5, size + 0.5, "murk", soft=2)
    rows = CORE[7]
    if size >= 9:  # bared (phase 2): a bigger crystal
        rows = ["....a....", "...aab...", "..abbbc..", ".abbbbcc.", "abbbbccbd", "abbbcccbd", ".bbccccd.", "..bcccd..", "...bdd...", "....d...."]
    if not bright:
        leg = {"a": ("glow", 2), "b": ("glow", 1), "c": ("glow", 1), "d": ("glow", 0)}
    else:
        leg = LEG
    r.stamp(round(cx) - 4, round(cy) - len(rows) // 2, rows, leg)


# a hand-drawn angry eye in a dark socket (right eye; the left one is its mirror): 0 = the
# socket / brow (tone 0 of the face's own material), a/b/c = the glow from bright to core
SOCKET_EYE = ["...00", "000ab", "0abc0", ".000."]
SOCKET_NARROW = ["...00", "00000", "0abc0", "....."]


def glow_eyes(r, cx, cy, gap, state="open", socket=None):
    """Two glowing eyes, `gap` px from the centre each. With `socket` (a material), each eye is a
    hand-drawn slanted eye in a dark socket under a heavy brow (reads at 1x on a light or dark face)."""
    for s in (-1, 1):
        x = round(cx + s * gap) - (1 if s < 0 else 0)
        y = round(cy)
        if socket and state in ("open", "narrow"):
            rows = SOCKET_EYE if state == "open" else SOCKET_NARROW
            leg = {"0": (socket, 0), "a": ("glow", 4), "b": ("glow", 3), "c": ("glow", 2)}
            r.stamp(x - 2, y - 2, rows, leg, flip=s < 0)
            continue
        if state == "open":
            r.stamp(x - 1, y - 1, ["ab", "bc"] if s < 0 else ["ab", "bc"], {"a": ("glow", 4), "b": ("glow", 3), "c": ("glow", 2)})
            r.px([(x - 2 if s < 0 else x + 1, y - 2), (x - 1 if s < 0 else x, y - 2)], "murk", 0)  # a heavy brow
        elif state == "shut":
            r.px([(x - 1, y), (x, y)], "glow", 1)
        elif state == "narrow":
            r.px([(x - 1, y), (x, y)], "glow", 4)


def orb(r, x, y, rad):
    """An enemy-magic orb (hand-shaded)."""
    r.ellipse(x, y, rad, rad, "glow", tone=2)
    r.ellipse(x - 0.4, y - 0.4, rad * 0.62, rad * 0.62, "glow", tone=3)
    r.px([(int(x - rad * 0.4), int(y - rad * 0.4))], "glow", 4)


def cracks(r, segs):
    """Phase-2 cracks: glowing seams through the body (2 px groups, not single dots)."""
    for x0, y0, x1, y1 in segs:
        r.add(r.m_line(x0, y0, x1, y1), "glow", tone=3, cast=False)
        r.add(r.m_line(x0 + 1, y0, x1 + 1, y1), "glow", tone=1, cast=False)
