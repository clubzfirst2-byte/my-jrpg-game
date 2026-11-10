import { describe, it, expect, afterEach, vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { BUTTON_SCALE, HUD_BUTTONS, buttonBox, cssVar, frameUrls, hudButtonCss, showButtonLabels, LABEL_SESSIONS } from '../../src/ui/uiSkin.js';
import { BUTTON_LABELS_ROW, SETTING_ROWS } from '../../src/ui/settingsMenu.js';

// Graphics v2, W4: the v2 UI's round buttons are drawn rings at their exact diameters (inspection
// I-1: no 66.3 px), at whole-px places, never overlapping, at every button size.

const SIZES = /** @type {const} */ (['small', 'medium', 'large']);
const ART = new URL('../../src/art-release-v2/ui/', import.meta.url);
const sprites = Object.keys(JSON.parse(readFileSync(new URL('manifest.json', ART), 'utf8')).sprites);

describe('v2 round buttons (uiSkin.js)', () => {
  it('every diameter, place and icon offset is a whole px; diameters are the drawn rings, ≥ 44', () => {
    for (const id of Object.keys(HUD_BUTTONS)) {
      for (const size of SIZES) {
        const b = buttonBox(id, size);
        for (const v of [b.d, b.side, b.bottom, b.icon, b.inset]) expect(Number.isInteger(v), `${id} ${size}`).toBe(true);
        expect(b.d).toBe(HUD_BUTTONS[id].sizes[size]);
        expect(b.d).toBeGreaterThanOrEqual(44);
        expect(b.inset * 2 + b.icon).toBeLessThanOrEqual(b.d);
      }
    }
  });

  it('the generated CSS has no fractional px and uses only art that exists', () => {
    const css = hudButtonCss();
    expect(css).not.toMatch(/\d\.\d+px/);
    const names = [...css.matchAll(/var\(--ui-([a-z0-9-]+)\)/g)].map((m) => m[1]);
    expect(names.length).toBeGreaterThan(0);
    const known = new Set(sprites.map((n) => cssVar(n).slice(5)));
    expect(known.size).toBeGreaterThan(50);
    for (const n of names) expect(known.has(n), n).toBe(true);
    // one rule set per button, size and hand: 8 buttons × 3 sizes × 2 hands × (box, pressed, icon)
    expect(css.split('\n')).toHaveLength(Object.keys(HUD_BUTTONS).length * 3 * 2 * 3);
  });

  it('styles.css uses only v2 UI art that exists', () => {
    const css = readFileSync(new URL('../../src/styles.css', import.meta.url), 'utf8');
    const known = new Set(sprites.map((n) => cssVar(n).slice(5)));
    const used = [...css.matchAll(/var\(--ui-([a-z0-9-]+)\)/g)].map((m) => m[1]);
    expect(used.length).toBeGreaterThan(20);
    for (const n of used) expect(known.has(n), n).toBe(true);
  });

  it('no two round buttons overlap, at any size (⇄ sits clear above the ability button)', () => {
    for (const size of SIZES) {
      const boxes = Object.keys(HUD_BUTTONS).map((id) => ({ id, ...buttonBox(id, size) }));
      for (let i = 0; i < boxes.length; i++)
        for (let j = i + 1; j < boxes.length; j++) {
          const a = boxes[i];
          const b = boxes[j];
          const d = Math.hypot(a.side + a.d / 2 - (b.side + b.d / 2), a.bottom + a.d / 2 - (b.bottom + b.d / 2));
          expect(d, `${a.id} / ${b.id} at ${size}`).toBeGreaterThanOrEqual(a.d / 2 + b.d / 2);
        }
      const ab = buttonBox('ability-button', size);
      const next = buttonBox('ability-next', size);
      expect(next.bottom - (ab.bottom + ab.d)).toBe(6);
    }
  });

  it('the sizes follow the v1 cluster (× 0.85 / 1 / 1.15, rounded)', () => {
    expect(BUTTON_SCALE).toEqual({ small: 0.85, medium: 1, large: 1.15 });
    expect(buttonBox('attack-button', 'small').d).toBe(66); // not 66.3
    expect(buttonBox('attack-button', 'large').d).toBe(90);
    expect(buttonBox('dash-button', 'small').d).toBe(44); // ≥ 44 (48 × 0.85 = 40.8)
  });
});

describe('button labels (first sessions, or the setting)', () => {
  it('auto: the first sessions only; on / off: always / never', () => {
    expect(LABEL_SESSIONS).toBe(3);
    expect([1, 2, 3, 4, 10].map((n) => showButtonLabels('auto', n))).toEqual([true, true, true, false, false]);
    expect(showButtonLabels('on', 99)).toBe(true);
    expect(showButtonLabels('off', 1)).toBe(false);
  });

  it('the settings row exists for the v2 UI only (not in the v1 rows)', () => {
    expect(BUTTON_LABELS_ROW.key).toBe('buttonLabels');
    expect(BUTTON_LABELS_ROW.label).toBe('ボタンに文字を表示');
    expect(BUTTON_LABELS_ROW.options.map((o) => o.value)).toEqual(['auto', 'on', 'off']);
    expect(SETTING_ROWS.some((r) => r.key === 'buttonLabels')).toBe(false);
  });
});

describe('frame URLs (cut out of the sheet as PNG data: URLs)', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('cuts each sheet place out on one canvas; file URLs pass through; order kept; canvas freed', () => {
    const canvases = [];
    vi.stubGlobal('document', {
      createElement: () => {
        const c = { width: 0, height: 0, draws: [], sizes: [], getContext: () => ({ drawImage: (...a) => c.draws.push(a) }), toDataURL: () => (c.sizes.push([c.width, c.height]), `data:image/png;base64,${c.sizes.length}`) };
        canvases.push(c);
        return c;
      },
    });
    const sheet = {};
    const urls = frameUrls(
      new Map([
        ['panel.menu', { sheet, x: 3, y: 4, w: 30, h: 20 }],
        ['heart.4', '/src/art-release-v2/ui/heart.4.png'],
        ['heart.0', { sheet, x: 40, y: 0, w: 22, h: 20 }],
      ]),
    );
    expect(urls).toEqual([
      ['panel.menu', 'data:image/png;base64,1'],
      ['heart.4', '/src/art-release-v2/ui/heart.4.png'],
      ['heart.0', 'data:image/png;base64,2'],
    ]);
    expect(canvases).toHaveLength(1);
    const [c] = canvases;
    expect(c.draws).toEqual([
      [sheet, 3, 4, 30, 20, 0, 0, 30, 20],
      [sheet, 40, 0, 22, 20, 0, 0, 22, 20],
    ]);
    expect(c.sizes).toEqual([[30, 20], [22, 20]]);
    expect([c.width, c.height]).toEqual([0, 0]);
  });
});
