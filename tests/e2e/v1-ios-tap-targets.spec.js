import { test, expect } from '@playwright/test';

// v1.0 (iPhone): every button the player taps is at least 44 × 44 pt (Apple HIG; 1 CSS px = 1 pt),
// the HUD buttons do not run into the HUD text, the round buttons' labels are 12 px or more, and
// the settings screen's 閉じる can be reached without scrolling. Checked on the smallest and the
// largest iPhone landscape screens, with normal and large text.

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);
const MIN = 44;
const VIEWPORTS = [
  { width: 734, height: 343 }, // iPhone SE-class / Safari with its bars
  { width: 852, height: 393 }, // iPhone 15 Pro
  { width: 932, height: 430 }, // iPhone 15 Pro Max
];

/** Visible buttons (and tappable item rows) smaller than 44 px in either direction. */
const smallTargets = (page) =>
  page.evaluate((min) => {
    const out = [];
    for (const el of document.querySelectorAll('#ui button, #ui .inv-row.clickable')) {
      if (el.closest('[hidden]') || el.closest('#debug-panel')) continue;
      const r = el.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) continue;
      if (r.width < min - 0.01 || r.height < min - 0.01) out.push(`${el.id || el.className} ${Math.round(r.width)}x${Math.round(r.height)}`);
    }
    return out;
  }, MIN);

const overlap = (a, b) => a.x < b.x + b.width && b.x < a.x + a.width && a.y < b.y + b.height && b.y < a.y + a.height;

// Graphics v2 (W4): the same checks with the v2 UI (?ui=v2: glass discs with icons, plates, frames);
// its round buttons are whole-px art diameters (uiSkin.js), and its labels show for the first sessions.
for (const ui of ['v1', 'v2']) {
  for (const vp of VIEWPORTS) {
    for (const large of [false, true]) {
      test(`tap targets ≥ 44 px at ${vp.width}×${vp.height}${large ? ', large text' : ''}, ui ${ui}`, async ({ page }) => {
        const errors = [];
        page.on('pageerror', (e) => errors.push(e.message));
        await page.setViewportSize(vp);
        await page.goto(`/?map=world&time=10&season=summer&ui=${ui}`);
        expect(await page.evaluate(() => document.getElementById('ui')?.classList.contains('ui-v2'))).toBe(ui === 'v2');
        await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
        await api(page, 'clearEnemies');
        if (large) await page.evaluate(() => document.getElementById('ui')?.classList.add('text-large'));
        for (const id of ['travel_sword', 'guard_spear', 'rusty_greatsword', 'ember_sword', 'star_steel_sword']) await api(page, 'give', id);
        await api(page, 'standBy', 'elder');
        await expect(page.locator('#use-button')).toBeVisible();

        // In play: Ⅱ, 持ち物, 話す and the round buttons.
        expect(await smallTargets(page)).toEqual([]);
        const pause = await page.locator('#pause-button').boundingBox();
        const bag = await page.locator('#bag-button').boundingBox();
        expect(overlap(pause, bag)).toBe(false);
        for (const id of ['hud-hearts', 'hud-clock', 'hud-treasure']) {
          const box = await page.locator(`#${id}`).boundingBox();
          if (!box) continue;
          expect(overlap(pause, box), `pause / ${id}`).toBe(false);
          expect(overlap(bag, box), `bag / ${id}`).toBe(false);
        }
        for (const id of ['dash-button', 'guard-button', 'jump-button', 'bow-button', 'dodge-button', 'attack-button']) {
          const px = await page.locator(`#${id}`).evaluate((el) => parseFloat(getComputedStyle(el).fontSize));
          expect(px, id).toBeGreaterThanOrEqual(12);
        }

        // Every button size, either hand, with two abilities (⇄ shown): every target ≥ 44 px, the
        // labels ≥ 12 px and inside their circle, and no two buttons overlapping (QA2 M-1, M-2).
        await api(page, 'grantAbility', 'light');
        await api(page, 'grantAbility', 'resonance');
        await expect(page.locator('#ability-next')).toBeVisible();
        for (const size of ['btn-small', '', 'btn-large']) {
          for (const left of [false, true]) {
            await page.evaluate(([size, left]) => {
              const ui = /** @type {HTMLElement} */ (document.getElementById('ui'));
              ui.classList.remove('btn-small', 'btn-large');
              if (size) ui.classList.add(size);
              ui.classList.toggle('left-handed', left);
            }, /** @type {const} */ ([size, left]));
            const tag = `${size || 'btn-medium'}${left ? ' left' : ''}`;
            expect(await smallTargets(page), tag).toEqual([]);
            const check = await page.evaluate(() => {
              const ids = ['attack-button', 'jump-button', 'dodge-button', 'bow-button', 'guard-button', 'dash-button', 'ability-button', 'ability-next'];
              const boxes = ids.map((id) => /** @type {HTMLElement} */ (document.getElementById(id))).filter((el) => el && !el.hidden);
              const out = { small: /** @type {string[]} */ ([]), spill: /** @type {string[]} */ ([]), overlaps: /** @type {string[]} */ ([]), offscreen: /** @type {string[]} */ ([]) };
              for (const el of boxes) {
                const r = el.getBoundingClientRect();
                if (parseFloat(getComputedStyle(el).fontSize) < 12) out.small.push(el.id);
                const rg = document.createRange();
                rg.selectNodeContents(el);
                const t = rg.getBoundingClientRect();
                if (t.width > 0 && (t.left < r.left + 1 || t.right > r.right - 1 || t.top < r.top || t.bottom > r.bottom)) out.spill.push(el.id);
                if (r.left < 0 || r.top < 0 || r.right > innerWidth || r.bottom > innerHeight) out.offscreen.push(el.id);
              }
              // circles: centre distance against the radii (the round buttons and ⇄ are all circles)
              for (let i = 0; i < boxes.length; i++)
                for (let j = i + 1; j < boxes.length; j++) {
                  const a = boxes[i].getBoundingClientRect();
                  const b = boxes[j].getBoundingClientRect();
                  const d = Math.hypot(a.left + a.width / 2 - (b.left + b.width / 2), a.top + a.height / 2 - (b.top + b.height / 2));
                  if (d < a.width / 2 + b.width / 2) out.overlaps.push(`${boxes[i].id}/${boxes[j].id}`);
                }
              return out;
            });
            expect(check, tag).toEqual({ small: [], spill: [], overlaps: [], offscreen: [] });
            // The ability button's top-right corner (inside its circle) is the ability button, not ⇄.
            const hit = await page.evaluate(() => {
              const r = /** @type {HTMLElement} */ (document.getElementById('ability-button')).getBoundingClientRect();
              const k = 0.3; // 45° up-right, at 0.7 of the radius
              return document.elementFromPoint(r.left + r.width * (0.5 + k * 0.85), r.top + r.height * (0.5 - k * 0.85))?.id;
            });
            expect(hit, tag).toBe('ability-button');
          }
        }
        await page.evaluate(() => document.getElementById('ui')?.classList.remove('btn-small', 'btn-large', 'left-handed'));

        // The pause screen.
        await page.click('#pause-button');
        await expect(page.locator('#pause-overlay')).toBeVisible();
        expect(await smallTargets(page)).toEqual([]);

        // Settings: every choice ≥ 44 px, and 閉じる inside the panel without scrolling.
        await page.click('#open-settings');
        await expect(page.locator('#settings-menu')).toBeVisible();
        expect(await smallTargets(page)).toEqual([]);
        const fits = await page.evaluate(() => {
          const menu = /** @type {HTMLElement} */ (document.getElementById('settings-menu'));
          const m = menu.getBoundingClientRect();
          const c = /** @type {HTMLElement} */ (document.getElementById('settings-close')).getBoundingClientRect();
          return { scrollTop: menu.scrollTop, inside: c.top >= m.top && c.bottom <= m.bottom + 0.5 && c.bottom <= innerHeight };
        });
        expect(fits).toEqual({ scrollTop: 0, inside: true });
        await page.locator('#settings-close').click({ trial: true }); // nothing covers it
        await page.click('#settings-close');
        await expect(page.locator('#settings-menu')).toBeHidden();
        await page.click('#resume-button');
        await expect(page.locator('#pause-overlay')).toBeHidden();

        // The inventory: tabs (弓 too), 閉じる and the item rows.
        await page.click('#bag-button');
        await expect(page.locator('#inv-menu')).toBeVisible();
        await expect(page.locator('#inv-tab-bow')).toBeVisible();
        expect(await smallTargets(page)).toEqual([]);
        expect(await page.locator('#inv-menu .inv-row').count()).toBeGreaterThan(0);
        // A new tab starts at its top (QA2 L-4): scroll the weapons down, then switch to 素材.
        const scrolled = await page.locator('#inv-menu .inv-body').evaluate((el) => {
          el.scrollTop = el.scrollHeight;
          return el.scrollTop;
        });
        if (vp.height < 393 || large) expect(scrolled).toBeGreaterThan(0); // seven weapons do not fit there
        await page.click('#inv-tab-material');
        expect(await page.locator('#inv-menu .inv-body').evaluate((el) => el.scrollTop)).toBe(0);

        expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
        expect(errors).toEqual([]);
      });
    }
  }
}
