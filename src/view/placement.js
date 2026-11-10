// @ts-check
// W2 (graphics v2, scratchpad gfx_plan.md): the map placement layer, so the world stops looking like a
// grid. Pure and deterministic (no randomness at run time, same look on every load and device):
//   - decorative objects (trees, rocks, brambles, stumps, cacti) are DRAWN a few pixels off their
//     tile's centre, pulled together into loose clusters by a low-frequency noise field, with gaps
//     between them. Only the drawing moves: collision, saves (type@tx,ty) and the map are unchanged.
//   - ground variants are picked in patches (blobs) from noise rather than per tile: the plain
//     variant over most of the ground, the marked ones (flowers, reeds, pebbles...) gathered where the
//     noise is high, each patch leaning to one kind; and 2×2 macro pieces where W1's art provides them.
// Used only with the release terrain; ?placement=0 shows the old per-tile placement (comparison).

/** Object types placed decoratively (drawn off-centre). Never puzzle parts, chests, houses, furniture. */
export const DECOR_TYPES = Object.freeze(['tree', 'rock', 'bramble', 'stump', 'cactus']);

/**
 * The draw offset range from the tile centre / foot line, in game px (a tile is 16): x within ±4,
 * y within -3..0 — never below the tile's own foot line, so an object still sorts exactly by its tile
 * (raised rows in front stay in front, and the player, whose feet can never be inside a solid tile,
 * is drawn in front of anything on the tile north of him).
 */
export const MAX_OFFSET = Object.freeze({ x: 4, up: 3 });

/** Integer hash of a lattice point and a seed → [0, 1). @param {number} x @param {number} y @param {number} seed */
export function hash01(x, y, seed) {
  let h = (Math.imul(x | 0, 374761393) + Math.imul(y | 0, 668265263) + Math.imul(seed | 0, 2147483647)) >>> 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177) >>> 0;
  h = (h ^ (h >>> 16)) >>> 0;
  return h / 4294967296;
}

const smooth = (/** @type {number} */ t) => t * t * (3 - 2 * t);

/**
 * Smooth value noise in [0, 1): random values on a lattice of `scale` tiles, blended between them.
 * @param {number} x @param {number} y tile coordinates @param {number} scale lattice spacing in tiles @param {number} seed
 */
export function valueNoise(x, y, scale, seed) {
  const fx = x / scale;
  const fy = y / scale;
  const x0 = Math.floor(fx);
  const y0 = Math.floor(fy);
  const tx = smooth(fx - x0);
  const ty = smooth(fy - y0);
  const a = hash01(x0, y0, seed);
  const b = hash01(x0 + 1, y0, seed);
  const c = hash01(x0, y0 + 1, seed);
  const d = hash01(x0 + 1, y0 + 1, seed);
  return (a + (b - a) * tx) * (1 - ty) + (c + (d - c) * tx) * ty;
}

/** Two octaves (large blobs with ragged edges), in [0, 1). @param {number} x @param {number} y @param {number} scale @param {number} seed */
export function patchNoise(x, y, scale, seed) {
  return valueNoise(x, y, scale, seed) * 0.7 + valueNoise(x, y, scale / 2.5, seed + 17) * 0.3;
}

const SEED_CLUSTER = 101;
const SEED_JITTER = 202;
const SEED_PATCH = 303;
const SEED_KIND = 404;
const SEED_PICK = 505;
const SEED_MACRO = 606;
/** Clusters of decorative objects: blobs of about this many tiles. */
const CLUSTER_SCALE = 6;

/**
 * Where a decorative object is drawn relative to its tile centre, in whole game px: a small jitter,
 * plus a pull towards the denser side of the cluster field (objects gather into clumps; between
 * clumps the spacing opens up). Bounded by MAX_OFFSET.
 * @param {number} tx @param {number} ty
 * @returns {[number, number]}
 */
export function decorOffset(tx, ty) {
  const e = 0.5;
  const gx = patchNoise(tx + e, ty, CLUSTER_SCALE, SEED_CLUSTER) - patchNoise(tx - e, ty, CLUSTER_SCALE, SEED_CLUSTER);
  const gy = patchNoise(tx, ty + e, CLUSTER_SCALE, SEED_CLUSTER) - patchNoise(tx, ty - e, CLUSTER_SCALE, SEED_CLUSTER);
  const len = Math.hypot(gx, gy) || 1;
  // pull: up to 3 px towards the higher field, stronger where the field slopes most
  const k = Math.min(1, len * 6) * 3;
  const jx = (hash01(tx, ty, SEED_JITTER) - 0.5) * 4;
  const jy = (hash01(tx, ty, SEED_JITTER + 1) - 0.5) * 3;
  const dx = Math.max(-MAX_OFFSET.x, Math.min(MAX_OFFSET.x, Math.round((gx / len) * k + jx)));
  // y: the same pull and jitter, folded into -3..0 (only ever up from the foot line)
  const dy = Math.max(-MAX_OFFSET.up, Math.min(0, Math.round(((gy / len) * k + jy) / 2 - MAX_OFFSET.up / 2)));
  return [dx === 0 ? 0 : dx, dy === 0 ? 0 : dy];
}

/**
 * The ground variant of a tile, in patches: variant 0 (the plain one) over most of the ground; the
 * marked variants gathered where a patch field is high (about 60 % of the tiles in the middle of a
 * patch, about 4 % between patches), each patch leaning to one variant. About half the ground or more
 * stays plain (guide 3.3: variant 0 is the quietest and the most common). n = the variants available.
 * @param {number} tx @param {number} ty @param {number} n
 */
export function patchVariant(tx, ty, n) {
  if (n <= 1) return 0;
  const m = patchNoise(tx, ty, 7, SEED_PATCH);
  const t = Math.max(0, Math.min(1, (m - 0.5) / 0.25));
  const p = 0.04 + smooth(t) * 0.56;
  if (hash01(tx, ty, SEED_PICK) >= p) return 0;
  // the patch's kind, from a slower field, with a quarter of the tiles taking another marked variant
  const kind = Math.min(n - 2, Math.floor(valueNoise(tx, ty, 11, SEED_KIND) * (n - 1)));
  if (hash01(tx, ty, SEED_PICK + 1) < 0.25) return 1 + Math.floor(hash01(tx, ty, SEED_PICK + 2) * (n - 1));
  return 1 + kind;
}

/**
 * 2×2 macro pieces (for W1's art: "<ground>.macro.<q>", q = 0 nw, 1 ne, 2 sw, 3 se): the quarter a
 * tile takes in its 2×2 block when that block is chosen for a macro piece (about 1 block in 9, in the
 * plainer parts of the patch field), else -1. The view uses it only where the art exists and the 4
 * tiles show the same ground.
 * @param {number} tx @param {number} ty
 */
export function macroQuarter(tx, ty) {
  const bx = Math.floor(tx / 2);
  const by = Math.floor(ty / 2);
  if (patchNoise(bx * 2 + 1, by * 2 + 1, 7, SEED_PATCH) > 0.55) return -1;
  if (hash01(bx, by, SEED_MACRO) >= 0.16) return -1;
  return (tx - bx * 2) + (ty - by * 2) * 2;
}

/**
 * Whether the placement layer is on. ?placement=0 turns it off, to compare; ?v2=0 (every graphics v2
 * change back to the approved look) turns it off too, unless ?placement=1 asks for it.
 */
export function placementEnabled(search = globalThis.location?.search ?? '') {
  const q = new URLSearchParams(search);
  const p = q.get('placement');
  if (p === '0' || p === '1') return p === '1';
  return q.get('v2') !== '0';
}
