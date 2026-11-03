// @ts-check
// Axis-separated AABB vs. tile collision with terrain height. The box sits at the entity's feet
// (DESIGN.md 3.1): x = horizontal center, y = bottom edge of the feet, z = altitude in px.
// A tile blocks if it is solid, or if its terrain is higher than `maxHeight` (the highest ground
// the body may move onto: z + step height when walking, z when airborne).
import { isSolidTile, terrainHeightAt } from '../world/tilemap.js';

/**
 * @typedef {object} Body
 * @property {number} x
 * @property {number} y
 * @property {number} halfWidth
 * @property {number} height
 */

const EPS = 1e-4;
const HEIGHT_EPS = 1e-3;
/** Moves are split into sub-steps no longer than this, so fast bodies cannot tunnel through tiles. */
const MAX_SUBSTEP = 4;

/**
 * @param {import('../world/tilemap.js').TileMap} map
 * @param {number} px @param {number} py
 * @param {number} maxHeight
 */
function blockedAt(map, px, py, maxHeight) {
  const ts = map.tileSize;
  if (isSolidTile(map, Math.floor(px / ts), Math.floor(py / ts))) return true;
  return terrainHeightAt(map, px, py) > maxHeight + HEIGHT_EPS;
}

/**
 * Moves a body by (dx, dy), sliding along walls and cliffs.
 * @param {Body} body mutated in place
 * @param {import('../world/tilemap.js').TileMap} map
 * @param {number} dx
 * @param {number} dy
 * @param {number} [maxHeight] highest terrain the body may enter (default: no height limit)
 * @returns {{ hitX: boolean, hitY: boolean }}
 */
export function moveAndCollide(body, map, dx, dy, maxHeight = Infinity) {
  const n = Math.max(1, Math.ceil(Math.max(Math.abs(dx), Math.abs(dy)) / MAX_SUBSTEP));
  let hitX = false;
  let hitY = false;
  for (let i = 0; i < n; i++) {
    if (!hitX) hitX = moveAxisX(body, map, dx / n, maxHeight);
    if (!hitY) hitY = moveAxisY(body, map, dy / n, maxHeight);
  }
  return { hitX, hitY };
}

/** @param {Body} b @param {import('../world/tilemap.js').TileMap} map @param {number} dx @param {number} maxH */
function moveAxisX(b, map, dx, maxH) {
  if (dx === 0) return false;
  const ts = map.tileSize;
  const nx = b.x + dx;
  const edge = dx > 0 ? nx + b.halfWidth - EPS : nx - b.halfWidth;
  const curEdge = dx > 0 ? b.x + b.halfWidth - EPS : b.x - b.halfWidth;
  // Only tiles newly entered can block (never push a body back out of a tile it already overlaps).
  if (Math.floor(edge / ts) === Math.floor(curEdge / ts)) {
    b.x = nx;
    return false;
  }
  // Sample the leading edge at the top and bottom of the box (box height < tile size).
  const ys = [b.y - b.height, b.y - EPS];
  for (const py of ys) {
    if (blockedAt(map, edge, py, maxH)) {
      const tx = Math.floor(edge / ts);
      b.x = dx > 0 ? tx * ts - b.halfWidth : (tx + 1) * ts + b.halfWidth;
      return true;
    }
  }
  b.x = nx;
  return false;
}

/** @param {Body} b @param {import('../world/tilemap.js').TileMap} map @param {number} dy @param {number} maxH */
function moveAxisY(b, map, dy, maxH) {
  if (dy === 0) return false;
  const ts = map.tileSize;
  const ny = b.y + dy;
  const edge = dy > 0 ? ny - EPS : ny - b.height;
  const curEdge = dy > 0 ? b.y - EPS : b.y - b.height;
  if (Math.floor(edge / ts) === Math.floor(curEdge / ts)) {
    b.y = ny;
    return false;
  }
  const xs = [b.x - b.halfWidth, b.x + b.halfWidth - EPS];
  for (const px of xs) {
    if (blockedAt(map, px, edge, maxH)) {
      const ty = Math.floor(edge / ts);
      b.y = dy > 0 ? ty * ts : (ty + 1) * ts + b.height;
      return true;
    }
  }
  b.y = ny;
  return false;
}

/** How far the "standing" points are inset from the box sides (lets toes hang over a ledge a bit). */
const FOOT_INSET = 2;

/**
 * Highest terrain under the body's feet.
 * @param {Body} b @param {import('../world/tilemap.js').TileMap} map
 */
export function groundHeightUnder(b, map) {
  const xl = b.x - b.halfWidth + FOOT_INSET;
  const xr = b.x + b.halfWidth - FOOT_INSET;
  const yt = b.y - b.height + FOOT_INSET;
  const yb = b.y - EPS;
  return Math.max(
    terrainHeightAt(map, xl, yt),
    terrainHeightAt(map, xr, yt),
    terrainHeightAt(map, xl, yb),
    terrainHeightAt(map, xr, yb),
  );
}

/**
 * True if the body currently overlaps any solid tile (used by tests and sanity checks).
 * @param {Body} b @param {import('../world/tilemap.js').TileMap} map
 */
export function overlapsSolid(b, map) {
  const ts = map.tileSize;
  const left = Math.floor((b.x - b.halfWidth) / ts);
  const right = Math.floor((b.x + b.halfWidth - EPS) / ts);
  const top = Math.floor((b.y - b.height) / ts);
  const bottom = Math.floor((b.y - EPS) / ts);
  for (let ty = top; ty <= bottom; ty++) {
    for (let tx = left; tx <= right; tx++) if (isSolidTile(map, tx, ty)) return true;
  }
  return false;
}
