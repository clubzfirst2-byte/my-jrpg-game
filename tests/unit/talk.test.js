import { describe, it, expect } from 'vitest';
import { createGameState, stepGame } from '../../src/game/state.js';
import { WORLD } from '../../src/game/world/world.js';
import { startDialogue, dialogueView, advance, questState, buy, sell, sellPrice, questLog, TALK_DATA } from '../../src/game/npc/talk.js';
import { validateTalk } from '../../src/game/npc/validateTalk.js';
import { addItem } from '../../src/game/items/inventory.js';
import { applyProgress, emptyProgress, tileFeet } from '../../src/game/world/features.js';
import ITEMS from '../../data/items.json';

// P9 completion check (DESIGN.md roadmap): conversations and flag transitions.

const none = { moveX: 0, moveY: 0, dash: false, jump: false, attack: false, dodge: false, guard: false, bow: false };
const world = () => {
  const s = createGameState(WORLD);
  s.enemies = [];
  s.enemySpawns = [];
  return s;
};
/** Reads every line until the conversation asks a question or ends; returns what was said. */
function readAll(s) {
  const said = [];
  for (let k = 0; k < 20 && s.dialogue; k++) {
    const v = dialogueView(s);
    said.push(v.text);
    if (v.choices) return { said, choices: v.choices };
    advance(s);
  }
  return { said, choices: null };
}

describe('data', () => {
  it('dialogue, quests, shops and villagers are consistent (every node reachable)', () => {
    expect(validateTalk({ ...TALK_DATA, items: ITEMS }, WORLD)).toEqual([]);
  });

  it('broken references are caught', () => {
    const bad = JSON.parse(JSON.stringify(TALK_DATA));
    bad.dialogue.dialogues.elder.nodes.ask.choices[0].goto = 'nowhere';
    bad.dialogue.dialogues.elder.nodes.orphan = { text: ['…'] };
    bad.quests.quests[0].reward.items = { ghost: 1 };
    bad.shops.shops[0].sells.push({ item: 'ghost', price: 1 });
    const text = validateTalk({ ...bad, items: ITEMS }, { npcs: [{ id: 'x', dialogue: 'nobody' }] }).join('\n');
    expect(text).toMatch(/unknown node "nowhere"/);
    expect(text).toMatch(/orphan: unreachable/);
    expect(text).toMatch(/unknown item "ghost"/);
    expect(text).toMatch(/unknown dialogue "nobody"/);
  });
});

describe('the elder and the lost charm (none -> active -> ready -> done)', () => {
  it('first meeting sets a flag; the second talk skips the greeting', () => {
    const s = world();
    startDialogue(s, 'elder');
    const first = readAll(s);
    expect(first.said[0]).toMatch(/風見の村/);
    expect(s.progress.flags.elder_met).toBe(true);
    expect(first.choices).toEqual(['引き受ける', 'また今度']);
    advance(s, 1); // また今度
    readAll(s);
    expect(s.dialogue).toBe(null);
    expect(questState(s, 'lost_charm')).toBe('none');
    startDialogue(s, 'elder');
    expect(readAll(s).said[0]).toMatch(/困っておって/); // straight to the request
  });

  it('accepting starts the quest; it is ready once the charm is in the bag; reporting gives the reward', () => {
    const s = world();
    startDialogue(s, 'elder');
    readAll(s);
    advance(s, 0); // 引き受ける
    readAll(s);
    expect(questState(s, 'lost_charm')).toBe('active');
    expect(questLog(s).map((q) => q.id)).toEqual(['lost_charm']);
    startDialogue(s, 'elder');
    expect(readAll(s).said[0]).toMatch(/見つかったかの/);
    addItem(s.progress.inv, 'lost_charm');
    expect(questState(s, 'lost_charm')).toBe('ready');
    const money = s.progress.inv.money;
    startDialogue(s, 'elder');
    readAll(s);
    expect(questState(s, 'lost_charm')).toBe('done');
    expect(s.progress.inv.money).toBe(money + 150);
    expect(s.progress.inv.items.star_shard).toBe(1);
    expect(s.progress.inv.items.lost_charm).toBeUndefined(); // handed over
    expect(s.events.some((e) => e.type === 'questDone' && e.id === 'lost_charm')).toBe(true);
    startDialogue(s, 'elder');
    expect(readAll(s).said[0]).toMatch(/穏やか/);
  });

  it('the state survives a save (flags and quests are part of the progress)', () => {
    const s = world();
    startDialogue(s, 'elder');
    readAll(s);
    advance(s, 0);
    readAll(s);
    const saved = JSON.parse(JSON.stringify(s.progress));
    const t = world();
    applyProgress(t, saved);
    expect(questState(t, 'lost_charm')).toBe('active');
    expect(t.progress.flags.elder_met).toBe(true);
  });
});

describe('other quests', () => {
  it('the cook needs three pieces of meat', () => {
    const s = world();
    startDialogue(s, 'cook');
    readAll(s);
    advance(s, 0);
    readAll(s);
    addItem(s.progress.inv, 'beast_meat', 2);
    expect(questState(s, 'meat_for_cook')).toBe('active');
    addItem(s.progress.inv, 'beast_meat', 1);
    expect(questState(s, 'meat_for_cook')).toBe('ready');
    startDialogue(s, 'cook');
    readAll(s);
    expect(questState(s, 'meat_for_cook')).toBe('done');
    expect(s.progress.inv.items.beast_meat).toBeUndefined();
    expect(s.progress.inv.items.hunter_stew).toBe(1);
  });

  it('the guard’s errand is done by discovering the windmill', () => {
    const s = world();
    startDialogue(s, 'guard');
    readAll(s);
    advance(s, 0);
    readAll(s);
    expect(questState(s, 'windmill_watch')).toBe('active');
    s.progress.landmarks.push('windmill');
    expect(questState(s, 'windmill_watch')).toBe('ready');
  });

  it('completing is impossible before the goal is met', () => {
    const s = world();
    startDialogue(s, 'cook');
    readAll(s);
    advance(s, 0);
    readAll(s);
    startDialogue(s, 'cook');
    readAll(s);
    expect(questState(s, 'meat_for_cook')).toBe('active');
  });
});

describe('the shop', () => {
  it('talking to the merchant opens the shop; buying costs money, selling pays half', () => {
    const s = world();
    startDialogue(s, 'merchant');
    readAll(s);
    advance(s, 0); // 見せて
    expect(s.shop).toBe('general');
    expect(s.dialogue).toBe(null);
    s.progress.inv.money = 10;
    expect(buy(s, 'general', 'arrow', 3)).toBe('ok');
    expect(s.progress.inv.money).toBe(1);
    expect(buy(s, 'general', 'travel_sword')).toBe('money');
    expect(buy(s, 'general', 'ember_sword')).toBe('none'); // not sold here
    addItem(s.progress.inv, 'beast_fang', 1);
    expect(sell(s, 'general', 'beast_fang')).toBe('ok');
    expect(s.progress.inv.money).toBe(1 + sellPrice('general', 'beast_fang'));
    addItem(s.progress.inv, 'lost_charm');
    expect(sell(s, 'general', 'lost_charm')).toBe('key'); // story items cannot be sold
  });
});

describe('in the village', () => {
  it('the attack button talks to the villager in front (instead of swinging)', () => {
    const s = world();
    const elder = s.npcs.find((n) => n.id === 'elder');
    const p = s.player;
    const f = tileFeet(s.map, Math.floor(elder.x / 16), Math.floor(elder.y / 16) + 1);
    Object.assign(p, { x: f.x, y: f.y, z: elder.z, facing: 'up', aimX: 0, aimY: -1 });
    elder.homeX = elder.tx = elder.x;
    elder.homeY = elder.ty = elder.y;
    stepGame(s, { ...none, attack: true });
    expect(s.dialogue?.id).toBe('elder');
    expect(p.action).toBe('none');
  });

  it('villagers stroll near home and stop for the player', () => {
    const s = world();
    const n = s.npcs.find((x) => !x.stay); // (v1.0: the princess on the beach comes first and stays put)
    s.player.x = 5 * 16;
    s.player.y = 5 * 16;
    for (let i = 0; i < 60 * 20; i++) stepGame(s, none);
    expect(Math.hypot(n.x - n.homeX, n.y - n.homeY)).toBeLessThanOrEqual(30);
    s.player.x = n.x + 10;
    s.player.y = n.y;
    const at = { x: n.x, y: n.y };
    for (let i = 0; i < 60; i++) stepGame(s, none);
    expect(Math.hypot(n.x - at.x, n.y - at.y)).toBeLessThan(0.5);
    expect(n.facing).toBe('right');
  });

  it('a found story item never comes back', () => {
    const s = world();
    const charm = WORLD.pickups.find((p) => p.item === 'lost_charm');
    const t = world();
    applyProgress(t, { ...emptyProgress(), picked: { [charm.id]: t.env.now - 48 * 60_000 } });
    stepGame(t, none);
    expect(t.pickups.some((p) => p.key === charm.id)).toBe(false);
    void s;
  });
});
