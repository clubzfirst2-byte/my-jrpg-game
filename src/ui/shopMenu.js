// @ts-check
// The shop (P9): buy what the shop sells with 星貨, or sell from the bag at half price.
import { itemDef, baseId } from '../game/items/inventory.js';
import { shopDef, buy, sell, sellPrice } from '../game/npc/talk.js';
import { itemIconElement } from '../view/assets/objectsArt.js';

export class ShopMenu {
  /**
   * @param {HTMLElement} root
   * @param {{ getState: () => any, onClose: () => void, toast: (msg: string) => void }} hooks
   */
  constructor(root, hooks) {
    this.hooks = hooks;
    /** @type {'buy' | 'sell'} */
    this.tab = 'buy';
    this.el = document.createElement('div');
    this.el.id = 'shop-menu';
    this.el.hidden = true;
    root.append(this.el);
  }

  get isOpen() {
    return !this.el.hidden;
  }

  open() {
    this.tab = 'buy';
    this.el.hidden = false;
    this.render();
  }

  close() {
    this.el.hidden = true;
    this.hooks.onClose();
  }

  render() {
    const s = this.hooks.getState();
    const shopId = s.shop;
    if (!shopId) return;
    const shop = shopDef(shopId);
    const inv = s.progress.inv;
    const head = document.createElement('div');
    head.className = 'inv-head';
    const title = document.createElement('div');
    title.className = 'shop-title';
    title.textContent = shop.name;
    const tabs = document.createElement('div');
    tabs.className = 'inv-tabs';
    for (const [t, label] of /** @type {const} */ ([['buy', '買う'], ['sell', '売る']])) {
      const b = button(`shop-tab-${t}`, label, () => {
        this.tab = t;
        this.render();
      });
      b.classList.toggle('active', this.tab === t);
      tabs.append(b);
    }
    const money = document.createElement('div');
    money.className = 'inv-money';
    money.textContent = `★ ${inv.money} 星貨`;
    head.append(title, tabs, money, button('shop-close', '閉じる', () => this.close()));
    const list = document.createElement('div');
    list.className = 'inv-list inv-body';
    if (this.tab === 'buy') {
      for (const e of shop.sells) {
        const d = itemDef(e.item);
        list.append(
          row(`shop-buy-${e.item}`, `${d.name}`, `${e.price} 星貨  ${d.desc}`, inv.money >= e.price, () => {
            const r = buy(s, shopId, e.item);
            this.hooks.toast(r === 'ok' ? `${d.name}を買った` : r === 'money' ? '星貨が足りない' : r === 'full' ? 'これ以上持てない' : '売っていない');
            this.render();
          }, e.item),
        );
      }
    } else {
      const ids = Object.keys(inv.items).filter((id) => sellPrice(shopId, id) > 0);
      if (ids.length === 0) list.append(row('shop-nothing', '売れる物がない', '', false, null));
      for (const id of ids) {
        const d = itemDef(baseId(id));
        const price = sellPrice(shopId, id);
        list.append(
          row(`shop-sell-${id.replace(':', '-')}`, `${d.name} ×${inv.items[id]}`, `${price} 星貨で売る`, true, () => {
            const r = sell(s, shopId, id);
            this.hooks.toast(r === 'ok' ? `${d.name}を売った（+${price}）` : r === 'worn' ? '身につけている物は売れない' : '売れない');
            this.render();
          }, id),
        );
      }
    }
    this.el.replaceChildren(head, list);
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
 * @param {string} id @param {string} title @param {string} detail @param {boolean} enabled @param {(() => void) | null} onClick
 * @param {string} [item] the item the row is about: its icon goes before the title (v1.0)
 */
function row(id, title, detail, enabled, onClick, item) {
  const el = document.createElement('div');
  el.className = `inv-row${onClick && enabled ? ' clickable' : ''}`;
  el.id = id;
  if (item) el.append(itemIconElement(item));
  const t = document.createElement('div');
  t.className = 'inv-row-title';
  t.textContent = title;
  const d = document.createElement('div');
  d.className = 'inv-row-detail';
  d.textContent = detail;
  el.append(t, d);
  if (onClick && enabled) {
    el.setAttribute('role', 'button');
    el.addEventListener('click', onClick);
  } else el.style.opacity = '0.55';
  return el;
}
