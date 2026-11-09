import { test, expect } from '@playwright/test';
import { waitTicks, ticksOf } from './ticks.js';

// P11.1: the game as an app — installable (manifest, icons), playable with no network (service
// worker), and the start time is measured and reported.

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);

test('manifest and icons for the home screen', async ({ page, request }) => {
  await page.goto('/');
  const href = await page.locator('link[rel="manifest"]').getAttribute('href');
  const m = await (await request.get(new URL(href, page.url()).href)).json();
  expect(m.name).toBe('星環のレガリア');
  expect(m.short_name).toBe('星環のレガリア');
  expect(m.display).toBe('fullscreen');
  expect(m.orientation).toBe('landscape');
  expect(m.start_url).toBe('./');
  for (const icon of m.icons) {
    const r = await request.get(new URL(icon.src, page.url()).href);
    expect(r.status(), icon.src).toBe(200);
    expect(r.headers()['content-type']).toContain('image/png');
    const [w, h] = icon.sizes.split('x').map(Number);
    const body = await r.body();
    expect(body.readUInt32BE(16)).toBe(w); // PNG width / height from IHDR
    expect(body.readUInt32BE(20)).toBe(h);
  }
  expect(m.icons.some((i) => i.purpose === 'maskable')).toBe(true);
  expect((await request.get(new URL('icons/apple-touch-icon.png', page.url()).href)).status()).toBe(200);
});

test('the service worker keeps every file of this version', async ({ page, request }) => {
  await page.goto('/');
  const sw = await (await request.get(new URL('sw.js', page.url()).href)).text();
  const script = await page.locator('script[type="module"]').getAttribute('src');
  expect(sw).toContain('index.html');
  expect(sw).toContain(script.replace(/^\.\//, ''));
  expect(sw).toMatch(/seimyaku-/);
});

test('with no network at all, the game still starts and plays', async ({ page, context, browserName }) => {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/?map=world&sw=1');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  // (A browser build without service workers cannot be tested for this; iPhone Safari has them.)
  test.skip(!(await page.evaluate(() => 'serviceWorker' in navigator && window.isSecureContext)), 'no service workers in this browser build');
  // Wait until the service worker has kept everything and controls the page.
  await page.evaluate(() => navigator.serviceWorker.ready);
  await page.reload();
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await expect.poll(() => page.evaluate(() => !!navigator.serviceWorker.controller)).toBe(true);
  // Every file the game needs is kept (what makes an offline start possible), in every browser.
  const missing = await page.evaluate(async () => {
    const text = await (await fetch('sw.js')).text();
    const files = JSON.parse(/const FILES = (\[.*?\]);/.exec(text)[1]);
    const out = [];
    for (const f of files) if (!(await caches.match(new URL(f, location.href).href, { ignoreSearch: true, ignoreVary: true }))) out.push(f);
    return out;
  });
  expect(missing).toEqual([]);
  // Starting with the network off: Playwright's WebKit cannot navigate offline through a service
  // worker (it reports an internal error), so the start itself is driven in Chromium here and
  // checked on the iPhone (docs/device-tests, P11.1).
  if (browserName !== 'chromium') {
    expect(errors).toEqual([]);
    return;
  }
  await context.setOffline(true);
  try {
    await page.reload();
    await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
    const t0 = (await api(page, 'player')).x;
    await page.keyboard.down('ArrowRight');
    await waitTicks(page, ticksOf(400));
    await page.keyboard.up('ArrowRight');
    expect((await api(page, 'player')).x).toBeGreaterThan(t0);
    expect((await api(page, 'loadTiming')).fromCache).toBe(true);
  } finally {
    await context.setOffline(false);
  }
  expect(errors).toEqual([]);
});

test('the start time is measured and goes into the report', async ({ page }) => {
  await page.goto('/?map=world&debug=1&reportSec=2');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  const t = await api(page, 'loadTiming');
  expect(t.readyMs).toBeGreaterThan(0);
  expect(t.readyMs).toBeLessThan(20_000);
  expect(t.scriptsMs).toBeLessThanOrEqual(t.readyMs);
});
