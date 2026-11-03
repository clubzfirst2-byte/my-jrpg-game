// @ts-check
// Two enemy types for P3 (DESIGN.md 5.6): a melee "beast" and a ranged "archer".
// Both telegraph their attacks (a visible wind-up) so a perfect dodge / guard is readable.
import { moveAndCollide, groundHeightUnder } from '../physics/collision.js';
import { waterSurfaceUnder } from './swimming.js';
import { direction, overlaps } from '../combat/hitbox.js';
import { hitPlayer } from '../combat/damage.js';

export const ENEMY_KINDS = Object.freeze({
  beast: {
    hp: 12,
    speed: 46,
    sightRange: 96,
    attackRange: 24,
    windupMs: 500,
    activeMs: 160,
    recoveryMs: 700,
    lungeSpeed: 170,
    damage: 2,
    radius: 6,
  },
  archer: {
    hp: 8,
    speed: 34,
    sightRange: 140,
    keepMin: 64,
    keepMax: 112,
    windupMs: 600,
    cooldownMs: 1800,
    shotSpeed: 90,
    shotLifeMs: 2200,
    damage: 2,
    radius: 6,
  },
});

/** Stunned after a parry (perfect guard) for this long. */
export const PARRY_STUN_MS = 1200;
const HALF_WIDTH = 5;
const HEIGHT = 6;
const STEP = 8;

/**
 * @param {'beast' | 'archer'} kind @param {number} x @param {number} y @param {number} z @param {number} id
 */
export function createEnemy(kind, x, y, z, id) {
  const k = ENEMY_KINDS[kind];
  return {
    id,
    kind,
    x,
    y,
    z,
    prevX: x,
    prevY: y,
    homeX: x,
    homeY: y,
    halfWidth: HALF_WIDTH,
    height: HEIGHT,
    hp: k.hp,
    maxHp: k.hp,
    state: 'idle',
    t: 0,
    cooldownMs: 0,
    stunMs: 0,
    faceX: 0,
    faceY: 1,
    lastHitId: '',
    attackSeq: 0,
    knockX: 0,
    knockY: 0,
    knockMs: 0,
    wanderMs: 0,
    wanderX: 0,
    wanderY: 0,
  };
}

/**
 * One AI step. `dt` is already scaled by slow motion.
 * @param {any} e @param {any} state @param {number} dt seconds
 */
export function updateEnemy(e, state, dt) {
  const ms = dt * 1000;
  e.prevX = e.x;
  e.prevY = e.y;
  e.t += ms;
  if (e.state === 'dead') return;
  const k = ENEMY_KINDS[/** @type {'beast' | 'archer'} */ (e.kind)];
  const p = state.player;
  const dx = p.x - e.x;
  const dy = p.y - e.y;
  const dist = Math.hypot(dx, dy);
  const sees = !p.dead && dist < k.sightRange && Math.abs(p.z - e.z) < 24 && !p.swimming;
  const toPlayer = direction(dx, dy, { x: e.faceX, y: e.faceY });

  // Knockback slides the enemy regardless of state.
  if (e.knockMs > 0) {
    e.knockMs -= ms;
    walk(e, state.map, e.knockX * dt, e.knockY * dt);
  }

  switch (e.state) {
    case 'stun':
      if (e.t >= e.stunMs) setState(e, 'idle');
      break;
    case 'idle':
    case 'chase':
      if (!sees) {
        wander(e, state.map, k, ms, dt);
        break;
      }
      e.faceX = toPlayer.x;
      e.faceY = toPlayer.y;
      if (e.kind === 'beast') {
        if (dist <= /** @type {typeof ENEMY_KINDS.beast} */ (k).attackRange) setState(e, 'windup');
        else walk(e, state.map, toPlayer.x * k.speed * dt, toPlayer.y * k.speed * dt);
      } else {
        e.cooldownMs = Math.max(0, e.cooldownMs - ms);
        const archer = /** @type {typeof ENEMY_KINDS.archer} */ (k);
        if (dist < archer.keepMin) walk(e, state.map, -toPlayer.x * k.speed * dt, -toPlayer.y * k.speed * dt);
        else if (dist > archer.keepMax) walk(e, state.map, toPlayer.x * k.speed * dt, toPlayer.y * k.speed * dt);
        if (e.cooldownMs <= 0) setState(e, 'windup');
      }
      break;
    case 'windup':
      e.faceX = toPlayer.x;
      e.faceY = toPlayer.y;
      if (e.t >= k.windupMs) {
        if (e.kind === 'beast') {
          e.attackSeq += 1;
          setState(e, 'attack');
        } else {
          shoot(e, state, /** @type {typeof ENEMY_KINDS.archer} */ (k));
          e.cooldownMs = /** @type {typeof ENEMY_KINDS.archer} */ (k).cooldownMs;
          setState(e, 'idle');
        }
      }
      break;
    case 'attack': {
      // Beast lunge: a hitbox on its body while it moves.
      const beast = /** @type {typeof ENEMY_KINDS.beast} */ (k);
      walk(e, state.map, e.faceX * beast.lungeSpeed * dt, e.faceY * beast.lungeSpeed * dt);
      const hit = { x: e.x + e.faceX * 6, y: e.y - 3 + e.faceY * 6, z: e.z, r: 8 };
      const body = { x: p.x, y: p.y - 3, z: p.z, r: 5 };
      if (overlaps(hit, body) && e.hitPlayerSeq !== e.attackSeq) {
        const result = hitPlayer(state, { owner: 'enemy', id: `e${e.id}-${e.attackSeq}`, damage: beast.damage, from: { x: e.x, y: e.y }, kind: 'melee' });
        // Any contact uses up this lunge: a dodged or blocked attack must not land later in the same lunge.
        e.hitPlayerSeq = e.attackSeq;
        if (result === 'parried') {
          e.stunMs = PARRY_STUN_MS;
          setState(e, 'stun');
          break;
        }
      }
      if (e.t >= beast.activeMs) setState(e, 'recover');
      break;
    }
    case 'recover':
      if (e.t >= /** @type {typeof ENEMY_KINDS.beast} */ (k).recoveryMs) setState(e, 'idle');
      break;
  }
}

/** @param {any} e @param {string} s */
function setState(e, s) {
  e.state = s;
  e.t = 0;
}

/**
 * Moves on the ground only (no climbing, no swimming, no falling off cliffs).
 * @param {any} e @param {any} map @param {number} dx @param {number} dy
 */
function walk(e, map, dx, dy) {
  const before = { x: e.x, y: e.y };
  moveAndCollide(e, map, dx, dy, e.z + STEP);
  const ground = groundHeightUnder(e, map);
  if (waterSurfaceUnder(map, e) !== null || ground < e.z - STEP) {
    e.x = before.x; // stay out of water and away from ledges
    e.y = before.y;
    return;
  }
  e.z = ground;
}

/** @param {any} e @param {any} map @param {any} k @param {number} ms @param {number} dt */
function wander(e, map, k, ms, dt) {
  e.wanderMs -= ms;
  if (e.wanderMs <= 0) {
    // Deterministic wander from the enemy's own counters (no global RNG): pause, then drift.
    const phase = (e.id * 7 + Math.floor(e.t / 1000)) % 4;
    const dirs = [
      { x: 1, y: 0 },
      { x: 0, y: 1 },
      { x: -1, y: 0 },
      { x: 0, y: -1 },
    ];
    const home = direction(e.homeX - e.x, e.homeY - e.y, dirs[phase]);
    const far = Math.hypot(e.homeX - e.x, e.homeY - e.y) > 32;
    const d = far ? home : dirs[phase];
    e.wanderX = phase % 2 === 0 || far ? d.x : 0;
    e.wanderY = phase % 2 === 0 || far ? d.y : 0;
    e.wanderMs = 1200;
  }
  walk(e, map, e.wanderX * k.speed * 0.4 * dt, e.wanderY * k.speed * 0.4 * dt);
}

/** @param {any} e @param {any} state @param {typeof ENEMY_KINDS.archer} k */
function shoot(e, state, k) {
  state.projectiles.push({
    kind: 'orb',
    owner: 'enemy',
    id: `o${state.nextId++}`,
    x: e.x + e.faceX * 8,
    y: e.y - 4 + e.faceY * 8,
    z: e.z,
    vx: e.faceX * k.shotSpeed,
    vy: e.faceY * k.shotSpeed,
    lifeMs: k.shotLifeMs,
    damage: k.damage,
  });
  state.events.push({ type: 'enemyShoot', tick: state.tick, x: e.x, y: e.y });
}

/** For the view: 0..1 how far into the wind-up (telegraph) the enemy is. @param {any} e */
export function windupProgress(e) {
  if (e.state !== 'windup') return 0;
  return Math.min(1, e.t / ENEMY_KINDS[/** @type {'beast' | 'archer'} */ (e.kind)].windupMs);
}

