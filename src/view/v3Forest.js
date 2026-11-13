// @ts-check
// Graphics v3 (?v3=1): the forest's v3 ground, trees and props (docs/art-release-v3/FOREST.md, NAMES.md 1-3,
// 2.1). Pure (no PixiJS): the view (gameView.js) asks it which picture goes where; the unit tests compare
// it with the art side's reference (tools/art_v3/compare_forest_v3.py) through tests/fixtures/forest_v3_ref.json.
//
// The forest ground of a display tile is drawn with the plains' rules (v3Plains.js), only the names and the
// flow colours differ (FOREST.md 1):
//   1. the base <s.>forest.grass.v3.<m><j%4><i%4>, m = macro_of(⌊i/4⌋, ⌊j/4⌋) (the plains' MacroGrid)
//   2. the flow on a full forest tile: flowKey (the plains' flow_corner / flow_key, a corner 'm' unless its 4
//      display tiles are full forest), <set.>forest.grassflow.v3.<bits>.<v> × FOREST_FLOW_TINT[season][kind]
//   3. the forest edges over a lower ground: <s.>forest.grass.v3.edge.<mask>.<v>, mask and v by the v2 rule
//   4. winter only (NAMES.md 2.1): on a display tile with both forest and plains corners the two exchange
//      places in the priority (winterPriority), so the plains winter base is drawn and the forest winter
//      edge over it (mask = the forest corners); every mask a v reads is read in its own tile's order.
import { PRIORITY } from './groundV2.js';
import { hsh, seasonPrefix, v3Season, flowSet } from './v3Plains.js';

/** FOREST_FLOW_TINT[season][kind] (FOREST.md 1, gen_forest_v3.flow_tints). */
export const FOREST_FLOW_TINT = Object.freeze({
  summer: Object.freeze({ d: 0x1a3830, l: 0x2d5632 }),
  autumn: Object.freeze({ d: 0x4a3c20, l: 0x544c28 }),
  winter: Object.freeze({ d: 0xaabcd6, l: 0xfafcff }),
});

/** The base tile key of display tile (i, j). @param {import('./v3Plains.js').MacroGrid} macro @param {string | null | undefined} season @param {number} i @param {number} j */
export function forestBaseKey(macro, season, i, j) {
  const m4 = (/** @type {number} */ v) => ((v % 4) + 4) % 4;
  return `${seasonPrefix(season)}forest.grass.v3.${macro.at(Math.floor(i / 4), Math.floor(j / 4))}${m4(j)}${m4(i)}`;
}

/** The v3 key of a forest edge over a lower ground (v2's "forest.grass.edge.<mask>.<v>"). @param {string | null | undefined} season @param {string} v2Name e.g. "edge.5.2" */
export const forestEdgeKey = (season, v2Name) => `${seasonPrefix(season)}forest.grass.v3.${v2Name}`;

/**
 * How a forest flow tile is drawn (as v3Plains.flowLook): its grey shape, the colour it is multiplied by,
 * whether it is mirrored; null when its picture is not loaded.
 * @param {string | null | undefined} season @param {import('./v3Plains.js').FlowKey} fk @param {(key: string) => boolean} has
 * @returns {{ key: string, tint: number, flip: boolean } | null}
 */
export function forestFlowLook(season, fk, has) {
  const key = `${flowSet(season)}forest.grassflow.v3.${fk[1]}.${fk[2]}`;
  const tint = /** @type {Record<string, number>} */ (FOREST_FLOW_TINT[v3Season(season)])[fk[0]];
  return has(key) && tint !== undefined ? { key, tint, flip: fk[3] } : null;
}

/**
 * Which bundle a forest v3 key goes in: its season's (base, edges, trees, props; winter's flow shapes too),
 * "flow" (the flow shapes summer and autumn share), or null (e.g. the v1-named forest.pine).
 * @param {string} key @returns {'summer' | 'autumn' | 'winter' | 'flow' | null}
 */
export function v3ForestPartOf(key) {
  const m = /^(?:(autumn|winter)\.)?forest\.(grass|grassflow|tree|prop)\.v3\./.exec(key);
  if (!m) return null;
  if (m[2] === 'grassflow' && !m[1]) return 'flow';
  return /** @type {'autumn' | 'winter' | undefined} */ (m[1]) ?? 'summer';
}

/** The bundle of a part of the forest v3 art. @param {'summer' | 'autumn' | 'winter' | 'flow'} part */
export const v3ForestBundleName = (part) => `v3:forest:${part}`;

/** The bundles of the forest v3 art a season draws with (summer's for spring). @param {string | null | undefined} season */
export const v3ForestBundles = (season) => {
  const s = v3Season(season);
  return s === 'winter' ? [v3ForestBundleName(s)] : [v3ForestBundleName(s), v3ForestBundleName('flow')];
};

// --- winter: the forest / plains pair (NAMES.md 2.1) ---

/** v2's priority with moss and plains exchanged. */
const SWAPPED = Object.freeze(PRIORITY.map((c) => (c === 'moss' ? 'plains' : c === 'plains' ? 'moss' : c)));

/**
 * The priority of a display tile in winter: forest (moss) and plains exchanged when its corners hold both,
 * else v2's. @param {(string | null)[]} cls the 4 corners @returns {readonly string[]}
 */
export const winterPriority = (cls) => (cls.includes('moss') && cls.includes('plains') ? SWAPPED : PRIORITY);

/**
 * The mask of terrain t on display tile (i, j) read in that tile's own winter order (compare_forest_v3.winter_mask).
 * @param {string} t @param {number} i @param {number} j @param {(x: number, y: number) => string | null} classAt
 */
export function winterMaskOf(t, i, j, classAt) {
  const cs = [classAt(i, j), classAt(i + 1, j), classAt(i, j + 1), classAt(i + 1, j + 1)];
  const P = winterPriority(cs);
  const r = P.indexOf(t);
  let m = 0;
  cs.forEach((c, k) => {
    if (c && P.indexOf(c) >= r && P.indexOf(c) >= 0) m |= 1 << k;
  });
  return m;
}

// --- trees and props (FOREST.md 1-2) ---

/** The trees: game px (the art is 4 px per game px). Winter birch: frame 0 only (bare). */
export const FOREST_TREES = Object.freeze({
  pine_s: { w: 16, h: 30 },
  pine_l: { w: 32, h: 64 },
  spruce: { w: 20, h: 52 },
  birch: { w: 28, h: 40 },
});

/** The props: game px, sway frames, solid-looking (only at a tree's foot or as a tree's own picture). */
export const FOREST_PROPS = Object.freeze({
  fern: { w: 12, h: 10, frames: 2, solid: false },
  toadstool: { w: 8, h: 8, frames: 1, solid: false },
  roots: { w: 16, h: 8, frames: 1, solid: false },
  rock_moss: { w: 12, h: 10, frames: 1, solid: true },
  log_moss: { w: 20, h: 10, frames: 1, solid: true },
});

/** @typedef {keyof typeof FOREST_TREES} ForestTreeKind */

/**
 * Which v3 tree a forest tree is drawn as (drawing only: its tile, collision and saves stay). `room` is the
 * free distance around it in tiles (v3TreeRoom: 1 = something on a next tile, 3 = nothing within 2), `dense`
 * whether its 8 neighbours are all trees (deep in the wood, mostly hidden by the trees in front). The old
 * large pine (2 tiles wide) with room, or as a tall tree standing out of the thick of the wood; the spruce and
 * the birch (1.3 / 1.8 tiles) with a free tile round them or here and there at the wood's edge; the small pine
 * (1 tile, as the v1 tree) in the thick of the wood. By the tree's hash h (0..1) within that.
 *   room 3: pine_l 40%, birch 35%, spruce 25%     room 2: spruce 40%, birch 35%, pine_s 25%
 *   room 1: pine_s 60%, spruce 30%, birch 10%     dense:  pine_s 50%, spruce 38%, pine_l 12%
 * @param {number} room @param {boolean} dense @param {number} h @returns {ForestTreeKind}
 */
export function forestTreeKind(room, dense, h) {
  if (room >= 3) return h < 0.4 ? 'pine_l' : h < 0.75 ? 'birch' : 'spruce';
  if (room === 2) return h < 0.4 ? 'spruce' : h < 0.75 ? 'birch' : 'pine_s';
  if (dense) return h < 0.5 ? 'pine_s' : h < 0.88 ? 'spruce' : 'pine_l';
  return h < 0.6 ? 'pine_s' : h < 0.9 ? 'spruce' : 'birch';
}

/**
 * How a forest tree object is drawn: a v3 tree (forestTreeKind), or, for 1 tree in 20 at the wood's edge
 * (room 1, not dense), a fallen mossy log (still the same solid tile).
 * @param {number} room @param {boolean} dense @param {number} h @param {number} h2
 * @returns {{ what: 'tree' | 'prop', kind: string, set: 'forest' }}
 */
export function forestTreeLook(room, dense, h, h2) {
  if (room <= 1 && !dense && h2 < 1 / 20) return { what: 'prop', kind: 'log_moss', set: 'forest' };
  return { what: 'tree', kind: forestTreeKind(room, dense, h), set: 'forest' };
}

/**
 * The prop at the foot of a tree whose front (south) is open (on the tree's own tile), or null: about 1 in 3.
 * Roots (FOREST.md 1: always at a tree's foot), a fern, a mossy rock, toadstools.
 * @param {number} h 0..1 whether @param {number} h2 0..1 which @returns {keyof typeof FOREST_PROPS | null}
 */
export function forestFootProp(h, h2) {
  if (h > 0.34) return null;
  if (h2 < 0.45) return 'roots';
  if (h2 < 0.7) return 'fern';
  if (h2 < 0.85) return 'rock_moss';
  return 'toadstool';
}

/**
 * The prop on an open moss tile (walkable, nothing on or next to it, moss all round), or null: ferns in
 * loose patches (`patch` 0..1, a slow noise), toadstools near trees; about 1 tile in 8 inside a patch, 1 in
 * 40 outside. @param {number} patch @param {number} h @param {number} h2 @param {boolean} nearTree
 * @returns {keyof typeof FOREST_PROPS | null}
 */
export function forestOpenProp(patch, h, h2, nearTree) {
  const inPatch = patch > 0.55;
  if (h > (inPatch ? 0.125 + 0.25 * (patch - 0.55) : 0.025)) return null;
  if (nearTree && h2 < 0.3) return 'toadstool';
  return 'fern';
}

/**
 * The roots' place beside the trunk (FOREST.md 1): 4-12 game px left or right of the tree's foot, the foot
 * 1-2 px lower than the tree's (in front of it). @param {number} tx @param {number} ty @returns {[number, number]}
 */
export function rootsOffset(tx, ty) {
  const h = hsh(tx, ty, 951);
  const d = 4 + (h % 9);
  return [(h >>> 8) & 1 ? d : -d, 1 + ((h >>> 9) & 1)];
}


// --- the plains pine near the forest (NAMES.md 4, FOREST.md 4) ---

/**
 * The chunks where the map must not place the plains pine (plains.tree.v3.pine): those within a Chebyshev
 * chunk distance of 2 of a chunk overlapped by a forest region's rectangle (the test of gameView.chunkBundles).
 * @param {{ id: string, tx: number, ty: number, tw: number, th: number }[]} regions @param {number} chunk tiles
 * @returns {(tx: number, ty: number) => boolean} whether the tile is in such a chunk
 */
export function plainsPineBanned(regions, chunk) {
  /** @type {[number, number][]} */
  const a = [];
  for (const r of regions) {
    if (r.id !== 'forest') continue;
    for (let cy = Math.floor(r.ty / chunk); cy * chunk < r.ty + r.th; cy++) for (let cx = Math.floor(r.tx / chunk); cx * chunk < r.tx + r.tw; cx++) a.push([cx, cy]);
  }
  return (tx, ty) => {
    const cx = Math.floor(tx / chunk);
    const cy = Math.floor(ty / chunk);
    return a.some(([ax, ay]) => Math.max(Math.abs(cx - ax), Math.abs(cy - ay)) <= 2);
  };
}
