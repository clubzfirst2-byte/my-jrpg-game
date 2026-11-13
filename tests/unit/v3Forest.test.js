import { describe, it, expect } from 'vitest';
import { readFileSync, readdirSync } from 'node:fs';
import { GameView, CHUNK } from '../../src/view/gameView.js';
import { Ground, Shape } from '../../src/game/world/tilemap.js';
import { PREFIX, SEASONAL, PRIORITY, deepMap, landKey, maskOf } from '../../src/view/groundV2.js';
import { chunkRange, CHUNK_KEEP_MARGIN_TILES, CHUNK_LOAD_MARGIN_TILES } from '../../src/view/chunkRange.js';
import { createGameState, MAPS } from '../../src/game/state.js';
import { regionAt } from '../../src/game/world/world.js';
import { hash01 } from '../../src/view/placement.js';
import {
  FOREST_FLOW_TINT, FOREST_TREES, FOREST_PROPS, forestFlowLook, forestTreeKind, forestTreeLook, forestFootProp, forestOpenProp, plainsPineBanned, rootsOffset,
  v3ForestBundles, v3ForestPartOf, winterMaskOf, winterPriority,
} from '../../src/view/v3Forest.js';
import { floraFrames, plainsTreeLook, treeKind, v3PinePartOf, v3PlainsPartOf } from '../../src/view/v3Plains.js';

// Graphics v3 forest (docs/art-release-v3/FOREST.md, NAMES.md 2.1): the engine places the forest's v3 ground
// exactly as the art side's reference does. tests/fixtures/forest_v3_ref.json is written by
// tools/forest_v3_ref_fixture.py, which runs the reference unchanged (render_ref.render_v2, gen_ground_v3's
// macro_of / flow_key, gen_forest_v3's FOREST_FLOW_TINT, compare_forest_v3.winter_forest_v for the winter
// exchange) on the art side's map, the independent inspection's border map, 3 random maps and a forest
// with a path, sand and a pond.

const REF = JSON.parse(readFileSync(new URL('../fixtures/forest_v3_ref.json', import.meta.url), 'utf8'));
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

/** A reference key as the engine names it (as v3PlainsRef.test.js). */
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

/** Every display tile's pieces as the engine draws them ("key[~f]@#tint" for a flow shape), by "i,j". */
function engineDraws(v, W, H, season) {
  const seasonKey = (k) => (k.includes('.v3.') ? k : season && SEASONAL.some((c) => k.startsWith(`${PREFIX[c]}.`)) ? `${season}.${k}` : k);
  const drawn = new Map();
  for (let cy = 0; cy * CHUNK < H; cy++) {
    for (let cx = 0; cx * CHUNK < W; cx++) {
      const here = new Map();
      for (const p of v.groundPiecesV2(cx, cy)) {
        if (p.quarter) continue;
        const id = `${(p.x - 8) / 16},${(p.y - 8) / 16}`;
        if (!here.has(id)) here.set(id, []);
        const flow = p.tint !== undefined ? `${p.flip ? '~f' : ''}@#${p.tint.toString(16).padStart(6, '0')}` : '';
        here.get(id).push((p.anim ? p.key : seasonKey(p.key)) + flow);
      }
      for (const [id, keys] of here) if (!drawn.has(id)) drawn.set(id, keys.join('|'));
    }
  }
  return drawn;
}

describe('v3 forest ground: the engine draws what the art side\'s reference draws', () => {
  for (const ref of REF.maps) {
    it(`${ref.name}: every display tile, bottom first (base, flow, forest and plains edges; winter: the exchange of NAMES.md 2.1)`, () => {
      const rows = ref.rows;
      const W = rows[0].length;
      const H = rows.length;
      const drawn = engineDraws(view(rows, ref.season), W, H, ref.season);
      const n = { tiles: 0, base: 0, flow: 0, edges: 0, swapped: 0 };
      const missing = new Set();
      for (let j = 0; j < H - 1; j++) {
        for (let i = 0; i < W - 1; i++) {
          const want = ref.draws[`${i},${j}`].split('|').map(engineKey).join('|');
          expect(drawn.get(`${i},${j}`), `${ref.name} ${i},${j}`).toBe(want);
          for (const piece of want.split('|')) {
            const k = piece.replace(/(?:~f)?@#[0-9a-f]{6}$/, '');
            if (!k.startsWith('tile.water') && !ART.has(k)) missing.add(k);
            if (/forest\.grass\.v3\.[a-h]\d\d$/.test(k)) n.base++;
            if (k.includes('forest.grassflow')) n.flow++;
            if (/(?:forest|plains)\.grass\.v3\.edge\./.test(k)) n.edges++;
          }
          if (ref.season === 'winter' && /plains\.grass\.v3\.[a-h]\d\d\|winter\.forest\.grass\.v3\.edge\./.test(want)) n.swapped++;
          n.tiles++;
        }
      }
      expect([...missing]).toEqual([]);
      expect(n.tiles).toBe((W - 1) * (H - 1));
      expect(n.base).toBeGreaterThan(100);
      if (!ref.name.startsWith('random')) expect(n.flow).toBeGreaterThan(50);
      expect(n.edges).toBeGreaterThan(30);
      // winter: every forest / plains tile is the plains winter base with the forest winter edge over it
      if (ref.season === 'winter' && !ref.name.startsWith('forestpath')) expect(n.swapped).toBeGreaterThan(30);
      if (ref.season !== 'winter') expect(n.swapped).toBe(0);
    });
  }

  it('the inspection\'s border map in winter: 140 forest / plains tiles, every forest edge v as winter_forest_v (diagonal-only touches included)', () => {
    const ref = REF.maps.find((m) => m.name === 'inspection73x41.winter');
    let border = 0;
    for (const keys of Object.values(ref.draws)) if (keys.includes('winter.forest.grass.v3.edge.') && keys.startsWith('winter.plains.grass.v3.')) border++;
    expect(border).toBe(140);
  });

  it('winter order: forest and plains exchanged only on a tile holding both; masks read in each tile\'s own order', () => {
    expect(winterPriority(['moss', 'plains', 'moss', 'moss']).indexOf('plains')).toBeLessThan(winterPriority(['moss', 'plains', 'moss', 'moss']).indexOf('moss'));
    expect(winterPriority(['moss', 'path', 'moss', 'moss'])).toBe(PRIORITY);
    // two forest cells touching only diagonally: that tile's forest mask is 9 in winter (15 in the v2 order)
    const rows = ['mp', 'pm'];
    const at = (x, y) => CLASS[rows[Math.max(0, Math.min(1, y))][Math.max(0, Math.min(1, x))]];
    expect(winterMaskOf('moss', 0, 0, at)).toBe(9);
    expect(maskOf('moss', 0, 0, at)).toBe(15);
  });

  it('FOREST_FLOW_TINT is gen_forest_v3.flow_tints; the forest\'s flow is its own grey shape times it', () => {
    for (const s of ['summer', 'autumn', 'winter']) for (const k of ['d', 'l']) expect(`#${FOREST_FLOW_TINT[s][k].toString(16).padStart(6, '0')}`).toBe(REF.tints[s][k]);
    const has = (k) => ART.has(k);
    expect(forestFlowLook('autumn', ['d', '1111', 2, true], has)).toEqual({ key: 'forest.grassflow.v3.1111.2', tint: 0x4a3c20, flip: true });
    expect(forestFlowLook('winter', ['l', '0011', 6, false], has)).toEqual({ key: 'winter.forest.grassflow.v3.0011.6', tint: 0xfafcff, flip: false });
  });
});

describe('v3 forest art: bundles, trees and props', () => {
  it('every forest v3 file is in exactly one bundle part; summer and autumn share the flow shapes', () => {
    const forest = V3.filter((k) => /forest\./.test(k));
    expect(forest.length).toBe(803);
    const parts = {};
    for (const k of forest) {
      const p = v3ForestPartOf(k);
      if (p === null) {
        expect(k).toMatch(/^(?:(?:autumn|winter)\.)?forest\.pine$/); // (the v1 name: region:forest's slot)
        continue;
      }
      parts[p] = (parts[p] ?? 0) + 1;
      expect(v3PlainsPartOf(k)).toBe(null);
    }
    expect(parts.flow).toBe(104);
    expect(parts.winter).toBe(128 + 52 + 104 + 10 + 6);
    expect(parts.summer).toBe(128 + 52 + 12 + 6);
    expect(parts.autumn).toBe(128 + 52 + 12 + 6);
    expect(v3ForestBundles('spring')).toEqual(['v3:forest:summer', 'v3:forest:flow']);
    expect(v3ForestBundles('winter')).toEqual(['v3:forest:winter']);
    expect(v3PinePartOf('autumn.plains.tree.v3.pine.1')).toBe('pine.autumn');
    expect(v3PlainsPartOf('autumn.plains.tree.v3.pine.1')).toBe(null);
  });

  it('trees: 4 kinds, sway 3 frames (the bare winter birch 1); props: fern sways 2', () => {
    const has = (k) => ART.has(k);
    for (const s of ['summer', 'autumn', 'winter']) {
      for (const k of Object.keys(FOREST_TREES)) expect(floraFrames(has, s, 'tree', k, 'forest'), `${s} ${k}`).toBe(s === 'winter' && k === 'birch' ? 1 : 3);
      for (const [k, p] of Object.entries(FOREST_PROPS)) expect(floraFrames(has, s, 'prop', k, 'forest'), `${s} ${k}`).toBe(p.frames);
    }
  });

  it('the tree kind by its room: the old large pine only with room or standing out of the thick of the wood; mostly small pines in it', () => {
    const count = (room, dense) => {
      const n = {};
      for (let i = 0; i < 4000; i++) {
        const l = forestTreeLook(room, dense, hash01(i, 3, 961), hash01(i, 3, 962));
        const k = l.what === 'tree' ? l.kind : `prop.${l.kind}`;
        n[k] = (n[k] ?? 0) + 1;
      }
      return n;
    };
    expect(Object.keys(count(3, false)).sort()).toEqual(['birch', 'pine_l', 'spruce']);
    expect(Object.keys(count(2, false)).sort()).toEqual(['birch', 'pine_s', 'spruce']);
    expect(Object.keys(count(1, false)).sort()).toEqual(['birch', 'pine_s', 'prop.log_moss', 'spruce']);
    const dense = count(1, true);
    expect(Object.keys(dense).sort()).toEqual(['pine_l', 'pine_s', 'spruce']);
    expect(dense.pine_s / 4000).toBeGreaterThan(0.4);
    expect(forestTreeKind(3, false, 0)).toBe('pine_l');
  });

  it('props: the solid-looking ones (mossy rock, log) never on open moss; roots always at a trunk, 4-12 px beside it, in front', () => {
    const open = new Set();
    const foot = new Set();
    for (let i = 0; i < 20000; i++) {
      const k = forestOpenProp(hash01(i, 0, 1), hash01(i, 0, 3), hash01(i, 0, 4), hash01(i, 0, 7) < 0.5);
      if (k) open.add(k);
      const f = forestFootProp(hash01(i, 0, 5), hash01(i, 0, 6));
      if (f) foot.add(f);
      const [dx, dy] = rootsOffset(i, 7);
      expect(Math.abs(dx)).toBeGreaterThanOrEqual(4);
      expect(Math.abs(dx)).toBeLessThanOrEqual(12);
      expect([1, 2]).toContain(dy);
    }
    for (const k of open) expect(FOREST_PROPS[k].solid, k).toBe(false);
    expect([...open].sort()).toEqual(['fern', 'toadstool']);
    expect([...foot].sort()).toEqual(['fern', 'rock_moss', 'roots', 'toadstool']);
  });
});

// --- the plains pine near the forest (FOREST.md 4, NAMES.md 4) ---

/** A view of a real map with only what the tree looks and the chunk bundles need. */
function mapView(name) {
  const state = createGameState(MAPS[name]);
  const v = Object.create(GameView.prototype);
  Object.assign(v, {
    v3: true, map: state.map, regions: state.regions, season: null, groundV2: true, v2Tiles: new Map(), sandUnderTrees: new Set(), v3Looks: new WeakMap(), v3Trees: null, v3Others: null, v3PineBanned: null,
    assets: { builders: { has: () => true }, hasTexture: () => true },
  });
  return v;
}

/** The plains trees of a map and whether each is drawn as the pine. */
function plainsTrees(v) {
  return v.map.objects.filter((o) => o.type === 'tree' && regionAt(v.regions, o.tx, o.ty)?.id === 'plains').map((o) => ({ o, pine: v.v3TreeLook(o).kind === 'pine' }));
}

describe('the plains pine is never within 2 chunks of the forest (FOREST.md 4)', () => {
  for (const name of ['world', 'forestedge']) {
    it(`${name}: no plains tree drawn as the pine in a chunk within 2 of a chunk the forest region's rectangle overlaps; pines elsewhere`, () => {
      const v = mapView(name);
      const forest = v.regions.filter((r) => r.id === 'forest');
      const A = new Set();
      for (const r of forest) for (let cy = Math.floor(r.ty / CHUNK); cy * CHUNK < r.ty + r.th; cy++) for (let cx = Math.floor(r.tx / CHUNK); cx * CHUNK < r.tx + r.tw; cx++) {
        // (the same overlap test as gameView.chunkBundles)
        const x0 = cx * CHUNK;
        const y0 = cy * CHUNK;
        if (r.tx < x0 + CHUNK && r.tx + r.tw > x0 && r.ty < y0 + CHUNK && r.ty + r.th > y0) A.add(`${cx},${cy}`);
      }
      const near = (tx, ty) => [...A].some((a) => {
        const [ax, ay] = a.split(',').map(Number);
        return Math.max(Math.abs(Math.floor(tx / CHUNK) - ax), Math.abs(Math.floor(ty / CHUNK) - ay)) <= 2;
      });
      const trees = plainsTrees(v);
      let banned = 0;
      let before = 0;
      for (const t of trees) {
        const o = t.o;
        const was = plainsTreeLook(v.v3TreeRoom(o.tx, o.ty), hash01(o.tx, o.ty, 931), hash01(o.tx, o.ty, 932)).kind === 'pine';
        if (near(o.tx, o.ty)) {
          banned++;
          if (was) before++;
          expect(t.pine, `${o.tx},${o.ty}`).toBe(false);
        } else expect(t.pine).toBe(was); // (elsewhere the look is as before)
        expect(plainsPineBanned(v.regions, CHUNK)(o.tx, o.ty)).toBe(near(o.tx, o.ty));
      }
      console.log(`${name}: plains trees ${trees.length}, in the banned chunks ${banned} (pines there before the rule: ${before}), pines now ${trees.filter((t) => t.pine).length}`);
      expect(banned).toBeGreaterThan(0);
      expect(trees.filter((t) => t.pine).length).toBeGreaterThan(0);
      // the pine's share goes to the others (treeKind)
      expect(treeKind(3, 0.5, false)).toBe('oak_l');
      expect(treeKind(3, 0.7, false)).toBe('oak_m');
      expect(treeKind(2, 0.6, false)).toBe('oak_m');
      expect(treeKind(2, 0.8, false)).toBe('sapling');
    });
  }

  it('forestedge: wherever the view is (SE and 15 Pro), while a chunk holding the forest\'s v3 bundles can be kept, no chunk holding the plains pine\'s bundle can be, and no plains pine is on screen', () => {
    const v = mapView('forestedge');
    const ts = 16;
    const map = v.map;
    const ncx = Math.ceil(map.width / CHUNK);
    const ncy = Math.ceil(map.height / CHUNK);
    const forestChunk = new Map();
    const pineChunk = new Map();
    for (let cy = 0; cy < ncy; cy++) for (let cx = 0; cx < ncx; cx++) {
      forestChunk.set(`${cx},${cy}`, v.v3ForestBundlesOf(cx, cy).length > 0);
      pineChunk.set(`${cx},${cy}`, v.v3PineBundleOf(cx, cy) !== null);
    }
    expect([...pineChunk.values()].some(Boolean)).toBe(true);
    const pines = plainsTrees(v).filter((t) => t.pine).map((t) => t.o);
    let both = 0;
    let shown = 0;
    let views = 0;
    for (const [vwT, vhT] of [[20.8, 11.7], [20.0, 9.2]]) {
      const vw = vwT * ts;
      const vh = vhT * ts;
      for (let oy = 0; oy <= map.height * ts - vh; oy += 8) {
        for (let ox = 0; ox <= map.width * ts - vw; ox += 8) {
          // every chunk in the keep range may have been built before (gameView.updateChunks)
          const keep = chunkRange({ x: ox, y: oy }, vw, vh, ts * CHUNK_KEEP_MARGIN_TILES, { chunkPx: CHUNK * ts, ncx, ncy });
          let f = false;
          let p = false;
          for (let cy = keep.y0; cy <= keep.y1; cy++) for (let cx = keep.x0; cx <= keep.x1; cx++) {
            f ||= forestChunk.get(`${cx},${cy}`);
            p ||= pineChunk.get(`${cx},${cy}`);
          }
          views++;
          if (f && p) both++;
          if (!f) continue;
          // a plains pine (24 × 50 game px on its feet) in the view
          for (const o of pines) {
            const x = o.tx * ts + 8;
            const y = o.ty * ts + 16;
            if (x + 12 > ox && x - 12 < ox + vw && y > oy && y - 50 < oy + vh) shown++;
          }
        }
      }
    }
    expect(views).toBeGreaterThan(10000);
    expect(both).toBe(0);
    expect(shown).toBe(0);
  }, 60_000);

  it('the reach (FOREST.md 4): a plains pine on screen while a chunk of A is kept stands within 34 tiles across / 28 down or up of A\'s chunks: 2 chunks', () => {
    const ts = 16;
    const size = CHUNK * ts;
    let wx = 0;
    let wy = 0;
    let wc = 0;
    const [vw, vh] = [20.8 * ts, 11.7 * ts];
    const HALF = 0.75;
    const UP = 200 / 64;
    for (let off = 0; off < CHUNK; off += 3) {
      for (const len of [1, 31, 33, 70]) {
        const r = { tx: 10 * CHUNK + off, ty: 10 * CHUNK + off, tw: len, th: len };
        const ax0 = Math.floor(r.tx / CHUNK);
        const ax1 = Math.floor((r.tx + r.tw - 1) / CHUNK);
        const ay0 = Math.floor(r.ty / CHUNK);
        const ay1 = Math.floor((r.ty + r.th - 1) / CHUNK);
        const E = { x0: ax0 * CHUNK, x1: (ax1 + 1) * CHUNK - 1, y0: ay0 * CHUNK, y1: (ay1 + 1) * CHUNK - 1 };
        for (let oy = (E.y0 - 50) * ts; oy <= (E.y1 + 50) * ts; oy += 16) {
          for (let ox = (E.x0 - 60) * ts; ox <= (E.x1 + 60) * ts; ox += 16) {
            const keep = chunkRange({ x: ox, y: oy }, vw, vh, ts * CHUNK_KEEP_MARGIN_TILES, { chunkPx: size, ncx: 40, ncy: 40 });
            if (!(ax1 >= keep.x0 && ax0 <= keep.x1 && ay1 >= keep.y0 && ay0 <= keep.y1)) continue;
            const X0 = ox / ts;
            const X1 = (ox + vw) / ts;
            const Y0 = oy / ts;
            const Y1 = (oy + vh) / ts;
            for (let fy = Math.floor(Y0) - 1; fy <= Math.ceil(Y1 + UP); fy++) {
              for (let fx = Math.floor(X0 - 2); fx <= Math.ceil(X1 + 1); fx++) {
                if (fx + 0.5 + HALF <= X0 || fx + 0.5 - HALF >= X1 || fy + 1 <= Y0 || fy + 1 - UP >= Y1) continue;
                const dx = fx < E.x0 ? E.x0 - fx : fx > E.x1 ? fx - E.x1 : 0;
                const dy = fy < E.y0 ? E.y0 - fy : fy > E.y1 ? fy - E.y1 : 0;
                const cx = Math.floor(fx / CHUNK);
                const cy = Math.floor(fy / CHUNK);
                wc = Math.max(wc, cx < ax0 ? ax0 - cx : cx > ax1 ? cx - ax1 : 0, cy < ay0 ? ay0 - cy : cy > ay1 ? cy - ay1 : 0);
                if (dy === 0) wx = Math.max(wx, dx);
                if (dx === 0) wy = Math.max(wy, dy);
              }
            }
          }
        }
      }
    }
    console.log(`reach from A's chunks: across ${wx}, down / up ${wy} tiles, ${wc} chunks (keep ${CHUNK_KEEP_MARGIN_TILES}, build ${CHUNK_LOAD_MARGIN_TILES})`);
    expect(wx).toBeLessThanOrEqual(34);
    expect(wy).toBeLessThanOrEqual(28);
    expect(Math.ceil((CHUNK_KEEP_MARGIN_TILES + 21 + 1) / CHUNK)).toBe(2);
    expect(wc).toBe(2);
  }, 60_000);
});
