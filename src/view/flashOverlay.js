// @ts-check
// v1.0: the attack warning flash as an OVERLAY (docs/art-direction/ART_STYLE_GUIDE.md 5.4 B): red
// #ff3a3a at 50% laid over the enemy's shape. A sprite tint only multiplies (a dark body stays
// dark), so the overlay is a second sprite on top: the frame's solid-white silhouette, tinted red at
// alpha 0.5. That is an ordinary textured quad — it batches with the rest, with no filter and no
// extra render pass (a ColorMatrixFilter would render each flashing sprite to its own texture every
// frame: a framebuffer switch and a broken batch per enemy, which costs on the iPhone's tiled GPU).
//
// Silhouettes are made once per frame texture on first use (a canvas copy of that frame with every
// opaque pixel turned white) and cached; only frames that are on screen during a wind-up ever get
// one (a few dozen at most, each the size of one sprite). A silhouette whose source texture was
// destroyed (its region's art released) is destroyed with it.
//
// gfx W5 ('rim', the default with the graphics v2 effects; ?fx=v1 keeps the solid one): the overlay
// is strong on the outline (one game px wide) and faint inside, so the red pulse still reads while the
// art's inner detail (the v2 enemies' shading and patterns) stays visible.
import { Rectangle, Sprite, Texture } from 'pixi.js';
import { WARNING_FLASH } from './enemyAnim.js';

/** gfx W5 rim overlay: the outline's and the inside's opacity in the silhouette, and the overlay's. */
export const RIM_FLASH = Object.freeze({ edge: 1, inside: 0.3, alpha: 0.9 });

/**
 * The rim silhouette's opacity per pixel (0..255): RIM_FLASH.edge on the outline — an opaque pixel
 * within `r` px (one game px) of a transparent one or the frame's edge — RIM_FLASH.inside within the
 * body, 0 outside. Pure.
 * @param {ArrayLike<number>} alpha the frame's alpha, row by row @param {number} w @param {number} h @param {number} r
 * @returns {Uint8ClampedArray}
 */
export function rimAlpha(alpha, w, h, r) {
  const out = new Uint8ClampedArray(w * h);
  const clear = (/** @type {number} */ x, /** @type {number} */ y) => x < 0 || y < 0 || x >= w || y >= h || alpha[y * w + x] < 128;
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      if (alpha[y * w + x] < 128) continue;
      let edge = false;
      for (let d = 1; d <= r && !edge; d++) edge = clear(x - d, y) || clear(x + d, y) || clear(x, y - d) || clear(x, y + d);
      out[y * w + x] = Math.round(255 * (edge ? RIM_FLASH.edge : RIM_FLASH.inside));
    }
  }
  return out;
}

/** Solid-white copies of sprite frames (or, 'rim', strong outlines over a faint body), made on demand. */
export class SilhouetteCache {
  /** @param {'solid' | 'rim'} [mode] */
  constructor(mode = 'solid') {
    /** @type {Map<Texture, Texture>} */
    this.map = new Map();
    this.mode = mode;
  }

  /** @param {Texture} tex */
  get(tex) {
    const hit = this.map.get(tex);
    if (hit) return hit;
    this.prune();
    const made = makeSilhouette(tex, this.mode);
    this.map.set(tex, made);
    return made;
  }

  /** Drops the silhouettes of textures that are gone. */
  prune() {
    for (const [src, sil] of this.map) {
      if (!src.destroyed) continue;
      if (sil !== Texture.WHITE) sil.destroy(true);
      this.map.delete(src);
    }
  }

  get size() {
    return this.map.size;
  }
}

/** @param {Texture} tex @param {'solid' | 'rim'} mode @returns {Texture} */
function makeSilhouette(tex, mode) {
  const src = tex.source;
  const res = src.resolution || 1;
  const img = /** @type {any} */ (src.resource);
  const f = tex.frame;
  const w = Math.max(1, Math.round(f.width * res));
  const h = Math.max(1, Math.round(f.height * res));
  if (!img || typeof document === 'undefined') return Texture.WHITE;
  const canvas = document.createElement('canvas');
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext('2d');
  if (!ctx) return Texture.WHITE;
  ctx.drawImage(img, Math.round(f.x * res), Math.round(f.y * res), w, h, 0, 0, w, h);
  ctx.globalCompositeOperation = 'source-in';
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, w, h);
  if (mode === 'rim') {
    // The same as rimAlpha, by compositing (no pixel read-back, which is slow): the body shrunk by
    // one game px (the silhouette kept only where its copies shifted by r px all four ways are
    // opaque), faded out of the silhouette to RIM_FLASH.inside.
    const r = Math.max(1, Math.round(res));
    const inner = document.createElement('canvas');
    inner.width = w;
    inner.height = h;
    const ic = inner.getContext('2d');
    if (ic) {
      ic.drawImage(canvas, 0, 0);
      ic.globalCompositeOperation = 'destination-in';
      for (const [dx, dy] of [[r, 0], [-r, 0], [0, r], [0, -r]]) ic.drawImage(canvas, dx, dy);
      ctx.globalCompositeOperation = 'destination-out';
      ctx.globalAlpha = RIM_FLASH.edge - RIM_FLASH.inside;
      ctx.drawImage(inner, 0, 0);
      ctx.globalAlpha = 1;
    }
  }
  // Same set-up as the atlases (placeholderPack.js): the frame is measured in game pixels.
  const source = Texture.from(canvas, true).source;
  source.scaleMode = 'nearest';
  if (res !== 1) source.resolution = res;
  return new Texture({ source, frame: new Rectangle(0, 0, w / res, h / res) });
}

/**
 * Lays (or hides) the warning overlay over an enemy sprite. Created lazily: an enemy that never
 * winds up never gets one.
 * @param {Sprite} spr the enemy's sprite (already placed this frame)
 * @param {Sprite | null} overlay its overlay so far
 * @param {number} alpha 0 = off, else the overlay's strength (WARNING_FLASH.alpha)
 * @param {SilhouetteCache} cache
 * @param {import('pixi.js').Container} parent where the overlay goes (the sprite's container)
 * @returns {Sprite | null} the overlay to keep
 */
export function placeFlash(spr, overlay, alpha, cache, parent) {
  if (alpha <= 0) {
    if (overlay) overlay.visible = false;
    return overlay;
  }
  const o = overlay ?? new Sprite(Texture.WHITE);
  if (!overlay) {
    o.tint = WARNING_FLASH.color;
    parent.addChild(o);
  }
  o.texture = cache.get(spr.texture);
  o.anchor.copyFrom(spr.anchor);
  o.position.copyFrom(spr.position);
  o.scale.copyFrom(spr.scale);
  o.alpha = alpha * spr.alpha;
  o.zIndex = spr.zIndex + 0.001; // right over its own sprite
  o.visible = true;
  return o;
}
