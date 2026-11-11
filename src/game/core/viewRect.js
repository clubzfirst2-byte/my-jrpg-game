// @ts-check
// Graphics v3 (?v3=1, src/view/assets/artV3.js): the narrow view's play adjustment. Pure.

/**
 * The v3 view's play adjustments: an enemy sees the hero, and attacks, only while it is on screen.
 * The view rectangle is the camera's, in game px; `margin` keeps a sliver at the edges off limits (an
 * enemy whose feet are at the very edge is not really visible yet).
 * @param {{ x: number, y: number }} e
 * @param {{ x: number, y: number, width: number, height: number } | null | undefined} view
 * @param {{ side?: number, top?: number, bottom?: number }} [margin] game px (top: room for its body above its feet)
 */
export function onScreen(e, view, margin = {}) {
  if (!view) return true;
  const side = margin.side ?? 6;
  const top = margin.top ?? 12;
  const bottom = margin.bottom ?? 2;
  return e.x >= view.x + side && e.x <= view.x + view.width - side && e.y >= view.y + top && e.y <= view.y + view.height - bottom;
}
