import { test, expect } from '@playwright/test';

// P10.3: the remaining regions (白嶺山脈, 囁きの森, 鏡湖と群島) in a second column, joined by passes.
// Completion check (DESIGN.md roadmap): chunk streaming and memory measured across every region.

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);

async function open(page) {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/?map=world&time=10&season=summer');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await api(page, 'clearEnemies');
  return errors;
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
  return api(page, 'stream');
}

const WEST = ['island', 'plains', 'desert'];
const EAST = ['mountains', 'forest', 'lake'];
const STOPS = [
  ['island', 48, 60],
  ['plains', 50, 100],
  ['desert', 48, 190],
  ['lake', 128 + 34, 232],
  ['forest', 128 + 30, 148],
  ['mountains', 128 + 47, 70],
];

test('every region: its own art only, and touring all of them again and again does not pile up memory', async ({ page }) => {
  test.setTimeout(120_000);
  const errors = await open(page);
  const laps = [];
  for (let lap = 0; lap < 4; lap++) {
    for (const [name, tx, ty] of STOPS) {
      const s = await visit(page, tx, ty);
      expect(s.region, name).toBe(name === 'island' ? 'island' : name);
      // Its own art is loaded there, and never the other column's: columns never share a chunk.
      const loaded = s.bundleNames.filter((b) => b.startsWith('region:'));
      if (name !== 'island') expect(loaded, name).toContain(`region:${name}`);
      const other = EAST.includes(name) ? WEST : EAST;
      expect(loaded.filter((b) => other.includes(b.slice(7))), name).toEqual([]);
      expect(s.chunks).toBeLessThanOrEqual(9);
    }
    laps.push(await api(page, 'stream'));
  }
  expect(laps[3].built).toBeGreaterThan(laps[0].built);
  expect(laps[3].textures).toBeLessThanOrEqual(laps[1].textures + 1);
  expect(laps[3].displayObjects).toBeLessThanOrEqual(laps[1].displayObjects * 1.1);
  expect(laps[3].bundles).toBe(laps[1].bundles);
  expect(errors).toEqual([]);
});

test('walking east over the pass from the plains into the forest (the camera follows into the east column)', async ({ page }, testInfo) => {
  const errors = await open(page);
  await visit(page, 90, 72 + 53);
  await page.keyboard.down('ArrowRight');
  try {
    await expect.poll(async () => (await api(page, 'stream')).region, { timeout: 6000 }).toBe('forest');
  } finally {
    await page.keyboard.up('ArrowRight');
  }
  const cam = await api(page, 'camera');
  expect(cam.bounds.x).toBe(128 * 16); // the east column's outdoors
  await expect(page.locator('#hud-clock')).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath('forest.png') });
  // And back west.
  await page.keyboard.down('ArrowLeft');
  try {
    await expect.poll(async () => (await api(page, 'stream')).region, { timeout: 6000 }).toBe('plains');
  } finally {
    await page.keyboard.up('ArrowLeft');
  }
  expect((await api(page, 'camera')).bounds.x).toBe(0);
  expect(errors).toEqual([]);
});
