// @ts-check
// Inventory menu (P6): weapons, bows, armor, materials, dishes; cooking at a fire and the forge
// at the anvil. DOM + CSS (DESIGN.md 5.8). The game is paused while it is open.
import {
  itemDef,
  baseId,
  healOf,
  equipGear,
  equipArmor,
  eatStack,
  cook,
  cookResult,
  upgradeWeapon,
  repairGear,
  nextUpgrade,
  repairCost,
  canAfford,
  ITEMS,
  useShard,
  countOf,
  SHARD,
} from '../game/items/inventory.js';
import { ABILITY_NAMES } from '../game/puzzles/abilities.js';
import { questLog } from '../game/npc/talk.js';
import { scrollCue } from './scrollCue.js';

/** @typedef {'weapon' | 'bow' | 'armor' | 'material' | 'food' | 'power' | 'quest' | 'cook' | 'forge'} Tab */

const TAB_NAMES = /** @type {Record<Tab, string>} */ ({
  weapon: '武器',
  bow: '弓',
  armor: '防具',
  material: '素材',
  food: '料理',
  power: '能力',
  quest: 'クエスト',
  cook: '鍋',
  forge: '鍛冶',
});

const EFFECT_NAMES = /** @type {Record<string, string>} */ ({
  stamina: 'がんばりが回復',
  attackUp: '攻撃力アップ',
  defenseUp: '防御力アップ',
  fireproof: '炎に強くなる',
});

export class InventoryMenu {
  /**
   * @param {HTMLElement} root
   * @param {{ getState: () => any, onOpen: () => void, onClose: () => void, toast: (msg: string) => void, talk?: () => void }} hooks
   */
  constructor(root, hooks) {
    this.hooks = hooks;
    /** @type {Tab} */
    this.tab = 'weapon';
    /** @type {string[]} ingredients chosen in the pot */
    this.pot = [];

    this.bagButton = button('bag-button', '持ち物', () => this.open());
    // The station (fire / anvil) is decided when the button is pressed: the game is paused while the
    // menu is open, so the player is still there.
    this.useButton = button('use-button', '', () => (this.useKind === 'talk' || this.useKind === 'sleep' ? this.hooks.talk?.() : this.open(this.useTab, true)));
    /** @type {'cook' | 'forge' | 'talk' | 'sleep'} what the button does now */
    this.useKind = 'cook';
    /** @type {Tab | null} cooking / forge tab available in this opening of the menu */
    this.station = null;
    this.useButton.hidden = true;
    /** @type {Tab} */
    this.useTab = 'cook';

    this.el = document.createElement('div');
    this.el.id = 'inv-menu';
    this.el.hidden = true;
    this.head = document.createElement('div');
    this.head.className = 'inv-head';
    this.money = document.createElement('div');
    this.money.className = 'inv-money';
    this.tabs = document.createElement('div');
    this.tabs.className = 'inv-tabs';
    const close = button('inv-close', '閉じる', () => this.close());
    this.head.append(this.tabs, this.money, close);
    this.body = document.createElement('div');
    this.body.className = 'inv-body';
    this.el.append(this.head, this.body);
    root.append(this.bagButton, this.useButton, this.el);
    this.cue = scrollCue(this.el, () => this.body);
  }

  get isOpen() {
    return !this.el.hidden;
  }

  /** Shows the "料理する / 鍛冶 / 話す / 眠る" button when something usable is in reach. @param {'cook' | 'forge' | 'talk' | 'sleep' | null} nearby @param {string} [who] */
  setNearby(nearby, who = '') {
    // Called every frame: touch the DOM only when something changes. Rewriting the label every
    // frame replaces its text node, and WebKit (iPhone Safari) can then drop a tap on the button.
    const hidden = !nearby || this.isOpen;
    if (this.useButton.hidden !== hidden) this.useButton.hidden = hidden;
    if (nearby) this.useKind = nearby;
    if ((nearby === 'cook' || nearby === 'forge') && nearby !== this.useTab) this.useTab = nearby;
    const label = this.useKind === 'talk' ? `話す（${who}）` : this.useKind === 'sleep' ? '眠る' : this.useTab === 'cook' ? '料理する' : '鍛冶';
    if (this.useButton.textContent !== label) this.useButton.textContent = label;
  }

  /** @param {Tab} [tab] @param {boolean} [atStation] opened from the "料理する / 鍛冶" button */
  open(tab, atStation = false) {
    const s = this.hooks.getState();
    this.station = atStation && tab ? tab : s.nearby;
    if (tab) this.tab = tab;
    if ((this.tab === 'cook' || this.tab === 'forge') && this.station !== this.tab) this.tab = 'weapon';
    this.pot = [];
    this.el.hidden = false;
    this.useButton.hidden = true;
    this.hooks.onOpen();
    this.render();
  }

  close() {
    this.el.hidden = true;
    this.hooks.onClose();
  }

  toggle() {
    if (this.isOpen) this.close();
    else this.open();
  }

  /** Draws the menu, then updates its "more below" cue. */
  render() {
    this.renderContent();
    this.cue();
  }

  renderContent() {
    const s = this.hooks.getState();
    const inv = s.progress.inv;
    this.money.textContent = `★ ${inv.money} 星貨`;
    /** @type {Tab[]} */
    const tabs = ['weapon', 'bow', 'armor', 'material', 'food', 'power', 'quest'];
    if (this.station === 'cook') tabs.push('cook');
    if (this.station === 'forge') tabs.push('forge');
    this.tabs.replaceChildren(
      ...tabs.map((t) => {
        const b = button(`inv-tab-${t}`, TAB_NAMES[t], () => {
          this.tab = t;
          this.render();
        });
        b.classList.toggle('active', t === this.tab);
        return b;
      }),
    );
    this.body.replaceChildren();
    const list = document.createElement('div');
    list.className = 'inv-list';
    this.body.append(list);
    const empty = (/** @type {string} */ text) => {
      const p = document.createElement('p');
      p.className = 'inv-empty';
      p.textContent = text;
      list.append(p);
    };

    switch (this.tab) {
      case 'weapon':
      case 'bow': {
        const kind = this.tab;
        const gear = kind === 'weapon' ? inv.weapons : inv.bows;
        if (kind === 'bow') empty(`矢 ×${inv.items.arrow ?? 0}`);
        if (gear.length === 0) empty(kind === 'weapon' ? '武器を持っていない（素手で戦う）' : '弓を持っていない');
        gear.forEach((/** @type {any} */ g, /** @type {number} */ i) => {
          const d = itemDef(g.id);
          const on = inv.equip[kind] === i;
          list.append(
            row(`inv-${kind}-${i}`, `${on ? '◆ ' : ''}${d.name}${g.lvl ? ` +${g.lvl}` : ''}`, `耐久 ${g.dur}/${d.durability}  ${d.desc}`, on, () => {
              equipGear(inv, kind, i);
              this.render();
            }),
          );
        });
        break;
      }
      case 'armor': {
        const owned = Object.keys(inv.items).filter((id) => itemDef(baseId(id)).type === 'armor');
        if (owned.length === 0) empty('防具を持っていない');
        for (const id of owned) {
          const d = itemDef(id);
          const on = inv.equip[d.slot] === id;
          const slot = { head: '頭', body: '胴', legs: '足' }[/** @type {'head' | 'body' | 'legs'} */ (d.slot)];
          list.append(
            row(`inv-armor-${id}`, `${on ? '◆ ' : ''}${d.name}（${slot}）`, `防御 ${d.defense}  ${d.desc}`, on, () => {
              equipArmor(inv, id);
              this.render();
            }),
          );
        }
        break;
      }
      case 'material':
      case 'food': {
        const type = this.tab;
        const ids = Object.keys(inv.items).filter((id) => itemDef(baseId(id)).type === type);
        if (ids.length === 0) empty(type === 'food' ? '料理を持っていない（たき火で作れる）' : '素材を持っていない');
        for (const id of ids) {
          const d = itemDef(baseId(id));
          const heal = healOf(id);
          const effect = d.effect ? `・${EFFECT_NAMES[d.effect.kind]}` : '';
          const canEat = heal > 0 || !!d.effect;
          list.append(
            row(`inv-item-${id.replace(':', '-')}`, `${d.name} ×${inv.items[id]}`, `${canEat ? `食べる：回復 ${heal / 4} ハート${effect}  ` : ''}${d.desc}`, false, canEat ? () => this.eat(id) : null),
          );
        }
        break;
      }
      case 'power':
        this.renderPower(list, s);
        break;
      case 'quest': {
        const log = questLog(s);
        if (log.length === 0) empty('受けているクエストはない（村の人と話してみよう）');
        const STATE = /** @type {Record<string, string>} */ ({ active: '進行中', ready: '報告できる', done: '達成' });
        for (const q of log) list.append(row(`inv-quest-${q.id}`, `${q.state === 'done' ? '✓ ' : ''}${q.name}（${STATE[q.state]}）`, q.desc, q.state === 'ready', null));
        break;
      }
      case 'cook':
        this.renderCook(list, inv);
        break;
      case 'forge':
        this.renderForge(list, inv);
        break;
      default:
    }
  }

  /** @param {string} id */
  eat(id) {
    const s = this.hooks.getState();
    const name = itemDef(baseId(id)).name;
    const r = eatStack(s.progress.inv, id, s.player, s.env.now);
    if (r) this.hooks.toast(`${name}を食べた${r.heal ? `（${r.heal / 4} ハート回復）` : ''}${r.effect ? `  ${EFFECT_NAMES[r.effect]}` : ''}`);
    this.render();
  }

  /** 星環 abilities (choose the one for the button) and star shards (P7). @param {HTMLElement} list @param {any} s */
  renderPower(list, s) {
    const pr = s.progress;
    const DESC = /** @type {Record<string, string>} */ ({
      light: '光の玉を浮かべる。暗い所を照らし、光で動く仕掛けを動かす',
      telekinesis: '前にある鉄の箱を、ぶつかるまで滑らせる',
      vine: '前の水や穴に蔓の足場を作る（6 つまで・燃える）',
      resonance: '周りの共鳴石を響かせる（壁ごしでも届く）',
    });
    if (pr.abilities.length === 0) {
      const p = document.createElement('p');
      p.className = 'inv-empty';
      p.textContent = '星環の力をまだ持っていない（光る石柱の試練や、塔の上の祭壇で得られる）';
      list.append(p);
    }
    for (const id of pr.abilities) {
      const on = pr.ability === id;
      list.append(
        row(`inv-power-${id}`, `${on ? '◆ ' : ''}${ABILITY_NAMES[id]}`, DESC[id] ?? '', on, () => {
          pr.ability = id;
          this.render();
        }),
      );
    }
    const n = countOf(pr.inv, 'star_shard');
    const line = row('inv-shards', `星の欠片 ×${n}`, `1 つで ハート +1（最大 ${SHARD.maxHearts}）か がんばり +${SHARD.stamina}（最大 ${SHARD.maxStamina}）`, false, null);
    const actions = document.createElement('div');
    actions.className = 'inv-actions';
    for (const [kind, label] of /** @type {const} */ ([['heart', 'ハート +1'], ['stamina', 'がんばり +']])) {
      const b = button(`inv-shard-${kind}`, label, () => {
        if (useShard(pr, s.player, kind)) this.hooks.toast(kind === 'heart' ? 'ハートが 1 つ増えた！' : 'がんばりが増えた！');
        this.render();
      });
      b.disabled = n === 0;
      actions.append(b);
    }
    line.append(actions);
    list.append(line);
  }

  /** @param {HTMLElement} list @param {any} inv */
  renderCook(list, inv) {
    const pot = document.createElement('div');
    pot.className = 'inv-pot';
    const label = document.createElement('span');
    label.textContent = '鍋：';
    pot.append(label);
    this.pot.forEach((id, k) => {
      pot.append(
        button(`inv-pot-${k}`, itemDef(id).name, () => {
          this.pot.splice(k, 1);
          this.render();
        }),
      );
    });
    if (this.pot.length > 0) {
      const { result } = cookResult(this.pot);
      const known = inv.recipes.includes(result);
      const hint = document.createElement('span');
      hint.className = 'inv-hint';
      hint.textContent = `→ ${known ? itemDef(result).name : '？？？'}`;
      pot.append(
        hint,
        button('inv-cook', '料理する', () => {
          const r = cook(inv, this.pot);
          if (r) this.hooks.toast(`${r.name}ができた！${r.discovered ? '（新しいレシピ）' : ''}`);
          this.pot = [];
          this.render();
        }),
      );
    }
    list.append(pot);
    const mats = Object.keys(inv.items).filter((id) => itemDef(baseId(id)).type === 'material');
    if (mats.length === 0) {
      const p = document.createElement('p');
      p.className = 'inv-empty';
      p.textContent = '素材がない';
      list.append(p);
    }
    for (const id of mats) {
      const used = this.pot.filter((x) => x === id).length;
      const left = inv.items[id] - used;
      list.append(
        row(`inv-add-${id}`, `${itemDef(id).name} ×${left}`, '鍋に入れる（3 つまで）', false, left > 0 && this.pot.length < 3 ? () => {
          this.pot.push(id);
          this.render();
        } : null),
      );
    }
    const known = ITEMS.recipes.filter((/** @type {any} */ r) => inv.recipes.includes(r.result));
    const book = document.createElement('p');
    book.className = 'inv-empty';
    book.textContent = `覚えたレシピ：${known.length === 0 ? 'なし' : known.map((/** @type {any} */ r) => `${itemDef(r.result).name}（${r.ingredients.map((/** @type {string} */ i) => itemDef(i).name).join('＋')}）`).join('、')}`;
    list.append(book);
  }

  /** @param {HTMLElement} list @param {any} inv */
  renderForge(list, inv) {
    if (inv.weapons.length === 0 && inv.bows.length === 0) {
      const p = document.createElement('p');
      p.className = 'inv-empty';
      p.textContent = '鍛えるものがない';
      list.append(p);
    }
    inv.weapons.forEach((/** @type {any} */ g, /** @type {number} */ i) => {
      const d = itemDef(g.id);
      const up = nextUpgrade(g);
      const cost = up ? `${up.money} 星貨${Object.entries(up.materials ?? {}).map(([id, n]) => `・${itemDef(id).name}×${n}`).join('')}` : '';
      const line = row(`inv-forge-${i}`, `${d.name}${g.lvl ? ` +${g.lvl}` : ''}`, `耐久 ${g.dur}/${d.durability}${up ? `  強化（+${up.level}）：${cost}` : '  これ以上は強化できない'}`, false, null);
      const actions = document.createElement('div');
      actions.className = 'inv-actions';
      const upB = button(`inv-upgrade-${i}`, '強化', () => {
        const r = upgradeWeapon(inv, i);
        this.hooks.toast(r === 'ok' ? `${d.name}を +${g.lvl} に鍛えた` : r === 'cost' ? '星貨か素材が足りない' : 'これ以上は強化できない');
        this.render();
      });
      upB.disabled = !up || !canAfford(inv, up);
      const rc = repairCost(g);
      const fix = button(`inv-repair-${i}`, rc > 0 ? `修理 ${rc}` : '修理', () => {
        const r = repairGear(inv, 'weapon', i);
        this.hooks.toast(r === 'ok' ? `${d.name}を直した` : r === 'cost' ? '星貨が足りない' : '傷んでいない');
        this.render();
      });
      fix.disabled = rc === 0 || inv.money < rc;
      actions.append(upB, fix);
      line.append(actions);
      list.append(line);
    });
    inv.bows.forEach((/** @type {any} */ g, /** @type {number} */ i) => {
      const d = itemDef(g.id);
      const rc = repairCost(g);
      const line = row(`inv-forge-bow-${i}`, d.name, `耐久 ${g.dur}/${d.durability}`, false, null);
      const fix = button(`inv-repair-bow-${i}`, rc > 0 ? `修理 ${rc}` : '修理', () => {
        const r = repairGear(inv, 'bow', i);
        this.hooks.toast(r === 'ok' ? `${d.name}を直した` : r === 'cost' ? '星貨が足りない' : '傷んでいない');
        this.render();
      });
      fix.disabled = rc === 0 || inv.money < rc;
      line.append(fix);
      list.append(line);
    });
  }
}

/** @param {string} id @param {string} text @param {() => void} onClick */
function button(id, text, onClick) {
  const b = document.createElement('button');
  b.type = 'button';
  b.id = id;
  b.textContent = text;
  b.addEventListener('click', onClick);
  return b;
}

/**
 * @param {string} id @param {string} title @param {string} detail @param {boolean} active
 * @param {(() => void) | null} onClick
 */
function row(id, title, detail, active, onClick) {
  const el = document.createElement('div');
  el.className = `inv-row${active ? ' active' : ''}`;
  el.id = id;
  const t = document.createElement('div');
  t.className = 'inv-row-title';
  t.textContent = title;
  const d = document.createElement('div');
  d.className = 'inv-row-detail';
  d.textContent = detail;
  el.append(t, d);
  if (onClick) {
    el.classList.add('clickable');
    el.setAttribute('role', 'button');
    el.addEventListener('click', onClick);
  }
  return el;
}
