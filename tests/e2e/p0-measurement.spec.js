import { test, expect } from '@playwright/test';

/** Collect page errors so a test fails on any runtime error. */
function trackErrors(page) {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  return errors;
}

test('boots with the WebGL renderer and shows the measurement overlay', async ({ page }, testInfo) => {
  const errors = trackErrors(page);
  await page.goto('/?map=height&debug=1');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await expect(page.locator('#game-canvas')).toBeVisible();
  await expect(page.locator('#fatal')).toBeHidden();

  expect(await page.evaluate(() => window.__debugApi.rendererName())).toBe('webgl');

  // Overlay shows live numbers.
  await expect(page.locator('#debug-panel')).toBeVisible();
  await expect(page.locator('#debug-stats')).toContainText('FPS', { timeout: 5_000 });
  await expect.poll(() => page.evaluate(() => window.__debugApi.summary().frames)).toBeGreaterThan(10);
  await expect.poll(() => page.evaluate(() => window.__debugApi.drawCalls())).toBeGreaterThan(0);

  await page.screenshot({ path: testInfo.outputPath('overlay.png') });
  expect(errors).toEqual([]);
  expect(await page.evaluate(() => window.__debugApi.errors())).toBe(0);
});

test('load test controls change the sprite count', async ({ page }) => {
  await page.goto('/?map=height&debug=1&bench=200');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  expect(await page.evaluate(() => window.__debugApi.sprites())).toBe(200);

  await page.getByRole('button', { name: '負荷 ×2' }).click();
  expect(await page.evaluate(() => window.__debugApi.sprites())).toBe(400);
  await page.getByRole('button', { name: '負荷 ÷2' }).click();
  expect(await page.evaluate(() => window.__debugApi.sprites())).toBe(200);
  await page.getByRole('button', { name: '負荷 0' }).click();
  expect(await page.evaluate(() => window.__debugApi.sprites())).toBe(0);
});

test('timed measurement produces a markdown report', async ({ page }) => {
  await page.goto('/?map=height&debug=1&bench=100&reportSec=2');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await page.locator('#debug-report-start').click();
  await expect(page.locator('#debug-modal')).toBeVisible({ timeout: 10_000 });
  const body = await page.locator('#debug-modal-body').inputValue();
  expect(body).toContain('### 計測レポート');
  expect(body).toContain('平均 FPS');
  expect(body).toContain('| 負荷テストのスプライト数 | 100 |');
});

test('runtime errors are shown on screen', async ({ page }) => {
  await page.goto('/?map=height');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await expect(page.locator('#error-badge')).toBeHidden();
  await page.evaluate(() => setTimeout(() => {
    throw new Error('e2e-intentional-error');
  }, 0));
  await expect(page.locator('#error-badge')).toBeVisible();
  await expect(page.locator('#error-badge')).toHaveText('エラー 1');
  await page.locator('#error-badge').click();
  await expect(page.locator('#debug-modal-body')).toHaveValue(/e2e-intentional-error/);
});

test('debug panel toggles and is hidden by default', async ({ page }) => {
  await page.goto('/?map=height');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await expect(page.locator('#debug-panel')).toBeHidden();
  await page.locator('#debug-toggle').click();
  await expect(page.locator('#debug-panel')).toBeVisible();
});
