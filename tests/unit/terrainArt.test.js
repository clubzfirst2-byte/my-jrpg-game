import { describe, it, expect, vi } from 'vitest';
import { readdirSync, readFileSync } from 'node:fs';
import { decodePng } from '../../tools/release-art-pack.mjs';

// v1.0: the terrain release art in normal play (src/view/assets/terrainArt.js). Its files are named
// after the game's sprite keys; these tests pin that every terrain key of the game has its art,
// that every art file is used by the bundle its production record puts it in, and that it fits.
vi.mock('pixi.js', () => ({ Rectangle: class {}, Texture: class {} }));
const { REGION_ENTRIES, placeholderEntries, releaseHeroEntries, releaseNpcEntries, releaseEnemyEntries, atlasSizeFor, ART_SCALE, mustKeepSize } = await import('../../src/view/assets/placeholderPack.js');
const { isTerrainKey, wantsTerrainArt, TERRAIN_GROUP, TERRAIN_OBJECTS, groundVariant, levelBrightness, indoorLight, groundCacheResolution } = await import('../../src/view/assets/terrainArt.js');

const ROOT = new URL('../../src/art-release/', import.meta.url);
/** name -> { w, h } of every PNG in a release folder (from the IHDR). */
const sizes = (group) =>
  new Map(
    readdirSync(new URL(`${group}/`, ROOT))
      .filter((f) => f.endsWith('.png'))
      .map((f) => {
        const buf = readFileSync(new URL(`${group}/${f}`, ROOT));
        return [f.slice(0, -4), { w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) }];
      }),
  );
const ART = sizes(TERRAIN_GROUP);

/** Bundle name -> its entries, as the game registers them (main.js): 'base' and REGION_ENTRIES. */
const BUNDLES = new Map([['base', placeholderEntries()], ...Object.entries(REGION_ENTRIES).map(([n, make]) => [n, make()])]);
/** key -> bundle names holding it */
const holders = new Map();
for (const [name, entries] of BUNDLES) for (const e of entries) holders.set(e.key, [...(holders.get(e.key) ?? []), name]);

/** The production record's grouping (docs/art-release/terrain/PRODUCTION.md): `base`, `region-desert`, `season-autumn`, ... */
const RECORD = new Map();
for (const m of readFileSync(new URL('../../docs/art-release/terrain/PRODUCTION.md', import.meta.url), 'utf8').matchAll(/^\| (base|region-[a-z]+|season-[a-z]+) \| \d+ \| (.+) \|$/gm)) {
  const bundle = m[1] === 'base' ? 'base' : m[1].replace('-', ':');
  for (const n of m[2].matchAll(/`([^`]+)`/g)) RECORD.set(n[1], bundle);
}

/**
 * Terrain keys the game draws with no terrain art, and why (none today: every terrain key has art).
 * @type {Record<string, string>}
 */
const FALLBACKS = {};

describe('terrain release art → game sprite keys', () => {
  it('has the 111 files of the production record, every one a terrain key', () => {
    expect(ART.size).toBe(111);
    expect([...RECORD.keys()].sort()).toEqual([...ART.keys()].sort());
    for (const name of ART.keys()) expect(isTerrainKey(name), name).toBe(true);
  });

  it('every terrain key the game draws has its art (or a deliberate fallback)', () => {
    const terrainKeys = [...holders.keys()].filter(isTerrainKey);
    expect(terrainKeys.length).toBe(111);
    const missing = terrainKeys.filter((k) => !ART.has(k) && !(k in FALLBACKS));
    expect(missing).toEqual([]);
  });

  it('no art is left unused: each file is held by the bundle its record names (base, its region, its season)', () => {
    for (const [name, bundle] of RECORD) expect(holders.get(name), name).toEqual([bundle]);
  });

  it('nothing outside the terrain is a terrain key (objects, puzzle parts, icons, effects, characters keep their own art)', () => {
    const other = [...holders.keys()].filter((k) => !isTerrainKey(k));
    for (const k of ['obj.chest.closed', 'obj.house', 'obj.stairs', 'obj.crate', 'sw.plate.on', 'fx.shadow', 'ui.marker', 'px', 'player.walk.down.0', 'enemy.beast.0']) expect(other, k).toContain(k);
    expect(TERRAIN_OBJECTS.every((k) => holders.has(k))).toBe(true);
  });

  it('tiles and faces are exactly 2 art px per game px of their placeholder (32×32 = 16 game px); the rest stand on their feet', () => {
    for (const entries of BUNDLES.values()) {
      for (const e of entries) {
        const art = ART.get(e.key);
        if (!art) continue;
        if (mustKeepSize(e.anchor)) {
          expect([art.w, art.h], e.key).toEqual([e.rows[0].length * ART_SCALE, e.rows.length * ART_SCALE]);
        } else {
          expect(e.anchor, e.key).toEqual([0.5, 1]);
          // feet: the bottom row is drawn near the middle (the sprite stands where the placeholder stood)
          const img = decodePng(readFileSync(new URL(`${TERRAIN_GROUP}/${e.key}.png`, ROOT)), e.key);
          const row = img.height - 1;
          const opaque = [...Array(img.width).keys()].filter((x) => img.data[(row * img.width + x) * 4 + 3] === 255);
          expect(opaque.length, e.key).toBeGreaterThan(0);
          const mid = (Math.min(...opaque) + Math.max(...opaque) + 1) / 2;
          expect(Math.abs(mid - img.width / 2), e.key).toBeLessThanOrEqual(3);
        }
      }
    }
    // the water's two frames share one frame size
    expect(ART.get('tile.water.0')).toEqual(ART.get('tile.water.1'));
  });

  it('with the release hero, villagers and enemies the base atlas of the release art stays within 2048 × 1024', () => {
    const release = new Map([...sizes('hero'), ...sizes('npc'), ...sizes('enemy'), ...ART]);
    const keys = new Set(release.keys());
    const base = [...placeholderEntries(), ...releaseHeroEntries(keys), ...releaseNpcEntries(keys), ...releaseEnemyEntries(keys)];
    const real = base.filter((e) => release.has(e.key)).map((e) => ({ ...e, image: { width: release.get(e.key).w, height: release.get(e.key).h } }));
    expect(real.filter((e) => ART.has(e.key)).length).toBe(43);
    const size = atlasSizeFor(real);
    expect(size.width).toBeLessThanOrEqual(2048);
    expect(size.height).toBeLessThanOrEqual(1024);
  });

  it('the release terrain is drawn near its own colours (flat 0.95, +0.05 a level); the placeholders keep 0.8 + 0.07', () => {
    expect(levelBrightness(0, true)).toBeCloseTo(0.95);
    expect(levelBrightness(1, true)).toBeCloseTo(1);
    expect(levelBrightness(4, true)).toBe(1);
    expect(levelBrightness(0, false)).toBeCloseTo(0.8);
    expect(levelBrightness(2, false)).toBeCloseTo(0.94);
  });

  it('the cached flat ground keeps the art density (2 art px per game px with the release terrain)', () => {
    expect(groundCacheResolution(true)).toBe(ART_SCALE);
    expect(groundCacheResolution(false)).toBe(1);
  });

  it('indoors is a little brighter with the release terrain (its stone is darker); the placeholders keep 0.55', () => {
    expect(indoorLight(true)).toEqual({ r: 0.65, g: 0.65, b: 0.75 });
    expect(indoorLight(false)).toEqual({ r: 0.55, g: 0.55, b: 0.65 });
  });

  it('release ground variants: 0 (plain) about half the time, the marked ones an equal share each; placeholders evenly', () => {
    for (const n of [3, 4]) {
      const counts = Array(n).fill(0);
      const N = 2 * n * 1000;
      for (let h = 0; h < N; h++) counts[groundVariant(h, n, true)]++;
      expect(counts[0] / N).toBeCloseTo((n + 1) / (2 * n), 5);
      for (let v = 1; v < n; v++) expect(counts[v] / N).toBeCloseTo(1 / (2 * n), 5);
      for (let h = 0; h < 50; h++) expect(groundVariant(h, n, false)).toBe(h % n);
    }
  });

  it('is drawn in normal play, not with ?terrain=placeholder, ?hd=0 or ?hero=placeholder (unless ?terrain=release)', () => {
    const p = (q) => new URLSearchParams(q);
    expect(wantsTerrainArt(p(''), true)).toBe(true);
    expect(wantsTerrainArt(p('terrain=placeholder'), true)).toBe(false);
    expect(wantsTerrainArt(p('hd=0'), true)).toBe(false);
    expect(wantsTerrainArt(p('hero=placeholder'), false)).toBe(false);
    expect(wantsTerrainArt(p('hero=placeholder&terrain=release'), false)).toBe(true);
    expect(wantsTerrainArt(p('hd=0&terrain=release'), false)).toBe(false);
  });
});
