import { test, expect } from '@playwright/test';

// The hero's release art (src/art-release/hero), drawn by action and frame. Adopted on 2026-11-08:
// normal play uses it (?hero=release is the same); ?hero=placeholder shows the old hero.

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);

async function open(page, query) {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('console', (m) => {
    if (m.text().startsWith('art:')) errors.push(m.text());
  });
  await page.goto(`/?map=field${query}`);
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await api(page, 'clearEnemies');
  return errors;
}

/** Waits until the hero's drawn texture matches. */
const drawn = (page, re) => expect.poll(async () => (await api(page, 'heroPose')).texture ?? '', { timeout: 8000, intervals: [50] }).toMatch(re);

test('release hero: standing breathes (idle), walking and dashing use their own frames, in every direction', async ({ page }, testInfo) => {
  const errors = await open(page, '&hero=release');
  await drawn(page, /^hero\.idle\.down\.\d$/);
  // every idle frame comes round
  const idle = new Set();
  for (let i = 0; i < 40 && idle.size < 4; i++) {
    idle.add((await api(page, 'heroPose')).frame);
    await page.waitForTimeout(60);
  }
  expect(idle.size).toBe(4);
  for (const [key, dir] of [
    ['ArrowRight', 'right'],
    ['ArrowLeft', 'left'],
    ['ArrowUp', 'up'],
    ['ArrowDown', 'down'],
  ]) {
    await page.keyboard.down(key);
    await drawn(page, new RegExp(`^hero\\.walk\\.${dir}\\.\\d$`));
    await page.keyboard.down('ShiftLeft');
    await drawn(page, new RegExp(`^hero\\.run\\.${dir}\\.\\d$`));
    await page.keyboard.up('ShiftLeft');
    await page.keyboard.up(key);
  }
  await page.screenshot({ path: testInfo.outputPath('hero-release.png') });
  // the hero's size is the standard (32×56 art = 16×28 game px)
  expect((await api(page, 'art')).hero).toMatchObject({ w: 16, h: 28 });
  expect(errors).toEqual([]);
});

test('release hero: sword, dodge, shield, bow and jump each show their own frames', async ({ page }, testInfo) => {
  const errors = await open(page, '&hero=release');
  await drawn(page, /^hero\.idle\.down\.\d$/);
  // record every texture drawn (short actions last a few frames only)
  await page.evaluate(() => {
    const w = /** @type {any} */ (window);
    w.__seen = new Set();
    const tick = () => {
      w.__seen.add(w.__debugApi.heroPose().texture);
      requestAnimationFrame(tick);
    };
    tick();
  });
  const seen = () => page.evaluate(() => [...(/** @type {any} */ (window).__seen)]);
  const shows = (re) => expect.poll(async () => (await seen()).some((t) => re.test(t ?? '')), { message: String(re), timeout: 6000, intervals: [50] }).toBe(true);
  await page.keyboard.press('KeyJ');
  await shows(/^hero\.attack1\.down\.\d$/);
  await page.waitForTimeout(600);
  await page.keyboard.press('KeyL');
  await shows(/^hero\.dodge\.down\.\d$/);
  await page.waitForTimeout(600);
  await page.keyboard.down('KeyI');
  await shows(/^hero\.guard\.down\.1$/);
  // the hero holds his own shield: the separate shield effect is hidden
  await page.screenshot({ path: testInfo.outputPath('hero-guard.png') });
  await page.keyboard.up('KeyI');
  await page.waitForTimeout(300);
  await page.keyboard.down('KeyU');
  await shows(/^hero\.bow\.down\.3$/);
  await page.screenshot({ path: testInfo.outputPath('hero-bow.png') });
  await page.keyboard.up('KeyU');
  await page.waitForTimeout(600);
  await page.keyboard.press('Space');
  await shows(/^hero\.jump\.down\.\d$/);
  expect(errors).toEqual([]);
});

test('release hero facing left: the sword, shield and bow frames drawn for that side', async ({ page }) => {
  const errors = await open(page, '&hero=release');
  await drawn(page, /^hero\.idle\.down\.\d$/);
  await page.evaluate(() => {
    const w = /** @type {any} */ (window);
    w.__seen = new Set();
    const tick = () => {
      w.__seen.add(w.__debugApi.heroPose().texture);
      requestAnimationFrame(tick);
    };
    tick();
  });
  const seen = () => page.evaluate(() => [...(/** @type {any} */ (window).__seen)]);
  const shows = (re) => expect.poll(async () => (await seen()).some((t) => re.test(t ?? '')), { message: String(re), timeout: 6000, intervals: [50] }).toBe(true);
  await page.keyboard.down('ArrowLeft');
  await drawn(page, /^hero\.walk\.left\.\d$/);
  await page.keyboard.up('ArrowLeft');
  await page.keyboard.press('KeyJ');
  await shows(/^hero\.attack1\.left\.\d$/);
  await page.waitForTimeout(600);
  await page.keyboard.down('KeyI');
  await shows(/^hero\.guard\.left\.1$/);
  await page.keyboard.up('KeyI');
  await page.waitForTimeout(300);
  await page.keyboard.down('KeyU');
  await shows(/^hero\.bow\.left\.3$/);
  await page.keyboard.up('KeyU');
  expect(errors).toEqual([]);
});

test('normal play uses the adopted release hero; ?hero=placeholder still shows the old one', async ({ page }) => {
  const errors = await open(page, '');
  await drawn(page, /^hero\.idle\.down\.\d$/);
  expect((await api(page, 'art')).hero).toMatchObject({ w: 16, h: 28 });
  expect(errors).toEqual([]);
  await open(page, '&hero=placeholder');
  await page.waitForTimeout(200);
  expect((await api(page, 'heroPose')).texture).toBeNull();
  expect((await api(page, 'art')).hero).toMatchObject({ w: 16, h: 16 });
});
