// The service worker's precache list (vite.config.js, serviceWorker): every built file normal play
// needs, kept for offline play. Files that normal play never loads are left out — they are still
// built and load from the network when asked for (perf v1, scratchpad perf_v1.md "小 1"):
//   - release art groups the game does not load yet, or loads only for review (?npc=revision…)
//   - the P12 prototype art (src/art-proto, ?…=proto): one small JS chunk per frame

import { V2_ENABLED } from '../src/view/assets/artV2.js';

/** The fixed files outside the bundle (public/). */
export const PRECACHE_STATIC = ['./', 'index.html', 'manifest.webmanifest', 'icons/icon-192.png', 'icons/icon-512.png', 'icons/icon-maskable-512.png', 'icons/apple-touch-icon.png'];

/**
 * Release art groups (src/art-release/<group>) loaded only on demand, never in normal play:
 * the review sets npc-revision* (?npc=revision…). The terrain and the objects are drawn in
 * normal play since v1.0, so they are kept.
 * A group the game starts to load in normal play must be taken off this list (else it is not
 * available offline): terrain and objects since v1.0 (terrainArt.js, objectsArt.js).
 * Graphics v2 groups (release-v2-<group>, src/art-release-v2) are kept once enabled (artV2.js
 * V2_ENABLED, i.e. drawn by default); until then they load on demand (?<group>=v2).
 * @param {string} group
 */
export const onDemandReleaseGroup = (group) => group.startsWith('npc-revision') || (group.startsWith('v2-') && !V2_ENABLED.includes(group.slice(3)));

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

/**
 * The page's preloads of the Graphics v2 groups, decided by the URL as the game decides (artV2.js
 * artVersion): a group's files are preloaded only when it will be drawn (?v2=0, ?<group>=v1 → not).
 * An inline script, so it runs while the HTML is read, before the game's JS.
 * @param {Record<string, string[]>} hrefs v2 group (folder name) → files to preload
 * @param {readonly string[]} [enabled] the groups drawn by default
 * @returns {string}
 */
export function v2PreloadScript(hrefs, enabled = V2_ENABLED) {
  return `(function(){var q=new URLSearchParams(location.search),E=${JSON.stringify(enabled)},G=${JSON.stringify(hrefs)};
for(var g in G){var a=q.get(g);if(!(a==='v2'||(a!=='v1'&&q.get('v2')!=='0'&&E.indexOf(g)>=0)))continue;
G[g].forEach(function(h){var l=document.createElement('link');l.rel='preload';if(/\\.json$/.test(h)){l.as='fetch';l.type='application/json';l.crossOrigin='anonymous';}else{l.as='image';}l.href=h;document.head.appendChild(l);});}})();`;
}
