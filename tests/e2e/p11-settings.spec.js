import { test, expect } from '@playwright/test';

// P11.3: the settings screen — difficulty, text size, button size, which hand holds the buttons,
// the sound volumes; every choice applies at once and is remembered.

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);
const CLUSTER = ['attack-button', 'jump-button', 'dodge-button', 'bow-button', 'guard-button', 'dash-button'];

async function open(page) {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/?map=world&time=10&season=summer');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await api(page, 'clearEnemies');
  return errors;
}
async function settings(page) {
  await page.click('#pause-button');
  await page.click('#open-settings');
  await expect(page.locator('#settings-menu')).toBeVisible();
}
async function done(page) {
  await page.click('#settings-close');
  await page.click('#resume-button');
  await expect(page.locator('#pause-overlay')).toBeHidden();
}
/** The cluster's buttons: inside the screen and not overlapping each other. */
async function clusterIsTidy(page) {
  const boxes = await Promise.all(CLUSTER.map((id) => page.locator(`#${id}`).boundingBox()));
  const vp = page.viewportSize();
  for (const [i, a] of boxes.entries()) {
    expect(a.x >= 0 && a.y >= 0 && a.x + a.width <= vp.width && a.y + a.height <= vp.height, CLUSTER[i]).toBe(true);
    for (const [j, b] of boxes.entries()) {
      if (j <= i) continue;
      const ra = a.width / 2;
      const rb = b.width / 2;
      const d = Math.hypot(a.x + ra - (b.x + rb), a.y + ra - (b.y + rb));
      expect(d, `${CLUSTER[i]} / ${CLUSTER[j]}`).toBeGreaterThanOrEqual(ra + rb - 1);
    }
  }
  return boxes;
}

test('choices apply at once and are remembered', async ({ page }, testInfo) => {
  const errors = await open(page);
  await settings(page);
  await page.click('#set-difficulty-hard');
  await expect(page.locator('#settings-menu .settings-note')).toContainText('1.5');
  await page.click('#set-textSize-large');
  await page.click('#set-buttonSize-small');
  await page.click('#set-bgmVolume-0');
  await expect(page.locator('#set-difficulty-hard')).toHaveClass(/selected/);
  await page.screenshot({ path: testInfo.outputPath('settings.png') });
  await done(page);
  await expect(page.locator('#ui')).toHaveClass(/text-large/);
  await expect(page.locator('#ui')).toHaveClass(/btn-small/);
  expect((await api(page, 'audio')).volumes.bgm).toBe(0);
  await page.reload();
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  expect(await api(page, 'settings')).toMatchObject({ difficulty: 'hard', textSize: 'large', buttonSize: 'small', bgmVolume: 0 });
  await expect(page.locator('#ui')).toHaveClass(/text-large/);
  expect(errors).toEqual([]);
});

test('every button size, either hand: the buttons stay on screen and never overlap', async ({ page }) => {
  const errors = await open(page);
  const vp = page.viewportSize();
  for (const hand of ['right', 'left']) {
    for (const size of ['small', 'medium', 'large']) {
      await settings(page);
      await page.click(`#set-hand-${hand}`);
      await page.click(`#set-buttonSize-${size}`);
      await done(page);
      const boxes = await clusterIsTidy(page);
      const attack = boxes[0];
      if (hand === 'right') expect(attack.x).toBeGreaterThan(vp.width / 2);
      else expect(attack.x + attack.width).toBeLessThan(vp.width / 2);
    }
  }
  expect(errors).toEqual([]);
});

test('left hand on the buttons: the stick works on the right half instead', async ({ page }) => {
  const errors = await open(page);
  await settings(page);
  await page.click('#set-hand-left');
  await done(page);
  const vp = page.viewportSize();
  const drag = async (x) => {
    const p0 = (await api(page, 'player')).x;
    await page.mouse.move(x, vp.height * 0.4);
    await page.mouse.down();
    await page.mouse.move(x + 40, vp.height * 0.4, { steps: 4 });
    await page.waitForTimeout(500);
    await page.mouse.up();
    return (await api(page, 'player')).x - p0;
  };
  // (The left half first: after a real stick move the player would still be slowing down.)
  expect(await drag(vp.width * 0.3)).toBeLessThan(1); // left half: not the stick any more
  expect(await drag(vp.width * 0.7)).toBeGreaterThan(8); // right half: the stick
  expect(errors).toEqual([]);
});
