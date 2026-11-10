// @ts-check
// Draws the game state. Reads state only; never writes to it (DESIGN.md 1.1).
//
// Draw order (DESIGN.md 3.3):
//   base      ground at height 0 (cached into one texture; re-cached when water animates)
//   actors    Y-sorted: elevated terrain rows, trees/rocks, shadow, player
//   overlay   player silhouette when something hides the player
// Sort keys: characters/objects use their feet y; an elevated terrain row uses its NORTH edge.
// That one rule puts a character behind a cliff when north of it, on top of it when standing on it,
// and in front of it when south of it.
import { Container, Graphics, Rectangle, Sprite, Texture, TexturePool } from 'pixi.js';
import { chunkRange, CHUNK_KEEP_MARGIN_TILES, CHUNK_LOAD_MARGIN_TILES } from './chunkRange.js';
import { Ground, Shape, LEVEL_PX, inBounds, northEdgeHeight, southEdgeHeight } from '../game/world/tilemap.js';
import { lerp } from '../game/core/math.js';
import { Camera } from './camera.js';
import { windupProgress, ENEMY_KINDS } from '../game/entities/enemies.js';
import { BOSS_KINDS } from '../game/entities/bosses.js';
import { FINAL_BOSS, FINAL_BOSS_ENEMY_ID } from '../game/entities/finalBoss.js';
import { COMBAT } from '../game/entities/playerCombat.js';
import { areaAt } from '../game/world/features.js';
import { sourceFrameKey, drawSourceTelegraphs, drawSeatLights } from './sourceView.js';
import { FeatureView } from './featureView.js';
import { EnvView } from './envView.js';
import { WeatherView, starRingOpen, crystalLightColor } from './weatherView.js';
import { ItemView } from './itemView.js';
import { PuzzleView } from './puzzleView.js';
import { NpcView } from './npcView.js';
import { regionAt, outdoorAt } from '../game/world/world.js';
import { seasonAt } from '../game/env/weather.js';
import { SEASON_ENTRIES, seasonKeys, SOURCE_BUNDLE, SOURCE_REGIONS } from './assets/placeholderPack.js';
import { HeroAnimator } from './heroAnim.js';
import { DECOR_TYPES, decorOffset, macroQuarter, patchVariant, placementEnabled } from './placement.js';
import { CORNERS, MACRO_NAMES, PREFIX, PRIORITY, SEASONAL, WATER_FRAMES, WATER_FRAME_SEC as WATER_FRAME_SEC_V2, calmNumber, deepMap, displayLayers, edgeVariantOf, groundClass, landKey, macroPlacement, quarterOfCorner, ruinCellTile, ruinTile, tileScheme } from './groundV2.js';
import { GROUND_RUIN_BUNDLE, GROUND_V2_KEY, groundBundleOf, picturesBundleOf, seasonGroundBundleOf, faceMaterial, faceVariant, groundCacheResolution, groundVariant, indoorLight, levelBrightness, releaseSeasonKeys, usesReleaseTerrain, waterAround, waterEdgePieces } from './assets/terrainArt.js';
import { openingView } from '../game/story/story.js';
import { enemyFrameKey, warningFlashAlpha, defeatAlpha } from './enemyAnim.js';
import { SilhouetteCache, placeFlash } from './flashOverlay.js';
import { EnemySlots } from './enemySlots.js';

/** Chunk size in tiles (P8). */
export const CHUNK = 32;

/** gfx W1: the ground classes whose art is in their region's bundle (groundV2.groundClass). */
const REGION_GROUNDS = new Set(['plains', 'lake', 'moss', 'snow', 'dsand']);

/**
 * The area a chunk's flat ground is cached over (world px): always the whole chunk, never just the
 * part that has flat ground in it.
 *
 * v1.0 final (QA C-1, "a thin black line across the grass north of the beach ring"): the cache
 * texture used to be sized to the flat ground's bounds. A chunk whose top rows are raised (drawn in
 * the Y-sorted rows instead) then asked for e.g. 512×384, and PixiJS's texture pool (8.21+) gave it a
 * texture backed at the SCREEN's height (394 at 852×393, DPR 2) rather than a power of two. With a
 * backing taller than the frame, the tiles' pixel snapping in that render lands a few tile edges one
 * texel off, leaving 1-texel rows of the cache transparent: a dark line across the whole chunk
 * (island chunk 1,1: world rows 46 and 58). It only showed at screen sizes whose height a chunk's flat
 * part fits under. A whole chunk is 512×512 (CHUNK × 16 px, a power of two): the pool always backs
 * that at exactly 512×512, so frame and backing match at every screen size. (Also a chunk at the
 * edge of a map whose size is not a whole number of chunks: the area past the edge stays transparent.)
 * @param {number} cx @param {number} cy @param {number} ts tile size (px)
 */
export function chunkCacheArea(cx, cy, ts) {
  const size = CHUNK * ts;
  return { x: cx * size, y: cy * size, width: size, height: size };
}

/**
 * @typedef {import('../game/world/world.js').RegionInfo} RegionInfo
 * @typedef {{ cx: number, cy: number, base: Container, rows: Map<number, Container>, water: Sprite[],
 *   edges: { sprite: Sprite, key: string }[], waterFrame: number,
 *   extents: Map<number, { x0: number, x1: number, y0: number, y1: number }[]>, bundles: string[] }} Chunk
 */

const WALK_FPS = 8;
const WALK_CYCLE = [1, 0, 2, 0];
const WATER_FRAME_SEC = 0.6;
const EDGE_COLOR = 0x1a1c2c;
const TREE_FADE_ALPHA = 0.5;
const CLIFF_SHADOW_PX = 6;
const EDGE_PX = 2;
const GLIDER_SHOULDER_Y = 9;
/** v1.0 (C9): the pendant on the hero's chest, in placeholder pixels above his feet (×heroK). */
const PENDANT_Y = 7;
/** The hero's placeholder height in game pixels; offsets around the hero below are for this size
 *  and scale with the hero's real height (P11.5: the 32×56 art is 28 game pixels tall). */
const HERO_BASE_H = 16;
const STAMINA_OK = 0x7bd46a;
const STAMINA_LOW = 0xe8c14a;
const STAMINA_EXHAUSTED = 0xe8505b;
/** Aim at the body rather than the feet. */
const CAMERA_TARGET_OFFSET_Y = 8;
const CLIFF_SHADOW_ALPHA = 0.32;

/**
 * Higher ground is drawn slightly brighter so levels read at a glance (multiplicative tint).
 * v1.0: the release terrain is tinted less (terrainArt.levelBrightness).
 * @param {number} heightPx
 * @param {boolean} [release] whether the terrain is the release art
 */
export function levelTint(heightPx, release = false) {
  const level = heightPx / LEVEL_PX;
  const v = Math.round(255 * levelBrightness(level, release));
  return (v << 16) | (v << 8) | v;
}

/** @typedef {{ sprite: Sprite, x0: number, x1: number, y0: number, y1: number, key: number }} Occluder */

export class GameView {
  /**
   * @param {import('pixi.js').Application} app
   * @param {import('./assets/assetManager.js').AssetManager} assets
   * @param {import('../game/state.js').GameState} state
   */
  constructor(app, assets, state) {
    this.app = app;
    this.assets = assets;
    /** v1.0: the terrain is drawn from its release art (its brightness and variants, terrainArt.js). */
    this.releaseTerrain = usesReleaseTerrain(assets);
    /** P10.2: the season the world is drawn for, and its art bundle (held while it lasts). */
    /** @type {string | null} */
    this.season = null;
    /** @type {string | null} */
    this.seasonBundle = null;
    /** @type {string | null} */
    this.seasonLoading = null;
    /** @type {string | null} */
    this.seasonLoaded = null;
    /** @type {Set<string>} */
    this.seasonKeySet = new Set();
    this.map = state.map;
    this.world = new Container();
    this.world.label = 'world';
    this.base = new Container();
    this.base.label = 'base';
    this.actors = new Container();
    this.actors.label = 'actors';
    this.actors.sortableChildren = true;
    this.overlay = new Container();
    this.overlay.label = 'overlay';
    this.world.addChild(this.base, this.actors, this.overlay);
    app.stage.addChildAt(this.world, 0);

    // Camera (DESIGN.md 3.5): outdoors = the map (or its outdoor part); areas (caves) set their own.
    this.camera = new Camera();
    /** @type {string | null} id of the area whose bounds are applied ('' = outdoors) */
    this.boundsArea = null;
    /** @type {string | null} */
    this.boundsKey = null;
    this.applyBounds(state);

    this.waterFrame = -1;
    // P8: the terrain and objects are built in chunks around the camera and freed behind it.
    /** @type {Map<string, Chunk>} */
    this.chunks = new Map();
    /** @type {Map<any, { o: any, sprite: Sprite, occluder: Occluder | null }>} object -> its sprite (loaded chunks only) */
    this.objectSprites = new Map();
    /** @type {RegionInfo[]} */
    this.regions = state.regions ?? [];
    /**
     * v1.0 QA4 L-6: the desert's trees stand on a tile of grass (the map's tree tile), which read as
     * a square green patch in the sand; with the release terrain those tiles are drawn as desert sand
     * (only the look: the ground stays grass for the game, so fire and saves are unchanged).
     * @type {Set<number>}
     */
    /** QA4 L-1: quarters of shore pieces, per texture (dropped with it). @type {WeakMap<Texture, Map<string, Texture>>} */
    this.edgeQuarters = new WeakMap();
    /**
     * W2 (graphics v2): the placement layer — decorative objects drawn off-centre in clusters, ground
     * variants in patches, 2×2 macro pieces where the art has them (placement.js). Release terrain
     * only; ?placement=0 to compare.
     */
    this.placement = this.releaseTerrain && placementEnabled();
    /** @type {any[]} the outdoor areas (decorative placement is for outdoors, not the rooms' rock walls) */
    this.outdoors = state.outdoors ?? [];
    /** W2: how many variants each ground has in the loaded art (W1 adds more), per bundle state. @type {{ version: string, counts: Map<string, number> }} */
    this.variantCounts = { version: '', counts: new Map() };
    /**
     * gfx W1: the v2 ground (src/art-release-v2/terrain, ?terrain=v2 until enabled) is drawn on the dual
     * grid with transitions and 4-frame water (groundV2.js). Known by its art being loaded.
     */
    this.groundV2 = this.releaseTerrain && assets.hasTexture(GROUND_V2_KEY);
    /** W1: deep water cells (no land within 2 cells), fixed for the map. @type {Uint8Array | null} */
    this.deepWater = null;
    /** W1: per display tile, its lowest flat land and its macro piece (fixed for the map). @type {Map<string, any>} */
    this.v2Tiles = new Map();
    /** W1: water redraws of the chunk caches (count, total ms) and the view rectangle (only visible chunks redraw). */
    this.waterStats = { redraws: 0, ms: 0, deferred: 0 };
    /** W1: ground keys asked for and not in the loaded art (tests: none). @type {Set<string>} */
    this.v2Missing = new Set();
    /** W1 round 6: the calm tiles' numbers of the display grid / of the cell grid, only while a chunk is built (groundV2.calmNumber). @type {Map<number, number> | null} */
    this.calmMemo = null;
    /** @type {Map<number, number> | null} */
    this.cellCalmMemo = null;
    /** W1 round 6: the blocks' picture numbers (groundV2.blockPicture), fixed for the map; one per 3×3 display tiles. @type {Map<number, number> | null} */
    this.v2Pictures = null;
    /** @type {{ x: number, y: number, w: number, h: number } | null} */
    this.viewRect = null;
    this.sandUnderTrees = new Set(
      this.releaseTerrain
        ? (state.map.objects ?? [])
            .filter((/** @type {any} */ o) => o.type === 'tree' && state.map.ground[o.ty * state.map.width + o.tx] === Ground.GRASS && regionAt(this.regions, o.tx, o.ty)?.id === 'desert')
            .map((/** @type {any} */ o) => o.ty * state.map.width + o.tx)
        : [],
    );
    /** Bundles being loaded (async). @type {Set<string>} */
    this.bundlesLoading = new Set();
    /** Bundles loaded ahead of their chunks (one reference held here). @type {Set<string>} */
    this.preloaded = new Set();
    /** Load every chunk at once (?chunks=all: for comparing against streaming). */
    this.loadAll = false;
    this.chunkStats = { built: 0, freed: 0, pending: 0, updates: 0 };
    /** Chunks were freed since the last update: their cache textures sit idle in the TexturePool. */
    this.chunkCachesFreed = false;
    /** v1.1: shore tiles whose corner water has no piece (left plain sand), counted as chunks are built. */
    this.edgeStats = { fallbacks: 0 };
    this.hasBraziers = this.map.objects.some((o) => o.type === 'brazier');
    // Screen-space layer above the world (landmark markers).
    this.screenLayer = new Container();
    this.screenLayer.label = 'screen';
    app.stage.addChild(this.screenLayer);
    this.features = new FeatureView((key) => this.makeSprite(key), this.actors, this.screenLayer, state);
    // Environment (P4): ash / wet ground goes between the cached ground and the actors.
    this.envGround = new Container();
    this.envGround.label = 'env-ground';
    this.world.addChildAt(this.envGround, 1);
    this.env = new EnvView(
      (key) => this.makeSprite(key),
      (key) => this.assets.texture(key),
      this.envGround,
      this.actors,
      state,
    );
    this.envVersion = -1;
    this.charmHome = false;
    /** v1.0: the beach ring glows while it is a gate */
    this.ringOpen = false;
    /** v1.0: the source's art bundle: held only while the player is in the desert (its arena is there) */
    this.sourceHeld = false;
    this.sourceLoading = false;
    /** @type {Graphics | null} v1.0: the source's telegraphs (ground) and seat lights */
    this.sourceGround = null;
    /** @type {Graphics | null} */
    this.sourceMarks = null;
    /** @type {Graphics | null} P10.4: slam telegraph */
    this.bossRing = null;
    this.items = new ItemView((key) => this.makeSprite(key), this.actors);
    this.npcs = new NpcView(assets, (key) => this.makeSprite(key), this.actors);
    this.puzzles = new PuzzleView(
      (key) => this.makeSprite(key),
      (key) => this.assets.texture(key),
      this.envGround,
      this.actors,
      this.overlay,
      state,
    );
    // Time of day and weather (P5): light map, rain, lightning, above the world.
    this.weather = new WeatherView(app, (key) => this.makeSprite(key), this.actors);
    this.weather.crystalLight = crystalLightColor(assets.texture('obj.crystal'));
    this.weather.attach(app.stage, app.stage.getChildIndex(this.world) + 1);
    this.weather.indoorAmbient = indoorLight(this.releaseTerrain);
    // (v1.0 attack warnings stay in the world, sorted with their enemy, so trees in front hide them;
    // at night the light map lights each winding-up enemy instead: weatherView.js warningLights.)

    this.shadow = this.makeSprite('fx.shadow');
    this.shadow.alpha = 0.35;
    this.player = this.makeSprite('player.walk.down.0');
    this.silhouette = this.makeSprite('player.walk.down.0');
    this.silhouette.tint = 0x101828;
    this.silhouette.alpha = 0.55;
    this.silhouette.visible = false;
    this.glider = this.makeSprite('fx.glider');
    this.glider.visible = false;
    this.actors.addChild(this.shadow, this.player, this.glider);
    // v1.0 (C9): the pendant's glow in the opening (a soft blue light on the hero's chest).
    this.pendantGlow = new Graphics();
    for (const [r, a] of /** @type {const} */ ([[7, 0.18], [4.5, 0.32], [2.5, 0.6], [1, 1]])) this.pendantGlow.circle(0, 0, r).fill({ color: r > 1 ? 0x7fe8ff : 0xffffff, alpha: a });
    this.pendantGlow.visible = false;
    this.actors.addChild(this.pendantGlow);
    // Stamina wheel beside the player (shown only while not full).
    this.staminaWheel = new Graphics();
    this.staminaWheel.visible = false;
    this.overlay.addChild(this.silhouette, this.staminaWheel);

    // --- P3 combat visuals ---
    /** One sprite per enemy, tied to the enemy object it was made for (ids are reused on respawn: enemySlots.js). */
    /** @type {EnemySlots<Sprite>} */
    this.enemySprites = new EnemySlots((id, spr) => this.releaseEnemySprite(id, spr));
    /** v1.0: each enemy's frame (tests, ?debug) and its wind-up warning overlay (made on first use). */
    /** @type {Map<number, string>} */
    this.enemyKeys = new Map();
    /** @type {Map<number, Sprite>} */
    this.flashSprites = new Map();
    this.silhouettes = new SilhouetteCache();
    /** Frame counts of the enemies' release actions, cleared when the loaded art changes. @type {Map<string, number>} */
    this.enemyFrameCounts = new Map();
    this.enemyFrameCountsAt = -1;
    /** @param {string} k */
    this.hasTexture = (k) => this.assets.hasTexture(k);
    /** @type {Sprite[]} */
    this.projectileSprites = [];
    this.slash = this.makeSprite('fx.slash');
    this.slash.visible = false;
    this.shield = this.makeSprite('fx.shield');
    this.shield.visible = false;
    this.bow = this.makeSprite('fx.bow');
    this.bow.visible = false;
    this.actors.addChild(this.slash, this.shield, this.bow);
    this.aimLine = new Graphics();
    this.overlay.addChild(this.aimLine);
    // Screen-space tint for slow motion (perfect dodge / bullet time).
    this.slowTint = new Graphics();
    this.slowTint.visible = false;
    app.stage.addChild(this.slowTint);
    /** True while the player is hidden behind terrain (exposed for tests). */
    this.playerOccluded = false;
    /** How much taller the drawn hero is than the placeholder (P11.5). */
    this.heroK = 1;
    /** The hero's animation (release art; heroAnim.js). */
    this.heroAnim = new HeroAnimator();
    /** @type {import('./heroAnim.js').HeroPose | null} */
    this.heroPose = null;
    /** The release texture drawn for the hero (null: the placeholder hero). @type {string | null} */
    this.heroKey = null;
  }

  /** The texture name for the current season (P10.2: e.g. "obj.tree" -> "autumn.obj.tree"). @param {string} key */
  seasonal(key) {
    return this.seasonKeySet.has(key) ? `${this.season}.${key}` : key;
  }

  /** @param {string} key */
  makeSprite(key) {
    const k = this.seasonal(key);
    const s = new Sprite(this.assets.texture(k));
    const [ax, ay] = this.assets.meta(k).anchor;
    s.anchor.set(ax, ay);
    return s;
  }

  /**
   * P10.2: dresses the world for the season. The new season's art is loaded first (the old look stays
   * on screen meanwhile); then every chunk is rebuilt at once with it, and the old season's art is
   * released. Summer is the plain art.
   * @param {number} worldMs
   */
  updateSeason(worldMs) {
    const want = seasonAt(worldMs).id;
    if (want === this.season) return;
    const bundle = SEASON_ENTRIES[`season:${want}`] ? `season:${want}` : null;
    if (bundle && !this.assets.isLoaded(bundle)) {
      if (this.seasonLoading !== bundle) {
        this.seasonLoading = bundle;
        this.assets.load(bundle).then(
          () => {
            // Arrived too late (the season moved on): let it go.
            if (this.seasonLoading !== bundle) this.assets.unload(bundle);
            else this.seasonLoaded = bundle;
          },
          () => (this.seasonLoading = null),
        );
      }
      if (this.seasonLoaded !== bundle) return;
    }
    for (const c of this.chunks.values()) this.destroyChunk(c);
    this.chunks.clear();
    if (this.seasonBundle) this.assets.unload(this.seasonBundle);
    this.seasonBundle = bundle;
    this.seasonLoading = null;
    this.seasonLoaded = null;
    this.season = want;
    this.seasonKeySet = seasonKeys(want);
    // v1.1: the release terrain's own season keys (autumn forest and mountains, the lips of the cliff
    // variants), where the season's bundle has them.
    if (this.releaseTerrain) for (const k of releaseSeasonKeys(want)) if (this.assets.hasTexture(`${want}.${k}`)) this.seasonKeySet.add(k);
    // gfx W1: the v2 ground's season keys (32 calm tiles, the 8 pictures' pieces, edges of the 4 seasonal grounds);
    // the mountains' snow has no v2 seasons, so its ground and its edges stay as they are.
    if (this.groundV2 && want) {
      for (const k of [...this.seasonKeySet]) if (k.startsWith('mountains.snow.')) this.seasonKeySet.delete(k);
      for (const cls of SEASONAL) {
        const p = /** @type {any} */ (PREFIX)[cls];
        const names = [...Array.from({ length: 32 }, (_, n) => String(n)), ...MACRO_NAMES.flatMap((m) => [0, 1, 2, 3].map((q) => `${m}.${q}`)), ...Array.from({ length: 14 }, (_, m) => [0, 1].map((v) => `edge.${m + 1}.${v}`)).flat()];
        // (each seasonal ground's season art is a bundle of its own, loaded by the chunks that have it)
        const apart = bundle !== null && this.assets.builders.has(seasonGroundBundleOf(bundle, cls));
        for (const n of names) {
          const k = landKey(cls, n);
          if (k !== p && (apart || this.assets.hasTexture(`${want}.${k}`))) this.seasonKeySet.add(k);
        }
      }
    }
    this.envVersion = -1;
  }

  /** @param {number} tx @param {number} ty */
  surfaceKey(tx, ty) {
    // W1 round 2: with the v2 ground, a land cell on the cell grid (raised ground) takes its edge-matched tile
    if (this.groundV2) {
      const cls = this.groundClassAt(tx, ty);
      if (cls && cls !== 'water') return landKey(cls, String(this.cellWang(tx, ty, cls)));
    }
    const g = this.drawnGround(tx, ty);
    // P8: each region dresses the same ground in its own art (its asset bundle).
    const region = regionAt(this.regions, tx, ty);
    if (region?.id === 'desert' && g === Ground.SAND) return this.groundKey(tx, ty, 'desert.sand', 3);
    if (region?.id === 'plains' && g === Ground.GRASS) return this.groundKey(tx, ty, 'plains.grass', 4);
    // P10.3: the east column.
    if (region?.id === 'forest' && g === Ground.GRASS) return this.groundKey(tx, ty, 'forest.grass', 4);
    if (region?.id === 'mountains' && g === Ground.GRASS) return this.groundKey(tx, ty, 'mountains.snow', 4);
    if (region?.id === 'lake' && g === Ground.GRASS) return this.groundKey(tx, ty, 'lake.grass', 4);
    if (g === Ground.WOOD) return 'tile.wood';
    if (g === Ground.WALL) return 'tile.walltop';
    if (g === Ground.DARK) return 'tile.dark';
    if (g === Ground.PATH) return 'tile.path';
    if (g === Ground.WATER) return 'tile.water.0';
    if (g === Ground.RUIN) return 'tile.ruin';
    if (g === Ground.SAND) return 'tile.sand';
    if (g === Ground.METAL) return 'tile.metal';
    if (g === Ground.PIT) {
      // v1.0: a pit's far wall is drawn on its top row only; below a pit tile it is all dark.
      if (this.releaseTerrain && ty > 0 && this.map.ground[(ty - 1) * this.map.width + tx] === Ground.PIT) return 'tile.dark';
      return 'tile.pit';
    }
    return this.groundKey(tx, ty, 'tile.grass', 3);
  }

  /** Which of a ground's n variants tile (tx, ty) shows (terrainArt.groundVariant). @param {number} tx @param {number} ty @param {number} n */
  variant(tx, ty, n) {
    return groundVariant(hash(tx, ty), n, this.releaseTerrain);
  }

  /**
   * The key of a varied ground ("<base>.<variant>"). W2: with the placement layer, the variant comes
   * in patches (placement.patchVariant) out of however many variants the loaded art has (at least n),
   * and a 2×2 macro piece ("<base>.macro.<q>") replaces 4 tiles of the same ground where the art has one.
   * @param {number} tx @param {number} ty @param {string} base @param {number} n the variants every set has
   */
  groundKey(tx, ty, base, n) {
    if (!this.placement) return `${base}.${this.variant(tx, ty, n)}`;
    const macro = this.macroKey(tx, ty, base);
    if (macro) return macro;
    return `${base}.${patchVariant(tx, ty, this.variantCount(base, n))}`;
  }

  /** How many variants "<base>.<k>" the loaded art has (n at least; W1 may give 6–8). @param {string} base @param {number} n */
  variantCount(base, n) {
    const counts = this.countsCache();
    let c = counts.get(base);
    if (c === undefined) {
      c = n;
      // (a ground the season redraws counts only the variants the season has too)
      const seasonal = this.seasonKeySet.has(`${base}.0`);
      while (c < 8 && this.assets.hasTexture(`${base}.${c}`) && (!seasonal || this.assets.hasTexture(`${this.season}.${base}.${c}`))) c++;
      counts.set(base, c);
    }
    return c;
  }

  /** The art counts (variants, macro sets), kept while the loaded art and the season stay the same. */
  countsCache() {
    const version = `${this.assets.version}|${this.season}`;
    if (this.variantCounts.version !== version) this.variantCounts = { version, counts: new Map() };
    return this.variantCounts.counts;
  }

  /**
   * W2: a 2×2 macro piece's key for this tile, when the art has macro pieces for this ground, the block
   * is chosen (placement.macroQuarter), and its 4 tiles are flat ground of the same kind with no water edge.
   * @param {number} tx @param {number} ty @param {string} base @returns {string | null}
   */
  macroKey(tx, ty, base) {
    if (!this.assets.hasTexture(`${base}.macro.0`)) return null;
    const q = macroQuarter(tx, ty);
    if (q < 0) return null;
    const bx = tx - (q % 2);
    const by = ty - (q >> 1);
    const map = this.map;
    const g = this.drawnGround(tx, ty);
    const region = regionAt(this.regions, tx, ty);
    for (let k = 0; k < 4; k++) {
      const x = bx + (k % 2);
      const y = by + (k >> 1);
      if (!inBounds(map, x, y)) return null;
      const i = y * map.width + x;
      if (this.drawnGround(x, y) !== g || map.elev[i] !== 0 || map.shape[i] === Shape.RAMP_N || regionAt(this.regions, x, y) !== region || this.waterEdge(x, y)) return null;
    }
    return `${base}.macro.${q}`;
  }

  /**
   * v1.1: the water-edge pieces of a flat tile next to water (release terrain): a shore tile in place
   * of the island's or the desert's sand, bank overlays on grass-like ground (terrainArt.waterEdgePieces).
   * Only water at the same height counts. Counts the corners left plain (edgeStats.fallbacks).
   * @param {number} tx @param {number} ty @returns {{ base: string | null, overlays: string[] } | null}
   */
  waterEdge(tx, ty) {
    const map = this.map;
    const i = ty * map.width + tx;
    const g = this.drawnGround(tx, ty);
    // v1.0 QA4 L-2: paths get the grass's bank too (their straight edge stood out beside the banks).
    if (g !== Ground.SAND && g !== Ground.GRASS && g !== Ground.PATH) return null;
    const water = (/** @type {number} */ dx, /** @type {number} */ dy) => {
      const nx = tx + dx;
      const ny = ty + dy;
      if (!inBounds(map, nx, ny)) return false;
      const j = ny * map.width + nx;
      return map.ground[j] === Ground.WATER && map.elev[j] === map.elev[i];
    };
    const around = waterAround(water);
    if (!around.mask && !around.corners.length) return null;
    const kind = g !== Ground.SAND ? 'bank' : regionAt(this.regions, tx, ty)?.id === 'desert' ? 'shore-desert' : 'shore';
    const pieces = waterEdgePieces(kind, around);
    if (pieces.fallback) this.edgeStats.fallbacks++;
    // Art missing (should not happen with the release terrain): the plain ground.
    const ok = (/** @type {string} */ k) => this.assets.hasTexture(`${k.split('#')[0]}.0`);
    return { base: pieces.base && ok(pieces.base) ? pieces.base : null, overlays: pieces.overlays.filter(ok) };
  }

  /** W1: the deep-water map, computed on first use. */
  deepAt(/** @type {number} */ x, /** @type {number} */ y) {
    const map = this.map;
    if (!this.deepWater) this.deepWater = deepMap(map.width, map.height, (cx, cy) => map.ground[cy * map.width + cx] === Ground.WATER);
    return this.deepWater[y * map.width + x] === 1;
  }

  /** W1: a cell's ground class for the dual grid (null: drawn on the cell grid). @param {number} x @param {number} y */
  groundClassAt(x, y) {
    const g = this.drawnGround(x, y);
    const name = g === Ground.GRASS ? 'grass' : g === Ground.SAND ? 'sand' : g === Ground.PATH ? 'path' : g === Ground.RUIN ? 'ruin' : g === Ground.WATER ? 'water' : 'other';
    return groundClass(name, regionAt(this.regions, x, y)?.id);
  }

  /** W1: whether a key's art is loaded in the current season (a miss is recorded: tests expect none). @param {string} key */
  v2Has(key) {
    const k = this.seasonal(key);
    if (this.assets.hasTexture(k)) return true;
    this.v2Missing.add(k);
    return false;
  }

  /** W1: the texture of a key in the current season, or null when its art is not loaded. @param {string} key */
  v2Texture(key) {
    return this.v2Has(key) ? this.assets.texture(this.seasonal(key)) : null;
  }

  /**
   * W1: a cell's own tile on the cell grid (for display tiles that cannot blend): its v2 land tile, its
   * water (animated: key without the frame), or its v1 tile (wood, wall top, metal, pit, dark).
   * @param {number} x @param {number} y @returns {{ key: string, anim: boolean }}
   */
  cellKeyV2(x, y) {
    const cls = this.groundClassAt(x, y);
    if (cls === 'water') return { key: `tile.water${this.deepAt(x, y) ? '.deep' : ''}${hash(x, y) % 2 ? '.v1' : ''}`, anim: true };
    if (!cls) return { key: this.surfaceKey(x, y), anim: false };
    return { key: landKey(cls, String(this.cellWang(x, y, cls))), anim: false };
  }

  /**
   * W1 rounds 2-6: the tile of a cell drawn on the cell grid (raised ground, and quarters of cells that
   * cannot blend), picked as its ground asks (groundV2.js): A a calm tile (calmNumber over the cells, as
   * over the display tiles), C the ruin floor by its row and column.
   * @param {number} x @param {number} y @param {string} cls
   */
  cellWang(x, y, cls) {
    return tileScheme(cls) === 'C' ? ruinCellTile(x, y, hash) : calmNumber(x, y, hash, this.cellCalmMemo ?? undefined);
  }

  /**
   * W1: the lowest land of display tile (i, j) when it is all flat land (render_ref.lowest_land; null
   * when a corner is water, a ground without v2 art, raised or a ramp). Cached for the map.
   * @param {number} i @param {number} j @returns {string | null}
   */
  lowestLand(i, j) {
    const key = `l${i},${j}`;
    if (this.v2Tiles.has(key)) return this.v2Tiles.get(key);
    const map = this.map;
    let low = /** @type {string | null} */ (null);
    for (const [dx, dy] of CORNERS) {
      const x = Math.max(0, Math.min(map.width - 1, i + dx));
      const y = Math.max(0, Math.min(map.height - 1, j + dy));
      const c = this.groundClassAt(x, y);
      if (!c || c === 'water' || map.elev[y * map.width + x] !== 0 || map.shape[y * map.width + x] === Shape.RAMP_N) {
        low = null;
        break;
      }
      if (!low || PRIORITY.indexOf(c) < PRIORITY.indexOf(low)) low = c;
    }
    this.v2Tiles.set(key, low);
    return low;
  }

  /**
   * W1: whether the (k+1)×(k+1) cells from (i, j) are one flat land ground (a k×k block of display
   * tiles on uniform ground), and which. @param {number} i @param {number} j @param {number} k
   */
  uniformBlock(i, j, k) {
    const map = this.map;
    let g = /** @type {string | null} */ (null);
    for (let dy = 0; dy <= k; dy++) {
      for (let dx = 0; dx <= k; dx++) {
        const x = i + dx;
        const y = j + dy;
        if (!inBounds(map, x, y) || map.elev[y * map.width + x] !== 0 || map.shape[y * map.width + x] === Shape.RAMP_N) return null;
        const c = this.groundClassAt(x, y);
        if (!c || c === 'water' || (g && c !== g)) return null;
        g = c;
      }
    }
    return g;
  }

  /**
   * W1: the picture piece of display tile (i, j), or null: groundV2.macroPlacement (the placement rule
   * lives there alone), cached per map (the same in every season).
   * @param {number} i @param {number} j @returns {{ name: string, block: string } | null}
   */
  macroAt(i, j) {
    const key = `m${i},${j}`;
    if (this.v2Tiles.has(key)) return this.v2Tiles.get(key);
    if (!this.v2Pictures) this.v2Pictures = new Map();
    const out = macroPlacement(i, j, { uniformBlock: (a, b, k) => this.uniformBlock(a, b, k), hash, width: this.map.width, height: this.map.height, pictures: this.v2Pictures });
    this.v2Tiles.set(key, out);
    return out;
  }

  /**
   * W1 rounds 2-6: the tile of display tile (i, j) whose lowest land is cls (render_ref), picked as its
   * ground asks (groundV2.js); a picture piece, where one is placed, is drawn instead (macroAt):
   *   A  a calm tile 0-31 (calmNumber: light / dark group, never a neighbour's number);
   *   C  the ruin floor: its row phase and its column's symbols.
   * @param {number} i @param {number} j @param {string} cls
   */
  wangAt(i, j, cls) {
    return tileScheme(cls) === 'C' ? ruinTile(i, j, hash) : calmNumber(i, j, hash, this.calmMemo ?? undefined);
  }

  /**
   * W1: the flat ground of a chunk on the dual grid (groundV2.js): display tile (i, j) at
   * (i*16 + 8, j*16 + 8) over the cells (i..i+1, j..j+1). The chunk draws the display tiles that reach
   * into it (its cache area clips the overhang), so chunk borders join. A display tile blends only when
   * its 4 corners are flat ground with v2 art; otherwise each flat corner shows its quarter of its own
   * cell's tile (raised cells are drawn by their rows, and the cliff faces separate them).
   * @param {Container} base @param {{ sprite: Sprite, key: string }[]} edges @param {number} cx @param {number} cy
   */
  buildGroundV2(base, edges, cx, cy) {
    const frame = Math.max(0, this.waterFrame);
    for (const p of this.groundPiecesV2(cx, cy)) {
      let tex = null;
      if (p.anim) {
        if (this.assets.hasTexture(`${p.key}.0`)) tex = this.edgeTexture(p.quarter ? `${p.key}#${p.quarter}` : p.key, frame);
        else this.v2Missing.add(`${p.key}.0`);
      } else {
        tex = this.v2Texture(p.key);
        if (tex && p.quarter) tex = this.quarterTexture(tex, p.quarter);
      }
      if (!tex) continue;
      const s = new Sprite(tex);
      s.position.set(p.x, p.y);
      base.addChild(s);
      if (p.anim) edges.push({ sprite: s, key: p.quarter ? `${p.key}#${p.quarter}` : p.key });
    }
  }

  /**
   * W1: what buildGroundV2 draws for a chunk, bottom first: each piece's key (season not applied;
   * anim: a water key without its frame), its position in game px and, for a cell that cannot blend,
   * the quarter of its tile. Pure apart from the view's caches (unit tests walk the world with it).
   * @param {number} cx @param {number} cy
   * @returns {{ key: string, anim: boolean, x: number, y: number, quarter: string | null }[]}
   */
  groundPiecesV2(cx, cy) {
    const map = this.map;
    const ts = map.tileSize;
    const half = ts / 2;
    const clampX = (/** @type {number} */ x) => Math.max(0, Math.min(map.width - 1, x));
    const clampY = (/** @type {number} */ y) => Math.max(0, Math.min(map.height - 1, y));
    const flat = (/** @type {number} */ x, /** @type {number} */ y) => map.elev[y * map.width + x] === 0 && map.shape[y * map.width + x] !== Shape.RAMP_N;
    const i1 = Math.min(map.width, (cx + 1) * CHUNK) - 1;
    const j1 = Math.min(map.height, (cy + 1) * CHUNK) - 1;
    /** @type {{ key: string, anim: boolean, x: number, y: number, quarter: string | null }[]} */
    const out = [];
    // round 6: a calm tile's number depends on its neighbours' (groundV2.calmNumber): worked out once per
    // chunk build, in memos that live only while the chunk is built (buildChunk; nothing per frame, nothing kept)
    const own = !this.calmMemo;
    if (own) {
      this.calmMemo = new Map();
      this.cellCalmMemo = new Map();
    }
    try {
      this.groundPiecesInto(out, cx, cy, j1, i1, clampX, clampY, flat, half, ts);
    } finally {
      if (own) {
        this.calmMemo = null;
        this.cellCalmMemo = null;
      }
    }
    return out;
  }

  /**
   * groundPiecesV2's loop. @param {{ key: string, anim: boolean, x: number, y: number, quarter: string | null }[]} out
   * @param {number} cx @param {number} cy @param {number} j1 @param {number} i1
   * @param {(x: number) => number} clampX @param {(y: number) => number} clampY @param {(x: number, y: number) => boolean} flat
   * @param {number} half @param {number} ts
   */
  groundPiecesInto(out, cx, cy, j1, i1, clampX, clampY, flat, half, ts) {
    const map = this.map;
    for (let j = cy * CHUNK - 1; j <= j1; j++) {
      for (let i = cx * CHUNK - 1; i <= i1; i++) {
        const px = i * ts + half;
        const py = j * ts + half;
        const cells = CORNERS.map(([dx, dy]) => [clampX(i + dx), clampY(j + dy)]);
        const cls = cells.map(([x, y]) => this.groundClassAt(x, y));
        if (cells.every(([x, y]) => flat(x, y)) && cls.every((c) => c !== null)) {
          const layers = displayLayers({
            cls: /** @type {string[]} */ (cls),
            deep: cells.map(([x, y]) => this.deepAt(x, y)),
            waterVariant: hash(i, j) % 2,
            edgeVariant: (c) => edgeVariantOf(c, i, j, hash),
            // round 2: the edge-matched tile, or a macro piece where a block is placed
            pick: (c) => String(this.wangAt(i, j, c)),
            macro: () => {
              const m = this.macroAt(i, j);
              return m && this.v2Has(landKey(/** @type {string} */ (cls[0]), m.name)) ? m.name : null;
            },
          });
          for (const l of layers) out.push({ key: l.key, anim: l.anim, x: px, y: py, quarter: null });
          continue;
        }
        // cannot blend: each flat corner inside the map shows its own cell's quarter
        CORNERS.forEach(([dx, dy], k) => {
          const x = i + dx;
          const y = j + dy;
          if (!inBounds(map, x, y) || !flat(x, y)) return;
          const own = this.cellKeyV2(x, y);
          out.push({ key: own.key, anim: own.anim, x: px + dx * half, y: py + dy * half, quarter: quarterOfCorner(k) });
        });
      }
    }
  }

  /**
   * The texture of a water-edge piece at a water frame. "<key>#<corner>" (QA4 L-1) is that corner's
   * quarter of the piece, cut once per texture and kept with it.
   * @param {string} key @param {number} frame @returns {Texture}
   */
  edgeTexture(key, frame) {
    const [k, quarter] = key.split('#');
    const tex = this.assets.texture(`${k}.${frame}`);
    return quarter ? this.quarterTexture(tex, quarter) : tex;
  }

  /** A quarter (ne, se, sw, nw) of a tile's texture, cut once per texture and kept with it. @param {Texture} tex @param {string} quarter */
  quarterTexture(tex, quarter) {
    let cut = this.edgeQuarters.get(tex);
    if (!cut) this.edgeQuarters.set(tex, (cut = new Map()));
    let q = cut.get(quarter);
    if (!q) {
      const f = tex.frame;
      const [qx, qy] = edgeQuarterOffset(`#${quarter}`, f.width);
      q = new Texture({ source: tex.source, frame: new Rectangle(f.x + qx, f.y + qy, f.width / 2, f.height / 2) });
      cut.set(quarter, q);
    }
    return q;
  }

  /** The ground a flat tile is drawn as (v1.0 QA4 L-6: desert tree tiles as sand). @param {number} tx @param {number} ty */
  drawnGround(tx, ty) {
    const i = ty * this.map.width + tx;
    return this.sandUnderTrees.has(i) ? Ground.SAND : this.map.ground[i];
  }

  /** @param {number} cx @param {number} cy */
  chunkKey(cx, cy) {
    return `${cx},${cy}`;
  }

  /** Bundles a chunk's art needs (its regions', and the season's; with the v2 ground, see ringBundles). @param {number} cx @param {number} cy @returns {string[]} */
  chunkBundles(cx, cy) {
    const x0 = cx * CHUNK;
    const y0 = cy * CHUNK;
    const list = this.regions
      .filter((r) => r.bundle && r.tx < x0 + CHUNK && r.tx + r.tw > x0 && r.ty < y0 + CHUNK && r.ty + r.th > y0)
      .map((r) => /** @type {string} */ (r.bundle));
    if (this.groundV2) {
      // gfx W1: a region's own ground is apart (terrainArt.REGION_GROUND_PREFIX): its calm tiles and
      // edges ("ground:"), its pictures ("pictures:"); and on the dual grid a chunk's display tiles reach
      // one cell out of it: the next region's ground too where a cell of that ring has it (only its
      // calm tiles and edges: a picture always covers a cell of the chunk drawing it)
      const part = (/** @type {string | null} */ b) => (b && this.assets.builders.has(b) ? b : null);
      for (const r of [...list]) {
        for (const b of [part(groundBundleOf(r)), part(picturesBundleOf(r))]) if (b && !list.includes(b)) list.push(b);
      }
      for (const r of this.ringBundles(cx, cy)) {
        const b = part(groundBundleOf(r)) ?? r;
        if (!list.includes(b)) list.push(b);
      }
      // round 3: the ruin floor's edges over water, only where the ruin floor meets water
      if (this.assets.builders.has(GROUND_RUIN_BUNDLE) && this.chunkHasRuinShore(cx, cy)) list.push(GROUND_RUIN_BUNDLE);
    }
    // P10.2: and the season's look (gfx W1: the season's art of each seasonal ground the chunk has, apart).
    if (!this.seasonBundle) return list;
    list.push(this.seasonBundle);
    if (this.groundV2) {
      for (const cls of this.chunkClasses(cx, cy)) {
        const b = seasonGroundBundleOf(this.seasonBundle, cls);
        if (this.assets.builders.has(b)) list.push(b);
      }
    }
    return list;
  }

  /**
   * W1: the ground classes of a chunk's cells and of the ring of cells its display tiles reach. Fixed
   * for the map. @param {number} cx @param {number} cy @returns {string[]}
   */
  chunkClasses(cx, cy) {
    const key = `k${cx},${cy}`;
    let out = this.v2Tiles.get(key);
    if (out === undefined) {
      const map = this.map;
      const set = new Set();
      for (let y = Math.max(0, cy * CHUNK - 1); y <= Math.min(map.height - 1, (cy + 1) * CHUNK); y++) {
        for (let x = Math.max(0, cx * CHUNK - 1); x <= Math.min(map.width - 1, (cx + 1) * CHUNK); x++) {
          const c = this.groundClassAt(x, y);
          if (c) set.add(c);
        }
      }
      out = [...set].sort();
      this.v2Tiles.set(key, out);
    }
    return out;
  }

  /**
   * W1: the region bundles whose ground the ring of cells just outside a chunk needs (its display
   * tiles reach one cell out): those of the regions whose own ground (region grass, moss, snow, desert
   * sand) lies in the ring (chunkBundles loads their ground bundle). Fixed for the map. @param {number} cx @param {number} cy @returns {string[]}
   */
  ringBundles(cx, cy) {
    const key = `b${cx},${cy}`;
    let out = this.v2Tiles.get(key);
    if (out === undefined) {
      const map = this.map;
      const set = new Set();
      const x0 = cx * CHUNK - 1;
      const y0 = cy * CHUNK - 1;
      const x1 = (cx + 1) * CHUNK;
      const y1 = (cy + 1) * CHUNK;
      for (let y = y0; y <= y1; y++) {
        for (let x = x0; x <= x1; x++) {
          if (y !== y0 && y !== y1 && x !== x0 && x !== x1) continue;
          if (!inBounds(map, x, y)) continue;
          const cls = this.groundClassAt(x, y);
          if (!cls || !REGION_GROUNDS.has(cls)) continue;
          const b = regionAt(this.regions, x, y)?.bundle;
          if (b) set.add(b);
        }
      }
      out = [...set];
      this.v2Tiles.set(key, out);
    }
    return out;
  }

  /**
   * W1: whether a display tile of a chunk has ruin floor and water among its corners (the chunk's
   * cells and the ring of cells its display tiles reach). Fixed for the map.
   * @param {number} cx @param {number} cy
   */
  chunkHasRuinShore(cx, cy) {
    const key = `r${cx},${cy}`;
    let has = this.v2Tiles.get(key);
    if (has === undefined) {
      const map = this.map;
      const xa = Math.max(0, cx * CHUNK - 1);
      const ya = Math.max(0, cy * CHUNK - 1);
      const xb = Math.min(map.width - 1, (cx + 1) * CHUNK);
      const yb = Math.min(map.height - 1, (cy + 1) * CHUNK);
      const is = (/** @type {number} */ x, /** @type {number} */ y, /** @type {number} */ g) => x >= xa && x <= xb && y >= ya && y <= yb && this.drawnGround(x, y) === g;
      has = false;
      for (let y = ya; y <= yb && !has; y++) {
        for (let x = xa; x <= xb && !has; x++) {
          if (this.drawnGround(x, y) !== Ground.RUIN) continue;
          for (let dy = -1; dy <= 1 && !has; dy++) for (let dx = -1; dx <= 1 && !has; dx++) has = is(x + dx, y + dy, Ground.WATER);
        }
      }
      this.v2Tiles.set(key, has);
    }
    return has;
  }

  /**
   * Builds the terrain and objects of one chunk (CHUNK x CHUNK tiles). Flat ground goes into one
   * cached texture per chunk; raised rows are Y-sorted with the actors as before (DESIGN.md 3.3).
   * @param {number} cx @param {number} cy
   * @returns {Chunk}
   */
  buildChunk(cx, cy) {
    // W1 round 6: the calm tiles' numbers of this chunk, worked out once while it is built (groundV2.calmNumber)
    this.calmMemo = new Map();
    this.cellCalmMemo = new Map();
    try {
      return this.buildChunkInner(cx, cy);
    } finally {
      this.calmMemo = null;
      this.cellCalmMemo = null;
    }
  }

  /** buildChunk's work. @param {number} cx @param {number} cy */
  buildChunkInner(cx, cy) {
    const map = this.map;
    const ts = map.tileSize;
    const base = new Container();
    base.label = `chunk-${cx},${cy}`;
    /** @type {Sprite[]} */
    const water = [];
    /** v1.1: water-edge pieces (shore tiles, bank overlays), animated with the water. @type {{ sprite: Sprite, key: string }[]} */
    const edges = [];
    /** @type {Map<number, Container>} */
    const rows = new Map();
    /** @type {Map<number, { x0: number, x1: number, y0: number, y1: number }[]>} */
    const extents = new Map();
    const rowContainer = (/** @type {number} */ ty) => {
      let c = rows.get(ty);
      if (!c) {
        c = new Container();
        c.label = `terrain-row-${ty}-${cx}`;
        // North edge of the row (see header comment); chunks to the east draw after (same as the
        // tile order of one big map, so chunk borders look exactly the same).
        c.zIndex = ty * ts + 0.001 + cx * 1e-5;
        rows.set(ty, c);
        this.actors.addChild(c);
      }
      return c;
    };
    const x1 = Math.min(map.width, (cx + 1) * CHUNK);
    const y1 = Math.min(map.height, (cy + 1) * CHUNK);
    // gfx W1: the v2 ground draws the flat ground on the dual grid (the cell loop below then draws
    // only the raised rows and ramps, as before).
    if (this.groundV2) this.buildGroundV2(base, edges, cx, cy);
    for (let ty = cy * CHUNK; ty < y1; ty++) {
      for (let tx = cx * CHUNK; tx < x1; tx++) {
        const i = ty * map.width + tx;
        const h = map.elev[i];
        const isRamp = map.shape[i] === Shape.RAMP_N;
        const x = tx * ts;

        if (h === 0 && !isRamp) {
          if (this.groundV2) continue; // (drawn on the dual grid above)
          // v1.1: next to water, the release terrain's sand becomes a shore tile and grass gets a bank.
          const edge = this.releaseTerrain ? this.waterEdge(tx, ty) : null;
          const frame = Math.max(0, this.waterFrame);
          const s = edge?.base ? new Sprite(this.assets.texture(`${edge.base}.${frame}`)) : this.makeSprite(this.surfaceKey(tx, ty));
          s.position.set(x, ty * ts);
          base.addChild(s);
          if (edge?.base) edges.push({ sprite: s, key: edge.base });
          for (const key of edge?.overlays ?? []) {
            const o = new Sprite(this.edgeTexture(key, frame));
            const [qx, qy] = edgeQuarterOffset(key, ts);
            o.position.set(x + qx, ty * ts + qy);
            base.addChild(o);
            edges.push({ sprite: o, key });
          }
          if (map.ground[i] === Ground.WATER) {
            if (this.waterFrame >= 0) s.texture = this.assets.texture(`tile.water.${this.waterFrame}`);
            water.push(s);
          }
          continue;
        }

        const row = rowContainer(ty);
        const top = ty * ts - h;
        const surface = this.makeSprite(isRamp ? 'tile.ramp' : this.surfaceKey(tx, ty));
        surface.position.set(x, top);
        surface.tint = levelTint(isRamp ? h - LEVEL_PX / 2 : h, this.releaseTerrain);
        row.addChild(surface);

        // South face: from this tile's south edge down to the south neighbor's north edge.
        const faceTop = (ty + 1) * ts - southEdgeHeight(map, tx, ty);
        const faceBottom = (ty + 1) * ts - northEdgeHeight(map, tx, ty + 1);
        this.addFace(row, tx, ty, x, faceTop, faceBottom);
        if (faceBottom > faceTop) {
          // Contact shadow on the ground at the foot of the cliff.
          const shade = this.edge(x, faceBottom, ts, CLIFF_SHADOW_PX);
          shade.alpha = CLIFF_SHADOW_ALPHA;
          row.addChild(shade);
        }

        // Dark outlines where a neighbor is lower (reads as an edge from above).
        if (!isRamp) {
          const lowerEast = inBounds(map, tx + 1, ty) && map.elev[i + 1] < h;
          const lowerWest = inBounds(map, tx - 1, ty) && map.elev[i - 1] < h;
          const lowerNorth = inBounds(map, tx, ty - 1) && southEdgeHeight(map, tx, ty - 1) < h;
          if (lowerEast) {
            row.addChild(this.edge(x + ts - EDGE_PX, top, EDGE_PX, ts));
            // Light comes from the upper left: cast a shadow onto the lower ground to the east.
            const eastH = map.elev[i + 1];
            const shade = this.edge(x + ts, ty * ts - eastH, CLIFF_SHADOW_PX, ts);
            shade.alpha = CLIFF_SHADOW_ALPHA;
            row.addChild(shade);
          }
          if (lowerWest) row.addChild(this.edge(x, top, EDGE_PX, ts));
          if (lowerNorth) row.addChild(this.edge(x, top, ts, EDGE_PX));
        }

        const list = extents.get(ty) ?? [];
        list.push({ x0: x, x1: x + ts, y0: top, y1: Math.max(faceBottom, faceTop) });
        extents.set(ty, list);
      }
    }
    base.tint = levelTint(0, this.releaseTerrain);
    this.base.addChild(base);
    // A chunk's flat ground -> one textured quad per frame, cached over the whole chunk (see
    // chunkCacheArea: a partial area could get a screen-sized texture and seams), at the terrain art's
    // density (2 with the release terrain, else its fine pixels were halved: terrainArt.groundCacheResolution).
    const area = chunkCacheArea(cx, cy, ts);
    base.boundsArea = new Rectangle(area.x, area.y, area.width, area.height);
    base.cacheAsTexture({ scaleMode: 'nearest', antialias: false, resolution: groundCacheResolution(this.releaseTerrain) });

    // Objects standing in this chunk now.
    for (const o of map.objects) {
      if (o.tx < cx * CHUNK || o.tx >= x1 || o.ty < cy * CHUNK || o.ty >= y1 || this.objectSprites.has(o)) continue;
      this.addObjectSprite(o);
    }
    this.chunkStats.built++;
    return { cx, cy, base, rows, water, edges, extents, bundles: this.chunkBundles(cx, cy), waterFrame: this.waterFrame };
  }

  /** @param {Chunk} c */
  destroyChunk(c) {
    const map = this.map;
    c.base.cacheAsTexture(false);
    c.base.destroy({ children: true });
    for (const r of c.rows.values()) r.destroy({ children: true });
    const inChunk = (/** @type {number} */ tx, /** @type {number} */ ty) => Math.floor(tx / CHUNK) === c.cx && Math.floor(ty / CHUNK) === c.cy;
    for (const [o, e] of this.objectSprites) {
      const home = this.chunks.get(this.chunkKey(Math.floor(o.tx / CHUNK), Math.floor(o.ty / CHUNK)));
      if (inChunk(o.tx, o.ty) || !home || home === c) {
        e.sprite.destroy();
        this.objectSprites.delete(o);
      }
    }
    // Villagers use the plains art: drop their sprites before that bundle can be released.
    if (c.bundles.includes('region:plains')) this.npcs.clear();
    if (c.bundles.some((b) => b.startsWith('region:'))) this.dropBossSprites();
    for (const b of c.bundles) this.assets.unload(b);
    this.chunkStats.freed++;
    void map;
  }

  /**
   * Loads the chunks around the view and frees the far ones (P8). A chunk whose region art is not
   * loaded yet waits for its bundle (loaded in the background, released with the last chunk).
   * @param {{ x: number, y: number }} origin @param {number} viewW @param {number} viewH world px
   */
  updateChunks(origin, viewW, viewH) {
    this.viewRect = { x: origin.x, y: origin.y, w: viewW, h: viewH };
    const ts = this.map.tileSize;
    const size = CHUNK * ts;
    const ncx = Math.ceil(this.map.width / CHUNK);
    const ncy = Math.ceil(this.map.height / CHUNK);
    const range = (/** @type {number} */ margin) => chunkRange(origin, viewW, viewH, margin, { chunkPx: size, ncx, ncy, all: this.loadAll });
    const want = range(ts * CHUNK_LOAD_MARGIN_TILES); // a little beyond the screen
    const keep = range(ts * CHUNK_KEEP_MARGIN_TILES); // hysteresis: freed only once out of view
    // v1.0 (perf review of the terrain cache): the chunk caches (cacheAsTexture) are the only users of
    // PixiJS's TexturePool, which keeps every texture given back and never shrinks: 4 MB each with
    // the release terrain. Once chunks have been freed (the frame before), let the idle ones go.
    if (this.chunkCachesFreed) {
      TexturePool.clear(true);
      this.chunkCachesFreed = false;
    }
    this.chunkStats.updates++;
    let pending = 0;
    // the bundles of chunks still waiting for others (gfx W1: a chunk may wait on several bundles that
    // are not a region's, e.g. a region's pictures and the next region's ground: none is let go meanwhile)
    /** @type {Set<string>} */
    const waiting = new Set();
    for (let cy = want.y0; cy <= want.y1; cy++) {
      for (let cx = want.x0; cx <= want.x1; cx++) {
        const key = this.chunkKey(cx, cy);
        if (this.chunks.has(key)) continue;
        const bundles = this.chunkBundles(cx, cy);
        const missing = bundles.filter((b) => !this.assets.isLoaded(b));
        if (missing.length > 0) {
          for (const b of missing) this.requestBundle(b);
          for (const b of bundles) waiting.add(b);
          pending++;
          continue;
        }
        for (const b of bundles) this.assets.retain(b);
        this.chunks.set(key, this.buildChunk(cx, cy));
      }
    }
    this.chunkStats.pending = pending;
    for (const [key, c] of this.chunks) {
      if (c.cx < keep.x0 || c.cx > keep.x1 || c.cy < keep.y0 || c.cy > keep.y1) {
        this.destroyChunk(c);
        this.chunks.delete(key);
        this.chunkCachesFreed = true;
      }
    }
    // A bundle loaded for chunks that were left behind before being built: let it go.
    for (const b of this.preloaded) {
      const used = [...this.chunks.values()].some((c) => c.bundles.includes(b));
      if (used) {
        this.assets.unload(b); // the chunks hold their own references now
        this.preloaded.delete(b);
      } else if (!this.bundlesLoading.has(b)) {
        const stillWanted = waiting.has(b) || this.regions.some((r) => r.bundle === b && this.regionNear(r, origin, viewW, viewH));
        if (!stillWanted) {
          if (b === 'region:plains') this.npcs.clear();
          this.dropBossSprites();
          this.assets.unload(b);
          this.preloaded.delete(b);
        }
      }
    }
  }

  /** @param {RegionInfo} r @param {{ x: number, y: number }} o @param {number} w @param {number} h */
  regionNear(r, o, w, h) {
    const ts = this.map.tileSize;
    const m = CHUNK * ts;
    return r.tx * ts < o.x + w + m && (r.tx + r.tw) * ts > o.x - m && r.ty * ts < o.y + h + m && (r.ty + r.th) * ts > o.y - m;
  }

  /** @param {string} name */
  requestBundle(name) {
    if (this.bundlesLoading.has(name) || this.assets.isLoaded(name)) return;
    this.bundlesLoading.add(name);
    this.assets.load(name).then(
      () => {
        this.bundlesLoading.delete(name);
        this.preloaded.add(name);
      },
      () => this.bundlesLoading.delete(name),
    );
  }

  /** Bosses are drawn with region art: drop their sprites before a region bundle can go (redrawn next frame if still loaded). */
  /**
   * v1.0: the source's art is loaded while the player is in the desert region (its strip of rooms
   * holds the antechamber and the arena) and released elsewhere (about 4 MB with the release art).
   * @param {import('../game/state.js').GameState} state
   */
  updateSourceBundle(state) {
    const p = state.player;
    const want = SOURCE_REGIONS.includes(regionAt(this.regions, Math.floor(p.x / 16), Math.floor(p.y / 16))?.id ?? '');
    if (want && !this.sourceHeld && !this.sourceLoading) {
      this.sourceLoading = true;
      this.assets.load(SOURCE_BUNDLE).then(
        () => {
          this.sourceLoading = false;
          this.sourceHeld = true; // (released on the next frame if no longer wanted)
        },
        () => {
          this.sourceLoading = false;
        },
      );
    } else if (!want && this.sourceHeld) {
      this.enemySprites.drop(FINAL_BOSS_ENEMY_ID); // (its warning overlay too)
      this.sourceHeld = false;
      this.assets.unload(SOURCE_BUNDLE);
    }
  }

  dropBossSprites() {
    for (const id of this.enemySprites.ids()) if (id >= 1000) this.enemySprites.drop(id);
  }

  /** Releases an enemy's sprite and its warning overlay (EnemySlots calls this). @param {number} id @param {Sprite} spr */
  releaseEnemySprite(id, spr) {
    spr.destroy();
    this.enemyKeys.delete(id);
    this.flashSprites.get(id)?.destroy();
    this.flashSprites.delete(id);
  }

  /**
   * What the enemies look like on screen (tests, ?debug): frame, size in game px, warning overlay.
   * Only sprites drawn for an enemy still in the game: one left by an enemy that was cleared or
   * respawned (not yet redrawn) is not listed.
   * @param {{ enemies: any[] }} state
   */
  enemyDebug(state) {
    return this.enemySprites.live(state.enemies).map(({ id, owner, sprite: s }) => {
      const f = this.flashSprites.get(id);
      return { id, kind: owner.kind, key: this.enemyKeys.get(id) ?? '', w: s.texture.width, h: s.texture.height, tint: s.tint, flash: f && f.visible ? f.alpha : 0, flashColor: f ? f.tint : null };
    });
  }

  /** Chunk / bundle numbers for the debug overlay and tests. */
  streamStats() {
    return { chunks: this.chunks.size, built: this.chunkStats.built, freed: this.chunkStats.freed, pending: this.chunkStats.pending, updates: this.chunkStats.updates, objects: this.objectSprites.size, bundles: this.assets.stats().bundles };
  }

  /**
   * @param {Container} row @param {number} tx @param {number} ty
   * @param {number} x @param {number} faceTop @param {number} faceBottom
   */
  addFace(row, tx, ty, x, faceTop, faceBottom) {
    let remaining = faceBottom - faceTop;
    if (remaining <= 0) return;
    const g = this.map.ground[ty * this.map.width + tx];
    const kind = g === Ground.RUIN ? 'ruin' : g === Ground.WALL ? 'wall' : g === Ground.SAND ? 'sand' : g === Ground.PATH ? 'path' : 'other';
    // v1.1 (release terrain): plateau faces for sand and paths, and a band variant per tile.
    const mat = faceMaterial(kind, regionAt(this.regions, tx, ty)?.id, this.releaseTerrain);
    const variant = faceVariant(hash(tx, ty), mat, this.releaseTerrain);
    let y = faceTop;
    let first = true;
    while (remaining > 0) {
      const seg = remaining >= 8 ? 8 : 4;
      const last = remaining - seg <= 0;
      const key = `face.${mat}.${first ? 'top' : 'mid'}${last ? '-base' : ''}.${seg}`;
      const s = this.makeSprite(variant && this.assets.hasTexture(this.seasonal(key + variant)) ? key + variant : key);
      s.position.set(x, y);
      row.addChild(s);
      y += seg;
      remaining -= seg;
      first = false;
    }
  }

  /** @param {number} x @param {number} y @param {number} w @param {number} h */
  edge(x, y, w, h) {
    const s = this.makeSprite('px');
    s.position.set(x, y);
    s.width = w;
    s.height = h;
    s.tint = EDGE_COLOR;
    s.alpha = 0.55;
    return s;
  }

  /** Sprite key of a map object in its current state. @param {any} o @param {number} timeSec */
  objectKey(o, timeSec) {
    if (o.type === 'receiver') return o.on ? 'obj.receiver.on' : 'obj.receiver.off';
    if (o.type === 'brazier') return `obj.brazier.${Math.floor(timeSec * 6) % 2}`;
    if (o.type === 'sconce') return o.lit ? 'obj.sconce.on' : 'obj.sconce.off';
    if (o.type === 'stone') return o.glow ? 'obj.stone.on' : 'obj.stone.off';
    // P10.3: conifers in the forest and the mountains.
    if (o.type === 'tree') {
      const r = regionAt(this.regions, o.tx, o.ty)?.id;
      if (r === 'forest' || r === 'mountains') return `${r}.pine`;
    }
    if (o.type === 'charm_shelf') return this.charmHome ? 'obj.charm_shelf.on' : 'obj.charm_shelf'; // P10.1
    if (o.type === 'star_ring') return this.ringOpen ? 'obj.star_ring.on' : 'obj.star_ring.off'; // v1.0
    return `obj.${o.type}`;
  }

  /** @param {any} o */
  addObjectSprite(o) {
    const map = this.map;
    const ts = map.tileSize;
    const s = this.makeSprite(this.objectKey(o, 0));
    // W2: decorative objects outdoors are drawn a little off-centre, in clusters (placement.decorOffset);
    // only the drawing: collision and saves stay keyed to the tile. dy <= 0, so it still sorts by its tile.
    const [dx, dy] = this.placement && DECOR_TYPES.includes(o.type) && outdoorAt(this.outdoors, o.tx, o.ty) ? decorOffset(o.tx, o.ty) : [0, 0];
    const x = o.tx * ts + ts / 2 + dx;
    const feetY = o.ty * ts + ts + dy;
    const z = map.elev[o.ty * map.width + o.tx];
    s.position.set(x, feetY - z);
    // The door mat lies flat on the floor: under anyone standing on it.
    s.zIndex = o.type === 'mat' || o.type === 'stairs' ? feetY - ts : feetY;
    s.visible = !o.gone;
    this.actors.addChild(s);
    /** @type {Occluder | null} */
    let occluder = null;
    // Trees and houses (v1.0: the release house is 56 game px tall) fade when the player is behind them.
    if (o.type === 'tree' || o.type === 'house') {
      const w = s.width / 2;
      occluder = { sprite: s, x0: x - w, x1: x + w, y0: feetY - z - s.height, y1: feetY - z, key: feetY };
    }
    this.objectSprites.set(o, { o, sprite: s, occluder });
  }

  /** Objects changed by the environment (burnt, broken, opened, powered). @param {number} timeSec */
  updateObjects(timeSec, now = 0) {
    const ts = this.map.tileSize;
    for (const e of this.objectSprites.values()) {
      const { o, sprite } = e;
      sprite.visible = !o.gone;
      if (o.gone) continue;
      if (o.type === 'crate') {
        // Crates move (P7): slide from the old tile over 0.2 s.
        const k = o.movedAt === undefined ? 1 : Math.min(1, (now - o.movedAt) / 200);
        const tx = o.fromTx === undefined ? o.tx : o.fromTx + (o.tx - o.fromTx) * k;
        const ty = o.fromTy === undefined ? o.ty : o.fromTy + (o.ty - o.fromTy) * k;
        const feetY = ty * ts + ts;
        sprite.position.set(Math.round(tx * ts + ts / 2), Math.round(feetY - this.map.elev[o.ty * this.map.width + o.tx]));
        sprite.zIndex = feetY;
      }
      if (o.type === 'stump' && e.occluder) {
        e.occluder = null;
        sprite.alpha = 1;
      }
      sprite.texture = this.assets.texture(this.seasonal(this.objectKey(o, timeSec)));
    }
  }

  /**
   * @param {import('../game/state.js').GameState} state
   * @param {number} alpha interpolation factor from the fixed-step loop
   * @param {number} timeSec real time, for purely visual animation
   * @param {number} dtSec real time since the previous rendered frame (camera smoothing)
   */
  render(state, alpha, timeSec, dtSec) {
    const p = state.player;
    const x = lerp(p.prevX, p.x, alpha);
    const y = lerp(p.prevY, p.y, alpha);
    const z = lerp(p.prevZ, p.z, alpha);
    const sx = Math.round(x);
    const sy = Math.round(y - z);

    // Climbing reuses the walk frames facing the wall (back view on a north wall).
    const frame = p.moving
      ? WALK_CYCLE[Math.floor(p.walkTime * WALK_FPS) % WALK_CYCLE.length]
      : !p.grounded && !p.climbing
        ? 1
        : 0;
    // Release art (hero.<action>.<dir>.<frame>): the full animation set when it is loaded.
    const pose = this.heroAnim.update(p, state, timeSec, dtSec * 1000);
    this.heroPose = pose;
    const releaseKey = this.heroAnim.textureKey(pose, p.facing, p.moving, (k) => this.assets.hasTexture(k));
    this.heroKey = releaseKey;
    // Otherwise the placeholder hero. Swimming: head and shoulders above the water, ripples alternate.
    const tex = releaseKey
      ? this.assets.texture(releaseKey)
      : p.swimming
        ? this.assets.texture(`player.swim.${p.facing}.${Math.floor(p.walkTime * (p.moving ? 6 : 2)) % 2}`)
        : this.assets.texture(`player.walk.${p.facing}.${frame}`);
    this.player.texture = tex;
    // P11.5: the glider, the hidden-player check, the stamina wheel, the shield and the bow sit
    // relative to the hero's body, so they follow the drawn hero's height (not its hit box).
    this.heroK = Math.max(1, tex.height / HERO_BASE_H);
    this.player.position.set(sx, sy);
    this.player.zIndex = y;
    // v1.0 (C9): the pendant glows as he gets up in the opening.
    const op = openingView(state);
    this.pendantGlow.visible = !!op && op.glow > 0.01;
    if (op && this.pendantGlow.visible) {
      this.pendantGlow.position.set(sx, sy - Math.round(PENDANT_Y * this.heroK));
      this.pendantGlow.alpha = op.glow;
      this.pendantGlow.zIndex = y + 0.002;
    }
    // Glider canopy above the player's head; its cords end at the shoulders.
    this.glider.visible = p.gliding;
    if (p.gliding) {
      this.glider.position.set(sx, sy - Math.round(GLIDER_SHOULDER_Y * this.heroK));
      this.glider.zIndex = y + 0.001;
    }

    // Shadow on the ground below; smaller and fainter the higher the player is.
    const above = Math.max(0, z - p.groundZ);
    const k = Math.max(0.45, 1 - above / 96);
    this.shadow.visible = !p.swimming; // no ground shadow on the water surface
    this.shadow.position.set(sx, Math.round(y - p.groundZ) - 1);
    this.shadow.scale.set(k);
    this.shadow.alpha = 0.35 * k;
    this.shadow.zIndex = y - 0.002;

    this.updateOcclusion(sx, sy, y, tex);
    this.drawStamina(p, sx, sy, timeSec);
    this.renderCombat(state, alpha, sx, sy, y, timeSec);
    this.animateWater(timeSec);

    // Follow the ground under the player during short jumps (so jumping does not bob the screen),
    // but the player's real height during long airborne states (gliding, climbing) so they stay
    // near the center. Smoothing blends the switch.
    const camZ = p.gliding || p.climbing ? z : p.groundZ;
    this.camera.setViewport(this.app.screen.width, this.app.screen.height);
    // Entering / leaving an area (cave) switches the camera bounds and cuts to the player.
    const aimY = CAMERA_TARGET_OFFSET_Y * this.heroK;
    if (this.applyBounds(state)) this.camera.snapTo(x, y - camZ - aimY);
    else this.camera.follow(x, y - camZ - aimY, dtSec);
    this.applyCamera();
    this.updateSeason(state.env.now);
    this.updateSourceBundle(state);
    this.updateChunks(this.camera.origin(), this.app.screen.width / this.camera.zoom, this.app.screen.height / this.camera.zoom);
    // P10.1: the elder's charm is back on its shelf once the quest is done.
    const charmHome = state.progress.quests.lost_charm === 'done';
    if (charmHome !== this.charmHome) {
      this.charmHome = charmHome;
      this.envVersion = -1;
    }
    // v1.0 (C5): the beach ring glows while it is the gate to the source.
    // v1.0 (C9): it flashes once in the opening.
    // (open — and glowing — until the ending is seen: the way back to the princess by the source)
    const ringOpen = starRingOpen(state);
    if (ringOpen !== this.ringOpen) {
      this.ringOpen = ringOpen;
      this.envVersion = -1;
    }
    if (state.env.version !== this.envVersion || this.hasBraziers) {
      this.envVersion = state.env.version;
      // Resonance stones glow while their switch is active.
      for (const sw of state.switches) {
        if (sw.kind !== 'stone') continue;
        const o = state.env.objectAt.get(sw.ty * this.map.width + sw.tx);
        if (o) o.glow = !!state.switchActive[sw.id];
      }
      this.updateObjects(timeSec, state.env.now);
    }
    const o = this.camera.origin();
    this.env.update(state, o, this.app.screen.width / this.camera.zoom, this.app.screen.height / this.camera.zoom, timeSec);
    this.weather.update(state, o, this.camera.zoom, this.boundsArea ? areaAt(state, state.player.x, state.player.y) : null, timeSec, dtSec);
    this.items.update(state, timeSec);
    this.npcs.update(state, alpha, { x, y }, timeSec);
    this.puzzles.update(state, timeSec);
    this.features.update(
      state,
      (key) => this.assets.texture(key),
      this.camera.origin(),
      this.camera.zoom,
      this.app.screen.width,
      this.app.screen.height,
      timeSec,
      this.boundsArea ? this.camera.bounds : null,
    );
  }

  /**
   * Sets the camera bounds for where the player is. Returns true when they changed.
   * @param {import('../game/state.js').GameState} state
   */
  applyBounds(state) {
    const area = areaAt(state, state.player.x, state.player.y);
    const ts = this.map.tileSize;
    // P10.3: outdoors, the column of regions the player is in (each has its own bounds).
    const outdoor = area ? null : (outdoorAt(state.outdoors, Math.floor(state.player.x / ts), Math.floor(state.player.y / ts)) ?? state.outdoor);
    const key = area ? area.id : `:${outdoor?.id ?? ''}`;
    if (key === this.boundsKey) return false;
    this.boundsKey = key;
    this.boundsArea = area ? area.id : '';
    const r = area ?? outdoor ?? { tx: 0, ty: 0, tw: this.map.width, th: this.map.height };
    this.camera.setBounds({ x: r.tx * ts, y: r.ty * ts, width: r.tw * ts, height: r.th * ts });
    return true;
  }

  /** Positions the world under the camera. Origin is already snapped to whole screen pixels. */
  applyCamera() {
    const o = this.camera.origin();
    const zoom = this.camera.zoom;
    this.world.scale.set(zoom);
    this.world.position.set(-o.x * zoom, -o.y * zoom);
  }

  /**
   * Cuts the camera straight to the player (after teleports, respawn or entering an area).
   * @param {import('../game/state.js').GameState} state
   */
  snapCamera(state) {
    const p = state.player;
    this.applyBounds(state);
    this.camera.snapTo(p.x, p.y - p.groundZ - CAMERA_TARGET_OFFSET_Y);
    this.applyCamera();
  }

  /**
   * Fades trees in front of the player; shows a silhouette when terrain hides the player.
   * @param {number} sx @param {number} sy @param {number} key @param {import('pixi.js').Texture} tex
   */
  updateOcclusion(sx, sy, key, tex) {
    const px0 = sx - 6;
    const px1 = sx + 6;
    const py0 = sy - Math.round(15 * this.heroK);
    const py1 = sy - 1;
    for (const { occluder: t } of this.objectSprites.values()) {
      if (!t) continue;
      const hides = t.key > key && px1 > t.x0 && px0 < t.x1 && py1 > t.y0 && py0 < t.y1;
      t.sprite.alpha = hides ? TREE_FADE_ALPHA : 1;
    }
    let occluded = false;
    const ts = this.map.tileSize;
    const firstRow = Math.floor(key / ts);
    for (let r = firstRow; r < firstRow + 6 && !occluded; r++) {
      if (r * ts + 0.001 <= key) continue; // rows drawn before the player can't hide it
      const tiles = [];
      for (const c of this.chunks.values()) tiles.push(...(c.extents.get(r) ?? []));
      for (const e of tiles) {
        if (px1 > e.x0 && px0 < e.x1 && py1 > e.y0 && py0 < e.y1) {
          occluded = true;
          break;
        }
      }
    }
    this.playerOccluded = occluded;
    this.silhouette.visible = occluded;
    if (occluded) {
      this.silhouette.texture = tex;
      this.silhouette.position.set(sx, sy);
    }
  }

  /**
   * @param {import('../game/entities/player.js').Player} p
   * @param {number} sx @param {number} sy player screen position (feet) @param {number} timeSec
   */
  drawStamina(p, sx, sy, timeSec) {
    const g = this.staminaWheel;
    const show = p.stamina < p.maxStamina || p.climbing;
    g.visible = show;
    if (!show) return;
    const cx = sx + 11;
    const cy = sy - Math.round(18 * this.heroK);
    const r = 5;
    const frac = Math.max(0, Math.min(1, p.stamina / p.maxStamina));
    // Exhausted: red and pulsing until the wheel is full again.
    const color = p.exhausted ? STAMINA_EXHAUSTED : frac < 0.3 ? STAMINA_LOW : STAMINA_OK;
    g.clear();
    g.circle(cx, cy, r + 1).fill({ color: 0x1a1c2c, alpha: 0.55 });
    if (frac > 0) {
      const start = -Math.PI / 2;
      g.moveTo(cx, cy).arc(cx, cy, r, start, start + frac * Math.PI * 2).lineTo(cx, cy).fill({ color });
    }
    g.alpha = p.exhausted ? 0.6 + 0.4 * Math.abs(Math.sin(timeSec * 6)) : 1;
  }

  /**
   * Enemies, projectiles, sword slash, shield, bow, hurt blink, slow-motion tint (P3).
   * @param {import('../game/state.js').GameState} state @param {number} alpha
   * @param {number} sx @param {number} sy player screen position @param {number} py player feet y
   * @param {number} timeSec
   */
  renderCombat(state, alpha, sx, sy, py, timeSec) {
    const p = /** @type {any} */ (state.player);

    // Enemies: create / update / remove sprites by id.
    const seen = new Set();
    if (this.enemyFrameCountsAt !== this.assets.version) {
      this.enemyFrameCounts.clear(); // art came or went: recount the release frames once
      this.enemyFrameCountsAt = this.assets.version;
    }
    for (const e of state.enemies) {
      // P10.4: a core of the murk is drawn by its region's art, only while that is loaded.
      if (e.boss && !this.assets.hasTexture(`enemy.${e.kind}.0`)) continue;
      // v1.0: the source is drawn by its own bundle, only while that is loaded.
      if (e.final && !this.assets.hasTexture('enemy.boss_source.idle.0')) continue;
      seen.add(e.id);
      // v1.0: the source has a frame for each action (front-facing: never flipped).
      const sourceKey = e.final ? sourceFrameKey(e, timeSec, (k) => this.assets.hasTexture(k)) : null;
      let spr = this.enemySprites.get(e); // (a sprite another enemy left under this id is dropped)
      if (!spr) {
        spr = this.makeSprite(sourceKey ?? `enemy.${e.kind}.0`);
        this.enemySprites.set(e, spr);
        this.actors.addChild(spr);
      }
      const ex = lerp(e.prevX, e.x, alpha);
      const ey = lerp(e.prevY, e.y, alpha);
      const moving = Math.hypot(e.x - e.prevX, e.y - e.prevY) > 0.01;
      // v1.0: the release art's frame for what it is doing (enemyAnim.js), else the placeholder.
      // (the source: its own frame for each state of the fight, sourceView.js)
      const key = sourceKey ?? enemyFrameKey(e, timeSec, moving, this.hasTexture, this.enemyFrameCounts);
      spr.texture = this.assets.texture(key);
      this.enemyKeys.set(e.id, key);
      spr.position.set(Math.round(ex), Math.round(ey - e.z));
      spr.zIndex = ey;
      spr.scale.x = !e.final && e.faceX < -0.2 ? -1 : 1; // (the source faces front: never flipped)
      // Stunned: pale blue (multiplied).
      spr.tint = e.state === 'stun' ? 0xa8b8ff : 0xffffff;
      spr.alpha = e.state === 'dead' ? (e.final ? Math.max(0, 1 - e.t / FINAL_BOSS.defeatMs) : defeatAlpha(e.t)) : 1;
      // Telegraph (v1.0, ART_STYLE_GUIDE 5.4 B): the wind-up pulses under a 50% red overlay, faster
      // as the attack nears — laid over the art, so it shows on dark bodies too (flashOverlay.js).
      const flash = warningFlashAlpha(e, timeSec, windupProgress(e));
      const overlay = placeFlash(spr, this.flashSprites.get(e.id) ?? null, flash, this.silhouettes, this.actors);
      if (overlay) this.flashSprites.set(e.id, overlay);
    }
    // P10.4: a core winding up its slam shows the shockwave's reach on the ground.
    if (!this.bossRing) {
      this.bossRing = new Graphics();
      this.actors.addChild(this.bossRing);
    }
    this.bossRing.clear();
    for (const e of state.enemies) {
      // (v1.0: the sentinel's small slam shows its reach the same way.)
      const slams = e.boss ? e.pattern === 'slam' : e.kind === 'sentinel';
      if (e.state !== 'windup' || !slams) continue;
      const k = windupProgress(e);
      const r = e.boss ? BOSS_KINDS[e.bossKind].slamRadius : ENEMY_KINDS.sentinel.slamRadius;
      this.bossRing.circle(Math.round(e.x), Math.round(e.y - e.z), r).stroke({ width: 2, color: 0xd0202a, alpha: 0.6 + 0.4 * k });
      this.bossRing.circle(Math.round(e.x), Math.round(e.y - e.z), r * k).fill({ color: 0xd0202a, alpha: 0.18 });
      this.bossRing.zIndex = e.y - r;
    }
    // v1.0: the source's slam / wave reach (on the ground) and its awake seats (above everything).
    if (!this.sourceGround) {
      this.sourceGround = new Graphics();
      this.sourceGround.zIndex = -1e6;
      this.actors.addChild(this.sourceGround);
      this.sourceMarks = new Graphics();
      this.overlay.addChild(this.sourceMarks);
    }
    this.sourceGround.clear();
    /** @type {Graphics} */ (this.sourceMarks).clear();
    drawSourceTelegraphs(this.sourceGround, state);
    drawSeatLights(/** @type {Graphics} */ (this.sourceMarks), state, timeSec);
    this.enemySprites.sweep(seen);

    // Projectiles: keep one sprite per projectile.
    while (this.projectileSprites.length < state.projectiles.length) {
      const spr = this.makeSprite('fx.arrow');
      this.actors.addChild(spr);
      this.projectileSprites.push(spr);
    }
    this.projectileSprites.forEach((spr, i) => {
      const pr = state.projectiles[i];
      spr.visible = !!pr;
      if (!pr) return;
      spr.texture = this.assets.texture(pr.kind === 'arrow' ? 'fx.arrow' : 'fx.orb');
      spr.position.set(Math.round(pr.x), Math.round(pr.y - pr.z - 6));
      spr.rotation = pr.kind === 'arrow' ? Math.atan2(pr.vy, pr.vx) : 0;
      spr.tint = pr.reflected ? 0xfff2a0 : 0xffffff;
      spr.zIndex = pr.y + 0.5;
    });

    // Sword slash while the blade is live.
    const hb = state.hitboxes.find((h) => h.owner === 'player');
    this.slash.visible = !!hb;
    if (hb) {
      this.slash.position.set(Math.round(hb.x), Math.round(hb.y - p.z - 4));
      this.slash.rotation = Math.atan2(p.aimY, p.aimX);
      this.slash.alpha = p.comboIndex === 2 ? 1 : 0.85;
      this.slash.zIndex = py + 0.01;
    }

    // Shield in front while guarding; bow and aim line while aiming.
    // The release hero holds his own shield and bow in his guard / bow frames: no second one on top.
    const held = this.heroKey ? this.heroKey.split('.')[1] : '';
    this.shield.visible = !!p.guarding && held !== 'guard';
    if (p.guarding) {
      this.shield.position.set(Math.round(sx + p.aimX * 7), Math.round(sy - 7 * this.heroK + p.aimY * 4));
      this.shield.zIndex = p.aimY < 0 ? py - 0.01 : py + 0.01;
    }
    const aiming = p.action === 'aim';
    this.bow.visible = aiming && held !== 'bow';
    this.aimLine.clear();
    if (aiming) {
      const drawn = p.actionMs >= COMBAT.bowDrawMs;
      this.bow.position.set(Math.round(sx + p.aimX * 7), Math.round(sy - 8 * this.heroK + p.aimY * 4));
      this.bow.rotation = Math.atan2(p.aimY, p.aimX);
      this.bow.zIndex = p.aimY < 0 ? py - 0.01 : py + 0.01;
      // Dotted aim line, brighter once the draw is full.
      for (let d = 12; d < 64; d += 6) {
        this.aimLine.rect(Math.round(sx + p.aimX * d), Math.round(sy - 8 * this.heroK + p.aimY * d), 1, 1);
      }
      this.aimLine.fill({ color: drawn ? 0xfff2a0 : 0xffffff, alpha: drawn ? 0.9 : 0.4 });
    }

    // Hurt: blink while invulnerable. Dodge: a little transparent. Dead: lying faded.
    const blink = p.invulnMs > 0 && Math.floor(timeSec * 12) % 2 === 0;
    this.player.alpha = p.dead ? 0.5 : blink ? 0.3 : p.action === 'dodge' ? 0.7 : 1;
    // (the release hero has his own collapse frames: no turning the sprite on its side)
    // (the placeholder hero lies on his side in the opening until he gets up, v1.0)
    const lying = p.dead || (openingView(state)?.riseFrame ?? 0) >= 2;
    this.player.rotation = lying && held !== 'down' ? Math.PI / 2 : 0;

    // Slow motion tint (screen space).
    const slow = state.flurryMs > 0 || state.bulletTime;
    this.slowTint.visible = slow;
    if (slow) {
      this.slowTint.clear();
      this.slowTint.rect(0, 0, this.app.screen.width, this.app.screen.height);
      this.slowTint.fill({ color: state.bulletTime ? 0x203860 : 0x401860, alpha: 0.18 });
    }
  }

  /** @param {number} timeSec */
  animateWater(timeSec) {
    // gfx W1: the v2 water has 4 frames of 0.28 s; v1 2 frames of 0.6 s.
    const frames = this.groundV2 ? WATER_FRAMES : 2;
    const frame = Math.floor(timeSec / (this.groundV2 ? WATER_FRAME_SEC_V2 : WATER_FRAME_SEC)) % frames;
    if (frame === this.waterFrame) {
      // a chunk that came into view since its water last changed catches up (W1)
      for (const c of this.chunks.values()) if (c.waterFrame !== frame && this.chunkVisible(c)) this.redrawWater(c, frame);
      return;
    }
    this.waterFrame = frame;
    for (const c of this.chunks.values()) {
      // (a chunk can have edge pieces of water in the next chunk, and no water of its own)
      if (c.water.length === 0 && c.edges.length === 0) continue;
      // W1: only the chunks on screen redraw their cache now; the others when they come into view
      if (this.groundV2 && !this.chunkVisible(c)) {
        this.waterStats.deferred++;
        continue;
      }
      this.redrawWater(c, frame);
    }
  }

  /** Puts a chunk's water (and its edge pieces) on a frame and redraws its cache. @param {Chunk} c @param {number} frame */
  redrawWater(c, frame) {
    c.waterFrame = frame;
    if (c.water.length === 0 && c.edges.length === 0) return;
    const t0 = performance.now();
    if (c.water.length) {
      const tex = this.assets.texture(`tile.water.${frame}`);
      for (const s of c.water) s.texture = tex;
    }
    for (const e of c.edges) e.sprite.texture = this.edgeTexture(e.key, frame);
    c.base.updateCacheTexture();
    this.waterStats.redraws++;
    this.waterStats.ms += performance.now() - t0;
  }

  /** Whether a chunk is on screen (the view rectangle of the last update, plus the raised-ground margin). @param {Chunk} c */
  chunkVisible(c) {
    const v = this.viewRect;
    if (!v) return true;
    const size = CHUNK * this.map.tileSize;
    return c.cx * size < v.x + v.w && (c.cx + 1) * size > v.x && c.cy * size < v.y + v.h + 64 && (c.cy + 1) * size > v.y;
  }
}

/**
 * Where a quarter piece ("<key>#<ne|se|sw|nw>", QA4 L-1) sits in its tile: its top-left corner.
 * @param {string} key @param {number} size the tile's size @returns {[number, number]}
 */
function edgeQuarterOffset(key, size) {
  const quarter = key.split('#')[1];
  if (!quarter) return [0, 0];
  return [quarter.endsWith('e') ? size / 2 : 0, quarter.startsWith('s') ? size / 2 : 0];
}

/** Stable per-tile variation. @param {number} x @param {number} y */
function hash(x, y) {
  let h = (x * 374761393 + y * 668265263) >>> 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177) >>> 0;
  return (h ^ (h >>> 16)) >>> 0;
}
