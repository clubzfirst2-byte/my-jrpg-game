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
import { hash } from './tileHash.js';
import { groundClassOf, tableIndex, uniformBlockOf } from './groundTables.js';
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
import { CORNERS, MACRO_NAMES, STEP_NAMES, PREFIX, PRIORITY, SEASONAL, WATER_FRAMES, WATER_FRAME_SEC as WATER_FRAME_SEC_V2, calmNumber, deepMapShaped, displayLayers, edgeVariantOf, landKey, macroPlacement, quarterOfCorner, ruinCellTile, ruinTile, tileScheme } from './groundV2.js';
import { GROUND_RUIN_BUNDLE, GROUND_V2_KEY, ISLAND_EDGES_BUNDLE, ISLAND_STEPS_BUNDLE, detailBundleOf, groundBundleOf, seasonGroundBundleOf, faceMaterial, faceVariant, groundCacheResolution, groundVariant, indoorLight, levelBrightness, releaseSeasonKeys, usesReleaseTerrain, waterAround, waterEdgePieces } from './assets/terrainArt.js';
import { openingView } from '../game/story/story.js';
import { enemyFrameKey, warningFlashAlpha, defeatAlpha } from './enemyAnim.js';
import { SilhouetteCache, placeFlash, RIM_FLASH } from './flashOverlay.js';
import { EnemySlots } from './enemySlots.js';
import { objectShadow, characterShadow, placeShadow, weatherShadow, shadowTexture, SHADOW } from './shadows.js';
import { PANE_AREA, WINDOW_GLOW, windowGlow, hasWindows, paneImageFromTable, windowLightSpots } from './houseWindows.js';
import { AmbientParticles, ambientKinds, mistTextures } from './ambientParticles.js';
import { HitFx } from './hitFx.js';
import { isDark, hourOf } from '../game/env/weather.js';

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
 *   extents: Map<number, { x0: number, x1: number, y0: number, y1: number }[]>, baked: any[], shade: Container, bundles: string[] }} Chunk
 * @typedef {{ o: any, sprite: Sprite, occluder: Occluder | null, shadow?: Sprite | null, shadowType?: string, shadowGone?: boolean, windows?: Sprite[] | null }} ObjectEntry
 */

const WALK_FPS = 8;
/** gfx W5: enemies drawn without a cast shadow (the storm lord's art stands in its own puddle). */
const NO_SHADOW_KINDS = new Set(['boss_storm']);
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
   * @param {{ fx?: 'v1' | 'v2' }} [opts] gfx W5: fx 'v1' = the look before the effects (fxSwitch.js)
   */
  constructor(app, assets, state, opts = {}) {
    this.app = app;
    /** gfx W5: the light / shadow / effects drawn (fxSwitch.js); false = the look before them (?fx=v1). */
    this.fxV2 = opts.fx !== 'v1';
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
    /** @type {Map<any, ObjectEntry>} object -> its sprite (loaded chunks only) */
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
    /** gfx v2 integration (start-up): the map's ground tables (groundTables.js), when given. @type {any} */
    this.groundTables = null;
    /** gfx v2 integration (start-up): chunks built per frame at most (updateChunks); no limit in play. */
    this.chunkBudget = Infinity;
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
    /** gfx W5: the sun's shadows' strength now (shadows.weatherShadow: the weather, a lightning flash) */
    this.shadowStrength = 1;
    /** every loose object shadow (crates, raised ground, chests, stones) @type {Set<Sprite>} */
    this.looseShadows = new Set();
    // gfx W5: the chests' and record stones' shadows (shadows.js)
    this.features = new FeatureView((key) => this.makeSprite(key), this.actors, this.screenLayer, state, this.fxV2 ? (g, x, y) => this.looseShadow(g, x, y) : undefined);
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
    // gfx W5 — light, shadow and effects (all pooled or cached; nothing allocated per frame):
    // cast shadows on the ground, under everything that stands: one layer whose opacity is the
    // sun's strength (the weather, a lightning flash) — changing it redraws nothing,
    this.shadowLayer = new Container();
    this.shadowLayer.label = 'shadows';
    this.world.addChildAt(this.shadowLayer, this.world.getChildIndex(this.actors));
    /** flat-ground shadows (in their chunk's container in the shadow layer), by object @type {Map<any, { sprite: Sprite, base: Container }[]>} */
    this.bakedShadows = new Map();

    /** effect groups on (setFx, for measuring) */
    const on = this.fxV2;
    this.fxOn = { shadows: on, particles: on, hitfx: on, windows: on, rain: on };
    /** villagers' and enemies' shadows: one per character sprite, kept @type {Map<Sprite, Sprite>} */
    this.charShadowOf = new Map();
    /** characters' shadows placed this frame (fxDebug), and the frame's number */
    this.charShadowN = 0;
    this.charShadowFrame = 0;
    this.placeCharShadow = (/** @type {Sprite} */ spr, /** @type {number} */ z) => this.charShadow(spr, z);
    this.npcShadowFn = (/** @type {Sprite} */ spr) => this.charShadow(spr, spr.zIndex);
    this.enemyShadowFn = (/** @type {{ owner: any, sprite: Sprite }} */ slot) => {
      // (the source has its own arena light; the storm lord stands in a puddle of its own art, and a
      // shadow on the grass under it would lift the puddle off the ground)
      if (!slot.owner.final && !NO_SHADOW_KINDS.has(slot.owner.kind)) this.charShadow(slot.sprite, slot.sprite.zIndex);
    };
    // lit windows (houseWindows.js),
    /** @type {Sprite[]} */
    this.windowSprites = [];
    /** world px of each lit window's pool of light on the ground (null until the house art is known) @type {{ x: number, y: number }[] | null} */
    this.windowLights = null;
    this.lastWindowGlow = 1;
    /** the lit glass per house texture @type {Map<Texture, { tex: Texture, scale: number } | null>} */
    this.paneTextures = new Map();
    /** lit glass, above the light map (in the glow layer) */
    this.windowLayer = new Container();
    this.windowLayer.label = 'windows';
    /** the windows' pools of light on the ground (under the actors, over the shadows) */
    this.poolLayer = new Container();
    this.poolLayer.label = 'window-pools';
    this.world.addChildAt(this.poolLayer, this.world.getChildIndex(this.actors));
    // ambient particles: lit like the world (in it, over the actors) and glowing (over the light map),
    this.ambientParticles = new AmbientParticles(assets.texture('px'), mistTextures());
    this.world.addChild(this.ambientParticles.under);
    this.ambientKinds = ambientKinds({ region: null, season: 'summer', dark: false, day: true, weather: 'clear', indoor: true, nearWater: false, snowGround: false });
    this.ambientCheckAt = -1;
    /** the ambient particles move every other frame (time gathered here) */
    this.ambientDt = 0;
    this.ambientFrame = 0;
    this.viewRect = { x: 0, y: 0, w: 0, h: 0 };
    this.nearWaterFn = (/** @type {number} */ x, /** @type {number} */ y) => this.nearWater(x, y, 2);
    // and hit effects (hitFx.js). The glowing layers follow the world's camera (applyCamera).
    this.hitFx = new HitFx(assets.texture('px'));
    this.glowLayer = new Container();
    this.glowLayer.label = 'glow';
    this.glowLayer.addChild(this.windowLayer, this.ambientParticles.glow, this.hitFx.layer);
    app.stage.addChildAt(this.glowLayer, app.stage.getChildIndex(this.weather.overlay) + 1);
    this.setFx('', false); // (the layers as fxOn says)
    /** capturing a still: the hit effects stop where they are */
    this.fxHold = false;
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
    /** the boss ring / the source's marks have something drawn (they are cleared only when needed) */
    this.bossRingDrawn = false;
    this.aimDrawn = false;
    this.sourceDrawn = false;
    this.silhouettes = new SilhouetteCache(this.fxV2 ? 'rim' : 'solid'); // gfx W5: a red rim keeps the v2 art's detail
    /** Frame counts and speeds of the enemies' actions (enemyFrames.js), cleared when the loaded art changes. @type {Map<string, { n: number, fps: number }>} */
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
    // gfx W5: the slash leaves two fading after-images (the last two frames' places).
    this.slashTrail = [this.makeSprite('fx.slash'), this.makeSprite('fx.slash')];
    for (const t of this.slashTrail) {
      t.visible = false;
      this.actors.addChild(t);
    }
    /** the slash's last two places: x, y, rotation, zIndex, shown (1/0) */
    this.slashHist = new Float64Array(10);
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
  /**
   * gfx v2 integration (start-up): the deep map worked out off the main thread (deepWorker.js), taken
   * when it is for this map and none is made yet. @param {Uint8Array | null} deep
   */
  presetDeepWater(deep) {
    if (!this.deepWater && deep && deep.length === this.map.width * this.map.height) this.deepWater = deep;
  }

  deepAt(/** @type {number} */ x, /** @type {number} */ y) {
    const map = this.map;
    // (inspection R2: the deep areas' border wanders and their corners are round: groundV2.deepMapShaped)
    if (!this.deepWater) this.deepWater = deepMapShaped(map.width, map.height, (cx, cy) => map.ground[cy * map.width + cx] === Ground.WATER, hash);
    return this.deepWater[y * map.width + x] === 1;
  }

  /** W1: a cell's ground class for the dual grid (null: drawn on the cell grid). @param {number} x @param {number} y */
  groundClassAt(x, y) {
    return groundClassOf(this.map, this.regions, this.sandUnderTrees, x, y);
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
    return tileScheme(cls) === 'C' ? ruinCellTile(x, y, hash) : this.calmAt(x, y, this.cellCalmMemo);
  }

  /**
   * A calm tile's number (groundV2.calmNumber): from the map's table when the worker made it
   * (groundTables.js; the same number), else worked out. @param {number} i @param {number} j @param {Map<number, number> | null} memo
   */
  calmAt(i, j, memo) {
    const t = this.groundTables;
    const at = t ? tableIndex(t, i, j) : -1;
    return at >= 0 ? /** @type {any} */ (t).calm[at] : calmNumber(i, j, hash, memo ?? undefined);
  }

  /**
   * gfx v2 integration (start-up): the map's ground tables worked out off the main thread
   * (groundTables.js, deepWorker.js), taken when they are this map's. @param {any} tables
   */
  presetGroundTables(tables) {
    if (tables && tables.width === this.map.width && tables.height === this.map.height) this.groundTables = tables;
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
    return uniformBlockOf(this.map, (x, y) => this.groundClassAt(x, y), i, j, k);
  }

  /**
   * W1: the picture piece of display tile (i, j), or null: groundV2.macroPlacement (the placement rule
   * lives there alone), cached per map (the same in every season).
   * @param {number} i @param {number} j @returns {{ name: string, block: string } | null}
   */
  macroAt(i, j) {
    // gfx v2 integration (start-up): from the map's table when the worker made it (groundTables.js)
    const t = this.groundTables;
    const at = t ? tableIndex(t, i, j) : -1;
    if (t && at >= 0) return t.macro[at];
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
    return tileScheme(cls) === 'C' ? ruinTile(i, j, hash) : this.calmAt(i, j, this.calmMemo);
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
    for (const p of this.groundPiecesV2(cx, cy)) {
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
      base.addChild(s);
    }
    return water;
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
    const classAt = (/** @type {number} */ x, /** @type {number} */ y) => this.groundClassAt(clampX(x), clampY(y));
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
            edgeVariant: (t, m) => edgeVariantOf(t, m, i, j, hash, classAt),
            pick: (t) => String(this.wangAt(i, j, t)),
            // a picture piece where a picture is placed
            macro: () => {
              const m = pictures ? this.macroAt(i, j) : null;
              return m && this.v2Has(landKey(c[0], m.name)) ? m.name : null;
            },
          });
        if (allFlat && cls.every((c) => c !== null)) {
          for (const l of layersOf(/** @type {string[]} */ (cls), true)) out.push({ key: l.key, anim: l.anim, x: px, y: py, quarter: null });
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
    // gfx W5: the shadows of the objects on flat ground: small pixel sprites in this chunk's own
    // container in the shadow layer (they batch into one draw with the rest; the layer's opacity is
    // the weather's, so a lightning flash or a change of weather costs nothing — baking them into the
    // ground cache meant redrawing every chunk's cache, about a second a time on the software renderer).
    /** @type {any[]} */
    const baked = [];
    const shade = new Container();
    shade.label = `shadows-${cx}-${cy}`;
    for (const o of map.objects) {
      if (o.tx < cx * CHUNK || o.tx >= x1 || o.ty < cy * CHUNK || o.ty >= y1) continue;
      if (o.type === 'crate' || map.elev[o.ty * map.width + o.tx] > 0) continue;
      const sh = this.bakedShadowSprite(o);
      if (!sh) continue;
      shade.addChild(sh);
      baked.push(o);
      let list = this.bakedShadows.get(o);
      if (!list) {
        list = [];
        this.bakedShadows.set(o, list);
      }
      list.push({ sprite: sh, base: shade });
    }
    this.shadowLayer.addChild(shade);
    base.tint = levelTint(0, this.releaseTerrain);
    this.base.addChild(base);
    // A chunk's flat ground -> one textured quad per frame, cached over the whole chunk (see
    // chunkCacheArea: a partial area could get a screen-sized texture and seams), at the terrain art's
    // density (2 with the release terrain, else its fine pixels were halved: terrainArt.groundCacheResolution).
    const area = chunkCacheArea(cx, cy, ts);
    base.boundsArea = new Rectangle(area.x, area.y, area.width, area.height);
    base.cacheAsTexture({ scaleMode: 'nearest', antialias: false, resolution: groundCacheResolution(this.releaseTerrain) });
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

    // Objects standing in this chunk now (shadows on raised ground go in their terrain row).
    for (const o of map.objects) {
      if (o.tx < cx * CHUNK || o.tx >= x1 || o.ty < cy * CHUNK || o.ty >= y1 || this.objectSprites.has(o)) continue;
      this.addObjectSprite(o, rowContainer);
    }
    this.chunkStats.built++;
    return { cx, cy, base, rows, water, edges, extents, baked, shade, bundles: this.chunkBundles(cx, cy), waterFrame: this.waterFrame, waterMesh, waterKeys };
  }

  /** @param {Chunk} c */
  destroyChunk(c) {
    const map = this.map;
    c.base.cacheAsTexture(false);
    c.base.destroy({ children: true });
    if (c.waterMesh) {
      const g = c.waterMesh.geometry;
      c.waterMesh.destroy();
      g.destroy();
    }
    c.shade.destroy({ children: true }); // (its flat-ground shadows)
    for (const o of c.baked) {
      const list = this.bakedShadows.get(o);
      if (!list) continue;
      const left = list.filter((b) => b.base !== c.shade);
      if (left.length) this.bakedShadows.set(o, left);
      else this.bakedShadows.delete(o);
    }
    for (const r of c.rows.values()) r.destroy({ children: true });
    const inChunk = (/** @type {number} */ tx, /** @type {number} */ ty) => Math.floor(tx / CHUNK) === c.cx && Math.floor(ty / CHUNK) === c.cy;
    for (const [o, e] of this.objectSprites) {
      const home = this.chunks.get(this.chunkKey(Math.floor(o.tx / CHUNK), Math.floor(o.ty / CHUNK)));
      if (inChunk(o.tx, o.ty) || !home || home === c) {
        e.sprite.destroy();
        if (e.shadow && !e.shadow.destroyed) {
          this.looseShadows.delete(e.shadow);
          e.shadow.destroy();
        }
        for (const w of e.windows ?? []) {
          w.destroy();
          this.windowSprites.splice(this.windowSprites.indexOf(w), 1);
        }
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
    // gfx v2 integration (start-up): at most chunkBudget chunks built per frame (main.js: 1 while the
    // title or the loading note is up, so no frame holds the page for long and a tap is answered); the
    // rest wait for the next frames and count as pending
    let budget = this.chunkBudget;
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
        if (budget <= 0) {
          for (const b of bundles) waiting.add(b); // (its bundles are kept for it)
          pending++;
          continue;
        }
        budget--;
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

  /**
   * A flat-ground object's shadow for a chunk's ground cache (null: none, or its art is not loaded).
   * @param {any} o
   */
  bakedShadowSprite(o) {
    const key = this.seasonal(this.objectKey(o, 0));
    if (!this.fxV2 || !this.assets.hasTexture(key)) return null;
    const tex = this.assets.texture(key);
    const g = objectShadow(o.type, tex.width, tex.height);
    if (!g) return null;
    const ts = this.map.tileSize;
    const [dx, dy] = this.decorShift(o); // (W2: under the object where it is drawn)
    const sh = this.makeShadow(g, o.tx * ts + ts / 2 + dx, o.ty * ts + ts + dy, 1);
    sh.visible = !o.gone && this.fxOn.shadows;
    return sh;
  }

  /**
   * A shadow sprite (shadows.js: pixel steps, whole game px) at the strength of the moment; it keeps
   * its geometry so a change of weather can restrengthen it.
   * @param {import('./shadows.js').ShadowGeom} g @param {number} x @param {number} y feet, world px
   * @param {number} [strength] its own strength (1 for the shadow layer's, whose opacity is the weather's)
   */
  makeShadow(g, x, y, strength = this.shadowStrength) {
    const sh = new Sprite();
    sh.tint = SHADOW.color;
    sh.label = 'shadow';
    placeShadow(sh, x, y, g, strength);
    /** @type {any} */ (sh).shadowG = g;
    return sh;
  }

  /** W2: an object's draw offset from its tile (decorative objects outdoors; [0, 0] otherwise). @param {any} o @returns {[number, number]} */
  decorShift(o) {
    return this.placement && DECOR_TYPES.includes(o.type) && outdoorAt(this.outdoors, o.tx, o.ty) ? decorOffset(o.tx, o.ty) : [0, 0];
  }

  /**
   * @param {any} o
   * @param {(ty: number) => Container} [rowOf] the chunk's terrain row for raised ground
   */
  addObjectSprite(o, rowOf) {
    const map = this.map;
    const ts = map.tileSize;
    const s = this.makeSprite(this.objectKey(o, 0));
    // W2: decorative objects outdoors are drawn a little off-centre, in clusters (placement.decorOffset);
    // only the drawing: collision and saves stay keyed to the tile. dy <= 0, so it still sorts by its tile.
    const [dx, dy] = this.decorShift(o);
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
    // gfx W5: its soft shadow, leaning to the lower right (shadows.js). On flat ground it is baked
    // into the chunk's ground (bakedShadowSprite); a moving crate's is loose in the shadow layer and
    // one on raised ground goes in its terrain row.
    /** @type {Sprite | null} */
    let shadow = null;
    const g = this.fxV2 && (o.type === 'crate' || (z > 0 && rowOf)) ? objectShadow(o.type, Math.abs(s.width), s.height) : null;
    if (g) {
      const inLayer = o.type === 'crate' || !rowOf; // (in the shadow layer, whose opacity is the weather's)
      shadow = this.makeShadow(g, x, feetY - z, inLayer ? 1 : this.shadowStrength);
      this.looseShadows.add(shadow);
      shadow.visible = !o.gone && this.fxOn.shadows;
      if (inLayer) this.shadowLayer.addChild(shadow);
      else rowOf(o.ty).addChild(shadow);
    }
    // gfx W5: a lived-in house lights its windows at night (houseWindows.js).
    /** @type {Sprite[] | null} */
    let windows = null;
    const panes = this.fxV2 && o.type === 'house' && hasWindows(s.texture) ? this.paneTexture(s.texture) : null;
    if (panes) {
      // only the glass, recoloured from the house's own pixels, drawn above the light map (it shines)
      const p = new Sprite(panes.tex);
      p.scale.set(1 / panes.scale);
      p.position.set(x + PANE_AREA.x, feetY - z + PANE_AREA.y);
      p.visible = false;
      /** @type {any} */ (p).house = s; // (it fades with the house when the player walks behind it)
      this.windowLayer.addChild(p);
      this.windowSprites.push(p);
      windows = [p];
      // and the orange pools on the ground in front of the windows (under whoever stands there)
      const P = WINDOW_GLOW.pool;
      for (const spot of windowLightSpots(x, feetY - z)) {
        const pool = new Sprite(shadowTexture({ shape: 'oval', w: P.w, h: P.h }));
        pool.tint = P.color;
        pool.position.set(Math.round(spot.x - P.w / 2), Math.round(spot.y - P.h / 2));
        pool.alpha = 0;
        /** @type {any} */ (pool).house = s;
        /** @type {any} */ (pool).pool = true;
        this.poolLayer.addChild(pool);
        this.windowSprites.push(pool);
        windows.push(pool);
      }
    }
    this.objectSprites.set(o, { o, sprite: s, occluder, shadow, shadowType: o.type, shadowGone: !!o.gone, windows });
  }

  /**
   * gfx W5: the lit glass of a house texture (houseWindows.HOUSE_GLASS, read off the release house's
   * art), made once per texture; null when there is none.
   * @param {Texture} tex @returns {{ tex: Texture, scale: number } | null}
   */
  paneTexture(tex) {
    const had = this.paneTextures.get(tex);
    if (had !== undefined) return had;
    /** @type {{ tex: Texture, scale: number } | null} */
    let out = null;
    try {
      // the glass of the release house, from the table read off its art (no pixel read-back)
      const img = paneImageFromTable();
      const scale = img.scale;
      if (img.glass > 0) {
        const c = document.createElement('canvas');
        c.width = img.w;
        c.height = img.h;
        const ctx = /** @type {CanvasRenderingContext2D} */ (c.getContext('2d'));
        const id = ctx.createImageData(img.w, img.h);
        id.data.set(img.data);
        ctx.putImageData(id, 0, 0);
        const t = Texture.from(c);
        t.source.scaleMode = 'nearest';
        out = { tex: t, scale };
      }
    } catch (err) {
      console.warn(`gfx: house windows: ${String(err)}`);
    }
    this.paneTextures.set(tex, out);
    return out;
  }

  /** Whether there is water within r tiles of a world point (fireflies). @param {number} x @param {number} y @param {number} r */
  nearWater(x, y, r) {
    const map = this.map;
    const tx = Math.floor(x / map.tileSize);
    const ty = Math.floor(y / map.tileSize);
    for (let dy = -r; dy <= r; dy++) {
      for (let dx = -r; dx <= r; dx++) {
        const X = tx + dx;
        const Y = ty + dy;
        if (X >= 0 && Y >= 0 && X < map.width && Y < map.height && map.ground[Y * map.width + X] === Ground.WATER) return true;
      }
    }
    return false;
  }

  /**
   * gfx W5 (measuring): switches an effect group off / on. Returns what is on.
   * @param {string} name shadows | particles | hitfx | windows | rain @param {boolean} on
   */
  setFx(name, on) {
    const fx = this.fxOn;
    if (this.fxV2 && name in fx) fx[/** @type {'shadows'} */ (name)] = on;
    this.shadowLayer.visible = fx.shadows;
    for (const sh of this.looseShadows) if (sh.parent !== this.shadowLayer) sh.visible = fx.shadows; // (raised ground, chests: outside the layer)
    for (const [o, list] of this.bakedShadows) for (const b of list) b.sprite.visible = fx.shadows && !o.gone;
    this.ambientParticles.under.visible = fx.particles;
    this.ambientParticles.glow.visible = fx.particles;
    this.hitFx.layer.visible = fx.hitfx;
    this.weather.fancyRain = fx.rain;
    return { ...fx };
  }

  /** gfx W5 (tests, measuring): the version drawn, the groups on, and what is showing now. */
  fxDebug() {
    let baked = 0;
    for (const list of this.bakedShadows.values()) for (const b of list) if (b.sprite.visible) baked++;
    let loose = 0;
    for (const e of this.objectSprites.values()) if (e.shadow?.visible) loose++;
    return {
      version: this.fxV2 ? 'v2' : 'v1',
      on: { ...this.fxOn },
      shadows: { baked, loose, characters: this.charShadowN },
      windows: { sprites: this.windowSprites.filter((w) => !(/** @type {any} */ (w).pool)).length, lit: this.windowSprites.filter((w) => !(/** @type {any} */ (w).pool) && w.visible).length, pools: this.windowSprites.filter((w) => /** @type {any} */ (w).pool && w.alpha > 0).length, glow: this.weather.windowGlow, lights: this.weather.windowLights.length },
      particles: { showing: this.fxOn.particles ? this.ambientParticles.visible : 0, kinds: { ...this.ambientKinds }, max: this.ambientParticles.pool.length + this.ambientParticles.glowPool.length + this.ambientParticles.mistPool.length },
      hit: { active: this.fxOn.hitfx ? this.hitFx.active : 0, pool: this.hitFx.sparks.length + this.hitFx.rings.length, trail: this.slashTrail.filter((t) => t.visible).length },
      rain: { fancy: this.weather.fancyRain, drops: this.weather.drops.filter((d) => d.s.visible).length, splashes: this.weather.splashes.filter((p) => p.s.alpha > 0).length },
    };
  }

  /** A loose shadow (restrengthened with the weather). @param {import('./shadows.js').ShadowGeom} g @param {number} x @param {number} y */
  looseShadow(g, x, y) {
    const sh = this.makeShadow(g, x, y);
    this.looseShadows.add(sh);
    return sh;
  }

  /**
   * Moves / reshapes an object's shadow (keeping its geometry for restrengthening).
   * @param {Sprite} sh @param {number} x @param {number} y @param {import('./shadows.js').ShadowGeom | null} g
   * @param {number} [strength] (1 in the shadow layer, whose opacity carries the weather's)
   */
  reshadow(sh, x, y, g, strength = sh.parent === this.shadowLayer ? 1 : this.shadowStrength) {
    if (!g) return;
    /** @type {any} */ (sh).shadowG = g;
    placeShadow(sh, x, y, g, strength);
  }

  /**
   * gfx W5: the sun's shadows at a new strength (the weather turned; a lightning flash came or went).
   * The shadow layer's opacity carries it; the few shadows outside it (on raised ground, under the
   * chests and stones) are restrengthened one by one.
   * @param {number} k 0..1
   */
  setShadowStrength(k) {
    if (k === this.shadowStrength) return;
    this.shadowStrength = k;
    this.shadowLayer.alpha = k;
    for (const sh of this.looseShadows) {
      const g = /** @type {any} */ (sh).shadowG;
      if (g && sh.parent !== this.shadowLayer) sh.alpha = g.alpha * k;
    }
  }

  /** A pooled shadow under a villager / enemy sprite (feet at its position). @param {Sprite} spr @param {number} zIndex */
  charShadow(spr, zIndex) {
    if (!spr.visible || spr.alpha <= 0.05 || spr.destroyed) return;
    if (this.shadowStrength <= 0) return; // (a lightning flash)
    // off screen: nothing to place (its shadow keeps its old place, at no opacity)
    const v = this.viewRect;
    if (spr.x < v.x - 32 || spr.x > v.x + v.w + 32 || spr.y < v.y - 16 || spr.y > v.y + v.h + 48) return;
    // each character keeps its own shadow sprite: its place in the sorted actors changes only when
    // the character moves; one not used this frame is hidden (and not gathered for drawing)
    let s = this.charShadowOf.get(spr);
    if (!s) {
      s = new Sprite();
      s.tint = SHADOW.color;
      this.actors.addChild(s);
      this.charShadowOf.set(spr, s);
    }
    /** @type {any} */ (s).seen = this.charShadowFrame;
    s.visible = true;
    this.charShadowN++;
    const g = characterShadow(Math.abs(spr.width));
    placeShadow(s, spr.x, spr.y, g, this.shadowStrength * spr.alpha);
    s.zIndex = zIndex - 0.003;
  }

  /**
   * gfx W5, per frame: villagers' and enemies' shadows, lit windows, ambient particles and hit effects.
   * @param {import('../game/state.js').GameState} state @param {number} timeSec @param {number} dtSec
   */
  updateEffects(state, timeSec, dtSec) {
    if (!this.fxV2) return; // (?fx=v1: none of them)
    // The sun's shadows: softer under clouds, rain and snow, gone in a lightning flash; indoors as they are.
    this.setShadowStrength(this.boundsArea ? 1 : weatherShadow(this.weather.kind, this.weather.flashing));
    // Where the view is (world px), for what is on screen.
    const o = this.camera.origin();
    const v = this.viewRect;
    v.x = o.x;
    v.y = o.y;
    v.w = this.app.screen.width / this.camera.zoom;
    v.h = this.app.screen.height / this.camera.zoom;
    // A chunk's flat-ground shadows are drawn only while the chunk is near the view: the hidden ones
    // are not gathered when the world's draw list is rebuilt (a fight in a forest rebuilds it often,
    // with hundreds of tree shadows in the chunks around); this changes only at a chunk border.
    const span = CHUNK * this.map.tileSize;
    for (const c of this.chunks.values()) {
      const near = c.cx * span < v.x + v.w + 64 && (c.cx + 1) * span > v.x - 64 && c.cy * span < v.y + v.h + 96 && (c.cy + 1) * span > v.y - 64;
      if (c.shade.visible !== near) c.shade.visible = near;
    }
    // Shadows under the villagers and the enemies on screen (one per character, kept; see charShadow).
    this.charShadowN = 0;
    const frame = ++this.charShadowFrame;
    if (this.fxOn.shadows) {
      this.npcs.sprites.forEach(this.npcShadowFn);
      this.enemySprites.slots.forEach(this.enemyShadowFn);
    }
    for (const [owner, sh] of this.charShadowOf) {
      if (owner.destroyed) {
        sh.destroy();
        this.charShadowOf.delete(owner);
      } else if (/** @type {any} */ (sh).seen !== frame) sh.visible = false;
    }

    // Lit windows: on at dusk, by the ambient light; their light goes into the light map.
    const amb = this.weather.ambient;
    const glow = this.boundsArea || !this.fxOn.windows ? 0 : windowGlow(amb);
    if (this.windowLights === null && this.assets.hasTexture('obj.house')) {
      const lights = [];
      if (hasWindows(this.assets.texture('obj.house'))) {
        const ts = this.map.tileSize;
        for (const o of this.map.objects) {
          if (o.type !== 'house') continue;
          const fy = o.ty * ts + ts - this.map.elev[o.ty * this.map.width + o.tx];
          lights.push(...windowLightSpots(o.tx * ts + ts / 2, fy));
        }
      }
      this.windowLights = lights;
      this.weather.windowLights = lights;
    }
    this.weather.windowGlow = glow;
    // (by day nothing to do once they are out)
    const windowsOut = glow <= 0.01 && this.lastWindowGlow <= 0.01;
    this.lastWindowGlow = glow;
    for (let i = 0; !windowsOut && i < this.windowSprites.length; i++) {
      const w = this.windowSprites[i];
      const house = /** @type {any} */ (w).house;
      const pool = /** @type {any} */ (w).pool;
      if (!pool) w.visible = glow > 0.01 && house.visible;
      // (a pool is shown by its opacity: it sits in the world, where `visible` would rebuild its draw list)
      w.alpha = pool ? (house.visible ? glow * WINDOW_GLOW.pool.alpha : 0) : glow * house.alpha;
    }

    // Ambient particles: which kinds, re-decided twice a second.
    if (timeSec - this.ambientCheckAt > 0.5 || timeSec < this.ambientCheckAt) {
      this.ambientCheckAt = timeSec;
      const ts = this.map.tileSize;
      const region = regionAt(this.regions, Math.floor(state.player.x / ts), Math.floor(state.player.y / ts))?.id ?? null;
      const lum = 0.299 * amb.r + 0.587 * amb.g + 0.114 * amb.b;
      const cx = v.x + v.w / 2;
      const cy = v.y + v.h / 2;
      this.ambientKinds = ambientKinds({
        region,
        season: this.season ?? 'summer',
        dark: isDark(amb),
        hour: hourOf(state.env.now),
        day: lum > 0.95,
        weather: this.weather.kind,
        indoor: !!this.boundsArea,
        nearWater: this.nearWater(cx, cy, Math.ceil(Math.max(v.w, v.h) / 2 / ts)),
        snowGround: region === 'mountains',
      });
    }
    // (they drift slowly: moved every other frame, with the time of both)
    this.ambientDt += dtSec;
    if ((this.ambientFrame++ & 1) === 0) {
      this.ambientParticles.update(this.ambientKinds, v, this.nearWaterFn, timeSec, Math.min(0.1, this.ambientDt));
      this.ambientDt = 0;
    }

    // Hit effects for this frame's events.
    this.hitFx.takeEvents(state);
    this.hitFx.update(this.fxHold ? 0 : Math.min(0.1, dtSec));
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
      // gfx W5: the shadow follows (a crate sliding; a tree burnt to a stump; a jar broken).
      const sh = e.shadow;
      if (sh && o.type === 'crate' && o.movedAt !== undefined && now - o.movedAt < 250) this.reshadow(sh, sprite.x, sprite.y, objectShadow('crate', sprite.width, sprite.height));
      if (o.type !== e.shadowType || !!o.gone !== e.shadowGone) {
        e.shadowType = o.type;
        e.shadowGone = !!o.gone;
        const g = objectShadow(o.type, Math.abs(sprite.width), sprite.height);
        const show = !o.gone && !!g && this.fxOn.shadows;
        if (sh) {
          sh.visible = show;
          if (g) this.reshadow(sh, sprite.x, sprite.y, g);
        }
        // on flat ground (in the shadow layer)
        const baked = this.bakedShadows.get(o);
        if (baked) {
          for (const b of baked) {
            b.sprite.visible = show;
            const [dx, dy] = this.decorShift(o);
            if (g) this.reshadow(b.sprite, o.tx * ts + ts / 2 + dx, o.ty * ts + ts + dy, g, 1);
          }
        }
      }
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
    this.updateEffects(state, timeSec, dtSec);
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
    this.glowLayer.scale.set(zoom);
    this.glowLayer.position.set(-o.x * zoom, -o.y * zoom);
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
      const sourceKey = e.final ? sourceFrameKey(e, timeSec, this.hasTexture, this.enemyFrameCounts) : null;
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
      const pulse = warningFlashAlpha(e, timeSec, windupProgress(e));
      const flash = pulse > 0 && this.fxV2 ? RIM_FLASH.alpha : pulse; // (gfx W5: the rim overlay)
      const overlay = placeFlash(spr, this.flashSprites.get(e.id) ?? null, flash, this.silhouettes, this.actors);
      if (overlay) this.flashSprites.set(e.id, overlay);
    }
    // P10.4: a core winding up its slam shows the shockwave's reach on the ground.
    if (!this.bossRing) {
      this.bossRing = new Graphics();
      this.actors.addChild(this.bossRing);
    }
    // (cleared and redrawn only while there is a ring to show, or once to take the last one away: a
    // Graphics changed every frame made PixiJS rebuild the whole world's draw list every frame)
    const slamming = (/** @type {any} */ e) => e.state === 'windup' && (e.boss ? e.pattern === 'slam' : e.kind === 'sentinel');
    const ringWanted = state.enemies.some(slamming);
    if (ringWanted || this.bossRingDrawn) this.bossRing.clear();
    this.bossRingDrawn = ringWanted;
    for (const e of ringWanted ? state.enemies : []) {
      // (v1.0: the sentinel's small slam shows its reach the same way.)
      if (!slamming(e)) continue;
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
    // (the same: only while the source is in the fight, or once after)
    const sourceUp = state.enemies.some((/** @type {any} */ x) => x.final && x.state !== 'dead');
    if (sourceUp || this.sourceDrawn) {
      this.sourceGround.clear();
      /** @type {Graphics} */ (this.sourceMarks).clear();
      drawSourceTelegraphs(this.sourceGround, state);
      drawSeatLights(/** @type {Graphics} */ (this.sourceMarks), state, timeSec);
    }
    this.sourceDrawn = sourceUp;
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
    // gfx W5: two after-images where the slash was the last two frames (fading out after it ends).
    const hist = this.slashHist;
    for (let k = 0; k < 2; k++) {
      const t = this.slashTrail[k];
      const j = k * 5;
      const on = hist[j + 4] === 1 && this.fxOn.hitfx && this.fxV2;
      t.visible = on; // (hidden between swings: not gathered when the world's draw list is rebuilt)
      if (on) {
        t.alpha = k === 0 ? 0.45 : 0.2;
        t.position.set(hist[j], hist[j + 1]);
        t.rotation = hist[j + 2];
        t.zIndex = hist[j + 3];
      }
    }
    hist.copyWithin(5, 0, 5);
    hist[0] = this.slash.x;
    hist[1] = this.slash.y;
    hist[2] = this.slash.rotation;
    hist[3] = this.slash.zIndex - 0.001;
    hist[4] = this.slash.visible ? 1 : 0;

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
    // (cleared only when there is something to take away: an emptied Graphics each frame made
    // PixiJS rebuild the world's whole draw list every frame)
    if (aiming || this.aimDrawn) this.aimLine.clear();
    this.aimDrawn = aiming;
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

