// @ts-check
// Integrity check of the item data (P6, DESIGN.md roadmap: "データの整合性チェック"). Used by the unit
// tests and by `npm run check:data` (CI). Returns a list of problems; empty means valid.

const TYPES = ['weapon', 'bow', 'ammo', 'armor', 'material', 'food', 'key'];
const SLOTS = ['head', 'body', 'legs'];
const TRAITS = ['shockproof', 'grip', 'fireproof'];
const EFFECTS = ['stamina', 'attackUp', 'defenseUp', 'fireproof'];
const ELEMENTS = ['fire'];

/**
 * @param {any} data contents of data/items.json
 * @param {{ chests?: any[], pickups?: any[] }} [map] references from a map to check too
 * @returns {string[]}
 */
export function validateItems(data, map = {}) {
  /** @type {string[]} */
  const errors = [];
  const err = (/** @type {string} */ m) => errors.push(m);
  const num = (/** @type {any} */ v, /** @type {string} */ what, min = -Infinity, max = Infinity) => {
    if (typeof v !== 'number' || !Number.isFinite(v) || v < min || v > max) err(`${what}: expected a number in ${min}..${max}, got ${JSON.stringify(v)}`);
  };
  if (!data || typeof data !== 'object') return ['items.json: not an object'];
  num(data.version, 'version', 1);
  if (!Array.isArray(data.items)) return [...errors, 'items: must be an array'];

  /** @type {Map<string, any>} */
  const byId = new Map();
  for (const [k, it] of data.items.entries()) {
    const at = `items[${k}]${it && it.id ? ` (${it.id})` : ''}`;
    if (!it || typeof it.id !== 'string' || !/^[a-z][a-z0-9_]*$/.test(it.id)) {
      err(`${at}: id must be lower_snake_case`);
      continue;
    }
    if (byId.has(it.id)) err(`${at}: duplicate id`);
    byId.set(it.id, it);
    if (typeof it.name !== 'string' || it.name.length === 0) err(`${at}: name is required`);
    if (!TYPES.includes(it.type)) err(`${at}: type must be one of ${TYPES.join(', ')}`);
    if (typeof it.desc !== 'string') err(`${at}: desc is required`);
    num(it.price, `${at}.price`, 0, 10000);
    switch (it.type) {
      case 'weapon':
        num(it.damage, `${at}.damage`, 0.1, 10);
        num(it.reach, `${at}.reach`, -8, 16);
        num(it.speed, `${at}.speed`, 0.5, 2);
        num(it.durability, `${at}.durability`, 1, 999);
        if (it.element !== undefined && !ELEMENTS.includes(it.element)) err(`${at}.element: unknown "${it.element}"`);
        break;
      case 'bow':
        num(it.damage, `${at}.damage`, 0.1, 10);
        num(it.durability, `${at}.durability`, 1, 999);
        break;
      case 'armor':
        if (!SLOTS.includes(it.slot)) err(`${at}.slot: must be one of ${SLOTS.join(', ')}`);
        num(it.defense, `${at}.defense`, 0, 10);
        if (it.trait !== undefined && !TRAITS.includes(it.trait)) err(`${at}.trait: unknown "${it.trait}"`);
        break;
      case 'material':
      case 'food':
        if (it.heal !== undefined) num(it.heal, `${at}.heal`, 0, 80);
        if (it.type === 'food' && it.heal === undefined) err(`${at}.heal: food needs heal`);
        if (it.effect !== undefined) {
          if (!EFFECTS.includes(it.effect?.kind)) err(`${at}.effect.kind: unknown "${it.effect?.kind}"`);
          num(it.effect?.ms, `${at}.effect.ms`, 0, 3_600_000);
        }
        if (it.tags !== undefined && (!Array.isArray(it.tags) || it.tags.some((/** @type {any} */ t) => typeof t !== 'string'))) err(`${at}.tags: must be strings`);
        break;
      default:
    }
  }
  const exists = (/** @type {string} */ id, /** @type {string} */ where, /** @type {string[]} */ types) => {
    const it = byId.get(id);
    if (!it) err(`${where}: unknown item "${id}"`);
    else if (types && !types.includes(it.type)) err(`${where}: "${id}" is a ${it.type}, expected ${types.join(' / ')}`);
  };

  // Recipes: existing ingredients (materials), a food result, no two recipes with the same ingredients.
  const seen = new Set();
  for (const [k, r] of (data.recipes ?? []).entries()) {
    const at = `recipes[${k}]`;
    exists(r.result, `${at}.result`, ['food']);
    if (!Array.isArray(r.ingredients) || r.ingredients.length < 1 || r.ingredients.length > 3) err(`${at}.ingredients: 1 to 3 items`);
    else {
      for (const i of r.ingredients) exists(i, `${at}.ingredients`, ['material']);
      const key = [...r.ingredients].sort().join('+');
      if (seen.has(key)) err(`${at}: same ingredients as another recipe (${key})`);
      seen.add(key);
    }
  }
  for (const id of ['mixed_stew', 'dubious_food']) exists(id, 'cooking fallback', ['food']);

  // Forge.
  const f = data.forge;
  if (!f) err('forge: missing');
  else {
    num(f.maxLevel, 'forge.maxLevel', 1, 10);
    num(f.damagePerLevel, 'forge.damagePerLevel', 0, 2);
    num(f.repairMoneyPerPoint, 'forge.repairMoneyPerPoint', 0, 100);
    if (!Array.isArray(f.upgrades) || f.upgrades.length !== f.maxLevel) err('forge.upgrades: one entry per level');
    else
      f.upgrades.forEach((/** @type {any} */ u, /** @type {number} */ k) => {
        if (u.level !== k + 1) err(`forge.upgrades[${k}].level: expected ${k + 1}`);
        num(u.money, `forge.upgrades[${k}].money`, 0, 100000);
        for (const [id, n] of Object.entries(u.materials ?? {})) {
          exists(id, `forge.upgrades[${k}].materials`, ['material']);
          num(n, `forge.upgrades[${k}].materials.${id}`, 1, 99);
        }
      });
  }

  // Drops.
  for (const [kind, list] of Object.entries(data.drops ?? {})) {
    for (const [k, d] of /** @type {any[]} */ (list).entries()) {
      exists(d.item, `drops.${kind}[${k}]`, TYPES);
      num(d.count, `drops.${kind}[${k}].count`, 1, 99);
      num(d.chance, `drops.${kind}[${k}].chance`, 0, 1);
    }
  }

  // Starting kit and limits.
  const s = data.start;
  if (!s) err('start: missing');
  else {
    for (const id of s.weapons ?? []) exists(id, 'start.weapons', ['weapon']);
    for (const id of s.bows ?? []) exists(id, 'start.bows', ['bow']);
    for (const id of Object.keys(s.items ?? {})) exists(id, 'start.items', ['ammo', 'material', 'food', 'armor']);
    num(s.money, 'start.money', 0, 100000);
  }
  num(data.limits?.weapons, 'limits.weapons', 1, 20);
  num(data.limits?.bows, 'limits.bows', 1, 20);
  num(data.limits?.stack, 'limits.stack', 1, 999);
  num(data.fists?.damage, 'fists.damage', 0, 1);

  // References from a map.
  for (const c of map.chests ?? []) {
    if (c.reward === 'item') exists(c.item, `chest ${c.id}`, TYPES);
    else if (c.reward === 'money') num(c.money, `chest ${c.id}.money`, 1, 100000);
    else if (c.reward !== 'heart') err(`chest ${c.id}: reward must be heart / money / item`);
  }
  const pickIds = new Set();
  for (const p of map.pickups ?? []) {
    exists(p.item, `pickup ${p.id}`, TYPES);
    if (pickIds.has(p.id)) err(`pickup ${p.id}: duplicate id`);
    pickIds.add(p.id);
  }
  return errors;
}
