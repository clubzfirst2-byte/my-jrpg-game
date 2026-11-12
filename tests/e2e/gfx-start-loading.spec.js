import { test, expect } from '@playwright/test';

// gfx v2 integration (start-up): the title shows as soon as its own art and the save are read; the
// world (art sheets, atlases, the view, the HUD) is prepared after it (main.js). A start pressed before
// the start area is drawn with all its art waits behind a short loading note, so the world never shows
// with missing or stand-in pictures.

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);

test('the title comes before the world is ready; a start pressed then waits behind the loading note and the start area shows complete', async ({ page }) => {
  const problems = [];
  page.on('pageerror', (e) => problems.push(`pageerror: ${e.message}`));
  page.on('console', (m) => {
    if (m.type() === 'warning' || m.type() === 'error') problems.push(`${m.type()}: ${m.text()}`);
  });
  // a slow phone: the world's preparation takes a while after the title
  const cdp = await page.context().newCDPSession(page);
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
  await page.goto('/');
  await expect(page.locator('#title-screen')).toBeVisible({ timeout: 30_000 });
  // the title does not wait for the world
  expect(await page.evaluate(() => document.body.dataset.ready === 'true')).toBe(false);
  await page.click('#title-new');
  await expect(page.locator('#title-screen')).toBeHidden();
  await expect(page.locator('#start-loading')).toBeVisible();
  // the note goes once the start area is drawn with its art (and the HUD's frames are in)
  await expect(page.locator('#start-loading')).toBeHidden({ timeout: 60_000 });
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 1 });
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true');
  const s = await api(page, 'stream');
  expect(s.pending).toBe(0);
  expect(s.chunks).toBeGreaterThan(0);
  const e = await api(page, 'terrainEdges');
  expect(e.fallbacks).toBe(0);
  expect(e.missing).toEqual([]);
  // the game runs: the opening (a new game) is on
  await expect.poll(() => api(page, 'titleVisible')).toBe(false);
  expect(problems).toEqual([]);
});

test('a start pressed once the world is ready: the note only for a moment, the game goes on', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await page.click('#title-new');
  await expect(page.locator('#start-loading')).toBeHidden({ timeout: 5_000 });
  await expect(page.locator('#title-screen')).toBeHidden();
});
