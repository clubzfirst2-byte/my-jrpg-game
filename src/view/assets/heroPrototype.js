// @ts-check
// P12: the hero PROTOTYPE frames (仮素材, waiting for approval) — src/art-proto/hero/*.png, drawn
// by tools/hero_proto/gen_hero_prototype.py. They are NOT in src/art, so the game never uses them
// unless asked with ?hero=proto; they are loaded only then.

const files = /** @type {Record<string, () => Promise<string>>} */ (import.meta.glob('../../art-proto/hero/*.png', { query: '?url', import: 'default' }));

/** @returns {Promise<Map<string, string>>} sprite name → PNG URL */
export async function heroPrototypeFrames() {
  const entries = await Promise.all(Object.entries(files).map(async ([path, load]) => [/** @type {string} */ (path.split('/').pop()).replace(/\.png$/i, ''), await load()]));
  return new Map(/** @type {[string, string][]} */ (entries));
}
