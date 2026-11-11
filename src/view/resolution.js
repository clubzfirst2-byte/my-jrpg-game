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

/**
 * How the canvas is scaled to the screen (?scale=, render_audit.md, gfx_plan.md 2026-11-11).
 * - 'fit' (default until the director decides): today's behaviour. Every game pixel is a whole number of
 *   device pixels, but a canvas (art) pixel may be x.5 device pixels (2.5 on iPhone 15 Pro, 1.5 on SE),
 *   so art pixels alternate 2 and 3 (1 and 2) device pixels.
 * - 'int': the device scale is a multiple of every art density in use, so every canvas pixel and every art
 *   pixel is a whole number of device pixels (3 on 15 Pro, 2 on SE). The view area changes instead
 *   (about 27×12 tiles on 15 Pro, 21×12 on SE). The canvas covers the screen to the device pixel; any
 *   remainder (< 1 canvas pixel) is cropped on whole device pixels, never left as a border.
 */
export const SCALE_MODES = /** @type {const} */ (['fit', 'int']);
/** @typedef {typeof SCALE_MODES[number]} ScaleMode */
/** @type {ScaleMode} */
export const DEFAULT_SCALE_MODE = 'fit';

/** @param {string | null | undefined} value  @returns {ScaleMode} */
export function parseScaleMode(value) {
  return value === 'int' ? 'int' : DEFAULT_SCALE_MODE;
}

/** @param {number} a @param {number} b */
function gcd(a, b) {
  while (b) [a, b] = [b, a % b];
  return a;
}

/**
 * Smallest device scale step that keeps every density whole: lcm of the densities.
 * @param {readonly number[]} densities  pixels per game pixel (canvas density, art densities)
 */
export function crispUnit(densities) {
  let u = 1;
  for (const d of densities) {
    const n = Math.max(1, Math.round(d));
    u = (u * n) / gcd(u, n);
  }
  return u;
}

/**
 * 'int' mode: device pixels per game pixel. A multiple of `unit` (so canvas and art pixels are whole
 * device pixels), chosen so the visible short side is as close as possible to `targetHeight`
 * game px (ties go to the larger scale, i.e. the closer view). Never below `unit`.
 * @param {number} shortSide device pixels on the shorter side
 * @param {number} targetHeight game pixels
 * @param {number} unit
 */
export function chooseIntScale(shortSide, targetHeight, unit) {
  const k = Math.max(1, Math.round(shortSide / (targetHeight * unit)));
  return k * unit;
}

/**
 * Like computeResolution, with the scale mode and the art densities kept apart from the canvas density.
 * @param {number} cssWidth
 * @param {number} cssHeight
 * @param {number} dpr
 * @param {number} targetHeight game pixels across the shorter side
 * @param {{ mode?: ScaleMode, canvasDensity?: number, artDensities?: readonly number[] }} [options]
 *   canvasDensity: canvas pixels per game pixel (the camera zoom; 2 with the release art).
 *   artDensities: art pixels per game pixel of every art set on screen (default: [canvasDensity]).
 *     A future 2× art set (density 4) is listed here; in 'int' mode the device scale then becomes
 *     a multiple of 4 as well, so its pixels stay whole too. The texture density never changes the
 *     visible area in 'fit' mode.
 */
export function computeView(cssWidth, cssHeight, dpr, targetHeight, options = {}) {
  const mode = options.mode ?? DEFAULT_SCALE_MODE;
  const canvasDensity = options.canvasDensity ?? 1;
  if (mode !== 'int') {
    const r = computeResolution(cssWidth, cssHeight, dpr, targetHeight, canvasDensity);
    const artDensities = options.artDensities ?? [canvasDensity];
    return {
      ...r,
      mode: /** @type {ScaleMode} */ ('fit'),
      artDensities: [...artDensities],
      artPixel: artDensities.map((d) => r.scale / d),
      gameWidth: r.width / canvasDensity,
      tilesX: r.width / canvasDensity / 16,
      tilesY: r.height / canvasDensity / 16,
      /** null: centred with translate(-50%, -50%) as before (unchanged 'fit' behaviour). */
      cssLeft: /** @type {number | null} */ (null),
      cssTop: /** @type {number | null} */ (null),
    };
  }
  const artDensities = options.artDensities ?? [canvasDensity];
  const deviceW = Math.max(1, Math.round(cssWidth * dpr));
  const deviceH = Math.max(1, Math.round(cssHeight * dpr));
  const unit = crispUnit([canvasDensity, ...artDensities]);
  const scale = chooseIntScale(Math.min(deviceW, deviceH), targetHeight, unit);
  const canvasScale = scale / canvasDensity; // whole number: unit is a multiple of canvasDensity
  // Cover the screen in whole canvas pixels; the overshoot (< canvasScale device px) is cropped
  // evenly, on whole device pixels.
  const width = Math.ceil(deviceW / canvasScale);
  const height = Math.ceil(deviceH / canvasScale);
  const overX = width * canvasScale - deviceW;
  const overY = height * canvasScale - deviceH;
  const gameWidth = width / canvasDensity;
  const gameHeightFull = height / canvasDensity;
  return {
    mode: /** @type {ScaleMode} */ ('int'),
    width,
    height,
    scale,
    canvasScale,
    artDensity: canvasDensity,
    artDensities: [...artDensities],
    /** Device pixels per art pixel, per art density (all whole numbers). */
    artPixel: artDensities.map((d) => scale / d),
    gameWidth,
    gameHeight: Math.min(gameWidth, gameHeightFull),
    /** Visible tiles (16 game px) across and down. */
    tilesX: gameWidth / 16,
    tilesY: gameHeightFull / 16,
    cssCanvasWidth: (width * canvasScale) / dpr,
    cssCanvasHeight: (height * canvasScale) / dpr,
    /** Canvas top-left in CSS px, on a whole device pixel (no translate(-50%) half-pixel shift). */
    cssLeft: -Math.floor(overX / 2) / dpr,
    cssTop: -Math.floor(overY / 2) / dpr,
  };
}

/** @param {number} current */
export function nextCandidate(current) {
  const i = RESOLUTION_CANDIDATES.indexOf(/** @type {any} */ (current));
  return RESOLUTION_CANDIDATES[(i + 1) % RESOLUTION_CANDIDATES.length];
}
