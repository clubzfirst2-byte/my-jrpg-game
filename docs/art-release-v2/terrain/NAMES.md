# Ground v2 — key scheme (for wiring)

Folder `src/art-release-v2/terrain/`: **1882 PNGs** = 189 v1 keys redrawn + 1507 new keys + 186 v1 keys copied unchanged (not redrawn: ruin / wall faces, v1.1 shores, trees, rocks, floors…). The group **contains every key of the v1 terrain group**, so it can replace it as a whole (`manifest.json` lists the three groups; the test checks v2 ⊇ v1). All new / redrawn ground tiles are 32×32 art px (= one 16 px map cell), anchor **top-left**, alpha 0 / 255. Generator: `tools/terrain_v2/gen_v2.py`; `tools/terrain_v2/render_ref.py` is a reference renderer of everything below (the review images use it).

## 1. Grounds

| ground | prefix (= the v1 key) | tiles | picked by | macro pieces | seasons |
|---|---|---|---|---|---|
| island grass | `tile.grass` | `tile.grass.0` – `.15` | A: calm tile by hash | `.macro.0-3`, `.macro2.0-3` … `.macro8.0-3` | autumn (16 calm tiles + 8 pictures), winter (16 calm snow tiles + 8 pictures, with the plant's tips) |
| plains grass | `plains.grass` | `plains.grass.0` – `.15` | A: calm tile by hash | `.macro.0-3`, `.macro2.0-3` … `.macro8.0-3` | autumn (16 calm tiles + 8 pictures), winter (16 calm snow tiles + 8 pictures, with the plant's tips) |
| lake shore grass | `lake.grass` | `lake.grass.0` – `.15` | A: calm tile by hash | `.macro.0-3`, `.macro2.0-3` … `.macro8.0-3` | autumn (16 calm tiles + 8 pictures), winter (16 calm snow tiles + 8 pictures, with the plant's tips) |
| forest floor (moss) | `forest.grass` | `forest.grass.0` – `.15` | A: calm tile by hash | `.macro.0-3`, `.macro2.0-3` … `.macro8.0-3` | autumn (16 calm tiles + 8 pictures), winter (16 calm snow tiles + 8 pictures, with the plant's tips) |
| mountain snow | `mountains.snow` | `mountains.snow.0` – `.15` | A: calm tile by hash | `.macro.0-3`, `.macro2.0-3` … `.macro8.0-3` | — |
| island sand | `tile.sand` | `tile.sand`, `tile.sand.1` – `.15` | A: calm tile by hash | `.macro.0-3`, `.macro2.0-3` … `.macro8.0-3` | — |
| desert sand | `desert.sand` | `desert.sand.0` – `.15` | A: calm tile by hash | `.macro.0-3`, `.macro2.0-3` … `.macro8.0-3` | — |
| path | `tile.path` | `tile.path`, `tile.path.1` – `.15` | A: calm tile by hash | `.macro.0-3`, `.macro2.0-3` … `.macro8.0-3` | — |
| ruin floor | `tile.ruin` | `tile.ruin`, `tile.ruin.1` – `.65` | C: row phase + column symbols | — | — |

`hash(i, j)` = gameView's hash (render_ref.dhash). For tile.sand / tile.path / tile.ruin, n = 0 is the bare v1 key. `render_ref.py` does all of this.

**A. Every ground except the ruin floor (round 5; 16 calm tiles + 8 pictures of 2×2 tiles):** island / plains / lake grass, moss, path, mountain snow, island sand, desert sand, and the autumn / winter sets of the 4 seasonal grounds. Integer `hash` values are unsigned 32-bit; `/` below is a float division.

1. **Blocks.** Cut the display grid (section 2) into blocks of 3×3 display tiles; block `(a, b)` covers display tiles `3a … 3a+2`, `3b … 3b+2`. Every block (a, b ≥ 0, and one block past the map's right / bottom edge) is looked at; `h = hash(a, b)`.
2. **Is there a picture?** Density noise over the blocks, a value noise on a lattice of 4 blocks: `v(x, y) = (hash(x + 5003, y + 7919) % 1024) / 1023`; `gx = floor(a / 4)`, `gy = floor(b / 4)`, `fx = (a % 4 + 0.5) / 4`, `fy = (b % 4 + 0.5) / 4`, `sx = fx·fx·(3 − 2·fx)`, `sy = fy·fy·(3 − 2·fy)`; `top = v(gx, gy) + (v(gx+1, gy) − v(gx, gy))·sx`, `bot = v(gx, gy+1) + (v(gx+1, gy+1) − v(gx, gy+1))·sx`, `n = top + (bot − top)·sy`. `pNone = min(1, max(0, 2·(n − 0.3)))`. The block has a picture when `((h >> 16) % 1024) / 1024 >= pNone` (thick where n < 0.3, bare where n > 0.8: clusters and open stretches).
3. **Where in the block.** `OFF = [0, 0, 1, 2, 2, 2]`; raw offsets `rx(a, b) = OFF[hash(a, b) % 6]`, `ry(a, b) = OFF[(hash(a, b) >> 8) % 6]`. Then, in this order: `ox = rx(a, b)`, `oy = ry(a, b)`; if `ox == 2` and `rx(a+1, b) == 0`: `ox = 1`; if `oy == 2` and `ry(a, b+1) == 0`: `oy = 1`; if `ox == 2` and `oy == 2` and `rx(a+1, b+1) == 0` and `ry(a+1, b+1) == 0`: `oy = 1`; if `ox == 2` and `oy == 0` and `rx(a+1, b−1) == 0` and `ry(a+1, b−1) == 2`: `ox = 1`. The picture's NW display tile is `(i0, j0) = (3a + ox, 3b + oy)`; with offset 2 it reaches one tile into the next block. These rules keep pictures from overlapping (they can touch along an edge), and the chances (1/3, 1/6, 1/2) make every column and row of a block equally often covered (no 96-px period).
4. **Which picture** (no two side-by-side blocks share one): raw number `r(a, b) = hash(a + 409, b + 1031) % 8`. When `a + b` is even, `m = r(a, b)`. When `a + b` is odd: `free` = the numbers 0-7, in increasing order, that are none of `r(a−1, b)`, `r(a+1, b)`, `r(a, b−1)`, `r(a, b+1)`; `m = free[floor(hash(a + 409, b + 1031) / 8) % len(free)]`. Name: `macro` for m = 0, else `macro<m+1>` (`macro2` … `macro8`).
5. **Draw it** only when it stays on the map (`i0 + 2`, `j0 + 2` inside) and the 9 map cells under its 4 display tiles (cells `i0 … i0+2`, `j0 … j0+2`) are all one ground of this scheme: `<prefix>.<name>.<q>`, q = 0 NW `(i0, j0)`, 1 NE, 2 SW, 3 SE.
6. **Every other display tile** whose lowest ground is of this scheme: calm tile `n = hash(i + 3, j + 11) % 16`. Any calm tile joins any other and any picture (nothing crosses their edges).

In winter the 4 seasonal grounds use the same rule with their `winter.` keys (snow with the tips of the ground's own plant), in autumn with their `autumn.` keys. The pictures carry the large things (grass: thickets, lit patches, flower clusters / reeds, island clover carpets in white bloom - 2 of the 8 pictures wide ones; moss beds, worn stretches; snow: blue hollows, drift swells, wind ridges, glints, capped stones; sand: ripple fields, dune swells, pale smooth stretches, pebble clusters, shells / dry grass), the calm tiles a grain and the small things. Each kind's positions are spread evenly over x and y (in the pictures: one per 2 or 4 px modulo 32), and the mean row / column brightness of the 16 calm tiles and of the 32 picture quarters is evened out with grain specks, so no 32- / 64-px pattern on average.

**C. Ruin floor (66 tiles; round 3):** rectangular stones in straight courses 11 art px high that run across the whole map, their joints staggered course by course.
- row phase `R = (32·j) mod 11` = `(10·j) mod 11` (0-10), the same for a whole row of display tiles (j ≥ 0)
- column symbol `s(i)` (0-2) of the vertical line of edges at the west of column i (i ≥ 0), never the same on two neighbouring lines: `k = floor(i / 2)`, `e0 = hash(k, 7) % 3`, `e1 = hash(k + 1, 7) % 3`; `s = e0` when i is even; when i is odd, `s = 3 − e0 − e1` if `e0 ≠ e1`, else `(e0 + 1 + hash(k, 11) % 2) % 3`
- `W = s(i)`, `E = s(i + 1)`, `n = 6·R + 2·W + (E if E < W else E − 1)`
- the ruin's overlay over water is `tile.ruin.edge.<mask>.<R>` (R = 0-10, the same row phase), so the courses run on from the overlay into the full tiles beside it. No pictures.

**Changes in round 5** (for the engine): island sand and desert sand move from B (64 tiles by ripple phases) to A; B is gone. The picture placement of A is new (steps 2-4 above: density noise, offsets 0 / 1 / 2, no two side-by-side blocks with the same picture). Keys removed (all new in v2; every v1 key stays): `tile.sand.16-63`, `desert.sand.16-63`. Keys added: `tile.sand.macro*.0-3`, `desert.sand.macro*.0-3` (8 pictures each).

Round 4: A replaced the round-3 edge types of the grass-likes, moss and path and took in mountain snow and the 4 winter sets (removed then: `*.macro3.4-8`, `mountains.snow.16-63`, `winter.<4 grounds>.16-63`).
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
- `desert.sand.*` — 13
- `desert.sand.edge.*` — 28
- `desert.sand.macro.*` — 4
- `desert.sand.macro2.*` — 4
- `desert.sand.macro3.*` — 4
- `desert.sand.macro4.*` — 4
- `desert.sand.macro5.*` — 4
- `desert.sand.macro6.*` — 4
- `desert.sand.macro7.*` — 4
- `desert.sand.macro8.*` — 4
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
- `tile.sand.*` — 15
- `tile.sand.edge.*` — 28
- `tile.sand.macro.*` — 4
- `tile.sand.macro2.*` — 4
- `tile.sand.macro3.*` — 4
- `tile.sand.macro4.*` — 4
- `tile.sand.macro5.*` — 4
- `tile.sand.macro6.*` — 4
- `tile.sand.macro7.*` — 4
- `tile.sand.macro8.*` — 4
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
