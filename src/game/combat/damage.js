// @ts-check
// Damage rules (DESIGN.md 5.6; P3): perfect dodge, guard / perfect guard, invulnerability,
// knockback. Health is in quarter hearts for the player and plain points for enemies.
import { COMBAT, dodgeInvulnerable } from '../entities/playerCombat.js';
import { direction, fromFront } from './hitbox.js';

/**
 * @typedef {object} Hit
 * @property {'player' | 'enemy'} owner
 * @property {string} id         one hit per target per id
 * @property {number} damage
 * @property {{ x: number, y: number }} from  where the hit comes from (for guard direction / knockback)
 * @property {'melee' | 'projectile' | 'env'} kind  env = fire / electricity (cannot be guarded)
 * @property {number} [knock]  knockback strength (default 1)
 */

/**
 * Applies an enemy hit to the player.
 * @param {any} state @param {Hit} hit
 * @returns {'ignored' | 'justDodge' | 'dodged' | 'parried' | 'blocked' | 'hurt'}
 */
export function hitPlayer(state, hit) {
  const p = state.player;
  if (p.dead) return 'ignored';
  if (p.action === 'dodge' && p.actionMs <= COMBAT.justDodgeMs) {
    if (state.flurryMs <= 0) state.events.push({ type: 'justDodge', tick: state.tick });
    state.flurryMs = COMBAT.flurryMs;
    return 'justDodge';
  }
  if (dodgeInvulnerable(p)) return 'dodged';
  if (p.invulnMs > 0) return 'ignored';
  if (hit.kind !== 'env' && p.guarding && fromFront(p, { x: p.aimX, y: p.aimY }, hit.from)) {
    if (p.guardMs <= COMBAT.justGuardMs) {
      state.events.push({ type: 'parry', tick: state.tick, x: p.x, y: p.y });
      return 'parried';
    }
    knockback(p, hit.from, 0.4);
    state.events.push({ type: 'block', tick: state.tick, x: p.x, y: p.y });
    return 'blocked';
  }
  p.hp = Math.max(0, p.hp - hit.damage);
  p.invulnMs = COMBAT.hurtInvulnMs;
  knockback(p, hit.from, hit.knock ?? 1);
  state.events.push({ type: 'hurt', tick: state.tick, x: p.x, y: p.y });
  if (p.hp === 0) p.dead = true;
  return 'hurt';
}

/**
 * Applies a player hit to an enemy.
 * @param {any} state @param {any} e enemy @param {Hit} hit
 * @returns {boolean} whether it landed
 */
export function hitEnemy(state, e, hit) {
  if (e.state === 'dead' || e.lastHitId === hit.id) return false;
  e.lastHitId = hit.id;
  e.hp = Math.max(0, e.hp - hit.damage);
  const d = direction(e.x - hit.from.x, e.y - hit.from.y, { x: 0, y: 1 });
  const k = hit.knock ?? 1;
  e.knockX = d.x * COMBAT.knockbackSpeed * k;
  e.knockY = d.y * COMBAT.knockbackSpeed * k;
  e.knockMs = COMBAT.knockbackMs;
  state.events.push({ type: 'hitEnemy', tick: state.tick, x: e.x, y: e.y });
  if (e.hp === 0) {
    e.state = 'dead';
    e.t = 0;
    state.events.push({ type: 'enemyDown', tick: state.tick, x: e.x, y: e.y });
  } else {
    // Hits interrupt the enemy (including a wind-up): a short stagger.
    e.state = 'stun';
    e.t = 0;
    e.stunMs = 250;
  }
  return true;
}

/** @param {any} body @param {{ x: number, y: number }} from @param {number} strength */
function knockback(body, from, strength) {
  const d = direction(body.x - from.x, body.y - from.y, { x: 0, y: 1 });
  body.knockX = d.x * COMBAT.knockbackSpeed * strength;
  body.knockY = d.y * COMBAT.knockbackSpeed * strength;
  body.knockMs = COMBAT.knockbackMs;
}
