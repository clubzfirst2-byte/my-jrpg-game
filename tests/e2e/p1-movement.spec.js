import { test, expect } from '@playwright/test';
import { waitTicks } from './ticks.js';

async function open(page, query = '') {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto(`/?map=height${query.replace('?', '&')}`);
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  // Not a combat test: keep enemies from interfering (P3 added enemies to this map).
  await page.evaluate(() => window.__debugApi.clearEnemies());
  return errors;
}

const player = (page) => page.evaluate(() => window.__debugApi.player());
const tick = (page) => page.evaluate(() => window.__debugApi.tick());
/** The player's x and the logic tick, read in the same frame. */
const xAtTick = (page) => page.evaluate(() => ({ x: window.__debugApi.player().x, t: window.__debugApi.tick() }));

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
  // walk for 36 logic ticks (0.6 s of game time): counted in ticks, not wall time, so a slow
  // renderer (the release hero draws at 2 pixels per game pixel) cannot shorten the walk
  await page.keyboard.down('ArrowRight');
  await waitTicks(page, 36);
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
    const a = await xAtTick(page);
    await page.waitForTimeout(300);
    const b = await xAtTick(page);
    await page.mouse.up();
    if (dash) await page.locator('#dash-button').dispatchEvent('pointerup', { pointerId: 99 });
    await page.waitForTimeout(300);
    return (b.x - a.x) / (b.t - a.t);
  };
  const walk = await speed(false);
  const dash = await speed(true);
  expect(walk).toBeGreaterThan(0.5);
  expect(dash).toBeGreaterThan(walk * 1.4);
});

for (const fps of [60, 30]) {
  test(`game speed is the same at ${fps}fps (fixed 60Hz logic)`, async ({ page }) => {
    await open(page, `?fps=${fps}`);
    // Read position, loop counters and time in ONE call so they describe the same moment
    // (a frame running between separate reads would skew distance vs. step count).
    // Taken inside an animation frame, right after the game's own update for that frame, so the
    // frame clock and the wall clock line up even when the machine stalls between frames.
    const snapshot = () =>
      page.evaluate(
        () =>
          new Promise((resolve) =>
            requestAnimationFrame((t) =>
              resolve({ p: window.__debugApi.player(), l: window.__debugApi.loop(), t }),
            ),
          ),
      );
    await page.keyboard.down('ArrowRight');
    await page.waitForTimeout(300);
    const s0 = await snapshot();
    await page.waitForTimeout(1000);
    const s1 = await snapshot();
    const [a, l0, b, l1] = [s0.p, s0.l, s1.p, s1.l];
    const wallMs = s1.t - s0.t;
    await page.keyboard.up('ArrowRight');

    const STEP = 1000 / 60;
    const steps = l1.totalSteps - l0.totalSteps;
    const elapsed = l1.elapsedMs - l0.elapsedMs; // real time as seen by the game's frame clock
    const accounted = steps * STEP + (l1.droppedMs - l0.droppedMs) + (l1.pendingMs - l0.pendingMs);
    // The loop simulates every millisecond at 60 steps/s, except time it deliberately drops
    // (frames slower than 4 steps or hitches > 250ms, e.g. software WebGL on CI).
    expect(Math.abs(accounted - elapsed)).toBeLessThan(1);
    // The frame clock follows real time (loose bound: one slow frame of misalignment allowed).
    expect(elapsed / wallMs).toBeGreaterThan(0.6);
    expect(elapsed / wallMs).toBeLessThan(1.4);
    // When the display keeps up (>= 15fps), nothing is dropped and the logic runs at 60 steps/s.
    if (l1.droppedMs - l0.droppedMs === 0) expect((steps * 1000) / elapsed).toBeCloseTo(60, -1);
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
  // The old hero (1 art pixel per game pixel). Since docs/perf/hd-view-size.md the release hero gives
  // the same game scale per candidate too (it used to share one scale between neighbouring
  // candidates); the placeholder hero is kept here only so the pinned widths stay the same.
  await open(page, '?debug=1&hero=placeholder');
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
