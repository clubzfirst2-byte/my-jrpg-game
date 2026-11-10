// @ts-check
// Small user settings in localStorage (DESIGN.md 2.6: localStorage only for small settings).
// Every access is guarded: storage can be unavailable (private browsing, blocked site data).

const KEY = 'seimyaku.settings.v1';

/**
 * @typedef {object} Settings
 * @property {number} resolution  internal height candidate
 * @property {number} bgmVolume  P11.2: music, 0..1
 * @property {number} sfxVolume  P11.2: sound effects, 0..1
 * @property {'easy' | 'normal' | 'hard'} difficulty  P11.3
 * @property {'normal' | 'large'} textSize  P11.3: conversations, messages, menus
 * @property {'small' | 'medium' | 'large'} buttonSize  P11.3: the touch buttons
 * @property {'right' | 'left'} hand  P11.3: which hand presses the action buttons
 * @property {'auto' | 'on' | 'off'} buttonLabels  W4 (v2 UI): text on the round buttons — the first
 *   few play sessions only (auto), always, or never (icons only); the v1 UI always shows text
 */

/** @type {Settings} */
const DEFAULTS = { resolution: 216, bgmVolume: 0.5, sfxVolume: 0.8, difficulty: /** @type {const} */ ('normal'), textSize: /** @type {const} */ ('normal'), buttonSize: /** @type {const} */ ('medium'), hand: /** @type {const} */ ('right'), buttonLabels: /** @type {const} */ ('auto') };

/** @returns {Settings} */
export function loadSettings() {
  try {
    const raw = window.localStorage.getItem(KEY);
    if (!raw) return { ...DEFAULTS };
    return { ...DEFAULTS, ...JSON.parse(raw) };
  } catch {
    return { ...DEFAULTS };
  }
}

/** @param {Settings} settings */
export function saveSettings(settings) {
  try {
    window.localStorage.setItem(KEY, JSON.stringify(settings));
    return true;
  } catch {
    return false;
  }
}

const SESSIONS_KEY = 'seimyaku.sessions.v1';

/**
 * W4: counts this play session (each start of the game) and returns how many there have been,
 * this one included (1 when storage is unavailable, so the first-plays help shows).
 * @returns {number}
 */
export function countSession() {
  try {
    const n = (parseInt(window.localStorage.getItem(SESSIONS_KEY) ?? '0', 10) || 0) + 1;
    window.localStorage.setItem(SESSIONS_KEY, String(n));
    return n;
  } catch {
    return 1;
  }
}
