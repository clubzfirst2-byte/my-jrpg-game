// @ts-check
// gfx W5: lit windows on the village houses at night. The panes of the release house
// (src/art-release/objects/obj.house.png, 96×112 art px = 48×56 game px, feet at the bottom centre)
// are covered by a warm glow drawn in code, and each window adds a warm light to the light map, so
// the windows shine and spill light on the ground around the house. Pure (unit-tested).

/**
 * The release house's two windows, relative to its feet (game px): the pane rectangles found in the
 * art (glass at art x 12–25 and 70–83, y 44–56: two leaves each side of a mullion).
 */
export const HOUSE_WINDOWS = Object.freeze([
  Object.freeze({ x: -18, y: -34, w: 7, h: 6 }),
  Object.freeze({ x: 11, y: -34, w: 7, h: 6 }),
]);
/** The art the windows were measured on (game px): only this house gets them. */
export const HOUSE_SIZE = Object.freeze({ w: 48, h: 56 });

/** The glow's colour, and its light in the light map (radius in world px). */
export const WINDOW_GLOW = Object.freeze({ color: 0xffc860, alpha: 0.9, light: 0xffc070, radius: 18 });

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
