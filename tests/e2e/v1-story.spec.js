import { test, expect } from '@playwright/test';
import { waitTicks } from './ticks.js';

// v1.0 story (docs/story/V1_STORY_PROPOSAL.md C3 / C4 / C14): the princess's 写し身 by the beach
// record stone (see-through), talked to with the attack button; once met she also waits by the
// other record stones. The new villagers are in 風見の村 and by the pass to the forest.

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);
const sprite = async (page, id) => (await api(page, 'npcSprites')).find((s) => s.id === id);

async function open(page) {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/?map=world&time=10&season=summer');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await api(page, 'clearEnemies');
  return errors;
}

/** Taps through the lines until the box asks a question or closes. */
async function readOn(page) {
  for (let k = 0; k < 12; k++) {
    const v = await api(page, 'dialogue');
    if (!v || v.choices) return v;
    await page.click('#dialogue');
  }
  return api(page, 'dialogue');
}

test('the 写し身 on the beach: see-through, spoken to with the attack button; then by every record stone', async ({ page }, testInfo) => {
  const errors = await open(page);
  const ids = async () => (await api(page, 'npcs')).map((n) => n.id);
  expect(await ids()).toContain('princess_beach');
  expect(await ids()).not.toContain('princess_plains');
  await api(page, 'standBy', 'princess_beach');
  await waitTicks(page, 10);
  const s = await sprite(page, 'princess_beach');
  expect(s.key).toMatch(/^npc\.(princess\.(idle|walk)|9\.walk)\./); // her release art once it is in, a placeholder until then
  expect(s.alpha).toBeGreaterThan(0.3);
  expect(s.alpha).toBeLessThan(1);
  await page.screenshot({ path: testInfo.outputPath('princess-beach.png') });
  await expect.poll(() => api(page, 'nearby')).toBe('talk');
  await page.keyboard.press('KeyJ');
  await expect(page.locator('.dialogue-speaker')).toHaveText('星環の姫');
  const q = await readOn(page);
  expect(q.choices).toEqual(['うなずく', '胸の石を見る']);
  await page.click('#dialogue-choice-0');
  await readOn(page);
  await expect(page.locator('#dialogue')).toBeHidden();
  const p = await api(page, 'progress');
  expect(p.flags.princess_met).toBe(true);
  expect(p.quests.star_ring_call).toBe('active');
  await expect.poll(async () => (await api(page, 'toasts')).join('|')).toContain('星環の呼び声');
  // Now she waits by the other record stones too.
  await expect.poll(ids).toContain('princess_plains');
  for (const r of ['desert', 'mountains', 'forest', 'lake']) expect(await ids()).toContain(`princess_${r}`);
  await api(page, 'standBy', 'princess_forest'); // the east column: her art is in the base bundle
  await expect.poll(async () => (await sprite(page, 'princess_forest'))?.alpha ?? 1, { timeout: 10_000 }).toBeLessThan(1);
  expect(errors).toEqual([]);
});

test('the new villagers: the woman and the smith in the village, the traveller by the pass', async ({ page }, testInfo) => {
  const errors = await open(page);
  for (const [id, speaker] of [
    ['woman', '村の女性'],
    ['smith', '鍛冶職人'],
    ['traveller', '旅人'],
  ]) {
    await api(page, 'standBy', id);
    await expect.poll(() => sprite(page, id), { timeout: 10_000 }).toBeTruthy(); // (the plains art loads near it)
    const s = await sprite(page, id);
    expect(s.alpha, id).toBe(1);
    await api(page, 'talkTo', id);
    await expect(page.locator('.dialogue-speaker')).toHaveText(speaker);
    const q = await readOn(page);
    expect(q.choices, id).toEqual(['うなずく', '首を横にふる']);
    await page.screenshot({ path: testInfo.outputPath(`${id}.png`) });
    await page.click('#dialogue-choice-1');
    await readOn(page);
    await expect(page.locator('#dialogue')).toBeHidden();
  }
  expect(errors).toEqual([]);
});
