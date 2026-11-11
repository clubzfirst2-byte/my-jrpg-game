import { describe, it, expect } from 'vitest';
import { DECOR_TYPES, MAX_OFFSET, decorOffset, hash01, macroQuarter, patchNoise, patchVariant, placementEnabled, valueNoise } from '../../src/view/placement.js';
import { createGameState, MAPS } from '../../src/game/state.js';
import { objectBaseline, objectId } from '../../src/game/world/worldDiff.js';

// W2: the placement layer (src/view/placement.js) — draw offsets, clusters, ground patches.
const range = (n) => [...Array(n).keys()];
const grid = (w, h) => range(w * h).map((i) => [i % w, Math.floor(i / w)]);

describe('placement layer (W2)', () => {
  it('is deterministic: the same tile always gets the same look', () => {
    for (const [x, y] of [[0, 0], [17, 3], [200, 250]]) {
      expect(decorOffset(x, y)).toEqual(decorOffset(x, y));
      expect(patchVariant(x, y, 4)).toBe(patchVariant(x, y, 4));
      expect(hash01(x, y, 7)).toBe(hash01(x, y, 7));
    }
    expect(valueNoise(3.5, 2.25, 6, 1)).toBeGreaterThanOrEqual(0);
    expect(patchNoise(3.5, 2.25, 6, 1)).toBeLessThan(1);
  });

  it('decorative offsets stay small and never go below the foot line (so sorting by tile still holds)', () => {
    const seen = new Set();
    for (const [x, y] of grid(120, 120)) {
      const [dx, dy] = decorOffset(x, y);
      expect(Number.isInteger(dx) && Number.isInteger(dy)).toBe(true);
      expect(Math.abs(dx)).toBeLessThanOrEqual(MAX_OFFSET.x);
      expect(dy).toBeLessThanOrEqual(0);
      expect(dy).toBeGreaterThanOrEqual(-MAX_OFFSET.up);
      seen.add(`${dx},${dy}`);
    }
    // a real spread, not a fixed nudge
    expect(seen.size).toBeGreaterThan(20);
    expect(DECOR_TYPES).toEqual(['tree', 'rock', 'bramble', 'stump', 'cactus']);
  });

  it('offsets pull neighbours together: on average, adjacent objects lean the same way (clusters)', () => {
    let same = 0;
    let n = 0;
    for (const [x, y] of grid(100, 100)) {
      const [a] = decorOffset(x, y);
      const [b] = decorOffset(x + 1, y);
      if (a !== 0 && b !== 0) {
        n++;
        if (Math.sign(a) === Math.sign(b)) same++;
      }
    }
    expect(same / n).toBeGreaterThan(0.6);
  });

  it('ground variants come in patches: about two thirds plain, the marked ones clumped together', () => {
    for (const n of [3, 4, 8]) {
      const counts = Array(n).fill(0);
      for (const [x, y] of grid(200, 200)) counts[patchVariant(x, y, n)]++;
      const plain = counts[0] / 40000;
      expect(plain).toBeGreaterThan(0.6);
      expect(plain).toBeLessThan(0.9);
      for (let v = 1; v < n; v++) expect(counts[v], `n=${n} variant ${v}`).toBeGreaterThan(0);
    }
    // clumped: a marked tile has more marked neighbours than chance
    let marked = 0;
    let both = 0;
    let all = 0;
    for (const [x, y] of grid(200, 200)) {
      const m = patchVariant(x, y, 4) !== 0;
      if (m) marked++;
      all++;
      if (m && patchVariant(x + 1, y, 4) !== 0) both++;
    }
    expect(both / marked).toBeGreaterThan((marked / all) * 1.5);
    expect(patchVariant(5, 5, 1)).toBe(0);
  });

  it('2×2 macro blocks: the 4 tiles of a chosen block take the 4 quarters, other blocks none', () => {
    let blocks = 0;
    for (const [bx, by] of grid(60, 60)) {
      const qs = [0, 1, 2, 3].map((k) => macroQuarter(bx * 2 + (k % 2), by * 2 + (k >> 1)));
      if (qs[0] < 0) {
        expect(qs).toEqual([-1, -1, -1, -1]);
        continue;
      }
      blocks++;
      expect(qs).toEqual([0, 1, 2, 3]);
    }
    expect(blocks / 3600).toBeGreaterThan(0.02);
    expect(blocks / 3600).toBeLessThan(0.2);
  });

  it('only the drawing moves: the map, its objects and every save key are what they were', () => {
    const a = createGameState(MAPS.world);
    const ids = objectBaseline(a.map.objects).map(objectId);
    // the placement layer is view-only: nothing in the game state depends on it
    const b = createGameState(MAPS.world);
    expect(objectBaseline(b.map.objects).map(objectId)).toEqual(ids);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it('?placement=0 turns it off (comparison)', () => {
    expect(placementEnabled('')).toBe(true);
    expect(placementEnabled('?placement=0')).toBe(false);
    expect(placementEnabled('?map=world&placement=1')).toBe(true);
  });
});
