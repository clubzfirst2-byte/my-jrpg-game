// @ts-check
// gfx W5: soft cast shadows on the ground, with the light from the top left (ART_STYLE_GUIDE: the
// art is lit from the upper left), so every shadow leans a little to the lower right of what casts
// it. One shared texture (a soft oval), stretched per caster; the sprites batch with each other.
//
// Where they are drawn (gameView.js):
// - map objects on flat ground: baked into the chunk's cached ground texture, so a forest of
//   shadows costs nothing per frame (no extra layer to fill); the cache is redrawn only when an
//   object in the chunk changes (a tree burns down, a jar breaks);
// - crates (they move): loose sprites under the actors;
// - map objects on raised ground: in their terrain row (over its surface, under what stands on it);
// - characters (villagers, enemies) and the island's chests / stones: small pooled sprites sorted
//   with them.
// The geometry is pure (unit-tested); the texture needs a canvas.
import { Texture } from 'pixi.js';

/** Objects that lie flat (no shadow). */
const FLAT = new Set(['mat', 'stairs', 'door', 'plate', 'sensor', 'vine', 'pit']);
/** Tall objects cast a longer shadow to the lower right. */
const TALL = new Set(['tree', 'house', 'pillar', 'cactus', 'star_ring', 'shelf', 'charm_shelf', 'stove']);

/** Shadow strength by kind (0..1, the texture's centre). */
export const SHADOW = Object.freeze({ object: 0.5, tall: 0.46, character: 0.42, color: 0x0c1018 });

/**
 * A caster's shadow: centre offset from its feet (dx right, dy down), size and opacity, or null
 * for flat things. `w` / `h`: the caster's drawn size in game px.
 * @param {string} type @param {number} w @param {number} h
 * @returns {{ dx: number, dy: number, w: number, h: number, alpha: number } | null}
 */
export function objectShadow(type, w, h) {
  if (FLAT.has(type) || w <= 0) return null;
  if (TALL.has(type)) {
    // Light from the upper left: a long soft shadow toward the lower right of the trunk / wall.
    const sw = Math.round(w * 1.05 + h * 0.18);
    return { dx: Math.round(w * 0.16 + h * 0.06), dy: -1, w: sw, h: Math.max(4, Math.round(Math.min(w, 48) * 0.42)), alpha: SHADOW.tall };
  }
  return { dx: Math.round(w * 0.12), dy: -1, w: Math.round(w * 1.0 + 2), h: Math.max(3, Math.round(w * 0.42)), alpha: SHADOW.object };
}

/**
 * A character's shadow (villager, enemy): close under the feet, a little to the lower right.
 * @param {number} w drawn width in game px (absolute)
 */
export function characterShadow(w) {
  const sw = Math.max(8, Math.round(w * 0.8));
  return { dx: Math.round(sw * 0.1), dy: -1, w: sw, h: Math.max(3, Math.round(sw * 0.36)), alpha: SHADOW.character };
}

/** @type {Texture | null} */
let shared = null;
/** The soft oval (white; tinted SHADOW.color where drawn), made once. */
export function shadowTexture() {
  if (shared && !shared.destroyed) return shared;
  const W = 64;
  const H = 32;
  const c = document.createElement('canvas');
  c.width = W;
  c.height = H;
  const g = /** @type {CanvasRenderingContext2D} */ (c.getContext('2d'));
  g.save();
  g.scale(1, H / W); // a circle squashed into the oval
  const grad = g.createRadialGradient(W / 2, W / 2, 0, W / 2, W / 2, W / 2);
  for (let k = 0; k <= 12; k++) {
    const t = k / 12;
    grad.addColorStop(t, `rgba(255,255,255,${(1 - t ** 3).toFixed(4)})`);
  }
  g.fillStyle = grad;
  g.fillRect(0, 0, W, W);
  g.restore();
  shared = Texture.from(c);
  shared.source.scaleMode = 'linear';
  return shared;
}

/**
 * Places a shadow sprite (anchor 0.5) for a caster standing at (x, y) in world px.
 * @param {import('pixi.js').Sprite} s @param {number} x @param {number} y
 * @param {{ dx: number, dy: number, w: number, h: number, alpha: number }} g
 */
export function placeShadow(s, x, y, g) {
  s.position.set(x + g.dx, y + g.dy);
  s.width = g.w;
  s.height = g.h;
  s.alpha = g.alpha;
}
