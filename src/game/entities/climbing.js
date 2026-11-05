// @ts-check
// Climbing (DESIGN.md 3.2, 5.3; P2.1). Pure logic on the player object.
//
// Controls are relative to the wall, the same for every wall direction:
//   push toward the wall = climb up, pull away = climb down, sideways = move along the wall.
// Reaching the top pulls the player up onto the ledge ("mantle"). Jump lets go.
import { Ground, Shape, isSolidTile, inBounds, terrainHeightAt } from '../world/tilemap.js';
import { groundHeightUnder, moveAndCollide } from '../physics/collision.js';

export const CLIMB = Object.freeze({
  /** Vertical climbing speed (px/s). */
  speed: 24,
  /** Sideways speed along the wall (px/s). */
  traverseSpeed: 24,
  /** Seconds of pushing into a wall before grabbing it (avoids accidental grabs when brushing walls). */
  grabDelay: 0.2,
  /** Stamina per second while moving on the wall / while hanging still. */
  moveCost: 12,
  hangCost: 0,
  /** How far the player is pulled onto the ledge when reaching the top (px). */
  mantleDistance: 8,
  /** After letting go, the wall cannot be grabbed again for this long (no instant re-grab mid-fall). */
  regrabCooldown: 0.4,
  /** Rain (P5): walls are slippery. Climbing up, the player slides back down this far every so often. */
  slipEvery: 1.2,
  slipDistance: 10,
});

/** @typedef {'up' | 'down' | 'left' | 'right'} Dir */

/** @type {Record<Dir, { dx: number, dy: number }>} */
const DIRS = { up: { dx: 0, dy: -1 }, down: { dx: 0, dy: 1 }, left: { dx: -1, dy: 0 }, right: { dx: 1, dy: 0 } };

/**
 * The point just beyond the body's leading edge in a direction.
 * @param {{ x: number, y: number, halfWidth: number, height: number }} b @param {Dir} dir
 */
export function probePoint(b, dir) {
  switch (dir) {
    case 'up':
      return { px: b.x, py: b.y - b.height - 0.5 };
    case 'down':
      return { px: b.x, py: b.y + 0.5 };
    case 'left':
      return { px: b.x - b.halfWidth - 0.5, py: b.y - b.height / 2 };
    default:
      return { px: b.x + b.halfWidth + 0.5, py: b.y - b.height / 2 };
  }
}

/**
 * Whether the terrain at a point can be climbed. Ruin walls, ramps (stairs), water, trees and rocks cannot.
 * @param {import('../world/tilemap.js').TileMap} map @param {number} px @param {number} py
 */
export function isClimbableAt(map, px, py) {
  const tx = Math.floor(px / map.tileSize);
  const ty = Math.floor(py / map.tileSize);
  if (!inBounds(map, tx, ty) || isSolidTile(map, tx, ty)) return false;
  const i = ty * map.width + tx;
  return map.ground[i] !== Ground.RUIN && map.ground[i] !== Ground.WALL && map.shape[i] !== Shape.RAMP_N;
}

/**
 * Describes the wall in front of the body.
 * @param {import('./player.js').Player} p @param {import('../world/tilemap.js').TileMap} map @param {Dir} dir
 */
export function wallAhead(p, map, dir) {
  const { px, py } = probePoint(p, dir);
  return { top: terrainHeightAt(map, px, py), climbable: isClimbableAt(map, px, py) };
}

/**
 * Called each step while on the ground or in the air. Grabs the wall the player is pushing into.
 * @param {import('./player.js').Player} p
 * @param {import('../world/tilemap.js').TileMap} map
 * @param {{ hitX: boolean, hitY: boolean }} hit collision result of this step's move
 * @param {boolean} pushing input points into `p.facing`
 * @param {number} stepHeight
 * @param {number} dt
 */
export function tryGrabWall(p, map, hit, pushing, stepHeight, dt) {
  const horizontal = p.facing === 'left' || p.facing === 'right';
  const blocked = horizontal ? hit.hitX : hit.hitY;
  if (!pushing || !blocked || p.exhausted || p.stamina <= 0 || p.regrabCooldown > 0) {
    p.climbPush = 0;
    return false;
  }
  const wall = wallAhead(p, map, p.facing);
  // Standing or swimming: needs a real wall (taller than a step) and a deliberate push.
  const settled = p.grounded || p.swimming;
  const tallEnough = settled ? wall.top > p.z + stepHeight : wall.top > p.z;
  if (!wall.climbable || !tallEnough) {
    p.climbPush = 0;
    return false;
  }
  // In the air the grab is immediate; on the ground it needs a short deliberate push.
  p.climbPush += dt;
  if (settled && p.climbPush < CLIMB.grabDelay) return false;
  p.climbing = true;
  p.gliding = false;
  p.swimming = false;
  p.climbDir = p.facing;
  p.grounded = false;
  p.vx = p.vy = p.vz = 0;
  p.climbPush = 0;
  return true;
}

/**
 * One fixed step while climbing.
 * @param {import('./player.js').Player} p
 * @param {import('../input.js').InputFrame} input
 * @param {import('../world/tilemap.js').TileMap} map
 * @param {number} dt
 * @returns {'climbing' | 'mantled' | 'released' | 'reachedGround'}
 */
export function updateClimb(p, input, map, dt) {
  const dir = /** @type {Dir} */ (p.climbDir);
  const d = DIRS[dir];
  // Perpendicular axis along the wall.
  const s = { dx: d.dy === 0 ? 0 : 1, dy: d.dy === 0 ? 1 : 0 };
  const toward = input.moveX * d.dx + input.moveY * d.dy;
  const side = input.moveX * s.dx + input.moveY * s.dy;

  if (p.exhausted || p.stamina <= 0) return release(p);
  if (p.jumpBuffered > 0) {
    p.jumpBuffered = 0;
    return release(p);
  }

  let moving = false;

  // Along the wall: only while the wall continues and nothing blocks the way at this height.
  if (Math.abs(side) > 0.01) {
    const delta = side * CLIMB.traverseSpeed * dt;
    const probe = { x: p.x + s.dx * delta, y: p.y + s.dy * delta, halfWidth: p.halfWidth, height: p.height };
    const { px, py } = probePoint(probe, dir);
    const groundThere = groundHeightUnder(probe, map);
    const wallThere = terrainHeightAt(map, px, py);
    if (isClimbableAt(map, px, py) && wallThere > groundThere) {
      const before = { x: p.x, y: p.y };
      moveAndCollide(p, map, s.dx * delta, s.dy * delta, p.z);
      moving = Math.hypot(p.x - before.x, p.y - before.y) > 0.001;
    }
  }

  // Up / down the wall.
  if (Math.abs(toward) > 0.01) {
    p.z += toward * CLIMB.speed * dt;
    moving = true;
  }
  // Rain: going up, the hands slip now and then (BotW-like; the way up takes longer and more stamina).
  if (p.rainOn && toward > 0.01) {
    p.slipTime = (p.slipTime ?? 0) + dt;
    if (p.slipTime >= CLIMB.slipEvery) {
      p.slipTime = 0;
      p.z -= CLIMB.slipDistance;
      p.lastEvent = { type: 'slip' };
    }
  } else {
    p.slipTime = 0;
  }

  const ground = groundHeightUnder(p, map);
  p.groundZ = ground;
  const wall = wallAhead(p, map, dir);

  if (p.z >= wall.top) return mantle(p, map, d);
  if (p.z <= ground) {
    p.z = ground;
    p.climbing = false;
    p.grounded = true;
    return /** @type {const} */ ('reachedGround');
  }

  p.stamina = Math.max(0, p.stamina - (moving ? CLIMB.moveCost : CLIMB.hangCost) * dt);
  p.staminaRestTime = 0;
  if (p.stamina <= 0) p.exhausted = true;
  p.moving = moving;
  p.walkTime = moving ? p.walkTime + dt : p.walkTime;
  return 'climbing';
}

/**
 * @param {import('./player.js').Player} p
 * @returns {'released'}
 */
function release(p) {
  p.climbing = false;
  p.regrabCooldown = CLIMB.regrabCooldown;
  p.grounded = false;
  p.vz = 0;
  p.fallPeakZ = p.z;
  p.coyote = 0;
  return 'released';
}

/**
 * Pulls the player up onto the ledge.
 * @param {import('./player.js').Player} p @param {import('../world/tilemap.js').TileMap} map @param {{ dx: number, dy: number }} d
 * @returns {'mantled'}
 */
function mantle(p, map, d) {
  // Move fully onto the top tile (the body is flush with the wall, so this lands inside it).
  const dist = d.dy !== 0 ? p.height + 2 : p.halfWidth * 2 + 2;
  p.x += d.dx * Math.max(dist, CLIMB.mantleDistance);
  p.y += d.dy * Math.max(dist, CLIMB.mantleDistance);
  p.z = groundHeightUnder(p, map);
  p.groundZ = p.z;
  p.climbing = false;
  p.grounded = true;
  p.vx = p.vy = p.vz = 0;
  p.fallPeakZ = p.z;
  return 'mantled';
}
