import { test, expect } from '@playwright/test';

// P8: the open-world foundation — chunk streaming, region art bundles, saving differences,
// and the long-play tour.

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);

async function open(page, query = '') {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto(`/?map=world&time=10${query}`);
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await api(page, 'clearEnemies');
  return errors;
}

const STOPS = [
  [47, 72],
  [50, 100],
  [48, 190],
  [36, 236],
  [48, 60],
];

test('travelling around the world again and again does not pile up memory', async ({ page }) => {
  const errors = await open(page);
  /** @type {any[]} */
  const laps = [];
  // Streaming finishes over a few frames: read the numbers once nothing is built or freed anymore.
  const settled = async () => {
    let last = '';
    for (let k = 0; k < 40; k++) {
      const s = await api(page, 'stream');
      const key = `${s.built}/${s.freed}/${s.bundles}`;
      if (key === last) return s;
      last = key;
      await page.waitForTimeout(150);
    }
    return api(page, 'stream');
  };
  for (let lap = 0; lap < 4; lap++) {
    for (const [tx, ty] of STOPS) {
      await api(page, 'teleport', tx, ty);
      await page.waitForTimeout(250);
    }
    laps.push(await settled());
  }
  // Chunks are built and freed all along, but what is alive stays the same lap after lap.
  expect(laps[3].built).toBeGreaterThan(laps[0].built);
  expect(laps[3].freed).toBeGreaterThan(laps[0].freed);
  expect(laps[3].textures).toBeLessThanOrEqual(laps[1].textures + 1);
  expect(laps[3].displayObjects).toBeLessThanOrEqual(laps[1].displayObjects * 1.1);
  expect(laps[3].chunks).toBeLessThanOrEqual(9);
  expect(errors).toEqual([]);
});

test('chunk borders look exactly the same as the whole map drawn at once', async ({ page, browser }, testInfo) => {
  // Streaming: arrive at the spot after a trip to the desert (chunks built in another order).
  await open(page);
  await api(page, 'teleport', 48, 190);
  await page.waitForTimeout(300);
  await api(page, 'teleport', 60, 30); // near the corner of 4 chunks (x 64, y 32), with cliffs
  await api(page, 'pause');
  await api(page, 'setVisualTime', 100); // the same instant of every animation in both pages
  const hideHud = (p) => p.evaluate(() => (document.getElementById('ui').style.visibility = 'hidden')); // the clock ticks
  await hideHud(page);
  await page.waitForTimeout(300);
  const streamed = await page.locator('#game-canvas').screenshot();
  // Whole map at once.
  const other = await browser.newPage({ viewport: page.viewportSize() ?? undefined });
  await open(other, '&chunks=all');
  await api(other, 'teleport', 48, 190); // same trip: the same landmarks discovered (their arrows are drawn)
  await other.waitForTimeout(300);
  await api(other, 'teleport', 60, 30);
  await api(other, 'pause');
  await api(other, 'setVisualTime', 100);
  await hideHud(other);
  await other.waitForTimeout(300);
  const whole = await other.locator('#game-canvas').screenshot();
  await testInfo.attach('streamed', { body: streamed, contentType: 'image/png' });
  await testInfo.attach('whole', { body: whole, contentType: 'image/png' });
  expect(streamed.equals(whole)).toBe(true);
  await other.close();
});

test('a region’s art is loaded near it and released away from it', async ({ page }) => {
  const errors = await open(page);
  await api(page, 'teleport', 48, 40);
  await page.waitForTimeout(300);
  expect((await api(page, 'stream')).bundleNames).not.toContain('region:desert');
  await api(page, 'teleport', 48, 200);
  await expect.poll(async () => (await api(page, 'stream')).bundleNames, { timeout: 5_000 }).toContain('region:desert');
  expect((await api(page, 'stream')).region).toBe('desert');
  await api(page, 'teleport', 48, 40);
  await expect.poll(async () => (await api(page, 'stream')).bundleNames, { timeout: 5_000 }).not.toContain('region:desert');
  expect(errors).toEqual([]);
});

test('a broken jar stays broken after つづきから (the world is saved as differences)', async ({ page }) => {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await page.click('#title-new');
  await api(page, 'clearEnemies');
  // The jar at the camp (73,36): hit it from the south.
  await api(page, 'teleport', 73, 37);
  await api(page, 'face', 'up');
  await expect
    .poll(
      async () => {
        await page.keyboard.press('KeyJ');
        return (await api(page, 'envTile', 73, 36)).material;
      },
      { timeout: 5_000 },
    )
    .not.toBe('jar');
  expect(await api(page, 'saveNow')).toBe(true);
  await page.reload();
  await expect(page.locator('#title-continue')).toBeEnabled({ timeout: 20_000 });
  await page.click('#title-continue');
  expect((await api(page, 'envTile', 73, 36)).material).not.toBe('jar');
  expect(errors).toEqual([]);
});

test('the auto tour runs through the regions and writes a report', async ({ page }) => {
  const errors = await open(page, '&debug=1');
  await api(page, 'startTour', 0.15); // 9 seconds
  await expect.poll(() => api(page, 'tourRunning'), { timeout: 20_000 }).toBe(false);
  expect((await api(page, 'tourResult')).length).toBeGreaterThan(0);
  await expect(page.locator('#debug-modal')).toBeVisible();
  await expect(page.locator('#debug-modal-body')).toHaveValue(/自動巡回/);
  expect(errors).toEqual([]);
});
