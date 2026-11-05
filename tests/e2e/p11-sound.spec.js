import { test, expect } from '@playwright/test';

// P11.2: sound — it starts on the first touch / key (iOS rule), game events make their sounds,
// the music follows where the player is, pausing silences it, and the volumes are remembered.

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);

async function open(page, { keepEnemies = false } = {}) {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/?map=world&time=10&season=summer');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  if (keepEnemies) await api(page, 'setHp', 400);
  else await api(page, 'clearEnemies');
  return errors;
}

test('sound starts on the first key press, and a sword swing makes its sound', async ({ page, browserName }) => {
  const errors = await open(page);
  expect((await api(page, 'audio')).unlocked).toBe(false); // nothing before the player does something
  await page.keyboard.press('j');
  await expect.poll(async () => (await api(page, 'audio')).lastSfx).toBe('swing');
  // (Headless WebKit has no audio output to start; the iPhone check is in the device test list.)
  if (browserName === 'chromium') await expect.poll(async () => (await api(page, 'audio')).unlocked).toBe(true);
  expect(errors).toEqual([]);
});

test('the music follows the player: fields, night, a house, a cave, a boss', async ({ page }) => {
  const errors = await open(page, { keepEnemies: true }); // (the cores of the murk are enemies)
  await page.keyboard.press('Shift'); // a key: sound allowed
  await expect.poll(async () => (await api(page, 'audio')).track).toBe('field');
  await api(page, 'teleport', 30, 200); // the desert
  await expect.poll(async () => (await api(page, 'audio')).track).toBe('desert');
  await api(page, 'teleport', 18, 72 + 23);
  await page.keyboard.down('ArrowUp');
  await expect.poll(async () => (await api(page, 'area'))).toBe('inn');
  await page.keyboard.up('ArrowUp');
  await expect.poll(async () => (await api(page, 'audio')).track).toBe('village');
  const mine = (await api(page, 'places')).warps.find((w) => w.id === 'mine-out');
  await api(page, 'teleport', mine.tx, mine.ty - 2);
  await expect.poll(async () => (await api(page, 'audio')).track).toBe('cave');
  const boss = (await api(page, 'bosses')).find((b) => b.id === 'core_desert');
  await api(page, 'setHp', 400);
  await api(page, 'teleport', Math.floor(boss.x / 16), Math.floor(boss.y / 16) + 4);
  await expect.poll(async () => (await api(page, 'audio')).track).toBe('boss');
  await api(page, 'teleport', 48, 60);
  await api(page, 'setHour', 22);
  await expect.poll(async () => (await api(page, 'audio')).track).toBe('night');
  expect(errors).toEqual([]);
});

test('pausing silences the sound; the volumes are set on the pause screen and remembered', async ({ page, browserName }) => {
  const errors = await open(page);
  await page.keyboard.press('j');
  await page.click('#pause-button');
  await expect(page.locator('#pause-overlay')).toBeVisible();
  if (browserName === 'chromium') await expect.poll(async () => (await api(page, 'audio')).state).toBe('suspended');
  await expect(page.locator('#volume-bgm')).toHaveText('BGM 50%');
  await page.click('#volume-bgm'); // 75%
  await page.click('#volume-sfx'); // 100%
  await expect(page.locator('#volume-bgm')).toHaveText('BGM 75%');
  await expect(page.locator('#volume-sfx')).toHaveText('効果音 100%');
  await expect(page.locator('#pause-overlay')).toBeVisible(); // the volume buttons do not resume
  expect((await api(page, 'audio')).volumes).toEqual({ bgm: 0.75, sfx: 1 });
  await page.click('#resume-button');
  await expect(page.locator('#pause-overlay')).toBeHidden();
  await page.reload();
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  expect((await api(page, 'audio')).volumes).toEqual({ bgm: 0.75, sfx: 1 });
  expect(errors).toEqual([]);
});
