// @ts-check
// Graphics v3 (?v3=1): the plains' v3 ground, trees and props (docs/art-release-v3/STYLE.md 6, 7.1b, 7.2).
// Pure (no PixiJS): the view (gameView.js) asks it which picture goes where; the unit tests compare it
// with the art side's reference (tools/art_v3/gen_ground_v3.py: macro_of, flow_corner, flow_key, and
// tools/terrain_v2/render_ref.py for the grass edges) through tests/fixtures/ground_v3_ref.json.
//
// The ground of a plains display tile (i, j) (the dual grid's tile, corners = the cells (i, j) .. (i+1, j+1)):
//   1. the base: one tile of the 8 patterns of 4×4 tiles, <s.>plains.grass.v3.<m><j%4><i%4> with
//      m = macroOf(⌊i/4⌋, ⌊j/4⌋) (the first of a hashed order of a..h that is not the pattern of the block
//      on the left, above, above-left or above-right)
//   2. the flow (only on a display tile whose 4 corners are plains): flowKey(i, j) = (kind, corners, v),
//      <s.>plains.grassflow.v3.<d|l><corners>.<v>, v used as it comes (0-7 where the border crosses 2
//      sides, else 0-1). A world corner whose 4 display tiles are not all full plains has no flow ('m'),
//      so the flow fades out before the grass edges.
//   3. the grass edges over a lower ground: <s.>plains.grass.v3.edge.<mask>.<v>, mask and v by the v2
//      rule (groundV2.edgeVariantOf), the v2 key's name with ".v3" in it.
// <s.> is "" in summer and spring, "autumn." or "winter." (v3Season).

/** The 8 base patterns. */
export const PATTERNS = Object.freeze(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']);

/** gen_ground_v3.hsh: an unsigned 32-bit hash of a lattice point and a seed (as Python computes it). @param {number} x @param {number} y @param {number} [s] */
export function hsh(x, y, s = 0) {
  let h = (Math.imul(x | 0, 374761393) + Math.imul(y | 0, 668265263) + Math.imul(s | 0, 2147483647)) >>> 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177) >>> 0;
  return (h ^ (h >>> 16)) >>> 0;
}

/** The v3 art's season ("summer" for spring and for no season). @param {string | null | undefined} season @returns {'summer' | 'autumn' | 'winter'} */
export const v3Season = (season) => (season === 'autumn' || season === 'winter' ? season : 'summer');

/** The file prefix of a v3 season ("", "autumn.", "winter."). @param {string | null | undefined} season */
export const seasonPrefix = (season) => {
  const s = v3Season(season);
  return s === 'summer' ? '' : `${s}.`;
};

/**
 * gen_ground_v3.macro_of: the base pattern of each block of 4×4 display tiles. Memoised, computed row by
 * row without recursion (a block depends on the row above up to one block further right).
 */
export class MacroGrid {
  constructor() {
    /** @type {Map<number, string[]>} row by → patterns of blocks 0, 1, 2, ... */
    this.rows = new Map();
  }

  /** @param {number} bx @param {number} by @returns {string} */
  at(bx, by) {
    if (bx < 0 || by < 0) return this.pick(bx, by);
    this.fill(by, bx);
    return /** @type {string[]} */ (this.rows.get(by))[bx];
  }

  /** Row `by` known up to block `bx` (and the rows above it as far as it needs). @param {number} by @param {number} bx */
  fill(by, bx) {
    /** @type {[number, number][]} */
    const todo = [];
    for (let y = by, x = bx; y >= 0; y--, x++) {
      const row = this.rows.get(y);
      if (row && row.length > x) break;
      todo.push([y, x]);
    }
    for (let k = todo.length - 1; k >= 0; k--) {
      const [y, x] = todo[k];
      let row = this.rows.get(y);
      if (!row) this.rows.set(y, (row = []));
      for (let i = row.length; i <= x; i++) row.push(this.pick(i, y));
    }
  }

  /** One block, its neighbours above already known (the order is the reference's). @param {number} bx @param {number} by */
  pick(bx, by) {
    const near = new Set();
    if (bx > 0) near.add(this.known(bx - 1, by));
    if (by > 0) {
      near.add(this.known(bx, by - 1));
      near.add(this.known(bx + 1, by - 1));
      if (bx > 0) near.add(this.known(bx - 1, by - 1));
    }
    const order = PATTERNS.map((m) => ({ m, h: hsh(bx * 7 + m.charCodeAt(0), by * 13 + m.charCodeAt(0), 91) }))
      .sort((a, b) => a.h - b.h)
      .map((e) => e.m);
    return order.find((m) => !near.has(m)) ?? order[0];
  }

  /** @param {number} bx @param {number} by */
  known(bx, by) {
    if (bx < 0 || by < 0) return this.pick(bx, by);
    const row = this.rows.get(by);
    if (row && row.length > bx) return row[bx];
    return this.at(bx, by);
  }
}

/** The base tile key of display tile (i, j). @param {MacroGrid} macro @param {string | null | undefined} season @param {number} i @param {number} j */
export function baseKey(macro, season, i, j) {
  const m4 = (/** @type {number} */ v) => ((v % 4) + 4) % 4;
  return `${seasonPrefix(season)}plains.grass.v3.${macro.at(Math.floor(i / 4), Math.floor(j / 4))}${m4(j)}${m4(i)}`;
}

/** gen_ground_v3._value_noise. @param {number} x @param {number} y @param {number} scale @param {number} seed */
function valueNoise(x, y, scale, seed) {
  const gx = x / scale;
  const gy = y / scale;
  const x0 = Math.floor(gx);
  const y0 = Math.floor(gy);
  const fx = gx - x0;
  const fy = gy - y0;
  const sx = fx * fx * (3 - 2 * fx);
  const sy = fy * fy * (3 - 2 * fy);
  const r = (/** @type {number} */ i, /** @type {number} */ j) => (hsh(i, j, seed) % 10000) / 10000.0;
  const a = r(x0, y0) + (r(x0 + 1, y0) - r(x0, y0)) * sx;
  const b = r(x0, y0 + 1) + (r(x0 + 1, y0 + 1) - r(x0, y0 + 1)) * sx;
  return a + (b - a) * sy;
}

/** gen_ground_v3.flow_value. @param {number} cx @param {number} cy */
export const flowValue = (cx, cy) => 0.65 * valueNoise(cx, cy, 6.0, 1) + 0.35 * valueNoise(cx, cy, 3.0, 2);

/** @param {number} x @param {number} y @returns {'d' | 'l' | 'm'} */
const rawCorner = (x, y) => {
  const v = flowValue(x, y);
  return v < 0.32 ? 'd' : v > 0.66 ? 'l' : 'm';
};
const AROUND = Object.freeze([[1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [-1, -1], [1, -1], [-1, 1]]);

/**
 * gen_ground_v3.flow_corner: a world corner's flow, 'd' (thick, dark), 'l' (thin, sunny) or 'm' (none);
 * a corner next to the opposite state is 'm'. @param {number} cx @param {number} cy @returns {'d' | 'l' | 'm'}
 */
export function flowCorner(cx, cy) {
  const st = rawCorner(cx, cy);
  if (st === 'm') return st;
  const opp = st === 'd' ? 'l' : 'd';
  for (const [dx, dy] of AROUND) if (rawCorner(cx + dx, cy + dy) === opp) return 'm';
  return st;
}

/** The sides a border crosses (its 2 corners differ), N E S W. bits: TL TR BR BL. @param {string} bits @returns {('N' | 'E' | 'S' | 'W')[]} */
export function crossed(bits) {
  const [tl, tr, br, bl] = [...bits].map((b) => b === '1');
  /** @type {('N' | 'E' | 'S' | 'W')[]} */
  const out = [];
  if (tl !== tr) out.push('N');
  if (tr !== br) out.push('E');
  if (bl !== br) out.push('S');
  if (tl !== bl) out.push('W');
  return out;
}

/** How many flow variants a corner set has (8 where the border crosses 2 sides, else 2). @param {string} bits */
export const flowVariants = (bits) => {
  const n = crossed(bits).length;
  return n === 2 ? 8 : 2;
};

/** gen_ground_v3.side_state: a side's state 0 / 1, the same for both tiles sharing it. @param {number} i @param {number} j @param {'N' | 'E' | 'S' | 'W'} side */
export function sideState(i, j, side) {
  const h = side === 'N' ? hsh(2 * i + 1, 2 * j, 61) : side === 'E' ? hsh(2 * i + 2, 2 * j + 1, 61) : side === 'S' ? hsh(2 * i + 1, 2 * j + 2, 61) : hsh(2 * i, 2 * j + 1, 61);
  return (h >>> 4) & 1;
}

/**
 * gen_ground_v3.flow_key: (kind, corners TL TR BR BL, v) of display tile (i, j), or null (no flow).
 * `corner` gives a world corner's state (the game's: flowCorner, 'm' where the 4 display tiles around the
 * corner are not all full plains). @param {number} i @param {number} j
 * @param {(cx: number, cy: number) => 'd' | 'l' | 'm'} [corner]
 * @returns {[string, string, number] | null}
 */
export function flowKey(i, j, corner = flowCorner) {
  const cs = [corner(i, j), corner(i + 1, j), corner(i + 1, j + 1), corner(i, j + 1)];
  const kinds = [...new Set(cs.filter((k) => k !== 'm'))].sort();
  if (!kinds.length) return null;
  const kind = kinds[0];
  const bits = cs.map((k) => (k === kind ? '1' : '0')).join('');
  const sides = crossed(bits);
  const v = sides.length === 2 ? sideState(i, j, sides[0]) + 2 * sideState(i, j, sides[1]) + 4 * (hsh(i, j, 34) % 2) : hsh(i, j, 33) % 2;
  return [kind, bits, v];
}

/** The key of a flow tile. @param {string | null | undefined} season @param {[string, string, number]} fk */
export const flowTileKey = (season, fk) => `${seasonPrefix(season)}plains.grassflow.v3.${fk[0]}${fk[1]}.${fk[2]}`;

/**
 * How a flow tile is drawn: its texture key and a tint (0xffffff: as painted). The one place to change
 * when the flow comes as shapes coloured by the game (inspect_v3_pilot.md, production 3rd check, memory
 * (1): one alpha shape per corners / v shared by d and l, its colour multiplied in): FLOW_SHAPE then
 * names the shape's key and FLOW_TINT the colour per season and kind, and this returns them.
 * @param {string | null | undefined} season @param {[string, string, number]} fk
 * @param {(key: string) => boolean} has whether a texture is loaded
 * @returns {{ key: string, tint: number } | null}
 */
export function flowLook(season, fk, has) {
  const painted = flowTileKey(season, fk);
  if (has(painted)) return { key: painted, tint: 0xffffff };
  const shape = FLOW_SHAPE(fk);
  const tint = FLOW_TINT[v3Season(season)]?.[fk[0]];
  if (shape && tint !== undefined && has(shape)) return { key: shape, tint };
  return null;
}

/** The shared shape of a flow tile (none yet: the flow is painted per season and kind). @param {[string, string, number]} fk @returns {string | null} */
// eslint-disable-next-line no-unused-vars
export const FLOW_SHAPE = (fk) => null;
/** The flow's colour per season and kind when drawn from shapes (none yet). @type {Record<string, Record<string, number>>} */
export const FLOW_TINT = {};

/** The v3 key of the plains grass edge over a lower ground (v2's "plains.grass.edge.<mask>.<v>"). @param {string | null | undefined} season @param {string} v2Name e.g. "edge.5.2" */
export const edgeKey = (season, v2Name) => `${seasonPrefix(season)}plains.grass.v3.${v2Name}`;

/** Whether a key is plains v3 art (the bundles "v3:plains:<season>"). @param {string} key @returns {'summer' | 'autumn' | 'winter' | null} */
export function v3PlainsSeasonOf(key) {
  const m = /^(?:(autumn|winter)\.)?plains\.(?:grass|grassflow|tree|prop)\.v3\./.exec(key);
  if (!m) return null;
  return /** @type {'autumn' | 'winter' | undefined} */ (m[1]) ?? 'summer';
}

/** The bundle of a season's plains v3 art. @param {string | null | undefined} season */
export const v3PlainsBundle = (season) => `v3:plains:${v3Season(season)}`;

// --- trees (STYLE.md 7.1b) and props (7.2) ---

/** The trees: art size in game px (the art is 4 px per game px) and sway frames per season. */
export const TREES = Object.freeze({
  oak_l: { w: 40, h: 56 },
  oak_m: { w: 28, h: 40 },
  pine: { w: 24, h: 50 },
  sapling: { w: 16, h: 28 },
});

/**
 * Which v3 tree a plains tree is drawn as (only the drawing: the tree's tile, collision and saves stay).
 * `room` is the free distance around it in tiles (1 = something on a next tile, 3 = nothing within 2):
 * the large broadleaf only with nothing within 2 tiles (its crown is 2.5 tiles wide), the middle one or
 * the pine with nothing on the next tiles, the sapling (1 tile, as the v1 tree) in a grove or next to a
 * house, wall or another object. Within its room the kind is by the tree's hash, so a stand of trees
 * mixes them: room 3 → oak_l 45%, pine 30%, oak_m 25%; room 2 → oak_m 50%, pine 35%, sapling 15%;
 * room 1 → sapling.
 * @param {number} room @param {number} h 0..1 (the tree's own hash)
 * @returns {keyof typeof TREES}
 */
export function treeKind(room, h) {
  if (room >= 3) return h < 0.45 ? 'oak_l' : h < 0.75 ? 'pine' : 'oak_m';
  if (room === 2) return h < 0.5 ? 'oak_m' : h < 0.85 ? 'pine' : 'sapling';
  return 'sapling';
}

/** Sway frames: trees 0 / +1 / -1 texel (loop 0 1 0 2), grass and flowers 0 / 1. */
export const TREE_SWAY = Object.freeze([0, 1, 0, 2]);
export const PROP_SWAY = Object.freeze([0, 1]);
/** Seconds per sway step: the wind is slow (one 4-step tree sway in about 3 s). */
export const SWAY_STEP_SEC = 0.75;
/** How far the wind's gust moves per second, in tiles (a wave runs across a stand of trees). */
const GUST_TILES_PER_SEC = 4;

/**
 * The sway step of something at tile (tx, ty) at time t (seconds): a slow wave across the field (the
 * gust reaches the trees further east later), with a little per-object lag so neighbours do not move in
 * step. @param {number} tx @param {number} ty @param {number} t
 */
export function swayStep(tx, ty, t) {
  const lag = (hsh(tx, ty, 977) % 3) * 0.25;
  return Math.floor((t - (tx + ty * 0.5) / GUST_TILES_PER_SEC) / SWAY_STEP_SEC + lag);
}

/** The frame of a sway cycle at a step. @param {readonly number[]} cycle @param {number} frames how many frames the art has @param {number} step */
export function swayFrame(cycle, frames, step) {
  if (frames <= 1) return 0;
  const f = cycle[((step % cycle.length) + cycle.length) % cycle.length];
  return f < frames ? f : 0;
}

/**
 * The props (STYLE.md 7.2), drawn only (nothing to bump into, never saved). Size in game px; `frames`
 * sway frames; `solid`: it looks like something one would bump into (a rock, a log, a bush), so it is
 * only drawn where the player cannot walk anyway — at the foot of a tree, on the tree's own tile, or as
 * a tree's own picture (the log; the stump of a burnt tree, which the game lets one walk past) — never
 * on open ground the player walks over.
 */
export const PROPS = Object.freeze({
  tuft: { w: 8, h: 6, frames: 2, solid: false },
  tallgrass: { w: 10, h: 10, frames: 2, solid: false },
  flowers_mix: { w: 12, h: 8, frames: 2, solid: false },
  flowers_white: { w: 12, h: 8, frames: 2, solid: false },
  flowers_yellow: { w: 12, h: 8, frames: 2, solid: false },
  clover: { w: 10, h: 5, frames: 1, solid: false },
  pebbles: { w: 10, h: 5, frames: 1, solid: false },
  mushrooms: { w: 8, h: 6, frames: 1, solid: false },
  shrub: { w: 8, h: 8, frames: 1, solid: false },
  bush: { w: 16, h: 12, frames: 1, solid: true },
  bush_berry: { w: 16, h: 12, frames: 1, solid: true },
  rock_s: { w: 8, h: 6, frames: 1, solid: true },
  rock_m: { w: 12, h: 9, frames: 1, solid: true },
  stump: { w: 12, h: 10, frames: 1, solid: true },
  log: { w: 16, h: 7, frames: 1, solid: true },
});

/** @typedef {keyof typeof PROPS} PropKind */

/**
 * The prop on an open grass tile (walkable, nothing on it, grass all round), or null. Patches by a slow
 * noise (`patch` 0..1 at the tile, `flowerNoise` 0..1 for which flower leads a patch), about 1 tile in 9
 * inside a patch and 1 in 40 outside; flowers gather in their patches, mushrooms only near trees.
 * @param {number} patch @param {number} flowerNoise @param {number} h 0..1 whether there is one @param {number} h2 0..1 which
 * @param {boolean} nearTree a tree within 2 tiles
 * @returns {PropKind | null}
 */
export function openProp(patch, flowerNoise, h, h2, nearTree) {
  const inPatch = patch > 0.55;
  if (h > (inPatch ? 0.11 + 0.25 * (patch - 0.55) : 0.025)) return null;
  if (nearTree && h2 < 0.12) return 'mushrooms';
  if (inPatch && h2 < 0.55) return flowerNoise < 0.36 ? 'flowers_mix' : flowerNoise < 0.66 ? 'flowers_yellow' : 'flowers_white';
  if (h2 < 0.72) return 'tuft';
  if (h2 < 0.84) return 'tallgrass';
  if (h2 < 0.91) return 'clover';
  if (h2 < 0.96) return 'shrub';
  return 'pebbles';
}

/**
 * The prop at the foot of a tree (on the tree's own tile, which the player cannot walk on), or null:
 * about 1 tree in 4. A bush or a berry bush in front of the trunk, a rock beside it, mushrooms.
 * (The stump is a burnt tree's own picture, the log a grove tree's: plainsTreeLook.)
 * @param {number} h 0..1 whether @param {number} h2 0..1 which
 * @returns {PropKind | null}
 */
export function treeFootProp(h, h2) {
  if (h > 0.26) return null;
  if (h2 < 0.34) return 'bush';
  if (h2 < 0.54) return 'bush_berry';
  if (h2 < 0.74) return 'rock_s';
  if (h2 < 0.86) return 'rock_m';
  return 'mushrooms';
}

/**
 * How a plains tree object is drawn: a v3 tree by its room (treeKind), or, for 1 grove tree in 16, a
 * fallen log (still the same solid tile; burnt, it becomes a stump as any tree). @param {number} room @param {number} h @param {number} h2
 * @returns {{ what: 'tree' | 'prop', kind: string }}
 */
export function plainsTreeLook(room, h, h2) {
  if (room <= 1 && h2 < 1 / 16) return { what: 'prop', kind: 'log' };
  return { what: 'tree', kind: treeKind(room, h) };
}

/** The key of a tree / prop frame. @param {string | null | undefined} season @param {'tree' | 'prop'} what @param {string} kind @param {number} frame */
export const floraKey = (season, what, kind, frame) => `${seasonPrefix(season)}plains.${what}.v3.${kind}.${frame}`;

/** How many frames of a tree / prop are loaded. @param {(key: string) => boolean} has @param {string | null | undefined} season @param {'tree' | 'prop'} what @param {string} kind */
export function floraFrames(has, season, what, kind) {
  let n = 0;
  while (n < 4 && has(floraKey(season, what, kind, n))) n++;
  return n;
}
