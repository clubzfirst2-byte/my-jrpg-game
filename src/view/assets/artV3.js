// @ts-check
// Graphics v3 (docs/art-release-v3/STYLE.md, human decision 2026-11-11): art redrawn at twice the detail
// (density 4: 4 art pixels per game pixel, a tile is 64×64, the hero 64×112) and shown at a whole number
// of device pixels per art pixel, which makes the view smaller (about 20×9 tiles on an iPhone 15 Pro in
// landscape, 21×12 on an SE). The new art lives in src/art-release-v3/<group>/, beside the approved v1 /
// v2 art, which is never changed. The build packs each v3 group like a v1 one (vite.config.js releaseArt:
// release-v3-<group>.png / .json; in the game its name is "v3/<group>").
//
// URL switches (nothing is saved):
//   ?v3=1            v3: the v3 art where there is some, the rest of the art (density 2, or the
//                    placeholders) blown up to 2×2 (4×4) v3 pixels, and the narrow integer view
//   ?v3=0            the game as before (density 2, ?scale=fit / ?scale=int as asked)
//   ?<group>=v2      with ?v3=1: that group's previous art only (e.g. ?hero=v2), still in the v3 view
// The default is V3_DEFAULT (off until the director decides).
// Pure (no Vite / PixiJS imports): tools/precache.mjs and the unit tests read it.

/** Whether v3 is on without ?v3= (the director's decision; off until then). */
export const V3_DEFAULT = false;

/** Art pixels per game pixel of the v3 art (STYLE.md 0). */
export const V3_DENSITY = 4;

/**
 * The v3 view aims at this many game px across the shorter side: with the device scale a multiple of
 * V3_DENSITY (resolution.computeView, 'int'), k = max(1, round(short side / (160 × 4))) =
 * max(1, round(short side / 640)) device px per art px (STYLE.md 2.1) and 4k per game px.
 */
export const V3_TARGET_HEIGHT = 160;

/** The v3 groups (folders of src/art-release-v3). */
export const V3_GROUPS = Object.freeze(['hero', 'npc', 'enemy', 'terrain', 'objects', 'fx']);

/** The name a v3 group has in the game (the build's sheet table). @param {string} group */
export const v3Name = (group) => `v3/${group}`;

/** Whether v3 is on. @param {URLSearchParams} params */
export function v3Enabled(params) {
  const v = params.get('v3');
  if (v === '1') return true;
  if (v === '0') return false;
  return V3_DEFAULT;
}

/**
 * The v3 groups to load: those in the build, except a group asked back to its previous art (?hero=v2).
 * @param {URLSearchParams} params @param {Iterable<string>} available the v3 groups in this build
 * @returns {string[]} names ("v3/<group>")
 */
export function v3ArtGroups(params, available) {
  if (!v3Enabled(params)) return [];
  // (a group's season sheets, "terrain.autumn", go with it: release-art-pack.seasonPartOf)
  const off = (/** @type {string} */ g) => ['v1', 'v2'].includes(params.get(g.split('.')[0]) ?? '');
  return [...available].filter((g) => !off(g)).sort().map(v3Name);
}

/**
 * Which region bundle a v3 key goes in (memory: STYLE.md 10.1 (1), a region's art only near it), or null
 * (hero, villagers, enemies: the base bundle, where they keep their v1 frames' place; the plains' ground,
 * trees and props: their own bundle per season, v3Plains.v3PlainsSeasonOf / placeholderPack.v3PlainsEntries;
 * the pilot's tree, flowers and stump, replaced by the production art, are not packed). The pilot's stone
 * house is the plains'.
 * @param {string} key
 */
export function v3RegionOf(key) {
  if (key === 'obj.v3.house_stone') return 'region:plains';
  return null;
}

/**
 * Left-facing frames are not kept in v3 (memory: STYLE.md 10.1 (3)): a `.left.` frame is drawn as its
 * `.right.` frame mirrored. For the existing art this is done only where the left frame IS the right one
 * mirrored, pixel for pixel (the caller compares; e.g. the hero's walk), so nothing changes on screen;
 * a left frame drawn on its own (a held sword, the villagers' light from the upper left) is kept.
 * @param {string} key @returns {string | null} the right-facing key it mirrors, or null
 */
export function mirrorSourceOf(key) {
  return key.includes('.left.') ? key.replace('.left.', '.right.') : null;
}

/** The v3 view's play adjustment for enemies (src/game/core/viewRect.js). */
export { onScreen } from '../../game/core/viewRect.js';

/**
 * Camera framing in a boss fight with the v3 view (STYLE.md 2.3 (2)): when the arena is larger than
 * the view, aim between the hero and the boss so both are in sight, and take in the attack being
 * telegraphed (a slam's ring). The hero always stays on screen: when everything cannot fit, the
 * hero's side wins and the rest is shown as far as it fits. The UI insets (HUD at the top, the boss
 * bar, the buttons) are kept clear of the hero.
 * Per axis: the box of everything of interest is centred when it fits the free part of the view;
 * else the centre is pulled toward it as far as the hero's box allows.
 * @param {{ x0: number, y0: number, x1: number, y1: number }} hero  game px box (feet at y1)
 * @param {{ x0: number, y0: number, x1: number, y1: number }[]} others the boss, its telegraph
 * @param {{ width: number, height: number }} view game px
 * @param {{ top?: number, bottom?: number, left?: number, right?: number }} [insets] game px of the view covered by UI
 * @returns {{ x: number, y: number }} where the camera should centre (before the bounds clamp)
 */
export function frameFight(hero, others, view, insets = {}) {
  const t = insets.top ?? 0;
  const b = insets.bottom ?? 0;
  const l = insets.left ?? 0;
  const r = insets.right ?? 0;
  const axis = (/** @type {number} */ h0, /** @type {number} */ h1, /** @type {number[]} */ lo, /** @type {number[]} */ hi, /** @type {number} */ size, /** @type {number} */ before, /** @type {number} */ after) => {
    const free = Math.max(1, size - before - after);
    // centre of the free part = camera centre + (before - after) / 2
    const shift = (before - after) / 2;
    const a0 = Math.min(h0, ...lo);
    const a1 = Math.max(h1, ...hi);
    let c = (a0 + a1) / 2;
    if (a1 - a0 > free) {
      // keep the hero's box inside the free part, as close to the middle of everything as it allows
      const minC = h1 - free / 2;
      const maxC = h0 + free / 2;
      c = minC <= maxC ? Math.min(Math.max(c, minC), maxC) : (h0 + h1) / 2;
    }
    return c - shift;
  };
  return {
    x: axis(hero.x0, hero.x1, others.map((o) => o.x0), others.map((o) => o.x1), view.width, l, r),
    y: axis(hero.y0, hero.y1, others.map((o) => o.y0), others.map((o) => o.y1), view.height, t, b),
  };
}

/**
 * Graphics v3: where a message (toast) goes so it covers neither the hero nor an enemy. The narrow view
 * makes everyone large and close to the middle: an enemy a few tiles above the hero is where the
 * top-centre message is. The top slot (the usual one) unless something is under it and the low slot
 * (the boss fight's, between the stick side and the buttons) is clear.
 * @param {{ x: number, y: number, width: number, height: number }} top
 * @param {{ x: number, y: number, width: number, height: number }} low
 * @param {{ x: number, y: number, width: number, height: number }[]} actors CSS px boxes of the hero and the enemies
 * @returns {'top' | 'low'}
 */
export function chooseToastSlot(top, low, actors) {
  const hit = (/** @type {typeof top} */ a, /** @type {typeof top} */ b) => a.x < b.x + b.width && b.x < a.x + a.width && a.y < b.y + b.height && b.y < a.y + a.height;
  const covers = (/** @type {typeof top} */ slot) => actors.some((a) => hit(slot, a));
  return covers(top) && !covers(low) ? 'low' : 'top';
}
