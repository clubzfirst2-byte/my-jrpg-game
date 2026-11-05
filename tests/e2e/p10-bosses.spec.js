import { test, expect } from '@playwright/test';

// P10.4: the four cores of the murk — a boss wakes when you step into its arena, shows its health,
// turns fiercer below half, and once beaten is purified for good.

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);

async function open(page, query = '') {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto(`/?map=world&time=10&season=summer${query}`);
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  return errors;
}

test('the forest core: wakes in its arena, shows its health, rages below half, and is purified', async ({ page }, testInfo) => {
  const errors = await open(page);
  const boss = (await api(page, 'bosses')).find((b) => b.id === 'core_forest');
  expect(boss.name).toBe('朽ち根のヌシ');
  await expect(page.locator('#boss-bar')).toBeHidden();
  await api(page, 'setHp', 400);
  await api(page, 'teleport', Math.floor(boss.x / 16), Math.floor(boss.y / 16) + 4);
  await expect(page.locator('#boss-bar')).toBeVisible();
  await expect(page.locator('#boss-bar .boss-name')).toHaveText('朽ち根のヌシ');
  await expect.poll(async () => (await api(page, 'toasts')).some((t) => t.includes('目を覚ました'))).toBe(true);
  // It attacks (a wind-up first).
  await expect.poll(async () => (await api(page, 'bosses')).find((b) => b.id === 'core_forest').state, { timeout: 5000 }).toBe('windup');
  await page.screenshot({ path: testInfo.outputPath('forest-core.png') });
  // (Its charges can knock the player out of the arena, where it calms down: step back in.)
  const backIn = () => api(page, 'teleport', Math.floor(boss.arena.tx + boss.arena.tw / 2), boss.arena.ty + boss.arena.th - 2);
  await api(page, 'hurtBoss', 'core_forest', 31);
  await expect.poll(async () => {
    await backIn();
    return page.locator('#boss-bar').getAttribute('class');
  }).toMatch(/phase2/);
  await api(page, 'hurtBoss', 'core_forest', 99);
  await expect.poll(async () => (await api(page, 'progress')).bosses).toEqual(['core_forest']);
  await expect.poll(async () => (await api(page, 'toasts')).some((t) => t.includes('浄化した') && t.includes('1/4'))).toBe(true);
  await expect(page.locator('#boss-bar')).toBeHidden();
  expect((await api(page, 'inventory')).items.star_shard).toBeGreaterThanOrEqual(1);
  expect(errors).toEqual([]);
});

test('touring past all four arenas draws each core with its region art, without errors', async ({ page }) => {
  const errors = await open(page);
  for (const id of ['core_forest', 'core_mountains', 'core_desert', 'core_lake']) {
    const boss = (await api(page, 'bosses')).find((b) => b.id === id);
    await api(page, 'teleport', Math.floor(boss.x / 16), Math.floor(boss.y / 16) + 12);
    await page.waitForTimeout(400);
  }
  await api(page, 'teleport', 48, 60);
  await page.waitForTimeout(600);
  expect(errors).toEqual([]);
});
