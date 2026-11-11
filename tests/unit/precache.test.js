import { describe, it, expect } from 'vitest';
import { precacheFiles, onDemandReleaseGroup, preloadReleaseGroup, releaseGroupOf, PRECACHE_STATIC } from '../../tools/precache.mjs';

/** @param {string} fileName @param {string[]} moduleIds */
const chunk = (fileName, moduleIds) => [fileName, { type: 'chunk', fileName, moduleIds }];
/** @param {string} fileName @param {string} name */
const asset = (fileName, name) => [fileName, { type: 'asset', fileName, names: [name] }];

const bundle = Object.fromEntries([
  chunk('assets/index-a.js', ['/r/src/main.js', '/r/src/view/assets/heroPrototype.js']),
  chunk('assets/pixi-b.js', ['/r/node_modules/pixi.js/lib/index.mjs']),
  chunk('assets/legacyObjects-c.js', ['/r/src/data/legacyObjects.js']),
  chunk('assets/enemy.archer.0-d.js', ['/r/src/art-proto/enemy/enemy.archer.0.png?url']),
  chunk('assets/player.walk.down.0-e.js', ['C:\\r\\src\\art-proto\\hero\\player.walk.down.0.png?url']),
  asset('assets/index-f.css', 'index.css'),
  asset('assets/index-a.js.map', 'index.js.map'),
  ...['hero', 'npc', 'enemy', 'npc-revision', 'npc-revision-b2', 'terrain', 'objects', 'v2-terrain', 'v2-ui'].flatMap((g) => [asset(`assets/release-${g}-1.png`, `release-${g}.png`), asset(`assets/release-${g}-2.json`, `release-${g}.json`)]),
]);

describe('service worker precache list (perf v1)', () => {
  const files = precacheFiles(/** @type {any} */ (bundle));

  it('keeps everything normal play needs', () => {
    for (const f of PRECACHE_STATIC) expect(files).toContain(f);
    for (const f of ['assets/index-a.js', 'assets/pixi-b.js', 'assets/legacyObjects-c.js', 'assets/index-f.css']) expect(files).toContain(f);
    for (const g of ['hero', 'npc', 'enemy', 'terrain', 'objects']) expect(files).toEqual(expect.arrayContaining([`assets/release-${g}-1.png`, `assets/release-${g}-2.json`]));
  });

  it('leaves out the prototype chunks, the review and unused release sheets, and source maps', () => {
    for (const g of ['npc-revision', 'npc-revision-b2']) {
      expect(files).not.toContain(`assets/release-${g}-1.png`);
      expect(files).not.toContain(`assets/release-${g}-2.json`);
    }
    expect(files).not.toContain('assets/enemy.archer.0-d.js');
    expect(files).not.toContain('assets/player.walk.down.0-e.js');
    expect(files).not.toContain('assets/index-a.js.map');
    expect(new Set(files).size).toBe(files.length);
  });

  it('gfx W1: the v2 terrain is drawn by default, so it is kept for offline play; the v1 terrain stays kept (?terrain=v1, ?v2=0 offline); a v2 group not drawn by default is not', () => {
    for (const g of ['v2-terrain', 'terrain']) expect(files).toEqual(expect.arrayContaining([`assets/release-${g}-1.png`, `assets/release-${g}-2.json`]));
    expect(files).not.toContain('assets/release-v2-ui-1.png');
    expect(onDemandReleaseGroup('v2-terrain')).toBe(false);
    expect(onDemandReleaseGroup('terrain')).toBe(false);
    expect(onDemandReleaseGroup('v2-ui')).toBe(true);
    // (neither terrain sheet is preloaded by the HTML itself: a script picks the one drawn)
    const groups = new Set(['terrain', 'v2-terrain', 'hero']);
    expect(preloadReleaseGroup('terrain', groups) || preloadReleaseGroup('v2-terrain', groups)).toBe(false);
    expect(preloadReleaseGroup('hero', groups)).toBe(true);
  });

  it('a chunk mixing prototype and other modules is kept', () => {
    const mixed = Object.fromEntries([chunk('assets/x.js', ['/r/src/art-proto/hero/a.png?url', '/r/src/main.js'])]);
    expect(precacheFiles(/** @type {any} */ (mixed))).toContain('assets/x.js');
  });

  it('names the release groups', () => {
    expect(releaseGroupOf('release-npc-revision-b2.png')).toBe('npc-revision-b2');
    expect(releaseGroupOf('release-hero.json')).toBe('hero');
    expect(releaseGroupOf('index.css')).toBeNull();
    expect(['hero', 'npc', 'enemy', 'terrain', 'objects'].some(onDemandReleaseGroup)).toBe(false);
    expect(['npc-revision', 'npc-revision-b2', 'npc-revision-b3'].every(onDemandReleaseGroup)).toBe(true);
  });
});
