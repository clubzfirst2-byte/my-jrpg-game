import { test, expect } from '@playwright/test';

// Height verification map (default). The tower top (4 levels = 64px) spans columns 22-27, rows 4-7.

async function open(page) {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  return errors;
}

const player = (page) => page.evaluate(() => window.__debugApi.player());
const teleport = (page, tx, ty) => page.evaluate(([x, y]) => window.__debugApi.teleport(x, y), [tx, ty]);

/** Walk west off the tower top and press jump once airborne. */
async function jumpOffAndGlide(page, pressJump) {
  await teleport(page, 22, 5); // west edge of the tower top
  await page.keyboard.down('ArrowLeft');
  await expect.poll(async () => (await player(page)).grounded, { timeout: 3000, intervals: [30] }).toBe(false);
  await page.waitForTimeout(100);
  await pressJump();
  await expect.poll(async () => (await player(page)).gliding, { timeout: 2000, intervals: [30] }).toBe(true);
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
