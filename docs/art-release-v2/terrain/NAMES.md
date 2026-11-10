# Ground v2 — key scheme (for wiring)

Folder `src/art-release-v2/terrain/`: **1914 PNGs** = 189 v1 keys redrawn + 1539 new keys + 186 v1 keys copied unchanged (not redrawn: ruin / wall faces, v1.1 shores, trees, rocks, floors…). The group **contains every key of the v1 terrain group**, so it can replace it as a whole (`manifest.json` lists the three groups; the test checks v2 ⊇ v1). All new / redrawn ground tiles are 32×32 art px (= one 16 px map cell), anchor **top-left**, alpha 0 / 255. Generator: `tools/terrain_v2/gen_v2.py`; `tools/terrain_v2/render_ref.py` is a reference renderer of everything below (the review images use it).

## 1. Grounds

| ground | prefix (= the v1 key) | tiles | picked by | macro pieces | seasons |
|---|---|---|---|---|---|
| island grass | `tile.grass` | `tile.grass.0` – `.15` | A: calm tile by hash | `.macro.0-3`, `.macro2.0-3` … `.macro8.0-3` | autumn (16 calm tiles + 8 pictures), winter (16 calm snow tiles + 8 pictures, with the plant's tips) |
| plains grass | `plains.grass` | `plains.grass.0` – `.15` | A: calm tile by hash | `.macro.0-3`, `.macro2.0-3` … `.macro8.0-3` | autumn (16 calm tiles + 8 pictures), winter (16 calm snow tiles + 8 pictures, with the plant's tips) |
| lake shore grass | `lake.grass` | `lake.grass.0` – `.15` | A: calm tile by hash | `.macro.0-3`, `.macro2.0-3` … `.macro8.0-3` | autumn (16 calm tiles + 8 pictures), winter (16 calm snow tiles + 8 pictures, with the plant's tips) |
| forest floor (moss) | `forest.grass` | `forest.grass.0` – `.15` | A: calm tile by hash | `.macro.0-3`, `.macro2.0-3` … `.macro8.0-3` | autumn (16 calm tiles + 8 pictures), winter (16 calm snow tiles + 8 pictures, with the plant's tips) |
| mountain snow | `mountains.snow` | `mountains.snow.0` – `.15` | A: calm tile by hash | `.macro.0-3`, `.macro2.0-3` … `.macro8.0-3` | — |
| island sand | `tile.sand` | `tile.sand`, `tile.sand.1` – `.63` | B: W / E phases | — | — |
| desert sand | `desert.sand` | `desert.sand.0` – `.63` | B: W / E phases | — | — |
| path | `tile.path` | `tile.path`, `tile.path.1` – `.15` | A: calm tile by hash | `.macro.0-3`, `.macro2.0-3` … `.macro8.0-3` | — |
| ruin floor | `tile.ruin` | `tile.ruin`, `tile.ruin.1` – `.65` | C: row phase + column symbols | — | — |

`hash(i, j)` = gameView's hash (render_ref.dhash). For tile.sand / tile.path / tile.ruin, n = 0 is the bare v1 key. `render_ref.py` does all of this.

**A. Island / plains / lake grass, moss, path, mountain snow, and the winter of the 4 seasonal grounds (round 4; 16 calm tiles + 8 pictures of 2×2 tiles):**
- **Pictures first.** Cut the display grid (section 2) into blocks of 3×3 display tiles. Block `(a, b)` covers display tiles `3a … 3a+2`, `3b … 3b+2`. Per block: `h = hash(a, b)`; the picture's NW tile is `(i0, j0) = (3a + h % 2, 3b + (h >> 1) % 2)` (**a hashed offset of 0 or 1 tile on each axis: pictures are NOT on even tiles and never touch**); picture number `m = (h >> 2) % 8`; **no picture** when `(h >> 5) % 8 == 0`, when the picture would leave the map, or when the 9 map cells under its 4 display tiles (cells `i0 … i0+2`, `j0 … j0+2`) are not all one ground of this scheme. The picture's 4 display tiles are drawn with `<prefix>.<name>.<q>`, name = `macro` (m = 0) or `macro<m+1>` (m = 1-7: `macro2` … `macro8`), q = 0 NW `(i0, j0)`, 1 NE, 2 SW, 3 SE.
- **Every other display tile** whose lowest ground is of this scheme: calm tile `n = hash(i + 3, j + 11) % 16`. Any calm tile joins any other and any picture (nothing crosses their edges), so no edge types.
- In winter the 4 seasonal grounds use the same rule with their `winter.` keys (snow with the tips of the ground's own plant); mountain snow has no seasons.
- Why: the 8 pictures carry the large things (thickets, lit patches, clover carpets / flowers / reeds, moss beds, worn stretches; on snow: blue hollows, drift swells, wind ridges, glints, capped stones), the calm tiles a grain and the small things (clumps, single clover in 4 forms, pebbles, needles, small hollows, glints…). Each kind's positions are spread evenly over x and y (in the pictures: all different modulo 32), so no 32- or 64-px pattern on average; the hashed offset keeps the pictures off a 64-px grid.

**B. Sand, desert sand (64 tiles; round 3):** only the W / E edges carry anything: the ripples cross them at one of 8 phases. `n = E + 8·W`, E / W = `(hash(2i, 2j+1) >> 8) % 8` for the vertical edge on the left of display tile (i, j) (W) and `(hash(2i+2, 2j+1) >> 8) % 8` on its right (E); 0 when the two tiles' lowest grounds differ. Nothing crosses the N / S edges. No pictures. Round 4: where the ripples bend from their W rows to their E rows depends on `(E − W) mod 8`, so the bends are not on the same columns in every tile.

**C. Ruin floor (66 tiles; round 3):** rectangular stones in straight courses 11 art px high that run across the whole map, their joints staggered course by course.
- row phase `R = (32·j) mod 11` = `(10·j) mod 11` (0-10), the same for a whole row of display tiles (j ≥ 0)
- column symbol `s(i)` (0-2) of the vertical line of edges at the west of column i (i ≥ 0), never the same on two neighbouring lines: `k = floor(i / 2)`, `e0 = hash(k, 7) % 3`, `e1 = hash(k + 1, 7) % 3`; `s = e0` when i is even; when i is odd, `s = 3 − e0 − e1` if `e0 ≠ e1`, else `(e0 + 1 + hash(k, 11) % 2) % 3`
- `W = s(i)`, `E = s(i + 1)`, `n = 6·R + 2·W + (E if E < W else E − 1)`
- the ruin's overlay over water is `tile.ruin.edge.<mask>.<R>` (R = 0-10, the same row phase), so the courses run on from the overlay into the full tiles beside it. No pictures.

**Changes in round 4** (for the engine): scheme A replaces the round-3 edge types of the grass-likes, moss and path (no `N + 2E + 4S + 8W`, no P %), and now also covers mountain snow and the 4 winter sets (round 3: B with 64 tiles). `.macro3` is now a 2×2 picture like the others. Keys removed (all were new in v2; every v1 key stays): `*.macro3.4-8`, `mountains.snow.16-63`, `winter.<4 grounds>.16-63`. Keys added: `*.macro4.0-3` … `*.macro8.0-3`, and `.macro.0-3` … `.macro8.0-3` of `mountains.snow` and of the 4 winter sets.
- **Seasons:** `autumn.<key>` / `winter.<key>` for every key of the 4 seasonal grounds (the existing season-key scheme). `autumn.mountains.snow.*` stays the v1.1 art (copied).
- Measured (`check.txt`): the repeat measure of the first inspection (mean |ΔL| at 32 px ÷ at 24 px) and the banding measure (autocorrelation of the row means and of the column means at 32 px and at 64 px), 80×48 fields.

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
- `autumn.forest.grass.macro3.*` — 4
- `autumn.forest.grass.macro4.*` — 4
- `autumn.forest.grass.macro5.*` — 4
- `autumn.forest.grass.macro6.*` — 4
- `autumn.forest.grass.macro7.*` — 4
- `autumn.forest.grass.macro8.*` — 4
- `autumn.lake.grass.*` — 12
- `autumn.lake.grass.edge.*` — 28
- `autumn.lake.grass.macro.*` — 4
- `autumn.lake.grass.macro2.*` — 4
- `autumn.lake.grass.macro3.*` — 4
- `autumn.lake.grass.macro4.*` — 4
- `autumn.lake.grass.macro5.*` — 4
- `autumn.lake.grass.macro6.*` — 4
- `autumn.lake.grass.macro7.*` — 4
- `autumn.lake.grass.macro8.*` — 4
- `autumn.plains.grass.*` — 12
- `autumn.plains.grass.edge.*` — 28
- `autumn.plains.grass.macro.*` — 4
- `autumn.plains.grass.macro2.*` — 4
- `autumn.plains.grass.macro3.*` — 4
- `autumn.plains.grass.macro4.*` — 4
- `autumn.plains.grass.macro5.*` — 4
- `autumn.plains.grass.macro6.*` — 4
- `autumn.plains.grass.macro7.*` — 4
- `autumn.plains.grass.macro8.*` — 4
- `autumn.tile.grass.*` — 13
- `autumn.tile.grass.edge.*` — 28
- `autumn.tile.grass.macro.*` — 4
- `autumn.tile.grass.macro2.*` — 4
- `autumn.tile.grass.macro3.*` — 4
- `autumn.tile.grass.macro4.*` — 4
- `autumn.tile.grass.macro5.*` — 4
- `autumn.tile.grass.macro6.*` — 4
- `autumn.tile.grass.macro7.*` — 4
- `autumn.tile.grass.macro8.*` — 4
- `desert.sand.*` — 61
- `desert.sand.edge.*` — 28
- `forest.grass.*` — 12
- `forest.grass.edge.*` — 28
- `forest.grass.macro.*` — 4
- `forest.grass.macro2.*` — 4
- `forest.grass.macro3.*` — 4
- `forest.grass.macro4.*` — 4
- `forest.grass.macro5.*` — 4
- `forest.grass.macro6.*` — 4
- `forest.grass.macro7.*` — 4
- `forest.grass.macro8.*` — 4
- `lake.grass.*` — 12
- `lake.grass.edge.*` — 28
- `lake.grass.macro.*` — 4
- `lake.grass.macro2.*` — 4
- `lake.grass.macro3.*` — 4
- `lake.grass.macro4.*` — 4
- `lake.grass.macro5.*` — 4
- `lake.grass.macro6.*` — 4
- `lake.grass.macro7.*` — 4
- `lake.grass.macro8.*` — 4
- `mountains.snow.*` — 12
- `mountains.snow.edge.*` — 28
- `mountains.snow.macro.*` — 4
- `mountains.snow.macro2.*` — 4
- `mountains.snow.macro3.*` — 4
- `mountains.snow.macro4.*` — 4
- `mountains.snow.macro5.*` — 4
- `mountains.snow.macro6.*` — 4
- `mountains.snow.macro7.*` — 4
- `mountains.snow.macro8.*` — 4
- `plains.grass.*` — 12
- `plains.grass.edge.*` — 28
- `plains.grass.macro.*` — 4
- `plains.grass.macro2.*` — 4
- `plains.grass.macro3.*` — 4
- `plains.grass.macro4.*` — 4
- `plains.grass.macro5.*` — 4
- `plains.grass.macro6.*` — 4
- `plains.grass.macro7.*` — 4
- `plains.grass.macro8.*` — 4
- `tile.grass.*` — 13
- `tile.grass.edge.*` — 28
- `tile.grass.macro.*` — 4
- `tile.grass.macro2.*` — 4
- `tile.grass.macro3.*` — 4
- `tile.grass.macro4.*` — 4
- `tile.grass.macro5.*` — 4
- `tile.grass.macro6.*` — 4
- `tile.grass.macro7.*` — 4
- `tile.grass.macro8.*` — 4
- `tile.path.*` — 15
- `tile.path.edge.*` — 28
- `tile.path.macro.*` — 4
- `tile.path.macro2.*` — 4
- `tile.path.macro3.*` — 4
- `tile.path.macro4.*` — 4
- `tile.path.macro5.*` — 4
- `tile.path.macro6.*` — 4
- `tile.path.macro7.*` — 4
- `tile.path.macro8.*` — 4
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
- `winter.forest.grass.*` — 12
- `winter.forest.grass.edge.*` — 28
- `winter.forest.grass.macro.*` — 4
- `winter.forest.grass.macro2.*` — 4
- `winter.forest.grass.macro3.*` — 4
- `winter.forest.grass.macro4.*` — 4
- `winter.forest.grass.macro5.*` — 4
- `winter.forest.grass.macro6.*` — 4
- `winter.forest.grass.macro7.*` — 4
- `winter.forest.grass.macro8.*` — 4
- `winter.lake.grass.*` — 12
- `winter.lake.grass.edge.*` — 28
- `winter.lake.grass.macro.*` — 4
- `winter.lake.grass.macro2.*` — 4
- `winter.lake.grass.macro3.*` — 4
- `winter.lake.grass.macro4.*` — 4
- `winter.lake.grass.macro5.*` — 4
- `winter.lake.grass.macro6.*` — 4
- `winter.lake.grass.macro7.*` — 4
- `winter.lake.grass.macro8.*` — 4
- `winter.plains.grass.*` — 12
- `winter.plains.grass.edge.*` — 28
- `winter.plains.grass.macro.*` — 4
- `winter.plains.grass.macro2.*` — 4
- `winter.plains.grass.macro3.*` — 4
- `winter.plains.grass.macro4.*` — 4
- `winter.plains.grass.macro5.*` — 4
- `winter.plains.grass.macro6.*` — 4
- `winter.plains.grass.macro7.*` — 4
- `winter.plains.grass.macro8.*` — 4
- `winter.tile.grass.*` — 13
- `winter.tile.grass.edge.*` — 28
- `winter.tile.grass.macro.*` — 4
- `winter.tile.grass.macro2.*` — 4
- `winter.tile.grass.macro3.*` — 4
- `winter.tile.grass.macro4.*` — 4
- `winter.tile.grass.macro5.*` — 4
- `winter.tile.grass.macro6.*` — 4
- `winter.tile.grass.macro7.*` — 4
- `winter.tile.grass.macro8.*` — 4

Redrawn v1 keys: `autumn.face.earth.top-base.4`, `autumn.face.earth.top-base.4.v1`, `autumn.face.earth.top-base.4.v2`, `autumn.face.earth.top-base.8`, `autumn.face.earth.top-base.8.v1`, `autumn.face.earth.top-base.8.v2`, `autumn.face.earth.top.4`, `autumn.face.earth.top.4.v1`, `autumn.face.earth.top.4.v2`, `autumn.face.earth.top.8`, `autumn.face.earth.top.8.v1`, `autumn.face.earth.top.8.v2`, `autumn.face.stone.top-base.4`, `autumn.face.stone.top-base.4.v1`, `autumn.face.stone.top-base.4.v2`, `autumn.face.stone.top-base.8`, `autumn.face.stone.top-base.8.v1`, `autumn.face.stone.top-base.8.v2`, `autumn.face.stone.top.4`, `autumn.face.stone.top.4.v1`, `autumn.face.stone.top.4.v2`, `autumn.face.stone.top.8`, `autumn.face.stone.top.8.v1`, `autumn.face.stone.top.8.v2`, `autumn.forest.grass.0`, `autumn.forest.grass.1`, `autumn.forest.grass.2`, `autumn.forest.grass.3`, `autumn.lake.grass.0`, `autumn.lake.grass.1`, `autumn.lake.grass.2`, `autumn.lake.grass.3`, `autumn.plains.grass.0`, `autumn.plains.grass.1`, `autumn.plains.grass.2`, `autumn.plains.grass.3`, `autumn.tile.grass.0`, `autumn.tile.grass.1`, `autumn.tile.grass.2`, `desert.sand.0`, `desert.sand.1`, `desert.sand.2`, `face.desert.mid-base.4`, `face.desert.mid-base.4.v1`, `face.desert.mid-base.8`, `face.desert.mid-base.8.v1`, `face.desert.mid.4`, `face.desert.mid.4.v1`, `face.desert.mid.8`, `face.desert.mid.8.v1`, `face.desert.top-base.4`, `face.desert.top-base.4.v1`, `face.desert.top-base.8`, `face.desert.top-base.8.v1`, `face.desert.top.4`, `face.desert.top.4.v1`, `face.desert.top.8`, `face.desert.top.8.v1`, `face.earth.mid-base.4`, `face.earth.mid-base.4.v1`, `face.earth.mid-base.4.v2`, `face.earth.mid-base.8`, `face.earth.mid-base.8.v1`, `face.earth.mid-base.8.v2`, `face.earth.mid.4`, `face.earth.mid.4.v1`, `face.earth.mid.4.v2`, `face.earth.mid.8`, `face.earth.mid.8.v1`, `face.earth.mid.8.v2`, `face.earth.top-base.4`, `face.earth.top-base.4.v1`, `face.earth.top-base.4.v2`, `face.earth.top-base.8`, `face.earth.top-base.8.v1`, `face.earth.top-base.8.v2`, `face.earth.top.4`, `face.earth.top.4.v1`, `face.earth.top.4.v2`, `face.earth.top.8`, `face.earth.top.8.v1`, `face.earth.top.8.v2`, `face.path.mid-base.4`, `face.path.mid-base.4.v1`, `face.path.mid-base.8`, `face.path.mid-base.8.v1`, `face.path.mid.4`, `face.path.mid.4.v1`, `face.path.mid.8`, `face.path.mid.8.v1`, `face.path.top-base.4`, `face.path.top-base.4.v1`, `face.path.top-base.8`, `face.path.top-base.8.v1`, `face.path.top.4`, `face.path.top.4.v1`, `face.path.top.8`, `face.path.top.8.v1`, `face.sand.mid-base.4`, `face.sand.mid-base.4.v1`, `face.sand.mid-base.8`, `face.sand.mid-base.8.v1`, `face.sand.mid.4`, `face.sand.mid.4.v1`, `face.sand.mid.8`, `face.sand.mid.8.v1`, `face.sand.top-base.4`, `face.sand.top-base.4.v1`, `face.sand.top-base.8`, `face.sand.top-base.8.v1`, `face.sand.top.4`, `face.sand.top.4.v1`, `face.sand.top.8`, `face.sand.top.8.v1`, `face.stone.mid-base.4`, `face.stone.mid-base.4.v1`, `face.stone.mid-base.4.v2`, `face.stone.mid-base.8`, `face.stone.mid-base.8.v1`, `face.stone.mid-base.8.v2`, `face.stone.mid.4`, `face.stone.mid.4.v1`, `face.stone.mid.4.v2`, `face.stone.mid.8`, `face.stone.mid.8.v1`, `face.stone.mid.8.v2`, `face.stone.top-base.4`, `face.stone.top-base.4.v1`, `face.stone.top-base.4.v2`, `face.stone.top-base.8`, `face.stone.top-base.8.v1`, `face.stone.top-base.8.v2`, `face.stone.top.4`, `face.stone.top.4.v1`, `face.stone.top.4.v2`, `face.stone.top.8`, `face.stone.top.8.v1`, `face.stone.top.8.v2`, `forest.grass.0`, `forest.grass.1`, `forest.grass.2`, `forest.grass.3`, `lake.grass.0`, `lake.grass.1`, `lake.grass.2`, `lake.grass.3`, `mountains.snow.0`, `mountains.snow.1`, `mountains.snow.2`, `mountains.snow.3`, `plains.grass.0`, `plains.grass.1`, `plains.grass.2`, `plains.grass.3`, `tile.grass.0`, `tile.grass.1`, `tile.grass.2`, `tile.path`, `tile.ruin`, `tile.sand`, `tile.water.0`, `tile.water.1`, `winter.face.earth.top-base.4`, `winter.face.earth.top-base.4.v1`, `winter.face.earth.top-base.4.v2`, `winter.face.earth.top-base.8`, `winter.face.earth.top-base.8.v1`, `winter.face.earth.top-base.8.v2`, `winter.face.earth.top.4`, `winter.face.earth.top.4.v1`, `winter.face.earth.top.4.v2`, `winter.face.earth.top.8`, `winter.face.earth.top.8.v1`, `winter.face.earth.top.8.v2`, `winter.forest.grass.0`, `winter.forest.grass.1`, `winter.forest.grass.2`, `winter.forest.grass.3`, `winter.lake.grass.0`, `winter.lake.grass.1`, `winter.lake.grass.2`, `winter.lake.grass.3`, `winter.plains.grass.0`, `winter.plains.grass.1`, `winter.plains.grass.2`, `winter.plains.grass.3`, `winter.tile.grass.0`, `winter.tile.grass.1`, `winter.tile.grass.2`.
