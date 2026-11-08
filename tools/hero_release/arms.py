"""The hero's arms, drawn pixel by pixel (release art, stage 4).

Four basic poses per view, each a hand-made pixel map (like heads.py and body.py):
  down     the arm hanging at the side
  forward  the hand brought forward (front view: towards the viewer, in front of the body;
           side view: reaching ahead)
  up       raised (beside the head)
  out      spread to the side (front / back view); side view: swung back ("back")
Every map is the hero's RIGHT arm (the sword arm) as seen in that view; his left arm is the same
map mirrored (front / back view) or drawn behind the body (side view), one tone darker: it is
on the shaded side, further from the light at the top left.

Characters:
  .          empty
  0 1 2 3 4  cloak (the cape drapes the shoulder), tone 0 .. 4
  a b c d e  sleeve (white), tone 0 .. 4 (a = its own contour where it lies over the body)
  f g h i j  gold (the cape's rim), tone 0 .. 4
  v w x y z  leather glove, tone 0 .. 4
  S          the shoulder joint (anchor; drawn as cloak tone 2)
  H          the hand (anchor; drawn as glove tone 3) — props (sword, bow, shield) are held here
Which pose a frame uses follows from where its hand should be (pick()).
"""

MATS = {**{c: ("cloak", i) for i, c in enumerate("01234")}, **{c: ("shirt", i) for i, c in enumerate("abcde")},
        **{c: ("gold", i) for i, c in enumerate("fghij")}, **{c: ("leather", i) for i, c in enumerate("vwxyz")},
        "S": ("cloak", 2), "H": ("leather", 3)}

# ------------------------------------------------------------------ front view (facing the viewer)
# his right arm is on the image's LEFT; the body's centre is to the right of these maps

FRONT = {
    "down": """
......S
.......
.......
.......
.......
.acb...
acba...
acba...
abba...
vxxv...
vxHv...
.vv....
""",
    "forward": """
..22S...
.23332..
.23321..
.2hhh1..
.acca...
.acccaa.
..abbcca
....vxyv
....vxHv
.....vv.
""",
    "up": """
.vv.......
vxHv......
vxxv......
.abbaa....
..acbaa...
...acbba..
.....accb2
......h332
........2S
""",
    "out": """
........h22S
......aah332
vvv.aaccah2.
vHxaacccba..
vxxaabbbba..
.vv..aaaa...
""",
}

# ------------------------------------------------------------------ back view (facing away)
# his right arm is on the image's RIGHT; the body's centre is to the left of these maps

BACK = {
    "down": """
S......
.......
.......
.......
.......
.......
....abc
....abca
....abba
....vxxv
....vHxv
.....vv.
""",
    "forward": """
S2..
2332
3321
hhh1
""",
    "up": """
.......vv.
......vxHv
......vxxv
....aabba.
...aabca..
..abbca...
2bcca.....
233h......
S2........
""",
    "out": """
S22h........
233haa......
.2haccaa.vvv
..abccca.xHv
..abbbbaaxxv
...aaaa..vv.
""",
}

# ------------------------------------------------------------------ side view (facing right)
# the near arm is his right arm; the shoulder is under the cape, which drapes over it

SIDE = {
    "down": """
.2S3.
23332
23321
2hhh1
.acb.
.acb.
.acb.
.abb.
.vxv.
vxHxv
.vv..
""",
    "forward": """
.2S3......
23332.....
23321.....
2hhh1.....
.acbaaa...
.acccccvv.
..abbbvxHv
.......vv.
""",
    "up": """
..........vv.
.........vxHv
.........vxxv
.......aabba.
......aabca..
....aabca....
...acba......
.2acb........
2S32.........
""",
    "back": """
..2S3
.23332
.23321
.2hhh1
.acb..
acb...
abb...
vxv...
vHxv..
.vv...
""",
}


def _grid(text):
    rows = [r for r in text.strip("\n").split("\n")]
    w = max(len(r) for r in rows)
    rows = [r.ljust(w, ".").replace(" ", ".") for r in rows]
    s = h = None
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == "S":
                s = (x, y)
            elif ch == "H":
                h = (x, y)
    return {"rows": rows, "S": s, "H": h}


VIEWS = {"down": {k: _grid(v) for k, v in FRONT.items()}, "up": {k: _grid(v) for k, v in BACK.items()},
         "side": {k: _grid(v) for k, v in SIDE.items()}}
# the back view's "forward" has no hand: the arm is hidden in front of the body
VIEWS["up"]["forward"]["H"] = VIEWS["up"]["forward"]["S"]


def pick(view, side, shoulder, hand):
    """The basic pose for a hand position (both in frame pixels). side: 'R' or 'L'."""
    dx, dy = hand[0] - shoulder[0], hand[1] - shoulder[1]
    if view == "side":
        if dy < -5:
            return "up"
        if dx >= 4:
            return "forward"
        if dx <= -3:
            return "back"
        return "down"
    # front / back: "outwards" is away from the body's centre line
    out = (shoulder[0] - hand[0]) if shoulder[0] < 15.5 else (hand[0] - shoulder[0])
    if dy < -5:
        return "up"
    if out >= 5 and dy < 6:
        return "out"
    if out <= -2:
        return "forward"
    return "down"


def stamp(L, view, side, pose, shoulder, darker=False):
    """Draws the arm with its shoulder at `shoulder` (frame pixels) on layer L; returns the hand's
    position. Front / back view: the arm on the image's other side is the map mirrored."""
    g = VIEWS[view][pose]
    rows, (sx, sy), (hx, hy) = g["rows"], g["S"], g["H"]
    w = len(rows[0])
    mirror = (view == "down" and side == "L") or (view == "up" and side == "L")
    shade = 1 if darker else 0
    ox, oy = round(shoulder[0]), round(shoulder[1])
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == ".":
                continue
            m, t = MATS[ch]
            t = max(0, t - shade) if t > 0 else 0
            mx = (sx - x) if mirror else (x - sx)
            L.put(ox + mx, oy + y - sy, m, t)
    hxx = (sx - hx) if mirror else (hx - sx)
    return (ox + hxx, oy + hy - sy)
