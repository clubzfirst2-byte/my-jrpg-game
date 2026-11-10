import { test, expect } from '@playwright/test';

// Graphics v2, W4: the v2 UI art on the DOM UI (src/ui/uiSkin.js, styles.css `#ui.ui-v2`).
// ?ui=v2 puts it on; ?ui=v1 and ?v2=0 keep the v1 UI exactly. The round buttons are drawn rings at
// their exact whole-px diameters (inspection I-1), the boss bar's frame is 12 px (I-2), the settings
// (text size, button size, hand, labels) work as before, and the saved game is not touched.

const api = (page, fn, ...args) => page.evaluate(([f, a]) => window.__debugApi[f](...a), [fn, args]);
const ROUND = ['attack-button', 'jump-button', 'dodge-button', 'bow-button', 'guard-button', 'dash-button', 'ability-button', 'ability-next'];
const DIAMETERS = {
  small: [66, 51, 49, 44, 44, 44, 44, 44],
  medium: [78, 60, 58, 52, 52, 48, 52, 44],
  large: [90, 69, 67, 60, 60, 55, 60, 44],
};

async function open(page, query) {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto(`/?map=world&time=10&season=summer${query}`);
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await api(page, 'clearEnemies');
  return errors;
}
const isV2 = (page) => page.evaluate(() => document.getElementById('ui')?.classList.contains('ui-v2'));
async function settings(page) {
  await page.click('#pause-button');
  await page.click('#open-settings');
  await expect(page.locator('#settings-menu')).toBeVisible();
}
async function done(page) {
  await page.click('#settings-close');
  await page.click('#resume-button');
  await expect(page.locator('#pause-overlay')).toBeHidden();
}
/** The art an element (or its ::before) is drawn with: loads, and is the size it is shown at. */
const artOf = (page, sel, pseudo = null) =>
  page.evaluate(
    async ([sel, pseudo]) => {
      const el = /** @type {HTMLElement} */ (document.querySelector(sel));
      const cs = getComputedStyle(el, pseudo);
      const src = cs.backgroundImage !== 'none' ? cs.backgroundImage : cs.borderImageSource;
      const url = /url\("(.+?)"\)/.exec(src)?.[1];
      if (!url) return null;
      const img = new Image();
      img.src = url;
      await img.decode();
      return { w: img.naturalWidth, h: img.naturalHeight, rendering: cs.imageRendering };
    },
    [sel, pseudo],
  );

test('?ui=v1, ?v2=0 and no switch: the v1 UI, nothing of v2 loaded or stored', async ({ page }) => {
  for (const query of ['', '&ui=v1', '&v2=0']) {
    const requests = [];
    page.on('request', (r) => requests.push(r.url()));
    const errors = await open(page, query);
    expect(await isV2(page), query).toBe(false);
    expect(await page.evaluate(() => !!document.getElementById('ui-v2-buttons'))).toBe(false);
    expect(await page.evaluate(() => document.documentElement.style.length)).toBe(0); // no --ui-* frames
    expect(requests.filter((u) => /release-v2-ui|art-release-v2\/ui/.test(u))).toEqual([]);
    expect(await page.evaluate(() => localStorage.getItem('seimyaku.sessions.v1'))).toBe(null);
    // the v1 look: text on a translucent disc with a border, SVG hearts
    const attack = await page.locator('#attack-button').evaluate((el) => ({ text: el.textContent, color: getComputedStyle(el).color, border: getComputedStyle(el).borderTopWidth, image: getComputedStyle(el).backgroundImage }));
    expect(attack).toMatchObject({ text: '攻撃', border: '2px', image: 'none' });
    expect(attack.color).not.toBe('rgba(0, 0, 0, 0)');
    await settings(page);
    await expect(page.locator('#set-buttonLabels-auto')).toHaveCount(0);
    await done(page);
    expect(errors).toEqual([]);
    page.removeAllListeners('request');
  }
});

test('?ui=v2: rings at their exact diameters (I-1) at every size and hand, icons, labels for the first sessions', async ({ page }, testInfo) => {
  const errors = await open(page, '&ui=v2');
  expect(await isV2(page)).toBe(true);
  await api(page, 'grantAbility', 'light');
  await api(page, 'grantAbility', 'resonance');
  await expect(page.locator('#ability-next')).toBeVisible();
  // the first session: the text labels show (12 px or more), no icon
  await expect(page.locator('#ui')).toHaveClass(/ui-labels/);
  const label = await page.locator('#attack-button').evaluate((el) => ({ size: parseFloat(getComputedStyle(el).fontSize), color: getComputedStyle(el).color, icon: getComputedStyle(el, '::before').display }));
  expect(label.size).toBeGreaterThanOrEqual(12);
  expect(label.color).not.toBe('rgba(0, 0, 0, 0)');
  expect(label.icon).toBe('none');

  const vp = page.viewportSize();
  for (const hand of ['right', 'left']) {
    for (const size of /** @type {const} */ (['small', 'medium', 'large'])) {
      await settings(page);
      await page.click(`#set-hand-${hand}`);
      await page.click(`#set-buttonSize-${size}`);
      await done(page);
      const boxes = await page.evaluate((ids) => ids.map((id) => {
        const r = /** @type {HTMLElement} */ (document.getElementById(id)).getBoundingClientRect();
        return [r.left, r.top, r.width, r.height];
      }), ROUND);
      for (const [i, [x, y, w, h]] of boxes.entries()) {
        const tag = `${ROUND[i]} ${size} ${hand}`;
        expect([w, h], tag).toEqual([DIAMETERS[size][i], DIAMETERS[size][i]]);
        expect(Number.isInteger(x) && Number.isInteger(y), `${tag} at ${x},${y}`).toBe(true);
        expect(x >= 0 && y >= 0 && x + w <= vp.width && y + h <= vp.height, tag).toBe(true);
        // the ring is the art of that diameter, shown 1 : 1, pixelated
        expect(await artOf(page, `#${ROUND[i]}`), tag).toEqual({ w, h, rendering: 'pixelated' });
      }
      const attack = boxes[0];
      if (hand === 'right') expect(attack[0]).toBeGreaterThan(vp.width / 2);
      else expect(attack[0] + attack[2]).toBeLessThan(vp.width / 2);
    }
  }

  // 「ボタンに文字を表示：なし」: icons (whole px, 1 : 1), the names stay as aria-labels; remembered
  await settings(page);
  await page.click('#set-hand-right');
  await page.click('#set-buttonSize-medium');
  await page.click('#set-buttonLabels-off');
  await done(page);
  await expect(page.locator('#ui')).not.toHaveClass(/ui-labels/);
  for (const id of ROUND) {
    const icon = await page.locator(`#${id}`).evaluate((el) => {
      const cs = getComputedStyle(el, '::before');
      return { left: cs.left, top: cs.top, w: parseFloat(cs.width), h: parseFloat(cs.height), aria: el.getAttribute('aria-label') };
    });
    expect(Number.isInteger(parseFloat(icon.left)) && Number.isInteger(parseFloat(icon.top)), id).toBe(true);
    expect(await artOf(page, `#${id}`, '::before'), id).toEqual({ w: icon.w, h: icon.h, rendering: 'pixelated' });
    expect(icon.aria, id).toBeTruthy();
  }
  // the selected power's name stays readable on the ability button (12 px), and follows ⇄
  const ability = page.locator('#ability-button');
  const before = await ability.textContent();
  expect(await ability.evaluate((el) => ({ size: parseFloat(getComputedStyle(el).fontSize), shown: getComputedStyle(el).color !== 'rgba(0, 0, 0, 0)' }))).toEqual({ size: 12, shown: true });
  await page.click('#ability-next');
  await expect(ability).not.toHaveText(/** @type {string} */ (before));
  await expect(ability).toHaveAttribute('aria-label', /** @type {string} */ (await ability.textContent()));
  // pause and bag: 44 × 44 plates
  for (const id of ['pause-button', 'bag-button']) {
    const b = await page.locator(`#${id}`).boundingBox();
    expect([b.width, b.height], id).toEqual([44, 44]);
  }
  await page.screenshot({ path: testInfo.outputPath('hud-icons.png') });
  // the buttons still work: attack is pressed by touch, the bag opens
  await page.locator('#attack-button').dispatchEvent('pointerdown', { pointerId: 7, pointerType: 'touch', isPrimary: true });
  await expect(page.locator('#attack-button')).toHaveClass(/active/);
  await page.locator('#attack-button').dispatchEvent('pointerup', { pointerId: 7, pointerType: 'touch', isPrimary: true });
  await page.reload();
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  expect(await api(page, 'settings')).toMatchObject({ buttonLabels: 'off', hand: 'right', buttonSize: 'medium' });
  await expect(page.locator('#ui')).not.toHaveClass(/ui-labels/);
  expect(errors).toEqual([]);
});

test('?ui=v2: labels stop after the first sessions (auto), and 「いつも」 keeps them', async ({ page }) => {
  await page.addInitScript(() => {
    if (!sessionStorage.getItem('seeded')) localStorage.setItem('seimyaku.sessions.v1', '3');
    sessionStorage.setItem('seeded', '1');
  });
  const errors = await open(page, '&ui=v2'); // the 4th session
  await expect(page.locator('#ui')).not.toHaveClass(/ui-labels/);
  await settings(page);
  await expect(page.locator('#set-buttonLabels-auto')).toHaveClass(/selected/);
  await page.click('#set-buttonLabels-on');
  await done(page);
  await expect(page.locator('#ui')).toHaveClass(/ui-labels/);
  expect(errors).toEqual([]);
});

test('?ui=v2: title, menus, dialogue and the boss bar wear the art; large text keeps the frames crisp', async ({ page }, testInfo) => {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  // the title: the logo at 2 CSS px per art px, 48-px plates, the name still text for screen readers
  await page.goto('/?ui=v2');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await expect(page.locator('#title-screen')).toBeVisible();
  await expect(page.locator('#title-screen h1')).toHaveText('星環のレガリア');
  expect(await artOf(page, '#title-screen h1')).toEqual({ w: 230, h: 64, rendering: 'pixelated' });
  const logo = await page.locator('#title-screen h1').boundingBox();
  expect([logo.width, logo.height]).toEqual([460, 128]);
  const vp = page.viewportSize();
  for (const id of ['title-new', 'title-continue']) {
    const b = await page.locator(`#${id}`).boundingBox();
    expect(b.height, id).toBeGreaterThanOrEqual(44);
    expect(b.y >= logo.y + logo.height && b.y + b.height <= vp.height, id).toBe(true);
  }
  expect(await page.locator('#title-new').evaluate((el) => parseFloat(getComputedStyle(el).fontSize))).toBeGreaterThanOrEqual(12);
  await page.screenshot({ path: testInfo.outputPath('title.png') });

  await page.goto('/?map=world&time=10&season=summer&ui=v2');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  // hearts: the drawn quarters
  expect(await artOf(page, '#hud-hearts svg')).toEqual({ w: 22, h: 20, rendering: 'pixelated' });
  // the boss bar: its frame exactly 12 px high (I-2), also with large text
  const boss = (await api(page, 'bosses')).find((b) => b.id === 'core_forest');
  await api(page, 'setHp', 400);
  await api(page, 'teleport', Math.floor(boss.x / 16), Math.floor(boss.y / 16) + 4);
  await expect(page.locator('#boss-bar')).toBeVisible();
  expect((await page.locator('#boss-bar .boss-track').boundingBox()).height).toBe(12);
  await page.evaluate(() => document.getElementById('ui')?.classList.add('text-large'));
  expect((await page.locator('#boss-bar .boss-track').boundingBox()).height).toBe(12);
  expect(await page.locator('#boss-bar .boss-name').evaluate((el) => parseFloat(getComputedStyle(el).fontSize))).toBeGreaterThanOrEqual(12);
  await page.screenshot({ path: testInfo.outputPath('boss.png') });
  await page.evaluate(() => document.getElementById('ui')?.classList.remove('text-large'));

  // dialogue: the round buttons are hidden behind the box, and come back
  await page.goto('/?map=world&time=10&season=summer&ui=v2');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await api(page, 'clearEnemies');
  await api(page, 'standBy', 'elder');
  await expect(page.locator('#use-button')).toBeVisible();
  await api(page, 'talkTo', 'elder');
  await expect(page.locator('#dialogue')).toBeVisible();
  await expect(page.locator('#attack-button')).toBeHidden();
  expect(await page.locator('.dialogue-text').evaluate((el) => parseFloat(getComputedStyle(el).fontSize))).toBeGreaterThanOrEqual(12);
  expect(await artOf(page, '#dialogue')).toMatchObject({ w: 32, h: 32 });
  await page.screenshot({ path: testInfo.outputPath('dialogue.png') });
  for (let i = 0; i < 30 && (await api(page, 'dialogue')); i++) {
    await page.keyboard.press('Enter');
    await page.waitForTimeout(120);
  }
  if (!(await api(page, 'dialogue'))) await expect(page.locator('#attack-button')).toBeVisible();

  // the inventory: frame, tabs and rows; with large text (zoom 1.22) the frame's edge is still 10 screen px
  await page.goto('/?map=world&time=10&season=summer&ui=v2');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  await api(page, 'clearEnemies');
  for (const id of ['travel_sword', 'guard_spear']) await api(page, 'give', id);
  await page.click('#bag-button');
  await expect(page.locator('#inv-menu')).toBeVisible();
  expect(await artOf(page, '#inv-menu')).toMatchObject({ w: 32, h: 32 });
  expect(await artOf(page, '#inv-menu .inv-row')).toMatchObject({ w: 20, h: 20 });
  const edge = () => page.locator('#inv-menu').evaluate((el) => {
    const cs = getComputedStyle(el);
    return parseFloat(cs.borderImageWidth) * (parseFloat(cs.zoom) || 1);
  });
  expect(await edge()).toBeCloseTo(10, 3);
  await page.evaluate(() => document.getElementById('ui')?.classList.add('text-large'));
  expect(await page.locator('#inv-menu').evaluate((el) => getComputedStyle(el).zoom)).toBe('1.22');
  expect(await edge()).toBeCloseTo(10, 3);
  await page.screenshot({ path: testInfo.outputPath('inventory-large.png') });
  expect(errors).toEqual([]);
});

test('the saved game is the same in either UI: saved in v1, continued in v2, saved there, continued in v1', async ({ page }, testInfo) => {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  const title = async (ui) => {
    await page.goto(`/?ui=${ui}`);
    await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
    await expect(page.locator('#title-screen')).toBeVisible();
    expect(await isV2(page)).toBe(ui === 'v2');
  };
  await title('v1');
  await page.click('#title-new');
  await api(page, 'skipOpening');
  await api(page, 'give', 'travel_sword');
  expect(await api(page, 'saveNow')).toBe(true);

  await title('v2');
  await expect(page.locator('#title-continue')).toBeEnabled();
  // はじめから asks first: the question and both buttons fit on the screen, 44 px or more
  await page.click('#title-new');
  await expect(page.locator('.title-confirm')).toBeVisible();
  const vp = page.viewportSize();
  for (const id of ['title-confirm-yes', 'title-confirm-no']) {
    const b = await page.locator(`#${id}`).boundingBox();
    expect(b.height >= 44 && b.y + b.height <= vp.height, id).toBe(true);
  }
  await page.screenshot({ path: testInfo.outputPath('title-confirm.png') });
  await page.click('#title-confirm-no');
  await page.click('#title-continue');
  expect((await api(page, 'inventory')).weapons.some((w) => w.id === 'travel_sword')).toBe(true);
  await api(page, 'give', 'guard_spear');
  expect(await api(page, 'saveNow')).toBe(true);

  await title('v1');
  await page.click('#title-continue');
  const ids = (await api(page, 'inventory')).weapons.map((w) => w.id);
  expect(ids).toEqual(expect.arrayContaining(['travel_sword', 'guard_spear']));
  expect(errors).toEqual([]);
});

// ---- W4 inspection, round 2 (W-1 … W-4) ----

test('?ui=v2 W-1: with no save, つづきから is an opaque plate on the title', async ({ page }) => {
  await page.goto('/?ui=v2');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true', { timeout: 20_000 });
  const cont = page.locator('#title-continue');
  await expect(cont).toBeDisabled();
  expect(await cont.evaluate((el) => ({ bg: getComputedStyle(el).backgroundColor, clip: getComputedStyle(el).backgroundClip }))).toEqual({ bg: 'rgb(20, 32, 51)', clip: 'padding-box' });
});

test('?ui=v2 W-2: the text labels stay inside the rings\' metal edge, every size and hand', async ({ page }) => {
  const errors = await open(page, '&ui=v2');
  await api(page, 'grantAbility', 'light');
  await api(page, 'grantAbility', 'resonance');
  await expect(page.locator('#ui')).toHaveClass(/ui-labels/);
  for (const size of ['btn-small', '', 'btn-large']) {
    for (const left of [false, true]) {
      const out = await page.evaluate(([size, left]) => {
        const ui = /** @type {HTMLElement} */ (document.getElementById('ui'));
        ui.classList.remove('btn-small', 'btn-large');
        if (size) ui.classList.add(size);
        ui.classList.toggle('left-handed', left);
        const bad = [];
        for (const el of document.querySelectorAll('#ui .action-button')) {
          if (/** @type {HTMLElement} */ (el).hidden) continue;
          const b = el.getBoundingClientRect();
          const cx = b.left + b.width / 2;
          const cy = b.top + b.height / 2;
          const r = b.width / 2 - 5; // the metal edge is 5 art px = 5 CSS px
          const range = document.createRange();
          range.selectNodeContents(el);
          // the text's line boxes (wider and taller than the glyphs' ink); 1 px for the corners' round-off
          for (const t of range.getClientRects())
            for (const [x, y] of [[t.left, t.top], [t.right, t.top], [t.left, t.bottom], [t.right, t.bottom]])
              if (Math.hypot(x - cx, y - cy) > r + 1) bad.push(`${el.id} (${b.width} px): ${Math.hypot(x - cx, y - cy).toFixed(1)} > ${r}`);
          if (parseFloat(getComputedStyle(el).fontSize) < 12) bad.push(`${el.id} font`);
        }
        return bad;
      }, [size, left]);
      expect(out, `${size || 'medium'} ${left ? 'left' : 'right'}`).toEqual([]);
    }
  }
  expect(errors).toEqual([]);
});

for (const ui of ['v1', 'v2']) {
  test(`?ui=${ui} W-3: the ability message keeps clear of the buttons and names the hand`, async ({ page }) => {
    for (const hand of ['right', 'left']) {
      await page.addInitScript((hand) => localStorage.setItem('seimyaku.settings.v1', JSON.stringify({ hand, buttonSize: 'large' })), hand);
      const errors = await open(page, `&ui=${ui}`);
      await api(page, 'grantAbility', 'light');
      await api(page, 'grantAbility', 'resonance');
      const toast = page.locator('#toast');
      await expect(toast).toBeVisible();
      await expect(toast).toContainText(`${hand === 'left' ? '左' : '右'}の「能力」ボタン`);
      await expect(page.locator('#ability-next')).toBeVisible();
      const t = await toast.boundingBox();
      for (const id of ['ability-next', 'ability-button', 'dash-button', 'dodge-button', 'bow-button', 'guard-button', 'jump-button', 'attack-button', 'pause-button', 'bag-button']) {
        const b = await page.locator(`#${id}`).boundingBox();
        const overlap = t.x < b.x + b.width && b.x < t.x + t.width && t.y < b.y + b.height && b.y < t.y + t.height;
        expect(overlap, `${hand}: toast over ${id}`).toBe(false);
      }
      expect(errors).toEqual([]);
    }
  });
}

test('?ui=v2 W-4: the full-screen panels are opaque and hide the HUD under them (inventory, settings), large text too', async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem('seimyaku.settings.v1', JSON.stringify({ textSize: 'large' })));
  const errors = await open(page, '&ui=v2');
  const hudIds = ['attack-button', 'pause-button', 'bag-button'];
  const shown = () => page.evaluate((ids) => ids.map((id) => getComputedStyle(/** @type {HTMLElement} */ (document.getElementById(id))).visibility), hudIds);
  expect(await shown()).toEqual(['visible', 'visible', 'visible']);
  await page.click('#bag-button');
  await expect(page.locator('#inv-menu')).toBeVisible();
  await expect(page.locator('#ui')).toHaveClass(/panel-open/);
  expect(await shown()).toEqual(['hidden', 'hidden', 'hidden']);
  expect(await page.locator('#inv-menu').evaluate((el) => getComputedStyle(el).backgroundColor)).toBe('rgb(11, 18, 29)');
  // 閉じる with its × icon
  expect(await artOf(page, '#inv-close', '::before')).toMatchObject({ w: 20, h: 20 });
  await page.click('#inv-close');
  await expect(page.locator('#ui')).not.toHaveClass(/panel-open/);
  expect(await shown()).toEqual(['visible', 'visible', 'visible']);
  // settings (over the pause screen)
  await settings(page);
  await expect(page.locator('#ui')).toHaveClass(/panel-open/);
  expect(await page.locator('#settings-menu').evaluate((el) => getComputedStyle(el).backgroundColor)).toBe('rgb(11, 18, 29)');
  expect(await page.locator('.pause-version').evaluate((el) => parseFloat(getComputedStyle(el).fontSize))).toBeGreaterThanOrEqual(12);
  await done(page);
  await expect(page.locator('#ui')).not.toHaveClass(/panel-open/);
  expect(errors).toEqual([]);
});
