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
 * Whether the loaded base bundle draws the terrain from the release art (its tiles are on the
 * 2-pixels-per-game-pixel atlas). Read once by the view, after the base bundle has loaded.
 * @param {import('./assetManager.js').AssetManager} assets
 */
export function usesReleaseTerrain(assets) {
  return assets.hasTexture('tile.grass.0') && assets.texture('tile.grass.0').source.resolution > 1;
}

/**
 * The height tint of the ground (gameView.levelTint): higher ground is drawn a little brighter so
 * levels read at a glance. The placeholders keep their 0.8 + 0.07 per level; the release terrain
 * was approved at its own colours, so its flat ground is drawn at 0.95 (+0.05 per level, up to 1):
 * otherwise it showed 20–44 % darker than the hero and villagers standing on it (inspection of
 * e7d40c0). Cliff faces, edge lines and contact shadows still mark the levels.
 * @param {number} level height in levels (may be fractional, e.g. on a ramp)
 * @param {boolean} release
 */
export function levelBrightness(level, release) {
  return Math.min(1, release ? 0.95 + 0.05 * level : 0.8 + 0.07 * level);
}

/**
 * The resolution of a chunk's cached flat ground (gameView.buildChunk, cacheAsTexture), in texture
 * pixels per game pixel: the release terrain has 2 art pixels per game pixel (ART_SCALE), and a cache
 * at 1 drew it at half detail (every 2×2 block of art one pixel). 512 × 512 game px chunk: 4 MB at 2,
 * 1 MB at 1.
 * @param {boolean} release
 */
export function groundCacheResolution(release) {
  return release ? 2 : 1;
}

/**
 * The ambient light indoors (caves, mines, trial rooms, the source's rooms; not the dark trial rooms
 * or the lived-in houses, which have their own). The release ruin and cave stone is darker than the
 * placeholders', so under the placeholders' 0.55 the floors were near black with little contrast
 * against the walls (re-inspection of a25fb7d); the release terrain got 0.65 / 0.65 / 0.75.
 * v1.0 (final QA L-2, "stone rooms are grey and darker than on main"): 0.72 / 0.70 / 0.76, a little
 * brighter and less blue (the release stone is already blue-grey). (0.80 / 0.78 / 0.84 was brighter
 * still but left a fire's warm pool only half as distinct; with weatherView's FIRE_LIGHT_ROOM it is
 * back to about 80% of before.) The dark trial rooms (AMB_DARK_ROOM) are not affected, so their
 * puzzles stay dark.
 * @param {boolean} release
 */
export function indoorLight(release) {
  return release ? { r: 0.72, g: 0.7, b: 0.76 } : { r: 0.55, g: 0.55, b: 0.65 };
}

/**
 * Which of a ground's n variants a tile shows (gameView.surfaceKey), from a stable per-tile hash.
 * The placeholders pick them evenly. The release terrain's variant 0 is the plain one and the others
 * carry a visible mark (reeds, shells, flowers, mushrooms), so variant 0 covers about half of the
 * ground and each other one an equal share (n = 4: 5/8 plain, 1/8 each) — marks no longer form a
 * grid on wide open ground (guide 3.3: variant 0 is the quietest and the most common).
 * @param {number} hash non-negative integer @param {number} n @param {boolean} release
 */
export function groundVariant(hash, n, release) {
  if (!release) return hash % n;
  const k = hash % (2 * n);
  return k <= n ? 0 : k - n;
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
