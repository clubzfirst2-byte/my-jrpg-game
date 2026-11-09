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

test('the elder, the merchant and the guard use their release art (16×28) beside the release hero; the others keep the placeholder', async ({ page }, testInfo) => {
  const warnings = [];
  page.on('console', (m) => {
    if (m.text().startsWith('art:')) warnings.push(m.text());
  });
  const errors = await open(page);
  expect(await api(page, 'art')).toMatchObject({ density: 2, overrides: 248 + 120, hero: { w: 16, h: 28 } });
  for (const id of ['elder', 'guard', 'merchant']) {
    await api(page, 'standBy', id);
    await waitTicks(page, 10);
    const s = await sprite(page, id);
    expect(s.key, id).toMatch(new RegExp(`^npc\\.${id}\\.(idle|walk)\\.(down|up|right|left)\\.\\d$`));
    expect([s.w, s.h], id).toEqual([16, 28]);
    await page.screenshot({ path: testInfo.outputPath(`${id}.png`) });
  }
  await api(page, 'standBy', 'cook');
  await waitTicks(page, 10);
  const cook = await sprite(page, 'cook');
  expect(cook.key).toMatch(/^npc\.2\.walk\./);
  expect([cook.w, cook.h]).toEqual([16, 16]);
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

test('?npc=placeholder keeps the placeholder villagers; normal play shows the release villagers with the release hero', async ({ page }) => {
  await open(page, '&hero=release&npc=placeholder');
  expect((await api(page, 'art')).overrides).toBe(248);
  await api(page, 'standBy', 'elder');
  await waitTicks(page, 10);
  expect((await sprite(page, 'elder')).key).toMatch(/^npc\.1\.walk\./);
  // normal play (no ?hero, since PR #43): the release hero and the release villagers together
  const page2 = await page.context().newPage();
  await open(page2, '');
  expect(await api(page2, 'art')).toMatchObject({ density: 2, overrides: 248 + 120 });
  await api(page2, 'standBy', 'elder');
  await waitTicks(page2, 10);
  expect((await sprite(page2, 'elder')).key).toMatch(/^npc\.elder\./);
  // ?hero=placeholder: the placeholder hero and the placeholder villagers (as before the release art)
  const page4 = await page.context().newPage();
  await open(page4, '&hero=placeholder');
  expect(await api(page4, 'art')).toMatchObject({ density: 1, overrides: 0 });
  // the villagers' release art alone (without the hero's) can be asked for
  const page3 = await page.context().newPage();
  await open(page3, '&hero=placeholder&npc=release');
  expect(await api(page3, 'art')).toMatchObject({ density: 2, overrides: 120 });
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
