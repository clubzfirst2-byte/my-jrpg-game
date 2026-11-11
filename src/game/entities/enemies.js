// @ts-check
// Enemy types (P3, DESIGN.md 5.6; v1.0 docs/enemy/ENEMY_BOSS_DESIGN.md 2章). Every attack is
// telegraphed (a visible wind-up) so a perfect dodge / guard is readable.
//   beast     melee: closes in, winds up, lunges
//   archer    ranged: keeps its distance, winds up, shoots a murk orb
//   slime     澱だまり (v1.0): hops toward the player (moves only while in the air), squashes, body-slams. Weak, many
//   sentinel  遺跡の番兵 (v1.0): slow stone-and-bronze machine; raises its fist and slams the ground (a small
//             shockwave around it, jumpable). Swords glance off it (half damage), small hits do not
//             stagger it, electricity does double damage and stuns it.
import { moveAndCollide, groundHeightUnder } from '../physics/collision.js';
import { waterSurfaceUnder } from './swimming.js';
import { Ground } from '../world/tilemap.js';
import { direction, overlaps } from '../combat/hitbox.js';
import { hitPlayer } from '../combat/damage.js';
import { updateBoss, bossWindup } from './bosses.js';
import { updateFinalBoss } from './finalBoss.js';
import { onScreen } from '../core/viewRect.js';

/** @typedef {'beast' | 'archer' | 'slime' | 'sentinel'} EnemyKind */

export const ENEMY_KINDS = Object.freeze({
  beast: {
    attack: 'lunge',
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
    attack: 'shoot',
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
  // 澱だまり: a hop is `hopMs` long, in the air (moving) for the first `hopAirMs` of it.
  slime: {
    attack: 'lunge',
    hp: 6,
    speed: 40,
    sightRange: 88,
    attackRange: 18,
    windupMs: 450,
    activeMs: 180,
    recoveryMs: 650,
    lungeSpeed: 130,
    damage: 1,
    radius: 5,
    hopMs: 600,
    hopAirMs: 280,
  },
  // 遺跡の番兵: the slam is a ring of `slamRadius` around its feet for `activeMs`.
  sentinel: {
    attack: 'slam',
    hp: 20,
    speed: 16,
    sightRange: 80,
    attackRange: 26,
    windupMs: 900,
    activeMs: 200,
    recoveryMs: 1100,
    slamRadius: 28,
    damage: 3,
    radius: 7,
    /** sword (melee) hits do this fraction of their damage */
    armor: 0.5,
    /** the element that does double damage (and staggers it) */
    weak: 'shock',
    /** small hits do not stagger it; knockback barely moves it */
    heavy: true,
  },
});

/** Stunned after a parry (perfect guard) for this long. */
export const PARRY_STUN_MS = 1200;
const HALF_WIDTH = 5;
const HEIGHT = 6;
const STEP = 8;

/**
 * @param {EnemyKind} kind @param {number} x @param {number} y @param {number} z @param {number} id
 */
export function createEnemy(kind, x, y, z, id) {
  const k = /** @type {any} */ (ENEMY_KINDS[kind]);
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
    hitPlayerSeq: -1,
    knockX: 0,
    knockY: 0,
    knockMs: 0,
    wanderMs: 0,
    wanderX: 0,
    wanderY: 0,
    // v1.0: the slime's hop clock (each starts at its own point, so a group does not hop in step),
    // and what hits do to it (damage.js reads these).
    hopMs: k.hopMs ? (id * 137) % k.hopMs : 0,
    /** ms since its last shot (the view holds the shot pose for a moment) */
    sinceShotMs: 1e9,
    weak: k.weak ?? null,
    armor: k.armor ?? 1,
    heavy: !!k.heavy,
  };
}

/**
 * How fast the enemy covers ground right now, as a multiple of its speed. A slime moves only while
 * it is in the air (faster then, so its average matches its speed); the others walk steadily.
 * @param {any} e @param {any} k
 */
export function strideFactor(e, k) {
  if (!k.hopMs) return 1;
  return e.hopMs < k.hopAirMs ? k.hopMs / k.hopAirMs : 0;
}

/**
 * One AI step. `dt` is already scaled by slow motion.
 * @param {any} e @param {any} state @param {number} dt seconds
 */
export function updateEnemy(e, state, dt) {
  if (e.boss) return updateBoss(e, state, dt); // P10.4
  if (e.final) return updateFinalBoss(e, state, dt); // v1.0: 淀みの源
  const ms = dt * 1000;
  e.prevX = e.x;
  e.prevY = e.y;
  e.t += ms;
  if (e.state === 'dead') return;
  const k = /** @type {any} */ (ENEMY_KINDS[/** @type {EnemyKind} */ (e.kind)]);
  if (k.hopMs) e.hopMs = (e.hopMs + ms) % k.hopMs;
  e.sinceShotMs += ms;
  const p = state.player;
  const dx = p.x - e.x;
  const dy = p.y - e.y;
  const dist = Math.hypot(dx, dy);
  // graphics v3 (?v3=1, the narrow view): an enemy off screen does not see the hero, so it never
  // aims or shoots from out of sight (state.viewRect; absent otherwise: unchanged)
  const sees = !p.dead && dist < k.sightRange && Math.abs(p.z - e.z) < 24 && !p.swimming && onScreen(e, state.viewRect);
  const toPlayer = direction(dx, dy, { x: e.faceX, y: e.faceY });

  // Knockback slides the enemy regardless of state (a heavy one barely moves).
  if (e.knockMs > 0) {
    e.knockMs -= ms;
    const kb = e.heavy ? 0.3 : 1;
    walk(e, state.map, e.knockX * dt * kb, e.knockY * dt * kb);
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
      if (k.attack === 'shoot') {
        e.cooldownMs = Math.max(0, e.cooldownMs - ms);
        if (dist < k.keepMin) walk(e, state.map, -toPlayer.x * k.speed * dt, -toPlayer.y * k.speed * dt);
        else if (dist > k.keepMax) walk(e, state.map, toPlayer.x * k.speed * dt, toPlayer.y * k.speed * dt);
        if (e.cooldownMs <= 0) setState(e, 'windup');
      } else if (dist <= k.attackRange && (!k.hopMs || strideFactor(e, k) === 0)) {
        // In reach: wind up (a slime first lands, then squashes).
        setState(e, 'windup');
      } else {
        const v = k.speed * strideFactor(e, k) * dt;
        walk(e, state.map, toPlayer.x * v, toPlayer.y * v);
      }
      break;
    case 'windup':
      // A lunge aims until it goes; a slam is committed where it stands.
      if (k.attack !== 'slam') {
        e.faceX = toPlayer.x;
        e.faceY = toPlayer.y;
      }
      if (e.t >= k.windupMs) {
        if (k.attack === 'shoot') {
          // graphics v3: an archer that has gone off screen while drawing lets the shot go (aims again once seen)
          if (onScreen(e, state.viewRect)) {
            shoot(e, state, k);
            e.cooldownMs = k.cooldownMs;
          }
          setState(e, 'idle');
        } else {
          e.attackSeq += 1;
          setState(e, 'attack');
          if (k.attack === 'slam') state.events.push({ type: 'enemySlam', tick: state.tick, x: e.x, y: e.y });
        }
      }
      break;
    case 'attack':
      if (k.attack === 'slam') {
        // The shockwave hugs the ground: jumping over it works (like a core's slam).
        if (p.z - p.groundZ < 6) strike(e, state, k, { x: e.x, y: e.y, z: e.z, r: k.slamRadius });
      } else {
        // Lunge / body slam: a hitbox on its body while it moves.
        walk(e, state.map, e.faceX * k.lungeSpeed * dt, e.faceY * k.lungeSpeed * dt);
        strike(e, state, k, { x: e.x + e.faceX * 6, y: e.y - 3 + e.faceY * 6, z: e.z, r: 8 });
      }
      if (e.state === 'attack' && e.t >= k.activeMs) setState(e, 'recover');
      break;
    case 'recover':
      if (e.t >= k.recoveryMs) setState(e, 'idle');
      break;
  }
}

/**
 * An attack's hitbox touching the player hurts them once per attack; a parry stuns the enemy.
 * @param {any} e @param {any} state @param {any} k @param {{ x: number, y: number, z: number, r: number }} hit
 */
function strike(e, state, k, hit) {
  const p = state.player;
  if (e.hitPlayerSeq === e.attackSeq || !overlaps(hit, { x: p.x, y: p.y - 3, z: p.z, r: 5 })) return;
  const result = hitPlayer(state, { owner: 'enemy', id: `e${e.id}-${e.attackSeq}`, damage: k.damage, from: { x: e.x, y: e.y }, kind: 'melee' });
  // Any contact uses up this attack: a dodged or blocked attack must not land later in the same one.
  e.hitPlayerSeq = e.attackSeq;
  if (result === 'parried') {
    e.stunMs = PARRY_STUN_MS;
    setState(e, 'stun');
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
  const pit = map.ground[Math.floor(e.y / map.tileSize) * map.width + Math.floor(e.x / map.tileSize)] === Ground.PIT;
  if (pit || waterSurfaceUnder(map, e) !== null || ground < e.z - STEP) {
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
  const v = k.speed * 0.4 * strideFactor(e, k) * dt;
  walk(e, map, e.wanderX * v, e.wanderY * v);
}

/** @param {any} e @param {any} state @param {any} k */
function shoot(e, state, k) {
  e.sinceShotMs = 0;
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
  if (e.boss || e.final) return bossWindup(e);
  if (e.state !== 'windup') return 0;
  return Math.min(1, e.t / ENEMY_KINDS[/** @type {EnemyKind} */ (e.kind)].windupMs);
}

