import { describe, it, expect } from 'vitest';
import { readdirSync, readFileSync } from 'node:fs';
import { createGameState, MAPS } from '../../src/game/state.js';
import { regionAt } from '../../src/game/world/world.js';
import { V3_ENEMY_KINDS, kindsByRegion, v3EnemyBundle, v3EnemyKindOf, v3EnemyUnused } from '../../src/view/assets/enemyV3.js';
import { opaqueBox, atlasSizeFor, releaseEnemyEntries } from '../../src/view/assets/placeholderPack.js';
import { decodePng } from '../../tools/release-art-pack.mjs';

// Graphics v3: the normal enemies at density 4 (ENEMY.md): the same keys as v2 at twice the size, one
// bundle per kind packed without transparent margins, a region loading only the kinds that spawn there.

const dir3 = new URL('../../src/art-release-v3/enemy/', import.meta.url);
const V3 = readdirSync(dir3).filter((f) => f.endsWith('.png')).map((f) => f.slice(0, -4));
const png = (dir, k) => decodePng(readFileSync(new URL(`${k}.png`, dir)));

describe('v3 normal enemies', () => {
  it('140 frames, each the size frames.json gives its action (twice v2: ENEMY.md 1); the ones used are the per-action frames of 4 kinds', () => {
    expect(V3.length).toBe(140);
    const spec = JSON.parse(readFileSync(new URL('frames.json', dir3), 'utf8'));
    expect(spec.density).toBe(4);
    for (const k of V3) {
      const m = /^enemy\.(\w+)\.(\w+)\.(\d+)$/.exec(k);
      if (!m || !spec.kinds[m[1]]) continue;
      const a = png(dir3, k);
      expect([a.width, a.height], k).toEqual(spec.kinds[m[1]].actions[m[2]].size);
      expect(Number(m[3])).toBeLessThan(spec.kinds[m[1]].actions[m[2]].frames);
    }
    const used = V3.filter((k) => !v3EnemyUnused(k));
    expect(used.every((k) => V3_ENEMY_KINDS.includes(v3EnemyKindOf(k)))).toBe(true);
    expect(used.length).toBe(120); // 4 kinds × 30 frames (not the 16 shots, not the 4 minimal frames)
    expect(v3EnemyKindOf('enemy.boss_root.idle.0')).toBe(null);
    expect(releaseEnemyEntries(new Map(V3.map((k) => [k, k]))).some((e) => e.key.startsWith('enemy.shot.'))).toBe(false);
  });
  it('a region\'s kinds: those that spawn in it (the plains: beasts only; the mountains: all 4)', () => {
    const s = createGameState(MAPS.world);
    const by = kindsByRegion(s.enemySpawns, (x, y) => regionAt(s.regions, x, y)?.id);
    expect([...by.get('plains')]).toEqual(['beast']);
    expect([...by.get('mountains')].sort()).toEqual(['archer', 'beast', 'sentinel', 'slime']);
    expect(v3EnemyBundle('slime')).toBe('v3:enemy:slime');
  });
  it('packed without transparent margins, every region\'s kinds fit 2.9 MB (the mountains, all 4 kinds, the most)', () => {
    /** @param {string[]} kinds */
    const bytes = (kinds) => {
      let total = 0;
      for (const kind of kinds) {
        const entries = V3.filter((k) => !v3EnemyUnused(k) && v3EnemyKindOf(k) === kind).map((k) => {
          const img = png(dir3, k);
          const t = opaqueBox(img.data, img.width, img.height);
          return { rows: [], trim: t, image: { width: img.width, height: img.height } };
        });
        entries.sort((a, b) => b.trim.h - a.trim.h);
        const { width, height } = atlasSizeFor(entries, { exactHeight: true });
        total += width * height * 4;
      }
      return total;
    };
    expect(bytes(['archer', 'beast', 'sentinel', 'slime'])).toBeLessThanOrEqual(2.9e6);
    expect(bytes(['beast'])).toBeLessThan(0.7e6);
  });
  it('opaqueBox: the box of the opaque pixels, 1×1 when there are none', () => {
    const w = 4;
    const h = 3;
    const px = new Uint8Array(w * h * 4);
    px[(1 * w + 2) * 4 + 3] = 255;
    px[(2 * w + 1) * 4 + 3] = 255;
    expect(opaqueBox(px, w, h)).toEqual({ x: 1, y: 1, w: 2, h: 2 });
    expect(opaqueBox(new Uint8Array(16), 2, 2)).toEqual({ x: 0, y: 0, w: 1, h: 1 });
  });
});
