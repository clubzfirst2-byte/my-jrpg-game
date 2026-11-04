import { test, expect } from '@playwright/test';

// P3.5: the first island — title screen, chests, checkpoints, saving and loading, the secret cave.
// Every test gets a fresh browser context, so IndexedDB starts empty.

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);

/** Opens the game at the title (no ?map=, so saving is on). */
async function openTitle(page) {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await expect(page.locator('#title-screen')).toBeVisible();
  return errors;
}

/** Title -> はじめから, enemies removed (these tests are not about combat). */
async function startNew(page) {
  const errors = await openTitle(page);
  await page.click('#title-new');
  await expect(page.locator('#title-screen')).toBeHidden();
  await api(page, 'clearEnemies');
  return errors;
}

const CHESTS = { camp: [86, 44], islet: [87, 63], cave: [107, 5] };

/** Stands below a chest facing it and presses attack until that chest is open. */
async function openChest(page, id) {
  const [tx, ty] = CHESTS[id];
  await api(page, 'teleport', tx, ty + 1);
  await api(page, 'face', 'up');
  await expect
    .poll(
      async () => {
        await page.keyboard.press('KeyJ');
        return (await api(page, 'progress')).openedChests;
      },
      { timeout: 5_000 },
    )
    .toContain(id);
}

test('the title screen starts a new game on the island', async ({ page }, testInfo) => {
  const errors = await openTitle(page);
  await expect(page.locator('#title-continue')).toBeDisabled(); // nothing saved yet
  await page.screenshot({ path: testInfo.outputPath('title.png') });
  expect(await api(page, 'tick')).toBe(0); // the game waits on the title
  await page.click('#title-new');
  await expect.poll(() => api(page, 'tick')).toBeGreaterThan(10);
  expect((await api(page, 'saveInfo')).enabled).toBe(true);
  await page.screenshot({ path: testInfo.outputPath('island-start.png') });
  expect(errors).toEqual([]);
});

test('opening a chest gives its item, shows it, and saves', async ({ page }, testInfo) => {
  const errors = await startNew(page);
  await openChest(page, 'camp'); // the camp chest
  const pr = await api(page, 'progress');
  expect(pr.openedChests).toEqual(['camp']);
  expect(pr.inv.items.grip_boots).toBe(1); // P6: the camp chest holds climbing boots
  await expect.poll(async () => (await api(page, 'toasts')).join('|')).toContain('岩登りの靴を手に入れた');
  await expect.poll(async () => (await api(page, 'saveInfo')).saves).toBeGreaterThan(0);
  await page.screenshot({ path: testInfo.outputPath('chest-open.png') });
  expect(errors).toEqual([]);
});

test('progress survives a reload: つづきから restores chests and the checkpoint', async ({ page }) => {
  const errors = await startNew(page);
  await openChest(page, 'camp');
  await api(page, 'teleport', 72, 47); // the camp checkpoint stone
  await expect.poll(async () => (await api(page, 'progress')).checkpoint).toBe('camp');
  expect(await api(page, 'saveNow')).toBe(true);

  await page.reload();
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await expect(page.locator('#title-continue')).toBeEnabled();
  await page.click('#title-continue');
  const pr = await api(page, 'progress');
  expect(pr.openedChests).toEqual(['camp']);
  expect(pr.checkpoint).toBe('camp');
  // Back at the checkpoint, not the beach.
  const p = await api(page, 'player');
  expect(Math.floor(p.x / 16)).toBe(72);
  expect(Math.floor(p.y / 16)).toBe(48);
  expect(pr.inv.items.grip_boots).toBe(1);
  expect(errors).toEqual([]);
});

test('はじめから over an existing save asks first', async ({ page }) => {
  await startNew(page);
  await openChest(page, 'camp');
  expect(await api(page, 'saveNow')).toBe(true);
  await page.reload();
  await expect(page.locator('#title-screen')).toBeVisible();
  await page.click('#title-new');
  await expect(page.locator('.title-confirm')).toBeVisible();
  await expect(page.locator('.title-confirm')).toContainText('上書き');
  await page.click('#title-confirm-no');
  await expect(page.locator('#title-continue')).toBeVisible();
  await page.click('#title-new');
  await page.click('#title-confirm-yes');
  expect((await api(page, 'progress')).openedChests).toEqual([]);
});

test('a damaged latest save falls back to the previous one', async ({ page }) => {
  await startNew(page);
  await openChest(page, 'camp');
  expect(await api(page, 'saveNow')).toBe(true); // a generation without the islet money
  const before = (await api(page, 'saveInfo')).saves;
  await openChest(page, 'islet'); // the chest triggers exactly one autosave: with the money
  await expect.poll(async () => (await api(page, 'saveInfo')).saves).toBe(before + 1);
  // Damage the latest generation directly in IndexedDB.
  await page.evaluate(
    () =>
      new Promise((resolve, reject) => {
        const req = indexedDB.open('seimyaku', 1);
        req.onsuccess = () => {
          const tx = req.result.transaction('saves', 'readwrite');
          const store = tx.objectStore('saves');
          const meta = store.get('slot1meta');
          meta.onsuccess = () => {
            const key = `slot1${meta.result.latest}`;
            const g = store.get(key);
            g.onsuccess = () => store.put({ ...g.result, data: { ...g.result.data, maxHp: 999 } }, key);
          };
          tx.oncomplete = () => resolve(undefined);
          tx.onerror = () => reject(tx.error);
        };
      }),
  );
  await page.reload();
  await expect(page.locator('.title-note')).toContainText('ひとつ前');
  await page.click('#title-continue');
  const pr = await api(page, 'progress');
  expect(pr.inv.money).toBe(0); // the previous generation (the damaged one had the islet money)
  expect(pr.openedChests).toEqual(['camp']);
});

test('the secret cave: in through the cliff opening, out onto the high ledge', async ({ page }, testInfo) => {
  const errors = await startNew(page);
  await api(page, 'teleport', 34, 43);
  await page.keyboard.down('ArrowUp');
  await expect.poll(() => api(page, 'area'), { timeout: 5_000 }).toBe('cave');
  await page.keyboard.up('ArrowUp');
  const cam = await api(page, 'camera');
  expect(cam.bounds.x).toBe(98 * 16); // the camera is held inside the cave
  await page.waitForTimeout(300);
  await page.screenshot({ path: testInfo.outputPath('cave.png') });

  await openChest(page, 'cave');
  await api(page, 'teleport', 108, 4);
  await page.keyboard.down('ArrowUp');
  await expect.poll(() => api(page, 'area'), { timeout: 5_000 }).toBe(null);
  await page.keyboard.up('ArrowUp');
  const p = await api(page, 'player');
  expect(p.z).toBe(48); // on the north ledge
  expect((await api(page, 'camera')).bounds.x).toBe(0);
  expect(errors).toEqual([]);
});

test('discovered landmarks off-screen get an edge marker', async ({ page }) => {
  await startNew(page);
  await api(page, 'teleport', 48, 35); // high ground: the camp smoke and the big tree are spotted
  await expect.poll(async () => (await api(page, 'progress')).landmarks).toEqual(expect.arrayContaining(['tower', 'smoke', 'bigtree']));
  await api(page, 'teleport', 20, 64);
  await expect.poll(() => api(page, 'markers')).toEqual(expect.arrayContaining(['smoke', 'tower']));
});
