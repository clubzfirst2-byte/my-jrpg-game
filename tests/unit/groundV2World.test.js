import { describe, it, expect } from 'vitest';
import { readdirSync } from 'node:fs';
import { GameView, CHUNK } from '../../src/view/gameView.js';
import { createGameState, MAPS } from '../../src/game/state.js';
import { Ground, Shape, southEdgeHeight } from '../../src/game/world/tilemap.js';
import { regionAt } from '../../src/game/world/world.js';
import { inSeason } from '../../src/game/env/weather.js';
import { REGION_ENTRIES, SEASON_ENTRIES, placeholderEntries } from '../../src/view/assets/placeholderPack.js';
import { GROUND_RUIN_BUNDLE, ISLAND_EDGES_BUNDLE, ISLAND_STEPS_BUNDLE, releaseTerrainEntries, v2BundleParts } from '../../src/view/assets/terrainArt.js';
import { MACRO_GROUNDS, MACRO_NAMES, macroPlacement, tileScheme } from '../../src/view/groundV2.js';

// gfx W1 round 3: the whole world map, chunk by chunk, through the same code that draws the v2 ground
// (GameView.groundPiecesV2 and the raised cells' surfaceKey), in every season: every key it asks for is
// in the v2 art AND in a bundle that is loaded for that chunk (base + its regions' + the season's + the
// ruin floor's edges where the ruin floor meets water). No key is ever missing.

const ART = new Set(readdirSync(new URL('../../src/art-release-v2/terrain/', import.meta.url)).filter((f) => f.endsWith('.png')).map((f) => f.slice(0, -4)));
const overrides = new Map([...ART].map((k) => [k, `${k}.png`]));
const keysOf = (/** @type {{ key: string }[]} */ es) => es.map((e) => e.key);
const BASE = new Set([...keysOf(placeholderEntries()), ...keysOf(releaseTerrainEntries('placeholder', overrides)), ...keysOf(releaseTerrainEntries('common:ground', overrides))]);
const BUNDLE = new Map([
  ...[GROUND_RUIN_BUNDLE, ISLAND_EDGES_BUNDLE, ISLAND_STEPS_BUNDLE].map((n) => [n, new Set(keysOf(releaseTerrainEntries(n, overrides)))]),
  // (with the v2 ground, as main.js registers them: a region's own ground, and each seasonal
  // ground's autumn / winter art, are bundles of their own — terrainArt.v2BundleParts)
  ...Object.entries({ ...REGION_ENTRIES, ...SEASON_ENTRIES }).flatMap(([n, make]) => {
    const all = [...keysOf(make()), ...keysOf(releaseTerrainEntries(n, overrides))];
    const parts = v2BundleParts(n);
    return parts ? parts.map(([part, keep]) => [part, new Set(all.filter(keep))]) : [[n, new Set(all)]];
  }),
]);

/** A view of the world with only what the ground needs (no renderer), the v2 art "loaded". */
function worldView() {
  const state = createGameState(MAPS.world);
  const v = Object.create(GameView.prototype);
  const assets = { hasTexture: (k) => ART.has(k), isLoaded: () => true, load: async () => {}, unload: () => {}, builders: new Map([...BUNDLE.keys()].map((n) => [n, () => null])), version: 0 };
  Object.assign(v, {
    map: state.map,
    regions: state.regions,
    assets,
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
  });
  v.sandUnderTrees = new Set(
    (state.map.objects ?? []).filter((o) => o.type === 'tree' && state.map.ground[o.ty * state.map.width + o.tx] === Ground.GRASS && regionAt(v.regions, o.tx, o.ty)?.id === 'desert').map((o) => o.ty * state.map.width + o.tx),
  );
  return v;
}

describe('ground v2 on the world map: no key is ever missing', () => {
  for (const season of ['summer', 'autumn', 'winter']) {
    it(`${season}: every ground key of every chunk is in the art and in a bundle loaded for that chunk`, () => {
      const v = worldView();
      v.updateSeason(inSeason(0, season));
      expect(v.season).toBe(season);
      const map = v.map;
      const missing = new Set();
      const unloaded = new Set();
      const drawn = new Set();
      let ruinShore = 0;
      let steps = 0;
      for (let cy = 0; cy * CHUNK < map.height; cy++) {
        for (let cx = 0; cx * CHUNK < map.width; cx++) {
          const bundles = v.chunkBundles(cx, cy);
          if (bundles.includes(GROUND_RUIN_BUNDLE)) ruinShore++;
          const loaded = (k) => BASE.has(k) || bundles.some((b) => BUNDLE.get(b)?.has(k));
          const keys = [];
          for (const p of v.groundPiecesV2(cx, cy)) {
            if (p.anim) for (let f = 0; f < 4; f++) keys.push(`${p.key}.${f}`);
            else keys.push(v.seasonal(p.key));
          }
          // raised cells (drawn by their rows on the cell grid)
          for (let y = cy * CHUNK; y < Math.min(map.height, (cy + 1) * CHUNK); y++) {
            for (let x = cx * CHUNK; x < Math.min(map.width, (cx + 1) * CHUNK); x++) {
              const c = v.groundClassAt(x, y);
              const h = map.elev[y * map.width + x];
              if (h > 0 && c && c !== 'water') keys.push(v.seasonal(v.surfaceKey(x, y)));
              // the step pieces (NAMES.md 2b), as buildChunk asks for them
              if (h > 0 && map.shape[y * map.width + x] !== Shape.RAMP_N) {
                const lower = (nx, ny) => nx >= 0 && ny >= 0 && nx < map.width && ny < map.height && map.elev[ny * map.width + nx] < h;
                const north = y > 0 && southEdgeHeight(map, x, y - 1) < h;
                const step = v.stepPieces(x, y, h, north, lower(x + 1, y), lower(x - 1, y));
                for (const k of step?.rims ?? []) keys.push(v.seasonal(k));
                if (lower(x + 1, y)) {
                  const shade = v.stepShadeKey(x, y);
                  if (shade) keys.push(v.seasonal(shade));
                  if (shade) steps++;
                }
                if (step?.rims.length) steps++;
              }
            }
          }
          for (const k of keys) {
            // only the v2 ground's keys (v1 cell-grid tiles such as wood floors are the v1 pack's)
            if (!/^(?:autumn\.|winter\.)?(?:tile\.(?:grass|sand|path|ruin|water)|plains\.grass|lake\.grass|forest\.grass|mountains\.snow|desert\.sand)(?:\.|$)/.test(k)) continue;
            drawn.add(k);
            if (!ART.has(k)) missing.add(k);
            else if (!loaded(k)) unloaded.add(`${k} @${cx},${cy}`);
          }
        }
      }
      expect([...missing]).toEqual([]);
      expect([...unloaded]).toEqual([]);
      // a border loads the neighbour's ground, not all of its art: the mountains' south row of chunks (y 64-95) meets the forest at y = 96
      const border = v.chunkBundles(5, 2);
      expect(border).toEqual(expect.arrayContaining(['region:mountains', 'ground:forest']));
      expect(border).not.toContain('ground:mountains'); // (the mountains' ground stays in its region's bundle)
      expect(border).not.toContain('region:forest');
      // a season's ground art only where that ground is: none in the mountains' heart (snow has no seasons), the plains' in the plains
      if (season !== 'summer') {
        expect(v.chunkBundles(5, 1).filter((b) => b.startsWith(`season:${season}:`))).toEqual([]);
        expect(v.chunkBundles(1, 3)).toContain(`season:${season}:plains`);
      }
      expect([...v.v2Missing]).toEqual([]);
      // the walk covers every way of picking a tile
      const any = (re) => [...drawn].some((k) => re.test(k));
      expect(any(/^tile\.ruin\.(?:[1-9]|\d\d)$/)).toBe(true);
      expect(any(/^tile\.ruin\.edge\.\d+\.(?:[2-9]|10)$/)).toBe(true);
      expect(ruinShore).toBeGreaterThan(0);
      expect(any(/^desert\.sand\.(?:1[0-5]|[4-9])$/)).toBe(true);
      expect(any(/^desert\.sand\.macro\d?\.\d$/)).toBe(true);
      expect(any(/^tile\.sand\.macro\d?\.\d$/)).toBe(true);
      expect(any(/^mountains\.snow\.(?:1[0-5]|[1-9])$/)).toBe(true);
      expect(any(/^mountains\.snow\.macro\d?\.\d$/)).toBe(true);
      // rounds 4-6: no 3×3 piece, 32 calm tiles (no 64 snow / sand tiles any more)
      expect(any(/\.macro3\.[4-8]$/)).toBe(false);
      expect(any(/^(?:winter\.(?:tile|plains|lake|forest)\.grass|mountains\.snow|tile\.sand|desert\.sand)\.(?:3[2-9]|[4-9]\d)$/)).toBe(false);
      expect(any(/^tile\.water\.foam\./)).toBe(true);
      // the seasonal grounds: their season's calm tiles and pictures (all 8)
      const p = season === 'summer' ? '' : `${season}\\.`;
      for (const m of MACRO_NAMES) expect(any(new RegExp(`^${p}(?:tile|plains|lake|forest)\\.grass\\.${m}\\.[0-3]$`)), `${season} ${m}`).toBe(true);
      expect(any(new RegExp(`^${p}tile\\.grass\\.(?:1[0-5]|[1-9])$`))).toBe(true);
      expect(any(/^tile\.path\.macro/)).toBe(true);
      // (no grass-like key without the season's prefix in autumn / winter)
      if (season !== 'summer') expect(any(/^(?:tile|plains|lake|forest)\.grass\./)).toBe(false);
      // the ruin floor (C) never gets a picture
      expect(any(/^tile\.ruin\.macro/)).toBe(false);
      expect(drawn.size).toBeGreaterThan(500);
      // rounds 7-8: steps drawn with their rims and shadows, edge variants 2 / 3, dunes
      expect(steps).toBeGreaterThan(100);
      expect(any(/\.step\.[1-7]\.[01]$/)).toBe(true);
      expect(any(/\.step\.shade\.[01]$/)).toBe(true);
      expect(any(/\.edge\.\d+\.[23]$/)).toBe(true);
      expect(any(/^desert\.sand\.dune[1-6]\.[0-3]$/)).toBe(true);
    });
  }
});

describe('picture placement: one function (groundV2.macroPlacement)', () => {
  const hash = (x, y) => {
    let h = (x * 374761393 + y * 668265263) >>> 0;
    h = Math.imul(h ^ (h >>> 13), 1274126177) >>> 0;
    return (h ^ (h >>> 16)) >>> 0;
  };
  const W = 150;
  const H = 120;
  /** every picture on a W × H map of one ground: NW tile "i0,j0" → its block's pieces */
  const place = (g) => {
    const ctx = { uniformBlock: () => g, hash, width: W, height: H };
    const out = new Map();
    for (let j = -3; j < H + 3; j++) {
      for (let i = -3; i < W + 3; i++) {
        const m = macroPlacement(i, j, ctx);
        if (!m) continue;
        expect(i >= 0 && j >= 0 && i < W - 1 && j < H - 1, `${i},${j} on the map`).toBe(true);
        if (!out.has(m.block)) out.set(m.block, []);
        out.get(m.block).push(m.name);
      }
    }
    return out;
  };
  it('places 2×2 pictures only on the grounds with pictures, 4 pieces each, never overlapping, all 8 numbers, none past the map\'s edge', () => {
    for (const g of ['grass', 'plains', 'lake', 'moss', 'path', 'snow', 'sand', 'dsand', 'ruin']) {
      const pics = place(g);
      expect(pics.size > 0, g).toBe(MACRO_GROUNDS.includes(g));
      expect(pics.size > 0, g).toBe(tileScheme(g) === 'A');
      for (const [id, names] of pics) {
        expect(names.map((n) => n.split('.')[1]).sort(), id).toEqual(['0', '1', '2', '3']);
        expect(new Set(names.map((n) => n.split('.')[0])).size).toBe(1);
        const [i0, j0] = id.split(',').map(Number);
        expect(i0 + 2).toBeLessThan(W);
        expect(j0 + 2).toBeLessThan(H);
      }
      if (g === 'grass') {
        expect(new Set([...pics.values()].map((n) => n[0].split('.')[0]))).toEqual(new Set(MACRO_NAMES));
        // clusters and open stretches: some blocks of 3×3 tiles have none (density noise), most have one
        const blocks = (W / 3) * (H / 3);
        expect(pics.size).toBeGreaterThan(0.25 * blocks);
        expect(pics.size).toBeLessThan(0.95 * blocks);
      }
    }
    // not on mixed ground
    expect(macroPlacement(4, 4, { uniformBlock: () => null, hash, width: W, height: H })).toBeNull();
  });

  it('no two side-by-side blocks show the same picture', () => {
    const pics = place('grass');
    const byBlock = new Map([...pics].map(([id, names]) => {
      const [i0, j0] = id.split(',').map(Number);
      // (the picture's block: offsets 0-2 from 3a, 3b)
      return [`${Math.floor(i0 / 3)},${Math.floor(j0 / 3)}`, names[0].split('.')[0]];
    }));
    let pairs = 0;
    for (const [id, name] of byBlock) {
      const [a, b] = id.split(',').map(Number);
      for (const n of [`${a + 1},${b}`, `${a},${b + 1}`]) {
        if (!byBlock.has(n)) continue;
        pairs++;
        expect(byBlock.get(n), `${id} / ${n}`).not.toBe(name);
      }
    }
    expect(pairs).toBeGreaterThan(100);
  });
});
