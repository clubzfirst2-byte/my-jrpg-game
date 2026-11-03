// @ts-check
// Swimming (DESIGN.md 3.3.4; P2.3). Pure logic on the player object.
// Water is walkable: stepping in starts swimming. Swimming is slow, cannot jump, and spends stamina.
// Running out of stamina while swimming = drowning: back to the last safe ground, half a heart lost.
import { Ground, inBounds } from '../world/tilemap.js';

export const SWIM = Object.freeze({
  /** Swimming speed (px/s) and with the dash button held. */
  speed: 40,
  dashSpeed: 64,
  accel: 300,
  /** Stamina per second: treading water / swimming / dash-swimming. */
  idleCost: 3,
  moveCost: 6,
  dashCost: 18,
  /** Quarter hearts lost when drowning. */
  drownDamage: 2,
});

/**
 * Whether the body's feet center is over water.
 * @param {import('../world/tilemap.js').TileMap} map
 * @param {{ x: number, y: number, height: number }} b
 */
export function isInWater(map, b) {
  return waterSurfaceUnder(map, b) !== null;
}

/**
 * Height of the water surface under the body's feet center, or null if not over water.
 * @param {import('../world/tilemap.js').TileMap} map
 * @param {{ x: number, y: number, height: number }} b
 */
export function waterSurfaceUnder(map, b) {
  const tx = Math.floor(b.x / map.tileSize);
  const ty = Math.floor((b.y - b.height / 2) / map.tileSize);
  if (!inBounds(map, tx, ty)) return null;
  const i = ty * map.width + tx;
  return map.ground[i] === Ground.WATER ? map.elev[i] : null;
}

/**
 * Starts swimming at the water surface.
 * @param {import('./player.js').Player} p @param {number} surface
 */
export function enterWater(p, surface) {
  p.swimming = true;
  p.grounded = false;
  p.gliding = false;
  p.climbing = false;
  p.dashing = false;
  p.z = surface;
  p.vz = 0;
  p.fallPeakZ = surface; // falling into water never hurts
  p.coyote = 0;
}

/** @param {import('./player.js').Player} p @param {number} ground */
export function leaveWater(p, ground) {
  p.swimming = false;
  p.grounded = true;
  p.z = ground;
  p.vz = 0;
}

/**
 * Stamina for one step of swimming. Returns true if the player drowned.
 * @param {import('./player.js').Player} p @param {boolean} moving @param {boolean} dashing @param {number} dt
 */
export function swimStamina(p, moving, dashing, dt) {
  const cost = dashing ? SWIM.dashCost : moving ? SWIM.moveCost : SWIM.idleCost;
  p.stamina = Math.max(0, p.stamina - cost * dt);
  p.staminaRestTime = 0;
  if (p.stamina > 0) return false;
  p.exhausted = true;
  drown(p);
  return true;
}

/**
 * Back to the last safe ground, minus half a heart.
 * @param {import('./player.js').Player} p
 */
export function drown(p) {
  p.swimming = false;
  p.grounded = true;
  p.x = p.prevX = p.safeX;
  p.y = p.prevY = p.safeY;
  p.z = p.prevZ = p.groundZ = p.safeZ;
  p.vx = p.vy = p.vz = 0;
  p.hp = Math.max(0, p.hp - SWIM.drownDamage);
  p.lastEvent = { type: 'drown' };
}
