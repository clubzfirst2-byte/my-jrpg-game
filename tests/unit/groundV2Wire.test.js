import { describe, it, expect } from 'vitest';
import { readdirSync } from 'node:fs';
import { Container } from 'pixi.js';
import { GameView, CHUNK } from '../../src/view/gameView.js';
import { Ground, Shape } from '../../src/game/world/tilemap.js';
import { createGameState, MAPS } from '../../src/game/state.js';
import { STEP_NAMES, deepMap, deepMapShaped, landKey } from '../../src/view/groundV2.js';
import { ATLAS_H, ATLAS_W, WATER_KEYS, waterQuads, waterSlot } from '../../src/view/waterLayer.js';
import { preloadReleaseGroup, preloadSwitchScript } from '../../tools/precache.mjs';

// gfx W1, the fixes after the inspections: the water layer (no chunk cache redrawn by the water), the
// shaped deep water (R2), the step pieces (NAMES.md 2b), the border by a wall (W1), the preload.

const hash = (x, y) => {
  let h = (x * 374761393 + y * 668265263) >>> 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177) >>> 0;
  return (h ^ (h >>> 16)) >>> 0;
};
const ART = new Set(readdirSync(new URL('../../src/art-release-v2/terrain/', import.meta.url)).filter((f) => f.endsWith('.png')).map((f) => f.slice(0, -4)));

describe('water layer: quads over the shared water atlas', () => {
  it('one slot per water key, apart, inside the atlas; every key has its 4 frames in the art', () => {
    const seen = new Set();
    for (const k of WATER_KEYS) {
      const [x, y] = waterSlot(k);
      expect(x).toBeGreaterThanOrEqual(1);
      expect(x + 16).toBeLessThanOrEqual(ATLAS_W - 1);
      expect(y + 16).toBeLessThanOrEqual(ATLAS_H - 1);
      seen.add(`${x},${y}`);
      for (let f = 0; f < 4; f++) expect(ART.has(`${k}.${f}`), `${k}.${f}`).toBe(true);
    }
    expect(seen.size).toBe(32);
    expect(waterSlot('tile.grass.0')).toBeNull();
  });

  it('a whole tile, a quarter (its own part of the tile), clipped to the chunk; unknown keys skipped', () => {
    const area = { x: 0, y: 0, width: 512, height: 512 };
    const q = waterQuads(
      [
        { key: 'tile.water', x: 24, y: 40, quarter: null },
        { key: 'tile.water.foam.3', x: 100, y: 100, quarter: 'se' },
        { key: 'tile.water.deep', x: -8, y: 504, quarter: null }, // half outside on two sides
        { key: 'tile.water.deep', x: 600, y: 0, quarter: null }, // outside
        { key: 'tile.grass.0', x: 0, y: 0, quarter: null },
      ],
      area,
    );
    expect(q.skipped).toEqual(['tile.grass.0']);
    expect(q.keys).toEqual(['tile.water', 'tile.water.foam.3#se', 'tile.water.deep']);
    expect(q.indices.length).toBe(18);
    // whole tile: 16 × 16 at its place, the slot's 16 × 16
    expect([...q.positions.slice(0, 8)]).toEqual([24, 40, 40, 40, 40, 56, 24, 56]);
    const [sx] = waterSlot('tile.water');
    expect(q.uvs[0] * ATLAS_W).toBeCloseTo(sx);
    expect(q.uvs[4] * ATLAS_W).toBeCloseTo(sx + 16);
    // quarter "se": 8 × 8, the slot's lower right
    const [fx, fy] = waterSlot('tile.water.foam.3');
    expect([...q.positions.slice(8, 16)]).toEqual([100, 100, 108, 100, 108, 108, 100, 108]);
    expect(q.uvs[8] * ATLAS_W).toBeCloseTo(fx + 8);
    expect(q.uvs[9] * ATLAS_H).toBeCloseTo(fy + 8);
    // clipped: the part inside the chunk, its texture part with it
    const [dx, dy] = waterSlot('tile.water.deep');
    expect([...q.positions.slice(16, 24)]).toEqual([0, 504, 8, 504, 8, 512, 0, 512]);
    expect(q.uvs[16] * ATLAS_W).toBeCloseTo(dx + 8);
    expect(q.uvs[21] * ATLAS_H).toBeCloseTo(dy + 8);
  });
});

describe('deep water, shaped (inspection R2)', () => {
  const m = createGameState(MAPS.world).map;
  const W = m.width;
  const H = m.height;
  const water = (x, y) => m.ground[y * W + x] === Ground.WATER;
  const longestRun = (d) => {
    let max = 0;
    for (let y = 1; y < H; y++) {
      let r = 0;
      for (let x = 0; x < W; x++) {
        r = water(x, y) && water(x, y - 1) && d[y * W + x] !== d[(y - 1) * W + x] ? r + 1 : 0;
        max = Math.max(max, r);
      }
    }
    for (let x = 1; x < W; x++) {
      let r = 0;
      for (let y = 0; y < H; y++) {
        r = water(x, y) && water(x - 1, y) && d[y * W + x] !== d[y * W + x - 1] ? r + 1 : 0;
        max = Math.max(max, r);
      }
    }
    return max;
  };
  const shaped = deepMapShaped(W, H, water, hash);
  const ref = deepMap(W, H, water);

  it('the shallow band along every shore stays 2 cells or more; deep cells form 2×2 areas', () => {
    for (let y = 0; y < H; y++) {
      for (let x = 0; x < W; x++) {
        if (!shaped[y * W + x]) continue;
        expect(water(x, y)).toBe(true);
        for (let dy = -2; dy <= 2; dy++) for (let dx = -2; dx <= 2; dx++) if (dx * dx + dy * dy <= 4 && x + dx >= 0 && y + dy >= 0 && x + dx < W && y + dy < H) expect(water(x + dx, y + dy), `${x},${y}`).toBe(true);
        const at = (a, b) => a >= 0 && b >= 0 && a < W && b < H && shaped[b * W + a] === 1;
        expect([[0, 0], [-1, 0], [0, -1], [-1, -1]].some(([ox, oy]) => at(x + ox, y + oy) && at(x + ox + 1, y + oy) && at(x + ox, y + oy + 1) && at(x + ox + 1, y + oy + 1))).toBe(true);
      }
    }
  });

  it('its border no longer runs straight along the shore: the longest straight run along cell edges is a quarter of the reference rule\'s', () => {
    const a = longestRun(ref);
    const b = longestRun(shaped);
    expect(a).toBeGreaterThan(30);
    expect(b).toBeLessThanOrEqual(12);
    // about as much deep water as before (it is a shape change)
    const n = (d) => d.reduce((s, v) => s + v, 0);
    expect(n(shaped) / n(ref)).toBeGreaterThan(0.8);
    expect(n(shaped) / n(ref)).toBeLessThan(1.1);
  });
});

/** A small map: grass with a raised grass block, a raised ruin block, a ruin floor and a water channel between walls. */
function smallView({ ground, elev }) {
  const H = ground.length;
  const W = ground[0].length;
  const G = { g: Ground.GRASS, u: Ground.RUIN, '~': Ground.WATER, '#': Ground.WALL, s: Ground.SAND, w: Ground.WOOD };
  const map = { width: W, height: H, tileSize: 16, ground: new Uint8Array(W * H), elev: new Uint8Array(W * H), shape: new Uint8Array(W * H).fill(Shape.FLAT) };
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    map.ground[y * W + x] = G[ground[y][x]];
    map.elev[y * W + x] = Number(elev[y][x]) * 8;
  }
  const v = Object.create(GameView.prototype);
  return Object.assign(v, { map, regions: [], season: null, v2Tiles: new Map(), sandUnderTrees: new Set(), deepWater: null, seasonKeySet: new Set(), v2Missing: new Set(), assets: { hasTexture: (k) => ART.has(k) }, calmMemo: null, cellCalmMemo: null, v2Pictures: null, actors: new Container() });
}

describe('one-level steps (NAMES.md 2b)', () => {
  const v = smallView({
    ground: ['gggggggg', 'gggggggg', 'gggguuug', 'gggguuug', 'ggggggww', 'gggggggw'],
    elev: ['00000000', '01110000', '01110110', '01100110', '00000011', '00000001'],
  });
  const lower = (x, y, h) => x >= 0 && y >= 0 && x < v.map.width && y < v.map.height && v.map.elev[y * v.map.width + x] < h;
  const pieces = (x, y) => {
    const h = v.map.elev[y * v.map.width + x];
    return v.stepPieces(x, y, h, lower(x, y - 1, h), lower(x + 1, y, h), lower(x - 1, y, h));
  };

  it('a rim of the cell\'s ground with mask N 1 + E 2 + W 4 and v = hash(tx + 5, ty + 9) % 2, instead of the 1-px lines; every one in the art', () => {
    expect(pieces(1, 1).rims).toEqual([`tile.grass.step.5.${hash(6, 10) % 2}`]); // north and west lower
    expect(pieces(3, 1).rims).toEqual([`tile.grass.step.3.${hash(8, 10) % 2}`]); // north and east lower
    expect(pieces(2, 1).rims[0]).toBe(`tile.grass.step.1.${hash(7, 10) % 2}`);
    expect(pieces(5, 2).rims).toEqual([`tile.ruin.step.5.${hash(10, 11) % 2}`]); // the ruin floor has them too
    for (let y = 0; y < 6; y++) for (let x = 0; x < 8; x++) if (v.map.elev[y * 8 + x] > 0) for (const k of pieces(x, y)?.rims ?? []) expect(ART.has(k), k).toBe(true);
    // a ground with no v2 art (wood): null — the v1 lines
    expect(pieces(6, 4)).toBeNull();
    expect(STEP_NAMES.length).toBe(18);
  });

  it('inner corners where the N and E (W) sides are not lower but the NE (NW) cell is', () => {
    // (2, 3): north (2, 2) raised, east (3, 3) lower → no inner corner; (1, 2): N and W? W lower
    // (2, 2): N (2, 1) and E (3, 2) raised, NE (3, 1) raised → none; build a case: (2, 3) N=(2,2) raised, W=(1,3) raised, NW=(1,2) raised
    const w = smallView({ ground: ['gggg', 'gggg', 'gggg', 'gggg'], elev: ['0000', '0110', '1110', '1110'] });
    const lw = (x, y, h) => x >= 0 && y >= 0 && x < 4 && y < 4 && w.map.elev[y * 4 + x] < h;
    const at = (x, y) => w.stepPieces(x, y, 8, lw(x, y - 1, 8), lw(x + 1, y, 8), lw(x - 1, y, 8));
    // (1, 2): N (1, 1) raised, W (0, 2) raised, NW (0, 1) lower → inner.nw
    expect(at(1, 2).rims).toContain('tile.grass.step.inner.nw');
    // (2, 2): N (2, 1) raised, E (3, 2) lower → an east rim, no inner corner
    expect(at(2, 2).rims).toEqual([`tile.grass.step.2.${hash(7, 11) % 2}`]);
    // (1, 1): N lower, W (0, 1) lower → rim 5
    expect(at(1, 1).rims[0]).toBe(`tile.grass.step.5.${hash(6, 10) % 2}`);
    expect(ART.has('tile.grass.step.inner.ne') && ART.has('tile.grass.step.inner.nw')).toBe(true);
  });

  it('the shadow on the lower east cell is that cell\'s ground (v = hash(tx + 6, ty + 9) % 2); none on water or a ground with no v2 art', () => {
    expect(v.stepShadeKey(3, 1)).toBe(`tile.grass.step.shade.${hash(9, 10) % 2}`);
    expect(v.stepShadeKey(4, 2)).toBe(`tile.ruin.step.shade.${hash(10, 11) % 2}`); // (5, 2) is ruin floor
    expect(v.stepShadeKey(5, 4)).toBeNull(); // (6, 4) wood
    const wv = smallView({ ground: ['g~'], elev: ['10'] });
    expect(wv.stepShadeKey(0, 0)).toBeNull();
  });

  it('the shadows of a row come after every chunk\'s surfaces of that row (a slightly lower east cell does not hide them)', () => {
    const rows = new Map();
    const shades = new Map([[7, [new Container()]]]);
    v.flushShades(shades, 7, rows, 3);
    const c = rows.get(7.5);
    for (let cx = 0; cx < 40; cx++) expect(c.zIndex).toBeGreaterThan(7 * 16 + 0.001 + cx * 1e-5);
    expect(c.zIndex).toBeLessThan(8 * 16);
    expect(shades.has(7)).toBe(false);
  });
});

describe('W1: a border between grounds next to a wall runs on to the wall', () => {
  // a ruin floor with a water channel between two walls (as the lake region's room)
  const v = smallView({
    ground: ['#uuuuuu#', '#uuuuuu#', '#~~~~~~#', '#~~~~~~#', '#uuuuuu#', '#uuuuuu#'],
    elev: ['00000000', '00000000', '00000000', '00000000', '00000000', '00000000'],
  });
  it('the display tiles by the walls draw the ruin floor\'s edge over the water on the quarters that are not wall', () => {
    const pieces = v.groundPiecesV2(0, 0);
    // display tile (0, 1): corners wall, ruin, wall, water → the ruin floor's edge over the water on its east quarters
    const at = (i, j) => pieces.filter((p) => Math.floor((p.x - 8) / 16) === i && Math.floor((p.y - 8) / 16) === j);
    const t01 = at(0, 1);
    expect(t01.some((p) => p.key.startsWith('tile.ruin.edge.') && p.quarter === 'ne')).toBe(true);
    expect(t01.some((p) => p.key.startsWith('tile.ruin.edge.') && p.quarter === 'se')).toBe(true);
    expect(t01.some((p) => p.anim && p.quarter === 'se')).toBe(true); // the water under it
    // the same on the east wall's side, and at the channel's south border
    expect(at(6, 1).some((p) => p.key.startsWith('tile.ruin.edge.') && p.quarter === 'nw')).toBe(true);
    expect(at(0, 3).some((p) => p.key.startsWith('tile.ruin.edge.') && p.quarter === 'se')).toBe(true);
    // the wall's own quarters as before (its v1 tile, not blended)
    expect(t01.filter((p) => p.quarter === 'se' || p.quarter === 'nw').length).toBeGreaterThan(0);
    // every key in the art
    for (const p of pieces) if (!p.anim && p.key.startsWith('tile.ruin')) expect(ART.has(p.key), p.key).toBe(true);
    expect([...v.v2Missing]).toEqual([]);
    expect(CHUNK).toBe(32);
    // the same with raised walls (as in the lake region's room): the border still runs on to them
    const r = smallView({
      ground: ['#uuuuuu#', '#uuuuuu#', '#~~~~~~#', '#~~~~~~#', '#uuuuuu#', '#uuuuuu#'],
      elev: ['10000001', '10000001', '10000001', '10000001', '10000001', '10000001'],
    });
    const rp = r.groundPiecesV2(0, 0);
    const rat = (i, j) => rp.filter((p) => Math.floor((p.x - 8) / 16) === i && Math.floor((p.y - 8) / 16) === j);
    expect(rat(0, 1).some((p) => p.key.startsWith('tile.ruin.edge.') && p.quarter === 'ne')).toBe(true);
    expect(rat(6, 1).some((p) => p.key.startsWith('tile.ruin.edge.') && p.quarter === 'nw')).toBe(true);
    expect(rat(0, 1).some((p) => p.quarter === 'nw' || p.quarter === 'sw')).toBe(false); // the raised wall: drawn by its row
    expect(landKey('ruin', '0')).toBe('tile.ruin');
  });
});

describe('preload: only the terrain sheet that is drawn (fx-v2\'s fix, by the URL)', () => {
  const pairs = { terrain: { v1: { png: './t1.png', json: './t1.json' }, v2: { png: './t2.png', json: './t2.json' } } };
  const run = (search) => {
    const links = [];
    const document = { createElement: () => ({ attrs: {}, setAttribute(k, v) { this.attrs[k] = v; } }), head: { appendChild: (l) => links.push(l.attrs) } };
    new Function('location', 'document', preloadSwitchScript(pairs))({ search }, document);
    return links.map((l) => l.href);
  };
  it('v1 by default and with ?terrain=v1 / ?v2=0; v2 with ?terrain=v2; none with ?terrain=placeholder or ?hd=0', () => {
    expect(run('')).toEqual(['./t1.png', './t1.json']);
    expect(run('?map=world&terrain=v1')).toEqual(['./t1.png', './t1.json']);
    expect(run('?v2=0')).toEqual(['./t1.png', './t1.json']);
    expect(run('?terrain=v2')).toEqual(['./t2.png', './t2.json']);
    expect(run('?v2=0&terrain=v2')).toEqual(['./t2.png', './t2.json']);
    expect(run('?terrain=placeholder')).toEqual([]);
    expect(run('?hd=0')).toEqual([]);
  });
  it('the pair is not preloaded by the HTML itself; the other groups are as before', () => {
    const groups = new Set(['terrain', 'v2-terrain', 'hero', 'npc-revision-a']);
    expect(preloadReleaseGroup('terrain', groups)).toBe(false);
    expect(preloadReleaseGroup('v2-terrain', groups)).toBe(false);
    expect(preloadReleaseGroup('hero', groups)).toBe(true);
    expect(preloadReleaseGroup('npc-revision-a', groups)).toBe(false);
  });
});
