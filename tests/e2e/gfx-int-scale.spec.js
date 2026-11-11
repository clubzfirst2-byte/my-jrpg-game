import { test, expect } from '@playwright/test';

// ?scale=int (render_audit.md 案1, approved 2026-11-11): every canvas (art) pixel is a whole number of
// device pixels, the canvas sits on the device pixel grid and covers the screen (no border), the
// default stays ?scale=fit, and the hero, enemies, the toast and the boss bar are not hidden under
// the HUD or the buttons on any of the target screens.

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);

const SCREENS = [
  { name: '15 Pro landscape', width: 852, height: 393, dpr: 3, scale: 6 },
  { name: '15 Pro portrait', width: 393, height: 852, dpr: 3, scale: 6 },
  { name: 'SE landscape', width: 667, height: 375, dpr: 2, scale: 4 },
  { name: 'SE portrait', width: 375, height: 667, dpr: 2, scale: 4 },
  { name: 'Pro Max landscape', width: 932, height: 430, dpr: 3, scale: 6 },
  { name: 'Pro Max portrait', width: 430, height: 932, dpr: 3, scale: 6 },
  { name: 'iPad landscape', width: 1180, height: 820, dpr: 2, scale: 8 },
];

const overlap = (a, b) => a.x < b.x + b.width && b.x < a.x + a.width && a.y < b.y + b.height && b.y < a.y + a.height;

/** UI boxes that cover the game: the HUD and every visible button (CSS px). */
const uiBoxes = (page) =>
  page.evaluate(() => {
    const out = [];
    for (const el of document.querySelectorAll('#ui button, #hud-hearts, #hud-clock, #hud-treasure, #stamina, #ability-hud')) {
      if (el.closest('[hidden]') || el.closest('#debug-panel') || el.id === 'debug-toggle') continue;
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden' || Number(cs.opacity) === 0) continue;
      const r = el.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) continue;
      out.push({ id: el.id || el.className, x: r.x, y: r.y, width: r.width, height: r.height });
    }
    return out;
  });

/** Sprite bounds (canvas px) → CSS px on the page. */
const spritesCss = (page) =>
  page.evaluate(() => {
    const c = document.getElementById('game-canvas').getBoundingClientRect();
    const res = window.__debugApi.resolution();
    const k = res.canvasScale / window.devicePixelRatio;
    const t = (b) => ({ ...b, x: c.x + b.x * k, y: c.y + b.y * k, width: b.width * k, height: b.height * k });
    const s = window.__debugApi.spriteBounds();
    return { hero: t(s.hero), enemies: s.enemies.map(t) };
  });

async function open(browser, screen, query, { keepEnemies = false } = {}) {
  const context = await browser.newContext({
    viewport: { width: screen.width, height: screen.height },
    deviceScaleFactor: screen.dpr,
    isMobile: true,
    hasTouch: true,
  });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto(`/?map=world&time=10&season=summer&weather=clear${query}`);
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 30_000 });
  if (!keepEnemies) await api(page, 'clearEnemies');
  return { context, page, errors };
}

test('default is fit (unchanged), ?scale=fit is the same', async ({ browser }) => {
  for (const q of ['', '&scale=fit', '&scale=bogus']) {
    const { context, page, errors } = await open(browser, SCREENS[0], q);
    const res = await api(page, 'resolution');
    expect(res.mode).toBe('fit');
    expect(res).toMatchObject({ scale: 5, canvasScale: 2.5, width: 1024, height: 472 });
    await expect(page.locator('#game-canvas')).toHaveAttribute('data-scale', 'fit');
    expect(await page.locator('#game-canvas').evaluate((el) => el.style.transform)).toBe('');
    expect(errors).toEqual([]);
    await context.close();
  }
});

for (const screen of SCREENS) {
  test(`?scale=int ${screen.name} ${screen.width}×${screen.height}@${screen.dpr}: whole pixels, no border, nothing under the UI`, async ({ browser }, testInfo) => {
    const { context, page, errors } = await open(browser, screen, '&scale=int');
    const res = await api(page, 'resolution');
    expect(res.mode).toBe('int');
    expect(res.scale).toBe(screen.scale);
    expect(Number.isInteger(res.canvasScale)).toBe(true);
    await expect(page.locator('#game-canvas')).toHaveAttribute('data-scale', 'int');

    // The canvas covers the viewport, on whole device pixels, one canvas px = canvasScale device px.
    const rect = await page.locator('#game-canvas').evaluate((el) => {
      const r = el.getBoundingClientRect();
      return { x: r.x, y: r.y, width: r.width, height: r.height, cw: el.width, ch: el.height };
    });
    const d = screen.dpr;
    expect(Math.abs(rect.x * d - Math.round(rect.x * d))).toBeLessThan(0.01);
    expect(Math.abs(rect.y * d - Math.round(rect.y * d))).toBeLessThan(0.01);
    expect(rect.width * d).toBeCloseTo(rect.cw * res.canvasScale, 3);
    expect(rect.height * d).toBeCloseTo(rect.ch * res.canvasScale, 3);
    expect(rect.x).toBeLessThanOrEqual(0.001);
    expect(rect.y).toBeLessThanOrEqual(0.001);
    expect(rect.x + rect.width).toBeGreaterThanOrEqual(screen.width - 0.001);
    expect(rect.y + rect.height).toBeGreaterThanOrEqual(screen.height - 0.001);

    // The camera origin is on whole canvas pixels.
    const cam = await api(page, 'camera');
    for (const v of [cam.origin.x * cam.zoom, cam.origin.y * cam.zoom]) expect(Math.abs(v - Math.round(v))).toBeLessThan(1e-6);

    // Hero and nearby enemies (open ground by the start beach, left / right / above / below) are not
    // under the HUD or a button. The rotate hint covers everything in portrait: the game is played
    // in landscape, so in portrait only the canvas checks above apply.
    const portrait = screen.height > screen.width;
    const ui = await uiBoxes(page);
    const p = await api(page, 'player');
    const tx = Math.floor(p.x / 16);
    const ty = Math.floor(p.y / 16);
    for (const [dx, dy] of [[4, 0], [-4, 0], [0, -3], [0, 3]]) await api(page, 'spawnEnemy', 'beast', tx + dx, ty + dy);
    const boxes = await spritesCss(page);
    const blocked = [];
    if (!portrait) {
      for (const u of ui) {
        if (overlap(boxes.hero, u)) blocked.push(`hero/${u.id}`);
        for (const e of boxes.enemies) if (overlap(e, u)) blocked.push(`enemy${e.id}/${u.id}`);
      }
    }
    testInfo.annotations.push({ type: 'boxes', description: JSON.stringify({ res: { scale: res.scale, w: res.width, h: res.height }, hero: boxes.hero, enemies: boxes.enemies.length }) });
    expect(blocked).toEqual([]);
    expect(errors).toEqual([]);
    await page.screenshot({ path: testInfo.outputPath('int.png') });
    await context.close();
  });
}

for (const screen of SCREENS.filter((s) => s.width > s.height)) {
  test(`?scale=int ${screen.name}: boss fight — boss bar and toast clear of the buttons, hero and boss visible`, async ({ browser }, testInfo) => {
    const { context, page, errors } = await open(browser, screen, '&scale=int', { keepEnemies: true });
    const boss = (await api(page, 'bosses')).find((b) => b.id === 'core_forest');
    await api(page, 'teleport', Math.floor(boss.x / 16), Math.floor(boss.y / 16) + 4);
    await expect(page.locator('#boss-bar')).toBeVisible();
    await api(page, 'showToast', '星の欠片を手に入れた');
    await expect(page.locator('#toast')).toBeVisible();
    const ui = await uiBoxes(page);
    const bar = await page.locator('#boss-bar').boundingBox();
    const toastBox = await page.locator('#toast').boundingBox();
    const boxes = await spritesCss(page);
    const bossBox = boxes.enemies.find((e) => e.boss);
    const blocked = [];
    for (const u of ui) {
      if (overlap(bar, u)) blocked.push(`bossbar/${u.id}`);
      if (overlap(toastBox, u)) blocked.push(`toast/${u.id}`);
      if (overlap(boxes.hero, u)) blocked.push(`hero/${u.id}`);
    }
    if (overlap(boxes.hero, bar)) blocked.push('hero/bossbar');
    if (overlap(boxes.hero, toastBox)) blocked.push('hero/toast');
    expect(blocked).toEqual([]);
    // the boss is on screen (its middle is inside the viewport and not under a button)
    expect(bossBox).toBeTruthy();
    const mid = { x: bossBox.x + bossBox.width / 2, y: bossBox.y + bossBox.height / 2, width: 1, height: 1 };
    expect(mid.x).toBeGreaterThan(0);
    expect(mid.x).toBeLessThan(screen.width);
    expect(mid.y).toBeGreaterThan(0);
    expect(mid.y).toBeLessThan(screen.height);
    for (const u of ui) expect(overlap(mid, u), `boss middle / ${u.id}`).toBe(false);
    await page.screenshot({ path: testInfo.outputPath('boss-int.png') });
    expect(errors).toEqual([]);
    await context.close();
  });
}

test('?scale=int saves nothing: settings and the save are the same as with fit', async ({ browser }) => {
  const { context, page } = await open(browser, SCREENS[0], '&scale=int');
  const settings = await api(page, 'settings');
  expect(JSON.stringify(settings)).not.toContain('int');
  await api(page, 'saveNow');
  const keys = await page.evaluate(() => Object.keys(localStorage).map((k) => [k, localStorage.getItem(k)]));
  for (const [, v] of keys) expect(v ?? '').not.toMatch(/"scale"|scaleMode/);
  await context.close();
});
