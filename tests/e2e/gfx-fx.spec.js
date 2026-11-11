import { test, expect } from '@playwright/test';

// gfx W5: cast shadows, lit windows at night, rain / mist / particles, hit effects — and the switch
// back to the look before them (?fx=v1 / ?v2=0). Drawing only.

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);

async function open(page, query) {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto(`/?map=world&${query}`);
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 40_000 });
  await api(page, 'clearEnemies');
  return errors;
}
async function settle(page) {
  await expect.poll(async () => (await api(page, 'stream')).pending, { timeout: 20_000 }).toBe(0);
}

test('the village at night: shadows on the ground and the windows lit, within the pools', async ({ page }, testInfo) => {
  const errors = await open(page, 'time=21&season=summer&weather=clear');
  await api(page, 'teleport', 24, 91);
  await settle(page);
  await expect.poll(async () => (await api(page, 'fxInfo')).windows.lit, { timeout: 10_000 }).toBeGreaterThan(0);
  const fx = await api(page, 'fxInfo');
  expect(fx.version).toBe('v2');
  expect((await api(page, 'art')).groups).toContain('v2/enemy'); // the enemies' v2 art by default
  expect(fx.shadows.baked).toBeGreaterThan(0);
  expect(fx.windows.glow).toBeGreaterThan(0.5);
  expect(fx.windows.lights).toBeGreaterThanOrEqual(fx.windows.sprites);
  expect(fx.particles.showing).toBeLessThanOrEqual(fx.particles.max);
  expect((await api(page, 'weather')).lightOn).toBe(true);
  await page.screenshot({ path: testInfo.outputPath('village-night.png') });
  // by day the windows are off
  await api(page, 'setHour', 11);
  await expect.poll(async () => (await api(page, 'fxInfo')).windows.lit).toBe(0);
  expect(errors).toEqual([]);
});

test('saving and continuing work as before with the effects on (drawing only)', async ({ page }) => {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 40_000 });
  await page.click('#title-new');
  await api(page, 'skipOpening');
  await api(page, 'clearEnemies');
  await api(page, 'teleport', 24, 91);
  await settle(page);
  expect((await api(page, 'fxInfo')).version).toBe('v2');
  await api(page, 'addMoney', 123);
  const before = await api(page, 'progress');
  expect(await api(page, 'saveNow')).toBe(true);
  await page.reload();
  await expect(page.locator('#title-continue')).toBeEnabled({ timeout: 40_000 });
  await page.click('#title-continue');
  await settle(page);
  // (what was saved comes back: the bag, with the money added before saving)
  const after = await api(page, 'progress');
  expect(after.inv).toEqual(before.inv);
  expect(after.inv.money).toBeGreaterThanOrEqual(123);
  expect((await api(page, 'fxInfo')).version).toBe('v2');
  expect(errors).toEqual([]);
});

test('rain: two layers, splashes and mist; a blow throws sparks for several frames', async ({ page }, testInfo) => {
  const errors = await open(page, 'time=15&season=summer&weather=rain');
  await api(page, 'teleport', 50, 104);
  await settle(page);
  await expect.poll(async () => (await api(page, 'fxInfo')).rain.splashes, { timeout: 10_000 }).toBeGreaterThan(0);
  await expect.poll(async () => (await api(page, 'fxInfo')).particles.kinds.mist).toBeGreaterThan(0);
  const fx = await api(page, 'fxInfo');
  expect(fx.rain.fancy).toBe(true);
  expect(fx.rain.drops).toBeGreaterThan(0);
  expect(fx.particles.kinds.leaves).toBe(0);
  await page.screenshot({ path: testInfo.outputPath('rain.png') });

  await api(page, 'setHp', 400);
  await api(page, 'spawnEnemy', 'slime', 51, 104);
  await api(page, 'face', 'right');
  let most = 0;
  for (let i = 0; i < 40 && most === 0; i++) {
    await page.keyboard.press('KeyJ');
    for (let k = 0; k < 3; k++) most = Math.max(most, (await api(page, 'fxInfo')).hit.active);
  }
  expect(await api(page, 'events')).toContain('hitEnemy');
  expect(most).toBeGreaterThan(0);
  expect(most).toBeLessThanOrEqual(fx.hit.pool);
  expect(errors).toEqual([]);
});

for (const q of ['fx=v1', 'v2=0']) {
  test(`?${q}: the look before — no shadows, windows, particles, splashes or sparks`, async ({ page }, testInfo) => {
    const errors = await open(page, `time=21&season=summer&weather=rain&${q}`);
    await api(page, 'teleport', 24, 91);
    await settle(page);
    await expect.poll(async () => (await api(page, 'weather')).rainVisible).toBe(true);
    await api(page, 'setHp', 400);
    await api(page, 'spawnEnemy', 'slime', 25, 91);
    await api(page, 'face', 'right');
    for (let i = 0; i < 40 && !(await api(page, 'events')).includes('hitEnemy'); i++) await page.keyboard.press('KeyJ');
    const fx = await api(page, 'fxInfo');
    expect(fx.version).toBe('v1');
    // ?v2=0 also draws the v1 enemies; ?fx=v1 turns only the effects off
    const groups = (await api(page, 'art')).groups;
    expect(groups.includes('v2/enemy')).toBe(q === 'fx=v1');
    expect(groups.includes('enemy')).toBe(q === 'v2=0');
    expect(fx.shadows).toEqual({ baked: 0, loose: 0, characters: 0 });
    expect(fx.windows.sprites).toBe(0);
    expect(fx.windows.glow).toBe(0);
    expect(fx.particles.showing).toBe(0);
    expect(fx.hit.active).toBe(0);
    expect(fx.hit.trail).toBe(0);
    expect(fx.rain.fancy).toBe(false);
    expect(fx.rain.splashes).toBe(0);
    expect(fx.rain.drops).toBeGreaterThan(0); // (the rain itself was there before)
    // the measuring switch cannot turn them on in this mode
    expect((await api(page, 'fx', 'shadows', true)).shadows).toBe(false);
    await page.screenshot({ path: testInfo.outputPath('v1.png') });
    expect(errors).toEqual([]);
  });
}

for (const q of ['', 'v2=0', 'enemy=v1']) {
  test(`${q ? `?${q}` : 'default'}: only the enemy sheet that is drawn is preloaded (no unused-preload warning)`, async ({ page }) => {
    const warnings = [];
    page.on('console', (m) => {
      if (m.type() === 'warning' && /preload/i.test(m.text())) warnings.push(m.text());
    });
    await page.goto(`/?map=world&time=10${q ? `&${q}` : ''}`);
    await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 40_000 });
    const groups = (await api(page, 'art')).groups;
    const preloaded = await page.evaluate(() => [...document.querySelectorAll('link[rel=preload]')].map((l) => l.getAttribute('href')));
    const v2 = groups.includes('v2/enemy');
    expect(preloaded.some((h) => h.includes('release-v2-enemy'))).toBe(v2);
    expect(preloaded.some((h) => /release-enemy-/.test(h))).toBe(!v2);
    await page.waitForTimeout(5000); // (the browser warns a few seconds after the load event)
    expect(warnings).toEqual([]);
  });
}
