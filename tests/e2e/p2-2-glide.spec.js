import { test, expect } from '@playwright/test';

// Height verification map (default). The tower top (4 levels = 64px) spans columns 22-27, rows 4-7.

async function open(page) {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/?map=height');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  // Not a combat test: keep enemies from interfering (P3 added enemies to this map).
  await page.evaluate(() => window.__debugApi.clearEnemies());
  return errors;
}

const player = (page) => page.evaluate(() => window.__debugApi.player());
const teleport = (page, tx, ty) => page.evaluate(([x, y]) => window.__debugApi.teleport(x, y), [tx, ty]);

/**
 * Walk west off the tower top and open the glider. The game is paused and advanced step by step
 * while the test walks off the edge and presses jump, so the result does not depend on how fast
 * the machine is.
 */
async function jumpOffAndGlide(page, pressJump) {
  await teleport(page, 22, 5); // west edge of the tower top
  await page.evaluate(() => window.__debugApi.pause());
  await page.keyboard.down('ArrowLeft');
  // Step until the player leaves the edge, then past the coyote window (0.08s = 5 steps).
  const left = await page.evaluate(() => {
    const api = window.__debugApi;
    for (let i = 0; i < 120 && api.player().grounded; i++) api.step(1);
    api.step(8);
    return api.player();
  });
  expect(left.grounded).toBe(false);
  expect(left.z).toBeGreaterThan(40); // still high above the ground
  await pressJump(); // latched while paused
  await page.evaluate(() => window.__debugApi.step(1));
  expect((await player(page)).gliding).toBe(true);
  await page.keyboard.down('ArrowLeft'); // pausing released the held keys: hold again before resuming
  await page.evaluate(() => window.__debugApi.resume());
}

test('jumping off the tower and opening the glider lands far away without damage', async ({ page }, testInfo) => {
  const errors = await open(page);
  await jumpOffAndGlide(page, () => page.keyboard.press('Space'));
  await page.waitForTimeout(400);
  await page.screenshot({ path: testInfo.outputPath('gliding.png') });
  const mid = await player(page);
  expect(mid.stamina).toBeLessThan(100);
  // The camera keeps the gliding player near the center of the screen (DESIGN.md 3.5).
  const cam = await page.evaluate(() => window.__debugApi.camera());
  expect(Math.abs(cam.y - (mid.y - mid.z - 8))).toBeLessThan(cam.viewHeight * 0.2);
  await expect.poll(async () => (await player(page)).grounded, { timeout: 8000 }).toBe(true);
  await page.keyboard.up('ArrowLeft');
  const p = await player(page);
  expect(p.hp).toBe(12); // a plain fall from 64px would cost half a heart
  expect(p.z).toBe(0);
  expect(p.x).toBeLessThan(22 * 16 - 120); // carried well away from the tower
  expect(errors).toEqual([]);
});

test('the touch jump button opens and closes the glider', async ({ page }) => {
  await open(page);
  const tap = async () => {
    await page.locator('#jump-button').dispatchEvent('pointerdown', { pointerId: 9 });
    await page.waitForTimeout(60);
    await page.locator('#jump-button').dispatchEvent('pointerup', { pointerId: 9 });
  };
  await jumpOffAndGlide(page, tap);
  await page.waitForTimeout(300);
  await tap();
  await expect.poll(async () => (await player(page)).gliding, { timeout: 2000, intervals: [30] }).toBe(false);
  await page.keyboard.up('ArrowLeft');
});
