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
  star_shard: 'icon.star_shard', // v1.0: the key items' own icons
  lost_charm: 'icon.charm',
  // v1.0.1: weapons and armour that borrowed another icon (tools/object_release/icons_v1_1.py ITEM_ICONS)
  guard_spear: 'icon.spear',
  rusty_greatsword: 'icon.greatsword',
  ember_sword: 'icon.ember_sword',
  star_steel_sword: 'icon.star_sword',
  insulated_cap: 'icon.cap',
  grip_boots: 'icon.boots',
  // v1.0.1: one icon per dish (icon.food stays the fallback of the food type)
  ...Object.fromEntries(['grilled_meat', 'mushroom_skewer', 'berry_jam', 'hunter_stew', 'ember_soup', 'hearty_skewer', 'mixed_stew', 'dubious_food'].map((id) => [id, `icon.dish.${id}`])),
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
