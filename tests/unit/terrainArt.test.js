import { describe, it, expect, vi } from 'vitest';
import { readdirSync, readFileSync } from 'node:fs';
import { decodePng } from '../../tools/release-art-pack.mjs';

// v1.0: the terrain release art in normal play (src/view/assets/terrainArt.js). Its files are named
// after the game's sprite keys; these tests pin that every terrain key of the game has its art,
// that every art file is used by the bundle its production record puts it in, and that it fits.
vi.mock('pixi.js', () => ({ Rectangle: class {}, Texture: class {} }));
const { REGION_ENTRIES, placeholderEntries, releaseHeroEntries, releaseNpcEntries, releaseEnemyEntries, atlasSizeFor, ART_SCALE, mustKeepSize } = await import('../../src/view/assets/placeholderPack.js');
const { isTerrainKey, wantsTerrainArt, TERRAIN_GROUP, TERRAIN_OBJECTS, groundVariant, levelBrightness, indoorLight, groundCacheResolution, releaseTerrainEntries, releaseSeasonKeys, v11Bundle, faceVariant, faceMaterial, waterAround, waterEdgePieces } =
  await import('../../src/view/assets/terrainArt.js');

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

/** Bundle name -> its entries, as the game registers them (main.js): 'base' and REGION_ENTRIES, with the v1.1 terrain entries for the art given. */
const BUNDLES = new Map([
  ['base', [...placeholderEntries(), ...releaseTerrainEntries('placeholder', ART)]],
  ...Object.entries(REGION_ENTRIES).map(([n, make]) => [n, [...make(), ...releaseTerrainEntries(n, ART)]]),
]);
/** key -> bundle names holding it */
const holders = new Map();
for (const [name, entries] of BUNDLES) for (const e of entries) holders.set(e.key, [...(holders.get(e.key) ?? []), name]);

/** The production record's grouping (docs/art-release/terrain/PRODUCTION.md): `base`, `region-desert`, `season-autumn`, ... */
const RECORD = new Map();
for (const m of readFileSync(new URL('../../docs/art-release/terrain/PRODUCTION.md', import.meta.url), 'utf8').matchAll(/^\| (base|region-[a-z]+|season-[a-z]+) \| \d+ \| (.+) \|$/gm)) {
  const bundle = m[1] === 'base' ? 'base' : m[1].replace('-', ':');
  for (const n of m[2].matchAll(/`([^`]+)`/g)) RECORD.set(n[1], bundle);
}

/** The v1.1 keys of docs/art-release/terrain/NAMES.md ("<0|1>" = the 2 water frames). */
const V11 = new Set(
  [...readFileSync(new URL('../../docs/art-release/terrain/NAMES.md', import.meta.url), 'utf8').matchAll(/^\| `([^`]+)` \|/gm)].flatMap((m) =>
    m[1].endsWith('.<0|1>') ? [0, 1].map((f) => m[1].replace('<0|1>', String(f))) : [m[1]],
  ),
);

/**
 * Terrain keys the game draws with no terrain art, and why (none today: every terrain key has art).
 * @type {Record<string, string>}
 */
const FALLBACKS = {};

describe('terrain release art → game sprite keys', () => {
  it('has the 111 files of the production record and the 264 of NAMES.md (v1.1), every one a terrain key', () => {
    expect(V11.size).toBe(264);
    expect(ART.size).toBe(111 + V11.size);
    expect([...RECORD.keys()].sort()).toEqual([...ART.keys()].filter((k) => !V11.has(k)).sort());
    for (const name of ART.keys()) expect(isTerrainKey(name), name).toBe(true);
    // the v1.1 keys are exactly the keys with a v1.1 bundle
    expect([...ART.keys()].filter((k) => v11Bundle(k) !== null).sort()).toEqual([...V11].sort());
  });

  it('every terrain key the game draws has its art (or a deliberate fallback)', () => {
    const terrainKeys = [...holders.keys()].filter(isTerrainKey);
    expect(terrainKeys.length).toBe(375);
    const missing = terrainKeys.filter((k) => !ART.has(k) && !(k in FALLBACKS));
    expect(missing).toEqual([]);
  });

  it('no art is left unused: each file is held by the bundle its record names (base, its region, its season)', () => {
    for (const [name, bundle] of RECORD) expect(holders.get(name), name).toEqual([bundle]);
    // v1.1: base (island shore, banks, earth / ruin / wall variants, sand and path plateaus), the
    // desert (its shore and plateau), the mountains (stone variants), autumn and winter (lips, forest, mountains)
    const where = (k) => holders.get(k);
    for (const k of V11) expect(where(k)?.length, k).toBe(1);
    expect(where('tile.shore.5.0')).toEqual(['base']);
    expect(where('tile.bank.inner.ne.1')).toEqual(['base']);
    expect(where('tile.shore-desert.15.1')).toEqual(['region:desert']);
    expect(where('face.desert.top.8')).toEqual(['region:desert']);
    expect(where('face.stone.mid.4.v2')).toEqual(['region:mountains']);
    expect(where('face.sand.mid-base.8')).toEqual(['base']);
    expect(where('autumn.mountains.pine')).toEqual(['season:autumn']);
    expect(where('winter.face.earth.top.8.v1')).toEqual(['season:winter']);
    const unused = [...ART.keys()].filter((k) => !holders.has(k));
    expect(unused).toEqual([]);
  });

  it('v1.1 water edges: the 4-neighbour mask (N 1, E 2, S 4, W 8) and the corners no side piece covers', () => {
    const at = (cells) => (dx, dy) => cells.includes(`${dx},${dy}`);
    expect(waterAround(at([]))).toEqual({ mask: 0, corners: [] });
    expect(waterAround(at(['0,-1']))).toEqual({ mask: 1, corners: [] });
    expect(waterAround(at(['1,0', '0,1']))).toEqual({ mask: 6, corners: [] });
    expect(waterAround(at(['0,-1', '1,0', '0,1', '-1,0']))).toEqual({ mask: 15, corners: [] });
    // a diagonal next to a water side is drawn by the side piece
    expect(waterAround(at(['0,-1', '1,-1', '-1,-1']))).toEqual({ mask: 1, corners: [] });
    // only a diagonal: an inner corner; a side and the opposite diagonal: both
    expect(waterAround(at(['1,1']))).toEqual({ mask: 0, corners: ['se'] });
    expect(waterAround(at(['0,-1', '1,1']))).toEqual({ mask: 1, corners: ['se'] });
    expect(waterAround(at(['1,-1', '-1,1']))).toEqual({ mask: 0, corners: ['ne', 'sw'] });
  });

  it('v1.1 water-edge pieces: shore tiles replace the sand (one piece), bank overlays stack on grass', () => {
    expect(waterEdgePieces('shore', { mask: 5, corners: [] })).toEqual({ base: 'tile.shore.5', overlays: [], fallback: false });
    expect(waterEdgePieces('shore-desert', { mask: 0, corners: ['nw'] })).toEqual({ base: 'tile.shore-desert.inner.nw', overlays: [], fallback: false });
    // a side and the opposite diagonal: the side piece, the corner stays plain (listed)
    expect(waterEdgePieces('shore', { mask: 1, corners: ['se'] })).toEqual({ base: 'tile.shore.1', overlays: [], fallback: true });
    expect(waterEdgePieces('shore', { mask: 0, corners: ['ne', 'sw'] })).toEqual({ base: null, overlays: [], fallback: true });
    expect(waterEdgePieces('bank', { mask: 1, corners: ['se'] })).toEqual({ base: null, overlays: ['tile.bank.1', 'tile.bank.inner.se'], fallback: false });
    expect(waterEdgePieces('bank', { mask: 0, corners: ['ne', 'sw'] })).toEqual({ base: null, overlays: ['tile.bank.inner.ne', 'tile.bank.inner.sw'], fallback: false });
    // every piece the selection can name has its 2 frames
    for (const kind of ['shore', 'shore-desert', 'bank']) {
      for (let mask = 0; mask < 16; mask++) {
        for (const corners of [[], ['ne'], ['se'], ['sw'], ['nw']]) {
          const p = waterEdgePieces(kind, { mask, corners });
          for (const k of [p.base, ...p.overlays].filter(Boolean)) for (const f of [0, 1]) expect(ART.has(`${k}.${f}`), `${k}.${f}`).toBe(true);
        }
      }
    }
  });

  it('v1.1 cliff band variants: a third each per tile (plateaus: a half, .v1 only), release only', () => {
    const counts = { '': 0, '.v1': 0, '.v2': 0 };
    for (let h = 0; h < 3000; h++) counts[faceVariant(h, 'earth', true)]++;
    expect(counts).toEqual({ '': 1000, '.v1': 1000, '.v2': 1000 });
    for (const mat of ['earth', 'ruin', 'wall', 'stone']) {
      for (const v of ['.v1', '.v2']) for (const part of ['top', 'mid', 'mid-base', 'top-base']) for (const h of [4, 8]) expect(ART.has(`face.${mat}.${part}.${h}${v}`)).toBe(true);
    }
    // the plateau faces have a .v1 only: half each (hash % 2), no .v2
    const plateau = { '': 0, '.v1': 0 };
    for (let h = 0; h < 3000; h++) plateau[faceVariant(h, 'desert', true)]++;
    expect(plateau).toEqual({ '': 1500, '.v1': 1500 });
    for (const mat of ['sand', 'desert', 'path']) {
      for (const part of ['top', 'mid', 'mid-base', 'top-base']) for (const h of [4, 8]) expect(ART.has(`face.${mat}.${part}.${h}.v1`)).toBe(true);
      expect(ART.has(`face.${mat}.top.8.v2`)).toBe(false);
    }
    expect(holders.get('face.desert.mid.8.v1')).toEqual(['region:desert']);
    expect(holders.get('face.path.top-base.4.v1')).toEqual(['base']);
    for (let h = 0; h < 9; h++) expect(faceVariant(h, 'earth', false)).toBe('');
  });

  it('v1.1 plateau faces: raised sand, desert sand and paths get their own face (release only)', () => {
    expect(faceMaterial('sand', 'island', true)).toBe('sand');
    expect(faceMaterial('sand', 'desert', true)).toBe('desert');
    expect(faceMaterial('path', 'plains', true)).toBe('path');
    expect(faceMaterial('other', 'mountains', true)).toBe('stone');
    expect(faceMaterial('ruin', 'mountains', true)).toBe('ruin');
    expect(faceMaterial('wall', undefined, true)).toBe('wall');
    expect(faceMaterial('sand', 'desert', false)).toBe('earth');
    expect(faceMaterial('path', 'mountains', false)).toBe('stone');
    for (const mat of ['sand', 'desert', 'path']) for (const part of ['top', 'mid', 'mid-base', 'top-base']) for (const h of [4, 8]) expect(ART.has(`face.${mat}.${part}.${h}`)).toBe(true);
  });

  it('v1.1 autumn: the forest and the mountains change (ground, pines, stone lips), and the lips of the cliff variants follow autumn and winter', () => {
    const autumn = releaseSeasonKeys('autumn');
    for (const k of ['forest.grass.0', 'forest.grass.3', 'mountains.snow.2', 'forest.pine', 'mountains.pine', 'face.stone.top.8', 'face.stone.top-base.4.v2', 'face.earth.top.8.v1']) expect(autumn).toContain(k);
    for (const k of autumn) expect(holders.get(`autumn.${k}`), k).toEqual(['season:autumn']);
    for (const k of releaseSeasonKeys('winter')) expect(holders.get(`winter.${k}`), k).toEqual(['season:winter']);
    expect(releaseSeasonKeys('spring')).toEqual([]);
    expect(releaseSeasonKeys('summer')).toEqual([]);
    // every v1.1 season art file is a key some season uses
    const used = new Set([...autumn.map((k) => `autumn.${k}`), ...releaseSeasonKeys('winter').map((k) => `winter.${k}`)]);
    for (const k of V11) if (/^(autumn|winter)\./.test(k)) expect(used.has(k), k).toBe(true);
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

  it('with the release hero, villagers, enemies, objects and the v1.1 terrain the base atlas of the release art stays within 2048 × 1024', () => {
    const release = new Map([...sizes('hero'), ...sizes('npc'), ...sizes('enemy'), ...sizes('objects'), ...ART]);
    const keys = new Set(release.keys());
    const base = [...placeholderEntries(), ...releaseHeroEntries(keys), ...releaseNpcEntries(keys), ...releaseEnemyEntries(keys), ...releaseTerrainEntries('placeholder', keys)];
    const real = base.filter((e) => release.has(e.key)).map((e) => ({ ...e, image: { width: release.get(e.key).w, height: release.get(e.key).h } }));
    expect(real.filter((e) => ART.has(e.key)).length).toBe(43 + 76 + 48 + 16 + 16);
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
    expect(indoorLight(true)).toEqual({ r: 0.72, g: 0.7, b: 0.76 });
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
