import { test, expect } from '@playwright/test';

// v1.0 C5-C7 (docs/story/V1_STORY_PROPOSAL.md, C15 E2E part): the beach ring opens with source_open
// and leads to the source's antechamber; in the arena 淀みの源 shrugs off blows while inverted,
// staggers when its four seats are awake, and is purified by three hits (the flag source_purified
// and the event sourcePurified, the hook for the ending). Uses the debug API (src/debug/finalBossDebug.js).

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);

async function open(page) {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/?map=world&time=10&season=summer');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  return errors;
}

test('the beach ring is only a ring until source_open; then walking up into it leads to the antechamber', async ({ page }, testInfo) => {
  const errors = await open(page);
  await api(page, 'clearEnemies');
  const places = await api(page, 'sourcePlaces');
  expect(places.ring).toMatchObject({ facing: 'up' });
  const walkIn = async () => {
    await api(page, 'teleport', places.ring.tx, places.ring.ty + 1);
    await page.keyboard.down('ArrowUp');
    await page.waitForTimeout(700);
    await page.keyboard.up('ArrowUp');
    return api(page, 'area');
  };
  expect(await walkIn()).toBe(null);
  await page.screenshot({ path: testInfo.outputPath('ring-closed.png') });
  // The ring's art is in the base bundle; the source's own bundle is not loaded on the island.
  expect((await api(page, 'stream')).bundleNames).not.toContain('common:source');
  await api(page, 'setFlag', 'source_open');
  await api(page, 'teleport', places.ring.tx, places.ring.ty + 2);
  await page.waitForTimeout(300);
  await page.screenshot({ path: testInfo.outputPath('ring-open.png') });
  expect(await walkIn()).toBe('source_gate');
  expect(errors).toEqual([]);
});

test('the source: invulnerable while inverted, staggers with four seats awake, purified by three hits', async ({ page }, testInfo) => {
  const errors = await open(page);
  await api(page, 'clearEnemies');
  await api(page, 'setFlag', 'source_open');
  await api(page, 'setHp', 400);
  const places = await api(page, 'sourcePlaces');
  expect(places.seats.map((s) => s.id).sort()).toEqual(['source-echo', 'source-fire', 'source-light', 'source-weight']);
  await api(page, 'enterSourceArena');
  expect(await api(page, 'area')).toBe('source_arena');
  // (Attacks can knock the player around: keep them in the middle of the arena, full of health.)
  const stay = async () => {
    await api(page, 'teleport', places.arena.tx, places.arena.ty - 5);
    await api(page, 'setHp', 400);
  };
  await stay();
  // The source's art bundle is loaded near its arena (the desert region).
  await expect.poll(async () => (await api(page, 'stream')).bundleNames, { timeout: 5000 }).toContain('common:source');
  await expect(page.locator('#boss-bar')).toBeVisible();
  await expect(page.locator('#boss-bar .boss-name')).toHaveText('淀みの源');
  await expect.poll(async () => (await api(page, 'toasts')).some((t) => t.includes('座'))).toBe(true);
  const boss = await api(page, 'finalBoss');
  expect(boss).toMatchObject({ hp: 90, maxHp: 90, phase: 1, awake: true });
  // Inverted: blows do nothing.
  expect(await api(page, 'strikeFinalBoss')).toBe(false);
  expect((await api(page, 'finalBoss')).hp).toBe(90);
  // The light seat is dark at the start.
  expect((await api(page, 'seats'))['source-light'].active).toBe(false);
  await page.screenshot({ path: testInfo.outputPath('source-inverted.png') });
  for (const hpAfter of [60, 30, 0]) {
    // Wake all four seats (again, after the last wave put them out) until the ring turns back.
    await expect
      .poll(
        async () => {
          await stay();
          await api(page, 'activateSeats');
          return (await api(page, 'finalBoss'))?.state;
        },
        { timeout: 15_000 },
      )
      .toBe('stagger');
    if (hpAfter === 90 - 30) await page.screenshot({ path: testInfo.outputPath('source-stagger.png') });
    expect(await api(page, 'strikeFinalBoss')).toBe(true);
    expect((await api(page, 'finalBoss')).hp).toBe(hpAfter);
  }
  await expect.poll(async () => (await api(page, 'flags')).source_purified).toBe(true);
  await expect.poll(async () => (await api(page, 'events')).includes('sourcePurified')).toBe(true);
  await expect.poll(async () => (await api(page, 'toasts')).some((t) => t.includes('淀みの源を浄化した'))).toBe(true);
  await expect(page.locator('#boss-bar')).toBeHidden();
  // Not one of the cores, no star shard; and gone for good.
  expect((await api(page, 'progress')).bosses).toEqual([]);
  await expect.poll(async () => api(page, 'finalBoss'), { timeout: 5000 }).toBe(null);
  await stay();
  await page.waitForTimeout(500);
  expect(await api(page, 'finalBoss')).toBe(null);
  // The beach ring is closed again.
  // (and, back on the island, the source's bundle is released)
  await api(page, 'teleport', places.ring.tx, places.ring.ty + 1);
  await page.keyboard.down('ArrowUp');
  await page.waitForTimeout(700);
  await page.keyboard.up('ArrowUp');
  expect(await api(page, 'area')).toBe(null);
  await expect.poll(async () => (await api(page, 'stream')).bundleNames, { timeout: 5000 }).not.toContain('common:source');
  expect(errors).toEqual([]);
});
