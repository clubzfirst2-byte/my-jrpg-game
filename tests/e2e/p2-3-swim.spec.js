import { test, expect } from '@playwright/test';

// Height verification map (default). Pond: rows 5-10, columns 30-37; column 33 is water from
// row 5 to row 10 with land at rows 4 and 11. The tower top (64px) spans columns 22-27, rows 4-7.

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

test('wades into the pond, swims across and walks out on the far shore', async ({ page }, testInfo) => {
  const errors = await open(page);
  await teleport(page, 33, 11); // south shore
  await page.keyboard.down('ArrowUp');
  await expect.poll(async () => (await player(page)).swimming, { timeout: 4000, intervals: [30] }).toBe(true);
  await page.waitForTimeout(300);
  await page.screenshot({ path: testInfo.outputPath('swimming.png') });
  const mid = await player(page);
  expect(mid.z).toBe(0);
  expect(mid.stamina).toBeLessThan(100);
  await expect
    .poll(async () => {
      const p = await player(page);
      return p.grounded && p.y < 5 * 16;
    }, { timeout: 10_000, intervals: [50] })
    .toBe(true);
  await page.keyboard.up('ArrowUp');
  expect(errors).toEqual([]);
});

test('running out of stamina in the water returns the player to the shore', async ({ page }) => {
  await open(page);
  await teleport(page, 33, 11);
  await page.keyboard.down('ArrowUp');
  await expect.poll(async () => (await player(page)).swimming, { timeout: 4000, intervals: [30] }).toBe(true);
  await page.waitForTimeout(400);
  await page.keyboard.up('ArrowUp');
  await page.evaluate(() => window.__debugApi.setStamina(0.2));
  await expect.poll(async () => (await player(page)).swimming, { timeout: 3000, intervals: [30] }).toBe(false);
  const p = await player(page);
  expect(p.grounded).toBe(true);
  expect(p.hp).toBe(10); // half a heart lost
  expect(p.y).toBeGreaterThan(10 * 16); // back on the south shore
});

test('the glider now flies over the pond and splashes down without damage', async ({ page }) => {
  await open(page);
  await teleport(page, 27, 7); // east edge of the tower top, level with the pond's widest row
  await page.evaluate(() => window.__debugApi.pause());
  await page.keyboard.down('ArrowRight');
  // Step off the edge and past the coyote window, then open the glider (deterministic, see p2-2).
  await page.evaluate(() => {
    const api = window.__debugApi;
    for (let i = 0; i < 120 && api.player().grounded; i++) api.step(1);
    api.step(8);
  });
  await page.keyboard.press('Space');
  await page.evaluate(() => window.__debugApi.step(1));
  expect((await player(page)).gliding).toBe(true);
  await page.keyboard.down('ArrowRight');
  await page.evaluate(() => window.__debugApi.resume());
  await expect.poll(async () => (await player(page)).gliding, { timeout: 10_000, intervals: [50] }).toBe(false);
  await page.keyboard.up('ArrowRight');
  const p = await player(page);
  expect(p.x).toBeGreaterThan(31 * 16); // out over the pond (water used to stop the glider at its edge)
  expect(p.hp).toBe(12);
  expect(p.swimming || p.grounded).toBe(true);
});
