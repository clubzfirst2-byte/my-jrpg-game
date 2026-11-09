import { test, expect } from '@playwright/test';

// v1.0 enemies (docs/enemy/ENEMY_BOSS_DESIGN.md 2.3, 2.4): 澱だまり (slime) and 遺跡の番兵 (sentinel),
// and the wind-up warning as a 50% red overlay (ART_STYLE_GUIDE 5.4 B) instead of a red tint.
// On the height verification map, with each test placing what it needs next to the player.

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);

async function open(page, query = '') {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto(`/?map=height${query}`);
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await api(page, 'clearEnemies');
  await api(page, 'setHp', 400);
  await api(page, 'teleport', 8, 26);
  return errors;
}

const RED = 0xff3a3a;

test('the sentinel winds up under a 50% red overlay (the sprite itself is not tinted) and slams', async ({ page }, testInfo) => {
  const errors = await open(page);
  // Freeze the drawing clock where the pulse is on for the whole wind-up: sin(0.05 × (12..36)) > 0.
  await api(page, 'setVisualTime', 0.05);
  await api(page, 'spawnEnemy', 'sentinel', 9, 26);
  await expect
    .poll(async () => (await api(page, 'enemies')).find((e) => e.kind === 'sentinel')?.state, { timeout: 8000, intervals: [20] })
    .toBe('windup');
  const view = (await api(page, 'enemyView'))[0];
  expect(view.flash).toBeCloseTo(0.5);
  expect(view.flashColor).toBe(RED);
  expect(view.tint).toBe(0xffffff);
  await page.screenshot({ path: testInfo.outputPath('sentinel-windup.png') });
  // The slam lands (the player stands in reach) and the overlay goes away after the wind-up.
  await expect.poll(async () => (await api(page, 'events')).includes('enemySlam'), { timeout: 4000, intervals: [20] }).toBe(true);
  await expect.poll(async () => (await api(page, 'enemyView'))[0].flash, { timeout: 4000, intervals: [20] }).toBe(0);
  expect(errors).toEqual([]);
});

test('the slime and the sentinel are drawn at their design size (16×14 and 20×28 game px)', async ({ page }) => {
  const errors = await open(page);
  await api(page, 'spawnEnemy', 'slime', 12, 26);
  await api(page, 'spawnEnemy', 'sentinel', 14, 26);
  await expect.poll(async () => (await api(page, 'enemyView')).length, { timeout: 4000 }).toBe(2);
  const enemies = await api(page, 'enemies');
  const view = await api(page, 'enemyView');
  for (const e of enemies) {
    const v = view.find((x) => x.id === e.id);
    // Release art (enemy.<kind>.<action>.<n>, 2 art pixels per game pixel) or the placeholder (.0/.1): the same size.
    expect(v.key).toMatch(new RegExp(`^enemy\\.${e.kind}\\.(\\d|[a-z_0-9]+\\.\\d)$`));
    expect([v.w, v.h]).toEqual(e.kind === 'slime' ? [16, 14] : [20, 28]);
  }
  expect(errors).toEqual([]);
});

test('the sword defeats a slime; it leaves a murk crystal sometimes, and never an error', async ({ page }) => {
  const errors = await open(page);
  await api(page, 'spawnEnemy', 'slime', 10, 26);
  await page.keyboard.down('ArrowRight');
  await page.waitForTimeout(60);
  await page.keyboard.up('ArrowRight');
  await expect
    .poll(
      async () => {
        await page.keyboard.press('KeyJ');
        return (await api(page, 'enemies')).length;
      },
      { timeout: 15_000, intervals: [150] },
    )
    .toBe(0);
  expect(errors).toEqual([]);
});

test('the placeholder enemies still flash with the overlay (?hd=0, no release art)', async ({ page }) => {
  const errors = await open(page, '&hd=0');
  await api(page, 'setVisualTime', 0.05);
  await api(page, 'spawnEnemy', 'beast', 9, 26);
  await expect
    .poll(async () => (await api(page, 'enemyView'))[0]?.flash ?? 0, { timeout: 8000, intervals: [20] })
    .toBeCloseTo(0.5);
  const v = (await api(page, 'enemyView'))[0];
  expect(v.key).toMatch(/^enemy\.beast\.[01]$/);
  expect(v.flashColor).toBe(RED);
  expect(errors).toEqual([]);
});
