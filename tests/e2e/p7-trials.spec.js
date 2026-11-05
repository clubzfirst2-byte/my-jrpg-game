import { test, expect } from '@playwright/test';

// P7: the 星環 abilities and the three trials (each also solved another way in tests/unit/trials.test.js).

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);
const ARROW = { up: 'ArrowUp', down: 'ArrowDown', left: 'ArrowLeft', right: 'ArrowRight' };

async function open(page) {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/?map=island');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await api(page, 'clearEnemies');
  return errors;
}

/** Stand on a tile facing a direction (a short key tap turns the player, then back onto the tile). */
async function standAt(page, tx, ty, dir) {
  await api(page, 'teleport', tx, ty);
  await page.keyboard.down(ARROW[dir]);
  await page.waitForTimeout(40);
  await page.keyboard.up(ARROW[dir]);
  await api(page, 'teleport', tx, ty);
  await api(page, 'face', dir);
}

/** Uses the selected ability with the touch button. */
async function useAbility(page) {
  const b = page.locator('#ability-button');
  await b.dispatchEvent('pointerdown', { pointerId: 21 });
  await page.waitForTimeout(80);
  await b.dispatchEvent('pointerup', { pointerId: 21 });
}

test('the glowing pillar leads into the light trial; 灯火 lights the sensor and opens the door', async ({ page }, testInfo) => {
  const errors = await open(page);
  await expect(page.locator('#ability-button')).toBeHidden(); // nothing learned yet
  // Walk north into the pillar's doorway.
  await api(page, 'teleport', 17, 35);
  await page.keyboard.down('ArrowUp');
  await expect.poll(() => api(page, 'area'), { timeout: 5_000 }).toBe('trial_light');
  await page.keyboard.up('ArrowUp');
  await expect.poll(async () => (await api(page, 'abilities')).owned).toEqual(['light']);
  await expect(page.locator('#ability-button')).toHaveText('灯火');
  await expect.poll(async () => (await api(page, 'toasts')).join('|')).toContain('灯火');
  await standAt(page, 105, 27, 'up');
  await useAbility(page);
  await expect.poll(() => api(page, 'gates'), { timeout: 5_000 }).toContain('trial_light');
  await page.screenshot({ path: testInfo.outputPath('light-trial.png') });
  expect(errors).toEqual([]);
});

test('weight trial: 念動 slides the crate onto a plate; standing on the other opens the door', async ({ page }) => {
  const errors = await open(page);
  await api(page, 'teleport', 104, 49);
  await expect.poll(async () => (await api(page, 'abilities')).owned).toContain('telekinesis');
  await standAt(page, 105, 47, 'left');
  await page.keyboard.press('KeyQ');
  await expect.poll(async () => (await api(page, 'switches'))['plate-west']).toBe(true);
  await api(page, 'teleport', 109, 45);
  await expect.poll(() => api(page, 'gates'), { timeout: 5_000 }).toContain('trial_weight');
  expect(errors).toEqual([]);
});

test('chasm trial: a vine bridge (蔓結び) across the pit to the plate', async ({ page }, testInfo) => {
  const errors = await open(page);
  await api(page, 'teleport', 104, 67);
  await expect.poll(async () => (await api(page, 'abilities')).owned).toContain('vine');
  await standAt(page, 103, 64, 'up');
  await useAbility(page);
  await expect.poll(async () => (await api(page, 'envTile', 103, 63)).material).toBe('vine');
  // The cooldown runs on game time (a slow machine may need longer than it looks).
  await expect.poll(async () => (await api(page, 'abilities')).ready).toBe(true);
  await standAt(page, 103, 63, 'up');
  await useAbility(page);
  await expect.poll(async () => (await api(page, 'envTile', 103, 62)).material).toBe('vine');
  await standAt(page, 103, 62, 'up');
  await page.keyboard.down('ArrowUp');
  await expect.poll(() => api(page, 'gates'), { timeout: 5_000 }).toContain('trial_chasm');
  await page.keyboard.up('ArrowUp');
  expect(await api(page, 'events')).not.toContain('fell');
  await page.screenshot({ path: testInfo.outputPath('vine-bridge.png') });
  expect(errors).toEqual([]);
});

test('switching abilities, and a star shard adds a heart', async ({ page }) => {
  const errors = await open(page);
  await api(page, 'grantAbility', 'light');
  await api(page, 'grantAbility', 'resonance');
  await expect(page.locator('#ability-next')).toBeVisible();
  await page.click('#ability-next');
  await expect(page.locator('#ability-button')).toHaveText('共鳴');
  await api(page, 'give', 'star_shard', 1);
  await page.click('#bag-button');
  await page.click('#inv-tab-power');
  await page.click('#inv-shard-heart');
  expect((await api(page, 'progress')).maxHp).toBe(16);
  await page.click('#inv-close');
  expect(errors).toEqual([]);
});
