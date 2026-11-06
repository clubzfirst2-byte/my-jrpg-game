// @ts-check
// P12: PROTOTYPE art (仮素材, waiting for approval) — src/art-proto/<group>/*.png, drawn by the
// generators in tools/hero_proto and tools/art_proto. They are NOT in src/art, so the game never
// uses them unless asked, and they are loaded only then:
//   ?hero=proto   the hero          ?npc=proto   villagers          ?enemy=proto   enemies
//   ?proto=all    all of them

const files = /** @type {Record<string, () => Promise<string>>} */ (import.meta.glob('../../art-proto/*/*.png', { query: '?url', import: 'default' }));

/** The prototype groups (folders under src/art-proto). */
export const PROTO_GROUPS = /** @type {const} */ (['hero', 'npc', 'enemy']);

/**
 * @param {readonly string[]} groups which folders to load
 * @returns {Promise<Map<string, string>>} sprite name → PNG URL
 */
export async function prototypeFrames(groups) {
  const picked = Object.entries(files).filter(([path]) => groups.includes(/** @type {string} */ (path.split('/').at(-2))));
  const entries = await Promise.all(picked.map(async ([path, load]) => [/** @type {string} */ (path.split('/').pop()).replace(/\.png$/i, ''), await load()]));
  return new Map(/** @type {[string, string][]} */ (entries));
}

/** The hero prototype only (P12 v2). */
export const heroPrototypeFrames = () => prototypeFrames(['hero']);

/** Which prototype groups the URL asks for. @param {URLSearchParams} params */
export function requestedProtoGroups(params) {
  if (params.get('proto') === 'all') return [...PROTO_GROUPS];
  return PROTO_GROUPS.filter((g) => params.get(g) === 'proto');
}
