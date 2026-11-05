import { test, expect } from '@playwright/test';

// P11.5: the character standard (32×56 art at 2 pixels per game pixel). Without real art the game
// is exactly as before; ?hero=test shows a size-test hero (仮素材) of the new size; ?hd=0 is "before".

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);

async function open(page, query) {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto(`/?map=world&time=10&season=summer${query}`);
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await api(page, 'clearEnemies');
  return errors;
}

/** Walking speed in game px per logic tick (position and tick read together). */
async function walkSpeed(page) {
  const read = () => page.evaluate(() => ({ x: window.__debugApi.player().x, t: window.__debugApi.tick() }));
  await page.keyboard.down('ArrowRight');
  await page.waitForTimeout(300);
  const a = await read();
  await page.waitForTimeout(500);
  const b = await read();
  await page.keyboard.up('ArrowRight');
  return (b.x - a.x) / (b.t - a.t);
}

test('without real art nothing changes: 1 pixel per game pixel, the 16×16 placeholder hero', async ({ page }) => {
  const errors = await open(page, '');
  expect(await api(page, 'art')).toMatchObject({ density: 1, overrides: 0, zoom: 1, hero: { w: 16, h: 16, k: 1 } });
  expect(errors).toEqual([]);
});

test('the size-test hero: 32×56 art drawn 16×28 game px, finer canvas, same world and same speed', async ({ page }, testInfo) => {
  const errors = await open(page, '&hero=test');
  const art = await api(page, 'art');
  expect(art).toMatchObject({ density: 2, zoom: 2, hero: { w: 16, h: 28, k: 1.75 } });
  // The canvas has 2 pixels per game pixel; the game view stays near the target height.
  const res = await api(page, 'resolution');
  expect(res.artDensity).toBe(2);
  expect(Math.abs(res.gameHeight - res.target) / res.target).toBeLessThan(0.25);
  // Movement is game logic: the same speed in game pixels per tick as with the placeholder.
  await api(page, 'standBy', 'elder');
  const fast = await walkSpeed(page);
  await page.screenshot({ path: testInfo.outputPath('hero-size-test.png') });
  expect(errors).toEqual([]);

  const page2 = await page.context().newPage();
  await open(page2, '');
  await api(page2, 'standBy', 'elder');
  const before = await walkSpeed(page2);
  expect(Math.abs(fast - before) / before).toBeLessThan(0.05);
});

test('?hd=0 shows the game as before the real art, even with ?hero=test', async ({ page }) => {
  await open(page, '&hero=test&hd=0');
  expect(await api(page, 'art')).toMatchObject({ density: 1, overrides: 0, zoom: 1, hero: { w: 16, h: 16 } });
});
