// @ts-check
// Island features (P3.5, DESIGN.md 5.9): chests, checkpoints (respawn stones), warps (cave doorways),
// areas (camera bounds for interiors), landmarks, and the player's progress that is saved.
// Pure logic: no DOM, no PixiJS.
import { openDoors } from '../env/envSim.js';

export const MAX_HEARTS = 6;
/** How close (px) the player must be to touch a checkpoint / open a chest. */
const TOUCH_RANGE = 14;
const OPEN_RANGE = 20;

/**
 * @typedef {{ id: string, tx: number, ty: number, reward: 'heart' | 'treasure' }} ChestDef
 * @typedef {{ id: string, tx: number, ty: number }} CheckpointDef
 * @typedef {{ id: string, tx: number, ty: number, facing: 'up' | 'down' | 'left' | 'right', toTx: number, toTy: number, reveal?: boolean }} WarpDef  reveal: draw a cave opening on the cliff above
 * @typedef {{ id: string, tx: number, ty: number, tw: number, th: number }} AreaDef
 * @typedef {{ id: string, name: string, tx: number, ty: number, always: boolean }} LandmarkDef
 *
 * @typedef {object} Progress  what is saved (DESIGN.md 2.6)
 * @property {string[]} openedChests
 * @property {string[]} checkpoints     activated checkpoint ids
 * @property {string | null} checkpoint the one the player respawns at
 * @property {string[]} landmarks       discovered landmark ids
 * @property {number} treasures
 * @property {number} maxHp             quarter hearts
 * @property {string[]} gates           doors opened by powering their receiver (P4)
 */

/** @returns {Progress} */
export function emptyProgress() {
  return { openedChests: [], checkpoints: [], checkpoint: null, landmarks: [], treasures: 0, maxHp: 12, gates: [] };
}

/** Feet position at the center-bottom of a tile. @param {any} map @param {number} tx @param {number} ty */
export function tileFeet(map, tx, ty) {
  const ts = map.tileSize;
  return { x: tx * ts + ts / 2, y: ty * ts + ts - 2 };
}

/**
 * Chests and campfires block movement.
 * @param {any} state
 */
export function placeFeatureSolids(state) {
  const map = state.map;
  for (const c of [...state.chests, ...state.campfires]) map.solid[c.ty * map.width + c.tx] = 1;
}

/**
 * The chest in front of the player within reach, if any (closed chests only).
 * @param {any} state
 */
export function chestInReach(state) {
  const p = state.player;
  const ts = state.map.tileSize;
  let best = null;
  let bestD = Infinity;
  for (const c of state.chests) {
    if (state.progress.openedChests.includes(c.id)) continue;
    const cx = c.tx * ts + ts / 2;
    const cy = c.ty * ts + ts / 2;
    const dx = cx - p.x;
    const dy = cy - (p.y - 3);
    const d = Math.hypot(dx, dy);
    // In reach and roughly in front of the player.
    if (d < OPEN_RANGE && dx * p.aimX + dy * p.aimY > 0 && Math.abs(p.z - (state.map.elev[c.ty * state.map.width + c.tx] ?? 0)) < 12 && d < bestD) {
      best = c;
      bestD = d;
    }
  }
  return best;
}

/**
 * Opens a chest and applies its reward.
 * @param {any} state @param {ChestDef} c
 */
export function openChest(state, c) {
  const pr = state.progress;
  if (pr.openedChests.includes(c.id)) return;
  pr.openedChests.push(c.id);
  if (c.reward === 'heart') {
    pr.maxHp = Math.min(MAX_HEARTS * 4, pr.maxHp + 4);
    state.player.maxHp = pr.maxHp;
    state.player.hp = pr.maxHp; // a new heart container also refills
  } else {
    pr.treasures += 1;
  }
  state.events.push({ type: 'chest', tick: state.tick, reward: c.reward, id: c.id });
  state.saveRequested = true;
}

/**
 * Touching a checkpoint activates it and makes it the respawn point.
 * @param {any} state
 */
export function touchCheckpoints(state) {
  const p = state.player;
  if (!p.grounded) return;
  for (const c of state.checkpointDefs) {
    const f = tileFeet(state.map, c.tx, c.ty);
    if (Math.hypot(f.x - p.x, f.y - p.y) > TOUCH_RANGE) continue;
    const pr = state.progress;
    if (pr.checkpoint === c.id) continue;
    if (!pr.checkpoints.includes(c.id)) pr.checkpoints.push(c.id);
    pr.checkpoint = c.id;
    state.events.push({ type: 'checkpoint', tick: state.tick, id: c.id });
    state.saveRequested = true;
  }
}

/**
 * Stepping onto a doorway while facing its direction moves the player to the other side.
 * @param {any} state @returns {boolean} whether a warp happened
 */
export function checkWarps(state) {
  const p = state.player;
  if (!p.grounded || p.dead) return false;
  const ts = state.map.tileSize;
  const tx = Math.floor(p.x / ts);
  const ty = Math.floor((p.y - p.height / 2) / ts);
  for (const w of state.warps) {
    if (w.tx !== tx || w.ty !== ty || p.facing !== w.facing) continue;
    const f = tileFeet(state.map, w.toTx, w.toTy);
    p.x = p.prevX = f.x;
    p.y = p.prevY = f.y;
    p.z = p.prevZ = p.groundZ = state.map.elev[w.toTy * state.map.width + w.toTx];
    p.vx = p.vy = p.vz = 0;
    state.events.push({ type: 'warp', tick: state.tick, id: w.id });
    return true;
  }
  return false;
}

/**
 * The area (interior) containing a point, or null for the outdoors.
 * @param {any} state @param {number} x @param {number} y @returns {AreaDef | null}
 */
export function areaAt(state, x, y) {
  const ts = state.map.tileSize;
  for (const a of state.areas) {
    if (x >= a.tx * ts && x < (a.tx + a.tw) * ts && y >= a.ty * ts && y < (a.ty + a.th) * ts) return a;
  }
  return null;
}

/**
 * Landmarks get "discovered" when seen up close or from high ground (DESIGN.md 5.9).
 * @param {any} state @param {number} viewRadius px
 */
export function discoverLandmarks(state, viewRadius) {
  const p = state.player;
  const high = p.z >= HIGH_GROUND_PX;
  for (const l of state.landmarks) {
    if (state.progress.landmarks.includes(l.id)) continue;
    const f = tileFeet(state.map, l.tx, l.ty);
    if (l.always || high || Math.hypot(f.x - p.x, f.y - p.y) < viewRadius) {
      state.progress.landmarks.push(l.id);
      state.events.push({ type: 'landmark', tick: state.tick, id: l.id });
    }
  }
}

/** Standing this high (2 levels) counts as a lookout. */
export const HIGH_GROUND_PX = 32;

/**
 * Where the player respawns: the active checkpoint, else the map's start.
 * @param {any} state
 */
export function respawnPoint(state) {
  const id = state.progress.checkpoint;
  const c = id ? state.checkpointDefs.find((/** @type {CheckpointDef} */ d) => d.id === id) : null;
  if (!c) return { ...state.map.spawn };
  // Stand just south of the stone (it is not solid, but this keeps the player off it).
  return tileFeet(state.map, c.tx, c.ty + 1);
}

/**
 * Applies saved progress to a fresh game state.
 * @param {any} state @param {Progress} saved
 */
export function applyProgress(state, saved) {
  const pr = { ...emptyProgress(), ...saved };
  pr.openedChests = [...pr.openedChests];
  pr.checkpoints = [...pr.checkpoints];
  pr.landmarks = [...pr.landmarks];
  pr.gates = [...pr.gates];
  state.progress = pr;
  if (state.env) for (const link of pr.gates) openDoors(state.env, state.map, link);
  state.player.maxHp = pr.maxHp;
  state.player.hp = pr.maxHp;
}
