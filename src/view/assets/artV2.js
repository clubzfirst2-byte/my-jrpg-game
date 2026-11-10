// @ts-check
// Graphics v2 (scratchpad gfx_plan.md): new art lives in src/art-release-v2/<group>/ (terrain, enemy,
// ui, ...), beside the approved v1 art in src/art-release/<group>/, which is never changed. The build
// packs each v2 group like a v1 one (vite.config.js releaseArt: release-v2-<group>.png / .json; in the
// game its name is "v2/<group>"). A v2 group is drawn INSTEAD of its v1 group when it is present in
// the build and enabled; a group with no v1 counterpart (e.g. ui) is simply loaded when enabled.
//
// A group is enabled by default only after its art has passed independent inspection: then it is
// added to V2_ENABLED (and so also kept for offline play, tools/precache.mjs). URL switches, to compare:
//   ?v2=0              every group as v1 (the approved art)
//   ?<group>=v1|v2     one group as v1 or v2 (wins over ?v2=0 and over the list); e.g. ?terrain=v2
// Pure (no Vite / PixiJS imports): tools/precache.mjs reads V2_ENABLED too.

/**
 * The v2 groups that passed inspection and are drawn by default (the director adds a group once its
 * art is approved).
 * - enemy: gfx/w3-enemy-art d900394, passed independent inspection (2026-11-10)
 * @type {readonly string[]}
 */
export const V2_ENABLED = Object.freeze(['enemy']);

/** The name a v2 group has in the game (releaseFrames, the build's sheet table). @param {string} group */
export const v2Name = (group) => `v2/${group}`;

/** The folder of a group name ("v2/terrain" → "terrain"), and whether it is v2. @param {string} name */
export const parseGroupName = (name) => (name.startsWith('v2/') ? { group: name.slice(3), v2: true } : { group: name, v2: false });

/**
 * Which art a group is drawn from.
 * @param {string} group the folder name (terrain, enemy, ui, ...)
 * @param {URLSearchParams} params
 * @param {{ available: Iterable<string>, enabled?: readonly string[] }} opts available = the v2 groups in this build
 * @returns {'v1' | 'v2'}
 */
export function artVersion(group, params, { available, enabled = V2_ENABLED }) {
  if (![...available].includes(group)) return 'v1';
  const asked = params.get(group);
  if (asked === 'v1' || asked === 'v2') return asked;
  if (params.get('v2') === '0') return 'v1';
  return enabled.includes(group) ? 'v2' : 'v1';
}

/**
 * The release art groups to load: each v1 group the game wants, replaced by its v2 group when that is
 * drawn instead, plus the v2-only groups (no v1 folder) that are drawn.
 * @param {string[]} groups the v1 groups the game loads (main.js)
 * @param {URLSearchParams} params
 * @param {{ available: Iterable<string>, enabled?: readonly string[], v1Groups?: Iterable<string> }} opts
 *   v1Groups = every v1 folder (so a v2 group with a v1 counterpart that is not loaded now, e.g. the
 *   placeholder terrain, is not loaded either)
 * @returns {string[]}
 */
export function resolveArtGroups(groups, params, { available, enabled = V2_ENABLED, v1Groups = [] }) {
  const avail = [...available];
  const v1 = new Set([...v1Groups, ...groups]);
  const out = groups.map((g) => (artVersion(g, params, { available: avail, enabled }) === 'v2' ? v2Name(g) : g));
  for (const g of avail) if (!v1.has(g) && artVersion(g, params, { available: avail, enabled }) === 'v2') out.push(v2Name(g));
  return out;
}
