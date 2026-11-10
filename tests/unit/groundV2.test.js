import { describe, it, expect, vi } from 'vitest';
import { readdirSync, readFileSync } from 'node:fs';
import { PRIORITY, PREFIX, CORNERS, deepMap, displayLayers, groundClass, landKey, quarterOfCorner, WATER_FRAMES, P_TYPE1, edgesOf, wangIndex, edgeLook, EDGE_TYPES, edgeTypeOf, edgeCounts } from '../../src/view/groundV2.js';

vi.mock('pixi.js', () => ({ Rectangle: class {}, Texture: class {} }));
const { REGION_ENTRIES, placeholderEntries, releaseHeroEntries, releaseNpcEntries, releaseEnemyEntries, atlasSizeFor, tallestFirstOrder, mustKeepSize, ART_SCALE } = await import('../../src/view/assets/placeholderPack.js');
const { releaseTerrainEntries } = await import('../../src/view/assets/terrainArt.js');

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

const tile = (cls, deep = [false, false, false, false]) => displayLayers({ cls, deep, waterVariant: 0, edgeVariant: 1, pick: () => '2', macro: () => null });

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

  it('every land key the dual grid can name exists in the v2 art (bases, variants, macro, 14 masks × 2)', () => {
    for (const cls of Object.keys(PREFIX)) {
      const names = [...range(16).map(String), ...range(4).flatMap((q) => [`macro.${q}`, `macro2.${q}`]), ...range(9).map((q) => `macro3.${q}`)];
      for (const n of names) expect(has(landKey(cls, n)), landKey(cls, n)).toBe(true);
      for (let m = 1; m <= 14; m++) for (const v of [0, 1]) expect(has(landKey(cls, `edge.${m}.${v}`)), `${cls} edge ${m}.${v}`).toBe(true);
    }
    expect(landKey('sand', '0')).toBe('tile.sand');
    expect(landKey('dsand', '0')).toBe('desert.sand.0');
    for (const f of range(WATER_FRAMES)) {
      for (const k of ['tile.water', 'tile.water.v1', 'tile.water.deep', 'tile.water.deep.v1']) expect(has(`${k}.${f}`), `${k}.${f}`).toBe(true);
      for (let m = 1; m <= 14; m++) expect(has(`tile.water.deep.edge.${m}.${f}`) && has(`tile.water.foam.${m}.${f}`)).toBe(true);
    }
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

describe('ground v2 round 2: edge-matched tiles', () => {
  it('n = N + 2E + 4S + 8W; the edge ids of render_ref; the per-ground P (winter grass looks like snow)', () => {
    expect(wangIndex([1, 0, 0, 0])).toBe(1);
    expect(wangIndex([0, 1, 1, 1])).toBe(14);
    expect(edgesOf(3, 5)).toEqual([[7, 10, 3, 4], [8, 11, 4, 5], [7, 12, 3, 6], [6, 11, 2, 5]]);
    // two tiles that share an edge use the same id for it
    expect(edgesOf(3, 5)[1].slice(0, 2)).toEqual(edgesOf(4, 5)[3].slice(0, 2));
    expect(edgesOf(3, 5)[2].slice(0, 2)).toEqual(edgesOf(3, 6)[0].slice(0, 2));
    expect(P_TYPE1).toMatchObject({ grass: 10, moss: 12, sand: 50, ruin: 50, path: 10 });
    expect(edgeLook('plains', 'winter')).toBe('snow');
    expect(edgeLook('path', 'winter')).toBe('path');
    expect(edgeLook('plains', 'autumn')).toBe('plains');
    // data-driven types: today 2 per edge everywhere (type 1 with P), the index generalises to more
    expect(EDGE_TYPES.sand).toEqual({ ns: [50, 50], ew: [50, 50] });
    expect(edgeCounts('grass')).toEqual([2, 2, 2, 2]);
    // as the reference: type 1 when hash % 100 < P
    expect([edgeTypeOf('grass', 'ns', 9), edgeTypeOf('grass', 'ns', 10), edgeTypeOf('grass', 'ns', 90), edgeTypeOf('grass', 'ew', 109), edgeTypeOf('sand', 'ew', 149), edgeTypeOf('sand', 'ew', 150)]).toEqual([1, 0, 0, 1, 1, 0]);
    expect(wangIndex([1, 1, 1, 1])).toBe(15);
    expect(wangIndex([2, 1, 0, 3], [3, 4, 3, 4])).toBe(2 + 3 * (1 + 4 * (0 + 3 * 3)));
    // with P = 10 %, the calm tile .0 covers about two thirds of a ground
    expect(0.9 ** 4).toBeCloseTo(0.656, 2);
  });
});

describe('ground v2: bundles and memory', () => {
  const release = new Map([...sizes(new URL('../../src/art-release/hero/', import.meta.url)), ...sizes(new URL('../../src/art-release/npc/', import.meta.url)), ...sizes(new URL('../../src/art-release/enemy/', import.meta.url)), ...sizes(new URL('../../src/art-release/objects/', import.meta.url)), ...ART]);
  const keys = new Set(release.keys());
  const base = [...placeholderEntries(), ...releaseHeroEntries(keys), ...releaseNpcEntries(keys), ...releaseEnemyEntries(keys), ...releaseTerrainEntries('placeholder', keys)];
  const bundles = new Map([['base', base], ['common:ground', releaseTerrainEntries('common:ground', keys)], ...Object.entries(REGION_ENTRIES).map(([n, make]) => [n, [...make(), ...releaseTerrainEntries(n, keys)]])]);
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

  it('the island grounds and the water fit in the base atlas, packed tallest first: still 2048 × 1024, no second atlas', () => {
    const withImage = (es) => es.filter((e) => release.has(e.key)).map((e) => ({ ...e, image: { width: release.get(e.key).w, height: release.get(e.key).h } }));
    const g = releaseTerrainEntries('common:ground', keys);
    expect(g.length).toBeGreaterThan(300);
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
