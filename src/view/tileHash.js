// @ts-check
// Stable per-tile variation (gameView.js; shared with the deep-water worker, deepWorker.js). Pure.

/** @param {number} x @param {number} y */
export function hash(x, y) {
  let h = (x * 374761393 + y * 668265263) >>> 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177) >>> 0;
  return (h ^ (h >>> 16)) >>> 0;
}
