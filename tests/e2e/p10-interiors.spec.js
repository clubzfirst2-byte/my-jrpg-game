import { test, expect } from '@playwright/test';

// P10.1: inside the village houses — walk in through the door, shop across the counter, sleep in
// the inn until morning, walk back out over the mat.

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);

async function openVillage(page) {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/?map=world&time=10');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await api(page, 'clearEnemies');
  return errors;
}

/** Holds a key until `done()` is true (or gives up). */
// The limit is only how long to wait before giving up (a slow renderer walks fewer game ticks per second).
async function holdUntil(page, key, done, ms = 12_000) {
  await page.keyboard.down(key);
  try {
    await expect.poll(done, { timeout: ms, intervals: [50] }).toBe(true);
  } finally {
    await page.keyboard.up(key);
  }
}

/** Walks in through the door of a house: from two tiles south of its door, up. */
async function enter(page, door, room) {
  await api(page, 'teleport', door.tx, door.ty + 1);
  await page.waitForTimeout(200);
  await holdUntil(page, 'ArrowUp', async () => (await api(page, 'area')) === room);
}

test('in through the shop door, buying across the counter, out over the mat', async ({ page }, testInfo) => {
  const errors = await openVillage(page);
  await enter(page, { tx: 16, ty: 86 }, 'shop');
  await expect.poll(async () => (await api(page, 'toasts')).some((t) => t.includes('風見の雑貨屋'))).toBe(true);
  // Up to the counter: the shopkeeper is across it.
  await holdUntil(page, 'ArrowUp', async () => (await api(page, 'nearby')) === 'talk');
  await expect(page.locator('#use-button')).toHaveText('話す（雑貨屋）');
  await page.screenshot({ path: testInfo.outputPath('shop.png') });
  await page.keyboard.press('j');
  await expect.poll(async () => (await api(page, 'dialogue'))?.speaker).toBe('雑貨屋');
  for (let k = 0; k < 6 && !(await api(page, 'dialogue'))?.choices; k++) await page.click('#dialogue');
  await page.click('#dialogue-choice-0'); // 見せて
  await expect(page.locator('#shop-menu')).toBeVisible();
  await page.click('#shop-close');
  await expect(page.locator('#shop-menu')).toBeHidden();
  // Back out: down over the mat.
  // The world resumes (and input is reset) on the next frame after the shop closes.
  await page.waitForTimeout(150);
  await holdUntil(page, 'ArrowDown', async () => (await api(page, 'area')) === null);
  const p = await api(page, 'player');
  expect(Math.floor(p.x / 16)).toBe(16);
  expect(Math.floor(p.y / 16)).toBeGreaterThanOrEqual(87);
  expect(errors).toEqual([]);
});

test('sleeping in the inn until morning', async ({ page }, testInfo) => {
  const errors = await openVillage(page);
  await api(page, 'setHp', 4);
  await enter(page, { tx: 18, ty: 94 }, 'inn');
  // To the bed west of the door.
  await holdUntil(page, 'ArrowLeft', async () => (await api(page, 'player')).x < 102 * 16 + 8, 9000);
  await holdUntil(page, 'ArrowUp', async () => (await api(page, 'nearby')) === 'sleep');
  await expect(page.locator('#use-button')).toHaveText('眠る');
  await page.click('#use-button');
  await expect(page.locator('#dialogue-choice-0')).toHaveText('朝まで眠る');
  await page.screenshot({ path: testInfo.outputPath('bed.png') });
  await page.click('#dialogue-choice-0');
  expect((await api(page, 'weather')).clock).toMatch(/^06:0\d/);
  expect((await api(page, 'player')).hp).toBe((await api(page, 'progress')).maxHp);
  await page.click('#dialogue');
  await expect(page.locator('#dialogue')).toBeHidden();
  expect(errors).toEqual([]);
});
