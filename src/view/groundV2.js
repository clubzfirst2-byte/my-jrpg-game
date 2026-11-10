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
 * @typedef {{ key: string, anim: boolean }} Layer
 *   anim: an animated water key without its frame ("<key>.<f>" is drawn, f = 0..3)
 */

/**
 * The layers of one display tile (bottom first).
 * @param {{ cls: string[], deep: boolean[], waterVariant: number, edgeVariant: (cls: string) => number,
 *   pick: (cls: string) => string, macro: () => string | null }} t
 *   cls / deep: the 4 corners (NW, NE, SW, SE); pick = the base name for a full land tile (a variant);
 *   edgeVariant = the variant of a land's edge overlay (0 / 1; the ruin floor: its row phase);
 *   macro = a macro piece name ("macro.<q>") when the 4 corners are one land and the block is chosen
 * @returns {Layer[]}
 */
export function displayLayers({ cls, deep, waterVariant, edgeVariant, pick, macro }) {
  /** @type {Layer[]} */
  const out = [];
  const land = cls.filter((c) => c !== 'water');
  const rank = (/** @type {string} */ c) => PRIORITY.indexOf(c);
  let lowest = null;
  if (land.length < 4) {
    const allDeep = cls.every((c, k) => c === 'water' && deep[k]);
    const v = waterVariant ? '.v1' : '';
    out.push({ key: `tile.water${allDeep ? '.deep' : ''}${v}`, anim: true });
    const deepMask = cls.reduce((m, c, k) => (c === 'water' && deep[k] ? m | CORNERS[k][2] : m), 0);
    if (deepMask && !allDeep) out.push({ key: `tile.water.deep.edge.${deepMask}`, anim: true });
    const landMask = cls.reduce((m, c, k) => (c !== 'water' ? m | CORNERS[k][2] : m), 0);
    if (landMask) out.push({ key: `tile.water.foam.${landMask}`, anim: true });
  } else {
    lowest = land.reduce((a, b) => (rank(b) < rank(a) ? b : a));
    const name = (new Set(cls).size === 1 ? macro() : null) ?? pick(lowest);
    out.push({ key: landKey(lowest, name), anim: false });
  }
  for (const t of [...new Set(land)].sort((a, b) => rank(a) - rank(b))) {
    if (t === lowest) continue;
    const mask = cls.reduce((m, c, k) => (c !== 'water' && rank(c) >= rank(t) ? m | CORNERS[k][2] : m), 0);
    out.push({ key: mask === 15 ? landKey(t, '0') : landKey(t, `edge.${mask}.${edgeVariant(t)}`), anim: false });
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

// --- Rounds 2-5 (NAMES.md section 1): the tile of a display tile, picked in one of 2 ways ---
//   A  (round 5) every ground but the ruin floor (island / plains / lake grass, moss, path, mountain snow,
//      island sand, desert sand; and the autumn / winter sets of the 4 seasonal grounds, their season's
//      keys): 8 pictures of 2×2 tiles, at most one per block of 3×3 display tiles (macroPlacement), and
//      elsewhere one of 16 calm tiles by hash (calmTile); nothing crosses their edges
//   C  ruin floor: 66 tiles, stone courses 11 art px high across the whole map: the row phase R of the
//      tile's row and the symbols (0-2) of its column's two edges, n = 6R + 2W + (E if E < W else E - 1);
//      its overlay over water is edge.<mask>.<R>; no pictures

/** The grounds with pictures (A; render_ref.BUSY_MACRO). */
export const MACRO_GROUNDS = Object.freeze(['grass', 'plains', 'lake', 'moss', 'path', 'snow', 'sand', 'dsand']);

/** The names of the 8 pictures: picture m is "macro" (m = 0) or "macro<m+1>". */
export const MACRO_NAMES = Object.freeze(['macro', 'macro2', 'macro3', 'macro4', 'macro5', 'macro6', 'macro7', 'macro8']);

/** How a ground's tiles are picked (the same in every season). @param {string} cls @returns {'A' | 'C'} */
export const tileScheme = (cls) => (cls === 'ruin' ? 'C' : 'A');

/** How many tiles a ground has (names "0" .. count - 1). @param {string} cls */
export const tileCount = (cls) => (tileScheme(cls) === 'C' ? 66 : 16);

/** A: the calm tile of display tile (i, j): hash(i + 3, j + 11) % 16. @param {number} i @param {number} j @param {(a: number, b: number) => number} hash */
export const calmTile = (i, j, hash) => hash(i + 3, j + 11) % 16;

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

/** The variant of a land's edge overlay on display tile (i, j): the ruin's row phase, else 0 / 1. @param {string} cls @param {number} i @param {number} j @param {(a: number, b: number) => number} hash */
export const edgeVariantOf = (cls, i, j, hash) => (cls === 'ruin' ? ruinRow(j) : hash(i + 7, j) % 2);

// --- A: picture placement (NAMES.md section 1 A, steps 1-5; render_ref.macro_blocks) ---
// The one place the rule lives: macroPlacement and the helpers below it. hash values are unsigned 32-bit.

/** A step 3: the offsets 0 / 1 / 2 of a picture in its block, by hash % 6 (chances 1/3, 1/6, 1/2). */
const OFF = Object.freeze([0, 0, 1, 2, 2, 2]);
/** A step 2: blocks per cell of the density noise. */
const NOISE_CELL = 4;

/** @typedef {(a: number, b: number) => number} Hash */

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
export function blockDensity(a, b, hash) {
  const gx = Math.floor(a / NOISE_CELL);
  const gy = Math.floor(b / NOISE_CELL);
  const fx = ((((a % NOISE_CELL) + NOISE_CELL) % NOISE_CELL) + 0.5) / NOISE_CELL;
  const fy = ((((b % NOISE_CELL) + NOISE_CELL) % NOISE_CELL) + 0.5) / NOISE_CELL;
  const v = (/** @type {number} */ x, /** @type {number} */ y) => (hash(x + 5003, y + 7919) % 1024) / 1023;
  const sx = fx * fx * (3 - 2 * fx);
  const sy = fy * fy * (3 - 2 * fy);
  const top = v(gx, gy) + (v(gx + 1, gy) - v(gx, gy)) * sx;
  const bot = v(gx, gy + 1) + (v(gx + 1, gy + 1) - v(gx, gy + 1)) * sx;
  return top + (bot - top) * sy;
}

/** A step 2: whether block (a, b) has a picture: ((h >> 16) % 1024) / 1024 >= pNone. @param {number} a @param {number} b @param {Hash} hash */
export function blockHasPicture(a, b, hash) {
  const pNone = Math.min(1, Math.max(0, 2 * (blockDensity(a, b, hash) - 0.3)));
  return ((hash(a, b) >>> 16) % 1024) / 1024 >= pNone;
}

/** A step 4: the raw picture number of block (a, b). @param {number} a @param {number} b @param {Hash} hash */
const rawPicture = (a, b, hash) => hash(a + 409, b + 1031) % 8;

/** A step 4: the picture number (0-7) of block (a, b); no two side-by-side blocks share one. @param {number} a @param {number} b @param {Hash} hash */
export function blockPicture(a, b, hash) {
  const r = rawPicture(a, b, hash);
  if ((((a + b) % 2) + 2) % 2 === 0) return r;
  const taken = new Set([rawPicture(a - 1, b, hash), rawPicture(a + 1, b, hash), rawPicture(a, b - 1, hash), rawPicture(a, b + 1, hash)]);
  const free = [0, 1, 2, 3, 4, 5, 6, 7].filter((m) => !taken.has(m));
  return free[Math.floor(hash(a + 409, b + 1031) / 8) % free.length];
}

/**
 * A: the picture piece of display tile (i, j), or null (NAMES.md section 1 A). A picture of block
 * (a, b ≥ 0) has its NW tile at (3a + ox, 3b + oy), ox / oy 0-2 (blockOffsets), so tile (i, j) can hold
 * the picture of its own block or of the block left of / above / left-above it (offset 2); pictures
 * never overlap. Drawn when the block has one (blockHasPicture), it stays on the map (i0 + 2 < width,
 * j0 + 2 < height) and the 9 map cells under it (i0 … i0+2, j0 … j0+2) are one flat ground with
 * pictures (MACRO_GROUNDS). Its 4 display tiles are "<name>.<q>", q = 0 NW, 1 NE, 2 SW, 3 SE.
 * @param {number} i @param {number} j
 * @param {{ uniformBlock: (i: number, j: number, k: number) => string | null, hash: Hash, width: number, height: number }} ctx
 *   uniformBlock(i, j, k): the one flat land ground of the (k+1)×(k+1) cells from (i, j), or null; width / height: the map's, in cells
 * @returns {{ name: string, block: string } | null} name: "<picture>.<q>"; block: the picture's NW tile "i0,j0"
 */
export function macroPlacement(i, j, { uniformBlock, hash, width, height }) {
  const A = Math.floor(i / 3);
  const B = Math.floor(j / 3);
  for (const [a, b] of [[A, B], [A - 1, B], [A, B - 1], [A - 1, B - 1]]) {
    if (a < 0 || b < 0) continue;
    const [ox, oy] = blockOffsets(a, b, hash);
    const i0 = 3 * a + ox;
    const j0 = 3 * b + oy;
    if (i < i0 || i > i0 + 1 || j < j0 || j > j0 + 1) continue;
    if (!blockHasPicture(a, b, hash) || i0 + 2 >= width || j0 + 2 >= height) continue;
    const g = uniformBlock(i0, j0, 2);
    if (g === null || !MACRO_GROUNDS.includes(g)) continue;
    return { name: `${MACRO_NAMES[blockPicture(a, b, hash)]}.${i - i0 + (j - j0) * 2}`, block: `${i0},${j0}` };
  }
  return null;
}
