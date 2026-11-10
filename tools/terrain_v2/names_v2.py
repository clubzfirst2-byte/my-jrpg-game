"""Writes docs/art-release-v2/terrain/NAMES.md (the key scheme for the terrain engineer)."""

from keys_v2 import PREFIX, SINGLE
from transitions import PRIORITY
from wang import tile_count

LABEL = {"grass": "island grass", "plains": "plains grass", "lake": "lake shore grass", "moss": "forest floor (moss)",
         "snow": "mountain snow", "sand": "island sand", "dsand": "desert sand", "path": "path", "ruin": "ruin floor"}


def names_md(files, redrawn, new, copied):
    L = []
    a = L.append
    a("# Ground v2 — key scheme (for wiring)")
    a("")
    a(f"Folder `src/art-release-v2/terrain/`: **{len(files) + len(copied)} PNGs** = {len(redrawn)} v1 keys redrawn + "
      f"{len(new)} new keys + {len(copied)} v1 keys copied unchanged (not redrawn: ruin / wall faces, v1.1 shores, "
      "trees, rocks, floors…). The group **contains every key of the v1 terrain group**, so it can replace it as a whole "
      "(`manifest.json` lists the three groups; the test checks v2 ⊇ v1). All new / redrawn ground tiles are 32×32 art px "
      "(= one 16 px map cell), anchor **top-left**, alpha 0 / 255. Generator: `tools/terrain_v2/gen_v2.py`; "
      "`tools/terrain_v2/render_ref.py` is a reference renderer of everything below (the review images use it).")
    a("")
    a("## 1. Grounds")
    a("")
    a("| ground | prefix (= the v1 key) | tiles | picked by | macro pieces | seasons |")
    a("|---|---|---|---|---|---|")
    for g, p in PREFIX.items():
        n = tile_count(g)
        base = f"`{p}`, `{p}.1` – `.{n - 1}`" if g in SINGLE else f"`{p}.0` – `.{n - 1}`"
        seas = ("autumn (32 calm tiles + 8 pictures), winter (32 calm snow tiles + 8 pictures, with the plant's tips)"
                if g in ("grass", "plains", "lake", "moss") else "—")
        how = "A: steps 1-6 below" if n == 32 else "C: row phase + column symbols"
        mac = "`.macro.0-3`, `.macro2.0-3` … `.macro8.0-3`" if n == 32 else "—"
        a(f"| {LABEL[g]} | `{p}` | {base} | {how} | {mac} | {seas} |")
    a("")
    a("`hash(i, j)` = gameView's hash (render_ref.dhash). For tile.sand / tile.path / tile.ruin, n = 0 is the bare v1 key. "
      "`render_ref.py` does all of this.")
    a("")
    a("**A. Every ground except the ruin floor (round 5; 32 calm tiles in a light and a dark group + 8 pictures of 2×2 tiles):** island / plains / "
      "lake grass, moss, path, mountain snow, island sand, desert sand, and the autumn / winter sets of the 4 seasonal "
      "grounds. Integer `hash` values are unsigned 32-bit; `/` below is a float division.")
    a("")
    a("1. **Blocks.** Cut the display grid (section 2) into blocks of 3×3 display tiles; block `(a, b)` covers display "
      "tiles `3a … 3a+2`, `3b … 3b+2`. Every block (a, b ≥ 0, and one block past the map's right / bottom edge) is "
      "looked at; `h = hash(a, b)`.")
    a("2. **Is there a picture?** Density noise over the blocks, a value noise on a lattice of 4 blocks: "
      "`v(x, y) = (hash(x + 5003, y + 7919) % 1024) / 1023`; `gx = floor(a / 4)`, `gy = floor(b / 4)`, "
      "`fx = (a % 4 + 0.5) / 4`, `fy = (b % 4 + 0.5) / 4`, `sx = fx·fx·(3 − 2·fx)`, `sy = fy·fy·(3 − 2·fy)`; "
      "`top = v(gx, gy) + (v(gx+1, gy) − v(gx, gy))·sx`, `bot = v(gx, gy+1) + (v(gx+1, gy+1) − v(gx, gy+1))·sx`, "
      "`n = top + (bot − top)·sy`. `pNone = min(1, max(0, 2·(n − 0.3)))`. The block has a picture when "
      "`((h >> 16) % 1024) / 1024 >= pNone` (thick where n < 0.3, bare where n > 0.8: clusters and open stretches).")
    a("3. **Where in the block.** `OFF = [0, 0, 1, 2, 2, 2]`; raw offsets `rx(a, b) = OFF[hash(a, b) % 6]`, "
      "`ry(a, b) = OFF[(hash(a, b) >> 8) % 6]`. Then, in this order: `ox = rx(a, b)`, `oy = ry(a, b)`; "
      "if `ox == 2` and `rx(a+1, b) == 0`: `ox = 1`; if `oy == 2` and `ry(a, b+1) == 0`: `oy = 1`; "
      "if `ox == 2` and `oy == 2` and `rx(a+1, b+1) == 0` and `ry(a+1, b+1) == 0`: `oy = 1`; "
      "if `ox == 2` and `oy == 0` and `rx(a+1, b−1) == 0` and `ry(a+1, b−1) == 2`: `ox = 1`. "
      "The picture's NW display tile is `(i0, j0) = (3a + ox, 3b + oy)`; with offset 2 it reaches one tile into the "
      "next block. These rules keep pictures from overlapping (they can touch along an edge), and the chances "
      "(1/3, 1/6, 1/2) make every column and row of a block equally often covered (no 96-px period).")
    a("4. **Which picture** (round 6: no block shares its picture with any of its 8 neighbours where it can be helped): "
      "raw number `r(a, b) = hash(a + 409, b + 1031) % 8`, `k(a, b) = floor(hash(a + 409, b + 1031) / 8)`. The blocks "
      "are taken in 4 classes by `(a % 2, b % 2)`, each class using the final numbers `m` of earlier classes: "
      "**A** `(0, 0)`: `m = r(a, b)`. **B** `(1, 0)`: avoid `m(a−1, b)`, `m(a+1, b)`. **C** `(0, 1)`: avoid "
      "`m(a, b−1)`, `m(a, b+1)`, `m(a−1, b−1)`, `m(a+1, b−1)`, `m(a−1, b+1)`, `m(a+1, b+1)`. **D** `(1, 1)`: avoid "
      "all 8 neighbours `m(a±1, b)`, `m(a, b±1)`, `m(a±1, b±1)`; if that leaves no number, avoid only the 4 side "
      "neighbours. `free` = the numbers 0-7 not avoided, in increasing order; `m = free[k(a, b) % len(free)]`. "
      "Name: `macro` for m = 0, else `macro<m+1>` (`macro2` … `macro8`).")
    a("4b. **Desert dunes** (round 8): cut the blocks into cells of 4×3 blocks, `sa = floor(a / 4)`, "
      "`sb = floor(b / 3)`, `hs = hash(sa + 77, sb + 31)`. The cell's one dune block is `(4·sa + hs % 4, "
      "3·sb + (hs >> 2) % 3)`. If block (a, b) is it and its 9 map cells (step 5) are all desert sand, it shows "
      "`desert.sand.dune<k>.<q>` with `k = 1 + (sa % 3 + 3·(sb % 2) + hash(floor(sa / 3) + 13, floor(sb / 2) + 29)) "
      "% 6`, at the offsets of step 3, whether or not step 2 gave it a picture and instead of the picture of "
      "step 4. One dune per 12 blocks (about 4-5 on a screen); the 6 shapes sit in a 3×2 pattern of cells, so the "
      "same shape is at least 3 cells apart across and 2 down.")
    a("5. **Draw it** only when it stays on the map (`i0 + 2`, `j0 + 2` inside) and the 9 map cells under its 4 display "
      "tiles (cells `i0 … i0+2`, `j0 … j0+2`) are all one ground of this scheme **and one height** (round 8: a "
      "picture never straddles a step): `<prefix>.<name>.<q>`, q = 0 NW "
      "`(i0, j0)`, 1 NE, 2 SW, 3 SE.")
    a("6. **Every other display tile** whose lowest ground is of this scheme gets a calm tile `<prefix>.<c>`, "
      "c = 0-31 (round 6): 0-15 the light group (more lit grain, small lit patches), 16-31 the dark group. "
      "**Group:** `n2 = ` the value noise of step 2 over display tiles with a lattice of 6 tiles and the lattice "
      "values `(hash(x + 12011, y + 3407) % 1024) / 1023` (`gx = floor(i / 6)`, `fx = (i % 6 + 0.5) / 6`, the same "
      "for j; smoothstep blend as in step 2); `q = min(1, max(0, 0.8·(n2 − 0.5) + 0.5))`; group `g = 1` when "
      "`(hash(i + 71, j + 113) % 1024) / 1024 < q`, else 0. **Raw number** `c0(i, j) = 16·g(i, j) + "
      "hash(i + 3, j + 11) % 16`. **Number** (no calm tile shares its number with any of its 8 neighbours): the "
      "display tiles in 4 classes by `(i % 2, j % 2)` exactly as the blocks in step 4: **A** `(0, 0)`: `c = c0`. "
      "**B** `(1, 0)`: avoid `c(i±1, j)`. **C** `(0, 1)`: avoid `c(i, j±1)` and `c(i±1, j±1)`. **D** `(1, 1)`: avoid "
      "all 8 neighbours. `free` = the 16 numbers of the tile's own group `16·g … 16·g + 15` not avoided, in "
      "increasing order; `c = free[(hash(i + 3, j + 11) >> 4) % len(free)]`. The neighbours' numbers are computed by "
      "this rule whatever is drawn there (a picture, another ground). Any calm tile joins any other and any "
      "picture (nothing crosses their edges).")
    a("")
    a("In winter the 4 seasonal grounds use the same rule with their `winter.` keys (snow with the tips of the ground's "
      "own plant), in autumn with their `autumn.` keys. The pictures carry the large things (grass: thickets, lit "
      "patches, flower clusters / reeds, island clover carpets in white bloom - 2 of the 8 pictures wide ones; moss "
      "beds, worn stretches; snow: blue hollows, drift swells, wind ridges, glints, capped stones; sand: ripple fields, "
      "dune swells, pale smooth stretches, pebble clusters, shells / dry grass), the calm tiles a grain and the small "
      "things. Each kind's positions are spread evenly over x and y (in the pictures: one per 2 or 4 px modulo 32), and "
      "the mean row / column brightness of the 16 calm tiles and of the 32 picture quarters is evened out with grain "
      "specks, so no 32- / 64-px pattern on average.")
    a("")
    a("**C. Ruin floor (66 tiles; round 3):** rectangular stones in straight courses 11 art px high that run across the "
      "whole map, their joints staggered course by course.")
    a("- row phase `R = (32·j) mod 11` = `(10·j) mod 11` (0-10), the same for a whole row of display tiles (j ≥ 0)")
    a("- column symbol `s(i)` (0-2) of the vertical line of edges at the west of column i (i ≥ 0), never the same on two "
      "neighbouring lines: `k = floor(i / 2)`, `e0 = hash(k, 7) % 3`, `e1 = hash(k + 1, 7) % 3`; `s = e0` when i is even; "
      "when i is odd, `s = 3 − e0 − e1` if `e0 ≠ e1`, else `(e0 + 1 + hash(k, 11) % 2) % 3`")
    a("- `W = s(i)`, `E = s(i + 1)`, `n = 6·R + 2·W + (E if E < W else E − 1)`")
    a("- the ruin's overlay over water is `tile.ruin.edge.<mask>.<R>` (R = 0-10, the same row phase), so the courses "
      "run on from the overlay into the full tiles beside it. No pictures.")
    a("")
    a("**Changes in round 8** (for the engine): transition overlays never hold a detached island or a hole (16 "
      "sets × `edge.1.0`, `2.0`, `4.3`, `7.0-3` and the foam redrawn); masks 6 / 9 use the same shared wobble as "
      "the others; dunes by step 4b (new formula); pictures only on one height (step 5); inner step corners "
      "`<prefix>.step.inner.<ne|nw>` (2b). No key removed.")
    a("")
    a("**Changes in round 7** (for the engine): transition overlays have 4 variants per mask (masks 6 / 9: 2) chosen "
      "by side states (section 2, step 3); new step rims / shadows (section 2b); the desert's dunes are their own "
      "pictures `desert.sand.dune1-6.0-3` (step 4b; the 8 desert pictures no longer hold dunes). No key removed.")
    a("")
    a("**Changes in round 6** (for the engine): 32 calm tiles instead of 16 (`.16-.31` added for every ground and "
      "season set of A; island grass, plains, lake, moss, path, snow, sand, desert, and the autumn / winter sets), "
      "chosen by step 6 (light / dark groups by a noise; no calm tile equal to any of its 8 neighbours); the picture "
      "number of step 4 now avoids the diagonal neighbours too. Island grass: 2 of the 8 pictures (`.macro`, "
      "`.macro5`) carry a wide clover carpet; desert: 3 (`.macro2`, `.macro5`, `.macro7`) a big dune ridge.")
    a("")
    a("**Changes in round 5** (for the engine): island sand and desert sand move from B (64 tiles by ripple phases) "
      "to A; B is gone. The picture placement of A is new (steps 2-4 above: density noise, offsets 0 / 1 / 2, no two "
      "side-by-side blocks with the same picture). Keys removed (all new in v2; every v1 key stays): `tile.sand.16-63`, "
      "`desert.sand.16-63`. Keys added: `tile.sand.macro*.0-3`, `desert.sand.macro*.0-3` (8 pictures each).")
    a("")
    a("Round 4: A replaced the round-3 edge types of the grass-likes, moss and path and took in mountain snow and the 4 "
      "winter sets (removed then: `*.macro3.4-8`, `mountains.snow.16-63`, `winter.<4 grounds>.16-63`).")
    a("- **Seasons:** `autumn.<key>` / `winter.<key>` for every key of the 4 seasonal grounds (the existing season-key "
      "scheme). `autumn.mountains.snow.*` stays the v1.1 art (copied).")
    a("- Measured (`check.txt`): the repeat measure of the first inspection (mean |ΔL| at 32 px ÷ at 24 px) and the "
      "banding measure (autocorrelation of the row means and of the column means at 32 px and at 64 px), 80×48 fields.")
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
    a("3. `<v>` (round 7): masks 6 and 9 (the border crosses all 4 sides): `v = hash(i + 7, j) % 2` (as before). "
      "Every other mask: `v = sA + 2·sB` (0-3), where A and B are the two sides of the display tile that the border "
      "crosses, in the order N, E, S, W (a side is crossed when its two corners differ in the mask: N = NW≠NE, "
      "E = NE≠SE, S = SW≠SE, W = NW≠SW), and `s` is that side's **state**: the side's edge hash is "
      "`hash(2i+1, 2j)` (N), `hash(2i+2, 2j+1)` (E), `hash(2i+1, 2j+2)` (S), `hash(2i, 2j+1)` (W); "
      "`s = (edgeHash >> 4) & 1`, except **s = 0** when one of the side's two end cells is water (N: cells (i, j), "
      "(i+1, j); E: (i+1, j), (i+1, j+1); S: (i, j+1), (i+1, j+1); W: (i, j), (i, j+1)), or when the display tile "
      "across that side (N: (i, j−1), E: (i+1, j), S: (i, j+1), W: (i−1, j)) has mask 6 or 9 for the same terrain. "
      "The tiles on both sides of a side compute the same state, so the border joins; with state 1 it crosses "
      "about 3 px away from state 0, so a straight path's edge no longer repeats tile by tile. The ruin floor: `<v>` "
      "= its row phase R, 0-10 (section 1 C), unchanged. Round 7 also made every variant's border swing 4+ px "
      "inside the tile (mask 5 was almost straight); the keys `.0` / `.1` stay, `.2` / `.3` are new.")
    a("")
    a("**Priority**, low → high: water (section 3) < " + " < ".join(f"`{PREFIX[p]}`" for p in PRIORITY) + ".")
    a("Grass-like edges lie over path / sand / ruin, sand drifts over path and ruin, snow over path and ruin, every land "
      "over water. One set of 14 masks × 2 variants (ruin: × 11 row phases) per terrain covers every pair it can meet (world map cell edges: "
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
    a("## 2b. One-level steps (round 7, new; replaces the 1-px outline)")
    a("")
    a("For an elevated cell (gameView: its surface square on the cell grid at `(tx·16, ty·16 − h)`), where v1 draws a "
      "1-px dark line on the east / west / north side when that neighbour is lower (`lowerEast`, `lowerWest`, "
      "`lowerNorth`) and a translucent shadow strip on the lower ground east of it:")
    a("- **Rim:** draw `<prefix>.step.<mask>.<v>` over the cell's surface, same position and size (32×32 art px = one "
      "cell), instead of the lines. `<prefix>` = the cell's ground prefix (section 1; with the season prefix in autumn / "
      "winter for the 4 seasonal grounds); `mask = 1·lowerNorth + 2·lowerEast + 4·lowerWest` (1-7); "
      "`v = hash(tx + 5, ty + 9) % 2`. It holds a dark outline 0-3 px deep that swells, thins and breaks off along "
      "the side, a lit rim inside it on the north and west sides (they face the light) and a shaded rim on the east "
      "side. The south side keeps its cliff face (section 4).")
    a("- **Shadow:** on the lower cell east of it (`tx + 1`), instead of the translucent strip, draw "
      "`<prefix>.step.shade.<v>` with the LOWER cell's prefix at that cell's position on its own ground "
      "(`((tx+1)·16, ty·16 − h_east)`), `v = hash(tx + 6, ty + 9) % 2`: a 2-8 px shadow from its west side with a wavy "
      "edge.")
    a("- **Inner corners** (round 8): on a high cell whose north and east neighbours are not lower but whose NE "
      "neighbour is lower, also draw `<prefix>.step.inner.ne` over its surface; north and west not lower, NW lower: "
      "`<prefix>.step.inner.nw`. They join the end of the north rim of the side neighbour and the end of the east / "
      "west rim of the north neighbour (no gap at the corner).")
    a("- **Strength** (round 8): the outline is the ground's lightest tone at least 28 (0-255) darker than its core, "
      "and never lighter than tone 1; the shadow and the shaded east rim the lightest at least 15 darker (grass, "
      "plains, lake: tones 0 / 1; moss 0 / 1; island sand 1 / 1; desert, path, ruin 1 / 2; snow 1 / 2; autumn grass "
      "1 / 2, lake 1 / 1, moss 0 / 1).")
    a("- **Order and opacity:** the rim right after the cell's surface, before the next row's surfaces. The shadow "
      "after all the surfaces of its row (else a slightly lower east cell's surface would hide it), opaque, as "
      "drawn (it covers the small marks of the lower cell's ground under it; if the engine prefers it "
      "see-through, draw it at alpha 0.6 — its tone was chosen for full strength). No shadow when the lower east "
      "cell is water or a ground with no v2 art; a cliff face (south side) keeps its own contact shadow.")
    a("- Along a straight step the outline, rim and shadow depths are 32-periodic in the position along the side, so "
      "they join from cell to cell (variant 1 adds a bump that is 0 at the cell's corners). Keys exist for every "
      "ground of section 1 and every season set (`tile.ruin.step.*` too).")
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
    a("## 4. Cliff faces (round 3: redrawn under the v1 keys)")
    a("")
    a("`face.<earth|stone|sand|desert|path>.<top|mid|mid-base|top-base>.<4|8>` with the variants `.v1` / `.v2` (sand, "
      "desert, path: `.v1` only), and the season lips `autumn.face.earth.*`, `winter.face.earth.*`, `autumn.face.stone.*` "
      "(top / top-base): **the same keys, sizes (32×16 for `.8`, 32×8 for `.4`), stacking and variant rule as v1** "
      "(gameView.addFace, terrainArt.faceVariant), so nothing changes in the engine. Variants join each other (same "
      "outermost columns). `face.ruin.*` and `face.wall.*` (masonry, house walls) are the v1 files, copied.")
    a("")
    a("## 5. New keys by group")
    a("")
    groups = {}
    for k in sorted(new):
        if ".edge." in k:
            head = k.split(".edge.")[0] + ".edge.*"
        elif ".step." in k:
            head = k.split(".step.")[0] + ".step.*"
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
