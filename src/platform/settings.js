// @ts-check
// Small user settings in localStorage (DESIGN.md 2.6: localStorage only for small settings).
// Every access is guarded: storage can be unavailable (private browsing, blocked site data).

const KEY = 'seimyaku.settings.v1';

/**
 * @typedef {object} Settings
 * @property {number} resolution  internal height candidate
 * @property {number} bgmVolume  P11.2: music, 0..1
 * @property {number} sfxVolume  P11.2: sound effects, 0..1
 */

/** @type {Settings} */
const DEFAULTS = { resolution: 216, bgmVolume: 0.5, sfxVolume: 0.8 };

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
