import { test, expect } from '@playwright/test';

// P10.2: the seasons on screen — the clock says the season and day, each season has its own look
// (its own art bundle, loaded while it lasts), and it snows in winter.

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);

async function open(page, query) {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto(`/?map=world&time=10${query}`);
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await api(page, 'clearEnemies');
  return errors;
}

test('winter: snow on the ground and in the air, and the clock says so', async ({ page }, testInfo) => {
  const errors = await open(page, '&season=winter&weather=snow');
  await api(page, 'teleport', 50, 92);
  await expect.poll(async () => (await api(page, 'season')).view).toBe('winter');
  await expect(page.locator('#hud-clock')).toContainText('冬 1日目');
  await expect(page.locator('#hud-clock')).toContainText('雪');
  await expect.poll(async () => (await api(page, 'weather')).snowVisible).toBe(true);
  expect((await api(page, 'weather')).rainVisible).toBe(false);
  expect((await api(page, 'stream')).bundleNames).toContain('season:winter');
  await page.screenshot({ path: testInfo.outputPath('winter.png') });
  expect(errors).toEqual([]);
});

test('when the season turns, the world is redrawn in the new season and the old art is let go', async ({ page }) => {
  const errors = await open(page, '&season=autumn');
  await api(page, 'teleport', 30, 40);
  await expect.poll(async () => (await api(page, 'season')).view).toBe('autumn');
  const before = await api(page, 'stream');
  expect(before.bundleNames).toContain('season:autumn');
  await api(page, 'setSeason', 'winter');
  await expect.poll(async () => (await api(page, 'season')).view).toBe('winter');
  await expect.poll(async () => (await api(page, 'toasts')).some((t) => t.includes('冬になった'))).toBe(true);
  const after = await api(page, 'stream');
  expect(after.bundleNames).toContain('season:winter');
  expect(after.bundleNames).not.toContain('season:autumn');
  expect(after.built).toBeGreaterThan(before.built); // every chunk was rebuilt
  expect(after.textures).toBeLessThanOrEqual(before.textures + 1);
  // Summer is the plain art: no season bundle at all.
  await api(page, 'setSeason', 'summer');
  await expect.poll(async () => (await api(page, 'season')).view).toBe('summer');
  expect((await api(page, 'stream')).bundleNames.some((b) => b.startsWith('season:'))).toBe(false);
  expect(errors).toEqual([]);
});
