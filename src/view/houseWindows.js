// @ts-check
// gfx W5: lit windows on the village houses at night. Only the glass is lit: the panes' own pixels
// are found in the release house's art (src/art-release/objects/obj.house.png, 96×112 art px =
// 48×56 game px, feet at the bottom centre) and recoloured warm, so the frames, the mullions, the
// glints on the glass and the flower boxes stay as drawn. The glass is drawn above the light map (it
// shines in the dark); the light it gives falls on the ground in front of each window — not on the
// house's own wall. Pure (unit-tested), apart from the texture.

/**
 * Where to look for the glass in the release house (game px from its feet): the two windows' frames
 * (glass at art x 12–25 and 70–83, y 44–56, two leaves each side of a mullion).
 */
export const HOUSE_WINDOWS = Object.freeze([
  Object.freeze({ x: -18, y: -34, w: 7, h: 6 }),
  Object.freeze({ x: 11, y: -34, w: 7, h: 6 }),
]);
/** The art the windows were measured on (game px): only this house gets them. */
export const HOUSE_SIZE = Object.freeze({ w: 48, h: 56 });

/**
 * The glass's warm colours (lit, and the darker glass at the panes' edges), and the light on the
 * ground in front of each window (radius in world px, its centre this far below the house's feet),
 * with an orange pixel pool drawn there so it reads as lamp light, not a green smudge on the grass.
 */
export const WINDOW_GLOW = Object.freeze({
  glass: 0xffc860,
  deep: 0xd8903c,
  light: 0xff7430,
  radius: 6,
  groundY: 6,
  /** the pool of light on the ground: a stepped pixel oval (game px), orange, at this opacity at night */
  pool: Object.freeze({ w: 22, h: 10, color: 0xffa040, alpha: 0.55 }),
});

/**
 * How lit the windows are (0 by day .. 1 at night) for an ambient colour: they come on at dusk.
 * @param {{ r: number, g: number, b: number }} amb
 */
export function windowGlow(amb) {
  const lum = 0.299 * amb.r + 0.587 * amb.g + 0.114 * amb.b;
  return Math.max(0, Math.min(1, (0.85 - lum) / 0.45));
}

/** Whether a house texture is the release house the windows belong to. @param {{ width: number, height: number }} tex */
export const hasWindows = (tex) => tex.width === HOUSE_SIZE.w && tex.height === HOUSE_SIZE.h;

/**
 * Whether an art pixel is window glass (the blue-black panes, not their light-blue glints, the
 * wooden frame or the flowers): 0 no, 1 glass, 2 the darkest glass.
 * @param {number} r @param {number} g @param {number} b @param {number} a
 */
export function glassKind(r, g, b, a) {
  if (a < 128 || b < r + 20 || b < g) return 0;
  const lum = 0.299 * r + 0.587 * g + 0.114 * b;
  return lum < 40 ? 2 : lum < 110 ? 1 : 0;
}

/**
 * The glass pixels of the release house's two windows (art px, 2 per game px; rows top to bottom over
 * each HOUSE_WINDOWS rect): g glass, d the darkest glass, . anything else (frame, mullion, glints).
 * Read off the art by glassKind (a unit test checks it still matches obj.house.png), so the game
 * needs no pixel read-back from the GPU (which cost about a second on loading the village).
 */
export const HOUSE_GLASS = Object.freeze([
  Object.freeze([
    'dd...d...ddddd',
    'd...dd..dddddd',
    '...ggg..gggggg',
    '..ggg...gggggg',
    '.ggg.g..gggggg',
    'ggg.gg..gggggg',
    'gg.ggg..gggggg',
    '..............',
    '..............',
    'gggggg..gggggg',
    'gggggg..gggggg',
    'gggggg..gggggg',
  ]),
  Object.freeze([
    'dd...d...ddddd',
    'd...dd..dddddd',
    '...ggg..gggggg',
    '..ggg...gggggg',
    '.ggg.g..gggggg',
    'ggg.gg..gggggg',
    'gg.ggg..gggggg',
    '..............',
    '..............',
    'gggggg..gggggg',
    'gggggg..gggggg',
    'gggggg..gggggg',
  ]),
]);

/** The area of the art that holds both windows (game px from the feet): one sprite per house. */
export const PANE_AREA = Object.freeze({ x: HOUSE_WINDOWS[0].x, y: HOUSE_WINDOWS[0].y, w: HOUSE_WINDOWS[1].x + HOUSE_WINDOWS[1].w - HOUSE_WINDOWS[0].x, h: HOUSE_WINDOWS[0].h });

/**
 * The lit panes as an RGBA image over PANE_AREA, from the house's pixels.
 * @param {ArrayLike<number>} px RGBA of the whole house art @param {number} width its width in art px
 * @param {number} scale art px per game px
 * @returns {{ w: number, h: number, data: Uint8ClampedArray, glass: number }} glass: how many pixels lit
 */
export function paneImage(px, width, scale) {
  const w = Math.round(PANE_AREA.w * scale);
  const h = Math.round(PANE_AREA.h * scale);
  const data = new Uint8ClampedArray(w * h * 4);
  // art px of the area's corner (the feet are at the bottom centre of the art)
  const ox = Math.round((HOUSE_SIZE.w / 2 + PANE_AREA.x) * scale);
  const oy = Math.round((HOUSE_SIZE.h + PANE_AREA.y) * scale);
  let glass = 0;
  for (const win of HOUSE_WINDOWS) {
    const x0 = Math.round((win.x - PANE_AREA.x) * scale);
    const y0 = Math.round((win.y - PANE_AREA.y) * scale);
    for (let y = y0; y < y0 + win.h * scale; y++) {
      for (let x = x0; x < x0 + win.w * scale; x++) {
        const i = ((oy + y) * width + ox + x) * 4;
        const k = glassKind(px[i], px[i + 1], px[i + 2], px[i + 3]);
        if (!k) continue;
        const c = k === 2 ? WINDOW_GLOW.deep : WINDOW_GLOW.glass;
        const o = (y * w + x) * 4;
        data[o] = (c >> 16) & 255;
        data[o + 1] = (c >> 8) & 255;
        data[o + 2] = c & 255;
        data[o + 3] = 255;
        glass++;
      }
    }
  }
  return { w, h, data, glass };
}

/**
 * The lit panes as an RGBA image over PANE_AREA, from HOUSE_GLASS (the same image paneImage makes
 * from the art's pixels; 2 art px per game px).
 * @returns {{ w: number, h: number, data: Uint8ClampedArray, glass: number, scale: number }}
 */
export function paneImageFromTable() {
  const scale = 2;
  const w = PANE_AREA.w * scale;
  const h = PANE_AREA.h * scale;
  const data = new Uint8ClampedArray(w * h * 4);
  let glass = 0;
  HOUSE_WINDOWS.forEach((win, k) => {
    const x0 = (win.x - PANE_AREA.x) * scale;
    const y0 = (win.y - PANE_AREA.y) * scale;
    HOUSE_GLASS[k].forEach((row, y) => {
      for (let x = 0; x < row.length; x++) {
        if (row[x] === '.') continue;
        const c = row[x] === 'd' ? WINDOW_GLOW.deep : WINDOW_GLOW.glass;
        const o = ((y0 + y) * w + x0 + x) * 4;
        data[o] = (c >> 16) & 255;
        data[o + 1] = (c >> 8) & 255;
        data[o + 2] = c & 255;
        data[o + 3] = 255;
        glass++;
      }
    });
  });
  return { w, h, data, glass, scale };
}

/**
 * Where each window's light falls: on the ground in front of it (world px), below the house's feet.
 * @param {number} x the house's feet @param {number} feetY
 */
export const windowLightSpots = (x, feetY) => HOUSE_WINDOWS.map((w) => ({ x: x + w.x + w.w / 2, y: feetY + WINDOW_GLOW.groundY }));
