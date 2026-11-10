// @ts-check
// Graphics v2, W4 (scratchpad gfx_plan.md): the UI art of src/art-release-v2/ui on the DOM UI — title
// (logo, 4-layer parallax), glass disc buttons with icons, 9-slice frames for the panels, tabs, rows,
// text-button plates, hearts, the boss bar and the "more below" cue (styles.css, `#ui.ui-v2`).
// Loaded only when the `ui` v2 group is drawn (artV2.js: ?ui=v2, or once it is enabled by default;
// ?ui=v1 / ?v2=0 keep the v1 UI). The art's specs: docs/art-release-v2/ui/NAMES.md and manifest.json.
//
// How the art reaches CSS: every frame becomes a custom property on <html>, `--ui-<name with dots as
// dashes>: url(...)` (e.g. --ui-panel-menu). In the dev server a frame is its own PNG; in the build
// it is a place on the packed sheet, cut out once into a data URL.
//
// The round buttons' CSS is generated here from the manifest's table, so each diameter is EXACTLY a
// drawn ring (inspection I-1: no 66.3 px) and every position and icon offset is a whole CSS px.
import manifest from '../art-release-v2/ui/manifest.json';

/** @typedef {'small' | 'medium' | 'large'} ButtonSize */

/** The `--btn` factor of each button size (styles.css #ui.btn-small / .btn-large). */
export const BUTTON_SCALE = Object.freeze({ small: 0.85, medium: 1, large: 1.15 });

/**
 * Where each round button sits (styles.css, v1): its distance from the cluster's screen edge and from
 * the bottom at button size 中, in CSS px. The v2 positions are these × the size factor, rounded.
 */
export const BUTTON_PLACES = Object.freeze({
  'attack-button': { side: 18, bottom: 22 },
  'jump-button': { side: 104, bottom: 14 },
  'dodge-button': { side: 28, bottom: 110 },
  'bow-button': { side: 98, bottom: 84 },
  'guard-button': { side: 170, bottom: 40 },
  'dash-button': { side: 160, bottom: 104 },
  'ability-button': { side: 176, bottom: 158 },
});

/** @typedef {{ ring: string, icon: string, sizes: Record<ButtonSize, number>, iconSize: Record<ButtonSize, number> }} HudButton */

/** The manifest's round buttons (ring colour, icon, diameters, icon sizes per button size). */
export const HUD_BUTTONS = /** @type {Record<string, HudButton>} */ (manifest.hud);

/** The CSS custom property of a frame. @param {string} name e.g. "panel.menu" */
export const cssVar = (name) => `--ui-${name.replace(/\./g, '-')}`;

/**
 * One round button's box at a button size: its diameter, its distance from the cluster's edge and the
 * bottom, and where its icon goes inside it. All whole CSS px.
 * @param {string} id @param {ButtonSize} size
 */
export function buttonBox(id, size) {
  const b = HUD_BUTTONS[id];
  const k = BUTTON_SCALE[size];
  const d = b.sizes[size];
  const icon = b.iconSize[size];
  const inset = Math.floor((d - icon) / 2);
  if (id === 'ability-next') {
    // ⇄: centred 6 px above the ability button (v1.0 QA2 M-1)
    const ab = buttonBox('ability-button', size);
    return { d, side: ab.side + Math.floor((ab.d - d) / 2), bottom: ab.bottom + ab.d + 6, icon, inset };
  }
  const p = BUTTON_PLACES[/** @type {keyof typeof BUTTON_PLACES} */ (id)];
  return { d, side: Math.round(p.side * k), bottom: Math.round(p.bottom * k), icon, inset };
}

/** The CSS selector of a button size class on #ui (中 is neither class). @param {ButtonSize} size */
const sizeSel = (size) => (size === 'small' ? '.btn-small' : size === 'large' ? '.btn-large' : ':not(.btn-small):not(.btn-large)');

/**
 * The generated CSS for the round buttons (sizes, places, ring and icon art), for every button size and
 * either hand. The rules for the two hands never apply together, so neither needs to undo the other.
 * @returns {string}
 */
export function hudButtonCss() {
  const out = [];
  for (const size of /** @type {ButtonSize[]} */ (['small', 'medium', 'large'])) {
    for (const left of [false, true]) {
      const hand = left ? '.left-handed' : ':not(.left-handed)';
      const [near, far] = left ? ['left', 'right'] : ['right', 'left'];
      for (const [id, b] of Object.entries(HUD_BUTTONS)) {
        const box = buttonBox(id, size);
        const sel = `#ui.ui-v2${sizeSel(size)}${hand} #${id}`;
        const ring = (/** @type {string} */ state) => `var(${cssVar(`btn.ring.${b.ring}.${box.d}.${state}`)})`;
        out.push(
          `${sel} { width: ${box.d}px; height: ${box.d}px; ${near}: calc(${box.side}px + var(--safe-${near})); ${far}: auto; bottom: calc(${box.bottom}px + var(--safe-bottom)); background-color: transparent; border: 0; background-image: ${ring('idle')}; background-size: ${box.d}px ${box.d}px; }`,
          `${sel}.active, ${sel}:active { background-image: ${ring('pressed')}; }`,
          `${sel}::before { left: ${box.inset}px; top: ${box.inset}px; width: ${box.icon}px; height: ${box.icon}px; background-image: var(${cssVar(`icon.ui.${b.icon}.${box.icon}`)}); }`,
        );
      }
    }
  }
  return out.join('\n');
}

/**
 * Turns the frames (PNG URLs, or places on a packed sheet) into URLs CSS can use: a place on the sheet
 * is cut out on one software canvas (`willReadFrequently`: reading a GPU canvas back 98 times cost
 * ~100 ms of start-up) and encoded with `toDataURL`.
 *
 * Measured against `toBlob` + blob: URLs (W4 wiring, 852×393 DPR 3, CPU ×4): `toBlob` spends less on
 * the main thread (~45 ms against ~100 ms), but Chrome encodes small canvases in idle tasks, so the
 * whole cut-out takes ~200 ms and the title appears ~0.5 s later; memory and style recalculation were
 * the same. So `toDataURL`, and main.js does this while the world art is still loading.
 * @param {Map<string, import('../view/assets/placeholderPack.js').ArtSource>} frames
 * @returns {[string, string][]} name → URL, in the frames' order
 */
export function frameUrls(frames) {
  /** @type {HTMLCanvasElement | null} */
  let canvas = null;
  /** @type {CanvasRenderingContext2D | null} */
  let g = null;
  /** @type {[string, string][]} */
  const out = [];
  for (const [name, src] of frames) {
    if (typeof src === 'string') {
      out.push([name, src]);
      continue;
    }
    canvas ??= document.createElement('canvas');
    canvas.width = src.w; // (also clears it)
    canvas.height = src.h;
    g ??= /** @type {CanvasRenderingContext2D} */ (canvas.getContext('2d', { willReadFrequently: true }));
    g.drawImage(/** @type {CanvasImageSource} */ (src.sheet), src.x, src.y, src.w, src.h, 0, 0, src.w, src.h);
    out.push([name, canvas.toDataURL('image/png')]);
  }
  if (canvas) canvas.width = canvas.height = 0; // free the backing store
  return out;
}

/**
 * Puts the v2 UI on: the frames as CSS custom properties (one style sheet), the generated button CSS,
 * and the `ui-v2` class on #ui (and <html>, for anything outside it).
 * @param {HTMLElement} root #ui
 * @param {Map<string, import('../view/assets/placeholderPack.js').ArtSource>} frames the ui group's frames
 */
export function installUiSkin(root, frames) {
  const vars = frameUrls(frames).map(([name, url]) => `${cssVar(name)}: url("${url}");`);
  const style = document.createElement('style');
  style.id = 'ui-v2-buttons';
  style.textContent = `:root { ${vars.join(' ')} }\n${hudButtonCss()}`;
  document.head.append(style);
  root.classList.add('ui-v2');
  document.documentElement.classList.add('ui-v2');
}

/** How many play sessions show the text labels on the round buttons (setting 「はじめだけ」). */
export const LABEL_SESSIONS = 3;

/**
 * Whether the round buttons show their text labels (v2 UI; v1 always shows text).
 * @param {'auto' | 'on' | 'off'} setting @param {number} sessions sessions so far, this one included
 */
export const showButtonLabels = (setting, sessions) => setting === 'on' || (setting === 'auto' && sessions <= LABEL_SESSIONS);
