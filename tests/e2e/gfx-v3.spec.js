import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { decodePng } from '../../tools/release-art-pack.mjs';

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

    // v3 art where it is (the hero, the slime, the village woman), density 2 blown up 2×2 elsewhere
    // (e.g. the hero's approved climb, the stand-in until his v3 climb is loaded)
    const v3 = await api(page, 'v3');
    expect(v3.on).toBe(true);
    expect(v3.groups).toEqual(expect.arrayContaining(['v3/hero', 'v3/npc', 'v3/enemy', 'v3/terrain', 'v3/objects']));
    expect(await api(page, 'textureDensity', 'hero.idle.down.0')).toBe(4);
    // (the enemies' v3 frames: a bundle per kind, loaded with the regions where it spawns — the island: beasts, archers)
    await expect.poll(() => api(page, 'textureDensity', 'enemy.beast.idle.0')).toBe(4);
    expect(await api(page, 'textureDensity', 'npc.woman.idle.down.0')).toBe(4);
    expect(await api(page, 'textureDensity', 'hero.walk.right.0')).toBe(4);
    expect(await api(page, 'textureDensity', 'hero.climb.right.0')).toBe(null);
    expect(await api(page, 'textureDensity', 'v1.hero.climb.right.0')).toBe(2);
    expect(v3.hero.density).toBe(4);
    // memory: no CPU-side copies kept, no chunk caches
    expect(v3.cpu.total).toBe(0);
    // (the ground cache, a little larger than the screen: 15 Pro 3.5 MB, SE 4.5 MB; nothing else rendered to a texture over 1 MB)
    expect(v3.cache.bytes).toBeLessThan(4.6 * 2 ** 20);
    expect(v3.gpu.render - v3.cache.bytes).toBeLessThan(1 << 20);

    // the plains: v3 ground, trees and props (the summer bundle), the stone house (the plains' bundle)
    await api(page, 'teleport', 28, 89);
    await page.waitForTimeout(1500);
    expect(await api(page, 'textureDensity', 'plains.grass.v3.a00')).toBe(4);
    expect(await api(page, 'textureDensity', 'plains.grassflow.v3.1111.0')).toBe(4);
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
    expect(names.filter((n) => n.startsWith('v3:plains:')).sort()).toEqual(season === 'winter' ? ['v3:plains:winter'] : [`v3:plains:${season}`, 'v3:plains:flow'].sort());
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

// The art side's reference composes each plains ground tile (gen_ground_v3.ground_tile: the base, the flow
// shape mirrored when flip, times FLOW_TINT); tools/ground_v3_ref_fixture.py saved a meadow's tiles
// (tests/fixtures/ground_v3_tiles.<season>.png; 8 × 6 tiles, 47 with flow). On the SE (1 canvas px = 1 device px) with only the ground
// shown, every tile the engine draws from the same pieces must be those pixels, times the ground's level
// tint (levelTint(0): 242/255) — within 2 per channel for the rounding of two multiplications.
const TILES = JSON.parse(readFileSync(new URL('../fixtures/ground_v3_tiles.json', import.meta.url), 'utf8'));
for (const season of ['summer', 'autumn', 'winter']) {
  for (const cache of ['1', '0']) {
    test(`?v3=1 ${season}${cache === '0' ? ' (?v3cache=0)' : ''}: the plains ground is the reference's tiles, pixel for pixel`, async ({ browser }, testInfo) => {
      const { context, page, errors } = await open(browser, SE, `&v3=1&v3cache=${cache}`);
      await api(page, 'setSeason', season);
      await api(page, 'teleport', TILES.i0 + TILES.w / 2, TILES.j0 + TILES.h / 2);
      await page.waitForTimeout(2500);
      await expect.poll(async () => (await api(page, 'season')).view).toBe(season);
      await page.waitForTimeout(1000);
      const all = await api(page, 'layers', []);
      const keep = ['world', 'water', 'base', 'ground-cache'];
      await api(page, 'layers', all.filter((l) => !keep.includes(l)));
      await page.addStyleTag({ content: '#ui, #ui * { visibility: hidden !important }' });
      await page.waitForTimeout(400);
      const cam = await api(page, 'camera');
      const shot = decodePng(await page.screenshot());
      await testInfo.attach('ground', { body: await page.screenshot(), contentType: 'image/png' });
      const ref = decodePng(readFileSync(new URL(`../fixtures/ground_v3_tiles.${season}.png`, import.meta.url)));
      let compared = 0;
      let flows = 0;
      let worst = 0;
      for (let r = 0; r < TILES.h; r++) {
        for (let c = 0; c < TILES.w; c++) {
          const i = TILES.i0 + c;
          const j = TILES.j0 + r;
          const want = TILES.pieces[season][r][c];
          const got = (await api(page, 'groundAt', i, j)).map((p) => p.key + (p.tint !== null ? `${p.flip ? '~f' : ''}@#${p.tint.toString(16).padStart(6, '0')}` : '')).join('|');
          if (got !== want) continue; // (a tile next to other ground: its flow fades out, not the reference's tile)
          const x0 = Math.round((i * 16 + 8 - cam.origin.x) * 4);
          const y0 = Math.round((j * 16 + 8 - cam.origin.y) * 4);
          if (x0 < 0 || y0 < 0 || x0 + 64 > shot.width || y0 + 64 > shot.height) continue;
          for (let y = 0; y < 64; y++) {
            for (let x = 0; x < 64; x++) {
              const a = ((y0 + y) * shot.width + x0 + x) * 4;
              const b = ((r * 64 + y) * ref.width + c * 64 + x) * 4;
              for (let k = 0; k < 3; k++) worst = Math.max(worst, Math.abs(shot.data[a + k] - Math.round((ref.data[b + k] * 242) / 255)));
            }
          }
          compared++;
          if (want.includes('grassflow')) flows++;
        }
      }
      console.log(`${season} cache=${cache}: ${compared} tiles (${flows} with flow), worst ${worst}`);
      expect(compared).toBeGreaterThanOrEqual(40);
      expect(flows).toBeGreaterThanOrEqual(30);
      expect(worst).toBeLessThanOrEqual(2);
      expect(errors).toEqual([]);
      await context.close();
    });
  }
}

test('?v3=1: the village — its houses, fences, well and sign from the village bundle of the season; fences are solid; winter looks for the common objects, never for the open chest', async ({ browser }) => {
  for (const season of ['summer', 'winter']) {
    const { context, page, errors } = await open(browser, PRO, `&v3=1`);
    await api(page, 'setSeason', season);
    await api(page, 'teleport', 19, 86);
    await page.waitForTimeout(2500);
    await expect.poll(async () => (await api(page, 'season')).view).toBe(season);
    const names = (await api(page, 'stream')).bundleNames;
    expect(names).toContain(`v3:village:${season}`);
    for (const k of ['obj.house', 'obj.v3.house_stone', 'obj.v3.fence.l', 'obj.v3.fence.r', 'obj.v3.well', 'obj.v3.signpost']) expect(await api(page, 'textureDensity', k), k).toBe(4);
    if (season === 'winter') {
      expect(names).toContain('v3:objects:winter');
      expect(await api(page, 'textureDensity', 'winter.obj.chest.closed')).toBe(4);
      expect(await api(page, 'textureDensity', 'winter.obj.barrel')).toBe(4);
      expect(await api(page, 'textureDensity', 'winter.obj.chest.open')).toBe(null);
    } else expect(names).not.toContain('v3:objects:winter');
    // the fence north of the hero (tile 19,85) stops him
    const p0 = await api(page, 'player');
    await page.keyboard.down('ArrowUp');
    await page.waitForTimeout(800);
    await page.keyboard.up('ArrowUp');
    const p1 = await api(page, 'player');
    expect(p1.y).toBeGreaterThanOrEqual(86 * 16);
    expect(p1.y).toBeLessThanOrEqual(p0.y);
    const mem = await api(page, 'v3');
    expect(mem.gpu.total).toBeLessThan(35 * 2 ** 20);
    expect(errors).toEqual([]);
    await context.close();
  }
});

test('?v3=0: no village props, no v3 bundles (the game as before)', async ({ browser }) => {
  const { context, page, errors } = await open(browser, PRO, '&v3=0');
  await api(page, 'teleport', 19, 86);
  await page.waitForTimeout(2000);
  const names = (await api(page, 'stream')).bundleNames;
  expect(names.some((n) => n.startsWith('v3:'))).toBe(false);
  // nothing new stands at the fence's tile: the hero walks north through it
  await page.keyboard.down('ArrowUp');
  await page.waitForTimeout(800);
  await page.keyboard.up('ArrowUp');
  expect((await api(page, 'player')).y).toBeLessThan(86 * 16);
  expect(errors).toEqual([]);
  await context.close();
});

test('?v3=1: the normal enemies — v3 frames by kind, the plains loading only its beasts; another kind loads while it lives; trimmed frames keep their size', async ({ browser }, testInfo) => {
  for (const screen of [PRO, SE]) {
    const { context, page, errors } = await open(browser, screen, '&v3=1');
    await api(page, 'teleport', 52, 100);
    await page.waitForTimeout(2500);
    // (the plains: beasts; the island's chunks still near: beasts and archers)
    let names = (await api(page, 'stream')).bundleNames.filter((n) => n.startsWith('v3:enemy:'));
    expect(names).toContain('v3:enemy:beast');
    expect(names).not.toContain('v3:enemy:slime');
    expect(names).not.toContain('v3:enemy:sentinel');
    expect(await api(page, 'textureDensity', 'enemy.beast.move.3')).toBe(4);
    expect(await api(page, 'textureDensity', 'enemy.sentinel.idle.0')).toBe(null);
    for (const [k, dx, dy] of [['beast', 4, -1], ['slime', 3, 2], ['archer', -3, -2], ['sentinel', 6, 1]]) await api(page, 'spawnEnemy', k, 52 + dx, 100 + dy);
    await expect.poll(async () => (await api(page, 'stream')).bundleNames.filter((n) => n.startsWith('v3:enemy:')).sort(), { timeout: 15_000 }).toEqual(['v3:enemy:archer', 'v3:enemy:beast', 'v3:enemy:sentinel', 'v3:enemy:slime']);
    await page.waitForTimeout(500);
    // every live enemy is drawn with a v3 frame of its game size (a trimmed frame keeps its whole size)
    const SIZE = { beast: [22, 16], slime: [16, 14], archer: [16, 28], sentinel: [20, 28] };
    await expect.poll(async () => (await api(page, 'enemyFrames')).every((d) => d.density === 4)).toBe(true);
    for (const d of await api(page, 'enemyFrames')) expect([d.w, d.h], d.key).toEqual(SIZE[d.key.split('.')[1]]);
    const mem = await api(page, 'v3');
    expect(mem.gpu.total).toBeLessThan(35 * 2 ** 20);
    await page.screenshot({ path: testInfo.outputPath(`battle-${screen.name}.png`) });
    // the kinds go again once their enemies are gone (only the plains' beasts stay)
    await api(page, 'clearEnemies');
    await page.waitForTimeout(1500);
    names = (await api(page, 'stream')).bundleNames.filter((n) => n.startsWith('v3:enemy:'));
    expect(names).not.toContain('v3:enemy:slime');
    expect(names).not.toContain('v3:enemy:sentinel');
    expect(errors).toEqual([]);
    await context.close();
  }
});

// Graphics v3: the hero at density 4 (src/art-release-v3/hero, NAMES.md 5, STYLE.md 10.2, heroV3.js)

/** Records the hero's drawn frame every animation frame (short actions show a few frames only). */
const recordHero = (page) =>
  page.evaluate(() => {
    const w = /** @type {any} */ (window);
    w.__hero = [];
    const tick = () => {
      const h = w.__debugApi.v3().hero;
      w.__hero.push({ key: h.key, drawn: h.drawn, density: h.density, mirrored: h.mirrored, place: w.__debugApi.heroPlace() });
      w.__heroRaf = requestAnimationFrame(tick);
    };
    tick();
  });
const heroSeen = (page) => page.evaluate(() => /** @type {any} */ (window).__hero);

/** The hero's place and his effects' places relative to his feet (game px), for one frame. */
const relPlace = (p) => ({
  anchor: p.anchor,
  w: p.w,
  h: p.h,
  k: p.k,
  ...Object.fromEntries(['glider', 'shield', 'bow', 'slash', 'shadow'].map((n) => [n, p[n].visible ? [p[n].x - p.x, p[n].y - p.y] : null])),
});

test('?v3=1: the v3 hero — every action at density 4; left = right mirrored except attack 1-3, bow and guard; feet, size and effects where ?v3=0 has them', async ({ browser }) => {
  /** @type {Record<string, Record<string, any>>} */
  const byMode = {};
  for (const q of ['&v3=0', '&v3=1']) {
    const { context, page, errors } = await open(browser, PRO, q);
    await api(page, 'teleport', 52, 100);
    await page.waitForTimeout(800);
    await recordHero(page);
    // idle in the 4 directions, a walk to the left, the sword / shield / bow facing left and right
    for (const dir of ['down', 'up', 'right', 'left']) {
      await api(page, 'face', dir);
      await page.waitForTimeout(250);
    }
    await page.keyboard.down('ArrowLeft');
    await page.waitForTimeout(500);
    await page.keyboard.up('ArrowLeft');
    for (const [dir, key] of [['left', 'ArrowLeft'], ['right', 'ArrowRight']]) {
      await page.keyboard.down(key);
      await page.waitForTimeout(80);
      await page.keyboard.up(key);
      for (const press of ['KeyJ', 'KeyJ', 'KeyJ']) {
        await page.keyboard.press(press);
        await page.waitForTimeout(260);
      }
      const idle = () => expect.poll(async () => (await api(page, 'heroPose')).action, { timeout: 5000 }).toBe('idle');
      const shown = (re) => expect.poll(async () => (await heroSeen(page)).some((x) => re.test(x.key ?? '')), { message: String(re), timeout: 5000 }).toBe(true);
      await idle();
      await page.keyboard.down('KeyI');
      await shown(new RegExp(`^hero\\.guard\\.${dir}\\.1$`));
      await page.keyboard.up('KeyI');
      await idle();
      await page.keyboard.down('KeyU');
      await shown(new RegExp(`^hero\\.bow\\.${dir}\\.3$`));
      await page.keyboard.up('KeyU');
      await idle();
    }
    const seen = await heroSeen(page);
    /** @type {Record<string, any>} */
    const out = {};
    for (const s of seen) if (s.key && !out[s.key]) out[s.key] = s;
    byMode[q] = out;
    expect(errors).toEqual([]);
    await context.close();
  }
  const v0 = byMode['&v3=0'];
  const v1 = byMode['&v3=1'];
  // the actions asked for were drawn in both modes
  for (const re of [/^hero\.idle\.left\./, /^hero\.walk\.left\./, /^hero\.attack1\.left\./, /^hero\.attack2\.left\./, /^hero\.guard\.left\.1$/, /^hero\.bow\.left\.3$/, /^hero\.attack1\.right\./, /^hero\.guard\.right\.1$/, /^hero\.bow\.right\.3$/]) {
    expect(Object.keys(v1).some((k) => re.test(k)), `v3=1 ${re}`).toBe(true);
    expect(Object.keys(v0).some((k) => re.test(k)), `v3=0 ${re}`).toBe(true);
  }
  for (const [key, s] of Object.entries(v1)) {
    const action = key.split('.')[1];
    // every hero frame from the v3 art (never the old art beside the new)
    expect(s.density, key).toBe(4);
    expect(s.drawn, key).toBe(key);
    // NAMES.md 5: left = the right frame mirrored, except the actions with a held prop (their own left frames)
    const own = ['attack1', 'attack2', 'attack3', 'bow', 'guard'].includes(action);
    expect(s.mirrored, key).toBe(key.includes('.left.') && !own);
  }
  for (const [key, s] of Object.entries(v0)) {
    expect(s.density, key).toBe(2);
    expect(s.mirrored, key).toBe(false);
  }
  // the same feet (anchor), game size, heroK and effect offsets as ?v3=0, frame for frame
  let compared = 0;
  for (const key of Object.keys(v1)) {
    if (!v0[key]) continue;
    const a = relPlace(v0[key].place);
    const b = relPlace(v1[key].place);
    for (const n of ['glider', 'shield', 'bow', 'slash', 'shadow']) if (a[n] === null || b[n] === null) a[n] = b[n] = null; // (shown at different moments of the action)
    expect(b, key).toEqual(a);
    compared++;
  }
  expect(compared).toBeGreaterThan(15);
});

test('?v3=1: climb, swim and glide load when used — the approved frames meanwhile (never a missing hero), density 4 once loaded, let go after; memory', async ({ browser }) => {
  const context = await browser.newContext({ viewport: { width: PRO.width, height: PRO.height }, deviceScaleFactor: PRO.dpr, isMobile: true, hasTouch: true });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/?map=height&v3=1');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 30_000 });
  await api(page, 'clearEnemies');
  // at the start: the hero's kept bundle only (under 6.0 MB), the move bundle not loaded
  let names = (await api(page, 'stream')).bundleNames;
  expect(names).toContain('v3:hero');
  expect(names).not.toContain('v3:hero:move');
  const kept = await api(page, 'bundleBytes', 'v3:hero');
  expect(kept).toBeLessThanOrEqual(6.0e6);
  expect((await api(page, 'v3')).hero.move).toBe('out');
  expect(await api(page, 'textureDensity', 'hero.swim.up.0')).toBe(null);
  // swim: the pond's south shore, swim north
  await api(page, 'teleport', 33, 11);
  await page.waitForTimeout(300);
  await recordHero(page);
  await page.keyboard.down('ArrowUp');
  await expect.poll(async () => (await api(page, 'player')).swimming, { timeout: 4000, intervals: [30] }).toBe(true);
  await expect.poll(async () => (await api(page, 'v3')).hero.move, { timeout: 8000 }).toBe('in');
  await page.waitForTimeout(400);
  await page.keyboard.up('ArrowUp');
  const seen = await heroSeen(page);
  const swim = seen.filter((s) => s.key?.startsWith('hero.swim.'));
  expect(swim.length).toBeGreaterThan(0);
  // every frame of the swim drew a hero frame: the approved one (density 2) until the v3 one (density 4)
  for (const s of swim) {
    expect(s.drawn === s.key || s.drawn === `v1.${s.key}`, `${s.key} drawn ${s.drawn}`).toBe(true);
    expect(s.density, s.drawn).toBe(s.drawn.startsWith('v1.') ? 2 : 4);
    expect(s.place.h, s.drawn).toBe(28);
  }
  expect(swim.at(-1).density).toBe(4);
  expect(seen.every((s) => s.key !== null)).toBe(true);
  const move = await api(page, 'bundleBytes', 'v3:hero:move');
  expect(move).toBeLessThan(1.2 * 2 ** 20);
  // left = right mirrored for the swim too
  await api(page, 'face', 'left');
  await page.keyboard.down('ArrowLeft');
  await page.waitForTimeout(300);
  await page.keyboard.up('ArrowLeft');
  const h = (await api(page, 'v3')).hero;
  if (h.key?.startsWith('hero.swim.left.')) expect(h.mirrored).toBe(true);
  // out of the water and the keep time over: the move bundle goes, the hero is drawn from the kept bundle
  await api(page, 'setHeroMoveKeep', 300);
  await api(page, 'teleport', 33, 13);
  await expect.poll(async () => (await api(page, 'v3')).hero.move, { timeout: 8000 }).toBe('out');
  names = (await api(page, 'stream')).bundleNames;
  expect(names).not.toContain('v3:hero:move');
  const after = (await api(page, 'v3')).hero;
  expect(after.density).toBe(4);
  expect(after.moveUnloads).toBe(1);
  // climb: the move bundle comes back (frames drawn all along)
  await page.evaluate(() => cancelAnimationFrame(/** @type {any} */ (window).__heroRaf));
  await recordHero(page);
  await api(page, 'setHeroMoveKeep', 20_000);
  await api(page, 'teleport', 14, 22);
  await page.keyboard.down('ArrowUp');
  await expect.poll(async () => (await api(page, 'player')).climbing, { timeout: 4000 }).toBe(true);
  await expect.poll(async () => (await api(page, 'v3')).hero.move, { timeout: 8000 }).toBe('in');
  await page.keyboard.up('ArrowUp');
  const climb = (await heroSeen(page)).filter((s) => s.key?.startsWith('hero.climb.'));
  expect(climb.length).toBeGreaterThan(0);
  for (const s of climb) expect(s.drawn === s.key || s.drawn === `v1.${s.key}`, `${s.key} drawn ${s.drawn}`).toBe(true);
  expect((await api(page, 'v3')).hero.moveLoads).toBe(2);
  expect((await api(page, 'v3')).cpu.total).toBe(0);
  expect(errors).toEqual([]);
  await context.close();
});

test('?v3=0: the hero as before — no v3 hero bundles, no stand-ins, the approved frames', async ({ browser }) => {
  for (const q of ['', '&v3=0']) {
    const context = await browser.newContext({ viewport: { width: PRO.width, height: PRO.height }, deviceScaleFactor: PRO.dpr, isMobile: true, hasTouch: true });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', (e) => errors.push(e.message));
    await page.goto(`/?map=height${q}`);
    await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 30_000 });
    await api(page, 'clearEnemies');
    const names = (await api(page, 'stream')).bundleNames;
    expect(names.filter((n) => n.startsWith('v3:'))).toEqual([]);
    for (const k of ['hero.idle.down.0', 'hero.walk.left.0', 'hero.attack1.left.0', 'hero.swim.up.0', 'hero.climb.right.0', 'hero.glide.left.0']) expect(await api(page, 'textureDensity', k), k).toBe(2);
    expect(await api(page, 'textureDensity', 'v1.hero.swim.up.0')).toBe(null);
    await api(page, 'teleport', 33, 11);
    await page.keyboard.down('ArrowUp');
    await expect.poll(async () => (await api(page, 'player')).swimming, { timeout: 4000, intervals: [30] }).toBe(true);
    await page.waitForTimeout(200);
    await page.keyboard.up('ArrowUp');
    const h = (await api(page, 'v3')).hero;
    expect(h.key).toMatch(/^hero\.swim\.up\.\d$/);
    expect(h.drawn).toBe(h.key);
    expect(h.density).toBe(2);
    expect(h.move).toBe(undefined);
    expect(errors).toEqual([]);
    await context.close();
  }
});
