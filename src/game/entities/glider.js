// @ts-check
// Gliding (DESIGN.md 3.3.3; P2.2). Pure logic on the player object.
// Jump in mid-air opens the glider, jump again closes it. While gliding the player sinks slowly,
// steers freely and spends stamina. Landing while gliding never causes fall damage.

export const GLIDE = Object.freeze({
  /** Horizontal speed while gliding (px/s). */
  speed: 80,
  /** Steering acceleration (px/s^2): momentum carries, so turns are gentle. */
  accel: 300,
  /** Constant sink speed (px/s). From a 4-level (64px) tower: ~2.9s in the air, ~230px across. */
  fallSpeed: 22,
  /** Minimum height above the ground to open the glider (px). */
  minHeight: 12,
  /** Stamina per second while gliding. */
  cost: 6,
  /** Rising air over a fire (P5): climb speed, and how high above the ground it carries (px). */
  updraftSpeed: 70,
  updraftHeight: 112,
});

/** @param {import('./player.js').Player} p */
export function canOpenGlider(p) {
  return !p.grounded && !p.climbing && !p.exhausted && p.stamina > 0 && p.z - p.groundZ >= GLIDE.minHeight;
}

/** @param {import('./player.js').Player} p */
export function openGlider(p) {
  p.gliding = true;
  p.vz = -GLIDE.fallSpeed; // opening cancels any upward speed
  p.fallPeakZ = p.z;
}

/** Closing starts a normal fall; fall damage is measured from here. @param {import('./player.js').Player} p */
export function closeGlider(p) {
  p.gliding = false;
  p.fallPeakZ = p.z;
}

/**
 * Vertical motion and stamina for one step of gliding.
 * @param {import('./player.js').Player} p @param {number} dt
 */
export function glideStep(p, dt) {
  // Over a fire the hot air lifts the glider (P5), up to a height above the ground.
  const lifting = !!p.updraft && p.z - p.groundZ < GLIDE.updraftHeight;
  p.vz = lifting ? GLIDE.updraftSpeed : -GLIDE.fallSpeed;
  p.z += p.vz * dt;
  p.fallPeakZ = p.z; // only a fall after closing the glider can hurt
  p.stamina = Math.max(0, p.stamina - GLIDE.cost * dt);
  p.staminaRestTime = 0;
  if (p.stamina <= 0) {
    p.exhausted = true;
    closeGlider(p);
  }
}
