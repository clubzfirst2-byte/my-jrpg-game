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

### 3.2 Which picture [flow_key] — **changed in round 7**

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
   - none (1111): `v = hsh(tx, ty, 33) % 4`, `flip = ((hsh(tx, ty, 35) >>> 2) & 1) == 1`
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
| autumn | `#744b28` | `#91802e` |
| winter | `#99abc7` | `#dce6f2` |

### 3.4 Memory (one season resident)

Base 128 + edges 52 + flow shapes 104 = 284 tiles of 64×64 = 4.65 MB (4.44 MiB) RGBA; in atlases
1024×1024 (256 tiles) + 512×256 (28 of 32) = 4.5 MiB. The flow shapes are shared by summer and
autumn (only the tint changes); winter loads its own set.

## 4. Plains trees and props (production order 3)

- `<season.>plains.tree.v3.<kind>.<f>`: kind `oak_l` 160×224, `oak_m` 112×160, `sapling` 64×112,
  `pine` 96×200; f = sway frame 0–2 (play 0, 1, 0, 2); winter broadleaf: frame 0 only (bare).
- `<season.>plains.prop.v3.<kind>.<f>`: `tuft`, `tallgrass`, `flowers_mix`, `flowers_white`,
  `flowers_yellow` (f 0–1, sway), `bush_berry`, `bush`, `shrub`, `stump`, `rock_s`, `rock_m`,
  `pebbles`, `log`, `mushrooms`, `clover` (f 0).
- Anchor: the bottom centre (the foot on the bottom row).
