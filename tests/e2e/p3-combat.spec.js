import { test, expect } from '@playwright/test';

// Combat on the height verification map. The map's own enemies are cleared; each test places
// what it needs next to the player with the spawnEnemy test hook.

async function open(page) {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await page.evaluate(() => window.__debugApi.clearEnemies());
  return errors;
}

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);
const player = (page) => api(page, 'player');
const enemies = (page) => api(page, 'enemies');

/** Tap a touch button (pointer down, short hold, up). */
async function tap(page, id, holdMs = 60) {
  const b = page.locator(`#${id}`);
  await b.dispatchEvent('pointerdown', { pointerId: 11 });
  await page.waitForTimeout(holdMs);
  await b.dispatchEvent('pointerup', { pointerId: 11 });
}

test('the sword defeats a beast', async ({ page }, testInfo) => {
  const errors = await open(page);
  await api(page, 'teleport', 8, 26);
  await api(page, 'spawnEnemy', 'beast', 10, 26);
  // Face right, then keep swinging (J) until the beast is gone.
  await page.keyboard.down('ArrowRight');
  await page.waitForTimeout(60);
  await page.keyboard.up('ArrowRight');
  let shot = false;
  await expect
    .poll(
      async () => {
        await page.keyboard.press('KeyJ');
        if (!shot) {
          shot = true;
          await page.screenshot({ path: testInfo.outputPath('sword.png') });
        }
        return (await enemies(page)).length;
      },
      { timeout: 15_000, intervals: [150] },
    )
    .toBe(0);
  expect(errors).toEqual([]);
});

test('touch buttons: attack swings, dodge hops, guard raises the shield', async ({ page }) => {
  await open(page);
  const events = () => api(page, 'events');
  // Short actions are checked through the game's event log, so a slow machine cannot miss them.
  await tap(page, 'attack-button');
  await expect.poll(async () => (await events()).includes('swing'), { message: 'swing event', timeout: 3000, intervals: [50] }).toBe(true);

  await page.waitForTimeout(800);
  await tap(page, 'dodge-button');
  await expect.poll(async () => (await events()).includes('dodge'), { message: 'dodge event', timeout: 3000, intervals: [50] }).toBe(true);

  await page.waitForTimeout(600);
  const g = page.locator('#guard-button');
  await g.dispatchEvent('pointerdown', { pointerId: 12 });
  await expect.poll(async () => (await player(page)).guarding, { message: 'guard up', timeout: 3000, intervals: [20] }).toBe(true);
  await g.dispatchEvent('pointerup', { pointerId: 12 });
  await expect.poll(async () => (await player(page)).guarding, { message: 'guard down', timeout: 3000, intervals: [20] }).toBe(false);
});

test('the bow shoots an arrow after a full draw', async ({ page }, testInfo) => {
  await open(page);
  await page.keyboard.down('ArrowRight');
  await page.waitForTimeout(60);
  await page.keyboard.up('ArrowRight');
  await page.keyboard.down('KeyU');
  await page.waitForTimeout(600); // full draw is 400ms
  await page.screenshot({ path: testInfo.outputPath('aim.png') });
  await page.keyboard.up('KeyU');
  await expect
    .poll(async () => (await api(page, 'projectiles')).filter((p) => p.kind === 'arrow').length, { timeout: 2000, intervals: [20] })
    .toBeGreaterThan(0);
});

test('at zero health the player collapses and gets up again at the spawn point', async ({ page }, testInfo) => {
  await open(page);
  await api(page, 'teleport', 27, 5); // tower top east edge (64px): the fall costs half a heart
  await api(page, 'setHp', 2);
  await page.keyboard.down('ArrowRight');
  await expect.poll(async () => (await player(page)).dead, { timeout: 5000, intervals: [30] }).toBe(true);
  await page.keyboard.up('ArrowRight');
  await expect(page.locator('#death-overlay')).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath('death.png') });
  await expect.poll(async () => (await player(page)).dead, { timeout: 6000, intervals: [100] }).toBe(false);
  await expect(page.locator('#death-overlay')).toBeHidden();
  const p = await player(page);
  expect(p.hp).toBe(12);
  expect(p.x).toBe(5 * 16 + 8); // spawn point
});
