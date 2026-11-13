// @ts-check
// gfx v2 integration (start-up): the v2 ground's per-map tables, worked out off the main thread
// (deepWorker.js) while the title shows, so that the first chunks are built without them on the main
// thread. Only what does not change in play is tabled: the calm tiles' numbers (groundV2.calmNumber:
// the hash alone) and the picture pieces' places (groundV2.macroPlacement: the view keeps them for the
// map once worked out; pictures go on flat land only, which no vine — the one change of the ground in
// play, over water — makes or unmakes). The same functions as the view's (groundClassOf, uniformBlockOf
// are the view's own), so the tables hold the very values it would work out (tests/unit/groundTables.test.js).
import { Ground, Shape, inBounds } from '../game/world/tilemap.js';
import { regionAt } from '../game/world/world.js';
import { calmNumber, groundClass, macroPlacement } from './groundV2.js';

/**
 * A cell's ground class for the dual grid (null: drawn on the cell grid). The view's groundClassAt.
 * @param {{ width: number, ground: ArrayLike<number> }} map @param {any[]} regions @param {Set<number>} sandUnderTrees @param {number} x @param {number} y
 */
export function groundClassOf(map, regions, sandUnderTrees, x, y) {
  const i = y * map.width + x;
  const g = sandUnderTrees.has(i) ? Ground.SAND : map.ground[i];
  const name = g === Ground.GRASS ? 'grass' : g === Ground.SAND ? 'sand' : g === Ground.PATH ? 'path' : g === Ground.RUIN ? 'ruin' : g === Ground.WATER ? 'water' : 'other';
  return groundClass(name, regionAt(regions, x, y)?.id);
}

/**
 * The one flat land ground of the (k+1)×(k+1) cells from (i, j), or null. The view's uniformBlock.
 * @param {any} map @param {(x: number, y: number) => string | null} classAt @param {number} i @param {number} j @param {number} k
 */
export function uniformBlockOf(map, classAt, i, j, k) {
  let g = /** @type {string | null} */ (null);
  for (let dy = 0; dy <= k; dy++) {
    for (let dx = 0; dx <= k; dx++) {
      const x = i + dx;
      const y = j + dy;
      if (!inBounds(map, x, y) || map.elev[y * map.width + x] !== 0 || map.shape[y * map.width + x] === Shape.RAMP_N) return null;
      const c = classAt(x, y);
      if (!c || c === 'water' || (g && c !== g)) return null;
      g = c;
    }
  }
  return g;
}

/**
 * The cells of desert grass under a tree, drawn as sand with the release terrain (the view's sandUnderTrees).
 * @param {any} map @param {any[]} regions @returns {Set<number>}
 */
export const sandUnderTreesOf = (map, regions) =>
  new Set(
    (map.objects ?? [])
      .filter((/** @type {any} */ o) => o.type === 'tree' && map.ground[o.ty * map.width + o.tx] === Ground.GRASS && regionAt(regions, o.tx, o.ty)?.id === 'desert')
      .map((/** @type {any} */ o) => o.ty * map.width + o.tx),
  );

/**
 * The tables over the display grid (i from -1 to width-1, j from -1 to height-1; a cell (x, y) of the
 * map uses the same numbers), k = (j + 1) * (width + 1) + (i + 1): calm[k] the calm number; the picture
 * piece, or none: names[name[k]] and the picture's NW tile (bi[k], bj[k]), name[k] = -1 for none (typed
 * arrays: handed over from the worker without a copy; macroOf reads one).
 * @param {any} map parsed (tilemap.parseMap) @param {any[]} regions @param {(a: number, b: number) => number} hash
 * @returns {GroundTables}
 */
export function groundTablesOf(map, regions, hash) {
  const W = map.width + 1;
  const H = map.height + 1;
  const sand = sandUnderTreesOf(map, regions);
  const classAt = (/** @type {number} */ x, /** @type {number} */ y) => groundClassOf(map, regions, sand, x, y);
  const calm = new Uint8Array(W * H);
  const name = new Int16Array(W * H).fill(-1);
  const bi = new Int16Array(W * H);
  const bj = new Int16Array(W * H);
  /** @type {string[]} */
  const names = [];
  const memo = new Map();
  const pictures = new Map();
  const ctx = { uniformBlock: (/** @type {number} */ a, /** @type {number} */ b, /** @type {number} */ k) => uniformBlockOf(map, classAt, a, b, k), hash, width: map.width, height: map.height, pictures };
  for (let j = -1; j < map.height; j++) {
    for (let i = -1; i < map.width; i++) {
      const k = (j + 1) * W + (i + 1);
      calm[k] = calmNumber(i, j, hash, memo);
      const m = macroPlacement(i, j, ctx);
      if (m) {
        let n = names.indexOf(m.name);
        if (n < 0) n = names.push(m.name) - 1;
        name[k] = n;
        const [a, b] = m.block.split(',').map(Number);
        bi[k] = a;
        bj[k] = b;
      }
    }
  }
  return { width: map.width, height: map.height, calm, name, bi, bj, names };
}

/** @typedef {{ width: number, height: number, calm: Uint8Array, name: Int16Array, bi: Int16Array, bj: Int16Array, names: string[] }} GroundTables */

/** The picture piece at index k of the tables (macroPlacement's result), or null. @param {GroundTables} t @param {number} k */
export const macroOf = (t, k) => (t.name[k] < 0 ? null : { name: t.names[t.name[k]], block: `${t.bi[k]},${t.bj[k]}` });

/** The index of display tile / cell (i, j) in the tables, or -1 outside. @param {{ width: number, height: number }} t @param {number} i @param {number} j */
export const tableIndex = (t, i, j) => (i < -1 || j < -1 || i >= t.width || j >= t.height ? -1 : (j + 1) * (t.width + 1) + (i + 1));
