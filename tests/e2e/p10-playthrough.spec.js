import { test, expect } from '@playwright/test';
import { makeEnvelope, fnv1a } from '../../src/save/saveFormat.js';
import { LEGACY_OBJECTS } from '../../src/save/legacyObjects.js';

// P10.6: a playthrough from the title screen across every region, then つづきから — and an old save
// (written by P10.2, schema 2) still loads. (tests/unit/playthrough.test.js checks that every place
// in the world can be reached; tests/unit/compat.test.js loads saves of every era.)

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);

async function openTitle(page) {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await expect(page.locator('#title-screen')).toBeVisible();
  return errors;
}

/** Holds a key until `done()` (or gives up). */
async function holdUntil(page, key, done, ms = 6000) {
  await page.keyboard.down(key);
  try {
    await expect.poll(done, { timeout: ms, intervals: [50] }).toBe(true);
  } finally {
    await page.keyboard.up(key);
  }
}

test('a playthrough: every region, a quest, a night at the inn, a core purified — and it all comes back', async ({ page }, testInfo) => {
  test.setTimeout(150_000);
  const errors = await openTitle(page);
  await page.click('#title-new');
  await expect(page.locator('#title-screen')).toBeHidden();
  // (Enemies stay — the cores of the murk are enemies too; a deep well of health instead.)
  await api(page, 'setHp', 400);
  const places = await api(page, 'places');
  const cp = Object.fromEntries(places.checkpoints.map((c) => [c.id, c]));
  const touch = async (id) => {
    await api(page, 'teleport', cp[id].tx, cp[id].ty);
    await expect.poll(async () => (await api(page, 'progress')).checkpoints).toContain(id);
  };
  // The island, then down the causeway on foot into the plains.
  await touch('beach');
  await api(page, 'teleport', 47, 66);
  await holdUntil(page, 'ArrowDown', async () => (await api(page, 'stream')).region === 'plains', 15_000);
  await touch('plains');
  // The elder's request.
  await api(page, 'standBy', 'elder');
  await page.keyboard.press('j');
  for (let k = 0; k < 12 && (await api(page, 'progress')).quests.lost_charm !== 'active'; k++) {
    const d = await api(page, 'dialogue');
    if (!d) {
      await api(page, 'standBy', 'elder');
      await page.keyboard.press('j');
    } else if (d.choices) await page.click('#dialogue-choice-0');
    else await page.click('#dialogue');
    await page.waitForTimeout(120);
  }
  while (await api(page, 'dialogue')) await page.click('#dialogue');
  expect((await api(page, 'progress')).quests.lost_charm).toBe('active');
  // East over the pass into the forest, then north to the mountains and south to the lake.
  const pass = places.warps.find((w) => w.id === 'pass-forest');
  await api(page, 'teleport', pass.tx - 3, pass.ty);
  await holdUntil(page, 'ArrowRight', async () => (await api(page, 'stream')).region === 'forest');
  await touch('forest');
  await touch('mountains');
  await touch('lake');
  await touch('desert');
  // The forest core.
  const boss = (await api(page, 'bosses')).find((b) => b.id === 'core_forest');
  await api(page, 'setHp', 400);
  await api(page, 'teleport', Math.floor(boss.x / 16), Math.floor(boss.y / 16) + 4);
  await expect(page.locator('#boss-bar')).toBeVisible();
  await api(page, 'hurtBoss', 'core_forest', 999);
  await expect.poll(async () => (await api(page, 'progress')).bosses).toEqual(['core_forest']);
  // A night at the inn (in through the door, to a bed).
  await api(page, 'teleport', 18, 72 + 23);
  await holdUntil(page, 'ArrowUp', async () => (await api(page, 'area')) === 'inn');
  await holdUntil(page, 'ArrowLeft', async () => (await api(page, 'player')).x < 102 * 16 + 8, 3000);
  await holdUntil(page, 'ArrowUp', async () => (await api(page, 'nearby')) === 'sleep');
  await page.click('#use-button');
  await page.click('#dialogue-choice-0');
  expect((await api(page, 'weather')).clock).toMatch(/^06:0\d/);
  while (await api(page, 'dialogue')) await page.click('#dialogue');
  await page.screenshot({ path: testInfo.outputPath('inn-morning.png') });
  const before = await api(page, 'progress');
  expect(await api(page, 'saveNow')).toBe(true);

  // つづきから
  await page.reload();
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await page.click('#title-continue');
  await expect(page.locator('#title-screen')).toBeHidden();
  const after = await api(page, 'progress');
  expect(after.checkpoints.sort()).toEqual(['beach', 'desert', 'forest', 'lake', 'mountains', 'plains']);
  expect(after.bosses).toEqual(['core_forest']);
  expect(after.quests.lost_charm).toBe('active');
  expect(after.inv.money).toBe(before.inv.money);
  expect((await api(page, 'bosses')).map((b) => b.id)).not.toContain('core_forest');
  expect((await api(page, 'weather')).clock).toMatch(/^06:/);
  expect(errors).toEqual([]);
});

test('a save written by P10.2 (schema 2, objects named by list index) loads with つづきから', async ({ page }) => {
  const errors = await openTitle(page);
  // As P10.2 wrote it: a broken jar named by its index in that version's object list.
  const list = LEGACY_OBJECTS.p10.split(' ');
  const k = list.findIndex((id) => id.startsWith('jar@'));
  const [tx, ty] = list[k].split('@')[1].split(',').map(Number);
  const data = {
    openedChests: ['camp'],
    checkpoints: ['beach', 'plains'],
    checkpoint: 'plains',
    landmarks: ['tower', 'village'],
    maxHp: 12,
    gates: [],
    inv: { money: 42, items: { mushroom: 2 }, weapons: [{ id: 'wood_sword', dur: 20, lvl: 0 }], bows: [], equip: { weapon: 0, bow: -1, head: null, body: null, legs: null }, recipes: [] },
    picked: {},
    abilities: ['light'],
    ability: 'light',
    maxStamina: 100,
    flags: { elder_met: true },
    quests: { lost_charm: 'active' },
    worldMs: 3 * 24 * 60_000 + 10 * 60_000,
    worldDiff: { [`${Math.floor(tx / 32)},${Math.floor(ty / 32)}`]: { [k]: { gone: true } } },
  };
  const e = { ...makeEnvelope(data, '0.0.1', 5, 1_760_000_000_000), schemaVersion: 2 };
  e.checksum = fnv1a(JSON.stringify([e.schemaVersion, e.gameVersion, e.savedAt, e.seq, e.data]));
  await page.evaluate(
    (env) =>
      new Promise((resolve, reject) => {
        const req = indexedDB.open('seimyaku', 1);
        req.onupgradeneeded = () => req.result.createObjectStore('saves');
        req.onsuccess = () => {
          const tx = req.result.transaction('saves', 'readwrite');
          tx.objectStore('saves').put(env, 'slot1A');
          tx.objectStore('saves').put({ latest: 'A', seq: env.seq }, 'slot1meta');
          tx.oncomplete = () => resolve(undefined);
          tx.onerror = () => reject(tx.error);
        };
      }),
    e,
  );
  await page.reload();
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await expect(page.locator('#title-continue')).toBeEnabled();
  await page.click('#title-continue');
  await expect(page.locator('#title-screen')).toBeHidden();
  const pr = await api(page, 'progress');
  expect(pr.inv.money).toBe(42);
  expect(pr.quests.lost_charm).toBe('active');
  expect(pr.checkpoint).toBe('plains');
  expect(pr.bosses).toEqual([]);
  // Back at the plains checkpoint, running.
  expect((await api(page, 'stream')).region).toBe('plains');
  await page.waitForTimeout(500);
  expect(errors).toEqual([]);
});
