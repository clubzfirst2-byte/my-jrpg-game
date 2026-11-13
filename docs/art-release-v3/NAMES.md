# Art v3 — keys and placement rules (for wiring)

Folder `src/art-release-v3/terrain/` (and `hero/`, `npc/`, `enemy/`, `objects/` for the pilot). All
ground tiles are 64×64 art px = one 16-px map cell at density 4 (STYLE.md 1–2), anchor top-left,
alpha 0 / 255 only. The reference implementation of every rule below is
`tools/art_v3/gen_ground_v3.py` (functions named in brackets); `ground_tile(tx, ty, season)` there
composes one tile exactly as the game should.

## 0. Hash

`hsh(x, y, s)` [hsh] — 32-bit unsigned arithmetic, inputs wrap as two's complement:

```
h = (x * 374761393 + y * 668265263 + s * 2147483647) mod 2^32
h = ((h ^ (h >>> 13)) * 1274126177) mod 2^32        (JS: Math.imul(...) >>> 0)
return h ^ (h >>> 16)                                 (unsigned)
```

## 1. Plains grass — base layer (always drawn)

- Keys: `<season.>plains.grass.v3.<m><r><c>` — season prefix `""` (summer, spring), `autumn.`, `winter.`;
  pattern `m` in `abcdefgh`; `r`, `c` in 0–3. 128 keys per season.
- A 4×4-tile block `(bx, by) = (floor(tx/4), floor(ty/4))` uses pattern `macro_of(bx, by)` [macro_of]:
  - `near` = the patterns of the blocks (bx−1, by), (bx, by−1), (bx+1, by−1), (bx−1, by−1) (those that
    exist: bx ≥ 0, by ≥ 0; computed by this same rule)
  - `order` = the 8 letters sorted by `hsh(bx*7 + code(letter), by*13 + code(letter), 91)` ascending
    (code = the ASCII code, a = 97)
  - the first letter of `order` not in `near`
- Tile in the block: `r = ty % 4`, `c = tx % 4`.

## 2. Plains grass — transitions (unchanged from v2)

- Keys: `<season.>plains.grass.v3.edge.<mask>.<v>` — 52 per season. Drawn exactly by the v2 rule
  (`docs/art-release-v2/terrain/NAMES.md` 2: dual grid, priority, mask NW 1 / NE 2 / SW 4 / SE 8,
  side-state variant v 0–3, masks 6 / 9: 0–1). The border is v2's curve at 2×, so v3 edges join v2
  ground on the other side.

### 2.1 Winter exception: the forest / plains pair (decided by the director, 2026-11-12)

v2 NAMES 2 says the priority does not change in winter. **One exception, winter only:**

- On a display tile whose 4 corners hold **both forest (`moss`, `forest.grass`) and plains
  (`plains`, `plains.grass`)** cells, those two grounds **exchange their positions** in the v2
  priority list, for that tile: `… < mountains.snow < plains.grass < lake.grass < forest.grass < tile.grass`
  (v2: `… < mountains.snow < forest.grass < lake.grass < plains.grass < tile.grass`). Path, sand, snow and
  ruin stay below both, `tile.grass` above both; `lake.grass` matters only on a tile that also has a lake
  corner. A tile with no plains corner, or no forest corner, uses the v2 order.
- So on a forest / plains tile in winter: draw the **plains winter base**
  (`winter.plains.grass.v3.<m><r><c>` and its flow layer as usual), then the **forest winter edge**
  `winter.forest.grass.v3.edge.<mask>.<v>` with **mask = the forest corners** (NW 1, NE 2, SW 4, SE 8).
  (Summer / autumn: v2 order, the plains edge over the forest base, mask = the plains corners.)
- With other grounds on the same tile (e.g. forest, plains and path corners): the lowest ground's base,
  then each higher ground low to high, in the tile's order (path base, then plains edge with mask =
  plains + forest corners, then forest edge with mask = forest corners).
- **The variant v** of the forest edge: the v2 rule (v2 NAMES 2, item 3) unchanged, with **every mask
  read in the winter order** of its own display tile:
  - masks 6 / 9: `v = hash(i + 7, j) % 2`;
  - other masks: `v = sA + 2·sB` over the crossed sides in the order N, E, S, W; `s = (edgeHash >> 4) & 1`,
    and `s = 0` when a side's end cell is water, or when **this tile's or the tile across that side's
    forest mask, read in that tile's own winter order, is 6 or 9**.
  - This matters where forest cells touch **only diagonally** (two forest cells at (x, y) and
    (x+1, y+1) with plains at the other two corners): that tile's forest mask is 9 (or 6), so the sides
    of its 4 neighbours toward it have state 0, and the border joins. Reading the neighbour's mask in
    the v2 order instead (forest below plains: every forest / plains corner counts, the mask is 15)
    gives a different v on those neighbours (3 of 140 border tiles on the inspection's test map).
  - Reference: `winter_forest_v` in `tools/art_v3/compare_forest_v3.py` (matches the inspection's own
    renderer on 140 / 140 border tiles).
- Why: the plains winter edges have a 1-texel bright rim; between snow and snow it showed as a thin
  white pencil line round every clearing. The forest winter edges have no rim (FOREST.md 1).
- Drawing only: collision, heights and the map do not change.

## 3. Plains grass — flow layer (round 7; drawn over the base on full plains tiles only)

### 3.1 Corner state [flow_corner]

For world corner (cx, cy) (the tile (tx, ty) has corners (tx, ty), (tx+1, ty), (tx+1, ty+1), (tx, ty+1)):

```
vn(x, y, scale, seed): gx = x/scale, gy = y/scale, x0 = floor(gx), y0 = floor(gy),
    fx = gx − x0, fy = gy − y0, sx = fx²(3 − 2fx), sy = fy²(3 − 2fy),
    r(i, j) = (hsh(i, j, seed) % 10000) / 10000,
    a = r(x0, y0) + (r(x0+1, y0) − r(x0, y0))·sx,  b = r(x0, y0+1) + (r(x0+1, y0+1) − r(x0, y0+1))·sx,
    return a + (b − a)·sy
value(cx, cy) = 0.65·vn(cx, cy, 6, 1) + 0.35·vn(cx, cy, 3, 2)
raw = 'd' if value < 0.32, 'l' if value > 0.66, else 'm'
state = raw, except 'm' when any of the 8 neighbouring corners has raw = the opposite of raw ('d'↔'l')
```

The game also returns **'m' when any of the 4 map cells around the corner is not plains grass** (the
flow fades out before transitions), and draws no flow on a tile that is not entirely plains grass.

### 3.2 Which picture [flow_key] — **changed in round 7; 1111 rule changed in round 8**

`flow_key(tx, ty)` returns `None` or **(kind, bits, v, flip)**:

1. corners TL, TR, BR, BL; if none is 'd' or 'l' → None. `kind` = the one that occurs ('d' or 'l';
   both never occur on one tile). `b` = 4 chars, '1' where the corner is `kind`.
2. Mirror: `MIRROR = {0100: 1000, 0010: 0001, 0110: 1001, 1101: 1110, 1011: 0111, 0101: 1010}`.
   If `b` is a key of MIRROR: `bits = MIRROR[b]`, `flip = true`; else `bits = b`, `flip = false`.
   (Stored sets: 1000, 0001, 1001, 1110, 0111, 1100, 0011, 1010, 1111.)
3. Side state of the WORLD tile's side [side_state]:
   `N: hsh(2tx+1, 2ty, 61)`, `E: hsh(2tx+2, 2ty+1, 61)`, `S: hsh(2tx+1, 2ty+2, 61)`, `W: hsh(2tx, 2ty+1, 61)`;
   `s = (h >>> 4) & 1`. When `flip`, the stored tile's E side is the world W side and vice versa
   (`sStored(E) = s(W)`, `sStored(W) = s(E)`; N and S unchanged).
4. Crossed sides of `bits` (corners differ along the side, order N, E, S, W): N = TL≠TR, E = TR≠BR,
   S = BL≠BR, W = TL≠BL.
   - none (1111) [full_v]: `v0 = hsh(tx, ty, 33) % 4`; if the LEFT tile (tx − 1, ty) is also 1111 and
     its v equals v0, then `v = (v0 + 1) % 4`, else `v = v0`. The left tile's v is found by the same
     rule, so: go left from (tx, ty) while the tile is 1111 to the first 1111 tile x0 of the row run
     (its left tile is not 1111), then for x = x0 … tx: `v0 = hsh(x, ty, 33) % 4`,
     `v = (v0 + 1) % 4 if v0 == vPrev else v0` (vPrev = none at x0). Two 1111 tiles side by side never
     have the same v. `flip = ((hsh(tx, ty, 35) >>> 2) & 1) == 1` (unchanged).
     "1111" = all four corners are the same kind ('d' or 'l'; never 'm').
   - 4 sides (1010): `v = sStored(N) + 2·sStored(E) + 4·sStored(S) + 8·sStored(W)` (0–15)
   - 2 sides A, B: `v = sStored(A) + 2·sStored(B) + 4·((tx + 2·ty) % 3)` (0–11; `%` non-negative)
5. File: `<set.>plains.grassflow.v3.<bits>.<v>` with set `""` for summer and autumn, `winter.` for winter.
6. Draw: the picture over the base tile, **mirrored left-right when `flip`** (scale.x = −1 about the
   tile's centre), **multiplied by the colour `FLOW_TINT[season][kind]`** (the pictures are grey:
   blade tip 255, body 214; the result is tip = the tint, body = 214/255 of it).

Before round 7 the return was (kind, bits, v) with files `<season.>plains.grassflow.v3.<kind><bits>.<v>`
(v 0–7, coloured). Those files are gone.

### 3.3 FLOW_TINT [flow_tints]

| season | d (thick grass) | l (sunny grass) |
|---|---|---|
| summer (and spring) | `#335d3a` | `#638b46` |
| autumn | `#80572c` | `#a79138` |
| winter | `#aabcd6` | `#fafcff` |

Round 8 changed the autumn and winter colours only (the shapes are the same pictures for every tint).
Before: autumn d `#744b28`, l `#91802e`; winter d `#99abc7`, l `#dce6f2`.

### 3.4 Memory (one season resident)

Base 128 + edges 52 + flow shapes 104 = 284 tiles of 64×64 = 4.65 MB (4.44 MiB) RGBA; in atlases
1024×1024 (256 tiles) + 512×256 (28 of 32) = 4.72 MB (4.5 MiB). The flow shapes are shared by summer and
autumn (only the tint changes); winter loads its own set.

## 4. Plains trees and props (production order 3)

- `<season.>plains.tree.v3.<kind>.<f>`: kind `oak_l` 160×224, `oak_m` 112×160, `sapling` 64×112,
  `pine` 96×200; f = sway frame 0–2 (play 0, 1, 0, 2); winter broadleaf: frame 0 only (bare).
- **No plains `pine` near the forest region** (decided by the director, 2026-11-13; FOREST.md 4):
  where the forest's art is resident, the plains pine is not loaded, so the map must not place
  `plains.tree.v3.pine` in any 32-tile chunk (`gameView.CHUNK`) whose Chebyshev chunk distance
  `max(|cx − ax|, |cy − ay|)` to a chunk `(ax, ay)` overlapped by the forest region's rectangle
  (`r.tx, r.ty, r.tw, r.th`, the same test as `gameView.chunkBundles`) is 2 or less. Basis: a region's
  bundle is held while one of its chunks is built (view + 4 tiles, `CHUNK_LOAD_MARGIN_TILES`) or kept
  (view + 12, `CHUNK_KEEP_MARGIN_TILES`), or while its rectangle is within 32 tiles of the view
  (`gameView.regionNear`); the ring of cells outside a chunk loads only the next region's
  `ground:` bundle (`ringBundles`), not its trees. So a plains pine that can be on screen while the forest
  bundle is held has its foot at most 32 + 21 + 1 = 54 tiles across / 32 + 12 + 4 = 48 tiles vertically from
  the rectangle (largest view 20.8×11.7 tiles, STYLE.md 2): within 2 chunks. Recompute if these
  numbers change.
- `<season.>plains.prop.v3.<kind>.<f>`: `tuft`, `tallgrass`, `flowers_mix`, `flowers_white`,
  `flowers_yellow` (f 0–1, sway), `bush_berry`, `bush`, `shrub`, `stump`, `rock_s`, `rock_m`,
  `pebbles`, `log`, `mushrooms`, `clover` (f 0).
- Anchor: the bottom centre (the foot on the bottom row).

## 5. Hero (production order 2)

- `hero.<action>.<dir>.<n>` in `src/art-release-v3/hero/`, the same actions, frame counts, fps and keys as
  the approved hero (`src/art-release/hero`, `src/view/heroAnim.js`). 64×112 (the actions v1 draws 48 wide:
  96×112). Anchor: the bottom row's centre (v1's bottom-centre anchor ×2).
- dir `down`, `up`, `right` are stored. **`left` is not stored for actions without a held prop**: the game
  draws `right` mirrored (scale.x = −1 about the frame's centre).
  **The engine needs this step** (the v1 loader expects a `hero.<action>.left.<n>` file for every frame):
  for idle, walk, run, jump, land, glide, climb, swim, dodge, hurt and down, when
  `hero.<action>.left.<n>` is asked for, load `hero.<action>.right.<n>` and draw it with scale.x = −1
  (the anchor, the bottom row's centre, stays on the feet). Only attack1–3, bow and guard have real
  `left` files. v1's left frames are exact mirrors of its
  right frames for every such action. Actions with a prop in one hand (attack1–3, bow, guard) store `left`
  too.
- Done so far: idle 4, walk 6, run 6 for down / right / up (48 files); attack1 4, attack2 4, attack3 6, bow 4,
  guard 2 for down / right / up / left, dodge 4 and hurt 2 for down / right / up (98 files).
- jump 2, land 2, glide 4, climb 4, swim 4, down 4 for down / right / up (60 files). All 206 stored frames are done.
- climb, swim and glide are loaded only when used (decision 2026-11-12, STYLE 10.2).
