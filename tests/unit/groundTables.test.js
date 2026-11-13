import { describe, it, expect } from 'vitest';
import { createGameState, MAPS } from '../../src/game/state.js';
import { calmNumber, macroPlacement } from '../../src/view/groundV2.js';
import { hash } from '../../src/view/tileHash.js';
import { groundClassOf, macroOf, sandUnderTreesOf, tableIndex, uniformBlockOf } from '../../src/view/groundTables.js';
import { groundDataOf } from '../../src/view/deepWorker.js';

// gfx v2 integration (start-up): the ground tables the worker makes from the map definition hold the
// very values the view works out from the game's own map (calm numbers, picture pieces).
describe('ground tables off the main thread (groundTables.js, deepWorker.js)', () => {
  const def = /** @type {any} */ (MAPS.world);
  const msg = structuredClone(Array.isArray(def) ? { ground: def } : { ground: def.ground, height: def.height, regions: def.regions });
  const { tables } = groundDataOf(msg);
  const state = createGameState(MAPS.world);
  const map = state.map;
  const sand = sandUnderTreesOf(map, state.regions);
  const classAt = (x, y) => groundClassOf(map, state.regions, sand, x, y);
  const ctx = { uniformBlock: (a, b, k) => uniformBlockOf(map, classAt, a, b, k), hash, width: map.width, height: map.height, pictures: new Map() };

  it('covers the display grid of the map (-1 … width-1, -1 … height-1)', () => {
    expect(tables.width).toBe(map.width);
    expect(tables.height).toBe(map.height);
    expect(tableIndex(tables, -1, -1)).toBe(0);
    expect(tableIndex(tables, map.width, 0)).toBe(-1);
  });

  it('the same calm numbers and picture pieces as worked out from the game state, everywhere', () => {
    let pictures = 0;
    const memo = new Map();
    for (let j = -1; j < map.height; j++) {
      for (let i = -1; i < map.width; i++) {
        const k = tableIndex(tables, i, j);
        expect(tables.calm[k]).toBe(calmNumber(i, j, hash, memo));
        const m = macroPlacement(i, j, ctx);
        expect(macroOf(tables, k)).toEqual(m);
        if (m) pictures++;
      }
    }
    expect(pictures).toBeGreaterThan(100);
  });
});
