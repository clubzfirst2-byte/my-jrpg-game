// @ts-check
// Graphics v3 (?v3=1): the flat ground drawn once into a render texture a little larger than the view,
// and that texture drawn each frame (one quad) instead of the hundreds of ground sprites. v3 keeps no
// per-chunk cache (16 MB a chunk at 4 texture px per game px, STYLE.md 10.1 (5)); this one is the size
// of the screen plus a margin (15 Pro 1342×654 px, 3.3 MB; SE 1398×814 px, 4.3 MB) and is drawn again
// only when the view leaves it (the camera moved by the margin), when a chunk comes or goes, or when
// the ground changes (season, water edges). It holds the ground pieces (base, flow, grass edges, the
// v2 ground, water edges): the swaying props, the actors and the water mesh under it stay live.
// The texture's pixels are the canvas's: its origin sits on the canvas pixel grid, so it is drawn
// pixel for pixel as the sprites were.
import { Matrix, RenderTexture, Sprite } from 'pixi.js';

/** The margin round the view, game px (half a tile). */
export const CACHE_MARGIN = 8;

/**
 * Where the cache should lie for a view, or null when the current one still covers the view. The new
 * area leads in the direction the view moves (the margin behind it goes ahead: the view crosses twice
 * the margin before the next redraw), on the canvas pixel grid. Pure.
 * @param {{ x: number, y: number, w: number, h: number } | null} rect the current area (game px), or null
 * @param {{ x: number, y: number }} origin the view's top left (game px) @param {number} vw @param {number} vh
 * @param {{ x: number, y: number }} dir the view's last move (sign per axis)
 * @param {number} res canvas px per game px @param {number} [margin]
 * @returns {{ x: number, y: number, w: number, h: number } | null}
 */
export function planCacheRect(rect, origin, vw, vh, dir, res, margin = CACHE_MARGIN) {
  const w = Math.ceil((vw + 2 * margin) * res) / res;
  const h = Math.ceil((vh + 2 * margin) * res) / res;
  const eps = 1e-6;
  if (rect && rect.w === w && rect.h === h && origin.x >= rect.x - eps && origin.y >= rect.y - eps && origin.x + vw <= rect.x + w + eps && origin.y + vh <= rect.y + h + eps) return null;
  const lead = (/** @type {number} */ d) => margin * (1 - Math.sign(d)); // moving +: 0 behind, 2 margins ahead
  const snap = (/** @type {number} */ v) => Math.round(v * res) / res;
  return { x: snap(origin.x - lead(dir.x)), y: snap(origin.y - lead(dir.y)), w, h };
}

export class GroundCache {
  /**
   * @param {any} renderer PixiJS renderer @param {import('pixi.js').Container} source what is cached (hidden in the normal pass)
   */
  constructor(renderer, source) {
    this.renderer = renderer;
    this.source = source;
    /** The sprite that shows the cache in the world (put it where the source was). */
    this.sprite = new Sprite();
    this.sprite.label = 'ground-cache';
    /** @type {RenderTexture | null} */
    this.texture = null;
    /** @type {{ x: number, y: number, w: number, h: number } | null} */
    this.rect = null;
    this.dirty = true;
    /** @type {{ x: number, y: number } | null} */
    this.last = null;
    this.dir = { x: 0, y: 0 };
    this.stats = { redraws: 0, ms: 0 };
  }

  /** The ground changed (a chunk came or went, the season, the water edges): draw it again. */
  invalidate() {
    this.dirty = true;
  }

  /**
   * The area to draw into the cache this frame (game px), so the caller shows the ground there (its
   * culling), or the current one. @param {{ x: number, y: number }} origin @param {number} vw @param {number} vh @param {number} res
   */
  plan(origin, vw, vh, res) {
    if (this.last) {
      const dx = origin.x - this.last.x;
      const dy = origin.y - this.last.y;
      if (dx) this.dir.x = Math.sign(dx);
      if (dy) this.dir.y = Math.sign(dy);
    }
    this.last = { x: origin.x, y: origin.y };
    const next = planCacheRect(this.rect, origin, vw, vh, this.dir, res);
    if (next) {
      this.rect = next;
      this.dirty = true;
    }
    return /** @type {{ x: number, y: number, w: number, h: number }} */ (this.rect);
  }

  /** Draws the source into the cache when it is dirty, and places the sprite. @param {number} res canvas px per game px */
  update(res) {
    const r = this.rect;
    if (!r) return;
    if (this.dirty) {
      const t0 = performance.now();
      const pw = Math.round(r.w * res);
      const ph = Math.round(r.h * res);
      if (!this.texture || this.texture.source.pixelWidth !== pw || this.texture.source.pixelHeight !== ph) {
        this.texture?.destroy(true);
        this.texture = RenderTexture.create({ width: r.w, height: r.h, resolution: res, scaleMode: 'nearest', antialias: false });
        this.sprite.texture = this.texture;
      }
      this.source.visible = true;
      this.renderer.render({ container: this.source, target: this.texture, clear: true, clearColor: [0, 0, 0, 0], transform: new Matrix().translate(-r.x, -r.y) });
      this.dirty = false;
      this.stats.redraws++;
      this.stats.ms += performance.now() - t0;
    }
    this.source.visible = false;
    this.sprite.position.set(r.x, r.y);
  }

  /** The cache's memory, bytes. */
  bytes() {
    return this.texture ? this.texture.source.pixelWidth * this.texture.source.pixelHeight * 4 : 0;
  }

  destroy() {
    this.texture?.destroy(true);
    this.texture = null;
    this.sprite.destroy();
  }
}
