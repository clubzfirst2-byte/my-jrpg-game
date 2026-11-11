// @ts-check
// gfx W5: cast shadows on the ground, with the light from the top left (ART_STYLE_GUIDE: the art is
// lit from the upper left), so every shadow leans a little to the lower right of what casts it.
//
// Drawn as pixel art, like everything else: each shadow is a small mask at one texel per game pixel
// (5 device px on a 15 Pro), scaled nearest-neighbour, with 2–3 flat steps of darkness — a dotted
// oval with stepped edges for trees, rocks and characters, and for the village house a shape that
// follows its walls (a band along the right wall under the eave, with a stepped top, and one along
// its foot). One texture per shape and size, made once and shared.
//
// Where they are drawn (gameView.js):
// - map objects on flat ground: small sprites in their chunk's container in the shadow layer (one
//   batched draw); the layer's opacity is the sun's strength, so a change of weather or a lightning
//   flash costs nothing (baking them into the chunks' ground caches meant redrawing every cache);
// - crates (they move): loose sprites under the actors;
// - map objects on raised ground: in their terrain row (over its surface, under what stands on it);
// - characters (villagers, enemies) and the island's chests / stones: small pooled sprites sorted
//   with them.
// The geometry and the masks are pure (unit-tested); the textures need a canvas.
import { atlasFrame, whiteRGBA } from './pixelAtlas.js';

/** Objects that lie flat (no shadow). */
const FLAT = new Set(['mat', 'stairs', 'door', 'plate', 'sensor', 'vine', 'pit']);
/** Tall objects cast a longer shadow to the lower right. */
const TALL = new Set(['tree', 'pillar', 'cactus', 'star_ring', 'shelf', 'charm_shelf', 'stove']);

/**
 * Shadow strength by kind (opacity of the darkest step), its colour, and the opacity of each step
 * (1 = outermost .. 3 = core) as a share of the darkest.
 */
export const SHADOW = Object.freeze({ object: 0.5, tall: 0.46, character: 0.42, color: 0x0c1018, steps: Object.freeze([0, 0.4, 0.7, 1]) });

/**
 * The release house (src/art-release/objects/obj.house.png, 48×56 game px, feet at the bottom
 * centre) as measured on the art: its walls span x −23..+23 and the eave of the roof is 36 px above
 * the feet. Its shadow follows those walls.
 */
export const HOUSE_SHADOW = Object.freeze({ w: 48, h: 56, wallRight: 23, eave: 36, band: 6, foot: 3, footFrom: -19 });

/**
 * How strong the sun's shadows are in this weather (1 clear .. 0 none): overcast skies soften them,
 * and a lightning flash (light from everywhere) puts them out for a moment.
 * @param {string} kind clear | cloudy | rain | storm | snow @param {boolean} [flash]
 */
export function weatherShadow(kind, flash = false) {
  if (flash) return 0;
  return kind === 'cloudy' ? 0.6 : kind === 'rain' ? 0.4 : kind === 'storm' || kind === 'snow' ? 0.3 : 1;
}

/**
 * @typedef {{ dx: number, dy: number, w: number, h: number, alpha: number, shape: 'oval' | 'house' }} ShadowGeom
 *   dx, dy: the centre's offset from the caster's feet (game px); w, h: the mask's size (whole px)
 */

/**
 * A caster's shadow, or null for flat things. `w` / `h`: the caster's drawn size in game px.
 * @param {string} type @param {number} w @param {number} h
 * @returns {ShadowGeom | null}
 */
export function objectShadow(type, w, h) {
  if (FLAT.has(type) || w <= 0) return null;
  if (type === 'house' && w === HOUSE_SHADOW.w && h === HOUSE_SHADOW.h) {
    const H = HOUSE_SHADOW;
    const x0 = H.footFrom;
    const x1 = H.wallRight + H.band;
    const y0 = -H.eave;
    const y1 = H.foot;
    return { dx: (x0 + x1) / 2, dy: (y0 + y1) / 2, w: x1 - x0, h: y1 - y0, alpha: SHADOW.tall, shape: 'house' };
  }
  if (TALL.has(type) || type === 'house') {
    // Light from the upper left: a long shadow toward the lower right of the trunk / wall.
    const sw = Math.round(w * 1.05 + h * 0.18);
    return { dx: Math.round(w * 0.16 + h * 0.06), dy: -1, w: sw, h: Math.max(4, Math.round(Math.min(w, 48) * 0.42)), alpha: SHADOW.tall, shape: 'oval' };
  }
  return { dx: Math.round(w * 0.12), dy: -1, w: Math.round(w * 1.0 + 2), h: Math.max(3, Math.round(w * 0.42)), alpha: SHADOW.object, shape: 'oval' };
}

/**
 * A character's shadow (villager, enemy): close under the feet, a little to the lower right. Its
 * centre sits a pixel below the feet, so a squat body (a slime) does not hide it.
 * @param {number} w drawn width in game px (absolute)
 * @returns {ShadowGeom}
 */
export function characterShadow(w) {
  const sw = Math.max(8, Math.round(w * 0.8));
  return { dx: Math.round(sw * 0.1), dy: 1, w: sw, h: Math.max(3, Math.round(sw * 0.36)), alpha: SHADOW.character, shape: 'oval' };
}

/**
 * The shadow's pixels: one byte per game px, the step of darkness (0 none, 1 outermost .. 3 core).
 * @param {{ w: number, h: number, shape: 'oval' | 'house' }} g
 * @returns {{ w: number, h: number, data: Uint8Array }}
 */
export function shadowMask(g) {
  const w = Math.max(1, Math.round(g.w));
  const h = Math.max(1, Math.round(g.h));
  const data = new Uint8Array(w * h);
  if (g.shape === 'house') {
    const H = HOUSE_SHADOW;
    const x0 = H.footFrom;
    const y0 = -H.eave;
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const gx = x + x0; // game px from the feet
        const gy = y + y0;
        let step = 0;
        // along the right wall, under the eave: its top steps down 2 px every 2 columns
        const c = gx - H.wallRight;
        if (c >= 0 && c < H.band && gy < 0 && gy >= -H.eave + 2 * Math.floor(c / 2)) step = c >= H.band - 1 ? 1 : c >= H.band - 2 ? 2 : 3;
        // along the foot of the house (its front, shifted right by the light)
        if (gy >= 0 && gy < H.foot) {
          const r = gy === H.foot - 1 ? 1 : gy === H.foot - 2 ? 2 : 3;
          const e = w - 1 - x; // the right end steps in with the band
          const s = Math.min(r, e === 0 ? 1 : e === 1 ? 2 : 3);
          step = Math.max(step, s);
        }
        data[y * w + x] = step;
      }
    }
    return { w, h, data };
  }
  // A dotted oval: three flat rings, the inner ones smaller.
  const rx = w / 2;
  const ry = h / 2;
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const nx = (x + 0.5 - rx) / rx;
      const ny = (y + 0.5 - ry) / ry;
      const d = nx * nx + ny * ny;
      data[y * w + x] = d < 0.4 ? 3 : d < 0.72 ? 2 : d < 1 ? 1 : 0;
    }
  }
  return { w, h, data };
}

/**
 * The shared texture frame of a shadow's shape and size (white, the steps in its alpha; tinted
 * SHADOW.color where drawn): one texel per game px, nearest-neighbour, on the effects' atlas.
 * @param {{ w: number, h: number, shape: 'oval' | 'house' }} g
 */
export function shadowTexture(g) {
  const w = Math.max(1, Math.round(g.w));
  const h = Math.max(1, Math.round(g.h));
  return atlasFrame(`shadow:${g.shape}:${w}x${h}`, w, h, () => {
    const m = shadowMask(g);
    return whiteRGBA(
      Array.from(m.data, (v) => Math.round(SHADOW.steps[v] * 255)),
      m.data.length,
    );
  });
}

/**
 * Places a shadow sprite for a caster standing at (x, y) in world px: its texture for the shape and
 * size, on whole game pixels (the steps stay one game pixel wide), at the strength given.
 * @param {import('pixi.js').Sprite} s @param {number} x @param {number} y
 * @param {ShadowGeom} g @param {number} [strength] 0..1, the weather's (weatherShadow)
 */
export function placeShadow(s, x, y, g, strength = 1) {
  const tex = shadowTexture(g);
  if (s.texture !== tex) s.texture = tex;
  s.anchor.set(0, 0);
  s.scale.set(1);
  s.position.set(Math.round(x + g.dx - g.w / 2), Math.round(y + g.dy - g.h / 2));
  s.alpha = g.alpha * strength;
}
