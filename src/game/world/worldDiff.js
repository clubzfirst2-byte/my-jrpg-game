// @ts-check
// Saving the world as differences (P8, DESIGN.md 4.1 / roadmap "セーブの差分保存"): only objects that
// changed since the map was made are written — burnt trees (now stumps), cut brambles, broken jars,
// opened doors, moved crates, lit sconces — grouped by the chunk they started in. Loading applies
// them back onto a freshly built world. Pure logic.
//
// Each object is named by what the map made it and where ("jar@44,58"), not by its position in the
// list of objects: that list changes whenever the map gains things (P10.1 added house walls), and an
// old save must still find its broken jar (P10.3 fix; P10.6 checks save compatibility).
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

/** How a save names an object: what it was and where, when the map was made. @param {{ type: string, tx: number, ty: number }} b */
export const objectId = (b) => `${b.type}@${b.tx},${b.ty}`;

/**
 * Changes since the baseline, grouped by chunk ("cx,cy" -> { "type@tx,ty": changedFields }).
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
    (diff[key] ??= {})[objectId(b)] = change;
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
  /** @type {Map<string, number>} */
  const byId = new Map();
  state.objectBaseline.forEach((/** @type {any} */ b, /** @type {number} */ i) => byId.set(objectId(b), i));
  for (const entries of Object.values(diff)) {
    for (const [k, change] of Object.entries(entries)) {
      // An object the map no longer has (or an unconverted old entry) is skipped.
      const i = byId.get(k);
      if (i === undefined) continue;
      const o = map.objects[i];
      const b = state.objectBaseline[i];
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

/**
 * Whether an old (index-named) change could belong to an object of this kind.
 * @param {string} type @param {Record<string, any>} change
 */
export function legacyFits(type, change) {
  if (change.type === 'stump') return type === 'tree';
  if (change.type !== undefined) return change.type === type;
  if ('lit' in change) return type === 'sconce';
  if ('on' in change) return type === 'receiver';
  if ('tx' in change || 'ty' in change) return type === 'crate';
  if ('hp' in change) return type === 'bramble';
  if ('gone' in change) return ['jar', 'bramble', 'door', 'crystal', 'tree', 'stump'].includes(type);
  return false;
}

/**
 * Converts a world diff written by P8-P10.2 (objects named by list index) to names. The version that
 * wrote it is unknown, so each entry is looked up in every old list; it is kept only when the
 * candidates that fit (in the same chunk, the right kind of thing for the change) all name the same
 * object. Anything doubtful is dropped: a tree growing back is better than the wrong door opening.
 * @param {Record<string, Record<string, any>> | undefined} diff
 * @param {string[][]} lists the old object lists ("type@tx,ty" in list order)
 */
export function nameIndexedDiff(diff, lists) {
  if (!diff) return diff;
  /** @type {Record<string, Record<string, any>>} */
  const out = {};
  for (const [chunk, entries] of Object.entries(diff)) {
    for (const [k, change] of Object.entries(entries)) {
      if (!/^\d+$/.test(k)) {
        (out[chunk] ??= {})[k] = change; // already a name
        continue;
      }
      const fits = new Set();
      for (const list of lists) {
        const id = list[Number(k)];
        if (!id) continue;
        const m = /^(.+)@(\d+),(\d+)$/.exec(id);
        if (!m) continue;
        const [, type, tx, ty] = m;
        if (`${Math.floor(Number(tx) / DIFF_CHUNK)},${Math.floor(Number(ty) / DIFF_CHUNK)}` !== chunk) continue;
        if (legacyFits(type, change)) fits.add(id);
      }
      if (fits.size === 1) (out[chunk] ??= {})[[...fits][0]] = change;
    }
  }
  return out;
}
