import { test, expect } from '@playwright/test';

// P4: environment simulation on the first island (fire, dousing, electricity, far-away freezing).

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);

async function open(page, query = '') {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto(`/?map=island${query}`);
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await api(page, 'clearEnemies');
  return errors;
}

const ARROW = { up: 'ArrowUp', down: 'ArrowDown', left: 'ArrowLeft', right: 'ArrowRight' };

/** Face a direction at a tile: a short tap of the arrow key, then back onto the tile. */
async function face(page, dir, tx, ty) {
  await api(page, 'teleport', tx, ty);
  await page.keyboard.down(ARROW[dir]);
  await page.waitForTimeout(50);
  await page.keyboard.up(ARROW[dir]);
  await api(page, 'teleport', tx, ty);
  await api(page, 'face', dir);
}

test('an arrow shot through the brazier burns the brambles in front of the hidden forest', async ({ page }, testInfo) => {
  const errors = await open(page);
  // Brazier at (14,49), brambles at (14,46): stand south of the brazier and shoot north.
  await face(page, 'up', 14, 51);
  expect((await api(page, 'envTile', 14, 46)).material).toBe('bramble');
  // Draw for exactly 0.5 s of game time (the full draw is 0.4 s), then release.
  await api(page, 'pause');
  await page.keyboard.down('KeyU');
  await api(page, 'step', 30);
  await page.keyboard.up('KeyU');
  await api(page, 'step', 30);
  await api(page, 'resume');
  await expect.poll(() => api(page, 'envEvents'), { timeout: 5_000 }).toContain('fireArrow');
  await expect.poll(async () => (await api(page, 'envTile', 14, 46)).solid, { timeout: 15_000 }).toBe(false);
  await page.screenshot({ path: testInfo.outputPath('forest-fire.png') });
  expect(errors).toEqual([]);
});

test('the camp crystal shocks an enemy standing on the metal floor', async ({ page }) => {
  const errors = await open(page);
  await api(page, 'spawnEnemy', 'beast', 75, 43);
  await face(page, 'right', 70, 41); // the crystal is at (71,41)
  await api(page, 'pause');
  const before = (await api(page, 'enemies'))[0].hp;
  await page.keyboard.down('KeyJ');
  await api(page, 'step', 2);
  await page.keyboard.up('KeyJ');
  await api(page, 'step', 20);
  expect(await api(page, 'envEvents')).toContain('discharge');
  expect((await api(page, 'enemies'))[0].hp).toBeLessThan(before);
  await api(page, 'resume');
  expect(errors).toEqual([]);
});

test('the vault opens when the islet crystal powers the receiver, and stays open after a reload', async ({ page }) => {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await page.click('#title-new');
  await api(page, 'clearEnemies');
  expect((await api(page, 'envTile', 75, 58)).solid).toBe(true); // a rune door
  await face(page, 'left', 85, 62); // the crystal is at (84,62)
  await expect
    .poll(
      async () => {
        await page.keyboard.press('KeyJ');
        return (await api(page, 'progress')).gates;
      },
      { timeout: 5_000 },
    )
    .toEqual(['vault']);
  expect((await api(page, 'envTile', 75, 58)).solid).toBe(false);
  await expect.poll(async () => (await api(page, 'toasts')).join('|')).toContain('扉が開いた');
  expect(await api(page, 'saveNow')).toBe(true);
  await page.reload();
  await expect(page.locator('#title-continue')).toBeEnabled({ timeout: 20_000 });
  await page.click('#title-continue');
  expect((await api(page, 'envTile', 75, 58)).solid).toBe(false);
  expect(errors).toEqual([]);
});

test('a big fire stays within the per-tick cell limit', async ({ page }, testInfo) => {
  const errors = await open(page, '&debug=1');
  // Grass east of the spawn hill: set a 30 x 20 block alight (600 tiles) around the player.
  await api(page, 'teleport', 30, 40);
  const lit = await page.evaluate(() => {
    let n = 0;
    for (let ty = 30; ty < 50; ty++) for (let tx = 22; tx < 52; tx++) if (window.__debugApi.envIgnite(tx, ty)) n++;
    return n;
  });
  expect(lit).toBeGreaterThan(400);
  await page.waitForTimeout(3000);
  const env = await api(page, 'env');
  expect(env.maxTickCells).toBeLessThanOrEqual(512);
  expect(env.burning).toBeGreaterThan(0);
  const s = await api(page, 'summary');
  await page.screenshot({ path: testInfo.outputPath('big-fire.png') });
  await testInfo.attach('big-fire-stats', { body: JSON.stringify({ env, fps: s.fps, p95Ms: s.p95Ms }, null, 2), contentType: 'application/json' });
  expect(errors).toEqual([]);
});

test('a fire far away freezes, and catches up when the player comes back', async ({ page }) => {
  const errors = await open(page);
  // Game time is advanced step by step (paused), so the time away is exact on any machine.
  await api(page, 'pause');
  await api(page, 'teleport', 30, 60); // south-west meadow
  expect(await api(page, 'envIgnite', 32, 58)).toBe(true);
  await api(page, 'teleport', 80, 30); // far east: the west of the island is frozen
  await api(page, 'step', 12);
  const frozen = await api(page, 'env');
  await api(page, 'step', 240); // 4 s away
  const still = await api(page, 'env');
  expect(still.burning).toBe(frozen.burning); // nothing computed over there
  expect(still.ash).toBe(frozen.ash);
  await api(page, 'teleport', 30, 60); // back
  await api(page, 'step', 30);
  // Fast-forwarded by the time away (4 coarse 1 s steps), then back to normal.
  const after = await api(page, 'env');
  expect(after.catchUpSteps).toBeGreaterThanOrEqual(4);
  expect(after.pendingRegions).toBe(0);
  expect(after.ash + after.burning).toBeGreaterThan(1);
  await api(page, 'resume');
  expect(errors).toEqual([]);
});
