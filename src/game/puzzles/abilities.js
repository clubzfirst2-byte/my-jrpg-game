// @ts-check
// The four 星環 abilities (P7, DESIGN.md 5.7):
//   灯火 light        a floating light orb (lights the dark, feeds light sensors)
//   念動 telekinesis  sends a crate sliding until it hits something
//   蔓結び vine        grows a vine platform over water or a pit (a bridge, a few at a time; it burns)
//   共鳴 resonance    a pulse that wakes resonance stones around (through walls)
// Plus crates pushed by sword hits, and falling into pits. Pure logic.
import { Ground } from '../world/tilemap.js';
import { energize } from './switches.js';

/** Higher than this above a pit's floor (px), the player is on a ledge beside it, not in it. */
const PIT_LEDGE_PX = 8;

export const ABILITY_IDS = /** @type {const} */ (['light', 'telekinesis', 'vine', 'resonance']);
/** @type {Record<string, string>} */
export const ABILITY_NAMES = { light: '灯火', telekinesis: '念動', vine: '蔓結び', resonance: '共鳴' };

export const ABILITY = Object.freeze({
  cooldownMs: { light: 600, telekinesis: 400, vine: 300, resonance: 1500 },
  orbMs: 20_000,
  orbAhead: 14,
  orbHeight: 10,
  /** Telekinesis reaches crates this many tiles ahead; slides stop after this many tiles. */
  reachTiles: 5,
  maxSlide: 12,
  vineReach: 3,
  vineMax: 6,
  vineMs: 60_000,
  pulseRadiusTiles: 7,
  pulseMs: 600,
  /** Falling into a pit: back to the edge, half a heart. */
  pitDamage: 2,
});

/** @param {any} state @param {string} id */
export function grantAbility(state, id) {
  const pr = state.progress;
  if (pr.abilities.includes(id)) return false;
  pr.abilities.push(id);
  if (!pr.ability) pr.ability = id;
  state.saveRequested = true;
  state.events.push({ type: 'ability', tick: state.tick, id });
  return true;
}

/** Next owned ability (for the switch button). @param {any} state */
export function cycleAbility(state) {
  const pr = state.progress;
  if (pr.abilities.length === 0) return null;
  const k = pr.abilities.indexOf(pr.ability);
  pr.ability = pr.abilities[(k + 1) % pr.abilities.length];
  return pr.ability;
}

/** Tiles in front of the player, nearest first. @param {any} state @param {number} n */
function tilesAhead(state, n) {
  const p = state.player;
  const map = state.map;
  const ts = map.tileSize;
  const d = { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] }[/** @type {'up'} */ (p.facing)];
  const tx = Math.floor(p.x / ts);
  const ty = Math.floor((p.y - 3) / ts);
  /** @type {number[]} */
  const out = [];
  for (let k = 1; k <= n; k++) {
    const x = tx + d[0] * k;
    const y = ty + d[1] * k;
    if (x < 0 || y < 0 || x >= map.width || y >= map.height) break;
    out.push(y * map.width + x);
  }
  return { tiles: out, dx: d[0], dy: d[1] };
}

/**
 * Uses the selected ability (the ability button).
 * @param {any} state
 * @returns {boolean} whether something happened
 */
export function useAbility(state) {
  const pr = state.progress;
  const id = pr.ability;
  const now = state.env.now;
  if (!id || !pr.abilities.includes(id)) {
    state.events.push({ type: 'noAbility', tick: state.tick });
    return false;
  }
  if ((state.abilityReadyAt ?? 0) > now) return false;
  state.abilityReadyAt = now + ABILITY.cooldownMs[/** @type {'light'} */ (id)];
  const p = state.player;
  let ok = false;
  if (id === 'light') {
    state.orb = { x: p.x + p.aimX * ABILITY.orbAhead, y: p.y + p.aimY * ABILITY.orbAhead, z: p.z + ABILITY.orbHeight, untilMs: now + ABILITY.orbMs };
    ok = true;
  } else if (id === 'telekinesis') {
    const { tiles, dx, dy } = tilesAhead(state, ABILITY.reachTiles);
    for (const i of tiles) {
      const o = state.env.objectAt.get(i);
      if (o && !o.gone && o.type === 'crate') {
        ok = slideCrate(state, o, dx, dy, ABILITY.maxSlide) > 0;
        break;
      }
      if (state.map.solid[i]) break; // something in the way
    }
  } else if (id === 'vine') {
    const { tiles } = tilesAhead(state, ABILITY.vineReach);
    for (const i of tiles) {
      const g = state.map.ground[i];
      if (g === Ground.WATER || g === Ground.PIT) {
        growVine(state, i);
        ok = true;
        break;
      }
      if (state.map.solid[i]) break;
    }
  } else if (id === 'resonance') {
    const ts = state.map.tileSize;
    const r = ABILITY.pulseRadiusTiles * ts;
    state.pulse = { x: p.x, y: p.y - 6, startMs: now };
    energize(state, 'resonance', (i) => {
      const x = (i % state.map.width) * ts + ts / 2;
      const y = Math.floor(i / state.map.width) * ts + ts / 2;
      return Math.hypot(x - p.x, y - p.y) <= r;
    });
    ok = true;
  }
  state.events.push({ type: ok ? 'abilityUsed' : 'noTarget', tick: state.tick, id });
  return ok;
}

/** @param {any} state @param {number} i */
function growVine(state, i) {
  const env = state.env;
  // Keep at most vineMax: the oldest withers.
  if (env.vines.size >= ABILITY.vineMax) {
    const oldest = [...env.vines.entries()].sort((a, b) => a[1].untilMs - b[1].untilMs)[0];
    witherVine(state, oldest[0]);
  }
  env.vines.set(i, { ground: state.map.ground[i], untilMs: env.now + ABILITY.vineMs });
  state.map.ground[i] = Ground.VINE;
  env.version++;
}

/** @param {any} state @param {number} i */
export function witherVine(state, i) {
  const v = state.env.vines.get(i);
  if (!v) return;
  state.map.ground[i] = v.ground;
  state.env.vines.delete(i);
  state.env.version++;
}

/**
 * Moves a crate: slides it up to `max` tiles until blocked (walls, objects, other heights, water,
 * pits). Returns the tiles moved.
 * @param {any} state @param {any} o crate @param {number} dx @param {number} dy @param {number} max
 */
export function slideCrate(state, o, dx, dy, max) {
  const map = state.map;
  const env = state.env;
  const from = o.ty * map.width + o.tx;
  const h = map.elev[from];
  let x = o.tx;
  let y = o.ty;
  for (let k = 0; k < max; k++) {
    const nx = x + dx;
    const ny = y + dy;
    if (nx < 0 || ny < 0 || nx >= map.width || ny >= map.height) break;
    const n = ny * map.width + nx;
    const g = map.ground[n];
    if (map.solid[n] || map.elev[n] !== h || g === Ground.WATER || g === Ground.PIT) break;
    x = nx;
    y = ny;
  }
  const moved = Math.abs(x - o.tx) + Math.abs(y - o.ty);
  if (moved === 0) return 0;
  const to = y * map.width + x;
  env.objectAt.delete(from);
  map.solid[from] = 0;
  o.fromTx = o.tx;
  o.fromTy = o.ty;
  o.movedAt = env.now;
  o.tx = x;
  o.ty = y;
  env.objectAt.set(to, o);
  map.solid[to] = 1;
  env.version++;
  state.events.push({ type: 'crateMoved', tick: state.tick });
  return moved;
}

/**
 * Every step: orb and vines run out; stepping into a pit.
 * @param {any} state
 */
export function stepAbilities(state) {
  const env = state.env;
  const now = env.now;
  if (state.orb && state.orb.untilMs <= now) state.orb = null;
  if (state.pulse && now - state.pulse.startMs > ABILITY.pulseMs) state.pulse = null;
  for (const [i, v] of [...env.vines]) if (v.untilMs <= now) witherVine(state, i);
  // Pits: walking (not jumping or gliding) onto one drops you back at the edge.
  const p = state.player;
  if (p.dead || !p.grounded || p.climbing) return;
  const ts = state.map.tileSize;
  const i = Math.floor(p.y / ts) * state.map.width + Math.floor(p.x / ts);
  if (state.map.ground[i] !== Ground.PIT) return;
  // Volume phase 1: standing on a ledge above the pit (the body still on the higher ground while its
  // middle is past the edge) is not falling in: the player walks off, and may open the glider.
  if (p.z - state.map.elev[i] > PIT_LEDGE_PX) return;
  p.x = p.prevX = p.safeX;
  p.y = p.prevY = p.safeY;
  p.z = p.prevZ = p.groundZ = p.safeZ;
  p.vx = p.vy = p.vz = 0;
  p.hp = Math.max(0, p.hp - ABILITY.pitDamage);
  if (p.hp === 0) p.dead = true;
  state.events.push({ type: 'fell', tick: state.tick });
}
