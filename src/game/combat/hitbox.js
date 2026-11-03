// @ts-check
// Combat geometry on the ground plane plus a height band (DESIGN.md 3.1: feet position + z).

/** Two things can only touch if their heights are this close (px). */
export const Z_REACH = 16;

/**
 * @typedef {{ x: number, y: number, z: number, r: number }} Circle  hit area at the feet / body
 */

/** @param {Circle} a @param {Circle} b */
export function overlaps(a, b) {
  return Math.hypot(a.x - b.x, a.y - b.y) < a.r + b.r && Math.abs(a.z - b.z) < Z_REACH;
}

/**
 * Normalized direction, or the fallback when the vector is (almost) zero.
 * @param {number} x @param {number} y @param {{ x: number, y: number }} fallback
 */
export function direction(x, y, fallback) {
  const len = Math.hypot(x, y);
  return len < 1e-6 ? { ...fallback } : { x: x / len, y: y / len };
}

/** Unit vector for a 4-way facing. @param {'up' | 'down' | 'left' | 'right'} facing */
export function facingVector(facing) {
  switch (facing) {
    case 'up':
      return { x: 0, y: -1 };
    case 'down':
      return { x: 0, y: 1 };
    case 'left':
      return { x: -1, y: 0 };
    default:
      return { x: 1, y: 0 };
  }
}

/**
 * Whether a hit coming from `from` arrives within the defender's front arc (90° each side of `aim`).
 * @param {{ x: number, y: number }} defender @param {{ x: number, y: number }} aim unit vector
 * @param {{ x: number, y: number }} from
 */
export function fromFront(defender, aim, from) {
  const dx = from.x - defender.x;
  const dy = from.y - defender.y;
  return dx * aim.x + dy * aim.y > 0;
}
