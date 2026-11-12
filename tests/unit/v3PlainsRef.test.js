import { describe, it, expect } from 'vitest';
import { readFileSync, readdirSync } from 'node:fs';
import { GameView, CHUNK } from '../../src/view/gameView.js';
import { Ground, Shape } from '../../src/game/world/tilemap.js';
import { PREFIX, SEASONAL, deepMap, landKey } from '../../src/view/groundV2.js';
import {
  MacroGrid, PATTERNS, flowKey, flowCorner, flowLook, flowVariants, hsh, baseKey, v3Season, seasonPrefix, v3PlainsPartOf, v3PlainsBundles, FLOW_TINT, STORED, MIRROR, flipBits,
  treeKind, plainsTreeLook, openProp, treeFootProp, PROPS, swayStep, swayFrame, TREE_SWAY, PROP_SWAY, floraKey, floraFrames,
} from '../../src/view/v3Plains.js';
import { hash01 } from '../../src/view/placement.js';
import { v3ArtGroups } from '../../src/view/assets/artV3.js';
import { packGroup, seasonPartOf } from '../../tools/release-art-pack.mjs';

// Graphics v3 (STYLE.md 6): the engine places the plains' v3 ground exactly as the art side's reference
// does. tests/fixtures/ground_v3_ref.json is written by tools/ground_v3_ref_fixture.py, which runs the
// reference unchanged — tools/art_v3/gen_ground_v3.py (macro_of, flow_corner, flow_key) and
// tools/terrain_v2/render_ref.py (render_v2: the other grounds, the water and the grass edges' mask and v)
// — and records every tile it draws per display tile, bottom first.

const REF = JSON.parse(readFileSync(new URL('../fixtures/ground_v3_ref.json', import.meta.url), 'utf8'));
const V2 = readdirSync(new URL('../../src/art-release-v2/terrain/', import.meta.url)).filter((f) => f.endsWith('.png')).map((f) => f.slice(0, -4));
const V3 = readdirSync(new URL('../../src/art-release-v3/terrain/', import.meta.url)).filter((f) => f.endsWith('.png')).map((f) => f.slice(0, -4));
const ART = new Set([...V2, ...V3]);

const CLASS = { g: 'grass', p: 'plains', l: 'lake', m: 'moss', n: 'snow', s: 'sand', d: 'dsand', '=': 'path', u: 'ruin', '~': 'water' };

function view(rows, season) {
  const W = rows[0].length;
  const H = rows.length;
  const map = { width: W, height: H, tileSize: 16, ground: new Uint8Array(W * H), elev: new Uint8Array(W * H), shape: new Uint8Array(W * H).fill(Shape.FLAT) };
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) map.ground[y * W + x] = rows[y][x] === '~' ? Ground.WATER : Ground.GRASS;
  const v = Object.create(GameView.prototype);
  Object.assign(v, { v3: true, v3Macro: null, map, regions: [], season, v2Tiles: new Map(), sandUnderTrees: new Set(), deepWater: null, seasonKeySet: new Set(), v2Missing: new Set(), assets: { hasTexture: (k) => ART.has(k) } });
  v.groundClassAt = (x, y) => CLASS[rows[y][x]] ?? null;
  v.surfaceKey = () => 'tile.wood';
  const deep = deepMap(W, H, (x, y) => rows[y][x] === '~');
  v.deepAt = (x, y) => deep[y * W + x] === 1;
  return v;
}

/** A reference key as the engine names it (v2 keys as groundV2Ref.test.js; v3 keys are the same). */
function engineKey(ref) {
  if (ref.includes('.v3.')) return ref;
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

describe('v3 plains ground: the engine draws what the art side\'s reference draws', () => {
  for (const ref of REF.maps) {
    it(`${ref.name}: every display tile, bottom first (base pattern, flow kind / corners / v, grass edges, the rest)`, () => {
      const rows = ref.rows;
      const W = rows[0].length;
      const H = rows.length;
      const v = view(rows, ref.season);
      const seasonKey = (k) => (k.includes('.v3.') ? k : ref.season && SEASONAL.some((c) => k.startsWith(`${PREFIX[c]}.`)) ? `${ref.season}.${k}` : k);
      const drawn = new Map();
      for (let cy = 0; cy * CHUNK < H; cy++) {
        for (let cx = 0; cx * CHUNK < W; cx++) {
          const here = new Map();
          for (const p of v.groundPiecesV2(cx, cy)) {
            if (p.quarter) continue;
            const id = `${(p.x - 8) / 16},${(p.y - 8) / 16}`;
            if (!here.has(id)) here.set(id, []);
            // (a flow shape: "<key>[~f]@<tint>", ~f mirrored left to right)
            const flow = p.tint !== undefined ? `${p.flip ? '~f' : ''}@#${p.tint.toString(16).padStart(6, '0')}` : '';
            here.get(id).push((p.anim ? p.key : seasonKey(p.key)) + flow);
          }
          for (const [id, keys] of here) if (!drawn.has(id)) drawn.set(id, keys.join('|'));
        }
      }
      let compared = 0;
      let flows = 0;
      let edges = 0;
      let flips = 0;
      const vs = new Set();
      const missing = new Set();
      for (let j = 0; j < H - 1; j++) {
        for (let i = 0; i < W - 1; i++) {
          const want = ref.draws[`${i},${j}`].split('|').map(engineKey).join('|');
          expect(drawn.get(`${i},${j}`), `${ref.name} ${i},${j}`).toBe(want);
          for (const piece of want.split('|')) {
            const k = piece.replace(/(?:~f)?@#[0-9a-f]{6}$/, '');
            if (piece.includes('~f')) flips++;
            if (k.startsWith('tile.water')) continue;
            if (!ART.has(k)) missing.add(k);
            if (k.includes('grassflow')) {
              flows++;
              vs.add(Number(k.split('.').at(-1)));
            }
            if (k.includes('grass.v3.edge.')) edges++;
          }
          compared++;
        }
      }
      expect([...missing]).toEqual([]);
      expect(compared).toBe((W - 1) * (H - 1));
      expect(flows).toBeGreaterThan(100);
      expect(edges).toBeGreaterThan(50);
      // the flow's v used as it comes (round 7: up to 11 / 15), some drawn mirrored
      if (ref.season === null) expect(Math.max(...vs)).toBeGreaterThanOrEqual(11);
      expect(flips).toBeGreaterThan(20);
    });
  }

  it('the base pattern of every block over the world\'s range is macro_of\'s (from -1, rows top to bottom)', () => {
    const { bx0, by0, rows } = REF.macro;
    const g = new MacroGrid();
    // (asked out of order: the grid fills itself without recursion)
    expect(g.at(64, 71)).toBe(rows[71 - by0][64 - bx0]);
    for (let r = 0; r < rows.length; r++) for (let c = 0; c < rows[r].length; c++) expect(g.at(bx0 + c, by0 + r), `${bx0 + c},${by0 + r}`).toBe(rows[r][c]);
    // never the same as the block on the left, above, above-left or above-right
    for (let by = 1; by < 72; by++) {
      for (let bx = 1; bx < 64; bx++) {
        const m = g.at(bx, by);
        expect([g.at(bx - 1, by), g.at(bx, by - 1), g.at(bx - 1, by - 1), g.at(bx + 1, by - 1)]).not.toContain(m);
      }
    }
  });

  it('flow_key of every display tile over a window (negative included) is the reference\'s', () => {
    const { i0, j0, rows } = REF.flow;
    let n = 0;
    for (let r = 0; r < rows.length; r++) {
      const cells = rows[r].split(' ');
      for (let c = 0; c < cells.length; c++) {
        const fk = flowKey(i0 + c, j0 + r);
        expect(fk ? `${fk[0]}${fk[1]}.${fk[2]}${fk[3] ? 'f' : ''}` : '.', `${i0 + c},${j0 + r}`).toBe(cells[c]);
        if (fk) {
          n++;
          expect(STORED).toContain(fk[1]);
          expect(fk[2]).toBeLessThan(flowVariants(fk[1]));
          for (const set of ['', 'winter.']) expect(ART.has(`${set}plains.grassflow.v3.${fk[1]}.${fk[2]}`), `${set}${fk[1]}.${fk[2]}`).toBe(true);
        }
      }
    }
    expect(n).toBeGreaterThan(3000);
  });

  it('the stored corner sets, their variant counts, the mirror pairs and FLOW_TINT are the reference\'s', () => {
    expect([...STORED]).toEqual(REF.stored);
    for (const b of STORED) expect(flowVariants(b), b).toBe(REF.variants[b]);
    for (const [m, b] of Object.entries(MIRROR)) expect(flipBits(m)).toBe(b);
    expect(Object.keys(MIRROR).length + STORED.length).toBe(15);
    for (const s of ['summer', 'autumn', 'winter']) for (const k of ['d', 'l']) expect(`#${FLOW_TINT[s][k].toString(16).padStart(6, '0')}`).toBe(REF.tints[s][k]);
  });

  it('hsh is the reference\'s 32-bit hash (negative coordinates too) and hash01 × 2³²', () => {
    expect(hsh(0, 0, 0)).toBe(0);
    for (const [x, y, s] of [[1, 2, 3], [-1, -5, 61], [255, 287, 91], [-3, 7, 34]]) expect(hsh(x, y, s)).toBe(hash01(x, y, s) * 2 ** 32);
    expect(flowCorner(0, 0)).toMatch(/^[dlm]$/);
  });
});

describe('v3 plains: seasons, keys, the flow\'s colour hook', () => {
  it('spring and no season draw summer\'s art; autumn / winter their own', () => {
    expect([null, 'spring', 'summer', 'autumn', 'winter'].map(v3Season)).toEqual(['summer', 'summer', 'summer', 'autumn', 'winter']);
    expect(seasonPrefix('spring')).toBe('');
    expect(v3PlainsBundles('spring')).toEqual(['v3:plains:summer', 'v3:plains:flow']);
    expect(v3PlainsBundles('autumn')).toEqual(['v3:plains:autumn', 'v3:plains:flow']);
    expect(v3PlainsBundles('winter')).toEqual(['v3:plains:winter']);
    expect(v3PlainsPartOf('winter.plains.grassflow.v3.0011.5')).toBe('winter');
    expect(v3PlainsPartOf('plains.grassflow.v3.0011.5')).toBe('flow');
    expect(v3PlainsPartOf('autumn.plains.grass.v3.edge.3.1')).toBe('autumn');
    expect(v3PlainsPartOf('plains.tree.v3.oak_l.2')).toBe('summer');
    expect(v3PlainsPartOf('plains.grass.12')).toBe(null);
    expect(v3PlainsPartOf('prop.v3.tuft')).toBe(null);
    const g = new MacroGrid();
    expect(baseKey(g, 'autumn', 5, 2)).toBe(`autumn.plains.grass.v3.${g.at(1, 0)}21`);
    expect(baseKey(g, null, -1, -1)).toBe(`plains.grass.v3.${g.at(-1, -1)}33`);
    expect(PATTERNS.length).toBe(8);
  });
  it('the flow is a grey shape (summer and autumn share one set, winter its own) times FLOW_TINT[season][kind], maybe mirrored', () => {
    const fk = /** @type {[string, string, number, boolean]} */ (['l', '0011', 6, true]);
    const has = (k) => ART.has(k);
    expect(flowLook('winter', fk, has)).toEqual({ key: 'winter.plains.grassflow.v3.0011.6', tint: 0xdce6f2, flip: true });
    expect(flowLook('autumn', ['d', '1111', 3, false], has)).toEqual({ key: 'plains.grassflow.v3.1111.3', tint: 0x744b28, flip: false });
    expect(flowLook('spring', ['d', '1111', 3, false], has)?.tint).toBe(0x335d3a);
    expect(flowLook('summer', fk, () => false)).toBe(null);
  });
});

describe('v3 plains trees and props', () => {
  const has = (k) => ART.has(k);
  it('every tree and prop kind has art in every season; trees sway 3 frames (bare winter broadleaves 1), grass and flowers 2', () => {
    for (const s of ['summer', 'autumn', 'winter']) {
      for (const k of ['oak_l', 'oak_m', 'pine', 'sapling']) expect(floraFrames(has, s, 'tree', k), `${s} ${k}`).toBe(s === 'winter' && k !== 'pine' ? 1 : 3);
      for (const [k, p] of Object.entries(PROPS)) expect(floraFrames(has, s, 'prop', k), `${s} ${k}`).toBe(p.frames);
    }
    expect(floraKey('autumn', 'tree', 'pine', 2)).toBe('autumn.plains.tree.v3.pine.2');
  });
  it('the tree kind by its room: the large broadleaf only with 2 free tiles round it, the sapling in a grove', () => {
    const count = (room) => {
      const n = {};
      for (let i = 0; i < 2000; i++) {
        const l = plainsTreeLook(room, hash01(i, 1, 931), hash01(i, 1, 932));
        const k = l.what === 'tree' ? l.kind : `prop.${l.kind}`;
        n[k] = (n[k] ?? 0) + 1;
      }
      return n;
    };
    expect(Object.keys(count(3)).sort()).toEqual(['oak_l', 'oak_m', 'pine']);
    expect(Object.keys(count(2)).sort()).toEqual(['oak_m', 'pine', 'sapling']);
    const grove = count(1);
    expect(Object.keys(grove).sort()).toEqual(['prop.log', 'sapling']);
    expect(grove['prop.log'] / 2000).toBeGreaterThan(0.03);
    expect(grove['prop.log'] / 2000).toBeLessThan(0.1);
    expect(treeKind(3, 0)).toBe('oak_l');
  });
  it('props on open ground never look solid; the solid-looking ones only at a tree\'s foot', () => {
    const open = new Set();
    const foot = new Set();
    let n = 0;
    for (let i = 0; i < 20000; i++) {
      const k = openProp(hash01(i, 0, 1), hash01(i, 0, 2), hash01(i, 0, 3), hash01(i, 0, 4), hash01(i, 0, 7) < 0.5);
      if (k) {
        open.add(k);
        n++;
      }
      const f = treeFootProp(hash01(i, 0, 5), hash01(i, 0, 6));
      if (f) foot.add(f);
    }
    for (const k of open) expect(PROPS[k].solid, k).toBe(false);
    expect([...open].sort()).toEqual(['clover', 'flowers_mix', 'flowers_white', 'flowers_yellow', 'mushrooms', 'pebbles', 'shrub', 'tallgrass', 'tuft']);
    expect([...foot].sort()).toEqual(['bush', 'bush_berry', 'mushrooms', 'rock_m', 'rock_s']);
    expect(n / 20000).toBeGreaterThan(0.03);
    expect(n / 20000).toBeLessThan(0.15);
  });
  it('sway: trees 0 / +1 / 0 / -1, grass 0 / 1, a slow wave (a step every 0.75 s), never a frame the art lacks', () => {
    const fr = [0, 1, 2, 3, 4, 5, 6, 7].map((s) => swayFrame(TREE_SWAY, 3, s));
    expect(fr).toEqual([0, 1, 0, 2, 0, 1, 0, 2]);
    expect(swayFrame(TREE_SWAY, 1, 1)).toBe(0);
    expect(swayFrame(PROP_SWAY, 2, -3)).toBe(1);
    expect(swayStep(10, 10, 0.75 + 10) - swayStep(10, 10, 10)).toBe(1);
    // the gust reaches the trees further east later
    expect(swayStep(0, 0, 5)).toBeGreaterThanOrEqual(swayStep(40, 0, 5));
  });
});

describe('v3 sheets: one per season', () => {
  it('the build packs a v3 group\'s autumn / winter frames apart; ?terrain=v2 drops all of its parts', () => {
    expect(['autumn.plains.tree.v3.pine.0', 'winter.x', 'plains.grass.v3.a00', 'hero.idle.down.0'].map(seasonPartOf)).toEqual(['autumn', 'winter', '', '']);
    const dir = new URL('../../src/art-release-v3/terrain/', import.meta.url).pathname;
    const w = packGroup(dir, (n) => seasonPartOf(n) === 'winter');
    expect(Object.keys(w.table.frames).every((k) => k.startsWith('winter.'))).toBe(true);
    expect(Object.keys(w.table.frames).length).toBe(V3.filter((k) => k.startsWith('winter.')).length);
    expect(w.table.width * w.table.height * 4).toBeLessThan(10 * 2 ** 20);
    const avail = ['terrain', 'terrain.autumn', 'terrain.winter', 'hero'];
    expect(v3ArtGroups(new URLSearchParams('v3=1'), avail)).toEqual(['v3/hero', 'v3/terrain', 'v3/terrain.autumn', 'v3/terrain.winter']);
    expect(v3ArtGroups(new URLSearchParams('v3=1&terrain=v2'), avail)).toEqual(['v3/hero']);
  }, 30000);
});
