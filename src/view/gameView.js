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
import { Container, Graphics, Sprite } from 'pixi.js';
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
import { WeatherView } from './weatherView.js';
import { ItemView } from './itemView.js';
import { PuzzleView } from './puzzleView.js';
import { NpcView } from './npcView.js';
import { regionAt, outdoorAt } from '../game/world/world.js';
import { seasonAt } from '../game/env/weather.js';
import { SEASON_ENTRIES, seasonKeys, SOURCE_BUNDLE, SOURCE_REGIONS } from './assets/placeholderPack.js';
import { HeroAnimator } from './heroAnim.js';
import { enemyFrameKey, warningFlashAlpha, defeatAlpha } from './enemyAnim.js';
import { SilhouetteCache, placeFlash } from './flashOverlay.js';
import { EnemySlots } from './enemySlots.js';

/** Chunk size in tiles (P8). */
export const CHUNK = 32;

/**
 * @typedef {import('../game/world/world.js').RegionInfo} RegionInfo
 * @typedef {{ cx: number, cy: number, base: Container, rows: Map<number, Container>, water: Sprite[],
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
 * @param {number} heightPx
 */
export function levelTint(heightPx) {
  const level = heightPx / LEVEL_PX;
  const v = Math.round(255 * Math.min(1, 0.8 + 0.07 * level));
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
    /** Bundles being loaded (async). @type {Set<string>} */
    this.bundlesLoading = new Set();
    /** Bundles loaded ahead of their chunks (one reference held here). @type {Set<string>} */
    this.preloaded = new Set();
    /** Load every chunk at once (?chunks=all: for comparing against streaming). */
    this.loadAll = false;
    this.chunkStats = { built: 0, freed: 0, pending: 0, updates: 0 };
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
    this.weather.attach(app.stage, app.stage.getChildIndex(this.world) + 1);
    // v1.0: attack warnings (the wind-up overlay, the slam rings) are drawn ABOVE the light map, so
    // night and dark rooms do not dim them: a world-space layer that follows the world's camera
    // transform (applyCamera), just over the light map and under the rain.
    this.warnLayer = new Container();
    this.warnLayer.label = 'warnings';
    app.stage.addChildAt(this.warnLayer, app.stage.getChildIndex(this.weather.overlay) + 1);

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
    this.envVersion = -1;
  }

  /** @param {number} tx @param {number} ty */
  surfaceKey(tx, ty) {
    const g = this.map.ground[ty * this.map.width + tx];
    // P8: each region dresses the same ground in its own art (its asset bundle).
    const region = regionAt(this.regions, tx, ty);
    if (region?.id === 'desert' && g === Ground.SAND) return `desert.sand.${hash(tx, ty) % 3}`;
    if (region?.id === 'plains' && g === Ground.GRASS) return `plains.grass.${hash(tx, ty) % 4}`;
    // P10.3: the east column.
    if (region?.id === 'forest' && g === Ground.GRASS) return `forest.grass.${hash(tx, ty) % 4}`;
    if (region?.id === 'mountains' && g === Ground.GRASS) return `mountains.snow.${hash(tx, ty) % 4}`;
    if (region?.id === 'lake' && g === Ground.GRASS) return `lake.grass.${hash(tx, ty) % 4}`;
    if (g === Ground.WOOD) return 'tile.wood';
    if (g === Ground.WALL) return 'tile.walltop';
    if (g === Ground.DARK) return 'tile.dark';
    if (g === Ground.PATH) return 'tile.path';
    if (g === Ground.WATER) return 'tile.water.0';
    if (g === Ground.RUIN) return 'tile.ruin';
    if (g === Ground.SAND) return 'tile.sand';
    if (g === Ground.METAL) return 'tile.metal';
    if (g === Ground.PIT) return 'tile.pit';
    return `tile.grass.${hash(tx, ty) % 3}`;
  }

  /** @param {number} cx @param {number} cy */
  chunkKey(cx, cy) {
    return `${cx},${cy}`;
  }

  /** Bundles a chunk's art needs (its regions', and the season's). @param {number} cx @param {number} cy @returns {string[]} */
  chunkBundles(cx, cy) {
    const x0 = cx * CHUNK;
    const y0 = cy * CHUNK;
    const list = this.regions
      .filter((r) => r.bundle && r.tx < x0 + CHUNK && r.tx + r.tw > x0 && r.ty < y0 + CHUNK && r.ty + r.th > y0)
      .map((r) => /** @type {string} */ (r.bundle));
    // P10.2: and the season's look.
    return this.seasonBundle ? [...list, this.seasonBundle] : list;
  }

  /**
   * Builds the terrain and objects of one chunk (CHUNK x CHUNK tiles). Flat ground goes into one
   * cached texture per chunk; raised rows are Y-sorted with the actors as before (DESIGN.md 3.3).
   * @param {number} cx @param {number} cy
   * @returns {Chunk}
   */
  buildChunk(cx, cy) {
    const map = this.map;
    const ts = map.tileSize;
    const base = new Container();
    base.label = `chunk-${cx},${cy}`;
    /** @type {Sprite[]} */
    const water = [];
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
    for (let ty = cy * CHUNK; ty < y1; ty++) {
      for (let tx = cx * CHUNK; tx < x1; tx++) {
        const i = ty * map.width + tx;
        const h = map.elev[i];
        const isRamp = map.shape[i] === Shape.RAMP_N;
        const x = tx * ts;

        if (h === 0 && !isRamp) {
          const s = this.makeSprite(this.surfaceKey(tx, ty));
          s.position.set(x, ty * ts);
          base.addChild(s);
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
        surface.tint = levelTint(isRamp ? h - LEVEL_PX / 2 : h);
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
    base.tint = levelTint(0);
    this.base.addChild(base);
    // A chunk's flat ground -> one textured quad per frame.
    base.cacheAsTexture({ scaleMode: 'nearest', antialias: false });

    // Objects standing in this chunk now.
    for (const o of map.objects) {
      if (o.tx < cx * CHUNK || o.tx >= x1 || o.ty < cy * CHUNK || o.ty >= y1 || this.objectSprites.has(o)) continue;
      this.addObjectSprite(o);
    }
    this.chunkStats.built++;
    return { cx, cy, base, rows, water, extents, bundles: this.chunkBundles(cx, cy) };
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
    const ts = this.map.tileSize;
    const size = CHUNK * ts;
    const ncx = Math.ceil(this.map.width / CHUNK);
    const ncy = Math.ceil(this.map.height / CHUNK);
    const range = (/** @type {number} */ margin) => ({
      x0: this.loadAll ? 0 : Math.max(0, Math.floor((origin.x - margin) / size)),
      x1: this.loadAll ? ncx - 1 : Math.min(ncx - 1, Math.floor((origin.x + viewW + margin) / size)),
      y0: this.loadAll ? 0 : Math.max(0, Math.floor((origin.y - margin) / size)),
      y1: this.loadAll ? ncy - 1 : Math.min(ncy - 1, Math.floor((origin.y + viewH + margin + 64) / size)),
    });
    const want = range(ts * 4); // a little beyond the screen (raised ground draws up to 4 tiles higher)
    const keep = range(size); // hysteresis: freed only once well out of view
    this.chunkStats.updates++;
    let pending = 0;
    for (let cy = want.y0; cy <= want.y1; cy++) {
      for (let cx = want.x0; cx <= want.x1; cx++) {
        const key = this.chunkKey(cx, cy);
        if (this.chunks.has(key)) continue;
        const bundles = this.chunkBundles(cx, cy);
        const missing = bundles.filter((b) => !this.assets.isLoaded(b));
        if (missing.length > 0) {
          for (const b of missing) this.requestBundle(b);
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
      }
    }
    // A bundle loaded for chunks that were left behind before being built: let it go.
    for (const b of this.preloaded) {
      const used = [...this.chunks.values()].some((c) => c.bundles.includes(b));
      if (used) {
        this.assets.unload(b); // the chunks hold their own references now
        this.preloaded.delete(b);
      } else if (!this.bundlesLoading.has(b)) {
        const stillWanted = this.regions.some((r) => r.bundle === b && this.regionNear(r, origin, viewW, viewH));
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
    const mountains = regionAt(this.regions, tx, ty)?.id === 'mountains';
    const mat = g === Ground.RUIN ? 'ruin' : g === Ground.WALL ? 'wall' : mountains ? 'stone' : 'earth';
    let y = faceTop;
    let first = true;
    while (remaining > 0) {
      const seg = remaining >= 8 ? 8 : 4;
      const last = remaining - seg <= 0;
      const s = this.makeSprite(`face.${mat}.${first ? 'top' : 'mid'}${last ? '-base' : ''}.${seg}`);
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
    const x = o.tx * ts + ts / 2;
    const feetY = o.ty * ts + ts;
    const z = map.elev[o.ty * map.width + o.tx];
    s.position.set(x, feetY - z);
    // The door mat lies flat on the floor: under anyone standing on it.
    s.zIndex = o.type === 'mat' || o.type === 'stairs' ? feetY - ts : feetY;
    s.visible = !o.gone;
    this.actors.addChild(s);
    /** @type {Occluder | null} */
    let occluder = null;
    if (o.type === 'tree') {
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
    const ringOpen = !!state.progress.flags.source_open && !state.progress.flags.source_purified;
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
    this.warnLayer.scale.set(zoom);
    this.warnLayer.position.set(-o.x * zoom, -o.y * zoom);
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
      const overlay = placeFlash(spr, this.flashSprites.get(e.id) ?? null, flash, this.silhouettes, this.warnLayer);
      if (overlay) this.flashSprites.set(e.id, overlay);
    }
    // P10.4: a core winding up its slam shows the shockwave's reach on the ground.
    if (!this.bossRing) {
      this.bossRing = new Graphics();
      this.warnLayer.addChild(this.bossRing); // (above the light map, like the overlay)
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
    this.player.rotation = p.dead && held !== 'down' ? Math.PI / 2 : 0;

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
    const frame = Math.floor(timeSec / WATER_FRAME_SEC) % 2;
    if (frame === this.waterFrame) return;
    this.waterFrame = frame;
    const tex = this.assets.texture(`tile.water.${frame}`);
    for (const c of this.chunks.values()) {
      if (c.water.length === 0) continue;
      for (const s of c.water) s.texture = tex;
      c.base.updateCacheTexture();
    }
  }
}

/** Stable per-tile variation. @param {number} x @param {number} y */
function hash(x, y) {
  let h = (x * 374761393 + y * 668265263) >>> 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177) >>> 0;
  return (h ^ (h >>> 16)) >>> 0;
}
