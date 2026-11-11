"""9-slice frames (dialogue, menus, shop, pause, ending, toast), tabs, list rows, text buttons, the scroll
cue, hearts and the boss bar. 1 art px = 1 CSS px.

Every 9-slice is built so its EDGES ARE UNIFORM along their length (ornaments only in the corners): the
engineer can use `border-image-repeat: stretch` and no pixel is ever resampled unevenly.
"""

from common import col, new, rounded_rect_mask, side

NAVY_FILL = 236  # panel fill alpha (the old panels were 0.94-0.95)


def frame(w, h, radius, bands, fill, fill_alpha=NAVY_FILL):
    """bands: from the outside in, each (mat_tl, tone_tl, mat_br, tone_br[, alpha]); fill: (mat, tone)."""
    im = new(w, h)
    m = rounded_rect_mask(w, h, radius)
    # distance to the outside along the rounded shape (Chebyshev to the rounded rect)
    layers = [m]
    for _ in bands:
        prev = layers[-1]
        nxt = [[prev[y][x] and all(0 <= y + dy < h and 0 <= x + dx < w and prev[y + dy][x + dx]
                                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                for x in range(w)] for y in range(h)]
        layers.append(nxt)
    for y in range(h):
        for x in range(w):
            if not m[y][x]:
                continue
            k = next((i for i in range(len(bands)) if not layers[i + 1][y][x]), None)
            if k is None:
                im.putpixel((x, y), col(fill[0], fill[1], fill_alpha))
                continue
            b = bands[k]
            # which side of the panel: light falls on the top and left (split on the anti-diagonal)
            tl = (x + 0.5) / w + (y + 0.5) / h < 1
            a = b[4] if len(b) > 4 else 255
            im.putpixel((x, y), col(b[0], b[1], a) if tl else col(b[2], b[3], a))
    return im


def diamond(im, cx, cy, r, mat, tones=(4, 3, 2, 1), outline=("navy", 0)):
    """A small gem/rivet: a pixel diamond lit from the top left, outlined."""
    for y in range(cy - r - 1, cy + r + 2):
        for x in range(cx - r - 1, cx + r + 2):
            d = abs(x - cx) + abs(y - cy)
            if d == r + 1:
                im.putpixel((x, y), col(*outline))
            elif d <= r:
                t = tones[0] if (x - cx) + (y - cy) < -r // 2 else tones[1] if (x - cx) + (y - cy) <= 0 else tones[2]
                im.putpixel((x, y), col(mat, t))


def star4(im, cx, cy, r, mat):
    """A four-pointed star (the 星環 sparkle), outlined in navy."""
    pts = {(cx, cy)}
    for k in range(1, r + 1):
        pts |= {(cx + k, cy), (cx - k, cy), (cx, cy + k), (cx, cy - k)}
    pts |= {(cx + 1, cy + 1), (cx - 1, cy - 1), (cx + 1, cy - 1), (cx - 1, cy + 1)} if r >= 3 else set()
    for x, y in pts:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in pts and im.getpixel((x + dx, y + dy))[3] != 255:
                im.putpixel((x + dx, y + dy), col("navy", 0))
    for x, y in pts:
        t = 4 if (x <= cx and y <= cy) else 3 if (x == cx or y == cy) else 2
        im.putpixel((x, y), col(mat, t))


def panel_menu():
    """Inventory, settings, pause: a dark navy panel with a cool steel-blue rim and gold rivet corners."""
    # bevelled (inspection R-2): outline, steel-blue rim, a 2-px bevel lit top-left / dark bottom-right,
    # then a dark inner line before the fill
    im = frame(32, 32, 4, [("navy", 0, "navy", 0), ("gem", 3, "gem", 1), ("navy", 4, "navy", 1),
                           ("navy", 3, "navy", 2), ("navy", 0, "navy", 0)], ("navy", 1))
    for cx, cy in ((6, 6), (25, 6), (6, 25), (25, 25)):
        diamond(im, cx, cy, 2, "gold")
    return im, 10


def panel_dialogue():
    """Conversation box: gold rim (warm, the speaker's voice), small 星環 stars in the corners."""
    im = frame(32, 32, 4, [("navy", 0, "navy", 0), ("gold", 3, "gold", 1), ("gold", 2, "chestwood", 1),
                           ("navy", 4, "navy", 1), ("navy", 0, "navy", 0)], ("navy", 1))
    for cx, cy in ((6, 6), (25, 6), (6, 25), (25, 25)):
        star4(im, cx, cy, 2, "gem")
    return im, 10


def panel_shop():
    """The shop: a wooden counter frame (red-brown furniture wood) with gold corner brackets."""
    im = frame(32, 32, 3, [("navy", 0, "navy", 0), ("chestwood", 4, "chestwood", 2), ("chestwood", 3, "chestwood", 1),
                           ("chestwood", 2, "chestwood", 1), ("navy", 0, "navy", 0, 210)], ("navy", 1))
    for cx, cy, sx, sy in ((2, 2, 1, 1), (29, 2, -1, 1), (2, 29, 1, -1), (29, 29, -1, -1)):  # L brackets
        for k in range(6):
            im.putpixel((cx + sx * k, cy), col("gold", 3 if k < 3 else 2))
            im.putpixel((cx, cy + sy * k), col("gold", 3 if k < 3 else 2))
        im.putpixel((cx, cy), col("gold", 4))
    return im, 11


def panel_ending():
    """The ending: a double gold rim with a gem line between, star-ring medallions in the corners."""
    im = frame(48, 48, 5, [("navy", 0, "navy", 0), ("gold", 4, "gold", 2), ("gold", 3, "gold", 1),
                           ("navy", 0, "navy", 0), ("gem", 3, "gem", 1), ("navy", 4, "navy", 1), ("navy", 0, "navy", 0)],
               ("navy", 1))
    for cx, cy in ((8, 8), (39, 8), (8, 39), (39, 39)):
        for y in range(cy - 5, cy + 6):
            for x in range(cx - 5, cx + 6):
                d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                if 3.6 <= d <= 5.3:
                    im.putpixel((x, y), col("navy", 0) if d > 4.7 else col("gold", 4 if (x - cx) + (y - cy) < 0 else 2))
        star4(im, cx, cy, 2, "gem")
    return im, 16


def toast():
    """The toast: a slim panel, gem-blue hairline rim."""
    im = frame(16, 16, 3, [("navy", 0, "navy", 0), ("gem", 2, "gem", 1), ("navy", 3, "navy", 1)], ("navy", 1), 228)
    return im, 5


def nameplate():
    """The speaker's name tag on the dialogue box: gold-rimmed."""
    im = frame(16, 16, 2, [("navy", 0, "navy", 0), ("gold", 3, "gold", 2)], ("navy", 2), 245)
    return im, 5


def crest():
    """A crest for the top edge of the pause / settings panel: the star ring (a gem ring, a gold star)."""
    im = new(31, 17)
    cx, cy = 15, 9
    for y in range(17):
        for x in range(31):
            d = ((x - cx) ** 2 + ((y - cy) * 1.35) ** 2) ** 0.5
            if 9.6 <= d <= 12.2:
                im.putpixel((x, y), col("gem", 3 if y < cy else 2) if d < 11.3 else col("navy", 0))
    star4(im, cx, cy - 1, 4, "gold")
    return im


def tab(state):
    """Menu tabs: idle (navy), active (lit, gold top line), pressed (sunk, gem)."""
    if state == "idle":
        im = frame(20, 20, 3, [("navy", 0, "navy", 0), ("navy", 4, "navy", 2)], ("navy", 3), 240)
    elif state == "active":
        im = frame(20, 20, 3, [("navy", 0, "navy", 0), ("gold", 3, "gold", 2), ("gem", 3, "gem", 2)], ("gem", 1), 245)
    else:
        im = frame(20, 20, 3, [("navy", 0, "navy", 0), ("navy", 1, "navy", 4)], ("navy", 2), 245)
    return im, 6


def row(state):
    """List rows (inventory, shop): idle, selected (gem rim + lit fill), pressed."""
    if state == "idle":
        im = frame(20, 20, 3, [("navy", 3, "navy", 3, 230)], ("navy", 2), 170)
    elif state == "selected":
        im = frame(20, 20, 3, [("navy", 0, "navy", 0), ("gem", 3, "gem", 2), ("navy", 0, "navy", 0, 180)], ("navy", 3), 220)
    else:
        im = frame(20, 20, 3, [("navy", 0, "navy", 0), ("gem", 2, "gem", 1)], ("gem", 0), 230)
    return im, 6


def text_button(state):
    """Menu / title / choice buttons (also the pause and bag buttons, with an icon): a bevelled navy plate."""
    if state == "idle":
        im = frame(24, 24, 4, [("navy", 0, "navy", 0), ("gem", 2, "navy", 1), ("navy", 4, "navy", 2)], ("navy", 3), 255)
    elif state == "pressed":
        im = frame(24, 24, 4, [("navy", 0, "navy", 0), ("navy", 1, "gem", 2), ("navy", 2, "navy", 3)], ("navy", 2), 245)
    elif state == "selected":
        im = frame(24, 24, 4, [("navy", 0, "navy", 0), ("gold", 3, "gold", 2), ("gem", 3, "gem", 1)], ("gem", 1), 245)
    else:  # disabled
        im = frame(24, 24, 4, [("navy", 0, "navy", 0, 200), ("navy", 3, "navy", 2, 200)], ("navy", 2), 170)
    return im, 8


def cue(frame_i):
    """The 'more below' / 'next line' cue: a gold chevron, two frames (the second 1 px lower)."""
    im = new(11, 9)
    pts = [(x, y) for y in range(4) for x in range(y, 9 - y)]
    for x, y in pts:
        im.putpixel((x + 1, y + 1 + frame_i), col("gold", 4 if y == 0 and x < 5 else 3 if y < 2 else 2))
    from common import outline
    outline(im, col("navy", 0))
    return im


HEART = [
    "....xxxx....xxxx....",
    "...xxxxxx..xxxxxx...",
    "..xxxxxxxxxxxxxxxx..",
    ".xxxxxxxxxxxxxxxxxx.",
    ".xxxxxxxxxxxxxxxxxx.",
    ".xxxxxxxxxxxxxxxxxx.",
    ".xxxxxxxxxxxxxxxxxx.",
    "..xxxxxxxxxxxxxxxx..",
    "..xxxxxxxxxxxxxxxx..",
    "...xxxxxxxxxxxxxx...",
    "....xxxxxxxxxxxx....",
    ".....xxxxxxxxxx.....",
    "......xxxxxxxx......",
    ".......xxxxxx.......",
    "........xxxx........",
    ".........xx.........",
]


def heart(quarters):
    """HP heart 22x20 (the HUD's size): 0 = empty .. 4 = full, filled from the left like the HUD does."""
    im = new(22, 20)
    m = [[False] * 22 for _ in range(20)]
    for y, r in enumerate(HEART):
        for x, ch in enumerate(r):
            if ch == "x":
                m[y + 2][x + 1] = True
    cut = 1 + 20 * quarters / 4
    for y in range(20):
        for x in range(22):
            if not m[y][x]:
                continue
            s = side(m, x, y)
            if x < cut:
                t = 2
                if y <= 5 and 3 <= x <= 7 and (x + y) <= 10:
                    t = 4 if (x, y) in ((4, 4), (5, 4), (4, 5)) else 3
                if s == "br" or y >= 13:
                    t = 1
                im.putpixel((x, y), col("berry", t) if quarters else col("navy", 2))
            else:
                # the empty part (inspection M-3): a light grey-blue rim inside the navy outline, so an empty
                # heart still shows on night, cave and indoor black; a dark slate inside
                edge = any(not (0 <= x + dx < 22 and 0 <= y + dy < 20 and m[y + dy][x + dx])
                           for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                if edge:
                    im.putpixel((x, y), col("steel", 4 if s == "tl" else 3))
                else:
                    im.putpixel((x, y), col("steel", 1 if y > 8 else 2))
    from common import outline
    outline(im, col("navy", 0))
    return im


def bossbar_frame():
    """The boss bar's track frame: a dark violet slot with a steel rim and gem rivets at the ends."""
    im = frame(24, 12, 3, [("navy", 0, "navy", 0), ("steel", 3, "steel", 1), ("navy", 0, "navy", 0)], ("navy", 0), 220)
    # the rivets sit inside the top corners (inspection I-2): the side bands stay uniform, so the frame may
    # be stretched in height too
    diamond(im, 4, 2, 1, "miasma", tones=(4, 3, 2, 1))
    diamond(im, 19, 2, 1, "miasma", tones=(4, 3, 2, 1))
    return im, (7, 5, 7, 5)


def bossbar_fill(phase):
    """The fill, 4 px wide (repeat-x), 4 rows tall: lit top row, darker bottom (phase 2 turns red)."""
    mat = "miasma" if phase == 1 else "berry"
    im = new(4, 4)
    for y, t in enumerate((4, 3, 2, 1)):
        for x in range(4):
            im.putpixel((x, y), col(mat, t))
    return im
