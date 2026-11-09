// @ts-check
// Internal resolution with integer scaling (DESIGN.md 2.1). No PixiJS import: unit-testable.

/** The three candidates compared in P1 (target internal height in game pixels). */
export const RESOLUTION_CANDIDATES = /** @type {const} */ ([180, 216, 270]);
export const DEFAULT_TARGET_HEIGHT = 216;

/**
 * Computes the internal render size for a viewport.
 * - Every game pixel becomes exactly `scale` x `scale` device pixels (crisp, even game pixels).
 * - `scale` is chosen so the visible height in game pixels is as close as possible to the target.
 *   It does not depend on `artDensity`, so the release (HD) art shows exactly the same part of the
 *   world as the placeholder art (docs/perf/hd-view-size.md).
 * - The internal size is then grown to cover the whole viewport (no black bars). The overshoot is
 *   less than one game pixel and is cropped evenly at the edges.
 * @param {number} cssWidth   viewport width in CSS px
 * @param {number} cssHeight  viewport height in CSS px
 * @param {number} dpr        devicePixelRatio
 * @param {number} targetHeight
 * @param {number} [artDensity] P11.5: art pixels per game pixel (2 for the real art in src/art:
 *   tiles 32×32, characters 32×56). The canvas then has that many pixels per game pixel and the
 *   camera zooms by the same factor, so the finer art keeps every pixel. `targetHeight` stays in
 *   game pixels. One canvas pixel covers `scale / artDensity` device pixels: an integer when `scale`
 *   is even; when it is odd (e.g. 5) art pixels alternate 2 and 3 device pixels. Game pixels land
 *   exactly on `scale` device pixels when they sit on whole game px, so main.js then snaps the
 *   camera to whole game px (Camera.snapStep). If `scale < artDensity` (very small window at DPR 1)
 *   `canvasScale` is 0.5: the canvas is drawn larger than the screen and shrunk (art pixels are
 *   dropped); this does not happen on iPhones.
 */
export function computeResolution(cssWidth, cssHeight, dpr, targetHeight, artDensity = 1) {
  const deviceW = Math.max(1, Math.round(cssWidth * dpr));
  const deviceH = Math.max(1, Math.round(cssHeight * dpr));
  // Base the scale on the shorter side so portrait screens still get a sensible zoom.
  const shortSide = Math.min(deviceW, deviceH);
  const scale = Math.max(1, Math.round(shortSide / targetHeight));
  // Visible size in game pixels (covers the viewport; overshoot < 1 game px).
  const gameW = Math.ceil(deviceW / scale);
  const gameH = Math.ceil(deviceH / scale);
  const width = gameW * artDensity;
  const height = gameH * artDensity;
  return {
    width,
    height,
    /** Device pixels per game pixel (always an integer). */
    scale,
    /** Device pixels per canvas pixel (`scale / artDensity`; may be x.5 with HD art). */
    canvasScale: scale / artDensity,
    artDensity,
    /** Game pixels visible across the shorter side (what `targetHeight` aims for). */
    gameHeight: Math.min(gameW, gameH),
    /** Canvas size in CSS px (may exceed the viewport by < 1 game pixel). */
    cssCanvasWidth: (gameW * scale) / dpr,
    cssCanvasHeight: (gameH * scale) / dpr,
  };
}

/** @param {number} current */
export function nextCandidate(current) {
  const i = RESOLUTION_CANDIDATES.indexOf(/** @type {any} */ (current));
  return RESOLUTION_CANDIDATES[(i + 1) % RESOLUTION_CANDIDATES.length];
}
