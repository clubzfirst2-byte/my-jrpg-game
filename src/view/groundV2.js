// @ts-check
// Ground v2 (gfx W1; docs/art-release-v2/terrain/NAMES.md, reference renderer tools/terrain_v2/render_ref.py):
// the ground drawn on a DUAL grid — display tiles shifted half a cell (+8, +8 game px), each covering
// the centres of 4 map cells (NW, NE, SW, SE) — so borders between grounds become drawn transitions
// instead of a 16-px staircase. Per display tile:
//   - with water corners: shallow / deep water (+ the deep-edge overlay when mixed, + the shore foam
//     overlay when any corner is land), animated, then each land's overlay;
//   - else the lowest-priority land as a full tile (a variant in patches, or a 2×2 macro piece), then
//     each higher land present, low to high, as its edge overlay (mask = the corners whose priority is
//     at least its own; all 4 → its base tile).
// Pure: the view (gameView.js) supplies the cells and draws the layers. Collision is not involved.

/** Land priority, low → high (water is below all). */
export const PRIORITY = Object.freeze(['ruin', 'path', 'dsand', 'sand', 'snow', 'moss', 'lake', 'plains', 'grass']);

/** The key prefix of each ground class (= its v1 key family). */
export const PREFIX = Object.freeze({
  grass: 'tile.grass',
  plains: 'plains.grass',
  lake: 'lake.grass',
  moss: 'forest.grass',
  snow: 'mountains.snow',
  sand: 'tile.sand',
  dsand: 'desert.sand',
  path: 'tile.path',
  ruin: 'tile.ruin',
});

/** Grounds whose calm tile is the bare prefix (tile.sand, tile.path, tile.ruin), not "<prefix>.0". */
const BARE = new Set(['sand', 'path', 'ruin']);

/** The grounds the seasons redraw (autumn / winter keys exist for them). */
export const SEASONAL = Object.freeze(['grass', 'plains', 'lake', 'moss']);

/** Water frames and their length (NAMES.md: 4 frames, 0.25–0.3 s each). */
export const WATER_FRAMES = 4;
export const WATER_FRAME_SEC = 0.28;

/** Corner bits: NW 1, NE 2, SW 4, SE 8; and the cell offsets of the 4 corners. */
export const CORNERS = Object.freeze([
  [0, 0, 1],
  [1, 0, 2],
  [0, 1, 4],
  [1, 1, 8],
]);

/**
 * A map cell's ground class, or null for grounds drawn on the cell grid (wood, wall top, metal,
 * pit, dark): water, the region's grass, sand (the desert's own), path, ruin floor.
 * @param {'grass' | 'sand' | 'path' | 'ruin' | 'water' | 'other'} ground @param {string | undefined} region
 * @returns {string | null}
 */
export function groundClass(ground, region) {
  if (ground === 'water') return 'water';
  if (ground === 'path') return 'path';
  if (ground === 'ruin') return 'ruin';
  if (ground === 'sand') return region === 'desert' ? 'dsand' : 'sand';
  if (ground === 'grass') return { plains: 'plains', lake: 'lake', forest: 'moss', mountains: 'snow' }[region ?? ''] ?? 'grass';
  return null;
}

/**
 * The key of a land tile: name "0" (the calm base), "1".. (its other tiles), "macro.<q>", "edge.<mask>.<v>".
 * @param {string} cls @param {string} name
 */
export function landKey(cls, name) {
  const p = /** @type {Record<string, string>} */ (PREFIX)[cls];
  if (name === '0' && BARE.has(cls)) return p;
  return `${p}.${name}`;
}

/**
 * Deep water: a water cell with no land within 2 cells (Chebyshev; outside the map is not land), kept
 * only where such cells form a 2×2 or larger area (W1 inspection: no 1-cell deep trenches).
 * @param {number} width @param {number} height @param {(x: number, y: number) => boolean} isWater
 * @returns {Uint8Array} 1 = deep
 */
export function deepMap(width, height, isWater) {
  // land distance ≤ 2 by dilating the land mask twice (separable max over a 5×5 window)
  const land = new Uint8Array(width * height);
  for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) land[y * width + x] = isWater(x, y) ? 0 : 1;
  const rows = new Uint8Array(width * height);
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      let v = 0;
      for (let dx = -2; dx <= 2 && !v; dx++) {
        const nx = x + dx;
        if (nx >= 0 && nx < width) v = land[y * width + nx];
      }
      rows[y * width + x] = v;
    }
  }
  const deep = new Uint8Array(width * height);
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      if (land[y * width + x]) continue;
      let v = 0;
      for (let dy = -2; dy <= 2 && !v; dy++) {
        const ny = y + dy;
        if (ny >= 0 && ny < height) v = rows[ny * width + x];
      }
      deep[y * width + x] = v ? 0 : 1;
    }
  }
  // keep a deep cell only if one of the 4 blocks of 2×2 cells containing it is all deep
  const at = (/** @type {number} */ x, /** @type {number} */ y) => x >= 0 && y >= 0 && x < width && y < height && deep[y * width + x] === 1;
  const kept = new Uint8Array(width * height);
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      if (!at(x, y)) continue;
      for (const [ox, oy] of [[0, 0], [-1, 0], [0, -1], [-1, -1]]) {
        if (at(x + ox, y + oy) && at(x + ox + 1, y + oy) && at(x + ox, y + oy + 1) && at(x + ox + 1, y + oy + 1)) {
          kept[y * width + x] = 1;
          break;
        }
      }
    }
  }
  return kept;
}

/**
 * Deep water, shaped (inspection R2; the engine's, not render_ref's): a water cell is deep when its
 * distance to the nearest land cell (Euclidean, in cells; outside the map is not land) is more than a
 * threshold of 2 + 1.6 × a smooth noise (2-cell lattice) ± 0.7 by a hash per cell (2.0 … 4.3) — so the
 * deep area's border steps in and out every few cells along a straight shore and its corners are round,
 * not a copy of the shore 2 cells out —, as deepMap only where such cells form a 2×2 area, and with no
 * straight border longer than 4 cells (R3, notchStraightRuns; world map: longest straight run along
 * cell edges 43 → 4 cells, none of 5 or more). The shallow band is always 2+ cells wide.
 * @param {number} width @param {number} height @param {(x: number, y: number) => boolean} isWater
 * @param {(a: number, b: number) => number} hash
 * @returns {Uint8Array} 1 = deep
 */
export function deepMapShaped(width, height, isWater, hash) {
  const R = 5;
  const land = new Uint8Array(width * height);
  for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) land[y * width + x] = isWater(x, y) ? 0 : 1;
  const deep = new Uint8Array(width * height);
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      if (land[y * width + x]) continue;
      const t = Math.max(2, 2 + 1.6 * smoothNoise(x, y, 2, 4441, 9157, hash) + 1.4 * ((hash(x + 811, y + 277) % 1024) / 1023 - 0.5));
      let near = Infinity;
      for (let dy = -R; dy <= R && near > t * t; dy++) {
        const ny = y + dy;
        if (ny < 0 || ny >= height) continue;
        for (let dx = -R; dx <= R; dx++) {
          const nx = x + dx;
          if (nx < 0 || nx >= width || !land[ny * width + nx]) continue;
          near = Math.min(near, dx * dx + dy * dy);
        }
      }
      deep[y * width + x] = near > t * t ? 1 : 0;
    }
  }
  // R3: no straight border longer than 4 cells (notches, then the 2×2 rule again, until it holds)
  let out = keep2x2(width, height, deep);
  for (let n = 0; n < 4; n++) {
    const next = keep2x2(width, height, notchStraightRuns(out, width, height, isWater, hash, 4));
    if (next.every((v, k) => v === out[k])) break;
    out = next;
  }
  return out;
}

/**
 * Inspection R3: breaks the deep area's straight borders. Along each line of cell edges (between rows,
 * then between columns) where deep and shallow water meet for more than maxRun cells in a row, a deep
 * cell on the border is made shallow every 2 … maxRun cells (by hash): a small notch, so no straight
 * piece is longer than maxRun. Only deep cells change (the shallow band along the shore never narrows).
 * @param {Uint8Array} deep @param {number} width @param {number} height
 * @param {(x: number, y: number) => boolean} isWater @param {(a: number, b: number) => number} hash @param {number} maxRun
 */
function notchStraightRuns(deep, width, height, isWater, hash, maxRun) {
  const d = deep.slice();
  for (const horiz of [true, false]) {
    const A = horiz ? height : width;
    const B = horiz ? width : height;
    for (let a = 1; a < A; a++) {
      const cells = (/** @type {number} */ b) => (horiz ? [b, a, b, a - 1] : [a, b, a - 1, b]);
      let run = 0;
      let start = 0;
      for (let b = 0; b <= B; b++) {
        const [x1, y1, x0, y0] = cells(b);
        const on = b < B && isWater(x1, y1) && isWater(x0, y0) && d[y1 * width + x1] !== d[y0 * width + x0];
        if (on) {
          if (!run) start = b;
          run++;
          continue;
        }
        if (run > maxRun) {
          for (let k = start + 1 + (hash(start + 31 * a, a + 7) % maxRun); k < b; k += 2 + (hash(k + 13, a + (horiz ? 17 : 34)) % (maxRun - 1))) {
            const [p1, q1, p0, q0] = cells(k);
            if (d[q1 * width + p1]) d[q1 * width + p1] = 0;
            else if (d[q0 * width + p0]) d[q0 * width + p0] = 0;
          }
        }
        run = 0;
      }
    }
  }
  return d;
}

/** Keeps a deep cell only if one of the 4 blocks of 2×2 cells containing it is all deep. @param {number} width @param {number} height @param {Uint8Array} deep */
function keep2x2(width, height, deep) {
  const at = (/** @type {number} */ x, /** @type {number} */ y) => x >= 0 && y >= 0 && x < width && y < height && deep[y * width + x] === 1;
  const kept = new Uint8Array(width * height);
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      if (!at(x, y)) continue;
      for (const [ox, oy] of [[0, 0], [-1, 0], [0, -1], [-1, -1]]) {
        if (at(x + ox, y + oy) && at(x + ox + 1, y + oy) && at(x + ox, y + oy + 1) && at(x + ox + 1, y + oy + 1)) {
          kept[y * width + x] = 1;
          break;
        }
      }
    }
  }
  return kept;
}

/** A ground class's place in PRIORITY (-1 when not in it), as PRIORITY.indexOf. */
const RANK = new Map(PRIORITY.map((c, i) => [c, i]));
/** @param {string} c */
const rankOf = (c) => RANK.get(c) ?? -1;

/**
 * @typedef {{ key: string, anim: boolean }} Layer
 *   anim: an animated water key without its frame ("<key>.<f>" is drawn, f = 0..3)
 */

/**
 * The layers of one display tile (bottom first).
 * @param {{ cls: string[], deep: boolean[], waterVariant: number, edgeVariant: (cls: string, mask: number) => number,
 *   pick: (cls: string) => string, macro: () => string | null }} t
 *   cls / deep: the 4 corners (NW, NE, SW, SE); pick = the base name for a full land tile (a variant);
 *   edgeVariant = the variant of a land's edge overlay of a mask (round 7: 0-3 by the side states; masks
 *   6 / 9: 0 / 1; the ruin floor: its row phase);
 *   macro = a macro piece name ("macro.<q>") when the 4 corners are one land and the block is chosen
 * @returns {Layer[]}
 */
export function displayLayers({ cls, deep, waterVariant, edgeVariant, pick, macro }) {
  // (gfx v2 integration, start-up: the same layers as before, worked out in plain loops — it runs for
  // every display tile of every chunk built; tests/unit/groundV2*.test.js)
  /** @type {Layer[]} */
  const out = [];
  let nLand = 0;
  let allDeep = true;
  let deepMask = 0;
  let landMask = 0;
  let same = true;
  /** @type {string[]} the land classes, each once, in corner order */
  const kinds = [];
  for (let k = 0; k < 4; k++) {
    const c = cls[k];
    const bit = CORNERS[k][2];
    if (c === 'water') {
      if (deep[k]) deepMask |= bit;
      else allDeep = false;
    } else {
      nLand++;
      landMask |= bit;
      allDeep = false;
      if (!kinds.includes(c)) kinds.push(c);
    }
    if (c !== cls[0]) same = false;
  }
  let lowest = null;
  if (nLand < 4) {
    const v = waterVariant ? '.v1' : '';
    out.push({ key: `tile.water${allDeep ? '.deep' : ''}${v}`, anim: true });
    if (deepMask && !allDeep) out.push({ key: `tile.water.deep.edge.${deepMask}`, anim: true });
    if (landMask) out.push({ key: `tile.water.foam.${landMask}`, anim: true });
  } else {
    // the first corner of the lowest rank (corner order)
    for (let k = 0; k < 4; k++) if (lowest === null || rankOf(cls[k]) < rankOf(lowest)) lowest = cls[k];
    const name = (same ? macro() : null) ?? pick(/** @type {string} */ (lowest));
    out.push({ key: landKey(/** @type {string} */ (lowest), name), anim: false });
  }
  if (kinds.length > 1) kinds.sort((a, b) => rankOf(a) - rankOf(b)); // (stable, as before)
  for (const t of kinds) {
    if (t === lowest) continue;
    const rt = rankOf(t);
    let mask = 0;
    for (let k = 0; k < 4; k++) if (cls[k] !== 'water' && rankOf(cls[k]) >= rt) mask |= CORNERS[k][2];
    out.push({ key: mask === 15 ? landKey(t, '0') : landKey(t, `edge.${mask}.${edgeVariant(t, mask)}`), anim: false });
  }
  return out;
}

/**
 * The quarter of a cell's own tile that falls in a display tile, for display tiles that cannot blend
 * (a corner raised, a ramp, or a ground with no v2 transitions): the NW corner cell shows its SE
 * quarter, and so on. Returns the quarter name of corner k.
 * @param {number} k 0 NW, 1 NE, 2 SW, 3 SE
 */
export const quarterOfCorner = (k) => /** @type {const} */ (['se', 'sw', 'ne', 'nw'])[k];

// --- Rounds 2-6 (NAMES.md section 1): the tile of a display tile, picked in one of 2 ways ---
//   A  (rounds 5-6) every ground but the ruin floor (island / plains / lake grass, moss, path, mountain
//      snow, island sand, desert sand; and the autumn / winter sets of the 4 seasonal grounds, their
//      season's keys): 8 pictures of 2×2 tiles, at most one per block of 3×3 display tiles
//      (macroPlacement), and elsewhere one of 32 calm tiles, light (0-15) or dark (16-31) by a noise,
//      never the same as a neighbour's (calmNumber); nothing crosses their edges
//   C  ruin floor: 66 tiles, stone courses 11 art px high across the whole map: the row phase R of the
//      tile's row and the symbols (0-2) of its column's two edges, n = 6R + 2W + (E if E < W else E - 1);
//      its overlay over water is edge.<mask>.<R>; no pictures

/** The grounds with pictures (A; render_ref.BUSY_MACRO). */
export const MACRO_GROUNDS = Object.freeze(['grass', 'plains', 'lake', 'moss', 'path', 'snow', 'sand', 'dsand']);

/** The names of a ground's step pieces (NAMES.md 2b): rims "step.<mask>.<v>" (mask N 1 + E 2 + W 4), the shadow, the inner corners. */
export const STEP_NAMES = Object.freeze([...[1, 2, 3, 4, 5, 6, 7].flatMap((m) => [`step.${m}.0`, `step.${m}.1`]), 'step.shade.0', 'step.shade.1', 'step.inner.ne', 'step.inner.nw']);

/** The names of the 8 pictures: picture m is "macro" (m = 0) or "macro<m+1>". */
export const MACRO_NAMES = Object.freeze(['macro', 'macro2', 'macro3', 'macro4', 'macro5', 'macro6', 'macro7', 'macro8']);

/** How a ground's tiles are picked (the same in every season). @param {string} cls @returns {'A' | 'C'} */
export const tileScheme = (cls) => (cls === 'ruin' ? 'C' : 'A');

/** How many tiles a ground has (names "0" .. count - 1). @param {string} cls */
export const tileCount = (cls) => (tileScheme(cls) === 'C' ? 66 : 32);

/** @typedef {(a: number, b: number) => number} Hash */

/** Python's floor modulo (the reference's % on negative numbers). @param {number} a @param {number} n */
const pmod = (a, n) => ((a % n) + n) % n;

/**
 * NAMES.md 1 A: a value noise in [0, 1], lattice values (hash(gx + sx0, gy + sy0) % 1024) / 1023 every
 * `cell` units, smoothstep-blended (render_ref._smooth_noise).
 * @param {number} x @param {number} y @param {number} cell @param {number} sx0 @param {number} sy0 @param {Hash} hash
 */
export function smoothNoise(x, y, cell, sx0, sy0, hash) {
  const gx = Math.floor(x / cell);
  const gy = Math.floor(y / cell);
  const fx = (pmod(x, cell) + 0.5) / cell;
  const fy = (pmod(y, cell) + 0.5) / cell;
  const v = (/** @type {number} */ p, /** @type {number} */ q) => (hash(p + sx0, q + sy0) % 1024) / 1023;
  const sx = fx * fx * (3 - 2 * fx);
  const sy = fy * fy * (3 - 2 * fy);
  const top = v(gx, gy) + (v(gx + 1, gy) - v(gx, gy)) * sx;
  const bot = v(gx, gy + 1) + (v(gx + 1, gy + 1) - v(gx, gy + 1)) * sx;
  return top + (bot - top) * sy;
}

/** The neighbours a cell of class (x % 2, y % 2) avoids (steps 4 and 6): B (1, 0) its 2 side ones, C (0, 1) 6, D (1, 1) all 8; A none. @param {number} x @param {number} y @returns {[number, number][]} */
function avoided(x, y) {
  const cx = pmod(x, 2);
  const cy = pmod(y, 2);
  if (cx === 0 && cy === 0) return [];
  if (cx === 1 && cy === 0) return [[x - 1, y], [x + 1, y]];
  if (cx === 0) return [[x, y - 1], [x, y + 1], [x - 1, y - 1], [x + 1, y - 1], [x - 1, y + 1], [x + 1, y + 1]];
  /** @type {[number, number][]} */
  const out = [];
  for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) if (dx || dy) out.push([x + dx, y + dy]);
  return out;
}

/** A step 6: the calm tiles' group of display tile (i, j): 0 light (0-15), 1 dark (16-31), by a noise of 6-tile cells. @param {number} i @param {number} j @param {Hash} hash */
export function calmGroup(i, j, hash) {
  const n = smoothNoise(i, j, 6, 12011, 3407, hash);
  const q = Math.min(1, Math.max(0, 0.8 * (n - 0.5) + 0.5));
  return (hash(i + 71, j + 113) % 1024) / 1024 < q ? 1 : 0;
}

/**
 * A step 6: the calm tile (0-31) of display tile (i, j) — or of a cell drawn on the cell grid, by the same
 * rule over cells: its group's raw number, or (classes B, C, D by (i % 2, j % 2)) the k-th number of
 * its group none of the neighbours it avoids has. The neighbours' numbers come first, so a memo is
 * passed: one per chunk build (gameView.groundPiecesV2), never kept per frame.
 * @param {number} i @param {number} j @param {Hash} hash @param {Map<number, number>} [memo] keyed by calmKey
 */
export function calmNumber(i, j, hash, memo = new Map()) {
  const key = calmKey(i, j);
  const known = memo.get(key);
  if (known !== undefined) return known;
  const h = hash(i + 3, j + 11);
  const g = calmGroup(i, j, hash);
  let n = 16 * g + (h % 16);
  const nb = avoided(i, j);
  if (nb.length) {
    const taken = new Set(nb.map(([x, y]) => calmNumber(x, y, hash, memo)));
    const free = [];
    for (let k = 0; k < 16; k++) if (!taken.has(16 * g + k)) free.push(16 * g + k);
    n = free[(h >>> 4) % free.length];
  }
  memo.set(key, n);
  return n;
}

/** A memo key for (i, j) (|i|, |j| < 2^15). @param {number} i @param {number} j */
const calmKey = (i, j) => (i + 32768) * 65536 + (j + 32768);

/** C: the row phase of display-tile row j: (32·j) mod 11. @param {number} j */
export const ruinRow = (j) => (((10 * j) % 11) + 11) % 11;

/**
 * C: the symbol (0-2) of the vertical line of tile edges at the west of display-tile column i;
 * neighbouring lines never have the same symbol (wang.ruin_symbol).
 * @param {number} i @param {(a: number, b: number) => number} hash gameView's hash
 */
export function ruinSymbol(i, hash) {
  const k = Math.floor(i / 2);
  const e0 = hash(k, 7) % 3;
  if (i - 2 * k === 0) return e0;
  const e1 = hash(k + 1, 7) % 3;
  return e0 !== e1 ? 3 - e0 - e1 : (e0 + 1 + (hash(k, 11) % 2)) % 3;
}

/** C: n = 6R + 2W + (E if E < W else E - 1) for row phase R and the column's symbols W ≠ E. @param {number} r @param {number} w @param {number} e */
export const ruinIndex = (r, w, e) => 6 * r + 2 * w + (e < w ? e : e - 1);

/** C: the ruin tile of display tile (i, j). @param {number} i @param {number} j @param {(a: number, b: number) => number} hash */
export const ruinTile = (i, j, hash) => ruinIndex(ruinRow(j), ruinSymbol(i, hash), ruinSymbol(i + 1, hash));

/**
 * C on the cell grid (raised ruin floor, and quarters of cells that cannot blend): the cell's tile is
 * half a tile up and left of the display grid, so its row phase is (32·y − 16) mod 11: the courses of a
 * cell's tile continue into the display tiles around it.
 * @param {number} x @param {number} y @param {(a: number, b: number) => number} hash
 */
export const ruinCellTile = (x, y, hash) => ruinIndex((((10 * y + 6) % 11) + 11) % 11, ruinSymbol(x, hash), ruinSymbol(x + 1, hash));

/** The mask of terrain t on display tile (i, j): its corners whose ground is land of priority ≥ t's. @param {string} t @param {number} i @param {number} j @param {(x: number, y: number) => string | null} classAt */
export function maskOf(t, i, j, classAt) {
  const r = PRIORITY.indexOf(t);
  let m = 0;
  for (const [dx, dy, bit] of CORNERS) {
    const c = classAt(i + dx, j + dy);
    if (c && PRIORITY.indexOf(c) >= r && PRIORITY.indexOf(c) >= 0) m |= bit;
  }
  return m;
}

/** The sides of a display tile a mask's border crosses, in the order N, E, S, W (transitions.crossing_sides). @param {number} m @returns {('N' | 'E' | 'S' | 'W')[]} */
export function crossingSides(m) {
  const [nw, ne, sw, se] = [1, 2, 4, 8].map((b) => (m & b) !== 0);
  return /** @type {('N' | 'E' | 'S' | 'W')[]} */ (['N', 'E', 'S', 'W'].filter((_, k) => [nw !== ne, ne !== se, sw !== se, nw !== sw][k]));
}

/** A side of display tile (i, j): its edge's hash arguments, its two end cells, the display tile across it. */
const SIDE = Object.freeze({
  N: (/** @type {number} */ i, /** @type {number} */ j) => ({ h: [2 * i + 1, 2 * j], ends: [[i, j], [i + 1, j]], across: [i, j - 1] }),
  E: (/** @type {number} */ i, /** @type {number} */ j) => ({ h: [2 * i + 2, 2 * j + 1], ends: [[i + 1, j], [i + 1, j + 1]], across: [i + 1, j] }),
  S: (/** @type {number} */ i, /** @type {number} */ j) => ({ h: [2 * i + 1, 2 * j + 2], ends: [[i, j + 1], [i + 1, j + 1]], across: [i, j + 1] }),
  W: (/** @type {number} */ i, /** @type {number} */ j) => ({ h: [2 * i, 2 * j + 1], ends: [[i, j], [i, j + 1]], across: [i - 1, j] }),
});

/**
 * The variant of terrain t's edge overlay (mask m) on display tile (i, j) (NAMES.md 2, step 3; round 7,
 * render_ref.edge_variant): the ruin floor its row phase; masks 6 / 9 hash(i + 7, j) % 2; else
 * sA + 2·sB over the 2 sides the border crosses (N, E, S, W order), a side's state being
 * (its edge's hash >> 4) & 1, or 0 when one of its end cells is water or the display tile across it
 * (or this one) has mask 6 / 9 for t — so the tiles on both sides of a side agree.
 * @param {string} t @param {number} m @param {number} i @param {number} j @param {Hash} hash
 * @param {(x: number, y: number) => string | null} classAt a cell's ground class (clamped to the map, as the display grid's corners)
 */
export function edgeVariantOf(t, m, i, j, hash, classAt) {
  if (t === 'ruin') return ruinRow(j);
  if (m === 6 || m === 9) return hash(i + 7, j) % 2;
  const state = (/** @type {'N' | 'E' | 'S' | 'W'} */ sd) => {
    const { h, ends, across } = SIDE[sd](i, j);
    if (ends.some(([x, y]) => classAt(x, y) === 'water')) return 0;
    const ma = maskOf(t, across[0], across[1], classAt);
    if (ma === 6 || ma === 9 || maskOf(t, i, j, classAt) === 6 || maskOf(t, i, j, classAt) === 9) return 0;
    return (hash(h[0], h[1]) >>> 4) & 1;
  };
  const [a, b] = crossingSides(m);
  return state(a) + 2 * state(b);
}

// --- A: picture placement (NAMES.md section 1 A, steps 1-5; render_ref.macro_blocks) ---
// The one place the rule lives: macroPlacement and the helpers below it. hash values are unsigned 32-bit.

/** A step 3: the offsets 0 / 1 / 2 of a picture in its block, by hash % 6 (chances 1/3, 1/6, 1/2). */
const OFF = Object.freeze([0, 0, 1, 2, 2, 2]);
/** A step 2: blocks per cell of the density noise. */
const NOISE_CELL = 4;

/** A step 3: the raw offsets of block (a, b). @param {number} a @param {number} b @param {Hash} hash @returns {[number, number]} */
export function rawOffsets(a, b, hash) {
  const h = hash(a, b);
  return [OFF[h % 6], OFF[(h >>> 8) % 6]];
}

/** A step 3: the offsets of block (a, b), an offset 2 taken back to 1 where it would meet the next block's picture. @param {number} a @param {number} b @param {Hash} hash @returns {[number, number]} */
export function blockOffsets(a, b, hash) {
  let [ox, oy] = rawOffsets(a, b, hash);
  if (ox === 2 && rawOffsets(a + 1, b, hash)[0] === 0) ox = 1;
  if (oy === 2 && rawOffsets(a, b + 1, hash)[1] === 0) oy = 1;
  if (ox === 2 && oy === 2) {
    const [rx, ry] = rawOffsets(a + 1, b + 1, hash);
    if (rx === 0 && ry === 0) oy = 1;
  }
  if (ox === 2 && oy === 0) {
    const [rx, ry] = rawOffsets(a + 1, b - 1, hash);
    if (rx === 0 && ry === 2) ox = 1;
  }
  return [ox, oy];
}

/** A step 2: the density noise of block (a, b), 0..1 (value noise on a lattice of 4 blocks, smoothstep-blended). @param {number} a @param {number} b @param {Hash} hash */
export const blockDensity = (a, b, hash) => smoothNoise(a, b, NOISE_CELL, 5003, 7919, hash);

/** A step 2: whether block (a, b) has a picture: ((h >> 16) % 1024) / 1024 >= pNone. @param {number} a @param {number} b @param {Hash} hash */
export function blockHasPicture(a, b, hash) {
  const pNone = Math.min(1, Math.max(0, 2 * (blockDensity(a, b, hash) - 0.3)));
  return ((hash(a, b) >>> 16) % 1024) / 1024 >= pNone;
}

/**
 * A step 4 (round 6): the picture number (0-7) of block (a, b): no block shares it with any of its 8
 * neighbours where it can be helped. Classes by (a % 2, b % 2) as the calm tiles (avoided): A its raw
 * number hash(a + 409, b + 1031) % 8; B, C, D the k-th number none of their avoided neighbours has
 * (D: if none is left, only its 4 side neighbours), k = floor(hash(a + 409, b + 1031) / 8).
 * @param {number} a @param {number} b @param {Hash} hash @param {Map<number, number>} [memo] keyed by calmKey
 */
export function blockPicture(a, b, hash, memo = new Map()) {
  const key = calmKey(a, b);
  const known = memo.get(key);
  if (known !== undefined) return known;
  const h = hash(a + 409, b + 1031);
  let m = h % 8;
  const nb = avoided(a, b);
  if (nb.length) {
    const freeOf = (/** @type {[number, number][]} */ list) => {
      const taken = new Set(list.map(([x, y]) => blockPicture(x, y, hash, memo)));
      return [0, 1, 2, 3, 4, 5, 6, 7].filter((k) => !taken.has(k));
    };
    let free = freeOf(nb);
    if (!free.length) free = freeOf([[a - 1, b], [a + 1, b], [a, b - 1], [a, b + 1]]);
    m = free[Math.floor(h / 8) % free.length];
  }
  memo.set(key, m);
  return m;
}

/**
 * A step 4b (round 8): the desert's dune of block (a, b), 1-6, or 0: one dune block per cell of 4 × 3
 * blocks, its shape from the cell's place in a 3 × 2 pattern of cells, turned by a hash per pattern.
 * @param {number} a @param {number} b @param {Hash} hash
 */
export function blockDune(a, b, hash) {
  const sa = Math.floor(a / 4);
  const sb = Math.floor(b / 3);
  const hs = hash(sa + 77, sb + 31);
  if (a !== 4 * sa + (hs % 4) || b !== 3 * sb + ((hs >>> 2) % 3)) return 0;
  return 1 + ((pmod(sa, 3) + 3 * pmod(sb, 2) + hash(Math.floor(sa / 3) + 13, Math.floor(sb / 2) + 29)) % 6);
}

/**
 * A: the picture piece of display tile (i, j), or null (NAMES.md section 1 A). A picture of block
 * (a, b ≥ 0) has its NW tile at (3a + ox, 3b + oy), ox / oy 0-2 (blockOffsets), so tile (i, j) can hold
 * the picture of its own block or of the block left of / above / left-above it (offset 2); pictures
 * never overlap. Drawn when it stays on the map (i0 + 2 < width, j0 + 2 < height), the 9 map cells
 * under it (i0 … i0+2, j0 … j0+2) are one flat ground with pictures (MACRO_GROUNDS; flat: one height,
 * round 8 step 5), and the block has one (blockHasPicture) — or, on desert sand, is its cell's dune
 * block (blockDune, step 4b: "dune<k>" instead of the picture). Its 4 display tiles are "<name>.<q>", q = 0 NW, 1 NE, 2 SW, 3 SE.
 * @param {number} i @param {number} j
 * @param {{ uniformBlock: (i: number, j: number, k: number) => string | null, hash: Hash, width: number, height: number, pictures?: Map<number, number> }} ctx
 *   uniformBlock(i, j, k): the one flat land ground of the (k+1)×(k+1) cells from (i, j), or null; width / height: the map's, in cells;
 *   pictures: a memo of the blocks' picture numbers (blockPicture)
 * @returns {{ name: string, block: string } | null} name: "<picture>.<q>"; block: the picture's NW tile "i0,j0"
 */
export function macroPlacement(i, j, { uniformBlock, hash, width, height, pictures }) {
  const A = Math.floor(i / 3);
  const B = Math.floor(j / 3);
  for (const [a, b] of [[A, B], [A - 1, B], [A, B - 1], [A - 1, B - 1]]) {
    if (a < 0 || b < 0) continue;
    const [ox, oy] = blockOffsets(a, b, hash);
    const i0 = 3 * a + ox;
    const j0 = 3 * b + oy;
    if (i < i0 || i > i0 + 1 || j < j0 || j > j0 + 1) continue;
    if (i0 + 2 >= width || j0 + 2 >= height) continue;
    const g = uniformBlock(i0, j0, 2);
    if (g === null || !MACRO_GROUNDS.includes(g)) continue;
    // step 4b: the desert's dune block shows its dune, picture or not
    const dune = g === 'dsand' ? blockDune(a, b, hash) : 0;
    if (!dune && !blockHasPicture(a, b, hash)) continue;
    const name = dune ? `dune${dune}` : MACRO_NAMES[blockPicture(a, b, hash, pictures)];
    return { name: `${name}.${i - i0 + (j - j0) * 2}`, block: `${i0},${j0}` };
  }
  return null;
}
