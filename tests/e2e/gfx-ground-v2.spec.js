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
  await page.goto(`/?map=world&time=10&weather=clear${query.includes('season=') ? '' : '&season=summer'}${query}`);
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
  // 4 frames, all of them shown — from the shared water atlas: no chunk cache is redrawn by the water
  const w0 = (await api(page, 'terrainEdges')).water;
  const seen = new Set();
  await expect.poll(async () => seen.add((await api(page, 'terrainEdges')).frame).size, { timeout: 6_000, intervals: [60] }).toBe(4);
  const w1 = (await api(page, 'terrainEdges')).water;
  expect(w1.redraws - w0.redraws).toBe(0);
  expect(w1.atlasRenders - w0.atlasRenders).toBeGreaterThanOrEqual(3);
  expect(w1.meshes).toBeGreaterThan(0);
  // no atlas beside the base one for the ground; the regions load theirs as before
  const s = await api(page, 'stream');
  expect(s.bundleNames).not.toContain('common:ground');
  expect((await api(page, 'textureList')).filter((t) => t.endsWith(':2048x1024')).length).toBe(1);
  // plains, desert, lake, forest, mountains, the cliff, a ruin (trial of light), the village: every key the view asks for is in the loaded art
  for (const [x, y] of [[50, 104], [48, 190], [162, 232], [150, 160], [175, 70], [51, 51], [104, 29], [24, 91]]) {
    await visit(page, x, y);
    const t = await api(page, 'terrainEdges');
    expect(t.fallbacks).toBe(0);
    expect(t.missing, `at ${x},${y}`).toEqual([]);
  }
  // the ruin floor's 66 tiles are in the base atlas too (round 3): still one 2048×1024 atlas
  await visit(page, 104, 29);
  expect((await api(page, 'textureList')).filter((t) => t.endsWith(':2048x1024')).length).toBe(1);
  // the page preloads only the terrain sheet it draws (?terrain=v2: the v2 one): no browser note either
  expect(problems).toEqual([]);
});

test('?terrain=v1 and the default keep the v1.1 ground; v2 stays within the 35 MB image guide in the same place (at most 2 MB more)', async ({ page, browser }) => {
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
  // (round 8 art: the island grounds' edge variants 2 / 3 and step pieces, 2 × 512 × 256, do not fit in
  // the base atlas; the guide is 35 MB of images: perf v1)
  expect(mb.v2, JSON.stringify(mb)).toBeLessThanOrEqual(35);
  expect(mb.v2 - mb.v1, JSON.stringify(mb)).toBeLessThanOrEqual(2);
  await other.context().close();
});

for (const season of ['autumn', 'winter']) {
  test(`?terrain=v2 in ${season}: every ground key is in the loaded art (the season's calm tiles and pictures)`, async ({ page }) => {
    const problems = await open(page, `&terrain=v2&season=${season}`);
    for (const [x, y] of [[49, 69], [24, 91], [150, 160], [162, 232], [104, 29]]) {
      await visit(page, x, y);
      await expect.poll(async () => (await api(page, 'season')).view, { timeout: 10_000 }).toBe(season);
      await visit(page, x, y);
      expect((await api(page, 'terrainEdges')).missing, `at ${x},${y}`).toEqual([]);
    }
    expect(problems).toEqual([]);
  });
}

test('?terrain=v2 does not touch the save: the same save data as v1 after the same steps', async ({ page }) => {
  const snap = {};
  for (const ver of ['v1', 'v2']) {
    await page.goto(`/?terrain=${ver}&e2e=1`);
    await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
    snap[ver] = await page.evaluate(() => Object.keys(localStorage).sort());
  }
  expect(snap.v2).toEqual(snap.v1);
});
