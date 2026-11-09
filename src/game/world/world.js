// @ts-check
// The world (P8): the first island with the region templates stacked below it, as one map.
// P10.3: a second column of regions to the east, joined to the first by passes.
// Every region keeps its own coordinates in its definition; here they are offset and joined.
// The map arrays for the whole world are small (a few bytes per tile); what is loaded and freed as
// the player moves is the drawing (chunks) and each region's art (asset bundles), see src/view.
import { ISLAND } from './maps/island.js';
import { REGIONS } from './maps/regions.js';

/**
 * @typedef {{ id: string, name: string, tx: number, ty: number, tw: number, th: number, climate: 'temperate' | 'dry' | 'cold', bundle: string | null }} RegionInfo
 */

/** Columns start on chunk boundaries (32 tiles). */
const COLUMN_ALIGN = 32;

/** Width of the outdoor world (the east strip holds the indoor rooms: caves, trials, houses). */
export const OUTDOOR_W = 96;

/**
 * Joins the island and the regions into one map definition (P10.3: in two columns). The island
 * and the regions with `col: 0` are stacked south in the west column, as since P8; the ones with
 * `col: 1` are stacked from the top in the east column. Each column is as wide as the island (its
 * outdoors plus a strip of rooms); the camera shows one column's outdoors at a time. Regions in
 * different columns are joined by passes: warps at the edge of each outdoors.
 * @param {import('./tilemap.js').IslandDef} island @param {any[]} regions
 * @returns {import('./tilemap.js').IslandDef & { regions: RegionInfo[], outdoors: import('./features.js').AreaDef[] }}
 */
export function stitchWorld(island, regions) {
  const iw = island.ground[0].length;
  // A column is a whole number of chunks wide (P8 chunks are 32 tiles): a chunk never holds two
  // columns, so the far column's art is never loaded for nothing. The filler between and below the
  // columns is nothing at all (solid dark): no swimming around the edge of the world (P10.6).
  const colW = Math.ceil(iw / COLUMN_ALIGN) * COLUMN_ALIGN;
  /** @type {string[][]} */
  const cols = [island.ground.map((r) => r + '%'.repeat(colW - iw)), []];
  /** @type {string[][]} */
  const heights = [(island.height ?? island.ground.map((r) => '0'.repeat(r.length))).map((r) => r + '0'.repeat(colW - iw)), []];
  /** @type {any} */
  const def = {
    ...island,
    enemies: [...(island.enemies ?? [])],
    chests: [...(island.chests ?? [])],
    checkpoints: [...(island.checkpoints ?? [])],
    landmarks: [...(island.landmarks ?? [])],
    pickups: [...(island.pickups ?? [])],
    envObjects: [...(island.envObjects ?? [])],
    campfires: [...(island.campfires ?? [])],
    npcs: [...(island.npcs ?? [])],
    warps: [...(island.warps ?? [])],
    areas: [...(island.areas ?? [])],
    bosses: [...(island.bosses ?? [])],
    switches: [...(island.switches ?? [])],
    /** @type {RegionInfo[]} */
    regions: [{ id: 'island', name: 'はじまりの島', tx: 0, ty: 0, tw: OUTDOOR_W, th: island.ground.length, climate: 'temperate', bundle: null }],
  };
  /** @type {Record<string, { ox: number, oy: number }>} */
  const placed = { island: { ox: 0, oy: 0 } };
  for (const r of regions) {
    const col = r.col ?? 0;
    const ox = col * colW;
    const oy = cols[col].length;
    const pad = colW - r.ground[0].length;
    if (pad < 0) throw new Error(`Region ${r.id} is wider than the world`);
    for (const row of r.ground) cols[col].push(row + '%'.repeat(pad));
    for (const row of r.height) heights[col].push(row + '0'.repeat(pad));
    placed[r.id] = { ox, oy };
    const at = (/** @type {any} */ o) => ({ ...o, tx: o.tx + ox, ty: o.ty + oy });
    for (const key of ['enemies', 'chests', 'checkpoints', 'landmarks', 'pickups', 'envObjects', 'campfires', 'npcs', 'areas', 'switches']) {
      for (const o of r[key] ?? []) def[key].push(at(o));
    }
    // P10.4: bosses and their arenas.
    for (const b of r.bosses ?? []) def.bosses.push({ ...at(b), arena: at(b.arena) });
    // v1.0 (C7): 淀みの源, the final boss, in its own list (not one of the four cores).
    if (r.finalBoss) {
      const fb = r.finalBoss;
      def.finalBoss = { ...at(fb), arena: at(fb.arena), roam: at(fb.roam), crate: at(fb.crate) };
    }
    // P10.1: house doors lead to rooms in the region's east strip (both ends move with the region).
    for (const w of r.warps ?? []) def.warps.push({ ...w, tx: w.tx + ox, ty: w.ty + oy, toTx: w.toTx + ox, toTy: w.toTy + oy });
    // The region (its climate and art bundle) includes its strip of rooms.
    def.regions.push({ id: r.id, name: r.name, tx: ox, ty: oy, tw: r.ground[0].length, th: r.ground.length, climate: r.climate, bundle: r.bundle });
  }
  // P10.3: passes between the columns (each end is given in its own region's coordinates).
  // v1.0 (C5/C6): the island has one too (the beach ring to the source's antechamber), and a pass
  // may be conditional (`if`: flags, see features.js warpOpen).
  delete def.passes;
  for (const r of [...regions, { id: 'island', passes: island.passes }]) {
    for (const p of r.passes ?? []) {
      const from = placed[r.id];
      const to = placed[p.to.region];
      if (!to) throw new Error(`Pass ${p.id}: unknown region ${p.to.region}`);
      def.warps.push({ id: p.id, tx: p.tx + from.ox, ty: p.ty + from.oy, facing: p.facing, toTx: p.to.tx + to.ox, toTy: p.to.ty + to.oy, ...(p.if ? { if: p.if } : {}) });
    }
  }
  const twoCols = cols[1].length > 0;
  const height = Math.max(cols[0].length, cols[1].length);
  const colHeights = [cols[0].length, cols[1].length];
  for (const rows of cols) while (rows.length < height) rows.push('%'.repeat(colW));
  for (const rows of heights) while (rows.length < height) rows.push('0'.repeat(colW));
  def.ground = cols[0].map((row, y) => (twoCols ? row + cols[1][y] : row));
  def.height = heights[0].map((row, y) => (twoCols ? row + heights[1][y] : row));
  // Camera bounds outside every room: one column's outdoors at a time.
  def.outdoors = [{ id: 'outdoor', tx: 0, ty: 0, tw: OUTDOOR_W, th: colHeights[0] }];
  if (twoCols) def.outdoors.push({ id: 'outdoor-east', tx: colW, ty: 0, tw: OUTDOOR_W, th: colHeights[1] });
  def.outdoor = def.outdoors[0];
  return def;
}

/** The outdoors (camera bounds) containing a point in tiles, if any. @param {any[]} outdoors @param {number} tx @param {number} ty */
export function outdoorAt(outdoors, tx, ty) {
  return outdoors.find((o) => tx >= o.tx && tx < o.tx + o.tw && ty >= o.ty && ty < o.ty + o.th) ?? null;
}

export const WORLD = stitchWorld(ISLAND, REGIONS);

/** The region containing a tile row / column, or null (sea between, east strip). @param {RegionInfo[]} regions @param {number} tx @param {number} ty */
export function regionAt(regions, tx, ty) {
  return regions.find((r) => tx >= r.tx && tx < r.tx + r.tw && ty >= r.ty && ty < r.ty + r.th) ?? null;
}
