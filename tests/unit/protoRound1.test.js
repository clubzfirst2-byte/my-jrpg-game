import { describe, it, expect, vi } from 'vitest';
import { readdirSync, readFileSync } from 'node:fs';
import { inflateSync } from 'node:zlib';

// P12 round 1 prototypes (src/art-proto/npc, src/art-proto/enemy): names, sizes, motion.
vi.mock('pixi.js', () => ({ Rectangle: class {}, Texture: class {} }));
const { REGION_ENTRIES, placeholderEntries } = await import('../../src/view/assets/placeholderPack.js');

const read = (dir, name) => {
  const buf = readFileSync(new URL(`../../src/art-proto/${dir}/${name}.png`, import.meta.url));
  const w = buf.readUInt32BE(16);
  const h = buf.readUInt32BE(20);
  const idat = [];
  for (let p = 8; p < buf.length; ) {
    const n = buf.readUInt32BE(p);
    if (buf.toString('ascii', p + 4, p + 8) === 'IDAT') idat.push(buf.subarray(p + 8, p + 8 + n));
    p += 12 + n;
  }
  const raw = inflateSync(Buffer.concat(idat));
  return { w, h, raw, alpha: (x, y) => raw[y * (w * 4 + 1) + 1 + x * 4 + 3] };
};
const names = (dir) => readdirSync(new URL(`../../src/art-proto/${dir}/`, import.meta.url)).filter((f) => f.endsWith('.png')).map((f) => f.slice(0, -4));
const keys = [...placeholderEntries(), ...REGION_ENTRIES['region:plains']()].map((e) => e.key);

describe('round 1 NPCs (the elder look 1, the watchman look 3)', () => {
  it('replace exactly their 12 walk frames each, at 32×56', () => {
    const npc = names('npc').sort();
    expect(npc).toEqual(keys.filter((k) => /^npc\.(1|3)\.walk\./.test(k)).sort());
    for (const n of npc) {
      const { w, h, alpha } = read('npc', n);
      expect([w, h], n).toEqual([32, 56]);
      expect(alpha(0, 0), n).toBe(0);
    }
  });
  it('the three walk frames differ, and left is right mirrored', () => {
    for (const look of [1, 3]) {
      for (const d of ['down', 'up', 'right']) {
        const frames = [0, 1, 2].map((f) => read('npc', `npc.${look}.walk.${d}.${f}`).raw.toString('base64'));
        expect(new Set(frames).size, `${look} ${d}`).toBe(3);
      }
      const r = read('npc', `npc.${look}.walk.right.1`);
      const l = read('npc', `npc.${look}.walk.left.1`);
      for (let y = 0; y < 56; y++) for (let x = 0; x < 32; x++) expect(l.alpha(31 - x, y)).toBe(r.alpha(x, y));
    }
  });
});

describe('round 1 enemies (beast, goblin = archer)', () => {
  it('replace their 2 frames, at the planned sizes, and the frames differ', () => {
    expect(names('enemy').sort()).toEqual(['enemy.archer.0', 'enemy.archer.1', 'enemy.beast.0', 'enemy.beast.1']);
    for (const [kind, size] of [['beast', [44, 32]], ['archer', [32, 44]]]) {
      const [a, b] = [0, 1].map((f) => read('enemy', `enemy.${kind}.${f}`));
      expect([a.w, a.h], kind).toEqual(size);
      expect([b.w, b.h], kind).toEqual(size);
      expect(a.raw.equals(b.raw), kind).toBe(false);
      expect(keys).toContain(`enemy.${kind}.0`);
    }
  });
});
