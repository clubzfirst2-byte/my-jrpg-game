import { describe, it, expect } from 'vitest';
import { readdirSync } from 'node:fs';
import { chooseToastSlot, V3_DEFAULT, V3_DENSITY, V3_TARGET_HEIGHT, v3Enabled, v3ArtGroups, v3RegionOf, mirrorSourceOf, frameFight, onScreen } from '../../src/view/assets/artV3.js';
import { computeView } from '../../src/view/resolution.js';
import { planCacheRect, CACHE_MARGIN } from '../../src/view/groundCache.js';
import { GameView, CHUNK } from '../../src/view/gameView.js';
import { createGameState, MAPS } from '../../src/game/state.js';
import { createEnemy, updateEnemy } from '../../src/game/entities/enemies.js';
import { inSeason } from '../../src/game/env/weather.js';
import { REGION_ENTRIES, mirroredFrames, releaseV3RegionEntries, v3PlainsEntries, atlasSizeFor, densityOf, ART_SCALE, SheetRef, acquireSheet, releaseSheet } from '../../src/view/assets/placeholderPack.js';
import { onDemandReleaseGroup, precacheFiles } from '../../tools/precache.mjs';

// Graphics v3 (docs/art-release-v3/STYLE.md, ?v3=1): density 4, the narrow integer view, the play
// adjustments and the memory measures. ?v3=0 (and the default, until the director decides) is the game
// as before.

const P = (q) => new URLSearchParams(q);

describe('switch', () => {
  it('is off by default until the director decides; ?v3=1 / ?v3=0', () => {
    expect(V3_DEFAULT).toBe(false);
    expect(v3Enabled(P(''))).toBe(false);
    expect(v3Enabled(P('v3=1'))).toBe(true);
    expect(v3Enabled(P('v3=0'))).toBe(false);
    expect(v3Enabled(P('v3=yes'))).toBe(false);
  });
  it('loads the v3 groups only with ?v3=1, each one can go back to its previous art (?hero=v2)', () => {
    const avail = ['terrain', 'hero', 'npc', 'enemy', 'objects'];
    expect(v3ArtGroups(P(''), avail)).toEqual([]);
    expect(v3ArtGroups(P('v3=0'), avail)).toEqual([]);
    expect(v3ArtGroups(P('v3=1'), avail)).toEqual(['v3/enemy', 'v3/hero', 'v3/npc', 'v3/objects', 'v3/terrain']);
    expect(v3ArtGroups(P('v3=1&hero=v2&terrain=v1'), avail)).toEqual(['v3/enemy', 'v3/npc', 'v3/objects']);
  });
  it('the v3 groups are not preloaded or kept offline while v3 is not the default', () => {
    expect(onDemandReleaseGroup('v3-hero')).toBe(!V3_DEFAULT);
    expect(onDemandReleaseGroup('hero')).toBe(false);
    const files = precacheFiles({ 'assets/release-v3-hero-x.png': { type: 'asset', fileName: 'assets/release-v3-hero-x.png', names: ['release-v3-hero.png'] }, 'assets/release-hero-y.png': { type: 'asset', fileName: 'assets/release-hero-y.png', names: ['release-hero.png'] } });
    expect(files).toContain('assets/release-hero-y.png');
    expect(files).not.toContain('assets/release-v3-hero-x.png');
  });
});

describe('the v3 view (STYLE.md 2.2): k = max(1, round(short side / 640)), game scale 4k', () => {
  const opts = { mode: /** @type {const} */ ('int'), canvasDensity: V3_DENSITY, artDensities: [V3_DENSITY, ART_SCALE] };
  /** [name, css w, css h, dpr, k, canvas w × h, tiles] */
  const SCREENS = [
    ['iPhone 15 Pro', 852, 393, 3, 2, 1278, 590, 20.0, 9.2],
    ['iPhone 15', 844, 390, 3, 2, 1266, 585, 19.8, 9.1],
    ['iPhone 15 Pro Max', 932, 430, 3, 2, 1398, 645, 21.8, 10.1],
    ['iPhone SE', 667, 375, 2, 1, 1334, 750, 20.8, 11.7],
    ['PC 1920×1080', 1920, 1080, 1, 2, 960, 540, 15.0, 8.4],
  ];
  for (const [name, w, h, dpr, k, cw, ch, tx, ty] of SCREENS) {
    it(`${name}: k=${k}, canvas ${cw}×${ch}, ${tx}×${ty} tiles`, () => {
      const r = computeView(w, h, dpr, V3_TARGET_HEIGHT, opts);
      expect(r.canvasScale).toBe(k);
      expect(r.scale).toBe(4 * k);
      expect(r.artPixel).toEqual([k, 2 * k]); // a v3 pixel is k device px, a density-2 pixel 2k (whole)
      expect([r.width, r.height]).toEqual([cw, ch]);
      expect(r.tilesX).toBeCloseTo(tx, 0);
      expect(r.tilesY).toBeCloseTo(ty, 0);
      expect(Math.abs(r.tilesX - tx)).toBeLessThan(0.1);
      expect(Math.abs(r.tilesY - ty)).toBeLessThan(0.1);
    });
  }
});

describe('art', () => {
  it('density: v3 sources carry 4, the rest is ART_SCALE (2)', () => {
    expect(densityOf('a.png')).toBe(ART_SCALE);
    expect(densityOf({ url: 'a.png', density: 4 })).toBe(4);
    expect(densityOf({ sheet: /** @type {any} */ ({}), x: 0, y: 0, w: 1, h: 1 })).toBe(ART_SCALE);
    expect(densityOf({ sheet: /** @type {any} */ ({}), x: 0, y: 0, w: 1, h: 1, density: 4 })).toBe(4);
  });
  it('the v3 plains art: one bundle per season (summer for spring too), the stone house in the village bundle (villageV3.test.js), the characters in the base one', () => {
    const files = readdirSync(new URL('../../src/art-release-v3/terrain/', import.meta.url)).map((f) => f.slice(0, -4));
    const objects = readdirSync(new URL('../../src/art-release-v3/objects/', import.meta.url)).map((f) => f.slice(0, -4));
    const overrides = new Map([...files, ...objects, 'hero.idle.down.0', 'enemy.slime.idle.0'].map((k) => [k, { url: `${k}.png`, density: 4 }]));
    expect(v3RegionOf('hero.idle.down.0')).toBe(null);
    expect(v3RegionOf('npc.woman.idle.down.0')).toBe(null);
    expect(releaseV3RegionEntries('region:plains', overrides).map((e) => e.key)).toEqual([]);
    expect(releaseV3RegionEntries('region:forest', overrides)).toEqual([]);
    const seasons = /** @type {const} */ (['summer', 'autumn', 'winter']);
    const all = [...seasons, /** @type {const} */ ('flow')].flatMap((s) => v3PlainsEntries(s, overrides).map((e) => e.key));
    expect(new Set(all).size).toBe(all.length);
    // every production file is in exactly one season's bundle; the pilot's tree / flowers / stump in none
    expect(all.sort()).toEqual(files.filter((f) => /plains\.(?:grass|grassflow|tree|prop)\.v3\./.test(f)).sort());
    for (const s of seasons) {
      const e = v3PlainsEntries(s, overrides);
      expect(e.filter((x) => /grass\.v3\.[a-h]\d\d$/.test(x.key)).length).toBe(128);
      // the flow shapes: winter's own 104, summer and autumn share the "flow" bundle's 104
      expect(e.filter((x) => x.key.includes('grassflow')).length).toBe(s === 'winter' ? 104 : 0);
      expect(e.filter((x) => x.key.includes('.edge.')).length).toBe(52);
      for (const x of e) expect(x.anchor).toEqual(/grass(?:flow)?\.v3\./.test(x.key) ? [0, 0] : [0.5, 1]);
      if (s !== 'summer') expect(e.every((x) => x.key.startsWith(`${s}.`))).toBe(true);
    }
    expect(v3PlainsEntries('flow', overrides).length).toBe(104);
    expect(v3PlainsEntries('flow', overrides).every((x) => /^plains\.grassflow\.v3\.[01]{4}\.\d+$/.test(x.key))).toBe(true);
    expect(REGION_ENTRIES['region:plains']).toBeTypeOf('function');
  });
  it('a v3 atlas is only as high as it is used (exactHeight), a season of plains art fits 2048 × about 1100', () => {
    const tile = { rows: [], image: { width: 64, height: 64 } };
    const tree = { rows: [], image: { width: 160, height: 224 } };
    const set = [...Array(12).fill(tree), ...Array(384).fill(tile)];
    expect(atlasSizeFor(set)).toEqual({ width: 2048, height: 2048 });
    const exact = atlasSizeFor(set, { exactHeight: true });
    expect(exact.width).toBe(2048);
    expect(exact.height % 4).toBe(0);
    expect(exact.height).toBeLessThan(1200);
  });
});

describe('left frames mirrored from right ones (STYLE.md 10.1 (3))', () => {
  const img = (w, h, id) => ({ width: w, height: h, id });
  it('only where the left is the right mirrored (or the right is finer: v3), else kept', () => {
    const all = [
      { key: 'hero.walk.right.0', image: img(32, 56, 'r0') },
      { key: 'hero.walk.left.0', image: img(32, 56, 'l0') }, // the same mirrored
      { key: 'hero.attack1.right.0', image: img(48, 56, 'r1') },
      { key: 'hero.attack1.left.0', image: img(48, 56, 'l1') }, // sword in the other hand: own art
      { key: 'hero.idle.right.0', image: img(64, 112, 'r2'), density: 4 },
      { key: 'hero.idle.left.0', image: img(32, 56, 'l2') }, // v1 left, v3 right: mirrored v3
      { key: 'npc.a.idle.left.0', image: img(32, 56, 'l3') }, // no right frame
      { key: 'player.walk.left.0' }, // placeholder: untouched
      { key: 'player.walk.right.0' },
    ];
    const same = (l, r) => ({ l0: 'r0' })[l.id] === r.id;
    const m = mirroredFrames(all, { same });
    expect([...m]).toEqual([
      ['hero.walk.left.0', 'hero.walk.right.0'],
      ['hero.idle.left.0', 'hero.idle.right.0'],
    ]);
    expect(mirrorSourceOf('hero.walk.left.3')).toBe('hero.walk.right.3');
    expect(mirrorSourceOf('hero.walk.down.3')).toBe(null);
  });
});

describe('CPU-side sheets let go between builds (STYLE.md 10.1 (6))', () => {
  it('a SheetRef keeps its image only while someone cuts from it', async () => {
    const image = /** @type {any} */ ({ src: 'sheet.png', naturalWidth: 64, naturalHeight: 32 });
    const ref = new SheetRef(image);
    expect(ref.src).toBe('sheet.png');
    expect([ref.naturalWidth, ref.naturalHeight]).toEqual([64, 32]);
    const a = await acquireSheet(ref);
    const b = await acquireSheet(ref);
    expect(a).toBe(image);
    expect(b).toBe(image);
    releaseSheet(ref);
    expect(ref.image).toBe(image);
    releaseSheet(ref);
    expect(ref.image).toBe(null);
    releaseSheet(ref);
    expect(ref.users).toBe(0);
    // a plain image is passed through
    expect(await acquireSheet(image)).toBe(image);
  });
});

describe('play: enemies see and attack only on screen (state.viewRect)', () => {
  it('onScreen: inside the view less its margins; no view = no limit', () => {
    const view = { x: 0, y: 0, width: 320, height: 147 };
    expect(onScreen({ x: 160, y: 80 }, null)).toBe(true);
    expect(onScreen({ x: 160, y: 80 }, view)).toBe(true);
    expect(onScreen({ x: 3, y: 80 }, view)).toBe(false);
    expect(onScreen({ x: 160, y: 5 }, view)).toBe(false); // its body would be above the top edge
    expect(onScreen({ x: 160, y: 146 }, view)).toBe(false);
    expect(onScreen({ x: 330, y: 80 }, view)).toBe(false);
  });

  /** An archer 120 px north of the hero on the open start beach: in its sight range (140), off a 147-px-tall view centred on the hero. */
  function archerScene() {
    const state = createGameState(MAPS.world);
    state.enemies.length = 0;
    const p = state.player;
    const e = createEnemy('archer', p.x, p.y - 120, p.z, 900);
    state.enemies.push(e);
    return { state, p, e };
  }
  const run = (state, e, ms) => {
    for (let t = 0; t < ms; t += 1000 / 60) updateEnemy(e, state, 1 / 60);
  };

  it('without a view (?v3=0, tests): the archer aims and shoots from 120 px as before', () => {
    const { state, e } = archerScene();
    run(state, e, 1500);
    expect(state.projectiles.filter((s) => s.owner === 'enemy').length).toBeGreaterThan(0);
  });
  it('with the v3 view: an archer off screen never aims or shoots', () => {
    const { state, p, e } = archerScene();
    state.viewRect = { x: p.x - 160, y: p.y - 74, width: 320, height: 147 };
    run(state, e, 3000);
    expect(state.projectiles.length).toBe(0);
    expect(e.state).not.toBe('windup');
  });
  it('with the v3 view: once on screen it aims and shoots', () => {
    const { state, p, e } = archerScene();
    state.viewRect = { x: p.x - 160, y: p.y - 140, width: 320, height: 147 };
    run(state, e, 1500);
    expect(state.projectiles.filter((s) => s.owner === 'enemy').length).toBeGreaterThan(0);
  });
  it('with the v3 view: an archer that leaves the screen while drawing lets the shot go', () => {
    const { state, p, e } = archerScene();
    state.viewRect = { x: p.x - 160, y: p.y - 140, width: 320, height: 147 };
    for (let i = 0; i < 200 && e.state !== 'windup'; i++) updateEnemy(e, state, 1 / 60);
    expect(e.state).toBe('windup');
    state.viewRect = { x: p.x - 160, y: p.y - 74, width: 320, height: 147 };
    run(state, e, 1000);
    expect(state.projectiles.length).toBe(0);
  });
});

describe('arena camera (frameFight)', () => {
  const view = { width: 320, height: 147 };
  const box = (x, y, w, h) => ({ x0: x - w / 2, x1: x + w / 2, y0: y - h, y1: y });
  const inView = (c, b, insets = { top: 0, bottom: 0 }) => b.y0 >= c.y - view.height / 2 + insets.top - 1e-9 && b.y1 <= c.y + view.height / 2 - insets.bottom + 1e-9 && b.x0 >= c.x - view.width / 2 && b.x1 <= c.x + view.width / 2;

  it('hero and boss both fit: both on screen, centred between them', () => {
    const hero = box(100, 200, 20, 32);
    const boss = box(100, 120, 56, 66);
    const c = frameFight(hero, [boss], view);
    expect(inView(c, hero)).toBe(true);
    expect(inView(c, boss)).toBe(true);
  });
  it('the telegraph is taken in when it fits', () => {
    const hero = box(100, 200, 20, 32);
    const boss = box(100, 150, 56, 66);
    const ring = { x0: 60, x1: 140, y0: 110, y1: 190 };
    const c = frameFight(hero, [boss, ring], view);
    for (const b of [hero, boss, ring]) expect(inView(c, b)).toBe(true);
  });
  it('too much to fit: the hero always stays on screen, as near the rest as allowed', () => {
    const hero = box(100, 400, 20, 32);
    const boss = box(100, 120, 56, 66);
    const c = frameFight(hero, [boss], view);
    expect(inView(c, hero)).toBe(true);
    expect(c.y).toBeLessThan(400 - 16); // pulled toward the boss
  });
  it('the hero is kept clear of the UI insets (boss bar)', () => {
    const insets = { top: 30, bottom: 0 };
    const hero = box(100, 140, 20, 32);
    const boss = box(100, 400, 56, 66);
    const c = frameFight(hero, [boss], view, insets);
    expect(inView(c, hero, insets)).toBe(true);
  });
});

/** A view of the world with only what the ground needs (as groundV2World.test.js), the v2 and v3 terrain art "loaded". */
function worldView(v3) {
  const v2 = readdirSync(new URL('../../src/art-release-v2/terrain/', import.meta.url)).map((f) => f.slice(0, -4));
  const v3art = readdirSync(new URL('../../src/art-release-v3/terrain/', import.meta.url)).map((f) => f.slice(0, -4));
  const ART = new Set([...v2, ...v3art]);
  const state = createGameState(MAPS.world);
  const v = Object.create(GameView.prototype);
  Object.assign(v, {
    v3,
    map: state.map,
    regions: state.regions,
    assets: { hasTexture: (k) => ART.has(k), isLoaded: () => true, load: async () => {}, unload: () => {}, builders: new Map(), version: 0 },
    groundV2: true,
    releaseTerrain: true,
    placement: true,
    season: null,
    seasonBundle: null,
    seasonKeySet: new Set(),
    chunks: new Map(),
    v2Tiles: new Map(),
    v2Missing: new Set(),
    deepWater: null,
    variantCounts: { version: '', counts: new Map() },
    sandUnderTrees: new Set(),
  });
  return v;
}

describe('v3 ground (no chunk cache)', () => {
  /** Every land piece of every chunk (the plains column), "x,y,key,quarter" → count. */
  const landPieces = (v, cxs, cys) => {
    const n = new Map();
    for (const cy of cys) for (const cx of cxs) for (const p of v.groundPiecesV2(cx, cy)) {
      if (p.anim) continue;
      const k = `${p.x},${p.y},${p.key.replace(/\.v3\..*$/, '.v3')},${p.quarter}`;
      n.set(k, (n.get(k) ?? 0) + 1);
    }
    return n;
  };
  const cxs = [0, 1];
  const cys = [2, 3, 4];

  it('?v3=0: the pieces are as before (the overhang drawn by both chunks, clipped by their caches)', () => {
    const before = landPieces(worldView(false), cxs, cys);
    expect([...before.values()].some((c) => c > 1)).toBe(true);
  });
  it('?v3=1: each display tile is drawn by exactly one chunk, the same pieces otherwise', () => {
    const v = worldView(true);
    v.updateSeason(inSeason(0, 'summer'));
    const after = landPieces(v, cxs, cys);
    expect([...after.values()].every((c) => c === 1)).toBe(true);
    const w = worldView(false);
    w.v3PlainsGround = () => false;
    const before = landPieces(w, cxs, cys);
    // the same set of positions (v3 only swaps the key of a one-ground display tile)
    // (the first sampled chunk row's north overhang belongs to the row above it, not sampled)
    const y0 = cys[0] * CHUNK * 16 + 8;
    const pos = (m) => new Set([...m.keys()].filter((k) => Number(k.split(',')[1]) >= y0).map((k) => k.split(',').slice(0, 2).join(',') + ',' + k.split(',')[3]));
    expect(pos(after)).toEqual(pos(before));
  });
  it('?v3=1: the plains grass is the v3 ground in every season (base, flow, grass edges; spring = summer)', () => {
    for (const [season, pre] of [['summer', ''], ['spring', ''], ['autumn', 'autumn.'], ['winter', 'winter.']]) {
      const v = worldView(true);
      v.updateSeason(inSeason(0, season));
      const keys = new Set();
      for (let cy = 2; cy <= 4; cy++) for (const cx of [0, 1]) for (const p of v.groundPiecesV2(cx, cy)) keys.add(p.key);
      const base = [...keys].filter((k) => new RegExp(`^${pre.replace('.', '\\.')}plains\\.grass\\.v3\\.[a-h]\\d\\d$`).test(k));
      expect(base.length, season).toBeGreaterThan(100);
      expect([...keys].some((k) => k.startsWith(`${season === 'winter' ? 'winter.' : ''}plains.grassflow.v3.`)), season).toBe(true);
      expect([...keys].some((k) => k.startsWith(`${pre}plains.grass.v3.edge.`)), season).toBe(true);
      // no v2 plains grass left on the flat ground
      expect([...keys].filter((k) => /^plains\.grass\.(?:\d+|macro|edge)/.test(k)), season).toEqual([]);
    }
  });
  it('CHUNK is a whole number of v3 groups', () => {
    expect(CHUNK % 8).toBe(0);
  });
});

describe('messages in the narrow view (chooseToastSlot)', () => {
  const top = { x: 300, y: 80, width: 200, height: 34 };
  const low = { x: 100, y: 340, width: 300, height: 34 };
  it('top unless something is under it and the low slot is clear', () => {
    expect(chooseToastSlot(top, low, [{ x: 410, y: 150, width: 30, height: 56 }])).toBe('top');
    expect(chooseToastSlot(top, low, [{ x: 410, y: 100, width: 30, height: 30 }])).toBe('low');
    expect(chooseToastSlot(top, low, [{ x: 410, y: 100, width: 30, height: 30 }, { x: 200, y: 330, width: 30, height: 30 }])).toBe('top');
  });
});

describe('the v3 ground cache (groundCache.js): a texture a little larger than the view', () => {
  const res = 4;
  it('covers the view with a margin, on the canvas pixel grid; leads in the direction of the move', () => {
    const r = planCacheRect(null, { x: 100.25, y: 50.5 }, 319.5, 147.5, { x: 0, y: 0 }, res);
    expect(r).toEqual({ x: 100.25 - CACHE_MARGIN, y: 50.5 - CACHE_MARGIN, w: 319.5 + 2 * CACHE_MARGIN, h: 147.5 + 2 * CACHE_MARGIN });
    for (const v of [r.x, r.y, r.w, r.h]) expect(Number.isInteger(v * res)).toBe(true);
    // 15 Pro 1342 × 654 px (3.3 MB), SE 1398 × 814 px (4.3 MB)
    expect(r.w * res * r.h * res * 4).toBeLessThan(3.6 * 2 ** 20);
    const se = planCacheRect(null, { x: 0, y: 0 }, 333.5, 187.5, { x: 0, y: 0 }, res);
    expect(se.w * res * se.h * res * 4).toBeLessThan(4.6 * 2 ** 20);
    // moving right: nothing behind, twice the margin ahead
    const right = planCacheRect(null, { x: 100, y: 50 }, 319.5, 147.5, { x: 1, y: 0 }, res);
    expect(right.x).toBe(100);
    expect(right.y).toBe(50 - CACHE_MARGIN);
  });
  it('is kept while the view stays inside it, drawn again once it leaves', () => {
    const r = planCacheRect(null, { x: 100, y: 50 }, 319.5, 147.5, { x: 1, y: 0 }, res);
    expect(planCacheRect(r, { x: 100 + 2 * CACHE_MARGIN, y: 50 }, 319.5, 147.5, { x: 1, y: 0 }, res)).toBe(null);
    expect(planCacheRect(r, { x: 100 + 2 * CACHE_MARGIN + 0.25, y: 50 }, 319.5, 147.5, { x: 1, y: 0 }, res)).not.toBe(null);
    expect(planCacheRect(r, { x: 100, y: 50 - CACHE_MARGIN - 0.25 }, 319.5, 147.5, { x: 1, y: 0 }, res)).not.toBe(null);
    // the view's size changed (rotation, resize): a new texture
    expect(planCacheRect(r, { x: 100, y: 50 }, 300, 147.5, { x: 1, y: 0 }, res)).not.toBe(null);
  });
});
