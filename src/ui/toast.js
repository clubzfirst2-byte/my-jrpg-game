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
    if (this.timer) clearTimeout(this.timer);
    this.timer = setTimeout(() => {
      this.el.hidden = true;
    }, ms);
  }
}
