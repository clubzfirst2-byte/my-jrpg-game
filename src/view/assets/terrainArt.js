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
const REGION_GROUND = /^(desert\.sand|plains\.grass|forest\.grass|mountains\.snow|lake\.grass)\.(?:\d+|macro[2-8]?\.\d|edge\.\d+\.\d)$/;

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

// --- v1.1 (docs/art-release/terrain/NAMES.md): water edges, cliff band variants, plateau faces,
// autumn forest and mountains. These keys have no placeholder: like the hero's frames, they get a
// slot in their bundle only when the art is given, and the view uses them only with the release
// terrain, so the placeholder look is unchanged.

const FEET = /** @type {[number, number]} */ ([0.5, 1]);
const TOP_LEFT = /** @type {[number, number]} */ ([0, 0]);
const EDGE = '(?:\\d+|inner\\.(?:ne|se|sw|nw))\\.[01]';
const PART = '(?:top|mid)(?:-base)?\\.(?:4|8)';
const LIP = 'top(?:-base)?\\.(?:4|8)';
/** Ground v2 pieces: the pictures' 2×2 pieces (macro, macro2 … macro8) and transition edges. */
const V2_PIECE = '(?:macro[2-8]?\\.[0-3]|edge\\.\\d+\\.[01])';
/** v1.1 keys → the bundle that holds them ('placeholder' = the base bundle, a region's, a season's). */
const V11_KEYS = /** @type {[RegExp, string][]} */ ([
  [new RegExp(`^tile\\.(?:shore|bank)\\.${EDGE}$`), 'placeholder'],
  [new RegExp(`^tile\\.shore-desert\\.${EDGE}$`), 'region:desert'],
  [new RegExp(`^face\\.(?:earth|ruin|wall)\\.${PART}\\.v[12]$`), 'placeholder'],
  [new RegExp(`^face\\.stone\\.${PART}\\.v[12]$`), 'region:mountains'],
  [new RegExp(`^face\\.(?:sand|path)\\.${PART}(?:\\.v1)?$`), 'placeholder'],
  [new RegExp(`^face\\.desert\\.${PART}(?:\\.v1)?$`), 'region:desert'],
  [new RegExp(`^winter\\.face\\.earth\\.${LIP}\\.v[12]$`), 'season:winter'],
  [new RegExp(`^autumn\\.face\\.earth\\.${LIP}\\.v[12]$`), 'season:autumn'],
  [new RegExp(`^autumn\\.face\\.stone\\.${LIP}(?:\\.v[12])?$`), 'season:autumn'],
  [/^autumn\.(?:forest\.grass|mountains\.snow)\.\d$/, 'season:autumn'],
  [/^autumn\.(?:forest|mountains)\.pine$/, 'season:autumn'],
  // Ground v2 (src/art-release-v2/terrain, gfx W1; drawn with ?terrain=v2 until enabled): the
  // tiles of each ground (16, or 66 for the ruin floor: groundV2.js), the 8 pictures of 2×2 pieces of
  // every ground but the ruin floor (rounds 4-5: macro, macro2 … macro8), transition edges and the 4-frame water. The island's
  // grounds and the water are listed apart (common:ground; main.js packs them into the base atlas,
  // tallest first, which stays 2048×1024), the ruin floor's edges over water in a bundle of their own
  // (loaded with the chunks where the ruin floor meets water), the regions' and
  // the seasons' in theirs. Keys the v1 bundles already hold (tile.grass.0-2, plains.grass.0-3,
  // tile.water.0/1, ...) are not repeated.
  [new RegExp(`^tile\\.(?:grass\\.(?:[3-9]|\\d\\d)|(?:sand|path|ruin)\\.(?:[1-9]|\\d\\d))$`), 'common:ground'],
  [new RegExp(`^tile\\.(?:grass|sand|path)\\.${V2_PIECE}$`), 'common:ground'],
  [/^tile\.water\.(?:[2-3]|v1\.[0-3]|deep(?:\.v1)?\.[0-3]|deep\.edge\.\d+\.[0-3]|foam\.\d+\.[0-3])$/, 'common:ground'],
  // (round 3: the ruin floor's edges over water, 14 masks × 11 row phases, in a bundle of their own)
  [/^tile\.ruin\.edge\.\d+\.\d+$/, 'common:ruin'],
  [new RegExp(`^plains\\.grass\\.(?:[4-9]|\\d\\d|${V2_PIECE})$`), 'region:plains'],
  [new RegExp(`^lake\\.grass\\.(?:[4-9]|\\d\\d|${V2_PIECE})$`), 'region:lake'],
  [new RegExp(`^forest\\.grass\\.(?:[4-9]|\\d\\d|${V2_PIECE})$`), 'region:forest'],
  [new RegExp(`^mountains\\.snow\\.(?:[4-9]|\\d\\d|${V2_PIECE})$`), 'region:mountains'],
  [new RegExp(`^desert\\.sand\\.(?:[3-9]|\\d\\d|${V2_PIECE})$`), 'region:desert'],
  [new RegExp(`^autumn\\.(?:tile\\.grass\\.(?:[3-9]|\\d\\d)|(?:plains|lake|forest)\\.grass\\.(?:[4-9]|\\d\\d)|(?:tile|plains|lake|forest)\\.grass\\.${V2_PIECE})$`), 'season:autumn'],
  [new RegExp(`^winter\\.(?:tile\\.grass\\.(?:[3-9]|\\d\\d)|(?:plains|lake|forest)\\.grass\\.(?:[4-9]|\\d\\d)|(?:tile|plains|lake|forest)\\.grass\\.${V2_PIECE})$`), 'season:winter'],
]);

/**
 * gfx W1: with the v2 ground, each region's own ground (its grass, moss, snow or desert sand, the v1
 * keys too) is apart from the rest of the region's art, in 2 bundles: "ground:<region>" (its 16 calm
 * tiles and its edges, 256 × 256) and "pictures:<region>" (its 8 pictures' pieces, 256 × 256). A chunk
 * of the region loads both; a chunk whose display tiles reach one cell into the region loads only its
 * ground (no picture can lie there: a picture covers a cell of the chunk drawing it). The region's own
 * atlas keeps its v1 size (gameView.chunkBundles).
 */
export const REGION_GROUND_PREFIX = Object.freeze({
  'region:plains': 'plains.grass',
  'region:lake': 'lake.grass',
  'region:forest': 'forest.grass',
  'region:mountains': 'mountains.snow',
  'region:desert': 'desert.sand',
});

/** The ground bundle of a region bundle ("region:plains" → "ground:plains"), or null. @param {string} region */
export const groundBundleOf = (region) => (region in REGION_GROUND_PREFIX ? `ground:${region.slice('region:'.length)}` : null);

/** The pictures bundle of a region bundle ("region:plains" → "pictures:plains"), or null. @param {string} region */
export const picturesBundleOf = (region) => (region in REGION_GROUND_PREFIX ? `pictures:${region.slice('region:'.length)}` : null);

/**
 * Which part of a region's own ground a key is: "pictures" (<prefix>.macro….<q>), "ground" (its other
 * keys), or null (the rest of the region's art). @param {string} region @param {string} key
 * @returns {'ground' | 'pictures' | null}
 */
export function regionGroundPart(region, key) {
  const p = /** @type {Record<string, string>} */ (REGION_GROUND_PREFIX)[region];
  if (!p || (key !== p && !key.startsWith(`${p}.`))) return null;
  return /^macro\d?\./.test(key.slice(p.length + 1)) ? 'pictures' : 'ground';
}

/**
 * gfx W1 round 6: with the v2 ground, the autumn / winter art of the 4 seasonal grounds (their 32 calm
 * tiles, pictures and edges, 512 × 256 each) is apart from the rest of the season's art, one bundle per
 * ground: "season:<season>:<ground>", loaded only by the chunks that have that ground (gameView.chunkBundles).
 */
export const SEASON_GROUND_PREFIX = Object.freeze({ grass: 'tile.grass', plains: 'plains.grass', lake: 'lake.grass', moss: 'forest.grass' });

/** The bundle of a seasonal ground's art in a season bundle ("season:winter", "plains" → "season:winter:plains"). @param {string} season @param {string} cls */
export const seasonGroundBundleOf = (season, cls) => `${season}:${cls}`;

/** Which seasonal ground a key of a season's art belongs to ("winter.plains.grass.7" → "plains"), or null. @param {string} season e.g. "winter" @param {string} key */
export function seasonGroundOf(season, key) {
  for (const [cls, p] of Object.entries(SEASON_GROUND_PREFIX)) {
    const q = `${season}.${p}`;
    if (key === q || key.startsWith(`${q}.`)) return cls;
  }
  return null;
}

/**
 * gfx W1: with the v2 ground, the bundles a region or season bundle is registered as — [name, keep a
 * key?] — or null when it stays whole: a region as itself, "ground:" and "pictures:"; autumn / winter as
 * themselves and one bundle per seasonal ground. @param {string} name @returns {[string, (key: string) => boolean][] | null}
 */
export function v2BundleParts(name) {
  const ground = groundBundleOf(name);
  const pictures = picturesBundleOf(name);
  if (ground && pictures) {
    return [
      [name, (k) => regionGroundPart(name, k) === null],
      [ground, (k) => regionGroundPart(name, k) === 'ground'],
      [pictures, (k) => regionGroundPart(name, k) === 'pictures'],
    ];
  }
  const season = /^season:(autumn|winter)$/.exec(name)?.[1];
  if (!season) return null;
  return [[name, (k) => seasonGroundOf(season, k) === null], ...Object.keys(SEASON_GROUND_PREFIX).map((cls) => /** @type {[string, (key: string) => boolean]} */ ([seasonGroundBundleOf(name, cls), (k) => seasonGroundOf(season, k) === cls]))];
}

/** gfx W1 round 3: the bundle of the ruin floor's edges over water, loaded with the chunks where the ruin floor meets water (gameView.chunkBundles). */
export const GROUND_RUIN_BUNDLE = 'common:ruin';

/** A key only the v2 ground has (its 4-frame water): the v2 ground is drawn when it is loaded. */
export const GROUND_V2_KEY = 'tile.water.3';
const V11_WATER_EDGE = /^tile\.(?:shore|shore-desert|bank)\./;

/** The bundle a v1.1 terrain key belongs in ('placeholder' = the base bundle), or null. @param {string} key */
export function v11Bundle(key) {
  return V11_KEYS.find(([re]) => re.test(key))?.[1] ?? null;
}

/**
 * The v1.1 terrain entries of one bundle, for the art given (only the names are read). Tiles and
 * faces keep the 16 px grid (placeholderPack.withOverrides checks their size: 32×32, 32×8, 32×16);
 * the pines stand on their feet.
 * @param {string} bundle 'placeholder' (base), 'region:<id>' or 'season:<id>'
 * @param {Map<string, unknown> | Set<string>} [overrides]
 * @returns {{ key: string, rows: string[], anchor: [number, number] }[]}
 */
export function releaseTerrainEntries(bundle, overrides) {
  if (!overrides?.size) return [];
  // Ground v2 replaces the v1.1 water edges (shore tiles, banks) with foam + transitions: with the v2
  // ground given, those pieces get no slot (it keeps the base atlas at 2048×1024).
  const groundV2 = overrides.has(GROUND_V2_KEY);
  return [...overrides.keys()]
    .filter((k) => v11Bundle(k) === bundle && !(groundV2 && V11_WATER_EDGE.test(k)))
    .sort()
    .map((key) => {
      if (key.endsWith('.pine')) return { key, rows: Array(30).fill('.'.repeat(16)), anchor: FEET };
      const h = /^(?:\w+\.)?face\./.test(key) ? (/\.8(?:\.v[12])?$/.test(key) ? 8 : 4) : 16;
      return { key, rows: Array(h).fill('.'.repeat(16)), anchor: TOP_LEFT };
    });
}

/**
 * The keys (without the season's prefix) a season replaces with v1.1 art: the autumn forest and
 * mountains (ground, pines, stone lips) and the season lips of the cliff variants.
 * @param {string} season
 * @returns {string[]}
 */
export function releaseSeasonKeys(season) {
  const lips = (/** @type {string} */ mat) => ['top', 'top-base'].flatMap((p) => [4, 8].flatMap((h) => ['', '.v1', '.v2'].map((v) => `face.${mat}.${p}.${h}${v}`)));
  if (season === 'winter') return lips('earth').filter((k) => k.includes('.v'));
  if (season !== 'autumn') return [];
  return [
    ...lips('earth').filter((k) => k.includes('.v')),
    ...lips('stone'),
    ...[0, 1, 2, 3].flatMap((i) => [`forest.grass.${i}`, `mountains.snow.${i}`]),
    'forest.pine',
    'mountains.pine',
  ];
}

/**
 * The cliff band variant of a tile's face (every segment of it): 0 = the plain key, 1 = ".v1",
 * 2 = ".v2", from the tile's hash, so long cliffs do not repeat every 32 px (release terrain only).
 * The plateau faces (sand, desert, path) have a ".v1" only: hash % 2. The view draws a variant only
 * where its art is loaded (gameView.addFace), else the plain key.
 * @param {number} hash @param {string} mat @param {boolean} release
 */
export function faceVariant(hash, mat, release) {
  if (!release || !mat) return '';
  if (PLATEAU_FACES.includes(mat)) return ['', '.v1'][hash % 2];
  return ['', '.v1', '.v2'][hash % 3];
}

/** The plateau face materials (v1.1), with one band variant (.v1). */
const PLATEAU_FACES = ['sand', 'desert', 'path'];

/**
 * The face material under a raised tile. The placeholders: ruin, wall, the mountains' stone, else
 * earth. The release terrain also has plateau faces for sand (the desert's own) and paths, instead
 * of the grass-lipped earth.
 * @param {'ruin' | 'wall' | 'sand' | 'path' | 'other'} ground @param {string | undefined} region
 * @param {boolean} release
 */
export function faceMaterial(ground, region, release) {
  if (ground === 'ruin') return 'ruin';
  if (ground === 'wall') return 'wall';
  if (release && ground === 'sand') return region === 'desert' ? 'desert' : 'sand';
  if (release && ground === 'path') return 'path';
  return region === 'mountains' ? 'stone' : 'earth';
}

/** The diagonals, the two side bits next to each (a side piece already draws that corner) and the offset. */
const DIAGONALS = /** @type {const} */ ([
  ['ne', 1, 2, 1, -1],
  ['se', 4, 2, 1, 1],
  ['sw', 4, 8, -1, 1],
  ['nw', 1, 8, -1, -1],
]);

/**
 * The water around a tile: the 4-neighbour mask (N = 1, E = 2, S = 4, W = 8) and the diagonals
 * that are water while neither side next to them is (they need an inner-corner piece).
 * @param {(dx: number, dy: number) => boolean} water whether the neighbour at (dx, dy) is water
 * @returns {{ mask: number, corners: ('ne' | 'se' | 'sw' | 'nw')[] }}
 */
export function waterAround(water) {
  const mask = (water(0, -1) ? 1 : 0) | (water(1, 0) ? 2 : 0) | (water(0, 1) ? 4 : 0) | (water(-1, 0) ? 8 : 0);
  const corners = DIAGONALS.filter(([, a, b, dx, dy]) => !(mask & a) && !(mask & b) && water(dx, dy)).map(([d]) => d);
  return { mask, corners };
}

/**
 * The water-edge pieces of a tile (keys without the frame: ".0" / ".1" follow the water).
 *   'shore' / 'shore-desert': a full tile in place of the sand, so one piece only: the side piece
 *     (mask), or an inner corner when only one diagonal is water. A corner beside a side piece, or
 *     2+ corners alone, have no piece of their own (fallback: true; that corner stays plain sand).
 *   'bank': overlays drawn on the grass-like ground; they stack, so every corner gets its piece.
 * @param {'shore' | 'shore-desert' | 'bank'} kind @param {{ mask: number, corners: string[] }} around
 * @returns {{ base: string | null, overlays: string[], fallback: boolean }}
 */
export function waterEdgePieces(kind, { mask, corners }) {
  if (kind === 'bank') {
    return { base: null, overlays: [...(mask ? [`tile.bank.${mask}`] : []), ...corners.map((d) => `tile.bank.inner.${d}`)], fallback: false };
  }
  // v1.0 QA4 L-1: a corner the full shore tile cannot hold (beside a side piece, or a second inner
  // corner) is drawn on top from that corner's quarter of the shore's own inner-corner piece
  // ("<key>#<corner>"): an inner corner's foam stays within its quarter (≤ 10 × 10 art px of 16 × 16),
  // and the rest of the quarter is the same sand as the piece under it. (The bank's corner, tried
  // first, drew its dark earth line on the sand.) fallback: true = composited this way.
  const extra = (/** @type {string[]} */ cs) => cs.map((d) => `tile.${kind}.inner.${d}#${d}`);
  if (mask) return { base: `tile.${kind}.${mask}`, overlays: extra(corners), fallback: corners.length > 0 };
  if (corners.length) return { base: `tile.${kind}.inner.${corners[0]}`, overlays: extra(corners.slice(1)), fallback: corners.length > 1 };
  return { base: null, overlays: [], fallback: false };
}

/**
 * Debug / test helper (window.__debugApi.terrainArt): of the terrain keys loaded right now, which are
 * drawn from the release art (2 pixels per game pixel) and which from the placeholder.
 * @param {import('./assetManager.js').AssetManager} assets
 * @param {any} [view] the game view (v1.1: its chunks' water-edge pieces)
 */
export function terrainDebugApi(assets, view) {
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
    /** v1.1: the water-edge pieces in the built chunks (texture names as drawn now) and the water's frame. */
    terrainEdges: () => {
      const chunks = /** @type {{ edges?: { sprite: { texture: { label?: string } }, key: string }[] }[]} */ ([...(view?.chunks?.values() ?? [])]);
      const edges = chunks.flatMap((c) => c.edges ?? []);
      return { count: edges.length, keys: [...new Set(edges.map((e) => e.key))].sort(), frame: view?.waterFrame ?? -1, fallbacks: view?.edgeStats?.fallbacks ?? 0, groundV2: !!view?.groundV2, water: { ...(view?.waterStats ?? {}) }, missing: [...(view?.v2Missing ?? [])] };
    },
  };
}
