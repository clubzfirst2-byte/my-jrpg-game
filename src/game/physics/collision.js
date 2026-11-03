// @ts-check
// Axis-separated AABB vs. tile collision. The box sits at the entity's feet (DESIGN.md 3.1):
// x = horizontal center, y = bottom edge of the feet.
import { isSolidTile } from '../world/tilemap.js';

/**
 * @typedef {object} Body
 * @property {number} x
 * @property {number} y
 * @property {number} halfWidth
 * @property {number} height
 */

const EPS = 1e-4;
/** Moves are split into sub-steps no longer than this, so fast bodies cannot tunnel through tiles. */
const MAX_SUBSTEP = 4;

/**
 * Moves a body by (dx, dy), sliding along walls.
 * @param {Body} body mutated in place
 * @param {import('../world/tilemap.js').TileMap} map
 * @param {number} dx
 * @param {number} dy
 * @returns {{ hitX: boolean, hitY: boolean }}
 */
export function moveAndCollide(body, map, dx, dy) {
  const n = Math.max(1, Math.ceil(Math.max(Math.abs(dx), Math.abs(dy)) / MAX_SUBSTEP));
  let hitX = false;
  let hitY = false;
  for (let i = 0; i < n; i++) {
    if (!hitX) hitX = moveAxisX(body, map, dx / n);
    if (!hitY) hitY = moveAxisY(body, map, dy / n);
  }
  return { hitX, hitY };
}

/** @param {Body} b @param {import('../world/tilemap.js').TileMap} map @param {number} dx */
function moveAxisX(b, map, dx) {
  if (dx === 0) return false;
  const ts = map.tileSize;
  const nx = b.x + dx;
  const top = Math.floor((b.y - b.height) / ts);
  const bottom = Math.floor((b.y - EPS) / ts);
  if (dx > 0) {
    const tx = Math.floor((nx + b.halfWidth - EPS) / ts);
    for (let ty = top; ty <= bottom; ty++) {
      if (isSolidTile(map, tx, ty)) {
        b.x = tx * ts - b.halfWidth;
        return true;
      }
    }
  } else {
    const tx = Math.floor((nx - b.halfWidth) / ts);
    for (let ty = top; ty <= bottom; ty++) {
      if (isSolidTile(map, tx, ty)) {
        b.x = (tx + 1) * ts + b.halfWidth;
        return true;
      }
    }
  }
  b.x = nx;
  return false;
}

/** @param {Body} b @param {import('../world/tilemap.js').TileMap} map @param {number} dy */
function moveAxisY(b, map, dy) {
  if (dy === 0) return false;
  const ts = map.tileSize;
  const ny = b.y + dy;
  const left = Math.floor((b.x - b.halfWidth) / ts);
  const right = Math.floor((b.x + b.halfWidth - EPS) / ts);
  if (dy > 0) {
    const ty = Math.floor((ny - EPS) / ts);
    for (let tx = left; tx <= right; tx++) {
      if (isSolidTile(map, tx, ty)) {
        b.y = ty * ts;
        return true;
      }
    }
  } else {
    const ty = Math.floor((ny - b.height) / ts);
    for (let tx = left; tx <= right; tx++) {
      if (isSolidTile(map, tx, ty)) {
        b.y = (ty + 1) * ts + b.height;
        return true;
      }
    }
  }
  b.y = ny;
  return false;
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
