import { test, expect } from '@playwright/test';

// v1.0: the terrain release art (src/art-release/terrain, src/view/assets/terrainArt.js) in normal
// play: the base bundle's ground, cliffs and nature objects, each region's own ground and trees, and
// each season's look are drawn from it (2 pixels per game pixel), with no console warning;
// ?terrain=placeholder keeps the placeholder terrain for comparison.

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);

async function open(page, query = '') {
  const problems = [];
  page.on('pageerror', (e) => problems.push(`pageerror: ${e.message}`));
  page.on('console', (m) => {
    if (m.type() === 'warning' || m.type() === 'error' || m.text().startsWith('art:')) problems.push(`${m.type()}: ${m.text()}`);
  });
  await page.goto(`/?map=world&time=10${query}`);
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await api(page, 'clearEnemies');
  return problems;
}

/** Teleports and waits until the view has really updated there with every wanted chunk built. */
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

const STOPS = [
  ['plains', 50, 100, 'plains.grass.0'],
  ['desert', 48, 190, 'tile.shore-desert.1.0'],
  ['lake', 128 + 34, 232, 'lake.grass.0'],
  ['forest', 128 + 30, 148, 'forest.pine'],
  ['mountains', 128 + 47, 70, 'face.stone.mid.4.v1'],
];

test('normal play draws the terrain from its release art: base, every region, no warnings', async ({ page }, testInfo) => {
  test.setTimeout(90_000);
  const problems = await open(page, '&season=summer');
  const t = await api(page, 'terrainArt');
  expect(t.placeholder).toEqual([]);
  for (const key of ['tile.grass.0', 'tile.path', 'tile.sand', 'tile.water.0', 'tile.water.1', 'tile.ruin', 'tile.wood', 'tile.walltop', 'tile.dark', 'tile.pit', 'tile.vine', 'tile.ramp', 'face.earth.top.8', 'face.ruin.mid-base.4', 'face.wall.top.8', 'obj.tree', 'obj.rock', 'obj.bramble', 'obj.stump', 'tile.shore.5.0', 'tile.bank.inner.ne.1', 'face.earth.mid.8.v2', 'face.sand.top.8', 'face.path.mid-base.4']) {
    expect(t.release, key).toContain(key);
  }
  expect(await api(page, 'artUrl', 'tile.grass.0')).not.toBeNull();
  await page.screenshot({ path: testInfo.outputPath('island.png') });
  for (const [region, tx, ty, key] of STOPS) {
    await visit(page, tx, ty);
    const r = await api(page, 'terrainArt');
    expect(r.bundles, region).toContain(`region:${region}`);
    expect(r.release, region).toContain(key);
    expect(r.placeholder, region).toEqual([]);
    await page.screenshot({ path: testInfo.outputPath(`${region}.png`) });
  }
  expect(problems).toEqual([]);
});

test('v1.1 water edges: shore tiles and grass banks along the island beach, following the water frames', async ({ page }) => {
  const problems = await open(page, '&season=summer');
  await visit(page, 26, 62);
  const a = await api(page, 'terrainEdges');
  expect(a.count).toBeGreaterThan(20);
  expect(a.keys.some((k) => k.startsWith('tile.shore.'))).toBe(true);
  expect(a.keys.some((k) => k.startsWith('tile.bank.'))).toBe(true);
  // the pieces switch with the water's 2 frames (0.6 s each)
  await expect.poll(async () => (await api(page, 'terrainEdges')).frame, { timeout: 5_000 }).not.toBe(a.frame);
  // the placeholder terrain has no edge pieces
  const p = await page.context().newPage();
  await open(p, '&season=summer&terrain=placeholder');
  await visit(p, 26, 62);
  expect((await api(p, 'terrainEdges')).count).toBe(0);
  expect(problems).toEqual([]);
});

test('each season brings its own terrain art (spring tree, autumn and winter ground, lips, trees)', async ({ page }) => {
  for (const [season, key] of [['spring', 'spring.obj.tree'], ['autumn', 'autumn.tile.grass.0'], ['winter', 'winter.face.earth.top.8'], ['autumn', 'autumn.forest.grass.0'], ['autumn', 'autumn.face.stone.top.8.v1'], ['autumn', 'autumn.mountains.pine'], ['winter', 'winter.face.earth.top-base.4.v2']]) {
    const p = await page.context().newPage();
    const problems = await open(p, `&season=${season}`);
    await expect.poll(async () => (await api(p, 'terrainArt')).bundles, { timeout: 10_000 }).toContain(`season:${season}`);
    const t = await api(p, 'terrainArt');
    expect(t.release, season).toContain(key);
    expect(t.placeholder, season).toEqual([]);
    expect(problems, season).toEqual([]);
    await p.close();
  }
});

test('?terrain=placeholder keeps the placeholder terrain beside the release hero', async ({ page }) => {
  await open(page, '&season=summer');
  const withArt = (await api(page, 'art')).overrides;
  const p = await page.context().newPage();
  await open(p, '&season=summer&terrain=placeholder');
  const art = await api(p, 'art');
  expect(art).toMatchObject({ density: 2, hero: { w: 16, h: 28 } });
  expect(art.overrides).toBe(withArt - 351);
  const t = await api(p, 'terrainArt');
  expect(t.release).toEqual([]);
  expect(t.placeholder).toContain('tile.grass.0');
});
