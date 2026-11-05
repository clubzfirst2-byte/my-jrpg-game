// @ts-check
// Villagers on screen (P9). Their art is in the plains bundle, so a villager is drawn only while
// that bundle is loaded and the villager is near the camera (P8 streaming); far away, no sprite.
import { lerp } from '../game/core/math.js';

const WALK_FPS = 6;
const WALK_CYCLE = [1, 0, 2, 0];
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
  }

  /**
   * @param {import('../game/state.js').GameState} state @param {number} alpha
   * @param {{ x: number, y: number }} center camera center (world px)
   */
  update(state, alpha, center) {
    const ready = this.assets.isLoaded('region:plains');
    for (const n of state.npcs) {
      const near = ready && Math.hypot(n.x - center.x, n.y - center.y) < NEAR_PX;
      let s = this.sprites.get(n.id);
      if (!near) {
        if (s) {
          s.destroy();
          this.sprites.delete(n.id);
        }
        continue;
      }
      const frame = n.moving ? WALK_CYCLE[Math.floor(n.walkTime * WALK_FPS) % WALK_CYCLE.length] : 0;
      const key = `npc.${n.look}.walk.${n.facing}.${frame}`;
      if (!s) {
        s = this.makeSprite(key);
        this.actors.addChild(s);
        this.sprites.set(n.id, s);
      }
      s.texture = this.assets.texture(key);
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
  }
}
