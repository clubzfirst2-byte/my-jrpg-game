// @ts-check
// The conversation box (P9): who is speaking, one line at a time (tap / J / Enter for the next),
// and the answers when a question is asked. The game waits while it is open.

export class DialogueBox {
  /**
   * @param {HTMLElement} root
   * @param {{ next: () => void, choose: (i: number) => void }} hooks
   */
  constructor(root, hooks) {
    this.hooks = hooks;
    this.el = document.createElement('div');
    this.el.id = 'dialogue';
    this.el.hidden = true;
    this.el.setAttribute('role', 'dialog');
    this.speaker = document.createElement('div');
    this.speaker.className = 'dialogue-speaker';
    this.text = document.createElement('div');
    this.text.className = 'dialogue-text';
    this.more = document.createElement('div');
    this.more.className = 'dialogue-more';
    this.more.textContent = '▼';
    this.choices = document.createElement('div');
    this.choices.className = 'dialogue-choices';
    this.el.append(this.speaker, this.text, this.more, this.choices);
    this.el.addEventListener('click', (e) => {
      if (/** @type {HTMLElement} */ (e.target).closest('button')) return;
      if (this.choices.childElementCount === 0) hooks.next();
    });
    root.append(this.el);
    this.shown = '';
  }

  get isOpen() {
    return !this.el.hidden;
  }

  /** @param {{ speaker: string, text: string, choices: string[] | null } | null} view */
  show(view) {
    if (!view) {
      this.el.hidden = true;
      this.shown = '';
      return;
    }
    const key = JSON.stringify(view);
    if (key === this.shown) return; // only touch the DOM when something changed
    this.shown = key;
    this.el.hidden = false;
    this.speaker.textContent = view.speaker;
    this.text.textContent = view.text;
    this.more.hidden = !!view.choices;
    this.choices.replaceChildren(
      ...(view.choices ?? []).map((label, i) => {
        const b = document.createElement('button');
        b.type = 'button';
        b.id = `dialogue-choice-${i}`;
        b.textContent = label;
        b.addEventListener('click', () => this.hooks.choose(i));
        return b;
      }),
    );
  }
}
