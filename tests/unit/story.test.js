import { describe, it, expect } from 'vitest';
import { createGameState, stepGame } from '../../src/game/state.js';
import { WORLD } from '../../src/game/world/world.js';
import { startDialogue, dialogueView, advance, questState, conditionHolds, coresPurified, completeQuest, TALK_DATA } from '../../src/game/npc/talk.js';
import { validateTalk } from '../../src/game/npc/validateTalk.js';
import { npcPresent, syncNpcs, npcAlpha, npcInReach, NPC } from '../../src/game/npc/npcs.js';
import { markNewGame, noticeOnLoad, noticeOnCore, NOTICE, STORY_FLAG } from '../../src/game/npc/storyNotices.js';
import { addItem } from '../../src/game/items/inventory.js';
import { applyProgress, emptyProgress, respawnPoint, warpOpen } from '../../src/game/world/features.js';
import { npcFrameKey } from '../../src/view/npcAnim.js';
import ITEMS from '../../data/items.json';

// v1.0 story (docs/story/V1_STORY_PROPOSAL.md, C2 / C3 / C4 / C8 / C14 and their part of C15):
// conditions on the cores of the murk, villagers who come and go, the new people and quests, the
// notices, and an exhaustive check that no quest can get stuck — with who is there at the time.

const CORES = ['core_forest', 'core_mountains', 'core_desert', 'core_lake'];
const none = { moveX: 0, moveY: 0, dash: false, jump: false, attack: false, dodge: false, guard: false, bow: false };
const world = () => {
  const s = createGameState(WORLD);
  s.enemies = [];
  s.enemySpawns = [];
  return s;
};
/** Reads every line until the conversation asks a question or ends. */
function readAll(s) {
  const said = [];
  for (let k = 0; k < 30 && s.dialogue; k++) {
    const v = dialogueView(s);
    said.push(v.text);
    if (v.choices) return { said, choices: v.choices };
    advance(s);
  }
  return { said, choices: null };
}
/** Talks until the end, answering with the given choices in turn. */
function talk(s, id, answers = []) {
  startDialogue(s, id);
  const said = [];
  const queue = [...answers];
  for (let k = 0; k < 10 && s.dialogue; k++) {
    const r = readAll(s);
    said.push(...r.said);
    if (r.choices) advance(s, queue.shift() ?? 0);
  }
  return said;
}
const ids = (s) => s.npcs.map((n) => n.id);
const withCores = (s, n) => {
  s.progress.bosses = CORES.slice(0, n);
};

describe('C2: conditions on the cores of the murk, and the cores goal', () => {
  it('cores counts the purified cores (old saves count right: only the core_ ids)', () => {
    const s = world();
    expect(coresPurified(s)).toBe(0);
    s.progress.bosses = ['core_lake', 'source']; // a final boss id is listed apart and never counts
    expect(coresPurified(s)).toBe(1);
    expect(conditionHolds(s, { cores: 1 })).toBe(true);
    expect(conditionHolds(s, { cores: 2 })).toBe(false);
    expect(conditionHolds(s, { boss: 'core_lake' })).toBe(true);
    expect(conditionHolds(s, { boss: 'core_forest' })).toBe(false);
  });

  it('「星環の呼び声」 is ready once all four cores are purified', () => {
    const s = world();
    s.progress.quests.star_ring_call = 'active';
    for (let n = 0; n < 4; n++) {
      withCores(s, n);
      expect(questState(s, 'star_ring_call')).toBe('active');
    }
    withCores(s, 4);
    expect(questState(s, 'star_ring_call')).toBe('ready');
  });

  it('the checker knows the new conditions and goal, and catches bad ones', () => {
    expect(validateTalk({ ...TALK_DATA, items: ITEMS }, WORLD)).toEqual([]);
    const bad = JSON.parse(JSON.stringify(TALK_DATA));
    bad.dialogue.dialogues.child.start[1].if = [{ cores: 5 }];
    bad.dialogue.dialogues.woman.start[1].if = [{ boss: 'core_moon' }];
    bad.quests.quests.find((q) => q.id === 'star_ring_call').goal.count = 0;
    const text = validateTalk({ ...bad, items: ITEMS }, WORLD).join('\n');
    expect(text).toMatch(/cores must be a whole number 1\.\.4/);
    expect(text).toMatch(/unknown core of the murk "core_moon"/);
    expect(text).toMatch(/star_ring_call\)\.goal: count must be a whole number 1\.\.4/);
    // Without the world, a boss is any core_ id.
    expect(validateTalk({ ...TALK_DATA, items: ITEMS }).join('\n')).not.toMatch(/core of the murk/);
  });
});

describe('C3: villagers who come and go (if) and the see-through princess (ghost)', () => {
  it('a new game: the princess is on the beach only; the other stones wait for her to be met', () => {
    const s = world();
    expect(ids(s)).toContain('princess_beach');
    for (const r of ['plains', 'desert', 'mountains', 'forest', 'lake']) expect(ids(s)).not.toContain(`princess_${r}`);
    expect(ids(s)).not.toContain('princess_home');
    for (const id of ['woman', 'smith', 'traveller', 'elder', 'cook', 'guard', 'merchant', 'child']) expect(ids(s)).toContain(id);
  });

  it('meeting her on the beach puts her by every record stone (in the order of the map)', () => {
    const s = world();
    talk(s, 'princess', [0]); // うなずく
    expect(s.progress.flags.princess_met).toBe(true);
    expect(questState(s, 'star_ring_call')).toBe('active');
    stepGame(s, none);
    const order = WORLD.npcs.map((n) => n.id).filter((id) => ids(s).includes(id));
    expect(ids(s)).toEqual(order);
    for (const r of ['beach', 'plains', 'desert', 'mountains', 'forest', 'lake']) expect(ids(s)).toContain(`princess_${r}`);
  });

  it('every 写し身 stands beside a record stone, and each is a ghost', () => {
    const ghosts = WORLD.npcs.filter((n) => n.ghost);
    expect(ghosts.map((n) => n.id).sort()).toEqual(['princess_beach', 'princess_desert', 'princess_forest', 'princess_lake', 'princess_mountains', 'princess_plains']);
    for (const g of ghosts) {
      const near = WORLD.checkpoints.find((c) => Math.abs(c.tx - g.tx) <= 1 && Math.abs(c.ty - g.ty) <= 1);
      expect(near?.id, g.id).toBe(g.id.replace('princess_', ''));
      expect(g.dialogue).toBe('princess');
      expect(g.stay).toBe(true);
    }
  });

  it('the source purified: every 写し身 is gone; the ending seen: she is in the village', () => {
    const s = world();
    s.progress.flags.princess_met = true;
    stepGame(s, none);
    expect(s.npcs.filter((n) => n.ghost)).toHaveLength(6);
    s.progress.flags.source_purified = true;
    stepGame(s, none);
    expect(s.npcs.filter((n) => n.ghost)).toEqual([]);
    expect(ids(s)).not.toContain('princess_home');
    s.progress.flags.ending_seen = true;
    stepGame(s, none);
    expect(ids(s)).toContain('princess_home');
    expect(s.npcs.find((n) => n.id === 'princess_home').ghost).toBe(false);
  });

  it('a saved game brings the right people with it', () => {
    const s = world();
    applyProgress(s, { ...emptyProgress(), flags: { princess_met: true, ending_seen: true, regalia_kept: true } });
    stepGame(s, none);
    expect(s.npcs.filter((n) => n.id.startsWith('princess_')).map((n) => n.id)).toEqual(['princess_home']);
  });

  it('someone being talked to stays until the conversation ends', () => {
    const s = world();
    startDialogue(s, 'princess', 'princess_beach');
    s.progress.flags.source_purified = true;
    syncNpcs(s); // (the princess by the source comes, C10)
    expect(ids(s)).toContain('princess_beach');
    expect(ids(s)).toContain('princess_end');
    s.dialogue = null;
    expect(syncNpcs(s)).toBe(true);
    expect(ids(s)).not.toContain('princess_beach');
  });

  it('villagers added by hand (debug) are left alone', () => {
    const s = world();
    s.npcs.push({ ...s.npcs[0], id: 'visitor' });
    s.progress.flags.source_purified = true;
    syncNpcs(s);
    expect(ids(s).at(-1)).toBe('visitor');
  });

  it('a ghost grows clearer with each core purified; everyone else is drawn solid', () => {
    const s = world();
    const p = s.npcs.find((n) => n.id === 'princess_beach');
    const elder = s.npcs.find((n) => n.id === 'elder');
    const alphas = [0, 1, 2, 3, 4].map((n) => {
      withCores(s, n);
      return npcAlpha(s, p);
    });
    expect(alphas[0]).toBeCloseTo(NPC.ghostAlpha);
    for (let k = 1; k < 5; k++) expect(alphas[k]).toBeGreaterThan(alphas[k - 1]);
    expect(alphas[4]).toBeLessThan(1);
    expect(npcAlpha(s, elder)).toBe(1);
  });

  it('a villager who is not there cannot be talked to', () => {
    const s = world();
    s.progress.flags.source_purified = true;
    stepGame(s, none);
    const def = WORLD.npcs.find((n) => n.id === 'princess_beach');
    const p = s.player;
    Object.assign(p, { x: def.tx * 16 + 8, y: (def.ty + 1) * 16 + 14, facing: 'up', aimX: 0, aimY: -1 });
    stepGame(s, { ...none, attack: true });
    expect(s.dialogue).toBe(null);
  });

  it('every princess is drawn from npc.princess.* (art), whatever her id; others from their id', () => {
    const s = world();
    s.progress.flags.princess_met = true;
    stepGame(s, none);
    const art = new Set(['npc.princess.idle.down.0', 'npc.woman.idle.down.0']);
    const has = (k) => art.has(k) || k.startsWith('npc.princess.') || k.startsWith('npc.woman.');
    const princesses = s.npcs.filter((n) => n.name === '星環の姫');
    expect(princesses).toHaveLength(6);
    for (const n of princesses) {
      expect(n.art, n.id).toBe('princess');
      expect(npcFrameKey(n, 0, has), n.id).toMatch(/^npc\.princess\.idle\.down\.\d$/);
      expect(npcFrameKey(n, 0, () => false), n.id).toBe('npc.9.walk.down.0'); // the placeholder until her art is in
    }
    expect(WORLD.npcs.find((n) => n.id === 'princess_home').art).toBe('princess');
    const woman = s.npcs.find((n) => n.id === 'woman');
    expect(woman.art).toBe('woman');
    expect(npcFrameKey(woman, 0, has)).toMatch(/^npc\.woman\.idle\./);
  });

  it('coming back to life by a record stone, an attack swings: the 写し身 is out of talk range there', () => {
    const s = world();
    s.progress.flags.princess_met = true;
    stepGame(s, none);
    for (const n of s.npcs.filter((x) => x.ghost)) {
      s.progress.checkpoint = n.id.replace('princess_', '');
      const at = respawnPoint(s);
      expect(Math.hypot(n.x - at.x, n.y - at.y), n.id).toBeGreaterThan(n.reach);
      // …but standing right in front of her (south, facing up) she can be spoken to.
      expect(14, n.id).toBeLessThan(n.reach);
      Object.assign(s.player, { x: at.x, y: at.y, z: n.z, facing: 'up', aimX: 0, aimY: -1 });
      s.dialogue = null;
      s.player.action = 'none';
      for (const [aimX, aimY] of [[0, -1], [1, 0], [-1, 0]]) {
        Object.assign(s.player, { aimX, aimY });
        expect(npcInReach(s)?.id ?? null, `${n.id} ${aimX},${aimY}`).not.toBe(n.id);
      }
      Object.assign(s.player, { x: n.x, y: n.y + 14, aimX: 0, aimY: -1 });
      expect(npcInReach(s)?.id, n.id).toBe(n.id);
    }
  });

  it('the princess in the village stays in front of the inn (never on its doorstep)', () => {
    const s = world();
    s.progress.flags.ending_seen = true;
    stepGame(s, none);
    const n = s.npcs.find((x) => x.id === 'princess_home');
    expect(n.stay).toBe(true);
    s.player.x = 5 * 16;
    s.player.y = 5 * 16;
    for (let i = 0; i < 60 * 20; i++) stepGame(s, none);
    expect([n.x, n.y]).toEqual([n.homeX, n.homeY]);
  });

  it('the checker reads appearance conditions like a dialogue’s, and catches bad ones', () => {
    const npcs = [
      { id: 'a', name: 'a', dialogue: 'princess', tx: 1, ty: 1, if: [{ flag: 'x', iz: true }] },
      { id: 'b', name: 'b', dialogue: 'princess', tx: 1, ty: 1, if: [] },
      { id: 'c', name: 'c', dialogue: 'princess', tx: 1, ty: 1, ghost: 'yes' },
      { id: 'd', name: 'd', dialogue: 'princess', tx: 1, ty: 1, if: [{ quest: 'nope', state: 'done' }], colour: 1 },
      { id: 'e_1', name: 'e', dialogue: 'princess', tx: 1, ty: 1 },
      { id: 'f_1', name: 'f', dialogue: 'princess', tx: 1, ty: 1, art: 'Princess-1', reach: 0 },
      { id: 'g', name: 'g', dialogue: 'princess', tx: 1, ty: 1, if: [{ slots: 'shield' }] },
    ];
    const text = validateTalk({ ...TALK_DATA, items: ITEMS }, { npcs }).join('\n');
    expect(text).toMatch(/npc a\.if\[0\]: unknown condition "iz"/);
    expect(text).toMatch(/npc b: if must list at least one condition/);
    expect(text).toMatch(/npc c: ghost must be true or false/);
    expect(text).toMatch(/npc d\.if\[0\]: unknown quest "nope"/);
    expect(text).toMatch(/npc d: unknown field "colour"/);
    expect(text).toMatch(/npc e_1: an id that is not a plain name needs an art name/);
    expect(text).toMatch(/npc f_1: art must be a name of lowercase letters/);
    expect(text).toMatch(/npc f_1: reach must be above 0/);
    expect(text).toMatch(/npc g\.if\[0\]: slots must be weapon \/ bow/);
  });
});

describe('C4: the new people in the world (nothing that was there has moved: compat.test.js)', () => {
  it('the village woman and the smith are in 風見の村, the traveller by the pass to the forest', () => {
    const plains = WORLD.regions.find((r) => r.id === 'plains');
    const local = (id) => {
      const n = WORLD.npcs.find((x) => x.id === id);
      return [n.tx - plains.tx, n.ty - plains.ty];
    };
    const village = WORLD.landmarks.find((l) => l.id === 'village');
    for (const id of ['woman', 'smith', 'princess_home']) {
      const n = WORLD.npcs.find((x) => x.id === id);
      expect(Math.hypot(n.tx - village.tx, n.ty - village.ty), id).toBeLessThan(12);
    }
    const pass = WORLD.warps.find((w) => w.id === 'pass-forest');
    const t = WORLD.npcs.find((x) => x.id === 'traveller');
    expect(Math.hypot(t.tx - pass.tx, t.ty - pass.ty)).toBeLessThan(10);
    expect(local('traveller')[0]).toBeLessThan(96); // outdoors, on the plains side
  });

  it('the art drops in by id: npc.<id>.* release frames, a placeholder look meanwhile', () => {
    const looks = Object.fromEntries(WORLD.npcs.map((n) => [n.id, n.look]));
    expect(looks).toMatchObject({ woman: 6, smith: 7, traveller: 8, princess_home: 9, princess_beach: 9 });
  });

  it('nobody new stands on a doorstep or a warp', () => {
    for (const n of WORLD.npcs) for (const w of WORLD.warps) expect(n.tx === w.tx && n.ty === w.ty, `${n.id} on ${w.id}`).toBe(false);
  });
});

describe('C14: the story in data', () => {
  it('first meeting: refusing twice is fine; she waits at any stone; then the quest begins', () => {
    const s = world();
    const first = talk(s, 'princess', [1, 1]); // 胸の石を見る → 目をそらす
    expect(first[0]).toMatch(/届いていた/);
    expect(questState(s, 'star_ring_call')).toBe('none');
    expect(talk(s, 'princess', [0])[0]).toMatch(/新月の夜/); // straight to the request
    expect(questState(s, 'star_ring_call')).toBe('active');
  });

  it('her words follow the cores; with all four she opens the gate and the source quest starts', () => {
    const s = world();
    talk(s, 'princess', [0]);
    const firstLine = (n) => {
      withCores(s, n);
      return talk(s, 'princess')[0];
    };
    expect(firstLine(0)).toMatch(/森・山・荒野・湖/);
    expect(firstLine(1)).toMatch(/一つ目/);
    expect(firstLine(2)).toMatch(/二つ/);
    expect(firstLine(3)).toMatch(/あと一つ/);
    expect(firstLine(4)).toMatch(/すべて断たれました/);
    expect(questState(s, 'star_ring_call')).toBe('done');
    expect(s.progress.inv.items.star_shard).toBe(1);
    expect(s.progress.flags.source_open).toBe(true);
    expect(questState(s, 'source_of_murk')).toBe('active');
    expect(talk(s, 'princess')[0]).toMatch(/浜の星環が開いています/);
  });

  it('an old save (four cores, never met her): meet → accept → report at once', () => {
    const s = world();
    withCores(s, 4);
    talk(s, 'princess', [0]);
    expect(questState(s, 'star_ring_call')).toBe('ready');
    talk(s, 'princess');
    expect(s.progress.flags.source_open).toBe(true);
  });

  it('the ending: one choice only, ever; the quest is reported', () => {
    const s = world();
    Object.assign(s.progress.flags, { princess_met: true, source_open: true, source_purified: true });
    s.progress.quests = { star_ring_call: 'done', source_of_murk: 'active' };
    expect(questState(s, 'source_of_murk')).toBe('ready');
    const said = talk(s, 'ending', [1, 0]); // 胸に戻す, うなずく
    expect(said.at(-1)).toMatch(/ありがとう/);
    expect(questState(s, 'source_of_murk')).toBe('done');
    for (let k = 0; k < 3; k++) {
      expect(talk(s, 'ending', [0, 0])[0]).toMatch(/帰りましょう/);
    }
    expect(s.progress.flags.regalia_kept).toBe(true);
    expect(s.progress.flags.regalia_joined).toBeUndefined();
    // Afterwards in the village.
    s.progress.flags.ending_seen = true;
    expect(talk(s, 'princess')[0]).toMatch(/まだ光っていますね/);
  });

  it('the village woman: mushrooms for medicine; her words change with the forest core and after the ending', () => {
    const s = world();
    talk(s, 'woman', [0]);
    expect(questState(s, 'forest_mushrooms')).toBe('active');
    addItem(s.progress.inv, 'mushroom', 3);
    const jam = s.progress.inv.items.berry_jam ?? 0;
    talk(s, 'woman');
    expect(questState(s, 'forest_mushrooms')).toBe('done');
    expect(s.progress.inv.items.mushroom).toBeUndefined();
    expect(s.progress.inv.items.berry_jam).toBe(jam + 2);
    expect(talk(s, 'woman')[0]).toMatch(/大樹のほうから/);
    s.progress.bosses = ['core_forest'];
    expect(talk(s, 'woman')[0]).toMatch(/森の霧が晴れた/);
    s.progress.flags.ending_seen = true;
    expect(talk(s, 'woman')[0]).toMatch(/空がこんなに青かった/);
  });

  it('the smith forges the 星鋼の剣 from three crystals — with the hands full, he says to come back', () => {
    const s = world();
    talk(s, 'smith', [0]);
    addItem(s.progress.inv, 'murk_crystal', 3);
    while (s.progress.inv.weapons.length < ITEMS.limits.weapons) addItem(s.progress.inv, 'wood_sword');
    expect(conditionHolds(s, { slots: 'weapon', is: false })).toBe(true);
    const said = talk(s, 'smith');
    expect(said.join('')).toMatch(/手がいっぱい/);
    expect(said.join('')).not.toMatch(/打ち上がった/); // he does not say he hands it over
    expect(questState(s, 'murk_steel')).toBe('ready'); // nothing lost: the crystals are still in the bag
    expect(s.progress.inv.items.murk_crystal).toBe(3);
    // (and completing it some other way never loses the sword either)
    expect(completeQuest(s, 'murk_steel')).toBe(false);
    expect(s.events.some((e) => e.type === 'full' && e.item === 'star_steel_sword')).toBe(true);
    s.progress.inv.weapons.pop();
    expect(talk(s, 'smith').join('')).toMatch(/打ち上がった/);
    expect(questState(s, 'murk_steel')).toBe('done');
    expect(s.progress.inv.weapons.at(-1)).toMatchObject({ id: 'star_steel_sword', dur: 45, lvl: 0 });
    expect(s.progress.inv.items.murk_crystal).toBeUndefined();
  });

  it('the traveller: the mirror lake legend (a landmark), and the reward', () => {
    const s = world();
    expect(talk(s, 'traveller', [1])).toContain('そうですか。旅は、足の向くままが一番です。');
    expect(talk(s, 'traveller', [0])[0]).toMatch(/鏡湖には言い伝え/);
    s.progress.landmarks.push('mirror_lake');
    const arrows = s.progress.inv.items.arrow ?? 0;
    talk(s, 'traveller');
    expect(questState(s, 'mirror_tale')).toBe('done');
    expect(s.progress.inv.items.arrow).toBe(arrows + 15);
    expect(s.progress.inv.money).toBeGreaterThanOrEqual(100);
  });

  it('the elder tells the legend once, after she has been met (and his errand still goes on)', () => {
    const s = world();
    talk(s, 'elder', [1]); // また今度
    s.progress.flags.princess_met = true;
    expect(talk(s, 'elder')[0]).toMatch(/新月の夜の星のように/);
    expect(s.progress.flags.elder_legend).toBe(true);
    expect(talk(s, 'elder', [0])[0]).toMatch(/困っておって/);
    expect(questState(s, 'lost_charm')).toBe('active');
  });

  it('the guard points to the beach until she is met; the child cheers a purified core', () => {
    const s = world();
    s.progress.quests.windmill_watch = 'done';
    expect(talk(s, 'guard')[0]).toMatch(/青く光る/);
    s.progress.flags.princess_met = true;
    expect(talk(s, 'guard')[0]).toMatch(/今日も村は平和だ/);
    withCores(s, 1);
    expect(talk(s, 'guard')[0]).toMatch(/霧が薄くなった/);
    talk(s, 'child');
    expect(talk(s, 'child')[0]).toMatch(/やっつけた/);
  });

  it('after the ending, a villager met for the first time speaks of the clear sky — and still asks the favour', () => {
    const quests = { elder: 'lost_charm', cook: 'meat_for_cook', guard: 'windmill_watch', woman: 'forest_mushrooms', smith: 'murk_steel', traveller: 'mirror_tale' };
    const firstBefore = {};
    for (const id of Object.keys(quests)) firstBefore[id] = talk(world(), id, [1])[0];
    for (const [id, q] of Object.entries(quests)) {
      const s = world();
      Object.assign(s.progress.flags, { princess_met: true, ending_seen: true, regalia_kept: true });
      const said = talk(s, id, [0]);
      expect(said[0], id).not.toBe(firstBefore[id]);
      expect(said.join(''), id).toMatch(/霧|晴れ/);
      expect(questState(s, q), id).toBe('active');
    }
    // the elder no longer asks which guardian you are once she is back
    const s = world();
    Object.assign(s.progress.flags, { princess_met: true, elder_met: true, ending_seen: true });
    expect(talk(s, 'elder', [1]).join('')).not.toMatch(/どっちかのう/);
    // and the merchant and the child have their own words after it too
    expect(talk(s, 'merchant', [1])[0]).toMatch(/霧が晴れて/);
    expect(talk(s, 'child')[0]).toMatch(/銀の髪/);
  });

  it('after the ending the cook treats you once', () => {
    const s = world();
    Object.assign(s.progress.flags, { ending_seen: true });
    s.progress.quests.meat_for_cook = 'done';
    talk(s, 'cook');
    expect(s.progress.inv.items.hunter_stew).toBe(1);
    talk(s, 'cook');
    expect(s.progress.inv.items.hunter_stew).toBe(1);
  });

  it('the 星鋼の剣 is a weapon like the others (data checked with the items)', () => {
    const sword = ITEMS.items.find((i) => i.id === 'star_steel_sword');
    expect(sword).toMatchObject({ type: 'weapon', damage: 2, durability: 45, price: 160 });
  });

  it('completing directly is the same as through the dialogue', () => {
    const s = world();
    s.progress.quests.mirror_tale = 'active';
    expect(completeQuest(s, 'mirror_tale')).toBe(false);
    s.progress.landmarks.push('mirror_lake');
    expect(completeQuest(s, 'mirror_tale')).toBe(true);
  });
});

describe('C8: notices', () => {
  it('a new game is marked as one of the story; loading it shows nothing', () => {
    const s = world();
    markNewGame(s);
    expect(noticeOnLoad(s)).toBe(null);
  });

  it('an old save without the princess: once, whatever the cores', () => {
    for (const n of [0, 2, 4]) {
      const s = world();
      applyProgress(s, { ...emptyProgress(), bosses: CORES.slice(0, n) });
      expect(noticeOnLoad(s)).toBe(NOTICE.oldSave);
      expect(s.progress.flags[STORY_FLAG]).toBe(true);
      expect(noticeOnLoad(s)).toBe(null);
    }
    const met = world();
    applyProgress(met, { ...emptyProgress(), flags: { princess_met: true } });
    expect(noticeOnLoad(met)).toBe(null);
  });

  it('the fourth core, with her quest not reported (or never taken)', () => {
    const s = world();
    withCores(s, 3);
    expect(noticeOnCore(s)).toBe(null);
    withCores(s, 4);
    expect(noticeOnCore(s)).toBe(NOTICE.allCores);
    s.progress.quests.star_ring_call = 'active';
    expect(noticeOnCore(s)).toBe(NOTICE.allCores);
    s.progress.quests.star_ring_call = 'done';
    expect(noticeOnCore(s)).toBe(null);
  });
});

// ---- C15: no quest can get stuck (the proposal's locksim, with who is there at the time) ----

/** A light state for talking (talk.js reads only these). */
const light = (progress) => ({ progress, events: [], tick: 0, dialogue: null, shop: null, saveRequested: false });
const clone = (s) => ({ ...light(structuredClone(s.progress)), dialogue: s.dialogue && { ...s.dialogue } });

/** Every way a conversation can go (each answer of each question): the progress after each. */
function outcomes(progress, dialogueId) {
  const out = [];
  const run = (s) => {
    for (let k = 0; k < 60 && s.dialogue; k++) {
      const v = dialogueView(s);
      if (v.choices) {
        for (let c = 0; c < v.choices.length; c++) {
          const t = clone(s);
          advance(t, c);
          run(t);
        }
        return;
      }
      advance(s);
    }
    out.push(s.progress);
  };
  const s = light(structuredClone(progress));
  startDialogue(s, dialogueId);
  run(s);
  return out;
}

/** The dialogues of the villagers there now (their appearance conditions). */
const present = (progress) => [...new Set(WORLD.npcs.filter((n) => npcPresent(light(progress), n)).map((n) => n.dialogue))];

/** Whether some sequence of up to `depth` conversations with people who are there reaches `goal`. */
function reachable(progress, goal, depth = 3) {
  let frontier = [progress];
  const seen = new Set([JSON.stringify(progress)]);
  for (let d = 0; d < depth; d++) {
    const next = [];
    for (const p of frontier) {
      for (const dlg of present(p)) {
        for (const q of outcomes(p, dlg)) {
          if (goal(light(q))) return true;
          const key = JSON.stringify(q);
          if (seen.has(key)) continue;
          seen.add(key);
          next.push(q);
        }
      }
    }
    frontier = next;
  }
  return false;
}

/** Story phases (flags and the princess's quests): before / after the gate, the choice, the ending. */
const PHASES = [
  { name: 'new game', flags: {}, quests: {} },
  { name: 'met, not taken', flags: { princess_met: true }, quests: {} },
  { name: 'her quest taken', flags: { princess_met: true }, quests: { star_ring_call: 'active' } },
  { name: 'gate open', flags: { princess_met: true, source_open: true }, quests: { star_ring_call: 'done', source_of_murk: 'active' } },
  { name: 'source purified', flags: { princess_met: true, source_open: true, source_purified: true }, quests: { star_ring_call: 'done', source_of_murk: 'active' } },
  { name: 'joined', flags: { princess_met: true, source_open: true, source_purified: true, regalia_joined: true }, quests: { star_ring_call: 'done', source_of_murk: 'done' } },
  { name: 'kept', flags: { princess_met: true, source_open: true, source_purified: true, regalia_kept: true }, quests: { star_ring_call: 'done', source_of_murk: 'done' } },
  { name: 'after, joined', flags: { princess_met: true, source_open: true, source_purified: true, regalia_joined: true, ending_seen: true }, quests: { star_ring_call: 'done', source_of_murk: 'done' } },
  { name: 'after, kept', flags: { princess_met: true, source_open: true, source_purified: true, regalia_kept: true, ending_seen: true }, quests: { star_ring_call: 'done', source_of_murk: 'done' } },
];
const SIDE = ['lost_charm', 'meat_for_cook', 'windmill_watch', 'forest_mushrooms', 'murk_steel', 'mirror_tale'];
const MET = ['elder_met', 'woman_met', 'smith_met', 'traveller_met', 'child_told'];

/** Makes a quest's goal met in a progress. */
function meetGoal(p, id) {
  const g = TALK_DATA.quests.quests.find((q) => q.id === id).goal;
  if (g.type === 'item') addItem(p.inv, g.item, g.count);
  if (g.type === 'landmark') p.landmarks.push(g.landmark);
  if (g.type === 'flag') p.flags[g.flag] = true;
  if (g.type === 'cores') p.bosses = CORES.slice(0, g.count);
}

function situation(phase, cores, extraFlags) {
  const p = emptyProgress();
  Object.assign(p.flags, phase.flags, extraFlags);
  Object.assign(p.quests, phase.quests);
  p.bosses = CORES.slice(0, cores);
  return p;
}

describe('C15: no quest gets stuck, with who is there at the time (every phase × cores 0..4)', () => {
  it('every side quest: not taken → its giver is there and gives it; ready → it can be reported', () => {
    const stuck = [];
    let checked = 0;
    for (const phase of PHASES) {
      for (let cores = 0; cores <= 4; cores++) {
        for (const met of [false, true]) {
          for (const legend of [false, true]) {
            const extra = { ...(met ? Object.fromEntries(MET.map((f) => [f, true])) : {}), ...(legend ? { elder_legend: true } : {}) };
            for (const id of SIDE) {
              const fresh = situation(phase, cores, extra);
              checked++;
              if (!reachable(fresh, (s) => questState(s, id) !== 'none')) stuck.push(`${phase.name}/${cores}/${met}/${legend}: cannot take ${id}`);
              const ready = situation(phase, cores, { ...extra, ...Object.fromEntries(MET.map((f) => [f, true])) });
              ready.quests[id] = 'active';
              meetGoal(ready, id);
              checked++;
              if (!reachable(ready, (s) => questState(s, id) === 'done')) stuck.push(`${phase.name}/${cores}/${met}/${legend}: cannot report ${id}`);
            }
          }
        }
      }
    }
    expect(stuck).toEqual([]);
    expect(checked).toBe(PHASES.length * 5 * 4 * SIDE.length * 2);
  });

  it('「星環の呼び声」: before it is taken a 写し身 is there to give it (any cores, old saves too); with four cores it can be reported', () => {
    const stuck = [];
    for (const phase of PHASES.slice(0, 2)) {
      for (let cores = 0; cores <= 4; cores++) {
        if (!reachable(situation(phase, cores, {}), (s) => questState(s, 'star_ring_call') !== 'none')) stuck.push(`${phase.name}/${cores}: cannot take`);
      }
    }
    const ready = situation(PHASES[2], 4, {});
    if (!reachable(ready, (s) => questState(s, 'star_ring_call') === 'done' && s.progress.flags.source_open && questState(s, 'source_of_murk') === 'active')) stuck.push('cannot report');
    expect(stuck).toEqual([]);
  });

  it('「淀みの源」: once the source is purified the 写し身 are gone, and the ending reports it', () => {
    const p = situation(PHASES[4], 4, {});
    expect(present(p)).not.toContain('princess');
    // The princess who speaks the ending (princess_end, by the source) is placed with the arena
    // (C6 / C10). Until then the dialogue itself is checked; once she is in the world, through her.
    const there = WORLD.npcs.some((n) => n.dialogue === 'ending');
    const done = there
      ? reachable(p, (s) => questState(s, 'source_of_murk') === 'done')
      : outcomes(p, 'ending').every((q) => questState(light(q), 'source_of_murk') === 'done');
    expect(done).toBe(true);
    // A 写し身 talked to just as the source falls has words for it too (wait_end).
    const s = light(structuredClone(p));
    startDialogue(s, 'princess');
    expect(dialogueView(s).text).toMatch(/源のあった所へ/);
  });

  it('every villager there in every situation can be talked to (a start always matches)', () => {
    for (const phase of PHASES) {
      for (let cores = 0; cores <= 4; cores++) {
        const p = situation(phase, cores, {});
        for (const dlg of present(p)) expect(outcomes(p, dlg).length, `${phase.name} ${dlg}`).toBeGreaterThan(0);
      }
    }
  });

  it('the princess is somewhere in every phase (beach / every stone / the village after the ending)', () => {
    for (const [k, phase] of PHASES.entries()) {
      const p = situation(phase, 4, {});
      const princesses = WORLD.npcs.filter((n) => n.id.startsWith('princess_') && npcPresent(light(p), n)).map((n) => n.id);
      if (phase.flags.ending_seen) expect(princesses, phase.name).toEqual(['princess_home']);
      else if (phase.flags.source_purified) {
        expect(princesses, phase.name).toEqual(['princess_end']); // by the source (C10)
        // …and the way to her stays open (the beach ring), until the ending is seen.
        expect(warpOpen(light(p), WORLD.warps.find((w) => w.id === 'source-gate')), phase.name).toBe(true);
      }
      else expect(princesses.length, phase.name).toBe(k === 0 ? 1 : 6);
    }
  });
});
