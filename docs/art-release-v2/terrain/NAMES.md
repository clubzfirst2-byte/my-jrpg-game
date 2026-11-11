# Ground v2 — key scheme (for wiring)

Folder `src/art-release-v2/terrain/`: **3940 PNGs** = 189 v1 keys redrawn + 3565 new keys + 186 v1 keys copied unchanged (not redrawn: ruin / wall faces, v1.1 shores, trees, rocks, floors…). The group **contains every key of the v1 terrain group**, so it can replace it as a whole (`manifest.json` lists the three groups; the test checks v2 ⊇ v1). All new / redrawn ground tiles are 32×32 art px (= one 16 px map cell), anchor **top-left**, alpha 0 / 255. Generator: `tools/terrain_v2/gen_v2.py`; `tools/terrain_v2/render_ref.py` is a reference renderer of everything below (the review images use it).

## 1. Grounds

| ground | prefix (= the v1 key) | tiles | picked by | macro pieces | seasons |
|---|---|---|---|---|---|
| island grass | `tile.grass` | `tile.grass.0` – `.31` | A: steps 1-6 below | `.macro.0-3`, `.macro2.0-3` … `.macro8.0-3` | autumn (32 calm tiles + 8 pictures), winter (32 calm snow tiles + 8 pictures, with the plant's tips) |
| plains grass | `plains.grass` | `plains.grass.0` – `.31` | A: steps 1-6 below | `.macro.0-3`, `.macro2.0-3` … `.macro8.0-3` | autumn (32 calm tiles + 8 pictures), winter (32 calm snow tiles + 8 pictures, with the plant's tips) |
| lake shore grass | `lake.grass` | `lake.grass.0` – `.31` | A: steps 1-6 below | `.macro.0-3`, `.macro2.0-3` … `.macro8.0-3` | autumn (32 calm tiles + 8 pictures), winter (32 calm snow tiles + 8 pictures, with the plant's tips) |
| forest floor (moss) | `forest.grass` | `forest.grass.0` – `.31` | A: steps 1-6 below | `.macro.0-3`, `.macro2.0-3` … `.macro8.0-3` | autumn (32 calm tiles + 8 pictures), winter (32 calm snow tiles + 8 pictures, with the plant's tips) |
| mountain snow | `mountains.snow` | `mountains.snow.0` – `.31` | A: steps 1-6 below | `.macro.0-3`, `.macro2.0-3` … `.macro8.0-3` | — |
| island sand | `tile.sand` | `tile.sand`, `tile.sand.1` – `.31` | A: steps 1-6 below | `.macro.0-3`, `.macro2.0-3` … `.macro8.0-3` | — |
| desert sand | `desert.sand` | `desert.sand.0` – `.31` | A: steps 1-6 below | `.macro.0-3`, `.macro2.0-3` … `.macro8.0-3` | — |
| path | `tile.path` | `tile.path`, `tile.path.1` – `.31` | A: steps 1-6 below | `.macro.0-3`, `.macro2.0-3` … `.macro8.0-3` | — |
| ruin floor | `tile.ruin` | `tile.ruin`, `tile.ruin.1` – `.65` | C: row phase + column symbols | — | — |

`hash(i, j)` = gameView's hash (render_ref.dhash). For tile.sand / tile.path / tile.ruin, n = 0 is the bare v1 key. `render_ref.py` does all of this.

**A. Every ground except the ruin floor (round 5; 32 calm tiles in a light and a dark group + 8 pictures of 2×2 tiles):** island / plains / lake grass, moss, path, mountain snow, island sand, desert sand, and the autumn / winter sets of the 4 seasonal grounds. Integer `hash` values are unsigned 32-bit; `/` below is a float division.

1. **Blocks.** Cut the display grid (section 2) into blocks of 3×3 display tiles; block `(a, b)` covers display tiles `3a … 3a+2`, `3b … 3b+2`. Every block (a, b ≥ 0, and one block past the map's right / bottom edge) is looked at; `h = hash(a, b)`.
2. **Is there a picture?** Density noise over the blocks, a value noise on a lattice of 4 blocks: `v(x, y) = (hash(x + 5003, y + 7919) % 1024) / 1023`; `gx = floor(a / 4)`, `gy = floor(b / 4)`, `fx = (a % 4 + 0.5) / 4`, `fy = (b % 4 + 0.5) / 4`, `sx = fx·fx·(3 − 2·fx)`, `sy = fy·fy·(3 − 2·fy)`; `top = v(gx, gy) + (v(gx+1, gy) − v(gx, gy))·sx`, `bot = v(gx, gy+1) + (v(gx+1, gy+1) − v(gx, gy+1))·sx`, `n = top + (bot − top)·sy`. `pNone = min(1, max(0, 2·(n − 0.3)))`. The block has a picture when `((h >> 16) % 1024) / 1024 >= pNone` (thick where n < 0.3, bare where n > 0.8: clusters and open stretches).
3. **Where in the block.** `OFF = [0, 0, 1, 2, 2, 2]`; raw offsets `rx(a, b) = OFF[hash(a, b) % 6]`, `ry(a, b) = OFF[(hash(a, b) >> 8) % 6]`. Then, in this order: `ox = rx(a, b)`, `oy = ry(a, b)`; if `ox == 2` and `rx(a+1, b) == 0`: `ox = 1`; if `oy == 2` and `ry(a, b+1) == 0`: `oy = 1`; if `ox == 2` and `oy == 2` and `rx(a+1, b+1) == 0` and `ry(a+1, b+1) == 0`: `oy = 1`; if `ox == 2` and `oy == 0` and `rx(a+1, b−1) == 0` and `ry(a+1, b−1) == 2`: `ox = 1`. The picture's NW display tile is `(i0, j0) = (3a + ox, 3b + oy)`; with offset 2 it reaches one tile into the next block. These rules keep pictures from overlapping (they can touch along an edge), and the chances (1/3, 1/6, 1/2) make every column and row of a block equally often covered (no 96-px period).
4. **Which picture** (round 6: no block shares its picture with any of its 8 neighbours where it can be helped): raw number `r(a, b) = hash(a + 409, b + 1031) % 8`, `k(a, b) = floor(hash(a + 409, b + 1031) / 8)`. The blocks are taken in 4 classes by `(a % 2, b % 2)`, each class using the final numbers `m` of earlier classes: **A** `(0, 0)`: `m = r(a, b)`. **B** `(1, 0)`: avoid `m(a−1, b)`, `m(a+1, b)`. **C** `(0, 1)`: avoid `m(a, b−1)`, `m(a, b+1)`, `m(a−1, b−1)`, `m(a+1, b−1)`, `m(a−1, b+1)`, `m(a+1, b+1)`. **D** `(1, 1)`: avoid all 8 neighbours `m(a±1, b)`, `m(a, b±1)`, `m(a±1, b±1)`; if that leaves no number, avoid only the 4 side neighbours. `free` = the numbers 0-7 not avoided, in increasing order; `m = free[k(a, b) % len(free)]`. Name: `macro` for m = 0, else `macro<m+1>` (`macro2` … `macro8`).
4b. **Desert dunes** (round 8): cut the blocks into cells of 4×3 blocks, `sa = floor(a / 4)`, `sb = floor(b / 3)`, `hs = hash(sa + 77, sb + 31)`. The cell's one dune block is `(4·sa + hs % 4, 3·sb + (hs >> 2) % 3)`. If block (a, b) is it and its 9 map cells (step 5) are all desert sand, it shows `desert.sand.dune<k>.<q>` with `k = 1 + (sa % 3 + 3·(sb % 2) + hash(floor(sa / 3) + 13, floor(sb / 2) + 29)) % 6`, at the offsets of step 3, whether or not step 2 gave it a picture and instead of the picture of step 4. One dune per 12 blocks (about 4-5 on a screen). Inside a group of 3×2 cells (12×6 blocks: the same `floor(sa / 3)`, `floor(sb / 2)`) the 6 dunes all have different shapes. The hash term changes from group to group, so across a group border two dunes of the same shape can come close (measured: about 1 dune in 8 has one of its own shape within 8 tiles; side by side about 1 in 80).
5. **Draw it** only when it stays on the map (`i0 + 2`, `j0 + 2` inside) and the 9 map cells under its 4 display tiles (cells `i0 … i0+2`, `j0 … j0+2`) are all one ground of this scheme **and one height** (round 8: a picture never straddles a step): `<prefix>.<name>.<q>`, q = 0 NW `(i0, j0)`, 1 NE, 2 SW, 3 SE.
6. **Every other display tile** whose lowest ground is of this scheme gets a calm tile `<prefix>.<c>`, c = 0-31 (round 6): 0-15 the light group (more lit grain, small lit patches), 16-31 the dark group. **Group:** `n2 = ` the value noise of step 2 over display tiles with a lattice of 6 tiles and the lattice values `(hash(x + 12011, y + 3407) % 1024) / 1023` (`gx = floor(i / 6)`, `fx = (i % 6 + 0.5) / 6`, the same for j; smoothstep blend as in step 2); `q = min(1, max(0, 0.8·(n2 − 0.5) + 0.5))`; group `g = 1` when `(hash(i + 71, j + 113) % 1024) / 1024 < q`, else 0. **Raw number** `c0(i, j) = 16·g(i, j) + hash(i + 3, j + 11) % 16`. **Number** (no calm tile shares its number with any of its 8 neighbours): the display tiles in 4 classes by `(i % 2, j % 2)` exactly as the blocks in step 4: **A** `(0, 0)`: `c = c0`. **B** `(1, 0)`: avoid `c(i±1, j)`. **C** `(0, 1)`: avoid `c(i, j±1)` and `c(i±1, j±1)`. **D** `(1, 1)`: avoid all 8 neighbours. `free` = the 16 numbers of the tile's own group `16·g … 16·g + 15` not avoided, in increasing order; `c = free[(hash(i + 3, j + 11) >> 4) % len(free)]`. The neighbours' numbers are computed by this rule whatever is drawn there (a picture, another ground). Any calm tile joins any other and any picture (nothing crosses their edges).

In winter the 4 seasonal grounds use the same rule with their `winter.` keys (snow with the tips of the ground's own plant), in autumn with their `autumn.` keys. The pictures carry the large things (grass: thickets, lit patches, flower clusters / reeds, island clover carpets in white bloom - 2 of the 8 pictures wide ones; moss beds, worn stretches; snow: blue hollows, drift swells, wind ridges, glints, capped stones; sand: ripple fields, dune swells, pale smooth stretches, pebble clusters, shells / dry grass), the calm tiles a grain and the small things. Each kind's positions are spread evenly over x and y (in the pictures: one per 2 or 4 px modulo 32), and the mean row / column brightness of the 16 calm tiles and of the 32 picture quarters is evened out with grain specks, so no 32- / 64-px pattern on average.

**C. Ruin floor (66 tiles; round 3):** rectangular stones in straight courses 11 art px high that run across the whole map, their joints staggered course by course.
- row phase `R = (32·j) mod 11` = `(10·j) mod 11` (0-10), the same for a whole row of display tiles (j ≥ 0)
- column symbol `s(i)` (0-2) of the vertical line of edges at the west of column i (i ≥ 0), never the same on two neighbouring lines: `k = floor(i / 2)`, `e0 = hash(k, 7) % 3`, `e1 = hash(k + 1, 7) % 3`; `s = e0` when i is even; when i is odd, `s = 3 − e0 − e1` if `e0 ≠ e1`, else `(e0 + 1 + hash(k, 11) % 2) % 3`
- `W = s(i)`, `E = s(i + 1)`, `n = 6·R + 2·W + (E if E < W else E − 1)`
- the ruin's overlay over water is `tile.ruin.edge.<mask>.<R>` (R = 0-10, the same row phase), so the courses run on from the overlay into the full tiles beside it. No pictures.

**Changes in round 10** (for the engine): new step pieces `<prefix>.step2.<mask>.<code>` and `<prefix>.step2.inner.<ne|nw>.<s>` with their rule (section 2c): use them instead of 2b's rims, inner corners and east shadow, and one tint for every level. No key removed; 2b's keys stay.

**Changes in round 8** (for the engine): transition overlays never hold a detached island or a hole (16 sets × `edge.1.0`, `2.0`, `4.3`, `7.0-3` and the foam redrawn); masks 6 / 9 use the same shared wobble as the others; dunes by step 4b (new formula); pictures only on one height (step 5); inner step corners `<prefix>.step.inner.<ne|nw>` (2b). No key removed.

**Changes in round 7** (for the engine): transition overlays have 4 variants per mask (masks 6 / 9: 2) chosen by side states (section 2, step 3); new step rims / shadows (section 2b); the desert's dunes are their own pictures `desert.sand.dune1-6.0-3` (step 4b; the 8 desert pictures no longer hold dunes). No key removed.

**Changes in round 6** (for the engine): 32 calm tiles instead of 16 (`.16-.31` added for every ground and season set of A; island grass, plains, lake, moss, path, snow, sand, desert, and the autumn / winter sets), chosen by step 6 (light / dark groups by a noise; no calm tile equal to any of its 8 neighbours); the picture number of step 4 now avoids the diagonal neighbours too. Island grass: 2 of the 8 pictures (`.macro`, `.macro5`) carry a wide clover carpet; desert: 3 (`.macro2`, `.macro5`, `.macro7`) a big dune ridge.

**Changes in round 5** (for the engine): island sand and desert sand move from B (64 tiles by ripple phases) to A; B is gone. The picture placement of A is new (steps 2-4 above: density noise, offsets 0 / 1 / 2, no two side-by-side blocks with the same picture). Keys removed (all new in v2; every v1 key stays): `tile.sand.16-63`, `desert.sand.16-63`. Keys added: `tile.sand.macro*.0-3`, `desert.sand.macro*.0-3` (8 pictures each).

Round 4: A replaced the round-3 edge types of the grass-likes, moss and path and took in mountain snow and the 4 winter sets (removed then: `*.macro3.4-8`, `mountains.snow.16-63`, `winter.<4 grounds>.16-63`).
- **Seasons:** `autumn.<key>` / `winter.<key>` for every key of the 4 seasonal grounds (the existing season-key scheme). `autumn.mountains.snow.*` stays the v1.1 art (copied).
- Measured (`check.txt`): the repeat measure of the first inspection (mean |ΔL| at 32 px ÷ at 24 px) and the banding measure (autocorrelation of the row means and of the column means at 32 px and at 64 px), 80×48 fields.

## 2. Transitions — dual grid, 4 corners, layered overlays

**Scheme.** Draw the ground on a grid shifted by half a cell (+8, +8 game px). Display tile `(i, j)` covers the centres of 4 map cells: **NW = (i, j), NE = (i+1, j), SW = (i, j+1), SE = (i+1, j+1)**, and is drawn at game px `(i*16 + 8, j*16 + 8)`. Each corner has the terrain of its cell.

1. Draw the full ground tile (section 1) of the **lowest-priority** terrain among the 4 corners.
2. For each **higher** terrain present, low to high, draw `<prefix>.edge.<mask>.<v>` with **mask = sum of the corners whose terrain priority is >= this terrain's: NW 1, NE 2, SW 4, SE 8** (1-14). If a higher terrain has all 4 corners, draw its base tile instead.
3. `<v>` (round 7): masks 6 and 9 (the border crosses all 4 sides): `v = hash(i + 7, j) % 2` (as before). Every other mask: `v = sA + 2·sB` (0-3), where A and B are the two sides of the display tile that the border crosses, in the order N, E, S, W (a side is crossed when its two corners differ in the mask: N = NW≠NE, E = NE≠SE, S = SW≠SE, W = NW≠SW), and `s` is that side's **state**: the side's edge hash is `hash(2i+1, 2j)` (N), `hash(2i+2, 2j+1)` (E), `hash(2i+1, 2j+2)` (S), `hash(2i, 2j+1)` (W); `s = (edgeHash >> 4) & 1`, except **s = 0** when one of the side's two end cells is water (N: cells (i, j), (i+1, j); E: (i+1, j), (i+1, j+1); S: (i, j+1), (i+1, j+1); W: (i, j), (i, j+1)), or when the display tile across that side (N: (i, j−1), E: (i+1, j), S: (i, j+1), W: (i−1, j)) has mask 6 or 9 for the same terrain. The tiles on both sides of a side compute the same state, so the border joins; with state 1 it crosses about 3 px away from state 0, so a straight path's edge no longer repeats tile by tile. The ruin floor: `<v>` = its row phase R, 0-10 (section 1 C), unchanged. Round 7 also made every variant's border swing 4+ px inside the tile (mask 5 was almost straight); the keys `.0` / `.1` stay, `.2` / `.3` are new.

**Priority**, low → high: water (section 3) < `tile.ruin` < `tile.path` < `desert.sand` < `tile.sand` < `mountains.snow` < `forest.grass` < `lake.grass` < `plains.grass` < `tile.grass`.
Grass-like edges lie over path / sand / ruin, sand drifts over path and ruin, snow over path and ruin, every land over water. One set of 14 masks × 2 variants (ruin: × 11 row phases) per terrain covers every pair it can meet (world map cell edges: lake|sand 1720, grass|ruin 884, moss|path 880, plains|path 780, grass|sand 672, dsand|grass 427, ruin|snow 396, grass|path 369, path|snow 287, lake|path 214, …).

Seasons: `autumn.<prefix>.edge.<mask>.<v>` / `winter.<prefix>.edge.<mask>.<v>` for the 4 seasonal grounds (winter edges are snow edges). The priority does not change.

Notes:
- The border follows the map cells' edges (± a few px of drawn wobble): collision does not change, a 1-cell path stays 1 cell wide.
- **Height:** blend only corners of the same height; where they differ, draw each cell's own tile as today and let the cliff faces separate them. (The review images are flat.)
- Grounds without v2 art (wood, wall top, metal, pit, dark) stay on the cell grid (their v1 keys, copied).

## 2b. One-level steps (round 7, new; replaces the 1-px outline)

For an elevated cell (gameView: its surface square on the cell grid at `(tx·16, ty·16 − h)`), where v1 draws a 1-px dark line on the east / west / north side when that neighbour is lower (`lowerEast`, `lowerWest`, `lowerNorth`) and a translucent shadow strip on the lower ground east of it:
- **Rim:** draw `<prefix>.step.<mask>.<v>` over the cell's surface, same position and size (32×32 art px = one cell), instead of the lines. `<prefix>` = the cell's ground prefix (section 1; with the season prefix in autumn / winter for the 4 seasonal grounds); `mask = 1·lowerNorth + 2·lowerEast + 4·lowerWest` (1-7); `v = hash(tx + 5, ty + 9) % 2`. It holds a dark outline 0-3 px deep that swells, thins and breaks off along the side, a lit rim inside it on the north and west sides (they face the light) and a shaded rim on the east side. The south side keeps its cliff face (section 4).
- **Shadow:** on the lower cell east of it (`tx + 1`), instead of the translucent strip, draw `<prefix>.step.shade.<v>` with the LOWER cell's prefix at that cell's position on its own ground (`((tx+1)·16, ty·16 − h_east)`), `v = hash(tx + 6, ty + 9) % 2`: a shadow from its west side, 2-8 px wide (4-9 px on moss, autumn moss, path and ruin, whose shadow tone is lighter) with a wavy edge.
- **Inner corners** (round 8): on a high cell whose north and east neighbours are not lower but whose NE neighbour is lower, also draw `<prefix>.step.inner.ne` over its surface; north and west not lower, NW lower: `<prefix>.step.inner.nw`. They join the end of the north rim of the side neighbour and the end of the east / west rim of the north neighbour (no gap at the corner).
- **Strength** (round 8): the outline is the ground's lightest tone at least 28 (0-255) darker than its core, and never lighter than tone 1; the shadow and the shaded east rim the lightest at least 15 darker (grass, plains, lake: tones 0 / 1; moss 0 / 1; island sand 1 / 1; desert, path, ruin 1 / 2; snow 1 / 2; autumn grass 1 / 2, lake 1 / 1, moss 0 / 1).
- **Order and opacity:** the rim right after the cell's surface, before the next row's surfaces. The shadow after all the surfaces of its row (else a slightly lower east cell's surface would hide it), opaque, as drawn (it covers the small marks of the lower cell's ground under it; if the engine prefers it see-through, draw it at alpha 0.6 — its tone was chosen for full strength). No shadow when the lower east cell is water or a ground with no v2 art; a cliff face (south side) keeps its own contact shadow.
- Along a straight step the outline, rim and shadow depths are 32-periodic in the position along the side, so they join from cell to cell (variant 1 adds a bump that is 0 at the cell's corners). Keys exist for every ground of section 1 and every season set (`tile.ruin.step.*` too).

## 2c. Steps off the cell edges (round 10, new; use instead of 2b's rims, shadow and inner corners)

The step line of 2b runs on the cell's edge, so terraces read as a staircase of cell edges. The step2 pieces draw it INSIDE the high cell at a depth that changes from cell corner to cell corner. Collision and heights do not change: only the drawing.
- **Corner state:** every cell corner (vertex) `(vx, vy)` (the NW corner of cell (tx, ty) is (tx, ty), its NE (tx+1, ty), SE (tx+1, ty+1), SW (tx, ty+1)) has `s = (hash(vx + 211, vy + 97) >> 3) & 1`. The rim line's depth there is 3 px (s = 0) or 9 px (s = 1) on the north and west sides, 6 / 12 px on the east side, blended along the side with a small wave that is 0 at the corners. Two cells that share a corner agree on it, so a terrace's rim is continuous and wanders by about 6 px instead of following the cell edges.
- **Rim:** on a raised cell, where 2b would draw `step.<mask>.<v>`, draw `<prefix>.step2.<mask>.<code>` (same position, after the surface; mask as in 2b: lower north 1, east 2, west 4). The corners of the lowered sides — N: NW, NE; E: NE, SE; W: NW, SW — taken together and in the order NW, NE, SE, SW; `code = Σ s(k-th of them)·2^k` (mask 1, 2, 4: codes 0-3; 3, 5: 0-7; 6, 7: 0-15). It holds the dark outline, the lit rim (north, west) or shaded rim (east), rounded outer corners (6 px), and on the east side a 2.5-4.5 px wavy shadow outside the rim that stops short of the cell's edge. Between the rim and the cell's edge the cell's own surface shows (it reads as the lower ground).
- **Inner corners:** where 2b draws `step.inner.<ne|nw>` (north and east / west not lower, NE / NW lower), draw `<prefix>.step2.inner.<ne|nw>.<s>`, s = the state of that corner (NE: (tx+1, ty), NW: (tx, ty)).
- **Shadow (R2):** the east shadow is part of the rim piece, on the high cell itself, so it shows wherever the step's east side shows (2b's `step.shade` on the lower east cell was hidden behind a higher cell to the south on diagonal terraces). With step2, do NOT draw `step.shade` on the east cell.
- **Tint:** with step2, draw every raised surface with the level-0 tint (gameView.levelTint: the same brightness for every level with the v2 ground). Otherwise the 5 % brighter raised surface shows the cell's straight edge outside the moved rim.
- The south side keeps its cliff face (section 4) and its contact shadow.
- `tools/terrain_v2/render_steps.py` draws all of this from the world map (review images `steps_*`).

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

- `autumn.forest.grass.*` — 28
- `autumn.forest.grass.edge.*` — 52
- `autumn.forest.grass.macro.*` — 4
- `autumn.forest.grass.macro2.*` — 4
- `autumn.forest.grass.macro3.*` — 4
- `autumn.forest.grass.macro4.*` — 4
- `autumn.forest.grass.macro5.*` — 4
- `autumn.forest.grass.macro6.*` — 4
- `autumn.forest.grass.macro7.*` — 4
- `autumn.forest.grass.macro8.*` — 4
- `autumn.forest.grass.step.*` — 18
- `autumn.forest.grass.step2.*` — 64
- `autumn.lake.grass.*` — 28
- `autumn.lake.grass.edge.*` — 52
- `autumn.lake.grass.macro.*` — 4
- `autumn.lake.grass.macro2.*` — 4
- `autumn.lake.grass.macro3.*` — 4
- `autumn.lake.grass.macro4.*` — 4
- `autumn.lake.grass.macro5.*` — 4
- `autumn.lake.grass.macro6.*` — 4
- `autumn.lake.grass.macro7.*` — 4
- `autumn.lake.grass.macro8.*` — 4
- `autumn.lake.grass.step.*` — 18
- `autumn.lake.grass.step2.*` — 64
- `autumn.plains.grass.*` — 28
- `autumn.plains.grass.edge.*` — 52
- `autumn.plains.grass.macro.*` — 4
- `autumn.plains.grass.macro2.*` — 4
- `autumn.plains.grass.macro3.*` — 4
- `autumn.plains.grass.macro4.*` — 4
- `autumn.plains.grass.macro5.*` — 4
- `autumn.plains.grass.macro6.*` — 4
- `autumn.plains.grass.macro7.*` — 4
- `autumn.plains.grass.macro8.*` — 4
- `autumn.plains.grass.step.*` — 18
- `autumn.plains.grass.step2.*` — 64
- `autumn.tile.grass.*` — 29
- `autumn.tile.grass.edge.*` — 52
- `autumn.tile.grass.macro.*` — 4
- `autumn.tile.grass.macro2.*` — 4
- `autumn.tile.grass.macro3.*` — 4
- `autumn.tile.grass.macro4.*` — 4
- `autumn.tile.grass.macro5.*` — 4
- `autumn.tile.grass.macro6.*` — 4
- `autumn.tile.grass.macro7.*` — 4
- `autumn.tile.grass.macro8.*` — 4
- `autumn.tile.grass.step.*` — 18
- `autumn.tile.grass.step2.*` — 64
- `desert.sand.*` — 29
- `desert.sand.dune1.*` — 4
- `desert.sand.dune2.*` — 4
- `desert.sand.dune3.*` — 4
- `desert.sand.dune4.*` — 4
- `desert.sand.dune5.*` — 4
- `desert.sand.dune6.*` — 4
- `desert.sand.edge.*` — 52
- `desert.sand.macro.*` — 4
- `desert.sand.macro2.*` — 4
- `desert.sand.macro3.*` — 4
- `desert.sand.macro4.*` — 4
- `desert.sand.macro5.*` — 4
- `desert.sand.macro6.*` — 4
- `desert.sand.macro7.*` — 4
- `desert.sand.macro8.*` — 4
- `desert.sand.step.*` — 18
- `desert.sand.step2.*` — 64
- `forest.grass.*` — 28
- `forest.grass.edge.*` — 52
- `forest.grass.macro.*` — 4
- `forest.grass.macro2.*` — 4
- `forest.grass.macro3.*` — 4
- `forest.grass.macro4.*` — 4
- `forest.grass.macro5.*` — 4
- `forest.grass.macro6.*` — 4
- `forest.grass.macro7.*` — 4
- `forest.grass.macro8.*` — 4
- `forest.grass.step.*` — 18
- `forest.grass.step2.*` — 64
- `lake.grass.*` — 28
- `lake.grass.edge.*` — 52
- `lake.grass.macro.*` — 4
- `lake.grass.macro2.*` — 4
- `lake.grass.macro3.*` — 4
- `lake.grass.macro4.*` — 4
- `lake.grass.macro5.*` — 4
- `lake.grass.macro6.*` — 4
- `lake.grass.macro7.*` — 4
- `lake.grass.macro8.*` — 4
- `lake.grass.step.*` — 18
- `lake.grass.step2.*` — 64
- `mountains.snow.*` — 28
- `mountains.snow.edge.*` — 52
- `mountains.snow.macro.*` — 4
- `mountains.snow.macro2.*` — 4
- `mountains.snow.macro3.*` — 4
- `mountains.snow.macro4.*` — 4
- `mountains.snow.macro5.*` — 4
- `mountains.snow.macro6.*` — 4
- `mountains.snow.macro7.*` — 4
- `mountains.snow.macro8.*` — 4
- `mountains.snow.step.*` — 18
- `mountains.snow.step2.*` — 64
- `plains.grass.*` — 28
- `plains.grass.edge.*` — 52
- `plains.grass.macro.*` — 4
- `plains.grass.macro2.*` — 4
- `plains.grass.macro3.*` — 4
- `plains.grass.macro4.*` — 4
- `plains.grass.macro5.*` — 4
- `plains.grass.macro6.*` — 4
- `plains.grass.macro7.*` — 4
- `plains.grass.macro8.*` — 4
- `plains.grass.step.*` — 18
- `plains.grass.step2.*` — 64
- `tile.grass.*` — 29
- `tile.grass.edge.*` — 52
- `tile.grass.macro.*` — 4
- `tile.grass.macro2.*` — 4
- `tile.grass.macro3.*` — 4
- `tile.grass.macro4.*` — 4
- `tile.grass.macro5.*` — 4
- `tile.grass.macro6.*` — 4
- `tile.grass.macro7.*` — 4
- `tile.grass.macro8.*` — 4
- `tile.grass.step.*` — 18
- `tile.grass.step2.*` — 64
- `tile.path.*` — 31
- `tile.path.edge.*` — 52
- `tile.path.macro.*` — 4
- `tile.path.macro2.*` — 4
- `tile.path.macro3.*` — 4
- `tile.path.macro4.*` — 4
- `tile.path.macro5.*` — 4
- `tile.path.macro6.*` — 4
- `tile.path.macro7.*` — 4
- `tile.path.macro8.*` — 4
- `tile.path.step.*` — 18
- `tile.path.step2.*` — 64
- `tile.ruin.*` — 65
- `tile.ruin.edge.*` — 154
- `tile.ruin.step.*` — 18
- `tile.ruin.step2.*` — 64
- `tile.sand.*` — 31
- `tile.sand.edge.*` — 52
- `tile.sand.macro.*` — 4
- `tile.sand.macro2.*` — 4
- `tile.sand.macro3.*` — 4
- `tile.sand.macro4.*` — 4
- `tile.sand.macro5.*` — 4
- `tile.sand.macro6.*` — 4
- `tile.sand.macro7.*` — 4
- `tile.sand.macro8.*` — 4
- `tile.sand.step.*` — 18
- `tile.sand.step2.*` — 64
- `tile.water.*` — 2
- `tile.water.deep.*` — 4
- `tile.water.deep.edge.*` — 56
- `tile.water.deep.v1.*` — 4
- `tile.water.foam.*` — 56
- `tile.water.v1.*` — 4
- `winter.forest.grass.*` — 28
- `winter.forest.grass.edge.*` — 52
- `winter.forest.grass.macro.*` — 4
- `winter.forest.grass.macro2.*` — 4
- `winter.forest.grass.macro3.*` — 4
- `winter.forest.grass.macro4.*` — 4
- `winter.forest.grass.macro5.*` — 4
- `winter.forest.grass.macro6.*` — 4
- `winter.forest.grass.macro7.*` — 4
- `winter.forest.grass.macro8.*` — 4
- `winter.forest.grass.step.*` — 18
- `winter.forest.grass.step2.*` — 64
- `winter.lake.grass.*` — 28
- `winter.lake.grass.edge.*` — 52
- `winter.lake.grass.macro.*` — 4
- `winter.lake.grass.macro2.*` — 4
- `winter.lake.grass.macro3.*` — 4
- `winter.lake.grass.macro4.*` — 4
- `winter.lake.grass.macro5.*` — 4
- `winter.lake.grass.macro6.*` — 4
- `winter.lake.grass.macro7.*` — 4
- `winter.lake.grass.macro8.*` — 4
- `winter.lake.grass.step.*` — 18
- `winter.lake.grass.step2.*` — 64
- `winter.plains.grass.*` — 28
- `winter.plains.grass.edge.*` — 52
- `winter.plains.grass.macro.*` — 4
- `winter.plains.grass.macro2.*` — 4
- `winter.plains.grass.macro3.*` — 4
- `winter.plains.grass.macro4.*` — 4
- `winter.plains.grass.macro5.*` — 4
- `winter.plains.grass.macro6.*` — 4
- `winter.plains.grass.macro7.*` — 4
- `winter.plains.grass.macro8.*` — 4
- `winter.plains.grass.step.*` — 18
- `winter.plains.grass.step2.*` — 64
- `winter.tile.grass.*` — 29
- `winter.tile.grass.edge.*` — 52
- `winter.tile.grass.macro.*` — 4
- `winter.tile.grass.macro2.*` — 4
- `winter.tile.grass.macro3.*` — 4
- `winter.tile.grass.macro4.*` — 4
- `winter.tile.grass.macro5.*` — 4
- `winter.tile.grass.macro6.*` — 4
- `winter.tile.grass.macro7.*` — 4
- `winter.tile.grass.macro8.*` — 4
- `winter.tile.grass.step.*` — 18
- `winter.tile.grass.step2.*` — 64

Redrawn v1 keys: `autumn.face.earth.top-base.4`, `autumn.face.earth.top-base.4.v1`, `autumn.face.earth.top-base.4.v2`, `autumn.face.earth.top-base.8`, `autumn.face.earth.top-base.8.v1`, `autumn.face.earth.top-base.8.v2`, `autumn.face.earth.top.4`, `autumn.face.earth.top.4.v1`, `autumn.face.earth.top.4.v2`, `autumn.face.earth.top.8`, `autumn.face.earth.top.8.v1`, `autumn.face.earth.top.8.v2`, `autumn.face.stone.top-base.4`, `autumn.face.stone.top-base.4.v1`, `autumn.face.stone.top-base.4.v2`, `autumn.face.stone.top-base.8`, `autumn.face.stone.top-base.8.v1`, `autumn.face.stone.top-base.8.v2`, `autumn.face.stone.top.4`, `autumn.face.stone.top.4.v1`, `autumn.face.stone.top.4.v2`, `autumn.face.stone.top.8`, `autumn.face.stone.top.8.v1`, `autumn.face.stone.top.8.v2`, `autumn.forest.grass.0`, `autumn.forest.grass.1`, `autumn.forest.grass.2`, `autumn.forest.grass.3`, `autumn.lake.grass.0`, `autumn.lake.grass.1`, `autumn.lake.grass.2`, `autumn.lake.grass.3`, `autumn.plains.grass.0`, `autumn.plains.grass.1`, `autumn.plains.grass.2`, `autumn.plains.grass.3`, `autumn.tile.grass.0`, `autumn.tile.grass.1`, `autumn.tile.grass.2`, `desert.sand.0`, `desert.sand.1`, `desert.sand.2`, `face.desert.mid-base.4`, `face.desert.mid-base.4.v1`, `face.desert.mid-base.8`, `face.desert.mid-base.8.v1`, `face.desert.mid.4`, `face.desert.mid.4.v1`, `face.desert.mid.8`, `face.desert.mid.8.v1`, `face.desert.top-base.4`, `face.desert.top-base.4.v1`, `face.desert.top-base.8`, `face.desert.top-base.8.v1`, `face.desert.top.4`, `face.desert.top.4.v1`, `face.desert.top.8`, `face.desert.top.8.v1`, `face.earth.mid-base.4`, `face.earth.mid-base.4.v1`, `face.earth.mid-base.4.v2`, `face.earth.mid-base.8`, `face.earth.mid-base.8.v1`, `face.earth.mid-base.8.v2`, `face.earth.mid.4`, `face.earth.mid.4.v1`, `face.earth.mid.4.v2`, `face.earth.mid.8`, `face.earth.mid.8.v1`, `face.earth.mid.8.v2`, `face.earth.top-base.4`, `face.earth.top-base.4.v1`, `face.earth.top-base.4.v2`, `face.earth.top-base.8`, `face.earth.top-base.8.v1`, `face.earth.top-base.8.v2`, `face.earth.top.4`, `face.earth.top.4.v1`, `face.earth.top.4.v2`, `face.earth.top.8`, `face.earth.top.8.v1`, `face.earth.top.8.v2`, `face.path.mid-base.4`, `face.path.mid-base.4.v1`, `face.path.mid-base.8`, `face.path.mid-base.8.v1`, `face.path.mid.4`, `face.path.mid.4.v1`, `face.path.mid.8`, `face.path.mid.8.v1`, `face.path.top-base.4`, `face.path.top-base.4.v1`, `face.path.top-base.8`, `face.path.top-base.8.v1`, `face.path.top.4`, `face.path.top.4.v1`, `face.path.top.8`, `face.path.top.8.v1`, `face.sand.mid-base.4`, `face.sand.mid-base.4.v1`, `face.sand.mid-base.8`, `face.sand.mid-base.8.v1`, `face.sand.mid.4`, `face.sand.mid.4.v1`, `face.sand.mid.8`, `face.sand.mid.8.v1`, `face.sand.top-base.4`, `face.sand.top-base.4.v1`, `face.sand.top-base.8`, `face.sand.top-base.8.v1`, `face.sand.top.4`, `face.sand.top.4.v1`, `face.sand.top.8`, `face.sand.top.8.v1`, `face.stone.mid-base.4`, `face.stone.mid-base.4.v1`, `face.stone.mid-base.4.v2`, `face.stone.mid-base.8`, `face.stone.mid-base.8.v1`, `face.stone.mid-base.8.v2`, `face.stone.mid.4`, `face.stone.mid.4.v1`, `face.stone.mid.4.v2`, `face.stone.mid.8`, `face.stone.mid.8.v1`, `face.stone.mid.8.v2`, `face.stone.top-base.4`, `face.stone.top-base.4.v1`, `face.stone.top-base.4.v2`, `face.stone.top-base.8`, `face.stone.top-base.8.v1`, `face.stone.top-base.8.v2`, `face.stone.top.4`, `face.stone.top.4.v1`, `face.stone.top.4.v2`, `face.stone.top.8`, `face.stone.top.8.v1`, `face.stone.top.8.v2`, `forest.grass.0`, `forest.grass.1`, `forest.grass.2`, `forest.grass.3`, `lake.grass.0`, `lake.grass.1`, `lake.grass.2`, `lake.grass.3`, `mountains.snow.0`, `mountains.snow.1`, `mountains.snow.2`, `mountains.snow.3`, `plains.grass.0`, `plains.grass.1`, `plains.grass.2`, `plains.grass.3`, `tile.grass.0`, `tile.grass.1`, `tile.grass.2`, `tile.path`, `tile.ruin`, `tile.sand`, `tile.water.0`, `tile.water.1`, `winter.face.earth.top-base.4`, `winter.face.earth.top-base.4.v1`, `winter.face.earth.top-base.4.v2`, `winter.face.earth.top-base.8`, `winter.face.earth.top-base.8.v1`, `winter.face.earth.top-base.8.v2`, `winter.face.earth.top.4`, `winter.face.earth.top.4.v1`, `winter.face.earth.top.4.v2`, `winter.face.earth.top.8`, `winter.face.earth.top.8.v1`, `winter.face.earth.top.8.v2`, `winter.forest.grass.0`, `winter.forest.grass.1`, `winter.forest.grass.2`, `winter.forest.grass.3`, `winter.lake.grass.0`, `winter.lake.grass.1`, `winter.lake.grass.2`, `winter.lake.grass.3`, `winter.plains.grass.0`, `winter.plains.grass.1`, `winter.plains.grass.2`, `winter.plains.grass.3`, `winter.tile.grass.0`, `winter.tile.grass.1`, `winter.tile.grass.2`.
