import { describe, it, expect, vi } from 'vitest';
import { readdirSync, readFileSync } from 'node:fs';
import { inflateSync } from 'node:zlib';

// Release art for objects, puzzle parts, icons, effects and UI (src/art-release/objects, tools/object_release).
// Not wired into the game yet: these tests pin the names, sizes and the guide's measurable rules.
vi.mock('pixi.js', () => ({ Rectangle: class {}, Texture: class {} }));
const { REGION_ENTRIES, placeholderEntries } = await import('../../src/view/assets/placeholderPack.js');

const DIR = new URL('../../src/art-release/objects/', import.meta.url);

/** Decodes an 8-bit RGBA PNG (any row filter). */
const read = (name) => {
  const buf = readFileSync(new URL(`${name}.png`, DIR));
  const w = buf.readUInt32BE(16);
  const h = buf.readUInt32BE(20);
  expect([buf[24], buf[25]], name).toEqual([8, 6]);
  const idat = [];
  for (let p = 8; p < buf.length; ) {
    const n = buf.readUInt32BE(p);
    if (buf.toString('ascii', p + 4, p + 8) === 'IDAT') idat.push(buf.subarray(p + 8, p + 8 + n));
    p += 12 + n;
  }
  const raw = inflateSync(Buffer.concat(idat));
  const stride = w * 4;
  const px = Buffer.alloc(stride * h);
  for (let y = 0; y < h; y++) {
    const f = raw[y * (stride + 1)];
    for (let i = 0; i < stride; i++) {
      const x = raw[y * (stride + 1) + 1 + i];
      const a = i >= 4 ? px[y * stride + i - 4] : 0;
      const b = y > 0 ? px[(y - 1) * stride + i] : 0;
      const c = i >= 4 && y > 0 ? px[(y - 1) * stride + i - 4] : 0;
      const pa = Math.abs(b - c);
      const pb = Math.abs(a - c);
      const pc = Math.abs(a + b - 2 * c);
      const pred = [0, a, b, (a + b) >> 1, pa <= pb && pa <= pc ? a : pb <= pc ? b : c][f];
      px[y * stride + i] = (x + pred) & 255;
    }
  }
  return { w, h, alpha: (x, y) => px[y * stride + x * 4 + 3] };
};

const SIZES = {
  // wave 1 (approved samples, finalised)
  'obj.house': [96, 112], 'obj.chest.closed': [32, 28], 'obj.chest.open': [32, 28], 'obj.jar': [20, 24],
  'obj.crate': [32, 32], 'obj.checkpoint.off': [24, 40], 'obj.checkpoint.on': [24, 40], 'obj.campfire.0': [32, 28],
  'obj.campfire.1': [32, 28], 'sw.plate.off': [28, 20], 'sw.plate.on': [28, 20], 'icon.sword': [20, 20],
  'icon.herb': [20, 20], 'icon.meat': [20, 20], 'fx.slash': [32, 40], 'fx.fire.0': [24, 28], 'fx.fire.1': [24, 28],
  // wave 2
  'obj.door': [32, 40], 'obj.cave': [32, 28], 'obj.stairs': [32, 32], 'obj.lowwall': [32, 24], 'obj.bed': [32, 52],
  'obj.table': [32, 28], 'obj.shelf': [32, 40], 'obj.charm_shelf': [32, 40], 'obj.charm_shelf.on': [32, 40],
  'obj.counter': [32, 32], 'obj.stove': [32, 40], 'obj.barrel': [24, 28], 'obj.mat': [32, 16], 'obj.anvil': [32, 24],
  'obj.brazier.0': [24, 32], 'obj.brazier.1': [24, 32], 'obj.crystal': [24, 36], 'obj.receiver.off': [24, 32],
  'obj.receiver.on': [24, 32], 'obj.sconce.off': [20, 36], 'obj.sconce.on': [20, 36], 'obj.stone.off': [24, 32],
  'obj.stone.on': [24, 32], 'obj.pillar': [24, 48], 'obj.altar': [32, 28], 'sw.sensor.off': [24, 28],
  'sw.sensor.on': [24, 28], 'obj.rock': [32, 28], 'obj.bramble': [32, 24], 'obj.stump': [28, 16],
  'obj.cactus': [24, 40], 'fx.glider': [44, 20], 'fx.shadow': [24, 10], 'fx.arrow': [20, 6], 'fx.orb': [12, 12],
  'fx.shield': [16, 18], 'fx.bow': [10, 24], 'fx.smoke': [12, 12], 'fx.light': [16, 16], 'ui.marker': [14, 14],
  ...Object.fromEntries(['bow', 'armor', 'mushroom', 'berry', 'pepper', 'fang', 'shard', 'arrows', 'food'].map((n) => [`icon.${n}`, [20, 20]])),
};
const NAMES = Object.keys(SIZES).sort();
const CENTRE = new Set(['fx.slash', 'fx.shadow', 'fx.arrow', 'fx.orb', 'fx.shield', 'fx.bow', 'fx.smoke', 'fx.light', 'ui.marker']);

describe('release objects (src/art-release/objects)', () => {
  it('holds exactly the expected 66 sprites, every one a real sprite key of the game', () => {
    const files = readdirSync(DIR).sort();
    expect(files).toEqual(NAMES.map((n) => `${n}.png`).sort());
    expect(NAMES).toHaveLength(66);
    const keys = new Set([...placeholderEntries(), ...Object.values(REGION_ENTRIES).flatMap((f) => f())].map((e) => e.key));
    for (const n of NAMES) expect(keys.has(n), n).toBe(true);
  });

  it('has each sprite at its release size (2x the placeholder; the house 96x112)', () => {
    for (const n of NAMES) {
      const { w, h } = read(n);
      expect([w, h], n).toEqual(SIZES[n]);
    }
  });

  it('uses only fully clear or fully opaque pixels (alpha 0 or 255), and is not empty', () => {
    for (const n of NAMES) {
      const { w, h, alpha } = read(n);
      let opaque = 0;
      for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
          const a = alpha(x, y);
          expect(a === 0 || a === 255, `${n} (${x},${y}) alpha ${a}`).toBe(true);
          if (a) opaque++;
        }
      }
      expect(opaque, n).toBeGreaterThan(0);
    }
  });

  it('keeps a clear 1 px margin round every icon', () => {
    for (const n of NAMES.filter((k) => k.startsWith('icon.'))) {
      const { w, h, alpha } = read(n);
      for (let i = 0; i < w; i++) {
        expect(alpha(i, 0) + alpha(i, h - 1), `${n} top/bottom ${i}`).toBe(0);
        expect(alpha(0, i) + alpha(w - 1, i), `${n} left/right ${i}`).toBe(0);
      }
    }
  });

  it('stands every feet-anchored object on its last row (no floating)', () => {
    for (const n of NAMES.filter((k) => !k.startsWith('icon.') && !CENTRE.has(k))) {
      const { w, h, alpha } = read(n);
      let any = 0;
      for (let x = 0; x < w; x++) any += alpha(x, h - 1);
      expect(any, n).toBeGreaterThan(0);
    }
  });

  it('changes state visibly: the two frames of every off/on, open/closed and animated pair differ', () => {
    const pairs = [['obj.chest.closed', 'obj.chest.open'], ['obj.checkpoint.off', 'obj.checkpoint.on'], ['obj.campfire.0', 'obj.campfire.1'],
      ['sw.plate.off', 'sw.plate.on'], ['fx.fire.0', 'fx.fire.1'], ['obj.brazier.0', 'obj.brazier.1'], ['obj.receiver.off', 'obj.receiver.on'],
      ['obj.sconce.off', 'obj.sconce.on'], ['obj.stone.off', 'obj.stone.on'], ['sw.sensor.off', 'sw.sensor.on'], ['obj.charm_shelf', 'obj.charm_shelf.on']];
    for (const [a, b] of pairs) {
      const A = read(a);
      const B = read(b);
      let shape = 0;
      for (let y = 0; y < A.h; y++) for (let x = 0; x < A.w; x++) if ((A.alpha(x, y) > 0) !== (B.alpha(x, y) > 0)) shape++;
      // guide 4.2: the shape changes by 6 px or more (a fire's frames: its flame tips move)
      expect(shape, `${a} -> ${b}`).toBeGreaterThanOrEqual(6);
    }
  });
});
