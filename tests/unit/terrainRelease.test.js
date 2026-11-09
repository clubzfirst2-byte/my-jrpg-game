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
const EXPECTED = [
  ...GROUND,
  'tile.ramp', 'tile.pit', 'tile.vine',
  ...faces('earth'), ...faces('ruin'), ...faces('wall'), ...faces('stone'),
  'obj.tree', 'forest.pine', 'mountains.pine', 'obj.rock', 'obj.bramble', 'obj.stump', 'obj.cactus',
  'spring.obj.tree', 'autumn.obj.tree', 'winter.obj.tree', 'winter.forest.pine',
  ...lips('autumn'), ...lips('winter'),
];

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

  it('every name is in LIST.md, at its release size', () => {
    for (const n of EXPECTED) {
      expect(LIST.has(n), n).toBe(true);
      const { w, h, depth, type, interlace } = readPng(n);
      expect([depth, type, interlace], n).toEqual([8, 6, 0]);
      expect([w, h], n).toEqual(LIST.get(n));
    }
  });

  it('every pixel is fully opaque or fully transparent', () => {
    for (const n of EXPECTED) {
      const { w, h, px } = readPng(n);
      for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) expect([0, 255], `${n} ${x},${y}`).toContain(px(x, y)[3]);
    }
  });

  it('ground tiles are fully opaque', () => {
    for (const n of GROUND) {
      const { w, h, px } = readPng(n);
      let holes = 0;
      for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) if (px(x, y)[3] !== 255) holes++;
      expect(holes, n).toBe(0);
    }
  });

  it('ground tiles wrap without a seam (edge-to-edge change no larger than inside the tile)', () => {
    for (const n of GROUND) {
      const { px } = readPng(n);
      const colDiff = (x0, x1) => range(32).reduce((s, y) => s + Math.abs(light(px(x0, y)) - light(px(x1, y))), 0) / 32;
      const rowDiff = (y0, y1) => range(32).reduce((s, x) => s + Math.abs(light(px(x, y0)) - light(px(x, y1))), 0) / 32;
      const inside = Math.max(...range(31).map((i) => colDiff(i, i + 1)), ...range(31).map((i) => rowDiff(i, i + 1)));
      expect(colDiff(31, 0), `${n} left/right`).toBeLessThanOrEqual(inside + 1);
      expect(rowDiff(31, 0), `${n} top/bottom`).toBeLessThanOrEqual(inside + 1);
    }
  });

  it('objects stand on their last row (feet anchor) and leave the top-left corner empty', () => {
    for (const n of ['obj.tree', 'spring.obj.tree', 'autumn.obj.tree', 'winter.obj.tree', 'forest.pine', 'winter.forest.pine', 'mountains.pine', 'obj.rock', 'obj.bramble', 'obj.stump', 'obj.cactus']) {
      const { w, h, px } = readPng(n);
      expect(px(0, 0)[3], n).toBe(0);
      expect(range(w).some((x) => px(x, h - 1)[3] === 255), n).toBe(true);
      expect(px(Math.floor(w / 2), h - 1)[3], `${n} bottom centre`).toBe(255);
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
