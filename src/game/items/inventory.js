// @ts-check
// Items and equipment (P6, DESIGN.md 5.6): inventory, weapons / bows with durability, armor with
// defense and traits, eating, cooking (recipes are discovered by cooking them), and the forge
// (upgrade and repair). All item numbers live in data/items.json. Pure logic.
import DATA from '../../../data/items.json';

/** @typedef {{ id: string, dur: number, lvl: number }} Gear */
/**
 * @typedef {object} Inventory  saved with the progress
 * @property {number} money
 * @property {Record<string, number>} items   stackable items (ammo, materials, food, armor) by id
 * @property {Gear[]} weapons
 * @property {Gear[]} bows
 * @property {{ weapon: number, bow: number, head: string | null, body: string | null, legs: string | null }} equip
 *   weapon / bow: index into the lists (-1 = none); armor: item id (owned in `items`)
 * @property {string[]} recipes  discovered dish ids
 */

export const ITEMS = DATA;
/** @type {Map<string, any>} */
const BY_ID = new Map(DATA.items.map((/** @type {any} */ it) => [it.id, it]));

/** @param {string} id */
export function itemDef(id) {
  const it = BY_ID.get(id);
  if (!it) throw new Error(`Unknown item "${id}"`);
  return it;
}

/** @param {string} id @returns {Gear} */
function newGear(id) {
  return { id, dur: itemDef(id).durability, lvl: 0 };
}

/** The starting kit. @returns {Inventory} */
export function createInventory() {
  const s = DATA.start;
  return {
    money: s.money,
    items: { ...s.items },
    weapons: s.weapons.map(newGear),
    bows: s.bows.map(newGear),
    equip: { weapon: s.weapons.length > 0 ? 0 : -1, bow: s.bows.length > 0 ? 0 : -1, head: null, body: null, legs: null },
    recipes: [],
  };
}

/** @param {Inventory} inv @param {string} id */
export const countOf = (inv, id) => inv.items[id] ?? 0;

/**
 * Adds items. Returns how many were actually taken (limits: weapon / bow slots, stack size).
 * @param {Inventory} inv @param {string} id @param {number} [n]
 */
export function addItem(inv, id, n = 1) {
  const def = itemDef(id);
  if (def.type === 'weapon' || def.type === 'bow') {
    const list = def.type === 'weapon' ? inv.weapons : inv.bows;
    const max = def.type === 'weapon' ? DATA.limits.weapons : DATA.limits.bows;
    let taken = 0;
    while (taken < n && list.length < max) {
      list.push(newGear(id));
      if (def.type === 'weapon' && inv.equip.weapon < 0) inv.equip.weapon = list.length - 1;
      if (def.type === 'bow' && inv.equip.bow < 0) inv.equip.bow = list.length - 1;
      taken++;
    }
    return taken;
  }
  const have = countOf(inv, id);
  const taken = Math.max(0, Math.min(n, DATA.limits.stack - have));
  if (taken > 0) inv.items[id] = have + taken;
  return taken;
}

/** @param {Inventory} inv @param {string} id @param {number} [n] @returns {boolean} */
export function removeItem(inv, id, n = 1) {
  const have = countOf(inv, id);
  if (have < n) return false;
  if (have === n) delete inv.items[id];
  else inv.items[id] = have - n;
  // Armor that is no longer owned comes off.
  for (const slot of /** @type {const} */ (['head', 'body', 'legs'])) if (inv.equip[slot] === id && countOf(inv, id) === 0) inv.equip[slot] = null;
  return true;
}

/** @param {Inventory} inv @param {'weapon' | 'bow'} kind @param {number} index */
export function equipGear(inv, kind, index) {
  const list = kind === 'weapon' ? inv.weapons : inv.bows;
  if (index < -1 || index >= list.length) return false;
  inv.equip[kind] = index;
  return true;
}

/** @param {Inventory} inv @param {string} id armor id (owned) */
export function equipArmor(inv, id) {
  const def = itemDef(id);
  if (def.type !== 'armor' || countOf(inv, id) === 0) return false;
  const slot = /** @type {'head' | 'body' | 'legs'} */ (def.slot);
  inv.equip[slot] = inv.equip[slot] === id ? null : id; // equipping the worn piece takes it off
  return true;
}

/** @param {Inventory} inv */
export function equippedWeapon(inv) {
  return inv.equip.weapon >= 0 ? inv.weapons[inv.equip.weapon] ?? null : null;
}
/** @param {Inventory} inv */
export function equippedBow(inv) {
  return inv.equip.bow >= 0 ? inv.bows[inv.equip.bow] ?? null : null;
}

/**
 * Sword stats of what is in hand (bare fists when nothing is).
 * @param {Inventory} inv
 * @returns {{ damage: number, reach: number, speed: number, element: string | null, name: string }}
 */
export function weaponStats(inv) {
  const g = equippedWeapon(inv);
  if (!g) return { ...DATA.fists, element: null, name: '素手' };
  const d = itemDef(g.id);
  return { damage: d.damage * (1 + DATA.forge.damagePerLevel * g.lvl), reach: d.reach, speed: d.speed, element: d.element ?? null, name: d.name };
}

/** @param {Inventory} inv */
export function bowStats(inv) {
  const g = equippedBow(inv);
  return g ? { damage: itemDef(g.id).damage, name: itemDef(g.id).name } : null;
}

/**
 * Wears down the gear in hand. Returns the broken item's name when it breaks (it is removed).
 * @param {Inventory} inv @param {'weapon' | 'bow'} kind
 * @returns {string | null}
 */
export function wearGear(inv, kind) {
  const list = kind === 'weapon' ? inv.weapons : inv.bows;
  const i = inv.equip[kind];
  const g = i >= 0 ? list[i] : null;
  if (!g) return null;
  g.dur -= 1;
  if (g.dur > 0) return null;
  list.splice(i, 1);
  inv.equip[kind] = list.length > 0 ? 0 : -1; // the next one comes to hand
  return itemDef(g.id).name;
}

/** Total defense and traits of the worn armor. @param {Inventory} inv */
export function armorStats(inv) {
  let defense = 0;
  /** @type {Set<string>} */
  const traits = new Set();
  for (const slot of /** @type {const} */ (['head', 'body', 'legs'])) {
    const id = inv.equip[slot];
    if (!id) continue;
    const d = itemDef(id);
    defense += d.defense;
    if (d.trait) traits.add(d.trait);
  }
  return { defense, traits };
}

/**
 * Damage after armor and buffs (quarter hearts). Never below 1 for a real hit.
 * @param {Inventory} inv @param {number} damage @param {boolean} defenseUp
 */
export function reduceDamage(inv, damage, defenseUp) {
  const { defense } = armorStats(inv);
  const cut = Math.floor(defense / 2) + (defenseUp ? 1 : 0);
  return Math.max(1, damage - cut);
}

/**
 * Eats a material or dish: heals and may start an effect.
 * @param {Inventory} inv @param {string} id @param {any} player @param {number} now world ms
 * @returns {{ heal: number, effect: string | null } | null}
 */
export function eat(inv, id, player, now) {
  const def = itemDef(id);
  if ((def.type !== 'food' && def.type !== 'material') || def.heal === undefined) return null;
  if (!removeItem(inv, id)) return null;
  const heal = def.heal;
  player.hp = Math.min(player.maxHp, player.hp + heal);
  const effect = def.effect ? applyEffect(player, def.effect, now) : null;
  return { heal, effect };
}

/** @param {any} player @param {{ kind: string, ms: number }} e @param {number} now */
function applyEffect(player, e, now) {
  if (e.kind === 'stamina') {
    player.stamina = player.maxStamina;
    player.exhausted = false;
  } else {
    player.buffs = { ...(player.buffs ?? {}), [e.kind]: now + e.ms };
  }
  return e.kind;
}

/** @param {any} player @param {string} kind @param {number} now */
export const hasBuff = (player, kind, now) => (player.buffs?.[kind] ?? 0) > now;

/**
 * What cooking these ingredients makes (1 to 3 materials).
 * Known recipe -> its dish. Anything else edible -> "ごった煮" healing 1.5x the ingredients.
 * Nothing edible (only parts) -> "あやしい料理".
 * @param {string[]} ingredients
 * @returns {{ result: string, heal: number }}
 */
export function cookResult(ingredients) {
  const key = [...ingredients].sort().join('+');
  const recipe = DATA.recipes.find((/** @type {any} */ r) => [...r.ingredients].sort().join('+') === key);
  if (recipe) return { result: recipe.result, heal: itemDef(recipe.result).heal };
  const heal = ingredients.reduce((s, id) => s + (itemDef(id).heal ?? 0), 0);
  if (heal === 0) return { result: 'dubious_food', heal: itemDef('dubious_food').heal };
  return { result: 'mixed_stew', heal: Math.round(heal * 1.5) };
}

/**
 * Cooks at a fire. Uses the ingredients; a new recipe is remembered.
 * Mixed stews remember their heal amount in a separate stack id ("mixed_stew:9").
 * @param {Inventory} inv @param {string[]} ingredients
 * @returns {{ result: string, name: string, heal: number, discovered: boolean } | null}
 */
export function cook(inv, ingredients) {
  if (ingredients.length < 1 || ingredients.length > 3) return null;
  /** @type {Record<string, number>} */
  const need = {};
  for (const id of ingredients) {
    if (itemDef(id).type !== 'material') return null;
    need[id] = (need[id] ?? 0) + 1;
  }
  for (const [id, n] of Object.entries(need)) if (countOf(inv, id) < n) return null;
  const { result, heal } = cookResult(ingredients);
  const stackId = result === 'mixed_stew' ? `mixed_stew:${heal}` : result;
  if (countOf(inv, stackId) >= DATA.limits.stack) return null;
  for (const [id, n] of Object.entries(need)) removeItem(inv, id, n);
  inv.items[stackId] = countOf(inv, stackId) + 1;
  const discovered = result !== 'mixed_stew' && result !== 'dubious_food' && !inv.recipes.includes(result);
  if (discovered) inv.recipes.push(result);
  return { result: stackId, name: itemDef(result).name, heal, discovered };
}

/** Base id of a stack id ("mixed_stew:9" -> "mixed_stew"). @param {string} stackId */
export const baseId = (stackId) => stackId.split(':')[0];

/** Heal of a stack (mixed stews carry their own). @param {string} stackId */
export function healOf(stackId) {
  const [id, h] = stackId.split(':');
  return h !== undefined ? Number(h) : (itemDef(id).heal ?? 0);
}

/**
 * Eats a stack (handles "mixed_stew:9").
 * @param {Inventory} inv @param {string} stackId @param {any} player @param {number} now
 */
export function eatStack(inv, stackId, player, now) {
  if (!stackId.includes(':')) return eat(inv, stackId, player, now);
  if (!removeItem(inv, stackId)) return null;
  const heal = healOf(stackId);
  player.hp = Math.min(player.maxHp, player.hp + heal);
  return { heal, effect: null };
}

/** The next upgrade for a weapon, or null at the max level. @param {Gear} g */
export function nextUpgrade(g) {
  return DATA.forge.upgrades.find((/** @type {any} */ u) => u.level === g.lvl + 1) ?? null;
}

/** @param {Inventory} inv @param {{ money: number, materials?: Record<string, number> }} cost */
export function canAfford(inv, cost) {
  if (inv.money < cost.money) return false;
  return Object.entries(cost.materials ?? {}).every(([id, n]) => countOf(inv, id) >= n);
}

/**
 * Forge: upgrade a weapon by one level (damage +20% each, refills durability).
 * @param {Inventory} inv @param {number} index weapon index
 * @returns {'ok' | 'max' | 'cost' | 'none'}
 */
export function upgradeWeapon(inv, index) {
  const g = inv.weapons[index];
  if (!g) return 'none';
  const up = nextUpgrade(g);
  if (!up) return 'max';
  if (!canAfford(inv, up)) return 'cost';
  inv.money -= up.money;
  for (const [id, n] of Object.entries(up.materials ?? {})) removeItem(inv, id, /** @type {number} */ (n));
  g.lvl += 1;
  g.dur = itemDef(g.id).durability;
  return 'ok';
}

/** Repair cost of a weapon or bow. @param {Gear} g */
export const repairCost = (g) => (itemDef(g.id).durability - g.dur) * DATA.forge.repairMoneyPerPoint;

/**
 * Forge: repair to full durability.
 * @param {Inventory} inv @param {'weapon' | 'bow'} kind @param {number} index
 * @returns {'ok' | 'full' | 'cost' | 'none'}
 */
export function repairGear(inv, kind, index) {
  const g = (kind === 'weapon' ? inv.weapons : inv.bows)[index];
  if (!g) return 'none';
  const cost = repairCost(g);
  if (cost === 0) return 'full';
  if (inv.money < cost) return 'cost';
  inv.money -= cost;
  g.dur = itemDef(g.id).durability;
  return 'ok';
}

/**
 * Drops of a defeated enemy (deterministic: `r` in [0,1) per drop entry).
 * @param {string} kind @param {(k: number) => number} r
 * @returns {{ item: string, count: number }[]}
 */
export function dropsFor(kind, r) {
  const list = /** @type {any} */ (DATA.drops)[kind] ?? [];
  return list.filter((/** @type {any} */ d, /** @type {number} */ k) => r(k) < d.chance).map((/** @type {any} */ d) => ({ item: d.item, count: d.count }));
}

/** Each 星の欠片 gives one heart or 20 stamina (P7, DESIGN.md 5.6). */
export const SHARD = Object.freeze({ heartQuarters: 4, maxHearts: 10, stamina: 20, maxStamina: 200 });

/**
 * Uses a star shard on the player's health or stamina.
 * @param {any} progress @param {any} player @param {'heart' | 'stamina'} kind
 * @returns {boolean}
 */
export function useShard(progress, player, kind) {
  const inv = progress.inv;
  if (countOf(inv, 'star_shard') === 0) return false;
  if (kind === 'heart' && progress.maxHp >= SHARD.maxHearts * 4) return false;
  if (kind === 'stamina' && progress.maxStamina >= SHARD.maxStamina) return false;
  removeItem(inv, 'star_shard');
  if (kind === 'heart') {
    progress.maxHp += SHARD.heartQuarters;
    player.maxHp = progress.maxHp;
    player.hp = progress.maxHp;
  } else {
    progress.maxStamina += SHARD.stamina;
    player.maxStamina = progress.maxStamina;
    player.stamina = progress.maxStamina;
  }
  return true;
}

/** A copy safe to save / restore (and to merge into old saves). @param {any} saved @returns {Inventory} */
export function normalizeInventory(saved) {
  const base = createInventory();
  if (!saved) return base;
  return {
    money: typeof saved.money === 'number' ? saved.money : base.money,
    items: { ...(saved.items ?? base.items) },
    weapons: (saved.weapons ?? base.weapons).filter((/** @type {Gear} */ g) => BY_ID.has(g.id)).map((/** @type {Gear} */ g) => ({ ...g })),
    bows: (saved.bows ?? base.bows).filter((/** @type {Gear} */ g) => BY_ID.has(g.id)).map((/** @type {Gear} */ g) => ({ ...g })),
    equip: { ...base.equip, ...(saved.equip ?? {}) },
    recipes: [...(saved.recipes ?? [])],
  };
}
