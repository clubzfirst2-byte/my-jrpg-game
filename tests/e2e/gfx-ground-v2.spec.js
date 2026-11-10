import { test, expect } from '@playwright/test';

// gfx W1: the v2 ground (src/art-release-v2/terrain, src/view/groundV2.js) with ?terrain=v2: the flat
// ground on the dual grid (transitions, shore foam, deep water), 4 water frames, no second ground
// atlas; ?terrain=v1 (and the default, until the group is enabled) keeps the v1.1 ground as it is.

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);

async function open(page, query = '') {
  const problems = [];
  page.on('pageerror', (e) => problems.push(`pageerror: ${e.message}`));
  page.on('console', (m) => {
    if (m.type() === 'warning' || m.type() === 'error' || m.text().startsWith('art:')) problems.push(`${m.type()}: ${m.text()}`);
  });
  await page.goto(`/?map=world&time=10&season=summer&weather=clear${query}`);
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await api(page, 'clearEnemies');
  return problems;
}

async function visit(page, tx, ty) {
  const before = await page.evaluate(([x, y]) => {
    const n = window.__debugApi.stream().updates;
    window.__debugApi.teleport(x, y);
    return n;
  }, [tx, ty]);
  await expect.poll(async () => {
    const s = await api(page, 'stream');
    return s.updates >= before + 2 && s.pending === 0;
  }, { timeout: 10_000 }).toBe(true);
}

const textureMb = async (page) => (await api(page, 'textureList')).reduce((s, t) => s + (/:(\d+)x(\d+)$/.exec(t) ? RegExp.$1 * RegExp.$2 * 4 : 0), 0) / 1048576;

test('?terrain=v2: shore foam and deep water on the beach, 4 water frames, the ground in the base atlas', async ({ page }) => {
  const problems = await open(page, '&terrain=v2');
  await visit(page, 49, 69);
  const e = await api(page, 'terrainEdges');
  expect(e.groundV2).toBe(true);
  expect(e.fallbacks).toBe(0);
  expect(e.keys.some((k) => k.startsWith('tile.water.foam.'))).toBe(true);
  expect(e.keys.some((k) => k.startsWith('tile.water.deep'))).toBe(true);
  expect(e.keys.some((k) => /^tile\.(shore|bank)/.test(k))).toBe(false); // the v1.1 water edges are replaced
  // 4 frames, all of them shown
  const seen = new Set();
  await expect.poll(async () => seen.add((await api(page, 'terrainEdges')).frame).size, { timeout: 6_000, intervals: [60] }).toBe(4);
  // no atlas beside the base one for the ground; the regions load theirs as before
  const s = await api(page, 'stream');
  expect(s.bundleNames).not.toContain('common:ground');
  expect((await api(page, 'textureList')).filter((t) => t.endsWith(':2048x1024')).length).toBe(1);
  for (const [x, y] of [[50, 104], [48, 190], [162, 232], [150, 160], [175, 70]]) {
    await visit(page, x, y);
    expect((await api(page, 'terrainEdges')).fallbacks).toBe(0);
  }
  // (with the URL switch the page's preload of the v1 terrain sheet goes unused: a browser note, not the game's)
  expect(problems.filter((p) => !p.includes('was preloaded using link preload'))).toEqual([]);
});

test('?terrain=v1 and the default keep the v1.1 ground; v2 costs no more than 1 MB of images in the same place', async ({ page, browser }) => {
  const mb = {};
  for (const q of ['&terrain=v1', '']) {
    const p = q ? page : await (await browser.newContext({ viewport: page.viewportSize() ?? undefined })).newPage();
    const problems = await open(p, q);
    await visit(p, 49, 69);
    const e = await api(p, 'terrainEdges');
    expect(e.groundV2).toBe(false);
    expect(e.keys.some((k) => k.startsWith('tile.shore.'))).toBe(true);
    expect(e.keys.some((k) => k.includes('foam') || k.includes('deep'))).toBe(false);
    expect(problems).toEqual([]);
    if (q) mb.v1 = await textureMb(p);
    else await p.context().close();
  }
  const other = await (await browser.newContext({ viewport: page.viewportSize() ?? undefined })).newPage();
  await open(other, '&terrain=v2');
  await visit(other, 49, 69);
  mb.v2 = await textureMb(other);
  expect(mb.v2 - mb.v1, JSON.stringify(mb)).toBeLessThanOrEqual(1);
  await other.context().close();
});

test('?terrain=v2 does not touch the save: the same save data as v1 after the same steps', async ({ page }) => {
  const snap = {};
  for (const ver of ['v1', 'v2']) {
    await page.goto(`/?terrain=${ver}&e2e=1`);
    await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
    snap[ver] = await page.evaluate(() => Object.keys(localStorage).sort());
  }
  expect(snap.v2).toEqual(snap.v1);
});
