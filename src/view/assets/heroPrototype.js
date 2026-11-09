// @ts-check
// P12: PROTOTYPE art (仮素材, waiting for approval) — src/art-proto/<group>/*.png, drawn by the
// generators in tools/hero_proto and tools/art_proto. They are NOT in src/art, so the game never
// uses them unless asked, and they are loaded only then:
//   ?hero=proto   the hero          ?npc=proto   villagers          ?enemy=proto   enemies
//   ?proto=all    all of them
import releaseSheets from 'virtual:release-art';

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

// Release art under review (QUALITY_POLICY: made at release quality, adopted after approval):
// src/art-release/<group>/*.png, loaded only with ?hero=release until it is approved.
// In the build each group is ONE sheet PNG + ONE frame table JSON (vite.config.js, releaseArt;
// docs/perf/release-art-packing.md), so it costs 2 requests instead of one per frame. In the dev
// server (no sheets) the frame files are loaded one by one; this glob is dropped from the build.
const releaseFiles = /** @type {Record<string, () => Promise<string>>} */ (
  import.meta.env.DEV ? import.meta.glob('../../art-release/*/*.png', { query: '?url', import: 'default' }) : {}
);

/** @param {string} url @returns {Promise<HTMLImageElement>} */
function loadSheet(url) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error(`Could not load ${url}`));
    img.src = url;
  });
}

/**
 * @param {string} group
 * @param {Record<string, { sheet: string, table: string }> | null} [sheets] the packed groups (the build's)
 * @returns {Promise<Map<string, import('./placeholderPack.js').ArtSource>>} sprite name → PNG URL (dev),
 *   or → its place on the group's sheet (build)
 */
export async function releaseFrames(group, sheets = releaseSheets) {
  const packed = sheets?.[group];
  if (packed) {
    try {
      const [sheet, table] = await Promise.all([loadSheet(packed.sheet), fetch(packed.table).then((r) => (r.ok ? r.json() : Promise.reject(new Error(`Could not load ${packed.table}`))))]);
      const frames = /** @type {Record<string, { x: number, y: number, w: number, h: number }>} */ (table.frames);
      return new Map(Object.entries(frames).map(([name, r]) => [name, { sheet, x: r.x, y: r.y, w: r.w, h: r.h }]));
    } catch (err) {
      console.warn(`art: release ${group}: ${String(err)}; using the placeholders`);
      return new Map();
    }
  }
  const picked = Object.entries(releaseFiles).filter(([path]) => path.split('/').at(-2) === group);
  const entries = await Promise.all(picked.map(async ([path, load]) => [/** @type {string} */ (path.split('/').pop()).replace(/\.png$/i, ''), await load()]));
  return new Map(/** @type {[string, string][]} */ (entries));
}

