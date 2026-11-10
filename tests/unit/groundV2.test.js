import { describe, it, expect, vi } from 'vitest';
import { readdirSync, readFileSync } from 'node:fs';
import { PRIORITY, PREFIX, SEASONAL, MACRO_GROUNDS, MACRO_NAMES, CORNERS, deepMap, displayLayers, groundClass, landKey, quarterOfCorner, WATER_FRAMES, ruinRow, ruinSymbol, ruinIndex, ruinTile, ruinCellTile, edgeVariantOf, tileScheme, tileCount, calmTile } from '../../src/view/groundV2.js';

vi.mock('pixi.js', () => ({ Rectangle: class {}, Texture: class {} }));
const { REGION_ENTRIES, SEASON_ENTRIES, placeholderEntries, releaseHeroEntries, releaseNpcEntries, releaseEnemyEntries, atlasSizeFor, tallestFirstOrder, mustKeepSize, ART_SCALE } = await import('../../src/view/assets/placeholderPack.js');
const { releaseTerrainEntries, GROUND_RUIN_BUNDLE } = await import('../../src/view/assets/terrainArt.js');

// gfx W1: ground v2 on the dual grid (src/view/groundV2.js), per docs/art-release-v2/terrain/NAMES.md
// and tools/terrain_v2/render_ref.py.
const V2 = new URL('../../src/art-release-v2/terrain/', import.meta.url);
const sizes = (dir) =>
  new Map(
    readdirSync(dir)
      .filter((f) => f.endsWith('.png'))
      .map((f) => {
        const b = readFileSync(new URL(f, dir));
        return [f.slice(0, -4), { w: b.readUInt32BE(16), h: b.readUInt32BE(20) }];
      }),
  );
const ART = sizes(V2);
const has = (k) => ART.has(k);

const tile = (cls, deep = [false, false, false, false]) => displayLayers({ cls, deep, waterVariant: 0, edgeVariant: (c) => (c === 'ruin' ? 7 : 1), pick: () => '2', macro: () => null });

describe('ground v2: classes, keys, priority', () => {
  it('maps the map grounds to classes like the reference (desert sand, region grasses, others on the cell grid)', () => {
    expect(groundClass('grass', 'plains')).toBe('plains');
    expect(groundClass('grass', 'forest')).toBe('moss');
    expect(groundClass('grass', 'mountains')).toBe('snow');
    expect(groundClass('grass', 'lake')).toBe('lake');
    expect(groundClass('grass', 'island')).toBe('grass');
    expect(groundClass('grass', 'desert')).toBe('grass');
    expect(groundClass('sand', 'desert')).toBe('dsand');
    expect(groundClass('sand', 'lake')).toBe('sand');
    expect(groundClass('water', 'lake')).toBe('water');
    expect(groundClass('other', 'plains')).toBeNull();
    expect(PRIORITY).toEqual(['ruin', 'path', 'dsand', 'sand', 'snow', 'moss', 'lake', 'plains', 'grass']);
  });

  /** Every name the engine can ask of a ground (groundV2.js A / B / C; the same in every season). */
  const namesOf = (cls) => {
    const names = range(tileCount(cls)).map(String);
    if (tileScheme(cls) === 'A') names.push(...MACRO_NAMES.flatMap((m) => range(4).map((q) => `${m}.${q}`)));
    for (let m = 1; m <= 14; m++) for (const v of cls === 'ruin' ? range(11) : [0, 1]) names.push(`edge.${m}.${v}`);
    return names;
  };

  it('every land key the engine can name exists in the v2 art: 16 tiles (ruin 66), 8 pictures × 4 (A only), 14 masks × 2 (ruin × 11 rows)', () => {
    let n = 0;
    for (const cls of Object.keys(PREFIX)) {
      for (const name of namesOf(cls)) {
        expect(has(landKey(cls, name)), landKey(cls, name)).toBe(true);
        n++;
      }
    }
    expect(landKey('sand', '0')).toBe('tile.sand');
    expect(landKey('ruin', '65')).toBe('tile.ruin.65');
    expect(landKey('dsand', '0')).toBe('desert.sand.0');
    expect(tileCount('grass') + tileCount('sand') + tileCount('ruin')).toBe(16 + 16 + 66);
    // round 5 removed the 64 sand tiles
    expect(has('tile.sand.16') || has('desert.sand.16')).toBe(false);
    // 8 A grounds × (16 + 32 + 28) + the ruin floor 66 + 154
    expect(n).toBe(8 * 76 + 220);
    for (const f of range(WATER_FRAMES)) {
      for (const k of ['tile.water', 'tile.water.v1', 'tile.water.deep', 'tile.water.deep.v1']) expect(has(`${k}.${f}`), `${k}.${f}`).toBe(true);
      for (let m = 1; m <= 14; m++) expect(has(`tile.water.deep.edge.${m}.${f}`) && has(`tile.water.foam.${m}.${f}`)).toBe(true);
    }
  });

  it('the seasons: autumn and winter have every key of the 4 seasonal grounds (16 calm tiles + 8 pictures + edges)', () => {
    for (const season of ['autumn', 'winter']) {
      for (const cls of SEASONAL) for (const name of namesOf(cls)) expect(has(`${season}.${landKey(cls, name)}`), `${season}.${landKey(cls, name)}`).toBe(true);
    }
    expect(namesOf('grass').length).toBe(16 + 32 + 28);
    // round 4 removed the 64 snow tiles of winter and the 3×3 macro3
    expect(has('winter.tile.grass.16')).toBe(false);
    expect(has('mountains.snow.16')).toBe(false);
    expect(has('tile.grass.macro3.4')).toBe(false);
    expect(has('winter.tile.grass.macro8.3')).toBe(true);
  });

  it('no ground has art the engine never names (macro pieces only where it places them)', () => {
    const named = new Set(Object.keys(PREFIX).flatMap((cls) => [...namesOf(cls).map((n) => landKey(cls, n)), ...(SEASONAL.includes(cls) ? ['autumn', 'winter'].flatMap((s) => namesOf(cls).map((n) => `${s}.${landKey(cls, n)}`)) : [])]));
    const ground = new RegExp(`^(?:autumn\\.|winter\\.)?(?:${Object.values(PREFIX).map((p) => p.replace('.', '\\.')).join('|')})(?:\\.(?:\\d+|macro\\d?\\.\\d|edge\\.\\d+\\.\\d+))?$`);
    // (autumn.mountains.snow.* is the v1.1 autumn of the mountains, not drawn by the v2 ground)
    const extra = [...ART.keys()].filter((k) => ground.test(k) && !named.has(k) && !k.startsWith('autumn.mountains.snow.'));
    expect(extra).toEqual([]);
    expect(MACRO_GROUNDS).toEqual(['grass', 'plains', 'lake', 'moss', 'path', 'snow', 'sand', 'dsand']);
  });
});

function range(n) {
  return [...Array(n).keys()];
}

describe('ground v2: the layers of a display tile', () => {
  it('one ground: its full tile (a variant, or a macro piece when all 4 corners are that ground)', () => {
    expect(tile(['plains', 'plains', 'plains', 'plains'])).toEqual([{ key: 'plains.grass.2', anim: false }]);
    expect(displayLayers({ cls: ['path', 'path', 'path', 'path'], deep: [], waterVariant: 0, edgeVariant: 0, pick: () => '0', macro: () => 'macro.3' })).toEqual([{ key: 'tile.path.macro.3', anim: false }]);
  });

  it('two lands: the lower as a full tile, the higher as its edge with mask = its corners (NW 1, NE 2, SW 4, SE 8)', () => {
    // grass NW + NE over path: grass mask 3
    expect(tile(['grass', 'grass', 'path', 'path'])).toEqual([
      { key: 'tile.path.2', anim: false },
      { key: 'tile.grass.edge.3.1', anim: false },
    ]);
  });

  it('three lands: low to high, each mask counts the corners at or above its priority', () => {
    // ruin (low), sand, plains (high)
    expect(tile(['ruin', 'sand', 'plains', 'sand']).map((l) => l.key)).toEqual(['tile.ruin.2', 'tile.sand.edge.14.1', 'plains.grass.edge.4.1']);
  });

  it('water: shallow, deep when all 4 corners are deep, deep edge when mixed, foam over land corners, then the land', () => {
    expect(tile(['water', 'water', 'water', 'water'])).toEqual([{ key: 'tile.water', anim: true }]);
    expect(tile(['water', 'water', 'water', 'water'], [true, true, true, true])).toEqual([{ key: 'tile.water.deep', anim: true }]);
    expect(tile(['water', 'water', 'water', 'water'], [true, false, true, false]).map((l) => l.key)).toEqual(['tile.water', 'tile.water.deep.edge.5']);
    expect(tile(['sand', 'water', 'lake', 'water'])).toEqual([
      { key: 'tile.water', anim: true },
      { key: 'tile.water.foam.5', anim: true },
      { key: 'tile.sand.edge.5.1', anim: false },
      { key: 'lake.grass.edge.4.1', anim: false },
    ]);
    expect(displayLayers({ cls: ['water', 'water', 'water', 'water'], deep: [false, false, false, false], waterVariant: 1, edgeVariant: 0, pick: () => '0', macro: () => null })[0].key).toBe('tile.water.v1');
  });

  it('cells that cannot blend show their own quarter: NW corner → its SE quarter, ...', () => {
    expect(range(4).map(quarterOfCorner)).toEqual(['se', 'sw', 'ne', 'nw']);
    expect(CORNERS.map((c) => c[2])).toEqual([1, 2, 4, 8]);
  });

  it('deep water forms areas of 2×2 or more: a 1-cell trench of deep water stays shallow', () => {
    // a channel 5 cells of water wide (land at x 0 and 6): only its middle column is 3 cells from land -> a trench, shallow
    const h = 12;
    const d = deepMap(7, h, (x) => x > 0 && x < 6);
    expect([...d].every((v) => v === 0)).toBe(true);
    // 6 cells wide: the 2 middle columns are deep
    const d2 = deepMap(8, h, (x) => x > 0 && x < 7);
    expect([d2[5 * 8 + 3], d2[5 * 8 + 4], d2[5 * 8 + 2]]).toEqual([1, 1, 0]);
  });

  it('deep water: no land within 2 cells (Chebyshev)', () => {
    const grid = ['~~~~~~~', '~~~~~~~', '~~~~~~~', '~~~~~~~', '~~~~~~#'];
    const d = deepMap(7, 5, (x, y) => grid[y][x] === '~');
    const at = (x, y) => d[y * 7 + x];
    expect(at(0, 0)).toBe(1);
    expect(at(4, 2)).toBe(0); // (6,4) is 2 away
    expect(at(3, 1)).toBe(1); // 3 away
    expect(at(6, 4)).toBe(0); // land
  });
});

describe('ground v2 rounds 2-5: the 2 ways of picking a tile', () => {
  const hash = (x, y) => {
    let h = (x * 374761393 + y * 668265263) >>> 0;
    h = Math.imul(h ^ (h >>> 13), 1274126177) >>> 0;
    return (h ^ (h >>> 16)) >>> 0;
  };

  it('which grounds: A every ground but the ruin floor (round 5); C the ruin floor; the same in every season', () => {
    expect(['grass', 'plains', 'lake', 'moss', 'path', 'snow', 'sand', 'dsand'].map(tileScheme)).toEqual(Array(8).fill('A'));
    expect(tileScheme('ruin')).toBe('C');
    expect(MACRO_GROUNDS.every((g) => tileScheme(g) === 'A')).toBe(true);
    expect(MACRO_NAMES).toEqual(['macro', 'macro2', 'macro3', 'macro4', 'macro5', 'macro6', 'macro7', 'macro8']);
  });

  it('A: the calm tile is hash(i + 3, j + 11) % 16, all 16 used', () => {
    expect(calmTile(5, 7, hash)).toBe(hash(8, 18) % 16);
    const seen = new Set();
    for (let i = 0; i < 40; i++) for (let j = 0; j < 40; j++) seen.add(calmTile(i, j, hash));
    expect(seen.size).toBe(16);
  });

  it('C: the ruin floor by its row phase (32·j mod 11) and its column symbols: 66 tiles, neighbouring lines never alike', () => {
    expect(range(12).map(ruinRow)).toEqual([0, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0]);
    expect(ruinRow(-1)).toBe(1); // (as Python's % for the row above the map)
    for (let j = 0; j < 40; j++) expect(ruinRow(j)).toBe((32 * j) % 11);
    // n = 6R + 2W + (E if E < W else E − 1): the 6 pairs W ≠ E in order
    expect([[0, 1], [0, 2], [1, 0], [1, 2], [2, 0], [2, 1]].map(([w, e]) => ruinIndex(0, w, e))).toEqual([0, 1, 2, 3, 4, 5]);
    expect(ruinIndex(10, 2, 1)).toBe(65);
    const seen = new Set();
    for (let i = -4; i < 600; i++) {
      const w = ruinSymbol(i, hash);
      const e = ruinSymbol(i + 1, hash);
      expect([0, 1, 2]).toContain(w);
      expect(e, `lines ${i} and ${i + 1}`).not.toBe(w);
      // the symbol of an even line is hash(i / 2, 7) % 3
      if (i % 2 === 0) expect(w).toBe(hash(i / 2, 7) % 3);
      for (let j = 0; j < 11; j++) seen.add(ruinTile(i, j, hash));
      // the tile to the east starts with the symbol this one ends with
      expect(Math.floor((ruinTile(i + 1, 3, hash) % 6) / 2)).toBe(e);
    }
    expect(seen.size).toBe(66);
    expect(Math.max(...seen)).toBe(65);
    // its overlay over water takes the row phase; the other grounds 0 / 1
    expect(edgeVariantOf('ruin', 5, 3, hash)).toBe(ruinRow(3));
    expect(range(50).every((i) => [0, 1].includes(edgeVariantOf('grass', i, 2, hash)))).toBe(true);
    // a cell's own tile (cell grid, half a tile up and left): its courses meet the display tiles' ((32·y − 16) mod 11)
    for (let y = 0; y < 30; y++) expect(Math.floor(ruinCellTile(4, y, hash) / 6)).toBe((32 * y - 16 + 11 * 100) % 11);
    for (let y = 0; y < 30; y++) expect((Math.floor(ruinCellTile(4, y, hash) / 6) + 16) % 11).toBe(ruinRow(y));
  });
});

describe('ground v2: bundles and memory', () => {
  const release = new Map([...sizes(new URL('../../src/art-release/hero/', import.meta.url)), ...sizes(new URL('../../src/art-release/npc/', import.meta.url)), ...sizes(new URL('../../src/art-release/enemy/', import.meta.url)), ...sizes(new URL('../../src/art-release/objects/', import.meta.url)), ...ART]);
  const keys = new Set(release.keys());
  const base = [...placeholderEntries(), ...releaseHeroEntries(keys), ...releaseNpcEntries(keys), ...releaseEnemyEntries(keys), ...releaseTerrainEntries('placeholder', keys)];
  const bundles = new Map([
    ['base', base],
    ['common:ground', releaseTerrainEntries('common:ground', keys)],
    [GROUND_RUIN_BUNDLE, releaseTerrainEntries(GROUND_RUIN_BUNDLE, keys)],
    ...Object.entries({ ...REGION_ENTRIES, ...SEASON_ENTRIES }).map(([n, make]) => [n, [...make(), ...releaseTerrainEntries(n, keys)]]),
  ]);
  const held = new Set([...bundles.values()].flatMap((es) => es.map((e) => e.key)));

  it('every v2 ground key the dual grid uses has a slot in a bundle (only the v1.1 shore pieces are left out)', () => {
    const unused = [...ART.keys()].filter((k) => !held.has(k));
    expect(unused.every((k) => /^tile\.(shore|shore-desert|bank)\./.test(k)), unused.filter((k) => !/^tile\.(shore|shore-desert|bank)\./.test(k)).join(' ')).toBe(true);
    for (const es of bundles.values()) {
      for (const e of es) {
        const a = ART.get(e.key);
        if (a && mustKeepSize(e.anchor)) expect([a.w, a.h], e.key).toEqual([e.rows[0].length * ART_SCALE, e.rows.length * ART_SCALE]);
      }
    }
  });

  it('each ground key is in the bundle that is loaded where it is drawn: island grounds, ruin floor and water with the base, the ruin floor\'s edges over water with their chunks, a region\'s with the region, a season\'s with the season', () => {
    const where = (k) => [...bundles].filter(([, es]) => es.some((e) => e.key === k)).map(([n]) => n);
    const home = { grass: 'base|common:ground', sand: 'base|common:ground', path: 'base|common:ground', ruin: 'base|common:ground', plains: 'region:plains', lake: 'region:lake', moss: 'region:forest', snow: 'region:mountains', dsand: 'region:desert' };
    for (const cls of Object.keys(PREFIX)) {
      const names = [...range(tileCount(cls)).map(String), ...(tileScheme(cls) === 'A' ? MACRO_NAMES.map((m) => `${m}.3`) : []), ...(cls === 'ruin' ? [] : ['edge.1.0', 'edge.14.1'])];
      for (const n of names) {
        const w = where(landKey(cls, n));
        expect(w.length, landKey(cls, n)).toBe(1);
        expect(home[cls].split('|'), landKey(cls, n)).toContain(w[0]);
      }
      if (!SEASONAL.includes(cls)) continue;
      for (const season of ['autumn', 'winter']) {
        for (const n of [...range(16).map(String), ...MACRO_NAMES.map((m) => `${m}.0`), 'edge.1.0', 'edge.14.1']) expect(where(`${season}.${landKey(cls, n)}`), `${season}.${landKey(cls, n)}`).toEqual([`season:${season}`]);
      }
    }
    expect(where('tile.water.foam.14.3')).toEqual(['common:ground']);
    // the ruin floor's edges over water: their own bundle, loaded where the ruin floor meets water
    for (let m = 1; m <= 14; m++) for (const r of range(11)) expect(where(`tile.ruin.edge.${m}.${r}`)).toEqual([GROUND_RUIN_BUNDLE]);
  });

  it('atlas sizes with the v2 ground: the ruin floor\'s edges 512 × 512, a region at most 512 × 512, a season at most 1024 × 512', () => {
    const withImage = (es) => es.filter((e) => release.has(e.key)).map((e) => ({ ...e, image: { width: release.get(e.key).w, height: release.get(e.key).h } }));
    expect(atlasSizeFor(withImage(bundles.get(GROUND_RUIN_BUNDLE)))).toEqual({ width: 512, height: 512 });
    for (const n of Object.keys({ ...REGION_ENTRIES, ...SEASON_ENTRIES })) {
      const size = atlasSizeFor(withImage(bundles.get(n)));
      expect(size.width * size.height, n).toBeLessThanOrEqual(n.startsWith('season:') ? 1024 * 512 : 512 * 512);
    }
  });

  it('the island grounds and the water fit in the base atlas, packed tallest first: still 2048 × 1024, no second atlas', () => {
    const withImage = (es) => es.filter((e) => release.has(e.key)).map((e) => ({ ...e, image: { width: release.get(e.key).w, height: release.get(e.key).h } }));
    const g = releaseTerrainEntries('common:ground', keys);
    expect(g.length).toBe(414); // the island grass, sand, path and ruin floor tiles, picture pieces and edges, and the water, less the keys v1 has too
    const packed = tallestFirstOrder(withImage([...base, ...g]));
    expect(atlasSizeFor(packed)).toEqual({ width: 2048, height: 1024 });
    // tallest first, the given order kept among equals; nothing lost
    expect(packed.length).toBe(withImage(base).length + g.length);
    for (let i = 1; i < packed.length; i++) expect(packed[i].image.height).toBeLessThanOrEqual(packed[i - 1].image.height);
    const tiles = packed.filter((e) => e.image.height === 32).map((e) => e.key);
    expect(tiles.filter((k) => g.some((e) => e.key === k))).toEqual(g.map((e) => e.key));
  });

  it('without the v2 ground nothing is listed for the base atlas beyond v1 (the v1 atlas keeps its layout)', () => {
    const v1 = new Set(sizes(new URL('../../src/art-release/terrain/', import.meta.url)).keys());
    expect(releaseTerrainEntries('common:ground', v1)).toEqual([]);
  });
});
