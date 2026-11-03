// @ts-check
// Internal resolution with integer scaling (DESIGN.md 2.1). No PixiJS import: unit-testable.

/** The three candidates compared in P1 (target internal height in game pixels). */
export const RESOLUTION_CANDIDATES = /** @type {const} */ ([180, 216, 270]);
export const DEFAULT_TARGET_HEIGHT = 216;

/**
 * Computes the internal render size for a viewport.
 * - Every game pixel becomes exactly `scale` x `scale` device pixels (crisp, even pixels).
 * - `scale` is chosen so the internal height is as close as possible to the target.
 * - The internal size is then grown to cover the whole viewport (no black bars). The overshoot is
 *   less than one game pixel and is cropped evenly at the edges.
 * @param {number} cssWidth   viewport width in CSS px
 * @param {number} cssHeight  viewport height in CSS px
 * @param {number} dpr        devicePixelRatio
 * @param {number} targetHeight
 */
export function computeResolution(cssWidth, cssHeight, dpr, targetHeight) {
  const deviceW = Math.max(1, Math.round(cssWidth * dpr));
  const deviceH = Math.max(1, Math.round(cssHeight * dpr));
  // Base the scale on the shorter side so portrait screens still get a sensible zoom.
  const shortSide = Math.min(deviceW, deviceH);
  const scale = Math.max(1, Math.round(shortSide / targetHeight));
  const width = Math.ceil(deviceW / scale);
  const height = Math.ceil(deviceH / scale);
  return {
    width,
    height,
    scale,
    /** Canvas size in CSS px (may exceed the viewport by < 1 game pixel). */
    cssCanvasWidth: (width * scale) / dpr,
    cssCanvasHeight: (height * scale) / dpr,
  };
}

/** @param {number} current */
export function nextCandidate(current) {
  const i = RESOLUTION_CANDIDATES.indexOf(/** @type {any} */ (current));
  return RESOLUTION_CANDIDATES[(i + 1) % RESOLUTION_CANDIDATES.length];
}
