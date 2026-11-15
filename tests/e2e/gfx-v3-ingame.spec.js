// @ts-check
// The in-game inspection of df638e6 (gfx_r1/inspect_v3_ingame.md): the fixes, under ?v3=1 and, where the
// fix is for both (the season switch), ?v3=0 too; ?v3=0 keeps everything else as before.
import { test, expect } from '@playwright/test';

const api = (page, f, ...a) => page.evaluate(([fn, args]) => window.__debugApi[fn](...args), [f, a]);
const PRO = { name: '15 Pro', width: 852, height: 393, dpr: 3 };
const SE = { name: 'SE', width: 667, height: 375, dpr: 2 };
const FOREST_AT = [140, 149];
const VILLAGE_AT = [28, 89];

async function open(browser, screen, query) {
  const context = await browser.newContext({ viewport: { width: screen.width, height: screen.height }, deviceScaleFactor: screen.dpr, isMobile: true, hasTouch: true });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto(`/?map=world&time=10&season=summer&weather=clear${query}`);
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 30_000 });
  await api(page, 'clearEnemies');
  return { context, page, errors };
}

const settle = (page) => expect.poll(async () => (await api(page, 'stream')).pending, { timeout: 30_000 }).toBe(0);

/** Stands the hero just north of a tall forest tree (its crown over him); returns the faded trees, or [] when none was found. */
async function underTree(page) {
  await api(page, 'teleport', ...FOREST_AT);
  await settle(page);
  await page.waitForTimeout(500);
  const trees = (await api(page, 'treesOnScreen')).filter((t) => t.region === 'forest');
  const at = new Set(trees.map((t) => `${t.tx},${t.ty}`));
  for (const t of trees) {
    if (at.has(`${t.tx},${t.ty - 1}`)) continue;
    await api(page, 'teleport', t.tx, t.ty - 1);
    await page.waitForTimeout(250);
    const f = await api(page, 'fadedTrees');
    if (f.some((x) => x.type === 'tree')) return f;
  }
  return [];
}

test('P1 the tree in front: ?v3=1 the faded tree is drawn behind the hero (still faded); ?v3=0 in front, faded, as before', async ({ browser }, testInfo) => {
  test.setTimeout(120_000);
  for (const [q, behind] of [['&v3=1', true], ['&v3=0', false]]) {
    const { context, page, errors } = await open(browser, SE, q);
    const faded = (await underTree(page)).filter((x) => x.type === 'tree');
    expect(faded.length, q).toBeGreaterThan(0);
    for (const t of faded) {
      expect(t.alpha, q).toBe(0.5);
      expect(t.behindHero, `${q} ${t.tx},${t.ty}`).toBe(behind);
      if (!behind) expect(t.zIndex).toBe(t.feet);
    }
    await page.screenshot({ path: testInfo.outputPath(`under-tree${q.replace(/[&=]/g, '')}.png`) });
    // walking out from under it: back to its own draw order, opaque
    const p = await api(page, 'player');
    await api(page, 'teleport', Math.floor(p.x / 16), Math.floor(p.y / 16) - 6);
    await page.waitForTimeout(300);
    expect((await api(page, 'fadedTrees')).filter((x) => x.type === 'tree' && faded.some((f) => f.tx === x.tx && f.ty === x.ty))).toEqual([]);
    expect(errors).toEqual([]);
    await context.close();
  }
});

test('P1 the season switch: no frame without the world (chunks and objects all along), the new season in, ?v3=1 and ?v3=0', async ({ browser }) => {
  test.setTimeout(180_000);
  for (const q of ['&v3=1', '&v3=0']) {
    for (const [where, to] of [[FOREST_AT, 'autumn'], [VILLAGE_AT, 'winter']]) {
      const { context, page, errors } = await open(browser, PRO, q);
      await api(page, 'teleport', ...where);
      await settle(page);
      await page.waitForTimeout(800);
      const before = await api(page, 'stream');
      expect(before.chunks).toBeGreaterThan(0);
      const s0 = (await api(page, 'frameLog')).seasonSwitches;
      await api(page, 'frameLogStart');
      await api(page, 'setSeason', to);
      await expect.poll(async () => (await api(page, 'season')).view, { timeout: 30_000 }).toBe(to);
      await page.waitForTimeout(500);
      const { frames, seasonSwitches } = await api(page, 'frameLog');
      expect(seasonSwitches - s0, `${q} ${to}`).toBe(1);
      expect(frames.length).toBeGreaterThan(3);
      // every frame drawn had the world: as many chunks as before (never 0), its trees and things
      for (const [i, f] of frames.entries()) {
        expect(f.chunks, `${q} ${to} frame ${i} ${JSON.stringify(f)}`).toBeGreaterThanOrEqual(Math.min(before.chunks, 1));
        expect(f.objects, `${q} ${to} frame ${i}`).toBeGreaterThan(0);
      }
      // the frame of the switch: the chunks there before are there after, at once
      const at = frames.findIndex((f) => f.season === to);
      expect(at).toBeGreaterThan(0);
      expect(frames[at].chunks, `${q} ${to}`).toBeGreaterThanOrEqual(frames[at - 1].chunks);
      expect(errors).toEqual([]);
      await context.close();
    }
  }
});

test('P2 a long move under ?v3=1: dark until the ground is in (never villagers over no ground); ?v3=0 no cover', async ({ browser }) => {
  test.setTimeout(120_000);
  for (const q of ['&v3=1', '&v3=0']) {
    const { context, page, errors } = await open(browser, SE, q);
    await api(page, 'teleport', 52, 100);
    await settle(page);
    await page.waitForTimeout(500);
    await api(page, 'frameLogStart');
    await api(page, 'teleport', ...FOREST_AT);
    await page.waitForTimeout(300);
    await api(page, 'teleport', ...VILLAGE_AT);
    await page.waitForTimeout(400);
    await settle(page);
    await expect.poll(async () => (await api(page, 'stream')).covered, { timeout: 10_000 }).toBe(false);
    await page.waitForTimeout(200);
    const { frames } = await api(page, 'frameLog');
    expect(frames.length).toBeGreaterThan(2);
    if (q === '&v3=1') {
      // covered from the jump on, uncovered only once nothing around the view waits
      expect(frames.some((f) => f.covered)).toBe(true);
      for (const [i, f] of frames.entries()) if (!f.covered && i > 0 && frames[i - 1].covered) expect(f.pending, `frame ${i}`).toBe(0);
      for (const f of frames) if (f.pending > 0 && f.chunks < 4) expect(f.covered).toBe(true);
      expect(frames.at(-1).covered).toBe(false);
    } else expect(frames.every((f) => !f.covered)).toBe(true);
    expect(errors).toEqual([]);
    await context.close();
  }
});

test('P2 the camera leads the hero under ?v3=1 (small, eased; none standing); ?v3=0 centred as before', async ({ browser }) => {
  test.setTimeout(90_000);
  for (const q of ['&v3=1', '&v3=0']) {
    const { context, page, errors } = await open(browser, PRO, q);
    await api(page, 'teleport', 30, 88); // (the village road, open to the east)
    await settle(page);
    await page.waitForTimeout(600);
    const lead = async () => {
      const c = await api(page, 'camera');
      const p = await api(page, 'player');
      return c.x - p.x;
    };
    expect(Math.abs(await lead())).toBeLessThanOrEqual(1);
    await page.keyboard.down('ArrowRight');
    await page.waitForTimeout(1500);
    const moving = await lead();
    await page.keyboard.up('ArrowRight');
    if (q === '&v3=1') {
      expect(moving).toBeGreaterThan(3);
      expect(moving).toBeLessThanOrEqual(21);
    } else {
      // (as before: the camera's easing trails the hero a little, never ahead)
      expect(moving).toBeLessThanOrEqual(1);
      expect(moving).toBeGreaterThanOrEqual(-16);
    }
    await page.waitForTimeout(2500);
    expect(Math.abs(await lead())).toBeLessThanOrEqual(1.5);
    expect(errors).toEqual([]);
    await context.close();
  }
});
