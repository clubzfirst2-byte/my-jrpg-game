// @ts-check
// Wind as part of the map (volume phase 1, 風切りの段丘): places where the air always moves.
//
//   wind lane (風の通り道)  a rectangle where the wind always blows one way. It carries a glider
//                            (on top of the weather's wind) and turns the vanes standing in it.
//   updraft (上昇気流)       a rectangle of rising air: a glider inside climbs, like over a fire (P5).
//   vane (風車)              a switch part (puzzles/switches.js, kind 'vane', input 'wind'): it turns
//                            while a lane's wind reaches it, or hot air rises from a fire beside it.
//
// The wind of a lane is stopped by whatever blocks movement on its way (a crate, brambles, a rock,
// a closed door): a vane behind such a thing stands still until the thing is moved, cut or burnt.
// Pure logic: no DOM, no PixiJS.

/**
 * @typedef {{ id: string, tx: number, ty: number, tw: number, th: number, dx: -1 | 0 | 1, dy: -1 | 0 | 1, speed?: number }} WindDef
 *   dx / dy: the way the air moves (one of them is 0); speed in px/s (default WIND.laneSpeed)
 * @typedef {{ id: string, tx: number, ty: number, tw: number, th: number, lift?: number }} UpdraftDef
 *   lift: how high above the ground it carries (px; default GLIDE.updraftHeight). Low under a roof.
 */

export const WIND = Object.freeze({
  /** How fast a lane carries a glider (px/s). Gliding itself is 80: against a lane you barely advance. */
  laneSpeed: 60,
});

/** @param {{ tx: number, ty: number, tw: number, th: number }} r @param {number} tx @param {number} ty */
const inside = (r, tx, ty) => tx >= r.tx && tx < r.tx + r.tw && ty >= r.ty && ty < r.ty + r.th;

/**
 * The lanes' wind at a point (px/s), summed.
 * @param {any} state @param {number} x @param {number} y @returns {{ x: number, y: number }}
 */
export function laneWindAt(state, x, y) {
  const ts = state.map.tileSize;
  const tx = Math.floor(x / ts);
  const ty = Math.floor(y / ts);
  let wx = 0;
  let wy = 0;
  for (const w of /** @type {WindDef[]} */ (state.winds ?? [])) {
    if (!inside(w, tx, ty)) continue;
    wx += w.dx * (w.speed ?? WIND.laneSpeed);
    wy += w.dy * (w.speed ?? WIND.laneSpeed);
  }
  return { x: wx, y: wy };
}

/** The rising air at a point, if any. @param {any} state @param {number} x @param {number} y @returns {UpdraftDef | null} */
export function updraftAt(state, x, y) {
  const ts = state.map.tileSize;
  const tx = Math.floor(x / ts);
  const ty = Math.floor(y / ts);
  return (state.updrafts ?? []).find((/** @type {UpdraftDef} */ u) => inside(u, tx, ty)) ?? null;
}

/**
 * Whether a lane's wind reaches a tile: the tile is in the lane and nothing solid stands between it
 * and the edge of the lane the wind comes from.
 * @param {any} state @param {number} tx @param {number} ty
 */
export function windReaches(state, tx, ty) {
  const map = state.map;
  for (const w of /** @type {WindDef[]} */ (state.winds ?? [])) {
    if (!inside(w, tx, ty) || (!w.dx && !w.dy)) continue;
    let x = tx - w.dx;
    let y = ty - w.dy;
    let open = true;
    while (inside(w, x, y)) {
      if (map.solid[y * map.width + x]) {
        open = false;
        break;
      }
      x -= w.dx;
      y -= w.dy;
    }
    if (open) return true;
  }
  return false;
}

/**
 * Whether a vane on tile i turns now: wind from a lane, or hot air from a fire on a tile beside it
 * (the eight around it).
 * @param {any} state @param {number} i
 */
export function vaneTurns(state, i) {
  const map = state.map;
  const tx = i % map.width;
  const ty = (i / map.width) | 0;
  if (windReaches(state, tx, ty)) return true;
  for (let dy = -1; dy <= 1; dy++) {
    for (let dx = -1; dx <= 1; dx++) {
      if (!dx && !dy) continue;
      const x = tx + dx;
      const y = ty + dy;
      if (x >= 0 && y >= 0 && x < map.width && y < map.height && state.env.burning.has(y * map.width + x)) return true;
    }
  }
  return false;
}
