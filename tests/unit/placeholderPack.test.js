import { describe, it, expect, vi } from 'vitest';

vi.mock('pixi.js', () => ({ Rectangle: class {}, Texture: class {} }));
const { placeholderEntries } = await import('../../src/view/assets/placeholderPack.js');
const { PALETTE } = await import('../../src/view/assets/placeholderArt.js');

describe('placeholder pack', () => {
  const entries = placeholderEntries();

  it('every sprite is rectangular and uses palette colors only', () => {
    for (const e of entries) {
      const w = e.rows[0].length;
      for (const r of e.rows) {
        expect(r.length, e.key).toBe(w);
        for (const c of r) expect(c === '.' || c in PALETTE, `${e.key} "${c}"`).toBe(true);
      }
    }
  });

  it('keys are unique', () => {
    const keys = entries.map((e) => e.key);
    expect(new Set(keys).size).toBe(keys.length);
  });

  it('everything fits the 256x256 atlas with the same shelf packing as the build', () => {
    let x = 0;
    let y = 0;
    let shelf = 0;
    for (const e of entries) {
      const w = e.rows[0].length;
      const h = e.rows.length;
      if (x + w > 256) {
        x = 0;
        y += shelf + 1;
        shelf = 0;
      }
      expect(y + h, e.key).toBeLessThanOrEqual(256);
      x += w + 1;
      shelf = Math.max(shelf, h);
    }
  });
});

describe('region bundles (P8, P9)', async () => {
  const { REGION_ENTRIES, atlasSizeFor } = await import('../../src/view/assets/placeholderPack.js');
  it('every region bundle is valid and fits an atlas', () => {
    for (const [name, make] of Object.entries(REGION_ENTRIES)) {
      const entries = make();
      for (const e of entries) for (const r of e.rows) expect(r.length, `${name} ${e.key}`).toBe(e.rows[0].length);
      for (const e of entries) for (const r of e.rows) for (const c of r) expect(c === '.' || c in PALETTE, `${name} ${e.key} "${c}"`).toBe(true);
      expect(atlasSizeFor(entries)).toBeLessThanOrEqual(512);
    }
  });
});
