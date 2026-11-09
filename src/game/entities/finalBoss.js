// @ts-check
// 淀みの源 — the final boss (v1.0, C7; docs/story/V1_STORY_PROPOSAL.md, docs/enemy/ENEMY_BOSS_DESIGN.md 3.5).
// The great 星環 of the continent, turned inside out: a ring floating in its arena (the desert's
// strip of rooms, tools/gen_world.py), with four empty seats (座) around it.
//
// - It is NOT one of the four cores: it is kept apart from WORLD.bosses (WORLD.finalBoss) and from
//   progress.bosses, so 「澱の核 n/4」 and everything counting the cores stay as they are.
// - While the ring is inverted, nothing hurts it (sword, arrows, fire, electricity: hitFinalBoss).
// - Four seats wake with fire, light, weight and resonance (puzzles/switches.js, `seat: true`). The
//   source reads each seat's current state (state.switchActive) every step; a seat that has woken
//   stays awake until the next inversion wave. When all four are awake at once the ring turns back
//   for a moment: it staggers for 8 s and can be hit. One hit takes a third of its health (whatever
//   the weapon) and the ring inverts again at once (a wave), so three rounds purify it.
// - Attacks: the cores' fan of orbs, ring of orbs and slam, and the inversion wave: a shockwave
//   (jump over it). After a stagger it inverts the ring again and puts every seat out — the sconce
//   goes dark (unlightSconce), the crate slides back home, the stone falls silent. The waves it sends
//   every few attacks during the fight only put out the floor's seats (crate, stone).
// - Below half health, phase 2: shorter wind-ups (the cores' rule, PHASE2_WINDUP) and waves more often.
// - It is in play only while the player is in its arena (placeFinalBoss): a new game's enemy list is
//   unchanged.
// - Defeated: progress.flags.source_purified is set (saved), the event below is pushed, no star
//   shard or money. With that flag it never appears again (placeFinalBoss / applyProgress).
//
// HOOK for the ending (C10): when the source is purified, `settleFinalBoss` pushes ONE event
//   { type: 'sourcePurified', tick, id: 'source', name: '淀みの源' }
// onto state.events (the same list the view and main.js read every frame: toasts, sounds) and asks
// for a save (state.saveRequested). Listen for that event type; or read
// state.progress.flags.source_purified, which stays set for good.
// Other events: sourceAwake, seatOn {id}, sourceStagger, sourceGuard (a hit that did nothing),
// sourceWave, sourcePhase, sourceHit.
// Pure logic.
import { direction, overlaps } from '../combat/hitbox.js';
import { hitPlayer } from '../combat/damage.js';
import { unlightSconce } from '../puzzles/switches.js';
import { PHASE2_WINDUP, inArena } from './bosses.js';

/** @typedef {'volley' | 'ring' | 'slam' | 'wave'} FinalPattern */
/** @typedef {{ tx: number, ty: number, tw: number, th: number }} Rect */
/**
 * @typedef {object} FinalBossDef  (tools/gen_world.py, offset by world.js)
 * @property {string} id
 * @property {number} tx @property {number} ty  where it floats (its home)
 * @property {Rect} arena  it wakes while the player is in here
 * @property {Rect} roam   and floats only in here (out of reach of the weight seat)
 * @property {string[]} seats  the switch ids of its four seats
 * @property {{ tx: number, ty: number }} crate  where the weight seat's crate starts (the wave puts it back)
 * @property {{ tx: number, ty: number }[]} [grass]  the grass by the light seat (the wave makes it whole again)
 */

export const FINAL_BOSS = Object.freeze({
  name: '淀みの源',
  hp: 90,
  /** Hits (during a stagger) to purify it: each takes this fraction of its health. */
  hits: 3,
  radius: 18,
  speed: 16,
  damage: 3,
  idleMs: 700,
  windupMs: 900,
  waveWindupMs: 1400,
  recoverMs: 1000,
  /** All four seats awake: the ring turns back this long. */
  staggerMs: 8000,
  phase1: /** @type {FinalPattern[]} */ (['volley', 'slam', 'ring', 'volley', 'ring', 'slam', 'wave']),
  phase2: /** @type {FinalPattern[]} */ (['ring', 'volley', 'slam', 'ring', 'volley', 'wave']),
  volleyShots: 7,
  ringShots: 12,
  shotSpeed: 78,
  slamRadius: 44,
  waveRadius: 64,
  /** The purified ring fades out this long before it leaves the enemy list (its defeat frames). */
  defeatMs: 2400,
});

/** Its id in the enemy list (ordinary enemies count from 1, the cores from 1000). */
export const FINAL_BOSS_ENEMY_ID = 2000;

/** The flag that the defeat sets, and that keeps it gone. */
export const SOURCE_PURIFIED = 'source_purified';

/**
 * @param {FinalBossDef} def @param {any} map @param {number} id
 */
export function createFinalBoss(def, map, id) {
  const ts = map.tileSize;
  const x = def.tx * ts + ts / 2;
  const y = def.ty * ts + ts - 2;
  return {
    id,
    final: true,
    bossId: def.id,
    kind: 'boss_source',
    name: FINAL_BOSS.name,
    x,
    y,
    z: map.elev[def.ty * map.width + def.tx] ?? 0,
    prevX: x,
    prevY: y,
    homeX: x,
    homeY: y,
    halfWidth: 8,
    height: 8,
    r: FINAL_BOSS.radius,
    hp: FINAL_BOSS.hp,
    maxHp: FINAL_BOSS.hp,
    weak: null,
    arena: def.arena,
    roam: def.roam,
    seatIds: [...def.seats],
    crateHome: { ...def.crate },
    grass: (def.grass ?? []).map((g) => ({ ...g })),
    /** @type {Record<string, boolean>} seats awake now */
    seats: Object.fromEntries(def.seats.map((s) => [s, false])),
    state: 'idle',
    t: 0,
    awake: false,
    phase: 1,
    patternIndex: 0,
    pattern: /** @type {FinalPattern | null} */ (null),
    windupMs: FINAL_BOSS.windupMs,
    /** the coming wave inverts the ring again (puts out every seat), not only the floor's */
    fullWave: false,
    staggers: 0,
    /** its own clock (ms), and when the phase-2 change shows (the view's transform frames) */
    clock: 0,
    transformFrom: 0,
    transformUntil: 0,
    stunMs: 0,
    faceX: 0,
    faceY: 1,
    lastHitId: '',
    guardTick: -1000,
    attackSeq: 0,
    hitPlayerSeq: -1,
    knockX: 0,
    knockY: 0,
    knockMs: 0,
  };
}

/**
 * The source is in play only while the player is in its arena (and until it is purified): it is
 * placed when they step in, and dropped with the other enemies when they fall (spawnEnemies).
 * @param {any} state
 */
export function placeFinalBoss(state) {
  const def = state.finalBossDef;
  if (!def || state.progress.flags[SOURCE_PURIFIED] || state.player.dead) return;
  if (!inArena({ arena: def.arena }, state.map, state.player.x, state.player.y)) return;
  if (state.enemies.some((/** @type {any} */ e) => e.final)) return;
  state.enemies.push(createFinalBoss(def, state.map, FINAL_BOSS_ENEMY_ID));
}

/** @param {any} e @param {string} s */
function setState(e, s) {
  e.state = s;
  e.t = 0;
}

/** Wind-up of a pattern (phase 2: shorter). @param {any} e @param {FinalPattern} pattern */
function windupFor(e, pattern) {
  const base = pattern === 'wave' ? FINAL_BOSS.waveWindupMs : FINAL_BOSS.windupMs;
  return Math.round(base * (e.phase === 2 ? PHASE2_WINDUP : 1));
}

/** @param {any} e @param {FinalPattern} pattern @param {boolean} [full] a wave that inverts the ring again (after a stagger) */
function startPattern(e, pattern, full = false) {
  e.pattern = pattern;
  e.fullWave = full;
  e.windupMs = windupFor(e, pattern);
  setState(e, 'windup');
}

/** Whether all four seats are awake now. @param {any} e */
export function allSeatsAwake(e) {
  return e.seatIds.length > 0 && e.seatIds.every((/** @type {string} */ id) => e.seats[id]);
}

/**
 * One step of the source. `dt` is already scaled by slow motion.
 * @param {any} e @param {any} state @param {number} dt seconds
 */
export function updateFinalBoss(e, state, dt) {
  const ms = dt * 1000;
  e.prevX = e.x;
  e.prevY = e.y;
  e.t += ms;
  e.clock += ms;
  e.knockMs = 0; // it does not budge
  if (e.state === 'dead') return;
  const map = state.map;
  const p = state.player;
  const playerIn = !p.dead && inArena(e, map, p.x, p.y);
  if (!playerIn) {
    // Asleep (or the player left): it settles back home and waits.
    if (e.awake) e.awake = false;
    if (e.state !== 'idle') setState(e, 'idle');
    floatTo(e, map, e.homeX, e.homeY, dt);
    return;
  }
  if (!e.awake) {
    e.awake = true;
    // A fresh fight: every seat starts asleep (a saved lit sconce or moved crate is put back).
    resetSeats(state, e);
    setState(e, 'idle');
    state.events.push({ type: 'sourceAwake', tick: state.tick, id: e.bossId });
  }
  const toPlayer = direction(p.x - e.x, p.y - e.y, { x: e.faceX, y: e.faceY });

  // The seats: read what each one receives now; one that woke stays awake until the next wave.
  if (e.state !== 'stagger') {
    for (const id of e.seatIds) {
      if (state.switchActive[id] && !e.seats[id]) {
        e.seats[id] = true;
        state.events.push({ type: 'seatOn', tick: state.tick, id });
      }
    }
    // (Not while a wave is coming: it is about to put them out.)
    if (allSeatsAwake(e) && !(e.pattern === 'wave' && e.state === 'windup')) {
      e.staggers++;
      e.pattern = null;
      setState(e, 'stagger');
      state.events.push({ type: 'sourceStagger', tick: state.tick, id: e.bossId });
      return;
    }
  }

  switch (e.state) {
    case 'stagger':
      if (e.t >= FINAL_BOSS.staggerMs) startPattern(e, 'wave', true); // it inverts again
      break;
    case 'idle': {
      e.faceX = toPlayer.x;
      e.faceY = toPlayer.y;
      floatTo(e, map, p.x, p.y, dt);
      if (e.t >= FINAL_BOSS.idleMs) {
        const list = e.phase === 1 ? FINAL_BOSS.phase1 : FINAL_BOSS.phase2;
        startPattern(e, list[e.patternIndex % list.length]);
        e.patternIndex++;
      }
      break;
    }
    case 'windup':
      if (e.pattern === 'volley') {
        e.faceX = toPlayer.x;
        e.faceY = toPlayer.y;
      }
      if (e.t >= e.windupMs) {
        e.attackSeq++;
        if (e.pattern === 'volley') fan(e, state, FINAL_BOSS.volleyShots, 1.0);
        else if (e.pattern === 'ring') fan(e, state, FINAL_BOSS.ringShots, Math.PI * 2);
        else if (e.pattern === 'wave') {
          resetSeats(state, e, e.fullWave ? 'all' : 'ground');
          state.events.push({ type: 'sourceWave', tick: state.tick, id: e.bossId, full: !!e.fullWave });
        }
        setState(e, 'attack');
      }
      break;
    case 'attack': {
      // Slam and wave: a shockwave along the ground for a moment (jumping over it works).
      const r = e.pattern === 'slam' ? FINAL_BOSS.slamRadius : e.pattern === 'wave' ? FINAL_BOSS.waveRadius : 0;
      if (r > 0 && p.z - p.groundZ < 6) touch(e, state, r);
      if (r === 0 || e.t >= 250) setState(e, 'recover');
      break;
    }
    case 'recover':
      if (e.t >= FINAL_BOSS.recoverMs) setState(e, 'idle');
      break;
  }
}

/** Floats toward a point, never leaving its roaming rectangle. @param {any} e @param {any} map @param {number} x @param {number} y @param {number} dt */
function floatTo(e, map, x, y, dt) {
  const ts = map.tileSize;
  const r = e.roam;
  const tx = Math.max(r.tx * ts + ts / 2, Math.min((r.tx + r.tw) * ts - ts / 2, x));
  const ty = Math.max(r.ty * ts + ts / 2, Math.min((r.ty + r.th) * ts - 2, y));
  const dx = tx - e.x;
  const dy = ty - e.y;
  const d = Math.hypot(dx, dy);
  const step = FINAL_BOSS.speed * dt;
  if (d <= step) {
    e.x = tx;
    e.y = ty;
  } else {
    e.x += (dx / d) * step;
    e.y += (dy / d) * step;
  }
}

/** A shockwave touching the player hurts once per attack. @param {any} e @param {any} state @param {number} r */
function touch(e, state, r) {
  const p = state.player;
  if (e.hitPlayerSeq === e.attackSeq) return;
  if (!overlaps({ x: e.x, y: e.y, z: e.z, r }, { x: p.x, y: p.y - 3, z: p.z, r: 5 })) return;
  hitPlayer(state, { owner: 'enemy', id: `${e.bossId}-${e.attackSeq}`, damage: FINAL_BOSS.damage, from: { x: e.x, y: e.y }, kind: 'melee', knock: 1.4 });
  e.hitPlayerSeq = e.attackSeq;
}

/** Orbs spread around the facing (a full circle for a ring). @param {any} e @param {any} state @param {number} n @param {number} spread */
function fan(e, state, n, spread) {
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
      vx: Math.cos(a) * FINAL_BOSS.shotSpeed,
      vy: Math.sin(a) * FINAL_BOSS.shotSpeed,
      lifeMs: 2800,
      damage: Math.max(2, FINAL_BOSS.damage - 1),
    });
  }
  state.events.push({ type: 'enemyShoot', tick: state.tick, x: e.x, y: e.y });
}

/**
 * The inversion wave puts seats back to sleep.
 * - 'all' (the ring inverting again after a stagger, and when it wakes): every seat. The sconce is
 *   put out, the crate slides back to where it started, the stone falls silent, and the grass by the
 *   light seat is whole again (put out, no ash): burning it is the light seat's way without
 *   abilities, and ash would otherwise take two minutes to grow back. Only those grass tiles are
 *   touched (the fire / ash of a tile lives in the environment simulation, not in the saved world
 *   differences).
 * - 'ground' (the waves it sends during the fight): only the seats on the floor — the crate is
 *   pushed back and the stone falls silent; the flames (sconce, burning grass) hold. So waking the
 *   fire and light seats takes one fire arrow each per round (fair without abilities: QA B-3).
 * @param {any} state @param {any} e @param {'all' | 'ground'} [scope]
 */
export function resetSeats(state, e, scope = 'all') {
  const map = state.map;
  if (scope === 'ground') {
    for (const s of state.switches) {
      if (!e.seatIds.includes(s.id) || !(s.kind === 'plate' || s.kind === 'stone')) continue;
      e.seats[s.id] = false;
      delete state.switchUntil[s.id];
    }
    returnCrate(state, e.crateHome);
    return;
  }
  const env = state.env;
  for (const g of e.grass ?? []) {
    const i = g.ty * state.map.width + g.tx;
    const c = env.cells.get(i);
    if (!c) continue;
    if (env.burning.delete(i)) c.burnMs = 0;
    c.ashUntil = 0;
    env.version++;
  }
  for (const id of e.seatIds) e.seats[id] = false;
  for (const s of state.switches) {
    if (!e.seatIds.includes(s.id)) continue;
    const o = state.env.objectAt.get(s.ty * map.width + s.tx);
    if (o && o.type === 'sconce') unlightSconce(state, o);
    delete state.switchUntil[s.id];
  }
  returnCrate(state, e.crateHome);
}

/** Slides the crate that started at `home` back there (unless something is in the way). @param {any} state @param {{ tx: number, ty: number }} home */
function returnCrate(state, home) {
  const map = state.map;
  const env = state.env;
  const k = state.objectBaseline.findIndex((/** @type {any} */ b) => b.type === 'crate' && b.tx === home.tx && b.ty === home.ty);
  const o = k >= 0 ? map.objects[k] : null;
  if (!o || o.gone || (o.tx === home.tx && o.ty === home.ty)) return;
  const to = home.ty * map.width + home.tx;
  const p = state.player;
  const ts = map.tileSize;
  if (env.objectAt.has(to) || map.solid[to] || (Math.floor(p.x / ts) === home.tx && Math.floor(p.y / ts) === home.ty)) return;
  const from = o.ty * map.width + o.tx;
  env.objectAt.delete(from);
  map.solid[from] = 0;
  o.fromTx = o.tx;
  o.fromTy = o.ty;
  o.movedAt = env.now;
  o.tx = home.tx;
  o.ty = home.ty;
  env.objectAt.set(to, o);
  map.solid[to] = 1;
  env.version++;
  state.events.push({ type: 'crateMoved', tick: state.tick });
}

/**
 * A player's hit on the source (from combat/damage.js hitEnemy). Inverted: nothing. Staggered: a
 * third of its health, and it inverts again.
 * @param {any} state @param {any} e @param {{ id: string, from: { x: number, y: number } }} hit
 * @returns {boolean} whether it landed
 */
export function hitFinalBoss(state, e, hit) {
  if (e.state === 'dead' || e.lastHitId === hit.id) return false;
  e.lastHitId = hit.id;
  if (e.state !== 'stagger') {
    // (One notice per half second of hammering at it.)
    if (state.tick - e.guardTick > 30) state.events.push({ type: 'sourceGuard', tick: state.tick, x: e.x, y: e.y });
    e.guardTick = state.tick;
    return false;
  }
  const third = Math.ceil(e.maxHp / FINAL_BOSS.hits);
  e.hp = Math.max(0, e.hp - third);
  state.events.push({ type: 'hitEnemy', tick: state.tick, x: e.x, y: e.y });
  state.events.push({ type: 'sourceHit', tick: state.tick, id: e.bossId, hp: e.hp });
  if (e.hp === 0) {
    e.state = 'dead';
    e.t = 0;
    e.awake = false;
    state.events.push({ type: 'enemyDown', tick: state.tick, x: e.x, y: e.y });
    return true;
  }
  if (e.phase === 1 && e.hp <= e.maxHp / 2) {
    e.phase = 2;
    e.patternIndex = 0;
    e.transformFrom = e.clock;
    e.transformUntil = e.clock + 1000;
    state.events.push({ type: 'sourcePhase', tick: state.tick, id: e.bossId });
  }
  startPattern(e, 'wave', true); // the ring flips back over
  return true;
}

/**
 * The purified source is remembered (a flag, saved) and announced once — the hook for the ending.
 * @param {any} state
 */
export function settleFinalBoss(state) {
  const flags = state.progress.flags;
  for (const e of state.enemies) {
    if (!e.final || e.state !== 'dead' || flags[SOURCE_PURIFIED]) continue;
    flags[SOURCE_PURIFIED] = true;
    state.events.push({ type: 'sourcePurified', tick: state.tick, id: e.bossId, name: e.name });
    state.saveRequested = true;
  }
}

/** The source as the player fights it (awake, alive), if any. @param {any} state */
export function activeFinalBoss(state) {
  return state.enemies.find((/** @type {any} */ e) => e.final && e.awake && e.state !== 'dead') ?? null;
}
