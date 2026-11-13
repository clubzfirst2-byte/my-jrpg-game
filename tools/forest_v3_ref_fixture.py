"""Records what the art side's reference draws for the forest v3 ground on fixed maps, for
tests/unit/v3Forest.test.js: the engine must pick exactly the same tiles.

  python3 tools/forest_v3_ref_fixture.py   ->  tests/fixtures/forest_v3_ref.json

The reference (none of it changed, only imported):
  - tools/terrain_v2/render_ref.py: render_v2 (every ground's v2 layers, the edges' mask and v), its drawing
    calls recorded as tools/ground_v3_ref_fixture.py does
  - tools/art_v3/gen_ground_v3.py: macro_of, flow_corner, flow_key (the forest uses the plains' rules, FOREST.md 1)
  - tools/art_v3/gen_forest_v3.py: FOREST_FLOW_TINT (flow_tints), the flow sets
  - tools/art_v3/compare_forest_v3.py: winter_forest_v (NAMES.md 2.1, the winter forest / plains exchange)
On top of render_v2's draws (FOREST.md 1, STYLE.md 6): a display tile whose lowest ground is the forest moss
(the plains) gets the forest (plains) v3 base; a full tile of either gets its flow shape (a world corner 'm'
unless the 4 display tiles around it are full tiles of that ground); the forest (plains) edges over a lower
ground take the v3 edge of the same mask and v. Winter: a display tile with forest and plains corners is the
plains winter base and the forest winter edge, mask = the forest corners, v = winter_forest_v.

The maps: compare_forest_v3.grid() (the art side's), the inspection's border map (independent inspection 3,
gfx_r1/ins_v3_forest3/tools/maps.py border_map, its rows kept in tests/fixtures/forest_v3_maps.json), 3 random
maps (forest 50 %), and a forest with a path, sand and a pond (the forest edges over lower grounds).
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "terrain_v2"))
sys.path.insert(0, os.path.join(HERE, "art_v3"))
import render_ref as RR  # noqa: E402
import gen_ground_v3 as G  # noqa: E402
import gen_forest_v3 as F  # noqa: E402
import compare_forest_v3 as C  # noqa: E402
from ground_v3_ref_fixture import record_v2  # noqa: E402

PRE = {"summer": "", "autumn": "autumn.", "winter": "winter."}
REF_FLOW_CORNER = G.flow_corner
LETTER = {"moss": "m", "plains": "p"}
NAME = {"moss": "forest", "plains": "plains"}


def flow_keys(grid, cls):
    """flow_key of every display tile with the corners masked for ground cls (as ground_v3_ref_fixture)."""
    H, W = len(grid), len(grid[0])
    ch = LETTER[cls]
    full = lambda i, j: 0 <= i < W - 1 and 0 <= j < H - 1 and all(grid[j + dy][i + dx] == ch for dx in (0, 1) for dy in (0, 1))

    def corner(cx, cy):
        if not all(full(cx + dx, cy + dy) for dx in (-1, 0) for dy in (-1, 0)):
            return "m"
        return REF_FLOW_CORNER(cx, cy)

    G.flow_corner = corner
    G.is_full.cache_clear()
    try:
        return {(i, j): G.flow_key(i, j) for j in range(H - 1) for i in range(W - 1) if full(i, j)}
    finally:
        G.flow_corner = REF_FLOW_CORNER
        G.is_full.cache_clear()


def record(grid, season):
    pre = PRE[season]
    flows = {c: flow_keys(grid, c) for c in ("moss", "plains")}
    tints = {"moss": F.flow_tints(season), "plains": G.flow_tints(season)}
    sets = {"moss": F.FLOW_SETS[season], "plains": G.FLOW_SETS[season]}
    out = {}
    v2 = record_v2(grid, None if season == "summer" else season)
    for (i, j), keys in v2.items():
        ts = [RR.terr(grid, x, y) for x, y in ((i, j), (i + 1, j), (i, j + 1), (i + 1, j + 1))]
        land = [t for t in ts if t not in ("water", "other")]
        lowest = None if "water" in ts or not land else min(land, key=RR.PRIORITY.index)
        if season == "winter" and "moss" in ts and "plains" in ts:
            assert set(ts) <= {"moss", "plains"}, (i, j, ts)  # (these maps: the pair alone)
            m = sum(b for b, t in zip((1, 2, 4, 8), ts) if t == "moss")
            out[f"{i},{j}"] = f"{pre}plains.grass.v3.{G.macro_of(i // 4, j // 4)}{j % 4}{i % 4}|{pre}forest.grass.v3.edge.{m}.{C.winter_forest_v(grid, m, i, j)}"
            continue
        new = []
        for n, k in enumerate(keys):
            m = re.match(r"^(?:(?:autumn|winter)\.)?g2\.(moss|plains)\.(.+)$", k)
            if m and n == 0 and lowest == m.group(1):
                cls = m.group(1)
                new.append(f"{pre}{NAME[cls]}.grass.v3.{G.macro_of(i // 4, j // 4)}{j % 4}{i % 4}")
                fk = flows[cls].get((i, j))
                if fk:
                    kind, bits, v, flip = fk
                    new.append(f"{sets[cls]}{NAME[cls]}.grassflow.v3.{bits}.{v}{'~f' if flip else ''}@{tints[cls][kind]}")
                continue
            e = re.match(r"^e(\d+)\.(\d+)$", m.group(2)) if m else None
            if e:
                new.append(f"{pre}{NAME[m.group(1)]}.grass.v3.edge.{e.group(1)}.{e.group(2)}")
                continue
            new.append(k)
        out[f"{i},{j}"] = "|".join(new)
    return out


def random_map(seed, W=40, H=30):
    return ["".join("m" if G.hsh(x // 2 + seed * 101, y // 2, 4000 + seed) % 2 else "p" for x in range(W)) for y in range(H)]


def forest_path_map(W=56, H=40):
    """Forest moss with a winding path, a sandy clearing and a pond (no plains: the forest / plains pair is the other maps')."""
    h = RR.dhash
    rows = []
    for y in range(H):
        r = ""
        for x in range(W):
            wob = h(x // 3, y // 3) % 3 - 1
            c = "m"
            if y == 18 + wob or x == 30 + wob:
                c = "="
            if 6 <= y <= 11 + wob and 8 <= x <= 16:
                c = "s"
            if 26 <= y <= 31 and 40 + wob <= x <= 48:
                c = "~"
            r += c
        rows.append(r)
    return rows


def main():
    with open(os.path.join(HERE, "..", "tests", "fixtures", "forest_v3_maps.json")) as f:
        inspection = json.load(f)["border_map"]
    maps = [("compare48x24", [r.replace("f", "m") for r in C.grid()]), ("inspection73x41", [r.replace("f", "m") for r in inspection])]
    maps += [(f"random{s}", random_map(s)) for s in (1, 2, 3)]
    maps.append(("forestpath56x40", forest_path_map()))
    out = {"maps": [], "tints": {s: F.flow_tints(s) for s in PRE}}
    for name, g in maps:
        for season in PRE:
            if name.startswith("random") and season != "winter":
                continue
            out["maps"].append({"name": f"{name}.{season}", "rows": g, "season": None if season == "summer" else season, "draws": record(g, season)})
    path = os.path.join(HERE, "..", "tests", "fixtures", "forest_v3_ref.json")
    with open(path, "w") as f:
        json.dump(out, f, separators=(",", ":"))
    print(path, os.path.getsize(path))


if __name__ == "__main__":
    main()
