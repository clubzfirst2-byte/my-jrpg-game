// @ts-check
// Villagers (P9): they stroll around their home spot, stop and face the player when spoken to,
// and are talked to with the attack button (like opening a chest). Pure logic.
// v1.0 (C3): a villager may be there only while conditions hold (`if`, the same conditions as a
// dialogue's start: flags, quest states, cores purified…) — added and removed as the progress
// changes — and may be see-through (`ghost`: the princess's 写し身, clearer with each core purified).
import { moveAndCollide, groundHeightUnder } from '../physics/collision.js';
import { roll } from '../core/hashRandom.js';
import { Ground } from '../world/tilemap.js';
import { conditionHolds, coresPurified } from './talk.js';

export const NPC = Object.freeze({
  speed: 24,
  /** Walks up to this far from home (px). */
  wander: 28,
  /** A new stroll target every few seconds. */
  pauseMs: 2600,
  /** Talk range (px) in front of the player. */
  talkRange: 28,
  /** Villagers stop walking when the player is this close. */
  stopNear: 40,
  /** How opaque a ghost is with no core purified, and how much clearer each core makes it. */
  ghostAlpha: 0.45,
  ghostAlphaPerCore: 0.1,
});

/**
 * @typedef {{ id: string, name: string, dialogue: string, look: number, x: number, y: number, z: number,
 *   prevX: number, prevY: number, homeX: number, homeY: number, tx: number, ty: number, waitMs: number,
 *   facing: string, moving: boolean, walkTime: number, halfWidth: number, height: number, stay: boolean, reach: number, ghost: boolean, art: string }} Npc
 * stay: never strolls (a shopkeeper behind the counter, P10.1); reach: talk range (across a counter);
 * ghost: drawn see-through (v1.0); art: the name of its release frames npc.<art>.* (v1.0: the
 * princess stands in seven places under seven ids, all drawn from npc.princess.*)
 */

/**
 * @typedef {{ id: string, name: string, dialogue: string, look?: number, tx: number, ty: number, stay?: boolean, reach?: number,
 *   if?: import('./talk.js').Condition[], ghost?: boolean, art?: string }} NpcDef
 * if: there only while all these conditions hold (v1.0)
 */

/**
 * @param {any} map @param {NpcDef[]} defs
 * @returns {Npc[]}
 */
export function createNpcs(map, defs) {
  const ts = map.tileSize;
  return defs.map((d) => {
    const x = d.tx * ts + ts / 2;
    const y = d.ty * ts + ts - 2;
    const body = { x, y, halfWidth: 5, height: 6 };
    return {
      id: d.id,
      name: d.name,
      dialogue: d.dialogue,
      look: d.look ?? 0,
      x,
      y,
      z: groundHeightUnder(body, map),
      prevX: x,
      prevY: y,
      homeX: x,
      homeY: y,
      tx: x,
      ty: y,
      waitMs: 0,
      facing: 'down',
      moving: false,
      walkTime: 0,
      halfWidth: 5,
      height: 6,
      stay: !!d.stay,
      reach: d.reach ?? NPC.talkRange,
      ghost: !!d.ghost,
      art: d.art ?? d.id,
    };
  });
}

/** Whether a villager is there now (all of its `if` conditions hold). @param {any} state @param {NpcDef} def */
export function npcPresent(state, def) {
  for (const c of def.if ?? []) if (!conditionHolds(state, c)) return false;
  return true;
}

/** @param {Npc[]} npcs @param {string} id */
function indexOfNpc(npcs, id) {
  for (let k = 0; k < npcs.length; k++) if (npcs[k].id === id) return k;
  return -1;
}

/**
 * Adds the villagers whose conditions now hold and removes those whose no longer do (v1.0, C3).
 * Someone being talked to stays until the conversation ends. Villagers keep the order of their
 * definitions; ones added by hand (debug) stay at the end. Cheap: run every step.
 * @param {any} state @returns {boolean} whether anyone came or went
 */
export function syncNpcs(state) {
  /** @type {NpcDef[]} */
  const defs = state.npcDefs ?? [];
  let changed = false;
  for (const d of defs) {
    if (!d.if) continue;
    const want = npcPresent(state, d);
    const k = indexOfNpc(state.npcs, d.id);
    if (want && k < 0) {
      state.npcs.push(...createNpcs(state.map, [d]));
      changed = true;
    } else if (!want && k >= 0 && state.dialogue?.npc !== d.id) {
      state.npcs.splice(k, 1);
      changed = true;
    }
  }
  if (changed) {
    const order = new Map(defs.map((d, k) => [d.id, k]));
    state.npcs.sort((/** @type {Npc} */ a, /** @type {Npc} */ b) => (order.get(a.id) ?? Infinity) - (order.get(b.id) ?? Infinity));
  }
  return changed;
}

/** How opaque a villager is drawn: 1, or a ghost's alpha (clearer with each core purified). @param {any} state @param {Npc} n */
export function npcAlpha(state, n) {
  if (!n.ghost) return 1;
  return Math.min(1, NPC.ghostAlpha + NPC.ghostAlphaPerCore * coresPurified(state));
}

/**
 * One step: stroll, or stand still and face the player when they are near / talking.
 * @param {any} state @param {number} dt seconds
 */
export function stepNpcs(state, dt) {
  syncNpcs(state);
  const p = state.player;
  const map = state.map;
  for (const n of /** @type {Npc[]} */ (state.npcs)) {
    n.prevX = n.x;
    n.prevY = n.y;
    const dx = p.x - n.x;
    const dy = p.y - n.y;
    const near = Math.hypot(dx, dy) < Math.max(NPC.stopNear, n.reach + 12);
    if (near || n.stay || state.dialogue?.npc === n.id) {
      n.moving = false;
      n.facing = !near && n.stay ? 'down' : Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? 'right' : 'left') : dy > 0 ? 'down' : 'up';
      continue;
    }
    const tdx = n.tx - n.x;
    const tdy = n.ty - n.y;
    const dist = Math.hypot(tdx, tdy);
    if (dist < 1) {
      n.moving = false;
      n.waitMs -= dt * 1000;
      if (n.waitMs <= 0) {
        // A new spot near home (deterministic per villager and time).
        const k = Math.floor(state.tick / 60);
        const a = roll(7, n.homeX, n.homeY, k) * Math.PI * 2;
        const r = roll(8, n.homeX, n.homeY, k) * NPC.wander;
        n.tx = n.homeX + Math.cos(a) * r;
        n.ty = n.homeY + Math.sin(a) * r;
        n.waitMs = NPC.pauseMs;
      }
      continue;
    }
    const step = Math.min(dist, NPC.speed * dt);
    const before = { x: n.x, y: n.y };
    moveAndCollide(n, map, (tdx / dist) * step, (tdy / dist) * step, n.z);
    // Never into water or pits.
    const i = Math.floor(n.y / map.tileSize) * map.width + Math.floor(n.x / map.tileSize);
    if (map.ground[i] === Ground.WATER || map.ground[i] === Ground.PIT) {
      n.x = before.x;
      n.y = before.y;
    }
    if (Math.hypot(n.x - before.x, n.y - before.y) < 0.01) {
      n.tx = n.x; // stuck: pick another spot next time
      n.ty = n.y;
    }
    n.moving = true;
    n.walkTime += dt;
    n.facing = Math.abs(tdx) > Math.abs(tdy) ? (tdx > 0 ? 'right' : 'left') : tdy > 0 ? 'down' : 'up';
  }
}

/**
 * The villager in front of the player, close enough to talk to.
 * @param {any} state @returns {Npc | null}
 */
export function npcInReach(state) {
  const p = state.player;
  let best = null;
  let bestD = Infinity;
  for (const n of /** @type {Npc[]} */ (state.npcs)) {
    const dx = n.x - p.x;
    const dy = n.y - p.y;
    const d = Math.hypot(dx, dy);
    if (d < n.reach && dx * p.aimX + dy * p.aimY > 0 && Math.abs(n.z - p.z) < 12 && d < bestD) {
      best = n;
      bestD = d;
    }
  }
  return best;
}
