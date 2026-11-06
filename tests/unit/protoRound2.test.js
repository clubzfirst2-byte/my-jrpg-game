import { describe, it, expect, vi } from 'vitest';
import { readdirSync, readFileSync } from 'node:fs';
import { inflateSync } from 'node:zlib';

// P12 round 2 prototypes: 6 NPCs × 12 frames (src/art-proto/npc), 32×56, 4 directions.
vi.mock('pixi.js', () => ({ Rectangle: class {}, Texture: class {} }));
const { REGION_ENTRIES, newLookEntries } = await import('../../src/view/assets/placeholderPack.js');

const DIR = new URL('../../src/art-proto/npc/', import.meta.url);
const ROUND2 = { 6: '村人', 4: '商人', 7: '鍛冶屋', 5: '子ども', 8: '旅人', 9: '星環の姫' };
const DIRS = ['down', 'up', 'right', 'left'];
const read = (name) => {
  const buf = readFileSync(new URL(`${name}.png`, DIR));
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
const files = readdirSync(DIR).filter((f) => f.endsWith('.png')).map((f) => f.slice(0, -4));

describe('round 2 NPCs', () => {
  it('6 characters × 4 directions × 3 frames = 72 files, nothing else for these looks', () => {
    const mine = files.filter((n) => /^npc\.(4|5|6|7|8|9)\./.test(n));
    expect(mine).toHaveLength(72);
    for (const look of Object.keys(ROUND2)) {
      for (const d of DIRS) for (let f = 0; f < 3; f++) expect(mine, `${ROUND2[look]} ${d} ${f}`).toContain(`npc.${look}.walk.${d}.${f}`);
    }
  });

  it('every frame is 32×56 with a transparent background, feet near the bottom', () => {
    for (const look of Object.keys(ROUND2)) {
      for (const d of DIRS) {
        for (let f = 0; f < 3; f++) {
          const name = `npc.${look}.walk.${d}.${f}`;
          const { w, h, alpha } = read(name);
          expect([w, h], name).toEqual([32, 56]);
          expect(alpha(0, 0), name).toBe(0);
          let lowest = -1;
          for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) if (alpha(x, y)) lowest = y;
          expect(lowest, name).toBeGreaterThanOrEqual(52);
        }
      }
    }
  });

  it('walks: the three frames of each direction differ; left is right mirrored', () => {
    for (const look of Object.keys(ROUND2)) {
      for (const d of DIRS) {
        const fr = [0, 1, 2].map((f) => read(`npc.${look}.walk.${d}.${f}`).raw.toString('base64'));
        expect(new Set(fr).size, `${ROUND2[look]} ${d}`).toBe(3);
      }
      const r = read(`npc.${look}.walk.right.2`);
      const l = read(`npc.${look}.walk.left.2`);
      for (let y = 0; y < 56; y++) for (let x = 0; x < 32; x++) expect(l.alpha(31 - x, y), ROUND2[look]).toBe(r.alpha(x, y));
    }
  });

  it('the characters are not colour swaps: their silhouettes differ', () => {
    const shape = (look) => {
      const { alpha } = read(`npc.${look}.walk.down.0`);
      let s = '';
      for (let y = 0; y < 56; y++) for (let x = 0; x < 32; x++) s += alpha(x, y) ? '1' : '0';
      return s;
    };
    const shapes = Object.keys(ROUND2).map(shape);
    expect(new Set(shapes).size).toBe(6);
  });
});

describe('new looks get a slot only when prototypes are given', () => {
  it('normal play: no extra entries', () => {
    expect(newLookEntries('region:plains', new Map())).toEqual([]);
    expect(newLookEntries('region:plains', undefined)).toEqual([]);
  });
  it('with prototypes: only the looks no placeholder has, only in the plains bundle', () => {
    const over = new Map([
      ['npc.9.walk.down.0', 'a.png'],
      ['npc.4.walk.down.0', 'b.png'],
      ['enemy.beast.0', 'c.png'],
    ]);
    expect(newLookEntries('region:plains', over).map((e) => e.key)).toEqual(['npc.9.walk.down.0']);
    expect(newLookEntries('region:forest', over)).toEqual([]);
    expect(REGION_ENTRIES['region:plains']().some((e) => e.key === 'npc.4.walk.down.0')).toBe(true);
  });
});
