import { test, expect } from '@playwright/test';

// Graphics v3 (docs/art-release-v3/STYLE.md, ?v3=1): the v3 art at density 4 and the narrow integer view
// (about 20×9 tiles on an iPhone 15 Pro, 21×12 on an SE), with the rest of the art blown up 2×2. The
// default and ?v3=0 are the game as before. In v3: enemies attack only on screen, the arena camera keeps
// the hero and the boss in sight, the UI covers neither the hero nor the enemies, taps are ≥ 44 px and
// text ≥ 12 px, the memory measures are in (no CPU-side copies, no 16 MB chunk caches), nothing is saved.

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);

const PRO = { name: '15 Pro', width: 852, height: 393, dpr: 3, scale: 8, k: 2, canvas: [1278, 590], tiles: [20.0, 9.2] };
const SE = { name: 'SE', width: 667, height: 375, dpr: 2, scale: 4, k: 1, canvas: [1334, 750], tiles: [20.8, 11.7] };

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

/** Visible UI text under 12 px and visible buttons under 44 px (CSS px). */
const tooSmall = (page) =>
  page.evaluate(() => {
    const out = [];
    for (const el of document.querySelectorAll('#ui *')) {
      if (el.closest('[hidden]') || el.closest('#debug-panel') || el.id === 'debug-toggle') continue;
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden' || Number(cs.opacity) === 0) continue;
      const r = el.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) continue;
      const ownText = [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
      if (ownText && parseFloat(cs.fontSize) < 12) out.push(`text ${el.id || el.className} ${cs.fontSize}`);
      if (el.tagName === 'BUTTON' && (r.width < 43.99 || r.height < 43.99)) out.push(`button ${el.id || el.className} ${Math.round(r.width)}x${Math.round(r.height)}`);
    }
    return out;
  });

async function open(browser, screen, query, { keepEnemies = false } = {}) {
  const context = await browser.newContext({ viewport: { width: screen.width, height: screen.height }, deviceScaleFactor: screen.dpr, isMobile: true, hasTouch: true });
  const page = await context.newPage();
  const errors = [];
  const requests = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('request', (r) => requests.push(r.url()));
  await page.goto(`/?map=world&time=10&season=summer&weather=clear${query}`);
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 30_000 });
  const bosses = await api(page, 'bosses');
  if (!keepEnemies) await api(page, 'clearEnemies');
  return { context, page, errors, requests, bosses };
}

test('default and ?v3=0: the game as before (no v3 art fetched, density 2, fit)', async ({ browser }) => {
  for (const q of ['', '&v3=0']) {
    const { context, page, errors, requests } = await open(browser, PRO, q);
    const res = await api(page, 'resolution');
    expect(res).toMatchObject({ mode: 'fit', scale: 5, canvasScale: 2.5, width: 1024, height: 472 });
    const v3 = await api(page, 'v3');
    expect(v3.on).toBe(false);
    expect(v3.groups).toEqual([]);
    expect(v3.viewRect).toBe(null);
    expect((await api(page, 'art')).density).toBe(2);
    expect(await api(page, 'textureDensity', 'hero.idle.down.0')).toBe(2);
    expect(requests.filter((u) => u.includes('release-v3-'))).toEqual([]);
    expect(errors).toEqual([]);
    await context.close();
  }
});

for (const screen of [PRO, SE]) {
  test(`?v3=1 ${screen.name}: density 4, the narrow integer view, v3 art and fallbacks, nothing under the UI`, async ({ browser }, testInfo) => {
    const { context, page, errors } = await open(browser, screen, '&v3=1');
    const res = await api(page, 'resolution');
    expect(res.mode).toBe('int');
    expect(res.scale).toBe(screen.scale);
    expect(res.canvasScale).toBe(screen.k);
    expect([res.width, res.height]).toEqual(screen.canvas);
    expect(Math.abs(res.tilesX - screen.tiles[0])).toBeLessThan(0.1);
    expect(Math.abs(res.tilesY - screen.tiles[1])).toBeLessThan(0.1);
    // the canvas covers the viewport on whole device pixels
    const rect = await page.locator('#game-canvas').evaluate((el) => {
      const r = el.getBoundingClientRect();
      return { x: r.x, y: r.y, width: r.width, height: r.height };
    });
    // (Chromium lays boxes out in 1/64 CSS px: 393.33 px reads back as 393.328)
    for (const v of [rect.x, rect.y, rect.width, rect.height]) expect(Math.abs(v * screen.dpr - Math.round(v * screen.dpr))).toBeLessThan((screen.dpr / 64) * 1.01);
    expect(rect.x + rect.width).toBeGreaterThanOrEqual(screen.width - 0.001);
    expect(rect.y + rect.height).toBeGreaterThanOrEqual(screen.height - 0.001);
    const cam = await api(page, 'camera');
    for (const v of [cam.origin.x * cam.zoom, cam.origin.y * cam.zoom]) expect(Math.abs(v - Math.round(v))).toBeLessThan(1e-6);

    // v3 art where it is (the hero standing, the slime, the village woman), density 2 blown up 2×2
    // elsewhere (e.g. his walk to the right)
    const v3 = await api(page, 'v3');
    expect(v3.on).toBe(true);
    expect(v3.groups).toEqual(expect.arrayContaining(['v3/hero', 'v3/npc', 'v3/enemy', 'v3/terrain', 'v3/objects']));
    expect(await api(page, 'textureDensity', 'hero.idle.down.0')).toBe(4);
    expect(await api(page, 'textureDensity', 'enemy.slime.idle.0')).toBe(4);
    expect(await api(page, 'textureDensity', 'npc.woman.idle.down.0')).toBe(4);
    expect(await api(page, 'textureDensity', 'hero.walk.right.0')).toBe(2);
    expect(v3.hero.density).toBe(4);
    // memory: no CPU-side copies kept, no chunk caches
    expect(v3.cpu.total).toBe(0);
    expect(v3.gpu.render).toBeLessThan(1 << 20);

    // the plains: v3 ground, trees and props (the summer bundle), the stone house (the plains' bundle)
    await api(page, 'teleport', 28, 89);
    await page.waitForTimeout(1500);
    expect(await api(page, 'textureDensity', 'plains.grass.v3.a00')).toBe(4);
    expect(await api(page, 'textureDensity', 'plains.grassflow.v3.d1111.0')).toBe(4);
    expect(await api(page, 'textureDensity', 'plains.tree.v3.oak_l.0')).toBe(4);
    expect(await api(page, 'textureDensity', 'obj.v3.house_stone')).toBe(4);

    // hero and enemies around him are not under the HUD or the buttons; taps ≥ 44 px, text ≥ 12 px
    const p = await api(page, 'player');
    const tx = Math.floor(p.x / 16);
    const ty = Math.floor(p.y / 16);
    for (const [dx, dy] of [[4, 0], [-4, 0], [0, -2], [0, 2], [1, -3]]) await api(page, 'spawnEnemy', 'slime', tx + dx, ty + dy);
    await page.waitForTimeout(200);
    const ui = await uiBoxes(page);
    const boxes = await spritesCss(page);
    const blocked = [];
    for (const u of ui) {
      if (overlap(boxes.hero, u)) blocked.push(`hero/${u.id}`);
      for (const e of boxes.enemies) if (overlap(e, u)) blocked.push(`enemy${e.id}/${u.id}`);
    }
    expect(blocked).toEqual([]);
    expect(await tooSmall(page)).toEqual([]);
    // a message covers neither the hero nor an enemy (the one 3 tiles above him is where the top-centre
    // message would be: it goes to the low slot meanwhile)
    await api(page, 'pause');
    await api(page, 'resume');
    await api(page, 'showToast', '星の欠片を手に入れた');
    await expect(page.locator('#toast')).toBeVisible();
    await page.waitForTimeout(150);
    const now = await spritesCss(page);
    const toastBox = await page.locator('#toast').boundingBox();
    expect(overlap(now.hero, toastBox), 'toast / hero').toBe(false);
    for (const e of now.enemies) expect(overlap(e, toastBox), `toast / enemy ${e.id}`).toBe(false);
    await page.screenshot({ path: testInfo.outputPath('v3-village.png') });
    expect(errors).toEqual([]);
    await context.close();
  });

  test(`?v3=1 ${screen.name}: a conversation does not cover the hero or the villager`, async ({ browser }, testInfo) => {
    const { context, page, errors } = await open(browser, screen, '&v3=1');
    await api(page, 'standBy', 'woman');
    await page.waitForTimeout(800);
    await api(page, 'talkTo', 'woman');
    await expect(page.locator('#dialogue')).toBeVisible();
    await page.waitForTimeout(300);
    const box = await page.locator('#dialogue').boundingBox();
    const hero = (await spritesCss(page)).hero;
    expect(overlap(hero, box)).toBe(false);
    const npc = (await api(page, 'npcSprites')).find((n) => n.id === 'woman');
    expect(npc).toBeTruthy();
    expect(await tooSmall(page)).toEqual([]);
    await page.screenshot({ path: testInfo.outputPath('v3-talk.png') });
    expect(errors).toEqual([]);
    await context.close();
  });

  test(`?v3=1 ${screen.name}: boss fight — hero and boss on screen, clear of the boss bar, the toast and the buttons`, async ({ browser }, testInfo) => {
    const { context, page, errors, bosses } = await open(browser, screen, '&v3=1', { keepEnemies: true });
    const boss = bosses.find((b) => b.id === 'core_forest');
    await api(page, 'teleport', Math.floor(boss.x / 16), Math.floor(boss.y / 16) + 3);
    await expect(page.locator('#boss-bar')).toBeVisible();
    await page.waitForTimeout(400); // the camera frames the fight
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
    expect(bossBox).toBeTruthy();
    const mid = { x: bossBox.x + bossBox.width / 2, y: bossBox.y + bossBox.height / 2, width: 1, height: 1 };
    expect(mid.x).toBeGreaterThan(0);
    expect(mid.x).toBeLessThan(screen.width);
    expect(mid.y).toBeGreaterThan(0);
    expect(mid.y).toBeLessThan(screen.height);
    for (const u of ui) expect(overlap(mid, u), `boss middle / ${u.id}`).toBe(false);
    // the hero is wholly on screen
    expect(boxes.hero.y).toBeGreaterThanOrEqual(0);
    expect(boxes.hero.y + boxes.hero.height).toBeLessThanOrEqual(screen.height);
    expect(await tooSmall(page)).toEqual([]);
    await page.screenshot({ path: testInfo.outputPath('v3-boss.png') });
    expect(errors).toEqual([]);
    await context.close();
  });
}

test('?v3=1: an archer off screen does not aim; with ?v3=0 the same archer does', async ({ browser }) => {
  for (const [q, shoots] of [['&v3=1', false], ['&v3=0', true]]) {
    const { context, page, errors } = await open(browser, PRO, q);
    await api(page, 'teleport', 52, 100);
    await page.waitForTimeout(800);
    const p = await api(page, 'player');
    // 7 tiles (112 px) north: in its sight (140), off the v3 view (147 px tall), on the old one (236)
    await api(page, 'spawnEnemy', 'archer', Math.floor(p.x / 16), Math.floor(p.y / 16) - 7);
    // watch it for 3.5 s: does it ever draw its bow (wind up) or have a shot out?
    let aimed = false;
    for (let i = 0; i < 35; i++) {
      await page.waitForTimeout(100);
      const archer = (await api(page, 'enemies')).find((e) => e.kind === 'archer');
      const shots = (await api(page, 'projectiles')).filter((x) => x.owner === 'enemy').length;
      if (archer?.state === 'windup' || shots > 0) aimed = true;
    }
    expect(aimed, q).toBe(shoots);
    if (!shoots) expect((await api(page, 'v3')).viewRect).not.toBe(null);
    expect(errors).toEqual([]);
    await context.close();
  }
});

test('?v3=1: facing left mirrors the right frame where they are the same; the warning flash works without CPU copies', async ({ browser }) => {
  const { context, page, errors } = await open(browser, PRO, '&v3=1');
  await api(page, 'teleport', 52, 100);
  await api(page, 'face', 'left');
  await page.waitForTimeout(300);
  const v = await api(page, 'v3');
  expect(v.hero.key).toMatch(/^hero\.idle\.left\.\d$/);
  expect(v.hero.mirrored).toBe(true);
  await api(page, 'face', 'down');
  await page.waitForTimeout(200);
  expect((await api(page, 'v3')).hero.mirrored).toBe(false);
  // a slime next to him winds up: its red warning overlay is made on the GPU
  const p = await api(page, 'player');
  await api(page, 'spawnEnemy', 'slime', Math.floor(p.x / 16) + 1, Math.floor(p.y / 16));
  let flashed = false;
  for (let i = 0; i < 40 && !flashed; i++) {
    await page.waitForTimeout(100);
    flashed = (await api(page, 'enemyView')).some((e) => e.flash > 0);
  }
  expect(flashed).toBe(true);
  expect(errors).toEqual([]);
  await context.close();
});

test('?v3=1 saves nothing of its own: settings and the save are as with ?v3=0', async ({ browser }) => {
  const saved = {};
  for (const q of ['&v3=0', '&v3=1']) {
    const { context, page } = await open(browser, PRO, q);
    await api(page, 'teleport', 52, 100);
    await page.waitForTimeout(500);
    const settings = await api(page, 'settings');
    expect(JSON.stringify(settings)).not.toMatch(/v3|viewRect/);
    await api(page, 'saveNow');
    const entries = await page.evaluate(() => Object.keys(localStorage).sort().map((k) => [k, localStorage.getItem(k)]));
    for (const [, val] of entries) expect(val ?? '').not.toMatch(/viewRect|"v3"/);
    saved[q] = entries.map(([k]) => k);
    await context.close();
  }
  expect(saved['&v3=1']).toEqual(saved['&v3=0']);
});

test('?v3=1: the plains in summer, autumn and winter — each season\'s own v3 bundle, its trees and props, swaying; memory under 35 MB', async ({ browser }) => {
  for (const season of ['summer', 'autumn', 'winter']) {
    const { context, page, errors } = await open(browser, SE, `&v3=1`);
    await api(page, 'setSeason', season);
    await api(page, 'teleport', 52, 100);
    await page.waitForTimeout(2500);
    const pre = season === 'summer' ? '' : `${season}.`;
    const names = (await api(page, 'stream')).bundleNames;
    expect(names).toContain(`v3:plains:${season}`);
    expect(names.filter((n) => n.startsWith('v3:plains:'))).toEqual([`v3:plains:${season}`]);
    expect(await api(page, 'textureDensity', `${pre}plains.grass.v3.a00`)).toBe(4);
    const a = (await api(page, 'v3')).plains;
    expect(a.season === season || (season === 'summer' && a.season === null)).toBe(true);
    expect(Object.keys(a.trees).length).toBeGreaterThanOrEqual(3);
    expect(Object.values(a.props).reduce((x, y) => x + y, 0)).toBeGreaterThan(20);
    expect(a.foot).toBeGreaterThan(5);
    // the sway moves on (trees: not in winter's bare broadleaves, but the pines; grass and flowers 2 frames)
    await page.waitForTimeout(1600);
    const b = (await api(page, 'v3')).plains;
    expect(JSON.stringify(b.frames)).not.toBe(JSON.stringify(a.frames));
    const mem = await api(page, 'v3');
    expect(mem.gpu.total).toBeLessThan(35 * 2 ** 20);
    expect(mem.cpu.total).toBe(0);
    expect(errors).toEqual([]);
    await context.close();
  }
});

test('?v3=1: changing the season near the plains loads the next season\'s v3 art first and lets the old one go', async ({ browser }) => {
  const { context, page, errors } = await open(browser, PRO, '&v3=1');
  await api(page, 'teleport', 52, 100);
  await page.waitForTimeout(2000);
  expect((await api(page, 'stream')).bundleNames).toContain('v3:plains:summer');
  await api(page, 'setSeason', 'autumn');
  await expect.poll(async () => (await api(page, 'season')).view, { timeout: 15_000 }).toBe('autumn');
  await page.waitForTimeout(1000);
  const names = (await api(page, 'stream')).bundleNames;
  expect(names).toContain('v3:plains:autumn');
  expect(names).not.toContain('v3:plains:summer');
  expect(await api(page, 'textureDensity', 'autumn.plains.tree.v3.oak_l.0')).toBe(4);
  expect(errors).toEqual([]);
  await context.close();
});
