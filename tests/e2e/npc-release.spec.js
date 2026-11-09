import { test, expect } from '@playwright/test';
import { waitTicks } from './ticks.js';

// NPC batch 1 (docs/npc/NPC_RELEASE_PLAN.md): the elder, the merchant and the guard drawn from their
// release art (src/art-release/npc/) beside the release hero; every other villager keeps the
// placeholder; walking, turning to talk, the shop and the draw order work as before.

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);

async function open(page, query = '&hero=release') {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto(`/?map=world&time=10&season=summer${query}`);
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await api(page, 'clearEnemies');
  return errors;
}

const sprite = async (page, id) => (await api(page, 'npcSprites')).find((s) => s.id === id);
const npcState = async (page, id) => (await api(page, 'npcState')).find((n) => n.id === id);

/** Holds a key until `done()` is true (or gives up). */
async function holdUntil(page, key, done, ms = 12_000) {
  await page.keyboard.down(key);
  try {
    await expect.poll(done, { timeout: ms, intervals: [50] }).toBe(true);
  } finally {
    await page.keyboard.up(key);
  }
}

test('all five villagers (batch 1: elder, merchant, guard; batch 2: cook, child) use their release art (16×28) beside the release hero', async ({ page }, testInfo) => {
  const warnings = [];
  page.on('console', (m) => {
    if (m.text().startsWith('art:')) warnings.push(m.text());
  });
  const errors = await open(page);
  expect(await api(page, 'art')).toMatchObject({ density: 2, overrides: 248 + 280, hero: { w: 16, h: 28 } });
  for (const id of ['elder', 'guard', 'merchant', 'cook', 'child']) {
    await api(page, 'standBy', id);
    await waitTicks(page, 10);
    const s = await sprite(page, id);
    expect(s.key, id).toMatch(new RegExp(`^npc\\.${id}\\.(idle|walk)\\.(down|up|right|left)\\.\\d$`));
    expect([s.w, s.h], id).toEqual([16, 28]);
    await page.screenshot({ path: testInfo.outputPath(`${id}.png`) });
  }
  expect(warnings).toEqual([]);
  expect(errors).toEqual([]);
});

test('standing, a villager breathes (the idle frames change); walking, the walk frames follow his direction', async ({ page }) => {
  const errors = await open(page);
  // Next to the elder he stops and stands: his idle loop plays.
  await api(page, 'standBy', 'elder');
  const seen = new Set();
  for (let k = 0; k < 12; k++) {
    await waitTicks(page, 12);
    const s = await sprite(page, 'elder');
    expect(s.key).toMatch(/^npc\.elder\.idle\.\w+\.[0-3]$/);
    seen.add(s.key);
  }
  expect(seen.size).toBeGreaterThan(1);
  // A few tiles away the guard strolls: walk frames, in the direction he is going.
  const g = (await api(page, 'npcs')).find((n) => n.id === 'guard');
  await api(page, 'teleport', g.tx - 6, g.ty + 4);
  await expect.poll(async () => (await npcState(page, 'guard')).moving, { timeout: 20_000, intervals: [50] }).toBe(true);
  const st = await npcState(page, 'guard');
  const s = await sprite(page, 'guard');
  expect(s.key).toMatch(/^npc\.guard\.walk\.(down|up|right|left)\.[0-5]$/);
  expect(s.key.split('.')[3]).toBe(st.facing);
  // When he stops he goes straight back to standing.
  await expect.poll(async () => (await npcState(page, 'guard')).moving, { timeout: 20_000, intervals: [50] }).toBe(false);
  await expect.poll(async () => (await sprite(page, 'guard')).key, { timeout: 2000 }).toMatch(/^npc\.guard\.idle\./);
  expect(errors).toEqual([]);
});

test('spoken to, a villager turns to the hero and is drawn facing him; the draw order follows the feet', async ({ page }, testInfo) => {
  const errors = await open(page);
  await api(page, 'standBy', 'guard'); // the hero just south of him
  await api(page, 'talkTo', 'guard');
  await expect.poll(async () => (await api(page, 'dialogue'))?.speaker).toBe('見張り');
  // (the world waits while they talk: no logic ticks, but he is drawn)
  await expect.poll(async () => (await npcState(page, 'guard')).facing).toBe('down');
  await expect.poll(async () => (await sprite(page, 'guard')).key).toMatch(/^npc\.guard\.idle\.down\./);
  await page.screenshot({ path: testInfo.outputPath('talk.png') });
  for (let k = 0; k < 8 && (await api(page, 'dialogue')); k++) await page.click('#dialogue');
  // Each villager is sorted by the y of its feet, like the hero (in front when lower on screen).
  for (const s of await api(page, 'npcSprites')) {
    const n = await npcState(page, s.id);
    expect(Math.abs(s.zIndex - n.y), s.id).toBeLessThan(1.01);
  }
  expect(errors).toEqual([]);
});

test('the shop works as before with the release merchant behind the counter', async ({ page }, testInfo) => {
  const errors = await open(page);
  await api(page, 'teleport', 16, 87);
  await waitTicks(page, 10);
  await holdUntil(page, 'ArrowUp', async () => (await api(page, 'area')) === 'shop');
  await holdUntil(page, 'ArrowUp', async () => (await api(page, 'nearby')) === 'talk');
  await waitTicks(page, 10);
  expect((await sprite(page, 'merchant')).key).toMatch(/^npc\.merchant\.idle\./);
  await page.screenshot({ path: testInfo.outputPath('shop.png') });
  await page.keyboard.press('j');
  await expect.poll(async () => (await api(page, 'dialogue'))?.speaker).toBe('雑貨屋');
  for (let k = 0; k < 6 && !(await api(page, 'dialogue'))?.choices; k++) await page.click('#dialogue');
  await page.click('#dialogue-choice-0');
  await expect(page.locator('#shop-menu')).toBeVisible();
  await page.click('#shop-close');
  await expect(page.locator('#shop-menu')).toBeHidden();
  expect(errors).toEqual([]);
});

test('?npc=placeholder keeps the placeholder villagers; normal play (no release hero yet on main) is unchanged', async ({ page }) => {
  await open(page, '&hero=release&npc=placeholder');
  expect((await api(page, 'art')).overrides).toBe(248);
  await api(page, 'standBy', 'elder');
  await waitTicks(page, 10);
  expect((await sprite(page, 'elder')).key).toMatch(/^npc\.1\.walk\./);
  const page2 = await page.context().newPage();
  await open(page2, '');
  expect(await api(page2, 'art')).toMatchObject({ density: 1, overrides: 0 });
  await api(page2, 'standBy', 'elder');
  await waitTicks(page2, 10);
  expect((await sprite(page2, 'elder')).key).toMatch(/^npc\.1\.walk\./);
  // the villagers' release art alone (without the hero's) can be asked for
  const page3 = await page.context().newPage();
  await open(page3, '&npc=release');
  expect(await api(page3, 'art')).toMatchObject({ density: 2, overrides: 280 });
});

test('iPhone landscape: the three villagers and the hero together on screen', async ({ page }, testInfo) => {
  const errors = await open(page);
  await api(page, 'standBy', 'elder');
  await waitTicks(page, 20);
  const vp = page.viewportSize();
  expect(vp.width).toBeGreaterThan(vp.height);
  const on = (await api(page, 'npcSprites')).filter((s) => s.key.startsWith('npc.elder') || s.key.startsWith('npc.guard'));
  expect(on.length).toBeGreaterThanOrEqual(1);
  await page.screenshot({ path: testInfo.outputPath('iphone.png') });
  expect(errors).toEqual([]);
});

test('batch 2: the woman and the smith (not in the village yet) stand, walk and turn like the others', async ({ page }, testInfo) => {
  const errors = await open(page);
  const e = (await api(page, 'npcs')).find((n) => n.id === 'elder');
  await api(page, 'addNpc', 'woman', e.tx + 3, e.ty + 2);
  await api(page, 'addNpc', 'smith', e.tx + 5, e.ty + 2);
  await api(page, 'teleport', e.tx + 4, e.ty + 4);
  await waitTicks(page, 10);
  for (const id of ['woman', 'smith']) {
    const s = await sprite(page, id);
    expect(s.key, id).toMatch(new RegExp(`^npc\\.${id}\\.(idle|walk)\\.`));
    expect([s.w, s.h], id).toEqual([16, 28]);
  }
  await page.screenshot({ path: testInfo.outputPath('batch2.png') });
  // a few tiles off they stroll: walk frames in the direction they go
  await api(page, 'teleport', e.tx + 4, e.ty + 9);
  await expect.poll(async () => (await npcState(page, 'smith')).moving, { timeout: 20_000, intervals: [50] }).toBe(true);
  const s = await sprite(page, 'smith');
  expect(s.key.split('.')[2]).toBe('walk');
  expect(s.key.split('.')[3]).toBe((await npcState(page, 'smith')).facing);
  expect(errors).toEqual([]);
});

test('?npc=revision shows batch 1 with the review\'s fixes (a separate set); without it, the approved frames', async ({ page }) => {
  await open(page, '&hero=release&npc=revision');
  expect((await api(page, 'art')).overrides).toBe(248 + 280);
  await api(page, 'standBy', 'guard');
  await waitTicks(page, 10);
  expect((await sprite(page, 'guard')).key).toMatch(/^npc\.guard\./);
  const page2 = await page.context().newPage();
  await open(page2, '&hero=release');
  // (the build inlines small images, so the files are compared by their contents)
  for (const key of ['npc.elder.idle.down.0', 'npc.merchant.idle.up.0', 'npc.guard.idle.down.0']) {
    expect(await api(page, 'artUrl', key), key).not.toBe(await api(page2, 'artUrl', key));
  }
  for (const key of ['npc.guard.idle.right.0', 'npc.cook.idle.down.0']) {
    expect(await api(page, 'artUrl', key), key).toBe(await api(page2, 'artUrl', key));
  }
});

test('?npc=revision-b2 shows the batch 2 fixes (woman, child, smith); the cook and batch 1 as submitted', async ({ page }) => {
  await open(page, '&hero=release&npc=revision-b2');
  expect((await api(page, 'art')).overrides).toBe(248 + 280);
  await api(page, 'standBy', 'child');
  await waitTicks(page, 10);
  expect((await sprite(page, 'child')).key).toMatch(/^npc\.child\./);
  const page2 = await page.context().newPage();
  await open(page2, '&hero=release');
  for (const key of ['npc.woman.idle.down.0', 'npc.child.idle.up.0', 'npc.smith.idle.down.0']) {
    expect(await api(page, 'artUrl', key), key).not.toBe(await api(page2, 'artUrl', key));
  }
  for (const key of ['npc.cook.idle.down.0', 'npc.elder.idle.down.0']) {
    expect(await api(page, 'artUrl', key), key).toBe(await api(page2, 'artUrl', key));
  }
  // both revisions together
  const page3 = await page.context().newPage();
  await open(page3, '&hero=release&npc=revision,revision-b2');
  expect(await api(page3, 'artUrl', 'npc.elder.idle.down.0')).not.toBe(await api(page2, 'artUrl', 'npc.elder.idle.down.0'));
  expect(await api(page3, 'artUrl', 'npc.smith.idle.down.0')).toBe(await api(page, 'artUrl', 'npc.smith.idle.down.0'));
});
