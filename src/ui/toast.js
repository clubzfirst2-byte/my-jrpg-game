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
    this.el.replaceChildren(...withBreaks(text));
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
    const oneLine = el.clientHeight;
    el.style.maxWidth = '';
    let width = balancedWidth(natural, capped, 28);
    if (!width) return;
    el.style.width = `${width}px`;
    // The message breaks only between phrases (withBreaks), so an even split may need a little
    // more room than one character: widen until it takes no more lines than it must.
    const lines = Math.ceil((natural - 28) / (capped - 28));
    const most = 16 + lines * (oneLine - 16) + 1; // 8 px padding top and bottom
    while (el.clientHeight > most && width < capped) {
      width = Math.min(capped, width + 16);
      el.style.width = `${width}px`;
    }
  }
}

// v1.0 (final QA L-6 rest, "目を開け／た。"): CSS does not know where Japanese words end, so a
// wrapped message could break in the middle of one. The toast breaks only between phrases instead
// (`word-break: keep-all` in the CSS, with a <wbr> at each place found here); a phrase too long for
// a line still wraps (`overflow-wrap: anywhere`).
const HIRAGANA = /[\u3041-\u309f]/;
/** Starts a new phrase after hiragana: kanji, katakana, latin letters, digits, opening brackets. */
const PHRASE_START = /[\u4e00-\u9fff\u3400-\u4dbf\u30a0-\u30fa\uff10-\uff19\uff21-\uff5a0-9A-Za-z「『（(【〈《]/;
/** Ends a phrase: a break may follow (unless more closing punctuation follows). */
const PHRASE_END = /[、。，．,！？!?…‥]/;
/** Closing brackets: a break may follow, but not before the particle after them (「灯火」を). */
const CLOSE = /[）)」』】〉》]/;
/** Never starts a line. */
const NO_LINE_START = /[、。，．,！？!?…‥）)」』】〉》ー〜～・：:；;]/;
/** Never ends a line. */
const NO_LINE_END = /[「『（(【〈《]/;

/**
 * The message cut into phrases, where a line may break: after punctuation and closing brackets,
 * before an opening bracket (and after a closing one, but not before its particle), and where a run of hiragana (particles, verb endings) is followed by a
 * new word. "裏返った星環——淀みの源が目を開けた。" → 裏返った | 星環——淀みの | 源が | 目を | 開けた。
 * Spaces stay as they are (the browser breaks there too).
 * @param {string} text @returns {string[]}
 */
export function phrases(text) {
  const out = [];
  let start = 0;
  for (let i = 1; i < text.length; i++) {
    const prev = text[i - 1];
    const cur = text[i];
    if (NO_LINE_START.test(cur) || NO_LINE_END.test(prev) || cur === ' ' || prev === ' ') continue;
    if (PHRASE_END.test(prev) || (CLOSE.test(prev) && !HIRAGANA.test(cur)) || NO_LINE_END.test(cur) || (HIRAGANA.test(prev) && PHRASE_START.test(cur))) {
      out.push(text.slice(start, i));
      start = i;
    }
  }
  out.push(text.slice(start));
  return out;
}

/** The message as text nodes with a <wbr> between phrases. @param {string} text @returns {Node[]} */
function withBreaks(text) {
  /** @type {Node[]} */
  const nodes = [];
  for (const p of phrases(text)) {
    if (nodes.length) nodes.push(document.createElement('wbr'));
    nodes.push(document.createTextNode(p));
  }
  return nodes;
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
