import { describe, it, expect } from 'vitest';
import DATA from '../../data/items.json';
import { validateItems } from '../../src/game/items/validateItems.js';
import {
  createInventory,
  addItem,
  removeItem,
  equipGear,
  equipArmor,
  weaponStats,
  wearGear,
  armorStats,
  eat,
  eatStack,
  cook,
  cookResult,
  upgradeWeapon,
  repairGear,
  repairCost,
  dropsFor,
  normalizeInventory,
  itemDef,
} from '../../src/game/items/inventory.js';
import { migrate, makeEnvelope, SCHEMA_VERSION } from '../../src/save/saveFormat.js';
import { createGameState, stepGame } from '../../src/game/state.js';
import { ISLAND } from '../../src/game/world/maps/island.js';
import { hitPlayer } from '../../src/game/combat/damage.js';
import { createEnemy } from '../../src/game/entities/enemies.js';
import { tileFeet, applyProgress, emptyProgress } from '../../src/game/world/features.js';

const none = { moveX: 0, moveY: 0, dash: false, jump: false, attack: false, dodge: false, guard: false, bow: false };
const player = () => ({ hp: 4, maxHp: 12, stamina: 10, maxStamina: 100, exhausted: true });

describe('item data (JSON integrity)', () => {
  it('data/items.json and the island references are valid', () => {
    expect(validateItems(DATA, ISLAND)).toEqual([]);
  });

  it('the validator catches broken data', () => {
    const bad = JSON.parse(JSON.stringify(DATA));
    bad.items.push({ ...bad.items[0] }); // duplicate id
    bad.items.push({ id: 'Bad Id', name: '', type: 'gem', desc: 'x', price: 1 });
    bad.recipes.push({ result: 'nothing', ingredients: ['beast_meat'] }); // unknown + duplicate ingredients
    bad.forge.upgrades[0].materials = { ghost: 1 };
    const errors = validateItems(bad, { chests: [{ id: 'c', reward: 'item', item: 'missing' }], pickups: [{ id: 'p', item: 'nope' }] });
    const text = errors.join('\n');
    expect(text).toMatch(/duplicate id/);
    expect(text).toMatch(/lower_snake_case/);
    expect(text).toMatch(/unknown item "nothing"/);
    expect(text).toMatch(/same ingredients/);
    expect(text).toMatch(/ghost/);
    expect(text).toMatch(/chest c/);
    expect(text).toMatch(/pickup p/);
  });
});

describe('inventory', () => {
  it('starts with a wooden sword, a bow and arrows in hand', () => {
    const inv = createInventory();
    expect(weaponStats(inv).name).toBe('木の剣');
    expect(inv.items.arrow).toBe(15);
    expect(inv.equip.bow).toBe(0);
  });

  it('stacks up to the limit and has a fixed number of weapon slots', () => {
    const inv = createInventory();
    expect(addItem(inv, 'arrow', 200)).toBe(DATA.limits.stack - 15);
    expect(inv.items.arrow).toBe(DATA.limits.stack);
    let taken = 0;
    for (let k = 0; k < 10; k++) taken += addItem(inv, 'travel_sword');
    expect(inv.weapons.length).toBe(DATA.limits.weapons);
    expect(taken).toBe(DATA.limits.weapons - 1);
    expect(removeItem(inv, 'arrow', 1000)).toBe(false);
  });

  it('a weapon wears with every hit and breaks; the next one comes to hand, then bare fists', () => {
    const inv = createInventory();
    addItem(inv, 'guard_spear');
    const dur = itemDef('wood_sword').durability;
    for (let k = 0; k < dur - 1; k++) expect(wearGear(inv, 'weapon')).toBe(null);
    expect(wearGear(inv, 'weapon')).toBe('木の剣');
    expect(weaponStats(inv).name).toBe('見張りの槍');
    inv.weapons[0].dur = 1;
    wearGear(inv, 'weapon');
    expect(weaponStats(inv).name).toBe('素手');
    expect(weaponStats(inv).damage).toBe(DATA.fists.damage);
  });

  it('armor adds defense and traits; wearing the worn piece again takes it off', () => {
    const inv = createInventory();
    addItem(inv, 'bark_vest');
    addItem(inv, 'grip_boots');
    equipArmor(inv, 'bark_vest');
    equipArmor(inv, 'grip_boots');
    expect(armorStats(inv).defense).toBe(3);
    expect(armorStats(inv).traits.has('grip')).toBe(true);
    equipArmor(inv, 'grip_boots');
    expect(armorStats(inv).defense).toBe(2);
    expect(equipArmor(inv, 'insulated_cap')).toBe(false); // not owned
  });

  it('eating heals and starts effects', () => {
    const inv = createInventory();
    addItem(inv, 'swift_herb');
    addItem(inv, 'hunter_stew');
    const p = player();
    expect(eat(inv, 'swift_herb', p, 0)).toEqual({ heal: 1, effect: 'stamina' });
    expect(p.stamina).toBe(100);
    expect(p.exhausted).toBe(false);
    eat(inv, 'hunter_stew', p, 1000);
    expect(p.hp).toBe(12); // capped at max
    expect(p.buffs.attackUp).toBe(1000 + 120000);
    expect(eat(inv, 'hunter_stew', p, 0)).toBe(null); // none left
    expect(eat(inv, 'beast_fang', p, 0)).toBe(null); // not food
  });
});

describe('cooking', () => {
  it('a known recipe makes its dish and is remembered once', () => {
    const inv = createInventory();
    addItem(inv, 'beast_meat', 2);
    addItem(inv, 'mushroom');
    addItem(inv, 'swift_herb');
    const r = cook(inv, ['swift_herb', 'beast_meat', 'mushroom']); // order does not matter
    expect(r).toMatchObject({ result: 'hunter_stew', discovered: true });
    expect(inv.items.beast_meat).toBe(1);
    expect(inv.recipes).toEqual(['hunter_stew']);
    expect(cook(inv, ['beast_meat'])).toMatchObject({ result: 'grilled_meat', discovered: true });
  });

  it('other mixes become a stew healing 1.5x; parts alone are dubious', () => {
    expect(cookResult(['red_berry', 'mushroom'])).toEqual({ result: 'mixed_stew', heal: 6 });
    expect(cookResult(['beast_fang'])).toEqual({ result: 'dubious_food', heal: 1 });
    const inv = createInventory();
    addItem(inv, 'red_berry');
    addItem(inv, 'mushroom');
    const r = cook(inv, ['red_berry', 'mushroom']);
    expect(r.result).toBe('mixed_stew:6');
    const p = player();
    eatStack(inv, 'mixed_stew:6', p, 0);
    expect(p.hp).toBe(10);
    expect(inv.recipes).toEqual([]);
  });

  it('cannot cook without the ingredients', () => {
    const inv = createInventory();
    expect(cook(inv, ['beast_meat'])).toBe(null);
    expect(cook(inv, [])).toBe(null);
  });
});

describe('forge', () => {
  it('upgrades with money and materials; each level adds damage and refills durability', () => {
    const inv = createInventory();
    inv.weapons[0].dur = 3;
    expect(upgradeWeapon(inv, 0)).toBe('cost');
    inv.money = 1000;
    addItem(inv, 'beast_fang', 3);
    addItem(inv, 'murk_crystal', 4);
    const base = weaponStats(inv).damage;
    expect(upgradeWeapon(inv, 0)).toBe('ok');
    expect(inv.weapons[0].dur).toBe(itemDef('wood_sword').durability);
    expect(weaponStats(inv).damage).toBeCloseTo(base * (1 + DATA.forge.damagePerLevel));
    expect(upgradeWeapon(inv, 0)).toBe('ok');
    expect(upgradeWeapon(inv, 0)).toBe('ok');
    expect(upgradeWeapon(inv, 0)).toBe('max');
    expect(inv.money).toBe(1000 - 30 - 60 - 120);
  });

  it('repairs for money by missing durability', () => {
    const inv = createInventory();
    inv.bows[0].dur = 10;
    expect(repairCost(inv.bows[0])).toBe(20);
    expect(repairGear(inv, 'bow', 0)).toBe('cost');
    inv.money = 25;
    expect(repairGear(inv, 'bow', 0)).toBe('ok');
    expect(inv.money).toBe(5);
    expect(repairGear(inv, 'bow', 0)).toBe('full');
  });
});

describe('in the game', () => {
  function island() {
    const s = createGameState(ISLAND);
    s.enemies = [];
    s.enemySpawns = [];
    stepGame(s, none); // places the map's items
    return s;
  }

  it('the bow needs arrows: each shot uses one and wears the bow', () => {
    const s = island();
    s.progress.inv.items.arrow = 1;
    const dur = s.progress.inv.bows[0].dur;
    const shoot = () => {
      for (let i = 0; i < 30; i++) stepGame(s, { ...none, bow: true });
      stepGame(s, none);
    };
    shoot();
    expect(s.progress.inv.items.arrow).toBeUndefined();
    expect(s.progress.inv.bows[0].dur).toBe(dur - 1);
    shoot();
    expect(s.events.some((e) => e.type === 'noArrows')).toBe(true);
  });

  it('a heavier weapon hits harder; a landed hit wears it', () => {
    const hitWith = (id) => {
      const s = island();
      if (id) {
        addItem(s.progress.inv, id);
        equipGear(s.progress.inv, 'weapon', 1);
      }
      const p = s.player;
      const e = createEnemy('beast', p.x, p.y + 12, p.z, 50);
      e.hp = 100;
      s.enemies = [e];
      p.facing = 'down';
      p.aimX = 0;
      p.aimY = 1;
      stepGame(s, { ...none, attack: true });
      for (let i = 0; i < 20; i++) stepGame(s, none);
      return { dealt: 100 - e.hp, dur: s.progress.inv.weapons[id ? 1 : 0].dur };
    };
    const wood = hitWith(null);
    const great = hitWith('rusty_greatsword');
    expect(great.dealt).toBeGreaterThan(wood.dealt);
    expect(wood.dur).toBe(itemDef('wood_sword').durability - 1);
  });

  it('armor softens hits; fire-proof and shock-proof stop those', () => {
    const s = island();
    const p = s.player;
    addItem(s.progress.inv, 'bark_vest');
    equipArmor(s.progress.inv, 'bark_vest');
    stepGame(s, none);
    const hp = p.hp;
    hitPlayer(s, { owner: 'enemy', id: 'x1', damage: 4, from: { x: p.x, y: p.y - 10 }, kind: 'melee' });
    expect(hp - p.hp).toBe(3); // defense 2 -> 1 less
    p.invulnMs = 0;
    addItem(s.progress.inv, 'insulated_cap');
    equipArmor(s.progress.inv, 'insulated_cap');
    stepGame(s, none);
    p.invulnMs = 0;
    expect(hitPlayer(s, { owner: 'enemy', id: 'x2', damage: 4, from: p, kind: 'env', element: 'shock' })).toBe('ignored');
  });

  it('defeated enemies drop items you pick up by walking over them', () => {
    const s = island();
    const p = s.player;
    const e = createEnemy('beast', p.x + 40, p.y, p.z, 77);
    e.state = 'dead';
    e.t = 0;
    s.enemies = [e];
    stepGame(s, none);
    const drops = s.pickups.filter((d) => d.key.startsWith('drop'));
    expect(drops.map((d) => d.item)).toContain('beast_meat');
    p.x = drops[0].x;
    p.y = drops[0].y;
    stepGame(s, none);
    expect(s.progress.inv.items[drops[0].item]).toBeGreaterThan(0);
    expect(dropsFor('archer', () => 0).map((d) => d.item)).toEqual(['murk_crystal', 'arrow']);
  });

  it('items placed on the map are remembered when taken and come back a day later', () => {
    const s = island();
    const pk = ISLAND.pickups.find((x) => x.item === 'mushroom');
    const f = tileFeet(s.map, pk.tx, pk.ty);
    s.player.x = f.x;
    s.player.y = f.y;
    s.player.z = s.map.elev[pk.ty * s.map.width + pk.tx];
    stepGame(s, none);
    expect(s.progress.inv.items.mushroom).toBe(1);
    expect(s.progress.picked[pk.id]).toBeGreaterThan(0);
    const t = createGameState(ISLAND);
    applyProgress(t, { ...emptyProgress(), picked: { [pk.id]: t.env.now } });
    stepGame(t, none);
    expect(t.pickups.some((x) => x.key === pk.id)).toBe(false);
    const u = createGameState(ISLAND);
    applyProgress(u, { ...emptyProgress(), picked: { [pk.id]: u.env.now - 25 * 60_000 } });
    stepGame(u, none);
    expect(u.pickups.some((x) => x.key === pk.id)).toBe(true);
  });

  it('chests now give equipment or money', () => {
    const s = island();
    const c = ISLAND.chests.find((x) => x.reward === 'money');
    const f = tileFeet(s.map, c.tx, c.ty + 1);
    Object.assign(s.player, { x: f.x, y: f.y, z: s.map.elev[(c.ty + 1) * s.map.width + c.tx], facing: 'up', aimX: 0, aimY: -1 });
    stepGame(s, { ...none, attack: true });
    expect(s.progress.inv.money).toBe(c.money);
  });

  it('the forge and the camp fire are in reach to use', () => {
    const s = island();
    const anvil = ISLAND.envObjects.find((o) => o.type === 'anvil');
    const f = tileFeet(s.map, anvil.tx, anvil.ty + 1);
    Object.assign(s.player, { x: f.x, y: f.y, z: s.map.elev[(anvil.ty + 1) * s.map.width + anvil.tx] });
    stepGame(s, none);
    expect(s.nearby).toBe('forge');
  });
});

describe('save format v2', () => {
  it('migrates old saves: treasures become money', () => {
    expect(SCHEMA_VERSION).toBe(3); // v3 (P10.3): world differences named by object
    const old = { ...makeEnvelope({ openedChests: ['camp'], treasures: 3, maxHp: 16 }, '0.0.1', 1, 0), schemaVersion: 1 };
    const r = migrate(old);
    expect(r.ok).toBe(true);
    expect(r.data.treasures).toBeUndefined();
    expect(r.data.inv.money).toBe(150);
    const inv = normalizeInventory(r.data.inv);
    expect(inv.money).toBe(150);
    expect(inv.weapons[0].id).toBe('wood_sword'); // the starting kit is given
  });
});
