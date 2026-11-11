// @ts-check
// P11.3: the settings screen (from the pause screen): difficulty, text size, button size, which
// hand holds the buttons, and the sound volumes. Every choice applies at once and is remembered.

/**
 * @typedef {import('../platform/settings.js').Settings} Settings
 * @typedef {{ key: keyof Settings, label: string, options: { value: any, label: string }[] }} Row
 */

/** @type {Row[]} */
export const SETTING_ROWS = [
  {
    key: 'difficulty',
    label: '難易度',
    options: [
      { value: 'easy', label: 'やさしい' },
      { value: 'normal', label: 'ふつう' },
      { value: 'hard', label: 'むずかしい' },
    ],
  },
  {
    key: 'textSize',
    label: '文字の大きさ',
    options: [
      { value: 'normal', label: 'ふつう' },
      { value: 'large', label: '大きい' },
    ],
  },
  {
    key: 'buttonSize',
    label: 'ボタンの大きさ',
    options: [
      { value: 'small', label: '小' },
      { value: 'medium', label: '中' },
      { value: 'large', label: '大' },
    ],
  },
  {
    key: 'hand',
    label: '持ち方',
    options: [
      { value: 'right', label: '右手でボタン' },
      { value: 'left', label: '左手でボタン' },
    ],
  },
  {
    key: 'bgmVolume',
    label: 'BGM',
    options: [0, 0.25, 0.5, 0.75, 1].map((v) => ({ value: v, label: v === 0 ? 'オフ' : `${v * 100}` })),
  },
  {
    key: 'sfxVolume',
    label: '効果音',
    options: [0, 0.25, 0.5, 0.75, 1].map((v) => ({ value: v, label: v === 0 ? 'オフ' : `${v * 100}` })),
  },
];

/** W4: shown only with the v2 UI (main.js), where the round buttons are icons. @type {Row} */
export const BUTTON_LABELS_ROW = {
  key: 'buttonLabels',
  label: 'ボタンに文字を表示',
  options: [
    { value: 'auto', label: 'はじめだけ' },
    { value: 'on', label: 'いつも' },
    { value: 'off', label: 'なし' },
  ],
};

/** What each difficulty means, shown under the choices. */
const DIFFICULTY_NOTES = /** @type {Record<string, string>} */ ({
  easy: '受けるダメージが半分',
  normal: '',
  hard: '受けるダメージが 1.5 倍',
});

export class SettingsMenu {
  /**
   * @param {HTMLElement} root
   * @param {{ get: () => Settings, set: (key: keyof Settings, value: any) => void, onClose: () => void }} hooks
   * @param {Row[]} [rows] the rows shown (SETTING_ROWS; W4 adds BUTTON_LABELS_ROW with the v2 UI)
   */
  constructor(root, hooks, rows = SETTING_ROWS) {
    this.hooks = hooks;
    this.settingRows = rows;
    this.el = document.createElement('div');
    this.el.id = 'settings-menu';
    this.el.hidden = true;
    this.el.addEventListener('click', (e) => e.stopPropagation());
    const title = document.createElement('div');
    title.className = 'settings-title';
    title.textContent = '設定';
    this.rows = document.createElement('div');
    this.rows.className = 'settings-rows';
    this.note = document.createElement('div');
    this.note.className = 'settings-note';
    const close = document.createElement('button');
    close.type = 'button';
    close.id = 'settings-close';
    close.textContent = '閉じる';
    close.addEventListener('click', () => this.close());
    // v1.0 (iPhone): the menu is taller than a landscape phone; the footer with 閉じる sticks to the
    // bottom of the scrolling panel, so it can always be reached without scrolling.
    const foot = document.createElement('div');
    foot.className = 'settings-foot';
    foot.append(close);
    this.el.append(title, this.rows, this.note, foot);
    root.append(this.el);
  }

  get isOpen() {
    return !this.el.hidden;
  }

  open() {
    this.render();
    this.el.hidden = false;
  }

  close() {
    this.el.hidden = true;
    this.hooks.onClose();
  }

  render() {
    const s = this.hooks.get();
    this.rows.replaceChildren(
      ...this.settingRows.map((row) => {
        const line = document.createElement('div');
        line.className = 'settings-row';
        const name = document.createElement('div');
        name.className = 'settings-label';
        name.textContent = row.label;
        const choices = document.createElement('div');
        choices.className = 'settings-choices';
        for (const opt of row.options) {
          const b = document.createElement('button');
          b.type = 'button';
          b.id = `set-${row.key}-${String(opt.value).replace('.', '_')}`;
          b.textContent = opt.label;
          b.classList.toggle('selected', s[row.key] === opt.value);
          b.addEventListener('click', () => {
            this.hooks.set(row.key, opt.value);
            this.render();
          });
          choices.append(b);
        }
        line.append(name, choices);
        return line;
      }),
    );
    this.note.textContent = DIFFICULTY_NOTES[s.difficulty] ?? '';
  }
}
