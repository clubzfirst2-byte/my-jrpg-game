// @ts-check
// Integrity check of what people say and do (P9): dialogue / quest / shop data and the villagers
// placed in the world. Every reference must exist (nodes, quests, items, shops, landmarks) and every
// node must be reachable. Used by unit tests and `npm run check:data`.

const QUEST_STATES = ['none', 'active', 'ready', 'done'];
const COND_KEYS = ['flag', 'is', 'quest', 'state', 'item', 'count', 'money'];
const EFFECT_KEYS = ['setFlag', 'clearFlag', 'startQuest', 'completeQuest', 'giveItem', 'count', 'giveMoney', 'openShop', 'sleep'];

/**
 * @param {{ dialogue: any, quests: any, shops: any, items: any }} data
 * @param {{ npcs?: any[], landmarks?: any[] }} [world]
 * @returns {string[]}
 */
export function validateTalk(data, world = {}) {
  /** @type {string[]} */
  const errors = [];
  const err = (/** @type {string} */ m) => errors.push(m);
  const items = new Set((data.items.items ?? []).map((/** @type {any} */ i) => i.id));
  const quests = new Map((data.quests.quests ?? []).map((/** @type {any} */ q) => [q.id, q]));
  const shops = new Map((data.shops.shops ?? []).map((/** @type {any} */ s) => [s.id, s]));
  const dialogues = data.dialogue.dialogues ?? {};
  const landmarks = new Set((world.landmarks ?? []).map((/** @type {any} */ l) => l.id));

  const checkCond = (/** @type {any} */ c, /** @type {string} */ at) => {
    for (const k of Object.keys(c)) if (!COND_KEYS.includes(k)) err(`${at}: unknown condition "${k}"`);
    if (c.quest !== undefined) {
      if (!quests.has(c.quest)) err(`${at}: unknown quest "${c.quest}"`);
      if (!QUEST_STATES.includes(c.state)) err(`${at}: quest state must be ${QUEST_STATES.join(' / ')}`);
    }
    if (c.item !== undefined && !items.has(c.item)) err(`${at}: unknown item "${c.item}"`);
  };
  const checkEffects = (/** @type {any[]} */ effects, /** @type {string} */ at) => {
    for (const e of effects ?? []) {
      for (const k of Object.keys(e)) if (!EFFECT_KEYS.includes(k)) err(`${at}: unknown effect "${k}"`);
      for (const k of ['startQuest', 'completeQuest']) if (e[k] !== undefined && !quests.has(e[k])) err(`${at}: unknown quest "${e[k]}"`);
      if (e.giveItem !== undefined && !items.has(e.giveItem)) err(`${at}: unknown item "${e.giveItem}"`);
      if (e.openShop !== undefined && !shops.has(e.openShop)) err(`${at}: unknown shop "${e.openShop}"`);
      if (e.sleep !== undefined && !(Number.isInteger(e.sleep) && e.sleep >= 0 && e.sleep < 24)) err(`${at}: sleep must be an hour 0..23`);
    }
  };

  for (const [id, d] of Object.entries(dialogues)) {
    const at = `dialogue ${id}`;
    const nodes = d.nodes ?? {};
    if (typeof d.name !== 'string' || !d.name) err(`${at}: name is required`);
    if (!Array.isArray(d.start) || d.start.length === 0) {
      err(`${at}: start must list at least one entry`);
      continue;
    }
    const lastStart = d.start[d.start.length - 1];
    if (lastStart.if && lastStart.if.length > 0) err(`${at}: the last start entry must have no conditions (a fallback)`);
    /** @type {string[]} */
    const queue = [];
    for (const [k, s] of d.start.entries()) {
      for (const c of s.if ?? []) checkCond(c, `${at}.start[${k}]`);
      if (!nodes[s.goto]) err(`${at}.start[${k}]: unknown node "${s.goto}"`);
      else queue.push(s.goto);
    }
    for (const [nid, n] of Object.entries(nodes)) {
      const nat = `${at}.${nid}`;
      if (!Array.isArray(n.text) || n.text.length === 0 || n.text.some((/** @type {any} */ t) => typeof t !== 'string' || !t)) err(`${nat}: text must be non-empty lines`);
      checkEffects(n.effects, nat);
      if (n.next !== undefined && n.next !== null && !nodes[n.next]) err(`${nat}: unknown next "${n.next}"`);
      if (n.choices !== undefined) {
        if (n.next !== undefined) err(`${nat}: a node has choices or next, not both`);
        if (!Array.isArray(n.choices) || n.choices.length < 2) err(`${nat}: choices need at least two answers`);
        for (const [k, c] of (n.choices ?? []).entries()) {
          if (typeof c.label !== 'string' || !c.label) err(`${nat}.choices[${k}]: label is required`);
          if (c.goto !== undefined && c.goto !== null && !nodes[c.goto]) err(`${nat}.choices[${k}]: unknown node "${c.goto}"`);
          checkEffects(c.effects, `${nat}.choices[${k}]`);
        }
      }
    }
    // Every node is reachable from a start entry.
    const seen = new Set();
    while (queue.length) {
      const nid = /** @type {string} */ (queue.pop());
      if (seen.has(nid) || !nodes[nid]) continue;
      seen.add(nid);
      const n = nodes[nid];
      if (n.next) queue.push(n.next);
      for (const c of n.choices ?? []) if (c.goto) queue.push(c.goto);
    }
    for (const nid of Object.keys(nodes)) if (!seen.has(nid)) err(`${at}.${nid}: unreachable node`);
  }

  const qids = new Set();
  for (const [k, q] of (data.quests.quests ?? []).entries()) {
    const at = `quests[${k}]${q.id ? ` (${q.id})` : ''}`;
    if (qids.has(q.id)) err(`${at}: duplicate id`);
    qids.add(q.id);
    if (!q.name || !q.desc) err(`${at}: name and desc are required`);
    if (!dialogues[q.giver]) err(`${at}: giver "${q.giver}" has no dialogue`);
    const g = q.goal ?? {};
    if (g.type === 'item') {
      if (!items.has(g.item)) err(`${at}.goal: unknown item "${g.item}"`);
      if (!(g.count >= 1)) err(`${at}.goal: count must be at least 1`);
    } else if (g.type === 'landmark') {
      if (world.landmarks && !landmarks.has(g.landmark)) err(`${at}.goal: unknown landmark "${g.landmark}"`);
    } else if (g.type !== 'flag') err(`${at}.goal: type must be item / landmark / flag`);
    for (const id of Object.keys(q.reward?.items ?? {})) if (!items.has(id)) err(`${at}.reward: unknown item "${id}"`);
    // Some dialogue must be able to start and complete it.
    const all = JSON.stringify(dialogues);
    if (!all.includes(`"startQuest":"${q.id}"`)) err(`${at}: no dialogue starts it`);
    if (!all.includes(`"completeQuest":"${q.id}"`)) err(`${at}: no dialogue completes it`);
  }

  for (const s of data.shops.shops ?? []) {
    if (!(s.buyRate >= 0 && s.buyRate <= 1)) err(`shop ${s.id}: buyRate must be 0..1`);
    for (const e of s.sells ?? []) {
      if (!items.has(e.item)) err(`shop ${s.id}: unknown item "${e.item}"`);
      if (!(e.price > 0)) err(`shop ${s.id}: ${e.item} needs a price above 0`);
    }
  }

  const nids = new Set();
  for (const n of world.npcs ?? []) {
    if (nids.has(n.id)) err(`npc ${n.id}: duplicate id`);
    nids.add(n.id);
    if (!dialogues[n.dialogue]) err(`npc ${n.id}: unknown dialogue "${n.dialogue}"`);
  }
  return errors;
}
