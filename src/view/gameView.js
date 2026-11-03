// @ts-check
// Draws the game state. Reads state only; never writes to it (DESIGN.md 1.1).
import { Container, Sprite } from 'pixi.js';
import { Ground } from '../game/world/tilemap.js';
import { lerp } from '../game/core/math.js';
import { cameraOrigin } from './camera.js';

const WALK_FPS = 8;
const WALK_CYCLE = [1, 0, 2, 0];
const WATER_FRAME_SEC = 0.6;

export class GameView {
  /**
   * @param {import('pixi.js').Application} app
   * @param {import('./assets/assetManager.js').AssetManager} assets
   * @param {import('../game/state.js').GameState} state
   */
  constructor(app, assets, state) {
    this.app = app;
    this.assets = assets;
    this.world = new Container();
    this.world.label = 'world';
    this.ground = new Container();
    this.ground.label = 'ground';
    // Y-sorted layer: objects and characters ordered by their feet (DESIGN.md 3.3).
    this.actors = new Container();
    this.actors.label = 'actors';
    this.actors.sortableChildren = true;
    this.world.addChild(this.ground, this.actors);
    app.stage.addChildAt(this.world, 0);

    /** @type {Sprite[]} */
    this.waterSprites = [];
    this.buildMap(state.map);

    this.player = this.makeSprite('player.walk.down.0');
    this.actors.addChild(this.player);
  }

  /** @param {string} key */
  makeSprite(key) {
    const s = new Sprite(this.assets.texture(key));
    const [ax, ay] = this.assets.meta(key).anchor;
    s.anchor.set(ax, ay);
    return s;
  }

  /** @param {import('../game/world/tilemap.js').TileMap} map */
  buildMap(map) {
    const ts = map.tileSize;
    for (let ty = 0; ty < map.height; ty++) {
      for (let tx = 0; tx < map.width; tx++) {
        const g = map.ground[ty * map.width + tx];
        let key = 'tile.path';
        if (g === Ground.GRASS) key = `tile.grass.${hash(tx, ty) % 3}`;
        else if (g === Ground.WATER) key = 'tile.water.0';
        const s = this.makeSprite(key);
        s.position.set(tx * ts, ty * ts);
        this.ground.addChild(s);
        if (g === Ground.WATER) this.waterSprites.push(s);
      }
    }
    for (const o of map.objects) {
      const s = this.makeSprite(o.type === 'tree' ? 'obj.tree' : 'obj.rock');
      const x = o.tx * ts + ts / 2;
      const y = o.ty * ts + ts;
      s.position.set(x, y);
      s.zIndex = y;
      this.actors.addChild(s);
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

    const frame = p.moving ? WALK_CYCLE[Math.floor(p.walkTime * WALK_FPS) % WALK_CYCLE.length] : 0;
    this.player.texture = this.assets.texture(`player.walk.${p.facing}.${frame}`);
    this.player.position.set(Math.round(x), Math.round(y));
    this.player.zIndex = y;

    const waterKey = `tile.water.${Math.floor(timeSec / WATER_FRAME_SEC) % 2}`;
    const waterTex = this.assets.texture(waterKey);
    if (this.waterSprites[0] && this.waterSprites[0].texture !== waterTex) {
      for (const s of this.waterSprites) s.texture = waterTex;
    }

    const map = state.map;
    const cam = cameraOrigin(
      x,
      y - 8, // center on the body, not the feet
      this.app.screen.width,
      this.app.screen.height,
      map.width * map.tileSize,
      map.height * map.tileSize,
    );
    this.world.position.set(-cam.x, -cam.y);
  }
}

/** Stable per-tile variation. @param {number} x @param {number} y */
function hash(x, y) {
  let h = (x * 374761393 + y * 668265263) >>> 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177) >>> 0;
  return (h ^ (h >>> 16)) >>> 0;
}
