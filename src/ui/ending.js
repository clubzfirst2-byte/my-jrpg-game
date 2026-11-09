// @ts-check
// v1.0 (C10): the ending screen — the title, a few lines of the credits rolling up, then 「おわり」.
// About 30 s; 「とばす」 or Enter / Escape ends it at once (not a stray tap: the taps that read the
// dialogue through would skip it before its title is read). Calls `onDone` exactly once. DOM + CSS like the title screen (styles.css #ending-screen).

/** The credits (who made what), shown in order. */
export const CREDITS = [
  // (placeholders until the real names are given)
  ['企画・物語・プログラム・絵', '星環のレガリア 制作チーム'],
  ['音楽と効果音', 'Web Audio による合成'],
  ['使った道具', 'PixiJS ・ Vite'],
  ['', 'あそんでくれて、ありがとう'],
];

export class EndingScreen {
  /**
   * @param {HTMLElement} root
   * @param {{ title: string, onDone: () => void, ms?: number, line?: string }} opts
   *   line: a closing line under the title (the princess's choice, for example)
   */
  constructor(root, opts) {
    const ms = opts.ms ?? 30_000;
    this.done = false;
    this.el = document.createElement('div');
    this.el.id = 'ending-screen';
    this.el.style.setProperty('--roll-ms', `${Math.max(1000, ms - 6000)}ms`);

    const roll = document.createElement('div');
    roll.className = 'ending-roll';
    const h = document.createElement('h1');
    h.textContent = opts.title;
    roll.append(h);
    if (opts.line) {
      const p = document.createElement('p');
      p.className = 'ending-line';
      p.textContent = opts.line;
      roll.append(p);
    }
    for (const [role, name] of CREDITS) {
      const row = document.createElement('p');
      row.className = 'ending-credit';
      if (role) {
        const r = document.createElement('span');
        r.className = 'ending-role';
        r.textContent = role;
        row.append(r);
      }
      const n = document.createElement('span');
      n.className = 'ending-name';
      n.textContent = name;
      row.append(n);
      roll.append(row);
    }

    const end = document.createElement('p');
    end.id = 'ending-end';
    end.textContent = 'おわり';

    const skip = document.createElement('button');
    skip.type = 'button';
    skip.id = 'ending-skip';
    skip.textContent = 'とばす';
    skip.addEventListener('click', (e) => {
      e.stopPropagation();
      this.finish();
    });

    this.el.append(roll, end, skip);
    // Keys, but not in its first moments (a key still held from the dialogue).
    const opened = performance.now();
    this.onKey = (/** @type {KeyboardEvent} */ e) => {
      if ((e.code === 'Enter' || e.code === 'Escape') && !e.repeat && performance.now() - opened > 800) {
        e.preventDefault();
        this.finish();
      }
    };
    window.addEventListener('keydown', this.onKey);
    this.onDone = opts.onDone;
    root.append(this.el);
    // 「おわり」 shows for the last seconds, then the screen ends by itself.
    this.endTimer = setTimeout(() => end.classList.add('shown'), Math.max(0, ms - 5000));
    this.timer = setTimeout(() => this.finish(), ms);
  }

  /** Ends the screen (once). */
  finish() {
    if (this.done) return;
    this.done = true;
    clearTimeout(this.timer);
    clearTimeout(this.endTimer);
    window.removeEventListener('keydown', this.onKey);
    this.el.remove();
    this.onDone();
  }
}
