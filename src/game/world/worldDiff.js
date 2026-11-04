// @ts-check
// Saving the world as differences (P8, DESIGN.md 4.1 / roadmap "セーブの差分保存"): only objects that
// changed since the map was made are written — burnt trees (now stumps), cut brambles, broken jars,
// opened doors, moved crates, lit sconces — grouped by the chunk they started in. Loading applies
// them back onto a freshly built world. Pure logic.
import { SOLID_OBJECTS } from '../env/envSim.js';

export const DIFF_CHUNK = 32;
/** Fields that can change on an object. */
const FIELDS = /** @type {const} */ (['type', 'tx', 'ty', 'gone', 'lit', 'on', 'hp']);

/**
 * The objects as the map made them (index = position in map.objects).
 * @param {any[]} objects @returns {any[]}
 */
export function objectBaseline(objects) {
  return objects.map((o) => ({ type: o.type, tx: o.tx, ty: o.ty }));
}

/**
 * Changes since the baseline, grouped by chunk ("cx,cy" -> { objectIndex: changedFields }).
 * @param {any} state @returns {Record<string, Record<string, any>>}
 */
export function computeWorldDiff(state) {
  /** @type {Record<string, Record<string, any>>} */
  const diff = {};
  const base = state.objectBaseline;
  state.map.objects.forEach((/** @type {any} */ o, /** @type {number} */ i) => {
    const b = base[i];
    if (!b) return;
    /** @type {Record<string, any>} */
    const change = {};
    for (const f of FIELDS) {
      const v = o[f];
      if (v !== undefined && v !== b[f] && !(v === false && b[f] === undefined)) change[f] = v;
    }
    if (Object.keys(change).length === 0) return;
    const key = `${Math.floor(b.tx / DIFF_CHUNK)},${Math.floor(b.ty / DIFF_CHUNK)}`;
    (diff[key] ??= {})[i] = change;
  });
  return diff;
}

/**
 * Applies saved differences to a freshly built world (objects, what blocks movement, where
 * objects stand). Entries that no longer match the map (an old save) are skipped.
 * @param {any} state @param {Record<string, Record<string, any>> | undefined} diff
 * @returns {number} objects changed
 */
export function applyWorldDiff(state, diff) {
  if (!diff) return 0;
  const map = state.map;
  const env = state.env;
  let n = 0;
  for (const entries of Object.values(diff)) {
    for (const [k, change] of Object.entries(entries)) {
      const o = map.objects[Number(k)];
      const b = state.objectBaseline[Number(k)];
      if (!o || !b) continue;
      const before = o.ty * map.width + o.tx;
      Object.assign(o, change);
      const after = o.ty * map.width + o.tx;
      if (before !== after && env.objectAt.get(before) === o) {
        env.objectAt.delete(before);
        map.solid[before] = 0;
        env.objectAt.set(after, o);
      }
      // Gone things and stumps no longer block; solid kinds block where they stand now.
      map.solid[after] = !o.gone && SOLID_OBJECTS.has(o.type) ? 1 : 0;
      n++;
    }
  }
  env.version++;
  return n;
}
