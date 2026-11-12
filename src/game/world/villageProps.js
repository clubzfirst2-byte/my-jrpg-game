// @ts-check
// Graphics v3 (?v3=1, docs/art-release-v3/VILLAGE.md): the village's new kinds of things — fences, a
// well, signposts — placed by rules read off the map as it is (no map data changes), and solid where
// they are drawn. Added only in the v3 view (main.js), after the save's baseline is taken, so a save
// never names them (worldDiff only reads the objects of the baseline) and ?v3=0 is the game as before.
//
// The rules (village = the houses' box grown by 4 tiles):
//   fences  between two houses of the same row whose sides are 3 or more tiles apart, on the houses'
//           front row: the tiles between them, a gate left open in the middle; each run's ends are
//           "l" / "r" pieces, the inner ones "h", a run of 1 a post. Solid: their tiles.
//   well    on the free 2×2 grass nearest the houses' centre (with a tile's room round it: never by a
//           path, a door or a villager), drawn across the 2 tiles; solid: its bottom row (the stone
//           ring; the roof above is walked behind, like a tree's crown).
//   signs   where the village's road leaves the village box, on the tile beside the road (north,
//           else south), facing the way out. Solid: its tile (the post).
// A tile is free when it is in the map, flat, grass, not solid, holds no object, is not a door's front
// and is 2 or more tiles from every villager's starting place.

import { Ground } from './tilemap.js';

/** The kinds this adds (gameView draws them with the v3 village art). */
export const VILLAGE_PROP_TYPES = Object.freeze(['fence', 'well', 'signpost']);

/**
 * @param {{ width: number, height: number, ground: ArrayLike<number>, elev: ArrayLike<number>, solid: ArrayLike<number>, objects: { type: string, tx: number, ty: number }[] }} map
 * @param {{ x: number, y: number }[]} [villagers] starting places (world px)
 * @returns {{ type: string, tx: number, ty: number, kind?: string, drawDx?: number, solid: [number, number][] }[]}
 */
export function villageProps(map, villagers = []) {
  const houses = map.objects.filter((o) => o.type === 'house').sort((a, b) => a.ty - b.ty || a.tx - b.tx);
  if (!houses.length) return [];
  const W = map.width;
  const at = (/** @type {number} */ x, /** @type {number} */ y) => y * W + x;
  const inMap = (/** @type {number} */ x, /** @type {number} */ y) => x >= 0 && y >= 0 && x < W && y < map.height;
  const taken = new Set(map.objects.map((o) => at(o.tx, o.ty)));
  const doors = new Set(houses.map((h) => at(h.tx, h.ty + 1)));
  const people = villagers.map((p) => [Math.floor(p.x / 16), Math.floor(p.y / 16)]);
  /** @type {Set<number>} tiles this has used */
  const used = new Set();
  const free = (/** @type {number} */ x, /** @type {number} */ y) =>
    inMap(x, y) && map.elev[at(x, y)] === 0 && map.ground[at(x, y)] === Ground.GRASS && !map.solid[at(x, y)] && !taken.has(at(x, y)) && !doors.has(at(x, y)) && !used.has(at(x, y)) && people.every(([px, py]) => Math.max(Math.abs(px - x), Math.abs(py - y)) >= 2);
  const box = {
    x0: Math.min(...houses.map((h) => h.tx - 1)) - 4,
    x1: Math.max(...houses.map((h) => h.tx + 1)) + 4,
    y0: Math.min(...houses.map((h) => h.ty - 1)) - 4,
    y1: Math.max(...houses.map((h) => h.ty)) + 4,
  };
  /** @type {ReturnType<typeof villageProps>} */
  const out = [];

  // fences between the houses of a row
  for (let k = 0; k + 1 < houses.length; k++) {
    const a = houses[k];
    const b = houses[k + 1];
    if (a.ty !== b.ty) continue;
    const x0 = a.tx + 2;
    const x1 = b.tx - 2;
    if (x1 - x0 + 1 < 3) continue;
    const gate = Math.floor((x0 + x1) / 2);
    for (const [r0, r1] of [[x0, gate - 1], [gate + 1, x1]]) {
      const run = [];
      for (let x = r0; x <= r1; x++) if (free(x, a.ty)) run.push(x);
      run.forEach((x, n) => {
        const kind = run.length === 1 ? 'post' : n === 0 ? 'l' : n === run.length - 1 ? 'r' : 'h';
        out.push({ type: 'fence', kind, tx: x, ty: a.ty, solid: [[x, a.ty]] });
        used.add(at(x, a.ty));
      });
    }
  }

  // the well: the free 2×2 block (with free tiles round it) nearest the houses' centre
  const cx = houses.reduce((s, h) => s + h.tx, 0) / houses.length;
  const cy = houses.reduce((s, h) => s + h.ty, 0) / houses.length;
  /** @type {[number, number, number] | null} */
  let best = null;
  for (let y = box.y0; y <= box.y1; y++) {
    for (let x = box.x0 + 1; x <= box.x1; x++) {
      let ok = true;
      for (let dy = -2; dy <= 1 && ok; dy++) for (let dx = -2; dx <= 1 && ok; dx++) if (!free(x + dx, y + dy)) ok = false;
      if (!ok) continue;
      const d = (x - 0.5 - cx) ** 2 + (y - cy) ** 2;
      if (!best || d < best[2]) best = [x, y, d];
    }
  }
  if (best) {
    const [x, y] = best;
    out.push({ type: 'well', tx: x, ty: y, drawDx: -8, solid: [[x - 1, y], [x, y]] });
    for (let dy = -1; dy <= 0; dy++) for (let dx = -1; dx <= 0; dx++) used.add(at(x + dx, y + dy));
  }

  // signposts where the road leaves the village box (west and east ends of each road row)
  for (let y = box.y0; y <= box.y1; y++) {
    for (const [x, out1] of [[box.x0, box.x0 - 1], [box.x1, box.x1 + 1]]) {
      const road = (/** @type {number} */ xx) => inMap(xx, y) && map.ground[at(xx, y)] === Ground.PATH;
      if (!road(x) || !road(out1)) continue;
      const side = [y - 1, y + 1].find((yy) => free(x, yy));
      if (side === undefined) continue;
      out.push({ type: 'signpost', tx: x, ty: side, solid: [[x, side]] });
      used.add(at(x, side));
    }
  }
  return out;
}

/**
 * Adds the village's props to a state's map (solid where drawn). @param {any} state
 * @returns {number} how many
 */
export function addVillageProps(state) {
  const map = state.map;
  const props = villageProps(map, state.npcs ?? []);
  for (const p of props) {
    const { solid, ...o } = p;
    map.objects.push(o);
    for (const [x, y] of solid) map.solid[y * map.width + x] = 1;
  }
  return props.length;
}
