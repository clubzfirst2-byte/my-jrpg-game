// @ts-check
// Villagers (P9): they stroll around their home spot, stop and face the player when spoken to,
// and are talked to with the attack button (like opening a chest). Pure logic.
// v1.0 (C3): a villager may be there only while conditions hold (`if`, the same conditions as a
// dialogue's start: flags, quest states, cores purified…) — added and removed as the progress
// changes — and may be see-through (`ghost`: the princess's 写し身, clearer with each core purified).
// v1.0 final: villagers have a small solid body (below: NPC_BODY, blockPlayerByNpcs).
import { moveAndCollide, groundHeightUnder } from '../physics/collision.js';
import { roll } from '../core/hashRandom.js';
import { Ground, isSolidTile } from '../world/tilemap.js';
import { conditionHolds, coresPurified } from './talk.js';

/**
 * v1.0 final (QA C-2, "the hero walks through villagers and stands on top of them while talking"):
 * a villager's solid body, a box at its feet like the player's (x ± halfWidth, y - depth .. y).
 * - The player cannot walk into it (and slides along it); a player already overlapping one (it
 *   appeared on top of them) can always walk out. The villager never moves the player.
 * - A strolling villager never steps into the player (it stops and picks another spot), and never
 *   into a keep-clear tile: a doorway (warp) and the tiles around it, or a 1-tile corridor. So none
 *   can stand in a doorway or a narrow passage.
 * - Last resort against any soft-lock: pushing into a villager for `yieldMs` makes it step aside
 *   (perpendicular to the push, if there is room); with no room, or if it keeps its place (`stay`),
 *   it lets the player squeeze through.
 * - Only within `zReach` of the player's height (jumping clears it, a ledge above is no wall).
 * - Ghosts (the princess's 写し身 by the record stones) have no body: an apparition you can walk
 *   through reads right, and it stands by the respawn points, where a body could box the player in.
 */
export const NPC_BODY = Object.freeze({ halfWidth: 5, depth: 6, zReach: 12, yieldMs: 900, asideStep: 14 });

/** Whether a villager has a solid body. @param {{ ghost?: boolean }} n */
export const npcSolid = (n) => !n.ghost;

/**
 * How much a player box (feet at x, y) overlaps a villager's body (0 = apart), in px².
 * @param {number} x @param {number} y @param {{ halfWidth: number, height: number }} p @param {{ x: number, y: number }} n
 */
export function npcOverlap(x, y, p, n) {
  const ox = Math.min(x + p.halfWidth, n.x + NPC_BODY.halfWidth) - Math.max(x - p.halfWidth, n.x - NPC_BODY.halfWidth);
  const oy = Math.min(y, n.y) - Math.max(y - p.height, n.y - NPC_BODY.depth);
  return ox > 0 && oy > 0 ? ox * oy : 0;
}

/** @type {WeakMap<object, { warps: any, clear: Uint8Array }>} */
const keepClearCache = new WeakMap();

/**
 * Tiles no strolling villager may step on: every warp (doorways) with the tiles around it, and every
 * 1-tile corridor (a walkable tile walled on both sides). 1 = keep clear.
 * @param {any} map @param {any[]} warps
 * @returns {Uint8Array}
 */
export function keepClearTiles(map, warps) {
  const hit = keepClearCache.get(map);
  if (hit && hit.warps === warps) return hit.clear;
  const w = map.width;
  const clear = new Uint8Array(w * map.height);
  const blocked = (/** @type {number} */ tx, /** @type {number} */ ty, /** @type {number} */ z) => {
    if (isSolidTile(map, tx, ty)) return true;
    const i = ty * w + tx;
    return map.ground[i] === Ground.WATER || map.ground[i] === Ground.PIT || map.elev[i] !== z;
  };
  for (let ty = 0; ty < map.height; ty++) {
    for (let tx = 0; tx < w; tx++) {
      if (isSolidTile(map, tx, ty)) continue;
      const z = map.elev[ty * w + tx];
      if ((blocked(tx - 1, ty, z) && blocked(tx + 1, ty, z)) || (blocked(tx, ty - 1, z) && blocked(tx, ty + 1, z))) clear[ty * w + tx] = 1;
    }
  }
  for (const wp of warps ?? []) {
    for (let dy = -1; dy <= 1; dy++) {
      for (let dx = -1; dx <= 1; dx++) {
        const tx = wp.tx + dx;
        const ty = wp.ty + dy;
        if (tx >= 0 && ty >= 0 && tx < w && ty < map.height) clear[ty * w + tx] = 1;
      }
    }
  }
  keepClearCache.set(map, { warps, clear });
  return clear;
}

/** Whether a villager's body at (x, y) touches a keep-clear tile. @param {any} map @param {Uint8Array} clear @param {number} x @param {number} y */
export function onKeepClear(map, clear, x, y) {
  const ts = map.tileSize;
  const x0 = Math.floor((x - NPC_BODY.halfWidth) / ts);
  const x1 = Math.floor((x + NPC_BODY.halfWidth - 1e-4) / ts);
  const y0 = Math.floor((y - NPC_BODY.depth) / ts);
  const y1 = Math.floor((y - 1e-4) / ts);
  for (let ty = y0; ty <= y1; ty++) for (let tx = x0; tx <= x1; tx++) if (clear[ty * map.width + tx]) return true;
  return false;
}

/** Whether a villager may stand at (x, y): no wall, water, pit or keep-clear tile under its body. @param {any} state @param {number} x @param {number} y */
function npcSpotFree(state, x, y) {
  const map = state.map;
  const ts = map.tileSize;
  for (const px of [x - NPC_BODY.halfWidth, x + NPC_BODY.halfWidth - 1e-4]) {
    for (const py of [y - NPC_BODY.depth, y - 1e-4]) {
      const tx = Math.floor(px / ts);
      const ty = Math.floor(py / ts);
      if (isSolidTile(map, tx, ty)) return false;
      const g = map.ground[ty * map.width + tx];
      if (g === Ground.WATER || g === Ground.PIT) return false;
    }
  }
  return !onKeepClear(map, keepClearTiles(map, state.warps), x, y);
}

/**
 * The player's position and height before their move (for blockPlayerByNpcs).
 * @typedef {{ x: number, y: number, z: number, groundZ: number, grounded: boolean, vz: number }} PlayerFrom
 * @param {any} p @returns {PlayerFrom}
 */
export const playerFrom = (p) => ({ x: p.x, y: p.y, z: p.z, groundZ: p.groundZ, grounded: p.grounded, vz: p.vz });

/**
 * After the player's own move (from `from`): undoes the part of it that walked into a villager's
 * body, sliding along it where it can (one axis kept). `pushing`: movement input is held (counts
 * toward the villager stepping aside, NPC_BODY.yieldMs). Mutates the player and the villager.
 * The height goes with the position: a move undone entirely puts z / groundZ / grounded back as
 * they were; a slide (one axis kept) re-reads the ground under the new spot, so the player never
 * stands for a frame at the height of a step they were stopped short of.
 * @param {any} state @param {PlayerFrom} from @param {boolean} pushing @param {number} dt seconds
 * @param {number} [stepHeight] how high a grounded player steps up (PLAYER_MOVE.stepHeight)
 * @returns {Npc | null} the villager that stopped the player, if any
 */
export function blockPlayerByNpcs(state, from, pushing, dt, stepHeight = 8) {
  const p = state.player;
  const fromX = from.x;
  const fromY = from.y;
  /** @type {Npc | null} */
  let blocker = null;
  let moved = false;
  // A villager that let the player through stays passable until they are apart.
  if (state.npcPassId) {
    const n = state.npcs.find((/** @type {Npc} */ x) => x.id === state.npcPassId);
    if (!n || npcOverlap(p.x, p.y, p, n) === 0) state.npcPassId = null;
  }
  for (let pass = 0; pass < 2; pass++) {
    for (const n of /** @type {Npc[]} */ (state.npcs)) {
      if (!npcSolid(n) || n.id === state.npcPassId || Math.abs(p.z - n.z) >= NPC_BODY.zReach) continue;
      const now = npcOverlap(p.x, p.y, p, n);
      if (now === 0 || now <= npcOverlap(fromX, fromY, p, n)) continue; // apart, or walking out
      blocker = n;
      moved = true;
      if (npcOverlap(p.x, fromY, p, n) === 0) {
        p.y = fromY;
        p.vy = 0;
      } else if (npcOverlap(fromX, p.y, p, n) === 0) {
        p.x = fromX;
        p.vx = 0;
      } else {
        p.x = fromX;
        p.y = fromY;
        p.vx = 0;
        p.vy = 0;
      }
    }
  }
  if (moved) {
    if (p.x === fromX && p.y === fromY) {
      p.z = from.z;
      p.groundZ = from.groundZ;
      p.grounded = from.grounded;
      p.vz = from.vz;
    } else if (from.grounded) {
      const ground = groundHeightUnder(p, state.map);
      p.groundZ = ground;
      if (Math.abs(ground - from.z) <= stepHeight) {
        p.z = ground;
        p.grounded = true;
        p.vz = from.vz;
      }
    }
  }
  // Pushing into the same villager for a while: it steps aside (or, with no room, lets them by).
  const push = state.npcPush;
  if (blocker && pushing && !state.dialogue) {
    const ms = push && push.id === blocker.id ? push.ms + dt * 1000 : dt * 1000;
    state.npcPush = { id: blocker.id, ms };
    if (ms >= NPC_BODY.yieldMs && !blocker.aside) {
      state.npcPush = null;
      // One who keeps their place (`stay`: the merchant, the princesses) never steps away from it
      // (it would not come back): it lets the player squeeze by instead.
      if (blocker.stay || !stepAside(state, blocker, fromX, fromY)) state.npcPassId = blocker.id;
    }
  } else if (!blocker) {
    state.npcPush = null;
  }
  return blocker;
}

/**
 * Picks a free spot beside the villager, across the player's way, and sends it there.
 * @param {any} state @param {Npc} n @param {number} fromX @param {number} fromY @returns {boolean}
 */
function stepAside(state, n, fromX, fromY) {
  const p = state.player;
  const dx = n.x - fromX;
  const dy = n.y - fromY;
  // Across the push: a mostly vertical push moves it sideways, a horizontal one up or down; the
  // side it already leans to (away from the player's line) first.
  const vertical = Math.abs(dy) >= Math.abs(dx);
  const lean = (vertical ? dx : dy) >= 0 ? 1 : -1;
  for (const s of [lean, -lean]) {
    for (const d of [NPC_BODY.asideStep, NPC_BODY.asideStep * 1.6]) {
      const x = vertical ? n.x + s * d : n.x;
      const y = vertical ? n.y : n.y + s * d;
      if (!npcSpotFree(state, x, y) || npcOverlap(p.x, p.y, p, { x, y }) > 0) continue;
      // The way there must be clear too (it walks).
      let ok = true;
      for (let k = 1; k <= 4 && ok; k++) {
        const ix = n.x + ((x - n.x) * k) / 4;
        const iy = n.y + ((y - n.y) * k) / 4;
        ok = npcSpotFree(state, ix, iy) && npcOverlap(p.x, p.y, p, { x: ix, y: iy }) === 0;
      }
      if (!ok) continue;
      n.aside = { x, y };
      return true;
    }
  }
  return false;
}

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
 *   facing: string, moving: boolean, walkTime: number, halfWidth: number, height: number, stay: boolean, reach: number, ghost: boolean, art: string,
 *   aside?: { x: number, y: number } | null }} Npc
 * stay: never strolls (a shopkeeper behind the counter, P10.1); reach: talk range (across a counter);
 * ghost: drawn see-through (v1.0); art: the name of its release frames npc.<art>.* (v1.0: the
 * princess stands in seven places under seven ids, all drawn from npc.princess.*); aside: where it
 * is stepping to, out of the player's way (v1.0 final, blockPlayerByNpcs)
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
      aside: null,
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
  for (const n of /** @type {Npc[]} */ (state.npcs)) {
    n.prevX = n.x;
    n.prevY = n.y;
    const dx = p.x - n.x;
    const dy = p.y - n.y;
    // v1.0 final: stepping out of the player's way (they kept pushing into it).
    if (n.aside && state.dialogue?.npc !== n.id) {
      const ax = n.aside.x - n.x;
      const ay = n.aside.y - n.y;
      const d = Math.hypot(ax, ay);
      const step = Math.min(d, NPC.speed * 1.5 * dt);
      if (d < 0.5 || !walkNpc(state, n, (ax / d) * step, (ay / d) * step)) {
        n.aside = null;
        n.moving = false;
        n.tx = n.x; // it strolls from here later
        n.ty = n.y;
      } else {
        n.moving = true;
        n.walkTime += dt;
        n.facing = Math.abs(ax) > Math.abs(ay) ? (ax > 0 ? 'right' : 'left') : ay > 0 ? 'down' : 'up';
      }
      continue;
    }
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
    if (!walkNpc(state, n, (tdx / dist) * step, (tdy / dist) * step)) {
      n.tx = n.x; // stuck: pick another spot next time
      n.ty = n.y;
    }
    n.moving = true;
    n.walkTime += dt;
    n.facing = Math.abs(tdx) > Math.abs(tdy) ? (tdx > 0 ? 'right' : 'left') : tdy > 0 ? 'down' : 'up';
  }
}

/**
 * Moves a villager one step: never into a wall, water, a pit, the player's body or a keep-clear tile
 * (doorways, 1-tile corridors; keepClearTiles). Returns whether it moved.
 * @param {any} state @param {Npc} n @param {number} dx @param {number} dy
 */
function walkNpc(state, n, dx, dy) {
  const map = state.map;
  const p = state.player;
  const before = { x: n.x, y: n.y };
  moveAndCollide(n, map, dx, dy, n.z);
  const i = Math.floor(n.y / map.tileSize) * map.width + Math.floor(n.x / map.tileSize);
  const clear = keepClearTiles(map, state.warps);
  const intoPlayer = npcSolid(n) && Math.abs(p.z - n.z) < NPC_BODY.zReach && npcOverlap(p.x, p.y, p, n) > npcOverlap(p.x, p.y, p, before);
  const intoClear = onKeepClear(map, clear, n.x, n.y) && !onKeepClear(map, clear, before.x, before.y);
  if (map.ground[i] === Ground.WATER || map.ground[i] === Ground.PIT || intoPlayer || intoClear) {
    n.x = before.x;
    n.y = before.y;
  }
  return Math.hypot(n.x - before.x, n.y - before.y) >= 0.01;
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
