// @ts-check
// v1.0: the terrain release art (src/art-release/terrain, docs/art-release/terrain/PRODUCTION.md) in
// normal play. Its 111 files are named after the game's own sprite keys (tile.*, face.*, the region
// grounds, the season variants "<season>.<key>", trees and the nature objects), so no renaming is
// needed: the frames go into the art overrides and every bundle that already holds a key picks up
// its art (placeholderPack.withOverrides) —
//   - the base bundle: the island ground, paths, water (2 frames), floors, walls, pits, the ramp,
//     vines, the earth / ruin / wall cliff faces, the tree and the rock / bramble / stump
//   - each region bundle only its own: desert sand + cactus, plains / forest / lake grass, the
//     mountains' snow, stone faces and pine, the forest pine
//   - each season bundle only its own (spring tree; autumn / winter ground, cliff lips and trees)
// Tiles and faces keep the 16 px grid (32 art px = 16 game px, ART_SCALE); trees and objects stand
// on their feet (anchor [0.5, 1]), as the placeholders did.
// The group is ONE packed sheet in the build (~21 KB PNG + ~6 KB table, vite.config.js releaseArt):
// smaller than splitting it per region would save, so it is loaded once with the other release art
// and kept for offline play (tools/precache.mjs); only the GPU atlases are per bundle.
//
//   ?terrain=placeholder   the placeholder terrain (before/after comparison)
//   ?terrain=release       the terrain art even where the rest is placeholder (?hero=placeholder)
// Like the villagers' and the enemies' art, it goes with the release hero (normal play); ?hd=0 and
// ?hero=placeholder show the game as before the release art.

/** The release art folder (src/art-release/terrain). */
export const TERRAIN_GROUP = 'terrain';

/**
 * Whether the terrain release art is drawn.
 * @param {URLSearchParams} params
 * @param {boolean} releaseHero whether the release hero is drawn (normal play)
 */
export function wantsTerrainArt(params, releaseHero) {
  const mode = params.get('terrain');
  if (params.get('hd') === '0' || mode === 'placeholder') return false;
  return releaseHero || mode === 'release';
}

/** Region grounds: <region>.<ground>.<variant> (gameView.surfaceKey). */
const REGION_GROUND = /^(desert\.sand|plains\.grass|forest\.grass|mountains\.snow|lake\.grass)\.\d+$/;

/** The nature objects drawn by the terrain art (the other obj.* keys are the objects art's). */
export const TERRAIN_OBJECTS = Object.freeze(['obj.tree', 'obj.rock', 'obj.bramble', 'obj.stump', 'obj.cactus', 'forest.pine', 'mountains.pine']);

/** The seasons that have their own look ("<season>.<key>"; summer is the plain art). */
const SEASON_PREFIX = /^(spring|autumn|winter)\./;

/**
 * Whether a sprite key is terrain (drawn by the terrain art): ground tiles, cliff faces, the region
 * grounds, trees and nature objects, and their season variants. Objects, puzzle parts, icons,
 * effects and characters are not.
 * @param {string} key
 */
export function isTerrainKey(key) {
  const k = key.replace(SEASON_PREFIX, '');
  return k.startsWith('tile.') || k.startsWith('face.') || REGION_GROUND.test(k) || TERRAIN_OBJECTS.includes(k);
}

/**
 * Debug / test helper (window.__debugApi.terrainArt): of the terrain keys loaded right now, which are
 * drawn from the release art (2 pixels per game pixel) and which from the placeholder.
 * @param {import('./assetManager.js').AssetManager} assets
 */
export function terrainDebugApi(assets) {
  return {
    terrainArt: () => {
      /** @type {Set<string>} */
      const release = new Set();
      /** @type {Set<string>} */
      const placeholder = new Set();
      for (const { bundle } of assets.loaded.values()) {
        for (const [key, tex] of bundle.textures) {
          if (!isTerrainKey(key)) continue;
          (tex.source.resolution > 1 ? release : placeholder).add(key);
        }
      }
      return { release: [...release].sort(), placeholder: [...placeholder].sort(), bundles: [...assets.loaded.keys()] };
    },
  };
}
