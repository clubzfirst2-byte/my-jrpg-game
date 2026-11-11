// The service worker's precache list (vite.config.js, serviceWorker): every built file normal play
// needs, kept for offline play. Files that normal play never loads are left out — they are still
// built and load from the network when asked for (perf v1, scratchpad perf_v1.md "小 1"):
//   - release art groups the game does not load yet, or loads only for review (?npc=revision…)
//   - the P12 prototype art (src/art-proto, ?…=proto): one small JS chunk per frame

import { V2_ENABLED } from '../src/view/assets/artV2.js';

/** The fixed files outside the bundle (public/). */
export const PRECACHE_STATIC = ['./', 'index.html', 'manifest.webmanifest', 'icons/icon-192.png', 'icons/icon-512.png', 'icons/icon-maskable-512.png', 'icons/apple-touch-icon.png'];

/**
 * Release art groups loaded only on demand, never kept for offline play:
 *   - the review sets npc-revision* (?npc=revision…);
 *   - a graphics v2 group (release-v2-<group>, src/art-release-v2) that is not drawn by default
 *     (artV2.js V2_ENABLED): it loads from the network when asked for (?<group>=v2).
 * Everything else is kept: every v1 group (src/art-release/<group>) the game loads — terrain and
 * objects since v1.0 —, and a v2 group once it is drawn by default. A v1 group whose v2 group is drawn
 * by default (terrain since gfx W1, as the enemies' in fx-v2) STAYS kept, so ?<group>=v1 and ?v2=0
 * still show it offline; it is only no longer preloaded (preloadReleaseGroup).
 * @param {string} group
 */
export const onDemandReleaseGroup = (group) => group.startsWith('npc-revision') || (group.startsWith('v2-') && !V2_ENABLED.includes(group.slice(3)));

/**
 * Whether the page preloads a release art group in its HTML (vite.config.js, transformIndexHtml):
 * the groups normal play draws. A graphics v2 group, and a v1 group that has a v2 counterpart, is not
 * preloaded statically: which of the two is drawn depends on the URL (?<group>=v1|v2, ?v2=0: artV2.js),
 * so the page chooses with a small script (preloadScript) — an unused preload is a console warning and
 * a wasted download on the phone. Which of them are kept for offline play is onDemandReleaseGroup's:
 * the v1 group always, the v2 group once it is drawn by default.
 * @param {string} group @param {Set<string>} groups every release group in the build
 */
export const preloadReleaseGroup = (group, groups) => !onDemandReleaseGroup(group) && !group.startsWith('v2-') && !hasV2Pair(group, groups);

/** Whether a group is one of a v1 / v2 pair in the build ("terrain" with "v2-terrain"). @param {string} group @param {Set<string>} groups */
export const hasV2Pair = (group, groups) => (group.startsWith('v2-') ? groups.has(group.slice(3)) : groups.has(`v2-${group}`));

/**
 * The page's ONE script (index.html, written by vite.config.js) that preloads the graphics v2 groups
 * and the v1 groups they replace, by the URL, with the rule the game uses (artV2.artVersion):
 *   ?<group>=v1|v2 first, then ?v2=0 (every group v1), then V2_ENABLED.
 * For each group the files of the side that will be drawn are preloaded, and only those:
 *   - a v1 / v2 pair (terrain, the enemies): the v1 sheet + frame table, or the v2 ones; neither when
 *     the group's release art is not drawn at all (?<group>=placeholder|proto, ?proto=all without
 *     ?<group>=release, ?hd=0: main.js, terrainArt.wantsTerrainArt);
 *   - a v2 group with no v1 counterpart (the UI): its files when it is drawn as v2, else nothing.
 * An inline script, so it runs while the HTML is read, before the game's JS.
 * @param {Record<string, { v1?: string[], v2?: string[] }>} groups hrefs by group (folder name) and side
 * @param {readonly string[]} [enabled] the groups drawn by default
 * @returns {string}
 */
export function preloadScript(groups, enabled = V2_ENABLED) {
  return `(function(){var p=new URLSearchParams(location.search),E=${JSON.stringify(enabled)},G=${JSON.stringify(groups)};
function add(h){var l=document.createElement('link');l.rel='preload';if(/\\.json$/.test(h)){l.as='fetch';l.type='application/json';l.crossOrigin='anonymous';}else{l.as='image';}l.href=h;document.head.appendChild(l);}
for(var g in G){var q=p.get(g),f=G[g];if(f.v1&&(p.get('hd')==='0'||q==='placeholder'||q==='proto'||(p.get('proto')==='all'&&q!=='release')))continue;
var v2=q==='v2'||(q!=='v1'&&p.get('v2')!=='0'&&E.indexOf(g)>=0);(f[v2?'v2':'v1']||[]).forEach(add);}})();`;
}

/**
 * preloadScript for v1 / v2 pairs given as a sheet and a frame table per side (gfx W1, the terrain).
 * @param {Record<string, { v1?: { png?: string, json?: string }, v2?: { png?: string, json?: string } }>} pairs
 * @param {readonly string[]} [enabled]
 */
export function preloadSwitchScript(pairs, enabled = V2_ENABLED) {
  /** @param {{ png?: string, json?: string } | undefined} f */
  const list = (f) => (f ? [f.png, f.json].filter((h) => h !== undefined) : undefined);
  return preloadScript(Object.fromEntries(Object.entries(pairs).map(([g, f]) => [g, { v1: list(f.v1) ?? [], v2: list(f.v2) }])), enabled);
}

/**
 * preloadScript for v2 groups given as their files only (W4, the UI; a group listed here with no v1 side
 * is preloaded only when drawn as v2).
 * @param {Record<string, string[]>} hrefs v2 group (folder name) → files to preload
 * @param {readonly string[]} [enabled]
 */
export function v2PreloadScript(hrefs, enabled = V2_ENABLED) {
  return preloadScript(Object.fromEntries(Object.entries(hrefs).map(([g, v2]) => [g, { v2 }])), enabled);
}

/**
 * The release art group of an emitted sheet / frame table (release-<group>.png|json), or of a frame
 * emitted on its own (release-<group>.<frame>.png: the v2 UI, vite.config.js), or null. Group names
 * have no dots. @param {string} name
 */
export const releaseGroupOf = (name) => /^release-([^.]+)(?:\..+)?\.(png|json)$/.exec(name)?.[1] ?? null;

/**
 * @param {Record<string, { type: 'chunk' | 'asset', fileName: string, name?: string, names?: string[], moduleIds?: string[] }>} bundle
 *   the Rollup output bundle (only these fields are read)
 * @returns {string[]} file names to precache, in bundle order, without duplicates
 */
export function precacheFiles(bundle) {
  const keep = Object.entries(bundle)
    .filter(([file, out]) => {
      if (file.endsWith('.map')) return false;
      if (out.type === 'chunk') {
        const ids = out.moduleIds ?? [];
        return !(ids.length > 0 && ids.every((id) => id.replace(/\\/g, '/').includes('/src/art-proto/')));
      }
      const names = out.names ?? (out.name ? [out.name] : []);
      return !names.some((n) => {
        const group = releaseGroupOf(n);
        return group !== null && onDemandReleaseGroup(group);
      });
    })
    .map(([file]) => file);
  return [...new Set([...PRECACHE_STATIC, ...keep])];
}

