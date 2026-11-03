// @ts-check
// Small user settings in localStorage (DESIGN.md 2.6: localStorage only for small settings).
// Every access is guarded: storage can be unavailable (private browsing, blocked site data).

const KEY = 'seimyaku.settings.v1';

/**
 * @typedef {object} Settings
 * @property {number} resolution  internal height candidate
 */

/** @type {Settings} */
const DEFAULTS = { resolution: 216 };

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
