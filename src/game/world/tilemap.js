// @ts-check
// Flat tile map for P1. Elevation is added in P2 (DESIGN.md 3).

export const TILE_SIZE = 16;

/** Ground tile ids (what is drawn underneath). */
export const Ground = Object.freeze({ GRASS: 0, PATH: 1, WATER: 2 });

/**
 * @typedef {{ type: 'tree' | 'rock', tx: number, ty: number }} MapObject
 * @typedef {object} TileMap
 * @property {number} width   in tiles
 * @property {number} height  in tiles
 * @property {number} tileSize
 * @property {Uint8Array} ground
 * @property {Uint8Array} solid   1 = blocks movement
 * @property {MapObject[]} objects
 * @property {{ x: number, y: number }} spawn  feet position in pixels
 */

/**
 * Parses an ASCII map (see maps/testField.js for the legend).
 * @param {string[]} rows
 * @returns {TileMap}
 */
export function parseMap(rows) {
  const height = rows.length;
  const width = rows[0]?.length ?? 0;
  if (!width || rows.some((r) => r.length !== width)) throw new Error('Map rows must be non-empty and equal length');
  const ground = new Uint8Array(width * height);
  const solid = new Uint8Array(width * height);
  /** @type {MapObject[]} */
  const objects = [];
  let spawn = { x: (width * TILE_SIZE) / 2, y: (height * TILE_SIZE) / 2 };

  for (let ty = 0; ty < height; ty++) {
    for (let tx = 0; tx < width; tx++) {
      const i = ty * width + tx;
      const c = rows[ty][tx];
      switch (c) {
        case '.':
          ground[i] = Ground.GRASS;
          break;
        case '=':
          ground[i] = Ground.PATH;
          break;
        case '~':
          ground[i] = Ground.WATER;
          solid[i] = 1;
          break;
        case 'T':
          ground[i] = Ground.GRASS;
          solid[i] = 1;
          objects.push({ type: 'tree', tx, ty });
          break;
        case '#':
          ground[i] = Ground.GRASS;
          solid[i] = 1;
          objects.push({ type: 'rock', tx, ty });
          break;
        case 'P':
          ground[i] = Ground.PATH;
          spawn = { x: tx * TILE_SIZE + TILE_SIZE / 2, y: ty * TILE_SIZE + TILE_SIZE - 2 };
          break;
        default:
          throw new Error(`Unknown map character "${c}" at ${tx},${ty}`);
      }
    }
  }
  return { width, height, tileSize: TILE_SIZE, ground, solid, objects, spawn };
}

/**
 * Outside the map counts as solid so nothing can leave it.
 * @param {TileMap} map @param {number} tx @param {number} ty
 */
export function isSolidTile(map, tx, ty) {
  if (tx < 0 || ty < 0 || tx >= map.width || ty >= map.height) return true;
  return map.solid[ty * map.width + tx] === 1;
}
