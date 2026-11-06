import { test, expect } from '@playwright/test';

// The hero's release art (src/art-release/hero, under review): drawn by action and frame with
// ?hero=release; normal play keeps the current hero until it is approved.

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

test('normal play does not use the release hero', async ({ page }) => {
  await open(page, '');
  await page.waitForTimeout(200);
  expect((await api(page, 'heroPose')).texture).toBeNull();
  expect((await api(page, 'art')).hero).toMatchObject({ w: 16, h: 16 });
});
