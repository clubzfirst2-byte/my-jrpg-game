// @ts-check
// Order-independent randomness: a hash of integers, so the same inputs always give the same
// number whatever order things are computed in (environment simulation, weather).

/** Deterministic number in [0, 1) from integers. */
export function roll(/** @type {number} */ seed, /** @type {number} */ a, /** @type {number} */ b, /** @type {number} */ c) {
  let h = Math.imul(seed ^ 0x9e3779b9, 0x85ebca6b) >>> 0;
  for (const v of [a, b, c]) {
    h = Math.imul(h ^ (v | 0), 0xcc9e2d51) >>> 0;
    h = ((h << 15) | (h >>> 17)) >>> 0;
    h = Math.imul(h, 0x1b873593) >>> 0;
  }
  h ^= h >>> 16;
  h = Math.imul(h, 0x85ebca6b) >>> 0;
  h ^= h >>> 13;
  return (h >>> 0) / 4294967296;
}
