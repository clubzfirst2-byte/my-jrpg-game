// @ts-check
// P12: PROTOTYPE art (仮素材, waiting for approval) — src/art-proto/<group>/*.png, drawn by the
// generators in tools/hero_proto and tools/art_proto. They are NOT in src/art, so the game never
// uses them unless asked, and they are loaded only then:
//   ?hero=proto   the hero          ?npc=proto   villagers          ?enemy=proto   enemies
//   ?proto=all    all of them
import releaseSheets from 'virtual:release-art';
import { V3_DENSITY } from './artV3.js';

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

// Release art (QUALITY_POLICY: made at release quality, adopted after approval): src/art-release/<group>/*.png.
// The hero's was adopted on 2026-11-08 and is loaded for normal play (src/main.js).
// In the build each group is ONE sheet PNG + ONE frame table JSON (vite.config.js, releaseArt;
// docs/perf/release-art-packing.md), so it costs 2 requests instead of one per frame. In the dev
// server (no sheets) the frame files are loaded one by one; this glob is dropped from the build.
// Graphics v2: src/art-release-v2/<group>/*.png, named "v2/<group>" in the game (artV2.js).
const releaseFiles = /** @type {Record<string, () => Promise<string>>} */ (
  import.meta.env.DEV ? import.meta.glob(['../../art-release/*/*.png', '../../art-release-v2/*/*.png', '../../art-release-v3/*/*.png'], { query: '?url', import: 'default' }) : {}
);

/**
 * The release group name of a dev-server frame path ("v2/<folder>" under art-release-v2, "v3/<folder>"
 * under art-release-v3, artV3.js). @param {string} path
 */
const devGroupOf = (path) => {
  const folder = /** @type {string} */ (path.split('/').at(-2));
  if (path.includes('/art-release-v2/')) return `v2/${folder}`;
  if (path.includes('/art-release-v3/')) return `v3/${folder}`;
  return folder;
};

/**
 * The graphics v2 groups in this build (the folders under src/art-release-v2), without the "v2/".
 * @param {Record<string, unknown> | null} [sheets] the packed groups (the build's)
 * @returns {string[]}
 */
export function availableV2Groups(sheets = releaseSheets) {
  const names = sheets ? Object.keys(sheets) : Object.keys(releaseFiles).map(devGroupOf);
  return [...new Set(names.filter((n) => n.startsWith('v2/')).map((n) => n.slice(3)))].sort();
}

/** The v1 release groups in this build (the folders under src/art-release). @param {Record<string, unknown> | null} [sheets] */
export function availableV1Groups(sheets = releaseSheets) {
  const names = sheets ? Object.keys(sheets) : Object.keys(releaseFiles).map(devGroupOf);
  return [...new Set(names.filter((n) => !n.startsWith('v2/') && !n.startsWith('v3/')))].sort();
}

/** The graphics v3 groups in this build (the folders under src/art-release-v3), without the "v3/". @param {Record<string, unknown> | null} [sheets] */
export function availableV3Groups(sheets = releaseSheets) {
  const names = sheets ? Object.keys(sheets) : Object.keys(releaseFiles).map(devGroupOf);
  return [...new Set(names.filter((n) => n.startsWith('v3/')).map((n) => n.slice(3)))].sort();
}

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
 * @param {string} group a folder of src/art-release, or "v2/<folder>" for src/art-release-v2 (artV2.js)
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
      const density = group.startsWith('v3/') ? V3_DENSITY : undefined;
      return new Map(Object.entries(frames).map(([name, r]) => [name, density ? { sheet, x: r.x, y: r.y, w: r.w, h: r.h, density } : { sheet, x: r.x, y: r.y, w: r.w, h: r.h }]));
    } catch (err) {
      console.warn(`art: release ${group}: ${String(err)}; using the placeholders`);
      return new Map();
    }
  }
  const picked = Object.entries(releaseFiles).filter(([path]) => devGroupOf(path) === group);
  const entries = await Promise.all(picked.map(async ([path, load]) => [/** @type {string} */ (path.split('/').pop()).replace(/\.png$/i, ''), await load()]));
  // v3 frames carry their density (4 art px per game px) so they are packed on an atlas of their own
  if (group.startsWith('v3/')) return new Map(entries.map(([k, url]) => [/** @type {string} */ (k), { url: /** @type {string} */ (url), density: V3_DENSITY }]));
  return new Map(/** @type {[string, string][]} */ (entries));
}

