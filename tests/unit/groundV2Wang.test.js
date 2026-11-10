import { describe, it, expect } from 'vitest';
import { GameView } from '../../src/view/gameView.js';
import { Ground, Shape } from '../../src/game/world/tilemap.js';
import { PRIORITY, P_TYPE1 } from '../../src/view/groundV2.js';

// gfx W1 round 2: the view's choice of edge-matched tiles and macro blocks (GameView.wangAt / macroAt /
// cellWang) against a port of the reference renderer (tools/terrain_v2/render_ref.py: macro_blocks,
// edge_type, lowest_land), on a map with grass, sand, path, ruin, water, a raised block and a ramp.

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
const CLASS = { g: 'grass', s: 'sand', '=': 'path', u: 'ruin', '~': 'water', w: 'other' };
const GROUND = { g: Ground.GRASS, s: Ground.SAND, '=': Ground.PATH, u: Ground.RUIN, '~': Ground.WATER, w: Ground.WOOD };
const BUSY = new Set(['grass', 'plains', 'lake', 'moss', 'path']);

/** The reference (render_ref.py), ported: macro blocks and the tile name of every display tile. */
function reference(rows, season = null) {
  const terr = (x, y) => CLASS[rows[Math.max(0, Math.min(H - 1, y))][Math.max(0, Math.min(W - 1, x))]];
  const lowest = (i, j) => {
    const ts = [terr(i, j), terr(i + 1, j), terr(i, j + 1), terr(i + 1, j + 1)];
    if (ts.includes('water') || ts.includes('other')) return null;
    return ts.reduce((a, b) => (PRIORITY.indexOf(b) < PRIORITY.indexOf(a) ? b : a));
  };
  const uniform = (i, j, k) => {
    const ts = new Set();
    for (let dx = 0; dx <= k; dx++) for (let dy = 0; dy <= k; dy++) ts.add(terr(i + dx, j + dy));
    return ts.size === 1 && !ts.has('water') && !ts.has('other');
  };
  const macro = new Map();
  for (let j = 0; j < H - 3; j += 3) {
    for (let i = 0; i < W - 3; i += 3) {
      if (uniform(i, j, 3) && dhash(i, j) % (BUSY.has(terr(i, j)) ? 6 : 12) === 0) for (let q = 0; q < 9; q++) macro.set(`${i + (q % 3)},${j + Math.floor(q / 3)}`, { name: `macro3.${q}`, block: `3:${i},${j}` });
    }
  }
  for (let j = 0; j < H - 2; j += 2) {
    for (let i = 0; i < W - 2; i += 2) {
      const cells = [[i, j], [i + 1, j], [i, j + 1], [i + 1, j + 1]];
      if (cells.some(([x, y]) => macro.has(`${x},${y}`)) || !uniform(i, j, 2)) continue;
      const h = dhash(i + 1, j) % (BUSY.has(terr(i, j)) ? 4 : 8);
      if (h < 2) cells.forEach(([x, y], q) => macro.set(`${x},${y}`, { name: `${h === 0 ? 'macro' : 'macro2'}.${q}`, block: `2:${i},${j}` }));
    }
  }
  const edge = (a, b, id, look) => {
    if (lowest(...a) !== lowest(...b)) return 0;
    const ma = macro.get(`${a}`);
    const mb = macro.get(`${b}`);
    if ((ma || mb) && (!ma || !mb || ma.block !== mb.block)) return 0;
    return dhash(...id) % 100 < P_TYPE1[look] ? 1 : 0;
  };
  const wang = (i, j) => {
    const low = lowest(i, j);
    const look = season === 'winter' && ['grass', 'plains', 'lake', 'moss'].includes(low) ? 'snow' : low;
    return edge([i, j - 1], [i, j], [2 * i + 1, 2 * j], look) + 2 * edge([i, j], [i + 1, j], [2 * i + 2, 2 * j + 1], look) + 4 * edge([i, j], [i, j + 1], [2 * i + 1, 2 * j + 2], look) + 8 * edge([i - 1, j], [i, j], [2 * i, 2 * j + 1], look);
  };
  return { lowest, macro, wang };
}

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

describe('ground v2 round 2: the view picks the tiles the reference renderer picks', () => {
  const rows = grid();

  it('macro blocks: 3×3 at multiples of 3, then 2×2 at even tiles, only on one flat land ground', () => {
    const ref = reference(rows);
    const v = view(rows);
    let blocks3 = 0;
    let blocks2 = 0;
    for (let j = -1; j < H; j++) {
      for (let i = -1; i < W; i++) {
        const m = v.macroAt(i, j);
        expect(m ?? null, `${i},${j}`).toEqual(ref.macro.get(`${i},${j}`) ?? null);
        if (m?.name === 'macro3.0') blocks3++;
        if (m?.name === 'macro.0' || m?.name === 'macro2.0') blocks2++;
      }
    }
    expect(blocks3).toBeGreaterThan(3);
    expect(blocks2).toBeGreaterThan(10);
  });

  it('edge-matched tiles: n = N + 2E + 4S + 8W, the same as the reference on every flat land tile (summer and winter)', () => {
    for (const season of [null, 'winter']) {
      const ref = reference(rows, season);
      const v = view(rows, { season });
      const seen = new Set();
      for (let j = 0; j < H - 1; j++) {
        for (let i = 0; i < W - 1; i++) {
          const low = ref.lowest(i, j);
          expect(v.lowestLand(i, j), `${i},${j}`).toBe(low);
          if (!low || ref.macro.has(`${i},${j}`)) continue;
          const n = v.wangAt(i, j, low);
          expect(n, `${season} ${i},${j}`).toBe(ref.wang(i, j));
          seen.add(`${low}.${n}`);
        }
      }
      // sand (P 50 %) uses all 16 tiles; grass (10 %; winter: the snow's 50 %) mostly the calm one
      for (let n = 0; n < 16; n++) expect(seen.has(`sand.${n}`), `sand.${n}`).toBe(true);
    }
  });

  it('two tiles that share an edge agree on its type; a macro block and a border between grounds have type-0 edges', () => {
    const v = view(rows);
    const bit = (n, k) => (n >> k) & 1;
    let plain = 0;
    let total = 0;
    for (let j = 0; j < H - 2; j++) {
      for (let i = 0; i < W - 2; i++) {
        const a = v.lowestLand(i, j);
        if (!a) continue;
        const n = v.wangAt(i, j, a);
        const e = v.lowestLand(i + 1, j);
        const s = v.lowestLand(i, j + 1);
        // my E edge = the W edge of the tile to the east; my S edge = the N edge of the tile below
        if (e) expect(bit(n, 1), `E ${i},${j}`).toBe(bit(v.wangAt(i + 1, j, e), 3));
        else expect(bit(n, 1)).toBe(0);
        if (s) expect(bit(n, 2), `S ${i},${j}`).toBe(bit(v.wangAt(i, j + 1, s), 0));
        else expect(bit(n, 2)).toBe(0);
        if (e && e !== a) expect(bit(n, 1)).toBe(0);
        const m = v.macroAt(i, j);
        const me = v.macroAt(i + 1, j);
        if ((m || me) && m?.block !== me?.block) expect(bit(n, 1), `macro edge ${i},${j}`).toBe(0);
        if (a === 'grass' && !m) {
          total++;
          if (n === 0) plain++;
        }
      }
    }
    // the calm base (.0) on most of the grass: 0.9^4 = 66 % away from borders and macro blocks, more next to them
    expect(plain / total).toBeGreaterThan(0.6);
  });

  it('raised ground and ramps do not blend: no lowest land, no macro block; their cells take a tile of their own level', () => {
    const raise = (x, y) => (x >= 2 && x <= 9 && y >= 12 && y <= 19 ? 1 : 0);
    const ramp = (x, y) => x === 5 && y === 20;
    const v = view(rows, { raise, ramp });
    for (let j = 11; j <= 20; j++) for (let i = 1; i <= 9; i++) if (j <= 19 || i === 4 || i === 5) expect(v.lowestLand(i, j), `${i},${j}`).toBeNull();
    for (let j = 9; j <= 21; j++) for (let i = 0; i <= 11; i++) if (v.macroAt(i, j)) expect(v.uniformBlock(...v.macroAt(i, j).block.slice(2).split(',').map(Number), Number(v.macroAt(i, j).block[0])), `${i},${j}`).toBe('grass');
    const bit = (n, k) => (n >> k) & 1;
    for (let y = 12; y <= 19; y++) {
      for (let x = 2; x <= 9; x++) {
        const n = v.cellWang(x, y, 'grass');
        expect(n).toBeGreaterThanOrEqual(0);
        expect(n).toBeLessThan(16);
        // the plateau's rim: type 0 toward the lower ground; inside it, neighbours agree
        if (y === 12) expect(bit(n, 0)).toBe(0);
        if (x === 9) expect(bit(n, 1)).toBe(0);
        if (y === 19) expect(bit(n, 2)).toBe(0);
        if (x === 2) expect(bit(n, 3)).toBe(0);
        if (x < 9) expect(bit(n, 1)).toBe(bit(v.cellWang(x + 1, y, 'grass'), 3));
        if (y < 19) expect(bit(n, 2)).toBe(bit(v.cellWang(x, y + 1, 'grass'), 0));
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
});
