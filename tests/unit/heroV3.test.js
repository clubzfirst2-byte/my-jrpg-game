import { describe, it, expect } from 'vitest';
import { readdirSync, readFileSync } from 'node:fs';
import { HERO_ANIMS } from '../../src/view/heroAnim.js';
import { HERO_V3_BUNDLE, HERO_V3_LAZY, HERO_V3_MOVE_BUNDLE, HERO_V3_OWN_LEFT, heroActionOf, heroCoveredByV3, heroDrawKey, heroFallbackKey, heroV3BundleOf, heroV3Parts } from '../../src/view/assets/heroV3.js';
import { opaqueBox, atlasSizeFor, knownOpaqueBox } from '../../src/view/assets/placeholderPack.js';
import { decodePng, opaqueRect } from '../../tools/release-art-pack.mjs';

// Graphics v3: the hero at density 4 (docs/art-release-v3/NAMES.md 5, STYLE.md 10.2): the approved hero's
// keys at twice the size; left = right mirrored except attack1-3, bow and guard; climb, swim and glide in
// a bundle loaded on use; the bundle kept all the time under 6.0 MB.

const dir3 = new URL('../../src/art-release-v3/hero/', import.meta.url);
const dir1 = new URL('../../src/art-release/hero/', import.meta.url);
const V3 = readdirSync(dir3).filter((f) => f.endsWith('.png')).map((f) => f.slice(0, -4));
const V1 = readdirSync(dir1).filter((f) => f.endsWith('.png')).map((f) => f.slice(0, -4));
const png = (dir, k) => decodePng(readFileSync(new URL(`${k}.png`, dir)));
const MiB = 2 ** 20;

/** GPU bytes of a bundle's atlas, packed as main.js does (trimmed, tallest first, exact height). */
const atlasBytes = (keys) => {
  const entries = keys.map((k) => {
    const img = png(dir3, k);
    return { rows: [], trim: opaqueBox(img.data, img.width, img.height), image: { width: img.width, height: img.height } };
  });
  entries.sort((a, b) => b.trim.h - a.trim.h);
  const { width, height } = atlasSizeFor(entries, { exactHeight: true });
  return width * height * 4;
};

describe('v3 hero', () => {
  it('206 stored frames: every action and frame of the approved hero for down / right / up, left only for attack1-3, bow and guard', () => {
    expect(V3.length).toBe(206);
    for (const [action, a] of Object.entries(HERO_ANIMS)) {
      for (const dir of ['down', 'right', 'up', 'left']) {
        for (let n = 0; n < a.frames; n++) {
          const key = `hero.${action}.${dir}.${n}`;
          const stored = dir !== 'left' || HERO_V3_OWN_LEFT.includes(action);
          expect(V3.includes(key), key).toBe(stored);
          // the approved hero has every one of them (the v3 keys are its keys)
          expect(V1.includes(key), key).toBe(true);
        }
      }
    }
  });
  it('64×112 (96×112 where the approved frame is 48 wide): twice the approved frame, the feet on the bottom row\'s centre', () => {
    for (const k of V3) {
      const a = png(dir3, k);
      const b = png(dir1, k);
      expect([a.width, a.height], k).toEqual([b.width * 2, b.height * 2]);
    }
  });
  it('the bundles: climb, swim and glide in the move bundle, the rest in the bundle kept; mirrored left frames for the actions without a prop', () => {
    expect(heroV3BundleOf('hero.climb.up.0')).toBe(HERO_V3_MOVE_BUNDLE);
    expect(heroV3BundleOf('hero.swim.left.3')).toBe(HERO_V3_MOVE_BUNDLE);
    expect(heroV3BundleOf('hero.glide.right.1')).toBe(HERO_V3_MOVE_BUNDLE);
    expect(heroV3BundleOf('hero.attack1.left.0')).toBe(HERO_V3_BUNDLE);
    expect(heroV3BundleOf('npc.woman.idle.down.0')).toBe(null);
    const core = heroV3Parts(V3, HERO_V3_BUNDLE);
    const move = heroV3Parts(V3, HERO_V3_MOVE_BUNDLE);
    expect(core.keys.length + move.keys.length).toBe(206);
    expect(move.keys.length).toBe(36); // 3 actions × 4 frames × 3 directions
    expect(move.keys.every((k) => HERO_V3_LAZY.includes(heroActionOf(k)))).toBe(true);
    // left = right mirrored: idle, walk, run, jump, land, dodge, hurt, down (core) and climb, swim, glide (move)
    expect(move.mirrorOf.size).toBe(12);
    expect(move.mirrorOf.get('hero.climb.left.2')).toBe('hero.climb.right.2');
    expect(core.mirrorOf.size).toBe(4 + 6 + 6 + 2 + 2 + 4 + 2 + 4);
    expect(core.mirrorOf.get('hero.walk.left.5')).toBe('hero.walk.right.5');
    // NAMES.md 5: attack1-3, bow and guard use their stored left frames, never a mirror
    for (const left of core.mirrorOf.keys()) expect(HERO_V3_OWN_LEFT.includes(heroActionOf(left)), left).toBe(false);
    for (const a of HERO_V3_OWN_LEFT) expect(core.keys).toContain(`hero.${a}.left.0`);
    // every approved key is drawn by the v3 hero (stored or mirrored)
    const v3 = new Set(V3);
    for (const k of V1) expect(heroCoveredByV3(k, v3), k).toBe(true);
    expect(heroCoveredByV3('hero.attack1.left.0', new Set(['hero.attack1.right.0']))).toBe(false);
  });
  it('memory (STYLE.md 10.2): the bundle kept all the time under 6.0 MB, the move bundle about 1 MB', () => {
    const core = atlasBytes(heroV3Parts(V3, HERO_V3_BUNDLE).keys);
    const move = atlasBytes(heroV3Parts(V3, HERO_V3_MOVE_BUNDLE).keys);
    expect(core).toBeLessThanOrEqual(6.0e6);
    expect(core).toBeLessThan(6.0 * MiB);
    expect(move).toBeLessThan(1.2 * MiB);
  });
  it('the frame drawn: the v3 frame when loaded, else its approved stand-in, else none', () => {
    const loaded = new Set(['hero.idle.down.0', heroFallbackKey('hero.swim.down.1')]);
    const has = (k) => loaded.has(k);
    expect(heroDrawKey('hero.idle.down.0', has)).toBe('hero.idle.down.0');
    expect(heroDrawKey('hero.swim.down.1', has)).toBe('v1.hero.swim.down.1');
    expect(heroDrawKey('hero.swim.down.2', has)).toBe(null);
    loaded.add('hero.swim.down.1');
    expect(heroDrawKey('hero.swim.down.1', has)).toBe('hero.swim.down.1');
  });
  it('the approved stand-ins for a left frame mirror the right one, as the v3 frames do (v1 left = right mirrored for climb, swim, glide)', () => {
    for (const action of HERO_V3_LAZY) {
      for (let n = 0; n < HERO_ANIMS[action].frames; n++) {
        const l = png(dir1, `hero.${action}.left.${n}`);
        const r = png(dir1, `hero.${action}.right.${n}`);
        let same = l.width === r.width && l.height === r.height;
        for (let y = 0; same && y < l.height; y++) {
          for (let x = 0; x < l.width && same; x++) {
            const i = (y * l.width + x) * 4;
            const j = (y * r.width + (r.width - 1 - x)) * 4;
            for (let c = 0; c < 4; c++) if (l.data[i + c] !== r.data[j + c]) same = false;
          }
        }
        expect(same, `${action} ${n}`).toBe(true);
      }
    }
  });
  it('the build\'s opaque box of each frame (release-art-pack.opaqueRect) is the box the game would read from the pixels; a box that does not fit is not used', () => {
    for (const k of V3) {
      const img = png(dir3, k);
      expect(opaqueRect(img), k).toEqual(opaqueBox(img.data, img.width, img.height));
    }
    expect(opaqueRect({ width: 2, height: 2, data: new Uint8Array(16) })).toEqual({ x: 0, y: 0, w: 1, h: 1 });
    const image = { width: 64, height: 112 };
    expect(knownOpaqueBox({ sheet: null, x: 0, y: 0, w: 64, h: 112, density: 4, opaque: { x: 3, y: 2, w: 56, h: 110 } }, image)).toEqual({ x: 3, y: 2, w: 56, h: 110 });
    expect(knownOpaqueBox({ sheet: null, x: 0, y: 0, w: 64, h: 112, density: 4, opaque: { x: 10, y: 2, w: 56, h: 110 } }, image)).toBe(null);
    expect(knownOpaqueBox({ url: 'a.png', density: 4 }, image)).toBe(null);
    expect(knownOpaqueBox('a.png', image)).toBe(null);
  });
});
