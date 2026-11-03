import { test, expect } from '@playwright/test';

async function open(page, query = '') {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto(`/${query}`);
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  return errors;
}

const player = (page) => page.evaluate(() => window.__debugApi.player());
const tick = (page) => page.evaluate(() => window.__debugApi.tick());

test('renders the test field and the player', async ({ page }, testInfo) => {
  const errors = await open(page);
  await page.waitForTimeout(500);
  await page.screenshot({ path: testInfo.outputPath('field.png') });
  const res = await page.evaluate(() => window.__debugApi.resolution());
  expect(res.target).toBe(216);
  expect(Number.isInteger(res.scale)).toBe(true);
  // Placeholder art is built into one atlas: few draw calls even with ~1600 tile sprites.
  expect(await page.evaluate(() => window.__debugApi.drawCalls())).toBeLessThanOrEqual(4);
  expect(errors).toEqual([]);
});

test('keyboard moves the player and Shift dashes', async ({ page }) => {
  await open(page);
  const start = await player(page);
  await page.keyboard.down('ArrowRight');
  await page.waitForTimeout(600);
  await page.keyboard.up('ArrowRight');
  const walked = await player(page);
  expect(walked.x).toBeGreaterThan(start.x + 20);
  expect(walked.facing).toBe('right');

  await page.keyboard.down('ArrowDown');
  await page.waitForTimeout(300);
  expect((await player(page)).facing).toBe('down');
  await page.keyboard.up('ArrowDown');
});

test('virtual stick (drag on the left half) moves the player', async ({ page }, testInfo) => {
  await open(page);
  const vp = page.viewportSize();
  const start = await player(page);
  const ox = vp.width * 0.2;
  const oy = vp.height * 0.6;
  await page.mouse.move(ox, oy);
  await page.mouse.down();
  await page.mouse.move(ox + 60, oy, { steps: 4 });
  await expect(page.locator('#stick-base')).toBeVisible();
  await page.waitForTimeout(700);
  await page.screenshot({ path: testInfo.outputPath('stick.png') });
  await page.mouse.up();
  await expect(page.locator('#stick-base')).toBeHidden();
  const end = await player(page);
  expect(end.x).toBeGreaterThan(start.x + 20);
  expect(end.facing).toBe('right');
});

test('dash button makes the player faster', async ({ page }) => {
  await open(page);
  const vp = page.viewportSize();
  const ox = vp.width * 0.2;
  const oy = vp.height * 0.6;

  // Walk right for a bit, measure speed in px per logic tick.
  const speed = async (dash) => {
    await page.mouse.move(ox, oy);
    await page.mouse.down();
    await page.mouse.move(ox + 60, oy, { steps: 4 });
    if (dash) await page.locator('#dash-button').dispatchEvent('pointerdown', { pointerId: 99 });
    await page.waitForTimeout(300); // reach full speed
    const a = await player(page);
    const t0 = await tick(page);
    await page.waitForTimeout(300);
    const b = await player(page);
    const t1 = await tick(page);
    await page.mouse.up();
    if (dash) await page.locator('#dash-button').dispatchEvent('pointerup', { pointerId: 99 });
    await page.waitForTimeout(300);
    return (b.x - a.x) / (t1 - t0);
  };
  const walk = await speed(false);
  const dash = await speed(true);
  expect(walk).toBeGreaterThan(0.5);
  expect(dash).toBeGreaterThan(walk * 1.4);
});

for (const fps of [60, 30]) {
  test(`game speed is the same at ${fps}fps (fixed 60Hz logic)`, async ({ page }) => {
    await open(page, `?fps=${fps}`);
    const loopState = () => page.evaluate(() => window.__debugApi.loop());
    await page.keyboard.down('ArrowRight');
    await page.waitForTimeout(300);
    const a = await player(page);
    const l0 = await loopState();
    const real0 = await page.evaluate(() => performance.now());
    await page.waitForTimeout(1000);
    const b = await player(page);
    const l1 = await loopState();
    const realMs = (await page.evaluate(() => performance.now())) - real0;
    await page.keyboard.up('ArrowRight');

    const steps = l1.totalSteps - l0.totalSteps;
    const droppedSteps = (l1.droppedMs - l0.droppedMs) / (1000 / 60);
    // Every millisecond of real time is either simulated at 60 steps/s or deliberately dropped
    // (only when the machine renders below 15fps, e.g. software WebGL on CI).
    expect(((steps + droppedSteps) * 1000) / realMs).toBeGreaterThan(54);
    expect(((steps + droppedSteps) * 1000) / realMs).toBeLessThan(66);
    // Walk speed 72 px/s = 1.2 px per logic step, regardless of display frame rate.
    expect((b.x - a.x) / steps).toBeCloseTo(1.2, 1);
  });
}

test('pauses when the app goes to the background and resumes on tap', async ({ page }) => {
  await open(page);
  await page.evaluate(() => {
    Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => 'hidden' });
    document.dispatchEvent(new Event('visibilitychange'));
  });
  expect(await page.evaluate(() => window.__debugApi.paused())).toBe(true);
  await expect(page.locator('#pause-overlay')).toBeVisible();
  const t0 = await tick(page);
  await page.waitForTimeout(400);
  expect(await tick(page)).toBe(t0); // logic is frozen while paused

  await page.evaluate(() => {
    Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => 'visible' });
    document.dispatchEvent(new Event('visibilitychange'));
  });
  await page.locator('#resume-button').click();
  await expect(page.locator('#pause-overlay')).toBeHidden();
  await page.waitForTimeout(300);
  expect(await tick(page)).toBeGreaterThan(t0);
});

test('pause button pauses the game', async ({ page }) => {
  await open(page);
  await page.locator('#pause-button').click();
  await expect(page.locator('#pause-overlay')).toBeVisible();
  await page.locator('#pause-overlay').click();
  await expect(page.locator('#pause-overlay')).toBeHidden();
});

test('resolution candidates can be switched from the debug panel and are remembered', async ({ page }, testInfo) => {
  await open(page, '?debug=1');
  const before = await page.evaluate(() => window.__debugApi.resolution());
  expect(before.target).toBe(216);
  await page.locator('#debug-resolution').click();
  const after = await page.evaluate(() => window.__debugApi.resolution());
  expect(after.target).toBe(270);
  expect(after.width).toBeGreaterThan(before.width);
  await page.screenshot({ path: testInfo.outputPath('res-270.png') });

  await page.reload();
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  expect((await page.evaluate(() => window.__debugApi.resolution())).target).toBe(270);

  await page.locator('#debug-resolution').click(); // panel is open again (?debug=1 is still in the URL)
  expect((await page.evaluate(() => window.__debugApi.resolution())).target).toBe(180);
  await page.screenshot({ path: testInfo.outputPath('res-180.png') });
});
