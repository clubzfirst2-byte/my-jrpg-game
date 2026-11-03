// @ts-check
// Player movement for P1: walk, dash, facing. Plain object + update function (DESIGN.md 1.2).
import { approach } from '../core/math.js';
import { moveAndCollide } from '../physics/collision.js';

/** Tunable movement values (px / s, px / s^2). */
export const PLAYER_MOVE = Object.freeze({
  walkSpeed: 72,
  dashSpeed: 128,
  accel: 900,
  decel: 1200,
});

/** @typedef {'down' | 'up' | 'left' | 'right'} Facing */

/**
 * @typedef {object} Player
 * @property {number} x       feet position
 * @property {number} y
 * @property {number} prevX   position at the previous logic step (for render interpolation)
 * @property {number} prevY
 * @property {number} vx
 * @property {number} vy
 * @property {number} halfWidth
 * @property {number} height
 * @property {Facing} facing
 * @property {boolean} moving
 * @property {boolean} dashing
 * @property {number} walkTime  seconds spent moving (drives walk animation)
 */

/** @param {number} x @param {number} y @returns {Player} */
export function createPlayer(x, y) {
  return {
    x,
    y,
    prevX: x,
    prevY: y,
    vx: 0,
    vy: 0,
    halfWidth: 5,
    height: 6,
    facing: 'down',
    moving: false,
    dashing: false,
    walkTime: 0,
  };
}

/**
 * @param {Player} p
 * @param {import('../input.js').InputFrame} input
 * @param {import('../world/tilemap.js').TileMap} map
 * @param {number} dt seconds (fixed step)
 */
export function updatePlayer(p, input, map, dt) {
  p.prevX = p.x;
  p.prevY = p.y;

  const mag = Math.min(1, Math.hypot(input.moveX, input.moveY));
  const hasInput = mag > 0;
  p.dashing = hasInput && input.dash;
  const maxSpeed = (p.dashing ? PLAYER_MOVE.dashSpeed : PLAYER_MOVE.walkSpeed) * (p.dashing ? 1 : mag);

  let tx = 0;
  let ty = 0;
  if (hasInput) {
    const len = Math.hypot(input.moveX, input.moveY);
    tx = (input.moveX / len) * maxSpeed;
    ty = (input.moveY / len) * maxSpeed;
    p.facing = facingFrom(input.moveX, input.moveY, p.facing);
  }
  const rate = (hasInput ? PLAYER_MOVE.accel : PLAYER_MOVE.decel) * dt;
  p.vx = approach(p.vx, tx, rate);
  p.vy = approach(p.vy, ty, rate);

  const hit = moveAndCollide(p, map, p.vx * dt, p.vy * dt);
  if (hit.hitX) p.vx = 0;
  if (hit.hitY) p.vy = 0;

  const moved = Math.hypot(p.x - p.prevX, p.y - p.prevY);
  p.moving = moved > 0.01;
  p.walkTime = p.moving ? p.walkTime + dt * (p.dashing ? 1.6 : 1) : 0;
}

/**
 * 4-way facing from the dominant axis; keeps the current facing on exact diagonals to avoid flicker.
 * @param {number} x @param {number} y @param {Facing} current
 * @returns {Facing}
 */
export function facingFrom(x, y, current) {
  const ax = Math.abs(x);
  const ay = Math.abs(y);
  if (ax === 0 && ay === 0) return current;
  if (Math.abs(ax - ay) < 1e-3) {
    // Diagonal: keep facing if it already matches one of the two axes.
    const h = x > 0 ? 'right' : 'left';
    const v = y > 0 ? 'down' : 'up';
    return current === h || current === v ? current : v;
  }
  if (ax > ay) return x > 0 ? 'right' : 'left';
  return y > 0 ? 'down' : 'up';
}
