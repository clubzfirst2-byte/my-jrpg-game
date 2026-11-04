// @ts-check
// How the player and the world act on the environment (P4): fire arrows, sword hits on objects,
// shock crystals (conduction through water and metal), water jars (dousing), and damage from fire
// and electricity. Pure logic.
import { ENV, material, ignite, wet, openDoors, envNeighbours, regionOf } from './envSim.js';
import { hitPlayer, hitEnemy } from '../combat/damage.js';

export const ENV_COMBAT = Object.freeze({
  /** Fire: half a heart per touch (the 800 ms invulnerability paces it); enemies 4 per second. */
  firePlayerDamage: 2,
  fireEnemyDamage: 4,
  fireEnemyEveryMs: 1000,
  /** Electricity: one heart for the player, 8 for enemies (and a stun). */
  shockPlayerDamage: 4,
  shockEnemyDamage: 8,
  /** Conduction search limits (cells and distance in tiles): the current fades with distance. */
  shockMaxCells: 400,
  shockMaxSteps: 24,
  sparkMs: 450,
  crystalCooldownMs: 1500,
  /** Dousing radius (tiles, Manhattan) of a broken water jar. */
  douseRadius: 2,
  brambleHp: 3,
  fireArrowDamage: 4,
});

/** @param {any} state @param {number} x @param {number} y */
export function tileIndexAt(state, x, y) {
  const m = state.map;
  const tx = Math.floor(x / m.tileSize);
  const ty = Math.floor(y / m.tileSize);
  if (tx < 0 || ty < 0 || tx >= m.width || ty >= m.height) return -1;
  return ty * m.width + tx;
}

/** A tile that lights arrows passing over it. @param {any} state @param {number} i */
export function isFireTile(state, i) {
  if (i < 0) return false;
  const env = state.env;
  if (env.burning.has(i)) return true;
  const o = env.objectAt.get(i);
  return !!o && !o.gone && (o.type === 'brazier' || o.type === 'campfire');
}

/**
 * Something hit the object / tile `i`: a sword swing or an arrow.
 * @param {any} state @param {number} i
 * @param {{ kind: 'sword' | 'arrow', id: string, fire?: boolean }} by
 * @returns {boolean} whether the hit did something
 */
export function hitTile(state, i, by) {
  const env = state.env;
  const map = state.map;
  if (i < 0) return false;
  if (by.kind === 'sword') {
    if (env.lastHit.get(i) === by.id) return false; // one hit per swing
    env.lastHit.set(i, by.id);
  }
  const o = env.objectAt.get(i);
  const mat = material(env, map, i);
  if (o && !o.gone) {
    if (o.type === 'crystal') return discharge(state, i);
    if (o.type === 'jar') {
      o.gone = true;
      map.solid[i] = 0;
      env.version++;
      douse(state, i);
      return true;
    }
    if (o.type === 'bramble' && by.kind === 'sword') {
      o.hp = (o.hp ?? ENV_COMBAT.brambleHp) - 1;
      state.events.push({ type: 'cut', tick: state.tick, x: o.tx, y: o.ty });
      if (o.hp <= 0) {
        o.gone = true;
        map.solid[i] = 0;
        env.version++;
      }
      return true;
    }
  }
  if (by.fire && ignite(env, map, i)) {
    state.events.push({ type: 'ignite', tick: state.tick });
    return true;
  }
  void mat;
  return false;
}

/**
 * Shock crystal: the current runs through the water and metal touching it.
 * @param {any} state @param {number} crystal tile index
 */
export function discharge(state, crystal) {
  const env = state.env;
  const map = state.map;
  const o = env.objectAt.get(crystal);
  if (!o || (o.cooldownUntil ?? 0) > env.now) return false;
  o.cooldownUntil = env.now + ENV_COMBAT.crystalCooldownMs;
  const reached = conductorsFrom(state, crystal);
  env.sparks = { cells: reached, untilMs: env.now + ENV_COMBAT.sparkMs };
  env.version++;
  state.events.push({ type: 'discharge', tick: state.tick, cells: reached.length });
  const set = new Set(reached);
  // Receivers touching the crystal or the current switch on and open their doors.
  for (const [i, r] of env.objectAt) {
    if (r.type !== 'receiver' || r.gone || !r.link) continue;
    const touching = envNeighbours(map, i).some((n) => set.has(n) || n === crystal);
    if (touching && openDoors(env, map, r.link)) {
      const pr = state.progress;
      if (pr && !pr.gates.includes(r.link)) pr.gates.push(r.link);
      state.saveRequested = true;
      state.events.push({ type: 'gateOpen', tick: state.tick, id: r.link });
    }
  }
  // Anyone standing in the current.
  const p = state.player;
  const pi = tileIndexAt(state, p.x, p.y);
  if (!p.dead && set.has(pi) && touchesSurface(state, p, pi)) {
    hitPlayer(state, { owner: 'enemy', id: `shock${state.tick}`, damage: ENV_COMBAT.shockPlayerDamage, from: { x: p.x, y: p.y + 1 }, kind: 'env', knock: 0.2, element: 'shock' });
  }
  for (const e of state.enemies) {
    if (e.state === 'dead') continue;
    const ei = tileIndexAt(state, e.x, e.y);
    if (set.has(ei) && touchesSurface(state, e, ei)) {
      hitEnemy(state, e, { owner: 'player', id: `shock${state.tick}`, damage: ENV_COMBAT.shockEnemyDamage, from: { x: e.x, y: e.y - 1 }, kind: 'projectile', knock: 0 });
      if (e.state === 'stun') e.stunMs = 1200;
    }
  }
  return true;
}

/**
 * The conductive tiles (water, metal) connected to a tile, nearest first, within the limits.
 * @param {any} state @param {number} from
 * @returns {number[]}
 */
export function conductorsFrom(state, from) {
  const env = state.env;
  const map = state.map;
  const conductive = (/** @type {number} */ i) => {
    const m = material(env, map, i);
    return m === 'water' || m === 'metal';
  };
  /** @type {number[]} */
  const out = [];
  const seen = new Set([from]);
  let frontier = envNeighbours(map, from).filter(conductive);
  for (const i of frontier) seen.add(i);
  for (let step = 0; step < ENV_COMBAT.shockMaxSteps && frontier.length > 0; step++) {
    /** @type {number[]} */
    const next = [];
    for (const i of frontier) {
      if (out.length >= ENV_COMBAT.shockMaxCells) return out;
      out.push(i);
      for (const n of envNeighbours(map, i)) {
        if (!seen.has(n) && conductive(n)) {
          seen.add(n);
          next.push(n);
        }
      }
    }
    frontier = next;
  }
  return out;
}

/** In the water / on the metal, not above it. @param {any} state @param {any} body @param {number} i */
function touchesSurface(state, body, i) {
  return body.z - state.map.elev[i] <= 4 || !!body.swimming;
}

/**
 * Water splashes over the tiles around: fires go out and the tiles stay wet for a while.
 * @param {any} state @param {number} center
 */
export function douse(state, center) {
  const map = state.map;
  const cx = center % map.width;
  const cy = (center / map.width) | 0;
  const r = ENV_COMBAT.douseRadius;
  for (let dy = -r; dy <= r; dy++) {
    for (let dx = -r; dx <= r; dx++) {
      if (Math.abs(dx) + Math.abs(dy) > r) continue;
      const x = cx + dx;
      const y = cy + dy;
      if (x < 0 || y < 0 || x >= map.width || y >= map.height) continue;
      wet(state.env, map, y * map.width + x);
    }
  }
  state.events.push({ type: 'douse', tick: state.tick });
}

/**
 * Sword swings against objects (crystals, jars, brambles). Called after the swing's hitboxes exist.
 * @param {any} state
 */
export function swordHitsObjects(state) {
  const map = state.map;
  const ts = map.tileSize;
  for (const hb of state.hitboxes) {
    if (hb.owner !== 'player') continue;
    const x0 = Math.floor((hb.x - hb.r) / ts);
    const x1 = Math.floor((hb.x + hb.r) / ts);
    const y0 = Math.floor((hb.y - hb.r) / ts);
    const y1 = Math.floor((hb.y + hb.r) / ts);
    for (let ty = y0; ty <= y1; ty++) {
      for (let tx = x0; tx <= x1; tx++) {
        if (tx < 0 || ty < 0 || tx >= map.width || ty >= map.height) continue;
        const i = ty * map.width + tx;
        const o = state.env.objectAt.get(i);
        if (!o || o.gone || Math.abs(hb.z - map.elev[i]) > 16) continue;
        hitTile(state, i, { kind: 'sword', id: hb.id });
      }
    }
  }
}

/**
 * Fire hurts whoever stands in it. @param {any} state @param {number} dtMs (enemy time)
 */
export function fireDamage(state, dtMs) {
  const env = state.env;
  const p = state.player;
  const pi = tileIndexAt(state, p.x, p.y);
  if (!p.dead && !p.swimming && env.burning.has(pi) && p.z - state.map.elev[pi] <= 8) {
    const r = hitPlayer(state, { owner: 'enemy', id: `fire${state.tick}`, damage: ENV_COMBAT.firePlayerDamage, from: { x: p.x, y: p.y + 1 }, kind: 'env', knock: 0.3, element: 'fire' });
    if (r === 'hurt') state.events.push({ type: 'burn', tick: state.tick });
  }
  for (const e of state.enemies) {
    if (e.state === 'dead') continue;
    e.fireMs = Math.max(0, (e.fireMs ?? 0) - dtMs);
    const ei = tileIndexAt(state, e.x, e.y);
    if (e.fireMs === 0 && env.burning.has(ei) && e.z - state.map.elev[ei] <= 8) {
      e.fireMs = ENV_COMBAT.fireEnemyEveryMs;
      hitEnemy(state, e, { owner: 'player', id: `fire${state.tick}`, damage: ENV_COMBAT.fireEnemyDamage, from: { x: e.x, y: e.y - 1 }, kind: 'projectile', knock: 0.2 });
    }
  }
}

/**
 * Arrow flight against the environment. Returns 'pass' to keep flying through a solid fire
 * source (it lights the arrow), 'stop' when it ends here, or 'fly'.
 * @param {any} state @param {any} pr projectile @param {boolean} blocked @param {boolean} expired
 * @returns {'pass' | 'stop' | 'fly'}
 */
export function arrowEnv(state, pr, blocked, expired) {
  if (pr.owner !== 'player' || pr.kind !== 'arrow') return blocked || expired ? 'stop' : 'fly';
  const i = tileIndexAt(state, pr.x, pr.y);
  if (isFireTile(state, i) && !pr.fire) {
    pr.fire = true;
    state.events.push({ type: 'fireArrow', tick: state.tick });
  }
  const o = i >= 0 ? state.env.objectAt.get(i) : undefined;
  if (blocked && o && !o.gone && (o.type === 'brazier' || o.type === 'campfire')) return 'pass';
  if (blocked) {
    hitTile(state, i, { kind: 'arrow', id: pr.id, fire: pr.fire });
    // Into a cliff: the fire lands on the tile it came from.
    if (pr.fire && !(o && !o.gone)) {
      const back = tileIndexAt(state, pr.x - pr.vx / 60, pr.y - pr.vy / 60);
      if (back >= 0) ignite(state.env, state.map, back);
    }
    return 'stop';
  }
  if (expired) {
    if (pr.fire) ignite(state.env, state.map, i); // a fire arrow sets the ground where it lands alight
    return 'stop';
  }
  return 'fly';
}

/** A fire arrow that hits an enemy burns it and the ground under it. @param {any} state @param {any} pr @param {any} e */
export function fireArrowHitsEnemy(state, pr, e) {
  if (!pr.fire) return;
  hitEnemy(state, e, { owner: 'player', id: `${pr.id}f`, damage: ENV_COMBAT.fireArrowDamage, from: { x: pr.x, y: pr.y }, kind: 'projectile', knock: 0 });
  ignite(state.env, state.map, tileIndexAt(state, e.x, e.y));
}

export { ENV, regionOf };
