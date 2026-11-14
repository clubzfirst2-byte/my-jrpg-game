// @ts-check
// The world (P8): the first island with the region templates stacked below it, as one map.
// P10.3: a second column of regions to the east, joined to the first by passes.
// Every region keeps its own coordinates in its definition; here they are offset and joined.
// The map arrays for the whole world are small (a few bytes per tile); what is loaded and freed as
// the player moves is the drawing (chunks) and each region's art (asset bundles), see src/view.
import { ISLAND } from './maps/island.js';
import { REGIONS } from './maps/regions.js';

/**
 * @typedef {{ id: string, name: string, tx: number, ty: number, tw: number, th: number, climate: 'temperate' | 'dry' | 'cold', bundle: string | null, art?: string, parent?: string }} RegionInfo
 */

/** Columns start on chunk boundaries (32 tiles). */
const COLUMN_ALIGN = 32;

/** Width of the outdoor world (the east strip holds the indoor rooms: caves, trials, houses). */
export const OUTDOOR_W = 96;

/**
 * Joins the island and the regions into one map definition (P10.3: in columns). The island
 * and the regions with `col: 0` are stacked south in the west column, as since P8; the ones with
 * `col: 1` (2, 3, ...) are stacked from the top in the columns to the east. Each column is as wide as the island (its
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
  // Volume phase 1: any number of columns (a region's `col`, 0 = the island's). A new column only
  // ever adds tiles to the east of the ones before it, so nothing already placed moves.
  const colCount = regions.reduce((n, r) => Math.max(n, (r.col ?? 0) + 1), 1);
  for (const r of regions) if (!Number.isInteger(r.col ?? 0) || (r.col ?? 0) < 0) throw new Error(`Region ${r.id}: bad column ${r.col}`);
  /** @type {string[][]} */
  const cols = Array.from({ length: colCount }, () => []);
  /** @type {string[][]} */
  const heights = Array.from({ length: colCount }, () => []);
  cols[0] = island.ground.map((r) => r + '%'.repeat(colW - iw));
  heights[0] = (island.height ?? island.ground.map((r) => '0'.repeat(r.length))).map((r) => r + '0'.repeat(colW - iw));
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
    winds: [...(island.winds ?? [])],
    updrafts: [...(island.updrafts ?? [])],
    surveys: [...(island.surveys ?? [])],
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
    for (const key of ['enemies', 'chests', 'checkpoints', 'landmarks', 'pickups', 'envObjects', 'campfires', 'npcs', 'areas', 'switches', 'winds', 'updrafts', 'surveys']) {
      for (const o of r[key] ?? []) def[key].push(at(o));
    }
    // P10.4: bosses and their arenas.
    for (const b of r.bosses ?? []) def.bosses.push({ ...at(b), arena: at(b.arena) });
    // v1.0 (C7): 淀みの源, the final boss, in its own list (not one of the four cores).
    if (r.finalBoss) {
      const fb = r.finalBoss;
      def.finalBoss = { ...at(fb), arena: at(fb.arena), roam: at(fb.roam), crate: at(fb.crate), grass: (fb.grass ?? []).map(at) };
    }
    // P10.1: house doors lead to rooms in the region's east strip (both ends move with the region).
    for (const w of r.warps ?? []) def.warps.push({ ...w, tx: w.tx + ox, ty: w.ty + oy, toTx: w.toTx + ox, toTy: w.toTy + oy });
    // The region (its climate and art bundle) includes its strip of rooms.
    // Volume phase 1: an 奥地 (`parent`) is dressed in its parent region's art (`art`) until its own is drawn.
    def.regions.push({ id: r.id, name: r.name, tx: ox, ty: oy, tw: r.ground[0].length, th: r.ground.length, climate: r.climate, bundle: r.bundle, ...(r.art ? { art: r.art } : {}), ...(r.parent ? { parent: r.parent } : {}) });
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
  const colHeights = cols.map((rows) => rows.length);
  const height = Math.max(...colHeights);
  for (const rows of cols) while (rows.length < height) rows.push('%'.repeat(colW));
  for (const rows of heights) while (rows.length < height) rows.push('0'.repeat(colW));
  def.ground = cols[0].map((_, y) => cols.map((rows) => rows[y]).join(''));
  def.height = heights[0].map((_, y) => heights.map((rows) => rows[y]).join(''));
  // Camera bounds outside every room: one column's outdoors at a time. (An empty column has none.)
  // Volume phase 1: a region may keep the camera off its west edge (`westMargin`, tiles: the widest
  // of its column counts). The view builds chunks 4 tiles beyond the screen (chunkRange.js), and the
  // chunk west of a column holds the strip of rooms of the column before it: with a margin of 5 the
  // art of that other region is never loaded just for standing at the edge.
  def.outdoors = [];
  colHeights.forEach((th, col) => {
    const margin = regions.reduce((m, r) => ((r.col ?? 0) === col ? Math.max(m, r.westMargin ?? 0) : m), 0);
    if (th > 0) def.outdoors.push({ id: outdoorId(col), tx: col * colW + margin, ty: 0, tw: OUTDOOR_W - margin, th });
  });
  def.outdoor = def.outdoors[0];
  return def;
}

/** The id of a column's outdoors: the first two keep the names they always had. @param {number} col */
export const outdoorId = (col) => (col === 0 ? 'outdoor' : col === 1 ? 'outdoor-east' : `outdoor-col${col}`);

/** The outdoors (camera bounds) containing a point in tiles, if any. @param {any[]} outdoors @param {number} tx @param {number} ty */
export function outdoorAt(outdoors, tx, ty) {
  return outdoors.find((o) => tx >= o.tx && tx < o.tx + o.tw && ty >= o.ty && ty < o.ty + o.th) ?? null;
}

export const WORLD = stitchWorld(ISLAND, REGIONS);

/** The region containing a tile row / column, or null (sea between, east strip). @param {RegionInfo[]} regions @param {number} tx @param {number} ty */
export function regionAt(regions, tx, ty) {
  return regions.find((r) => tx >= r.tx && tx < r.tx + r.tw && ty >= r.ty && ty < r.ty + r.th) ?? null;
}
