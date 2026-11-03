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
import { Container, Sprite } from 'pixi.js';
import { Ground, Shape, LEVEL_PX, inBounds, northEdgeHeight, southEdgeHeight } from '../game/world/tilemap.js';
import { lerp } from '../game/core/math.js';
import { cameraOrigin } from './camera.js';

const WALK_FPS = 8;
const WALK_CYCLE = [1, 0, 2, 0];
const WATER_FRAME_SEC = 0.6;
const EDGE_COLOR = 0x1a1c2c;
const TREE_FADE_ALPHA = 0.5;
const CLIFF_SHADOW_PX = 6;
const EDGE_PX = 2;
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

    /** @type {Sprite[]} */
    this.waterSprites = [];
    this.waterFrame = -1;
    /** @type {Occluder[]} trees (faded when they hide the player) */
    this.trees = [];
    /** Per row: screen extents of elevated tiles, for silhouette checks. @type {Map<number, { x0: number, x1: number, y0: number, y1: number }[]>} */
    this.elevatedRows = new Map();

    this.buildTerrain();
    this.buildObjects();

    this.shadow = this.makeSprite('fx.shadow');
    this.shadow.alpha = 0.35;
    this.player = this.makeSprite('player.walk.down.0');
    this.silhouette = this.makeSprite('player.walk.down.0');
    this.silhouette.tint = 0x101828;
    this.silhouette.alpha = 0.55;
    this.silhouette.visible = false;
    this.actors.addChild(this.shadow, this.player);
    this.overlay.addChild(this.silhouette);
    /** True while the player is hidden behind terrain (exposed for tests). */
    this.playerOccluded = false;
  }

  /** @param {string} key */
  makeSprite(key) {
    const s = new Sprite(this.assets.texture(key));
    const [ax, ay] = this.assets.meta(key).anchor;
    s.anchor.set(ax, ay);
    return s;
  }

  /** @param {number} tx @param {number} ty */
  surfaceKey(tx, ty) {
    const g = this.map.ground[ty * this.map.width + tx];
    if (g === Ground.PATH) return 'tile.path';
    if (g === Ground.WATER) return 'tile.water.0';
    if (g === Ground.RUIN) return 'tile.ruin';
    return `tile.grass.${hash(tx, ty) % 3}`;
  }

  buildTerrain() {
    const map = this.map;
    const ts = map.tileSize;
    /** @type {Map<number, Container>} */
    const rows = new Map();
    const rowContainer = (/** @type {number} */ ty) => {
      let c = rows.get(ty);
      if (!c) {
        c = new Container();
        c.label = `terrain-row-${ty}`;
        c.zIndex = ty * ts + 0.001; // north edge of the row (see header comment)
        rows.set(ty, c);
        this.actors.addChild(c);
      }
      return c;
    };

    for (let ty = 0; ty < map.height; ty++) {
      for (let tx = 0; tx < map.width; tx++) {
        const i = ty * map.width + tx;
        const h = map.elev[i];
        const isRamp = map.shape[i] === Shape.RAMP_N;
        const x = tx * ts;

        if (h === 0 && !isRamp) {
          const s = this.makeSprite(this.surfaceKey(tx, ty));
          s.position.set(x, ty * ts);
          this.base.addChild(s);
          if (map.ground[i] === Ground.WATER) this.waterSprites.push(s);
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

        const extents = this.elevatedRows.get(ty) ?? [];
        extents.push({ x0: x, x1: x + ts, y0: top, y1: Math.max(faceBottom, faceTop) });
        this.elevatedRows.set(ty, extents);
      }
    }
    this.base.tint = levelTint(0);
    // ~1500 static tiles -> one textured quad per frame.
    this.base.cacheAsTexture({ scaleMode: 'nearest', antialias: false });
  }

  /**
   * @param {Container} row @param {number} tx @param {number} ty
   * @param {number} x @param {number} faceTop @param {number} faceBottom
   */
  addFace(row, tx, ty, x, faceTop, faceBottom) {
    let remaining = faceBottom - faceTop;
    if (remaining <= 0) return;
    const mat = this.map.ground[ty * this.map.width + tx] === Ground.RUIN ? 'ruin' : 'earth';
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

  buildObjects() {
    const map = this.map;
    const ts = map.tileSize;
    for (const o of map.objects) {
      const s = this.makeSprite(o.type === 'tree' ? 'obj.tree' : 'obj.rock');
      const x = o.tx * ts + ts / 2;
      const feetY = o.ty * ts + ts;
      const z = map.elev[o.ty * map.width + o.tx];
      s.position.set(x, feetY - z);
      s.zIndex = feetY;
      this.actors.addChild(s);
      if (o.type === 'tree') {
        const w = s.width / 2;
        this.trees.push({ sprite: s, x0: x - w, x1: x + w, y0: feetY - z - s.height, y1: feetY - z, key: feetY });
      }
    }
  }

  /**
   * @param {import('../game/state.js').GameState} state
   * @param {number} alpha interpolation factor from the fixed-step loop
   * @param {number} timeSec real time, for purely visual animation
   */
  render(state, alpha, timeSec) {
    const p = state.player;
    const x = lerp(p.prevX, p.x, alpha);
    const y = lerp(p.prevY, p.y, alpha);
    const z = lerp(p.prevZ, p.z, alpha);
    const sx = Math.round(x);
    const sy = Math.round(y - z);

    const frame = p.moving ? WALK_CYCLE[Math.floor(p.walkTime * WALK_FPS) % WALK_CYCLE.length] : !p.grounded ? 1 : 0;
    const tex = this.assets.texture(`player.walk.${p.facing}.${frame}`);
    this.player.texture = tex;
    this.player.position.set(sx, sy);
    this.player.zIndex = y;

    // Shadow on the ground below; smaller and fainter the higher the player is.
    const above = Math.max(0, z - p.groundZ);
    const k = Math.max(0.45, 1 - above / 96);
    this.shadow.position.set(sx, Math.round(y - p.groundZ) - 1);
    this.shadow.scale.set(k);
    this.shadow.alpha = 0.35 * k;
    this.shadow.zIndex = y - 0.002;

    this.updateOcclusion(sx, sy, y, tex);
    this.animateWater(timeSec);

    const map = this.map;
    const cam = cameraOrigin(x, y - z - 8, this.app.screen.width, this.app.screen.height, map.width * map.tileSize, map.height * map.tileSize);
    this.world.position.set(-cam.x, -cam.y);
  }

  /**
   * Fades trees in front of the player; shows a silhouette when terrain hides the player.
   * @param {number} sx @param {number} sy @param {number} key @param {import('pixi.js').Texture} tex
   */
  updateOcclusion(sx, sy, key, tex) {
    const px0 = sx - 6;
    const px1 = sx + 6;
    const py0 = sy - 15;
    const py1 = sy - 1;
    for (const t of this.trees) {
      const hides = t.key > key && px1 > t.x0 && px0 < t.x1 && py1 > t.y0 && py0 < t.y1;
      t.sprite.alpha = hides ? TREE_FADE_ALPHA : 1;
    }
    let occluded = false;
    const ts = this.map.tileSize;
    const firstRow = Math.floor(key / ts);
    for (let r = firstRow; r < firstRow + 6 && !occluded; r++) {
      const tiles = this.elevatedRows.get(r);
      if (!tiles || r * ts + 0.001 <= key) continue; // rows drawn before the player can't hide it
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

  /** @param {number} timeSec */
  animateWater(timeSec) {
    if (this.waterSprites.length === 0) return;
    const frame = Math.floor(timeSec / WATER_FRAME_SEC) % 2;
    if (frame === this.waterFrame) return;
    this.waterFrame = frame;
    const tex = this.assets.texture(`tile.water.${frame}`);
    for (const s of this.waterSprites) s.texture = tex;
    this.base.updateCacheTexture();
  }
}

/** Stable per-tile variation. @param {number} x @param {number} y */
function hash(x, y) {
  let h = (x * 374761393 + y * 668265263) >>> 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177) >>> 0;
  return (h ^ (h >>> 16)) >>> 0;
}
