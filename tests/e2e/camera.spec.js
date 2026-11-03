import { test, expect } from '@playwright/test';

async function open(page, query = '') {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto(`/${query}`);
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  return errors;
}

const player = (page) => page.evaluate(() => window.__debugApi.player());
const camera = (page) => page.evaluate(() => window.__debugApi.camera());
const teleport = (page, tx, ty) => page.evaluate(([x, y]) => window.__debugApi.teleport(x, y), [tx, ty]);

test('camera follows smoothly: lags while moving, settles on the player when stopped', async ({ page }) => {
  await open(page);
  await teleport(page, 14, 13); // open ground in the middle of the map
  await page.keyboard.down('ArrowRight');
  await page.waitForTimeout(400);
  const moving = await camera(page);
  const pMoving = await player(page);
  await page.keyboard.up('ArrowRight');
  expect(pMoving.x - moving.x).toBeGreaterThan(0.5); // trails behind the player

  await page.waitForTimeout(1200);
  const settled = await camera(page);
  const p = await player(page);
  expect(Math.abs(settled.x - p.x)).toBeLessThan(0.5);
});

test('jumping does not bob the camera', async ({ page }) => {
  await open(page);
  await teleport(page, 14, 13);
  await page.waitForTimeout(300);
  const before = await camera(page);
  await page.keyboard.down('Space');
  let maxShift = 0;
  for (let i = 0; i < 10; i++) {
    const c = await camera(page);
    maxShift = Math.max(maxShift, Math.abs(c.y - before.y));
    await page.waitForTimeout(30);
  }
  await page.keyboard.up('Space');
  expect(maxShift).toBeLessThan(0.5);
});

test('camera never shows outside the map', async ({ page }, testInfo) => {
  await open(page);
  const mapW = 40 * 16;
  const mapH = 30 * 16;
  for (const [tx, ty] of [[2, 2], [37, 2], [2, 27], [37, 27]]) {
    await teleport(page, tx, ty);
    const c = await camera(page);
    expect(c.origin.x).toBeGreaterThanOrEqual(0);
    expect(c.origin.y).toBeGreaterThanOrEqual(0);
    expect(c.origin.x + c.viewWidth).toBeLessThanOrEqual(mapW + 0.001);
    expect(c.origin.y + c.viewHeight).toBeLessThanOrEqual(mapH + 0.001);
  }
  await page.screenshot({ path: testInfo.outputPath('corner.png') });
});

test('zoom can be changed and keeps pixel-aligned rendering', async ({ page }, testInfo) => {
  const errors = await open(page, '?zoom=2');
  await teleport(page, 14, 13);
  const c = await camera(page);
  const res = await page.evaluate(() => window.__debugApi.resolution());
  expect(c.zoom).toBe(2);
  expect(c.viewWidth).toBeCloseTo(res.width / 2, 6);
  expect(Number.isInteger(c.origin.x * 2)).toBe(true);
  await page.screenshot({ path: testInfo.outputPath('zoom2.png') });

  await page.evaluate(() => window.__debugApi.setZoom(1));
  await page.waitForTimeout(100);
  expect((await camera(page)).viewWidth).toBeCloseTo(res.width, 6);
  expect(errors).toEqual([]);
});

test('the canvas uses nearest-neighbour scaling (no blurry pixels)', async ({ page }) => {
  await open(page);
  const rendering = await page.locator('#game-canvas').evaluate((el) => getComputedStyle(el).imageRendering);
  expect(['pixelated', 'crisp-edges', '-webkit-optimize-contrast']).toContain(rendering);
  const res = await page.evaluate(() => window.__debugApi.resolution());
  expect(Number.isInteger(res.scale)).toBe(true);
});

test.describe('portrait', () => {
  // iPhone 15 held upright (the project already emulates a touch iPhone; only the orientation changes).
  test.use({ viewport: { width: 393, height: 659 } });

  test('asks to rotate to landscape, can be dismissed, and the game still runs', async ({ page }) => {
    await open(page);
    expect(await page.evaluate(() => window.__debugApi.rotateHintVisible())).toBe(true);
    await page.locator('#rotate-dismiss').click();
    expect(await page.evaluate(() => window.__debugApi.rotateHintVisible())).toBe(false);
    const c = await camera(page);
    expect(c.viewHeight).toBeGreaterThan(c.viewWidth); // camera adapts to the tall screen
  });
});

test('landscape does not show the rotate hint', async ({ page }) => {
  await open(page);
  expect(await page.evaluate(() => window.__debugApi.rotateHintVisible())).toBe(false);
});
