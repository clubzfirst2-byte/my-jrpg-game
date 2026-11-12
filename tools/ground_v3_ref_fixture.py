"""Records what the art side's reference draws for the plains v3 ground on fixed maps, for
tests/unit/v3PlainsRef.test.js: the engine must pick exactly the same tiles.

  python3 tools/ground_v3_ref_fixture.py   ->  tests/fixtures/ground_v3_ref.json

The reference (none of it changed, only imported):
  - tools/art_v3/gen_ground_v3.py (STYLE.md 6): macro_of (the base pattern of a 4 x 4 block), flow_corner,
    flow_key (kind, corners, v) and the file names of ground_tile / write / write_edges
  - tools/terrain_v2/render_ref.py: every other ground, the water, and the plains grass edges' mask and v
    (render_v2, run as is; its drawing calls are recorded, as tools/ground_v2_ref_fixture.py does)
On top of render_v2's draws, as STYLE.md 6 says: a display tile whose lowest ground is plains gets the v3
base in place of the v2 tile; a display tile whose 4 corners are plains gets the flow shape of flow_key
(round 7: "<shape key>[~f]@<tint>", ~f = mirrored left to right, tint = flow_tints[season][kind]), a
world corner being 'm' (no flow) unless the 4 display tiles around it are full plains tiles; the plains
grass edges over a lower ground take the v3 edge of the same mask and v.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "terrain_v2"))
sys.path.insert(0, os.path.join(HERE, "art_v3"))
from PIL import Image  # noqa: E402
import render_ref  # noqa: E402
import gen_ground_v3 as G  # noqa: E402

PRE = {None: "", "autumn": "autumn.", "winter": "winter."}
REF_FLOW_CORNER = G.flow_corner


class Key:
    def __init__(self, k):
        self.k = k


class Images(dict):
    def __missing__(self, k):
        return Key(k)


def record_v2(grid, season=None):
    draws = {}

    def alpha_composite(self, im, dest=(0, 0), source=(0, 0)):
        i, j = (dest[0] - 16) // 32, (dest[1] - 16) // 32
        draws.setdefault((i, j), []).append(im.k)

    old = Image.Image.alpha_composite, Image.Image.paste
    Image.Image.alpha_composite = alpha_composite
    Image.Image.paste = lambda self, *a, **k: None
    try:
        render_ref.render_v2(grid, Images(), frame=0, season=season)
    finally:
        Image.Image.alpha_composite, Image.Image.paste = old
    return draws


def record_v3(grid, season=None):
    H, W = len(grid), len(grid[0])
    pre = PRE[season]
    full = lambda i, j: 0 <= i < W - 1 and 0 <= j < H - 1 and all(grid[j + dy][i + dx] == "p" for dx in (0, 1) for dy in (0, 1))

    def corner(cx, cy):
        if not all(full(cx + dx, cy + dy) for dx in (-1, 0) for dy in (-1, 0)):
            return "m"
        return REF_FLOW_CORNER(cx, cy)

    G.flow_corner = corner  # flow_key reads the module's flow_corner
    try:
        out = {}
        for (i, j), keys in record_v2(grid, season).items():
            ts = [render_ref.terr(grid, x, y) for x, y in ((i, j), (i + 1, j), (i, j + 1), (i + 1, j + 1))]
            land = [t for t in ts if t not in ("water", "other")]
            lowest = None if "water" in ts or not land else min(land, key=render_ref.PRIORITY.index)
            new = []
            for n, k in enumerate(keys):
                m = re.match(r"^(?:(?:autumn|winter)\.)?g2\.plains\.(.+)$", k)
                if m and n == 0 and lowest == "plains":
                    new.append(f"{pre}plains.grass.v3.{G.macro_of(i // 4, j // 4)}{j % 4}{i % 4}")
                    if full(i, j):
                        fk = G.flow_key(i, j)
                        if fk:  # (kind, bits, v, flip): the shape, mirrored or not, times FLOW_TINT[season][kind]
                            kind, bits, v, flip = fk
                            tint = G.flow_tints(season or "summer")[kind]
                            new.append(f"{G.FLOW_SETS[season or 'summer']}plains.grassflow.v3.{bits}.{v}{'~f' if flip else ''}@{tint}")
                    continue
                e = re.match(r"^e(\d+)\.(\d+)$", m.group(1)) if m else None
                if e:
                    new.append(f"{pre}plains.grass.v3.edge.{e.group(1)}.{e.group(2)}")
                    continue
                new.append(k)
            out[f"{i},{j}"] = "|".join(new)
        return out
    finally:
        G.flow_corner = REF_FLOW_CORNER


def plains_grid(W=72, H=56):
    """Plains with uneven borders to island grass, a path (1 and 2 cells wide), a pond, sand and moss."""
    h = render_ref.dhash
    rows = []
    for y in range(H):
        r = ""
        for x in range(W):
            wob = h(x // 3, y // 3) % 3 - 1
            c = "p"
            if x + wob < 6:
                c = "g"
            if y == 30 or (x == 44 + wob and y < 30) or (x in (20, 21) and y > 40):
                c = "="
            if 8 + wob <= y <= 14 and 26 <= x <= 36 + wob:
                c = "~"
            if 46 <= y <= 50 + wob and 52 <= x <= 60:
                c = "s"
            if y + wob > 52 and x > 50:
                c = "m"
            r += c
        rows.append(r)
    return rows


def main():
    out = {"maps": [], "macro": None, "flow": None}
    g = plains_grid()
    out["maps"].append({"name": "plains72x56.summer", "rows": g, "season": None, "draws": record_v3(g)})
    small = [r[:44] for r in g[:36]]
    for season in ("autumn", "winter"):
        out["maps"].append({"name": f"plains44x36.{season}", "rows": small, "season": season, "draws": record_v3(small, season)})
    # the reference's own picks over the world's range (display tiles from -1): the base pattern of each
    # block, the flow key of each display tile (no ground mask: flow_corner as it is)
    out["macro"] = {"bx0": -1, "by0": -1, "rows": ["".join(G.macro_of(bx, by) for bx in range(-1, 65)) for by in range(-1, 73)]}
    flow_rows = []
    for j in range(-4, 96):
        row = []
        for i in range(-4, 124):
            fk = G.flow_key(i, j)
            row.append("." if fk is None else f"{fk[0]}{fk[1]}.{fk[2]}{'f' if fk[3] else ''}")
        flow_rows.append(" ".join(row))
    out["flow"] = {"i0": -4, "j0": -4, "rows": flow_rows}
    out["tints"] = {s: G.flow_tints(s) for s in ("summer", "autumn", "winter")}
    out["stored"] = list(G.STORED)
    out["variants"] = {b: G.n_flow_variants(b) for b in G.STORED}
    path = os.path.join(HERE, "..", "tests", "fixtures", "ground_v3_ref.json")
    with open(path, "w") as f:
        json.dump(out, f, separators=(",", ":"))
    print(path, os.path.getsize(path))


if __name__ == "__main__":
    main()


def tiles_fixture(i0=54, j0=112, w=8, h=6):
    """tests/fixtures/ground_v3_tiles.<season>.png: gen_ground_v3.ground_tile (the reference's own
    composition: base, flow shape mirrored when flip, times FLOW_TINT) of the world's display tiles
    (i0 .. i0+w-1, j0 .. j0+h-1) — a meadow of the plains — side by side, for the E2E pixel check
    (tests/e2e/gfx-v3.spec.js); and the pieces each was composed of."""
    from PIL import Image
    out = {"i0": i0, "j0": j0, "w": w, "h": h, "pieces": {}}
    for season in ("summer", "autumn", "winter"):
        img = Image.new("RGBA", (w * 64, h * 64))
        keys = []
        for j in range(j0, j0 + h):
            row = []
            for i in range(i0, i0 + w):
                img.alpha_composite(G.ground_tile(i, j, season), ((i - i0) * 64, (j - j0) * 64))
                pre = PRE[None if season == "summer" else season]
                base = f"{pre}plains.grass.v3.{G.macro_of(i // 4, j // 4)}{j % 4}{i % 4}"
                fk = G.flow_key(i, j)
                flow = "" if not fk else f"|{G.FLOW_SETS[season]}plains.grassflow.v3.{fk[1]}.{fk[2]}{'~f' if fk[3] else ''}@{G.flow_tints(season)[fk[0]]}"
                row.append(base + flow)
            keys.append(row)
        img.save(os.path.join(HERE, "..", "tests", "fixtures", f"ground_v3_tiles.{season}.png"), optimize=True)
        out["pieces"][season] = keys
    with open(os.path.join(HERE, "..", "tests", "fixtures", "ground_v3_tiles.json"), "w") as f:
        json.dump(out, f, separators=(",", ":"))


if __name__ == "__main__":
    tiles_fixture()
