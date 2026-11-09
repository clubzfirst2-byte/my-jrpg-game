// @ts-check
// Damage rules (DESIGN.md 5.6; P3): perfect dodge, guard / perfect guard, invulnerability,
// knockback. Health is in quarter hearts for the player and plain points for enemies.
import { COMBAT, dodgeInvulnerable } from '../entities/playerCombat.js';
import { direction, fromFront } from './hitbox.js';
import { hitFinalBoss } from '../entities/finalBoss.js';

/**
 * @typedef {object} Hit
 * @property {'player' | 'enemy'} owner
 * @property {string} id         one hit per target per id
 * @property {number} damage
 * @property {{ x: number, y: number }} from  where the hit comes from (for guard direction / knockback)
 * @property {'melee' | 'projectile' | 'env'} kind  env = fire / electricity (cannot be guarded)
 * @property {number} [knock]  knockback strength (default 1)
 * @property {'fire' | 'shock'} [element]  P6: fire / electricity (armor traits and buffs can stop them)
 */

/** P11.3: how hard hits land, by difficulty (quarter hearts are rounded, never below 1). */
export const DIFFICULTY = Object.freeze({ easy: 0.5, normal: 1, hard: 1.5 });

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
  // P6: protective gear and dishes.
  if ((hit.element === 'fire' && p.fireproof) || (hit.element === 'shock' && p.shockproof)) return 'ignored';
  if (hit.kind !== 'env' && p.guarding && fromFront(p, { x: p.aimX, y: p.aimY }, hit.from)) {
    if (p.guardMs <= COMBAT.justGuardMs) {
      state.events.push({ type: 'parry', tick: state.tick, x: p.x, y: p.y });
      return 'parried';
    }
    knockback(p, hit.from, 0.4);
    state.events.push({ type: 'block', tick: state.tick, x: p.x, y: p.y });
    return 'blocked';
  }
  // Armor: half its defense (rounded down) off every hit, one more with a defense dish; never below 1.
  const cut = Math.floor((p.defense ?? 0) / 2) + (p.defenseUp ? 1 : 0);
  const scaled = Math.max(1, Math.round(hit.damage * (DIFFICULTY[/** @type {'normal'} */ (state.difficulty)] ?? 1)));
  p.hp = Math.max(0, p.hp - Math.max(1, scaled - cut));
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
  if (e.final) return hitFinalBoss(state, e, hit); // v1.0: only a staggered source can be hurt
  if (e.state === 'dead' || e.lastHitId === hit.id) return false;
  e.lastHitId = hit.id;
  // P10.4: a core that burns takes double damage from fire.
  const damage = e.weak && hit.element === e.weak ? hit.damage * 2 : hit.damage;
  e.hp = Math.max(0, e.hp - damage);
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
  } else if (!e.boss) {
    // Hits interrupt the enemy (including a wind-up): a short stagger. (Bosses do not flinch.)
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
