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
      expect(atlasSizeFor(entries).width).toBeLessThanOrEqual(512);
    }
  });
});

describe('atlasSizeFor: power-of-two width and height (perf v1)', async () => {
  const { atlasSizeFor } = await import('../../src/view/assets/placeholderPack.js');
  /** @param {number} w @param {number} h */
  const img = (w, h) => ({ rows: ['.'], image: { width: w, height: h } });

  it('a wide, short set gets a wide, short atlas (2048×1024, not 2048×2048)', () => {
    // 676 frames of 48×56 in a 2048 wide atlas: 41 a row, 17 rows of 57 px = 968 px used.
    expect(atlasSizeFor(Array.from({ length: 676 }, () => img(48, 56)))).toEqual({ width: 2048, height: 1024 });
  });

  it('the width is the same as the square choice, so the layout is unchanged', () => {
    // 21 frames of 48×56 do not fit 256×256 (5 a row, 5 rows = 284 px), so the width is 512;
    // at 512 they take 3 rows (170 px), so the height is 256.
    expect(atlasSizeFor(Array.from({ length: 21 }, () => img(48, 56)))).toEqual({ width: 512, height: 256 });
  });

  it('the height is never under 64 nor over the width', () => {
    expect(atlasSizeFor([img(10, 10)])).toEqual({ width: 64, height: 64 });
    expect(atlasSizeFor([])).toEqual({ width: 64, height: 64 });
    expect(atlasSizeFor([img(100, 1000)])).toEqual({ width: 1024, height: 1024 });
  });

  it('a set filling exactly a power of two keeps it; one pixel more doubles it', () => {
    expect(atlasSizeFor([img(1024, 512)])).toEqual({ width: 1024, height: 512 });
    expect(atlasSizeFor([img(1024, 513)])).toEqual({ width: 1024, height: 1024 });
  });

  it('the 2048 limit stays', () => {
    expect(() => atlasSizeFor([img(2049, 10)])).toThrow('Too many sprites for one atlas');
    expect(() => atlasSizeFor(Array.from({ length: 3 }, () => img(2048, 700)))).toThrow('Too many sprites for one atlas');
  });
});

describe('v1.0 enemies: placeholders and release-art slots', async () => {
  const { releaseEnemyEntries, releaseBossEntries, REGION_ENTRIES } = await import('../../src/view/assets/placeholderPack.js');

  it('the slime and the sentinel have placeholder frames .0/.1 at half their release size, feet anchored', () => {
    const byKey = new Map(placeholderEntries().map((e) => [e.key, e]));
    for (const [kind, w, h] of [['slime', 16, 14], ['sentinel', 20, 28]]) {
      for (const f of [0, 1]) {
        const e = byKey.get(`enemy.${kind}.${f}`);
        expect(e, `${kind}.${f}`).toBeTruthy();
        expect([e.rows[0].length, e.rows.length]).toEqual([w, h]);
        expect(e.anchor).toEqual([0.5, 1]);
      }
    }
  });

  it('per-action release frames get a slot only when such art is given: enemies in the base bundle, cores in their region', () => {
    expect(releaseEnemyEntries(new Map())).toEqual([]);
    const art = new Map(
      ['enemy.beast.0', 'enemy.beast.windup.1', 'enemy.slime.idle.0', 'enemy.sentinel.attack.1', 'enemy.boss_root.windup_slam.0', 'enemy.boss_frost.idle2.1', 'enemy.boss_source.idle.0', 'enemy.shot.orb.0', 'hero.idle.down.0'].map((k) => [k, `${k}.png`]),
    );
    expect(releaseEnemyEntries(art).map((e) => e.key)).toEqual(['enemy.beast.windup.1', 'enemy.slime.idle.0', 'enemy.sentinel.attack.1']);
    expect(releaseEnemyEntries(art).every((e) => e.anchor[0] === 0.5 && e.anchor[1] === 1)).toBe(true);
    expect(releaseBossEntries('region:forest', art).map((e) => e.key)).toEqual(['enemy.boss_root.windup_slam.0']);
    expect(releaseBossEntries('region:mountains', art).map((e) => e.key)).toEqual(['enemy.boss_frost.idle2.1']);
    expect(releaseBossEntries('region:plains', art)).toEqual([]);
    // The minimal set (enemy.<kind>.<0|1>) replaces the placeholder frames by name instead.
    expect(REGION_ENTRIES['region:forest']().some((e) => e.key === 'enemy.boss_root.0')).toBe(true);
  });
});

describe('splitForAtlas: at most 2048×1024 per real-art atlas (gfx v2 integration)', async () => {
  const { atlasSizeFor, splitForAtlas } = await import('../../src/view/assets/placeholderPack.js');
  const img = (/** @type {number} */ w, /** @type {number} */ h) => ({ rows: ['.'], image: { width: w, height: h } });
  it('entries that fit stay one atlas, the same as before', () => {
    const fit = Array.from({ length: 676 }, () => img(48, 56));
    expect(splitForAtlas(fit)).toEqual([fit]);
    const small = Array.from({ length: 21 }, () => img(48, 56));
    expect(splitForAtlas(small)).toEqual([small]);
  });
  it('a little over 2048×1024: the first 2048×1024 and a small second atlas, not one 2048×2048', () => {
    const tall = Array.from({ length: 676 }, () => img(48, 56));
    const short = Array.from({ length: 400 }, () => img(32, 16)); // 7 shelves of 17 px: 968 + 119 > 1024
    const all = [...tall, ...short];
    expect(atlasSizeFor(all)).toEqual({ width: 2048, height: 2048 });
    const parts = splitForAtlas(all);
    expect(parts.length).toBe(2);
    expect(parts.flat()).toEqual(all);
    expect(atlasSizeFor(parts[0])).toEqual({ width: 2048, height: 1024 });
    const rest = atlasSizeFor(parts[1]);
    expect(rest.width * rest.height).toBeLessThanOrEqual(2048 * 64);
  });
});
