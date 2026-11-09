import { test, expect } from '@playwright/test';

// v1.0: the objects' release art (src/art-release/objects; src/view/assets/objectsArt.js) is drawn in
// normal play: buildings, chests, switches and seats, items on the ground, effects, and the item icons
// of the menus — at 2 art pixels per game pixel, with no console warnings. ?objects=placeholder
// shows the placeholders (comparison).

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);

async function open(page, query = '') {
  const errors = [];
  const warnings = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('console', (m) => {
    if (m.type() === 'warning' || m.type() === 'error') warnings.push(m.text());
  });
  await page.goto(`/?map=world&time=10&season=summer${query}`);
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await api(page, 'clearEnemies');
  return { errors, warnings };
}

test('normal play draws the objects from their release art (2 px per game px), with no warnings', async ({ page }, testInfo) => {
  const { errors, warnings } = await open(page);
  // the base bundle's objects, effects and icons
  for (const [key, w, h] of [['obj.chest.closed', 16, 14], ['sw.plate.on', 14, 10], ['fx.slash', 16, 20], ['icon.sword', 10, 10], ['ui.marker', 7, 7]]) {
    expect(await api(page, 'objectTexture', key), key).toEqual({ key, w, h, res: 2 });
  }
  // the beach ring (base bundle): its release art, 48×52 (24×26 game px), closed and open
  for (const key of ['obj.star_ring.off', 'obj.star_ring.on']) expect(await api(page, 'objectTexture', key)).toEqual({ key, w: 24, h: 26, res: 2 });
  await api(page, 'teleport', 43, 69);
  await expect.poll(async () => (await api(page, 'objectSprites')).find((s) => s.kind === 'star_ring')?.key).toBe('obj.star_ring.off');
  await api(page, 'setFlag', 'source_open');
  await expect.poll(async () => (await api(page, 'objectSprites')).find((s) => s.kind === 'star_ring')?.key).toBe('obj.star_ring.on');
  await api(page, 'setFlag', 'source_open', false);
  // the village (the plains bundle): the houses are the approved 96×112 (48×56 game px)
  await api(page, 'teleport', 24, 89);
  await expect.poll(async () => (await api(page, 'objectSprites')).filter((s) => s.kind === 'house').length, { timeout: 10_000 }).toBeGreaterThan(0);
  for (const s of (await api(page, 'objectSprites')).filter((x) => x.kind === 'house')) expect(s).toMatchObject({ key: 'obj.house', w: 48, h: 56, res: 2 });
  await page.screenshot({ path: testInfo.outputPath('village.png') });
  // behind a house (north of it) the player sees through it, like behind a tree; in front it is solid
  const house = () => api(page, 'objectSprites').then((l) => l.filter((s) => s.kind === 'house').map((s) => s.alpha));
  await api(page, 'teleport', 24, 83);
  await expect.poll(async () => (await house()).some((a) => a < 1)).toBe(true);
  await page.screenshot({ path: testInfo.outputPath('behind-house.png') });
  await api(page, 'teleport', 24, 87);
  await expect.poll(async () => (await house()).every((a) => a === 1)).toBe(true);
  // a trial: plates, sconce, resonance stone, chest — all release art, off then on
  await api(page, 'teleport', 106, 61);
  await page.waitForTimeout(300);
  const trial = (await api(page, 'objectSprites')).filter((s) => s.visible && ['plate', 'sconce', 'stone', 'chest', 'door'].includes(s.kind));
  expect(trial.length).toBeGreaterThan(3);
  for (const s of trial) expect(s.res, s.kind).toBe(2);
  await api(page, 'pause');
  await api(page, 'forceObjectStates', true);
  await expect.poll(async () => (await api(page, 'objectSprites')).filter((s) => s.kind === 'chest' && s.key === 'obj.chest.open').length).toBeGreaterThan(0);
  const keys = (await api(page, 'objectSprites')).map((s) => s.key);
  for (const k of ['sw.plate.on', 'obj.sconce.on', 'obj.stone.on']) expect(keys, k).toContain(k);
  await api(page, 'resume');
  // items on the ground use the icons
  await api(page, 'teleport', 40, 58);
  await api(page, 'dropPickup', 'mushroom', 41, 59);
  await expect.poll(async () => (await api(page, 'objectSprites')).find((s) => s.kind === 'pickup')?.key).toBe('icon.mushroom');
  expect((await api(page, 'objectSprites')).find((s) => s.kind === 'pickup')).toMatchObject({ w: 10, h: 10, res: 2 });
  // the menus show the same icons, from the packed sheet
  await api(page, 'give', 'red_berry', 2);
  await page.keyboard.press('e');
  await page.click('#inv-tab-material');
  await expect(page.locator('#inv-menu .item-icon[data-icon="icon.berry"]')).toBeVisible();
  const bg = await page.locator('#inv-menu .item-icon[data-icon="icon.berry"]').evaluate((el) => getComputedStyle(el).backgroundImage);
  expect(bg).toMatch(/release-objects|art-release\/objects/);
  await page.screenshot({ path: testInfo.outputPath('menu.png') });
  expect(warnings).toEqual([]);
  expect(errors).toEqual([]);
});

test('?objects=placeholder keeps the placeholder objects and icons', async ({ page }) => {
  const { errors } = await open(page, '&objects=placeholder');
  expect((await api(page, 'objectTexture', 'obj.chest.closed')).res).toBe(1);
  await api(page, 'give', 'red_berry', 1);
  await page.keyboard.press('e');
  await page.click('#inv-tab-material');
  const bg = await page.locator('#inv-menu .item-icon[data-icon="icon.berry"]').evaluate((el) => getComputedStyle(el).backgroundImage);
  expect(bg).toMatch(/^url\("data:image\/png/);
  expect(errors).toEqual([]);
});
