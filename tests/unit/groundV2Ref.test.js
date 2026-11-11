import { describe, it, expect } from 'vitest';
import { readFileSync, readdirSync } from 'node:fs';
import { GameView, CHUNK } from '../../src/view/gameView.js';
import { Ground, Shape } from '../../src/game/world/tilemap.js';
import { PREFIX, SEASONAL, deepMap, landKey } from '../../src/view/groundV2.js';

// gfx W1 round 5: on the same maps, the engine draws exactly what the reference renderer draws.
// tests/fixtures/ground_v2_ref.json is written by tools/ground_v2_ref_fixture.py, which runs
// tools/terrain_v2/render_ref.py (render_v2, unchanged) and records every tile it draws, bottom first.
// The engine's pieces (GameView.groundPiecesV2, the code that draws) are compared display tile by
// display tile: water, calm tiles, pictures, ruin floor, edges — and every one of them exists in the art.

const REF = JSON.parse(readFileSync(new URL('../fixtures/ground_v2_ref.json', import.meta.url), 'utf8'));
const ART = new Set(readdirSync(new URL('../../src/art-release-v2/terrain/', import.meta.url)).filter((f) => f.endsWith('.png')).map((f) => f.slice(0, -4)));

/** render_ref's grid characters → the engine's ground classes (null: drawn on the cell grid). */
const CLASS = { g: 'grass', p: 'plains', l: 'lake', m: 'moss', n: 'snow', s: 'sand', d: 'dsand', '=': 'path', u: 'ruin', '~': 'water' };

/** A view of a reference grid (classes straight from the grid, as render_ref's terr). */
function view(rows, season) {
  const W = rows[0].length;
  const H = rows.length;
  const map = { width: W, height: H, tileSize: 16, ground: new Uint8Array(W * H), elev: new Uint8Array(W * H), shape: new Uint8Array(W * H).fill(Shape.FLAT) };
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) map.ground[y * W + x] = rows[y][x] === '~' ? Ground.WATER : rows[y][x] in CLASS ? Ground.GRASS : Ground.WOOD;
  const v = Object.create(GameView.prototype);
  Object.assign(v, { map, regions: [], season, v2Tiles: new Map(), sandUnderTrees: new Set(), deepWater: null, seasonKeySet: new Set(), v2Missing: new Set(), assets: { hasTexture: (k) => ART.has(k) } });
  v.groundClassAt = (x, y) => CLASS[rows[y][x]] ?? null;
  v.surfaceKey = () => 'tile.wood'; // (the cells without v2 art: not compared)
  // the reference's deep water (NAMES.md 3); the engine shapes its deep areas further (deepMapShaped, inspection R2)
  const deep = deepMap(W, H, (x, y) => rows[y][x] === '~');
  v.deepAt = (x, y) => deep[y * W + x] === 1;
  return v;
}

/** A reference key ("[<season>.]g2.<ground>.<name>", "g2.water.<…>") as the engine names it. */
function engineKey(ref) {
  const m = /^(?:(autumn|winter)\.)?g2\.(\w+)\.(.+)$/.exec(ref);
  if (!m) throw new Error(ref);
  const [, season, base, name] = m;
  if (base === 'water') {
    let w = /^(deep|shallow)\.([01])\.\d$/.exec(name);
    if (w) return `tile.water${w[1] === 'deep' ? '.deep' : ''}${w[2] === '1' ? '.v1' : ''}`;
    w = /^(deep|foam)\.e(\d+)\.\d$/.exec(name);
    if (w) return w[1] === 'deep' ? `tile.water.deep.edge.${w[2]}` : `tile.water.foam.${w[2]}`;
    throw new Error(ref);
  }
  const e = /^e(\d+)\.(\d+)$/.exec(name);
  const key = landKey(base, e ? `edge.${e[1]}.${e[2]}` : name);
  return season ? `${season}.${key}` : key;
}

describe('ground v2 round 5: the engine draws what render_ref.py draws', () => {
  for (const ref of REF) {
    it(`${ref.name}: every display tile, bottom first (water, calm tiles, pictures, ruin floor, edges)`, () => {
      const rows = ref.rows;
      const W = rows[0].length;
      const H = rows.length;
      const v = view(rows, ref.season);
      const seasonKey = (k) => (ref.season && SEASONAL.some((c) => k.startsWith(`${PREFIX[c]}.`)) ? `${ref.season}.${k}` : k);
      /** the engine's keys per display tile (i, j) */
      const drawn = new Map();
      for (let cy = 0; cy * CHUNK < H; cy++) {
        for (let cx = 0; cx * CHUNK < W; cx++) {
          const here = new Map();
          for (const p of v.groundPiecesV2(cx, cy)) {
            if (p.quarter) continue;
            const id = `${(p.x - 8) / 16},${(p.y - 8) / 16}`;
            if (!here.has(id)) here.set(id, []);
            here.get(id).push(p.anim ? p.key : seasonKey(p.key));
          }
          for (const [id, keys] of here) if (!drawn.has(id)) drawn.set(id, keys.join('|'));
        }
      }
      let compared = 0;
      let pictures = 0;
      const missing = new Set();
      for (let j = 0; j < H - 1; j++) {
        for (let i = 0; i < W - 1; i++) {
          // (a corner without v2 art: render_ref pastes that cell's v1 tile over it; the engine draws each cell on its own)
          if ([rows[j][i], rows[j][i + 1], rows[j + 1][i], rows[j + 1][i + 1]].some((c) => !(c in CLASS))) continue;
          const want = ref.draws[`${i},${j}`].split('|').map(engineKey).join('|');
          expect(drawn.get(`${i},${j}`), `${ref.name} ${i},${j}`).toBe(want);
          for (const k of want.split('|')) {
            if (k.startsWith('tile.water')) for (let f = 0; f < 4; f++) !ART.has(`${k}.${f}`) && missing.add(`${k}.${f}`);
            else if (!ART.has(k)) missing.add(k);
          }
          compared++;
          if (want.includes('.macro')) pictures++;
        }
      }
      expect([...missing]).toEqual([]);
      expect(compared).toBeGreaterThan(0.95 * (W - 1) * (H - 1) - 40);
      expect(pictures).toBeGreaterThan(100);
    });
  }

  it('the fixture covers every ground, all 8 pictures, dunes, edge variants 0-3, the ruin floor by the water, deep water and winter', () => {
    const all = REF.flatMap((r) => Object.values(r.draws).flatMap((s) => s.split('|')));
    for (const g of ['grass', 'plains', 'lake', 'moss', 'snow', 'sand', 'dsand', 'path']) expect(all.some((k) => k.startsWith(`g2.${g}.macro`)), g).toBe(true);
    for (const m of ['macro', 'macro2', 'macro3', 'macro4', 'macro5', 'macro6', 'macro7', 'macro8']) expect(all.some((k) => k.startsWith(`g2.grass.${m}.`)), m).toBe(true);
    expect(all.some((k) => /^g2\.ruin\.(?:[1-9]|\d\d)$/.test(k))).toBe(true);
    expect(all.some((k) => /^g2\.ruin\.e\d+\.\d+$/.test(k))).toBe(true);
    expect(all.some((k) => k.startsWith('g2.water.deep.0'))).toBe(true);
    expect(all.some((k) => k.startsWith('winter.g2.grass.macro'))).toBe(true);
    // round 7-8: edge variants 2 / 3 by the side states, the desert's dunes
    expect(all.filter((k) => /\.e\d+\.[23]$/.test(k)).length).toBeGreaterThan(100);
    expect(all.some((k) => /^g2\.dsand\.dune[1-6]\.[0-3]$/.test(k))).toBe(true);
  });
});
