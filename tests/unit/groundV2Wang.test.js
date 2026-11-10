import { describe, it, expect } from 'vitest';
import { GameView } from '../../src/view/gameView.js';
import { Ground, Shape } from '../../src/game/world/tilemap.js';
import { PREFIX, displayLayers, landKey, CORNERS } from '../../src/view/groundV2.js';
import { readdirSync } from 'node:fs';

// gfx W1 rounds 2-5: the view's choice of ground tiles and pictures (GameView.wangAt / macroAt /
// cellWang) on a map with grass, sand, path, ruin, water, a raised block and a ramp: heights, the ruin
// floor's courses, caches; and every key it draws there exists in the art. (The exact match with the
// reference renderer, tools/terrain_v2/render_ref.py, is groundV2Ref.test.js.)

const W = 48;
const H = 36;
const dhash = (i, j) => {
  let h = (i * 374761393 + j * 668265263) >>> 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177) >>> 0;
  return (h ^ (h >>> 16)) >>> 0;
};

/** g grass, s sand, = path, u ruin, ~ water, w wood (no v2 art). */
function grid() {
  const rows = [];
  for (let y = 0; y < H; y++) {
    let r = '';
    for (let x = 0; x < W; x++) {
      let c = 'g';
      if (x >= 30) c = 's';
      if (y >= 28) c = '~';
      if (x === 12 || y === 9) c = '=';
      if (x >= 36 && x <= 44 && y >= 2 && y <= 10) c = 'u';
      if (x >= 20 && x <= 22 && y >= 20 && y <= 21) c = 'w';
      r += c;
    }
    rows.push(r);
  }
  return rows;
}
const GROUND = { g: Ground.GRASS, s: Ground.SAND, '=': Ground.PATH, u: Ground.RUIN, '~': Ground.WATER, w: Ground.WOOD };
/** A view with only what the ground choice reads (no renderer). */
function view(rows, { season = null, raise = () => 0, ramp = () => false } = {}) {
  const map = { width: W, height: H, tileSize: 16, ground: new Uint8Array(W * H), elev: new Uint8Array(W * H), shape: new Uint8Array(W * H) };
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      map.ground[y * W + x] = GROUND[rows[y][x]];
      map.elev[y * W + x] = raise(x, y);
      map.shape[y * W + x] = ramp(x, y) ? Shape.RAMP_N : Shape.FLAT;
    }
  }
  const v = Object.create(GameView.prototype);
  return Object.assign(v, { map, regions: [], season, v2Tiles: new Map(), sandUnderTrees: new Set(), deepWater: null });
}

const ART = new Set(readdirSync(new URL('../../src/art-release-v2/terrain/', import.meta.url)).filter((f) => f.endsWith('.png')).map((f) => f.slice(0, -4)));

describe('ground v2 rounds 2-5: the view picks the tiles the reference renderer picks', () => {
  const rows = grid();

  it('pictures: only on one flat ground with pictures (never on the ruin floor or across a border), 4 pieces each, never overlapping; the same in every season', () => {
    const blocks = new Map();
    for (const season of [null, 'autumn', 'winter']) {
      const v = view(rows, { season });
      for (let j = -1; j < H; j++) {
        for (let i = -1; i < W; i++) {
          const m = v.macroAt(i, j);
          if (!m) continue;
          expect(['grass', 'sand', 'path'], `${i},${j}`).toContain(v.lowestLand(i, j));
          expect(v.uniformBlock(...m.block.split(',').map(Number), 2)).toBe(v.lowestLand(i, j));
          if (!season) blocks.set(`${i},${j}`, m);
          else expect(m).toEqual(blocks.get(`${i},${j}`));
        }
      }
    }
    const byBlock = new Map();
    for (const [, m] of blocks) byBlock.set(m.block, [...(byBlock.get(m.block) ?? []), m.name]);
    expect(byBlock.size).toBeGreaterThan(20);
    for (const [id, names] of byBlock) expect(names.map((n) => n.split('.')[1]).sort(), id).toEqual(['0', '1', '2', '3']);
  });

  it('every flat land display tile: a calm tile hash(i + 3, j + 11) % 16, or the ruin floor\'s row / column tile', () => {
    for (const season of [null, 'autumn', 'winter']) {
      const v = view(rows, { season });
      for (let j = 0; j < H - 1; j++) {
        for (let i = 0; i < W - 1; i++) {
          const low = v.lowestLand(i, j);
          if (!low) continue;
          const n = v.wangAt(i, j, low);
          if (low === 'ruin') expect(Math.floor(n / 6)).toBe((32 * j) % 11);
          else expect(n, `${season} ${low} ${i},${j}`).toBe(dhash(i + 3, j + 11) % 16);
        }
      }
    }
  });

  it('C: one row phase along a whole row of ruin tiles, the next row 32 px on; neighbours share their column line\'s symbol', () => {
    const v = view(rows);
    const COMBOS = [[0, 1], [0, 2], [1, 0], [1, 2], [2, 0], [2, 1]];
    let n = 0;
    for (let j = 2; j <= 9; j++) {
      for (let i = 36; i <= 43; i++) {
        if (v.lowestLand(i, j) !== 'ruin' || v.lowestLand(i + 1, j) !== 'ruin') continue;
        const a = v.wangAt(i, j, 'ruin');
        const b = v.wangAt(i + 1, j, 'ruin');
        expect(Math.floor(a / 6)).toBe((32 * j) % 11);
        expect(Math.floor(b / 6)).toBe(Math.floor(a / 6));
        expect(COMBOS[a % 6][1]).toBe(COMBOS[b % 6][0]);
        n++;
      }
    }
    expect(n).toBeGreaterThan(30);
  });

  it('every key the view draws on this map exists in the v2 art, in every season (no missing tile, macro piece or edge)', () => {
    const hash = dhash;
    for (const season of [null, 'autumn', 'winter']) {
      const v = view(rows, { season });
      v.seasonKeySet = new Set();
      const keyOf = (k) => (season && ['tile.grass', 'plains.grass', 'lake.grass', 'forest.grass'].some((p) => k === p || k.startsWith(`${p}.`)) ? `${season}.${k}` : k);
      const drawn = new Set();
      for (let j = -1; j < H; j++) {
        for (let i = -1; i < W; i++) {
          const cells = CORNERS.map(([dx, dy]) => [Math.max(0, Math.min(W - 1, i + dx)), Math.max(0, Math.min(H - 1, j + dy))]);
          const cls = cells.map(([x, y]) => v.groundClassAt(x, y));
          if (cls.some((c) => c === null)) {
            // (cannot blend: each cell's own tile)
            cells.forEach(([x, y], k) => cls[k] && cls[k] !== 'water' && drawn.add(keyOf(landKey(cls[k], String(v.cellWang(x, y, cls[k]))))));
            continue;
          }
          const layers = displayLayers({
            cls,
            deep: cells.map(([x, y]) => v.deepAt(x, y)),
            waterVariant: hash(i, j) % 2,
            edgeVariant: (c) => (c === 'ruin' ? ((10 * j) % 11 + 11) % 11 : hash(i + 7, j) % 2),
            pick: (c) => String(v.wangAt(i, j, c)),
            macro: () => v.macroAt(i, j)?.name ?? null,
          });
          for (const l of layers) {
            if (l.anim) for (let f = 0; f < 4; f++) drawn.add(`${l.key}.${f}`);
            else drawn.add(keyOf(l.key));
          }
        }
      }
      const missing = [...drawn].filter((k) => !ART.has(k));
      expect(missing, `${season}`).toEqual([]);
      expect(drawn.size).toBeGreaterThan(200);
      // the ruin floor meets the water nowhere on this map, the sand does: foam and sand edges are drawn
      expect([...drawn].some((k) => k.startsWith('tile.water.foam.'))).toBe(true);
      expect([...drawn].some((k) => k.startsWith('tile.sand.edge.'))).toBe(true);
      expect([...drawn].some((k) => k.startsWith(`${season ? `${season}.` : ''}${PREFIX.grass}.edge.`))).toBe(true);
    }
  });

  it('raised ground and ramps do not blend: no lowest land, no macro block; their cells take a tile of their own level', () => {
    const raise = (x, y) => ((x >= 2 && x <= 9 && y >= 12 && y <= 19) || (x >= 38 && x <= 42 && y >= 4 && y <= 8) || (x >= 32 && x <= 35 && y >= 14 && y <= 17) ? 1 : 0);
    const ramp = (x, y) => x === 5 && y === 20;
    const v = view(rows, { raise, ramp });
    for (let j = 11; j <= 20; j++) for (let i = 1; i <= 9; i++) if (j <= 19 || i === 4 || i === 5) expect(v.lowestLand(i, j), `${i},${j}`).toBeNull();
    for (let j = 9; j <= 21; j++) for (let i = 0; i <= 11; i++) if (v.macroAt(i, j)) expect(v.uniformBlock(...v.macroAt(i, j).block.split(',').map(Number), 2), `${i},${j}`).toBe('grass');
    // a raised grass block (A): calm tiles by hash, as a display tile's
    for (let y = 12; y <= 19; y++) for (let x = 2; x <= 9; x++) expect(v.cellWang(x, y, 'grass')).toBe(dhash(x + 3, y + 11) % 16);
    // a raised sand block (A): calm tiles; a raised ruin block (C): one row phase per row
    for (let y = 14; y <= 17; y++) {
      for (let x = 32; x <= 35; x++) {
        expect(v.cellWang(x, y, 'sand')).toBe(dhash(x + 3, y + 11) % 16);
        expect(ART.has(landKey('sand', String(v.cellWang(x, y, 'sand'))))).toBe(true);
      }
    }
    for (let y = 4; y <= 8; y++) {
      const r = Math.floor(v.cellWang(38, y, 'ruin') / 6);
      for (let x = 38; x <= 42; x++) {
        const n = v.cellWang(x, y, 'ruin');
        expect(n).toBeLessThan(66);
        expect(Math.floor(n / 6)).toBe(r);
        expect(ART.has(landKey('ruin', String(n)))).toBe(true);
      }
    }
  });

  it('is fixed for the map: the same tile every time it is asked (chunks rebuilt while streaming look the same)', () => {
    const a = view(rows);
    const b = view(rows);
    for (let j = 30; j >= 0; j -= 3) for (let i = 40; i >= 0; i -= 2) b.macroAt(i, j); // another order of asking
    for (let j = 0; j < H - 1; j++) {
      for (let i = 0; i < W - 1; i++) {
        const low = a.lowestLand(i, j);
        if (low) expect(b.wangAt(i, j, low)).toBe(a.wangAt(i, j, low));
        expect(b.macroAt(i, j)).toEqual(a.macroAt(i, j));
      }
    }
  });

  it('the season changes the keys (winter.*), not the picks: summer, winter and summer again pick the same tiles and pictures', () => {
    const v = view(rows);
    const before = [];
    for (let j = 0; j < H - 1; j++) for (let i = 0; i < 29; i++) if (v.lowestLand(i, j)) before.push(v.macroAt(i, j)?.name ?? v.wangAt(i, j, v.lowestLand(i, j)));
    v.season = 'winter';
    const winter = [];
    for (let j = 0; j < H - 1; j++) for (let i = 0; i < 29; i++) if (v.lowestLand(i, j)) winter.push(v.macroAt(i, j)?.name ?? v.wangAt(i, j, v.lowestLand(i, j)));
    expect(winter).toEqual(before);
    expect(before.some((n) => typeof n === 'string')).toBe(true);
    v.season = null;
    const after = [];
    for (let j = 0; j < H - 1; j++) for (let i = 0; i < 29; i++) if (v.lowestLand(i, j)) after.push(v.macroAt(i, j)?.name ?? v.wangAt(i, j, v.lowestLand(i, j)));
    expect(after).toEqual(before);
  });
});
