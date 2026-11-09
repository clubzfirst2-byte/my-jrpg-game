// @ts-check
// v1.0: where an item icon stands on the ground (sprite anchor). Icons stand on their feet (FEET:
// the bottom of their 20×20) like the other objects; their drawings end on row 17 or 18, just above
// the guide's 1-px margin (6.1). The star shard's drawing ends on row 14, so on the ground it would
// float 4 art px higher than the rest: its feet are moved up to keep the same one empty row under
// the drawing as the row-18 icons (feet at row 16 of 20 → 0.8). Its 10×10 placeholder is drawn to
// match (it ends on row 6). The menus (CSS backgrounds) are not affected.
/** @type {Readonly<Record<string, [number, number]>>} */
export const ICON_ANCHORS = Object.freeze({
  'icon.star_shard': /** @type {[number, number]} */ ([0.5, 0.8]),
});
