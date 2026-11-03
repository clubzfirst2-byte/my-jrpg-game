// @ts-check
// Tile map with terrain elevation (DESIGN.md 3.1, 3.2).
// Terrain height is in pixels; 1 level (段) = LEVEL_PX. Elevation is part of the terrain, separate
// from a character's own z.

export const TILE_SIZE = 16;
/** One elevation level (段) in pixels. */
export const LEVEL_PX = 8;
/** Height values in map files are written in units of 4px. */
export const HEIGHT_UNIT_PX = 4;

/** Ground tile ids (what is drawn underneath, and the cliff material). */
export const Ground = Object.freeze({ GRASS: 0, PATH: 1, WATER: 2, RUIN: 3 });

/** Tile shapes. RAMP_N rises toward the north by exactly 1 level across the tile. */
export const Shape = Object.freeze({ FLAT: 0, RAMP_N: 1 });

const HEIGHT_DIGITS = '0123456789abcdefghijklmnopqrstuv';

/**
 * @typedef {{ type: 'tree' | 'rock', tx: number, ty: number }} MapObject
 * @typedef {object} TileMap
 * @property {number} width   in tiles
 * @property {number} height  in tiles
 * @property {number} tileSize
 * @property {Uint8Array} ground
 * @property {Uint8Array} solid    1 = blocks movement at any height (water, trees, rocks)
 * @property {Uint16Array} elev    terrain height in px (for ramps: the high, north edge)
 * @property {Uint8Array} shape
 * @property {MapObject[]} objects
 * @property {{ x: number, y: number }} spawn  feet position in pixels
 */

/**
 * @typedef {string[] | { ground: string[], height?: string[] }} MapDef
 */

/**
 * Parses an ASCII map. See maps/heightTest.js for the legend.
 * @param {MapDef} def
 * @returns {TileMap}
 */
export function parseMap(def) {
  const rows = Array.isArray(def) ? def : def.ground;
  const heightRows = Array.isArray(def) ? undefined : def.height;
  const height = rows.length;
  const width = rows[0]?.length ?? 0;
  if (!width || rows.some((r) => r.length !== width)) throw new Error('Map rows must be non-empty and equal length');
  if (heightRows && (heightRows.length !== height || heightRows.some((r) => r.length !== width))) {
    throw new Error('Height rows must match the ground rows');
  }
  const n = width * height;
  const ground = new Uint8Array(n);
  const solid = new Uint8Array(n);
  const elev = new Uint16Array(n);
  const shape = new Uint8Array(n);
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
        case 'u':
          ground[i] = Ground.RUIN;
          break;
        case '~':
          ground[i] = Ground.WATER;
          solid[i] = 1; // until swimming (P2.3)
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

  if (heightRows) {
    // First pass: flat heights.
    for (let ty = 0; ty < height; ty++) {
      for (let tx = 0; tx < width; tx++) {
        const c = heightRows[ty][tx];
        if (c === '^') continue;
        const v = HEIGHT_DIGITS.indexOf(c);
        if (v < 0) throw new Error(`Unknown height character "${c}" at ${tx},${ty}`);
        elev[ty * width + tx] = v * HEIGHT_UNIT_PX;
      }
    }
    // Second pass: ramps take their heights from their south (low) and north (high) neighbors.
    for (let ty = 0; ty < height; ty++) {
      for (let tx = 0; tx < width; tx++) {
        if (heightRows[ty][tx] !== '^') continue;
        const i = ty * width + tx;
        if (ty === 0 || ty === height - 1) throw new Error(`Ramp at ${tx},${ty} needs tiles to the north and south`);
        const low = elev[i + width];
        const high = elev[i - width];
        if (high - low !== LEVEL_PX) throw new Error(`Ramp at ${tx},${ty} must rise exactly ${LEVEL_PX}px (got ${low}->${high})`);
        shape[i] = Shape.RAMP_N;
        elev[i] = high;
      }
    }
  }
  return { width, height, tileSize: TILE_SIZE, ground, solid, elev, shape, objects, spawn };
}

/** @param {TileMap} map @param {number} tx @param {number} ty */
export function inBounds(map, tx, ty) {
  return tx >= 0 && ty >= 0 && tx < map.width && ty < map.height;
}

/**
 * Outside the map counts as solid so nothing can leave it.
 * @param {TileMap} map @param {number} tx @param {number} ty
 */
export function isSolidTile(map, tx, ty) {
  if (!inBounds(map, tx, ty)) return true;
  return map.solid[ty * map.width + tx] === 1;
}

/** Height that blocks everything (outside the map). */
export const UNREACHABLE = 1e6;

/**
 * Terrain height in px at a point (ramps interpolate from the north edge to the south edge).
 * @param {TileMap} map @param {number} px @param {number} py
 */
export function terrainHeightAt(map, px, py) {
  const ts = map.tileSize;
  const tx = Math.floor(px / ts);
  const ty = Math.floor(py / ts);
  if (!inBounds(map, tx, ty)) return UNREACHABLE;
  const i = ty * map.width + tx;
  const h = map.elev[i];
  if (map.shape[i] === Shape.RAMP_N) {
    const t = (py - ty * ts) / ts; // 0 at the north edge .. 1 at the south edge
    return h - LEVEL_PX * t;
  }
  return h;
}

/**
 * Height of a tile's south edge (what a cliff face below it starts from).
 * @param {TileMap} map @param {number} tx @param {number} ty
 */
export function southEdgeHeight(map, tx, ty) {
  if (!inBounds(map, tx, ty)) return 0;
  const i = ty * map.width + tx;
  return map.shape[i] === Shape.RAMP_N ? map.elev[i] - LEVEL_PX : map.elev[i];
}

/**
 * Height of a tile's north edge.
 * @param {TileMap} map @param {number} tx @param {number} ty
 */
export function northEdgeHeight(map, tx, ty) {
  if (!inBounds(map, tx, ty)) return 0;
  return map.elev[ty * map.width + tx];
}
