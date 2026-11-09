import { test, expect } from '@playwright/test';

// v1.0 C9 (the opening, minimal) and C10 (the ending), the C15 E2E part (docs/story/V1_STORY_PROPOSAL.md):
// はじめから → the opening (it plays, a tap skips it) → (debug: four cores) → the princess on the
// beach → the beach ring → the arena → (debug: the source purified) → her words by themselves →
// the ending screen (skipped) → the village in the morning → saved → reload → つづきから.

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);

/** Taps through the lines until the box asks a question or closes. */
async function readOn(page) {
  for (let k = 0; k < 16; k++) {
    const v = await api(page, 'dialogue');
    if (!v || v.choices) return v;
    await page.click('#dialogue');
  }
  return api(page, 'dialogue');
}
/** Reads a whole conversation, choosing the first answer each time. */
async function readAll(page) {
  for (let k = 0; k < 12; k++) {
    const v = await readOn(page);
    if (!v) return;
    await page.click('#dialogue-choice-0');
  }
}

test('はじめから → opening → the princess → the source → the ending → the village, saved and continued', async ({ page }, testInfo) => {
  test.setTimeout(150_000);
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await page.click('#title-new');
  await expect(page.locator('#title-screen')).toBeHidden();

  // The opening: it plays (the controls wait), then a tap skips it; never again.
  await expect.poll(async () => (await api(page, 'opening'))?.ms ?? -1).toBeGreaterThan(0);
  const start = await api(page, 'player');
  await page.screenshot({ path: testInfo.outputPath('opening.png') });
  await page.mouse.click(300, 200);
  await expect.poll(() => api(page, 'opening')).toBe(null);
  expect((await api(page, 'flags')).opening_seen).toBe(true);
  expect((await api(page, 'player')).x).toBe(start.x);

  // Four cores (debug), then the princess on the beach: she opens the gate.
  await api(page, 'clearEnemies');
  await api(page, 'setHp', 400);
  expect(await api(page, 'setCores', 4)).toBe(4);
  await api(page, 'standBy', 'princess_beach');
  await api(page, 'talkTo', 'princess_beach');
  await readAll(page); // うなずく → the quest at once ready
  await api(page, 'talkTo', 'princess_beach');
  await readAll(page); // the report: the gate opens
  await expect(page.locator('#dialogue')).toBeHidden();
  expect((await api(page, 'flags')).source_open).toBe(true);
  expect((await api(page, 'progress')).quests.source_of_murk).toBe('active');

  // Through the beach ring into the antechamber, then the arena.
  const places = await api(page, 'sourcePlaces');
  await api(page, 'teleport', places.ring.tx, places.ring.ty + 1);
  await page.keyboard.down('ArrowUp');
  await expect.poll(() => api(page, 'area'), { timeout: 5000 }).toBe('source_gate');
  await page.keyboard.up('ArrowUp');
  await api(page, 'enterSourceArena');
  expect(await api(page, 'area')).toBe('source_arena');
  const stay = async () => {
    await api(page, 'teleport', places.arena.tx, places.arena.ty - 5);
    await api(page, 'setHp', 400);
  };
  await expect.poll(async () => (await api(page, 'finalBoss'))?.awake ?? false, { timeout: 5000 }).toBe(true);
  for (let round = 0; round < 3; round++) {
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
    expect(await api(page, 'strikeFinalBoss')).toBe(true);
  }
  await expect.poll(async () => (await api(page, 'flags')).source_purified).toBe(true);

  // About 2 s later the princess speaks by herself.
  await expect.poll(async () => (await api(page, 'dialogue'))?.speaker ?? null, { timeout: 8000 }).toBe('星環の姫');
  expect((await api(page, 'npcs')).map((n) => n.id)).toContain('princess_end');
  await page.screenshot({ path: testInfo.outputPath('ending-dialogue.png') });
  await readAll(page); // 石を合わせる → うなずく
  expect((await api(page, 'flags')).regalia_joined).toBe(true);

  // The ending screen: the title, the credits, then 「おわり」; skipped here.
  await expect(page.locator('#ending-screen')).toBeVisible();
  await expect(page.locator('#ending-screen h1')).toHaveText('星環のレガリア');
  await expect(page.locator('#ending-skip')).toBeVisible();
  await page.waitForTimeout(1000);
  await page.screenshot({ path: testInfo.outputPath('ending-screen.png') });
  await page.click('#ending-skip');
  await expect(page.locator('#ending-screen')).toHaveCount(0);

  // The village in front of the inn, 6:00, the plains stone, ending_seen; saved.
  await expect.poll(async () => (await api(page, 'flags')).ending_seen).toBe(true);
  const p = await api(page, 'progress');
  expect(p.checkpoint).toBe('plains');
  expect((await api(page, 'weather')).clock).toMatch(/^06:/);
  expect(await api(page, 'area')).toBe(null);
  await expect.poll(async () => (await api(page, 'npcs')).map((n) => n.id)).toContain('princess_home');
  await page.screenshot({ path: testInfo.outputPath('village-morning.png') });
  expect(await api(page, 'saveNow')).toBe(true);

  // つづきから: in the village; no opening, no ending again.
  await page.reload();
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await page.click('#title-continue');
  await expect(page.locator('#title-screen')).toBeHidden();
  await page.waitForTimeout(500);
  expect(await api(page, 'opening')).toBe(null);
  expect((await api(page, 'ending')).ending).toBe(null);
  await expect(page.locator('#ending-screen')).toHaveCount(0);
  const after = await api(page, 'progress');
  expect(after.flags).toMatchObject({ ending_seen: true, regalia_joined: true, opening_seen: true });
  expect(after.checkpoint).toBe('plains');
  expect((await api(page, 'npcs')).map((n) => n.id)).toContain('princess_home');
  expect(errors).toEqual([]);
});
