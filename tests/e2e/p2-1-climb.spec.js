import { test, expect } from '@playwright/test';

// Height verification map (default). Tile coordinates refer to src/game/world/maps/heightTest.js.

async function open(page) {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  // Not a combat test: keep enemies from interfering (P3 added enemies to this map).
  await page.evaluate(() => window.__debugApi.clearEnemies());
  return errors;
}

const player = (page) => page.evaluate(() => window.__debugApi.player());
const teleport = (page, tx, ty) => page.evaluate(([x, y]) => window.__debugApi.teleport(x, y), [tx, ty]);

test('climbs a grass cliff and pulls up onto the plateau', async ({ page }, testInfo) => {
  const errors = await open(page);
  await teleport(page, 14, 22); // south of plateau B (1 level)
  await page.keyboard.down('ArrowUp');
  await expect.poll(async () => (await player(page)).climbing, { timeout: 3000 }).toBe(true);
  await page.screenshot({ path: testInfo.outputPath('climbing.png') });
  const mid = await player(page);
  expect(mid.stamina).toBeLessThanOrEqual(100);
  await expect.poll(async () => (await player(page)).grounded, { timeout: 4000 }).toBe(true);
  await page.keyboard.up('ArrowUp');
  const p = await player(page);
  expect(p.climbing).toBe(false);
  expect(p.z).toBe(16);
  expect(p.y).toBeLessThan(22 * 16);
  expect(errors).toEqual([]);
});

test('climbs the tower side three levels up and uses stamina', async ({ page }, testInfo) => {
  await open(page);
  await teleport(page, 28, 10); // ground east of the tower's 3rd tier (48px)
  await page.keyboard.down('ArrowLeft');
  await expect.poll(async () => (await player(page)).climbing, { timeout: 3000 }).toBe(true);
  await page.waitForTimeout(800);
  const climbing = await player(page);
  expect(climbing.stamina).toBeLessThan(100);
  await page.screenshot({ path: testInfo.outputPath('stamina-wheel.png') });
  await expect.poll(async () => (await player(page)).grounded, { timeout: 8000 }).toBe(true);
  await page.keyboard.up('ArrowLeft');
  expect((await player(page)).z).toBe(48);
});

test('the jump button lets go of the wall', async ({ page }) => {
  await open(page);
  await teleport(page, 28, 10);
  await page.keyboard.down('ArrowLeft');
  await expect.poll(async () => (await player(page)).climbing, { timeout: 3000 }).toBe(true);
  await page.waitForTimeout(400);
  expect((await player(page)).z).toBeGreaterThan(4);
  await page.locator('#jump-button').dispatchEvent('pointerdown', { pointerId: 5 });
  await page.waitForTimeout(80);
  await page.locator('#jump-button').dispatchEvent('pointerup', { pointerId: 5 });
  await page.keyboard.up('ArrowLeft');
  await expect.poll(async () => (await player(page)).grounded, { timeout: 3000 }).toBe(true);
  const p = await player(page);
  expect(p.climbing).toBe(false);
  expect(p.z).toBe(0);
});

test('the virtual stick can climb too', async ({ page }) => {
  await open(page);
  await teleport(page, 14, 22);
  const vp = page.viewportSize();
  const ox = vp.width * 0.2;
  const oy = vp.height * 0.6;
  await page.mouse.move(ox, oy);
  await page.mouse.down();
  await page.mouse.move(ox, oy - 60, { steps: 4 });
  // Release as soon as the player is on top (plateau B is small: walking on would fall off its far side).
  await expect.poll(async () => (await player(page)).z, { timeout: 6000, intervals: [40] }).toBe(16);
  await page.mouse.up();
  expect((await player(page)).grounded).toBe(true);
});
