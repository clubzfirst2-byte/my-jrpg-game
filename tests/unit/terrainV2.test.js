import { describe, it, expect } from 'vitest';
import { readdirSync, readFileSync } from 'node:fs';
import { inflateSync } from 'node:zlib';

// Ground v2 (gfx W1, src/art-release-v2/terrain, made by tools/terrain_v2/gen_v2.py; scheme in
// docs/art-release-v2/terrain/NAMES.md): the group holds every v1 terrain key (redrawn or copied),
// names, sizes, alpha, ramp colours, seamless grounds, complete and joining overlays, 4-frame water.
const DIR = new URL('../../src/art-release-v2/terrain/', import.meta.url);
const V1 = new URL('../../src/art-release/terrain/', import.meta.url);
const DOCS = new URL('../../docs/art-release-v2/terrain/', import.meta.url);
const RAMPS = JSON.parse(readFileSync(new URL('ramps.json', DOCS), 'utf8'));
const MANIFEST = JSON.parse(readFileSync(new URL('manifest.json', DOCS), 'utf8'));

const range = (n) => [...Array(n).keys()];
const PREFIX = { grass: 'tile.grass', plains: 'plains.grass', lake: 'lake.grass', moss: 'forest.grass', snow: 'mountains.snow', sand: 'tile.sand', dsand: 'desert.sand', path: 'tile.path', ruin: 'tile.ruin' };
const SINGLE = ['sand', 'path', 'ruin'];
const SEASONAL = ['grass', 'plains', 'lake', 'moss'];
const MASKS = range(14).map((i) => i + 1);
/** [ground, season prefix] for every set */
const SETS = [...Object.keys(PREFIX).map((g) => [g, '']), ...['autumn.', 'winter.'].flatMap((s) => SEASONAL.map((g) => [g, s]))];
const base = (g, s) => `${s}${PREFIX[g]}${SINGLE.includes(g) ? '' : '.0'}`;
const tiles = (g, s) => [base(g, s), ...[1, 2, 3].map((n) => `${s}${PREFIX[g]}.${n}`), ...range(4).map((q) => `${s}${PREFIX[g]}.macro.${q}`)];
const edges = (g, s) => MASKS.flatMap((m) => [0, 1].map((v) => `${s}${PREFIX[g]}.edge.${m}.${v}`));
const GROUND_KEYS = SETS.flatMap(([g, s]) => tiles(g, s));
const OVERLAY_KEYS = SETS.flatMap(([g, s]) => edges(g, s));
const WATER_TILES = ['tile.water', 'tile.water.v1', 'tile.water.deep', 'tile.water.deep.v1'].flatMap((p) => range(4).map((f) => `${p}.${f}`));
const WATER_OVERLAYS = ['tile.water.deep.edge', 'tile.water.foam'].flatMap((p) => MASKS.flatMap((m) => range(4).map((f) => `${p}.${m}.${f}`)));
const DRAWN = [...GROUND_KEYS, ...OVERLAY_KEYS, ...WATER_TILES, ...WATER_OVERLAYS];
const v1Keys = readdirSync(V1).filter((f) => f.endsWith('.png')).map((f) => f.slice(0, -4));

/** Decodes an 8-bit RGBA, non-interlaced PNG (what Pillow writes). */
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
  const stride = w * 4;
  const out = Buffer.alloc(h * stride);
  for (let y = 0; y < h; y++) {
    const f = raw[y * (stride + 1)];
    for (let i = 0; i < stride; i++) {
      const x = raw[y * (stride + 1) + 1 + i];
      const a = i >= 4 ? out[y * stride + i - 4] : 0;
      const b = y > 0 ? out[(y - 1) * stride + i] : 0;
      const c = i >= 4 && y > 0 ? out[(y - 1) * stride + i - 4] : 0;
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
const cache = new Map();
const png = (n) => {
  if (!cache.has(n)) cache.set(n, readPng(n));
  return cache.get(n);
};
const hex = ([r, g, b]) => `#${[r, g, b].map((v) => v.toString(16).padStart(2, '0')).join('')}`;

describe('ground v2 art', { timeout: 60000 }, () => {  // ~800 PNGs decoded: slow when the whole suite runs in parallel
  const files = readdirSync(DIR).filter((f) => f.endsWith('.png')).map((f) => f.slice(0, -4));

  it('holds every v1 terrain key (v2 replaces the v1 group), plus exactly the drawn keys of the scheme', () => {
    expect(new Set(DRAWN).size).toBe(DRAWN.length);
    for (const k of v1Keys) expect(files, k).toContain(k);
    expect(files.sort()).toEqual([...new Set([...DRAWN, ...v1Keys])].sort());
    expect([...MANIFEST.redrawn, ...MANIFEST.new].sort()).toEqual([...DRAWN].sort());
    expect([...MANIFEST.copied_from_v1].sort()).toEqual(v1Keys.filter((k) => !DRAWN.includes(k)).sort());
  });

  it('the keys not redrawn this round are the v1 files, byte for byte', () => {
    for (const k of MANIFEST.copied_from_v1) expect(readFileSync(new URL(`${k}.png`, DIR)).equals(readFileSync(new URL(`${k}.png`, V1))), k).toBe(true);
  });

  it('every drawn PNG is 32×32 RGBA, alpha 0 / 255 only, colours only from the registered ramps', () => {
    const allowed = new Set(Object.values(RAMPS.ramps).flat());
    for (const n of DRAWN) {
      const { w, h, depth, type, interlace, px } = png(n);
      expect([w, h, depth, type, interlace], n).toEqual([32, 32, 8, 6, 0]);
      for (let y = 0; y < 32; y++) {
        for (let x = 0; x < 32; x++) {
          const p = px(x, y);
          expect([0, 255], `${n} ${x},${y}`).toContain(p[3]);
          if (p[3] === 255 && !allowed.has(hex(p))) expect(hex(p), `${n} ${x},${y}`).toBe('a ramp colour');
        }
      }
    }
  });

  it('ground tiles and water tiles are fully opaque', () => {
    for (const n of [...GROUND_KEYS, ...WATER_TILES]) {
      const { px } = png(n);
      let holes = 0;
      for (let y = 0; y < 32; y++) for (let x = 0; x < 32; x++) if (px(x, y)[3] !== 255) holes++;
      expect(holes, n).toBe(0);
    }
  });

  it("every variant and macro piece shares the ground's 2-px edge band (they join in any order)", () => {
    const band = (t, side) => {
      const pts = [];
      for (let k = 0; k < 32; k++) {
        for (const d of [0, 1]) {
          if (side === 'top') pts.push(t.px(k, d).join());
          if (side === 'bottom') pts.push(t.px(k, 31 - d).join());
          if (side === 'left') pts.push(t.px(d, k).join());
          if (side === 'right') pts.push(t.px(31 - d, k).join());
        }
      }
      return pts.join('|');
    };
    const outer = [['top', 'left'], ['top', 'right'], ['bottom', 'left'], ['bottom', 'right']];
    for (const [g, s] of SETS) {
      const [b, ...rest] = tiles(g, s);
      const ref = png(b);
      rest.forEach((k, i) => {
        const sides = i < 3 ? ['top', 'bottom', 'left', 'right'] : outer[i - 3];
        for (const side of sides) expect(band(png(k), side), `${k} ${side}`).toBe(band(ref, side));
      });
    }
  });

  it('transition overlays: every mask 1-14 in both variants for every set; corners follow the mask', () => {
    const corner = { 1: [1, 1], 2: [30, 1], 4: [1, 30], 8: [30, 30] };
    const sets = [...SETS.map(([g, s]) => [`${s}${PREFIX[g]}.edge`, [0, 1]]), ['tile.water.deep.edge', range(4)], ['tile.water.foam', range(4)]];
    for (const [p, vs] of sets) {
      for (const m of MASKS) {
        for (const v of vs) {
          const t = png(`${p}.${m}.${v}`);
          for (const [bit, [x, y]] of Object.entries(corner)) {
            const opaque = t.px(x, y)[3] === 255;
            if (p.endsWith('foam')) {
              if (m & Number(bit)) expect(opaque, `${p}.${m}.${v} land corner ${bit}`).toBe(false);
            } else expect(opaque, `${p}.${m}.${v} corner ${bit}`).toBe(Boolean(m & Number(bit)));
          }
        }
      }
    }
  });

  it('transition overlays join their neighbours on the dual grid (shared corners -> the same border)', () => {
    const op = (t, x, y) => t.px(x, y)[3] === 255;
    for (const p of ['tile.grass', 'tile.sand', 'mountains.snow', 'winter.plains.grass']) {
      for (const a of MASKS) {
        for (const b of MASKS) {
          const A = png(`${p}.edge.${a}.0`);
          const B = png(`${p}.edge.${b}.1`);
          if (Boolean(a & 2) === Boolean(b & 1) && Boolean(a & 8) === Boolean(b & 4)) {
            const miss = range(32).filter((y) => op(A, 31, y) !== op(B, 0, y)).length;
            expect(miss, `${p} ${a}|${b}`).toBeLessThanOrEqual(3);
          }
          if (Boolean(a & 4) === Boolean(b & 1) && Boolean(a & 8) === Boolean(b & 2)) {
            const miss = range(32).filter((x) => op(A, x, 31) !== op(B, x, 0)).length;
            expect(miss, `${p} ${a}/${b}`).toBeLessThanOrEqual(3);
          }
        }
      }
    }
  });

  it('water: 4 frames; each water tile changes by 12-30 px from frame to frame (guide 3.5)', () => {
    for (const p of ['tile.water', 'tile.water.v1', 'tile.water.deep', 'tile.water.deep.v1']) {
      for (const f of range(4)) {
        const a = png(`${p}.${f}`);
        const b = png(`${p}.${(f + 1) % 4}`);
        let n = 0;
        for (let y = 0; y < 32; y++) for (let x = 0; x < 32; x++) if (a.px(x, y).join() !== b.px(x, y).join()) n++;
        expect(n, `${p} ${f}->${(f + 1) % 4}`).toBeGreaterThanOrEqual(12);
        expect(n, `${p} ${f}->${(f + 1) % 4}`).toBeLessThanOrEqual(30);
      }
    }
  });

  it('the green ground cores keep the hero-cloak rule (lightness at least 12 below the cloak)', () => {
    const L = (c) => {
      const [r, g, b] = [1, 3, 5].map((i) => parseInt(c.slice(i, i + 2), 16));
      return (0.299 * r + 0.587 * g + 0.114 * b) / 2.55;
    };
    for (const g of ['grass', 'plains', 'lake', 'moss']) expect(49 - L(RAMPS.ramps[g][3]), g).toBeGreaterThanOrEqual(12);
  });
});
