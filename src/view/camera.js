// @ts-check
// Camera for the 3/4 top-down view (DESIGN.md 3.5). No PixiJS import: unit-testable.
//
// - Follows a target with frame-rate independent exponential smoothing.
// - Never shows outside its bounds (the map, or a room / cave / dungeon area set with setBounds).
// - Zoom is a separate factor (world px -> screen px). Integer zoom keeps pixel art perfectly even.
// - The final origin is snapped to whole screen pixels so pixel art never blurs or shimmers.

/** @typedef {{ x: number, y: number, width: number, height: number }} Rect */

export const CAMERA_DEFAULTS = Object.freeze({
  /** Time for the camera to close ~63% of the distance to the target (seconds). */
  smoothTime: 0.12,
  /** Distances larger than this many view sizes cut instantly (respawn, room change). */
  snapDistanceViews: 1.5,
  zoom: 1,
  minZoom: 1,
  maxZoom: 4,
});

export class Camera {
  /** @param {Partial<typeof CAMERA_DEFAULTS>} [options] */
  constructor(options = {}) {
    const o = { ...CAMERA_DEFAULTS, ...options };
    this.smoothTime = o.smoothTime;
    this.snapDistanceViews = o.snapDistanceViews;
    this.minZoom = o.minZoom;
    this.maxZoom = o.maxZoom;
    this.zoom = clamp(o.zoom, o.minZoom, o.maxZoom);
    /** Center of the view in world px (unsnapped). */
    this.x = 0;
    this.y = 0;
    /** Screen (render target) size in px. */
    this.screenWidth = 1;
    this.screenHeight = 1;
    /** @type {Rect | null} */
    this.bounds = null;
    this.initialized = false;
  }

  /** Size of the visible world area in world px. */
  get viewWidth() {
    return this.screenWidth / this.zoom;
  }

  get viewHeight() {
    return this.screenHeight / this.zoom;
  }

  /** @param {number} width @param {number} height screen size in px */
  setViewport(width, height) {
    this.screenWidth = Math.max(1, width);
    this.screenHeight = Math.max(1, height);
  }

  /**
   * Area the camera may show (the whole map outdoors; a room, cave or dungeon floor indoors).
   * @param {Rect | null} rect
   */
  setBounds(rect) {
    this.bounds = rect;
  }

  /** @param {number} zoom */
  setZoom(zoom) {
    this.zoom = clamp(zoom, this.minZoom, this.maxZoom);
  }

  /** Jumps straight to the target (no smoothing). @param {number} tx @param {number} ty */
  snapTo(tx, ty) {
    this.x = tx;
    this.y = ty;
    this.initialized = true;
  }

  /**
   * Moves toward the target. Frame-rate independent: the same real time gives the same result
   * whether it is split into 60 or 30 frames.
   * @param {number} tx @param {number} ty target in world px
   * @param {number} dt seconds since the previous frame
   */
  follow(tx, ty, dt) {
    const far = this.snapDistanceViews * Math.max(this.viewWidth, this.viewHeight);
    if (!this.initialized || Math.hypot(tx - this.x, ty - this.y) > far) {
      this.snapTo(tx, ty);
      return;
    }
    const k = this.smoothTime <= 0 ? 1 : 1 - Math.exp(-Math.max(0, dt) / this.smoothTime);
    this.x += (tx - this.x) * k;
    this.y += (ty - this.y) * k;
  }

  /**
   * Top-left of the view in world px, clamped to the bounds and snapped to whole screen pixels.
   * @returns {{ x: number, y: number }}
   */
  origin() {
    const vw = this.viewWidth;
    const vh = this.viewHeight;
    let ox = this.x - vw / 2;
    let oy = this.y - vh / 2;
    if (this.bounds) {
      ox = clampAxis(ox, vw, this.bounds.x, this.bounds.width);
      oy = clampAxis(oy, vh, this.bounds.y, this.bounds.height);
    }
    return { x: Math.round(ox * this.zoom) / this.zoom, y: Math.round(oy * this.zoom) / this.zoom };
  }
}

/** @param {number} v @param {number} lo @param {number} hi */
function clamp(v, lo, hi) {
  return Math.min(Math.max(v, lo), hi);
}

/**
 * Keeps [o, o + view] inside [start, start + size]; centers the area when it is smaller than the view.
 * @param {number} o @param {number} view @param {number} start @param {number} size
 */
function clampAxis(o, view, start, size) {
  if (size <= view) return start + (size - view) / 2;
  return clamp(o, start, start + size - view);
}
