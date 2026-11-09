// @ts-check
// Conversations, quests and shops (P9). Everything people say is data (data/dialogue.json): a
// dialogue picks its starting node by conditions (flags, quest states, items), each node shows
// lines, may offer choices, and applies effects (set a flag, start / complete a quest, give items or
// money, open a shop). Quest states are derived: none -> active -> ready (goal met) -> done.
// Pure logic: the UI only shows `dialogueView` and calls `advance`.
import DIALOGUE from '../../../data/dialogue.json';
import QUESTS from '../../../data/quests.json';
import SHOPS from '../../../data/shops.json';
import ITEMS from '../../../data/items.json';
import { addItem, removeItem, countOf, itemDef } from '../items/inventory.js';
import { sleepUntil } from '../world/interiors.js';

export const TALK_DATA = { dialogue: DIALOGUE, quests: QUESTS, shops: SHOPS };

/**
 * @typedef {{ flag?: string, is?: boolean, quest?: string, state?: string, item?: string, count?: number, money?: number, cores?: number, boss?: string, slots?: string }} Condition
 * v1.0 (C2): cores — at least that many cores of the murk purified; boss — that core purified;
 * slots: 'weapon' | 'bow' — a free slot for one more (with is: false, none free).
 */
/** @typedef {{ setFlag?: string, clearFlag?: string, startQuest?: string, completeQuest?: string, giveItem?: string, count?: number, giveMoney?: number, openShop?: string, sleep?: number }} Effect  sleep: until that hour (P10.1) */

/** @param {string} id */
export function questDef(id) {
  const q = QUESTS.quests.find((/** @type {any} */ x) => x.id === id);
  if (!q) throw new Error(`Unknown quest "${id}"`);
  return q;
}

/** Prefix of the four cores of the murk in progress.bosses (the final boss is listed apart, C7). */
export const CORE_PREFIX = 'core_';

/**
 * How many cores of the murk have been purified (counted from the saved bosses, so saves from
 * before v1.0 are right as they are). @param {any} state
 */
export function coresPurified(state) {
  let n = 0;
  for (const id of state.progress.bosses ?? []) if (id.startsWith(CORE_PREFIX)) n++;
  return n;
}

/** Whether there is a free slot for one more weapon / bow (v1.0: the smith's sword). @param {any} inv @param {string} kind */
export function hasFreeSlot(inv, kind) {
  return kind === 'bow' ? inv.bows.length < ITEMS.limits.bows : inv.weapons.length < ITEMS.limits.weapons;
}

/** @param {any} state @param {any} q */
function goalMet(state, q) {
  const g = q.goal;
  const pr = state.progress;
  if (g.type === 'item') return countOf(pr.inv, g.item) >= g.count;
  if (g.type === 'landmark') return pr.landmarks.includes(g.landmark);
  if (g.type === 'flag') return !!pr.flags[g.flag];
  if (g.type === 'cores') return coresPurified(state) >= g.count;
  return false;
}

/**
 * none | active | ready (the goal is met, waiting to be reported) | done
 * @param {any} state @param {string} id
 */
export function questState(state, id) {
  const s = state.progress.quests[id];
  if (s === 'done') return 'done';
  if (s === 'active') return goalMet(state, questDef(id)) ? 'ready' : 'active';
  return 'none';
}

/** @param {any} state @param {Condition} c */
export function conditionHolds(state, c) {
  const pr = state.progress;
  if (c.flag !== undefined) return !!pr.flags[c.flag] === (c.is ?? true);
  if (c.quest !== undefined) return questState(state, c.quest) === c.state;
  if (c.item !== undefined) return countOf(pr.inv, c.item) >= (c.count ?? 1);
  if (c.money !== undefined) return pr.inv.money >= c.money;
  if (c.cores !== undefined) return coresPurified(state) >= c.cores;
  if (c.boss !== undefined) return (pr.bosses ?? []).includes(c.boss);
  if (c.slots !== undefined) return hasFreeSlot(pr.inv, c.slots) === (c.is ?? true);
  return true;
}

/**
 * Applies effects. Returns a shop id when one should open.
 * @param {any} state @param {Effect[]} effects @returns {string | null}
 */
export function applyEffects(state, effects = []) {
  const pr = state.progress;
  let shop = null;
  for (const e of effects) {
    if (e.setFlag) pr.flags[e.setFlag] = true;
    if (e.clearFlag) delete pr.flags[e.clearFlag];
    if (e.startQuest && !pr.quests[e.startQuest]) {
      pr.quests[e.startQuest] = 'active';
      state.events.push({ type: 'questStart', tick: state.tick, id: e.startQuest });
    }
    if (e.completeQuest) completeQuest(state, e.completeQuest);
    if (e.giveItem) addItem(pr.inv, e.giveItem, e.count ?? 1);
    if (e.giveMoney) pr.inv.money += e.giveMoney;
    if (e.openShop) shop = e.openShop;
    if (e.sleep !== undefined) sleepUntil(state, e.sleep);
  }
  if (effects.length > 0) state.saveRequested = true;
  return shop;
}

/**
 * Whether a quest's gear reward (a weapon or a bow, v1.0: the smith's 星鋼の剣) has a free slot.
 * Returns the first that does not fit, or null. @param {any} inv @param {any} q @returns {string | null}
 */
function gearThatDoesNotFit(inv, q) {
  for (const [item, n] of Object.entries(q.reward.items ?? {})) {
    const type = itemDef(item).type;
    if (type !== 'weapon' && type !== 'bow') continue;
    const list = type === 'weapon' ? inv.weapons : inv.bows;
    const max = type === 'weapon' ? ITEMS.limits.weapons : ITEMS.limits.bows;
    if (list.length + /** @type {number} */ (n) > max) return item;
  }
  return null;
}

/**
 * Completes a quest whose goal is met: takes the items (when `consume`), gives the reward. A gear
 * reward with no free slot is not lost: the quest stays ready (like a chest that stays shut, P6)
 * and a `full` event says why.
 * @param {any} state @param {string} id @returns {boolean}
 */
export function completeQuest(state, id) {
  if (questState(state, id) !== 'ready') return false;
  const q = questDef(id);
  const inv = state.progress.inv;
  const full = gearThatDoesNotFit(inv, q);
  if (full) {
    state.events.push({ type: 'full', tick: state.tick, item: full });
    return false;
  }
  if (q.consume && q.goal.type === 'item') removeItem(inv, q.goal.item, q.goal.count);
  inv.money += q.reward.money ?? 0;
  for (const [item, n] of Object.entries(q.reward.items ?? {})) addItem(inv, item, /** @type {number} */ (n));
  state.progress.quests[id] = 'done';
  state.events.push({ type: 'questDone', tick: state.tick, id });
  return true;
}

/**
 * Starts talking with someone. The first start entry whose conditions all hold is used.
 * @param {any} state @param {string} dialogueId @param {string} [npcId]
 */
export function startDialogue(state, dialogueId, npcId) {
  const d = /** @type {any} */ (DIALOGUE.dialogues)[dialogueId];
  if (!d) throw new Error(`Unknown dialogue "${dialogueId}"`);
  const entry = d.start.find((/** @type {any} */ s) => (s.if ?? []).every((/** @type {Condition} */ c) => conditionHolds(state, c)));
  state.dialogue = { id: dialogueId, npc: npcId ?? null, node: entry.goto, line: 0 };
  // The world waits while they talk, so the villager stops at once (else drawn mid-stride until the end).
  const n = npcId ? state.npcs?.find((/** @type {any} */ x) => x.id === npcId) : null;
  if (n) n.moving = false;
  enterNode(state);
  state.events.push({ type: 'talk', tick: state.tick, id: dialogueId });
}

/** Applies the effects of the node just entered. @param {any} state */
function enterNode(state) {
  const dlg = state.dialogue;
  const node = /** @type {any} */ (DIALOGUE.dialogues)[dlg.id].nodes[dlg.node];
  const shop = applyEffects(state, node.effects);
  if (shop) state.shop = shop;
}

/**
 * What the dialogue box shows now (null when nobody is talking).
 * @param {any} state
 * @returns {{ speaker: string, text: string, choices: string[] | null, last: boolean } | null}
 */
export function dialogueView(state) {
  const dlg = state.dialogue;
  if (!dlg) return null;
  const d = /** @type {any} */ (DIALOGUE.dialogues)[dlg.id];
  const node = d.nodes[dlg.node];
  const last = dlg.line >= node.text.length - 1;
  return { speaker: d.name, text: node.text[dlg.line], choices: last && node.choices ? node.choices.map((/** @type {any} */ c) => c.label) : null, last };
}

/**
 * Next line, or the chosen answer. Ends the conversation when there is nothing more.
 * @param {any} state @param {number} [choice]
 */
export function advance(state, choice) {
  const dlg = state.dialogue;
  if (!dlg) return;
  const d = /** @type {any} */ (DIALOGUE.dialogues)[dlg.id];
  const node = d.nodes[dlg.node];
  if (dlg.line < node.text.length - 1) {
    dlg.line++;
    return;
  }
  /** @type {string | null | undefined} */
  let next = node.next;
  if (node.choices) {
    if (choice === undefined) return; // the box waits for an answer
    const c = node.choices[choice];
    if (!c) return;
    const shop = applyEffects(state, c.effects);
    if (shop) state.shop = shop;
    next = c.goto;
  }
  if (!next) {
    state.dialogue = null;
    return;
  }
  dlg.node = next;
  dlg.line = 0;
  enterNode(state);
}

/** @param {string} id */
export function shopDef(id) {
  const s = SHOPS.shops.find((/** @type {any} */ x) => x.id === id);
  if (!s) throw new Error(`Unknown shop "${id}"`);
  return s;
}

/**
 * Buys `n` of an item the shop sells. @param {any} state @param {string} shopId @param {string} item @param {number} [n]
 * @returns {'ok' | 'money' | 'full' | 'none'}
 */
export function buy(state, shopId, item, n = 1) {
  const entry = shopDef(shopId).sells.find((/** @type {any} */ s) => s.item === item);
  if (!entry) return 'none';
  const inv = state.progress.inv;
  const cost = entry.price * n;
  if (inv.money < cost) return 'money';
  if (addItem(inv, item, n) < n) return 'full';
  inv.money -= cost;
  state.saveRequested = true;
  return 'ok';
}

/** What a shop pays for one of an item (key items are not for sale). @param {string} shopId @param {string} item */
export function sellPrice(shopId, item) {
  const d = itemDef(item.split(':')[0]);
  if (d.type === 'key') return 0;
  return Math.max(1, Math.floor((d.price ?? 0) * shopDef(shopId).buyRate));
}

/**
 * Sells one stackable item (materials, food, ammo, armor not worn).
 * @param {any} state @param {string} shopId @param {string} item
 * @returns {'ok' | 'none' | 'worn' | 'key'}
 */
export function sell(state, shopId, item) {
  const inv = state.progress.inv;
  if (sellPrice(shopId, item) === 0) return 'key';
  if (countOf(inv, item) === 0) return 'none';
  const worn = ['head', 'body', 'legs'].some((s) => inv.equip[s] === item) && countOf(inv, item) === 1;
  if (worn) return 'worn';
  removeItem(inv, item);
  inv.money += sellPrice(shopId, item);
  state.saveRequested = true;
  return 'ok';
}

/** The quests to show in the log (started ones). @param {any} state */
export function questLog(state) {
  return QUESTS.quests
    .filter((/** @type {any} */ q) => state.progress.quests[q.id])
    .map((/** @type {any} */ q) => ({ id: q.id, name: q.name, desc: q.desc, state: questState(state, q.id) }));
}
