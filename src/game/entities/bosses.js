// @ts-check
// Bosses (P10.4, DESIGN.md 5.6): the four 澱の核 (cores of the murk), one in each wild region.
// A boss waits in its arena, wakes when the player steps in, and cycles through its attack
// patterns. Every attack is telegraphed (a wind-up), so a perfect dodge / guard is always
// possible. Below half health it enters its second phase: shorter wind-ups and a fiercer pattern
// list. A boss shrugs off small hits (no stagger) but a parry stuns it. Some cores burn: fire does
// double damage. Defeating one purifies it for good (saved) and gives a star shard.
//
// Patterns:
//   charge  wind up facing the player, then dash in a straight line (a body hitbox)
//   slam    wind up, then a shockwave around the boss (radius) — jump or dodge through it
//   volley  wind up, then a fan of orbs toward the player
//   ring    wind up, then orbs in every direction
// Pure logic.
import { moveAndCollide, groundHeightUnder } from '../physics/collision.js';
import { direction, overlaps } from '../combat/hitbox.js';
import { hitPlayer } from '../combat/damage.js';
import { addItem } from '../items/inventory.js';

/** Stunned after a parry for this long. */
export const BOSS_PARRY_STUN_MS = 1600;

/**
 * @typedef {'charge' | 'slam' | 'volley' | 'ring'} Pattern
 * @typedef {{ name: string, hp: number, speed: number, radius: number, weak: 'fire' | null,
 *   damage: number, windupMs: number, recoverMs: number, phase1: Pattern[], phase2: Pattern[],
 *   chargeSpeed: number, chargeMs: number, slamRadius: number, shots: number, shotSpeed: number }} BossKind
 */

/** @type {Record<string, BossKind>} */
export const BOSS_KINDS = {
  // 囁きの森: an old root-thing that rams and stamps. Wood: it burns.
  root: {
    name: '朽ち根のヌシ',
    hp: 60,
    speed: 30,
    radius: 12,
    weak: 'fire',
    damage: 3,
    windupMs: 800,
    recoverMs: 900,
    phase1: ['charge', 'slam'],
    phase2: ['charge', 'slam', 'charge', 'volley'],
    chargeSpeed: 190,
    chargeMs: 600,
    slamRadius: 40,
    shots: 3,
    shotSpeed: 80,
  },
  // 白嶺山脈: horned frost that shakes the ground and throws ice in all directions. Ice: fire melts it.
  frost: {
    name: '凍て角のヌシ',
    hp: 70,
    speed: 26,
    radius: 12,
    weak: 'fire',
    damage: 3,
    windupMs: 850,
    recoverMs: 900,
    phase1: ['slam', 'ring'],
    phase2: ['ring', 'slam', 'ring', 'charge'],
    chargeSpeed: 170,
    chargeMs: 550,
    slamRadius: 48,
    shots: 8,
    shotSpeed: 70,
  },
  // 赤砂の荒野: a sand-wraith that shoots fans of grit and dashes.
  sand: {
    name: '砂嵐のヌシ',
    hp: 70,
    speed: 38,
    radius: 11,
    weak: null,
    damage: 3,
    windupMs: 700,
    recoverMs: 800,
    phase1: ['volley', 'charge'],
    phase2: ['volley', 'ring', 'charge', 'volley'],
    chargeSpeed: 210,
    chargeMs: 500,
    slamRadius: 40,
    shots: 5,
    shotSpeed: 95,
  },
  // 鏡湖と群島: a storm-eel that fills the air with sparks.
  storm: {
    name: '雷鳴のヌシ',
    hp: 60,
    speed: 34,
    radius: 11,
    weak: null,
    damage: 3,
    windupMs: 750,
    recoverMs: 850,
    phase1: ['ring', 'volley'],
    phase2: ['ring', 'volley', 'ring', 'slam'],
    chargeSpeed: 180,
    chargeMs: 500,
    slamRadius: 44,
    shots: 10,
    shotSpeed: 75,
  },
};

/** Phase 2: wind-ups this much shorter. */
export const PHASE2_WINDUP = 0.7;
/** What purifying a core gives. */
export const BOSS_REWARD = { money: 200, item: 'star_shard' };

/**
 * @typedef {{ id: string, kind: string, tx: number, ty: number, arena: { tx: number, ty: number, tw: number, th: number } }} BossDef
 */

/**
 * A boss in the enemy list (so sword / arrow / fire hits reach it like any enemy).
 * @param {BossDef} def @param {any} map @param {number} id
 */
export function createBoss(def, map, id) {
  const k = BOSS_KINDS[def.kind];
  const ts = map.tileSize;
  const x = def.tx * ts + ts / 2;
  const y = def.ty * ts + ts - 2;
  const half = 8;
  const z = groundHeightUnder({ x, y, halfWidth: half, height: 8 }, map);
  return {
    id,
    boss: true,
    bossId: def.id,
    kind: `boss_${def.kind}`,
    bossKind: def.kind,
    name: k.name,
    x,
    y,
    z,
    prevX: x,
    prevY: y,
    homeX: x,
    homeY: y,
    halfWidth: half,
    height: 8,
    r: k.radius,
    hp: k.hp,
    maxHp: k.hp,
    weak: k.weak,
    arena: def.arena,
    state: 'idle',
    t: 0,
    awake: false,
    /** back at its place and calm: the next wake is a new one (announced); stepping out and back in
     *  during a fight is not (final QA B-5) */
    settled: true,
    phase: 1,
    patternIndex: 0,
    pattern: /** @type {Pattern | null} */ (null),
    windupMs: k.windupMs,
    stunMs: 0,
    faceX: 0,
    faceY: 1,
    lastHitId: '',
    attackSeq: 0,
    hitPlayerSeq: -1,
    knockX: 0,
    knockY: 0,
    knockMs: 0,
  };
}

/** Whether a point (px) is inside a boss's arena. @param {any} e @param {any} map @param {number} x @param {number} y */
export function inArena(e, map, x, y) {
  const ts = map.tileSize;
  const a = e.arena;
  return x >= a.tx * ts && x < (a.tx + a.tw) * ts && y >= a.ty * ts && y < (a.ty + a.th) * ts;
}

/** @param {any} e @param {string} s */
function setState(e, s) {
  e.state = s;
  e.t = 0;
}

/** Moves inside the arena only. @param {any} e @param {any} map @param {number} dx @param {number} dy */
function move(e, map, dx, dy) {
  const before = { x: e.x, y: e.y };
  moveAndCollide(e, map, dx, dy, e.z + 8);
  if (!inArena(e, map, e.x, e.y) || Math.abs(groundHeightUnder(e, map) - e.z) > 8) {
    e.x = before.x;
    e.y = before.y;
    return false;
  }
  return true;
}

/**
 * One step of a boss. `dt` is already scaled by slow motion.
 * @param {any} e @param {any} state @param {number} dt seconds
 */
export function updateBoss(e, state, dt) {
  const ms = dt * 1000;
  e.prevX = e.x;
  e.prevY = e.y;
  e.t += ms;
  if (e.state === 'dead') return;
  const k = BOSS_KINDS[e.bossKind];
  const map = state.map;
  const p = state.player;
  const playerIn = !p.dead && inArena(e, map, p.x, p.y) && Math.abs(p.z - e.z) < 40;
  if (e.knockMs > 0) {
    e.knockMs -= ms;
    move(e, map, e.knockX * dt * 0.3, e.knockY * dt * 0.3); // heavy: barely pushed
  }
  // Phase 2 below half health.
  if (e.phase === 1 && e.hp <= e.maxHp / 2) {
    e.phase = 2;
    e.patternIndex = 0;
    e.windupMs = Math.round(k.windupMs * PHASE2_WINDUP);
    state.events.push({ type: 'bossPhase', tick: state.tick, id: e.bossId });
  }
  if (playerIn && !e.awake) {
    e.awake = true;
    // Announced once per wake: not again for the player stepping out and back in mid-fight.
    if (e.settled) state.events.push({ type: 'bossAwake', tick: state.tick, id: e.bossId });
    e.settled = false;
  }
  if (!playerIn) {
    // The player left: the core settles back at its place (no chasing across the region).
    e.awake = false;
    if (e.state !== 'stun') setState(e, 'idle');
    const home = direction(e.homeX - e.x, e.homeY - e.y, { x: 0, y: 1 });
    if (Math.hypot(e.homeX - e.x, e.homeY - e.y) > 2) move(e, map, home.x * k.speed * dt, home.y * k.speed * dt);
    else e.settled = true; // home again: asleep until the next wake
    return;
  }
  const dx = p.x - e.x;
  const dy = p.y - e.y;
  const dist = Math.hypot(dx, dy);
  const toPlayer = direction(dx, dy, { x: e.faceX, y: e.faceY });

  switch (e.state) {
    case 'stun':
      if (e.t >= e.stunMs) setState(e, 'idle');
      break;
    case 'idle':
      e.faceX = toPlayer.x;
      e.faceY = toPlayer.y;
      // Close in a little, then start the next pattern.
      if (dist > 48) move(e, map, toPlayer.x * k.speed * dt, toPlayer.y * k.speed * dt);
      if (e.t >= 500) {
        const list = e.phase === 1 ? k.phase1 : k.phase2;
        e.pattern = list[e.patternIndex % list.length];
        e.patternIndex++;
        setState(e, 'windup');
      }
      break;
    case 'windup':
      // A charge aims until it goes; the rest are committed where they stand.
      if (e.pattern === 'charge' || e.pattern === 'volley') {
        e.faceX = toPlayer.x;
        e.faceY = toPlayer.y;
      }
      if (e.t >= e.windupMs) {
        e.attackSeq++;
        if (e.pattern === 'volley') fan(e, state, k, k.shots, 0.9);
        else if (e.pattern === 'ring') fan(e, state, k, k.shots, Math.PI * 2);
        setState(e, 'attack');
      }
      break;
    case 'attack':
      if (e.pattern === 'charge') {
        const moved = move(e, map, e.faceX * k.chargeSpeed * dt, e.faceY * k.chargeSpeed * dt);
        touch(e, state, k, { x: e.x, y: e.y - 4, z: e.z, r: e.r });
        if (!moved || e.t >= k.chargeMs) setState(e, 'recover');
      } else if (e.pattern === 'slam') {
        // The shockwave is out for a moment; jumping over it works (it hugs the ground).
        if (p.z - p.groundZ < 6) touch(e, state, k, { x: e.x, y: e.y, z: e.z, r: k.slamRadius });
        if (e.t >= 200) setState(e, 'recover');
      } else {
        setState(e, 'recover');
      }
      break;
    case 'recover':
      if (e.t >= k.recoverMs) setState(e, 'idle');
      break;
  }
}

/** A hitbox touching the player hurts them once per attack. @param {any} e @param {any} state @param {BossKind} k @param {{ x: number, y: number, z: number, r: number }} hit */
function touch(e, state, k, hit) {
  const p = state.player;
  if (e.hitPlayerSeq === e.attackSeq) return;
  if (!overlaps(hit, { x: p.x, y: p.y - 3, z: p.z, r: 5 })) return;
  const r = hitPlayer(state, { owner: 'enemy', id: `${e.bossId}-${e.attackSeq}`, damage: k.damage, from: { x: e.x, y: e.y }, kind: 'melee', knock: 1.4 });
  e.hitPlayerSeq = e.attackSeq;
  if (r === 'parried') {
    e.stunMs = BOSS_PARRY_STUN_MS;
    setState(e, 'stun');
    state.events.push({ type: 'bossStun', tick: state.tick, id: e.bossId });
  }
}

/** Orbs spread over `spread` radians around the facing (a full circle for a ring). @param {any} e @param {any} state @param {BossKind} k @param {number} n @param {number} spread */
function fan(e, state, k, n, spread) {
  const base = Math.atan2(e.faceY, e.faceX);
  const full = spread >= Math.PI * 2 - 1e-6;
  for (let i = 0; i < n; i++) {
    const a = full ? base + (i / n) * Math.PI * 2 : base + (n === 1 ? 0 : (i / (n - 1) - 0.5) * spread);
    state.projectiles.push({
      kind: 'orb',
      owner: 'enemy',
      id: `${e.bossId}o${state.nextId++}`,
      x: e.x + Math.cos(a) * (e.r + 2),
      y: e.y - 6 + Math.sin(a) * (e.r + 2),
      z: e.z,
      vx: Math.cos(a) * k.shotSpeed,
      vy: Math.sin(a) * k.shotSpeed,
      lifeMs: 2600,
      damage: Math.max(2, k.damage - 1),
    });
  }
  state.events.push({ type: 'enemyShoot', tick: state.tick, x: e.x, y: e.y });
}

/** For the view: 0..1 into the wind-up. @param {any} e */
export function bossWindup(e) {
  return e.state === 'windup' ? Math.min(1, e.t / e.windupMs) : 0;
}

/**
 * A defeated core is purified for good: remembered in the progress, and it gives its reward once.
 * @param {any} state
 */
export function settleBosses(state) {
  for (const e of state.enemies) {
    if (!e.boss || e.state !== 'dead' || state.progress.bosses.includes(e.bossId)) continue;
    state.progress.bosses.push(e.bossId);
    state.progress.inv.money += BOSS_REWARD.money;
    addItem(state.progress.inv, BOSS_REWARD.item, 1);
    state.events.push({ type: 'bossDown', tick: state.tick, id: e.bossId, name: e.name, count: state.progress.bosses.length });
    state.saveRequested = true;
  }
}

/** The boss the player is fighting now (awake, alive), if any (v1.0: the source too). @param {any} state */
export function activeBoss(state) {
  return state.enemies.find((/** @type {any} */ e) => (e.boss || e.final) && e.awake && e.state !== 'dead') ?? null;
}
