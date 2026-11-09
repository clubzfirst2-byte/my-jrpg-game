import { expect } from '@playwright/test';

// Game time in E2E tests. The game simulates fixed 60 Hz logic ticks, but a slow renderer (software
// WebGL, the hero's 2× art density) gets fewer frames and the loop drops what it cannot catch up,
// so a wall-clock wait can give the game much less time than intended. Waits that the game must
// spend (holding a key to walk, draw, climb) are counted in ticks instead.

/** Waits until the game has run `n` more logic ticks (60 per second of game time). */
export async function waitTicks(page, n) {
  const tick = () => page.evaluate(() => /** @type {any} */ (window).__debugApi.tick());
  const t0 = await tick();
  await expect.poll(tick, { timeout: 20_000, intervals: [20] }).toBeGreaterThanOrEqual(t0 + n);
}

/** Milliseconds of game time as logic ticks. */
export const ticksOf = (ms) => Math.round((ms * 60) / 1000);
