// Volume phase 1: the ways through the air in 風切りの段丘, flown with the real game step.
// Shared by terrace.test.js (each route works) and playthrough.test.js (the routes join the shelves
// for the "everything can be reached" check, which has no gliding of its own).
import { createGameState, stepGame } from '../../src/game/state.js';
import { WORLD } from '../../src/game/world/world.js';
import { tileFeet } from '../../src/game/world/features.js';

export const none = { moveX: 0, moveY: 0, dash: false, jump: false, attack: false, dodge: false, guard: false, bow: false, ability: false };
const R = WORLD.regions.find((x) => x.id === 'terrace');
/** A tile of the terrace (its own coordinates) in world coordinates. */
export const T = (x, y) => ({ tx: R.tx + x, ty: R.ty + y });

export function terraceState() {
  const s = createGameState(WORLD);
  s.enemies = [];
  s.enemySpawns = [];
  return s;
}
export function place(s, { tx, ty }, facing) {
  const f = tileFeet(s.map, tx, ty);
  const p = s.player;
  Object.assign(p, { x: f.x, y: f.y, prevX: f.x, prevY: f.y, vx: 0, vy: 0, vz: 0, swimming: false, gliding: false, climbing: false });
  p.z = p.prevZ = p.groundZ = s.map.elev[ty * s.map.width + tx];
  p.grounded = true;
  p.safeX = p.x;
  p.safeY = p.y;
  p.safeZ = p.z;
  p.facing = facing;
  const v = { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] }[facing];
  p.aimX = v[0];
  p.aimY = v[1];
}
export const run = (s, input, n) => {
  for (let i = 0; i < n; i++) stepGame(s, input);
};

/**
 * from: where the player stands before the jump (terrace tiles). dir: the way held all the flight.
 * hover: seconds to hang still after opening the glider (to rise in an updraft). to: the rectangle
 * (terrace tiles, inclusive) the player must come down in, and the least height (px) of that ground.
 */
export const AIR_ROUTES = [
  { id: 'K1-east', note: 'the first glide: from the knoll over the first rift to the middle shelf', from: [27, 46], dir: [1, 0], to: { x0: 35, x1: 58, y0: 40, y1: 52, z: 0 } },
  { id: 'K3-east', note: 'the wind lane carries the glider over the second rift to the east shelf', from: [58, 59], dir: [1, 0], to: { x0: 72, x1: 92, y0: 54, y1: 64, z: 0 } },
  { id: 'U1-high', note: 'the updraft lifts the glider up onto the high terrace', from: [81, 43], dir: [0, -1], hover: 0, to: { x0: 73, x1: 91, y0: 6, y1: 35, z: 64 } },
  { id: 'L2-home', note: 'from the high terrace the west wind carries back to the middle shelf', from: [73, 17], dir: [-1, 0], to: { x0: 35, x1: 58, y0: 10, y1: 24, z: 0 } },
  { id: 'L2-west', note: 'and on over the first rift to the west shelf', from: [35, 17], dir: [-1, 0], to: { x0: 3, x1: 27, y0: 10, y1: 24, z: 0 } },
  { id: 'K2-west', note: 'the way back west by hand: from the knoll on the middle shelf', from: [35, 66], dir: [-1, 0], to: { x0: 3, x1: 27, y0: 60, y1: 72, z: 0 } },
  { id: 'K4-west', note: 'the way back west by hand: from the bluff on the east shelf', from: [72, 81], dir: [-1, 0], to: { x0: 35, x1: 58, y0: 76, y1: 86, z: 0 } },
  { id: 'U0-mound', note: 'the updraft beside 風見の塚 lifts onto the mound', from: [12, 80], dir: [1, 0], to: { x0: 18, x1: 23, y0: 76, y1: 83, z: 48 } },
];

/**
 * Flies a route: a jump, the glider opened near the top of the jump, the direction held until the
 * player is on the ground again (or has fallen into a rift).
 * @param {(typeof AIR_ROUTES)[number]} route @param {{ winds?: boolean, updrafts?: boolean }} [opt]
 */
export function flyRoute(route, opt = {}) {
  const s = terraceState();
  if (opt.winds === false) s.winds = [];
  if (opt.updrafts === false) s.updrafts = [];
  const [dx, dy] = route.dir;
  place(s, T(route.from[0], route.from[1]), dx > 0 ? 'right' : dx < 0 ? 'left' : dy < 0 ? 'up' : 'down');
  const move = { ...none, moveX: dx, moveY: dy };
  const p = s.player;
  stepGame(s, { ...move, jump: true });
  run(s, move, 11);
  stepGame(s, { ...move, jump: true }); // near the top of the jump: the glider opens
  const opened = p.gliding;
  if (route.hover) run(s, none, Math.round(route.hover * 60));
  let fell = false;
  for (let i = 0; i < 60 * 20; i++) {
    stepGame(s, move);
    if (s.events.some((e) => e.type === 'fell')) {
      fell = true;
      break;
    }
    if (p.grounded && !p.climbing) break;
  }
  const at = { tx: Math.floor(p.x / 16) - R.tx, ty: Math.floor(p.y / 16) - R.ty };
  const t = route.to;
  const landed = !fell && p.grounded && at.tx >= t.x0 && at.tx <= t.x1 && at.ty >= t.y0 && at.ty <= t.y1 && p.z >= t.z;
  return { s, opened, fell, landed, at, z: p.z };
}
