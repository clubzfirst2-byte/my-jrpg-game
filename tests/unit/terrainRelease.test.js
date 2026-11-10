import { describe, it, expect } from 'vitest';
import { readdirSync, readFileSync } from 'node:fs';
import { inflateSync } from 'node:zlib';

// Terrain release art (src/art-release/terrain, made by tools/terrain_release/gen_release.py):
// exact names, LIST.md sizes, alpha 0 / 255 only, ground tiles wrap without a seam.
const DIR = new URL('../../src/art-release/terrain/', import.meta.url);

const range = (n) => [...Array(n).keys()];
const FACE_KINDS = ['top', 'mid', 'mid-base', 'top-base'];
const faces = (mat) => [4, 8].flatMap((h) => FACE_KINDS.map((k) => `face.${mat}.${k}.${h}`));
const lips = (season) => [4, 8].flatMap((h) => ['top', 'top-base'].map((k) => `${season}.face.earth.${k}.${h}`));
const seasonGround = [...range(3).map((i) => `tile.grass.${i}`), ...range(4).map((i) => `plains.grass.${i}`), ...range(4).map((i) => `lake.grass.${i}`)];

/** Ground tiles (32×32, repeat on every side). */
const GROUND = [
  ...range(3).map((i) => `tile.grass.${i}`),
  'tile.path', 'tile.sand', 'tile.water.0', 'tile.water.1', 'tile.ruin', 'tile.metal', 'tile.wood', 'tile.walltop', 'tile.dark',
  ...range(3).map((i) => `desert.sand.${i}`),
  ...['plains.grass', 'forest.grass', 'mountains.snow', 'lake.grass'].flatMap((k) => range(4).map((i) => `${k}.${i}`)),
  ...seasonGround.map((n) => `autumn.${n}`),
  ...[...seasonGround, ...range(4).map((i) => `forest.grass.${i}`)].map((n) => `winter.${n}`),
];
/** v1.0: the 111 sprites of docs/art-kit/LIST.md. */
const V10 = [
  ...GROUND,
  'tile.ramp', 'tile.pit', 'tile.vine',
  ...faces('earth'), ...faces('ruin'), ...faces('wall'), ...faces('stone'),
  'obj.tree', 'forest.pine', 'mountains.pine', 'obj.rock', 'obj.bramble', 'obj.stump', 'obj.cactus',
  'spring.obj.tree', 'autumn.obj.tree', 'winter.obj.tree', 'winter.forest.pine',
  ...lips('autumn'), ...lips('winter'),
];

// v1.1 (docs/art-release/terrain/NAMES.md): water edges, cliff band variants, plateau faces, autumn
// in the forest and the mountains. Not in LIST.md: sizes by kind (tiles 32×32, faces 32×8 / 32×16, pines 32×60).
const CORNERS = ['ne', 'se', 'sw', 'nw'];
/** Water-edge sets: [prefix, its land tile (null = an overlay, transparent on the land side)]. */
const EDGE_SETS = [['tile.shore', 'tile.sand'], ['tile.shore-desert', 'desert.sand.0'], ['tile.bank', null]];
const edgeKeys = (p) => [0, 1].flatMap((f) => [...range(15).map((m) => `${p}.${m + 1}.${f}`), ...CORNERS.map((c) => `${p}.inner.${c}.${f}`)]);
const variants = (names) => names.flatMap((n) => [`${n}.v1`, `${n}.v2`]);
const GROUND11 = ['autumn.forest.grass', 'autumn.mountains.snow'].flatMap((k) => range(4).map((i) => `${k}.${i}`));
const V11 = [
  ...EDGE_SETS.flatMap(([p]) => edgeKeys(p)),
  ...variants([...faces('earth'), ...faces('ruin'), ...faces('wall'), ...faces('stone')]),
  ...variants([...lips('autumn'), ...lips('winter')]),
  ...faces('sand'), ...faces('desert'), ...faces('path'),
  ...GROUND11, 'autumn.forest.pine', 'autumn.mountains.pine',
  ...[4, 8].flatMap((h) => ['top', 'top-base'].map((k) => `autumn.face.stone.${k}.${h}`)).flatMap((n) => [n, `${n}.v1`, `${n}.v2`]),
];
const EXPECTED = [...V10, ...V11];
/** @param {string} n */
const v11Size = (n) => {
  const base = n.replace(/\.v\d$/, '');
  if (`.${base}`.includes('.face.')) return [32, base.endsWith('.4') ? 8 : 16];
  return base.endsWith('.pine') ? [32, 60] : [32, 32];
};

/** name -> [w, h] from docs/art-kit/LIST.md. */
const LIST = new Map(
  [...readFileSync(new URL('../../docs/art-kit/LIST.md', import.meta.url), 'utf8').matchAll(/\| `([^`]+)` \| (\d+)×(\d+)/g)].map((m) => [m[1], [Number(m[2]), Number(m[3])]]),
);

/** Decodes an 8-bit RGBA, non-interlaced PNG (what Pillow writes) into rows of RGBA bytes. */
function readPng(name) {
  const buf = readFileSync(new URL(`${name}.png`, DIR));
  const w = buf.readUInt32BE(16);
  const h = buf.readUInt32BE(20);
  const [depth, type, , , interlace] = buf.subarray(24, 29);
  const idat = [];
  for (let p = 8; p < buf.length; ) {
    const n = buf.readUInt32BE(p);
    if (buf.toString('ascii', p + 4, p + 8) === 'IDAT') idat.push(buf.subarray(p + 8, p + 8 + n));
    p += 12 + n;
  }
  const raw = inflateSync(Buffer.concat(idat));
  const bpp = 4;
  const stride = w * bpp;
  const out = Buffer.alloc(h * stride);
  for (let y = 0; y < h; y++) {
    const f = raw[y * (stride + 1)];
    for (let i = 0; i < stride; i++) {
      const x = raw[y * (stride + 1) + 1 + i];
      const a = i >= bpp ? out[y * stride + i - bpp] : 0;
      const b = y > 0 ? out[(y - 1) * stride + i] : 0;
      const c = i >= bpp && y > 0 ? out[(y - 1) * stride + i - bpp] : 0;
      let v = x;
      if (f === 1) v = x + a;
      else if (f === 2) v = x + b;
      else if (f === 3) v = x + ((a + b) >> 1);
      else if (f === 4) {
        const p = a + b - c;
        const pa = Math.abs(p - a);
        const pb = Math.abs(p - b);
        const pc = Math.abs(p - c);
        v = x + (pa <= pb && pa <= pc ? a : pb <= pc ? b : c);
      }
      out[y * stride + i] = v & 255;
    }
  }
  const px = (x, y) => [...out.subarray(y * stride + x * 4, y * stride + x * 4 + 4)];
  return { w, h, depth, type, interlace, px };
}

const light = ([r, g, b]) => 0.299 * r + 0.587 * g + 0.114 * b;

describe('terrain release art', () => {
  const files = readdirSync(DIR).filter((f) => f.endsWith('.png')).map((f) => f.slice(0, -4));

  it('has exactly the expected names (no file outside the list)', () => {
    expect(new Set(EXPECTED).size).toBe(EXPECTED.length);
    expect(files.sort()).toEqual([...EXPECTED].sort());
  });

  it('every v1.0 name is in LIST.md, at its release size; v1.1 sizes by kind', () => {
    for (const n of EXPECTED) {
      const { w, h, depth, type, interlace } = readPng(n);
      expect([depth, type, interlace], n).toEqual([8, 6, 0]);
      if (V10.includes(n)) {
        expect(LIST.has(n), n).toBe(true);
        expect([w, h], n).toEqual(LIST.get(n));
      } else {
        expect([w, h], n).toEqual(v11Size(n));
      }
    }
  });

  it('every pixel is fully opaque or fully transparent', () => {
    for (const n of EXPECTED) {
      const { w, h, px } = readPng(n);
      for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) expect([0, 255], `${n} ${x},${y}`).toContain(px(x, y)[3]);
    }
  });

  it('ground tiles (and the full water-edge tiles) are fully opaque', () => {
    for (const n of [...GROUND, ...GROUND11, ...edgeKeys('tile.shore'), ...edgeKeys('tile.shore-desert')]) {
      const { w, h, px } = readPng(n);
      let holes = 0;
      for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) if (px(x, y)[3] !== 255) holes++;
      expect(holes, n).toBe(0);
    }
  });

  it('ground tiles wrap without a seam (edge-to-edge change no larger than inside the tile)', () => {
    for (const n of [...GROUND, ...GROUND11]) {
      const { px } = readPng(n);
      const colDiff = (x0, x1) => range(32).reduce((s, y) => s + Math.abs(light(px(x0, y)) - light(px(x1, y))), 0) / 32;
      const rowDiff = (y0, y1) => range(32).reduce((s, x) => s + Math.abs(light(px(x, y0)) - light(px(x, y1))), 0) / 32;
      const inside = Math.max(...range(31).map((i) => colDiff(i, i + 1)), ...range(31).map((i) => rowDiff(i, i + 1)));
      expect(colDiff(31, 0), `${n} left/right`).toBeLessThanOrEqual(inside + 1);
      expect(rowDiff(31, 0), `${n} top/bottom`).toBeLessThanOrEqual(inside + 1);
    }
  });

  it('objects stand on their last row (feet anchor) and leave the top-left corner empty', () => {
    for (const n of ['obj.tree', 'spring.obj.tree', 'autumn.obj.tree', 'winter.obj.tree', 'forest.pine', 'winter.forest.pine', 'mountains.pine', 'autumn.forest.pine', 'autumn.mountains.pine', 'obj.rock', 'obj.bramble', 'obj.stump', 'obj.cactus']) {
      const { w, h, px } = readPng(n);
      expect(px(0, 0)[3], n).toBe(0);
      expect(range(w).some((x) => px(x, h - 1)[3] === 255), n).toBe(true);
      expect(px(Math.floor(w / 2), h - 1)[3], `${n} bottom centre`).toBe(255);
    }
  });

  it('water edges: each side that touches water joins tile.water of the same frame pixel for pixel', () => {
    const sides = [[1, (k) => [k, 0]], [2, (k) => [31, k]], [4, (k) => [k, 31]], [8, (k) => [0, k]]];
    for (const [p] of EDGE_SETS) {
      for (const f of [0, 1]) {
        const water = readPng(`tile.water.${f}`);
        for (let m = 1; m < 16; m++) {
          const t = readPng(`${p}.${m}.${f}`);
          for (const [bit, at] of sides) {
            if (!(m & bit)) continue;
            for (let k = 0; k < 32; k++) expect(t.px(...at(k)).join(), `${p}.${m}.${f} side ${bit} @${k}`).toBe(water.px(...at(k)).join());
          }
        }
      }
    }
  });

  it('water edges: the land side joins the plain land tile (a side away from water, outside the water bands)', () => {
    for (const [p, land] of EDGE_SETS) {
      if (!land) continue;
      const g = readPng(land);
      for (const f of [0, 1]) {
        // mask 1 (water north): the south row is the plain land's; mask 4 (water south): the north row
        for (const [m, y] of [[1, 31], [4, 0], [2, null], [8, null]]) {
          const t = readPng(`${p}.${m}.${f}`);
          if (y !== null) for (let x = 0; x < 32; x++) expect(t.px(x, y).join(), `${p}.${m}.${f} @${x},${y}`).toBe(g.px(x, y).join());
          else for (let yy = 0; yy < 32; yy++) {
            const x = m === 2 ? 0 : 31; // the side away from the water
            expect(t.px(x, yy).join(), `${p}.${m}.${f} @${x},${yy}`).toBe(g.px(x, yy).join());
          }
        }
      }
    }
  });

  it('the bank overlays are transparent on the land side and opaque on the water side', () => {
    for (const f of [0, 1]) {
      const t = readPng(`tile.bank.1.${f}`);
      expect(t.px(16, 0)[3]).toBe(255);
      expect(t.px(16, 31)[3]).toBe(0);
    }
  });

  it('cliff variants join the other variants: earth / stone keep the edge columns, ruin / wall the course rows', () => {
    for (const mat of ['earth', 'ruin', 'wall', 'stone']) {
      for (const n of faces(mat)) {
        const a = readPng(n);
        for (const v of ['v1', 'v2']) {
          const b = readPng(`${n}.${v}`);
          if (mat === 'earth' || mat === 'stone') {
            // the lip, lit band and dark base follow per-column profiles shared by all variants
            const diff = (x) => range(a.h).reduce((s, y) => s + Math.abs(light(a.px(x, y)) - light(b.px(x, y))), 0) / a.h;
            expect(diff(0) + diff(31), `${n}.${v}`).toBeLessThan(12);
          } else {
            // blocks: other joint positions, the same courses (row brightness) so the rows line up
            const row = (t, y) => range(32).reduce((s, x) => s + light(t.px(x, y)), 0) / 32;
            for (let y = 0; y < a.h; y++) expect(Math.abs(row(a, y) - row(b, y)), `${n}.${v} row ${y}`).toBeLessThan(25);
          }
        }
      }
    }
  });

  it('the two water frames differ by 12-30 px (guide 3.5)', () => {
    const a = readPng('tile.water.0');
    const b = readPng('tile.water.1');
    let d = 0;
    for (let y = 0; y < 32; y++) for (let x = 0; x < 32; x++) if (a.px(x, y).join() !== b.px(x, y).join()) d++;
    expect(d).toBeGreaterThanOrEqual(12);
    expect(d).toBeLessThanOrEqual(30);
  });
});
