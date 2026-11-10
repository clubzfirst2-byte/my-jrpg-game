# Ground v2 — key scheme (for wiring)

Folder `src/art-release-v2/terrain/`: **1058 PNGs** = 57 v1 keys redrawn + 683 new keys + 318 v1 keys copied unchanged (not redrawn this round: cliff faces, v1.1 shores, trees, rocks, floors…). The group **contains every key of the v1 terrain group**, so it can replace it as a whole (`manifest.json` lists the three groups; the test checks v2 ⊇ v1). All new / redrawn tiles are 32×32 art px (= one 16 px map cell), anchor **top-left**, alpha 0 / 255. Generator: `tools/terrain_v2/gen_v2.py`; `tools/terrain_v2/render_ref.py` is a reference renderer of everything below (the review images use it).

## 1. Grounds

| ground | prefix (= the v1 key) | base | variants | macro 2×2 | seasons |
|---|---|---|---|---|---|
| island grass | `tile.grass` | `tile.grass.0` | `tile.grass.1` – `tile.grass.3` | `tile.grass.macro.0` – `.3` | autumn, winter |
| plains grass | `plains.grass` | `plains.grass.0` | `plains.grass.1` – `plains.grass.3` | `plains.grass.macro.0` – `.3` | autumn, winter |
| lake shore grass | `lake.grass` | `lake.grass.0` | `lake.grass.1` – `lake.grass.3` | `lake.grass.macro.0` – `.3` | autumn, winter |
| forest floor (moss) | `forest.grass` | `forest.grass.0` | `forest.grass.1` – `forest.grass.3` | `forest.grass.macro.0` – `.3` | autumn, winter |
| mountain snow | `mountains.snow` | `mountains.snow.0` | `mountains.snow.1` – `mountains.snow.3` | `mountains.snow.macro.0` – `.3` | — |
| island sand | `tile.sand` | `tile.sand` | `tile.sand.1` – `tile.sand.3` | `tile.sand.macro.0` – `.3` | — |
| desert sand | `desert.sand` | `desert.sand.0` | `desert.sand.1` – `desert.sand.3` | `desert.sand.macro.0` – `.3` | — |
| path | `tile.path` | `tile.path` | `tile.path.1` – `tile.path.3` | `tile.path.macro.0` – `.3` | — |
| ruin floor | `tile.ruin` | `tile.ruin` | `tile.ruin.1` – `tile.ruin.3` | `tile.ruin.macro.0` – `.3` | — |

- **Base** (`.0`, or the bare v1 key for sand / path / ruin) is the calm tile; `.1` – `.3` carry the features (clumps, flowers, reeds, pebbles, roots, drifts, cracks…). 4 variants this round (the engine can use up to 8: pick the base on about two thirds of the ground, in noise patches, and `.1`–`.3` elsewhere).
- **Macro** `<prefix>.macro.<q>`, q = 0 NW, 1 NE, 2 SW, 3 SE: one 64×64 picture cut in four, for a flat 2×2 block of the same ground with no water edge.
- **Seasons:** `autumn.<key>` / `winter.<key>` for every key of the 4 seasonal grounds (the existing season-key scheme). `autumn.mountains.snow.*` stays the v1.1 art (copied).
- All base / variant / macro tiles of a ground join each other in any order (a shared 2-px edge band; the generator and the test check it). Macro pieces join each other only in their 2×2 arrangement.

## 2. Transitions — dual grid, 4 corners, layered overlays

**Scheme.** Draw the ground on a grid shifted by half a cell (+8, +8 game px). Display tile `(i, j)` covers the centres of 4 map cells: **NW = (i, j), NE = (i+1, j), SW = (i, j+1), SE = (i+1, j+1)**, and is drawn at game px `(i*16 + 8, j*16 + 8)`. Each corner has the terrain of its cell.

1. Draw the full ground tile (section 1) of the **lowest-priority** terrain among the 4 corners.
2. For each **higher** terrain present, low to high, draw `<prefix>.edge.<mask>.<v>` with **mask = sum of the corners whose terrain priority is >= this terrain's: NW 1, NE 2, SW 4, SE 8** (1-14). If a higher terrain has all 4 corners, draw its base tile instead.
3. `<v>` = 0 or 1, any per-tile hash (they join each other).

**Priority**, low → high: water (section 3) < `tile.ruin` < `tile.path` < `desert.sand` < `tile.sand` < `mountains.snow` < `forest.grass` < `lake.grass` < `plains.grass` < `tile.grass`.
Grass-like edges lie over path / sand / ruin, sand drifts over path and ruin, snow over path and ruin, every land over water. One set of 14 masks × 2 variants per terrain covers every pair it can meet (world map cell edges: lake|sand 1720, grass|ruin 884, moss|path 880, plains|path 780, grass|sand 672, dsand|grass 427, ruin|snow 396, grass|path 369, path|snow 287, lake|path 214, …).

Seasons: `autumn.<prefix>.edge.<mask>.<v>` / `winter.<prefix>.edge.<mask>.<v>` for the 4 seasonal grounds (winter edges are snow edges). The priority does not change.

Notes:
- The border follows the map cells' edges (± a few px of drawn wobble): collision does not change, a 1-cell path stays 1 cell wide.
- **Height:** blend only corners of the same height; where they differ, draw each cell's own tile as today and let the cliff faces separate them. (The review images are flat.)
- Grounds without v2 art (wood, wall top, metal, pit, dark) stay on the cell grid (their v1 keys, copied).

## 3. Water (4 frames)

| key | what |
|---|---|
| `tile.water.<f>`, `tile.water.v1.<f>` | shallow water, 2 variants, frames f = 0-3 (`tile.water.0` / `.1` are the v1 keys, redrawn) |
| `tile.water.deep.<f>`, `tile.water.deep.v1.<f>` | deep water |
| `tile.water.deep.edge.<mask>.<f>` | deep over shallow (mask = deep corners, 1-14) |
| `tile.water.foam.<mask>.<f>` | shore foam over the water (mask = LAND corners, 1-14), lapping in and out |

- A water cell is **deep** when no land cell is within 2 cells (Chebyshev), otherwise **shallow** (the shallow band follows every shore).
- Display tile with water corners: shallow `.<f>` (deep if all 4 corners are deep); if deep corners are mixed, `tile.water.deep.edge.<mask>.<f>`; if any corner is land, `tile.water.foam.<landmask>.<f>`; then the land overlays of section 2 (water is the lowest terrain).
- All water keys switch frames together, 4 frames (suggested 0.25–0.3 s each). Water tiles change 12–30 px per frame (guide 3.5); a foam overlay changes 16–40 px on a straight shore (72 on a diagonal 2-shore tile).
- This replaces the v1.1 water edges (`tile.shore.*`, `tile.shore-desert.*`, `tile.bank.*`, still in the folder, copied): a shore is now foam overlay + the land's own overlay.

## 4. New keys by group

- `autumn.forest.grass.edge.*` — 28
- `autumn.forest.grass.macro.*` — 4
- `autumn.lake.grass.edge.*` — 28
- `autumn.lake.grass.macro.*` — 4
- `autumn.plains.grass.edge.*` — 28
- `autumn.plains.grass.macro.*` — 4
- `autumn.tile.grass.*` — 1
- `autumn.tile.grass.edge.*` — 28
- `autumn.tile.grass.macro.*` — 4
- `desert.sand.*` — 1
- `desert.sand.edge.*` — 28
- `desert.sand.macro.*` — 4
- `forest.grass.edge.*` — 28
- `forest.grass.macro.*` — 4
- `lake.grass.edge.*` — 28
- `lake.grass.macro.*` — 4
- `mountains.snow.edge.*` — 28
- `mountains.snow.macro.*` — 4
- `plains.grass.edge.*` — 28
- `plains.grass.macro.*` — 4
- `tile.grass.*` — 1
- `tile.grass.edge.*` — 28
- `tile.grass.macro.*` — 4
- `tile.path.*` — 3
- `tile.path.edge.*` — 28
- `tile.path.macro.*` — 4
- `tile.ruin.*` — 3
- `tile.ruin.edge.*` — 28
- `tile.ruin.macro.*` — 4
- `tile.sand.*` — 3
- `tile.sand.edge.*` — 28
- `tile.sand.macro.*` — 4
- `tile.water.*` — 2
- `tile.water.deep.*` — 4
- `tile.water.deep.edge.*` — 56
- `tile.water.deep.v1.*` — 4
- `tile.water.foam.*` — 56
- `tile.water.v1.*` — 4
- `winter.forest.grass.edge.*` — 28
- `winter.forest.grass.macro.*` — 4
- `winter.lake.grass.edge.*` — 28
- `winter.lake.grass.macro.*` — 4
- `winter.plains.grass.edge.*` — 28
- `winter.plains.grass.macro.*` — 4
- `winter.tile.grass.*` — 1
- `winter.tile.grass.edge.*` — 28
- `winter.tile.grass.macro.*` — 4

Redrawn v1 keys: `autumn.forest.grass.0`, `autumn.forest.grass.1`, `autumn.forest.grass.2`, `autumn.forest.grass.3`, `autumn.lake.grass.0`, `autumn.lake.grass.1`, `autumn.lake.grass.2`, `autumn.lake.grass.3`, `autumn.plains.grass.0`, `autumn.plains.grass.1`, `autumn.plains.grass.2`, `autumn.plains.grass.3`, `autumn.tile.grass.0`, `autumn.tile.grass.1`, `autumn.tile.grass.2`, `desert.sand.0`, `desert.sand.1`, `desert.sand.2`, `forest.grass.0`, `forest.grass.1`, `forest.grass.2`, `forest.grass.3`, `lake.grass.0`, `lake.grass.1`, `lake.grass.2`, `lake.grass.3`, `mountains.snow.0`, `mountains.snow.1`, `mountains.snow.2`, `mountains.snow.3`, `plains.grass.0`, `plains.grass.1`, `plains.grass.2`, `plains.grass.3`, `tile.grass.0`, `tile.grass.1`, `tile.grass.2`, `tile.path`, `tile.ruin`, `tile.sand`, `tile.water.0`, `tile.water.1`, `winter.forest.grass.0`, `winter.forest.grass.1`, `winter.forest.grass.2`, `winter.forest.grass.3`, `winter.lake.grass.0`, `winter.lake.grass.1`, `winter.lake.grass.2`, `winter.lake.grass.3`, `winter.plains.grass.0`, `winter.plains.grass.1`, `winter.plains.grass.2`, `winter.plains.grass.3`, `winter.tile.grass.0`, `winter.tile.grass.1`, `winter.tile.grass.2`.
