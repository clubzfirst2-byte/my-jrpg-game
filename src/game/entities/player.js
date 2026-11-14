// @ts-check
// Player movement: walk, dash, jump, fall (DESIGN.md 3.3, 5.3). Plain object + update function.
import { approach } from '../core/math.js';
import { facingFrom } from '../core/facing.js';

export { facingFrom };
import { moveAndCollide, groundHeightUnder } from '../physics/collision.js';
import { LEVEL_PX, Ground } from '../world/tilemap.js';
import { tryGrabWall, updateClimb } from './climbing.js';
import { GLIDE, canOpenGlider, closeGlider, glideStep, openGlider } from './glider.js';
import { COMBAT } from './playerCombat.js';
import { SWIM, enterWater, isInWater, leaveWater, swimStamina, waterSurfaceUnder } from './swimming.js';

/** Tunable movement values (px, px/s, px/s^2, s). */
export const PLAYER_MOVE = Object.freeze({
  walkSpeed: 72,
  dashSpeed: 128,
  accel: 900,
  decel: 1200,
  airAccel: 420,
  gravity: 900,
  /** Apex of a standing jump: enough for a 1-level ledge (16px), not for 2 levels (32px). */
  jumpHeight: 20,
  /** Walk up / down height differences up to this (half a level) without jumping (DESIGN.md 3.2 段差). */
  stepHeight: 8,
  /** Jump still allowed this long after walking off a ledge. */
  coyoteTime: 0.08,
  /** A jump pressed this long before landing still happens on landing (DESIGN.md 1.3). */
  jumpBuffer: 0.12,
});

/** Stamina (DESIGN.md 5.3). One full wheel = 100. */
export const PLAYER_STAMINA = Object.freeze({
  max: 100,
  /** Drain per second while dashing. */
  dashCost: 20,
  /** Recovery per second on the ground when not dashing or climbing. */
  regen: 35,
  /** Seconds after using stamina before it starts to recover. */
  regenDelay: 0.5,
  /** Walk speed multiplier while exhausted (until stamina is full again). */
  exhaustedSpeed: 0.6,
});

const DODGE_SPEED = COMBAT.dodgeSpeed;

/** Falls of up to this height are safe (3 levels). */
export const SAFE_FALL_PX = 3 * LEVEL_PX;
/** Damage (in quarter hearts) per level fallen beyond the safe height. */
export const FALL_DAMAGE_PER_LEVEL = 2;
export const PLAYER_MAX_HP = 12; // 3 hearts x 4 quarters

/** @typedef {'down' | 'up' | 'left' | 'right'} Facing */

/**
 * @typedef {object} Player
 * @property {number} x       feet position on the ground plane
 * @property {number} y
 * @property {number} z       altitude of the feet in px (terrain height when standing)
 * @property {number} prevX   previous logic step (for render interpolation)
 * @property {number} prevY
 * @property {number} prevZ
 * @property {number} vx
 * @property {number} vy
 * @property {number} vz
 * @property {number} halfWidth
 * @property {number} height
 * @property {Facing} facing
 * @property {boolean} moving
 * @property {boolean} dashing
 * @property {boolean} grounded
 * @property {number} groundZ    terrain height under the feet (for the shadow)
 * @property {number} walkTime   seconds spent moving (drives walk animation)
 * @property {number} coyote     seconds left in which a jump is still allowed after leaving ground
 * @property {number} jumpBuffered seconds left for a buffered jump press
 * @property {boolean} jumpHeld
 * @property {number} fallPeakZ  highest z since leaving the ground
 * @property {number} hp
 * @property {number} maxHp
 * @property {number} stamina
 * @property {number} maxStamina
 * @property {boolean} exhausted     stamina ran out: no dash / climb, slower walk until full again
 * @property {number} staminaRestTime seconds since stamina was last used
 * @property {boolean} climbing
 * @property {'up' | 'down' | 'left' | 'right' | null} climbDir direction from the player toward the wall
 * @property {number} climbPush       seconds spent pushing into a climbable wall
 * @property {number} regrabCooldown  seconds until a wall may be grabbed again after letting go
 * @property {boolean} gliding
 * @property {boolean} swimming
 * @property {'none' | 'attack' | 'dodge' | 'aim'} [action]  combat action (P3, see playerCombat.js)
 * @property {number} [actionMs]
 * @property {number} [moveScale]
 * @property {number} [dodgeX]
 * @property {number} [dodgeY]
 * @property {number} [knockX]
 * @property {number} [knockY]
 * @property {number} [knockMs]
 * @property {boolean} [dead]
 * @property {number} [aimX]
 * @property {number} [aimY]
 * @property {boolean} [guarding]
 * @property {number} [guardMs]
 * @property {number} [invulnMs]
 * @property {number} [comboIndex]
 * @property {number} [attackId]
 * @property {number} safeX   last position standing on dry ground (drowning returns here)
 * @property {number} safeY
 * @property {number} safeZ
 * @property {number} spawnX
 * @property {number} spawnY
 * @property {number} spawnZ
 * @property {{ type: 'land', fall: number, damage: number } | { type: 'respawn' } | { type: 'drown' } | { type: 'slip' } | null} lastEvent
 * @property {number} [windX]   P5: wind drift while gliding (px/s), set by the game each step
 * @property {number} [windY]
 * @property {boolean} [updraft] P5: rising air over a fire under the player
 * @property {number} [updraftCap] volume phase 1: how high an updraft of the map carries (px above the ground)
 * @property {boolean} [rainOn]  P5: rain is falling on the player (slippery walls)
 * @property {number} [slipTime]
 */

/** @param {number} x @param {number} y @param {number} [z] @returns {Player} */
export function createPlayer(x, y, z = 0) {
  return {
    x,
    y,
    z,
    prevX: x,
    prevY: y,
    prevZ: z,
    vx: 0,
    vy: 0,
    vz: 0,
    halfWidth: 5,
    height: 6,
    facing: 'down',
    moving: false,
    dashing: false,
    grounded: true,
    groundZ: z,
    walkTime: 0,
    coyote: 0,
    jumpBuffered: 0,
    jumpHeld: false,
    fallPeakZ: z,
    hp: PLAYER_MAX_HP,
    maxHp: PLAYER_MAX_HP,
    stamina: PLAYER_STAMINA.max,
    maxStamina: PLAYER_STAMINA.max,
    exhausted: false,
    staminaRestTime: 0,
    climbing: false,
    climbDir: null,
    climbPush: 0,
    regrabCooldown: 0,
    gliding: false,
    swimming: false,
    safeX: x,
    safeY: y,
    safeZ: z,
    spawnX: x,
    spawnY: y,
    spawnZ: z,
    lastEvent: null,
  };
}

export function jumpVelocity() {
  return Math.sqrt(2 * PLAYER_MOVE.gravity * PLAYER_MOVE.jumpHeight);
}

/**
 * Fall damage in quarter hearts for a drop of `fall` px.
 * @param {number} fall
 */
export function fallDamage(fall) {
  if (fall <= SAFE_FALL_PX + 1e-6) return 0;
  return Math.ceil((fall - SAFE_FALL_PX) / LEVEL_PX) * FALL_DAMAGE_PER_LEVEL;
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
  p.prevZ = p.z;
  p.lastEvent = null;

  // --- jump input (press detection + buffer) ---
  if (input.jump && !p.jumpHeld) p.jumpBuffered = PLAYER_MOVE.jumpBuffer;
  p.jumpHeld = input.jump;
  const busy = p.action !== undefined && p.action !== 'none' && p.action !== 'aim'; // swinging / dodging
  if (p.jumpBuffered > 0 && (p.grounded || p.coyote > 0) && !busy) {
    p.vz = jumpVelocity();
    p.grounded = false;
    p.coyote = 0;
    p.jumpBuffered = 0;
    p.fallPeakZ = p.z;
  }
  // --- climbing (P2.1) ---
  if (p.climbing) {
    p.dashing = false;
    const result = updateClimb(p, input, map, dt);
    p.jumpBuffered = Math.max(0, p.jumpBuffered - dt);
    if (result === 'climbing' || result === 'mantled' || result === 'reachedGround') return;
    // 'released': fall from here using the normal air physics below.
  }

  // --- glider (P2.2): jump in mid-air opens it, jump again closes it ---
  if (p.jumpBuffered > 0 && !p.grounded && !p.climbing && !p.swimming) {
    if (p.gliding) {
      closeGlider(p);
      p.jumpBuffered = 0;
    } else if (canOpenGlider(p)) {
      openGlider(p);
      p.jumpBuffered = 0;
    }
    // Too low to open: the press stays buffered and becomes a jump on landing.
  }

  p.jumpBuffered = Math.max(0, p.jumpBuffered - dt);
  p.coyote = Math.max(0, p.coyote - dt);
  p.regrabCooldown = Math.max(0, p.regrabCooldown - dt);

  // --- swimming (P2.3) ---
  if (p.swimming) {
    updateSwim(p, input, map, dt);
    return;
  }

  // --- horizontal movement ---
  const mag = Math.min(1, Math.hypot(input.moveX, input.moveY));
  const hasInput = mag > 0;
  p.dashing = hasInput && input.dash && p.grounded && !p.exhausted && p.stamina > 0;
  const walkSpeed = PLAYER_MOVE.walkSpeed * (p.exhausted ? PLAYER_STAMINA.exhaustedSpeed : 1);
  if (p.action && p.action !== 'none') p.dashing = false;
  const scale = p.moveScale ?? 1;
  const maxSpeed = (p.gliding ? GLIDE.speed * mag : p.dashing ? PLAYER_MOVE.dashSpeed : walkSpeed * mag) * scale;
  let tx = 0;
  let ty = 0;
  if (hasInput) {
    const len = Math.hypot(input.moveX, input.moveY);
    tx = (input.moveX / len) * maxSpeed;
    ty = (input.moveY / len) * maxSpeed;
    // While swinging or aiming, combat controls the facing.
    if (p.action !== 'attack' && p.action !== 'aim') p.facing = facingFrom(input.moveX, input.moveY, p.facing);
  }
  let rate = (hasInput ? PLAYER_MOVE.accel : PLAYER_MOVE.decel) * dt;
  if (!p.grounded) rate = PLAYER_MOVE.airAccel * dt; // reduced air control keeps jump arcs readable
  if (p.gliding) rate = GLIDE.accel * dt;
  // Keep a dash's momentum through a jump (no instant slow-down when leaving the ground).
  const keepMomentum = !p.grounded && !p.gliding && Math.hypot(p.vx, p.vy) > Math.hypot(tx, ty);
  if (!keepMomentum) {
    p.vx = approach(p.vx, tx, rate);
    p.vy = approach(p.vy, ty, rate);
  }

  if (p.action === 'dodge') {
    // Dodge: a fixed quick hop in the chosen direction (P3).
    p.vx = p.dodgeX * DODGE_SPEED;
    p.vy = p.dodgeY * DODGE_SPEED;
  }
  // Knockback from hits adds on top of the player's own movement (P3).
  const kx = p.knockMs > 0 ? p.knockX : 0;
  const ky = p.knockMs > 0 ? p.knockY : 0;
  const maxHeight = p.grounded ? p.z + PLAYER_MOVE.stepHeight : p.z;
  // The wind carries a glider (P5).
  const wx = p.gliding ? (p.windX ?? 0) : 0;
  const wy = p.gliding ? (p.windY ?? 0) : 0;
  const hit = moveAndCollide(p, map, (p.vx + kx + wx) * dt, (p.vy + ky + wy) * dt, maxHeight);
  if (hit.hitX) p.vx = 0;
  if (hit.hitY) p.vy = 0;

  // Pushing into a climbable wall grabs it (not in the middle of a combat action).
  const pushing = !busy && hasInput && facingFrom(input.moveX, input.moveY, p.facing) === p.facing;
  if (tryGrabWall(p, map, hit, pushing, PLAYER_MOVE.stepHeight, dt)) {
    p.moving = false;
    return;
  }

  // --- vertical movement ---
  const ground = groundHeightUnder(p, map);
  p.groundZ = ground;
  if (p.grounded) {
    if (ground >= p.z - PLAYER_MOVE.stepHeight) {
      p.z = ground; // follow steps and ramps
      // Walked into water at our own level (not water far below the ledge we stand on).
      const surface = waterSurfaceUnder(map, p);
      if (surface !== null && surface >= p.z - PLAYER_MOVE.stepHeight) enterWater(p, surface);
    } else {
      // Walked off a ledge.
      p.grounded = false;
      p.vz = 0;
      p.coyote = PLAYER_MOVE.coyoteTime;
      p.fallPeakZ = p.z;
    }
  }
  if (!p.grounded) {
    if (p.gliding) {
      glideStep(p, dt);
    } else {
      // Exact for constant acceleration, so the jump apex does not depend on the step size.
      p.z += p.vz * dt - 0.5 * PLAYER_MOVE.gravity * dt * dt;
      p.vz -= PLAYER_MOVE.gravity * dt;
      p.fallPeakZ = Math.max(p.fallPeakZ, p.z);
    }
    const surface = waterSurfaceUnder(map, p);
    if (surface !== null && p.z <= surface) {
      enterWater(p, surface); // splashing into water never hurts
    } else if (p.z <= ground) {
      land(p, ground);
    }
  }

  const moved = Math.hypot(p.x - p.prevX, p.y - p.prevY);
  p.moving = p.grounded && moved > 0.01;
  p.walkTime = p.moving ? p.walkTime + dt * (p.dashing ? 1.6 : 1) : 0;
  // Last safe ground (drowning and pits return here). A pit is never safe (P7).
  const under = map.ground[Math.floor(p.y / map.tileSize) * map.width + Math.floor(p.x / map.tileSize)];
  if (p.grounded && !p.swimming && under !== Ground.PIT) {
    p.safeX = p.x;
    p.safeY = p.y;
    p.safeZ = p.z;
  }
  updateStamina(p, dt);
}

/**
 * One step in the water: slow movement, no jumping, stamina drains; walk out onto low shores,
 * grab climbable banks.
 * @param {Player} p
 * @param {import('../input.js').InputFrame} input
 * @param {import('../world/tilemap.js').TileMap} map
 * @param {number} dt
 */
function updateSwim(p, input, map, dt) {
  const mag = Math.min(1, Math.hypot(input.moveX, input.moveY));
  const hasInput = mag > 0;
  const dash = hasInput && input.dash && !p.exhausted;
  const speed = dash ? SWIM.dashSpeed : SWIM.speed * mag;
  let tx = 0;
  let ty = 0;
  if (hasInput) {
    const len = Math.hypot(input.moveX, input.moveY);
    tx = (input.moveX / len) * speed;
    ty = (input.moveY / len) * speed;
    p.facing = facingFrom(input.moveX, input.moveY, p.facing);
  }
  p.vx = approach(p.vx, tx, SWIM.accel * dt);
  p.vy = approach(p.vy, ty, SWIM.accel * dt);
  // Low shores (up to a step above the surface) can be walked onto.
  const hit = moveAndCollide(p, map, p.vx * dt, p.vy * dt, p.z + PLAYER_MOVE.stepHeight);
  if (hit.hitX) p.vx = 0;
  if (hit.hitY) p.vy = 0;

  const pushing = hasInput && facingFrom(input.moveX, input.moveY, p.facing) === p.facing;
  if (tryGrabWall(p, map, hit, pushing, PLAYER_MOVE.stepHeight, dt)) {
    p.moving = false;
    return;
  }

  const ground = groundHeightUnder(p, map);
  p.groundZ = ground;
  if (!isInWater(map, p)) {
    leaveWater(p, ground);
    p.moving = true;
    return;
  }

  const moving = Math.hypot(p.x - p.prevX, p.y - p.prevY) > 0.01;
  p.moving = moving;
  p.dashing = dash && moving;
  p.walkTime = p.walkTime + dt;
  swimStamina(p, moving, p.dashing, dt);
  if (p.hp === 0) p.dead = true;
}

/**
 * Dash drains stamina; resting on the ground restores it after a short delay.
 * Running out makes the player exhausted until the wheel is full again.
 * @param {Player} p @param {number} dt
 */
function updateStamina(p, dt) {
  if (p.dashing && p.moving) {
    p.stamina = Math.max(0, p.stamina - PLAYER_STAMINA.dashCost * dt);
    p.staminaRestTime = 0;
    if (p.stamina <= 0) p.exhausted = true;
    return;
  }
  if (!p.grounded) return;
  p.staminaRestTime += dt;
  if (p.staminaRestTime < PLAYER_STAMINA.regenDelay) return;
  p.stamina = Math.min(p.maxStamina, p.stamina + PLAYER_STAMINA.regen * dt);
  if (p.stamina >= p.maxStamina) p.exhausted = false;
}

/** @param {Player} p @param {number} ground */
function land(p, ground) {
  const fall = p.fallPeakZ - ground;
  p.z = ground;
  p.vz = 0;
  p.grounded = true;
  p.gliding = false;
  const damage = fallDamage(fall);
  p.lastEvent = { type: 'land', fall, damage };
  if (damage > 0) {
    p.hp = Math.max(0, p.hp - damage);
    if (p.hp === 0) p.dead = true; // the game state runs the death / respawn sequence (P3)
  }
}

/**
 * Back to the spawn point with full health (called by the game state after the death sequence).
 * @param {Player} p
 */
export function respawn(p) {
  p.x = p.prevX = p.spawnX;
  p.y = p.prevY = p.spawnY;
  p.z = p.prevZ = p.groundZ = p.spawnZ;
  p.vx = p.vy = p.vz = 0;
  p.hp = p.maxHp;
  p.stamina = p.maxStamina;
  p.exhausted = false;
  p.climbing = false;
  p.gliding = false;
  p.swimming = false;
  p.grounded = true;
  p.lastEvent = { type: 'respawn' };
}

