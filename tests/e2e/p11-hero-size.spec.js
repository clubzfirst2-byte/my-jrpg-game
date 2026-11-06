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
  // Waits are counted in logic ticks, not wall time: a slow renderer runs fewer ticks per second,
  // and the speed must be read after the walk has reached full speed.
  const read = () => page.evaluate(() => ({ x: window.__debugApi.player().x, t: window.__debugApi.tick() }));
  const untilTick = async (t) => expect.poll(async () => (await read()).t, { timeout: 15_000, intervals: [30] }).toBeGreaterThanOrEqual(t);
  await page.keyboard.down('ArrowRight');
  const start = (await read()).t;
  await untilTick(start + 20);
  const a = await read();
  await untilTick(a.t + 30);
  const b = await read();
  await page.keyboard.up('ArrowRight');
  return (b.x - a.x) / (b.t - a.t);
}

/** Walking speed on the flat test field (nothing to bump into), in game px per tick. */
async function fieldSpeed(context, query) {
  const page = await context.newPage();
  await page.goto(`/?map=field${query}`);
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await api(page, 'clearEnemies');
  const speed = await walkSpeed(page);
  await page.close();
  return speed;
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
  await api(page, 'standBy', 'elder');
  await page.screenshot({ path: testInfo.outputPath('hero-size-test.png') });
  expect(errors).toEqual([]);
  // Movement is game logic: the same speed in game pixels per tick as with the placeholder.
  const fast = await fieldSpeed(page.context(), '&hero=test');
  const before = await fieldSpeed(page.context(), '');
  expect(Math.abs(fast - before) / before).toBeLessThan(0.05);
});

test('?hd=0 shows the game as before the real art, even with ?hero=test', async ({ page }) => {
  await open(page, '&hero=test&hd=0');
  expect(await api(page, 'art')).toMatchObject({ density: 1, overrides: 0, zoom: 1, hero: { w: 16, h: 16 } });
});

test('P12 hero prototype (?hero=proto): all 20 frames of 32×56, same feet and speed; not used by default', async ({ page }, testInfo) => {
  const warnings = [];
  page.on('console', (m) => {
    if (m.text().startsWith('art:')) warnings.push(m.text());
  });
  const errors = await open(page, '&hero=proto');
  // 12 walk frames (frame 0 is the idle pose) + 8 swim frames, every one used (no size warnings).
  expect(await api(page, 'art')).toMatchObject({ density: 2, overrides: 20, zoom: 2, hero: { w: 16, h: 28, k: 1.75 } });
  await api(page, 'standBy', 'elder');
  await page.screenshot({ path: testInfo.outputPath('hero-prototype.png') });
  expect(warnings).toEqual([]);
  expect(errors).toEqual([]);
  // The same game: walking speed in game px per tick as with the placeholder.
  const speed = await fieldSpeed(page.context(), '&hero=proto');
  expect(Math.abs(speed - (await fieldSpeed(page.context(), ''))) / speed).toBeLessThan(0.05);
  const page2 = await page.context().newPage();
  await open(page2, '');
  expect((await api(page2, 'art')).hero).toMatchObject({ w: 16, h: 16 });
});

test('P12 round 1 prototypes (?proto=all): elder, watchman, beast and goblin drawn from the prototypes', async ({ page }, testInfo) => {
  const warnings = [];
  page.on('console', (m) => {
    if (m.text().startsWith('art:')) warnings.push(m.text());
  });
  const errors = await open(page, '&proto=all');
  // 20 hero + 24 NPC (elder, watchman) + 4 enemy (beast, goblin) frames
  expect((await api(page, 'art')).overrides).toBe(48);
  const elder = (await api(page, 'npcs')).find((n) => n.id === 'elder');
  await api(page, 'teleport', elder.tx + 2, elder.ty + 1);
  await api(page, 'spawnEnemy', 'beast', elder.tx + 4, elder.ty + 2);
  await api(page, 'spawnEnemy', 'archer', elder.tx + 6, elder.ty);
  await page.waitForTimeout(300);
  await page.screenshot({ path: testInfo.outputPath('round1.png') });
  expect(warnings).toEqual([]);
  expect(errors).toEqual([]);
  // Each group can be asked for alone.
  const page2 = await page.context().newPage();
  await open(page2, '&enemy=proto');
  expect(await api(page2, 'art')).toMatchObject({ overrides: 4, hero: { h: 16 } });
});
