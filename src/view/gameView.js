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
import { windupProgress } from '../game/entities/enemies.js';
import { COMBAT } from '../game/entities/playerCombat.js';
import { areaAt } from '../game/world/features.js';
import { FeatureView } from './featureView.js';

const WALK_FPS = 8;
const WALK_CYCLE = [1, 0, 2, 0];
const WATER_FRAME_SEC = 0.6;
const EDGE_COLOR = 0x1a1c2c;
const TREE_FADE_ALPHA = 0.5;
const CLIFF_SHADOW_PX = 6;
const EDGE_PX = 2;
const GLIDER_SHOULDER_Y = 9;
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
    this.applyBounds(state);

    /** @type {Sprite[]} */
    this.waterSprites = [];
    this.waterFrame = -1;
    /** @type {Occluder[]} trees (faded when they hide the player) */
    this.trees = [];
    /** Per row: screen extents of elevated tiles, for silhouette checks. @type {Map<number, { x0: number, x1: number, y0: number, y1: number }[]>} */
    this.elevatedRows = new Map();

    this.buildTerrain();
    this.buildObjects();
    // Screen-space layer above the world (landmark markers).
    this.screenLayer = new Container();
    this.screenLayer.label = 'screen';
    app.stage.addChild(this.screenLayer);
    this.features = new FeatureView((key) => this.makeSprite(key), this.actors, this.screenLayer, state);

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
    /** @type {Map<number, Sprite>} */
    this.enemySprites = new Map();
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
    if (g === Ground.SAND) return 'tile.sand';
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
    // Swimming: head and shoulders above the water line, ripples alternate.
    const tex = p.swimming
      ? this.assets.texture(`player.swim.${p.facing}.${Math.floor(p.walkTime * (p.moving ? 6 : 2)) % 2}`)
      : this.assets.texture(`player.walk.${p.facing}.${frame}`);
    this.player.texture = tex;
    this.player.position.set(sx, sy);
    this.player.zIndex = y;
    // Glider canopy above the player's head; its cords end at the shoulders.
    this.glider.visible = p.gliding;
    if (p.gliding) {
      this.glider.position.set(sx, sy - GLIDER_SHOULDER_Y);
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
    if (this.applyBounds(state)) this.camera.snapTo(x, y - camZ - CAMERA_TARGET_OFFSET_Y);
    else this.camera.follow(x, y - camZ - CAMERA_TARGET_OFFSET_Y, dtSec);
    this.applyCamera();
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
    const id = area ? area.id : '';
    if (id === this.boundsArea) return false;
    this.boundsArea = id;
    const ts = this.map.tileSize;
    const r = area ?? state.outdoor ?? { tx: 0, ty: 0, tw: this.map.width, th: this.map.height };
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
    const cy = sy - 18;
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
    for (const e of state.enemies) {
      seen.add(e.id);
      let spr = this.enemySprites.get(e.id);
      if (!spr) {
        spr = this.makeSprite(`enemy.${e.kind}.0`);
        this.enemySprites.set(e.id, spr);
        this.actors.addChild(spr);
      }
      const ex = lerp(e.prevX, e.x, alpha);
      const ey = lerp(e.prevY, e.y, alpha);
      const moving = Math.hypot(e.x - e.prevX, e.y - e.prevY) > 0.01;
      spr.texture = this.assets.texture(`enemy.${e.kind}.${moving ? Math.floor(timeSec * 6) % 2 : 0}`);
      spr.position.set(Math.round(ex), Math.round(ey - e.z));
      spr.zIndex = ey;
      spr.scale.x = e.faceX < -0.2 ? -1 : 1;
      // Telegraph: the wind-up pulses red, faster as the attack nears. Stunned: pale blue.
      if (e.state === 'windup') {
        const k = windupProgress(e);
        spr.tint = Math.sin(timeSec * (12 + 24 * k)) > 0 ? 0xff7070 : 0xffffff;
      } else if (e.state === 'stun') spr.tint = 0xa8b8ff;
      else spr.tint = 0xffffff;
      spr.alpha = e.state === 'dead' ? Math.max(0, 1 - e.t / 600) : 1;
    }
    for (const [id, spr] of this.enemySprites) {
      if (!seen.has(id)) {
        spr.destroy();
        this.enemySprites.delete(id);
      }
    }

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
    this.shield.visible = !!p.guarding;
    if (p.guarding) {
      this.shield.position.set(Math.round(sx + p.aimX * 7), Math.round(sy - 7 + p.aimY * 4));
      this.shield.zIndex = p.aimY < 0 ? py - 0.01 : py + 0.01;
    }
    const aiming = p.action === 'aim';
    this.bow.visible = aiming;
    this.aimLine.clear();
    if (aiming) {
      const drawn = p.actionMs >= COMBAT.bowDrawMs;
      this.bow.position.set(Math.round(sx + p.aimX * 7), Math.round(sy - 8 + p.aimY * 4));
      this.bow.rotation = Math.atan2(p.aimY, p.aimX);
      this.bow.zIndex = p.aimY < 0 ? py - 0.01 : py + 0.01;
      // Dotted aim line, brighter once the draw is full.
      for (let d = 12; d < 64; d += 6) {
        this.aimLine.rect(Math.round(sx + p.aimX * d), Math.round(sy - 8 + p.aimY * d), 1, 1);
      }
      this.aimLine.fill({ color: drawn ? 0xfff2a0 : 0xffffff, alpha: drawn ? 0.9 : 0.4 });
    }

    // Hurt: blink while invulnerable. Dodge: a little transparent. Dead: lying faded.
    const blink = p.invulnMs > 0 && Math.floor(timeSec * 12) % 2 === 0;
    this.player.alpha = p.dead ? 0.5 : blink ? 0.3 : p.action === 'dodge' ? 0.7 : 1;
    this.player.rotation = p.dead ? Math.PI / 2 : 0;

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
