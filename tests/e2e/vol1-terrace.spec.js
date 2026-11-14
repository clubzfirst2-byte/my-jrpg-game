import { test, expect } from '@playwright/test';
import { waitTicks } from './ticks.js';
import { makeEnvelope, fnv1a } from '../../src/save/saveFormat.js';
import { WORLD } from '../../src/game/world/world.js';

// Volume phase 1: 風切りの段丘 (the plains' 奥地), the map, survey stones, travel between record
// stones, and save format 4 — in the real game, with real keys and taps.

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);
const R = WORLD.regions.find((r) => r.id === 'terrace');
const T = (x, y) => [R.tx + x, R.ty + y];
const tileOf = async (page) => {
  const p = await api(page, 'player');
  return { tx: Math.floor(p.x / 16), ty: Math.floor(p.y / 16), p };
};

async function hold(page, key, until, ms = 15_000) {
  await page.keyboard.down(key);
  try {
    await expect.poll(until, { timeout: ms, intervals: [50] }).toBe(true);
  } finally {
    await page.keyboard.up(key);
  }
}
/** Turns the player (a short press of a direction key). */
async function face(page, key) {
  await page.keyboard.down(key);
  await waitTicks(page, 4);
  await page.keyboard.up(key);
  await waitTicks(page, 2);
}
async function swing(page) {
  await page.keyboard.press('KeyJ');
  await waitTicks(page, 45);
}

/** Writes a save as v1.0 wrote it (format 3: no `surveyed`). */
async function putV1Save(page, data) {
  const e = { ...makeEnvelope(data, '1.0.0', 7, 1_790_000_000_000), schemaVersion: 3 };
  e.checksum = fnv1a(JSON.stringify([e.schemaVersion, e.gameVersion, e.savedAt, e.seq, e.data]));
  await page.evaluate(
    (env) =>
      new Promise((resolve, reject) => {
        const req = indexedDB.open('seimyaku', 1);
        req.onupgradeneeded = () => req.result.createObjectStore('saves');
        req.onsuccess = () => {
          const tx = req.result.transaction('saves', 'readwrite');
          tx.objectStore('saves').clear();
          tx.objectStore('saves').put(env, 'slot1A');
          tx.objectStore('saves').put({ latest: 'A', seq: env.seq }, 'slot1meta');
          tx.oncomplete = () => resolve(undefined);
          tx.onerror = () => reject(tx.error);
        };
        req.onerror = () => reject(req.error);
      }),
    e,
  );
}
const V1_HALF_WAY = {
  openedChests: ['ledge', 'windmill'],
  checkpoints: ['beach', 'hill', 'plains', 'forest'],
  checkpoint: 'plains',
  landmarks: ['tower', 'village', 'windmill'],
  maxHp: 16,
  gates: ['trial_light'],
  inv: { money: 321, items: { arrow: 9 }, weapons: [{ id: 'travel_sword', dur: 30, lvl: 0 }], bows: [{ id: 'wood_bow', dur: 20, lvl: 0 }], equip: { weapon: 0, bow: 0, head: null, body: null, legs: null }, recipes: [] },
  picked: {},
  abilities: ['light'],
  ability: 'light',
  maxStamina: 100,
  flags: { princess_met: true, elder_met: true },
  quests: { star_ring_call: 'active' },
  bosses: ['core_forest'],
  worldMs: 2 * 24 * 60_000 + 10 * 60_000,
  worldDiff: {},
};

test('a v1.0 save continues, walks into the terrace, reads the survey stone, glides the rift, solves 風車の試練, and travels home by the map', async ({ page }, testInfo) => {
  test.setTimeout(240_000);
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/?time=10&season=summer');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 30_000 });
  await putV1Save(page, V1_HALF_WAY);
  await page.reload();
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 30_000 });
  await expect(page.locator('#title-continue')).toBeEnabled();
  await page.click('#title-continue');
  await expect(page.locator('#title-screen')).toBeHidden();
  let pr = await api(page, 'progress');
  expect(pr.checkpoint).toBe('plains');
  expect(pr.bosses).toEqual(['core_forest']);
  expect(pr.inv.money).toBe(321);
  expect(pr.surveyed).toEqual([]); // a save from before the map: nothing drawn yet
  expect((await api(page, 'saveInfo')).loaded).toBe('ok');
  await api(page, 'clearEnemies');

  // East through the pass under the windmill hill (real walking).
  const pass = WORLD.warps.find((w) => w.id === 'pass-terrace');
  await api(page, 'teleport', pass.tx - 4, pass.ty);
  await hold(page, 'ArrowRight', async () => (await api(page, 'stream')).region === 'terrace');
  // The terrace is dressed in the plains art: no new bundle is loaded for it.
  await expect.poll(async () => (await api(page, 'stream')).pending, { timeout: 15_000 }).toBe(0);
  const stream = await api(page, 'stream');
  expect(stream.bundleNames.filter((b) => b.startsWith('region:'))).toEqual(['region:plains']);
  // On along the road to the record stone.
  const stone = WORLD.checkpoints.find((c) => c.id === 'terrace');
  await api(page, 'teleport', stone.tx - 3, stone.ty + 1);
  await hold(page, 'ArrowRight', async () => (await api(page, 'progress')).checkpoints.includes('terrace'));
  await page.screenshot({ path: testInfo.outputPath('terrace-entry.png') });

  // The knoll: the survey stone draws the terrace on the map.
  const sv = WORLD.surveys.find((s) => s.region === 'terrace');
  await api(page, 'teleport', sv.tx + 2, sv.ty + 1);
  await hold(page, 'ArrowLeft', async () => (await api(page, 'progress')).surveyed.includes('terrace'));
  await expect(page.locator('#toast')).toContainText('測量石');

  // The first glide: off the knoll's east edge, the glider opened in the air, over the rift.
  await api(page, 'teleport', ...T(26, 46));
  await page.keyboard.down('ArrowRight');
  await expect.poll(async () => (await api(page, 'player')).grounded === false, { timeout: 10_000, intervals: [16] }).toBe(true);
  await page.keyboard.press('Space');
  await expect.poll(async () => (await api(page, 'player')).gliding, { timeout: 5_000, intervals: [16] }).toBe(true);
  await page.screenshot({ path: testInfo.outputPath('terrace-glide.png') });
  await expect.poll(async () => (await api(page, 'player')).grounded, { timeout: 20_000, intervals: [50] }).toBe(true);
  await page.keyboard.up('ArrowRight');
  let at = await tileOf(page);
  expect(at.tx - R.tx).toBeGreaterThanOrEqual(35); // on the middle shelf
  expect(at.tx - R.tx).toBeLessThanOrEqual(58);
  expect(await api(page, 'events')).not.toContain('fell');
  // The wind is drawn where it blows (stand-in streaks): at the ledge of the east lane.
  await api(page, 'teleport', ...T(56, 59));
  await expect.poll(async () => (await api(page, 'winds')).shown, { timeout: 10_000 }).toBeGreaterThan(0);
  await page.screenshot({ path: testInfo.outputPath('terrace-lane.png') });

  // 風車の試練: in through the glowing pillar.
  const gate = WORLD.warps.find((w) => w.id === 'trial_vane-in');
  await api(page, 'teleport', gate.tx, gate.ty + 2);
  await hold(page, 'ArrowUp', async () => (await api(page, 'area')) === 'trial_vane');
  const a = WORLD.areas.find((x) => x.id === 'trial_vane');
  const room = (x, y) => [a.tx - 98 + x, a.ty + y];
  expect(await api(page, 'gates')).not.toContain('trial_vane');
  // Cut the brambles standing in the wind (three cuts), then push the crate out of its row.
  await api(page, 'teleport', ...room(100, 7));
  await face(page, 'ArrowRight');
  for (let k = 0; k < 3; k++) await swing(page);
  expect(await api(page, 'gates')).not.toContain('trial_vane'); // the crate still stops the wind
  await api(page, 'teleport', ...room(106, 8));
  await face(page, 'ArrowUp');
  await swing(page);
  await expect.poll(async () => await api(page, 'gates'), { timeout: 10_000 }).toContain('trial_vane');
  await page.screenshot({ path: testInfo.outputPath('trial-vane-open.png') });

  // Home by the map: Ⅱ → 地図 → 風見の村 → 移る.
  await page.click('#pause-button');
  await page.click('#open-map');
  await expect(page.locator('#map-menu')).toBeVisible();
  await expect(page.locator('#map-travel')).toBeDisabled();
  const model = await api(page, 'mapModel');
  expect(model.regions.find((r) => r.id === 'terrace').surveyed).toBe(true);
  expect(model.regions.find((r) => r.id === 'plains').surveyed).toBe(false);
  expect(await page.locator('.map-stone').count()).toBe(5); // beach, hill, plains, forest + terrace
  await page.screenshot({ path: testInfo.outputPath('map.png') });
  await page.click('.map-stone[data-id="plains"]');
  await expect(page.locator('#map-travel')).toBeEnabled();
  await page.click('#map-travel');
  await expect(page.locator('#map-menu')).toBeHidden();
  await expect(page.locator('#pause-overlay')).toBeHidden();
  await expect.poll(async () => (await api(page, 'stream')).region).toBe('plains');
  at = await tileOf(page);
  const home = WORLD.checkpoints.find((c) => c.id === 'plains');
  expect([at.tx, at.ty]).toEqual([home.tx, home.ty + 1]);
  await waitTicks(page, 30); // (the game runs on after travelling)

  // Saved in format 4; つづきから brings everything back.
  expect(await api(page, 'saveNow')).toBe(true);
  const stored = await page.evaluate(
    () =>
      new Promise((resolve) => {
        const req = indexedDB.open('seimyaku', 1);
        req.onsuccess = () => {
          const g = req.result.transaction('saves').objectStore('saves').getAll();
          g.onsuccess = () => resolve(g.result.filter((x) => x.schemaVersion).sort((p, q) => q.seq - p.seq)[0]);
        };
      }),
  );
  expect(stored.schemaVersion).toBe(4);
  expect(stored.data.surveyed).toEqual(['terrace']);
  await page.reload();
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 30_000 });
  await page.click('#title-continue');
  await expect(page.locator('#title-screen')).toBeHidden();
  pr = await api(page, 'progress');
  expect(pr.surveyed).toEqual(['terrace']);
  expect(pr.checkpoints).toEqual(['beach', 'hill', 'plains', 'forest', 'terrace']);
  expect(pr.checkpoint).toBe('plains');
  expect(pr.gates).toEqual(['trial_light', 'trial_vane']);
  expect(pr.bosses).toEqual(['core_forest']);
  expect(pr.flags).toEqual(V1_HALF_WAY.flags);
  expect(pr.quests).toEqual(V1_HALF_WAY.quests);
  expect(pr.inv.money).toBe(321);
  expect(errors).toEqual([]);
});

test('the map on a small iPhone: every button is a 44 px target, the list scrolls, travel works', async ({ page }, testInfo) => {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.setViewportSize({ width: 568, height: 320 });
  await page.goto('/?map=world&time=10&season=summer');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 30_000 });
  await api(page, 'clearEnemies');
  // Touch every record stone and survey stone outdoors (by standing beside each).
  for (const c of WORLD.checkpoints) {
    await api(page, 'teleport', c.tx, c.ty + 1);
    await expect.poll(async () => (await api(page, 'progress')).checkpoints.includes(c.id), { timeout: 10_000 }).toBe(true);
  }
  for (const s of WORLD.surveys) {
    await api(page, 'teleport', s.tx, s.ty + 1);
    await expect.poll(async () => (await api(page, 'progress')).surveyed.includes(s.region), { timeout: 10_000 }).toBe(true);
  }
  await page.click('#pause-button');
  await expect(page.locator('#open-map')).toBeVisible();
  // The pause screen's buttons do not overlap with the new one.
  const boxes = await page.evaluate(() => [...document.querySelectorAll('#pause-overlay button')].map((b) => ({ id: b.id, r: b.getBoundingClientRect().toJSON() })));
  for (const p of boxes) for (const q of boxes) if (p.id < q.id) expect(p.r.x < q.r.x + q.r.width && q.r.x < p.r.x + p.r.width && p.r.y < q.r.y + q.r.height && q.r.y < p.r.y + p.r.height, `${p.id} / ${q.id}`).toBe(false);
  await page.click('#open-map');
  await expect(page.locator('#map-menu')).toBeVisible();
  const small = await page.evaluate(() => [...document.querySelectorAll('#map-menu button')].map((b) => b.getBoundingClientRect()).filter((r) => r.width < 44 || r.height < 44).length);
  expect(small).toBe(0);
  expect(await page.locator('.map-stone').count()).toBe(WORLD.checkpoints.length);
  const model = await api(page, 'mapModel');
  expect(model.regions.every((r) => r.surveyed)).toBe(true);
  // The drawing is on screen and not empty; the list scrolls inside the menu (nothing spills off the screen).
  const canvas = await page.locator('#map-canvas').boundingBox();
  expect(canvas.width).toBeGreaterThan(150);
  expect(canvas.height).toBeGreaterThan(150);
  const menu = await page.locator('#map-menu').boundingBox();
  expect(menu.x).toBeGreaterThanOrEqual(0);
  expect(menu.y + menu.height).toBeLessThanOrEqual(320);
  const list = await page.locator('.map-list').evaluate((el) => ({ scroll: el.scrollHeight, client: el.clientHeight }));
  expect(list.scroll).toBeGreaterThan(list.client);
  await page.locator('.map-stone[data-id="terrace_east"]').scrollIntoViewIfNeeded();
  await page.screenshot({ path: testInfo.outputPath('map-568.png') });
  await page.click('.map-stone[data-id="terrace_east"]');
  await page.click('#map-travel');
  await expect.poll(async () => (await api(page, 'stream')).region).toBe('terrace');
  expect((await api(page, 'progress')).checkpoint).toBe('terrace_east');
  // Closing the map goes back to the pause screen; the game is still waiting.
  await page.click('#pause-button');
  await page.click('#open-map');
  await page.click('#map-close');
  await expect(page.locator('#pause-overlay')).toBeVisible();
  await page.click('#resume-button');
  await waitTicks(page, 20);
  expect((await api(page, 'player')).dead).toBe(false);
  expect(errors).toEqual([]);
});
