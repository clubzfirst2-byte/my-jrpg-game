// @ts-check
// Mechanism parts (P7, DESIGN.md 5.7). A switch only cares about the KIND of input it gets —
// weight, light, fire, electricity (shock), resonance — never about how the player produced it,
// so every puzzle can be solved in more than one way.
//
//   plate   weight: the player, an enemy or a crate standing on it (only while it stays there)
//   sensor  light: a light orb, a flame (burning tile, lit sconce, brazier, campfire) nearby
//   sconce  fire: lit by a fire arrow, the fire blade, or a fire next to it (stays lit)
//   stone   resonance / shock: a resonance pulse or electricity reaching it (active for a while)
//
// Switches share a `link` (the doors they open) and a `group`: when every switch of one group is
// active at the same moment, the link's doors open for good (saved like the P4 vault).
// v1.0: seats (`seat: true`) of the final boss are read by it instead and never open anything.
// The final boss itself never counts as weight on a plate (it is huge and floats).
import { openDoors, envNeighbours } from '../env/envSim.js';
import { tileIndexAt } from '../env/envActions.js';

/** @typedef {'weight' | 'light' | 'fire' | 'shock' | 'resonance'} InputKind */
/**
 * @typedef {object} SwitchDef
 * @property {string} id
 * @property {'plate' | 'sensor' | 'sconce' | 'stone'} kind
 * @property {number} tx @property {number} ty
 * @property {string} link   doors it opens
 * @property {string} group  switches that must be active together
 * @property {InputKind[]} accepts
 * @property {boolean} [seat]  v1.0 (C7): a seat (座) of 淀みの源. Seats open no doors and are never
 *   saved as gates: the source reads their state (state.switchActive) every step, and its inversion
 *   wave puts them out again (finalBoss.js). Their link / group only name them.
 */

export const SWITCH = Object.freeze({
  /** Light reaches a sensor from this far (px). */
  lightRange: 40,
  /** A stone stays active this long after resonance / electricity (ms). */
  stoneMs: 10_000,
});

/** @param {any} state @param {SwitchDef} s */
const idx = (state, s) => s.ty * state.map.width + s.tx;

/** Where the light comes from now: orb, flames, lit sconces. @param {any} state */
export function lightSources(state) {
  const env = state.env;
  const map = state.map;
  const ts = map.tileSize;
  /** @type {{ x: number, y: number }[]} */
  const out = [];
  if (state.orb) out.push({ x: state.orb.x, y: state.orb.y });
  const center = (/** @type {number} */ i) => ({ x: (i % map.width) * ts + ts / 2, y: Math.floor(i / map.width) * ts + ts / 2 });
  for (const i of env.burning) out.push(center(i));
  for (const [i, o] of env.objectAt) {
    if (o.gone) continue;
    if ((o.type === 'sconce' && o.lit) || o.type === 'brazier' || o.type === 'campfire') out.push(center(i));
  }
  return out;
}

/**
 * Whether a switch is receiving one of its inputs right now.
 * @param {any} state @param {SwitchDef} s @param {{ x: number, y: number }[]} lights
 */
export function switchActive(state, s, lights) {
  const i = idx(state, s);
  const map = state.map;
  const ts = map.tileSize;
  const accepts = new Set(s.accepts);
  if (accepts.has('weight')) {
    const p = state.player;
    const on = (/** @type {any} */ b) => tileIndexAt(state, b.x, b.y) === i && b.z - map.elev[i] <= 2;
    const o = state.env.objectAt.get(i);
    if ((!p.dead && p.grounded && on(p)) || (o && !o.gone && o.type === 'crate') || state.enemies.some((/** @type {any} */ e) => e.state !== 'dead' && !e.final && on(e))) return true;
  }
  if (accepts.has('light')) {
    const cx = s.tx * ts + ts / 2;
    const cy = s.ty * ts + ts / 2;
    if (lights.some((l) => Math.hypot(l.x - cx, l.y - cy) <= SWITCH.lightRange)) return true;
  }
  if (accepts.has('fire')) {
    const o = state.env.objectAt.get(i);
    if (o && o.lit) return true;
  }
  if (accepts.has('resonance') || accepts.has('shock')) {
    if ((state.switchUntil[s.id] ?? 0) > state.env.now) return true;
  }
  return false;
}

/**
 * A resonance pulse or electricity reached these tiles: stones there wake up.
 * @param {any} state @param {'resonance' | 'shock'} kind @param {(i: number) => boolean} reaches
 */
export function energize(state, kind, reaches) {
  for (const s of /** @type {SwitchDef[]} */ (state.switches)) {
    if (!s.accepts.includes(kind)) continue;
    const i = idx(state, s);
    if (reaches(i) || envNeighbours(state.map, i).some(reaches)) {
      state.switchUntil[s.id] = state.env.now + SWITCH.stoneMs;
      state.events.push({ type: 'switchOn', tick: state.tick, id: s.id });
    }
  }
}

/**
 * Lights sconces next to a fire, then opens doors whose switch group is complete.
 * @param {any} state
 */
export function stepSwitches(state) {
  const env = state.env;
  const map = state.map;
  // A fire right next to a sconce lights it.
  for (const [i, o] of env.objectAt) {
    if (o.type !== 'sconce' || o.gone || o.lit) continue;
    if (envNeighbours(map, i).some((n) => env.burning.has(n))) lightSconce(state, o);
  }
  // Electricity in the air (crystals, lightning) energizes stones it touches.
  if (env.sparks && env.sparks.untilMs > env.now) {
    const cells = new Set(env.sparks.cells);
    energize(state, 'shock', (i) => cells.has(i));
  }
  if (state.switches.length === 0) return;
  const lights = lightSources(state);
  /** @type {Map<string, boolean>} link/group -> all active so far */
  const groups = new Map();
  state.switchActive = {};
  for (const s of /** @type {SwitchDef[]} */ (state.switches)) {
    const on = switchActive(state, s, lights);
    state.switchActive[s.id] = on;
    if (s.seat) continue; // read by the final boss, never a door
    const key = `${s.link}\u0000${s.group}`;
    groups.set(key, (groups.get(key) ?? true) && on);
  }
  for (const [key, all] of groups) {
    if (!all) continue;
    const link = key.split('\u0000')[0];
    if (state.progress.gates.includes(link)) continue;
    if (openDoors(env, map, link)) {
      state.progress.gates.push(link);
      state.saveRequested = true;
      state.events.push({ type: 'gateOpen', tick: state.tick, id: link });
    }
  }
}

/** @param {any} state @param {any} o */
export function lightSconce(state, o) {
  if (o.lit) return;
  o.lit = true;
  state.env.version++;
  state.events.push({ type: 'sconceLit', tick: state.tick });
}

/** v1.0 (C7): puts a sconce out (the source's inversion wave). @param {any} state @param {any} o */
export function unlightSconce(state, o) {
  if (!o.lit) return;
  o.lit = false;
  state.env.version++;
  state.events.push({ type: 'sconceOut', tick: state.tick });
}
