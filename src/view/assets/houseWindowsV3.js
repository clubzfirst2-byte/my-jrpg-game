// @ts-check
// Graphics v3 (?v3=1): the night windows of the v3 village houses (docs/art-release-v3/VILLAGE.md 2,
// village_windows.json). The lit windows (gfx/fx-v2's src/view/houseWindows.js, not on this branch yet)
// look for glass in fixed rectangles measured on the v1 house (96×112 art px, 48×56 game px, windows at
// game y -34 .. -28): the v3 house has the same game size but its windows lower (y -25.5 .. -15.5), so
// that table would light a square of wall. This is the v3 table — per house picture (the season's file):
// its size, and per window its rectangle (game px from the feet) and its glass, texel by texel (art
// px, 4 per game px), read off the pictures by houseWindows' own rule (glassKind) by
// tools/house_windows_v3.py; tests/unit/houseWindowsV3.test.js checks it against the pictures.
// The iron door bands and the winter snow outline also pass glassKind but lie outside every window,
// so they are never lit (VILLAGE.md 2: never search the whole picture).
import TABLE from './houseWindowsV3.json';

/** Texels per game px of the v3 houses. */
export const V3_WINDOW_SCALE = 4;

/**
 * gfx/fx-v2 houseWindows.glassKind: 0 not glass, 1 glass, 2 the darkest glass.
 * @param {number} r @param {number} g @param {number} b @param {number} a
 */
export function glassKind(r, g, b, a) {
  if (a < 128 || b < r + 20 || b < g) return 0;
  const lum = 0.299 * r + 0.587 * g + 0.114 * b;
  return lum < 40 ? 2 : lum < 110 ? 1 : 0;
}

/** A run-length coded mask row ("14g2.14g") as texels ("gggggggggggggg..ggg..."). @param {string} row */
export const unRle = (row) => row.replace(/(\d+)([.gd])/g, (_, n, c) => c.repeat(Number(n)));

/**
 * The windows of a v3 house picture, by its key as the season draws it ("obj.house", "winter.obj.v3.house_stone"
 * — autumn and spring use their own / summer's file as the village bundle does), or null.
 * @param {string} key @returns {{ size: [number, number], windows: { x: number, y: number, w: number, h: number, glass: string[] }[] } | null}
 */
export function v3HouseWindows(key) {
  const e = /** @type {Record<string, { size: [number, number], windows: { game: [number, number, number, number], glass: string[] }[] }>} */ (/** @type {unknown} */ (TABLE))[key];
  if (!e) return null;
  return { size: e.size, windows: e.windows.map((w) => ({ x: w.game[0], y: w.game[1], w: w.game[2], h: w.game[3], glass: w.glass.map(unRle) })) };
}

/** The picture key of a v3 house in a season (summer's file where the season has none). @param {string} key "obj.house" | "obj.v3.house_stone" @param {string | null | undefined} season */
export function v3HouseFile(key, season) {
  const s = season === 'autumn' || season === 'winter' ? season : null;
  return s && /** @type {Record<string, unknown>} */ (TABLE)[`${s}.${key}`] ? `${s}.${key}` : key;
}
