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
import { Rectangle, Sprite, Texture } from 'pixi.js';
import { WARNING_FLASH } from './enemyAnim.js';

/** Solid-white copies of sprite frames, made on demand. */
export class SilhouetteCache {
  constructor() {
    /** @type {Map<Texture, Texture>} */
    this.map = new Map();
  }

  /** @param {Texture} tex */
  get(tex) {
    const hit = this.map.get(tex);
    if (hit) return hit;
    this.prune();
    const made = makeSilhouette(tex);
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

/** @param {Texture} tex @returns {Texture} */
function makeSilhouette(tex) {
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
