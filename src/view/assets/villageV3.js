// @ts-check
// Graphics v3 (?v3=1): the village art of src/art-release-v3/objects (docs/art-release-v3/VILLAGE.md) and
// where it is kept (VILLAGE.md 4.0, the coordinator's measures 1 + 2):
//   1. a village's own bundle per season, "v3:village:<season>", with only the house kinds the village
//      uses (the house and the stone house) and its fences, well and signposts, loaded by the chunks that
//      have them and let go away from them (gameView.v3VillageBundleOf)
//   2. the things found everywhere (chests, barrels, crates, jars, fires, braziers, checkpoints, floor
//      plates) stay out of it: their summer look in the base bundle as before (the v3 frames replace the
//      v1 ones by name), their winter look in "v3:objects:winter", held through the winter. The open chest
//      has no winter look (VILLAGE.md 1: winter uses the summer file, no snow on the open lid).
// A season without its own file uses summer's (spring is summer; autumn has only the 2 houses).
// Pure (no PixiJS).
import { v3Season } from '../v3Plains.js';

/** The village bundle's keys (each drawn from its season's file, else summer's). */
export const V3_VILLAGE_KEYS = Object.freeze(['obj.house', 'obj.v3.house_stone', 'obj.v3.fence.h', 'obj.v3.fence.l', 'obj.v3.fence.r', 'obj.v3.fence.post', 'obj.v3.well', 'obj.v3.signpost']);

/** The object kinds whose chunks load the village bundle. */
export const V3_VILLAGE_TYPES = Object.freeze(['house', 'fence', 'well', 'signpost']);

/** The common objects with a winter file (not the open chest). */
export const V3_WINTER_OBJECTS = Object.freeze(['obj.chest.closed', 'obj.barrel', 'obj.crate', 'obj.jar', 'obj.campfire.0', 'obj.campfire.1', 'obj.brazier.0', 'obj.brazier.1', 'obj.checkpoint.off', 'obj.checkpoint.on', 'sw.plate.off', 'sw.plate.on']);

/** The bundle of the common objects' winter look. */
export const V3_OBJECTS_WINTER = 'v3:objects:winter';

/** The village bundle of a season. @param {string | null | undefined} season */
export const v3VillageBundle = (season) => `v3:village:${v3Season(season)}`;

/**
 * The art of the village bundle of a season: each key from its season's file, else summer's, under the
 * plain key (so the view asks for "obj.house" in every season). @template T
 * @param {'summer' | 'autumn' | 'winter'} season @param {Map<string, T>} overrides
 * @returns {Map<string, T>} only the keys with art
 */
export function villageSources(season, overrides) {
  /** @type {Map<string, T>} */
  const out = new Map();
  for (const k of V3_VILLAGE_KEYS) {
    const src = (season !== 'summer' ? overrides.get(`${season}.${k}`) : undefined) ?? overrides.get(k);
    if (src !== undefined) out.set(k, src);
  }
  return out;
}

/** The winter keys of the common objects that have art ("winter.obj.barrel", ...). @param {Map<string, unknown> | Set<string>} overrides */
export const winterObjectKeys = (overrides) => V3_WINTER_OBJECTS.map((k) => `winter.${k}`).filter((k) => overrides.has(k));
