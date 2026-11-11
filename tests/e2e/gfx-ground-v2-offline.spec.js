import { test, expect } from '@playwright/test';

// gfx W1: the ground v2 is drawn by default (artV2.js V2_ENABLED). With no network, the service worker
// must still have it — the default shows the v2 ground from its release art, not the placeholder —
// and it must still have the v1 terrain, so ?terrain=v1 and ?v2=0 show the v1 ground offline too
// (tools/precache.mjs, as fx-v2 did for the enemies).

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);

async function ready(page) {
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
}

test('offline: the default draws the v2 ground; ?terrain=v1 and ?v2=0 the v1 ground — all from the kept release art', async ({ page, context, browserName }) => {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/?map=world&sw=1&time=10&season=summer&weather=clear');
  await ready(page);
  test.skip(!(await page.evaluate(() => 'serviceWorker' in navigator && window.isSecureContext)), 'no service workers in this browser build');
  // (Playwright's WebKit cannot navigate offline through a service worker: see p11-pwa.spec.js)
  test.skip(browserName !== 'chromium', 'offline navigation is driven in Chromium');
  await page.evaluate(() => navigator.serviceWorker.ready);
  await page.reload();
  await ready(page);
  await expect.poll(() => page.evaluate(() => !!navigator.serviceWorker.controller)).toBe(true);
  // both terrain sheets are kept
  const kept = await page.evaluate(async () => {
    const text = await (await fetch('sw.js')).text();
    const files = JSON.parse(/const FILES = (\[.*?\]);/.exec(text)[1]);
    const terrain = files.filter((f) => /release-(?:v2-)?terrain-/.test(f));
    const missing = [];
    for (const f of terrain) if (!(await caches.match(new URL(f, location.href).href, { ignoreSearch: true, ignoreVary: true }))) missing.push(f);
    return { terrain, missing };
  });
  expect(kept.terrain.filter((f) => /release-terrain-/.test(f)).length).toBe(2); // the v1 sheet and table
  expect(kept.terrain.filter((f) => /release-v2-terrain-/.test(f)).length).toBe(2); // the v2 sheet and table
  expect(kept.missing).toEqual([]);

  await context.setOffline(true);
  try {
    for (const [q, v2] of [['', true], ['&terrain=v1', false], ['&v2=0', false], ['&terrain=v2', true]]) {
      await page.goto(`/?map=world&time=10&season=summer&weather=clear${q}`);
      await ready(page);
      await expect.poll(async () => (await api(page, 'stream')).pending, { timeout: 10_000 }).toBe(0);
      expect((await api(page, 'terrainEdges')).groundV2, q || 'default').toBe(v2);
      const art = await api(page, 'terrainArt');
      // the ground is drawn from the release art (2 px per game px), not the placeholder
      expect(art.release, q || 'default').toEqual(expect.arrayContaining(['tile.grass.0', 'tile.sand']));
      expect(art.placeholder.filter((k) => k.startsWith('tile.')), q || 'default').toEqual([]);
      // the v2 ground's own keys only with the v2 terrain
      expect(art.release.includes('tile.water.3'), q || 'default').toBe(v2);
      expect((await api(page, 'terrainEdges')).missing, q || 'default').toEqual([]);
    }
  } finally {
    await context.setOffline(false);
  }
  expect(errors).toEqual([]);
});
