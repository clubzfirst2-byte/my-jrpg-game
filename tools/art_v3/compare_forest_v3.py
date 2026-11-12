"""Comparison pictures of the v3 forest (gen_forest_v3.py, gen_forest_flora_v3.py) against the current
forest (v2 ground src/art-release-v2/terrain, v1 forest.pine), the same place, 3 seasons.

A map 48 x 24 tiles: forest moss on the right two thirds, the plains grass on the left, the border wavy.
Both are drawn with the v2 dual-grid rule (NAMES.md 2): per display tile the base of the lowest terrain
(forest moss) and, where plains corners are present, the plains edge overlay <prefix>.edge.<mask>.<v>
(the variant from tools/terrain_v2/render_ref.edge_variant). v3: the forest base + the flow layer
(round 2: per corner, as the game does: a corner with any non-forest cell around it is "m", on the
plains side too); winter: at the forest / plains border the forest's winter edge is drawn over the plains
snow (the pair's priority swapped in winter, FOREST.md 1), the plains v3 base + flow, the plains v3 edges over the forest; trees and props.
Current: v2 base tiles (render_ref.calm_number) and v2 plains edges; the v1 forest.pine at the same feet.
  <season>_15pro_now_k2.png / <season>_15pro_v3_k2.png   2556 x 1179 (1 game px = 8 px)
  <season>_se_now_k1.png / <season>_se_v3_k1.png         1334 x 750 (1 game px = 4 px)
  <season>_48x24_now_half.png / <season>_48x24_v3_half.png   the whole map at half size (v3 1 texel = 0.5 px)
  items_now_v3.png   the current forest.pine and the v3 trees / props at the same game size
No contact shadows. Run: python3 tools/art_v3/compare_forest_v3.py <out dir>
"""

import functools
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from PIL import Image  # noqa: E402

import gen_forest_v3 as F  # noqa: E402
import gen_ground_v3 as G  # noqa: E402
from v3lib import ROOT  # noqa: E402

sys.path.append(os.path.join(ROOT, "tools", "terrain_v2"))
import render_ref as RR  # noqa: E402

V2T = os.path.join(ROOT, "src", "art-release-v2", "terrain")
V1T = os.path.join(ROOT, "src", "art-release", "terrain")
V3T = os.path.join(ROOT, "src", "art-release-v3", "terrain")
W_T, H_T = 48, 24
PRE = {"summer": "", "autumn": "autumn.", "winter": "winter."}


@functools.lru_cache(maxsize=None)
def ld(p):
    return Image.open(p).convert("RGBA")


def grid():
    rows = []
    for y in range(H_T + 1):
        b = 17 + 2.5 * __import__("math").sin(y * 0.45) + 1.5 * __import__("math").sin(y * 1.3 + 1)
        rows.append("".join("p" if x < b else "m" for x in range(W_T + 1)))
    return rows


def masked_flow_key(g, terrain, tx, ty):
    """The game's rule (NAMES.md 3.1): a corner is 'm' when any map cell around it is not this ground,
    then gen_ground_v3.flow_key's rule with those corners (round 2: per corner, both grounds)."""
    def corner(cx, cy):
        if any(RR.terr(g, cx + dx, cy + dy) != terrain for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
            return "m"
        return G.flow_corner(cx, cy)
    cs = [corner(tx, ty), corner(tx + 1, ty), corner(tx + 1, ty + 1), corner(tx, ty + 1)]
    kinds = {k for k in cs if k != "m"}
    if not kinds:
        return None
    if all(c == G.flow_corner(x, y) for c, (x, y) in zip(cs, ((tx, ty), (tx + 1, ty), (tx + 1, ty + 1), (tx, ty + 1)))):
        return G.flow_key(tx, ty)
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


def tile_v3(g, terrain, i, j, season):
    """A v3 base tile with its flow (masked at the corners)."""
    from PIL import ImageOps
    pre = PRE[season]
    if terrain == "moss":
        t = ld(os.path.join(V3T, f"{pre}forest.grass.v3.{G.macro_of(i // 4, j // 4)}{j % 4}{i % 4}.png")).copy()
        sset, name, tint = F.FLOW_SETS[season], "forest", F.flow_tints(season)
    else:
        t = ld(os.path.join(V3T, f"{pre}plains.grass.v3.{G.macro_of(i // 4, j // 4)}{j % 4}{i % 4}.png")).copy()
        sset, name, tint = G.FLOW_SETS[season], "plains", G.flow_tints(season)
    fk = masked_flow_key(g, terrain, i, j)
    if fk:
        kind, bits, v, flip = fk
        sh = ld(os.path.join(V3T, f"{sset}{name}.grassflow.v3.{bits}.{v}.png"))
        if flip:
            sh = ImageOps.mirror(sh)
        t.alpha_composite(G.tinted(sh, tint[kind]))
    return t


def ground(ver, season):
    g = grid()
    d = 2 if ver == "now" else 4
    T = 16 * d
    im = Image.new("RGBA", (W_T * T, H_T * T), (0, 0, 0, 255))
    pre = PRE[season]
    for j in range(H_T):
        for i in range(W_T):
            ts = [RR.terr(g, *c) for c in [(i, j), (i + 1, j), (i, j + 1), (i + 1, j + 1)]]
            lowest = "m" if "moss" in ts else "p"  # render_ref.terr names: "moss" (m), "plains" (p)
            if ver == "now":
                n = RR.calm_number(i, j) % 32
                base = ld(os.path.join(V2T, f"{pre}{'forest' if lowest == 'm' else 'plains'}.grass.{n}.png"))
            else:
                swap = season == "winter" and "moss" in ts and "plains" in ts  # winter: forest edge over plains snow
                if swap:
                    base = tile_v3(g, "plains", i, j, season)
                    m = sum(b for b, t in zip((1, 2, 4, 8), ts) if t == "moss")
                    v = RR.edge_variant(g, "moss", m, i, j)
                    base = base.copy()
                    base.alpha_composite(ld(os.path.join(V3T, f"{pre}forest.grass.v3.edge.{m}.{v}.png")))
                    im.alpha_composite(base, (i * T, j * T))
                    continue
                base = tile_v3(g, "moss" if lowest == "m" else "plains", i, j, season)
            im.alpha_composite(base, (i * T, j * T))
            if lowest == "m" and "plains" in ts:
                m = sum(b for b, t in zip((1, 2, 4, 8), ts) if t == "plains")
                v = RR.edge_variant(g, "plains", m, i, j)
                key = f"{pre}plains.grass.edge.{m}.{v}.png" if ver == "now" else f"{pre}plains.grass.v3.edge.{m}.{v}.png"
                im.alpha_composite(ld(os.path.join(V2T if ver == "now" else V3T, key)), (i * T, j * T))
    return im, g


def things(g):
    """Trees and props on forest cells (feet in game px), from a hash: no grid."""
    out = []
    for y in range(1, H_T):
        for x in range(1, W_T):
            if not all(RR.terr(g, a, b) == "moss" for a in (x - 1, x, x + 1) for b in (y - 1, y, y + 1)):
                continue
            h = G.hsh(x, y, 77) % 100
            fx, fy = x * 16 + 8 + (G.hsh(x, y, 78) % 9) - 4, y * 16 + 14
            if h < 9:
                out.append(("tree", ("pine_s", "pine_s", "pine_l", "spruce", "birch")[G.hsh(x, y, 79) % 5], fx, fy))
            elif h < 14:
                out.append(("prop", ("fern", "fern", "toadstool", "log_moss", "rock_moss", "roots")[G.hsh(x, y, 80) % 6], fx, fy))
    return out


def scene(ver, season):
    im, g = ground(ver, season)
    d = 2 if ver == "now" else 4
    pre = PRE[season]
    for kind, name, fx, fy in sorted(things(g), key=lambda t: t[3]):
        if ver == "now":
            if kind != "tree":
                continue
            p = os.path.join(V2T, f"{pre}forest.pine.png")
            if not os.path.exists(p):
                p = os.path.join(V1T, f"{pre}forest.pine.png")
            sp = ld(p)
        else:
            f = 0
            sp = ld(os.path.join(V3T, f"{pre}forest.{'tree' if kind == 'tree' else 'prop'}.v3.{name}.{f}.png"))
        im.alpha_composite(sp, (fx * d - sp.width // 2, fy * d - sp.height))
    return im


def device(im, d, k, size, ox_tiles=12):
    """Crop the device view (k device px per texel at density d) starting `ox_tiles` tiles in."""
    s = k * (4 // d) if d == 4 else k * 2
    big = im.resize((im.width * s, im.height * s), Image.NEAREST)
    x0 = ox_tiles * 16 * 4 * k
    return big.crop((x0, 0, x0 + size[0], size[1]))


def items(path):
    rows = []
    for season, pre in PRE.items():
        cells = []
        p = os.path.join(V2T, f"{pre}forest.pine.png")
        a = ld(p)
        cells.append(a.resize((a.width * 4, a.height * 4), Image.NEAREST))
        for k in ("tree.v3.pine_s.0", "tree.v3.pine_l.0", "tree.v3.spruce.0", "tree.v3.birch.0", "prop.v3.fern.0",
                  "prop.v3.toadstool.0", "prop.v3.log_moss.0", "prop.v3.rock_moss.0", "prop.v3.roots.0"):
            b = ld(os.path.join(V3T, f"{pre}forest.{k}.png"))
            cells.append(b.resize((b.width * 2, b.height * 2), Image.NEAREST))
        W = sum(c.width + 16 for c in cells) + 16
        H = max(c.height for c in cells) + 24
        bg = (36, 72, 52, 255) if season != "winter" else (184, 200, 224, 255)
        r = Image.new("RGBA", (W, H), bg)
        x = 16
        for c in cells:
            r.alpha_composite(c, (x, H - 12 - c.height))
            x += c.width + 16
        rows.append(r)
    out = Image.new("RGBA", (max(r.width for r in rows), sum(r.height for r in rows)), (30, 30, 30, 255))
    y = 0
    for r in rows:
        out.alpha_composite(r, (0, y))
        y += r.height
    out.save(path, optimize=True)


def main(out):
    os.makedirs(out, exist_ok=True)
    for season in PRE:
        for ver in ("now", "v3"):
            im = scene(ver, season)
            d = 2 if ver == "now" else 4
            # 15 Pro k = 2: 1 game px = 8 device px; SE k = 1: 4 device px
            s15 = 8 // d
            big = im.resize((im.width * s15, im.height * s15), Image.NEAREST)
            x0 = 12 * 16 * 8
            big.crop((x0, 3 * 16 * 8, x0 + 2556, 3 * 16 * 8 + 1179)).save(os.path.join(out, f"{season}_15pro_{ver}_k2.png"), optimize=True)
            sse = 4 // d
            bse = im.resize((im.width * sse, im.height * sse), Image.NEAREST) if sse > 1 else im
            x0 = 12 * 16 * 4
            bse.crop((x0, 3 * 16 * 4, x0 + 1334, 3 * 16 * 4 + 750)).save(os.path.join(out, f"{season}_se_{ver}_k1.png"), optimize=True)
            half = im.resize((W_T * 32, H_T * 32), Image.NEAREST)  # v3: every other texel; now: 1 v2 px = 1 px
            half.save(os.path.join(out, f"{season}_48x24_{ver}_half.png"), optimize=True)
    items(os.path.join(out, "items_now_v3.png"))
    print(sorted(os.listdir(out)))


if __name__ == "__main__":
    main(sys.argv[1])
