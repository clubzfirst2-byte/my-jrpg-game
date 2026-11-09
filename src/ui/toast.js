// @ts-check
// Short messages at the top of the screen ("ハートの器を手に入れた", save failures, ...).

export class Toast {
  /** @param {HTMLElement} root */
  constructor(root) {
    this.el = document.createElement('div');
    this.el.id = 'toast';
    this.el.setAttribute('role', 'status');
    this.el.setAttribute('aria-live', 'polite');
    this.el.hidden = true;
    root.append(this.el);
    /** @type {ReturnType<typeof setTimeout> | null} */
    this.timer = null;
    /** Everything shown so far (for tests). @type {string[]} */
    this.history = [];
  }

  /** @param {string} text @param {{ ms?: number, kind?: 'info' | 'error' }} [opts] */
  show(text, opts = {}) {
    const { ms = 2500, kind = 'info' } = opts;
    this.history.push(text);
    if (this.history.length > 20) this.history.shift();
    this.el.textContent = text;
    this.el.dataset.kind = kind;
    this.el.hidden = false;
    this.balance();
    if (this.timer) clearTimeout(this.timer);
    this.timer = setTimeout(() => {
      this.el.hidden = true;
    }, ms);
  }

  /**
   * v1.0 QA2: where CSS `text-wrap: balance` is not supported (iOS Safari before 17.5), narrows a
   * message that wraps so its lines come out about even, instead of a full first line and its last
   * character alone on the next one.
   */
  balance() {
    const el = this.el;
    el.style.width = '';
    if (typeof CSS !== 'undefined' && CSS.supports?.('text-wrap', 'balance')) return;
    const capped = el.clientWidth; // with the max width
    el.style.maxWidth = 'none';
    const natural = el.clientWidth; // the message on one line
    el.style.maxWidth = '';
    const width = balancedWidth(natural, capped, 28);
    if (width) el.style.width = `${width}px`;
  }
}

/**
 * The box width that splits a message evenly over the lines it needs, or 0 when it fits on one
 * line. Widths include `padding` (both sides); one character (16 px) of slack keeps the line count.
 * @param {number} natural the box's width with the message on one line
 * @param {number} capped the box's maximum width
 * @param {number} padding
 */
export function balancedWidth(natural, capped, padding) {
  if (natural <= capped + 0.5) return 0;
  const lines = Math.ceil((natural - padding) / (capped - padding));
  return Math.min(capped, Math.ceil((natural - padding) / lines + padding + 16));
}
