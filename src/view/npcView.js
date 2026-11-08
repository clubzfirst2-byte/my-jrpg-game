// @ts-check
// Villagers on screen (P9). Their art is in the plains bundle, so a villager is drawn only while
// that bundle is loaded and the villager is near the camera (P8 streaming); far away, no sprite.
import { lerp } from '../game/core/math.js';
import { npcFrameKey } from './npcAnim.js';

const NEAR_PX = 480;

export class NpcView {
  /**
   * @param {import('./assets/assetManager.js').AssetManager} assets
   * @param {(key: string) => import('pixi.js').Sprite} makeSprite
   * @param {import('pixi.js').Container} actors
   */
  constructor(assets, makeSprite, actors) {
    this.assets = assets;
    this.makeSprite = makeSprite;
    this.actors = actors;
    /** @type {Map<string, import('pixi.js').Sprite>} */
    this.sprites = new Map();
    /** The frame each villager shows (tests, ?debug). @type {Map<string, string>} */
    this.keys = new Map();
  }

  /**
   * @param {import('../game/state.js').GameState} state @param {number} alpha
   * @param {{ x: number, y: number }} center camera center (world px)
   * @param {number} [timeSec] real time (the release art's breathing loop)
   */
  update(state, alpha, center, timeSec = 0) {
    const ready = this.assets.isLoaded('region:plains');
    const has = (/** @type {string} */ key) => this.assets.hasTexture(key);
    for (const n of state.npcs) {
      const near = ready && Math.hypot(n.x - center.x, n.y - center.y) < NEAR_PX;
      let s = this.sprites.get(n.id);
      if (!near) {
        if (s) {
          s.destroy();
          this.sprites.delete(n.id);
          this.keys.delete(n.id);
        }
        continue;
      }
      const key = npcFrameKey(n, timeSec, has);
      if (!s) {
        s = this.makeSprite(key);
        this.actors.addChild(s);
        this.sprites.set(n.id, s);
      }
      s.texture = this.assets.texture(key);
      this.keys.set(n.id, key);
      const x = lerp(n.prevX, n.x, alpha);
      const y = lerp(n.prevY, n.y, alpha);
      s.position.set(Math.round(x), Math.round(y - n.z));
      s.zIndex = y;
    }
  }

  /** Drop every sprite (before the plains art is released). */
  clear() {
    for (const s of this.sprites.values()) s.destroy();
    this.sprites.clear();
    this.keys.clear();
  }

  /** What is on screen: each villager's frame, size in game px and draw order. */
  debug() {
    return [...this.sprites].map(([id, s]) => ({ id, key: this.keys.get(id), w: s.texture.width, h: s.texture.height, zIndex: s.zIndex, x: s.x, y: s.y }));
  }
}
