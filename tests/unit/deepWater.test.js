import { describe, it, expect } from 'vitest';
import { createGameState, MAPS } from '../../src/game/state.js';
import { deepMapShaped } from '../../src/view/groundV2.js';
import { hash } from '../../src/view/tileHash.js';
import { Ground } from '../../src/game/world/tilemap.js';
import { deepMapOf } from '../../src/view/deepWorker.js';

// gfx v2 integration (start-up): the deep-water map worked out by the worker is the one the view works
// out itself (gameView.deepAt) on the game's own map.
describe('deep-water map off the main thread (deepWorker.js)', () => {
  it('the same array as the view computes from the game state, for the world map', () => {
    const map = createGameState(MAPS.world).map;
    const own = deepMapShaped(map.width, map.height, (x, y) => map.ground[y * map.width + x] === Ground.WATER, hash);
    const def = /** @type {any} */ (MAPS.world);
    const fromWorker = deepMapOf(Array.isArray(def) ? { ground: def } : { ground: def.ground, height: def.height });
    expect(fromWorker.length).toBe(own.length);
    expect(Buffer.from(fromWorker).equals(Buffer.from(own))).toBe(true);
    expect(own.some((v) => v === 1)).toBe(true);
  });
});
