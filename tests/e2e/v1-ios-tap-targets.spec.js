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

for (const vp of VIEWPORTS) {
  for (const large of [false, true]) {
    test(`tap targets ≥ 44 px at ${vp.width}×${vp.height}${large ? ', large text' : ''}`, async ({ page }) => {
      const errors = [];
      page.on('pageerror', (e) => errors.push(e.message));
      await page.setViewportSize(vp);
      await page.goto('/?map=world&time=10&season=summer');
      await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
      await api(page, 'clearEnemies');
      if (large) await page.evaluate(() => document.getElementById('ui')?.classList.add('text-large'));
      await api(page, 'give', 'travel_sword');
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

      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
      expect(errors).toEqual([]);
    });
  }
}
