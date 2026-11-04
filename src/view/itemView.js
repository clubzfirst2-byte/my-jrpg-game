// @ts-check
// Items lying in the world (P6): a small icon that bobs, sorted with the actors. Reads state only.
import { itemDef } from '../game/items/inventory.js';

const ICON_BY_ID = /** @type {Record<string, string>} */ ({
  mushroom: 'icon.mushroom',
  red_berry: 'icon.berry',
  swift_herb: 'icon.herb',
  ember_pepper: 'icon.pepper',
  beast_meat: 'icon.meat',
  beast_fang: 'icon.fang',
  murk_crystal: 'icon.shard',
  arrow: 'icon.arrows',
});
const ICON_BY_TYPE = /** @type {Record<string, string>} */ ({ weapon: 'icon.sword', bow: 'icon.bow', armor: 'icon.armor', food: 'icon.food', material: 'icon.berry', ammo: 'icon.arrows' });

/** Sprite key for an item. @param {string} id */
export function iconFor(id) {
  const base = id.split(':')[0];
  return ICON_BY_ID[base] ?? ICON_BY_TYPE[itemDef(base).type] ?? 'icon.food';
}

export class ItemView {
  /** @param {(key: string) => import('pixi.js').Sprite} makeSprite @param {import('pixi.js').Container} actors */
  constructor(makeSprite, actors) {
    this.makeSprite = makeSprite;
    this.actors = actors;
    /** @type {Map<string, import('pixi.js').Sprite>} */
    this.sprites = new Map();
  }

  /** @param {import('../game/state.js').GameState} state @param {number} timeSec */
  update(state, timeSec) {
    const seen = new Set();
    for (const p of state.pickups) {
      seen.add(p.key);
      let s = this.sprites.get(p.key);
      if (!s) {
        s = this.makeSprite(iconFor(p.item));
        this.actors.addChild(s);
        this.sprites.set(p.key, s);
      }
      const bob = Math.round(Math.sin(timeSec * 3 + p.x * 0.1) * 1.5);
      s.position.set(Math.round(p.x), Math.round(p.y - p.z) - 1 + bob);
      s.zIndex = p.y - 0.5;
    }
    for (const [key, s] of this.sprites) {
      if (seen.has(key)) continue;
      s.destroy();
      this.sprites.delete(key);
    }
  }
}
