// @ts-check
// Environment simulation (P4, DESIGN.md 4): fire spreading, burning out, ash regrowing, wet cells.
//
// - Active cells only: the burning cells are the only ones computed (10 Hz), at most
//   ENV.maxCellsPerTick per tick (the rest wait for the next tick, round-robin).
// - Sparse state: only cells that differ from the map (burning / wet / ash) are stored.
// - Regions far from the player are FROZEN: nothing is computed there, their clock stops.
//   When the player comes near again, the region is fast-forwarded from its clock to now in
//   coarse 1 s steps (DESIGN.md 4.4), a limited amount of work per game step.
// - Every random decision is a hash of (seed, cell, time), so the result does not depend on the
//   order cells are processed or on how the fast-forward is split across frames: the same history
//   gives the same island.
// Pure logic: no DOM, no PixiJS.
import { Ground } from '../world/tilemap.js';

export const ENV = Object.freeze({
  tickMs: 100,
  maxCellsPerTick: 512,
  regionTiles: 16,
  /** Regions within this many regions of the player's are simulated; the rest are frozen. */
  awakeRadius: 1,
  /** Coarse step of the fast-forward. */
  stepMs: 1000,
  /** Longer absences are fast-forwarded only over their last 10 minutes (fires are long out by then). */
  maxCatchUpMs: 600_000,
  /** Burning-cell steps of fast-forward per game step (keeps it to about 1-2 ms). */
  catchUpBudget: 3000,
  /** Chance per tick that a burning cell sets one flammable neighbour alight. */
  spreadChance: 0.1,
  wetMs: 20_000,
  regrowMs: 120_000,
  /** Burn time (ms) by material. */
  fuel: /** @type {Record<string, number>} */ ({ grass: 3000, tree: 12000, bramble: 2000 }),
});

const FLAMMABLE = new Set(['grass', 'tree', 'bramble']);
/** Objects that block movement while they exist. */
export const SOLID_OBJECTS = new Set(['tree', 'rock', 'bramble', 'crystal', 'jar', 'receiver', 'door', 'brazier', 'campfire']);

/**
 * @typedef {{ burnMs: number, at: number, wetUntil: number, ashUntil: number }} Cell
 *   burnMs > 0 while burning; `at` = the time burnMs refers to (fast-forward bookkeeping)
 * @typedef {{ type: string, tx: number, ty: number, gone?: boolean, link?: string, hp?: number, on?: boolean, cooldownUntil?: number }} EnvObject
 *
 * @typedef {object} Env
 * @property {number} seed
 * @property {number} now        game time (ms)
 * @property {number} nextTickMs
 * @property {Map<number, Cell>} cells
 * @property {Set<number>} burning
 * @property {number} rw @property {number} rh  regions across / down
 * @property {Float64Array} clock  per region: time it is simulated up to
 * @property {Uint8Array} awake    per region
 * @property {Uint8Array} pending  per region: waiting for / in a fast-forward
 * @property {{ regions: number[], T: number, end: number }[]} jobs
 * @property {Set<number>} heldIgnitions  ignitions across the border of a fast-forward, applied when it ends
 * @property {Map<number, EnvObject>} objectAt
 * @property {number} version      bumps whenever something visible changes
 * @property {number} cursor       round-robin position for the per-tick cap
 * @property {{ lastTickCells: number, maxTickCells: number, deferred: number, catchUpSteps: number, catchUpCells: number }} stats
 * @property {{ cells: number[], untilMs: number } | null} sparks
 * @property {Map<number, string>} lastHit  tile -> last sword swing id that hit it
 */

/**
 * @param {import('../world/tilemap.js').TileMap} map
 * @param {EnvObject[]} objects  every object on the map (trees, rocks, crystals, ...)
 * @param {number} [seed]
 * @returns {Env}
 */
export function createEnv(map, objects, seed = 1) {
  const rw = Math.ceil(map.width / ENV.regionTiles);
  const rh = Math.ceil(map.height / ENV.regionTiles);
  /** @type {Map<number, EnvObject>} */
  const objectAt = new Map();
  for (const o of objects) objectAt.set(o.ty * map.width + o.tx, o);
  return {
    seed,
    now: 0,
    nextTickMs: ENV.tickMs,
    cells: new Map(),
    burning: new Set(),
    rw,
    rh,
    clock: new Float64Array(rw * rh),
    awake: new Uint8Array(rw * rh),
    pending: new Uint8Array(rw * rh),
    jobs: [],
    heldIgnitions: new Set(),
    objectAt,
    version: 0,
    cursor: 0,
    stats: { lastTickCells: 0, maxTickCells: 0, deferred: 0, catchUpSteps: 0, catchUpCells: 0 },
    sparks: null,
    lastHit: new Map(),
  };
}

/** Deterministic number in [0, 1) from integers. */
export function roll(/** @type {number} */ seed, /** @type {number} */ a, /** @type {number} */ b, /** @type {number} */ c) {
  let h = Math.imul(seed ^ 0x9e3779b9, 0x85ebca6b) >>> 0;
  for (const v of [a, b, c]) {
    h = Math.imul(h ^ (v | 0), 0xcc9e2d51) >>> 0;
    h = ((h << 15) | (h >>> 17)) >>> 0;
    h = Math.imul(h, 0x1b873593) >>> 0;
  }
  h ^= h >>> 16;
  h = Math.imul(h, 0x85ebca6b) >>> 0;
  h ^= h >>> 13;
  return (h >>> 0) / 4294967296;
}

/** @param {Env} env @param {any} map @param {number} i */
export function regionOf(env, map, i) {
  const tx = i % map.width;
  const ty = (i / map.width) | 0;
  return ((ty / ENV.regionTiles) | 0) * env.rw + ((tx / ENV.regionTiles) | 0);
}

/**
 * What a tile is made of, for the rules.
 * @param {Env} env @param {any} map @param {number} i @param {number} [t] time (for ash regrowth)
 * @returns {string} grass | tree | bramble | water | metal | stump | rock | crystal | ... | none
 */
export function material(env, map, i, t = env.now) {
  const o = env.objectAt.get(i);
  if (o && !o.gone) return o.type;
  const g = map.ground[i];
  if (g === Ground.WATER) return 'water';
  if (g === Ground.METAL) return 'metal';
  if (g === Ground.GRASS) {
    const c = env.cells.get(i);
    return c && c.ashUntil > t ? 'ash' : 'grass';
  }
  return 'none';
}

/** @param {Env} env @param {any} map @param {number} i @param {number} t */
export function canIgnite(env, map, i, t) {
  if (env.burning.has(i)) return false;
  if (!FLAMMABLE.has(material(env, map, i, t))) return false;
  const c = env.cells.get(i);
  return !c || c.wetUntil <= t;
}

/** @param {Env} env @param {number} i */
function cell(env, i) {
  let c = env.cells.get(i);
  if (!c) {
    c = { burnMs: 0, at: 0, wetUntil: 0, ashUntil: 0 };
    env.cells.set(i, c);
  }
  return c;
}

/**
 * Sets a tile alight (if it can burn).
 * @param {Env} env @param {any} map @param {number} i @param {number} [at]
 * @returns {boolean}
 */
export function ignite(env, map, i, at = env.now) {
  if (!canIgnite(env, map, i, at)) return false;
  const c = cell(env, i);
  c.burnMs = ENV.fuel[material(env, map, i, at)];
  c.at = at;
  c.ashUntil = 0;
  env.burning.add(i);
  env.version++;
  return true;
}

/**
 * Puts out a tile and soaks it (it will not burn for a while).
 * @param {Env} env @param {any} map @param {number} i
 */
export function wet(env, map, i) {
  const c = cell(env, i);
  if (env.burning.delete(i)) c.burnMs = 0;
  c.wetUntil = env.now + ENV.wetMs;
  env.version++;
}

/** @param {Env} env @param {any} map @param {number} i @param {number} t */
function burnOut(env, map, i, t) {
  env.burning.delete(i);
  const c = cell(env, i);
  c.burnMs = 0;
  c.ashUntil = t + ENV.regrowMs;
  const o = env.objectAt.get(i);
  if (o && !o.gone) {
    if (o.type === 'tree') o.type = 'stump'; // a burnt tree leaves a stump you can walk past
    else if (o.type === 'bramble') o.gone = true;
    map.solid[i] = 0;
  }
  env.version++;
}

/** @param {any} map @param {number} i @returns {number[]} */
function neighbours(map, i) {
  const w = map.width;
  const tx = i % w;
  const out = [];
  if (tx > 0) out.push(i - 1);
  if (tx < w - 1) out.push(i + 1);
  if (i >= w) out.push(i - w);
  if (i + w < map.width * map.height) out.push(i + w);
  return out;
}
export { neighbours as envNeighbours };

/**
 * Advances the environment by one fixed game step.
 * @param {Env} env @param {any} map @param {{ x: number, y: number }} player @param {number} dtMs
 * @param {number} [budget] fast-forward work allowed this step
 */
export function stepEnv(env, map, player, dtMs, budget = ENV.catchUpBudget) {
  env.now += dtMs;
  updateAwake(env, map, player);
  runCatchUp(env, map, budget);
  if (env.sparks && env.sparks.untilMs <= env.now) {
    env.sparks = null;
    env.version++;
  }
  while (env.now >= env.nextTickMs) {
    tick(env, map);
    env.nextTickMs += ENV.tickMs;
  }
}

/** @param {Env} env @param {any} map @param {{ x: number, y: number }} player */
function updateAwake(env, map, player) {
  const ts = map.tileSize * ENV.regionTiles;
  const prx = Math.floor(player.x / ts);
  const pry = Math.floor(player.y / ts);
  /** @type {number[]} */
  const woke = [];
  for (let ry = 0; ry < env.rh; ry++) {
    for (let rx = 0; rx < env.rw; rx++) {
      const r = ry * env.rw + rx;
      const near = Math.abs(rx - prx) <= ENV.awakeRadius && Math.abs(ry - pry) <= ENV.awakeRadius ? 1 : 0;
      if (near === env.awake[r]) continue;
      env.awake[r] = near;
      if (near) woke.push(r);
      else if (!env.pending[r]) env.clock[r] = env.now; // freeze: remember when
    }
  }
  if (woke.length === 0) return;
  // Regions waking together are fast-forwarded together (fire crosses their borders naturally).
  const needs = woke.filter((r) => env.now - env.clock[r] >= ENV.stepMs && hasBurning(env, map, r));
  for (const r of woke) if (!needs.includes(r) && !env.pending[r]) env.clock[r] = env.now;
  if (needs.length === 0) return;
  for (const r of needs) env.pending[r] = 1;
  const start = Math.max(Math.min(...needs.map((r) => env.clock[r])), env.now - ENV.maxCatchUpMs);
  env.jobs.push({ regions: needs, T: start + ENV.stepMs, end: env.now });
}

/** @param {Env} env @param {any} map @param {number} r */
function hasBurning(env, map, r) {
  for (const i of env.burning) if (regionOf(env, map, i) === r) return true;
  return false;
}

/**
 * Fast-forward (DESIGN.md 4.4): coarse steps from the regions' clocks to the time they woke.
 * Whole steps only, so splitting the work across frames cannot change the result.
 * @param {Env} env @param {any} map @param {number} budget
 */
export function runCatchUp(env, map, budget) {
  const p = 1 - Math.pow(1 - ENV.spreadChance, ENV.stepMs / ENV.tickMs);
  while (budget > 0 && env.jobs.length > 0) {
    const job = env.jobs[0];
    const T = job.T;
    const inJob = new Set(job.regions);
    const list = [...env.burning].filter((i) => inJob.has(regionOf(env, map, i))).sort((a, b) => a - b);
    for (const i of list) {
      const c = /** @type {Cell} */ (env.cells.get(i));
      const r = regionOf(env, map, i);
      const from = Math.max(c.at, env.clock[r], T - ENV.stepMs);
      const dt = T - from;
      if (dt <= 0) continue;
      c.burnMs -= dt;
      c.at = T;
      for (const n of neighbours(map, i)) {
        if (roll(env.seed, n, Math.floor(T / ENV.stepMs), 1) >= p * (dt / ENV.stepMs)) continue;
        // Outside the fast-forward the world may be moving at its own pace: hold the ignition
        // until the fast-forward ends, so the result does not depend on how it was split.
        if (!inJob.has(regionOf(env, map, n))) env.heldIgnitions.add(n);
        else if (canIgnite(env, map, n, T)) ignite(env, map, n, T);
      }
      if (c.burnMs <= 0) burnOut(env, map, i, T);
    }
    budget -= Math.max(1, list.length);
    env.stats.catchUpSteps++;
    env.stats.catchUpCells += list.length;
    job.T += ENV.stepMs;
    if (job.T > job.end) {
      for (const r of job.regions) {
        env.clock[r] = job.end;
        env.pending[r] = 0;
      }
      // Cells left mid-step continue from the wake time.
      for (const i of env.burning) {
        const c = /** @type {Cell} */ (env.cells.get(i));
        if (inJob.has(regionOf(env, map, i)) && c.at < job.end) c.at = job.end;
      }
      env.jobs.shift();
      if (env.jobs.length === 0) releaseHeld(env, map);
    }
  }
}

/** @param {Env} env @param {any} map */
function releaseHeld(env, map) {
  for (const n of [...env.heldIgnitions].sort((a, b) => a - b)) {
    if (!env.pending[regionOf(env, map, n)]) ignite(env, map, n);
  }
  env.heldIgnitions.clear();
}

/** One 10 Hz tick over the burning cells of awake regions (capped). @param {Env} env @param {any} map */
function tick(env, map) {
  const t = env.nextTickMs;
  const all = [...env.burning].filter((i) => {
    const r = regionOf(env, map, i);
    return env.awake[r] && !env.pending[r] && /** @type {Cell} */ (env.cells.get(i)).at < t;
  });
  const n = Math.min(all.length, ENV.maxCellsPerTick);
  const startAt = all.length > 0 ? env.cursor % all.length : 0;
  env.stats.lastTickCells = n;
  env.stats.maxTickCells = Math.max(env.stats.maxTickCells, n);
  env.stats.deferred = all.length - n;
  env.cursor += n;
  const k = Math.floor(t / ENV.tickMs);
  for (let j = 0; j < n; j++) {
    const i = all[(startAt + j) % all.length];
    const c = /** @type {Cell} */ (env.cells.get(i));
    c.burnMs -= ENV.tickMs;
    c.at = t;
    for (const nb of neighbours(map, i)) {
      if (roll(env.seed, nb, k, 0) >= ENV.spreadChance) continue;
      if (env.pending[regionOf(env, map, nb)]) env.heldIgnitions.add(nb); // that region is being fast-forwarded
      else if (canIgnite(env, map, nb, t)) ignite(env, map, nb, t);
    }
    if (c.burnMs <= 0) burnOut(env, map, i, t);
  }
}

/**
 * Removes every door linked to `link` (a powered receiver opened them).
 * @param {Env} env @param {any} map @param {string} link @returns {boolean} whether any opened
 */
export function openDoors(env, map, link) {
  let opened = false;
  for (const [i, o] of env.objectAt) {
    if (o.type === 'door' && o.link === link && !o.gone) {
      o.gone = true;
      map.solid[i] = 0;
      opened = true;
    }
    if (o.type === 'receiver' && o.link === link) o.on = true;
  }
  if (opened) env.version++;
  return opened;
}

/** Counts for the debug overlay and tests. @param {Env} env */
export function envSummary(env) {
  let ash = 0;
  let wetCount = 0;
  for (const c of env.cells.values()) {
    if (c.ashUntil > env.now) ash++;
    if (c.wetUntil > env.now) wetCount++;
  }
  return {
    now: env.now,
    burning: env.burning.size,
    ash,
    wet: wetCount,
    awakeRegions: env.awake.reduce((a, b) => a + b, 0),
    pendingRegions: env.pending.reduce((a, b) => a + b, 0),
    jobs: env.jobs.length,
    ...env.stats,
  };
}
