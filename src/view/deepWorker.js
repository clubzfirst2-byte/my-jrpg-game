// @ts-check
// gfx v2 integration (start-up): the v2 ground's deep-water map (groundV2.deepMapShaped, the whole map,
// about 120 ms at x1 on the first draw) worked out off the main thread, while the title shows and the
// world's art is prepared. The same function, hash and ground as gameView.deepAt: the result is the
// same array (tests/unit/deepWater.test.js); the view falls back to working it out itself.
import { parseMap, Ground } from '../game/world/tilemap.js';
import { deepMapShaped } from './groundV2.js';
import { hash } from './tileHash.js';
import { groundTablesOf } from './groundTables.js';

/** The deep map of a map definition's ground rows. Pure. @param {{ ground: string[], height?: string[] }} def */
export function deepMapOf(def) {
  const map = parseMap(def);
  return deepMapShaped(map.width, map.height, (x, y) => map.ground[y * map.width + x] === Ground.WATER, hash);
}

/** The deep map and the ground tables (groundTables.js) of a map definition. @param {{ ground: string[], height?: string[], regions?: any[] }} def */
export function groundDataOf(def) {
  const map = parseMap(def);
  const deep = deepMapShaped(map.width, map.height, (x, y) => map.ground[y * map.width + x] === Ground.WATER, hash);
  return { deep, tables: groundTablesOf(map, def.regions ?? [], hash) };
}

// (as a worker: one message { ground, height, regions } in, { deep, tables } out, or null)
const scope = /** @type {any} */ (globalThis);
if (typeof scope.WorkerGlobalScope !== 'undefined' && scope instanceof scope.WorkerGlobalScope) {
  scope.onmessage = (/** @type {MessageEvent} */ e) => {
    try {
      const out = groundDataOf(e.data);
      scope.postMessage(out, [out.deep.buffer, out.tables.calm.buffer]);
    } catch {
      scope.postMessage(null);
    }
  };
}
