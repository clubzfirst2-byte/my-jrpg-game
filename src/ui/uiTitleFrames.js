// @ts-check
// Graphics v2, W4: which v2 UI frames the title screen shows (styles.css: the title's backgrounds and
// logo, the text plates, the toast-style note). Pure, shared by the build (vite.config.js: the page
// preloads these when the v2 UI is drawn) and the game (main.js: the title waits for these only; the
// other frames load in the background).

/** @param {string} name a frame of src/art-release-v2/ui, e.g. "title.bg.sky" */
export const isTitleFrame = (name) => name.startsWith('title.') || name.startsWith('btn.text.') || name === 'panel.toast';
