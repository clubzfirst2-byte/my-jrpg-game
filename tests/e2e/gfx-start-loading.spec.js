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
  // (records whether the loading note was ever shown: it may come and go between two checks)
  await page.addInitScript(() => {
    window.__noteShown = false;
    new MutationObserver(() => {
      const n = document.getElementById('start-loading');
      if (n && !n.hidden) window.__noteShown = true;
    }).observe(document, { subtree: true, childList: true, attributes: true, attributeFilter: ['hidden'] });
  });
  await page.goto('/');
  await expect(page.locator('#title-screen')).toBeVisible({ timeout: 30_000 });
  // the title does not wait for the world
  expect(await page.evaluate(() => document.body.dataset.ready === 'true')).toBe(false);
  const box = await page.locator('#title-new').boundingBox();
  await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2); // (a tap as soon as the title shows)
  await expect(page.locator('#title-screen')).toBeHidden();
  expect(await page.evaluate(() => window.__noteShown)).toBe(true);
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

test('a Space pressed behind the loading note skips the opening, as the first press does without the note', async ({ page }) => {
  const cdp = await page.context().newCDPSession(page);
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
  await page.goto('/');
  await expect(page.locator('#title-screen')).toBeVisible({ timeout: 30_000 });
  const box = await page.locator('#title-new').boundingBox();
  await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
  // the game starts behind the note (the opening on), then one Space while the note is still up
  await page.waitForFunction(() => performance.getEntriesByName('beginPlay').length > 0, null, { timeout: 60_000 });
  const noteUp = await page.evaluate(() => !document.getElementById('start-loading')?.hidden);
  await page.keyboard.press('Space');
  await expect(page.locator('#start-loading')).toBeHidden({ timeout: 60_000 });
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 1 });
  expect(await api(page, 'opening')).toBe(null);
  // (when the note was already gone, this is the plain case: the first Space skips it all the same)
  test.info().annotations.push({ type: 'note up at the Space', description: String(noteUp) });
});

test('a start pressed once the world is ready: the note only for a moment, the game goes on', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await page.click('#title-new');
  await expect(page.locator('#start-loading')).toBeHidden({ timeout: 5_000 });
  await expect(page.locator('#title-screen')).toBeHidden();
});
