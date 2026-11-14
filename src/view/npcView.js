// @ts-check
// Villagers on screen (P9). A villager is drawn while the art of its frame is loaded and it is near
// the camera (P8 streaming); far away, no sprite. The village's placeholder looks are in the plains
// bundle; release art and the princess's placeholder (she stands by record stones in every region,
// v1.0) are in the base bundle. Villagers who leave (their appearance condition, v1.0) lose their
// sprite; a ghost (the princess's 写し身) is see-through.
// Graphics v3 (assets/npcV3.js): a person with v3 art is drawn from its own bundle ("v3:npc:<who>"), and
// not at all until that is in; a left frame may be the right one mirrored (setFrame).
import { lerp } from '../game/core/math.js';
import { npcAlpha } from '../game/npc/npcs.js';
import { npcFrameKey } from './npcAnim.js';
import { setFrame } from './spriteFrame.js';

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
    /** The ids there this frame (reused: no garbage per frame). @type {Set<string>} */
    this.present = new Set();
    /** Graphics v3: the people (art names) drawn from bundles of their own (gameView sets it). @type {Set<string>} */
    this.own = new Set();
    this.hasKey = (/** @type {string} */ key) => this.assets.hasTexture(key);
    this.isOwn = (/** @type {string} */ art) => this.own.has(art);
    /** Graphics v3: the people whose left frames are their right frames mirrored (gameView sets it). @type {Set<string>} */
    this.mirrorLeft = new Set();
    this.isMirrorLeft = (/** @type {string} */ art) => this.mirrorLeft.has(art);
  }

  /**
   * @param {import('../game/state.js').GameState} state @param {number} alpha
   * @param {{ x: number, y: number }} center camera center (world px)
   * @param {number} [timeSec] real time (the release art's breathing loop)
   */
  update(state, alpha, center, timeSec = 0) {
    const has = this.hasKey;
    // Someone who left (v1.0 appearance conditions): no sprite.
    this.present.clear();
    for (const n of state.npcs) this.present.add(n.id);
    for (const id of this.sprites.keys()) if (!this.present.has(id)) this.drop(id); // (deleting while iterating a Map is safe)
    for (const n of state.npcs) {
      const near = Math.hypot(n.x - center.x, n.y - center.y) < NEAR_PX;
      const key = near ? npcFrameKey(n, timeSec, has, this.isOwn, this.isMirrorLeft) : null;
      let s = this.sprites.get(n.id);
      if (!key || !has(key)) {
        if (s) this.drop(n.id);
        continue;
      }
      if (!s) {
        s = this.makeSprite(key);
        this.actors.addChild(s);
        this.sprites.set(n.id, s);
      }
      setFrame(s, this.assets, key); // (graphics v3: a left frame may be its right frame mirrored)
      s.alpha = npcAlpha(state, n);
      this.keys.set(n.id, key);
      const x = lerp(n.prevX, n.x, alpha);
      const y = lerp(n.prevY, n.y, alpha);
      s.position.set(Math.round(x), Math.round(y - n.z));
      s.zIndex = y;
    }
  }

  /** @param {string} id */
  drop(id) {
    this.sprites.get(id)?.destroy();
    this.sprites.delete(id);
    this.keys.delete(id);
  }

  /** Graphics v3: drops the sprites showing one person's frames, before that person's bundle goes. @param {string} who art name */
  dropArt(who) {
    for (const [id, key] of this.keys) if (key.startsWith(`npc.${who}.`)) this.drop(id);
  }

  /** Drop every sprite (before the plains art is released). */
  clear() {
    for (const s of this.sprites.values()) s.destroy();
    this.sprites.clear();
    this.keys.clear();
  }

  /** What is on screen: each villager's frame, size in game px and draw order. */
  debug() {
    // (graphics v3: density = the drawn texture's art px per game px; mirrored = a left frame drawn from its right frame;
    // frame = the texture's place on its atlas, game px)
    return [...this.sprites].map(([id, s]) => ({ id, key: this.keys.get(id), w: s.texture.width, h: s.texture.height, zIndex: s.zIndex, x: s.x, y: s.y, alpha: s.alpha, anchor: [s.anchor.x, s.anchor.y], density: s.texture.source.resolution, mirrored: s.scale.x < 0, frame: [s.texture.frame.x, s.texture.frame.y, s.texture.frame.width, s.texture.frame.height] }));
  }
}
