// @ts-check

/** @typedef {'down' | 'up' | 'left' | 'right'} Facing */

/**
 * 4-way facing from the dominant axis; keeps the current facing on exact diagonals to avoid flicker.
 * @param {number} x @param {number} y @param {Facing} current
 * @returns {Facing}
 */
export function facingFrom(x, y, current) {
  const ax = Math.abs(x);
  const ay = Math.abs(y);
  if (ax === 0 && ay === 0) return current;
  if (Math.abs(ax - ay) < 1e-3) {
    const h = x > 0 ? 'right' : 'left';
    const v = y > 0 ? 'down' : 'up';
    return current === h || current === v ? current : v;
  }
  if (ax > ay) return x > 0 ? 'right' : 'left';
  return y > 0 ? 'down' : 'up';
}
