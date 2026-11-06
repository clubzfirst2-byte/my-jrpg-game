import { describe, it, expect, vi } from 'vitest';
import { readdirSync, readFileSync } from 'node:fs';
import { inflateSync } from 'node:zlib';

// P12: the hero prototype frames (src/art-proto/hero) follow the character standard.
vi.mock('pixi.js', () => ({ Rectangle: class {}, Texture: class {} }));
const { placeholderEntries } = await import('../../src/view/assets/placeholderPack.js');

const DIR = new URL('../../src/art-proto/hero/', import.meta.url);
const files = readdirSync(DIR).filter((f) => f.endsWith('.png'));

/** Width, height and the alpha of every pixel of an 8-bit RGBA PNG (filter type 0 rows). */
function readPng(buf) {
  const w = buf.readUInt32BE(16);
  const h = buf.readUInt32BE(20);
  const chunks = [];
  for (let p = 8; p < buf.length; ) {
    const n = buf.readUInt32BE(p);
    if (buf.toString('ascii', p + 4, p + 8) === 'IDAT') chunks.push(buf.subarray(p + 8, p + 8 + n));
    p += 12 + n;
  }
  const raw = inflateSync(Buffer.concat(chunks));
  const alpha = (x, y) => raw[y * (w * 4 + 1) + 1 + x * 4 + 3];
  return { w, h, alpha };
}

describe('hero prototype frames', () => {
  it('are exactly the hero placeholder names (walk 3 × 4, swim 2 × 4)', () => {
    const hero = placeholderEntries().filter((e) => e.key.startsWith('player.')).map((e) => e.key).sort();
    expect(files.map((f) => f.replace(/\.png$/, '')).sort()).toEqual(hero);
    expect(files).toHaveLength(20);
  });

  it('are 32×56 with a transparent background, the feet on the same line', () => {
    for (const f of files) {
      const { w, h, alpha } = readPng(readFileSync(new URL(f, DIR)));
      expect([w, h], f).toEqual([32, 56]);
      expect(alpha(0, 0), f).toBe(0);
      expect(alpha(31, 0), f).toBe(0);
      if (f.includes('.walk.')) {
        // The boots reach the bottom area (rows 50..55) in every walk frame.
        let lowest = -1;
        for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) if (alpha(x, y)) lowest = y;
        expect(lowest, f).toBeGreaterThanOrEqual(53);
      }
    }
  });
});

describe('hero prototype animation', () => {
  const pixels = (name) => {
    const { w, h, alpha } = readPng(readFileSync(new URL(`${name}.png`, DIR)));
    const raw = readFileSync(new URL(`${name}.png`, DIR));
    return { w, h, alpha, raw };
  };
  it('every walk and swim frame is a different picture (not a copy of another frame)', () => {
    for (const d of ['down', 'up', 'right', 'left']) {
      const walk = [0, 1, 2].map((i) => pixels(`player.walk.${d}.${i}`).raw.toString('base64'));
      expect(new Set(walk).size, d).toBe(3);
      const swim = [0, 1].map((i) => pixels(`player.swim.${d}.${i}`).raw.toString('base64'));
      expect(new Set(swim).size, d).toBe(2);
    }
  });
  it('the left frames are the right frames mirrored (as the game\'s placeholder)', () => {
    const a = readPng(readFileSync(new URL('player.walk.right.1.png', DIR)));
    const b = readPng(readFileSync(new URL('player.walk.left.1.png', DIR)));
    for (let y = 0; y < 56; y++) for (let x = 0; x < 32; x++) expect(b.alpha(31 - x, y)).toBe(a.alpha(x, y));
  });
});
