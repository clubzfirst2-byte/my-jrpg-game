// @ts-check
// gfx v2 integration (start-up): a short loading note between the title and play. The title shows as
// soon as its own art and the save are read; the world (art sheets, atlases, the view) is prepared
// after it. A start pressed before the start area is drawn with all its art waits behind this note
// (main.js), so the world never shows with missing or stand-in pictures. It covers the screen at
// once; its words appear only after a moment, so a quick start shows no flash of text.

export class StartLoading {
  /** @param {HTMLElement} root */
  constructor(root) {
    this.el = document.createElement('div');
    this.el.id = 'start-loading';
    this.el.setAttribute('role', 'status');
    this.el.hidden = true;
    const text = document.createElement('p');
    text.textContent = '読み込み中…';
    this.el.append(text);
    root.append(this.el);
  }

  show() {
    this.el.hidden = false;
  }

  hide() {
    this.el.hidden = true;
  }

  get visible() {
    return !this.el.hidden;
  }
}
