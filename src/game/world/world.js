// @ts-check
// The world (P8): the first island with the region templates stacked below it, as one map.
// Every region keeps its own coordinates in its definition; here they are offset and joined.
// The map arrays for the whole world are small (a few bytes per tile); what is loaded and freed as
// the player moves is the drawing (chunks) and each region's art (asset bundles), see src/view.
import { ISLAND } from './maps/island.js';
import { REGIONS } from './maps/regions.js';

/**
 * @typedef {{ id: string, name: string, tx: number, ty: number, tw: number, th: number, climate: 'temperate' | 'dry', bundle: string | null }} RegionInfo
 */

/** Width of the outdoor world (the island's east strip holds the indoor rooms). */
export const OUTDOOR_W = 96;

/**
 * Joins the island and the regions (stacked south) into one map definition.
 * @param {import('./tilemap.js').IslandDef} island @param {any[]} regions
 * @returns {import('./tilemap.js').IslandDef & { regions: RegionInfo[] }}
 */
export function stitchWorld(island, regions) {
  const width = island.ground[0].length;
  const ground = [...island.ground];
  const height = [...(island.height ?? island.ground.map((r) => '0'.repeat(r.length)))];
  /** @type {any} */
  const def = {
    ...island,
    ground,
    height,
    enemies: [...(island.enemies ?? [])],
    chests: [...(island.chests ?? [])],
    checkpoints: [...(island.checkpoints ?? [])],
    landmarks: [...(island.landmarks ?? [])],
    pickups: [...(island.pickups ?? [])],
    envObjects: [...(island.envObjects ?? [])],
    campfires: [...(island.campfires ?? [])],
    /** @type {RegionInfo[]} */
    regions: [{ id: 'island', name: 'はじまりの島', tx: 0, ty: 0, tw: OUTDOOR_W, th: island.ground.length, climate: 'temperate', bundle: null }],
  };
  for (const r of regions) {
    const oy = ground.length;
    const pad = width - r.ground[0].length;
    if (pad < 0) throw new Error(`Region ${r.id} is wider than the world`);
    for (const row of r.ground) ground.push(row + '~'.repeat(pad));
    for (const row of r.height) height.push(row + '0'.repeat(pad));
    const at = (/** @type {any} */ o) => ({ ...o, ty: o.ty + oy });
    for (const key of ['enemies', 'chests', 'checkpoints', 'landmarks', 'pickups', 'envObjects', 'campfires']) {
      for (const o of r[key] ?? []) def[key].push(at(o));
    }
    def.regions.push({ id: r.id, name: r.name, tx: 0, ty: oy, tw: r.ground[0].length, th: r.ground.length, climate: r.climate, bundle: r.bundle });
  }
  def.outdoor = { id: 'outdoor', tx: 0, ty: 0, tw: OUTDOOR_W, th: ground.length };
  return def;
}

export const WORLD = stitchWorld(ISLAND, REGIONS);

/** The region containing a tile row / column, or null (sea between, east strip). @param {RegionInfo[]} regions @param {number} tx @param {number} ty */
export function regionAt(regions, tx, ty) {
  return regions.find((r) => tx >= r.tx && tx < r.tx + r.tw && ty >= r.ty && ty < r.ty + r.th) ?? null;
}
