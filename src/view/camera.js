// @ts-check
// Camera math (no PixiJS import, so it is unit-testable).

/**
 * Top-left of the view so that the target is centered, clamped to the world.
 * If the world is smaller than the view on an axis, the world is centered on that axis.
 * Result is rounded to whole pixels to keep pixel art crisp.
 * @param {number} targetX @param {number} targetY
 * @param {number} viewW @param {number} viewH
 * @param {number} worldW @param {number} worldH
 */
export function cameraOrigin(targetX, targetY, viewW, viewH, worldW, worldH) {
  return { x: Math.round(axis(targetX, viewW, worldW)), y: Math.round(axis(targetY, viewH, worldH)) };
}

/** @param {number} target @param {number} view @param {number} world */
function axis(target, view, world) {
  if (world <= view) return (world - view) / 2;
  return Math.min(Math.max(target - view / 2, 0), world - view);
}
