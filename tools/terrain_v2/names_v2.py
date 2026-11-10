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
        seas = ("autumn (16 calm tiles + 8 pictures), winter (16 calm snow tiles + 8 pictures, with the plant's tips)"
                if g in ("grass", "plains", "lake", "moss") else "—")
        how = "A: calm tile by hash" if n == 16 else "B: W / E phases" if n == 64 else "C: row phase + column symbols"
        mac = "`.macro.0-3`, `.macro2.0-3` … `.macro8.0-3`" if n == 16 else "—"
        a(f"| {LABEL[g]} | `{p}` | {base} | {how} | {mac} | {seas} |")
    a("")
    a("`hash(i, j)` = gameView's hash (render_ref.dhash). For tile.sand / tile.path / tile.ruin, n = 0 is the bare v1 key. "
      "`render_ref.py` does all of this.")
    a("")
    a("**A. Island / plains / lake grass, moss, path, mountain snow, and the winter of the 4 seasonal grounds (round 4; "
      "16 calm tiles + 8 pictures of 2×2 tiles):**")
    a("- **Pictures first.** Cut the display grid (section 2) into blocks of 3×3 display tiles. Block `(a, b)` covers "
      "display tiles `3a … 3a+2`, `3b … 3b+2`. Per block: `h = hash(a, b)`; the picture's NW tile is "
      "`(i0, j0) = (3a + h % 2, 3b + (h >> 1) % 2)` (**a hashed offset of 0 or 1 tile on each axis: pictures are NOT "
      "on even tiles and never touch**); picture number `m = (h >> 2) % 8`; **no picture** when `(h >> 5) % 8 == 0`, "
      "when the picture would leave the map, or when the 9 map cells under its 4 display tiles (cells `i0 … i0+2`, "
      "`j0 … j0+2`) are not all one ground of this scheme. The picture's 4 display tiles are drawn with "
      "`<prefix>.<name>.<q>`, name = `macro` (m = 0) or `macro<m+1>` (m = 1-7: `macro2` … `macro8`), "
      "q = 0 NW `(i0, j0)`, 1 NE, 2 SW, 3 SE.")
    a("- **Every other display tile** whose lowest ground is of this scheme: calm tile `n = hash(i + 3, j + 11) % 16`. "
      "Any calm tile joins any other and any picture (nothing crosses their edges), so no edge types.")
    a("- In winter the 4 seasonal grounds use the same rule with their `winter.` keys (snow with the tips of the "
      "ground's own plant); mountain snow has no seasons.")
    a("- Why: the 8 pictures carry the large things (thickets, lit patches, clover carpets / flowers / reeds, moss beds, "
      "worn stretches; on snow: blue hollows, drift swells, wind ridges, glints, capped stones), the calm tiles a grain "
      "and the small things (clumps, single clover in 4 forms, pebbles, needles, small hollows, glints…). Each kind's "
      "positions are spread evenly over x and y (in the pictures: all different modulo 32), so no 32- or 64-px "
      "pattern on average; the hashed offset keeps the pictures off a 64-px grid.")
    a("")
    a("**B. Sand, desert sand (64 tiles; round 3):** only the W / E edges "
      "carry anything: the ripples cross them at one of 8 phases. `n = E + 8·W`, E / W = `(hash(2i, 2j+1) >> 8) % 8` "
      "for the vertical edge on the left of display tile (i, j) (W) and `(hash(2i+2, 2j+1) >> 8) % 8` on its right (E); "
      "0 when the two tiles' lowest grounds differ. Nothing crosses the N / S edges. No pictures. Round 4: where the "
      "ripples bend from their W rows to their E rows depends on `(E − W) mod 8`, so the bends are not on the same "
      "columns in every tile.")
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
    a("**Changes in round 4** (for the engine): scheme A replaces the round-3 edge types of the grass-likes, moss and "
      "path (no `N + 2E + 4S + 8W`, no P %), and now also covers mountain snow and the 4 winter sets (round 3: B with 64 "
      "tiles). `.macro3` is now a 2×2 picture like the others. Keys removed (all were new in v2; every v1 key stays): "
      "`*.macro3.4-8`, `mountains.snow.16-63`, `winter.<4 grounds>.16-63`. Keys added: `*.macro4.0-3` … `*.macro8.0-3`, "
      "and `.macro.0-3` … `.macro8.0-3` of `mountains.snow` and of the 4 winter sets.")
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
    a("3. `<v>` = 0 or 1, any per-tile hash (they join each other). The ruin floor: `<v>` = its row phase R, 0-10 (section 1 C).")
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
