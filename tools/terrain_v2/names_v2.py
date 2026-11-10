"""Writes docs/art-release-v2/terrain/NAMES.md (the key scheme for the terrain engineer)."""

from keys_v2 import PREFIX, SINGLE
from transitions import PRIORITY
from wang import P_TYPE1

LABEL = {"grass": "island grass", "plains": "plains grass", "lake": "lake shore grass", "moss": "forest floor (moss)",
         "snow": "mountain snow", "sand": "island sand", "dsand": "desert sand", "path": "path", "ruin": "ruin floor"}


def names_md(files, redrawn, new, copied):
    L = []
    a = L.append
    a("# Ground v2 — key scheme (for wiring)")
    a("")
    a(f"Folder `src/art-release-v2/terrain/`: **{len(files) + len(copied)} PNGs** = {len(redrawn)} v1 keys redrawn + "
      f"{len(new)} new keys + {len(copied)} v1 keys copied unchanged (not redrawn this round: cliff faces, v1.1 shores, "
      "trees, rocks, floors…). The group **contains every key of the v1 terrain group**, so it can replace it as a whole "
      "(`manifest.json` lists the three groups; the test checks v2 ⊇ v1). All new / redrawn tiles are 32×32 art px "
      "(= one 16 px map cell), anchor **top-left**, alpha 0 / 255. Generator: `tools/terrain_v2/gen_v2.py`; "
      "`tools/terrain_v2/render_ref.py` is a reference renderer of everything below (the review images use it).")
    a("")
    a("## 1. Grounds")
    a("")
    a("| ground | prefix (= the v1 key) | tiles | macro pieces | P(type 1) | seasons |")
    a("|---|---|---|---|---|---|")
    for g, p in PREFIX.items():
        base = f"`{p}`, `{p}.1` – `.15`" if g in SINGLE else f"`{p}.0` – `.15`"
        seas = "autumn, winter" if g in ("grass", "plains", "lake", "moss") else "—"
        a(f"| {LABEL[g]} | `{p}` | {base} | `.macro.0-3`, `.macro2.0-3`, `.macro3.0-8` | {P_TYPE1[g]} % | {seas} |")
    a("")
    a("**Round 2 (after the inspection): the tiles are edge-matched (Wang tiles), so the ground does not repeat every "
      "32 px.** Every edge between two display tiles has a type, 0 or 1. A ground tile is picked by its 4 edge types:")
    a("")
    a("    n = N + 2·E + 4·S + 8·W      (N = type of its top edge, E right, S bottom, W left)  ->  `<prefix>.<n>`")
    a("")
    a("(for tile.sand / tile.path / tile.ruin, n = 0 is the bare v1 key.) Two tiles that share an edge agree on its "
      "type, so whatever crosses that edge (a swale, a clump, a moss bed, a worn stretch, a sand ripple, a snow ridge, a "
      "paving joint) continues into the next tile; the generator and the test check that every tile with the same type "
      "on a side has the same 2-px band there.")
    a("")
    a("**Edge type** (`render_ref.edge_type`):")
    a("- the vertical edge left of display tile (i, j) has id `hash(2i, 2j+1)`, the horizontal edge above it `hash(2i+1, 2j)` "
      "(`hash` = gameView's hash); type 1 when `id % 100 < P`, P per ground in the table (the season's look: winter "
      "grass-like grounds use the snow P)")
    a("- type 0 when the two tiles' lowest grounds differ, or the edge is on the outside of a macro block")
    a("- with P = 10 %, `.0` (all 4 edges type 0, the calm base) covers about two thirds of a grass / path ground "
      "(0.9⁴ = 66 %); an engine noise patch may raise P (busier ground) or lower it. Sand, snow and ruin are all "
      "texture (ripples / ridges / paving that every tile continues): P = 50 % there.")
    a("")
    a("**Macro pieces** (all with type-0 outer edges, so force the edges around a placed block to type 0):")
    a("- `<prefix>.macro3.<q>` 3×3 (q = 0-8 in reading order), `<prefix>.macro.<q>` and `<prefix>.macro2.<q>` 2×2 (q = 0 NW, "
      "1 NE, 2 SW, 3 SE)")
    a("- render_ref: 3×3 blocks at i, j multiples of 3 whose 16 corner cells are one land ground, `hash(i, j) % 6 == 0` "
      "(sand / snow / ruin: `% 12`); then 2×2 blocks at even i, j (9 corner cells one ground, not overlapping): "
      "`hash(i+1, j) % 4` (sand / snow / ruin `% 8`): 0 → `.macro`, 1 → `.macro2`")
    a("- **Seasons:** `autumn.<key>` / `winter.<key>` for every key of the 4 seasonal grounds (the existing season-key "
      "scheme). `autumn.mountains.snow.*` stays the v1.1 art (copied).")
    a("- The repeat measure of the inspection (mean |ΔL| at 32 px ÷ at 24 px, 40×24 fields) is in `check.txt`: all ≥ 0.8.")
    a("")


    a("## 2. Transitions — dual grid, 4 corners, layered overlays")
    a("")
    a("**Scheme.** Draw the ground on a grid shifted by half a cell (+8, +8 game px). Display tile `(i, j)` covers the "
      "centres of 4 map cells: **NW = (i, j), NE = (i+1, j), SW = (i, j+1), SE = (i+1, j+1)**, and is drawn at game px "
      "`(i*16 + 8, j*16 + 8)`. Each corner has the terrain of its cell.")
    a("")
    a("1. Draw the full ground tile (section 1) of the **lowest-priority** terrain among the 4 corners.")
    a("2. For each **higher** terrain present, low to high, draw `<prefix>.edge.<mask>.<v>` with **mask = sum of the "
      "corners whose terrain priority is >= this terrain's: NW 1, NE 2, SW 4, SE 8** (1-14). If a higher terrain has all "
      "4 corners, draw its base tile instead.")
    a("3. `<v>` = 0 or 1, any per-tile hash (they join each other).")
    a("")
    a("**Priority**, low → high: water (section 3) < " + " < ".join(f"`{PREFIX[p]}`" for p in PRIORITY) + ".")
    a("Grass-like edges lie over path / sand / ruin, sand drifts over path and ruin, snow over path and ruin, every land "
      "over water. One set of 14 masks × 2 variants per terrain covers every pair it can meet (world map cell edges: "
      "lake|sand 1720, grass|ruin 884, moss|path 880, plains|path 780, grass|sand 672, dsand|grass 427, ruin|snow 396, "
      "grass|path 369, path|snow 287, lake|path 214, …).")
    a("")
    a("Seasons: `autumn.<prefix>.edge.<mask>.<v>` / `winter.<prefix>.edge.<mask>.<v>` for the 4 seasonal grounds (winter "
      "edges are snow edges). The priority does not change.")
    a("")
    a("Notes:")
    a("- The border follows the map cells' edges (± a few px of drawn wobble): collision does not change, a 1-cell path "
      "stays 1 cell wide.")
    a("- **Height:** blend only corners of the same height; where they differ, draw each cell's own tile as today and let "
      "the cliff faces separate them. (The review images are flat.)")
    a("- Grounds without v2 art (wood, wall top, metal, pit, dark) stay on the cell grid (their v1 keys, copied).")
    a("")
    a("## 3. Water (4 frames)")
    a("")
    a("| key | what |")
    a("|---|---|")
    a("| `tile.water.<f>`, `tile.water.v1.<f>` | shallow water, 2 variants, frames f = 0-3 (`tile.water.0` / `.1` are the v1 keys, redrawn) |")
    a("| `tile.water.deep.<f>`, `tile.water.deep.v1.<f>` | deep water |")
    a("| `tile.water.deep.edge.<mask>.<f>` | deep over shallow (mask = deep corners, 1-14) |")
    a("| `tile.water.foam.<mask>.<f>` | shore foam over the water (mask = LAND corners, 1-14), lapping in and out |")
    a("")
    a("- A water cell is **deep** when no land cell is within 2 cells (Chebyshev) **and it lies in a 2×2 block of such "
      "cells** (so a 1-cell-wide strip stays shallow: no dark 1-cell trenches); otherwise **shallow** (the shallow band "
      "follows every shore).")
    a("- Display tile with water corners: shallow `.<f>` (deep if all 4 corners are deep); if deep corners are mixed, "
      "`tile.water.deep.edge.<mask>.<f>`; if any corner is land, `tile.water.foam.<landmask>.<f>`; then the land "
      "overlays of section 2 (water is the lowest terrain).")
    a("- All water keys switch frames together, 4 frames (suggested 0.25–0.3 s each). Water tiles change 12–30 px per "
      "frame (guide 3.5); a foam overlay changes at most 36 px (on the diagonal 2-shore tiles 6 / 9 only one shore laps).")
    a("- This replaces the v1.1 water edges (`tile.shore.*`, `tile.shore-desert.*`, `tile.bank.*`, still in the folder, "
      "copied): a shore is now foam overlay + the land's own overlay.")
    a("")
    a("## 4. New keys by group")
    a("")
    groups = {}
    for k in sorted(new):
        if ".edge." in k:
            head = k.split(".edge.")[0] + ".edge.*"
        elif ".macro" in k:
            head = k.rsplit(".", 1)[0] + ".*"
        elif ".foam." in k:
            head = k.rsplit(".", 2)[0] + ".*"
        else:
            head = k.rsplit(".", 1)[0] + ".*"
        groups[head] = groups.get(head, 0) + 1
    for head, n in groups.items():
        a(f"- `{head}` — {n}")
    a("")
    a("Redrawn v1 keys: " + ", ".join(f"`{k}`" for k in redrawn) + ".")
    a("")
    return "\n".join(L)
