import { test, expect } from '@playwright/test';

// P9: villagers, conversations, quests and the shop in 風見の村 (the plains).

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);

async function openVillage(page) {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/?map=world&time=10');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await api(page, 'clearEnemies');
  await api(page, 'teleport', 24, 91);
  await page.waitForTimeout(300);
  return errors;
}

/** Taps through the lines until the box asks a question or closes. */
async function readOn(page) {
  for (let k = 0; k < 10; k++) {
    const v = await api(page, 'dialogue');
    if (!v || v.choices) return v;
    await page.click('#dialogue');
  }
  return api(page, 'dialogue');
}

test('talking with the attack button; accepting the elder’s request starts a quest', async ({ page }, testInfo) => {
  const errors = await openVillage(page);
  await api(page, 'standBy', 'elder');
  await expect.poll(() => api(page, 'nearby')).toBe('talk');
  await expect(page.locator('#use-button')).toContainText('話す');
  await page.keyboard.press('KeyJ'); // the attack button talks to the villager in front
  await expect(page.locator('#dialogue')).toBeVisible();
  await expect(page.locator('.dialogue-speaker')).toHaveText('長老');
  const tick = await api(page, 'tick');
  await page.waitForTimeout(200);
  expect(await api(page, 'tick')).toBe(tick); // the world waits while talking
  const q = await readOn(page);
  expect(q.choices).toEqual(['引き受ける', 'また今度']);
  await page.screenshot({ path: testInfo.outputPath('elder.png') });
  await page.click('#dialogue-choice-0');
  await readOn(page);
  await expect(page.locator('#dialogue')).toBeHidden();
  expect((await api(page, 'progress')).quests.lost_charm).toBe('active');
  await expect.poll(async () => (await api(page, 'toasts')).join('|')).toContain('なくしたお守り');
  // The quest log.
  await page.click('#bag-button');
  await page.click('#inv-tab-quest');
  await expect(page.locator('#inv-quest-lost_charm')).toContainText('進行中');
  await page.click('#inv-close');
  expect(errors).toEqual([]);
});

test('bringing the charm back completes the quest (reward: money and a star shard)', async ({ page }) => {
  const errors = await openVillage(page);
  await api(page, 'talkTo', 'elder');
  await readOn(page);
  await page.click('#dialogue-choice-0');
  await readOn(page);
  await api(page, 'give', 'lost_charm', 1);
  await api(page, 'talkTo', 'elder');
  await readOn(page);
  const p = await api(page, 'progress');
  expect(p.quests.lost_charm).toBe('done');
  expect(p.inv.money).toBe(150);
  expect(p.inv.items.star_shard).toBe(1);
  await expect.poll(async () => (await api(page, 'toasts')).join('|')).toContain('達成');
  expect(errors).toEqual([]);
});

test('the shop: buy arrows, sell a fang', async ({ page }, testInfo) => {
  const errors = await openVillage(page);
  await api(page, 'addMoney', 20);
  await api(page, 'give', 'beast_fang', 1);
  await api(page, 'talkTo', 'merchant');
  await readOn(page);
  await page.click('#dialogue-choice-0'); // 見せて
  await expect(page.locator('#shop-menu')).toBeVisible();
  await page.click('#shop-buy-arrow');
  expect((await api(page, 'inventory')).items.arrow).toBe(16);
  expect((await api(page, 'inventory')).money).toBe(17);
  await page.click('#shop-tab-sell');
  await page.click('#shop-sell-beast_fang');
  expect((await api(page, 'inventory')).money).toBe(22);
  await page.screenshot({ path: testInfo.outputPath('shop.png') });
  await page.click('#shop-close');
  await expect(page.locator('#shop-menu')).toBeHidden();
  expect(await api(page, 'shopOpen')).toBe(null);
  expect(errors).toEqual([]);
});

test('quests and flags are saved', async ({ page }) => {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await page.click('#title-new');
  await api(page, 'skipOpening'); // v1.0: the opening (C9) is not what this test is about
  await api(page, 'clearEnemies');
  await api(page, 'teleport', 24, 91);
  await api(page, 'talkTo', 'guard');
  await readOn(page);
  await page.click('#dialogue-choice-0');
  await readOn(page);
  expect(await api(page, 'saveNow')).toBe(true);
  await page.reload();
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 40_000 }); // (the title comes before the world is ready: gfx v2 start-up)
  await expect(page.locator('#title-continue')).toBeEnabled({ timeout: 20_000 });
  await page.click('#title-continue');
  expect((await api(page, 'progress')).quests.windmill_watch).toBe('active');
  expect(errors).toEqual([]);
});
