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
