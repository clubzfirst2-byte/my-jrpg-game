// @ts-check
// Which chunks the view builds and which it keeps (P8, gameView.updateChunks). Pure: unit-tested.

/** Chunks are built this many tiles beyond the screen (raised ground draws up to 4 tiles higher). */
export const CHUNK_LOAD_MARGIN_TILES = 4;
/**
 * ...and freed only once this many tiles beyond it (hysteresis: 8 tiles of walking back and forth
 * before a chunk is rebuilt). v1.0 perf review of the terrain cache: 12 instead of a whole chunk
 * (32): the release terrain's chunk caches are 4 MB each, and a 32-tile margin kept a 3 × 3 block
 * at a corner (worst case 48 → 35 MB of textures, no more rebuilds while walking about).
 */
export const CHUNK_KEEP_MARGIN_TILES = 12;

/**
 * The chunk index range (inclusive) covering the view plus a margin.
 * @param {{ x: number, y: number }} origin view's top-left, world px
 * @param {number} viewW @param {number} viewH view size, world px
 * @param {number} margin world px
 * @param {{ chunkPx: number, ncx: number, ncy: number, all?: boolean }} grid chunk size in px, chunk counts; all = every chunk
 */
export function chunkRange(origin, viewW, viewH, margin, { chunkPx, ncx, ncy, all = false }) {
  if (all) return { x0: 0, x1: ncx - 1, y0: 0, y1: ncy - 1 };
  return {
    x0: Math.max(0, Math.floor((origin.x - margin) / chunkPx)),
    x1: Math.min(ncx - 1, Math.floor((origin.x + viewW + margin) / chunkPx)),
    y0: Math.max(0, Math.floor((origin.y - margin) / chunkPx)),
    y1: Math.min(ncy - 1, Math.floor((origin.y + viewH + margin + 64) / chunkPx)),
  };
}
