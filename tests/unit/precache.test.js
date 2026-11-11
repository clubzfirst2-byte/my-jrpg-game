import { describe, it, expect } from 'vitest';
import { precacheFiles, onDemandReleaseGroup, releaseGroupOf, v2PreloadScript, PRECACHE_STATIC } from '../../tools/precache.mjs';

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
  ...['hero', 'npc', 'enemy', 'npc-revision', 'npc-revision-b2', 'terrain', 'objects'].flatMap((g) => [asset(`assets/release-${g}-1.png`, `release-${g}.png`), asset(`assets/release-${g}-2.json`, `release-${g}.json`)]),
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

  it('names the group of a v2 UI frame emitted on its own (release-v2-ui.<frame>.png), and keeps it offline', () => {
    expect(releaseGroupOf('release-v2-ui.panel.menu.png')).toBe('v2-ui');
    expect(releaseGroupOf('release-v2-ui.btn.ring.gold.66.idle.png')).toBe('v2-ui');
    expect(releaseGroupOf('release-v2-terrain.png')).toBe('v2-terrain');
    const bundle = { 'assets/release-v2-ui.panel.menu-x.png': { type: 'asset', fileName: 'assets/release-v2-ui.panel.menu-x.png', names: ['release-v2-ui.panel.menu.png'] } };
    expect(precacheFiles(/** @type {any} */ (bundle))).toContain('assets/release-v2-ui.panel.menu-x.png');
  });
});

describe('the v2 preloads follow the URL (index.html)', () => {
  /** Runs the page's script for a query; returns the preloaded hrefs. */
  const run = (query, enabled = ['ui']) => {
    const added = [];
    const doc = { createElement: () => ({}), head: { appendChild: (l) => added.push(l) } };
    new Function('location', 'document', v2PreloadScript({ ui: ['./a.png', './b.json'], terrain: ['./t.png'] }, enabled))({ search: query }, doc);
    return added.map((l) => `${l.href} ${l.as}`);
  };
  it('the default groups unless ?v2=0 / ?<group>=v1; others only when asked for', () => {
    expect(run('')).toEqual(['./a.png image', './b.json fetch']);
    expect(run('?ui=v1')).toEqual([]);
    expect(run('?v2=0')).toEqual([]);
    expect(run('?v2=0&ui=v2')).toEqual(['./a.png image', './b.json fetch']);
    expect(run('?terrain=v2')).toEqual(['./a.png image', './b.json fetch', './t.png image']);
    expect(run('', [])).toEqual([]);
  });
});

