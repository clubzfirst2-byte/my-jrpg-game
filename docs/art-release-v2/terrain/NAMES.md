# Ground v2 — key scheme (for wiring)

Folder `src/art-release-v2/terrain/`: **1859 PNGs** = 189 v1 keys redrawn + 1484 new keys + 186 v1 keys copied unchanged (not redrawn: ruin / wall faces, v1.1 shores, trees, rocks, floors…). The group **contains every key of the v1 terrain group**, so it can replace it as a whole (`manifest.json` lists the three groups; the test checks v2 ⊇ v1). All new / redrawn ground tiles are 32×32 art px (= one 16 px map cell), anchor **top-left**, alpha 0 / 255. Generator: `tools/terrain_v2/gen_v2.py`; `tools/terrain_v2/render_ref.py` is a reference renderer of everything below (the review images use it).

## 1. Grounds

| ground | prefix (= the v1 key) | tiles | picked by | macro pieces | seasons |
|---|---|---|---|---|---|
| island grass | `tile.grass` | `tile.grass.0` – `.15` | A: 4 edge types, P = 22 % | `.macro.0-3`, `.macro2.0-3`, `.macro3.0-8` | autumn (16 tiles + macros), winter (64 tiles, as snow) |
| plains grass | `plains.grass` | `plains.grass.0` – `.15` | A: 4 edge types, P = 10 % | `.macro.0-3`, `.macro2.0-3`, `.macro3.0-8` | autumn (16 tiles + macros), winter (64 tiles, as snow) |
| lake shore grass | `lake.grass` | `lake.grass.0` – `.15` | A: 4 edge types, P = 10 % | `.macro.0-3`, `.macro2.0-3`, `.macro3.0-8` | autumn (16 tiles + macros), winter (64 tiles, as snow) |
| forest floor (moss) | `forest.grass` | `forest.grass.0` – `.15` | A: 4 edge types, P = 12 % | `.macro.0-3`, `.macro2.0-3`, `.macro3.0-8` | autumn (16 tiles + macros), winter (64 tiles, as snow) |
| mountain snow | `mountains.snow` | `mountains.snow.0` – `.63` | B: W / E phases | — | — |
| island sand | `tile.sand` | `tile.sand`, `tile.sand.1` – `.63` | B: W / E phases | — | — |
| desert sand | `desert.sand` | `desert.sand.0` – `.63` | B: W / E phases | — | — |
| path | `tile.path` | `tile.path`, `tile.path.1` – `.15` | A: 4 edge types, P = 10 % | `.macro.0-3`, `.macro2.0-3`, `.macro3.0-8` | — |
| ruin floor | `tile.ruin` | `tile.ruin`, `tile.ruin.1` – `.65` | C: row phase + column symbols | — | — |

The tiles are edge-matched, so no ground repeats every 32 px. `hash` = gameView's hash. Display tile (i, j) (section 2) has the vertical edge `hash(2i, 2j+1)` on its left and the horizontal edge `hash(2i+1, 2j)` above it. For tile.sand / tile.path / tile.ruin, n = 0 is the bare v1 key. `render_ref.py` does all of this.

**A. Grass-likes, moss, path (16 tiles):** every edge has a type 0 / 1; `n = N + 2·E + 4·S + 8·W` (N = the type of the top edge, E right, S bottom, W left). Type 1 when `id % 100 < P`; type 0 when the two tiles' lowest grounds differ, or the edge is on the outside of a macro block. What crosses a type-1 edge (a swale, a clump, a moss bed, a worn stretch) continues in the next tile. An engine noise patch may raise or lower P. Island grass (round 3): P = 22 %, and its own feature, clover carpets in white bloom.

**B. Sand, desert sand, snow, and the winter of the 4 seasonal grounds (64 tiles; round 3):** only the W / E edges carry anything: the ripples / wind ridges cross them at one of 8 phases. `n = E + 8·W`, E / W = `(id >> 8) % 8` of that vertical edge; 0 when the two tiles' lowest grounds differ. Nothing crosses the N / S edges. No macro pieces. (Every row of a tile is a ripple crest in exactly one phase, so the rows' brightness has no 32-px period.)

**C. Ruin floor (66 tiles; round 3):** rectangular stones in straight courses 11 art px high that run across the whole map, their joints staggered course by course.
- row phase `R = (32·j) mod 11` = `(10·j) mod 11` (0-10), the same for a whole row of display tiles (j ≥ 0)
- column symbol `s(i)` (0-2) of the vertical line of edges at the west of column i (i ≥ 0), never the same on two neighbouring lines: `k = floor(i / 2)`, `e0 = hash(k, 7) % 3`, `e1 = hash(k + 1, 7) % 3`; `s = e0` when i is even; when i is odd, `s = 3 − e0 − e1` if `e0 ≠ e1`, else `(e0 + 1 + hash(k, 11) % 2) % 3`
- `W = s(i)`, `E = s(i + 1)`, `n = 6·R + 2·W + (E if E < W else E − 1)`
- the ruin's overlay over water is `tile.ruin.edge.<mask>.<R>` (R = 0-10, the same row phase), so the courses run on from the overlay into the full tiles beside it. No macro pieces.

**Macro pieces** (A only; all with type-0 outer edges, so force the edges around a placed block to type 0):
- `<prefix>.macro3.<q>` 3×3 (q = 0-8 in reading order), `<prefix>.macro.<q>` and `<prefix>.macro2.<q>` 2×2 (q = 0 NW, 1 NE, 2 SW, 3 SE)
- render_ref: 3×3 blocks at i, j multiples of 3 whose 16 corner cells are one land ground, `hash(i, j) % 6 == 0`; then 2×2 blocks at even i, j (9 corner cells one ground, not overlapping): `hash(i+1, j) % 4`: 0 → `.macro`, 1 → `.macro2`. Not in winter (the winter grounds are snow: B).
- **Seasons:** `autumn.<key>` / `winter.<key>` for every key of the 4 seasonal grounds (the existing season-key scheme); winter has the 64 snow tiles (with a few buried tips) and no macros. `autumn.mountains.snow.*` stays the v1.1 art (copied).
- Measured (`check.txt`): the repeat measure of the first inspection (mean |ΔL| at 32 px ÷ at 24 px, 40×24 fields) and the banding measure of the second (autocorrelation at 32 px of the row means and of the column means).

## 2. Transitions — dual grid, 4 corners, layered overlays

**Scheme.** Draw the ground on a grid shifted by half a cell (+8, +8 game px). Display tile `(i, j)` covers the centres of 4 map cells: **NW = (i, j), NE = (i+1, j), SW = (i, j+1), SE = (i+1, j+1)**, and is drawn at game px `(i*16 + 8, j*16 + 8)`. Each corner has the terrain of its cell.

1. Draw the full ground tile (section 1) of the **lowest-priority** terrain among the 4 corners.
2. For each **higher** terrain present, low to high, draw `<prefix>.edge.<mask>.<v>` with **mask = sum of the corners whose terrain priority is >= this terrain's: NW 1, NE 2, SW 4, SE 8** (1-14). If a higher terrain has all 4 corners, draw its base tile instead.
3. `<v>` = 0 or 1, any per-tile hash (they join each other). The ruin floor: `<v>` = its row phase R, 0-10 (section 1 C).

**Priority**, low → high: water (section 3) < `tile.ruin` < `tile.path` < `desert.sand` < `tile.sand` < `mountains.snow` < `forest.grass` < `lake.grass` < `plains.grass` < `tile.grass`.
Grass-like edges lie over path / sand / ruin, sand drifts over path and ruin, snow over path and ruin, every land over water. One set of 14 masks × 2 variants (ruin: × 11 row phases) per terrain covers every pair it can meet (world map cell edges: lake|sand 1720, grass|ruin 884, moss|path 880, plains|path 780, grass|sand 672, dsand|grass 427, ruin|snow 396, grass|path 369, path|snow 287, lake|path 214, …).

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

- A water cell is **deep** when no land cell is within 2 cells (Chebyshev) **and it lies in a 2×2 block of such cells** (so a 1-cell-wide strip stays shallow: no dark 1-cell trenches); otherwise **shallow** (the shallow band follows every shore).
- Display tile with water corners: shallow `.<f>` (deep if all 4 corners are deep); if deep corners are mixed, `tile.water.deep.edge.<mask>.<f>`; if any corner is land, `tile.water.foam.<landmask>.<f>`; then the land overlays of section 2 (water is the lowest terrain).
- All water keys switch frames together, 4 frames (suggested 0.25–0.3 s each). Water tiles change 12–30 px per frame (guide 3.5); a foam overlay changes at most 36 px (on the diagonal 2-shore tiles 6 / 9 only one shore laps).
- This replaces the v1.1 water edges (`tile.shore.*`, `tile.shore-desert.*`, `tile.bank.*`, still in the folder, copied): a shore is now foam overlay + the land's own overlay.

## 4. Cliff faces (round 3: redrawn under the v1 keys)

`face.<earth|stone|sand|desert|path>.<top|mid|mid-base|top-base>.<4|8>` with the variants `.v1` / `.v2` (sand, desert, path: `.v1` only), and the season lips `autumn.face.earth.*`, `winter.face.earth.*`, `autumn.face.stone.*` (top / top-base): **the same keys, sizes (32×16 for `.8`, 32×8 for `.4`), stacking and variant rule as v1** (gameView.addFace, terrainArt.faceVariant), so nothing changes in the engine. Variants join each other (same outermost columns). `face.ruin.*` and `face.wall.*` (masonry, house walls) are the v1 files, copied.

## 5. New keys by group

- `autumn.forest.grass.*` — 12
- `autumn.forest.grass.edge.*` — 28
- `autumn.forest.grass.macro.*` — 4
- `autumn.forest.grass.macro2.*` — 4
- `autumn.forest.grass.macro3.*` — 9
- `autumn.lake.grass.*` — 12
- `autumn.lake.grass.edge.*` — 28
- `autumn.lake.grass.macro.*` — 4
- `autumn.lake.grass.macro2.*` — 4
- `autumn.lake.grass.macro3.*` — 9
- `autumn.plains.grass.*` — 12
- `autumn.plains.grass.edge.*` — 28
- `autumn.plains.grass.macro.*` — 4
- `autumn.plains.grass.macro2.*` — 4
- `autumn.plains.grass.macro3.*` — 9
- `autumn.tile.grass.*` — 13
- `autumn.tile.grass.edge.*` — 28
- `autumn.tile.grass.macro.*` — 4
- `autumn.tile.grass.macro2.*` — 4
- `autumn.tile.grass.macro3.*` — 9
- `desert.sand.*` — 61
- `desert.sand.edge.*` — 28
- `forest.grass.*` — 12
- `forest.grass.edge.*` — 28
- `forest.grass.macro.*` — 4
- `forest.grass.macro2.*` — 4
- `forest.grass.macro3.*` — 9
- `lake.grass.*` — 12
- `lake.grass.edge.*` — 28
- `lake.grass.macro.*` — 4
- `lake.grass.macro2.*` — 4
- `lake.grass.macro3.*` — 9
- `mountains.snow.*` — 60
- `mountains.snow.edge.*` — 28
- `plains.grass.*` — 12
- `plains.grass.edge.*` — 28
- `plains.grass.macro.*` — 4
- `plains.grass.macro2.*` — 4
- `plains.grass.macro3.*` — 9
- `tile.grass.*` — 13
- `tile.grass.edge.*` — 28
- `tile.grass.macro.*` — 4
- `tile.grass.macro2.*` — 4
- `tile.grass.macro3.*` — 9
- `tile.path.*` — 15
- `tile.path.edge.*` — 28
- `tile.path.macro.*` — 4
- `tile.path.macro2.*` — 4
- `tile.path.macro3.*` — 9
- `tile.ruin.*` — 65
- `tile.ruin.edge.*` — 154
- `tile.sand.*` — 63
- `tile.sand.edge.*` — 28
- `tile.water.*` — 2
- `tile.water.deep.*` — 4
- `tile.water.deep.edge.*` — 56
- `tile.water.deep.v1.*` — 4
- `tile.water.foam.*` — 56
- `tile.water.v1.*` — 4
- `winter.forest.grass.*` — 60
- `winter.forest.grass.edge.*` — 28
- `winter.lake.grass.*` — 60
- `winter.lake.grass.edge.*` — 28
- `winter.plains.grass.*` — 60
- `winter.plains.grass.edge.*` — 28
- `winter.tile.grass.*` — 61
- `winter.tile.grass.edge.*` — 28

Redrawn v1 keys: `autumn.face.earth.top-base.4`, `autumn.face.earth.top-base.4.v1`, `autumn.face.earth.top-base.4.v2`, `autumn.face.earth.top-base.8`, `autumn.face.earth.top-base.8.v1`, `autumn.face.earth.top-base.8.v2`, `autumn.face.earth.top.4`, `autumn.face.earth.top.4.v1`, `autumn.face.earth.top.4.v2`, `autumn.face.earth.top.8`, `autumn.face.earth.top.8.v1`, `autumn.face.earth.top.8.v2`, `autumn.face.stone.top-base.4`, `autumn.face.stone.top-base.4.v1`, `autumn.face.stone.top-base.4.v2`, `autumn.face.stone.top-base.8`, `autumn.face.stone.top-base.8.v1`, `autumn.face.stone.top-base.8.v2`, `autumn.face.stone.top.4`, `autumn.face.stone.top.4.v1`, `autumn.face.stone.top.4.v2`, `autumn.face.stone.top.8`, `autumn.face.stone.top.8.v1`, `autumn.face.stone.top.8.v2`, `autumn.forest.grass.0`, `autumn.forest.grass.1`, `autumn.forest.grass.2`, `autumn.forest.grass.3`, `autumn.lake.grass.0`, `autumn.lake.grass.1`, `autumn.lake.grass.2`, `autumn.lake.grass.3`, `autumn.plains.grass.0`, `autumn.plains.grass.1`, `autumn.plains.grass.2`, `autumn.plains.grass.3`, `autumn.tile.grass.0`, `autumn.tile.grass.1`, `autumn.tile.grass.2`, `desert.sand.0`, `desert.sand.1`, `desert.sand.2`, `face.desert.mid-base.4`, `face.desert.mid-base.4.v1`, `face.desert.mid-base.8`, `face.desert.mid-base.8.v1`, `face.desert.mid.4`, `face.desert.mid.4.v1`, `face.desert.mid.8`, `face.desert.mid.8.v1`, `face.desert.top-base.4`, `face.desert.top-base.4.v1`, `face.desert.top-base.8`, `face.desert.top-base.8.v1`, `face.desert.top.4`, `face.desert.top.4.v1`, `face.desert.top.8`, `face.desert.top.8.v1`, `face.earth.mid-base.4`, `face.earth.mid-base.4.v1`, `face.earth.mid-base.4.v2`, `face.earth.mid-base.8`, `face.earth.mid-base.8.v1`, `face.earth.mid-base.8.v2`, `face.earth.mid.4`, `face.earth.mid.4.v1`, `face.earth.mid.4.v2`, `face.earth.mid.8`, `face.earth.mid.8.v1`, `face.earth.mid.8.v2`, `face.earth.top-base.4`, `face.earth.top-base.4.v1`, `face.earth.top-base.4.v2`, `face.earth.top-base.8`, `face.earth.top-base.8.v1`, `face.earth.top-base.8.v2`, `face.earth.top.4`, `face.earth.top.4.v1`, `face.earth.top.4.v2`, `face.earth.top.8`, `face.earth.top.8.v1`, `face.earth.top.8.v2`, `face.path.mid-base.4`, `face.path.mid-base.4.v1`, `face.path.mid-base.8`, `face.path.mid-base.8.v1`, `face.path.mid.4`, `face.path.mid.4.v1`, `face.path.mid.8`, `face.path.mid.8.v1`, `face.path.top-base.4`, `face.path.top-base.4.v1`, `face.path.top-base.8`, `face.path.top-base.8.v1`, `face.path.top.4`, `face.path.top.4.v1`, `face.path.top.8`, `face.path.top.8.v1`, `face.sand.mid-base.4`, `face.sand.mid-base.4.v1`, `face.sand.mid-base.8`, `face.sand.mid-base.8.v1`, `face.sand.mid.4`, `face.sand.mid.4.v1`, `face.sand.mid.8`, `face.sand.mid.8.v1`, `face.sand.top-base.4`, `face.sand.top-base.4.v1`, `face.sand.top-base.8`, `face.sand.top-base.8.v1`, `face.sand.top.4`, `face.sand.top.4.v1`, `face.sand.top.8`, `face.sand.top.8.v1`, `face.stone.mid-base.4`, `face.stone.mid-base.4.v1`, `face.stone.mid-base.4.v2`, `face.stone.mid-base.8`, `face.stone.mid-base.8.v1`, `face.stone.mid-base.8.v2`, `face.stone.mid.4`, `face.stone.mid.4.v1`, `face.stone.mid.4.v2`, `face.stone.mid.8`, `face.stone.mid.8.v1`, `face.stone.mid.8.v2`, `face.stone.top-base.4`, `face.stone.top-base.4.v1`, `face.stone.top-base.4.v2`, `face.stone.top-base.8`, `face.stone.top-base.8.v1`, `face.stone.top-base.8.v2`, `face.stone.top.4`, `face.stone.top.4.v1`, `face.stone.top.4.v2`, `face.stone.top.8`, `face.stone.top.8.v1`, `face.stone.top.8.v2`, `forest.grass.0`, `forest.grass.1`, `forest.grass.2`, `forest.grass.3`, `lake.grass.0`, `lake.grass.1`, `lake.grass.2`, `lake.grass.3`, `mountains.snow.0`, `mountains.snow.1`, `mountains.snow.2`, `mountains.snow.3`, `plains.grass.0`, `plains.grass.1`, `plains.grass.2`, `plains.grass.3`, `tile.grass.0`, `tile.grass.1`, `tile.grass.2`, `tile.path`, `tile.ruin`, `tile.sand`, `tile.water.0`, `tile.water.1`, `winter.face.earth.top-base.4`, `winter.face.earth.top-base.4.v1`, `winter.face.earth.top-base.4.v2`, `winter.face.earth.top-base.8`, `winter.face.earth.top-base.8.v1`, `winter.face.earth.top-base.8.v2`, `winter.face.earth.top.4`, `winter.face.earth.top.4.v1`, `winter.face.earth.top.4.v2`, `winter.face.earth.top.8`, `winter.face.earth.top.8.v1`, `winter.face.earth.top.8.v2`, `winter.forest.grass.0`, `winter.forest.grass.1`, `winter.forest.grass.2`, `winter.forest.grass.3`, `winter.lake.grass.0`, `winter.lake.grass.1`, `winter.lake.grass.2`, `winter.lake.grass.3`, `winter.plains.grass.0`, `winter.plains.grass.1`, `winter.plains.grass.2`, `winter.plains.grass.3`, `winter.tile.grass.0`, `winter.tile.grass.1`, `winter.tile.grass.2`.
