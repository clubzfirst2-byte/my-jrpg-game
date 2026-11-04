// @ts-check
// Draws the environment (P4): flames on burning tiles, ash, wet ground, electric sparks, and the
// changing environment objects (burnt trees become stumps, brambles / jars / doors disappear,
// receivers light up). Reads state only. Only tiles inside the view are drawn (pooled sprites).
import { Container } from 'pixi.js';

const ASH_TINT = 0x2a2018;
const WET_TINT = 0x2050a0;
const SPARK_TINT = 0xfff27a;
const FIRE_FPS = 8;
const MARGIN_TILES = 2;

export class EnvView {
  /**
   * @param {(key: string) => import('pixi.js').Sprite} makeSprite
   * @param {(key: string) => import('pixi.js').Texture} texture
   * @param {Container} groundLayer  under everything (for flat ground)
   * @param {Container} actors       Y-sorted layer
   * @param {import('../game/state.js').GameState} state
   */
  constructor(makeSprite, texture, groundLayer, actors, state) {
    this.makeSprite = makeSprite;
    this.texture = texture;
    this.actors = actors;
    this.ground = new Container();
    this.ground.label = 'env-ground';
    groundLayer.addChild(this.ground);
    /** @type {import('pixi.js').Sprite[]} */
    this.flat = []; // ash / wet / spark tiles on flat ground
    /** @type {import('pixi.js').Sprite[]} */
    this.raised = []; // the same on raised ground (sorted with the terrain rows)
    /** @type {import('pixi.js').Sprite[]} */
    this.flames = [];
    this.version = -1;
    void state;
  }

  /**
   * @param {import('../game/state.js').GameState} state
   * @param {{ x: number, y: number }} origin camera top-left (world px)
   * @param {number} viewW @param {number} viewH world px
   * @param {number} timeSec
   */
  update(state, origin, viewW, viewH, timeSec) {
    const env = state.env;
    const map = state.map;
    const ts = map.tileSize;
    const x0 = Math.floor(origin.x / ts) - MARGIN_TILES;
    const y0 = Math.floor(origin.y / ts) - MARGIN_TILES;
    const x1 = Math.ceil((origin.x + viewW) / ts) + MARGIN_TILES;
    const y1 = Math.ceil((origin.y + viewH) / ts) + MARGIN_TILES + 4; // raised ground draws higher up
    const inView = (/** @type {number} */ i) => {
      const tx = i % map.width;
      const ty = (i / map.width) | 0;
      return tx >= x0 && tx <= x1 && ty >= y0 && ty <= y1;
    };

    let nFlat = 0;
    let nRaised = 0;
    const tile = (/** @type {number} */ i, /** @type {number} */ tint, /** @type {number} */ alpha) => {
      const tx = i % map.width;
      const ty = (i / map.width) | 0;
      const h = map.elev[i];
      const pool = h > 0 ? this.raised : this.flat;
      const k = h > 0 ? nRaised++ : nFlat++;
      let s = pool[k];
      if (!s) {
        s = this.makeSprite('px');
        s.width = ts;
        s.height = ts;
        (h > 0 ? this.actors : this.ground).addChild(s);
        pool.push(s);
      }
      s.visible = true;
      s.tint = tint;
      s.alpha = alpha;
      s.position.set(tx * ts, ty * ts - h);
      s.zIndex = ty * ts + 0.002; // just above its terrain row
    };

    for (const [i, c] of env.cells) {
      if (!inView(i)) continue;
      if (c.ashUntil > env.now && !env.burning.has(i)) tile(i, ASH_TINT, 0.55);
      else if (c.wetUntil > env.now) tile(i, WET_TINT, 0.22);
    }
    if (env.sparks) {
      const flicker = Math.floor(timeSec * 30) % 2 === 0 ? 0.75 : 0.35;
      for (const i of env.sparks.cells) if (inView(i)) tile(i, SPARK_TINT, flicker);
    }
    for (let k = nFlat; k < this.flat.length; k++) this.flat[k].visible = false;
    for (let k = nRaised; k < this.raised.length; k++) this.raised[k].visible = false;

    // Flames.
    let nFire = 0;
    const frame = Math.floor(timeSec * FIRE_FPS);
    for (const i of env.burning) {
      if (!inView(i)) continue;
      let s = this.flames[nFire];
      if (!s) {
        s = this.makeSprite('fx.fire.0');
        this.actors.addChild(s);
        this.flames.push(s);
      }
      nFire++;
      const tx = i % map.width;
      const ty = (i / map.width) | 0;
      const o = env.objectAt.get(i);
      const big = !!o && !o.gone && o.type === 'tree';
      s.visible = true;
      s.texture = this.texture(`fx.fire.${(frame + i) % 2}`);
      s.scale.set(big ? 1.6 : 1);
      s.position.set(tx * ts + ts / 2, ty * ts + ts - 1 - map.elev[i] - (big ? 6 : 0));
      s.zIndex = ty * ts + ts + 0.5; // in front of the tree it burns
    }
    for (let k = nFire; k < this.flames.length; k++) this.flames[k].visible = false;
  }
}
