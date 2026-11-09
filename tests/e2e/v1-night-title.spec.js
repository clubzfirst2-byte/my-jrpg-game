import { test, expect } from '@playwright/test';
import { waitTicks } from './ticks.js';

// Final QA A-1: started from the title (normal play), nights and dark rooms were never dark — the
// light map had been drawn once at its starting size while boot waited for the save, and its sprite
// never followed the resize (src/view/weatherView.js createLightMap). The ?map= tests could not see
// it, so this one goes through the title.

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);

/** Mean brightness (0..255) of the screen as shown, from a screenshot decoded in the page. */
async function brightness(page) {
  const png = (await page.screenshot()).toString('base64');
  return page.evaluate(async (b64) => {
    const img = new Image();
    img.src = `data:image/png;base64,${b64}`;
    await img.decode();
    const c = document.createElement('canvas');
    c.width = img.width;
    c.height = img.height;
    const g = /** @type {CanvasRenderingContext2D} */ (c.getContext('2d'));
    g.drawImage(img, 0, 0);
    const d = g.getImageData(0, 0, c.width, c.height).data;
    let sum = 0;
    for (let i = 0; i < d.length; i += 4) sum += 0.299 * d[i] + 0.587 * d[i + 1] + 0.114 * d[i + 2];
    return sum / (d.length / 4);
  }, png);
}

/** Title → はじめから → the opening skipped, in clear weather, no enemies. */
async function startFromTitle(page) {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await page.click('#title-new');
  await expect(page.locator('#title-screen')).toBeHidden();
  await api(page, 'skipOpening');
  await api(page, 'clearEnemies');
  await api(page, 'setWeather', 'clear');
  return errors;
}

/** Sets the hour, lets a few frames draw, and measures. */
async function at(page, hour) {
  await api(page, 'setHour', hour);
  await waitTicks(page, 20);
  await page.waitForTimeout(200);
  return brightness(page);
}

test('from the title, 23:00 is much darker than noon (the light map works in normal play)', async ({ page }, testInfo) => {
  const errors = await startFromTitle(page);
  const noon = await at(page, 12);
  await page.screenshot({ path: testInfo.outputPath('title-noon.png') });
  const night = await at(page, 23);
  await page.screenshot({ path: testInfo.outputPath('title-night.png') });
  expect((await api(page, 'weather')).lightOn).toBe(true);
  // (QA measured 105 for both before the fix; ?map=world&time=23 gives about 38)
  expect(night).toBeLessThan(noon * 0.6);
  expect(errors).toEqual([]);
});

test('from the title, the dark trial room (灯りの試練) is dark even at noon', async ({ page }, testInfo) => {
  const errors = await startFromTitle(page);
  const noon = await at(page, 12);
  await api(page, 'teleport', 104, 31);
  await waitTicks(page, 20);
  await page.waitForTimeout(200);
  const room = await brightness(page);
  await page.screenshot({ path: testInfo.outputPath('title-dark-room.png') });
  expect(room).toBeLessThan(noon * 0.6);
  expect(errors).toEqual([]);
});
