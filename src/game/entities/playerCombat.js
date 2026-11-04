// @ts-check
// Player combat actions (DESIGN.md 5.3, 5.6; P3): sword combo, dodge, guard, bow.
// All timings are in milliseconds (DESIGN.md 1.3) so they hold at 30fps as well as 60fps.
import { direction, facingVector } from '../combat/hitbox.js';
import { facingFrom } from '../core/facing.js';
import { chestInReach, openChest } from '../world/features.js';

export const SWORD = Object.freeze([
  // startup: before the blade hits; active: hitbox live; recovery: after. reach: hitbox offset.
  // knock: knockback strength. Light hits barely push (so the combo stays in reach); the finisher sends flying.
  { startupMs: 70, activeMs: 110, recoveryMs: 200, damage: 4, reach: 13, radius: 10, knock: 0.2 },
  { startupMs: 70, activeMs: 110, recoveryMs: 200, damage: 4, reach: 13, radius: 10, knock: 0.2 },
  { startupMs: 110, activeMs: 140, recoveryMs: 380, damage: 8, reach: 15, radius: 12, knock: 1 }, // finisher
]);

export const COMBAT = Object.freeze({
  /** A press this long before a swing ends queues the next swing (DESIGN.md 1.3: 先行入力). */
  attackBufferMs: 200,
  /** Movement while swinging (fraction of walk speed). */
  attackMoveScale: 0.2,
  dodgeMs: 320,
  dodgeSpeed: 150,
  /** Invulnerable for this long from the start of a dodge. */
  dodgeInvulnMs: 260,
  /** A hit arriving this early in a dodge is a perfect dodge (slow-motion counter window). */
  justDodgeMs: 150,
  dodgeCooldownMs: 150,
  /** A hit arriving this soon after raising the guard is a perfect guard (parry). */
  justGuardMs: 150,
  guardMoveScale: 0.5,
  bowDrawMs: 400,
  bowMoveScale: 0.4,
  arrowSpeed: 240,
  arrowLifeMs: 900,
  arrowDamage: 4,
  /** Aiming in the air slows time (DESIGN.md 5.3) and costs stamina per second. */
  bulletTimeScale: 0.3,
  bulletTimeCost: 20,
  /** After taking a hit. */
  hurtInvulnMs: 800,
  knockbackSpeed: 140,
  knockbackMs: 200,
  /** Perfect dodge: enemies move at this speed for this long. */
  flurryScale: 0.2,
  flurryMs: 1500,
});

/**
 * Adds combat fields to a player object.
 * @param {import('./player.js').Player} p
 */
export function initCombat(p) {
  Object.assign(p, {
    aimX: 0,
    aimY: 1,
    action: /** @type {'none' | 'attack' | 'dodge' | 'aim'} */ ('none'),
    actionMs: 0,
    comboIndex: 0,
    comboQueued: false,
    attackId: 0,
    attackHeld: false,
    dodgeHeld: false,
    dodgeX: 0,
    dodgeY: 0,
    dodgeCooldownMs: 0,
    dodgeBufferMs: 0,
    guarding: false,
    guardMs: 0,
    bowHeld: false,
    invulnMs: 0,
    knockX: 0,
    knockY: 0,
    knockMs: 0,
    dead: false,
    moveScale: 1,
  });
}

/** True while the player may start combat actions on the ground. @param {any} p */
function canActOnGround(p) {
  return p.grounded && !p.climbing && !p.swimming && !p.gliding && !p.dead;
}

/**
 * Handles combat input for one step, before movement. Emits hitboxes and projectiles into `state`.
 * @param {any} p player (with combat fields)
 * @param {import('../input.js').InputFrame} input
 * @param {any} state game state ({ hitboxes, projectiles, nextId, ... })
 * @param {number} dt seconds
 */
export function combatStep(p, input, state, dt) {
  const ms = dt * 1000;
  // Aim follows the stick (analog), falling back to the facing.
  if (Math.hypot(input.moveX, input.moveY) > 0.2) {
    const d = direction(input.moveX, input.moveY, { x: 0, y: 1 });
    p.aimX = d.x;
    p.aimY = d.y;
  } else if (p.action === 'none') {
    const f = facingVector(p.facing);
    p.aimX = f.x;
    p.aimY = f.y;
  }

  p.invulnMs = Math.max(0, p.invulnMs - ms);
  p.knockMs = Math.max(0, p.knockMs - ms);
  p.dodgeCooldownMs = Math.max(0, p.dodgeCooldownMs - ms);
  p.dodgeBufferMs = Math.max(0, p.dodgeBufferMs - ms);

  const attackPressed = !!input.attack && !p.attackHeld;
  const dodgePressed = !!input.dodge && !p.dodgeHeld;
  // A dodge pressed while busy is remembered briefly (先行入力) and happens as soon as allowed.
  if (dodgePressed) p.dodgeBufferMs = COMBAT.attackBufferMs;
  p.attackHeld = !!input.attack;
  p.dodgeHeld = !!input.dodge;

  // Guard: held, on the ground, not during other actions.
  const wantsGuard = !!input.guard && canActOnGround(p) && p.action === 'none';
  if (wantsGuard && !p.guarding) p.guardMs = 0;
  p.guarding = wantsGuard;
  if (p.guarding) p.guardMs += ms;

  state.bulletTime = false;
  if (p.dead) {
    p.action = 'none';
    p.moveScale = 0;
    return;
  }
  if (p.climbing || p.swimming || p.gliding) {
    p.action = 'none';
    p.bowHeld = false;
    p.moveScale = 1;
    return;
  }

  switch (p.action) {
    case 'attack': {
      // Dodge cancels a swing once the blade has passed (its recovery).
      const sw = SWORD[p.comboIndex];
      if (p.dodgeBufferMs > 0 && p.actionMs >= sw.startupMs + sw.activeMs && p.dodgeCooldownMs <= 0) {
        p.dodgeBufferMs = 0;
        startDodge(p, input);
        state.events.push({ type: 'dodge', tick: state.tick });
        break;
      }
      stepAttack(p, attackPressed, state, ms);
      break;
    }
    case 'dodge':
      p.actionMs += ms;
      if (p.actionMs >= COMBAT.dodgeMs) {
        p.action = 'none';
        p.dodgeCooldownMs = COMBAT.dodgeCooldownMs;
      }
      break;
    case 'aim':
      stepAim(p, input, state, ms, dt);
      break;
    default:
      if (p.dodgeBufferMs > 0 && canActOnGround(p) && p.dodgeCooldownMs <= 0) {
        p.dodgeBufferMs = 0;
        startDodge(p, input);
        state.events.push({ type: 'dodge', tick: state.tick });
      } else if (attackPressed && canActOnGround(p) && !p.guarding) {
        // The attack button doubles as "open / examine" in front of a chest (P3.5).
        const chest = state.chests ? chestInReach(state) : null;
        if (chest) {
          openChest(state, chest);
        } else {
          startSwing(p, 0);
          state.events.push({ type: 'swing', tick: state.tick });
        }
      } else if (input.bow && !p.guarding && !p.bowHeld) {
        p.bowHeld = true;
        // P6: a bow in hand and an arrow to shoot.
        if (p.bow && p.arrows > 0) {
          p.action = 'aim';
          p.actionMs = 0;
        } else {
          state.events.push({ type: p.bow ? 'noArrows' : 'noBow', tick: state.tick });
        }
      }
  }
  if (!input.bow) p.bowHeld = false;

  p.moveScale =
    p.action === 'attack'
      ? COMBAT.attackMoveScale
      : p.action === 'aim' && p.grounded
        ? COMBAT.bowMoveScale
        : p.guarding
          ? COMBAT.guardMoveScale
          : 1;
}

/** @param {any} p @param {number} index */
function startSwing(p, index) {
  p.action = 'attack';
  p.actionMs = 0;
  p.comboIndex = index;
  p.comboQueued = false;
  p.attackId += 1;
  p.facing = facingFrom(p.aimX, p.aimY, p.facing);
}

/** @param {any} p @param {boolean} pressed @param {any} state @param {number} ms */
function stepAttack(p, pressed, state, ms) {
  // The weapon in hand (P6) scales the swing: damage, reach and speed (slower = longer timings).
  const w = p.weapon ?? { damage: 1, reach: 0, speed: 1, element: null };
  const base = SWORD[p.comboIndex];
  const sw = {
    ...base,
    startupMs: base.startupMs * w.speed,
    activeMs: base.activeMs * w.speed,
    recoveryMs: base.recoveryMs * w.speed,
    reach: base.reach + w.reach,
    damage: Math.max(1, Math.round(base.damage * w.damage * (p.attackUp ? 1.25 : 1))),
  };
  const total = sw.startupMs + sw.activeMs + sw.recoveryMs;
  if (pressed && p.comboIndex < SWORD.length - 1 && total - p.actionMs <= sw.recoveryMs + COMBAT.attackBufferMs) {
    p.comboQueued = true;
  }
  p.actionMs += ms;
  const t = p.actionMs;
  if (t > sw.startupMs && t <= sw.startupMs + sw.activeMs) {
    state.hitboxes.push({
      owner: 'player',
      id: `p${p.attackId}`,
      x: p.x + p.aimX * sw.reach,
      y: p.y - 4 + p.aimY * sw.reach,
      z: p.z,
      r: sw.radius,
      damage: sw.damage,
      knock: sw.knock,
      from: { x: p.x, y: p.y },
      kind: 'melee',
      element: w.element,
    });
  }
  // A queued press cancels the recovery into the next swing.
  if (p.comboQueued && t >= sw.startupMs + sw.activeMs) {
    startSwing(p, p.comboIndex + 1);
    return;
  }
  if (t >= total) {
    p.action = 'none';
    p.comboIndex = 0;
  }
}

/** @param {any} p @param {import('../input.js').InputFrame} input */
function startDodge(p, input) {
  // Dodge toward the stick; with no input, hop backward from the facing.
  const f = facingVector(p.facing);
  const d = Math.hypot(input.moveX, input.moveY) > 0.2 ? direction(input.moveX, input.moveY, f) : { x: -f.x, y: -f.y };
  p.action = 'dodge';
  p.actionMs = 0;
  p.dodgeX = d.x;
  p.dodgeY = d.y;
  p.guarding = false;
}

/**
 * Bow: hold to draw (and aim with the stick), release after a full draw to shoot.
 * @param {any} p @param {import('../input.js').InputFrame} input @param {any} state @param {number} ms @param {number} dt
 */
function stepAim(p, input, state, ms, dt) {
  p.actionMs += ms;
  p.facing = facingFrom(p.aimX, p.aimY, p.facing);
  if (!p.grounded) {
    // Aiming in mid-air slows time and costs stamina (real time, not slowed time).
    state.bulletTime = p.stamina > 0;
    p.stamina = Math.max(0, p.stamina - COMBAT.bulletTimeCost * dt / (state.bulletTime ? COMBAT.bulletTimeScale : 1));
    p.staminaRestTime = 0;
  }
  if (input.bow) return;
  // Released.
  if (p.actionMs >= COMBAT.bowDrawMs) {
    state.projectiles.push({
      kind: 'arrow',
      owner: 'player',
      id: `a${state.nextId++}`,
      x: p.x + p.aimX * 8,
      y: p.y - 4 + p.aimY * 8,
      z: p.z,
      vx: p.aimX * COMBAT.arrowSpeed,
      vy: p.aimY * COMBAT.arrowSpeed,
      lifeMs: COMBAT.arrowLifeMs,
      damage: Math.max(1, Math.round(COMBAT.arrowDamage * (p.bow?.damage ?? 1) * (p.attackUp ? 1.25 : 1))),
    });
    state.events.push({ type: 'shoot', tick: state.tick });
  }
  p.action = 'none';
  p.actionMs = 0;
}

/** Whether the player is currently invulnerable from a dodge. @param {any} p */
export function dodgeInvulnerable(p) {
  return p.action === 'dodge' && p.actionMs <= COMBAT.dodgeInvulnMs;
}
