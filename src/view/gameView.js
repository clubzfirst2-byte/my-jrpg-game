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
import { WaterAtlas, waterQuads } from './waterLayer.js';
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
import { WeatherView, starRingOpen, crystalLightColor, LIGHT_MAP_RESOLUTION_V3 } from './weatherView.js';
import { ItemView } from './itemView.js';
import { PuzzleView } from './puzzleView.js';
import { NpcView } from './npcView.js';
import { regionAt, outdoorAt } from '../game/world/world.js';
import { seasonAt } from '../game/env/weather.js';
import { SEASON_ENTRIES, seasonKeys, SOURCE_BUNDLE, SOURCE_REGIONS } from './assets/placeholderPack.js';
import { HeroAnimator } from './heroAnim.js';
import { DECOR_TYPES, decorOffset, macroQuarter, patchVariant, placementEnabled } from './placement.js';
import { CORNERS, MACRO_NAMES, STEP_NAMES, PREFIX, PRIORITY, SEASONAL, WATER_FRAMES, WATER_FRAME_SEC as WATER_FRAME_SEC_V2, calmNumber, deepMapShaped, displayLayers, edgeVariantOf, groundClass, landKey, macroPlacement, quarterOfCorner, ruinCellTile, ruinTile, tileScheme } from './groundV2.js';
import { GROUND_RUIN_BUNDLE, GROUND_V2_KEY, ISLAND_EDGES_BUNDLE, ISLAND_STEPS_BUNDLE, detailBundleOf, groundBundleOf, seasonGroundBundleOf, faceMaterial, faceVariant, groundCacheResolution, groundVariant, indoorLight, levelBrightness, releaseSeasonKeys, usesReleaseTerrain, waterAround, waterEdgePieces } from './assets/terrainArt.js';
import { openingView } from '../game/story/story.js';
import { enemyFrameKey, warningFlashAlpha, defeatAlpha } from './enemyAnim.js';
import { SilhouetteCache, placeFlash } from './flashOverlay.js';
import { EnemySlots } from './enemySlots.js';
import { setFrame } from './spriteFrame.js';
import { frameFight } from './assets/artV3.js';
import { GroundCache } from './groundCache.js';
import { V3_OBJECTS_WINTER, V3_VILLAGE_TYPES, V3_WINTER_OBJECTS, v3VillageBundle } from './assets/villageV3.js';
import { V3_ENEMY_KINDS, kindsByRegion, v3EnemyBundle } from './assets/enemyV3.js';
import { HERO_V3_LAZY, HERO_V3_MOVE_BUNDLE, HERO_V3_MOVE_KEEP_MS, heroDrawKey } from './assets/heroV3.js';
import { MacroGrid, PROPS, PROP_SWAY, TREE_SWAY, baseKey as v3BaseKey, edgeKey as v3EdgeKey, floraFrames, floraKey, flowCorner, flowKey, flowLook, openProp, plainsTreeLook, seasonPrefix, swayFrame, swayStep, treeFootProp, v3PineBundle, v3PlainsBundles } from './v3Plains.js';
import { FOREST_PROPS, forestBaseKey, forestEdgeKey, forestFlowLook, forestFootProp, forestOpenProp, forestTreeLook, plainsPineBanned, rootsOffset, v3ForestBundles, winterMaskOf, winterPriority } from './v3Forest.js';
import { activeBoss } from '../game/entities/bosses.js';
import { hash01, valueNoise } from './placement.js';

/** Graphics v3: the v3 ground tiles that are opaque over the whole tile (the base patterns), and their sprites' label. */
const OPAQUE_V3 = /^(?:\w+\.)?(?:plains|forest)\.grass\.v3\.[a-h]\d\d$/;
const OPAQUE_LABEL = 'v3-opaque';

/** Graphics v3: the chunk ground's culling groups, in tiles (gameView.groupGround). */
export const V3_GROUP_TILES = 8;

/** Chunk size in tiles (P8). */
export const CHUNK = 32;

/** The quarter of a display tile's texture over its corner k (NW, NE, SW, SE). */
const TILE_QUARTER = /** @type {const} */ (['nw', 'ne', 'sw', 'se']);

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
 *   waterMesh: import('pixi.js').Mesh | null, waterKeys: string[],
 *   extents: Map<number, { x0: number, x1: number, y0: number, y1: number }[]>, bundles: string[],
 *   sway?: { sprite: Sprite, kind: string, frames: number, tx: number, ty: number, frame: number, set?: 'plains' | 'forest' }[], foot?: { sprite: Sprite, o: any }[],
 *   props?: Container }} Chunk
 *   (graphics v3: sway = the swaying props of its ground, foot = the props at the foot of its trees, with the actors)
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
   * @param {{ v3?: boolean, v3Opaque?: boolean, v3Cache?: boolean, v3HeroMove?: boolean }} [opts] v3: graphics v3 and its narrow view (?v3=1, assets/artV3.js)
   */
  constructor(app, assets, state, opts = {}) {
    this.app = app;
    this.assets = assets;
    /**
     * Graphics v3 (?v3=1): the v3 art where it is loaded (the plains' 4×4 grass picture, its trees, the
     * stone house, the grass tufts and flowers), no cached chunk ground (a cache at 4 texture px per game
     * px would be 16 MB a chunk: each chunk's ground is a render group of its tiles instead), and in a
     * boss fight the camera framing the hero, the boss and its telegraph (artV3.frameFight).
     */
    this.v3 = !!opts.v3;
    /**
     * Graphics v3: the opaque ground tiles drawn without blending (groupGround), only with ?v3opaque=1: it
     * made no difference to the frame rate in the measurements (software WebGL) and costs a batch per
     * ground group (draw calls 8 → 22); kept to try on the phones.
     */
    this.v3Opaque = this.v3 && opts.v3Opaque === true;
    /** Graphics v3: the tiles with a tree (v3TreeRoom), made on first use. @type {Set<number> | null} */
    this.v3Trees = null;
    /** Graphics v3: the tiles with any object (addV3Decor), made on first use. @type {Set<number> | null} */
    this.v3Taken = null;
    /** Graphics v3: the plains ground's base patterns (v3Plains.MacroGrid), made on first use. @type {MacroGrid | null} */
    this.v3Macro = null;
    /** Graphics v3: the flow corners of the chunk being built (v3GroundSetup). @type {((cx: number, cy: number) => 'd' | 'l' | 'm') | null} */
    this.v3CornerAt = null;
    /** Graphics v3 (forest): the forest's flow corners of the chunk being built (v3GroundSetup). @type {((cx: number, cy: number) => 'd' | 'l' | 'm') | null} */
    this.v3ForestCornerAt = null;
    /** Graphics v3: whether the map must not place the plains pine on a tile (v3Forest.plainsPineBanned, FOREST.md 4), made on first use. @type {((tx: number, ty: number) => boolean) | null} */
    this.v3PineBanned = null;
    /** Graphics v3: how each plains tree is drawn (v3Plains.plainsTreeLook), fixed per tree. @type {WeakMap<object, { what: 'tree' | 'prop', kind: string }>} */
    this.v3Looks = new WeakMap();
    /** Graphics v3: frames loaded per tree / prop kind, kept while the loaded art and the season stay the same. @type {{ version: string, n: Map<string, number> }} */
    this.v3Frames = { version: '', n: new Map() };
    /** Graphics v3: the tree objects by tile (addV3Decor), made on first use. @type {Map<number, any> | null} */
    this.v3TreeObjects = null;
    /** Graphics v3: the other objects' tiles (v3TreeRoom), made on first use. @type {Set<number> | null} */
    this.v3Others = null;
    /** Graphics v3: the v3 plains bundles of the season the world is about to change to, kept while they load (updateSeason). @type {string[] | null} */
    this.v3SeasonWant = null;
    /** Graphics v3 (enemyV3.js): the normal enemy kinds that spawn in each region, for its chunks' bundles. */
    this.v3EnemyKinds = this.v3 ? kindsByRegion(state.enemySpawns ?? [], (x, y) => regionAt(state.regions, x, y)?.id) : null;
    /** Graphics v3: the enemy bundles live enemies need this frame (a kind spawned outside its regions), kept loaded. @type {Set<string>} */
    this.v3EnemyLive = new Set();
    /** Graphics v3: the winter look of the common objects, held while it is winter (updateSeason). @type {string | null} */
    this.v3SeasonObjects = null;
    /** Graphics v3: the camera's view of the last frame, game px (state.viewRect). @type {{ x: number, y: number, width: number, height: number } | null} */
    this.cameraRect = null;
    /** Graphics v3: the share of the view the UI covers at the top / bottom in a boss fight (main.js measures it). */
    this.fightInsets = { top: 0, bottom: 0 };
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
    /**
     * Graphics v3: the flat ground drawn into a texture a little larger than the view (groundCache.js),
     * shown in place of the ground sprites (null with ?v3cache=0); the swaying props stay sprites, in a
     * layer of their own just above it.
     * @type {GroundCache | null}
     */
    this.groundCache = this.v3 && opts.v3Cache !== false ? new GroundCache(app.renderer, this.base) : null;
    /** Graphics v3: the chunks' open-ground props (swaying grass and flowers), above the ground. */
    this.v3DecorLayer = new Container();
    this.v3DecorLayer.label = 'v3-decor';
    if (this.v3) this.world.addChildAt(this.v3DecorLayer, this.world.getChildIndex(this.base) + 1);
    if (this.groundCache) this.world.addChildAt(this.groundCache.sprite, this.world.getChildIndex(this.base) + 1);

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
    /** @type {Map<any, { o: any, sprite: Sprite, occluder: Occluder | null, v3?: boolean, frame?: number }>} object -> its sprite (loaded chunks only; graphics v3: a plains tree's sway frame) */
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
    // gfx W1: the v2 water, a layer of its own under the cached ground (waterLayer.js): one mesh per
    // chunk over a shared water atlas, so a water frame redraws no chunk cache.
    this.waterLayer = new Container();
    this.waterLayer.label = 'water';
    this.world.addChildAt(this.waterLayer, 0);
    /** @type {WaterAtlas | null} */
    this.waterAtlas = null;
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
      (key) => this.assets.texture(this.seasonal(key)), // (graphics v3: the plates' winter look)
      this.envGround,
      this.actors,
      this.overlay,
      state,
    );
    // Time of day and weather (P5): light map, rain, lightning, above the world.
    this.weather = new WeatherView(app, (key) => this.makeSprite(key), this.actors, this.v3 ? { lightResolution: LIGHT_MAP_RESOLUTION_V3 } : {});
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
    this.silhouettes = new SilhouetteCache(this.v3 ? app.renderer : null);
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
    /** The texture actually shown for heroKey (graphics v3: its approved stand-in "v1.<key>" while the move bundle loads). @type {string | null} */
    this.heroDrawn = null;
    /**
     * Graphics v3 (heroV3.js): the hero's climb / swim / glide frames, loaded when one of them starts and let
     * go HERO_V3_MOVE_KEEP_MS after the last use. state: 'out' | 'loading' | 'in'.
     */
    this.heroMove = opts.v3HeroMove ? { state: /** @type {'out' | 'loading' | 'in'} */ ('out'), lastUseMs: -Infinity, keepMs: HERO_V3_MOVE_KEEP_MS, loads: 0, unloads: 0, loadMs: /** @type {number | null} */ (null), fallbackFrames: 0 } : null;
  }

  /**
   * Graphics v3 (heroV3.js): loads the hero's climb / swim / glide bundle when one of those actions is
   * shown, and lets it go a while after the last use (before the frame is set, so no sprite keeps one of
   * its textures). @param {string} action the pose's action @param {number} nowMs real time
   */
  updateHeroMove(action, nowMs) {
    const m = this.heroMove;
    if (!m) return;
    const using = HERO_V3_LAZY.includes(action);
    if (using) m.lastUseMs = nowMs;
    if (using && m.state === 'out') {
      m.state = 'loading';
      const t0 = performance.now();
      this.assets.load(HERO_V3_MOVE_BUNDLE).then(
        () => {
          m.state = 'in';
          m.loads++;
          m.loadMs = Math.round(performance.now() - t0);
        },
        () => {
          m.state = 'out';
        },
      );
    } else if (!using && m.state === 'in' && nowMs - m.lastUseMs > m.keepMs) {
      // (the hero shows another action from this frame on; the hidden silhouette lets go of its texture too)
      this.silhouette.texture = Texture.EMPTY;
      this.assets.unload(HERO_V3_MOVE_BUNDLE);
      m.state = 'out';
      m.unloads++;
    }
  }

  /** Graphics v3: the hero's move bundle (tests, ?debug). */
  heroMoveStats() {
    const m = this.heroMove;
    return m ? { move: m.state, moveLoads: m.loads, moveUnloads: m.unloads, moveLoadMs: m.loadMs, fallbackFrames: m.fallbackFrames } : {};
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
    // graphics v3: near the plains, the season's v3 plains art first too (the old look stays meanwhile)
    if (this.v3) {
      const held = (/** @type {string} */ pre) => [...this.chunks.values()].some((c) => c.bundles.some((b) => b.startsWith(pre)));
      const near = held('v3:plains:');
      const nearVillage = held('v3:village:');
      // (graphics v3 forest: its bundles too, and the plains pine's where a chunk draws one)
      const wanted = [...(near ? v3PlainsBundles(want) : []), ...(held('v3:plains:pine.') ? [v3PineBundle(want)] : []), ...(held('v3:forest:') ? v3ForestBundles(want) : []), ...(nearVillage ? [v3VillageBundle(want)] : []), ...(want === 'winter' ? [V3_OBJECTS_WINTER] : [])];
      const missing = wanted.filter((b) => this.assets.builders.has(b) && !this.assets.isLoaded(b));
      if (missing.length) {
        this.v3SeasonWant = wanted; // (all of them: one loaded early must not be let go meanwhile)
        for (const b of missing) this.requestBundle(b);
        return;
      }
    }
    this.v3SeasonWant = null; // (the chunks rebuilt below take it over; updateChunks lets the preload go)
    // graphics v3 (VILLAGE.md 1): the winter look of the things found everywhere (chests, barrels, crates,
    // jars, fires, checkpoints, plates), a bundle the view holds through the winter; not the open chest
    if (this.v3) {
      const objs = want === 'winter' && this.assets.builders.has(V3_OBJECTS_WINTER) ? V3_OBJECTS_WINTER : null;
      if (objs !== this.v3SeasonObjects) {
        if (objs && this.assets.isLoaded(objs)) this.assets.retain(objs);
        if (this.v3SeasonObjects) this.assets.unload(this.v3SeasonObjects);
        this.v3SeasonObjects = objs && this.assets.isLoaded(objs) ? objs : null;
      }
    }
    for (const c of this.chunks.values()) this.destroyChunk(c);
    this.chunks.clear();
    if (this.seasonBundle) this.assets.unload(this.seasonBundle);
    this.seasonBundle = bundle;
    this.seasonLoading = null;
    this.seasonLoaded = null;
    this.season = want;
    this.seasonKeySet = seasonKeys(want);
    // graphics v3: the common objects' winter look (the keys its bundle has)
    if (this.v3SeasonObjects) for (const k of V3_WINTER_OBJECTS) if (this.assets.hasTexture(`winter.${k}`)) this.seasonKeySet.add(k);
    // v1.1: the release terrain's own season keys (autumn forest and mountains, the lips of the cliff
    // variants), where the season's bundle has them.
    if (this.releaseTerrain) for (const k of releaseSeasonKeys(want)) if (this.assets.hasTexture(`${want}.${k}`)) this.seasonKeySet.add(k);
    // gfx W1: the v2 ground's season keys (32 calm tiles, the 8 pictures' pieces, the step pieces, edges of the 4 seasonal grounds);
    // the mountains' snow has no v2 seasons, so its ground and its edges stay as they are.
    if (this.groundV2 && want) {
      for (const k of [...this.seasonKeySet]) if (k.startsWith('mountains.snow.')) this.seasonKeySet.delete(k);
      for (const cls of SEASONAL) {
        const p = /** @type {any} */ (PREFIX)[cls];
        const names = [
          ...Array.from({ length: 32 }, (_, n) => String(n)),
          ...MACRO_NAMES.flatMap((m) => [0, 1, 2, 3].map((q) => `${m}.${q}`)),
          // round 7: 4 edge variants (masks 6 / 9: 2), the step pieces
          ...Array.from({ length: 14 }, (_, m) => (m + 1 === 6 || m + 1 === 9 ? [0, 1] : [0, 1, 2, 3]).map((v) => `edge.${m + 1}.${v}`)).flat(),
          ...STEP_NAMES,
        ];
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
      // (graphics v3: raised plains ground takes the v3 base, on the cell grid)
      if (cls === 'plains' && this.v3PlainsGround()) return v3BaseKey((this.v3Macro ??= new MacroGrid()), this.season, tx, ty);
      if (cls === 'moss' && this.v3ForestGround()) return forestBaseKey((this.v3Macro ??= new MacroGrid()), this.season, tx, ty);
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
    // (inspection R2: the deep areas' border wanders and their corners are round: groundV2.deepMapShaped)
    if (!this.deepWater) this.deepWater = deepMapShaped(map.width, map.height, (cx, cy) => map.ground[cy * map.width + cx] === Ground.WATER, hash);
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
    if ((cls === 'plains' && this.v3PlainsGround()) || (cls === 'moss' && this.v3ForestGround())) return { key: this.surfaceKey(x, y), anim: false }; // (graphics v3)
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
   * The land is drawn into the chunk's cache (base); the water pieces are returned for its water mesh.
   * @param {Container} base @param {number} cx @param {number} cy
   */
  buildGroundV2(base, cx, cy) {
    /** @type {{ key: string, x: number, y: number, quarter: string | null }[]} */
    const water = [];
    for (const p of /** @type {{ key: string, anim: boolean, x: number, y: number, quarter: string | null, tint?: number, flip?: boolean }[]} */ (this.groundPiecesV2(cx, cy))) {
      // (the water goes to the chunk's water mesh, under the cache: buildChunk)
      if (p.anim) {
        water.push(p);
        continue;
      }
      let tex = this.v2Texture(p.key);
      if (tex && p.quarter) tex = this.quarterTexture(tex, p.quarter);
      if (!tex) continue;
      const s = new Sprite(tex);
      s.position.set(p.x, p.y);
      // (graphics v3: a flow shape coloured by the game and mirrored left to right about the tile's centre, v3Plains.flowLook)
      if (p.tint !== undefined) s.tint = p.tint;
      if (p.flip) {
        s.scale.x = -1;
        s.x += tex.width;
      }
      if (this.v3 && OPAQUE_V3.test(p.key)) s.label = OPAQUE_LABEL; // (graphics v3: drawn without blending, groupGround)
      base.addChild(s);
    }
    return water;
  }


  /**
   * Graphics v3: whether the plains' v3 ground of the current season is loaded (summer's for spring; the
   * bundle "v3:plains:<season>", loaded by the chunks that have plains, chunkBundles).
   */
  v3PlainsGround() {
    return this.v3 && this.assets.hasTexture(`${seasonPrefix(this.season)}plains.grass.v3.a00`);
  }

  /**
   * Graphics v3 (forest, FOREST.md 1): whether the forest's v3 ground of the current season is loaded
   * ("v3:forest:<season>", loaded by the chunks that have forest, chunkBundles).
   */
  v3ForestGround() {
    return this.v3 && this.assets.hasTexture(`${seasonPrefix(this.season)}forest.grass.v3.a00`);
  }

  /**
   * Graphics v3 (STYLE.md 6, v3Plains.js; the forest: FOREST.md 1, v3Forest.js): the v3 ground of display
   * tile (i, j) in place of the v2 layers, for the plains and the forest where their art is loaded: the
   * base pattern's tile where the lowest ground is plains / forest (a full tile's own, or the one the edges
   * of the higher grounds lie on), then the flow where all 4 corners are that ground, then the other layers,
   * the plains / forest edges over a lower ground taking their v3 picture (same mask and v: the v2 rule;
   * winter: v3Forest.winterPriority). Pieces whose v3 art is not loaded stay v2.
   * @param {{ key: string, anim: boolean, x: number, y: number, quarter: string | null, tint?: number, flip?: boolean }[]} out
   * @param {{ key: string, anim: boolean }[]} layers v2's (displayLayers) @param {string[]} cls the 4 corners
   * @param {number} i @param {number} j @param {number} px @param {number} py
   */
  v3PlainsLayers(out, layers, cls, i, j, px, py) {
    const has = (/** @type {string} */ k) => this.assets.hasTexture(k);
    const plainsOn = this.v3PlainsGround();
    const forestOn = this.v3ForestGround();
    const calm = /^(plains|forest)\.grass\.(?:\d+|macro\d?\.\d)$/;
    void cls;
    for (let n = 0; n < layers.length; n++) {
      const l = layers[n];
      const c = l.anim ? null : calm.exec(l.key);
      const g = c ? c[1] : null;
      if (c && (n === 0 || l.key === `${g}.grass.0`) && ((g === 'plains' && plainsOn) || (g === 'forest' && forestOn))) {
        const macro = /** @type {MacroGrid} */ (this.v3Macro);
        out.push({ key: g === 'plains' ? v3BaseKey(macro, this.season, i, j) : forestBaseKey(macro, this.season, i, j), anim: false, x: px, y: py, quarter: null });
        if (n === 0 && this.v3Full(g === 'plains' ? 'plains' : 'moss', i, j)) {
          const fk = flowKey(i, j, /** @type {any} */ (g === 'plains' ? this.v3CornerAt : this.v3ForestCornerAt));
          const look = fk && (g === 'plains' ? flowLook(this.season, fk, has) : forestFlowLook(this.season, fk, has));
          if (look) out.push({ key: look.key, anim: false, x: px, y: py, quarter: null, tint: look.tint, ...(look.flip ? { flip: true } : {}) });
        }
        continue;
      }
      const e = /^(plains|forest)\.grass\.(edge\.\d+\.\d+)$/.exec(l.key);
      const v3 = e && e[1] === 'plains' && plainsOn ? v3EdgeKey(this.season, e[2]) : e && e[1] === 'forest' && forestOn ? forestEdgeKey(this.season, e[2]) : null;
      out.push({ key: v3 && has(v3) ? v3 : l.key, anim: l.anim, x: px, y: py, quarter: null });
    }
  }

  /**
   * Graphics v3: the base patterns (made once, pure) and, for one chunk build, the flow corners of the
   * plains and of the forest: a world corner has the flow of v3Plains.flowCorner only when the 4 display
   * tiles around it are full tiles of that ground, else none ('m'), so the flow fades out before the edges
   * (STYLE.md 6, FOREST.md 1).
   */
  v3GroundSetup() {
    this.v3Macro ??= new MacroGrid();
    const corners = (/** @type {string} */ cls) => {
      /** @type {Map<number, 'd' | 'l' | 'm'>} */
      const memo = new Map();
      /** @param {number} cx @param {number} cy @returns {'d' | 'l' | 'm'} */
      return (cx, cy) => {
        const k = (cx + 8) * 65536 + (cy + 8);
        let v = memo.get(k);
        if (v === undefined) {
          v = this.v3Full(cls, cx - 1, cy - 1) && this.v3Full(cls, cx, cy - 1) && this.v3Full(cls, cx - 1, cy) && this.v3Full(cls, cx, cy) ? flowCorner(cx, cy) : 'm';
          memo.set(k, v);
        }
        return v;
      };
    };
    this.v3CornerAt = corners('plains');
    this.v3ForestCornerAt = corners('moss');
  }

  /** Graphics v3: whether display tile (i, j) is a full plains tile (its 4 corner cells in the map, flat, plains). @param {number} i @param {number} j */
  v3FullPlains(i, j) {
    return this.v3Full('plains', i, j);
  }

  /** Graphics v3: whether display tile (i, j) is a full tile of ground class cls (its 4 corner cells in the map, flat, that ground). @param {string} cls @param {number} i @param {number} j */
  v3Full(cls, i, j) {
    const map = this.map;
    for (const [dx, dy] of CORNERS) {
      const x = i + dx;
      const y = j + dy;
      if (!inBounds(map, x, y) || map.elev[y * map.width + x] !== 0 || map.shape[y * map.width + x] === Shape.RAMP_N || this.groundClassAt(x, y) !== cls) return false;
    }
    return true;
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
      // graphics v3 (no cache to clip the overhang): the land of the display tiles over the chunk's west /
      // north edge (x or y before the chunk's first display tile) is the previous chunk's last, drawn by
      // that chunk only — unclipped, in full (at the map's edge, by this one). The water mesh is still
      // clipped to the chunk (waterQuads), so its pieces stay.
      if (this.v3 && (cx > 0 || cy > 0)) {
        const x0 = cx * CHUNK * ts + half;
        const y0 = cy * CHUNK * ts + half;
        // (a chunk whose west neighbour lies wholly outside the outdoors it is in, never built with it
        // (updateChunks), draws its west display tiles itself)
        const west = cx > 0 && !this.v3OwnWestEdge(cx, cy);
        let n = 0;
        for (const p of out) if (p.anim || !((west && p.x < x0) || (cy > 0 && p.y < y0))) out[n++] = p;
        out.length = n;
      }
    } finally {
      if (own) {
        this.calmMemo = null;
        this.cellCalmMemo = null;
      }
    }
    return out;
  }

  /**
   * Graphics v3: whether chunk (cx, cy) draws the display tiles over its west edge itself: when it overlaps
   * an outdoor area and its west neighbour overlaps none of the outdoors it overlaps (the camera, held in
   * that outdoor, never builds the neighbour: updateChunks). Fixed for the map. @param {number} cx @param {number} cy
   */
  v3OwnWestEdge(cx, cy) {
    const key = `w${cx},${cy}`;
    let own = this.v2Tiles.get(key);
    if (own === undefined) {
      const over = (/** @type {any} */ o, /** @type {number} */ c) => o.tx < (c + 1) * CHUNK && o.tx + o.tw > c * CHUNK && o.ty < (cy + 1) * CHUNK && o.ty + o.th > cy * CHUNK;
      const mine = (this.outdoors ?? []).filter((o) => over(o, cx));
      own = mine.length > 0 && !mine.some((o) => over(o, cx - 1));
      this.v2Tiles.set(key, own);
    }
    return own;
  }

  /**
   * groundPiecesV2's loop. @param {{ key: string, anim: boolean, x: number, y: number, quarter: string | null }[]} out
   * @param {number} cx @param {number} cy @param {number} j1 @param {number} i1
   * @param {(x: number) => number} clampX @param {(y: number) => number} clampY @param {(x: number, y: number) => boolean} flat
   * @param {number} half @param {number} ts
   */
  groundPiecesInto(out, cx, cy, j1, i1, clampX, clampY, flat, half, ts) {
    const map = this.map;
    const v3 = this.v3PlainsGround() || this.v3ForestGround();
    if (v3) this.v3GroundSetup();
    const classAt = (/** @type {number} */ x, /** @type {number} */ y) => this.groundClassAt(clampX(x), clampY(y));
    // graphics v3 (NAMES.md 2.1): in winter, with the forest's v3 art, the forest / plains pair exchanged
    // on a tile with both, and every mask an edge's v reads read in its own tile's order
    const winter = v3 && this.season === 'winter' && this.v3ForestGround();
    for (let j = cy * CHUNK - 1; j <= j1; j++) {
      for (let i = cx * CHUNK - 1; i <= i1; i++) {
        const px = i * ts + half;
        const py = j * ts + half;
        const cells = CORNERS.map(([dx, dy]) => [clampX(i + dx), clampY(j + dy)]);
        const cls = cells.map(([x, y]) => this.groundClassAt(x, y));
        const allFlat = cells.every(([x, y]) => flat(x, y));
        /** @param {string[]} c the 4 corners' classes @param {boolean} pictures */
        const layersOf = (c, pictures) =>
          displayLayers({
            cls: c,
            deep: cells.map(([x, y]) => this.deepAt(x, y)),
            waterVariant: hash(i, j) % 2,
            // round 7: the edge variant by the states of the sides the border crosses
            edgeVariant: (t, m) => (winter ? edgeVariantOf(t, m, i, j, hash, classAt, winterMaskOf) : edgeVariantOf(t, m, i, j, hash, classAt)),
            ...(winter ? { priority: winterPriority(c) } : {}),
            pick: (t) => String(this.wangAt(i, j, t)),
            // a picture piece where a picture is placed
            macro: () => {
              const m = pictures ? this.macroAt(i, j) : null;
              return m && this.v2Has(landKey(c[0], m.name)) ? m.name : null;
            },
          });
        if (allFlat && cls.every((c) => c !== null)) {
          const layers = layersOf(/** @type {string[]} */ (cls), true);
          // graphics v3: the plains' v3 ground (base, flow, grass edges) where it is loaded
          if (v3) this.v3PlainsLayers(out, layers, /** @type {string[]} */ (cls), i, j, px, py);
          else for (const l of layers) out.push({ key: l.key, anim: l.anim, x: px, y: py, quarter: null });
          continue;
        }
        // W1 (inspection fix): a border between grounds next to a cell with no v2 art or raised (a wall):
        // those corners take the ground of the corner beside them, and the blended tile is drawn over the
        // other corners' quarters only — the border runs on to the wall instead of stopping square
        // (corners that are real: in the map, flat, with v2 art; the others are a wall, raised ground, ...)
        const isReal = CORNERS.map(([dx, dy], k) => inBounds(map, i + dx, j + dy) && flat(i + dx, j + dy) && cls[k] !== null);
        const real = cls.filter((c, k) => isReal[k]);
        if (real.length && new Set(real).size > 1) {
          const pick = (/** @type {number} */ k) => (isReal[k] ? cls[k] : null);
          const sub = cls.map((c, k) => pick(k) ?? pick(k ^ 1) ?? pick(k ^ 2) ?? pick(k ^ 3));
          const layers = layersOf(/** @type {string[]} */ (sub), false);
          CORNERS.forEach(([dx, dy], k) => {
            const x = i + dx;
            const y = j + dy;
            if (!inBounds(map, x, y) || !flat(x, y)) return;
            if (!isReal[k]) {
              const own = this.cellKeyV2(x, y);
              out.push({ key: own.key, anim: own.anim, x: px + dx * half, y: py + dy * half, quarter: quarterOfCorner(k) });
              return;
            }
            for (const l of layers) out.push({ key: l.key, anim: l.anim, x: px + dx * half, y: py + dy * half, quarter: TILE_QUARTER[k] });
          });
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
      // gfx W1: a region's own ground is apart (terrainArt.SPLIT_REGION_GROUND: "ground:" its calm tiles,
      // edges and step shadows; "detail:" its pictures, dunes and step rims), and on the dual grid a
      // chunk's display tiles reach one cell out of it: the next region's ground too where a cell of that
      // ring has it (only "ground:", not the rest of its art)
      const ground = (/** @type {string} */ r) => {
        const g = groundBundleOf(r);
        return g && this.assets.builders.has(g) ? g : r;
      };
      for (const r of [...list]) {
        const g = ground(r);
        if (g !== r && !list.includes(g)) list.push(g);
        // (its pictures, dunes and step rims: only the region's own chunks)
        const d = detailBundleOf(r);
        if (d && this.assets.builders.has(d) && !list.includes(d)) list.push(d);
      }
      for (const r of this.ringBundles(cx, cy)) {
        const g = ground(r);
        if (!list.includes(g)) list.push(g);
      }
      // round 3: the ruin floor's edges over water, only where the ruin floor meets water
      if (this.assets.builders.has(GROUND_RUIN_BUNDLE) && this.chunkHasRuinShore(cx, cy)) list.push(GROUND_RUIN_BUNDLE);
      // rounds 7-8: the island grounds' edge variants 2 / 3 and the step pieces, only where they are drawn
      const needs = this.chunkIslandNeeds(cx, cy);
      if (needs.edges && this.assets.builders.has(ISLAND_EDGES_BUNDLE)) list.push(ISLAND_EDGES_BUNDLE);
      if (needs.steps && this.assets.builders.has(ISLAND_STEPS_BUNDLE)) list.push(ISLAND_STEPS_BUNDLE);
    }
    // graphics v3: the plains' v3 ground, trees and props of the season, with the chunks that have plains
    list.push(...this.v3PlainsBundlesOf(cx, cy));
    // (graphics v3 forest: the forest's v3 ground, trees and props; the plains pine's bundle only where a tree is drawn as one)
    list.push(...this.v3ForestBundlesOf(cx, cy));
    const pine = this.v3PineBundleOf(cx, cy);
    if (pine) list.push(pine);
    const village = this.v3VillageBundleOf(cx, cy);
    if (village) list.push(village);
    // (graphics v3: the enemies' bundles are not a chunk's: they never hold its ground back, v3EnemyBundlesWanted)
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
   * Graphics v3 (enemyV3.js): the enemy bundles wanted now — the kinds that spawn in the regions of the
   * loaded chunks (outside every region: those that spawn there), and the kinds of the live enemies on them.
   * @param {any} state @returns {Set<string>}
   */
  v3EnemyBundlesWanted(state) {
    /** @type {Set<string>} */
    const out = new Set();
    const add = (/** @type {string} */ kind) => {
      const b = v3EnemyBundle(kind);
      if (this.assets.builders.has(b)) out.add(b);
    };
    for (const c of this.chunks.values()) {
      const key = `e${c.cx},${c.cy}`;
      let kinds = this.v2Tiles.get(key);
      if (kinds === undefined) {
        const x0 = c.cx * CHUNK;
        const y0 = c.cy * CHUNK;
        const here = this.regions.filter((r) => r.tx < x0 + CHUNK && r.tx + r.tw > x0 && r.ty < y0 + CHUNK && r.ty + r.th > y0).map((r) => r.id);
        kinds = [...new Set((here.length ? here : ['']).flatMap((r) => [...(this.v3EnemyKinds?.get(r) ?? [])]))];
        this.v2Tiles.set(key, kinds);
      }
      for (const k of kinds) add(k);
    }
    // (only the enemies on the loaded chunks: the others are far away and not drawn)
    const size = CHUNK * this.map.tileSize;
    for (const e of state.enemies) if (!e.boss && !e.final && V3_ENEMY_KINDS.includes(e.kind) && this.chunks.has(this.chunkKey(Math.floor(e.x / size), Math.floor(e.y / size)))) add(e.kind);
    return out;
  }

  /**
   * Graphics v3 (VILLAGE.md 4.0): the bundle of the village's houses, fences, well and signposts in the
   * current season ("v3:village:<season>", summer's in spring), for a chunk that has any of them, else null.
   * @param {number} cx @param {number} cy
   */
  v3VillageBundleOf(cx, cy) {
    if (!this.v3) return null;
    const b = v3VillageBundle(this.season);
    if (!this.assets.builders.has(b)) return null;
    const key = `v${cx},${cy}`;
    let has = this.v2Tiles.get(key);
    if (has === undefined) {
      has = this.map.objects.some((/** @type {any} */ o) => Math.floor(o.tx / CHUNK) === cx && Math.floor(o.ty / CHUNK) === cy && V3_VILLAGE_TYPES.includes(o.type)) ? ['y'] : [];
      this.v2Tiles.set(key, has);
    }
    return has.length ? b : null;
  }

  /**
   * Graphics v3: the bundles of the plains' v3 art in the current season ("v3:plains:<season>", summer's
   * in spring, and the flow shapes summer and autumn share) when a chunk has plains ground or a part of
   * the plains region, else none. @param {number} cx @param {number} cy
   */
  v3PlainsBundlesOf(cx, cy) {
    if (!this.v3) return [];
    const bs = v3PlainsBundles(this.season).filter((b) => this.assets.builders.has(b));
    if (!bs.length) return [];
    const x0 = cx * CHUNK;
    const y0 = cy * CHUNK;
    const inRegion = this.regions.some((r) => r.id === 'plains' && r.tx < x0 + CHUNK && r.tx + r.tw > x0 && r.ty < y0 + CHUNK && r.ty + r.th > y0);
    return inRegion || (this.groundV2 && this.chunkClasses(cx, cy).includes('plains')) ? bs : [];
  }

  /**
   * Graphics v3 (FOREST.md 4.0): the bundles of the forest's v3 art in the current season ("v3:forest:<season>",
   * summer's in spring, and the flow shapes summer and autumn share) when a chunk has forest ground or a part
   * of the forest region, else none. Held only by the chunks that need them (not by regionNear). @param {number} cx @param {number} cy
   */
  v3ForestBundlesOf(cx, cy) {
    if (!this.v3) return [];
    const bs = v3ForestBundles(this.season).filter((b) => this.assets.builders.has(b));
    if (!bs.length) return [];
    const x0 = cx * CHUNK;
    const y0 = cy * CHUNK;
    const inRegion = this.regions.some((r) => r.id === 'forest' && r.tx < x0 + CHUNK && r.tx + r.tw > x0 && r.ty < y0 + CHUNK && r.ty + r.th > y0);
    return inRegion || (this.groundV2 && this.chunkClasses(cx, cy).includes('moss')) ? bs : [];
  }

  /**
   * Graphics v3: the plains pine's bundle of the season ("v3:plains:pine.<season>", v3Plains.v3PinePartOf) for a
   * chunk that has a plains tree drawn as the pine, else null. The map places no pine within 2 chunks of the
   * forest (v3TreeLook, FOREST.md 4), so it is never held beside the forest's art. Fixed for the map.
   * @param {number} cx @param {number} cy
   */
  v3PineBundleOf(cx, cy) {
    if (!this.v3) return null;
    const b = v3PineBundle(this.season);
    if (!this.assets.builders.has(b)) return null;
    const key = `p${cx},${cy}`;
    let has = this.v2Tiles.get(key);
    if (has === undefined) {
      has = this.map.objects.some((/** @type {any} */ o) => o.type === 'tree' && Math.floor(o.tx / CHUNK) === cx && Math.floor(o.ty / CHUNK) === cy && regionAt(this.regions, o.tx, o.ty)?.id === 'plains' && this.v3TreeLook(o).kind === 'pine') ? ['y'] : [];
      this.v2Tiles.set(key, has);
    }
    return has.length ? b : null;
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
   * W1 (NAMES.md 2b): the step rims of a raised cell — "<prefix>.step.<mask>.<v>" (mask N 1 + E 2 + W 4
   * of the lower sides, v = hash(tx + 5, ty + 9) % 2) and the inner corners "<prefix>.step.inner.<ne|nw>"
   * (north and east / west not lower, the NE / NW cell lower) — or null when its ground has no v2 art
   * (then the 1-px lines are drawn, as in v1). Keys without the season (v2Texture adds it).
   * @param {number} tx @param {number} ty @param {number} h its height
   * @param {boolean} lowerNorth @param {boolean} lowerEast @param {boolean} lowerWest
   * @returns {{ rims: string[] } | null}
   */
  stepPieces(tx, ty, h, lowerNorth, lowerEast, lowerWest) {
    const cls = this.groundClassAt(tx, ty);
    if (!cls || cls === 'water') return null;
    const map = this.map;
    const p = /** @type {Record<string, string>} */ (PREFIX)[cls];
    const rims = [];
    const mask = (lowerNorth ? 1 : 0) + (lowerEast ? 2 : 0) + (lowerWest ? 4 : 0);
    if (mask) rims.push(`${p}.step.${mask}.${hash(tx + 5, ty + 9) % 2}`);
    const lowerAt = (/** @type {number} */ x, /** @type {number} */ y) => inBounds(map, x, y) && map.elev[y * map.width + x] < h;
    if (!lowerNorth && !lowerEast && lowerAt(tx + 1, ty - 1)) rims.push(`${p}.step.inner.ne`);
    if (!lowerNorth && !lowerWest && lowerAt(tx - 1, ty - 1)) rims.push(`${p}.step.inner.nw`);
    return { rims };
  }

  /**
   * W1 (NAMES.md 2b): the shadow a raised cell casts on the lower cell east of it,
   * "<prefix of the lower cell>.step.shade.<v>" (v = hash(tx + 6, ty + 9) % 2), or null when that cell is
   * water or has no v2 art (then the translucent strip, as in v1). @param {number} tx @param {number} ty
   */
  stepShadeKey(tx, ty) {
    const east = this.groundClassAt(tx + 1, ty);
    if (!east || east === 'water') return null;
    return `${/** @type {Record<string, string>} */ (PREFIX)[east]}.step.shade.${hash(tx + 6, ty + 9) % 2}`;
  }

  /**
   * W1 2b: draws a row's step shadows after all the surfaces of the row — in a container of their own,
   * sorted just after every chunk's row container of that row (a slightly lower raised cell to the east,
   * even in the next chunk, does not hide them), kept with the chunk's rows.
   * @param {Map<number, Sprite[]>} shades @param {number} ty @param {Map<number, Container>} rows @param {number} cx
   */
  flushShades(shades, ty, rows, cx) {
    const list = shades.get(ty);
    if (!list) return;
    const c = new Container();
    c.label = `step-shades-${ty}-${cx}`;
    c.zIndex = ty * this.map.tileSize + 0.002 + cx * 1e-5;
    for (const sh of list) c.addChild(sh);
    this.actors.addChild(c);
    rows.set(ty + 0.5, c);
    shades.delete(ty);
  }

  /**
   * W1 rounds 7-8: whether a chunk draws an island ground's edge overlay (island grass, sand or path over
   * a lower ground or water in one of its display tiles) and step pieces (a raised island ground or
   * ruin cell with a lower north / east / west neighbour, or such a lower east cell's shadow). Fixed
   * for the map. @param {number} cx @param {number} cy @returns {{ edges: boolean, steps: boolean }}
   */
  chunkIslandNeeds(cx, cy) {
    const key = `n${cx},${cy}`;
    let out = this.v2Tiles.get(key);
    if (out === undefined) {
      const map = this.map;
      const ISLAND = ['grass', 'sand', 'path'];
      const clsAt = (/** @type {number} */ x, /** @type {number} */ y) => this.groundClassAt(Math.max(0, Math.min(map.width - 1, x)), Math.max(0, Math.min(map.height - 1, y)));
      let edges = false;
      for (let j = cy * CHUNK - 1; j < (cy + 1) * CHUNK && !edges; j++) {
        for (let i = cx * CHUNK - 1; i < (cx + 1) * CHUNK && !edges; i++) {
          const cs = CORNERS.map(([dx, dy]) => clsAt(i + dx, j + dy));
          const rank = (/** @type {string | null} */ c) => (c === 'water' ? -1 : c === null ? 99 : PRIORITY.indexOf(c));
          const low = Math.min(...cs.filter((c) => c !== null).map(rank));
          edges = cs.some((c) => c !== null && ISLAND.includes(c) && rank(c) > low);
        }
      }
      let steps = false;
      const stepGround = (/** @type {string | null} */ c) => c !== null && (ISLAND.includes(c) || c === 'ruin');
      for (let y = cy * CHUNK; y < Math.min(map.height, (cy + 1) * CHUNK) && !steps; y++) {
        for (let x = cx * CHUNK; x < Math.min(map.width, (cx + 1) * CHUNK) && !steps; x++) {
          const h = map.elev[y * map.width + x];
          if (h === 0) continue;
          const lower = (/** @type {number} */ nx, /** @type {number} */ ny) => inBounds(map, nx, ny) && map.elev[ny * map.width + nx] < h;
          if (stepGround(this.groundClassAt(x, y)) && (lower(x + 1, y) || lower(x - 1, y) || lower(x, y - 1) || lower(x + 1, y - 1) || lower(x - 1, y - 1))) steps = true;
          if (lower(x + 1, y) && stepGround(this.groundClassAt(x + 1, y))) steps = true;
        }
      }
      out = { edges, steps };
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
    const waterPieces = this.groundV2 ? this.buildGroundV2(base, cx, cy) : [];
    /** gfx W1 2b: the step shadows of each row, drawn after all its surfaces. @type {Map<number, Sprite[]>} */
    const shades = new Map();
    for (let ty = cy * CHUNK; ty < y1; ty++) {
      if (ty > cy * CHUNK) this.flushShades(shades, ty - 1, rows, cx);
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
          // gfx W1 (NAMES.md 2b, rounds 7-8): with the v2 ground, a ground with v2 art draws its step
          // rim (and inner corners) right after its surface instead of the 1-px lines, and its shadow
          // on the lower east cell after all the surfaces of the row (shades, flushShades)
          const step = this.groundV2 ? this.stepPieces(tx, ty, h, lowerNorth, lowerEast, lowerWest) : null;
          if (step) {
            const at = row.getChildIndex(surface) + 1;
            let n = 0;
            for (const key of step.rims) {
              const tex = this.v2Texture(key);
              if (!tex) continue;
              const r = new Sprite(tex);
              r.position.set(x, top);
              r.tint = surface.tint;
              row.addChildAt(r, at + n++);
            }
          } else {
            if (lowerEast) row.addChild(this.edge(x + ts - EDGE_PX, top, EDGE_PX, ts));
            if (lowerWest) row.addChild(this.edge(x, top, EDGE_PX, ts));
            if (lowerNorth) row.addChild(this.edge(x, top, ts, EDGE_PX));
          }
          if (lowerEast) {
            // Light comes from the upper left: cast a shadow onto the lower ground to the east.
            const eastH = map.elev[i + 1];
            const shadeKey = this.groundV2 ? this.stepShadeKey(tx, ty) : null;
            const tex = shadeKey ? this.v2Texture(shadeKey) : null;
            if (tex) {
              const sh = new Sprite(tex);
              sh.position.set(x + ts, ty * ts - eastH);
              sh.tint = levelTint(eastH, this.releaseTerrain);
              const list = shades.get(ty) ?? [];
              list.push(sh);
              shades.set(ty, list);
            } else {
              const shade = this.edge(x + ts, ty * ts - eastH, CLIFF_SHADOW_PX, ts);
              shade.alpha = CLIFF_SHADOW_ALPHA;
              row.addChild(shade);
            }
          }
        }

        const list = extents.get(ty) ?? [];
        list.push({ x0: x, x1: x + ts, y0: top, y1: Math.max(faceBottom, faceTop) });
        extents.set(ty, list);
      }
    }
    this.flushShades(shades, y1 - 1, rows, cx);
    /** @type {ReturnType<GameView['addV3Decor']> | null} */
    let decor = null;
    /** graphics v3: the chunk's open-ground props, above the ground (and its cache). @type {Container | null} */
    let props = null;
    if (this.v3) {
      this.groupGround(base);
      props = new Container();
      props.label = `props-${cx},${cy}`;
      decor = this.addV3Decor(props, cx, cy, x1, y1);
      props.tint = levelTint(0, this.releaseTerrain);
      this.v3DecorLayer.addChild(props);
      this.groundCache?.invalidate();
    }
    base.tint = levelTint(0, this.releaseTerrain);
    this.base.addChild(base);
    // A chunk's flat ground -> one textured quad per frame, cached over the whole chunk (see
    // chunkCacheArea: a partial area could get a screen-sized texture and seams), at the terrain art's
    // density (2 with the release terrain, else its fine pixels were halved: terrainArt.groundCacheResolution).
    const area = chunkCacheArea(cx, cy, ts);
    base.boundsArea = new Rectangle(area.x, area.y, area.width, area.height);
    // graphics v3: no cache (STYLE.md 10.1 (5)); the tiles stay sprites in a render group of their own, so
    // they are not re-transformed every frame (the display tiles over the chunk's edge are drawn once, by
    // the chunk they start in: groundPiecesInto)
    if (this.v3) base.isRenderGroup = true;
    else base.cacheAsTexture({ scaleMode: 'nearest', antialias: false, resolution: groundCacheResolution(this.releaseTerrain) });
    // gfx W1: the v2 water under it, one mesh over the shared water atlas (its frames redraw no cache)
    let waterMesh = null;
    /** @type {string[]} */
    let waterKeys = [];
    if (this.groundV2 && waterPieces.length) {
      const atlas = this.ensureWaterAtlas();
      const quads = waterQuads(waterPieces, area);
      for (const k of quads.skipped) this.v2Missing.add(`${k}.0`);
      for (const k of new Set(quads.keys.map((q) => q.split('#')[0]))) if (!this.assets.hasTexture(`${k}.0`)) this.v2Missing.add(`${k}.0`);
      waterKeys = quads.keys;
      if (quads.indices.length) {
        waterMesh = atlas.mesh(quads);
        waterMesh.tint = base.tint;
        waterMesh.label = `water-${cx},${cy}`;
        this.waterLayer.addChild(waterMesh);
      }
    }

    // Objects standing in this chunk now.
    for (const o of map.objects) {
      if (o.tx < cx * CHUNK || o.tx >= x1 || o.ty < cy * CHUNK || o.ty >= y1 || this.objectSprites.has(o)) continue;
      this.addObjectSprite(o);
    }
    this.chunkStats.built++;
    return { cx, cy, base, rows, water, edges, extents, bundles: this.chunkBundles(cx, cy), waterFrame: this.waterFrame, waterMesh, waterKeys, ...(decor ? { sway: decor.sway, foot: decor.foot } : {}), ...(props ? { props } : {}) };
  }

  /** @param {Chunk} c */
  destroyChunk(c) {
    const map = this.map;
    if (!this.v3) c.base.cacheAsTexture(false);
    c.base.destroy({ children: true });
    if (c.waterMesh) {
      const g = c.waterMesh.geometry;
      c.waterMesh.destroy();
      g.destroy();
    }
    for (const r of c.rows.values()) r.destroy({ children: true });
    for (const f of c.foot ?? []) f.sprite.destroy();
    c.props?.destroy({ children: true });
    this.groundCache?.invalidate();
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
    if (this.v3) {
      // (graphics v3: with the ground cache, the ground it is about to hold: its area, a little larger than the view)
      const r = this.groundCache ? this.groundCache.plan(origin, viewW, viewH, this.camera.zoom * this.app.renderer.resolution) : { x: origin.x, y: origin.y, w: viewW, h: viewH };
      for (const c of this.chunks.values()) this.cullGround(c, r, r.w, r.h);
    }
    this.viewRect = { x: origin.x, y: origin.y, w: viewW, h: viewH };
    const ts = this.map.tileSize;
    const size = CHUNK * ts;
    const ncx = Math.ceil(this.map.width / CHUNK);
    const ncy = Math.ceil(this.map.height / CHUNK);
    const range = (/** @type {number} */ margin) => chunkRange(origin, viewW, viewH, margin, { chunkPx: size, ncx, ncy, all: this.loadAll });
    const want = range(ts * CHUNK_LOAD_MARGIN_TILES); // a little beyond the screen
    const keep = range(ts * CHUNK_KEEP_MARGIN_TILES); // hysteresis: freed only once out of view
    // graphics v3 (memory, FOREST.md 4): outdoors, no chunk wholly beside the column the camera is held in
    // (it is never on screen): e.g. at the forest's west edge, the plains' rooms chunk (x 96-127) and its
    // plains art; at the plains' east edge, the forest's ground in that chunk's ring. The display tiles over
    // such a column's west edge are drawn by its own first chunk then (groundPiecesV2).
    const b = this.v3 && this.boundsArea === '' ? this.camera.bounds : null;
    if (b && b.width >= viewW && !this.loadAll) {
      const c0 = Math.floor(b.x / size);
      const c1 = Math.floor((b.x + b.width - 1) / size);
      for (const r of [want, keep]) {
        r.x0 = Math.max(r.x0, c0);
        r.x1 = Math.min(r.x1, c1);
      }
    }
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
        const stillWanted = waiting.has(b) || !!this.v3SeasonWant?.includes(b) || this.v3EnemyLive.has(b) || this.regions.some((r) => r.bundle === b && this.regionNear(r, origin, viewW, viewH));
        if (!stillWanted) {
          if (b === 'region:plains') this.npcs.clear();
          this.dropBossSprites();
          // graphics v3: an enemy kind's frames: drop that kind's sprites first (redrawn next frame from the base bundle)
          const kind = /^v3:enemy:(\w+)$/.exec(b)?.[1];
          if (kind) this.dropEnemySpritesOf(kind);
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

  /** Graphics v3: drops the sprites of one normal enemy kind before its bundle goes (as dropBossSprites). @param {string} kind */
  dropEnemySpritesOf(kind) {
    for (const id of this.enemySprites.ids()) if (this.enemyKeys.get(id)?.startsWith(`enemy.${kind}.`)) this.enemySprites.drop(id);
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
      // (graphics v3: the forest's own v3 trees where they are loaded, FOREST.md 1)
      const v3 = r === 'forest' && this.v3 ? this.v3ForestTreeKey(o, timeSec) : null;
      if (v3) return v3;
      if (r === 'forest' || r === 'mountains') return `${r}.pine`;
    }
    if (o.type === 'charm_shelf') return this.charmHome ? 'obj.charm_shelf.on' : 'obj.charm_shelf'; // P10.1
    if (o.type === 'star_ring') return this.ringOpen ? 'obj.star_ring.on' : 'obj.star_ring.off'; // v1.0
    if (this.v3) {
      const v3 = this.v3ObjectKey(o, timeSec) ?? this.v3VillageKey(o);
      if (v3) return v3;
    }
    return `obj.${o.type}`;
  }

  /**
   * Graphics v3: the v3 art a plains object is drawn with, where it is loaded, in the season's look
   * (summer's in spring; only the drawing: the object, its tile, collision and saves are unchanged):
   *   - a tree: one of the 4 v3 trees by the room around it (v3Plains.treeKind: the large broadleaf only
   *     with nothing within 2 tiles, the middle one or the pine with nothing on the next tiles, the
   *     sapling in a grove), 1 grove tree in 16 a fallen log; swaying (v3Plains.swayStep)
   *   - a burnt tree (a stump): the v3 stump
   *   - every other house (by its tile): the stone and timber house (same 3-tile footprint)
   * @param {any} o @param {number} [timeSec] @returns {string | null}
   */
  v3ObjectKey(o, timeSec = 0) {
    if (regionAt(this.regions, o.tx, o.ty)?.id !== 'plains') return null;
    const has = (/** @type {string} */ k) => this.assets.hasTexture(k);
    if (o.type === 'tree') {
      const look = this.v3TreeLook(o);
      const n = this.v3FrameCount(look.what, look.kind);
      if (!n) return null;
      const f = look.what === 'tree' ? swayFrame(TREE_SWAY, n, swayStep(o.tx, o.ty, timeSec)) : 0;
      return floraKey(this.season, look.what, look.kind, f);
    }
    if (o.type === 'stump' && this.v3FrameCount('prop', 'stump')) return floraKey(this.season, 'prop', 'stump', 0);
    if (o.type === 'house' && hash01(o.tx, o.ty, 77) < 0.5 && has('obj.v3.house_stone')) return 'obj.v3.house_stone';
    return null;
  }

  /**
   * Graphics v3: the village's new kinds (game/world/villageProps.js, only in the v3 view): a fence piece
   * (h / l / r / post), the well, a signpost. Their art is the village bundle's ("v3:village:<season>").
   * @param {any} o @returns {string | null}
   */
  v3VillageKey(o) {
    if (o.type === 'fence') return `obj.v3.fence.${o.kind ?? 'post'}`;
    if (o.type === 'well') return 'obj.v3.well';
    if (o.type === 'signpost') return 'obj.v3.signpost';
    return null;
  }

  /**
   * Graphics v3: how a plains or forest tree is drawn (fixed per tree): a plains tree by v3Plains.plainsTreeLook
   * (never the pine within 2 chunks of the forest: v3Forest.plainsPineBanned, FOREST.md 4), a forest tree by
   * v3Forest.forestTreeLook. @param {any} o @returns {{ what: 'tree' | 'prop', kind: string, set?: 'plains' | 'forest' }}
   */
  v3TreeLook(o) {
    let look = this.v3Looks.get(o);
    if (!look) {
      const room = this.v3TreeRoom(o.tx, o.ty);
      if (regionAt(this.regions, o.tx, o.ty)?.id === 'forest') look = forestTreeLook(room, this.v3TreeDense(o.tx, o.ty), hash01(o.tx, o.ty, 961), hash01(o.tx, o.ty, 962));
      else {
        this.v3PineBanned ??= plainsPineBanned(this.regions, CHUNK);
        look = plainsTreeLook(room, hash01(o.tx, o.ty, 931), hash01(o.tx, o.ty, 932), !this.v3PineBanned(o.tx, o.ty));
      }
      this.v3Looks.set(o, look);
    }
    return look;
  }

  /** Graphics v3 (forest): whether the 8 tiles round a tree all hold trees (deep in the wood). @param {number} tx @param {number} ty */
  v3TreeDense(tx, ty) {
    this.v3TreeRoom(0, 0); // (makes v3Trees)
    const trees = /** @type {Set<number>} */ (this.v3Trees);
    const w = this.map.width;
    for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) if ((dx || dy) && !trees.has((ty + dy) * w + tx + dx)) return false;
    return true;
  }

  /**
   * Graphics v3 (forest, FOREST.md 1): the v3 art a forest tree is drawn with where it is loaded (one of the
   * 4 trees, swaying; 1 edge tree in 20 a mossy log), else null (the v1 forest.pine). @param {any} o @param {number} timeSec
   */
  v3ForestTreeKey(o, timeSec) {
    const look = this.v3TreeLook(o);
    const n = this.v3FrameCount(look.what, look.kind, 'forest');
    if (!n) return null;
    const f = look.what === 'tree' ? swayFrame(TREE_SWAY, n, swayStep(o.tx, o.ty, timeSec)) : 0;
    return floraKey(this.season, look.what, look.kind, f, 'forest');
  }

  /** Graphics v3: how many frames of a plains (forest) tree / prop kind are loaded in this season. @param {'tree' | 'prop'} what @param {string} kind @param {'plains' | 'forest'} [set] */
  v3FrameCount(what, kind, set = 'plains') {
    const version = `${this.assets.version}|${this.season}`;
    if (this.v3Frames.version !== version) this.v3Frames = { version, n: new Map() };
    const k = `${set}.${what}.${kind}`;
    let n = this.v3Frames.n.get(k);
    if (n === undefined) {
      n = floraFrames((key) => this.assets.hasTexture(key), this.season, what, kind, set);
      this.v3Frames.n.set(k, n);
    }
    return n;
  }

  /**
   * Graphics v3: the plains props (STYLE.md 7.2, v3Plains.PROPS), drawn only (nothing to bump into, never
   * saved), fixed per tile by hash, in the season's look:
   *   - on open plains grass (walkable, nothing on it or next to it but trees, plains grass all round, so
   *     never on a path or an edge): grass tufts, tall grass, flowers (each patch leaning to one of the
   *     3), clover, a low shrub, pebbles, mushrooms near trees — in loose patches (v3Plains.openProp),
   *     off the tile's centre (0-8 game px); in the ground's render group
   *   - at the foot of 1 tree in 4, on the tree's own tile (the player cannot stand there): a bush, a
   *     berry bush, a rock, mushrooms (v3Plains.treeFootProp); with the actors, just in front of the tree
   * Grass and flowers sway (their 2 frames). Only where the season's v3 art is loaded.
   * Graphics v3 forest (FOREST.md 1-2, v3Forest.js): in the forest region the same, with the forest's props:
   * ferns (swaying) and toadstools on open moss (forestOpenProp), and at the foot of 1 tree in 3 whose front
   * (south) tile is open: roots beside the trunk (rootsOffset), a fern, a mossy rock, toadstools (forestFootProp).
   * @param {Container} base @param {number} cx @param {number} cy @param {number} x1 @param {number} y1
   * @returns {{ sway: { sprite: Sprite, kind: string, frames: number, tx: number, ty: number, frame: number, set?: 'plains' | 'forest' }[], foot: { sprite: Sprite, o: any }[] }}
   *   the swaying ones, and those with the actors (destroyed with the chunk)
   */
  addV3Decor(base, cx, cy, x1, y1) {
    const map = this.map;
    const ts = map.tileSize;
    /** @type {{ sprite: Sprite, kind: string, frames: number, tx: number, ty: number, frame: number, set?: 'plains' | 'forest' }[]} */
    const sway = [];
    /** @type {{ sprite: Sprite, o: any }[]} */
    const foot = [];
    if (this.v3FrameCount('prop', 'fern', 'forest')) this.addV3ForestDecor(base, cx, cy, x1, y1, sway, foot);
    if (!this.v3FrameCount('prop', 'tuft')) return { sway, foot };
    if (!this.v3Taken) this.v3Taken = new Set(map.objects.filter((/** @type {any} */ o) => o.type !== 'tree').map((/** @type {any} */ o) => o.ty * map.width + o.tx));
    this.v3TreeRoom(0, 0); // (makes v3Trees)
    const trees = /** @type {Set<number>} */ (this.v3Trees);
    const plains = (/** @type {number} */ x, /** @type {number} */ y) => inBounds(map, x, y) && map.elev[y * map.width + x] === 0 && map.shape[y * map.width + x] !== Shape.RAMP_N && this.groundClassAt(x, y) === 'plains';
    const make = (/** @type {string} */ kind, /** @type {number} */ tx, /** @type {number} */ ty) => {
      const frames = this.v3FrameCount('prop', kind);
      if (!frames) return null;
      const f = frames > 1 ? swayFrame(PROP_SWAY, frames, swayStep(tx, ty, 0)) : 0;
      const key = floraKey(this.season, 'prop', kind, f);
      const sp = new Sprite(this.assets.texture(key));
      const [ax, ay] = this.assets.meta(key).anchor;
      sp.anchor.set(ax, ay);
      /** @type {any} */ (sp).v3Prop = kind; // (v3Stats)
      if (frames > 1) sway.push({ sprite: sp, kind, frames, tx, ty, frame: f });
      return sp;
    };
    for (let ty = cy * CHUNK; ty < y1; ty++) {
      for (let tx = cx * CHUNK; tx < x1; tx++) {
        const i = ty * map.width + tx;
        if (regionAt(this.regions, tx, ty)?.id !== 'plains') continue;
        if (trees.has(i)) {
          // at the foot of a tree, on its tile
          const o = this.v3TreeObjectAt(tx, ty);
          if (!o || o.gone || this.v3TreeLook(o).what !== 'tree') continue;
          const kind = treeFootProp(hash01(tx, ty, 941), hash01(tx, ty, 942));
          if (!kind) continue;
          const sp = make(kind, tx, ty);
          if (!sp) continue;
          const room = Math.max(0, 8 - PROPS[kind].w / 2);
          const [dx, dy] = this.placement && outdoorAt(this.outdoors, tx, ty) ? decorOffset(tx, ty) : [0, 0];
          const x = tx * ts + ts / 2 + dx + Math.round((hash01(tx, ty, 943) * 2 - 1) * room);
          const feetY = ty * ts + ts + dy;
          sp.position.set(x, feetY - 1 - map.elev[i]);
          sp.zIndex = feetY + 0.001;
          this.actors.addChild(sp);
          foot.push({ sprite: sp, o });
          continue;
        }
        if (!plains(tx, ty) || map.solid[i] || this.v3Taken.has(i)) continue;
        if (!plains(tx - 1, ty) || !plains(tx + 1, ty) || !plains(tx, ty - 1) || !plains(tx, ty + 1)) continue;
        let near = false;
        let blocked = false;
        for (let dy = -2; dy <= 2 && !blocked; dy++) {
          for (let dx = -2; dx <= 2; dx++) {
            const k = (ty + dy) * map.width + tx + dx;
            if (trees.has(k)) near = true;
            if (Math.abs(dx) <= 1 && Math.abs(dy) <= 1 && this.v3Taken.has(k)) blocked = true;
          }
        }
        if (blocked) continue;
        const kind = openProp(valueNoise(tx, ty, 6, 31), valueNoise(tx, ty, 9, 57), hash01(tx, ty, 919), hash01(tx, ty, 920), near);
        if (!kind) continue;
        const sp = make(kind, tx, ty);
        if (!sp) continue;
        sp.position.set(tx * ts + 4 + Math.floor(hash01(tx, ty, 921) * 9), ty * ts + 8 + Math.floor(hash01(tx, ty, 922) * 8));
        base.addChild(sp);
      }
    }
    return { sway, foot };
  }

  /**
   * Graphics v3 forest: addV3Decor's forest part (its props into `sway` / `foot`).
   * @param {Container} base @param {number} cx @param {number} cy @param {number} x1 @param {number} y1
   * @param {{ sprite: Sprite, kind: string, frames: number, tx: number, ty: number, frame: number, set?: 'plains' | 'forest' }[]} sway @param {{ sprite: Sprite, o: any }[]} foot
   */
  addV3ForestDecor(base, cx, cy, x1, y1, sway, foot) {
    const map = this.map;
    const ts = map.tileSize;
    if (!this.v3Taken) this.v3Taken = new Set(map.objects.filter((/** @type {any} */ o) => o.type !== 'tree').map((/** @type {any} */ o) => o.ty * map.width + o.tx));
    this.v3TreeRoom(0, 0); // (makes v3Trees)
    const trees = /** @type {Set<number>} */ (this.v3Trees);
    const moss = (/** @type {number} */ x, /** @type {number} */ y) => inBounds(map, x, y) && map.elev[y * map.width + x] === 0 && map.shape[y * map.width + x] !== Shape.RAMP_N && this.groundClassAt(x, y) === 'moss';
    const make = (/** @type {keyof typeof FOREST_PROPS} */ kind, /** @type {number} */ tx, /** @type {number} */ ty) => {
      const frames = this.v3FrameCount('prop', kind, 'forest');
      if (!frames) return null;
      const f = frames > 1 ? swayFrame(PROP_SWAY, frames, swayStep(tx, ty, 0)) : 0;
      const key = floraKey(this.season, 'prop', kind, f, 'forest');
      const sp = new Sprite(this.assets.texture(key));
      const [ax, ay] = this.assets.meta(key).anchor;
      sp.anchor.set(ax, ay);
      /** @type {any} */ (sp).v3Prop = `forest.${kind}`; // (v3Stats)
      if (frames > 1) sway.push({ sprite: sp, kind, frames, tx, ty, frame: f, set: 'forest' });
      return sp;
    };
    for (let ty = cy * CHUNK; ty < y1; ty++) {
      for (let tx = cx * CHUNK; tx < x1; tx++) {
        const i = ty * map.width + tx;
        if (regionAt(this.regions, tx, ty)?.id !== 'forest') continue;
        if (trees.has(i)) {
          // at the foot of a tree whose front is open (the others' feet are hidden by the trees in front)
          if (trees.has(i + map.width) || !moss(tx, ty + 1)) continue;
          const o = this.v3TreeObjectAt(tx, ty);
          if (!o || o.gone || this.v3TreeLook(o).what !== 'tree') continue;
          const kind = forestFootProp(hash01(tx, ty, 971), hash01(tx, ty, 972));
          if (!kind) continue;
          const sp = make(kind, tx, ty);
          if (!sp) continue;
          let x;
          let feetY = ty * ts + ts;
          if (kind === 'roots') {
            const [dx, dy] = rootsOffset(tx, ty);
            x = tx * ts + ts / 2 + dx;
            feetY += dy;
          } else x = tx * ts + ts / 2 + Math.round((hash01(tx, ty, 973) * 2 - 1) * Math.max(0, 8 - FOREST_PROPS[kind].w / 2));
          sp.position.set(x, feetY - 1 - map.elev[i]);
          sp.zIndex = feetY + 0.001;
          this.actors.addChild(sp);
          foot.push({ sprite: sp, o });
          continue;
        }
        if (!moss(tx, ty) || map.solid[i] || this.v3Taken.has(i)) continue;
        if (!moss(tx - 1, ty) || !moss(tx + 1, ty) || !moss(tx, ty - 1) || !moss(tx, ty + 1)) continue;
        let near = false;
        let blocked = false;
        for (let dy = -2; dy <= 2 && !blocked; dy++) {
          for (let dx = -2; dx <= 2; dx++) {
            const k = (ty + dy) * map.width + tx + dx;
            if (trees.has(k)) near = true;
            if (Math.abs(dx) <= 1 && Math.abs(dy) <= 1 && this.v3Taken.has(k)) blocked = true;
          }
        }
        if (blocked) continue;
        const kind = forestOpenProp(valueNoise(tx, ty, 6, 33), hash01(tx, ty, 974), hash01(tx, ty, 975), near);
        if (!kind) continue;
        const sp = make(kind, tx, ty);
        if (!sp) continue;
        sp.position.set(tx * ts + 4 + Math.floor(hash01(tx, ty, 976) * 9), ty * ts + 8 + Math.floor(hash01(tx, ty, 977) * 8));
        base.addChild(sp);
      }
    }
  }

  /** Graphics v3: the tree object on a tile, or null. @param {number} tx @param {number} ty */
  v3TreeObjectAt(tx, ty) {
    if (!this.v3TreeObjects) {
      /** @type {Map<number, any>} */
      const m = new Map();
      for (const o of this.map.objects) if (o.type === 'tree') m.set(o.ty * this.map.width + o.tx, o);
      this.v3TreeObjects = m;
    }
    return this.v3TreeObjects.get(ty * this.map.width + tx) ?? null;
  }

  /**
   * Graphics v3 (debug, tests): the plains' v3 trees and props on the loaded chunks — trees by their look,
   * the open-ground and tree-foot props by kind, and the sway frames shown now (trees, props).
   */
  v3Stats(region = 'plains') {
    const set = region === 'forest' ? 'forest' : 'plains';
    /** @type {Record<string, number>} */
    const trees = {};
    /** @type {Record<string, number>} */
    const props = {};
    const frames = { trees: [0, 0, 0], props: [0, 0] };
    for (const e of this.objectSprites.values()) {
      if (e.o.type !== 'tree' || regionAt(this.regions, e.o.tx, e.o.ty)?.id !== region || !this.v3FrameCount('tree', set === 'forest' ? 'pine_s' : 'sapling', set)) continue;
      const l = this.v3TreeLook(e.o);
      const k = l.what === 'tree' ? l.kind : `prop.${l.kind}`;
      trees[k] = (trees[k] ?? 0) + 1;
      if (e.v3 && e.frame !== undefined && e.frame >= 0) frames.trees[e.frame]++;
    }
    let foot = 0;
    const mine = (/** @type {string} */ key) => (set === 'forest') === key.startsWith('forest.');
    for (const c of this.chunks.values()) {
      for (const e of c.sway ?? []) if ((e.set ?? 'plains') === set) frames.props[e.frame]++;
      for (const f of c.foot ?? []) if (regionAt(this.regions, f.o.tx, f.o.ty)?.id === region) foot++;
      // (the open-ground props are the chunk ground's own children, after its groups)
      for (const sp of (c.props ?? c.base).children) {
        const key = /** @type {any} */ (sp).v3Prop;
        if (key && mine(key)) props[key.replace(/^forest\./, '')] = (props[key.replace(/^forest\./, '')] ?? 0) + 1;
      }
    }
    return { trees, props, foot, frames, season: this.season };
  }

  /**
   * Graphics v3: the sway of the plains trees, grass and flowers (their art's frames: trees 0 / +1 / -1,
   * grass 0 / 1), a slow wave across the field (v3Plains.swayStep). Only a texture swap where the frame
   * changes. @param {number} timeSec
   */
  updateSway(timeSec) {
    for (const c of this.chunks.values()) {
      // (a prop at the foot of a tree goes with the tree: burnt, cut)
      for (const f of c.foot ?? []) f.sprite.visible = f.o.type === 'tree' && !f.o.gone;
      for (const e of c.sway ?? []) {
        const f = swayFrame(PROP_SWAY, e.frames, swayStep(e.tx, e.ty, timeSec));
        if (f === e.frame) continue;
        e.frame = f;
        e.sprite.texture = this.assets.texture(floraKey(this.season, 'prop', e.kind, f, e.set ?? 'plains'));
      }
    }
    for (const e of this.objectSprites.values()) {
      const o = e.o;
      if (o.type !== 'tree' || o.gone || !e.v3) continue;
      const look = this.v3TreeLook(o);
      if (look.what !== 'tree') continue;
      const set = look.set ?? 'plains';
      const n = this.v3FrameCount('tree', look.kind, set);
      if (n < 2) continue;
      const f = swayFrame(TREE_SWAY, n, swayStep(o.tx, o.ty, timeSec));
      if (f === e.frame) continue;
      e.frame = f;
      e.sprite.texture = this.assets.texture(floraKey(this.season, 'tree', look.kind, f, set));
    }
  }

  /**
   * Graphics v3 (no ground cache): the chunk's ground sprites in groups of V3_GROUP_TILES × V3_GROUP_TILES
   * tiles, so the groups off screen are not drawn (cullGround). The pieces of the dual grid's display
   * tiles do not overlap one another, so regrouping them keeps the picture (decor goes on top after).
   * @param {Container} base
   */
  groupGround(base) {
    const size = V3_GROUP_TILES * this.map.tileSize;
    /** @type {Map<string, Container>} */
    const groups = new Map();
    /** @type {Map<Container, Container>} */
    const opaque = new Map();
    for (const child of [...base.children]) {
      // (a sprite mirrored left to right stands at its right edge)
      const gx = Math.floor((child.scale.x < 0 ? child.x - child.width : child.x) / size);
      const gy = Math.floor(child.y / size);
      const k = `${gx},${gy}`;
      let g = groups.get(k);
      if (!g) {
        g = new Container();
        g.label = `ground-${k}`;
        // the area it covers: its tiles, and the display tiles reaching 16 px past it
        g.boundsArea = new Rectangle(gx * size, gy * size, size + 16, size + 16);
        groups.set(k, g);
      }
      // the v3 base tiles (opaque, the whole tile) first, without blending: on a phone the ground is most
      // of the screen's pixels, and an opaque tile need not read what is under it. The display tiles do
      // not overlap one another, and their base is the bottom of each, so drawing them first changes nothing.
      if (this.v3Opaque && child.label === OPAQUE_LABEL) {
        let o = opaque.get(g);
        if (!o) {
          o = new Container();
          o.label = 'opaque';
          o.blendMode = 'none';
          opaque.set(g, o);
          g.addChildAt(o, 0);
        }
        o.addChild(child);
        continue;
      }
      g.addChild(child);
    }
    base.removeChildren();
    for (const g of groups.values()) base.addChild(g);
  }

  /** Graphics v3: shows only the ground groups that reach into the view (with a tile's margin). @param {Chunk} c @param {{ x: number, y: number }} origin @param {number} vw @param {number} vh */
  cullGround(c, origin, vw, vh) {
    const m = 16;
    for (const g of c.base.children) {
      const b = g.boundsArea;
      if (!b) continue;
      const on = b.x < origin.x + vw + m && b.x + b.width > origin.x - m && b.y < origin.y + vh + m && b.y + b.height > origin.y - m;
      if (g.visible !== on) g.visible = on;
    }
  }

  /** Graphics v3: the distance (tiles, Chebyshev, up to 3) to the nearest other tree or object. @param {number} tx @param {number} ty */
  v3TreeRoom(tx, ty) {
    const map = this.map;
    if (!this.v3Trees) this.v3Trees = new Set(map.objects.filter((/** @type {any} */ o) => o.type === 'tree').map((/** @type {any} */ o) => o.ty * map.width + o.tx));
    // (and any other object: a house, a wall, a barrel — no large crown over them)
    if (!this.v3Others) this.v3Others = new Set(map.objects.filter((/** @type {any} */ o) => o.type !== 'tree').map((/** @type {any} */ o) => o.ty * map.width + o.tx));
    for (let r = 1; r <= 2; r++) {
      for (let dy = -r; dy <= r; dy++) {
        for (let dx = -r; dx <= r; dx++) {
          if (Math.max(Math.abs(dx), Math.abs(dy)) !== r) continue;
          const k = (ty + dy) * map.width + tx + dx;
          if (this.v3Trees.has(k) || this.v3Others.has(k)) return r;
        }
      }
    }
    return 3;
  }

  /** @param {any} o */
  addObjectSprite(o) {
    const map = this.map;
    const ts = map.tileSize;
    const key = this.objectKey(o, 0);
    const s = this.makeSprite(key);
    // W2: decorative objects outdoors are drawn a little off-centre, in clusters (placement.decorOffset);
    // only the drawing: collision and saves stay keyed to the tile. dy <= 0, so it still sorts by its tile.
    const [dx, dy] = this.placement && DECOR_TYPES.includes(o.type) && outdoorAt(this.outdoors, o.tx, o.ty) ? decorOffset(o.tx, o.ty) : [0, 0];
    const x = o.tx * ts + ts / 2 + dx + (o.drawDx ?? 0); // (graphics v3: the well stands across 2 tiles)
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
    if (o.type === 'tree' || o.type === 'house' || o.type === 'well') {
      const w = s.width / 2;
      occluder = { sprite: s, x0: x - w, x1: x + w, y0: feetY - z - s.height, y1: feetY - z, key: feetY };
    }
    // (graphics v3: a v3 plains tree sways, updateSway)
    this.objectSprites.set(o, this.v3 && /^(?:\w+\.)?(?:plains|forest)\.tree\.v3\./.test(key) ? { o, sprite: s, occluder, v3: true, frame: -1 } : { o, sprite: s, occluder });
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
    // (graphics v3: climb / swim / glide come from a bundle loaded on use; meanwhile their approved frames)
    this.updateHeroMove(pose.action, performance.now());
    const has = this.heroMove ? (/** @type {string} */ k) => heroDrawKey(k, (x) => this.assets.hasTexture(x)) !== null : (/** @type {string} */ k) => this.assets.hasTexture(k);
    const releaseKey = this.heroAnim.textureKey(pose, p.facing, p.moving, has);
    this.heroKey = releaseKey;
    const drawKey = releaseKey && this.heroMove ? heroDrawKey(releaseKey, (x) => this.assets.hasTexture(x)) : releaseKey;
    if (this.heroMove && drawKey !== releaseKey) this.heroMove.fallbackFrames++;
    this.heroDrawn = drawKey;
    // Otherwise the placeholder hero. Swimming: head and shoulders above the water, ripples alternate.
    const heroFrame = drawKey ?? (p.swimming ? `player.swim.${p.facing}.${Math.floor(p.walkTime * (p.moving ? 6 : 2)) % 2}` : `player.walk.${p.facing}.${frame}`);
    setFrame(this.player, this.assets, heroFrame); // (graphics v3: a left frame may be its right frame mirrored)
    const tex = this.player.texture;
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
    // graphics v3: in a boss fight in an arena larger than the view, frame the hero, the boss and its telegraph
    const aim = (this.v3 && this.fightTarget(state, x, y - z, tex.height)) || { x, y: y - camZ - aimY };
    if (this.applyBounds(state)) this.camera.snapTo(aim.x, aim.y);
    else this.camera.follow(aim.x, aim.y, dtSec);
    this.applyCamera();
    if (this.v3) {
      const o = this.camera.origin();
      this.cameraRect = { x: o.x, y: o.y, width: this.camera.viewWidth, height: this.camera.viewHeight };
    }
    this.updateSeason(state.env.now);
    this.updateSourceBundle(state);
    this.updateChunks(this.camera.origin(), this.app.screen.width / this.camera.zoom, this.app.screen.height / this.camera.zoom);
    if (this.v3) this.updateSway(timeSec); // graphics v3: the plains trees, grass and flowers sway
    this.groundCache?.update(this.camera.zoom * this.app.renderer.resolution); // graphics v3: the ground, drawn again only when needed
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
      (key) => this.assets.texture(this.seasonal(key)), // (graphics v3: the chests', checkpoints' and fires' winter look)
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

  /**
   * Graphics v3 (STYLE.md 2.3 (2)): where the camera aims in a boss fight whose arena does not fit the
   * view: between the hero and the boss, taking in the slam / wave being telegraphed, the hero always
   * on screen and clear of the UI at the top (boss bar, hearts) and bottom (fightInsets). Null outside
   * a fight, or when the whole arena fits (the camera's bounds then show all of it).
   * @param {any} state @param {number} hx @param {number} hy the hero's drawn feet (game px) @param {number} heroH
   * @returns {{ x: number, y: number } | null}
   */
  fightTarget(state, hx, hy, heroH) {
    const boss = activeBoss(state);
    if (!boss?.arena) return null;
    const ts = this.map.tileSize;
    const vw = this.camera.viewWidth;
    const vh = this.camera.viewHeight;
    if (boss.arena.tw * ts <= vw && boss.arena.th * ts <= vh) return null;
    const bx = boss.x;
    const by = boss.y - (boss.z ?? 0);
    const hero = { x0: hx - 10, x1: hx + 10, y0: hy - heroH - 4, y1: hy + 4 };
    const half = boss.final ? 32 : 28;
    const others = [{ x0: bx - half, x1: bx + half, y0: by - (boss.final ? 72 : 60), y1: by + 6 }];
    const slams = boss.pattern === 'slam' || boss.pattern === 'wave';
    if (slams && (boss.state === 'windup' || boss.state === 'attack')) {
      const r = boss.final ? (boss.pattern === 'slam' ? FINAL_BOSS.slamRadius : FINAL_BOSS.waveRadius) : BOSS_KINDS[boss.bossKind].slamRadius;
      others.push({ x0: bx - r - 2, x1: bx + r + 2, y0: by - r - 2, y1: by + r + 2 });
    }
    const insets = { top: this.fightInsets.top * vh, bottom: this.fightInsets.bottom * vh };
    return frameFight(hero, others, { width: vw, height: vh }, insets);
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
      this.silhouette.anchor.copyFrom(this.player.anchor); // (graphics v3: mirrored like the hero)
      this.silhouette.scale.x = this.player.scale.x;
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
    // graphics v3: the v3 frames of the kinds that spawn in the regions of the loaded chunks and of every
    // live normal enemy's kind (loaded in the background, kept while wanted; meanwhile an enemy is drawn
    // with the base bundle's frames)
    if (this.v3EnemyKinds) {
      this.v3EnemyLive = this.v3EnemyBundlesWanted(state);
      for (const b of this.v3EnemyLive) if (!this.assets.isLoaded(b)) this.requestBundle(b);
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

  /** gfx W1: the shared water atlas of the v2 water (made on first use, at the current frame). */
  ensureWaterAtlas() {
    if (!this.waterAtlas) {
      this.waterAtlas = new WaterAtlas(this.app.renderer, (k) => (this.assets.hasTexture(k) ? this.assets.texture(k) : null));
      this.waterAtlas.setFrame(Math.max(0, this.waterFrame));
    }
    return this.waterAtlas;
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
    // gfx W1: the v2 water is drawn from the shared water atlas: one small redraw, no chunk cache
    if (this.groundV2) {
      this.waterAtlas?.setFrame(frame);
      return;
    }
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
    if (!this.v3) c.base.updateCacheTexture();
    else this.groundCache?.invalidate();
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
