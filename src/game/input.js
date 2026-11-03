// @ts-check
// Device-independent input for the logic layer. Touch / keyboard / gamepad are converted
// into this shape by src/platform (DESIGN.md 1.1).

/**
 * @typedef {object} InputFrame
 * @property {number} moveX  -1..1 (analog)
 * @property {number} moveY  -1..1 (analog, +down)
 * @property {boolean} dash
 */

/** @returns {InputFrame} */
export function emptyInput() {
  return { moveX: 0, moveY: 0, dash: false };
}

/** Analog values below this magnitude are treated as no input. */
export const STICK_DEADZONE = 0.15;

/**
 * Clamps a raw stick vector to the unit circle and applies the dead zone,
 * rescaling so movement starts smoothly just outside it.
 * @param {number} x @param {number} y
 * @returns {{ x: number, y: number }}
 */
export function normalizeStick(x, y) {
  const len = Math.hypot(x, y);
  if (len < STICK_DEADZONE) return { x: 0, y: 0 };
  const clamped = Math.min(len, 1);
  const scaled = (clamped - STICK_DEADZONE) / (1 - STICK_DEADZONE);
  return { x: (x / len) * scaled, y: (y / len) * scaled };
}
