// @ts-check
// Items in play (P6): what the equipment does to the player each step, using up arrows and wearing
// out weapons, enemy drops, items lying on the ground (picked up by walking over them), and what is
// nearby to use (a fire to cook on, the forge). Pure logic.
import { roll } from '../core/hashRandom.js';
import {
  weaponStats,
  bowStats,
  armorStats,
  hasBuff,
  wearGear,
  addItem,
  removeItem,
  countOf,
  dropsFor,
  itemDef,
} from './inventory.js';
import { ignite } from '../env/envSim.js';
import { tileIndexAt } from '../env/envActions.js';

/** Items lying in the world come back after one game day. */
export const PICKUP_REGROW_MS = 24 * 60_000;
const PICKUP_RANGE = 12;
const USE_RANGE = 26;

/**
 * @typedef {{ key: string, item: string, count: number, x: number, y: number, z: number, mapId?: string }} Pickup
 *   mapId: placed by the map (remembered when taken); drops have none
 */

/** @param {any} state */
const inv = (state) => state.progress.inv;

/**
 * Copies equipment and buffs onto the player for the physics and combat code to read.
 * @param {any} state
 */
export function applyGear(state) {
  const p = state.player;
  const i = inv(state);
  const now = state.env.now;
  p.weapon = weaponStats(i);
  p.bow = bowStats(i);
  p.arrows = countOf(i, 'arrow');
  const a = armorStats(i);
  p.defense = a.defense;
  p.grip = a.traits.has('grip');
  p.shockproof = a.traits.has('shockproof');
  p.fireproof = a.traits.has('fireproof') || hasBuff(p, 'fireproof', now);
  p.attackUp = hasBuff(p, 'attackUp', now);
  p.defenseUp = hasBuff(p, 'defenseUp', now);
}

/**
 * Places the map's items (except ones taken less than a day ago).
 * @param {any} state
 */
export function placePickups(state) {
  const map = state.map;
  const picked = state.progress.picked ?? {};
  /** @type {Pickup[]} */
  const list = [];
  for (const d of state.pickupDefs) {
    const t = picked[d.id];
    if (typeof t === 'number' && state.env.now - t < PICKUP_REGROW_MS) continue;
    const ts = map.tileSize;
    list.push({ key: d.id, mapId: d.id, item: d.item, count: d.count ?? 1, x: d.tx * ts + ts / 2, y: d.ty * ts + ts - 3, z: map.elev[d.ty * map.width + d.tx] });
  }
  state.pickups = list;
}

/**
 * Runs after combat each step: arrows / durability, drops, picking up, things in reach.
 * @param {any} state
 */
export function itemStep(state) {
  const i = inv(state);
  const p = state.player;
  // Shots fired this step use an arrow and wear the bow.
  for (const e of state.events) {
    if (e.tick !== state.tick) continue;
    if (e.type === 'shoot') {
      removeItem(i, 'arrow');
      const broke = wearGear(i, 'bow');
      if (broke) state.events.push({ type: 'broke', tick: state.tick, name: broke });
    }
  }
  // Sword hits that landed this step wear the blade; a fire blade lights what it cuts.
  if (state.landedHits.length > 0) {
    for (const h of state.landedHits) {
      if (h.element === 'fire') ignite(state.env, state.map, tileIndexAt(state, h.x, h.y));
    }
    const broke = wearGear(i, 'weapon');
    if (broke) state.events.push({ type: 'broke', tick: state.tick, name: broke });
  }
  const swing = state.hitboxes.find((/** @type {any} */ h) => h.owner === 'player' && h.element === 'fire');
  if (swing && swing.id !== state.lastFireSwing) {
    // The fire blade sets grass and brambles alight where it swings (once per swing).
    state.lastFireSwing = swing.id;
    ignite(state.env, state.map, tileIndexAt(state, swing.x, swing.y));
  }

  // Defeated enemies drop things (once).
  for (const e of state.enemies) {
    if (e.state !== 'dead' || e.dropped) continue;
    e.dropped = true;
    const drops = dropsFor(e.kind, (k) => roll(state.env.seed, e.id * 7919 + state.respawns, k, 31));
    drops.forEach((d, k) => {
      state.pickups.push({ key: `drop${state.nextId++}`, item: d.item, count: d.count, x: e.x + (k - (drops.length - 1) / 2) * 8, y: e.y, z: e.z });
    });
  }

  // Walking over an item picks it up.
  if (!p.dead) {
    state.pickups = state.pickups.filter((/** @type {Pickup} */ it) => {
      if (Math.hypot(it.x - p.x, it.y - p.y) > PICKUP_RANGE || Math.abs(it.z - p.z) > 12) return true;
      const taken = addItem(i, it.item, it.count);
      if (taken === 0) {
        if (state.fullWarnedKey !== it.key) state.events.push({ type: 'full', tick: state.tick, item: it.item });
        state.fullWarnedKey = it.key;
        return true;
      }
      state.events.push({ type: 'pickup', tick: state.tick, item: it.item, count: taken });
      if (taken < it.count) {
        it.count -= taken;
        return true;
      }
      if (it.mapId) state.progress.picked = { ...(state.progress.picked ?? {}), [it.mapId]: state.env.now };
      return false;
    });
  }

  // Something to use nearby: a fire (cooking) or the forge.
  state.nearby = null;
  for (const [idx, o] of state.env.objectAt) {
    if (o.gone || (o.type !== 'campfire' && o.type !== 'brazier' && o.type !== 'anvil')) continue;
    const ts = state.map.tileSize;
    const ox = (idx % state.map.width) * ts + ts / 2;
    const oy = Math.floor(idx / state.map.width) * ts + ts / 2;
    if (Math.hypot(ox - p.x, oy - (p.y - 4)) <= USE_RANGE && Math.abs(state.map.elev[idx] - p.z) < 12) {
      state.nearby = o.type === 'anvil' ? 'forge' : 'cook';
      break;
    }
  }
}

/** Name for messages. @param {string} id */
export const itemName = (id) => itemDef(id.split(':')[0]).name;
