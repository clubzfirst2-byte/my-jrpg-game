import { test, expect } from '@playwright/test';

// P6: items and equipment — the bag, picking things up, cooking at a fire, the forge, saving.

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);

async function open(page) {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/?map=island');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await api(page, 'clearEnemies');
  return errors;
}

test('the bag opens (the game pauses) and switches weapons', async ({ page }, testInfo) => {
  const errors = await open(page);
  await api(page, 'give', 'travel_sword');
  await page.click('#bag-button');
  await expect(page.locator('#inv-menu')).toBeVisible();
  const tick = await api(page, 'tick');
  await page.waitForTimeout(300);
  expect(await api(page, 'tick')).toBe(tick); // paused while the bag is open
  await page.click('#inv-weapon-1');
  expect((await api(page, 'inventory')).equip.weapon).toBe(1);
  await page.screenshot({ path: testInfo.outputPath('bag.png') });
  await page.click('#inv-close');
  await expect(page.locator('#inv-menu')).toBeHidden();
  await expect.poll(() => api(page, 'tick')).toBeGreaterThan(tick);
  await expect(page.locator('#hud-treasure')).toContainText('旅人の剣');
  expect(errors).toEqual([]);
});

test('walking over a mushroom picks it up; eating it heals', async ({ page }) => {
  const errors = await open(page);
  const mushroom = (await api(page, 'pickups')).find((p) => p.item === 'mushroom');
  await api(page, 'setHp', 4);
  await api(page, 'teleport', mushroom.tx, mushroom.ty);
  await expect.poll(async () => (await api(page, 'inventory')).items.mushroom ?? 0).toBe(1);
  await expect.poll(async () => (await api(page, 'toasts')).join('|')).toContain('森きのこを手に入れた');
  await page.keyboard.press('KeyE');
  await page.click('#inv-tab-material');
  await page.click('#inv-item-mushroom');
  expect((await api(page, 'player')).hp).toBe(6);
  expect((await api(page, 'inventory')).items.mushroom).toBeUndefined();
  expect(errors).toEqual([]);
});

test('cooking at the camp fire: a recipe is discovered', async ({ page }, testInfo) => {
  const errors = await open(page);
  await api(page, 'give', 'beast_meat', 1);
  await api(page, 'give', 'ember_pepper', 1);
  await api(page, 'teleport', 77, 42); // just south of the camp fire
  await expect.poll(() => api(page, 'nearby')).toBe('cook');
  await expect(page.locator('#use-button')).toHaveText('料理する');
  await page.click('#use-button');
  await expect.poll(() => api(page, 'menuOpen'), { message: 'tapping 料理する opens the menu' }).toBe(true);
  await expect(page.locator('#inv-tab-cook')).toHaveClass(/active/);
  await page.click('#inv-add-beast_meat');
  await page.click('#inv-add-ember_pepper');
  await page.click('#inv-cook');
  // v1.0 QA4: the できた row says it (a toast used to cover the pot and this row)
  await expect(page.locator('#inv-cooked')).toContainText('できた：火照りのスープ（新しいレシピ）');
  expect((await api(page, 'toasts')).join('|')).not.toContain('ができた');
  const inv = await api(page, 'inventory');
  expect(inv.items.ember_soup).toBe(1);
  expect(inv.recipes).toEqual(['ember_soup']);
  await page.screenshot({ path: testInfo.outputPath('cook.png') });
  expect(errors).toEqual([]);
});

test('the forge upgrades a weapon with money and materials', async ({ page }) => {
  const errors = await open(page);
  await api(page, 'addMoney', 100);
  await api(page, 'give', 'beast_fang', 1);
  await api(page, 'teleport', 53, 50); // south of the anvil by the hill stone
  await expect(page.locator('#use-button')).toHaveText('鍛冶');
  await page.click('#use-button');
  await page.click('#inv-upgrade-0');
  const inv = await api(page, 'inventory');
  expect(inv.weapons[0].lvl).toBe(1);
  expect(inv.money).toBe(70);
  expect(inv.items.beast_fang).toBeUndefined();
  expect(errors).toEqual([]);
});

test('the bag is saved and comes back with つづきから', async ({ page }) => {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await page.click('#title-new');
  await api(page, 'skipOpening'); // v1.0: the opening (C9) is not what this test is about
  await api(page, 'give', 'hunter_bow');
  await api(page, 'give', 'red_berry', 3);
  await api(page, 'addMoney', 42);
  expect(await api(page, 'saveNow')).toBe(true);
  await page.reload();
  await expect(page.locator('#title-continue')).toBeEnabled({ timeout: 20_000 });
  await page.click('#title-continue');
  const inv = await api(page, 'inventory');
  expect(inv.money).toBe(42);
  expect(inv.items.red_berry).toBe(3);
  expect(inv.bows.map((b) => b.id)).toEqual(['wood_bow', 'hunter_bow']);
  expect(errors).toEqual([]);
});
