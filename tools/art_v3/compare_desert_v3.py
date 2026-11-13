"""Comparison pictures of the v3 desert (gen_desert_v3.py, gen_desert_flora_v3.py) against the current
desert (v2 ground src/art-release-v2/terrain, the v2 / v1 obj.cactus, obj.rock, obj.tree), the same place.

A map 48 x 24 cells: desert sand, a winding path (the game's path to the lake pass is the same ground)
and a patch of ruin floor. The current picture is v2's own reference renderer
(tools/terrain_v2/render_ref.render_v2, unchanged: Wang ripple tiles, dunes, edges). For v3 the keys
render_v2 draws on each display tile are recorded and swapped: a desert sand base -> the v3 base tile +
the flow layer (per corner, as the game does: a corner with any non-desert cell around it is "m"), the
desert sand edge over the path / ruin -> the v3 edge (same mask, same v); the path and ruin floor have no
v3 yet and are the v2 tiles at 2 x 2 (STYLE 6, "まだ").
Objects: from a hash on desert cells. Current: obj.cactus, obj.rock, obj.tree (the oasis tree); v3: the
desert cactus / rock_l / palm_l at the same feet, and the other v3 trees / props (drawn in v3 only).
  desert_15pro_now_k2.png / desert_15pro_v3_k2.png   2556 x 1179 (1 game px = 8 px, 20 x 9.2 tiles)
  desert_se_now_k1.png / desert_se_v3_k1.png         1334 x 750 (1 game px = 4 px, 20.8 x 11.7 tiles)
  desert_48x24_now_half.png / desert_48x24_v3_half.png   the whole map, half size
  items_now_v3.png   the current cactus / rock / tree and the v3 trees / props at the same game size
No contact shadows. Run: python3 tools/art_v3/compare_desert_v3.py <out dir>
"""

import functools
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from PIL import Image, ImageOps  # noqa: E402

import gen_desert_v3 as D  # noqa: E402
import gen_ground_v3 as G  # noqa: E402
from v3lib import ROOT  # noqa: E402

sys.path.append(os.path.join(ROOT, "tools", "terrain_v2"))
import render_ref as RR  # noqa: E402

V2T = os.path.join(ROOT, "src", "art-release-v2", "terrain")
V1T = os.path.join(ROOT, "src", "art-release", "terrain")
V3T = os.path.join(ROOT, "src", "art-release-v3", "terrain")
W_T, H_T = 48, 24
PREFIX = {"dsand": "desert.sand", "path": "tile.path", "ruin": "tile.ruin", "sand": "tile.sand", "grass": "tile.grass"}
BARE = {"path", "ruin", "sand"}


@functools.lru_cache(maxsize=None)
def ld(p):
    return Image.open(p).convert("RGBA")


def grid():
    rows = []
    for y in range(H_T + 1):
        r = ""
        for x in range(W_T + 1):
            px = 20 + 7 * math.sin(y * 0.22) + 2 * math.sin(y * 0.7 + 1)  # a path winding north-south
            c = "=" if abs(x - px) < 1.3 else "d"
            if 6 <= y <= 9 and 22 <= x <= 40 + (y % 2):  # and a branch east
                c = "=" if abs(y - 7.5 + 0.8 * math.sin(x * 0.4)) < 1.0 else c
            if (x - 36) ** 2 / 20 + (y - 17) ** 2 / 9 < 1:
                c = "u"
            r += c
        rows.append(r)
    return rows


def v2_file(key):
    """g2.<class>.<name> -> the v2 file."""
    _, cls, name = key.split(".", 2)
    if name.startswith("e") and name[1].isdigit():
        m, v = name[1:].split(".")
        name = f"edge.{m}.{v}"
    p = PREFIX[cls] if (name == "0" and cls in BARE) else f"{PREFIX[cls]}.{name}"
    return os.path.join(V2T, p + ".png")


def record(g):
    """The keys render_v2 draws per display tile (bottom first)."""
    class Key:
        def __init__(self, k):
            self.k = k

    class Images(dict):
        def __missing__(self, k):
            return Key(k)
    draws = {}

    def ac(self, im, dest=(0, 0), source=(0, 0)):
        draws.setdefault(((dest[0] - 16) // 32, (dest[1] - 16) // 32), []).append(im.k)
    old = Image.Image.alpha_composite, Image.Image.paste
    Image.Image.alpha_composite = ac
    Image.Image.paste = lambda self, *a, **k: None
    try:
        RR.render_v2(g, Images(), frame=0)
    finally:
        Image.Image.alpha_composite, Image.Image.paste = old
    return draws


def masked_flow_key(g, tx, ty):
    """The game's rule: a corner is 'm' when any map cell around it is not desert sand."""
    def corner(cx, cy):
        if any(RR.terr(g, cx + dx, cy + dy) != "dsand" for dx in (-1, 0) for dy in (-1, 0)):
            return "m"
        return G.flow_corner(cx, cy)
    cs = [corner(tx, ty), corner(tx + 1, ty), corner(tx + 1, ty + 1), corner(tx, ty + 1)]
    if all(c == G.flow_corner(x, y) for c, (x, y) in zip(cs, ((tx, ty), (tx + 1, ty), (tx + 1, ty + 1), (tx, ty + 1)))):
        return G.flow_key(tx, ty)
    kinds = {k for k in cs if k != "m"}
    if not kinds:
        return None
    kind = kinds.pop()
    bits = "".join("1" if k == kind else "0" for k in cs)
    flip = bits in G.MIRROR
    stored = G.MIRROR.get(bits, bits)

    def st(side):
        if flip and side in ("E", "W"):
            side = "W" if side == "E" else "E"
        return G.side_state(tx, ty, side)
    sides = G.crossed(stored)
    if not sides:
        return kind, stored, G.full_v(tx, ty), bool((G.hsh(tx, ty, 35) >> 2) & 1)
    if len(sides) == 4:
        return kind, stored, st("N") + 2 * st("E") + 4 * st("S") + 8 * st("W"), flip
    return kind, stored, st(sides[0]) + 2 * st(sides[1]) + 4 * ((tx + 2 * ty) % G.INNER_SHAPES), flip


def v3_base(g, i, j):
    t = ld(os.path.join(V3T, f"desert.sand.v3.{G.macro_of(i // 4, j // 4)}{j % 4}{i % 4}.png")).copy()
    fk = masked_flow_key(g, i, j)
    if fk:
        kind, bits, v, flip = fk
        sh = ld(os.path.join(V3T, f"desert.sandflow.v3.{bits}.{v}.png"))
        if flip:
            sh = ImageOps.mirror(sh)
        t.alpha_composite(G.tinted(sh, D.flow_tints()[kind]))
    return t


def ground(ver, g):
    d = 2 if ver == "now" else 4
    T = 16 * d
    im = Image.new("RGBA", ((W_T + 1) * T, (H_T + 1) * T), (0, 0, 0, 255))
    for (i, j), keys in record(g).items():
        for k in keys:
            cls = k.split(".")[1]
            name = k.split(".", 2)[2]
            if ver == "now":
                tile = ld(v2_file(k))
            elif cls == "dsand" and name.startswith("e") and name[1].isdigit():
                m, v = name[1:].split(".")
                tile = ld(os.path.join(V3T, f"desert.sand.v3.edge.{m}.{v}.png"))
            elif cls == "dsand":
                tile = v3_base(g, i, j)
            else:
                tile = ld(v2_file(k)).resize((64, 64), Image.NEAREST)
            im.alpha_composite(tile, (i * T + T // 2, j * T + T // 2))
    return im.crop((T // 2, T // 2, T // 2 + W_T * T, T // 2 + H_T * T))


def things(g):
    """Objects on desert cells away from other grounds (feet in game px), from a hash: no grid."""
    out = []
    for y in range(1, H_T):
        for x in range(1, W_T):
            if not all(RR.terr(g, a, b) == "dsand" for a in (x - 1, x, x + 1) for b in (y - 1, y, y + 1)):
                continue
            h = G.hsh(x, y, 87) % 100
            fx, fy = x * 16 + 8 + (G.hsh(x, y, 88) % 9) - 4, y * 16 + 14
            if h < 4:
                out.append(("cactus", fx, fy))
            elif h < 6:
                out.append(("rock", fx, fy))
            elif h < 8:
                out.append(("tree", fx, fy))
            elif h < 13:
                out.append(("v3", ("cactus_l", "barrel", "pear", "agave", "rock_s", "bones", "tumbleweed",
                                    "drygrass", "sage", "pebbles", "snag", "palm_s")[G.hsh(x, y, 89) % 12], fx, fy))
    return out


V3_OF = {"cactus": "prop.v3.cactus", "rock": "prop.v3.rock_l", "tree": "tree.v3.palm_l"}


def scene(ver):
    g = grid()
    im = ground(ver, g)
    d = 2 if ver == "now" else 4
    for t in sorted(things(g), key=lambda t: t[-1]):
        if ver == "now":
            if t[0] == "v3":
                continue
            p = os.path.join(V2T, f"obj.{t[0]}.png")
            sp = ld(p if os.path.exists(p) else os.path.join(V1T, f"obj.{t[0]}.png"))
        elif t[0] == "v3":
            kind = "tree" if t[1] in ("snag", "palm_s") else "prop"
            sp = ld(os.path.join(V3T, f"desert.{kind}.v3.{t[1]}.0.png"))
        else:
            sp = ld(os.path.join(V3T, f"desert.{V3_OF[t[0]]}.0.png"))
        fx, fy = t[-2], t[-1]
        im.alpha_composite(sp, (fx * d - sp.width // 2, fy * d - sp.height))
    return im


def items(path):
    now = [ld(os.path.join(V2T, f"obj.{k}.png")) for k in ("cactus", "rock", "tree")]
    v3 = [ld(os.path.join(V3T, f"desert.{k}.png")) for k in
          ("tree.v3.palm_l.0", "tree.v3.palm_s.0", "tree.v3.snag.0", "prop.v3.cactus.0", "prop.v3.cactus_l.0",
           "prop.v3.barrel.0", "prop.v3.pear.0", "prop.v3.agave.0", "prop.v3.rock_l.0", "prop.v3.rock_s.0",
           "prop.v3.bones.0", "prop.v3.tumbleweed.0", "prop.v3.drygrass.0", "prop.v3.sage.0", "prop.v3.pebbles.0")]
    cells = [a.resize((a.width * 4, a.height * 4), Image.NEAREST) for a in now] + \
        [b.resize((b.width * 2, b.height * 2), Image.NEAREST) for b in v3]
    W = sum(c.width + 16 for c in cells) + 48
    H = max(c.height for c in cells) + 24
    r = Image.new("RGBA", (W, H), (168, 96, 60, 255))
    x = 16
    for n, c in enumerate(cells):
        r.alpha_composite(c, (x, H - 12 - c.height))
        x += c.width + (48 if n == 2 else 16)
    r.save(path, optimize=True)


def main(out):
    os.makedirs(out, exist_ok=True)
    for ver in ("now", "v3"):
        im = scene(ver)
        d = 2 if ver == "now" else 4
        s15 = 8 // d
        big = im.resize((im.width * s15, im.height * s15), Image.NEAREST)
        x0, y0 = 10 * 16 * 8, 2 * 16 * 8
        big.crop((x0, y0, x0 + 2556, y0 + 1179)).save(os.path.join(out, f"desert_15pro_{ver}_k2.png"), optimize=True)
        sse = 4 // d
        bse = im.resize((im.width * sse, im.height * sse), Image.NEAREST) if sse > 1 else im
        x0, y0 = 10 * 16 * 4, 2 * 16 * 4
        bse.crop((x0, y0, x0 + 1334, y0 + 750)).save(os.path.join(out, f"desert_se_{ver}_k1.png"), optimize=True)
        im.resize((W_T * 32, H_T * 32), Image.NEAREST).save(os.path.join(out, f"desert_48x24_{ver}_half.png"), optimize=True)
    items(os.path.join(out, "items_now_v3.png"))
    print(sorted(os.listdir(out)))


if __name__ == "__main__":
    main(sys.argv[1])
