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
 * The key of a land tile: name "0" (the calm base), "1".."7" (variants), "macro.<q>", "edge.<mask>.<v>".
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
 * @param {{ cls: string[], deep: boolean[], waterVariant: number, edgeVariant: number,
 *   pick: (cls: string) => string, macro: () => string | null }} t
 *   cls / deep: the 4 corners (NW, NE, SW, SE); pick = the base name for a full land tile (a variant);
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
    out.push({ key: mask === 15 ? landKey(t, '0') : landKey(t, `edge.${mask}.${edgeVariant}`), anim: false });
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

// --- Round 2 (NAMES.md section 1): edge-matched (Wang) ground tiles and macro blocks ---

/** P(edge type 1) per ground look, in % (render_ref / wang.P_TYPE1); winter grass-like grounds use the snow's. */
export const P_TYPE1 = Object.freeze({ grass: 10, plains: 10, lake: 10, moss: 12, path: 10, snow: 50, sand: 50, dsand: 50, ruin: 50 });

/** Grounds that use macro blocks twice as often (lines / paving grounds: half as often). */
export const BUSY_MACRO = Object.freeze(['grass', 'plains', 'lake', 'moss', 'path']);

/**
 * The ids of the 4 edges of display tile (i, j) and the neighbour across each: N, E, S, W (render_ref).
 * @param {number} i @param {number} j
 * @returns {[number, number, number, number][]} [edgeIdX, edgeIdY, neighbourI, neighbourJ]
 */
export function edgesOf(i, j) {
  return [
    [2 * i + 1, 2 * j, i, j - 1],
    [2 * i + 2, 2 * j + 1, i + 1, j],
    [2 * i + 1, 2 * j + 2, i, j + 1],
    [2 * i, 2 * j + 1, i - 1, j],
  ];
}

/**
 * Edge types per ground look, data-driven so more types are a data change: for the horizontal edges
 * (a tile's top / bottom: N, S) and the vertical ones (left / right: E, W), the weight in % of each
 * type (type 0 first). Round 2: 2 types everywhere, type 1 with P_TYPE1.
 * @type {Readonly<Record<string, { ns: readonly number[], ew: readonly number[] }>>}
 */
export const EDGE_TYPES = Object.freeze(
  Object.fromEntries(Object.entries(P_TYPE1).map(([g, p]) => [g, Object.freeze({ ns: Object.freeze([100 - p, p]), ew: Object.freeze([100 - p, p]) })])),
);

/**
 * The type of an edge from its hash, as render_ref.edge_type: hash % 100 falls in type 1's share
 * first (type 1 when hash % 100 < P), then type 2's, ...; the rest is type 0.
 * @param {string} look @param {'ns' | 'ew'} axis @param {number} h the edge's hash
 */
export function edgeTypeOf(look, axis, h) {
  const w = EDGE_TYPES[look]?.[axis] ?? [100];
  let r = h % 100;
  for (let t = 1; t < w.length; t++) {
    if (r < w[t]) return t;
    r -= w[t];
  }
  return 0;
}

/**
 * The tile index of 4 edge types, mixed radix over the types' counts (N, E, S, W):
 * n = N + kN·(E + kE·(S + kS·W)); with 2 types each, n = N + 2E + 4S + 8W.
 * @param {number[]} types @param {number[]} [counts] types per edge (N, E, S, W)
 */
export const wangIndex = (/** @type {number[]} */ types, /** @type {number[]} */ counts = [2, 2, 2, 2]) => types[0] + counts[0] * (types[1] + counts[1] * (types[2] + counts[2] * types[3]));

/** The type counts of a ground look's 4 edges (N, E, S, W). @param {string} look */
export const edgeCounts = (look) => {
  const t = EDGE_TYPES[look] ?? { ns: [100], ew: [100] };
  return [t.ns.length, t.ew.length, t.ns.length, t.ew.length];
};

/** The look whose P decides a ground's edges (winter grass-like grounds look like snow). @param {string} cls @param {string | null} season */
export const edgeLook = (cls, season) => (season === 'winter' && SEASONAL.includes(cls) ? 'snow' : cls);
