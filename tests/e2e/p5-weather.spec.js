import { test, expect } from '@playwright/test';

// P5: time of day and weather.

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);

async function open(page, query = '') {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto(`/?map=island${query}`);
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await api(page, 'clearEnemies');
  return errors;
}

test('night is dark with lights; a clear day needs no light map', async ({ page }, testInfo) => {
  const errors = await open(page, '&time=22');
  await api(page, 'teleport', 76, 44); // by the camp fire
  await expect.poll(async () => (await api(page, 'weather')).lightOn).toBe(true);
  await expect(page.locator('#hud-clock')).toContainText('22:');
  await page.screenshot({ path: testInfo.outputPath('night.png') });
  await api(page, 'setHour', 10); // the first morning is always clear
  await expect.poll(async () => (await api(page, 'weather')).lightOn).toBe(false); // no cost by day
  await expect(page.locator('#hud-clock')).toContainText('10:');
  const w = await api(page, 'weather');
  await testInfo.attach('light-cost', { body: JSON.stringify(w), contentType: 'application/json' });
  expect(errors).toEqual([]);
});

test('rain falls, puts a fire out, and keeps things from catching fire', async ({ page }, testInfo) => {
  const errors = await open(page, '&time=10');
  await api(page, 'teleport', 30, 40);
  expect(await api(page, 'envIgnite', 32, 40)).toBe(true);
  await api(page, 'setWeather', 'rain');
  await expect.poll(async () => (await api(page, 'weather')).rainVisible).toBe(true);
  await expect(page.locator('#hud-clock')).toContainText('雨');
  await expect.poll(async () => (await api(page, 'env')).burning, { timeout: 10_000 }).toBe(0);
  expect(await api(page, 'envIgnite', 34, 40)).toBe(false);
  await page.screenshot({ path: testInfo.outputPath('rain.png') });
  expect(errors).toEqual([]);
});

test('no rain in the cave', async ({ page }) => {
  const errors = await open(page, '&weather=rain&time=12');
  await expect.poll(async () => (await api(page, 'weather')).rainVisible).toBe(true);
  await api(page, 'teleport', 104, 12);
  await expect.poll(async () => (await api(page, 'weather')).rainVisible).toBe(false);
  expect(errors).toEqual([]);
});

test('lightning warns, then strikes and hurts the player standing there', async ({ page }, testInfo) => {
  const errors = await open(page, '&weather=storm&time=12');
  await api(page, 'teleport', 30, 40);
  const hp = (await api(page, 'player')).hp;
  await api(page, 'forceStrike', 30, 40);
  expect(await api(page, 'strikePending')).toBe(true);
  await expect.poll(() => api(page, 'events'), { timeout: 5_000 }).toContain('lightning');
  expect((await api(page, 'player')).hp).toBeLessThan(hp);
  await page.screenshot({ path: testInfo.outputPath('storm.png') });
  expect(errors).toEqual([]);
});

test('the time of day is saved and comes back with つづきから', async ({ page }) => {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await page.click('#title-new');
  await api(page, 'skipOpening'); // v1.0: the opening (C9) is not what this test is about
  await expect(page.locator('#hud-clock')).toContainText('07:');
  await api(page, 'setHour', 20);
  expect(await api(page, 'saveNow')).toBe(true);
  await page.reload();
  await expect(page.locator('#title-continue')).toBeEnabled({ timeout: 20_000 });
  await page.click('#title-continue');
  await expect(page.locator('#hud-clock')).toContainText('20:');
  expect(errors).toEqual([]);
});
